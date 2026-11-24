"""Führt die Automatik der Profile aus: Uhrzeiten und Anwesenheit.

Die Regeln selbst stehen in core/automation.py. Hier werden nur die Auslöser von Home Assistant
abonniert und die Runtime aufgerufen.

Anwesenheit je Person = Personen-Entität plus die zusätzlichen Signale aus
"Anwesenheit & Heimkehr". „Bei Rückkehr“ (ADR 0015) je Profil mit eigener Personenliste:
unscharf (nur wenn automatisch scharf, mit Türbeleg oder immer) oder reinlassen (Durchgang).
Türbeleg und Reinlassen verlangen eine Rückkehr (vorher sicher weg, jetzt zuhause) UND das
Öffnen einer Eingangstür innerhalb des Zeitfensters – beides, während das Profil scharf ist oder
die Eingangsverzögerung läuft. Ein Alarm wird nie beendet.
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

from .const import OPT_HOMECOMING_SIGNALS, OPT_HOMECOMING_SSIDS
from .core.automation import (
    AutoConfig,
    all_away_values,
    combine,
    disarm_due,
    door_proof_ok,
    is_active_day,
    parse_automation,
    person_value,
    schedule_action,
)
from .core.away_proof import (
    SIM_APPROACHING,
    SIM_AWAY,
    SIM_AWAY_NO_PROOF,
    SIM_HOME,
    SIM_REAL,
    AwayTracker,
    parse_proof_settings,
)
from .core.homecoming import DIRECTION_HINT as DIRECTION_APPROACH
from .core.homecoming import direction_hint, presence
from .core.notify_events import NotifyEvent
from .core.profiles import profile_ids
from .core.returning import (
    RETURN_ALWAYS,
    RETURN_AUTO_ONLY,
    ReturnConfig,
    parse_return,
)
from .core.state_machine import AlarmState
from .core.texts import tr
from .presence_proof import locatable, person_fixes

if TYPE_CHECKING:
    from .runtime import HauswachtRuntime

_LOGGER = logging.getLogger(__name__)

REASON_TIME = "Uhrzeit"
REASON_AWAY = "alle weg"
REASON_ARRIVAL = "Rückkehr"
REASON_ARRIVAL_DOOR = "Rückkehr mit Türbeleg"
REASON_ARRIVAL_ALWAYS = "Rückkehr"
REASON_RESTART = "Neustart"
REASON_SCHEDULE = "Zeitplan"
_PROOF_STATES = (AlarmState.ARMED, AlarmState.PENDING)
# Handy-Reinlassen (ADR 0013): so lange muss die Person vorher sicher weg gewesen sein
MIN_AWAY_FOR_PASSAGE = 5 * 60


class AutomationRunner:
    def __init__(self, runtime: HauswachtRuntime) -> None:
        self.runtime = runtime
        self.hass = runtime.hass
        self.configs: dict[str, AutoConfig] = {}
        self.auto_armed_by: str | None = None
        self._unsubs: list[CALLBACK_TYPE] = []
        self._away_timers: dict[str, CALLBACK_TYPE] = {}
        self._away_due: dict[str, float] = {}  # Profil -> wann „alle weg“ scharf schaltet
        self._shown: tuple[Any, ...] = ()  # zuletzt angezeigter Stand (Anwesenheit)
        self.signals: dict[str, tuple[str, ...]] = {}
        self.ssids: frozenset[str] = frozenset()
        self._home: dict[str, bool | None] = {}  # Person -> zuletzt bekannte Anwesenheit
        self._arrival_at: dict[str, float] = {}  # Profil -> letzte Rückkehr (scharf)
        self._door_at: dict[str, float] = {}  # Profil -> letzte Türöffnung (scharf)
        self._doors: frozenset[str] = frozenset()
        self._unsub_doors: CALLBACK_TYPE | None = None
        # „Bei Rückkehr“ je Profil (ADR 0015), nur Profile mit Auswahl und Personen
        self.returns: dict[str, ReturnConfig] = {}
        self._away_since: dict[str, float] = {}  # Person -> seit wann sicher weg
        self._phone_arrival: dict[str, tuple[float, str]] = {}  # Profil -> (Zeit, Person)
        self._phone_door_at: dict[str, float] = {}  # Profil -> letzte Türöffnung (scharf)
        # „weg“ nur mit Beleg (ADR 0015): Türöffnungen und belegte Abwesenheit je Person
        self.proof = AwayTracker()
        self._owners: dict[str, tuple[str, ...]] = {}  # Signal -> Personen (Tür + Signal)
        self._approach_at: dict[str, float] = {}  # Person -> letzte Annäherung (Richtung)

    # --- Lebenszyklus --------------------------------------------------------

    @callback
    def start(self) -> None:
        options = self.runtime.options
        self.proof.settings = parse_proof_settings(options)
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
        self.returns = {
            pid: back for pid in profile_ids(options) if (back := parse_return(options, pid)).active
        }
        for back in self.returns.values():
            persons.update(back.persons)
        schedules = sorted({cfg.schedule for cfg in self.configs.values() if cfg.schedule})
        if schedules:
            self._unsubs.append(
                async_track_state_change_event(self.hass, schedules, self._on_schedule)
            )
        if persons:
            owners: dict[str, list[str]] = {}
            for person in persons:
                sources = [person, *self.signals.get(person, ())]
                state = self.hass.states.get(person)
                trackers = state.attributes.get("device_trackers", []) if state else []
                if isinstance(trackers, list):  # Ortungen der Person (Frische, Beleg)
                    sources.extend(t for t in trackers if isinstance(t, str))
                for source in dict.fromkeys(sources):
                    owners.setdefault(source, []).append(person)
            self._owners = {k: tuple(v) for k, v in owners.items()}
            watched = set(self._owners)
            self._home = {p: self.person_home(p) for p in persons}
            # Wer beim Start schon weg ist, zählt ab jetzt als weg
            started = dt_util.utcnow().timestamp()
            self._away_since = {p: started for p, home in self._home.items() if home is False}
            self._unsubs.append(
                async_track_state_change_event(self.hass, sorted(watched), self._on_person)
            )
        self.refresh_doors()

    @callback
    def refresh_doors(self) -> None:
        """Eingangstüren abonnieren: Beleg für „weg“ und „Bei Rückkehr“ mit Tür."""
        doors = (
            self.runtime.entry_doors()
            if self._home or any(back.with_door for back in self.returns.values())
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
        self._away_due.clear()
        for cancel in self._away_timers.values():
            cancel()
        self._away_timers.clear()

    @callback
    def on_disarmed(self) -> None:
        self.auto_armed_by = None
        self._arrival_at.clear()
        self._door_at.clear()
        self._phone_arrival.clear()
        self._phone_door_at.clear()

    # --- Uhrzeiten -----------------------------------------------------------

    @callback
    def _on_time(self, profile_id: str, action: str, _now: datetime) -> None:
        cfg = self.configs.get(profile_id)
        if cfg is None:
            return
        today = dt_util.now().weekday()
        if action == "arm":
            if is_active_day(cfg, today):
                self.auto_arm(profile_id, REASON_TIME)
        elif disarm_due(cfg, today):
            self.auto_disarm(profile_id, REASON_TIME)

    # --- Zeitplan (Helfer) ------------------------------------------------------

    @callback
    def _on_schedule(self, event: Event[EventStateChangedData]) -> None:
        entity_id = event.data["entity_id"]
        old, new = event.data["old_state"], event.data["new_state"]
        next_event = new.attributes.get("next_event") if new else None
        seconds = None
        if isinstance(next_event, datetime):
            seconds = (next_event - dt_util.now()).total_seconds()
        elif isinstance(next_event, str) and (parsed := dt_util.parse_datetime(next_event)):
            seconds = (parsed - dt_util.now()).total_seconds()
        action = schedule_action(old.state if old else None, new.state if new else None, seconds)
        if action is None:
            return
        for profile_id, cfg in self.configs.items():
            if cfg.schedule != entity_id:
                continue
            if action == "arm":
                self.auto_arm(profile_id, REASON_SCHEDULE)
            else:
                self.auto_disarm(profile_id, REASON_SCHEDULE)

    # --- Anwesenheit ----------------------------------------------------------

    def _state(self, entity_id: str) -> str | None:
        state = self.hass.states.get(entity_id)
        return state.state if state else None

    def person_home(self, person: str) -> bool | None:
        """Person zuhause (True), sicher weg (False) oder unbekannt (None) – aus allen Signalen.

        Richtung "nähert sich"/"steht" zählt nicht (siehe ``direction_hint``). „Weg“ gilt nur mit
        Beleg – Tür und Ortung außerhalb oder eine frische, genaue Ortung außerhalb (ADR 0015);
        sonst ist die Person unbekannt. Im Testmodus kann die Anwesenheit simuliert sein
        (ADR 0016).
        """
        return self._assess(person)[0]

    def _assess(self, person: str) -> tuple[bool | None, dict[str, Any]]:
        """Bewertung einer Person mit Grund (für die Anzeige in Testkarte und Einstellungen)."""
        now = dt_util.utcnow().timestamp()
        simulated = self.runtime.presence_simulated(person)
        if simulated is not None:
            if simulated == SIM_HOME:
                return self.proof.judge(person, True, [], now), {"kind": "simulated"}
            if simulated == SIM_AWAY_NO_PROOF:
                return self.proof.judge(person, None, [], now), {"kind": "simulated"}
            if not self.proof.proven(person):
                self.proof.mark_proven(person, "simulated", now)
            return False, {"kind": "simulated"}
        signals = self.signals.get(person, ())
        values = {person: person_value(self._state(person))}
        for signal in signals:
            state = self._state(signal)
            if not direction_hint(state):
                values[signal] = presence(state, self.ssids)
        combined = combine(list(values.values()))
        fixes = (
            person_fixes(self.hass, person, signals, self.proof.settings.accuracy)
            if combined is False
            else []
        )
        result = self.proof.judge(person, combined, fixes, now)
        if result is True:
            return True, {"kind": "home", "by": [e for e, v in values.items() if v is True]}
        if result is False:
            kind = self.proof.kind(person)
            return False, {
                "kind": "away",
                "proof": kind[0] if kind else None,
                "at": kind[1] if kind else None,
            }
        if combined is False:
            return None, {"kind": "no_proof"}
        return None, {"kind": "unclear", "by": [e for e, v in values.items() if v is None]}

    def unlocatable(self) -> list[str]:
        """Personen der Automatik ohne Ortung und ohne „Tür + Signal“ – nie weg (Hinweis)."""
        return [
            p
            for p in self._home
            if p not in self.proof.settings.weak
            and not locatable(self.hass, p, self.signals.get(p, ()))
        ]

    # --- Anwesenheit testen und anzeigen (ADR 0016) ---------------------------

    @property
    def presence_persons(self) -> list[str]:
        """Personen aus den Profil-Automatiken dieses Bereichs."""
        return list(self._home)

    @callback
    def presence_simulated_changed(self, person: str, value: str) -> None:
        """Simulation hat sich geändert (nur Testmodus): neu bewerten."""
        if person not in self._home:
            return
        now = dt_util.utcnow().timestamp()
        if value in (SIM_REAL, SIM_HOME):
            self.proof.forget(person)  # simulierter Beleg zählt nicht weiter
        if value == SIM_APPROACHING:
            self._approach_at[person] = now
        elif value != SIM_HOME:
            # Weg/Echt: eine (simulierte) Annäherung von vorhin gilt nicht mehr.
            # Bei „Zuhause“ bleibt sie, damit „Bei Rückkehr“ sie wie im Echtbetrieb sieht.
            self._approach_at.pop(person, None)
        self._evaluate(now)
        if value in (SIM_AWAY, SIM_APPROACHING):
            # Im Test gilt eine simulierte Abwesenheit sofort als lang genug (5 Minuten)
            self._away_since[person] = now - MIN_AWAY_FOR_PASSAGE

    @callback
    def skip_wait(self) -> list[str]:
        """„Wartezeit überspringen“ (Testmodus): laufende „alle weg“-Wartezeiten jetzt beenden."""
        done = list(self._away_timers)
        for pid in done:
            cancel = self._away_timers.get(pid)
            if cancel is not None:
                cancel()
            self._away_elapsed(pid, dt_util.utcnow())
        return done

    def presence_report(self) -> dict[str, Any]:
        """Je Person Zustand und Grund, je Profil was „alle weg“ gerade macht."""
        now = dt_util.utcnow().timestamp()
        persons: dict[str, dict[str, Any]] = {}
        for person in self._home:
            value, reason = self._assess(person)
            approach = self._approach_at.get(person)
            if value is True:
                approach = None  # zuhause angekommen: „nähert sich“ ist vorbei
            persons[person] = {
                "state": "home" if value is True else "away" if value is False else "unknown",
                "reason": reason,
                "simulated": self.runtime.presence_simulated(person),
                "approach_at": approach if approach and now - approach <= 3600 else None,
            }
        profiles = []
        for pid, cfg in self.configs.items():
            if not cfg.away_persons:
                continue
            waiting = [p for p in cfg.away_persons if persons.get(p, {}).get("state") != "away"]
            profiles.append({"profile": pid, "waiting": waiting, "due": self._away_due.get(pid)})
        return {"persons": persons, "profiles": profiles}

    def _signal_value(self, entity_id: str, state: str | None) -> bool | None:
        if entity_id.startswith("person."):
            return person_value(state)
        return None if direction_hint(state) else presence(state, self.ssids)

    @callback
    def _on_person(self, event: Event[EventStateChangedData]) -> None:
        now = dt_util.utcnow().timestamp()
        # „Tür + Signal“: ein Signal wechselt von „da“ auf „weg“ (Nachtrag 0.61, ADR 0015)
        entity_id = event.data["entity_id"]
        old, new_state = event.data["old_state"], event.data["new_state"]
        if (
            old is not None
            and new_state is not None
            and self._signal_value(entity_id, old.state) is True
            and self._signal_value(entity_id, new_state.state) is False
        ):
            for owner in self._owners.get(entity_id, ()):
                self.proof.note_signal_left(owner, now)
        # Annäherung (Richtung „nähert sich“) – verlängert die Eingangsverzögerung (ADR 0015)
        if new_state is not None and new_state.state in DIRECTION_APPROACH:
            for owner in self._owners.get(entity_id, ()):
                self._approach_at[owner] = now
        self._evaluate(now)

    @callback
    def _evaluate(self, now: float) -> None:
        """Anwesenheit neu bewerten: Rückkehr erkennen, „alle weg“ planen oder abbrechen."""
        arrived: list[str] = []
        long_away: list[str] = []  # Heimkehr nach mindestens 5 Minuten sicher weg
        current: dict[str, bool | None] = {}
        for person in list(self._home):
            new = self.person_home(person)
            current[person] = new
            if self._home[person] is False and new is True:
                arrived.append(person)
                if now - self._away_since.get(person, now) >= MIN_AWAY_FOR_PASSAGE:
                    long_away.append(person)
            if new is False and self._home[person] is not False:
                self._away_since[person] = now
            if new is not None:
                self._home[person] = new
        self._returned(now, arrived, long_away)
        for pid, cfg in self.configs.items():
            if not cfg.away_persons:
                continue
            values = [self.person_home(p) for p in cfg.away_persons]
            if all_away_values(values):
                if pid not in self._away_timers:
                    self._away_timers[pid] = async_call_later(
                        self.hass, cfg.away_delay * 60, partial(self._away_elapsed, pid)
                    )
                    self._away_due[pid] = now + cfg.away_delay * 60
                    self._event("AutoArmScheduled", pid, minutes=cfg.away_delay)
                continue
            self._away_due.pop(pid, None)
            cancel = self._away_timers.pop(pid, None)
            if cancel is not None:
                cancel()
                self._event("AutoArmCancelled", pid)
        # Anzeige (Testkarte, Einstellungsseite) nur bei einer Änderung auffrischen
        signature = (tuple(sorted(current.items())), tuple(sorted(self._away_due)))
        if signature != self._shown:
            self._shown = signature
            self.runtime._notify()
            # Die Testkarte liest den Stand am Hauptbereich – auch ihn auffrischen
            main = getattr(self.runtime, "main", self.runtime)
            if main is not self.runtime:
                main._notify()

    @callback
    def _returned(self, now: float, arrived: list[str], long_away: list[str]) -> None:
        """„Bei Rückkehr“: jemand aus der Liste eines Profils ist heimgekommen."""
        for pid, back in self.returns.items():
            coming = [p for p in arrived if p in back.persons]
            if not coming:
                continue
            if back.mode == RETURN_AUTO_ONLY:
                self.auto_disarm(pid, REASON_ARRIVAL, only_if_auto=True)
            elif back.mode == RETURN_ALWAYS:
                # Ohne Tür – nur nach echter Abwesenheit (mindestens 5 Minuten sicher weg)
                if any(p in long_away for p in coming):
                    self.auto_disarm(pid, REASON_ARRIVAL_ALWAYS, allow_entry=True)
            elif back.door_proof and self._proof_active(pid):
                self._arrival_at[pid] = now
                self._event("ArrivalNoted", pid, persons=coming)
                self._check_door_proof(pid, back)
            elif back.lets_in and self._proof_active(pid):
                far = [p for p in coming if p in long_away]
                if far:
                    self._phone_arrival[pid] = (now, far[0])
                    self._event("PhoneArrivalNoted", pid, persons=far)
                    self._check_phone(pid, back)

    @callback
    def _away_elapsed(self, profile_id: str, _now: datetime) -> None:
        self._away_timers.pop(profile_id, None)
        self._away_due.pop(profile_id, None)
        cfg = self.configs.get(profile_id)
        if cfg is not None and all_away_values(self.person_home(p) for p in cfg.away_persons):
            self.auto_arm(profile_id, REASON_AWAY)

    # --- Annäherung verlängert die Eingangsverzögerung (ADR 0015) -----------------

    def entry_extension(self, profile_id: str | None, now: float) -> tuple[int, list[str]]:
        """Eingangsverzögerung nach Annäherung (Sekunden) und wer sich genähert hat.

        ``(0, [])``, wenn nichts verlängert wird: Profil ohne „Bei Rückkehr“ mit Tür, ohne
        eingestellte Verlängerung, oder niemand aus der Liste hat sich in der Gültigkeit genähert.
        """
        back = self.returns.get(profile_id or "")
        if back is None or not back.extends:
            return 0, []
        valid = back.approach_valid * 60
        near = [
            p
            for p in back.persons
            if (at := self._approach_at.get(p)) is not None and now - at <= valid
        ]
        return (back.approach_delay, near) if near else (0, [])

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
        self.proof.note_door(dt_util.utcnow().timestamp())  # Beleg für „weg“
        # Erst die Alarmanlage reagieren lassen (Eingangsverzögerung oder Sofortalarm),
        # dann prüfen – so zählt eine Tür, die sofort Alarm auslöst, nie als Beleg.
        self.hass.loop.call_soon(self._door_opened, event.data["entity_id"])

    @callback
    def _door_opened(self, entity_id: str) -> None:
        now = dt_util.utcnow().timestamp()
        for pid, back in self.returns.items():
            if not self._proof_active(pid):
                continue
            if back.lets_in:
                self._phone_door_at[pid] = now
                self._check_phone(pid, back)
            elif back.door_proof:
                self._door_at[pid] = now
                self._event("DoorNoted", pid, door=entity_id)
                self._check_door_proof(pid, back)

    @callback
    def _check_phone(self, profile_id: str, back: ReturnConfig) -> None:
        """Handy-Reinlassen: Heimkehr und Türöffnung passen zusammen -> reinlassen.

        Das Handy darf sich bis zu ``window`` Minuten vor dem Öffnen melden oder danach,
        solange die Eingangsverzögerung läuft. Eine Heimkehr lässt einmal rein.
        """
        arrival = self._phone_arrival.get(profile_id)
        door_at = self._phone_door_at.get(profile_id)
        if arrival is None or door_at is None:
            return
        if self.runtime.ctx.state is not AlarmState.PENDING:
            return  # nur in der Eingangsverzögerung (ein Alarm wird nie beendet)
        arrived_at, person = arrival
        if arrived_at < door_at - back.window * 60:
            return  # Heimkehr zu lange vor dem Öffnen
        self._phone_arrival.pop(profile_id, None)
        self._phone_door_at.pop(profile_id, None)
        state = self.hass.states.get(person)
        name = state.name if state is not None else person
        by = tr(self.runtime.lang, "passage_by_phone", who=name)
        try:
            self.runtime.passage(by, by_return=True)
        except HomeAssistantError as err:
            _LOGGER.warning("Handy-Reinlassen nicht möglich: %s", err)

    @callback
    def _check_door_proof(self, profile_id: str, back: ReturnConfig) -> None:
        if door_proof_ok(
            self._arrival_at.get(profile_id), self._door_at.get(profile_id), back.window
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
        if runtime.guest_active:
            # Gastmodus: Gäste sind im Haus, aber nicht geortet -> nicht automatisch scharf
            self._event("AutoArmSkipped", profile_id, reason=reason, guest_mode=True)
            runtime.notifier.notify(
                NotifyEvent.AUTOMATION,
                tr(runtime.lang, "guest_title"),
                tr(runtime.lang, "guest_skipped", profile=name),
                values={"profil": name, "grund": reason},
                test_mode=runtime.ctx.test_mode,
            )
            return
        try:
            # Die Nachricht "automatisch scharf" verschickt die Runtime – als eine Nachricht
            # zusammen mit "Scharf geschaltet" (und den Lücken), nicht als zweite
            runtime.auto_arm(profile_id, self._reason(reason))
        except HomeAssistantError as err:
            details = str(err) or type(err).__name__
            _LOGGER.warning("Automatisches Scharfschalten von %s fehlgeschlagen: %s", name, details)
            # Die Nachricht "nicht scharf geschaltet" (mit Knöpfen) verschickt runtime.arm()
            self._event("AutoArmFailed", profile_id, reason=reason, details=details)
            return
        self.auto_armed_by = profile_id
        self._event("AutoArmed", profile_id, reason=reason)

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
        runtime.auto_disarm(profile_id, self._reason(reason))
        self._event("AutoDisarmed", profile_id, reason=reason)

    def _reason(self, reason: str) -> str:
        """Grund für den Nachrichtentext in der Sprache von Home Assistant."""
        key = {
            REASON_TIME: "reason_time",
            REASON_AWAY: "reason_away",
            REASON_ARRIVAL: "reason_arrival",
            REASON_ARRIVAL_DOOR: "reason_arrival_door",
            REASON_RESTART: "reason_restart",
            REASON_SCHEDULE: "reason_schedule",
        }
        return tr(self.runtime.lang, key[reason]) if reason in key else reason

    @callback
    def _event(self, kind: str, profile_id: str, **data: Any) -> None:
        self.runtime.fire_event({"type": kind, "profile_id": profile_id, **data})
