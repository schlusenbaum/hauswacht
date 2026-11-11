"""Sprachausgabe über Lautsprecher (z. B. Echo-Geräte): Einstellungen, Nachtruhe, Auswahl.

Rein und ohne Home Assistant. Gespeichert unter ``options["speech"]``::

    speakers: [Geräte-IDs]            Standard-Lautsprecher für alle Ereignisse
    repeat: 30                        Alarm-Durchsage alle N Sekunden wiederholen (0 = einmal)
    quiet: {enabled, start, end}      Nachtruhe, z. B. 22:00–07:00
    events: {<ereignis>: {enabled, mode, speakers, in_quiet, text}}

Pro Alarmprofil kommen ``profile["speakers"]`` für Alarm, Eingangsverzögerung und
"Alarm beendet" hinzu (wie die Push-Empfänger des Profils).

Art: ``announce`` (Durchsage, mit Gong) oder ``speak`` (Sprechen). Hauswacht sucht am Gerät die
passende Benachrichtigungs-Entität; gibt es nur eine, wird sie genommen.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import time
from typing import Any

from .notify_events import PROFILE_FIRST, NotifyEvent

MODES = ("announce", "speak")
DEFAULT_MODE = "announce"
DEFAULT_REPEAT = 0
MIN_REPEAT, MAX_REPEAT = 10, 300
DEFAULT_QUIET_START = "22:00"
DEFAULT_QUIET_END = "07:00"

# Standardmäßig an (wirkt nur, wenn Lautsprecher gewählt sind)
DEFAULT_ENABLED: frozenset[NotifyEvent] = frozenset(
    {
        NotifyEvent.ALARM,
        NotifyEvent.ENTRY,
        NotifyEvent.ALWAYS_ACTIVE,
        NotifyEvent.ARM_FAILED,
    }
)
# Werden standardmäßig auch in der Nachtruhe angesagt
DEFAULT_IN_QUIET: frozenset[NotifyEvent] = frozenset(
    {NotifyEvent.ALARM, NotifyEvent.ENTRY, NotifyEvent.ALWAYS_ACTIVE}
)

# Suffixe/Wörter, an denen die Art einer Entität erkannt wird
_MODE_WORDS: Mapping[str, tuple[str, ...]] = {
    "announce": ("announce", "durchsage"),
    "speak": ("speak", "sprechen"),
}


@dataclass(frozen=True)
class EventSpeech:
    enabled: bool
    mode: str
    speakers: tuple[str, ...]  # leer = Standard-Lautsprecher
    in_quiet: bool
    text: str  # leer = Standardtext


@dataclass(frozen=True)
class SpeechConfig:
    speakers: tuple[str, ...]
    repeat: int
    quiet_enabled: bool
    quiet_start: time
    quiet_end: time
    events: Mapping[NotifyEvent, EventSpeech]


def _clean(values: Any) -> tuple[str, ...]:
    if not isinstance(values, Iterable) or isinstance(values, str):
        return ()
    return tuple(dict.fromkeys(v for v in values if isinstance(v, str) and v))


def _time(value: Any, default: str) -> time:
    for candidate in (value, default):
        try:
            hours, minutes = str(candidate).split(":")[:2]
            return time(int(hours), int(minutes))
        except (TypeError, ValueError):
            continue
    return time(0, 0)


def _repeat(value: Any) -> int:
    try:
        seconds = int(value)
    except (TypeError, ValueError):
        return DEFAULT_REPEAT
    if seconds <= 0:
        return 0
    return max(MIN_REPEAT, min(MAX_REPEAT, seconds))


def parse_speech(options: Mapping[str, Any]) -> SpeechConfig:
    raw = options.get("speech", {})
    raw = raw if isinstance(raw, Mapping) else {}
    quiet = raw.get("quiet", {})
    quiet = quiet if isinstance(quiet, Mapping) else {}
    stored_events = raw.get("events", {})
    stored_events = stored_events if isinstance(stored_events, Mapping) else {}
    events: dict[NotifyEvent, EventSpeech] = {}
    for event in NotifyEvent:
        data = stored_events.get(event.value, {})
        data = data if isinstance(data, Mapping) else {}
        mode = data.get("mode")
        events[event] = EventSpeech(
            enabled=bool(data.get("enabled", event in DEFAULT_ENABLED)),
            mode=mode if mode in MODES else DEFAULT_MODE,
            speakers=_clean(data.get("speakers")),
            in_quiet=bool(data.get("in_quiet", event in DEFAULT_IN_QUIET)),
            text=str(data.get("text") or "").strip(),
        )
    return SpeechConfig(
        speakers=_clean(raw.get("speakers")),
        repeat=_repeat(raw.get("repeat", DEFAULT_REPEAT)),
        quiet_enabled=bool(quiet.get("enabled", False)),
        quiet_start=_time(quiet.get("start"), DEFAULT_QUIET_START),
        quiet_end=_time(quiet.get("end"), DEFAULT_QUIET_END),
        events=events,
    )


def in_quiet_hours(config: SpeechConfig, now: time) -> bool:
    if not config.quiet_enabled or config.quiet_start == config.quiet_end:
        return False
    start, end = config.quiet_start, config.quiet_end
    if start < end:
        return start <= now < end
    return now >= start or now < end  # über Mitternacht


def speakers_for(
    config: SpeechConfig,
    event: NotifyEvent,
    *,
    now: time,
    profile_speakers: Iterable[str] = (),
) -> tuple[str, ...]:
    """Lautsprecher (Geräte) für ein Ereignis – leer = nicht ansagen."""
    setting = config.events[event]
    if not setting.enabled:
        return ()
    if in_quiet_hours(config, now) and not setting.in_quiet:
        return ()
    if event in PROFILE_FIRST and (profile := _clean(profile_speakers)):
        return profile
    return setting.speakers or config.speakers


@dataclass(frozen=True)
class Candidate:
    """Benachrichtigungs-Entität an einem Gerät."""

    entity_id: str
    unique_id: str = ""
    translation_key: str | None = None


def _mode_of(candidate: Candidate) -> str | None:
    if candidate.translation_key in MODES:
        return candidate.translation_key
    for mode, words in _MODE_WORDS.items():
        text = f"{candidate.unique_id} {candidate.entity_id}".casefold()
        if any(word in text for word in words):
            return mode
    return None


def pick_entity(candidates: Sequence[Candidate], mode: str) -> str | None:
    """Die Entität für die gewünschte Art; sonst die einzige bzw. erste."""
    if not candidates:
        return None
    for candidate in candidates:
        if _mode_of(candidate) == mode:
            return candidate.entity_id
    return sorted(candidates, key=lambda c: c.entity_id)[0].entity_id


def profile_speakers(options: Mapping[str, Any], profile_id: str | None) -> tuple[str, ...]:
    """Zusätzliche Lautsprecher eines Alarmprofils (für Alarm, Eingang, Alarm beendet)."""
    if profile_id is None:
        return ()
    profiles = options.get("profiles", {})
    profile = profiles.get(profile_id, {}) if isinstance(profiles, Mapping) else {}
    return _clean(profile.get("speakers")) if isinstance(profile, Mapping) else ()
