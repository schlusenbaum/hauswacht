"""Funkstille je Melder: eigene Grenze, nie prüfen, Empfehlung je Melder."""

from __future__ import annotations

from custom_components.hauswacht.core.changes.sensors import save_sensor, save_stale_override
from custom_components.hauswacht.core.checks import _monitoring
from custom_components.hauswacht.core.profiles import (
    stale_override_hours,
    stale_overrides_seconds,
)
from custom_components.hauswacht.core.sensors import SensorSnapshot, evaluate_readiness
from custom_components.hauswacht.core.silence import SilenceRecord, advice, sensor_advice

DOOR = "binary_sensor.hintertuer"
MOTION = "binary_sensor.flur"
HOUR = 3600.0


def test_save_override_modes() -> None:
    change = save_stale_override({}, DOOR, "hours", 24)
    assert change.options is not None
    assert change.options["stale_overrides"] == {DOOR: 24}
    off = save_stale_override(change.options, DOOR, "off")
    assert off.options is not None
    assert stale_override_hours(off.options) == {DOOR: 0}
    assert stale_overrides_seconds(off.options) == {DOOR: None}
    back = save_stale_override(off.options, DOOR, "default")
    assert back.options is not None
    assert back.options["stale_overrides"] == {}
    assert save_stale_override({}, DOOR, "hours", 0).errors == {
        "stale_hours": "stale_hours_invalid"
    }
    assert save_stale_override({}, DOOR, "laut").errors == {"stale": "invalid"}


def test_save_sensor_with_stale() -> None:
    options = {"zones": {"aussen": {"name": "Außen", "entities": [DOOR]}}}
    change = save_sensor(
        options,
        DOOR,
        {"group": "aussen", "stale": {"mode": "hours", "hours": 30}},
        labels={},
        device_class="door",
    )
    assert change.options is not None
    assert change.options["stale_overrides"] == {DOOR: 30}


def test_readiness_uses_own_limit() -> None:
    now = 100 * HOUR
    snapshots = {
        DOOR: SensorSnapshot(entity_id=DOOR, state="off", last_reported=now - 20 * HOUR),
        MOTION: SensorSnapshot(entity_id=MOTION, state="off", last_reported=now - 4 * HOUR),
    }
    general = evaluate_readiness([DOOR, MOTION], snapshots, now=now, stale_after=3 * HOUR)
    assert general.unavailable_sensors == {DOOR, MOTION}
    own = evaluate_readiness(
        [DOOR, MOTION],
        snapshots,
        now=now,
        stale_after=3 * HOUR,
        stale_overrides={DOOR: 24 * HOUR},
    )
    assert own.unavailable_sensors == {MOTION}
    never = evaluate_readiness(
        [DOOR], snapshots, now=now, stale_after=3 * HOUR, stale_overrides={DOOR: None}
    )
    assert never.unavailable_sensors == frozenset()
    # "Nicht verfügbar" wird auch bei "nie prüfen" erkannt
    gone = {DOOR: SensorSnapshot(entity_id=DOOR, state="unavailable", last_reported=now)}
    still = evaluate_readiness([DOOR], gone, now=now, stale_overrides={DOOR: None})
    assert still.unavailable_sensors == {DOOR}


def test_advice_per_sensor_and_without_own() -> None:
    records = {DOOR: SilenceRecord(longest=16 * HOUR), MOTION: SilenceRecord(longest=1.5 * HOUR)}
    assert advice(records, 5) == 24
    assert advice(records, 5, skip=[DOOR]) == 3
    assert sensor_advice(records[DOOR], 5) == 24
    assert sensor_advice(records[DOOR], 1) is None


def test_check_finds_tight_own_limit() -> None:
    overview = {
        "monitoring": {
            "stale_after_hours": 3,
            "recommended_hours": 3,
            "infrastructure": [{"name": "Bridge", "ok": True}],
            "stale_overrides": [
                {"name": "Hintertür", "hours": 12, "recommended": 24},
                {"name": "Keller", "hours": 0, "recommended": 30},
            ],
        }
    }
    codes = [f["code"] for f in _monitoring(overview, "de")]
    assert codes == ["silence_tight_sensor"]
