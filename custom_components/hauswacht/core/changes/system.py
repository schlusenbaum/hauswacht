"""Systemeinstellungen: Neustart, Funkstille, Funknetz, Anwesenheit, Bereiche, PIN-Regeln.

Dieselben Regeln wie im Einstellungsdialog – für die Einstellungsseite (ADR 0011, Stufe 5).
:func:`save_pin_rules` rechnet einen PIN-Hash (bewusst langsam) – im Executor aufrufen.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from ..action_codes import is_action_code, parse_action_codes
from ..areas import MAIN_AREA, parse_areas, profile_area
from ..away_proof import (
    OPT_AWAY_ACCURACY,
    OPT_AWAY_GEOFENCE,
    OPT_AWAY_WEAK,
    OPT_AWAY_WEAK_WINDOW,
    OPT_AWAY_WINDOW,
    parse_proof_settings,
)
from ..pin import hash_pin, is_valid_pin_format
from ..presence_rules import MODE_ALL, MODES, PersonRules, dump_presence_rules
from ..profiles import MAX_STALE_HOURS, profile_ids
from ..restart import (
    ARMED,
    BEHAVIORS,
    OPT_RESTART_BEHAVIOR,
    OPT_RESTART_CONTINUE_ALARM,
    OPT_RESTART_PROFILES,
)
from ..users import parse_users, pin_conflicts
from . import Change, copy_options, failed

OPT_STALE_AFTER_HOURS = "stale_after_hours"
OPT_INFRASTRUCTURE = "infrastructure"
OPT_HOMECOMING_OBSERVE = "homecoming_observe"
OPT_HOMECOMING_PERSONS = "homecoming_persons"
OPT_HOMECOMING_SSIDS = "homecoming_ssids"
OPT_HOMECOMING_SIGNALS = "homecoming_signals"
OPT_SETTINGS_PAGE = "settings_page"
OPT_AREAS = "areas"
OPT_USERS = "users"
OPT_CODE_ARM_REQUIRED = "code_arm_required"
OPT_END_ALARM_WITHOUT_PIN = "end_alarm_without_pin"
OPT_BUTTONS_WITHOUT_PIN = "buttons_without_pin"
OPT_CARD_PIN_UNLINKED = "card_pin_unlinked"
MASTER_USER_ID = "master"
MASTER_USER_NAME = "Master-PIN"


def _clean(values: Iterable[Any] | None) -> list[str]:
    return sorted({str(v) for v in values or [] if v})


def save_restart(options: Mapping[str, Any], data: Mapping[str, Any]) -> Change:
    """Verhalten nach Neustart. ``data``: behavior, continue_alarm, profiles {Bereich: Profil}."""
    behavior = str(data.get("behavior") or "")
    if behavior not in BEHAVIORS:
        return failed({"behavior": "invalid"})
    raw = data.get("profiles") if isinstance(data.get("profiles"), Mapping) else {}
    areas = parse_areas(options)
    chosen = {
        str(area): str(pid)
        for area, pid in (raw or {}).items()
        if pid
        and area in areas
        and pid in profile_ids(options)
        and profile_area(options, pid) == area
    }
    if behavior == ARMED and not chosen:
        return failed({"base": "restart_needs_profile"})
    new = copy_options(options)
    new[OPT_RESTART_BEHAVIOR] = behavior
    new[OPT_RESTART_PROFILES] = chosen
    new[OPT_RESTART_CONTINUE_ALARM] = bool(data.get("continue_alarm", False))
    return Change(options=new)


def save_silence(options: Mapping[str, Any], hours: Any) -> Change:
    """Maximale Funkstille in Stunden (0 = aus)."""
    try:
        value = int(hours or 0)
    except (TypeError, ValueError):
        return failed({"hours": "invalid"})
    new = copy_options(options)
    new[OPT_STALE_AFTER_HOURS] = min(max(value, 0), MAX_STALE_HOURS)
    return Change(options=new)


def save_infrastructure(options: Mapping[str, Any], entities: Iterable[Any] | None) -> Change:
    """Statussensoren der Funknetze und Gateways."""
    new = copy_options(options)
    new[OPT_INFRASTRUCTURE] = _clean(entities)
    return Change(options=new)


def save_homecoming(options: Mapping[str, Any], data: Mapping[str, Any]) -> Change:
    """Anwesenheit und Heimkehr-Beobachtung.

    ``data``: observe, persons, ssids (Liste oder Text mit Kommas), signals {Person: [Entitäten]},
    optional proof_window (Minuten), proof_accuracy (strict | simple), proof_weak (Personen mit
    „Tür + Signal“), proof_weak_window (Minuten) und proof_geofence (Signale, die als Ortung
    zählen – ADR 0018: Signale oder Tracker einer Person mit Geofence statt Koordinaten).
    """
    ssids = data.get("ssids") or []
    if isinstance(ssids, str):
        ssids = ssids.split(",")
    signals = data.get("signals") if isinstance(data.get("signals"), Mapping) else {}
    new = copy_options(options)
    new[OPT_HOMECOMING_OBSERVE] = bool(data.get("observe", False))
    new[OPT_HOMECOMING_PERSONS] = list(dict.fromkeys(str(p) for p in data.get("persons") or []))
    new[OPT_HOMECOMING_SSIDS] = [s.strip() for s in ssids if str(s).strip()]
    new[OPT_HOMECOMING_SIGNALS] = {
        str(person): _clean(entities) for person, entities in (signals or {}).items() if entities
    }
    # „weg“ nur mit Beleg (ADR 0015): nur übernehmen, wenn mitgeschickt (der Dialog kennt es nicht)
    keys = ("proof_window", "proof_accuracy", "proof_weak", "proof_weak_window", "proof_geofence")
    if any(key in data for key in keys):
        weak = data.get("proof_weak", options.get(OPT_AWAY_WEAK, []))
        proof = parse_proof_settings(
            {
                OPT_AWAY_WINDOW: data.get("proof_window", options.get(OPT_AWAY_WINDOW)),
                OPT_AWAY_ACCURACY: data.get("proof_accuracy", options.get(OPT_AWAY_ACCURACY)),
                OPT_AWAY_WEAK: list(weak) if isinstance(weak, list | tuple) else [],
                OPT_AWAY_WEAK_WINDOW: data.get(
                    "proof_weak_window", options.get(OPT_AWAY_WEAK_WINDOW)
                ),
                OPT_AWAY_GEOFENCE: list(
                    data.get("proof_geofence", options.get(OPT_AWAY_GEOFENCE)) or []
                ),
            }
        )
        new[OPT_AWAY_WINDOW] = proof.window
        new[OPT_AWAY_ACCURACY] = proof.accuracy
        new[OPT_AWAY_WEAK] = sorted(proof.weak)
        new[OPT_AWAY_WEAK_WINDOW] = proof.weak_window
        new[OPT_AWAY_GEOFENCE] = sorted(proof.geofence)
    # Ankommen/Weggehen je Person (ADR 0021): nur übernehmen, wenn mitgeschickt
    if isinstance(data.get("presence"), Mapping):
        new.update(_presence(data["presence"], new[OPT_HOMECOMING_SIGNALS]))
    return Change(options=new)


def _presence(raw: Mapping[str, Any], signals: Mapping[str, list[str]]) -> dict[str, Any]:
    """Regeln je Person aus dem Formular – nur Signale, die die Person wirklich hat."""
    rules: dict[str, PersonRules] = {}
    for person, data in raw.items():
        if not isinstance(person, str) or not isinstance(data, Mapping):
            continue
        own = {person, *signals.get(person, [])}

        def pick(key: str, own: set[str] = own, data: Mapping[str, Any] = data) -> frozenset[str]:
            value = data.get(key)
            items = value if isinstance(value, list | tuple) else []
            return frozenset(e for e in items if isinstance(e, str) and e in own)

        mode = data.get("mode")
        rule = PersonRules(
            arrive_off=pick("arrive_off"),
            leave_off=pick("leave_off"),
            mode=mode if mode in MODES else MODE_ALL,
            door=data.get("door", True) is not False,
        )
        if rule != PersonRules():
            rules[person] = rule
    return dump_presence_rules(rules)


def save_settings_page(options: Mapping[str, Any], enabled: bool) -> Change:
    new = copy_options(options)
    new[OPT_SETTINGS_PAGE] = bool(enabled)
    return Change(options=new)


def delete_area(options: Mapping[str, Any], area_id: str) -> Change:
    """Bereich löschen – nur ohne Profile; der Hauptbereich bleibt immer."""
    if area_id == MAIN_AREA or area_id not in options.get(OPT_AREAS, {}):
        return failed({"base": "unknown_area"})
    used = [pid for pid in profile_ids(options) if profile_area(options, pid) == area_id]
    if used:
        return failed({"base": "area_has_profiles"}, profiles=used)
    new = copy_options(options)
    new[OPT_AREAS] = {k: v for k, v in options.get(OPT_AREAS, {}).items() if k != area_id}
    users = {k: dict(v) for k, v in options.get(OPT_USERS, {}).items()}
    for data in users.values():
        if isinstance(data.get("areas"), list):
            data["areas"] = [a for a in data["areas"] if a != area_id]
        if isinstance(data.get("area_rights"), Mapping):
            data["area_rights"] = {k: v for k, v in data["area_rights"].items() if k != area_id}
    new[OPT_USERS] = users
    return Change(options=new, item_id=area_id)


def save_pin_rules(options: Mapping[str, Any], data: Mapping[str, Any]) -> Change:
    """PIN-Regeln und Master-PIN (intern ein Benutzer mit allen Rechten).

    ``data``: master_pin (leer = nicht ändern), remove_master_pin, code_arm_required,
    end_alarm_without_pin, buttons_without_pin, card_pin_unlinked. Langsam – im Executor.
    """
    master = str(data.get("master_pin") or "").strip()
    users_opt: dict[str, Any] = dict(options.get(OPT_USERS, {}))
    if data.get("remove_master_pin"):
        users_opt.pop(MASTER_USER_ID, None)
    elif master:
        if not is_valid_pin_format(master):
            return failed({"master_pin": "invalid_pin"})
        if is_action_code(parse_action_codes(options), master):
            return failed({"master_pin": "pin_is_action_code"})
        if found := pin_conflicts(master, parse_users(options), kind="pin"):
            return failed({"master_pin": "pin_is_duress"}, conflict=", ".join(found))
        hashed = hash_pin(master)
        users_opt[MASTER_USER_ID] = {
            **users_opt.get(MASTER_USER_ID, {}),
            "name": MASTER_USER_NAME,
            "pin_salt": hashed.salt,
            "pin_digest": hashed.digest,
        }
    new = copy_options(options)
    new[OPT_USERS] = users_opt
    for key in (OPT_CODE_ARM_REQUIRED, OPT_END_ALARM_WITHOUT_PIN, OPT_BUTTONS_WITHOUT_PIN):
        new[key] = bool(data.get(key, False))
    new[OPT_CARD_PIN_UNLINKED] = bool(data.get(OPT_CARD_PIN_UNLINKED, True))
    return Change(options=new)


def delete_control(options: Mapping[str, Any], control_id: str) -> Change:
    """Bedienteil entfernen (Anlegen und Anlernen bleibt im Dialog)."""
    stored = dict(options.get("controls", {}))
    if control_id not in stored:
        return failed({"base": "unknown_control"})
    stored.pop(control_id)
    new = copy_options(options)
    new["controls"] = stored
    return Change(options=new, item_id=control_id)


def save_learn_minutes(options: Mapping[str, Any], minutes: Any) -> Change:
    """Anlernzeit für neue Karten in Minuten (0 = Anlernen aus)."""
    from ..controls import MAX_LEARN_MINUTES  # noqa: PLC0415

    try:
        value = int(minutes or 0)
    except (TypeError, ValueError):
        return failed({"minutes": "invalid"})
    new = copy_options(options)
    new["card_learn_minutes"] = min(max(value, 0), MAX_LEARN_MINUTES)
    return Change(options=new)
