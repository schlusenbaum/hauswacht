"""Führt die Automatik der Profile aus: Uhrzeiten und Anwesenheit.

Die Regeln selbst stehen in core/automation.py. Hier werden nur die Auslöser von Home Assistant
abonniert und die Runtime aufgerufen.
"""

from __future__ import annotations

import logging
from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING, Any

from homeassistant.core import CALLBACK_TYPE, Event, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import (
    EventStateChangedData,
    async_call_later,
    async_track_state_change_event,
    async_track_time_change,
)
from homeassistant.util import dt as dt_util

from .const import EVENT_HAUSWACHT
from .core.automation import AutoConfig, all_away, anyone_home, is_active_day, parse_automation
from .core.notify_events import NotifyEvent
from .core.profiles import profile_ids
from .core.reactions import auto_armed_message, auto_disarmed_message
from .core.state_machine import AlarmState

if TYPE_CHECKING:
    from .runtime import HauswachtRuntime

_LOGGER = logging.getLogger(__name__)

REASON_TIME = "Uhrzeit"
REASON_AWAY = "alle weg"
REASON_ARRIVAL = "Rückkehr"


class AutomationRunner:
    def __init__(self, runtime: HauswachtRuntime) -> None:
        self.runtime = runtime
        self.hass = runtime.hass
        self.configs: dict[str, AutoConfig] = {}
        self.auto_armed_by: str | None = None
        self._unsubs: list[CALLBACK_TYPE] = []
        self._away_timers: dict[str, CALLBACK_TYPE] = {}

    # --- Lebenszyklus --------------------------------------------------------

    @callback
    def start(self) -> None:
        options = self.runtime.entry.options
        self.configs = {
            pid: cfg
            for pid in profile_ids(options)
            if (cfg := parse_automation(options, pid)).enabled
        }
        persons: set[str] = set()
        for pid, cfg in self.configs.items():
            if cfg.arm_time:
                self._unsubs.append(
                    async_track_time_change(
                        self.hass,
                        partial(self._on_time, pid, "arm"),
                        hour=cfg.arm_time.hour,
                        minute=cfg.arm_time.minute,
                        second=cfg.arm_time.second,
                    )
                )
            if cfg.disarm_time:
                self._unsubs.append(
                    async_track_time_change(
                        self.hass,
                        partial(self._on_time, pid, "disarm"),
                        hour=cfg.disarm_time.hour,
                        minute=cfg.disarm_time.minute,
                        second=cfg.disarm_time.second,
                    )
                )
            persons.update(cfg.away_persons)
        if persons:
            self._unsubs.append(
                async_track_state_change_event(self.hass, sorted(persons), self._on_person)
            )

    @callback
    def stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        for cancel in self._away_timers.values():
            cancel()
        self._away_timers.clear()

    @callback
    def on_disarmed(self) -> None:
        self.auto_armed_by = None

    # --- Uhrzeiten -----------------------------------------------------------

    @callback
    def _on_time(self, profile_id: str, action: str, _now: datetime) -> None:
        cfg = self.configs.get(profile_id)
        if cfg is None or not is_active_day(cfg, dt_util.now().weekday()):
            return
        if action == "arm":
            self.auto_arm(profile_id, REASON_TIME)
        else:
            self.auto_disarm(profile_id, REASON_TIME)

    # --- Anwesenheit ----------------------------------------------------------

    def _person_states(self, cfg: AutoConfig) -> list[str | None]:
        states: list[str | None] = []
        for entity_id in cfg.away_persons:
            state = self.hass.states.get(entity_id)
            states.append(state.state if state else None)
        return states

    @callback
    def _on_person(self, _event: Event[EventStateChangedData]) -> None:
        for pid, cfg in self.configs.items():
            if not cfg.away_persons:
                continue
            states = self._person_states(cfg)
            if all_away(states):
                if pid not in self._away_timers:
                    self._away_timers[pid] = async_call_later(
                        self.hass, cfg.away_delay * 60, partial(self._away_elapsed, pid)
                    )
                    self._event("AutoArmScheduled", pid, minutes=cfg.away_delay)
            else:
                cancel = self._away_timers.pop(pid, None)
                if cancel is not None:
                    cancel()
                    self._event("AutoArmCancelled", pid)
                if cfg.disarm_on_arrival and anyone_home(states):
                    self.auto_disarm(pid, REASON_ARRIVAL, only_if_auto=True)

    @callback
    def _away_elapsed(self, profile_id: str, _now: datetime) -> None:
        self._away_timers.pop(profile_id, None)
        cfg = self.configs.get(profile_id)
        if cfg is not None and all_away(self._person_states(cfg)):
            self.auto_arm(profile_id, REASON_AWAY)

    # --- Aktionen -------------------------------------------------------------

    @callback
    def auto_arm(self, profile_id: str, reason: str) -> None:
        runtime = self.runtime
        name = runtime.profile_name(profile_id)
        if runtime.ctx.state is not AlarmState.DISARMED:
            # Nie über ein anderes (oder dasselbe) scharfe Profil hinweg umschalten
            self._event("AutoArmSkipped", profile_id, reason=reason)
            return
        try:
            runtime.arm(profile_id, changed_by="Automatik")
        except HomeAssistantError as err:
            details = str(err) or type(err).__name__
            _LOGGER.warning("Automatisches Scharfschalten von %s fehlgeschlagen: %s", name, details)
            # Die Nachricht "nicht scharf geschaltet" (mit Knöpfen) verschickt runtime.arm()
            self._event("AutoArmFailed", profile_id, reason=reason, details=details)
            return
        self.auto_armed_by = profile_id
        self._event("AutoArmed", profile_id, reason=reason)
        runtime.notifier.notify(
            NotifyEvent.AUTOMATION,
            *auto_armed_message(name, reason),
            test_mode=runtime.ctx.test_mode,
        )

    @callback
    def auto_disarm(self, profile_id: str, reason: str, *, only_if_auto: bool = False) -> None:
        runtime = self.runtime
        ctx = runtime.ctx
        if ctx.profile is None or ctx.profile.profile_id != profile_id:
            return
        # Ein laufender Alarm oder eine Eingangsverzögerung wird nie automatisch beendet.
        if ctx.state not in (AlarmState.ARMED, AlarmState.ARMING):
            self._event("AutoDisarmSkipped", profile_id, reason=reason)
            return
        if only_if_auto and self.auto_armed_by != profile_id:
            return
        runtime.disarm_trusted(changed_by="Automatik")
        self._event("AutoDisarmed", profile_id, reason=reason)
        runtime.notifier.notify(
            NotifyEvent.AUTOMATION,
            *auto_disarmed_message(runtime.profile_name(profile_id), reason),
            test_mode=ctx.test_mode,
        )

    @callback
    def _event(self, kind: str, profile_id: str, **data: Any) -> None:
        self.hass.bus.async_fire(EVENT_HAUSWACHT, {"type": kind, "profile_id": profile_id, **data})
