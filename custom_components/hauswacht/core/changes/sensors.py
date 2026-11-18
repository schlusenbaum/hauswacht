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
from . import Change, copy_options, failed
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
    options: Mapping[str, Any],
    *,
    zones: Iterable[str],
    sensors: Iterable[str],
    sirens: Mapping[str, Any] | None = None,
) -> Change:
    """Immer aktiv: Gruppen und einzelne Melder.

    ``sirens`` (optional): sirens_enabled, sirens, siren_tone, siren_volume, reaction_time – wie
    im Dialog. Fehlt es, bleiben die Sirenen-Einstellungen, wie sie sind. Nur eingetragene
    Sirenen und Einbruchtöne zählen; Brandtöne sind hier nie möglich.
    """
    from ..siren_guard import BURGLAR_TONES, VOLUME_LEVELS  # noqa: PLC0415

    known = set(options.get("zones", {}))
    always = dict(options.get("always_active", {}) or {})
    always["zones"] = [z for z in zones if z in known]
    always["sensors"] = sorted({str(s) for s in sensors if "." in str(s)})
    if sirens is not None:
        registered = set(options.get("sirens", []))
        tone = sirens.get("siren_tone")
        volume = sirens.get("siren_volume")
        try:
            reaction = int(sirens.get("reaction_time") or 180)
        except (TypeError, ValueError):
            reaction = 180
        always.update(
            {
                "sirens_enabled": bool(sirens.get("sirens_enabled")),
                "sirens": [s for s in sirens.get("sirens") or [] if s in registered],
                "siren_tone": tone if tone in BURGLAR_TONES else "burglar",
                "siren_volume": volume if volume in VOLUME_LEVELS else "high",
                "reaction_time": min(max(reaction, 1), 3600),
            }
        )
    return Change(options={**options, "always_active": always})


def save_sensor(
    options: Mapping[str, Any],
    entity_id: str,
    data: Mapping[str, Any],
    *,
    labels: Mapping[str, frozenset[str]],
    device_class: str | None,
) -> Change:
    """Einen Melder bearbeiten: Gruppe, Typ, Immer aktiv, ausgenommen je Profil.

    ``data``: ``group`` (ID oder leer = keine), ``type``, ``always`` (bool), ``excluded``
    (Liste der Profile, in denen der Melder nicht allein auslöst), ``stale`` (eigene
    Funkstille-Grenze, siehe :func:`save_stale_override`).
    Kommt der Melder über ein Label in eine Gruppe, lässt sich die Gruppe hier nicht wechseln.
    """
    if "." not in entity_id:
        return failed({"base": "required"})
    zones = parse_zones(options)
    group = data.get("group") or None
    if group is not None and group not in zones:
        return failed({"group": "unknown_group"})
    by_label = [
        z.zone_id for z in zones.values() if z.label and entity_id in labels.get(z.label, ())
    ]
    if by_label and group not in by_label:
        return failed({"group": "group_by_label"})
    new: dict[str, Any] = dict(options)
    stored = {k: dict(v) for k, v in options.get("zones", {}).items()}
    for zone_id, zone in stored.items():
        entities = [e for e in zone.get("entities", []) if e != entity_id]
        if zone_id == group and not by_label:
            entities = sorted({*entities, entity_id})
        zone["entities"] = entities
    new["zones"] = stored
    kind = data.get("type")
    if kind:
        try:
            SensorType(kind)
        except ValueError:
            return failed({"type": "unknown_type"})
        new = apply_types(new, {entity_id: kind}, {entity_id: device_class})
    if "always" in data:
        always = dict(new.get("always_active", {}) or {})
        sensors = {s for s in always.get("sensors", []) if s != entity_id}
        if data.get("always"):
            sensors.add(entity_id)
        always["sensors"] = sorted(sensors)
        new["always_active"] = always
    if "excluded" in data:
        excluded = set(data.get("excluded") or [])
        profiles = {k: dict(v) for k, v in new.get("profiles", {}).items()}
        for profile_id, profile in profiles.items():
            current = {e for e in profile.get("excluded", []) or [] if e != entity_id}
            if profile_id in excluded and group in (profile.get("zones") or []):
                current.add(entity_id)
            if current or "excluded" in profile:
                profile["excluded"] = sorted(current)
        new["profiles"] = profiles
    if isinstance(data.get("stale"), Mapping):
        stale = data["stale"]
        change = save_stale_override(new, entity_id, str(stale.get("mode")), stale.get("hours"))
        if not change.ok or change.options is None:
            return change
        new = change.options
    return Change(options=new, item_id=entity_id)


STALE_DEFAULT = "default"  # allgemeiner Wert
STALE_HOURS = "hours"  # eigene Stunden
STALE_OFF = "off"  # nie prüfen
STALE_MODES = (STALE_DEFAULT, STALE_HOURS, STALE_OFF)


def save_stale_override(
    options: Mapping[str, Any], entity_id: str, mode: str, hours: Any = None
) -> Change:
    """Funkstille je Melder: allgemeiner Wert, eigene Stunden (1–168) oder nie prüfen.

    Gespeichert in ``stale_overrides`` = {Melder: Stunden}, 0 = nie prüfen.
    """
    from ..profiles import MAX_STALE_HOURS, OPT_STALE_OVERRIDES  # noqa: PLC0415

    if "." not in entity_id:
        return failed({"base": "required"})
    if mode not in STALE_MODES:
        return failed({"stale": "invalid"})
    overrides = {
        str(k): v for k, v in (options.get(OPT_STALE_OVERRIDES) or {}).items() if k != entity_id
    }
    if mode == STALE_OFF:
        overrides[entity_id] = 0
    elif mode == STALE_HOURS:
        try:
            value = int(hours)
        except (TypeError, ValueError):
            return failed({"stale_hours": "stale_hours_invalid"})
        if not 1 <= value <= MAX_STALE_HOURS:
            return failed({"stale_hours": "stale_hours_invalid"})
        overrides[entity_id] = value
    new = copy_options(options)
    new[OPT_STALE_OVERRIDES] = dict(sorted(overrides.items()))
    return Change(options=new, item_id=entity_id)


TARGET_ALWAYS = "__always__"  # Melder aus Messwert: in "Immer aktiv" einsetzen


def check_threshold_helper(
    options: Mapping[str, Any], data: Mapping[str, Any]
) -> tuple[dict[str, str], dict[str, Any]]:
    """Melder aus Messwert: Eingaben prüfen -> (Fehler, Daten für den Schwellenwert-Helfer).

    ``data``: source (sensor.…), name, upper, lower, hysteresis, type, target (Gruppe oder
    ``TARGET_ALWAYS``). Ob die Quelle existiert, prüft die Home-Assistant-Schicht.
    """
    errors: dict[str, str] = {}
    name = str(data.get("name") or "").strip()
    if not str(data.get("source") or "").startswith("sensor."):
        errors["source"] = "control_entity"
    if not name:
        errors["name"] = "helper_name"
    limits: dict[str, float] = {}
    for key in ("upper", "lower"):
        value = data.get(key)
        if value not in (None, ""):
            try:
                limits[key] = float(value)
            except (TypeError, ValueError):
                errors[key] = "invalid"
    if not limits and not errors:
        errors["base"] = "helper_no_limit"
    elif "upper" in limits and "lower" in limits and limits["lower"] > limits["upper"]:
        errors["base"] = "helper_range"
    try:
        hysteresis = float(data.get("hysteresis") or 0)
    except (TypeError, ValueError):
        errors["hysteresis"] = "invalid"
        hysteresis = 0.0
    if str(data.get("type") or "technical") not in {t.value for t in SensorType}:
        errors["type"] = "invalid"
    target = str(data.get("target") or TARGET_ALWAYS)
    if target != TARGET_ALWAYS and target not in options.get("zones", {}):
        errors["target"] = "invalid"
    payload = {"name": name, "entity_id": data.get("source"), "hysteresis": hysteresis, **limits}
    return errors, payload


def place_new_sensor(options: Mapping[str, Any], entity_id: str, kind: str, target: str) -> Change:
    """Neuen Melder mit Typ in eine Meldergruppe oder "immer aktiv" eintragen."""
    new = copy_options(options)
    types = dict(options.get("sensor_types", {}))
    types[entity_id] = kind
    new["sensor_types"] = types
    if target == TARGET_ALWAYS:
        always = dict(options.get("always_active", {}) or {})
        always["sensors"] = sorted({*always.get("sensors", []), entity_id})
        new["always_active"] = always
    else:
        zones = {k: dict(v) for k, v in options.get("zones", {}).items()}
        if target in zones:
            zones[target]["entities"] = sorted({*zones[target].get("entities", []), entity_id})
        new["zones"] = zones
    return Change(options=new, item_id=entity_id)
