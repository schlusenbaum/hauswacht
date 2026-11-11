"""Zentrale Zustandsmaschine der Einbruchmeldeanlage.

Die Zustandsmaschine ist die einzige maßgebliche Instanz für den Anlagenzustand.
Sie ist eine reine Funktion::

    neuer_kontext, effekte = step(kontext, ereignis, now)

- Sie führt selbst keine Aktionen aus (keine Timer, keine Sirenen, keine Pushes).
  Stattdessen liefert sie *Effekte*, die eine äußere Schicht ausführt.
- Zeit wird als ``now`` (monotone Sekunden) übergeben, damit Tests deterministisch sind.
- Timer werden über ein Token abgesichert: Ein abgelaufener Timer, dessen Token nicht
  mehr aktuell ist (z. B. weil inzwischen unscharf geschaltet wurde), wird ignoriert.
- Welche Sensoren in einem Profil aktiv sind, entscheidet die Sensorbewertung
  außerhalb. Die Zustandsmaschine erhält nur Auslösungen mit ihrer Rolle.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum
from typing import ClassVar

# ---------------------------------------------------------------------------
# Grundtypen
# ---------------------------------------------------------------------------


class AlarmState(StrEnum):
    """Interne Anlagenzustände."""

    DISARMED = "disarmed"
    ARMING = "arming"  # Ausgangsverzögerung läuft
    ARMED = "armed"
    PENDING = "pending"  # Eingangsverzögerung läuft
    TRIGGERED = "triggered"  # Alarm, Reaktionsphase (Sirenen/Benachrichtigungen) läuft
    ALARM_HOLD = "alarm_hold"  # Reaktionsphase vorbei, Alarm noch nicht quittiert


class SensorRole(StrEnum):
    """Rolle eines Sensors bei der Alarmbewertung."""

    ENTRY = "entry"  # startet die Eingangsverzögerung
    INSTANT = "instant"  # löst sofort aus
    FOLLOWER = "follower"  # verzögert nur, wenn bereits eine Eingangsverzögerung läuft
    TAMPER_24H = "tamper_24h"  # Manipulation, wird immer gemeldet


class OpenSensorPolicy(StrEnum):
    """Umgang mit offenen Sensoren beim Scharfschalten."""

    REFUSE = "refuse"  # Scharfschaltung verweigern
    CONFIRM = "confirm"  # nur nach bewusster Bestätigung, Sensor wird überbrückt
    BYPASS_AUTO = "bypass_auto"  # automatisch überbrücken (wird gemeldet)


class UnavailableSensorPolicy(StrEnum):
    """Umgang mit nicht verfügbaren Sensoren beim Scharfschalten."""

    REFUSE = "refuse"
    CONFIRM = "confirm"


class TimerKind(StrEnum):
    EXIT_DELAY = "exit_delay"
    ENTRY_DELAY = "entry_delay"
    REACTION = "reaction"


@dataclass(frozen=True)
class ProfileRuntime:
    """Die für die Zustandsmaschine relevanten Werte eines Profils."""

    profile_id: str
    exit_delay: int = 0
    entry_delay: int = 0
    reaction_time: int = 180
    open_policy: OpenSensorPolicy = OpenSensorPolicy.REFUSE
    unavailable_policy: UnavailableSensorPolicy = UnavailableSensorPolicy.REFUSE
    max_alarm_cycles: int = 1  # Anzahl Reaktionszyklen inkl. des ersten
    tamper_triggers_alarm: bool = False

    def __post_init__(self) -> None:
        if not self.profile_id:
            raise ValueError("profile_id darf nicht leer sein")
        if self.exit_delay < 0 or self.entry_delay < 0:
            raise ValueError("Verzögerungen dürfen nicht negativ sein")
        if self.reaction_time <= 0:
            raise ValueError("reaction_time muss größer als 0 sein")
        if self.max_alarm_cycles < 1:
            raise ValueError("max_alarm_cycles muss mindestens 1 sein")


@dataclass(frozen=True)
class Readiness:
    """Ergebnis der Bereitschaftsprüfung (kommt von der Sensorbewertung)."""

    open_sensors: frozenset[str] = frozenset()
    unavailable_sensors: frozenset[str] = frozenset()


@dataclass(frozen=True)
class AlarmContext:
    """Vollständiger Zustand der Zustandsmaschine (unveränderlich)."""

    state: AlarmState = AlarmState.DISARMED
    profile: ProfileRuntime | None = None
    bypassed: frozenset[str] = frozenset()
    # Nach "Alarm beenden" überbrückt, bis der Sensor wieder geschlossen ist
    bypassed_until_closed: frozenset[str] = frozenset()
    accepted_unavailable: frozenset[str] = frozenset()
    timer_token: int = 0
    timer_kind: TimerKind | None = None
    deadline: float | None = None
    alarm_cycles: int = 0
    trigger_sensor: str | None = None
    test_mode: bool = False
    # Alarm durch einen immer aktiven Melder im unscharfen Zustand: "Alarm beenden" -> unscharf
    return_to_disarmed: bool = False


# ---------------------------------------------------------------------------
# Ereignisse (Eingang)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Startup:
    """Home Assistant / Integration wurde (neu) gestartet."""

    previous_profile_id: str | None = None  # war die Anlage vorher scharf?
    test_mode: bool = False  # Testmodus bleibt über Neustarts erhalten


@dataclass(frozen=True)
class ArmRequested:
    profile: ProfileRuntime
    readiness: Readiness = Readiness()
    confirmed: bool = False


@dataclass(frozen=True)
class DisarmRequested:
    """Unscharf schalten. Während eines Alarms: nur den Alarm beenden, scharf bleiben."""

    code_valid: bool = True
    # Sensoren des Profils, die gerade offen sind (für "Alarm beenden")
    open_sensors: frozenset[str] = frozenset()


@dataclass(frozen=True)
class SensorClosed:
    """Ein überwachter Sensor ist wieder geschlossen bzw. in Ruhe."""

    sensor_key: str


@dataclass(frozen=True)
class SensorTriggered:
    sensor_key: str
    role: SensorRole


@dataclass(frozen=True)
class AlwaysActiveTriggered:
    """Ein immer aktiver Melder hat ausgelöst (auch im unscharfen Zustand).

    ``profile`` liefert die Reaktion, wenn die Anlage unscharf ist (eigene Einstellungen für
    "Immer aktiv"). Ist sie scharf, gilt die Reaktion des aktiven Profils.
    """

    sensor_key: str
    profile: ProfileRuntime


@dataclass(frozen=True)
class ExitDelayElapsed:
    token: int
    readiness: Readiness = Readiness()


@dataclass(frozen=True)
class EntryDelayElapsed:
    token: int


@dataclass(frozen=True)
class ReactionTimeElapsed:
    token: int


@dataclass(frozen=True)
class SetTestMode:
    enabled: bool


Event = (
    Startup
    | ArmRequested
    | DisarmRequested
    | SensorTriggered
    | AlwaysActiveTriggered
    | SensorClosed
    | ExitDelayElapsed
    | EntryDelayElapsed
    | ReactionTimeElapsed
    | SetTestMode
)

# ---------------------------------------------------------------------------
# Effekte (Ausgang)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StateChanged:
    old: AlarmState
    new: AlarmState
    cause: str


@dataclass(frozen=True)
class Rejected:
    reason: str
    open_sensors: frozenset[str] = frozenset()
    unavailable_sensors: frozenset[str] = frozenset()


@dataclass(frozen=True)
class ConfirmationRequired:
    open_sensors: frozenset[str]
    unavailable_sensors: frozenset[str]


@dataclass(frozen=True)
class SensorsBypassed:
    sensors: frozenset[str]


@dataclass(frozen=True)
class AlarmAcknowledged:
    """Alarm beendet, das Profil bleibt scharf."""

    profile_id: str
    bypassed_until_closed: frozenset[str]


@dataclass(frozen=True)
class SensorsRestored:
    """Überbrückte Sensoren sind wieder geschlossen und werden wieder überwacht."""

    sensors: frozenset[str]


@dataclass(frozen=True)
class ArmingAborted:
    open_sensors: frozenset[str]
    unavailable_sensors: frozenset[str]


@dataclass(frozen=True)
class StartTimer:
    kind: TimerKind
    token: int
    seconds: int


@dataclass(frozen=True)
class CancelTimer:
    token: int


@dataclass(frozen=True)
class ActivateReaction:
    """Alarmreaktion ausführen. Der Sirenen-Guard entscheidet, was davon real passiert."""

    profile_id: str
    cycle: int
    sensor_key: str
    test_mode: bool


@dataclass(frozen=True)
class StopReaction:
    profile_id: str
    test_mode: bool


@dataclass(frozen=True)
class TamperDetected:
    sensor_key: str
    state: AlarmState


@dataclass(frozen=True)
class RestartedDisarmed:
    previous_profile_id: str


@dataclass(frozen=True)
class TestModeChanged:
    __test__: ClassVar[bool] = False  # kein pytest-Testfall

    enabled: bool


@dataclass(frozen=True)
class Ignored:
    reason: str


Effect = (
    StateChanged
    | Rejected
    | ConfirmationRequired
    | SensorsBypassed
    | AlarmAcknowledged
    | SensorsRestored
    | ArmingAborted
    | StartTimer
    | CancelTimer
    | ActivateReaction
    | StopReaction
    | TamperDetected
    | RestartedDisarmed
    | TestModeChanged
    | Ignored
)

Result = tuple[AlarmContext, tuple[Effect, ...]]

# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


def _start_timer(
    ctx: AlarmContext, kind: TimerKind, seconds: int, now: float
) -> tuple[AlarmContext, StartTimer]:
    token = ctx.timer_token + 1
    new_ctx = replace(ctx, timer_token=token, timer_kind=kind, deadline=now + seconds)
    return new_ctx, StartTimer(kind=kind, token=token, seconds=seconds)


def _cancel_timer(ctx: AlarmContext) -> tuple[AlarmContext, list[Effect]]:
    if ctx.timer_kind is None:
        return ctx, []
    cancelled = ctx.timer_token
    new_ctx = replace(ctx, timer_token=cancelled + 1, timer_kind=None, deadline=None)
    return new_ctx, [CancelTimer(token=cancelled)]


def _goto(ctx: AlarmContext, new_state: AlarmState, cause: str) -> tuple[AlarmContext, Effect]:
    return replace(ctx, state=new_state), StateChanged(old=ctx.state, new=new_state, cause=cause)


def _profile(ctx: AlarmContext) -> ProfileRuntime:
    if ctx.profile is None:  # pragma: no cover - Programmierfehler
        raise RuntimeError(f"Zustand {ctx.state} ohne Profil")
    return ctx.profile


@dataclass(frozen=True)
class _ReadinessVerdict:
    allowed: bool
    needs_confirmation: bool
    refused: bool
    bypass: frozenset[str]
    accepted_unavailable: frozenset[str]


def evaluate_readiness(
    profile: ProfileRuntime,
    readiness: Readiness,
    *,
    confirmed: bool,
    already_bypassed: frozenset[str] = frozenset(),
    already_accepted_unavailable: frozenset[str] = frozenset(),
) -> _ReadinessVerdict:
    """Bewertet offene und nicht verfügbare Sensoren gemäß den Profil-Policies."""
    open_new = readiness.open_sensors - already_bypassed
    unavailable_new = readiness.unavailable_sensors - already_accepted_unavailable

    refused = False
    needs_confirmation = False

    if unavailable_new:
        if profile.unavailable_policy is UnavailableSensorPolicy.REFUSE:
            refused = True
        elif not confirmed:
            needs_confirmation = True

    if open_new:
        if profile.open_policy is OpenSensorPolicy.REFUSE:
            refused = True
        elif profile.open_policy is OpenSensorPolicy.CONFIRM and not confirmed:
            needs_confirmation = True

    allowed = not refused and not needs_confirmation
    return _ReadinessVerdict(
        allowed=allowed,
        needs_confirmation=needs_confirmation and not refused,
        refused=refused,
        bypass=already_bypassed | (open_new if allowed else frozenset()),
        accepted_unavailable=already_accepted_unavailable
        | (unavailable_new if allowed else frozenset()),
    )


def _trigger(ctx: AlarmContext, sensor_key: str, now: float, cause: str) -> Result:
    profile = _profile(ctx)
    effects: list[Effect] = []
    ctx, cancel = _cancel_timer(ctx)
    effects += cancel
    ctx, changed = _goto(ctx, AlarmState.TRIGGERED, cause)
    effects.append(changed)
    cycle = ctx.alarm_cycles + 1
    ctx = replace(ctx, alarm_cycles=cycle, trigger_sensor=sensor_key)
    ctx, timer = _start_timer(ctx, TimerKind.REACTION, profile.reaction_time, now)
    effects.append(timer)
    effects.append(
        ActivateReaction(
            profile_id=profile.profile_id,
            cycle=cycle,
            sensor_key=sensor_key,
            test_mode=ctx.test_mode,
        )
    )
    return ctx, tuple(effects)


# ---------------------------------------------------------------------------
# Ereignisbehandlung
# ---------------------------------------------------------------------------


def _on_startup(ctx: AlarmContext, event: Startup) -> Result:
    # Regel: Nach einem Neustart ist die Anlage IMMER unscharf.
    # Nur das Timer-Token wird weitergezählt, damit alte Timer sicher verfallen.
    new_ctx = AlarmContext(test_mode=event.test_mode, timer_token=ctx.timer_token + 1)
    effects: list[Effect] = []
    if ctx.state is not AlarmState.DISARMED:
        effects.append(StateChanged(old=ctx.state, new=AlarmState.DISARMED, cause="startup"))
    if event.previous_profile_id is not None:
        effects.append(RestartedDisarmed(previous_profile_id=event.previous_profile_id))
    return new_ctx, tuple(effects)


def _on_arm(ctx: AlarmContext, event: ArmRequested, now: float) -> Result:
    if ctx.state is not AlarmState.DISARMED:
        return ctx, (Rejected(reason="not_disarmed"),)

    profile = event.profile
    verdict = evaluate_readiness(profile, event.readiness, confirmed=event.confirmed)
    if verdict.refused:
        return ctx, (
            Rejected(
                reason="not_ready",
                open_sensors=event.readiness.open_sensors,
                unavailable_sensors=event.readiness.unavailable_sensors,
            ),
        )
    if verdict.needs_confirmation:
        return ctx, (
            ConfirmationRequired(
                open_sensors=event.readiness.open_sensors,
                unavailable_sensors=event.readiness.unavailable_sensors,
            ),
        )

    effects: list[Effect] = []
    ctx = replace(
        ctx,
        profile=profile,
        bypassed=verdict.bypass,
        accepted_unavailable=verdict.accepted_unavailable,
        alarm_cycles=0,
        trigger_sensor=None,
    )
    if verdict.bypass:
        effects.append(SensorsBypassed(sensors=verdict.bypass))

    if profile.exit_delay > 0:
        ctx, changed = _goto(ctx, AlarmState.ARMING, "arm_requested")
        ctx, timer = _start_timer(ctx, TimerKind.EXIT_DELAY, profile.exit_delay, now)
        effects += [changed, timer]
    else:
        ctx, changed = _goto(ctx, AlarmState.ARMED, "arm_requested")
        effects.append(changed)
    return ctx, tuple(effects)


def _on_disarm(ctx: AlarmContext, event: DisarmRequested) -> Result:
    if ctx.state is AlarmState.DISARMED:
        return ctx, (Ignored(reason="already_disarmed"),)
    if not event.code_valid:
        return ctx, (Rejected(reason="invalid_code"),)

    if ctx.state in (AlarmState.TRIGGERED, AlarmState.ALARM_HOLD):
        if ctx.return_to_disarmed:
            return _end_always_alarm(ctx)
        return _acknowledge(ctx, event)
    effects: list[Effect] = []
    # Aus TRIGGERED/ALARM_HOLD geht es nur über "Alarm beenden" (bleibt scharf). Ein durch
    # die Brandsperre verhinderter Sirenen-Stopp wird vom Executor bis zum Erfolg wiederholt.
    ctx, cancel = _cancel_timer(ctx)
    effects += cancel
    ctx, changed = _goto(ctx, AlarmState.DISARMED, "disarm_requested")
    effects.append(changed)
    ctx = replace(
        ctx,
        profile=None,
        bypassed=frozenset(),
        accepted_unavailable=frozenset(),
        alarm_cycles=0,
        trigger_sensor=None,
        bypassed_until_closed=frozenset(),
    )
    return ctx, tuple(effects)


def _on_always_active(ctx: AlarmContext, event: AlwaysActiveTriggered, now: float) -> Result:
    """Immer aktiver Melder: unscharf -> Alarm mit eigener Reaktion, scharf -> sofortiger
    Alarm mit der Reaktion des aktiven Profils."""
    state = ctx.state
    if state is AlarmState.TRIGGERED:
        return ctx, (Ignored(reason="already_triggered"),)
    if state is AlarmState.DISARMED:
        ctx = replace(ctx, profile=event.profile, return_to_disarmed=True, alarm_cycles=0)
        return _trigger(ctx, event.sensor_key, now, "always_active")
    profile = _profile(ctx)
    if state is AlarmState.ALARM_HOLD and ctx.alarm_cycles >= profile.max_alarm_cycles:
        return ctx, (Ignored(reason="max_alarm_cycles_reached"),)
    return _trigger(ctx, event.sensor_key, now, "always_active")


def _end_always_alarm(ctx: AlarmContext) -> Result:
    """Alarm eines immer aktiven Melders aus dem unscharfen Zustand beenden: wieder unscharf."""
    profile = _profile(ctx)
    effects: list[Effect] = []
    ctx, cancel = _cancel_timer(ctx)
    effects += cancel
    ctx, changed = _goto(ctx, AlarmState.DISARMED, "always_alarm_ended")
    effects.append(changed)
    effects.append(StopReaction(profile_id=profile.profile_id, test_mode=ctx.test_mode))
    ctx = replace(
        ctx,
        profile=None,
        bypassed=frozenset(),
        accepted_unavailable=frozenset(),
        alarm_cycles=0,
        trigger_sensor=None,
        bypassed_until_closed=frozenset(),
        return_to_disarmed=False,
    )
    return ctx, tuple(effects)


def _acknowledge(ctx: AlarmContext, event: DisarmRequested) -> Result:
    """Alarm beenden: Sirenen aus, Profil bleibt scharf, offene Sensoren bis zum Schließen
    überbrückt (sonst löste z. B. die offene Tür sofort erneut aus)."""
    profile = _profile(ctx)
    effects: list[Effect] = []
    ctx, cancel = _cancel_timer(ctx)
    effects += cancel
    ctx, changed = _goto(ctx, AlarmState.ARMED, "alarm_acknowledged")
    effects.append(changed)
    # Ob und welche Sirenen tatsächlich gestoppt werden, entscheidet der Sirenen-Guard.
    effects.append(StopReaction(profile_id=profile.profile_id, test_mode=ctx.test_mode))
    temporary = event.open_sensors - ctx.bypassed
    ctx = replace(
        ctx,
        bypassed=ctx.bypassed | temporary,
        bypassed_until_closed=ctx.bypassed_until_closed | temporary,
        alarm_cycles=0,
        trigger_sensor=None,
    )
    effects.append(
        AlarmAcknowledged(profile_id=profile.profile_id, bypassed_until_closed=temporary)
    )
    return ctx, tuple(effects)


def _on_sensor_closed(ctx: AlarmContext, event: SensorClosed) -> Result:
    if event.sensor_key not in ctx.bypassed_until_closed:
        return ctx, (Ignored(reason="not_temporarily_bypassed"),)
    restored = frozenset({event.sensor_key})
    ctx = replace(
        ctx,
        bypassed=ctx.bypassed - restored,
        bypassed_until_closed=ctx.bypassed_until_closed - restored,
    )
    return ctx, (SensorsRestored(sensors=restored),)


def _on_sensor(ctx: AlarmContext, event: SensorTriggered, now: float) -> Result:
    if event.role is SensorRole.TAMPER_24H:
        return _on_tamper(ctx, event, now)

    state = ctx.state
    if state is AlarmState.DISARMED:
        return ctx, (Ignored(reason="disarmed"),)
    if event.sensor_key in ctx.bypassed:
        return ctx, (Ignored(reason="bypassed"),)
    if state is AlarmState.ARMING:
        # Während der Ausgangsverzögerung wird nicht ausgelöst. Am Ende der
        # Verzögerung prüft die Bereitschaftsprüfung erneut, ob alles zu ist.
        return ctx, (Ignored(reason="exit_delay"),)
    if state is AlarmState.TRIGGERED:
        return ctx, (Ignored(reason="already_triggered"),)

    profile = _profile(ctx)

    if state is AlarmState.ALARM_HOLD:
        if ctx.alarm_cycles >= profile.max_alarm_cycles:
            return ctx, (Ignored(reason="max_alarm_cycles_reached"),)
        return _trigger(ctx, event.sensor_key, now, "retrigger")

    if state is AlarmState.PENDING:
        if event.role is SensorRole.INSTANT:
            return _trigger(ctx, event.sensor_key, now, "instant_during_entry_delay")
        return ctx, (Ignored(reason="entry_delay_running"),)

    # state is ARMED
    if event.role is SensorRole.ENTRY and profile.entry_delay > 0:
        effects: list[Effect] = []
        ctx, changed = _goto(ctx, AlarmState.PENDING, "entry_sensor")
        ctx = replace(ctx, trigger_sensor=event.sensor_key)
        ctx, timer = _start_timer(ctx, TimerKind.ENTRY_DELAY, profile.entry_delay, now)
        effects += [changed, timer]
        return ctx, tuple(effects)
    return _trigger(ctx, event.sensor_key, now, f"{event.role.value}_sensor")


def _on_tamper(ctx: AlarmContext, event: SensorTriggered, now: float) -> Result:
    detected = TamperDetected(sensor_key=event.sensor_key, state=ctx.state)
    armed_states = (AlarmState.ARMED, AlarmState.PENDING, AlarmState.ALARM_HOLD)
    if ctx.state in armed_states and _profile(ctx).tamper_triggers_alarm:
        profile = _profile(ctx)
        if ctx.state is AlarmState.ALARM_HOLD and ctx.alarm_cycles >= profile.max_alarm_cycles:
            return ctx, (detected,)
        new_ctx, effects = _trigger(ctx, event.sensor_key, now, "tamper")
        return new_ctx, (detected, *effects)
    return ctx, (detected,)


def _on_exit_elapsed(ctx: AlarmContext, event: ExitDelayElapsed) -> Result:
    if ctx.state is not AlarmState.ARMING or event.token != ctx.timer_token:
        return ctx, (Ignored(reason="stale_timer"),)
    profile = _profile(ctx)
    # Erneute Prüfung: Bereits bestätigte Überbrückungen bleiben gültig. Neue
    # Probleme können jetzt nicht mehr bestätigt werden -> Abbruch (sichere Seite).
    verdict = evaluate_readiness(
        profile,
        event.readiness,
        confirmed=False,
        already_bypassed=ctx.bypassed,
        already_accepted_unavailable=ctx.accepted_unavailable,
    )
    ctx = replace(ctx, timer_kind=None, deadline=None)
    if not verdict.allowed:
        effects: list[Effect] = [
            ArmingAborted(
                open_sensors=event.readiness.open_sensors - ctx.bypassed,
                unavailable_sensors=event.readiness.unavailable_sensors - ctx.accepted_unavailable,
            )
        ]
        ctx, changed = _goto(ctx, AlarmState.DISARMED, "exit_check_failed")
        effects.append(changed)
        ctx = replace(ctx, profile=None, bypassed=frozenset(), accepted_unavailable=frozenset())
        return ctx, tuple(effects)

    effects = []
    newly_bypassed = verdict.bypass - ctx.bypassed
    if newly_bypassed:
        effects.append(SensorsBypassed(sensors=newly_bypassed))
    ctx = replace(ctx, bypassed=verdict.bypass, accepted_unavailable=verdict.accepted_unavailable)
    ctx, changed = _goto(ctx, AlarmState.ARMED, "exit_delay_elapsed")
    effects.append(changed)
    return ctx, tuple(effects)


def _on_entry_elapsed(ctx: AlarmContext, event: EntryDelayElapsed, now: float) -> Result:
    if ctx.state is not AlarmState.PENDING or event.token != ctx.timer_token:
        return ctx, (Ignored(reason="stale_timer"),)
    ctx = replace(ctx, timer_kind=None, deadline=None)
    return _trigger(ctx, ctx.trigger_sensor or "unknown", now, "entry_delay_elapsed")


def _on_reaction_elapsed(ctx: AlarmContext, event: ReactionTimeElapsed) -> Result:
    if ctx.state is not AlarmState.TRIGGERED or event.token != ctx.timer_token:
        return ctx, (Ignored(reason="stale_timer"),)
    ctx = replace(ctx, timer_kind=None, deadline=None)
    ctx, changed = _goto(ctx, AlarmState.ALARM_HOLD, "reaction_time_elapsed")
    # Sirenen ohne eigene Laufzeitbegrenzung laufen sonst weiter. Ob tatsächlich
    # ausgeschaltet wird, entscheidet der Sirenen-Guard (Brandsperre!).
    profile = _profile(ctx)
    return ctx, (changed, StopReaction(profile_id=profile.profile_id, test_mode=ctx.test_mode))


def _on_test_mode(ctx: AlarmContext, event: SetTestMode) -> Result:
    # Testmodus darf nur im unscharfen Zustand gewechselt werden. So kann ein
    # laufender echter Alarm nicht durch Umschalten "weggeschaltet" werden und
    # ein Testalarm nicht plötzlich echt werden.
    if ctx.state is not AlarmState.DISARMED:
        return ctx, (Rejected(reason="test_mode_change_requires_disarmed"),)
    if ctx.test_mode == event.enabled:
        return ctx, (Ignored(reason="test_mode_unchanged"),)
    return replace(ctx, test_mode=event.enabled), (TestModeChanged(enabled=event.enabled),)


def step(ctx: AlarmContext, event: Event, now: float) -> Result:
    """Verarbeitet genau ein Ereignis und liefert neuen Kontext und Effekte."""
    match event:
        case Startup():
            return _on_startup(ctx, event)
        case ArmRequested():
            return _on_arm(ctx, event, now)
        case DisarmRequested():
            return _on_disarm(ctx, event)
        case SensorTriggered():
            return _on_sensor(ctx, event, now)
        case AlwaysActiveTriggered():
            return _on_always_active(ctx, event, now)
        case SensorClosed():
            return _on_sensor_closed(ctx, event)
        case ExitDelayElapsed():
            return _on_exit_elapsed(ctx, event)
        case EntryDelayElapsed():
            return _on_entry_elapsed(ctx, event, now)
        case ReactionTimeElapsed():
            return _on_reaction_elapsed(ctx, event)
        case SetTestMode():
            return _on_test_mode(ctx, event)
    raise TypeError(f"Unbekanntes Ereignis: {event!r}")  # pragma: no cover
