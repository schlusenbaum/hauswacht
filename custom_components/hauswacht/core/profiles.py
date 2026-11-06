"""Profilverwaltung (reine Logik).

Es gibt die vier eingebauten Profile Zuhause, Nacht, Abwesend und Urlaub. Pro Profil sind
Zeiten, überwachte Zonen, der Umgang mit offenen bzw. ausgefallenen Sensoren, die Zahl der
Alarmzyklen und die Reaktion auf Manipulation einstellbar.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .state_machine import OpenSensorPolicy, ProfileRuntime, UnavailableSensorPolicy

MAX_DELAY = 600  # Sekunden
MAX_REACTION_TIME = 900
MAX_ALARM_CYCLES = 10
DEFAULT_ALARM_CYCLES = 3
MAX_STALE_HOURS = 168


@dataclass(frozen=True)
class BuiltinProfile:
    profile_id: str
    panel_state: str  # Zustand der alarm_control_panel-Entität im scharfen Zustand
    exit_delay: int
    entry_delay: int
    reaction_time: int = 180


BUILTIN_PROFILES: tuple[BuiltinProfile, ...] = (
    BuiltinProfile("home", "armed_home", exit_delay=0, entry_delay=30),
    BuiltinProfile("night", "armed_night", exit_delay=0, entry_delay=30),
    BuiltinProfile("away", "armed_away", exit_delay=60, entry_delay=30),
    BuiltinProfile("vacation", "armed_vacation", exit_delay=60, entry_delay=30),
)

PROFILE_IDS: tuple[str, ...] = tuple(p.profile_id for p in BUILTIN_PROFILES)
PANEL_STATE_BY_PROFILE: Mapping[str, str] = {p.profile_id: p.panel_state for p in BUILTIN_PROFILES}

PROFILE_FIELDS = ("exit_delay", "entry_delay", "reaction_time")


def _bounded_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    """Liest einen Wert aus den Optionen; Ungültiges fällt auf den Standard zurück."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    if number < minimum or number > maximum:
        return default
    return number


def profile_settings(options: Mapping[str, Any], profile_id: str) -> dict[str, int]:
    """Aktuelle Zeiten eines Profils (Optionen mit Standardwerten ergänzt)."""
    builtin = next(p for p in BUILTIN_PROFILES if p.profile_id == profile_id)
    stored: Mapping[str, Any] = options.get("profiles", {}).get(profile_id, {})
    return {
        "exit_delay": _bounded_int(stored.get("exit_delay"), builtin.exit_delay, 0, MAX_DELAY),
        "entry_delay": _bounded_int(stored.get("entry_delay"), builtin.entry_delay, 0, MAX_DELAY),
        "reaction_time": _bounded_int(
            stored.get("reaction_time"), builtin.reaction_time, 1, MAX_REACTION_TIME
        ),
    }


@dataclass(frozen=True)
class ProfileBehaviour:
    """Verhalten eines Profils über die Zeiten hinaus."""

    zones: tuple[str, ...] = ()
    open_policy: OpenSensorPolicy = OpenSensorPolicy.REFUSE
    unavailable_policy: UnavailableSensorPolicy = UnavailableSensorPolicy.REFUSE
    max_alarm_cycles: int = DEFAULT_ALARM_CYCLES
    tamper_triggers_alarm: bool = False


def _enum[E: (OpenSensorPolicy, UnavailableSensorPolicy)](
    value: Any, kind: type[E], default: E
) -> E:
    try:
        return kind(value)
    except ValueError:
        return default


def profile_behaviour(options: Mapping[str, Any], profile_id: str) -> ProfileBehaviour:
    stored: Mapping[str, Any] = options.get("profiles", {}).get(profile_id, {})
    zones = stored.get("zones", [])
    return ProfileBehaviour(
        zones=tuple(str(z) for z in zones) if isinstance(zones, list | tuple) else (),
        open_policy=_enum(stored.get("open_policy"), OpenSensorPolicy, OpenSensorPolicy.REFUSE),
        unavailable_policy=_enum(
            stored.get("unavailable_policy"),
            UnavailableSensorPolicy,
            UnavailableSensorPolicy.REFUSE,
        ),
        max_alarm_cycles=_bounded_int(
            stored.get("max_alarm_cycles"), DEFAULT_ALARM_CYCLES, 1, MAX_ALARM_CYCLES
        ),
        tamper_triggers_alarm=bool(stored.get("tamper_triggers_alarm", False)),
    )


def stale_after_seconds(options: Mapping[str, Any]) -> float | None:
    """Wie lange ein Sensor schweigen darf, bevor er als ausgefallen gilt (None = aus)."""
    hours = _bounded_int(options.get("stale_after_hours"), 0, 0, MAX_STALE_HOURS)
    return hours * 3600.0 if hours > 0 else None


def build_profiles(options: Mapping[str, Any]) -> dict[str, ProfileRuntime]:
    """Erzeugt die Laufzeitprofile aus den Optionen eines Konfigurationseintrags."""
    profiles: dict[str, ProfileRuntime] = {}
    for builtin in BUILTIN_PROFILES:
        settings = profile_settings(options, builtin.profile_id)
        behaviour = profile_behaviour(options, builtin.profile_id)
        profiles[builtin.profile_id] = ProfileRuntime(
            profile_id=builtin.profile_id,
            exit_delay=settings["exit_delay"],
            entry_delay=settings["entry_delay"],
            reaction_time=settings["reaction_time"],
            open_policy=behaviour.open_policy,
            unavailable_policy=behaviour.unavailable_policy,
            max_alarm_cycles=behaviour.max_alarm_cycles,
            tamper_triggers_alarm=behaviour.tamper_triggers_alarm,
        )
    return profiles
