"""Integrationstests: Hauswacht in einer echten (Test-)Home-Assistant-Instanz.

Es werden keine Sirenen und keine Geräte angesprochen.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from typing import Any

import pytest
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import ServiceValidationError
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    async_capture_events,
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.hauswacht.const import DOMAIN, EVENT_HAUSWACHT
from custom_components.hauswacht.core.pin import hash_pin

from .conftest import PANEL, TEST_MODE, make_entry, setup_entry


async def _service(hass: HomeAssistant, domain: str, service: str, **data: Any) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)
    await hass.async_block_till_done()


async def _advance(hass: HomeAssistant, seconds: int) -> None:
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=seconds))
    await hass.async_block_till_done()


def _state(hass: HomeAssistant) -> str:
    state = hass.states.get(PANEL)
    assert state is not None
    return state.state


def _pin_options(pin: str = "4711", *, arm_required: bool = False) -> dict[str, Any]:
    stored = hash_pin(pin)
    return {"pin_salt": stored.salt, "pin_digest": stored.digest, "code_arm_required": arm_required}


# --- Einrichtung ------------------------------------------------------------


async def test_config_flow_creates_entry(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Hauswacht"


async def test_only_one_instance(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_setup_starts_disarmed(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    assert entry.state is ConfigEntryState.LOADED
    assert _state(hass) == AlarmControlPanelState.DISARMED
    test_mode = hass.states.get(TEST_MODE)
    assert test_mode is not None
    assert test_mode.state == "off"


async def test_unload(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED


# --- Scharf / Unscharf ------------------------------------------------------


async def test_arm_night_without_exit_delay(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    assert _state(hass) == AlarmControlPanelState.ARMED_NIGHT
    state = hass.states.get(PANEL)
    assert state is not None
    assert state.attributes["profile"] == "night"


async def test_arm_away_with_exit_delay(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    await _service(hass, "alarm_control_panel", "alarm_arm_away", entity_id=PANEL)
    assert _state(hass) == AlarmControlPanelState.ARMING
    state = hass.states.get(PANEL)
    assert state is not None
    assert state.attributes["timer"] == "exit_delay"
    assert state.attributes["timer_ends_at"] is not None

    await _advance(hass, 30)
    assert _state(hass) == AlarmControlPanelState.ARMING
    await _advance(hass, 61)
    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY


async def test_disarm_during_exit_delay(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    await _service(hass, "alarm_control_panel", "alarm_arm_away", entity_id=PANEL)
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL)
    assert _state(hass) == AlarmControlPanelState.DISARMED
    await _advance(hass, 120)  # alter Timer darf nichts mehr bewirken
    assert _state(hass) == AlarmControlPanelState.DISARMED


async def test_profile_timings_from_options(hass: HomeAssistant) -> None:
    options = {"profiles": {"away": {"exit_delay": 0, "entry_delay": 10, "reaction_time": 60}}}
    await setup_entry(hass, make_entry(options))
    await _service(hass, "alarm_control_panel", "alarm_arm_away", entity_id=PANEL)
    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY


async def test_arming_other_profile_while_armed_is_rejected(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    with pytest.raises(ServiceValidationError):
        await _service(hass, "alarm_control_panel", "alarm_arm_home", entity_id=PANEL)
    assert _state(hass) == AlarmControlPanelState.ARMED_NIGHT


# --- PIN --------------------------------------------------------------------


async def test_disarm_requires_correct_pin(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry(_pin_options()))
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    with pytest.raises(ServiceValidationError):
        await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL, code="1234")
    assert _state(hass) == AlarmControlPanelState.ARMED_NIGHT
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL, code="4711")
    assert _state(hass) == AlarmControlPanelState.DISARMED


async def test_pin_for_arming_when_configured(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry(_pin_options(arm_required=True)))
    state = hass.states.get(PANEL)
    assert state is not None
    assert state.attributes["code_arm_required"] is True
    with pytest.raises(ServiceValidationError):
        await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL, code="0000")
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL, code="4711")
    assert _state(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_without_pin_no_code_needed(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    state = hass.states.get(PANEL)
    assert state is not None
    assert state.attributes.get("code_format") is None


# --- Testmodus --------------------------------------------------------------


async def test_test_mode_switch(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    await _service(hass, "switch", "turn_on", entity_id=TEST_MODE)
    state = hass.states.get(TEST_MODE)
    assert state is not None
    assert state.state == "on"


async def test_test_mode_cannot_change_while_armed(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    with pytest.raises(ServiceValidationError):
        await _service(hass, "switch", "turn_on", entity_id=TEST_MODE)
    state = hass.states.get(TEST_MODE)
    assert state is not None
    assert state.state == "off"


# --- Neustart ---------------------------------------------------------------


async def test_restart_while_armed_comes_back_disarmed(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    entry = make_entry()
    hass_storage[f"{DOMAIN}.{entry.entry_id}"] = {
        "version": 1,
        "minor_version": 1,
        "key": f"{DOMAIN}.{entry.entry_id}",
        "data": {"armed_profile": "away", "test_mode": True},
    }
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    await setup_entry(hass, entry)

    assert _state(hass) == AlarmControlPanelState.DISARMED
    restart = [e for e in events if e.data["type"] == "RestartedDisarmed"]
    assert restart
    assert restart[0].data["previous_profile_id"] == "away"
    test_mode = hass.states.get(TEST_MODE)
    assert test_mode is not None
    assert test_mode.state == "on"  # Testmodus bleibt erhalten


async def test_reload_while_armed_disarms(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert _state(hass) == AlarmControlPanelState.DISARMED


# --- Optionen ---------------------------------------------------------------


async def test_options_flow_sets_pin(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "code"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"new_pin": "12a"}
    )
    assert result["errors"] == {"new_pin": "invalid_pin"}
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"new_pin": "2468"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert "2468" not in str(entry.options)
    state = hass.states.get(PANEL)
    assert state is not None
    assert state.attributes["code_format"] == "number"


async def test_options_flow_profile_timings(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "profiles"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "profile_edit"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"profile": "away"}
    )
    assert result["step_id"] == "profile_settings"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"exit_delay": 5, "entry_delay": 20, "reaction_time": 120}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    away = entry.options["profiles"]["away"]
    assert (away["exit_delay"], away["entry_delay"], away["reaction_time"]) == (5, 20, 120)
    assert away["zones"] == ["aussenhaut", "keller"]  # bisherige Zonen bleiben erhalten


async def test_options_flow_blocked_while_armed(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "disarm_first"


# --- Profil "Individuell" ---------------------------------------------------


async def test_custom_profile(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    await _service(hass, "alarm_control_panel", "alarm_arm_custom_bypass", entity_id=PANEL)
    assert _state(hass) == AlarmControlPanelState.ARMED_CUSTOM_BYPASS
    state = hass.states.get(PANEL)
    assert state is not None
    assert state.attributes["profile"] == "custom"


# --- Schutz gegen PIN-Raten -------------------------------------------------


async def test_pin_lock_after_five_wrong_entries(hass: HomeAssistant) -> None:
    push = async_mock_service(hass, "notify", "mobile_app_test")
    await setup_entry(hass, make_entry({**_pin_options(), "notify_system": ["mobile_app_test"]}))
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    for _ in range(5):
        with pytest.raises(ServiceValidationError):
            await _service(
                hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL, code="0000"
            )
    # Gesperrt: auch der richtige PIN wird jetzt abgelehnt
    with pytest.raises(ServiceValidationError, match=r"."):
        await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL, code="4711")
    assert _state(hass) == AlarmControlPanelState.ARMED_NIGHT
    assert len(push) >= 3  # Warnungen ab dem 3. Fehlversuch

    await _advance(hass, 61)
    _shift_monotonic(hass, 61)
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL, code="4711")
    assert _state(hass) == AlarmControlPanelState.DISARMED


def _shift_monotonic(hass: HomeAssistant, seconds: float) -> None:
    """Die Sperre nutzt time.monotonic(); im Test verschieben wir ihr Ende direkt."""
    entry = hass.config_entries.async_entries("hauswacht")[0]
    runtime = entry.runtime_data
    runtime._code_guard = replace(
        runtime._code_guard, locked_until=runtime._code_guard.locked_until - seconds
    )
