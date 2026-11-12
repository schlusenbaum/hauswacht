"""Zustand der Anlage als Text, wie ihn das Bedienfeld zeigt (z. B. für Keypads)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .profiles import panel_state
from .state_machine import AlarmContext, AlarmState

_STATE_VALUE = {
    AlarmState.DISARMED: "disarmed",
    AlarmState.ARMING: "arming",
    AlarmState.PENDING: "pending",
    AlarmState.TRIGGERED: "triggered",
    AlarmState.ALARM_HOLD: "triggered",
}


def panel_value(ctx: AlarmContext, options: Mapping[str, Any]) -> str:
    if ctx.state is AlarmState.ARMED and ctx.profile is not None:
        return str(panel_state(options, ctx.profile.profile_id))
    return _STATE_VALUE.get(ctx.state, "armed_away")
