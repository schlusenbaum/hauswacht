"""Einrichtung und Optionen von Hauswacht."""

from __future__ import annotations

import copy
from collections.abc import Mapping
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
from .core.sensors import (
    Zone,
    parse_zones,
    resolve_zones,
    slugify,
    zone_conflicts,
)
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
    VERSION = 4

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
        return text + "\n\n"

    def _finding_text(self, finding: Finding) -> str:
        texts = FINDING_TEXTS_DE if self._german() else FINDING_TEXTS_EN
        return texts.get(finding.code, finding.code).format(
            rule=finding.rule, step=finding.step or "", detail=finding.detail
        )

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

    def _is_disarmed(self) -> bool:
        entry = self.config_entry
        if entry.state is not ConfigEntryState.LOADED:
            return True
        return bool(entry.runtime_data.ctx.state is AlarmState.DISARMED)

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
                        **_automation_from_input(user_input.get("automation") or {}),
                    }
                )
                profiles[profile_id] = data
                options[OPT_PROFILES] = profiles
                self._hints = self._profile_hints(options, profile_id)
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

    # --- Regeln ------------------------------------------------------------

    async def async_step_triggering(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Alarmauslösung: Meldergruppen und Auslöseregeln."""
        return self._menu("triggering", ["zones", "rules", "init"])

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
                    EntitySelector(EntitySelectorConfig(domain=SENSOR_DOMAIN, multiple=True))
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
                    EntitySelectorConfig(domain=SENSOR_DOMAIN, multiple=True)
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
