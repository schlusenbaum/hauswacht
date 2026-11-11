"""Auslöseregeln: Abfolgen von Meldern, Verschachtelung, unless, Bedingungen."""

from __future__ import annotations

from typing import Any

import pytest

from custom_components.hauswacht.core.rules import (
    Rule,
    RuleError,
    RuleResult,
    build_engine,
    describe_rule,
    from_editable,
    migrate_zone_confirmation,
    parse_rule,
    parse_rules,
    profile_findings,
    rule_members,
    step_form,
    step_from_form,
    to_editable,
    validate_rule,
    wizard_editable,
)
from custom_components.hauswacht.core.sensors import Zone

DOOR = "binary_sensor.tuer_hinten"
BW1 = "binary_sensor.bw1_keller"
BW2 = "binary_sensor.bw2_keller"
BUERO = "binary_sensor.tuer_buero"
WINDOW = "binary_sensor.fenster_kueche"
PM = "binary_sensor.pm_waschkueche"
FLUR = "binary_sensor.bwm_flur"

ZONES = {"keller": Zone("keller", "Keller", frozenset({BW1, BW2, PM}))}


def s(entity: str) -> dict[str, str]:
    return {"sensor": entity}


def g(zone: str) -> dict[str, str]:
    return {"group": zone}


def _rule(rule_id: str, *steps: dict[str, Any], **extra: Any) -> Rule:
    return parse_rule(rule_id, {"name": rule_id, "steps": list(steps), **extra})


def _engine(*rules: Rule):  # type: ignore[no-untyped-def]
    return build_engine(rules, ZONES, {})


def test_door_then_cellar_fires() -> None:
    rule = _rule("r", {"any": [s(DOOR)], "within": 120}, {"any": [g("keller")]})
    engine = _engine(rule)
    assert engine.record(DOOR, 0) == []
    assert engine.record(BW1, 60) == [rule]


def test_door_only_or_cellar_only_does_not_fire() -> None:
    rule = _rule("r", {"any": [s(DOOR)], "within": 120}, {"any": [g("keller")]})
    engine = _engine(rule)
    assert engine.record(BW1, 0) == []
    assert engine.record(BW2, 5) == []
    assert engine.record(DOOR, 10) == []  # Reihenfolge falsch


def test_window_expires() -> None:
    rule = _rule("r", {"any": [s(DOOR)], "within": 30}, {"any": [s(BW1)]})
    engine = _engine(rule)
    engine.record(DOOR, 0)
    assert engine.record(BW1, 31) == []


def test_three_steps_in_order() -> None:
    rule = _rule(
        "r", {"any": [s(DOOR)], "within": 30}, {"any": [s(BW1)], "within": 60}, {"any": [s(BUERO)]}
    )
    engine = _engine(rule)
    engine.record(DOOR, 0)
    assert engine.record(BUERO, 10) == []
    engine.record(BW1, 20)
    assert engine.record(BUERO, 70) == [rule]


def test_all_step_any_order() -> None:
    rule = _rule("r", {"any": [s(DOOR)], "within": 60}, {"all": [s(BW1), s(BUERO)]})
    engine = _engine(rule)
    engine.record(DOOR, 0)
    assert engine.record(BUERO, 10) == []
    assert engine.record(BW1, 20) == [rule]


def test_group_stands_for_its_sensors() -> None:
    every = _rule("all", {"all": [g("keller")], "within": 60})
    engine = _engine(every)
    engine.record(BW1, 0)
    engine.record(BW2, 1)
    assert engine.record(PM, 2) == [every]  # alle drei Kellermelder


def test_count_needs_different_sensors() -> None:
    rule = _rule("r", {"count": 2, "of": [g("keller")], "within": 120})
    engine = _engine(rule)
    assert engine.record(BW1, 0) == []
    assert engine.record(BW1, 10) == []
    assert engine.record(PM, 20) == [rule]


def test_nested_expression() -> None:
    # Keller ODER (Flur UND Büro)
    rule = _rule(
        "r",
        {"any": [s(DOOR)], "within": 120},
        {"any": [g("keller"), {"all": [s(FLUR), s(BUERO)]}]},
    )
    engine = _engine(rule)
    engine.record(DOOR, 0)
    assert engine.record(FLUR, 10) == []
    assert engine.record(BUERO, 20) == [rule]
    engine.reset()
    engine.record(DOOR, 100)
    assert engine.record(PM, 110) == [rule]


def test_unless_blocks_only_shortly_before_step_one() -> None:
    rule = _rule(
        "r",
        {"any": [s(WINDOW)], "within": 60},
        {"any": [g("keller")]},
        unless={"any": [s(FLUR)], "before": 300},
    )
    engine = _engine(rule)
    engine.record(FLUR, 0)  # jemand drinnen unterwegs
    engine.record(WINDOW, 100)  # … öffnet das Fenster
    assert engine.record(BW1, 110) == []
    engine.record(WINDOW, 500)  # Flur ist jetzt 500 s her
    assert engine.record(BW1, 510) == [rule]


def test_unless_blocked_until() -> None:
    rule = _rule(
        "r",
        {"any": [s(WINDOW)], "within": 60},
        {"any": [s(BW1)]},
        unless={"any": [s(FLUR)], "before": 300},
    )
    engine = _engine(rule)
    assert engine.blocked_until(rule, 0) is None
    engine.record(FLUR, 10)
    assert engine.blocked_until(rule, 20) == 310
    assert engine.blocked_until(rule, 400) is None


def test_progress_and_deadline() -> None:
    rule = _rule("r", {"any": [s(DOOR)], "within": 120}, {"any": [g("keller")]})
    engine = _engine(rule)
    assert engine.progress(0) == {}
    engine.record(DOOR, 10)
    progress = engine.progress(20)["r"]
    assert (progress.done, progress.total, progress.deadline) == (1, 2, 130)
    assert progress.first_sensor == DOOR
    assert engine.progress(131) == {}


def test_unrelated_sensor_ignored() -> None:
    rule = _rule("r", {"any": [s(DOOR)], "within": 120}, {"any": [g("keller")]})
    engine = _engine(rule)
    assert engine.record("binary_sensor.fremd", 0) == []
    assert engine.triggers == []
    assert engine.watched() == {DOOR, BW1, BW2, PM}


def test_legacy_storage_still_works() -> None:
    rules = parse_rules(
        {
            "rules": {
                "alt": {
                    "name": "Alt",
                    "steps": [
                        {"sensors": [DOOR], "within": 120},
                        {"zones": ["keller"], "mode": "count", "count": 2},
                    ],
                    "result": "entry_delay",
                },
                "kaputt": "nein",
                "falsch": {"steps": [{"any": "keinliste"}]},
            }
        }
    )
    assert set(rules) == {"alt"}
    rule = rules["alt"]
    assert rule.result is RuleResult.ENTRY_DELAY
    engine = _engine(rule)
    engine.record(DOOR, 0)
    engine.record(BW1, 10)
    assert engine.record(BW2, 20) == [rule]


def test_validate_rule_errors() -> None:
    bad = _rule(
        "bad",
        {"any": [s(DOOR), s(BW1)], "within": 30},
        {"any": [s(BW1)]},
        {"count": 5, "of": [g("keller")]},
    )
    codes = {(f.code, f.step) for f in validate_rule(bad, ZONES, {})}
    assert ("rule_same_sensor_next_step", 2) in codes
    assert ("rule_count_too_high", 3) in codes
    empty = _rule("empty", {"any": [g("gibtsnicht")]})
    assert validate_rule(empty, ZONES, {})[0].code == "rule_step_empty"
    assert validate_rule(_rule("none"), ZONES, {})[0].code == "rule_no_steps"


def test_parse_errors_name_the_place() -> None:
    with pytest.raises(RuleError, match="Schritt 2"):
        parse_rule("x", {"steps": [{"any": [s(DOOR)]}, {"oder": []}]})
    with pytest.raises(RuleError, match="Bedingung 1"):
        parse_rule("x", {"steps": [{"any": [s(DOOR)]}], "conditions": [{"time": {}}]})
    with pytest.raises(RuleError, match="unless"):
        parse_rule("x", {"steps": [{"any": [s(DOOR)]}], "unless": {"any": [s(FLUR)]}})


def test_profile_findings() -> None:
    redundant = _rule("redundant", {"any": [s(DOOR)], "within": 30}, {"any": [g("keller")]})
    short = _rule("kurz", {"any": [s(WINDOW)], "within": 60}, {"any": [s(BW1)]})
    long = _rule(
        "lang",
        {"any": [s(WINDOW)], "within": 30},
        {"any": [s(BW1)], "within": 30},
        {"any": [s(BUERO)]},
    )
    overlap = _rule(
        "overlap",
        {"any": [s(WINDOW)], "within": 30},
        {"any": [s(BW1)]},
        unless={"any": [s(WINDOW)], "before": 3600},
    )
    findings = profile_findings(frozenset({DOOR}), [redundant, short, long, overlap], ZONES, {})
    codes = {(f.code, f.rule, f.detail) for f in findings}
    assert ("rule_redundant_single", "redundant", "") in codes
    assert ("rule_contained", "lang", "kurz") in codes
    assert ("rule_unless_overlaps", "overlap", "") in codes
    assert ("rule_unless_long", "overlap", "3600") in codes


def test_rule_members() -> None:
    rule = _rule("r", {"any": [s(DOOR)], "within": 30}, {"any": [g("keller"), s(FLUR)]})
    assert rule_members(rule, ZONES, {}) == [frozenset({DOOR}), frozenset({BW1, BW2, PM, FLUR})]


def test_editable_roundtrip_with_group_names() -> None:
    rule = _rule(
        "r",
        {"any": [s(DOOR)], "within": 120},
        {"any": [g("keller"), {"all": [s(FLUR), s(BUERO)]}]},
        result="entry_delay",
        unless={"any": [g("keller")], "before": 300},
        conditions=[{"time": {"after": "22:00", "before": "06:00"}}],
    )
    shown = to_editable(rule, lambda z: ZONES[z].name)
    assert shown["steps"][1]["any"][0] == {"group": "Keller"}
    assert shown["unless"] == {"any": [{"group": "Keller"}], "before": 300}
    back, stored = from_editable(shown, ZONES, "r")
    assert back == rule
    assert stored["steps"][1]["any"][0] == {"group": "keller"}


def test_from_editable_errors() -> None:
    with pytest.raises(RuleError, match="Meldergruppe 'Kelle'"):
        from_editable({"name": "x", "steps": [{"any": [{"group": "Kelle"}]}]}, ZONES)
    with pytest.raises(RuleError, match="Unbekannte"):
        from_editable({"name": "x", "steps": [{"any": [s(DOOR)]}], "foo": 1}, ZONES)
    with pytest.raises(RuleError, match="name"):
        from_editable({"steps": [{"any": [s(DOOR)]}]}, ZONES)
    with pytest.raises(RuleError, match="Schritt 1"):
        from_editable({"name": "x", "steps": [{"any": [s(DOOR)], "wann": 3}]}, ZONES)


def test_wizard_forms() -> None:
    flat = _rule("r", {"count": 2, "of": [s(DOOR), g("keller")], "within": 90})
    form = step_form(flat.steps[0])
    assert form == {
        "sensors": [DOOR],
        "zones": ["keller"],
        "mode": "count",
        "count": 2,
        "within": 90,
    }
    assert step_from_form(form or {}) == {
        "count": 2,
        "of": [s(DOOR), g("keller")],
        "within": 90,
    }
    nested = _rule("n", {"any": [s(DOOR), {"all": [s(BW1), s(BW2)]}]})
    assert step_form(nested.steps[0]) is None
    assert wizard_editable(flat)
    assert not wizard_editable(nested)


def test_describe_rule() -> None:
    rule = _rule(
        "r",
        {"any": [s(DOOR), s(BUERO)], "within": 120},
        {"any": [g("keller")]},
        {"all": [s(BW1), s(PM)], "within": 30},
        result="entry_delay",
        unless={"any": [s(FLUR)], "before": 300},
        conditions=[{"time": {"after": "22:00", "before": "06:00"}}],
    )
    names = {DOOR: "Tür hinten", BUERO: "Tür Büro", BW1: "BW 1", PM: "PM Waschküche", FLUR: "Flur"}
    text = describe_rule(rule, names.__getitem__, lambda z: z.title())
    assert text == (
        "eine(r) von Tür hinten / Tür Büro, dann innerhalb von 120 s Meldergruppe Keller, "
        "dann innerhalb von 60 s BW 1 und PM Waschküche (alle, beliebige Reihenfolge) "
        "→ Eingangsverzögerung, dann Alarm – nicht, wenn in den 300 s davor Flur "
        "– nur wenn 22:00–06:00"
    )


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
    assert new["profiles"]["nacht"]["rules"] == ["bestaetigung_keller"]
    rule = parse_rules(new)["bestaetigung_keller"]
    engine = build_engine([rule], {"keller": Zone("keller", "Keller", frozenset({BW1, BW2}))}, {})
    engine.record(BW1, 0)
    assert engine.record(BW2, 10) == [rule]
