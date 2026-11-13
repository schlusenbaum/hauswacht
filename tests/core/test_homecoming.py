"""Tests der Heimkehr-Beobachtung (reine Auswertung, schaltet nichts)."""

from __future__ import annotations

from custom_components.hauswacht.core.homecoming import (
    CSV_HEADER,
    Arrival,
    DoorOpening,
    EntryTiming,
    PresenceState,
    csv_rows,
    describe,
    doors_without_arrival,
    entry_stats,
    evaluate,
    judge,
    presence,
    prune,
    recommended_entry_delay,
    report_markdown,
    to_csv,
    track,
)

DOOR = "binary_sensor.haustuer"


def arrival(at: float, source: str = "person.a", away: float = 3600) -> Arrival:
    return Arrival(at=at, person="person.a", source=source, away_seconds=away)


def test_presence_states() -> None:
    assert presence("home") is True
    assert presence("not_home") is False
    assert presence("Schule") is False
    assert presence("unknown") is None
    assert presence("unavailable") is None
    assert presence(None) is None


def test_track_arrival_after_absence() -> None:
    state, away = track(PresenceState(), "home", 0)
    assert away is None  # erster Wert: keine Heimkehr
    state, away = track(state, "not_home", 100)
    assert away is None
    state, away = track(state, "unknown", 200)  # unbekannt ändert nichts
    assert away is None
    state, away = track(state, "home", 700)
    assert away == 600
    assert state.home is True


def test_track_without_known_departure() -> None:
    _, away = track(PresenceState(home=False), "home", 50)
    assert away is None


def test_delay_relative_to_nearest_door() -> None:
    doors = [DoorOpening(1000, DOOR)]
    stats = evaluate([arrival(1040), arrival(990, source="person.b")], doors)
    assert stats["person.a"].delays == [40]
    assert stats["person.b"].delays == [-10]


def test_arrival_without_door_and_short_absence() -> None:
    doors = [DoorOpening(1000, DOOR)]
    stats = evaluate([arrival(5000), arrival(1010, away=60)], doors)
    assert stats["person.a"].arrivals == 1  # die kurze Abwesenheit zählt nicht
    assert stats["person.a"].without_door == 1


def test_false_alarms_per_entry_delay() -> None:
    doors = [DoorOpening(0, DOOR), DoorOpening(10000, DOOR), DoorOpening(20000, DOOR)]
    arrivals = [arrival(20), arrival(10050), arrival(20100)]
    s = evaluate(arrivals, doors)["person.a"]
    assert s.false_alarms(30) == 2
    assert s.false_alarms(60) == 1
    assert s.false_alarms(120) == 0
    assert s.as_dict()["false_alarms_at"]["45"] == 2


def test_doors_without_arrival() -> None:
    doors = [DoorOpening(0, DOOR), DoorOpening(10000, DOOR)]
    assert doors_without_arrival([arrival(30)], doors) == 1


def test_describe() -> None:
    doors = [DoorOpening(1000, DOOR)]
    names = {"person.a": "Anna", DOOR: "Haustür"}
    texts = [describe(v, names) for v in judge([arrival(1050), arrival(9000)], doors)]
    assert (
        texts[0]
        == "Anna: 50 s nach dem Öffnen (Haustür) erkannt – reicht ab 60 s Eingangsverzögerung"
    )
    assert texts[1] == "Anna: Ankunft ohne Türöffnung – würde ignoriert"


def test_prune_by_age_and_count() -> None:
    records = [{"at": 0}, {"at": 100 * 86400}]
    assert prune(records, 100 * 86400) == [{"at": 100 * 86400}]


def test_report() -> None:
    doors = [DoorOpening(0, DOOR)]
    stats = evaluate([arrival(40)], doors)
    text = report_markdown(stats, {"person.a": "Anna"}, door_only=3, days=2)
    assert "| Anna | 1 | 1 | 0 | 40 s |" in text
    assert report_markdown({}, {}, door_only=0, days=0) == "Noch keine Heimkehr aufgezeichnet."


# --- 0.27: weitere Signale, Fenster je Quelle, Tür bis unscharf -----------------------


def test_presence_for_more_signal_kinds() -> None:
    ssids = frozenset({"Heimnetz"})
    assert presence("on") is True
    assert presence("off") is False
    assert presence("Heimnetz", ssids) is True
    assert presence("<not connected>", ssids) is False
    assert presence("Nachbar", ssids) is False
    assert presence("towards") is True
    assert presence("arrived") is True
    assert presence("away_from") is False
    assert presence("stationary") is None
    assert presence("home") is True
    assert presence("Arbeit") is False


def test_window_per_source() -> None:
    doors = [DoorOpening(at=1000.0, sensor="binary_sensor.tuer")]
    arrivals = [Arrival(at=500.0, person="p", source="s", away_seconds=3600)]
    assert evaluate(arrivals, doors)["s"].without_door == 1
    wide = evaluate(arrivals, doors, windows={"s": 900})
    assert wide["s"].with_door == 1
    assert wide["s"].delays == [-500.0]


def test_entry_stats() -> None:
    timings = [
        EntryTiming(at=1, door="d", seconds=12, in_time=True, delay=30),
        EntryTiming(at=2, door="d", seconds=20, in_time=True, delay=30),
        EntryTiming(at=3, door="d", seconds=30, in_time=False, delay=30),
    ]
    stats = entry_stats(timings)["d"]
    assert stats["entries"] == 3
    assert stats["too_late"] == 1
    assert stats["max_seconds"] == 20
    assert stats["recommended_entry_delay"] == 25
    assert recommended_entry_delay(40) == 50


# --- 0.36: Bericht zum Herunterladen ---------------------------------------------------


def test_csv_rows_sorted_with_arrivals_and_entries() -> None:
    doors = [DoorOpening(100, DOOR)]
    verdicts = judge([arrival(140), arrival(9000, away=7200)], doors)
    timings = [EntryTiming(at=101, door=DOOR, seconds=12, in_time=True, delay=30)]
    names = {"person.a": "Anna", DOOR: "Haustür"}
    rows = csv_rows(verdicts, timings, names, lambda at: f"t{at:.0f}")
    assert rows[0] == CSV_HEADER
    assert [r[0] for r in rows[1:]] == ["Eingang", "Heimkehr", "Heimkehr"]
    assert rows[1] == (
        "Eingang",
        "t101",
        "",
        "Haustür",
        "12",
        "",
        "rechtzeitig unscharf (Verzögerung 30 s)",
    )
    assert rows[2][1:6] == ("t140", "Anna", "Haustür", "40", "60")
    assert "nach dem Öffnen" in rows[2][6]
    assert rows[3][3:5] == ("", "")  # ohne Tür
    assert "ohne Türöffnung" in rows[3][6]


def test_to_csv_for_german_excel() -> None:
    text = to_csv([("A", "B"), ("1", "x; y")])
    assert text.startswith("\ufeff")
    assert text == '\ufeffA;B\r\n1;"x; y"\r\n'
