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
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
    async_get_current_platform,
)

from .const import DOMAIN
from .core.profiles import panel_state, profile_for_mode, profile_info, used_panel_modes
from .core.state_machine import AlarmState
from .core.users import Action
from .entity import HauswachtEntity
from .runtime import HauswachtConfigEntry

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
    async_add_entities([HauswachtAlarmPanel(entry)])
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


class HauswachtAlarmPanel(HauswachtEntity, AlarmControlPanelEntity):
    _attr_name = None  # Entität heißt wie das Gerät: "Hauswacht"
    _attr_translation_key = "panel"

    def __init__(self, entry: HauswachtConfigEntry) -> None:
        super().__init__(entry, "panel")
        # Nur Knöpfe anbieten, denen ein Profil zugeordnet ist. Optionen ändern lädt neu.
        features = AlarmControlPanelEntityFeature(0)
        for mode in used_panel_modes(entry.options):
            features |= _FEATURE_BY_MODE[mode]
        self._attr_supported_features = features

    @property
    def alarm_state(self) -> AlarmControlPanelState:
        ctx = self.runtime.ctx
        if ctx.state is AlarmState.ARMED and ctx.profile is not None:
            return AlarmControlPanelState(
                panel_state(self.runtime.entry.options, ctx.profile.profile_id)
            )
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
        profile_id = profile_for_mode(self.runtime.entry.options, mode)
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
