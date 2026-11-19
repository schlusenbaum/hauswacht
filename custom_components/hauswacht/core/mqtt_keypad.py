"""MQTT-Schnittstelle (ADR 0012, Stufe 3) – rein und ohne Home Assistant.

Eine **MQTT-Schnittstelle** ist ein Keypad, das nur MQTT spricht: Wand-Tablet-Apps, Tasmota- oder
Arduino-Eigenbauten, Node-RED, andere Systeme. Hauswacht wertet seine Befehle mit demselben
Keypad-Kern aus wie jedes andere Keypad.

Topics (Basis z. B. ``hauswacht/flur``)::

    <basis>/set           rein   Befehl: Text (ARM_AWAY) oder JSON {"action", "code", "force", "id"}
    <basis>/state         raus   Zustand als Wort (gespeichert, retain)
    <basis>/attributes    raus   Details als JSON (gespeichert)
    <basis>/response      raus   Antwort auf jeden Befehl (JSON, nicht gespeichert)
    <basis>/availability  raus   online / offline (gespeichert)

Hier stehen: Befehle lesen, Zustandswörter (anpassbar) und die Prüfung des Basis-Topics.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .controls import KEY_DISARM, KEY_EMERGENCY
from .keypad_input import Display, normalize_button

DEFAULT_BASE = "hauswacht"
DEFAULT_CODE_FIELD = "code"
DEFAULT_DISARM_WORD = "DISARM"
DEFAULT_PANIC_WORD = "PANIC"
DEFAULT_MQTT_BUTTONS = ("arm_away", "arm_home", "arm_night")
MAX_PAYLOAD = 512  # Zeichen – längere Befehle werden ignoriert

# Zustandswörter wie die MQTT-Alarmzentrale von Home Assistant. Im Testmodus nie "triggered":
# Ein Gerät mit eigener Sirene soll nicht losheulen.
DEFAULT_STATE_WORDS: Mapping[str, str] = {
    Display.DISARMED: "disarmed",
    Display.EXIT_DELAY: "arming",
    Display.ARMED_HOME: "armed_home",
    Display.ARMED_AWAY: "armed_away",
    Display.ARMED_NIGHT: "armed_night",
    Display.ARMED_VACATION: "armed_vacation",
    Display.ARMED_CUSTOM_BYPASS: "armed_custom_bypass",
    Display.ENTRY_DELAY: "pending",
    Display.TRIGGERED: "triggered",
    Display.TEST_ALARM: "test_alarm",
    Display.FIRE: "triggered",
}

_WORD = re.compile(r"[\w\-]{1,64}")

TOPIC_SET = "set"
TOPIC_STATE = "state"
TOPIC_ATTRIBUTES = "attributes"
TOPIC_RESPONSE = "response"
TOPIC_AVAILABILITY = "availability"


@dataclass(frozen=True)
class MqttCommand:
    """Ein Befehl an eine MQTT-Schnittstelle."""

    button: str
    code: str | None = None
    force: bool = False
    request_id: Any = None


def parse_state_words(value: Any) -> dict[str, str]:
    """Eigene Zustandswörter: ``{Anzeige: Wort}``.

    Gespeichert als Mapping; im Formular als Text mit einer Zeile je Wort (``armed_away:
    ARMED_AWAY``). Unbekannte Zustände werden ignoriert.
    """
    pairs: list[tuple[Any, Any]]
    if isinstance(value, Mapping):
        pairs = list(value.items())
    elif isinstance(value, str):
        pairs = [tuple(line.split(":", 1)) for line in value.splitlines() if ":" in line]  # type: ignore[misc]
    else:
        return {}
    known = {d.value for d in Display}
    result: dict[str, str] = {}
    for key, word in pairs:
        state, text = str(key).strip(), str(word).strip()
        if state in known and text and len(text) <= 64:
            result[state] = text
    return result


def state_words_text(words: Mapping[str, str]) -> str:
    """Eigene Zustandswörter als Text fürs Formular."""
    return "\n".join(f"{state}: {word}" for state, word in words.items())


def state_word(display: str, words: Mapping[str, str]) -> str:
    return words.get(display) or DEFAULT_STATE_WORDS.get(display, display)


def parse_command(
    payload: Any,
    *,
    code_field: str = DEFAULT_CODE_FIELD,
    disarm_word: str = DEFAULT_DISARM_WORD,
    panic_word: str = DEFAULT_PANIC_WORD,
) -> MqttCommand | None:
    """Befehl lesen. Text (``ARM_AWAY``) oder JSON; None = kein gültiger Befehl.

    Das Befehlswort wird zur Taste (``ARM_AWAY`` → ``arm_away``); das Wort für Unscharf wird zu
    ``disarm``, das für Notruf zu ``emergency``.
    """
    if isinstance(payload, bytes):
        try:
            payload = payload.decode("utf-8")
        except UnicodeDecodeError:
            return None
    if not isinstance(payload, str):
        return None
    text = payload.strip()
    if not text or len(text) > MAX_PAYLOAD:
        return None
    word: Any
    code: Any = None
    force: Any = False
    request_id: Any = None
    if text.startswith("{"):
        try:
            data = json.loads(text)
        except ValueError:
            return None
        if not isinstance(data, dict):
            return None
        word = data.get("action", data.get("command"))
        code = data.get(code_field)
        force = data.get("force", False)
        request_id = data.get("id")
    else:
        word = text
    if not isinstance(word, (str, int)) or str(word).strip() == "":
        return None
    button = normalize_button(word)
    if not _WORD.fullmatch(button):
        return None  # kein Befehlswort (z. B. eine Liste oder Unsinn)
    if button == normalize_button(disarm_word):
        button = KEY_DISARM
    elif button == normalize_button(panic_word):
        button = KEY_EMERGENCY
    if isinstance(request_id, (dict, list)):
        request_id = None
    return MqttCommand(
        button=button,
        code=(str(code).strip() or None) if code not in (None, "") else None,
        force=force is True or str(force).lower() == "true",
        request_id=request_id,
    )


def validate_base_topic(topic: Any, others: list[str]) -> str | None:
    """Fehlerschlüssel für das Basis-Topic oder None.

    Keine Platzhalter (+, #), kein führender Schrägstrich, nicht unter ``zigbee2mqtt`` (dort
    lauschen die Zigbee2MQTT-Keypads) und nicht gleich oder überlappend mit einer anderen
    MQTT-Schnittstelle.
    """
    text = str(topic or "").strip().strip("/")
    if not text:
        return "mqtt_topic_missing"
    if any(c in text for c in "+#") or str(topic).strip().startswith("/"):
        return "mqtt_topic_invalid"
    if text.split("/")[0] == "zigbee2mqtt":
        return "mqtt_topic_z2m"
    for other in others:
        o = other.strip("/")
        if o and (text == o or text.startswith(o + "/") or o.startswith(text + "/")):
            return "mqtt_topic_taken"
    return None
