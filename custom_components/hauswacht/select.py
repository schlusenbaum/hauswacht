"""Auswahlliste "Profil": wählt das Profil, das die Knöpfe "Scharf schalten" verwenden.

Im scharfen Zustand zeigt sie das aktive Profil und lässt sich nicht ändern.
"""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .core.profiles import profile_infos
from .entity import HauswachtEntity
from .runtime import HauswachtConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HauswachtConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([HauswachtProfileSelect(entry)])


class HauswachtProfileSelect(HauswachtEntity, SelectEntity):
    _attr_translation_key = "profile"

    def __init__(self, entry: HauswachtConfigEntry) -> None:
        super().__init__(entry, "profile")
        self._attr_options = [info.name for info in profile_infos(entry.options)]

    @property
    def current_option(self) -> str | None:
        profile_id = self.runtime.selected_profile
        return self.runtime.profile_name(profile_id) if profile_id else None

    @property
    def icon(self) -> str | None:
        profile_id = self.runtime.selected_profile
        if profile_id is None:
            return None
        return next(
            (
                i.icon
                for i in profile_infos(self.runtime.entry.options)
                if i.profile_id == profile_id
            ),
            None,
        )

    async def async_select_option(self, option: str) -> None:
        self.runtime.select_profile(option)
