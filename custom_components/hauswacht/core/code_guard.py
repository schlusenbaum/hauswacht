"""Schutz gegen das Durchprobieren von PINs (reine Logik).

- Ab der 5. falschen Eingabe in Folge wird die PIN-Eingabe gesperrt: 60 s, danach bei jedem
  weiteren Fehlversuch doppelt so lange, höchstens 15 Minuten.
- Ab der 3. falschen Eingabe in Folge soll gewarnt werden.
- Eine richtige Eingabe setzt alles zurück.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

WARN_AFTER = 3
LOCK_AFTER = 5
FIRST_LOCK_SECONDS = 60
MAX_LOCK_SECONDS = 15 * 60


@dataclass(frozen=True)
class CodeGuardState:
    failures: int = 0
    locked_until: float = 0.0


@dataclass(frozen=True)
class FailureResult:
    state: CodeGuardState
    warn: bool
    lock_seconds: int | None


def remaining_lock(state: CodeGuardState, now: float) -> int:
    """Verbleibende Sperrzeit in ganzen Sekunden (0 = nicht gesperrt)."""
    remaining = state.locked_until - now
    return int(remaining + 0.999) if remaining > 0 else 0


def lock_duration(failures: int) -> int | None:
    if failures < LOCK_AFTER:
        return None
    seconds: int = FIRST_LOCK_SECONDS * (2 ** (failures - LOCK_AFTER))
    return min(seconds, MAX_LOCK_SECONDS)


def register_failure(state: CodeGuardState, now: float) -> FailureResult:
    failures = state.failures + 1
    lock = lock_duration(failures)
    new_state = replace(
        state,
        failures=failures,
        locked_until=now + lock if lock is not None else state.locked_until,
    )
    return FailureResult(state=new_state, warn=failures >= WARN_AFTER, lock_seconds=lock)


def register_success(_state: CodeGuardState) -> CodeGuardState:
    return CodeGuardState()
