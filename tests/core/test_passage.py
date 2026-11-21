"""Durchgang (ADR 0013) – Zustandsmaschine und Einstellungen, ohne Home Assistant."""

from __future__ import annotations

from custom_components.hauswacht.core.passage import (
    DEFAULT_DURATION,
    DEFAULT_PATH_AFTER,
    OutDoors,
    OutEnd,
    PassageConfig,
    out_candidates,
    parse_passage,
    passage_from_input,
    path_sensors,
)
from custom_components.hauswacht.core.state_machine import (
    AlarmContext,
    AlarmState,
    ArmRequested,
    DisarmRequested,
    Effect,
    Event,
    PassageDoorUsed,
    PassageEnd,
    PassageEnded,
    PassageGranted,
    PassageIn,
    PassageOut,
    ProfileRuntime,
    Rejected,
    SensorClosed,
    SensorRole,
    SensorTriggered,
    StateChanged,
    step,
)

NIGHT = ProfileRuntime(profile_id="night", entry_delay=30)
FRONT = "binary_sensor.front"
BACK = "binary_sensor.back"
DRIVEWAY = "binary_sensor.driveway"
WINDOW = "binary_sensor.window"


def run(ctx: AlarmContext, *events: Event) -> tuple[AlarmContext, list[Effect]]:
    effects: list[Effect] = []
    for event in events:
        ctx, new = step(ctx, event, 0.0)
        effects += new
    return ctx, effects


def armed() -> AlarmContext:
    ctx, _ = run(AlarmContext(), ArmRequested(profile=NIGHT))
    assert ctx.state is AlarmState.ARMED
    return ctx


def opened(sensor: str, role: SensorRole = SensorRole.ENTRY) -> SensorTriggered:
    return SensorTriggered(sensor_key=sensor, role=role)


# --- Reinkommen ---------------------------------------------------------------


def test_passage_in_ends_entry_delay_and_stays_armed() -> None:
    ctx, _ = run(armed(), opened(FRONT))
    assert ctx.state is AlarmState.PENDING
    ctx, effects = run(ctx, PassageIn(door=FRONT, path=frozenset({DRIVEWAY})))
    assert ctx.state is AlarmState.ARMED
    assert ctx.timer_kind is None
    assert StateChanged(old=AlarmState.PENDING, new=AlarmState.ARMED, cause="passage") in effects
    assert PassageGranted(direction="in", door=FRONT, path=frozenset({DRIVEWAY})) in effects
    assert FRONT in ctx.bypassed_until_closed
    assert DRIVEWAY in ctx.passage
    # Tür und Weg lösen nicht aus, andere Melder schon
    ctx, effects = run(ctx, opened(DRIVEWAY, SensorRole.INSTANT))
    assert ctx.state is AlarmState.ARMED
    ctx, _ = run(ctx, opened(WINDOW, SensorRole.INSTANT))
    assert ctx.state is AlarmState.TRIGGERED


def test_passage_in_door_watched_again_after_closing() -> None:
    ctx, _ = run(armed(), opened(FRONT), PassageIn(door=FRONT))
    ctx, _ = run(ctx, SensorClosed(sensor_key=FRONT))
    assert FRONT not in ctx.bypassed
    ctx, _ = run(ctx, opened(FRONT))
    assert ctx.state is AlarmState.PENDING  # nächste Öffnung braucht einen neuen Ausweis


def test_passage_not_while_disarmed_or_alarm() -> None:
    _, effects = run(AlarmContext(), PassageIn(door=FRONT))
    assert Rejected(reason="passage_not_possible") in effects
    ctx, _ = run(armed(), opened(WINDOW, SensorRole.INSTANT))
    assert ctx.state is AlarmState.TRIGGERED
    _, effects = run(ctx, PassageIn(door=FRONT))
    assert Rejected(reason="passage_not_possible") in effects
    _, effects = run(ctx, PassageOut(doors=frozenset({FRONT})))
    assert Rejected(reason="passage_not_possible") in effects


def test_path_end_keeps_active_sensors_until_closed() -> None:
    ctx, _ = run(armed(), opened(FRONT), PassageIn(door=FRONT, path=frozenset({DRIVEWAY})))
    ctx, effects = run(ctx, PassageEnd(still_active=frozenset({DRIVEWAY})))
    assert PassageEnded(restored=frozenset(), still_open=frozenset({DRIVEWAY})) in effects
    assert DRIVEWAY in ctx.bypassed_until_closed
    assert not ctx.passage
    ctx, _ = run(ctx, SensorClosed(sensor_key=DRIVEWAY))
    assert DRIVEWAY not in ctx.bypassed


# --- Rausgehen ----------------------------------------------------------------


def test_passage_out_first_door_only() -> None:
    ctx, effects = run(
        armed(), PassageOut(doors=frozenset({FRONT, BACK}), path=frozenset({DRIVEWAY}))
    )
    assert PassageGranted(direction="out", door=None, path=frozenset({DRIVEWAY})) in effects
    ctx, effects = run(ctx, opened(BACK))
    assert PassageDoorUsed(door=BACK) in effects
    assert ctx.state is AlarmState.ARMED
    assert BACK in ctx.passage
    # Mehrmals auf und zu: bleibt frei
    ctx, _ = run(ctx, SensorClosed(sensor_key=BACK), opened(BACK))
    assert ctx.state is AlarmState.ARMED
    # Die andere Tür bleibt scharf
    ctx, _ = run(ctx, opened(FRONT))
    assert ctx.state is AlarmState.PENDING


def test_passage_out_all_doors() -> None:
    ctx, _ = run(armed(), PassageOut(doors=frozenset({FRONT, BACK}), first_only=False))
    ctx, _ = run(ctx, opened(BACK), opened(FRONT))
    assert ctx.state is AlarmState.ARMED
    assert ctx.passage == {FRONT, BACK}


def test_passage_out_end_open_door_stays_bypassed_until_closed() -> None:
    ctx, _ = run(armed(), PassageOut(doors=frozenset({FRONT, BACK})), opened(FRONT))
    ctx, effects = run(ctx, PassageEnd(still_active=frozenset({FRONT})))
    assert PassageEnded(restored=frozenset(), still_open=frozenset({FRONT})) in effects
    assert not ctx.passage_doors
    ctx, _ = run(ctx, opened(BACK))
    assert ctx.state is AlarmState.PENDING  # Hintertür war nie frei
    ctx, _ = run(ctx, DisarmRequested())
    ctx, _ = run(ctx, ArmRequested(profile=NIGHT))
    assert not ctx.passage
    assert not ctx.bypassed


def test_passage_out_end_unused_door_is_watched() -> None:
    ctx, _ = run(armed(), PassageOut(doors=frozenset({FRONT})))
    ctx, _ = run(ctx, PassageEnd())
    ctx, _ = run(ctx, opened(FRONT))
    assert ctx.state is AlarmState.PENDING


def test_disarm_clears_passage() -> None:
    ctx, _ = run(armed(), PassageOut(doors=frozenset({FRONT}), path=frozenset({DRIVEWAY})))
    ctx, _ = run(ctx, opened(FRONT), DisarmRequested())
    assert ctx.state is AlarmState.DISARMED
    assert not ctx.passage
    assert not ctx.passage_doors


# --- Einstellungen ------------------------------------------------------------


def test_parse_defaults_and_limits() -> None:
    assert parse_passage({}, "night") == PassageConfig()
    options = {
        "profiles": {
            "night": {
                "passage": {
                    "enabled": True,
                    "duration": 999,
                    "out_doors": "all",
                    "out_end": "returned",
                    "path": [DRIVEWAY, 3],
                    "path_after": -5,
                    "persons": ["person.finja"],
                }
            }
        }
    }
    config = parse_passage(options, "night")
    assert config.enabled
    assert config.duration == 60
    assert config.out_doors is OutDoors.ALL
    assert config.out_end is OutEnd.RETURNED
    assert config.path == {DRIVEWAY}
    assert config.path_after == 0
    assert config.persons == ("person.finja",)
    assert passage_from_input({"enabled": True, "out_doors": "nonsense"}) == {
        "enabled": True,
        "duration": DEFAULT_DURATION,
        "out_doors": "first",
        "out_end": "time",
        "path": [],
        "path_after": DEFAULT_PATH_AFTER,
        "persons": [],
        "window": 5,
    }


def test_candidates_and_path() -> None:
    armed_sensors = frozenset({FRONT, BACK, DRIVEWAY})
    assert out_candidates(frozenset({FRONT, BACK}), frozenset({BACK}), armed_sensors) == {FRONT}
    config = PassageConfig(path=frozenset({DRIVEWAY, WINDOW}))
    assert path_sensors(config, armed_sensors, frozenset()) == {DRIVEWAY}


def test_save_profile_keeps_unknown_passage_fields() -> None:
    from custom_components.hauswacht.core.changes.profiles import save_profile  # noqa: PLC0415

    options = {
        "zones": {},
        "profiles": {
            "night": {
                "name": "Nacht",
                "passage": {"enabled": True, "persons": ["person.finja"], "window": 7},
            }
        },
    }
    form = {
        "name": "Nacht",
        "exit_delay": 0,
        "entry_delay": 30,
        "reaction_time": 180,
        "open_policy": "refuse",
        "unavailable_policy": "refuse",
        "max_alarm_cycles": 1,
        "tamper_triggers_alarm": False,
        "siren_tone": "burglar",
        "siren_volume": "high",
        "silent": False,
        "passage": {"enabled": True, "duration": 3, "path": [DRIVEWAY]},
    }
    change = save_profile(options, "night", form)
    assert change.options is not None
    stored = change.options["profiles"]["night"]["passage"]
    assert stored["duration"] == 3
    assert stored["path"] == [DRIVEWAY]
    assert stored["persons"] == ["person.finja"]  # Dialog kennt die Personen nicht
    assert stored["window"] == 7


def test_phone_passage_and_door_proof_exclude_each_other() -> None:
    from custom_components.hauswacht.core.changes.profiles import validate_profile  # noqa: PLC0415

    data = {
        "name": "Nacht",
        "automation": {"auto_arrival_mode": "door", "auto_away_persons": ["person.finja"]},
        "passage": {"enabled": True, "persons": ["person.finja"]},
    }
    assert validate_profile({"profiles": {}}, None, data)["base"] == "passage_door_proof"
    data["passage"] = {"enabled": True, "persons": []}
    assert "base" not in validate_profile({"profiles": {}}, None, data)
