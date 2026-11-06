"""Heimkehr-Beobachtung: Auswertung, ob eine Heimkehr-Automatik bei euch zuverlässig wäre.

Rein und ohne Home Assistant. Die Beobachtung SCHALTET NICHTS: Sie sammelt nur Türöffnungen
und Ankünfte (pro Person und pro Ortungsquelle) und rechnet aus, was eine Automatik getan
hätte. So lässt sich vor jeder echten Automatik mit echten Daten entscheiden.

Bewertet wird pro Ankunft:

- **mit Tür:** Innerhalb des Zeitfensters wurde eine Eingangstür geöffnet. Die Verzögerung
  ist "Ankunft erkannt" minus "Tür geöffnet" (negativ = vor dem Öffnen erkannt).
  Ist sie größer als die Eingangsverzögerung, hätte es einen FEHLALARM gegeben.
- **ohne Tür:** Keine Türöffnung im Zeitfenster – meist eine Falschmeldung der Ortung.
  Eine Automatik, die Ankunft UND Tür verlangt, ignoriert sie. Fiele sie zufällig mit einer
  fremden Türöffnung zusammen, wäre das ein falsches Unscharf.
"""

from __future__ import annotations

import statistics
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

HOME = "home"
IGNORED_STATES = frozenset({"unknown", "unavailable", ""})

DEFAULT_WINDOW = 300  # s: Tür und Ankunft gehören zusammen, wenn so nah beieinander
DEFAULT_MIN_AWAY = 300  # s: kürzere "Weg"-Phasen zählen nicht als Heimkehr
CANDIDATE_DELAYS: tuple[int, ...] = (30, 45, 60, 90, 120, 180)
MAX_AGE = 60 * 86400  # s: ältere Daten werden verworfen
MAX_RECORDS = 5000


def presence(state: str | None) -> bool | None:
    """True = zuhause, False = weg, None = unbekannt (zählt weder noch)."""
    if state is None or state in IGNORED_STATES:
        return None
    return state == HOME


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
) -> list[Verdict]:
    verdicts: list[Verdict] = []
    for arrival in arrivals:
        if arrival.away_seconds < min_away:
            continue
        door = nearest_door(arrival, doors, window)
        delay = arrival.at - door.at if door else None
        verdicts.append(Verdict(arrival=arrival, door=door, delay=delay))
    return verdicts


def evaluate(
    arrivals: Iterable[Arrival],
    doors: Sequence[DoorOpening],
    *,
    min_away: int = DEFAULT_MIN_AWAY,
    window: int = DEFAULT_WINDOW,
) -> dict[str, SourceStats]:
    """Statistik pro Ortungsquelle (Schlüssel = ``source``)."""
    stats: dict[str, SourceStats] = {}
    for verdict in judge(arrivals, doors, min_away=min_away, window=window):
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


def describe(verdict: Verdict, name: Mapping[str, str]) -> str:
    """Kurzer Text, was eine Heimkehr-Automatik getan hätte."""
    who = name.get(verdict.arrival.source, verdict.arrival.source)
    if verdict.delay is None or verdict.door is None:
        return f"{who}: Ankunft ohne Türöffnung – würde ignoriert"
    door = name.get(verdict.door.sensor, verdict.door.sensor)
    if verdict.delay <= 0:
        return f"{who}: {-verdict.delay:.0f} s VOR dem Öffnen ({door}) erkannt"
    ok = [d for d in CANDIDATE_DELAYS if verdict.delay <= d]
    hint = f"reicht ab {ok[0]} s Eingangsverzögerung" if ok else "zu spät für jede Verzögerung"
    return f"{who}: {verdict.delay:.0f} s nach dem Öffnen ({door}) erkannt – {hint}"


def prune(records: list[dict[str, Any]], now: float) -> list[dict[str, Any]]:
    """Alte Einträge verwerfen und die Menge begrenzen."""
    fresh = [r for r in records if now - float(r.get("at", 0)) <= MAX_AGE]
    return fresh[-MAX_RECORDS:]


def report_markdown(
    stats: Mapping[str, SourceStats], names: Mapping[str, str], *, door_only: int, days: float
) -> str:
    """Bericht als Markdown-Tabelle (für eine Benachrichtigung in Home Assistant)."""
    if not stats:
        return "Noch keine Heimkehr aufgezeichnet."
    header = "| Quelle | Heimkehr | mit Tür | ohne Tür | typ. Verzögerung | " + " | ".join(
        f"Fehlalarme bei {d} s" for d in CANDIDATE_DELAYS
    )
    rows = [header + " |", "|" + "---|" * (5 + len(CANDIDATE_DELAYS))]
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
        f"Beobachtet: {days:.1f} Tage. Türöffnungen ohne Heimkehr: {door_only}.\n\n"
        + "\n".join(rows)
        + "\n\n**Fehlalarme**: Heimkehr erst nach Ablauf der Eingangsverzögerung erkannt. "
        "**ohne Tür**: Ankunft ohne Türöffnung (meist Falschmeldung der Ortung)."
    )


@dataclass(frozen=True)
class PresenceState:
    home: bool | None = None
    away_since: float | None = None


def track(prev: PresenceState, state: str | None, now: float) -> tuple[PresenceState, float | None]:
    """Neuer Anwesenheitszustand; zweiter Wert = Dauer der Abwesenheit bei einer Heimkehr.

    Unbekannte Zustände ändern nichts. Eine Heimkehr zählt nur, wenn vorher eine Abwesenheit
    mit bekanntem Beginn beobachtet wurde.
    """
    value = presence(state)
    if value is None or value == prev.home:
        return prev, None
    if value:
        away = now - prev.away_since if prev.home is False and prev.away_since else None
        return PresenceState(home=True), away
    return PresenceState(home=False, away_since=now), None
