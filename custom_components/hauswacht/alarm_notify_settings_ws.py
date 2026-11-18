"""Einstellungsseite, Stufe 4: Alarmgeber und Benachrichtigungen (ADR 0011).

Liefert die Werte im Format des Einstellungsdialogs; gespeichert wird über dieselben
Funktionen (``save_sirens``, ``save_notify_settings``, ``save_event_text``).

Sicherheit: Die echte Sirenenansteuerung lässt sich nur mit ausdrücklicher Bestätigung
einschalten (``confirm_hardware``) – wie im Dialog. Ein Sirenentest ist hier nicht möglich.
"""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from .core.default_texts import default_message, default_title
from .core.messages import (
    ENGLISH_NAMES,
    EXAMPLE_VALUES_DE,
    EXAMPLE_VALUES_EN,
    default_speech,
    placeholder_names,
    render,
)
from .core.notify_events import NotifyEvent, enabled, event_targets
from .core.profiles import profile_info
from .core.siren_guard import is_fire_tone
from .core.siren_test import REMINDER_CHOICES
from .core.siren_test import parse_settings as parse_siren_test
from .core.speech import MAX_REPEAT, MIN_REPEAT, parse_speech
from .names import display_name
from .profile_settings_ws import _notify_choices, _speaker_choices

OPT_SIRENS = "sirens"
OPT_HARDWARE = "sirens_hardware_enabled"
OPT_ALLOW_SWITCH = "sirens_allow_switch"
OPT_TONES = "siren_tones"


def _siren_items(hass: HomeAssistant, main: Any, registered: list[str]) -> list[dict[str, Any]]:
    """Je eingetragener Sirene: Ton, bekannte Töne, ob Rauchmelder (dann nie Brandton)."""
    options = main.entry.options
    executor = getattr(main, "sirens", None)
    devices = executor.devices() if executor is not None else {}
    tones = dict(options.get(OPT_TONES, {}))
    fire_ok = set(options.get("siren_fire_tone_ok", []))
    items = []
    for siren in registered:
        caps = executor.capabilities(siren) if executor is not None else None
        device = devices.get(siren)
        known = sorted(caps.tones) if caps is not None and caps.tones else []
        items.append(
            {
                "id": siren,
                "name": display_name(hass, siren),
                "tone": tones.get(siren, ""),
                "tones": [{"tone": t, "fire": is_fire_tone(t)} for t in known],
                "tones_supported": bool(caps and caps.tones_supported),
                "smoke_detector": bool(device and device.fire_detector),
                "fire_ok": siren in fire_ok,
            }
        )
    return items


def _speech(hass: HomeAssistant, options: Any, lang: str) -> dict[str, Any]:
    """Sprachausgabe wie im Dialog: Lautsprecher, Wiederholung, Nachtruhe, je Ereignis."""
    config = parse_speech(options)
    return {
        "speakers": list(config.speakers),
        "repeat": config.repeat,
        "min_repeat": MIN_REPEAT,
        "max_repeat": MAX_REPEAT,
        "quiet_enabled": config.quiet_enabled,
        "quiet_start": config.quiet_start.strftime("%H:%M"),
        "quiet_end": config.quiet_end.strftime("%H:%M"),
        "events": [
            {
                "event": event.value,
                "enabled": setting.enabled,
                "mode": setting.mode,
                "speakers": list(setting.speakers),
                "in_quiet": setting.in_quiet,
                "text": setting.text,
                "default": default_speech(event, german=lang == "de"),
            }
            for event, setting in config.events.items()
        ],
        "speaker_choices": _speaker_choices(hass),
    }


def build_alarm_notify_settings(hass: HomeAssistant, main: Any) -> dict[str, Any]:
    options = main.entry.options
    lang = "de" if (hass.config.language or "").startswith("de") else "en"
    allow_switch = bool(options.get(OPT_ALLOW_SWITCH, False))
    registered = [s for s in options.get(OPT_SIRENS, []) if isinstance(s, str)]
    domains = ["siren", "switch"] if allow_switch else ["siren"]
    candidates = [
        {"id": s.entity_id, "name": display_name(hass, s.entity_id), "state": s.state}
        for s in hass.states.async_all(domains)
    ]
    push_disarm = bool(options.get("push_disarm", False))
    events = options.get("events", {})
    examples = EXAMPLE_VALUES_DE if lang == "de" else EXAMPLE_VALUES_EN
    return {
        "sirens": {
            "registered": registered,
            "hardware_enabled": bool(options.get(OPT_HARDWARE, False)),
            "allow_switch": allow_switch,
            "tones": dict(options.get(OPT_TONES, {})),
            "candidates": sorted(candidates, key=lambda c: str(c["name"]).casefold()),
            "items": _siren_items(hass, main, registered),
            "test": {
                "reminder_months": parse_siren_test(options).reminder_months,
                "prewarn": parse_siren_test(options).prewarn,
                "choices": list(REMINDER_CHOICES),
            },
            # Für „Sirene aus Schalter erstellen“: Schalter, die noch keine Sirene sind
            "switches": sorted(
                (
                    {"id": s.entity_id, "name": display_name(hass, s.entity_id)}
                    for s in hass.states.async_all("switch")
                    if s.entity_id not in registered
                ),
                key=lambda c: str(c["name"]).casefold(),
            ),
        },
        "notify": {
            "general": list(options.get("notify_system", [])),
            "test_mode": bool(options.get("notify_in_test_mode", False)),
            "push_disarm": push_disarm,
            "critical": bool(options.get("critical_alerts", True)),
            "duress": list(options.get("duress_notify", [])),
            "events": [
                {
                    "event": event.value,
                    "enabled": enabled(options, event, push_disarm=push_disarm),
                    "targets": list(event_targets(options, event)),
                    "title": events.get(event.value, {}).get("title", ""),
                    "message": events.get(event.value, {}).get("message", ""),
                    "preview": render(events[event.value]["message"], examples)
                    if events.get(event.value, {}).get("message")
                    else "",
                    # Vorlage zum Ändern: der Text von Hauswacht mit Platzhaltern
                    "default_title": default_title(event, lang),
                    "default_message": default_message(event, lang),
                }
                for event in NotifyEvent
            ],
            "reminder": {
                "persons": list(options.get("reminder_persons", [])),
                "profile": options.get("reminder_profile"),
                "delay": int(options.get("reminder_delay", 15)),
            },
            "placeholders": [f"{{{p}}}" for p in placeholder_names(lang)],
            "speech": _speech(hass, options, lang),
            # Beispielwerte für die Vorschau beim Tippen (beide Schreibweisen)
            "examples": {
                **dict(examples),
                **{en: examples.get(de, "") for en, de in ENGLISH_NAMES.items()},
            },
            "choices": {
                "notify": _notify_choices(hass),
                "persons": [
                    {"id": s.entity_id, "name": s.name} for s in hass.states.async_all("person")
                ],
                "profiles": [
                    {"id": pid, "name": profile_info(options, pid).name}
                    for pid in options.get("profiles", {})
                ],
            },
        },
    }
