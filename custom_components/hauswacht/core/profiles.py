"""Profilverwaltung (reine Logik).

Version 0.2.0 kennt die vier eingebauten Profile Zuhause, Nacht, Abwesend und Urlaub.
Ihre Zeiten sind über die Optionen einstellbar. Eigene Profile, Zonen und
Sensorzuordnung folgen mit 0.3.0.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .state_machine import ProfileRuntime

MAX_DELAY = 600  # Sekunden
MAX_REACTION_TIME = 900


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


def build_profiles(options: Mapping[str, Any]) -> dict[str, ProfileRuntime]:
    """Erzeugt die Laufzeitprofile aus den Optionen eines Konfigurationseintrags."""
    profiles: dict[str, ProfileRuntime] = {}
    for builtin in BUILTIN_PROFILES:
        settings = profile_settings(options, builtin.profile_id)
        profiles[builtin.profile_id] = ProfileRuntime(
            profile_id=builtin.profile_id,
            exit_delay=settings["exit_delay"],
            entry_delay=settings["entry_delay"],
            reaction_time=settings["reaction_time"],
        )
    return profiles
