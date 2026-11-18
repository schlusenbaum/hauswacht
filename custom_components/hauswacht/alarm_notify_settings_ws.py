"""Einstellungsseite, Stufe 4: Alarmgeber und Benachrichtigungen (ADR 0011).

Liefert die Werte im Format des Einstellungsdialogs; gespeichert wird über dieselben
Funktionen (``save_sirens``, ``save_notify_settings``, ``save_event_text``).

Sicherheit: Die echte Sirenenansteuerung lässt sich nur mit ausdrücklicher Bestätigung
einschalten (``confirm_hardware``) – wie im Dialog. Ein Sirenentest ist hier nicht möglich.
"""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from .core.messages import EXAMPLE_VALUES_DE, EXAMPLE_VALUES_EN, placeholder_names, render
from .core.notify_events import NotifyEvent, enabled, event_targets
from .core.profiles import profile_info
from .names import display_name
from .profile_settings_ws import _notify_choices

OPT_SIRENS = "sirens"
OPT_HARDWARE = "sirens_hardware_enabled"
OPT_ALLOW_SWITCH = "sirens_allow_switch"
OPT_TONES = "siren_tones"


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
                }
                for event in NotifyEvent
            ],
            "reminder": {
                "persons": list(options.get("reminder_persons", [])),
                "profile": options.get("reminder_profile"),
                "delay": int(options.get("reminder_delay", 15)),
            },
            "placeholders": [f"{{{p}}}" for p in placeholder_names(lang)],
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
