"""Benachrichtigungen über notify-Dienste (z. B. die Home-Assistant-App)."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from typing import Any

from homeassistant.core import HomeAssistant, callback

from .const import (
    EVENT_HAUSWACHT,
    OPT_CRITICAL_ALERTS,
    OPT_NOTIFY_IN_TEST_MODE,
    OPT_NOTIFY_SYSTEM,
    OPT_PUSH_DISARM,
)
from .core.notify_events import NORMAL_DATA, NotifyEvent, push_data, route

_LOGGER = logging.getLogger(__name__)

NOTIFY_DOMAIN = "notify"

# Hohe Priorität für die Home-Assistant-App (Android: priority/ttl, iOS: interruption-level).
PUSH_DATA: Mapping[str, Any] = NORMAL_DATA


class Notifier:
    def __init__(self, hass: HomeAssistant, options: Mapping[str, Any]) -> None:
        self.hass = hass
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
        if test_mode:
            title = f"[TEST] {title}"
        sent: list[str] = []
        for target in targets:
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

    @callback
    def notify(  # noqa: PLR0913
        self,
        event: NotifyEvent,
        title: str,
        message: str,
        *,
        profile_targets: Iterable[str] = (),
        data: Mapping[str, Any] | None = None,
        test_mode: bool = False,
    ) -> list[str]:
        """Nachricht zu einem Ereignis – an/aus und Empfänger laut Einstellungen."""
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
    def send_duress(
        self, targets: Iterable[str], title: str, message: str, *, test_mode: bool = False
    ) -> list[str]:
        """Bedrohungsalarm: eigene Empfänger, wichtig (durchbricht "Nicht stören")."""
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
            if self.hass.services.has_service(NOTIFY_DOMAIN, target):
                self.hass.async_create_task(
                    self._call(target, None, "clear_notification", {"tag": tag}),
                    f"hauswacht_clear_{target}",
                )

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
