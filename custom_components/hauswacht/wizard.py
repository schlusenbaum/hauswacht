"""Einrichtungsassistent (Teil 1): Einführung, Melder, Überwachungsart, Gruppen, Profile,
Zusammenfassung – ADR 0009.

Die Schritte stehen in einer Mixin-Klasse und werden sowohl von der Erstinstallation
(Config-Flow, startet automatisch) als auch vom Einstellungsdialog (Options-Flow, Menüpunkt
„Einrichtungsassistent“) genutzt. Gespeichert wird nur über die Einstellungsregeln in
``core/changes`` bzw. ``core/wizard``; der Assistent hat keine eigenen Regeln.

- Options-Flow: jeder Schritt speichert sofort (``_wizard_store`` -> ``_save``).
- Config-Flow: gesammelt, die Anlage wird am Ende mit diesen Einstellungen angelegt.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import floor_registry as fr
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
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

from .const import DOMAIN
from .core.changes.notifications import set_general_recipients
from .core.changes.profiles import save_profile
from .core.changes.sirens import save_sirens
from .core.changes.users import save_user, set_pins
from .core.profiles import MAX_DELAY, profile_infos, profile_settings
from .core.rules import parse_rules
from .core.sensor_types import MONITORED_DOMAINS, SensorType, parse_types, sensor_type
from .core.sensors import parse_zones
from .core.wizard import (
    AWAY,
    DEFAULT_ENTRY_DELAY,
    DEFAULT_EXIT_DELAY,
    MODE_BOTH,
    MODE_RULES,
    MODE_ZONES,
    NIGHT,
    Candidate,
    default_night_zones,
    save_groups,
    save_wizard_profile,
    set_entry_doors,
    split_outside_inside,
    status,
    suggest_sensors,
)
from .names import display_name
from .runtime import device_class_of, entities_by_label

MAX_LISTED = 40  # so viele Vorschläge stehen im Text, der Rest als "… und N weitere"


def candidates(hass: HomeAssistant) -> list[Candidate]:
    """Mögliche Melder aus Home Assistant, mit Etage und Raum."""
    entities = er.async_get(hass)
    devices = dr.async_get(hass)
    areas = ar.async_get(hass)
    floors = fr.async_get(hass)
    result: list[Candidate] = []
    for entity_id in hass.states.async_entity_ids("binary_sensor"):
        entry = entities.async_get(entity_id)
        if entry is not None and (
            entry.disabled_by is not None or entry.hidden_by is not None or entry.platform == DOMAIN
        ):
            continue
        area_id = entry.area_id if entry else None
        if entry is not None and area_id is None and entry.device_id:
            device = devices.async_get(entry.device_id)
            area_id = device.area_id if device else None
        area = areas.async_get_area(area_id) if area_id else None
        floor = floors.async_get_floor(area.floor_id) if area and area.floor_id else None
        place = " › ".join(
            x for x in ((floor.name if floor else ""), area.name if area else "") if x
        )
        result.append(
            Candidate(
                entity_id=entity_id,
                name=display_name(hass, entity_id),
                device_class=device_class_of(hass, entity_id),
                place=place,
            )
        )
    return result


class WizardSteps:
    """Schritte des Assistenten. Erwartet ``hass`` und die Methoden unten."""

    hass: HomeAssistant
    _wiz_sensors: list[str] | None = None
    _wiz_mode: str = MODE_ZONES
    _wiz_return: str | None = None
    _wiz_test_result: str = ""

    # --- von der jeweiligen Flow-Klasse bereitgestellt ------------------------

    def _wizard_options(self) -> Mapping[str, Any]:
        raise NotImplementedError

    async def _wizard_store(self, options: dict[str, Any], next_step: str) -> ConfigFlowResult:
        raise NotImplementedError

    async def _wizard_finish(self) -> ConfigFlowResult:
        raise NotImplementedError

    def _wizard_rules_possible(self) -> bool:
        """Auslöseregeln gibt es nur im Einstellungsdialog (Regel-Assistent)."""
        return False

    if TYPE_CHECKING:
        # kommen von der Flow-Klasse (FlowHandler); das Mixin steht dort hinten in der Basisliste
        def async_show_form(self, **kwargs: Any) -> ConfigFlowResult: ...

        def async_show_menu(self, **kwargs: Any) -> ConfigFlowResult: ...

    # --- Hilfen ----------------------------------------------------------------

    def _de(self) -> bool:
        return (self.hass.config.language or "").startswith("de")

    def _classes(self, entity_ids: list[str]) -> dict[str, str | None]:
        return {e: device_class_of(self.hass, e) for e in entity_ids}

    def _names(self, entity_ids: list[str] | set[str]) -> str:
        names = sorted((display_name(self.hass, e) for e in entity_ids), key=str.casefold)
        return ", ".join(names) if names else "–"

    # --- Start -----------------------------------------------------------------

    async def async_step_wizard(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        self._wiz_sensors = None
        self._wiz_return = None
        return self.async_show_menu(
            step_id="wizard", menu_options=["wizard_intro", "wizard_sensors"]
        )

    async def async_step_wizard_intro(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return await self.async_step_wizard_sensors()
        return self.async_show_form(step_id="wizard_intro", data_schema=vol.Schema({}))

    # --- Melder ----------------------------------------------------------------

    async def async_step_wizard_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        options = self._wizard_options()
        if user_input is not None:
            self._wiz_sensors = [str(e) for e in user_input.get("sensors") or []]
            return await self.async_step_wizard_mode()
        found = suggest_sensors(candidates(self.hass), options, entities_by_label(self.hass))
        lines = []
        place = None
        for candidate in found[:MAX_LISTED]:
            if candidate.place != place:
                place = candidate.place
                lines.append(f"\n**{place or ('ohne Raum' if self._de() else 'no room')}**")
            lines.append(f"- {candidate.name}")
        if len(found) > MAX_LISTED:
            more = len(found) - MAX_LISTED
            lines.append(f"- … und {more} weitere" if self._de() else f"- … and {more} more")
        if not found:
            lines.append(
                "Keine neuen Türen, Fenster oder Bewegungsmelder gefunden."
                if self._de()
                else "No new doors, windows or motion sensors found."
            )
        default = (
            self._wiz_sensors if self._wiz_sensors is not None else [c.entity_id for c in found]
        )
        schema = vol.Schema(
            {
                vol.Optional("sensors", default=default): EntitySelector(
                    EntitySelectorConfig(domain=list(MONITORED_DOMAINS), multiple=True)
                )
            }
        )
        return self.async_show_form(
            step_id="wizard_sensors",
            data_schema=schema,
            description_placeholders={"found": "\n".join(lines).strip()},
        )

    # --- Überwachungsart ---------------------------------------------------------

    async def async_step_wizard_mode(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self.async_show_menu(
            step_id="wizard_mode",
            menu_options=[
                "wizard_mode_zones",
                "wizard_mode_rules",
                "wizard_mode_both",
                "wizard_recipients",
            ],
        )

    async def async_step_wizard_mode_zones(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        self._wiz_mode = MODE_ZONES
        return await self.async_step_wizard_groups()

    async def async_step_wizard_mode_rules(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        self._wiz_mode = MODE_RULES
        return await self.async_step_wizard_rules()

    async def async_step_wizard_mode_both(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        self._wiz_mode = MODE_BOTH
        return await self.async_step_wizard_groups()

    # --- Meldergruppen -----------------------------------------------------------

    async def async_step_wizard_groups(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        options = self._wizard_options()
        errors: dict[str, str] = {}
        placeholders = {"conflicts": ""}
        de = self._de()
        if user_input is not None:
            outside = [str(e) for e in user_input.get("outside") or []]
            inside = [str(e) for e in user_input.get("inside") or []]
            groups = [
                (str(user_input.get("outside_name") or "").strip(), outside),
                (str(user_input.get("inside_name") or "").strip(), inside),
            ]
            change = save_groups(options, groups, labels=entities_by_label(self.hass))
            if change.ok:
                assert change.options is not None
                entry_doors = [e for e in user_input.get("entry_doors") or [] if e in outside]
                new = set_entry_doors(change.options, outside, entry_doors, self._classes(outside))
                nxt = "wizard_rules" if self._wiz_mode == MODE_BOTH else "wizard_profiles"
                return await self._wizard_store(new, nxt)
            errors = dict(change.errors)
            conflicts = change.details.get("conflicts") or {}
            listed = ", ".join(
                f"{display_name(self.hass, e)} ({zone})" for e, zone in conflicts.items()
            )
            if listed:
                head = "Schon in einer anderen Gruppe" if de else "Already in another group"
                placeholders["conflicts"] = f"\n\n⚠️ {head}: {listed}"
        sensors = self._wiz_sensors or []
        outside, inside = split_outside_inside(sensors, self._classes(sensors), options)
        types = parse_types(options)
        doors = [
            e
            for e in outside
            if sensor_type(e, device_class_of(self.hass, e), types) is SensorType.DOOR
        ]
        source = user_input or {}
        schema = vol.Schema(
            {
                vol.Optional(
                    "outside_name", default=source.get("outside_name", "Außen" if de else "Outside")
                ): TextSelector(),
                vol.Optional("outside", default=source.get("outside", outside)): EntitySelector(
                    EntitySelectorConfig(domain=list(MONITORED_DOMAINS), multiple=True)
                ),
                vol.Optional("entry_doors", default=source.get("entry_doors", doors)): (
                    EntitySelector(
                        EntitySelectorConfig(domain=list(MONITORED_DOMAINS), multiple=True)
                    )
                ),
                vol.Optional(
                    "inside_name", default=source.get("inside_name", "Innen" if de else "Inside")
                ): TextSelector(),
                vol.Optional("inside", default=source.get("inside", inside)): EntitySelector(
                    EntitySelectorConfig(domain=list(MONITORED_DOMAINS), multiple=True)
                ),
            }
        )
        return self.async_show_form(
            step_id="wizard_groups",
            data_schema=schema,
            errors=errors,
            description_placeholders=placeholders,
        )

    # --- Auslöseregeln -----------------------------------------------------------

    async def async_step_wizard_rules(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        rules = parse_rules(self._wizard_options())
        listed = ", ".join(r.name for r in rules.values()) or "–"
        if not self._wizard_rules_possible():
            return self.async_show_form(step_id="wizard_rules_later", data_schema=vol.Schema({}))
        # Nach dem Speichern einer Regel kommt der Regel-Assistent hierher zurück
        self._wiz_return = "wizard_rules"
        return self.async_show_menu(
            step_id="wizard_rules",
            menu_options=["rule_add", "wizard_profiles"],
            description_placeholders={"rules": listed},
        )

    async def async_step_wizard_rules_later(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self.async_step_wizard_profiles()

    # --- Alarmprofile ------------------------------------------------------------

    def _zone_select(self, options: Mapping[str, Any]) -> SelectSelector:
        return SelectSelector(
            SelectSelectorConfig(
                options=[
                    SelectOptionDict(value=z, label=zone.name)
                    for z, zone in parse_zones(options).items()
                ],
                multiple=True,
                mode=SelectSelectorMode.LIST,
            )
        )

    def _rule_select(self, options: Mapping[str, Any]) -> SelectSelector:
        return SelectSelector(
            SelectSelectorConfig(
                options=[
                    SelectOptionDict(value=r, label=rule.name)
                    for r, rule in parse_rules(options).items()
                ],
                multiple=True,
                mode=SelectSelectorMode.LIST,
            )
        )

    async def async_step_wizard_profiles(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        self._wiz_return = None
        options = self._wizard_options()
        zones = parse_zones(options)
        rules = parse_rules(options)
        if not zones and not rules:
            return await self.async_step_wizard_recipients()
        errors: dict[str, str] = {}
        if user_input is not None:
            current: dict[str, Any] = dict(options)
            exit_delay = int(user_input.get("exit_delay", DEFAULT_EXIT_DELAY))
            entry_delay = int(user_input.get("entry_delay", DEFAULT_ENTRY_DELAY))
            plan = [
                (AWAY, "away", {"exit_delay": exit_delay, "entry_delay": entry_delay}),
                (NIGHT, "night", {"entry_delay": entry_delay}),
            ]
            for mode, key, delays in plan:
                if not user_input.get(key):
                    continue
                chosen_zones = list(user_input.get(f"{key}_zones") or [])
                chosen_rules = list(user_input.get(f"{key}_rules") or [])
                if not chosen_zones and not chosen_rules:
                    errors[f"{key}_zones"] = "wizard_profile_empty"
                    continue
                change = save_wizard_profile(
                    current,
                    mode,
                    {"zones": chosen_zones, "rules": chosen_rules, **delays},
                    language="de" if self._de() else "en",
                    labels=entities_by_label(self.hass),
                    new_only={"exit_delay": 0} if mode == NIGHT else None,
                )
                if not change.ok:
                    errors.update(change.errors)
                    continue
                assert change.options is not None
                current = change.options
            if not errors:
                return await self._wizard_store(current, "wizard_recipients")
        existing = {i.panel_mode: i.profile_id for i in profile_infos(options)}
        away_id = existing.get(AWAY)
        times = profile_settings(options, away_id) if away_id else None
        all_members = [e for z in zones.values() for e in z.entities]
        night_default = default_night_zones(
            options, self._classes(all_members), entities_by_label(self.hass)
        )
        source = user_input or {}
        delay = NumberSelector(
            NumberSelectorConfig(
                min=0, max=MAX_DELAY, step=1, unit_of_measurement="s", mode=NumberSelectorMode.BOX
            )
        )
        fields: dict[Any, Any] = {
            vol.Optional("away", default=source.get("away", True)): BooleanSelector(),
            vol.Optional("away_zones", default=source.get("away_zones", list(zones))): (
                self._zone_select(options)
            ),
        }
        if rules:
            fields[vol.Optional("away_rules", default=source.get("away_rules", list(rules)))] = (
                self._rule_select(options)
            )
        fields.update(
            {
                vol.Optional(
                    "exit_delay",
                    default=source.get(
                        "exit_delay", times["exit_delay"] if times else DEFAULT_EXIT_DELAY
                    ),
                ): delay,
                vol.Optional(
                    "entry_delay",
                    default=source.get(
                        "entry_delay", times["entry_delay"] if times else DEFAULT_ENTRY_DELAY
                    ),
                ): delay,
                vol.Optional("night", default=source.get("night", True)): BooleanSelector(),
                vol.Optional("night_zones", default=source.get("night_zones", night_default)): (
                    self._zone_select(options)
                ),
            }
        )
        if rules:
            fields[vol.Optional("night_rules", default=source.get("night_rules", []))] = (
                self._rule_select(options)
            )
        return self.async_show_form(
            step_id="wizard_profiles", data_schema=vol.Schema(fields), errors=errors
        )

    # --- Empfänger (Teil 2) -------------------------------------------------------

    def _notify_choices(self) -> list[str]:
        services = self.hass.services.async_services_for_domain("notify")
        return sorted(
            s for s in services if s not in {"send_message", "notify", "persistent_notification"}
        )

    async def async_step_wizard_recipients(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        options = self._wizard_options()
        choices = self._notify_choices()
        if user_input is not None:
            chosen = [t for t in user_input.get("recipients") or [] if t in choices]
            if not chosen:
                return await self.async_step_wizard_sirens()
            change = set_general_recipients(options, chosen)
            assert change.options is not None
            return await self._wizard_store(change.options, "wizard_recipients_test")
        current = [t for t in options.get("notify_system") or [] if t in choices]
        default = current or [c for c in choices if c.startswith("mobile_app_")]
        schema = vol.Schema(
            {
                vol.Optional("recipients", default=default): SelectSelector(
                    SelectSelectorConfig(
                        options=choices, multiple=True, mode=SelectSelectorMode.LIST
                    )
                )
            }
        )
        return self.async_show_form(step_id="wizard_recipients", data_schema=schema)

    async def async_step_wizard_recipients_test(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        targets = list(self._wizard_options().get("notify_system") or [])
        return self.async_show_menu(
            step_id="wizard_recipients_test",
            menu_options=["wizard_send_test", "wizard_sirens"],
            description_placeholders={
                "recipients": ", ".join(targets) or "–",
                "result": getattr(self, "_wiz_test_result", ""),
            },
        )

    async def async_step_wizard_send_test(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Test-Nachricht – nur auf ausdrücklichen Knopfdruck."""
        de = self._de()
        title = "Hauswacht"
        message = (
            "Test-Nachricht aus dem Einrichtungsassistenten. Kommt sie an, erreichen dich auch "
            "Alarm-Nachrichten."
            if de
            else "Test message from the setup wizard. If it arrives, alarm messages reach you too."
        )
        ok: list[str] = []
        failed_targets: list[str] = []
        for target in self._wizard_options().get("notify_system") or []:
            try:
                await self.hass.services.async_call(
                    "notify", target, {"title": title, "message": message}, blocking=True
                )
                ok.append(target)
            except Exception:
                failed_targets.append(target)
        lines = []
        if ok:
            lines.append(("✅ Gesendet an: " if de else "✅ Sent to: ") + ", ".join(ok))
        if failed_targets:
            lines.append(("⚠️ Fehlgeschlagen: " if de else "⚠️ Failed: ") + ", ".join(failed_targets))
        self._wiz_test_result = "\n\n" + "\n".join(lines) if lines else ""
        return await self.async_step_wizard_recipients_test()

    # --- Sirenen (Teil 2) ----------------------------------------------------------

    def _wizard_siren_test_possible(self) -> bool:
        """Sirenentest gibt es nur im Einstellungsdialog (braucht die laufende Anlage)."""
        return False

    async def async_step_wizard_sirens(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        self._wiz_test_result = ""
        options = self._wizard_options()
        profiles = {i.profile_id: i.name for i in profile_infos(options)}
        if user_input is not None:
            chosen = [str(s) for s in user_input.get("sirens") or []]
            if not chosen:
                return await self.async_step_wizard_users()
            change = save_sirens(options, {"sirens": chosen})
            assert change.options is not None
            current = change.options
            for profile_id in user_input.get("profiles") or []:
                if profile_id not in profiles:
                    continue
                stored = current.get("profiles", {}).get(profile_id, {})
                merged = list(dict.fromkeys([*stored.get("sirens", []), *chosen]))
                updated = save_profile(
                    current,
                    profile_id,
                    {"name": profiles[profile_id], "sirens": merged},
                    partial=True,
                )
                if updated.ok:
                    assert updated.options is not None
                    current = updated.options
            nxt = "wizard_sirens_test" if self._wizard_siren_test_possible() else "wizard_users"
            return await self._wizard_store(current, nxt)
        found = sorted(self.hass.states.async_entity_ids("siren"))
        default = list(options.get("sirens") or []) or found
        schema = vol.Schema(
            {
                vol.Optional("sirens", default=default): EntitySelector(
                    EntitySelectorConfig(domain="siren", multiple=True)
                ),
                vol.Optional("profiles", default=list(profiles)): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(value=pid, label=name)
                            for pid, name in profiles.items()
                        ],
                        multiple=True,
                        mode=SelectSelectorMode.LIST,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="wizard_sirens", data_schema=schema)

    async def async_step_wizard_sirens_test(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        # Nach dem Sirenentest kommt der Einstellungsdialog hierher zurück
        self._wiz_return = "wizard_sirens_test"
        return self.async_show_menu(
            step_id="wizard_sirens_test", menu_options=["siren_test", "wizard_users"]
        )

    # --- Benutzer (Teil 2) ---------------------------------------------------------

    async def _ha_account(self, name: str) -> str | None:
        for user in await self.hass.auth.async_get_users():
            if (
                user.is_active
                and not user.system_generated
                and (user.name or "").casefold() == (name.casefold())
            ):
                return user.id
        return None

    async def async_step_wizard_users(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        self._wiz_return = None
        options = self._wizard_options()
        errors: dict[str, str] = {}
        placeholders = {"users": "", "conflict": ""}
        if user_input is not None:
            name = str(user_input.get("name") or "").strip()
            if not name:
                return await self.async_step_wizard_controls()
            change = save_user(options, None, {"name": name}, ha_user=await self._ha_account(name))
            errors = dict(change.errors)
            pin = str(user_input.get("pin") or "").strip()
            if change.ok and pin:
                assert change.options is not None
                assert change.item_id is not None
                with_pin = await self.hass.async_add_executor_job(
                    set_pins, change.options, change.item_id, {"new_pin": pin}
                )
                errors = {"pin" if k == "new_pin" else k: v for k, v in with_pin.errors.items()}
                placeholders["conflict"] = str(with_pin.details.get("conflict") or "")
                change = with_pin
            if not errors:
                assert change.options is not None
                return await self._wizard_store(change.options, "wizard_users_more")
        names = [str(d.get("name")) for d in (options.get("users") or {}).values()]
        placeholders["users"] = ", ".join(names) or "–"
        schema = vol.Schema(
            {
                vol.Optional("name"): TextSelector(),
                vol.Optional("pin"): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
            }
        )
        return self.async_show_form(
            step_id="wizard_users",
            data_schema=schema,
            errors=errors,
            description_placeholders=placeholders,
        )

    async def async_step_wizard_users_more(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        names = [str(d.get("name")) for d in (self._wizard_options().get("users") or {}).values()]
        return self.async_show_menu(
            step_id="wizard_users_more",
            menu_options=["wizard_users", "wizard_controls"],
            description_placeholders={"users": ", ".join(names) or "–"},
        )

    # --- Bedienteile (Teil 2, nur Hinweis) -----------------------------------------

    async def async_step_wizard_controls(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return await self.async_step_wizard_summary()
        return self.async_show_form(step_id="wizard_controls", data_schema=vol.Schema({}))

    # --- Zusammenfassung ---------------------------------------------------------

    def _summary_text(self) -> str:
        result = status(self._wizard_options())
        de = self._de()
        done: list[str] = []
        todo: list[str] = []
        if result.zones:
            done.append(("Meldergruppen: " if de else "Sensor groups: ") + ", ".join(result.zones))
        if result.rules:
            done.append(("Auslöseregeln: " if de else "Trigger rules: ") + ", ".join(result.rules))
        for name, zones, rules in result.profiles:
            watched = ", ".join([*zones, *rules]) or "–"
            done.append(
                f"Alarmprofil {name}: überwacht {watched}"
                if de
                else f"Alarm profile {name}: watches {watched}"
            )
        if not result.zones and not result.rules:
            todo.append(
                "Noch nichts wird überwacht – Meldergruppen oder Auslöseregeln fehlen."
                if de
                else "Nothing is monitored yet – sensor groups or trigger rules are missing."
            )
        if not result.profiles:
            todo.append(
                "Kein Alarmprofil – scharf schalten geht noch nicht."
                if de
                else "No alarm profile – arming is not possible yet."
            )
        if not result.recipients:
            todo.append(
                "Keine Empfänger – ein Alarm erreicht noch niemanden "
                "(Benachrichtigungen → Einstellungen)."
                if de
                else "No recipients – an alarm reaches nobody yet (Notifications → Settings)."
            )
        if result.sirens and not result.sirens_released:
            todo.append(
                "Sirenen eingetragen, aber noch nicht freigegeben – bewusst unter Alarmgeber – "
                "Sirenen → Sirenen und Freigabe, wenn alles passt."
                if de
                else "Sirens added but not released yet – deliberately under Alarm devices – "
                "sirens → Sirens and release, once everything works."
            )
        if not result.sirens:
            todo.append(
                "Keine Sirenen (Alarmgeber – Sirenen)."
                if de
                else "No sirens (Alarm devices – sirens)."
            )
        if not result.users:
            todo.append(
                "Keine Benutzer – bedient wird nur über die App (Systemeinstellungen → Benutzer)."
                if de
                else "No users – operated via the app only (System settings → Users)."
            )
        head_done = "✅ **Eingerichtet**" if de else "✅ **Set up**"
        head_todo = "⚠️ **Noch offen**" if de else "⚠️ **Still open**"
        text = head_done + "\n" + ("\n".join(f"- {d}" for d in done) if done else "- –")
        if todo:
            text += "\n\n" + head_todo + "\n" + "\n".join(f"- {t}" for t in todo)
        return text

    async def async_step_wizard_summary(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        self._wiz_return = None
        if user_input is not None:
            return await self._wizard_finish()
        return self.async_show_form(
            step_id="wizard_summary",
            data_schema=vol.Schema({}),
            description_placeholders={"summary": self._summary_text()},
        )
