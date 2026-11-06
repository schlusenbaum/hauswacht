"""Integrationstests: Automatik pro Profil (Uhrzeit, Anwesenheit)."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    async_capture_events,
    async_fire_time_changed,
)

from custom_components.hauswacht.const import EVENT_HAUSWACHT

from .conftest import PANEL, WINDOW, make_entry, set_sensor, setup_entry

A = "person.a"
B = "person.b"


async def _service(hass: HomeAssistant, domain: str, service: str, **data: Any) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)
    await hass.async_block_till_done()


def _state(hass: HomeAssistant) -> str:
    state = hass.states.get(PANEL)
    assert state is not None
    return state.state


async def _at(hass: HomeAssistant, hour: int, minute: int, days: int = 1) -> None:
    """Simuliert die Uhrzeit an einem künftigen Tag (geplante Zeitpunkte liegen in der Zukunft)."""
    moment = (dt_util.now() + timedelta(days=days)).replace(
        hour=hour, minute=minute, second=0, microsecond=0
    )
    async_fire_time_changed(hass, moment)
    await hass.async_block_till_done()


async def _later(hass: HomeAssistant, minutes: int) -> None:
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=minutes))
    await hass.async_block_till_done()


async def _person(hass: HomeAssistant, entity_id: str, state: str) -> None:
    hass.states.async_set(entity_id, state)
    await hass.async_block_till_done()


async def _setup(hass: HomeAssistant, **auto: Any) -> None:
    hass.states.async_set(A, "home")
    hass.states.async_set(B, "home")
    await setup_entry(hass, make_entry({"profiles": {"away": {**auto, "exit_delay": 0}}}))


# --- Uhrzeit ----------------------------------------------------------------


async def test_arm_and_disarm_by_time(hass: HomeAssistant) -> None:
    await _setup(hass, auto_arm_time="23:00:00", auto_disarm_time="06:30:00")
    await _at(hass, 23, 0)
    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY
    await _at(hass, 6, 30, days=2)
    assert _state(hass) == AlarmControlPanelState.DISARMED


async def test_time_on_other_weekday_does_nothing(hass: HomeAssistant) -> None:
    today = dt_util.now().weekday()
    other = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"][(today + 1) % 7]
    await _setup(hass, auto_arm_time="23:00:00", auto_weekdays=[other])
    await _at(hass, 23, 0)
    assert _state(hass) == AlarmControlPanelState.DISARMED


async def test_automatic_arming_never_overrides_other_profile(hass: HomeAssistant) -> None:
    await _setup(hass, auto_arm_time="23:00:00")
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    await _at(hass, 23, 0)
    assert _state(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_disarm_time_does_not_end_running_alarm(hass: HomeAssistant) -> None:
    await _setup(hass, auto_disarm_time="06:30:00")
    await _service(hass, "alarm_control_panel", "alarm_arm_away", entity_id=PANEL)
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    await _at(hass, 6, 30, days=2)
    assert _state(hass) == AlarmControlPanelState.TRIGGERED


async def test_automatic_arming_fails_with_open_window(hass: HomeAssistant) -> None:
    await _setup(hass, auto_arm_time="23:00:00")
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    await _at(hass, 23, 0)
    assert _state(hass) == AlarmControlPanelState.DISARMED
    assert [e for e in events if e.data["type"] == "AutoArmFailed"]


# --- Anwesenheit ------------------------------------------------------------


async def test_arm_when_all_away_after_delay(hass: HomeAssistant) -> None:
    await _setup(hass, auto_away_persons=[A, B], auto_away_delay=15)
    await _person(hass, A, "not_home")
    await _person(hass, B, "Arbeit")
    await _later(hass, 10)
    assert _state(hass) == AlarmControlPanelState.DISARMED
    await _later(hass, 16)
    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY


async def test_return_within_delay_cancels(hass: HomeAssistant) -> None:
    await _setup(hass, auto_away_persons=[A, B], auto_away_delay=15)
    await _person(hass, A, "not_home")
    await _person(hass, B, "not_home")
    await _later(hass, 5)
    await _person(hass, B, "home")  # z. B. Handy war nur kurz aus dem WLAN
    await _later(hass, 20)
    assert _state(hass) == AlarmControlPanelState.DISARMED


async def test_unknown_person_is_not_away(hass: HomeAssistant) -> None:
    await _setup(hass, auto_away_persons=[A, B], auto_away_delay=1)
    await _person(hass, A, "not_home")
    await _person(hass, B, "unknown")
    await _later(hass, 5)
    assert _state(hass) == AlarmControlPanelState.DISARMED


async def test_disarm_on_arrival_only_if_armed_automatically(hass: HomeAssistant) -> None:
    await _setup(hass, auto_away_persons=[A, B], auto_away_delay=1, auto_disarm_on_arrival=True)
    await _person(hass, A, "not_home")
    await _person(hass, B, "not_home")
    await _later(hass, 2)
    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY
    await _person(hass, A, "home")
    assert _state(hass) == AlarmControlPanelState.DISARMED


async def test_arrival_does_not_disarm_manual_arming(hass: HomeAssistant) -> None:
    await _setup(hass, auto_away_persons=[A, B], auto_disarm_on_arrival=True)
    await _person(hass, A, "not_home")
    await _person(hass, B, "not_home")
    await _service(hass, "alarm_control_panel", "alarm_arm_away", entity_id=PANEL)
    await _person(hass, A, "home")
    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY


# --- Optionen ---------------------------------------------------------------


async def test_options_flow_saves_automation(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "profiles"}
    )
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "profile_edit"}
    )
    flow = await hass.config_entries.options.async_configure(flow["flow_id"], {"profile": "night"})
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"],
        {
            "name": "Nacht",
            "automation": {
                "auto_arm_time": "22:45:00",
                "auto_weekdays": ["fri", "sat"],
                "auto_away_delay": 20,
                "auto_disarm_on_arrival": False,
            },
        },
    )
    assert flow["type"] is FlowResultType.CREATE_ENTRY
    night = entry.options["profiles"]["night"]
    assert night["auto_arm_time"] == "22:45:00"
    assert night["auto_weekdays"] == ["fri", "sat"]
    assert night["auto_away_delay"] == 20
    assert night["zones"] == ["aussenhaut", "keller"]
