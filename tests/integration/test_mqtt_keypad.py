"""Integrationstests: MQTT-Schnittstelle (ADR 0012, Stufe 3).

MQTT ist gemockt (mqtt_mock). Das „Gerät“ sind nur Nachrichten auf hauswacht/flur/set.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import async_fire_mqtt_message
from pytest_homeassistant_custom_component.typing import MqttMockHAClient

from custom_components.hauswacht.core.pin import hash_pin

from .conftest import PANEL, WINDOW, make_entry, set_sensor, setup_entry

BASE = "hauswacht/flur"
PIN = "1357"

# Der MQTT-Mock startet einen periodischen Timer, der nach dem Test noch läuft.
pytestmark = pytest.mark.parametrize("expected_lingering_timers", [True])


async def _setup(hass: HomeAssistant, **interface: Any) -> None:
    hashed = hash_pin(PIN)
    options = {
        "users": {"anna": {"name": "Anna", "pin_salt": hashed.salt, "pin_digest": hashed.digest}},
        "controls": {
            "tablet": {
                "name": "Tablet Flur",
                "kind": "mqtt_keypad",
                "topic": BASE,
                "buttons": {"arm_night": "night", "arm_away": "away"},
                **interface,
            }
        },
    }
    await setup_entry(hass, make_entry(options))


async def _send(hass: HomeAssistant, payload: str, *, retain: bool = False) -> None:
    async_fire_mqtt_message(hass, f"{BASE}/set", payload, retain=retain)
    await hass.async_block_till_done()
    await hass.async_block_till_done()


def _published(mqtt_mock: MqttMockHAClient, suffix: str) -> list[tuple[str, bool]]:
    return [
        (call.args[1], bool(call.args[3]) if len(call.args) > 3 else False)
        for call in mqtt_mock.async_publish.call_args_list
        if call.args[0] == f"{BASE}/{suffix}"
    ]


def _responses(mqtt_mock: MqttMockHAClient) -> list[dict[str, Any]]:
    return [json.loads(p) for p, _ in _published(mqtt_mock, "response")]


def _panel(hass: HomeAssistant) -> str:
    state = hass.states.get(PANEL)
    assert state is not None
    return state.state


async def test_online_and_state_published(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> None:
    await _setup(hass)
    assert ("online", True) in _published(mqtt_mock, "availability")
    assert ("disarmed", True) in _published(mqtt_mock, "state")
    attributes = json.loads(_published(mqtt_mock, "attributes")[-1][0])
    assert attributes["display"] == "disarmed"
    assert PIN not in json.dumps(attributes)


async def test_json_command_with_pin_and_response(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    await _setup(hass)
    await _send(hass, json.dumps({"action": "ARM_NIGHT", "code": PIN, "id": 7}))
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    assert _responses(mqtt_mock)[-1] | {"open_sensors": []} == {
        "keypad": "tablet",
        "result": "ok",
        "display": "armed_night",
        "open_sensors": [],
        "can_force": False,
        "lock_seconds": 0,
        "id": 7,
    }
    assert ("armed_night", True) in _published(mqtt_mock, "state")
    # Unscharf als Text ohne PIN: abgelehnt
    await _send(hass, "DISARM")
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    assert _responses(mqtt_mock)[-1]["result"] == "invalid_code"
    await _send(hass, json.dumps({"action": "DISARM", "code": PIN}))
    assert _panel(hass) == AlarmControlPanelState.DISARMED


async def test_retained_command_is_ignored(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    await _setup(hass)
    await _send(hass, json.dumps({"action": "ARM_NIGHT", "code": PIN}), retain=True)
    assert _panel(hass) == AlarmControlPanelState.DISARMED
    assert _responses(mqtt_mock) == []


async def test_not_ready_and_own_words(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> None:
    await _setup(hass, words={"armed_night": "NACHT"}, code_field="pin")
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    await _send(hass, json.dumps({"action": "arm night", "pin": PIN}))
    answer = _responses(mqtt_mock)[-1]
    assert answer["result"] == "not_ready"
    assert answer["open_sensors"]
    set_sensor(hass, WINDOW, "off")
    await hass.async_block_till_done()
    await _send(hass, json.dumps({"action": "ARM_NIGHT", "pin": PIN}))
    assert ("NACHT", True) in _published(mqtt_mock, "state")


async def test_unknown_word_is_unknown_button(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    await _setup(hass)
    await _send(hass, json.dumps({"action": "ARM_VACATION", "code": PIN}))
    assert _responses(mqtt_mock)[-1]["result"] == "unknown_button"
    assert _panel(hass) == AlarmControlPanelState.DISARMED
