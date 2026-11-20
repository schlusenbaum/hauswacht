"""Reparaturen, die du in Home Assistant selbst bestätigst.

Code-Entität der Keypads (Zigbee2MQTT): Sie speichert jede am Keypad getippte PIN im Verlauf.
Die Entität gehört der MQTT-Integration – Hauswacht schaltet sie deshalb **nicht** selbst ab,
sondern erst, wenn du es hier bestätigst (Einstellungen → Reparaturen).
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components.repairs import RepairsFlow
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, ISSUE_CODE_ENTITIES


class CodeEntitiesRepairFlow(RepairsFlow):
    """Bestätigen: Code-Entitäten deaktivieren."""

    def __init__(self, entities: list[str]) -> None:
        self._entities = entities

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            registry = er.async_get(self.hass)
            disabled: list[str] = []
            for entity_id in self._entities:
                entry = registry.async_get(entity_id)
                if entry is not None and entry.disabled_by is None:
                    # Du hast es bestätigt – deshalb "vom Benutzer deaktiviert"
                    registry.async_update_entity(
                        entity_id, disabled_by=er.RegistryEntryDisabler.USER
                    )
                    disabled.append(entity_id)
            await _remember(self.hass, self._entities)
            return self.async_create_entry(data={"disabled": disabled})
        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
            description_placeholders={"entities": "\n".join(f"- `{e}`" for e in self._entities)},
        )


async def _remember(hass: HomeAssistant, entities: list[str]) -> None:
    """Gemerkt: nicht noch einmal fragen, auch wenn du eine später wieder einschaltest."""
    for entry in hass.config_entries.async_loaded_entries(DOMAIN):
        main = entry.runtime_data
        main.code_entities_hidden.extend(e for e in entities if e not in main.code_entities_hidden)
        await main.async_save_now()


async def async_create_fix_flow(
    hass: HomeAssistant, issue_id: str, data: dict[str, str | int | float | None] | None
) -> RepairsFlow:
    """Von Home Assistant aufgerufen, wenn du bei einer Hauswacht-Reparatur auf „Beheben“ tippst."""
    if issue_id == ISSUE_CODE_ENTITIES and data is not None:
        entities = [e for e in str(data.get("entities") or "").split(",") if e]
        return CodeEntitiesRepairFlow(entities)
    raise ValueError(f"Unbekannte Reparatur: {issue_id}")
