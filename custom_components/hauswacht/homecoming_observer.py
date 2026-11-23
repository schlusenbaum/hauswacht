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
from .core.departure import (
    Departure,
    DepartureVerdict,
    advice_text,
    departure_csv_rows,
    departure_lines,
    departure_stats,
    judge_departures,
    wait_advice,
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
    csv_rows,
    describe,
    door_proof_advice,
    door_proof_lines,
    doors_without_arrival,
    entry_stats,
    evaluate,
    judge,
    prune,
    report_markdown,
    to_csv,
    track,
)
from .core.texts import DE, lang_of, tr
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
        self.departures: list[dict[str, Any]] = []
        self.since: float | None = None
        self.departure_since: float | None = None  # Beginn der Messung "Weggehen"
        self.entries: list[dict[str, Any]] = []
        self._entry_open: dict[str, Any] | None = None
        # Kombination fürs Weggehen: nur echte Anwesenheits-Signale, ohne Richtung (ADR 0014)
        self._present: dict[str, bool | None] = {}
        self._absent_since: dict[str, float] = {}  # Person: seit wann "alle Signale" weg
        self._direction_home_at: dict[str, float] = {}  # Richtung: seit wann "nähert sich"
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
        self.departures = list(stored.get("departures", []))
        self.entries = list(stored.get("entries", []))
        self.since = stored.get("since")
        self.departure_since = stored.get("departure_since")
        if not self.enabled:
            return
        now = dt_util.utcnow().timestamp()
        if self.since is None:
            self.since = now
        if self.departure_since is None:
            # Weggehen wird erst seit 0.60 gemessen – ältere Beobachtungstage zählen nicht
            self.departure_since = now
            self._store.async_delay_save(self._data, 10)
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
            if person not in self._present:
                self._present[person] = self._person_present(person)
                if self._present[person] is False:
                    self._absent_since[person] = self._initial_absent(person)
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

    def _initial_absent(self, person: str) -> float:
        """Beim Start schon weg: "weg seit" = spätester Abschied der Quellen (ohne Richtung)."""
        since = [
            state.away_since
            for source in self._person_sources(person)
            if source not in self._directions
            and (state := self._presence.get(source)) is not None
            and state.away_since
        ]
        return max(since) if since else dt_util.utcnow().timestamp()

    def _person_sources(self, person: str) -> list[str]:
        return [s for s, persons in self._owners.items() if person in persons]

    def _person_present(self, person: str) -> bool | None:
        """Kombination fürs Weggehen.

        Richtungs-Sensoren (Nähe, Places) zählen nicht: "nähert sich" heißt nicht "ist da", und
        "steht" heißt nicht "ist weg". Zuhause, sobald ein Signal zuhause meldet; weg, sobald
        mindestens eines "weg" meldet und keines "zuhause" (schweigende Signale zählen als weg).
        """
        values = [
            self._presence.get(s, PresenceState()).home
            for s in self._person_sources(person)
            if s not in self._directions
        ]
        if any(v is True for v in values):
            return True
        if any(v is False for v in values):
            return False
        return None

    def _track_leaving(self, person: str, now: float) -> bool:
        """Weggehen und Rückkehr der Kombination "alle Signale" mitschreiben."""
        before = self._present.get(person)
        present = self._person_present(person)
        if present is None or present == before:
            return False
        self._present[person] = present
        source = person + EARLIEST
        if before is True and present is False:
            self.departures.append({"at": now, "person": person, "source": source})
            self._absent_since[person] = now
            return True
        changed = False
        if present is True:
            for record in reversed(self.departures):
                if record["source"] == source:
                    if record.get("back") is None:
                        record["back"] = now
                        changed = True
                    break
            left = self._absent_since.pop(person, None)
            if before is False and left is not None:
                self.arrivals.append(
                    {
                        "at": (at := self._earliest_arrival(person, now, left)),
                        "person": person,
                        "source": source,
                        "away": at - left,
                    }
                )
                changed = True
        return changed

    def _earliest_arrival(self, person: str, now: float, left: float) -> float:
        """Frühestes Signal einer echten Heimkehr.

        Gezählt wird nur, wenn ein echtes Anwesenheits-Signal wieder "zuhause" meldet. Hat eine
        Richtung (Nähe, Places) kurz davor – höchstens 15 Minuten und nach dem Weggehen –
        "nähert sich" gemeldet, gilt dieser frühere Zeitpunkt. "Nähert sich" allein ist also
        keine Heimkehr mehr (z. B. bei Fahrten in der Umgebung).
        """
        earliest = now
        for source in self._person_sources(person):
            at = self._direction_home_at.get(source)
            if (
                source in self._directions
                and at is not None
                and left < at <= now
                and now - at <= APPROACH_WINDOW
            ):
                earliest = min(earliest, at)
        return earliest

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
            prev = self._presence.get(entity_id, PresenceState())
            state, away = track(prev, new.state, now, self.ssids)
            self._presence[entity_id] = state
            if entity_id in self._directions:
                # Wann die Richtung zuletzt "nähert sich/angekommen" meldete (Hinweis fürs
                # frühestes Signal – zählt nur, wenn danach wirklich jemand heimkommt)
                if state.home is True and prev.home is not True:
                    self._direction_home_at[entity_id] = now
                elif state.home is False:
                    self._direction_home_at.pop(entity_id, None)
            if away is not None:
                for person in self._owners[entity_id]:
                    self.arrivals.append(
                        {"at": now, "person": person, "source": entity_id, "away": away}
                    )
                changed = True
            if prev.home is True and state.home is False:
                for person in self._owners[entity_id]:
                    self.departures.append({"at": now, "person": person, "source": entity_id})
                changed = True
            for person in self._owners[entity_id]:
                changed = self._track_leaving(person, now) or changed
        if changed:
            self.doors = prune(self.doors, now)
            self.arrivals = prune(self.arrivals, now)
            self.departures = prune(self.departures, now)
            self._store.async_delay_save(self._data, 10)
            self._on_change()

    @callback
    def reset(self, part: str = "all") -> None:
        """Messungen löschen und neu beginnen (Einstellungsseite).

        ``part``: ``all`` (alles), ``departure`` (nur Weggehen) oder ``arrival`` (nur Heimkommen:
        die Heimkehr-Auswertung beginnt neu; die Heimkehrten bleiben intern gespeichert, weil das
        Weggehen mit ihnen erkennt, wann jemand zurück war). Der aktuelle Anwesenheitsstand
        bleibt erhalten, damit das nächste Kommen und Gehen sofort wieder zählt.
        """
        now = dt_util.utcnow().timestamp()
        if part == "arrival":
            self.since = now
        if part in ("departure", "all"):
            self.departures = []
            self.departure_since = now
        if part == "all":
            self.doors = []
            self.arrivals = []
            self.entries = []
            self._entry_open = None
            self.since = now
        self._store.async_delay_save(self._data, 1)
        self._on_change()

    def _data(self) -> dict[str, Any]:
        return {
            "doors": self.doors,
            "arrivals": self.arrivals,
            "departures": self.departures,
            "since": self.since,
            "departure_since": self.departure_since,
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

    def _parsed(self, *, everything: bool = False) -> tuple[list[Arrival], list[DoorOpening]]:
        """Heimkehrten und Türöffnungen.

        Für die Heimkehr-Auswertung nur ab ``since`` (nach "Heimkommen zurücksetzen" bleiben
        ältere Heimkehrten gespeichert, weil das Weggehen mit ihnen die Rückkehr erkennt).
        ``everything``: alles Gespeicherte (für die Messung "Weggehen").
        """
        start = 0.0 if everything or self.since is None else float(self.since)
        arrivals = [
            Arrival(
                at=float(a["at"]),
                person=str(a["person"]),
                source=str(a["source"]),
                away_seconds=float(a["away"]),
            )
            for a in self.arrivals
            if float(a["at"]) >= start
        ]
        doors = [
            DoorOpening(at=float(d["at"]), sensor=str(d["sensor"]))
            for d in self.doors
            if float(d["at"]) >= start
        ]
        return arrivals, doors

    def _departure_names(self, names: dict[str, str]) -> dict[str, str]:
        """Beim Weggehen heißt die Kombination "alle Signale" statt "frühestes Signal"."""
        result = dict(names)
        for person in self.persons:
            result[person + EARLIEST] = tr(
                self.lang, "dep_all", person=plain_name(self.hass, person)
            )
        return result

    def departure_verdicts(self) -> list[DepartureVerdict]:
        arrivals, doors = self._parsed(everything=True)
        departures = [
            Departure(
                at=float(d["at"]),
                person=str(d["person"]),
                source=str(d["source"]),
                back=float(d["back"]) if d.get("back") is not None else None,
            )
            for d in self.departures
        ]
        return judge_departures(departures, arrivals, doors, dt_util.utcnow().timestamp())

    def departure_advice(self) -> dict[str, dict[str, Any]]:
        """Je Person: Empfehlung für "Rausgehen ohne PIN erkennen" (ADR 0014)."""
        return wait_advice(self.departure_verdicts(), self.departure_days())

    @property
    def lang(self) -> str:
        return lang_of(self.hass.config.language)

    def _when(self, at: float, *, seconds: bool = False, year: bool = True) -> str:
        local = dt_util.as_local(dt_util.utc_from_timestamp(at))
        if self.lang == DE:
            fmt = "%d.%m.%Y %H:%M" if year else "%d.%m. %H:%M"
        else:
            fmt = "%Y-%m-%d %H:%M" if year else "%m-%d %H:%M"
        return local.strftime(fmt + (":%S" if seconds else ""))

    def names(self) -> dict[str, str]:
        names: dict[str, str] = {}
        arrivals, doors = self._parsed()
        lang = self.lang
        seen = [(a.person, a.source) for a in arrivals] + [
            (str(d["person"]), str(d["source"])) for d in self.departures
        ]
        for owner, source in seen:
            person = plain_name(self.hass, owner)
            if source == owner:
                names[source] = tr(lang, "hc_overall", person=person)
            elif source.endswith(EARLIEST):
                names[source] = tr(lang, "hc_earliest", person=person)
            else:
                names[source] = f"{person} – {plain_name(self.hass, source)}"
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

    def departure_days(self) -> float:
        """Tage, seit das Weggehen gemessen wird (für die Mindestdauer der Empfehlung)."""
        if self.departure_since is None:
            return 0.0
        return max(0.0, (dt_util.utcnow().timestamp() - self.departure_since) / 86400)

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
            f"{self._when(v.arrival.at, year=False)} " + describe(v, names, self.lang)
            for v in reversed(verdicts)
        ]

    def attributes(self) -> dict[str, Any]:
        names = self.names()
        return {
            "enabled": self.enabled,
            "days": round(self.days(), 1),
            "door_openings": len(self._parsed()[1]),
            "sources": {names.get(k, k): v.as_dict() for k, v in sorted(self.stats().items())},
            "recent": self.recent(),
            "entry_times": {
                display_name(self.hass, door): values
                for door, values in entry_stats(self.entry_timings()).items()
            },
            "door_proof": {
                plain_name(self.hass, person): values
                for person, values in door_proof_advice(self.stats()).items()
            },
            "departure": {
                self._departure_names(names).get(k, k): v.as_dict()
                for k, v in sorted(departure_stats(self.departure_verdicts()).items())
            },
            "departure_days": round(self.departure_days(), 1),
            "leaving_advice": {
                plain_name(self.hass, person): values
                for person, values in self.departure_advice().items()
            },
        }

    def measurements(self) -> dict[str, Any]:
        """Kurzfassung aller Messungen für die Einstellungsseite."""
        stats = self.stats()
        left = departure_stats(self.departure_verdicts())
        advice = self.departure_advice()
        lang = self.lang
        persons = []
        for person in self.persons:
            home = stats.get(person + EARLIEST)
            out = left.get(person + EARLIEST)
            values = advice.get(person)
            name = plain_name(self.hass, person)
            persons.append(
                {
                    "name": name,
                    "arrivals": home.arrivals if home else 0,
                    "arrivals_with_door": home.with_door if home else 0,
                    "left": out.with_door if out else 0,
                    "longest_left": round(max(out.delays)) if out and out.delays else None,
                    "pauses": len(out.pauses) if out else 0,
                    "longest_pause": (round(max(out.pauses) / 60) if out and out.pauses else None),
                    "status": values["status"] if values else "few",
                    "advice": (
                        advice_text(values, name, lang)
                        if values
                        else tr(lang, "dep_status_none", name=name)
                    ),
                }
            )
        return {
            "since": self._when(self.since) if self.since else None,
            "days": round(self.days(), 1),
            "departure_since": self._when(self.departure_since) if self.departure_since else None,
            "departure_days": round(self.departure_days(), 1),
            "doors": len(self._parsed()[1]),
            "persons": persons,
            "entries": [
                {
                    "door": display_name(self.hass, door),
                    "count": values["entries"],
                    "longest": values["max_seconds"],
                    "recommended": values["recommended_entry_delay"],
                }
                for door, values in entry_stats(self.entry_timings()).items()
            ],
        }

    def summary(self) -> int | None:
        if not self.enabled:
            return None
        arrivals, doors = self._parsed()
        return len(judge([a for a in arrivals if a.source == a.person], doors))

    def report_text(self) -> str:
        """Bericht als Markdown (Benachrichtigung und Download)."""
        lang = self.lang
        arrivals, doors = self._parsed()
        overall = frozenset(a.source for a in arrivals if a.source == a.person)
        text = report_markdown(
            self.stats(),
            self.names(),
            door_only=doors_without_arrival(arrivals, doors, sources=overall),
            days=self.days(),
            lang=lang,
        )
        timings = entry_stats(self.entry_timings())
        if timings:
            lines = [
                "\n\n" + tr(lang, "hc_entry_heading") + "\n",
                tr(lang, "hc_entry_cols"),
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
        proof = door_proof_lines(
            door_proof_advice(self.stats()),
            {p: plain_name(self.hass, p) for p in self.persons},
            lang,
        )
        if proof:
            text += "\n\n" + "\n".join(proof)
        verdicts = self.departure_verdicts()
        names = self.names()
        names.update({p: plain_name(self.hass, p) for p in self.persons})
        leaving = departure_lines(
            departure_stats(verdicts),
            wait_advice(verdicts, self.departure_days()),
            self._departure_names(names),
            lang,
        )
        if leaving:
            text += "\n\n" + "\n".join(leaving)
        if not self.enabled:
            text = tr(lang, "hc_off") + "\n\n" + text
        return text

    def export(self) -> dict[str, str]:
        """Bericht (Markdown) und alle Einzelwerte (CSV) zum Herunterladen."""
        now = dt_util.now()
        lang = self.lang
        arrivals, doors = self._parsed()
        names = self.names()
        timings = self.entry_timings()
        for timing in timings:
            names.setdefault(timing.door, display_name(self.hass, timing.door))
        recent = self.recent()
        markdown = (
            f"# {tr(lang, 'hc_heading')}\n\n"
            f"{tr(lang, 'hc_created')}: {self._when(now.timestamp())}\n\n"
            + self.report_text()
            + (
                f"\n\n## {tr(lang, 'hc_recent')}\n\n" + "\n".join(f"- {line}" for line in recent)
                if recent
                else ""
            )
            + "\n"
        )

        def local(at: float) -> str:
            return self._when(at, seconds=True)

        rows = csv_rows(
            judge(arrivals, doors, windows=self._windows(arrivals)),
            timings,
            names,
            local,
            lang,
            extra=departure_csv_rows(
                self.departure_verdicts(), self._departure_names(names), local, lang
            ),
        )
        return {
            "filename": f"{tr(lang, 'hc_filename')}-{now:%Y-%m-%d}",
            "markdown": markdown,
            # Deutsches Excel erwartet Semikolon, englisches Komma
            "csv": to_csv(rows, delimiter=";" if lang == DE else ","),
        }

    @callback
    def create_report(self) -> None:
        text = self.report_text() + "\n\n" + tr(self.lang, "hc_download")
        persistent_notification.async_create(
            self.hass,
            text,
            title=tr(self.lang, "hc_title"),
            notification_id=NOTIFICATION_REPORT,
        )
