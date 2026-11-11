"""Melder, die häufig allein auslösen."""

from __future__ import annotations

from custom_components.hauswacht.core.confirmation import FREQUENT_COUNT, LoneTriggerCounter

A, B = "binary_sensor.a", "binary_sensor.b"


def test_lone_trigger_counter() -> None:
    counter = LoneTriggerCounter()
    results = [counter.record(A, i * 600) for i in range(FREQUENT_COUNT)]
    assert results == [False] * (FREQUENT_COUNT - 1) + [True]
    assert counter.record(A, 5000) is False  # Zählung beginnt neu
    rare = LoneTriggerCounter()
    assert [rare.record(B, i * 4000) for i in range(4)] == [False] * 4  # zu selten
