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
    async_add_entities(
        [
            HauswachtSystemStatusSensor(entry),
            HauswachtHomecomingSensor(entry),
            HauswachtSimulationSensor(entry),
        ]
    )


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


class HauswachtHomecomingSensor(HauswachtEntity, SensorEntity):
    """Heimkehr-Beobachtung: Anzahl ausgewerteter Heimkehrten, Details in den Attributen."""

    _attr_translation_key = "homecoming"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:home-import-outline"

    def __init__(self, entry: HauswachtConfigEntry) -> None:
        super().__init__(entry, "homecoming")

    @property
    def native_value(self) -> int | None:
        return self.runtime.homecoming.summary()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self.runtime.homecoming.attributes()


class HauswachtSimulationSensor(HauswachtEntity, SensorEntity):
    """Testkarte: Anzahl simulierter Sensoren; alle Hauswacht-Sensoren in den Attributen."""

    _attr_translation_key = "simulation"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:test-tube"
    # Die Liste ändert sich mit jedem Sensor – nicht in die Historie schreiben
    _unrecorded_attributes = frozenset({"sensors"})

    def __init__(self, entry: HauswachtConfigEntry) -> None:
        super().__init__(entry, "simulation")

    @property
    def native_value(self) -> int:
        return self.runtime.simulated_count

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "test_mode": self.runtime.ctx.test_mode,
            "sensors": self.runtime.simulation_overview(),
        }
