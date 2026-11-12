"""Heimkehr-Beobachtung: zeichnet Türöffnungen und Ankünfte auf – und SCHALTET NICHTS.

Dieses Modul darf keine Dienste aufrufen und die Zustandsmaschine nicht berühren (statischer
Test). Es liest nur Zustände, speichert Zeitpunkte und erstellt auf Wunsch einen Bericht.
Die Auswertung selbst steckt in core/homecoming.py.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.core import CALLBACK_TYPE, Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    OPT_HOMECOMING_OBSERVE,
    OPT_HOMECOMING_PERSONS,
    OPT_HOMECOMING_SIGNALS,
    OPT_HOMECOMING_SSIDS,
)
from .core.homecoming import (
    APPROACH_WINDOW,
    DIRECTION_AWAY,
    DIRECTION_HOME,
    DIRECTION_NEUTRAL,
    EARLIEST,
    Arrival,
    DoorOpening,
    EntryTiming,
    PresenceState,
    SourceStats,
    describe,
    doors_without_arrival,
    entry_stats,
    evaluate,
    judge,
    prune,
    report_markdown,
    track,
    track_value,
)
from .names import display_name, plain_name

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
NOTIFICATION_REPORT = "hauswacht_homecoming_report"
RECENT = 10


class HomecomingObserver:
    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        options: dict[str, Any],
        doors: Callable[[], frozenset[str]],
        on_change: Callable[[], None],
    ) -> None:
        self.hass = hass
        self.enabled = bool(options.get(OPT_HOMECOMING_OBSERVE, False))
        self.persons: tuple[str, ...] = tuple(
            dict.fromkeys(p for p in options.get(OPT_HOMECOMING_PERSONS, []) if isinstance(p, str))
        )
        raw_signals = options.get(OPT_HOMECOMING_SIGNALS, {})
        self.signals: dict[str, tuple[str, ...]] = {
            str(person): tuple(e for e in entities if isinstance(e, str))
            for person, entities in (raw_signals.items() if isinstance(raw_signals, dict) else [])
            if isinstance(entities, list)
        }
        self.ssids: frozenset[str] = frozenset(
            s.strip() for s in options.get(OPT_HOMECOMING_SSIDS, []) if isinstance(s, str) and s
        )
        self._door_provider = doors
        self._on_change = on_change
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}.homecoming"
        )
        self.doors: list[dict[str, Any]] = []
        self.arrivals: list[dict[str, Any]] = []
        self.since: float | None = None
        self.entries: list[dict[str, Any]] = []
        self._entry_open: dict[str, Any] | None = None
        self._combined: dict[str, PresenceState] = {}
        self._directions: set[str] = set()
        self._door_entities: frozenset[str] = frozenset()
        self._owners: dict[str, tuple[str, ...]] = {}  # Quelle -> Personen
        self._presence: dict[str, PresenceState] = {}
        self._unsub: CALLBACK_TYPE | None = None

    # --- Lebenszyklus --------------------------------------------------------

    async def async_start(self) -> None:
        stored = await self._store.async_load() or {}
        self.doors = list(stored.get("doors", []))
        self.arrivals = list(stored.get("arrivals", []))
        self.entries = list(stored.get("entries", []))
        self.since = stored.get("since")
        if not self.enabled:
            return
        if self.since is None:
            self.since = dt_util.utcnow().timestamp()
        self.refresh()

    @callback
    def async_stop(self) -> None:
        if self._unsub is not None:
            self._unsub()
            self._unsub = None

    @callback
    def refresh(self) -> None:
        """Türen und Ortungsquellen neu ermitteln und abonnieren."""
        if not self.enabled:
            return
        owners: dict[str, list[str]] = {}
        for person in self.persons:
            owners.setdefault(person, []).append(person)
            state = self.hass.states.get(person)
            trackers = state.attributes.get("device_trackers", []) if state else []
            for tracker in trackers if isinstance(trackers, list) else []:
                if isinstance(tracker, str):
                    owners.setdefault(tracker, []).append(person)
            for signal in self.signals.get(person, ()):
                owners.setdefault(signal, []).append(person)
        new_owners = {k: tuple(v) for k, v in owners.items()}
        doors = self._door_provider()
        if new_owners == self._owners and doors == self._door_entities and self._unsub:
            return
        self._owners = new_owners
        self._door_entities = doors
        for source in self._owners:
            if source not in self._presence:
                self._presence[source] = self._initial_presence(source)
        for person in self.persons:
            if person not in self._combined:
                self._combined[person] = PresenceState(home=self._person_home(person))
        self.async_stop()
        wanted = sorted(set(self._owners) | doors)
        if wanted:
            self._unsub = async_track_state_change_event(self.hass, wanted, self._on_state)

    def _initial_presence(self, source: str) -> PresenceState:
        state = self.hass.states.get(source)
        if state is None:
            return PresenceState()
        self._note_direction(source, state.state)
        initial, _ = track(PresenceState(), state.state, state.last_changed.timestamp(), self.ssids)
        return initial

    def _note_direction(self, source: str, state: str | None) -> None:
        """Richtungs-Sensoren (Nähe) bekommen ein größeres Zeitfenster."""
        if state in DIRECTION_HOME | DIRECTION_AWAY | DIRECTION_NEUTRAL:
            self._directions.add(source)

    def _person_sources(self, person: str) -> list[str]:
        return [s for s, persons in self._owners.items() if person in persons]

    def _person_home(self, person: str) -> bool | None:
        """Kombination: irgendeine Quelle zuhause -> zuhause; alle bekannt weg -> weg."""
        values = [self._presence.get(s, PresenceState()).home for s in self._person_sources(person)]
        if any(v is True for v in values):
            return True
        if values and all(v is False for v in values):
            return False
        return None

    # --- Aufzeichnung --------------------------------------------------------

    @callback
    def _on_state(self, event: Event[EventStateChangedData]) -> None:
        entity_id = event.data["entity_id"]
        old = event.data["old_state"]
        new = event.data["new_state"]
        now = dt_util.utcnow().timestamp()
        changed = False
        opened = new is not None and new.state == "on" and (old is None or old.state == "off")
        if entity_id in self._door_entities and opened:
            self.doors.append({"at": now, "sensor": entity_id})
            changed = True
        if entity_id in self._owners and new is not None:
            trackers_changed = (
                old is not None
                and entity_id.startswith("person.")
                and old.attributes.get("device_trackers") != new.attributes.get("device_trackers")
            )
            if trackers_changed:
                self.hass.loop.call_soon(self.refresh)
            self._note_direction(entity_id, new.state)
            state, away = track(
                self._presence.get(entity_id, PresenceState()), new.state, now, self.ssids
            )
            self._presence[entity_id] = state
            if away is not None:
                for person in self._owners[entity_id]:
                    self.arrivals.append(
                        {"at": now, "person": person, "source": entity_id, "away": away}
                    )
                changed = True
            for person in self._owners[entity_id]:
                combined, away = track_value(
                    self._combined.get(person, PresenceState()), self._person_home(person), now
                )
                self._combined[person] = combined
                if away is not None:
                    self.arrivals.append(
                        {"at": now, "person": person, "source": person + EARLIEST, "away": away}
                    )
                    changed = True
        if changed:
            self.doors = prune(self.doors, now)
            self.arrivals = prune(self.arrivals, now)
            self._store.async_delay_save(self._data, 10)
            self._on_change()

    def _data(self) -> dict[str, Any]:
        return {
            "doors": self.doors,
            "arrivals": self.arrivals,
            "since": self.since,
            "entries": self.entries,
        }

    # --- Eingangsverzögerung: Tür auf bis unscharf ----------------------------

    @callback
    def entry_started(self, door: str | None, delay: int) -> None:
        """Eingangsverzögerung läuft (von der Laufzeit gemeldet)."""
        if not self.enabled:
            return
        self._entry_open = {
            "at": dt_util.utcnow().timestamp(),
            "door": door or "?",
            "delay": int(delay),
        }

    @callback
    def entry_finished(self, *, in_time: bool) -> None:
        """Eingangsverzögerung beendet: unscharf (rechtzeitig) oder Alarm (zu spät)."""
        started, self._entry_open = self._entry_open, None
        if started is None or not self.enabled:
            return
        now = dt_util.utcnow().timestamp()
        self.entries.append(
            {**started, "seconds": round(now - float(started["at"]), 1), "in_time": in_time}
        )
        self.entries = prune(self.entries, now)
        self._store.async_delay_save(self._data, 10)
        self._on_change()

    def entry_timings(self) -> list[EntryTiming]:
        return [
            EntryTiming(
                at=float(e["at"]),
                door=str(e["door"]),
                seconds=float(e["seconds"]),
                in_time=bool(e["in_time"]),
                delay=int(e.get("delay", 0)),
            )
            for e in self.entries
        ]

    # --- Auswertung ----------------------------------------------------------

    def _parsed(self) -> tuple[list[Arrival], list[DoorOpening]]:
        arrivals = [
            Arrival(
                at=float(a["at"]),
                person=str(a["person"]),
                source=str(a["source"]),
                away_seconds=float(a["away"]),
            )
            for a in self.arrivals
        ]
        doors = [DoorOpening(at=float(d["at"]), sensor=str(d["sensor"])) for d in self.doors]
        return arrivals, doors

    def names(self) -> dict[str, str]:
        names: dict[str, str] = {}
        arrivals, doors = self._parsed()
        for arrival in arrivals:
            person = plain_name(self.hass, arrival.person)
            if arrival.source == arrival.person:
                names[arrival.source] = f"{person} (gesamt)"
            elif arrival.source.endswith(EARLIEST):
                names[arrival.source] = f"{person} (frühestes Signal)"
            else:
                names[arrival.source] = f"{person} – {plain_name(self.hass, arrival.source)}"
        for door in doors:
            names[door.sensor] = display_name(self.hass, door.sensor)
        return names

    def _windows(self, arrivals: list[Arrival]) -> dict[str, int]:
        return {
            a.source: APPROACH_WINDOW
            for a in arrivals
            if a.source in self._directions or a.source.endswith(EARLIEST)
        }

    def stats(self) -> dict[str, SourceStats]:
        arrivals, doors = self._parsed()
        return evaluate(arrivals, doors, windows=self._windows(arrivals))

    def days(self) -> float:
        if self.since is None:
            return 0.0
        return max(0.0, (dt_util.utcnow().timestamp() - self.since) / 86400)

    def recent(self) -> list[str]:
        arrivals, doors = self._parsed()
        names = self.names()
        overall = [a for a in arrivals if a.source == a.person]
        verdicts = judge(overall, doors)[-RECENT:]
        return [
            f"{dt_util.as_local(dt_util.utc_from_timestamp(v.arrival.at)):%d.%m. %H:%M} "
            + describe(v, names)
            for v in reversed(verdicts)
        ]

    def attributes(self) -> dict[str, Any]:
        names = self.names()
        return {
            "enabled": self.enabled,
            "days": round(self.days(), 1),
            "door_openings": len(self.doors),
            "sources": {names.get(k, k): v.as_dict() for k, v in sorted(self.stats().items())},
            "recent": self.recent(),
            "entry_times": {
                display_name(self.hass, door): values
                for door, values in entry_stats(self.entry_timings()).items()
            },
        }

    def summary(self) -> int | None:
        if not self.enabled:
            return None
        arrivals, doors = self._parsed()
        return len(judge([a for a in arrivals if a.source == a.person], doors))

    @callback
    def create_report(self) -> None:
        arrivals, doors = self._parsed()
        overall = frozenset(a.source for a in arrivals if a.source == a.person)
        text = report_markdown(
            self.stats(),
            self.names(),
            door_only=doors_without_arrival(arrivals, doors, sources=overall),
            days=self.days(),
        )
        timings = entry_stats(self.entry_timings())
        if timings:
            lines = [
                "\n\n**Tür auf bis unscharf** (Eingangsverzögerung):\n",
                "| Tür | Eingänge | rechtzeitig | zu spät | typisch | längste | Empfehlung |",
                "|---|---|---|---|---|---|---|",
            ]
            for door, v in timings.items():
                lines.append(
                    f"| {display_name(self.hass, door)} | {v['entries']} | "
                    f"{v['in_time']} | {v['too_late']} | "
                    f"{v['median_seconds'] if v['median_seconds'] is not None else '–'} s | "
                    f"{v['max_seconds'] if v['max_seconds'] is not None else '–'} s | "
                    f"{v['recommended_entry_delay'] or '–'} s |"
                )
            text += "\n".join(lines)
        if not self.enabled:
            text = "Die Heimkehr-Beobachtung ist ausgeschaltet.\n\n" + text
        persistent_notification.async_create(
            self.hass,
            text,
            title="Hauswacht: Heimkehr-Beobachtung",
            notification_id=NOTIFICATION_REPORT,
        )
