"""Tests: Aktions-Codes (Code + Taste am Keypad)."""

from __future__ import annotations

from custom_components.hauswacht.core.action_codes import (
    ALL_KEYPADS,
    CodeAction,
    action_code_clash,
    find_action_code,
    is_action_code,
    is_valid_action_code,
    parse_action_codes,
)

OPTIONS = {
    "action_codes": {
        "licht": {"name": "Außenlicht", "code": "7777", "key": "arm_day_zones"},
        "aus": {"name": "Licht aus", "code": "7777", "key": "arm_night_zones", "keypad": "flur"},
        "nacht": {
            "name": "Nacht",
            "code": "11",
            "key": "arm_all_zones",
            "action": "arm",
            "profile": "night",
        },
        "kaputt": {"name": "x", "code": "1", "key": "arm_day_zones"},  # zu kurz
        "sos": {"name": "y", "code": "1234", "key": "emergency"},  # SOS hat keinen Code
        "arm_ohne": {"name": "z", "code": "55", "key": "disarm", "action": "arm"},  # ohne Profil
    }
}


def test_parse_keeps_only_valid_codes() -> None:
    codes = parse_action_codes(OPTIONS)
    assert [c.code_id for c in codes] == ["licht", "aus", "nacht"]
    assert codes[0].action is CodeAction.EVENT
    assert codes[0].keypad == ALL_KEYPADS
    assert codes[2].profile == "night"


def test_code_length() -> None:
    assert is_valid_action_code("11")
    assert is_valid_action_code("12345678")
    assert not is_valid_action_code("1")
    assert not is_valid_action_code("123456789")
    assert not is_valid_action_code("12a")


def test_find_by_code_key_and_keypad() -> None:
    codes = parse_action_codes(OPTIONS)
    found = find_action_code(codes, "7777", "arm_day_zones", "irgendwo")
    assert found is not None
    assert found.name == "Außenlicht"
    assert find_action_code(codes, "7777", "arm_night_zones", "flur") is not None
    assert find_action_code(codes, "7777", "arm_night_zones", "garage") is None
    assert find_action_code(codes, "7778", "arm_day_zones", "flur") is None
    assert find_action_code(codes, None, "arm_day_zones", "flur") is None


def test_clash_and_pin_check() -> None:
    codes = parse_action_codes(OPTIONS)
    assert action_code_clash(codes, "7777", "arm_day_zones", "flur") is not None  # alle überlappt
    assert action_code_clash(codes, "7777", "arm_all_zones", ALL_KEYPADS) is None
    assert action_code_clash(codes, "7777", "arm_day_zones", ALL_KEYPADS, exclude="licht") is None
    assert is_action_code(codes, "11")
    assert not is_action_code(codes, "1234")
