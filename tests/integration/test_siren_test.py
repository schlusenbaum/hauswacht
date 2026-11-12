"""Integrationstests: Sirenentest.

Die Sirene ist eine ATTRAPPE (Testzustand), siren.turn_on/turn_off sind gemockt – es ertönt
nichts. Geprüft wird, dass der Test nur unter allen Sicherheitsbedingungen sendet.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from homeassistant.auth.const import GROUP_ID_USER
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import Context, HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.hauswacht.const import DOMAIN

from .conftest import PANEL, TEST_MODE, make_entry, setup_entry

SIREN = "siren.flur"
PHONE = "mobile_app_testhandy"
FULL = 31  # an, aus, Töne, Lautstärke, Dauer


class Mocks:
    def __init__(self, hass: HomeAssistant) -> None:
        self.on: list[ServiceCall] = async_mock_service(hass, "siren", "turn_on")
        self.off: list[ServiceCall] = async_mock_service(hass, "siren", "turn_off")
        self.push: list[ServiceCall] = async_mock_service(hass, "notify", PHONE)


async def _setup(hass: HomeAssistant, *, enabled: bool = True, **options: Any) -> Mocks:
    hass.states.async_set(
        SIREN, "off", {"supported_features": FULL, "available_tones": ["burglar", "fire"]}
    )
    mocks = Mocks(hass)
    entry = make_entry(
        {"sirens": [SIREN], "sirens_hardware_enabled": enabled, "notify_system": [PHONE], **options}
    )
    await setup_entry(hass, entry)
    return mocks


async def _test(hass: HomeAssistant, context: Context | None = None, **data: Any) -> None:
    await hass.services.async_call(
        DOMAIN,
        "siren_test",
        {"entity_id": PANEL, "siren": SIREN, **data},
        blocking=True,
        context=context,
    )
    await hass.async_block_till_done()


def _later(hass: HomeAssistant, seconds: float) -> None:
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=seconds))


def _tester(hass: HomeAssistant) -> Any:
    return hass.config_entries.async_entries(DOMAIN)[0].runtime_data.siren_tester


async def test_blocked_without_hardware_release(hass: HomeAssistant) -> None:
    mocks = await _setup(hass, enabled=False)
    with pytest.raises(ServiceValidationError):
        await _test(hass)
    assert mocks.on == []


async def test_short_quiet_test_and_automatic_stop(hass: HomeAssistant) -> None:
    mocks = await _setup(hass)
    await _test(hass)
    assert [c.data for c in mocks.on] == [
        {"entity_id": SIREN, "tone": "burglar", "volume_level": 0.25, "duration": 3}
    ]
    assert _tester(hass).running == SIREN
    # Scharfschalten ist während des Tests gesperrt
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            "alarm_control_panel", "alarm_arm_night", {"entity_id": PANEL}, blocking=True
        )
    _later(hass, 4)
    await hass.async_block_till_done()
    assert [c.data["entity_id"] for c in mocks.off] == [SIREN]
    assert _tester(hass).running is None


async def test_duration_is_capped(hass: HomeAssistant) -> None:
    mocks = await _setup(hass)
    await _test(hass, duration=30, volume="high")
    assert mocks.on[0].data["duration"] == 10
    assert mocks.on[0].data["volume_level"] == 0.75


async def test_test_mode_blocks(hass: HomeAssistant) -> None:
    mocks = await _setup(hass)
    await hass.services.async_call("switch", "turn_on", {"entity_id": TEST_MODE}, blocking=True)
    with pytest.raises(ServiceValidationError):
        await _test(hass)
    assert mocks.on == []


async def test_armed_blocks(hass: HomeAssistant) -> None:
    mocks = await _setup(hass)
    await hass.services.async_call(
        "alarm_control_panel", "alarm_arm_night", {"entity_id": PANEL}, blocking=True
    )
    state = hass.states.get(PANEL)
    assert state is not None
    assert state.state == AlarmControlPanelState.ARMED_NIGHT
    with pytest.raises(ServiceValidationError):
        await _test(hass)
    assert mocks.on == []


async def test_fire_blocks(hass: HomeAssistant) -> None:
    mocks = await _setup(hass)
    hass.states.async_set("binary_sensor.rauchmelder_keller", "on", {"device_class": "smoke"})
    with pytest.raises(ServiceValidationError):
        await _test(hass)
    assert mocks.on == []


async def test_stop_service(hass: HomeAssistant) -> None:
    mocks = await _setup(hass)
    await _test(hass)
    await hass.services.async_call(DOMAIN, "siren_test_stop", {"entity_id": PANEL}, blocking=True)
    assert [c.data["entity_id"] for c in mocks.off] == [SIREN]
    assert _tester(hass).running is None


async def test_only_admins(hass: HomeAssistant) -> None:
    mocks = await _setup(hass)
    guest = await hass.auth.async_create_user("Gast", group_ids=[GROUP_ID_USER])
    assert not guest.is_admin
    with pytest.raises(ServiceValidationError):
        await _test(hass, context=Context(user_id=guest.id))
    assert mocks.on == []


async def test_result_is_recorded(hass: HomeAssistant) -> None:
    await _setup(hass)
    await _test(hass)
    await hass.services.async_call(
        DOMAIN,
        "siren_test_result",
        {"entity_id": PANEL, "siren": SIREN, "heard": True},
        blocking=True,
    )
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    sensor = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{entry.entry_id}_siren_test"
    )
    assert sensor is not None
    state = hass.states.get(sensor)
    assert state is not None
    assert state.state not in ("unknown", "unavailable")
    assert state.attributes["sirens"][0]["heard"] is True


async def test_reminder_and_prewarn(hass: HomeAssistant) -> None:
    mocks = await _setup(hass, siren_test={"reminder_months": 3, "prewarn": True})
    tester = _tester(hass)
    tester._check_reminder(None)
    await hass.async_block_till_done()
    assert any("fällig" in c.data["title"] for c in mocks.push)
    tester.prewarn_seconds = 0
    count = len(mocks.push)
    await _test(hass)
    assert len(mocks.push) == count + 1  # Vorwarnung
    assert mocks.on


async def test_options_flow_one_by_one(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _no_wait(_seconds: float) -> None:
        return None

    monkeypatch.setattr("custom_components.hauswacht.config_flow.asyncio.sleep", _no_wait)
    second = "siren.garten"
    hass.states.async_set(second, "off", {"supported_features": FULL})
    mocks = await _setup(hass, sirens=[SIREN, second])
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    for step in ("sirens", "siren_test"):
        flow = await hass.config_entries.options.async_configure(
            flow["flow_id"], {"next_step_id": step}
        )
    data = {"sirens": [SIREN, second], "tone": "burglar", "volume": "low", "duration": 2}
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {**data, "confirm": False}
    )
    assert flow["errors"] == {"confirm": "siren_test_confirm"}
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {**data, "confirm": True}
    )
    assert flow["step_id"] == "siren_test_next"
    assert "✅" in flow["description_placeholders"]["preview"]
    assert mocks.on == []  # noch nichts gesendet
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "siren_test_go"}
    )
    assert flow["step_id"] == "siren_test_heard"
    assert [c.data["entity_id"] for c in mocks.on] == [SIREN]
    _later(hass, 3)
    await hass.async_block_till_done()
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "siren_test_yes"}
    )
    assert flow["step_id"] == "siren_test_next"  # zweite Sirene: erneut fragen
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "siren_test_skip"}
    )
    assert flow["step_id"] == "sirens"
    assert len(mocks.on) == 1
    assert _tester(hass).records[SIREN].heard is True
