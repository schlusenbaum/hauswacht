"""Laufzeitschicht: verbindet die reine Zustandsmaschine mit Home Assistant.

Aufgaben:
- Ereignisse an die Zustandsmaschine geben (immer im Event-Loop, dadurch seriell).
- Effekte ausführen: Timer, Speicherung, HA-Ereignisse, Hinweise.
- Neustartverhalten: Anlage startet immer unscharf (ADR 0004).

In 0.2.0 werden Alarmreaktionen nur als Ereignis und Hinweis gemeldet.
Sirenen und Benachrichtigungen folgen mit 0.5.0 über den Siren Executor.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import fields
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    EVENT_HAUSWACHT,
    NOTIFICATION_ALARM,
    NOTIFICATION_RESTART,
    OPT_CODE_ARM_REQUIRED,
    OPT_PIN_DIGEST,
    OPT_PIN_SALT,
    STORAGE_VERSION,
)
from .core.pin import PinHash, verify_pin
from .core.profiles import build_profiles
from .core.state_machine import (
    ActivateReaction,
    AlarmContext,
    AlarmState,
    ArmingAborted,
    ArmRequested,
    CancelTimer,
    ConfirmationRequired,
    DisarmRequested,
    Effect,
    EntryDelayElapsed,
    Event,
    ExitDelayElapsed,
    ReactionTimeElapsed,
    Readiness,
    Rejected,
    RestartedDisarmed,
    SetTestMode,
    StartTimer,
    Startup,
    StateChanged,
    StopReaction,
    TimerKind,
    step,
)

_LOGGER = logging.getLogger(__name__)

type HauswachtConfigEntry = ConfigEntry[HauswachtRuntime]


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, frozenset | set):
        return sorted(_jsonable(v) for v in value)
    return value


def effect_payload(effect: Effect) -> dict[str, Any]:
    """Wandelt einen Effekt in Ereignisdaten für den HA-Event-Bus um."""
    payload: dict[str, Any] = {"type": type(effect).__name__}
    for field in fields(effect):
        payload[field.name] = _jsonable(getattr(effect, field.name))
    return payload


class HauswachtRuntime:
    """Hält den Zustand einer Hauswacht-Instanz und führt Effekte aus."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.ctx = AlarmContext()
        self.profiles = build_profiles(entry.options)
        self.delay_ends_at: datetime | None = None
        self._timer_cancel: CALLBACK_TYPE | None = None
        self._listeners: list[Callable[[], None]] = []
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}"
        )

    # --- Konfiguration -----------------------------------------------------

    @property
    def pin(self) -> PinHash | None:
        salt = self.entry.options.get(OPT_PIN_SALT)
        digest = self.entry.options.get(OPT_PIN_DIGEST)
        if not salt or not digest:
            return None
        return PinHash(salt=salt, digest=digest)

    @property
    def code_arm_required(self) -> bool:
        return self.pin is not None and bool(self.entry.options.get(OPT_CODE_ARM_REQUIRED, False))

    def check_code(self, code: str | None) -> bool:
        return verify_pin(code, self.pin)

    # --- Lebenszyklus ------------------------------------------------------

    async def async_start(self) -> None:
        data = await self._store.async_load() or {}
        previous = data.get("armed_profile")
        self._dispatch(
            Startup(
                previous_profile_id=previous if isinstance(previous, str) else None,
                test_mode=bool(data.get("test_mode", False)),
            )
        )
        # Sofort speichern, damit ein erneuter Absturz nicht doppelt meldet.
        await self._store.async_save(self._storage_data())

    @callback
    def async_stop(self) -> None:
        """Beim Entladen: Timer stoppen. Der gespeicherte Zustand bleibt erhalten."""
        self._cancel_timer()
        self._listeners.clear()

    @callback
    def add_listener(self, listener: Callable[[], None]) -> CALLBACK_TYPE:
        self._listeners.append(listener)

        @callback
        def remove() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return remove

    # --- Bedienung ---------------------------------------------------------

    @callback
    def arm(self, profile_id: str, *, confirmed: bool = False) -> None:
        profile = self.profiles.get(profile_id)
        if profile is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="unknown_profile",
                translation_placeholders={"profile": profile_id},
            )
        effects = self._dispatch(
            ArmRequested(profile=profile, readiness=self._readiness(), confirmed=confirmed)
        )
        self._raise_for_rejection(effects)

    @callback
    def disarm(self, code: str | None) -> None:
        if not self.check_code(code):
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="invalid_code")
        self._dispatch(DisarmRequested(code_valid=True))

    @callback
    def set_test_mode(self, enabled: bool) -> None:
        effects = self._dispatch(SetTestMode(enabled=enabled))
        self._raise_for_rejection(effects)

    # --- Interna -----------------------------------------------------------

    def _readiness(self) -> Readiness:
        # Sensorbewertung folgt mit 0.3.0.
        return Readiness()

    @staticmethod
    def _raise_for_rejection(effects: tuple[Effect, ...]) -> None:
        for effect in effects:
            if isinstance(effect, Rejected):
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key=f"rejected_{effect.reason}",
                    translation_placeholders={
                        "open": ", ".join(sorted(effect.open_sensors)) or "-",
                        "unavailable": ", ".join(sorted(effect.unavailable_sensors)) or "-",
                    },
                )
            if isinstance(effect, ConfirmationRequired):
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="confirmation_required",
                    translation_placeholders={
                        "open": ", ".join(sorted(effect.open_sensors)) or "-",
                        "unavailable": ", ".join(sorted(effect.unavailable_sensors)) or "-",
                    },
                )

    @callback
    def _dispatch(self, event: Event) -> tuple[Effect, ...]:
        old_ctx = self.ctx
        self.ctx, effects = step(self.ctx, event, time.monotonic())
        for effect in effects:
            self._apply(effect)
        if (old_ctx.state, old_ctx.profile, old_ctx.test_mode) != (
            self.ctx.state,
            self.ctx.profile,
            self.ctx.test_mode,
        ):
            self._store.async_delay_save(self._storage_data, 0)
        for listener in list(self._listeners):
            listener()
        return effects

    def _storage_data(self) -> dict[str, Any]:
        armed = self.ctx.state is not AlarmState.DISARMED and self.ctx.profile is not None
        return {
            "armed_profile": self.ctx.profile.profile_id if armed and self.ctx.profile else None,
            "test_mode": self.ctx.test_mode,
        }

    @callback
    def _apply(self, effect: Effect) -> None:
        self.hass.bus.async_fire(EVENT_HAUSWACHT, effect_payload(effect))

        match effect:
            case StartTimer():
                self._start_timer(effect)
            case CancelTimer():
                self._cancel_timer()
            case StateChanged():
                _LOGGER.info(
                    "Zustand %s -> %s (%s)", effect.old.value, effect.new.value, effect.cause
                )
            case ActivateReaction():
                self._on_alarm(effect)
            case StopReaction():
                _LOGGER.info("Alarmreaktion beendet (Profil %s)", effect.profile_id)
            case RestartedDisarmed():
                persistent_notification.async_create(
                    self.hass,
                    f"Home Assistant wurde neu gestartet. Hauswacht war vorher scharf "
                    f"(Profil: {effect.previous_profile_id}) und ist jetzt UNSCHARF.",
                    title="Hauswacht: nach Neustart unscharf",
                    notification_id=NOTIFICATION_RESTART,
                )
            case ArmingAborted():
                _LOGGER.warning(
                    "Scharfschaltung abgebrochen: offen=%s, nicht verfügbar=%s",
                    sorted(effect.open_sensors),
                    sorted(effect.unavailable_sensors),
                )
            case _:
                pass

    @callback
    def _on_alarm(self, effect: ActivateReaction) -> None:
        prefix = "TESTALARM" if effect.test_mode else "ALARM"
        _LOGGER.warning(
            "%s ausgelöst durch %s (Profil %s, Zyklus %s)",
            prefix,
            effect.sensor_key,
            effect.profile_id,
            effect.cycle,
        )
        persistent_notification.async_create(
            self.hass,
            f"{prefix}: ausgelöst durch {effect.sensor_key} (Profil {effect.profile_id}). "
            "Sirenen und Push-Benachrichtigungen sind in dieser Version noch nicht aktiv.",
            title=f"Hauswacht: {prefix}",
            notification_id=NOTIFICATION_ALARM,
        )

    @callback
    def _start_timer(self, effect: StartTimer) -> None:
        self._cancel_timer()
        self.delay_ends_at = dt_util.utcnow() + timedelta(seconds=effect.seconds)

        @callback
        def _elapsed(_now: datetime) -> None:
            self._timer_cancel = None
            self.delay_ends_at = None
            self._dispatch(self._timer_event(effect.kind, effect.token))

        self._timer_cancel = async_call_later(self.hass, effect.seconds, _elapsed)

    def _timer_event(self, kind: TimerKind, token: int) -> Event:
        if kind is TimerKind.EXIT_DELAY:
            return ExitDelayElapsed(token=token, readiness=self._readiness())
        if kind is TimerKind.ENTRY_DELAY:
            return EntryDelayElapsed(token=token)
        return ReactionTimeElapsed(token=token)

    @callback
    def _cancel_timer(self) -> None:
        if self._timer_cancel is not None:
            self._timer_cancel()
            self._timer_cancel = None
        self.delay_ends_at = None
