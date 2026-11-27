"""Konfiguration herunterladen (ADR 0019): ``hauswacht/export`` – alles für die Fehlersuche.

Sammelt in **eine** JSON-Datei, was man zum Nachvollziehen braucht: Versionen, alle Einstellungen,
die Anlagenübersicht, wer gerade als zuhause gilt und warum, die Fakten aus Home Assistant
(Ortung, Richtung, eingefrorene Ortungen), Messungen, Check-up, Szenarien und den Zustand der
beteiligten Entitäten.

Vor der Ausgabe ersetzt ``core/export.py`` Personen, Benutzer, Karten, Empfänger, Lautsprecher,
WLAN-Namen, MQTT-Topics, Geräte-IDs und Konten durch gleichbleibende Platzhalter; PIN-Hashes und
Aktions-Codes werden zu ``***``. Koordinaten kommen nie mit, nur „hat Koordinaten: ja/nein“.
Eine ungeschwärzte Fassung gibt es nicht.

Nur Administratoren. Der Befehl liest nur – er schaltet nichts und ändert nichts.
"""

from __future__ import annotations

import json
import platform
import re
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.const import __version__ as HA_VERSION
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.loader import async_get_integration
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .core.export import pseudonymize

WS_EXPORT = f"{DOMAIN}/export"
FORMAT = 1

# Von fremden Entitäten nur diese Attribute – nichts, was Orte oder Personen verrät
_ATTRIBUTES = (
    "device_class",
    "source_type",
    "in_zones",
    "gps_accuracy",
    "unit_of_measurement",
    "friendly_name",
    "device_trackers",
)
# Von eigenen Entitäten alles außer Ortsangaben und Bildern
_OWN_SKIP = frozenset({"latitude", "longitude", "entity_picture"})
_ENTITY = re.compile(r"\b[a-z_]+\.[a-z0-9_]+\b")


def _plain(value: Any) -> Any:
    """In JSON-taugliche Grundtypen umwandeln (Mengen sortiert, Datenklassen als dict)."""
    if is_dataclass(value) and not isinstance(value, type):
        return _plain(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, set | frozenset):
        return sorted((_plain(v) for v in value), key=str)
    if isinstance(value, list | tuple):
        return [_plain(v) for v in value]
    if isinstance(value, Enum):
        return value.value
    if value is None or isinstance(value, bool | int | float | str):
        return value
    return str(value)


def _safely(build: Any) -> Any:
    """Ein Abschnitt, der scheitert, soll nicht die ganze Datei verhindern."""
    try:
        return _plain(build())
    except Exception as err:
        return {"error": type(err).__name__, "message": str(err)}


def _has_coordinates(attributes: Mapping[str, Any]) -> bool:
    return isinstance(attributes.get("latitude"), int | float) and isinstance(
        attributes.get("longitude"), int | float
    )


def _state_row(hass: HomeAssistant, entity_id: str, own: bool) -> dict[str, Any] | None:
    state = hass.states.get(entity_id)
    entry = er.async_get(hass).async_get(entity_id)
    if state is None and entry is None:
        return None
    row: dict[str, Any] = {"platform": entry.platform if entry else None}
    if entry is not None and entry.disabled_by:
        row["disabled"] = True
    if state is None:
        row["state"] = None
        return row
    attributes = state.attributes
    if own:
        attrs = {k: v for k, v in attributes.items() if k not in _OWN_SKIP}
    else:
        attrs = {k: attributes[k] for k in _ATTRIBUTES if k in attributes}
    row.update(
        state=state.state,
        last_changed=state.last_changed.isoformat(),
        last_updated=state.last_updated.isoformat(),
        has_coordinates=_has_coordinates(attributes),
        attributes=_plain(attrs),
    )
    return row


def _referenced(hass: HomeAssistant, *parts: Any) -> list[str]:
    """Entitäten, die in den Einstellungen vorkommen, plus die Ortungen der Personen."""
    text = json.dumps(_plain(parts), ensure_ascii=False)
    found = [e for e in dict.fromkeys(_ENTITY.findall(text)) if hass.states.get(e) is not None]
    for entity_id in list(found):
        if entity_id.startswith("person."):
            trackers = hass.states.get(entity_id).attributes.get("device_trackers")  # type: ignore[union-attr]
            if isinstance(trackers, list):
                found.extend(t for t in trackers if isinstance(t, str))
    found.append("zone.home")
    return sorted(dict.fromkeys(found))


def _entities(hass: HomeAssistant, main: Any) -> dict[str, Any]:
    registry = er.async_get(hass)
    own = sorted(
        e.entity_id for e in er.async_entries_for_config_entry(registry, main.entry.entry_id)
    )
    others = [e for e in _referenced(hass, main.entry.options) if e not in own]
    result: dict[str, Any] = {"hauswacht": {}, "referenced": {}}
    for group, ids, is_own in (("hauswacht", own, True), ("referenced", others, False)):
        for entity_id in ids:
            if entity_id == "zone.home":
                state = hass.states.get(entity_id)
                result[group][entity_id] = {
                    "radius": state.attributes.get("radius") if state else None
                }
                continue
            if (row := _state_row(hass, entity_id, is_own)) is not None:
                result[group][entity_id] = row
    return result


async def build_export(hass: HomeAssistant, main: Any, language: str) -> dict[str, Any]:
    """Alles für die Fehlersuche – mit Platzhaltern statt echter Namen und Geheimnisse."""
    from .advisor_ws import build_facts, check  # noqa: PLC0415
    from .core.scenarios import scenarios  # noqa: PLC0415
    from .overview import build_overview  # noqa: PLC0415
    from .system_settings_ws import _measurements  # noqa: PLC0415

    integration = await async_get_integration(hass, DOMAIN)
    options = main.entry.options
    data = {
        "format": FORMAT,
        "created": dt_util.utcnow().isoformat(timespec="seconds"),
        "versions": {
            "hauswacht": str(integration.version),
            "home_assistant": HA_VERSION,
            "python": platform.python_version(),
            "entry": main.entry.version,
        },
        "language": language,
        "test_mode": bool(getattr(main.ctx, "test_mode", False)),
        "options": _plain(dict(options)),
        "overview": _safely(lambda: build_overview(main)),
        "presence": _safely(main.presence_overview),
        "facts": _safely(lambda: build_facts(hass, main, options)),
        "measurements": _safely(lambda: _measurements(main)),
        "findings": _safely(lambda: check(hass, main, options, language)),
        "scenarios": _safely(
            lambda: scenarios(options, build_facts(hass, main, options), language)
        ),
        "entities": _safely(lambda: _entities(hass, main)),
    }
    persons = {
        state.entity_id: str(state.attributes.get("friendly_name") or "")
        for state in hass.states.async_all("person")
    }
    return pseudonymize(data, persons)  # type: ignore[no-any-return]


def _filename() -> str:
    return f"hauswacht-konfiguration-{dt_util.now().strftime('%Y-%m-%d-%H%M')}"


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): WS_EXPORT, vol.Optional("language"): str})
@websocket_api.async_response
async def ws_export(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    from .advisor_ws import _language  # noqa: PLC0415
    from .settings_ws import _main  # noqa: PLC0415

    main = _main(hass)
    if main is None:
        connection.send_error(msg["id"], "not_loaded", "Hauswacht ist nicht geladen.")
        return
    language = _language(hass, msg.get("language"))
    data = await build_export(hass, main, language)
    connection.send_result(msg["id"], {"filename": _filename(), "data": data})


def async_register_export_websocket(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, ws_export)
