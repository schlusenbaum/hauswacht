"""Tests: Bedienteile und RFID-Karten."""

from __future__ import annotations

import pytest

from custom_components.hauswacht.core.controls import (
    ALL_AREAS,
    ControlKind,
    Emergency,
    Login,
    PendingLogin,
    TagAction,
    fresh_cards,
    is_random_uid,
    keypad_for_topic,
    keypad_mode,
    learn_minutes,
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


def test_learn_minutes_default_and_limits() -> None:
    assert learn_minutes({}) == 5
    assert learn_minutes({"card_learn_minutes": 0}) == 0
    assert learn_minutes({"card_learn_minutes": 999}) == 60
    assert learn_minutes({"card_learn_minutes": "x"}) == 5


def test_fresh_cards_drop_old_ones() -> None:
    seen = {"NEW": ("Keypad", 1000.0), "OLD": ("Keypad", 800.0)}
    assert list(fresh_cards(seen, 1000.0, 5)) == ["NEW", "OLD"]
    assert list(fresh_cards(seen, 1150.0, 5)) == ["NEW"]
    assert fresh_cards(seen, 1000.0, 0) == {"NEW": ("Keypad", 1000.0)}


def test_random_uids_are_detected() -> None:
    assert is_random_uid("+08837CF0")  # Handy
    assert is_random_uid("08ecA2b8")
    assert not is_random_uid("+041B4932E82880")  # feste 7-Byte-UID
    assert not is_random_uid("40CC995C")
    assert not is_random_uid("08837CF0AA")  # länger als 4 Byte


# --- 0.43: Taster und Türschlösser ---------------------------------------------


def test_parse_button_and_lock() -> None:
    from custom_components.hauswacht.core.controls import (  # noqa: PLC0415
        ControlKind,
        LockSource,
        parse_controls,
    )

    controls = parse_controls(
        {
            "controls": {
                "t": {
                    "kind": "button",
                    "entity": "event.t",
                    "presses": {"single": "away", "": "x", "double": None},
                },
                "s": {"kind": "lock", "entity": "lock.s", "source": "generic", "who": "sensor.w"},
                "n": {"kind": "lock", "entity": "lock.n", "topic": "nuki/1/", "profile": "night"},
            }
        }
    )
    assert controls["t"].kind is ControlKind.BUTTON
    assert controls["t"].presses == {"single": "away"}
    assert controls["s"].source is LockSource.GENERIC
    assert controls["s"].who == "sensor.w"
    assert controls["n"].source is LockSource.NUKI_MQTT  # Standard
    assert controls["n"].topic == "nuki/1"
    assert controls["n"].profile == "night"


@pytest.mark.parametrize(
    ("domain", "state", "event_type", "expected"),
    [
        ("event", "2026-11-15T12:00:00", "single", "single"),
        ("event", "2026-11-15T12:00:00", None, None),
        ("sensor", "double", None, "double"),
        ("sensor", "", None, None),
        ("sensor", "None", None, None),
    ],
)
def test_press_value(domain: str, state: str, event_type: str | None, expected: str | None) -> None:
    from custom_components.hauswacht.core.controls import press_value  # noqa: PLC0415

    assert press_value(domain, state, event_type) == expected


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        ("unknown", "2026-11-15T12:00:00", True),  # erstes Drücken
        ("2026-11-15T12:00:00", "2026-11-15T12:00:05", True),
        ("unavailable", "2026-11-15T12:00:00", False),  # wieder verbunden
        (None, "2026-11-15T12:00:00", False),  # Neustart
        ("single", "single", False),
        ("", "single", True),
        ("single", "", False),
    ],
)
def test_is_new_press(old: str | None, new: str | None, expected: bool) -> None:
    from custom_components.hauswacht.core.controls import is_new_press  # noqa: PLC0415

    assert is_new_press(old, new) is expected


@pytest.mark.parametrize(
    ("payload", "intent", "identity", "reason"),
    [
        ("1,0,52653,0,0", "unlock", "NUKIAUTH52653", "ok"),  # App
        ("3,0,52653,0,0", "unlock", "NUKIAUTH52653", "ok"),  # öffnen
        ("1,0,1921,8192,1", "unlock", "NUKICODE8192", "ok"),  # Keypad-Code
        ("2,0,52653,0,0", "lock", "NUKIAUTH52653", "ok"),
        ("4,0,52653,0,0", "lock", "NUKIAUTH52653", "ok"),  # Lock 'n' Go
        ("1,2,0,0,1", "unlock", None, "not_by_person"),  # Knopf innen
        ("2,6,0,0,0", "lock", None, "not_by_person"),  # automatisch
        ("1,172,52653,0,0", "unlock", None, "not_by_person"),  # MQTT
        ("1,0,0,0,0", "unlock", None, "no_id"),
    ],
)
def test_parse_nuki_event(payload: str, intent: str, identity: str | None, reason: str) -> None:
    from custom_components.hauswacht.core.controls import parse_nuki_event  # noqa: PLC0415

    event = parse_nuki_event(payload)
    assert event is not None
    assert (event.intent, event.identity, event.reason) == (intent, identity, reason)


@pytest.mark.parametrize("payload", ["5,0,1,0,0", "80,0,1,0,0", "x,y", "1,0", ""])
def test_parse_nuki_event_ignores_other(payload: str) -> None:
    from custom_components.hauswacht.core.controls import parse_nuki_event  # noqa: PLC0415

    assert parse_nuki_event(payload) is None


def test_generic_identity_and_labels() -> None:
    from custom_components.hauswacht.core.controls import (  # noqa: PLC0415
        generic_identity,
        lock_id_label,
    )

    assert generic_identity("Anna") == "LOCKANNA"
    assert generic_identity(" 17 ") == "LOCK17"
    assert generic_identity("unknown") is None
    assert generic_identity("") is None
    assert generic_identity(None) is None
    assert lock_id_label("NUKIAUTH52653") == "Nuki-Benutzer 52653"
    assert lock_id_label("NUKICODE8192") == "Nuki-Keypad-Code 8192"
    assert lock_id_label("LOCKANNA") == "LOCKANNA"
    assert lock_id_label("NUKIAUTH52653", "en") == "Nuki user 52653"


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        ("locked", "unlocked", "unlock"),
        ("locked", "unlocking", "unlock"),
        ("unlocking", "unlocked", None),  # schon gezählt
        ("unlocked", "open", None),
        ("unlocked", "locked", "lock"),
        ("locked", "jammed", None),
        (None, "unlocked", None),
    ],
)
def test_lock_intent(old: str | None, new: str | None, expected: str | None) -> None:
    from custom_components.hauswacht.core.controls import lock_intent  # noqa: PLC0415

    assert lock_intent(old, new) == expected


def test_lock_confirmed() -> None:
    from custom_components.hauswacht.core.controls import lock_confirmed  # noqa: PLC0415

    assert lock_confirmed(100.0, 110.0)
    assert lock_confirmed(110.0, 100.0)
    assert not lock_confirmed(100.0, 131.0)
    assert not lock_confirmed(None, 100.0)
    assert not lock_confirmed(100.0, None)


def test_force_confirmed_window() -> None:
    from custom_components.hauswacht.core.controls import (  # noqa: PLC0415
        FORCE_ARM_WINDOW,
        PendingForce,
        force_confirmed,
    )

    users = frozenset({"anna"})
    pending = PendingForce("arm_night_zones", users, 100.0)
    assert force_confirmed(pending, "arm_night_zones", users, 105.0)
    assert not force_confirmed(pending, "arm_night_zones", users, 100.0 + FORCE_ARM_WINDOW + 1)
    assert not force_confirmed(pending, "arm_all_zones", users, 105.0)
    assert not force_confirmed(pending, "arm_night_zones", frozenset({"ben"}), 105.0)
    assert not force_confirmed(None, "arm_night_zones", users, 105.0)
