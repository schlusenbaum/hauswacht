"""„Bei Rückkehr“ je Profil (ADR 0015): was passiert, wenn eine Person heimkommt.

Rein und ohne Home Assistant. Gespeichert unter ``profiles.<id>.return``:

- ``mode``: was bei Rückkehr einer Person der Liste passiert
  - ``off``: nichts
  - ``auto_only``: unscharf – nur, wenn die Automatik das Profil scharf geschaltet hat
  - ``door``: unscharf mit Türbeleg – Handy-Ankunft und Türöffnung im Zeitfenster
  - ``always``: unscharf, auch nach Scharfschalten von Hand, ohne Tür (mit Warnhinweis)
  - ``passage``: reinlassen – das Profil bleibt scharf, die Tür ist frei (Durchgang, ADR 0013)
- ``persons``: eigene Personenliste (unabhängig von „Scharf, wenn alle weg“)
- ``window``: Minuten zwischen Handy-Ankunft und Türöffnung (``door`` und ``passage``)

Bis 0.60 stand das an zwei Stellen: „Unscharf bei Rückkehr“ in der Automatik (mit den Personen
von „Scharf, wenn alle weg“) und Handy-Reinlassen im Durchgang. ``legacy_return`` rechnet das um;
die Umstellung der gespeicherten Einstellungen macht ``migrate_return``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

RETURN_OFF = "off"
RETURN_AUTO_ONLY = "auto_only"
RETURN_DOOR = "door"
RETURN_ALWAYS = "always"
RETURN_PASSAGE = "passage"
RETURN_MODES: tuple[str, ...] = (
    RETURN_OFF,
    RETURN_AUTO_ONLY,
    RETURN_DOOR,
    RETURN_ALWAYS,
    RETURN_PASSAGE,
)
# Diese Auswahlen schalten unscharf; "passage" lässt nur rein
DISARMING: frozenset[str] = frozenset({RETURN_AUTO_ONLY, RETURN_DOOR, RETURN_ALWAYS})
# Bei diesen entscheidet das Handy-Signal nach (oder kurz vor) der Tür
WITH_DOOR: frozenset[str] = frozenset({RETURN_DOOR, RETURN_PASSAGE})

DEFAULT_WINDOW = 5  # Minuten
MAX_WINDOW = 30
KEY = "return"


@dataclass(frozen=True)
class ReturnConfig:
    mode: str = RETURN_OFF
    persons: tuple[str, ...] = ()
    window: int = DEFAULT_WINDOW  # Minuten

    @property
    def active(self) -> bool:
        """Etwas eingestellt und mindestens eine Person gewählt."""
        return self.mode != RETURN_OFF and bool(self.persons)

    @property
    def disarms(self) -> bool:
        return self.active and self.mode in DISARMING

    @property
    def door_proof(self) -> bool:
        return self.active and self.mode == RETURN_DOOR

    @property
    def lets_in(self) -> bool:
        return self.active and self.mode == RETURN_PASSAGE

    @property
    def with_door(self) -> bool:
        return self.active and self.mode in WITH_DOOR


def _strings(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(dict.fromkeys(v for v in value if isinstance(v, str) and v))


def _window(value: Any) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return DEFAULT_WINDOW
    return min(max(number, 1), MAX_WINDOW)


def _profile(options: Mapping[str, Any], profile_id: str | None) -> Mapping[str, Any]:
    profiles = options.get("profiles", {})
    if not isinstance(profiles, Mapping) or not profile_id:
        return {}
    stored = profiles.get(profile_id, {})
    return stored if isinstance(stored, Mapping) else {}


def legacy_return(stored: Mapping[str, Any]) -> ReturnConfig:
    """Bis 0.60: „Unscharf bei Rückkehr“ (Automatik) und Handy-Reinlassen (Durchgang).

    Waren beide gesetzt (z. B. „wie bisher“ und Handy-Reinlassen), gewinnt „reinlassen“ mit
    dessen Personenliste – es lässt das Profil scharf, also die sichere Seite.
    """
    passage = stored.get("passage")
    if isinstance(passage, Mapping) and passage.get("enabled"):
        persons = _strings(passage.get("persons"))
        if persons:
            return ReturnConfig(RETURN_PASSAGE, persons, _window(passage.get("window")))
    mode = stored.get("auto_arrival_mode")
    if mode not in (RETURN_AUTO_ONLY, RETURN_DOOR):
        mode = RETURN_AUTO_ONLY if stored.get("auto_disarm_on_arrival") else RETURN_OFF
    persons = _strings(stored.get("auto_away_persons"))
    if mode == RETURN_OFF or not persons:
        return ReturnConfig()
    return ReturnConfig(str(mode), persons, _window(stored.get("auto_arrival_window")))


def parse_return(options: Mapping[str, Any], profile_id: str | None) -> ReturnConfig:
    """„Bei Rückkehr“ eines Profils; ohne gespeicherten Abschnitt aus den alten Einstellungen."""
    stored = _profile(options, profile_id)
    raw = stored.get(KEY)
    if not isinstance(raw, Mapping):
        return legacy_return(stored)
    mode = raw.get("mode")
    return ReturnConfig(
        mode=str(mode) if mode in RETURN_MODES else RETURN_OFF,
        persons=_strings(raw.get("persons")),
        window=_window(raw.get("window")),
    )


def return_to_storage(config: ReturnConfig) -> dict[str, Any]:
    return {"mode": config.mode, "persons": list(config.persons), "window": config.window}


def return_from_input(data: Mapping[str, Any]) -> dict[str, Any]:
    """Gespeicherte Form aus dem Formular (Abschnitt "return")."""
    mode = data.get("mode")
    return return_to_storage(
        ReturnConfig(
            mode=str(mode) if mode in RETURN_MODES else RETURN_OFF,
            persons=_strings(data.get("persons")),
            window=_window(data.get("window")),
        )
    )


def migrate_return(options: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Alte Einstellungen in „Bei Rückkehr“ umstellen (Version 5.2).

    Die alten Schlüssel bleiben stehen (eine ältere Version liest sie weiter). Zurück kommen die
    neuen Optionen und die Profil-IDs, bei denen beides gesetzt war (Hinweis nach dem Update).
    """
    new = dict(options)
    profiles = options.get("profiles", {})
    if not isinstance(profiles, Mapping):
        return new, []
    both: list[str] = []
    changed: dict[str, Any] = {}
    for profile_id, stored in profiles.items():
        if not isinstance(stored, Mapping) or isinstance(stored.get(KEY), Mapping):
            changed[profile_id] = stored
            continue
        config = legacy_return(stored)
        arrival = stored.get("auto_arrival_mode")
        if config.mode == RETURN_PASSAGE and (
            arrival in (RETURN_AUTO_ONLY, RETURN_DOOR) or stored.get("auto_disarm_on_arrival")
        ):
            both.append(str(profile_id))
        changed[profile_id] = {**stored, KEY: return_to_storage(config)}
    new["profiles"] = changed
    return new, both
