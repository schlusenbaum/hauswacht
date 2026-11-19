"""MQTT-Schnittstelle (ADR 0012, Stufe 3): Befehle, Zustandswörter, Topics."""

from __future__ import annotations

from custom_components.hauswacht.core.controls import ControlKind, parse_controls
from custom_components.hauswacht.core.mqtt_keypad import (
    parse_command,
    parse_state_words,
    state_word,
    state_words_text,
    validate_base_topic,
)


def test_text_commands() -> None:
    assert parse_command("ARM_AWAY").button == "arm_away"  # type: ignore[union-attr]
    assert parse_command(b" disarm ").button == "disarm"  # type: ignore[union-attr]
    assert parse_command("PANIC").button == "emergency"  # type: ignore[union-attr]
    assert parse_command("AUS", disarm_word="aus").button == "disarm"  # type: ignore[union-attr]
    assert parse_command("") is None
    assert parse_command("x" * 600) is None
    assert parse_command(b"\xff") is None


def test_json_commands() -> None:
    cmd = parse_command('{"action": "ARM_NIGHT", "code": "1234", "force": true, "id": 7}')
    assert cmd is not None
    assert (cmd.button, cmd.code, cmd.force, cmd.request_id) == ("arm_night", "1234", True, 7)
    cmd = parse_command('{"command": "DISARM", "pin": 1234}', code_field="pin")
    assert cmd is not None
    assert (cmd.button, cmd.code, cmd.force) == ("disarm", "1234", False)
    assert parse_command('{"code": "1234"}') is None  # ohne Befehl
    assert parse_command("{kaputt") is None
    assert parse_command("[1, 2]") is None
    nested = parse_command('{"action": "ARM_AWAY", "id": {"a": 1}}')
    assert nested is not None
    assert nested.request_id is None


def test_state_words() -> None:
    assert state_word("exit_delay", {}) == "arming"
    assert state_word("entry_delay", {}) == "pending"
    # Im Testmodus nie "triggered" – auch nicht als Standardwort
    assert state_word("test_alarm", {}) == "test_alarm"
    words = parse_state_words("armed_away: ARMED_AWAY\nunbekannt: X\nkaputt\ndisarmed:  ")
    assert words == {"armed_away": "ARMED_AWAY"}
    assert state_word("armed_away", words) == "ARMED_AWAY"
    assert parse_state_words(state_words_text(words)) == words
    assert parse_state_words({"triggered": "ALARM"}) == {"triggered": "ALARM"}
    assert parse_state_words(None) == {}


def test_base_topic_rules() -> None:
    assert validate_base_topic("hauswacht/flur", []) is None
    assert validate_base_topic(" ", []) == "mqtt_topic_missing"
    assert validate_base_topic("haus/+/x", []) == "mqtt_topic_invalid"
    assert validate_base_topic("/hauswacht", []) == "mqtt_topic_invalid"
    assert validate_base_topic("zigbee2mqtt/flur", []) == "mqtt_topic_z2m"
    assert validate_base_topic("hauswacht/flur", ["hauswacht/flur/"]) == "mqtt_topic_taken"
    assert validate_base_topic("hauswacht/flur/x", ["hauswacht/flur"]) == "mqtt_topic_taken"
    assert validate_base_topic("hauswacht/flur2", ["hauswacht/flur"]) is None


def test_parse_mqtt_keypad_control() -> None:
    controls = parse_controls(
        {
            "controls": {
                "flur": {
                    "name": "Tablet",
                    "kind": "mqtt_keypad",
                    "topic": "hauswacht/flur/",
                    "buttons": {"ARM_AWAY": "away"},
                    "words": {"armed_away": "ARMED_AWAY"},
                    "code_field": "pin",
                }
            }
        }
    )
    tablet = controls["flur"]
    assert tablet.kind is ControlKind.MQTT_KEYPAD
    assert tablet.topic == "hauswacht/flur"
    assert dict(tablet.buttons) == {"arm_away": "away"}
    assert dict(tablet.words) == {"armed_away": "ARMED_AWAY"}
    assert (tablet.code_field, tablet.disarm_word, tablet.panic_word) == ("pin", "DISARM", "PANIC")
