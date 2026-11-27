"""Entscheidungen der Profil-Automatik – rein, ohne Home Assistant (ADR 0017).

Bis 0.63 standen diese Regeln in ``automation_runner.py`` zwischen den Abonnements von Home
Assistant. Seit 0.64 stehen sie hier, damit der Echtbetrieb und die Szenario-Vorschau
**dieselben** Funktionen aufrufen – eine zweite Kopie der Regeln liefe sonst auseinander.

Die Maschine bekommt Ereignisse (Anwesenheit neu bewertet, Tür auf, Wartezeit abgelaufen,
Annäherung) mit der Uhrzeit und dem Zustand der Alarmanlage und liefert **Aktionen** zurück. Sie
schaltet selbst nichts; der Runner (Echtbetrieb) bzw. die Simulation führt die Aktionen aus:

- ``Arm`` / ``Disarm`` – die Automatik möchte scharf bzw. unscharf schalten. Ob das geht
  (Gastmodus, schon scharf, laufender Alarm …), prüft der Ausführende mit ``arm_allowed`` und
  ``disarm_allowed`` erst im Moment des Schaltens.
- ``LetIn`` – „Bei Rückkehr: Reinlassen“: die Tür ist frei, das Profil bleibt scharf.
- ``StartTimer`` / ``CancelTimer`` – Wartezeit von „alle weg“.
- ``Note`` – ein Ereignis für Logbuch und Automationen (``AutoArmScheduled`` …).
- ``REFRESH`` – Anzeige (Testkarte, Einstellungsseite) neu zeichnen.

Regeln (ADR 0015): „Bei Rückkehr“ je Profil mit eigener Personenliste. Türbeleg und Reinlassen
verlangen eine Rückkehr (vorher sicher weg, jetzt zuhause) UND das Öffnen einer Eingangstür
innerhalb des Zeitfensters – beides, während das Profil scharf ist oder die Eingangsverzögerung
läuft. Ein Alarm wird nie beendet.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from .automation import AutoConfig, all_away_values, door_proof_ok
from .returning import RETURN_ALWAYS, RETURN_AUTO_ONLY, ReturnConfig
from .state_machine import AlarmState

REASON_TIME = "Uhrzeit"
REASON_AWAY = "alle weg"
REASON_ARRIVAL = "Rückkehr"
REASON_ARRIVAL_DOOR = "Rückkehr mit Türbeleg"
REASON_ARRIVAL_ALWAYS = "Rückkehr"
REASON_RESTART = "Neustart"
REASON_SCHEDULE = "Zeitplan"

# Türbeleg und Reinlassen wirken, solange das Profil scharf ist oder die Eingangsverzögerung läuft
PROOF_STATES = (AlarmState.ARMED, AlarmState.PENDING)
# Handy-Reinlassen und „Unscharf, auch nach Scharfschalten von Hand“: so lange muss die Person
# vorher sicher weg gewesen sein
MIN_AWAY_FOR_PASSAGE = 5 * 60


@dataclass(frozen=True)
class AlarmView:
    """Was die Automatik von der Alarmanlage wissen muss (Moment des Ereignisses)."""

    profile_id: str | None
    state: AlarmState


@dataclass(frozen=True)
class Arm:
    profile_id: str
    reason: str


@dataclass(frozen=True)
class Disarm:
    profile_id: str
    reason: str
    only_if_auto: bool = False
    allow_entry: bool = False


@dataclass(frozen=True)
class LetIn:
    profile_id: str
    person: str


@dataclass(frozen=True)
class StartTimer:
    profile_id: str
    seconds: int


@dataclass(frozen=True)
class CancelTimer:
    profile_id: str


@dataclass(frozen=True)
class Note:
    kind: str
    profile_id: str
    data: Mapping[str, Any] = field(default_factory=dict)


class _Refresh:
    def __repr__(self) -> str:
        return "REFRESH"


REFRESH = _Refresh()
Action = Arm | Disarm | LetIn | StartTimer | CancelTimer | Note | _Refresh


def arm_allowed(state: AlarmState, guest: bool) -> str | None:
    """Darf die Automatik jetzt scharf schalten? ``None`` = ja, sonst der Grund.

    Nie über ein anderes (oder dasselbe) scharfe Profil hinweg; im Gastmodus nie (Gäste sind im
    Haus, aber nicht geortet).
    """
    if state is not AlarmState.DISARMED:
        return "not_disarmed"
    if guest:
        return "guest_mode"
    return None


def disarm_allowed(
    alarm: AlarmView,
    profile_id: str,
    *,
    allow_entry: bool,
) -> bool:
    """Darf die Automatik dieses Profil jetzt unscharf schalten?

    Nur das Profil, das gerade scharf ist. Ein laufender Alarm wird nie automatisch beendet; die
    Eingangsverzögerung nur mit ``allow_entry`` (Türbeleg, „auch nach Scharfschalten von Hand“).
    """
    if alarm.profile_id != profile_id:
        return False
    allowed = (
        (AlarmState.ARMED, AlarmState.PENDING)
        if allow_entry
        else (AlarmState.ARMED, AlarmState.ARMING)
    )
    return alarm.state in allowed


class AutomationEngine:
    """Zustand und Entscheidungen von „alle weg“, „Bei Rückkehr“, Türbeleg und Annäherung."""

    def __init__(self) -> None:
        self.configs: dict[str, AutoConfig] = {}
        self.returns: dict[str, ReturnConfig] = {}
        self.auto_armed_by: str | None = None
        self.home: dict[str, bool | None] = {}  # Person -> zuletzt bekannte Anwesenheit
        self.away_since: dict[str, float] = {}  # Person -> seit wann sicher weg
        self.away_due: dict[str, float] = {}  # Profil -> wann „alle weg“ scharf schaltet
        self.arrival_at: dict[str, float] = {}  # Profil -> letzte Rückkehr (Türbeleg)
        self.door_at: dict[str, float] = {}  # Profil -> letzte Türöffnung (Türbeleg)
        self.phone_arrival: dict[str, tuple[float, str]] = {}  # Profil -> (Zeit, Person)
        self.phone_door_at: dict[str, float] = {}  # Profil -> letzte Türöffnung (Reinlassen)
        self.approach_at: dict[str, float] = {}  # Person -> letzte Annäherung (Richtung)

    # --- Einrichten ------------------------------------------------------------

    def configure(
        self, configs: Mapping[str, AutoConfig], returns: Mapping[str, ReturnConfig]
    ) -> None:
        self.configs = dict(configs)
        self.returns = dict(returns)

    @property
    def persons(self) -> set[str]:
        """Alle Personen aus „alle weg“ und „Bei Rückkehr“."""
        persons: set[str] = set()
        for cfg in self.configs.values():
            persons.update(cfg.away_sources)
        for back in self.returns.values():
            persons.update(back.persons)
        return persons

    def begin(self, current: Mapping[str, bool | None], now: float) -> None:
        """Start: aktuelle Anwesenheit übernehmen. Wer schon weg ist, zählt ab jetzt als weg."""
        self.home = dict(current)
        self.away_since = {p: now for p, home in self.home.items() if home is False}

    def stop(self) -> None:
        self.away_due.clear()

    def on_disarmed(self) -> None:
        self.auto_armed_by = None
        self.arrival_at.clear()
        self.door_at.clear()
        self.phone_arrival.clear()
        self.phone_door_at.clear()

    # --- Ereignisse -----------------------------------------------------------

    def note_approach(self, person: str, now: float) -> None:
        """Richtung „nähert sich“ – verlängert die Eingangsverzögerung (ADR 0015)."""
        self.approach_at[person] = now

    def forget_approach(self, person: str) -> None:
        self.approach_at.pop(person, None)

    def presence(
        self, current: Mapping[str, bool | None], now: float, alarm: AlarmView
    ) -> list[Action]:
        """Anwesenheit neu bewertet: Rückkehr erkennen, „alle weg“ planen oder abbrechen.

        ``current``: Bewertung jeder Person (zuhause, sicher weg, unbekannt) in diesem Moment.
        """
        actions: list[Action] = []
        arrived: list[str] = []
        long_away: list[str] = []  # Heimkehr nach mindestens 5 Minuten sicher weg
        for person in list(self.home):
            new = current.get(person)
            if self.home[person] is False and new is True:
                arrived.append(person)
                if now - self.away_since.get(person, now) >= MIN_AWAY_FOR_PASSAGE:
                    long_away.append(person)
            if new is False and self.home[person] is not False:
                self.away_since[person] = now
            if new is not None:
                self.home[person] = new
        actions += self._returned(now, arrived, long_away, alarm)
        for pid, cfg in self.configs.items():
            if not cfg.away_sources:
                continue
            if all_away_values(current.get(p) for p in cfg.away_sources):
                # Nur planen, solange die Anlage unscharf ist – sonst würde nach dem automatischen
                # Scharfschalten bei jeder Signaländerung neu geplant und dann verworfen (0.64.0b5)
                if pid not in self.away_due and alarm.state is AlarmState.DISARMED:
                    self.away_due[pid] = now + cfg.away_delay * 60
                    actions.append(StartTimer(pid, cfg.away_delay * 60))
                    actions.append(Note("AutoArmScheduled", pid, {"minutes": cfg.away_delay}))
                continue
            if self.away_due.pop(pid, None) is not None:
                actions.append(CancelTimer(pid))
                actions.append(Note("AutoArmCancelled", pid))
        return actions

    def away_elapsed(self, profile_id: str, values: Iterable[bool | None]) -> list[Action]:
        """Wartezeit von „alle weg“ abgelaufen: noch immer alle weg -> scharf schalten."""
        self.away_due.pop(profile_id, None)
        if profile_id in self.configs and all_away_values(values):
            return [Arm(profile_id, REASON_AWAY)]
        return []

    def door_opened(self, entity_id: str, now: float, alarm: AlarmView) -> list[Action]:
        """Eine Eingangstür ging auf – NACHDEM die Alarmanlage darauf reagiert hat.

        So zählt eine Tür, die sofort Alarm auslöst, nie als Beleg.
        """
        actions: list[Action] = []
        for pid, back in self.returns.items():
            if not self.proof_active(pid, alarm):
                continue
            if back.lets_in:
                self.phone_door_at[pid] = now
                actions += self._check_phone(pid, back, alarm)
            elif back.door_proof:
                self.door_at[pid] = now
                actions.append(Note("DoorNoted", pid, {"door": entity_id}))
                actions += self._check_door_proof(pid, back)
        actions.append(REFRESH)
        return actions

    # --- Abfragen --------------------------------------------------------------

    @staticmethod
    def proof_active(profile_id: str, alarm: AlarmView) -> bool:
        return alarm.profile_id == profile_id and alarm.state in PROOF_STATES

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
            if (at := self.approach_at.get(p)) is not None and now - at <= valid
        ]
        return (back.approach_delay, near) if near else (0, [])

    def return_report(self, profile_id: str, now: float, alarm: AlarmView) -> dict[str, Any]:
        """„Bei Rückkehr“: was ist schon da, worauf wird gewartet (nur solange scharf)."""
        back = self.returns[profile_id]
        window = back.window * 60

        def until(at: float | None) -> float | None:
            return at + window if at is not None and now - at <= window else None

        arrival = self.arrival_at.get(profile_id)
        door = self.door_at.get(profile_id)
        if back.lets_in:
            phone = self.phone_arrival.get(profile_id)
            arrival = phone[0] if phone else None
            door = self.phone_door_at.get(profile_id)
        active = self.proof_active(profile_id, alarm)
        return {
            "mode": back.mode,
            "active": active,
            "arrival_until": until(arrival) if active else None,
            "door_until": until(door) if active else None,
        }

    # --- intern ----------------------------------------------------------------

    def _returned(
        self, now: float, arrived: list[str], long_away: list[str], alarm: AlarmView
    ) -> list[Action]:
        """„Bei Rückkehr“: jemand aus der Liste eines Profils ist heimgekommen."""
        actions: list[Action] = []
        for pid, back in self.returns.items():
            coming = [p for p in arrived if p in back.persons]
            if not coming:
                continue
            if back.mode == RETURN_AUTO_ONLY:
                actions.append(Disarm(pid, REASON_ARRIVAL, only_if_auto=True))
            elif back.mode == RETURN_ALWAYS:
                # Ohne Tür – nur nach echter Abwesenheit (mindestens 5 Minuten sicher weg)
                if any(p in long_away for p in coming):
                    actions.append(Disarm(pid, REASON_ARRIVAL_ALWAYS, allow_entry=True))
            elif back.door_proof and self.proof_active(pid, alarm):
                self.arrival_at[pid] = now
                actions.append(Note("ArrivalNoted", pid, {"persons": coming}))
                actions += self._check_door_proof(pid, back)
                actions.append(REFRESH)
            elif back.lets_in and self.proof_active(pid, alarm):
                far = [p for p in coming if p in long_away]
                if far:
                    self.phone_arrival[pid] = (now, far[0])
                    actions.append(Note("PhoneArrivalNoted", pid, {"persons": far}))
                    actions += self._check_phone(pid, back, alarm)
                    actions.append(REFRESH)
        return actions

    def _check_phone(self, profile_id: str, back: ReturnConfig, alarm: AlarmView) -> list[Action]:
        """Handy-Reinlassen: Heimkehr und Türöffnung passen zusammen -> reinlassen.

        Das Handy darf sich bis zu ``window`` Minuten vor dem Öffnen melden oder danach,
        solange die Eingangsverzögerung läuft. Eine Heimkehr lässt einmal rein.
        """
        arrival = self.phone_arrival.get(profile_id)
        door_at = self.phone_door_at.get(profile_id)
        if arrival is None or door_at is None:
            return []
        if alarm.state is not AlarmState.PENDING:
            return []  # nur in der Eingangsverzögerung (ein Alarm wird nie beendet)
        arrived_at, person = arrival
        if arrived_at < door_at - back.window * 60:
            return []  # Heimkehr zu lange vor dem Öffnen
        self.phone_arrival.pop(profile_id, None)
        self.phone_door_at.pop(profile_id, None)
        return [LetIn(profile_id, person)]

    def _check_door_proof(self, profile_id: str, back: ReturnConfig) -> list[Action]:
        if door_proof_ok(
            self.arrival_at.get(profile_id), self.door_at.get(profile_id), back.window
        ):
            self.arrival_at.pop(profile_id, None)
            self.door_at.pop(profile_id, None)
            return [Disarm(profile_id, REASON_ARRIVAL_DOOR, allow_entry=True)]
        return []
