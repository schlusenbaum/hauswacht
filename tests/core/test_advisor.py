"""Gemeinsame Prüfung (ADR 0017): Befunde und Vorschläge."""

from __future__ import annotations

from typing import Any

from custom_components.hauswacht.core.advisor import (
    ERROR,
    MIN_SAMPLES,
    OP_ADD,
    OP_REMOVE,
    OP_SET,
    TIP,
    WARNING,
    Facts,
    Measured,
    advise,
    errors,
    find_fix,
    patch,
)

ANNA = "person.anna"
BEN = "person.ben"
DOOR = "binary_sensor.haustuer"
NAMES = {ANNA: "Anna", BEN: "Ben", DOOR: "Haustür"}


def _options(**profile: Any) -> dict[str, Any]:
    base = {"name": "Abwesend", "zones": ["eg"], "entry_delay": 30}
    base.update(profile)
    return {"profiles": {"away": base}}


def _facts(**values: Any) -> Facts:
    values.setdefault("names", NAMES)
    values.setdefault("entry_doors", {"away": (DOOR,)})
    return Facts(**values)


def _codes(found: list[dict[str, Any]]) -> list[str]:
    return [f["code"] for f in found]


def test_nothing_set_nothing_found() -> None:
    assert advise(_options(), _facts()) == []


def test_all_away_with_unlocatable_person_never_arms() -> None:
    options = _options(auto_away_persons=[ANNA, BEN])
    found = advise(options, _facts(located=frozenset({BEN})))
    assert _codes(found) == ["away_never"]
    finding = found[0]
    assert finding["level"] == ERROR
    assert finding["profile"] == "away"
    assert "Anna" in finding["text"]
    assert "Abwesend" in finding["text"]
    remove, weak = finding["fixes"]
    assert remove == {
        "label": "Anna aus „Scharf, wenn alle weg“ nehmen",
        "profile": "away",
        "path": "automation.auto_away_persons",
        "op": "remove",
        "value": ANNA,
        "current": None,
        "weakens": False,
    }
    # Unsicherer Beleg: allgemeine Einstellung, muss ausdrücklich bestätigt werden
    assert weak["profile"] is None
    assert weak["path"] == "away_proof_weak"
    assert weak["op"] == "add"
    assert weak["weakens"] is True


def test_weak_proof_counts_as_detectable() -> None:
    options = _options(auto_away_persons=[ANNA])
    options["away_proof_weak"] = [ANNA]
    assert advise(options, _facts()) == []


def test_weak_proof_with_location_is_a_tip() -> None:
    options = _options()
    options["away_proof_weak"] = [ANNA]
    found = advise(options, _facts(located=frozenset({ANNA})))
    assert _codes(found) == ["weak_not_needed"]
    assert found[0]["level"] == TIP
    assert found[0]["profile"] is None
    assert found[0]["fixes"][0]["op"] == "remove"
    assert found[0]["fixes"][0]["weakens"] is False


def test_return_person_without_location_never_returns() -> None:
    options = _options(**{"return": {"mode": "door", "persons": [ANNA]}})
    found = advise(options, _facts())
    assert _codes(found) == ["return_never"]
    assert found[0]["level"] == WARNING
    assert found[0]["fixes"][0]["path"] == "return.persons"


def test_auto_only_without_automation() -> None:
    options = _options(**{"return": {"mode": "auto_only", "persons": [ANNA]}})
    found = advise(options, _facts(located=frozenset({ANNA})))
    assert _codes(found) == ["auto_only_without_automation"]
    assert found[0]["level"] == ERROR
    assert found[0]["fixes"] == []
    # Mit Uhrzeit hat das Profil eine Automatik
    options["profiles"]["away"]["auto_arm_time"] = "22:00"
    assert advise(options, _facts(located=frozenset({ANNA}))) == []


def test_door_modes_need_an_entry_door() -> None:
    for mode in ("door", "passage"):
        options = _options(**{"return": {"mode": mode, "persons": [ANNA]}})
        found = advise(options, _facts(located=frozenset({ANNA}), entry_doors={"away": ()}))
        assert _codes(found) == ["return_without_door"]
        assert found[0]["level"] == ERROR
    # „always“ braucht keine Tür
    options = _options(**{"return": {"mode": "always", "persons": [ANNA]}})
    assert advise(options, _facts(located=frozenset({ANNA}), entry_doors={})) == []


def test_approach_without_direction_signal() -> None:
    back = {"mode": "door", "persons": [ANNA], "approach_delay": 120}
    options = _options(**{"return": back})
    found = advise(options, _facts(located=frozenset({ANNA})))
    assert _codes(found) == ["approach_without_direction"]
    fix = found[0]["fixes"][0]
    assert (fix["path"], fix["op"], fix["value"], fix["weakens"]) == (
        "return.approach_delay",
        "set",
        0,
        False,
    )
    with_direction = _facts(located=frozenset({ANNA}), direction=frozenset({ANNA}))
    assert advise(options, with_direction) == []


def test_entry_delay_shorter_than_measured() -> None:
    measured = {DOOR: Measured(seconds=45, longest=36, count=MIN_SAMPLES)}
    found = advise(_options(entry_delay=30), _facts(entry_needed=measured))
    assert _codes(found) == ["entry_too_short"]
    finding = found[0]
    assert "36 s" in finding["why"]
    assert "Haustür" in finding["why"]
    fix = finding["fixes"][0]
    # Längere Eingangsverzögerung = später Alarm: muss bestätigt werden
    assert (fix["path"], fix["value"], fix["weakens"]) == ("entry_delay", 45, True)
    assert fix["current"] == 30  # für die Vorschau „vorher → nachher“
    assert advise(_options(entry_delay=45), _facts(entry_needed=measured)) == []


def test_too_few_measurements_say_nothing() -> None:
    measured = {DOOR: Measured(seconds=45, longest=36, count=MIN_SAMPLES - 1)}
    assert advise(_options(entry_delay=30), _facts(entry_needed=measured)) == []


def test_measured_door_outside_profile_does_not_count() -> None:
    measured = {"binary_sensor.keller": Measured(seconds=90, longest=70, count=5)}
    assert advise(_options(entry_delay=30), _facts(entry_needed=measured)) == []


def test_door_proof_needs_long_enough_entry_delay() -> None:
    options = _options(entry_delay=30, **{"return": {"mode": "door", "persons": [ANNA]}})
    proof = {ANNA: Measured(seconds=60, longest=48, count=4)}
    found = advise(options, _facts(located=frozenset({ANNA}), proof_needed=proof))
    assert _codes(found) == ["proof_too_short"]
    assert "48 s" in found[0]["why"]
    assert found[0]["fixes"][0]["value"] == 60
    # Bei „always“ entscheidet die Tür nicht – kein Befund
    options["profiles"]["away"]["return"]["mode"] = "always"
    assert advise(options, _facts(located=frozenset({ANNA}), proof_needed=proof)) == []


def test_order_errors_first_and_errors_filter() -> None:
    options = _options(auto_away_persons=[ANNA], **{"return": {"mode": "door", "persons": [BEN]}})
    options["away_proof_weak"] = [BEN]
    found = advise(options, _facts(located=frozenset({BEN})))
    assert [f["level"] for f in found] == [ERROR, TIP]
    assert _codes(errors(found)) == ["away_never"]


def test_english_texts() -> None:
    options = _options(auto_away_persons=[ANNA])
    found = advise(options, _facts(), "en")
    assert found[0]["text"].startswith("Profile Abwesend: Anna can never")
    assert found[0]["fixes"][0]["label"] == "Remove Anna from “arm when all away”"


def test_find_fix_only_current_suggestions() -> None:
    options = _options(auto_away_persons=[ANNA])
    found = advise(options, _facts())
    wanted = {
        "profile": "away",
        "path": "automation.auto_away_persons",
        "op": "remove",
        "value": ANNA,
        "label": "egal",
    }
    finding, fix = find_fix(found, wanted) or ({}, {})
    assert finding["code"] == "away_never"
    assert fix["weakens"] is False
    # Etwas anderes als vorgeschlagen: nicht gefunden
    assert find_fix(found, {**wanted, "value": BEN}) is None
    assert find_fix(found, {**wanted, "path": "entry_delay", "op": "set"}) is None
    # Behoben: der alte Vorschlag greift nicht mehr
    assert find_fix(advise(options, _facts(located=frozenset({ANNA}))), wanted) is None


def test_patch_set_add_remove() -> None:
    form: dict[str, Any] = {"entry_delay": 30, "automation": {"auto_away_persons": [ANNA, BEN]}}
    patch(form, "entry_delay", OP_SET, 45)
    patch(form, "automation.auto_away_persons", OP_REMOVE, ANNA)
    patch(form, "return.persons", OP_ADD, BEN)
    patch(form, "return.persons", OP_ADD, BEN)  # nicht doppelt
    assert form == {
        "entry_delay": 45,
        "automation": {"auto_away_persons": [BEN]},
        "return": {"persons": [BEN]},
    }
