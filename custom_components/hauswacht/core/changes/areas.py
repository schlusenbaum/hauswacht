"""Bereiche anlegen und ändern (z. B. Haus und Einliegerwohnung)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..areas import DEFAULT_ICON, MAIN_AREA, parse_areas
from ..sensors import slugify
from . import Change, copy_options, failed

OPT_AREAS = "areas"


def save_area(options: Mapping[str, Any], area_id: str | None, data: Mapping[str, Any]) -> Change:
    """Bereich anlegen (``area_id=None``) oder ändern. ``data``: name, icon (optional)."""
    name = str(data.get("name") or "").strip()
    areas = parse_areas(options)
    if not name:
        return failed({"name": "area_name_required"})
    if any(a.name.casefold() == name.casefold() for a in areas.values() if a.area_id != area_id):
        return failed({"name": "area_name_taken"})
    stored = {k: dict(v) for k, v in options.get(OPT_AREAS, {}).items()}
    new_id = area_id or slugify(name, existing=[*stored.keys(), MAIN_AREA])
    entry = stored.get(new_id, {})
    entry.update({"name": name, "icon": data.get("icon") or DEFAULT_ICON})
    stored[new_id] = entry
    new = copy_options(options)
    new[OPT_AREAS] = stored
    return Change(options=new, item_id=new_id)
