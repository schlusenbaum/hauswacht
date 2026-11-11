"""Bereiche: unabhängig scharf schaltbare Teile, frei benannt.

Rein und ohne Home Assistant. Gespeichert unter ``options["areas"]`` als
``{bereich_id: {"name": …, "icon": …}}``. Den Hauptbereich (``main``) gibt es immer – er ist die
bisherige, einzige Anlage; seine Entitäts-IDs bleiben unverändert.

Jedes Alarmprofil gehört zu genau einem Bereich (``profile["area"]``, fehlt = Hauptbereich).
Meldergruppen und Auslöseregeln sind Bausteine für alle Bereiche. Immer aktive Melder,
Heimkehr-Beobachtung und die Erinnerung "Alle weg" gehören zum Hauptbereich.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

MAIN_AREA = "main"
DEFAULT_MAIN_NAME = "Haus"
DEFAULT_ICON = "mdi:home-outline"

# Nur für den Hauptbereich
MAIN_ONLY_KEYS = (
    "always_active",
    "homecoming_observe",
    "homecoming_persons",
    "reminder_persons",
    "reminder_profile",
)


@dataclass(frozen=True)
class Area:
    area_id: str
    name: str
    icon: str = DEFAULT_ICON


def parse_areas(options: Mapping[str, Any]) -> dict[str, Area]:
    """Alle Bereiche, der Hauptbereich zuerst."""
    raw = options.get("areas", {})
    raw = raw if isinstance(raw, Mapping) else {}
    main = raw.get(MAIN_AREA, {}) if isinstance(raw.get(MAIN_AREA), Mapping) else {}
    areas = {
        MAIN_AREA: Area(
            MAIN_AREA,
            str(main.get("name") or DEFAULT_MAIN_NAME),
            str(main.get("icon") or DEFAULT_ICON),
        )
    }
    for area_id, data in raw.items():
        if area_id == MAIN_AREA or not isinstance(data, Mapping):
            continue
        areas[str(area_id)] = Area(
            str(area_id), str(data.get("name") or area_id), str(data.get("icon") or DEFAULT_ICON)
        )
    return areas


def profile_area(options: Mapping[str, Any], profile_id: str) -> str:
    profiles = options.get("profiles", {})
    profile = profiles.get(profile_id, {}) if isinstance(profiles, Mapping) else {}
    area = profile.get("area") if isinstance(profile, Mapping) else None
    return area if isinstance(area, str) and area in parse_areas(options) else MAIN_AREA


def area_options(options: Mapping[str, Any], area_id: str) -> dict[str, Any]:
    """Optionen aus Sicht eines Bereichs: nur seine Alarmprofile, Hauptbereich-Teile nur dort."""
    view = dict(options)
    profiles = options.get("profiles", {})
    if isinstance(profiles, Mapping):
        view["profiles"] = {
            pid: data
            for pid, data in profiles.items()
            if profile_area(options, str(pid)) == area_id
        }
    if area_id != MAIN_AREA:
        for key in MAIN_ONLY_KEYS:
            view.pop(key, None)
    return view


def multi_area(options: Mapping[str, Any]) -> bool:
    return len(parse_areas(options)) > 1


ALL_PANEL_KEY = "all_panel"


def stale_area_device(identifier: str, entry_id: str, areas: set[str]) -> bool:
    """Gehört die Geräte-Kennung (``<eintrag>_<bereich>``) zu einem gelöschten Bereich?

    Das Hauswacht-Gerät selbst (Kennung = Eintrags-ID) ist nie veraltet.
    """
    prefix = f"{entry_id}_"
    if not identifier.startswith(prefix):
        return False
    return identifier[len(prefix) :] not in areas


def stale_all_panel(unique_id: str, entry_id: str, areas: set[str]) -> bool:
    """Bedienfeld "Alle Bereiche", obwohl es nur noch einen Bereich gibt?"""
    return unique_id == f"{entry_id}_{ALL_PANEL_KEY}" and len(areas) < 2
