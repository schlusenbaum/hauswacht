"""Anwesenheit je Person (ADR 0021): Ankommen/Weggehen je Signal, „eines reicht (nach Tür)“."""

from __future__ import annotations

import itertools

from custom_components.hauswacht.core.away_proof import (
    PROOF_ONE,
    PROOF_ONE_DOOR,
    AwayTracker,
    Fix,
    ProofSettings,
)
from custom_components.hauswacht.core.presence_rules import (
    MODE_ONE,
    OPT_ARRIVE_OFF,
    OPT_LEAVE_MODE,
    OPT_LEAVE_NO_DOOR,
    OPT_LEAVE_OFF,
    PersonRules,
    Signal,
    dump_presence_rules,
    parse_presence_rules,
)

ANNA = "person.anna"
WLAN = "sensor.anna_wlan"
PING = "device_tracker.anna_ping"
BLE = "device_tracker.anna_ble"
GPS = "device_tracker.anna_gps"


def tracker(rules: PersonRules | None = None, **settings: object) -> AwayTracker:
    t = AwayTracker(ProofSettings(**settings))  # type: ignore[arg-type]
    if rules is not None:
        t.rules = {ANNA: rules}
    return t


def sig(entity: str, value: bool | None, since: float = 0.0) -> Signal:
    return Signal(entity, value, since)


# --- Optionen ---------------------------------------------------------------------------------


def test_parse_empty_options_gives_no_rules() -> None:
    assert parse_presence_rules({}) == {}


def test_parse_and_dump_roundtrip() -> None:
    options = {
        OPT_ARRIVE_OFF: {ANNA: [GPS]},
        OPT_LEAVE_OFF: {ANNA: [BLE]},
        OPT_LEAVE_MODE: {ANNA: "one"},
        OPT_LEAVE_NO_DOOR: [ANNA],
    }
    rules = parse_presence_rules(options)
    assert rules == {ANNA: PersonRules(frozenset({GPS}), frozenset({BLE}), MODE_ONE, door=False)}
    assert dump_presence_rules(rules) == options


def test_parse_ignores_garbage_and_defaults() -> None:
    options = {
        OPT_ARRIVE_OFF: {ANNA: "kaputt", "person.ben": []},
        OPT_LEAVE_MODE: {ANNA: "schnell"},
        OPT_LEAVE_NO_DOOR: "x",
        OPT_LEAVE_OFF: [],
    }
    assert parse_presence_rules(options) == {}


# --- Ohne Regeln: genau wie bisher -------------------------------------------------------------


def test_default_rules_behave_like_judge() -> None:
    """Jede Folge von Signalwerten ergibt mit und ohne ADR 0021 dasselbe."""
    values = (True, False, None)
    fix = Fix(True, True, 0.0)
    for seq in itertools.product(itertools.product(values, repeat=2), repeat=4):
        old, new = AwayTracker(), AwayTracker()
        old.note_door(1.0)
        new.note_door(1.0)
        for step, (a, b) in enumerate(seq):
            now = 10.0 + step * 60
            combined = True if True in (a, b) else False if (a, b) == (False, False) else None
            expected = old.judge(ANNA, combined, [fix], now)
            got = new.judge_signals(ANNA, [sig(WLAN, a), sig(PING, b)], [fix], now)
            assert got == expected, seq


# --- Ankommen und Weggehen getrennt -------------------------------------------------------------


def test_bluetooth_only_for_arriving_does_not_keep_anna_home() -> None:
    """Bluetooth sieht durch die Tür: fürs Weggehen abgewählt, darf es nicht zuhause halten."""
    t = tracker(PersonRules(leave_off=frozenset({BLE})))
    assert t.judge_signals(ANNA, [sig(WLAN, True), sig(BLE, True)], [], 0.0) is True
    t.note_door(100.0)
    fix = Fix(True, True, 150.0)
    # WLAN weg, Bluetooth sagt weiter „da“ (seit vorhin) – Beleg: Tür + Ortung
    assert t.judge_signals(ANNA, [sig(WLAN, False, 140.0), sig(BLE, True, 0.0)], [fix], 160.0) is (
        False
    )
    # Bluetooth sagt weiter „da“, aber nicht neu – Anna bleibt weg
    assert t.judge_signals(ANNA, [sig(WLAN, False, 140.0), sig(BLE, True, 0.0)], [], 900.0) is (
        False
    )


def test_arriving_signal_counts_again_after_it_changed() -> None:
    t = tracker(PersonRules(leave_off=frozenset({BLE})))
    t.judge_signals(ANNA, [sig(WLAN, True), sig(BLE, True)], [], 0.0)
    t.note_door(100.0)
    t.judge_signals(
        ANNA, [sig(WLAN, False, 140.0), sig(BLE, True)], [Fix(True, True, 150.0)], 160.0
    )
    # Bluetooth war kurz weg und ist jetzt wieder da (nach dem Weggehen) -> Ankommen
    assert t.judge_signals(ANNA, [sig(WLAN, False, 140.0), sig(BLE, True, 2000.0)], [], 2001.0)


def test_signal_only_for_leaving_never_makes_home() -> None:
    t = tracker(PersonRules(arrive_off=frozenset({GPS})))
    assert t.judge_signals(ANNA, [sig(WLAN, False), sig(GPS, True, 50.0)], [], 60.0) is None


# --- „eines reicht (nach Tür)“ ------------------------------------------------------------------


def test_one_signal_after_door_is_enough() -> None:
    t = tracker(PersonRules(mode=MODE_ONE))
    assert t.judge_signals(ANNA, [sig(WLAN, True), sig(PING, True)], [], 0.0) is True
    t.note_door(100.0)
    t.note_signal_left(ANNA, 140.0, WLAN)
    # Ping sagt noch „da“ – trotzdem weg, ohne Ortung
    assert t.judge_signals(ANNA, [sig(WLAN, False, 140.0), sig(PING, True)], [], 141.0) is False
    assert t.kind(ANNA) == (PROOF_ONE_DOOR, 141.0)
    # Ping sagt weiter „da“ (seit vorher) – bleibt weg
    assert t.judge_signals(ANNA, [sig(WLAN, False, 140.0), sig(PING, True)], [], 200.0) is False


def test_one_signal_without_door_is_not_enough() -> None:
    t = tracker(PersonRules(mode=MODE_ONE))
    t.judge_signals(ANNA, [sig(WLAN, True), sig(PING, True)], [], 0.0)
    t.note_signal_left(ANNA, 140.0, WLAN)  # Handy schläft nachts ein
    assert t.judge_signals(ANNA, [sig(WLAN, False, 140.0), sig(PING, True)], [], 141.0) is True


def test_one_signal_too_long_after_door_is_not_enough() -> None:
    t = tracker(PersonRules(mode=MODE_ONE), weak_window=5)
    t.judge_signals(ANNA, [sig(WLAN, True), sig(PING, True)], [], 0.0)
    t.note_door(100.0)
    t.note_signal_left(ANNA, 100.0 + 5 * 60 + 1, WLAN)
    assert t.judge_signals(ANNA, [sig(WLAN, False, 401.0), sig(PING, True)], [], 402.0) is True


def test_door_before_coming_home_does_not_count() -> None:
    t = tracker(PersonRules(mode=MODE_ONE))
    t.note_door(100.0)  # Anna kommt rein
    t.judge_signals(ANNA, [sig(WLAN, True, 150.0), sig(PING, True)], [], 150.0)
    t.note_signal_left(ANNA, 200.0, WLAN)  # Handy schläft danach ein – keine neue Tür
    assert t.judge_signals(ANNA, [sig(WLAN, False, 200.0), sig(PING, True)], [], 201.0) is True


def test_one_without_door_when_switched_off() -> None:
    t = tracker(PersonRules(mode=MODE_ONE, door=False))
    t.judge_signals(ANNA, [sig(WLAN, True), sig(PING, True)], [], 0.0)
    t.note_signal_left(ANNA, 140.0, WLAN)
    assert t.judge_signals(ANNA, [sig(WLAN, False, 140.0), sig(PING, True)], [], 141.0) is False
    assert t.kind(ANNA) == (PROOF_ONE, 141.0)


def test_signal_must_still_be_away() -> None:
    t = tracker(PersonRules(mode=MODE_ONE))
    t.judge_signals(ANNA, [sig(WLAN, True), sig(PING, True)], [], 0.0)
    t.note_door(100.0)
    t.note_signal_left(ANNA, 140.0, WLAN)
    # WLAN ist schon wieder da, bevor bewertet wird
    assert t.judge_signals(ANNA, [sig(WLAN, True, 145.0), sig(PING, True)], [], 146.0) is True


def test_unknown_signal_never_counts_as_away() -> None:
    t = tracker(PersonRules(mode=MODE_ONE))
    t.judge_signals(ANNA, [sig(WLAN, True), sig(PING, True)], [], 0.0)
    t.note_door(100.0)
    t.note_signal_left(ANNA, 140.0, WLAN)
    assert t.judge_signals(ANNA, [sig(WLAN, None, 140.0), sig(PING, True)], [], 141.0) is True


def test_signal_not_for_leaving_does_not_trigger() -> None:
    t = tracker(PersonRules(mode=MODE_ONE, leave_off=frozenset({WLAN})))
    t.judge_signals(ANNA, [sig(WLAN, True), sig(PING, True)], [], 0.0)
    t.note_door(100.0)
    t.note_signal_left(ANNA, 140.0, WLAN)
    assert t.judge_signals(ANNA, [sig(WLAN, False, 140.0), sig(PING, True)], [], 141.0) is True


def test_trigger_coming_back_means_mistake() -> None:
    """Das auslösende Signal ist wieder da -> Irrtum, zuhause – auch wenn es nur fürs Weggehen
    zählt."""
    t = tracker(PersonRules(mode=MODE_ONE, arrive_off=frozenset({GPS})))
    t.judge_signals(ANNA, [sig(WLAN, True), sig(GPS, True)], [], 0.0)
    t.note_door(100.0)
    t.note_signal_left(ANNA, 140.0, GPS)
    assert t.judge_signals(ANNA, [sig(WLAN, True), sig(GPS, False, 140.0)], [], 141.0) is False
    assert t.judge_signals(ANNA, [sig(WLAN, True), sig(GPS, True, 300.0)], [], 301.0) is True


def test_arriving_after_one_brings_home() -> None:
    t = tracker(PersonRules(mode=MODE_ONE))
    t.judge_signals(ANNA, [sig(WLAN, True), sig(PING, True)], [], 0.0)
    t.note_door(100.0)
    t.note_signal_left(ANNA, 140.0, WLAN)
    t.judge_signals(ANNA, [sig(WLAN, False, 140.0), sig(PING, True)], [], 141.0)
    t.note_signal_left(ANNA, 300.0, PING)
    assert t.judge_signals(ANNA, [sig(WLAN, False, 140.0), sig(PING, False, 300.0)], [], 301.0) is (
        False
    )
    # Ping wieder da -> zuhause
    assert t.judge_signals(ANNA, [sig(WLAN, False, 140.0), sig(PING, True, 5000.0)], [], 5001.0)


def test_one_still_allows_all_with_proof() -> None:
    """„eines reicht“ ist nie langsamer: alle weg mit Beleg geht weiterhin."""
    t = tracker(PersonRules(mode=MODE_ONE))
    t.judge_signals(ANNA, [sig(WLAN, True)], [], 0.0)
    fix = Fix(True, True, 5000.0)
    assert t.judge_signals(ANNA, [sig(WLAN, False, 4000.0)], [fix], 5001.0) is False
