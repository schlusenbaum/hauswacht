"""Immer aktive Melder und Scharf durch Schließen – Einstellungen."""

from __future__ import annotations

from custom_components.hauswacht.core.always_active import (
    ALWAYS_PROFILE_ID,
    always_reaction_options,
    always_runtime,
    parse_always_active,
    parse_arm_on_close,
)
from custom_components.hauswacht.core.reactions import parse_reaction


def test_always_active_defaults_to_notification_only() -> None:
    options = {"sirens": ["siren.a"], "always_active": {"sensors": ["binary_sensor.tresor"]}}
    config = parse_always_active(options)
    assert config.configured
    assert not config.sirens_enabled
    reaction = parse_reaction(always_reaction_options(options), ALWAYS_PROFILE_ID)
    assert reaction.sirens == ()
    assert reaction.silent is True


def test_always_active_with_sirens() -> None:
    options = {
        "sirens": ["siren.a"],
        "always_active": {
            "zones": ["schrank"],
            "sirens_enabled": True,
            "sirens": ["siren.a", "siren.fremd"],
            "reaction_time": 90,
        },
    }
    config = parse_always_active(options)
    reaction = parse_reaction(always_reaction_options(options), ALWAYS_PROFILE_ID)
    assert reaction.sirens == ("siren.a",)  # nur registrierte Sirenen
    assert reaction.silent is False
    assert always_runtime(config).reaction_time == 90
    assert not parse_always_active({}).configured


def test_arm_on_close() -> None:
    options = {
        "profiles": {
            "away": {
                "arm_on_close": {"enabled": True, "doors": ["binary_sensor.tuer"], "settle": 99}
            },
            "night": {"arm_on_close": {"enabled": True, "doors": []}},
        }
    }
    away = parse_arm_on_close(options, "away")
    assert away.enabled
    assert away.doors == {"binary_sensor.tuer"}
    assert away.settle == 60
    assert not parse_arm_on_close(options, "night").enabled  # ohne Tür aus
    assert not parse_arm_on_close(options, "fehlt").enabled
