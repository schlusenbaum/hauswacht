"""Integrationstests: Sensorzustände simulieren (Testkarte).

Simuliert wird nur für Hauswacht. Die Zustände in Home Assistant bleiben unverändert,
Sirenen sind ATTRAPPEN und dürfen nie angesteuert werden.
"""

from __future__ import annotations

from typing import Any

import pytest
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.hauswacht.const import DOMAIN

from .conftest import (
    DOOR,
    MOTION,
    PANEL,
    TAMPER,
    TEST_MODE,
    WINDOW,
    make_entry,
    set_sensor,
    setup_entry,
)


async def _service(hass: HomeAssistant, domain: str, service: str, **data: Any) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)
    await hass.async_block_till_done()


async def _sim(hass: HomeAssistant, sensor: str, state: str) -> None:
    await _service(hass, DOMAIN, "simulate_state", entity_id=PANEL, sensor=sensor, state=state)


def _state(hass: HomeAssistant, entity_id: str = PANEL) -> str:
    state = hass.states.get(entity_id)
    assert state is not None
    return state.state


def _sim_sensor(hass: HomeAssistant) -> str:
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    entity_id = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{entry.entry_id}_simulation"
    )
    assert entity_id is not None
    return entity_id


async def _setup_test_mode(hass: HomeAssistant) -> list[Any]:
    sirens = async_mock_service(hass, "siren", "turn_on")
    await setup_entry(hass, make_entry())
    await _service(hass, "switch", "turn_on", entity_id=TEST_MODE)
    return sirens


async def test_simulation_requires_test_mode(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    with pytest.raises(ServiceValidationError):
        await _sim(hass, WINDOW, "on")


async def test_unknown_sensor_rejected(hass: HomeAssistant) -> None:
    await _setup_test_mode(hass)
    with pytest.raises(ServiceValidationError):
        await _sim(hass, "binary_sensor.fremd", "on")


async def test_open_window_blocks_arming_and_ha_state_unchanged(hass: HomeAssistant) -> None:
    await _setup_test_mode(hass)
    await _sim(hass, WINDOW, "on")
    assert _state(hass, WINDOW) == "off"  # echter Zustand in Home Assistant unverändert
    with pytest.raises(ServiceValidationError):
        await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)

    await _sim(hass, WINDOW, "real")
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    assert _state(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_door_entry_delay_and_motion_alarm_without_sirens(hass: HomeAssistant) -> None:
    sirens = await _setup_test_mode(hass)
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    await _sim(hass, DOOR, "on")
    assert _state(hass) == AlarmControlPanelState.PENDING
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL)
    await _sim(hass, DOOR, "off")

    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    await _sim(hass, MOTION, "on")
    assert _state(hass) == AlarmControlPanelState.TRIGGERED
    assert sirens == []  # Testmodus: keine Sirene


async def test_tamper_simulation(hass: HomeAssistant) -> None:
    sirens = await _setup_test_mode(hass)
    await _sim(hass, TAMPER, "on")
    sensor = hass.states.get(_sim_sensor(hass))
    assert sensor is not None
    assert sensor.state == "1"
    assert sirens == []


async def test_real_changes_ignored_while_simulated(hass: HomeAssistant) -> None:
    await _setup_test_mode(hass)
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    await _sim(hass, WINDOW, "off")
    set_sensor(hass, WINDOW, "on")  # echtes Öffnen während der Simulation
    await hass.async_block_till_done()
    assert _state(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_reset_to_real_value_evaluates_real_state(hass: HomeAssistant) -> None:
    await _setup_test_mode(hass)
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    await _sim(hass, WINDOW, "off")
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    await _service(hass, DOMAIN, "simulate_reset", entity_id=PANEL)
    # Zurück auf echt: das echte Fenster ist offen -> Testalarm
    assert _state(hass) == AlarmControlPanelState.TRIGGERED


async def test_unavailable_blocks_arming(hass: HomeAssistant) -> None:
    await _setup_test_mode(hass)
    await _sim(hass, MOTION, "unavailable")
    with pytest.raises(ServiceValidationError):
        await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)


async def test_overview_and_leaving_test_mode_clears(hass: HomeAssistant) -> None:
    await _setup_test_mode(hass)
    await _sim(hass, WINDOW, "on")
    sensor = hass.states.get(_sim_sensor(hass))
    assert sensor is not None
    assert sensor.state == "1"
    assert sensor.attributes["test_mode"] is True
    rows = {r["entity_id"]: r for r in sensor.attributes["sensors"]}
    assert set(rows) >= {DOOR, WINDOW, MOTION, TAMPER}
    assert rows[WINDOW]["simulated"] == "on"
    assert rows[WINDOW]["real"] == "off"
    assert rows[WINDOW]["device_class"] == "window"
    assert rows[DOOR]["simulated"] is None

    await _service(hass, "switch", "turn_off", entity_id=TEST_MODE)
    sensor = hass.states.get(_sim_sensor(hass))
    assert sensor is not None
    assert sensor.state == "0"
    # Ohne Testmodus zählt wieder der echte Zustand: scharf schalten geht
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    assert _state(hass) == AlarmControlPanelState.ARMED_NIGHT
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL)
    await _service(hass, "switch", "turn_on", entity_id=TEST_MODE)
    sensor = hass.states.get(_sim_sensor(hass))
    assert sensor is not None
    assert sensor.state == "0"  # alte Simulation kommt nicht wieder
