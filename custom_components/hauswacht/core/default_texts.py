"""Standardtexte der Benachrichtigungen als Vorlage mit Platzhaltern.

Die Einstellungsseite zeigt beim Bearbeiten eines eigenen Texts zuerst den Text von Hauswacht –
als Vorlage, die man ändern kann. Die Vorlagen sind aus denselben Texten gebaut wie die echten
Nachrichten (``core.texts``), nur mit Platzhaltern statt Werten.

Wird eine Vorlage **unverändert** gespeichert, bleibt es beim Text von Hauswacht (es wird nichts
gespeichert) – dann kommen auch Zusätze wie die Liste der Sirenen weiter mit. Wo der Text von
Hauswacht je nach Lage anders aussieht (z. B. Störungen), ist die Vorlage ``{text}``: das ist der
vollständige Text von Hauswacht.

Rein und ohne Home Assistant.
"""

from __future__ import annotations

from .messages import ENGLISH_NAMES
from .notify_events import NotifyEvent
from .texts import DE, tr

FULL_TEXT = "{text}"

# Ereignisse mit festem Titel (Schlüssel in core.texts)
_TITLES: dict[NotifyEvent, str] = {
    NotifyEvent.ENTRY: "entry_title",
    NotifyEvent.ARMED: "armed_title",
    NotifyEvent.DISARMED: "disarmed_title",
    NotifyEvent.ALARM_ENDED: "alarm_ended_title",
    NotifyEvent.ARM_FAILED: "arm_failed_title",
    NotifyEvent.REMINDER: "reminder_title",
    NotifyEvent.ALWAYS_ACTIVE: "always_title",
    NotifyEvent.RULE_NOTIFY: "rule_notify_title",
    NotifyEvent.ARM_HINT: "arm_hint_title",
    NotifyEvent.UNCONFIRMED: "unconfirmed_title",
    NotifyEvent.UNCONFIRMED_FREQUENT: "lone_title",
    NotifyEvent.PASSAGE: "passage_title",
}


def _ph(name: str, lang: str) -> str:
    """Platzhalter in der Sprache von Home Assistant, z. B. ``{melder}`` bzw. ``{sensor}``."""
    if lang == DE:
        return f"{{{name}}}"
    english = {german: english for english, german in ENGLISH_NAMES.items()}
    return f"{{{english.get(name, name)}}}"


def default_title(event: NotifyEvent, lang: str = DE) -> str:
    if event is NotifyEvent.ALARM:
        return tr(lang, "alarm_title", prefix=tr(lang, "alarm_prefix"))
    key = _TITLES.get(event)
    return tr(lang, key) if key else FULL_TEXT


def default_message(event: NotifyEvent, lang: str = DE) -> str:
    sensor, profile = _ph("melder", lang), _ph("profil", lang)
    # "(von Anna)" fällt weg, wenn niemand bekannt ist – leere Klammern räumt render() auf
    who = f" ({_ph('wer', lang)})"
    if event is NotifyEvent.ALARM:
        return tr(lang, "alarm", prefix=tr(lang, "alarm_prefix"), sensor=sensor, profile=profile)
    if event is NotifyEvent.ENTRY:
        return tr(lang, "entry", sensor=sensor, seconds=_ph("sekunden", lang), profile=profile)
    if event is NotifyEvent.ARMED:
        return tr(lang, "armed", profile=profile, by=who)
    if event is NotifyEvent.DISARMED:
        return tr(lang, "disarmed", by=who)
    if event is NotifyEvent.ARM_FAILED:
        return tr(lang, "arm_failed", profile=profile, by=who, reason=_ph("grund", lang))
    if event is NotifyEvent.ALWAYS_ACTIVE:
        return tr(lang, "always", sensor=sensor)
    if event is NotifyEvent.RULE_NOTIFY:
        return tr(lang, "rule_notify", rule=_ph("regel", lang), sensor=sensor)
    return FULL_TEXT


def is_default(event: NotifyEvent, key: str, text: str, lang: str = DE) -> bool:
    """Steht im Feld noch genau die Vorlage (oder nichts)? Dann bleibt der Text von Hauswacht."""
    text = text.strip()
    if not text:
        return True
    template = default_title(event, lang) if key == "title" else default_message(event, lang)
    return text == template
