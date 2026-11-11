"""Tests der Zustandsmaschine – ohne Home Assistant, ohne Geräte."""

from __future__ import annotations

from dataclasses import replace

import pytest

from custom_components.hauswacht.core.state_machine import (
    ActivateReaction,
    AlarmAcknowledged,
    AlarmContext,
    AlarmState,
    AlwaysActiveTriggered,
    ArmingAborted,
    ArmRequested,
    CancelTimer,
    ConfirmationRequired,
    DisarmRequested,
    Effect,
    EntryDelayElapsed,
    Event,
    ExitDelayElapsed,
    Ignored,
    OpenSensorPolicy,
    ProfileRuntime,
    ReactionTimeElapsed,
    Readiness,
    Rejected,
    RestartedDisarmed,
    SensorClosed,
    SensorRole,
    SensorsBypassed,
    SensorsRestored,
    SensorTriggered,
    SetTestMode,
    StartTimer,
    Startup,
    StopReaction,
    TamperDetected,
    TestModeChanged,
    TimerKind,
    UnavailableSensorPolicy,
    step,
)

NOTHING_OPEN = Readiness()
NIGHT = ProfileRuntime(profile_id="night", exit_delay=0, entry_delay=30, reaction_time=180)
AWAY = ProfileRuntime(profile_id="away", exit_delay=60, entry_delay=30, reaction_time=180)


class Harness:
    """Kleine Hilfe: führt Ereignisse nacheinander aus und merkt sich Effekte."""

    def __init__(self, ctx: AlarmContext | None = None) -> None:
        self.ctx = ctx or AlarmContext()
        self.now = 0.0
        self.effects: tuple[Effect, ...] = ()

    def send(self, event: Event) -> tuple[Effect, ...]:
        self.ctx, self.effects = step(self.ctx, event, self.now)
        return self.effects

    def timer(self) -> StartTimer:
        timers = [e for e in self.effects if isinstance(e, StartTimer)]
        assert len(timers) == 1, self.effects
        return timers[0]

    def arm(self, profile: ProfileRuntime, readiness: Readiness = NOTHING_OPEN) -> None:
        self.send(ArmRequested(profile=profile, readiness=readiness))
        if profile.exit_delay > 0:
            token = self.timer().token
            self.send(ExitDelayElapsed(token=token))
        assert self.ctx.state is AlarmState.ARMED


def of_type[T](effects: tuple[Effect, ...], kind: type[T]) -> list[T]:
    return [e for e in effects if isinstance(e, kind)]


# --- Scharfschalten ---------------------------------------------------------


def test_initial_state_is_disarmed() -> None:
    assert AlarmContext().state is AlarmState.DISARMED


def test_arm_without_exit_delay_goes_directly_to_armed() -> None:
    h = Harness()
    h.send(ArmRequested(profile=NIGHT))
    assert h.ctx.state is AlarmState.ARMED
    assert h.ctx.profile == NIGHT


def test_arm_with_exit_delay_starts_exit_timer() -> None:
    h = Harness()
    h.send(ArmRequested(profile=AWAY))
    assert h.ctx.state is AlarmState.ARMING
    timer = h.timer()
    assert timer.kind is TimerKind.EXIT_DELAY
    assert timer.seconds == 60


def test_exit_delay_elapsed_arms() -> None:
    h = Harness()
    h.arm(AWAY)
    assert h.ctx.state is AlarmState.ARMED


def test_arm_rejected_when_not_disarmed() -> None:
    h = Harness()
    h.arm(NIGHT)
    effects = h.send(ArmRequested(profile=AWAY))
    assert of_type(effects, Rejected)[0].reason == "not_disarmed"
    assert h.ctx.profile == NIGHT


def test_open_sensor_refused_by_default() -> None:
    h = Harness()
    effects = h.send(
        ArmRequested(profile=NIGHT, readiness=Readiness(open_sensors=frozenset({"kueche"})))
    )
    rejected = of_type(effects, Rejected)[0]
    assert rejected.reason == "not_ready"
    assert rejected.open_sensors == {"kueche"}
    assert h.ctx.state is AlarmState.DISARMED


def test_unavailable_sensor_refused_by_default() -> None:
    h = Harness()
    effects = h.send(
        ArmRequested(profile=NIGHT, readiness=Readiness(unavailable_sensors=frozenset({"bad"})))
    )
    assert of_type(effects, Rejected)[0].unavailable_sensors == {"bad"}
    assert h.ctx.state is AlarmState.DISARMED


def test_open_sensor_with_confirm_policy_needs_confirmation_then_bypasses() -> None:
    profile = ProfileRuntime(profile_id="p", open_policy=OpenSensorPolicy.CONFIRM)
    readiness = Readiness(open_sensors=frozenset({"kueche"}))
    h = Harness()
    effects = h.send(ArmRequested(profile=profile, readiness=readiness))
    assert of_type(effects, ConfirmationRequired)
    assert h.ctx.state is AlarmState.DISARMED

    effects = h.send(ArmRequested(profile=profile, readiness=readiness, confirmed=True))
    assert h.ctx.state is AlarmState.ARMED
    assert h.ctx.bypassed == {"kueche"}
    assert of_type(effects, SensorsBypassed)[0].sensors == {"kueche"}


def test_bypassed_sensor_does_not_trigger() -> None:
    profile = ProfileRuntime(profile_id="p", open_policy=OpenSensorPolicy.BYPASS_AUTO)
    h = Harness()
    h.arm(profile, Readiness(open_sensors=frozenset({"kueche"})))
    effects = h.send(SensorTriggered("kueche", SensorRole.INSTANT))
    assert of_type(effects, Ignored)[0].reason == "bypassed"
    assert h.ctx.state is AlarmState.ARMED


def test_unavailable_with_confirm_policy() -> None:
    profile = ProfileRuntime(profile_id="p", unavailable_policy=UnavailableSensorPolicy.CONFIRM)
    readiness = Readiness(unavailable_sensors=frozenset({"bwm"}))
    h = Harness()
    assert of_type(h.send(ArmRequested(profile, readiness)), ConfirmationRequired)
    h.send(ArmRequested(profile, readiness, confirmed=True))
    assert h.ctx.state is AlarmState.ARMED
    assert h.ctx.accepted_unavailable == {"bwm"}


def test_refuse_beats_confirmation() -> None:
    profile = ProfileRuntime(profile_id="p", open_policy=OpenSensorPolicy.CONFIRM)
    readiness = Readiness(
        open_sensors=frozenset({"kueche"}), unavailable_sensors=frozenset({"bad"})
    )
    effects = Harness().send(ArmRequested(profile, readiness, confirmed=True))
    assert of_type(effects, Rejected)


# --- Ausgangsverzögerung ----------------------------------------------------


def test_sensors_ignored_during_exit_delay() -> None:
    h = Harness()
    h.send(ArmRequested(profile=AWAY))
    effects = h.send(SensorTriggered("haustuer", SensorRole.ENTRY))
    assert of_type(effects, Ignored)[0].reason == "exit_delay"
    assert h.ctx.state is AlarmState.ARMING


def test_exit_check_aborts_when_new_sensor_open() -> None:
    h = Harness()
    h.send(ArmRequested(profile=AWAY))
    token = h.timer().token
    effects = h.send(
        ExitDelayElapsed(token=token, readiness=Readiness(open_sensors=frozenset({"kueche"})))
    )
    assert of_type(effects, ArmingAborted)[0].open_sensors == {"kueche"}
    assert h.ctx.state is AlarmState.DISARMED
    assert h.ctx.profile is None


def test_exit_check_keeps_confirmed_bypass() -> None:
    profile = ProfileRuntime(profile_id="p", exit_delay=30, open_policy=OpenSensorPolicy.CONFIRM)
    readiness = Readiness(open_sensors=frozenset({"kueche"}))
    h = Harness()
    h.send(ArmRequested(profile, readiness, confirmed=True))
    token = h.timer().token
    h.send(ExitDelayElapsed(token=token, readiness=readiness))
    assert h.ctx.state is AlarmState.ARMED


def test_exit_check_with_confirm_policy_cannot_ask_again_and_aborts() -> None:
    profile = ProfileRuntime(profile_id="p", exit_delay=30, open_policy=OpenSensorPolicy.CONFIRM)
    h = Harness()
    h.send(ArmRequested(profile))
    token = h.timer().token
    h.send(ExitDelayElapsed(token, Readiness(open_sensors=frozenset({"bad"}))))
    assert h.ctx.state is AlarmState.DISARMED


def test_exit_check_with_bypass_auto_bypasses_new_open_sensor() -> None:
    profile = ProfileRuntime(
        profile_id="p", exit_delay=30, open_policy=OpenSensorPolicy.BYPASS_AUTO
    )
    h = Harness()
    h.send(ArmRequested(profile))
    token = h.timer().token
    effects = h.send(ExitDelayElapsed(token, Readiness(open_sensors=frozenset({"bad"}))))
    assert h.ctx.state is AlarmState.ARMED
    assert of_type(effects, SensorsBypassed)[0].sensors == {"bad"}


def test_disarm_during_exit_delay_cancels_timer() -> None:
    h = Harness()
    h.send(ArmRequested(profile=AWAY))
    token = h.timer().token
    effects = h.send(DisarmRequested())
    assert of_type(effects, CancelTimer)[0].token == token
    assert h.ctx.state is AlarmState.DISARMED
    # Der alte Timer darf danach nichts mehr bewirken
    effects = h.send(ExitDelayElapsed(token=token))
    assert of_type(effects, Ignored)[0].reason == "stale_timer"
    assert h.ctx.state is AlarmState.DISARMED


# --- Eingangsverzögerung und Auslösung --------------------------------------


def test_entry_sensor_starts_entry_delay() -> None:
    h = Harness()
    h.arm(NIGHT)
    h.send(SensorTriggered("haustuer", SensorRole.ENTRY))
    assert h.ctx.state is AlarmState.PENDING
    assert h.timer().kind is TimerKind.ENTRY_DELAY
    assert h.timer().seconds == 30


def test_entry_delay_elapsed_triggers_alarm() -> None:
    h = Harness()
    h.arm(NIGHT)
    h.send(SensorTriggered("haustuer", SensorRole.ENTRY))
    token = h.timer().token
    effects = h.send(EntryDelayElapsed(token=token))
    assert h.ctx.state is AlarmState.TRIGGERED
    activate = of_type(effects, ActivateReaction)[0]
    assert activate.sensor_key == "haustuer"
    assert activate.cycle == 1
    assert activate.test_mode is False


def test_disarm_within_entry_delay_prevents_alarm() -> None:
    h = Harness()
    h.arm(NIGHT)
    h.send(SensorTriggered("haustuer", SensorRole.ENTRY))
    token = h.timer().token
    effects = h.send(DisarmRequested())
    assert not of_type(effects, StopReaction)  # es lief noch keine Reaktion
    assert h.ctx.state is AlarmState.DISARMED
    effects = h.send(EntryDelayElapsed(token=token))
    assert of_type(effects, Ignored)
    assert not of_type(effects, ActivateReaction)


def test_follower_during_entry_delay_does_not_trigger() -> None:
    h = Harness()
    h.arm(NIGHT)
    h.send(SensorTriggered("haustuer", SensorRole.ENTRY))
    h.send(SensorTriggered("bwm_flur", SensorRole.FOLLOWER))
    assert h.ctx.state is AlarmState.PENDING


def test_second_entry_sensor_during_entry_delay_does_not_restart_timer() -> None:
    h = Harness()
    h.arm(NIGHT)
    h.send(SensorTriggered("haustuer", SensorRole.ENTRY))
    token = h.timer().token
    effects = h.send(SensorTriggered("hintertuer", SensorRole.ENTRY))
    assert not of_type(effects, StartTimer)
    assert h.ctx.timer_token == token


def test_instant_during_entry_delay_triggers_immediately() -> None:
    h = Harness()
    h.arm(NIGHT)
    h.send(SensorTriggered("haustuer", SensorRole.ENTRY))
    effects = h.send(SensorTriggered("fenster", SensorRole.INSTANT))
    assert h.ctx.state is AlarmState.TRIGGERED
    assert of_type(effects, CancelTimer)
    assert of_type(effects, ActivateReaction)[0].sensor_key == "fenster"


@pytest.mark.parametrize("role", [SensorRole.INSTANT, SensorRole.FOLLOWER])
def test_instant_and_follower_trigger_when_armed(role: SensorRole) -> None:
    h = Harness()
    h.arm(NIGHT)
    h.send(SensorTriggered("x", role))
    assert h.ctx.state is AlarmState.TRIGGERED


def test_entry_sensor_without_entry_delay_triggers_immediately() -> None:
    h = Harness()
    h.arm(ProfileRuntime(profile_id="p", entry_delay=0))
    h.send(SensorTriggered("haustuer", SensorRole.ENTRY))
    assert h.ctx.state is AlarmState.TRIGGERED


def test_sensor_ignored_when_disarmed() -> None:
    h = Harness()
    effects = h.send(SensorTriggered("haustuer", SensorRole.INSTANT))
    assert of_type(effects, Ignored)[0].reason == "disarmed"


def test_simultaneous_triggers_produce_only_one_activation() -> None:
    h = Harness()
    h.arm(NIGHT)
    first = h.send(SensorTriggered("a", SensorRole.INSTANT))
    second = h.send(SensorTriggered("b", SensorRole.INSTANT))
    assert len(of_type(first, ActivateReaction)) == 1
    assert not of_type(second, ActivateReaction)


# --- Reaktionsphase, Nachalarm, Re-Trigger ----------------------------------


def test_reaction_time_elapsed_goes_to_alarm_hold() -> None:
    h = Harness()
    h.arm(NIGHT)
    h.send(SensorTriggered("x", SensorRole.INSTANT))
    effects = h.send(ReactionTimeElapsed(token=h.timer().token))
    assert h.ctx.state is AlarmState.ALARM_HOLD
    # Ende der Reaktionszeit beendet auch Sirenen ohne eigene Laufzeit
    assert of_type(effects, StopReaction)[0].profile_id == "night"


def test_retrigger_respects_max_cycles() -> None:
    profile = ProfileRuntime(profile_id="p", reaction_time=10, max_alarm_cycles=2)
    h = Harness()
    h.arm(profile)
    h.send(SensorTriggered("x", SensorRole.INSTANT))
    h.send(ReactionTimeElapsed(token=h.timer().token))

    effects = h.send(SensorTriggered("y", SensorRole.INSTANT))
    assert h.ctx.state is AlarmState.TRIGGERED
    assert of_type(effects, ActivateReaction)[0].cycle == 2

    h.send(ReactionTimeElapsed(token=h.timer().token))
    effects = h.send(SensorTriggered("z", SensorRole.INSTANT))
    assert h.ctx.state is AlarmState.ALARM_HOLD
    assert of_type(effects, Ignored)[0].reason == "max_alarm_cycles_reached"


def test_disarm_while_triggered_only_ends_alarm() -> None:
    """Unscharf während des Alarms: Alarm beenden, Profil bleibt scharf."""
    h = Harness()
    h.arm(NIGHT)
    h.send(SensorTriggered("x", SensorRole.INSTANT))
    effects = h.send(DisarmRequested(open_sensors=frozenset({"x"})))
    assert h.ctx.state is AlarmState.ARMED
    assert h.ctx.profile == NIGHT
    assert of_type(effects, StopReaction)[0].profile_id == "night"
    assert of_type(effects, CancelTimer)  # Reaktionszeit-Timer beendet
    ack = of_type(effects, AlarmAcknowledged)[0]
    assert ack.bypassed_until_closed == frozenset({"x"})
    assert h.ctx.alarm_cycles == 0
    # zweites Unscharf: jetzt wirklich unscharf
    h.send(DisarmRequested())
    assert h.ctx.state is AlarmState.DISARMED
    assert h.ctx.bypassed_until_closed == frozenset()


def test_end_alarm_from_alarm_hold() -> None:
    h = Harness()
    h.arm(NIGHT)
    h.send(SensorTriggered("x", SensorRole.INSTANT))
    h.send(ReactionTimeElapsed(token=h.timer().token))
    effects = h.send(DisarmRequested())
    assert h.ctx.state is AlarmState.ARMED
    # Erneuter Stopp, falls er am Ende der Reaktionszeit durch die Brandsperre blockiert war
    assert of_type(effects, StopReaction)[0].profile_id == "night"


def test_open_sensor_bypassed_until_closed() -> None:
    h = Harness()
    h.arm(NIGHT)
    h.send(SensorTriggered("door", SensorRole.ENTRY))
    h.send(EntryDelayElapsed(token=h.timer().token))
    h.send(DisarmRequested(open_sensors=frozenset({"door"})))
    # offene Tür löst nicht erneut aus
    assert of_type(h.send(SensorTriggered("door", SensorRole.ENTRY)), Ignored)
    assert h.ctx.state is AlarmState.ARMED
    # andere Sensoren bleiben scharf
    h.send(SensorTriggered("window", SensorRole.INSTANT))
    assert h.ctx.state is AlarmState.TRIGGERED
    h.send(DisarmRequested(open_sensors=frozenset({"door"})))
    # Tür zu: wieder überwacht
    restored = h.send(SensorClosed("door"))
    assert of_type(restored, SensorsRestored)[0].sensors == frozenset({"door"})
    h.send(SensorTriggered("door", SensorRole.ENTRY))
    assert h.ctx.state is AlarmState.PENDING


def test_sensor_closed_does_not_restore_permanent_bypass() -> None:
    h = Harness()
    h.arm(NIGHT)
    h.ctx = replace(h.ctx, bypassed=frozenset({"door"}))
    assert of_type(h.send(SensorClosed("door")), Ignored)
    assert "door" in h.ctx.bypassed


def test_invalid_code_does_not_end_alarm() -> None:
    h = Harness()
    h.arm(NIGHT)
    h.send(SensorTriggered("x", SensorRole.INSTANT))
    h.send(DisarmRequested(code_valid=False))
    assert h.ctx.state is AlarmState.TRIGGERED


def test_invalid_code_does_not_disarm() -> None:
    h = Harness()
    h.arm(NIGHT)
    h.send(SensorTriggered("x", SensorRole.INSTANT))
    effects = h.send(DisarmRequested(code_valid=False))
    assert of_type(effects, Rejected)[0].reason == "invalid_code"
    assert h.ctx.state is AlarmState.TRIGGERED


def test_stale_reaction_timer_after_disarm_is_ignored() -> None:
    h = Harness()
    h.arm(NIGHT)
    h.send(SensorTriggered("x", SensorRole.INSTANT))
    token = h.timer().token
    h.send(DisarmRequested())
    h.arm(NIGHT)
    effects = h.send(ReactionTimeElapsed(token=token))
    assert of_type(effects, Ignored)[0].reason == "stale_timer"
    assert h.ctx.state is AlarmState.ARMED


# --- Manipulation -----------------------------------------------------------


def test_tamper_is_reported_even_when_disarmed() -> None:
    h = Harness()
    effects = h.send(SensorTriggered("kontakt_tamper", SensorRole.TAMPER_24H))
    assert of_type(effects, TamperDetected)[0].state is AlarmState.DISARMED
    assert h.ctx.state is AlarmState.DISARMED


def test_tamper_only_reports_by_default_when_armed() -> None:
    h = Harness()
    h.arm(NIGHT)
    effects = h.send(SensorTriggered("t", SensorRole.TAMPER_24H))
    assert of_type(effects, TamperDetected)
    assert h.ctx.state is AlarmState.ARMED


def test_tamper_triggers_alarm_when_configured() -> None:
    h = Harness()
    h.arm(ProfileRuntime(profile_id="p", tamper_triggers_alarm=True))
    effects = h.send(SensorTriggered("t", SensorRole.TAMPER_24H))
    assert of_type(effects, TamperDetected)
    assert h.ctx.state is AlarmState.TRIGGERED


# --- Neustart ---------------------------------------------------------------


@pytest.mark.parametrize(
    "state",
    [AlarmState.ARMED, AlarmState.PENDING, AlarmState.TRIGGERED, AlarmState.ALARM_HOLD],
)
def test_startup_always_disarms(state: AlarmState) -> None:
    ctx = AlarmContext(state=state, profile=NIGHT, timer_token=7)
    new_ctx, effects = step(ctx, Startup(previous_profile_id="night"), 0.0)
    assert new_ctx.state is AlarmState.DISARMED
    assert new_ctx.profile is None
    assert new_ctx.timer_token > 7  # alte Timer verfallen
    assert of_type(effects, RestartedDisarmed)[0].previous_profile_id == "night"
    assert not of_type(effects, ActivateReaction)


def test_startup_without_previous_profile_has_no_restart_notice() -> None:
    _, effects = step(AlarmContext(), Startup(), 0.0)
    assert not of_type(effects, RestartedDisarmed)


def test_startup_keeps_test_mode() -> None:
    new_ctx, _ = step(AlarmContext(), Startup(test_mode=True), 0.0)
    assert new_ctx.test_mode is True


def test_timer_from_before_restart_is_ignored() -> None:
    h = Harness()
    h.arm(NIGHT)
    h.send(SensorTriggered("haustuer", SensorRole.ENTRY))
    token = h.timer().token
    h.send(Startup(previous_profile_id="night"))
    effects = h.send(EntryDelayElapsed(token=token))
    assert of_type(effects, Ignored)
    assert h.ctx.state is AlarmState.DISARMED


# --- Testmodus --------------------------------------------------------------


def test_test_mode_flag_is_passed_to_reaction() -> None:
    h = Harness()
    assert of_type(h.send(SetTestMode(enabled=True)), TestModeChanged)
    h.arm(NIGHT)
    effects = h.send(SensorTriggered("x", SensorRole.INSTANT))
    assert of_type(effects, ActivateReaction)[0].test_mode is True
    effects = h.send(DisarmRequested())
    assert of_type(effects, StopReaction)[0].test_mode is True


@pytest.mark.parametrize("enabled", [True, False])
def test_test_mode_cannot_change_while_armed(enabled: bool) -> None:
    h = Harness(AlarmContext(test_mode=not enabled))
    h.arm(NIGHT)
    effects = h.send(SetTestMode(enabled=enabled))
    assert of_type(effects, Rejected)[0].reason == "test_mode_change_requires_disarmed"
    assert h.ctx.test_mode is (not enabled)


# --- Profilvalidierung ------------------------------------------------------


@pytest.mark.parametrize(
    "kwargs",
    [
        {"profile_id": ""},
        {"profile_id": "p", "exit_delay": -1},
        {"profile_id": "p", "entry_delay": -1},
        {"profile_id": "p", "reaction_time": 0},
        {"profile_id": "p", "max_alarm_cycles": 0},
    ],
)
def test_invalid_profiles_are_rejected(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError, match=r"."):
        ProfileRuntime(**kwargs)  # type: ignore[arg-type]


# --- Immer aktive Melder -------------------------------------------------------

ALWAYS = ProfileRuntime(profile_id="__always__", reaction_time=60)


def test_always_active_from_disarmed_and_back_to_disarmed() -> None:
    h = Harness()
    effects = h.send(AlwaysActiveTriggered(sensor_key="binary_sensor.tresor", profile=ALWAYS))
    assert h.ctx.state is AlarmState.TRIGGERED
    assert h.ctx.profile == ALWAYS
    assert any(isinstance(e, ActivateReaction) and e.profile_id == "__always__" for e in effects)
    effects = h.send(DisarmRequested())
    assert h.ctx.state is AlarmState.DISARMED
    assert h.ctx.profile is None
    assert h.ctx.return_to_disarmed is False
    assert any(isinstance(e, StopReaction) for e in effects)


def test_always_active_while_armed_uses_active_profile() -> None:
    h = Harness()
    h.send(ArmRequested(profile=NIGHT))
    assert h.ctx.state is AlarmState.ARMED
    effects = h.send(AlwaysActiveTriggered(sensor_key="binary_sensor.tresor", profile=ALWAYS))
    assert h.ctx.state is AlarmState.TRIGGERED
    assert any(isinstance(e, ActivateReaction) and e.profile_id == "night" for e in effects)
    h.send(DisarmRequested())
    assert h.ctx.state is AlarmState.ARMED  # Alarm beendet, Profil bleibt scharf


def test_always_active_ignored_while_triggered() -> None:
    h = Harness()
    h.send(AlwaysActiveTriggered(sensor_key="binary_sensor.a", profile=ALWAYS))
    effects = h.send(AlwaysActiveTriggered(sensor_key="binary_sensor.b", profile=ALWAYS))
    assert any(isinstance(e, Ignored) for e in effects)
