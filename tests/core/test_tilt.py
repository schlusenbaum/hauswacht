"""Melder mit Kippstellung (ADR 0010)."""

from __future__ import annotations

import pytest

from custom_components.hauswacht.core.profiles import profile_behaviour
from custom_components.hauswacht.core.sensor_types import SensorType
from custom_components.hauswacht.core.state_machine import (
    AlarmContext,
    AlarmState,
    ArmRequested,
    BypassedSensorOpened,
    OpenSensorPolicy,
    ProfileRuntime,
    Readiness,
    SensorRole,
    SensorsRestored,
    StateChanged,
    step,
)
from custom_components.hauswacht.core.tilt import (
    TILTED,
    TiltSource,
    delete_tilt_source,
    judge,
    known_values,
    looks_like_tilt,
    parse_tilt_sources,
    position,
    save_tilt_source,
    suggest,
    types_with_tilt,
)

SENORO = TiltSource(
    entity_id="sensor.fenster_opening_state",
    closed=frozenset({"closed"}),
    tilted=frozenset({"tilted"}),
)
GRIFF = TiltSource(
    entity_id="binary_sensor.griff",
    attribute="window_state",
    closed=frozenset({"closed"}),
    tilted=frozenset({"tilted"}),
)


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        ("closed", "off"),
        ("CLOSED", "off"),
        ("tilted", TILTED),
        ("open", "on"),
        ("half_open", "on"),  # unbekannt: sichere Seite
        ("unavailable", "unavailable"),
        ("unknown", "unknown"),
        ("", "unavailable"),
        (None, None),
    ],
)
def test_position_from_state(state: str | None, expected: str | None) -> None:
    assert position(SENORO, state) == expected


def test_position_from_attribute() -> None:
    assert position(GRIFF, "on", {"window_state": "TILTED"}) == TILTED
    assert position(GRIFF, "off", {"window_state": "CLOSED"}) == "off"
    assert position(GRIFF, "on", {"window_state": "OPEN"}) == "on"
    # Attribut fehlt: nicht verfügbar statt stillschweigend zu
    assert position(GRIFF, "off", {}) == "unavailable"
    assert position(GRIFF, "unavailable", {"window_state": "CLOSED"}) == "unavailable"


@pytest.mark.parametrize(
    ("value", "allowed", "expected"),
    [
        (TILTED, True, "off"),
        (TILTED, False, "on"),
        ("on", True, "on"),
        ("off", False, "off"),
        ("unavailable", True, "unavailable"),
        (None, True, None),
    ],
)
def test_judge(value: str | None, allowed: bool, expected: str | None) -> None:
    assert judge(value, tilt_allowed=allowed) == expected


def test_known_values_and_suggestion() -> None:
    values = known_values("tilted", {"options": ["open", "closed", "tilted"]}, None)
    assert values == ["open", "closed", "tilted"]
    assert suggest(values) == (["closed"], ["tilted"])
    assert looks_like_tilt(values)
    assert not looks_like_tilt(["on", "off"])
    assert known_values("on", {"window_state": "CLOSED"}, "window_state") == ["CLOSED"]
    assert suggest(["offen", "gekippt", "zu"]) == (["zu"], ["gekippt"])


def test_save_parse_and_delete() -> None:
    options = {
        "zones": {"fenster": {"name": "Fenster", "entities": ["sensor.f", "binary_sensor.t"]}}
    }
    options = save_tilt_source(
        options, "sensor.f", attribute=None, closed=["closed"], tilted=["tilted", "closed"]
    )
    source = parse_tilt_sources(options)["sensor.f"]
    assert source.closed == frozenset({"closed"})
    assert source.tilted == frozenset({"tilted"})  # nie zugleich zu und gekippt
    assert types_with_tilt(options)["sensor.f"] is SensorType.WINDOW
    removed = delete_tilt_source(options, "sensor.f")
    assert "sensor.f" not in parse_tilt_sources(removed)
    assert removed["zones"]["fenster"]["entities"] == ["binary_sensor.t"]
    with pytest.raises(ValueError, match="no_closed_value"):
        save_tilt_source(options, "sensor.g", attribute=None, closed=[], tilted=["tilted"])


def test_explicit_type_wins() -> None:
    options = save_tilt_source(
        {"sensor_types": {"sensor.f": "door"}}, "sensor.f", attribute=None, closed=["zu"], tilted=[]
    )
    assert types_with_tilt(options)["sensor.f"] is SensorType.DOOR


def test_profile_setting_default_off() -> None:
    options = {
        "profiles": {"nacht": {"name": "Nacht"}, "weg": {"name": "Weg", "tilt_allowed": True}}
    }
    assert profile_behaviour(options, "nacht").tilt_allowed is False
    assert profile_behaviour(options, "weg").tilt_allowed is True


PROFILE = ProfileRuntime(profile_id="weg", open_policy=OpenSensorPolicy.CONFIRM)


def _armed_with_bypass() -> AlarmContext:
    ctx, _ = step(
        AlarmContext(),
        ArmRequested(
            profile=PROFILE,
            readiness=Readiness(open_sensors=frozenset({"sensor.f"})),
            confirmed=True,
        ),
        0.0,
    )
    assert ctx.state is AlarmState.ARMED
    assert "sensor.f" in ctx.bypassed
    return ctx


def test_bypassed_tilted_window_opened_fully_triggers() -> None:
    ctx = _armed_with_bypass()
    ctx, effects = step(ctx, BypassedSensorOpened("sensor.f", SensorRole.INSTANT), 1.0)
    assert ctx.state is AlarmState.TRIGGERED
    assert "sensor.f" not in ctx.bypassed
    assert any(isinstance(e, SensorsRestored) for e in effects)
    assert any(isinstance(e, StateChanged) and e.new is AlarmState.TRIGGERED for e in effects)


def test_bypassed_opened_ignored_when_not_bypassed() -> None:
    ctx, effects = step(AlarmContext(), BypassedSensorOpened("sensor.f", SensorRole.INSTANT), 0.0)
    assert ctx.state is AlarmState.DISARMED
    assert effects[0].reason == "not_bypassed"  # type: ignore[attr-defined]
