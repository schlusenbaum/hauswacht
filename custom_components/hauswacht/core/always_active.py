"""Immer aktive Melder und "Scharf durch Schließen der Tür".

Rein und ohne Home Assistant.

**Immer aktiv** (``options["always_active"]``): Melder, die auch im unscharfen Zustand auslösen.
Unscharf ist die Reaktion standardmäßig nur eine (wichtige) Benachrichtigung; mit
``sirens_enabled`` gibt es einen Alarm mit eigener Sirenen-Reaktion, den "Alarm beenden" wieder
nach unscharf zurückführt. Scharf lösen sie sofort aus – mit der Reaktion des aktiven Profils.

**Scharf durch Schließen** (pro Profil): Die Ausgangsverzögerung endet vorzeitig, wenn eine
Ausgangstür geschlossen wird und die Beruhigungszeit lang zu bleibt. Ausgangstüren dürfen beim
Scharfschalten offen sein; am Ende der Ausgangsverzögerung gilt die normale Prüfung.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .state_machine import ProfileRuntime

ALWAYS_PROFILE_ID = "__always__"
ALWAYS_PROFILE_NAME = "Immer aktiv"
DEFAULT_ALWAYS_REACTION = 180
DEFAULT_SETTLE = 5
MAX_SETTLE = 60


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


@dataclass(frozen=True)
class AlwaysActive:
    zones: tuple[str, ...] = ()
    sensors: tuple[str, ...] = ()
    sirens_enabled: bool = False
    sirens: tuple[str, ...] = ()
    tone: str | None = None
    volume: str | None = None
    reaction_time: int = DEFAULT_ALWAYS_REACTION

    @property
    def configured(self) -> bool:
        return bool(self.zones or self.sensors)


def parse_always_active(options: Mapping[str, Any]) -> AlwaysActive:
    raw = options.get("always_active", {})
    if not isinstance(raw, Mapping):
        return AlwaysActive()
    return AlwaysActive(
        zones=_strings(raw.get("zones")),
        sensors=_strings(raw.get("sensors")),
        sirens_enabled=bool(raw.get("sirens_enabled", False)),
        sirens=_strings(raw.get("sirens")),
        tone=raw.get("siren_tone") if isinstance(raw.get("siren_tone"), str) else None,
        volume=raw.get("siren_volume") if isinstance(raw.get("siren_volume"), str) else None,
        reaction_time=_int(raw.get("reaction_time"), DEFAULT_ALWAYS_REACTION, 1, 3600),
    )


def always_runtime(config: AlwaysActive) -> ProfileRuntime:
    """Pseudo-Profil für einen Alarm im unscharfen Zustand."""
    return ProfileRuntime(profile_id=ALWAYS_PROFILE_ID, reaction_time=config.reaction_time)


def always_reaction_options(options: Mapping[str, Any]) -> dict[str, Any]:
    """Optionen so umbauen, dass ``parse_reaction(…, ALWAYS_PROFILE_ID)`` die Reaktion liefert.

    Ohne ``sirens_enabled`` keine Sirenen (stiller Alarm).
    """
    config = parse_always_active(options)
    stored: dict[str, Any] = {
        "sirens": list(config.sirens) if config.sirens_enabled else [],
        "silent": not config.sirens_enabled,
        "notify": [],
    }
    if config.tone:
        stored["siren_tone"] = config.tone
    if config.volume:
        stored["siren_volume"] = config.volume
    return {"sirens": options.get("sirens", []), "profiles": {ALWAYS_PROFILE_ID: stored}}


@dataclass(frozen=True)
class ArmOnClose:
    enabled: bool = False
    doors: frozenset[str] = frozenset()
    settle: int = DEFAULT_SETTLE


def parse_arm_on_close(options: Mapping[str, Any], profile_id: str) -> ArmOnClose:
    profiles = options.get("profiles", {})
    stored = profiles.get(profile_id, {}) if isinstance(profiles, Mapping) else {}
    raw = stored.get("arm_on_close", {}) if isinstance(stored, Mapping) else {}
    if not isinstance(raw, Mapping):
        return ArmOnClose()
    doors = frozenset(_strings(raw.get("doors")))
    return ArmOnClose(
        enabled=bool(raw.get("enabled", False)) and bool(doors),
        doors=doors,
        settle=_int(raw.get("settle"), DEFAULT_SETTLE, 1, MAX_SETTLE),
    )
