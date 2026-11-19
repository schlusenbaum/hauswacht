"""Allgemeiner Keypad-Eingang (ADR 0012): Ergebnisse, Anzeige, doppelte Meldungen."""

from __future__ import annotations

from custom_components.hauswacht.core.controls import (
    REPLY_ALREADY_DISARMED,
    REPLY_INVALID_CODE,
    REPLY_NOT_READY,
    ControlKind,
    parse_controls,
)
from custom_components.hauswacht.core.keypad_input import (
    DUPLICATE_WINDOW,
    NOT_ALLOWED,
    Display,
    InputOutcome,
    KeypadResult,
    RecentInputs,
    area_display,
    combined_display,
    generic_keypad_for,
    normalize_button,
    public_result,
    remember_unknown,
    z2m_reply,
)


def _outcome(result: str, **kw: object) -> InputOutcome:
    return InputOutcome(result, **kw)  # type: ignore[arg-type]


def test_z2m_replies_unchanged() -> None:
    assert z2m_reply(_outcome("ok"), "disarm", "disarm") == "disarm"
    assert z2m_reply(_outcome("ok"), "arm_all_zones", "x") == "arm_all_zones"
    assert z2m_reply(_outcome("ok", action_code=True), "arm_all_zones", "disarm") == "disarm"
    assert z2m_reply(_outcome("invalid_code"), "disarm", "x") == REPLY_INVALID_CODE
    assert z2m_reply(_outcome("locked"), "disarm", "x") == REPLY_INVALID_CODE
    assert z2m_reply(_outcome(NOT_ALLOWED), "disarm", "x") == REPLY_INVALID_CODE
    assert z2m_reply(_outcome(NOT_ALLOWED), "arm_all_zones", "x") == REPLY_NOT_READY
    assert z2m_reply(_outcome("pending"), "disarm", "x") == REPLY_NOT_READY
    assert z2m_reply(_outcome("unknown_button"), "arm_day_zones", "x") == REPLY_NOT_READY
    assert z2m_reply(_outcome("already_disarmed"), "disarm", "x") == REPLY_ALREADY_DISARMED
    assert z2m_reply(_outcome("ok", emergency=True), "emergency", "x") is None


def test_missing_rights_look_like_wrong_pin() -> None:
    assert public_result(_outcome(NOT_ALLOWED)) == KeypadResult.INVALID_CODE
    assert public_result(_outcome("not_ready")) == "not_ready"


def test_generic_buttons_are_free_names() -> None:
    controls = parse_controls(
        {
            "controls": {
                "flur": {
                    "name": "Keypad Flur",
                    "kind": "generic_keypad",
                    "buttons": {"Away": "abwesend", "home ": "zuhause", "disarm": "x", "n": ""},
                },
                "z2m": {"name": "Z", "kind": "keypad", "buttons": {"away": "abwesend"}},
            }
        }
    )
    assert controls["flur"].kind is ControlKind.GENERIC_KEYPAD
    assert dict(controls["flur"].buttons) == {"away": "abwesend", "home": "zuhause"}
    assert dict(controls["z2m"].buttons) == {}  # Zigbee2MQTT: nur feste Tasten
    assert generic_keypad_for(controls, "flur") is controls["flur"]
    assert generic_keypad_for(controls, "keypad flur") is controls["flur"]
    assert generic_keypad_for(controls, "z2m") is None  # kein allgemeines Keypad
    assert generic_keypad_for(controls, "") is None
    assert normalize_button(" Arm Away ") == "arm_away"


def test_display_states() -> None:
    assert area_display("arming", test_mode=False) is Display.EXIT_DELAY
    assert area_display("pending", test_mode=False) is Display.ENTRY_DELAY
    assert area_display("triggered", test_mode=False) is Display.TRIGGERED
    # Testmodus: nie "triggered" – Keypads mit Sirene dürfen nicht losheulen
    assert area_display("triggered", test_mode=True) is Display.TEST_ALARM
    assert area_display("armed_night", test_mode=False) is Display.ARMED_NIGHT


def test_combined_display() -> None:
    d = Display
    assert combined_display([d.DISARMED, d.ARMED_NIGHT], fire=False) is d.ARMED_NIGHT
    assert combined_display([d.ARMED_HOME, d.ARMED_NIGHT], fire=False) is d.ARMED_AWAY
    assert combined_display([d.EXIT_DELAY, d.TRIGGERED], fire=False) is d.TRIGGERED
    assert combined_display([d.DISARMED], fire=False) is d.DISARMED
    assert combined_display([d.TRIGGERED], fire=True) is d.FIRE  # Brand hat Vorrang


def test_duplicates_within_window_only() -> None:
    recent = RecentInputs()
    key = RecentInputs.key("away", "abc", False)
    first = _outcome("invalid_code")
    assert recent.duplicate("flur", key, 10.0) is None
    recent.remember("flur", key, 10.0, first)
    assert recent.duplicate("flur", key, 11.0) is first
    assert recent.duplicate("flur", RecentInputs.key("away", "xyz", False), 11.0) is None
    assert recent.duplicate("garage", key, 11.0) is None
    assert recent.duplicate("flur", key, 10.0 + DUPLICATE_WINDOW + 0.1) is None


def test_unknown_keypads_are_remembered_briefly() -> None:
    seen = remember_unknown({}, "flur", 0.0)
    seen = remember_unknown(seen, "garage", 60.0)
    assert list(seen) == ["garage", "flur"]
    seen = remember_unknown(seen, "flur", 120.0)
    assert list(seen) == ["flur", "garage"]
    assert remember_unknown(seen, "keller", 120.0 + 3601) == {"keller": 3721.0}
    many: dict[str, float] = {}
    for i in range(10):
        many = remember_unknown(many, f"k{i}", float(i))
    assert len(many) == 5
