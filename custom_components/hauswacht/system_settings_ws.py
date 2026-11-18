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
from homeassistant.helpers import device_registry as dr
from homeassistant.util import dt as dt_util

from .const import MASTER_USER_ID
from .core.action_codes import ACTION_CODE_KEYS, ALL_KEYPADS, CodeAction, parse_action_codes
from .core.areas import parse_areas, profile_area
from .core.automation import parse_automation
from .core.changes.cards import all_cards
from .core.controls import (
    ALL_AREAS,
    ARM_KEYS,
    MAX_LEARN_MINUTES,
    ControlKind,
    learn_minutes,
    lock_id_label,
    parse_controls,
)
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


Z2M_BASE_TOPIC = "zigbee2mqtt"


def keypad_topic(hass: HomeAssistant, device_id: str | None) -> str:
    """MQTT-Topic eines Zigbee2MQTT-Geräts: Basis-Topic + Gerätename in Zigbee2MQTT."""
    device = dr.async_get(hass).async_get(device_id) if device_id else None
    if device is None or not device.name:
        return ""
    return f"{Z2M_BASE_TOPIC}/{device.name}"


def _devices(hass: HomeAssistant, *, domain: str | None = None) -> list[dict[str, str]]:
    found = []
    for device in dr.async_get(hass).devices.values():
        if domain is not None:
            domains = {
                entry.domain
                for ce in device.config_entries
                if (entry := hass.config_entries.async_get_entry(ce)) is not None
            }
            if domain not in domains:
                continue
        name = device.name_by_user or device.name or device.id
        found.append({"id": device.id, "name": str(name)})
    return sorted(found, key=lambda d: d["name"].casefold())


def _control_choices(hass: HomeAssistant) -> dict[str, Any]:
    events = {
        s.entity_id: [t for t in s.attributes.get("event_types", []) or [] if isinstance(t, str)]
        for s in hass.states.async_all("event")
    }
    return {
        "mqtt_devices": _devices(hass, domain="mqtt"),
        "devices": _devices(hass),
        "button_entities": _entities(hass, ["event", "sensor"]),
        "event_types": events,
        "locks": _entities(hass, ["lock"]),
        "who_entities": _entities(hass, ["sensor", "event"]),
        "arm_keys": list(ARM_KEYS),
        "all_areas": ALL_AREAS,
        "kinds": [k.value for k in ControlKind],
    }


def _last_used(main: Any, key: str) -> str:
    used = getattr(main, "last_used", {}).get(key)
    if not used:
        return ""
    return dt_util.as_local(dt_util.utc_from_timestamp(used)).isoformat()


def build_cards(hass: HomeAssistant, main: Any) -> dict[str, Any]:
    """Karten der Benutzer und zuletzt gelesene unbekannte Karten zum Anlernen."""
    options = main.entry.options
    lang = "de" if (hass.config.language or "").startswith("de") else "en"
    users = {k: v for k, v in options.get("users", {}).items() if k != MASTER_USER_ID}
    controls = getattr(main, "controls", None)
    unknown = controls.learnable_cards() if controls is not None else {}
    random = controls.recent_random() if controls is not None else None
    return {
        "cards": [
            {
                "tag": tag,
                "label": lock_id_label(tag, lang),
                "user": uid,
                "user_name": str(users[uid].get("name") or uid),
                "name": name,
                "active": active,
                "last_used": _last_used(main, f"card:{tag}"),
            }
            for tag, uid, name, active in all_cards(users)
        ],
        "unknown": [
            {
                "tag": tag,
                "label": lock_id_label(tag, lang),
                "source": source,
                "when": dt_util.as_local(dt_util.utc_from_timestamp(when)).strftime("%H:%M"),
            }
            for tag, (source, when) in unknown.items()
        ],
        "random_seen": (
            {
                "source": random[0],
                "when": dt_util.as_local(dt_util.utc_from_timestamp(random[1])).strftime("%H:%M"),
            }
            if random
            else None
        ),
        "learn_minutes": learn_minutes(options),
        "users": [{"id": uid, "name": str(d.get("name") or uid)} for uid, d in users.items()],
    }


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
                {**dict(data), "id": cid, "kind": controls[cid].kind.value}
                for cid, data in options.get("controls", {}).items()
                if cid in controls
            ],
            "learn_minutes": learn_minutes(options),
            "learn_max": MAX_LEARN_MINUTES,
            "choices": _control_choices(hass),
        },
        "cards": build_cards(hass, main),
    }
