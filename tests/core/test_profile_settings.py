"""Tests: einzelne Profil-Einstellungen lesen und schreiben."""

from __future__ import annotations

from datetime import time

import pytest

from custom_components.hauswacht.core.profile_settings import (
    SettingError,
    read_number,
    read_select,
    read_switch,
    read_time,
    write,
)

OPTIONS = {
    "profiles": {
        "night": {"name": "Nacht", "entry_delay": 45, "silent": True, "open_policy": "confirm"},
        "away": {"name": "Abwesend", "entry_delay": 9999, "open_policy": "quatsch"},
    }
}


def test_read_values_and_defaults() -> None:
    assert read_number(OPTIONS, "night", "entry_delay") == 45
    assert read_number(OPTIONS, "night", "exit_delay") == 30  # Standard
    assert read_number(OPTIONS, "away", "entry_delay") == 30  # außerhalb der Grenzen
    assert read_select(OPTIONS, "night", "open_policy") == "confirm"
    assert read_select(OPTIONS, "away", "open_policy") == "refuse"
    assert read_switch(OPTIONS, "night", "silent") is True
    assert read_switch(OPTIONS, "away", "silent") is False
    assert read_time(OPTIONS, "night", "auto_arm_time") is None


def test_write_returns_copy() -> None:
    new = write(OPTIONS, "night", "entry_delay", 60.0)
    assert new["profiles"]["night"]["entry_delay"] == 60
    assert OPTIONS["profiles"]["night"]["entry_delay"] == 45
    assert new["profiles"]["night"]["name"] == "Nacht"


def test_write_time_and_clear() -> None:
    new = write(OPTIONS, "night", "auto_arm_time", time(23, 15))
    assert new["profiles"]["night"]["auto_arm_time"] == "23:15:00"
    assert read_time(new, "night", "auto_arm_time") == time(23, 15)
    cleared = write(new, "night", "auto_arm_time", None)
    assert read_time(cleared, "night", "auto_arm_time") is None


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("entry_delay", 601),
        ("entry_delay", -1),
        ("open_policy", "egal"),
        ("siren_tone", "fire"),  # nie ein Brandton
        ("zones", ["x"]),  # Listen nur in der Integration
        ("name", "Neu"),
    ],
)
def test_write_rejects_invalid(key: str, value: object) -> None:
    with pytest.raises(SettingError):
        write(OPTIONS, "night", key, value)


def test_write_unknown_profile() -> None:
    with pytest.raises(SettingError):
        write(OPTIONS, "vacation", "entry_delay", 10)
