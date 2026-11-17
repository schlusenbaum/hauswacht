"""Integrationstests: Verhalten nach Neustart (wiederherstellen, scharf, unscharf).

Der Zustand "vor dem Neustart" wird über den gespeicherten Zustand vorgegeben. Keine echten
Geräte, keine Sirenen.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    async_capture_events,
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.hauswacht.const import DOMAIN, EVENT_HAUSWACHT

from .conftest import DOOR, PANEL, WINDOW, make_entry, set_sensor, setup_entry

pytestmark = pytest.mark.parametrize("expected_lingering_timers", [True])


def _state(hass: HomeAssistant) -> str:
    state = hass.states.get(PANEL)
    assert state is not None
    return state.state


def _stored(hass_storage: dict[str, Any], entry_id: str, data: dict[str, Any]) -> None:
    hass_storage[f"{DOMAIN}.{entry_id}"] = {
        "version": 1,
        "minor_version": 1,
        "key": f"{DOMAIN}.{entry_id}",
        "data": data,
    }


async def _later(hass: HomeAssistant, seconds: float) -> None:
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=seconds))
    await hass.async_block_till_done()


async def test_restore_is_default_and_arms_again(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    entry = make_entry()
    _stored(
        hass_storage,
        entry.entry_id,
        {"armed_profile": "night", "restore": {"profile": "night", "state": "armed"}},
    )
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    await setup_entry(hass, entry)
    assert _state(hass) == AlarmControlPanelState.ARMED_NIGHT
    assert any(e.data["type"] == "RestoredAfterRestart" for e in events)
    assert not any(e.data["type"] == "RestartedDisarmed" for e in events)
    # wirklich scharf: ein Fenster löst aus
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    assert _state(hass) == AlarmControlPanelState.TRIGGERED


async def test_restore_from_older_version(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    """Bis 0.44 war nur das scharfe Profil gespeichert – das genügt zum Wiederherstellen."""
    entry = make_entry()
    _stored(hass_storage, entry.entry_id, {"armed_profile": "away"})
    await setup_entry(hass, entry)
    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY  # ohne Ausgangsverzögerung


async def test_restore_keeps_bypassed_sensors(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    entry = make_entry()
    _stored(
        hass_storage,
        entry.entry_id,
        {"restore": {"profile": "night", "state": "armed", "bypassed": [WINDOW]}},
    )
    set_sensor(hass, WINDOW, "on")
    await setup_entry(hass, entry, sensors=False)
    state = hass.states.get(PANEL)
    assert state is not None
    assert state.state == AlarmControlPanelState.ARMED_NIGHT
    assert WINDOW in state.attributes["bypassed_sensors"]


async def test_restore_entry_delay_starts_again(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    entry = make_entry()
    _stored(
        hass_storage,
        entry.entry_id,
        {"restore": {"profile": "away", "state": "pending", "trigger_sensor": DOOR}},
    )
    await setup_entry(hass, entry)
    assert _state(hass) == AlarmControlPanelState.PENDING
    await hass.services.async_call(
        "alarm_control_panel", "alarm_disarm", {"entity_id": PANEL}, blocking=True
    )
    assert _state(hass) == AlarmControlPanelState.DISARMED


async def test_restore_never_continues_alarm(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    entry = make_entry()
    _stored(
        hass_storage,
        entry.entry_id,
        {"restore": {"profile": "night", "state": "triggered", "trigger_sensor": WINDOW}},
    )
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    await setup_entry(hass, entry)
    assert _state(hass) == AlarmControlPanelState.ARMED_NIGHT
    assert not any(e.data["type"] == "ActivateReaction" for e in events)
    restored = [e for e in events if e.data["type"] == "RestoredAfterRestart"]
    assert restored[0].data["alarm_was_active"] is True


async def test_alarm_before_restart_goes_to_alarm_recipients(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    push = async_mock_service(hass, "notify", "mobile_app_alarm")
    entry = make_entry({"profiles": {"night": {"notify": ["mobile_app_alarm"]}}})
    _stored(
        hass_storage,
        entry.entry_id,
        {"restore": {"profile": "night", "state": "triggered", "trigger_sensor": WINDOW}},
    )
    await setup_entry(hass, entry)
    await hass.async_block_till_done()
    assert _state(hass) == AlarmControlPanelState.ARMED_NIGHT
    assert any("restart" in c.data["title"].lower() for c in push)


async def test_restore_can_resume_alarm(hass: HomeAssistant, hass_storage: dict[str, Any]) -> None:
    entry = make_entry({"restart_continue_alarm": True})
    _stored(
        hass_storage,
        entry.entry_id,
        {"restore": {"profile": "night", "state": "triggered", "trigger_sensor": WINDOW}},
    )
    await setup_entry(hass, entry)
    await hass.async_block_till_done()
    assert _state(hass) == AlarmControlPanelState.TRIGGERED


async def test_resume_only_while_reaction_was_running(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    entry = make_entry({"restart_continue_alarm": True})
    _stored(
        hass_storage,
        entry.entry_id,
        {"restore": {"profile": "night", "state": "alarm_hold", "trigger_sensor": WINDOW}},
    )
    await setup_entry(hass, entry)
    await hass.async_block_till_done()
    assert _state(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_open_window_at_startup_is_bypassed_not_alarm(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    """Melder meldet erst beim Hochfahren – und offen: überbrücken statt Sirenenalarm."""
    entry = make_entry()
    _stored(hass_storage, entry.entry_id, {"restore": {"profile": "night", "state": "armed"}})
    set_sensor(hass, WINDOW, "unavailable")
    await setup_entry(hass, entry, sensors=False)
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    state = hass.states.get(PANEL)
    assert state is not None
    assert state.state == AlarmControlPanelState.ARMED_NIGHT
    assert WINDOW in state.attributes["bypassed_until_closed"]
    assert WINDOW in state.attributes["bypassed_sensors"]
    # nach der Startphase kurz weg und wieder offen gemeldet: weiter überbrückt, kein Alarm
    await _later(hass, 130)
    set_sensor(hass, WINDOW, "unavailable")
    await hass.async_block_till_done()
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    assert _state(hass) == AlarmControlPanelState.ARMED_NIGHT
    # geschlossen und wieder geöffnet: normal überwacht
    set_sensor(hass, WINDOW, "off")
    await hass.async_block_till_done()
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    assert _state(hass) == AlarmControlPanelState.TRIGGERED


async def test_door_at_startup_starts_entry_delay(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    entry = make_entry()
    _stored(hass_storage, entry.entry_id, {"restore": {"profile": "away", "state": "armed"}})
    set_sensor(hass, DOOR, "unavailable")
    await setup_entry(hass, entry, sensors=False)
    set_sensor(hass, DOOR, "on")
    await hass.async_block_till_done()
    assert _state(hass) == AlarmControlPanelState.PENDING


async def test_no_sensor_lost_messages_during_startup(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    entry = make_entry()
    _stored(hass_storage, entry.entry_id, {"restore": {"profile": "night", "state": "armed"}})
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    await setup_entry(hass, entry)
    set_sensor(hass, WINDOW, "unavailable")
    await hass.async_block_till_done()
    assert not any(e.data["type"] == "SensorUnavailable" for e in events)
    # nach der Startphase gemeldet, wenn er dann noch fehlt
    await _later(hass, 130)
    assert any(e.data["type"] == "SensorUnavailable" for e in events)


async def test_restore_disarmed_stays_disarmed(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    entry = make_entry()
    _stored(hass_storage, entry.entry_id, {"armed_profile": None, "restore": None})
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    await setup_entry(hass, entry)
    assert _state(hass) == AlarmControlPanelState.DISARMED
    assert not any(e.data["type"] in ("RestoredAfterRestart", "RestartedDisarmed") for e in events)


async def test_always_armed_after_start(hass: HomeAssistant) -> None:
    entry = make_entry({"restart_behavior": "armed", "restart_profiles": {"main": "night"}})
    await setup_entry(hass, entry)
    assert _state(hass) == AlarmControlPanelState.DISARMED  # erst nach einer Minute
    await _later(hass, 61)
    assert _state(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_always_armed_refuses_open_sensors(hass: HomeAssistant) -> None:
    entry = make_entry({"restart_behavior": "armed", "restart_profiles": {"main": "night"}})
    await setup_entry(hass, entry)
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    await _later(hass, 61)
    assert _state(hass) == AlarmControlPanelState.DISARMED  # normal geprüft


async def test_restart_saves_details(hass: HomeAssistant, hass_storage: dict[str, Any]) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    await hass.services.async_call(
        "alarm_control_panel", "alarm_arm_night", {"entity_id": PANEL}, blocking=True
    )
    await hass.async_block_till_done()
    await _later(hass, 1)
    saved = hass_storage[f"{DOMAIN}.{entry.entry_id}"]["data"]["restore"]
    assert saved["profile"] == "night"
    assert saved["state"] == "armed"


async def test_options_restart_step(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    for step in ("system", "restart"):
        flow = await hass.config_entries.options.async_configure(
            flow["flow_id"], {"next_step_id": step}
        )
    assert flow["step_id"] == "restart"
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"restart_behavior": "armed"}
    )
    assert flow["errors"] == {"base": "restart_needs_profile"}
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"restart_behavior": "armed", "restart_profile": "away"}
    )
    assert flow["type"] == "menu"
    assert entry.options["restart_behavior"] == "armed"
    assert entry.options["restart_profiles"] == {"main": "away"}
