"""Einstellungsregeln: Auslöseregeln anlegen, ändern, löschen (Einstellungsseite)."""

from __future__ import annotations

from typing import Any

from custom_components.hauswacht.core.changes.rules import check_rule, delete_rule, save_rule

DOOR = "binary_sensor.haustuer"
CELLAR = "binary_sensor.keller_bewegung"
LABELS: dict[str, frozenset[str]] = {}


def _options() -> dict[str, Any]:
    return {
        "zones": {"keller": {"name": "Keller", "entities": [CELLAR]}},
        "profiles": {"away": {"name": "Abwesend", "rules": []}, "night": {"name": "Nacht"}},
        "rules": {
            "alt": {
                "name": "Alt",
                "result": "alarm",
                "steps": [{"any": [{"sensor": DOOR}], "within": 60}],
            }
        },
    }


def _rule(name: str = "Tür dann Keller") -> dict[str, Any]:
    return {
        "name": name,
        "result": "alarm",
        "steps": [
            {"any": [{"sensor": DOOR}], "within": 90},
            {"any": [{"group": "Keller"}], "within": 60},
        ],
    }


def test_new_rule_with_group_by_name_and_profiles() -> None:
    change = save_rule(_options(), None, _rule(), labels=LABELS, profiles=["away", "night"])
    assert change.ok, change.errors
    assert change.item_id
    assert change.options is not None
    stored = change.options["rules"][change.item_id]
    # Meldergruppe intern per ID
    assert stored["steps"][1]["any"] == [{"group": "keller"}]
    assert change.options["profiles"]["away"]["rules"] == [change.item_id]
    assert change.options["profiles"]["night"]["rules"] == [change.item_id]


def test_profiles_none_keeps_assignment_and_removal_works() -> None:
    options = _options()
    options["profiles"]["away"]["rules"] = ["alt"]
    kept = save_rule(options, "alt", _rule("Alt"), labels=LABELS)
    assert kept.options is not None
    assert kept.options["profiles"]["away"]["rules"] == ["alt"]
    removed = save_rule(options, "alt", _rule("Alt"), labels=LABELS, profiles=[])
    assert removed.options is not None
    assert removed.options["profiles"]["away"]["rules"] == []


def test_errors() -> None:
    options = _options()
    assert save_rule(options, None, _rule("Alt"), labels=LABELS).errors == {
        "name": "rule_name_taken"
    }
    assert save_rule(options, None, _rule(""), labels=LABELS).errors == {
        "name": "rule_name_required"
    }
    bad = {**_rule(), "steps": [{"any": [{"group": "Garten"}]}]}
    change = save_rule(options, None, bad, labels=LABELS)
    assert change.errors == {"base": "rule_yaml_invalid"}
    assert "Garten" in change.details["message"]
    # Derselbe Melder in zwei Schritten hintereinander
    same = {**_rule(), "steps": [{"any": [{"sensor": DOOR}]}, {"any": [{"sensor": DOOR}]}]}
    change = save_rule(options, None, same, labels=LABELS)
    assert change.errors == {"base": "rule_invalid"}
    assert change.details["findings"][0]["code"] == "rule_same_sensor_next_step"
    assert save_rule(options, "gibtsnicht", _rule(), labels=LABELS).errors == {
        "base": "unknown_rule"
    }


def test_check_without_name_still_parses() -> None:
    change, rule = check_rule(_options(), None, _rule(""), labels=LABELS)
    assert change.errors == {"name": "rule_name_required"}
    assert rule is not None
    assert len(rule.steps) == 2


def test_delete_removes_from_profiles() -> None:
    options = _options()
    options["profiles"]["away"]["rules"] = ["alt"]
    change = delete_rule(options, "alt")
    assert change.options is not None
    assert "alt" not in change.options["rules"]
    assert change.options["profiles"]["away"]["rules"] == []
    assert delete_rule(options, "nix").errors == {"base": "unknown_rule"}
