"""Tests: Sirenentest – Grenzen, Einstellungen, Protokoll, Fälligkeit."""

from __future__ import annotations

from datetime import UTC, datetime

from custom_components.hauswacht.core.siren_test import (
    MAX_SECONDS,
    SirenTestRecord,
    add_months,
    clamp_seconds,
    due_sirens,
    dump_records,
    parse_records,
    parse_settings,
)

NOW = datetime(2026, 11, 12, 12, 0, tzinfo=UTC)


def test_clamp_seconds() -> None:
    assert clamp_seconds(3) == 3
    assert clamp_seconds(30) == MAX_SECONDS
    assert clamp_seconds(0) == 1
    assert clamp_seconds("x") == 3
    assert clamp_seconds(2.7) == 2


def test_settings() -> None:
    assert parse_settings({}).reminder_months == 0
    assert not parse_settings({}).prewarn
    settings = parse_settings({"siren_test": {"reminder_months": "6", "prewarn": True}})
    assert settings.reminder_months == 6
    assert settings.prewarn
    assert parse_settings({"siren_test": {"reminder_months": 5}}).reminder_months == 0


def test_records_roundtrip() -> None:
    records = {"siren.a": SirenTestRecord(at=NOW, heard=True, by="Christian", seconds=3)}
    assert parse_records(dump_records(records)) == records
    assert parse_records({"siren.b": {"at": "kaputt"}, "siren.c": "x"}) == {}


def test_add_months_end_of_month() -> None:
    assert add_months(datetime(2026, 8, 31, tzinfo=UTC), 6).date().isoformat() == "2027-02-28"
    assert add_months(datetime(2026, 11, 12, tzinfo=UTC), 3).month == 2


def test_due_sirens() -> None:
    records = {
        "siren.ok": SirenTestRecord(at=datetime(2026, 10, 1, tzinfo=UTC), heard=True),
        "siren.alt": SirenTestRecord(at=datetime(2026, 1, 1, tzinfo=UTC), heard=True),
        "siren.stumm": SirenTestRecord(at=datetime(2026, 11, 1, tzinfo=UTC), heard=False),
    }
    sirens = ["siren.ok", "siren.alt", "siren.stumm", "siren.neu"]
    assert due_sirens(sirens, records, 6, NOW) == ["siren.alt", "siren.stumm", "siren.neu"]
    assert due_sirens(sirens, records, 0, NOW) == []
