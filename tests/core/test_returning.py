"""„Bei Rückkehr“ (ADR 0015) – Einstellungen und Umstellung, ohne Home Assistant."""

from __future__ import annotations

from typing import Any

from custom_components.hauswacht.core.returning import (
    RETURN_ALWAYS,
    RETURN_AUTO_ONLY,
    RETURN_DOOR,
    RETURN_OFF,
    RETURN_PASSAGE,
    ReturnConfig,
    legacy_return,
    migrate_return,
    parse_return,
    return_from_input,
)

A = "person.anna"
B = "person.ben"


def test_parse_stored_and_limits() -> None:
    options = {"profiles": {"n": {"return": {"mode": "door", "persons": [A, A, 3], "window": 99}}}}
    config = parse_return(options, "n")
    assert config == ReturnConfig(RETURN_DOOR, (A,), 30)
    assert config.disarms
    assert config.door_proof
    assert config.with_door
    assert not config.lets_in
    assert parse_return({"profiles": {"n": {"return": {"mode": "x"}}}}, "n").mode == RETURN_OFF
    assert parse_return({}, "n") == ReturnConfig()
    assert parse_return({"profiles": {"n": {}}}, None) == ReturnConfig()


def test_needs_persons_to_be_active() -> None:
    assert not ReturnConfig(RETURN_ALWAYS).active
    assert ReturnConfig(RETURN_ALWAYS, (A,)).disarms
    assert ReturnConfig(RETURN_PASSAGE, (A,)).lets_in
    assert not ReturnConfig(RETURN_PASSAGE, (A,)).disarms


def test_legacy_arrival_uses_away_persons() -> None:
    stored = {"auto_arrival_mode": "door", "auto_away_persons": [A], "auto_arrival_window": 8}
    assert legacy_return(stored) == ReturnConfig(RETURN_DOOR, (A,), 8)
    old_switch = {"auto_disarm_on_arrival": True, "auto_away_persons": [A]}
    assert legacy_return(old_switch).mode == RETURN_AUTO_ONLY
    assert legacy_return({"auto_arrival_mode": "door"}) == ReturnConfig()  # ohne Personen: aus


def test_legacy_phone_passage_wins() -> None:
    stored = {
        "auto_arrival_mode": "auto_only",
        "auto_away_persons": [A, B],
        "passage": {"enabled": True, "persons": [B], "window": 3},
    }
    assert legacy_return(stored) == ReturnConfig(RETURN_PASSAGE, (B,), 3)
    # Durchgang aus: Handy-Reinlassen galt nicht
    stored["passage"] = {"enabled": False, "persons": [B]}
    assert legacy_return(stored).mode == RETURN_AUTO_ONLY


def test_migrate_keeps_old_keys_and_reports_both() -> None:
    options: dict[str, Any] = {
        "other": 1,
        "profiles": {
            "night": {
                "auto_arrival_mode": "auto_only",
                "auto_away_persons": [A],
                "passage": {"enabled": True, "persons": [A, B]},
            },
            "away": {"auto_arrival_mode": "door", "auto_away_persons": [A]},
            "done": {"return": {"mode": "always", "persons": [B]}},
        },
    }
    new, both = migrate_return(options)
    assert both == ["night"]
    assert new["other"] == 1
    assert new["profiles"]["night"]["return"] == {
        "mode": "passage",
        "persons": [A, B],
        "window": 5,
    }
    assert new["profiles"]["night"]["auto_arrival_mode"] == "auto_only"  # bleibt für ältere
    assert new["profiles"]["away"]["return"]["mode"] == "door"
    assert new["profiles"]["done"] == {"return": {"mode": "always", "persons": [B]}}
    assert "return" not in options["profiles"]["away"]  # Original unverändert


def test_from_input() -> None:
    assert return_from_input({"mode": "always", "persons": [A], "window": "4"}) == {
        "mode": "always",
        "persons": [A],
        "window": 4,
    }
    assert return_from_input({"mode": "nonsense"})["mode"] == RETURN_OFF
