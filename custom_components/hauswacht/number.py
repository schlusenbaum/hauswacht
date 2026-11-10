"""Zahlen-Einstellungen des bearbeiteten Profils (Verzögerungen, Reaktionszeit, Zyklen)."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .core.profile_settings import NUMBERS, read_number
from .profile_setting_entities import ProfileSettingEntity
from .runtime import HauswachtConfigEntry

ICONS = {
    "exit_delay": "mdi:timer-arrow-right-outline",
    "entry_delay": "mdi:timer-arrow-left-outline",
    "reaction_time": "mdi:timer-alert-outline",
    "max_alarm_cycles": "mdi:repeat",
    "auto_away_delay": "mdi:account-clock-outline",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HauswachtConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities(ProfileNumber(entry, key) for key in NUMBERS)


class ProfileNumber(ProfileSettingEntity, NumberEntity):
    _attr_mode = NumberMode.BOX

    def __init__(self, entry: HauswachtConfigEntry, key: str) -> None:
        super().__init__(entry, key)
        setting = NUMBERS[key]
        self._attr_native_min_value = setting.minimum
        self._attr_native_max_value = setting.maximum
        self._attr_native_step = setting.step
        self._attr_native_unit_of_measurement = setting.unit
        self._attr_icon = ICONS.get(key)

    @property
    def native_value(self) -> int | None:
        if self.runtime.edit_profile is None:
            return None
        return read_number(self.runtime.entry.options, self._profile_id, self._key)

    async def async_set_native_value(self, value: float) -> None:
        await self.runtime.async_set_profile_setting(self._key, int(value))
