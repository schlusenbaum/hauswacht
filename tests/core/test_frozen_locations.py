"""Ortung, die sich nie bewegt (0.64.0b5): exakt gleiche Koordinaten über 24 Stunden."""

from __future__ import annotations

from custom_components.hauswacht.core.away_proof import FROZEN_AFTER, FrozenLocations

GPS = "device_tracker.handy"


def test_unchanged_coordinates_freeze_after_a_day() -> None:
    frozen = FrozenLocations()
    assert frozen.see(GPS, 51.9243091, 8.8408192, 0) is True
    assert frozen.see(GPS, 51.9243091, 8.8408192, 3600) is False  # nichts Neues
    assert frozen.frozen_for(GPS, FROZEN_AFTER - 1) is None
    assert frozen.frozen_for(GPS, FROZEN_AFTER + 10) == FROZEN_AFTER + 10


def test_any_movement_resets() -> None:
    frozen = FrozenLocations()
    frozen.see(GPS, 51.9243091, 8.8408192, 0)
    # Echte Ortungen schwanken: schon ein Meter ist eine Bewegung
    assert frozen.see(GPS, 51.924318, 8.8408192, FROZEN_AFTER) is True
    assert frozen.frozen_for(GPS, FROZEN_AFTER + 10) is None


def test_tiny_rounding_noise_is_no_movement() -> None:
    frozen = FrozenLocations()
    frozen.see(GPS, 51.92430910, 8.84081920, 0)
    assert frozen.see(GPS, 51.92430911, 8.84081921, 10) is False


def test_unknown_entity_is_not_frozen() -> None:
    assert FrozenLocations().frozen_for(GPS, 10 * FROZEN_AFTER) is None


def test_dump_and_load_survive_restart() -> None:
    frozen = FrozenLocations()
    frozen.see(GPS, 51.9, 8.8, 100)
    again = FrozenLocations()
    again.load(frozen.dump())
    assert again.frozen_for(GPS, 100 + FROZEN_AFTER) == FROZEN_AFTER
    # Kaputte Daten werden übergangen
    again.load({"x": "kaputt", 1: [1, 2, 3], "y": [1, 2]})
    assert set(again.seen) == {GPS}
