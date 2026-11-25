"""Integrationstests: Taster (nur scharf) und Türschloss (unscharf beim Aufschließen).

MQTT ist gemockt; Taster, Schloss und "Wer"-Sensor sind nur Zustände bzw. Nachrichten.
Hauswacht schaltet das Schloss nie – es liest nur mit. Keine echten Geräte, keine Sirenen.
"""

from __future__ import annotations

from typing import Any

import pytest
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import (
    async_capture_events,
    async_fire_mqtt_message,
    async_mock_service,
)
from pytest_homeassistant_custom_component.typing import MqttMockHAClient

from custom_components.hauswacht.const import EVENT_HAUSWACHT
from custom_components.hauswacht.core.pin import hash_pin

from .conftest import PANEL, WINDOW, make_entry, set_sensor, setup_entry

BUTTON = "event.taster_flur"
ACTION_SENSOR = "sensor.taster_keller_action"
LOCK = "lock.haustuer"
WHO = "sensor.haustuer_benutzer"
NUKI = "nuki/3A1B2C4D"
PHONE = "mobile_app_testhandy"

pytestmark = pytest.mark.parametrize("expected_lingering_timers", [True])


def _panel(hass: HomeAssistant) -> str:
    state = hass.states.get(PANEL)
    assert state is not None
    return state.state


def _controls() -> dict[str, Any]:
    return {
        "taster": {
            "name": "Taster Flur",
            "kind": "button",
            "entity": BUTTON,
            "presses": {"single": "away", "double": "night"},
        },
        "keller": {
            "name": "Taster Keller",
            "kind": "button",
            "entity": ACTION_SENSOR,
            "presses": {"hold": "night"},
        },
        "schloss": {
            "name": "Haustür-Schloss",
            "kind": "lock",
            "entity": LOCK,
            "source": "nuki_mqtt",
            "topic": NUKI,
            "profile": "night",
        },
        "schloss2": {
            "name": "Kellertür-Schloss",
            "kind": "lock",
            "entity": "lock.kellertuer",
            "source": "generic",
            "who": WHO,
        },
    }


async def _setup(hass: HomeAssistant, pin: str | None = None, **extra: Any) -> Any:
    hass.states.async_set(BUTTON, "unknown", {"event_types": ["single", "double", "long"]})
    hass.states.async_set(ACTION_SENSOR, "")
    hass.states.async_set(LOCK, "locked")
    hass.states.async_set("lock.kellertuer", "locked")
    hass.states.async_set(WHO, "")
    users = {
        "anna": {"name": "Anna", "tags": ["NUKIAUTH52653", "LOCKANNA"]},
        "gast": {"name": "Gast", "tags": ["NUKICODE8192"], "can_disarm": False},
    }
    if pin is not None:
        hashed = hash_pin(pin)
        users["anna"].update({"pin_salt": hashed.salt, "pin_digest": hashed.digest})
    entry = make_entry({"users": users, "controls": _controls(), "notify_system": [PHONE], **extra})
    await setup_entry(hass, entry)
    return entry


async def _press(hass: HomeAssistant, at: str, event_type: str) -> None:
    hass.states.async_set(BUTTON, at, {"event_type": event_type, "event_types": ["single"]})
    await hass.async_block_till_done()


async def _nuki(hass: HomeAssistant, payload: str) -> None:
    async_fire_mqtt_message(hass, f"{NUKI}/lockActionEvent", payload)
    await hass.async_block_till_done()


async def _lock(hass: HomeAssistant, state: str, entity_id: str = LOCK) -> None:
    hass.states.async_set(entity_id, state)
    await hass.async_block_till_done()


async def _arm_away(hass: HomeAssistant) -> None:
    await hass.services.async_call(
        "alarm_control_panel", "alarm_arm_away", {"entity_id": PANEL}, blocking=True
    )
    await hass.async_block_till_done()
    assert _panel(hass) in (AlarmControlPanelState.ARMING, AlarmControlPanelState.ARMED_AWAY)


# --- Taster ---------------------------------------------------------------------


async def test_button_press_arms_profile(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> None:
    await _setup(hass)
    await _press(hass, "2026-11-15T12:00:00.000+00:00", "double")
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    state = hass.states.get(PANEL)
    assert state is not None
    assert state.attributes["changed_by"] == "Taster Flur"


async def test_button_never_disarms(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> None:
    await _setup(hass)
    await _press(hass, "2026-11-15T12:00:00.000+00:00", "double")
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    # Noch einmal drücken (auch eine andere Druckart) schaltet weder um noch unscharf
    await _press(hass, "2026-11-15T12:00:05.000+00:00", "single")
    await _press(hass, "2026-11-15T12:00:09.000+00:00", "double")
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_button_unassigned_press_does_nothing(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    await _setup(hass)
    await _press(hass, "2026-11-15T12:00:00.000+00:00", "long")
    assert _panel(hass) == AlarmControlPanelState.DISARMED


async def test_button_reconnect_is_no_press(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    """Gerät wieder verbunden: Zustand wird wiederhergestellt – das ist kein Drücken."""
    await _setup(hass)
    hass.states.async_set(BUTTON, "unavailable")
    await hass.async_block_till_done()
    await _press(hass, "2026-11-15T12:00:00.000+00:00", "double")
    assert _panel(hass) == AlarmControlPanelState.DISARMED


async def test_action_sensor_button(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> None:
    await _setup(hass)
    hass.states.async_set(ACTION_SENSOR, "hold")
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_button_refuses_when_pin_required(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    notify = async_mock_service(hass, "notify", PHONE)
    await _setup(hass, pin="1357", code_arm_required=True)
    await _press(hass, "2026-11-15T12:00:00.000+00:00", "double")
    assert _panel(hass) == AlarmControlPanelState.DISARMED
    assert any("PIN" in str(call.data.get("message")) for call in notify)


async def test_button_refused_arm_sends_one_message(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    """Offenes Fenster: nur "Scharfschalten nicht möglich" (mit Knopf), kein zweites
    "Bedienteil abgelehnt"."""
    notify = async_mock_service(hass, "notify", PHONE)
    await _setup(hass)
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    await _press(hass, "2026-11-15T12:00:00.000+00:00", "double")
    assert _panel(hass) == AlarmControlPanelState.DISARMED
    messages = [c for c in notify if c.data["message"] != "clear_notification"]
    assert len(messages) == 1
    assert "not armed" in messages[0].data["title"]


# --- Türschloss: Nuki über MQTT ----------------------------------------------------


async def test_nuki_unlock_by_known_user_disarms(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    await _setup(hass)
    await _arm_away(hass)
    await _nuki(hass, "1,0,52653,0,0")  # aufschließen per App, Auth-ID 52653
    assert _panel(hass) != AlarmControlPanelState.DISARMED  # Schloss hat sich noch nicht bewegt
    await _lock(hass, "unlocked")
    assert _panel(hass) == AlarmControlPanelState.DISARMED
    state = hass.states.get(PANEL)
    assert state is not None
    assert state.attributes["changed_by"] == "Anna (Haustür-Schloss)"


async def test_disabled_lock_id_does_not_disarm(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    entry = await _setup(hass)
    users = dict(entry.options["users"])
    users["anna"] = {
        **users["anna"],
        "tags": ["LOCKANNA"],
        "tags_disabled": ["NUKIAUTH52653"],
        "tag_names": {"NUKIAUTH52653": "Nuki-App"},
    }
    hass.config_entries.async_update_entry(entry, options={**entry.options, "users": users})
    await hass.async_block_till_done()
    await _arm_away(hass)
    await _nuki(hass, "1,0,52653,0,0")
    await _lock(hass, "unlocked")
    assert _panel(hass) != AlarmControlPanelState.DISARMED
    assert any("Nuki-App" in c.data["message"] for c in push)
    assert "NUKIAUTH52653" not in entry.runtime_data.controls.unknown_cards


async def test_nuki_state_first_then_event(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    await _setup(hass)
    await _arm_away(hass)
    await _lock(hass, "unlocked")
    await _nuki(hass, "1,0,52653,0,0")
    assert _panel(hass) == AlarmControlPanelState.DISARMED


async def test_nuki_event_without_lock_moving_does_nothing(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    """Manche Nuki melden auch einen falschen Keypad-Code – ohne Bewegung zählt das nicht."""
    await _setup(hass)
    await _arm_away(hass)
    await _nuki(hass, "1,0,52653,0,1")
    assert _panel(hass) != AlarmControlPanelState.DISARMED


@pytest.mark.parametrize(
    "payload",
    [
        "1,2,0,0,1",  # Knopf am Schloss (innen)
        "1,172,52653,0,0",  # über MQTT (z. B. aus Home Assistant)
        "1,3,0,0,0",  # Zeitsteuerung
        "1,0,0,0,0",  # keine Kennung
        "1,0,77777,0,0",  # unbekannte Kennung
    ],
)
async def test_nuki_never_disarms_without_known_person(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient, payload: str
) -> None:
    await _setup(hass)
    await _arm_away(hass)
    await _nuki(hass, payload)
    await _lock(hass, "unlocked")
    assert _panel(hass) != AlarmControlPanelState.DISARMED


async def test_nuki_keypad_code_without_disarm_right(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    notify = async_mock_service(hass, "notify", PHONE)
    await _setup(hass)
    await _arm_away(hass)
    await _nuki(hass, "1,0,1234,8192,1")  # Keypad-Code des Gasts (darf nicht unscharf)
    await _lock(hass, "unlocked")
    assert _panel(hass) != AlarmControlPanelState.DISARMED
    assert notify  # Systemmeldung "nicht möglich"


async def test_door_opening_alone_does_nothing(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    await _setup(hass)
    await _arm_away(hass)
    await _lock(hass, "unlocked")
    assert _panel(hass) != AlarmControlPanelState.DISARMED


async def test_unknown_lock_id_is_offered_for_learning(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    entry = await _setup(hass)
    await _nuki(hass, "1,0,4711,0,0")
    await _lock(hass, "unlocked")
    assert "NUKIAUTH4711" in entry.runtime_data.controls.unknown_cards


async def test_lock_from_outside_arms_profile(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    await _setup(hass)
    await _lock(hass, "unlocked")
    await _nuki(hass, "2,0,52653,0,0")  # abschließen per App
    await _lock(hass, "locked")
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_auto_lock_does_not_arm(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> None:
    await _setup(hass)
    await _lock(hass, "unlocked")
    await _nuki(hass, "2,6,0,0,0")  # automatisch abgeschlossen
    await _lock(hass, "locked")
    assert _panel(hass) == AlarmControlPanelState.DISARMED


# --- Türschloss: allgemeine Quelle -------------------------------------------------


async def test_generic_who_sensor_disarms(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> None:
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    await _setup(hass)
    await _arm_away(hass)
    hass.states.async_set(WHO, "Anna")
    await hass.async_block_till_done()
    await _lock(hass, "unlocked", "lock.kellertuer")
    assert _panel(hass) == AlarmControlPanelState.DISARMED
    assert any(e.data["type"] == "LockIdentified" for e in events)


# --- Einrichtung ------------------------------------------------------------------


async def test_nuki_passage_keeps_armed(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> None:
    """Schloss auf "Durchgang": erlaubt das scharfe Profil ihn, bleibt es scharf (ADR 0013)."""
    hass.states.async_set(LOCK, "locked")
    entry = await _setup(
        hass,
        profiles={"night": {"passage": {"enabled": True}}},
    )
    options = dict(entry.options)
    controls = {k: dict(v) for k, v in options["controls"].items()}
    controls["schloss"]["action"] = "passage"
    hass.config_entries.async_update_entry(entry, options={**options, "controls": controls})
    await hass.async_block_till_done()
    await hass.services.async_call(
        "alarm_control_panel", "alarm_arm_night", {"entity_id": PANEL}, blocking=True
    )
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    await _nuki(hass, "1,0,52653,0,0")
    await _lock(hass, "unlocked")
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    state = hass.states.get(PANEL)
    assert state is not None
    assert state.attributes["passage"]["direction"] == "out"


async def test_nuki_passage_without_profile_passage_disarms(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    entry = await _setup(hass)
    options = dict(entry.options)
    controls = {k: dict(v) for k, v in options["controls"].items()}
    controls["schloss"]["action"] = "passage"
    hass.config_entries.async_update_entry(entry, options={**options, "controls": controls})
    await hass.async_block_till_done()
    await _arm_away(hass)
    await _nuki(hass, "1,0,52653,0,0")
    await _lock(hass, "unlocked")
    assert _panel(hass) == AlarmControlPanelState.DISARMED  # wie bisher
