"""Sensorlogik (reine Funktionen).

- Zonen bestehen aus direkt gewählten Entitäten und optional allen Entitäten mit einem Label.
- Die Rolle eines Sensors ergibt sich aus seiner Geräteklasse, Ausnahmen sind einstellbar.
- Die Bereitschaft (offen / nicht verfügbar / zu lange still) wird aus Zustands-Schnappschüssen
  berechnet, nicht aus Live-Zugriffen. Dadurch ist alles ohne Home Assistant testbar.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from .state_machine import Readiness, SensorRole

TRIGGER_STATE = "on"
UNAVAILABLE_STATES = frozenset({"unavailable", "unknown"})

DEFAULT_ROLE_BY_DEVICE_CLASS: Mapping[str, SensorRole] = {
    "door": SensorRole.ENTRY,
    "garage_door": SensorRole.ENTRY,
    "opening": SensorRole.ENTRY,
    "window": SensorRole.INSTANT,
    "vibration": SensorRole.INSTANT,
    "motion": SensorRole.FOLLOWER,
    "occupancy": SensorRole.FOLLOWER,
    "presence": SensorRole.FOLLOWER,
    "moving": SensorRole.FOLLOWER,
    "tamper": SensorRole.TAMPER_24H,
}


@dataclass(frozen=True)
class Zone:
    zone_id: str
    name: str
    entities: frozenset[str] = frozenset()
    label: str | None = None  # Label-ID


@dataclass(frozen=True)
class SensorSnapshot:
    """Momentaufnahme eines Sensors."""

    entity_id: str
    state: str | None  # None = Entität existiert nicht
    device_class: str | None = None
    last_reported: float | None = None  # Unix-Zeitstempel


# --- Konfiguration lesen ----------------------------------------------------


def slugify(name: str, existing: Iterable[str] = ()) -> str:
    """Erzeugt eine stabile, eindeutige ID aus einem Namen ("Außenhaut" -> "aussenhaut")."""
    text = name.strip().lower().replace("ß", "ss")
    for umlaut, repl in (("ä", "ae"), ("ö", "oe"), ("ü", "ue")):
        text = text.replace(umlaut, repl)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "_", text).strip("_") or "zone"
    taken = set(existing)
    candidate, number = slug, 2
    while candidate in taken:
        candidate = f"{slug}_{number}"
        number += 1
    return candidate


def parse_zones(options: Mapping[str, Any]) -> dict[str, Zone]:
    zones: dict[str, Zone] = {}
    raw = options.get("zones", {})
    if not isinstance(raw, Mapping):
        return zones
    for zone_id, data in raw.items():
        if not isinstance(data, Mapping):
            continue
        entities = data.get("entities", [])
        label = data.get("label")
        zones[str(zone_id)] = Zone(
            zone_id=str(zone_id),
            name=str(data.get("name") or zone_id),
            entities=frozenset(str(e) for e in entities if isinstance(e, str)),
            label=str(label) if label else None,
        )
    return zones


def parse_role_overrides(options: Mapping[str, Any]) -> dict[str, SensorRole]:
    overrides: dict[str, SensorRole] = {}
    raw = options.get("sensor_roles", {})
    if not isinstance(raw, Mapping):
        return overrides
    for entity_id, role in raw.items():
        try:
            overrides[str(entity_id)] = SensorRole(role)
        except ValueError:
            continue
    return overrides


# --- Zonen auflösen ---------------------------------------------------------


def resolve_zone(zone: Zone, entities_by_label: Mapping[str, frozenset[str]]) -> frozenset[str]:
    """Alle Entitäten einer Zone: direkt gewählte plus alle mit dem Label der Zone."""
    from_label = entities_by_label.get(zone.label, frozenset()) if zone.label else frozenset()
    return zone.entities | from_label


def resolve_zones(
    zone_ids: Iterable[str],
    zones: Mapping[str, Zone],
    entities_by_label: Mapping[str, frozenset[str]],
) -> frozenset[str]:
    members: set[str] = set()
    for zone_id in zone_ids:
        zone = zones.get(zone_id)
        if zone is not None:
            members |= resolve_zone(zone, entities_by_label)
    return frozenset(members)


def all_configured_sensors(
    zones: Mapping[str, Zone], entities_by_label: Mapping[str, frozenset[str]]
) -> frozenset[str]:
    return resolve_zones(zones.keys(), zones, entities_by_label)


# --- Rollen -----------------------------------------------------------------


def default_role(device_class: str | None) -> SensorRole:
    """Rolle aus der Geräteklasse. Unbekanntes löst sicherheitshalber sofort aus."""
    if device_class is None:
        return SensorRole.INSTANT
    return DEFAULT_ROLE_BY_DEVICE_CLASS.get(device_class, SensorRole.INSTANT)


def sensor_role(
    entity_id: str, device_class: str | None, overrides: Mapping[str, SensorRole]
) -> SensorRole:
    return overrides.get(entity_id) or default_role(device_class)


# --- Bereitschaft und Auslösung ---------------------------------------------


def is_unavailable(snapshot: SensorSnapshot, now: float, stale_after: float | None) -> bool:
    """Nicht verfügbar: fehlt, unavailable/unknown oder meldet sich zu lange nicht."""
    if snapshot.state is None or snapshot.state in UNAVAILABLE_STATES:
        return True
    if stale_after and stale_after > 0:
        if snapshot.last_reported is None:
            return True
        return now - snapshot.last_reported > stale_after
    return False


def evaluate_readiness(
    entity_ids: Iterable[str],
    snapshots: Mapping[str, SensorSnapshot],
    *,
    now: float,
    stale_after: float | None = None,
) -> Readiness:
    """Bereitschaft für eine Menge von Sensoren.

    Offen heißt: Zustand "on" (Tür/Fenster offen, Bewegung erkannt, Manipulation aktiv).
    """
    open_sensors: set[str] = set()
    unavailable: set[str] = set()
    for entity_id in entity_ids:
        snapshot = snapshots.get(entity_id) or SensorSnapshot(entity_id=entity_id, state=None)
        if is_unavailable(snapshot, now, stale_after):
            unavailable.add(entity_id)
        elif snapshot.state == TRIGGER_STATE:
            open_sensors.add(entity_id)
    return Readiness(
        open_sensors=frozenset(open_sensors), unavailable_sensors=frozenset(unavailable)
    )


def is_trigger(old_state: str | None, new_state: str | None) -> bool:
    """Eine Auslösung ist jeder Wechsel nach "on" aus einem anderen Zustand.

    Auch unavailable -> on zählt (sichere Seite: ein verpasstes Öffnen wird nachgeholt).
    """
    return new_state == TRIGGER_STATE and old_state != TRIGGER_STATE


def became_unavailable(old_state: str | None, new_state: str | None) -> bool:
    return (new_state is None or new_state in UNAVAILABLE_STATES) and not (
        old_state is None or old_state in UNAVAILABLE_STATES
    )
