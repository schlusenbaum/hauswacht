"""Tests des Schutzes gegen PIN-Raten."""

from __future__ import annotations

import pytest

from custom_components.hauswacht.core.code_guard import (
    FORGET_AFTER_SECONDS,
    MAX_LOCK_SECONDS,
    CodeGuardState,
    current_failures,
    lock_duration,
    register_failure,
    register_success,
    remaining_lock,
)


@pytest.mark.parametrize(
    ("failures", "expected"),
    [(1, None), (4, None), (5, 60), (6, 120), (7, 240), (8, 480), (9, 900), (20, MAX_LOCK_SECONDS)],
)
def test_lock_duration(failures: int, expected: int | None) -> None:
    assert lock_duration(failures) == expected


def test_warning_from_third_failure() -> None:
    state = CodeGuardState()
    warnings = []
    for _ in range(4):
        result = register_failure(state, now=0.0)
        state = result.state
        warnings.append(result.warn)
    assert warnings == [False, False, True, True]


def test_fifth_failure_locks_for_a_minute() -> None:
    state = CodeGuardState()
    for _ in range(4):
        state = register_failure(state, now=100.0).state
    assert remaining_lock(state, 100.0) == 0
    result = register_failure(state, now=100.0)
    assert result.lock_seconds == 60
    assert remaining_lock(result.state, 100.0) == 60
    assert remaining_lock(result.state, 159.5) == 1
    assert remaining_lock(result.state, 160.0) == 0


def test_success_resets() -> None:
    state = CodeGuardState(failures=7, locked_until=999.0)
    assert register_success(state) == CodeGuardState()


def test_failures_expire_after_a_day() -> None:
    state = CodeGuardState()
    for _ in range(4):
        state = register_failure(state, 1000.0).state
    assert current_failures(state, 1000.0 + FORGET_AFTER_SECONDS) == 4
    later = 1000.0 + FORGET_AFTER_SECONDS + 1
    assert current_failures(state, later) == 0
    # Der nächste Fehlversuch zählt wieder als erster – keine Sperre, keine Warnung
    result = register_failure(state, later)
    assert result.state.failures == 1
    assert result.lock_seconds is None
    assert not result.warn


def test_expiry_window_slides_with_each_failure() -> None:
    state = register_failure(CodeGuardState(), 0.0).state
    state = register_failure(state, FORGET_AFTER_SECONDS - 10).state  # vor Ablauf: zählt weiter
    assert current_failures(state, 2 * FORGET_AFTER_SECONDS - 20) == 2
