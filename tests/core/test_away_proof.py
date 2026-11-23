"""„weg“ nur mit Beleg (ADR 0015)."""

from __future__ import annotations

from custom_components.hauswacht.core.away_proof import (
    ACCURACY_SIMPLE,
    AwayTracker,
    Fix,
    Home,
    ProofSettings,
    distance_m,
    locate,
    parse_proof_settings,
    proven_away,
)

HOME = Home(52.0, 13.0, 100.0)
NEAR = {"latitude": 52.0018, "longitude": 13.0, "gps_accuracy": 200}  # ~200 m, ungenau
FAR = {"latitude": 52.05, "longitude": 13.0, "gps_accuracy": 20}  # ~5,6 km
S = ProofSettings()


def test_distance() -> None:
    assert 190 < distance_m(52.0, 13.0, 52.0018, 13.0) < 210


def test_locate_needs_coordinates() -> None:
    assert locate("not_home", {}, 0, home=HOME) is None  # WLAN, Ping, Router: kein Beleg
    assert locate("unavailable", FAR, 0, home=HOME) is None
    fix = locate("not_home", FAR, 5, home=HOME)
    assert fix == Fix(outside_zone=True, outside_sure=True, at=5)


def test_strict_ignores_gps_jump_simple_does_not() -> None:
    strict = locate("not_home", NEAR, 0, home=HOME)
    assert strict is not None
    assert strict.outside_zone
    assert not strict.outside_sure  # 200 m < 100 m Radius + 200 m Ungenauigkeit
    simple = locate("not_home", NEAR, 0, home=HOME, accuracy=ACCURACY_SIMPLE)
    assert simple is not None
    assert simple.outside_sure


def test_fresh_accurate_fix_alone() -> None:
    fix = Fix(outside_zone=True, outside_sure=True, at=1000)
    assert proven_away([fix], [], 1000 + 14 * 60, S)
    assert not proven_away([fix], [], 1000 + 16 * 60, S)  # zu alt


def test_door_then_inaccurate_fix() -> None:
    fix = Fix(outside_zone=True, outside_sure=False, at=1000 + 5 * 60)
    assert not proven_away([fix], [], 5000, S)
    assert proven_away([fix], [1000], 5000, S)  # Tür, 5 min später geortet
    assert not proven_away([fix], [1000 + 6 * 60], 5000, S)  # Ortung VOR der Tür
    assert not proven_away([fix], [1000 - 11 * 60], 5000, S)  # Tür zu lange davor


def test_old_door_from_before_last_return_does_not_count() -> None:
    fix = Fix(outside_zone=True, outside_sure=False, at=1100)
    assert not proven_away([fix], [1000], 5000, S, since=2000)


def test_tracker_sticky_until_home() -> None:
    tracker = AwayTracker()
    tracker.judge("p", True, [], 0)
    # WLAN weg, aber keine Ortung: unbekannt (schlafendes Handy macht niemanden abwesend)
    assert tracker.judge("p", False, [], 100) is None
    fix = Fix(outside_zone=True, outside_sure=True, at=200)
    assert tracker.judge("p", False, [fix], 200) is False
    assert tracker.judge("p", False, [], 99999) is False  # bleibt belegt
    assert tracker.judge("p", None, [], 99999) is None
    assert tracker.judge("p", False, [], 99999) is False
    assert tracker.judge("p", True, [], 100000) is True
    assert tracker.judge("p", False, [], 100001) is None  # neues Weggehen braucht neuen Beleg


def test_tracker_door_before_fix() -> None:
    tracker = AwayTracker()
    tracker.judge("p", True, [], 0)
    tracker.note_door(1000)
    fix = Fix(outside_zone=True, outside_sure=False, at=1200)
    assert tracker.judge("p", False, [fix], 1300) is False


def test_parse_settings() -> None:
    assert parse_proof_settings({}) == ProofSettings(15, "strict")
    assert parse_proof_settings(
        {"away_proof_window": "30", "away_proof_accuracy": "simple"}
    ) == ProofSettings(30, "simple")
    assert parse_proof_settings({"away_proof_window": 0, "away_proof_accuracy": "x"}) == (
        ProofSettings(1, "strict")
    )


def test_check_hint_for_person_without_location() -> None:
    from custom_components.hauswacht.core.checks import run_checks  # noqa: PLC0415

    overview = {
        "profiles": [],
        "monitoring": {"homecoming": {"no_fix": ["Niklas"]}, "infrastructure": [{"ok": True}]},
    }
    found = [f for f in run_checks(overview, "de") if f["code"] == "away_no_fix"]
    assert len(found) == 1
    assert found[0]["severity"] == "warning"
    assert found[0]["text"].startswith("Niklas kann nicht als weg erkannt werden")
