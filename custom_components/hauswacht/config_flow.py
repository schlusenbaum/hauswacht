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
    EntitySelector,
    EntitySelectorConfig,
    LabelSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    DOMAIN,
    NAME,
    OPT_CODE_ARM_REQUIRED,
    OPT_PIN_DIGEST,
    OPT_PIN_SALT,
    OPT_PROFILES,
    OPT_SENSOR_ROLES,
    OPT_STALE_AFTER_HOURS,
    OPT_ZONES,
    ROLE_AUTO,
)
from .core.pin import hash_pin, is_valid_pin_format
from .core.profiles import (
    MAX_ALARM_CYCLES,
    MAX_DELAY,
    MAX_REACTION_TIME,
    MAX_STALE_HOURS,
    PROFILE_IDS,
    profile_behaviour,
    profile_settings,
    stale_after_seconds,
)
from .core.sensors import Zone, parse_zones, slugify
from .core.state_machine import (
    AlarmState,
    OpenSensorPolicy,
    SensorRole,
    UnavailableSensorPolicy,
)

SENSOR_DOMAIN = "binary_sensor"


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
        self._zone_id: str | None = None

    def _is_disarmed(self) -> bool:
        entry = self.config_entry
        if entry.state is not ConfigEntryState.LOADED:
            return True
        return bool(entry.runtime_data.ctx.state is AlarmState.DISARMED)

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if not self._is_disarmed():
            return self.async_abort(reason="disarm_first")
        return self.async_show_menu(
            step_id="init", menu_options=["zones", "profile", "roles", "monitoring", "code"]
        )

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

    # --- Profile ----------------------------------------------------------

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
        zones = parse_zones(options)
        if user_input is not None and "exit_delay" in user_input:
            profiles = {k: dict(v) for k, v in options.get(OPT_PROFILES, {}).items()}
            profiles[self._profile_id] = {
                "exit_delay": int(user_input["exit_delay"]),
                "entry_delay": int(user_input["entry_delay"]),
                "reaction_time": int(user_input["reaction_time"]),
                "zones": [z for z in user_input.get("zones", []) if z in zones],
                "open_policy": user_input["open_policy"],
                "unavailable_policy": user_input["unavailable_policy"],
                "max_alarm_cycles": int(user_input["max_alarm_cycles"]),
                "tamper_triggers_alarm": bool(user_input["tamper_triggers_alarm"]),
            }
            options[OPT_PROFILES] = profiles
            return self.async_create_entry(data=options)

        current = profile_settings(options, self._profile_id)
        behaviour = profile_behaviour(options, self._profile_id)
        schema = vol.Schema(
            {
                vol.Optional(
                    "zones", default=[z for z in behaviour.zones if z in zones]
                ): _zone_selector(zones, multiple=True),
                vol.Required("exit_delay", default=current["exit_delay"]): _seconds(MAX_DELAY),
                vol.Required("entry_delay", default=current["entry_delay"]): _seconds(MAX_DELAY),
                vol.Required("reaction_time", default=current["reaction_time"]): _seconds(
                    MAX_REACTION_TIME, minimum=1
                ),
                vol.Required("open_policy", default=behaviour.open_policy.value): _select(
                    [p.value for p in OpenSensorPolicy], "open_policy"
                ),
                vol.Required(
                    "unavailable_policy", default=behaviour.unavailable_policy.value
                ): _select([p.value for p in UnavailableSensorPolicy], "unavailable_policy"),
                vol.Required(
                    "max_alarm_cycles", default=behaviour.max_alarm_cycles
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1, max=MAX_ALARM_CYCLES, step=1, mode=NumberSelectorMode.BOX
                    )
                ),
                vol.Required(
                    "tamper_triggers_alarm", default=behaviour.tamper_triggers_alarm
                ): BooleanSelector(),
            }
        )
        return self.async_show_form(
            step_id="profile_settings",
            data_schema=schema,
            description_placeholders={"profile": self._profile_id},
        )

    # --- Zonen ------------------------------------------------------------

    async def async_step_zones(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self.async_show_menu(
            step_id="zones", menu_options=["zone_add", "zone_edit", "zone_delete"]
        )

    def _zone_schema(self, defaults: dict[str, Any]) -> vol.Schema:
        label_key = (
            vol.Optional("label", default=defaults["label"])
            if defaults.get("label")
            else vol.Optional("label")
        )
        return vol.Schema(
            {
                vol.Required("name", default=defaults.get("name", "")): TextSelector(),
                vol.Optional("entities", default=defaults.get("entities", [])): EntitySelector(
                    EntitySelectorConfig(domain=SENSOR_DOMAIN, multiple=True)
                ),
                label_key: LabelSelector(),
            }
        )

    def _save_zone(
        self, zone_id: str | None, user_input: dict[str, Any]
    ) -> tuple[dict[str, Any] | None, dict[str, str]]:
        name = str(user_input.get("name") or "").strip()
        entities = [str(e) for e in user_input.get("entities") or []]
        label = user_input.get("label") or None
        errors: dict[str, str] = {}
        if not name:
            errors["name"] = "zone_name_required"
        elif not entities and not label:
            errors["base"] = "zone_empty"
        if errors:
            return None, errors
        options = dict(self.config_entry.options)
        zones = {k: dict(v) for k, v in options.get(OPT_ZONES, {}).items()}
        new_id = zone_id or slugify(name, existing=zones.keys())
        zones[new_id] = {"name": name, "entities": sorted(set(entities)), "label": label}
        options[OPT_ZONES] = zones
        return options, {}

    async def async_step_zone_add(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            options, errors = self._save_zone(None, user_input)
            if options is not None:
                return self.async_create_entry(data=options)
        return self.async_show_form(
            step_id="zone_add", data_schema=self._zone_schema(user_input or {}), errors=errors
        )

    async def async_step_zone_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        zones = parse_zones(self.config_entry.options)
        if not zones:
            return self.async_abort(reason="no_zones")
        if user_input is not None:
            self._zone_id = user_input["zone"]
            return await self.async_step_zone_edit_settings()
        return self.async_show_form(
            step_id="zone_edit",
            data_schema=vol.Schema({vol.Required("zone"): _zone_selector(zones)}),
        )

    async def async_step_zone_edit_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        assert self._zone_id is not None
        errors: dict[str, str] = {}
        if user_input is not None and "name" in user_input:
            options, errors = self._save_zone(self._zone_id, user_input)
            if options is not None:
                return self.async_create_entry(data=options)
        zone = parse_zones(self.config_entry.options)[self._zone_id]
        defaults = user_input or {
            "name": zone.name,
            "entities": sorted(zone.entities),
            "label": zone.label,
        }
        return self.async_show_form(
            step_id="zone_edit_settings",
            data_schema=self._zone_schema(defaults),
            errors=errors,
            description_placeholders={"zone": zone.name},
        )

    async def async_step_zone_delete(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        zones = parse_zones(self.config_entry.options)
        if not zones:
            return self.async_abort(reason="no_zones")
        if user_input is not None:
            zone_id = user_input["zone"]
            options = dict(self.config_entry.options)
            options[OPT_ZONES] = {
                k: v for k, v in options.get(OPT_ZONES, {}).items() if k != zone_id
            }
            profiles = {k: dict(v) for k, v in options.get(OPT_PROFILES, {}).items()}
            for settings in profiles.values():
                if "zones" in settings:
                    settings["zones"] = [z for z in settings["zones"] if z != zone_id]
            options[OPT_PROFILES] = profiles
            return self.async_create_entry(data=options)
        return self.async_show_form(
            step_id="zone_delete",
            data_schema=vol.Schema({vol.Required("zone"): _zone_selector(zones)}),
        )

    # --- Rollen -----------------------------------------------------------

    async def async_step_roles(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        options = dict(self.config_entry.options)
        roles = dict(options.get(OPT_SENSOR_ROLES, {}))
        if user_input is not None:
            entity_id = user_input["entity"]
            role = user_input["role"]
            if role == ROLE_AUTO:
                roles.pop(entity_id, None)
            else:
                roles[entity_id] = role
            options[OPT_SENSOR_ROLES] = roles
            return self.async_create_entry(data=options)
        overrides = ", ".join(f"{e}: {r}" for e, r in sorted(roles.items())) or "–"
        schema = vol.Schema(
            {
                vol.Required("entity"): EntitySelector(EntitySelectorConfig(domain=SENSOR_DOMAIN)),
                vol.Required("role", default=ROLE_AUTO): _select(
                    [ROLE_AUTO, *[r.value for r in SensorRole]], "role"
                ),
            }
        )
        return self.async_show_form(
            step_id="roles",
            data_schema=schema,
            description_placeholders={"overrides": overrides},
        )

    # --- Überwachung ------------------------------------------------------

    async def async_step_monitoring(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        options = dict(self.config_entry.options)
        if user_input is not None:
            options[OPT_STALE_AFTER_HOURS] = int(user_input[OPT_STALE_AFTER_HOURS])
            return self.async_create_entry(data=options)
        current = stale_after_seconds(options)
        schema = vol.Schema(
            {
                vol.Required(
                    OPT_STALE_AFTER_HOURS, default=int(current / 3600) if current else 0
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0,
                        max=MAX_STALE_HOURS,
                        step=1,
                        unit_of_measurement="h",
                        mode=NumberSelectorMode.BOX,
                    )
                )
            }
        )
        return self.async_show_form(step_id="monitoring", data_schema=schema)


def _select(options: list[str], translation_key: str) -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=options, translation_key=translation_key, mode=SelectSelectorMode.DROPDOWN
        )
    )


def _zone_selector(zones: dict[str, Zone], *, multiple: bool = False) -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=[
                SelectOptionDict(value=zone_id, label=zone.name) for zone_id, zone in zones.items()
            ],
            multiple=multiple,
            mode=SelectSelectorMode.LIST,
        )
    )
