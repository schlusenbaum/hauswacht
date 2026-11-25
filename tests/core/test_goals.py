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
