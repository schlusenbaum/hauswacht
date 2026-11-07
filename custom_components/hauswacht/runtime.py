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
import secrets
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
from homeassistant.core import Event as HaEventAny
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import (
    EventStateChangedData,
    async_call_later,
    async_track_state_change_event,
)
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .automation_runner import AutomationRunner
from .const import (
    DOMAIN,
    EVENT_HAUSWACHT,
    NOTIFICATION_ALARM,
    NOTIFICATION_FAULT,
    NOTIFICATION_RESTART,
    OPT_CODE_ARM_REQUIRED,
    OPT_END_ALARM_WITHOUT_PIN,
    OPT_INFRASTRUCTURE,
    OPT_PIN_DIGEST,
    OPT_PIN_SALT,
    OPT_PUSH_DISARM,
    PUSH_ACTION_EVENT,
    PUSH_ACTION_PREFIX,
    PUSH_TAG,
    STORAGE_VERSION,
)
from .core.code_guard import (
    CodeGuardState,
    register_failure,
    register_success,
    remaining_lock,
)
from .core.infrastructure import SystemReport, faulty_indicators, system_report
from .core.pin import PinHash, verify_pin
from .core.profiles import (
    build_profiles,
    find_profile,
    profile_behaviour,
    profile_info,
    stale_after_seconds,
)
from .core.reactions import (
    alarm_message,
    fault_message,
    invalid_code_message,
    parse_reaction,
    restart_message,
    sensor_lost_message,
    tamper_message,
)
from .core.sensors import (
    SensorSnapshot,
    all_configured_sensors,
    became_unavailable,
    evaluate_readiness,
    is_last_seen_entity,
    is_trigger,
    parse_role_overrides,
    parse_zones,
    resolve_zone,
    resolve_zones,
    sensor_role,
)
from .core.state_machine import (
    ActivateReaction,
    AlarmAcknowledged,
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
    SensorClosed,
    SensorRole,
    SensorsRestored,
    SensorTriggered,
    SetTestMode,
    StartTimer,
    Startup,
    StateChanged,
    StopReaction,
    TamperDetected,
    TimerKind,
    step,
)
from .homecoming_observer import HomecomingObserver
from .names import display_name
from .notifier import Notifier
from .siren_executor import SirenExecutor

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
        self.sirens = SirenExecutor(hass, entry.options)
        self._code_guard = CodeGuardState()
        self._selected_profile: str | None = None
        self.automation = AutomationRunner(self)
        self.notifier = Notifier(hass, entry.options)
        self.zones = parse_zones(entry.options)
        self.role_overrides = parse_role_overrides(entry.options)
        self.stale_after = stale_after_seconds(entry.options)
        self.infrastructure: frozenset[str] = frozenset(
            str(e) for e in entry.options.get(OPT_INFRASTRUCTURE, []) if isinstance(e, str)
        )
        self._infra_faulty: frozenset[str] = frozenset()
        self.delay_ends_at: datetime | None = None
        self.armed_sensors: frozenset[str] = frozenset()
        self.candidates: frozenset[str] = frozenset()
        self._labels: dict[str, frozenset[str]] = {}
        self._last_seen_entity: dict[str, str] = {}
        self._timer_cancel: CALLBACK_TYPE | None = None
        self._unsub_states: CALLBACK_TYPE | None = None
        self._unsub_registry: CALLBACK_TYPE | None = None
        self._subscribed: frozenset[str] = frozenset()
        self._listeners: list[Callable[[], None]] = []
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}"
        )
        # Push-Knopf "Unscharf schalten": gilt nur für die laufende Scharfschaltung
        self.push_disarm = bool(entry.options.get(OPT_PUSH_DISARM, False))
        self._session: str | None = None
        self._pushed_targets: set[str] = set()
        self._unsub_push: CALLBACK_TYPE | None = None
        self._acting_user: str | None = None  # wer gerade per Push-Knopf bedient
        self.homecoming = HomecomingObserver(
            hass, entry.entry_id, dict(entry.options), self.entry_doors, self._notify
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
    def end_alarm_needs_code(self) -> bool:
        """Braucht "Alarm beenden" einen PIN? Nur mit PIN und ohne die Ausnahme-Option."""
        return self.pin is not None and not bool(
            self.entry.options.get(OPT_END_ALARM_WITHOUT_PIN, False)
        )

    @property
    def code_arm_required(self) -> bool:
        return self.pin is not None and bool(self.entry.options.get(OPT_CODE_ARM_REQUIRED, False))

    def check_code(self, code: str | None) -> bool:
        return verify_pin(code, self.pin)

    # --- Lebenszyklus ------------------------------------------------------

    # --- Profile ----------------------------------------------------------

    def profile_name(self, profile_id: str | None) -> str:
        if profile_id is None:
            return "-"
        return profile_info(self.entry.options, profile_id).name

    @property
    def selected_profile(self) -> str | None:
        """Profil der Auswahlliste: das aktive Profil, sonst die Auswahl, sonst das erste."""
        if self.ctx.profile is not None:
            return self.ctx.profile.profile_id
        if self._selected_profile in self.profiles:
            return self._selected_profile
        return next(iter(self.profiles), None)

    @callback
    def select_profile(self, profile_ref: str) -> None:
        if self.ctx.state is not AlarmState.DISARMED:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="select_requires_disarmed"
            )
        profile_id = find_profile(self.entry.options, profile_ref)
        if profile_id is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="unknown_profile",
                translation_placeholders={"profile": profile_ref},
            )
        self._selected_profile = profile_id
        self._store.async_delay_save(self._storage_data, 0)
        self._notify()

    @callback
    def arm_selected(self, *, confirmed: bool = False) -> None:
        profile_id = self.selected_profile
        if profile_id is None:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="no_profiles")
        self.arm(profile_id, confirmed=confirmed)

    async def async_start(self) -> None:
        data = await self._store.async_load() or {}
        selected = data.get("selected_profile")
        self._selected_profile = selected if isinstance(selected, str) else None
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
        self._infra_faulty = self.faulty_infrastructure()
        self.automation.start()
        self._unsub_registry = self.hass.bus.async_listen(
            er.EVENT_ENTITY_REGISTRY_UPDATED, self._on_registry_updated
        )
        if self.push_disarm:
            self._unsub_push = self.hass.bus.async_listen(PUSH_ACTION_EVENT, self._on_push_action)
        await self.homecoming.async_start()

    @callback
    def async_stop(self) -> None:
        """Beim Entladen: Timer und Abos stoppen. Der gespeicherte Zustand bleibt erhalten."""
        self._cancel_timer()
        self.automation.stop()
        self.sirens.cancel_retry()
        self.homecoming.async_stop()
        if self._unsub_push is not None:
            self._unsub_push()
            self._unsub_push = None
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
    def arm(self, profile_ref: str, *, confirmed: bool = False) -> None:
        """Schaltet ein Profil scharf (Profil-ID oder Name)."""
        profile_id = find_profile(self.entry.options, profile_ref)
        profile = self.profiles.get(profile_id) if profile_id else None
        if profile_id is None or profile is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="unknown_profile",
                translation_placeholders={"profile": profile_ref},
            )
        sensors = self.profile_sensors(profile_id)
        if not sensors:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="profile_has_no_sensors",
                translation_placeholders={"profile": self.profile_name(profile_id)},
            )
        if self.ctx.state is AlarmState.DISARMED:
            self.armed_sensors = sensors
        effects = self._dispatch(
            ArmRequested(profile=profile, readiness=self._readiness(), confirmed=confirmed)
        )
        self._raise_for_rejection(effects)

    @callback
    def verify_code(self, code: str | None) -> None:
        """Prüft den PIN mit Schutz gegen Durchprobieren. Wirft bei Fehler oder Sperre."""
        if self.pin is None:
            return
        now = time.monotonic()
        locked = remaining_lock(self._code_guard, now)
        if locked:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="code_locked",
                translation_placeholders={"seconds": str(locked)},
            )
        if self.check_code(code):
            self._code_guard = register_success(self._code_guard)
            return
        result = register_failure(self._code_guard, now)
        self._code_guard = result.state
        failures = result.state.failures
        self.hass.bus.async_fire(
            EVENT_HAUSWACHT,
            {"type": "InvalidCode", "failures": failures, "lock_seconds": result.lock_seconds},
        )
        if result.warn:
            self.notifier.send_system(*invalid_code_message(failures, result.lock_seconds))
        if result.lock_seconds:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="code_locked",
                translation_placeholders={"seconds": str(result.lock_seconds)},
            )
        raise ServiceValidationError(translation_domain=DOMAIN, translation_key="invalid_code")

    @callback
    def disarm(self, code: str | None) -> None:
        """Unscharf schalten; während eines Alarms nur den Alarm beenden (bleibt scharf)."""
        self.verify_code(code)
        self._dispatch(self._disarm_request())

    @callback
    def disarm_trusted(self) -> None:
        """Wie ``disarm`` ohne PIN – nur für eigene Automatik und den Push-Knopf."""
        self._dispatch(self._disarm_request())

    @callback
    def disarm_now(self) -> None:
        """Sofort unscharf, auch während eines Alarms (erst Alarm beenden, dann unscharf)."""
        if self.ctx.state in (AlarmState.TRIGGERED, AlarmState.ALARM_HOLD):
            self._dispatch(self._disarm_request())
        self._dispatch(DisarmRequested(code_valid=True))

    @callback
    def end_alarm(self) -> None:
        """Nur den Alarm beenden; außerhalb eines Alarms passiert nichts."""
        if self.ctx.state in (AlarmState.TRIGGERED, AlarmState.ALARM_HOLD):
            self._dispatch(self._disarm_request())

    def _disarm_request(self) -> DisarmRequested:
        open_now = (
            self._readiness().open_sensors
            if self.ctx.state in (AlarmState.TRIGGERED, AlarmState.ALARM_HOLD)
            else frozenset()
        )
        return DisarmRequested(code_valid=True, open_sensors=open_now)

    # --- Push-Knopf "Unscharf schalten" --------------------------------------

    def entry_doors(self) -> frozenset[str]:
        """Alle konfigurierten Sensoren mit der Rolle "Eingang" (für die Heimkehr-Beobachtung)."""
        doors: set[str] = set()
        for entity_id in self.candidates:
            state = self.hass.states.get(entity_id)
            device_class = state.attributes.get("device_class") if state else None
            if sensor_role(entity_id, device_class, self.role_overrides) is SensorRole.ENTRY:
                doors.add(entity_id)
        return frozenset(doors)

    def _push_actions(self, title: str = "Unscharf schalten") -> dict[str, Any]:
        if not self.push_disarm or self._session is None:
            return {"tag": PUSH_TAG}
        return {
            "tag": PUSH_TAG,
            "actions": [
                {
                    "action": f"{PUSH_ACTION_PREFIX}{self._session}",
                    "title": title,
                    # iOS: nur mit entsperrtem Gerät (Face ID / Code)
                    "authenticationRequired": True,
                }
            ],
        }

    def _alarm_targets(self) -> tuple[str, ...]:
        if self.ctx.profile is None:
            return ()
        return parse_reaction(self.entry.options, self.ctx.profile.profile_id).notify

    @callback
    def _send_alarm_push(self, title: str, message: str) -> None:
        targets = self._alarm_targets()
        sent = self.notifier.send(
            targets, title, message, test_mode=self.ctx.test_mode, data=self._push_actions()
        )
        self._pushed_targets.update(sent)

    @callback
    def _on_entry_delay(self) -> None:
        if not self.push_disarm or self.ctx.profile is None:
            return
        sensor = self.ctx.trigger_sensor or ""
        self._send_alarm_push(
            "Hauswacht: Tür geöffnet",
            f"{display_name(self.hass, sensor)} – Eingangsverzögerung "
            f"{self.ctx.profile.entry_delay} s läuft "
            f"(Profil {self.profile_name(self.ctx.profile.profile_id)}).",
        )

    async def _on_push_action(self, event: HaEventAny[Any]) -> None:
        action = event.data.get("action")
        if not isinstance(action, str) or not action.startswith(PUSH_ACTION_PREFIX):
            return
        if self._session is None or action != f"{PUSH_ACTION_PREFIX}{self._session}":
            _LOGGER.warning(
                "Veralteter Push-Knopf ignoriert (gehört zu einer früheren Scharfschaltung)"
            )
            return
        user_id = event.context.user_id
        user = await self.hass.auth.async_get_user(user_id) if user_id else None
        if user is None or not user.is_active or user.system_generated:
            _LOGGER.warning("Push-Knopf ohne gültigen Home-Assistant-Benutzer ignoriert")
            return
        if self.ctx.state is AlarmState.DISARMED:
            return
        targets = self._alarm_targets()
        test_mode = self.ctx.test_mode
        _LOGGER.warning("Push-Knopf durch %s (Zustand %s)", user.name, self.ctx.state.value)
        self._acting_user = user.name
        try:
            self.disarm_trusted()
        finally:
            self._acting_user = None
        if self.ctx.state is AlarmState.DISARMED:
            self.notifier.send(
                targets,
                "Hauswacht: unscharf",
                f"Unscharf geschaltet über den Push-Knopf von {user.name}.",
                test_mode=test_mode,
            )

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
                last_seen=self._last_seen(entity_id),
            )
        return result

    def _last_seen(self, entity_id: str) -> float | None:
        """Gerätseitiger "Zuletzt gesehen"-Zeitpunkt, falls das Gerät einen solchen Sensor hat."""
        companion = self._last_seen_entity.get(entity_id)
        state = self.hass.states.get(companion) if companion else None
        if state is None:
            return None
        parsed = dt_util.parse_datetime(state.state)
        return parsed.timestamp() if parsed is not None else None

    def last_contacts(self) -> dict[str, str | None]:
        """Letzter Kontakt je konfiguriertem Sensor (für Anzeige und Auswertung)."""
        contacts: dict[str, str | None] = {}
        for entity_id, snapshot in self.snapshots(self.candidates).items():
            contact = snapshot.last_contact
            contacts[entity_id] = (
                dt_util.utc_from_timestamp(contact).isoformat() if contact is not None else None
            )
        return dict(sorted(contacts.items()))

    @callback
    def _find_last_seen_entities(self, entity_ids: frozenset[str]) -> dict[str, str]:
        registry = er.async_get(self.hass)
        found: dict[str, str] = {}
        for entity_id in entity_ids:
            entry = registry.async_get(entity_id)
            if entry is None or entry.device_id is None:
                continue
            for sibling in er.async_entries_for_device(registry, entry.device_id):
                if is_last_seen_entity(
                    entity_id=sibling.entity_id,
                    unique_id=sibling.unique_id,
                    device_class=sibling.device_class or sibling.original_device_class,
                    original_name=sibling.original_name,
                    translation_key=sibling.translation_key,
                ):
                    found[entity_id] = sibling.entity_id
                    break
        return found

    def readiness_for(self, entity_ids: frozenset[str]) -> Readiness:
        """Bereitschaft der Sensoren. Gestörte Infrastruktur zählt als "nicht verfügbar"."""
        readiness = evaluate_readiness(
            entity_ids,
            self.snapshots(entity_ids),
            now=dt_util.utcnow().timestamp(),
            stale_after=self.stale_after,
        )
        faulty = self.faulty_infrastructure()
        if not faulty:
            return readiness
        return Readiness(
            open_sensors=readiness.open_sensors,
            unavailable_sensors=readiness.unavailable_sensors | faulty,
        )

    # --- Infrastruktur und Systemstatus -------------------------------------

    def _infrastructure_classes(self) -> dict[str, str | None]:
        classes: dict[str, str | None] = {}
        for entity_id in self.infrastructure:
            state = self.hass.states.get(entity_id)
            classes[entity_id] = state.attributes.get("device_class") if state else None
        return classes

    def _infrastructure_states(self) -> dict[str, str | None]:
        states: dict[str, str | None] = {}
        for entity_id in self.infrastructure:
            state = self.hass.states.get(entity_id)
            states[entity_id] = state.state if state else None
        return states

    def faulty_infrastructure(self) -> frozenset[str]:
        return faulty_indicators(self._infrastructure_states(), self._infrastructure_classes())

    def system_report(self) -> SystemReport:
        sensors = evaluate_readiness(
            self.candidates,
            self.snapshots(self.candidates),
            now=dt_util.utcnow().timestamp(),
            stale_after=self.stale_after,
        )
        return system_report(
            self._infrastructure_states(),
            sensors.unavailable_sensors,
            self._infrastructure_classes(),
        )

    @callback
    def _check_infrastructure(self) -> None:
        faulty = self.faulty_infrastructure()
        if faulty == self._infra_faulty:
            return
        new_faults = faulty - self._infra_faulty
        recovered = self._infra_faulty - faulty
        self._infra_faulty = faulty
        armed = self.ctx.state is not AlarmState.DISARMED
        for entity_id in sorted(new_faults):
            _LOGGER.warning("Infrastruktur gestört: %s", entity_id)
            self.hass.bus.async_fire(
                EVENT_HAUSWACHT,
                {"type": "InfrastructureFault", "indicator": entity_id, "armed": armed},
            )
        for entity_id in sorted(recovered):
            _LOGGER.info("Infrastruktur wieder verfügbar: %s", entity_id)
            self.hass.bus.async_fire(
                EVENT_HAUSWACHT,
                {"type": "InfrastructureRecovered", "indicator": entity_id, "armed": armed},
            )
        if faulty and armed and new_faults:
            self.notifier.send_system(*fault_message(faulty), test_mode=self.ctx.test_mode)
            persistent_notification.async_create(
                self.hass,
                "Hauswacht ist scharf, aber folgende Systeme sind gestört: "
                f"{', '.join(sorted(faulty))}. Sensoren dahinter können nicht melden.",
                title="Hauswacht: Störung",
                notification_id=NOTIFICATION_FAULT,
            )
        elif not faulty:
            persistent_notification.async_dismiss(self.hass, NOTIFICATION_FAULT)

    # --- Simulation (nur Testmodus) -----------------------------------------

    @callback
    def simulate_trigger(self, entity_id: str) -> None:
        """Simuliert das Auslösen eines konfigurierten Sensors. Nur im Testmodus erlaubt."""
        if not self.ctx.test_mode:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="simulation_requires_test_mode"
            )
        if entity_id not in self.candidates and entity_id not in self.armed_sensors:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="unknown_sensor",
                translation_placeholders={"sensor": entity_id},
            )
        state = self.hass.states.get(entity_id)
        device_class = state.attributes.get("device_class") if state else None
        role = sensor_role(entity_id, device_class, self.role_overrides)
        self.hass.bus.async_fire(
            EVENT_HAUSWACHT, {"type": "SensorSimulated", "sensor_key": entity_id}
        )
        armed = self.ctx.state is not AlarmState.DISARMED
        if role is SensorRole.TAMPER_24H or (armed and entity_id in self.armed_sensors):
            self._dispatch(SensorTriggered(sensor_key=entity_id, role=role))

    def _readiness(self) -> Readiness:
        return self.readiness_for(self.armed_sensors)

    @callback
    def _refresh_sensors(self) -> None:
        """Labels neu einlesen und Zustandsabos auf alle konfigurierten Sensoren setzen."""
        self._labels = entities_by_label(self.hass)
        self.candidates = all_configured_sensors(self.zones, self._labels)
        self._last_seen_entity = self._find_last_seen_entities(self.candidates | self.armed_sensors)
        # Gerade scharf überwachte Sensoren bleiben abonniert, auch wenn ihr Label
        # inzwischen entfernt wurde – sonst würden sie unbemerkt nicht mehr überwacht.
        # Die "Zuletzt gesehen"-Sensoren werden mit abonniert, damit die Anzeige aktuell bleibt.
        wanted = (
            self.candidates
            | self.armed_sensors
            | self.infrastructure
            | frozenset(self._last_seen_entity.values())
        )
        self.homecoming.refresh()
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
        if entity_id in self.infrastructure:
            self._check_infrastructure()
        if entity_id not in self.candidates and entity_id not in self.armed_sensors:
            self._notify()  # Infrastruktur oder "Zuletzt gesehen"-Sensor
            return
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
        if entity_id in self.ctx.bypassed_until_closed and new_state == "off":
            self._dispatch(SensorClosed(sensor_key=entity_id))
            return
        self._notify()

    @callback
    def _on_sensor_lost(self, entity_id: str) -> None:
        _LOGGER.warning("Überwachter Sensor nicht mehr verfügbar: %s", entity_id)
        self.hass.bus.async_fire(
            EVENT_HAUSWACHT, {"type": "SensorUnavailable", "sensor_key": entity_id}
        )
        self.notifier.send_system(*sensor_lost_message(entity_id), test_mode=self.ctx.test_mode)
        persistent_notification.async_create(
            self.hass,
            f"Der überwachte Sensor {entity_id} ist nicht mehr verfügbar. "
            "Hauswacht ist scharf, kann diesen Bereich aber nicht mehr überwachen.",
            title="Hauswacht: Sensor ausgefallen",
            notification_id=f"{NOTIFICATION_ALARM}_{entity_id}",
        )

    def _rejection_placeholders(
        self, open_sensors: frozenset[str], unavailable: frozenset[str]
    ) -> dict[str, str]:
        """Klartext für Meldungen: Namen mit Raum, gestörte Infrastruktur getrennt."""
        faulty = unavailable & self.infrastructure

        def names(ids: frozenset[str]) -> str:
            return ", ".join(sorted(display_name(self.hass, e) for e in ids)) or "-"

        return {
            "open": names(open_sensors),
            "unavailable": names(unavailable - faulty),
            "faulty": names(faulty),
        }

    def _raise_for_rejection(self, effects: tuple[Effect, ...]) -> None:
        for effect in effects:
            if isinstance(effect, Rejected):
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key=f"rejected_{effect.reason}",
                    translation_placeholders=self._rejection_placeholders(
                        effect.open_sensors, effect.unavailable_sensors
                    ),
                )
            if isinstance(effect, ConfirmationRequired):
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="confirmation_required",
                    translation_placeholders=self._rejection_placeholders(
                        effect.open_sensors, effect.unavailable_sensors
                    ),
                )

    @callback
    def _dispatch(self, event: Event) -> tuple[Effect, ...]:
        old_ctx = self.ctx
        self.ctx, effects = step(self.ctx, event, time.monotonic())
        for effect in effects:
            self._apply(effect)
        if self.ctx.state is AlarmState.DISARMED:
            self.sirens.reset()
            self.automation.on_disarmed()
            if self.armed_sensors:
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
            "selected_profile": self._selected_profile,
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
                if effect.old is AlarmState.DISARMED:
                    self._session = secrets.token_hex(8)
                if effect.new is AlarmState.PENDING:
                    self._on_entry_delay()
                if effect.new is AlarmState.DISARMED:
                    self._session = None
                    if self._pushed_targets:
                        self.notifier.clear(self._pushed_targets, PUSH_TAG)
                        self._pushed_targets.clear()
            case ActivateReaction():
                self._on_alarm(effect)
            case StopReaction():
                _LOGGER.info("Alarmreaktion beendet (Profil %s)", effect.profile_id)
                self.sirens.stop(test_mode=effect.test_mode)
            case TamperDetected():
                self.notifier.send_system(
                    *tamper_message(effect.sensor_key), test_mode=self.ctx.test_mode
                )
            case RestartedDisarmed():
                self.notifier.send_system(
                    *restart_message(self.profile_name(effect.previous_profile_id))
                )
                persistent_notification.async_create(
                    self.hass,
                    f"Home Assistant wurde neu gestartet. Hauswacht war vorher scharf "
                    f"(Profil: {self.profile_name(effect.previous_profile_id)}) "
                    "und ist jetzt UNSCHARF.",
                    title="Hauswacht: nach Neustart unscharf",
                    notification_id=NOTIFICATION_RESTART,
                )
            case AlarmAcknowledged():
                self._on_acknowledged(effect)
            case SensorsRestored():
                _LOGGER.info("Wieder überwacht: %s", sorted(effect.sensors))
            case ArmingAborted():
                _LOGGER.warning(
                    "Scharfschaltung abgebrochen: offen=%s, nicht verfügbar=%s",
                    sorted(effect.open_sensors),
                    sorted(effect.unavailable_sensors),
                )
            case _:
                pass

    @callback
    def _on_acknowledged(self, effect: AlarmAcknowledged) -> None:
        name = self.profile_name(effect.profile_id)
        by = f" von {self._acting_user}" if self._acting_user else ""
        message = f"Alarm beendet{by}. Profil {name} bleibt scharf."
        if effect.bypassed_until_closed:
            names = ", ".join(
                display_name(self.hass, s) for s in sorted(effect.bypassed_until_closed)
            )
            message += f" Bis zum Schließen nicht überwacht: {names}."
        _LOGGER.warning(message)
        targets = parse_reaction(self.entry.options, effect.profile_id).notify
        if self._pushed_targets:
            self.notifier.clear(self._pushed_targets, PUSH_TAG)
            self._pushed_targets.clear()
        self.notifier.send(
            targets, "Hauswacht: Alarm beendet", message, test_mode=self.ctx.test_mode
        )
        persistent_notification.async_dismiss(self.hass, NOTIFICATION_ALARM)

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
        reaction = parse_reaction(self.entry.options, effect.profile_id)
        profile = self.profiles[effect.profile_id]
        decision = self.sirens.activate(
            reaction.siren_targets,
            reaction.tone,
            reaction.volume,
            profile.reaction_time,
            test_mode=effect.test_mode,
        )
        title, message = alarm_message(
            self.profile_name(effect.profile_id),
            display_name(self.hass, effect.sensor_key),
            test_mode=effect.test_mode,
        )
        if decision.commands:
            message += " Sirenen: " + ", ".join(c.entity_id for c in decision.commands) + "."
        if decision.blocked:
            reasons = sorted({b.reason.value for b in decision.blocked})
            message += " Gesperrte Sirenen (" + ", ".join(reasons) + ")."
        if reaction.silent:
            message += " Stiller Alarm."
        sent = self.notifier.send(
            reaction.notify,
            title,
            message,
            test_mode=effect.test_mode,
            data=self._push_actions("Alarm beenden"),
        )
        self._pushed_targets.update(sent)
        persistent_notification.async_create(
            self.hass, message, title=title, notification_id=NOTIFICATION_ALARM
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
