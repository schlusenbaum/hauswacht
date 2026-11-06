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
from .core.profiles import PANEL_STATE_BY_PROFILE, PROFILE_IDS
from .core.state_machine import AlarmState
from .entity import HauswachtEntity
from .runtime import HauswachtConfigEntry

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
            vol.Required("profile"): vol.In(PROFILE_IDS),
            vol.Optional("confirm", default=False): cv.boolean,
            vol.Optional("code"): cv.string,
        },
        "async_arm_profile",
    )


class HauswachtAlarmPanel(HauswachtEntity, AlarmControlPanelEntity):
    _attr_name = None  # Entität heißt wie das Gerät: "Hauswacht"
    _attr_translation_key = "panel"
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_HOME
        | AlarmControlPanelEntityFeature.ARM_NIGHT
        | AlarmControlPanelEntityFeature.ARM_AWAY
        | AlarmControlPanelEntityFeature.ARM_VACATION
    )

    def __init__(self, entry: HauswachtConfigEntry) -> None:
        super().__init__(entry, "panel")

    @property
    def alarm_state(self) -> AlarmControlPanelState:
        ctx = self.runtime.ctx
        if ctx.state is AlarmState.ARMED and ctx.profile is not None:
            return AlarmControlPanelState(PANEL_STATE_BY_PROFILE[ctx.profile.profile_id])
        return _STATE_MAP[ctx.state]

    @property
    def code_format(self) -> CodeFormat | None:
        return CodeFormat.NUMBER if self.runtime.pin is not None else None

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
            "phase": ctx.state.value,
            "test_mode": ctx.test_mode,
            "timer": ctx.timer_kind.value if ctx.timer_kind else None,
            "timer_ends_at": ends_at.isoformat() if ends_at else None,
            "trigger_sensor": ctx.trigger_sensor,
            "alarm_cycles": ctx.alarm_cycles,
            "bypassed_sensors": sorted(ctx.bypassed),
            "monitored_sensors": sorted(self.runtime.armed_sensors),
            "open_sensors": sorted(readiness.open_sensors),
            "unavailable_sensors": sorted(readiness.unavailable_sensors),
            "zones": self.runtime.zone_members(),
        }

    def _arm(self, profile_id: str, code: str | None, *, confirm: bool = False) -> None:
        if self.runtime.code_arm_required and not self.runtime.check_code(code):
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="invalid_code")
        self.runtime.arm(profile_id, confirmed=confirm)

    async def async_arm_profile(
        self, profile: str, confirm: bool = False, code: str | None = None
    ) -> None:
        """Dienst hauswacht.arm: Profil scharf schalten, optional mit Bestätigung."""
        self._arm(profile, code, confirm=confirm)

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        self.runtime.disarm(code)

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        self._arm("home", code)

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        self._arm("night", code)

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        self._arm("away", code)

    async def async_alarm_arm_vacation(self, code: str | None = None) -> None:
        self._arm("vacation", code)
