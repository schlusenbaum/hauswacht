"""Websocket-Befehle der Einstellungsseite (ADR 0011) – nur für Administratoren.

- ``hauswacht/settings/get``: was die Seite zum Bearbeiten braucht (Einstellungen der Melder,
  Auswahl an Entitäten, Labels) und eine **Revision** (Prüfsumme der Einstellungen).
- ``hauswacht/settings/apply``: eine Änderung über die Logikschicht (``core/changes``) – dieselben
  Regeln wie im Einstellungsdialog. Gespeichert wird nur, wenn alle Bereiche unscharf sind und die
  Revision noch stimmt (sonst hat zwischendurch jemand anders etwas geändert).

Diese Befehle schalten nichts – sie ändern nur Einstellungen.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import label_registry as lr
from homeassistant.util.yaml import parse_yaml

from .advisor_ws import async_register_advisor_websocket
from .alarm_notify_settings_ws import build_alarm_notify_settings
from .const import DOMAIN
from .core.always_active import parse_always_active
from .core.changes import Change, options_revision
from .core.changes.action_codes import delete_action_code, save_action_code
from .core.changes.areas import save_area
from .core.changes.cards import add_card, edit_card
from .core.changes.controls import save_control
from .core.changes.notifications import save_event_text, save_notify_settings
from .core.changes.profiles import delete_profile, save_profile
from .core.changes.rules import delete_rule, save_rule
from .core.changes.sensors import (
    TARGET_ALWAYS,
    check_threshold_helper,
    place_new_sensor,
    remove_group,
    remove_strength,
    remove_tilt,
    save_always,
    save_group,
    save_sensor,
    save_strength,
    save_tilt,
)
from .core.changes.sirens import save_siren_test_settings, save_siren_tone, save_sirens
from .core.changes.speech import save_speech_event, save_speech_settings
from .core.changes.system import (
    delete_area,
    delete_control,
    save_homecoming,
    save_infrastructure,
    save_learn_minutes,
    save_pin_rules,
    save_restart,
    save_settings_page,
    save_silence,
)
from .core.changes.users import delete_user, save_person
from .core.sensor_types import SensorType, default_type
from .core.tilt import effective_types, parse_tilt_sources
from .core.vibration import parse_vibration_sources, rule_for_zone_id
from .goals_ws import async_register_goals_websocket
from .names import display_name
from .people_settings_ws import build_people_settings, ha_user_choices, to_iso
from .profile_settings_ws import build_profile_settings
from .rule_settings_ws import build_rule_settings, ws_rule_check
from .runtime import device_class_of, entities_by_label
from .system_settings_ws import build_cards, build_system_settings, keypad_topic

WS_GET = f"{DOMAIN}/settings/get"
WS_APPLY = f"{DOMAIN}/settings/apply"
WS_NEW_CARDS = f"{DOMAIN}/settings/new_cards"
DATA_WS = f"{DOMAIN}_settings_ws_registered"
_LOGGER = logging.getLogger(__name__)

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
    "sirens_save",
    "notify_save",
    "notify_text_save",
    "rule_save",
    "rule_delete",
    "user_save",
    "user_delete",
    "restart_save",
    "silence_save",
    "network_save",
    "homecoming_save",
    "area_save",
    "area_delete",
    "settings_page_save",
    "pin_rules_save",
    "action_code_save",
    "action_code_delete",
    "control_delete",
    "learn_save",
    "siren_tone_save",
    "siren_test_save",
    "siren_from_switch",
    "control_save",
    "card_add",
    "card_save",
    "speech_save",
    "speech_event_save",
    "helper_create",
)
# Brauchen Rechenzeit (PIN-Hashes) – laufen im Executor, nur mit reiner Logik
SLOW_ACTIONS = {
    "user_save": lambda o, d: save_person(o, d.get("id") or None, d, ha_user=d.get("ha_user")),
    "pin_rules_save": save_pin_rules,
    "action_code_save": lambda o, d: save_action_code(o, d.get("id") or None, d),
}
# Einfache Änderungen ohne Home Assistant: Aktion -> Funktion(Einstellungen, Daten)
SIMPLE_ACTIONS = {
    "user_delete": lambda o, d: (
        delete_user(o, str(d.get("id")))
        if d.get("id") in o.get("users", {})
        else Change(errors={"base": "unknown_user"})
    ),
    "restart_save": save_restart,
    "silence_save": lambda o, d: save_silence(o, d.get("hours")),
    "network_save": lambda o, d: save_infrastructure(o, d.get("entities")),
    "homecoming_save": save_homecoming,
    "area_save": lambda o, d: save_area(o, d.get("id") or None, d),
    "area_delete": lambda o, d: delete_area(o, str(d.get("id"))),
    "settings_page_save": lambda o, d: save_settings_page(o, bool(d.get("enabled"))),
    "action_code_delete": lambda o, d: delete_action_code(o, str(d.get("id"))),
    "control_delete": lambda o, d: delete_control(o, str(d.get("id"))),
    "learn_save": lambda o, d: save_learn_minutes(o, d.get("minutes")),
    "siren_test_save": lambda o, d: save_siren_test_settings(
        o, d.get("reminder_months"), bool(d.get("prewarn"))
    ),
    "card_add": add_card,
    "speech_save": save_speech_settings,
    "card_save": lambda o, d: edit_card(o, str(d.get("tag")), d),
}


def revision(options: Mapping[str, Any]) -> str:
    return options_revision(options)


def _main(hass: HomeAssistant) -> Any:
    for entry in hass.config_entries.async_loaded_entries(DOMAIN):
        runtime = getattr(entry, "runtime_data", None)
        if runtime is not None:
            return runtime
    return None


def build_settings(
    hass: HomeAssistant, main: Any, ha_users: list[dict[str, str]] | None = None
) -> dict[str, Any]:
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
        # Stand, mit dem Hauswacht gerade läuft – nach dem Speichern erst nach dem Neuladen gleich
        "loaded_revision": main.loaded_revision,
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
        "always": {
            "zones": list(always.zones),
            "sensors": sorted(always.sensors),
            "sirens_enabled": always.sirens_enabled,
            "sirens": list(always.sirens),
            "siren_tone": always.tone or "burglar",
            "siren_volume": always.volume or "high",
            "reaction_time": always.reaction_time,
        },
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
        **build_alarm_notify_settings(hass, main),
        "rule_edit": build_rule_settings(hass, main),
        "people": build_people_settings(options, ha_users or []),
        "system": build_system_settings(hass, main),
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
    if action == "sirens_save":
        return save_sirens(
            options,
            {
                "sirens": list(data.get("sirens") or []),
                "sirens_hardware_enabled": bool(data.get("hardware_enabled")),
                "sirens_allow_switch": bool(data.get("allow_switch")),
                "confirm_hardware": bool(data.get("confirm_hardware")),
            },
        )
    if action == "notify_save":
        return save_notify_settings(options, data)
    if action == "notify_text_save":
        lang = "de" if (hass.config.language or "").startswith("de") else "en"
        return save_event_text(
            options,
            str(data.get("event")),
            str(data.get("title") or ""),
            str(data.get("message") or ""),
            lang=lang,
        )
    if action == "rule_save":
        raw: Any = data.get("rule")
        if data.get("yaml") is not None:
            try:
                raw = parse_yaml(str(data["yaml"]))
            except HomeAssistantError as err:
                return Change(errors={"base": "rule_yaml_invalid"}, details={"message": str(err)})
        profiles = data.get("profiles")
        return save_rule(
            options,
            data.get("id") or None,
            raw,
            labels=labels,
            profiles=list(profiles) if isinstance(profiles, list) else None,
        )
    if action == "siren_tone_save":
        siren = str(data.get("siren") or "")
        executor = getattr(main, "sirens", None)
        device = executor.devices().get(siren) if executor is not None else None
        return save_siren_tone(
            options,
            siren,
            str(data.get("tone") or ""),
            allow_fire=bool(data.get("allow_fire_tone")),
            confirm_fire=bool(data.get("confirm_fire_tone")),
            smoke_detector=bool(device and device.fire_detector),
        )
    if action == "speech_event_save":
        lang = "de" if (hass.config.language or "").startswith("de") else "en"
        return save_speech_event(options, str(data.get("event")), data, lang=lang)
    if action == "control_save":
        payload = dict(data)
        if payload.get("kind") == "keypad":
            # Ohne eigenes Topic: aus dem gewählten Zigbee2MQTT-Gerät bilden (wie im Dialog)
            topic = str(payload.get("topic") or "").strip().rstrip("/")
            if not topic or topic == "zigbee2mqtt":
                topic = keypad_topic(hass, payload.get("keypad_device"))
            payload["topic"] = topic
        return save_control(options, payload.get("id") or None, payload)
    if action in SIMPLE_ACTIONS:
        return SIMPLE_ACTIONS[action](options, data)
    if action in SLOW_ACTIONS:
        return SLOW_ACTIONS[action](options, data)
    if action == "rule_delete":
        return delete_rule(options, str(data.get("id")))
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
    if action != "always_save":
        return Change(errors={"base": "unknown_action"})
    sirens = data.get("sirens_settings")
    return save_always(
        options,
        zones=data.get("zones") or [],
        sensors=data.get("sensors") or [],
        sirens=sirens if isinstance(sirens, Mapping) else None,
    )


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): WS_GET})
@websocket_api.async_response
async def ws_settings_get(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    ha_users = await ha_user_choices(hass)
    main = _main(hass)
    if main is None:
        connection.send_error(msg["id"], "not_loaded", "Hauswacht ist nicht geladen.")
        return
    connection.send_result(msg["id"], build_settings(hass, main, ha_users))


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_APPLY,
        vol.Required("revision"): str,
        vol.Required("action"): vol.In(ACTIONS),
        vol.Optional("data", default={}): dict,
    }
)
@websocket_api.async_response
async def ws_settings_apply(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    main = _main(hass)
    if main is None:
        connection.send_error(msg["id"], "not_loaded", "Hauswacht ist nicht geladen.")
        return
    entry = main.entry
    data = dict(msg["data"])
    if msg["action"] == "user_save":
        data["valid_from"] = to_iso(data.get("valid_from"))
        data["valid_until"] = to_iso(data.get("valid_until"))
    if msg["action"] == "user_save" and not data.get("ha_user"):
        # Wie im Dialog: heißt der Benutzer wie ein Home-Assistant-Konto, wird er verknüpft
        name = str(data.get("name") or "").strip().casefold()
        data["ha_user"] = next(
            (u["id"] for u in await ha_user_choices(hass) if u["name"].casefold() == name), None
        )
    if not main.all_disarmed:
        connection.send_result(msg["id"], {"ok": False, "errors": {"base": "disarm_first"}})
        return
    if msg["revision"] != revision(entry.options):
        connection.send_result(msg["id"], {"ok": False, "errors": {"base": "changed_elsewhere"}})
        return
    if msg["action"] == "siren_from_switch":
        change = await _siren_from_switch(hass, entry.options, data)
    elif msg["action"] == "helper_create":
        change = await _helper_create(hass, entry.options, data)
    elif msg["action"] in SLOW_ACTIONS:
        # Nur reine Logik im Executor (keine Zugriffe auf Home Assistant)
        options = entry.options
        slow = SLOW_ACTIONS[msg["action"]]
        change = await hass.async_add_executor_job(slow, options, data)
        # Während des Rechnens kann sich etwas geändert haben
        if not main.all_disarmed or msg["revision"] != revision(entry.options):
            connection.send_result(
                msg["id"], {"ok": False, "errors": {"base": "changed_elsewhere"}}
            )
            return
    else:
        change = apply_change(hass, main, msg["action"], data)
    if not change.ok or change.options is None:
        connection.send_result(
            msg["id"],
            {"ok": False, "errors": dict(change.errors), "details": dict(change.details)},
        )
        return
    hass.config_entries.async_update_entry(entry, options=change.options)
    connection.send_result(
        msg["id"], {"ok": True, "revision": revision(entry.options), "id": change.item_id}
    )


async def _siren_from_switch(
    hass: HomeAssistant, options: Mapping[str, Any], data: Mapping[str, Any]
) -> Change:
    """Helfer „Gerätetyp eines Schalters ändern“ (Typ Sirene) anlegen und die Sirene eintragen.

    Legt nur einen Helfer an – der Schalter selbst wird nicht geschaltet (wie im Dialog).
    """
    if not data.get("confirm"):
        return Change(errors={"confirm": "siren_switch_confirm"})
    switch = str(data.get("switch") or "")
    if not switch.startswith("switch.") or hass.states.get(switch) is None:
        return Change(errors={"switch": "control_entity"})
    try:
        flow = await hass.config_entries.flow.async_init(
            "switch_as_x", context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            flow["flow_id"], {"entity_id": switch, "target_domain": "siren"}
        )
    except Exception:
        _LOGGER.exception("Helfer Schalter als Sirene konnte nicht angelegt werden")
        return Change(errors={"base": "helper_failed"})
    created = result.get("result")
    if result.get("type") != "create_entry" or created is None:
        return Change(errors={"base": "helper_failed"})
    sirens = [
        e.entity_id
        for e in er.async_entries_for_config_entry(er.async_get(hass), created.entry_id)
        if e.domain == "siren"
    ]
    if not sirens:
        return Change(errors={"base": "helper_failed"})
    return save_sirens(options, {"sirens": [*options.get("sirens", []), sirens[0]]})


async def _helper_create(
    hass: HomeAssistant, options: Mapping[str, Any], data: Mapping[str, Any]
) -> Change:
    """Melder aus Messwert: Schwellenwert-Helfer anlegen und gleich als Melder einsetzen.

    Wie im Dialog – legt nur einen neuen Helfer an, ändert nichts Bestehendes.
    """
    errors, payload = check_threshold_helper(options, data)
    if "source" not in errors and hass.states.get(str(data.get("source"))) is None:
        errors["source"] = "control_entity"
    if errors:
        return Change(errors=errors)
    try:
        flow = await hass.config_entries.flow.async_init(
            "threshold", context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(flow["flow_id"], payload)
    except Exception:
        _LOGGER.exception("Schwellenwert-Helfer konnte nicht angelegt werden")
        return Change(errors={"base": "helper_failed"})
    created = result.get("result")
    if result.get("type") != "create_entry" or created is None:
        return Change(errors={"base": "helper_failed"})
    # Entität vorab im Register anlegen, damit ihre ID sofort feststeht (wie im Dialog)
    entity_id = (
        er.async_get(hass)
        .async_get_or_create(
            "binary_sensor",
            "threshold",
            created.entry_id,
            suggested_object_id=payload["name"],
            config_entry=created,
        )
        .entity_id
    )
    return place_new_sensor(
        options,
        entity_id,
        str(data.get("type") or "technical"),
        str(data.get("target") or TARGET_ALWAYS),
    )


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): WS_NEW_CARDS})
@callback
def ws_new_cards(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Karten anlernen: zuletzt gelesene unbekannte Karten (die Seite fragt alle paar Sekunden)."""
    main = _main(hass)
    if main is None:
        connection.send_error(msg["id"], "not_loaded", "Hauswacht ist nicht geladen.")
        return
    connection.send_result(msg["id"], build_cards(hass, main))


@callback
def async_register_settings_websocket(hass: HomeAssistant) -> None:
    if hass.data.get(DATA_WS):
        return
    websocket_api.async_register_command(hass, ws_settings_get)
    websocket_api.async_register_command(hass, ws_settings_apply)
    websocket_api.async_register_command(hass, ws_rule_check)
    websocket_api.async_register_command(hass, ws_new_cards)
    async_register_advisor_websocket(hass)
    async_register_goals_websocket(hass)
    hass.data[DATA_WS] = True
