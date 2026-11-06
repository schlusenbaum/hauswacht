"""Automatik pro Profil (reine Logik): wann ein Profil von selbst scharf oder unscharf wird.

Gespeichert im jeweiligen Profil:

- ``auto_arm_time`` / ``auto_disarm_time``: Uhrzeit "HH:MM[:SS]" oder leer
- ``auto_weekdays``: Wochentage für die Uhrzeiten (leer = jeden Tag)
- ``auto_away_persons``: Personen; sind alle weg, wird nach ``auto_away_delay`` Minuten
  scharf geschaltet
- ``auto_disarm_on_arrival``: unscharf, sobald eine dieser Personen heimkommt
  (nur wenn das Profil zuvor automatisch scharf geschaltet wurde)

Sicherheitsregeln:
- Automatisch scharf geschaltet wird nur aus "unscharf" heraus, nie über ein anderes Profil.
- Offene Sensoren werden automatisch nie bestätigt – dann wird nur gemeldet.
- Eine Person mit unbekanntem oder nicht verfügbarem Aufenthalt gilt NICHT als weg.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import time
from typing import Any

WEEKDAYS: tuple[str, ...] = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
HOME_STATE = "home"
UNKNOWN_STATES = frozenset({"unavailable", "unknown"})
DEFAULT_AWAY_DELAY = 15  # Minuten
MAX_AWAY_DELAY = 240


@dataclass(frozen=True)
class AutoConfig:
    arm_time: time | None = None
    disarm_time: time | None = None
    weekdays: frozenset[str] = frozenset()
    away_persons: tuple[str, ...] = ()
    away_delay: int = DEFAULT_AWAY_DELAY
    disarm_on_arrival: bool = False

    @property
    def enabled(self) -> bool:
        return bool(self.arm_time or self.disarm_time or self.away_persons)


def parse_time(value: Any) -> time | None:
    if not isinstance(value, str) or not value.strip():
        return None
    parts = value.strip().split(":")
    if len(parts) not in (2, 3):
        return None
    try:
        numbers = [int(p) for p in parts]
        return time(numbers[0], numbers[1], numbers[2] if len(numbers) == 3 else 0)
    except ValueError:
        return None


def parse_automation(options: Mapping[str, Any], profile_id: str) -> AutoConfig:
    stored = options.get("profiles", {}).get(profile_id, {})
    if not isinstance(stored, Mapping):
        return AutoConfig()
    days = stored.get("auto_weekdays", [])
    persons = stored.get("auto_away_persons", [])
    delay = stored.get("auto_away_delay", DEFAULT_AWAY_DELAY)
    try:
        delay_int = int(delay)
    except (TypeError, ValueError):
        delay_int = DEFAULT_AWAY_DELAY
    if not 1 <= delay_int <= MAX_AWAY_DELAY:
        delay_int = DEFAULT_AWAY_DELAY
    return AutoConfig(
        arm_time=parse_time(stored.get("auto_arm_time")),
        disarm_time=parse_time(stored.get("auto_disarm_time")),
        weekdays=frozenset(d for d in days if d in WEEKDAYS)
        if isinstance(days, list)
        else frozenset(),
        away_persons=tuple(dict.fromkeys(p for p in persons if isinstance(p, str)))
        if isinstance(persons, list)
        else (),
        away_delay=delay_int,
        disarm_on_arrival=bool(stored.get("auto_disarm_on_arrival", False)),
    )


def is_active_day(config: AutoConfig, weekday_index: int) -> bool:
    """weekday_index: 0 = Montag (wie datetime.weekday())."""
    return not config.weekdays or WEEKDAYS[weekday_index] in config.weekdays


def all_away(person_states: Iterable[str | None]) -> bool:
    """True nur, wenn ALLE Personen sicher nicht zu Hause sind.

    Ein unbekannter Aufenthalt zählt nicht als weg (sichere Seite: lieber nicht automatisch
    scharf schalten, als jemanden im Haus einzuschließen).
    """
    states = list(person_states)
    if not states:
        return False
    return all(s is not None and s not in UNKNOWN_STATES and s != HOME_STATE for s in states)


def anyone_home(person_states: Iterable[str | None]) -> bool:
    return any(s == HOME_STATE for s in person_states)
