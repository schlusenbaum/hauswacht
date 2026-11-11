"""Gemeinsame Basis für Hauswacht-Entitäten."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, NAME
from .runtime import HauswachtConfigEntry, HauswachtRuntime

DOCS_URL = "https://github.com/schlusenbaum/hauswacht/blob/main/docs/installation.md"


class HauswachtEntity(Entity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry: HauswachtConfigEntry, key: str) -> None:
        self.runtime: HauswachtRuntime = entry.runtime_data
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=NAME,
            manufacturer="Hauswacht",
            model="Einbruchmeldeanlage",
            entry_type=DeviceEntryType.SERVICE,
            # Auf der Geräteseite: Link zur Anleitung (erklärt alle Entitäten)
            configuration_url=DOCS_URL,
        )

    def _keep_object_id(self, german: str, english: str) -> None:
        """Bisherige Entitäts-ID behalten, auch wenn der Anzeigename länger geworden ist."""
        language = (self.runtime.hass.config.language or "").split("-")[0]
        self.entity_id = f"{self._platform_domain}.{german if language == 'de' else english}"

    _platform_domain = ""

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self.runtime.add_listener(self.async_write_ha_state))
