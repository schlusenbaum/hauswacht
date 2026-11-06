"""Anzeigenamen für Meldungen und Attribute."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er


def display_name(hass: HomeAssistant, entity_id: str) -> str:
    """Anzeigename mit Raum, z. B. "Küche: Fensterkontakt links"."""
    state = hass.states.get(entity_id)
    name = state.name if state else entity_id
    entry = er.async_get(hass).async_get(entity_id)
    area_id = entry.area_id if entry else None
    if entry and area_id is None and entry.device_id:
        device = dr.async_get(hass).async_get(entry.device_id)
        area_id = device.area_id if device else None
    area = ar.async_get(hass).async_get_area(area_id) if area_id else None
    if area is None or area.name.casefold() in name.casefold():
        return name
    return f"{area.name}: {name}"


def plain_name(hass: HomeAssistant, entity_id: str) -> str:
    state = hass.states.get(entity_id)
    return state.name if state else entity_id
