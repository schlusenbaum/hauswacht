"""Tests: Melderarten (offen/zu) und Melder-Typen."""

from __future__ import annotations

from custom_components.hauswacht.core.sensor_types import (
    SensorType,
    default_type,
    excluded_sensors,
    is_monitorable,
    migrate_roles_to_types,
    normalize,
    parse_types,
    role_overrides,
    sensor_type,
)
from custom_components.hauswacht.core.sensors import sensor_role
from custom_components.hauswacht.core.state_machine import SensorRole


def test_lock_and_cover_are_open_closed() -> None:
    assert normalize("lock.haustuer", "unlocked") == "on"
    assert normalize("lock.haustuer", "jammed") == "on"
    assert normalize("lock.haustuer", "locked") == "off"
    assert normalize("cover.garage", "opening") == "on"
    assert normalize("cover.garage", "closed") == "off"
    assert normalize("cover.garage", "seltsam") == "unavailable"
    assert normalize("binary_sensor.tuer", "on") == "on"
    assert normalize("binary_sensor.tuer", None) is None
    assert normalize("lock.haustuer", "unknown") == "unknown"


def test_only_open_closed_kinds() -> None:
    assert is_monitorable("binary_sensor.x")
    assert is_monitorable("lock.x")
    assert is_monitorable("cover.x")
    for gone in ("sensor.x", "event.x", "input_boolean.x", "switch.x", "camera.x"):
        assert not is_monitorable(gone)


def test_default_types() -> None:
    assert default_type("binary_sensor.t", "door") is SensorType.DOOR
    assert default_type("binary_sensor.t", "garage_door") is SensorType.DOOR
    assert default_type("binary_sensor.f", "window") is SensorType.WINDOW
    assert default_type("binary_sensor.b", "occupancy") is SensorType.MOTION
    assert default_type("binary_sensor.m", "tamper") is SensorType.TAMPER
    assert default_type("binary_sensor.w", "moisture") is SensorType.TECHNICAL
    assert default_type("binary_sensor.r", "smoke") is SensorType.OTHER  # Rauch bewusst nicht
    assert default_type("binary_sensor.v", "vibration") is SensorType.OTHER
    assert default_type("binary_sensor.x", None) is SensorType.OTHER
    assert default_type("lock.s", None) is SensorType.DOOR
    assert default_type("cover.tor", "garage") is SensorType.DOOR
    assert default_type("cover.rollo", "shutter") is SensorType.OTHER


def test_types_drive_roles() -> None:
    types = parse_types({"sensor_types": {"binary_sensor.f": "door", "binary_sensor.x": "quatsch"}})
    assert types == {"binary_sensor.f": SensorType.DOOR}
    overrides = role_overrides(types)
    assert sensor_role("binary_sensor.f", "window", overrides) is SensorRole.ENTRY
    assert sensor_role("binary_sensor.b", "motion", overrides) is SensorRole.FOLLOWER
    assert sensor_role("lock.s", None, overrides) is SensorRole.ENTRY
    assert sensor_type("binary_sensor.w", "moisture", types) is SensorType.TECHNICAL


def test_migration_roles_to_types_and_cleanup() -> None:
    old = {
        "sensor_roles": {"binary_sensor.f": "entry", "binary_sensor.b": "follower", "x": "?"},
        "sensor_thresholds": {"sensor.t": {"above": 5}},
        "sensor_cameras": {"binary_sensor.f": "camera.c"},
        "zones": {"aussen": {"name": "Außen", "entities": ["binary_sensor.f", "sensor.t"]}},
        "always_active": {"sensors": ["event.klingel", "binary_sensor.w"]},
        "profiles": {"nacht": {"name": "Nacht", "camera": "camera.c", "save_snapshots": True}},
    }
    new = migrate_roles_to_types(old)
    assert "sensor_roles" not in new
    assert new["sensor_types"] == {"binary_sensor.f": "door", "binary_sensor.b": "motion"}
    assert "sensor_thresholds" not in new
    assert "sensor_cameras" not in new
    assert new["zones"]["aussen"]["entities"] == ["binary_sensor.f"]
    assert new["always_active"]["sensors"] == ["binary_sensor.w"]
    assert new["profiles"]["nacht"] == {"name": "Nacht"}


def test_excluded_sensors() -> None:
    options = {"profiles": {"nacht": {"excluded": ["binary_sensor.flur", 3]}}}
    assert excluded_sensors(options, "nacht") == frozenset({"binary_sensor.flur"})
    assert excluded_sensors(options, "x") == frozenset()
