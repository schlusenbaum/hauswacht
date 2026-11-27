"""Einrichten nach Zielen (ADR 0017, 0.65): Websocket-Befehle – nur für Administratoren.

- ``hauswacht/goals/start``: Haushalt (Personen mit Ortung/Richtung, Meldergruppen, Sirenen,
  Empfänger, vorhandene Profile für die Ziele) und vorgeschlagene Antworten.
- ``hauswacht/goals/plan``: aus den Antworten den Plan rechnen – „bisher → neu“ je Profil, dazu
  die Szenario-Vorschau und die Prüfung für die Einstellungen, wie sie danach wären. Gespeichert
  wird nichts.
- ``hauswacht/goals/apply``: den Plan übernehmen. Der Plan wird dafür **neu gerechnet** (die Seite
  schickt nur die Antworten, nie fertige Einstellungen). Nur unscharf, nur mit gültiger Revision,
  Überschreiben oder Abschwächen nur mit ``confirm``.

Die Regeln stehen in ``core/goals.py``. Hier wird nichts geschaltet, keine Sirene freigegeben und
kein Rauchmelder verändert. Sirenen von Rauchmeldern werden angeboten (seit 0.65.0b2), aber nur
eingetragen – als Einbruchsirene bekommen sie nur den Einbruchton und sind bei Brand gesperrt.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import floor_registry as fr

from .advisor_ws import build_facts
from .const import DOMAIN
from .core.advisor import advise
from .core.away_proof import parse_proof_settings
from .core.goals import (
    GOALS,
    RETURN_CHOICES,
    Household,
    SensorInfo,
    build,
    detectable,
    suggestions,
    targets,
)
from .core.profiles import profile_info
from .core.reactions import is_fire_indicator
from .core.scenarios import scenarios
from .core.sensor_types import SensorType, default_type
from .core.sensors import parse_zones, resolve_zone
from .core.tilt import effective_types
from .names import display_name, plain_name
from .notify_targets import notify_choices

WS_START = f"{DOMAIN}/goals/start"
WS_PLAN = f"{DOMAIN}/goals/plan"
WS_APPLY = f"{DOMAIN}/goals/apply"


def _language(hass: HomeAssistant, wanted: str | None) -> str:
    if wanted in ("de", "en"):
        return wanted
    return "de" if (hass.config.language or "").startswith("de") else "en"


def _smoke_detector(hass: HomeAssistant, entity_id: str) -> bool:
    """Gehört die Sirene zu einem Rauchmelder? Dann bietet der Assistent sie nie an."""
    registry = er.async_get(hass)
    entry = registry.async_get(entity_id)
    if entry is None or entry.device_id is None:
        return False
    return any(
        is_fire_indicator(s.entity_id, s.device_class or s.original_device_class)
        for s in er.async_entries_for_device(
            registry, entry.device_id, include_disabled_entities=True
        )
    )


def _sirens(hass: HomeAssistant, options: Mapping[str, Any]) -> list[str]:
    """Eingetragene und weitere Sirenen – auch die von Rauchmeldern (deutlich gekennzeichnet)."""
    registered = [s for s in options.get("sirens", []) if isinstance(s, str)]
    domains = ["siren", "switch"] if options.get("sirens_allow_switch") else ["siren"]
    found = [*registered, *(s.entity_id for s in hass.states.async_all(domains))]
    return list(dict.fromkeys(found))


_WATCHED = (SensorType.DOOR, SensorType.WINDOW, SensorType.MOTION)


def _place(hass: HomeAssistant, entity_id: str) -> str:
    """„Etage › Raum“ aus Entität bzw. Gerät (leer, wenn nichts zugeordnet ist)."""
    entry = er.async_get(hass).async_get(entity_id)
    area_id = entry.area_id if entry else None
    if area_id is None and entry is not None and entry.device_id is not None:
        device = dr.async_get(hass).async_get(entry.device_id)
        area_id = device.area_id if device else None
    area = ar.async_get(hass).async_get_area(area_id) if area_id else None
    if area is None:
        return ""
    floor = fr.async_get(hass).async_get_floor(area.floor_id) if area.floor_id else None
    return f"{floor.name} › {area.name}" if floor else area.name


def _sensors(hass: HomeAssistant, options: Mapping[str, Any]) -> tuple[SensorInfo, ...]:
    """Türen, Fenster, Bewegung: in Gruppen und frei (frei nur Binärsensoren mit passender Art)."""
    from .runtime import device_class_of, entities_by_label  # noqa: PLC0415 – Import-Kreis

    labels = entities_by_label(hass)
    types = effective_types(options)
    member_of: dict[str, str] = {}
    via_label: set[str] = set()
    for zone_id, zone in parse_zones(options).items():
        for entity_id in zone.entities:
            member_of[entity_id] = zone_id
        for entity_id in labels.get(zone.label, frozenset()) if zone.label else ():
            if entity_id not in zone.entities:
                member_of.setdefault(entity_id, zone_id)
                via_label.add(entity_id)
    candidates = [*member_of, *(s.entity_id for s in hass.states.async_all("binary_sensor"))]
    found: list[SensorInfo] = []
    for entity_id in dict.fromkeys(candidates):
        default = default_type(entity_id, device_class_of(hass, entity_id))
        kind = types.get(entity_id, default)
        grouped = entity_id in member_of
        if kind not in _WATCHED and not (kind == SensorType.OTHER and default in _WATCHED):
            continue
        if not grouped and default not in _WATCHED:
            continue
        found.append(
            SensorInfo(
                entity_id=entity_id,
                name=display_name(hass, entity_id),
                kind=kind.value,
                default=default.value,
                place=_place(hass, entity_id),
                group=member_of.get(entity_id),
                via_label=entity_id in via_label,
            )
        )
    return tuple(
        sorted(found, key=lambda s: (s.place == "", s.place.casefold(), s.name.casefold()))
    )


def _motion_groups(hass: HomeAssistant, options: Mapping[str, Any]) -> frozenset[str]:
    from .runtime import device_class_of, entities_by_label  # noqa: PLC0415 – Import-Kreis

    labels = entities_by_label(hass)
    types = effective_types(options)
    return frozenset(
        zone_id
        for zone_id, zone in parse_zones(options).items()
        if any(
            types.get(e, default_type(e, device_class_of(hass, e))) == SensorType.MOTION
            for e in resolve_zone(zone, labels)
        )
    )


def household(hass: HomeAssistant, main: Any, options: Mapping[str, Any]) -> Household:
    persons = tuple(s.entity_id for s in hass.states.async_all("person"))
    facts = build_facts(hass, main, options, persons)
    sirens = _sirens(hass, options)
    notify = notify_choices(hass)
    sensors = _sensors(hass, options)
    names = {s: display_name(hass, s) for s in sirens}
    names.update({n["id"]: n["name"] for n in notify})
    names.update({s.entity_id: s.name for s in sensors})
    return Household(
        persons=persons,
        facts=facts,
        motion_groups=_motion_groups(hass, options),
        sirens=tuple(sirens),
        smoke=frozenset(s for s in sirens if _smoke_detector(hass, s)),
        sensors=sensors,
        notify=tuple(n["id"] for n in notify),
        names=names,
    )


def _start(hass: HomeAssistant, main: Any) -> dict[str, Any]:
    options = main.entry.options
    hh = household(hass, main, options)
    weak = parse_proof_settings(options).weak
    can = detectable(options, hh)
    registered = set(options.get("sirens", []))
    found = targets(options)
    return {
        "revision": _revision(options),
        "editable": bool(main.all_disarmed),
        "goals": list(GOALS),
        "return_modes": list(RETURN_CHOICES),
        "persons": [
            {
                "id": p,
                "name": plain_name(hass, p),
                "located": p in hh.facts.located,
                "weak": p in weak,
                "direction": p in hh.facts.direction,
                "detectable": p in can,
                "frozen": p in hh.facts.frozen,
            }
            for p in hh.persons
        ],
        "groups": [
            {"id": zone_id, "name": zone.name, "motion": zone_id in hh.motion_groups}
            for zone_id, zone in parse_zones(options).items()
        ],
        "sirens": [
            {"id": s, "name": hh.name(s), "registered": s in registered, "smoke": s in hh.smoke}
            for s in hh.sirens
        ],
        "sensors": [
            {
                "id": s.entity_id,
                "name": s.name,
                "kind": s.kind,
                "place": s.place,
                "group": s.group,
                "via_label": s.via_label,
            }
            for s in hh.sensors
        ],
        "hardware_enabled": bool(options.get("sirens_hardware_enabled", False)),
        "notify": [{"id": n, "name": hh.name(n)} for n in hh.notify],
        "targets": {
            goal: ({"id": pid, "name": profile_info(options, pid).name} if pid else None)
            for goal, pid in found.items()
        },
        "answers": suggestions(options, hh),
    }


def _revision(options: Mapping[str, Any]) -> str:
    from .settings_ws import revision  # noqa: PLC0415

    return revision(options)


def _labels(hass: HomeAssistant) -> Mapping[str, frozenset[str]]:
    from .runtime import entities_by_label  # noqa: PLC0415

    return entities_by_label(hass)


def _main(hass: HomeAssistant) -> Any:
    from .settings_ws import _main as find  # noqa: PLC0415

    return find(hass)


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): WS_START})
@callback
def ws_goals_start(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    main = _main(hass)
    if main is None:
        connection.send_error(msg["id"], "not_loaded", "Hauswacht ist nicht geladen.")
        return
    connection.send_result(msg["id"], _start(hass, main))


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_PLAN,
        vol.Required("answers"): dict,
        vol.Optional("language"): str,
    }
)
@callback
def ws_goals_plan(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Plan, Vorschau und Prüfung – nur gerechnet, nichts gespeichert."""
    main = _main(hass)
    if main is None:
        connection.send_error(msg["id"], "not_loaded", "Hauswacht ist nicht geladen.")
        return
    options = main.entry.options
    language = _language(hass, msg.get("language"))
    hh = household(hass, main, options)
    plan, after = build(options, hh, msg["answers"], language, labels=_labels(hass))
    result: dict[str, Any] = {"plan": plan, "scenarios": [], "findings": []}
    if after is not None:
        facts = build_facts(hass, main, after, hh.persons)
        touched = set(plan["profiles"])
        result["scenarios"] = [
            s for s in scenarios(after, facts, language) if s["profile"] in touched
        ]
        result["findings"] = [f for f in advise(after, facts, language) if f["profile"] in touched]
    connection.send_result(msg["id"], result)


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_APPLY,
        vol.Required("revision"): str,
        vol.Required("answers"): dict,
        vol.Optional("confirm", default=False): bool,
        vol.Optional("language"): str,
    }
)
@callback
def ws_goals_apply(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Den Plan übernehmen – neu gerechnet aus den Antworten, mit allen Sicherungen."""
    main = _main(hass)
    if main is None:
        connection.send_error(msg["id"], "not_loaded", "Hauswacht ist nicht geladen.")
        return
    entry = main.entry
    if not main.all_disarmed:
        connection.send_result(msg["id"], {"ok": False, "errors": {"base": "disarm_first"}})
        return
    if msg["revision"] != _revision(entry.options):
        connection.send_result(msg["id"], {"ok": False, "errors": {"base": "changed_elsewhere"}})
        return
    language = _language(hass, msg.get("language"))
    hh = household(hass, main, entry.options)
    plan, after = build(entry.options, hh, msg["answers"], language, labels=_labels(hass))
    if after is None:
        connection.send_result(
            msg["id"], {"ok": False, "errors": {"base": "plan_invalid"}, "plan": plan}
        )
        return
    if plan["needs_confirm"] and not msg["confirm"]:
        connection.send_result(msg["id"], {"ok": False, "errors": {"base": "confirm_needed"}})
        return
    # Nie nebenbei freigeben: die Freigabe bleibt, wie sie war
    if bool(after.get("sirens_hardware_enabled")) != bool(
        entry.options.get("sirens_hardware_enabled")
    ):  # pragma: no cover - Schutz, save_sirens verhindert das schon
        connection.send_result(msg["id"], {"ok": False, "errors": {"base": "plan_invalid"}})
        return
    hass.config_entries.async_update_entry(entry, options=dict(after))
    connection.send_result(
        msg["id"], {"ok": True, "revision": _revision(entry.options), "profiles": plan["profiles"]}
    )


@callback
def async_register_goals_websocket(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, ws_goals_start)
    websocket_api.async_register_command(hass, ws_goals_plan)
    websocket_api.async_register_command(hass, ws_goals_apply)
