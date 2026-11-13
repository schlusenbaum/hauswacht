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
from .texts import DE, tr

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
# Englische Namen derselben Platzhalter – beide Schreibweisen gehen in jeder Sprache
ENGLISH_NAMES: Mapping[str, str] = {
    "area": "bereich",
    "profile": "profil",
    "sensor": "melder",
    "open": "offen",
    "who": "wer",
    "seconds": "sekunden",
    "time": "uhrzeit",
    "rule": "regel",
    "reason": "grund",
}
ALL_PLACEHOLDERS: frozenset[str] = frozenset(PLACEHOLDERS) | frozenset(ENGLISH_NAMES)


def placeholder_names(lang: str = DE) -> tuple[str, ...]:
    """Platzhalter für die Hilfe im Einstellungsdialog, in der Sprache von Home Assistant."""
    if lang == DE:
        return PLACEHOLDERS
    german_to_english = {v: k for k, v in ENGLISH_NAMES.items()}
    return tuple(german_to_english.get(p, p) for p in PLACEHOLDERS)


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


def check_template(template: str, lang: str = DE) -> None:
    """Wirft TemplateError bei unbekannten Platzhaltern, Formatangaben oder Klammerfehlern."""
    if len(template) > MAX_LENGTH:
        raise TemplateError(tr(lang, "tpl_too_long", max=MAX_LENGTH))
    try:
        parts = list(string.Formatter().parse(template))
    except ValueError as err:
        raise TemplateError(tr(lang, "tpl_braces")) from err
    for _literal, field, spec, conversion in parts:
        if field is None:
            continue
        if field not in ALL_PLACEHOLDERS:
            raise TemplateError(tr(lang, "tpl_unknown", field=f"{{{field}}}"))
        if spec or conversion:
            raise TemplateError(tr(lang, "tpl_format", field=f"{{{field}}}"))


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
    filled.update({english: filled[german] for english, german in ENGLISH_NAMES.items()})
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
    NotifyEvent.ALARM: "Attention, burglar alarm! Triggered by {sensor}.",
    NotifyEvent.ENTRY: "Entry delay running. Please disarm within {seconds} seconds.",
    NotifyEvent.ARMED: "Alarm system armed, profile {profile}.",
    NotifyEvent.DISARMED: "Alarm system disarmed.",
    NotifyEvent.ALARM_ENDED: "Alarm ended.",
    NotifyEvent.ARM_FAILED: "Arming not possible, profile {profile}. {reason}",
    NotifyEvent.AUTOMATION: "{text}",
    NotifyEvent.FAULT: "Alarm system fault. {text}",
    NotifyEvent.SYSTEM: "{text}",
    NotifyEvent.REMINDER: "The alarm system is still disarmed.",
    NotifyEvent.ALWAYS_ACTIVE: "Attention, {sensor} was triggered.",
    NotifyEvent.RULE_NOTIFY: "Trigger rule {rule} met by {sensor}.",
    NotifyEvent.ARM_HINT: "Note: {open} is open.",
    NotifyEvent.UNCONFIRMED: "{text}",
    NotifyEvent.UNCONFIRMED_FREQUENT: "{text}",
}


def default_speech(event: NotifyEvent, *, german: bool = True) -> str:
    return (DEFAULT_SPEECH_DE if german else DEFAULT_SPEECH_EN)[event]
