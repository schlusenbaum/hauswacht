"""Integrationstests: Websocket-Befehle der Einstellungsseite (ADR 0011 Stufe 2).

Nur Einstellungen werden geändert; es werden keine Sirenen oder Geräte angesprochen.
"""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from .conftest import DOOR, MOTION, PANEL, WINDOW, make_entry, setup_entry


async def _ws(hass_ws_client: Any, hass: HomeAssistant, **msg: Any) -> dict[str, Any]:
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(msg)
    response = await client.receive_json()
    assert response["success"], response
    return response["result"]  # type: ignore[no-any-return]


def _options(hass: HomeAssistant) -> Any:
    return hass.config_entries.async_entries("hauswacht")[0].options


async def test_get_lists_groups_and_entities(hass: HomeAssistant, hass_ws_client: Any) -> None:
    await setup_entry(hass, make_entry())
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    assert data["editable"] is True
    assert {g["id"] for g in data["groups"]} == {"aussen", "keller"}
    assert data["sensor_types"][DOOR] == "door"
    assert any(e["id"] == WINDOW for e in data["entities"])
    assert len(data["revision"]) == 16


async def test_apply_saves_group_with_types(hass: HomeAssistant, hass_ws_client: Any) -> None:
    await setup_entry(hass, make_entry())
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    result = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="group_save",
        data={
            "id": "keller",
            "name": "Keller",
            "entities": [MOTION],
            "types": {MOTION: "door"},
        },
    )
    assert result["ok"] is True
    await hass.async_block_till_done()
    assert _options(hass)["sensor_types"][MOTION] == "door"
    # Die alte Revision gilt nicht mehr
    again = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="group_delete",
        data={"id": "keller"},
    )
    assert again == {"ok": False, "errors": {"base": "changed_elsewhere"}}


async def test_apply_reports_field_errors(hass: HomeAssistant, hass_ws_client: Any) -> None:
    await setup_entry(hass, make_entry())
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    result = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="group_save",
        data={"name": "Doppelt", "entities": [DOOR]},
    )
    assert result["ok"] is False
    assert result["errors"] == {"base": "zone_overlap"}
    assert result["details"]["conflicts"] == {DOOR: "Außen"}


async def test_apply_refused_while_armed(hass: HomeAssistant, hass_ws_client: Any) -> None:
    await setup_entry(hass, make_entry())
    await hass.services.async_call(
        "hauswacht", "arm", {"entity_id": PANEL, "profile": "home"}, blocking=True
    )
    await hass.async_block_till_done()
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    assert data["editable"] is False
    result = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="group_delete",
        data={"id": "keller"},
    )
    assert result == {"ok": False, "errors": {"base": "disarm_first"}}
    assert "keller" in _options(hass)["zones"]


async def test_apply_special_and_always(hass: HomeAssistant, hass_ws_client: Any) -> None:
    hass.states.async_set("input_number.test", "0")
    await setup_entry(hass, make_entry())
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    result = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="strength_save",
        data={"entity": "input_number.test", "threshold": 25, "group": "keller"},
    )
    assert result["ok"] is True
    await hass.async_block_till_done()
    assert "input_number.test" in _options(hass)["zones"]["keller"]["entities"]
    # Nach dem Neuladen holt die Seite die Einstellungen (und die Revision) neu
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    result = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="always_save",
        data={"zones": [], "sensors": [WINDOW]},
    )
    assert result["ok"] is True, result
    await hass.async_block_till_done()
    assert _options(hass)["always_active"]["sensors"] == [WINDOW]


async def test_apply_sensor_excluded_in_profile(hass: HomeAssistant, hass_ws_client: Any) -> None:
    await setup_entry(hass, make_entry())
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    assert {p["id"] for p in data["profiles"]} >= {"home", "night"}
    result = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="sensor_save",
        data={"entity": MOTION, "group": "keller", "type": "motion", "excluded": ["night"]},
    )
    assert result["ok"] is True, result
    await hass.async_block_till_done()
    assert _options(hass)["profiles"]["night"]["excluded"] == [MOTION]


async def test_apply_profile_save_new_and_delete(hass: HomeAssistant, hass_ws_client: Any) -> None:
    await setup_entry(hass, make_entry())
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    edit = data["profile_edit"]
    night = next(p for p in edit["profiles"] if p["id"] == "night")
    changed = {**night, "entry_delay": 45, "excluded": [MOTION]}
    result = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="profile_save",
        data=changed,
    )
    assert result["ok"] is True, result
    await hass.async_block_till_done()
    stored = _options(hass)["profiles"]["night"]
    assert stored["entry_delay"] == 45
    assert stored["excluded"] == [MOTION]
    # Neues Profil aus den Vorgaben; gleicher Knopf wie "Nacht" wird abgelehnt
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    new = {**data["profile_edit"]["defaults"], "name": "Garten", "panel_mode": "night"}
    refused = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="profile_save",
        data=new,
    )
    assert refused["errors"] == {"panel_mode": "panel_mode_taken"}
    new["panel_mode"] = "none"
    new["zones"] = ["aussen"]
    created = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="profile_save",
        data=new,
    )
    assert created["ok"] is True, created
    await hass.async_block_till_done()
    assert _options(hass)["profiles"]["garten"]["zones"] == ["aussen"]
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    deleted = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="profile_delete",
        data={"id": "garten"},
    )
    assert deleted["ok"] is True
    await hass.async_block_till_done()
    assert "garten" not in _options(hass)["profiles"]
