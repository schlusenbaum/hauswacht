"""Websocket-Befehle der Einstellungsseite (ADR 0011) – nur für Administratoren.

- ``hauswacht/settings/get``: was die Seite zum Bearbeiten braucht (Einstellungen der Melder,
  Auswahl an Entitäten, Labels) und eine **Revision** (Prüfsumme der Einstellungen).
- ``hauswacht/settings/apply``: eine Änderung über die Logikschicht (``core/changes``) – dieselben
  Regeln wie im Einstellungsdialog. Gespeichert wird nur, wenn alle Bereiche unscharf sind und die
  Revision noch stimmt (sonst hat zwischendurch jemand anders etwas geändert).

Diese Befehle schalten nichts – sie ändern nur Einstellungen.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import label_registry as lr

from .const import DOMAIN
from .core.always_active import parse_always_active
from .core.changes import Change
from .core.changes.profiles import delete_profile, save_profile
from .core.changes.sensors import (
    remove_group,
    remove_strength,
    remove_tilt,
    save_always,
    save_group,
    save_sensor,
    save_strength,
    save_tilt,
)
from .core.sensor_types import SensorType, default_type
from .core.tilt import effective_types, parse_tilt_sources
from .core.vibration import parse_vibration_sources, rule_for_zone_id
from .names import display_name
from .profile_settings_ws import build_profile_settings
from .runtime import device_class_of, entities_by_label

WS_GET = f"{DOMAIN}/settings/get"
WS_APPLY = f"{DOMAIN}/settings/apply"
DATA_WS = f"{DOMAIN}_settings_ws_registered"

# Entitäten für die Auswahl: Melder (offen/zu) und Quellen für Besondere Melder
PICKER_DOMAINS = (
    "binary_sensor",
    "lock",
    "cover",
    "sensor",
    "input_select",
    "select",
    "input_number",
    "number",
)

ACTIONS = (
    "group_save",
    "group_delete",
    "tilt_save",
    "tilt_delete",
    "strength_save",
    "strength_delete",
    "always_save",
    "sensor_save",
    "profile_save",
    "profile_delete",
)


def revision(options: Mapping[str, Any]) -> str:
    """Prüfsumme der Einstellungen – ändert sich mit jeder Änderung, egal von wo."""
    raw = json.dumps(options, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _main(hass: HomeAssistant) -> Any:
    for entry in hass.config_entries.async_loaded_entries(DOMAIN):
        runtime = getattr(entry, "runtime_data", None)
        if runtime is not None:
            return runtime
    return None


def build_settings(hass: HomeAssistant, main: Any) -> dict[str, Any]:
    options = main.entry.options
    types = effective_types(options)
    always = parse_always_active(options)
    labels = entities_by_label(hass)
    excluded_by_profile = {
        pid: list(data.get("excluded", []) or [])
        for pid, data in options.get("profiles", {}).items()
    }
    entities = []
    for state in hass.states.async_all(PICKER_DOMAINS):
        entity_id = state.entity_id
        device_class = state.attributes.get("device_class")
        entities.append(
            {
                "id": entity_id,
                "name": display_name(hass, entity_id),
                "domain": entity_id.split(".", 1)[0],
                "device_class": device_class,
                "state": state.state,
                "suggested": default_type(entity_id, device_class).value,
            }
        )
    return {
        "revision": revision(options),
        "editable": bool(main.all_disarmed),
        "types": [t.value for t in SensorType],
        "groups": [
            {
                "id": zone_id,
                "name": data.get("name", zone_id),
                "entities": list(data.get("entities", [])),
                "label": data.get("label"),
                "vibration_count": rule_for_zone_id(options, zone_id).count,
                "vibration_window": rule_for_zone_id(options, zone_id).window,
            }
            for zone_id, data in options.get("zones", {}).items()
        ],
        "sensor_types": {
            e: types.get(e, default_type(e, device_class_of(hass, e))).value
            for zone in options.get("zones", {}).values()
            for e in zone.get("entities", [])
        },
        "tilt": [
            {
                "entity": s.entity_id,
                "attribute": s.attribute,
                "closed": sorted(s.closed),
                "tilted": sorted(s.tilted),
            }
            for s in parse_tilt_sources(options).values()
        ],
        "strength": [
            {"entity": s.entity_id, "threshold": s.threshold}
            for s in parse_vibration_sources(options).values()
        ],
        "always": {"zones": list(always.zones), "sensors": sorted(always.sensors)},
        # Melder, die über ein Label in einer Gruppe stecken (dort nicht verschiebbar)
        "label_members": {
            zone_id: sorted(labels.get(data["label"], frozenset()))
            for zone_id, data in options.get("zones", {}).items()
            if data.get("label")
        },
        "profiles": [
            {
                "id": pid,
                "name": data.get("name", pid),
                "zones": list(data.get("zones", []) or []),
                "excluded": excluded_by_profile[pid],
            }
            for pid, data in options.get("profiles", {}).items()
        ],
        "labels": [
            {"id": label.label_id, "name": label.name}
            for label in lr.async_get(hass).async_list_labels()
        ],
        "entities": sorted(entities, key=lambda e: str(e["name"]).casefold()),
        "profile_edit": build_profile_settings(hass, main),
    }


def apply_change(hass: HomeAssistant, main: Any, action: str, data: Mapping[str, Any]) -> Change:
    """Änderung über die Logikschicht berechnen (noch nichts speichern)."""
    options = main.entry.options
    labels = entities_by_label(hass)
    if action == "group_save":
        members = list(data.get("entities") or [])
        return save_group(
            options,
            data.get("id") or None,
            data,
            labels=labels,
            device_classes={e: device_class_of(hass, e) for e in members},
        )
    if action == "sensor_save":
        entity_id = str(data.get("entity") or "")
        return save_sensor(
            options, entity_id, data, labels=labels, device_class=device_class_of(hass, entity_id)
        )
    if action == "profile_save":
        payload = {k: v for k, v in data.items() if k != "id"}
        return save_profile(options, data.get("id") or None, payload, entities_by_label=labels)
    if action == "profile_delete":
        if data.get("id") not in options.get("profiles", {}):
            return Change(errors={"base": "unknown_profile"})
        return delete_profile(options, str(data.get("id")))
    if action == "group_delete":
        return remove_group(options, str(data.get("id")))
    if action == "tilt_save":
        return save_tilt(options, data, labels=labels)
    if action == "tilt_delete":
        return remove_tilt(options, str(data.get("entity")))
    if action == "strength_save":
        return save_strength(options, data, labels=labels)
    if action == "strength_delete":
        return remove_strength(options, str(data.get("entity")))
    return save_always(options, zones=data.get("zones") or [], sensors=data.get("sensors") or [])


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): WS_GET})
@callback
def ws_settings_get(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    main = _main(hass)
    if main is None:
        connection.send_error(msg["id"], "not_loaded", "Hauswacht ist nicht geladen.")
        return
    connection.send_result(msg["id"], build_settings(hass, main))


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_APPLY,
        vol.Required("revision"): str,
        vol.Required("action"): vol.In(ACTIONS),
        vol.Optional("data", default={}): dict,
    }
)
@callback
def ws_settings_apply(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    main = _main(hass)
    if main is None:
        connection.send_error(msg["id"], "not_loaded", "Hauswacht ist nicht geladen.")
        return
    entry = main.entry
    if not main.all_disarmed:
        connection.send_result(msg["id"], {"ok": False, "errors": {"base": "disarm_first"}})
        return
    if msg["revision"] != revision(entry.options):
        connection.send_result(msg["id"], {"ok": False, "errors": {"base": "changed_elsewhere"}})
        return
    change = apply_change(hass, main, msg["action"], msg["data"])
    if not change.ok or change.options is None:
        connection.send_result(
            msg["id"],
            {"ok": False, "errors": dict(change.errors), "details": dict(change.details)},
        )
        return
    hass.config_entries.async_update_entry(entry, options=change.options)
    connection.send_result(
        msg["id"], {"ok": True, "revision": revision(change.options), "id": change.item_id}
    )


@callback
def async_register_settings_websocket(hass: HomeAssistant) -> None:
    if hass.data.get(DATA_WS):
        return
    websocket_api.async_register_command(hass, ws_settings_get)
    websocket_api.async_register_command(hass, ws_settings_apply)
    hass.data[DATA_WS] = True
