"""Messung für die Ausgangserkennung (0.63.1) – Auswertung ohne Home Assistant."""

from __future__ import annotations

from typing import Any

from custom_components.hauswacht.core.departure import Departure, judge_departures
from custom_components.hauswacht.core.exit_check import (
    CHECK_WINDOW,
    LIFE_SIGN_FRESH,
    exit_check_lines,
    exit_check_stats,
    exit_check_text,
    note_life_sign,
    parse_checks,
)
from custom_components.hauswacht.core.homecoming import EARLIEST, DoorOpening
from custom_components.hauswacht.core.texts import DE, EN

NIKLAS = "person.niklas"
PETRA = "person.petra"
DOOR = "binary_sensor.haustuer"
NOW = 100_000.0


def check(at: float, **persons: tuple[float | None, float | None, float | None]) -> dict[str, Any]:
    return {
        "at": at,
        "sensor": DOOR,
        "persons": {
            f"person.{name}": {"age": age, "confirm": confirm, "last": last}
            for name, (age, confirm, last) in persons.items()
        },
    }


def verdicts_for(door_times: list[float], person: str = NIKLAS) -> list[Any]:
    """Niklas geht durch diese Türöffnungen raus (alle Signale „weg“ 120 s danach)."""
    doors = [DoorOpening(at=t, sensor=DOOR) for t in door_times]
    departures = [
        Departure(at=t + 120, person=person, source=person + EARLIEST) for t in door_times
    ]
    return judge_departures(departures, [], doors, NOW)


def test_parse_skips_broken_entries() -> None:
    checks = parse_checks([check(10, niklas=(5, 20, 30)), {"at": "x"}, {"sensor": DOOR}])
    assert len(checks) == 1
    assert checks[0].persons[NIKLAS].age == 5
    assert checks[0].persons[NIKLAS].fresh


def test_note_life_sign_first_and_last() -> None:
    record = check(1000, niklas=(10, None, None))
    assert note_life_sign(record, NIKLAS, 1030)
    assert note_life_sign(record, NIKLAS, 1100)
    entry = record["persons"][NIKLAS]
    assert entry["confirm"] == 30
    assert entry["last"] == 100
    # nach dem Fenster und für Unbekannte: nichts
    assert not note_life_sign(record, NIKLAS, 1000 + CHECK_WINDOW + 1)
    assert not note_life_sign(record, "person.fremd", 1050)


def test_sign_before_leaving_counts_fresh_only() -> None:
    times = [1000.0, 5000.0, 9000.0]
    raw = [
        check(1000, niklas=(20, 5, 90)),  # Lebenszeichen, Ping meldet noch 90 s „zuhause“
        check(5000, niklas=(LIFE_SIGN_FRESH + 50, None, None)),  # zu alt
        check(9000, niklas=(None, None, None)),  # schlief schon
    ]
    stats = exit_check_stats(parse_checks(raw), verdicts_for(times), NOW)[NIKLAS]
    assert stats["left"] == 3
    assert stats["left_with_sign"] == 1
    assert stats["left_echo"] == 1
    assert stats["left_echo_max"] == 90
    assert stats["stayed"] == 0


def test_still_here_for_people_who_stay() -> None:
    raw = [
        check(1000, petra=(30, 20, 600)),
        check(3000, petra=(10, 45, 500)),
        check(6000, petra=(60, None, None)),  # 15 Minuten nichts
        check(8000, petra=(None, 5, 5)),  # ohne Lebenszeichen vorher: zählt nicht
    ]
    stats = exit_check_stats(parse_checks(raw), [], NOW)[PETRA]
    assert stats["stayed"] == 3
    assert stats["confirm_median"] == 32
    assert stats["confirm_max"] == 45
    assert stats["unconfirmed"] == 1


def test_open_checks_are_not_counted_yet() -> None:
    raw = [check(NOW - 60, petra=(10, 5, 5))]
    assert exit_check_stats(parse_checks(raw), [], NOW) == {}


def test_texts_need_enough_data() -> None:
    few = {
        "left": 2,
        "left_with_sign": 2,
        "stayed": 1,
        "confirm_median": 10,
        "confirm_max": 10,
        "unconfirmed": 0,
        "left_echo": 0,
        "left_echo_max": None,
    }
    assert exit_check_text(few, "Niklas", DE) == []
    enough = {**few, "left": 4, "left_with_sign": 1, "stayed": 5, "unconfirmed": 2}
    lines = exit_check_text(enough, "Niklas", DE)
    assert "1 von 4" in lines[0]
    assert "2 von 5" in lines[1]
    assert exit_check_text(enough, "Niklas", EN)[0].startswith("Niklas: when leaving, 1 of 4")


def test_report_section() -> None:
    raw = [check(1000, niklas=(20, 5, 90), petra=(30, 20, 600))]
    stats = exit_check_stats(parse_checks(raw), verdicts_for([1000.0]), NOW)
    lines = exit_check_lines(stats, {NIKLAS: "Niklas", PETRA: "Petra"}, DE)
    assert lines[0].startswith("**Vorbereitung Ausgangserkennung**")
    assert any(line.startswith("| Niklas | 1 / 1 |") for line in lines)
    assert any(line.startswith("| Petra | 0 / 0 | 20 s / 20 s | 0 / 1 |") for line in lines)
    assert exit_check_lines({}, {}, DE) == []
