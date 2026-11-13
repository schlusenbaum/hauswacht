"""Heimkehr-Beobachtung: Auswertung, ob eine Heimkehr-Automatik bei euch zuverlässig wäre.

Rein und ohne Home Assistant. Die Beobachtung SCHALTET NICHTS: Sie sammelt nur Türöffnungen
und Ankünfte (pro Person und pro Ortungsquelle) und rechnet aus, was eine Automatik getan
hätte. So lässt sich vor jeder echten Automatik mit echten Daten entscheiden.

Ortungsquellen sind die Geräte-Tracker der Person und – ab 0.27 – zusätzliche Signale je
Person: Binärsensoren (an = zuhause), WLAN-Sensoren der Companion App (verbunden mit einem der
Heim-WLANs = zuhause) und die Richtung aus der Integration "Nähe" (nähert sich/angekommen =
zuhause, entfernt sich = weg). Je Person gibt es außerdem die Kombination "frühestes Signal"
(irgendeine Quelle meldet zuhause).

Bewertet wird pro Ankunft:

- **mit Tür:** Innerhalb des Zeitfensters wurde eine Eingangstür geöffnet. Die Verzögerung
  ist "Ankunft erkannt" minus "Tür geöffnet" (negativ = vor dem Öffnen erkannt).
  Ist sie größer als die Eingangsverzögerung, hätte es einen FEHLALARM gegeben.
- **ohne Tür:** Keine Türöffnung im Zeitfenster – meist eine Falschmeldung der Ortung.
  Eine Automatik, die Ankunft UND Tür verlangt, ignoriert sie. Fiele sie zufällig mit einer
  fremden Türöffnung zusammen, wäre das ein falsches Unscharf.
"""

from __future__ import annotations

import csv
import io
import statistics
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from .texts import DE, tr

HOME = "home"
IGNORED_STATES = frozenset({"unknown", "unavailable", ""})

DEFAULT_WINDOW = 300  # s: Tür und Ankunft gehören zusammen, wenn so nah beieinander
DEFAULT_MIN_AWAY = 300  # s: kürzere "Weg"-Phasen zählen nicht als Heimkehr
CANDIDATE_DELAYS: tuple[int, ...] = (30, 45, 60, 90, 120, 180)
MAX_AGE = 60 * 86400  # s: ältere Daten werden verworfen
MAX_RECORDS = 5000


DIRECTION_HOME = frozenset({"towards", "arrived"})
DIRECTION_AWAY = frozenset({"away_from"})
DIRECTION_NEUTRAL = frozenset({"stationary"})
APPROACH_WINDOW = 900  # s: Annäherung kommt oft Minuten vor der Tür
EARLIEST = "#frühestes"  # Kennung der Kombination je Person: "<person>#frühestes"


def presence(state: str | None, ssids: frozenset[str] = frozenset()) -> bool | None:
    """True = zuhause, False = weg, None = unbekannt (zählt weder noch).

    - Tracker/Person: ``home`` = zuhause, alles andere (``not_home``, andere Zone) = weg
    - Binärsensor: ``on`` = zuhause, ``off`` = weg
    - Richtung (Nähe): nähert sich/angekommen = zuhause, entfernt sich = weg, steht = unbekannt
    - WLAN-Sensor: Name eines Heim-WLANs = zuhause, sonst weg
    """
    if state is None or state in IGNORED_STATES or state in DIRECTION_NEUTRAL:
        return None
    if state in (HOME, "on") or state in DIRECTION_HOME:
        return True
    if state in ("off", "not_home") or state in DIRECTION_AWAY:
        return False
    return state in ssids


@dataclass(frozen=True)
class DoorOpening:
    at: float
    sensor: str


@dataclass(frozen=True)
class Arrival:
    at: float
    person: str
    source: str  # Personen-Entität (gesamt) oder einzelne Ortungsquelle
    away_seconds: float


@dataclass
class SourceStats:
    arrivals: int = 0
    with_door: int = 0
    without_door: int = 0
    delays: list[float] = field(default_factory=list)

    def on_time(self, entry_delay: int) -> int:
        return sum(1 for d in self.delays if d <= entry_delay)

    def false_alarms(self, entry_delay: int) -> int:
        return self.with_door - self.on_time(entry_delay)

    def as_dict(self) -> dict[str, Any]:
        after = [d for d in self.delays if d > 0]
        return {
            "arrivals": self.arrivals,
            "with_door": self.with_door,
            "without_door": self.without_door,
            "median_delay": round(statistics.median(self.delays)) if self.delays else None,
            "max_delay": round(max(self.delays)) if self.delays else None,
            "detected_after_door": len(after),
            "false_alarms_at": {str(d): self.false_alarms(d) for d in CANDIDATE_DELAYS},
        }


@dataclass(frozen=True)
class Verdict:
    arrival: Arrival
    door: DoorOpening | None
    delay: float | None  # s nach der Türöffnung; None ohne Tür


def nearest_door(
    arrival: Arrival, doors: Sequence[DoorOpening], window: int = DEFAULT_WINDOW
) -> DoorOpening | None:
    best: DoorOpening | None = None
    for door in doors:
        diff = abs(arrival.at - door.at)
        if diff <= window and (best is None or diff < abs(arrival.at - best.at)):
            best = door
    return best


def judge(
    arrivals: Iterable[Arrival],
    doors: Sequence[DoorOpening],
    *,
    min_away: int = DEFAULT_MIN_AWAY,
    window: int = DEFAULT_WINDOW,
    windows: Mapping[str, int] | None = None,
) -> list[Verdict]:
    verdicts: list[Verdict] = []
    for arrival in arrivals:
        if arrival.away_seconds < min_away:
            continue
        door = nearest_door(arrival, doors, (windows or {}).get(arrival.source, window))
        delay = arrival.at - door.at if door else None
        verdicts.append(Verdict(arrival=arrival, door=door, delay=delay))
    return verdicts


def evaluate(
    arrivals: Iterable[Arrival],
    doors: Sequence[DoorOpening],
    *,
    min_away: int = DEFAULT_MIN_AWAY,
    window: int = DEFAULT_WINDOW,
    windows: Mapping[str, int] | None = None,
) -> dict[str, SourceStats]:
    """Statistik pro Ortungsquelle (Schlüssel = ``source``)."""
    stats: dict[str, SourceStats] = {}
    for verdict in judge(arrivals, doors, min_away=min_away, window=window, windows=windows):
        entry = stats.setdefault(verdict.arrival.source, SourceStats())
        entry.arrivals += 1
        if verdict.delay is None:
            entry.without_door += 1
        else:
            entry.with_door += 1
            entry.delays.append(verdict.delay)
    return stats


def doors_without_arrival(
    arrivals: Sequence[Arrival],
    doors: Iterable[DoorOpening],
    *,
    window: int = DEFAULT_WINDOW,
    sources: frozenset[str] | None = None,
) -> int:
    """Türöffnungen ohne Ankunft (Hinausgehen, Besuch, Lüften …) – nur zur Einordnung."""
    relevant = [a for a in arrivals if sources is None or a.source in sources]
    return sum(1 for door in doors if not any(abs(a.at - door.at) <= window for a in relevant))


def describe(verdict: Verdict, name: Mapping[str, str], lang: str = DE) -> str:
    """Kurzer Text, was eine Heimkehr-Automatik getan hätte."""
    who = name.get(verdict.arrival.source, verdict.arrival.source)
    if verdict.delay is None or verdict.door is None:
        return tr(lang, "hc_no_door", who=who)
    door = name.get(verdict.door.sensor, verdict.door.sensor)
    if verdict.delay <= 0:
        return tr(lang, "hc_before", who=who, seconds=f"{-verdict.delay:.0f}", door=door)
    ok = [d for d in CANDIDATE_DELAYS if verdict.delay <= d]
    hint = tr(lang, "hc_enough_from", seconds=ok[0]) if ok else tr(lang, "hc_too_late")
    return tr(lang, "hc_after", who=who, seconds=f"{verdict.delay:.0f}", door=door, hint=hint)


def prune(records: list[dict[str, Any]], now: float) -> list[dict[str, Any]]:
    """Alte Einträge verwerfen und die Menge begrenzen."""
    fresh = [r for r in records if now - float(r.get("at", 0)) <= MAX_AGE]
    return fresh[-MAX_RECORDS:]


def report_markdown(
    stats: Mapping[str, SourceStats],
    names: Mapping[str, str],
    *,
    door_only: int,
    days: float,
    lang: str = DE,
) -> str:
    """Bericht als Markdown-Tabelle (für eine Benachrichtigung in Home Assistant)."""
    if not stats:
        return tr(lang, "hc_none")
    columns = [
        tr(lang, "hc_col_source"),
        tr(lang, "hc_col_arrivals"),
        tr(lang, "hc_col_with_door"),
        tr(lang, "hc_col_without_door"),
        tr(lang, "hc_col_delay"),
        *(tr(lang, "hc_col_false", seconds=d) for d in CANDIDATE_DELAYS),
    ]
    rows = ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
    for source in sorted(stats, key=lambda s: names.get(s, s)):
        s = stats[source]
        median = f"{statistics.median(s.delays):.0f} s" if s.delays else "–"
        cells = [
            names.get(source, source),
            str(s.arrivals),
            str(s.with_door),
            str(s.without_door),
            median,
            *(str(s.false_alarms(d)) for d in CANDIDATE_DELAYS),
        ]
        rows.append("| " + " | ".join(cells) + " |")
    return (
        tr(lang, "hc_summary", days=f"{days:.1f}", door_only=door_only)
        + "\n\n"
        + "\n".join(rows)
        + "\n\n"
        + tr(lang, "hc_legend")
    )


@dataclass(frozen=True)
class PresenceState:
    home: bool | None = None
    away_since: float | None = None


def track(
    prev: PresenceState, state: str | None, now: float, ssids: frozenset[str] = frozenset()
) -> tuple[PresenceState, float | None]:
    """Neuer Anwesenheitszustand; zweiter Wert = Dauer der Abwesenheit bei einer Heimkehr.

    Unbekannte Zustände ändern nichts. Eine Heimkehr zählt nur, wenn vorher eine Abwesenheit
    mit bekanntem Beginn beobachtet wurde.
    """
    value = presence(state, ssids)
    return track_value(prev, value, now)


def track_value(
    prev: PresenceState, value: bool | None, now: float
) -> tuple[PresenceState, float | None]:
    """Wie ``track``, mit bereits bewertetem Zustand (für Kombinationen)."""
    if value is None or value == prev.home:
        return prev, None
    if value:
        away = now - prev.away_since if prev.home is False and prev.away_since else None
        return PresenceState(home=True), away
    return PresenceState(home=False, away_since=now), None


# --- Zeit von "Tür auf" bis "unscharf" -------------------------------------------------


@dataclass(frozen=True)
class EntryTiming:
    """Eine Eingangsverzögerung: wie lange bis zum Unscharfschalten (oder Alarm)."""

    at: float
    door: str
    seconds: float
    in_time: bool  # False = Zeit abgelaufen, Alarm
    delay: int  # eingestellte Eingangsverzögerung


def recommended_entry_delay(longest: float) -> int:
    """Längste gemessene Zeit plus Puffer (25 %, mindestens 5 s), auf 5 s aufgerundet."""
    padded = longest + max(5.0, longest * 0.25)
    return int(-(-padded // 5) * 5)


def entry_stats(timings: Sequence[EntryTiming]) -> dict[str, dict[str, Any]]:
    """Je Tür: Anzahl, rechtzeitig, zu spät, typische und längste Zeit, Empfehlung."""
    by_door: dict[str, list[EntryTiming]] = {}
    for timing in timings:
        by_door.setdefault(timing.door, []).append(timing)
    result: dict[str, dict[str, Any]] = {}
    for door, items in by_door.items():
        done = [t.seconds for t in items if t.in_time]
        result[door] = {
            "entries": len(items),
            "in_time": len(done),
            "too_late": len(items) - len(done),
            "median_seconds": round(statistics.median(done)) if done else None,
            "max_seconds": round(max(done)) if done else None,
            "recommended_entry_delay": recommended_entry_delay(max(done)) if done else None,
        }
    return result


CSV_COLUMNS = (
    "hc_csv_kind",
    "hc_csv_time",
    "hc_csv_who",
    "hc_csv_door",
    "hc_csv_seconds",
    "hc_csv_away",
    "hc_csv_result",
)


def csv_header(lang: str = DE) -> tuple[str, ...]:
    return tuple(tr(lang, key) for key in CSV_COLUMNS)


def csv_rows(
    verdicts: Iterable[Verdict],
    timings: Iterable[EntryTiming],
    names: Mapping[str, str],
    local: Callable[[float], str],
    lang: str = DE,
) -> list[tuple[str, ...]]:
    """Alle Heimkehrten und Eingänge als Tabelle (älteste zuerst), zum Herunterladen.

    ``local`` formatiert einen Zeitstempel (UTC-Sekunden) als Ortszeit.
    """
    rows: list[tuple[float, tuple[str, ...]]] = []
    for v in verdicts:
        door = names.get(v.door.sensor, v.door.sensor) if v.door else ""
        delay = f"{v.delay:.0f}" if v.delay is not None else ""
        result = describe(v, names, lang).split(": ", 1)[-1]
        rows.append(
            (
                v.arrival.at,
                (
                    tr(lang, "hc_csv_arrival"),
                    local(v.arrival.at),
                    names.get(v.arrival.source, v.arrival.source),
                    door,
                    delay,
                    f"{v.arrival.away_seconds / 60:.0f}",
                    result,
                ),
            )
        )
    for t in timings:
        result = tr(lang, "hc_entry_in_time" if t.in_time else "hc_entry_too_late", delay=t.delay)
        rows.append(
            (
                t.at,
                (
                    tr(lang, "hc_csv_entry"),
                    local(t.at),
                    "",
                    names.get(t.door, t.door),
                    f"{t.seconds:.0f}",
                    "",
                    result,
                ),
            )
        )
    return [csv_header(lang), *(row for _at, row in sorted(rows, key=lambda r: r[0]))]


def to_csv(rows: Iterable[Sequence[str]], delimiter: str = ";") -> str:
    """CSV für Excel & Co.: UTF-8 mit BOM; Semikolon (deutsch) bzw. Komma (englisch)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=delimiter, lineterminator="\r\n")
    writer.writerows(rows)
    return "﻿" + buffer.getvalue()
