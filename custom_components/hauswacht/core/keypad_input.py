"""Allgemeiner Keypad-Eingang (ADR 0012) – rein und ohne Home Assistant.

Ein **allgemeines Keypad** ist ein Bedienteil, das Hauswacht nicht selbst kennt (ZHA, Z-Wave,
ESPHome, Node-RED …). Ein Übersetzer (Blueprint, Automation, Gerät) ruft die Aktion
``hauswacht.keypad_input`` auf; Hauswacht wertet die Eingabe mit demselben Keypad-Kern aus wie
beim Zigbee2MQTT-Keypad und antwortet mit einem Ergebnis. Was das Keypad anzeigen soll, steht in
seiner Anzeige-Entität.

Hier liegen: die Ergebnisse, die Zuordnung zu den Antworten an Zigbee2MQTT-Keypads, die
Anzeige-Zustände, das Erkennen doppelter Meldungen und das Merken unbekannter Keypads.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from .controls import (
    KEY_DISARM,
    KEY_EMERGENCY,
    REPLY_ALREADY_DISARMED,
    REPLY_INVALID_CODE,
    REPLY_NOT_READY,
    Control,
    ControlKind,
)


class KeypadResult(StrEnum):
    """Antwort der Aktion ``hauswacht.keypad_input`` (öffentlich – nur erweitern)."""

    OK = "ok"
    INVALID_CODE = "invalid_code"  # falscher Ausweis oder keine Rechte (kein Unterschied!)
    LOCKED = "locked"  # zu viele Fehlversuche, gemeinsame Sperre läuft
    NOT_READY = "not_ready"  # Scharfschalten abgelehnt (offene/ausgefallene Melder …)
    PENDING = "pending"  # "Karte und PIN": erster Ausweis erkannt, zweiter fehlt noch
    ALREADY_DISARMED = "already_disarmed"
    UNKNOWN_BUTTON = "unknown_button"  # Taste ohne Profil
    UNKNOWN_KEYPAD = "unknown_keypad"  # Keypad ist in Hauswacht nicht angelegt


# Interne Ergebnisse, die nur das Zigbee2MQTT-Keypad unterscheidet
NOT_ALLOWED = "not_allowed"


@dataclass(frozen=True)
class InputOutcome:
    """Ergebnis einer Keypad-Eingabe – für alle Wege gleich."""

    result: str  # KeypadResult oder NOT_ALLOWED
    open_sensors: tuple[str, ...] = ()
    can_force: bool = False
    lock_seconds: int = 0
    # Aktions-Code ausgeführt (Zigbee2MQTT zeigt danach den Zustand statt der Taste)
    action_code: bool = False
    emergency: bool = False
    # Scharfschalten gescheitert und schon gemeldet ("Scharfschalten nicht möglich" mit Knöpfen)
    reported: bool = False


def public_result(outcome: InputOutcome) -> str:
    """Ergebnis für allgemeine Keypads: fehlende Rechte sehen aus wie ein falscher PIN."""
    if outcome.result == NOT_ALLOWED:
        return KeypadResult.INVALID_CODE.value
    return outcome.result


def z2m_reply(outcome: InputOutcome, button: str, display_mode: str) -> str | None:
    """Antwort an ein Zigbee2MQTT-Keypad – genau wie vor dem allgemeinen Eingang.

    None = keine Antwort senden (Notruf). ``display_mode`` ist die aktuelle Anzeige (nach einem
    Aktions-Code zeigt das Keypad den Zustand statt der Taste).
    """
    if outcome.emergency:
        return None
    result = outcome.result
    if result == KeypadResult.OK:
        return display_mode if outcome.action_code else button
    if result in (KeypadResult.INVALID_CODE, KeypadResult.LOCKED):
        return REPLY_INVALID_CODE
    if result == NOT_ALLOWED:
        # Unscharf ohne Recht: "falscher PIN"; scharf ohne Recht: wie bisher "nicht bereit"
        return REPLY_INVALID_CODE if button == KEY_DISARM else REPLY_NOT_READY
    if result == KeypadResult.ALREADY_DISARMED:
        return REPLY_ALREADY_DISARMED
    return REPLY_NOT_READY


# --- Tasten -------------------------------------------------------------------------

RESERVED_BUTTONS = frozenset({KEY_DISARM, KEY_EMERGENCY})
DEFAULT_GENERIC_BUTTONS = ("home", "away", "night")


def normalize_button(value: object) -> str:
    """Tastenname vergleichbar machen (Groß/klein und Leerzeichen egal)."""
    return str(value or "").strip().casefold().replace(" ", "_")


# --- Keypad finden ------------------------------------------------------------------


def generic_keypad_for(controls: Mapping[str, Control], ref: object) -> Control | None:
    """Allgemeines Keypad über Kennung, Namen oder Anzeige-Entität finden."""
    wanted = str(ref or "").strip()
    if not wanted:
        return None
    keypads = [c for c in controls.values() if c.kind is ControlKind.GENERIC_KEYPAD]
    for control in keypads:
        if control.control_id == wanted:
            return control
    folded = wanted.casefold()
    for control in keypads:
        if control.name.casefold() == folded:
            return control
    return None


# --- Doppelte Meldungen -------------------------------------------------------------

DUPLICATE_WINDOW = 2.0  # s


@dataclass
class RecentInputs:
    """Letzte Eingabe je Keypad: dieselbe Eingabe kurz danach zählt nicht noch einmal."""

    last: dict[str, tuple[str, float, InputOutcome]] = field(default_factory=dict)

    @staticmethod
    def key(button: str, code: str | None, force: bool) -> str:
        return f"{button}\x1f{code or ''}\x1f{int(force)}"

    def duplicate(self, keypad_id: str, key: str, now: float) -> InputOutcome | None:
        seen = self.last.get(keypad_id)
        if seen is None or seen[0] != key or now - seen[1] > DUPLICATE_WINDOW:
            return None
        return seen[2]

    def remember(self, keypad_id: str, key: str, now: float, outcome: InputOutcome) -> None:
        self.last[keypad_id] = (key, now, outcome)


# --- Unbekannte Keypads -------------------------------------------------------------

UNKNOWN_KEYPADS_KEPT = 5
UNKNOWN_KEYPAD_MINUTES = 60


def remember_unknown(
    seen: Mapping[str, float], ref: str, now: float, minutes: int = UNKNOWN_KEYPAD_MINUTES
) -> dict[str, float]:
    """Unbekannte Keypads (Kennung -> zuletzt gemeldet), neueste zuerst, alte fallen weg."""
    ref = ref.strip()[:64]
    fresh = {k: t for k, t in seen.items() if now - t <= minutes * 60 and k != ref}
    if not ref:
        return fresh
    return dict(list({ref: now, **fresh}.items())[:UNKNOWN_KEYPADS_KEPT])


# --- Anzeige ------------------------------------------------------------------------


class Display(StrEnum):
    """Zustände der Anzeige-Entität eines allgemeinen Keypads (öffentlich – nur erweitern)."""

    DISARMED = "disarmed"
    EXIT_DELAY = "exit_delay"
    ARMED_HOME = "armed_home"
    ARMED_AWAY = "armed_away"
    ARMED_NIGHT = "armed_night"
    ARMED_VACATION = "armed_vacation"
    ARMED_CUSTOM_BYPASS = "armed_custom_bypass"
    ENTRY_DELAY = "entry_delay"
    TRIGGERED = "triggered"
    TEST_ALARM = "test_alarm"
    FIRE = "fire"


_PANEL_TO_DISPLAY = {
    "disarmed": Display.DISARMED,
    "arming": Display.EXIT_DELAY,
    "pending": Display.ENTRY_DELAY,
    "triggered": Display.TRIGGERED,
    "armed_home": Display.ARMED_HOME,
    "armed_away": Display.ARMED_AWAY,
    "armed_night": Display.ARMED_NIGHT,
    "armed_vacation": Display.ARMED_VACATION,
    "armed_custom_bypass": Display.ARMED_CUSTOM_BYPASS,
}

# Reihenfolge, wenn ein Keypad mehrere Bereiche zeigt: Wichtigstes zuerst
_PRIORITY = (
    Display.TRIGGERED,
    Display.TEST_ALARM,
    Display.ENTRY_DELAY,
    Display.EXIT_DELAY,
)


def area_display(panel_state: str, *, test_mode: bool) -> Display:
    """Zustand eines Bereichs (Bedienfeld) -> Anzeige. Im Testmodus nie ``triggered``."""
    display = _PANEL_TO_DISPLAY.get(panel_state, Display.ARMED_AWAY)
    if display is Display.TRIGGERED and test_mode:
        return Display.TEST_ALARM
    return display


def combined_display(areas: list[Display], *, fire: bool) -> Display:
    """Mehrere Bereiche -> eine Anzeige. Brand hat Vorrang vor allem anderen."""
    if fire:
        return Display.FIRE
    for wanted in _PRIORITY:
        if wanted in areas:
            return wanted
    armed = [a for a in areas if a is not Display.DISARMED]
    if not armed:
        return Display.DISARMED
    return armed[0] if len(set(armed)) == 1 else Display.ARMED_AWAY
