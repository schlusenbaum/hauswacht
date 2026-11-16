"""Integrationstests: Sirenen, die vor einem Neustart an waren, werden danach ausgeschaltet.

Der Zustand "vor dem Neustart" wird über den gespeicherten Zustand vorgegeben. Die
Sirenen-Dienste sind ATTRAPPEN (async_mock_service); es wird nichts geschaltet.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    async_capture_events,
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.hauswacht.const import DOMAIN, EVENT_HAUSWACHT

from .conftest import PANEL, WINDOW, make_entry, set_sensor, setup_entry

pytestmark = pytest.mark.parametrize("expected_lingering_timers", [True])

# Sirene ohne eigene Laufzeit (nur ein/aus) – wie ein Relais. Als siren.…, weil Hauswacht die
# switch-Plattform selbst lädt und damit Attrappen für switch.turn_off ersetzen würde.
RELAY = "siren.sirene_garage"
ON_OFF_ONLY = 3  # SirenEntityFeature.TURN_ON | TURN_OFF
PHONE = "mobile_app_testhandy"


class Mocks:
    def __init__(self, hass: HomeAssistant) -> None:
        self.on: list[ServiceCall] = async_mock_service(hass, "siren", "turn_on")
        self.off: list[ServiceCall] = async_mock_service(hass, "siren", "turn_off")
        self.push: list[ServiceCall] = async_mock_service(hass, "notify", PHONE)


def _stored(hass_storage: dict[str, Any], entry_id: str, data: dict[str, Any]) -> None:
    hass_storage[f"{DOMAIN}.{entry_id}"] = {
        "version": 1,
        "minor_version": 1,
        "key": f"{DOMAIN}.{entry_id}",
        "data": data,
    }


def _options(**extra: Any) -> dict[str, Any]:
    night = {"sirens": [RELAY], "notify": [PHONE], "exit_delay": 0, "entry_delay": 0}
    return {"sirens": [RELAY], "notify_system": [PHONE], "profiles": {"night": night}, **extra}


async def _start(
    hass: HomeAssistant, hass_storage: dict[str, Any], saved: dict[str, Any], **options: Any
) -> Mocks:
    mocks = Mocks(hass)
    hass.states.async_set(RELAY, "on", {"supported_features": ON_OFF_ONLY})
    entry = make_entry(_options(**options))
    _stored(hass_storage, entry.entry_id, saved)
    await setup_entry(hass, entry)
    await hass.async_block_till_done()
    return mocks


async def _later(hass: HomeAssistant, seconds: float) -> None:
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=seconds))
    await hass.async_block_till_done()


async def test_siren_on_before_restart_is_switched_off(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    mocks = await _start(
        hass,
        hass_storage,
        {"sirens": {"activated": [RELAY], "pending_stop": []}},
        sirens_hardware_enabled=True,
    )
    assert [c.data["entity_id"] for c in mocks.off] == [RELAY]
    assert mocks.on == []
    assert any("switched off" in c.data["message"] for c in mocks.push)


async def test_switched_off_even_without_hardware_release(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    """Ausschalten ist die sichere Richtung – auch wenn die Freigabe inzwischen aus ist."""
    mocks = await _start(hass, hass_storage, {"sirens": {"activated": [RELAY]}})
    assert [c.data["entity_id"] for c in mocks.off] == [RELAY]


async def test_fire_blocks_switching_off_and_retries(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    hass.states.async_set("binary_sensor.rm_flur_smoke", "on", {"device_class": "smoke"})
    mocks = await _start(
        hass, hass_storage, {"sirens": {"activated": [RELAY]}}, sirens_hardware_enabled=True
    )
    assert mocks.off == []
    assert any("fire lock" in c.data["message"] for c in mocks.push)
    # Brand vorbei: beim nächsten Versuch (jede Minute) ausgeschaltet
    hass.states.async_set("binary_sensor.rm_flur_smoke", "off", {"device_class": "smoke"})
    await _later(hass, 61)
    assert [c.data["entity_id"] for c in mocks.off] == [RELAY]


async def test_disarming_before_switch_off_does_not_forget(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    hass.states.async_set("binary_sensor.rm_flur_smoke", "on", {"device_class": "smoke"})
    mocks = await _start(
        hass,
        hass_storage,
        {
            "restore": {"profile": "night", "state": "armed"},
            "sirens": {"activated": [RELAY]},
        },
        sirens_hardware_enabled=True,
    )
    await hass.services.async_call(
        "alarm_control_panel", "alarm_disarm", {"entity_id": PANEL}, blocking=True
    )
    await hass.async_block_till_done()
    assert mocks.off == []
    hass.states.async_set("binary_sensor.rm_flur_smoke", "off", {"device_class": "smoke"})
    await _later(hass, 61)
    assert [c.data["entity_id"] for c in mocks.off] == [RELAY]


async def test_unknown_or_removed_siren_is_ignored(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    mocks = await _start(
        hass,
        hass_storage,
        {"sirens": {"activated": ["switch.nicht_mehr_eingetragen"]}},
        sirens_hardware_enabled=True,
    )
    assert mocks.off == []


async def test_nothing_saved_switches_nothing(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    mocks = await _start(hass, hass_storage, {}, sirens_hardware_enabled=True)
    await _later(hass, 130)
    assert mocks.off == []
    assert mocks.on == []


async def test_second_attempt_after_startup_only_if_still_on(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    mocks = await _start(
        hass, hass_storage, {"sirens": {"activated": [RELAY]}}, sirens_hardware_enabled=True
    )
    assert len(mocks.off) == 1
    # Sirene meldet weiter "an" (z. B. erst jetzt wieder erreichbar): zweiter Versuch
    await _later(hass, 130)
    assert len(mocks.off) == 2
    # danach nichts mehr
    await _later(hass, 300)
    assert len(mocks.off) == 2


async def test_new_alarm_is_not_switched_off_by_second_attempt(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    mocks = await _start(
        hass,
        hass_storage,
        {"restore": {"profile": "night", "state": "armed"}, "sirens": {"activated": [RELAY]}},
        sirens_hardware_enabled=True,
    )
    assert len(mocks.off) == 1
    # neuer Alarm noch in der Startphase schaltet die Sirene wieder ein
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    assert [c.data["entity_id"] for c in mocks.on] == [RELAY]
    # zweiter Versuch nach der Startphase: die Sirene gehört jetzt dem neuen Alarm
    await _later(hass, 130)
    assert len(mocks.off) == 1


async def test_activated_sirens_are_saved(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    mocks = await _start(
        hass,
        hass_storage,
        {"restore": {"profile": "night", "state": "armed"}},
        sirens_hardware_enabled=True,
    )
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    assert mocks.on
    assert any(e.data["type"] == "SirenDecision" for e in events)
    await _later(hass, 1)
    key = next(k for k in hass_storage if k.startswith(f"{DOMAIN}.") and k.count(".") == 1)
    assert hass_storage[key]["data"]["sirens"]["activated"] == [RELAY]
