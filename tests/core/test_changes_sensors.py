"""Melder bearbeiten über die Logikschicht (Einstellungsseite, ADR 0011 Stufe 2)."""

from __future__ import annotations

from typing import Any

from custom_components.hauswacht.core.changes.sensors import (
    apply_types,
    remove_group,
    remove_strength,
    remove_tilt,
    save_always,
    save_group,
    save_strength,
    save_tilt,
)

DOOR = "binary_sensor.haustuer"
SHOCK = "binary_sensor.erschuetterung"
CLASSES = {DOOR: "door", SHOCK: "vibration"}


def _options() -> dict[str, Any]:
    return {
        "zones": {"aussen": {"name": "Außen", "entities": [DOOR], "label": None}},
        "profiles": {"weg": {"name": "Weg", "zones": ["aussen"]}},
    }


def test_new_group_with_types_and_rule() -> None:
    change = save_group(
        _options(),
        None,
        {
            "name": "Fenster",
            "entities": [SHOCK],
            "types": {SHOCK: "vibration"},
            "vibration_count": 2,
            "vibration_window": 60,
        },
        labels={},
        device_classes=CLASSES,
    )
    assert change.ok
    assert change.options is not None
    assert change.item_id == "fenster"
    zone = change.options["zones"]["fenster"]
    assert zone["entities"] == [SHOCK]
    assert (zone["vibration_count"], zone["vibration_window"]) == (2, 60)
    # Vorschlag "Erschütterung" wird nicht extra gespeichert
    assert SHOCK not in change.options["sensor_types"]


def test_type_deviation_stored_and_reset() -> None:
    change = save_group(
        _options(),
        "aussen",
        {"name": "Außen", "entities": [DOOR], "types": {DOOR: "window"}},
        labels={},
        device_classes=CLASSES,
    )
    assert change.options is not None
    assert change.options["sensor_types"] == {DOOR: "window"}
    reset = apply_types(change.options, {DOOR: "door"}, CLASSES)
    assert reset["sensor_types"] == {}


def test_group_errors() -> None:
    assert save_group(_options(), None, {"name": ""}, labels={}, device_classes={}).errors == {
        "name": "zone_name_required"
    }
    overlap = save_group(
        _options(), None, {"name": "Neu", "entities": [DOOR]}, labels={}, device_classes=CLASSES
    )
    assert overlap.errors == {"base": "zone_overlap"}
    assert overlap.details["conflicts"] == {DOOR: "Außen"}
    bad_type = save_group(
        _options(),
        "aussen",
        {"name": "Außen", "entities": [DOOR], "types": {DOOR: "banane"}},
        labels={},
        device_classes=CLASSES,
    )
    assert bad_type.errors == {"types": "unknown_type"}
    bad_count = save_group(
        _options(),
        "aussen",
        {"name": "Außen", "entities": [DOOR], "vibration_count": 9},
        labels={},
        device_classes=CLASSES,
    )
    assert bad_count.errors == {"vibration_count": "out_of_range"}


def test_remove_group_also_from_profiles() -> None:
    change = remove_group(_options(), "aussen")
    assert change.options is not None
    assert change.options["zones"] == {}
    assert change.options["profiles"]["weg"]["zones"] == []
    assert remove_group(_options(), "gibtsnicht").errors == {"base": "unknown_group"}


def test_tilt_save_places_in_group_and_removes() -> None:
    change = save_tilt(
        _options(),
        {"entity": "sensor.f", "closed": ["closed"], "tilted": ["tilted"], "group": "aussen"},
        labels={},
    )
    assert change.options is not None
    assert "sensor.f" in change.options["zones"]["aussen"]["entities"]
    assert save_tilt(_options(), {"entity": "sensor.f", "closed": []}, labels={}).errors == {
        "closed": "tilt_no_closed"
    }
    overlap = save_tilt(
        _options(), {"entity": "sensor.f", "closed": ["a"], "tilted": ["A"]}, labels={}
    )
    assert overlap.errors == {"tilted": "tilt_overlap"}
    removed = remove_tilt(change.options, "sensor.f")
    assert removed.options is not None
    assert "sensor.f" not in removed.options["zones"]["aussen"]["entities"]


def test_strength_save_and_remove() -> None:
    change = save_strength(_options(), {"entity": "sensor.v", "threshold": "30"}, labels={})
    assert change.options is not None
    assert change.options["vibration_sources"]["sensor.v"]["threshold"] == 30.0
    assert save_strength(_options(), {"entity": "sensor.v"}, labels={}).errors == {
        "threshold": "required"
    }
    removed = remove_strength(change.options, "sensor.v")
    assert removed.options is not None
    assert removed.options["vibration_sources"] == {}


def test_always_keeps_siren_settings() -> None:
    options = {**_options(), "always_active": {"sensors": ["x.a"], "sirens_enabled": True}}
    change = save_always(options, zones=["aussen", "weg"], sensors=["binary_sensor.wasser"])
    assert change.options is not None
    always = change.options["always_active"]
    assert always == {
        "sensors": ["binary_sensor.wasser"],
        "sirens_enabled": True,
        "zones": ["aussen"],
    }
