"""Tests: Funkstille-Beobachtung."""

from __future__ import annotations

from custom_components.hauswacht.core.silence import (
    SilenceRecord,
    advice,
    dump,
    format_duration,
    load,
    recommend_hours,
    update,
)


def test_update_tracks_longest_gap_and_ignores_baseline() -> None:
    record = update(SilenceRecord(), None, 1000.0, baseline=True)
    assert record.longest == 0
    record = update(record, 1000.0, 4600.0, baseline=False)
    assert record.longest == 3600
    record = update(record, 4600.0, 5000.0, baseline=False)
    assert record.longest == 3600
    # Erster Kontakt nach einem Neustart: Pause über den Neustart zählt nicht
    record = update(record, 5000.0, 50000.0, baseline=True)
    assert record.longest == 3600
    assert record.contacts == 4


def test_recommendation() -> None:
    assert recommend_hours(3600) == 2  # 1 h * 1,5 -> 2 h
    assert recommend_hours(60) == 1
    records = {"a": SilenceRecord(longest=7000), "b": SilenceRecord(longest=100)}
    assert advice(records, days=2) is None  # zu wenig Tage
    assert advice(records, days=5) == 3
    assert advice({}, days=10) is None


def test_format_and_roundtrip() -> None:
    assert format_duration(6720) == "1 h 52 min"
    assert format_duration(300) == "5 min"
    records = {"a": SilenceRecord(longest=10.0, longest_at=5.0, contacts=2)}
    assert load(dump(records)) == records
    assert load({"x": "kaputt", "y": {"longest": "x"}}) == {}
