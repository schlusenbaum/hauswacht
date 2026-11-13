"""Integrationstests: Alarmkarte – Schalten über das angemeldete Konto, PIN nur wo verlangt."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockUser
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.hauswacht.core.pin import hash_pin

from .conftest import PANEL, WINDOW, make_entry, set_sensor, setup_entry

PIN = "1357"


def _anna(ha_user: str | None = None, **extra: Any) -> dict[str, Any]:
    pin = hash_pin(PIN)
    data: dict[str, Any] = {"name": "Anna", "pin_salt": pin.salt, "pin_digest": pin.digest}
    if ha_user:
        data["ha_user"] = ha_user
    data.update(extra)
    return {"anna": data}


async def _ws(client: Any, **msg: Any) -> dict[str, Any]:
    await client.send_json_auto_id(msg)
    reply = await client.receive_json()
    assert reply["success"], reply
    return reply["result"]  # type: ignore[no-any-return]


async def _action(client: Any, action: str, **extra: Any) -> dict[str, Any]:
    return await _ws(client, type="hauswacht/alarm/action", area="main", action=action, **extra)


async def test_without_pins_card_switches_freely(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    await setup_entry(hass, make_entry())
    client = await hass_ws_client(hass)
    info = await _ws(client, type="hauswacht/alarm/info")
    assert info["pin"] is False
    area = info["areas"][0]
    assert area["entity_id"] == PANEL
    assert "night" in {p["id"] for p in area["profiles"]}
    assert area["pin"] == {"arm": False, "disarm": False, "end_alarm": False}

    assert (await _action(client, "arm", profile="night"))["ok"]
    await hass.async_block_till_done()
    assert hass.states.get(PANEL).state == "armed_night"
    assert (await _action(client, "disarm"))["ok"]
    await hass.async_block_till_done()
    assert hass.states.get(PANEL).state == "disarmed"


async def test_linked_account_needs_no_pin(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, hass_admin_user: MockUser
) -> None:
    await setup_entry(hass, make_entry({"users": _anna(hass_admin_user.id)}))
    client = await hass_ws_client(hass)
    info = await _ws(client, type="hauswacht/alarm/info")
    assert info["pin"] is False
    assert info["user"] == "Anna"
    assert (await _action(client, "arm", profile="night"))["ok"]
    await hass.async_block_till_done()
    assert hass.states.get(PANEL).attributes["changed_by"] == "Anna"
    assert (await _action(client, "disarm"))["ok"]
    await hass.async_block_till_done()
    assert hass.states.get(PANEL).state == "disarmed"


async def test_unlinked_account_needs_pin(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    await setup_entry(hass, make_entry({"users": _anna()}))
    client = await hass_ws_client(hass)
    info = await _ws(client, type="hauswacht/alarm/info")
    assert info["pin"] is True
    assert info["areas"][0]["pin"]["disarm"] is True
    assert info["areas"][0]["pin"]["arm"] is False  # Scharf nur mit PIN, wenn so eingestellt

    assert (await _action(client, "arm", profile="night"))["ok"]
    await hass.async_block_till_done()
    missing = await _action(client, "disarm")
    assert missing["ok"] is False
    assert missing["error"] == "card_pin_required"
    wrong = await _action(client, "disarm", code="0000")
    assert wrong["error"] == "invalid_code"
    assert (await _action(client, "disarm", code=PIN))["ok"]
    await hass.async_block_till_done()
    assert hass.states.get(PANEL).state == "disarmed"
    assert hass.states.get(PANEL).attributes["changed_by"] == "Anna"


async def test_pin_rule_for_unlinked_accounts_can_be_switched_off(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    await setup_entry(hass, make_entry({"users": _anna(), "card_pin_unlinked": False}))
    client = await hass_ws_client(hass)
    assert (await _ws(client, type="hauswacht/alarm/info"))["pin"] is False


async def test_linked_account_with_card_pin(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, hass_admin_user: MockUser
) -> None:
    users = _anna(hass_admin_user.id, card_pin=True)
    await setup_entry(hass, make_entry({"users": users}))
    client = await hass_ws_client(hass)
    assert (await _ws(client, type="hauswacht/alarm/info"))["pin"] is True
    assert (await _action(client, "arm", profile="night"))["ok"]
    await hass.async_block_till_done()
    assert (await _action(client, "disarm"))["error"] == "card_pin_required"


async def test_rights_of_linked_user_apply(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, hass_admin_user: MockUser
) -> None:
    users = _anna(hass_admin_user.id, can_disarm=False)
    await setup_entry(hass, make_entry({"users": users}))
    client = await hass_ws_client(hass)
    info = await _ws(client, type="hauswacht/alarm/info")
    assert info["areas"][0]["may"] == {"arm": True, "disarm": False, "end_alarm": True}
    assert (await _action(client, "arm", profile="night"))["ok"]
    await hass.async_block_till_done()
    denied = await _action(client, "disarm")
    assert denied["error"] == "action_not_allowed"
    assert hass.states.get(PANEL).state == "armed_night"


async def test_open_sensor_asks_and_can_be_forced(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    entry = make_entry({"profiles": {"night": {"open_policy": "confirm"}}})
    await setup_entry(hass, entry)
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    client = await hass_ws_client(hass)
    asked = await _action(client, "arm", profile="night")
    assert asked["ok"] is False
    assert asked["can_force"] is True
    assert asked["message"]
    assert (await _action(client, "arm", profile="night", force=True))["ok"]
    await hass.async_block_till_done()
    assert hass.states.get(PANEL).state == "armed_night"


async def test_read_only_account_cannot_switch(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, hass_read_only_access_token: str
) -> None:
    await setup_entry(hass, make_entry())
    client = await hass_ws_client(hass, hass_read_only_access_token)
    info = await _ws(client, type="hauswacht/alarm/info")
    assert info["areas"] == []
    result = await _action(client, "arm", profile="night")
    assert result["error"] == "card_no_access"
    assert hass.states.get(PANEL).state == "disarmed"
