"""Alarm-Bedienfeld von Hauswacht."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
    CodeFormat,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
    async_get_current_platform,
)

from .const import DOMAIN
from .core.areas import ALL_PANEL_KEY
from .core.profiles import (
    find_profile,
    panel_state,
    profile_for_mode,
    profile_info,
    used_panel_modes,
)
from .core.siren_test import DEFAULT_SECONDS, DEFAULT_TONE, DEFAULT_VOLUME, TONES, VOLUMES
from .core.state_machine import AlarmState
from .core.users import Action
from .entity import HauswachtEntity
from .runtime import HauswachtConfigEntry, HauswachtRuntime
from .siren_test import SirenTester

_FEATURE_BY_MODE: dict[str, AlarmControlPanelEntityFeature] = {
    "home": AlarmControlPanelEntityFeature.ARM_HOME,
    "night": AlarmControlPanelEntityFeature.ARM_NIGHT,
    "away": AlarmControlPanelEntityFeature.ARM_AWAY,
    "vacation": AlarmControlPanelEntityFeature.ARM_VACATION,
    "custom": AlarmControlPanelEntityFeature.ARM_CUSTOM_BYPASS,
}

_STATE_MAP: dict[AlarmState, AlarmControlPanelState] = {
    AlarmState.DISARMED: AlarmControlPanelState.DISARMED,
    AlarmState.ARMING: AlarmControlPanelState.ARMING,
    AlarmState.PENDING: AlarmControlPanelState.PENDING,
    AlarmState.TRIGGERED: AlarmControlPanelState.TRIGGERED,
    AlarmState.ALARM_HOLD: AlarmControlPanelState.TRIGGERED,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HauswachtConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    main = entry.runtime_data
    panels: list[AlarmControlPanelEntity] = [
        HauswachtAlarmPanel(entry, area) for area in main.areas.values()
    ]
    if len(main.areas) > 1:
        panels.append(HauswachtAllPanel(entry))
    async_add_entities(panels)
    async_get_current_platform().async_register_entity_service(
        "arm",
        {
            vol.Required("profile"): cv.string,
            vol.Optional("confirm", default=False): cv.boolean,
            vol.Optional("code"): cv.string,
        },
        "async_arm_profile",
    )
    async_get_current_platform().async_register_entity_service(
        "simulate_trigger",
        {vol.Required("sensor"): cv.entity_id},
        "async_simulate_trigger",
    )
    async_get_current_platform().async_register_entity_service(
        "simulate_state",
        {
            vol.Required("sensor"): cv.entity_id,
            vol.Required("state"): vol.In(["on", "off", "unavailable", "real"]),
        },
        "async_simulate_state",
    )
    async_get_current_platform().async_register_entity_service(
        "simulate_reset", {}, "async_simulate_reset"
    )
    async_get_current_platform().async_register_entity_service(
        "siren_test",
        {
            vol.Required("siren"): cv.entity_id,
            vol.Optional("duration", default=DEFAULT_SECONDS): vol.Coerce(float),
            vol.Optional("volume", default=DEFAULT_VOLUME): vol.In(VOLUMES),
            vol.Optional("tone", default=DEFAULT_TONE): vol.In(TONES),
        },
        "async_siren_test",
    )
    async_get_current_platform().async_register_entity_service(
        "siren_test_result",
        {vol.Required("siren"): cv.entity_id, vol.Required("heard"): cv.boolean},
        "async_siren_test_result",
    )
    async_get_current_platform().async_register_entity_service(
        "siren_test_stop", {}, "async_siren_test_stop"
    )


class _SirenTestMixin(HauswachtEntity):
    """Dienste für den Sirenentest (an jedem Bedienfeld, wirken immer über den Hauptbereich)."""

    async def _admin_name(self) -> str | None:
        """Sirenentest nur für Administratoren (oder ohne Benutzer, z. B. Automationen)."""
        if self._context is None or self._context.user_id is None:
            return None
        user = await self.hass.auth.async_get_user(self._context.user_id)
        if user is None or not user.is_admin:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="siren_test_admin_only"
            )
        return user.name

    def _tester(self) -> SirenTester:
        tester = self.runtime.main.siren_tester
        assert tester is not None  # Hauptbereich hat immer einen
        return tester

    async def async_siren_test(self, siren: str, duration: float, volume: str, tone: str) -> None:
        """Dienst hauswacht.siren_test: eine Sirene kurz prüfen (echter Ton!)."""
        by = await self._admin_name()
        tester = self._tester()
        result = await tester.async_run(
            siren,
            tone=tone,
            volume=volume,
            seconds=duration,
            by=by,
            prewarn=tester.settings.prewarn,
        )
        if not result["started"]:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="siren_test_blocked",
                translation_placeholders={"reason": str(result["reason"])},
            )

    async def async_siren_test_result(self, siren: str, heard: bool) -> None:
        by = await self._admin_name()
        self._tester().record(siren, heard, by=by)

    async def async_siren_test_stop(self) -> None:
        self._tester().stop()


class HauswachtAlarmPanel(_SirenTestMixin, AlarmControlPanelEntity):
    _attr_name = None  # Entität heißt wie das Gerät: "Hauswacht"
    _attr_translation_key = "panel"

    def __init__(self, entry: HauswachtConfigEntry, runtime: HauswachtRuntime) -> None:
        super().__init__(entry, "panel", runtime)
        # Nur Knöpfe anbieten, denen ein Profil zugeordnet ist. Optionen ändern lädt neu.
        features = AlarmControlPanelEntityFeature(0)
        for mode in used_panel_modes(self.runtime.options):
            features |= _FEATURE_BY_MODE[mode]
        self._attr_supported_features = features

    @property
    def alarm_state(self) -> AlarmControlPanelState:
        ctx = self.runtime.ctx
        if ctx.state is AlarmState.ARMED and ctx.profile is not None:
            return AlarmControlPanelState(panel_state(self.runtime.options, ctx.profile.profile_id))
        return _STATE_MAP[ctx.state]

    @property
    def icon(self) -> str | None:
        """Im scharfen Zustand das Symbol des aktiven Profils."""
        profile = self.runtime.ctx.profile
        if profile is None:
            return None
        return profile_info(self.runtime.entry.options, profile.profile_id).icon

    @property
    def code_format(self) -> CodeFormat | None:
        return CodeFormat.NUMBER if self.runtime.has_codes else None

    @property
    def code_arm_required(self) -> bool:
        return self.runtime.code_arm_required

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        ctx = self.runtime.ctx
        ends_at = self.runtime.delay_ends_at
        readiness = self.runtime.readiness_for(self.runtime.candidates)
        return {
            "area": self.runtime.area_id,
            "area_name": self.runtime.area_name,
            "profile": ctx.profile.profile_id if ctx.profile else None,
            "profile_name": self.runtime.profile_name(ctx.profile.profile_id)
            if ctx.profile
            else None,
            "phase": ctx.state.value,
            "test_mode": ctx.test_mode,
            "timer": ctx.timer_kind.value if ctx.timer_kind else None,
            "timer_ends_at": ends_at.isoformat() if ends_at else None,
            "trigger_sensor": ctx.trigger_sensor,
            "alarm_cycles": ctx.alarm_cycles,
            "bypassed_sensors": sorted(ctx.bypassed),
            "bypassed_until_closed": sorted(ctx.bypassed_until_closed),
            "monitored_sensors": sorted(self.runtime.armed_sensors),
            "open_rule_sensors": sorted(self.runtime.open_rule_sensors()),
            "open_sensors": sorted(readiness.open_sensors),
            "unavailable_sensors": sorted(readiness.unavailable_sensors),
            "zones": self.runtime.zone_members(),
            "last_contact": self.runtime.last_contacts(),
            "sirens_hardware_enabled": self.runtime.sirens.hardware_enabled,
            "last_siren_decision": self.runtime.sirens.last_result or None,
        }

    @property
    def changed_by(self) -> str | None:
        return self.runtime.changed_by

    @property
    def _user_id(self) -> str | None:
        return self._context.user_id if self._context else None

    async def _arm_mode(self, mode: str, code: str | None) -> None:
        profile_id = profile_for_mode(self.runtime.options, mode)
        if profile_id is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="no_profile_for_mode",
                translation_placeholders={"mode": mode},
            )
        await self._arm(profile_id, code)

    async def _arm(self, profile_id: str, code: str | None, *, confirm: bool = False) -> None:
        actor = await self.runtime.async_authorize(
            code=code,
            user_id=self._user_id,
            action=Action.ARM,
            require_code=self.runtime.code_arm_required,
        )
        self.runtime.arm(profile_id, confirmed=confirm, changed_by=actor)

    async def async_arm_profile(
        self, profile: str, confirm: bool = False, code: str | None = None
    ) -> None:
        """Dienst hauswacht.arm: Profil scharf schalten, optional mit Bestätigung."""
        await self._arm(profile, code, confirm=confirm)

    async def async_simulate_trigger(self, sensor: str) -> None:
        """Dienst hauswacht.simulate_trigger: Sensorauslösung simulieren (nur Testmodus)."""
        self.runtime.simulate_trigger(sensor)

    async def async_simulate_state(self, sensor: str, state: str) -> None:
        """Dienst hauswacht.simulate_state: Sensorzustand für Hauswacht vortäuschen (Testmodus)."""
        self.runtime.simulate_state(sensor, state)

    async def async_simulate_reset(self) -> None:
        """Dienst hauswacht.simulate_reset: alle Sensoren wieder mit echtem Zustand."""
        self.runtime.simulate_reset()

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        await self.runtime.async_disarm(code, self._user_id)

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        await self._arm_mode("home", code)

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        await self._arm_mode("night", code)

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        await self._arm_mode("away", code)

    async def async_alarm_arm_vacation(self, code: str | None = None) -> None:
        await self._arm_mode("vacation", code)

    async def async_alarm_arm_custom_bypass(self, code: str | None = None) -> None:
        await self._arm_mode("custom", code)


class HauswachtAllPanel(_SirenTestMixin, AlarmControlPanelEntity):
    """Bedienfeld "Alle Bereiche": schaltet jeden Bereich mit dem Profil seines Knopfs.

    Bereiche ohne Profil für den gedrückten Knopf bleiben, wie sie sind. Unscharf schaltet alle.
    Zustand: Alarm > Eingangsverzögerung > Ausgangsverzögerung > unscharf (alle) > gemeinsamer
    scharfer Zustand; teilweise oder unterschiedlich scharf zeigt "scharf (benutzerdefiniert)".
    """

    _attr_translation_key = "all_panel"
    _platform_domain = "alarm_control_panel"

    def __init__(self, entry: HauswachtConfigEntry) -> None:
        super().__init__(entry, ALL_PANEL_KEY)
        self._keep_object_id("hauswacht_alle", "hauswacht_all")
        features = AlarmControlPanelEntityFeature(0)
        for area in self.runtime.areas.values():
            for mode in used_panel_modes(area.options):
                features |= _FEATURE_BY_MODE[mode]
        self._attr_supported_features = features

    async def async_added_to_hass(self) -> None:
        for area in self.runtime.areas.values():
            self.async_on_remove(area.add_listener(self.async_write_ha_state))

    def _area_state(self, area: HauswachtRuntime) -> AlarmControlPanelState:
        ctx = area.ctx
        if ctx.state is AlarmState.ARMED and ctx.profile is not None:
            return AlarmControlPanelState(panel_state(area.options, ctx.profile.profile_id))
        return _STATE_MAP[ctx.state]

    @property
    def alarm_state(self) -> AlarmControlPanelState:
        states = [self._area_state(area) for area in self.runtime.areas.values()]
        for wanted in (
            AlarmControlPanelState.TRIGGERED,
            AlarmControlPanelState.PENDING,
            AlarmControlPanelState.ARMING,
        ):
            if wanted in states:
                return wanted
        if all(state is AlarmControlPanelState.DISARMED for state in states):
            return AlarmControlPanelState.DISARMED
        if len(set(states)) == 1:
            return states[0]
        return AlarmControlPanelState.ARMED_CUSTOM_BYPASS

    @property
    def code_format(self) -> CodeFormat | None:
        return CodeFormat.NUMBER if self.runtime.has_codes else None

    @property
    def code_arm_required(self) -> bool:
        return self.runtime.code_arm_required

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "areas": {
                area.area_name: {
                    "state": self._area_state(area).value,
                    "profile_name": area.profile_name(area.ctx.profile.profile_id)
                    if area.ctx.profile
                    else None,
                }
                for area in self.runtime.areas.values()
            },
            "test_mode": self.runtime.ctx.test_mode,
        }

    @property
    def changed_by(self) -> str | None:
        return self.runtime.changed_by

    @property
    def _user_id(self) -> str | None:
        return self._context.user_id if self._context else None

    @staticmethod
    def _reason(err: Exception) -> str:
        text = str(err)
        if text:
            return text
        return str(getattr(err, "translation_key", "") or type(err).__name__)

    def _raise_partial(self, failed: dict[str, str], done: list[str]) -> None:
        if not failed:
            return
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="areas_failed",
            translation_placeholders={
                "failed": "; ".join(f"{name}: {why}" for name, why in failed.items()),
                "done": ", ".join(done) or "-",
            },
        )

    async def _arm_mode(self, mode: str, code: str | None) -> None:
        targets = [
            (area, profile_id)
            for area in self.runtime.areas.values()
            if (profile_id := profile_for_mode(area.options, mode)) is not None
        ]
        if not targets:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="no_profile_for_mode",
                translation_placeholders={"mode": mode},
            )
        failed: dict[str, str] = {}
        done: list[str] = []
        for area, profile_id in targets:
            try:
                actor = await area.async_authorize(
                    code=code,
                    user_id=self._user_id,
                    action=Action.ARM,
                    require_code=area.code_arm_required,
                )
                area.arm(profile_id, changed_by=actor)
            except HomeAssistantError as err:
                failed[area.area_name] = self._reason(err)
            else:
                done.append(area.area_name)
        self._raise_partial(failed, done)

    async def async_arm_profile(
        self, profile: str, confirm: bool = False, code: str | None = None
    ) -> None:
        """Dienst hauswacht.arm am Bedienfeld "Alle": an den Bereich des Profils weitergeben."""
        for area in self.runtime.areas.values():
            if find_profile(area.options, profile) is not None:
                actor = await area.async_authorize(
                    code=code,
                    user_id=self._user_id,
                    action=Action.ARM,
                    require_code=area.code_arm_required,
                )
                area.arm(profile, confirmed=confirm, changed_by=actor)
                return
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="unknown_profile",
            translation_placeholders={"profile": profile},
        )

    async def async_simulate_trigger(self, sensor: str) -> None:
        self.runtime.simulate_trigger(sensor)

    async def async_simulate_state(self, sensor: str, state: str) -> None:
        self.runtime.simulate_state(sensor, state)

    async def async_simulate_reset(self) -> None:
        self.runtime.simulate_reset()

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        failed: dict[str, str] = {}
        done: list[str] = []
        for area in self.runtime.areas.values():
            if area.is_disarmed:
                continue
            try:
                await area.async_disarm(code, self._user_id)
            except HomeAssistantError as err:
                failed[area.area_name] = self._reason(err)
            else:
                done.append(area.area_name)
        self._raise_partial(failed, done)

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        await self._arm_mode("home", code)

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        await self._arm_mode("night", code)

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        await self._arm_mode("away", code)

    async def async_alarm_arm_vacation(self, code: str | None = None) -> None:
        await self._arm_mode("vacation", code)

    async def async_alarm_arm_custom_bypass(self, code: str | None = None) -> None:
        await self._arm_mode("custom", code)
