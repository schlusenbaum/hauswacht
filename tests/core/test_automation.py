"""Tests der Automatik-Logik."""

from __future__ import annotations

from datetime import time
from typing import Any

import pytest

from custom_components.hauswacht.core.automation import (
    DEFAULT_AWAY_DELAY,
    AutoConfig,
    all_away,
    anyone_home,
    is_active_day,
    parse_automation,
    parse_time,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("23:00", time(23, 0)),
        ("06:30:15", time(6, 30, 15)),
        ("", None),
        (None, None),
        ("25:00", None),
        ("abc", None),
        ("1:2:3:4", None),
    ],
)
def test_parse_time(value: object, expected: time | None) -> None:
    assert parse_time(value) == expected


def test_parse_automation() -> None:
    options = {
        "profiles": {
            "nacht": {
                "auto_arm_time": "23:00:00",
                "auto_disarm_time": "06:30",
                "auto_weekdays": ["mon", "tue", "xyz"],
                "auto_away_persons": ["person.a", "person.b", "person.a"],
                "auto_away_delay": 20,
                "auto_disarm_on_arrival": True,
            }
        }
    }
    config = parse_automation(options, "nacht")
    assert config.arm_time == time(23, 0)
    assert config.disarm_time == time(6, 30)
    assert config.weekdays == {"mon", "tue"}
    assert config.away_persons == ("person.a", "person.b")
    assert config.away_delay == 20
    assert config.disarm_on_arrival
    assert config.enabled


def test_parse_automation_defaults() -> None:
    config = parse_automation({}, "x")
    assert config == AutoConfig()
    assert not config.enabled
    assert config.away_delay == DEFAULT_AWAY_DELAY


@pytest.mark.parametrize("delay", [0, 999, "x", None])
def test_invalid_delay_falls_back(delay: object) -> None:
    options = {"profiles": {"p": {"auto_away_delay": delay}}}
    assert parse_automation(options, "p").away_delay == DEFAULT_AWAY_DELAY


def test_active_days() -> None:
    every_day = AutoConfig()
    assert all(is_active_day(every_day, i) for i in range(7))
    weekend = AutoConfig(weekdays=frozenset({"sat", "sun"}))
    assert not is_active_day(weekend, 0)
    assert is_active_day(weekend, 5)


@pytest.mark.parametrize(
    ("states", "away"),
    [
        (["not_home", "Arbeit"], True),
        (["not_home", "home"], False),
        (["not_home", "unavailable"], False),  # unbekannt zählt nicht als weg
        (["not_home", None], False),
        ([], False),
    ],
)
def test_all_away(states: list[str | None], away: bool) -> None:
    assert all_away(states) is away


def test_anyone_home() -> None:
    assert anyone_home(["not_home", "home"])
    assert not anyone_home(["not_home", "unknown"])


# --- 0.42: Anwesenheit aus mehreren Signalen, Unscharf mit Türbeleg -------------------


def test_arrival_mode_takes_over_old_switch() -> None:
    from custom_components.hauswacht.core.automation import (  # noqa: PLC0415
        ARRIVAL_AUTO_ONLY,
        ARRIVAL_DOOR,
        ARRIVAL_OFF,
        arrival_mode,
    )

    assert arrival_mode({}) == ARRIVAL_OFF
    assert arrival_mode({"auto_disarm_on_arrival": True}) == ARRIVAL_AUTO_ONLY
    assert arrival_mode({"auto_disarm_on_arrival": False}) == ARRIVAL_OFF
    # Die neue Auswahl gewinnt gegen den alten Schalter
    assert arrival_mode({"auto_arrival_mode": "door", "auto_disarm_on_arrival": True}) == (
        ARRIVAL_DOOR
    )
    assert arrival_mode({"auto_arrival_mode": "quatsch"}) == ARRIVAL_OFF


def test_door_proof_needs_persons() -> None:
    options: dict[str, Any] = {"profiles": {"p": {"auto_arrival_mode": "door"}}}
    config = parse_automation(options, "p")
    assert config.arrival_mode == "door"
    assert not config.door_proof
    assert not config.disarm_on_arrival
    options["profiles"]["p"]["auto_away_persons"] = ["person.a"]
    config = parse_automation(options, "p")
    assert config.door_proof
    assert config.disarm_on_arrival


@pytest.mark.parametrize(("value", "expected"), [(10, 10), (0, 5), (31, 5), ("x", 5), (None, 5)])
def test_arrival_window(value: object, expected: int) -> None:
    options = {"profiles": {"p": {"auto_arrival_window": value}}}
    assert parse_automation(options, "p").arrival_window == expected


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        ("home", True),
        ("not_home", False),
        ("Arbeit", False),
        ("unknown", None),
        ("unavailable", None),
        ("", None),
        (None, None),
    ],
)
def test_person_value(state: str | None, expected: bool | None) -> None:
    from custom_components.hauswacht.core.automation import person_value  # noqa: PLC0415

    assert person_value(state) is expected


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        ([False, False], False),  # alle sicher weg
        ([False, True], True),  # ein Signal zuhause genügt
        ([False, None], None),  # ein unbekanntes Signal: nicht weg
        ([None, True], True),
        ([], None),
    ],
)
def test_combine(values: list[bool | None], expected: bool | None) -> None:
    from custom_components.hauswacht.core.automation import combine  # noqa: PLC0415

    assert combine(values) is expected


def test_all_away_and_anyone_home_values() -> None:
    from custom_components.hauswacht.core.automation import (  # noqa: PLC0415
        all_away_values,
        anyone_home_values,
    )

    assert all_away_values([False, False])
    assert not all_away_values([False, None])
    assert not all_away_values([])
    assert anyone_home_values([None, True])
    assert not anyone_home_values([None, False])


@pytest.mark.parametrize(
    ("arrival", "door", "expected"),
    [
        (100.0, 130.0, True),  # Tür nach der Ortung
        (130.0, 100.0, True),  # Ortung nach der Tür
        (100.0, 400.0, True),  # genau 5 Minuten
        (100.0, 401.0, False),
        (None, 100.0, False),  # Tür ohne Rückkehr
        (100.0, None, False),  # Rückkehr ohne Tür (Geister-Heimkehr)
    ],
)
def test_door_proof_ok(arrival: float | None, door: float | None, expected: bool) -> None:
    from custom_components.hauswacht.core.automation import door_proof_ok  # noqa: PLC0415

    assert door_proof_ok(arrival, door, 5) is expected


# --- 0.44.3: "Unscharf um" über Nacht ---------------------------------------------------


@pytest.mark.parametrize(
    ("weekday", "expected"),
    [
        (0, True),  # Montag: aktiver Tag
        (4, True),  # Freitag
        (5, True),  # Samstag früh: Freitagnacht scharf geschaltet
        (6, False),  # Sonntag früh: Samstag ist kein aktiver Tag
    ],
)
def test_disarm_due_overnight(weekday: int, expected: bool) -> None:
    from custom_components.hauswacht.core.automation import disarm_due  # noqa: PLC0415

    workdays = frozenset({"mon", "tue", "wed", "thu", "fri"})
    night = AutoConfig(arm_time=time(23, 0), disarm_time=time(6, 30), weekdays=workdays)
    assert disarm_due(night, weekday) is expected


def test_disarm_due_same_day_only_on_active_days() -> None:
    from custom_components.hauswacht.core.automation import disarm_due, overnight  # noqa: PLC0415

    workdays = frozenset({"mon", "tue", "wed", "thu", "fri"})
    day = AutoConfig(arm_time=time(7, 30), disarm_time=time(16, 0), weekdays=workdays)
    assert not overnight(day)
    assert disarm_due(day, 4)
    assert not disarm_due(day, 5)  # Samstag: kein Tagesprofil
    # nur "Unscharf um" ohne Scharf-Uhrzeit: kein "über Nacht"
    only_disarm = AutoConfig(disarm_time=time(6, 30), weekdays=workdays)
    assert not overnight(only_disarm)
    assert not disarm_due(only_disarm, 5)
    # ohne Wochentage: täglich
    assert disarm_due(AutoConfig(arm_time=time(23, 0), disarm_time=time(6, 30)), 6)
