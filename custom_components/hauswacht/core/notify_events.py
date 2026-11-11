"""Benachrichtigungen pro Ereignis: an/aus, Empfänger, Wichtigkeit.

Rein und ohne Home Assistant. Gespeichert unter ``options["events"][<ereignis>]`` als
``{"enabled": bool, "targets": [notify-Dienste]}``. Fehlende Werte = Standard.

Empfänger:
- Alarm, "Tür geöffnet" und "Alarm beendet": zuerst die Empfänger des Profils (wie bisher),
  sonst die des Ereignisses, sonst die allgemeinen Empfänger.
- Alle anderen: die des Ereignisses, sonst die allgemeinen Empfänger.

Der Bedrohungsalarm ist kein einstellbares Ereignis: immer an, eigene Empfänger.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from enum import StrEnum
from typing import Any


class NotifyEvent(StrEnum):
    ALARM = "alarm"
    ENTRY = "entry"
    ARMED = "armed"
    DISARMED = "disarmed"
    ALARM_ENDED = "alarm_ended"
    ARM_FAILED = "arm_failed"
    AUTOMATION = "automation"
    FAULT = "fault"
    SYSTEM = "system"
    REMINDER = "reminder"
    ALWAYS_ACTIVE = "always_active"  # immer aktiver Melder im unscharfen Zustand
    RULE_NOTIFY = "rule_notify"  # Auslöseregel mit Ergebnis "nur Benachrichtigung"
    ARM_HINT = "arm_hint"  # beim Scharfschalten: offene Melder, die nur in Regeln vorkommen
    UNCONFIRMED = "unconfirmed"  # Einzelauslösung ohne Bestätigung, kein Alarm
    UNCONFIRMED_FREQUENT = "unconfirmed_frequent"  # Melder löst häufig allein aus


DEFAULT_ENABLED: Mapping[NotifyEvent, bool] = {
    NotifyEvent.ALARM: True,
    NotifyEvent.ENTRY: True,  # wirkt nur, wenn der Push-Knopf aktiviert ist (siehe enabled())
    NotifyEvent.ARMED: False,
    NotifyEvent.DISARMED: False,
    NotifyEvent.ALARM_ENDED: True,
    NotifyEvent.ARM_FAILED: True,
    NotifyEvent.AUTOMATION: True,
    NotifyEvent.FAULT: True,
    NotifyEvent.SYSTEM: True,
    NotifyEvent.REMINDER: True,
    NotifyEvent.ALWAYS_ACTIVE: True,
    NotifyEvent.RULE_NOTIFY: True,
    NotifyEvent.ARM_HINT: True,
    NotifyEvent.UNCONFIRMED: False,
    NotifyEvent.UNCONFIRMED_FREQUENT: False,
}

# Durchbrechen "Nicht stören" (wenn die Option dafür an ist)
CRITICAL: frozenset[NotifyEvent] = frozenset({NotifyEvent.ALARM, NotifyEvent.ALWAYS_ACTIVE})

PROFILE_FIRST: frozenset[NotifyEvent] = frozenset(
    {NotifyEvent.ALARM, NotifyEvent.ENTRY, NotifyEvent.ALARM_ENDED}
)


def _clean(targets: Any) -> tuple[str, ...]:
    if not isinstance(targets, Iterable) or isinstance(targets, str):
        return ()
    return tuple(dict.fromkeys(t for t in targets if isinstance(t, str) and t))


def _stored(options: Mapping[str, Any], event: NotifyEvent) -> Mapping[str, Any]:
    events = options.get("events", {})
    stored = events.get(event.value, {}) if isinstance(events, Mapping) else {}
    return stored if isinstance(stored, Mapping) else {}


def enabled(options: Mapping[str, Any], event: NotifyEvent, *, push_disarm: bool) -> bool:
    stored = _stored(options, event)
    if "enabled" in stored:
        return bool(stored["enabled"])
    if event is NotifyEvent.ENTRY:
        return push_disarm
    return DEFAULT_ENABLED[event]


def event_targets(options: Mapping[str, Any], event: NotifyEvent) -> tuple[str, ...]:
    return _clean(_stored(options, event).get("targets"))


def route(
    options: Mapping[str, Any],
    event: NotifyEvent,
    *,
    system_targets: Iterable[str],
    profile_targets: Iterable[str] = (),
    push_disarm: bool = False,
) -> tuple[str, ...]:
    """Empfänger für ein Ereignis (leer = nicht senden)."""
    if not enabled(options, event, push_disarm=push_disarm):
        return ()
    if event in PROFILE_FIRST and (profile := _clean(profile_targets)):
        return profile
    return event_targets(options, event) or _clean(system_targets)


# Zusatzdaten für die Home-Assistant-App
NORMAL_DATA: Mapping[str, Any] = {
    "priority": "high",
    "ttl": 0,
    "push": {"interruption-level": "time-sensitive"},
}
CRITICAL_DATA: Mapping[str, Any] = {
    "priority": "high",
    "ttl": 0,
    # Android: Alarm-Kanal (klingt auch bei "Nicht stören"); iOS: kritischer Hinweis
    "channel": "alarm_stream",
    "push": {
        "interruption-level": "critical",
        "sound": {"name": "default", "critical": 1, "volume": 1.0},
    },
}


def push_data(event: NotifyEvent | None, *, critical_allowed: bool) -> Mapping[str, Any]:
    """``event=None`` = Bedrohungsalarm (immer wichtig, wenn erlaubt)."""
    if critical_allowed and (event is None or event in CRITICAL):
        return CRITICAL_DATA
    return NORMAL_DATA
