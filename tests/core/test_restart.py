"""Verhalten nach Neustart: Plan aus Einstellung und gespeichertem Zustand."""

from __future__ import annotations

from custom_components.hauswacht.core.restart import (
    RestartKind,
    plan_restart,
    restart_behavior,
    restart_profile,
    saved_state,
)

KNOWN = {"night", "away"}


def test_default_is_restore() -> None:
    assert restart_behavior({}) == "restore"
    assert restart_behavior({"restart_behavior": "quatsch"}) == "restore"
    assert restart_behavior({"restart_behavior": "disarmed"}) == "disarmed"


def test_restart_profile_per_area() -> None:
    options = {"restart_profiles": {"main": "away", "garage": ""}}
    assert restart_profile(options, "main") == "away"
    assert restart_profile(options, "garage") is None
    assert restart_profile({}, "main") is None


def test_restore_armed_state() -> None:
    saved = saved_state(
        profile_id="night",
        state="armed",
        bypassed={"binary_sensor.window"},
        bypassed_until_closed=set(),
        accepted_unavailable=set(),
        trigger_sensor=None,
        auto_armed_by="night",
    )
    plan = plan_restart(
        "restore", saved=saved, previous_profile="night", fixed_profile=None, known_profiles=KNOWN
    )
    assert plan.kind is RestartKind.RESTORE
    assert plan.profile_id == "night"
    assert plan.bypassed == {"binary_sensor.window"}
    assert plan.auto_armed_by == "night"
    assert not plan.entry_delay
    assert not plan.alarm_was_active
    assert plan.report_disarmed is None


def test_restore_exit_delay_becomes_armed() -> None:
    saved = {"profile": "away", "state": "arming"}
    plan = plan_restart(
        "restore", saved=saved, previous_profile="away", fixed_profile=None, known_profiles=KNOWN
    )
    assert plan.kind is RestartKind.RESTORE
    assert not plan.entry_delay


def test_restore_entry_delay_starts_again() -> None:
    saved = {"profile": "away", "state": "pending", "trigger_sensor": "binary_sensor.door"}
    plan = plan_restart(
        "restore", saved=saved, previous_profile="away", fixed_profile=None, known_profiles=KNOWN
    )
    assert plan.entry_delay
    assert plan.trigger_sensor == "binary_sensor.door"


def test_restore_never_continues_alarm() -> None:
    for state in ("triggered", "alarm_hold"):
        saved = {"profile": "away", "state": state, "trigger_sensor": "binary_sensor.window"}
        plan = plan_restart(
            "restore",
            saved=saved,
            previous_profile="away",
            fixed_profile=None,
            known_profiles=KNOWN,
        )
        assert plan.kind is RestartKind.RESTORE
        assert plan.alarm_was_active
        assert plan.alarm_in_reaction is (state == "triggered")
        assert not plan.entry_delay


def test_continue_alarm_option() -> None:
    from custom_components.hauswacht.core.restart import continue_alarm  # noqa: PLC0415

    assert not continue_alarm({})
    assert continue_alarm({"restart_continue_alarm": True})


def test_restore_from_older_version_without_details() -> None:
    """Bis 0.44 wurde nur das scharfe Profil gespeichert."""
    plan = plan_restart(
        "restore", saved=None, previous_profile="night", fixed_profile=None, known_profiles=KNOWN
    )
    assert plan.kind is RestartKind.RESTORE
    assert plan.profile_id == "night"
    assert plan.bypassed == frozenset()


def test_restore_disarmed_stays_disarmed() -> None:
    plan = plan_restart(
        "restore", saved=None, previous_profile=None, fixed_profile=None, known_profiles=KNOWN
    )
    assert plan.kind is RestartKind.DISARMED
    assert plan.report_disarmed is None


def test_restore_deleted_profile_is_disarmed_and_reported() -> None:
    plan = plan_restart(
        "restore",
        saved={"profile": "gone", "state": "armed"},
        previous_profile="gone",
        fixed_profile=None,
        known_profiles=KNOWN,
    )
    assert plan.kind is RestartKind.DISARMED
    assert plan.report_disarmed == "gone"


def test_always_armed() -> None:
    plan = plan_restart(
        "armed", saved=None, previous_profile=None, fixed_profile="away", known_profiles=KNOWN
    )
    assert plan.kind is RestartKind.ARM
    assert plan.profile_id == "away"
    # ohne (gültiges) Profil: unscharf, und melden, wenn vorher scharf
    plan = plan_restart(
        "armed", saved=None, previous_profile="night", fixed_profile="gone", known_profiles=KNOWN
    )
    assert plan.kind is RestartKind.DISARMED
    assert plan.report_disarmed == "night"


def test_always_disarmed() -> None:
    plan = plan_restart(
        "disarmed",
        saved={"profile": "night", "state": "armed"},
        previous_profile="night",
        fixed_profile=None,
        known_profiles=KNOWN,
    )
    assert plan.kind is RestartKind.DISARMED
    assert plan.report_disarmed == "night"


def test_saved_state_disarmed_is_none() -> None:
    assert (
        saved_state(
            profile_id=None,
            state="disarmed",
            bypassed=(),
            bypassed_until_closed=(),
            accepted_unavailable=(),
            trigger_sensor=None,
            auto_armed_by=None,
        )
        is None
    )
