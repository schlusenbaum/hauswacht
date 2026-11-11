"""Gemeinsame Basis für Hauswacht-Entitäten."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.util import slugify

from .const import DOMAIN, NAME
from .core.areas import MAIN_AREA
from .runtime import HauswachtConfigEntry, HauswachtRuntime

DOCS_URL = "https://github.com/schlusenbaum/hauswacht/blob/main/docs/installation.md"


class HauswachtEntity(Entity):
    """Basis: gehört zum Hauptbereich oder – mit ``runtime`` – zu einem weiteren Bereich.

    Entitäten des Hauptbereichs behalten ihre bisherigen IDs. Jeder weitere Bereich bekommt ein
    eigenes Gerät "Hauswacht <Bereich>", das über das Hauswacht-Gerät angebunden ist.
    """

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self, entry: HauswachtConfigEntry, key: str, runtime: HauswachtRuntime | None = None
    ) -> None:
        self.runtime: HauswachtRuntime = runtime or entry.runtime_data
        area_id = self.runtime.area_id
        if area_id == MAIN_AREA:
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
        else:
            self._attr_unique_id = f"{entry.entry_id}_{area_id}_{key}"
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, f"{entry.entry_id}_{area_id}")},
                name=f"{NAME} {self.runtime.area_name}",
                manufacturer="Hauswacht",
                model="Bereich",
                entry_type=DeviceEntryType.SERVICE,
                via_device=(DOMAIN, entry.entry_id),
                configuration_url=DOCS_URL,
            )

    def _keep_object_id(self, german: str, english: str) -> None:
        """Bisherige Entitäts-ID behalten, auch wenn der Anzeigename länger geworden ist.

        In weiteren Bereichen kommt der Bereichsname hinter "hauswacht" dazu.
        """
        language = (self.runtime.hass.config.language or "").split("-")[0]
        object_id = german if language == "de" else english
        if self.runtime.area_id != MAIN_AREA:
            area = slugify(self.runtime.area_name) or self.runtime.area_id
            object_id = object_id.replace("hauswacht", f"hauswacht_{area}", 1)
        self.entity_id = f"{self._platform_domain}.{object_id}"

    _platform_domain = ""

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self.runtime.add_listener(self.async_write_ha_state))
