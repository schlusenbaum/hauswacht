"""Integrationstests: Benachrichtigungen pro Ereignis, Knöpfe beim Scharfschalten, Erinnerung.

notify-Dienste sind ATTRAPPEN. Sirenen werden nicht freigegeben, Personen sind Testzustände.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import Context, HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from pytest_homeassistant_custom_component.common import (
    MockUser,
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.hauswacht.const import (
    PUSH_ACTION_EVENT,
    PUSH_ARM_FORCE_PREFIX,
    PUSH_ARM_NOW_PREFIX,
    PUSH_ARM_RETRY_PREFIX,
)

from .conftest import DOOR, PANEL, WINDOW, make_entry, set_sensor, setup_entry

PHONE = "mobile_app_testhandy"
OTHER = "mobile_app_zweithandy"
PERSON_A = "person.anna"
PERSON_B = "person.ben"


async def _service(hass: HomeAssistant, domain: str, service: str, **data: Any) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)
    await hass.async_block_till_done()


def _panel(hass: HomeAssistant) -> str:
    state = hass.states.get(PANEL)
    assert state is not None
    return state.state


def _titles(calls: list[ServiceCall]) -> list[str]:
    return [str(c.data.get("title", "")) for c in calls]


def _actions(call: ServiceCall) -> dict[str, str]:
    return {a["title"]: a["action"] for a in call.data["data"]["actions"]}


async def _press(hass: HomeAssistant, action: str, user_id: str | None) -> None:
    hass.bus.async_fire(PUSH_ACTION_EVENT, {"action": action}, context=Context(user_id=user_id))
    await hass.async_block_till_done()


# --- Ereignisse an/aus und Empfänger ----------------------------------------


async def test_armed_and_disarmed_off_by_default(hass: HomeAssistant) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    await setup_entry(hass, make_entry({"notify_system": [PHONE]}))
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL)
    assert push == []


async def test_armed_and_disarmed_when_enabled(hass: HomeAssistant) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    other = async_mock_service(hass, "notify", OTHER)
    options = {
        "notify_system": [PHONE],
        "events": {
            "armed": {"enabled": True, "targets": []},
            "disarmed": {"enabled": True, "targets": [OTHER]},
        },
    }
    await setup_entry(hass, make_entry(options))
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL)
    messages = [c for c in push if c.data["message"] != "clear_notification"]
    assert len(messages) == 1
    assert "armed" in messages[0].data["title"].lower()
    # Bekommt die Unscharf-Nachricht nicht: die Scharf-Nachricht wird weggeräumt
    assert push[-1].data["message"] == "clear_notification"
    assert len(other) == 1  # eigene Empfänger statt der allgemeinen
    assert "disarmed" in other[0].data["title"].lower()


async def test_alarm_event_can_be_switched_off(hass: HomeAssistant) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    options = {
        "profiles": {"night": {"notify": [PHONE]}},
        "events": {"alarm": {"enabled": False, "targets": []}},
    }
    await setup_entry(hass, make_entry(options))
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.TRIGGERED
    assert push == []


async def test_alarm_push_is_critical(hass: HomeAssistant) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    await setup_entry(hass, make_entry({"profiles": {"night": {"notify": [PHONE]}}}))
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    data = push[0].data["data"]
    assert data["channel"] == "alarm_stream"
    assert data["push"]["interruption-level"] == "critical"
    assert data["push"]["sound"]["critical"] == 1


async def test_critical_alerts_can_be_switched_off(hass: HomeAssistant) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    options = {"critical_alerts": False, "profiles": {"night": {"notify": [PHONE]}}}
    await setup_entry(hass, make_entry(options))
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    data = push[0].data["data"]
    assert "channel" not in data
    assert data["push"]["interruption-level"] == "time-sensitive"


# --- Scharfschalten abgelehnt: "Trotzdem scharf" / "Erneut versuchen" --------


async def test_arm_failed_push_with_force_button(
    hass: HomeAssistant, hass_admin_user: MockUser
) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    options = {"notify_system": [PHONE], "profiles": {"home": {"open_policy": "confirm"}}}
    await setup_entry(hass, make_entry(options))
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    with pytest.raises(ServiceValidationError):
        await _service(hass, "alarm_control_panel", "alarm_arm_home", entity_id=PANEL)

    assert len(push) == 1
    assert "not armed" in push[0].data["title"]
    actions = _actions(push[0])
    assert set(actions) == {"Arm anyway", "Try again"}
    assert actions["Arm anyway"].startswith(PUSH_ARM_FORCE_PREFIX)
    assert actions["Try again"].startswith(PUSH_ARM_RETRY_PREFIX)

    await _press(hass, actions["Arm anyway"], hass_admin_user.id)
    state = hass.states.get(PANEL)
    assert state is not None
    assert state.state == AlarmControlPanelState.ARMED_HOME
    assert state.attributes["bypassed_sensors"] == [WINDOW]


async def test_arm_failed_retry_button(hass: HomeAssistant, hass_admin_user: MockUser) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    await setup_entry(hass, make_entry({"notify_system": [PHONE]}))
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    with pytest.raises(ServiceValidationError):
        await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    actions = _actions(push[0])
    assert set(actions) == {"Try again"}  # Überbrücken ist nicht erlaubt

    # Fenster noch offen: erneut abgelehnt, neue Nachricht mit neuem Knopf
    await _press(hass, actions["Try again"], hass_admin_user.id)
    assert _panel(hass) == AlarmControlPanelState.DISARMED
    assert len(push) == 2

    set_sensor(hass, WINDOW, "off")
    await hass.async_block_till_done()
    await _press(hass, _actions(push[1])["Try again"], hass_admin_user.id)
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_arm_button_needs_user_and_is_single_use(
    hass: HomeAssistant, hass_admin_user: MockUser
) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    await setup_entry(hass, make_entry({"notify_system": [PHONE]}))
    set_sensor(hass, DOOR, "on")
    await hass.async_block_till_done()
    with pytest.raises(ServiceValidationError):
        await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    retry = _actions(push[0])["Try again"]
    set_sensor(hass, DOOR, "off")
    await hass.async_block_till_done()

    await _press(hass, retry, None)  # ohne Benutzer: ignoriert (und verbraucht)
    assert _panel(hass) == AlarmControlPanelState.DISARMED
    await _press(hass, retry, hass_admin_user.id)
    assert _panel(hass) == AlarmControlPanelState.DISARMED
    await _press(hass, PUSH_ARM_RETRY_PREFIX + "erfunden", hass_admin_user.id)
    assert _panel(hass) == AlarmControlPanelState.DISARMED


async def test_arm_failed_can_be_switched_off(hass: HomeAssistant) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    options = {"notify_system": [PHONE], "events": {"arm_failed": {"enabled": False}}}
    await setup_entry(hass, make_entry(options))
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    with pytest.raises(ServiceValidationError):
        await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    assert push == []


# --- Erinnerung "Alle weg, Anlage unscharf" ---------------------------------


def _people(hass: HomeAssistant, a: str, b: str) -> None:
    hass.states.async_set(PERSON_A, a, {"friendly_name": "Anna"})
    hass.states.async_set(PERSON_B, b, {"friendly_name": "Ben"})


def _reminder_options(**extra: Any) -> dict[str, Any]:
    return {
        "notify_system": [PHONE],
        "reminder_persons": [PERSON_A, PERSON_B],
        "reminder_profile": "away",
        "reminder_delay": 10,
        **extra,
    }


async def _wait(hass: HomeAssistant, freezer: FrozenDateTimeFactory, minutes: int) -> None:
    freezer.tick(timedelta(minutes=minutes))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


async def test_reminder_when_everyone_is_away(
    hass: HomeAssistant, hass_admin_user: MockUser, freezer: FrozenDateTimeFactory
) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    _people(hass, "home", "home")
    await setup_entry(hass, make_entry(_reminder_options()))

    _people(hass, "not_home", "not_home")
    await hass.async_block_till_done()
    await _wait(hass, freezer, 5)
    assert push == []
    await _wait(hass, freezer, 6)
    assert len(push) == 1
    assert "disarmed" in push[0].data["title"]
    actions = _actions(push[0])
    assert list(actions) == ["Arm now (Abwesend)"]
    assert actions["Arm now (Abwesend)"].startswith(PUSH_ARM_NOW_PREFIX)
    # nichts selbst geschaltet
    assert _panel(hass) == AlarmControlPanelState.DISARMED

    # nur einmal pro Abwesenheit
    await _wait(hass, freezer, 30)
    assert len(push) == 1

    await _press(hass, actions["Arm now (Abwesend)"], hass_admin_user.id)
    assert _panel(hass) in (AlarmControlPanelState.ARMING, AlarmControlPanelState.ARMED_AWAY)


async def test_no_reminder_if_someone_returns_or_unknown(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    _people(hass, "home", "home")
    await setup_entry(hass, make_entry(_reminder_options()))

    _people(hass, "not_home", "not_home")
    await hass.async_block_till_done()
    await _wait(hass, freezer, 5)
    _people(hass, "home", "not_home")
    await hass.async_block_till_done()
    await _wait(hass, freezer, 20)
    assert push == []

    _people(hass, "not_home", "unknown")  # unbekannt zählt nicht als weg
    await hass.async_block_till_done()
    await _wait(hass, freezer, 20)
    assert push == []


async def test_no_reminder_when_armed(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    _people(hass, "home", "home")
    await setup_entry(hass, make_entry(_reminder_options()))
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    _people(hass, "not_home", "not_home")
    await hass.async_block_till_done()
    await _wait(hass, freezer, 20)
    assert push == []


async def test_reminder_off_without_persons(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    _people(hass, "not_home", "not_home")
    await setup_entry(hass, make_entry({"notify_system": [PHONE]}))
    await _wait(hass, freezer, 60)
    assert push == []


# --- Optionen ---------------------------------------------------------------
