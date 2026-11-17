"""Einstellungsregeln: Meldergruppen (gemeinsam für Dialog und Assistent)."""

from __future__ import annotations

from typing import Any

from custom_components.hauswacht.core.changes.zones import delete_zone, save_zone

DOOR = "binary_sensor.haustuer"
WINDOW = "binary_sensor.fenster_kueche"
MOTION = "binary_sensor.bewegung_flur"


def _options() -> dict[str, Any]:
    return {
        "zones": {"aussen": {"name": "Außen", "entities": [DOOR, WINDOW], "label": None}},
        "profiles": {"night": {"name": "Nacht", "zones": ["aussen", "innen"]}},
    }


def test_new_zone_gets_id_from_name() -> None:
    options = _options()
    change = save_zone(options, None, {"name": " Innen ", "entities": [MOTION, MOTION]})
    assert change.ok
    assert change.item_id == "innen"
    assert change.options is not None
    assert change.options["zones"]["innen"] == {
        "name": "Innen",
        "entities": [MOTION],
        "label": None,
    }
    # Eingabe bleibt unverändert
    assert "innen" not in options["zones"]


def test_same_name_gets_unique_id() -> None:
    change = save_zone(_options(), None, {"name": "Außen", "entities": [MOTION]})
    assert change.item_id == "aussen_2"


def test_name_and_members_required() -> None:
    assert save_zone(_options(), None, {"name": "", "entities": [MOTION]}).errors == {
        "name": "zone_name_required"
    }
    empty = save_zone(_options(), None, {"name": "Leer"})
    assert empty.errors == {"base": "zone_empty"}
    assert empty.options is None
    assert save_zone(_options(), None, {"name": "Per Label", "label": "keller"}).ok


def test_sensor_belongs_to_one_zone_only() -> None:
    change = save_zone(_options(), None, {"name": "Innen", "entities": [MOTION, DOOR]})
    assert not change.ok
    assert change.errors == {"base": "zone_overlap"}
    assert change.details["conflicts"] == {DOOR: "Außen"}


def test_overlap_via_label() -> None:
    labels = {"erdgeschoss": frozenset({WINDOW})}
    change = save_zone(
        _options(), None, {"name": "EG", "label": "erdgeschoss"}, entities_by_label=labels
    )
    assert change.details["conflicts"] == {WINDOW: "Außen"}


def test_editing_keeps_id_and_ignores_own_members() -> None:
    change = save_zone(_options(), "aussen", {"name": "Hülle", "entities": [DOOR]})
    assert change.ok
    assert change.options is not None
    assert change.options["zones"]["aussen"]["name"] == "Hülle"
    assert change.options["zones"]["aussen"]["entities"] == [DOOR]


def test_delete_removes_zone_from_profiles() -> None:
    options = _options()
    change = delete_zone(options, "aussen")
    assert change.options is not None
    assert change.options["zones"] == {}
    assert change.options["profiles"]["night"]["zones"] == ["innen"]
    assert options["profiles"]["night"]["zones"] == ["aussen", "innen"]
