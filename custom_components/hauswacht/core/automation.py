"""Automatik pro Profil (reine Logik): wann ein Profil von selbst scharf oder unscharf wird.

Gespeichert im jeweiligen Profil:

- ``auto_arm_time`` / ``auto_disarm_time``: Uhrzeit "HH:MM[:SS]" oder leer
- ``auto_weekdays``: Wochentage für die Uhrzeiten (leer = jeden Tag)
- ``auto_away_persons``: Personen; sind alle weg, wird nach ``auto_away_delay`` Minuten
  scharf geschaltet
- ``auto_arrival_mode``: "Unscharf bei Rückkehr" einer dieser Personen
  - ``off``: aus
  - ``auto_only``: wie bisher – nur wenn das Profil zuvor automatisch scharf geschaltet wurde,
    nie in der Eingangsverzögerung (früher ``auto_disarm_on_arrival: true``)
  - ``door``: mit Türbeleg – Rückkehr UND Öffnen einer Eingangstür innerhalb von
    ``auto_arrival_window`` Minuten, egal in welcher Reihenfolge; auch während der
    Eingangsverzögerung, egal wie scharf geschaltet wurde

Anwesenheit je Person: die Person selbst plus die zusätzlichen Signale aus
"Anwesenheit & Heimkehr" (WLAN, Bluetooth, Nähe, Binärsensoren).
- zuhause: irgendein Signal meldet zuhause
- weg: ALLE Signale melden sicher weg (unbekannt oder nicht verfügbar zählt nie als weg)

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

ARRIVAL_OFF = "off"
ARRIVAL_AUTO_ONLY = "auto_only"
ARRIVAL_DOOR = "door"
ARRIVAL_MODES: tuple[str, ...] = (ARRIVAL_OFF, ARRIVAL_AUTO_ONLY, ARRIVAL_DOOR)
DEFAULT_ARRIVAL_WINDOW = 5  # Minuten zwischen Rückkehr und Türöffnung
MAX_ARRIVAL_WINDOW = 30


@dataclass(frozen=True)
class AutoConfig:
    arm_time: time | None = None
    disarm_time: time | None = None
    weekdays: frozenset[str] = frozenset()
    away_persons: tuple[str, ...] = ()
    away_delay: int = DEFAULT_AWAY_DELAY
    arrival_mode: str = ARRIVAL_OFF
    arrival_window: int = DEFAULT_ARRIVAL_WINDOW

    @property
    def disarm_on_arrival(self) -> bool:
        """Irgendeine Form von "Unscharf bei Rückkehr" an (und Personen gewählt)."""
        return self.arrival_mode != ARRIVAL_OFF and bool(self.away_persons)

    @property
    def door_proof(self) -> bool:
        return self.arrival_mode == ARRIVAL_DOOR and bool(self.away_persons)

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
        arrival_mode=arrival_mode(stored),
        arrival_window=_int_in(
            stored.get("auto_arrival_window"), 1, MAX_ARRIVAL_WINDOW, DEFAULT_ARRIVAL_WINDOW
        ),
    )


def arrival_mode(stored: Mapping[str, Any]) -> str:
    """Stufe von "Unscharf bei Rückkehr"; ältere Einstellungen (Schalter) werden übernommen."""
    mode = stored.get("auto_arrival_mode")
    if mode in ARRIVAL_MODES:
        return str(mode)
    return ARRIVAL_AUTO_ONLY if stored.get("auto_disarm_on_arrival") else ARRIVAL_OFF


def _int_in(value: Any, minimum: int, maximum: int, default: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return number if minimum <= number <= maximum else default


def is_active_day(config: AutoConfig, weekday_index: int) -> bool:
    """weekday_index: 0 = Montag (wie datetime.weekday())."""
    return not config.weekdays or WEEKDAYS[weekday_index] in config.weekdays


def overnight(config: AutoConfig) -> bool:
    """Scharf am Abend, unscharf am nächsten Morgen (Unscharf-Uhrzeit vor der Scharf-Uhrzeit)."""
    return (
        config.arm_time is not None
        and config.disarm_time is not None
        and config.disarm_time < config.arm_time
    )


def disarm_due(config: AutoConfig, weekday_index: int) -> bool:
    """Gilt "Unscharf um" heute?

    An einem aktiven Tag immer. Geht das Profil über Nacht (z. B. scharf 23:00, unscharf 06:30),
    zusätzlich am Morgen nach einem aktiven Tag: Bei Mo–Fr wird Freitagnacht scharf geschaltet
    und Samstag früh wieder unscharf – sonst bliebe die Anlage das ganze Wochenende scharf.
    """
    if is_active_day(config, weekday_index):
        return True
    return overnight(config) and is_active_day(config, (weekday_index - 1) % 7)


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


# --- Anwesenheit aus mehreren Signalen ---------------------------------------------------


def person_value(state: str | None) -> bool | None:
    """Personen-Entität: zuhause, weg (andere Zone/not_home) oder unbekannt."""
    if state is None or state in UNKNOWN_STATES or state == "":
        return None
    return state == HOME_STATE


def combine(values: Iterable[bool | None]) -> bool | None:
    """Ein Signal zuhause -> zuhause; alle sicher weg -> weg; sonst unbekannt."""
    items = list(values)
    if any(v is True for v in items):
        return True
    if items and all(v is False for v in items):
        return False
    return None


def all_away_values(values: Iterable[bool | None]) -> bool:
    """Alle Personen sicher weg (unbekannt zählt nicht als weg)."""
    items = list(values)
    return bool(items) and all(v is False for v in items)


def anyone_home_values(values: Iterable[bool | None]) -> bool:
    return any(v is True for v in values)


def door_proof_ok(arrival_at: float | None, door_at: float | None, window_minutes: int) -> bool:
    """Rückkehr und Türöffnung liegen höchstens ``window_minutes`` auseinander."""
    if arrival_at is None or door_at is None:
        return False
    return abs(arrival_at - door_at) <= window_minutes * 60
