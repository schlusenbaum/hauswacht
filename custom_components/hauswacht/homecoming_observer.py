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

from .const import DOMAIN, OPT_HOMECOMING_OBSERVE, OPT_HOMECOMING_PERSONS
from .core.homecoming import (
    Arrival,
    DoorOpening,
    PresenceState,
    SourceStats,
    describe,
    doors_without_arrival,
    evaluate,
    judge,
    prune,
    report_markdown,
    track,
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
        self._door_provider = doors
        self._on_change = on_change
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}.homecoming"
        )
        self.doors: list[dict[str, Any]] = []
        self.arrivals: list[dict[str, Any]] = []
        self.since: float | None = None
        self._door_entities: frozenset[str] = frozenset()
        self._owners: dict[str, tuple[str, ...]] = {}  # Quelle -> Personen
        self._presence: dict[str, PresenceState] = {}
        self._unsub: CALLBACK_TYPE | None = None

    # --- Lebenszyklus --------------------------------------------------------

    async def async_start(self) -> None:
        stored = await self._store.async_load() or {}
        self.doors = list(stored.get("doors", []))
        self.arrivals = list(stored.get("arrivals", []))
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
        new_owners = {k: tuple(v) for k, v in owners.items()}
        doors = self._door_provider()
        if new_owners == self._owners and doors == self._door_entities and self._unsub:
            return
        self._owners = new_owners
        self._door_entities = doors
        for source in self._owners:
            if source not in self._presence:
                self._presence[source] = self._initial_presence(source)
        self.async_stop()
        wanted = sorted(set(self._owners) | doors)
        if wanted:
            self._unsub = async_track_state_change_event(self.hass, wanted, self._on_state)

    def _initial_presence(self, source: str) -> PresenceState:
        state = self.hass.states.get(source)
        if state is None:
            return PresenceState()
        initial, _ = track(PresenceState(), state.state, state.last_changed.timestamp())
        return initial

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
            state, away = track(self._presence.get(entity_id, PresenceState()), new.state, now)
            self._presence[entity_id] = state
            if away is not None:
                for person in self._owners[entity_id]:
                    self.arrivals.append(
                        {"at": now, "person": person, "source": entity_id, "away": away}
                    )
                changed = True
        if changed:
            self.doors = prune(self.doors, now)
            self.arrivals = prune(self.arrivals, now)
            self._store.async_delay_save(self._data, 10)
            self._on_change()

    def _data(self) -> dict[str, Any]:
        return {"doors": self.doors, "arrivals": self.arrivals, "since": self.since}

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
            else:
                names[arrival.source] = f"{person} – {plain_name(self.hass, arrival.source)}"
        for door in doors:
            names[door.sensor] = display_name(self.hass, door.sensor)
        return names

    def stats(self) -> dict[str, SourceStats]:
        arrivals, doors = self._parsed()
        return evaluate(arrivals, doors)

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
        if not self.enabled:
            text = "Die Heimkehr-Beobachtung ist ausgeschaltet.\n\n" + text
        persistent_notification.async_create(
            self.hass,
            text,
            title="Hauswacht: Heimkehr-Beobachtung",
            notification_id=NOTIFICATION_REPORT,
        )
