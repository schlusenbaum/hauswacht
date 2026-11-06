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
from homeassistant.core import Event as HaEvent
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import (
    EventStateChangedData,
    async_call_later,
    async_track_state_change_event,
)
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
from .core.profiles import build_profiles, profile_behaviour, stale_after_seconds
from .core.sensors import (
    SensorSnapshot,
    all_configured_sensors,
    became_unavailable,
    evaluate_readiness,
    is_trigger,
    parse_role_overrides,
    parse_zones,
    resolve_zone,
    resolve_zones,
    sensor_role,
)
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
    SensorRole,
    SensorTriggered,
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

SENSOR_DOMAIN = "binary_sensor"


def entities_by_label(hass: HomeAssistant) -> dict[str, frozenset[str]]:
    """Label-ID -> binary_sensor-Entitäten mit diesem Label.

    Bewusst nur Labels direkt an der Entität (nicht am Gerät): Ein Geräte-Label würde sonst
    auch Batterie- oder Verbindungs-Sensoren desselben Geräts in die Zone ziehen.
    """
    index: dict[str, set[str]] = {}
    for entry in er.async_get(hass).entities.values():
        if entry.domain != SENSOR_DOMAIN or entry.disabled_by is not None:
            continue
        for label in entry.labels:
            index.setdefault(label, set()).add(entry.entity_id)
    return {label: frozenset(ids) for label, ids in index.items()}


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
        self.zones = parse_zones(entry.options)
        self.role_overrides = parse_role_overrides(entry.options)
        self.stale_after = stale_after_seconds(entry.options)
        self.delay_ends_at: datetime | None = None
        self.armed_sensors: frozenset[str] = frozenset()
        self.candidates: frozenset[str] = frozenset()
        self._labels: dict[str, frozenset[str]] = {}
        self._timer_cancel: CALLBACK_TYPE | None = None
        self._unsub_states: CALLBACK_TYPE | None = None
        self._unsub_registry: CALLBACK_TYPE | None = None
        self._subscribed: frozenset[str] = frozenset()
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
        self._refresh_sensors()
        self._unsub_registry = self.hass.bus.async_listen(
            er.EVENT_ENTITY_REGISTRY_UPDATED, self._on_registry_updated
        )

    @callback
    def async_stop(self) -> None:
        """Beim Entladen: Timer und Abos stoppen. Der gespeicherte Zustand bleibt erhalten."""
        self._cancel_timer()
        for unsub in (self._unsub_states, self._unsub_registry):
            if unsub is not None:
                unsub()
        self._unsub_states = self._unsub_registry = None
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
        sensors = self.profile_sensors(profile_id)
        if not sensors:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="profile_has_no_sensors",
                translation_placeholders={"profile": profile_id},
            )
        if self.ctx.state is AlarmState.DISARMED:
            self.armed_sensors = sensors
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

    # --- Sensoren ----------------------------------------------------------

    def profile_sensors(self, profile_id: str) -> frozenset[str]:
        zone_ids = profile_behaviour(self.entry.options, profile_id).zones
        return resolve_zones(zone_ids, self.zones, self._labels)

    def zone_members(self) -> dict[str, list[str]]:
        return {zone.name: sorted(resolve_zone(zone, self._labels)) for zone in self.zones.values()}

    def snapshots(self, entity_ids: frozenset[str]) -> dict[str, SensorSnapshot]:
        result: dict[str, SensorSnapshot] = {}
        for entity_id in entity_ids:
            state = self.hass.states.get(entity_id)
            result[entity_id] = SensorSnapshot(
                entity_id=entity_id,
                state=state.state if state else None,
                device_class=state.attributes.get("device_class") if state else None,
                last_reported=state.last_reported.timestamp() if state else None,
            )
        return result

    def readiness_for(self, entity_ids: frozenset[str]) -> Readiness:
        return evaluate_readiness(
            entity_ids,
            self.snapshots(entity_ids),
            now=dt_util.utcnow().timestamp(),
            stale_after=self.stale_after,
        )

    def _readiness(self) -> Readiness:
        return self.readiness_for(self.armed_sensors)

    @callback
    def _refresh_sensors(self) -> None:
        """Labels neu einlesen und Zustandsabos auf alle konfigurierten Sensoren setzen."""
        self._labels = entities_by_label(self.hass)
        self.candidates = all_configured_sensors(self.zones, self._labels)
        # Gerade scharf überwachte Sensoren bleiben abonniert, auch wenn ihr Label
        # inzwischen entfernt wurde – sonst würden sie unbemerkt nicht mehr überwacht.
        wanted = self.candidates | self.armed_sensors
        if wanted == self._subscribed and self._unsub_states is not None:
            return
        if self._unsub_states is not None:
            self._unsub_states()
            self._unsub_states = None
        self._subscribed = wanted
        if wanted:
            self._unsub_states = async_track_state_change_event(
                self.hass, sorted(wanted), self._on_sensor_state
            )
        self._notify()

    @callback
    def _on_registry_updated(self, _event: HaEvent[Any]) -> None:
        # Die Menge der GERADE überwachten Sensoren bleibt bis zum Unscharfschalten fest
        # (armed_sensors). Neu gelabelte Sensoren zählen ab der nächsten Scharfschaltung.
        self._refresh_sensors()

    @callback
    def _on_sensor_state(self, event: HaEvent[EventStateChangedData]) -> None:
        entity_id = event.data["entity_id"]
        old = event.data["old_state"]
        new = event.data["new_state"]
        old_state = old.state if old else None
        new_state = new.state if new else None
        device_class = new.attributes.get("device_class") if new else None
        role = sensor_role(entity_id, device_class, self.role_overrides)
        armed = self.ctx.state is not AlarmState.DISARMED

        relevant = role is SensorRole.TAMPER_24H or (armed and entity_id in self.armed_sensors)
        if relevant and is_trigger(old_state, new_state):
            self._dispatch(SensorTriggered(sensor_key=entity_id, role=role))
            return
        if armed and entity_id in self.armed_sensors and became_unavailable(old_state, new_state):
            self._on_sensor_lost(entity_id)
        self._notify()

    @callback
    def _on_sensor_lost(self, entity_id: str) -> None:
        _LOGGER.warning("Überwachter Sensor nicht mehr verfügbar: %s", entity_id)
        self.hass.bus.async_fire(
            EVENT_HAUSWACHT, {"type": "SensorUnavailable", "sensor_key": entity_id}
        )
        persistent_notification.async_create(
            self.hass,
            f"Der überwachte Sensor {entity_id} ist nicht mehr verfügbar. "
            "Hauswacht ist scharf, kann diesen Bereich aber nicht mehr überwachen.",
            title="Hauswacht: Sensor ausgefallen",
            notification_id=f"{NOTIFICATION_ALARM}_{entity_id}",
        )

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
        if self.ctx.state is AlarmState.DISARMED and self.armed_sensors:
            self.armed_sensors = frozenset()
            self._refresh_sensors()
        if (old_ctx.state, old_ctx.profile, old_ctx.test_mode) != (
            self.ctx.state,
            self.ctx.profile,
            self.ctx.test_mode,
        ):
            self._store.async_delay_save(self._storage_data, 0)
        self._notify()
        return effects

    @callback
    def _notify(self) -> None:
        for listener in list(self._listeners):
            listener()

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
