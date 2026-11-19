"""Bedienteile: Keypads, NFC-Aufkleber, RFID-Leser, Taster und Türschlösser.

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
      # generic_keypad (allgemeines Keypad, ADR 0012) – Eingabe über hauswacht.keypad_input:
      buttons: {<freier Tastenname>: <profil>}   # z. B. home, away, night
      login / emergency wie beim Keypad
      # sticker (NFC-Aufkleber, gescannt mit der Companion App):
      tag: "<tag-id>"
      action: disarm | arm | toggle
      profile: <profil>                      # für arm/toggle
      # reader (fester RFID-/NFC-Leser, z. B. ESPHome):
      device: "<geräte-id>"
      action / profile wie beim Aufkleber
      login: card | card_and_pin
      # button (Taster, z. B. Zigbee-Taster im Flur) – schaltet NUR scharf:
      entity: "event.taster_flur" | "sensor.taster_flur_action"
      presses: {single: <profil>, double: <profil>, long: <profil>}
      # lock (Türschloss) – unscharf beim Aufschließen durch einen bekannten Benutzer:
      entity: "lock.haustuer"
      source: nuki_mqtt | generic
      topic: "nuki/<id>"                      # nuki_mqtt: liest <topic>/lockActionEvent
      who: "sensor.haustuer_benutzer"         # generic: Wert = Kennung des Benutzers
      profile: <profil> | None                # optional: Abschließen von außen -> scharf

**Ausweise** gehören zu den Benutzern: PIN (wie bisher) und RFID-Karten/-Anhänger
(``users.<id>.tags``). Ein NFC-Aufkleber ist KEIN Ausweis: Er sagt nur "hier, diese Aktion" –
ausgewiesen wird mit dem Handy eines bekannten Benutzers.

Ein **Taster** ist ebenfalls kein Ausweis – deshalb schaltet er nur scharf. Ein **Türschloss**
weist aus, wenn es sagt, *wer* aufgeschlossen hat: Die Kennung (z. B. Nuki-Benutzer oder
Keypad-Code) gehört wie eine Karte zum Benutzer (gespeichert bei ``tags``, mit Präfix
``NUKIAUTH``/``NUKICODE``/``LOCK``, damit sie nie mit einer Karte oder einem PIN verwechselt
wird). Zusätzlich muss das Schloss in Home Assistant wirklich auf- bzw. zuschließen.
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
    BUTTON = "button"
    LOCK = "lock"
    # Allgemeines Keypad (ADR 0012): ZHA, Z-Wave, ESPHome … über die Aktion keypad_input
    GENERIC_KEYPAD = "generic_keypad"
    # MQTT-Schnittstelle (ADR 0012, Stufe 3): Befehle auf <topic>/set, Zustand auf <topic>/state
    MQTT_KEYPAD = "mqtt_keypad"


# Keypads, deren Tasten freie Namen haben
FREE_BUTTON_KINDS = frozenset({ControlKind.GENERIC_KEYPAD, ControlKind.MQTT_KEYPAD})


class LockSource(StrEnum):
    NUKI_MQTT = "nuki_mqtt"
    GENERIC = "generic"


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
    entity: str = ""
    presses: Mapping[str, str] = field(default_factory=dict)
    source: LockSource = LockSource.NUKI_MQTT
    who: str = ""
    # MQTT-Schnittstelle: eigene Zustandswörter, Name des Code-Felds, Wörter für Unscharf/Notruf
    words: Mapping[str, str] = field(default_factory=dict)
    code_field: str = "code"
    disarm_word: str = "DISARM"
    panic_word: str = "PANIC"


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


def is_random_uid(code: Any) -> bool:
    """Zufalls-UID nach ISO 14443-3: 4 Byte, erstes Byte 0x08 (z. B. Handys, manche Ausweise).

    Solche Nummern ändern sich bei jedem Lesen und taugen nicht als Ausweis. Eine feste 4-Byte-UID
    darf laut Norm nicht mit 0x08 beginnen.
    """
    tag = normalize_tag(code)
    return len(tag) == 8 and tag.startswith("08") and all(c in "0123456789ABCDEF" for c in tag)


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
            buttons=_buttons(kind, buttons),
            login=_enum(Login, data.get("login"), default_login),
            emergency=_enum(Emergency, data.get("emergency"), Emergency.OFF),
            tag=normalize_tag(data.get("tag")),
            device=str(data.get("device") or ""),
            action=_enum(TagAction, data.get("action"), TagAction.DISARM),
            profile=profile if isinstance(profile, str) and profile else None,
            entity=str(data.get("entity") or ""),
            presses=_presses(data.get("presses")),
            source=_enum(LockSource, data.get("source"), LockSource.NUKI_MQTT),
            who=str(data.get("who") or ""),
            words=_words(data.get("words")),
            code_field=str(data.get("code_field") or "code").strip() or "code",
            disarm_word=str(data.get("disarm_word") or "DISARM").strip() or "DISARM",
            panic_word=str(data.get("panic_word") or "PANIC").strip() or "PANIC",
        )
    return result


def _words(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping):
        return {}
    return {str(k): str(v) for k, v in value.items() if str(k).strip() and str(v).strip()}


def _buttons(kind: ControlKind, value: Any) -> dict[str, str]:
    """Tasten -> Profil. Zigbee2MQTT: feste Tasten; allgemeines Keypad: freie Namen."""
    if not isinstance(value, Mapping):
        return {}
    if kind in FREE_BUTTON_KINDS:
        result: dict[str, str] = {}
        for key, profile in value.items():
            name = str(key).strip().casefold().replace(" ", "_")
            reserved = name in (KEY_DISARM, KEY_EMERGENCY)
            if name and not reserved and isinstance(profile, str) and profile:
                result[name] = profile
        return result
    return {k: str(v) for k, v in value.items() if k in ARM_KEYS and isinstance(v, str) and v}


def _presses(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping):
        return {}
    return {str(k): str(v) for k, v in value.items() if str(k).strip() and isinstance(v, str) and v}


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


# --- Taster ---------------------------------------------------------------------------

IGNORED_VALUES = frozenset({"", "unknown", "unavailable", "none", "None"})


def press_value(domain: str, state: str | None, event_type: Any) -> str | None:
    """Welche Druckart? Ereignis-Entität: Attribut ``event_type``; Sensor: sein Wert."""
    value = event_type if domain == "event" else state
    if not isinstance(value, str) or value in IGNORED_VALUES:
        return None
    return value


def is_new_press(old_state: str | None, new_state: str | None) -> bool:
    """Wirklich gedrückt – nicht nur wieder verbunden oder nach einem Neustart geladen?

    - Ereignis-Entität: neuer Zeitstempel.
    - Sensor (Zigbee2MQTT "action"): Wert ändert sich auf eine Druckart.
    - Nie aus "nicht verfügbar" heraus (Gerät wieder verbunden, Zustand wiederhergestellt).
    """
    if old_state is None or new_state is None or new_state in IGNORED_VALUES:
        return False
    return old_state not in ("unavailable", new_state)


# --- Türschlösser ---------------------------------------------------------------------

LOCK_CONFIRM_WINDOW = 30.0  # s: Kennung und Zustand des Schlosses müssen so nah beieinander sein
UNLOCK = "unlock"
LOCK = "lock"
UNLOCKED_STATES = frozenset({"unlocked", "unlocking", "open", "opening"})
LOCKED_STATES = frozenset({"locked", "locking"})

# Nuki MQTT "lockActionEvent": "Aktion,Auslöser,Auth-ID,Code-ID,Zusatz"
NUKI_UNLOCK_ACTIONS = frozenset({1, 3})  # aufschließen, öffnen (Falle ziehen)
NUKI_LOCK_ACTIONS = frozenset({2, 4, 6})  # abschließen, Lock 'n' Go, voll abschließen
NUKI_PERSON_TRIGGER = 0  # App/Bluetooth, Keypad, Fob – ein Mensch mit Berechtigung
# Andere Auslöser zählen nie: 2 = Knopf am Schloss (innen), 3 = Zeitsteuerung,
# 6 = automatisch abschließen, 171 = HomeKit/Matter, 172 = MQTT (z. B. Home Assistant)


@dataclass(frozen=True)
class LockEvent:
    """Wer hat das Schloss betätigt? ``identity`` ist None, wenn das nicht erkennbar ist."""

    intent: str  # UNLOCK | LOCK
    identity: str | None
    reason: str = "ok"  # ok | not_by_person | no_id


def parse_nuki_event(payload: Any) -> LockEvent | None:
    """Nuki ``lockActionEvent`` lesen; None = keine Auf-/Zuschließ-Aktion (oder unlesbar)."""
    try:
        parts = [int(p.strip()) for p in str(payload).split(",")]
    except ValueError:
        return None
    if len(parts) < 4:
        return None
    action, trigger, auth_id, code_id = parts[:4]
    if action in NUKI_UNLOCK_ACTIONS:
        intent = UNLOCK
    elif action in NUKI_LOCK_ACTIONS:
        intent = LOCK
    else:
        return None
    if trigger != NUKI_PERSON_TRIGGER:
        return LockEvent(intent, None, "not_by_person")
    if code_id > 0:
        return LockEvent(intent, f"NUKICODE{code_id}")
    if auth_id > 0:
        return LockEvent(intent, f"NUKIAUTH{auth_id}")
    return LockEvent(intent, None, "no_id")


def generic_identity(value: Any) -> str | None:
    """Kennung aus einem beliebigen Sensor/Ereignis (z. B. Benutzername oder Nummer)."""
    if not isinstance(value, str) or value.strip() in IGNORED_VALUES:
        return None
    tag = normalize_tag(value)
    return f"LOCK{tag}" if tag else None


def lock_intent(old_state: str | None, new_state: str | None) -> str | None:
    """Zustandswechsel des Schlosses: aufgeschlossen, abgeschlossen oder nichts davon."""
    if old_state is None or new_state is None:
        return None
    if new_state in UNLOCKED_STATES and old_state not in UNLOCKED_STATES:
        return UNLOCK
    if new_state in LOCKED_STATES and old_state not in LOCKED_STATES:
        return LOCK
    return None


def lock_confirmed(
    identity_at: float | None, state_at: float | None, window: float = LOCK_CONFIRM_WINDOW
) -> bool:
    """Kennung und Zustandswechsel gehören zusammen (egal in welcher Reihenfolge)."""
    if identity_at is None or state_at is None:
        return False
    return abs(identity_at - state_at) <= window


def lock_id_label(tag: str, lang: str = "de") -> str:
    """Lesbare Form einer Schloss-Kennung für Formulare."""
    names = (
        (("NUKIAUTH", "Nuki-Benutzer "), ("NUKICODE", "Nuki-Keypad-Code "))
        if lang == "de"
        else (("NUKIAUTH", "Nuki user "), ("NUKICODE", "Nuki keypad code "))
    )
    for prefix, text in names:
        if tag.startswith(prefix):
            return text + tag[len(prefix) :]
    return tag


# --- Trotzdem scharf am Keypad ---------------------------------------------------

# So lange gilt ein zweiter Druck derselben Taste als Bestätigung
FORCE_ARM_WINDOW = 10.0

# Kein Ausweis (Scharfschalten ohne PIN ist erlaubt): leere Menge statt Benutzern
NOBODY: frozenset[str] = frozenset()


@dataclass(frozen=True)
class PendingForce:
    """Erster Versuch scharf zu schalten scheiterte an offenen Meldern ("nicht bereit").

    ``users``: wer es war – leer, wenn ohne PIN/Karte gedrückt wurde (nur möglich, wenn
    Scharfschalten ohne PIN erlaubt ist). ``identity``: der Ausweis des ersten Drucks, damit ein
    zweiter Druck ohne PIN in seinem Namen bestätigen kann (Rechte, "geändert von").
    """

    key: str
    users: frozenset[str]
    at: float
    identity: object = None


def pending_valid(pending: PendingForce | None, key: str, now: float) -> bool:
    """Gibt es zu dieser Taste eine Bestätigung, die noch gilt (gleiche Taste, rechtzeitig)?"""
    return pending is not None and pending.key == key and 0 <= now - pending.at <= FORCE_ARM_WINDOW


def force_confirmed(
    pending: PendingForce | None, key: str, users: frozenset[str], now: float
) -> bool:
    """Ist das der zweite Druck derselben Taste, rechtzeitig und durch dieselbe Person?

    - Beide Male mit Ausweis: dieselbe(n) Person(en).
    - Zweiter Druck ohne Ausweis (``users`` leer): bestätigt den ersten – egal ob der mit oder
      ohne PIN kam. Ob ein Druck ohne PIN überhaupt zählt, entscheidet der Aufrufer.
    - Erster Druck ohne Ausweis, zweiter mit: zählt (die Person darf "trotzdem scharf").
    """
    if pending is None or not pending_valid(pending, key, now):
        return False
    return not users or not pending.users or pending.users == users
