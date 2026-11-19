"""Aktion ``hauswacht.keypad_input`` – Eingang für allgemeine Keypads (ADR 0012).

Ein Übersetzer (Blueprint, Automation, ESPHome-Gerät, Node-RED) meldet Taste und Ausweis eines
Keypads, das Hauswacht nicht selbst kennt. Hauswacht wertet die Eingabe mit dem Keypad-Kern aus
und antwortet (Antwortdaten der Aktion).

Aufrufen dürfen nur Automationen und Skripte (ohne Benutzer) und Administratoren – sonst könnte
jeder angemeldete Benutzer z. B. einen Notruf ohne PIN auslösen.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import ServiceValidationError, Unauthorized
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN

if TYPE_CHECKING:
    from .controls import ControlManager

SERVICE_KEYPAD_INPUT = "keypad_input"

KEYPAD_INPUT_SCHEMA = vol.Schema(
    {
        vol.Required("keypad"): cv.string,
        vol.Optional("button", default=""): vol.Any(None, cv.string),
        vol.Optional("code"): vol.Any(None, cv.string),
        vol.Optional("force", default=False): cv.boolean,
    }
)


def _controls(hass: HomeAssistant) -> ControlManager:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED and entry.runtime_data.controls is not None:
            controls: ControlManager = entry.runtime_data.controls
            return controls
    raise ServiceValidationError(translation_domain=DOMAIN, translation_key="not_loaded")


async def _check_caller(hass: HomeAssistant, call: ServiceCall) -> None:
    """Nur Automationen/Skripte (kein Benutzer) und Administratoren."""
    user_id = call.context.user_id
    if user_id is None:
        return
    user = await hass.auth.async_get_user(user_id)
    if user is None or not (user.is_admin or user.system_generated):
        raise Unauthorized(context=call.context)


def async_register_keypad_service(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_KEYPAD_INPUT):
        return

    async def handle(call: ServiceCall) -> ServiceResponse:
        await _check_caller(hass, call)
        data: dict[str, Any] = dict(call.data)
        code = data.get("code")
        response = await _controls(hass).async_generic_input(
            str(data["keypad"]).strip(),
            str(data.get("button") or ""),
            str(code) if code not in (None, "") else None,
            force=bool(data.get("force")),
        )
        return response

    hass.services.async_register(
        DOMAIN,
        SERVICE_KEYPAD_INPUT,
        handle,
        schema=KEYPAD_INPUT_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
