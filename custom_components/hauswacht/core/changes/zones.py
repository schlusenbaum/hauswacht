"""Meldergruppen anlegen, ändern, löschen."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..sensors import Zone, parse_zones, slugify, zone_conflicts
from . import Change, copy_options, failed

OPT_ZONES = "zones"
OPT_PROFILES = "profiles"


def save_zone(
    options: Mapping[str, Any],
    zone_id: str | None,
    data: Mapping[str, Any],
    *,
    entities_by_label: Mapping[str, frozenset[str]] | None = None,
) -> Change:
    """Meldergruppe anlegen (``zone_id=None``) oder ändern.

    ``data``: ``name``, ``entities`` (Liste), ``label`` (optional).

    Regeln: Name nötig; mindestens ein Melder oder ein Label; ein Melder gehört zu genau einer
    Gruppe (sonst ``details["conflicts"]`` = {Melder: Name der anderen Gruppe}).
    """
    name = str(data.get("name") or "").strip()
    members = sorted({str(e) for e in data.get("entities") or ()})
    label = data.get("label") or None
    if not name:
        return failed({"name": "zone_name_required"})
    if not members and not label:
        return failed({"base": "zone_empty"})
    new = copy_options(options)
    zones = {k: dict(v) for k, v in options.get(OPT_ZONES, {}).items()}
    new_id = zone_id or slugify(name, existing=zones.keys())
    zone = Zone(zone_id=new_id, name=name, entities=frozenset(members), label=label)
    conflicts = zone_conflicts(zone, parse_zones(options), entities_by_label or {})
    if conflicts:
        return failed({"base": "zone_overlap"}, conflicts=conflicts)
    zones[new_id] = {"name": name, "entities": members, "label": label}
    new[OPT_ZONES] = zones
    return Change(options=new, item_id=new_id)


def delete_zone(options: Mapping[str, Any], zone_id: str) -> Change:
    """Meldergruppe löschen und aus allen Profilen entfernen."""
    new = copy_options(options)
    new[OPT_ZONES] = {k: v for k, v in options.get(OPT_ZONES, {}).items() if k != zone_id}
    profiles = {k: dict(v) for k, v in options.get(OPT_PROFILES, {}).items()}
    for settings in profiles.values():
        if "zones" in settings:
            settings["zones"] = [z for z in settings["zones"] if z != zone_id]
    new[OPT_PROFILES] = profiles
    return Change(options=new, item_id=zone_id)
