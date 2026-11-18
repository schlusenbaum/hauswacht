"""Aktions-Codes anlegen, ändern, löschen (Code + Taste am Keypad -> Aktion).

Dieselben Regeln wie im Dialog: Name eindeutig, 2–8 Ziffern, Code + Taste nicht doppelt (auch
nicht überlappend über „alle Keypads“), kein PIN. :func:`save_action_code` vergleicht mit den
PIN-Hashes (bewusst langsam) – im Executor aufrufen.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..action_codes import (
    ACTION_CODE_KEYS,
    ALL_KEYPADS,
    OPT_ACTION_CODES,
    CodeAction,
    action_code_clash,
    is_valid_action_code,
    parse_action_codes,
)
from ..controls import KEY_DAY
from ..profiles import profile_ids
from ..users import parse_users, pin_conflicts
from . import Change, copy_options, failed
from .users import unique_user_id


def save_action_code(
    options: Mapping[str, Any], code_id: str | None, data: Mapping[str, Any]
) -> Change:
    """``data``: name, code, key, keypad, action, profile (nur bei ``arm``)."""
    stored: dict[str, Any] = dict(options.get(OPT_ACTION_CODES, {}))
    if code_id is not None and code_id not in stored:
        return failed({"base": "unknown_action_code"})
    name = str(data.get("name") or "").strip()
    code = str(data.get("code") or "").strip()
    key = str(data.get("key") or KEY_DAY)
    keypad = str(data.get("keypad") or ALL_KEYPADS)
    action = str(data.get("action") or CodeAction.EVENT.value)
    profile = data.get("profile") or None
    errors: dict[str, str] = {}
    others = [c for c in parse_action_codes(options) if c.code_id != code_id]
    if not name:
        errors["name"] = "user_name_required"
    elif any(c.name.casefold() == name.casefold() for c in others):
        errors["name"] = "action_code_name_taken"
    if key not in ACTION_CODE_KEYS:
        errors["key"] = "invalid"
    if action not in {a.value for a in CodeAction}:
        errors["action"] = "invalid"
    clash = None
    if not is_valid_action_code(code):
        errors["code"] = "action_code_invalid"
    elif (clash := action_code_clash(others, code, key, keypad)) is not None:
        errors["code"] = "action_code_taken"
    if action == CodeAction.ARM.value and profile not in profile_ids(options):
        errors["profile"] = "action_code_profile_missing"
    if errors:
        return failed(errors, conflict=clash.name if clash else "")
    if pin_conflicts(code, parse_users(options), kind="duress"):
        return failed({"code": "action_code_is_pin"})
    entry: dict[str, Any] = {
        "name": name,
        "code": code,
        "key": key,
        "keypad": keypad,
        "action": action,
    }
    if action == CodeAction.ARM.value:
        entry["profile"] = profile
    new_id = code_id or unique_user_id(name, stored)
    stored[new_id] = entry
    new = copy_options(options)
    new[OPT_ACTION_CODES] = stored
    return Change(options=new, item_id=new_id)


def delete_action_code(options: Mapping[str, Any], code_id: str) -> Change:
    stored = dict(options.get(OPT_ACTION_CODES, {}))
    if code_id not in stored:
        return failed({"base": "unknown_action_code"})
    stored.pop(code_id)
    new = copy_options(options)
    new[OPT_ACTION_CODES] = stored
    return Change(options=new, item_id=code_id)
