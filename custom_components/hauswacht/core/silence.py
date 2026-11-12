"""Funkstille-Beobachtung: wie lange schweigen eure Melder im Normalbetrieb?

Rein und ohne Home Assistant. Je Melder wird die längste Pause zwischen zwei Lebenszeichen
gemerkt. Daraus ergibt sich eine Empfehlung für "Maximale Funkstille" (längste Pause plus
Sicherheitsaufschlag, auf volle Stunden aufgerundet). Die Beobachtung ändert nichts – den Wert
übernimmt man selbst.

Pausen über einen Neustart hinweg zählen nicht: Nach dem Start wird der erste Kontakt nur als
Ausgangspunkt genommen.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

SAFETY_FACTOR = 1.5
MIN_HOURS = 1
MIN_DAYS_FOR_ADVICE = 3.0


@dataclass(frozen=True)
class SilenceRecord:
    longest: float = 0.0  # s
    longest_at: float | None = None  # Ende der längsten Pause
    contacts: int = 0


def update(
    record: SilenceRecord, previous: float | None, contact: float, *, baseline: bool
) -> SilenceRecord:
    """Neuer Kontakt. ``baseline`` = erster Kontakt nach dem Start (keine Pause werten)."""
    if previous is None or baseline or contact <= previous:
        return SilenceRecord(record.longest, record.longest_at, record.contacts + 1)
    gap = contact - previous
    if gap > record.longest:
        return SilenceRecord(gap, contact, record.contacts + 1)
    return SilenceRecord(record.longest, record.longest_at, record.contacts + 1)


def recommend_hours(longest: float) -> int:
    return max(MIN_HOURS, math.ceil(longest * SAFETY_FACTOR / 3600))


def advice(records: Mapping[str, SilenceRecord], days: float) -> int | None:
    """Empfohlene maximale Funkstille in Stunden (None = noch zu wenig Daten)."""
    longest = max((r.longest for r in records.values()), default=0.0)
    if days < MIN_DAYS_FOR_ADVICE or longest <= 0:
        return None
    return recommend_hours(longest)


def format_duration(seconds: float) -> str:
    minutes = round(seconds / 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours} h {minutes:02d} min" if hours else f"{minutes} min"


def dump(records: Mapping[str, SilenceRecord]) -> dict[str, dict[str, Any]]:
    return {
        k: {"longest": r.longest, "longest_at": r.longest_at, "contacts": r.contacts}
        for k, r in records.items()
    }


def load(raw: Any) -> dict[str, SilenceRecord]:
    result: dict[str, SilenceRecord] = {}
    if not isinstance(raw, Mapping):
        return result
    for key, data in raw.items():
        if not isinstance(data, Mapping):
            continue
        try:
            result[str(key)] = SilenceRecord(
                longest=float(data.get("longest", 0.0)),
                longest_at=float(data["longest_at"]) if data.get("longest_at") else None,
                contacts=int(data.get("contacts", 0)),
            )
        except (TypeError, ValueError):
            continue
    return result
