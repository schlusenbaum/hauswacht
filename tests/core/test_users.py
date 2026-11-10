"""Tests: Benutzer, gemeinsame PINs, Rechte, Gäste-Zeitraum, Bedrohungs-PIN."""

from __future__ import annotations

from custom_components.hauswacht.core.pin import PinHash
from custom_components.hauswacht.core.users import (
    LEGACY_USER_NAME,
    Action,
    User,
    allowed,
    find_by_ha_user,
    has_codes,
    label,
    match_pin,
    migrate_legacy_pin,
    parse_users,
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
