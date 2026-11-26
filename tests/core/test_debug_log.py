"""Debug-Log (ADR 0020): kurze Zeilen ohne Namen, Codes, Orte und Nachrichtentexte."""

from __future__ import annotations

from dataclasses import dataclass

from custom_components.hauswacht.core.debug_log import SECRET_FIELDS, describe
from custom_components.hauswacht.core.state_machine import (
    AlarmState,
    ArmRequested,
    PassageIn,
    ProfileRuntime,
    Readiness,
    StateChanged,
)


def test_event_and_effect_are_short() -> None:
    arm = ArmRequested(
        profile=ProfileRuntime(profile_id="night", entry_delay=30),
        readiness=Readiness(open_sensors=frozenset({"binary_sensor.b", "binary_sensor.a"})),
    )
    assert describe(arm) == (
        "ArmRequested(profile=night, readiness=Readiness(open_sensors="
        "[binary_sensor.a, binary_sensor.b]))"
    )
    changed = StateChanged(old=AlarmState.DISARMED, new=AlarmState.ARMING, cause="user")
    assert describe(changed) == "StateChanged(old=disarmed, new=arming, cause=user)"


def test_names_never_appear() -> None:
    assert describe(PassageIn(door="binary_sensor.tuer", by="Anna")) == (
        "PassageIn(door=binary_sensor.tuer)"
    )
    text = describe(
        {
            "kind": "away",
            "by": "Anna",
            "code": "4711",
            "tags": ["04AABB"],
            "latitude": 52.1,
            "longitude": 9.6,
            "ssid": "FritzBox",
            "title": "Alarm",
            "message": "Anna kam heim",
            "nested": {"name": "Ben", "pin": "1234", "ok": True},
        }
    )
    assert text == "{kind=away, nested={ok=True}}"


def test_secret_fields_in_dataclasses_are_skipped() -> None:
    @dataclass
    class Example:
        sensor: str
        code: str
        user_id: str

    assert describe(Example("binary_sensor.x", "1234", "u1")) == "Example(sensor=binary_sensor.x)"
    assert {"code", "pin", "tag", "latitude", "message", "by"} <= SECRET_FIELDS


def test_timestamps_are_readable() -> None:
    assert describe({"at": 1_764_150_000.0}) == "{at=09:40:00 UTC}"
    assert describe({"window": 900, "accuracy": 0.5}) == "{window=900, accuracy=0.5}"


def test_long_lists_are_cut() -> None:
    text = describe([f"binary_sensor.m{i:02d}" for i in range(20)])
    assert text.endswith("… (+8)]")
