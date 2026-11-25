"""Gemeinsame Prüfung (ADR 0017): Fakten aus Home Assistant sammeln und der Websocket-Befehl.

Die Regeln stehen in ``core/advisor.py``. Hier wird nur eingesammelt, was dafür aus Home
Assistant kommt: wer geortet werden kann, wer ein Richtungs-Signal hat, die Eingangstüren je
Profil und die Messwerte der Heimkehr-Beobachtung.

``hauswacht/advisor/check`` prüft die gespeicherten Einstellungen – oder, mit ``action`` und
``data``, die Einstellungen, wie sie **nach** dieser Änderung wären. Gerechnet wird mit derselben
Logik wie beim Speichern (``apply_change``), gespeichert wird nichts. So zeigen die Seitenblätter
Hinweise schon vor dem Speichern. Der Befehl schaltet nichts und ändert nichts.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN
from .core.advisor import Facts, Measured, advise
from .core.automation import parse_automation
from .core.homecoming import DIRECTION_AWAY, DIRECTION_HOME, DIRECTION_NEUTRAL, door_proof_advice
from .core.homecoming import entry_stats as entry_stats_of
from .core.profiles import profile_behaviour, profile_ids
from .core.returning import parse_return
from .core.sensor_types import SensorType, default_type, excluded_sensors
from .core.sensors import parse_zones, resolve_zones
from .core.tilt import effective_types
from .names import plain_name
from .presence_proof import locatable
from .runtime import device_class_of, entities_by_label

WS_CHECK = f"{DOMAIN}/advisor/check"
# Nur diese Änderungen lassen sich vorab prüfen (Seitenblätter Profil und Anwesenheit)
CHECK_ACTIONS = ("profile_save", "homecoming_save")
_DIRECTIONS = DIRECTION_HOME | DIRECTION_AWAY | DIRECTION_NEUTRAL


def _signals(options: Mapping[str, Any], person: str) -> tuple[str, ...]:
    raw = options.get("homecoming_signals", {})
    entities = raw.get(person, []) if isinstance(raw, Mapping) else []
    return tuple(e for e in entities if isinstance(e, str))


def _persons(options: Mapping[str, Any]) -> list[str]:
    found = [p for p in options.get("homecoming_persons", []) if isinstance(p, str)]
    found.extend(p for p in options.get("away_proof_weak", []) or [] if isinstance(p, str))
    for pid in profile_ids(options):
        found.extend(parse_automation(options, pid).away_persons)
        found.extend(parse_return(options, pid).persons)
    return list(dict.fromkeys(found))


def _has_direction(hass: HomeAssistant, signals: tuple[str, ...]) -> bool:
    return any(
        (state := hass.states.get(entity_id)) is not None and state.state in _DIRECTIONS
        for entity_id in signals
    )


def _entry_doors(hass: HomeAssistant, options: Mapping[str, Any]) -> dict[str, tuple[str, ...]]:
    zones = parse_zones(options)
    labels = entities_by_label(hass)
    types = effective_types(options)
    result: dict[str, tuple[str, ...]] = {}
    for pid in profile_ids(options):
        members = resolve_zones(profile_behaviour(options, pid).zones, zones, labels)
        members -= excluded_sensors(options, pid)
        result[pid] = tuple(
            sorted(
                e
                for e in members
                if types.get(e, default_type(e, device_class_of(hass, e))) == SensorType.DOOR
            )
        )
    return result


def _measured(main: Any) -> tuple[dict[str, Measured], dict[str, Measured]]:
    observer = getattr(main, "homecoming", None)
    if observer is None or not observer.enabled:
        return {}, {}
    entry = {
        door: Measured(v["recommended_entry_delay"], v["max_seconds"], v["in_time"])
        for door, v in entry_stats_of(observer.entry_timings()).items()
        if v.get("recommended_entry_delay") is not None
    }
    proof = {
        person: Measured(v["recommended_entry_delay"], v["longest_after_door"], v["with_door"])
        for person, v in door_proof_advice(observer.stats()).items()
    }
    return entry, proof


def build_facts(hass: HomeAssistant, main: Any, options: Mapping[str, Any]) -> Facts:
    persons = _persons(options)
    entry, proof = _measured(main)
    doors = _entry_doors(hass, options)
    names = {p: plain_name(hass, p) for p in persons}
    names.update({d: plain_name(hass, d) for ids in doors.values() for d in ids})
    return Facts(
        located=frozenset(p for p in persons if locatable(hass, p, _signals(options, p))),
        direction=frozenset(p for p in persons if _has_direction(hass, _signals(options, p))),
        entry_doors=doors,
        entry_needed=entry,
        proof_needed=proof,
        names=names,
    )


def check(
    hass: HomeAssistant, main: Any, options: Mapping[str, Any], language: str
) -> list[dict[str, Any]]:
    return advise(options, build_facts(hass, main, options), language)


def _language(hass: HomeAssistant, wanted: str | None) -> str:
    if wanted in ("de", "en"):
        return wanted
    return "de" if (hass.config.language or "").startswith("de") else "en"


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_CHECK,
        vol.Optional("action"): vol.In(CHECK_ACTIONS),
        vol.Optional("data", default={}): dict,
        vol.Optional("language"): str,
    }
)
@callback
def ws_advisor_check(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    from .settings_ws import _main, apply_change  # noqa: PLC0415

    main = _main(hass)
    if main is None:
        connection.send_error(msg["id"], "not_loaded", "Hauswacht ist nicht geladen.")
        return
    options: Mapping[str, Any] = main.entry.options
    item = None
    if action := msg.get("action"):
        # Wie nach dem Speichern – berechnet, nicht gespeichert
        change = apply_change(hass, main, action, msg["data"])
        if not change.ok or change.options is None:
            connection.send_result(msg["id"], {"findings": [], "errors": dict(change.errors)})
            return
        options = change.options
        item = change.item_id  # z. B. die ID eines neuen Profils
    language = _language(hass, msg.get("language"))
    connection.send_result(
        msg["id"], {"findings": check(hass, main, options, language), "item": item}
    )


@callback
def async_register_advisor_websocket(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, ws_advisor_check)
