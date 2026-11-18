"""Empfänger und Benachrichtigungs-Einstellungen."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from ..notify_events import NotifyEvent
from . import Change, copy_options

OPT_NOTIFY_SYSTEM = "notify_system"
OPT_NOTIFY_IN_TEST_MODE = "notify_in_test_mode"
OPT_PUSH_DISARM = "push_disarm"
OPT_CRITICAL_ALERTS = "critical_alerts"
OPT_DURESS_NOTIFY = "duress_notify"
OPT_EVENTS = "events"
OPT_REMINDER_PERSONS = "reminder_persons"
OPT_REMINDER_PROFILE = "reminder_profile"
OPT_REMINDER_DELAY = "reminder_delay"
DEFAULT_REMINDER_DELAY = 15


def set_general_recipients(options: Mapping[str, Any], targets: Iterable[str]) -> Change:
    """Allgemeine Empfänger (für alle Ereignisse ohne eigene Empfänger)."""
    new = copy_options(options)
    new[OPT_NOTIFY_SYSTEM] = list(dict.fromkeys(str(t) for t in targets))
    return Change(options=new)


def save_notify_settings(options: Mapping[str, Any], data: Mapping[str, Any]) -> Change:
    """Das ganze Formular "Benachrichtigungen – Einstellungen".

    Eigene Texte je Ereignis (title/message) bleiben erhalten; Ereignisse, die im Formular fehlen,
    bleiben wie gespeichert.
    """
    new = copy_options(options)
    new[OPT_NOTIFY_SYSTEM] = list(data.get(OPT_NOTIFY_SYSTEM) or [])
    new[OPT_NOTIFY_IN_TEST_MODE] = bool(data.get(OPT_NOTIFY_IN_TEST_MODE))
    new[OPT_PUSH_DISARM] = bool(data.get(OPT_PUSH_DISARM))
    new[OPT_CRITICAL_ALERTS] = bool(data.get(OPT_CRITICAL_ALERTS, True))
    new[OPT_DURESS_NOTIFY] = list(data.get(OPT_DURESS_NOTIFY) or [])
    stored_events = options.get(OPT_EVENTS, {})
    events: dict[str, dict[str, Any]] = {}
    for event in NotifyEvent:
        given = data.get(f"event_{event.value}")
        if isinstance(given, dict):
            events[event.value] = {
                **stored_events.get(event.value, {}),
                "enabled": bool(given.get("enabled")),
                "targets": list(given.get("targets") or []),
            }
        elif event.value in stored_events:
            events[event.value] = stored_events[event.value]
    new[OPT_EVENTS] = events
    reminder = data.get("reminder")
    if isinstance(reminder, dict):
        new[OPT_REMINDER_PERSONS] = list(reminder.get(OPT_REMINDER_PERSONS) or [])
        profile = reminder.get(OPT_REMINDER_PROFILE)
        if profile:
            new[OPT_REMINDER_PROFILE] = profile
        else:
            new.pop(OPT_REMINDER_PROFILE, None)
        new[OPT_REMINDER_DELAY] = int(reminder.get(OPT_REMINDER_DELAY) or DEFAULT_REMINDER_DELAY)
    return Change(options=new)


def save_event_text(
    options: Mapping[str, Any], event: str, title: str, message: str, *, lang: str = "de"
) -> Change:
    """Eigener Titel und Text eines Ereignisses (leer = Text von Hauswacht).

    Steht im Feld noch genau die Vorlage von Hauswacht (``core.default_texts``), wird nichts
    gespeichert – es bleibt beim Text von Hauswacht. Prüft die Platzhalter wie der Dialog;
    Fehler: ``invalid_template`` mit der Meldung in ``details["message"]``.
    """
    from ..default_texts import is_default  # noqa: PLC0415
    from ..messages import TemplateError, check_template  # noqa: PLC0415

    try:
        kind = NotifyEvent(event)
    except ValueError:
        return Change(errors={"event": "unknown_event"})
    texts = {"title": str(title or "").strip(), "message": str(message or "").strip()}
    texts = {k: "" if is_default(kind, k, v, lang) else v for k, v in texts.items()}
    for key, text in texts.items():
        try:
            check_template(text, lang)
        except TemplateError as err:
            return Change(errors={key: "invalid_template"}, details={"message": str(err)})
    new = copy_options(options)
    events = {k: dict(v) for k, v in options.get(OPT_EVENTS, {}).items()}
    stored = events.get(kind.value, {})
    for key, text in texts.items():
        if text:
            stored[key] = text
        else:
            stored.pop(key, None)
    events[kind.value] = stored
    new[OPT_EVENTS] = events
    return Change(options=new, item_id=kind.value)
