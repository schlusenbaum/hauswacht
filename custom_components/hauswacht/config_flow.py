"""Einrichtung und Optionen von Hauswacht."""

from __future__ import annotations

import asyncio
import copy
import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    SOURCE_USER,
    ConfigEntry,
    ConfigEntryState,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import section
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.selector import (
    BooleanSelector,
    DateTimeSelector,
    DeviceSelector,
    DeviceSelectorConfig,
    EntitySelector,
    EntitySelectorConfig,
    IconSelector,
    LabelSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    ObjectSelector,
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
    OPT_AREAS,
    OPT_BUTTONS_WITHOUT_PIN,
    OPT_CARD_LEARN_MINUTES,
    OPT_CODE_ARM_REQUIRED,
    OPT_CONTROLS,
    OPT_CRITICAL_ALERTS,
    OPT_DURESS_NOTIFY,
    OPT_END_ALARM_WITHOUT_PIN,
    OPT_EVENTS,
    OPT_HOMECOMING_OBSERVE,
    OPT_HOMECOMING_PERSONS,
    OPT_HOMECOMING_SIGNALS,
    OPT_HOMECOMING_SSIDS,
    OPT_INFRASTRUCTURE,
    OPT_NOTIFY_IN_TEST_MODE,
    OPT_NOTIFY_SYSTEM,
    OPT_PROFILES,
    OPT_PUSH_DISARM,
    OPT_REMINDER_DELAY,
    OPT_REMINDER_PERSONS,
    OPT_REMINDER_PROFILE,
    OPT_SENSOR_TYPES,
    OPT_SIREN_TEST,
    OPT_SIRENS,
    OPT_SIRENS_HARDWARE_ENABLED,
    OPT_SPEECH,
    OPT_STALE_AFTER_HOURS,
    OPT_USERS,
    OPT_ZONES,
)
from .core.always_active import (
    DEFAULT_SETTLE,
    MAX_SETTLE,
    ArmOnClose,
    parse_always_active,
    parse_arm_on_close,
)
from .core.areas import DEFAULT_ICON as DEFAULT_AREA_ICON
from .core.areas import MAIN_AREA, multi_area, parse_areas, profile_area
from .core.automation import (
    DEFAULT_AWAY_DELAY,
    MAX_AWAY_DELAY,
    WEEKDAYS,
    AutoConfig,
    parse_automation,
)
from .core.controls import ALL_AREAS as CONTROL_ALL_AREAS
from .core.controls import ARM_KEYS as CONTROL_ARM_KEYS
from .core.controls import (
    MAX_LEARN_MINUTES,
    ControlKind,
    learn_minutes,
    normalize_tag,
    parse_controls,
)
from .core.messages import (
    EXAMPLE_VALUES_DE,
    EXAMPLE_VALUES_EN,
    PLACEHOLDERS,
    TemplateError,
    check_template,
    default_speech,
    render,
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
    ProfileInfo,
    profile_behaviour,
    profile_ids,
    profile_info,
    profile_infos,
    profile_settings,
    stale_after_seconds,
)
from .core.reactions import parse_reaction
from .core.rules import DEFAULT_WITHIN as RULE_DEFAULT_WITHIN
from .core.rules import MAX_STEPS as RULE_MAX_STEPS
from .core.rules import MAX_UNLESS as RULE_MAX_UNLESS
from .core.rules import MAX_WITHIN as RULE_MAX_WITHIN
from .core.rules import (
    Finding,
    Rule,
    RuleError,
    RuleResult,
    StepMode,
    describe_rule,
    describe_step,
    from_editable,
    parse_rule,
    parse_rules,
    parse_step,
    profile_findings,
    profile_rule_ids,
    rule_to_data,
    step_form,
    step_from_form,
    to_editable,
    validate_rule,
    wizard_editable,
)
from .core.sensor_types import (
    MONITORED_DOMAINS,
    SensorType,
    default_type,
    excluded_sensors,
    parse_types,
    sensor_type,
)
from .core.sensors import (
    Zone,
    all_configured_sensors,
    parse_zones,
    resolve_zones,
    slugify,
    zone_conflicts,
)
from .core.siren_guard import BURGLAR_TONES, VOLUME_LEVELS
from .core.siren_test import DEFAULT_SECONDS as SIREN_DEFAULT_SECONDS
from .core.siren_test import DEFAULT_TONE as SIREN_DEFAULT_TONE
from .core.siren_test import DEFAULT_VOLUME as SIREN_DEFAULT_VOLUME
from .core.siren_test import MAX_SECONDS as SIREN_MAX_SECONDS
from .core.siren_test import REMINDER_CHOICES as SIREN_TEST_REMINDERS
from .core.siren_test import TONES as SIREN_TONES
from .core.siren_test import VOLUMES as SIREN_VOLUMES
from .core.siren_test import clamp_seconds as clamp_siren_seconds
from .core.siren_test import parse_settings as parse_siren_test
from .core.speech import MAX_REPEAT as SPEECH_MAX_REPEAT
from .core.speech import MODES as SPEECH_MODES
from .core.speech import Candidate, is_speaker, parse_speech, profile_speakers
from .core.state_machine import (
    OpenSensorPolicy,
    UnavailableSensorPolicy,
)
from .core.users import RIGHTS_ALL, RIGHTS_PER_AREA, Action, parse_users, pin_conflicts
from .names import display_name, plain_name
from .runtime import device_class_of, entities_by_label
from .siren_test import SirenTester

SENSOR_DOMAIN = "binary_sensor"
THRESHOLD_DOMAIN = "threshold"
_LOGGER = logging.getLogger(__name__)
TARGET_ALWAYS = "__always__"

FINDING_TEXTS_DE = {
    "rule_no_steps": "Auslöseregel „{rule}“ hat keinen Schritt mit Meldern.",
    "rule_step_empty": "Schritt {step} hat keine Melder (Meldergruppe leer?).",
    "rule_count_too_high": "Schritt {step} verlangt mehr Melder, als er hat ({detail}).",
    "rule_same_sensor_next_step": "Ein Melder steht in Schritt {step} und im Schritt davor.",
    "rule_redundant_single": "Auslöseregel „{rule}“ bewirkt nichts – ihr erster Schritt löst "
    "hier schon allein aus.",
    "rule_single_step_any": "Auslöseregel „{rule}“ hat nur einen Schritt „einer davon“ – das ist "
    "dasselbe wie „allein auslösend“.",
    "rule_contained": "Auslöseregel „{rule}“ bewirkt nichts – „{detail}“ löst immer vorher aus.",
    "rule_unless_empty": "„Nicht, wenn vorher …“ hat keine Melder.",
    "rule_unless_overlaps": "Auslöseregel „{rule}“: „Nicht, wenn vorher …“ enthält Melder aus "
    "Schritt 1 – ein zweites Auslösen kann die Regel selbst sperren.",
    "rule_unless_long": "Auslöseregel „{rule}“: „Nicht, wenn vorher …“ wirkt sehr lange "
    "({detail} s).",
}
FINDING_TEXTS_EN = {
    "rule_no_steps": "Trigger rule “{rule}” has no step with sensors.",
    "rule_step_empty": "Step {step} has no sensors (empty sensor group?).",
    "rule_count_too_high": "Step {step} needs more sensors than it has ({detail}).",
    "rule_same_sensor_next_step": "A sensor is in step {step} and in the step before.",
    "rule_redundant_single": "Trigger rule “{rule}” has no effect – its first step already "
    "triggers alone here.",
    "rule_single_step_any": "Trigger rule “{rule}” has only one “any of” step – same as "
    "“triggers alone”.",
    "rule_contained": "Trigger rule “{rule}” has no effect – “{detail}” always triggers first.",
    "rule_unless_empty": "“Not if before …” has no sensors.",
    "rule_unless_overlaps": "Trigger rule “{rule}”: “not if before …” contains sensors of step 1 – "
    "a second trigger can block the rule itself.",
    "rule_unless_long": "Trigger rule “{rule}”: “not if before …” lasts very long ({detail} s).",
}
SIREN_ENTITY_DOMAIN = "siren"  # nur zur Auswahl im Formular, kein Dienstaufruf


class HauswachtConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 5

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
        self._hints: list[str] = []
        self._rule_id: str | None = None
        self._draft: dict[str, Any] | None = None
        self._draft_step = 0
        self._area_id: str | None = None
        self._event: str | None = None
        self._infos: list[str] = []
        self._type_fields: dict[str, str] = {}
        self._siren_queue: list[str] = []
        self._control_id: str | None = None
        self._control_kind: ControlKind = ControlKind.KEYPAD
        self._user_pending: tuple[str, dict[str, Any]] | None = None
        self._offered_new: set[str] = set()
        self._siren_params: dict[str, Any] = {}
        self._siren_prewarned = False
        self._siren_summary: list[str] = []
        self._siren_by: str | None = None
        self._pending: dict[str, Any] | None = None
        self._notes: list[str] = []

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

    def _german(self) -> bool:
        return (self.hass.config.language or "").startswith("de")

    def _saved_text(self) -> str:
        text = "✅ Gespeichert." if self._german() else "✅ Saved."
        hints, self._hints = self._hints, []
        if hints:
            text += "\n\n" + "\n".join(f"⚠️ {h}" for h in hints)
        infos, self._infos = self._infos, []
        if infos:
            text += "\n\n" + "\n".join(f"ℹ️ {i}" for i in infos)
        notes, self._notes = self._notes, []
        if notes:
            label = "Vorschau" if self._german() else "Preview"
            text += "\n\n" + "\n".join(f"💬 {label}: „{n}“" for n in notes)
        return text + "\n\n"

    def _finding_text(self, finding: Finding) -> str:
        texts = FINDING_TEXTS_DE if self._german() else FINDING_TEXTS_EN
        return texts.get(finding.code, finding.code).format(
            rule=finding.rule, step=finding.step or "", detail=finding.detail
        )

    def _type_of(self, options: Mapping[str, Any], entity_id: str) -> SensorType:
        return sensor_type(entity_id, device_class_of(self.hass, entity_id), parse_types(options))

    def _profile_armed(self, options: Mapping[str, Any], profile_id: str) -> list[str]:
        """Melder, die im Profil einzeln auslösen (Gruppen ohne Technik, ohne Ausnahmen)."""
        sensors = resolve_zones(
            profile_behaviour(options, profile_id).zones,
            parse_zones(options),
            entities_by_label(self.hass),
        )
        excluded = excluded_sensors(options, profile_id)
        return sorted(
            (
                display_name(self.hass, e)
                for e in sensors
                if e not in excluded and self._type_of(options, e) is not SensorType.TECHNICAL
            ),
            key=str.casefold,
        )

    def _armed_text(self, options: Mapping[str, Any], profile_id: str) -> str:
        armed = self._profile_armed(options, profile_id)
        return ", ".join(armed) if armed else "–"

    def _profile_hints(self, options: Mapping[str, Any], profile_id: str) -> list[str]:
        """Hinweise zu Regeln, die im Profil nichts bewirken."""
        zones = parse_zones(options)
        labels = entities_by_label(self.hass)
        rules = parse_rules(options)
        chosen = [rules[r] for r in profile_rule_ids(options, profile_id) if r in rules]
        single = resolve_zones(profile_behaviour(options, profile_id).zones, zones, labels)
        name = profile_info(options, profile_id).name
        return [
            f"{name}: {self._finding_text(f)}"
            for f in profile_findings(single, chosen, zones, labels)
        ]

    def _menu(self, step_id: str, menu_options: list[str]) -> ConfigFlowResult:
        saved, self._saved = self._saved, False
        return self.async_show_menu(
            step_id=step_id,
            menu_options=menu_options,
            description_placeholders={"saved": self._saved_text() if saved else ""},
        )

    def _loaded(self) -> bool:
        return self.config_entry.state is ConfigEntryState.LOADED

    def _is_disarmed(self) -> bool:
        entry = self.config_entry
        if entry.state is not ConfigEntryState.LOADED:
            return True
        # Alle Bereiche müssen unscharf sein (Optionen ändern lädt alles neu)
        return bool(entry.runtime_data.all_disarmed)

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if not self._is_disarmed():
            return self.async_abort(reason="disarm_first")
        return self._menu(
            "init", ["triggering", "profiles", "sirens", "notifications", "system", "done"]
        )

    async def async_step_done(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Schließen. Gespeichert wurde bereits nach jedem Formular."""
        return self.async_create_entry(data=dict(self.config_entry.options))

    async def async_step_system(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self._menu(
            "system",
            [
                "areas",
                "users",
                "controls",
                "sensor_behaviour",
                "infrastructure",
                "homecoming",
                "init",
            ],
        )

    # --- Bereiche ------------------------------------------------------------

    async def async_step_areas(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self._menu("areas", ["area_add", "area_edit", "area_delete", "system"])

    def _area_selector(
        self, *, include_main: bool = True, multiple: bool = False
    ) -> SelectSelector:
        return SelectSelector(
            SelectSelectorConfig(
                options=[
                    SelectOptionDict(value=a.area_id, label=a.name)
                    for a in parse_areas(self.config_entry.options).values()
                    if include_main or a.area_id != MAIN_AREA
                ],
                multiple=multiple,
                mode=SelectSelectorMode.LIST,
            )
        )

    async def async_step_area_add(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        self._area_id = None
        return await self.async_step_area_settings()

    async def async_step_area_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._area_id = user_input["area"]
            return await self.async_step_area_settings()
        return self.async_show_form(
            step_id="area_edit",
            data_schema=vol.Schema({vol.Required("area"): self._area_selector()}),
        )

    async def async_step_area_delete(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        options = dict(self.config_entry.options)
        if not multi_area(options):
            return self.async_abort(reason="no_areas")
        errors: dict[str, str] = {}
        if user_input is not None:
            area_id = user_input["area"]
            used = [
                i.name
                for i in profile_infos(options)
                if profile_area(options, i.profile_id) == area_id
            ]
            if used:
                errors["area"] = "area_has_profiles"
            else:
                options[OPT_AREAS] = {
                    k: v for k, v in options.get(OPT_AREAS, {}).items() if k != area_id
                }
                # Benutzer-Zuordnungen zum gelöschten Bereich entfernen
                users = {k: dict(v) for k, v in options.get(OPT_USERS, {}).items()}
                for data in users.values():
                    if isinstance(data.get("areas"), list):
                        data["areas"] = [a for a in data["areas"] if a != area_id]
                options[OPT_USERS] = users
                return await self._save(options, "areas")
        return self.async_show_form(
            step_id="area_delete",
            data_schema=vol.Schema({vol.Required("area"): self._area_selector(include_main=False)}),
            errors=errors,
        )

    async def async_step_area_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        options = dict(self.config_entry.options)
        areas = parse_areas(options)
        area_id = getattr(self, "_area_id", None)
        current = areas.get(area_id) if area_id else None
        errors: dict[str, str] = {}
        if user_input is not None:
            name = str(user_input.get("name") or "").strip()
            if not name:
                errors["name"] = "area_name_required"
            elif any(
                a.name.casefold() == name.casefold() for a in areas.values() if a.area_id != area_id
            ):
                errors["name"] = "area_name_taken"
            else:
                stored = {k: dict(v) for k, v in options.get(OPT_AREAS, {}).items()}
                new_id = area_id or slugify(name, existing=[*stored.keys(), MAIN_AREA])
                data = stored.get(new_id, {})
                data.update({"name": name, "icon": user_input.get("icon") or DEFAULT_AREA_ICON})
                stored[new_id] = data
                options[OPT_AREAS] = stored
                return await self._save(options, "areas")
        source = user_input or {}
        return self.async_show_form(
            step_id="area_settings",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "name", default=source.get("name", current.name if current else "")
                    ): TextSelector(),
                    vol.Required(
                        "icon",
                        default=source.get("icon", current.icon if current else DEFAULT_AREA_ICON),
                    ): IconSelector(),
                }
            ),
            errors=errors,
            description_placeholders={"area": current.name if current else "–"},
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
                    SelectOptionDict(value=i.profile_id, label=self._profile_label(i))
                    for i in profile_infos(self.config_entry.options)
                ],
                mode=SelectSelectorMode.LIST,
            )
        )

    def _profile_label(self, info: ProfileInfo) -> str:
        options = self.config_entry.options
        if not multi_area(options):
            return info.name
        area = parse_areas(options)[profile_area(options, info.profile_id)]
        return f"{info.name} ({area.name})"

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
        area = user_input.get("area") or (
            profile_area(options, self._profile_id) if self._profile_id else MAIN_AREA
        )
        same_area = [i for i in others if profile_area(options, i.profile_id) == area]
        if mode != PANEL_MODE_NONE and any(i.panel_mode == mode for i in same_area):
            errors["panel_mode"] = "panel_mode_taken"
        chosen = resolve_zones(
            user_input.get("zones") or [], parse_zones(options), entities_by_label(self.hass)
        )
        if set(user_input.get("excluded") or []) - chosen:
            errors["excluded"] = "excluded_not_in_groups"
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
                if "area" in user_input:
                    data["area"] = user_input["area"]
                data.update(
                    {
                        "name": name,
                        "icon": user_input.get("icon") or DEFAULT_ICON,
                        "panel_mode": None if mode == PANEL_MODE_NONE else mode,
                        "exit_delay": int(user_input["exit_delay"]),
                        "entry_delay": int(user_input["entry_delay"]),
                        "reaction_time": int(user_input["reaction_time"]),
                        "zones": [z for z in user_input.get("zones", []) if z in zones],
                        "excluded": sorted(set(user_input.get("excluded") or [])),
                        "rules": [
                            r for r in user_input.get("rules", []) if r in parse_rules(options)
                        ],
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
                        "speakers": list(user_input.get("speakers") or []),
                        **_automation_from_input(user_input.get("automation") or {}),
                        "arm_on_close": _arm_on_close_from_input(
                            user_input.get("arm_on_close") or {}
                        ),
                    }
                )
                profiles[profile_id] = data
                options[OPT_PROFILES] = profiles
                self._hints = self._profile_hints(options, profile_id)
                armed_label = "Scharf in" if self._german() else "Armed in"
                self._infos = [f"{armed_label} {name}: {self._armed_text(options, profile_id)}"]
                return await self._save(options, "profiles")

        pid = self._profile_id or ""
        info = profile_info(options, pid) if self._profile_id else None
        current = profile_settings(options, pid)
        behaviour = profile_behaviour(options, pid)
        reaction = parse_reaction(options, pid)
        source = user_input or {}
        area_field: dict[Any, Any] = {}
        if multi_area(options):
            area_field[
                vol.Required(
                    "area",
                    default=source.get("area", profile_area(options, pid) if pid else MAIN_AREA),
                )
            ] = self._area_selector()
        schema = vol.Schema(
            {
                vol.Required("name", default=source.get("name", info.name if info else "")): (
                    TextSelector()
                ),
                **area_field,
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
                vol.Optional(
                    "excluded", default=sorted(excluded_sensors(options, pid))
                ): EntitySelector(
                    EntitySelectorConfig(
                        include_entities=sorted(
                            all_configured_sensors(zones, entities_by_label(self.hass))
                        ),
                        multiple=True,
                    )
                ),
                vol.Optional(
                    "rules",
                    default=[
                        r for r in profile_rule_ids(options, pid) if r in parse_rules(options)
                    ],
                ): self._rule_selector(multiple=True),
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
                vol.Optional(
                    "speakers", default=list(profile_speakers(options, pid))
                ): self._speaker_selector(),
                # Kein default am Bereich: Sonst füllt die Oberfläche die Felder darin nicht
                # vor, und "OK" bleibt ohne Meldung wirkungslos.
                vol.Optional("automation"): section(
                    _automation_schema(parse_automation(options, pid)),
                    {"collapsed": True},
                ),
                vol.Optional("arm_on_close"): section(
                    _arm_on_close_schema(parse_arm_on_close(options, pid)),
                    {"collapsed": True},
                ),
            }
        )
        return self.async_show_form(
            step_id="profile_settings",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "profile": info.name if info else "–",
                "armed": self._armed_text(options, pid) if pid else "–",
            },
        )

    # --- Regeln ------------------------------------------------------------

    async def async_step_triggering(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Alarmauslösung: Meldergruppen und Auslöseregeln."""
        return self._menu(
            "triggering", ["zones", "rules", "always_active", "helper_create", "init"]
        )

    async def async_step_helper_create(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Assistent: aus einem Messwert einen Schwellenwert-Helfer (Binärsensor) anlegen
        und gleich als Melder einsetzen. Legt nur einen neuen Helfer an, ändert nichts
        Bestehendes."""
        options = dict(self.config_entry.options)
        zones = parse_zones(options)
        errors: dict[str, str] = {}
        if user_input is not None:
            upper, lower = user_input.get("upper"), user_input.get("lower")
            if upper is None and lower is None:
                errors["base"] = "helper_no_limit"
            elif upper is not None and lower is not None and float(lower) > float(upper):
                errors["base"] = "helper_range"
            if not errors:
                entity_id = await self._create_threshold_helper(user_input)
                if entity_id is None:
                    errors["base"] = "helper_failed"
                else:
                    self._place_new_sensor(options, entity_id, user_input)
                    created = "Angelegt" if self._german() else "Created"
                    self._infos = [f"{created}: {entity_id}"]
                    return await self._save(options, "triggering")
        targets = [TARGET_ALWAYS, *zones]
        source = user_input or {}
        schema = vol.Schema(
            {
                vol.Required("source", default=source.get("source", vol.UNDEFINED)): (
                    EntitySelector(EntitySelectorConfig(domain="sensor"))
                ),
                vol.Required("name", default=source.get("name", "")): TextSelector(),
                vol.Optional(
                    "upper", description={"suggested_value": source.get("upper")}
                ): NumberSelector(NumberSelectorConfig(mode=NumberSelectorMode.BOX, step="any")),
                vol.Optional(
                    "lower", description={"suggested_value": source.get("lower")}
                ): NumberSelector(NumberSelectorConfig(mode=NumberSelectorMode.BOX, step="any")),
                vol.Required("hysteresis", default=source.get("hysteresis", 0)): NumberSelector(
                    NumberSelectorConfig(min=0, mode=NumberSelectorMode.BOX, step="any")
                ),
                vol.Required(
                    "type", default=source.get("type", SensorType.TECHNICAL.value)
                ): _select([t.value for t in SensorType], "sensor_type"),
                vol.Required("target", default=source.get("target", TARGET_ALWAYS)): (
                    SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                SelectOptionDict(
                                    value=t,
                                    label=(
                                        ("Immer aktiv" if self._german() else "Always active")
                                        if t == TARGET_ALWAYS
                                        else zones[t].name
                                    ),
                                )
                                for t in targets
                            ],
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    )
                ),
            }
        )
        return self.async_show_form(step_id="helper_create", data_schema=schema, errors=errors)

    async def _create_threshold_helper(self, user_input: Mapping[str, Any]) -> str | None:
        """Schwellenwert-Helfer über den Home-Assistant-Assistenten anlegen.

        Die Entität wird vorab im Register angelegt, damit ihre ID sofort feststeht.
        """
        data: dict[str, Any] = {
            "name": str(user_input["name"]).strip() or "Hauswacht Schwelle",
            "entity_id": user_input["source"],
            "hysteresis": float(user_input.get("hysteresis") or 0),
        }
        for key in ("upper", "lower"):
            if user_input.get(key) is not None:
                data[key] = float(user_input[key])
        try:
            flow = await self.hass.config_entries.flow.async_init(
                THRESHOLD_DOMAIN, context={"source": SOURCE_USER}
            )
            result = await self.hass.config_entries.flow.async_configure(flow["flow_id"], data)
        except Exception:
            _LOGGER.exception("Schwellenwert-Helfer konnte nicht angelegt werden")
            return None
        entry = result.get("result")
        if result.get("type") != "create_entry" or entry is None:
            return None
        registered = er.async_get(self.hass).async_get_or_create(
            "binary_sensor",
            THRESHOLD_DOMAIN,
            entry.entry_id,
            suggested_object_id=data["name"],
            config_entry=entry,
        )
        return registered.entity_id

    def _place_new_sensor(
        self, options: dict[str, Any], entity_id: str, user_input: Mapping[str, Any]
    ) -> None:
        """Neuen Melder mit Typ in eine Meldergruppe oder "immer aktiv" eintragen."""
        types = dict(options.get(OPT_SENSOR_TYPES, {}))
        types[entity_id] = user_input["type"]
        options[OPT_SENSOR_TYPES] = types
        target = user_input["target"]
        if target == TARGET_ALWAYS:
            always = dict(options.get("always_active", {}))
            always["sensors"] = sorted({*always.get("sensors", []), entity_id})
            options["always_active"] = always
            return
        zones = {k: dict(v) for k, v in options.get(OPT_ZONES, {}).items()}
        if target in zones:
            zones[target]["entities"] = sorted({*zones[target].get("entities", []), entity_id})
            options[OPT_ZONES] = zones

    async def async_step_always_active(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Immer aktive Melder: lösen auch im unscharfen Zustand aus."""
        options = dict(self.config_entry.options)
        zones = parse_zones(options)
        registered = [s for s in options.get(OPT_SIRENS, []) if isinstance(s, str)]
        current = parse_always_active(options)
        if user_input is not None:
            options["always_active"] = {
                "zones": [z for z in user_input.get("zones") or [] if z in zones],
                "sensors": list(user_input.get("sensors") or []),
                "sirens_enabled": bool(user_input.get("sirens_enabled")),
                "sirens": [s for s in user_input.get("sirens") or [] if s in registered],
                "siren_tone": user_input.get("siren_tone"),
                "siren_volume": user_input.get("siren_volume"),
                "reaction_time": int(user_input.get("reaction_time") or 180),
            }
            return await self._save(options, "triggering")
        schema = vol.Schema(
            {
                vol.Optional("zones", default=list(current.zones)): _zone_selector(
                    zones, multiple=True
                ),
                vol.Optional("sensors", default=list(current.sensors)): EntitySelector(
                    EntitySelectorConfig(domain=list(MONITORED_DOMAINS), multiple=True)
                ),
                vol.Optional("sirens_enabled", default=current.sirens_enabled): BooleanSelector(),
                vol.Optional("sirens", default=list(current.sirens)): _list_selector(
                    registered, multiple=True
                ),
                vol.Optional("siren_tone", default=current.tone or "burglar"): _select(
                    sorted(BURGLAR_TONES), "siren_tone"
                ),
                vol.Optional("siren_volume", default=current.volume or "high"): _select(
                    list(VOLUME_LEVELS), "siren_volume"
                ),
                vol.Optional("reaction_time", default=current.reaction_time): _seconds(
                    MAX_REACTION_TIME, minimum=1
                ),
            }
        )
        return self.async_show_form(step_id="always_active", data_schema=schema)

    async def async_step_rules(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        saved, self._saved = self._saved, False
        return self.async_show_menu(
            step_id="rules",
            menu_options=["rule_add", "rule_yaml_add", "rule_edit", "rule_delete", "triggering"],
            description_placeholders={
                "saved": self._saved_text() if saved else "",
                "rules": self._rules_list_text(),
            },
        )

    def _rule_selector(self, *, multiple: bool = False) -> SelectSelector:
        rules = parse_rules(self.config_entry.options)
        return SelectSelector(
            SelectSelectorConfig(
                options=[SelectOptionDict(value=r.rule_id, label=r.name) for r in rules.values()],
                multiple=multiple,
                mode=SelectSelectorMode.LIST,
            )
        )

    # Regel-Assistent: Entwurf im Dialog, gespeichert wird erst mit "Fertig – speichern"

    def _rule_text(self, rule: Rule) -> str:
        zones = parse_zones(self.config_entry.options)
        return describe_rule(
            rule,
            lambda e: display_name(self.hass, e),
            lambda z: zones[z].name if z in zones else z,
            "de" if self._german() else "en",
        )

    def _draft_rule(self) -> Rule:
        draft = self._draft or {}
        parsed = parse_rules({"rules": {"entwurf": draft}})
        return parsed.get("entwurf") or Rule(rule_id="entwurf", name="", steps=())

    def _zone_name(self, zone_id: str) -> str:
        zones = parse_zones(self.config_entry.options)
        return zones[zone_id].name if zone_id in zones else zone_id

    def _rules_list_text(self) -> str:
        rules = parse_rules(self.config_entry.options)
        if not rules:
            return "–"
        return "\n".join(f"- **{r.name}:** {self._rule_text(r)}" for r in rules.values())

    def _problems(self, rule: Rule) -> list[Finding]:
        options = self.config_entry.options
        return validate_rule(rule, parse_zones(options), entities_by_label(self.hass))

    async def async_step_rule_add(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        self._rule_id = None
        self._draft = {"name": "", "result": RuleResult.ALARM.value, "steps": []}
        return await self.async_step_rule_meta()

    async def async_step_rule_yaml_add(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        self._rule_id = None
        self._draft = {
            "name": "",
            "result": RuleResult.ALARM.value,
            "steps": [{"any": [], "within": RULE_DEFAULT_WITHIN}],
        }
        return await self.async_step_rule_yaml()

    async def async_step_rule_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        stored = self.config_entry.options.get("rules", {})
        if not stored:
            return self.async_abort(reason="no_rules")
        if user_input is not None:
            self._rule_id = user_input["rule"]
            self._draft = copy.deepcopy(dict(stored[self._rule_id]))
            if not wizard_editable(self._draft_rule()):
                return await self.async_step_rule_yaml()
            return await self.async_step_rule_overview()
        return self.async_show_form(
            step_id="rule_edit",
            data_schema=vol.Schema({vol.Required("rule"): self._rule_selector()}),
        )

    async def async_step_rule_meta(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Name und Ergebnis der Regel."""
        assert self._draft is not None
        errors: dict[str, str] = {}
        if user_input is not None:
            name = str(user_input.get("name") or "").strip()
            rules = parse_rules(self.config_entry.options)
            if not name:
                errors["name"] = "rule_name_required"
            elif any(r.name == name and r.rule_id != self._rule_id for r in rules.values()):
                errors["name"] = "rule_name_taken"
            else:
                self._draft["name"] = name
                self._draft["result"] = user_input.get("result", RuleResult.ALARM.value)
                if not self._draft.get("steps"):
                    self._draft_step = 0
                    return await self.async_step_rule_step()
                return await self.async_step_rule_overview()
        schema = vol.Schema(
            {
                vol.Required("name", default=self._draft.get("name", "")): TextSelector(),
                vol.Required(
                    "result", default=self._draft.get("result", RuleResult.ALARM.value)
                ): _select([r.value for r in RuleResult], "rule_result"),
            }
        )
        return self.async_show_form(step_id="rule_meta", data_schema=schema, errors=errors)

    async def async_step_rule_step(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Einen Schritt anlegen oder bearbeiten (Index in self._draft_step)."""
        assert self._draft is not None
        zones = parse_zones(self.config_entry.options)
        steps: list[dict[str, Any]] = self._draft.setdefault("steps", [])
        index = self._draft_step
        errors: dict[str, str] = {}
        if user_input is not None:
            form = dict(user_input)
            form["zones"] = [z for z in user_input.get("zones") or [] if z in zones]
            if not form.get("sensors") and not form["zones"]:
                errors["base"] = "step_empty"
            else:
                data = step_from_form(form)
                if index < len(steps):
                    steps[index] = data
                else:
                    steps.append(data)
                return await self.async_step_rule_overview()
        current = step_form(parse_step(steps[index])) if index < len(steps) else None
        return self.async_show_form(
            step_id="rule_step",
            data_schema=self._step_schema(current, zones),
            errors=errors,
            description_placeholders={
                "step": str(index + 1),
                "rule_text": self._rule_text(self._draft_rule()),
            },
        )

    async def async_step_rule_unless(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Assistent: "Nicht, wenn vorher …" (einer der Melder in den X s vor Schritt 1)."""
        assert self._draft is not None
        zones = parse_zones(self.config_entry.options)
        rule = self._draft_rule()
        if user_input is not None:
            sensors = list(user_input.get("sensors") or [])
            groups = [z for z in user_input.get("zones") or [] if z in zones]
            if sensors or groups:
                self._draft["unless"] = {
                    "any": [{"sensor": s} for s in sensors] + [{"group": z} for z in groups],
                    "before": int(user_input.get("before") or 300),
                }
            else:
                self._draft.pop("unless", None)
            return await self.async_step_rule_overview()
        current = step_form(parse_step(dict(self._draft["unless"]))) if rule.unless else None
        schema = vol.Schema(
            {
                vol.Optional("sensors", default=(current or {}).get("sensors", [])): (
                    EntitySelector(
                        EntitySelectorConfig(domain=list(MONITORED_DOMAINS), multiple=True)
                    )
                ),
                vol.Optional("zones", default=(current or {}).get("zones", [])): _zone_selector(
                    zones, multiple=True
                ),
                vol.Optional(
                    "before", default=rule.unless.before if rule.unless else 300
                ): _seconds(RULE_MAX_UNLESS, minimum=1),
            }
        )
        return self.async_show_form(
            step_id="rule_unless",
            data_schema=schema,
            description_placeholders={"rule_text": self._rule_text(rule)},
        )

    async def async_step_rule_yaml(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Expertenmodus: die ganze Regel als YAML."""
        assert self._draft is not None
        zones = parse_zones(self.config_entry.options)
        errors: dict[str, str] = {}
        placeholders = {"problem": ""}
        if user_input is not None:
            rules = parse_rules(self.config_entry.options)
            raw = user_input.get("rule")
            name = str(raw.get("name") or "").strip() if isinstance(raw, Mapping) else ""
            rule_id = self._rule_id or slugify(name or "regel", existing=rules.keys())
            try:
                rule, stored = from_editable(raw, zones, rule_id)
            except RuleError as err:
                errors["base"] = "rule_yaml_invalid"
                placeholders["problem"] = str(err)
            else:
                problems = self._problems(rule)
                if any(r.name == rule.name and r.rule_id != rule_id for r in rules.values()):
                    errors["base"] = "rule_name_taken"
                elif problems:
                    errors["base"] = "rule_yaml_invalid"
                    placeholders["problem"] = "; ".join(self._finding_text(f) for f in problems)
                else:
                    self._rule_id = rule_id
                    self._draft = stored
                    return await self.async_step_rule_save()
        rule = self._draft_rule()
        shown = (
            to_editable(rule, self._zone_name)
            if rule.steps
            else {
                "name": self._draft.get("name", ""),
                "result": "alarm",
                "steps": [{"any": [{"group": "…"}], "within": RULE_DEFAULT_WITHIN}],
            }
        )
        default = user_input.get("rule") if user_input else shown
        return self.async_show_form(
            step_id="rule_yaml",
            data_schema=vol.Schema({vol.Required("rule", default=default): ObjectSelector()}),
            errors=errors,
            description_placeholders=placeholders,
        )

    async def async_step_rule_overview(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Zwischenstand der Regel mit allen Möglichkeiten."""
        assert self._draft is not None
        rule = self._draft_rule()
        menu = ["rule_save", "rule_step_add"]
        if rule.steps:
            menu += ["rule_step_edit", "rule_step_remove", "rule_unless"]
        menu += ["rule_meta", "rule_yaml", "rule_cancel"]
        if len(rule.steps) >= RULE_MAX_STEPS:
            menu.remove("rule_step_add")
        problems = self._problems(rule)
        problem_text = "\n".join(f"⚠️ {self._finding_text(f)}" for f in problems)
        return self.async_show_menu(
            step_id="rule_overview",
            menu_options=menu,
            description_placeholders={
                "name": str(self._draft.get("name") or "–"),
                "rule_text": self._rule_text(rule),
                "steps": str(len(rule.steps)),
                "problems": f"\n\n{problem_text}" if problem_text else "",
            },
        )

    async def async_step_rule_step_add(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        assert self._draft is not None
        self._draft_step = len(self._draft.get("steps", []))
        return await self.async_step_rule_step()

    async def async_step_rule_step_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        assert self._draft is not None
        steps = self._draft.get("steps", [])
        if user_input is not None:
            self._draft_step = int(user_input["step"]) - 1
            return await self.async_step_rule_step()
        rule = self._draft_rule()
        language = "de" if self._german() else "en"
        options = [
            SelectOptionDict(
                value=str(number),
                label=f"{number}: "
                + describe_step(
                    step, lambda e: display_name(self.hass, e), self._zone_name, language
                ),
            )
            for number, step in enumerate(rule.steps[: len(steps)], start=1)
        ]
        return self.async_show_form(
            step_id="rule_step_edit",
            data_schema=vol.Schema(
                {
                    vol.Required("step"): SelectSelector(
                        SelectSelectorConfig(options=options, mode=SelectSelectorMode.LIST)
                    )
                }
            ),
        )

    async def async_step_rule_step_remove(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        assert self._draft is not None
        steps = self._draft.get("steps", [])
        if steps:
            steps.pop()
        return await self.async_step_rule_overview()

    async def async_step_rule_cancel(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        self._draft = None
        return await self.async_step_rules()

    async def async_step_rule_save(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        assert self._draft is not None
        options = dict(self.config_entry.options)
        rules = parse_rules(options)
        rule_id = self._rule_id or slugify(
            str(self._draft.get("name") or "regel"), existing=rules.keys()
        )
        try:
            rule = parse_rule(rule_id, self._draft)
        except RuleError:
            return await self.async_step_rule_overview()
        if not rule.steps or self._problems(rule):
            # Nicht speicherbar: zurück zur Übersicht, dort stehen die Gründe
            return await self.async_step_rule_overview()
        stored = {k: dict(v) for k, v in options.get("rules", {}).items()}
        stored[rule_id] = rule_to_data(rule)
        options["rules"] = stored
        self._hints = [
            hint
            for pid in profile_ids(options)
            if rule_id in profile_rule_ids(options, pid)
            for hint in self._profile_hints(options, pid)
        ]
        self._draft = None
        return await self._save(options, "rules")

    async def async_step_rule_delete(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if not parse_rules(self.config_entry.options):
            return self.async_abort(reason="no_rules")
        if user_input is not None:
            rule_id = user_input["rule"]
            options = dict(self.config_entry.options)
            options["rules"] = {k: v for k, v in options.get("rules", {}).items() if k != rule_id}
            profiles = {k: dict(v) for k, v in options.get(OPT_PROFILES, {}).items()}
            for settings in profiles.values():
                if "rules" in settings:
                    settings["rules"] = [r for r in settings["rules"] if r != rule_id]
            options[OPT_PROFILES] = profiles
            return await self._save(options, "rules")
        return self.async_show_form(
            step_id="rule_delete",
            data_schema=vol.Schema({vol.Required("rule"): self._rule_selector()}),
        )

    def _step_schema(self, form: Mapping[str, Any] | None, zones: dict[str, Zone]) -> vol.Schema:
        form = form or {}
        return vol.Schema(
            {
                vol.Optional("sensors", default=list(form.get("sensors", []))): EntitySelector(
                    EntitySelectorConfig(domain=list(MONITORED_DOMAINS), multiple=True)
                ),
                vol.Optional("zones", default=list(form.get("zones", []))): _zone_selector(
                    zones, multiple=True
                ),
                vol.Optional("mode", default=form.get("mode", StepMode.ANY.value)): _select(
                    [m.value for m in StepMode], "step_mode"
                ),
                vol.Optional("count", default=form.get("count", 2)): NumberSelector(
                    NumberSelectorConfig(min=1, max=20, step=1, mode=NumberSelectorMode.BOX)
                ),
                vol.Optional("within", default=form.get("within", RULE_DEFAULT_WITHIN)): _seconds(
                    RULE_MAX_WITHIN, minimum=1
                ),
            }
        )

    # --- Zonen ------------------------------------------------------------

    async def async_step_zones(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self._menu("zones", ["zone_add", "zone_edit", "zone_delete", "triggering"])

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
                    EntitySelectorConfig(domain=list(MONITORED_DOMAINS), multiple=True)
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
        new_zone = Zone(zone_id=new_id, name=name, entities=frozenset(entities), label=label)
        conflicts = zone_conflicts(new_zone, parse_zones(options), entities_by_label(self.hass))
        if conflicts:
            text = ", ".join(
                f"{display_name(self.hass, entity_id)} ({zone})"
                for entity_id, zone in conflicts.items()
            )
            return None, {"base": "zone_overlap"}, {"conflicts": text}
        zones[new_id] = {
            "name": name,
            "entities": sorted(set(entities)),
            "label": label,
        }
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
                return await self._zone_types_start(options, user_input)
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
                return await self._zone_types_start(options, user_input)
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

    async def _zone_types_start(
        self, options: dict[str, Any], user_input: dict[str, Any]
    ) -> ConfigFlowResult:
        """Nach dem Speichern der Gruppe: Typ jedes Melders zeigen und ändern lassen."""
        label = user_input.get("label") or None
        members = set(user_input.get("entities") or [])
        if label:
            members |= entities_by_label(self.hass).get(label, frozenset())
        self._pending = options
        self._type_fields = {}
        for entity_id in sorted(members, key=lambda e: display_name(self.hass, e).casefold()):
            name = display_name(self.hass, entity_id)
            key = name if name not in self._type_fields else f"{name} ({entity_id})"
            self._type_fields[key] = entity_id
        if not self._type_fields:
            return await self._save(options, "zones")
        return await self.async_step_zone_types()

    async def async_step_zone_types(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Typ je Melder: Vorschlag aus der Geräteklasse, Abweichungen werden gespeichert."""
        options = dict(self._pending or self.config_entry.options)
        stored = {k: v for k, v in options.get(OPT_SENSOR_TYPES, {}).items()}
        if user_input is not None:
            for key, entity_id in self._type_fields.items():
                chosen = user_input.get(key)
                proposal = default_type(entity_id, device_class_of(self.hass, entity_id))
                if chosen and chosen != proposal.value:
                    stored[entity_id] = chosen
                else:
                    stored.pop(entity_id, None)
            options[OPT_SENSOR_TYPES] = stored
            self._pending = None
            return await self._save(options, "zones")
        fields: dict[Any, Any] = {}
        for key, entity_id in self._type_fields.items():
            current = self._type_of(options, entity_id)
            fields[vol.Required(key, default=current.value)] = _select(
                [t.value for t in SensorType], "sensor_type"
            )
        return self.async_show_form(step_id="zone_types", data_schema=vol.Schema(fields))

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
        """Funkstille: wie lange ein Melder schweigen darf. Typen stehen in den Meldergruppen."""
        options = dict(self.config_entry.options)
        if user_input is not None:
            options[OPT_STALE_AFTER_HOURS] = int(user_input.get(OPT_STALE_AFTER_HOURS) or 0)
            return await self._save(options, "system")
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
            }
        )
        silence = self.config_entry.runtime_data.silence if self._loaded() else None
        observed = silence.summary_text(self._german()) if silence else "–"
        return self.async_show_form(
            step_id="sensor_behaviour",
            data_schema=schema,
            description_placeholders={"observation": observed},
        )

    # --- Sirenen -----------------------------------------------------------

    async def async_step_sirens(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self._menu("sirens", ["siren_settings", "siren_test", "siren_test_settings", "init"])

    async def async_step_siren_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
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
                return await self._save(options, "sirens")
        schema = vol.Schema(
            {
                vol.Optional(OPT_SIRENS, default=list(options.get(OPT_SIRENS, []))): EntitySelector(
                    EntitySelectorConfig(domain=SIREN_ENTITY_DOMAIN, multiple=True)
                ),
                vol.Required(OPT_SIRENS_HARDWARE_ENABLED, default=was_enabled): BooleanSelector(),
                vol.Optional("confirm_hardware", default=False): BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="siren_settings", data_schema=schema, errors=errors)

    # --- Sirenentest ---------------------------------------------------------

    def _tester(self) -> SirenTester | None:
        entry = self.config_entry
        if entry.state is not ConfigEntryState.LOADED:
            return None
        tester: SirenTester | None = entry.runtime_data.siren_tester
        return tester

    async def async_step_siren_test_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        options = dict(self.config_entry.options)
        current = parse_siren_test(options)
        if user_input is not None:
            options[OPT_SIREN_TEST] = {
                "reminder_months": int(user_input.get("reminder_months") or 0),
                "prewarn": bool(user_input.get("prewarn")),
            }
            return await self._save(options, "sirens")
        return self.async_show_form(
            step_id="siren_test_settings",
            data_schema=vol.Schema(
                {
                    vol.Required("reminder_months", default=str(current.reminder_months)): _select(
                        [str(m) for m in SIREN_TEST_REMINDERS], "siren_test_reminder"
                    ),
                    vol.Required("prewarn", default=current.prewarn): BooleanSelector(),
                }
            ),
        )

    async def async_step_siren_test(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Sirenentest: Sirenen und Werte wählen, dann je Sirene einzeln bestätigen."""
        tester = self._tester()
        if tester is None or not tester.sirens:
            return self.async_abort(reason="no_sirens")
        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input.get("confirm"):
                errors["confirm"] = "siren_test_confirm"
            elif (blocker := tester.blocker()) is not None:
                errors["base"] = blocker
            elif not user_input.get("sirens"):
                errors["sirens"] = "siren_test_none"
            else:
                self._siren_queue = list(user_input["sirens"])
                self._siren_params = {
                    "tone": user_input["tone"],
                    "volume": user_input["volume"],
                    "seconds": clamp_siren_seconds(user_input["duration"]),
                }
                self._siren_prewarned = False
                self._siren_summary = []
                return await self.async_step_siren_test_next()
        return self.async_show_form(
            step_id="siren_test",
            data_schema=vol.Schema(
                {
                    vol.Required("sirens", default=list(tester.sirens)): _list_selector(
                        [
                            SelectOptionDict(value=s, label=display_name(self.hass, s))
                            for s in tester.sirens
                        ],
                        multiple=True,
                    ),
                    vol.Required("tone", default=SIREN_DEFAULT_TONE): _select(
                        list(SIREN_TONES), "siren_tone"
                    ),
                    vol.Required("volume", default=SIREN_DEFAULT_VOLUME): _select(
                        list(SIREN_VOLUMES), "siren_volume"
                    ),
                    vol.Required("duration", default=SIREN_DEFAULT_SECONDS): NumberSelector(
                        NumberSelectorConfig(
                            min=1,
                            max=SIREN_MAX_SECONDS,
                            step=1,
                            unit_of_measurement="s",
                            mode=NumberSelectorMode.SLIDER,
                        )
                    ),
                    vol.Required("confirm", default=False): BooleanSelector(),
                }
            ),
            errors=errors,
            description_placeholders={"last": self._siren_last_text(tester)},
        )

    def _siren_last_text(self, tester: SirenTester) -> str:
        lines = []
        for row in tester.attributes()["sirens"]:
            when = row["last_test"][:16].replace("T", " ") if row["last_test"] else "–"
            heard = {True: "✅", False: "❌", None: ""}[row["heard"]]
            lines.append(f"{row['name']}: {when} {heard}".strip())
        return "; ".join(lines) or "–"

    def _siren_preview(self, tester: SirenTester, siren: str) -> str:
        params = self._siren_params
        decision = tester.preview(siren, params["tone"], params["volume"], params["seconds"])
        if decision.commands:
            command = decision.commands[0]
            parts = [f"Ton {command.tone or 'Standard'}"]
            if command.volume_level is not None:
                parts.append(f"Lautstärke {int(command.volume_level * 100)} %")
            parts.append(f"{params['seconds']} s")
            return "✅ " + ", ".join(parts)
        reason = decision.blocked[0].reason.value if decision.blocked else "blocked"
        return f"⛔ {reason}"

    async def async_step_siren_test_next(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        tester = self._tester()
        if tester is None or not self._siren_queue:
            self._infos = self._siren_summary or ["–"]
            self._saved = True
            return await self.async_step_sirens()
        siren = self._siren_queue[0]
        return self.async_show_menu(
            step_id="siren_test_next",
            menu_options=["siren_test_go", "siren_test_skip", "siren_test_cancel"],
            description_placeholders={
                "siren": display_name(self.hass, siren),
                "preview": self._siren_preview(tester, siren),
                "left": str(len(self._siren_queue)),
            },
        )

    async def async_step_siren_test_go(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        tester = self._tester()
        if tester is None or not self._siren_queue:
            return await self.async_step_siren_test_next()
        siren = self._siren_queue[0]
        params = self._siren_params
        by = None
        if self.context.get("user_id"):
            user = await self.hass.auth.async_get_user(self.context["user_id"])
            by = user.name if user else None
        result = await tester.async_run(
            siren,
            tone=params["tone"],
            volume=params["volume"],
            seconds=params["seconds"],
            by=by,
            prewarn=tester.settings.prewarn and not self._siren_prewarned,
        )
        self._siren_prewarned = True
        if not result["started"]:
            self._siren_summary.append(f"{display_name(self.hass, siren)}: ⛔ {result['reason']}")
            self._siren_queue.pop(0)
            return await self.async_step_siren_test_next()
        await asyncio.sleep(result["seconds"] + 1)
        self._siren_by = by
        return await self.async_step_siren_test_heard()

    async def async_step_siren_test_heard(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        siren = self._siren_queue[0] if self._siren_queue else ""
        return self.async_show_menu(
            step_id="siren_test_heard",
            menu_options=["siren_test_yes", "siren_test_no"],
            description_placeholders={"siren": display_name(self.hass, siren) if siren else "–"},
        )

    async def _siren_answer(self, heard: bool) -> ConfigFlowResult:
        tester = self._tester()
        if tester is not None and self._siren_queue:
            siren = self._siren_queue.pop(0)
            tester.record(
                siren,
                heard,
                by=self._siren_by,
                seconds=self._siren_params["seconds"],
                volume=self._siren_params["volume"],
            )
            mark = "✅" if heard else "❌"
            self._siren_summary.append(f"{display_name(self.hass, siren)}: {mark}")
        return await self.async_step_siren_test_next()

    async def async_step_siren_test_yes(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._siren_answer(True)

    async def async_step_siren_test_no(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._siren_answer(False)

    async def async_step_siren_test_skip(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if self._siren_queue:
            skipped = self._siren_queue.pop(0)
            label = "übersprungen" if self._german() else "skipped"
            self._siren_summary.append(f"{display_name(self.hass, skipped)}: {label}")
        return await self.async_step_siren_test_next()

    async def async_step_siren_test_cancel(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        self._siren_queue = []
        return await self.async_step_siren_test_next()

    # --- Benachrichtigungen --------------------------------------------------

    def _notify_services(self) -> list[SelectOptionDict]:
        """Empfänger: notify-Dienste (z. B. App mit Knöpfen) und Benachrichtigungs-Entitäten
        (z. B. WhatsApp, Telegram, E-Mail – nur Titel und Text)."""
        services = self.hass.services.async_services_for_domain("notify")
        options = [
            SelectOptionDict(value=s, label=s)
            for s in sorted(services)
            if s not in {"send_message", "notify", "persistent_notification"}
        ]
        text_only = " – nur Text" if self._german() else " – text only"
        registry = er.async_get(self.hass)
        for state in sorted(
            self.hass.states.async_all("notify"), key=lambda st: st.name.casefold()
        ):
            entry = registry.async_get(state.entity_id)
            candidate = Candidate(
                state.entity_id,
                entry.unique_id if entry else "",
                entry.translation_key if entry else None,
            )
            if is_speaker(candidate):
                continue  # Lautsprecher stehen unter "Sprachausgabe"
            options.append(
                SelectOptionDict(
                    value=state.entity_id, label=f"{state.name} ({state.entity_id}){text_only}"
                )
            )
        return options

    async def async_step_notifications(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self._menu(
            "notifications",
            ["notify_settings", "notify_texts", "speech", "speech_events", "init"],
        )

    # --- Eigene Texte und Sprachausgabe ------------------------------------------

    def _event_selector(self) -> SelectSelector:
        return _select([e.value for e in NotifyEvent], "notify_event")

    def _example_values(self) -> Mapping[str, str]:
        return EXAMPLE_VALUES_DE if self._german() else EXAMPLE_VALUES_EN

    def _placeholder_help(self) -> str:
        return ", ".join(f"{{{p}}}" for p in PLACEHOLDERS)

    async def async_step_notify_texts(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._event = user_input["event"]
            return await self.async_step_notify_text_edit()
        return self.async_show_form(
            step_id="notify_texts",
            data_schema=vol.Schema({vol.Required("event"): self._event_selector()}),
        )

    async def async_step_notify_text_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        options = dict(self.config_entry.options)
        event = NotifyEvent(self._event or NotifyEvent.ALARM.value)
        events = {k: dict(v) for k, v in options.get(OPT_EVENTS, {}).items()}
        stored = events.get(event.value, {})
        errors: dict[str, str] = {}
        placeholders = {"error": "", "placeholders": self._placeholder_help(), "preview": ""}
        if user_input is not None:
            texts = {k: str(user_input.get(k) or "").strip() for k in ("title", "message")}
            for key, text in texts.items():
                try:
                    check_template(text)
                except TemplateError as err:
                    errors[key] = "invalid_template"
                    placeholders["error"] = str(err)
            if not errors:
                for key, text in texts.items():
                    if text:
                        stored[key] = text
                    else:
                        stored.pop(key, None)
                events[event.value] = stored
                options[OPT_EVENTS] = events
                example = {**self._example_values()}
                if texts["message"]:
                    self._notes.append(render(texts["message"], example))
                return await self._save(options, "notifications")
        current = stored.get("message")
        if isinstance(current, str) and current:
            placeholders["preview"] = render(current, self._example_values())
        return self.async_show_form(
            step_id="notify_text_edit",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "title", description={"suggested_value": stored.get("title", "")}
                    ): TextSelector(),
                    vol.Optional(
                        "message", description={"suggested_value": stored.get("message", "")}
                    ): TextSelector(TextSelectorConfig(multiline=True)),
                }
            ),
            errors=errors,
            description_placeholders=placeholders,
        )

    def _speaker_selector(self) -> DeviceSelector:
        return DeviceSelector(DeviceSelectorConfig(entity=[{"domain": "notify"}], multiple=True))

    async def async_step_speech(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        options = dict(self.config_entry.options)
        raw = dict(options.get(OPT_SPEECH, {}))
        config = parse_speech(options)
        if user_input is not None:
            raw["speakers"] = list(user_input.get("speakers") or [])
            raw["repeat"] = int(user_input.get("repeat") or 0)
            raw["quiet"] = {
                "enabled": bool(user_input.get("quiet_enabled")),
                "start": str(user_input.get("quiet_start") or "22:00")[:5],
                "end": str(user_input.get("quiet_end") or "07:00")[:5],
            }
            options[OPT_SPEECH] = raw
            return await self._save(options, "notifications")
        return self.async_show_form(
            step_id="speech",
            data_schema=vol.Schema(
                {
                    vol.Optional("speakers", default=list(config.speakers)): (
                        self._speaker_selector()
                    ),
                    vol.Required("repeat", default=config.repeat): NumberSelector(
                        NumberSelectorConfig(
                            min=0,
                            max=SPEECH_MAX_REPEAT,
                            step=5,
                            unit_of_measurement="s",
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Required("quiet_enabled", default=config.quiet_enabled): (
                        BooleanSelector()
                    ),
                    vol.Required(
                        "quiet_start", default=config.quiet_start.strftime("%H:%M:00")
                    ): TimeSelector(),
                    vol.Required(
                        "quiet_end", default=config.quiet_end.strftime("%H:%M:00")
                    ): TimeSelector(),
                }
            ),
        )

    async def async_step_speech_events(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._event = user_input["event"]
            return await self.async_step_speech_event_edit()
        return self.async_show_form(
            step_id="speech_events",
            data_schema=vol.Schema({vol.Required("event"): self._event_selector()}),
        )

    async def async_step_speech_event_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        options = dict(self.config_entry.options)
        event = NotifyEvent(self._event or NotifyEvent.ALARM.value)
        setting = parse_speech(options).events[event]
        default_text = default_speech(event, german=self._german())
        errors: dict[str, str] = {}
        placeholders = {
            "error": "",
            "placeholders": self._placeholder_help(),
            "default": default_text,
            "preview": render(setting.text or default_text, self._example_values()),
        }
        if user_input is not None and "mode" in user_input:
            text = str(user_input.get("text") or "").strip()
            try:
                check_template(text)
            except TemplateError as err:
                errors["text"] = "invalid_template"
                placeholders["error"] = str(err)
            if not errors:
                raw = dict(options.get(OPT_SPEECH, {}))
                stored_events = {k: dict(v) for k, v in raw.get("events", {}).items()}
                stored_events[event.value] = {
                    "enabled": bool(user_input.get("enabled")),
                    "mode": user_input["mode"],
                    "speakers": list(user_input.get("speakers") or []),
                    "in_quiet": bool(user_input.get("in_quiet")),
                    "text": text,
                }
                raw["events"] = stored_events
                options[OPT_SPEECH] = raw
                self._notes.append(render(text or default_text, self._example_values()))
                return await self._save(options, "notifications")
        return self.async_show_form(
            step_id="speech_event_edit",
            data_schema=vol.Schema(
                {
                    vol.Required("enabled", default=setting.enabled): BooleanSelector(),
                    vol.Required("mode", default=setting.mode): _select(
                        list(SPEECH_MODES), "speech_mode"
                    ),
                    vol.Optional("speakers", default=list(setting.speakers)): (
                        self._speaker_selector()
                    ),
                    vol.Required("in_quiet", default=setting.in_quiet): BooleanSelector(),
                    vol.Optional("text", description={"suggested_value": setting.text}): (
                        TextSelector(TextSelectorConfig(multiline=True))
                    ),
                }
            ),
            errors=errors,
            description_placeholders=placeholders,
        )

    async def async_step_notify_settings(
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
                    # Eigene Texte (title/message) behalten
                    events[event.value] = {
                        **options.get(OPT_EVENTS, {}).get(event.value, {}),
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
            return await self._save(options, "notifications")

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
        return self.async_show_form(step_id="notify_settings", data_schema=vol.Schema(fields))

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
            tag_list = _tag_input(user_input.get("tags"))
            if (tag_error := self._tag_error(tag_list, user_id, stored_all, current)) is not None:
                errors["tags"], placeholders["conflict"] = tag_error
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
                scope = user_input.get("rights", RIGHTS_ALL)
                if scope == RIGHTS_ALL:
                    data["rights"] = RIGHTS_ALL
                    data.pop("areas", None)
                    data.pop("area_rights", None)
                data["tags"] = tag_list
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
                if scope == RIGHTS_PER_AREA:
                    self._user_pending = (new_id, new_options)
                    return await self.async_step_user_area_rights()
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

    async def async_step_user_area_rights(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Rechte je Bereich: für jeden Bereich, was der Benutzer dort darf."""
        assert self._user_pending is not None
        user_id, options = self._user_pending
        users = dict(options[OPT_USERS])
        data = dict(users[user_id])
        areas = parse_areas(options)
        if user_input is not None:
            data["rights"] = RIGHTS_PER_AREA
            data["area_rights"] = {
                area.area_id: [a for a in user_input.get(area.name, []) if a in RIGHT_VALUES]
                for area in areas.values()
            }
            data.pop("areas", None)
            users[user_id] = data
            new_options = dict(options)
            new_options[OPT_USERS] = users
            self._user_pending = None
            return await self._save(new_options, "users")
        current = _area_rights_defaults(data, list(areas))
        fields: dict[Any, Any] = {
            vol.Optional(area.name, default=current[area.area_id]): SelectSelector(
                SelectSelectorConfig(
                    options=list(RIGHT_VALUES),
                    multiple=True,
                    translation_key="user_right",
                    mode=SelectSelectorMode.LIST,
                )
            )
            for area in areas.values()
        }
        return self.async_show_form(
            step_id="user_area_rights",
            data_schema=vol.Schema(fields),
            description_placeholders={"name": str(data.get("name", user_id))},
        )

    # --- Bedienteile ---------------------------------------------------------

    async def async_step_controls(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self._menu(
            "controls",
            [
                "control_add_keypad",
                "control_add_sticker",
                "control_add_reader",
                "control_edit",
                "control_delete",
                "control_learn",
                "system",
            ],
        )

    async def async_step_control_learn(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Anlernzeit für neue Karten (0 = Anlernen aus)."""
        if user_input is not None:
            options = dict(self.config_entry.options)
            options[OPT_CARD_LEARN_MINUTES] = int(user_input[OPT_CARD_LEARN_MINUTES])
            return await self._save(options, "controls")
        current = learn_minutes(self.config_entry.options)
        return self.async_show_form(
            step_id="control_learn",
            data_schema=vol.Schema(
                {
                    vol.Required(OPT_CARD_LEARN_MINUTES, default=current): NumberSelector(
                        NumberSelectorConfig(
                            min=0,
                            max=MAX_LEARN_MINUTES,
                            step=1,
                            unit_of_measurement="min",
                            mode=NumberSelectorMode.BOX,
                        )
                    )
                }
            ),
        )

    async def async_step_control_add_keypad(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        self._control_id, self._control_kind = None, ControlKind.KEYPAD
        return await self.async_step_control_settings()

    async def async_step_control_add_sticker(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        self._control_id, self._control_kind = None, ControlKind.STICKER
        return await self.async_step_control_settings()

    async def async_step_control_add_reader(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        self._control_id, self._control_kind = None, ControlKind.READER
        return await self.async_step_control_settings()

    def _control_selector(self) -> SelectSelector:
        return SelectSelector(
            SelectSelectorConfig(
                options=[
                    SelectOptionDict(value=c.control_id, label=c.name)
                    for c in parse_controls(self.config_entry.options).values()
                ],
                mode=SelectSelectorMode.LIST,
            )
        )

    async def async_step_control_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        controls = parse_controls(self.config_entry.options)
        if not controls:
            return self.async_abort(reason="no_controls")
        if user_input is not None:
            self._control_id = user_input["control"]
            self._control_kind = controls[self._control_id].kind
            return await self.async_step_control_settings()
        return self.async_show_form(
            step_id="control_edit",
            data_schema=vol.Schema({vol.Required("control"): self._control_selector()}),
        )

    async def async_step_control_delete(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if not parse_controls(self.config_entry.options):
            return self.async_abort(reason="no_controls")
        if user_input is not None:
            options = dict(self.config_entry.options)
            options[OPT_CONTROLS] = {
                k: v for k, v in options.get(OPT_CONTROLS, {}).items() if k != user_input["control"]
            }
            return await self._save(options, "controls")
        return self.async_show_form(
            step_id="control_delete",
            data_schema=vol.Schema({vol.Required("control"): self._control_selector()}),
        )

    def _control_area_selector(self) -> SelectSelector:
        areas = parse_areas(self.config_entry.options)
        everything = "Alle Bereiche" if self._german() else "All areas"
        return SelectSelector(
            SelectSelectorConfig(
                options=[
                    SelectOptionDict(value=CONTROL_ALL_AREAS, label=everything),
                    *(SelectOptionDict(value=a.area_id, label=a.name) for a in areas.values()),
                ],
                mode=SelectSelectorMode.DROPDOWN,
            )
        )

    def _control_profile_selector(self) -> SelectSelector:
        return SelectSelector(
            SelectSelectorConfig(
                options=[
                    SelectOptionDict(value=i.profile_id, label=self._profile_label(i))
                    for i in profile_infos(self.config_entry.options)
                ],
                mode=SelectSelectorMode.DROPDOWN,
            )
        )

    def _validate_control(self, kind: ControlKind, data: dict[str, Any]) -> dict[str, str]:
        errors: dict[str, str] = {}
        options = self.config_entry.options
        area = data.get("area") or CONTROL_ALL_AREAS
        profiles = [data.get("profile")] if kind is not ControlKind.KEYPAD else []
        if kind is ControlKind.KEYPAD:
            profiles = [data.get(k) for k in CONTROL_ARM_KEYS]
            if not str(data.get("topic") or "").strip().strip("/"):
                errors["topic"] = "control_topic"
        elif data.get("action") in ("arm", "toggle") and not data.get("profile"):
            errors["profile"] = "control_profile_required"
        if kind is ControlKind.STICKER and not normalize_tag(data.get("tag")):
            errors["tag"] = "control_tag"
        if kind is ControlKind.READER and not data.get("device"):
            errors["device"] = "control_device"
        for profile in profiles:
            if profile and area != CONTROL_ALL_AREAS and profile_area(options, profile) != area:
                errors["base"] = "control_profile_area"
        return errors

    async def async_step_control_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        kind = self._control_kind
        stored = dict(self.config_entry.options.get(OPT_CONTROLS, {}))
        current: dict[str, Any] = dict(stored.get(self._control_id or "", {}))
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = self._validate_control(kind, user_input)
            if not errors:
                data: dict[str, Any] = {
                    "name": str(user_input.get("name") or "").strip() or kind.value,
                    "kind": kind.value,
                    "area": user_input.get("area") or CONTROL_ALL_AREAS,
                }
                if kind is ControlKind.KEYPAD:
                    data["topic"] = str(user_input["topic"]).strip().rstrip("/")
                    data["buttons"] = {
                        k: user_input[k] for k in CONTROL_ARM_KEYS if user_input.get(k)
                    }
                    data["login"] = user_input.get("login", "pin_or_card")
                    data["emergency"] = user_input.get("emergency", "off")
                else:
                    data["action"] = user_input.get("action", "disarm")
                    data["profile"] = user_input.get("profile") or None
                if kind is ControlKind.STICKER:
                    data["tag"] = normalize_tag(user_input.get("tag"))
                if kind is ControlKind.READER:
                    data["device"] = user_input.get("device")
                    data["login"] = user_input.get("login", "card")
                control_id = self._control_id or slugify(data["name"], existing=list(stored))
                stored[control_id] = data
                options = dict(self.config_entry.options)
                options[OPT_CONTROLS] = stored
                return await self._save(options, "controls")
        source = {**current, **(user_input or {})}
        buttons = current.get("buttons", {})
        fields: dict[Any, Any] = {
            vol.Required("name", default=source.get("name", "")): TextSelector(),
            vol.Required("area", default=source.get("area", CONTROL_ALL_AREAS)): (
                self._control_area_selector()
            ),
        }
        if kind is ControlKind.KEYPAD:
            fields[vol.Required("topic", default=source.get("topic", "zigbee2mqtt/"))] = (
                TextSelector()
            )
            for key in CONTROL_ARM_KEYS:
                fields[vol.Optional(key, description={"suggested_value": buttons.get(key)})] = (
                    self._control_profile_selector()
                )
            fields[vol.Required("login", default=source.get("login", "pin_or_card"))] = _select(
                ["pin_or_card", "card_and_pin"], "control_login"
            )
            fields[vol.Required("emergency", default=source.get("emergency", "off"))] = _select(
                ["off", "silent", "alarm"], "control_emergency"
            )
        else:
            if kind is ControlKind.STICKER:
                fields[vol.Required("tag", default=source.get("tag", ""))] = TextSelector()
            else:
                fields[vol.Required("device", default=source.get("device", vol.UNDEFINED))] = (
                    DeviceSelector(DeviceSelectorConfig())
                )
            fields[vol.Required("action", default=source.get("action", "disarm"))] = _select(
                ["disarm", "arm", "toggle"], "control_action"
            )
            fields[
                vol.Optional("profile", description={"suggested_value": source.get("profile")})
            ] = self._control_profile_selector()
            if kind is ControlKind.READER:
                fields[vol.Required("login", default=source.get("login", "card"))] = _select(
                    ["card", "card_and_pin"], "control_login"
                )
        return self.async_show_form(
            step_id=f"control_{kind.value}",
            data_schema=vol.Schema(fields),
            errors=errors,
        )

    async def async_step_control_keypad(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self.async_step_control_settings(user_input)

    async def async_step_control_sticker(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self.async_step_control_settings(user_input)

    async def async_step_control_reader(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self.async_step_control_settings(user_input)

    # --- Heimkehr-Beobachtung ---------------------------------------------

    async def async_step_homecoming(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        options = dict(self.config_entry.options)
        if user_input is not None:
            options[OPT_HOMECOMING_OBSERVE] = bool(user_input.get(OPT_HOMECOMING_OBSERVE))
            options[OPT_HOMECOMING_PERSONS] = list(user_input.get(OPT_HOMECOMING_PERSONS) or [])
            options[OPT_HOMECOMING_SSIDS] = [
                part.strip()
                for part in str(user_input.get(OPT_HOMECOMING_SSIDS) or "").split(",")
                if part.strip()
            ]
            if not options[OPT_HOMECOMING_PERSONS]:
                return await self._save(options, "system")
            self._pending = options
            return await self.async_step_homecoming_signals()
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
                vol.Optional(
                    OPT_HOMECOMING_SSIDS,
                    description={
                        "suggested_value": ", ".join(options.get(OPT_HOMECOMING_SSIDS, []))
                    },
                ): TextSelector(),
            }
        )
        return self.async_show_form(step_id="homecoming", data_schema=schema)

    async def async_step_homecoming_signals(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Zusätzliche Signale je Person (WLAN, Bluetooth, Annäherung …) – nur Beobachtung."""
        options = dict(self._pending or self.config_entry.options)
        persons = list(options.get(OPT_HOMECOMING_PERSONS, []))
        fields: dict[str, str] = {}
        for person in persons:
            name = plain_name(self.hass, person)
            fields[name if name not in fields else f"{name} ({person})"] = person
        stored = dict(options.get(OPT_HOMECOMING_SIGNALS, {}))
        if user_input is not None:
            options[OPT_HOMECOMING_SIGNALS] = {
                person: sorted(set(user_input.get(key) or []))
                for key, person in fields.items()
                if user_input.get(key)
            }
            self._pending = None
            return await self._save(options, "system")
        schema = vol.Schema(
            {
                vol.Optional(key, default=list(stored.get(person, []))): EntitySelector(
                    EntitySelectorConfig(
                        domain=["device_tracker", "binary_sensor", "sensor"], multiple=True
                    )
                )
                for key, person in fields.items()
            }
        )
        return self.async_show_form(step_id="homecoming_signals", data_schema=schema)

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

    def _tags_field(self, current: dict[str, Any]) -> dict[Any, Any]:
        """Beliebig viele Karten/Chips: eigene plus zuletzt gelesene unbekannte zum Anlernen."""
        stored = current.get("tags", [])
        tags = [t for t in stored if isinstance(t, str)] if isinstance(stored, list) else []
        options = [SelectOptionDict(value=t, label=t) for t in tags]
        unknown = self._unknown_cards()
        self._offered_new = set(unknown) - set(tags)
        de = self._german()
        for tag, (source, when) in unknown.items():
            if tag in tags:
                continue
            time_text = dt_util.as_local(dt_util.utc_from_timestamp(when)).strftime("%H:%M")
            hint = (
                f"neu, gelesen an {source} um {time_text}"
                if de
                else f"new, read at {source} at {time_text}"
            )
            options.append(SelectOptionDict(value=tag, label=f"{tag} ({hint})"))
        return {
            vol.Optional("tags", default=tags): SelectSelector(
                SelectSelectorConfig(
                    options=options,
                    multiple=True,
                    custom_value=True,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )
        }

    def _tag_error(
        self,
        tags: list[str],
        user_id: str | None,
        stored: Mapping[str, Any],
        current: Mapping[str, Any],
    ) -> tuple[str, str] | None:
        """Karte gehört schon jemand anderem, oder eine angebotene neue Karte ist abgelaufen."""
        if (owner := _tag_owner(tags, user_id, stored)) is not None:
            return "tag_taken", owner
        own = set(current.get("tags", []) or [])
        expired = (set(tags) - own) & self._offered_new - set(self._unknown_cards())
        if expired:
            return "card_expired", ", ".join(sorted(expired))
        return None

    def _unknown_cards(self) -> dict[str, tuple[str, float]]:
        """Zuletzt an Keypads/Lesern gelesene unbekannte Karten (nur wenn geladen)."""
        if not self._loaded():
            return {}
        controls = getattr(self.config_entry.runtime_data, "controls", None)
        return controls.learnable_cards() if controls is not None else {}

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
                **self._user_area_field(current),
                **self._tags_field(current),
            }
        )

    def _user_area_field(self, current: dict[str, Any]) -> dict[Any, Any]:
        """Rechte für alle Bereiche gleich oder je Bereich (nur bei mehreren Bereichen)."""
        if not multi_area(self.config_entry.options):
            return {}
        return {
            vol.Required("rights", default=_rights_scope(current)): _select(
                [RIGHTS_ALL, RIGHTS_PER_AREA], "user_rights_scope"
            )
        }


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


def _arm_on_close_schema(current: ArmOnClose) -> vol.Schema:
    """Scharf durch Schließen der Tür (alles optional)."""
    return vol.Schema(
        {
            vol.Optional("enabled", default=current.enabled): BooleanSelector(),
            vol.Optional("doors", default=sorted(current.doors)): EntitySelector(
                EntitySelectorConfig(domain=list(MONITORED_DOMAINS), multiple=True)
            ),
            vol.Optional("settle", default=current.settle): _seconds(MAX_SETTLE, minimum=1),
        }
    )


def _arm_on_close_from_input(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "enabled": bool(data.get("enabled", False)),
        "doors": [d for d in data.get("doors") or [] if isinstance(d, str)],
        "settle": int(data.get("settle") or DEFAULT_SETTLE),
    }


def _automation_from_input(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "auto_arm_time": data.get("auto_arm_time") or None,
        "auto_disarm_time": data.get("auto_disarm_time") or None,
        "auto_weekdays": [d for d in data.get("auto_weekdays", []) if d in WEEKDAYS],
        "auto_away_persons": list(data.get("auto_away_persons") or []),
        "auto_away_delay": int(data.get("auto_away_delay", DEFAULT_AWAY_DELAY)),
        "auto_disarm_on_arrival": bool(data.get("auto_disarm_on_arrival", False)),
    }


RIGHT_VALUES = (Action.ARM.value, Action.DISARM.value, Action.END_ALARM.value)


def _tag_input(value: Any) -> list[str]:
    """Karten aus der Auswahl (Liste) oder – wie früher – als Text mit Komma."""
    items = value if isinstance(value, list) else str(value or "").split(",")
    return list(dict.fromkeys(t for t in (normalize_tag(i) for i in items) if t))


def _tag_owner(tags: list[str], user_id: str | None, stored: Mapping[str, Any]) -> str | None:
    """Gehört eine dieser Karten schon einem anderen Benutzer? Dann dessen Name."""
    for other_id, other in stored.items():
        if other_id != user_id and set(tags) & set(other.get("tags", []) or []):
            return str(other.get("name", other_id))
    return None


def _rights_scope(current: Mapping[str, Any]) -> str:
    """Bisherige Einschränkung auf Bereiche (vor 0.29) zählt als "je Bereich"."""
    if current.get("rights") in (RIGHTS_ALL, RIGHTS_PER_AREA):
        return str(current["rights"])
    return RIGHTS_PER_AREA if current.get("areas") else RIGHTS_ALL


def _area_rights_defaults(data: Mapping[str, Any], area_ids: list[str]) -> dict[str, list[str]]:
    """Vorbelegung je Bereich: gespeicherte Rechte, sonst die allgemeinen Rechte."""
    stored = data.get("area_rights")
    if isinstance(stored, Mapping) and data.get("rights") == RIGHTS_PER_AREA:
        return {
            a: [r for r in stored.get(a, []) if r in RIGHT_VALUES]
            if isinstance(stored.get(a), list)
            else []
            for a in area_ids
        }
    general = [
        right
        for right, key in zip(RIGHT_VALUES, ("can_arm", "can_disarm", "can_end_alarm"), strict=True)
        if data.get(key, True)
    ]
    limited = data.get("areas") if isinstance(data.get("areas"), list) else []
    return {a: list(general) if not limited or a in limited else [] for a in area_ids}


def _select(options: list[str], translation_key: str) -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=options, translation_key=translation_key, mode=SelectSelectorMode.DROPDOWN
        )
    )


def _list_selector(
    values: list[str] | list[SelectOptionDict], *, multiple: bool = False, custom: bool = False
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
