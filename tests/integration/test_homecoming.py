"""Integrationstests: Push-Knopf "Unscharf schalten" und Heimkehr-Beobachtung.

notify-Dienste sind ATTRAPPEN. Personen und Ortungsquellen sind reine Testzustände.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.components.persistent_notification import (
    _async_get_or_create_notifications,
)
from homeassistant.core import Context, HomeAssistant, ServiceCall
from pytest_homeassistant_custom_component.common import MockUser, async_mock_service

from custom_components.hauswacht.const import PUSH_ACTION_EVENT, PUSH_ACTION_PREFIX

from .conftest import DOOR, PANEL, make_entry, set_sensor, setup_entry

PHONE = "mobile_app_testhandy"
PERSON = "person.anna"
ROUTER = "device_tracker.anna_router"
OBSERVER = "sensor.hauswacht_homecoming_observation"
REPORT = "button.hauswacht_homecoming_report"


def _night(**extra: Any) -> dict[str, Any]:
    night = {"entry_delay": 30, "notify": [PHONE]}
    return {"profiles": {"night": night}, **extra}


async def _service(hass: HomeAssistant, domain: str, service: str, **data: Any) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)
    await hass.async_block_till_done()


def _panel(hass: HomeAssistant) -> str:
    state = hass.states.get(PANEL)
    assert state is not None
    return state.state


def _action(call: ServiceCall) -> str:
    actions = call.data["data"]["actions"]
    assert actions[0]["title"] == "Unscharf schalten"
    assert actions[0]["authenticationRequired"] is True
    return str(actions[0]["action"])


async def _press(hass: HomeAssistant, action: str, user_id: str | None) -> None:
    hass.bus.async_fire(PUSH_ACTION_EVENT, {"action": action}, context=Context(user_id=user_id))
    await hass.async_block_till_done()


async def _arm_and_open(hass: HomeAssistant) -> None:
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    set_sensor(hass, DOOR, "on")
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.PENDING


# --- Push-Knopf -------------------------------------------------------------


async def test_push_button_disarms_from_notification(
    hass: HomeAssistant, hass_admin_user: MockUser
) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    await setup_entry(hass, make_entry(_night(push_disarm=True)))
    await _arm_and_open(hass)

    assert len(push) == 1
    assert "Tür geöffnet" in push[0].data["title"]
    action = _action(push[0])
    assert action.startswith(PUSH_ACTION_PREFIX)

    await _press(hass, action, hass_admin_user.id)
    assert _panel(hass) == AlarmControlPanelState.DISARMED
    messages = [c.data["message"] for c in push[1:]]
    assert "clear_notification" in messages
    assert any("Push-Knopf" in m for m in messages)


async def test_push_button_also_on_alarm(hass: HomeAssistant, hass_admin_user: MockUser) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    await setup_entry(hass, make_entry(_night(push_disarm=True)))
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    set_sensor(hass, "binary_sensor.kuechenfenster", "on")
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.TRIGGERED
    await _press(hass, _action(push[0]), hass_admin_user.id)
    assert _panel(hass) == AlarmControlPanelState.DISARMED


async def test_stale_button_from_earlier_arming_is_ignored(
    hass: HomeAssistant, hass_admin_user: MockUser
) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    await setup_entry(hass, make_entry(_night(push_disarm=True)))
    await _arm_and_open(hass)
    old_action = _action(push[0])
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL)
    set_sensor(hass, DOOR, "off")
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)

    await _press(hass, old_action, hass_admin_user.id)
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_button_without_user_is_ignored(hass: HomeAssistant) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    await setup_entry(hass, make_entry(_night(push_disarm=True)))
    await _arm_and_open(hass)
    await _press(hass, _action(push[0]), None)
    assert _panel(hass) == AlarmControlPanelState.PENDING


async def test_push_disarm_off_by_default(hass: HomeAssistant) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    await setup_entry(hass, make_entry(_night()))
    await _arm_and_open(hass)
    assert push == []  # kein Push bei Türöffnung
    set_sensor(hass, "binary_sensor.kuechenfenster", "on")
    await hass.async_block_till_done()
    assert "actions" not in push[0].data["data"]  # Alarm-Push ohne Knopf


# --- Heimkehr-Beobachtung ----------------------------------------------------


def _person(hass: HomeAssistant, state: str, tracker: str) -> None:
    hass.states.async_set(PERSON, state, {"friendly_name": "Anna", "device_trackers": [ROUTER]})
    hass.states.async_set(ROUTER, tracker, {"friendly_name": "Router"})


async def test_observation_records_and_switches_nothing(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    _person(hass, "not_home", "not_home")
    options = _night(homecoming_observe=True, homecoming_persons=[PERSON], push_disarm=True)
    await setup_entry(hass, make_entry(options))

    freezer.tick(timedelta(minutes=20))
    set_sensor(hass, DOOR, "on")
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=10))
    hass.states.async_set(ROUTER, "home", {"friendly_name": "Router"})
    freezer.tick(timedelta(seconds=30))
    _person(hass, "home", "home")
    await hass.async_block_till_done()

    # nichts geschaltet, nichts verschickt
    assert _panel(hass) == AlarmControlPanelState.DISARMED
    assert push == []

    state = hass.states.get(OBSERVER)
    assert state is not None
    assert state.state == "1"
    sources = state.attributes["sources"]
    assert sources["Anna (gesamt)"]["with_door"] == 1
    assert sources["Anna (gesamt)"]["median_delay"] == 40
    assert sources["Anna – Router"]["median_delay"] == 10
    assert sources["Anna (gesamt)"]["false_alarms_at"]["30"] == 1
    assert "40 s nach dem Öffnen" in state.attributes["recent"][0]


async def test_arrival_without_door_is_counted(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    _person(hass, "not_home", "not_home")
    options = {"homecoming_observe": True, "homecoming_persons": [PERSON]}
    await setup_entry(hass, make_entry(options))
    freezer.tick(timedelta(minutes=20))
    _person(hass, "home", "home")
    await hass.async_block_till_done()
    state = hass.states.get(OBSERVER)
    assert state is not None
    assert state.attributes["sources"]["Anna (gesamt)"]["without_door"] == 1


async def test_report_button_creates_notification(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    _person(hass, "not_home", "not_home")
    options = {"homecoming_observe": True, "homecoming_persons": [PERSON]}
    await setup_entry(hass, make_entry(options))
    freezer.tick(timedelta(minutes=20))
    set_sensor(hass, DOOR, "on")
    freezer.tick(timedelta(seconds=20))
    _person(hass, "home", "home")
    await hass.async_block_till_done()
    await _service(hass, "button", "press", entity_id=REPORT)
    notifications = _async_get_or_create_notifications(hass)
    report = notifications["hauswacht_homecoming_report"]
    assert "| Anna (gesamt) | 1 | 1 | 0 | 20 s |" in report["message"]


async def test_observation_off_by_default(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    state = hass.states.get(OBSERVER)
    assert state is not None
    assert state.state == "unknown"


async def test_homecoming_options(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "homecoming"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"homecoming_observe": True, "homecoming_persons": [PERSON]}
    )
    await hass.async_block_till_done()
    assert entry.options["homecoming_observe"] is True
    assert entry.options["homecoming_persons"] == [PERSON]
