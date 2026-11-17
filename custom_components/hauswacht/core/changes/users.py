"""Benutzer anlegen, ändern, löschen; PIN und Bedrohungs-PIN setzen.

Achtung: :func:`set_pins` prüft und rechnet PIN-Hashes (bewusst langsam) – in Home Assistant
im Executor aufrufen, nie in der Ereignisschleife.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..action_codes import is_action_code, parse_action_codes
from ..pin import hash_pin, is_valid_pin_format
from ..users import RIGHTS_ALL, RIGHTS_PER_AREA, Action, parse_users, pin_conflicts
from . import Change, copy_options, failed

OPT_USERS = "users"
RIGHT_VALUES = (Action.ARM.value, Action.DISARM.value, Action.END_ALARM.value)


def unique_user_id(name: str, existing: Mapping[str, Any]) -> str:
    base = "".join(c if c.isalnum() else "_" for c in name.casefold()).strip("_") or "benutzer"
    candidate, number = base, 2
    while candidate in existing:
        candidate, number = f"{base}_{number}", number + 1
    return candidate


def _stored(options: Mapping[str, Any]) -> dict[str, Any]:
    return dict(options.get(OPT_USERS, {}))


def validate_user_name(
    options: Mapping[str, Any], user_id: str | None, name: str
) -> dict[str, str]:
    name = name.strip()
    if not name:
        return {"name": "user_name_required"}
    if any(
        str(d.get("name", "")).casefold() == name.casefold()
        for uid, d in _stored(options).items()
        if uid != user_id
    ):
        return {"name": "user_name_taken"}
    return {}


def save_user(
    options: Mapping[str, Any],
    user_id: str | None,
    data: Mapping[str, Any],
    *,
    ha_user: str | None = None,
) -> Change:
    """Benutzer anlegen (``user_id=None``) oder ändern – ohne PINs und Karten.

    ``data``: name, active, can_arm, can_disarm, can_end_alarm, can_force_arm, card_pin,
    valid_from/valid_until (ISO-Text oder None), rights ("all" | "per_area"). ``ha_user``:
    verknüpftes Home-Assistant-Konto (der Dialog ermittelt es auch aus dem Namen). Bei
    ``rights="per_area"`` folgt :func:`set_area_rights`. Gespeicherte PINs, Karten und
    unbekannte Schlüssel bleiben erhalten.
    """
    name = str(data.get("name") or "").strip()
    errors = validate_user_name(options, user_id, name)
    if errors:
        return failed(errors)
    users = _stored(options)
    stored = dict(users.get(user_id, {})) if user_id else {}
    stored.update(
        {
            "name": name,
            "active": bool(data.get("active", True)),
            "can_arm": bool(data.get("can_arm", True)),
            "can_disarm": bool(data.get("can_disarm", True)),
            "can_end_alarm": bool(data.get("can_end_alarm", True)),
            "can_force_arm": bool(data.get("can_force_arm", True)),
            "ha_user": ha_user,
            "card_pin": bool(data.get("card_pin", False)),
            "valid_from": data.get("valid_from") or None,
            "valid_until": data.get("valid_until") or None,
        }
    )
    if data.get("rights", RIGHTS_ALL) == RIGHTS_ALL:
        stored["rights"] = RIGHTS_ALL
        stored.pop("areas", None)
        stored.pop("area_rights", None)
    new_id = user_id or unique_user_id(name, users)
    users[new_id] = stored
    new = copy_options(options)
    new[OPT_USERS] = users
    return Change(options=new, item_id=new_id)


def set_area_rights(options: Mapping[str, Any], user_id: str, rights: Mapping[str, Any]) -> Change:
    """Rechte je Bereich: {Bereich-ID: ["arm", "disarm", "end_alarm"]}."""
    users = _stored(options)
    stored = dict(users[user_id])
    stored["rights"] = RIGHTS_PER_AREA
    stored["area_rights"] = {
        area_id: [a for a in actions or [] if a in RIGHT_VALUES]
        for area_id, actions in rights.items()
    }
    stored.pop("areas", None)
    users[user_id] = stored
    new = copy_options(options)
    new[OPT_USERS] = users
    return Change(options=new, item_id=user_id)


def delete_user(options: Mapping[str, Any], user_id: str) -> Change:
    new = copy_options(options)
    new[OPT_USERS] = {k: v for k, v in _stored(options).items() if k != user_id}
    return Change(options=new, item_id=user_id)


def validate_pins(
    options: Mapping[str, Any], user_id: str | None, new_pin: str, new_duress: str
) -> Change:
    """PIN-Regeln (leer = nicht ändern). Bei Fehlern ``details["conflict"]`` = Namen."""
    errors: dict[str, str] = {}
    if new_pin and not is_valid_pin_format(new_pin):
        errors["new_pin"] = "invalid_pin"
    if new_duress and not is_valid_pin_format(new_duress):
        errors["new_duress_pin"] = "invalid_pin"
    if new_pin and new_duress and new_pin == new_duress:
        errors["new_duress_pin"] = "duress_equals_pin"
    codes = parse_action_codes(options)
    for field, value in (("new_pin", new_pin), ("new_duress_pin", new_duress)):
        if value and field not in errors and is_action_code(codes, value):
            errors[field] = "pin_is_action_code"
    if errors:
        return failed(errors)
    users = parse_users(options)
    if new_pin and (found := pin_conflicts(new_pin, users, kind="pin")):
        return failed({"new_pin": "pin_is_duress"}, conflict=", ".join(found))
    if new_duress and (found := pin_conflicts(new_duress, users, kind="duress", exclude=user_id)):
        return failed({"new_duress_pin": "duress_conflict"}, conflict=", ".join(found))
    return Change(options=copy_options(options), item_id=user_id)


def set_pins(options: Mapping[str, Any], user_id: str, data: Mapping[str, Any]) -> Change:
    """PIN und Bedrohungs-PIN setzen, ändern oder entfernen.

    ``data``: new_pin, new_duress_pin (leer = nicht ändern), remove_pin, remove_duress_pin.
    Langsam (Hashes) – im Executor aufrufen.
    """
    new_pin = str(data.get("new_pin") or "").strip()
    new_duress = str(data.get("new_duress_pin") or "").strip()
    checked = validate_pins(options, user_id, new_pin, new_duress)
    if not checked.ok:
        return checked
    users = _stored(options)
    stored = dict(users[user_id])
    if data.get("remove_pin"):
        stored.pop("pin_salt", None)
        stored.pop("pin_digest", None)
    elif new_pin:
        hashed = hash_pin(new_pin)
        stored["pin_salt"], stored["pin_digest"] = hashed.salt, hashed.digest
    if data.get("remove_duress_pin"):
        stored.pop("duress_salt", None)
        stored.pop("duress_digest", None)
    elif new_duress:
        hashed = hash_pin(new_duress)
        stored["duress_salt"], stored["duress_digest"] = hashed.salt, hashed.digest
    users[user_id] = stored
    new = copy_options(options)
    new[OPT_USERS] = users
    return Change(options=new, item_id=user_id)
