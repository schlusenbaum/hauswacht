"""Systemstatus von Hauswacht: ok, einzelne Sensoren ausgefallen oder Infrastruktur gestört."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .core.infrastructure import SystemStatus
from .entity import HauswachtEntity
from .runtime import HauswachtConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HauswachtConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([HauswachtSystemStatusSensor(entry)])


class HauswachtSystemStatusSensor(HauswachtEntity, SensorEntity):
    _attr_translation_key = "system_status"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry: HauswachtConfigEntry) -> None:
        super().__init__(entry, "system_status")
        self._attr_options = [s.value for s in SystemStatus]

    @property
    def native_value(self) -> str:
        return self.runtime.system_report().status.value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        report = self.runtime.system_report()
        return {
            "faulty_infrastructure": sorted(report.faulty_infrastructure),
            "unavailable_sensors": sorted(report.unavailable_sensors),
            "monitored_infrastructure": sorted(self.runtime.infrastructure),
        }
