"""Sirenentest: eine Sirene kurz und leise prüfen – über den Siren Executor und den Guard.

Kein Sonderweg: Hardware-Freigabe, Testmodus (sperrt!), Brandsperre und Einbruchtöne gelten wie
bei einem echten Alarm. Zusätzlich: nur unscharf, höchstens 10 s, immer nur eine Sirene.
Während des Tests ist Scharfschalten gesperrt; Unscharf schalten bricht ihn ab.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_call_later, async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN, EVENT_HAUSWACHT
from .core.notify_events import NotifyEvent
from .core.siren_guard import ActivateRequest, GuardDecision, decide_activation
from .core.siren_test import (
    DEFAULT_TONE,
    DEFAULT_VOLUME,
    PREWARN_SECONDS,
    SirenTestRecord,
    clamp_seconds,
    due_sirens,
    dump_records,
    parse_records,
    parse_settings,
)
from .names import display_name

if TYPE_CHECKING:
    from .runtime import HauswachtRuntime

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
REMINDER_CHECK = timedelta(hours=1)
REMINDER_REPEAT = timedelta(days=7)


class SirenTester:
    """Gehört zum Hauptbereich; prüft immer alle Bereiche."""

    # In Tests kürzer
    prewarn_seconds: float = PREWARN_SECONDS

    def __init__(self, hass: HomeAssistant, runtime: HauswachtRuntime) -> None:
        self.hass = hass
        self.runtime = runtime
        self.settings = parse_settings(runtime.entry.options)
        self.records: dict[str, SirenTestRecord] = {}
        self.running: str | None = None
        self._reminded: datetime | None = None
        self._stop_timer: CALLBACK_TYPE | None = None
        self._unsub_reminder: CALLBACK_TYPE | None = None
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{runtime.entry.entry_id}.siren_tests"
        )

    # --- Start/Stopp ----------------------------------------------------------

    async def async_start(self) -> None:
        data = await self._store.async_load() or {}
        self.records = parse_records(data.get("records"))
        reminded = data.get("reminded")
        try:
            self._reminded = datetime.fromisoformat(reminded) if reminded else None
        except ValueError:
            self._reminded = None
        if self.settings.reminder_months:
            self._unsub_reminder = async_track_time_interval(
                self.hass, self._check_reminder, REMINDER_CHECK, name="hauswacht_siren_reminder"
            )

    @callback
    def async_stop(self) -> None:
        self.stop()
        if self._unsub_reminder is not None:
            self._unsub_reminder()
            self._unsub_reminder = None

    def _save(self) -> None:
        self._store.async_delay_save(
            lambda: {
                "records": dump_records(self.records),
                "reminded": self._reminded.isoformat() if self._reminded else None,
            },
            0,
        )

    # --- Prüfen ---------------------------------------------------------------

    @property
    def sirens(self) -> tuple[str, ...]:
        return self.runtime.sirens.sirens

    def blocker(self) -> str | None:
        """Warum gerade kein Test möglich ist (Übersetzungsschlüssel) oder None."""
        if self.running is not None:
            return "siren_test_running"
        if not self.runtime.all_disarmed:
            return "siren_test_armed"
        return None

    def preview(self, siren: str, tone: str, volume: str, seconds: int) -> GuardDecision:
        """Was der Guard bei einem Test entscheiden würde – sendet nichts."""
        executor = self.runtime.sirens
        return decide_activation(
            executor.guard_context(test_mode=self.runtime.ctx.test_mode),
            ActivateRequest(
                targets=(siren,), tone=tone, volume=volume, duration=clamp_seconds(seconds)
            ),
        )

    # --- Ausführen ------------------------------------------------------------

    async def async_run(  # noqa: PLR0913
        self,
        siren: str,
        *,
        tone: str = DEFAULT_TONE,
        volume: str = DEFAULT_VOLUME,
        seconds: int | float = 3,
        by: str | None = None,
        prewarn: bool = False,
    ) -> dict[str, Any]:
        """Eine Sirene testen. Liefert {"started": bool, "reason": str | None, ...}."""
        seconds = clamp_seconds(seconds)
        if siren not in self.sirens:
            return {"started": False, "reason": "unknown_device"}
        if (reason := self.blocker()) is not None:
            return {"started": False, "reason": reason}
        if prewarn:
            name = display_name(self.hass, siren)
            self.runtime.notifier.notify(
                NotifyEvent.SYSTEM,
                "Hauswacht: Sirenentest",
                f"Sirenentest {name} in {int(self.prewarn_seconds)} Sekunden "
                f"({seconds} s, Lautstärke {volume}).",
            )
            await asyncio.sleep(self.prewarn_seconds)
            if (reason := self.blocker()) is not None:
                return {"started": False, "reason": reason}
        decision = self.runtime.sirens.activate(
            (siren,), tone, volume, seconds, test_mode=self.runtime.ctx.test_mode
        )
        if not decision.commands:
            why = decision.blocked[0].reason.value if decision.blocked else "blocked"
            self._event(siren, "blocked", by=by, reason=why)
            return {"started": False, "reason": why}
        self.running = siren
        self._event(siren, "started", by=by, seconds=seconds, volume=volume)
        self._stop_timer = async_call_later(self.hass, seconds + 0.5, self._timeout)
        self.runtime._notify()
        return {"started": True, "reason": None, "seconds": seconds}

    @callback
    def _timeout(self, _now: datetime) -> None:
        self._stop_timer = None
        self.stop()

    @callback
    def stop(self) -> None:
        """Test beenden (Zeit abgelaufen, Unscharf schalten oder Entladen)."""
        if self._stop_timer is not None:
            self._stop_timer()
            self._stop_timer = None
        if self.running is None:
            return
        siren, self.running = self.running, None
        self.runtime.sirens.stop(test_mode=self.runtime.ctx.test_mode)
        self._event(siren, "stopped")
        self.runtime._notify()

    @callback
    def record(
        self,
        siren: str,
        heard: bool | None,
        *,
        by: str | None = None,
        seconds: int = 3,
        volume: str = DEFAULT_VOLUME,
    ) -> None:
        self.records[siren] = SirenTestRecord(
            at=dt_util.now(), heard=heard, by=by, seconds=clamp_seconds(seconds), volume=volume
        )
        self._event(siren, "result", by=by, heard=heard)
        self._save()
        self.runtime._notify()

    def _event(self, siren: str, step: str, **data: Any) -> None:
        self.hass.bus.async_fire(
            EVENT_HAUSWACHT,
            {"type": "SirenTest", "step": step, "siren": siren, **data},
        )
        _LOGGER.info("Sirenentest %s: %s %s", siren, step, data)

    # --- Erinnerung -----------------------------------------------------------

    def due(self) -> list[str]:
        return due_sirens(self.sirens, self.records, self.settings.reminder_months, dt_util.now())

    @callback
    def _check_reminder(self, _now: datetime | None = None) -> None:
        due = self.due()
        now = dt_util.now()
        if not due or (self._reminded and now - self._reminded < REMINDER_REPEAT):
            return
        self._reminded = now
        self._save()
        names = ", ".join(display_name(self.hass, s) for s in due)
        self.runtime.notifier.notify(
            NotifyEvent.SYSTEM,
            "Hauswacht: Sirenentest fällig",
            f"Bitte die Sirenen prüfen: {names}. Einstellungen → Alarmgeber – Sirenen → "
            "Sirenentest oder Testkarte.",
        )

    # --- Anzeige --------------------------------------------------------------

    def attributes(self) -> dict[str, Any]:
        return {
            "sirens": [
                {
                    "entity_id": siren,
                    "name": display_name(self.hass, siren),
                    "last_test": record.at.isoformat()
                    if (record := self.records.get(siren))
                    else None,
                    "heard": record.heard if record else None,
                }
                for siren in self.sirens
            ],
            "running": self.running,
            "due": self.due(),
            "reminder_months": self.settings.reminder_months,
            "prewarn": self.settings.prewarn,
            "blocked": self.blocker(),
        }

    def last_test(self) -> datetime | None:
        return max((r.at for r in self.records.values()), default=None)
