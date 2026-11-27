"""Ortungen einer Person aus Home Assistant lesen – für „weg“ nur mit Beleg (ADR 0015).

Die Regeln selbst stehen in ``core/away_proof.py``; hier nur das Lesen der Zustände.

Seit 0.64.0b5: Eine Ortung, die seit mindestens 24 Stunden exakt dieselbe Position **außerhalb**
von Zuhause meldet, gilt als eingefroren (vorgetäuschter Standort, hängende App). Sie zählt dann
weder als Beleg noch als „kann geortet werden“. Wann sich die Koordinaten zuletzt geändert haben,
merkt sich Hauswacht (auch über einen Neustart hinweg).
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.storage import Store

from .const import DOMAIN
from .core.away_proof import Fix, FrozenLocations, Home, geofence_fix, is_locator, locate

_LOGGER = logging.getLogger(__name__)
DATA_FROZEN = f"{DOMAIN}_frozen_locations"
STORE_KEY = f"{DOMAIN}.frozen_locations"
STORE_VERSION = 1
SAVE_DELAY = 60  # Sekunden


class FrozenStore:
    """``FrozenLocations`` mit Speicher in Home Assistant."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.data = FrozenLocations()
        self._store: Store[dict[str, Any]] = Store(hass, STORE_VERSION, STORE_KEY)

    async def async_load(self) -> None:
        stored = await self._store.async_load()
        if stored:
            self.data.load(stored.get("seen"))

    def note(self, entity_id: str, state: State) -> None:
        lat, lon = state.attributes.get("latitude"), state.attributes.get("longitude")
        if not isinstance(lat, int | float) or not isinstance(lon, int | float):
            return
        if self.data.see(entity_id, float(lat), float(lon), _updated(state)):
            self._store.async_delay_save(lambda: {"seen": self.data.dump()}, SAVE_DELAY)

    def frozen_for(self, entity_id: str, state: State) -> float | None:
        """Eingefroren (Sekunden) – nur außerhalb von Zuhause; zuhause zählt eine Ortung nie."""
        self.note(entity_id, state)
        if state.state == "home":
            return None
        return self.data.frozen_for(entity_id, _updated(state))


async def async_load_frozen(hass: HomeAssistant) -> None:
    """Beim Start einmal laden (mehrere Einträge/Bereiche teilen sich den Stand)."""
    if DATA_FROZEN in hass.data:
        return
    store = FrozenStore(hass)
    hass.data[DATA_FROZEN] = store
    try:
        await store.async_load()
    except (OSError, ValueError) as err:  # pragma: no cover - nur Protokoll
        _LOGGER.warning("Gespeicherte Ortungen nicht lesbar: %s", err)


def _frozen(hass: HomeAssistant, entity_id: str, state: State) -> bool:
    store: FrozenStore | None = hass.data.get(DATA_FROZEN)
    return store is not None and store.frozen_for(entity_id, state) is not None


def frozen_locations(
    hass: HomeAssistant, person: str, signals: tuple[str, ...]
) -> dict[str, float]:
    """Eingefrorene Ortungen einer Person: Entität -> seit wie vielen Sekunden."""
    store: FrozenStore | None = hass.data.get(DATA_FROZEN)
    if store is None:
        return {}
    found: dict[str, float] = {}
    for entity_id in _candidates(hass, person, signals):
        state = hass.states.get(entity_id)
        if state is None or not is_locator(state.attributes):
            continue
        seconds = store.frozen_for(entity_id, state)
        if seconds is not None:
            found[entity_id] = seconds
    return found


def home_zone(hass: HomeAssistant) -> Home | None:
    """Zone „Zuhause“ (Mittelpunkt und Radius); ohne Zone die Koordinaten von Home Assistant."""
    state = hass.states.get("zone.home")
    if state is not None:
        lat, lon = state.attributes.get("latitude"), state.attributes.get("longitude")
        radius = state.attributes.get("radius", 100)
        if isinstance(lat, int | float) and isinstance(lon, int | float):
            return Home(float(lat), float(lon), float(radius or 100))
    if hass.config.latitude is None or hass.config.longitude is None:
        return None
    return Home(float(hass.config.latitude), float(hass.config.longitude), 100.0)


def _candidates(hass: HomeAssistant, person: str, signals: tuple[str, ...]) -> list[str]:
    """Die Person selbst, ihre Geräte-Tracker und die Zusatzsignale (ohne Doppelte)."""
    found = [person]
    state = hass.states.get(person)
    trackers = state.attributes.get("device_trackers", []) if state is not None else []
    if isinstance(trackers, list):
        found.extend(t for t in trackers if isinstance(t, str))
    found.extend(signals)
    return list(dict.fromkeys(found))


def _updated(state: State) -> float:
    """Letzte Meldung – auch eine unveränderte (``last_reported``) zählt als frisch."""
    times = [state.last_updated.timestamp()]
    reported = getattr(state, "last_reported", None)
    if reported is not None:
        times.append(reported.timestamp())
    return max(times)


def person_fixes(
    hass: HomeAssistant,
    person: str,
    signals: tuple[str, ...],
    accuracy: str,
    geofence: frozenset[str] = frozenset(),
) -> list[Fix]:
    """Ortungen der Person – mit Koordinaten oder als Geofence markiert (ADR 0018)."""
    home = home_zone(hass)
    fixes: list[Fix] = []
    for entity_id in _candidates(hass, person, signals):
        state = hass.states.get(entity_id)
        if state is None:
            continue
        if entity_id in geofence and not is_locator(state.attributes):
            fix = geofence_fix(state.state, _updated(state))
        elif is_locator(state.attributes) and _frozen(hass, entity_id, state):
            continue
        else:
            fix = locate(
                state.state, state.attributes, _updated(state), home=home, accuracy=accuracy
            )
        if fix is not None:
            fixes.append(fix)
    return fixes


def locatable(
    hass: HomeAssistant,
    person: str,
    signals: tuple[str, ...],
    geofence: frozenset[str] = frozenset(),
) -> bool:
    """Kann die Person außerhalb geortet werden (Koordinaten oder Geofence, ADR 0018)?"""
    for entity_id in _candidates(hass, person, signals):
        state = hass.states.get(entity_id)
        if state is None:
            continue
        if entity_id in geofence:
            return True
        if is_locator(state.attributes) and not _frozen(hass, entity_id, state):
            return True
    return False
