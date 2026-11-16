"""Aktions-Codes: Code + Funktionstaste am Keypad löst eine festgelegte Aktion aus.

Beispiel: "7777 + Haus" = Ereignis "Außenlicht" für eine eigene Automation.

Ein Aktions-Code ist **kein Ausweis**: Er gehört keiner Person, ist nicht geheim und kann nie
unscharf schalten. Erlaubt sind nur:

- ``event``: Ereignis an der Entität ``event.hauswacht_aktions_code`` (für eigene Automationen –
  Hauswacht selbst schaltet dabei nichts),
- ``arm``: ein Alarmprofil scharf schalten,
- ``silent_emergency``: stiller Notruf (wie die SOS-Taste auf "still").

Gespeichert unter ``options["action_codes"] = {id: {name, code, key, keypad, action, profile}}``.
Der Code steht im Klartext in den Einstellungen – er ist kein Geheimnis wie ein PIN.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .controls import KEY_ALL, KEY_DAY, KEY_DISARM, KEY_NIGHT

OPT_ACTION_CODES = "action_codes"
ALL_KEYPADS = "all"
# Tasten, die einen Code mitschicken (SOS schickt keinen)
ACTION_CODE_KEYS = (KEY_DAY, KEY_NIGHT, KEY_ALL, KEY_DISARM)
CODE_MIN = 2
CODE_MAX = 8


class CodeAction(StrEnum):
    EVENT = "event"
    ARM = "arm"
    SILENT_EMERGENCY = "silent_emergency"


@dataclass(frozen=True)
class ActionCode:
    code_id: str
    name: str
    code: str
    key: str
    keypad: str = ALL_KEYPADS  # Bedienteil-ID oder "all"
    action: CodeAction = CodeAction.EVENT
    profile: str | None = None  # nur bei ARM

    def applies_to(self, keypad_id: str) -> bool:
        return self.keypad in (ALL_KEYPADS, keypad_id)


def is_valid_action_code(code: str) -> bool:
    return code.isdigit() and CODE_MIN <= len(code) <= CODE_MAX


def parse_action_codes(options: Mapping[str, Any]) -> tuple[ActionCode, ...]:
    stored = options.get(OPT_ACTION_CODES, {})
    if not isinstance(stored, Mapping):
        return ()
    result: list[ActionCode] = []
    for code_id, data in stored.items():
        if not isinstance(data, Mapping):
            continue
        code = str(data.get("code") or "")
        key = str(data.get("key") or "")
        if not is_valid_action_code(code) or key not in ACTION_CODE_KEYS:
            continue
        try:
            action = CodeAction(str(data.get("action") or CodeAction.EVENT))
        except ValueError:
            continue
        profile = data.get("profile")
        if action is CodeAction.ARM and not isinstance(profile, str):
            continue
        result.append(
            ActionCode(
                code_id=str(code_id),
                name=str(data.get("name") or code_id),
                code=code,
                key=key,
                keypad=str(data.get("keypad") or ALL_KEYPADS),
                action=action,
                profile=profile if isinstance(profile, str) else None,
            )
        )
    return tuple(result)


def find_action_code(
    codes: Iterable[ActionCode], code: str | None, key: str, keypad_id: str
) -> ActionCode | None:
    """Aktions-Code zu Code + Taste an diesem Keypad (ein bestimmtes Keypad vor "alle")."""
    if not code:
        return None
    matches = [c for c in codes if c.code == code and c.key == key and c.applies_to(keypad_id)]
    matches.sort(key=lambda c: c.keypad == ALL_KEYPADS)
    return matches[0] if matches else None


def action_code_clash(
    codes: Iterable[ActionCode], code: str, key: str, keypad: str, *, exclude: str | None = None
) -> ActionCode | None:
    """Gibt es schon einen Aktions-Code mit demselben Code und derselben Taste (überlappend)?"""
    for other in codes:
        if other.code_id == exclude or other.code != code or other.key != key:
            continue
        if ALL_KEYPADS in (keypad, other.keypad) or keypad == other.keypad:
            return other
    return None


def is_action_code(codes: Iterable[ActionCode], code: str) -> bool:
    """Ist dieser Code ein Aktions-Code (mit irgendeiner Taste)? Dann taugt er nicht als PIN."""
    return any(c.code == code for c in codes)
