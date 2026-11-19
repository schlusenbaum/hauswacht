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
from homeassistant.helpers import device_registry as dr
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

from . import menu_lists
from .const import (
    DOMAIN,
    MASTER_USER_ID,
    MASTER_USER_NAME,
    NAME,
    OPT_AREAS,
    OPT_BUTTONS_WITHOUT_PIN,
    OPT_CARD_LEARN_MINUTES,
    OPT_CARD_PIN_UNLINKED,
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
    OPT_SETTINGS_PAGE,
    OPT_SIREN_FIRE_TONE_OK,
    OPT_SIREN_TEST,
    OPT_SIREN_TONES,
    OPT_SIRENS,
    OPT_SIRENS_ALLOW_SWITCH,
    OPT_SIRENS_HARDWARE_ENABLED,
    OPT_SPEECH,
    OPT_STALE_AFTER_HOURS,
    OPT_USERS,
    OPT_ZONES,
)
from .core.action_codes import (
    ACTION_CODE_KEYS,
    ALL_KEYPADS,
    OPT_ACTION_CODES,
    ActionCode,
    CodeAction,
    action_code_clash,
    is_action_code,
    is_valid_action_code,
    parse_action_codes,
)
from .core.always_active import (
    MAX_SETTLE,
    ArmOnClose,
    parse_always_active,
    parse_arm_on_close,
)
from .core.areas import DEFAULT_ICON as DEFAULT_AREA_ICON
from .core.areas import MAIN_AREA, multi_area, parse_areas, profile_area
from .core.automation import (
    ARRIVAL_MODES,
    MAX_ARRIVAL_WINDOW,
    MAX_AWAY_DELAY,
    WEEKDAYS,
    AutoConfig,
    parse_automation,
)
from .core.changes.areas import save_area
from .core.changes.cards import all_cards as _all_cards
from .core.changes.cards import put_card as _put_card
from .core.changes.cards import remove_card as _remove_card
from .core.changes.cards import tag_owner as _tag_owner
from .core.changes.controls import GENERIC_BUTTON_FIELDS, validate_control
from .core.changes.controls import control_data as _control_data
from .core.changes.notifications import save_event_text, save_notify_settings
from .core.changes.profiles import delete_profile, save_profile
from .core.changes.sensors import (
    STALE_DEFAULT,
    STALE_HOURS,
    STALE_MODES,
    STALE_OFF,
    save_stale_override,
)
from .core.changes.sirens import save_sirens
from .core.changes.users import (
    RIGHT_VALUES,
    delete_user,
    save_user,
    set_area_rights,
    set_pins,
    unique_user_id,
    validate_user_name,
)
from .core.changes.zones import delete_zone, save_zone
from .core.controls import ALL_AREAS as CONTROL_ALL_AREAS
from .core.controls import ARM_KEYS as CONTROL_ARM_KEYS
from .core.controls import (
    KEY_ALL,
    KEY_DAY,
    KEY_DISARM,
    KEY_NIGHT,
    MAX_LEARN_MINUTES,
    ControlKind,
    is_random_uid,
    learn_minutes,
    lock_id_label,
    normalize_tag,
    parse_controls,
)
from .core.default_texts import default_message, default_title
from .core.keypad_input import DEFAULT_GENERIC_BUTTONS
from .core.messages import (
    EXAMPLE_VALUES_DE,
    EXAMPLE_VALUES_EN,
    TemplateError,
    check_template,
    default_speech,
    placeholder_names,
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
    stale_override_hours,
)
from .core.reactions import parse_reaction
from .core.restart import ARMED as RESTART_ARMED
from .core.restart import BEHAVIORS as RESTART_BEHAVIORS
from .core.restart import DEFAULT_BEHAVIOR as DEFAULT_RESTART_BEHAVIOR
from .core.restart import (
    OPT_RESTART_BEHAVIOR,
    OPT_RESTART_CONTINUE_ALARM,
    OPT_RESTART_PROFILES,
    continue_alarm,
    restart_behavior,
)
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
    domain_of,
    excluded_sensors,
    sensor_type,
)
from .core.sensors import (
    Zone,
    all_configured_sensors,
    parse_zones,
    resolve_zone,
    resolve_zones,
    slugify,
)
from .core.silence import format_duration as format_silence
from .core.siren_guard import BURGLAR_TONES, VOLUME_LEVELS, is_fire_tone
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
from .core.tilt import (
    OPT_TILT_SENSORS,
    delete_tilt_source,
    effective_types,
    known_values,
    parse_tilt_sources,
    save_tilt_source,
    suggest,
)
from .core.tilt import STATE_DOMAINS as TILT_STATE_DOMAINS
from .core.users import RIGHTS_ALL, RIGHTS_PER_AREA, parse_users, pin_conflicts
from .core.vibration import MAX_COUNT as VIBRATION_MAX_COUNT
from .core.vibration import MAX_WINDOW as VIBRATION_MAX_WINDOW
from .core.vibration import MIN_WINDOW as VIBRATION_MIN_WINDOW
from .core.vibration import STRENGTH_DOMAINS as VIBRATION_STRENGTH_DOMAINS
from .core.vibration import (
    delete_vibration_source,
    parse_vibration_sources,
    rule_for_zone_id,
    save_vibration_source,
    save_zone_rule,
)
from .names import display_name, plain_name
from .runtime import device_class_of, entities_by_label
from .siren_test import SirenTester
from .wizard import WizardSteps

SENSOR_DOMAIN = "binary_sensor"
THRESHOLD_DOMAIN = "threshold"
# Home-Assistant-Helfer "Gerätetyp eines Schalters ändern" (Schalter → Sirene)
SWITCH_AS_X_DOMAIN = "switch_as_x"
AUTO_TONE = "_auto"  # Ton je Sirene: Standard-Einbruchton
_LOGGER = logging.getLogger(__name__)
TARGET_ALWAYS = "__always__"
TARGET_NONE = "__none__"

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


# "Neue Karte anlernen" in der Kartenliste; so lange wartet der Dialog aufs Hinhalten
CARD_NEW = "__new__"
# Basis-Topic von Zigbee2MQTT (Standard); abweichend: Topic im Keypad-Formular selbst eintragen
Z2M_BASE_TOPIC = "zigbee2mqtt"
ACTION_CODE_NEW = "__new__"
# "Kartennummer eintippen": ohne Warten, mit den zuletzt gelesenen Karten zur Auswahl
CARD_TYPE = "__type__"
CARD_WAIT_SECONDS = 120


class HauswachtConfigFlow(ConfigFlow, WizardSteps, domain=DOMAIN):
    """Erstinstallation: wahlweise gleich mit dem Einrichtungsassistenten (ADR 0009)."""

    VERSION = 5

    _wiz_options: dict[str, Any] | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self.async_show_menu(step_id="user", menu_options=["wizard", "plain"])

    async def async_step_plain(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self.async_create_entry(title=NAME, data={}, options={})

    def _wizard_options(self) -> Mapping[str, Any]:
        return self._wiz_options or {}

    async def _wizard_store(self, options: dict[str, Any], next_step: str) -> ConfigFlowResult:
        self._wiz_options = options
        step = getattr(self, f"async_step_{next_step}")
        result: ConfigFlowResult = await step()
        return result

    async def _wizard_finish(self) -> ConfigFlowResult:
        return self.async_create_entry(title=NAME, data={}, options=dict(self._wizard_options()))

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


class HauswachtOptionsFlow(OptionsFlow, WizardSteps):
    """Optionen: PIN und Profilzeiten. Nur im unscharfen Zustand änderbar."""

    def __init__(self) -> None:
        self._profile_id: str | None = None
        self._zone_id: str | None = None
        self._tilt_draft: dict[str, Any] = {}
        self._vibration_edit: str | None = None
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
        self._siren_tone_target: str | None = None
        self._control_id: str | None = None
        self._control_kind: ControlKind = ControlKind.KEYPAD
        self._user_pending: tuple[str, dict[str, Any]] | None = None
        self._offered_new: set[str] = set()
        self._card: str | None = None
        self._action_code: str | None = None
        self._new_card: str | None = None
        self._card_task: asyncio.Task[str | None] | None = None
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
        return sensor_type(
            entity_id, device_class_of(self.hass, entity_id), effective_types(options)
        )

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
        placeholders = {"saved": self._saved_text() if saved else ""}
        items = self._menu_items(step_id)
        if items is not None:
            placeholders["items"] = items
        return self.async_show_menu(
            step_id=step_id,
            menu_options=menu_options,
            description_placeholders=placeholders,
        )

    def _menu_items(self, step_id: str) -> str | None:
        """Was es schon gibt – oben in jedem Menü zum Anlegen/Bearbeiten/Löschen."""
        options = self.config_entry.options
        lang = "de" if self._german() else "en"
        if step_id == "zones":
            return menu_lists.zones_text(self.hass, options, lang)
        if step_id == "profiles":
            return menu_lists.profiles_text(options, lang)
        if step_id == "areas":
            return menu_lists.areas_text(options, lang)
        if step_id == "users":
            return menu_lists.users_text(options, lang)
        if step_id == "controls":
            return menu_lists.controls_text(options, lang)
        if step_id == "sirens":
            return menu_lists.sirens_text(self.hass, options, lang)
        if step_id == "special_sensors":
            return menu_lists.special_text(self.hass, options, lang)
        return None

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
            "init",
            ["wizard", "triggering", "profiles", "sirens", "notifications", "system", "done"],
        )

    # --- Einrichtungsassistent (wizard.py) -------------------------------------

    def _wizard_options(self) -> Mapping[str, Any]:
        return self.config_entry.options

    async def _wizard_store(self, options: dict[str, Any], next_step: str) -> ConfigFlowResult:
        return await self._save(options, next_step)

    async def _wizard_finish(self) -> ConfigFlowResult:
        return await self.async_step_init()

    def _wizard_rules_possible(self) -> bool:
        return True

    def _wizard_siren_test_possible(self) -> bool:
        return True

    def _wizard_test_mode(self) -> bool | None:
        if self.config_entry.state is not ConfigEntryState.LOADED:
            return False
        return bool(self.config_entry.runtime_data.ctx.test_mode)

    async def async_step_done(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Schließen. Gespeichert wurde bereits nach jedem Formular."""
        return self.async_create_entry(data=dict(self.config_entry.options))

    async def async_step_settings_page(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Einstellungsseite in der Seitenleiste ein- oder ausblenden (ADR 0011)."""
        options = dict(self.config_entry.options)
        if user_input is not None:
            options[OPT_SETTINGS_PAGE] = bool(user_input.get("enabled"))
            return await self._save(options, "system")
        return self.async_show_form(
            step_id="settings_page",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "enabled", default=bool(options.get(OPT_SETTINGS_PAGE, True))
                    ): BooleanSelector()
                }
            ),
        )

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
                "restart",
                "settings_page",
                "init",
            ],
        )

    # --- Verhalten nach Neustart ----------------------------------------------

    def _restart_profile_key(self, area_id: str, area_name: str, single: bool) -> str:
        """Feldname je Bereich (mehrere Bereiche: der Name ist zugleich die Beschriftung)."""
        if single:
            return "restart_profile"
        prefix = "Profil" if self._german() else "Profile"
        return f"{prefix}: {area_name}" if area_id != MAIN_AREA else "restart_profile"

    async def async_step_restart(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Was nach einem Neustart von Home Assistant passiert."""
        options = self.config_entry.options
        areas = parse_areas(options)
        single = len(areas) == 1
        stored = dict(options.get(OPT_RESTART_PROFILES) or {})
        errors: dict[str, str] = {}
        if user_input is not None:
            behavior = user_input.get(OPT_RESTART_BEHAVIOR, DEFAULT_RESTART_BEHAVIOR)
            chosen = {
                area_id: user_input[key]
                for area_id, area in areas.items()
                if (key := self._restart_profile_key(area_id, area.name, single)) in user_input
                and user_input[key]
            }
            if behavior == RESTART_ARMED and not chosen:
                errors["base"] = "restart_needs_profile"
            else:
                new = dict(options)
                new[OPT_RESTART_BEHAVIOR] = behavior
                new[OPT_RESTART_PROFILES] = chosen
                new[OPT_RESTART_CONTINUE_ALARM] = bool(
                    user_input.get(OPT_RESTART_CONTINUE_ALARM, False)
                )
                return await self._save(new, "system")
        fields: dict[Any, Any] = {
            vol.Required(OPT_RESTART_BEHAVIOR, default=restart_behavior(options)): _select(
                list(RESTART_BEHAVIORS), "restart_behavior"
            ),
            vol.Optional(
                OPT_RESTART_CONTINUE_ALARM, default=continue_alarm(options)
            ): BooleanSelector(),
        }
        for area_id, area in areas.items():
            infos = [
                i for i in profile_infos(options) if profile_area(options, i.profile_id) == area_id
            ]
            if not infos:
                continue
            key = self._restart_profile_key(area_id, area.name, single)
            fields[vol.Optional(key, description={"suggested_value": stored.get(area_id)})] = (
                SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(value=i.profile_id, label=self._profile_label(i))
                            for i in infos
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                )
            )
        return self.async_show_form(
            step_id="restart", data_schema=vol.Schema(fields), errors=errors
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
            change = save_area(options, area_id, user_input)
            errors = dict(change.errors)
            if change.ok:
                assert change.options is not None
                return await self._save(change.options, "areas")
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
                elif is_action_code(parse_action_codes(options), master):
                    errors["master_pin"] = "pin_is_action_code"
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
                options[OPT_CARD_PIN_UNLINKED] = bool(user_input.get(OPT_CARD_PIN_UNLINKED, True))
                return await self._save(options, "users")
        users = parse_users(options)
        with_pin = sorted(
            u.name for u in users if u.pin is not None and u.user_id != MASTER_USER_ID
        )
        placeholders["pin_users"] = ", ".join(with_pin) or "–"
        placeholders["master"] = menu_lists.master_pin_text(
            options, "de" if self._german() else "en"
        )
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
                vol.Optional(
                    OPT_CARD_PIN_UNLINKED,
                    default=bool(options.get(OPT_CARD_PIN_UNLINKED, True)),
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
            change = delete_profile(self.config_entry.options, user_input["profile"])
            assert change.options is not None
            return await self._save(change.options, "profiles")
        return self.async_show_form(
            step_id="profile_delete",
            data_schema=vol.Schema({vol.Required("profile"): self._profile_selector()}),
        )

    async def async_step_profile_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        options = dict(self.config_entry.options)
        zones = parse_zones(options)
        registered_sirens = [s for s in options.get(OPT_SIRENS, []) if isinstance(s, str)]
        errors: dict[str, str] = {}
        if user_input is not None and "name" in user_input:
            change = save_profile(
                options,
                self._profile_id,
                user_input,
                entities_by_label=entities_by_label(self.hass),
            )
            errors = dict(change.errors)
            if change.ok:
                assert change.options is not None
                assert change.item_id is not None
                options, profile_id = change.options, change.item_id
                name = str(user_input["name"]).strip()
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
                # Auslöseregeln nur zeigen, wenn es welche gibt (sonst stünde der Hinweis leer da)
                **(
                    {
                        vol.Optional(
                            "rules",
                            default=[
                                r
                                for r in profile_rule_ids(options, pid)
                                if r in parse_rules(options)
                            ],
                        ): self._rule_selector(multiple=True)
                    }
                    if parse_rules(options)
                    else {}
                ),
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
                # Nur mit Meldern mit Kippstellung (ADR 0010)
                **(
                    {
                        vol.Required(
                            "tilt_allowed", default=behaviour.tilt_allowed
                        ): BooleanSelector()
                    }
                    if parse_tilt_sources(options)
                    else {}
                ),
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
            "triggering",
            ["zones", "rules", "always_active", "special_sensors", "helper_create", "init"],
        )

    # --- Besondere Melder (ADR 0010) ------------------------------------------

    async def async_step_special_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Melder mit Kippstellung (und später Erschütterungsstärke)."""
        options = self.config_entry.options
        items = ["tilt_add"]
        if parse_tilt_sources(options):
            items += ["tilt_edit", "tilt_delete"]
        items.append("vibration_add")
        if parse_vibration_sources(options):
            items += ["vibration_edit", "vibration_delete"]
        return self._menu("special_sensors", [*items, "triggering"])

    def _vibration_source_selector(self) -> SelectSelector:
        sources = parse_vibration_sources(self.config_entry.options)
        return SelectSelector(
            SelectSelectorConfig(
                options=[
                    SelectOptionDict(value=e, label=display_name(self.hass, e))
                    for e in sorted(sources, key=lambda e: display_name(self.hass, e).casefold())
                ],
                mode=SelectSelectorMode.DROPDOWN,
            )
        )

    def _group_target_selector(self, zones: dict[str, Zone]) -> SelectSelector:
        return SelectSelector(
            SelectSelectorConfig(
                options=[
                    SelectOptionDict(
                        value=t,
                        label=(
                            ("Noch in keine Meldergruppe" if self._german() else "No group yet")
                            if t == TARGET_NONE
                            else zones[t].name
                        ),
                    )
                    for t in [TARGET_NONE, *zones]
                ],
                mode=SelectSelectorMode.DROPDOWN,
            )
        )

    def _add_to_group(self, options: dict[str, Any], entity_id: str, target: str | None) -> None:
        """Melder in eine Meldergruppe aufnehmen – nur, wenn er noch in keiner steht."""
        zones = parse_zones(options)
        if not target or target not in zones:
            return
        labels = entities_by_label(self.hass)
        if any(entity_id in resolve_zone(z, labels) for z in zones.values()):
            return
        stored = {k: dict(v) for k, v in options.get(OPT_ZONES, {}).items()}
        stored[target]["entities"] = sorted({*stored[target].get("entities", []), entity_id})
        options[OPT_ZONES] = stored

    async def async_step_vibration_add(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Erschütterungsstärke als Zahl: Quelle und Schwelle (ADR 0010 Teil B)."""
        options = dict(self.config_entry.options)
        zones = parse_zones(options)
        current = parse_vibration_sources(options)
        editing = self._vibration_edit
        errors: dict[str, str] = {}
        if user_input is not None:
            entity_id = editing or user_input["entity"]
            state = self.hass.states.get(entity_id)
            if state is None:
                errors["entity"] = "tilt_entity_missing"
            else:
                options = save_vibration_source(
                    options, entity_id, threshold=float(user_input["threshold"])
                )
                self._add_to_group(options, entity_id, user_input.get("target"))
                self._vibration_edit = None
                return await self._save(options, "special_sensors")
        schema: dict[Any, Any] = {}
        if editing is None:
            schema[vol.Required("entity")] = EntitySelector(
                EntitySelectorConfig(domain=list(VIBRATION_STRENGTH_DOMAINS))
            )
        default = current[editing].threshold if editing in current else vol.UNDEFINED
        schema[vol.Required("threshold", default=default)] = NumberSelector(
            NumberSelectorConfig(mode=NumberSelectorMode.BOX, step="any")
        )
        if not any(
            (editing or "") in resolve_zone(z, entities_by_label(self.hass)) for z in zones.values()
        ):
            schema[vol.Optional("target", default=TARGET_NONE)] = self._group_target_selector(zones)
        state = self.hass.states.get(editing) if editing else None
        return self.async_show_form(
            step_id="vibration_add",
            data_schema=vol.Schema(schema),
            errors=errors,
            description_placeholders={
                "sensor": display_name(self.hass, editing) if editing else "–",
                "current": f"`{state.state}`" if state else "–",
            },
        )

    async def async_step_vibration_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if not parse_vibration_sources(self.config_entry.options):
            return await self.async_step_special_sensors()
        if user_input is not None:
            self._vibration_edit = user_input["sensor"]
            return await self.async_step_vibration_add()
        return self.async_show_form(
            step_id="vibration_edit",
            data_schema=vol.Schema({vol.Required("sensor"): self._vibration_source_selector()}),
        )

    async def async_step_vibration_delete(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if not parse_vibration_sources(self.config_entry.options):
            return await self.async_step_special_sensors()
        if user_input is not None:
            options = delete_vibration_source(self.config_entry.options, user_input["sensor"])
            return await self._save(options, "special_sensors")
        return self.async_show_form(
            step_id="vibration_delete",
            data_schema=vol.Schema({vol.Required("sensor"): self._vibration_source_selector()}),
        )

    def _tilt_source_selector(self) -> SelectSelector:
        sources = parse_tilt_sources(self.config_entry.options)
        return SelectSelector(
            SelectSelectorConfig(
                options=[
                    SelectOptionDict(value=e, label=display_name(self.hass, e))
                    for e in sorted(sources, key=lambda e: display_name(self.hass, e).casefold())
                ],
                mode=SelectSelectorMode.DROPDOWN,
            )
        )

    async def async_step_tilt_add(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Schritt 1: Quelle wählen (Entität, optional Attribut)."""
        errors: dict[str, str] = {}
        if user_input is not None:
            entity_id = user_input["entity"]
            attribute = str(user_input.get("attribute") or "").strip() or None
            state = self.hass.states.get(entity_id)
            if state is None:
                errors["entity"] = "tilt_entity_missing"
            elif attribute is not None and attribute not in state.attributes:
                errors["attribute"] = "tilt_attribute_missing"
            elif attribute is None and domain_of(entity_id) not in TILT_STATE_DOMAINS:
                errors["attribute"] = "tilt_attribute_needed"
            else:
                self._tilt_draft = {"entity": entity_id, "attribute": attribute}
                return await self.async_step_tilt_map()
        defaults = user_input or {}
        return self.async_show_form(
            step_id="tilt_add",
            data_schema=vol.Schema(
                {
                    vol.Required("entity", default=defaults.get("entity", vol.UNDEFINED)): (
                        EntitySelector(
                            EntitySelectorConfig(
                                domain=[*TILT_STATE_DOMAINS, "binary_sensor", "lock", "cover"]
                            )
                        )
                    ),
                    vol.Optional(
                        "attribute", description={"suggested_value": defaults.get("attribute")}
                    ): TextSelector(),
                }
            ),
            errors=errors,
        )

    async def async_step_tilt_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        sources = parse_tilt_sources(self.config_entry.options)
        if not sources:
            return await self.async_step_special_sensors()
        if user_input is not None:
            source = sources[user_input["sensor"]]
            self._tilt_draft = {"entity": source.entity_id, "attribute": source.attribute}
            return await self.async_step_tilt_map()
        return self.async_show_form(
            step_id="tilt_edit",
            data_schema=vol.Schema({vol.Required("sensor"): self._tilt_source_selector()}),
        )

    async def async_step_tilt_delete(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if not parse_tilt_sources(self.config_entry.options):
            return await self.async_step_special_sensors()
        if user_input is not None:
            options = delete_tilt_source(self.config_entry.options, user_input["sensor"])
            return await self._save(options, "special_sensors")
        return self.async_show_form(
            step_id="tilt_delete",
            data_schema=vol.Schema({vol.Required("sensor"): self._tilt_source_selector()}),
        )

    async def async_step_tilt_map(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Schritt 2: Welche Werte bedeuten zu, welche gekippt? Der Rest zählt als offen."""
        draft = self._tilt_draft
        entity_id, attribute = draft["entity"], draft["attribute"]
        options = dict(self.config_entry.options)
        zones = parse_zones(options)
        errors: dict[str, str] = {}
        if user_input is not None:
            closed = list(user_input.get("closed") or [])
            tilted = list(user_input.get("tilted") or [])
            if not closed:
                errors["closed"] = "tilt_no_closed"
            elif {v.casefold() for v in closed} & {v.casefold() for v in tilted}:
                errors["tilted"] = "tilt_overlap"
            else:
                options = save_tilt_source(
                    options, entity_id, attribute=attribute, closed=closed, tilted=tilted
                )
                target = user_input.get("target") or TARGET_NONE
                if target in zones and not any(
                    entity_id in resolve_zone(z, entities_by_label(self.hass))
                    for z in zones.values()
                ):
                    stored = {k: dict(v) for k, v in options.get(OPT_ZONES, {}).items()}
                    stored[target]["entities"] = sorted(
                        {*stored[target].get("entities", []), entity_id}
                    )
                    options[OPT_ZONES] = stored
                return await self._save(options, "special_sensors")
        state = self.hass.states.get(entity_id)
        values = known_values(
            state.state if state else None, state.attributes if state else None, attribute
        )
        current = parse_tilt_sources(options).get(entity_id)
        if current is not None:
            stored = options.get(OPT_TILT_SENSORS, {}).get(entity_id, {})
            closed_default = list(stored.get("closed", []))
            tilted_default = list(stored.get("tilted", []))
        else:
            closed_default, tilted_default = suggest(values)
        choices = sorted(
            {*values, *closed_default, *tilted_default}, key=lambda v: str(v).casefold()
        )
        member_of = next(
            (
                z.zone_id
                for z in zones.values()
                if entity_id in resolve_zone(z, entities_by_label(self.hass))
            ),
            None,
        )
        targets = [TARGET_NONE, *zones]

        def value_selector() -> SelectSelector:
            return SelectSelector(
                SelectSelectorConfig(
                    options=choices, multiple=True, custom_value=True, mode=SelectSelectorMode.LIST
                )
            )

        schema: dict[Any, Any] = {
            vol.Optional("closed", default=closed_default): value_selector(),
            vol.Optional("tilted", default=tilted_default): value_selector(),
        }
        if member_of is None:
            schema[vol.Optional("target", default=TARGET_NONE)] = SelectSelector(
                SelectSelectorConfig(
                    options=[
                        SelectOptionDict(
                            value=t,
                            label=(
                                ("Noch in keine Meldergruppe" if self._german() else "No group yet")
                                if t == TARGET_NONE
                                else zones[t].name
                            ),
                        )
                        for t in targets
                    ],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )
        return self.async_show_form(
            step_id="tilt_map",
            data_schema=vol.Schema(schema),
            errors=errors,
            description_placeholders={
                "sensor": display_name(self.hass, entity_id)
                + (f" ({attribute})" if attribute else ""),
                "values": ", ".join(f"`{v}`" for v in values) or "–",
                "current": f"`{_current_value(state, attribute)}`" if state else "–",
            },
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
        if self._wiz_return:
            # Regel aus dem Einrichtungsassistenten heraus angelegt oder abgebrochen: dorthin zurück
            self._saved = False
            step = getattr(self, f"async_step_{self._wiz_return}")
            result: ConfigFlowResult = await step()
            return result
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
                # Melder mit Kippstellung (Sensoren mit Text-Zustand passen nicht in die Auswahl
                # oben) – nur, wenn es welche gibt
                **(
                    {
                        vol.Optional(
                            "tilt_entities", default=defaults.get("tilt_entities", [])
                        ): SelectSelector(
                            SelectSelectorConfig(
                                options=[
                                    SelectOptionDict(value=e, label=display_name(self.hass, e))
                                    for e in sorted(tilt)
                                ],
                                multiple=True,
                            )
                        )
                    }
                    if (tilt := self._special_sources())
                    else {}
                ),
                label_key: LabelSelector(),
            }
        )

    def _special_sources(self) -> set[str]:
        """Besondere Melder (Kippstellung, Erschütterungsstärke) – passen nicht in die normale
        Auswahl, weil sie Sensoren mit Text- oder Zahlenwerten sind."""
        options = self.config_entry.options
        return {*parse_tilt_sources(options), *parse_vibration_sources(options)}

    def _zone_input(self, user_input: dict[str, Any]) -> dict[str, Any]:
        """Melder mit Kippstellung aus ihrem eigenen Feld zu den Sensoren der Gruppe nehmen."""
        merged = dict(user_input)
        tilt = list(merged.pop("tilt_entities", None) or [])
        merged["entities"] = sorted({*(merged.get("entities") or []), *tilt})
        return merged

    def _save_zone(
        self, zone_id: str | None, user_input: dict[str, Any]
    ) -> tuple[dict[str, Any] | None, dict[str, str], dict[str, str]]:
        change = save_zone(
            self.config_entry.options,
            zone_id,
            user_input,
            entities_by_label=entities_by_label(self.hass),
        )
        if not change.ok:
            conflicts = change.details.get("conflicts") or {}
            text = ", ".join(
                f"{display_name(self.hass, entity_id)} ({zone})"
                for entity_id, zone in conflicts.items()
            )
            return None, dict(change.errors), {"conflicts": text} if conflicts else {}
        self._zone_id = change.item_id
        return change.options, {}, {}

    async def async_step_zone_add(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        placeholders: dict[str, str] = {"conflicts": ""}
        if user_input is not None:
            user_input = self._zone_input(user_input)
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
            user_input = self._zone_input(user_input)
            options, errors, extra = self._save_zone(self._zone_id, user_input)
            if options is not None:
                return await self._zone_types_start(options, user_input)
            placeholders.update(extra)
        zone = parse_zones(self.config_entry.options)[self._zone_id]
        tilt = self._special_sources()
        defaults = user_input or {
            "name": zone.name,
            "entities": sorted(e for e in zone.entities if domain_of(e) in MONITORED_DOMAINS),
            "tilt_entities": sorted(e for e in zone.entities if e in tilt),
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
            types = effective_types(options)
            if any(
                sensor_type(e, device_class_of(self.hass, e), types) is SensorType.VIBRATION
                for e in self._type_fields.values()
            ):
                # Gruppe mit Erschütterungsmeldern: Fehlalarmschutz einstellen
                self._pending = options
                return await self.async_step_zone_vibration()
            self._pending = None
            return await self._save(options, "zones")
        fields: dict[Any, Any] = {}
        for key, entity_id in self._type_fields.items():
            current = self._type_of(options, entity_id)
            fields[vol.Required(key, default=current.value)] = _select(
                [t.value for t in SensorType], "sensor_type"
            )
        return self.async_show_form(step_id="zone_types", data_schema=vol.Schema(fields))

    async def async_step_zone_vibration(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Fehlalarmschutz für die Erschütterungsmelder der Gruppe (ADR 0010 Teil B)."""
        options = dict(self._pending or self.config_entry.options)
        zone_id = self._zone_id
        if zone_id is None or zone_id not in options.get(OPT_ZONES, {}):
            self._pending = None
            return await self._save(options, "zones")
        if user_input is not None:
            options = save_zone_rule(
                options,
                zone_id,
                count=int(user_input["vibration_count"]),
                window=int(user_input["vibration_window"]),
            )
            self._pending = None
            return await self._save(options, "zones")
        rule = rule_for_zone_id(options, zone_id)
        return self.async_show_form(
            step_id="zone_vibration",
            data_schema=vol.Schema(
                {
                    vol.Required("vibration_count", default=rule.count): NumberSelector(
                        NumberSelectorConfig(
                            min=1, max=VIBRATION_MAX_COUNT, step=1, mode=NumberSelectorMode.BOX
                        )
                    ),
                    vol.Required("vibration_window", default=rule.window): _seconds(
                        VIBRATION_MAX_WINDOW, minimum=VIBRATION_MIN_WINDOW
                    ),
                }
            ),
            description_placeholders={"zone": options[OPT_ZONES][zone_id].get("name", zone_id)},
        )

    async def async_step_zone_delete(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        zones = parse_zones(self.config_entry.options)
        if not zones:
            return self.async_abort(reason="no_zones")
        if user_input is not None:
            change = delete_zone(self.config_entry.options, user_input["zone"])
            assert change.options is not None
            return await self._save(change.options, "zones")
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
            sensor = user_input.get("stale_sensor")
            if sensor:
                # Erst den allgemeinen Wert übernehmen, dann den Melder einstellen
                self.hass.config_entries.async_update_entry(self.config_entry, options=options)
                self._stale_sensor = str(sensor)
                return await self.async_step_stale_sensor()
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
                vol.Optional("stale_sensor"): EntitySelector(
                    EntitySelectorConfig(domain=list(MONITORED_DOMAINS))
                ),
            }
        )
        silence = self.config_entry.runtime_data.silence if self._loaded() else None
        observed = silence.summary_text(self._german()) if silence else "–"
        return self.async_show_form(
            step_id="sensor_behaviour",
            data_schema=schema,
            description_placeholders={
                "observation": observed,
                "own": self._stale_overrides_text(),
            },
        )

    def _stale_overrides_text(self) -> str:
        """Melder mit eigener Funkstille-Grenze, z. B. "Hintertür: 24 h, Keller: nie prüfen"."""
        own = stale_override_hours(self.config_entry.options)
        if not own:
            return "–"
        never = "nie prüfen" if self._german() else "never check"
        return ", ".join(
            f"{display_name(self.hass, e)}: {f'{h} h' if h else never}" for e, h in own.items()
        )

    async def async_step_stale_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Funkstille für einen Melder: wie allgemein, eigene Stunden oder nie prüfen."""
        options = dict(self.config_entry.options)
        entity_id = getattr(self, "_stale_sensor", "") or ""
        errors: dict[str, str] = {}
        if user_input is not None:
            change = save_stale_override(
                options, entity_id, str(user_input.get("mode")), user_input.get("hours")
            )
            # Feld heißt im Dialog "hours"
            errors = {("hours" if k == "stale_hours" else k): v for k, v in change.errors.items()}
            if change.ok and change.options is not None:
                return await self._save(change.options, "system")
        own = stale_override_hours(options).get(entity_id)
        mode = STALE_DEFAULT if own is None else (STALE_OFF if own == 0 else STALE_HOURS)
        silence = self.config_entry.runtime_data.silence if self._loaded() else None
        german = self._german()
        record = silence.records.get(entity_id) if silence is not None else None
        advice_hours = silence.sensor_advice(entity_id) if silence is not None else None
        if record is None:
            observed = (
                "Für diesen Melder gibt es noch keine Beobachtung."
                if german
                else "No observation for this sensor yet."
            )
        else:
            days = f"{silence.days():.1f}" if silence is not None else "0"
            pause = format_silence(record.longest)
            observed = (
                f"Längste Pause {pause} bei {record.contacts} Meldungen in {days} Tagen."
                if german
                else f"Longest pause {pause} with {record.contacts} reports in {days} days."
            )
            if advice_hours:
                observed += (
                    f" **Empfehlung: {advice_hours} h.**"
                    if german
                    else f" **Recommendation: {advice_hours} h.**"
                )
        schema = vol.Schema(
            {
                vol.Required("mode", default=mode): _select(list(STALE_MODES), "stale_mode"),
                vol.Optional(
                    "hours", description={"suggested_value": own or advice_hours}
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1,
                        max=MAX_STALE_HOURS,
                        step=1,
                        unit_of_measurement="h",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
            }
        )
        return self.async_show_form(
            step_id="stale_sensor",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "sensor": display_name(self.hass, entity_id),
                "observation": observed,
            },
        )

    # --- Sirenen -----------------------------------------------------------

    async def async_step_sirens(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if self._wiz_return:
            # Sirenentest aus dem Einrichtungsassistenten heraus: dorthin zurück
            self._saved = False
            step = getattr(self, f"async_step_{self._wiz_return}")
            result: ConfigFlowResult = await step()
            return result
        return self._menu(
            "sirens",
            [
                "siren_settings",
                "siren_from_switch",
                "siren_tones",
                "siren_test",
                "siren_test_settings",
                "init",
            ],
        )

    async def async_step_siren_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        options = dict(self.config_entry.options)
        was_enabled = bool(options.get(OPT_SIRENS_HARDWARE_ENABLED, False))
        allow_switch = bool(options.get(OPT_SIRENS_ALLOW_SWITCH, False))
        errors: dict[str, str] = {}
        if user_input is not None:
            change = save_sirens(
                options,
                {
                    **user_input,
                    OPT_SIRENS: user_input.get(OPT_SIRENS) or [],
                    OPT_SIRENS_HARDWARE_ENABLED: bool(
                        user_input.get(OPT_SIRENS_HARDWARE_ENABLED, False)
                    ),
                    OPT_SIRENS_ALLOW_SWITCH: bool(user_input.get(OPT_SIRENS_ALLOW_SWITCH, False)),
                },
            )
            errors = dict(change.errors)
            if change.ok:
                assert change.options is not None
                options = change.options
                if options[OPT_SIRENS_ALLOW_SWITCH] and not allow_switch:
                    # Gerade eingeschaltet: Formular erneut zeigen, jetzt mit Schaltern
                    self.hass.config_entries.async_update_entry(self.config_entry, options=options)
                    return await self.async_step_siren_settings()
                return await self._save(options, "sirens")
        domains = [SIREN_ENTITY_DOMAIN, "switch"] if allow_switch else [SIREN_ENTITY_DOMAIN]
        schema = vol.Schema(
            {
                vol.Optional(OPT_SIRENS, default=list(options.get(OPT_SIRENS, []))): EntitySelector(
                    EntitySelectorConfig(domain=domains, multiple=True)
                ),
                vol.Required(OPT_SIRENS_HARDWARE_ENABLED, default=was_enabled): BooleanSelector(),
                vol.Optional("confirm_hardware", default=False): BooleanSelector(),
                vol.Optional(OPT_SIRENS_ALLOW_SWITCH, default=allow_switch): BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="siren_settings", data_schema=schema, errors=errors)

    async def async_step_siren_from_switch(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Assistent: aus einem Schalter über den Home-Assistant-Helfer "Gerätetyp eines
        Schalters ändern" eine Sirene machen und gleich als Sirene eintragen. Legt nur einen
        neuen Helfer an; der Schalter selbst wird nicht geschaltet."""
        options = dict(self.config_entry.options)
        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input.get("confirm"):
                errors["confirm"] = "siren_switch_confirm"
            else:
                entity_id = await self._create_switch_siren(str(user_input["switch"]))
                if entity_id is None:
                    errors["base"] = "helper_failed"
                else:
                    options[OPT_SIRENS] = sorted({*options.get(OPT_SIRENS, []), entity_id})
                    created = "Angelegt" if self._german() else "Created"
                    self._infos = [f"{created}: {entity_id}"]
                    return await self._save(options, "sirens")
        schema = vol.Schema(
            {
                vol.Required("switch"): EntitySelector(EntitySelectorConfig(domain="switch")),
                vol.Optional("confirm", default=False): BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="siren_from_switch", data_schema=schema, errors=errors)

    async def _create_switch_siren(self, switch: str) -> str | None:
        """Helfer "Schalter als Sirene" anlegen; liefert die neue Sirenen-Entität."""
        try:
            flow = await self.hass.config_entries.flow.async_init(
                SWITCH_AS_X_DOMAIN, context={"source": SOURCE_USER}
            )
            result = await self.hass.config_entries.flow.async_configure(
                flow["flow_id"], {"entity_id": switch, "target_domain": SIREN_ENTITY_DOMAIN}
            )
        except Exception:
            _LOGGER.exception("Helfer Schalter als Sirene konnte nicht angelegt werden")
            return None
        entry = result.get("result")
        if result.get("type") != "create_entry" or entry is None:
            return None
        sirens = [
            e.entity_id
            for e in er.async_entries_for_config_entry(er.async_get(self.hass), entry.entry_id)
            if e.domain == SIREN_ENTITY_DOMAIN
        ]
        return sirens[0] if sirens else None

    async def async_step_siren_tones(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ton je Sirene: erst die Sirene wählen."""
        options = dict(self.config_entry.options)
        sirens = [s for s in options.get(OPT_SIRENS, []) if isinstance(s, str)]
        if not sirens:
            return self.async_abort(reason="no_sirens")
        if user_input is not None:
            self._siren_tone_target = str(user_input["siren"])
            return await self.async_step_siren_tone_edit()
        tones = dict(options.get(OPT_SIREN_TONES, {}))
        auto = "automatisch" if self._german() else "automatic"
        choices = [
            SelectOptionDict(
                value=s, label=f"{display_name(self.hass, s)} – {tones.get(s) or auto}"
            )
            for s in sirens
        ]
        return self.async_show_form(
            step_id="siren_tones",
            data_schema=vol.Schema(
                {
                    vol.Required("siren"): SelectSelector(
                        SelectSelectorConfig(options=choices, mode=SelectSelectorMode.LIST)
                    )
                }
            ),
        )

    async def async_step_siren_tone_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ton je Sirene: aus den Tönen wählen, die das Gerät selbst meldet.

        Brandtöne nur als Experten-Freigabe mit eigener Bestätigung – und nie für Sirenen mit
        eigenen Brandsensoren (Rauchmelder).
        """
        options = dict(self.config_entry.options)
        siren = self._siren_tone_target or ""
        executor = self.config_entry.runtime_data.sirens if self._loaded() else None
        caps = executor.capabilities(siren) if executor is not None else None
        device = executor.devices().get(siren) if executor is not None else None
        smoke_detector = bool(device and device.fire_detector)
        known = sorted(caps.tones) if caps is not None and caps.tones else []
        tones = dict(options.get(OPT_SIREN_TONES, {}))
        fire_ok = {s for s in options.get(OPT_SIREN_FIRE_TONE_OK, []) if isinstance(s, str)}
        placeholders = self._siren_tone_placeholders(siren, caps, known)
        errors: dict[str, str] = {}
        current = tones.get(siren, AUTO_TONE)
        allow = siren in fire_ok
        if user_input is not None:
            tone = str(user_input.get("tone") or "").strip()
            allow = bool(user_input.get("allow_fire_tone"))
            current = tone or AUTO_TONE
            fire = bool(tone) and tone != AUTO_TONE and is_fire_tone(tone)
            if fire and smoke_detector:
                errors["tone"] = "siren_tone_fire_detector"
            elif fire and not allow:
                errors["tone"] = "siren_tone_fire"
            elif fire and not user_input.get("confirm_fire_tone"):
                errors["confirm_fire_tone"] = "siren_tone_fire_confirm"
            else:
                if tone in ("", AUTO_TONE):
                    tones.pop(siren, None)
                else:
                    tones[siren] = tone
                if fire:
                    fire_ok.add(siren)
                else:
                    fire_ok.discard(siren)
                options[OPT_SIREN_TONES] = tones
                options[OPT_SIREN_FIRE_TONE_OK] = sorted(fire_ok)
                return await self._save(options, "sirens")
        return self.async_show_form(
            step_id="siren_tone_edit",
            data_schema=self._siren_tone_schema(
                known, current, allow=allow, expert=not smoke_detector
            ),
            errors=errors,
            description_placeholders=placeholders,
        )

    def _siren_tone_schema(
        self, known: list[str], current: str, *, allow: bool, expert: bool
    ) -> vol.Schema:
        german = self._german()
        auto = "Automatisch (Standard-Einbruchton)" if german else "Automatic (burglar tone)"
        marker = " – Brandton" if german else " – fire tone"
        choices = [SelectOptionDict(value=AUTO_TONE, label=auto)] + [
            SelectOptionDict(value=t, label=t + (marker if is_fire_tone(t) else ""))
            for t in known
            if expert or not is_fire_tone(t)
        ]
        fields: dict[Any, Any] = {
            vol.Required("tone", default=current or AUTO_TONE): SelectSelector(
                SelectSelectorConfig(
                    options=choices, mode=SelectSelectorMode.DROPDOWN, custom_value=True
                )
            )
        }
        if expert:
            fields[vol.Optional("allow_fire_tone", default=allow)] = BooleanSelector()
            fields[vol.Optional("confirm_fire_tone", default=False)] = BooleanSelector()
        return vol.Schema(fields)

    def _siren_tone_placeholders(self, siren: str, caps: Any, known: list[str]) -> dict[str, str]:
        if caps is None or not caps.tones_supported:
            known_text = "– (diese Sirene kennt keine Töne)" if self._german() else "– (no tones)"
        else:
            known_text = ", ".join(known) or "–"
        return {"siren": display_name(self.hass, siren), "tones": known_text}

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
        return ", ".join(f"{{{p}}}" for p in placeholder_names("de" if self._german() else "en"))

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
        lang = "de" if self._german() else "en"
        if user_input is not None:
            texts = {k: str(user_input.get(k) or "").strip() for k in ("title", "message")}
            # Gleiche Regeln wie auf der Einstellungsseite: Vorlage unverändert = Text von Hauswacht
            change = save_event_text(
                options, event.value, texts["title"], texts["message"], lang=lang
            )
            if change.ok and change.options is not None:
                saved = change.options[OPT_EVENTS].get(event.value, {})
                if saved.get("message"):
                    self._notes.append(render(saved["message"], self._example_values()))
                return await self._save(dict(change.options), "notifications")
            errors = dict(change.errors)
            placeholders["error"] = str(change.details.get("message", ""))
        current = stored.get("message")
        if isinstance(current, str) and current:
            placeholders["preview"] = render(current, self._example_values())
        return self.async_show_form(
            step_id="notify_text_edit",
            data_schema=vol.Schema(
                {
                    # Vorschlag: eigener Text oder die Vorlage von Hauswacht zum Ändern
                    vol.Optional(
                        "title",
                        description={
                            "suggested_value": stored.get("title") or default_title(event, lang)
                        },
                    ): TextSelector(),
                    vol.Optional(
                        "message",
                        description={
                            "suggested_value": stored.get("message") or default_message(event, lang)
                        },
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
                check_template(text, "de" if self._german() else "en")
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
            change = save_notify_settings(options, user_input)
            assert change.options is not None
            options = change.options
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
        return self._menu(
            "users", ["user_add", "user_edit", "user_delete", "cards", "pins", "code", "system"]
        )

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
            change = delete_user(self.config_entry.options, user_input["user"])
            assert change.options is not None
            return await self._save(change.options, "users")
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
            errors = validate_user_name(options, user_id, name)
            if not errors:
                change = save_user(
                    options,
                    user_id,
                    {
                        **user_input,
                        "valid_from": _to_iso(user_input.get("valid_from")),
                        "valid_until": _to_iso(user_input.get("valid_until")),
                    },
                    ha_user=user_input.get("ha_user") or await self._ha_user_by_name(name),
                )
                assert change.options is not None
                assert change.item_id is not None
                if user_input.get("rights", RIGHTS_ALL) == RIGHTS_PER_AREA:
                    self._user_pending = (change.item_id, change.options)
                    return await self.async_step_user_area_rights()
                return await self._save(change.options, "users")

        placeholders["status"] = self._credential_status(current)
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
            change = set_area_rights(
                options,
                user_id,
                {area.area_id: user_input.get(area.name, []) for area in areas.values()},
            )
            assert change.options is not None
            self._user_pending = None
            return await self._save(change.options, "users")
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

    # --- Aktions-Codes --------------------------------------------------------

    def _keypads(self) -> dict[str, str]:
        """Eingerichtete Keypads: ID -> Name."""
        return {
            c.control_id: c.name
            for c in parse_controls(self.config_entry.options).values()
            if c.kind in (ControlKind.KEYPAD, ControlKind.GENERIC_KEYPAD)
        }

    def _action_code_label(self, code: ActionCode) -> str:
        de = self._german()
        keys = {
            KEY_DAY: "🏠 Haus" if de else "🏠 house",
            KEY_NIGHT: "🌙 Nacht" if de else "🌙 night",
            KEY_ALL: "🔒 Schloss" if de else "🔒 lock",
            KEY_DISARM: "🔓 offenes Schloss" if de else "🔓 open lock",
        }
        keypad = (
            ("alle Keypads" if de else "all keypads")
            if code.keypad == ALL_KEYPADS
            else self._keypads().get(code.keypad, code.keypad)
        )
        if code.action is CodeAction.ARM:
            names = {i.profile_id: i.name for i in profile_infos(self.config_entry.options)}
            what = ("scharf: " if de else "arm: ") + names.get(code.profile or "", "?")
        elif code.action is CodeAction.SILENT_EMERGENCY:
            what = "stiller Notruf" if de else "silent emergency"
        else:
            what = "Ereignis" if de else "event"
        return f"{code.name} – {code.code} + {keys[code.key]} · {keypad} → {what}"

    async def async_step_action_codes(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Liste der Aktions-Codes (Code + Taste am Keypad -> Aktion)."""
        if not self._keypads():
            return self.async_abort(reason="no_keypads")
        if user_input is not None:
            choice = user_input["action_code"]
            self._action_code = None if choice == ACTION_CODE_NEW else choice
            return await self.async_step_action_code_edit()
        de = self._german()
        options = [
            SelectOptionDict(
                value=ACTION_CODE_NEW,
                label="➕ Neuer Aktions-Code" if de else "➕ New action code",
            )
        ]
        options.extend(
            SelectOptionDict(value=c.code_id, label=self._action_code_label(c))
            for c in sorted(
                parse_action_codes(self.config_entry.options), key=lambda c: c.name.casefold()
            )
        )
        saved, self._saved = self._saved, False
        return self.async_show_form(
            step_id="action_codes",
            data_schema=vol.Schema(
                {
                    vol.Required("action_code"): SelectSelector(
                        SelectSelectorConfig(options=options, mode=SelectSelectorMode.LIST)
                    )
                }
            ),
            description_placeholders={"saved": self._saved_text() if saved else ""},
        )

    async def async_step_action_code_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Einen Aktions-Code anlegen, ändern oder löschen."""
        options = dict(self.config_entry.options)
        stored: dict[str, Any] = dict(options.get(OPT_ACTION_CODES, {}))
        code_id = self._action_code
        current: dict[str, Any] = dict(stored.get(code_id, {})) if code_id else {}
        errors: dict[str, str] = {}
        conflict = ""
        if user_input is not None:
            if code_id and user_input.get("delete"):
                stored.pop(code_id, None)
                options[OPT_ACTION_CODES] = stored
                self._action_code = None
                return await self._save(options, "action_codes")
            data, errors, conflict = await self._validate_action_code(user_input, code_id, stored)
            if not errors:
                stored[code_id or unique_user_id(data["name"], stored)] = data
                options[OPT_ACTION_CODES] = stored
                self._action_code = None
                return await self._save(options, "action_codes")
            current = {**current, **user_input}
        keypads = [SelectOptionDict(value=ALL_KEYPADS, label=self._all_keypads_label())]
        keypads.extend(SelectOptionDict(value=k, label=n) for k, n in self._keypads().items())
        fields: dict[Any, Any] = {
            vol.Required("name", default=current.get("name", "")): TextSelector(),
            vol.Required("code", default=current.get("code", "")): TextSelector(),
            vol.Required("key", default=current.get("key", KEY_DAY)): _select(
                list(ACTION_CODE_KEYS), "action_code_key"
            ),
            vol.Required("keypad", default=current.get("keypad", ALL_KEYPADS)): SelectSelector(
                SelectSelectorConfig(options=keypads, mode=SelectSelectorMode.DROPDOWN)
            ),
            vol.Required("action", default=current.get("action", CodeAction.EVENT.value)): (
                _select([a.value for a in CodeAction], "action_code_action")
            ),
            vol.Optional(
                "profile", description={"suggested_value": current.get("profile")}
            ): self._control_profile_selector(),
        }
        if code_id:
            fields[vol.Optional("delete", default=False)] = BooleanSelector()
        return self.async_show_form(
            step_id="action_code_edit",
            data_schema=vol.Schema(fields),
            errors=errors,
            description_placeholders={"conflict": conflict},
        )

    def _all_keypads_label(self) -> str:
        return "Alle Keypads" if self._german() else "All keypads"

    async def _validate_action_code(
        self, user_input: dict[str, Any], code_id: str | None, stored: Mapping[str, Any]
    ) -> tuple[dict[str, Any], dict[str, str], str]:
        """Prüfen: Name eindeutig, 2–8 Ziffern, kein PIN, Code + Taste nicht doppelt."""
        name = str(user_input.get("name") or "").strip()
        code = str(user_input.get("code") or "").strip()
        key = str(user_input.get("key") or KEY_DAY)
        keypad = str(user_input.get("keypad") or ALL_KEYPADS)
        action = str(user_input.get("action") or CodeAction.EVENT.value)
        profile = user_input.get("profile")
        data: dict[str, Any] = {
            "name": name,
            "code": code,
            "key": key,
            "keypad": keypad,
            "action": action,
        }
        errors: dict[str, str] = {}
        conflict = ""
        others = [c for c in parse_action_codes({OPT_ACTION_CODES: stored}) if c.code_id != code_id]
        if not name:
            errors["name"] = "user_name_required"
        elif any(c.name.casefold() == name.casefold() for c in others):
            errors["name"] = "action_code_name_taken"
        if not is_valid_action_code(code):
            errors["code"] = "action_code_invalid"
        elif (clash := action_code_clash(others, code, key, keypad)) is not None:
            errors["code"] = "action_code_taken"
            conflict = clash.name
        if action == CodeAction.ARM.value:
            if not profile:
                errors["profile"] = "action_code_profile_missing"
            else:
                data["profile"] = profile
        if not errors:
            users = parse_users(self.config_entry.options)
            found = await self.hass.async_add_executor_job(
                lambda: pin_conflicts(code, users, kind="duress")
            )
            if found:
                errors["code"] = "action_code_is_pin"
        return data, errors, conflict

    # --- Karten und PINs ------------------------------------------------------

    def _when_used(self, key: str) -> str:
        """ "zuletzt 16.11. 07:12" bzw. "noch nie benutzt" (nur wenn Hauswacht läuft)."""
        if not self._loaded():
            return ""
        used = getattr(self.config_entry.runtime_data, "last_used", {}).get(key)
        de = self._german()
        if not used:
            return "noch nie benutzt" if de else "never used"
        local = dt_util.as_local(dt_util.utc_from_timestamp(used))
        today = dt_util.now().date()
        text = local.strftime("%H:%M") if local.date() == today else local.strftime("%d.%m.%Y")
        return f"zuletzt {text}" if de else f"last {text}"

    def _credential_status(self, current: Mapping[str, Any]) -> str:
        """Kurzer Stand im Benutzer-Dialog: "2 Karten · PIN gesetzt"."""
        de = self._german()
        cards = len(current.get("tags", []) or []) + len(current.get("tags_disabled", []) or [])
        parts = [
            (f"{cards} Karte" if cards == 1 else f"{cards} Karten")
            if de
            else (f"{cards} card" if cards == 1 else f"{cards} cards"),
            ("PIN gesetzt" if de else "PIN set")
            if current.get("pin_digest")
            else ("kein PIN" if de else "no PIN"),
        ]
        if current.get("duress_digest"):
            parts.append("Bedrohungs-PIN gesetzt" if de else "duress PIN set")
        return " · ".join(parts)

    def _users_choice(self) -> SelectSelector:
        stored = self.config_entry.options.get(OPT_USERS, {})
        return SelectSelector(
            SelectSelectorConfig(
                options=[
                    SelectOptionDict(value=uid, label=str(data.get("name") or uid))
                    for uid, data in stored.items()
                    if uid != MASTER_USER_ID  # Master-PIN ist keine Person
                ],
                mode=SelectSelectorMode.DROPDOWN,
            )
        )

    async def async_step_cards(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Alle Karten, Finger und Schloss-Kennungen: wem gehören sie, aktiv, zuletzt benutzt."""
        users = self.config_entry.options.get(OPT_USERS, {})
        if not users:
            return self.async_abort(reason="no_users")
        if user_input is not None:
            choice = user_input["card"]
            if choice == CARD_NEW:
                return await self._card_new_start()
            if choice == CARD_TYPE:
                self._new_card = None
                return await self.async_step_card_new()
            self._card = choice
            return await self.async_step_card_edit()
        de = self._german()
        lang = "de" if de else "en"
        options = [
            SelectOptionDict(
                value=CARD_NEW,
                label="➕ Neue Karte anlernen (hinhalten)"
                if de
                else "➕ Learn new card (hold it up)",
            ),
            SelectOptionDict(
                value=CARD_TYPE,
                label="⌨️ Kartennummer eintippen" if de else "⌨️ Type in card number",
            ),
        ]
        for tag, uid, name, active in _all_cards(users):
            owner = str(users[uid].get("name") or uid)
            ident = lock_id_label(tag, lang)
            title = f"{name} ({ident})" if name else ident
            state = (
                self._when_used(f"card:{tag}") if active else ("deaktiviert" if de else "disabled")
            )
            text = f"{'🟢' if active else '⏸️'} {title} – {owner}"
            options.append(
                SelectOptionDict(value=tag, label=f"{text} · {state}" if state else text)
            )
        saved, self._saved = self._saved, False
        return self.async_show_form(
            step_id="cards",
            data_schema=vol.Schema(
                {
                    vol.Required("card"): SelectSelector(
                        SelectSelectorConfig(options=options, mode=SelectSelectorMode.LIST)
                    )
                }
            ),
            description_placeholders={"saved": self._saved_text() if saved else ""},
        )

    async def _card_new_start(self) -> ConfigFlowResult:
        """Neue Karte: immer auf das Hinhalten warten – eine früher gelesene (z. B. aus einem
        abgebrochenen Versuch) wird nicht vorausgewählt. Geht weiter, sobald eine gelesen ist."""
        self._new_card = None
        controls = (
            getattr(self.config_entry.runtime_data, "controls", None) if self._loaded() else None
        )
        waiting_possible = (
            controls is not None
            and learn_minutes(self.config_entry.options) > 0
            and self._is_disarmed()
        )
        if not waiting_possible:
            return await self.async_step_card_new()
        return await self.async_step_card_wait()

    async def async_step_card_wait(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """ "Halte die Karte jetzt ans Keypad …" – wartet bis zu CARD_WAIT_SECONDS."""
        if self._card_task is None:
            self._card_task = self.hass.async_create_background_task(
                self._wait_for_card(), "hauswacht_card_wait"
            )
        if not self._card_task.done():
            return self.async_show_progress(
                step_id="card_wait",
                progress_action="wait_card",
                progress_task=self._card_task,
                description_placeholders={"seconds": str(CARD_WAIT_SECONDS)},
            )
        self._new_card = self._card_task.result()
        self._card_task = None
        return self.async_show_progress_done(next_step_id="card_new")

    async def _wait_for_card(self) -> str | None:
        controls = getattr(self.config_entry.runtime_data, "controls", None)
        if controls is None:
            return None
        future: asyncio.Future[str] = self.hass.loop.create_future()

        def _read(tag: str) -> None:
            if not future.done():
                future.set_result(tag)

        remove = controls.wait_for_card(_read)
        try:
            return await asyncio.wait_for(future, CARD_WAIT_SECONDS)
        except TimeoutError:
            return None
        finally:
            remove()

    async def async_step_card_new(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Neue Karte: erkannte/gelesene Karte oder eingetippte Nummer, Name, Benutzer."""
        options = dict(self.config_entry.options)
        users: dict[str, Any] = dict(options.get(OPT_USERS, {}))
        errors: dict[str, str] = {}
        conflict = ""
        if user_input is not None:
            tags = _tag_input(user_input.get("card"))
            tag = tags[0] if tags else ""
            if (error := self._card_error(tag, users)) is not None:
                errors["card"], conflict = error
            elif user_input.get("user") not in users:
                errors["user"] = "user_missing"
            else:
                _put_card(
                    users,
                    tag,
                    user_input["user"],
                    str(user_input.get("name") or "").strip(),
                    active=bool(user_input.get("active", True)),
                )
                options[OPT_USERS] = users
                self._new_card = None
                return await self._save(options, "cards")
        card_options = self._new_card_options()
        if self._new_card:
            # Gerade erkannt: nur diese Karte anbieten, keine älteren
            card_options = [o for o in card_options if o["value"] == self._new_card] or [
                SelectOptionDict(value=self._new_card, label=self._new_card)
            ]
            self._offered_new &= {self._new_card}
        default = self._new_card or (card_options[0]["value"] if card_options else None)
        de = self._german()
        if self._new_card:
            found = (
                f"✅ Karte erkannt: **{self._new_card}**"
                if de
                else f"✅ Card recognised: **{self._new_card}**"
            )
        elif card_options:
            found = (
                "Zuletzt gelesene unbekannte Karten stehen unten zur Auswahl."
                if de
                else "Recently read unknown cards are offered below."
            )
        else:
            found = (
                "Es wurde keine neue Karte gelesen. Halte sie an ein Keypad oder einen Leser und "
                "öffne diesen Dialog noch einmal – oder tippe die Nummer ein."
                if de
                else "No new card was read. Hold it to a keypad or reader and open this dialog "
                "again – or type in the number."
            )
        card_key = vol.Required("card", default=default) if default else vol.Required("card")
        schema = vol.Schema(
            {
                card_key: SelectSelector(
                    SelectSelectorConfig(
                        options=card_options, custom_value=True, mode=SelectSelectorMode.DROPDOWN
                    )
                ),
                vol.Optional("name"): TextSelector(),
                vol.Required("user"): self._users_choice(),
                vol.Optional("active", default=True): BooleanSelector(),
            }
        )
        return self.async_show_form(
            step_id="card_new",
            data_schema=self.add_suggested_values_to_schema(schema, user_input or {}),
            errors=errors,
            description_placeholders={
                "found": found,
                "conflict": conflict,
                "random": self._random_hint(),
            },
        )

    async def async_step_card_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Eine Karte: umbenennen, anderem Benutzer geben, deaktivieren, löschen."""
        options = dict(self.config_entry.options)
        users: dict[str, Any] = dict(options.get(OPT_USERS, {}))
        tag = self._card
        row = next((r for r in _all_cards(users) if r[0] == tag), None)
        if tag is None or row is None:
            return await self.async_step_cards()
        _, owner, name, active = row
        if user_input is not None:
            if user_input.get("delete"):
                _remove_card(users, tag)
            else:
                target = user_input.get("user") if user_input.get("user") in users else owner
                _put_card(
                    users,
                    tag,
                    target,
                    str(user_input.get("name") or "").strip(),
                    active=bool(user_input.get("active", True)),
                )
            options[OPT_USERS] = users
            self._card = None
            return await self._save(options, "cards")
        lang = "de" if self._german() else "en"
        schema = vol.Schema(
            {
                vol.Optional("name", description={"suggested_value": name}): TextSelector(),
                vol.Required("user", default=owner): self._users_choice(),
                vol.Optional("active", default=active): BooleanSelector(),
                vol.Optional("delete", default=False): BooleanSelector(),
            }
        )
        return self.async_show_form(
            step_id="card_edit",
            data_schema=schema,
            description_placeholders={
                "card": lock_id_label(tag, lang),
                "used": self._when_used(f"card:{tag}"),
            },
        )

    async def async_step_pins(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Wer hat einen PIN / Bedrohungs-PIN, wann zuletzt benutzt (PINs selbst nie sichtbar)."""
        users = self.config_entry.options.get(OPT_USERS, {})
        if not users:
            return self.async_abort(reason="no_users")
        if user_input is not None:
            self._user_id = user_input["user"]
            return await self.async_step_pin_edit()
        de = self._german()
        options = []
        for uid, data in users.items():
            parts = []
            if data.get("pin_digest"):
                parts.append("PIN")
            if data.get("duress_digest"):
                parts.append("Bedrohungs-PIN" if de else "duress PIN")
            if parts:
                used = self._when_used(f"pin:{uid}")
                if used:
                    parts.append(used)
            text = " · ".join(parts) if parts else ("kein PIN" if de else "no PIN")
            options.append(SelectOptionDict(value=uid, label=f"{data.get('name') or uid} – {text}"))
        saved, self._saved = self._saved, False
        return self.async_show_form(
            step_id="pins",
            data_schema=vol.Schema(
                {
                    vol.Required("user"): SelectSelector(
                        SelectSelectorConfig(options=options, mode=SelectSelectorMode.LIST)
                    )
                }
            ),
            description_placeholders={"saved": self._saved_text() if saved else ""},
        )

    async def async_step_pin_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """PIN und Bedrohungs-PIN eines Benutzers setzen, ändern oder entfernen."""
        options = dict(self.config_entry.options)
        stored_all: dict[str, Any] = dict(options.get(OPT_USERS, {}))
        user_id = getattr(self, "_user_id", None)
        if user_id not in stored_all:
            return await self.async_step_pins()
        data = dict(stored_all[user_id])
        name = str(data.get("name") or user_id)
        errors: dict[str, str] = {}
        conflict = ""
        if user_input is not None:
            change = await self.hass.async_add_executor_job(
                set_pins, self.config_entry.options, user_id, user_input
            )
            errors = dict(change.errors)
            conflict = str(change.details.get("conflict") or "")
            if change.ok:
                assert change.options is not None
                return await self._save(change.options, "pins")
        schema = vol.Schema(
            {
                vol.Optional("new_pin"): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
                vol.Optional("remove_pin", default=False): BooleanSelector(),
                vol.Optional("new_duress_pin"): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
                vol.Optional("remove_duress_pin", default=False): BooleanSelector(),
            }
        )
        return self.async_show_form(
            step_id="pin_edit",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "name": name,
                "status": self._credential_status(data),
                "conflict": conflict,
            },
        )

    # --- Bedienteile ---------------------------------------------------------

    async def async_step_controls(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self._menu(
            "controls",
            [
                "control_add_keypad",
                "control_add_generic_keypad",
                "control_add_sticker",
                "control_add_reader",
                "control_add_button",
                "control_add_lock",
                "control_edit",
                "control_delete",
                "control_learn",
                "action_codes",
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

    async def async_step_control_add_generic_keypad(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        self._control_id, self._control_kind = None, ControlKind.GENERIC_KEYPAD
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

    async def async_step_control_add_button(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        self._control_id, self._control_kind = None, ControlKind.BUTTON
        return await self.async_step_control_settings()

    async def async_step_control_add_lock(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        self._control_id, self._control_kind = None, ControlKind.LOCK
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

    def _keypad_topic(self, device_id: str | None) -> str:
        """MQTT-Topic eines Zigbee2MQTT-Geräts: Basis-Topic + Gerätename in Zigbee2MQTT."""
        device = dr.async_get(self.hass).async_get(device_id) if device_id else None
        if device is None or not device.name:
            return ""
        return f"{Z2M_BASE_TOPIC}/{device.name}"

    def _resolve_keypad_topic(self, user_input: dict[str, Any]) -> dict[str, Any]:
        """Ohne eigenes Topic: aus dem gewählten Keypad-Gerät bilden."""
        topic = str(user_input.get("topic") or "").strip().rstrip("/")
        if not topic or topic == Z2M_BASE_TOPIC:
            topic = self._keypad_topic(user_input.get("keypad_device"))
        return {**user_input, "topic": topic}

    def _validate_control(self, kind: ControlKind, data: dict[str, Any]) -> dict[str, str]:
        return validate_control(self.config_entry.options, kind, data)

    async def async_step_control_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        kind = self._control_kind
        stored = dict(self.config_entry.options.get(OPT_CONTROLS, {}))
        current: dict[str, Any] = dict(stored.get(self._control_id or "", {}))
        errors: dict[str, str] = {}
        if user_input is not None:
            if kind is ControlKind.KEYPAD:
                user_input = self._resolve_keypad_topic(user_input)
            errors = self._validate_control(kind, user_input)
            if not errors:
                data = _control_data(kind, user_input, current)
                control_id = self._control_id or slugify(data["name"], existing=list(stored))
                stored[control_id] = data
                options = dict(self.config_entry.options)
                options[OPT_CONTROLS] = stored
                if kind is ControlKind.BUTTON:
                    # Zweiter Schritt: welche Druckart welches Profil schaltet
                    self._control_id = control_id
                    self._pending = options
                    return await self.async_step_control_presses()
                return await self._save(options, "controls")
        source = {**current, **(user_input or {})}
        placeholders: dict[str, str] = {}
        if kind is ControlKind.GENERIC_KEYPAD:
            unknown = self._unknown_keypads()
            if not self._control_id and unknown and not source.get("name"):
                source["name"] = unknown[0]  # zuletzt gemeldetes unbekanntes Keypad
            placeholders = {
                "ident": self._control_id or "–",
                "unknown": ", ".join(f"`{u}`" for u in unknown) or "–",
            }
        fields = self._control_fields(kind, source, current)
        return self.async_show_form(
            step_id=f"control_{kind.value}",
            data_schema=vol.Schema(fields),
            errors=errors,
            description_placeholders=placeholders or None,
        )

    def _unknown_keypads(self) -> list[str]:
        """Unbekannte Keypads, die sich zuletzt über keypad_input gemeldet haben."""
        runtime = getattr(self.config_entry, "runtime_data", None)
        controls = getattr(runtime, "controls", None)
        return list(getattr(controls, "unknown_keypads", {}) or {})

    def _control_fields(
        self, kind: ControlKind, source: dict[str, Any], current: dict[str, Any]
    ) -> dict[Any, Any]:
        """Formularfelder je Art des Bedienteils."""
        buttons = current.get("buttons", {})
        fields: dict[Any, Any] = {
            vol.Required("name", default=source.get("name", "")): TextSelector(),
            vol.Required("area", default=source.get("area", CONTROL_ALL_AREAS)): (
                self._control_area_selector()
            ),
        }
        if kind is ControlKind.KEYPAD:
            device = source.get("keypad_device")
            topic = str(source.get("topic") or "")
            if device and topic == self._keypad_topic(device):
                topic = ""  # kommt automatisch aus dem Gerät
            fields[vol.Optional("keypad_device", description={"suggested_value": device})] = (
                DeviceSelector(DeviceSelectorConfig(integration="mqtt"))
            )
            fields[vol.Optional("topic", description={"suggested_value": topic})] = TextSelector()
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
        elif kind is ControlKind.GENERIC_KEYPAD:
            self._generic_keypad_fields(fields, source, buttons)
        elif kind is ControlKind.BUTTON:
            fields[vol.Required("entity", default=source.get("entity", vol.UNDEFINED))] = (
                EntitySelector(EntitySelectorConfig(domain=["event", "sensor"]))
            )
        elif kind is ControlKind.LOCK:
            fields[vol.Required("entity", default=source.get("entity", vol.UNDEFINED))] = (
                EntitySelector(EntitySelectorConfig(domain="lock"))
            )
            fields[vol.Required("source", default=source.get("source", "nuki_mqtt"))] = _select(
                ["nuki_mqtt", "generic"], "lock_source"
            )
            fields[vol.Optional("topic", description={"suggested_value": source.get("topic")})] = (
                TextSelector()
            )
            fields[vol.Optional("who", description={"suggested_value": source.get("who")})] = (
                EntitySelector(EntitySelectorConfig(domain=["sensor", "event"]))
            )
            fields[
                vol.Optional("profile", description={"suggested_value": source.get("profile")})
            ] = self._control_profile_selector()
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
        return fields

    def _generic_keypad_fields(
        self, fields: dict[Any, Any], source: dict[str, Any], buttons: Mapping[str, Any]
    ) -> None:
        """Allgemeines Keypad: freie Tasten (Name → Profil), Anmeldung, Notruf."""
        pairs = list(buttons.items()) or [(name, None) for name in DEFAULT_GENERIC_BUTTONS]
        for n in range(1, GENERIC_BUTTON_FIELDS + 1):
            name, profile = pairs[n - 1] if len(pairs) >= n else (None, None)
            name = source.get(f"button_{n}", name)
            profile = source.get(f"profile_{n}", profile)
            fields[vol.Optional(f"button_{n}", description={"suggested_value": name})] = (
                TextSelector()
            )
            fields[vol.Optional(f"profile_{n}", description={"suggested_value": profile})] = (
                self._control_profile_selector()
            )
        fields[vol.Required("login", default=source.get("login", "pin_or_card"))] = _select(
            ["pin_or_card", "card_and_pin"], "control_login"
        )
        fields[vol.Required("emergency", default=source.get("emergency", "off"))] = _select(
            ["off", "silent", "alarm"], "control_emergency"
        )

    async def async_step_control_keypad(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self.async_step_control_settings(user_input)

    async def async_step_control_generic_keypad(
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

    async def async_step_control_button(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self.async_step_control_settings(user_input)

    async def async_step_control_lock(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self.async_step_control_settings(user_input)

    async def async_step_control_presses(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Taster: je Druckart ein Profil. Ereignis-Entitäten nennen ihre Druckarten selbst."""
        options = dict(self._pending or self.config_entry.options)
        stored = dict(options.get(OPT_CONTROLS, {}))
        control_id = self._control_id or ""
        data = dict(stored.get(control_id, {}))
        known = self._event_types(str(data.get("entity") or ""))
        current: dict[str, str] = dict(data.get("presses", {}))
        errors: dict[str, str] = {}
        if user_input is not None:
            if known:
                presses = {t: user_input[t] for t in known if user_input.get(t)}
            else:
                presses = {
                    str(user_input[f"press_{n}"]).strip(): user_input[f"profile_{n}"]
                    for n in (1, 2, 3)
                    if str(user_input.get(f"press_{n}") or "").strip()
                    and user_input.get(f"profile_{n}")
                }
            area = data.get("area") or CONTROL_ALL_AREAS
            if not presses:
                errors["base"] = "button_no_press"
            elif area != CONTROL_ALL_AREAS and any(
                profile_area(options, p) != area for p in presses.values()
            ):
                errors["base"] = "control_profile_area"
            if not errors:
                data["presses"] = presses
                stored[control_id] = data
                options[OPT_CONTROLS] = stored
                self._pending = None
                return await self._save(options, "controls")
        fields: dict[Any, Any] = {}
        if known:
            for event_type in known:
                suggested = {"suggested_value": current.get(event_type)}
                fields[vol.Optional(event_type, description=suggested)] = (
                    self._control_profile_selector()
                )
        else:
            pairs = list(current.items())
            for n in (1, 2, 3):
                press, profile = pairs[n - 1] if len(pairs) >= n else (None, None)
                fields[vol.Optional(f"press_{n}", description={"suggested_value": press})] = (
                    TextSelector()
                )
                fields[vol.Optional(f"profile_{n}", description={"suggested_value": profile})] = (
                    self._control_profile_selector()
                )
        return self.async_show_form(
            step_id="control_presses_event" if known else "control_presses",
            data_schema=vol.Schema(fields),
            errors=errors,
            description_placeholders={"entity": str(data.get("entity") or "")},
        )

    async def async_step_control_presses_event(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self.async_step_control_presses(user_input)

    def _event_types(self, entity_id: str) -> list[str]:
        """Druckarten einer Ereignis-Entität (Attribut ``event_types``)."""
        if not entity_id.startswith("event."):
            return []
        state = self.hass.states.get(entity_id)
        types = state.attributes.get("event_types") if state else None
        return [t for t in types if isinstance(t, str) and t] if isinstance(types, list) else []

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
            if not _presence_persons(options):
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
        """Zusätzliche Signale je Person (WLAN, Bluetooth, Annäherung …).

        Gelten für die Heimkehr-Beobachtung UND die Profil-Automatik ("alle weg", "Rückkehr").
        """
        options = dict(self._pending or self.config_entry.options)
        persons = _presence_persons(options)
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

    def _new_card_options(self) -> list[SelectOptionDict]:
        """Zuletzt gelesene unbekannte Karten zum Anlernen ("neu, gelesen an … um …")."""
        lang = "de" if self._german() else "en"
        unknown = self._unknown_cards()
        self._offered_new = set(unknown)
        options: list[SelectOptionDict] = []
        for tag, (source, when) in unknown.items():
            time_text = dt_util.as_local(dt_util.utc_from_timestamp(when)).strftime("%H:%M")
            hint = (
                f"neu, gelesen an {source} um {time_text}"
                if lang == "de"
                else f"new, read at {source} at {time_text}"
            )
            options.append(
                SelectOptionDict(value=tag, label=f"{lock_id_label(tag, lang)} ({hint})")
            )
        return options

    def _card_error(self, tag: str, stored: Mapping[str, Any]) -> tuple[str, str] | None:
        """Neue Karte: fehlt, gehört schon jemandem, Zufallsnummer, oder inzwischen abgelaufen."""
        if not tag:
            return "card_missing", ""
        if (owner := _tag_owner([tag], None, stored)) is not None:
            return "tag_taken", owner
        if is_random_uid(tag):
            return "tag_random", tag
        if tag in self._offered_new and tag not in self._unknown_cards():
            return "card_expired", tag
        return None

    def _random_hint(self) -> str:
        """Hinweis, wenn kürzlich eine Zufallsnummer (z. B. Handy) gelesen wurde."""
        controls = (
            getattr(self.config_entry.runtime_data, "controls", None) if self._loaded() else None
        )
        seen = controls.recent_random() if controls is not None else None
        if seen is None:
            return ""
        source, when = seen
        time_text = dt_util.as_local(dt_util.utc_from_timestamp(when)).strftime("%H:%M")
        if self._german():
            return (
                f"\n\n⚠️ An {source} wurde um {time_text} eine **Zufallsnummer** gelesen "
                "(z. B. ein Handy oder ein Ausweis mit Datenschutz-Modus). Sie ändert sich bei "
                "jedem Lesen und taugt nicht als Ausweis – deshalb wird sie nicht zum Anlernen "
                "angeboten."
            )
        return (
            f"\n\n⚠️ A **random ID** was read at {source} at {time_text} (e.g. a phone or a "
            "privacy-mode badge). It changes on every read and cannot be used as a credential – "
            "so it is not offered for learning."
        )

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
                vol.Optional(
                    "can_force_arm", default=bool(current.get("can_force_arm", True))
                ): BooleanSelector(),
                vol.Optional("ha_user", description=ha_desc): SelectSelector(
                    SelectSelectorConfig(
                        options=await self._ha_user_options(), mode=SelectSelectorMode.DROPDOWN
                    )
                ),
                vol.Optional("card_pin", default=bool(current.get("card_pin", False))): (
                    BooleanSelector()
                ),
                vol.Optional(
                    "valid_from", description=_suggested_local(current.get("valid_from"))
                ): DateTimeSelector(),
                vol.Optional(
                    "valid_until", description=_suggested_local(current.get("valid_until"))
                ): DateTimeSelector(),
                **self._user_area_field(current),
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


def _presence_persons(options: Mapping[str, Any]) -> list[str]:
    """Personen der Heimkehr-Beobachtung und der Profil-Automatik (ohne Doppelte)."""
    persons = [p for p in options.get(OPT_HOMECOMING_PERSONS, []) if isinstance(p, str)]
    for pid in profile_ids(options):
        persons.extend(parse_automation(options, pid).away_persons)
    return list(dict.fromkeys(persons))


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
            vol.Optional("auto_schedule", description=suggested(auto.schedule)): EntitySelector(
                EntitySelectorConfig(domain="schedule")
            ),
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
            vol.Optional("auto_arrival_mode", default=auto.arrival_mode): _select(
                list(ARRIVAL_MODES), "arrival_mode"
            ),
            vol.Optional("auto_arrival_window", default=auto.arrival_window): NumberSelector(
                NumberSelectorConfig(
                    min=1,
                    max=MAX_ARRIVAL_WINDOW,
                    step=1,
                    unit_of_measurement="min",
                    mode=NumberSelectorMode.BOX,
                )
            ),
        }
    )


def _current_value(state: Any, attribute: str | None) -> Any:
    """Aktueller Wert einer Quelle mit Kippstellung (Zustand oder Attribut)."""
    return state.state if attribute is None else state.attributes.get(attribute)


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


def _tag_input(value: Any) -> list[str]:
    """Karten aus der Auswahl (Liste) oder – wie früher – als Text mit Komma."""
    items = value if isinstance(value, list) else str(value or "").split(",")
    return list(dict.fromkeys(t for t in (normalize_tag(i) for i in items) if t))


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
