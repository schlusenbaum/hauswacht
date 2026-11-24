"""Beobachtung "Weggehen" (ADR 0014) – Auswertung ohne Home Assistant."""

from __future__ import annotations

from typing import Any

from custom_components.hauswacht.core.checks import run_checks
from custom_components.hauswacht.core.departure import (
    Departure,
    DepartureVerdict,
    advice_text,
    departure_csv_rows,
    departure_lines,
    departure_stats,
    judge_departures,
    recommended_wait,
    wait_advice,
)
from custom_components.hauswacht.core.homecoming import EARLIEST, Arrival, DoorOpening
from custom_components.hauswacht.core.texts import DE, EN

NIKLAS = "person.niklas"
FINJA = "person.finja"
DOOR = "binary_sensor.haustuer"
DAY = 86400.0


def dep(at: float, person: str = NIKLAS, source: str | None = None) -> Departure:
    return Departure(at=at, person=person, source=source or person + EARLIEST)


def back(at: float, away: float, person: str = NIKLAS) -> Arrival:
    return Arrival(at=at, person=person, source=person + EARLIEST, away_seconds=away)


def door(at: float) -> DoorOpening:
    return DoorOpening(at=at, sensor=DOOR)


def test_recommended_wait() -> None:
    assert recommended_wait(0) == 60
    assert recommended_wait(150) == 240  # 150 s + 1 min, auf Minuten aufgerundet
    assert recommended_wait(400) == 540  # 400 s + 25 % = 500 s -> 9 min


def test_door_shortly_before_counts_as_leaving() -> None:
    verdicts = judge_departures(
        [dep(1000), dep(5000)], [back(3000, 2000)], [door(880), door(4000)], now=10000
    )
    left, pause = verdicts
    assert left.door == door(880)
    assert left.delay == 120
    assert left.away == 2000
    assert left.back
    # Tür 1000 s vorher ist länger als 15 min her -> Schweigepause, noch nicht zurück
    assert pause.door is None
    assert pause.away == 5000
    assert not pause.back


def test_latest_door_wins_and_signal_may_be_a_bit_early() -> None:
    (v,) = judge_departures([dep(1000)], [], [door(300), door(900)], now=2000)
    assert v.delay == 100
    (early,) = judge_departures([dep(1000)], [], [door(1030)], now=2000)
    assert early.delay == -30  # Bluetooth merkt es knapp vor dem Öffnen
    stats = departure_stats([early])
    assert stats[NIKLAS + EARLIEST].delays == [0.0]


def test_shared_pauses_look_like_wifi_outage() -> None:
    verdicts = judge_departures(
        [dep(1000), dep(1020, FINJA), dep(9000)],
        [back(2800, 1800), back(2800, 1780, FINJA), back(9600, 600)],
        [],
        now=10000,
    )
    assert [v.shared for v in verdicts] == [True, True, False]
    stats = departure_stats(verdicts)
    assert stats[NIKLAS + EARLIEST].shared == 1
    assert len(stats[NIKLAS + EARLIEST].pauses) == 2


def _leaving(delays: list[float], pauses: tuple[float, ...] = ()) -> list[DepartureVerdict]:
    departures: list[Departure] = []
    arrivals: list[Arrival] = []
    doors: list[DoorOpening] = []
    t = 0.0
    for delay in delays:
        t += DAY
        doors.append(door(t))
        departures.append(dep(t + delay))
        arrivals.append(back(t + 3600, 3600 - delay))
    for pause in pauses:
        t += DAY
        departures.append(dep(t))
        arrivals.append(back(t + pause, pause))
    return judge_departures(departures, arrivals, doors, now=t + DAY)


def test_advice_statuses() -> None:
    assert wait_advice(_leaving([60, 90]), days=10)[NIKLAS]["status"] == "few"
    assert wait_advice(_leaving([60, 90, 120]), days=1)[NIKLAS]["status"] == "few"
    ok = wait_advice(_leaving([60, 90, 120], (180,)), days=10)[NIKLAS]
    assert ok["status"] == "ok"
    assert ok["wait_minutes"] == 3  # 120 s + 1 min
    assert ok["pauses"] == 1
    assert ok["pauses_longer"] == 0
    pauses = wait_advice(_leaving([60, 90, 120], (180, 3600, 7200)), days=10)[NIKLAS]
    assert pauses["status"] == "pauses"
    assert pauses["pauses_longer"] == 2
    slow = wait_advice(_leaving([60, 90, 850]), days=10)[NIKLAS]
    assert slow["status"] == "slow"
    assert slow["wait_minutes"] == 15
    assert slow["needed_minutes"] == 18


def test_shared_pauses_do_not_spoil_the_advice() -> None:
    verdicts = _leaving([60, 90, 120])
    outage = judge_departures(
        [v.departure for v in verdicts] + [dep(50 * DAY), dep(50 * DAY + 10, FINJA)],
        [back(50 * DAY + 3600, 3600), back(50 * DAY + 3600, 3590, FINJA)]
        + [back(v.departure.at + v.away, v.away) for v in verdicts],
        [v.door for v in verdicts if v.door],
        now=60 * DAY,
    )
    advice = wait_advice(outage, days=60)[NIKLAS]
    assert advice["status"] == "ok"
    assert advice["shared_pauses"] == 1


def test_report_texts_and_csv() -> None:
    verdicts = _leaving([60, 90, 120], (3600,))
    names = {NIKLAS + EARLIEST: "Niklas (frühestes Signal)", NIKLAS: "Niklas", DOOR: "Haustür"}
    advice = wait_advice(verdicts, days=10)
    lines = departure_lines(departure_stats(verdicts), advice, names, DE)
    assert "| Niklas (frühestes Signal) | 3 | 90 s | 120 s | 1 | 60 min |" in lines
    assert any("Niklas: Alle Signale haben 1× länger als 3 min geschwiegen" in x for x in lines)
    assert departure_lines({}, {}, names) == []
    rows = departure_csv_rows(verdicts, names, lambda at: f"t{at:.0f}", EN)
    assert rows[0][1][0] == "Leaving"
    assert rows[0][1][3] == "Haustür"
    assert rows[-1][1][6].startswith("silent pause without door, 60 min")
    assert "zuverlässig" in advice_text(dict(advice[NIKLAS], status="ok"), "Niklas")


def _overview(status: str) -> dict[str, Any]:
    person = {
        "name": "Niklas",
        "status": status,
        "with_door": 4,
        "wait_minutes": 3,
        "needed_minutes": 3,
        "pauses_longer": 2,
    }
    return {
        "profiles": [],
        "monitoring": {"homecoming": {"leaving": [person]}, "infrastructure": [{"ok": True}]},
    }


def test_checks_show_advice_and_warnings() -> None:
    def codes(status: str) -> list[tuple[str, str]]:
        return [
            (f["code"], f["severity"])
            for f in run_checks(_overview(status), "de")
            if f["code"].startswith("leaving")
        ]

    assert codes("few") == []
    assert codes("ok") == [("leaving_ok", "info")]
    assert codes("slow") == [("leaving_slow", "warning")]
    assert codes("pauses") == [("leaving_pauses", "warning")]
    text = next(f["text"] for f in run_checks(_overview("pauses"), "en") if f["key"] == "Niklas")
    assert "silent 2× for longer than 3 min" in text


def test_departure_right_after_reset_is_not_a_pause() -> None:
    """Weggehen kurz nach dem Zurücksetzen: Die Tür davor ist nicht bekannt – nicht zählen."""
    verdicts = judge_departures(
        [dep(1050), dep(1000 + 40 * 60), dep(1200)], [], [door(1150)], now=5000, doors_since=1000
    )
    assert [v.departure.at for v in verdicts] == [1200, 3400]
    assert verdicts[0].door is not None  # mit Tür: zählt weiter
    assert verdicts[1].door is None  # später ohne Tür: echte Schweigepause
