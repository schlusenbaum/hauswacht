"""Alarmprofile anlegen, ändern, löschen."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from ..always_active import DEFAULT_SETTLE
from ..areas import MAIN_AREA, profile_area
from ..automation import (
    ARRIVAL_AUTO_ONLY,
    ARRIVAL_DOOR,
    ARRIVAL_MODES,
    ARRIVAL_OFF,
    DEFAULT_ARRIVAL_WINDOW,
    DEFAULT_AWAY_DELAY,
    WEEKDAYS,
)
from ..passage import passage_from_input
from ..profiles import DEFAULT_ICON, PANEL_MODE_NONE, profile_infos
from ..rules import parse_rules
from ..sensors import parse_zones, resolve_zones, slugify
from . import Change, copy_options, failed

OPT_PROFILES = "profiles"
OPT_SIRENS = "sirens"


def automation_from_input(data: Mapping[str, Any]) -> dict[str, Any]:
    """Profil-Automatik aus dem Formular (Abschnitt "automation")."""
    mode = data.get("auto_arrival_mode")
    if mode not in ARRIVAL_MODES:
        mode = ARRIVAL_AUTO_ONLY if data.get("auto_disarm_on_arrival") else ARRIVAL_OFF
    return {
        "auto_arm_time": data.get("auto_arm_time") or None,
        "auto_disarm_time": data.get("auto_disarm_time") or None,
        "auto_weekdays": [d for d in data.get("auto_weekdays", []) if d in WEEKDAYS],
        "auto_away_persons": list(data.get("auto_away_persons") or []),
        "auto_away_delay": int(data.get("auto_away_delay", DEFAULT_AWAY_DELAY)),
        "auto_arrival_mode": mode,
        "auto_arrival_window": int(data.get("auto_arrival_window") or DEFAULT_ARRIVAL_WINDOW),
        "auto_schedule": data.get("auto_schedule") or None,
        # alter Schalter (bis 0.41) passend mitführen
        "auto_disarm_on_arrival": mode == ARRIVAL_AUTO_ONLY,
    }


def arm_on_close_from_input(data: Mapping[str, Any]) -> dict[str, Any]:
    """ "Scharf durch Schließen" aus dem Formular (Abschnitt "arm_on_close")."""
    return {
        "enabled": bool(data.get("enabled", False)),
        "doors": [d for d in data.get("doors") or [] if isinstance(d, str)],
        "settle": int(data.get("settle") or DEFAULT_SETTLE),
    }


def validate_profile(
    options: Mapping[str, Any],
    profile_id: str | None,
    data: Mapping[str, Any],
    *,
    entities_by_label: Mapping[str, frozenset[str]] | None = None,
) -> dict[str, str]:
    """Fehler je Feld (leer = in Ordnung)."""
    others = [i for i in profile_infos(options) if i.profile_id != profile_id]
    name = str(data.get("name") or "").strip()
    errors: dict[str, str] = {}
    if not name:
        errors["name"] = "profile_name_required"
    elif any(i.name.casefold() == name.casefold() for i in others):
        errors["name"] = "profile_name_taken"
    mode = data.get("panel_mode", PANEL_MODE_NONE)
    area = data.get("area") or (profile_area(options, profile_id) if profile_id else MAIN_AREA)
    same_area = [i for i in others if profile_area(options, i.profile_id) == area]
    if mode != PANEL_MODE_NONE and any(i.panel_mode == mode for i in same_area):
        errors["panel_mode"] = "panel_mode_taken"
    chosen = resolve_zones(data.get("zones") or [], parse_zones(options), entities_by_label or {})
    if set(data.get("excluded") or []) - chosen:
        errors["excluded"] = "excluded_not_in_groups"
    auto = data.get("automation") or {}
    if auto.get("auto_arrival_mode", ARRIVAL_OFF) != ARRIVAL_OFF and not auto.get(
        "auto_away_persons"
    ):
        errors["base"] = "arrival_needs_persons"
    passage = data.get("passage") or {}
    if (
        auto.get("auto_arrival_mode") == ARRIVAL_DOOR
        and passage.get("enabled")
        and passage.get("persons")
    ):
        # Dieselbe Heimkehr kann nicht zugleich unscharf schalten und nur reinlassen (ADR 0013)
        errors["base"] = "passage_door_proof"
    return errors


def _fields(options: Mapping[str, Any]) -> dict[str, Callable[[Mapping[str, Any]], Any]]:
    """Gespeicherter Wert je Schlüssel, berechnet aus der Eingabe (Standard bei fehlendem Feld)."""
    zones = parse_zones(options)
    rules = parse_rules(options)
    registered_sirens = [s for s in options.get(OPT_SIRENS, []) if isinstance(s, str)]

    def panel_mode(d: Mapping[str, Any]) -> str | None:
        mode = d.get("panel_mode", PANEL_MODE_NONE)
        return None if mode == PANEL_MODE_NONE else mode

    return {
        "icon": lambda d: d.get("icon") or DEFAULT_ICON,
        "panel_mode": panel_mode,
        "exit_delay": lambda d: int(d["exit_delay"]),
        "entry_delay": lambda d: int(d["entry_delay"]),
        "reaction_time": lambda d: int(d["reaction_time"]),
        "zones": lambda d: [z for z in d.get("zones", []) if z in zones],
        "excluded": lambda d: sorted(set(d.get("excluded") or [])),
        "rules": lambda d: [r for r in d.get("rules", []) if r in rules],
        "open_policy": lambda d: d["open_policy"],
        "unavailable_policy": lambda d: d["unavailable_policy"],
        "max_alarm_cycles": lambda d: int(d["max_alarm_cycles"]),
        "tamper_triggers_alarm": lambda d: bool(d["tamper_triggers_alarm"]),
        "sirens": lambda d: [s for s in d.get("sirens", []) if s in registered_sirens],
        "siren_tone": lambda d: d["siren_tone"],
        "siren_volume": lambda d: d["siren_volume"],
        "silent": lambda d: bool(d["silent"]),
        "notify": lambda d: list(d.get("notify", [])),
        "speakers": lambda d: list(d.get("speakers") or []),
    }


def save_profile(
    options: Mapping[str, Any],
    profile_id: str | None,
    data: Mapping[str, Any],
    *,
    entities_by_label: Mapping[str, frozenset[str]] | None = None,
    partial: bool = False,
) -> Change:
    """Alarmprofil anlegen (``profile_id=None``) oder ändern.

    ``partial=False`` (Einstellungsdialog): ``data`` ist das ganze Formular; fehlende Listen
    bedeuten "leer". ``partial=True`` (Assistent): nur die übergebenen Felder werden geändert,
    alles andere bleibt bzw. nimmt den Standardwert. Unbekannte gespeicherte Schlüssel bleiben
    immer erhalten.
    """
    errors = validate_profile(options, profile_id, data, entities_by_label=entities_by_label)
    if errors:
        return failed(errors)
    new = copy_options(options)
    profiles = {k: dict(v) for k, v in options.get(OPT_PROFILES, {}).items()}
    name = str(data["name"]).strip()
    new_id = profile_id or slugify(name, existing=profiles.keys())
    stored = dict(profiles.get(new_id, {}))
    if "area" in data:
        stored["area"] = data["area"]
    stored["name"] = name
    for key, convert in _fields(options).items():
        if partial and key not in data:
            continue
        stored[key] = convert(data)
    if not partial or "automation" in data:
        stored.update(automation_from_input(data.get("automation") or {}))
    elif "auto_schedule" in data:
        # Assistent: nur den Zeitplan setzen, die übrige Automatik bleibt
        stored["auto_schedule"] = data.get("auto_schedule") or None
    if "tilt_allowed" in data:
        # Nur im Formular, wenn es Melder mit Kippstellung gibt – sonst bleibt der Wert
        stored["tilt_allowed"] = bool(data["tilt_allowed"])
    if not partial or "arm_on_close" in data:
        stored["arm_on_close"] = arm_on_close_from_input(data.get("arm_on_close") or {})
    if not partial or "passage" in data:
        # Felder, die ein Formular nicht kennt (z. B. Personen im Dialog), bleiben erhalten
        before = stored.get("passage")
        merged = dict(before) if isinstance(before, Mapping) else {}
        merged.update(data.get("passage") or {})
        stored["passage"] = passage_from_input(merged)
    profiles[new_id] = stored
    new[OPT_PROFILES] = profiles
    return Change(options=new, item_id=new_id)


def delete_profile(options: Mapping[str, Any], profile_id: str) -> Change:
    """Alarmprofil löschen."""
    new = copy_options(options)
    new[OPT_PROFILES] = {k: v for k, v in options.get(OPT_PROFILES, {}).items() if k != profile_id}
    return Change(options=new, item_id=profile_id)
