"""Einstellungsseite, Stufe 5: System, PIN-Regeln, Aktions-Codes, Bedienteile (ADR 0011).

Liefert die Werte für die Seitenblätter. Gespeichert wird über ``core.changes.system`` und
``core.changes.action_codes`` – dieselben Regeln wie im Dialog.

Bedienteile anlegen und einstellen bleibt im Dialog: Kennungen, Karten und Tastendrücke werden
dort am Gerät angelernt. Auf der Seite lassen sie sich ansehen und löschen.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.core import HomeAssistant

from .const import MASTER_USER_ID
from .core.action_codes import ACTION_CODE_KEYS, ALL_KEYPADS, CodeAction, parse_action_codes
from .core.areas import parse_areas, profile_area
from .core.automation import parse_automation
from .core.controls import MAX_LEARN_MINUTES, ControlKind, learn_minutes, parse_controls
from .core.profiles import MAX_STALE_HOURS, profile_ids, profile_info
from .core.restart import BEHAVIORS, continue_alarm, restart_behavior
from .names import display_name


def _presence_persons(options: Mapping[str, Any]) -> list[str]:
    """Personen der Heimkehr-Beobachtung und der Profil-Automatik (ohne Doppelte)."""
    persons = [p for p in options.get("homecoming_persons", []) if isinstance(p, str)]
    for pid in profile_ids(options):
        persons.extend(parse_automation(options, pid).away_persons)
    return list(dict.fromkeys(persons))


def _entities(hass: HomeAssistant, domains: list[str]) -> list[dict[str, str]]:
    found = [
        {"id": s.entity_id, "name": display_name(hass, s.entity_id)}
        for s in hass.states.async_all(domains)
    ]
    return sorted(found, key=lambda e: e["name"].casefold())


def build_system_settings(hass: HomeAssistant, main: Any) -> dict[str, Any]:
    options = main.entry.options
    areas = parse_areas(options)
    profiles = [
        {"id": pid, "name": profile_info(options, pid).name, "area": profile_area(options, pid)}
        for pid in profile_ids(options)
    ]
    silence = getattr(main, "silence", None)
    german = (hass.config.language or "").startswith("de")
    observation = silence.summary_text(german) if silence is not None else ""
    stale = options.get("stale_after_hours", 0)
    users = options.get("users", {})
    controls = parse_controls(options)
    keypads = [
        {"id": c.control_id, "name": c.name}
        for c in controls.values()
        if c.kind is ControlKind.KEYPAD
    ]
    return {
        "restart": {
            "behavior": restart_behavior(options),
            "behaviors": list(BEHAVIORS),
            "continue_alarm": continue_alarm(options),
            "profiles": dict(options.get("restart_profiles") or {}),
        },
        "silence": {
            "hours": int(stale or 0),
            "max": MAX_STALE_HOURS,
            "observation": observation,
        },
        "network": {
            "entities": list(options.get("infrastructure", [])),
            "choices": _entities(hass, ["binary_sensor"]),
        },
        "homecoming": {
            "observe": bool(options.get("homecoming_observe", False)),
            "persons": list(options.get("homecoming_persons", [])),
            "ssids": list(options.get("homecoming_ssids", [])),
            "signals": dict(options.get("homecoming_signals", {})),
            # Personen, für die es Zusatzsignale gibt (Beobachtung und Profil-Automatik)
            "signal_persons": _presence_persons(options),
            "person_choices": _entities(hass, ["person"]),
            "signal_choices": _entities(hass, ["device_tracker", "binary_sensor", "sensor"]),
        },
        "areas": [
            {
                "id": a.area_id,
                "name": a.name,
                "icon": a.icon,
                "profiles": [p["name"] for p in profiles if p["area"] == a.area_id],
            }
            for a in areas.values()
        ],
        "profiles": profiles,
        "settings_page": bool(options.get("settings_page", True)),
        "pin_rules": {
            "master": MASTER_USER_ID in users,
            "code_arm_required": bool(options.get("code_arm_required", False)),
            "end_alarm_without_pin": bool(options.get("end_alarm_without_pin", False)),
            "buttons_without_pin": bool(options.get("buttons_without_pin", False)),
            "card_pin_unlinked": bool(options.get("card_pin_unlinked", True)),
            "pin_users": sorted(
                str(d.get("name") or uid)
                for uid, d in users.items()
                if uid != MASTER_USER_ID and isinstance(d, Mapping) and d.get("pin_digest")
            ),
        },
        "action_codes": {
            "codes": [
                {
                    "id": c.code_id,
                    "name": c.name,
                    "code": c.code,
                    "key": c.key,
                    "keypad": c.keypad,
                    "action": c.action.value,
                    "profile": c.profile,
                }
                for c in sorted(parse_action_codes(options), key=lambda c: c.name.casefold())
            ],
            "keys": list(ACTION_CODE_KEYS),
            "actions": [a.value for a in CodeAction],
            "keypads": keypads,
            "all_keypads": ALL_KEYPADS,
        },
        "controls": {
            "items": [
                {"id": c.control_id, "name": c.name, "kind": c.kind.value}
                for c in controls.values()
            ],
            "learn_minutes": learn_minutes(options),
            "learn_max": MAX_LEARN_MINUTES,
        },
    }
