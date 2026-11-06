"""Tests des Sirenen-Guards – die wichtigsten Sicherheitstests des Projekts."""

from __future__ import annotations

import pytest

from custom_components.hauswacht.core.siren_guard import (
    BURGLAR_TONES,
    FIRE_TONES,
    ActivateRequest,
    BlockReason,
    FireIndicator,
    GuardContext,
    GuardDecision,
    SirenDevice,
    decide_activation,
    decide_stop,
)


def device(key: str, fire: FireIndicator = FireIndicator.CLEAR, **kw: object) -> SirenDevice:
    params: dict[str, object] = {"max_duration": 240, "burglar_allowed": True}
    params.update(kw)
    return SirenDevice(
        key=key,
        entity_id=f"siren.{key}",
        fire_state=fire,
        **params,  # type: ignore[arg-type]
    )


def ctx(
    *devices: SirenDevice,
    hardware: bool = True,
    test_mode: bool = False,
    activated: frozenset[str] = frozenset(),
) -> GuardContext:
    return GuardContext(
        hardware_enabled=hardware,
        test_mode=test_mode,
        devices={d.key: d for d in devices},
        activated_by_hauswacht=activated,
    )


REQ = ActivateRequest(targets=("diele", "wohnzimmer"), tone="burglar", volume="high", duration=180)


def reasons(decision: GuardDecision) -> set[BlockReason]:
    return {b.reason for b in decision.blocked}


# --- Aktivierung ------------------------------------------------------------


def test_activation_allowed_in_normal_operation() -> None:
    decision = decide_activation(ctx(device("diele"), device("wohnzimmer")), REQ)
    assert [c.entity_id for c in decision.commands] == ["siren.diele", "siren.wohnzimmer"]
    assert all(c.action == "turn_on" for c in decision.commands)
    assert decision.commands[0].tone == "burglar"
    assert decision.commands[0].volume_level == 0.75
    assert not decision.blocked


def test_test_mode_blocks_every_activation() -> None:
    decision = decide_activation(ctx(device("diele"), device("wohnzimmer"), test_mode=True), REQ)
    assert decision.commands == ()
    assert reasons(decision) == {BlockReason.TEST_MODE}


def test_test_mode_blocks_even_with_hardware_enabled() -> None:
    decision = decide_activation(ctx(device("diele"), hardware=True, test_mode=True), REQ)
    assert decision.commands == ()


def test_hardware_disabled_blocks_every_activation() -> None:
    decision = decide_activation(ctx(device("diele"), device("wohnzimmer"), hardware=False), REQ)
    assert decision.commands == ()
    assert reasons(decision) == {BlockReason.HARDWARE_DISABLED}


@pytest.mark.parametrize("fire", [FireIndicator.ACTIVE, FireIndicator.UNKNOWN])
def test_fire_on_any_device_blocks_all_activations(fire: FireIndicator) -> None:
    # Brand (oder unklarer Zustand) im Schlafzimmer, Einbruchalarm für EG angefordert
    guard = ctx(device("diele"), device("wohnzimmer"), device("schlafzimmer", fire))
    decision = decide_activation(guard, REQ)
    assert decision.commands == ()
    assert reasons(decision) == {BlockReason.FIRE_LOCK}


@pytest.mark.parametrize("tone", sorted(FIRE_TONES))
def test_fire_tones_are_forbidden_for_burglar_alarm(tone: str) -> None:
    request = ActivateRequest(targets=("diele",), tone=tone, volume="high", duration=60)
    decision = decide_activation(ctx(device("diele")), request)
    assert decision.commands == ()
    assert reasons(decision) == {BlockReason.INVALID_TONE}


@pytest.mark.parametrize("tone", sorted(BURGLAR_TONES))
def test_burglar_tones_are_allowed(tone: str) -> None:
    request = ActivateRequest(targets=("diele",), tone=tone, volume="low", duration=60)
    assert decide_activation(ctx(device("diele")), request).commands


def test_unknown_tone_and_volume_and_duration_are_rejected() -> None:
    guard = ctx(device("diele"))
    assert reasons(
        decide_activation(guard, ActivateRequest(("diele",), "doorbell", "high", 60))
    ) == {BlockReason.INVALID_TONE}
    assert reasons(decide_activation(guard, ActivateRequest(("diele",), "burglar", "max", 60))) == {
        BlockReason.INVALID_VOLUME
    }
    assert reasons(decide_activation(guard, ActivateRequest(("diele",), "burglar", "high", 0))) == {
        BlockReason.INVALID_DURATION
    }


def test_duration_is_capped_to_device_maximum() -> None:
    request = ActivateRequest(targets=("diele",), tone="burglar", volume="high", duration=600)
    decision = decide_activation(ctx(device("diele", max_duration=240)), request)
    assert decision.commands[0].duration == 240


def test_only_requested_devices_are_activated() -> None:
    guard = ctx(device("diele"), device("wohnzimmer"), device("schlafzimmer"))
    request = ActivateRequest(targets=("diele",), tone="burglar", volume="high", duration=60)
    decision = decide_activation(guard, request)
    assert [c.device_key for c in decision.commands] == ["diele"]


def test_device_not_allowed_for_burglar_is_skipped() -> None:
    guard = ctx(device("diele"), device("wohnzimmer", burglar_allowed=False))
    decision = decide_activation(guard, REQ)
    assert [c.device_key for c in decision.commands] == ["diele"]
    assert reasons(decision) == {BlockReason.NOT_ALLOWED_FOR_BURGLAR}


def test_unknown_device_is_skipped() -> None:
    decision = decide_activation(ctx(device("diele")), REQ)
    assert [c.device_key for c in decision.commands] == ["diele"]
    assert reasons(decision) == {BlockReason.UNKNOWN_DEVICE}


def test_duplicate_targets_produce_one_command() -> None:
    request = ActivateRequest(("diele", "diele"), "burglar", "high", 60)
    assert len(decide_activation(ctx(device("diele")), request).commands) == 1


def test_empty_target_list_produces_no_commands() -> None:
    request = ActivateRequest((), "burglar", "high", 60)
    assert decide_activation(ctx(device("diele")), request) == GuardDecision()


# --- Abschalten -------------------------------------------------------------


def test_stop_only_devices_activated_by_hauswacht() -> None:
    guard = ctx(device("diele"), device("wohnzimmer"), activated=frozenset({"diele"}))
    decision = decide_stop(guard)
    assert [c.entity_id for c in decision.commands] == ["siren.diele"]
    assert decision.commands[0].action == "turn_off"


def test_explicit_stop_of_foreign_device_is_blocked() -> None:
    guard = ctx(device("diele"), device("wohnzimmer"), activated=frozenset({"diele"}))
    decision = decide_stop(guard, targets=["wohnzimmer"])
    assert decision.commands == ()
    assert reasons(decision) == {BlockReason.NOT_ACTIVATED_BY_HAUSWACHT}


@pytest.mark.parametrize("fire", [FireIndicator.ACTIVE, FireIndicator.UNKNOWN])
def test_fire_anywhere_blocks_every_stop(fire: FireIndicator) -> None:
    # Einbruchalarm lief auf Diele, nun Brand in Finjas Zimmer: NICHTS darf
    # ausgeschaltet werden, auch nicht die von Hauswacht aktivierte Diele.
    guard = ctx(device("diele"), device("finja", fire), activated=frozenset({"diele"}))
    decision = decide_stop(guard)
    assert decision.commands == ()
    assert reasons(decision) == {BlockReason.FIRE_LOCK}


def test_stop_blocked_in_test_mode() -> None:
    guard = ctx(device("diele"), test_mode=True, activated=frozenset({"diele"}))
    assert decide_stop(guard).commands == ()


def test_stop_blocked_without_hardware_release() -> None:
    guard = ctx(device("diele"), hardware=False, activated=frozenset({"diele"}))
    assert decide_stop(guard).commands == ()


def test_stop_with_nothing_activated_does_nothing() -> None:
    assert decide_stop(ctx(device("diele"))) == GuardDecision()


# --- Systematische Eigenschaftsprüfung --------------------------------------


@pytest.mark.parametrize("hardware", [True, False])
@pytest.mark.parametrize("test_mode", [True, False])
@pytest.mark.parametrize("fire", list(FireIndicator))
def test_no_command_ever_escapes_the_locks(
    hardware: bool, test_mode: bool, fire: FireIndicator
) -> None:
    """Für jede Kombination gilt: Befehle nur, wenn ALLE Sperren offen sind."""
    guard = ctx(
        device("diele"),
        device("wohnzimmer", fire),
        hardware=hardware,
        test_mode=test_mode,
        activated=frozenset({"diele", "wohnzimmer"}),
    )
    all_open = hardware and not test_mode and fire is FireIndicator.CLEAR
    assert bool(decide_activation(guard, REQ).commands) is all_open
    assert bool(decide_stop(guard).commands) is all_open
