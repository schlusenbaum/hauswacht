"""Regeln: Abfolgen von Meldern."""

from __future__ import annotations

from custom_components.hauswacht.core.rules import (
    Rule,
    RuleResult,
    Step,
    StepMode,
    build_engine,
    describe_rule,
    migrate_zone_confirmation,
    parse_rules,
    profile_findings,
    rule_members,
    validate_rule,
)
from custom_components.hauswacht.core.sensors import Zone

DOOR = "binary_sensor.tuer_hinten"
BW1 = "binary_sensor.bw1_keller"
BW2 = "binary_sensor.bw2_keller"
BUERO = "binary_sensor.tuer_buero"
WINDOW = "binary_sensor.fenster_kueche"
PM = "binary_sensor.pm_waschkueche"

ZONES = {"keller": Zone("keller", "Keller", frozenset({BW1, BW2, PM}))}


def _rule(rule_id: str, *steps: Step, result: RuleResult = RuleResult.ALARM) -> Rule:
    return Rule(rule_id=rule_id, name=rule_id, steps=steps, result=result)


def _engine(*rules: Rule):  # type: ignore[no-untyped-def]
    return build_engine(rules, ZONES, {})


def test_door_then_cellar_fires() -> None:
    rule = _rule("r", Step(sensors=frozenset({DOOR}), within=120), Step(zones=("keller",)))
    engine = _engine(rule)
    assert engine.record(DOOR, 0) == []
    assert engine.record(BW1, 60) == [rule]


def test_door_only_or_cellar_only_does_not_fire() -> None:
    rule = _rule("r", Step(sensors=frozenset({DOOR}), within=120), Step(zones=("keller",)))
    engine = _engine(rule)
    assert engine.record(BW1, 0) == []
    assert engine.record(BW2, 5) == []  # zwei Kellermelder ohne Tür: kein Alarm
    assert engine.record(DOOR, 10) == []  # Reihenfolge falsch


def test_window_expires() -> None:
    rule = _rule("r", Step(sensors=frozenset({DOOR}), within=30), Step(sensors=frozenset({BW1})))
    engine = _engine(rule)
    engine.record(DOOR, 0)
    assert engine.record(BW1, 31) == []


def test_three_steps_in_order() -> None:
    rule = _rule(
        "r",
        Step(sensors=frozenset({DOOR}), within=30),
        Step(sensors=frozenset({BW1}), within=60),
        Step(sensors=frozenset({BUERO})),
    )
    engine = _engine(rule)
    engine.record(DOOR, 0)
    assert engine.record(BUERO, 10) == []  # Büro vor Keller zählt nicht
    engine.record(BW1, 20)
    assert engine.record(BUERO, 70) == [rule]


def test_all_step_any_order() -> None:
    rule = _rule(
        "r",
        Step(sensors=frozenset({DOOR}), within=60),
        Step(sensors=frozenset({BW1, BUERO}), mode=StepMode.ALL),
    )
    engine = _engine(rule)
    engine.record(DOOR, 0)
    assert engine.record(BUERO, 10) == []
    assert engine.record(BW1, 20) == [rule]


def test_count_needs_different_sensors() -> None:
    rule = _rule("r", Step(zones=("keller",), mode=StepMode.COUNT, count=2, within=120))
    engine = _engine(rule)
    assert engine.record(BW1, 0) == []
    assert engine.record(BW1, 10) == []  # derselbe Melder zählt nicht doppelt
    assert engine.record(PM, 20) == [rule]


def test_count_spread_limit() -> None:
    rule = _rule("r", Step(zones=("keller",), mode=StepMode.COUNT, count=2, within=60))
    engine = _engine(rule)
    engine.record(BW1, 0)
    assert engine.record(BW2, 61) == []


def test_rules_are_or_combined() -> None:
    r1 = _rule("r1", Step(sensors=frozenset({DOOR}), within=30), Step(sensors=frozenset({BW1})))
    r2 = _rule("r2", Step(sensors=frozenset({DOOR}), within=60), Step(sensors=frozenset({PM})))
    r3 = _rule("r3", Step(sensors=frozenset({WINDOW}), within=60), Step(sensors=frozenset({BW1})))
    engine = _engine(r1, r2, r3)
    engine.record(DOOR, 0)
    assert engine.record(PM, 45) == [r2]
    engine.reset()
    engine.record(WINDOW, 100)
    assert engine.record(BW1, 110) == [r3]


def test_progress_and_deadline() -> None:
    rule = _rule("r", Step(sensors=frozenset({DOOR}), within=120), Step(zones=("keller",)))
    engine = _engine(rule)
    assert engine.progress(0) == {}
    engine.record(DOOR, 10)
    progress = engine.progress(20)["r"]
    assert (progress.done, progress.total, progress.deadline) == (1, 2, 130)
    assert progress.first_sensor == DOOR
    assert engine.progress(131) == {}


def test_unrelated_sensor_ignored() -> None:
    rule = _rule("r", Step(sensors=frozenset({DOOR}), within=120), Step(zones=("keller",)))
    engine = _engine(rule)
    assert engine.record("binary_sensor.fremd", 0) == []
    assert engine.triggers == []
    assert engine.watched() == {DOOR, BW1, BW2, PM}


def test_parse_rules() -> None:
    rules = parse_rules(
        {
            "rules": {
                "tuer_keller": {
                    "name": "Tür, dann Keller",
                    "steps": [
                        {"sensors": [DOOR], "within": 120},
                        {"zones": ["keller"], "mode": "count", "count": 2},
                        {"sensors": []},  # leerer Schritt wird ignoriert
                    ],
                    "result": "entry_delay",
                },
                "kaputt": "nein",
            }
        }
    )
    assert set(rules) == {"tuer_keller"}
    rule = rules["tuer_keller"]
    assert rule.result is RuleResult.ENTRY_DELAY
    assert len(rule.steps) == 2
    assert rule.steps[0].within == 120
    assert rule.steps[1].mode is StepMode.COUNT


def test_validate_rule_errors() -> None:
    bad = _rule(
        "bad",
        Step(sensors=frozenset({DOOR, BW1}), within=30),
        Step(sensors=frozenset({BW1})),
        Step(zones=("keller",), mode=StepMode.COUNT, count=5),
    )
    codes = {(f.code, f.step) for f in validate_rule(bad, rule_members(bad, ZONES, {}))}
    assert ("rule_same_sensor_next_step", 2) in codes
    assert ("rule_count_too_high", 3) in codes
    empty = _rule("empty", Step(zones=("gibtsnicht",)))
    assert validate_rule(empty, rule_members(empty, ZONES, {}))[0].code == "rule_step_empty"
    assert validate_rule(_rule("none"), [])[0].code == "rule_no_steps"


def test_profile_findings() -> None:
    redundant = _rule(
        "redundant", Step(sensors=frozenset({DOOR}), within=30), Step(zones=("keller",))
    )
    short = _rule(
        "kurz", Step(sensors=frozenset({WINDOW}), within=60), Step(sensors=frozenset({BW1}))
    )
    long = _rule(
        "lang",
        Step(sensors=frozenset({WINDOW}), within=30),
        Step(sensors=frozenset({BW1}), within=30),
        Step(sensors=frozenset({BUERO})),
    )
    members = {r.rule_id: rule_members(r, ZONES, {}) for r in (redundant, short, long)}
    findings = profile_findings(frozenset({DOOR}), [redundant, short, long], members)
    codes = {(f.code, f.rule, f.detail) for f in findings}
    assert ("rule_redundant_single", "redundant", "") in codes
    assert ("rule_contained", "lang", "kurz") in codes


def test_migrate_zone_confirmation() -> None:
    options = {
        "zones": {
            "keller": {
                "name": "Keller",
                "entities": [BW1, BW2],
                "confirm": True,
                "confirm_window": 90,
            },
            "aussen": {"name": "Außen", "entities": [DOOR]},
        },
        "profiles": {
            "nacht": {"name": "Nacht", "zones": ["aussen", "keller"]},
            "zuhause": {"name": "Zuhause", "zones": ["aussen"]},
        },
    }
    new = migrate_zone_confirmation(options)
    assert "confirm" not in new["zones"]["keller"]
    rule = new["rules"]["bestaetigung_keller"]
    assert rule["steps"] == [{"zones": ["keller"], "mode": "count", "count": 2, "within": 90}]
    assert new["profiles"]["nacht"]["zones"] == ["aussen"]
    assert new["profiles"]["nacht"]["rules"] == ["bestaetigung_keller"]
    assert "rules" not in new["profiles"]["zuhause"]
    assert migrate_zone_confirmation({"zones": {}})["rules"] == {}


def test_describe_rule() -> None:
    rule = _rule(
        "r",
        Step(sensors=frozenset({DOOR, BUERO}), within=120),
        Step(zones=("keller",)),
        Step(sensors=frozenset({BW1, PM}), mode=StepMode.ALL, within=30),
        result=RuleResult.ENTRY_DELAY,
    )
    names = {DOOR: "Tür hinten", BUERO: "Tür Büro", BW1: "BW 1", PM: "PM Waschküche"}
    text = describe_rule(rule, names.__getitem__, lambda z: z.title())
    assert text == (
        "eine(r) von Tür Büro / Tür hinten, dann innerhalb von 120 s Meldergruppe Keller, "
        "dann innerhalb von 60 s BW 1 und PM Waschküche (alle, beliebige Reihenfolge) "
        "→ Eingangsverzögerung, dann Alarm"
    )
    count = _rule("c", Step(zones=("keller",), mode=StepMode.COUNT, count=2))
    assert describe_rule(count, str, str, "en") == (
        "at least 2 different of group keller → alarm immediately"
    )
