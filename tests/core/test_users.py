"""Tests: Benutzer, gemeinsame PINs, Rechte, Gäste-Zeitraum, Bedrohungs-PIN."""

from __future__ import annotations

from custom_components.hauswacht.core.pin import PinHash
from custom_components.hauswacht.core.users import (
    LEGACY_USER_NAME,
    Action,
    User,
    allowed,
    allowed_in,
    card_needs_pin,
    find_by_ha_user,
    has_codes,
    label,
    match_pin,
    migrate_legacy_pin,
    parse_users,
    people_without_pin,
    pin_conflicts,
)


def ph(code: str) -> PinHash:
    # Test-"Hash": der PIN selbst; verify vergleicht nur (schnell, ohne PBKDF2)
    return PinHash(salt="x", digest=code)


def fake_verify(code: str | None, stored: PinHash | None) -> bool:
    return stored is not None and code == stored.digest


CHRISTIAN = User("c", "Christian", pin=ph("1111"), duress_pin=ph("9111"), ha_user="ha-c")
PETRA = User("p", "Petra", pin=ph("1111"), can_disarm=False)
NIKLAS = User("n", "Niklas", pin=ph("2222"), can_disarm=False)
GAST = User("g", "Gast", pin=ph("3333"), valid_from=1000.0, valid_until=2000.0)
GESPERRT = User("x", "Alt", pin=ph("4444"), active=False)
ALL = (CHRISTIAN, PETRA, NIKLAS, GAST, GESPERRT)


def match(code: str, now: float = 1500.0):  # type: ignore[no-untyped-def]
    return match_pin(code, ALL, now, verify=fake_verify)


def test_single_user_pin() -> None:
    m = match("2222")
    assert m.users == (NIKLAS,)
    assert label(m.users) == "Niklas"


def test_shared_pin_shows_all_names() -> None:
    m = match("1111")
    assert set(m.users) == {CHRISTIAN, PETRA}
    assert label(m.users) == "gemeinsamer PIN (Christian, Petra)"


def test_rights_if_any_user_may() -> None:
    assert allowed(match("1111").users, Action.DISARM)  # Christian darf
    assert not allowed(match("2222").users, Action.DISARM)  # Niklas nicht
    assert allowed(match("2222").users, Action.ARM)


def test_guest_only_within_window() -> None:
    assert match("3333", now=1500).users == (GAST,)
    early = match("3333", now=500)
    assert early.users == ()
    assert early.blocked == (GAST,)
    assert match("3333", now=2500).blocked == (GAST,)


def test_inactive_user_is_blocked() -> None:
    m = match("4444")
    assert not m.ok
    assert m.blocked == (GESPERRT,)


def test_duress_pin() -> None:
    m = match("9111")
    assert m.ok
    assert m.duress == (CHRISTIAN,)
    assert m.users == ()


def test_wrong_and_empty_pin() -> None:
    assert not match("0000").ok
    assert not match_pin(None, ALL, 0, verify=fake_verify).ok


def test_has_codes_and_ha_user() -> None:
    assert has_codes(ALL)
    assert not has_codes([User("a", "A")])
    assert find_by_ha_user(ALL, "ha-c") == CHRISTIAN
    assert find_by_ha_user(ALL, "unbekannt") is None
    assert find_by_ha_user(ALL, None) is None


def test_pin_conflicts() -> None:
    # normaler PIN darf keinem Bedrohungs-PIN gleichen
    assert pin_conflicts("9111", ALL, kind="pin", verify=fake_verify) == ["Christian"]
    assert pin_conflicts("1111", ALL, kind="pin", verify=fake_verify) == []  # gemeinsam ok
    # auch der eigene Bedrohungs-PIN zählt
    assert pin_conflicts("9111", ALL, kind="pin", exclude="c", verify=fake_verify) == ["Christian"]
    # Bedrohungs-PIN darf keinem normalen gleichen
    assert pin_conflicts("2222", ALL, kind="duress", verify=fake_verify) == ["Niklas"]
    # eigener alter Bedrohungs-PIN zählt beim Ersetzen nicht
    assert pin_conflicts("9111", ALL, kind="duress", exclude="c", verify=fake_verify) == []
    assert pin_conflicts("9111", ALL, kind="duress", exclude="p", verify=fake_verify) == [
        "Christian"
    ]


def test_parse_users_with_legacy_pin() -> None:
    options = {
        "pin_salt": "aa",
        "pin_digest": "bb",
        "users": {
            "u1": {
                "name": "Petra",
                "pin_salt": "s",
                "pin_digest": "d",
                "can_disarm": False,
                "valid_until": "2026-12-31T23:59:00+01:00",
                "ha_user": "ha-p",
            },
            "kaputt": "nicht ok",
        },
    }
    users = parse_users(options)
    assert [u.name for u in users] == [LEGACY_USER_NAME, "Petra"]
    petra = users[1]
    assert petra.pin == PinHash(salt="s", digest="d")
    assert petra.can_disarm is False
    assert petra.valid_until is not None
    assert petra.ha_user == "ha-p"
    assert parse_users({}) == ()


def test_migrate_legacy_pin() -> None:
    new = migrate_legacy_pin({"pin_salt": "s", "pin_digest": "d", "users": {"p": {"name": "P"}}})
    assert "pin_salt" not in new
    assert new["users"]["hauptbenutzer"] == {
        "name": LEGACY_USER_NAME,
        "pin_salt": "s",
        "pin_digest": "d",
    }
    assert new["users"]["p"] == {"name": "P"}
    assert LEGACY_USER_NAME in {u.name for u in parse_users(new)}
    assert migrate_legacy_pin({"x": 1}) == {"x": 1}


def test_people_without_pin() -> None:
    ha = {"ha-c": "Christian", "ha-p": "Petra", "ha-f": "Finja"}
    only_me = [User("c", "Christian", pin=ph("1111"), ha_user="ha-c")]
    assert people_without_pin(only_me, ha) == ["Finja", "Petra"]
    users = [*only_me, User("p", "Petra"), User("f", "Finja", pin=ph("2222"))]
    assert people_without_pin(users, ha) == ["Petra"]
    # ohne PINs ist alles egal
    assert people_without_pin([User("p", "Petra")], ha) == []
    # Master-PIN zählt nicht als Person
    master = [User("master", "Master-PIN", pin=ph("9999"))]
    assert people_without_pin(master, {"ha-c": "Christian"}) == ["Christian"]


# --- Rechte je Bereich -------------------------------------------------------


def test_general_rights_apply_to_all_areas() -> None:
    assert CHRISTIAN.may_in(Action.DISARM, "main")
    assert CHRISTIAN.may_in(Action.DISARM, "garage")
    assert not PETRA.may_in(Action.DISARM, "garage")


def test_legacy_area_list_limits_general_rights() -> None:
    user = User("a", "Anna", areas=("garage",), can_end_alarm=False)
    assert user.may_in(Action.DISARM, "garage")
    assert not user.may_in(Action.END_ALARM, "garage")
    assert not user.may_in(Action.ARM, "main")


def test_per_area_rights_parsed_and_checked() -> None:
    users = parse_users(
        {
            "users": {
                "anna": {
                    "name": "Anna",
                    "can_disarm": False,  # gilt bei "je Bereich" nicht
                    "rights": "per_area",
                    "area_rights": {"main": ["arm"], "garage": ["arm", "disarm", "bogus"]},
                }
            }
        }
    )
    anna = users[0]
    assert anna.may_in(Action.ARM, "main")
    assert not anna.may_in(Action.DISARM, "main")
    assert anna.may_in(Action.DISARM, "garage")
    assert not anna.may_in(Action.ARM, "gartenhaus")  # nicht eingetragen = gesperrt
    assert allowed_in(users, Action.DISARM, "garage")
    assert not allowed_in(users, Action.DISARM, "main")


def test_rights_all_ignores_old_area_rights() -> None:
    users = parse_users(
        {"users": {"anna": {"name": "Anna", "rights": "all", "area_rights": {"main": []}}}}
    )
    assert users[0].area_rights is None
    assert users[0].may_in(Action.DISARM, "main")


def test_shared_pin_combines_per_area_rights() -> None:
    a = User("a", "A", area_rights=(("main", frozenset({Action.ARM})),))
    b = User("b", "B", area_rights=(("garage", frozenset({Action.DISARM})),))
    assert allowed_in((a, b), Action.DISARM, "garage")
    assert not allowed_in((a, b), Action.DISARM, "main")


def test_card_needs_pin_only_with_pins() -> None:
    nobody = (User("a", "Anna", ha_user="ha-a"),)
    assert not card_needs_pin(nobody, "ha-a", unlinked_pin=True)
    assert not card_needs_pin(nobody, "ha-fremd", unlinked_pin=True)


def test_card_needs_pin_per_account() -> None:
    tablet = User("t", "Tablet", ha_user="ha-t", card_pin=True)
    users = (CHRISTIAN, tablet)
    assert not card_needs_pin(users, "ha-c", unlinked_pin=True)  # zugeordnet, Standard ohne PIN
    assert card_needs_pin(users, "ha-t", unlinked_pin=False)  # beim Benutzer verlangt
    assert card_needs_pin(users, "ha-fremd", unlinked_pin=True)  # ohne Benutzer: PIN-Regel
    assert not card_needs_pin(users, "ha-fremd", unlinked_pin=False)
    assert card_needs_pin(users, None, unlinked_pin=True)


def test_card_pin_parsed() -> None:
    users = parse_users({"users": {"t": {"name": "Tablet", "card_pin": True}, "a": {"name": "A"}}})
    assert {u.name: u.card_pin for u in users} == {"Tablet": True, "A": False}
