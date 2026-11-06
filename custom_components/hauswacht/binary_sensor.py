"""Binärsensor "Offene Sensoren": an, sobald ein Sensor einer Hauswacht-Zone offen ist.

Damit lassen sich Dashboard-Karten (z. B. "Trotzdem scharf schalten") und Automationen
ohne Vorlagen ein- und ausblenden.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import HauswachtEntity
from .names import display_name
from .runtime import HauswachtConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HauswachtConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([HauswachtOpenSensorsBinarySensor(entry)])


class HauswachtOpenSensorsBinarySensor(HauswachtEntity, BinarySensorEntity):
    _attr_translation_key = "open_sensors"
    _attr_device_class = BinarySensorDeviceClass.OPENING

    def __init__(self, entry: HauswachtConfigEntry) -> None:
        super().__init__(entry, "open_sensors")

    def _open(self) -> list[str]:
        readiness = self.runtime.readiness_for(self.runtime.candidates)
        return sorted(readiness.open_sensors)

    @property
    def is_on(self) -> bool:
        return bool(self._open())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        open_sensors = self._open()
        return {
            "sensors": open_sensors,
            "names": [display_name(self.hass, entity_id) for entity_id in open_sensors],
        }
