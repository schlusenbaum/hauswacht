"""Integrationstests: Alarm erst, wenn ein zweiter Melder der Zone bestätigt.

Alle Sensoren sind Testzustände, notify-Dienste sind ATTRAPPEN, Sirenen nicht freigegeben.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import (
    async_capture_events,
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.hauswacht.const import EVENT_HAUSWACHT

from .conftest import DOOR, MOTION, PANEL, TAMPER, WINDOW, make_entry, set_sensor, setup_entry

MOTION2 = "binary_sensor.bwm_flur"
PHONE = "mobile_app_testhandy"


def _zones(confirm: bool = True) -> dict[str, Any]:
    return {
        "aussenhaut": {"name": "Außenhaut", "entities": [DOOR, WINDOW, TAMPER], "label": None},
        "keller": {
            "name": "Keller",
            "entities": [MOTION, MOTION2],
            "label": None,
            "confirm": confirm,
            "confirm_window": 60,
        },
    }


async def _service(hass: HomeAssistant, domain: str, service: str, **data: Any) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)
    await hass.async_block_till_done()


def _panel(hass: HomeAssistant) -> str:
    state = hass.states.get(PANEL)
    assert state is not None
    return state.state


def _motion2(hass: HomeAssistant, state: str) -> None:
    hass.states.async_set(MOTION2, state, {"device_class": "motion"})


async def _setup(hass: HomeAssistant, **extra: Any) -> None:
    _motion2(hass, "off")
    await setup_entry(hass, make_entry({"zones": _zones(), **extra}))
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT


async def _wait(hass: HomeAssistant, freezer: FrozenDateTimeFactory, seconds: int) -> None:
    freezer.tick(timedelta(seconds=seconds))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


async def test_single_sensor_does_not_trigger(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    await _setup(hass)
    set_sensor(hass, MOTION, "on")
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    assert "TriggerUnconfirmed" in [e.data["type"] for e in events]
    await _wait(hass, freezer, 61)
    assert "TriggerUnconfirmedExpired" in [e.data["type"] for e in events]
    # Nach Ablauf bestätigt ein zweiter Melder die alte Auslösung nicht mehr
    _motion2(hass, "on")
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_second_sensor_confirms(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    await _setup(hass)
    set_sensor(hass, MOTION, "on")
    await hass.async_block_till_done()
    await _wait(hass, freezer, 30)
    _motion2(hass, "on")
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.TRIGGERED


async def test_same_sensor_twice_does_not_confirm(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    await _setup(hass)
    for state in ("on", "off", "on"):
        set_sensor(hass, MOTION, state)
        await hass.async_block_till_done()
        await _wait(hass, freezer, 10)
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_without_second_available_sensor_triggers_immediately(
    hass: HomeAssistant,
) -> None:
    await _setup(hass)
    _motion2(hass, "unavailable")
    await hass.async_block_till_done()
    set_sensor(hass, MOTION, "on")
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.TRIGGERED


async def test_other_zone_still_instant(hass: HomeAssistant) -> None:
    await _setup(hass)
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.TRIGGERED


async def test_door_still_starts_entry_delay(hass: HomeAssistant) -> None:
    zones = _zones()
    zones["keller"]["entities"] = [MOTION, MOTION2, DOOR]
    zones["aussenhaut"]["entities"] = [WINDOW, TAMPER]
    _motion2(hass, "off")
    await setup_entry(
        hass, make_entry({"zones": zones, "profiles": {"night": {"entry_delay": 30}}})
    )
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    set_sensor(hass, DOOR, "on")
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.PENDING


async def test_unconfirmed_notifications_off_by_default(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    await _setup(hass, notify_system=[PHONE])
    set_sensor(hass, MOTION, "on")
    await hass.async_block_till_done()
    await _wait(hass, freezer, 61)
    assert push == []


async def test_unconfirmed_and_frequent_notifications(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    events = {
        "unconfirmed": {"enabled": True, "targets": []},
        "unconfirmed_frequent": {"enabled": True, "targets": []},
    }
    await _setup(hass, notify_system=[PHONE], events=events)
    for _ in range(3):
        set_sensor(hass, MOTION, "on")
        await hass.async_block_till_done()
        await _wait(hass, freezer, 61)
        set_sensor(hass, MOTION, "off")
        await hass.async_block_till_done()
    titles = [c.data["title"] for c in push]
    assert titles.count("Hauswacht: unbestätigte Auslösung") == 3
    assert "Hauswacht: Melder löst häufig allein aus" in titles
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_zone_option_needs_two_sensors(hass: HomeAssistant) -> None:
    from homeassistant.data_entry_flow import FlowResultType  # noqa: PLC0415

    _motion2(hass, "off")
    entry = make_entry()
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    for step in ("zones", "zone_edit"):
        flow = await hass.config_entries.options.async_configure(
            flow["flow_id"], {"next_step_id": step}
        )
    flow = await hass.config_entries.options.async_configure(flow["flow_id"], {"zone": "keller"})
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"name": "Keller", "entities": [MOTION], "confirm": True}
    )
    assert flow["errors"] == {"confirm": "confirm_needs_two"}
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"],
        {"name": "Keller", "entities": [MOTION, MOTION2], "confirm": True, "confirm_window": 90},
    )
    assert flow["type"] is FlowResultType.MENU
    stored = entry.options["zones"]["keller"]
    assert stored["confirm"] is True
    assert stored["confirm_window"] == 90
