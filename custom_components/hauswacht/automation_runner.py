"""Führt die Automatik der Profile aus: Uhrzeiten und Anwesenheit.

Die Regeln selbst stehen in core/automation.py. Hier werden nur die Auslöser von Home Assistant
abonniert und die Runtime aufgerufen.

Anwesenheit je Person = Personen-Entität plus die zusätzlichen Signale aus
"Anwesenheit & Heimkehr". "Unscharf mit Türbeleg" verlangt eine Rückkehr (vorher sicher weg,
jetzt zuhause) UND das Öffnen einer Eingangstür innerhalb des Zeitfensters – beides, während
das Profil scharf ist oder die Eingangsverzögerung läuft. Ein Alarm wird nie beendet.
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

from .const import EVENT_HAUSWACHT, OPT_HOMECOMING_SIGNALS, OPT_HOMECOMING_SSIDS
from .core.automation import (
    ARRIVAL_AUTO_ONLY,
    AutoConfig,
    all_away_values,
    anyone_home_values,
    combine,
    door_proof_ok,
    is_active_day,
    parse_automation,
    person_value,
)
from .core.homecoming import presence
from .core.notify_events import NotifyEvent
from .core.profiles import profile_ids
from .core.reactions import auto_armed_message, auto_disarmed_message
from .core.state_machine import AlarmState
from .core.texts import tr

if TYPE_CHECKING:
    from .runtime import HauswachtRuntime

_LOGGER = logging.getLogger(__name__)

REASON_TIME = "Uhrzeit"
REASON_AWAY = "alle weg"
REASON_ARRIVAL = "Rückkehr"
REASON_ARRIVAL_DOOR = "Rückkehr mit Türbeleg"
_PROOF_STATES = (AlarmState.ARMED, AlarmState.PENDING)


class AutomationRunner:
    def __init__(self, runtime: HauswachtRuntime) -> None:
        self.runtime = runtime
        self.hass = runtime.hass
        self.configs: dict[str, AutoConfig] = {}
        self.auto_armed_by: str | None = None
        self._unsubs: list[CALLBACK_TYPE] = []
        self._away_timers: dict[str, CALLBACK_TYPE] = {}
        self.signals: dict[str, tuple[str, ...]] = {}
        self.ssids: frozenset[str] = frozenset()
        self._home: dict[str, bool | None] = {}  # Person -> zuletzt bekannte Anwesenheit
        self._arrival_at: dict[str, float] = {}  # Profil -> letzte Rückkehr (scharf)
        self._door_at: dict[str, float] = {}  # Profil -> letzte Türöffnung (scharf)
        self._doors: frozenset[str] = frozenset()
        self._unsub_doors: CALLBACK_TYPE | None = None

    # --- Lebenszyklus --------------------------------------------------------

    @callback
    def start(self) -> None:
        options = self.runtime.options
        self.configs = {
            pid: cfg
            for pid in profile_ids(options)
            if (cfg := parse_automation(options, pid)).enabled
        }
        raw = options.get(OPT_HOMECOMING_SIGNALS, {})
        self.signals = {
            str(person): tuple(e for e in entities if isinstance(e, str))
            for person, entities in (raw.items() if isinstance(raw, dict) else [])
            if isinstance(entities, list)
        }
        self.ssids = frozenset(
            s.strip() for s in options.get(OPT_HOMECOMING_SSIDS, []) if isinstance(s, str) and s
        )
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
            watched = set(persons)
            for person in persons:
                watched.update(self.signals.get(person, ()))
            self._home = {p: self.person_home(p) for p in persons}
            self._unsubs.append(
                async_track_state_change_event(self.hass, sorted(watched), self._on_person)
            )
        self.refresh_doors()

    @callback
    def refresh_doors(self) -> None:
        """Eingangstüren für "Unscharf mit Türbeleg" (neu) abonnieren."""
        doors = (
            self.runtime.entry_doors()
            if any(cfg.door_proof for cfg in self.configs.values())
            else frozenset()
        )
        if doors == self._doors and (self._unsub_doors is not None or not doors):
            return
        self._doors = doors
        if self._unsub_doors is not None:
            self._unsub_doors()
            self._unsub_doors = None
        if doors:
            self._unsub_doors = async_track_state_change_event(
                self.hass, sorted(doors), self._on_door
            )

    @callback
    def stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        if self._unsub_doors is not None:
            self._unsub_doors()
            self._unsub_doors = None
        self._doors = frozenset()
        for cancel in self._away_timers.values():
            cancel()
        self._away_timers.clear()

    @callback
    def on_disarmed(self) -> None:
        self.auto_armed_by = None
        self._arrival_at.clear()
        self._door_at.clear()

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

    def _state(self, entity_id: str) -> str | None:
        state = self.hass.states.get(entity_id)
        return state.state if state else None

    def person_home(self, person: str) -> bool | None:
        """Person zuhause (True), sicher weg (False) oder unbekannt (None) – aus allen Signalen."""
        return combine(
            [
                person_value(self._state(person)),
                *(presence(self._state(s), self.ssids) for s in self.signals.get(person, ())),
            ]
        )

    @callback
    def _on_person(self, _event: Event[EventStateChangedData]) -> None:
        now = dt_util.utcnow().timestamp()
        arrived: list[str] = []
        for person in list(self._home):
            new = self.person_home(person)
            if self._home[person] is False and new is True:
                arrived.append(person)
            if new is not None:
                self._home[person] = new
        for pid, cfg in self.configs.items():
            if not cfg.away_persons:
                continue
            values = [self.person_home(p) for p in cfg.away_persons]
            if all_away_values(values):
                if pid not in self._away_timers:
                    self._away_timers[pid] = async_call_later(
                        self.hass, cfg.away_delay * 60, partial(self._away_elapsed, pid)
                    )
                    self._event("AutoArmScheduled", pid, minutes=cfg.away_delay)
                continue
            cancel = self._away_timers.pop(pid, None)
            if cancel is not None:
                cancel()
                self._event("AutoArmCancelled", pid)
            if cfg.arrival_mode == ARRIVAL_AUTO_ONLY and anyone_home_values(values):
                self.auto_disarm(pid, REASON_ARRIVAL, only_if_auto=True)
            elif (
                cfg.door_proof
                and any(p in cfg.away_persons for p in arrived)
                and self._proof_active(pid)
            ):
                self._arrival_at[pid] = now
                self._event("ArrivalNoted", pid, persons=arrived)
                self._check_door_proof(pid, cfg)

    @callback
    def _away_elapsed(self, profile_id: str, _now: datetime) -> None:
        self._away_timers.pop(profile_id, None)
        cfg = self.configs.get(profile_id)
        if cfg is not None and all_away_values(self.person_home(p) for p in cfg.away_persons):
            self.auto_arm(profile_id, REASON_AWAY)

    # --- Türbeleg -------------------------------------------------------------

    def _proof_active(self, profile_id: str) -> bool:
        ctx = self.runtime.ctx
        return (
            ctx.profile is not None
            and ctx.profile.profile_id == profile_id
            and ctx.state in _PROOF_STATES
        )

    @callback
    def _on_door(self, event: Event[EventStateChangedData]) -> None:
        old = event.data["old_state"]
        new = event.data["new_state"]
        if new is None or new.state != "on" or (old is not None and old.state != "off"):
            return
        # Erst die Alarmanlage reagieren lassen (Eingangsverzögerung oder Sofortalarm),
        # dann prüfen – so zählt eine Tür, die sofort Alarm auslöst, nie als Beleg.
        self.hass.loop.call_soon(self._door_opened, event.data["entity_id"])

    @callback
    def _door_opened(self, entity_id: str) -> None:
        now = dt_util.utcnow().timestamp()
        for pid, cfg in self.configs.items():
            if cfg.door_proof and self._proof_active(pid):
                self._door_at[pid] = now
                self._event("DoorNoted", pid, door=entity_id)
                self._check_door_proof(pid, cfg)

    @callback
    def _check_door_proof(self, profile_id: str, cfg: AutoConfig) -> None:
        if door_proof_ok(
            self._arrival_at.get(profile_id), self._door_at.get(profile_id), cfg.arrival_window
        ):
            self._arrival_at.pop(profile_id, None)
            self._door_at.pop(profile_id, None)
            self.auto_disarm(profile_id, REASON_ARRIVAL_DOOR, allow_entry=True)

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
            runtime.arm(profile_id, changed_by=tr(runtime.lang, "automation_actor"))
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
            *auto_armed_message(name, self._reason(reason), runtime.lang),
            values={"profil": name, "grund": reason},
            test_mode=runtime.ctx.test_mode,
        )

    @callback
    def auto_disarm(
        self,
        profile_id: str,
        reason: str,
        *,
        only_if_auto: bool = False,
        allow_entry: bool = False,
    ) -> None:
        runtime = self.runtime
        ctx = runtime.ctx
        if ctx.profile is None or ctx.profile.profile_id != profile_id:
            return
        # Ein laufender Alarm wird nie automatisch beendet. Die Eingangsverzögerung nur mit
        # Türbeleg (Rückkehr und Tür) – sonst auch sie nicht.
        allowed = (
            (AlarmState.ARMED, AlarmState.PENDING)
            if allow_entry
            else (AlarmState.ARMED, AlarmState.ARMING)
        )
        if ctx.state not in allowed:
            self._event("AutoDisarmSkipped", profile_id, reason=reason)
            return
        if only_if_auto and self.auto_armed_by != profile_id:
            return
        runtime.disarm_trusted(changed_by=tr(runtime.lang, "automation_actor"))
        self._event("AutoDisarmed", profile_id, reason=reason)
        runtime.notifier.notify(
            NotifyEvent.AUTOMATION,
            *auto_disarmed_message(
                runtime.profile_name(profile_id), self._reason(reason), runtime.lang
            ),
            values={"profil": runtime.profile_name(profile_id), "grund": reason},
            test_mode=ctx.test_mode,
        )

    def _reason(self, reason: str) -> str:
        """Grund für den Nachrichtentext in der Sprache von Home Assistant."""
        key = {
            REASON_TIME: "reason_time",
            REASON_AWAY: "reason_away",
            REASON_ARRIVAL: "reason_arrival",
            REASON_ARRIVAL_DOOR: "reason_arrival_door",
        }
        return tr(self.runtime.lang, key[reason]) if reason in key else reason

    @callback
    def _event(self, kind: str, profile_id: str, **data: Any) -> None:
        self.hass.bus.async_fire(EVENT_HAUSWACHT, {"type": kind, "profile_id": profile_id, **data})
