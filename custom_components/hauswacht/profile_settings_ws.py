"""Einstellungsseite, Stufe 3: Daten zum Bearbeiten der Alarmprofile (ADR 0011).

Liefert je Profil alle Werte im Format des Einstellungsdialogs und die Auswahlmöglichkeiten
(Sirenen, Empfänger, Lautsprecher, Personen, Zeitpläne …). Gespeichert wird über
``save_profile`` – dieselbe Funktion wie im Dialog.
"""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .core.always_active import DEFAULT_SETTLE, MAX_SETTLE, parse_arm_on_close
from .core.areas import MAIN_AREA, parse_areas, profile_area
from .core.automation import (
    ARRIVAL_MODES,
    DEFAULT_ARRIVAL_WINDOW,
    DEFAULT_AWAY_DELAY,
    MAX_ARRIVAL_WINDOW,
    MAX_AWAY_DELAY,
    WEEKDAYS,
    parse_automation,
)
from .core.profiles import (
    DEFAULT_ALARM_CYCLES,
    DEFAULT_ENTRY_DELAY,
    DEFAULT_EXIT_DELAY,
    DEFAULT_ICON,
    DEFAULT_REACTION_TIME,
    MAX_ALARM_CYCLES,
    MAX_DELAY,
    MAX_REACTION_TIME,
    PANEL_MODES,
    profile_behaviour,
    profile_info,
    profile_settings,
)
from .core.reactions import DEFAULT_TONE, DEFAULT_VOLUME, parse_reaction
from .core.rules import parse_rules, profile_rule_ids
from .core.sensor_types import excluded_sensors
from .core.siren_guard import BURGLAR_TONE_ORDER, VOLUME_LEVELS
from .core.speech import profile_speakers
from .core.state_machine import OpenSensorPolicy, UnavailableSensorPolicy
from .core.tilt import parse_tilt_sources
from .names import display_name
from .notify_targets import notify_choices


def _time(value: Any) -> str | None:
    return value.strftime("%H:%M") if value is not None else None


def _profile(options: Any, pid: str) -> dict[str, Any]:
    info = profile_info(options, pid)
    times = profile_settings(options, pid)
    behaviour = profile_behaviour(options, pid)
    reaction = parse_reaction(options, pid)
    auto = parse_automation(options, pid)
    close = parse_arm_on_close(options, pid)
    return {
        "id": pid,
        "name": info.name,
        "icon": info.icon,
        "panel_mode": info.panel_mode or "none",
        "area": profile_area(options, pid),
        "zones": list(behaviour.zones),
        "excluded": sorted(excluded_sensors(options, pid)),
        "rules": list(profile_rule_ids(options, pid)),
        "exit_delay": times["exit_delay"],
        "entry_delay": times["entry_delay"],
        "reaction_time": times["reaction_time"],
        "open_policy": behaviour.open_policy.value,
        "unavailable_policy": behaviour.unavailable_policy.value,
        "max_alarm_cycles": behaviour.max_alarm_cycles,
        "tamper_triggers_alarm": behaviour.tamper_triggers_alarm,
        "tilt_allowed": behaviour.tilt_allowed,
        "sirens": list(reaction.sirens),
        "siren_tone": reaction.tone,
        "siren_volume": reaction.volume,
        "silent": reaction.silent,
        "notify": list(reaction.notify),
        "speakers": list(profile_speakers(options, pid)),
        "automation": {
            "auto_arm_time": _time(auto.arm_time),
            "auto_disarm_time": _time(auto.disarm_time),
            "auto_weekdays": sorted(auto.weekdays, key=WEEKDAYS.index),
            "auto_schedule": auto.schedule,
            "auto_away_persons": list(auto.away_persons),
            "auto_away_delay": auto.away_delay,
            "auto_arrival_mode": auto.arrival_mode,
            "auto_arrival_window": auto.arrival_window,
        },
        "arm_on_close": {
            "enabled": close.enabled,
            "doors": sorted(close.doors),
            "settle": close.settle,
        },
    }


def _notify_choices(hass: HomeAssistant) -> list[dict[str, str]]:
    """Empfänger wie im Dialog – jedes Handy nur einmal (siehe ``notify_targets``)."""
    return [{"id": c["id"], "name": c["name"]} for c in notify_choices(hass)]


def _speaker_choices(hass: HomeAssistant) -> list[dict[str, str]]:
    """Geräte mit einer Benachrichtigungs-Entität (wie die Geräteauswahl im Dialog)."""
    registry = er.async_get(hass)
    devices = dr.async_get(hass)
    found: dict[str, str] = {}
    for entry in registry.entities.values():
        if entry.domain != "notify" or entry.device_id is None or entry.disabled_by:
            continue
        device = devices.async_get(entry.device_id)
        if device is not None:
            found[device.id] = device.name_by_user or device.name or device.id
    return [{"id": k, "name": v} for k, v in sorted(found.items(), key=lambda i: i[1].casefold())]


def build_profile_settings(hass: HomeAssistant, main: Any) -> dict[str, Any]:
    options = main.entry.options
    rules = parse_rules(options)
    areas = parse_areas(options)
    registered = [s for s in options.get("sirens", []) if isinstance(s, str)]
    return {
        "profiles": [_profile(options, pid) for pid in options.get("profiles", {})],
        "choices": {
            "panel_modes": ["none", *PANEL_MODES],
            "areas": [{"id": a.area_id, "name": a.name} for a in areas.values()],
            "rules": [{"id": r.rule_id, "name": r.name} for r in rules.values()],
            "open_policies": [p.value for p in OpenSensorPolicy],
            "unavailable_policies": [p.value for p in UnavailableSensorPolicy],
            "sirens": [{"id": s, "name": display_name(hass, s)} for s in registered],
            "tones": list(BURGLAR_TONE_ORDER),
            "volumes": list(VOLUME_LEVELS),
            "notify": _notify_choices(hass),
            "speakers": _speaker_choices(hass),
            "persons": [
                {"id": s.entity_id, "name": s.name} for s in hass.states.async_all("person")
            ],
            "schedules": [
                {"id": s.entity_id, "name": s.name} for s in hass.states.async_all("schedule")
            ],
            "weekdays": list(WEEKDAYS),
            "arrival_modes": list(ARRIVAL_MODES),
            "tilt": bool(parse_tilt_sources(options)),
        },
        "defaults": {
            "name": "",
            "icon": DEFAULT_ICON,
            "panel_mode": "none",
            "area": MAIN_AREA,
            "zones": [],
            "excluded": [],
            "rules": [],
            "exit_delay": DEFAULT_EXIT_DELAY,
            "entry_delay": DEFAULT_ENTRY_DELAY,
            "reaction_time": DEFAULT_REACTION_TIME,
            "open_policy": OpenSensorPolicy.REFUSE.value,
            "unavailable_policy": UnavailableSensorPolicy.REFUSE.value,
            "max_alarm_cycles": DEFAULT_ALARM_CYCLES,
            "tamper_triggers_alarm": False,
            "tilt_allowed": False,
            "sirens": [],
            "siren_tone": DEFAULT_TONE,
            "siren_volume": DEFAULT_VOLUME,
            "silent": False,
            "notify": [],
            "speakers": [],
            "automation": {
                "auto_arm_time": None,
                "auto_disarm_time": None,
                "auto_weekdays": [],
                "auto_schedule": None,
                "auto_away_persons": [],
                "auto_away_delay": DEFAULT_AWAY_DELAY,
                "auto_arrival_mode": "off",
                "auto_arrival_window": DEFAULT_ARRIVAL_WINDOW,
            },
            "arm_on_close": {"enabled": False, "doors": [], "settle": DEFAULT_SETTLE},
        },
        "limits": {
            "delay": MAX_DELAY,
            "reaction": MAX_REACTION_TIME,
            "cycles": MAX_ALARM_CYCLES,
            "away_delay": MAX_AWAY_DELAY,
            "arrival_window": MAX_ARRIVAL_WINDOW,
            "settle": MAX_SETTLE,
        },
    }
