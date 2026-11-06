"""Integrationstests: "Unscharf" während eines Alarms beendet nur den Alarm."""

from __future__ import annotations

from typing import Any

from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import Context, HomeAssistant
from pytest_homeassistant_custom_component.common import MockUser, async_mock_service

from custom_components.hauswacht.const import PUSH_ACTION_EVENT

from .conftest import DOOR, PANEL, WINDOW, make_entry, set_sensor, setup_entry

PHONE = "mobile_app_testhandy"


async def _service(hass: HomeAssistant, domain: str, service: str, **data: Any) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)
    await hass.async_block_till_done()


def _state(hass: HomeAssistant) -> Any:
    state = hass.states.get(PANEL)
    assert state is not None
    return state


async def _alarm_by_window(hass: HomeAssistant) -> None:
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    assert _state(hass).state == AlarmControlPanelState.TRIGGERED


async def test_disarm_during_alarm_keeps_profile_armed(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    await _alarm_by_window(hass)

    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL)
    state = _state(hass)
    assert state.state == AlarmControlPanelState.ARMED_NIGHT
    assert state.attributes["bypassed_until_closed"] == [WINDOW]

    # offenes Fenster löst nicht erneut aus, die Tür schon
    set_sensor(hass, DOOR, "on")
    await hass.async_block_till_done()
    assert _state(hass).state == AlarmControlPanelState.PENDING

    # zweites Unscharf: wirklich unscharf
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL)
    assert _state(hass).state == AlarmControlPanelState.DISARMED


async def test_closed_sensor_is_monitored_again(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    await _alarm_by_window(hass)
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL)

    set_sensor(hass, WINDOW, "off")
    await hass.async_block_till_done()
    assert _state(hass).attributes["bypassed_until_closed"] == []
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    assert _state(hass).state == AlarmControlPanelState.TRIGGERED


async def test_push_button_during_alarm_ends_alarm(
    hass: HomeAssistant, hass_admin_user: MockUser
) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    options = {"push_disarm": True, "profiles": {"night": {"notify": [PHONE]}}}
    await setup_entry(hass, make_entry(options))
    await _alarm_by_window(hass)

    action = push[0].data["data"]["actions"][0]
    assert action["title"] == "Alarm beenden"
    hass.bus.async_fire(
        PUSH_ACTION_EVENT,
        {"action": action["action"]},
        context=Context(user_id=hass_admin_user.id),
    )
    await hass.async_block_till_done()
    assert _state(hass).state == AlarmControlPanelState.ARMED_NIGHT
    messages = [c.data["message"] for c in push[1:]]
    assert "clear_notification" in messages
    assert any("Alarm beendet von" in m and "bleibt scharf" in m for m in messages)


# --- Knöpfe "Unscharf schalten" und "Alarm beenden" --------------------------

DISARM_NOW = "button.hauswacht_disarm_now"
END_ALARM = "button.hauswacht_end_alarm"


async def test_disarm_button_disarms_even_during_alarm(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    await _alarm_by_window(hass)
    await _service(hass, "button", "press", entity_id=DISARM_NOW)
    state = _state(hass)
    assert state.state == AlarmControlPanelState.DISARMED
    assert state.attributes["bypassed_until_closed"] == []


async def test_disarm_button_when_armed(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    await _service(hass, "button", "press", entity_id=DISARM_NOW)
    assert _state(hass).state == AlarmControlPanelState.DISARMED


async def test_end_alarm_button_keeps_armed(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    await _alarm_by_window(hass)
    await _service(hass, "button", "press", entity_id=END_ALARM)
    assert _state(hass).state == AlarmControlPanelState.ARMED_NIGHT
    # außerhalb eines Alarms bewirkt der Knopf nichts
    await _service(hass, "button", "press", entity_id=END_ALARM)
    assert _state(hass).state == AlarmControlPanelState.ARMED_NIGHT


async def test_buttons_unavailable_with_pin(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "code"}
    )
    flow = await hass.config_entries.options.async_configure(flow["flow_id"], {"new_pin": "2468"})
    await hass.async_block_till_done()
    for entity_id in (DISARM_NOW, END_ALARM):
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.state == "unavailable"
