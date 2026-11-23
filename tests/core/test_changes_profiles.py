"""Einstellungsregeln: Alarmprofile (gemeinsam für Dialog und Assistent)."""

from __future__ import annotations

from typing import Any

from custom_components.hauswacht.core.changes.profiles import (
    automation_from_input,
    delete_profile,
    save_profile,
)

DOOR = "binary_sensor.haustuer"
MOTION = "binary_sensor.bewegung_flur"


def _options() -> dict[str, Any]:
    return {
        "zones": {
            "aussen": {"name": "Außen", "entities": [DOOR]},
            "innen": {"name": "Innen", "entities": [MOTION]},
        },
        "rules": {},
        "sirens": ["siren.flur"],
        "profiles": {
            "night": {
                "name": "Nacht",
                "panel_mode": "night",
                "zones": ["aussen"],
                "exit_delay": 0,
                "future_key": "bleibt",
            }
        },
    }


def _form(**changes: Any) -> dict[str, Any]:
    """Das ganze Formular des Einstellungsdialogs."""
    form: dict[str, Any] = {
        "name": "Abwesend",
        "icon": "mdi:shield",
        "panel_mode": "away",
        "exit_delay": 60,
        "entry_delay": 30,
        "reaction_time": 180,
        "zones": ["aussen", "innen", "gibt_es_nicht"],
        "excluded": [],
        "rules": [],
        "open_policy": "refuse",
        "unavailable_policy": "warn",
        "max_alarm_cycles": 3,
        "tamper_triggers_alarm": True,
        "sirens": ["siren.flur", "siren.unbekannt"],
        "siren_tone": "burglar",
        "siren_volume": "high",
        "silent": False,
        "notify": ["mobile_app_anna"],
        "speakers": [],
        "automation": {},
        "arm_on_close": {},
    }
    form.update(changes)
    return form


def test_new_profile_from_full_form() -> None:
    change = save_profile(_options(), None, _form())
    assert change.ok
    assert change.item_id == "abwesend"
    assert change.options is not None
    stored = change.options["profiles"]["abwesend"]
    assert stored["zones"] == ["aussen", "innen"]  # unbekannte Gruppe fällt weg
    assert stored["sirens"] == ["siren.flur"]  # nur eingetragene Sirenen
    assert stored["panel_mode"] == "away"
    assert stored["exit_delay"] == 60
    assert "auto_arrival_mode" not in stored  # gehört seit 0.61 zu „Bei Rückkehr“
    assert stored["arm_on_close"]["enabled"] is False


def test_full_form_missing_lists_mean_empty() -> None:
    form = _form(name="Nacht", panel_mode="night")
    del form["zones"]
    change = save_profile(_options(), "night", form)
    assert change.options is not None
    stored = change.options["profiles"]["night"]
    assert stored["zones"] == []
    assert stored["future_key"] == "bleibt"  # unbekannte Schlüssel bleiben


def test_partial_changes_only_given_fields() -> None:
    change = save_profile(_options(), "night", {"name": "Nacht", "entry_delay": 20}, partial=True)
    assert change.ok
    assert change.options is not None
    stored = change.options["profiles"]["night"]
    assert stored["entry_delay"] == 20
    assert stored["zones"] == ["aussen"]
    assert stored["exit_delay"] == 0
    assert "auto_arrival_mode" not in stored
    assert "arm_on_close" not in stored


def test_partial_new_profile_with_few_fields() -> None:
    change = save_profile(
        _options(), None, {"name": "Urlaub", "zones": ["aussen", "innen"]}, partial=True
    )
    assert change.options is not None
    assert change.options["profiles"]["urlaub"] == {"name": "Urlaub", "zones": ["aussen", "innen"]}


def test_validation() -> None:
    assert save_profile(_options(), None, _form(name=" ")).errors == {
        "name": "profile_name_required"
    }
    assert save_profile(_options(), None, _form(name="nacht")).errors == {
        "name": "profile_name_taken"
    }
    assert save_profile(_options(), None, _form(panel_mode="night")).errors == {
        "panel_mode": "panel_mode_taken"
    }
    excluded = _form(zones=["aussen"], excluded=[MOTION])
    assert save_profile(_options(), None, excluded).errors == {"excluded": "excluded_not_in_groups"}
    back = _form(**{"return": {"mode": "door", "persons": []}})
    assert save_profile(_options(), None, back).errors == {"return": "return_needs_persons"}
    # eigener Name und eigener Knopf beim Ändern erlaubt
    assert save_profile(_options(), "night", _form(name="Nacht", panel_mode="night")).ok


def test_panel_mode_free_in_other_area() -> None:
    options = _options()
    options["areas"] = {"wohnung": {"name": "Einliegerwohnung"}}
    change = save_profile(options, None, _form(panel_mode="night", area="wohnung"))
    assert change.ok
    assert change.options is not None
    assert change.options["profiles"]["abwesend"]["area"] == "wohnung"


def test_automation_form_no_longer_writes_arrival() -> None:
    auto = automation_from_input({"auto_arrival_mode": "door", "auto_away_persons": ["p"]})
    assert "auto_arrival_mode" not in auto
    assert "auto_disarm_on_arrival" not in auto


def test_return_saved_from_form_and_dialog_keeps_it() -> None:
    form = _form(**{"return": {"mode": "passage", "persons": ["person.a"], "window": 7}})
    change = save_profile(_options(), "night", form)
    assert change.options is not None
    stored = change.options["profiles"]["night"]
    assert stored["return"] == {
        "mode": "passage",
        "persons": ["person.a"],
        "window": 7,
        "approach_delay": 0,
        "approach_valid": 15,
    }
    # Der Dialog kennt „Bei Rückkehr“ nicht – die Einstellung bleibt
    again = save_profile(change.options, "night", _form(name="Nacht"))
    assert again.options is not None
    assert again.options["profiles"]["night"]["return"]["mode"] == "passage"


def test_delete_profile() -> None:
    options = _options()
    change = delete_profile(options, "night")
    assert change.options is not None
    assert change.options["profiles"] == {}
    assert "night" in options["profiles"]


def test_partial_schedule_keeps_other_automation() -> None:
    options = _options()
    options["profiles"]["night"]["auto_away_persons"] = ["person.anna"]
    change = save_profile(
        options, "night", {"name": "Nacht", "auto_schedule": "schedule.nacht"}, partial=True
    )
    assert change.options is not None
    stored = change.options["profiles"]["night"]
    assert stored["auto_schedule"] == "schedule.nacht"
    assert stored["auto_away_persons"] == ["person.anna"]


def test_full_form_stores_schedule() -> None:
    change = save_profile(_options(), None, _form(automation={"auto_schedule": "schedule.x"}))
    assert change.options is not None
    assert change.options["profiles"]["abwesend"]["auto_schedule"] == "schedule.x"
