"""Bedingungen für Auslöseregeln."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

import pytest

from custom_components.hauswacht.core.conditions import (
    ConditionError,
    all_met,
    check,
    entities,
    evaluate,
)

STATES: dict[str, tuple[str, Mapping[str, Any]]] = {
    "person.niklas": ("Schule", {}),
    "person.anna": ("home", {}),
    "zone.schule": ("1", {"friendly_name": "Schule"}),
    "sensor.temp": ("22.5", {}),
    "climate.bad": ("heat", {"temperature": 21}),
    "switch.urlaub": ("on", {}),
    "sensor.kaputt": ("unavailable", {}),
}
NIGHT = datetime(2026, 11, 11, 23, 30)  # Mittwoch
DAY = datetime(2026, 11, 11, 12, 0)


def get(entity: str) -> tuple[str, Mapping[str, Any]] | None:
    return STATES.get(entity)


def test_time_over_midnight_and_weekdays() -> None:
    night = {"time": {"after": "22:00", "before": "06:00"}}
    assert evaluate(night, get, NIGHT) is True
    assert evaluate(night, get, DAY) is False
    assert evaluate({"time": {"weekdays": ["wed"]}}, get, DAY) is True
    assert evaluate({"time": {"weekdays": ["sat", "sun"]}}, get, DAY) is False


def test_person_zone_state_numeric() -> None:
    assert evaluate({"person": {"entity": "person.niklas", "in": "zone.schule"}}, get, DAY)
    assert evaluate({"person": {"entity": "person.niklas", "in": "not_home"}}, get, DAY)
    assert not evaluate({"person": {"entity": "person.anna", "in": "not_home"}}, get, DAY)
    assert evaluate({"state": {"entity": "switch.urlaub", "is": ["on", "auto"]}}, get, DAY)
    assert evaluate({"numeric": {"entity": "sensor.temp", "above": 20, "below": 25}}, get, DAY)
    assert not evaluate({"numeric": {"entity": "sensor.temp", "below": 20}}, get, DAY)
    attr = {"numeric": {"entity": "climate.bad", "attribute": "temperature", "above": 20}}
    assert evaluate(attr, get, DAY)


def test_logic_and_unknown_is_safe_side() -> None:
    unknown = {"numeric": {"entity": "sensor.kaputt", "above": 1}}
    assert evaluate(unknown, get, DAY) is None
    assert evaluate({"not": unknown}, get, DAY) is None
    assert evaluate({"or": [unknown, {"state": {"entity": "switch.urlaub", "is": "on"}}]}, get, DAY)
    # im Zweifel gilt die Regel
    assert all_met([{"not": unknown}], get, DAY) is True
    assert all_met([{"state": {"entity": "switch.urlaub", "is": "off"}}], get, DAY) is False
    assert all_met([], get, DAY) is True


def test_check_and_entities() -> None:
    nested = {
        "and": [
            {"person": {"entity": "person.niklas", "in": "zone.schule"}},
            {"not": {"state": {"entity": "switch.urlaub", "is": "on"}}},
        ]
    }
    check(nested)
    assert entities(nested) == {"person.niklas", "zone.schule", "switch.urlaub"}
    for bad in (
        {"time": {}},
        {"time": {"after": "25:99x"}},
        {"numeric": {"entity": "sensor.t"}},
        {"person": {"entity": "sensor.x", "in": "home"}},
        {"person": {"entity": "person.x", "in": "keller"}},
        {"state": {"entity": "switch.x"}},
        {"wetter": {}},
        {"and": []},
    ):
        with pytest.raises(ConditionError):
            check(bad)
