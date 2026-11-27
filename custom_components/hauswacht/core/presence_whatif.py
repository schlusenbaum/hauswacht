"""„Was wäre wenn“ für die Anwesenheit je Person (ADR 0021) – rein, ohne Home Assistant.

Grundlage sind die Messungen der Heimkehr-Beobachtung (Weggehen): wann ein Signal einer Person
von „da“ auf „weg“ wechselte, wann es zurückkam, und wann eine Eingangstür aufging. Damit lassen
sich die Regeln aus ADR 0021 auf den vergangenen Tagen **nachspielen** – ohne etwas zu schalten.

Begriffe:

- **Weggang:** Alle Signale der Person waren weg (Kombination), kurz davor war eine Tür auf, und
  bei der Rückkehr war wieder eine Tür auf (oder die Person ist noch weg). Das ist ein echtes
  Rausgehen.
- **Irrtum:** Ein Signal wechselt auf „weg“ und kommt zurück, **ohne** dass bei der Rückkehr eine
  Tür aufging. Die Person war also gar nicht draußen (schlafendes Handy, WLAN-Aussetzer).
- **Erkannt nach:** Sekunden von der Tür bis die Regel „weg“ sagt.

Alles ist eine **Schätzung**: Hauswacht weiß nicht sicher, wer wirklich draußen war. Bei „alle
müssen weg sein“ kommt im Echtbetrieb noch der Beleg (Ortung) dazu; den kann die Nachrechnung
nicht nachspielen – sie zeigt nur, wann alle Weggehen-Signale weg waren, und rechnet für
diese Regel keine Irrtümer (dagegen schützt der Beleg).
"""

from __future__ import annotations

import statistics
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from itertools import combinations
from typing import Any

from .departure import DEPARTURE_EARLY, DEPARTURE_WINDOW, DepartureVerdict
from .homecoming import EARLIEST, DoorIndex, DoorOpening
from .presence_rules import MODE_ALL, MODE_ONE, PersonRules

EVAL_DAYS = 14  # so weit zurück wird nachgerechnet
MIN_TRIPS = 5  # so viele Weggänge braucht eine Empfehlung
MAX_MISTAKES = 0  # so oft darf „eines reicht“ in den 14 Tagen fälschlich gewesen sein
MIN_DETECTED = 0.8  # so viele Weggänge muss eine Empfehlung erkennen (Anteil)
MAX_SEARCH = 8  # bis zu so vielen Signalen werden alle Kombinationen probiert
SAME_EVENT = 60  # s: Irrtümer mehrerer Signale so nah beieinander zählen einmal
SHORT_TRIP = 10 * 60  # s: so kurz weg = „nur kurz raus“ (Müll, Briefkasten)
NIGHT = range(0, 6)  # Stunden, die als „nachts“ gelten


# „weg“-Zeit für die Haus-Zeile: ab, bis (None = noch weg), fälschlich, Tür davor
Away = tuple[float, float | None, bool, float]
Span = tuple[float, float, bool, float]


@dataclass(frozen=True)
class Flip:
    """Ein Signal wechselte auf „weg“ – und kam vielleicht zurück."""

    at: float
    back: float | None
    door_before: float | None  # letzte Tür kurz davor (bis 15 min, oder knapp danach)
    door_at_back: bool  # bei der Rückkehr war eine Tür auf

    @property
    def mistake(self) -> bool:
        return self.back is not None and not self.door_at_back


@dataclass(frozen=True)
class Trip:
    """Ein echter Weggang: Tür, dann alle weg, Rückkehr mit Tür (oder noch weg)."""

    door: float
    back: float | None


@dataclass(frozen=True)
class Outcome:
    """Ergebnis einer Regel für eine Person."""

    trips: int  # echte Weggänge im Zeitraum
    detected: int  # davon erkannt
    median: float | None  # typische Sekunden Tür -> „weg“
    mistakes: int | None  # vermutlich fälschlich „weg“ (None: Beleg schützt, nicht berechnet)
    night: int  # davon nachts

    def as_dict(self) -> dict[str, Any]:
        return {
            "trips": self.trips,
            "detected": self.detected,
            "median": round(self.median) if self.median is not None else None,
            "mistakes": self.mistakes,
            "night": self.night,
        }


def _door_at(index: DoorIndex, at: float) -> bool:
    return index.latest_between(at - DEPARTURE_WINDOW, at + DEPARTURE_EARLY) is not None


def collect(
    verdicts: Iterable[DepartureVerdict], doors: Sequence[DoorOpening], since: float
) -> tuple[dict[str, list[Trip]], dict[tuple[str, str], list[Flip]]]:
    """Weggänge je Person und Wechsel je (Person, Signal) ab ``since``."""
    index = DoorIndex(doors)
    trips: dict[str, list[Trip]] = {}
    flips: dict[tuple[str, str], list[Flip]] = {}
    for v in sorted(verdicts, key=lambda x: x.departure.at):
        dep = v.departure
        if dep.at < since:
            continue
        back = dep.at + v.away if v.back else None
        door_back = back is not None and _door_at(index, back)
        if dep.source.endswith(EARLIEST):
            if v.door is not None and (back is None or door_back):
                trips.setdefault(dep.person, []).append(Trip(v.door.at, back))
            continue
        flips.setdefault((dep.person, dep.source), []).append(
            Flip(dep.at, back, v.door.at if v.door else None, door_back)
        )
    return trips, flips


def _delay(trip: Trip, flips: Sequence[Flip], now: float) -> float | None:
    """Sekunden von der Tür bis das Signal bei diesem Weggang „weg“ sagte."""
    end = trip.back if trip.back is not None else now
    for flip in flips:
        if trip.door - DEPARTURE_EARLY <= flip.at <= end:
            return max(0.0, flip.at - trip.door)
    return None


def _count_events(times: Iterable[float]) -> list[float]:
    """Zeitpunkte zusammenfassen, die höchstens ``SAME_EVENT`` auseinanderliegen."""
    events: list[float] = []
    for t in sorted(times):
        if not events or t - events[-1] > SAME_EVENT:
            events.append(t)
    return events


@dataclass(frozen=True)
class History:
    """Was für eine Person gemessen wurde – und die Uhr für die Nachrechnung."""

    trips: Sequence[Trip]
    flips: Mapping[str, Sequence[Flip]]  # Signal -> Wechsel auf „weg“
    now: float
    window: float  # s: Zeitfenster nach der Tür (wie „Tür + Signal“)
    is_night: Callable[[float], bool] = lambda _t: False


def simulate(
    rules: PersonRules, signals: Sequence[str], hist: History
) -> tuple[Outcome, list[Away]]:
    """Regel nachspielen. Gibt das Ergebnis und die „weg“-Zeiten zurück:
    (ab, bis, fälschlich, Tür) – für die Haus-Zeile.
    """
    leave = [s for s in signals if rules.leaves(s)]
    delays: list[float] = []
    away: list[Away] = []
    for trip in hist.trips:
        per = [_delay(trip, hist.flips.get(s, ()), hist.now) for s in leave]
        if rules.mode == MODE_ONE:
            ok = [d for d in per if d is not None and (not rules.door or d <= hist.window)]
            found = min(ok) if ok else None
        else:
            known = [d for d in per if d is not None]
            found = max(known) if known and len(known) == len(per) else None
        if found is not None:
            delays.append(found)
            away.append((trip.door + found, trip.back, False, trip.door))
    mistakes: int | None = None
    night = 0
    if rules.mode == MODE_ONE:
        backs: dict[float, float | None] = {}
        for s in leave:
            for flip in hist.flips.get(s, ()):
                if not flip.mistake:
                    continue
                if rules.door and (
                    flip.door_before is None or not 0 <= flip.at - flip.door_before <= hist.window
                ):
                    continue
                backs[flip.at] = flip.back
        events = _count_events(backs)
        mistakes = len(events)
        night = sum(1 for t in events if hist.is_night(t))
        away.extend((t, backs.get(t), True, t) for t in events)
    median = statistics.median(delays) if delays else None
    return Outcome(len(hist.trips), len(delays), median, mistakes, night), away


def signal_summary(signal: str, hist: History) -> dict[str, Any]:
    """Für die Spalte „Gemessen“: wie schnell und wie oft geirrt."""
    flips = hist.flips.get(signal, ())
    delays = [d for t in hist.trips if (d := _delay(t, flips, hist.now)) is not None]
    return {
        "id": signal,
        "trips": len(hist.trips),
        "seen": len(delays),  # bei so vielen Weggängen sagte das Signal „weg“
        "median": round(statistics.median(delays)) if delays else None,
        "mistakes": len(_count_events(f.at for f in flips if f.mistake)),
    }


def _subsets(signals: Sequence[str]) -> list[tuple[str, ...]]:
    """Alle nicht leeren Kombinationen (bei sehr vielen Signalen nur alle und je eines weniger)."""
    if len(signals) > MAX_SEARCH:
        return [tuple(signals), *(tuple(x for x in signals if x != s) for s in signals)]
    return [c for n in range(len(signals), 0, -1) for c in combinations(signals, n)]


def _with_leave(
    rules: PersonRules, signals: Sequence[str], leave: Iterable[str], mode: str
) -> PersonRules:
    off = frozenset(s for s in signals if s not in set(leave))
    return PersonRules(rules.arrive_off, off, mode, door=True)


@dataclass(frozen=True)
class Advice:
    rules: PersonRules  # empfohlene Regel (Haken fürs Weggehen und „Weggehen erkennen“)
    outcome: Outcome
    best_one: tuple[PersonRules, Outcome] | None  # schnellste „eines reicht“, auch wenn verworfen


def _rank(outcome: Outcome) -> tuple[int, float]:
    return (-outcome.detected, outcome.median if outcome.median is not None else 1e12)


def advise(rules: PersonRules, signals: Sequence[str], hist: History) -> Advice:
    """Empfehlung: Welche Signale fürs Weggehen, und reicht eines (nach Tür)?

    Probiert alle Kombinationen von Weggehen-Signalen durch. „Eines reicht (nach Tür)“ wird
    empfohlen, wenn es höchstens ``MAX_MISTAKES``-mal fälschlich gewesen wäre und mindestens
    80 % der Weggänge erkannt hätte – die Kombination, die am meisten erkennt und am schnellsten
    ist. Sonst „alle müssen weg sein“ mit den Signalen, die die meisten Weggänge erkennen.
    Haken fürs Ankommen bleiben, wie sie sind.
    """
    need = max(1, round(len(hist.trips) * MIN_DETECTED))
    best_one: tuple[PersonRules, Outcome] | None = None
    good_one: tuple[PersonRules, Outcome] | None = None
    best_all: tuple[PersonRules, Outcome, int] | None = None
    for subset in _subsets(signals):
        one = _with_leave(rules, signals, subset, MODE_ONE)
        out, _a = simulate(one, signals, hist)
        if best_one is None or (out.mistakes or 0, *_rank(out)) < (
            best_one[1].mistakes or 0,
            *_rank(best_one[1]),
        ):
            best_one = (one, out)
        ok = (out.mistakes or 0) <= MAX_MISTAKES and out.detected >= need
        if ok and (good_one is None or _rank(out) < _rank(good_one[1])):
            good_one = (one, out)
        # „alle müssen“: nur Signale abwählen, die Weggänge verhindern (nie „weg“ sagen) –
        # bei gleich vielen erkannten Weggängen bleiben möglichst viele Signale (Beleg ist Pflicht)
        every = _with_leave(rules, signals, subset, MODE_ALL)
        out_all, _b = simulate(every, signals, hist)
        if best_all is None or (-out_all.detected, -len(subset)) < (
            -best_all[1].detected,
            -best_all[2],
        ):
            best_all = (every, out_all, len(subset))
    if good_one is not None and hist.trips:
        return Advice(good_one[0], good_one[1], best_one)
    if best_all is None or not hist.trips:
        keep = PersonRules(rules.arrive_off, rules.leave_off, MODE_ALL, True)
        out, _c = simulate(keep, signals, hist)
        return Advice(keep, out, best_one)
    # Bei „alle müssen“ nur abwählen, wenn dadurch mehr Weggänge erkannt werden
    keep = PersonRules(rules.arrive_off, rules.leave_off, MODE_ALL, True)
    out_keep, _d = simulate(keep, signals, hist)
    if out_keep.detected >= best_all[1].detected:
        return Advice(keep, out_keep, best_one)
    return Advice(best_all[0], best_all[1], best_one)


def recommend(rules: PersonRules, signals: Sequence[str], hist: History) -> PersonRules:
    """Nur die empfohlene Regel (siehe :func:`advise`)."""
    return advise(rules, signals, hist).rules


def person_whatif(
    person: str, rules: PersonRules, signals: Sequence[str], hist: History
) -> dict[str, Any]:
    """Alles für eine Person: Messwerte je Signal, jetzt / Empfehlung / ohne Tür."""
    own = [person, *signals]
    current, _a = simulate(rules, own, hist)
    advice = advise(rules, own, hist)
    no_door = PersonRules(rules.arrive_off, rules.leave_off, MODE_ONE, door=False)
    without, _c = simulate(no_door, own, hist)
    best_one = None
    if advice.best_one is not None and advice.rules.mode != MODE_ONE:
        one_rules, one_out = advice.best_one
        best_one = {"leave": [s for s in own if one_rules.leaves(s)], **one_out.as_dict()}
    return {
        "person": person,
        "enough": len(hist.trips) >= MIN_TRIPS,
        "trips": len(hist.trips),
        "min_trips": MIN_TRIPS,
        "max_mistakes": MAX_MISTAKES,
        "signals": [signal_summary(s, hist) for s in own],
        "current": current.as_dict(),
        "advice": {
            "mode": advice.rules.mode,
            "door": advice.rules.door,
            "leave_off": sorted(advice.rules.leave_off),
            **advice.outcome.as_dict(),
        },
        "best_one": best_one,  # warum nicht „eines reicht“: so wäre es gewesen
        "no_door": without.as_dict(),
    }


def _union(intervals: Iterable[Span]) -> list[Span]:
    merged: list[Span] = []
    for start, end, wrong, door in sorted(intervals):
        if merged and start <= merged[-1][1]:
            s0, e0, w0, d0 = merged[-1]
            merged[-1] = (s0, max(e0, end), w0 or wrong, d0)
        else:
            merged.append((start, end, wrong, door))
    return merged


def _intersect(a: Sequence[Span], b: Sequence[Span]) -> list[Span]:
    out = []
    for s1, e1, w1, d1 in a:
        for s2, e2, w2, d2 in b:
            start, end = max(s1, s2), min(e1, e2)
            if start < end:
                # die Tür dessen, der als Letzter ging
                out.append((start, end, w1 or w2, d1 if s1 >= s2 else d2))
    return out


def house(
    away: Mapping[str, Sequence[Away]],
    persons: Sequence[str],
    delay_minutes: int,
    now: float,
) -> dict[str, Any]:
    """Wie oft wäre ein Profil mit „Scharf, wenn alle weg“ scharf geworden?

    ``away``: je Person die „weg“-Zeiten aus :func:`simulate`. Das Haus ist leer, wo sich die
    Zeiten **aller** Personen überschneiden; scharf wird es, wenn das mindestens die Wartezeit
    lang so bleibt.

    - ``armed``: so oft scharf
    - ``wrong``: davon war mindestens eine Person vermutlich gar nicht weg
    - ``short``: davon kam jemand nach weniger als 10 Minuten zurück
    - ``after``: typische Minuten von der Tür des Letzten bis „scharf“
    """
    wait = delay_minutes * 60
    empty: list[Span] | None = None
    for person in persons:
        mine = _union((s, e if e is not None else now, w, d) for s, e, w, d in away.get(person, ()))
        empty = mine if empty is None else _intersect(empty, mine)
    armed = [x for x in (empty or []) if x[1] - x[0] >= wait]
    after = [x[0] + wait - x[3] for x in armed if not x[2]]
    return {
        "armed": len(armed),
        "wrong": sum(1 for x in armed if x[2]),
        "short": sum(1 for x in armed if x[1] - (x[0] + wait) < SHORT_TRIP),
        "after": round(statistics.median(after) / 60, 1) if after else None,
    }


@dataclass(frozen=True)
class WhatIfInput:
    verdicts: Sequence[DepartureVerdict]
    doors: Sequence[DoorOpening]
    persons: Sequence[str]  # beobachtete Personen
    signals: Mapping[str, Sequence[str]]
    rules: Mapping[str, PersonRules]
    # Profil -> (Personen bei „Scharf, wenn alle weg“, Wartezeit in Minuten), ohne eigenen Auslöser
    profiles: Mapping[str, tuple[Sequence[str], int]]
    now: float
    window: float
    is_night: Callable[[float], bool] = lambda _t: False


def whatif(data: WhatIfInput) -> dict[str, Any]:
    """Nachrechnung für die Seite „Anwesenheit“: je Person und je Profil."""
    since = data.now - EVAL_DAYS * 86400
    trips, flips = collect(data.verdicts, data.doors, since)
    result: dict[str, Any] = {"days": EVAL_DAYS, "persons": {}, "profiles": {}}
    current_away: dict[str, list[Away]] = {}
    advised_away: dict[str, list[Away]] = {}
    for person in data.persons:
        rule = data.rules.get(person, PersonRules())
        signals = list(data.signals.get(person, ()))
        own = [person, *signals]
        hist = History(
            trips.get(person, []),
            {s: flips.get((person, s), []) for s in own},
            data.now,
            data.window,
            data.is_night,
        )
        result["persons"][person] = person_whatif(person, rule, signals, hist)
        _o, current_away[person] = simulate(rule, own, hist)
        _p, advised_away[person] = simulate(recommend(rule, own, hist), own, hist)
    for pid, (members, delay) in data.profiles.items():
        if not members or any(p not in data.persons for p in members):
            result["profiles"][pid] = {"observed": False}
            continue
        quick = min(delay, 3)
        result["profiles"][pid] = {
            "observed": True,
            "delay": delay,
            "current": house(current_away, members, delay, data.now),
            "advised": house(advised_away, members, delay, data.now),
            "advised_quick": {"delay": quick, **house(advised_away, members, quick, data.now)},
        }
    return result
