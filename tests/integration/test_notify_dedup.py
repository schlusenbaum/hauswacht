"""Integrationstests: jedes Ereignis nur eine Nachricht, alte Nachrichten verschwinden.

notify-Dienste sind ATTRAPPEN, Sensoren und Indikatoren nur Testzustände. Keine Sirenen.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import Context, HomeAssistant, ServiceCall
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockUser,
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.hauswacht.automation_runner import REASON_TIME
from custom_components.hauswacht.const import PUSH_ACTION_EVENT, PUSH_STATE_TAG, PUSH_TAG

from .conftest import PANEL, WINDOW, make_entry, set_sensor, setup_entry

PHONE = "mobile_app_testhandy"
Z2M = "binary_sensor.zigbee2mqtt_bridge_connection_state"
STATE_TAG = f"{PUSH_STATE_TAG}_main"
LOST_TAG = f"hauswacht_lost_{WINDOW}"


async def _service(hass: HomeAssistant, domain: str, service: str, **data: Any) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)
    await hass.async_block_till_done()


async def _later(hass: HomeAssistant, seconds: float) -> None:
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=seconds))
    await hass.async_block_till_done()


def _panel(hass: HomeAssistant) -> str:
    state = hass.states.get(PANEL)
    assert state is not None
    return state.state


def _messages(calls: list[ServiceCall]) -> list[ServiceCall]:
    return [c for c in calls if c.data["message"] != "clear_notification"]


def _clears(calls: list[ServiceCall]) -> list[str]:
    return [c.data["data"]["tag"] for c in calls if c.data["message"] == "clear_notification"]


def _tag(call: ServiceCall) -> str | None:
    return call.data.get("data", {}).get("tag")


# --- Automatisch scharf/unscharf: eine Nachricht statt zwei ------------------


async def test_auto_arm_and_disarm_one_message_each(hass: HomeAssistant) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    options = {
        "notify_system": [PHONE],
        "events": {
            "armed": {"enabled": True, "targets": []},
            "disarmed": {"enabled": True, "targets": []},
        },
    }
    entry = make_entry(options)
    await setup_entry(hass, entry)
    runner = entry.runtime_data.automation

    runner.auto_arm("night", REASON_TIME)
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    messages = _messages(push)
    assert len(messages) == 1
    assert "armed" in messages[0].data["title"].lower()
    assert "automatically" in messages[0].data["message"]
    assert _tag(messages[0]) == STATE_TAG

    runner.auto_disarm("night", REASON_TIME)
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.DISARMED
    messages = _messages(push)
    assert len(messages) == 2
    assert "disarmed automatically" in messages[1].data["message"]
    assert _tag(messages[1]) == STATE_TAG  # ersetzt die Scharf-Nachricht


async def test_auto_arm_without_armed_event_sends_automation_message(
    hass: HomeAssistant,
) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    entry = make_entry({"notify_system": [PHONE]})  # "Scharf/Unscharf geschaltet" aus
    await setup_entry(hass, entry)
    runner = entry.runtime_data.automation

    runner.auto_arm("night", REASON_TIME)
    await hass.async_block_till_done()
    runner.auto_disarm("night", REASON_TIME)
    await hass.async_block_till_done()
    messages = _messages(push)
    assert [m.data["title"] for m in messages] == [
        "Hauswacht: armed automatically",
        "Hauswacht: disarmed automatically",
    ]
    assert all(_tag(m) == STATE_TAG for m in messages)


async def test_auto_arm_with_exit_delay_reports_once_when_armed(hass: HomeAssistant) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    options = {"notify_system": [PHONE], "events": {"armed": {"enabled": True, "targets": []}}}
    entry = make_entry(options)
    await setup_entry(hass, entry)

    entry.runtime_data.automation.auto_arm("away", REASON_TIME)
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.ARMING
    assert _messages(push) == []
    await _later(hass, 61)
    assert _panel(hass) == AlarmControlPanelState.ARMED_AWAY
    messages = _messages(push)
    assert len(messages) == 1
    assert "automatically" in messages[0].data["message"]


async def test_manual_arm_after_failed_auto_arm_is_not_automatic(hass: HomeAssistant) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    options = {"notify_system": [PHONE], "events": {"armed": {"enabled": True, "targets": []}}}
    entry = make_entry(options)
    await setup_entry(hass, entry)
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    entry.runtime_data.automation.auto_arm("night", REASON_TIME)  # Fenster offen: scheitert
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.DISARMED
    set_sensor(hass, WINDOW, "off")
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    armed = [m for m in _messages(push) if m.data["title"] == "Hauswacht: armed"]
    assert len(armed) == 1
    assert "automatically" not in armed[0].data["message"]


# --- Unscharf über den Push-Knopf -------------------------------------------


async def test_push_disarm_reply_replaces_armed_message(
    hass: HomeAssistant, hass_admin_user: MockUser
) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    options = {
        "push_disarm": True,
        "profiles": {"night": {"notify": [PHONE], "entry_delay": 30}},
        "events": {"armed": {"enabled": True, "targets": [PHONE]}},
    }
    await setup_entry(hass, make_entry(options))
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    set_sensor(hass, "binary_sensor.haustuer", "on")
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.PENDING
    action = next(a["action"] for c in push for a in c.data.get("data", {}).get("actions", []))
    hass.bus.async_fire(
        PUSH_ACTION_EVENT, {"action": action}, context=Context(user_id=hass_admin_user.id)
    )
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.DISARMED
    reply = _messages(push)[-1]
    assert "push button" in reply.data["message"]
    assert _tag(reply) == STATE_TAG  # ersetzt "scharf", bleibt nicht zusätzlich stehen
    assert STATE_TAG not in _clears(push)


# --- Ausgefallene Melder ----------------------------------------------------


async def test_sensor_lost_once_and_cleared_when_back(hass: HomeAssistant) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    await setup_entry(hass, make_entry({"notify_system": [PHONE]}))
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)

    set_sensor(hass, WINDOW, "unavailable")
    await hass.async_block_till_done()
    assert _messages(push) == []  # erst nach kurzer Wartezeit
    await _later(hass, 11)
    lost = _messages(push)
    assert len(lost) == 1
    assert _tag(lost[0]) == LOST_TAG
    assert "binary_sensor." not in lost[0].data["message"]  # Name statt Entitäts-ID

    # Nochmal weg ohne Wiederkehr: keine zweite Nachricht
    set_sensor(hass, WINDOW, "unknown")
    await hass.async_block_till_done()
    await _later(hass, 11)
    assert len(_messages(push)) == 1

    set_sensor(hass, WINDOW, "off")
    await hass.async_block_till_done()
    assert LOST_TAG in _clears(push)
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_sensor_back_quickly_sends_nothing(hass: HomeAssistant) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    await setup_entry(hass, make_entry({"notify_system": [PHONE]}))
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    set_sensor(hass, WINDOW, "unavailable")
    await hass.async_block_till_done()
    set_sensor(hass, WINDOW, "off")
    await hass.async_block_till_done()
    await _later(hass, 11)
    assert _messages(push) == []


async def test_infrastructure_fault_replaces_single_sensor_messages(hass: HomeAssistant) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    hass.states.async_set(Z2M, "on", {"device_class": "connectivity"})
    await setup_entry(hass, make_entry({"notify_system": [PHONE], "infrastructure": [Z2M]}))
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)

    set_sensor(hass, WINDOW, "unavailable")  # Melder zuerst, Bridge kurz danach
    await hass.async_block_till_done()
    hass.states.async_set(Z2M, "off", {"device_class": "connectivity"})
    await hass.async_block_till_done()
    await _later(hass, 11)
    messages = _messages(push)
    assert len(messages) == 1
    assert _tag(messages[0]) != LOST_TAG  # nur die Störung, nicht zusätzlich der Melder


# --- Alarm beendet, scharf bleibt --------------------------------------------


async def test_alarm_ended_replaces_alarm_message(
    hass: HomeAssistant, hass_admin_user: MockUser
) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    options = {"push_disarm": True, "profiles": {"night": {"notify": [PHONE]}}}
    await setup_entry(hass, make_entry(options))
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.TRIGGERED
    action = push[0].data["data"]["actions"][0]["action"]
    hass.bus.async_fire(
        PUSH_ACTION_EVENT, {"action": action}, context=Context(user_id=hass_admin_user.id)
    )
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    ended = _messages(push)[-1]
    assert "ended" in ended.data["title"].lower()
    assert _tag(ended) == PUSH_TAG  # ersetzt die Alarm-Nachricht
    assert _clears(push) == []

    set_sensor(hass, WINDOW, "off")
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL)
    assert PUSH_TAG in _clears(push)  # beim Unscharfschalten weg
