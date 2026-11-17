"""Einrichtungsassistent: Vorschläge und Zusammenfassung (ADR 0009).

Rein und ohne Home Assistant. Der Assistent selbst (Formulare) steht in ``wizard.py`` und
speichert nur über die Einstellungsregeln in ``core/changes``.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .areas import MAIN_AREA, profile_area
from .changes import Change
from .changes.profiles import save_profile
from .changes.zones import save_zone
from .profiles import profile_info, profile_infos
from .rules import parse_rules
from .sensor_types import SensorType, parse_types, sensor_type
from .sensors import parse_zones, resolve_zones

# Geräteklassen, die der Assistent als Melder vorschlägt (Technik, Rauch usw. nicht)
SUGGESTED_TYPES = frozenset({SensorType.DOOR, SensorType.WINDOW, SensorType.MOTION})

MODE_ZONES = "zones"
MODE_RULES = "rules"
MODE_BOTH = "both"

AWAY = "away"
NIGHT = "night"
DEFAULT_EXIT_DELAY = 60
DEFAULT_ENTRY_DELAY = 30

PROFILE_TEXTS: Mapping[str, Mapping[str, tuple[str, str]]] = {
    # panel_mode: {Sprache: (Name, Symbol)}
    AWAY: {
        "de": ("Abwesend", "mdi:shield-lock-outline"),
        "en": ("Away", "mdi:shield-lock-outline"),
    },
    NIGHT: {"de": ("Nacht", "mdi:weather-night"), "en": ("Night", "mdi:weather-night")},
}


@dataclass(frozen=True)
class Candidate:
    """Ein möglicher Melder aus Home Assistant."""

    entity_id: str
    name: str
    device_class: str | None = None
    place: str = ""  # "Erdgeschoss › Küche" oder ""


def grouped_entities(options: Mapping[str, Any], labels: Mapping[str, frozenset[str]]) -> set[str]:
    """Melder, die schon in einer Meldergruppe stehen."""
    zones = parse_zones(options)
    return set(resolve_zones(zones, zones, labels))


def suggest_sensors(
    candidates: Iterable[Candidate],
    options: Mapping[str, Any],
    labels: Mapping[str, frozenset[str]] | None = None,
) -> list[Candidate]:
    """Türen, Fenster und Bewegungsmelder, die noch in keiner Gruppe stehen – nach Ort sortiert."""
    taken = grouped_entities(options, labels or {})
    found = [
        c
        for c in candidates
        if c.entity_id not in taken
        and sensor_type(c.entity_id, c.device_class, {}) in SUGGESTED_TYPES
    ]
    return sorted(found, key=lambda c: (c.place == "", c.place.casefold(), c.name.casefold()))


def split_outside_inside(
    sensors: Iterable[str], device_classes: Mapping[str, str | None], options: Mapping[str, Any]
) -> tuple[list[str], list[str]]:
    """Vorschlag: Türen/Fenster nach "Außen", Bewegung nach "Innen"."""
    stored_types = parse_types(options)
    outside: list[str] = []
    inside: list[str] = []
    for entity_id in sensors:
        kind = sensor_type(entity_id, device_classes.get(entity_id), stored_types)
        (inside if kind is SensorType.MOTION else outside).append(entity_id)
    return sorted(outside), sorted(inside)


def save_groups(
    options: Mapping[str, Any],
    groups: Sequence[tuple[str, Sequence[str]]],
    *,
    labels: Mapping[str, frozenset[str]] | None = None,
) -> Change:
    """Mehrere Meldergruppen nacheinander anlegen; leere werden übersprungen."""
    current: dict[str, Any] = dict(options)
    created: list[str] = []
    for name, entities in groups:
        if not entities:
            continue
        change = save_zone(
            current, None, {"name": name, "entities": list(entities)}, entities_by_label=labels
        )
        if not change.ok:
            return change
        assert change.options is not None
        current = change.options
        created.append(str(change.item_id))
    return Change(options=current, item_id=",".join(created) or None)


def set_entry_doors(
    options: Mapping[str, Any],
    outside: Iterable[str],
    entry_doors: Iterable[str],
    device_classes: Mapping[str, str | None],
) -> dict[str, Any]:
    """Nur gewählte Eingangstüren behalten die Eingangsverzögerung; andere Türen lösen sofort aus.

    Gespeichert werden nur Abweichungen vom Vorschlag der Geräteklasse.
    """
    stored = dict(options.get("sensor_types", {}))
    chosen = set(entry_doors)
    for entity_id in outside:
        proposal = sensor_type(entity_id, device_classes.get(entity_id), {})
        if entity_id in chosen:
            if proposal is SensorType.DOOR:
                stored.pop(entity_id, None)
            else:
                stored[entity_id] = SensorType.DOOR.value
        elif (SensorType(stored[entity_id]) if entity_id in stored else proposal) is (
            SensorType.DOOR
        ):
            stored[entity_id] = SensorType.OTHER.value
    new = dict(options)
    new["sensor_types"] = stored
    return new


def _main_profile_with_mode(options: Mapping[str, Any], mode: str) -> str | None:
    for info in profile_infos(options):
        if info.panel_mode == mode and profile_area(options, info.profile_id) == MAIN_AREA:
            return info.profile_id
    return None


def save_wizard_profile(  # noqa: PLR0913
    options: Mapping[str, Any],
    mode: str,
    data: Mapping[str, Any],
    *,
    language: str = "de",
    labels: Mapping[str, frozenset[str]] | None = None,
    new_only: Mapping[str, Any] | None = None,
) -> Change:
    """Vorgeschlagenes Profil (``away``/``night``) anlegen – oder das vorhandene mit demselben
    Bedienfeld-Knopf ergänzen statt ein zweites anzulegen. Nur übergebene Felder ändern sich;
    ``new_only`` gilt nur für ein neu angelegtes Profil (z. B. Ausgangsverzögerung 0 bei Nacht).
    """
    existing = _main_profile_with_mode(options, mode)
    if existing is not None:
        name = profile_info(options, existing).name
        return save_profile(
            options, existing, {**data, "name": name}, entities_by_label=labels, partial=True
        )
    texts = PROFILE_TEXTS[mode]["de" if language == "de" else "en"]
    name, icon = texts
    taken = {i.name.casefold() for i in profile_infos(options)}
    if name.casefold() in taken:
        name = f"{name} 2"
    return save_profile(
        options,
        None,
        {"name": name, "icon": icon, "panel_mode": mode, **(new_only or {}), **data},
        entities_by_label=labels,
        partial=True,
    )


def default_night_zones(
    options: Mapping[str, Any],
    device_classes: Mapping[str, str | None],
    labels: Mapping[str, frozenset[str]] | None = None,
) -> list[str]:
    """Nachts sinnvoll: Gruppen ohne Bewegungsmelder (man bewegt sich ja im Haus)."""
    zones = parse_zones(options)
    stored_types = parse_types(options)
    result = []
    for zone_id in zones:
        members = resolve_zones([zone_id], zones, labels or {})
        if members and all(
            sensor_type(e, device_classes.get(e), stored_types) is not SensorType.MOTION
            for e in members
        ):
            result.append(zone_id)
    return result


@dataclass(frozen=True)
class Status:
    """Was eingerichtet ist und was noch fehlt (für die Zusammenfassung)."""

    zones: list[str]
    rules: list[str]
    profiles: list[tuple[str, list[str], list[str]]]  # Name, Gruppen, Regeln
    recipients: bool
    sirens: bool
    users: bool


def status(options: Mapping[str, Any]) -> Status:
    zones = parse_zones(options)
    rules = parse_rules(options)
    profiles = []
    for info in profile_infos(options):
        stored = options.get("profiles", {}).get(info.profile_id, {})
        profiles.append(
            (
                info.name,
                [zones[z].name for z in stored.get("zones", []) if z in zones],
                [rules[r].name for r in stored.get("rules", []) if r in rules],
            )
        )
    recipients = bool(options.get("notify_system")) or any(
        p.get("notify") for p in options.get("profiles", {}).values() if isinstance(p, Mapping)
    )
    return Status(
        zones=[z.name for z in zones.values()],
        rules=[r.name for r in rules.values()],
        profiles=profiles,
        recipients=recipients,
        sirens=bool(options.get("sirens")),
        users=bool(options.get("users")),
    )
