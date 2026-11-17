"""Einrichtungsassistent: Vorschläge, Gruppen, Profile, Zusammenfassung."""

from __future__ import annotations

from typing import Any

from custom_components.hauswacht.core.wizard import (
    Candidate,
    default_night_zones,
    save_groups,
    save_wizard_profile,
    set_entry_doors,
    split_outside_inside,
    status,
    suggest_sensors,
)

DOOR = "binary_sensor.haustuer"
TERRACE = "binary_sensor.terrassentuer"
WINDOW = "binary_sensor.fenster_kueche"
MOTION = "binary_sensor.bewegung_flur"
SMOKE = "binary_sensor.rauch_flur"
CLASSES = {DOOR: "door", TERRACE: "door", WINDOW: "window", MOTION: "motion", SMOKE: "smoke"}


def _candidates() -> list[Candidate]:
    return [
        Candidate(MOTION, "Bewegung Flur", "motion", "Erdgeschoss › Flur"),
        Candidate(SMOKE, "Rauchmelder Flur", "smoke", "Erdgeschoss › Flur"),
        Candidate(WINDOW, "Fenster Küche", "window", "Erdgeschoss › Küche"),
        Candidate(DOOR, "Haustür", "door", ""),
        Candidate("binary_sensor.batterie", "Batterie", "battery", ""),
    ]


def test_suggestions_only_doors_windows_motion_sorted_by_place() -> None:
    found = suggest_sensors(_candidates(), {})
    assert [c.entity_id for c in found] == [MOTION, WINDOW, DOOR]


def test_suggestions_skip_grouped_sensors() -> None:
    options = {"zones": {"aussen": {"name": "Außen", "entities": [WINDOW]}}}
    assert WINDOW not in [c.entity_id for c in suggest_sensors(_candidates(), options)]


def test_split_outside_inside() -> None:
    outside, inside = split_outside_inside([MOTION, DOOR, WINDOW], CLASSES, {})
    assert outside == [WINDOW, DOOR]  # sortiert nach Entität
    assert inside == [MOTION]


def test_save_groups_skips_empty_and_reports_overlap() -> None:
    change = save_groups({}, [("Außen", [DOOR, WINDOW]), ("Innen", [])])
    assert change.ok
    assert change.options is not None
    assert list(change.options["zones"]) == ["aussen"]
    clash = save_groups(change.options, [("Noch mal", [DOOR])])
    assert clash.errors == {"base": "zone_overlap"}


def test_entry_doors() -> None:
    options = set_entry_doors({}, [DOOR, TERRACE, WINDOW], [DOOR], CLASSES)
    # Terrassentür ist keine Eingangstür -> löst sofort aus; Haustür bleibt Vorschlag
    assert options["sensor_types"] == {TERRACE: "other"}
    again = set_entry_doors(options, [DOOR, TERRACE, WINDOW], [DOOR, TERRACE], CLASSES)
    assert again["sensor_types"] == {}
    window_as_entry = set_entry_doors({}, [WINDOW], [WINDOW], CLASSES)
    assert window_as_entry["sensor_types"] == {WINDOW: "door"}


def _with_groups() -> dict[str, Any]:
    change = save_groups({}, [("Außen", [DOOR, WINDOW]), ("Innen", [MOTION])])
    assert change.options is not None
    return change.options


def test_night_defaults_to_groups_without_motion() -> None:
    assert default_night_zones(_with_groups(), CLASSES) == ["aussen"]


def test_wizard_creates_profiles() -> None:
    options = _with_groups()
    away = save_wizard_profile(
        options, "away", {"zones": ["aussen", "innen"], "exit_delay": 60, "entry_delay": 30}
    )
    assert away.ok
    assert away.options is not None
    stored = away.options["profiles"]["abwesend"]
    assert stored["panel_mode"] == "away"
    assert stored["zones"] == ["aussen", "innen"]
    english = save_wizard_profile(options, "night", {"zones": ["aussen"]}, language="en")
    assert english.options is not None
    assert english.options["profiles"]["night"]["name"] == "Night"


def test_wizard_completes_existing_profile_instead_of_duplicate() -> None:
    options = {
        **_with_groups(),
        "profiles": {"n": {"name": "Schlafen", "panel_mode": "night", "exit_delay": 5}},
    }
    change = save_wizard_profile(options, "night", {"zones": ["aussen"]})
    assert change.item_id == "n"
    assert change.options is not None
    assert change.options["profiles"]["n"] == {
        "name": "Schlafen",
        "panel_mode": "night",
        "exit_delay": 5,
        "zones": ["aussen"],
    }


def test_name_clash_without_same_button_gets_suffix() -> None:
    options = {**_with_groups(), "profiles": {"x": {"name": "Nacht", "panel_mode": None}}}
    change = save_wizard_profile(options, "night", {"zones": ["aussen"]})
    assert change.ok
    assert change.options is not None
    assert change.options["profiles"]["nacht_2"]["name"] == "Nacht 2"


def test_status() -> None:
    options = _with_groups()
    change = save_wizard_profile(options, "away", {"zones": ["aussen", "innen"]})
    assert change.options is not None
    result = status(change.options)
    assert result.zones == ["Außen", "Innen"]
    assert result.profiles == [("Abwesend", ["Außen", "Innen"], [])]
    assert not result.recipients
    assert not result.sirens
    assert not result.users
    assert status({"notify_system": ["mobile_app_a"]}).recipients
