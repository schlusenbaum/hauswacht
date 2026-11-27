"""Ausgangserkennung im Echtbetrieb (ADR 0014) – Home-Assistant-Schicht.

Hängt an der Eingangsverzögerung eines Bereichs:

1. Beginnt sie, prüft :meth:`ExitDetector.begin`, ob das Profil die Ausgangserkennung nutzt, ob
   jemand nachweislich zuhause ist (ein Weggehen-Signal sagt „zuhause“) und – wenn eingetragen –
   ob der Melder im Haus kurz vorher etwas gemeldet hat. Dann wird aus der Eingangsverzögerung
   eine stille Wartezeit.
2. Sofort geht eine wichtige Nachricht an alle Alarm-Empfänger mit [Alarm jetzt] und
   [Durchlassen].
3. Während der Wartezeit werden die Signale dieser Personen beobachtet. Sagen sie mindestens
   30 Sekunden lang „weg“ (Regeln aus ADR 0021, Schutz gegen WLAN-Ausfall), ist die Person
   rausgegangen: Das Profil bleibt scharf, die Tür wird überbrückt, bis sie zu ist.
4. Sonst gibt es am Ende der Wartezeit Alarm – wie nach der Eingangsverzögerung.

Die Ausgangserkennung schaltet nie unscharf, hält nie eine laufende Sirene an und ändert nichts
an Brandalarm, 24h-Meldern oder Sabotage.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.core import CALLBACK_TYPE, Event, EventStateChangedData, callback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.util import dt as dt_util

from .const import OPT_HOMECOMING_SIGNALS, OPT_HOMECOMING_SSIDS
from .core.automation import parse_automation, person_value
from .core.away_proof import SIM_HOME, SIM_REAL
from .core.exit_detection import (
    CONFIRM,
    ExitWatch,
    can_leave,
    gone,
    inside_ok,
    parse_exit,
)
from .core.homecoming import direction_hint, presence
from .core.presence_rules import (
    DEFAULT_RULES,
    MODE_ONE,
    PersonRules,
    Signal,
    parse_presence_rules,
    trigger_value,
    triggered,
)
from .core.profiles import profile_ids
from .core.returning import parse_return
from .names import display_name

if TYPE_CHECKING:
    from .runtime import HauswachtRuntime

_LOGGER = logging.getLogger(__name__)

CHECK_EVERY = timedelta(seconds=5)


def presence_persons(options: Mapping[str, Any]) -> list[str]:
    """Alle Personen, deren Anwesenheit Hauswacht kennt (Beobachtung, Automatik, Rückkehr,
    Signale)."""
    found = [p for p in options.get("homecoming_persons", []) if isinstance(p, str)]
    signals = options.get(OPT_HOMECOMING_SIGNALS, {})
    if isinstance(signals, Mapping):
        found.extend(p for p in signals if isinstance(p, str))
    found.extend(triggered(options))
    for pid in profile_ids(options):
        found.extend(parse_automation(options, pid).away_persons)
        found.extend(parse_return(options, pid).persons)
    return list(dict.fromkeys(found))


class ExitDetector:
    """Stille Wartezeit statt Eingangsverzögerung, wenn jemand rausgeht (ADR 0014)."""

    def __init__(self, runtime: HauswachtRuntime) -> None:
        self.runtime = runtime
        self.hass = runtime.hass
        self.watch: ExitWatch | None = None
        self.seconds = 0
        self._inside_last: dict[str, float] = {}
        self._unsub_inside: CALLBACK_TYPE | None = None
        self._unsubs: list[CALLBACK_TYPE] = []

    # --- Lebenszyklus -------------------------------------------------------------------

    @callback
    def start(self) -> None:
        """Melder im Haus aller Profile mitverfolgen (wann zuletzt „an“)."""
        options = self.runtime.options
        inside = sorted(
            {e for pid in profile_ids(options) for e in parse_exit(options, pid).inside}
        )
        if inside:
            self._unsub_inside = async_track_state_change_event(self.hass, inside, self._on_inside)

    @callback
    def stop(self) -> None:
        self.end()
        if self._unsub_inside is not None:
            self._unsub_inside()
            self._unsub_inside = None

    @callback
    def _on_inside(self, event: Event[EventStateChangedData]) -> None:
        new = event.data["new_state"]
        if new is not None and new.state == "on":
            self.note_inside(event.data["entity_id"])

    @callback
    def note_inside(self, entity_id: str) -> None:
        """Melder im Haus meldet „an“ – echt oder im Testmodus simuliert."""
        self._inside_last[entity_id] = dt_util.utcnow().timestamp()

    def inside_of(self, profile_id: str | None) -> frozenset[str]:
        """Melder im Haus eines Profils (nur, wenn die Ausgangserkennung dort an ist)."""
        config = parse_exit(self.runtime.options, profile_id)
        return config.inside if config.enabled else frozenset()

    def all_inside(self) -> frozenset[str]:
        options = self.runtime.options
        return frozenset(e for pid in profile_ids(options) for e in self.inside_of(pid))

    @property
    def active(self) -> bool:
        return self.watch is not None

    # --- Signale ------------------------------------------------------------------------

    def _ssids(self) -> frozenset[str]:
        raw = self.runtime.options.get(OPT_HOMECOMING_SSIDS, [])
        return frozenset(s.strip() for s in raw if isinstance(s, str) and s)

    def _simulated(self, person: str) -> bool | None:
        """Im Testmodus simulierte Anwesenheit (ADR 0016): True zuhause, False weg, None echt."""
        value = self.runtime.presence_simulated(person)
        if value is None or value == SIM_REAL:
            return None
        return value == SIM_HOME

    def _rules(self, person: str) -> PersonRules:
        """Regeln der Person; mit eigenem Auslöser zählt nur er (wie „eines reicht“)."""
        rule = parse_presence_rules(self.runtime.options).get(person, DEFAULT_RULES)
        return PersonRules(mode=MODE_ONE) if rule.trigger else rule

    def _signals(self, person: str) -> list[Signal]:
        rule = parse_presence_rules(self.runtime.options).get(person, DEFAULT_RULES)
        if rule.trigger is not None:
            # Eigener Auslöser der Person: nur er zählt
            state = self.hass.states.get(rule.trigger)
            value = trigger_value(state.state if state else None, rule.trigger_away)
            since = state.last_changed.timestamp() if state is not None else 0.0
            return [Signal(rule.trigger, value, since)]
        raw = self.runtime.options.get(OPT_HOMECOMING_SIGNALS, {})
        extra = raw.get(person, []) if isinstance(raw, Mapping) else []
        ssids = self._ssids()
        found: list[Signal] = []
        for entity_id in [person, *(e for e in extra if isinstance(e, str))]:
            state = self.hass.states.get(entity_id)
            value = state.state if state is not None else None
            since = state.last_changed.timestamp() if state is not None else 0.0
            if entity_id.startswith("person."):
                found.append(Signal(entity_id, person_value(value), since))
            elif not direction_hint(value):
                found.append(Signal(entity_id, presence(value, ssids), since))
        return found

    def _wlan_dependent(self, entity_id: str) -> bool:
        """Hängt das Signal am WLAN? (Ping, Router, WLAN-Sensor der App)"""
        state = self.hass.states.get(entity_id)
        if state is None:
            return True
        if entity_id.startswith("person."):
            source = state.attributes.get("source")
            return isinstance(source, str) and self._wlan_dependent(source)
        if entity_id.startswith("device_tracker."):
            return state.attributes.get("source_type") == "router"
        return entity_id.startswith("sensor.")  # WLAN-Sensoren der App (SSID, Verbindung)

    # --- Ablauf -------------------------------------------------------------------------

    @callback
    def begin(self) -> str | None:
        """Eingangsverzögerung beginnt – was nun?

        - ``"passage"``: Melder im Haus hat kurz vorher etwas gemeldet – jemand kam von innen:
          automatischer Durchgang (wie die Durchgang-Taste „rausgehen“), ohne Handy-Prüfung.
        - ``"wait"``: kein Melder im Haus eingetragen, aber jemand nachweislich zuhause: stille
          Wartezeit, das Handy muss „weg“ sagen.
        - ``None``: normale Eingangsverzögerung.
        """
        self.end()
        runtime = self.runtime
        profile = runtime.ctx.profile
        door = runtime.ctx.trigger_sensor
        if profile is None or door is None or door not in runtime.entry_doors():
            return None
        config = parse_exit(runtime.options, profile.profile_id)
        if not config.enabled:
            return None
        now = dt_util.utcnow().timestamp()
        if not inside_ok(config, [self._inside_last.get(e, 0.0) for e in config.inside], now):
            _LOGGER.debug("Ausgangserkennung: Melder im Haus ohne Meldung – normale Verzögerung")
            return None
        if config.inside:
            # Jemand kam von innen: automatischer Durchgang (Entscheidung C, ADR 0014)
            _LOGGER.debug("Ausgangserkennung: Melder im Haus meldete – automatischer Durchgang")
            runtime.fire_event(
                {"type": "ExitPassage", "profile_id": profile.profile_id, "door": door}
            )
            return "passage"
        home = frozenset(
            p
            for p in presence_persons(runtime.options)
            if (sim := self._simulated(p)) is True
            or (sim is None and can_leave(self._rules(p), self._signals(p)))
        )
        if not home:
            _LOGGER.debug("Ausgangserkennung: niemand nachweislich zuhause – normale Verzögerung")
            return None
        self.watch = ExitWatch(now, door, home)
        self.seconds = config.wait * 60
        watched = sorted({s.entity_id for p in home for s in self._signals(p)})
        self._unsubs.append(async_track_state_change_event(self.hass, watched, self._on_signal))
        self._unsubs.append(async_track_time_interval(self.hass, self._tick, CHECK_EVERY))
        _LOGGER.info(
            "Ausgangserkennung: stille Wartezeit %s min, zuhause: %s",
            config.wait,
            ", ".join(sorted(home)),
        )
        runtime.fire_event(
            {
                "type": "ExitWaitStarted",
                "profile_id": profile.profile_id,
                "door": door,
                "seconds": config.wait * 60,
                "persons": sorted(home),
            }
        )
        return "wait"

    @callback
    def end(self) -> None:
        """Wartezeit vorbei (unscharf, Alarm, Durchgang …): nicht mehr beobachten."""
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        self.watch = None
        self.seconds = 0

    @callback
    def _on_signal(self, _event: Event[EventStateChangedData]) -> None:
        self._evaluate()

    @callback
    def _tick(self, _now: Any) -> None:
        self._evaluate()

    @callback
    def _evaluate(self) -> None:
        watch = self.watch
        if watch is None:
            return
        now = dt_util.utcnow().timestamp()
        for person in watch.candidates:
            sim = self._simulated(person)
            if sim is not None:  # Testmodus: simulierte Anwesenheit (ADR 0016)
                watch.note(person, not sim, now)
                continue
            away = gone(self._rules(person), self._signals(person), watch.opened_at)
            wlan = bool(away) and all(self._wlan_dependent(e) for e in away)
            watch.note(person, bool(away), now, wlan_only=wlan)
        person = watch.left(now)
        if person is None:
            return
        door = watch.door
        self.end()
        _LOGGER.info("Ausgangserkennung: %s ist rausgegangen", person)
        self.runtime.exit_let_out(door, display_name(self.hass, person), person)

    def message_values(self) -> dict[str, Any]:
        """Für Anzeige und Nachrichten: wie lange, wer war zuhause."""
        watch = self.watch
        return {
            "persons": sorted(watch.candidates) if watch else [],
            "confirm": CONFIRM,
        }
