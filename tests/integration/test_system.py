"""Integrationstests: Systemstatus, Infrastruktur-Störungen und Simulation im Testmodus.

Alle Sensoren und Indikatoren sind Testzustände. Es werden keine Geräte geschaltet.
"""

from __future__ import annotations

from typing import Any

import pytest
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from pytest_homeassistant_custom_component.common import async_capture_events

from custom_components.hauswacht.const import EVENT_HAUSWACHT

from .conftest import DOOR, MOTION, PANEL, TEST_MODE, WINDOW, make_entry, set_sensor, setup_entry

Z2M = "binary_sensor.zigbee2mqtt_bridge_connection_state"
STATUS = "sensor.hauswacht_system_status"


async def _service(hass: HomeAssistant, domain: str, service: str, **data: Any) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)
    await hass.async_block_till_done()


async def _set(hass: HomeAssistant, entity_id: str, state: str) -> None:
    if entity_id == Z2M:
        hass.states.async_set(Z2M, state, {"device_class": "connectivity"})
    else:
        set_sensor(hass, entity_id, state)
    await hass.async_block_till_done()


def _value(hass: HomeAssistant, entity_id: str) -> str:
    state = hass.states.get(entity_id)
    assert state is not None
    return state.state


async def _setup_with_infra(hass: HomeAssistant) -> None:
    hass.states.async_set(Z2M, "on", {"device_class": "connectivity"})
    await setup_entry(hass, make_entry({"infrastructure": [Z2M]}))


# --- Systemstatus -----------------------------------------------------------


async def test_status_ok(hass: HomeAssistant) -> None:
    await _setup_with_infra(hass)
    assert _value(hass, STATUS) == "ok"


async def test_status_degraded_on_unavailable_sensor(hass: HomeAssistant) -> None:
    await _setup_with_infra(hass)
    await _set(hass, MOTION, "unavailable")
    assert _value(hass, STATUS) == "degraded"


async def test_status_fault_on_infrastructure_failure(hass: HomeAssistant) -> None:
    await _setup_with_infra(hass)
    await _set(hass, Z2M, "off")
    assert _value(hass, STATUS) == "fault"
    state = hass.states.get(STATUS)
    assert state is not None
    assert state.attributes["faulty_infrastructure"] == [Z2M]


async def test_infrastructure_fault_refuses_arming(hass: HomeAssistant) -> None:
    await _setup_with_infra(hass)
    await _set(hass, Z2M, "unavailable")
    with pytest.raises(ServiceValidationError):
        await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)


# --- Ausfall und Wiederkehr im scharfen Zustand -----------------------------


async def test_outage_and_recovery_without_false_alarm(hass: HomeAssistant) -> None:
    """Z2M fällt aus, Sensoren werden unavailable und kommen geschlossen zurück."""
    await _setup_with_infra(hass)
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)

    await _set(hass, Z2M, "off")
    for sensor in (DOOR, WINDOW, MOTION):
        await _set(hass, sensor, "unavailable")
    assert _value(hass, PANEL) == AlarmControlPanelState.ARMED_NIGHT
    types = [e.data["type"] for e in events]
    assert "InfrastructureFault" in types
    assert "SensorUnavailable" in types

    for sensor in (DOOR, WINDOW, MOTION):
        await _set(hass, sensor, "off")
    await _set(hass, Z2M, "on")
    assert _value(hass, PANEL) == AlarmControlPanelState.ARMED_NIGHT
    assert "InfrastructureRecovered" in [e.data["type"] for e in events]
    assert not [e for e in events if e.data["type"] == "ActivateReaction"]
    assert _value(hass, STATUS) == "ok"


async def test_sensor_returning_open_after_outage_triggers(hass: HomeAssistant) -> None:
    """Sichere Seite: Kommt ein Fenster nach dem Ausfall offen zurück, ist das ein Alarm."""
    await _setup_with_infra(hass)
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    await _set(hass, WINDOW, "unavailable")
    await _set(hass, WINDOW, "on")
    assert _value(hass, PANEL) == AlarmControlPanelState.TRIGGERED


# --- Simulation -------------------------------------------------------------


async def test_simulation_requires_test_mode(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    with pytest.raises(ServiceValidationError):
        await _service(hass, "hauswacht", "simulate_trigger", entity_id=PANEL, sensor=WINDOW)
    assert _value(hass, PANEL) == AlarmControlPanelState.ARMED_NIGHT


async def test_simulation_rejects_unknown_sensor(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    await _service(hass, "switch", "turn_on", entity_id=TEST_MODE)
    with pytest.raises(ServiceValidationError):
        await _service(
            hass, "hauswacht", "simulate_trigger", entity_id=PANEL, sensor="binary_sensor.fremd"
        )


async def test_simulated_window_triggers_test_alarm(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    await _service(hass, "switch", "turn_on", entity_id=TEST_MODE)
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    await _service(hass, "hauswacht", "simulate_trigger", entity_id=PANEL, sensor=WINDOW)

    assert _value(hass, PANEL) == AlarmControlPanelState.TRIGGERED
    alarm = [e for e in events if e.data["type"] == "ActivateReaction"]
    assert alarm[0].data["test_mode"] is True
    assert alarm[0].data["sensor_key"] == WINDOW
    # Der echte Sensor wurde nicht verändert
    assert _value(hass, WINDOW) == "off"


async def test_simulated_door_runs_entry_delay(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    await _service(hass, "switch", "turn_on", entity_id=TEST_MODE)
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    await _service(hass, "hauswacht", "simulate_trigger", entity_id=PANEL, sensor=DOOR)
    assert _value(hass, PANEL) == AlarmControlPanelState.PENDING
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL)
    assert _value(hass, PANEL) == AlarmControlPanelState.DISARMED


async def test_simulation_while_disarmed_does_nothing(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    await _service(hass, "switch", "turn_on", entity_id=TEST_MODE)
    await _service(hass, "hauswacht", "simulate_trigger", entity_id=PANEL, sensor=WINDOW)
    assert _value(hass, PANEL) == AlarmControlPanelState.DISARMED


# --- Optionen ---------------------------------------------------------------


async def test_options_flow_infrastructure(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "infrastructure"}
    )
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"infrastructure": [Z2M]}
    )
    await hass.async_block_till_done()
    assert entry.options["infrastructure"] == [Z2M]
