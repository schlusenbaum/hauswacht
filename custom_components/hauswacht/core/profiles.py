"""Profilverwaltung (reine Logik).

Profile sind vollständig Konfiguration: Es gibt keine eingebauten Profile. Jedes Profil hat
eine stabile ID, einen Namen, ein Symbol, optional einen Knopf am Bedienfeld
(Zuhause/Nacht/Abwesend/Urlaub/Benutzerdefiniert) und alle Einstellungen zu Zonen, Zeiten,
Verhalten und Reaktionen.

Gespeichert wird alles in den Optionen unter ``profiles``::

    {"profiles": {"<id>": {"name": ..., "icon": ..., "panel_mode": ..., "zones": [...], ...}}}

Die Reihenfolge der Einträge ist die Anzeigereihenfolge.
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

DEFAULT_EXIT_DELAY = 30
DEFAULT_ENTRY_DELAY = 30
DEFAULT_REACTION_TIME = 180
DEFAULT_ICON = "mdi:shield-home-outline"

# Knöpfe des Home-Assistant-Bedienfelds und der Zustand, den es im scharfen Zustand zeigt
PANEL_MODES: tuple[str, ...] = ("home", "night", "away", "vacation", "custom")
PANEL_STATE_BY_MODE: Mapping[str, str] = {
    "home": "armed_home",
    "night": "armed_night",
    "away": "armed_away",
    "vacation": "armed_vacation",
    "custom": "armed_custom_bypass",
}
# Profile ohne eigenen Knopf zeigen sich am Bedienfeld als "benutzerdefiniert"
FALLBACK_PANEL_STATE = "armed_custom_bypass"
PANEL_MODE_NONE = "none"


@dataclass(frozen=True)
class ProfileInfo:
    profile_id: str
    name: str
    icon: str
    panel_mode: str | None


def _bounded_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    """Liest einen Wert aus den Optionen; Ungültiges fällt auf den Standard zurück."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    if number < minimum or number > maximum:
        return default
    return number


def _stored_profiles(options: Mapping[str, Any]) -> Mapping[str, Any]:
    raw = options.get("profiles", {})
    return raw if isinstance(raw, Mapping) else {}


def _stored(options: Mapping[str, Any], profile_id: str) -> Mapping[str, Any]:
    data = _stored_profiles(options).get(profile_id, {})
    return data if isinstance(data, Mapping) else {}


# --- Profile auflisten und finden --------------------------------------------


def profile_ids(options: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(
        str(pid) for pid, data in _stored_profiles(options).items() if isinstance(data, Mapping)
    )


def profile_info(options: Mapping[str, Any], profile_id: str) -> ProfileInfo:
    stored = _stored(options, profile_id)
    mode = stored.get("panel_mode")
    return ProfileInfo(
        profile_id=profile_id,
        name=str(stored.get("name") or profile_id),
        icon=str(stored.get("icon") or DEFAULT_ICON),
        panel_mode=mode if mode in PANEL_MODES else None,
    )


def profile_infos(options: Mapping[str, Any]) -> list[ProfileInfo]:
    return [profile_info(options, pid) for pid in profile_ids(options)]


def find_profile(options: Mapping[str, Any], reference: str) -> str | None:
    """Profil-ID zu einer ID oder einem Namen (Groß-/Kleinschreibung egal)."""
    if reference in profile_ids(options):
        return reference
    wanted = reference.strip().casefold()
    for info in profile_infos(options):
        if info.name.casefold() == wanted:
            return info.profile_id
    return None


def profile_for_mode(options: Mapping[str, Any], mode: str) -> str | None:
    """Das Profil, das einem Bedienfeld-Knopf zugeordnet ist."""
    for info in profile_infos(options):
        if info.panel_mode == mode:
            return info.profile_id
    return None


def used_panel_modes(options: Mapping[str, Any]) -> tuple[str, ...]:
    used = {info.panel_mode for info in profile_infos(options) if info.panel_mode}
    return tuple(mode for mode in PANEL_MODES if mode in used)


def panel_state(options: Mapping[str, Any], profile_id: str) -> str:
    mode = profile_info(options, profile_id).panel_mode
    return PANEL_STATE_BY_MODE[mode] if mode else FALLBACK_PANEL_STATE


# --- Einstellungen ------------------------------------------------------------


def profile_settings(options: Mapping[str, Any], profile_id: str) -> dict[str, int]:
    """Zeiten eines Profils (fehlende oder ungültige Werte -> Standard)."""
    stored = _stored(options, profile_id)
    return {
        "exit_delay": _bounded_int(stored.get("exit_delay"), DEFAULT_EXIT_DELAY, 0, MAX_DELAY),
        "entry_delay": _bounded_int(stored.get("entry_delay"), DEFAULT_ENTRY_DELAY, 0, MAX_DELAY),
        "reaction_time": _bounded_int(
            stored.get("reaction_time"), DEFAULT_REACTION_TIME, 1, MAX_REACTION_TIME
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
    stored = _stored(options, profile_id)
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
    for profile_id in profile_ids(options):
        settings = profile_settings(options, profile_id)
        behaviour = profile_behaviour(options, profile_id)
        profiles[profile_id] = ProfileRuntime(
            profile_id=profile_id,
            exit_delay=settings["exit_delay"],
            entry_delay=settings["entry_delay"],
            reaction_time=settings["reaction_time"],
            open_policy=behaviour.open_policy,
            unavailable_policy=behaviour.unavailable_policy,
            max_alarm_cycles=behaviour.max_alarm_cycles,
            tamper_triggers_alarm=behaviour.tamper_triggers_alarm,
        )
    return profiles


# --- Migration von Version 1 (feste Profile) ----------------------------------

# Die fünf festen Profile bis 0.7.0: ID, Name, Symbol, Knopf, Ausgangsverzögerung
LEGACY_PROFILES: tuple[tuple[str, str, str, str, int], ...] = (
    ("home", "Zuhause", "mdi:home-outline", "home", 0),
    ("night", "Nacht", "mdi:weather-night", "night", 0),
    ("away", "Abwesend", "mdi:shield-lock-outline", "away", 60),
    ("vacation", "Urlaub", "mdi:airplane", "vacation", 60),
    ("custom", "Individuell", "mdi:tune-variant", "custom", 0),
)


def migrate_v1_options(options: Mapping[str, Any]) -> dict[str, Any]:
    """Wandelt die festen Profile in normale, frei änderbare Profile um.

    Bisher nicht gespeicherte Zeiten werden mit den damaligen Standardwerten festgeschrieben,
    damit sich das Verhalten durch die Migration nicht ändert.
    """
    new_options = dict(options)
    old = _stored_profiles(options)
    profiles: dict[str, Any] = {}
    for profile_id, name, icon, mode, exit_delay in LEGACY_PROFILES:
        stored = old.get(profile_id, {})
        data: dict[str, Any] = {
            "name": name,
            "icon": icon,
            "panel_mode": mode,
            "exit_delay": exit_delay,
            "entry_delay": DEFAULT_ENTRY_DELAY,
            "reaction_time": DEFAULT_REACTION_TIME,
        }
        if isinstance(stored, Mapping):
            data.update(stored)
        profiles[profile_id] = data
    new_options["profiles"] = profiles
    return new_options
