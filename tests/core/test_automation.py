"""Tests der Automatik-Logik."""

from __future__ import annotations

from datetime import time

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
