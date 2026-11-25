"""Einrichten nach Zielen (ADR 0017, 0.65): Vorschläge, Plan, Überschreiben, Sirenen."""

from __future__ import annotations

from typing import Any

from custom_components.hauswacht.core.advisor import Facts, Measured
from custom_components.hauswacht.core.goals import (
    AWAY,
    NIGHT,
    NIGHT_RETURN,
    RETURN,
    Household,
    build,
    suggestions,
)
from custom_components.hauswacht.core.goals import (
    GARAGE as GARAGE_GOAL,
)

ANNA = "person.anna"
BEN = "person.ben"
SIREN = "siren.flur"
APP = "notify.mobile_app_anna"


def _options(**extra: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "zones": {
            "aussen": {"name": "Außen", "entities": ["binary_sensor.tuer"]},
            "innen": {"name": "Innen", "entities": ["binary_sensor.bwm"]},
        },
        "profiles": {"home": {"name": "Zuhause", "panel_mode": "home", "zones": ["aussen"]}},
        "sirens": [],
    }
    base.update(extra)
    return base


def _hh(**facts: Any) -> Household:
    facts.setdefault("located", frozenset({ANNA}))
    facts.setdefault("names", {ANNA: "Anna", BEN: "Ben"})
    return Household(
        persons=(ANNA, BEN),
        facts=Facts(**facts),
        motion_groups=frozenset({"innen"}),
        sirens=(SIREN,),
        notify=(APP,),
        names={SIREN: "Sirene Flur", APP: "Handy Anna"},
    )


def _answers(options: dict[str, Any], hh: Household, *goals: str, **extra: Any) -> dict[str, Any]:
    answers = suggestions(options, hh)
    answers["goals"] = list(goals)
    answers.update(extra)
    return answers


def test_suggestions_from_household() -> None:
    options = _options()
    answers = suggestions(options, _hh())
    assert answers["goals"] == []
    # Nachts ohne Gruppen mit Bewegungsmeldern
    assert answers[NIGHT]["zones"] == ["aussen"]
    assert answers[AWAY]["zones"] == ["aussen", "innen"]
    # Nur Personen, die als weg erkannt werden können
    assert answers[AWAY]["persons"] == [ANNA]
    assert answers[RETURN] == {"persons": [ANNA], "mode": "door"}


def test_weak_person_counts_as_detectable() -> None:
    options = _options(away_proof_weak=[BEN])
    assert suggestions(options, _hh())[AWAY]["persons"] == [ANNA, BEN]


def test_new_profiles_for_all_goals() -> None:
    options = _options()
    hh = _hh(proof_needed={ANNA: Measured(50, 38, 3)})
    answers = _answers(options, hh, NIGHT, AWAY, RETURN, NIGHT_RETURN, sirens=[SIREN], notify=[APP])
    answers[NIGHT]["arm_time"] = "22:30"
    plan, after = build(options, hh, answers)
    assert plan["errors"] == []
    assert after is not None
    assert plan["profiles"] == ["nacht", "abwesend"]
    night = after["profiles"]["nacht"]
    assert night["panel_mode"] == "night"
    assert night["zones"] == ["aussen"]
    assert night["auto_arm_time"] == "22:30"
    assert night["return"]["mode"] == "passage"
    away = after["profiles"]["abwesend"]
    assert away["panel_mode"] == "away"
    assert away["auto_away_persons"] == [ANNA]
    assert away["return"]["mode"] == "door"
    # Eingangsverzögerung aus der Messung (Türbeleg von Anna: 50 s)
    assert away["entry_delay"] == 50
    # Sirene nur eingetragen, nie freigegeben
    assert after["sirens"] == [SIREN]
    assert not after.get("sirens_hardware_enabled")
    assert away["sirens"] == [SIREN]
    assert away["notify"] == [APP]
    # Neues anlegen braucht keine Bestätigung
    assert plan["needs_confirm"] is False
    assert any("nur eingetragen" in n for n in plan["notes"])
    # Nichts verändert an den Eingaben
    assert "nacht" not in options["profiles"]


def test_existing_profile_is_extended_and_overwrites_are_marked() -> None:
    options = _options(
        profiles={
            "away": {
                "name": "Abwesend",
                "panel_mode": "away",
                "zones": ["aussen"],
                "entry_delay": 30,
                "auto_arm_time": "08:00",
                "return": {"mode": "auto_only", "persons": [ANNA], "window": 5},
            }
        }
    )
    hh = _hh(proof_needed={ANNA: Measured(50, 38, 3)})
    answers = _answers(options, hh, AWAY, RETURN)
    answers[AWAY]["zones"] = ["aussen", "innen"]
    answers[RETURN]["mode"] = "door"
    plan, after = build(options, hh, answers)
    assert after is not None
    away = after["profiles"]["away"]
    # Die übrige Automatik bleibt (Uhrzeit), „alle weg“ kommt dazu
    assert away["auto_arm_time"] == "08:00"
    assert away["auto_away_persons"] == [ANNA]
    assert away["zones"] == ["aussen", "innen"]
    (step,) = plan["steps"]
    changes = {c["label"]: c for c in step["changes"]}
    assert changes["Meldergruppen"]["overwrite"] is False  # nur ergänzt
    assert changes["Bei Rückkehr"]["overwrite"] is True  # auto_only -> Türbeleg
    assert changes["Bei Rückkehr"]["before"] == "Unscharf, nur wenn automatisch scharf"
    assert changes["Eingangsverzögerung"]["weakens"] is True  # 30 -> 50 s
    assert plan["needs_confirm"] is True
    assert step["title"] == "Profil Abwesend"


def test_unchanged_answers_change_nothing() -> None:
    options = _options(
        profiles={
            "away": {
                "name": "Abwesend",
                "panel_mode": "away",
                "zones": ["aussen", "innen"],
                "auto_away_persons": [ANNA],
                "auto_away_delay": 15,
            }
        }
    )
    hh = _hh()
    plan, after = build(options, hh, _answers(options, hh, AWAY))
    assert after is not None
    assert plan["steps"][0]["changes"] == []
    assert plan["needs_confirm"] is False


def test_errors_and_undetectable_note() -> None:
    options = _options()
    hh = _hh()
    plan, after = build(options, hh, _answers(options, hh))
    assert after is None
    assert plan["errors"] == ["Bitte mindestens ein Ziel wählen."]
    answers = _answers(options, hh, AWAY)
    answers[AWAY]["persons"] = []
    plan, after = build(options, hh, answers)
    assert after is None
    assert any("mindestens eine Person" in e for e in plan["errors"])
    # Ben ohne Ortung: geht, aber mit deutlichem Hinweis
    answers[AWAY]["persons"] = [ANNA, BEN]
    plan, after = build(options, hh, answers)
    assert after is not None
    assert any(n.startswith("Ben kann nie als weg erkannt werden") for n in plan["notes"])


def test_new_night_profile_needs_groups_even_for_night_return_only() -> None:
    options = _options()
    hh = _hh()
    answers = _answers(options, hh, NIGHT_RETURN)
    answers[NIGHT]["zones"] = []
    plan, after = build(options, hh, answers)
    assert after is None
    assert any("Meldergruppe" in e for e in plan["errors"])


def test_invalid_time_and_unknown_items_are_ignored_safely() -> None:
    options = _options()
    hh = _hh()
    answers = _answers(options, hh, NIGHT, sirens=["siren.rauchmelder"], notify=["notify.x"])
    answers[NIGHT]["arm_time"] = "25:99"
    plan, after = build(options, hh, answers)
    assert after is None
    assert any("Uhrzeit" in e for e in plan["errors"])
    answers[NIGHT]["arm_time"] = None
    plan, after = build(options, hh, answers)
    assert after is not None
    # Nicht angebotene Sirenen (z. B. Rauchmelder) und Empfänger werden nie übernommen
    assert after["sirens"] == []
    assert "sirens" not in after["profiles"]["nacht"]


def test_english() -> None:
    options = _options()
    hh = _hh()
    plan, after = build(options, hh, _answers(options, hh, AWAY), "en")
    assert after is not None
    assert plan["steps"][0]["title"] == "New profile Away"
    assert "away" in after["profiles"]


# --- Türen, Fenster, Garage, Rauchmelder (0.65.0b2) ------------------------------------------

TUER = "binary_sensor.tuer"
BWM = "binary_sensor.bwm"
TERRASSE = "binary_sensor.terrasse"
KUECHE = "binary_sensor.fenster_kueche"
GARAGE_TOR = "binary_sensor.garagentor"
FLUR_BWM = "binary_sensor.bwm_flur"
SMOKE = "siren.rauchmelder_diele"


def _sensors_hh(**extra: Any) -> Household:
    from custom_components.hauswacht.core.goals import SensorInfo  # noqa: PLC0415

    sensors = (
        SensorInfo(TUER, "Haustür", "door", "door", "EG › Flur", "aussen"),
        SensorInfo(TERRASSE, "Terrassentür", "door", "door", "EG › Wohnen", "aussen"),
        SensorInfo(BWM, "Bewegung Flur", "motion", "motion", "EG › Flur", "innen"),
        SensorInfo(KUECHE, "Fenster Küche", "window", "window", "EG › Küche", None),
        SensorInfo(FLUR_BWM, "Bewegung OG", "motion", "motion", "OG › Flur", None),
        SensorInfo(GARAGE_TOR, "Garagentor", "door", "door", "", None),
    )
    names = {s.entity_id: s.name for s in sensors}
    return Household(
        persons=(ANNA,),
        facts=Facts(located=frozenset({ANNA}), names={ANNA: "Anna", **names}),
        motion_groups=frozenset({"innen"}),
        sirens=(SIREN, SMOKE),
        smoke=frozenset({SMOKE}),
        notify=(APP,),
        names={SIREN: "Sirene Flur", SMOKE: "Rauchmelder Diele", APP: "Handy Anna", **names},
        sensors=sensors,
        **extra,
    )


def _sensor_options() -> dict[str, Any]:
    return _options(
        zones={
            "aussen": {"name": "Außen", "entities": [TUER, TERRASSE]},
            "innen": {"name": "Innen", "entities": [BWM]},
        }
    )


def test_sensor_suggestions_put_free_sensors_into_existing_groups() -> None:
    options = _sensor_options()
    hh = _sensors_hh()
    answers = suggestions(options, hh)
    assert answers["sensors"] == {
        "add": [],
        "outside": "aussen",
        "inside": "innen",
        "entry_doors": [TUER, TERRASSE, GARAGE_TOR],
    }
    answers["goals"] = [AWAY]
    answers["sensors"]["add"] = [KUECHE, FLUR_BWM, GARAGE_TOR]
    plan, after = build(options, hh, answers)
    assert after is not None, plan
    assert sorted(after["zones"]["aussen"]["entities"]) == sorted(
        [TUER, TERRASSE, KUECHE, GARAGE_TOR]
    )
    assert sorted(after["zones"]["innen"]["entities"]) == sorted([BWM, FLUR_BWM])
    # Nur ergänzt: keine Bestätigung nötig
    assert plan["needs_confirm"] is False
    assert plan["steps"][0]["title"] == "Türen, Fenster und Bewegungsmelder"


def test_new_groups_without_existing_ones() -> None:
    options = _options(zones={})
    hh = _sensors_hh()
    from dataclasses import replace  # noqa: PLC0415

    hh = replace(hh, sensors=tuple(replace(s, group=None) for s in hh.sensors))
    answers = suggestions(options, hh)
    assert answers["sensors"]["outside"] == "new"
    assert "@outside" in answers[NIGHT]["zones"]
    assert "@inside" in answers[AWAY]["zones"]
    answers["goals"] = [NIGHT, AWAY]
    answers["sensors"]["add"] = [s.entity_id for s in hh.sensors]
    plan, after = build(options, hh, answers)
    assert after is not None, plan
    zones = after["zones"]
    assert zones["aussen"]["name"] == "Außen"
    assert zones["innen"]["name"] == "Innen"
    # Nachts nur Außen, abwesend beides – mit den echten IDs statt der Platzhalter
    assert after["profiles"]["nacht"]["zones"] == ["aussen"]
    assert after["profiles"]["abwesend"]["zones"] == ["aussen", "innen"]


def test_entry_doors_patio_triggers_immediately() -> None:
    options = _sensor_options()
    hh = _sensors_hh()
    answers = suggestions(options, hh)
    answers["goals"] = [AWAY]
    answers["sensors"]["add"] = []
    answers["sensors"]["entry_doors"] = [TUER]  # Terrassentür keine Eingangstür
    plan, after = build(options, hh, answers)
    assert after is not None, plan
    assert after["sensor_types"] == {TERRASSE: "other"}
    row = next(c for c in plan["steps"][0]["changes"] if c["label"].startswith("Eingangstüren"))
    assert row["overwrite"] is True  # Terrassentür fällt weg
    assert row["weakens"] is False  # sofort auslösend ist strenger


def test_making_a_watched_window_an_entry_door_weakens() -> None:
    options = _sensor_options()
    options["zones"]["aussen"]["entities"].append(KUECHE)
    hh = _sensors_hh()
    from dataclasses import replace  # noqa: PLC0415

    hh = replace(
        hh,
        sensors=tuple(
            replace(s, group="aussen") if s.entity_id == KUECHE else s for s in hh.sensors
        ),
    )
    answers = suggestions(options, hh)
    answers["goals"] = [AWAY]
    answers["sensors"]["add"] = []
    answers["sensors"]["entry_doors"] = [TUER, TERRASSE, KUECHE]
    plan, after = build(options, hh, answers)
    assert after is not None, plan
    assert after["sensor_types"] == {KUECHE: "door"}
    assert plan["needs_confirm"] is True


def test_missing_entry_answer_changes_no_types() -> None:
    options = _sensor_options()
    hh = _sensors_hh()
    answers = suggestions(options, hh)
    answers["goals"] = [AWAY]
    del answers["sensors"]["entry_doors"]
    plan, after = build(options, hh, answers)
    assert after is not None, plan
    assert after.get("sensor_types", {}) == {}


def test_garage_separately() -> None:
    options = _sensor_options()
    hh = _sensors_hh()
    answers = suggestions(options, hh)
    answers["goals"] = [GARAGE_GOAL]
    answers["garage"] = {"sensors": [GARAGE_TOR], "away": True}
    options["profiles"]["away"] = {"name": "Abwesend", "panel_mode": "away", "zones": ["aussen"]}
    plan, after = build(options, hh, answers)
    assert after is not None, plan
    assert after["zones"]["garage"]["entities"] == [GARAGE_TOR]
    # Das Garagentor ist nicht zusätzlich in „Außen“
    assert GARAGE_TOR not in after["zones"]["aussen"]["entities"]
    garage = after["profiles"]["garage"]
    assert garage["zones"] == ["garage"]
    assert garage["panel_mode"] == "custom"
    # Auch scharf, wenn alle weg: das vorhandene Abwesend-Profil bekommt die Gruppe
    assert after["profiles"]["away"]["zones"] == ["aussen", "garage"]
    assert set(plan["profiles"]) == {"garage", "away"}


def test_garage_moves_sensor_out_of_its_group() -> None:
    options = _sensor_options()
    hh = _sensors_hh()
    answers = suggestions(options, hh)
    answers["goals"] = [GARAGE_GOAL]
    answers["sensors"]["add"] = []
    answers["garage"] = {"sensors": [TERRASSE], "away": False}
    plan, after = build(options, hh, answers)
    assert after is not None, plan
    assert after["zones"]["aussen"]["entities"] == [TUER]
    assert after["zones"]["garage"]["entities"] == [TERRASSE]
    assert plan["needs_confirm"] is True  # Gruppe Außen verliert einen Melder
    assert any("wechselt aus der Gruppe Außen" in n for n in plan["notes"])
    # Nie eine Gruppe leer räumen
    answers["garage"] = {"sensors": [BWM], "away": False}
    plan, after = build(options, hh, answers)
    assert after is None
    assert any("keinen Melder mehr" in e for e in plan["errors"])


def test_smoke_detector_siren_only_registered_with_note() -> None:
    options = _sensor_options()
    hh = _sensors_hh()
    answers = suggestions(options, hh)
    answers["goals"] = [NIGHT]
    answers["sirens"] = [SMOKE]
    plan, after = build(options, hh, answers)
    assert after is not None, plan
    assert after["sirens"] == [SMOKE]
    assert not after.get("sirens_hardware_enabled")
    assert after["profiles"]["nacht"]["sirens"] == [SMOKE]
    assert any(n.startswith("Rauchmelder als Einbruchsirene") for n in plan["notes"])
