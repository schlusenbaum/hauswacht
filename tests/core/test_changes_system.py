"""Einstellungsregeln: System, PIN-Regeln, Aktions-Codes, Bedienteile (Einstellungsseite)."""

from __future__ import annotations

from typing import Any

from custom_components.hauswacht.core.changes.action_codes import (
    delete_action_code,
    save_action_code,
)
from custom_components.hauswacht.core.changes.system import (
    delete_area,
    delete_control,
    save_homecoming,
    save_infrastructure,
    save_learn_minutes,
    save_pin_rules,
    save_restart,
    save_silence,
)
from custom_components.hauswacht.core.changes.users import save_person


def _options() -> dict[str, Any]:
    return {
        "areas": {"garage": {"name": "Garage"}},
        "profiles": {
            "away": {"name": "Abwesend"},
            "garage_on": {"name": "Garage scharf", "area": "garage"},
        },
        "controls": {"flur": {"name": "Flur", "kind": "keypad"}},
    }


def test_restart() -> None:
    options = _options()
    assert save_restart(options, {"behavior": "armed"}).errors == {"base": "restart_needs_profile"}
    # Profil eines anderen Bereichs zählt nicht
    wrong = save_restart(options, {"behavior": "armed", "profiles": {"main": "garage_on"}})
    assert wrong.errors == {"base": "restart_needs_profile"}
    change = save_restart(
        options, {"behavior": "armed", "profiles": {"main": "away"}, "continue_alarm": True}
    )
    assert change.options is not None
    assert change.options["restart_profiles"] == {"main": "away"}
    assert change.options["restart_continue_alarm"] is True
    assert save_restart(options, {"behavior": "egal"}).errors == {"behavior": "invalid"}


def test_silence_network_homecoming_learn() -> None:
    options = _options()
    silence = save_silence(options, 999)
    assert silence.options is not None
    assert silence.options["stale_after_hours"] == 168
    network = save_infrastructure(options, ["binary_sensor.b", "binary_sensor.a", ""])
    assert network.options is not None
    assert network.options["infrastructure"] == ["binary_sensor.a", "binary_sensor.b"]
    home = save_homecoming(
        options,
        {
            "observe": True,
            "persons": ["person.anna"],
            "ssids": " Heim , Gast,",
            "signals": {"person.anna": ["sensor.wlan"], "person.bob": []},
        },
    )
    assert home.options is not None
    assert home.options["homecoming_ssids"] == ["Heim", "Gast"]
    assert home.options["homecoming_signals"] == {"person.anna": ["sensor.wlan"]}
    assert "away_proof_window" not in home.options  # Dialog schickt es nicht mit
    proof = save_homecoming(options, {"proof_window": 30, "proof_accuracy": "simple"})
    assert proof.options is not None
    assert proof.options["away_proof_window"] == 30
    assert proof.options["away_proof_accuracy"] == "simple"
    weak = save_homecoming(options, {"proof_weak": ["person.niklas"], "proof_weak_window": 3})
    assert weak.options is not None
    assert weak.options["away_proof_weak"] == ["person.niklas"]
    assert weak.options["away_proof_weak_window"] == 3
    learn = save_learn_minutes(options, 500)
    assert learn.options is not None
    assert learn.options["card_learn_minutes"] == 60


def test_delete_area_and_control() -> None:
    options = _options()
    assert delete_area(options, "garage").errors == {"base": "area_has_profiles"}
    assert delete_area(options, "main").errors == {"base": "unknown_area"}
    options["profiles"].pop("garage_on")
    options["users"] = {"anna": {"name": "Anna", "area_rights": {"garage": ["arm"], "main": []}}}
    change = delete_area(options, "garage")
    assert change.options is not None
    assert "garage" not in change.options["areas"]
    assert change.options["users"]["anna"]["area_rights"] == {"main": []}
    control = delete_control(options, "flur")
    assert control.options is not None
    assert control.options["controls"] == {}


def test_pin_rules_and_master_pin() -> None:
    options = _options()
    change = save_pin_rules(options, {"master_pin": "123", "code_arm_required": True})
    assert change.errors == {"master_pin": "invalid_pin"}
    change = save_pin_rules(options, {"master_pin": "123456", "code_arm_required": True})
    assert change.options is not None
    assert change.options["users"]["master"]["pin_digest"]
    assert change.options["code_arm_required"] is True
    assert change.options["card_pin_unlinked"] is True
    removed = save_pin_rules(change.options, {"remove_master_pin": True})
    assert removed.options is not None
    assert "master" not in removed.options["users"]


def test_action_codes() -> None:
    options = _options()
    data = {"name": "Licht", "code": "7777", "key": "arm_day_zones", "action": "event"}
    change = save_action_code(options, None, data)
    assert change.ok, change.errors
    assert change.options is not None
    code_id = change.item_id
    assert code_id
    # Gleicher Code mit gleicher Taste: abgelehnt, mit Namen des anderen
    clash = save_action_code(change.options, None, {**data, "name": "Licht 2"})
    assert clash.errors == {"code": "action_code_taken"}
    assert clash.details["conflict"] == "Licht"
    assert save_action_code(options, None, {**data, "code": "1"}).errors == {
        "code": "action_code_invalid"
    }
    arm = save_action_code(options, None, {**data, "action": "arm"})
    assert arm.errors == {"profile": "action_code_profile_missing"}
    # Kein PIN als Aktions-Code
    with_pin = save_person(options, None, {"name": "Anna", "new_duress_pin": "4444"})
    assert with_pin.options is not None
    pin = save_action_code(with_pin.options, None, {**data, "code": "4444"})
    assert pin.errors == {"code": "action_code_is_pin"}
    deleted = delete_action_code(change.options, code_id)
    assert deleted.options is not None
    assert deleted.options["action_codes"] == {}
