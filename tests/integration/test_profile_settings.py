"""Integrationstests: Profil-Einstellungen über Entitäten (Dashboard)."""

from __future__ import annotations

from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError

from .conftest import PANEL, make_entry, setup_entry

EDIT = "select.hauswacht_edit_profile"
EXIT_DELAY = "number.hauswacht_exit_delay"
SILENT = "switch.hauswacht_silent_alarm"
TONE = "select.hauswacht_siren_tone"
ARM_TIME = "time.hauswacht_arm_automatically_at"


async def _service(hass: HomeAssistant, domain: str, service: str, **data: Any) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)
    await hass.async_block_till_done()


def _state(hass: HomeAssistant, entity_id: str) -> str:
    state = hass.states.get(entity_id)
    assert state is not None, entity_id
    return state.state


async def test_edit_profile_shows_its_values(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    await _service(hass, "select", "select_option", entity_id=EDIT, option="Nacht")
    assert _state(hass, EXIT_DELAY) == "0"
    await _service(hass, "select", "select_option", entity_id=EDIT, option="Abwesend")
    assert _state(hass, EXIT_DELAY) == "60"


async def test_change_settings_updates_profile(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    await _service(hass, "select", "select_option", entity_id=EDIT, option="Nacht")

    await _service(hass, "number", "set_value", entity_id=EXIT_DELAY, value=45)
    await _service(hass, "switch", "turn_on", entity_id=SILENT)
    await _service(hass, "select", "select_option", entity_id=TONE, option="emergency")
    await _service(hass, "time", "set_value", entity_id=ARM_TIME, time="22:30:00")

    night = entry.options["profiles"]["night"]
    assert night["exit_delay"] == 45
    assert night["silent"] is True
    assert night["siren_tone"] == "emergency"
    assert night["auto_arm_time"] == "22:30:00"
    assert night["name"] == "Nacht"  # Rest unverändert
    assert entry.options["profiles"]["away"]["exit_delay"] == 60
    # Auswahl bleibt nach dem Neuladen erhalten
    assert _state(hass, EDIT) == "Nacht"
    assert _state(hass, EXIT_DELAY) == "45"


async def test_settings_locked_while_armed(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    assert _state(hass, EXIT_DELAY) == "unavailable"
    # Home Assistant leitet Änderungen an nicht verfügbare Entitäten gar nicht weiter
    await _service(hass, "number", "set_value", entity_id=EXIT_DELAY, value=300)
    assert entry.options["profiles"]["night"]["exit_delay"] == 0


async def test_runtime_refuses_change_while_armed(hass: HomeAssistant) -> None:
    """Zweite Sperre direkt in Hauswacht, falls die Entität doch aufgerufen wird."""
    entry = make_entry()
    await setup_entry(hass, entry)
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    with pytest.raises(ServiceValidationError):
        await entry.runtime_data.async_set_profile_setting("exit_delay", 300)
    assert entry.options["profiles"]["night"]["exit_delay"] == 0
