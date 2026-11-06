"""Tests der Reaktionslogik: Profil-Reaktionen, Brand-Indikatoren, Texte."""

from __future__ import annotations

import pytest

from custom_components.hauswacht.core.reactions import (
    DEFAULT_TONE,
    DEFAULT_VOLUME,
    alarm_message,
    fire_state,
    is_fire_indicator,
    parse_max_duration,
    parse_reaction,
)
from custom_components.hauswacht.core.siren_guard import FireIndicator

OPTIONS = {
    "sirens": ["siren.diele", "siren.wohnzimmer"],
    "profiles": {
        "night": {
            "sirens": ["siren.diele", "siren.fremd"],
            "siren_tone": "police_panic",
            "siren_volume": "medium",
            "notify": ["mobile_app_a", "mobile_app_b"],
        },
        "home": {"sirens": ["siren.diele"], "silent": True, "siren_tone": "fire"},
    },
}


def test_reaction_defaults() -> None:
    reaction = parse_reaction({}, "away")
    assert reaction.sirens == ()
    assert reaction.tone == DEFAULT_TONE
    assert reaction.volume == DEFAULT_VOLUME
    assert reaction.notify == ()
    assert not reaction.silent


def test_reaction_only_registered_sirens() -> None:
    reaction = parse_reaction(OPTIONS, "night")
    assert reaction.sirens == ("siren.diele",)  # siren.fremd ist nicht registriert
    assert reaction.tone == "police_panic"
    assert reaction.volume == "medium"
    assert reaction.notify == ("mobile_app_a", "mobile_app_b")


def test_fire_tone_falls_back_to_burglar() -> None:
    assert parse_reaction(OPTIONS, "home").tone == DEFAULT_TONE


def test_silent_alarm_has_no_siren_targets() -> None:
    reaction = parse_reaction(OPTIONS, "home")
    assert reaction.sirens == ("siren.diele",)
    assert reaction.siren_targets == ()


@pytest.mark.parametrize(
    ("entity_id", "device_class", "expected"),
    [
        ("binary_sensor.rauchmelder_diele_smoke", "smoke", True),
        ("binary_sensor.rauchmelder_diele_test", None, True),
        ("binary_sensor.co_melder", "carbon_monoxide", True),
        ("binary_sensor.rauchmelder_diele_battery_low", "battery", False),
        ("binary_sensor.rauchmelder_diele_fault", "problem", False),
        ("sensor.rauchmelder_diele_test", None, False),
    ],
)
def test_is_fire_indicator(entity_id: str, device_class: str | None, expected: bool) -> None:
    assert is_fire_indicator(entity_id, device_class) is expected


@pytest.mark.parametrize(
    ("states", "expected"),
    [
        ([], FireIndicator.CLEAR),
        (["off", "off"], FireIndicator.CLEAR),
        (["off", "on"], FireIndicator.ACTIVE),
        (["off", "unavailable"], FireIndicator.UNKNOWN),
        ([None], FireIndicator.UNKNOWN),
        (["unknown", "on"], FireIndicator.ACTIVE),
    ],
)
def test_fire_state(states: list[str | None], expected: FireIndicator) -> None:
    assert fire_state(states) is expected


@pytest.mark.parametrize(
    ("state", "expected"),
    [("240", 240), ("240.0", 240), ("unavailable", 99), (None, 99), ("0", 99), ("-5", 99)],
)
def test_parse_max_duration(state: str | None, expected: int) -> None:
    assert parse_max_duration(state, 99) == expected


def test_alarm_message_marks_test_mode() -> None:
    title, message = alarm_message("night", "binary_sensor.fenster", test_mode=True)
    assert "TESTALARM" in title
    assert "binary_sensor.fenster" in message
    assert "EINBRUCHALARM" in alarm_message("night", "x", test_mode=False)[0]
