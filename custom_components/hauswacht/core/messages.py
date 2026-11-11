"""Eigene Texte für Benachrichtigungen und Sprachausgabe: Platzhalter, Prüfung, Standardtexte.

Rein und ohne Home Assistant. Platzhalter werden in geschweiften Klammern geschrieben, z. B.
``Achtung, Einbruchalarm! Ausgelöst durch {melder}.`` Bewusst keine Vorlagensprache (Jinja):
einfach, sicher und beim Speichern vollständig prüfbar.

Fehlende Werte werden leer eingesetzt; doppelte Leerzeichen und Leerzeichen vor Satzzeichen
werden danach entfernt.
"""

from __future__ import annotations

import re
import string
from collections.abc import Mapping

from .notify_events import NotifyEvent

PLACEHOLDERS: tuple[str, ...] = (
    "bereich",  # Bereichsname (leer bei nur einem Bereich)
    "profil",  # Alarmprofil
    "melder",  # auslösender Melder mit Raum
    "offen",  # offene Melder
    "wer",  # wer geschaltet hat
    "sekunden",  # Eingangs- bzw. Ausgangsverzögerung
    "uhrzeit",  # aktuelle Uhrzeit (HH:MM)
    "regel",  # Auslöseregel
    "grund",  # Grund (z. B. warum Scharfschalten scheiterte)
    "text",  # der Standardtext von Hauswacht
)

# Beispielwerte für die Vorschau im Einstellungsdialog
EXAMPLE_VALUES_DE: Mapping[str, str] = {
    "bereich": "Garage",
    "profil": "Abwesend",
    "melder": "Küchenfenster (Küche)",
    "offen": "Terrassentür (Wohnzimmer)",
    "wer": "Christian",
    "sekunden": "30",
    "uhrzeit": "22:15",
    "regel": "Tür, dann Keller",
    "grund": "Offen: Terrassentür (Wohnzimmer)",
    "text": "Standardtext von Hauswacht",
}
EXAMPLE_VALUES_EN: Mapping[str, str] = {
    **EXAMPLE_VALUES_DE,
    "profil": "Away",
    "melder": "Kitchen window (Kitchen)",
    "offen": "Patio door (Living room)",
    "regel": "Door, then basement",
    "grund": "Open: Patio door (Living room)",
    "text": "Hauswacht's default text",
}

MAX_LENGTH = 500


class TemplateError(ValueError):
    """Text ist fehlerhaft (Meldung nennt die Stelle)."""


def check_template(template: str) -> None:
    """Wirft TemplateError bei unbekannten Platzhaltern, Formatangaben oder Klammerfehlern."""
    if len(template) > MAX_LENGTH:
        raise TemplateError(f"höchstens {MAX_LENGTH} Zeichen")
    try:
        parts = list(string.Formatter().parse(template))
    except ValueError as err:
        raise TemplateError("geschweifte Klammern passen nicht zusammen") from err
    for _literal, field, spec, conversion in parts:
        if field is None:
            continue
        if field not in PLACEHOLDERS:
            raise TemplateError(f"unbekannter Platzhalter {{{field}}}")
        if spec or conversion:
            raise TemplateError(f"{{{field}}}: keine Formatangaben erlaubt")


def _tidy(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" +([.,;:!?])", r"\1", text)
    text = re.sub(r"\(\s*\)", "", text)
    return text.strip()


def render(template: str, values: Mapping[str, str]) -> str:
    """Text mit Werten füllen. Ein fehlerhafter Text fällt auf ``{text}`` zurück."""
    try:
        check_template(template)
    except TemplateError:
        return _tidy(str(values.get("text", "")))
    filled = {key: str(values.get(key, "") or "") for key in PLACEHOLDERS}
    return _tidy(template.format(**filled))


# --- Standardtexte der Sprachausgabe ---------------------------------------------------

DEFAULT_SPEECH_DE: Mapping[NotifyEvent, str] = {
    NotifyEvent.ALARM: "Achtung, Einbruchalarm! Ausgelöst durch {melder}.",
    NotifyEvent.ENTRY: "Eingangsverzögerung läuft. Bitte innerhalb von {sekunden} Sekunden "
    "unscharf schalten.",
    NotifyEvent.ARMED: "Alarmanlage scharf geschaltet, Profil {profil}.",
    NotifyEvent.DISARMED: "Alarmanlage unscharf geschaltet.",
    NotifyEvent.ALARM_ENDED: "Alarm beendet.",
    NotifyEvent.ARM_FAILED: "Scharfschalten nicht möglich, Profil {profil}. {grund}",
    NotifyEvent.AUTOMATION: "{text}",
    NotifyEvent.FAULT: "Störung der Alarmanlage. {text}",
    NotifyEvent.SYSTEM: "{text}",
    NotifyEvent.REMINDER: "Die Alarmanlage ist noch unscharf.",
    NotifyEvent.ALWAYS_ACTIVE: "Achtung, {melder} hat ausgelöst.",
    NotifyEvent.RULE_NOTIFY: "Auslöseregel {regel} erfüllt durch {melder}.",
    NotifyEvent.ARM_HINT: "Hinweis: {offen} ist offen.",
    NotifyEvent.UNCONFIRMED: "{text}",
    NotifyEvent.UNCONFIRMED_FREQUENT: "{text}",
}
DEFAULT_SPEECH_EN: Mapping[NotifyEvent, str] = {
    NotifyEvent.ALARM: "Attention, burglar alarm! Triggered by {melder}.",
    NotifyEvent.ENTRY: "Entry delay running. Please disarm within {sekunden} seconds.",
    NotifyEvent.ARMED: "Alarm system armed, profile {profil}.",
    NotifyEvent.DISARMED: "Alarm system disarmed.",
    NotifyEvent.ALARM_ENDED: "Alarm ended.",
    NotifyEvent.ARM_FAILED: "Arming not possible, profile {profil}. {grund}",
    NotifyEvent.AUTOMATION: "{text}",
    NotifyEvent.FAULT: "Alarm system fault. {text}",
    NotifyEvent.SYSTEM: "{text}",
    NotifyEvent.REMINDER: "The alarm system is still disarmed.",
    NotifyEvent.ALWAYS_ACTIVE: "Attention, {melder} was triggered.",
    NotifyEvent.RULE_NOTIFY: "Trigger rule {regel} met by {melder}.",
    NotifyEvent.ARM_HINT: "Note: {offen} is open.",
    NotifyEvent.UNCONFIRMED: "{text}",
    NotifyEvent.UNCONFIRMED_FREQUENT: "{text}",
}


def default_speech(event: NotifyEvent, *, german: bool = True) -> str:
    return (DEFAULT_SPEECH_DE if german else DEFAULT_SPEECH_EN)[event]
