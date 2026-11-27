"""„Was wäre wenn“ für die Anwesenheit je Person (ADR 0021) – WebSocket für die Einstellungsseite.

Die Seite schickt ihren **Entwurf** (Signale, Haken, „Weggehen erkennen“) und bekommt zurück, was
mit diesen Einstellungen in den letzten 14 Tagen passiert wäre. Gerechnet wird mit den Messungen
der Heimkehr-Beobachtung – es wird nichts gespeichert, nichts geschaltet. Nur für Administratoren.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .core.automation import parse_automation
from .core.away_proof import parse_proof_settings
from .core.changes.system import save_homecoming
from .core.presence_rules import parse_presence_rules
from .core.presence_whatif import NIGHT, WhatIfInput, whatif
from .core.profiles import profile_ids, profile_info

WS_WHATIF = f"{DOMAIN}/presence/whatif"


def _main(hass: HomeAssistant) -> Any:
    for entry in hass.config_entries.async_loaded_entries(DOMAIN):
        runtime = getattr(entry, "runtime_data", None)
        if runtime is not None:
            return runtime
    return None


def _is_night(at: float) -> bool:
    return dt_util.as_local(dt_util.utc_from_timestamp(at)).hour in NIGHT


def build_whatif(main: Any, options: Mapping[str, Any]) -> dict[str, Any]:
    """Nachrechnung mit ``options`` (gespeichert oder Entwurf) auf den echten Messungen."""
    observer = getattr(main, "homecoming", None)
    if observer is None or not observer.enabled:
        return {"enabled": False}
    verdicts, doors = observer.whatif_data()
    raw = options.get("homecoming_signals", {})
    signals = {
        str(p): [e for e in entities if isinstance(e, str)]
        for p, entities in (raw.items() if isinstance(raw, Mapping) else [])
        if isinstance(entities, list)
    }
    profiles: dict[str, tuple[list[str], int]] = {}
    names: dict[str, str] = {}
    triggers: dict[str, str] = {}  # Profile mit eigenem Auslöser: keine Nachrechnung
    for pid in profile_ids(options):
        auto = parse_automation(options, pid)
        if auto.away_entity:
            triggers[pid] = profile_info(options, pid).name  # Personen zählen nicht (ADR 0018)
            continue
        if not auto.away_persons:
            continue
        profiles[pid] = (list(auto.away_persons), auto.away_delay)
        names[pid] = profile_info(options, pid).name
    result = whatif(
        WhatIfInput(
            verdicts=verdicts,
            doors=doors,
            persons=list(observer.persons),
            signals=signals,
            rules=parse_presence_rules(options),
            profiles=profiles,
            now=dt_util.utcnow().timestamp(),
            window=parse_proof_settings(options).weak_seconds,
            is_night=_is_night,
        )
    )
    for pid, entry in result["profiles"].items():
        entry["name"] = names.get(pid, pid)
    for person in result["persons"].values():
        pid = person.get("wait_profile")
        person["wait_profile_name"] = names.get(pid) if pid else None
    for pid, name in triggers.items():
        result["profiles"][pid] = {"observed": False, "trigger": True, "name": name}
    return {"enabled": True, **result}


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): WS_WHATIF, vol.Optional("data"): dict})
@callback
def ws_presence_whatif(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Was wäre mit diesem Entwurf passiert? Liest nur, speichert nichts."""
    main = _main(hass)
    if main is None:
        connection.send_error(msg["id"], "not_loaded", "Hauswacht ist nicht geladen.")
        return
    options: Mapping[str, Any] = main.entry.options
    draft = msg.get("data")
    if isinstance(draft, dict):
        change = save_homecoming(options, draft)  # dieselben Regeln wie beim Speichern
        if change.options is not None:
            options = change.options
    connection.send_result(msg["id"], build_whatif(main, options))


@callback
def async_register_whatif_websocket(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, ws_presence_whatif)
