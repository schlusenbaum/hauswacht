"""Erschütterungsmelder (ADR 0010 Teil B)."""

from __future__ import annotations

import pytest

from custom_components.hauswacht.core.sensor_types import SensorType, default_type
from custom_components.hauswacht.core.tilt import effective_types
from custom_components.hauswacht.core.vibration import (
    DEFAULT_COUNT,
    DEFAULT_WINDOW,
    VibrationCounter,
    VibrationRule,
    VibrationSource,
    delete_vibration_source,
    parse_vibration_sources,
    position,
    rule_for,
    rule_for_zone_id,
    save_vibration_source,
    save_zone_rule,
)

SOURCE = VibrationSource(entity_id="sensor.fenster_vibration", threshold=30)


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        ("0", "off"),
        ("29.9", "off"),
        ("30", "on"),
        ("120", "on"),
        ("abc", "unavailable"),
        ("unavailable", "unavailable"),
        ("unknown", "unknown"),
        (None, None),
    ],
)
def test_position(state: str | None, expected: str | None) -> None:
    assert position(SOURCE, state) == expected


def test_default_type_and_effective_types() -> None:
    assert default_type("binary_sensor.erschuetterung", "vibration") is SensorType.VIBRATION
    options = save_vibration_source({}, "sensor.v", threshold=30)
    assert effective_types(options)["sensor.v"] is SensorType.VIBRATION
    options["sensor_types"] = {"sensor.v": "window"}
    assert effective_types(options)["sensor.v"] is SensorType.WINDOW


def test_save_parse_delete() -> None:
    options = {"zones": {"fenster": {"name": "Fenster", "entities": ["sensor.v", "x.y"]}}}
    options = save_vibration_source(options, "sensor.v", threshold=12.5)
    assert parse_vibration_sources(options)["sensor.v"].threshold == 12.5
    removed = delete_vibration_source(options, "sensor.v")
    assert parse_vibration_sources(removed) == {}
    assert removed["zones"]["fenster"]["entities"] == ["x.y"]


def test_zone_rule_defaults_and_bounds() -> None:
    options = {"zones": {"fenster": {"name": "Fenster", "entities": ["sensor.v"]}}}
    assert rule_for(options, "sensor.v") == VibrationRule(DEFAULT_COUNT, DEFAULT_WINDOW)
    options = save_zone_rule(options, "fenster", count=2, window=60)
    assert rule_for_zone_id(options, "fenster") == VibrationRule(2, 60)
    assert rule_for(options, "sensor.v") == VibrationRule(2, 60)
    # Unsinnige Werte -> Standard
    options = save_zone_rule(options, "fenster", count=99, window=1)
    assert rule_for_zone_id(options, "fenster") == VibrationRule(DEFAULT_COUNT, DEFAULT_WINDOW)
    assert rule_for_zone_id(options, "gibtsnicht") == VibrationRule()


def test_counter_single_report_triggers() -> None:
    counter = VibrationCounter()
    assert counter.record("a", 0.0, VibrationRule(1, 60)) == (True, 1)


def test_counter_two_within_window() -> None:
    counter = VibrationCounter()
    rule = VibrationRule(2, 60)
    assert counter.record("a", 0.0, rule) == (False, 1)
    assert counter.record("a", 30.0, rule) == (True, 2)
    # danach wieder von vorn
    assert counter.record("a", 31.0, rule) == (False, 1)


def test_counter_window_expires_and_counts_per_sensor() -> None:
    counter = VibrationCounter()
    rule = VibrationRule(2, 60)
    assert counter.record("a", 0.0, rule) == (False, 1)
    assert counter.record("b", 10.0, rule) == (False, 1)  # anderer Melder zählt nicht mit
    assert counter.record("a", 61.0, rule) == (False, 1)  # erste Meldung zu alt
    assert counter.record("a", 100.0, rule) == (True, 2)
    counter.reset()
    assert counter.record("b", 101.0, rule) == (False, 1)
