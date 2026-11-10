"""Auswahllisten.

- "Profil": wählt das Profil, das die Knöpfe "Scharf schalten" verwenden.
- "Profil bearbeiten": wählt das Profil, dessen Einstellungen die Einstellungs-Entitäten zeigen.
- Auswahl-Einstellungen des bearbeiteten Profils (Verhalten, Sirenenton, Lautstärke).

Im scharfen Zustand zeigt sie das aktive Profil und lässt sich nicht ändern.
"""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .core.profile_settings import SELECTS, read_select
from .core.profiles import profile_infos
from .entity import HauswachtEntity
from .profile_setting_entities import ProfileSettingEntity
from .runtime import HauswachtConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HauswachtConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities(
        [
            HauswachtProfileSelect(entry),
            HauswachtEditProfileSelect(entry),
            *(ProfileSelect(entry, key) for key in SELECTS),
        ]
    )


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


class HauswachtEditProfileSelect(HauswachtEntity, SelectEntity):
    """Welches Profil die Einstellungs-Entitäten zeigen und ändern."""

    _attr_translation_key = "edit_profile"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:playlist-edit"

    def __init__(self, entry: HauswachtConfigEntry) -> None:
        super().__init__(entry, "edit_profile")
        self._attr_options = [info.name for info in profile_infos(entry.options)]

    @property
    def current_option(self) -> str | None:
        profile_id = self.runtime.edit_profile
        return self.runtime.profile_name(profile_id) if profile_id else None

    async def async_select_option(self, option: str) -> None:
        self.runtime.select_edit_profile(option)


SELECT_ICONS = {
    "open_policy": "mdi:window-open-variant",
    "unavailable_policy": "mdi:lan-disconnect",
    "siren_tone": "mdi:bullhorn-outline",
    "siren_volume": "mdi:volume-high",
}


class ProfileSelect(ProfileSettingEntity, SelectEntity):
    def __init__(self, entry: HauswachtConfigEntry, key: str) -> None:
        super().__init__(entry, key)
        self._attr_options = list(SELECTS[key].options)
        self._attr_icon = SELECT_ICONS.get(key)

    @property
    def current_option(self) -> str | None:
        if self.runtime.edit_profile is None:
            return None
        return read_select(self.runtime.entry.options, self._profile_id, self._key)

    async def async_select_option(self, option: str) -> None:
        await self.runtime.async_set_profile_setting(self._key, option)
