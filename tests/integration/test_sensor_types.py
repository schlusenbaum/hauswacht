"""Integrationstests: Schlösser/Abdeckungen, Melder-Typen, Ausnahmen im Profil, Helfer-Assistent.

Alle Zustände sind Testzustände; es gibt keine Geräte und keine Sirenen.
"""

from __future__ import annotations

from typing import Any

import pytest
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_mock_service

from custom_components.hauswacht.const import DOMAIN

from .conftest import DOOR, MOTION, PANEL, TAMPER, WINDOW, make_entry, setup_entry

LOCK = "lock.haustuer_schloss"
COVER = "cover.garagentor"
WATER = "binary_sensor.wassermelder_keller"
PHONE = "mobile_app_testhandy"
TEMP = "sensor.temperatur_heizungskeller"

OPTIONS: dict[str, Any] = {
    "zones": {
        "aussen": {
            "name": "Außen",
            "entities": [DOOR, WINDOW, TAMPER, LOCK, COVER],
            "label": None,
        },
        "keller": {"name": "Keller", "entities": [MOTION, WATER], "label": None},
    },
}


async def _service(hass: HomeAssistant, domain: str, service: str, **data: Any) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)
    await hass.async_block_till_done()


def _panel(hass: HomeAssistant) -> str:
    state = hass.states.get(PANEL)
    assert state is not None
    return state.state


async def _setup(hass: HomeAssistant, **options: Any) -> MockConfigEntry:
    hass.states.async_set(LOCK, "locked")
    hass.states.async_set(COVER, "closed", {"device_class": "garage"})
    hass.states.async_set(WATER, "off", {"device_class": "moisture"})
    entry = make_entry({**OPTIONS, **options})
    await setup_entry(hass, entry)
    return entry


async def test_unlocked_lock_starts_entry_delay(hass: HomeAssistant) -> None:
    await _setup(hass)
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    hass.states.async_set(LOCK, "unlocked")
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.PENDING


async def test_open_cover_blocks_arming(hass: HomeAssistant) -> None:
    await _setup(hass)
    hass.states.async_set(COVER, "open", {"device_class": "garage"})
    await hass.async_block_till_done()
    with pytest.raises(ServiceValidationError):
        await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    assert _panel(hass) == AlarmControlPanelState.DISARMED


async def test_technical_sensor_never_part_of_arming(hass: HomeAssistant) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    await _setup(hass, notify_system=[PHONE])
    # Nasser Wassermelder blockiert das Scharfschalten nicht
    hass.states.async_set(WATER, "on", {"device_class": "moisture"})
    await hass.async_block_till_done()
    assert push, "Technik-Melder meldet auch unscharf"
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    count = len(push)
    # Scharf: wieder nur Benachrichtigung, kein Einbruchalarm
    hass.states.async_set(WATER, "off", {"device_class": "moisture"})
    await hass.async_block_till_done()
    hass.states.async_set(WATER, "on", {"device_class": "moisture"})
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    assert len(push) > count


async def test_type_door_on_window(hass: HomeAssistant) -> None:
    await _setup(hass, sensor_types={WINDOW: "door"})
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    hass.states.async_set(WINDOW, "on", {"device_class": "window"})
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.PENDING


async def test_excluded_sensor_does_not_trigger(hass: HomeAssistant) -> None:
    await _setup(hass, profiles={"night": {"excluded": [MOTION]}})
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    hass.states.async_set(MOTION, "on", {"device_class": "occupancy"})
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    hass.states.async_set(WINDOW, "on", {"device_class": "window"})
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.TRIGGERED


async def test_migration_v4_roles_to_types(hass: HomeAssistant) -> None:
    old = MockConfigEntry(
        domain=DOMAIN,
        title="Hauswacht",
        data={},
        options={
            **make_entry().options,
            "sensor_roles": {WINDOW: "entry"},
            "sensor_thresholds": {TEMP: {"above": 5}},
        },
        version=4,
    )
    await setup_entry(hass, old)
    assert old.version == 5
    assert old.options["sensor_types"] == {WINDOW: "door"}
    assert "sensor_roles" not in old.options
    assert "sensor_thresholds" not in old.options
