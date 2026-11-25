"""Gemeinsame Prüfung (ADR 0017): Fakten aus Home Assistant sammeln und der Websocket-Befehl.

Die Regeln stehen in ``core/advisor.py``. Hier wird nur eingesammelt, was dafür aus Home
Assistant kommt: wer geortet werden kann, wer ein Richtungs-Signal hat, die Eingangstüren je
Profil und die Messwerte der Heimkehr-Beobachtung.

``hauswacht/advisor/check`` prüft die gespeicherten Einstellungen – oder, mit ``action`` und
``data``, die Einstellungen, wie sie **nach** dieser Änderung wären. Gerechnet wird mit derselben
Logik wie beim Speichern (``apply_change``), gespeichert wird nichts. So zeigen die Seitenblätter
Hinweise schon vor dem Speichern. Der Befehl schaltet nichts und ändert nichts.

``hauswacht/advisor/scenarios`` rechnet die Szenario-Vorschau (``core/scenarios.py``) mit den
gespeicherten Einstellungen – nur gerechnet, nichts geschaltet.

``hauswacht/advisor/apply`` übernimmt **einen** Vorschlag aus dem Check-up (Reiter „Assistent“).
Sicherungen:

- nur Administratoren, nur wenn alle Bereiche unscharf sind und die Revision stimmt;
- nur ein Vorschlag, den der Assistent **gerade jetzt** selbst macht (nichts Beliebiges);
- Vorschläge, die die Anlage nachgiebiger machen (``weakens``), nur mit ``confirm``;
- gespeichert wird über dieselbe Logik wie im Seitenblatt (``profile_save`` bzw.
  ``homecoming_save``) – mit allen ihren Prüfungen.

Auch dieser Befehl ändert nur Einstellungen; er schaltet nichts und löst keine Sirene aus.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN
from .core.advisor import Facts, Measured, advise, find_fix, patch
from .core.automation import parse_automation
from .core.away_proof import parse_proof_settings
from .core.changes import Change
from .core.homecoming import DIRECTION_AWAY, DIRECTION_HOME, DIRECTION_NEUTRAL, door_proof_advice
from .core.homecoming import entry_stats as entry_stats_of
from .core.profiles import profile_behaviour, profile_ids
from .core.returning import parse_return
from .core.scenarios import scenarios
from .core.sensor_types import SensorType, default_type, excluded_sensors
from .core.sensors import parse_zones, resolve_zones
from .core.tilt import effective_types
from .names import plain_name
from .presence_proof import frozen_locations, locatable

WS_CHECK = f"{DOMAIN}/advisor/check"
WS_APPLY_FIX = f"{DOMAIN}/advisor/apply"
WS_SCENARIOS = f"{DOMAIN}/advisor/scenarios"
# Nur diese Änderungen lassen sich vorab prüfen (Seitenblätter Profil und Anwesenheit)
CHECK_ACTIONS = ("profile_save", "homecoming_save")
_DIRECTIONS = DIRECTION_HOME | DIRECTION_AWAY | DIRECTION_NEUTRAL


def _signals(options: Mapping[str, Any], person: str) -> tuple[str, ...]:
    raw = options.get("homecoming_signals", {})
    entities = raw.get(person, []) if isinstance(raw, Mapping) else []
    return tuple(e for e in entities if isinstance(e, str))


def _persons(options: Mapping[str, Any]) -> list[str]:
    found = [p for p in options.get("homecoming_persons", []) if isinstance(p, str)]
    found.extend(p for p in options.get("away_proof_weak", []) or [] if isinstance(p, str))
    for pid in profile_ids(options):
        found.extend(parse_automation(options, pid).away_persons)
        found.extend(parse_return(options, pid).persons)
    return list(dict.fromkeys(found))


def _has_direction(hass: HomeAssistant, signals: tuple[str, ...]) -> bool:
    return any(
        (state := hass.states.get(entity_id)) is not None and state.state in _DIRECTIONS
        for entity_id in signals
    )


def _members(
    hass: HomeAssistant, options: Mapping[str, Any]
) -> tuple[dict[str, tuple[str, ...]], dict[str, tuple[str, ...]]]:
    """Eingangstüren und Fenster je Profil (Melder der Meldergruppen, ohne Ausgenommene)."""
    from .runtime import device_class_of, entities_by_label  # noqa: PLC0415 – Import-Kreis

    zones = parse_zones(options)
    labels = entities_by_label(hass)
    types = effective_types(options)
    doors: dict[str, tuple[str, ...]] = {}
    windows: dict[str, tuple[str, ...]] = {}
    for pid in profile_ids(options):
        members = resolve_zones(profile_behaviour(options, pid).zones, zones, labels)
        members -= excluded_sensors(options, pid)
        kinds = {e: types.get(e, default_type(e, device_class_of(hass, e))) for e in members}
        doors[pid] = tuple(sorted(e for e, t in kinds.items() if t == SensorType.DOOR))
        windows[pid] = tuple(sorted(e for e, t in kinds.items() if t == SensorType.WINDOW))
    return doors, windows


def _measured(main: Any) -> tuple[dict[str, Measured], dict[str, Measured]]:
    observer = getattr(main, "homecoming", None)
    if observer is None or not observer.enabled:
        return {}, {}
    entry = {
        door: Measured(v["recommended_entry_delay"], v["max_seconds"], v["in_time"])
        for door, v in entry_stats_of(observer.entry_timings()).items()
        if v.get("recommended_entry_delay") is not None
    }
    proof = {
        person: Measured(v["recommended_entry_delay"], v["longest_after_door"], v["with_door"])
        for person, v in door_proof_advice(observer.stats()).items()
    }
    return entry, proof


def build_facts(
    hass: HomeAssistant,
    main: Any,
    options: Mapping[str, Any],
    extra_persons: tuple[str, ...] = (),
) -> Facts:
    """Fakten für die Prüfung; ``extra_persons``: zusätzlich (alle Personen fürs Einrichten)."""
    persons = list(dict.fromkeys([*_persons(options), *extra_persons]))
    entry, proof = _measured(main)
    doors, windows = _members(hass, options)
    frozen = {p: f for p in persons if (f := frozen_locations(hass, p, _signals(options, p)))}
    names = {p: plain_name(hass, p) for p in persons}
    names.update({e: plain_name(hass, e) for f in frozen.values() for e in f})
    for group in (doors, windows):
        names.update({e: plain_name(hass, e) for ids in group.values() for e in ids})
    return Facts(
        located=frozenset(p for p in persons if locatable(hass, p, _signals(options, p))),
        direction=frozenset(p for p in persons if _has_direction(hass, _signals(options, p))),
        entry_doors=doors,
        windows=windows,
        entry_needed=entry,
        proof_needed=proof,
        frozen=frozen,
        names=names,
    )


def check(
    hass: HomeAssistant, main: Any, options: Mapping[str, Any], language: str
) -> list[dict[str, Any]]:
    return advise(options, build_facts(hass, main, options), language)


def _language(hass: HomeAssistant, wanted: str | None) -> str:
    if wanted in ("de", "en"):
        return wanted
    return "de" if (hass.config.language or "").startswith("de") else "en"


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_CHECK,
        vol.Optional("action"): vol.In(CHECK_ACTIONS),
        vol.Optional("data", default={}): dict,
        vol.Optional("language"): str,
    }
)
@callback
def ws_advisor_check(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    from .settings_ws import _main, apply_change  # noqa: PLC0415

    main = _main(hass)
    if main is None:
        connection.send_error(msg["id"], "not_loaded", "Hauswacht ist nicht geladen.")
        return
    options: Mapping[str, Any] = main.entry.options
    item = None
    if action := msg.get("action"):
        # Wie nach dem Speichern – berechnet, nicht gespeichert
        change = apply_change(hass, main, action, msg["data"])
        if not change.ok or change.options is None:
            connection.send_result(msg["id"], {"findings": [], "errors": dict(change.errors)})
            return
        options = change.options
        item = change.item_id  # z. B. die ID eines neuen Profils
    language = _language(hass, msg.get("language"))
    connection.send_result(
        msg["id"], {"findings": check(hass, main, options, language), "item": item}
    )


def homecoming_payload(options: Mapping[str, Any]) -> dict[str, Any]:
    """Formular „Anwesenheit“ aus den gespeicherten Einstellungen (wie das Seitenblatt)."""
    proof = parse_proof_settings(options)
    signals = options.get("homecoming_signals", {})
    return {
        "observe": bool(options.get("homecoming_observe", False)),
        "persons": list(options.get("homecoming_persons", []) or []),
        "ssids": list(options.get("homecoming_ssids", []) or []),
        "signals": {k: list(v) for k, v in signals.items()} if isinstance(signals, Mapping) else {},
        "proof_window": proof.window,
        "proof_accuracy": proof.accuracy,
        "proof_weak": sorted(proof.weak),
        "proof_weak_window": proof.weak_window,
    }


def fix_change(hass: HomeAssistant, main: Any, fix: Mapping[str, Any]) -> Change:
    """Den Vorschlag ins passende Formular eintragen und wie beim Speichern rechnen."""
    from .profile_settings_ws import profile_payload  # noqa: PLC0415
    from .settings_ws import apply_change  # noqa: PLC0415

    options = main.entry.options
    path, op, value = str(fix["path"]), str(fix["op"]), fix["value"]
    if fix.get("profile"):
        if fix["profile"] not in options.get("profiles", {}):
            return Change(errors={"base": "unknown_profile"})
        form = profile_payload(options, str(fix["profile"]))
        patch(form, path, op, value)
        return apply_change(hass, main, "profile_save", form)
    if path != "away_proof_weak":
        return Change(errors={"base": "unknown_fix"})
    form = homecoming_payload(options)
    patch(form, "proof_weak", op, value)
    return apply_change(hass, main, "homecoming_save", form)


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_APPLY_FIX,
        vol.Required("revision"): str,
        vol.Required("fix"): dict,
        vol.Optional("confirm", default=False): bool,
        vol.Optional("language"): str,
    }
)
@callback
def ws_advisor_apply(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    from .settings_ws import _main, revision  # noqa: PLC0415

    main = _main(hass)
    if main is None:
        connection.send_error(msg["id"], "not_loaded", "Hauswacht ist nicht geladen.")
        return
    entry = main.entry
    if not main.all_disarmed:
        connection.send_result(msg["id"], {"ok": False, "errors": {"base": "disarm_first"}})
        return
    if msg["revision"] != revision(entry.options):
        connection.send_result(msg["id"], {"ok": False, "errors": {"base": "changed_elsewhere"}})
        return
    language = _language(hass, msg.get("language"))
    found = find_fix(check(hass, main, entry.options, language), msg["fix"])
    if found is None:
        # Nicht (mehr) vorgeschlagen – z. B. inzwischen behoben
        connection.send_result(msg["id"], {"ok": False, "errors": {"base": "fix_not_offered"}})
        return
    _finding, fix = found
    if fix["weakens"] and not msg["confirm"]:
        connection.send_result(msg["id"], {"ok": False, "errors": {"base": "confirm_needed"}})
        return
    change = fix_change(hass, main, fix)
    if not change.ok or change.options is None:
        connection.send_result(msg["id"], {"ok": False, "errors": dict(change.errors)})
        return
    hass.config_entries.async_update_entry(entry, options=change.options)
    connection.send_result(msg["id"], {"ok": True, "revision": revision(entry.options)})


@websocket_api.require_admin
@websocket_api.websocket_command(
    {vol.Required("type"): WS_SCENARIOS, vol.Optional("language"): str}
)
@callback
def ws_advisor_scenarios(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Szenario-Vorschau „Was passiert, wenn …?“ – nur gerechnet, nichts geschaltet."""
    from .settings_ws import _main  # noqa: PLC0415

    main = _main(hass)
    if main is None:
        connection.send_error(msg["id"], "not_loaded", "Hauswacht ist nicht geladen.")
        return
    options = main.entry.options
    facts = build_facts(hass, main, options)
    language = _language(hass, msg.get("language"))
    connection.send_result(msg["id"], {"scenarios": scenarios(options, facts, language)})


@callback
def async_register_advisor_websocket(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, ws_advisor_check)
    websocket_api.async_register_command(hass, ws_advisor_apply)
    websocket_api.async_register_command(hass, ws_advisor_scenarios)
