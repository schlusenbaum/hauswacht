"""„Was wäre wenn“ für die Anwesenheit je Person (ADR 0021)."""

from __future__ import annotations

from custom_components.hauswacht.core.departure import Departure, judge_departures
from custom_components.hauswacht.core.homecoming import EARLIEST, Arrival, DoorOpening
from custom_components.hauswacht.core.presence_rules import MODE_ALL, MODE_ONE, PersonRules
from custom_components.hauswacht.core.presence_whatif import (
    MIN_TRIPS,
    WhatIfInput,
    house,
    whatif,
)

ANNA = "person.anna"
BEN = "person.ben"
WLAN = "sensor.anna_wlan"
PING = "device_tracker.anna_ping"
DAY = 86400.0
NOW = 20 * DAY


class World:
    """Ausgedachte Messungen: Türen, Wechsel je Signal, Rückkehr."""

    def __init__(self) -> None:
        self.doors: list[DoorOpening] = []
        self.departures: list[Departure] = []
        self.arrivals: list[Arrival] = []

    def door(self, at: float) -> None:
        self.doors.append(DoorOpening(at, "binary_sensor.haustuer"))

    def flip(self, person: str, source: str, at: float, back: float | None) -> None:
        self.departures.append(Departure(at, person, source))
        if back is not None:
            self.arrivals.append(Arrival(back, person, source, back - at))

    def trip(self, person: str, at: float, delays: dict[str, float], back: float) -> None:
        """Echter Weggang: Tür, Signale nach ``delays`` weg, Rückkehr mit Tür."""
        self.door(at)
        for source, delay in delays.items():
            self.flip(person, source, at + delay, back)
        last = at + max(delays.values())
        self.departures.append(Departure(last, person, person + EARLIEST, back))
        self.door(back)

    def run(self, rules: dict[str, PersonRules], profiles=None, persons=(ANNA,)):  # type: ignore[no-untyped-def]
        verdicts = judge_departures(self.departures, self.arrivals, self.doors, NOW)
        return whatif(
            WhatIfInput(
                verdicts=verdicts,
                doors=self.doors,
                persons=list(persons),
                signals={ANNA: [WLAN, PING], BEN: []},
                rules=rules,
                profiles=profiles or {},
                now=NOW,
                window=300,
                is_night=lambda t: (t % DAY) < 6 * 3600,
            )
        )


def _five_trips(world: World) -> None:
    for day in range(7, 12):
        world.trip(
            ANNA, day * DAY + 8 * 3600, {WLAN: 40, PING: 180, ANNA: 600}, day * DAY + 17 * 3600
        )


def test_measured_per_signal() -> None:
    world = World()
    _five_trips(world)
    anna = world.run({})["persons"][ANNA]
    by = {s["id"]: s for s in anna["signals"]}
    assert by[WLAN]["median"] == 40
    assert by[PING]["median"] == 180
    assert by[WLAN]["seen"] == 5
    assert by[WLAN]["mistakes"] == 0
    assert anna["trips"] == 5
    assert anna["enough"]


def test_one_is_faster_and_recommended_without_mistakes() -> None:
    world = World()
    _five_trips(world)
    anna = world.run({})["persons"][ANNA]
    assert anna["current"]["median"] == 600  # alle müssen weg: das langsamste zählt
    assert anna["advice"]["mode"] == MODE_ONE
    assert anna["advice"]["median"] == 40
    assert anna["advice"]["mistakes"] == 0


def test_sleeping_phone_without_door_counts_only_without_door_rule() -> None:
    world = World()
    _five_trips(world)
    world.flip(ANNA, WLAN, 12 * DAY + 2 * 3600, 12 * DAY + 2 * 3600 + 900)  # nachts, keine Tür
    anna = world.run({})["persons"][ANNA]
    assert anna["advice"]["mistakes"] == 0  # „nach Tür“ schützt
    assert anna["no_door"]["mistakes"] == 1
    assert anna["no_door"]["night"] == 1
    assert {s["id"]: s for s in anna["signals"]}[WLAN]["mistakes"] == 1


def test_mistake_after_someone_elses_door_stops_recommendation() -> None:
    world = World()
    _five_trips(world)
    world.door(13 * DAY + 12 * 3600)  # Ben geht raus
    world.flip(ANNA, WLAN, 13 * DAY + 12 * 3600 + 60, 13 * DAY + 13 * 3600)  # Annas WLAN hakt
    anna = world.run({})["persons"][ANNA]
    # WLAN hat sich nach einer Tür geirrt -> eines reicht, aber ohne WLAN fürs Weggehen
    assert anna["advice"]["mode"] == MODE_ONE
    assert anna["advice"]["leave_off"] == [WLAN]
    assert anna["advice"]["mistakes"] == 0
    assert anna["advice"]["median"] == 180
    current = world.run({ANNA: PersonRules(mode=MODE_ONE)})["persons"][ANNA]["current"]
    assert current["mistakes"] == 1


def test_all_signals_wrong_keeps_all_and_says_why() -> None:
    world = World()
    _five_trips(world)
    for i, source in enumerate((WLAN, PING, ANNA)):
        at = 13 * DAY + (10 + i) * 3600
        world.door(at)
        world.flip(ANNA, source, at + 30, at + 1800)  # jedes Signal irrt sich einmal nach Tür
    anna = world.run({})["persons"][ANNA]
    assert anna["advice"]["mode"] == MODE_ALL
    assert anna["advice"]["leave_off"] == []  # nichts abwählen, was nicht hilft
    assert anna["best_one"]["mistakes"] == 1
    assert anna["best_one"]["median"] is not None


def test_too_few_trips_no_recommendation() -> None:
    world = World()
    world.trip(ANNA, 5 * DAY, {WLAN: 40}, 5 * DAY + 3600)
    anna = world.run({})["persons"][ANNA]
    assert not anna["enough"]
    assert anna["min_trips"] == MIN_TRIPS
    assert anna["advice"]["mode"] == MODE_ALL


def test_old_data_is_not_used() -> None:
    world = World()
    world.trip(ANNA, 1 * DAY, {WLAN: 40}, 1 * DAY + 3600)  # älter als 14 Tage
    assert world.run({})["persons"][ANNA]["trips"] == 0


def test_signal_not_for_leaving_is_ignored() -> None:
    world = World()
    _five_trips(world)
    rules = {ANNA: PersonRules(leave_off=frozenset({ANNA}))}
    assert world.run(rules)["persons"][ANNA]["current"]["median"] == 180


def test_house_needs_everyone_and_wait() -> None:
    a = [(100.0, 1000.0, False, 90.0)]
    b = [(300.0, 2000.0, False, 250.0)]
    result = house({ANNA: a, BEN: b}, [ANNA, BEN], 2, 5000.0)
    assert result["armed"] == 1
    assert result["wrong"] == 0
    assert result["after"] == round((300 + 120 - 250) / 60, 1)
    # zu kurz für 15 Minuten Wartezeit
    assert house({ANNA: a, BEN: b}, [ANNA, BEN], 15, 5000.0)["armed"] == 0
    # Ben nie weg -> nie scharf
    assert house({ANNA: a}, [ANNA, BEN], 1, 5000.0)["armed"] == 0


def test_house_marks_wrong_and_short() -> None:
    a = [(100.0, 400.0, True, 100.0)]  # Irrtum
    result = house({ANNA: a}, [ANNA], 1, 5000.0)
    assert result == {"armed": 1, "wrong": 1, "short": 1, "after": None}


def test_profiles_in_result() -> None:
    world = World()
    _five_trips(world)
    result = world.run({}, profiles={"away": ([ANNA], 15), "night": ([ANNA, BEN], 5)})
    away = result["profiles"]["away"]
    assert away["observed"]
    assert away["current"]["armed"] == 5
    assert away["advised_quick"]["delay"] == 3
    assert away["advised"]["after"] < away["current"]["after"]
    assert result["profiles"]["night"] == {"observed": False}  # Ben wird nicht beobachtet
