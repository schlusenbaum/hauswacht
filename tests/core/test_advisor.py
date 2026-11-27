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
    person_uses,
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


def test_frozen_location_is_a_warning() -> None:
    gps = "device_tracker.anna_gps"
    facts = _facts(frozen={ANNA: {gps: 3 * 86400}}, names={**NAMES, gps: "Annas iPhone"})
    found = advise(_options(), facts)
    assert _codes(found) == ["location_frozen"]
    assert found[0]["level"] == WARNING
    assert "seit 3 Tagen" in found[0]["text"]
    assert "Annas iPhone" in found[0]["text"]
    hours = advise(_options(), _facts(frozen={ANNA: {gps: 30 * 3600}}), "en")
    assert "for 30 hours" in hours[0]["text"]


def test_own_trigger_is_a_warning_not_an_error() -> None:
    entity = "input_boolean.alle_weg"
    options = _options(auto_away_persons=[BEN], auto_away_entity=entity)
    found = advise(options, _facts(names={**NAMES, entity: "Alle weg"}))
    assert _codes(found) == ["away_entity", "away_persons_ignored"]
    assert found[0]["level"] == WARNING
    assert "Alle weg" in found[0]["text"]
    assert "„on“" in found[0]["why"]


def test_persons_ignored_with_own_trigger_offers_untick() -> None:
    """ADR 0021: Personen neben eigenem Auslöser werden nicht beachtet – Hinweis mit Vorschlag."""
    entity = "input_boolean.alle_weg"
    options = _options(auto_away_persons=[ANNA, BEN], auto_away_entity=entity)
    found = advise(options, _facts(names={**NAMES, entity: "Alle weg"}))
    tip = next(f for f in found if f["code"] == "away_persons_ignored")
    assert tip["level"] == TIP
    assert "Anna, Ben" in tip["why"]
    fix = tip["fixes"][0]
    assert (fix["path"], fix["op"], fix["value"], fix["weakens"]) == (
        "automation.auto_away_persons",
        "set",
        [],
        False,
    )
    # ohne angehakte Personen kein Hinweis
    assert _codes(advise(_options(auto_away_entity=entity), _facts())) == ["away_entity"]


def test_presence_settings_without_effect() -> None:
    signals = {"homecoming_signals": {ANNA: ["sensor.anna_wlan"]}}
    # Anna steht nirgends -> Hinweis
    found = advise({**_options(), **signals}, _facts())
    assert _codes(found) == ["presence_unused"]
    # nur in einem Profil mit eigenem Auslöser -> wirkt trotzdem nirgends
    trigger = _options(auto_away_persons=[ANNA], auto_away_entity="input_boolean.x")
    assert "presence_unused" in _codes(advise({**trigger, **signals}, _facts()))
    # in „Scharf, wenn alle weg“ -> kein Hinweis
    used = _options(auto_away_persons=[ANNA])
    assert "presence_unused" not in _codes(
        advise({**used, **signals}, _facts(located=frozenset({ANNA})))
    )


def test_one_is_enough_counts_as_detectable() -> None:
    """„eines reicht (nach Tür)“: auch ohne Ortung als weg erkennbar – kein „nie weg“."""
    options = {**_options(auto_away_persons=[BEN]), "presence_leave_mode": {BEN: "one"}}
    assert "away_never" not in _codes(advise(options, _facts()))


def test_person_uses() -> None:
    options = {
        "profiles": {
            "away": {"name": "Abwesend", "auto_away_persons": [ANNA]},
            "night": {
                "name": "Nacht",
                "auto_away_persons": [ANNA],
                "auto_away_entity": "input_boolean.x",
            },
        },
        "homecoming_observe": True,
        "homecoming_persons": [ANNA],
    }
    assert person_uses(options, ANNA) == [
        ("away", "away"),
        ("away_ignored", "night"),
        ("observe", None),
    ]
    assert person_uses(options, BEN) == []


def test_exit_detection_findings() -> None:
    """ADR 0014: ohne Melder im Haus Warnung, ohne Eingangsverzögerung Fehler."""
    on = {"enabled": True, "wait": 3}
    found = advise(_options(exit_detect=on), _facts())
    warn = next(f for f in found if f["code"] == "exit_no_inside")
    assert warn["level"] == WARNING
    assert "3 min" in warn["text"]
    inside = {**on, "inside": ["binary_sensor.treppe"]}
    assert "exit_no_inside" not in _codes(advise(_options(exit_detect=inside), _facts()))
    no_delay = advise(_options(exit_detect=on, entry_delay=0), _facts())
    assert _codes(no_delay) == ["exit_no_delay"]
    assert no_delay[0]["level"] == ERROR
