"""Listen „Vorhanden:“ für die Menüs des Einstellungsdialogs und des Assistenten.

Überall, wo man etwas anlegen, bearbeiten oder löschen kann, steht oben, was es schon gibt –
z. B. „Vorhandene Meldergruppen: Außen (5 Melder), Innen (2 Melder)“. Nur Anzeige, keine Logik.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import MASTER_USER_ID
from .core.areas import MAIN_AREA, multi_area, parse_areas, profile_area
from .core.controls import parse_controls
from .core.profiles import profile_infos
from .core.rules import parse_rules
from .core.sensors import parse_zones, resolve_zone
from .core.tilt import parse_tilt_sources
from .core.users import parse_users
from .names import display_name
from .runtime import entities_by_label

KIND_NAMES: Mapping[str, Mapping[str, str]] = {
    "de": {
        "keypad": "Keypad",
        "sticker": "NFC-Aufkleber",
        "reader": "RFID-Leser",
        "button": "Taster",
        "lock": "Türschloss",
    },
    "en": {
        "keypad": "keypad",
        "sticker": "NFC sticker",
        "reader": "RFID reader",
        "button": "button",
        "lock": "door lock",
    },
}

HEADS: Mapping[str, Mapping[str, str]] = {
    "zones": {"de": "Vorhandene Meldergruppen", "en": "Existing sensor groups"},
    "profiles": {"de": "Vorhandene Alarmprofile", "en": "Existing alarm profiles"},
    "areas": {"de": "Vorhandene Bereiche", "en": "Existing areas"},
    "users": {"de": "Vorhandene Benutzer", "en": "Existing users"},
    "controls": {"de": "Vorhandene Bedienteile", "en": "Existing control devices"},
    "sirens": {"de": "Eingetragene Sirenen", "en": "Registered sirens"},
    "tilt": {"de": "Melder mit Kippstellung", "en": "Sensors with tilt position"},
}


def _block(kind: str, lang: str, lines: list[str]) -> str:
    head = HEADS[kind][lang]
    if not lines:
        return f"**{head}:** –\n\n"
    return f"**{head}:**\n" + "\n".join(f"- {line}" for line in lines) + "\n\n"


def zones_text(hass: HomeAssistant, options: Mapping[str, Any], lang: str) -> str:
    labels = entities_by_label(hass)
    lines = []
    for zone in parse_zones(options).values():
        count = len(resolve_zone(zone, labels))
        lines.append(
            f"{zone.name} ({count} Melder)" if lang == "de" else f"{zone.name} ({count} sensors)"
        )
    return _block("zones", lang, lines)


def profiles_text(options: Mapping[str, Any], lang: str) -> str:
    zones = parse_zones(options)
    rules = parse_rules(options)
    areas = parse_areas(options)
    several = multi_area(options)
    lines = []
    for info in profile_infos(options):
        stored = options.get("profiles", {}).get(info.profile_id, {})
        watched = [zones[z].name for z in stored.get("zones", []) if z in zones]
        watched += [rules[r].name for r in stored.get("rules", []) if r in rules]
        parts = [f"**{info.name}**"]
        if several:
            area = profile_area(options, info.profile_id)
            parts.append(f"({areas[area].name})" if area in areas else "")
        text = " ".join(p for p in parts if p)
        nothing = "überwacht nichts" if lang == "de" else "watches nothing"
        lines.append(f"{text} – {', '.join(watched) if watched else nothing}")
    return _block("profiles", lang, lines)


def areas_text(options: Mapping[str, Any], lang: str) -> str:
    main = "Hauptbereich" if lang == "de" else "main area"
    lines = [
        f"{area.name} ({main})" if area_id == MAIN_AREA else area.name
        for area_id, area in parse_areas(options).items()
    ]
    return _block("areas", lang, lines)


def users_text(options: Mapping[str, Any], lang: str) -> str:
    now = dt_util.utcnow().timestamp()
    de = lang == "de"
    lines = []
    for user in parse_users(options):
        if user.user_id == MASTER_USER_ID:
            continue
        marks = ["PIN ✓" if user.pin else ("ohne PIN" if de else "no PIN")]
        if user.tags:
            count = len(user.tags)
            marks.append(f"{count} Karte{'n' if count != 1 else ''}" if de else f"{count} card(s)")
        if not user.active:
            marks.append("inaktiv" if de else "inactive")
        elif not user.valid_at(now):
            marks.append("nicht gültig" if de else "not valid")
        lines.append(f"{user.name} ({', '.join(marks)})")
    return _block("users", lang, lines) + master_pin_text(options, lang) + "\n\n"


def master_pin_text(options: Mapping[str, Any], lang: str) -> str:
    """Nur ob es einen Master-PIN gibt – ohne Benutzer, ohne PIN."""
    exists = any(u.user_id == MASTER_USER_ID and u.pin for u in parse_users(options))
    if lang == "de":
        return "**Master-PIN:** ✅ eingerichtet" if exists else "**Master-PIN:** – keiner"
    return "**Master PIN:** ✅ set up" if exists else "**Master PIN:** – none"


def controls_text(options: Mapping[str, Any], lang: str) -> str:
    names = KIND_NAMES[lang if lang in KIND_NAMES else "en"]
    lines = [
        f"{control.name} ({names.get(control.kind.value, control.kind.value)})"
        for control in parse_controls(options).values()
    ]
    return _block("controls", lang, lines)


def sirens_text(hass: HomeAssistant, options: Mapping[str, Any], lang: str) -> str:
    de = lang == "de"
    lines = [display_name(hass, s) for s in options.get("sirens", []) if isinstance(s, str)]
    released = bool(options.get("sirens_hardware_enabled"))
    state = (
        ("Freigabe: **an**" if released else "Freigabe: **aus** (Sirenen bleiben stumm)")
        if de
        else ("Release: **on**" if released else "Release: **off** (sirens stay silent)")
    )
    return _block("sirens", lang, lines) + state + "\n\n"


def tilt_text(hass: HomeAssistant, options: Mapping[str, Any], lang: str) -> str:
    """Melder mit Kippstellung: Name, Quelle und Werte für zu und gekippt."""
    lines = []
    labels = entities_by_label(hass)
    zones = parse_zones(options)
    for source in sorted(
        parse_tilt_sources(options).values(),
        key=lambda s: display_name(hass, s.entity_id).casefold(),
    ):
        group = next(
            (z.name for z in zones.values() if source.entity_id in resolve_zone(z, labels)), None
        )
        closed = ", ".join(sorted(source.closed)) or "–"
        tilted = ", ".join(sorted(source.tilted)) or "–"
        where = group or ("keine Meldergruppe" if lang == "de" else "no group")
        if lang == "de":
            lines.append(
                f"{display_name(hass, source.entity_id)} – zu: {closed}; "
                f"gekippt: {tilted} ({where})"
            )
        else:
            lines.append(
                f"{display_name(hass, source.entity_id)} – closed: {closed}; tilted: {tilted} "
                f"({where})"
            )
    return _block("tilt", lang, lines)
