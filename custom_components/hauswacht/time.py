"""Uhrzeit-Einstellungen des bearbeiteten Profils (automatisch scharf/unscharf)."""

from __future__ import annotations

from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .core.profile_settings import TIMES, read_time
from .profile_setting_entities import ProfileSettingEntity
from .runtime import HauswachtConfigEntry

ICONS = {"auto_arm_time": "mdi:clock-start", "auto_disarm_time": "mdi:clock-end"}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HauswachtConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities(ProfileTime(entry, key) for key in TIMES)


class ProfileTime(ProfileSettingEntity, TimeEntity):
    """Leer (unbekannt) = keine Automatik nach Uhrzeit. Eine Uhrzeit entfernen geht nur in der
    Integration (Home Assistant kann eine Uhrzeit-Entität nicht leeren)."""

    def __init__(self, entry: HauswachtConfigEntry, key: str) -> None:
        super().__init__(entry, key)
        self._attr_icon = ICONS.get(key)

    @property
    def native_value(self) -> time | None:
        if self.runtime.edit_profile is None:
            return None
        return read_time(self.runtime.entry.options, self._profile_id, self._key)

    async def async_set_value(self, value: time) -> None:
        await self.runtime.async_set_profile_setting(self._key, value)
