"""Bedienteile: Keypads, NFC-Aufkleber und RFID-Leser.

Rein und ohne Home Assistant.

**Bedienteil** = womit man bedient. Gespeichert unter ``options["controls"]``::

    <id>:
      name: "Keypad Flur"
      kind: keypad | sticker | reader
      area: <bereich> | "__all__"
      # keypad (Zigbee2MQTT, Alarm-Bedienteil nach Zigbee-Standard "IAS ACE"):
      topic: "zigbee2mqtt/Keypad Flur"
      buttons: {arm_day_zones: <profil>, arm_night_zones: <profil>, arm_all_zones: <profil>}
      login: pin_or_card | card_and_pin
      emergency: off | silent | alarm
      # sticker (NFC-Aufkleber, gescannt mit der Companion App):
      tag: "<tag-id>"
      action: disarm | arm | toggle
      profile: <profil>                      # für arm/toggle
      # reader (fester RFID-/NFC-Leser, z. B. ESPHome):
      device: "<geräte-id>"
      action / profile wie beim Aufkleber
      login: card | card_and_pin

**Ausweise** gehören zu den Benutzern: PIN (wie bisher) und RFID-Karten/-Anhänger
(``users.<id>.tags``). Ein NFC-Aufkleber ist KEIN Ausweis: Er sagt nur "hier, diese Aktion" –
ausgewiesen wird mit dem Handy eines bekannten Benutzers.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

ALL_AREAS = "__all__"
CARD_AND_PIN_WINDOW = 30.0  # s: zweiter Ausweis muss so schnell folgen


class ControlKind(StrEnum):
    KEYPAD = "keypad"
    STICKER = "sticker"
    READER = "reader"


class TagAction(StrEnum):
    DISARM = "disarm"
    ARM = "arm"
    TOGGLE = "toggle"


class Login(StrEnum):
    PIN_OR_CARD = "pin_or_card"
    CARD = "card"
    CARD_AND_PIN = "card_and_pin"


class Emergency(StrEnum):
    OFF = "off"
    SILENT = "silent"
    ALARM = "alarm"


# Tasten eines Zigbee-Alarm-Bedienteils (Zigbee2MQTT "action")
KEY_DISARM = "disarm"
KEY_DAY = "arm_day_zones"
KEY_NIGHT = "arm_night_zones"
KEY_ALL = "arm_all_zones"
KEY_EMERGENCY = "emergency"
ARM_KEYS = (KEY_DAY, KEY_NIGHT, KEY_ALL)
# Panel-Knopf -> Taste (Vorschlag, wenn nichts zugeordnet ist)
DEFAULT_KEY_FOR_MODE = {"home": KEY_DAY, "night": KEY_NIGHT, "away": KEY_ALL}


@dataclass(frozen=True)
class Control:
    control_id: str
    name: str
    kind: ControlKind
    area: str = ALL_AREAS
    topic: str = ""
    buttons: Mapping[str, str] = field(default_factory=dict)
    login: Login = Login.PIN_OR_CARD
    emergency: Emergency = Emergency.OFF
    tag: str = ""
    device: str = ""
    action: TagAction = TagAction.DISARM
    profile: str | None = None


def normalize_tag(value: Any) -> str:
    """Karten-/Aufkleber-IDs vergleichbar machen (Groß/klein, Trenner egal)."""
    return "".join(ch for ch in str(value or "").upper() if ch.isalnum())


def _enum(cls: type[StrEnum], value: Any, default: StrEnum) -> Any:
    try:
        return cls(value)
    except ValueError:
        return default


def looks_like_card(code: Any) -> bool:
    """Karten-ID statt PIN? PINs haben 4–8 Ziffern – alles andere ist sicher kein PIN.

    Nur solche Codes merkt sich Hauswacht als "unbekannte Karte" zum Anlernen; ein falsch
    eingetippter PIN wird so nie angezeigt.
    """
    tag = normalize_tag(code)
    return bool(tag) and (len(tag) > 8 or not tag.isdigit())


UNKNOWN_CARDS_KEPT = 10
DEFAULT_LEARN_MINUTES = 5
MAX_LEARN_MINUTES = 60


def learn_minutes(options: Mapping[str, Any]) -> int:
    """Wie lange eine unbekannte Karte zum Anlernen angeboten wird (0 = Anlernen aus)."""
    try:
        value = int(options.get("card_learn_minutes", DEFAULT_LEARN_MINUTES))
    except (TypeError, ValueError):
        return DEFAULT_LEARN_MINUTES
    return max(0, min(MAX_LEARN_MINUTES, value))


def fresh_cards(
    seen: Mapping[str, tuple[str, float]], now: float, minutes: int
) -> dict[str, tuple[str, float]]:
    """Nur Karten, die vor höchstens ``minutes`` Minuten gelesen wurden."""
    return {tag: info for tag, info in seen.items() if now - info[1] <= minutes * 60}


def remember_card(
    seen: dict[str, tuple[str, float]], tag: str, source: str, now: float
) -> dict[str, tuple[str, float]]:
    """Zuletzt gelesene unbekannte Karten (ID -> (Bedienteil, Zeitpunkt)), neueste zuerst."""
    tag = normalize_tag(tag)
    rest = {k: v for k, v in seen.items() if k != tag}
    newest = {tag: (source, now), **rest}
    return dict(list(newest.items())[:UNKNOWN_CARDS_KEPT])


def parse_controls(options: Mapping[str, Any]) -> dict[str, Control]:
    raw = options.get("controls", {})
    result: dict[str, Control] = {}
    if not isinstance(raw, Mapping):
        return result
    for control_id, data in raw.items():
        if not isinstance(data, Mapping):
            continue
        kind = _enum(ControlKind, data.get("kind"), ControlKind.KEYPAD)
        buttons = data.get("buttons", {})
        default_login = Login.CARD if kind is ControlKind.READER else Login.PIN_OR_CARD
        profile = data.get("profile")
        result[str(control_id)] = Control(
            control_id=str(control_id),
            name=str(data.get("name") or control_id),
            kind=kind,
            area=str(data.get("area") or ALL_AREAS),
            topic=str(data.get("topic") or "").strip().rstrip("/"),
            buttons={
                k: str(v) for k, v in buttons.items() if k in ARM_KEYS and isinstance(v, str) and v
            }
            if isinstance(buttons, Mapping)
            else {},
            login=_enum(Login, data.get("login"), default_login),
            emergency=_enum(Emergency, data.get("emergency"), Emergency.OFF),
            tag=normalize_tag(data.get("tag")),
            device=str(data.get("device") or ""),
            action=_enum(TagAction, data.get("action"), TagAction.DISARM),
            profile=profile if isinstance(profile, str) and profile else None,
        )
    return result


def sticker_for(controls: Mapping[str, Control], tag_id: str) -> Control | None:
    wanted = normalize_tag(tag_id)
    return next(
        (c for c in controls.values() if c.kind is ControlKind.STICKER and c.tag == wanted),
        None,
    )


def reader_for(controls: Mapping[str, Control], device_id: str | None) -> Control | None:
    if not device_id:
        return None
    return next(
        (c for c in controls.values() if c.kind is ControlKind.READER and c.device == device_id),
        None,
    )


def keypad_for_topic(controls: Mapping[str, Control], topic: str) -> Control | None:
    return next(
        (c for c in controls.values() if c.kind is ControlKind.KEYPAD and c.topic == topic),
        None,
    )


def tag_intent(action: TagAction, armed: bool) -> str:
    """Was ein Aufkleber/Leser jetzt tun soll: "disarm" oder "arm"."""
    if action is TagAction.TOGGLE:
        return "disarm" if armed else "arm"
    return action.value


# --- Rückmeldung an Zigbee-Keypads ---------------------------------------------------


def keypad_mode(state: str) -> str:
    """Zustand des Bedienfelds -> Anzeige am Keypad ("arm_mode" bei Zigbee2MQTT)."""
    if state == "triggered":
        return "in_alarm"
    if state == "pending":
        return "entry_delay"
    if state == "arming":
        return "exit_delay"
    if state == "disarmed":
        return "disarm"
    return {"armed_home": KEY_DAY, "armed_night": KEY_NIGHT}.get(state, KEY_ALL)


# Antworten auf eine Keypad-Anfrage
REPLY_INVALID_CODE = "invalid_code"
REPLY_NOT_READY = "not_ready"
REPLY_ALREADY_DISARMED = "already_disarmed"


@dataclass
class PendingLogin:
    """Erster Ausweis bei "Karte und PIN": wer, womit, wann."""

    user_ids: frozenset[str]
    kind: str  # "card" | "pin"
    at: float


def second_factor_ok(
    pending: PendingLogin | None, user_ids: frozenset[str], kind: str, now: float
) -> bool:
    """Passt der zweite Ausweis (andere Art, gleicher Benutzer, rechtzeitig) zum ersten?"""
    if pending is None or pending.kind == kind:
        return False
    if now - pending.at > CARD_AND_PIN_WINDOW:
        return False
    return bool(pending.user_ids & user_ids)
