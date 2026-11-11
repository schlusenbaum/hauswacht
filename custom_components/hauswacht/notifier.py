"""Benachrichtigungen über notify-Dienste (z. B. die Home-Assistant-App)."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from .const import (
    EVENT_HAUSWACHT,
    OPT_CRITICAL_ALERTS,
    OPT_NOTIFY_IN_TEST_MODE,
    OPT_NOTIFY_SYSTEM,
    OPT_PUSH_DISARM,
)
from .core.messages import default_speech, render
from .core.notify_events import NORMAL_DATA, NotifyEvent, push_data, route
from .core.speech import Candidate, is_speaker, parse_speech, pick_entity, speakers_for

_LOGGER = logging.getLogger(__name__)

NOTIFY_DOMAIN = "notify"

# Hohe Priorität für die Home-Assistant-App (Android: priority/ttl, iOS: interruption-level).
PUSH_DATA: Mapping[str, Any] = NORMAL_DATA


class Notifier:
    def __init__(
        self, hass: HomeAssistant, options: Mapping[str, Any], *, label: str | None = None
    ) -> None:
        self.hass = hass
        # Bereichsname im Titel (nur bei mehreren Bereichen gesetzt)
        self.label = label
        self.system_targets: tuple[str, ...] = tuple(
            dict.fromkeys(t for t in options.get(OPT_NOTIFY_SYSTEM, []) if isinstance(t, str))
        )
        self.in_test_mode = bool(options.get(OPT_NOTIFY_IN_TEST_MODE, False))
        self.options = options
        self.critical_allowed = bool(options.get(OPT_CRITICAL_ALERTS, True))

    @callback
    def send(  # noqa: PLR0913
        self,
        targets: Iterable[str],
        title: str,
        message: str,
        *,
        test_mode: bool = False,
        data: Mapping[str, Any] | None = None,
        base: Mapping[str, Any] = NORMAL_DATA,
    ) -> list[str]:
        """Verschickt eine Nachricht. Im Testmodus nur, wenn das ausdrücklich erlaubt ist."""
        targets = tuple(dict.fromkeys(targets))
        if not targets:
            return []
        if test_mode and not self.in_test_mode:
            self.hass.bus.async_fire(
                EVENT_HAUSWACHT,
                {"type": "NotificationSuppressed", "targets": list(targets), "title": title},
            )
            return []
        if self.label:
            title = f"{title} ({self.label})"
        if test_mode:
            title = f"[TEST] {title}"
        sent: list[str] = []
        for target in targets:
            if target.startswith(f"{NOTIFY_DOMAIN}."):
                # Benachrichtigungs-Entität (z. B. WhatsApp, Telegram): nur Titel und Text
                if self.hass.states.get(target) is None:
                    _LOGGER.warning("Benachrichtigungs-Entität %s existiert nicht", target)
                    continue
                self.hass.async_create_task(
                    self._call_entity(target, title, message), f"hauswacht_notify_{target}"
                )
                sent.append(target)
                continue
            if not self.hass.services.has_service(NOTIFY_DOMAIN, target):
                _LOGGER.warning("Benachrichtigungsdienst notify.%s existiert nicht", target)
                continue
            self.hass.async_create_task(
                self._call(target, title, message, {**base, **(data or {})}),
                f"hauswacht_notify_{target}",
            )
            sent.append(target)
        return sent

    @callback
    def send_system(self, title: str, message: str, *, test_mode: bool = False) -> list[str]:
        return self.notify(NotifyEvent.SYSTEM, title, message, test_mode=test_mode)

    def fill_values(self, message: str, values: Mapping[str, Any] | None) -> dict[str, str]:
        """Platzhalter-Werte; Bereich, Uhrzeit und Standardtext ergänzt Hauswacht selbst."""
        filled = {k: str(v) for k, v in (values or {}).items() if v is not None}
        filled.setdefault("bereich", self.label or "")
        filled.setdefault("uhrzeit", dt_util.now().strftime("%H:%M"))
        filled["text"] = message
        return filled

    def _custom_text(self, event: NotifyEvent, key: str) -> str:
        events = self.options.get("events", {})
        stored = events.get(event.value, {}) if isinstance(events, Mapping) else {}
        value = stored.get(key) if isinstance(stored, Mapping) else None
        return str(value).strip() if isinstance(value, str) else ""

    @callback
    def notify(  # noqa: PLR0913
        self,
        event: NotifyEvent,
        title: str,
        message: str,
        *,
        profile_targets: Iterable[str] = (),
        profile_speakers: Iterable[str] = (),
        values: Mapping[str, Any] | None = None,
        data: Mapping[str, Any] | None = None,
        test_mode: bool = False,
        speak: bool = True,
    ) -> list[str]:
        """Nachricht zu einem Ereignis – Push und Sprachausgabe laut Einstellungen.

        ``values`` füllt die Platzhalter eigener Texte (siehe ``core.messages``).
        """
        filled = self.fill_values(message, values)
        if speak:
            self.speak(event, filled, profile_speakers=profile_speakers, test_mode=test_mode)
        if custom := self._custom_text(event, "title"):
            title = render(custom, {**filled, "text": title}) or title
        if custom := self._custom_text(event, "message"):
            message = render(custom, filled) or message
        targets = route(
            self.options,
            event,
            system_targets=self.system_targets,
            profile_targets=profile_targets,
            push_disarm=bool(self.options.get(OPT_PUSH_DISARM, False)),
        )
        return self.send(
            targets,
            title,
            message,
            test_mode=test_mode,
            data=data,
            base=push_data(event, critical_allowed=self.critical_allowed),
        )

    @callback
    def speak(
        self,
        event: NotifyEvent,
        values: Mapping[str, str],
        *,
        profile_speakers: Iterable[str] = (),
        test_mode: bool = False,
    ) -> list[str]:
        """Sprachausgabe für ein Ereignis. Liefert die angesprochenen Entitäten."""
        config = parse_speech(self.options)
        devices = speakers_for(
            config, event, now=dt_util.now().time(), profile_speakers=profile_speakers
        )
        if not devices:
            return []
        setting = config.events[event]
        german = (self.hass.config.language or "de").startswith("de")
        text = render(setting.text or default_speech(event, german=german), values)
        if not setting.text and self.label:
            text = f"{self.label}: {text}"
        if not text:
            return []
        entities = self.speaker_entities(devices, setting.mode)
        if not entities:
            return []
        if test_mode and not self.in_test_mode:
            self.hass.bus.async_fire(
                EVENT_HAUSWACHT,
                {"type": "SpeechSuppressed", "event": event.value, "entities": entities},
            )
            return []
        if test_mode:
            text = "Test. " + text
        self.hass.async_create_task(self._speak(entities, text), f"hauswacht_speak_{event.value}")
        return entities

    def is_speaker_entity(self, entity_id: str) -> bool:
        """Ist das eine Lautsprecher-Entität (Durchsage/Sprechen)?"""
        if not entity_id.startswith(f"{NOTIFY_DOMAIN}."):
            return False
        entry = er.async_get(self.hass).async_get(entity_id)
        if entry is None:
            return is_speaker(Candidate(entity_id))
        return is_speaker(Candidate(entity_id, entry.unique_id, entry.translation_key))

    def speaker_entities(self, devices: Iterable[str], mode: str) -> list[str]:
        """Benachrichtigungs-Entität je Gerät, passend zur Art (Durchsage/Sprechen)."""
        registry = er.async_get(self.hass)
        found: list[str] = []
        for device_id in devices:
            candidates = [
                Candidate(e.entity_id, e.unique_id, e.translation_key)
                for e in er.async_entries_for_device(registry, device_id)
                if e.domain == NOTIFY_DOMAIN and not e.disabled_by
            ]
            entity_id = pick_entity(candidates, mode)
            if entity_id is None:
                _LOGGER.warning("Lautsprecher %s hat keine Benachrichtigungs-Entität", device_id)
                continue
            found.append(entity_id)
        return list(dict.fromkeys(found))

    async def _speak(self, entities: list[str], text: str) -> None:
        try:
            await self.hass.services.async_call(
                NOTIFY_DOMAIN,
                "send_message",
                {"entity_id": entities, "message": text},
                blocking=True,
            )
        except Exception:
            _LOGGER.exception("Sprachausgabe an %s fehlgeschlagen", ", ".join(entities))

    @callback
    def send_duress(
        self, targets: Iterable[str], title: str, message: str, *, test_mode: bool = False
    ) -> list[str]:
        """Bedrohungsalarm: eigene Empfänger, wichtig (durchbricht "Nicht stören")."""
        # Nie über Lautsprecher: der Notruf muss heimlich bleiben
        targets = [t for t in targets if not self.is_speaker_entity(t)]
        return self.send(
            targets,
            title,
            message,
            test_mode=test_mode,
            base=push_data(None, critical_allowed=self.critical_allowed),
        )

    @callback
    def clear(self, targets: Iterable[str], tag: str) -> None:
        """Entfernt eine frühere Benachrichtigung (Home-Assistant-App, per ``tag``)."""
        for target in dict.fromkeys(targets):
            if "." in target:
                continue  # Entitäten kennen kein Zurückziehen
            if self.hass.services.has_service(NOTIFY_DOMAIN, target):
                self.hass.async_create_task(
                    self._call(target, None, "clear_notification", {"tag": tag}),
                    f"hauswacht_clear_{target}",
                )

    async def _call_entity(self, entity_id: str, title: str, message: str) -> None:
        try:
            await self.hass.services.async_call(
                NOTIFY_DOMAIN,
                "send_message",
                {"entity_id": entity_id, "title": title, "message": message},
                blocking=True,
            )
        except Exception:
            _LOGGER.exception("Benachrichtigung an %s fehlgeschlagen", entity_id)

    async def _call(
        self, target: str, title: str | None, message: str, data: Mapping[str, Any]
    ) -> None:
        payload: dict[str, Any] = {"message": message, "data": dict(data)}
        if title is not None:
            payload["title"] = title
        try:
            await self.hass.services.async_call(NOTIFY_DOMAIN, target, payload, blocking=True)
        except Exception:
            _LOGGER.exception("Benachrichtigung an notify.%s fehlgeschlagen", target)
