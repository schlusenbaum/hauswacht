"""Integrationstests: Erschütterungsmelder (ADR 0010 Teil B).

Alle Sensoren sind Testzustände. Es werden keine Sirenen oder Geräte angesprochen.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import async_capture_events

from custom_components.hauswacht.const import EVENT_HAUSWACHT

from .conftest import PANEL, make_entry, setup_entry

SHOCK = "binary_sensor.erschuetterung_bad"
STRENGTH = "sensor.fenster_vibration"


def _options(count: int = 1, window: int = 60) -> dict[str, Any]:
    return {
        "vibration_sources": {STRENGTH: {"threshold": 30}},
        "zones": {
            "fenster": {
                "name": "Fenster",
                "entities": [SHOCK, STRENGTH],
                "label": None,
                "vibration_count": count,
                "vibration_window": window,
            },
        },
        "profiles": {"home": {"zones": ["fenster"]}},
    }


async def _service(hass: HomeAssistant, domain: str, service: str, **data: Any) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)
    await hass.async_block_till_done()


async def _shock(hass: HomeAssistant, state: str) -> None:
    hass.states.async_set(SHOCK, state, {"device_class": "vibration"})
    await hass.async_block_till_done()


async def _strength(hass: HomeAssistant, value: str) -> None:
    hass.states.async_set(STRENGTH, value, {"unit_of_measurement": ""})
    await hass.async_block_till_done()


def _panel(hass: HomeAssistant) -> Any:
    state = hass.states.get(PANEL)
    assert state is not None
    return state


async def _setup(hass: HomeAssistant, **rule: int) -> None:
    await _shock(hass, "off")
    await _strength(hass, "0")
    await setup_entry(hass, make_entry(_options(**rule)))


async def test_vibration_never_blocks_arming(hass: HomeAssistant) -> None:
    await _setup(hass)
    await _shock(hass, "on")  # Sensor hält "an" noch eine Weile
    await _service(hass, "hauswacht", "arm", entity_id=PANEL, profile="home")
    assert _panel(hass).attributes["phase"] == "armed"
    assert SHOCK not in _panel(hass).attributes["open_sensors"]


async def test_single_report_triggers_by_default(hass: HomeAssistant) -> None:
    await _setup(hass)
    await _service(hass, "hauswacht", "arm", entity_id=PANEL, profile="home")
    await _shock(hass, "on")
    assert _panel(hass).state == AlarmControlPanelState.TRIGGERED


async def test_two_reports_needed(hass: HomeAssistant) -> None:
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    await _setup(hass, count=2, window=60)
    await _service(hass, "hauswacht", "arm", entity_id=PANEL, profile="home")
    await _shock(hass, "on")
    assert _panel(hass).attributes["phase"] == "armed"
    counted = [e.data for e in events if e.data.get("type") == "VibrationCounted"]
    assert counted[-1]["count"] == 1
    assert counted[-1]["needed"] == 2
    await _shock(hass, "off")
    await _shock(hass, "on")
    assert _panel(hass).state == AlarmControlPanelState.TRIGGERED


async def test_strength_threshold_triggers(hass: HomeAssistant) -> None:
    await _setup(hass)
    await _service(hass, "hauswacht", "arm", entity_id=PANEL, profile="home")
    await _strength(hass, "12")
    assert _panel(hass).attributes["phase"] == "armed"
    await _strength(hass, "45")
    assert _panel(hass).state == AlarmControlPanelState.TRIGGERED


async def test_strength_same_value_counts_again(hass: HomeAssistant) -> None:
    await _setup(hass, count=2, window=60)
    await _service(hass, "hauswacht", "arm", entity_id=PANEL, profile="home")
    await _strength(hass, "45")
    assert _panel(hass).attributes["phase"] == "armed"
    await _strength(hass, "45")  # gleiche Zahl erneut gemeldet
    assert _panel(hass).state == AlarmControlPanelState.TRIGGERED


async def test_strength_not_a_number_is_unavailable(hass: HomeAssistant) -> None:
    await _setup(hass)
    await _strength(hass, "kaputt")
    assert STRENGTH in _panel(hass).attributes["unavailable_sensors"]
