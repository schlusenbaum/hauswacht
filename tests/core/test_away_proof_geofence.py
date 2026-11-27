"""ADR 0018: Signale ohne Koordinaten, die als Ortung zählen (Geofence)."""

from __future__ import annotations

from custom_components.hauswacht.core.away_proof import (
    OPT_AWAY_GEOFENCE,
    PROOF_FRESH,
    AwayTracker,
    geofence_fix,
    parse_proof_settings,
)
from custom_components.hauswacht.core.changes.system import save_homecoming

A = "person.anna"
GEO = "device_tracker.anna_homekit"


def test_geofence_fix() -> None:
    assert geofence_fix("not_home", 5) is not None
    fix = geofence_fix("Arbeit", 5)
    assert fix is not None
    assert (fix.outside_zone, fix.outside_sure, fix.at) == (True, True, 5)
    home = geofence_fix("home", 5)
    assert home is not None
    assert home.outside_zone is False
    assert geofence_fix("unknown", 5) is None
    assert geofence_fix("unavailable", 5) is None
    assert geofence_fix(None, 5) is None


def test_geofence_fix_is_a_fresh_proof() -> None:
    tracker = AwayTracker(parse_proof_settings({}))
    fix = geofence_fix("not_home", 100)
    assert fix is not None
    assert tracker.judge(A, False, [fix], 110) is False
    assert tracker.kind(A) == (PROOF_FRESH, 110)


def test_settings_and_saving() -> None:
    assert parse_proof_settings({OPT_AWAY_GEOFENCE: [GEO, 3]}).geofence == frozenset({GEO})
    assert parse_proof_settings({OPT_AWAY_GEOFENCE: "x"}).geofence == frozenset()
    change = save_homecoming({}, {"signals": {A: [GEO]}, "proof_geofence": [GEO]})
    assert change.options is not None
    assert change.options[OPT_AWAY_GEOFENCE] == [GEO]
    # Ohne den Schlüssel bleibt es, wie es war
    kept = save_homecoming(change.options, {"signals": {A: [GEO]}, "proof_window": 20})
    assert kept.options is not None
    assert kept.options[OPT_AWAY_GEOFENCE] == [GEO]
