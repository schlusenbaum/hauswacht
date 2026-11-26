"""Integrationstests: Konfiguration herunterladen (ADR 0019).

Der Befehl liest nur; es werden keine Sirenen oder Geräte angesprochen.
"""

from __future__ import annotations

import json
import re
from typing import Any

from homeassistant.core import HomeAssistant

from .conftest import make_entry, setup_entry

ANNA = "person.anna"
PHONE = "device_tracker.handy_von_anna"
SIGNAL = "sensor.anna_wlan"


def _setup_states(hass: HomeAssistant) -> None:
    hass.states.async_set(
        ANNA, "not_home", {"friendly_name": "Anna Beispiel", "device_trackers": [PHONE]}
    )
    hass.states.async_set(
        PHONE,
        "not_home",
        {
            "friendly_name": "Handy von Anna",
            "source_type": "gps",
            "latitude": 52.123456,
            "longitude": 9.654321,
            "gps_accuracy": 12,
        },
    )
    hass.states.async_set(SIGNAL, "FritzBox Beispiel", {"friendly_name": "WLAN Anna"})


OPTIONS = {
    "homecoming_persons": [ANNA],
    "homecoming_signals": {ANNA: [SIGNAL]},
    "homecoming_ssids": ["FritzBox Beispiel"],
    "notify_system": ["notify.mobile_app_handy_von_anna"],
    "users": {
        "clara": {
            "name": "Clara Muster",
            "pin_salt": "c2FsdHNhbHQ",
            "pin_digest": "0123456789abcdef",
            "tags": ["04A1B2C3D4"],
        }
    },
}


async def _export(hass: HomeAssistant, hass_ws_client: Any, token: str | None = None) -> Any:
    client = await (hass_ws_client(hass, token) if token else hass_ws_client(hass))
    await client.send_json_auto_id({"type": "hauswacht/export", "language": "de"})
    return await client.receive_json()


async def test_export_has_everything_but_no_real_values(
    hass: HomeAssistant, hass_ws_client: Any
) -> None:
    _setup_states(hass)
    await setup_entry(hass, make_entry(OPTIONS))
    response = await _export(hass, hass_ws_client)
    assert response["success"], response
    result = response["result"]
    assert result["filename"].startswith("hauswacht-konfiguration-")
    data = result["data"]
    for section in (
        "versions",
        "options",
        "overview",
        "presence",
        "facts",
        "measurements",
        "findings",
        "scenarios",
        "entities",
    ):
        assert section in data, section
        assert not (isinstance(data[section], dict) and "error" in data[section]), data[section]
    # Struktur bleibt, Werte sind Platzhalter
    options = data["options"]
    assert options["homecoming_persons"] == ["person.person_1"]
    assert options["homecoming_signals"] == {"person.person_1": ["sensor.person_1_wlan"]}
    assert options["homecoming_ssids"] == ["wlan_1"]
    assert options["notify_system"] == ["notify.empfaenger_1"]
    user = options["users"]["benutzer_1"]
    assert user["name"] == "Benutzer 1"
    assert user["pin_digest"] == "***"
    assert user["tags"] == ["karte_1"]
    # Ortung: Zustand ja, Koordinaten nie
    tracker = data["entities"]["referenced"]["device_tracker.handy_von_person_1"]
    assert tracker["has_coordinates"] is True
    assert tracker["attributes"]["source_type"] == "gps"
    assert "latitude" not in tracker["attributes"]
    # Eigene Entitäten von Hauswacht sind dabei
    assert any(e.startswith("alarm_control_panel.") for e in data["entities"]["hauswacht"])
    # Nirgends ein echter Wert
    text = json.dumps(data, ensure_ascii=False)
    for secret in (
        "Anna",
        "Beispiel",
        "Clara",
        "Muster",
        "FritzBox",
        "mobile_app",
        "c2FsdHNhbHQ",
        "0123456789abcdef",
        "04A1B2C3D4",
        "52.12",
        "9.65",
    ):
        assert re.search(rf"(?<![^\W\d_]){re.escape(secret)}", text, re.I) is None, secret


async def test_export_only_for_admins(
    hass: HomeAssistant, hass_ws_client: Any, hass_read_only_access_token: str
) -> None:
    await setup_entry(hass, make_entry())
    response = await _export(hass, hass_ws_client, hass_read_only_access_token)
    assert response["success"] is False
    assert response["error"]["code"] == "unauthorized"
