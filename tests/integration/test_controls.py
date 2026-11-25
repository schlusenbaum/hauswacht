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


async def test_disabled_card_reports_and_counts(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    niklas = {
        "name": "Niklas",
        "tags": [CARD],
        "tags_disabled": ["0011223344"],
        "tag_names": {"0011223344": "Geldbörse"},
    }
    options = {"users": {"niklas": niklas}, "controls": _controls(), "notify_system": [PHONE]}
    push = async_mock_service(hass, "notify", PHONE)
    entry = make_entry(options)
    await setup_entry(hass, entry)
    await hass.services.async_call(
        "alarm_control_panel", "alarm_arm_night", {"entity_id": PANEL}, blocking=True
    )
    await hass.async_block_till_done()
    await _press(hass, "disarm", "0011223344", 1)
    assert _panel(hass) != AlarmControlPanelState.DISARMED
    state = hass.states.get(PANEL)
    assert state is not None
    assert state.attributes["code_failures"] == 1
    assert any("Geldbörse" in c.data["message"] and "Niklas" in c.data["message"] for c in push)
    # deaktivierte Karte wird nicht zum Anlernen angeboten
    assert entry.runtime_data.controls.unknown_cards == {}


async def test_card_name_in_logbook_actor(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> None:
    niklas = {"name": "Niklas", "tags": [CARD, "0011223344"], "tag_names": {CARD: "Schlüsselbund"}}
    await setup_entry(hass, make_entry({"users": {"niklas": niklas}, "controls": _controls()}))
    await hass.services.async_call(
        "alarm_control_panel", "alarm_arm_night", {"entity_id": PANEL}, blocking=True
    )
    await hass.async_block_till_done()
    await _press(hass, "disarm", CARD.lower(), 5)
    assert _panel(hass) == AlarmControlPanelState.DISARMED
    state = hass.states.get(PANEL)
    assert state is not None
    assert state.attributes["changed_by"] == "Niklas · Schlüsselbund (Keypad Flur)"
    # Karte ohne Namen: wie bisher nur der Benutzer
    await hass.services.async_call(
        "alarm_control_panel", "alarm_arm_night", {"entity_id": PANEL}, blocking=True
    )
    await hass.async_block_till_done()
    await _press(hass, "disarm", "0011223344", 6)
    state = hass.states.get(PANEL)
    assert state is not None
    assert state.attributes["changed_by"] == "Niklas (Keypad Flur)"


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


def _offered(flow: Any) -> list[str]:
    key = next(k for k in flow["data_schema"].schema if str(k) == "card")
    return [o["value"] for o in flow["data_schema"].schema[key].config["options"]]


def _card_labels(flow: Any) -> dict[str, str]:
    key = next(k for k in flow["data_schema"].schema if str(k) == "card")
    return {o["value"]: o["label"] for o in flow["data_schema"].schema[key].config["options"]}


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


async def test_learning_time_setting(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> None:
    """Anlernzeit 0: unbekannte Karten werden gar nicht erst gemerkt."""
    options = {
        "users": {"niklas": {"name": "Niklas", "tags": [CARD, "0011223344"]}},
        "controls": _controls(),
        "card_learn_minutes": 0,
    }
    entry = make_entry(options)
    await setup_entry(hass, entry)
    await _press(hass, "disarm", "a1b2c3d4e5", 1)
    assert entry.runtime_data.controls.unknown_cards == {}


async def test_random_uid_not_learnable(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> None:
    entry = await _setup_without_pin(hass)
    await _press(hass, "disarm", "+08837CF0", 1)  # Handy: Zufallsnummer
    assert entry.runtime_data.controls.unknown_cards == {}


def _z2m_entity(hass: HomeAssistant, device_name: str, key: str) -> str:
    """Wie Zigbee2MQTT per MQTT-Discovery: Gerät mit Entität sensor.<gerät>_<key>."""
    from homeassistant.helpers import device_registry as dr  # noqa: PLC0415
    from homeassistant.helpers import entity_registry as er  # noqa: PLC0415

    mqtt_entry = next(iter(hass.config_entries.async_entries("mqtt")))
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=mqtt_entry.entry_id,
        identifiers={("mqtt", f"zigbee2mqtt_0x00aa_{device_name}")},
        name=device_name,
    )
    entry = er.async_get(hass).async_get_or_create(
        "sensor",
        "mqtt",
        f"0x00aa_{device_name}_{key}_zigbee2mqtt",
        config_entry=mqtt_entry,
        device_id=device.id,
        suggested_object_id=f"{device_name}_{key}",
    )
    return entry.entity_id


async def test_keypad_code_entity_offered_as_repair_not_changed(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    """Die Code-Entität gehört der MQTT-Integration: Hauswacht ändert sie nicht selbst, sondern
    bietet das Abschalten als Reparatur an – erst nach Bestätigung wird sie deaktiviert."""
    from homeassistant.components.repairs import repairs_flow_manager  # noqa: PLC0415
    from homeassistant.helpers import entity_registry as er  # noqa: PLC0415
    from homeassistant.helpers import issue_registry as ir  # noqa: PLC0415

    from custom_components.hauswacht.const import DOMAIN, ISSUE_CODE_ENTITIES  # noqa: PLC0415

    code = _z2m_entity(hass, "Keypad Flur", "action_code")
    zone = _z2m_entity(hass, "Keypad Flur", "action_zone")
    other = _z2m_entity(hass, "Anderes Keypad", "action_code")  # nicht in Hauswacht
    await _setup(hass)
    registry = er.async_get(hass)
    assert registry.async_get(code).disabled_by is None  # nichts eigenmächtig geändert
    issue = ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_CODE_ENTITIES)
    assert issue is not None
    assert issue.is_fixable
    assert issue.data == {"entities": code}
    assert other not in str(issue.translation_placeholders)

    # Bestätigen: jetzt wird nur die Code-Entität deaktiviert
    manager = repairs_flow_manager(hass)
    assert manager is not None
    flow = await manager.async_init(DOMAIN, data={"issue_id": ISSUE_CODE_ENTITIES})
    assert flow["step_id"] == "confirm"
    flow = await manager.async_configure(flow["flow_id"], {})
    await hass.async_block_till_done()
    assert registry.async_get(code).disabled_by is er.RegistryEntryDisabler.USER
    assert registry.async_get(zone).disabled_by is None
    assert registry.async_get(other).disabled_by is None
    assert ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_CODE_ENTITIES) is None

    # bewusst wieder eingeschaltet: Hauswacht fragt nicht noch einmal (auch nach Neustart)
    registry.async_update_entity(code, disabled_by=None)
    await hass.async_block_till_done()
    entry = hass.config_entries.async_entries("hauswacht")[0]
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert registry.async_get(code).disabled_by is None
    assert ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_CODE_ENTITIES) is None


async def test_code_entity_created_later_is_offered(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    from homeassistant.helpers import entity_registry as er  # noqa: PLC0415
    from homeassistant.helpers import issue_registry as ir  # noqa: PLC0415

    from custom_components.hauswacht.const import DOMAIN, ISSUE_CODE_ENTITIES  # noqa: PLC0415

    await _setup(hass)
    assert ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_CODE_ENTITIES) is None
    code = _z2m_entity(hass, "Keypad Flur", "action_code")
    await hass.async_block_till_done()
    assert er.async_get(hass).async_get(code).disabled_by is None
    assert ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_CODE_ENTITIES) is not None
    # Selbst deaktiviert: Meldung verschwindet
    er.async_get(hass).async_update_entity(code, disabled_by=er.RegistryEntryDisabler.USER)
    await hass.async_block_till_done()
    assert ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_CODE_ENTITIES) is None


ACTION_CODES = {
    "licht": {"name": "Außenlicht", "code": "7777", "key": "arm_day_zones"},
    "nacht": {
        "name": "Nacht per Code",
        "code": "11",
        "key": "arm_all_zones",
        "action": "arm",
        "profile": "night",
    },
    "notruf": {
        "name": "Notruf",
        "code": "9111",
        "key": "arm_night_zones",
        "action": "silent_emergency",
    },
}


async def _setup_codes(hass: HomeAssistant) -> Any:
    options = {
        "users": _users(),
        "controls": _controls(),
        "notify_system": [PHONE],
        "action_codes": ACTION_CODES,
    }
    entry = make_entry(options)
    await setup_entry(hass, entry)
    return entry


async def test_action_code_fires_event_without_failure(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    await _setup_codes(hass)
    event_entity = "event.hauswacht_action_code"  # Testumgebung: Englisch
    state = hass.states.get(event_entity)
    assert state is not None
    assert state.attributes["event_types"] == ["Außenlicht"]
    await _press(hass, "arm_day_zones", "7777", 1)
    state = hass.states.get(event_entity)
    assert state is not None
    assert state.attributes["event_type"] == "Außenlicht"
    assert state.attributes["keypad"] == "Keypad Flur"
    assert _panel(hass) == AlarmControlPanelState.DISARMED  # Taste "Tag" hat sonst kein Profil
    panel = hass.states.get(PANEL)
    assert panel is not None
    assert panel.attributes["code_failures"] == 0
    assert {"mode": "disarm", "transaction": 1} in _sent(mqtt_mock)


async def test_action_code_arms_profile(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> None:
    await _setup_codes(hass)
    await _press(hass, "arm_all_zones", "11", 2)
    assert _panel(hass) in (AlarmControlPanelState.ARMING, AlarmControlPanelState.ARMED_NIGHT)
    panel = hass.states.get(PANEL)
    assert panel is not None
    assert "Nacht per Code" in panel.attributes["changed_by"]


async def test_action_code_never_disarms(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> None:
    entry = await _setup_codes(hass)
    entry.runtime_data.arm("night", changed_by="Test")
    await hass.async_block_till_done()
    await _press(hass, "disarm", "7777", 3)  # 7777 gibt es nur mit "Haus"
    assert _panel(hass) != AlarmControlPanelState.DISARMED


async def test_silent_emergency_code(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    await _setup_codes(hass)
    await _press(hass, "arm_night_zones", "9111", 4)
    assert _panel(hass) == AlarmControlPanelState.DISARMED
    assert push  # Nachricht an die Alarm-Empfänger


async def test_action_code_locked_during_pin_lockout(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    await _setup_codes(hass)
    for transaction in range(10, 15):
        await _press(hass, "disarm", "0000", transaction)
    await _press(hass, "arm_day_zones", "7777", 20)
    state = hass.states.get("event.hauswacht_action_code")
    assert state is not None
    assert state.attributes.get("event_type") is None
    assert {"mode": "invalid_code", "transaction": 20} in _sent(mqtt_mock)


async def _setup_force(hass: HomeAssistant, *, policy: str, may: bool = True) -> None:
    users = _users()
    users["anna"]["can_force_arm"] = may
    options = {
        "users": users,
        "controls": _controls(),
        "notify_system": [PHONE],
        "profiles": {"night": {"open_policy": policy}},
    }
    await setup_entry(hass, make_entry(options))
    set_sensor(hass, WINDOW, "on")  # Fenster offen
    await hass.async_block_till_done()


async def test_keypad_second_press_arms_anyway(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    await _setup_force(hass, policy="confirm")
    await _press(hass, "arm_night_zones", PIN, 30)
    assert _panel(hass) == AlarmControlPanelState.DISARMED
    assert {"mode": "not_ready", "transaction": 30} in _sent(mqtt_mock)
    await _press(hass, "arm_night_zones", PIN, 31)  # gleich noch einmal: trotzdem scharf
    assert _panel(hass) in (AlarmControlPanelState.ARMING, AlarmControlPanelState.ARMED_NIGHT)
    state = hass.states.get(PANEL)
    assert state is not None
    assert WINDOW in state.attributes["bypassed_sensors"]


async def test_keypad_force_needs_right(hass: HomeAssistant, mqtt_mock: MqttMockHAClient) -> None:
    await _setup_force(hass, policy="confirm", may=False)
    await _press(hass, "arm_night_zones", PIN, 40)
    await _press(hass, "arm_night_zones", PIN, 41)
    assert _panel(hass) == AlarmControlPanelState.DISARMED


async def test_keypad_force_respects_refuse(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    await _setup_force(hass, policy="refuse")
    await _press(hass, "arm_night_zones", PIN, 50)
    await _press(hass, "arm_night_zones", PIN, 51)
    assert _panel(hass) == AlarmControlPanelState.DISARMED


async def test_keypad_force_needs_same_key(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    await _setup_force(hass, policy="confirm")
    await _press(hass, "arm_night_zones", PIN, 60)
    await _press(hass, "disarm", PIN, 61)  # dazwischen etwas anderes: Bestätigung verfällt
    await _press(hass, "arm_night_zones", PIN, 62)
    assert _panel(hass) == AlarmControlPanelState.DISARMED


async def test_keypad_second_press_without_pin_confirms(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    await _setup_force(hass, policy="confirm")
    await _press(hass, "arm_night_zones", PIN, 70)
    assert _panel(hass) == AlarmControlPanelState.DISARMED
    await _press(hass, "arm_night_zones", None, 71)  # nur die Taste: bestätigt den ersten Druck
    assert _panel(hass) in (AlarmControlPanelState.ARMING, AlarmControlPanelState.ARMED_NIGHT)
    state = hass.states.get(PANEL)
    assert state is not None
    assert WINDOW in state.attributes["bypassed_sensors"]
    assert state.attributes["changed_by"] == "Anna (Keypad Flur)"
    # Rückmeldung: was nicht überwacht wird
    assert any("bypassed until disarming" in c.data["message"] for c in push)


async def test_keypad_force_without_any_pin(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    await _setup_force(hass, policy="confirm")
    await _press(hass, "arm_night_zones", None, 80)  # Scharfschalten ohne PIN ist erlaubt
    assert _panel(hass) == AlarmControlPanelState.DISARMED
    assert {"mode": "not_ready", "transaction": 80} in _sent(mqtt_mock)
    await _press(hass, "arm_night_zones", None, 81)
    assert _panel(hass) in (AlarmControlPanelState.ARMING, AlarmControlPanelState.ARMED_NIGHT)


async def test_keypad_force_with_pin_required(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    users = _users()
    options = {
        "users": users,
        "controls": _controls(),
        "notify_system": [PHONE],
        "code_arm_required": True,
        "profiles": {"night": {"open_policy": "confirm"}},
    }
    await setup_entry(hass, make_entry(options))
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    await _press(hass, "arm_night_zones", None, 90)  # ohne PIN: abgelehnt, nichts gemerkt
    assert {"mode": "invalid_code", "transaction": 90} in _sent(mqtt_mock)
    await _press(hass, "arm_night_zones", None, 91)
    assert _panel(hass) == AlarmControlPanelState.DISARMED
    await _press(hass, "arm_night_zones", PIN, 92)
    await _press(hass, "arm_night_zones", None, 93)  # zweiter Druck darf ohne PIN kommen
    assert _panel(hass) in (AlarmControlPanelState.ARMING, AlarmControlPanelState.ARMED_NIGHT)


async def test_keypad_unavailable_bypass_auto(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    options = {
        "users": _users(),
        "controls": _controls(),
        "notify_system": [PHONE],
        "profiles": {"night": {"unavailable_policy": "bypass_auto"}},
    }
    await setup_entry(hass, make_entry(options))
    set_sensor(hass, WINDOW, "unavailable")
    await hass.async_block_till_done()
    await _press(hass, "arm_night_zones", PIN, 95)
    assert _panel(hass) in (AlarmControlPanelState.ARMING, AlarmControlPanelState.ARMED_NIGHT)
    assert any("monitored again as soon as it reports" in c.data["message"] for c in push)


async def test_one_message_on_arming_and_cleared_on_disarm(
    hass: HomeAssistant, mqtt_mock: MqttMockHAClient
) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    options = {
        "users": _users(),
        "controls": _controls(),
        "notify_system": [PHONE],
        "events": {"armed": {"enabled": True}},
        "profiles": {"night": {"open_policy": "bypass_auto"}},
    }
    await setup_entry(hass, make_entry(options))
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    await _press(hass, "arm_night_zones", PIN, 100)
    await hass.async_block_till_done()
    sent = [c for c in push if c.data["message"] != "clear_notification"]
    # Nur EINE Nachricht: "scharf" mit dem Hinweis auf den überbrückten Melder
    assert len(sent) == 1
    assert "bypassed until disarming" in sent[0].data["message"]
    assert sent[0].data["data"]["tag"] == "hauswacht_state_main"
    await _press(hass, "disarm", PIN, 101)
    await hass.async_block_till_done()
    cleared = [c for c in push if c.data["message"] == "clear_notification"]
    assert cleared
    assert cleared[-1].data["data"]["tag"] == "hauswacht_state_main"
