"""Szenario-Vorschau „Was passiert, wenn …?“ (ADR 0017) – rein, ohne Home Assistant.

Spielt typische Situationen mit **denselben Bausteinen wie der Echtbetrieb** durch:

- der Zustandsmaschine (``state_machine.step``: scharf, Eingangsverzögerung, Alarm),
- der Profil-Automatik (``AutomationEngine``: „alle weg“, „Bei Rückkehr“, Türbeleg, Reinlassen,
  Annäherung) samt ``arm_allowed`` / ``disarm_allowed``,
- dem Beleg für „weg“ (``AwayTracker``: Ortung, Tür + Ortung, „Tür + Signal“).

Vereinfacht ist nur die **Welt** drumherum: Jede Person hat ein Handy, das „zuhause“ oder „weg“
meldet (WLAN, Ping …), und – wenn Hauswacht eine Ortung für sie kennt – eine Ortung, die drinnen
oder draußen ist. Es wird nichts geschaltet; die Uhr ist ausgedacht.

Ein Szenario liefert::

    {"key": "...", "profile": id, "title": "...", "result": "ok" | "warn" | "bad",
     "summary": "...", "steps": [{"t": Sekunden, "text": "..."}]}

``ok`` = so soll es sein, ``warn`` = funktioniert, aber mit Haken (z. B. unsicherer Beleg),
``bad`` = unerwünscht (Fehlalarm beim Heimkommen, Einbruch ohne Alarm, wird nie scharf).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .advisor import MIN_SAMPLES, Facts
from .automation import parse_automation
from .automation_engine import (
    REFRESH,
    AlarmView,
    Arm,
    AutomationEngine,
    CancelTimer,
    Disarm,
    LetIn,
    Note,
    StartTimer,
    arm_allowed,
    disarm_allowed,
)
from .away_proof import AwayTracker, Fix, parse_proof_settings
from .profiles import build_profiles, profile_ids, profile_info
from .returning import parse_return
from .state_machine import (
    ActivateReaction,
    AlarmContext,
    AlarmState,
    ArmRequested,
    DisarmRequested,
    EntryDelayElapsed,
    ExitDelayElapsed,
    PassageIn,
    SensorRole,
    SensorTriggered,
    StateChanged,
    TimerKind,
    step,
)
from .state_machine import StartTimer as AlarmTimer

OK = "ok"
WARN = "warn"
BAD = "bad"
RESULTS = (BAD, WARN, OK)

START = 1_000_000.0  # ausgedachte Uhr
# Ohne Messung: so lange vor dem Öffnen der Tür meldet das Handy „zuhause“ (im WLAN)
DEFAULT_PHONE_BEFORE_DOOR = 30
# So lange nach dem Öffnen der Tür wechselt beim Weggehen das Handy auf „weg“
LEAVE_SIGNAL_AFTER = 60
# So lange ist man unterwegs, bevor man heimkommt
AWAY_FOR = 2 * 3600


# --- Texte --------------------------------------------------------------------------------------

TEXTS: Mapping[str, Mapping[str, str]] = {
    "de": {
        # Titel
        "t_burglary_door": "Einbruch durch die Tür {door}",
        "t_burglary_window": "Einbruch durch ein Fenster ({window})",
        "t_return": "{person} kommt heim",
        "t_all_leave": "Alle gehen weg",
        "t_phones_sleep": "Alle sind zuhause, die Handys schlafen ein",
        "t_short_out": "Jemand geht kurz raus – dabei schläft das Handy von {person} ein",
        # Schritte
        "s_armed_manual": "Profil {profile} wird von Hand scharf geschaltet.",
        "s_armed": "Profil {profile} ist scharf.",
        "s_arming": "Ausgangsverzögerung läuft ({s} s).",
        "s_door_open": "Die Tür {door} geht auf.",
        "s_leaves": "{person} geht aus dem Haus.",
        "s_arrives": "{person} kommt heim.",
        "s_window_open": "Das Fenster {window} geht auf.",
        "s_pending": "Eingangsverzögerung läuft ({s} s).",
        "s_pending_long": "Eingangsverzögerung läuft – verlängert auf {s} s, weil sich {who} "
        "genähert hat.",
        "s_alarm": "ALARM.",
        "s_disarmed": "Profil wird unscharf geschaltet ({reason}).",
        "s_let_in": "{person} wird reingelassen – das Profil bleibt scharf.",
        "s_phone_home": "Das Handy von {person} meldet „zuhause“.",
        "s_phone_away": "Das Handy von {person} meldet „weg“.",
        "s_fix_out": "Die Ortung von {person} ist außerhalb von Zuhause.",
        "s_approach": "{person} nähert sich (Richtung).",
        "s_proven": "{person} gilt jetzt als weg ({kind}).",
        "s_timer": "Alle weg – Profil {profile} wird in {m} Minuten scharf.",
        "s_cancel": "Wartezeit abgebrochen – nicht mehr alle weg.",
        "s_auto_armed": "Profil {profile} wird automatisch scharf (alle weg).",
        "s_skip_disarm": "Nicht automatisch unscharf: das Profil wurde von Hand scharf geschaltet.",
        "s_wait": "{m} Minuten später …",
        "proof_fresh": "Ortung",
        "proof_door": "Tür und Ortung",
        "proof_weak": "Tür + Signal – unsicher",
        # Ergebnisse
        "r_alarm_after": "Alarm nach {s} s – so soll es sein.",
        "r_alarm_now": "Sofort Alarm – so soll es sein.",
        "r_no_alarm": "Kein Alarm! Die Tür löst in diesem Profil nicht aus.",
        "r_disarmed": "Unscharf nach {s} s – ohne PIN, ohne Alarm.",
        "r_disarmed_now": "Unscharf, sobald die Tür aufgeht – ohne PIN, ohne Alarm.",
        "r_disarmed_before": "Unscharf, schon bevor die Tür aufgeht – ohne PIN, ohne Alarm.",
        "r_let_in": "Reingelassen nach {s} s – das Profil bleibt scharf, kein Alarm.",
        "r_false_alarm": "Fehlalarm nach {s} s: das Handy meldet sich zu spät. Abhilfe: längere "
        "Eingangsverzögerung (Vorschlag im Check-up).",
        "r_pin_needed": "Nichts passiert von selbst – {person} muss in der Eingangsverzögerung "
        "({s} s) mit PIN, Karte o. Ä. unscharf schalten.",
        "r_pin_needed_manual": "Die Eingangsverzögerung läuft ({s} s) – {person} muss mit PIN, "
        "Karte o. Ä. unscharf schalten (das Profil wurde von Hand scharf geschaltet).",
        "r_armed_after": "Scharf nach {m} Minuten – so soll es sein.",
        "r_armed_weak": "Scharf nach {m} Minuten – aber nur mit unsicherem Beleg (Tür + Signal) "
        "für {who}.",
        "r_never_armed": "Wird nie scharf: {who} gilt nie als weg (keine Ortung, „Tür + Signal“ "
        "aus).",
        "r_stays_disarmed": "Bleibt unscharf – ein schlafendes Handy macht niemanden abwesend.",
        "r_armed_home": "Achtung: Profil {profile} wird scharf, obwohl {who} zuhause ist – "
        "„Tür + Signal“ hält das einschlafende Handy für Weggehen. Bewegt sich {who}, gibt es "
        "Alarm.",
    },
    "en": {
        "t_burglary_door": "Burglary through the door {door}",
        "t_burglary_window": "Burglary through a window ({window})",
        "t_return": "{person} comes home",
        "t_all_leave": "Everyone leaves",
        "t_phones_sleep": "Everyone is home, the phones go to sleep",
        "t_short_out": "Someone steps out briefly – meanwhile the phone of {person} goes to sleep",
        "s_armed_manual": "Profile {profile} is armed by hand.",
        "s_armed": "Profile {profile} is armed.",
        "s_arming": "Exit delay running ({s} s).",
        "s_door_open": "The door {door} opens.",
        "s_leaves": "{person} leaves the house.",
        "s_arrives": "{person} comes home.",
        "s_window_open": "The window {window} opens.",
        "s_pending": "Entry delay running ({s} s).",
        "s_pending_long": "Entry delay running – extended to {s} s because {who} was approaching.",
        "s_alarm": "ALARM.",
        "s_disarmed": "Profile is disarmed ({reason}).",
        "s_let_in": "{person} is let in – the profile stays armed.",
        "s_phone_home": "The phone of {person} reports “home”.",
        "s_phone_away": "The phone of {person} reports “away”.",
        "s_fix_out": "The location of {person} is outside home.",
        "s_approach": "{person} is approaching (direction).",
        "s_proven": "{person} now counts as away ({kind}).",
        "s_timer": "Everyone away – profile {profile} arms in {m} minutes.",
        "s_cancel": "Waiting time cancelled – not everyone is away any more.",
        "s_auto_armed": "Profile {profile} arms automatically (everyone away).",
        "s_skip_disarm": "Not disarmed automatically: the profile was armed by hand.",
        "s_wait": "{m} minutes later …",
        "proof_fresh": "location",
        "proof_door": "door and location",
        "proof_weak": "door + signal – uncertain",
        "r_alarm_after": "Alarm after {s} s – as it should be.",
        "r_alarm_now": "Immediate alarm – as it should be.",
        "r_no_alarm": "No alarm! The door does not trigger in this profile.",
        "r_disarmed": "Disarmed after {s} s – without PIN, without alarm.",
        "r_disarmed_now": "Disarmed as soon as the door opens – without PIN, without alarm.",
        "r_disarmed_before": "Disarmed even before the door opens – without PIN, without alarm.",
        "r_let_in": "Let in after {s} s – the profile stays armed, no alarm.",
        "r_false_alarm": "False alarm after {s} s: the phone reports too late. Fix: a longer "
        "entry delay (suggestion in the check-up).",
        "r_pin_needed": "Nothing happens on its own – {person} has to disarm with PIN, card or "
        "similar during the entry delay ({s} s).",
        "r_pin_needed_manual": "The entry delay is running ({s} s) – {person} has to disarm with "
        "PIN, card or similar (the profile was armed by hand).",
        "r_armed_after": "Armed after {m} minutes – as it should be.",
        "r_armed_weak": "Armed after {m} minutes – but only with an uncertain proof (door + "
        "signal) for {who}.",
        "r_never_armed": "Never arms: {who} never counts as away (no location, “door + signal” "
        "off).",
        "r_stays_disarmed": "Stays disarmed – a sleeping phone makes nobody absent.",
        "r_armed_home": "Caution: profile {profile} arms although {who} is at home – “door + "
        "signal” takes the sleeping phone for leaving. If {who} moves, there is an alarm.",
    },
}


# --- Simulation -----------------------------------------------------------------------------


@dataclass
class _Person:
    phone: bool = True  # Handy meldet „zuhause“ (WLAN, Ping …)
    fix_at: float | None = None  # letzte Ortung (nur mit Ortung)
    fix_out: bool = False


@dataclass
class _Timer:
    due: float
    kind: str  # "alarm" oder "away"
    data: Any = None


@dataclass
class Sim:
    """Eine ausgedachte Anlage: Zustandsmaschine, Automatik und Beleg wie im Echtbetrieb."""

    options: Mapping[str, Any]
    facts: Facts
    lang: str = "de"
    now: float = START
    ctx: AlarmContext = field(default_factory=AlarmContext)
    steps: list[dict[str, Any]] = field(default_factory=list)
    alarm_at: float | None = None
    disarmed_at: float | None = None
    let_in_at: float | None = None
    proofs: dict[str, str] = field(default_factory=dict)
    skipped_disarm: bool = False
    # Kopf des Szenarios (für das Ergebnis)
    key: str = ""
    profile_id: str | None = None
    title: str = ""

    def __post_init__(self) -> None:
        self.profiles = build_profiles(self.options)
        self.engine = AutomationEngine()
        pids = profile_ids(self.options)
        self.engine.configure(
            {pid: parse_automation(self.options, pid) for pid in pids},
            {pid: parse_return(self.options, pid) for pid in pids},
        )
        self.tracker = AwayTracker(parse_proof_settings(self.options))
        self.people = {p: _Person() for p in self.engine.persons}
        self.timers: list[_Timer] = []
        self.engine.begin(self._current(), self.now)

    # --- Kopf und Ergebnis -------------------------------------------------------------

    def label(self, key: str, profile_id: str | None, title: str, **values: Any) -> None:
        self.key, self.profile_id, self.title = key, profile_id, self.text(title, **values)

    def result(self, result: str, summary: str, **values: Any) -> dict[str, Any]:
        return {
            "key": self.key,
            "profile": self.profile_id,
            "title": self.title,
            "result": result,
            "summary": self.text(summary, **values),
            "steps": self.steps,
        }

    # --- Texte -------------------------------------------------------------------------

    def text(self, key: str, **values: Any) -> str:
        return TEXTS[self.lang][key].format(**values)

    def note(self, key: str, **values: Any) -> None:
        self.steps.append({"t": round(self.now - START), "text": self.text(key, **values)})

    def name(self, entity_id: str) -> str:
        return self.facts.name(entity_id)

    def pname(self, pid: str) -> str:
        return profile_info(self.options, pid).name

    # --- Welt ---------------------------------------------------------------------------

    def _fixes(self, person: str) -> list[Fix]:
        p = self.people[person]
        if person not in self.facts.located or p.fix_at is None:
            return []
        return [Fix(p.fix_out, p.fix_out, p.fix_at)]

    def _current(self) -> dict[str, bool | None]:
        current: dict[str, bool | None] = {}
        for person, p in self.people.items():
            before = self.tracker.proven(person)
            value = self.tracker.judge(person, p.phone, self._fixes(person), self.now)
            if value is False and not before:
                kind = (self.tracker.kind(person) or ("", 0.0))[0]
                self.proofs[person] = kind
                self.note("s_proven", person=self.name(person), kind=self.text(f"proof_{kind}"))
            current[person] = value
        return current

    def _view(self) -> AlarmView:
        profile = self.ctx.profile
        return AlarmView(profile.profile_id if profile else None, self.ctx.state)

    def evaluate(self) -> None:
        self.run(self.engine.presence(self._current(), self.now, self._view()))

    def phone(self, person: str, home: bool, *, quiet: bool = False) -> None:
        p = self.people[person]
        if p.phone and not home:
            self.tracker.note_signal_left(person, self.now)
        p.phone = home
        if not quiet:
            self.note("s_phone_home" if home else "s_phone_away", person=self.name(person))
        self.evaluate()

    def fix(self, person: str, outside: bool) -> None:
        if person not in self.facts.located:
            return
        p = self.people[person]
        p.fix_at, p.fix_out = self.now, outside
        if outside:
            self.note("s_fix_out", person=self.name(person))
        self.evaluate()

    def approach(self, person: str) -> None:
        if person in self.facts.direction:
            self.engine.note_approach(person, self.now)
            self.note("s_approach", person=self.name(person))

    def door(self, entity_id: str) -> None:
        self.note("s_door_open", door=self.name(entity_id))
        self.tracker.note_door(self.now)
        self._alarm(SensorTriggered(sensor_key=entity_id, role=SensorRole.ENTRY))
        # Wie im Echtbetrieb: erst reagiert die Alarmanlage, dann zählt die Tür als Beleg
        self.run(self.engine.door_opened(entity_id, self.now, self._view()))
        self.evaluate()

    def window(self, entity_id: str) -> None:
        self.note("s_window_open", window=self.name(entity_id))
        self._alarm(SensorTriggered(sensor_key=entity_id, role=SensorRole.INSTANT))

    def arm(self, pid: str) -> None:
        self.note("s_armed_manual", profile=self.pname(pid))
        self._alarm(ArmRequested(profile=self.profiles[pid], confirmed=True))
        self.wait_until_settled()

    # --- Zeit ---------------------------------------------------------------------------

    def wait(self, seconds: float) -> None:
        end = self.now + seconds
        while True:
            due = sorted((t for t in self.timers if t.due <= end), key=lambda t: t.due)
            if not due:
                break
            timer = due[0]
            self.timers.remove(timer)
            self.now = timer.due
            self._fire(timer)
        self.now = end

    def wait_until_settled(self) -> None:
        """Ausgangsverzögerung abwarten (scharf schalten dauert)."""
        while self.ctx.state is AlarmState.ARMING:
            exits = [t for t in self.timers if t.kind == "alarm"]
            if not exits:
                break
            self.wait(min(t.due for t in exits) - self.now)

    def _fire(self, timer: _Timer) -> None:
        if timer.kind == "away":
            pid = timer.data
            config = self.engine.configs[pid]
            values = [self._current().get(p) for p in config.away_persons]
            self.run(self.engine.away_elapsed(pid, values))
            return
        kind, token = timer.data
        if kind is TimerKind.EXIT_DELAY:
            self._alarm(ExitDelayElapsed(token=token))
        elif kind is TimerKind.ENTRY_DELAY:
            self._alarm(EntryDelayElapsed(token=token))
        # Reaktionszeit: Szenario ist mit dem Alarm zu Ende

    # --- Ausführen ----------------------------------------------------------------------

    def _alarm(self, event: Any) -> None:
        self.ctx, effects = step(self.ctx, event, self.now)
        for effect in effects:
            if isinstance(effect, AlarmTimer):
                self.timers = [t for t in self.timers if t.kind != "alarm"]
                seconds = effect.seconds
                if effect.kind is TimerKind.ENTRY_DELAY:
                    seconds = self._entry_seconds(seconds)
                elif effect.kind is TimerKind.EXIT_DELAY:
                    self.note("s_arming", s=seconds)
                if effect.kind is not TimerKind.REACTION:
                    self.timers.append(
                        _Timer(self.now + seconds, "alarm", (effect.kind, effect.token))
                    )
            elif isinstance(effect, StateChanged):
                self._changed(effect)
            elif isinstance(effect, ActivateReaction) and self.alarm_at is None:
                self.alarm_at = self.now
                self.note("s_alarm")

    def _entry_seconds(self, seconds: int) -> int:
        profile = self.ctx.profile
        extra, near = self.engine.entry_extension(profile.profile_id if profile else None, self.now)
        if extra > seconds:
            self.note("s_pending_long", s=extra, who=", ".join(self.name(p) for p in near))
            return extra
        self.note("s_pending", s=seconds)
        return seconds

    def _changed(self, effect: StateChanged) -> None:
        if effect.new is AlarmState.ARMED and effect.old is AlarmState.ARMING:
            self.note("s_armed", profile=self.pname(self.ctx.profile.profile_id))  # type: ignore[union-attr]
        if effect.new is AlarmState.DISARMED:
            self.timers = [t for t in self.timers if t.kind != "alarm"]
            self.engine.on_disarmed()

    def run(self, actions: list[Any]) -> None:
        for action in actions:
            if action is REFRESH or isinstance(action, Note):
                continue
            if isinstance(action, StartTimer):
                self.timers.append(_Timer(self.now + action.seconds, "away", action.profile_id))
                m = action.seconds // 60
                self.note("s_timer", profile=self.pname(action.profile_id), m=m)
            elif isinstance(action, CancelTimer):
                self.timers = [
                    t for t in self.timers if not (t.kind == "away" and t.data == action.profile_id)
                ]
                self.note("s_cancel")
            elif isinstance(action, Arm):
                if arm_allowed(self.ctx.state, guest=False) is None:
                    self.note("s_auto_armed", profile=self.pname(action.profile_id))
                    self._alarm(
                        ArmRequested(profile=self.profiles[action.profile_id], confirmed=True)
                    )
                    self.engine.auto_armed_by = action.profile_id
            elif isinstance(action, Disarm):
                self._disarm(action)
            elif isinstance(action, LetIn) and self.ctx.state is AlarmState.PENDING:
                self._alarm(PassageIn(door=self.ctx.trigger_sensor, by=action.person))
                self.let_in_at = self.now
                self.note("s_let_in", person=self.name(action.person))

    def _disarm(self, action: Disarm) -> None:
        if not disarm_allowed(self._view(), action.profile_id, allow_entry=action.allow_entry):
            return
        if action.only_if_auto and self.engine.auto_armed_by != action.profile_id:
            self.skipped_disarm = True
            self.note("s_skip_disarm")
            return
        self._alarm(DisarmRequested())
        self.disarmed_at = self.now
        self.note("s_disarmed", reason=action.reason)


# --- Szenarien ------------------------------------------------------------------------------


def _burglary_door(
    options: Mapping[str, Any], facts: Facts, lang: str, pid: str, door: str
) -> dict[str, Any]:
    sim = Sim(options, facts, lang)
    sim.label(f"burglary_door:{pid}:{door}", pid, "t_burglary_door", door=facts.name(door))
    sim.arm(pid)
    sim.wait(60)
    opened = sim.now
    sim.door(door)
    sim.wait(15 * 60)
    if sim.alarm_at is None:
        return sim.result(BAD, "r_no_alarm")
    return sim.result(OK, "r_alarm_after", s=round(sim.alarm_at - opened))


def _burglary_window(
    options: Mapping[str, Any], facts: Facts, lang: str, pid: str, window: str
) -> dict[str, Any]:
    sim = Sim(options, facts, lang)
    sim.label(f"burglary_window:{pid}", pid, "t_burglary_window", window=facts.name(window))
    sim.arm(pid)
    sim.wait(60)
    sim.window(window)
    if sim.alarm_at is None:
        return sim.result(BAD, "r_no_alarm")
    return sim.result(OK, "r_alarm_now")


def _leave(sim: Sim, persons: list[str], door: str | None) -> None:
    """Personen gehen nacheinander durch die Tür; danach meldet das Handy „weg“."""
    for person in persons:
        sim.note("s_leaves", person=sim.name(person))
        if door is not None:
            sim.door(door)
        sim.wait(LEAVE_SIGNAL_AFTER)
        sim.phone(person, False)
        sim.wait(5 * 60)
        sim.fix(person, outside=True)


def _return(
    options: Mapping[str, Any], facts: Facts, lang: str, pid: str, person: str
) -> dict[str, Any]:
    """Eine Person aus „Bei Rückkehr“ kommt heim (mit ihrer gemessenen Zeit, wenn es sie gibt).

    Vorher gehen alle weg. Schaltet „alle weg“ das Profil, ist es automatisch scharf, sonst wird
    es von Hand scharf geschaltet.
    """
    auto = parse_automation(options, pid)
    doors = facts.entry_doors.get(pid, ())
    door = doors[0] if doors else None
    sim = Sim(options, facts, lang)
    sim.label(f"return:{pid}:{person}", pid, "t_return", person=facts.name(person))
    _leave(sim, [person, *(p for p in sim.people if p != person)], door)
    if auto.away_persons:
        sim.wait(auto.away_delay * 60 + 60)
    if sim.ctx.state is AlarmState.DISARMED:
        sim.arm(pid)
    sim.wait(AWAY_FOR)
    # Heimkommen: das Handy meldet sich vor der Tür – oder so spät nach der Tür wie gemessen
    measured = facts.proof_needed.get(person)
    after = measured.longest if measured is not None and measured.count >= MIN_SAMPLES else None
    sim.approach(person)
    sim.wait(5 * 60)
    sim.note("s_arrives", person=sim.name(person))
    if after is None:
        sim.fix(person, outside=False)
        sim.phone(person, True)
        sim.wait(DEFAULT_PHONE_BEFORE_DOOR)
    opened = sim.now
    if door is not None:
        sim.door(door)
    if after is not None:
        sim.wait(after)
        sim.fix(person, outside=False)
        sim.phone(person, True)
    sim.wait(15 * 60)
    return _return_verdict(sim, person, opened)


def _return_verdict(sim: Sim, person: str, opened: float) -> dict[str, Any]:
    seconds = sim.profiles[sim.profile_id or ""].entry_delay
    if sim.skipped_disarm and sim.disarmed_at is None and sim.let_in_at is None:
        # Von Hand scharf: hier wird bewusst nicht automatisch unscharf – die Person schaltet
        # in der Eingangsverzögerung selbst unscharf (kein Fehlalarm, nur ohne Komfort)
        return sim.result(WARN, "r_pin_needed_manual", s=seconds, person=sim.name(person))
    if sim.alarm_at is not None:
        return sim.result(BAD, "r_false_alarm", s=round(sim.alarm_at - opened))
    if sim.let_in_at is not None:
        return sim.result(OK, "r_let_in", s=round(sim.let_in_at - opened))
    if sim.disarmed_at is not None and sim.disarmed_at < opened:
        return sim.result(OK, "r_disarmed_before")
    if sim.disarmed_at is not None and round(sim.disarmed_at - opened) == 0:
        return sim.result(OK, "r_disarmed_now")
    if sim.disarmed_at is not None:
        return sim.result(OK, "r_disarmed", s=round(sim.disarmed_at - opened))
    return sim.result(WARN, "r_pin_needed", s=seconds, person=sim.name(person))


def _all_leave(options: Mapping[str, Any], facts: Facts, lang: str, pid: str) -> dict[str, Any]:
    auto = parse_automation(options, pid)
    doors = facts.entry_doors.get(pid, ())
    sim = Sim(options, facts, lang)
    sim.label(f"all_leave:{pid}", pid, "t_all_leave")
    start = sim.now
    _leave(sim, list(auto.away_persons), doors[0] if doors else None)
    sim.wait(auto.away_delay * 60 + 60)
    if sim.ctx.state is AlarmState.DISARMED:
        who = ", ".join(sim.name(p) for p in auto.away_persons if p not in sim.proofs)
        return sim.result(BAD, "r_never_armed", who=who)
    minutes = round((sim.now - start) / 60)
    weak = [p for p in auto.away_persons if sim.proofs.get(p) == "weak"]
    if weak:
        return sim.result(WARN, "r_armed_weak", m=minutes, who=", ".join(map(sim.name, weak)))
    return sim.result(OK, "r_armed_after", m=minutes)


def _phones_sleep(options: Mapping[str, Any], facts: Facts, lang: str, pid: str) -> dict[str, Any]:
    """Alle zuhause, alle Handys schlafen ein (oder das WLAN fällt aus) – ohne Tür."""
    auto = parse_automation(options, pid)
    sim = Sim(options, facts, lang)
    sim.label(f"phones_sleep:{pid}", pid, "t_phones_sleep")
    for person in auto.away_persons:
        sim.phone(person, False)
    sim.wait(auto.away_delay * 60 + 30 * 60)
    if sim.ctx.state is not AlarmState.DISARMED:
        who = ", ".join(sim.name(p) for p in auto.away_persons)
        return sim.result(BAD, "r_armed_home", profile=sim.pname(pid), who=who)
    return sim.result(OK, "r_stays_disarmed")


def _short_out(
    options: Mapping[str, Any], facts: Facts, lang: str, pid: str, person: str
) -> dict[str, Any]:
    """„Tür + Signal“: jemand anderes geht kurz raus, und das Handy der Person schläft ein."""
    auto = parse_automation(options, pid)
    doors = facts.entry_doors.get(pid, ())
    sim = Sim(options, facts, lang)
    sim.label(f"short_out:{pid}:{person}", pid, "t_short_out", person=facts.name(person))
    # Alle anderen sind unterwegs (sonst würde ohnehin nicht scharf geschaltet)
    _leave(sim, [p for p in auto.away_persons if p != person], doors[0] if doors else None)
    sim.wait(30 * 60)
    if doors:
        sim.door(doors[0])  # Paket annehmen, Müll rausbringen …
    sim.wait(60)
    sim.phone(person, False)
    sim.wait(auto.away_delay * 60 + 60)
    if sim.ctx.state is not AlarmState.DISARMED:
        return sim.result(WARN, "r_armed_home", profile=sim.pname(pid), who=sim.name(person))
    return sim.result(OK, "r_stays_disarmed")


def scenarios(
    options: Mapping[str, Any], facts: Facts, language: str = "de"
) -> list[dict[str, Any]]:
    """Alle Standard-Szenarien je Profil: Unerwünschtes zuerst, dann mit Haken, dann gut."""
    lang = "de" if language == "de" else "en"
    found: list[dict[str, Any]] = []
    weak = parse_proof_settings(options).weak
    for pid in profile_ids(options):
        doors = facts.entry_doors.get(pid, ())
        windows = facts.windows.get(pid, ())
        found.extend(_burglary_door(options, facts, lang, pid, door) for door in doors)
        if windows:
            found.append(_burglary_window(options, facts, lang, pid, windows[0]))
        back = parse_return(options, pid)
        if back.active:
            found.extend(_return(options, facts, lang, pid, p) for p in back.persons)
        auto = parse_automation(options, pid)
        if auto.away_persons:
            found.append(_all_leave(options, facts, lang, pid))
            found.append(_phones_sleep(options, facts, lang, pid))
            found.extend(
                _short_out(options, facts, lang, pid, p) for p in auto.away_persons if p in weak
            )
    return sorted(found, key=lambda s: RESULTS.index(s["result"]))
