"""Integrationstests: Melder mit Kippstellung (ADR 0010).

Alle Sensoren sind Testzustände. Es werden keine Sirenen oder Geräte angesprochen.
"""

from __future__ import annotations

from typing import Any

import pytest
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import ServiceValidationError
from pytest_homeassistant_custom_component.common import async_capture_events

from custom_components.hauswacht.const import EVENT_HAUSWACHT

from .conftest import PANEL, make_entry, setup_entry

TILT = "sensor.fenster_schlafzimmer_opening_state"
HANDLE = "binary_sensor.fenstergriff_bad"
OPTIONS = ["open", "tilted", "closed"]

TILT_OPTIONS: dict[str, Any] = {
    "tilt_sensors": {
        TILT: {"attribute": None, "closed": ["closed"], "tilted": ["tilted"]},
        HANDLE: {"attribute": "window_state", "closed": ["CLOSED"], "tilted": ["TILTED"]},
    },
    "zones": {
        "fenster": {"name": "Fenster", "entities": [TILT, HANDLE], "label": None},
    },
    "profiles": {
        # Nacht: gekippt erlaubt; Zuhause: gekippt zählt als offen ("trotzdem scharf" möglich)
        "night": {"zones": ["fenster"], "tilt_allowed": True},
        "home": {"zones": ["fenster"], "open_policy": "confirm"},
    },
}


async def _service(hass: HomeAssistant, domain: str, service: str, **data: Any) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)
    await hass.async_block_till_done()


async def _window(hass: HomeAssistant, value: str) -> None:
    hass.states.async_set(TILT, value, {"options": OPTIONS, "device_class": "enum"})
    await hass.async_block_till_done()


async def _handle(hass: HomeAssistant, value: str) -> None:
    state = "off" if value == "CLOSED" else "on"
    hass.states.async_set(HANDLE, state, {"window_state": value, "device_class": "window"})
    await hass.async_block_till_done()


def _panel(hass: HomeAssistant) -> Any:
    state = hass.states.get(PANEL)
    assert state is not None
    return state


async def _setup(hass: HomeAssistant, window: str = "closed", handle: str = "CLOSED") -> None:
    await _window(hass, window)
    await _handle(hass, handle)
    await setup_entry(hass, make_entry(TILT_OPTIONS))


async def test_tilted_allowed_at_night_open_triggers(hass: HomeAssistant) -> None:
    await _setup(hass, window="tilted")
    await _service(hass, "hauswacht", "arm", entity_id=PANEL, profile="night")
    panel = _panel(hass)
    assert panel.attributes["phase"] == "armed"
    assert panel.attributes["tilted_sensors"] == [TILT]
    assert TILT not in panel.attributes["open_sensors"]
    await _window(hass, "open")
    assert _panel(hass).state == AlarmControlPanelState.TRIGGERED


async def test_tilted_back_to_closed_is_quiet(hass: HomeAssistant) -> None:
    await _setup(hass, window="tilted")
    await _service(hass, "hauswacht", "arm", entity_id=PANEL, profile="night")
    await _window(hass, "closed")
    await _window(hass, "tilted")
    assert _panel(hass).attributes["phase"] == "armed"


async def test_tilted_counts_as_open_without_permission(hass: HomeAssistant) -> None:
    await _setup(hass, window="tilted")
    with pytest.raises(ServiceValidationError):
        await _service(hass, "hauswacht", "arm", entity_id=PANEL, profile="home")
    assert _panel(hass).attributes["phase"] == "disarmed"


async def test_tilting_while_armed_triggers_without_permission(hass: HomeAssistant) -> None:
    await _setup(hass)
    await _service(hass, "hauswacht", "arm", entity_id=PANEL, profile="home")
    await _window(hass, "tilted")
    assert _panel(hass).state == AlarmControlPanelState.TRIGGERED


async def test_bypassed_tilted_window_opened_fully_triggers(hass: HomeAssistant) -> None:
    await _setup(hass, window="tilted")
    await _service(hass, "hauswacht", "arm", entity_id=PANEL, profile="home", confirm=True)
    assert TILT in _panel(hass).attributes["bypassed_sensors"]
    await _window(hass, "open")
    panel = _panel(hass)
    assert panel.state == AlarmControlPanelState.TRIGGERED
    assert panel.attributes["trigger_sensor"] == TILT


async def test_attribute_source(hass: HomeAssistant) -> None:
    await _setup(hass, handle="TILTED")
    await _service(hass, "hauswacht", "arm", entity_id=PANEL, profile="night")
    assert HANDLE in _panel(hass).attributes["tilted_sensors"]
    await _handle(hass, "OPEN")
    assert _panel(hass).state == AlarmControlPanelState.TRIGGERED


async def test_unknown_value_counts_as_open(hass: HomeAssistant) -> None:
    await _setup(hass, window="spaltlueftung")
    with pytest.raises(ServiceValidationError):
        await _service(hass, "hauswacht", "arm", entity_id=PANEL, profile="night")


async def test_unavailable_blocks_arming(hass: HomeAssistant) -> None:
    await _setup(hass, window="unavailable")
    with pytest.raises(ServiceValidationError):
        await _service(hass, "hauswacht", "arm", entity_id=PANEL, profile="night")


async def test_event_has_position(hass: HomeAssistant) -> None:
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    await _setup(hass, window="tilted")
    await _service(hass, "hauswacht", "arm", entity_id=PANEL, profile="night")
    await _window(hass, "open")
    with_sensor = [e.data for e in events if e.data.get("sensor_key") == TILT]
    assert with_sensor
    assert with_sensor[-1]["position"] == "open"


async def test_profile_switch_exists(hass: HomeAssistant) -> None:
    await _setup(hass)
    assert any("tilted" in s.entity_id for s in hass.states.async_all("switch"))


async def test_options_flow_adds_select_helper(hass: HomeAssistant) -> None:
    hass.states.async_set("input_select.testfenster", "zu", {"options": ["offen", "gekippt", "zu"]})
    await _setup(hass)
    entry = hass.config_entries.async_entries("hauswacht")[0]
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "triggering"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "special_sensors"}
    )
    assert result["type"] is FlowResultType.MENU
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "tilt_add"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"entity": "input_select.testfenster"}
    )
    assert result["step_id"] == "tilt_map"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"closed": ["zu"], "tilted": ["gekippt"], "target": "fenster"}
    )
    assert result["type"] is FlowResultType.MENU
    await hass.async_block_till_done()
    options = hass.config_entries.async_entries("hauswacht")[0].options
    assert options["tilt_sensors"]["input_select.testfenster"]["tilted"] == ["gekippt"]
    assert "input_select.testfenster" in options["zones"]["fenster"]["entities"]


async def test_options_flow_needs_closed_value(hass: HomeAssistant) -> None:
    hass.states.async_set("input_select.testfenster", "zu", {"options": ["offen", "gekippt", "zu"]})
    await _setup(hass)
    entry = hass.config_entries.async_entries("hauswacht")[0]
    result = await hass.config_entries.options.async_init(entry.entry_id)
    for step in ("triggering", "special_sensors", "tilt_add"):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"next_step_id": step}
        )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"entity": "input_select.testfenster"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"closed": [], "tilted": ["gekippt"]}
    )
    assert result["errors"] == {"closed": "tilt_no_closed"}
