"""Bereiche."""

from __future__ import annotations

from custom_components.hauswacht.core.areas import (
    MAIN_AREA,
    area_options,
    multi_area,
    parse_areas,
    profile_area,
    stale_all_panel,
    stale_area_device,
)

OPTIONS = {
    "areas": {"main": {"name": "Wohnhaus"}, "garage": {"name": "Garage", "icon": "mdi:garage"}},
    "profiles": {
        "nacht": {"name": "Nacht"},
        "garage_zu": {"name": "Garage zu", "area": "garage"},
        "kaputt": {"name": "X", "area": "gibtsnicht"},
    },
    "always_active": {"sensors": ["binary_sensor.tresor"]},
    "reminder_persons": ["person.a"],
}


def test_parse_areas_main_first() -> None:
    areas = parse_areas(OPTIONS)
    assert list(areas) == ["main", "garage"]
    assert areas["main"].name == "Wohnhaus"
    assert areas["garage"].icon == "mdi:garage"
    assert parse_areas({})[MAIN_AREA].name == "Haus"
    assert multi_area(OPTIONS)
    assert not multi_area({})


def test_profile_area_and_view() -> None:
    assert profile_area(OPTIONS, "nacht") == MAIN_AREA
    assert profile_area(OPTIONS, "garage_zu") == "garage"
    assert profile_area(OPTIONS, "kaputt") == MAIN_AREA  # unbekannter Bereich -> Hauptbereich
    main = area_options(OPTIONS, MAIN_AREA)
    assert set(main["profiles"]) == {"nacht", "kaputt"}
    assert "always_active" in main
    garage = area_options(OPTIONS, "garage")
    assert set(garage["profiles"]) == {"garage_zu"}
    assert "always_active" not in garage
    assert "reminder_persons" not in garage


def test_stale_area_device() -> None:
    areas = {"main", "garage"}
    assert not stale_area_device("e1", "e1", areas)  # Hauswacht-Gerät selbst
    assert not stale_area_device("e1_garage", "e1", areas)
    assert stale_area_device("e1_gartenhaus", "e1", areas)
    assert not stale_area_device("e2_gartenhaus", "e1", areas)  # anderer Eintrag


def test_stale_all_panel() -> None:
    assert stale_all_panel("e1_all_panel", "e1", {"main"})
    assert not stale_all_panel("e1_all_panel", "e1", {"main", "garage"})
    assert not stale_all_panel("e1_panel", "e1", {"main"})
