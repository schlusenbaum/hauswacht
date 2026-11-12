"""Funkstille-Beobachtung: misst die längste Pause zwischen Lebenszeichen je Melder.

Schaltet nichts und ruft keine Dienste auf. Gehört zum Hauptbereich und beobachtet die Melder
aller Bereiche. Die Auswertung steckt in core/silence.py.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .core.silence import SilenceRecord, advice, dump, format_duration, load, update
from .names import display_name

if TYPE_CHECKING:
    from .runtime import HauswachtRuntime

STORAGE_VERSION = 1
SAMPLE_INTERVAL = timedelta(minutes=1)


class SilenceObserver:
    def __init__(self, hass: HomeAssistant, runtime: HauswachtRuntime) -> None:
        self.hass = hass
        self.runtime = runtime
        self.records: dict[str, SilenceRecord] = {}
        self.since: float | None = None
        self._previous: dict[str, float] = {}
        self._baseline: set[str] = set()
        self._unsub: CALLBACK_TYPE | None = None
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{runtime.entry.entry_id}.silence"
        )

    async def async_start(self) -> None:
        data = await self._store.async_load() or {}
        self.records = load(data.get("records"))
        since = data.get("since")
        self.since = float(since) if since else dt_util.utcnow().timestamp()
        self.sample()
        self._unsub = async_track_time_interval(
            self.hass, self._tick, SAMPLE_INTERVAL, name="hauswacht_silence"
        )

    @callback
    def async_stop(self) -> None:
        if self._unsub is not None:
            self._unsub()
            self._unsub = None

    @callback
    def _tick(self, _now: datetime) -> None:
        self.sample()

    def _contacts(self) -> dict[str, float]:
        contacts: dict[str, float] = {}
        for area in self.runtime.areas.values():
            for entity_id, snapshot in area.snapshots(area.candidates).items():
                if snapshot.last_contact is not None:
                    contacts[entity_id] = snapshot.last_contact
        return contacts

    @callback
    def sample(self) -> None:
        """Kontakte lesen; neue Kontakte verlängern ggf. die längste Pause."""
        changed = False
        for entity_id, contact in self._contacts().items():
            previous = self._previous.get(entity_id)
            if previous is not None and contact == previous:
                continue
            first = entity_id not in self._baseline
            self._baseline.add(entity_id)
            record = self.records.get(entity_id, SilenceRecord())
            new = update(record, previous, contact, baseline=first)
            self._previous[entity_id] = contact
            if new.longest != record.longest:
                changed = True
            self.records[entity_id] = new
        if changed:
            self._store.async_delay_save(
                lambda: {"records": dump(self.records), "since": self.since}, 30
            )

    def days(self) -> float:
        if self.since is None:
            return 0.0
        return max(0.0, (dt_util.utcnow().timestamp() - self.since) / 86400)

    def advice_hours(self) -> int | None:
        return advice(self.records, self.days())

    def longest(self) -> tuple[str, SilenceRecord] | None:
        if not self.records:
            return None
        return max(self.records.items(), key=lambda item: item[1].longest)

    def summary_text(self, german: bool = True) -> str:
        """Kurzfassung für den Einstellungsdialog."""
        days = self.days()
        longest = self.longest()
        if longest is None or longest[1].longest <= 0:
            return (
                f"Beobachtet seit {days:.1f} Tagen – noch keine Pause gemessen."
                if german
                else f"Observed for {days:.1f} days – no pause measured yet."
            )
        name = display_name(self.hass, longest[0])
        pause = format_duration(longest[1].longest)
        hours = self.advice_hours()
        if german:
            text = f"Beobachtet seit {days:.1f} Tagen. Längste Pause: {name} {pause}."
            return text + (
                f" **Empfehlung: {hours} h.**" if hours else " Empfehlung ab 3 Tagen Beobachtung."
            )
        text = f"Observed for {days:.1f} days. Longest pause: {name} {pause}."
        return text + (
            f" **Recommendation: {hours} h.**" if hours else " Recommendation after 3 days."
        )

    def attributes(self) -> dict[str, Any]:
        return {
            "days": round(self.days(), 1),
            "recommended_hours": self.advice_hours(),
            "sensors": {
                display_name(self.hass, entity_id): {
                    "longest_pause": format_duration(record.longest),
                    "longest_pause_s": round(record.longest),
                    "contacts": record.contacts,
                }
                for entity_id, record in sorted(
                    self.records.items(), key=lambda item: -item[1].longest
                )
            },
        }
