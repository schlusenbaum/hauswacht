"""Melder bearbeiten: Meldergruppen mit Typen und Fehlalarmschutz, Besondere Melder, Immer aktiv.

Für die Einstellungsseite (ADR 0011, Stufe 2). Nutzt dieselben Regeln wie der Dialog
(``save_zone``, ``delete_zone``, Kippstellung, Erschütterung).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from ..sensor_types import SensorType, default_type
from ..sensors import parse_zones, resolve_zone
from ..tilt import delete_tilt_source, effective_types, save_tilt_source
from ..vibration import (
    MAX_COUNT,
    MAX_WINDOW,
    MIN_WINDOW,
    delete_vibration_source,
    save_vibration_source,
    save_zone_rule,
)
from . import Change, failed
from .zones import delete_zone, save_zone

OPT_SENSOR_TYPES = "sensor_types"


def _default(options: Mapping[str, Any], entity_id: str, device_class: str | None) -> SensorType:
    """Vorgeschlagener Typ (wie im Dialog): Besondere Melder haben ihren eigenen Vorschlag."""
    special = effective_types({**options, OPT_SENSOR_TYPES: {}})
    return special.get(entity_id) or default_type(entity_id, device_class)


def apply_types(
    options: Mapping[str, Any],
    chosen: Mapping[str, str],
    device_classes: Mapping[str, str | None],
) -> dict[str, Any]:
    """Typen speichern – nur Abweichungen vom Vorschlag (wie der Dialog)."""
    new = dict(options)
    types = dict(options.get(OPT_SENSOR_TYPES, {}) or {})
    for entity_id, value in chosen.items():
        kind = SensorType(value)
        if kind is _default(options, entity_id, device_classes.get(entity_id)):
            types.pop(entity_id, None)
        else:
            types[entity_id] = kind.value
    new[OPT_SENSOR_TYPES] = types
    return new


def save_group(
    options: Mapping[str, Any],
    zone_id: str | None,
    data: Mapping[str, Any],
    *,
    labels: Mapping[str, frozenset[str]],
    device_classes: Mapping[str, str | None],
) -> Change:
    """Meldergruppe anlegen oder ändern – mit Typen und Fehlalarmschutz.

    ``data``: ``name``, ``entities``, ``label`` (optional), ``types`` ({Melder: Typ}, optional),
    ``vibration_count`` und ``vibration_window`` (optional).
    """
    types = data.get("types") or {}
    try:
        for value in types.values():
            SensorType(value)
    except ValueError:
        return failed({"types": "unknown_type"})
    count = data.get("vibration_count")
    window = data.get("vibration_window")
    if count is not None and not 1 <= int(count) <= MAX_COUNT:
        return failed({"vibration_count": "out_of_range"})
    if window is not None and not MIN_WINDOW <= int(window) <= MAX_WINDOW:
        return failed({"vibration_window": "out_of_range"})
    change = save_zone(
        options,
        zone_id,
        {"name": data.get("name"), "entities": data.get("entities"), "label": data.get("label")},
        entities_by_label=labels,
    )
    if not change.ok or change.options is None or change.item_id is None:
        return change
    new = apply_types(change.options, types, device_classes)
    if count is not None or window is not None:
        new = save_zone_rule(
            new,
            change.item_id,
            count=int(count if count is not None else 1),
            window=int(window if window is not None else 60),
        )
    return Change(options=new, item_id=change.item_id)


def remove_group(options: Mapping[str, Any], zone_id: str) -> Change:
    if zone_id not in options.get("zones", {}):
        return failed({"base": "unknown_group"})
    return delete_zone(options, zone_id)


def _add_to_group(
    options: dict[str, Any], entity_id: str, group: str | None, labels: Mapping[str, frozenset[str]]
) -> dict[str, Any]:
    """Melder in eine Meldergruppe aufnehmen – nur, wenn er noch in keiner steht."""
    zones = parse_zones(options)
    if not group or group not in zones:
        return options
    if any(entity_id in resolve_zone(z, labels) for z in zones.values()):
        return options
    stored = {k: dict(v) for k, v in options.get("zones", {}).items()}
    stored[group]["entities"] = sorted({*stored[group].get("entities", []), entity_id})
    return {**options, "zones": stored}


def save_tilt(
    options: Mapping[str, Any],
    data: Mapping[str, Any],
    *,
    labels: Mapping[str, frozenset[str]],
) -> Change:
    """Melder mit Kippstellung: ``entity``, ``attribute``, ``closed``, ``tilted``, ``group``."""
    entity_id = str(data.get("entity") or "")
    closed = [str(v) for v in data.get("closed") or []]
    tilted = [str(v) for v in data.get("tilted") or []]
    if "." not in entity_id:
        return failed({"entity": "required"})
    if not closed:
        return failed({"closed": "tilt_no_closed"})
    if {v.casefold() for v in closed} & {v.casefold() for v in tilted}:
        return failed({"tilted": "tilt_overlap"})
    new = save_tilt_source(
        options,
        entity_id,
        attribute=str(data.get("attribute") or "").strip() or None,
        closed=closed,
        tilted=tilted,
    )
    return Change(
        options=_add_to_group(new, entity_id, data.get("group"), labels), item_id=entity_id
    )


def remove_tilt(options: Mapping[str, Any], entity_id: str) -> Change:
    return Change(options=delete_tilt_source(options, entity_id), item_id=entity_id)


def save_strength(
    options: Mapping[str, Any],
    data: Mapping[str, Any],
    *,
    labels: Mapping[str, frozenset[str]],
) -> Change:
    """Erschütterungsstärke: ``entity``, ``threshold``, ``group``."""
    entity_id = str(data.get("entity") or "")
    if "." not in entity_id:
        return failed({"entity": "required"})
    try:
        threshold = float(data.get("threshold"))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return failed({"threshold": "required"})
    new = save_vibration_source(options, entity_id, threshold=threshold)
    return Change(
        options=_add_to_group(new, entity_id, data.get("group"), labels), item_id=entity_id
    )


def remove_strength(options: Mapping[str, Any], entity_id: str) -> Change:
    return Change(options=delete_vibration_source(options, entity_id), item_id=entity_id)


def save_always(
    options: Mapping[str, Any], *, zones: Iterable[str], sensors: Iterable[str]
) -> Change:
    """Immer aktiv: Gruppen und einzelne Melder (Sirenen-Einstellungen bleiben, wie sie sind)."""
    known = set(options.get("zones", {}))
    always = dict(options.get("always_active", {}) or {})
    always["zones"] = [z for z in zones if z in known]
    always["sensors"] = sorted({str(s) for s in sensors if "." in str(s)})
    return Change(options={**options, "always_active": always})
