"""Bedienteile anlegen und einstellen: Keypad, allgemeines Keypad, NFC-Aufkleber, RFID-Leser,
Taster, Türschloss.

Dieselben Regeln für Einstellungsdialog und Einstellungsseite. Das MQTT-Topic eines Keypads aus
dem gewählten Zigbee2MQTT-Gerät bildet die Home-Assistant-Schicht vorher (Geräteregister).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..areas import profile_area
from ..controls import ALL_AREAS, ARM_KEYS, ControlKind, normalize_tag
from ..keypad_input import RESERVED_BUTTONS, normalize_button
from ..profiles import profile_ids
from ..sensors import slugify
from . import Change, copy_options, failed

OPT_CONTROLS = "controls"
GENERIC_BUTTON_FIELDS = 4  # Dialog: so viele Tasten (Name + Profil) je allgemeinem Keypad


def generic_buttons(data: Mapping[str, Any]) -> dict[str, str]:
    """Tasten eines allgemeinen Keypads: ``buttons`` (Seite) oder ``button_n``/``profile_n``
    (Dialog). Tastennamen klein und ohne Leerzeichen; "disarm" und "emergency" sind fest."""
    pairs: list[tuple[Any, Any]] = []
    raw = data.get("buttons")
    if isinstance(raw, Mapping):
        pairs.extend(raw.items())
    for n in range(1, GENERIC_BUTTON_FIELDS + 1):
        pairs.append((data.get(f"button_{n}"), data.get(f"profile_{n}")))
    result: dict[str, str] = {}
    for name, profile in pairs:
        key = normalize_button(name)
        if key and profile and isinstance(profile, str):
            result[key] = profile
    return result


def validate_control(
    options: Mapping[str, Any], kind: ControlKind, data: Mapping[str, Any]
) -> dict[str, str]:
    """Fehler im Formular eines Bedienteils (Feld -> Fehlerschlüssel)."""
    errors: dict[str, str] = {}
    area = data.get("area") or ALL_AREAS
    profiles = [data.get("profile")] if kind is not ControlKind.KEYPAD else []
    if kind is ControlKind.BUTTON:
        profiles = list((data.get("presses") or {}).values())
    if kind is ControlKind.KEYPAD:
        profiles = [data.get(k) for k in ARM_KEYS]
        if not str(data.get("topic") or "").strip().strip("/"):
            errors["keypad_device"] = "control_keypad_topic"
    elif kind is ControlKind.GENERIC_KEYPAD:
        buttons = generic_buttons(data)
        profiles = list(buttons.values())
        if any(normalize_button(n) in RESERVED_BUTTONS for n in _button_names(data)):
            errors["base"] = "control_button_reserved"
        elif not buttons:
            errors["base"] = "control_no_buttons"
    elif (
        kind in (ControlKind.STICKER, ControlKind.READER)
        and data.get("action") in ("arm", "toggle")
        and not data.get("profile")
    ):
        errors["profile"] = "control_profile_required"
    if kind is ControlKind.STICKER and not normalize_tag(data.get("tag")):
        errors["tag"] = "control_tag"
    if kind is ControlKind.READER and not data.get("device"):
        errors["device"] = "control_device"
    if kind in (ControlKind.BUTTON, ControlKind.LOCK) and not data.get("entity"):
        errors["entity"] = "control_entity"
    if kind is ControlKind.LOCK:
        profiles = [data.get("profile")]
        if data.get("source") == "generic" and not data.get("who"):
            errors["who"] = "control_who"
        if data.get("source", "nuki_mqtt") == "nuki_mqtt" and not str(
            data.get("topic") or ""
        ).strip().strip("/"):
            errors["topic"] = "control_topic"
    for profile in profiles:
        if profile and area != ALL_AREAS and profile_area(options, profile) != area:
            errors["base"] = "control_profile_area"
    return errors


def _button_names(data: Mapping[str, Any]) -> list[Any]:
    raw = data.get("buttons")
    names = list(raw) if isinstance(raw, Mapping) else []
    names += [data.get(f"button_{n}") for n in range(1, GENERIC_BUTTON_FIELDS + 1)]
    return [n for n in names if n]


def control_data(
    kind: ControlKind, user_input: Mapping[str, Any], current: Mapping[str, Any]
) -> dict[str, Any]:
    """Gespeicherte Daten eines Bedienteils aus dem Formular."""
    data: dict[str, Any] = {
        "name": str(user_input.get("name") or "").strip() or kind.value,
        "kind": kind.value,
        "area": user_input.get("area") or ALL_AREAS,
    }
    if kind is ControlKind.KEYPAD:
        data["topic"] = str(user_input["topic"]).strip().rstrip("/")
        if user_input.get("keypad_device"):
            data["keypad_device"] = user_input["keypad_device"]
        data["buttons"] = {k: user_input[k] for k in ARM_KEYS if user_input.get(k)}
        data["login"] = user_input.get("login", "pin_or_card")
        data["emergency"] = user_input.get("emergency", "off")
    elif kind is ControlKind.GENERIC_KEYPAD:
        data["buttons"] = generic_buttons(user_input)
        data["login"] = user_input.get("login", "pin_or_card")
        data["emergency"] = user_input.get("emergency", "off")
    elif kind is ControlKind.BUTTON:
        data["entity"] = user_input["entity"]
        data["presses"] = dict(current.get("presses", {}))
    elif kind is ControlKind.LOCK:
        data["entity"] = user_input["entity"]
        data["source"] = user_input.get("source", "nuki_mqtt")
        data["topic"] = str(user_input.get("topic") or "").strip().rstrip("/")
        data["who"] = user_input.get("who") or ""
        data["profile"] = user_input.get("profile") or None
    else:
        data["action"] = user_input.get("action", "disarm")
        data["profile"] = user_input.get("profile") or None
    if kind is ControlKind.STICKER:
        data["tag"] = normalize_tag(user_input.get("tag"))
    if kind is ControlKind.READER:
        data["device"] = user_input.get("device")
        data["login"] = user_input.get("login", "card")
    return data


def save_control(
    options: Mapping[str, Any], control_id: str | None, data: Mapping[str, Any]
) -> Change:
    """Einstellungsseite: Bedienteil anlegen oder ändern, Taster gleich mit Druckarten.

    ``data``: kind und die Felder des Formulars; beim Taster zusätzlich ``presses``
    ({Druckart: Profil-ID}).
    """
    stored = {k: dict(v) for k, v in options.get(OPT_CONTROLS, {}).items()}
    if control_id is not None and control_id not in stored:
        return failed({"base": "unknown_control"})
    try:
        kind = ControlKind(str(data.get("kind") or stored.get(control_id or "", {}).get("kind")))
    except ValueError:
        return failed({"base": "unknown_control"})
    known = set(profile_ids(options))
    presses = {
        str(p).strip(): str(pid)
        for p, pid in (data.get("presses") or {}).items()
        if str(p).strip() and pid in known
    }
    errors = validate_control(options, kind, {**data, "presses": presses})
    if kind is ControlKind.BUTTON and not presses and not errors:
        errors["base"] = "button_no_press"
    if errors:
        return failed(errors)
    current = stored.get(control_id or "", {})
    entry = control_data(kind, data, current)
    if kind is ControlKind.BUTTON:
        entry["presses"] = presses
    new_id = control_id or slugify(entry["name"], existing=list(stored))
    stored[new_id] = entry
    new = copy_options(options)
    new[OPT_CONTROLS] = stored
    return Change(options=new, item_id=new_id)
