"""Entscheidungen der Profil-Automatik (ADR 0017) – ohne Home Assistant."""

from __future__ import annotations

from custom_components.hauswacht.core.automation import AutoConfig
from custom_components.hauswacht.core.automation_engine import (
    MIN_AWAY_FOR_PASSAGE,
    REASON_ARRIVAL,
    REASON_ARRIVAL_DOOR,
    REASON_AWAY,
    REFRESH,
    AlarmView,
    Arm,
    AutomationEngine,
    CancelTimer,
    Disarm,
    LetIn,
    Note,
    StartTimer,
    arm_allowed,
    disarm_allowed,
)
from custom_components.hauswacht.core.returning import ReturnConfig
from custom_components.hauswacht.core.state_machine import AlarmState

A = "person.anna"
B = "person.ben"
DOOR = "binary_sensor.haustuer"
DISARMED = AlarmView(None, AlarmState.DISARMED)
ARMED = AlarmView("away", AlarmState.ARMED)
PENDING = AlarmView("away", AlarmState.PENDING)


def engine(
    *, away: tuple[str, ...] = (A, B), back: ReturnConfig | None = None, delay: int = 15
) -> AutomationEngine:
    e = AutomationEngine()
    configs = {"away": AutoConfig(away_persons=away, away_delay=delay)} if away else {}
    e.configure(configs, {"away": back} if back else {})
    e.begin({p: True for p in e.persons}, 0.0)
    return e


def test_all_away_schedules_and_cancels() -> None:
    e = engine()
    assert e.presence({A: False, B: True}, 10, DISARMED) == []
    actions = e.presence({A: False, B: False}, 20, DISARMED)
    assert actions == [StartTimer("away", 900), Note("AutoArmScheduled", "away", {"minutes": 15})]
    assert e.away_due == {"away": 20 + 900}
    # schon geplant: kein zweiter Timer
    assert e.presence({A: False, B: False}, 30, DISARMED) == []
    # jemand zurück: abbrechen
    actions = e.presence({A: True, B: False}, 40, DISARMED)
    assert actions == [CancelTimer("away"), Note("AutoArmCancelled", "away")]
    assert e.away_due == {}


def test_unknown_never_counts_as_away() -> None:
    e = engine()
    assert e.presence({A: False, B: None}, 10, DISARMED) == []


def test_away_elapsed_arms_only_if_still_away() -> None:
    e = engine()
    e.presence({A: False, B: False}, 0, DISARMED)
    assert e.away_elapsed("away", [False, True]) == []
    assert e.away_due == {}
    e.presence({A: False, B: False}, 0, DISARMED)
    assert e.away_elapsed("away", [False, False]) == [Arm("away", REASON_AWAY)]


def test_return_auto_only() -> None:
    e = engine(back=ReturnConfig(mode="auto_only", persons=(A,)))
    e.presence({A: False, B: False}, 0, ARMED)
    actions = e.presence({A: True, B: False}, 60, ARMED)
    assert Disarm("away", REASON_ARRIVAL, only_if_auto=True) in actions


def test_return_always_needs_five_minutes_away() -> None:
    e = engine(back=ReturnConfig(mode="always", persons=(A,)))
    e.presence({A: False, B: True}, 0, ARMED)
    assert not [a for a in e.presence({A: True, B: True}, 60, ARMED) if isinstance(a, Disarm)]
    e.presence({A: False, B: True}, 100, ARMED)
    actions = e.presence({A: True, B: True}, 100 + MIN_AWAY_FOR_PASSAGE, ARMED)
    assert next(a for a in actions if isinstance(a, Disarm)).allow_entry


def test_door_proof_arrival_then_door() -> None:
    e = engine(back=ReturnConfig(mode="door", persons=(A,), window=5))
    e.presence({A: False, B: True}, 0, ARMED)
    actions = e.presence({A: True, B: True}, 100, ARMED)
    assert Note("ArrivalNoted", "away", {"persons": [A]}) in actions
    assert not [a for a in actions if isinstance(a, Disarm)]
    actions = e.door_opened(DOOR, 200, PENDING)
    assert Disarm("away", REASON_ARRIVAL_DOOR, allow_entry=True) in actions
    assert actions[-1] is REFRESH
    assert e.arrival_at == {}
    assert e.door_at == {}


def test_door_proof_door_then_arrival_and_window() -> None:
    e = engine(back=ReturnConfig(mode="door", persons=(A,), window=5))
    e.presence({A: False, B: True}, 0, ARMED)
    e.door_opened(DOOR, 1000, PENDING)
    actions = e.presence({A: True, B: True}, 1000 + 4 * 60, PENDING)
    assert Disarm("away", REASON_ARRIVAL_DOOR, allow_entry=True) in actions
    # außerhalb des Zeitfensters: nichts
    e2 = engine(back=ReturnConfig(mode="door", persons=(A,), window=5))
    e2.presence({A: False, B: True}, 0, ARMED)
    e2.door_opened(DOOR, 1000, PENDING)
    assert not [a for a in e2.presence({A: True}, 1000 + 6 * 60, PENDING) if isinstance(a, Disarm)]


def test_door_proof_not_while_disarmed() -> None:
    e = engine(back=ReturnConfig(mode="door", persons=(A,)))
    e.presence({A: False, B: True}, 0, DISARMED)
    actions = e.presence({A: True, B: True}, 100, DISARMED)
    assert actions == []
    assert e.door_opened(DOOR, 110, DISARMED) == [REFRESH]


def test_let_in_only_during_entry_delay() -> None:
    e = engine(back=ReturnConfig(mode="passage", persons=(A,), window=5))
    e.presence({A: False, B: True}, 0, ARMED)
    later = MIN_AWAY_FOR_PASSAGE + 10
    e.presence({A: True, B: True}, later, ARMED)  # Handy zuerst, noch scharf
    actions = e.door_opened(DOOR, later + 20, PENDING)
    assert LetIn("away", A) in actions
    # einmal reinlassen, dann ist die Heimkehr verbraucht
    assert not [a for a in e.door_opened(DOOR, later + 30, PENDING) if isinstance(a, LetIn)]


def test_let_in_needs_long_absence() -> None:
    e = engine(back=ReturnConfig(mode="passage", persons=(A,), window=5))
    e.presence({A: False, B: True}, 0, ARMED)
    e.presence({A: True, B: True}, 60, ARMED)  # nur 1 Minute weg
    assert not [a for a in e.door_opened(DOOR, 70, PENDING) if isinstance(a, LetIn)]


def test_entry_extension_after_approach() -> None:
    back = ReturnConfig(mode="door", persons=(A,), approach_delay=90, approach_valid=15)
    e = engine(back=back)
    assert e.entry_extension("away", 100) == (0, [])
    e.note_approach(A, 100)
    assert e.entry_extension("away", 100 + 14 * 60) == (90, [A])
    assert e.entry_extension("away", 100 + 16 * 60) == (0, [])
    assert e.entry_extension("other", 200) == (0, [])


def test_on_disarmed_clears_proofs() -> None:
    e = engine(back=ReturnConfig(mode="door", persons=(A,)))
    e.auto_armed_by = "away"
    e.presence({A: False, B: True}, 0, ARMED)
    e.presence({A: True, B: True}, 100, ARMED)
    e.on_disarmed()
    assert e.auto_armed_by is None
    assert e.arrival_at == {}


def test_return_report() -> None:
    e = engine(back=ReturnConfig(mode="door", persons=(A,), window=5))
    e.presence({A: False, B: True}, 0, ARMED)
    e.presence({A: True, B: True}, 100, ARMED)
    report = e.return_report("away", 160, ARMED)
    assert report == {"mode": "door", "active": True, "arrival_until": 400, "door_until": None}
    assert e.return_report("away", 160, DISARMED)["arrival_until"] is None


def test_guards() -> None:
    assert arm_allowed(AlarmState.DISARMED, guest=False) is None
    assert arm_allowed(AlarmState.ARMED, guest=False) == "not_disarmed"
    assert arm_allowed(AlarmState.DISARMED, guest=True) == "guest_mode"
    assert disarm_allowed(ARMED, "away", allow_entry=False)
    assert not disarm_allowed(PENDING, "away", allow_entry=False)
    assert disarm_allowed(PENDING, "away", allow_entry=True)
    assert not disarm_allowed(AlarmView("away", AlarmState.TRIGGERED), "away", allow_entry=True)
    assert not disarm_allowed(ARMED, "night", allow_entry=True)


def test_all_away_not_rescheduled_while_armed() -> None:
    """0.64.0b5: nach dem Scharfschalten wird „alle weg“ nicht bei jeder Änderung neu geplant."""
    e = engine()
    e.presence({A: False, B: False}, 0, DISARMED)
    assert e.away_elapsed("away", [False, False]) == [Arm("away", REASON_AWAY)]
    # scharf, alle noch weg: eine Signaländerung plant nichts neu
    assert e.presence({A: False, B: False}, 60, ARMED) == []
    assert e.away_due == {}
    # wieder unscharf (z. B. aus der Ferne), alle noch weg: wieder ganz normal planen
    actions = e.presence({A: False, B: False}, 120, DISARMED)
    assert actions == [StartTimer("away", 900), Note("AutoArmScheduled", "away", {"minutes": 15})]
