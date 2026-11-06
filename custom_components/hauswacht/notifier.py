"""Benachrichtigungen über notify-Dienste (z. B. die Home-Assistant-App)."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from typing import Any

from homeassistant.core import HomeAssistant, callback

from .const import EVENT_HAUSWACHT, OPT_NOTIFY_IN_TEST_MODE, OPT_NOTIFY_SYSTEM

_LOGGER = logging.getLogger(__name__)

NOTIFY_DOMAIN = "notify"

# Hohe Priorität für die Home-Assistant-App (Android: priority/ttl, iOS: interruption-level).
PUSH_DATA: dict[str, Any] = {
    "priority": "high",
    "ttl": 0,
    "push": {"interruption-level": "time-sensitive"},
}


class Notifier:
    def __init__(self, hass: HomeAssistant, options: Mapping[str, Any]) -> None:
        self.hass = hass
        self.system_targets: tuple[str, ...] = tuple(
            dict.fromkeys(t for t in options.get(OPT_NOTIFY_SYSTEM, []) if isinstance(t, str))
        )
        self.in_test_mode = bool(options.get(OPT_NOTIFY_IN_TEST_MODE, False))

    @callback
    def send(
        self, targets: Iterable[str], title: str, message: str, *, test_mode: bool = False
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
                self._call(target, title, message), f"hauswacht_notify_{target}"
            )
            sent.append(target)
        return sent

    @callback
    def send_system(self, title: str, message: str, *, test_mode: bool = False) -> list[str]:
        return self.send(self.system_targets, title, message, test_mode=test_mode)

    async def _call(self, target: str, title: str, message: str) -> None:
        try:
            await self.hass.services.async_call(
                NOTIFY_DOMAIN,
                target,
                {"title": title, "message": message, "data": PUSH_DATA},
                blocking=True,
            )
        except Exception:
            _LOGGER.exception("Benachrichtigung an notify.%s fehlgeschlagen", target)
