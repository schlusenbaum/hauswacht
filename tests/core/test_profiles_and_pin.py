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
    DEFAULT_EXIT_DELAY,
    FALLBACK_PANEL_STATE,
    build_profiles,
    find_profile,
    migrate_v1_options,
    panel_state,
    profile_for_mode,
    profile_ids,
    profile_info,
    profile_settings,
    used_panel_modes,
)

OPTIONS = {
    "profiles": {
        "nacht_eg": {"name": "Nacht EG", "icon": "mdi:weather-night", "panel_mode": "night"},
        "garten": {"name": "Garten", "exit_delay": 90},
        "kaputt": "kein Profil",
    }
}

# --- Profile ----------------------------------------------------------------


def test_no_builtin_profiles() -> None:
    assert profile_ids({}) == ()
    assert build_profiles({}) == {}


def test_profiles_in_stored_order_and_garbage_ignored() -> None:
    assert profile_ids(OPTIONS) == ("nacht_eg", "garten")


def test_profile_info() -> None:
    info = profile_info(OPTIONS, "nacht_eg")
    assert (info.name, info.icon, info.panel_mode) == ("Nacht EG", "mdi:weather-night", "night")
    garten = profile_info(OPTIONS, "garten")
    assert garten.panel_mode is None
    assert garten.icon.startswith("mdi:")


def test_invalid_panel_mode_is_ignored() -> None:
    options = {"profiles": {"x": {"name": "X", "panel_mode": "armed_galaxy"}}}
    assert profile_info(options, "x").panel_mode is None


def test_find_profile_by_id_or_name() -> None:
    assert find_profile(OPTIONS, "garten") == "garten"
    assert find_profile(OPTIONS, "nacht eg") == "nacht_eg"
    assert find_profile(OPTIONS, "Keller") is None


def test_panel_modes() -> None:
    assert profile_for_mode(OPTIONS, "night") == "nacht_eg"
    assert profile_for_mode(OPTIONS, "away") is None
    assert used_panel_modes(OPTIONS) == ("night",)
    assert panel_state(OPTIONS, "nacht_eg") == "armed_night"
    assert panel_state(OPTIONS, "garten") == FALLBACK_PANEL_STATE


def test_settings_defaults_and_overrides() -> None:
    assert profile_settings(OPTIONS, "nacht_eg")["exit_delay"] == DEFAULT_EXIT_DELAY
    assert profile_settings(OPTIONS, "garten")["exit_delay"] == 90
    assert set(build_profiles(OPTIONS)) == {"nacht_eg", "garten"}


@pytest.mark.parametrize("bad", [-1, 601, "abc", None, 3.7e9])
def test_invalid_option_values_fall_back_to_defaults(bad: object) -> None:
    settings = profile_settings({"profiles": {"p": {"entry_delay": bad}}}, "p")
    assert settings["entry_delay"] == 30


def test_reaction_time_zero_falls_back() -> None:
    settings = profile_settings({"profiles": {"p": {"reaction_time": 0}}}, "p")
    assert settings["reaction_time"] == 180


# --- Migration ----------------------------------------------------------------


def test_migration_creates_former_fixed_profiles() -> None:
    old = {
        "zones": {"aussen": {"name": "Außen", "entities": ["binary_sensor.t"]}},
        "profiles": {"night": {"zones": ["aussen"], "entry_delay": 15}},
        "pin_salt": "aa",
    }
    new = migrate_v1_options(old)
    assert profile_ids(new) == ("home", "night", "away", "vacation", "custom")
    night = new["profiles"]["night"]
    assert night["name"] == "Nacht"
    assert night["panel_mode"] == "night"
    assert night["zones"] == ["aussen"]
    assert night["entry_delay"] == 15  # geänderter Wert bleibt
    assert new["profiles"]["away"]["exit_delay"] == 60  # alter Standard festgeschrieben
    assert new["pin_salt"] == "aa"  # andere Optionen bleiben unverändert
    assert used_panel_modes(new) == ("home", "night", "away", "vacation", "custom")


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
