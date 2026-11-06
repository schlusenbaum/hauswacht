"""Einrichtung und Optionen von Hauswacht."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigEntryState,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import DOMAIN, NAME, OPT_CODE_ARM_REQUIRED, OPT_PIN_DIGEST, OPT_PIN_SALT, OPT_PROFILES
from .core.pin import hash_pin, is_valid_pin_format
from .core.profiles import MAX_DELAY, MAX_REACTION_TIME, PROFILE_IDS, profile_settings
from .core.state_machine import AlarmState


class HauswachtConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title=NAME, data={}, options={})
        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return HauswachtOptionsFlow()


def _seconds(maximum: int, minimum: int = 0) -> NumberSelector:
    return NumberSelector(
        NumberSelectorConfig(
            min=minimum,
            max=maximum,
            step=1,
            unit_of_measurement="s",
            mode=NumberSelectorMode.BOX,
        )
    )


class HauswachtOptionsFlow(OptionsFlow):
    """Optionen: PIN und Profilzeiten. Nur im unscharfen Zustand änderbar."""

    def __init__(self) -> None:
        self._profile_id: str | None = None

    def _is_disarmed(self) -> bool:
        entry = self.config_entry
        if entry.state is not ConfigEntryState.LOADED:
            return True
        return bool(entry.runtime_data.ctx.state is AlarmState.DISARMED)

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if not self._is_disarmed():
            return self.async_abort(reason="disarm_first")
        return self.async_show_menu(step_id="init", menu_options=["code", "profile"])

    async def async_step_code(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        options = dict(self.config_entry.options)
        errors: dict[str, str] = {}
        if user_input is not None:
            new_pin = str(user_input.get("new_pin") or "").strip()
            if user_input.get("remove_pin"):
                options.pop(OPT_PIN_SALT, None)
                options.pop(OPT_PIN_DIGEST, None)
            elif new_pin:
                if not is_valid_pin_format(new_pin):
                    errors["new_pin"] = "invalid_pin"
                else:
                    stored = hash_pin(new_pin)
                    options[OPT_PIN_SALT] = stored.salt
                    options[OPT_PIN_DIGEST] = stored.digest
            options[OPT_CODE_ARM_REQUIRED] = bool(user_input.get(OPT_CODE_ARM_REQUIRED, False))
            if not errors:
                return self.async_create_entry(data=options)

        has_pin = bool(options.get(OPT_PIN_DIGEST))
        schema = vol.Schema(
            {
                vol.Optional("new_pin"): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
                vol.Optional("remove_pin", default=False): BooleanSelector(),
                vol.Optional(
                    OPT_CODE_ARM_REQUIRED,
                    default=bool(options.get(OPT_CODE_ARM_REQUIRED, False)),
                ): BooleanSelector(),
            }
        )
        return self.async_show_form(
            step_id="code",
            data_schema=schema,
            errors=errors,
            description_placeholders={"pin_status": "●●●●" if has_pin else "–"},
        )

    async def async_step_profile(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._profile_id = user_input["profile"]
            return await self.async_step_profile_settings()
        schema = vol.Schema(
            {
                vol.Required("profile"): SelectSelector(
                    SelectSelectorConfig(
                        options=list(PROFILE_IDS),
                        translation_key="profile",
                        mode=SelectSelectorMode.LIST,
                    )
                )
            }
        )
        return self.async_show_form(step_id="profile", data_schema=schema)

    async def async_step_profile_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        assert self._profile_id is not None
        options = dict(self.config_entry.options)
        if user_input is not None and "exit_delay" in user_input:
            profiles = {k: dict(v) for k, v in options.get(OPT_PROFILES, {}).items()}
            profiles[self._profile_id] = {
                "exit_delay": int(user_input["exit_delay"]),
                "entry_delay": int(user_input["entry_delay"]),
                "reaction_time": int(user_input["reaction_time"]),
            }
            options[OPT_PROFILES] = profiles
            return self.async_create_entry(data=options)

        current = profile_settings(options, self._profile_id)
        schema = vol.Schema(
            {
                vol.Required("exit_delay", default=current["exit_delay"]): _seconds(MAX_DELAY),
                vol.Required("entry_delay", default=current["entry_delay"]): _seconds(MAX_DELAY),
                vol.Required("reaction_time", default=current["reaction_time"]): _seconds(
                    MAX_REACTION_TIME, minimum=1
                ),
            }
        )
        return self.async_show_form(
            step_id="profile_settings",
            data_schema=schema,
            description_placeholders={"profile": self._profile_id},
        )
