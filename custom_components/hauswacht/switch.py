"""Testmodus-Schalter und Schalter-Einstellungen des bearbeiteten Profils.

Der Testmodus lässt sich nur im unscharfen Zustand umschalten (Regel Z3).
Er bleibt über Neustarts erhalten.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .core.profile_settings import SWITCHES, read_switch
from .core.tilt import parse_tilt_sources
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
            HauswachtTestModeSwitch(entry),
            HauswachtGuestModeSwitch(entry),
            *(
                ProfileSwitch(entry, key)
                for key in SWITCHES
                # "Gekippte Fenster erlaubt" nur, wenn es Melder mit Kippstellung gibt
                if key != "tilt_allowed" or parse_tilt_sources(entry.options)
            ),
        ]
    )


class HauswachtTestModeSwitch(HauswachtEntity, SwitchEntity):
    _attr_translation_key = "test_mode"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry: HauswachtConfigEntry) -> None:
        super().__init__(entry, "test_mode")

    @property
    def is_on(self) -> bool:
        return self.runtime.ctx.test_mode

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.runtime.set_test_mode(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.runtime.set_test_mode(False)


class HauswachtGuestModeSwitch(HauswachtEntity, SwitchEntity):
    """Gastmodus für alle Bereiche: an = keine automatische Scharfschaltung (bis zum Ausschalten).

    Mit Ende-Zeitpunkt oder für einzelne Bereiche: Aktion ``hauswacht.guest_mode`` oder die
    Alarm-Karte.
    """

    _attr_translation_key = "guest_mode"
    _attr_icon = "mdi:account-group"
    _platform_domain = "switch"

    def __init__(self, entry: HauswachtConfigEntry) -> None:
        super().__init__(entry, "guest_mode")
        self._keep_object_id("hauswacht_gastmodus", "hauswacht_guest_mode")

    @property
    def is_on(self) -> bool:
        return any(a.guest_active for a in self.runtime.areas.values())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "areas": {
                a.area_id: (ends.isoformat() if (ends := a.guest_ends_at) else "off")
                for a in self.runtime.areas.values()
                if a.guest_active
            }
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        by = await self.runtime.async_user_label(self._user_id)
        for area in self.runtime.areas.values():
            area.set_guest_mode(True, by=by)

    async def async_turn_off(self, **kwargs: Any) -> None:
        by = await self.runtime.async_user_label(self._user_id)
        for area in self.runtime.areas.values():
            area.set_guest_mode(False, by=by)

    @property
    def _user_id(self) -> str | None:
        return self._context.user_id if self._context else None


SWITCH_ICONS = {
    "silent": "mdi:volume-off",
    "tamper_triggers_alarm": "mdi:shield-alert-outline",
    "tilt_allowed": "mdi:window-open-variant",
}


class ProfileSwitch(ProfileSettingEntity, SwitchEntity):
    def __init__(self, entry: HauswachtConfigEntry, key: str) -> None:
        super().__init__(entry, key)
        self._attr_icon = SWITCH_ICONS.get(key)

    @property
    def is_on(self) -> bool | None:
        if self.runtime.edit_profile is None:
            return None
        return read_switch(self.runtime.entry.options, self._profile_id, self._key)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.runtime.async_set_profile_setting(self._key, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.runtime.async_set_profile_setting(self._key, False)
