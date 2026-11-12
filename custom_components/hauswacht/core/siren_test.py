"""Sirenentest: Grenzen, Einstellungen, Protokoll und Fälligkeit.

Rein und ohne Home Assistant. Der Test selbst geht durch den Sirenen-Guard wie ein echter
Alarm (Hardware-Freigabe, Testmodus, Brandsperre, Einbruchtöne); hier stehen nur die
zusätzlichen Grenzen des Tests:

- immer nur eine Sirene auf einmal, mehrere nacheinander mit Bestätigung
- höchstens ``MAX_SECONDS`` Sekunden, Standard ``DEFAULT_SECONDS``
- nur, wenn alle Bereiche unscharf sind und kein Alarm läuft

Gespeichert unter ``options["siren_test"]``::

    reminder_months: 0 | 3 | 6 | 12     Erinnerung "Sirenentest fällig" (0 = aus)
    prewarn: bool                       Vorwarnung an alle vor dem ersten Ton
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .siren_guard import BURGLAR_TONE_ORDER, VOLUME_LEVELS

MAX_SECONDS = 10
DEFAULT_SECONDS = 3
DEFAULT_VOLUME = "low"
DEFAULT_TONE = BURGLAR_TONE_ORDER[0]
REMINDER_CHOICES = (0, 3, 6, 12)
PREWARN_SECONDS = 10
VOLUMES = tuple(VOLUME_LEVELS)
TONES = BURGLAR_TONE_ORDER


@dataclass(frozen=True)
class SirenTestSettings:
    reminder_months: int = 0
    prewarn: bool = False


def parse_settings(options: Mapping[str, Any]) -> SirenTestSettings:
    raw = options.get("siren_test", {})
    raw = raw if isinstance(raw, Mapping) else {}
    try:
        months = int(raw.get("reminder_months", 0))
    except (TypeError, ValueError):
        months = 0
    return SirenTestSettings(
        reminder_months=months if months in REMINDER_CHOICES else 0,
        prewarn=bool(raw.get("prewarn", False)),
    )


def clamp_seconds(value: Any) -> int:
    """Testdauer in Sekunden, immer zwischen 1 und ``MAX_SECONDS``."""
    try:
        seconds = int(float(value))
    except (TypeError, ValueError):
        return DEFAULT_SECONDS
    return max(1, min(MAX_SECONDS, seconds))


@dataclass(frozen=True)
class SirenTestRecord:
    at: datetime
    heard: bool | None  # None = keine Rückmeldung
    by: str | None = None
    seconds: int = DEFAULT_SECONDS
    volume: str = DEFAULT_VOLUME


def parse_records(raw: Any) -> dict[str, SirenTestRecord]:
    result: dict[str, SirenTestRecord] = {}
    if not isinstance(raw, Mapping):
        return result
    for siren, data in raw.items():
        if not isinstance(data, Mapping):
            continue
        try:
            at = datetime.fromisoformat(str(data["at"]))
        except (KeyError, ValueError):
            continue
        heard = data.get("heard")
        result[str(siren)] = SirenTestRecord(
            at=at,
            heard=heard if isinstance(heard, bool) else None,
            by=data.get("by") if isinstance(data.get("by"), str) else None,
            seconds=clamp_seconds(data.get("seconds", DEFAULT_SECONDS)),
            volume=str(data.get("volume", DEFAULT_VOLUME)),
        )
    return result


def dump_records(records: Mapping[str, SirenTestRecord]) -> dict[str, dict[str, Any]]:
    return {
        siren: {
            "at": record.at.isoformat(),
            "heard": record.heard,
            "by": record.by,
            "seconds": record.seconds,
            "volume": record.volume,
        }
        for siren, record in records.items()
    }


def add_months(moment: datetime, months: int) -> datetime:
    month_index = moment.month - 1 + months
    year = moment.year + month_index // 12
    month = month_index % 12 + 1
    for day in (moment.day, 30, 29, 28):
        try:
            return moment.replace(year=year, month=month, day=day)
        except ValueError:
            continue
    return moment.replace(year=year, month=month, day=28)


def due_sirens(
    sirens: Iterable[str],
    records: Mapping[str, SirenTestRecord],
    months: int,
    now: datetime,
) -> list[str]:
    """Sirenen, deren Test fällig ist: nie getestet, nicht gehört oder zu lange her."""
    if months <= 0:
        return []
    due = []
    for siren in sirens:
        record = records.get(siren)
        if record is None or record.heard is not True or add_months(record.at, months) <= now:
            due.append(siren)
    return due
