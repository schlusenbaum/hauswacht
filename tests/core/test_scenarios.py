"""Szenario-Vorschau (ADR 0017): dieselben Bausteine wie im Echtbetrieb, ausgedachte Uhr."""

from __future__ import annotations

from typing import Any

from custom_components.hauswacht.core.advisor import Facts, Measured
from custom_components.hauswacht.core.scenarios import BAD, OK, WARN, scenarios

ANNA = "person.anna"
BEN = "person.ben"
DOOR = "binary_sensor.haustuer"
WINDOW = "binary_sensor.fenster"
NAMES = {ANNA: "Anna", BEN: "Ben", DOOR: "Haustür", WINDOW: "Fenster"}


def _options(*, weak: Any = (), **profile: Any) -> dict[str, Any]:
    base: dict[str, Any] = {"name": "Abwesend", "zones": ["eg"], "entry_delay": 30}
    base.update(profile)
    return {"profiles": {"away": base}, "away_proof_weak": list(weak)}


def _facts(**values: Any) -> Facts:
    values.setdefault("names", NAMES)
    values.setdefault("entry_doors", {"away": (DOOR,)})
    values.setdefault("located", frozenset({ANNA, BEN}))
    return Facts(**values)


def _by_key(found: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {s["key"]: s for s in found}


def test_burglary_door_and_window() -> None:
    found = _by_key(scenarios(_options(), _facts(windows={"away": (WINDOW,)})))
    door = found[f"burglary_door:away:{DOOR}"]
    assert door["result"] == OK
    assert door["summary"] == "Alarm nach 30 s – so soll es sein."
    assert door["title"] == "Einbruch durch die Tür Haustür"
    assert any(step["text"] == "ALARM." for step in door["steps"])
    window = found["burglary_window:away"]
    assert (window["result"], window["summary"]) == (OK, "Sofort Alarm – so soll es sein.")


def test_burglary_without_entry_delay_is_immediate() -> None:
    found = _by_key(scenarios(_options(entry_delay=0), _facts()))
    assert found[f"burglary_door:away:{DOOR}"]["summary"] == "Alarm nach 0 s – so soll es sein."


def test_return_with_door_proof_in_time() -> None:
    back = {"mode": "door", "persons": [ANNA], "window": 5}
    found = _by_key(scenarios(_options(**{"return": back}), _facts()))
    anna = found[f"return:away:{ANNA}"]
    assert anna["result"] == OK
    assert anna["summary"] == "Unscharf, sobald die Tür aufgeht – ohne PIN, ohne Alarm."


def test_return_too_slow_phone_is_false_alarm() -> None:
    """Gemessen: das Handy meldet sich bis zu 48 s nach der Tür – 30 s reichen nicht."""
    back = {"mode": "door", "persons": [ANNA], "window": 5}
    facts = _facts(proof_needed={ANNA: Measured(60, 48, 4)})
    found = _by_key(scenarios(_options(**{"return": back}), facts))
    anna = found[f"return:away:{ANNA}"]
    assert anna["result"] == BAD
    assert anna["summary"].startswith("Fehlalarm nach 30 s")
    # Mit passender Eingangsverzögerung klappt es
    found = _by_key(scenarios(_options(entry_delay=60, **{"return": back}), facts))
    assert found[f"return:away:{ANNA}"]["summary"] == "Unscharf nach 48 s – ohne PIN, ohne Alarm."


def test_return_too_few_measurements_use_default() -> None:
    back = {"mode": "door", "persons": [ANNA], "window": 5}
    facts = _facts(proof_needed={ANNA: Measured(60, 48, 2)})
    found = _by_key(scenarios(_options(**{"return": back}), facts))
    assert found[f"return:away:{ANNA}"]["result"] == OK


def test_return_let_in_stays_armed() -> None:
    back = {"mode": "passage", "persons": [ANNA], "window": 5}
    found = _by_key(scenarios(_options(**{"return": back}), _facts()))
    anna = found[f"return:away:{ANNA}"]
    assert anna["result"] == OK
    assert anna["summary"].startswith("Reingelassen nach 0 s")


def test_return_always_disarms_before_the_door() -> None:
    back = {"mode": "always", "persons": [ANNA], "window": 5}
    found = _by_key(scenarios(_options(**{"return": back}), _facts()))
    assert found[f"return:away:{ANNA}"]["summary"].startswith("Unscharf, schon bevor")


def test_return_auto_only_after_manual_arming_needs_pin() -> None:
    back = {"mode": "auto_only", "persons": [ANNA], "window": 5}
    found = _by_key(scenarios(_options(auto_arm_time="22:00", **{"return": back}), _facts()))
    anna = found[f"return:away:{ANNA}"]
    assert anna["result"] == WARN
    assert "von Hand scharf geschaltet" in anna["summary"]


def test_return_auto_only_after_all_away_disarms() -> None:
    back = {"mode": "auto_only", "persons": [ANNA], "window": 5}
    options = _options(auto_away_persons=[ANNA], auto_away_delay=10, **{"return": back})
    found = _by_key(scenarios(options, _facts()))
    anna = found[f"return:away:{ANNA}"]
    assert anna["result"] == OK
    texts = [s["text"] for s in anna["steps"]]
    assert "Profil Abwesend wird automatisch scharf (alle weg)." in texts


def test_approach_extends_entry_delay() -> None:
    back = {"mode": "door", "persons": [ANNA], "window": 5, "approach_delay": 90}
    facts = _facts(direction=frozenset({ANNA}), proof_needed={ANNA: Measured(60, 48, 4)})
    found = _by_key(scenarios(_options(**{"return": back}), facts))
    anna = found[f"return:away:{ANNA}"]
    assert anna["result"] == OK
    assert any("verlängert auf 90 s" in s["text"] for s in anna["steps"])


def test_all_leave_arms_or_never() -> None:
    options = _options(auto_away_persons=[ANNA, BEN], auto_away_delay=10)
    found = _by_key(scenarios(options, _facts()))
    assert found["all_leave:away"]["result"] == OK
    assert found["phones_sleep:away"]["result"] == OK
    # Ben ohne Ortung und ohne „Tür + Signal“: wird nie scharf
    found = _by_key(scenarios(options, _facts(located=frozenset({ANNA}))))
    leave = found["all_leave:away"]
    assert leave["result"] == BAD
    assert leave["summary"].startswith("Wird nie scharf: Ben")


def test_weak_proof_arms_with_warning_and_short_out() -> None:
    options = _options(weak=(BEN,), auto_away_persons=[ANNA, BEN], auto_away_delay=10)
    found = _by_key(scenarios(options, _facts(located=frozenset({ANNA}))))
    assert found["all_leave:away"]["result"] == WARN
    assert "unsicherem Beleg" in found["all_leave:away"]["summary"]
    # Schlafendes Handy ohne Tür: bleibt unscharf – mit Tür kurz davor: scharf, obwohl Ben da ist
    assert found["phones_sleep:away"]["result"] == OK
    short = found[f"short_out:away:{BEN}"]
    assert short["result"] == WARN
    assert "obwohl Ben zuhause ist" in short["summary"]


def test_sorted_bad_first_and_english() -> None:
    back = {"mode": "door", "persons": [ANNA], "window": 5}
    facts = _facts(proof_needed={ANNA: Measured(60, 48, 4)})
    found = scenarios(_options(**{"return": back}), facts, "en")
    assert found[0]["result"] == BAD
    assert found[0]["title"] == "Anna comes home"
    assert found[0]["summary"].startswith("False alarm after 30 s")


def test_own_trigger_is_not_played_through() -> None:
    entity = "input_boolean.alle_weg"
    options = _options(auto_away_entity=entity, auto_away_persons=[ANNA])
    found = _by_key(scenarios(options, _facts(names={**NAMES, entity: "Alle weg"})))
    leave = found["all_leave:away"]
    assert leave["result"] == WARN
    assert "Alle weg" in leave["summary"]
    assert "phones_sleep:away" not in found


def test_one_is_enough_in_scenarios() -> None:
    """ADR 0021: „eines reicht (nach Tür)“ – Ben ohne Ortung wird erkannt; ohne Tür unsicher."""
    options = {
        **_options(auto_away_persons=[ANNA, BEN], auto_away_delay=10),
        "presence_leave_mode": {BEN: "one"},
    }
    found = _by_key(scenarios(options, _facts(located=frozenset({ANNA}))))
    leave = found["all_leave:away"]
    assert leave["result"] == OK
    assert any("eines reicht" in step["text"] for step in leave["steps"])
    assert found["phones_sleep:away"]["result"] == OK  # schlafendes Handy ohne Tür: nichts
    assert found[f"short_out:away:{BEN}"]["result"] == WARN  # fremde Tür + Handy schläft
    # „nach Tür“ abgeschaltet: ein schlafendes Handy schaltet scharf
    no_door = {
        **_options(auto_away_persons=[BEN], auto_away_delay=10),
        "presence_leave_mode": {BEN: "one"},
        "presence_leave_no_door": [BEN],
    }
    found = _by_key(scenarios(no_door, _facts(located=frozenset({ANNA}))))
    assert found["phones_sleep:away"]["result"] == BAD
    assert found["all_leave:away"]["result"] == WARN
