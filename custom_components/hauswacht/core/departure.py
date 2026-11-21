"""Beobachtung "Weggehen": Wie schnell merken die Signale, dass jemand das Haus verlassen hat?

Rein und ohne Home Assistant, und wie die Heimkehr-Beobachtung SCHALTET SIE NICHTS. Sie ist
die Messung für die spätere Ausgangserkennung (ADR 0014): Wenn eine Tür aufgeht, während
jemand zuhause ist, soll Hauswacht eine stille Wartezeit lang prüfen, ob dessen Handy "weg"
meldet. Dafür braucht es zwei Zahlen je Person:

- **Wie lange dauert es**, bis nach dem Rausgehen ALLE Signale der Person "weg" melden?
  Daraus ergibt sich die empfohlene Wartezeit.
- **Schweigepausen:** Wie oft melden alle Signale "weg", obwohl gar keine Tür aufging
  (schlafendes Handy, WLAN-Aussetzer)? Eine Pause, die länger ist als die Wartezeit, würde
  später einen Einbruch als "Rausgehen" durchgehen lassen – dann gibt es einen Warnhinweis.

Grundsatz: Ohne geöffnete Tür kann niemand weggehen. Ein "Weg" ohne Türöffnung kurz davor
ist deshalb eine Schweigepause.
"""

from __future__ import annotations

import statistics
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from .homecoming import EARLIEST, Arrival, DoorOpening
from .texts import DE, tr

DEPARTURE_WINDOW = 900  # s: so lange vor dem "Weg" darf die Tür aufgegangen sein
DEPARTURE_EARLY = 60  # s: so lange darf ein Signal VOR dem Öffnen "weg" melden (Bluetooth)
SHARED_WINDOW = 60  # s: Pausen mehrerer Personen so nah beieinander = WLAN-/Router-Ausfall
WAIT_MIN = 60  # s: kürzeste einstellbare Wartezeit (1 min)
WAIT_MAX = 900  # s: längste einstellbare Wartezeit (15 min)
MIN_WITH_DOOR = 3  # so oft muss jemand beim Rausgehen gemessen sein
MIN_DAYS = 2.0  # so lange muss beobachtet sein, damit Schweigepausen auffallen können


@dataclass(frozen=True)
class Departure:
    at: float
    person: str
    source: str  # Personen-Entität, einzelne Quelle oder "<person>#frühestes"


@dataclass(frozen=True)
class DepartureVerdict:
    departure: Departure
    door: DoorOpening | None  # None = Schweigepause (keine Tür kurz davor)
    delay: float | None  # s von "Tür auf" bis "weg"; None ohne Tür
    away: float  # s bis zur Rückkehr (oder bis jetzt, wenn noch weg)
    back: bool  # False = noch weg
    shared: bool = False  # Schweigepause gleichzeitig bei einer anderen Person


@dataclass
class DepartureStats:
    departures: int = 0
    with_door: int = 0
    delays: list[float] = field(default_factory=list)
    pauses: list[float] = field(default_factory=list)  # Dauer der Schweigepausen
    shared: int = 0  # davon gleichzeitig bei anderen (WLAN-Ausfall?)

    def as_dict(self) -> dict[str, Any]:
        return {
            "departures": self.departures,
            "with_door": self.with_door,
            "median_seconds": round(statistics.median(self.delays)) if self.delays else None,
            "max_seconds": round(max(self.delays)) if self.delays else None,
            "pauses": len(self.pauses),
            "longest_pause_minutes": round(max(self.pauses) / 60) if self.pauses else None,
            "shared_pauses": self.shared,
        }


def door_before(departure: Departure, doors: Sequence[DoorOpening]) -> DoorOpening | None:
    """Letzte Türöffnung kurz vor (oder knapp nach) dem "Weg"."""
    best: DoorOpening | None = None
    for door in doors:
        if -DEPARTURE_EARLY <= departure.at - door.at <= DEPARTURE_WINDOW and (
            best is None or door.at > best.at
        ):
            best = door
    return best


def _back_at(departure: Departure, arrivals: Sequence[Arrival]) -> float | None:
    """Erste Rückkehr derselben Quelle nach dem "Weg"."""
    times = [
        a.at
        for a in arrivals
        if a.person == departure.person and a.source == departure.source and a.at > departure.at
    ]
    return min(times) if times else None


def judge_departures(
    departures: Iterable[Departure],
    arrivals: Sequence[Arrival],
    doors: Sequence[DoorOpening],
    now: float,
) -> list[DepartureVerdict]:
    items = sorted(departures, key=lambda d: d.at)
    verdicts: list[DepartureVerdict] = []
    for departure in items:
        door = door_before(departure, doors)
        back = _back_at(departure, arrivals)
        verdicts.append(
            DepartureVerdict(
                departure=departure,
                door=door,
                delay=departure.at - door.at if door else None,
                away=(back if back is not None else now) - departure.at,
                back=back is not None,
            )
        )
    # Schweigepausen der Kombination, die bei mehreren Personen gleichzeitig beginnen
    pauses = [v for v in verdicts if v.door is None and v.departure.source.endswith(EARLIEST)]
    shared = {
        id(v)
        for v in pauses
        if any(
            o.departure.person != v.departure.person
            and abs(o.departure.at - v.departure.at) <= SHARED_WINDOW
            for o in pauses
        )
    }
    return [
        DepartureVerdict(
            departure=v.departure,
            door=v.door,
            delay=v.delay,
            away=v.away,
            back=v.back,
            shared=id(v) in shared,
        )
        for v in verdicts
    ]


def departure_stats(verdicts: Iterable[DepartureVerdict]) -> dict[str, DepartureStats]:
    """Statistik pro Quelle (Schlüssel = ``source``)."""
    stats: dict[str, DepartureStats] = {}
    for v in verdicts:
        entry = stats.setdefault(v.departure.source, DepartureStats())
        entry.departures += 1
        if v.delay is not None:
            entry.with_door += 1
            entry.delays.append(max(0.0, v.delay))
        else:
            entry.pauses.append(v.away)
            entry.shared += int(v.shared)
    return stats


def recommended_wait(longest: float) -> int:
    """Längste Zeit bis "weg" plus Puffer (25 %, mindestens 1 min), auf Minuten aufgerundet."""
    padded = longest + max(60.0, longest * 0.25)
    return int(-(-padded // 60) * 60)


def wait_advice(verdicts: Sequence[DepartureVerdict], days: float) -> dict[str, dict[str, Any]]:
    """Je Person (Kombination "frühestes Signal"): Empfehlung für die Wartezeit.

    ``status``:

    - ``few``: noch zu wenig gemessen (weniger als 3× Rausgehen oder unter 2 Tagen)
    - ``ok``: Rausgehen wird zuverlässig erkannt; ``wait`` ist die empfohlene Wartezeit
    - ``slow``: die Signale merken das Rausgehen erst nach mehr als 15 Minuten
    - ``pauses``: alle Signale schweigen manchmal länger als die Wartezeit, ohne dass eine Tür
      aufging. Pausen, die gleichzeitig bei mehreren Personen beginnen (WLAN-Ausfall), zählen
      nicht – dagegen schützt später eine eigene Regel.
    """
    stats = departure_stats(v for v in verdicts if v.departure.source.endswith(EARLIEST))
    advice: dict[str, dict[str, Any]] = {}
    for source, entry in stats.items():
        person = source[: -len(EARLIEST)]
        longest = max(entry.delays) if entry.delays else 0.0
        wait = recommended_wait(longest) if entry.delays else None
        target = min(max(wait or WAIT_MIN, WAIT_MIN), WAIT_MAX)
        own = [
            v.away
            for v in verdicts
            if v.departure.source == source and v.door is None and not v.shared
        ]
        longer = sum(1 for pause in own if pause > target)
        if entry.with_door < MIN_WITH_DOOR or days < MIN_DAYS:
            status = "few"
        elif wait is not None and wait > WAIT_MAX:
            status = "slow"
        elif longer:
            status = "pauses"
        else:
            status = "ok"
        advice[person] = {
            "status": status,
            "with_door": entry.with_door,
            "longest_seconds": round(longest) if entry.delays else None,
            "wait_minutes": round(target / 60) if wait is not None else None,
            "needed_minutes": round(wait / 60) if wait is not None else None,
            "pauses": len(entry.pauses),
            "pauses_longer": longer,
            "shared_pauses": entry.shared,
        }
    return advice


def departure_lines(
    stats: Mapping[str, DepartureStats],
    advice: Mapping[str, Mapping[str, Any]],
    names: Mapping[str, str],
    lang: str = DE,
) -> list[str]:
    """Abschnitt "Weggehen" für den Bericht (leer, solange nichts aufgezeichnet ist)."""
    if not stats:
        return []
    lines = [
        tr(lang, "dep_heading"),
        "",
        tr(lang, "dep_cols"),
        "|---|---|---|---|---|---|",
    ]
    for source in sorted(stats, key=lambda s: names.get(s, s)):
        s = stats[source]
        median = f"{statistics.median(s.delays):.0f} s" if s.delays else "–"
        longest = f"{max(s.delays):.0f} s" if s.delays else "–"
        pause = f"{max(s.pauses) / 60:.0f} min" if s.pauses else "–"
        lines.append(
            f"| {names.get(source, source)} | {s.with_door} | {median} | {longest} | "
            f"{len(s.pauses)} | {pause} |"
        )
    lines += ["", tr(lang, "dep_legend")]
    if advice:
        lines += ["", tr(lang, "dep_advice_heading"), ""]
        for person in sorted(advice, key=lambda p: names.get(p, p)):
            lines.append("- " + advice_text(advice[person], names.get(person, person), lang))
    return lines


def advice_text(advice: Mapping[str, Any], name: str, lang: str = DE) -> str:
    """Ein Satz je Person, passend zum Status der Empfehlung."""
    return tr(
        lang,
        "dep_status_" + str(advice["status"]),
        name=name,
        count=advice["with_door"],
        minutes=advice["wait_minutes"],
        needed=advice["needed_minutes"],
        pauses=advice["pauses_longer"],
    )


def describe_departure(verdict: DepartureVerdict, names: Mapping[str, str], lang: str = DE) -> str:
    who = names.get(verdict.departure.source, verdict.departure.source)
    minutes = f"{verdict.away / 60:.0f}"
    if verdict.door is None or verdict.delay is None:
        key = "dep_pause_shared" if verdict.shared else "dep_pause"
        return tr(lang, key if verdict.back else key + "_open", who=who, minutes=minutes)
    door = names.get(verdict.door.sensor, verdict.door.sensor)
    return tr(lang, "dep_left", who=who, seconds=f"{max(0.0, verdict.delay):.0f}", door=door)


def departure_csv_rows(
    verdicts: Iterable[DepartureVerdict],
    names: Mapping[str, str],
    local: Callable[[float], str],
    lang: str = DE,
) -> list[tuple[float, tuple[str, ...]]]:
    """Zeilen für die CSV-Tabelle der Heimkehr-Beobachtung (gleiche Spalten)."""
    rows: list[tuple[float, tuple[str, ...]]] = []
    for v in verdicts:
        door = names.get(v.door.sensor, v.door.sensor) if v.door else ""
        delay = f"{max(0.0, v.delay):.0f}" if v.delay is not None else ""
        rows.append(
            (
                v.departure.at,
                (
                    tr(lang, "dep_csv_kind"),
                    local(v.departure.at),
                    names.get(v.departure.source, v.departure.source),
                    door,
                    delay,
                    f"{v.away / 60:.0f}",
                    describe_departure(v, names, lang).split(": ", 1)[-1],
                ),
            )
        )
    return rows
