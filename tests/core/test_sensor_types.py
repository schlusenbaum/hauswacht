"""Tests: weitere Sensorarten (Schloss, Abdeckung, Ereignis, Messwert, Helfer)."""

from __future__ import annotations

from custom_components.hauswacht.core.sensor_types import (
    Threshold,
    camera_for,
    event_triggered,
    is_monitorable,
    normalize,
    parse_cameras,
    parse_thresholds,
    profile_camera,
)
from custom_components.hauswacht.core.sensors import sensor_role
from custom_components.hauswacht.core.state_machine import SensorRole


def test_lock_and_cover() -> None:
    assert normalize("lock.haustuer", "unlocked") == "on"
    assert normalize("lock.haustuer", "jammed") == "on"
    assert normalize("lock.haustuer", "locked") == "off"
    assert normalize("lock.haustuer", "unavailable") == "unavailable"
    assert normalize("cover.garage", "open") == "on"
    assert normalize("cover.garage", "opening") == "on"
    assert normalize("cover.garage", "closed") == "off"
    assert normalize("cover.garage", "seltsam") == "unavailable"


def test_binary_and_helpers_unchanged() -> None:
    assert normalize("binary_sensor.tuer", "on") == "on"
    assert normalize("input_boolean.x", "off") == "off"
    assert normalize("switch.x", "on") == "on"
    assert normalize("binary_sensor.tuer", None) is None
    assert normalize("binary_sensor.tuer", "unknown") == "unknown"


def test_sensor_threshold() -> None:
    limits = {"sensor.vib": Threshold(above=5), "sensor.temp": Threshold(below=3)}
    assert normalize("sensor.vib", "7.5", limits) == "on"
    assert normalize("sensor.vib", "5", limits) == "off"
    assert normalize("sensor.temp", "1", limits) == "on"
    assert normalize("sensor.vib", "abc", limits) == "unavailable"
    assert normalize("sensor.ohne", "100", limits) == "off"  # ohne Schwellwert nie


def test_event() -> None:
    old, new = "2026-11-11T20:00:00+00:00", "2026-11-11T20:05:00+00:00"
    assert normalize("event.klingel", new) == "off"
    assert event_triggered("event.klingel", old, new)
    assert event_triggered("event.klingel", "unknown", new)
    assert not event_triggered("event.klingel", "unavailable", new)  # Neustart
    assert not event_triggered("event.klingel", new, new)
    assert not event_triggered("event.klingel", old, "unavailable")
    assert not event_triggered("binary_sensor.x", "off", "on")


def test_default_roles() -> None:
    assert sensor_role("lock.tuer", None, {}) is SensorRole.ENTRY
    assert sensor_role("cover.tor", "garage", {}) is SensorRole.ENTRY
    assert sensor_role("cover.rollo", "shutter", {}) is SensorRole.INSTANT
    assert sensor_role("event.klingel", "doorbell", {}) is SensorRole.INSTANT
    assert sensor_role("sensor.vib", None, {}) is SensorRole.INSTANT
    assert sensor_role("binary_sensor.tuer", "door", {}) is SensorRole.ENTRY
    assert sensor_role("lock.tuer", None, {"lock.tuer": SensorRole.INSTANT}) is SensorRole.INSTANT


def test_monitorable() -> None:
    assert is_monitorable("lock.x")
    assert not is_monitorable("camera.x")
    assert not is_monitorable("light.x")


def test_parse_thresholds_and_cameras() -> None:
    options = {
        "sensor_thresholds": {"sensor.a": {"above": "5"}, "sensor.b": {}, "sensor.c": "x"},
        "sensor_cameras": {"binary_sensor.t": "camera.flur", "binary_sensor.u": "light.x"},
        "profiles": {"p": {"camera": "camera.garten", "save_snapshots": True}},
    }
    assert parse_thresholds(options) == {"sensor.a": Threshold(above=5.0)}
    cameras = parse_cameras(options)
    assert cameras == {"binary_sensor.t": "camera.flur"}
    assert profile_camera(options, "p") == ("camera.garten", True)
    assert profile_camera(options, "x") == (None, False)
    assert camera_for("binary_sensor.t", cameras, "camera.garten") == "camera.flur"
    assert camera_for("binary_sensor.z", cameras, "camera.garten") == "camera.garten"
    assert camera_for(None, cameras, None) is None
