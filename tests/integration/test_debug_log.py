"""Integrationstests: Debug-Log (ADR 0020).

Mit eingeschaltetem Debug stehen die Entscheidungen im Log – aber nie eine PIN, ein Name oder
ein Nachrichtentext. Es werden keine Sirenen oder Geräte angesprochen.
"""

from __future__ import annotations

import logging
from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.hauswacht.core.pin import hash_pin

from .conftest import DOOR, PANEL, WINDOW, make_entry, set_sensor, setup_entry

PIN = "1357"
PHONE = "mobile_app_testhandy"


def _user(name: str) -> dict[str, Any]:
    hashed = hash_pin(PIN)
    return {"name": name, "pin_salt": hashed.salt, "pin_digest": hashed.digest}


async def _service(hass: HomeAssistant, domain: str, service: str, **data: Any) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)
    await hass.async_block_till_done()


async def test_debug_log_shows_decisions_without_secrets(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    async_mock_service(hass, "notify", PHONE)
    caplog.set_level(logging.DEBUG, logger="custom_components.hauswacht")
    await setup_entry(
        hass,
        make_entry({"users": {"p": _user("Petra Beispiel")}, "notify_system": [f"notify.{PHONE}"]}),
    )
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    # Fenster auf: im Profil „Nacht“ überwacht → Alarm (ohne Sirenen)
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL, code=PIN)
    # Unscharf: Tür auf zählt nicht
    set_sensor(hass, DOOR, "on")
    await hass.async_block_till_done()

    debug = "\n".join(r.getMessage() for r in caplog.records if r.levelno == logging.DEBUG)
    assert "Bereich main: ArmRequested(profile=night" in debug
    assert f"Melder {WINDOW} off → on" in debug
    assert "überwacht, löst aus" in debug
    assert "StateChanged(old=armed, new=triggered" in debug
    assert "DisarmRequested(" in debug
    assert f"Melder {DOOR} off → on" in debug
    assert "unscharf, nicht immer aktiv" in debug
    assert "Benachrichtigung alarm" in debug

    everything = "\n".join(r.getMessage() for r in caplog.records)
    for secret in (PIN, "Petra", "Beispiel"):
        assert secret not in everything, secret


async def test_no_debug_lines_when_debug_is_off(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO, logger="custom_components.hauswacht")
    await setup_entry(hass, make_entry())
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    assert not [r for r in caplog.records if r.levelno == logging.DEBUG]
