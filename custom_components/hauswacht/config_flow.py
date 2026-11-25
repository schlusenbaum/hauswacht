"""Installation von Hauswacht – eingerichtet wird alles auf der Einstellungsseite.

Bis 0.63.1 gab es hier einen großen Einstellungsdialog mit Einrichtungsassistent. Seit 0.63.2
ist die Einstellungsseite (Seitenleiste „Hauswacht“, ADR 0011) der einzige Weg: Die Installation
legt nur den Eintrag an, und „Konfigurieren“ verweist auf die Seite.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback

from .const import DOMAIN, NAME
from .frontend import PANEL_URL_PATH

SETTINGS_URL = f"/{PANEL_URL_PATH}"


class HauswachtConfigFlow(ConfigFlow, domain=DOMAIN):
    """Installation: ein Schritt mit Hinweis auf die Einstellungsseite."""

    VERSION = 5
    MINOR_VERSION = 2  # 5.2: „Bei Rückkehr“ je Profil (ADR 0015)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title=NAME, data={}, options={})
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            description_placeholders={"url": SETTINGS_URL},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return HauswachtOptionsFlow()


class HauswachtOptionsFlow(OptionsFlow):
    """„Konfigurieren“: nur noch ein Wegweiser zur Einstellungsseite (ab 0.63.2)."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self.async_abort(
            reason="use_settings_page", description_placeholders={"url": SETTINGS_URL}
        )
