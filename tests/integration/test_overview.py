"""Integrationstests: Anlagenübersicht, Prüfhinweise als Reparaturen, Diagnose-Datei."""

from __future__ import annotations

import json
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.hauswacht.const import DOMAIN
from custom_components.hauswacht.core.pin import hash_pin
from custom_components.hauswacht.diagnostics import async_get_config_entry_diagnostics

from .conftest import DOOR, MOTION, make_entry, setup_entry

PIN = "1357"
CARD = "041B4932E82880"


def _users() -> dict[str, Any]:
    pin = hash_pin(PIN)
    duress = hash_pin("9999")
    return {
        "anna": {
            "name": "Anna",
            "pin_salt": pin.salt,
            "pin_digest": pin.digest,
            "duress_salt": duress.salt,
            "duress_digest": duress.digest,
            "tags": [CARD],
        }
    }


OPTIONS: dict[str, Any] = {
    "users": _users(),
    "notify_system": ["mobile_app_annas_handy"],
    "rules": {
        "tuer_keller": {
            "name": "Tür, dann Keller",
            "result": "alarm",
            "steps": [{"any": [{"sensor": DOOR}], "within": 60}, {"any": [{"sensor": MOTION}]}],
        }
    },
}


async def test_overview_via_websocket(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    await setup_entry(hass, make_entry(OPTIONS))
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "hauswacht/overview"})
    msg = await client.receive_json()
    assert msg["success"], msg
    data = msg["result"]
    assert {p["name"] for p in data["profiles"]} >= {"Zuhause", "Nacht"}
    night = next(p for p in data["profiles"] if p["name"] == "Nacht")
    assert night["zones"] == ["Außen", "Keller"]
    door = next(s for s in data["sensors"] if s["entity_id"] == DOOR)
    assert door["profiles"]["night"] == "armed"
    assert door["type"] == "door"
    assert data["users"][0]["cards"] == ["…2880"]
    assert data["users"][0]["pin"] is True
    rule = data["rules"][0]
    assert rule["name"] == "Tür, dann Keller"
    assert rule["profiles"] == []
    codes = {f["code"] for f in data["findings"]}
    # Keine Sirene, aber ein Empfänger -> nur Hinweis; Bedrohungs-PIN ohne Empfänger -> wichtig
    assert "profile_no_siren" in codes
    assert "duress_no_targets" in codes
    assert "rule_unused" in codes
    # Nichts Geheimes in der Übersicht
    text = json.dumps(data, ensure_ascii=False)
    assert CARD not in text
    assert "pin_digest" not in text
    assert "salt" not in text
    assert "9999" not in text


async def test_overview_admin_only(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, hass_read_only_access_token: str
) -> None:
    await setup_entry(hass, make_entry(OPTIONS))
    client = await hass_ws_client(hass, hass_read_only_access_token)
    await client.send_json_auto_id({"type": "hauswacht/overview"})
    msg = await client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == "unauthorized"


async def test_important_findings_become_repairs(hass: HomeAssistant) -> None:
    entry = make_entry(OPTIONS)
    await setup_entry(hass, entry)
    reviewer = entry.runtime_data.reviewer
    assert reviewer is not None
    active = reviewer.refresh()
    assert "check_duress_no_targets" in active
    registry = ir.async_get(hass)
    issue = registry.async_get_issue(DOMAIN, "check_duress_no_targets")
    assert issue is not None
    assert issue.translation_key == "check_finding"
    assert "Bedrohungs-PIN" in (issue.translation_placeholders or {})["hint"]
    # Behoben: Empfänger eingetragen -> Hinweis verschwindet
    hass.config_entries.async_update_entry(
        entry, options={**entry.options, "duress_notify": ["mobile_app_annas_handy"]}
    )
    await hass.async_block_till_done()
    reviewer = entry.runtime_data.reviewer
    assert reviewer is not None
    assert "check_duress_no_targets" not in reviewer.refresh()
    assert registry.async_get_issue(DOMAIN, "check_duress_no_targets") is None


async def test_diagnostics_are_redacted(hass: HomeAssistant) -> None:
    entry = make_entry(OPTIONS)
    await setup_entry(hass, entry)
    data = await async_get_config_entry_diagnostics(hass, entry)
    text = json.dumps(data, ensure_ascii=False)
    assert "Anna" not in text
    assert CARD not in text
    assert "annas_handy" not in text
    assert "**REDACTED**" in text
    assert data["overview"]["profiles"]
