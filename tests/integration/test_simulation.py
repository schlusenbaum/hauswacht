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


def _rows(hass: HomeAssistant) -> dict[str, dict[str, Any]]:
    sensor = hass.states.get(_sim_sensor(hass))
    assert sensor is not None
    return {r["entity_id"]: r for r in sensor.attributes["sensors"]}


async def test_status_shows_bypass_and_profile(hass: HomeAssistant) -> None:
    await _setup_test_mode(hass)
    assert _rows(hass)[WINDOW]["status"] == "disarmed"
    assert _rows(hass)[TAMPER]["status"] == "tamper_message"

    await _service(hass, "alarm_control_panel", "alarm_arm_home", entity_id=PANEL)
    rows = _rows(hass)
    assert rows[WINDOW]["status"] == "monitored"
    assert rows[MOTION]["status"] == "not_monitored"  # Keller gehört nicht zu "Zuhause"
    assert rows[TAMPER]["status"] == "tamper_message"

    await _sim(hass, WINDOW, "on")
    assert _state(hass) == AlarmControlPanelState.TRIGGERED
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL)
    assert _rows(hass)[WINDOW]["status"] == "bypassed_until_closed"

    # Zweites "Auf" an einem offenen Fenster ändert nichts; erst "Zu", dann wieder überwacht
    await _sim(hass, WINDOW, "on")
    assert _state(hass) == AlarmControlPanelState.ARMED_HOME
    await _sim(hass, WINDOW, "off")
    assert _rows(hass)[WINDOW]["status"] == "monitored"
    await _sim(hass, WINDOW, "on")
    assert _state(hass) == AlarmControlPanelState.TRIGGERED


async def test_door_after_ended_alarm_starts_entry_delay(hass: HomeAssistant) -> None:
    """Fenster löst aus, Alarm beendet (Fenster bleibt offen), Tür geht auf -> neuer Alarm."""
    await setup_entry(hass, make_entry({"profiles": {"home": {"entry_delay": 30}}}))
    await _service(hass, "switch", "turn_on", entity_id=TEST_MODE)
    await _service(hass, "alarm_control_panel", "alarm_arm_home", entity_id=PANEL)
    await _sim(hass, WINDOW, "on")
    assert _state(hass) == AlarmControlPanelState.TRIGGERED
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL)
    assert _state(hass) == AlarmControlPanelState.ARMED_HOME
    await _sim(hass, DOOR, "on")
    assert _state(hass) == AlarmControlPanelState.PENDING


async def test_tamper_status_with_alarm_setting(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry({"profiles": {"home": {"tamper_triggers_alarm": True}}}))
    await _service(hass, "switch", "turn_on", entity_id=TEST_MODE)
    await _service(hass, "alarm_control_panel", "alarm_arm_home", entity_id=PANEL)
    assert _rows(hass)[TAMPER]["status"] == "tamper_alarm"


async def test_entities_explain_themselves(hass: HomeAssistant) -> None:
    from homeassistant.helpers import device_registry as dr  # noqa: PLC0415

    await setup_entry(hass, make_entry())
    registry = er.async_get(hass)
    simulation = registry.async_get(_sim_sensor(hass))
    assert simulation is not None
    assert simulation.hidden_by is er.RegistryEntryHider.INTEGRATION  # nur für die Testkarte
    assert simulation.entity_id == "sensor.hauswacht_simulated_sensors"  # ID bleibt kurz
    assert registry.async_get("binary_sensor.hauswacht_open_sensors") is not None
    device = dr.async_get(hass).async_get(simulation.device_id or "")
    assert device is not None
    assert device.configuration_url is not None
    assert "docs/installation.md" in device.configuration_url
