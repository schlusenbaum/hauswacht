"""Durchgang (ADR 0013): rein oder raus, ohne unscharf zu schalten.

Rein und ohne Home Assistant.

Ein Durchgang lässt eine Tür (und frei gewählte Außenmelder auf dem Weg) kurz frei. Das Profil
bleibt scharf, alle anderen Melder lösen weiter aus.

- **Reinkommen** (Einlass): während der Eingangsverzögerung nach einem Ausweis. Die geöffnete
  Tür ist frei, bis sie wieder zu ist; die Wegmelder bis dahin plus Nachlaufzeit.
- **Rausgehen** (Ausgang): wenn scharf, vor dem Öffnen. Die erste Eingangstür, die danach
  aufgeht, ist für die Durchgangszeit frei (einstellbar: alle Eingangstüren); die Wegmelder für
  die ganze Zeit.

Einstellungen je Profil unter ``profiles.<id>.passage``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

# Tastenziel am Keypad (statt einer Profil-ID): "Durchgang"
PASSAGE_TARGET = "__passage__"

DEFAULT_DURATION = 5  # Minuten
MAX_DURATION = 60
DEFAULT_PATH_AFTER = 60  # Sekunden
MAX_PATH_AFTER = 600
DEFAULT_WINDOW = 5  # Minuten (Handy-Reinlassen, ab 0.59.0b2)
MAX_WINDOW = 30
# Rausgehen mit Ende "zurück": so oft muss die Tür zugehen (raus + zurück)
CLOSES_FOR_RETURN = 2


class Direction(StrEnum):
    IN = "in"  # Reinkommen (Einlass)
    OUT = "out"  # Rausgehen (Ausgang)


class OutDoors(StrEnum):
    FIRST = "first"  # nur die erste Tür, die nach dem Start aufgeht
    ALL = "all"  # alle Eingangstüren


class OutEnd(StrEnum):
    TIME = "time"  # nach Ablauf der Durchgangszeit
    RETURNED = "returned"  # schon, wenn man zurück ist und die Tür zu ist


@dataclass(frozen=True)
class PassageConfig:
    enabled: bool = False
    duration: int = DEFAULT_DURATION  # Minuten
    out_doors: OutDoors = OutDoors.FIRST
    out_end: OutEnd = OutEnd.TIME
    path: frozenset[str] = frozenset()
    path_after: int = DEFAULT_PATH_AFTER  # Sekunden
    persons: tuple[str, ...] = ()
    window: int = DEFAULT_WINDOW  # Minuten


def _strings(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(dict.fromkeys(v for v in value if isinstance(v, str) and v))


def _int(value: Any, default: int, low: int, high: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return min(max(number, low), high)


def _enum[E: StrEnum](kind: type[E], value: Any, default: E) -> E:
    try:
        return kind(value)
    except ValueError:
        return default


def parse_passage(options: Mapping[str, Any], profile_id: str | None) -> PassageConfig:
    """Durchgang-Einstellungen eines Profils (fehlt etwas: Standard, aus)."""
    profiles = options.get("profiles", {})
    stored = profiles.get(profile_id, {}) if isinstance(profiles, Mapping) and profile_id else {}
    raw = stored.get("passage", {}) if isinstance(stored, Mapping) else {}
    if not isinstance(raw, Mapping):
        return PassageConfig()
    return PassageConfig(
        enabled=bool(raw.get("enabled", False)),
        duration=_int(raw.get("duration"), DEFAULT_DURATION, 1, MAX_DURATION),
        out_doors=_enum(OutDoors, raw.get("out_doors"), OutDoors.FIRST),
        out_end=_enum(OutEnd, raw.get("out_end"), OutEnd.TIME),
        path=frozenset(_strings(raw.get("path"))),
        path_after=_int(raw.get("path_after"), DEFAULT_PATH_AFTER, 0, MAX_PATH_AFTER),
        persons=_strings(raw.get("persons")),
        window=_int(raw.get("window"), DEFAULT_WINDOW, 1, MAX_WINDOW),
    )


def passage_from_input(data: Mapping[str, Any]) -> dict[str, Any]:
    """Gespeicherte Form aus dem Formular (Abschnitt "passage")."""
    config = parse_passage({"profiles": {"p": {"passage": dict(data)}}}, "p")
    return {
        "enabled": config.enabled,
        "duration": config.duration,
        "out_doors": config.out_doors.value,
        "out_end": config.out_end.value,
        "path": sorted(config.path),
        "path_after": config.path_after,
        "persons": list(config.persons),
        "window": config.window,
    }


def out_candidates(
    entry_doors: frozenset[str], bypassed: frozenset[str], armed: frozenset[str]
) -> frozenset[str]:
    """Türen, die beim Rausgehen benutzt werden dürfen: scharfe Eingangstüren, die nicht
    ohnehin überbrückt sind."""
    return (entry_doors & armed) - bypassed


def path_sensors(
    config: PassageConfig, armed: frozenset[str], bypassed: frozenset[str]
) -> frozenset[str]:
    """Wegmelder, die der Durchgang wirklich freigeben muss (scharf und nicht schon frei)."""
    return (config.path & armed) - bypassed
