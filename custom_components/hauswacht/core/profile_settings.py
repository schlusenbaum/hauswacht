"""Einzelne Profil-Einstellungen lesen und schreiben (für Einstellungs-Entitäten im Dashboard).

Rein und ohne Home Assistant. Nur "Kleinigkeiten" – Verzögerungen, Uhrzeiten, Schalter.
Zonen, Sirenen, Benachrichtigungsziele und Personen (Listen) bleiben in der Integration.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import time
from typing import Any

from .automation import DEFAULT_AWAY_DELAY, MAX_AWAY_DELAY, parse_time
from .profiles import (
    DEFAULT_ALARM_CYCLES,
    DEFAULT_ENTRY_DELAY,
    DEFAULT_EXIT_DELAY,
    DEFAULT_REACTION_TIME,
    MAX_ALARM_CYCLES,
    MAX_DELAY,
    MAX_REACTION_TIME,
)
from .reactions import DEFAULT_TONE, DEFAULT_VOLUME
from .siren_guard import BURGLAR_TONES, VOLUME_LEVELS
from .state_machine import OpenSensorPolicy, UnavailableSensorPolicy


@dataclass(frozen=True)
class NumberSetting:
    minimum: int
    maximum: int
    step: int
    default: int
    unit: str | None


@dataclass(frozen=True)
class SelectSetting:
    options: tuple[str, ...]
    default: str


NUMBERS: Mapping[str, NumberSetting] = {
    "exit_delay": NumberSetting(0, MAX_DELAY, 5, DEFAULT_EXIT_DELAY, "s"),
    "entry_delay": NumberSetting(0, MAX_DELAY, 5, DEFAULT_ENTRY_DELAY, "s"),
    "reaction_time": NumberSetting(10, MAX_REACTION_TIME, 10, DEFAULT_REACTION_TIME, "s"),
    "max_alarm_cycles": NumberSetting(1, MAX_ALARM_CYCLES, 1, DEFAULT_ALARM_CYCLES, None),
    "auto_away_delay": NumberSetting(1, MAX_AWAY_DELAY, 1, DEFAULT_AWAY_DELAY, "min"),
}

SELECTS: Mapping[str, SelectSetting] = {
    "open_policy": SelectSetting(
        tuple(p.value for p in OpenSensorPolicy), OpenSensorPolicy.REFUSE.value
    ),
    "unavailable_policy": SelectSetting(
        tuple(p.value for p in UnavailableSensorPolicy), UnavailableSensorPolicy.REFUSE.value
    ),
    "siren_tone": SelectSetting(tuple(sorted(BURGLAR_TONES)), DEFAULT_TONE),
    "siren_volume": SelectSetting(tuple(VOLUME_LEVELS), DEFAULT_VOLUME),
}

SWITCHES: Mapping[str, bool] = {
    "silent": False,
    "tamper_triggers_alarm": False,
    "auto_disarm_on_arrival": False,
}

TIMES: tuple[str, ...] = ("auto_arm_time", "auto_disarm_time")


class SettingError(ValueError):
    """Ungültiger Schlüssel oder Wert."""


def _stored(options: Mapping[str, Any], profile_id: str) -> Mapping[str, Any]:
    stored = options.get("profiles", {}).get(profile_id, {})
    return stored if isinstance(stored, Mapping) else {}


def read_number(options: Mapping[str, Any], profile_id: str, key: str) -> int:
    setting = NUMBERS[key]
    try:
        value = int(_stored(options, profile_id).get(key, setting.default))
    except (TypeError, ValueError):
        return setting.default
    return value if setting.minimum <= value <= setting.maximum else setting.default


def read_select(options: Mapping[str, Any], profile_id: str, key: str) -> str:
    setting = SELECTS[key]
    value = _stored(options, profile_id).get(key)
    return value if value in setting.options else setting.default


def read_switch(options: Mapping[str, Any], profile_id: str, key: str) -> bool:
    return bool(_stored(options, profile_id).get(key, SWITCHES[key]))


def read_time(options: Mapping[str, Any], profile_id: str, key: str) -> time | None:
    if key not in TIMES:
        raise SettingError(key)
    return parse_time(_stored(options, profile_id).get(key))


def _validated(key: str, value: Any) -> Any:
    if key in NUMBERS:
        setting = NUMBERS[key]
        number = int(value)
        if not setting.minimum <= number <= setting.maximum:
            raise SettingError(f"{key}={value}")
        return number
    if key in SELECTS:
        if value not in SELECTS[key].options:
            raise SettingError(f"{key}={value}")
        return value
    if key in SWITCHES:
        return bool(value)
    if key in TIMES:
        if value is None:
            return None
        if not isinstance(value, time):
            raise SettingError(f"{key}={value}")
        return value.strftime("%H:%M:%S")
    raise SettingError(key)


def write(options: Mapping[str, Any], profile_id: str, key: str, value: Any) -> dict[str, Any]:
    """Neue Optionen mit einer geänderten Einstellung (Original bleibt unverändert)."""
    if profile_id not in options.get("profiles", {}):
        raise SettingError(profile_id)
    new = copy.deepcopy(dict(options))
    new["profiles"][profile_id][key] = _validated(key, value)
    return new
