"""Erinnerung "Alle weg, Anlage ist unscharf" mit Knopf "Jetzt scharf schalten".

Die sichere Alternative zum automatischen Scharfschalten bei Abwesenheit: Hauswacht schaltet
nichts selbst, sondern fragt per Push. Unbekannte Aufenthalte zählen nicht als weg. Pro
Abwesenheit kommt höchstens eine Erinnerung.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from homeassistant.core import CALLBACK_TYPE, Event, callback
from homeassistant.helpers.event import (
    EventStateChangedData,
    async_call_later,
    async_track_state_change_event,
)

from .const import OPT_REMINDER_DELAY, OPT_REMINDER_PERSONS, OPT_REMINDER_PROFILE
from .core.automation import all_away
from .core.profiles import profile_ids
from .core.state_machine import AlarmState
from .core.texts import tr

if TYPE_CHECKING:
    from .runtime import HauswachtRuntime

_LOGGER = logging.getLogger(__name__)

DEFAULT_REMINDER_DELAY = 15  # Minuten
MAX_REMINDER_DELAY = 240


class ReminderRunner:
    def __init__(self, runtime: HauswachtRuntime) -> None:
        self.runtime = runtime
        self.hass = runtime.hass
        options = runtime.options
        persons = options.get(OPT_REMINDER_PERSONS, [])
        self.persons: tuple[str, ...] = (
            tuple(p for p in persons if isinstance(p, str)) if isinstance(persons, list) else ()
        )
        profile = options.get(OPT_REMINDER_PROFILE)
        self.profile_id: str | None = (
            profile if isinstance(profile, str) and profile in profile_ids(options) else None
        )
        try:
            delay = int(options.get(OPT_REMINDER_DELAY, DEFAULT_REMINDER_DELAY))
        except (TypeError, ValueError):
            delay = DEFAULT_REMINDER_DELAY
        self.delay_minutes = min(max(delay, 1), MAX_REMINDER_DELAY)
        self._unsub: CALLBACK_TYPE | None = None
        self._timer: CALLBACK_TYPE | None = None
        self._sent = False

    @property
    def enabled(self) -> bool:
        return bool(self.persons and self.profile_id)

    @callback
    def start(self) -> None:
        if not self.enabled:
            return
        self._unsub = async_track_state_change_event(self.hass, list(self.persons), self._on_person)
        self._evaluate()

    @callback
    def stop(self) -> None:
        if self._unsub is not None:
            self._unsub()
            self._unsub = None
        self._cancel_timer()

    @callback
    def _cancel_timer(self) -> None:
        if self._timer is not None:
            self._timer()
            self._timer = None

    def _all_away(self) -> bool:
        return all_away((s.state if (s := self.hass.states.get(p)) else None) for p in self.persons)

    @callback
    def _on_person(self, _event: Event[EventStateChangedData]) -> None:
        self._evaluate()

    @callback
    def _evaluate(self) -> None:
        if not self._all_away():
            # Jemand ist (wieder) da oder unbekannt: neue Abwesenheit = neue Erinnerung
            self._sent = False
            self._cancel_timer()
            return
        if self._sent or self._timer is not None:
            return
        self._timer = async_call_later(self.hass, self.delay_minutes * 60, self._on_timer)

    @callback
    def _on_timer(self, _now: datetime) -> None:
        self._timer = None
        if self._sent or not self._all_away() or self.profile_id is None:
            return
        if self.runtime.ctx.state is not AlarmState.DISARMED:
            return
        self._sent = True
        _LOGGER.info("Erinnerung: alle weg, Anlage unscharf")
        self.runtime.send_arm_reminder(
            self.profile_id,
            tr(self.runtime.lang, "reminder", minutes=self.delay_minutes),
        )
