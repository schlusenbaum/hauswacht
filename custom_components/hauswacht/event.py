"""Ereignis-Entität "Aktions-Code": für eigene Automationen.

Wird an einem Keypad ein Aktions-Code mit der Aktion "Ereignis" eingegeben (z. B. "7777 + Haus"),
löst diese Entität ein Ereignis aus. Der Ereignistyp ist der Name des Aktions-Codes, z. B.
"Außenlicht". In einer Automation: Auslöser "Entität → Hauswacht Aktions-Code", Ereignistyp
wählen – was dann passiert, bestimmt die Automation. Hauswacht selbst schaltet dabei nichts.

Die Entität gibt es nur, wenn mindestens ein Aktions-Code mit der Aktion "Ereignis" eingerichtet
ist.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.event import EventEntity
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import EVENT_HAUSWACHT
from .core.action_codes import CodeAction, parse_action_codes
from .entity import HauswachtEntity
from .runtime import HauswachtConfigEntry

EVENT_TYPE_ACTION_CODE = "ActionCode"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HauswachtConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    names = sorted(
        {c.name for c in parse_action_codes(entry.options) if c.action is CodeAction.EVENT}
    )
    if names:
        async_add_entities([ActionCodeEvent(entry, names)])


class ActionCodeEvent(HauswachtEntity, EventEntity):
    _attr_translation_key = "action_code"
    _attr_icon = "mdi:dialpad"

    def __init__(self, entry: HauswachtConfigEntry, names: list[str]) -> None:
        super().__init__(entry, "action_code")
        self._attr_event_types = names
        self._keep_object_id("hauswacht_aktions_code", "hauswacht_action_code")

    _platform_domain = "event"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self.hass.bus.async_listen(EVENT_HAUSWACHT, self._on_event))

    @callback
    def _on_event(self, event: Event[Any]) -> None:
        data = event.data
        if data.get("type") != EVENT_TYPE_ACTION_CODE or data.get("action") != CodeAction.EVENT:
            return
        name = data.get("name")
        if name not in self.event_types:
            return
        self._trigger_event(
            str(name), {"keypad": data.get("control"), "test": bool(data.get("test"))}
        )
        self.async_write_ha_state()
