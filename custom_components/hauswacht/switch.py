"""Testmodus-Schalter.

Der Testmodus lässt sich nur im unscharfen Zustand umschalten (Regel Z3).
Er bleibt über Neustarts erhalten.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import HauswachtEntity
from .runtime import HauswachtConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HauswachtConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([HauswachtTestModeSwitch(entry)])


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
