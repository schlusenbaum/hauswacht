"""Ortungen einer Person aus Home Assistant lesen – für „weg“ nur mit Beleg (ADR 0015).

Die Regeln selbst stehen in ``core/away_proof.py``; hier nur das Lesen der Zustände.
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant, State

from .core.away_proof import Fix, Home, is_locator, locate


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
    hass: HomeAssistant, person: str, signals: tuple[str, ...], accuracy: str
) -> list[Fix]:
    home = home_zone(hass)
    fixes: list[Fix] = []
    for entity_id in _candidates(hass, person, signals):
        state = hass.states.get(entity_id)
        if state is None:
            continue
        fix = locate(state.state, state.attributes, _updated(state), home=home, accuracy=accuracy)
        if fix is not None:
            fixes.append(fix)
    return fixes


def locatable(hass: HomeAssistant, person: str, signals: tuple[str, ...]) -> bool:
    """Kann die Person überhaupt außerhalb geortet werden (eine Entität mit Koordinaten)?"""
    return any(
        (state := hass.states.get(entity_id)) is not None and is_locator(state.attributes)
        for entity_id in _candidates(hass, person, signals)
    )
