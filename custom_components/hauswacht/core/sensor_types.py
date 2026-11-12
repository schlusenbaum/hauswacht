"""Melderarten und Melder-Typen.

Rein und ohne Home Assistant.

**Arten:** Hauswacht nimmt nur Melder, die "offen/zu" kennen: Binärsensoren, Schlösser und
Abdeckungen. Intern wird alles auf "on" (offen/ausgelöst) und "off" (zu/ruhig) abgebildet;
``unavailable``/``unknown`` gilt als nicht verfügbar. Messwerte, Ereignisse usw. werden über
einen Home-Assistant-Helfer (z. B. Schwellenwert) zu einem Binärsensor.

**Typen:** Jeder Melder hat einen Typ, der festlegt, *wie* er reagiert. Vorschlag aus der
Geräteklasse, änderbar in der Meldergruppe (``options["sensor_types"]``). *Wann* er scharf ist,
legen Meldergruppen und Alarmprofile fest.

| Typ | Rolle |
|---|---|
| Tür | Eingang (Eingangsverzögerung) |
| Fenster | sofort |
| Bewegung | Mitläufer |
| Manipulation | immer gemeldet |
| Technik (Wasser, Gas, Frost …) | immer aktiv, nie Teil der Scharfschaltung |
| Sonstiges | sofort (sicherheitshalber) |
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Any

from .state_machine import SensorRole

ON, OFF = "on", "off"
UNAVAILABLE = "unavailable"
NOT_AVAILABLE_STATES = frozenset({"unavailable", "unknown", ""})

MONITORED_DOMAINS: tuple[str, ...] = ("binary_sensor", "lock", "cover")

LOCK_ON = frozenset({"unlocked", "unlocking", "open", "opening", "jammed"})
LOCK_OFF = frozenset({"locked", "locking"})
COVER_ON = frozenset({"open", "opening", "closing"})
COVER_OFF = frozenset({"closed"})
COVER_DOOR_CLASSES = frozenset({"door", "garage", "gate"})


class SensorType(StrEnum):
    DOOR = "door"
    WINDOW = "window"
    MOTION = "motion"
    TAMPER = "tamper"
    TECHNICAL = "technical"
    OTHER = "other"


TYPE_ROLE: Mapping[SensorType, SensorRole] = {
    SensorType.DOOR: SensorRole.ENTRY,
    SensorType.WINDOW: SensorRole.INSTANT,
    SensorType.MOTION: SensorRole.FOLLOWER,
    SensorType.TAMPER: SensorRole.TAMPER_24H,
    SensorType.TECHNICAL: SensorRole.INSTANT,
    SensorType.OTHER: SensorRole.INSTANT,
}

# Bisherige Rollen-Abweichungen -> Typ (Migration)
ROLE_TYPE: Mapping[SensorRole, SensorType] = {
    SensorRole.ENTRY: SensorType.DOOR,
    SensorRole.INSTANT: SensorType.WINDOW,
    SensorRole.FOLLOWER: SensorType.MOTION,
    SensorRole.TAMPER_24H: SensorType.TAMPER,
}

TYPE_BY_DEVICE_CLASS: Mapping[str, SensorType] = {
    "door": SensorType.DOOR,
    "garage_door": SensorType.DOOR,
    "opening": SensorType.DOOR,
    "lock": SensorType.DOOR,
    "window": SensorType.WINDOW,
    "motion": SensorType.MOTION,
    "occupancy": SensorType.MOTION,
    "presence": SensorType.MOTION,
    "moving": SensorType.MOTION,
    "tamper": SensorType.TAMPER,
    "moisture": SensorType.TECHNICAL,
    "gas": SensorType.TECHNICAL,
    "cold": SensorType.TECHNICAL,
    "heat": SensorType.TECHNICAL,
    "carbon_monoxide": SensorType.TECHNICAL,
}


def domain_of(entity_id: str) -> str:
    return entity_id.split(".", 1)[0]


def is_monitorable(entity_id: str) -> bool:
    return domain_of(entity_id) in MONITORED_DOMAINS


def normalize(entity_id: str, state: str | None) -> str | None:
    """Rohzustand -> "on", "off", "unavailable"/"unknown" oder None (Entität fehlt)."""
    if state is None:
        return None
    if state in NOT_AVAILABLE_STATES:
        return UNAVAILABLE if state == "" else state
    domain = domain_of(entity_id)
    if domain == "lock":
        if state in LOCK_ON:
            return ON
        return OFF if state in LOCK_OFF else UNAVAILABLE
    if domain == "cover":
        if state in COVER_ON:
            return ON
        return OFF if state in COVER_OFF else UNAVAILABLE
    return state


def default_type(entity_id: str, device_class: str | None) -> SensorType:
    """Vorschlag aus Art und Geräteklasse. Unbekanntes: Sonstiges (löst sofort aus)."""
    domain = domain_of(entity_id)
    if domain == "lock":
        return SensorType.DOOR
    if domain == "cover":
        return SensorType.DOOR if device_class in COVER_DOOR_CLASSES else SensorType.OTHER
    if device_class is None:
        return SensorType.OTHER
    return TYPE_BY_DEVICE_CLASS.get(device_class, SensorType.OTHER)


def parse_types(options: Mapping[str, Any]) -> dict[str, SensorType]:
    """Gewählte Typen (Abweichungen vom Vorschlag)."""
    raw = options.get("sensor_types", {})
    result: dict[str, SensorType] = {}
    if not isinstance(raw, Mapping):
        return result
    for entity_id, value in raw.items():
        try:
            result[str(entity_id)] = SensorType(value)
        except ValueError:
            continue
    return result


def sensor_type(
    entity_id: str, device_class: str | None, types: Mapping[str, SensorType]
) -> SensorType:
    return types.get(entity_id) or default_type(entity_id, device_class)


def role_overrides(types: Mapping[str, SensorType]) -> dict[str, SensorRole]:
    """Rollen aus den gewählten Typen (für die Zustandsmaschine)."""
    return {entity_id: TYPE_ROLE[kind] for entity_id, kind in types.items()}


def migrate_roles_to_types(options: Mapping[str, Any]) -> dict[str, Any]:
    """Bisherige Rollen-Abweichungen (``sensor_roles``) in Typen umwandeln; Reste aus 0.24
    (Schwellwerte, Kameras) entfernen und nicht mehr unterstützte Melderarten aussortieren."""
    new = dict(options)
    types = dict(new.get("sensor_types", {}) or {})
    roles = new.pop("sensor_roles", {}) or {}
    if isinstance(roles, Mapping):
        for entity_id, role in roles.items():
            try:
                types.setdefault(str(entity_id), ROLE_TYPE[SensorRole(role)].value)
            except (ValueError, KeyError):
                continue
    new["sensor_types"] = {k: v for k, v in types.items() if is_monitorable(k)}
    for key in ("sensor_thresholds", "sensor_cameras"):
        new.pop(key, None)
    zones = new.get("zones", {})
    if isinstance(zones, Mapping):
        new["zones"] = {
            zid: (
                {**zone, "entities": [e for e in zone.get("entities", []) if is_monitorable(e)]}
                if isinstance(zone, Mapping) and isinstance(zone.get("entities"), list)
                else zone
            )
            for zid, zone in zones.items()
        }
    always = new.get("always_active")
    if isinstance(always, Mapping) and isinstance(always.get("sensors"), list):
        new["always_active"] = {
            **always,
            "sensors": [e for e in always["sensors"] if is_monitorable(e)],
        }
    profiles = new.get("profiles", {})
    if isinstance(profiles, Mapping):
        new["profiles"] = {
            pid: (
                {k: v for k, v in data.items() if k not in ("camera", "save_snapshots")}
                if isinstance(data, Mapping)
                else data
            )
            for pid, data in profiles.items()
        }
    return new


def excluded_sensors(options: Mapping[str, Any], profile_id: str) -> frozenset[str]:
    """Ausgenommene Melder eines Alarmprofils (lösen einzeln nicht aus)."""
    profiles = options.get("profiles", {})
    stored = profiles.get(profile_id, {}) if isinstance(profiles, Mapping) else {}
    raw = stored.get("excluded", []) if isinstance(stored, Mapping) else []
    if not isinstance(raw, list):
        return frozenset()
    return frozenset(e for e in raw if isinstance(e, str))
