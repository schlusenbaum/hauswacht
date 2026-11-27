"""Integrationstests: Ausgangserkennung (ADR 0014) – Rausgehen ohne PIN erkennen.

Kein echtes Gerät: Sensoren und Handys sind Testzustände, notify ist eine Attrappe. Keine Sirenen.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import HomeAssistant, ServiceCall
from pytest_homeassistant_custom_component.common import (
    async_capture_events,
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.hauswacht.const import EVENT_HAUSWACHT

from .conftest import DOOR, MOTION, PANEL, make_entry, set_sensor, setup_entry

BEN = "person.ben"
WLAN = "binary_sensor.ben_wlan"
PHONE = "mobile_app_testhandy"


def _options(**exit_detect: Any) -> dict[str, Any]:
    return {
        "notify_system": [PHONE],
        "homecoming_signals": {BEN: [WLAN]},
        "presence_leave_mode": {BEN: "one"},
        "profiles": {
            "night": {
                "entry_delay": 30,
                "exit_detect": {"enabled": True, "wait": 3, **exit_detect},
            }
        },
    }


async def _setup(hass: HomeAssistant, **exit_detect: Any) -> list[ServiceCall]:
    push = async_mock_service(hass, "notify", PHONE)
    hass.states.async_set(BEN, "home")
    hass.states.async_set(WLAN, "on")
    await setup_entry(hass, make_entry(_options(**exit_detect)))
    await hass.services.async_call(
        "alarm_control_panel", "alarm_arm_night", {"entity_id": PANEL}, blocking=True
    )
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    return push


def _panel(hass: HomeAssistant) -> str:
    state = hass.states.get(PANEL)
    assert state is not None
    return state.state


async def _wait(hass: HomeAssistant, freezer: FrozenDateTimeFactory, seconds: float) -> None:
    """Uhr in kleinen Schritten vorstellen (Prüfung alle 5 Sekunden)."""
    step = 5.0
    passed = 0.0
    while passed < seconds:
        freezer.tick(timedelta(seconds=step))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        passed += step


async def _door(hass: HomeAssistant) -> None:
    set_sensor(hass, DOOR, "on")
    await hass.async_block_till_done()


async def test_person_goes_out_stays_armed(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    push = await _setup(hass)
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    await _door(hass)
    assert _panel(hass) == AlarmControlPanelState.PENDING
    assert any(e.data.get("type") == "ExitWaitStarted" for e in events)
    # sofortige Nachricht mit „Alarm jetzt“
    first = [c for c in push if c.data.get("message") != "clear_notification"]
    assert first
    actions = first[-1].data["data"]["actions"]
    assert actions[0]["title"] == "Alarm jetzt"
    await _wait(hass, freezer, 20)
    hass.states.async_set(WLAN, "off")  # Bens Handy verliert das WLAN
    await hass.async_block_till_done()
    await _wait(hass, freezer, 40)  # 30 s Puffer
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    assert any(e.data.get("type") == "ExitDetected" for e in events)
    await _wait(hass, freezer, 300)
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT  # kein Alarm danach


async def test_nobody_goes_out_alarm_after_wait(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    await _setup(hass)
    await _door(hass)
    await _wait(hass, freezer, 60)
    assert _panel(hass) == AlarmControlPanelState.PENDING  # nicht nach 30 s: stille Wartezeit
    await _wait(hass, freezer, 130)
    assert _panel(hass) == AlarmControlPanelState.TRIGGERED


async def test_short_hiccup_is_not_going_out(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    await _setup(hass)
    await _door(hass)
    hass.states.async_set(WLAN, "off")
    await hass.async_block_till_done()
    await _wait(hass, freezer, 10)
    hass.states.async_set(WLAN, "on")  # nach 10 s wieder da
    await hass.async_block_till_done()
    await _wait(hass, freezer, 60)
    assert _panel(hass) == AlarmControlPanelState.PENDING


async def test_inside_sensor_without_motion_normal_entry_delay(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    await _setup(hass, inside=[MOTION])
    await _door(hass)
    await _wait(hass, freezer, 35)
    assert _panel(hass) == AlarmControlPanelState.TRIGGERED


async def test_nobody_home_normal_entry_delay(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    await _setup(hass)
    hass.states.async_set(WLAN, "off")
    hass.states.async_set(BEN, "not_home")
    await hass.async_block_till_done()
    await _door(hass)
    await _wait(hass, freezer, 35)
    assert _panel(hass) == AlarmControlPanelState.TRIGGERED


async def test_alarm_now(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    await _setup(hass)
    await _door(hass)
    entry = hass.config_entries.async_entries("hauswacht")[0]
    entry.runtime_data.exit_alarm_now()
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.TRIGGERED
