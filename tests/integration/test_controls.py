"""Integrationstests: Bedienteile – Zigbee2MQTT-Keypads, NFC-Aufkleber, RFID-Leser.

MQTT ist gemockt (mqtt_mock), Keypads und Leser sind nur Nachrichten bzw. Ereignisse.
Es gibt keine echten Geräte und keine Sirenen.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from homeassistant.auth.const import GROUP_ID_USER
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import Context, HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from pytest_homeassistant_custom_component.common import (
    MockUser,
    async_capture_events,
    async_fire_mqtt_message,
    async_mock_service,
)
from pytest_homeassistant_custom_component.typing import MqttMockHAClient

from custom_components.hauswacht.const import DOMAIN, EVENT_HAUSWACHT
from custom_components.hauswacht.core.pin import hash_pin

from .conftest import PANEL, WINDOW, make_entry, set_sensor, setup_entry

TOPIC = "zigbee2mqtt/Keypad Flur"
PHONE = "mobile_app_testhandy"
PIN = "1357"
CARD = "04A1B2C3"
STICKER = "AA-BB-CC"

# Der MQTT-Mock startet einen periodischen Timer, der nach dem Test noch läuft.
pytestmark = pytest.mark.parametrize("expected_lingering_timers", [True])


def _users(ha_user: str | None = None) -> dict[str, Any]:
    hashed = hash_pin(PIN)
    return {
        "anna": {
            "name": "Anna",
            "pin_salt": hashed.salt,
            "pin_digest": hashed.digest,
            "tags": [CARD],
            "ha_user": ha_user,
        }
    }


def _controls(**keypad: Any) -> dict[str, Any]:
    return {
        "flur": {
            "name": "Keypad Flur",
            "kind": "keypad",
            "topic": TOPIC,
            "buttons": {"arm_night_zones": "night"},
            **keypad,
        },
        "tuer": {
            "name": "Aufkleber Tür",
            "kind": "sticker",
            "tag": STICKER,
            "action": "toggle",
            "profile": "night",
        },
        "leser": {"name": "Leser", "kind": "reader", "device": "reader1", "action": "disarm"},
    }


async def _setup(hass: HomeAssistant, ha_user: str | None = None, **keypad: Any) -> None:
    options = {"users": _users(ha_user), "controls": _controls(**keypad), "notify_system": [PHONE]}
    await setup_entry(hass, make_entry(options))


def _panel(hass: HomeAssistant) -> str:
    state = hass.states.get(PANEL)
    assert state is not None
    return state.state


async def _press(hass: HomeAssistant, action: str, code: str | None, transaction: int) -> None:
    payload: dict[str, Any] = {"action": action, "action_transaction": transaction}
    if code is not None:
        payload["action_code"] = code
    async_fire_mqtt_message(hass, TOPIC, json.dumps(payload))
    await hass.async_block_till_done()
    await hass.async_block_till_done()


def _sent(mqtt_mock: MqttMockHAClient) -> list[dict[str, Any]]:
    return [
        json.loads(call.args[1])["arm_mode"]
        for call in mqtt_mock.async_publish.call_args_list
        if call.args[0] == f"{TOPIC}/set"
    ]


async def _arm(hass: HomeAssistant) -> None:
    await hass.services.async_call(
        "alarm_control_panel", "alarm_arm_night", {"entity_id": PANEL, "code": PIN}, blocking=True
    )
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_keypad_disarm_with_pin_and_state_display(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    await _setup(hass)
    await _arm(hass)
    assert {"mode": "arm_night_zones"} in _sent(mqtt_mock)  # Zustand angezeigt
    await _press(hass, "disarm", PIN, 7)
    assert _panel(hass) == AlarmControlPanelState.DISARMED
    assert {"mode": "disarm", "transaction": 7} in _sent(mqtt_mock)
    state = hass.states.get(PANEL)
    assert state is not None
    assert state.attributes["changed_by"] == "Anna (Keypad Flur)"


async def test_keypad_wrong_pin_is_rejected(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    await _setup(hass)
    await _arm(hass)
    await _press(hass, "disarm", "0000", 8)
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    assert {"mode": "invalid_code", "transaction": 8} in _sent(mqtt_mock)


async def test_keypad_card_and_arm_key(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> None:
    await _setup(hass)
    await _press(hass, "arm_night_zones", CARD, 1)
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    assert {"mode": "arm_night_zones", "transaction": 1} in _sent(mqtt_mock)
    # Taste ohne zugeordnetes Profil
    await _press(hass, "arm_all_zones", CARD, 2)
    assert {"mode": "not_ready", "transaction": 2} in _sent(mqtt_mock)


async def test_keypad_not_ready_when_window_open(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    await _setup(hass)
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    await _press(hass, "arm_night_zones", PIN, 3)
    assert _panel(hass) == AlarmControlPanelState.DISARMED
    assert {"mode": "not_ready", "transaction": 3} in _sent(mqtt_mock)


async def test_card_and_pin(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> None:
    await _setup(hass, login="card_and_pin")
    await _arm(hass)
    await _press(hass, "disarm", PIN, 4)
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT  # erst ein Ausweis
    assert {"mode": "not_ready", "transaction": 4} in _sent(mqtt_mock)
    await _press(hass, "disarm", CARD, 5)
    assert _panel(hass) == AlarmControlPanelState.DISARMED


async def test_emergency_silent_and_alarm(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    await _setup(hass, emergency="silent")
    await _press(hass, "emergency", None, 9)
    assert any("EMERGENCY" in c.data["title"] for c in push)
    assert _panel(hass) == AlarmControlPanelState.DISARMED


async def test_emergency_alarm(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> None:
    await _setup(hass, emergency="alarm")
    await _press(hass, "emergency", None, 10)
    assert _panel(hass) == AlarmControlPanelState.TRIGGERED


async def test_sticker_needs_known_phone(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient, hass_admin_user: MockUser
) -> None:
    await _setup(hass, ha_user=hass_admin_user.id)
    # Fremdes Handy (kein Hauswacht-Benutzer): nichts passiert
    hass.bus.async_fire("tag_scanned", {"tag_id": STICKER, "device_id": "x"}, context=Context())
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.DISARMED
    # Handy von Anna: umschalten -> scharf (Nacht)
    hass.bus.async_fire(
        "tag_scanned",
        {"tag_id": "aa:bb:cc", "device_id": "x"},
        context=Context(user_id=hass_admin_user.id),
    )
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    hass.bus.async_fire(
        "tag_scanned",
        {"tag_id": STICKER, "device_id": "x"},
        context=Context(user_id=hass_admin_user.id),
    )
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.DISARMED


async def test_reader_card(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> None:
    await _setup(hass)
    await _arm(hass)
    hass.bus.async_fire("tag_scanned", {"tag_id": "ffff", "device_id": "reader1"})
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    hass.bus.async_fire("tag_scanned", {"tag_id": CARD, "device_id": "reader1"})
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.DISARMED


async def test_options_add_keypad(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    for step in ("system", "controls", "control_add_keypad"):
        flow = await hass.config_entries.options.async_configure(
            flow["flow_id"], {"next_step_id": step}
        )
    assert flow["step_id"] == "control_keypad"
    base = {"name": "Keypad Flur", "area": "__all__", "login": "pin_or_card", "emergency": "off"}
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {**base, "topic": " "}
    )
    assert flow["errors"] == {"topic": "control_topic"}
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {**base, "topic": TOPIC + "/", "arm_night_zones": "night"}
    )
    assert flow["type"] == "menu"
    stored = entry.options["controls"]["keypad_flur"]
    assert stored["topic"] == TOPIC
    assert stored["buttons"] == {"arm_night_zones": "night"}


async def _setup_without_pin(hass: HomeAssistant) -> Any:
    options = {
        "users": {"niklas": {"name": "Niklas", "tags": [CARD, "0011223344"]}},
        "controls": _controls(),
    }
    entry = make_entry(options)
    await setup_entry(hass, entry)
    return entry


async def test_card_works_without_any_pin(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> None:
    await _setup_without_pin(hass)
    state = hass.states.get(PANEL)
    assert state is not None
    assert state.attributes["code_format"] is None  # Dashboard bleibt ohne PIN
    await hass.services.async_call(
        "alarm_control_panel", "alarm_arm_night", {"entity_id": PANEL}, blocking=True
    )
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    await _press(hass, "disarm", None, 1)  # ohne Karte: abgelehnt
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    assert {"mode": "invalid_code", "transaction": 1} in _sent(mqtt_mock)
    await _press(hass, "disarm", "00-11-22-33-44", 2)  # zweite Karte von Niklas
    assert _panel(hass) == AlarmControlPanelState.DISARMED
    state = hass.states.get(PANEL)
    assert state is not None
    assert state.attributes["changed_by"] == "Niklas (Keypad Flur)"


async def test_unknown_card_offered_in_user_form(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    entry = await _setup_without_pin(hass)
    await _press(hass, "disarm", "a1b2c3d4e5", 1)  # neue Karte
    await _press(hass, "disarm", "1234", 2)  # falscher PIN: wird nie angezeigt
    assert list(entry.runtime_data.controls.unknown_cards) == ["A1B2C3D4E5"]
    state = hass.states.get(PANEL)
    assert state is not None
    assert state.attributes["code_failures"] == 1  # nur der PIN zählt, die Karte nicht
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    for step in ("system", "users", "user_edit"):
        flow = await hass.config_entries.options.async_configure(
            flow["flow_id"], {"next_step_id": step}
        )
    flow = await hass.config_entries.options.async_configure(flow["flow_id"], {"user": "niklas"})
    key = next(k for k in flow["data_schema"].schema if str(k) == "tags")
    offered = [o["value"] for o in flow["data_schema"].schema[key].config["options"]]
    assert offered == [CARD, "0011223344", "A1B2C3D4E5"]
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"name": "Niklas", "tags": [CARD, "0011223344", "A1B2C3D4E5"]}
    )
    assert flow["type"] == "menu"
    assert entry.options["users"]["niklas"]["tags"] == [CARD, "0011223344", "A1B2C3D4E5"]
    assert "pin_digest" not in entry.options["users"]["niklas"]


async def test_reset_failed_attempts_admin_only(
    hass: HomeAssistant,
    mqtt_mock: MqttMockHAClient,
    hass_admin_user: MockUser,
) -> None:
    await _setup(hass)
    await hass.auth.async_create_user("Besitzer")  # der erste Benutzer ist Eigentümer
    guest = await hass.auth.async_create_user("Gast", group_ids=[GROUP_ID_USER])
    assert not guest.is_admin
    for transaction in (20, 21, 22):
        await _press(hass, "disarm", "0000", transaction)
    state = hass.states.get(PANEL)
    assert state is not None
    assert state.attributes["code_failures"] == 3
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            "reset_code_lock",
            {"entity_id": PANEL},
            blocking=True,
            context=Context(user_id=guest.id),
        )
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    await hass.services.async_call(
        DOMAIN,
        "reset_code_lock",
        {"entity_id": PANEL},
        blocking=True,
        context=Context(user_id=hass_admin_user.id),
    )
    await hass.async_block_till_done()
    state = hass.states.get(PANEL)
    assert state is not None
    assert state.attributes["code_failures"] == 0
    assert state.attributes["code_locked_until"] is None
    assert [e.data["type"] for e in events] == ["CodeLockReset"]
    assert events[0].data["failures"] == 3


async def _user_form(hass: HomeAssistant, entry: Any, user: str) -> Any:
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    for step in ("system", "users", "user_edit"):
        flow = await hass.config_entries.options.async_configure(
            flow["flow_id"], {"next_step_id": step}
        )
    return await hass.config_entries.options.async_configure(flow["flow_id"], {"user": user})


def _offered(flow: Any) -> list[str]:
    key = next(k for k in flow["data_schema"].schema if str(k) == "tags")
    return [o["value"] for o in flow["data_schema"].schema[key].config["options"]]


async def test_learning_only_while_disarmed(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    entry = await _setup_without_pin(hass)
    await hass.services.async_call(
        "alarm_control_panel", "alarm_arm_night", {"entity_id": PANEL}, blocking=True
    )
    await hass.async_block_till_done()
    await _press(hass, "disarm", "a1b2c3d4e5", 1)
    assert entry.runtime_data.controls.unknown_cards == {}


async def test_learned_card_expires(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> None:
    entry = await _setup_without_pin(hass)
    await _press(hass, "disarm", "a1b2c3d4e5", 1)
    flow = await _user_form(hass, entry, "niklas")
    assert "A1B2C3D4E5" in _offered(flow)
    # Formular zu lange offen: Karte ist inzwischen abgelaufen
    controls = entry.runtime_data.controls
    source, when = controls.unknown_cards["A1B2C3D4E5"]
    controls.unknown_cards["A1B2C3D4E5"] = (source, when - 6 * 60)
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"name": "Niklas", "tags": [CARD, "0011223344", "A1B2C3D4E5"]}
    )
    assert flow["errors"] == {"tags": "card_expired"}
    assert "A1B2C3D4E5" not in _offered(flow)
    assert "A1B2C3D4E5" not in entry.options["users"]["niklas"]["tags"]


async def test_learning_time_setting(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> None:
    entry = await _setup_without_pin(hass)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    for step in ("system", "controls", "control_learn"):
        flow = await hass.config_entries.options.async_configure(
            flow["flow_id"], {"next_step_id": step}
        )
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"card_learn_minutes": 0}
    )
    assert flow["step_id"] == "controls"
    assert entry.options["card_learn_minutes"] == 0
    await hass.async_block_till_done()
    await _press(hass, "disarm", "a1b2c3d4e5", 1)
    assert (
        hass.config_entries.async_get_entry(entry.entry_id).runtime_data.controls.unknown_cards
        == {}
    )


async def test_random_uid_not_learnable(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> None:
    entry = await _setup_without_pin(hass)
    await _press(hass, "disarm", "+08837CF0", 1)  # Handy: Zufallsnummer
    assert entry.runtime_data.controls.unknown_cards == {}
    flow = await _user_form(hass, entry, "niklas")
    assert "08837CF0" not in _offered(flow)
    assert "Zufallsnummer" in flow["description_placeholders"]["random"] or (
        "random ID" in flow["description_placeholders"]["random"]
    )
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"name": "Niklas", "tags": [CARD, "08ECA2B8"]}
    )
    assert flow["errors"] == {"tags": "tag_random"}
