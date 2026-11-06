"""Integrationstests: Sirenen und Benachrichtigungen.

Sirenen- und notify-Dienste sind hier ATTRAPPEN (async_mock_service). Es existiert kein
Gerät; geprüft wird nur, welche Dienstaufrufe Hauswacht absetzen WÜRDE.
"""

from __future__ import annotations

from typing import Any

import pytest
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
    async_mock_service,
)

from custom_components.hauswacht.const import EVENT_HAUSWACHT

from .conftest import PANEL, TEST_MODE, WINDOW, make_entry, set_sensor, setup_entry

SIREN = "siren.rm_diele"
SMOKE = "binary_sensor.rm_diele_smoke"
TEST_BUTTON = "binary_sensor.rm_diele_test"
MAX_DURATION = "number.rm_diele_max_duration"
PHONE = "mobile_app_testhandy"


def _smoke_detector(hass: HomeAssistant) -> None:
    """Rauchmelder mit Sirene als Registry-Einträge und Testzustände (kein echtes Gerät)."""
    source = MockConfigEntry(domain="test")
    source.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=source.entry_id, identifiers={("test", "rm_diele")}
    )
    registry = er.async_get(hass)
    for domain, uid, object_id, device_class in (
        ("siren", "rm_siren", "rm_diele", None),
        ("binary_sensor", "rm_smoke", "rm_diele_smoke", "smoke"),
        ("binary_sensor", "rm_test", "rm_diele_test", None),
        ("number", "rm_max", "rm_diele_max_duration", None),
    ):
        registry.async_get_or_create(
            domain,
            "test",
            uid,
            suggested_object_id=object_id,
            device_id=device.id,
            config_entry=source,
            original_device_class=device_class,
        )
    hass.states.async_set(SIREN, "off")
    hass.states.async_set(SMOKE, "off", {"device_class": "smoke"})
    hass.states.async_set(TEST_BUTTON, "off")
    hass.states.async_set(MAX_DURATION, "240")


def _options(**extra: Any) -> dict[str, Any]:
    night: dict[str, Any] = {
        "sirens": [SIREN],
        "siren_tone": "burglar",
        "siren_volume": "high",
        "notify": [PHONE],
    }
    night.update(extra.pop("night", {}))
    return {"sirens": [SIREN], "profiles": {"night": night}, **extra}


class Mocks:
    def __init__(self, hass: HomeAssistant) -> None:
        self.on: list[ServiceCall] = async_mock_service(hass, "siren", "turn_on")
        self.off: list[ServiceCall] = async_mock_service(hass, "siren", "turn_off")
        self.push: list[ServiceCall] = async_mock_service(hass, "notify", PHONE)


async def _setup(hass: HomeAssistant, **options: Any) -> Mocks:
    _smoke_detector(hass)
    mocks = Mocks(hass)
    await setup_entry(hass, make_entry(_options(**options)))
    return mocks


async def _service(hass: HomeAssistant, domain: str, service: str, **data: Any) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)
    await hass.async_block_till_done()


async def _alarm(hass: HomeAssistant) -> None:
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    state = hass.states.get(PANEL)
    assert state is not None
    assert state.state == AlarmControlPanelState.TRIGGERED


# --- Hardware-Sperre (Standard) ---------------------------------------------


async def test_sirens_locked_by_default(hass: HomeAssistant) -> None:
    mocks = await _setup(hass)
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    await _alarm(hass)
    assert mocks.on == []
    decision = next(e for e in events if e.data["type"] == "SirenDecision")
    assert decision.data["blocked"] == {SIREN: "hardware_disabled"}
    # Push geht trotzdem raus
    assert len(mocks.push) == 1
    assert "EINBRUCHALARM" in mocks.push[0].data["title"]
    assert "hardware_disabled" in mocks.push[0].data["message"]


# --- Freigegebene Hardware --------------------------------------------------


async def test_released_siren_is_activated(hass: HomeAssistant) -> None:
    mocks = await _setup(hass, sirens_hardware_enabled=True)
    await _alarm(hass)
    assert len(mocks.on) == 1
    call = mocks.on[0].data
    assert call["entity_id"] == SIREN
    assert call["tone"] == "burglar"
    assert call["volume_level"] == 0.75
    assert call["duration"] == 180


async def test_duration_capped_to_device_maximum(hass: HomeAssistant) -> None:
    mocks = await _setup(hass, sirens_hardware_enabled=True, night={"reaction_time": 600})
    await _alarm(hass)
    assert mocks.on[0].data["duration"] == 240


async def test_disarm_stops_only_own_siren(hass: HomeAssistant) -> None:
    mocks = await _setup(hass, sirens_hardware_enabled=True)
    await _alarm(hass)
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL)
    assert [c.data["entity_id"] for c in mocks.off] == [SIREN]


async def test_silent_profile_sends_only_push(hass: HomeAssistant) -> None:
    mocks = await _setup(hass, sirens_hardware_enabled=True, night={"silent": True})
    await _alarm(hass)
    assert mocks.on == []
    assert len(mocks.push) == 1


async def test_profile_without_sirens(hass: HomeAssistant) -> None:
    mocks = await _setup(hass, sirens_hardware_enabled=True, night={"sirens": []})
    await _alarm(hass)
    assert mocks.on == []


# --- Testmodus --------------------------------------------------------------


async def test_test_mode_never_activates_sirens(hass: HomeAssistant) -> None:
    mocks = await _setup(hass, sirens_hardware_enabled=True)
    await _service(hass, "switch", "turn_on", entity_id=TEST_MODE)
    await _alarm(hass)
    assert mocks.on == []
    assert mocks.push == []  # Push im Testmodus standardmäßig unterdrückt
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL)
    assert mocks.off == []


async def test_test_mode_push_when_allowed(hass: HomeAssistant) -> None:
    mocks = await _setup(hass, sirens_hardware_enabled=True, notify_in_test_mode=True)
    await _service(hass, "switch", "turn_on", entity_id=TEST_MODE)
    await _alarm(hass)
    assert mocks.on == []
    assert mocks.push[0].data["title"].startswith("[TEST]")


async def test_simulated_trigger_never_activates_sirens(hass: HomeAssistant) -> None:
    mocks = await _setup(hass, sirens_hardware_enabled=True)
    await _service(hass, "switch", "turn_on", entity_id=TEST_MODE)
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    await _service(hass, "hauswacht", "simulate_trigger", entity_id=PANEL, sensor=WINDOW)
    assert mocks.on == []


# --- Brandschutz ------------------------------------------------------------


@pytest.mark.parametrize(
    ("entity_id", "state"),
    [(SMOKE, "on"), (TEST_BUTTON, "on"), (SMOKE, "unavailable")],
)
async def test_fire_or_unknown_on_siren_device_blocks(
    hass: HomeAssistant, entity_id: str, state: str
) -> None:
    mocks = await _setup(hass, sirens_hardware_enabled=True)
    hass.states.async_set(entity_id, state, {"device_class": "smoke"} if entity_id == SMOKE else {})
    await _alarm(hass)
    assert mocks.on == []


async def test_fire_at_other_detector_blocks(hass: HomeAssistant) -> None:
    mocks = await _setup(hass, sirens_hardware_enabled=True)
    hass.states.async_set("binary_sensor.rauch_keller", "on", {"device_class": "smoke"})
    await _alarm(hass)
    assert mocks.on == []


async def test_unavailable_other_detector_does_not_block(hass: HomeAssistant) -> None:
    mocks = await _setup(hass, sirens_hardware_enabled=True)
    hass.states.async_set("binary_sensor.rauch_keller", "unavailable", {"device_class": "smoke"})
    await _alarm(hass)
    assert len(mocks.on) == 1


async def test_fire_during_alarm_blocks_turn_off(hass: HomeAssistant) -> None:
    mocks = await _setup(hass, sirens_hardware_enabled=True)
    await _alarm(hass)
    assert len(mocks.on) == 1
    hass.states.async_set(SMOKE, "on", {"device_class": "smoke"})
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL)
    state = hass.states.get(PANEL)
    assert state is not None
    assert state.state == AlarmControlPanelState.DISARMED
    assert mocks.off == []  # Brand: niemals ausschalten


async def test_number_entities_are_never_written(hass: HomeAssistant) -> None:
    set_value = async_mock_service(hass, "number", "set_value")
    mocks = await _setup(hass, sirens_hardware_enabled=True)
    await _alarm(hass)
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL)
    assert len(mocks.on) == 1
    assert set_value == []


# --- Systemmeldungen --------------------------------------------------------


async def test_tamper_sends_system_message(hass: HomeAssistant) -> None:
    mocks = await _setup(hass, notify_system=[PHONE])
    set_sensor(hass, "binary_sensor.kontakt_tamper", "on")
    await hass.async_block_till_done()
    assert "Manipulation" in mocks.push[0].data["title"]


# --- Optionen ---------------------------------------------------------------


async def test_enabling_hardware_requires_confirmation(hass: HomeAssistant) -> None:
    _smoke_detector(hass)
    entry = make_entry()
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "sirens"}
    )
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"sirens": [SIREN], "sirens_hardware_enabled": True}
    )
    assert flow["errors"] == {"base": "confirm_hardware_required"}
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"],
        {"sirens": [SIREN], "sirens_hardware_enabled": True, "confirm_hardware": True},
    )
    assert flow["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options["sirens_hardware_enabled"] is True
    assert entry.options["sirens"] == [SIREN]


# --- Gerätefähigkeiten ------------------------------------------------------

PLAIN = "siren.aussensirene"


async def test_plain_siren_gets_only_supported_fields(hass: HomeAssistant) -> None:
    """Einfache Sirene ohne Rauchmelder: nur Ein/Aus, also ohne Ton, Lautstärke, Dauer."""
    mocks = await _setup(
        hass, sirens=[PLAIN], sirens_hardware_enabled=True, night={"sirens": [PLAIN]}
    )
    hass.states.async_set(PLAIN, "off", {"supported_features": 3})
    await _alarm(hass)
    assert [c.data for c in mocks.on] == [{"entity_id": PLAIN}]


async def test_smoke_detector_without_tone_selection_is_not_used(hass: HomeAssistant) -> None:
    mocks = await _setup(hass, sirens_hardware_enabled=True)
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    hass.states.async_set(SIREN, "off", {"supported_features": 3})
    await _alarm(hass)
    assert mocks.on == []
    decision = next(e for e in events if e.data["type"] == "SirenDecision")
    assert decision.data["blocked"] == {SIREN: "no_burglar_tone"}


async def test_other_burglar_tone_when_requested_one_missing(hass: HomeAssistant) -> None:
    mocks = await _setup(hass, sirens_hardware_enabled=True)
    hass.states.async_set(
        SIREN,
        "off",
        {"supported_features": 31, "available_tones": {1: "fire", 2: "emergency"}},
    )
    await _alarm(hass)
    assert mocks.on[0].data["tone"] == "emergency"


async def test_device_with_only_fire_tones_is_not_used(hass: HomeAssistant) -> None:
    mocks = await _setup(hass, sirens_hardware_enabled=True)
    hass.states.async_set(
        SIREN, "off", {"supported_features": 31, "available_tones": ["fire", "fire_panic"]}
    )
    await _alarm(hass)
    assert mocks.on == []
