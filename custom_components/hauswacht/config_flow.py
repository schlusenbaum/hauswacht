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
from homeassistant.data_entry_flow import section
from homeassistant.helpers.selector import (
    BooleanSelector,
    DateTimeSelector,
    EntitySelector,
    EntitySelectorConfig,
    IconSelector,
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
    TimeSelector,
)
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    MASTER_USER_ID,
    MASTER_USER_NAME,
    NAME,
    OPT_BUTTONS_WITHOUT_PIN,
    OPT_CODE_ARM_REQUIRED,
    OPT_CRITICAL_ALERTS,
    OPT_DURESS_NOTIFY,
    OPT_END_ALARM_WITHOUT_PIN,
    OPT_EVENTS,
    OPT_HOMECOMING_OBSERVE,
    OPT_HOMECOMING_PERSONS,
    OPT_INFRASTRUCTURE,
    OPT_NOTIFY_IN_TEST_MODE,
    OPT_NOTIFY_SYSTEM,
    OPT_PROFILES,
    OPT_PUSH_DISARM,
    OPT_REMINDER_DELAY,
    OPT_REMINDER_PERSONS,
    OPT_REMINDER_PROFILE,
    OPT_SENSOR_ROLES,
    OPT_SIRENS,
    OPT_SIRENS_HARDWARE_ENABLED,
    OPT_STALE_AFTER_HOURS,
    OPT_USERS,
    OPT_ZONES,
    ROLE_AUTO,
)
from .core.automation import (
    DEFAULT_AWAY_DELAY,
    MAX_AWAY_DELAY,
    WEEKDAYS,
    AutoConfig,
    parse_automation,
)
from .core.notify_events import NotifyEvent, enabled, event_targets
from .core.pin import hash_pin, is_valid_pin_format
from .core.profiles import (
    DEFAULT_ICON,
    MAX_ALARM_CYCLES,
    MAX_DELAY,
    MAX_REACTION_TIME,
    MAX_STALE_HOURS,
    PANEL_MODE_NONE,
    PANEL_MODES,
    profile_behaviour,
    profile_ids,
    profile_info,
    profile_infos,
    profile_settings,
    stale_after_seconds,
)
from .core.reactions import parse_reaction
from .core.sensors import Zone, parse_zones, slugify, zone_conflicts
from .core.siren_guard import BURGLAR_TONES, VOLUME_LEVELS
from .core.state_machine import (
    AlarmState,
    OpenSensorPolicy,
    SensorRole,
    UnavailableSensorPolicy,
)
from .core.users import parse_users, pin_conflicts
from .names import display_name
from .runtime import entities_by_label

SENSOR_DOMAIN = "binary_sensor"
SIREN_ENTITY_DOMAIN = "siren"  # nur zur Auswahl im Formular, kein Dienstaufruf


class HauswachtConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 3

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
        self._saved = False

    async def _save(self, options: dict[str, Any], back: str) -> ConfigFlowResult:
        """Sofort speichern und zurück ins Menü – so lassen sich mehrere Dinge nacheinander
        ändern, ohne dass sich der Dialog schließt."""
        if not self._is_disarmed():
            # Die Anlage wurde scharf geschaltet, während der Dialog offen war: nichts speichern
            return self.async_abort(reason="disarm_first")
        self.hass.config_entries.async_update_entry(self.config_entry, options=options)
        self._saved = True
        step = getattr(self, f"async_step_{back}")
        result: ConfigFlowResult = await step()
        return result

    def _saved_text(self) -> str:
        if (self.hass.config.language or "").startswith("de"):
            return "✅ Gespeichert.\n\n"
        return "✅ Saved.\n\n"

    def _menu(self, step_id: str, menu_options: list[str]) -> ConfigFlowResult:
        saved, self._saved = self._saved, False
        return self.async_show_menu(
            step_id=step_id,
            menu_options=menu_options,
            description_placeholders={"saved": self._saved_text() if saved else ""},
        )

    def _is_disarmed(self) -> bool:
        entry = self.config_entry
        if entry.state is not ConfigEntryState.LOADED:
            return True
        return bool(entry.runtime_data.ctx.state is AlarmState.DISARMED)

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if not self._is_disarmed():
            return self.async_abort(reason="disarm_first")
        return self._menu(
            "init", ["zones", "profiles", "sirens", "notifications", "system", "done"]
        )

    async def async_step_done(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Schließen. Gespeichert wurde bereits nach jedem Formular."""
        return self.async_create_entry(data=dict(self.config_entry.options))

    async def async_step_system(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self._menu(
            "system", ["users", "sensor_behaviour", "infrastructure", "homecoming", "init"]
        )

    async def async_step_code(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """PIN-Regeln und optionaler Master-PIN (intern ein Benutzer mit allen Rechten)."""
        options = dict(self.config_entry.options)
        errors: dict[str, str] = {}
        placeholders: dict[str, str] = {"conflict": ""}
        if user_input is not None:
            master = str(user_input.get("master_pin") or "").strip()
            users_opt: dict[str, Any] = dict(options.get(OPT_USERS, {}))
            if user_input.get("remove_master_pin"):
                users_opt.pop(MASTER_USER_ID, None)
            elif master:
                if not is_valid_pin_format(master):
                    errors["master_pin"] = "invalid_pin"
                else:
                    users = parse_users(options)
                    found = await self.hass.async_add_executor_job(
                        lambda: pin_conflicts(master, users, kind="pin")
                    )
                    if found:
                        errors["master_pin"] = "pin_is_duress"
                        placeholders["conflict"] = ", ".join(found)
                    else:
                        hashed = await self.hass.async_add_executor_job(hash_pin, master)
                        users_opt[MASTER_USER_ID] = {
                            **users_opt.get(MASTER_USER_ID, {}),
                            "name": MASTER_USER_NAME,
                            "pin_salt": hashed.salt,
                            "pin_digest": hashed.digest,
                        }
            if not errors:
                options[OPT_USERS] = users_opt
                for key in (OPT_CODE_ARM_REQUIRED, OPT_END_ALARM_WITHOUT_PIN):
                    options[key] = bool(user_input.get(key, False))
                options[OPT_BUTTONS_WITHOUT_PIN] = bool(user_input.get(OPT_BUTTONS_WITHOUT_PIN))
                return await self._save(options, "users")
        users = parse_users(options)
        with_pin = sorted(u.name for u in users if u.pin is not None)
        placeholders["pin_users"] = ", ".join(with_pin) or "–"
        schema = vol.Schema(
            {
                vol.Optional("master_pin"): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
                vol.Optional("remove_master_pin", default=False): BooleanSelector(),
                vol.Optional(
                    OPT_CODE_ARM_REQUIRED,
                    default=bool(options.get(OPT_CODE_ARM_REQUIRED, False)),
                ): BooleanSelector(),
                vol.Optional(
                    OPT_END_ALARM_WITHOUT_PIN,
                    default=bool(options.get(OPT_END_ALARM_WITHOUT_PIN, False)),
                ): BooleanSelector(),
                vol.Optional(
                    OPT_BUTTONS_WITHOUT_PIN,
                    default=bool(options.get(OPT_BUTTONS_WITHOUT_PIN, False)),
                ): BooleanSelector(),
            }
        )
        return self.async_show_form(
            step_id="code", data_schema=schema, errors=errors, description_placeholders=placeholders
        )

    # --- Profile ----------------------------------------------------------

    async def async_step_profiles(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self._menu("profiles", ["profile_add", "profile_edit", "profile_delete", "init"])

    def _profile_selector(self) -> SelectSelector:
        return SelectSelector(
            SelectSelectorConfig(
                options=[
                    SelectOptionDict(value=i.profile_id, label=i.name)
                    for i in profile_infos(self.config_entry.options)
                ],
                mode=SelectSelectorMode.LIST,
            )
        )

    async def async_step_profile_add(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        self._profile_id = None
        return await self.async_step_profile_settings()

    async def async_step_profile_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if not profile_ids(self.config_entry.options):
            return self.async_abort(reason="no_profiles")
        if user_input is not None:
            self._profile_id = user_input["profile"]
            return await self.async_step_profile_settings()
        return self.async_show_form(
            step_id="profile_edit",
            data_schema=vol.Schema({vol.Required("profile"): self._profile_selector()}),
        )

    async def async_step_profile_delete(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if not profile_ids(self.config_entry.options):
            return self.async_abort(reason="no_profiles")
        if user_input is not None:
            options = dict(self.config_entry.options)
            options[OPT_PROFILES] = {
                k: v for k, v in options.get(OPT_PROFILES, {}).items() if k != user_input["profile"]
            }
            return await self._save(options, "profiles")
        return self.async_show_form(
            step_id="profile_delete",
            data_schema=vol.Schema({vol.Required("profile"): self._profile_selector()}),
        )

    def _validate_profile(self, user_input: dict[str, Any]) -> dict[str, str]:
        options = self.config_entry.options
        others = [i for i in profile_infos(options) if i.profile_id != self._profile_id]
        name = str(user_input.get("name") or "").strip()
        errors: dict[str, str] = {}
        if not name:
            errors["name"] = "profile_name_required"
        elif any(i.name.casefold() == name.casefold() for i in others):
            errors["name"] = "profile_name_taken"
        mode = user_input.get("panel_mode", PANEL_MODE_NONE)
        if mode != PANEL_MODE_NONE and any(i.panel_mode == mode for i in others):
            errors["panel_mode"] = "panel_mode_taken"
        return errors

    async def async_step_profile_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        options = dict(self.config_entry.options)
        zones = parse_zones(options)
        registered_sirens = [s for s in options.get(OPT_SIRENS, []) if isinstance(s, str)]
        errors: dict[str, str] = {}
        if user_input is not None and "name" in user_input:
            errors = self._validate_profile(user_input)
            if not errors:
                profiles = {k: dict(v) for k, v in options.get(OPT_PROFILES, {}).items()}
                name = str(user_input["name"]).strip()
                profile_id = self._profile_id or slugify(name, existing=profiles.keys())
                mode = user_input.get("panel_mode", PANEL_MODE_NONE)
                data = dict(profiles.get(profile_id, {}))  # unbekannte Schlüssel behalten
                data.update(
                    {
                        "name": name,
                        "icon": user_input.get("icon") or DEFAULT_ICON,
                        "panel_mode": None if mode == PANEL_MODE_NONE else mode,
                        "exit_delay": int(user_input["exit_delay"]),
                        "entry_delay": int(user_input["entry_delay"]),
                        "reaction_time": int(user_input["reaction_time"]),
                        "zones": [z for z in user_input.get("zones", []) if z in zones],
                        "open_policy": user_input["open_policy"],
                        "unavailable_policy": user_input["unavailable_policy"],
                        "max_alarm_cycles": int(user_input["max_alarm_cycles"]),
                        "tamper_triggers_alarm": bool(user_input["tamper_triggers_alarm"]),
                        "sirens": [
                            s for s in user_input.get("sirens", []) if s in registered_sirens
                        ],
                        "siren_tone": user_input["siren_tone"],
                        "siren_volume": user_input["siren_volume"],
                        "silent": bool(user_input["silent"]),
                        "notify": list(user_input.get("notify", [])),
                        **_automation_from_input(user_input.get("automation") or {}),
                    }
                )
                profiles[profile_id] = data
                options[OPT_PROFILES] = profiles
                return await self._save(options, "profiles")

        pid = self._profile_id or ""
        info = profile_info(options, pid) if self._profile_id else None
        current = profile_settings(options, pid)
        behaviour = profile_behaviour(options, pid)
        reaction = parse_reaction(options, pid)
        source = user_input or {}
        schema = vol.Schema(
            {
                vol.Required("name", default=source.get("name", info.name if info else "")): (
                    TextSelector()
                ),
                vol.Required(
                    "icon", default=source.get("icon", info.icon if info else DEFAULT_ICON)
                ): IconSelector(),
                vol.Required(
                    "panel_mode",
                    default=source.get(
                        "panel_mode",
                        (info.panel_mode if info and info.panel_mode else PANEL_MODE_NONE),
                    ),
                ): _select([PANEL_MODE_NONE, *PANEL_MODES], "panel_mode"),
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
                vol.Optional("sirens", default=list(reaction.sirens)): _list_selector(
                    registered_sirens, multiple=True
                ),
                vol.Required("siren_tone", default=reaction.tone): _select(
                    sorted(BURGLAR_TONES), "siren_tone"
                ),
                vol.Required("siren_volume", default=reaction.volume): _select(
                    list(VOLUME_LEVELS), "siren_volume"
                ),
                vol.Required("silent", default=reaction.silent): BooleanSelector(),
                vol.Optional("notify", default=list(reaction.notify)): _list_selector(
                    self._notify_services(), multiple=True, custom=True
                ),
                # Kein default am Bereich: Sonst füllt die Oberfläche die Felder darin nicht
                # vor, und "OK" bleibt ohne Meldung wirkungslos.
                vol.Optional("automation"): section(
                    _automation_schema(parse_automation(options, pid)),
                    {"collapsed": True},
                ),
            }
        )
        return self.async_show_form(
            step_id="profile_settings",
            data_schema=schema,
            errors=errors,
            description_placeholders={"profile": info.name if info else "–"},
        )

    # --- Zonen ------------------------------------------------------------

    async def async_step_zones(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self._menu("zones", ["zone_add", "zone_edit", "zone_delete", "init"])

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
    ) -> tuple[dict[str, Any] | None, dict[str, str], dict[str, str]]:
        name = str(user_input.get("name") or "").strip()
        entities = [str(e) for e in user_input.get("entities") or []]
        label = user_input.get("label") or None
        errors: dict[str, str] = {}
        if not name:
            errors["name"] = "zone_name_required"
        elif not entities and not label:
            errors["base"] = "zone_empty"
        if errors:
            return None, errors, {}
        options = dict(self.config_entry.options)
        zones = {k: dict(v) for k, v in options.get(OPT_ZONES, {}).items()}
        new_id = zone_id or slugify(name, existing=zones.keys())
        conflicts = zone_conflicts(
            Zone(zone_id=new_id, name=name, entities=frozenset(entities), label=label),
            parse_zones(options),
            entities_by_label(self.hass),
        )
        if conflicts:
            text = ", ".join(
                f"{display_name(self.hass, entity_id)} ({zone})"
                for entity_id, zone in conflicts.items()
            )
            return None, {"base": "zone_overlap"}, {"conflicts": text}
        zones[new_id] = {"name": name, "entities": sorted(set(entities)), "label": label}
        options[OPT_ZONES] = zones
        return options, {}, {}

    async def async_step_zone_add(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        placeholders: dict[str, str] = {"conflicts": ""}
        if user_input is not None:
            options, errors, extra = self._save_zone(None, user_input)
            if options is not None:
                return await self._save(options, "zones")
            placeholders.update(extra)
        return self.async_show_form(
            step_id="zone_add",
            data_schema=self._zone_schema(user_input or {}),
            errors=errors,
            description_placeholders=placeholders,
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
        placeholders: dict[str, str] = {"conflicts": ""}
        if user_input is not None and "name" in user_input:
            options, errors, extra = self._save_zone(self._zone_id, user_input)
            if options is not None:
                return await self._save(options, "zones")
            placeholders.update(extra)
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
            description_placeholders={"zone": zone.name, **placeholders},
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
            return await self._save(options, "zones")
        return self.async_show_form(
            step_id="zone_delete",
            data_schema=vol.Schema({vol.Required("zone"): _zone_selector(zones)}),
        )

    # --- Rollen -----------------------------------------------------------

    async def async_step_sensor_behaviour(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Sensorverhalten: Rollen-Ausnahmen und maximale Funkstille in einem Formular."""
        options = dict(self.config_entry.options)
        roles = dict(options.get(OPT_SENSOR_ROLES, {}))
        if user_input is not None:
            options[OPT_STALE_AFTER_HOURS] = int(user_input.get(OPT_STALE_AFTER_HOURS) or 0)
            entity_id = user_input.get("entity")
            if entity_id:
                role = user_input.get("role") or ROLE_AUTO
                if role == ROLE_AUTO:
                    roles.pop(entity_id, None)
                else:
                    roles[entity_id] = role
            options[OPT_SENSOR_ROLES] = roles
            return await self._save(options, "system")
        overrides = (
            ", ".join(f"{display_name(self.hass, e)}: {r}" for e, r in sorted(roles.items())) or "–"
        )
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
                ),
                vol.Optional("entity"): EntitySelector(EntitySelectorConfig(domain=SENSOR_DOMAIN)),
                vol.Optional("role", default=ROLE_AUTO): _select(
                    [ROLE_AUTO, *[r.value for r in SensorRole]], "role"
                ),
            }
        )
        return self.async_show_form(
            step_id="sensor_behaviour",
            data_schema=schema,
            description_placeholders={"overrides": overrides},
        )

    # --- Sirenen -----------------------------------------------------------

    async def async_step_sirens(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        options = dict(self.config_entry.options)
        was_enabled = bool(options.get(OPT_SIRENS_HARDWARE_ENABLED, False))
        errors: dict[str, str] = {}
        if user_input is not None:
            enable = bool(user_input.get(OPT_SIRENS_HARDWARE_ENABLED, False))
            if enable and not was_enabled and not user_input.get("confirm_hardware"):
                errors["base"] = "confirm_hardware_required"
            else:
                sirens = sorted(set(user_input.get(OPT_SIRENS) or []))
                options[OPT_SIRENS] = sirens
                options[OPT_SIRENS_HARDWARE_ENABLED] = enable
                # Aus Profilen entfernen, was nicht mehr registriert ist
                profiles = {k: dict(v) for k, v in options.get(OPT_PROFILES, {}).items()}
                for settings in profiles.values():
                    if "sirens" in settings:
                        settings["sirens"] = [s for s in settings["sirens"] if s in sirens]
                options[OPT_PROFILES] = profiles
                return await self._save(options, "init")
        schema = vol.Schema(
            {
                vol.Optional(OPT_SIRENS, default=list(options.get(OPT_SIRENS, []))): EntitySelector(
                    EntitySelectorConfig(domain=SIREN_ENTITY_DOMAIN, multiple=True)
                ),
                vol.Required(OPT_SIRENS_HARDWARE_ENABLED, default=was_enabled): BooleanSelector(),
                vol.Optional("confirm_hardware", default=False): BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="sirens", data_schema=schema, errors=errors)

    # --- Benachrichtigungen --------------------------------------------------

    def _notify_services(self) -> list[str]:
        services = self.hass.services.async_services_for_domain("notify")
        return sorted(s for s in services if s not in {"send_message", "notify"})

    async def async_step_notifications(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        options = dict(self.config_entry.options)
        if user_input is not None:
            options[OPT_NOTIFY_SYSTEM] = list(user_input.get(OPT_NOTIFY_SYSTEM) or [])
            options[OPT_NOTIFY_IN_TEST_MODE] = bool(user_input.get(OPT_NOTIFY_IN_TEST_MODE))
            options[OPT_PUSH_DISARM] = bool(user_input.get(OPT_PUSH_DISARM))
            options[OPT_CRITICAL_ALERTS] = bool(user_input.get(OPT_CRITICAL_ALERTS, True))
            options[OPT_DURESS_NOTIFY] = list(user_input.get(OPT_DURESS_NOTIFY) or [])
            events: dict[str, dict[str, Any]] = {}
            for event in NotifyEvent:
                stored = user_input.get(f"event_{event.value}")
                if isinstance(stored, dict):
                    events[event.value] = {
                        "enabled": bool(stored.get("enabled")),
                        "targets": list(stored.get("targets") or []),
                    }
                elif event.value in options.get(OPT_EVENTS, {}):
                    events[event.value] = options[OPT_EVENTS][event.value]
            options[OPT_EVENTS] = events
            reminder = user_input.get("reminder")
            if isinstance(reminder, dict):
                options[OPT_REMINDER_PERSONS] = list(reminder.get(OPT_REMINDER_PERSONS) or [])
                profile = reminder.get(OPT_REMINDER_PROFILE)
                if profile:
                    options[OPT_REMINDER_PROFILE] = profile
                else:
                    options.pop(OPT_REMINDER_PROFILE, None)
                options[OPT_REMINDER_DELAY] = int(reminder.get(OPT_REMINDER_DELAY) or 15)
            return await self._save(options, "init")

        services = self._notify_services()
        push_disarm = bool(options.get(OPT_PUSH_DISARM, False))
        fields: dict[Any, Any] = {
            vol.Optional(
                OPT_NOTIFY_SYSTEM, default=list(options.get(OPT_NOTIFY_SYSTEM, []))
            ): _list_selector(services, multiple=True, custom=True),
            vol.Required(
                OPT_NOTIFY_IN_TEST_MODE,
                default=bool(options.get(OPT_NOTIFY_IN_TEST_MODE, False)),
            ): BooleanSelector(),
            vol.Required(OPT_PUSH_DISARM, default=push_disarm): BooleanSelector(),
            vol.Required(
                OPT_CRITICAL_ALERTS, default=bool(options.get(OPT_CRITICAL_ALERTS, True))
            ): BooleanSelector(),
            vol.Optional(
                OPT_DURESS_NOTIFY, default=list(options.get(OPT_DURESS_NOTIFY, []))
            ): _list_selector(services, multiple=True, custom=True),
        }
        for event in NotifyEvent:
            # Kein default am Bereich (siehe Profile), Felder darin optional mit default
            fields[vol.Optional(f"event_{event.value}")] = section(
                vol.Schema(
                    {
                        vol.Optional(
                            "enabled", default=enabled(options, event, push_disarm=push_disarm)
                        ): BooleanSelector(),
                        vol.Optional(
                            "targets", default=list(event_targets(options, event))
                        ): _list_selector(services, multiple=True, custom=True),
                    }
                ),
                {"collapsed": True},
            )
        reminder_fields: dict[Any, Any] = {
            vol.Optional(
                OPT_REMINDER_PERSONS, default=list(options.get(OPT_REMINDER_PERSONS, []))
            ): EntitySelector(EntitySelectorConfig(domain="person", multiple=True)),
        }
        profile = options.get(OPT_REMINDER_PROFILE)
        profile_key = (
            vol.Optional(OPT_REMINDER_PROFILE, default=profile)
            if isinstance(profile, str) and profile in profile_ids(options)
            else vol.Optional(OPT_REMINDER_PROFILE)
        )
        reminder_fields[profile_key] = self._profile_selector()
        reminder_fields[
            vol.Optional(OPT_REMINDER_DELAY, default=int(options.get(OPT_REMINDER_DELAY, 15)))
        ] = NumberSelector(
            NumberSelectorConfig(
                min=1, max=240, step=1, unit_of_measurement="min", mode=NumberSelectorMode.BOX
            )
        )
        fields[vol.Optional("reminder")] = section(vol.Schema(reminder_fields), {"collapsed": True})
        return self.async_show_form(step_id="notifications", data_schema=vol.Schema(fields))

    # --- Benutzer ------------------------------------------------------------

    async def async_step_users(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self._menu("users", ["user_add", "user_edit", "user_delete", "code", "system"])

    def _user_selector(self) -> SelectSelector:
        stored = self.config_entry.options.get(OPT_USERS, {})
        return SelectSelector(
            SelectSelectorConfig(
                options=[
                    SelectOptionDict(value=uid, label=str(data.get("name") or uid))
                    for uid, data in stored.items()
                ],
                mode=SelectSelectorMode.LIST,
            )
        )

    async def async_step_user_add(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        self._user_id = None
        return await self.async_step_user_settings()

    async def async_step_user_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if not self.config_entry.options.get(OPT_USERS):
            return self.async_abort(reason="no_users")
        if user_input is not None:
            self._user_id = user_input["user"]
            return await self.async_step_user_settings()
        return self.async_show_form(
            step_id="user_edit",
            data_schema=vol.Schema({vol.Required("user"): self._user_selector()}),
        )

    async def async_step_user_delete(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if not self.config_entry.options.get(OPT_USERS):
            return self.async_abort(reason="no_users")
        if user_input is not None:
            options = dict(self.config_entry.options)
            options[OPT_USERS] = {
                k: v for k, v in options.get(OPT_USERS, {}).items() if k != user_input["user"]
            }
            return await self._save(options, "users")
        return self.async_show_form(
            step_id="user_delete",
            data_schema=vol.Schema({vol.Required("user"): self._user_selector()}),
        )

    async def _ha_user_by_name(self, name: str) -> str | None:
        """Wurde ein Home-Assistant-Benutzer als Name gewählt, wird er automatisch verknüpft."""
        for option in await self._ha_user_options():
            if option["label"].casefold() == name.casefold():
                return option["value"]
        return None

    async def _ha_user_options(self) -> list[SelectOptionDict]:
        users = await self.hass.auth.async_get_users()
        return [
            SelectOptionDict(value=u.id, label=u.name or u.id)
            for u in users
            if u.is_active and not u.system_generated
        ]

    async def async_step_user_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        options = self.config_entry.options
        stored_all: dict[str, Any] = dict(options.get(OPT_USERS, {}))
        user_id = getattr(self, "_user_id", None)
        current: dict[str, Any] = dict(stored_all.get(user_id, {})) if user_id else {}
        errors: dict[str, str] = {}
        placeholders = {"conflict": ""}
        if user_input is not None:
            name = str(user_input.get("name") or "").strip()
            new_pin = str(user_input.get("new_pin") or "").strip()
            new_duress = str(user_input.get("new_duress_pin") or "").strip()
            errors, conflict = await self._validate_user(
                name, (new_pin, new_duress), user_id, stored_all
            )
            placeholders["conflict"] = conflict
            if not errors:
                data = dict(current)
                data.update(
                    {
                        "name": name,
                        "active": bool(user_input.get("active", True)),
                        "can_arm": bool(user_input.get("can_arm", True)),
                        "can_disarm": bool(user_input.get("can_disarm", True)),
                        "can_end_alarm": bool(user_input.get("can_end_alarm", True)),
                        "ha_user": user_input.get("ha_user") or await self._ha_user_by_name(name),
                        "valid_from": _to_iso(user_input.get("valid_from")),
                        "valid_until": _to_iso(user_input.get("valid_until")),
                    }
                )
                if user_input.get("remove_pin"):
                    data.pop("pin_salt", None)
                    data.pop("pin_digest", None)
                elif new_pin:
                    hashed = await self.hass.async_add_executor_job(hash_pin, new_pin)
                    data["pin_salt"], data["pin_digest"] = hashed.salt, hashed.digest
                if user_input.get("remove_duress_pin"):
                    data.pop("duress_salt", None)
                    data.pop("duress_digest", None)
                elif new_duress:
                    hashed = await self.hass.async_add_executor_job(hash_pin, new_duress)
                    data["duress_salt"], data["duress_digest"] = hashed.salt, hashed.digest
                new_id = user_id or _unique_id(name, stored_all)
                stored_all[new_id] = data
                new_options = dict(options)
                new_options[OPT_USERS] = stored_all
                return await self._save(new_options, "users")

        status = []
        if current.get("pin_digest"):
            status.append("PIN gesetzt")
        if current.get("duress_digest"):
            status.append("Bedrohungs-PIN gesetzt")
        placeholders["status"] = ", ".join(status) or "kein PIN"
        schema = await self._user_schema(current)
        return self.async_show_form(
            step_id="user_settings",
            data_schema=schema,
            errors=errors,
            description_placeholders=placeholders,
        )

    # --- Heimkehr-Beobachtung ---------------------------------------------

    async def async_step_homecoming(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        options = dict(self.config_entry.options)
        if user_input is not None:
            options[OPT_HOMECOMING_OBSERVE] = bool(user_input.get(OPT_HOMECOMING_OBSERVE))
            options[OPT_HOMECOMING_PERSONS] = list(user_input.get(OPT_HOMECOMING_PERSONS) or [])
            return await self._save(options, "system")
        schema = vol.Schema(
            {
                vol.Required(
                    OPT_HOMECOMING_OBSERVE,
                    default=bool(options.get(OPT_HOMECOMING_OBSERVE, False)),
                ): BooleanSelector(),
                vol.Optional(
                    OPT_HOMECOMING_PERSONS,
                    default=list(options.get(OPT_HOMECOMING_PERSONS, [])),
                ): EntitySelector(EntitySelectorConfig(domain="person", multiple=True)),
            }
        )
        return self.async_show_form(step_id="homecoming", data_schema=schema)

    # --- Infrastruktur ------------------------------------------------------

    async def async_step_infrastructure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        options = dict(self.config_entry.options)
        if user_input is not None:
            options[OPT_INFRASTRUCTURE] = sorted(set(user_input.get(OPT_INFRASTRUCTURE) or []))
            return await self._save(options, "system")
        schema = vol.Schema(
            {
                vol.Optional(
                    OPT_INFRASTRUCTURE, default=list(options.get(OPT_INFRASTRUCTURE, []))
                ): EntitySelector(EntitySelectorConfig(domain=SENSOR_DOMAIN, multiple=True))
            }
        )
        return self.async_show_form(step_id="infrastructure", data_schema=schema)

    async def _validate_user(
        self, name: str, pins: tuple[str, str], user_id: str | None, stored_all: dict[str, Any]
    ) -> tuple[dict[str, str], str]:
        new_pin, new_duress = pins
        errors: dict[str, str] = {}
        conflict = ""
        if not name:
            errors["name"] = "user_name_required"
        elif any(
            str(d.get("name", "")).casefold() == name.casefold()
            for uid, d in stored_all.items()
            if uid != user_id
        ):
            errors["name"] = "user_name_taken"
        if new_pin and not is_valid_pin_format(new_pin):
            errors["new_pin"] = "invalid_pin"
        if new_duress and not is_valid_pin_format(new_duress):
            errors["new_duress_pin"] = "invalid_pin"
        if new_pin and new_duress and new_pin == new_duress:
            errors["new_duress_pin"] = "duress_equals_pin"
        users = parse_users(self.config_entry.options)
        if not errors and new_pin:
            found = await self.hass.async_add_executor_job(
                lambda: pin_conflicts(new_pin, users, kind="pin")
            )
            if found:
                errors["new_pin"] = "pin_is_duress"
                conflict = ", ".join(found)
        if not errors and new_duress:
            found = await self.hass.async_add_executor_job(
                lambda: pin_conflicts(new_duress, users, kind="duress", exclude=user_id)
            )
            if found:
                errors["new_duress_pin"] = "duress_conflict"
                conflict = ", ".join(found)
        return errors, conflict

    async def _user_schema(self, current: dict[str, Any]) -> vol.Schema:
        ha_user = current.get("ha_user")
        ha_desc = {"suggested_value": ha_user} if ha_user else {}
        # Namen: Vorschläge aus den Home-Assistant-Benutzern, freie Namen erlaubt
        taken = {
            str(d.get("name", "")).casefold()
            for uid, d in self.config_entry.options.get(OPT_USERS, {}).items()
            if uid != getattr(self, "_user_id", None)
        }
        name_options = [
            o["label"] for o in await self._ha_user_options() if o["label"].casefold() not in taken
        ]
        current_name = current.get("name")
        if current_name and current_name not in name_options:
            name_options.insert(0, current_name)
        name_key = (
            vol.Required("name", default=current_name) if current_name else vol.Required("name")
        )
        return vol.Schema(
            {
                name_key: SelectSelector(
                    SelectSelectorConfig(
                        options=name_options, custom_value=True, mode=SelectSelectorMode.DROPDOWN
                    )
                ),
                vol.Optional("new_pin"): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
                vol.Optional("remove_pin", default=False): BooleanSelector(),
                vol.Optional("new_duress_pin"): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
                vol.Optional("remove_duress_pin", default=False): BooleanSelector(),
                vol.Optional("active", default=bool(current.get("active", True))): (
                    BooleanSelector()
                ),
                vol.Optional("can_arm", default=bool(current.get("can_arm", True))): (
                    BooleanSelector()
                ),
                vol.Optional("can_disarm", default=bool(current.get("can_disarm", True))): (
                    BooleanSelector()
                ),
                vol.Optional(
                    "can_end_alarm", default=bool(current.get("can_end_alarm", True))
                ): BooleanSelector(),
                vol.Optional("ha_user", description=ha_desc): SelectSelector(
                    SelectSelectorConfig(
                        options=await self._ha_user_options(), mode=SelectSelectorMode.DROPDOWN
                    )
                ),
                vol.Optional(
                    "valid_from", description=_suggested_local(current.get("valid_from"))
                ): DateTimeSelector(),
                vol.Optional(
                    "valid_until", description=_suggested_local(current.get("valid_until"))
                ): DateTimeSelector(),
            }
        )


def _automation_schema(auto: AutoConfig) -> vol.Schema:
    """Automatik eines Profils. Leere Felder bedeuten: diese Automatik ist aus."""

    def suggested(value: Any) -> dict[str, Any]:
        return {"suggested_value": value} if value else {}

    return vol.Schema(
        {
            vol.Optional(
                "auto_arm_time",
                description=suggested(auto.arm_time.isoformat() if auto.arm_time else None),
            ): TimeSelector(),
            vol.Optional(
                "auto_disarm_time",
                description=suggested(auto.disarm_time.isoformat() if auto.disarm_time else None),
            ): TimeSelector(),
            vol.Optional("auto_weekdays", default=sorted(auto.weekdays, key=WEEKDAYS.index)): (
                SelectSelector(
                    SelectSelectorConfig(
                        options=list(WEEKDAYS),
                        multiple=True,
                        translation_key="weekday",
                        mode=SelectSelectorMode.LIST,
                    )
                )
            ),
            vol.Optional(
                "auto_away_persons", description=suggested(list(auto.away_persons))
            ): EntitySelector(EntitySelectorConfig(domain="person", multiple=True)),
            vol.Optional("auto_away_delay", default=auto.away_delay): NumberSelector(
                NumberSelectorConfig(
                    min=1,
                    max=MAX_AWAY_DELAY,
                    step=1,
                    unit_of_measurement="min",
                    mode=NumberSelectorMode.BOX,
                )
            ),
            vol.Optional(
                "auto_disarm_on_arrival", default=auto.disarm_on_arrival
            ): BooleanSelector(),
        }
    )


def _automation_from_input(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "auto_arm_time": data.get("auto_arm_time") or None,
        "auto_disarm_time": data.get("auto_disarm_time") or None,
        "auto_weekdays": [d for d in data.get("auto_weekdays", []) if d in WEEKDAYS],
        "auto_away_persons": list(data.get("auto_away_persons") or []),
        "auto_away_delay": int(data.get("auto_away_delay", DEFAULT_AWAY_DELAY)),
        "auto_disarm_on_arrival": bool(data.get("auto_disarm_on_arrival", False)),
    }


def _select(options: list[str], translation_key: str) -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=options, translation_key=translation_key, mode=SelectSelectorMode.DROPDOWN
        )
    )


def _list_selector(
    values: list[str], *, multiple: bool = False, custom: bool = False
) -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=values,
            multiple=multiple,
            custom_value=custom,
            mode=SelectSelectorMode.DROPDOWN,
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


def _to_iso(value: Any) -> str | None:
    """Datum/Uhrzeit aus dem Formular (lokale Zeit) als ISO-Text mit Zeitzone."""
    if not value:
        return None
    parsed = dt_util.parse_datetime(str(value))
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt_util.get_default_time_zone())
    return parsed.isoformat()


def _suggested_local(value: Any) -> dict[str, Any]:
    if not isinstance(value, str) or not value:
        return {}
    parsed = dt_util.parse_datetime(value)
    if parsed is None:
        return {}
    return {"suggested_value": dt_util.as_local(parsed).strftime("%Y-%m-%d %H:%M:%S")}


def _unique_id(name: str, existing: dict[str, Any]) -> str:
    base = "".join(c if c.isalnum() else "_" for c in name.casefold()).strip("_") or "benutzer"
    candidate, n = base, 2
    while candidate in existing:
        candidate, n = f"{base}_{n}", n + 1
    return candidate
