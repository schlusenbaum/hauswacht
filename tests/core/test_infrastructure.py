"""Tests der Infrastruktur-Überwachung und des Systemstatus."""

from __future__ import annotations

import pytest

from custom_components.hauswacht.core.infrastructure import (
    SystemStatus,
    faulty_indicators,
    is_healthy,
    system_report,
)


@pytest.mark.parametrize(
    ("state", "healthy"),
    [("on", True), ("off", False), ("unavailable", False), ("unknown", False), (None, False)],
)
def test_is_healthy(state: str | None, healthy: bool) -> None:
    assert is_healthy(state) is healthy


def test_faulty_indicators() -> None:
    states = {"binary_sensor.z2m": "on", "binary_sensor.mqtt": "off", "binary_sensor.ble": None}
    assert faulty_indicators(states) == {"binary_sensor.mqtt", "binary_sensor.ble"}


def test_status_ok() -> None:
    report = system_report({"binary_sensor.z2m": "on"}, [])
    assert report.status is SystemStatus.OK


def test_status_ok_without_indicators() -> None:
    assert system_report({}, []).status is SystemStatus.OK


def test_status_degraded_when_sensor_unavailable() -> None:
    report = system_report({"binary_sensor.z2m": "on"}, ["binary_sensor.fenster"])
    assert report.status is SystemStatus.DEGRADED
    assert report.unavailable_sensors == {"binary_sensor.fenster"}


def test_fault_beats_degraded() -> None:
    report = system_report({"binary_sensor.z2m": "off"}, ["binary_sensor.fenster"])
    assert report.status is SystemStatus.FAULT
    assert report.faulty_infrastructure == {"binary_sensor.z2m"}
