"""Integrationstests: immer aktive Melder und Scharf durch Schließen der Tür.

Alle Sensoren sind Testzustände, Sirenen und notify-Dienste sind ATTRAPPEN; die
Sirenen-Hardware ist nicht freigegeben.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import ServiceValidationError
from pytest_homeassistant_custom_component.common import (
    async_fire_time_changed,
    async_mock_service,
)

from .conftest import DOOR, PANEL, WINDOW, make_entry, set_sensor, setup_entry

SAFE = "binary_sensor.tresor"
PHONE = "mobile_app_testhandy"


async def _service(hass: HomeAssistant, domain: str, service: str, **data: Any) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)
    await hass.async_block_till_done()


def _panel(hass: HomeAssistant) -> str:
    state = hass.states.get(PANEL)
    assert state is not None
    return state.state


async def _safe(hass: HomeAssistant, state: str) -> None:
    hass.states.async_set(SAFE, state, {"device_class": "door"})
    await hass.async_block_till_done()


async def _wait(hass: HomeAssistant, freezer: FrozenDateTimeFactory, seconds: int) -> None:
    freezer.tick(timedelta(seconds=seconds))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


async def _setup(hass: HomeAssistant, **always: Any) -> list[Any]:
    push = async_mock_service(hass, "notify", PHONE)
    await _safe(hass, "off")
    options = {"notify_system": [PHONE], "always_active": {"sensors": [SAFE], **always}}
    await setup_entry(hass, make_entry(options))
    return push


async def test_disarmed_notification_only(hass: HomeAssistant) -> None:
    sirens = async_mock_service(hass, "siren", "turn_on")
    push = await _setup(hass)
    await _safe(hass, "on")
    assert _panel(hass) == AlarmControlPanelState.DISARMED
    assert sirens == []
    call = next(c for c in push if c.data["title"] == "Hauswacht: always-active sensor")
    assert call.data["data"]["push"]["interruption-level"] == "critical"


async def test_disarmed_with_sirens_alarm_and_back_to_disarmed(hass: HomeAssistant) -> None:
    await _setup(hass, sirens_enabled=True)
    await _safe(hass, "on")
    state = hass.states.get(PANEL)
    assert state is not None
    assert state.state == AlarmControlPanelState.TRIGGERED
    assert state.attributes["profile_name"] == "Immer aktiv"
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL)
    assert _panel(hass) == AlarmControlPanelState.DISARMED


async def test_armed_triggers_immediately_with_profile(hass: HomeAssistant) -> None:
    await _setup(hass)
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    await _safe(hass, "on")
    assert _panel(hass) == AlarmControlPanelState.TRIGGERED
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL)
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_always_active_options(hass: HomeAssistant) -> None:
    entry = make_entry({"sirens": ["siren.a"]})
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    for step in ("triggering", "always_active"):
        flow = await hass.config_entries.options.async_configure(
            flow["flow_id"], {"next_step_id": step}
        )
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"],
        {"sensors": [SAFE], "sirens_enabled": True, "sirens": ["siren.a"], "reaction_time": 60},
    )
    assert flow["type"] is FlowResultType.MENU
    stored = entry.options["always_active"]
    assert stored["sensors"] == [SAFE]
    assert stored["sirens_enabled"] is True
    assert stored["reaction_time"] == 60


# --- Scharf durch Schließen der Tür -----------------------------------------


def _away(**closing: Any) -> dict[str, Any]:
    arm_on_close = {"enabled": True, "doors": [DOOR], "settle": 5, **closing}
    return {"profiles": {"away": {"exit_delay": 60, "arm_on_close": arm_on_close}}}


async def test_arm_by_closing_door(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    await setup_entry(hass, make_entry(_away()))
    set_sensor(hass, DOOR, "on")  # Tür offen beim Scharfschalten: erlaubt
    await hass.async_block_till_done()
    await _service(hass, "alarm_control_panel", "alarm_arm_away", entity_id=PANEL)
    assert _panel(hass) == AlarmControlPanelState.ARMING
    set_sensor(hass, DOOR, "off")
    await hass.async_block_till_done()
    await _wait(hass, freezer, 3)
    set_sensor(hass, DOOR, "on")  # noch einmal auf: Beruhigungszeit beginnt neu
    await hass.async_block_till_done()
    await _wait(hass, freezer, 4)
    assert _panel(hass) == AlarmControlPanelState.ARMING
    set_sensor(hass, DOOR, "off")
    await hass.async_block_till_done()
    await _wait(hass, freezer, 6)
    assert _panel(hass) == AlarmControlPanelState.ARMED_AWAY


async def test_exit_door_still_open_at_end_aborts(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    await setup_entry(hass, make_entry(_away()))
    set_sensor(hass, DOOR, "on")
    await hass.async_block_till_done()
    await _service(hass, "alarm_control_panel", "alarm_arm_away", entity_id=PANEL)
    await _wait(hass, freezer, 61)
    assert _panel(hass) == AlarmControlPanelState.DISARMED


async def test_without_arm_on_close_open_door_refuses(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry({"profiles": {"away": {"exit_delay": 60}}}))
    set_sensor(hass, DOOR, "on")
    await hass.async_block_till_done()
    with pytest.raises(ServiceValidationError):
        await _service(hass, "alarm_control_panel", "alarm_arm_away", entity_id=PANEL)
    assert _panel(hass) == AlarmControlPanelState.DISARMED


async def test_other_open_sensor_still_refuses(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry(_away()))
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    with pytest.raises(ServiceValidationError):
        await _service(hass, "alarm_control_panel", "alarm_arm_away", entity_id=PANEL)
    assert _panel(hass) == AlarmControlPanelState.DISARMED
