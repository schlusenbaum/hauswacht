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
    SirenCapabilities,
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


# --- Brand an fremden Meldern -----------------------------------------------


def test_external_active_fire_blocks_activation_and_stop() -> None:
    guard = GuardContext(
        hardware_enabled=True,
        test_mode=False,
        devices={"diele": device("diele")},
        activated_by_hauswacht=frozenset({"diele"}),
        external_fire=FireIndicator.ACTIVE,
    )
    assert decide_activation(guard, REQ).commands == ()
    assert decide_stop(guard).commands == ()


def test_external_unknown_fire_does_not_block() -> None:
    guard = GuardContext(
        hardware_enabled=True,
        test_mode=False,
        devices={"diele": device("diele")},
        external_fire=FireIndicator.UNKNOWN,
    )
    assert decide_activation(guard, REQ).commands


# --- Gerätefähigkeiten ------------------------------------------------------

ONE = ActivateRequest(targets=("s",), tone="burglar", volume="high", duration=180)


def caps(**kw: object) -> SirenCapabilities:
    return SirenCapabilities(**kw)  # type: ignore[arg-type]


def test_full_capabilities_send_everything() -> None:
    tones = frozenset({"burglar", "fire", "emergency"})
    decision = decide_activation(ctx(device("s", capabilities=caps(tones=tones))), ONE)
    command = decision.commands[0]
    assert (command.tone, command.volume_level, command.duration) == ("burglar", 0.75, 180)


def test_fallback_to_other_burglar_tone_never_fire() -> None:
    tones = frozenset({"fire", "fire_panic", "police_panic"})
    decision = decide_activation(ctx(device("s", capabilities=caps(tones=tones))), ONE)
    assert decision.commands[0].tone == "police_panic"


def test_only_fire_tones_blocks() -> None:
    tones = frozenset({"fire", "fire_panic"})
    decision = decide_activation(ctx(device("s", capabilities=caps(tones=tones))), ONE)
    assert decision.commands == ()
    assert reasons(decision) == {BlockReason.NO_BURGLAR_TONE}


def test_unknown_tone_list_sends_requested_tone() -> None:
    decision = decide_activation(ctx(device("s", capabilities=caps(tones=None))), ONE)
    assert decision.commands[0].tone == "burglar"


def test_plain_siren_without_tones_volume_duration() -> None:
    plain = caps(tones_supported=False, volume=False, duration=False, turn_off=True)
    decision = decide_activation(ctx(device("s", capabilities=plain)), ONE)
    command = decision.commands[0]
    assert (command.tone, command.volume_level, command.duration) == (None, None, None)


def test_smoke_detector_without_tone_selection_blocked() -> None:
    no_tones = caps(tones_supported=False)
    decision = decide_activation(ctx(device("s", capabilities=no_tones, fire_detector=True)), ONE)
    assert decision.commands == ()
    assert reasons(decision) == {BlockReason.NO_BURGLAR_TONE}


def test_siren_that_cannot_be_limited_is_blocked() -> None:
    endless = caps(tones_supported=False, duration=False, turn_off=False)
    decision = decide_activation(ctx(device("s", capabilities=endless)), ONE)
    assert reasons(decision) == {BlockReason.CANNOT_LIMIT}


def test_duration_only_device_without_turn_off_is_allowed() -> None:
    decision = decide_activation(ctx(device("s", capabilities=caps(turn_off=False))), ONE)
    assert decision.commands[0].duration == 180


def test_max_duration_ignored_when_duration_unsupported() -> None:
    plain = caps(duration=False)
    decision = decide_activation(ctx(device("s", capabilities=plain, max_duration=0)), ONE)
    assert decision.commands[0].duration is None


def test_stop_skips_device_without_turn_off() -> None:
    decision = decide_stop(
        ctx(device("s", capabilities=caps(turn_off=False)), activated=frozenset({"s"}))
    )
    assert decision.commands == ()
    assert reasons(decision) == {BlockReason.TURN_OFF_UNSUPPORTED}


@pytest.mark.parametrize("fire", [FireIndicator.ACTIVE, FireIndicator.UNKNOWN])
def test_capabilities_never_bypass_fire_lock(fire: FireIndicator) -> None:
    plain = caps(tones_supported=False, volume=False)
    decision = decide_activation(ctx(device("s", fire, capabilities=plain)), ONE)
    assert reasons(decision) == {BlockReason.FIRE_LOCK}


# --- 0.40: Ton je Sirene (z. B. HmIP-ASIR) und Schalter als Sirene ----------------------

ASIR_TONES = frozenset(
    {"FREQUENCY_RISING", "FREQUENCY_RISING_AND_FALLING", "LOW_BATTERY", "DISARMED"}
)


def _one(dev: SirenDevice) -> GuardDecision:
    return decide_activation(ctx(dev), ActivateRequest(("x",), "burglar", "high", 180))


def test_siren_with_own_tone_names_stays_blocked_without_setting() -> None:
    dev = device("x", capabilities=SirenCapabilities(tones=ASIR_TONES))
    assert reasons(_one(dev)) == {BlockReason.NO_BURGLAR_TONE}


def test_configured_tone_is_used() -> None:
    dev = device(
        "x",
        capabilities=SirenCapabilities(tones=ASIR_TONES),
        tone="FREQUENCY_RISING_AND_FALLING",
    )
    decision = _one(dev)
    assert decision.commands[0].tone == "FREQUENCY_RISING_AND_FALLING"
    assert decision.commands[0].duration == 180


@pytest.mark.parametrize("tone", ["fire", "FIRE_ALARM", "Brandalarm", "smoke_alarm"])
def test_configured_fire_tone_is_never_used(tone: str) -> None:
    dev = device("x", capabilities=SirenCapabilities(tones=frozenset({tone})), tone=tone)
    assert _one(dev).commands == ()


def test_configured_tone_unknown_to_device_falls_back() -> None:
    caps = SirenCapabilities(tones=frozenset({"burglar"}))
    dev = device("x", capabilities=caps, tone="FREQUENCY_RISING")
    assert _one(dev).commands[0].tone == "burglar"


def test_switch_like_device_only_turns_on_and_off() -> None:
    caps = SirenCapabilities(
        tones_supported=False, tones=None, volume=False, duration=False, turn_off=True
    )
    decision = _one(device("x", capabilities=caps))
    command = decision.commands[0]
    assert (command.tone, command.volume_level, command.duration) == (None, None, None)
    stop = decide_stop(ctx(device("x", capabilities=caps), activated=frozenset({"x"})))
    assert [c.action for c in stop.commands] == ["turn_off"]
    # Brandsperre gilt auch für Schalter
    burning = ctx(device("x", capabilities=caps), device("rm", FireIndicator.ACTIVE))
    assert (
        decide_activation(burning, ActivateRequest(("x",), "burglar", "high", 180)).commands == ()
    )


# --- 0.41: Brandton als Experten-Freigabe ---------------------------------------------

OUTDOOR_TONES = frozenset({"fire", "chime"})


def test_expert_fire_tone_for_plain_siren() -> None:
    caps = SirenCapabilities(tones=OUTDOOR_TONES)
    locked = device("x", capabilities=caps, tone="fire")
    assert _one(locked).commands == ()
    released = device("x", capabilities=caps, tone="fire", fire_tone_allowed=True)
    assert _one(released).commands[0].tone == "fire"


def test_expert_fire_tone_never_on_smoke_detector() -> None:
    caps = SirenCapabilities(tones=OUTDOOR_TONES)
    dev = device("x", capabilities=caps, tone="fire", fire_tone_allowed=True, fire_detector=True)
    assert _one(dev).commands == ()


def test_expert_fire_tone_does_not_bypass_fire_lock() -> None:
    caps = SirenCapabilities(tones=OUTDOOR_TONES)
    dev = device("x", capabilities=caps, tone="fire", fire_tone_allowed=True)
    burning = ctx(dev, device("rm", FireIndicator.ACTIVE))
    assert (
        decide_activation(burning, ActivateRequest(("x",), "burglar", "high", 180)).commands == ()
    )


def test_expert_release_only_for_the_configured_tone() -> None:
    # Freigabe ohne eingestellten Ton: kein automatischer Brandton
    caps = SirenCapabilities(tones=OUTDOOR_TONES)
    dev = device("x", capabilities=caps, fire_tone_allowed=True)
    assert _one(dev).commands == ()
