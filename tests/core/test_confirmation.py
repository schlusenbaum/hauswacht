"""Bestätigung durch einen zweiten Melder."""

from __future__ import annotations

from custom_components.hauswacht.core.confirmation import (
    FREQUENT_COUNT,
    ConfirmationTracker,
    LoneTriggerCounter,
)
from custom_components.hauswacht.core.sensors import parse_zones

A, B, C = "binary_sensor.a", "binary_sensor.b", "binary_sensor.c"


def test_second_sensor_confirms() -> None:
    tracker = ConfirmationTracker()
    assert tracker.check(A, "keller", 120, 0, others_available=2) is False
    assert tracker.check(B, "keller", 120, 60, others_available=2) is True
    assert tracker.pending == {}


def test_same_sensor_twice_does_not_confirm() -> None:
    tracker = ConfirmationTracker()
    assert tracker.check(A, "keller", 120, 0, others_available=2) is False
    assert tracker.check(A, "keller", 120, 30, others_available=2) is False
    assert tracker.pending[A].since == 0
    assert tracker.pending[A].until == 150


def test_window_expires() -> None:
    tracker = ConfirmationTracker()
    tracker.check(A, "keller", 120, 0, others_available=2)
    assert tracker.check(B, "keller", 120, 121, others_available=2) is False
    assert set(tracker.pending) == {B}


def test_other_zone_does_not_confirm() -> None:
    tracker = ConfirmationTracker()
    tracker.check(A, "keller", 120, 0, others_available=2)
    assert tracker.check(C, "eg", 120, 10, others_available=2) is False


def test_no_other_sensor_available_triggers_immediately() -> None:
    tracker = ConfirmationTracker()
    assert tracker.check(A, "keller", 120, 0, others_available=0) is True


def test_expire_returns_lone_triggers() -> None:
    tracker = ConfirmationTracker()
    tracker.check(A, "keller", 120, 0, others_available=2)
    assert tracker.expire(100) == []
    assert tracker.expire(120) == [A]


def test_lone_trigger_counter() -> None:
    counter = LoneTriggerCounter()
    results = [counter.record(A, i * 600) for i in range(FREQUENT_COUNT)]
    assert results == [False] * (FREQUENT_COUNT - 1) + [True]
    assert counter.record(A, 5000) is False  # Zählung beginnt neu
    counter2 = LoneTriggerCounter()
    assert [counter2.record(B, i * 4000) for i in range(4)] == [False] * 4  # zu selten


def test_zone_parses_confirm_options() -> None:
    zones = parse_zones(
        {
            "zones": {
                "keller": {"name": "Keller", "entities": [A], "confirm": True, "confirm_window": 5},
                "eg": {"name": "EG", "entities": [B]},
            }
        }
    )
    assert zones["keller"].confirm is True
    assert zones["keller"].confirm_window == 10  # Untergrenze
    assert zones["eg"].confirm is False
    assert zones["eg"].confirm_window == 120
