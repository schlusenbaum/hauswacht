"""Sprachausgabe: Lautsprecher, Wiederholung, Nachtruhe und je Ereignis Art, Text, Lautsprecher.

Dieselben Regeln wie im Dialog. Texte werden wie bei Push-Nachrichten geprüft (Platzhalter).
Unverändert gespeicherter Standardtext zählt als „Standard“ (es wird kein Text gespeichert).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..messages import TemplateError, check_template, default_speech
from ..notify_events import NotifyEvent
from ..speech import MAX_REPEAT, MIN_REPEAT, MODES
from . import Change, copy_options, failed

OPT_SPEECH = "speech"


def _hhmm(value: Any, fallback: str) -> str:
    text = str(value or "")[:5]
    parts = text.split(":")
    if len(parts) == 2 and all(p.isdigit() for p in parts):
        hour, minute = int(parts[0]), int(parts[1])
        if 0 <= hour < 24 and 0 <= minute < 60:
            return f"{hour:02d}:{minute:02d}"
    return fallback


def save_speech_settings(options: Mapping[str, Any], data: Mapping[str, Any]) -> Change:
    """``data``: speakers (Geräte), repeat (s, 0 = einmal), quiet_enabled, quiet_start,
    quiet_end."""
    try:
        repeat = int(data.get("repeat") or 0)
    except (TypeError, ValueError):
        return failed({"repeat": "invalid"})
    if repeat:
        repeat = max(MIN_REPEAT, min(MAX_REPEAT, repeat))
    raw = dict(options.get(OPT_SPEECH, {}) or {})
    raw["speakers"] = [str(s) for s in data.get("speakers") or []]
    raw["repeat"] = repeat
    raw["quiet"] = {
        "enabled": bool(data.get("quiet_enabled")),
        "start": _hhmm(data.get("quiet_start"), "22:00"),
        "end": _hhmm(data.get("quiet_end"), "07:00"),
    }
    new = copy_options(options)
    new[OPT_SPEECH] = raw
    return Change(options=new)


def save_speech_event(
    options: Mapping[str, Any], event: str, data: Mapping[str, Any], *, lang: str = "de"
) -> Change:
    """``data``: enabled, mode (announce/speak), speakers, in_quiet, text (leer = Standard)."""
    try:
        kind = NotifyEvent(event)
    except ValueError:
        return failed({"event": "unknown_event"})
    mode = str(data.get("mode") or MODES[0])
    if mode not in MODES:
        return failed({"mode": "invalid"})
    text = str(data.get("text") or "").strip()
    if text == default_speech(kind, german=lang == "de"):
        text = ""
    try:
        check_template(text, lang)
    except TemplateError as err:
        return failed({"text": "invalid_template"}, message=str(err))
    raw = dict(options.get(OPT_SPEECH, {}) or {})
    events = {k: dict(v) for k, v in (raw.get("events") or {}).items()}
    events[kind.value] = {
        "enabled": bool(data.get("enabled")),
        "mode": mode,
        "speakers": [str(s) for s in data.get("speakers") or []],
        "in_quiet": bool(data.get("in_quiet")),
        "text": text,
    }
    raw["events"] = events
    new = copy_options(options)
    new[OPT_SPEECH] = raw
    return Change(options=new, item_id=kind.value)
