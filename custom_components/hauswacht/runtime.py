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
from collections.abc import Callable, Mapping
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
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.event import (
    EventStateChangedData,
    async_call_later,
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .automation_runner import AutomationRunner
from .const import (
    DOMAIN,
    EVENT_HAUSWACHT,
    ISSUE_PIN_COVERAGE,
    MASTER_USER_ID,
    NOTIFICATION_ALARM,
    NOTIFICATION_ARM_HINT,
    NOTIFICATION_FAULT,
    NOTIFICATION_RESTART,
    OPT_BUTTONS_WITHOUT_PIN,
    OPT_CARD_PIN_UNLINKED,
    OPT_CODE_ARM_REQUIRED,
    OPT_DURESS_NOTIFY,
    OPT_END_ALARM_WITHOUT_PIN,
    OPT_INFRASTRUCTURE,
    OPT_PUSH_DISARM,
    PUSH_ACTION_EVENT,
    PUSH_ACTION_PREFIX,
    PUSH_ARM_FORCE_PREFIX,
    PUSH_ARM_NOW_PREFIX,
    PUSH_ARM_RETRY_PREFIX,
    PUSH_ARM_TAG,
    PUSH_TAG,
    STORAGE_VERSION,
)
from .controls import ControlManager
from .core.always_active import (
    ALWAYS_PROFILE_ID,
    ALWAYS_PROFILE_NAME,
    always_reaction_options,
    always_runtime,
    parse_always_active,
    parse_arm_on_close,
)
from .core.areas import MAIN_AREA, area_options, parse_areas
from .core.code_guard import (
    CodeGuardState,
    current_failures,
    register_failure,
    register_success,
    remaining_lock,
)
from .core.conditions import all_met as conditions_met
from .core.confirmation import FREQUENT_COUNT, LoneTriggerCounter
from .core.controls import looks_like_card
from .core.infrastructure import SystemReport, faulty_indicators, system_report
from .core.notify_events import NotifyEvent
from .core.profile_settings import SettingError
from .core.profile_settings import write as write_setting
from .core.profiles import (
    build_profiles,
    find_profile,
    profile_behaviour,
    profile_info,
    profile_infos,
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
from .core.rules import (
    STRICTNESS,
    Progress,
    Rule,
    RuleEngine,
    RuleResult,
    build_engine,
    describe_rule,
    parse_rules,
    profile_rule_ids,
)
from .core.sensor_types import (
    MONITORED_DOMAINS,
    SensorType,
    domain_of,
    excluded_sensors,
    normalize,
    parse_types,
    role_overrides,
    sensor_type,
)
from .core.sensors import (
    SensorSnapshot,
    all_configured_sensors,
    became_unavailable,
    evaluate_readiness,
    is_last_seen_entity,
    is_trigger,
    parse_zones,
    resolve_zone,
    resolve_zones,
    sensor_role,
)
from .core.speech import parse_speech, profile_speakers
from .core.state_machine import (
    ActivateReaction,
    AlarmAcknowledged,
    AlarmContext,
    AlarmState,
    AlwaysActiveTriggered,
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
from .core.texts import by as by_text
from .core.texts import lang_of, quoted, tr
from .core.users import (
    Action,
    Identity,
    User,
    allowed_in,
    find_by_ha_user,
    has_codes,
    match_pin,
    match_tag,
    parse_users,
    people_without_pin,
)
from .core.users import label as users_label
from .homecoming_observer import HomecomingObserver
from .names import display_name
from .notifier import Notifier
from .reminder import ReminderRunner
from .review import IssueReporter
from .silence_observer import SilenceObserver
from .siren_executor import SirenExecutor
from .siren_test import SirenTester

_LOGGER = logging.getLogger(__name__)

SIMULATION_REAL = "real"
SIMULATION_VALUES = frozenset({"on", "off", "unavailable", SIMULATION_REAL})

# So lange gelten Push-Knöpfe zum Scharfschalten ("Trotzdem scharf", "Jetzt scharf")
PENDING_ARM_SECONDS = 15 * 60
REMINDER_ARM_SECONDS = 2 * 60 * 60  # Erinnerung wird oft erst später gelesen

type HauswachtConfigEntry = ConfigEntry[HauswachtRuntime]

SENSOR_DOMAIN = "binary_sensor"


def device_class_of(hass: HomeAssistant, entity_id: str) -> str | None:
    """Geräteklasse aus dem Zustand, sonst aus dem Entitätsregister (auch vor dem Start)."""
    if (state := hass.states.get(entity_id)) is not None and (
        dc := state.attributes.get("device_class")
    ):
        return str(dc)
    entry = er.async_get(hass).async_get(entity_id)
    if entry is None:
        return None
    return entry.device_class or entry.original_device_class


def entities_by_label(hass: HomeAssistant) -> dict[str, frozenset[str]]:
    """Label-ID -> binary_sensor-Entitäten mit diesem Label.

    Bewusst nur Labels direkt an der Entität (nicht am Gerät): Ein Geräte-Label würde sonst
    auch Batterie- oder Verbindungs-Sensoren desselben Geräts in die Zone ziehen.
    """
    index: dict[str, set[str]] = {}
    for entry in er.async_get(hass).entities.values():
        if entry.domain not in MONITORED_DOMAINS or entry.disabled_by is not None:
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

    def __init__(  # noqa: PLR0915
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        area_id: str = MAIN_AREA,
        main: HauswachtRuntime | None = None,
    ) -> None:
        self.hass = hass
        self.entry = entry
        # Bereiche: jeder Bereich hat eine eigene Runtime; der Hauptbereich hält die übrigen
        self.area_id = area_id
        self.main: HauswachtRuntime = main or self
        self.areas: dict[str, HauswachtRuntime] = {area_id: self} if main is None else {}
        # Geräte-ID des Hauswacht-Geräts (vom Setup gesetzt; Bereichsgeräte hängen darunter)
        self.device_id: str | None = None
        self.options: dict[str, Any] = area_options(entry.options, area_id)
        self.ctx = AlarmContext()
        self.profiles = build_profiles(self.options)
        # Sirenen-Belegung über alle Bereiche: Sirene -> Bereiche, die sie gerade nutzen
        self.siren_owners: dict[str, set[str]] = self.main.siren_owners if main else {}
        self.sirens = SirenExecutor(hass, entry.options, owner=area_id, owners=self.siren_owners)
        # Sirenentest: nur im Hauptbereich (gilt für alle Bereiche)
        self.siren_tester: SirenTester | None = SirenTester(hass, self) if main is None else None
        # Bedienteile (Keypads, NFC, RFID): nur im Hauptbereich, bedienen je nach Einstellung
        self.controls: ControlManager | None = ControlManager(hass, self) if main is None else None
        # Funkstille-Beobachtung: ebenfalls nur im Hauptbereich (beobachtet alle Bereiche)
        self.silence: SilenceObserver | None = SilenceObserver(hass, self) if main is None else None
        self.reviewer: IssueReporter | None = IssueReporter(hass, self) if main is None else None
        self._code_guard = CodeGuardState()
        self._selected_profile: str | None = None
        self._edit_profile: str | None = None
        self.automation = AutomationRunner(self)
        areas = parse_areas(entry.options)
        self.notifier = Notifier(
            hass, entry.options, label=areas[area_id].name if len(areas) > 1 else None
        )
        self.reminder = ReminderRunner(self)
        self.zones = parse_zones(entry.options)
        self.sensor_types = parse_types(entry.options)
        self.role_overrides = role_overrides(self.sensor_types)
        self.stale_after = stale_after_seconds(entry.options)
        # Funknetz/Gateways überwacht nur der Hauptbereich (sonst doppelte Meldungen)
        self.infrastructure: frozenset[str] = frozenset(
            str(e)
            for e in entry.options.get(OPT_INFRASTRUCTURE, [])
            if isinstance(e, str) and main is None
        )
        self._infra_faulty: frozenset[str] = frozenset()
        # Simulierte Sensorzustände (nur Testmodus, nur für Hauswacht, nie in Home Assistant)
        self._simulated: dict[str, str] = self.main._simulated if main else {}
        # Regeln ("Tür, dann Keller"): Sammlung, Auswertung für das scharfe Profil
        self.rules: dict[str, Rule] = parse_rules(self.options)
        self._engine = RuleEngine()
        self._partials: dict[str, Progress] = {}
        self._partial_timer: CALLBACK_TYPE | None = None
        self._fired_rule: str | None = None
        self._lone = LoneTriggerCounter()
        # Allein auslösende Melder des scharfen Profils (Teilmenge von armed_sensors)
        self.single_sensors: frozenset[str] = frozenset()
        # Immer aktive Melder (auch unscharf)
        self.always = parse_always_active(self.options)
        self.always_sensors: frozenset[str] = frozenset()
        self.technical_sensors: frozenset[str] = frozenset()
        # Scharf durch Schließen der Tür (für die laufende Scharfschaltung)
        self._exit_doors: frozenset[str] = frozenset()
        self._exit_settle = 5
        self._settle_timer: CALLBACK_TYPE | None = None
        self._speech_repeat: CALLBACK_TYPE | None = None
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
        store_key = f"{DOMAIN}.{entry.entry_id}"
        if area_id != MAIN_AREA:
            store_key += f".{area_id}"
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, store_key)
        # Push-Knopf "Unscharf schalten": gilt nur für die laufende Scharfschaltung
        self.push_disarm = bool(entry.options.get(OPT_PUSH_DISARM, False))
        self._session: str | None = None
        self._pushed_targets: set[str] = set()
        self._unsub_push: CALLBACK_TYPE | None = None
        # Wer zuletzt bedient hat (Benutzer, gemeinsamer PIN, HA-Konto oder "Automatik")
        self.changed_by: str | None = None
        # Push-Knöpfe zum Scharfschalten: Kennung -> (Profil, gültig bis)
        self._pending_arms: dict[str, tuple[str, float]] = {}
        self._arm_pushed: set[str] = set()
        self._via_push = False
        self.users = parse_users(entry.options)
        self.homecoming = HomecomingObserver(
            hass, entry.entry_id, dict(self.options), self.entry_doors, self._notify
        )

    # --- Konfiguration -----------------------------------------------------

    @property
    def has_codes(self) -> bool:
        """Gibt es mindestens einen PIN (Hauptbenutzer oder Benutzer)?"""
        return has_codes(self.users)

    @property
    def end_alarm_needs_code(self) -> bool:
        """Braucht "Alarm beenden" einen PIN? Nur mit PIN und ohne die Ausnahme-Option."""
        return self.has_codes and not bool(self.entry.options.get(OPT_END_ALARM_WITHOUT_PIN, False))

    @property
    def buttons_without_pin(self) -> bool:
        return bool(self.entry.options.get(OPT_BUTTONS_WITHOUT_PIN, False))

    def button_blocked(self, action: Action) -> bool:
        """Kann ein Dashboard-Knopf (ohne PIN-Abfrage) diese Aktion nicht ausführen?"""
        if self.buttons_without_pin:
            return False
        if action is Action.ARM:
            return self.code_arm_required
        if action is Action.END_ALARM:
            return self.end_alarm_needs_code
        return self.has_codes

    @property
    def code_arm_required(self) -> bool:
        return self.has_codes and bool(self.entry.options.get(OPT_CODE_ARM_REQUIRED, False))

    @property
    def card_unlinked_pin(self) -> bool:
        """Alarmkarte: Konten ohne Hauswacht-Benutzer brauchen einen PIN (Standard an)."""
        return bool(self.entry.options.get(OPT_CARD_PIN_UNLINKED, True))

    # --- Lebenszyklus ------------------------------------------------------

    # --- Profile ----------------------------------------------------------

    @property
    def lang(self) -> str:
        """Sprache der Benachrichtigungen: wie Home Assistant (Deutsch oder Englisch)."""
        return lang_of(self.hass.config.language)

    def profile_name(self, profile_id: str | None) -> str:
        if profile_id is None:
            return "-"
        if profile_id == ALWAYS_PROFILE_ID:
            return ALWAYS_PROFILE_NAME
        return profile_info(self.entry.options, profile_id).name

    @property
    def selected_profile(self) -> str | None:
        """Profil der Auswahlliste: das aktive Profil, sonst die Auswahl, sonst das erste."""
        if self.ctx.profile is not None:
            return self.ctx.profile.profile_id
        if self._selected_profile in self.profiles:
            return self._selected_profile
        return next(iter(self.profiles), None)

    # --- Profil-Einstellungen im Dashboard -------------------------------------

    @property
    def is_disarmed(self) -> bool:
        return self.ctx.state is AlarmState.DISARMED

    @property
    def all_disarmed(self) -> bool:
        """Sind alle Bereiche unscharf?"""
        return all(area.is_disarmed for area in self.main.areas.values())

    def _all_profile_ids(self) -> list[str]:
        """Alle Alarmprofile, über alle Bereiche (für "Profil bearbeiten")."""
        return [info.profile_id for info in profile_infos(self.entry.options)]

    @property
    def edit_profile(self) -> str | None:
        """Profil, dessen Einstellungen die Einstellungs-Entitäten zeigen und ändern."""
        ids = self._all_profile_ids()
        if self._edit_profile in ids:
            return self._edit_profile
        return next(iter(ids), None)

    @callback
    def select_edit_profile(self, profile_ref: str) -> None:
        profile_id = next(
            (
                pid
                for pid in self._all_profile_ids()
                if pid == profile_ref or self.profile_name(pid) == profile_ref
            ),
            None,
        )
        if profile_id is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="unknown_profile",
                translation_placeholders={"profile": profile_ref},
            )
        self._edit_profile = profile_id
        self._store.async_delay_save(self._storage_data, 0)
        self._notify()

    async def async_set_profile_setting(self, key: str, value: Any) -> None:
        """Eine Einstellung des bearbeiteten Profils ändern – nur im unscharfen Zustand."""
        if not self.all_disarmed:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="settings_require_disarmed"
            )
        profile_id = self.edit_profile
        if profile_id is None:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="no_profiles")
        try:
            options = write_setting(self.entry.options, profile_id, key, value)
        except (SettingError, TypeError, ValueError) as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_setting",
                translation_placeholders={"setting": key},
            ) from err
        _LOGGER.info(
            "Profil %s: %s = %s",
            self.profile_name(profile_id),
            key,
            options["profiles"][profile_id][key],
        )
        # Auswahl sichern, bevor das Neuladen nach der Optionsänderung startet
        await self._store.async_save(self._storage_data())
        self.hass.config_entries.async_update_entry(self.entry, options=options)

    @callback
    def select_profile(self, profile_ref: str) -> None:
        if self.ctx.state is not AlarmState.DISARMED:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="select_requires_disarmed"
            )
        profile_id = find_profile(self.options, profile_ref)
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
    def arm_selected(self, *, confirmed: bool = False, changed_by: str | None = None) -> None:
        profile_id = self.selected_profile
        if profile_id is None:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="no_profiles")
        self.arm(profile_id, confirmed=confirmed, changed_by=changed_by)

    async def async_start(self) -> None:
        data = await self._store.async_load() or {}
        selected = data.get("selected_profile")
        self._selected_profile = selected if isinstance(selected, str) else None
        edit = data.get("edit_profile")
        self._edit_profile = edit if isinstance(edit, str) else None
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
        self.reminder.start()
        if self.siren_tester is not None:
            await self.siren_tester.async_start()
        if self.silence is not None:
            await self.silence.async_start()
        if self.reviewer is not None:
            self.reviewer.async_start()
        if self.controls is not None:
            await self.controls.async_start()
        self._unsub_registry = self.hass.bus.async_listen(
            er.EVENT_ENTITY_REGISTRY_UPDATED, self._on_registry_updated
        )
        self._unsub_push = self.hass.bus.async_listen(PUSH_ACTION_EVENT, self._on_push_action)
        await self.homecoming.async_start()
        if self.main is self:
            await self._async_check_pin_coverage()

    @callback
    def async_stop(self) -> None:
        """Beim Entladen: Timer und Abos stoppen. Der gespeicherte Zustand bleibt erhalten."""
        self._cancel_timer()
        self._cancel_settle()
        self._cancel_speech_repeat()
        self._reset_rules()
        self.automation.stop()
        self.reminder.stop()
        if self.siren_tester is not None:
            self.siren_tester.async_stop()
        if self.silence is not None:
            self.silence.async_stop()
        if self.reviewer is not None:
            self.reviewer.async_stop()
        if self.controls is not None:
            self.controls.async_stop()
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
    def arm(
        self, profile_ref: str, *, confirmed: bool = False, changed_by: str | None = None
    ) -> None:
        """Schaltet ein Profil scharf (Profil-ID oder Name)."""
        tester = self.main.siren_tester
        if tester is not None and tester.running is not None:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="siren_test_running"
            )
        profile_id = find_profile(self.options, profile_ref)
        profile = self.profiles.get(profile_id) if profile_id else None
        if profile_id is None or profile is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="unknown_profile",
                translation_placeholders={"profile": profile_ref},
            )
        sensors = self.profile_sensors(profile_id)
        engine = build_engine(
            [
                self.rules[r]
                for r in profile_rule_ids(self.entry.options, profile_id)
                if r in self.rules
            ],
            self.zones,
            self._labels,
        )
        if not sensors and not engine.watched():
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="profile_has_no_sensors",
                translation_placeholders={"profile": self.profile_name(profile_id)},
            )
        if self.ctx.state is AlarmState.DISARMED:
            self.single_sensors = sensors
            self.armed_sensors = sensors | engine.watched()
            self._engine = engine
            closing = parse_arm_on_close(self.entry.options, profile_id)
            self._exit_doors = closing.doors if closing.enabled else frozenset()
            self._exit_settle = closing.settle
        previous = self.changed_by
        self.changed_by = changed_by
        effects = self._dispatch(
            ArmRequested(
                profile=profile,
                # Ausgangstüren dürfen beim Scharfschalten offen sein (Scharf durch Schließen)
                readiness=self.readiness_for(self.single_sensors - self._exit_doors),
                confirmed=confirmed,
            )
        )
        try:
            self._raise_for_rejection(effects)
        except ServiceValidationError as err:
            self.changed_by = previous
            self._notify_arm_failed(profile_id, effects, err, changed_by)
            raise
        if self._arm_pushed:
            self.notifier.clear(self._arm_pushed, PUSH_ARM_TAG)
            self._arm_pushed.clear()

    def _notify_arm_failed(
        self,
        profile_id: str,
        effects: tuple[Effect, ...],
        err: ServiceValidationError,
        changed_by: str | None,
    ) -> None:
        """Push "Scharfschalten gescheitert" mit "Trotzdem scharf" / "Erneut versuchen"."""
        can_confirm = any(isinstance(e, ConfirmationRequired) for e in effects)
        token = secrets.token_hex(8)
        self._pending_arms[token] = (profile_id, time.monotonic() + PENDING_ARM_SECONDS)
        actions = []
        if can_confirm:
            actions.append(
                {
                    "action": f"{PUSH_ARM_FORCE_PREFIX}{token}",
                    "title": tr(self.lang, "btn_arm_anyway"),
                    "authenticationRequired": True,
                }
            )
        actions.append(
            {
                "action": f"{PUSH_ARM_RETRY_PREFIX}{token}",
                "title": tr(self.lang, "btn_retry"),
                "authenticationRequired": True,
            }
        )
        by = tr(self.lang, "by_paren", who=changed_by) if changed_by else ""
        sent = self.notifier.notify(
            NotifyEvent.ARM_FAILED,
            tr(self.lang, "arm_failed_title"),
            tr(self.lang, "arm_failed", profile=self.profile_name(profile_id), by=by, reason=err),
            values={"profil": self.profile_name(profile_id), "wer": changed_by, "grund": str(err)},
            data={"tag": PUSH_ARM_TAG, "actions": actions},
            test_mode=self.ctx.test_mode,
        )
        self._arm_pushed.update(sent)

    @callback
    def send_arm_reminder(self, profile_id: str, message: str) -> None:
        """Erinnerung mit Knopf "Jetzt scharf schalten"."""
        token = secrets.token_hex(8)
        self._pending_arms[token] = (profile_id, time.monotonic() + REMINDER_ARM_SECONDS)
        sent = self.notifier.notify(
            NotifyEvent.REMINDER,
            tr(self.lang, "reminder_title"),
            message,
            values={"profil": self.profile_name(profile_id)},
            data={
                "tag": PUSH_ARM_TAG,
                "actions": [
                    {
                        "action": f"{PUSH_ARM_NOW_PREFIX}{token}",
                        "title": tr(
                            self.lang, "btn_arm_now", profile=self.profile_name(profile_id)
                        ),
                        "authenticationRequired": True,
                    }
                ],
            },
            test_mode=self.ctx.test_mode,
        )
        self._arm_pushed.update(sent)

    async def async_check_code(self, code: str | None, action: Action) -> str | None:
        """Prüft den PIN (mit Schutz gegen Durchprobieren) und liefert, wer es war.

        Ohne PINs: None. Bedrohungs-PIN: gilt als gültig, löst heimlich einen Notruf aus.
        """
        if not self.has_codes:
            return None
        identity = await self.async_identify(code, action)
        if not identity.duress:
            self.check_allowed(identity.users, action)
        return users_label(identity.users, self.lang)

    def check_allowed(self, users: tuple[User, ...], action: Action) -> None:
        """Darf mindestens einer dieser Benutzer die Aktion in diesem Bereich?"""
        if not self.permits(users, action):
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="action_not_allowed",
                translation_placeholders={"user": users_label(users, self.lang)},
            )

    async def async_identify(self, code: str | None, action: Action) -> Identity:
        """Ausweis prüfen: RFID-Karte oder PIN, mit gemeinsamem Schutz gegen Durchprobieren.

        Ungültig -> ServiceValidationError (``invalid_code`` oder ``code_locked``).
        """
        now = time.monotonic()
        locked = remaining_lock(self.main._code_guard, now)
        if locked:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="code_locked",
                translation_placeholders={"seconds": str(locked)},
            )
        timestamp = dt_util.utcnow().timestamp()
        card = match_tag(code, self.users, timestamp)
        if card.users:
            self.main._code_guard = register_success(self.main._code_guard)
            return Identity(kind="card", users=card.users)
        # PBKDF2 ist absichtlich langsam: im Hintergrund, damit Home Assistant nicht hängt
        match = await self.hass.async_add_executor_job(match_pin, code, self.users, timestamp)
        if match.duress:
            self.main._code_guard = register_success(self.main._code_guard)
            self._send_duress_alert(users_label(match.duress, self.lang), action)
            return Identity(kind="pin", users=match.duress, duress=True)
        if match.users:
            self.main._code_guard = register_success(self.main._code_guard)
            return Identity(kind="pin", users=match.users)
        blocked = match.blocked + card.blocked
        if blocked:
            self.notifier.send_system(
                tr(self.lang, "blocked_credential_title"),
                tr(self.lang, "blocked_credential", who=users_label(blocked, self.lang)),
            )
        if looks_like_card(code) and not blocked:
            # Unbekannte Karte (z. B. zum Anlernen): kann kein PIN sein und ist nicht zu erraten,
            # zählt daher nicht als Fehleingabe.
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="invalid_code")
        result = register_failure(self.main._code_guard, now)
        self.main._code_guard = result.state
        self.main._notify()
        failures = result.state.failures
        self.hass.bus.async_fire(
            EVENT_HAUSWACHT,
            {"type": "InvalidCode", "failures": failures, "lock_seconds": result.lock_seconds},
        )
        if result.warn:
            self.notifier.send_system(
                *invalid_code_message(failures, result.lock_seconds, self.lang)
            )
        if result.lock_seconds:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="code_locked",
                translation_placeholders={"seconds": str(result.lock_seconds)},
            )
        raise ServiceValidationError(translation_domain=DOMAIN, translation_key="invalid_code")

    def code_guard_info(self) -> dict[str, Any]:
        """Falscheingaben und Sperre (gemeinsam für alle Bereiche) für die Anzeige."""
        guard = self.main._code_guard
        left = remaining_lock(guard, time.monotonic())
        return {
            "code_failures": current_failures(guard, time.monotonic()),
            "code_locked_until": (dt_util.utcnow() + timedelta(seconds=left)).isoformat()
            if left
            else None,
        }

    def reset_code_guard(self, by: str | None) -> None:
        """Falscheingabezähler und Sperre zurücksetzen (nur Administratoren)."""
        failures = current_failures(self.main._code_guard, time.monotonic())
        self.main._code_guard = CodeGuardState()
        self.hass.bus.async_fire(
            EVENT_HAUSWACHT, {"type": "CodeLockReset", "by": by, "failures": failures}
        )
        _LOGGER.info("Falscheingaben zurückgesetzt (%s Fehlversuche) von %s", failures, by)
        for area in self.main.areas.values():
            area._notify()

    def permits(self, users: tuple[User, ...], action: Action) -> bool:
        """Darf mindestens einer dieser Benutzer die Aktion in diesem Bereich?"""
        return allowed_in(users, action, self.area_id)

    @property
    def area_name(self) -> str:
        return parse_areas(self.entry.options)[self.area_id].name

    async def async_actor_for_user(self, user_id: str | None, action: Action) -> str | None:
        """Wer bedient ohne PIN (Dashboard-Knopf, Push)? Verknüpfter Benutzer mit Rechten,
        sonst der Name des Home-Assistant-Kontos (dann ist alles erlaubt, wie bisher)."""
        linked = find_by_ha_user(self.users, user_id)
        if linked is not None:
            if not linked.valid_at(dt_util.utcnow().timestamp()) or not linked.may_in(
                action, self.area_id
            ):
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="action_not_allowed",
                    translation_placeholders={"user": linked.name},
                )
            return linked.name
        user = await self.hass.auth.async_get_user(user_id) if user_id else None
        return user.name if user is not None else None

    async def async_authorize(
        self, *, code: str | None, user_id: str | None, action: Action, require_code: bool
    ) -> str | None:
        """PIN prüfen, wenn nötig – sonst über das Home-Assistant-Konto zuordnen."""
        if require_code and self.has_codes:
            return await self.async_check_code(code, action)
        return await self.async_actor_for_user(user_id, action)

    async def _async_check_pin_coverage(self) -> None:
        """Reparatur-Hinweis, wenn es PINs gibt, aber Personen ohne PIN."""
        ha_users = {
            u.id: u.name
            for u in await self.hass.auth.async_get_users()
            if u.is_active and not u.system_generated and u.name
        }
        missing = people_without_pin(self.users, ha_users, ignore=[MASTER_USER_ID])
        if missing:
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                ISSUE_PIN_COVERAGE,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=ISSUE_PIN_COVERAGE,
                translation_placeholders={
                    "people": ", ".join(missing),
                    "buttons": "an" if self.buttons_without_pin else "aus",
                },
            )
        else:
            ir.async_delete_issue(self.hass, DOMAIN, ISSUE_PIN_COVERAGE)

    def _send_duress_alert(self, actor: str, action: Action) -> None:
        """Heimlicher Notruf: nur Push an die eigens festgelegten Empfänger, sonst nichts
        Sichtbares (kein Logbuch-Text, keine Benachrichtigung in Home Assistant)."""
        targets = [t for t in self.entry.options.get(OPT_DURESS_NOTIFY, []) if isinstance(t, str)]
        what = tr(
            self.lang,
            {
                Action.ARM: "duress_arm",
                Action.DISARM: "duress_disarm",
                Action.END_ALARM: "duress_end_alarm",
            }[action],
        )
        self.notifier.send_duress(
            targets,
            tr(self.lang, "duress_title"),
            tr(self.lang, "duress", who=actor, what=what),
            test_mode=self.ctx.test_mode,
        )

    def _action_for_disarm(self) -> Action:
        if self.ctx.state in (AlarmState.TRIGGERED, AlarmState.ALARM_HOLD):
            return Action.END_ALARM
        return Action.DISARM

    async def async_disarm(self, code: str | None, user_id: str | None = None) -> None:
        """Unscharf schalten; während eines Alarms nur den Alarm beenden (bleibt scharf)."""
        actor = await self.async_authorize(
            code=code, user_id=user_id, action=self._action_for_disarm(), require_code=True
        )
        self.disarm_trusted(changed_by=actor)

    @callback
    def disarm_trusted(self, changed_by: str | None = None) -> None:
        """Wie ``async_disarm`` ohne PIN – für eigene Automatik und bereits Geprüftes."""
        tester = self.main.siren_tester
        if tester is not None and tester.running is not None:
            tester.stop()  # Unscharf schalten bricht einen Sirenentest ab
        self.changed_by = changed_by
        self._dispatch(self._disarm_request())

    @callback
    def disarm_now(self, changed_by: str | None = None) -> None:
        """Sofort unscharf, auch während eines Alarms (erst Alarm beenden, dann unscharf)."""
        self.changed_by = changed_by
        if self.ctx.state in (AlarmState.TRIGGERED, AlarmState.ALARM_HOLD):
            self._dispatch(self._disarm_request())
        self._dispatch(DisarmRequested(code_valid=True))

    @callback
    def end_alarm(self, changed_by: str | None = None) -> None:
        """Nur den Alarm beenden; außerhalb eines Alarms passiert nichts."""
        if self.ctx.state in (AlarmState.TRIGGERED, AlarmState.ALARM_HOLD):
            self.changed_by = changed_by
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

    def _push_actions(self, title: str | None = None) -> dict[str, Any]:
        title = title or tr(self.lang, "btn_disarm")
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

    def _profile_speakers(self, profile_id: str | None = None) -> tuple[str, ...]:
        if profile_id is None and self.ctx.profile is not None:
            profile_id = self.ctx.profile.profile_id
        return profile_speakers(self.entry.options, profile_id)

    @callback
    def _send_alarm_push(
        self, title: str, message: str, values: Mapping[str, Any] | None = None
    ) -> None:
        sent = self.notifier.notify(
            NotifyEvent.ENTRY,
            title,
            message,
            values=values,
            profile_targets=self._alarm_targets(),
            profile_speakers=self._profile_speakers(),
            data=self._push_actions(),
            test_mode=self.ctx.test_mode,
        )
        self._pushed_targets.update(sent)

    @callback
    def _on_entry_delay(self) -> None:
        if self.ctx.profile is None:
            return
        sensor = self.ctx.trigger_sensor or ""
        self._send_alarm_push(
            tr(self.lang, "entry_title"),
            tr(
                self.lang,
                "entry",
                sensor=display_name(self.hass, sensor),
                seconds=self.ctx.profile.entry_delay,
                profile=self.profile_name(self.ctx.profile.profile_id),
            ),
            {
                "melder": display_name(self.hass, sensor),
                "sekunden": self.ctx.profile.entry_delay,
                "profil": self.profile_name(self.ctx.profile.profile_id),
            },
        )

    async def _on_push_action(self, event: HaEventAny[Any]) -> None:
        action = event.data.get("action")
        if not isinstance(action, str):
            return
        for prefix in (PUSH_ARM_FORCE_PREFIX, PUSH_ARM_RETRY_PREFIX, PUSH_ARM_NOW_PREFIX):
            if action.startswith(prefix):
                await self._on_push_arm(prefix, action[len(prefix) :], event.context.user_id)
                return
        if not action.startswith(PUSH_ACTION_PREFIX) or not self.push_disarm:
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
        try:
            actor = await self.async_actor_for_user(user.id, self._action_for_disarm())
        except ServiceValidationError:
            self.notifier.send(
                targets,
                tr(self.lang, "push_denied_title"),
                tr(self.lang, "push_denied", who=user.name),
                test_mode=test_mode,
            )
            return
        _LOGGER.warning("Push-Knopf durch %s (Zustand %s)", actor, self.ctx.state.value)
        self._via_push = True
        try:
            self.disarm_trusted(changed_by=actor)
        finally:
            self._via_push = False
        if self.ctx.state is AlarmState.DISARMED:
            self.notifier.send(
                targets,
                tr(self.lang, "disarmed_title"),
                tr(self.lang, "push_disarmed", who=actor),
                test_mode=test_mode,
            )

    async def _on_push_arm(self, prefix: str, token: str, user_id: str | None) -> None:
        """Push-Knöpfe "Trotzdem scharf", "Erneut versuchen", "Jetzt scharf"."""
        pending = self._pending_arms.pop(token, None)
        if pending is None or pending[1] < time.monotonic():
            _LOGGER.warning("Veralteter Push-Knopf zum Scharfschalten ignoriert")
            return
        user = await self.hass.auth.async_get_user(user_id) if user_id else None
        if user is None or not user.is_active or user.system_generated:
            _LOGGER.warning("Push-Knopf ohne gültigen Home-Assistant-Benutzer ignoriert")
            return
        if self.ctx.state is not AlarmState.DISARMED:
            return
        profile_id = pending[0]
        try:
            actor = await self.async_actor_for_user(user.id, Action.ARM)
            # Scheitert es erneut, kommt eine neue Nachricht mit neuen Knöpfen
            self.arm(profile_id, confirmed=prefix == PUSH_ARM_FORCE_PREFIX, changed_by=actor)
        except ServiceValidationError as err:
            _LOGGER.info("Scharfschalten per Push-Knopf nicht möglich: %s", err)

    @callback
    def set_test_mode(self, enabled: bool) -> None:
        """Testmodus gilt für alle Bereiche; umschalten nur, wenn alle unscharf sind."""
        if self.main is not self:
            self.main.set_test_mode(enabled)
            return
        for area in self.areas.values():
            if area.ctx.state is not AlarmState.DISARMED:
                area._raise_for_rejection(area._dispatch(SetTestMode(enabled=enabled)))
        for area in self.areas.values():
            area._raise_for_rejection(area._dispatch(SetTestMode(enabled=enabled)))
        if not self.ctx.test_mode and self._simulated:
            self._simulated.clear()  # ohne Testmodus gelten wieder nur echte Zustände
            for area in self.areas.values():
                area._notify()

    # --- Interna -----------------------------------------------------------

    # --- Sensoren ----------------------------------------------------------

    def profile_sensors(self, profile_id: str) -> frozenset[str]:
        """Melder, die im Profil einzeln auslösen: Gruppen ohne Technik-Melder und Ausnahmen."""
        zone_ids = profile_behaviour(self.entry.options, profile_id).zones
        sensors = resolve_zones(zone_ids, self.zones, self._labels)
        return sensors - self.technical_sensors - excluded_sensors(self.entry.options, profile_id)

    def type_of(self, entity_id: str) -> SensorType:
        return sensor_type(entity_id, device_class_of(self.hass, entity_id), self.sensor_types)

    def zone_members(self) -> dict[str, list[str]]:
        return {zone.name: sorted(resolve_zone(zone, self._labels)) for zone in self.zones.values()}

    def snapshots(self, entity_ids: frozenset[str]) -> dict[str, SensorSnapshot]:
        result: dict[str, SensorSnapshot] = {}
        now = dt_util.utcnow().timestamp()
        for entity_id in entity_ids:
            state = self.hass.states.get(entity_id)
            if (simulated := self.simulated(entity_id)) is not None:
                result[entity_id] = SensorSnapshot(
                    entity_id=entity_id,
                    state=simulated,
                    device_class=state.attributes.get("device_class") if state else None,
                    last_reported=now,
                    last_seen=None,
                )
                continue
            result[entity_id] = SensorSnapshot(
                entity_id=entity_id,
                state=normalize(entity_id, state.state if state else None),
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
            self.notifier.notify(
                NotifyEvent.FAULT, *fault_message(faulty, self.lang), test_mode=self.ctx.test_mode
            )
            title, message = fault_message(faulty, self.lang)
            persistent_notification.async_create(
                self.hass,
                message,
                title=title,
                notification_id=NOTIFICATION_FAULT,
            )
        elif not faulty:
            persistent_notification.async_dismiss(self.hass, NOTIFICATION_FAULT)

    # --- Immer aktive Melder --------------------------------------------------

    @callback
    def _always_triggered(self, entity_id: str) -> None:
        """Unscharf: Benachrichtigung (oder Alarm mit eigener Sirene), scharf: sofort Alarm."""
        name = display_name(self.hass, entity_id)
        self.hass.bus.async_fire(
            EVENT_HAUSWACHT, {"type": "AlwaysActiveTriggered", "sensor_key": entity_id}
        )
        # Technik-Melder: auch scharf nie Einbruchalarm, nur die Reaktion "immer aktiv"
        technical_only = entity_id in self.technical_sensors and not self.always.sirens_enabled
        if technical_only or (
            self.ctx.state is AlarmState.DISARMED and not self.always.sirens_enabled
        ):
            prefix = "[TEST] " if self.ctx.test_mode else ""
            message = tr(self.lang, "always", sensor=name)
            self.notifier.notify(
                NotifyEvent.ALWAYS_ACTIVE,
                tr(self.lang, "always_title"),
                message,
                values={"melder": name},
                test_mode=self.ctx.test_mode,
            )
            persistent_notification.async_create(
                self.hass,
                prefix + message,
                title=tr(self.lang, "always_title"),
                notification_id=f"{NOTIFICATION_ALARM}_always",
            )
            self._notify()
            return
        self._dispatch(
            AlwaysActiveTriggered(sensor_key=entity_id, profile=always_runtime(self.always))
        )

    @callback
    def panic(self, key: str, name: str) -> None:
        """Notruf-Taste mit Alarm: sofortiger Alarm (unscharf mit der Reaktion "immer aktiv",
        scharf mit der des aktiven Profils). Sirenen nur über den Guard."""
        self.hass.bus.async_fire(EVENT_HAUSWACHT, {"type": "Panic", "control": name})
        self._dispatch(AlwaysActiveTriggered(sensor_key=key, profile=always_runtime(self.always)))

    # --- Scharf durch Schließen der Tür -------------------------------------

    def _all_exit_doors(self) -> frozenset[str]:
        doors: set[str] = set()
        for profile_id in self.profiles:
            closing = parse_arm_on_close(self.entry.options, profile_id)
            if closing.enabled:
                doors |= closing.doors
        return frozenset(doors)

    @callback
    def _on_exit_door(self, new_state: str | None) -> None:
        """Ausgangstür während der Ausgangsverzögerung: zu -> nach Beruhigungszeit scharf."""
        self._cancel_settle()
        if new_state != "off":
            return

        @callback
        def _settled(_now: datetime) -> None:
            self._settle_timer = None
            if self.ctx.state is not AlarmState.ARMING:
                return
            states = self.snapshots(self._exit_doors)
            if any(s.state == "on" for s in states.values()):
                return
            _LOGGER.info("Ausgangstür geschlossen – Ausgangsverzögerung endet vorzeitig")
            self.hass.bus.async_fire(EVENT_HAUSWACHT, {"type": "ArmedByClosingDoor"})
            self._cancel_timer()
            self._dispatch(
                ExitDelayElapsed(token=self.ctx.timer_token, readiness=self._readiness())
            )

        self._settle_timer = async_call_later(self.hass, self._exit_settle, _settled)

    @callback
    def _cancel_settle(self) -> None:
        if self._settle_timer is not None:
            self._settle_timer()
            self._settle_timer = None

    # --- Regeln ("Tür, dann Keller") ----------------------------------------

    def _all_rule_sensors(self) -> frozenset[str]:
        return build_engine(self.rules.values(), self.zones, self._labels).watched()

    def rule_names(self, entity_id: str) -> list[str]:
        """Regeln des scharfen Profils, in denen der Melder vorkommt."""
        return [
            rule.name
            for rule in self._engine.rules
            if any(entity_id in m for m in self._engine.members.get(rule.rule_id, []))
        ]

    @callback
    def _sensor_triggered(self, entity_id: str, role: SensorRole) -> None:
        """Allein auslösende Melder direkt weiter, Regelmelder über die Regeln."""
        if entity_id in self.always_sensors and role is not SensorRole.TAMPER_24H:
            self._always_triggered(entity_id)
            return
        if role is SensorRole.TAMPER_24H or entity_id in self.single_sensors:
            self._dispatch(SensorTriggered(sensor_key=entity_id, role=role))
        if role is SensorRole.TAMPER_24H or entity_id not in self._engine.watched():
            return
        if self.ctx.state not in (AlarmState.ARMED, AlarmState.PENDING, AlarmState.ALARM_HOLD):
            return
        now = dt_util.utcnow().timestamp()
        recorded = self._engine.record(entity_id, now)
        fired = [r for r in recorded if self._conditions_met(r)]
        for rule in recorded:
            if rule not in fired:
                _LOGGER.info("Regel %s erfüllt, Bedingungen aber nicht – kein Alarm", rule.name)
                self.hass.bus.async_fire(
                    EVENT_HAUSWACHT,
                    {"type": "RuleConditionsNotMet", "rule": rule.rule_id, "sensor_key": entity_id},
                )
        if not fired:
            self.hass.bus.async_fire(EVENT_HAUSWACHT, {"type": "RuleStep", "sensor_key": entity_id})
            self._update_partials(now)
            return
        # Bei mehreren erfüllten Regeln gilt das strengere Ergebnis
        rule = max(fired, key=lambda r: STRICTNESS[r.result])
        if rule.result is RuleResult.NOTIFY:
            self.hass.bus.async_fire(
                EVENT_HAUSWACHT,
                {
                    "type": "RuleFired",
                    "rule": rule.rule_id,
                    "name": rule.name,
                    "sensor_key": entity_id,
                },
            )
            self.notifier.notify(
                NotifyEvent.RULE_NOTIFY,
                tr(self.lang, "rule_notify_title"),
                tr(
                    self.lang,
                    "rule_notify",
                    rule=quoted(self.lang, rule.name),
                    sensor=display_name(self.hass, entity_id),
                ),
                values={"regel": rule.name, "melder": display_name(self.hass, entity_id)},
                test_mode=self.ctx.test_mode,
            )
            self._reset_rules()
            self._notify()
            return
        self._fired_rule = rule.name
        _LOGGER.warning("Regel erfüllt: %s (durch %s)", rule.name, entity_id)
        self.hass.bus.async_fire(
            EVENT_HAUSWACHT,
            {"type": "RuleFired", "rule": rule.rule_id, "name": rule.name, "sensor_key": entity_id},
        )
        self._reset_rules(keep_fired=True)
        result_role = (
            SensorRole.ENTRY if rule.result is RuleResult.ENTRY_DELAY else SensorRole.INSTANT
        )
        self._dispatch(SensorTriggered(sensor_key=entity_id, role=result_role))

    def _conditions_met(self, rule: Rule) -> bool:
        """Bedingungen der Regel; nicht auswertbar = erfüllt (sichere Seite)."""

        def get(entity_id: str) -> tuple[str, Mapping[str, Any]] | None:
            state = self.hass.states.get(entity_id)
            return (state.state, state.attributes) if state else None

        return conditions_met(rule.conditions, get, dt_util.now())

    @callback
    def _update_partials(self, now: float) -> None:
        """Teilweise erfüllte Regeln verfolgen; abgelaufene ggf. melden."""
        current = self._engine.progress(now)
        for rule_id, old in self._partials.items():
            if rule_id not in current:
                self._on_rule_expired(old, now)
        self._partials = current
        if self._partial_timer is not None:
            self._partial_timer()
            self._partial_timer = None
        if current:
            delay = max(0.0, min(p.deadline for p in current.values()) - now) + 0.01

            @callback
            def _check(_now: datetime) -> None:
                self._partial_timer = None
                self._update_partials(dt_util.utcnow().timestamp())

            self._partial_timer = async_call_later(self.hass, delay, _check)
        self._notify()

    @callback
    def _on_rule_expired(self, progress: Progress, now: float) -> None:
        rule = self.rules.get(progress.rule_id)
        name = rule.name if rule else progress.rule_id
        first = display_name(self.hass, progress.first_sensor)
        _LOGGER.info("Regel %s nur teilweise erfüllt (%s)", name, progress.first_sensor)
        self.hass.bus.async_fire(
            EVENT_HAUSWACHT,
            {"type": "RuleExpired", "rule": progress.rule_id, "sensor_key": progress.first_sensor},
        )
        self.notifier.notify(
            NotifyEvent.UNCONFIRMED,
            tr(self.lang, "unconfirmed_title"),
            tr(
                self.lang,
                "unconfirmed",
                rule=quoted(self.lang, name),
                done=progress.done,
                total=progress.total,
                sensor=first,
            ),
            values={"regel": name, "melder": first},
            test_mode=self.ctx.test_mode,
        )
        if self._lone.record(progress.first_sensor, now):
            self.notifier.notify(
                NotifyEvent.UNCONFIRMED_FREQUENT,
                tr(self.lang, "lone_title"),
                tr(self.lang, "lone", sensor=first, count=FREQUENT_COUNT),
                values={"melder": first},
                test_mode=self.ctx.test_mode,
            )

    @callback
    def _reset_rules(self, *, keep_fired: bool = False) -> None:
        """Verlauf und Teilfortschritte verwerfen (ohne "unbestätigt"-Meldung)."""
        self._engine.reset()
        self._partials = {}
        if self._partial_timer is not None:
            self._partial_timer()
            self._partial_timer = None
        if not keep_fired:
            self._fired_rule = None

    def _blocked_until(self, rule: Rule) -> str | None:
        until = self._engine.blocked_until(rule, dt_util.utcnow().timestamp())
        return dt_util.utc_from_timestamp(until).isoformat() if until else None

    def rules_overview(self) -> list[dict[str, Any]]:
        """Regeln der scharfen Profile aller Bereiche mit Fortschritt (für die Testkarte)."""
        if self.main is not self:
            return self.main.rules_overview()
        multiple = len(self.areas) > 1
        rows: list[dict[str, Any]] = []
        for area in self.areas.values():
            for row in area._own_rules_overview():
                row["area"] = area.area_name if multiple else None
                rows.append(row)
        return rows

    def _own_rules_overview(self) -> list[dict[str, Any]]:
        rows = []
        for rule in self._engine.rules:
            progress = self._partials.get(rule.rule_id)
            rows.append(
                {
                    "name": rule.name,
                    "steps": len(rule.steps),
                    "done": progress.done if progress else 0,
                    "deadline": dt_util.utc_from_timestamp(progress.deadline).isoformat()
                    if progress
                    else None,
                    "result": rule.result.value,
                    "blocked_until": self._blocked_until(rule),
                    "text": describe_rule(
                        rule,
                        lambda e: display_name(self.hass, e),
                        lambda z: self.zones[z].name if z in self.zones else z,
                        "de" if (self.hass.config.language or "").startswith("de") else "en",
                    ),
                }
            )
        return rows

    # --- Simulation (nur Testmodus) -----------------------------------------

    def simulated(self, entity_id: str) -> str | None:
        """Simulierter Zustand – nur im Testmodus wirksam."""
        if not self.ctx.test_mode:
            return None
        return self._simulated.get(entity_id)

    def _all_known(self) -> frozenset[str]:
        """Sensoren aller Bereiche (für Simulation und Testkarte)."""
        known: set[str] = set()
        for area in self.main.areas.values():
            known |= area.candidates | area.armed_sensors
        return frozenset(known)

    def _require_simulation(self, entity_id: str) -> None:
        if not self.ctx.test_mode:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="simulation_requires_test_mode"
            )
        if entity_id not in self._all_known():
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="unknown_sensor",
                translation_placeholders={"sensor": entity_id},
            )

    @callback
    def simulate_state(self, entity_id: str, value: str) -> None:
        """Sensorzustand für Hauswacht simulieren ("on", "off", "unavailable") oder mit
        "real" auf den echten Wert zurücksetzen. Das Gerät und sein Zustand in Home
        Assistant bleiben unverändert; andere Automationen merken nichts davon."""
        if self.main is not self:
            self.main.simulate_state(entity_id, value)
            return
        if value not in SIMULATION_VALUES:
            raise ServiceValidationError(f"Unbekannter Zustand: {value}")
        self._require_simulation(entity_id)
        real = self.hass.states.get(entity_id)
        real_state = normalize(entity_id, real.state if real else None)
        old = self._simulated.get(entity_id, real_state)
        if value == SIMULATION_REAL:
            self._simulated.pop(entity_id, None)
            new = real_state
        else:
            self._simulated[entity_id] = value
            new = value
        self.hass.bus.async_fire(
            EVENT_HAUSWACHT,
            {"type": "SensorSimulated", "sensor_key": entity_id, "state": value},
        )
        device_class = real.attributes.get("device_class") if real else None
        for area in self.areas.values():
            if old != new and entity_id in area.candidates | area.armed_sensors:
                area._handle_sensor_change(entity_id, old, new, device_class)
            else:
                area._notify()

    @callback
    def simulate_reset(self) -> None:
        """Alle simulierten Zustände auf die echten Werte zurücksetzen."""
        if self.main is not self:
            self.main.simulate_reset()
            return
        if not self.ctx.test_mode:
            self._simulated.clear()
            for area in self.areas.values():
                area._notify()
            return
        for entity_id in list(self._simulated):
            self.simulate_state(entity_id, SIMULATION_REAL)

    def simulation_overview(self) -> list[dict[str, Any]]:
        """Alle Hauswacht-Sensoren mit echtem und simuliertem Zustand (für die Testkarte)."""
        rows: list[dict[str, Any]] = []
        areas = list(self.main.areas.values())
        for entity_id in self._all_known():
            state = self.hass.states.get(entity_id)
            device_class = state.attributes.get("device_class") if state else None
            # Status aus dem Bereich, der mit dem Melder gerade am meisten tut
            owner = next(
                (
                    a
                    for a in areas
                    if a._sensor_status(entity_id, device_class)
                    not in ("disarmed", "not_monitored")
                ),
                self.main,
            )
            status = owner._sensor_status(entity_id, device_class)
            idle = status in ("disarmed", "not_monitored")
            rows.append(
                {
                    "entity_id": entity_id,
                    "name": display_name(self.hass, entity_id),
                    "device_class": device_class,
                    "role": sensor_role(entity_id, device_class, self.role_overrides).value,
                    "real": normalize(entity_id, state.state if state else None),
                    "raw": state.state if state else None,
                    "kind": domain_of(entity_id),
                    "type": self.type_of(entity_id).value,
                    "simulated": self.simulated(entity_id),
                    "status": status,
                    "rules": owner.rule_names(entity_id),
                    "area": owner.area_name if len(areas) > 1 and not idle else None,
                }
            )
        return sorted(rows, key=lambda r: str(r["name"]).casefold())

    def _sensor_status(self, entity_id: str, device_class: str | None) -> str:
        """Was Hauswacht gerade mit dem Sensor macht (Anzeige in der Testkarte)."""
        ctx = self.ctx
        armed = ctx.state is not AlarmState.DISARMED and ctx.profile is not None
        role = sensor_role(entity_id, device_class, self.role_overrides)
        if role is SensorRole.TAMPER_24H:
            if armed and ctx.profile is not None and ctx.profile.tamper_triggers_alarm:
                return "tamper_alarm"
            return "tamper_message"
        if entity_id in self.always_sensors:
            return "always_active"
        if not armed:
            return "disarmed"
        if entity_id in ctx.bypassed_until_closed:
            return "bypassed_until_closed"
        if entity_id in ctx.bypassed:
            return "bypassed"
        if entity_id in self.single_sensors:
            return "monitored"
        if entity_id in self._engine.watched():
            return "in_rule"
        return "not_monitored"

    @property
    def simulated_count(self) -> int:
        return len(self._simulated) if self.main.ctx.test_mode else 0

    @callback
    def simulate_trigger(self, entity_id: str) -> None:
        """Simuliert das Auslösen eines konfigurierten Sensors. Nur im Testmodus erlaubt."""
        if self.main is not self:
            self.main.simulate_trigger(entity_id)
            return
        self._require_simulation(entity_id)
        for area in self.areas.values():
            area._simulate_trigger(entity_id)

    @callback
    def _simulate_trigger(self, entity_id: str) -> None:
        state = self.hass.states.get(entity_id)
        device_class = state.attributes.get("device_class") if state else None
        role = sensor_role(entity_id, device_class, self.role_overrides)
        self.hass.bus.async_fire(
            EVENT_HAUSWACHT, {"type": "SensorSimulated", "sensor_key": entity_id}
        )
        armed = self.ctx.state is not AlarmState.DISARMED
        if (role is SensorRole.TAMPER_24H and self._tamper_mine(entity_id)) or (
            armed and entity_id in self.armed_sensors
        ):
            self._sensor_triggered(entity_id, role)

    def _tamper_mine(self, entity_id: str) -> bool:
        """Manipulation meldet genau ein Bereich: der scharfe, der den Melder überwacht –
        sonst der Hauptbereich (keine doppelten Meldungen bei mehreren Bereichen)."""
        claimed = [
            a
            for a in self.main.areas.values()
            if a.ctx.state is not AlarmState.DISARMED and entity_id in a.armed_sensors
        ]
        if claimed:
            return self in claimed[:1]
        return self.main is self

    def _readiness(self) -> Readiness:
        # Melder, die nur in Regeln vorkommen, blockieren das Scharfschalten nicht
        return self.readiness_for(self.single_sensors)

    @callback
    def _refresh_sensors(self) -> None:
        """Labels neu einlesen und Zustandsabos auf alle konfigurierten Sensoren setzen."""
        self._labels = entities_by_label(self.hass)
        # Technik-Melder (Wasser, Gas, Frost …) aus allen Gruppen sind immer aktiv
        self.technical_sensors = frozenset(
            e
            for e in all_configured_sensors(self.zones, self._labels)
            if self.type_of(e) is SensorType.TECHNICAL
        )
        self.always_sensors = (
            frozenset(self.always.sensors)
            | resolve_zones(self.always.zones, self.zones, self._labels)
            | self.technical_sensors
        )
        configured = (
            all_configured_sensors(self.zones, self._labels)
            | self._all_rule_sensors()
            | self.always_sensors
            | self._all_exit_doors()
        )
        # Nur Melder mit offen/zu (z. B. Messwerte aus 0.24 in alten Auslöseregeln ignorieren)
        self.candidates = frozenset(e for e in configured if domain_of(e) in MONITORED_DOMAINS)
        if ignored := sorted(configured - self.candidates):
            _LOGGER.warning(
                "Hauswacht ignoriert Entitäten ohne offen/zu (Auslöseregeln prüfen): %s",
                ", ".join(ignored),
            )
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
        if self.simulated(entity_id) is not None:
            self._notify()  # simulierter Zustand hat Vorrang; der echte wird nur angezeigt
            return
        old = event.data["old_state"]
        new = event.data["new_state"]
        device_class = new.attributes.get("device_class") if new else None
        self._handle_sensor_change(
            entity_id,
            normalize(entity_id, old.state if old else None),
            normalize(entity_id, new.state if new else None),
            device_class,
        )

    @callback
    def _handle_sensor_change(
        self,
        entity_id: str,
        old_state: str | None,
        new_state: str | None,
        device_class: str | None,
    ) -> None:
        """Zustandswechsel eines Sensors bewerten – echt oder simuliert."""
        role = sensor_role(entity_id, device_class, self.role_overrides)
        armed = self.ctx.state is not AlarmState.DISARMED
        if self.ctx.state is AlarmState.ARMING and entity_id in self._exit_doors:
            self._on_exit_door(new_state)

        relevant = (
            (role is SensorRole.TAMPER_24H and self._tamper_mine(entity_id))
            or entity_id in self.always_sensors
            or (armed and entity_id in self.armed_sensors)
        )
        if relevant and is_trigger(old_state, new_state):
            self._sensor_triggered(entity_id, role)
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
        self.notifier.notify(
            NotifyEvent.FAULT,
            *sensor_lost_message(entity_id, self.lang),
            test_mode=self.ctx.test_mode,
        )
        title, message = sensor_lost_message(entity_id, self.lang)
        persistent_notification.async_create(
            self.hass,
            message + tr(self.lang, "sensor_lost_armed"),
            title=title,
            notification_id=f"{NOTIFICATION_ALARM}_{entity_id}",
        )

    def _rejection_placeholders(
        self, open_sensors: frozenset[str], unavailable: frozenset[str]
    ) -> dict[str, str]:
        """Klartext für Meldungen: Namen mit Raum, gestörte Infrastruktur getrennt."""
        faulty = unavailable & self.main.infrastructure

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
        if self.ctx.state is not AlarmState.ARMING:
            self._cancel_settle()
        if self.ctx.state is AlarmState.DISARMED:
            self.sirens.reset()
            self._reset_rules()
            self._engine = RuleEngine()
            self._exit_doors = frozenset()
            self.automation.on_disarmed()
            if self.armed_sensors:
                self.armed_sensors = frozenset()
                self.single_sensors = frozenset()
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
            "edit_profile": self._edit_profile,
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
                if effect.new is not AlarmState.TRIGGERED:
                    self._cancel_speech_repeat()
                self._observe_entry(effect)
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
                self._notify_state_change(effect)
            case ActivateReaction():
                self._on_alarm(effect)
            case StopReaction():
                _LOGGER.info("Alarmreaktion beendet (Profil %s)", effect.profile_id)
                self.sirens.stop(test_mode=effect.test_mode)
            case TamperDetected():
                self.notifier.notify(
                    NotifyEvent.FAULT,
                    *tamper_message(effect.sensor_key, self.lang),
                    test_mode=self.ctx.test_mode,
                )
            case RestartedDisarmed():
                title, message = restart_message(
                    self.profile_name(effect.previous_profile_id), self.lang
                )
                self.notifier.send_system(title, message)
                persistent_notification.async_create(
                    self.hass,
                    message,
                    title=title,
                    notification_id=NOTIFICATION_RESTART,
                )
            case AlarmAcknowledged():
                self._reset_rules()
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
    def open_rule_sensors(self) -> dict[str, list[str]]:
        """Offene Melder, die im scharfen Profil nur in Regeln vorkommen -> Regelnamen.

        Sie können eine Regel erst wieder beginnen, wenn sie zu und wieder auf gehen.
        """
        only_rules = self.armed_sensors - self.single_sensors
        snapshots = self.snapshots(only_rules)
        return {
            entity_id: self.rule_names(entity_id)
            for entity_id in sorted(only_rules)
            if snapshots[entity_id].state == "on"
        }

    @callback
    def _hint_open_rule_sensors(self) -> None:
        """Hinweis beim Scharfschalten: offene Regelmelder sind bis zum Schließen eine Lücke."""
        open_sensors = self.open_rule_sensors()
        if not open_sensors or self.ctx.profile is None:
            return
        lang = self.lang
        lines = [
            tr(
                lang,
                "arm_hint_item",
                sensor=display_name(self.hass, entity_id),
                rules=", ".join(quoted(lang, n) for n in names),
            )
            for entity_id, names in open_sensors.items()
        ]
        message = tr(
            lang,
            "arm_hint",
            profile=self.profile_name(self.ctx.profile.profile_id),
            items="; ".join(lines),
        )
        self.hass.bus.async_fire(
            EVENT_HAUSWACHT, {"type": "OpenRuleSensors", "sensors": list(open_sensors)}
        )
        self.notifier.notify(
            NotifyEvent.ARM_HINT,
            tr(lang, "arm_hint_title"),
            message,
            values={
                "profil": self.profile_name(self.ctx.profile.profile_id),
                "offen": ", ".join(display_name(self.hass, e) for e in open_sensors),
            },
            test_mode=self.ctx.test_mode,
        )
        persistent_notification.async_create(
            self.hass,
            message,
            title=tr(lang, "arm_hint_short_title"),
            notification_id=NOTIFICATION_ARM_HINT,
        )

    def _notify_state_change(self, effect: StateChanged) -> None:
        """Ereignisse "Scharf geschaltet" und "Unscharf geschaltet" (standardmäßig aus)."""
        lang = self.lang
        by = by_text(lang, self.changed_by)
        if (
            effect.new is AlarmState.ARMED
            and effect.old in (AlarmState.ARMING, AlarmState.DISARMED)
            and self.ctx.profile is not None
        ):
            self.notifier.notify(
                NotifyEvent.ARMED,
                tr(lang, "armed_title"),
                tr(lang, "armed", profile=self.profile_name(self.ctx.profile.profile_id), by=by),
                values={
                    "profil": self.profile_name(self.ctx.profile.profile_id),
                    "wer": self.changed_by,
                },
                test_mode=self.ctx.test_mode,
            )
            self._hint_open_rule_sensors()
        if effect.new is AlarmState.DISARMED:
            persistent_notification.async_dismiss(self.hass, NOTIFICATION_ARM_HINT)
        if effect.cause == "always_alarm_ended":
            self.notifier.notify(
                NotifyEvent.ALARM_ENDED,
                tr(lang, "alarm_ended_title"),
                tr(lang, "alarm_ended_disarmed", by=by),
                values={"wer": self.changed_by},
                test_mode=self.ctx.test_mode,
            )
        if (
            effect.new is AlarmState.DISARMED
            and effect.old is not AlarmState.DISARMED
            and not self._via_push  # dort gibt es eine eigene Rückmeldung
        ):
            self.notifier.notify(
                NotifyEvent.DISARMED,
                tr(lang, "disarmed_title"),
                tr(lang, "disarmed", by=by),
                values={"wer": self.changed_by},
                test_mode=self.ctx.test_mode,
            )

    @callback
    def _on_acknowledged(self, effect: AlarmAcknowledged) -> None:
        name = self.profile_name(effect.profile_id)
        lang = self.lang
        message = tr(lang, "alarm_ended_armed", by=by_text(lang, self.changed_by), profile=name)
        if effect.bypassed_until_closed:
            names = ", ".join(
                display_name(self.hass, s) for s in sorted(effect.bypassed_until_closed)
            )
            message += tr(lang, "alarm_ended_bypassed", sensors=names)
        _LOGGER.warning(message)
        targets = parse_reaction(self.entry.options, effect.profile_id).notify
        if self._pushed_targets:
            self.notifier.clear(self._pushed_targets, PUSH_TAG)
            self._pushed_targets.clear()
        self.notifier.notify(
            NotifyEvent.ALARM_ENDED,
            tr(lang, "alarm_ended_title"),
            message,
            profile_targets=targets,
            profile_speakers=self._profile_speakers(effect.profile_id),
            values={"wer": self.changed_by, "profil": name},
            test_mode=self.ctx.test_mode,
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
        if effect.profile_id == ALWAYS_PROFILE_ID:
            reaction = parse_reaction(
                always_reaction_options(self.entry.options), ALWAYS_PROFILE_ID
            )
            profile = always_runtime(self.always)
        else:
            reaction = parse_reaction(self.entry.options, effect.profile_id)
            profile = self.profiles[effect.profile_id]
        decision = self.sirens.activate(
            reaction.siren_targets,
            reaction.tone,
            reaction.volume,
            profile.reaction_time,
            test_mode=effect.test_mode,
        )
        lang = self.lang
        title, message = alarm_message(
            self.profile_name(effect.profile_id),
            display_name(self.hass, effect.sensor_key),
            test_mode=effect.test_mode,
            lang=lang,
        )
        if decision.commands:
            message += tr(
                lang, "alarm_sirens", sirens=", ".join(c.entity_id for c in decision.commands)
            )
        if decision.blocked:
            reasons = sorted({b.reason.value for b in decision.blocked})
            message += tr(lang, "alarm_sirens_blocked", reasons=", ".join(reasons))
        alarm_values = {
            "melder": display_name(self.hass, effect.sensor_key),
            "profil": self.profile_name(effect.profile_id),
            "regel": self._fired_rule or "",
        }
        if self._fired_rule:
            message += tr(lang, "alarm_rule", rule=self._fired_rule)
            self._fired_rule = None
        if reaction.silent:
            message += tr(lang, "alarm_silent")
        sent = self.notifier.notify(
            NotifyEvent.ALARM,
            title,
            message,
            profile_targets=reaction.notify,
            profile_speakers=self._profile_speakers(effect.profile_id),
            values=alarm_values,
            test_mode=effect.test_mode,
            data=self._push_actions(tr(lang, "btn_end_alarm")),
            # Stiller Alarm: nichts ansagen (sonst hört es der Eindringling)
            speak=not reaction.silent,
        )
        if not reaction.silent:
            self._start_speech_repeat(
                effect.profile_id,
                self.notifier.fill_values(message, alarm_values),
                test_mode=effect.test_mode,
            )
        self._pushed_targets.update(sent)
        persistent_notification.async_create(
            self.hass, message, title=title, notification_id=NOTIFICATION_ALARM
        )

    @callback
    def _start_speech_repeat(
        self, profile_id: str, values: Mapping[str, str], *, test_mode: bool
    ) -> None:
        """Alarm-Durchsage alle N Sekunden wiederholen, solange der Alarm läuft."""
        self._cancel_speech_repeat()
        seconds = parse_speech(self.entry.options).repeat
        if not seconds:
            return
        speakers = self._profile_speakers(profile_id)

        @callback
        def _again(_now: datetime) -> None:
            if self.ctx.state is not AlarmState.TRIGGERED:
                self._cancel_speech_repeat()
                return
            self.notifier.speak(
                NotifyEvent.ALARM, values, profile_speakers=speakers, test_mode=test_mode
            )

        self._speech_repeat = async_track_time_interval(
            self.hass, _again, timedelta(seconds=seconds)
        )

    @callback
    def _observe_entry(self, effect: StateChanged) -> None:
        """Heimkehr-Beobachtung: Zeit von "Tür auf" bis "unscharf" messen (schaltet nichts)."""
        if effect.new is AlarmState.PENDING and effect.old is not AlarmState.PENDING:
            profile = self.ctx.profile
            self.homecoming.entry_started(
                self.ctx.trigger_sensor, profile.entry_delay if profile else 0
            )
        elif effect.old is AlarmState.PENDING and effect.new is not AlarmState.PENDING:
            self.homecoming.entry_finished(in_time=effect.new is AlarmState.DISARMED)

    @callback
    def _cancel_speech_repeat(self) -> None:
        if self._speech_repeat is not None:
            self._speech_repeat()
            self._speech_repeat = None

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
