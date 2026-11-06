"""Tests für Profile aus Optionen und die PIN-Verwaltung."""

from __future__ import annotations

import pytest

from custom_components.hauswacht.core.pin import (
    PinHash,
    hash_pin,
    is_valid_pin_format,
    verify_pin,
)
from custom_components.hauswacht.core.profiles import (
    PANEL_STATE_BY_PROFILE,
    PROFILE_IDS,
    build_profiles,
    profile_settings,
)

# --- Profile ----------------------------------------------------------------


def test_builtin_profiles_with_defaults() -> None:
    profiles = build_profiles({})
    assert set(profiles) == {"home", "night", "away", "vacation", "custom"}
    assert profiles["away"].exit_delay == 60
    assert profiles["night"].exit_delay == 0
    assert all(p.entry_delay == 30 for p in profiles.values())


def test_every_profile_has_a_panel_state() -> None:
    assert set(PANEL_STATE_BY_PROFILE) == set(PROFILE_IDS)
    assert PANEL_STATE_BY_PROFILE["vacation"] == "armed_vacation"


def test_options_override_defaults() -> None:
    options = {"profiles": {"away": {"exit_delay": 90, "entry_delay": 15, "reaction_time": 240}}}
    away = build_profiles(options)["away"]
    assert (away.exit_delay, away.entry_delay, away.reaction_time) == (90, 15, 240)


@pytest.mark.parametrize("bad", [-1, 601, "abc", None, 3.7e9])
def test_invalid_option_values_fall_back_to_defaults(bad: object) -> None:
    settings = profile_settings({"profiles": {"home": {"entry_delay": bad}}}, "home")
    assert settings["entry_delay"] == 30


def test_reaction_time_zero_falls_back() -> None:
    settings = profile_settings({"profiles": {"home": {"reaction_time": 0}}}, "home")
    assert settings["reaction_time"] == 180


# --- PIN --------------------------------------------------------------------


@pytest.mark.parametrize("pin", ["1234", "12345678", "0000"])
def test_valid_pin_formats(pin: str) -> None:
    assert is_valid_pin_format(pin)


@pytest.mark.parametrize("pin", ["", "123", "123456789", "12a4", " 1234", "١٢٣٤"])
def test_invalid_pin_formats(pin: str) -> None:
    assert not is_valid_pin_format(pin)


def test_hash_and_verify() -> None:
    stored = hash_pin("4711")
    assert "4711" not in stored.digest
    assert verify_pin("4711", stored)
    assert not verify_pin("4712", stored)
    assert not verify_pin("", stored)
    assert not verify_pin(None, stored)


def test_same_pin_gets_different_salt() -> None:
    assert hash_pin("4711").salt != hash_pin("4711").salt


def test_without_stored_pin_everything_is_accepted() -> None:
    assert verify_pin(None, None)
    assert verify_pin("9999", None)


def test_corrupted_hash_is_rejected() -> None:
    assert not verify_pin("4711", PinHash(salt="zz", digest="zz"))


def test_hash_pin_rejects_invalid_format() -> None:
    with pytest.raises(ValueError, match="PIN"):
        hash_pin("12")
