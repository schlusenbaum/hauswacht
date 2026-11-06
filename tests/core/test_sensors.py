"""Tests der Sensorlogik: Zonen, Labels, Rollen, Bereitschaft, Auslösung."""

from __future__ import annotations

import pytest

from custom_components.hauswacht.core.profiles import (
    DEFAULT_ALARM_CYCLES,
    build_profiles,
    profile_behaviour,
    stale_after_seconds,
)
from custom_components.hauswacht.core.sensors import (
    SensorSnapshot,
    Zone,
    all_configured_sensors,
    became_unavailable,
    default_role,
    evaluate_readiness,
    is_last_seen_entity,
    is_trigger,
    parse_role_overrides,
    parse_zones,
    resolve_zone,
    resolve_zones,
    sensor_role,
    slugify,
)
from custom_components.hauswacht.core.state_machine import (
    OpenSensorPolicy,
    SensorRole,
    UnavailableSensorPolicy,
)

OPTIONS = {
    "zones": {
        "aussenhaut": {
            "name": "Außenhaut",
            "entities": ["binary_sensor.haustuer", "binary_sensor.kuechenfenster"],
            "label": "label_aussen",
        },
        "keller": {"name": "Keller", "entities": ["binary_sensor.bwm_keller"]},
    }
}
LABELS = {"label_aussen": frozenset({"binary_sensor.hintertuer"})}


# --- Konfiguration ----------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Außenhaut", "aussenhaut"),
        ("Keller / Süd", "keller_sued"),
        ("  ", "zone"),
        ("Ñandú", "nandu"),
    ],
)
def test_slugify(name: str, expected: str) -> None:
    assert slugify(name) == expected


def test_slugify_avoids_duplicates() -> None:
    assert slugify("Keller", existing=["keller", "keller_2"]) == "keller_3"


def test_parse_zones() -> None:
    zones = parse_zones(OPTIONS)
    assert set(zones) == {"aussenhaut", "keller"}
    assert zones["aussenhaut"].name == "Außenhaut"
    assert zones["aussenhaut"].label == "label_aussen"
    assert zones["keller"].label is None


@pytest.mark.parametrize("bad", [None, "x", ["a"], {"z": "kaputt"}])
def test_parse_zones_tolerates_garbage(bad: object) -> None:
    assert parse_zones({"zones": bad}) == {}


def test_parse_role_overrides_ignores_invalid_roles() -> None:
    overrides = parse_role_overrides(
        {"sensor_roles": {"binary_sensor.a": "instant", "binary_sensor.b": "explode"}}
    )
    assert overrides == {"binary_sensor.a": SensorRole.INSTANT}


# --- Zonen ------------------------------------------------------------------


def test_zone_combines_direct_entities_and_label() -> None:
    zone = parse_zones(OPTIONS)["aussenhaut"]
    assert resolve_zone(zone, LABELS) == {
        "binary_sensor.haustuer",
        "binary_sensor.kuechenfenster",
        "binary_sensor.hintertuer",
    }


def test_zone_without_label_uses_only_direct_entities() -> None:
    zone = parse_zones(OPTIONS)["keller"]
    assert resolve_zone(zone, LABELS) == {"binary_sensor.bwm_keller"}


def test_label_only_zone() -> None:
    zone = Zone(zone_id="z", name="Z", label="label_aussen")
    assert resolve_zone(zone, LABELS) == {"binary_sensor.hintertuer"}


def test_resolve_multiple_zones_and_unknown_zone() -> None:
    zones = parse_zones(OPTIONS)
    members = resolve_zones(["aussenhaut", "keller", "gibt_es_nicht"], zones, LABELS)
    assert len(members) == 4


def test_all_configured_sensors() -> None:
    assert len(all_configured_sensors(parse_zones(OPTIONS), LABELS)) == 4


# --- Rollen -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("device_class", "role"),
    [
        ("door", SensorRole.ENTRY),
        ("window", SensorRole.INSTANT),
        ("occupancy", SensorRole.FOLLOWER),
        ("motion", SensorRole.FOLLOWER),
        ("presence", SensorRole.FOLLOWER),
        ("tamper", SensorRole.TAMPER_24H),
        ("smoke", SensorRole.INSTANT),
        (None, SensorRole.INSTANT),
    ],
)
def test_default_roles(device_class: str | None, role: SensorRole) -> None:
    assert default_role(device_class) is role


def test_override_wins_over_device_class() -> None:
    overrides = {"binary_sensor.fenster": SensorRole.ENTRY}
    assert sensor_role("binary_sensor.fenster", "window", overrides) is SensorRole.ENTRY
    assert sensor_role("binary_sensor.anderes", "window", overrides) is SensorRole.INSTANT


# --- Bereitschaft -----------------------------------------------------------

NOW = 1_000_000.0


def snap(entity_id: str, state: str | None, age: float = 10.0) -> SensorSnapshot:
    return SensorSnapshot(entity_id=entity_id, state=state, last_reported=NOW - age)


def test_all_closed_is_ready() -> None:
    snaps = {e: snap(e, "off") for e in ("a", "b")}
    readiness = evaluate_readiness(["a", "b"], snaps, now=NOW)
    assert not readiness.open_sensors
    assert not readiness.unavailable_sensors


def test_open_and_unavailable_sensors() -> None:
    snaps = {"a": snap("a", "on"), "b": snap("b", "unavailable"), "c": snap("c", "unknown")}
    readiness = evaluate_readiness(["a", "b", "c", "fehlt"], snaps, now=NOW)
    assert readiness.open_sensors == {"a"}
    assert readiness.unavailable_sensors == {"b", "c", "fehlt"}


def test_stale_sensor_counts_as_unavailable_only_when_enabled() -> None:
    snaps = {"a": snap("a", "off", age=7200)}
    assert not evaluate_readiness(["a"], snaps, now=NOW).unavailable_sensors
    readiness = evaluate_readiness(["a"], snaps, now=NOW, stale_after=3600)
    assert readiness.unavailable_sensors == {"a"}


def test_stale_without_timestamp_is_unavailable() -> None:
    snaps = {"a": SensorSnapshot(entity_id="a", state="off", last_reported=None)}
    assert evaluate_readiness(["a"], snaps, now=NOW, stale_after=60).unavailable_sensors == {"a"}


def test_unavailable_beats_open() -> None:
    snaps = {"a": snap("a", "on", age=7200)}
    readiness = evaluate_readiness(["a"], snaps, now=NOW, stale_after=60)
    assert readiness.unavailable_sensors == {"a"}
    assert not readiness.open_sensors


# --- Auslösung --------------------------------------------------------------


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        ("off", "on", True),
        ("unavailable", "on", True),
        (None, "on", True),
        ("on", "on", False),
        ("on", "off", False),
        ("off", "unavailable", False),
    ],
)
def test_is_trigger(old: str | None, new: str | None, expected: bool) -> None:
    assert is_trigger(old, new) is expected


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        ("off", "unavailable", True),
        ("on", None, True),
        ("unavailable", "unknown", False),
        ("off", "on", False),
    ],
)
def test_became_unavailable(old: str | None, new: str | None, expected: bool) -> None:
    assert became_unavailable(old, new) is expected


# --- Profilverhalten --------------------------------------------------------


def test_profile_behaviour_defaults() -> None:
    behaviour = profile_behaviour({}, "night")
    assert behaviour.zones == ()
    assert behaviour.open_policy is OpenSensorPolicy.REFUSE
    assert behaviour.unavailable_policy is UnavailableSensorPolicy.REFUSE
    assert behaviour.max_alarm_cycles == DEFAULT_ALARM_CYCLES
    assert behaviour.tamper_triggers_alarm is False


def test_profile_behaviour_from_options() -> None:
    options = {
        "profiles": {
            "away": {
                "zones": ["aussenhaut", "keller"],
                "open_policy": "confirm",
                "unavailable_policy": "confirm",
                "max_alarm_cycles": 5,
                "tamper_triggers_alarm": True,
            }
        }
    }
    behaviour = profile_behaviour(options, "away")
    assert behaviour.zones == ("aussenhaut", "keller")
    assert behaviour.open_policy is OpenSensorPolicy.CONFIRM
    assert behaviour.max_alarm_cycles == 5
    away = build_profiles(options)["away"]
    assert away.unavailable_policy is UnavailableSensorPolicy.CONFIRM
    assert away.tamper_triggers_alarm is True


def test_invalid_policies_fall_back_to_refuse() -> None:
    behaviour = profile_behaviour(
        {"profiles": {"home": {"open_policy": "egal", "max_alarm_cycles": 99}}}, "home"
    )
    assert behaviour.open_policy is OpenSensorPolicy.REFUSE
    assert behaviour.max_alarm_cycles == DEFAULT_ALARM_CYCLES


@pytest.mark.parametrize(("hours", "expected"), [(0, None), (None, None), (2, 7200.0), (999, None)])
def test_stale_after_seconds(hours: object, expected: float | None) -> None:
    assert stale_after_seconds({"stale_after_hours": hours}) == expected


# --- Letzter Kontakt (last_seen) --------------------------------------------


def test_last_seen_wins_over_last_reported() -> None:
    # HA hat den Sensor gerade erst (Neustart) aktualisiert, das Gerät schweigt aber seit 3 h.
    snapshot = SensorSnapshot(
        entity_id="a", state="off", last_reported=NOW - 10, last_seen=NOW - 3 * 3600
    )
    assert snapshot.last_contact == NOW - 3 * 3600
    readiness = evaluate_readiness(["a"], {"a": snapshot}, now=NOW, stale_after=3600)
    assert readiness.unavailable_sensors == {"a"}


def test_without_last_seen_falls_back_to_last_reported() -> None:
    snapshot = SensorSnapshot(entity_id="a", state="off", last_reported=NOW - 10)
    assert snapshot.last_contact == NOW - 10
    assert not evaluate_readiness(
        ["a"], {"a": snapshot}, now=NOW, stale_after=3600
    ).unavailable_sensors


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        (
            {"entity_id": "sensor.tuer_last_seen", "unique_id": None, "device_class": "timestamp"},
            True,
        ),
        (
            {
                "entity_id": "sensor.x",
                "unique_id": "0x1_last_seen_zigbee2mqtt",
                "device_class": "timestamp",
            },
            True,
        ),
        (
            {
                "entity_id": "sensor.x",
                "unique_id": None,
                "device_class": "timestamp",
                "original_name": "Last seen",
            },
            True,
        ),
        (
            {
                "entity_id": "sensor.x",
                "unique_id": None,
                "device_class": "timestamp",
                "translation_key": "last_seen",
            },
            True,
        ),
        ({"entity_id": "sensor.tuer_last_seen", "unique_id": None, "device_class": None}, False),
        (
            {
                "entity_id": "binary_sensor.tuer_last_seen",
                "unique_id": None,
                "device_class": "timestamp",
            },
            False,
        ),
        (
            {
                "entity_id": "sensor.letzter_batteriewechsel",
                "unique_id": None,
                "device_class": "timestamp",
            },
            False,
        ),
    ],
)
def test_is_last_seen_entity(kwargs: dict[str, str | None], expected: bool) -> None:
    assert is_last_seen_entity(**kwargs) is expected  # type: ignore[arg-type]
