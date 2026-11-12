"""Tests: Bedienteile und RFID-Karten."""

from __future__ import annotations

from custom_components.hauswacht.core.controls import (
    ALL_AREAS,
    ControlKind,
    Emergency,
    Login,
    PendingLogin,
    TagAction,
    keypad_for_topic,
    keypad_mode,
    looks_like_card,
    normalize_tag,
    parse_controls,
    reader_for,
    remember_card,
    second_factor_ok,
    sticker_for,
    tag_intent,
)
from custom_components.hauswacht.core.users import match_tag, parse_users, tag_conflicts

OPTIONS = {
    "controls": {
        "flur": {
            "name": "Keypad Flur",
            "kind": "keypad",
            "topic": "zigbee2mqtt/Keypad Flur/",
            "buttons": {"arm_night_zones": "night", "arm_all_zones": "away", "x": "y"},
            "emergency": "alarm",
        },
        "tuer": {"name": "Aufkleber Tür", "kind": "sticker", "tag": "04:a1-b2", "action": "toggle"},
        "leser": {"name": "Leser", "kind": "reader", "device": "dev1", "area": "garage"},
    }
}


def test_parse_controls() -> None:
    controls = parse_controls(OPTIONS)
    keypad = controls["flur"]
    assert keypad.kind is ControlKind.KEYPAD
    assert keypad.topic == "zigbee2mqtt/Keypad Flur"
    assert keypad.buttons == {"arm_night_zones": "night", "arm_all_zones": "away"}
    assert keypad.emergency is Emergency.ALARM
    assert keypad.login is Login.PIN_OR_CARD
    assert keypad.area == ALL_AREAS
    assert controls["tuer"].tag == "04A1B2"
    assert controls["tuer"].action is TagAction.TOGGLE
    assert controls["leser"].login is Login.CARD
    assert keypad_for_topic(controls, "zigbee2mqtt/Keypad Flur") is keypad
    assert sticker_for(controls, "04 A1 B2") is controls["tuer"]
    assert reader_for(controls, "dev1") is controls["leser"]
    assert reader_for(controls, None) is None


def test_normalize_and_intent() -> None:
    assert normalize_tag("ab:cd-12") == "ABCD12"
    assert tag_intent(TagAction.TOGGLE, armed=True) == "disarm"
    assert tag_intent(TagAction.TOGGLE, armed=False) == "arm"
    assert tag_intent(TagAction.ARM, armed=True) == "arm"


def test_keypad_mode() -> None:
    assert keypad_mode("disarmed") == "disarm"
    assert keypad_mode("arming") == "exit_delay"
    assert keypad_mode("pending") == "entry_delay"
    assert keypad_mode("triggered") == "in_alarm"
    assert keypad_mode("armed_home") == "arm_day_zones"
    assert keypad_mode("armed_night") == "arm_night_zones"
    assert keypad_mode("armed_away") == "arm_all_zones"
    assert keypad_mode("armed_custom_bypass") == "arm_all_zones"


def test_second_factor() -> None:
    first = PendingLogin(frozenset({"anna"}), "card", 100.0)
    assert second_factor_ok(first, frozenset({"anna"}), "pin", 110.0)
    assert not second_factor_ok(first, frozenset({"anna"}), "card", 110.0)  # gleiche Art
    assert not second_factor_ok(first, frozenset({"ben"}), "pin", 110.0)  # anderer Benutzer
    assert not second_factor_ok(first, frozenset({"anna"}), "pin", 200.0)  # zu spät
    assert not second_factor_ok(None, frozenset({"anna"}), "pin", 110.0)


def test_user_tags() -> None:
    options = {
        "users": {
            "anna": {"name": "Anna", "tags": ["04a1b2", "x"]},
            "ben": {"name": "Ben", "tags": "04:A1:B2, 99", "active": False},
        }
    }
    users = parse_users(options)
    assert users[0].tags == ("04A1B2", "X")
    assert users[1].tags == ("04A1B2", "99")
    match = match_tag("04-a1-b2", users, now=0)
    assert [u.name for u in match.users] == ["Anna"]
    assert [u.name for u in match.blocked] == ["Ben"]
    assert not match_tag("", users, now=0).ok
    assert tag_conflicts(users) == {"04A1B2": ["Anna", "Ben"]}


def test_pins_never_look_like_cards() -> None:
    for pin in ("1234", "13579", "12345678"):
        assert not looks_like_card(pin)
    assert looks_like_card("123456789")  # 9 Ziffern: kein PIN möglich
    assert looks_like_card("04:A1:B2")
    assert not looks_like_card("")


def test_remember_card_newest_first_and_limited() -> None:
    seen: dict[str, tuple[str, float]] = {}
    for i in range(12):
        seen = remember_card(seen, f"CARD{i:02d}", "Keypad", float(i))
    assert len(seen) == 10
    assert next(iter(seen)) == "CARD11"
    seen = remember_card(seen, "card05", "Leser", 99.0)
    assert next(iter(seen)) == "CARD05"
    assert seen["CARD05"] == ("Leser", 99.0)
