"""Ausgangserkennung (ADR 0014): rein, ohne Home Assistant."""

from __future__ import annotations

from custom_components.hauswacht.core.exit_detection import (
    CONFIRM,
    DEFAULT_WAIT,
    ExitConfig,
    ExitWatch,
    can_leave,
    exit_from_input,
    gone,
    inside_ok,
    parse_exit,
)
from custom_components.hauswacht.core.presence_rules import MODE_ONE, PersonRules, Signal

ANNA = "person.anna"
BEN = "person.ben"
WLAN = "sensor.ben_wlan"
BWM = "binary_sensor.treppe"


def test_parse_defaults_and_limits() -> None:
    assert parse_exit({}, "nacht") == ExitConfig()
    raw = {"profiles": {"nacht": {"exit_detect": {"enabled": True, "wait": 12}}}}
    assert parse_exit(raw, "nacht").wait == 5  # ohne Expertenoption höchstens 5 Minuten
    raw["profiles"]["nacht"]["exit_detect"]["expert"] = True
    assert parse_exit(raw, "nacht").wait == 12
    raw["profiles"]["nacht"]["exit_detect"]["wait"] = 99
    assert parse_exit(raw, "nacht").wait == 15
    assert exit_from_input({"enabled": True, "inside": [BWM, ""]}) == {
        "enabled": True,
        "wait": DEFAULT_WAIT,
        "expert": False,
        "inside": [BWM],
    }


def test_inside_sensor_is_optional() -> None:
    assert inside_ok(ExitConfig(), [], 1000.0)
    with_bwm = ExitConfig(inside=frozenset({BWM}))
    assert inside_ok(with_bwm, [950.0], 1000.0)
    assert not inside_ok(with_bwm, [700.0], 1000.0)  # zu lange her: kam von außen
    assert not inside_ok(with_bwm, [], 1000.0)


def test_can_leave_needs_a_leaving_signal_at_home() -> None:
    rules = PersonRules(leave_off=frozenset({BEN}))
    assert can_leave(rules, [Signal(BEN, True, 0), Signal(WLAN, True, 0)])
    assert not can_leave(rules, [Signal(BEN, True, 0), Signal(WLAN, False, 0)])


def test_gone_one_and_all() -> None:
    one = PersonRules(mode=MODE_ONE)
    signals = [Signal(BEN, True, 0), Signal(WLAN, False, 1010)]
    assert gone(one, signals, 1000.0) == [WLAN]
    assert gone(one, [Signal(WLAN, False, 500)], 1000.0) == []  # war schon vorher weg
    assert gone(PersonRules(), signals, 1000.0) == []  # alle müssen
    assert gone(PersonRules(), [Signal(BEN, False, 0), Signal(WLAN, False, 0)], 1000.0)
    assert gone(PersonRules(), [Signal(BEN, None, 0), Signal(WLAN, False, 0)], 1000.0) == []


def test_watch_needs_30_seconds() -> None:
    watch = ExitWatch(1000.0, "binary_sensor.haustuer", frozenset({ANNA, BEN}))
    watch.note(BEN, True, 1040.0)
    assert watch.left(1040.0 + CONFIRM - 1) is None
    assert watch.left(1040.0 + CONFIRM) == BEN


def test_watch_hiccup_resets() -> None:
    watch = ExitWatch(1000.0, None, frozenset({BEN}))
    watch.note(BEN, True, 1040.0)
    watch.note(BEN, False, 1050.0)  # nach 10 s wieder da
    watch.note(BEN, True, 1060.0)
    assert watch.left(1080.0) is None
    assert watch.left(1090.0) == BEN


def test_watch_ignores_persons_not_home() -> None:
    watch = ExitWatch(1000.0, None, frozenset({ANNA}))
    watch.note(BEN, True, 1010.0)
    assert watch.left(2000.0) is None


def test_wlan_outage_is_not_leaving() -> None:
    watch = ExitWatch(1000.0, None, frozenset({ANNA, BEN}))
    watch.note(ANNA, True, 1010.0, wlan_only=True)
    watch.note(BEN, True, 1020.0, wlan_only=True)
    assert watch.left(1200.0) is None
    # mit einem vom WLAN unabhängigen Signal (Bluetooth, Ortung) zählt es
    watch.note(BEN, True, 1020.0, wlan_only=False)
    assert watch.left(1200.0) is not None
