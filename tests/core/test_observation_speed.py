"""Auswertung der Beobachtung: gleiches Ergebnis wie "jede mit jeder", aber schnell.

Bei Wochen voller Daten lief die Auswertung früher Sekunden lang – bei jeder Signaländerung und
im Ereignis-Takt von Home Assistant. Diese Tests vergleichen das schnelle Verfahren mit dem
einfachen und halten fest, dass es schnell bleibt.
"""

from __future__ import annotations

import random
import time

from custom_components.hauswacht.core.departure import (
    DEPARTURE_EARLY,
    DEPARTURE_WINDOW,
    Departure,
    door_before,
    judge_departures,
)
from custom_components.hauswacht.core.homecoming import (
    EARLIEST,
    Arrival,
    DoorOpening,
    doors_without_arrival,
    judge,
    nearest_door,
)

DAY = 86400.0


def _data(n: int, seed: int = 7) -> tuple[list[Arrival], list[DoorOpening], list[Departure]]:
    rnd = random.Random(seed)
    span = 60 * DAY
    persons = ["person.a", "person.b"]
    sources = ["s1", "s2", "person.a#frühestes", "person.b#frühestes"]
    doors = sorted(
        (
            DoorOpening(at=float(int(rnd.uniform(0, span))), sensor=f"d{rnd.randint(1, 2)}")
            for _ in range(n)
        ),
        key=lambda d: d.at,
    )
    arrivals = [
        Arrival(
            at=rnd.uniform(0, span),
            person=rnd.choice(persons),
            source=rnd.choice(sources),
            away_seconds=rnd.uniform(0, 7200),
        )
        for _ in range(n)
    ]
    departures = [
        Departure(at=rnd.uniform(0, span), person=rnd.choice(persons), source=rnd.choice(sources))
        for _ in range(n)
    ]
    return arrivals, doors, departures


def test_same_result_as_simple_comparison() -> None:
    arrivals, doors, departures = _data(600)
    fast = judge(arrivals, doors, windows={"person.a#frühestes": 900})
    for verdict in fast:
        window = 900 if verdict.arrival.source == "person.a#frühestes" else 300
        simple = nearest_door(verdict.arrival, doors, window)
        assert (verdict.door.at if verdict.door else None) == (simple.at if simple else None)
    now = 61 * DAY
    for left in judge_departures(departures, arrivals, doors, now):
        before = door_before(left.departure, doors)
        assert (left.door.at if left.door else None) == (before.at if before else None)
        back = [
            a.at
            for a in arrivals
            if a.person == left.departure.person
            and a.source == left.departure.source
            and a.at > left.departure.at
        ]
        expected = (min(back) if back else now) - left.departure.at
        assert abs(left.away - expected) < 1e-6
    assert DEPARTURE_EARLY < DEPARTURE_WINDOW
    simple_count = sum(1 for d in doors if not any(abs(a.at - d.at) <= 300 for a in arrivals))
    assert doors_without_arrival(arrivals, doors) == simple_count
    assert EARLIEST == "#frühestes"


def test_fast_with_full_storage() -> None:
    arrivals, doors, departures = _data(5000)
    start = time.perf_counter()
    judge(arrivals, doors)
    judge_departures(departures, arrivals, doors, 61 * DAY)
    assert time.perf_counter() - start < 0.5  # früher: mehrere Sekunden
