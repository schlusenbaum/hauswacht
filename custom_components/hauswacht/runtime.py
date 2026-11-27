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
from dataclasses import dataclass, field, fields
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_STATE_REPORTED
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, State, callback
from homeassistant.core import Event as HaEvent
from homeassistant.core import Event as HaEventAny
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.event import (
    EventStateChangedData,
    async_call_later,
    async_track_point_in_utc_time,
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.start import async_at_started
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .automation_runner import REASON_RESTART, AutomationRunner
from .const import (
    DOMAIN,
    EVENT_AREA_ALL,
    EVENT_HAUSWACHT,
    ISSUE_PIN_COVERAGE,
    ISSUE_PIN_MASTER_ONLY,
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
    PUSH_CODE_TAG,
    PUSH_EXIT_ALARM_PREFIX,
    PUSH_EXIT_LET_PREFIX,
    PUSH_LOST_TAG,
    PUSH_PASSAGE_PREFIX,
    PUSH_PASSAGE_TAG,
    PUSH_STATE_TAG,
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
from .core.away_proof import SIM_REAL, SIM_VALUES
from .core.changes import options_revision
from .core.code_guard import (
    CodeGuardState,
    current_failures,
    register_failure,
    register_success,
    remaining_lock,
)
from .core.conditions import all_met as conditions_met
from .core.confirmation import FREQUENT_COUNT, LoneTriggerCounter
from .core.controls import looks_like_card, normalize_tag
from .core.debug_log import describe
from .core.exit_detection import parse_exit
from .core.infrastructure import SystemReport, faulty_indicators, system_report
from .core.notify_events import NotifyEvent
from .core.notify_events import enabled as notify_enabled
from .core.passage import (
    CLOSES_FOR_RETURN,
    Direction,
    OutDoors,
    OutEnd,
    PassageConfig,
    out_candidates,
    parse_passage,
    path_sensors,
)
from .core.profile_settings import SettingError
from .core.profile_settings import write as write_setting
from .core.profiles import (
    build_profiles,
    find_profile,
    profile_behaviour,
    profile_info,
    profile_infos,
    stale_after_seconds,
    stale_overrides_seconds,
)
from .core.reactions import (
    alarm_message,
    auto_armed_message,
    auto_disarmed_message,
    fault_message,
    invalid_code_message,
    parse_reaction,
    restart_message,
    sensor_lost_message,
    tamper_message,
)
from .core.restart import (
    ARM_AFTER_START,
    STARTUP_GRACE,
    RestartKind,
    RestartPlan,
    continue_alarm,
    plan_restart,
    restart_behavior,
    restart_profile,
    saved_state,
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
    role_overrides,
    sensor_type,
)
from .core.sensors import (
    UNAVAILABLE_STATES,
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
from .core.siren_guard import BlockReason
from .core.speech import parse_speech, profile_speakers
from .core.state_machine import (
    ActivateReaction,
    AlarmAcknowledged,
    AlarmContext,
    AlarmState,
    AlwaysActiveTriggered,
    ArmingAborted,
    ArmRequested,
    BypassedSensorOpened,
    BypassUntilClosed,
    CancelTimer,
    ConfirmationRequired,
    DisarmRequested,
    Effect,
    EntryDelayElapsed,
    Event,
    ExitDelayElapsed,
    PassageDoorUsed,
    PassageEnd,
    PassageEnded,
    PassageGranted,
    PassageIn,
    PassageOut,
    ReactionTimeElapsed,
    Readiness,
    Rejected,
    RestartedDisarmed,
    RestoreRequested,
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
from .core.tilt import POSITION_NAMES, TILTED, effective_types, judge, parse_tilt_sources
from .core.tilt import position as tilt_position
from .core.users import (
    Action,
    Identity,
    User,
    allowed_in,
    disabled_tag,
    find_by_ha_user,
    has_codes,
    identity_label,
    match_pin,
    match_tag,
    parse_users,
    people_without_pin,
    tag_credential,
)
from .core.users import label as users_label
from .core.vibration import (
    VibrationCounter,
    VibrationRule,
    parse_vibration_sources,
    rule_for_zone_id,
)
from .core.vibration import position as vibration_position
from .errors import ArmRefused
from .exit_detector import ExitDetector
from .homecoming_observer import HomecomingObserver
from .names import display_name
from .notifier import Notifier
from .reminder import ReminderRunner
from .review import IssueReporter
from .silence_observer import SilenceObserver
from .siren_executor import SirenExecutor
from .siren_test import SirenTester

_LOGGER = logging.getLogger(__name__)

# Ausgefallener Melder: so lange warten, bevor er einzeln gemeldet wird (Infrastruktur zuerst)
LOST_SETTLE_SECONDS = 10


def lost_tag(entity_id: str) -> str:
    """Eigene Nachricht je ausgefallenem Melder: ersetzt sich selbst, weg, wenn er wieder da ist."""
    return f"{PUSH_LOST_TAG}_{entity_id}"


SIMULATION_REAL = "real"
SIMULATION_VALUES = frozenset({"on", "off", "tilted", "unavailable", SIMULATION_REAL})

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
    for item in fields(effect):
        payload[item.name] = _jsonable(getattr(effect, item.name))
    return payload


# Gastmodus "bis ich ausschalte" (gespeicherter Wert statt eines Zeitpunkts)
GUEST_UNTIL_OFF = -1.0


@dataclass
class PassageOutRun:
    """Laufender Durchgang "rausgehen" (ADR 0013)."""

    until: float  # Zeitpunkt (UTC-Sekunden)
    by: str
    end: OutEnd
    sensors: set[str] = field(default_factory=set)  # Wegmelder und benutzte Türen
    doors: set[str] = field(default_factory=set)  # benutzte Türen
    closes: int = 0


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
        self.sirens.on_change = self._save_soon
        self.sirens.fire_event = self.fire_event
        self.sirens.test_mode_now = lambda: self.ctx.test_mode
        self._unsub_siren_check: CALLBACK_TYPE | None = None
        self._unsub_resume: CALLBACK_TYPE | None = None
        # Gastmodus: keine automatische Scharfschaltung (None = aus; GUEST_UNTIL_OFF = bis aus)
        self.guest_until: float | None = None
        self._unsub_guest: CALLBACK_TYPE | None = None
        # Wann Karten ("card:<ID>") und PINs ("pin:<Benutzer>") zuletzt geschaltet haben
        # (nur im Hauptbereich gepflegt; gespeichert, nicht in den Einstellungen)
        self.last_used: dict[str, float] = {}
        # Code-Entitäten der Keypads, die Hauswacht schon einmal deaktiviert hat (nur einmal)
        self.code_entities_hidden: list[str] = []
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
        self.exit = ExitDetector(self)  # Ausgangserkennung (ADR 0014)
        self._entry_token: int | None = None
        areas = parse_areas(entry.options)
        self.notifier = Notifier(
            hass, entry.options, label=areas[area_id].name if len(areas) > 1 else None
        )
        self.notifier.fire_event = self.fire_event
        self.reminder = ReminderRunner(self)
        self.zones = parse_zones(entry.options)
        # Melder mit Kippstellung (ADR 0010): drei Stellungen, Bewertung je Profil
        # Stand der Einstellungen, mit dem dieser Lauf gestartet ist (Einstellungsseite)
        self.loaded_revision = options_revision(entry.options)
        self.tilt_sources = parse_tilt_sources(entry.options)
        # Erschütterungsstärke als Zahl und Fehlalarmschutz je Meldergruppe (ADR 0010 Teil B)
        self.vibration_sources = parse_vibration_sources(entry.options)
        self._vibration = VibrationCounter()
        self._unsub_reported: CALLBACK_TYPE | None = None
        self._bypass_position: dict[str, str | None] = {}
        self.sensor_types = effective_types(entry.options)
        self.role_overrides = role_overrides(self.sensor_types)
        self.stale_after = stale_after_seconds(entry.options)
        # Eigene Funkstille-Grenzen je Melder (None = nie prüfen)
        self.stale_overrides = stale_overrides_seconds(entry.options)
        # Funknetz/Gateways überwacht nur der Hauptbereich (sonst doppelte Meldungen)
        self.infrastructure: frozenset[str] = frozenset(
            str(e)
            for e in entry.options.get(OPT_INFRASTRUCTURE, [])
            if isinstance(e, str) and main is None
        )
        self._infra_faulty: frozenset[str] = frozenset()
        # Simulierte Sensorzustände (nur Testmodus, nur für Hauswacht, nie in Home Assistant)
        self._simulated: dict[str, str] = self.main._simulated if main else {}
        # Simulierte Anwesenheit je Person (nur Testmodus, nur für Hauswacht – ADR 0016)
        self._presence_sim: dict[str, str] = self.main._presence_sim if main else {}
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
        # Nach dem Wiederherstellen: Startphase (keine Ausfallmeldungen, offene Melder überbrücken)
        self._grace_until: float | None = None
        self._unsub_grace: CALLBACK_TYPE | None = None
        # "Nach Neustart scharf": eigener Timer (Warten auf den Start, dann ARM_AFTER_START)
        self._unsub_restart_arm: CALLBACK_TYPE | None = None
        self._startup_open: frozenset[str] = frozenset()
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
        # Wer die letzte Scharf-/Unscharf-Nachricht bekommen hat (zum Ersetzen und Wegräumen)
        self._state_pushed: set[str] = set()
        # Wer Warnungen zu falschen PINs bekommen hat (beim Zurücksetzen wegräumen)
        self._code_pushed: set[str] = set()
        # Unscharf über den Push-Knopf: wer es war (die Rückmeldung ersetzt die Scharf-Nachricht)
        self._via_push: tuple[str, tuple[str, ...]] | None = None
        # Automatik schaltet: Grund für die eine Scharf-/Unscharf-Nachricht (statt zwei)
        self._auto_arm_reason: str | None = None
        self._auto_disarm_reason: tuple[str, str] | None = None  # (Profil, Grund)
        # Ausgefallene Melder: eine Nachricht je Melder, weg, sobald er sich wieder meldet
        self._lost_pushed: dict[str, set[str]] = {}
        self._lost_timers: dict[str, CALLBACK_TYPE] = {}
        # Durchgang (ADR 0013): reinkommen (Tür -> Wegmelder), rausgehen, Zeiten, Nachrichten
        self._passage_in_doors: dict[str, frozenset[str]] = {}
        self._passage_out: PassageOutRun | None = None
        self._passage_timers: dict[str, CALLBACK_TYPE] = {}
        self._passage_pushed: set[str] = set()
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
        # Erster Start in diesem Lauf von Home Assistant oder nur neu geladen?
        started: set[str] = self.hass.data.setdefault(f"{DOMAIN}_started", set())
        start_key = f"{self.entry.entry_id}:{self.area_id}"
        reload = start_key in started
        started.add(start_key)
        plan = plan_restart(
            restart_behavior(self.entry.options),
            saved=data.get("restore") if isinstance(data.get("restore"), dict) else None,
            previous_profile=previous if isinstance(previous, str) else None,
            fixed_profile=restart_profile(self.entry.options, self.area_id),
            known_profiles=set(self.profiles),
            reload=reload,
        )
        self._dispatch(
            Startup(
                previous_profile_id=plan.report_disarmed,
                test_mode=bool(data.get("test_mode", False)),
            )
        )
        self._refresh_sensors()
        if plan.kind is RestartKind.RESTORE:
            self._restore(plan)
        elif plan.kind is RestartKind.ARM and plan.profile_id is not None:
            self._schedule_restart_arm(plan.profile_id)
        # Eigene Sirenen, die vor dem Neustart an waren, nach dem Hochfahren ausschalten
        hidden = data.get("code_entities_hidden")
        if isinstance(hidden, list):
            self.code_entities_hidden = [h for h in hidden if isinstance(h, str)]
        guest = data.get("guest_until")
        if isinstance(guest, (int, float)) and (
            guest == GUEST_UNTIL_OFF or guest > dt_util.utcnow().timestamp()
        ):
            self.guest_until = float(guest)
            self._schedule_guest_end()
        stored_used = data.get("last_used")
        if isinstance(stored_used, dict):
            self.last_used = {
                str(k): float(v) for k, v in stored_used.items() if isinstance(v, (int, float))
            }
        if self.sirens.restore(data.get("sirens")):
            self._unsub_siren_check = async_at_started(self.hass, self._stop_restored_sirens)
        # Sofort speichern, damit ein erneuter Absturz nicht doppelt meldet.
        await self._store.async_save(self._storage_data())
        self._infra_faulty = self.faulty_infrastructure()
        self.automation.start()
        self.exit.start()
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

    # --- Verhalten nach Neustart -----------------------------------------------

    @callback
    def _restore(self, plan: RestartPlan) -> None:
        """Zustand von vor dem Neustart wiederherstellen (ohne Prüfung, ohne Ausgangszeit)."""
        profile_id = plan.profile_id
        profile = self.profiles.get(profile_id) if profile_id else None
        if profile_id is None or profile is None:
            return
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
        self.single_sensors = sensors
        self.armed_sensors = sensors | engine.watched()
        self._engine = engine
        self._exit_doors = frozenset()
        self.changed_by = tr(self.lang, "restart_actor")
        known = self.armed_sensors
        effects = self._dispatch(
            RestoreRequested(
                profile=profile,
                bypassed=plan.bypassed & known,
                bypassed_until_closed=plan.bypassed_until_closed & known,
                accepted_unavailable=plan.accepted_unavailable & known,
                entry_delay=plan.entry_delay,
                trigger_sensor=plan.trigger_sensor,
            )
        )
        if any(isinstance(e, Rejected) for e in effects):
            return
        self.automation.auto_armed_by = plan.auto_armed_by
        # Melder, die jetzt schon offen sind, aber nicht überbrückt waren: bis zum Schließen
        # überbrücken (ob sie vorher offen waren oder während des Neustarts geöffnet wurden,
        # lässt sich nicht unterscheiden) – gemeldet am Ende der Startphase.
        bypassed = self.ctx.bypassed | self.ctx.bypassed_until_closed
        open_now = frozenset(
            e
            for e in self.armed_sensors - bypassed
            if self._effective_state(e) == "on" and not self.is_vibration(e)
        )
        if open_now:
            self._dispatch(BypassUntilClosed(sensors=open_now))
            self._startup_open |= open_now
        self._grace_until = time.monotonic() + STARTUP_GRACE
        resume = plan.alarm_in_reaction and continue_alarm(self.entry.options)
        self._send_restored(profile_id, plan, resume=resume)
        self._unsub_grace = async_at_started(self.hass, self._start_grace_timer)
        if resume:
            sensor = plan.trigger_sensor

            @callback
            def _resume(_hass: HomeAssistant) -> None:
                self._resume_alarm(sensor)

            self._unsub_resume = async_at_started(self.hass, _resume)

    @callback
    def _resume_alarm(self, sensor: str | None) -> None:
        """Alarm von vor dem Neustart erneut auslösen (Einstellung "Laufenden Alarm
        fortsetzen"). Wie ein neuer Alarm: Reaktion des aktiven Profils, Sirenen nur über den
        Guard (Brandsperre, Testmodus, Freigabe)."""
        self._unsub_resume = None
        if self.ctx.state is not AlarmState.ARMED:
            return  # inzwischen unscharf oder schon ein neuer Alarm
        _LOGGER.warning("Alarm von vor dem Neustart wird fortgesetzt")
        self._dispatch(
            AlwaysActiveTriggered(
                sensor_key=sensor or "restart", profile=always_runtime(self.always)
            )
        )

    @callback
    def _start_grace_timer(self, _hass: HomeAssistant) -> None:
        self._grace_until = time.monotonic() + STARTUP_GRACE
        self._unsub_grace = async_call_later(self.hass, STARTUP_GRACE, self._grace_ended)

    @callback
    def _grace_ended(self, _now: Any = None) -> None:
        """Ende der Startphase: Melder melden, die noch fehlen oder offen vorgefunden wurden."""
        self._grace_until = None
        self._unsub_grace = None
        if self.ctx.state is AlarmState.DISARMED:
            self._startup_open = frozenset()
            return
        for entity_id in sorted(self.armed_sensors):
            if self._effective_state(entity_id) in (None, *UNAVAILABLE_STATES):
                self._on_sensor_lost(entity_id)
        still_open = frozenset(e for e in self._startup_open if e in self.ctx.bypassed_until_closed)
        self._startup_open = frozenset()
        if still_open:
            names = ", ".join(sorted(display_name(self.hass, e) for e in still_open))
            title = tr(self.lang, "restored_open_title")
            message = tr(self.lang, "restored_open", sensors=names)
            self.notifier.send_system(title, message)
            persistent_notification.async_create(
                self.hass, message, title=title, notification_id=f"{NOTIFICATION_RESTART}_open"
            )

    def _in_startup_grace(self) -> bool:
        return self._grace_until is not None and time.monotonic() < self._grace_until

    def _send_restored(self, profile_id: str, plan: RestartPlan, *, resume: bool) -> None:
        name = self.profile_name(profile_id)
        message = tr(self.lang, "restored", profile=name)
        if plan.entry_delay:
            message += tr(self.lang, "restored_entry")
        title = tr(self.lang, "restored_title")
        if plan.alarm_was_active:
            sensor = display_name(self.hass, plan.trigger_sensor) if plan.trigger_sensor else "-"
            message += tr(
                self.lang, "restored_alarm_resumed" if resume else "restored_alarm", sensor=sensor
            )
            # Wie ein Alarm an die Alarm-Empfänger (durchbricht "Nicht stören"), nicht nur als
            # System-Nachricht – ein Alarm in der Nacht soll nicht im Neustart untergehen.
            # Beim Fortsetzen meldet der neue Alarm selbst; hier nur der Hinweis.
            if not resume:
                self.notifier.notify(
                    NotifyEvent.ALARM,
                    tr(self.lang, "restored_alarm_title"),
                    message,
                    profile_targets=parse_reaction(self.entry.options, profile_id).notify,
                    values={"melder": sensor, "profil": name, "regel": ""},
                    test_mode=self.ctx.test_mode,
                    data=self._push_actions(),
                    speak=False,
                )
            else:
                self.notifier.send_system(title, message)
        else:
            self.notifier.send_system(title, message)
        persistent_notification.async_create(
            self.hass, message, title=title, notification_id=NOTIFICATION_RESTART
        )
        self.fire_event(
            {
                "type": "RestoredAfterRestart",
                "area": self.area_id,
                "profile_id": profile_id,
                "entry_delay": plan.entry_delay,
                "alarm_was_active": plan.alarm_was_active,
            },
        )

    @property
    def event_area(self) -> dict[str, Any]:
        """Bereich für jedes hauswacht_event (Feld ``area`` und ``area_name``)."""
        return {"area": self.area_id, "area_name": self.area_name}

    def all_areas_event(self) -> dict[str, Any]:
        """Bereich für Ereignisse der ganzen Anlage (Funknetz, Sirenentest, Bedienteile für
        alle Bereiche)."""
        return {"area": EVENT_AREA_ALL, "area_name": tr(self.lang, "event_all_areas")}

    @callback
    def fire_event(self, data: Mapping[str, Any]) -> None:
        """hauswacht_event auslösen – immer mit Bereich. Ein ``area`` in ``data`` hat Vorrang."""
        payload = {**self.event_area, **data}
        key = payload.get("sensor_key")
        if isinstance(key, str) and key in self.tilt_sources and "position" not in payload:
            payload["position"] = POSITION_NAMES.get(self._raw(key), self._raw(key))
        self.hass.bus.async_fire(EVENT_HAUSWACHT, payload)

    @callback
    def note_used(self, key: str) -> None:
        """Karte bzw. PIN hat gerade erfolgreich geschaltet (für "zuletzt benutzt")."""
        self.last_used[key] = dt_util.utcnow().timestamp()
        self._save_soon()

    async def async_save_now(self) -> None:
        await self._store.async_save(self._storage_data())

    @callback
    def _save_soon(self) -> None:
        self._store.async_delay_save(self._storage_data, 0)

    @callback
    def _stop_restored_sirens(self, _hass: HomeAssistant) -> None:
        """Nach dem Hochfahren: Sirenen ausschalten, die Hauswacht vor dem Neustart eingeschaltet
        hatte (z. B. Schalter ohne eigene Laufzeit) – nach der Startphase noch einmal, falls eine
        Sirene erst dann wieder erreichbar ist."""
        decision = self.sirens.stop_restored(test_mode=self.ctx.test_mode)
        sent = [c.entity_id for c in decision.commands]
        held = [b.device_key for b in decision.blocked if b.reason is BlockReason.FIRE_LOCK]
        if sent:
            names = ", ".join(display_name(self.hass, e) for e in sent)
            self.notifier.send_system(
                tr(self.lang, "sirens_restart_off_title"),
                tr(self.lang, "sirens_restart_off", sirens=names),
            )
        if held:
            names = ", ".join(display_name(self.hass, e) for e in held)
            self.notifier.send_system(
                tr(self.lang, "sirens_restart_off_title"),
                tr(self.lang, "sirens_restart_fire", sirens=names),
            )

        @callback
        def _again(_now: Any) -> None:
            self._unsub_siren_check = None
            self.sirens.stop_restored(test_mode=self.ctx.test_mode, only_on=True)

        self._unsub_siren_check = async_call_later(self.hass, STARTUP_GRACE, _again)

    @callback
    def _schedule_restart_arm(self, profile_id: str) -> None:
        """Einstellung "scharf": normal scharf schalten, kurz nachdem alles hochgefahren ist."""

        @callback
        def _later(_hass: HomeAssistant) -> None:
            self._unsub_restart_arm = async_call_later(self.hass, ARM_AFTER_START, _arm)

        @callback
        def _arm(_now: Any) -> None:
            self._unsub_restart_arm = None
            self.automation.auto_arm(profile_id, REASON_RESTART)

        # Läuft Home Assistant schon, ruft async_at_started _later sofort auf – dann steht der
        # Timer bereits in _unsub_restart_arm und darf nicht überschrieben werden.
        waiting = async_at_started(self.hass, _later)
        if self._unsub_restart_arm is None:
            self._unsub_restart_arm = waiting

    @callback
    def async_stop(self) -> None:
        """Beim Entladen: Timer und Abos stoppen. Der gespeicherte Zustand bleibt erhalten."""
        if self._unsub_grace is not None:
            self._unsub_grace()
            self._unsub_grace = None
        if self._unsub_restart_arm is not None:
            self._unsub_restart_arm()
            self._unsub_restart_arm = None
        if self._unsub_siren_check is not None:
            self._unsub_siren_check()
            self._unsub_siren_check = None
        if self._unsub_resume is not None:
            self._unsub_resume()
            self._unsub_resume = None
        if self._unsub_guest is not None:
            self._unsub_guest()
            self._unsub_guest = None
        self._cancel_timer()
        self._cancel_settle()
        self._cancel_speech_repeat()
        self._cancel_lost_timers()
        self._passage_reset()
        self._reset_rules()
        self.automation.stop()
        self.exit.stop()
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
        for unsub in (self._unsub_states, self._unsub_registry, self._unsub_reported):
            if unsub is not None:
                unsub()
        self._unsub_states = self._unsub_registry = self._unsub_reported = None
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
                readiness=self.readiness_for(
                    self.single_sensors - self._exit_doors,
                    tilt_allowed=self.tilt_allowed(profile_id),
                ),
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
        return identity_label(identity, self.lang)

    def check_allowed(self, users: tuple[User, ...], action: Action) -> None:
        """Darf mindestens einer dieser Benutzer die Aktion in diesem Bereich?"""
        if not self.permits(users, action):
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="action_not_allowed",
                translation_placeholders={"user": users_label(users, self.lang)},
            )

    async def async_identify(
        self, code: str | None, action: Action, source: str | None = None
    ) -> Identity:
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
            self.main.note_used(f"card:{normalize_tag(code)}")
            return Identity(
                kind="card", users=card.users, credential=tag_credential(code, card.users)
            )
        # PBKDF2 ist absichtlich langsam: im Hintergrund, damit Home Assistant nicht hängt
        match = await self.hass.async_add_executor_job(match_pin, code, self.users, timestamp)
        if match.duress:
            self.main._code_guard = register_success(self.main._code_guard)
            for user in match.duress:
                self.main.note_used(f"pin:{user.user_id}")
            self._send_duress_alert(users_label(match.duress, self.lang), action)
            return Identity(kind="pin", users=match.duress, duress=True)
        if match.users:
            self.main._code_guard = register_success(self.main._code_guard)
            for user in match.users:
                self.main.note_used(f"pin:{user.user_id}")
            return Identity(kind="pin", users=match.users)
        blocked = match.blocked + card.blocked
        if blocked:
            self.notifier.send_system(
                tr(self.lang, "blocked_credential_title"),
                tr(self.lang, "blocked_credential", who=users_label(blocked, self.lang)),
            )
        disabled = disabled_tag(code, self.users)
        if disabled is not None:
            owner, card_name = disabled
            self.notifier.send_system(
                tr(self.lang, "card_disabled_title"),
                tr(
                    self.lang,
                    "card_disabled",
                    card=card_name or normalize_tag(code),
                    who=owner.name,
                    where=source or "–",
                ),
            )
        if looks_like_card(code) and not blocked and disabled is None:
            # Unbekannte Karte (z. B. zum Anlernen): kann kein PIN sein und ist nicht zu erraten,
            # zählt daher nicht als Fehleingabe.
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="invalid_code")
        result = register_failure(self.main._code_guard, now)
        self.main._code_guard = result.state
        self.main._notify()
        failures = result.state.failures
        self.fire_event(
            {"type": "InvalidCode", "failures": failures, "lock_seconds": result.lock_seconds},
        )
        if result.warn:
            # Gleicher tag: jede neue Warnung ersetzt die vorige auf dem Handy
            sent = self.notifier.send_system(
                *invalid_code_message(failures, result.lock_seconds, self.lang),
                data={"tag": PUSH_CODE_TAG},
            )
            self.main._code_pushed.update(sent)
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
        self.fire_event(
            {"type": "CodeLockReset", "by": by, "failures": failures, **self.all_areas_event()}
        )
        # Wer zurückgesetzt hat, steht im Logbuch – im Log nie ein Name (ADR 0020)
        _LOGGER.info("Falscheingaben zurückgesetzt (%s Fehlversuche)", failures)
        if self.main._code_pushed:
            self.notifier.clear(self.main._code_pushed, PUSH_CODE_TAG)
            self.main._code_pushed.clear()
        for area in self.main.areas.values():
            area._notify()

    def permits(self, users: tuple[User, ...], action: Action) -> bool:
        """Darf mindestens einer dieser Benutzer die Aktion in diesem Bereich?"""
        return allowed_in(users, action, self.area_id)

    @property
    def area_name(self) -> str:
        return parse_areas(self.entry.options)[self.area_id].name

    async def async_user_label(self, user_id: str | None) -> str | None:
        """Name für Logbuch und Nachricht: zugeordneter Benutzer, sonst Home-Assistant-Konto."""
        linked = find_by_ha_user(self.users, user_id)
        if linked is not None:
            return linked.name
        user = await self.hass.auth.async_get_user(user_id) if user_id else None
        return user.name if user is not None else None

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
        missing = people_without_pin(self.users, ignore=[MASTER_USER_ID])
        # Mit Master-PIN können sie trotzdem unscharf schalten – nur eben mit dem Master-PIN
        master = any(u.user_id == MASTER_USER_ID and u.pin is not None for u in self.users)
        if missing:
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                ISSUE_PIN_COVERAGE,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=ISSUE_PIN_MASTER_ONLY if master else ISSUE_PIN_COVERAGE,
                translation_placeholders={
                    "people": ", ".join(missing),
                    "buttons": tr(self.lang, "on" if self.buttons_without_pin else "off"),
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
                Action.PASSAGE: "duress_passage",
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
        actions = [
            {
                "action": f"{PUSH_ACTION_PREFIX}{self._session}",
                "title": title,
                # iOS: nur mit entsperrtem Gerät (Face ID / Code)
                "authenticationRequired": True,
            }
        ]
        if self.ctx.state is AlarmState.PENDING and self.passage_ready:
            # Durchgang (ADR 0013): reinlassen statt unscharf – das Profil bleibt scharf
            actions.append(
                {
                    "action": f"{PUSH_PASSAGE_PREFIX}{self._session}",
                    "title": tr(self.lang, "btn_passage"),
                    "authenticationRequired": True,
                }
            )
        return {"tag": PUSH_TAG, "actions": actions}

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
        # Ausgangserkennung (ADR 0014): stille Wartezeit statt Eingangsverzögerung?
        if self.exit.begin() is not None:
            self._send_exit_push()
            return
        sensor = self.ctx.trigger_sensor or ""
        seconds, _near = self._entry_seconds(self.ctx.profile.entry_delay)
        self._send_alarm_push(
            tr(self.lang, "entry_title"),
            tr(
                self.lang,
                "entry",
                sensor=display_name(self.hass, sensor),
                seconds=seconds,
                profile=self.profile_name(self.ctx.profile.profile_id),
            ),
            {
                "melder": display_name(self.hass, sensor),
                "sekunden": seconds,
                "profil": self.profile_name(self.ctx.profile.profile_id),
            },
        )

    # --- Durchgang (ADR 0013) ---------------------------------------------------

    def passage_config(self) -> PassageConfig:
        """Durchgang-Einstellungen des scharfen Profils (unscharf: aus)."""
        profile = self.ctx.profile
        return parse_passage(self.entry.options, profile.profile_id if profile else None)

    @property
    def passage_ready(self) -> bool:
        """Durchgang gerade möglich? (Profil erlaubt ihn; scharf oder Eingangsverzögerung)"""
        return self.ctx.state in (AlarmState.ARMED, AlarmState.PENDING) and (
            self.passage_config().enabled
        )

    @callback
    def passage(self, changed_by: str | None, *, by_return: bool = False) -> Direction:
        """Durchgang öffnen – in der Eingangsverzögerung reinkommen, sonst rausgehen.

        Der Ausweis ist schon geprüft (Keypad, Aktion). Nicht möglich -> ServiceValidationError.
        ``by_return``: „Bei Rückkehr: reinlassen“ (ADR 0015) – gilt auch, wenn der Durchgang für
        Keypad und Co. nicht eingeschaltet ist; die Einstellungen (Weg, Nachlauf) gelten trotzdem.
        """
        ready = self.passage_ready or (
            by_return and self.ctx.state in (AlarmState.ARMED, AlarmState.PENDING)
        )
        if not ready:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="passage_not_possible"
            )
        config = self.passage_config()
        by = changed_by or ""
        if self.ctx.state is AlarmState.PENDING:
            self._passage_in(config, by, self.ctx.trigger_sensor)
            return Direction.IN
        self._passage_out_start(config, by)
        return Direction.OUT

    def _active(self, entity_id: str) -> bool:
        """Gerade offen bzw. in Bewegung?"""
        return self._effective_state(entity_id) not in (None, "off", *UNAVAILABLE_STATES)

    def _passage_in(self, config: PassageConfig, by: str, door: str | None) -> None:
        if door is not None and not self._active(door):
            door = None  # schon wieder zu: nichts zu überbrücken
        path = path_sensors(config, self.armed_sensors, self.ctx.bypassed)
        self.changed_by = by or self.changed_by
        _LOGGER.warning("Durchgang reinkommen (Tür %s)", door)
        self._dispatch(PassageIn(door=door, path=path, by=by))
        if door is not None:
            self._passage_in_doors[door] = path
            self._passage_later(
                f"guard:{door}", config.duration * 60, lambda: self._passage_door_guard(door)
            )
        elif path:
            self._passage_later(
                "path:-", config.path_after, lambda: self._passage_end_sensors(path)
            )
        door_name = display_name(self.hass, door) if door else "–"
        message = tr(self.lang, "passage_in", who=by, door=door_name, profile=self._profile_label())
        sent = self._passage_notify(message, {"wer": by, "melder": door_name}, tag=PUSH_TAG)
        # Ersetzt die Nachricht zur Eingangsverzögerung (gleicher tag), sonst wegräumen
        if stale := self._pushed_targets - set(sent):
            self.notifier.clear(stale, PUSH_TAG)
        self._pushed_targets = set(sent)
        self._notify()  # Anzeige erst jetzt vollständig (Tür eingetragen)

    def _passage_out_start(self, config: PassageConfig, by: str) -> None:
        doors = out_candidates(self.entry_doors(), self.ctx.bypassed, self.armed_sensors)
        path = path_sensors(config, self.armed_sensors, self.ctx.bypassed)
        if not doors and not path:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="passage_no_doors"
            )
        self._passage_out_end(warn=False)  # ein neuer Ausgang ersetzt einen laufenden
        _LOGGER.warning("Durchgang rausgehen (%s Min.)", config.duration)
        self.changed_by = by or self.changed_by
        self._dispatch(
            PassageOut(doors=doors, path=path, first_only=config.out_doors is OutDoors.FIRST, by=by)
        )
        self._passage_out = PassageOutRun(
            until=dt_util.utcnow().timestamp() + config.duration * 60,
            by=by,
            end=config.out_end,
            sensors=set(path),
        )
        self._passage_later("out", config.duration * 60, self._passage_out_end)
        message = tr(
            self.lang,
            "passage_out",
            who=by,
            minutes=config.duration,
            profile=self._profile_label(),
        )
        self._passage_notify(message, {"wer": by}, tag=PUSH_PASSAGE_TAG)
        self._notify()  # Anzeige erst jetzt vollständig (Ende eingetragen)

    def _passage_door_used(self, door: str) -> None:
        if self._passage_out is not None:
            self._passage_out.doors.add(door)
            self._passage_out.sensors.add(door)

    def _passage_door_closed(self, door: str) -> None:
        """Rausgehen: Tür wieder zu. Mit Ende "zurück": beim zweiten Mal (raus + zurück) aus."""
        run = self._passage_out
        if run is None or door not in run.doors:
            return
        run.closes += 1
        if run.end is OutEnd.RETURNED and run.closes >= CLOSES_FOR_RETURN:
            self._passage_out_end()

    @callback
    def _passage_out_end(self, warn: bool = True) -> None:
        """Rausgehen vorbei: Wegmelder und Tür wieder überwachen – offene erst, wenn sie zu
        sind (mit Warnung)."""
        run, self._passage_out = self._passage_out, None
        self._cancel_passage_timer("out")
        if run is None:
            return
        active = frozenset(s for s in run.sensors if self._active(s))
        self._dispatch(PassageEnd(sensors=frozenset(run.sensors), still_active=active))
        open_doors = sorted(active & run.doors)
        if warn and open_doors:
            self._passage_warn(open_doors)
        elif self._passage_pushed:
            self.notifier.clear(self._passage_pushed, PUSH_PASSAGE_TAG)
            self._passage_pushed.clear()

    @callback
    def _passage_door_guard(self, door: str) -> None:
        """Reinkommen: Tür nach der Durchgangszeit noch offen -> Warnung, Wegmelder enden."""
        self._passage_timers.pop(f"guard:{door}", None)
        if door not in self._passage_in_doors or self.ctx.state is AlarmState.DISARMED:
            return
        self._passage_end_sensors(self._passage_in_doors[door])
        self._passage_warn([door])

    @callback
    def _passage_end_sensors(self, sensors: frozenset[str]) -> None:
        if not sensors or self.ctx.state is AlarmState.DISARMED:
            return
        active = frozenset(s for s in sensors if self._active(s))
        self._dispatch(PassageEnd(sensors=sensors, still_active=active, close_doors=False))

    def _passage_restored(self, sensors: frozenset[str]) -> None:
        """Reinkommen: Tür wieder zu -> Wegmelder nach der Nachlaufzeit wieder überwachen."""
        for door in sensors & self._passage_in_doors.keys():
            path = self._passage_in_doors.pop(door)
            self._cancel_passage_timer(f"guard:{door}")
            if path:
                after = self.passage_config().path_after
                self._passage_later(
                    f"path:{door}", after, lambda p=path: self._passage_end_sensors(p)
                )

    def _passage_warn(self, doors: list[str]) -> None:
        names = ", ".join(display_name(self.hass, d) for d in doors)
        _LOGGER.warning("Nach dem Durchgang noch offen, nicht überwacht: %s", names)
        self.fire_event({"type": "PassageDoorOpen", "doors": doors})
        message = tr(self.lang, "passage_open", door=names, profile=self._profile_label())
        self._passage_notify(message, {"melder": names}, tag=PUSH_PASSAGE_TAG)

    def _passage_notify(self, message: str, values: dict[str, Any], *, tag: str) -> list[str]:
        sent = self.notifier.notify(
            NotifyEvent.PASSAGE,
            tr(self.lang, "passage_title"),
            message,
            values={"profil": self._profile_label(), **values},
            data={"tag": tag},
            test_mode=self.ctx.test_mode,
        )
        if tag == PUSH_PASSAGE_TAG:
            if stale := self._passage_pushed - set(sent):
                self.notifier.clear(stale, PUSH_PASSAGE_TAG)
            self._passage_pushed = set(sent)
        return sent

    def _profile_label(self) -> str:
        return self.profile_name(self.ctx.profile.profile_id) if self.ctx.profile else ""

    def _passage_later(self, key: str, seconds: float, action: Callable[[], None]) -> None:
        self._cancel_passage_timer(key)

        @callback
        def _fire(_now: Any) -> None:
            self._passage_timers.pop(key, None)
            action()

        self._passage_timers[key] = async_call_later(self.hass, seconds, _fire)

    def _cancel_passage_timer(self, key: str) -> None:
        if (timer := self._passage_timers.pop(key, None)) is not None:
            timer()

    def _passage_reset(self) -> None:
        """Unscharf oder Entladen: jeder Durchgang endet (Überbrückungen leert die Maschine)."""
        for timer in self._passage_timers.values():
            timer()
        self._passage_timers.clear()
        self._passage_in_doors.clear()
        self._passage_out = None
        if self._passage_pushed:
            self.notifier.clear(self._passage_pushed, PUSH_PASSAGE_TAG)
            self._passage_pushed.clear()

    def passage_info(self) -> dict[str, Any] | None:
        """Für Anzeige und Attribute: laufender Durchgang (sonst None)."""
        run = self._passage_out
        if run is None and not self._passage_in_doors and not self.ctx.passage:
            return None
        return {
            "direction": Direction.OUT.value if run is not None else Direction.IN.value,
            "until": dt_util.utc_from_timestamp(run.until).isoformat() if run else None,
            "by": run.by if run else self.changed_by,
            "doors": sorted(run.doors if run else self._passage_in_doors.keys()),
            "doors_allowed": sorted(self.ctx.passage_doors),
            "sensors": sorted(self.ctx.passage),
        }

    async def _on_push_action(self, event: HaEventAny[Any]) -> None:
        action = event.data.get("action")
        if not isinstance(action, str):
            return
        for prefix in (PUSH_ARM_FORCE_PREFIX, PUSH_ARM_RETRY_PREFIX, PUSH_ARM_NOW_PREFIX):
            if action.startswith(prefix):
                await self._on_push_arm(prefix, action[len(prefix) :], event.context.user_id)
                return
        if action.startswith((PUSH_EXIT_ALARM_PREFIX, PUSH_EXIT_LET_PREFIX)):
            await self._on_push_exit(action, event.context.user_id)
            return
        if action.startswith(PUSH_PASSAGE_PREFIX) and self.push_disarm:
            await self._on_push_passage(action, event.context.user_id)
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
        try:
            actor = await self.async_actor_for_user(user.id, self._action_for_disarm())
        except ServiceValidationError:
            self.notifier.send(
                targets,
                tr(self.lang, "push_denied_title"),
                tr(self.lang, "push_denied", who=user.name),
                test_mode=self.ctx.test_mode,
            )
            return
        _LOGGER.warning("Push-Knopf durch %s (Zustand %s)", actor, self.ctx.state.value)
        # Die Rückmeldung "unscharf geschaltet von …" verschickt _notify_state_change
        self._via_push = (actor, targets)
        try:
            self.disarm_trusted(changed_by=actor)
        finally:
            self._via_push = None

    async def _on_push_passage(self, action: str, user_id: str | None) -> None:
        """Push-Knopf "Reinlassen" (Durchgang, ADR 0013): bleibt scharf, Tür frei bis zu."""
        if self._session is None or action != f"{PUSH_PASSAGE_PREFIX}{self._session}":
            _LOGGER.warning("Veralteter Push-Knopf „Reinlassen“ ignoriert")
            return
        user = await self.hass.auth.async_get_user(user_id) if user_id else None
        if user is None or not user.is_active or user.system_generated:
            _LOGGER.warning("Push-Knopf ohne gültigen Home-Assistant-Benutzer ignoriert")
            return
        if self.ctx.state is not AlarmState.PENDING or not self.passage_ready:
            return  # Eingangsverzögerung vorbei (Alarm) oder schon unscharf
        try:
            actor = await self.async_actor_for_user(user.id, Action.PASSAGE)
        except ServiceValidationError:
            self.notifier.send(
                self._alarm_targets(),
                tr(self.lang, "push_denied_title"),
                tr(self.lang, "push_denied", who=user.name),
                test_mode=self.ctx.test_mode,
            )
            return
        _LOGGER.warning("Push-Knopf „Reinlassen“ durch %s", actor)
        self.passage(actor or user.name)

    async def _on_push_exit(self, action: str, user_id: str | None) -> None:
        """Push-Knöpfe der Ausgangserkennung (ADR 0014): „Alarm jetzt“ und „Durchlassen“."""
        if self._session is None or action not in (
            f"{PUSH_EXIT_ALARM_PREFIX}{self._session}",
            f"{PUSH_EXIT_LET_PREFIX}{self._session}",
        ):
            _LOGGER.warning("Veralteter Push-Knopf der Ausgangserkennung ignoriert")
            return
        if self.ctx.state is not AlarmState.PENDING:
            return  # Wartezeit schon vorbei
        if action.startswith(PUSH_EXIT_ALARM_PREFIX):
            # Alarm jetzt: jeder Empfänger darf auslösen – das macht die Anlage nur strenger
            _LOGGER.warning("Ausgangserkennung: Alarm jetzt per Push")
            self.exit_alarm_now()
            return
        user = await self.hass.auth.async_get_user(user_id) if user_id else None
        if user is None or not user.is_active or user.system_generated:
            _LOGGER.warning("Push-Knopf ohne gültigen Home-Assistant-Benutzer ignoriert")
            return
        try:
            actor = await self.async_actor_for_user(user.id, Action.PASSAGE)
        except ServiceValidationError:
            self.notifier.send(
                self._alarm_targets(),
                tr(self.lang, "push_denied_title"),
                tr(self.lang, "push_denied", who=user.name),
                test_mode=self.ctx.test_mode,
            )
            return
        _LOGGER.warning("Ausgangserkennung: Durchlassen per Push")
        door = self.exit.watch.door if self.exit.watch else self.ctx.trigger_sensor
        self.exit.end()
        self.exit_let_out(door, actor or user.name, None)

    @callback
    def exit_alarm_now(self) -> None:
        """„Alarm jetzt“: Wartezeit sofort beenden – wie eine abgelaufene Eingangsverzögerung."""
        if self.ctx.state is not AlarmState.PENDING or self._entry_token is None:
            return
        self.exit.end()
        self._cancel_timer()
        self._dispatch(self._timer_event(TimerKind.ENTRY_DELAY, self._entry_token))

    @callback
    def exit_let_out(self, door: str | None, who: str, person: str | None) -> None:
        """Jemand ist rausgegangen (oder durchgelassen): bleibt scharf, Tür frei bis zu."""
        if self.ctx.state is not AlarmState.PENDING:
            return
        if door is not None and not self._active(door):
            door = None  # schon wieder zu: nichts zu überbrücken
        self._dispatch(PassageIn(door=door, path=frozenset(), by=who))
        if door is not None:
            self._passage_in_doors[door] = frozenset()
            self._passage_later(
                f"guard:{door}",
                self.passage_config().duration * 60,
                lambda: self._passage_door_guard(door),
            )
        door_name = display_name(self.hass, door) if door else "–"
        key = "exit_left" if person is not None else "exit_let"
        self.fire_event(
            {
                "type": "ExitDetected" if person is not None else "ExitLetThrough",
                "profile_id": self.ctx.profile.profile_id if self.ctx.profile else None,
                "door": door,
                "person": person,
            }
        )
        sent = self.notifier.send_to_alarm_recipients(
            tr(self.lang, "exit_title"),
            tr(self.lang, key, who=who, door=door_name, profile=self._profile_label()),
            profile_targets=self._alarm_targets(),
            data={"tag": PUSH_TAG},
            test_mode=self.ctx.test_mode,
        )
        self._pushed_targets = set(sent)
        self._notify()

    @callback
    def _send_exit_push(self) -> None:
        """Sofort an alle Alarm-Empfänger: Tür offen – Alarm jetzt oder durchlassen?"""
        door = self.ctx.trigger_sensor or ""
        config = parse_exit(self.options, self.ctx.profile.profile_id if self.ctx.profile else None)
        actions = []
        if self._session is not None:
            actions.append(
                {
                    "action": f"{PUSH_EXIT_ALARM_PREFIX}{self._session}",
                    "title": tr(self.lang, "btn_exit_alarm"),
                }
            )
            if self.push_disarm:
                actions.append(
                    {
                        "action": f"{PUSH_EXIT_LET_PREFIX}{self._session}",
                        "title": tr(self.lang, "btn_exit_let"),
                        "authenticationRequired": True,
                    }
                )
        sent = self.notifier.send_to_alarm_recipients(
            tr(self.lang, "exit_title"),
            tr(
                self.lang,
                "exit_start",
                door=display_name(self.hass, door),
                profile=self._profile_label(),
                minutes=config.wait,
            ),
            profile_targets=self._alarm_targets(),
            data={"tag": PUSH_TAG, "actions": actions},
            test_mode=self.ctx.test_mode,
        )
        self._pushed_targets.update(sent)

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

    # --- Gastmodus ---------------------------------------------------------------

    @property
    def guest_active(self) -> bool:
        """Gastmodus an: Hauswacht schaltet diesen Bereich nicht automatisch scharf."""
        if self.guest_until is None:
            return False
        return self.guest_until == GUEST_UNTIL_OFF or self.guest_until > (
            dt_util.utcnow().timestamp()
        )

    @property
    def guest_ends_at(self) -> datetime | None:
        if not self.guest_active or self.guest_until in (None, GUEST_UNTIL_OFF):
            return None
        return dt_util.utc_from_timestamp(self.guest_until)

    @callback
    def set_guest_mode(
        self, enabled: bool, *, until: datetime | None = None, by: str | None = None
    ) -> None:
        """Gastmodus ein (bis ``until`` bzw. bis zum Ausschalten) oder aus."""
        if enabled and until is not None and until <= dt_util.utcnow():
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="guest_until_past"
            )
        was = self.guest_active
        self.guest_until = (
            (until.timestamp() if until is not None else GUEST_UNTIL_OFF) if enabled else None
        )
        self._schedule_guest_end()
        self._guest_changed(was, by=by)

    def _schedule_guest_end(self) -> None:
        if self._unsub_guest is not None:
            self._unsub_guest()
            self._unsub_guest = None
        ends = self.guest_ends_at
        if ends is None:
            return

        @callback
        def _end(_now: datetime) -> None:
            self._unsub_guest = None
            self.guest_until = None
            self._guest_changed(True, by=None)

        self._unsub_guest = async_track_point_in_utc_time(self.hass, _end, ends)

    def _guest_changed(self, was: bool, *, by: str | None) -> None:
        now = self.guest_active
        self._save_soon()
        self._notify()
        if self.main is not self:
            self.main._notify()
        if was == now and not now:
            return
        ends = self.guest_ends_at
        self.fire_event(
            {
                "type": "GuestMode",
                "area": self.area_id,
                "on": now,
                "until": ends.isoformat() if ends else None,
                "by": by,
            },
        )
        until = (
            dt_util.as_local(ends).strftime("%d.%m. %H:%M")
            if ends
            else tr(self.lang, "guest_until_off")
        )
        if now:
            text = tr(self.lang, "guest_on", area=self.area_name, until=until)
        else:
            text = tr(self.lang, "guest_off", area=self.area_name)
        if by:
            text += f" ({by})"
        self.notifier.notify(
            NotifyEvent.AUTOMATION, tr(self.lang, "guest_title"), text, test_mode=self.ctx.test_mode
        )

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
        if not self.ctx.test_mode and self._presence_sim:
            people = list(self._presence_sim)
            self._presence_sim.clear()  # Anwesenheit wieder echt
            for area in self.areas.values():
                for person in people:
                    area.automation.presence_simulated_changed(person, SIM_REAL)
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

    # --- Stellung (offen / zu / gekippt) -------------------------------------

    def read_position(self, entity_id: str, state: State | None) -> str | None:
        """Echte Stellung aus dem Home-Assistant-Zustand: on, off, tilted, unavailable …"""
        strength_source = self.vibration_sources.get(entity_id)
        if strength_source is not None:
            return vibration_position(strength_source, state.state if state else None)
        source = self.tilt_sources.get(entity_id)
        if source is not None:
            return tilt_position(
                source, state.state if state else None, state.attributes if state else None
            )
        return normalize(entity_id, state.state if state else None)

    def _raw(self, entity_id: str) -> str | None:
        """Stellung für Hauswacht: simuliert (Testmodus) oder echt – noch nicht bewertet."""
        simulated = self.simulated(entity_id)
        if simulated is not None:
            return simulated
        return self.read_position(entity_id, self.hass.states.get(entity_id))

    def tilt_allowed(self, profile_id: str | None = None) -> bool:
        """Erlaubt das Profil gekippte Fenster? Ohne Angabe: aktives bzw. ausgewähltes Profil."""
        pid = profile_id or self.selected_profile
        return bool(pid) and profile_behaviour(self.entry.options, pid).tilt_allowed

    def _judged(self, raw: str | None, tilt_allowed: bool | None = None) -> str | None:
        allowed = self.tilt_allowed() if tilt_allowed is None else tilt_allowed
        return judge(raw, tilt_allowed=allowed)

    def tilted_sensors(self, entity_ids: frozenset[str] | None = None) -> frozenset[str]:
        """Melder, die gerade gekippt sind."""
        ids = self.candidates if entity_ids is None else entity_ids
        return frozenset(e for e in ids if e in self.tilt_sources and self._raw(e) == TILTED)

    def snapshots(
        self, entity_ids: frozenset[str], *, tilt_allowed: bool | None = None
    ) -> dict[str, SensorSnapshot]:
        result: dict[str, SensorSnapshot] = {}
        now = dt_util.utcnow().timestamp()
        allowed = self.tilt_allowed() if tilt_allowed is None else tilt_allowed
        for entity_id in entity_ids:
            state = self.hass.states.get(entity_id)
            if (simulated := self.simulated(entity_id)) is not None:
                result[entity_id] = SensorSnapshot(
                    entity_id=entity_id,
                    state=judge(simulated, tilt_allowed=allowed),
                    device_class=state.attributes.get("device_class") if state else None,
                    last_reported=now,
                    last_seen=None,
                )
                continue
            result[entity_id] = SensorSnapshot(
                entity_id=entity_id,
                state=judge(self.read_position(entity_id, state), tilt_allowed=allowed),
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

    def readiness_for(
        self, entity_ids: frozenset[str], *, tilt_allowed: bool | None = None
    ) -> Readiness:
        """Bereitschaft der Sensoren. Gestörte Infrastruktur zählt als "nicht verfügbar"."""
        readiness = evaluate_readiness(
            entity_ids,
            self.snapshots(entity_ids, tilt_allowed=tilt_allowed),
            now=dt_util.utcnow().timestamp(),
            stale_after=self.stale_after,
            stale_overrides=self.stale_overrides,
        )
        # Erschütterung ist ein Vorgang, kein offener Zustand: blockiert das Scharfschalten nie
        open_sensors = frozenset(e for e in readiness.open_sensors if not self.is_vibration(e))
        faulty = self.faulty_infrastructure()
        return Readiness(
            open_sensors=open_sensors,
            unavailable_sensors=readiness.unavailable_sensors | faulty,
        )

    def is_vibration(self, entity_id: str) -> bool:
        return self.type_of(entity_id) is SensorType.VIBRATION

    def vibration_rule_of(self, entity_id: str) -> VibrationRule:
        """Fehlalarmschutz aus der Meldergruppe des Melders (ohne Gruppe: 1 Meldung)."""
        for zone in self.zones.values():
            if entity_id in resolve_zone(zone, self._labels):
                return rule_for_zone_id(self.entry.options, zone.zone_id)
        return VibrationRule()

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
            stale_overrides=self.stale_overrides,
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
            self.fire_event(
                {
                    "type": "InfrastructureFault",
                    "indicator": entity_id,
                    "armed": armed,
                    **self.all_areas_event(),
                },
            )
        for entity_id in sorted(recovered):
            _LOGGER.info("Infrastruktur wieder verfügbar: %s", entity_id)
            self.fire_event(
                {
                    "type": "InfrastructureRecovered",
                    "indicator": entity_id,
                    "armed": armed,
                    **self.all_areas_event(),
                },
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
        self.fire_event({"type": "AlwaysActiveTriggered", "sensor_key": entity_id})
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
        self.fire_event({"type": "Panic", "control": name})
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
            self.fire_event({"type": "ArmedByClosingDoor"})
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
        if entity_id in self.ctx.passage:
            return  # Durchgang: Weg und Tür zählen auch für Regeln nicht
        if self.ctx.state not in (AlarmState.ARMED, AlarmState.PENDING, AlarmState.ALARM_HOLD):
            return
        now = dt_util.utcnow().timestamp()
        recorded = self._engine.record(entity_id, now)
        fired = [r for r in recorded if self._conditions_met(r)]
        for rule in recorded:
            if rule not in fired:
                _LOGGER.info("Regel %s erfüllt, Bedingungen aber nicht – kein Alarm", rule.name)
                self.fire_event(
                    {"type": "RuleConditionsNotMet", "rule": rule.rule_id, "sensor_key": entity_id},
                )
        if not fired:
            self.fire_event({"type": "RuleStep", "sensor_key": entity_id})
            self._update_partials(now)
            return
        # Bei mehreren erfüllten Regeln gilt das strengere Ergebnis
        rule = max(fired, key=lambda r: STRICTNESS[r.result])
        if rule.result is RuleResult.NOTIFY:
            self.fire_event(
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
        self.fire_event(
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
        self.fire_event(
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

    def _effective_state(self, entity_id: str) -> str | None:
        """Zustand für Hauswacht: simuliert (Testmodus) oder echt, vereinheitlicht."""
        return self._judged(self._raw(entity_id))

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
        real_state = self.read_position(entity_id, real)
        if value == TILTED and entity_id not in self.tilt_sources:
            raise ServiceValidationError(f"{entity_id} hat keine Kippstellung")
        old = self._simulated.get(entity_id, real_state)
        if value == SIMULATION_REAL:
            self._simulated.pop(entity_id, None)
            new = real_state
        else:
            self._simulated[entity_id] = value
            new = value
        self.fire_event(
            {"type": "SensorSimulated", "sensor_key": entity_id, "state": value},
        )
        device_class = real.attributes.get("device_class") if real else None
        for area in self.areas.values():
            if old != new and entity_id in area.candidates | area.armed_sensors:
                area._handle_sensor_change(entity_id, old, new, device_class)
            else:
                area._notify()
        if old == "off" and new == "on":
            # Simulierte Eingangstür zählt wie die echte: „Bei Rückkehr“, Beleg für „weg“,
            # Durchgang (ADR 0016) – sonst ließe sich das im Testmodus nicht ausprobieren
            for area in self.areas.values():
                area.automation.door_seen(entity_id)

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

    # --- Anwesenheit simulieren und anzeigen (ADR 0016) ---------------------

    def presence_simulated(self, person: str) -> str | None:
        """Simulierte Anwesenheit – nur im Testmodus wirksam."""
        if not self.main.ctx.test_mode:
            return None
        return self._presence_sim.get(person)

    def presence_persons(self) -> list[str]:
        """Personen aus den Profil-Automatiken aller Bereiche."""
        return list(
            dict.fromkeys(
                p for a in self.main.areas.values() for p in a.automation.presence_persons
            )
        )

    @callback
    def simulate_presence(self, person: str, value: str) -> None:
        """Anwesenheit einer Person für Hauswacht simulieren (Testmodus) oder mit "real"
        zurücksetzen. Die Person in Home Assistant bleibt unverändert; andere Automationen und
        die Heimkehr-Beobachtung merken nichts davon."""
        if self.main is not self:
            self.main.simulate_presence(person, value)
            return
        if value not in SIM_VALUES:
            raise ServiceValidationError(f"Unbekannter Zustand: {value}")
        if not self.ctx.test_mode:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="simulation_requires_test_mode"
            )
        if person not in self.presence_persons():
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="unknown_presence_person",
                translation_placeholders={"person": person},
            )
        if value == SIM_REAL:
            self._presence_sim.pop(person, None)
        else:
            self._presence_sim[person] = value
        self.fire_event({"type": "PresenceSimulated", "person": person, "state": value})
        for area in self.areas.values():
            area.automation.presence_simulated_changed(person, value)
            area._notify()
        if self not in self.areas.values():
            self._notify()

    @callback
    def skip_wait(self) -> None:
        """Testmodus: laufende „alle weg“-Wartezeiten sofort beenden."""
        if self.main is not self:
            self.main.skip_wait()
            return
        if not self.ctx.test_mode:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="simulation_requires_test_mode"
            )
        for area in self.areas.values():
            area.automation.skip_wait()
            area._notify()
        if self not in self.areas.values():
            self._notify()

    def presence_overview(self) -> dict[str, Any]:
        """Anwesenheit aller Personen mit Grund und je Profil, was „alle weg“ macht."""
        persons: dict[str, dict[str, Any]] = {}
        profiles: list[dict[str, Any]] = []
        for area in self.main.areas.values():
            report = area.automation.presence_report()
            for person, row in report["persons"].items():
                persons.setdefault(person, row)
            for row in report["profiles"]:
                profiles.append(
                    {
                        **row,
                        "name": area.profile_name(row["profile"]),
                        "other_armed": (
                            area.profile_name(row["other_armed"]) if row["other_armed"] else None
                        ),
                        "waiting": [display_name(self.hass, p) for p in row["waiting"]],
                    }
                )
        for person, row in persons.items():
            row["name"] = display_name(self.hass, person)
            by = row["reason"].get("by")
            if by:
                row["reason"] = {**row["reason"], "by": [display_name(self.hass, e) for e in by]}
        return {"persons": persons, "profiles": profiles, "test_mode": self.main.ctx.test_mode}

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
                    "real": self.read_position(entity_id, state),
                    "tilt": entity_id in self.tilt_sources,
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
        for area in self.areas.values():
            area.automation.door_seen(entity_id)  # kurz auslösen = Tür ging auf

    @callback
    def _simulate_trigger(self, entity_id: str) -> None:
        state = self.hass.states.get(entity_id)
        device_class = state.attributes.get("device_class") if state else None
        role = sensor_role(entity_id, device_class, self.role_overrides)
        self.fire_event({"type": "SensorSimulated", "sensor_key": entity_id})
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
        self.candidates = frozenset(
            e
            for e in configured
            if domain_of(e) in MONITORED_DOMAINS
            or e in self.tilt_sources
            or e in self.vibration_sources
        )
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
        self.automation.refresh_doors()
        if self.vibration_sources and self._unsub_reported is None:
            self._unsub_reported = self.hass.bus.async_listen(
                EVENT_STATE_REPORTED,
                self._on_vibration_reported,
                event_filter=self._is_vibration_report,
            )
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
        old_position = self.read_position(entity_id, old)
        new_position = self.read_position(entity_id, new)
        if (
            entity_id in self.vibration_sources
            and old_position == new_position == "on"
            and old is not None
            and new is not None
            and old.state != new.state
        ):
            old_position = "off"  # neue Zahl über der Schwelle = neue Erschütterung
        self._handle_sensor_change(entity_id, old_position, new_position, device_class)

    @callback
    def _handle_sensor_change(
        self,
        entity_id: str,
        old_state: str | None,
        new_state: str | None,
        device_class: str | None,
    ) -> None:
        """Zustandswechsel eines Sensors bewerten – echt oder simuliert.

        ``old_state``/``new_state`` sind Stellungen (on, off, tilted …); bewertet werden sie
        hier im aktiven Profil (gekippt erlaubt oder nicht).
        """
        role = sensor_role(entity_id, device_class, self.role_overrides)
        armed = self.ctx.state is not AlarmState.DISARMED
        if (
            armed
            and entity_id in self.ctx.bypassed
            and old_state == TILTED
            and new_state == "on"
            and self._bypass_position.get(entity_id) == TILTED
        ):
            # Gekippt überbrückt, jetzt ganz geöffnet: neuer Vorgang (ADR 0010)
            self._dispatch(BypassedSensorOpened(sensor_key=entity_id, role=role))
            return
        old_state, new_state = self._judged(old_state), self._judged(new_state)
        if (entity_id in self._lost_pushed or entity_id in self._lost_timers) and new_state not in (
            None,
            *UNAVAILABLE_STATES,
        ):
            self._on_sensor_back(entity_id)
        if self.ctx.state is AlarmState.ARMING and entity_id in self._exit_doors:
            self._on_exit_door(new_state)

        relevant = (
            (role is SensorRole.TAMPER_24H and self._tamper_mine(entity_id))
            or entity_id in self.always_sensors
            or (armed and entity_id in self.armed_sensors)
        )
        if _LOGGER.isEnabledFor(logging.DEBUG):
            _LOGGER.debug(
                "Bereich %s: Melder %s %s → %s (%s, %s)",
                self.area_id,
                entity_id,
                old_state,
                new_state,
                role.value,
                self._sensor_verdict(entity_id, armed, relevant, old_state, new_state),
            )
        if (
            armed
            and self._in_startup_grace()
            and entity_id in self.armed_sensors
            and new_state == "on"
            and (old_state is None or old_state in UNAVAILABLE_STATES)
            and role is not SensorRole.ENTRY
            and entity_id not in self.ctx.bypassed
            and not self.is_vibration(entity_id)
        ):
            # Nach dem Wiederherstellen erstmals gemeldet und offen: Fenster oder Bewegung
            # bis zum Schließen überbrücken statt nachts Sirenenalarm – Eingangstüren starten
            # dagegen die Eingangsverzögerung (z. B. wer gerade heimkam).
            self._dispatch(BypassUntilClosed(sensors=frozenset({entity_id})))
            self._startup_open |= {entity_id}
            self._notify()
            return
        if relevant and is_trigger(old_state, new_state):
            if self.is_vibration(entity_id) and not self._vibration_counts(entity_id):
                return
            self._sensor_triggered(entity_id, role)
            return
        if (
            armed
            and entity_id in self.armed_sensors
            and became_unavailable(old_state, new_state)
            and not self._in_startup_grace()  # beim Hochfahren normal; gemeldet wird danach
        ):
            self._on_sensor_lost(entity_id)
        if (
            self._passage_out is not None
            and entity_id in self._passage_out.doors
            and new_state == "off"
            and old_state not in (None, "off", *UNAVAILABLE_STATES)
        ):
            self._passage_door_closed(entity_id)
        if entity_id in self.ctx.bypassed_until_closed and new_state == "off":
            self._dispatch(SensorClosed(sensor_key=entity_id))
            return
        self._notify()

    def _sensor_verdict(
        self,
        entity_id: str,
        armed: bool,
        relevant: bool,
        old_state: str | None,
        new_state: str | None,
    ) -> str:
        """Kurzer Grund für das Debug-Log: Warum zählt dieser Wechsel – oder nicht?"""
        if entity_id in self.ctx.bypassed or entity_id in self.ctx.bypassed_until_closed:
            return "überbrückt"
        if not relevant:
            if not armed:
                return "unscharf, nicht immer aktiv"
            profile = self.ctx.profile.profile_id if self.ctx.profile else "-"
            return f"im Profil {profile} nicht überwacht"
        if not is_trigger(old_state, new_state):
            return "überwacht, aber kein auslösender Wechsel"
        return "überwacht, löst aus"

    @callback
    def _vibration_counts(self, entity_id: str) -> bool:
        """Fehlalarmschutz: True, wenn genug Erschütterungen im Zeitfenster zusammenkamen."""
        rule = self.vibration_rule_of(entity_id)
        reached, count = self._vibration.record(entity_id, time.monotonic(), rule)
        if not reached:
            _LOGGER.info(
                "Erschütterung %s: %s von %s in %s s", entity_id, count, rule.count, rule.window
            )
            self.fire_event(
                {
                    "type": "VibrationCounted",
                    "sensor_key": entity_id,
                    "count": count,
                    "needed": rule.count,
                    "window": rule.window,
                }
            )
            self._notify()
        return reached

    @callback
    def _is_vibration_report(self, event_data: Mapping[str, Any]) -> bool:
        """Nur Meldungen der Erschütterungsstärken (Home Assistant verlangt den Filter)."""
        return event_data.get("entity_id") in self.vibration_sources

    @callback
    def _on_vibration_reported(self, event: HaEventAny[Any]) -> None:
        """Erschütterungsstärke: auch eine gleich gebliebene Zahl über der Schwelle ist eine
        neue Meldung (Home Assistant meldet sie als ``state_reported``)."""
        entity_id = event.data.get("entity_id")
        if entity_id not in self.vibration_sources or self.simulated(entity_id) is not None:
            return
        if entity_id not in self.candidates and entity_id not in self.armed_sensors:
            return
        new = event.data.get("new_state")
        if self.read_position(entity_id, new) != "on":
            return
        self._handle_sensor_change(
            entity_id, "off", "on", new.attributes.get("device_class") if new else None
        )

    @callback
    def _on_sensor_lost(self, entity_id: str) -> None:
        _LOGGER.warning("Überwachter Sensor nicht mehr verfügbar: %s", entity_id)
        self.fire_event({"type": "SensorUnavailable", "sensor_key": entity_id})
        title, message = sensor_lost_message(display_name(self.hass, entity_id), self.lang)
        # Push erst nach kurzer Wartezeit: fällt gleichzeitig z. B. Zigbee2MQTT aus, meldet
        # das die Störungsnachricht – nicht zusätzlich jeder einzelne Melder
        if entity_id not in self._lost_pushed and entity_id not in self._lost_timers:

            @callback
            def _send(_now: Any) -> None:
                self._lost_timers.pop(entity_id, None)
                self._push_sensor_lost(entity_id, title, message)

            self._lost_timers[entity_id] = async_call_later(self.hass, LOST_SETTLE_SECONDS, _send)
        persistent_notification.async_create(
            self.hass,
            message + tr(self.lang, "sensor_lost_armed"),
            title=title,
            notification_id=f"{NOTIFICATION_ALARM}_{entity_id}",
        )

    def _push_sensor_lost(self, entity_id: str, title: str, message: str) -> None:
        if self._effective_state(entity_id) not in (None, *UNAVAILABLE_STATES):
            return  # schon wieder da
        if self.main.faulty_infrastructure():
            return  # die Störungsnachricht nennt die Ursache
        sent = self.notifier.notify(
            NotifyEvent.FAULT,
            title,
            message,
            data={"tag": lost_tag(entity_id)},
            test_mode=self.ctx.test_mode,
        )
        if sent:
            self._lost_pushed[entity_id] = set(sent)

    def _on_sensor_back(self, entity_id: str) -> None:
        """Ausgefallener Melder meldet sich wieder: seine Ausfall-Nachricht verschwindet."""
        if (timer := self._lost_timers.pop(entity_id, None)) is not None:
            timer()
        if (targets := self._lost_pushed.pop(entity_id, None)) is not None:
            self.notifier.clear(targets, lost_tag(entity_id))
        persistent_notification.async_dismiss(self.hass, f"{NOTIFICATION_ALARM}_{entity_id}")

    def _cancel_lost_timers(self) -> None:
        for timer in self._lost_timers.values():
            timer()
        self._lost_timers.clear()

    def _rejection_placeholders(
        self, open_sensors: frozenset[str], unavailable: frozenset[str]
    ) -> dict[str, str]:
        """Klartext für Meldungen: Namen mit Raum, gestörte Infrastruktur getrennt."""
        faulty = unavailable & self.main.infrastructure

        tilted = self.tilted_sensors(open_sensors)

        def names(ids: frozenset[str]) -> str:
            return (
                ", ".join(
                    sorted(
                        display_name(self.hass, e)
                        + (tr(self.lang, "tilted_suffix") if e in tilted else "")
                        for e in ids
                    )
                )
                or "-"
            )

        return {
            "open": names(open_sensors),
            "unavailable": names(unavailable - faulty),
            "faulty": names(faulty),
        }

    def _raise_for_rejection(self, effects: tuple[Effect, ...]) -> None:
        for effect in effects:
            if isinstance(effect, Rejected):
                raise ArmRefused(
                    open_sensors=self._blocker_names(
                        effect.open_sensors | effect.unavailable_sensors
                    ),
                    confirmable=False,
                    translation_domain=DOMAIN,
                    translation_key=f"rejected_{effect.reason}",
                    translation_placeholders=self._rejection_placeholders(
                        effect.open_sensors, effect.unavailable_sensors
                    ),
                )
            if isinstance(effect, ConfirmationRequired):
                raise ArmRefused(
                    open_sensors=self._blocker_names(
                        effect.open_sensors | effect.unavailable_sensors
                    ),
                    confirmable=True,
                    translation_domain=DOMAIN,
                    translation_key="confirmation_required",
                    translation_placeholders=self._rejection_placeholders(
                        effect.open_sensors, effect.unavailable_sensors
                    ),
                )

    def _blocker_names(self, entity_ids: frozenset[str]) -> tuple[str, ...]:
        """Melder, die das Scharfschalten verhindern – als Namen (für Keypads)."""
        return tuple(sorted(display_name(self.hass, e) for e in entity_ids))

    @callback
    def _dispatch(self, event: Event) -> tuple[Effect, ...]:
        old_ctx = self.ctx
        self.ctx, effects = step(self.ctx, event, time.monotonic())
        if _LOGGER.isEnabledFor(logging.DEBUG):
            # Eingang → Wirkungen (ADR 0020): ohne Namen, Codes und Nachrichtentexte
            _LOGGER.debug(
                "Bereich %s: %s → %s",
                self.area_id,
                describe(event),
                ", ".join(describe(e) for e in effects) or "keine Wirkung",
            )
        # Stellung beim Überbrücken merken (gekippt überbrückt -> ganz offen löst aus)
        for entity_id in self.ctx.bypassed - old_ctx.bypassed:
            if entity_id in self.tilt_sources:
                self._bypass_position[entity_id] = self._raw(entity_id)
        for entity_id in old_ctx.bypassed - self.ctx.bypassed:
            self._bypass_position.pop(entity_id, None)
        for effect in effects:
            self._apply(effect)
        if self.ctx.state is not AlarmState.ARMING:
            self._cancel_settle()
        if self.ctx.state is AlarmState.DISARMED:
            self._vibration.reset()
            self.sirens.reset()
            self._reset_rules()
            self._engine = RuleEngine()
            self._exit_doors = frozenset()
            self._passage_reset()
            self.automation.on_disarmed()
            if self.armed_sensors:
                self.armed_sensors = frozenset()
                self.single_sensors = frozenset()
                self._refresh_sensors()
        if (
            old_ctx.state,
            old_ctx.profile,
            old_ctx.test_mode,
            old_ctx.bypassed,
            old_ctx.bypassed_until_closed,
            old_ctx.trigger_sensor,
            old_ctx.passage,
        ) != (
            self.ctx.state,
            self.ctx.profile,
            self.ctx.test_mode,
            self.ctx.bypassed,
            self.ctx.bypassed_until_closed,
            self.ctx.trigger_sensor,
            self.ctx.passage,
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
            "restore": saved_state(
                profile_id=self.ctx.profile.profile_id if armed and self.ctx.profile else None,
                state=self.ctx.state.value,
                # Ein Durchgang endet beim Neustart (ADR 0013)
                bypassed=self.ctx.bypassed - self.ctx.passage,
                bypassed_until_closed=self.ctx.bypassed_until_closed,
                accepted_unavailable=self.ctx.accepted_unavailable,
                trigger_sensor=self.ctx.trigger_sensor,
                auto_armed_by=self.automation.auto_armed_by,
            ),
            "test_mode": self.ctx.test_mode,
            "sirens": self.sirens.snapshot(),
            "last_used": self.last_used,
            "guest_until": self.guest_until,
            "code_entities_hidden": self.code_entities_hidden,
            "selected_profile": self._selected_profile,
            "edit_profile": self._edit_profile,
        }

    @callback
    def _apply(self, effect: Effect) -> None:
        self.fire_event(effect_payload(effect))

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
                if effect.old is AlarmState.PENDING and effect.new is not AlarmState.PENDING:
                    self.exit.end()
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
                self._passage_restored(effect.sensors)
            case PassageDoorUsed():
                self._passage_door_used(effect.door)
            case PassageEnded():
                _LOGGER.info(
                    "Durchgang beendet: wieder überwacht %s, offen %s",
                    sorted(effect.restored),
                    sorted(effect.still_open),
                )
            case PassageGranted():
                pass
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

    def _arm_gaps(self) -> tuple[list[str], list[str]]:
        """Was beim Scharfschalten NICHT überwacht wird: (Zeilen für die Nachricht, offene Melder).

        - offene Melder, die überbrückt wurden ("trotzdem scharf" oder automatisch),
        - ausgefallene Melder, die in Kauf genommen wurden (wieder überwacht, sobald sie sich
          melden),
        - offene Melder, die nur in Auslöseregeln vorkommen (Regel erst nach Schließen).
        """
        lang = self.lang
        open_rules = {
            e: names for e, names in self.open_rule_sensors().items() if e not in self.ctx.bypassed
        }
        bypassed = sorted(self.ctx.bypassed)
        unavailable = sorted(self.ctx.accepted_unavailable)

        def name(entity_id: str) -> str:
            return display_name(self.hass, entity_id)

        lines = [tr(lang, "arm_gap_bypassed", sensor=name(e)) for e in bypassed]
        lines += [tr(lang, "arm_gap_unavailable", sensor=name(e)) for e in unavailable]
        lines += [
            tr(
                lang,
                "arm_gap_rule",
                sensor=name(entity_id),
                rules=", ".join(quoted(lang, n) for n in names),
            )
            for entity_id, names in open_rules.items()
        ]
        if lines:
            self.fire_event(
                {
                    "type": "ArmedWithGaps",
                    "bypassed": bypassed,
                    "unavailable": unavailable,
                    "rule_sensors": list(open_rules),
                }
            )
        if open_rules:
            self.fire_event({"type": "OpenRuleSensors", "sensors": list(open_rules)})
        return lines, [name(e) for e in [*bypassed, *open_rules]]

    @property
    def _state_tag(self) -> str:
        return f"{PUSH_STATE_TAG}_{self.area_id}"

    def _state_push(
        self, event: NotifyEvent, title: str, message: str, values: dict[str, Any]
    ) -> None:
        """Scharf-/Unscharf-Nachricht: ersetzt die vorige auf dem Handy (gleicher ``tag``),
        bei Empfängern, die diesmal nichts bekommen, wird die alte weggeräumt."""
        self._state_replace(
            self.notifier.notify(
                event,
                title,
                message,
                values=values,
                data={"tag": self._state_tag},
                test_mode=self.ctx.test_mode,
            )
        )

    def _state_replace(self, sent: list[str]) -> None:
        """Neue Scharf-/Unscharf-Nachricht verschickt: bei den übrigen die alte wegräumen."""
        now = set(sent)
        if stale := self._state_pushed - now:
            self.notifier.clear(stale, self._state_tag)
        self._state_pushed = now

    def _clear_state_push(self) -> None:
        if self._state_pushed:
            self.notifier.clear(self._state_pushed, self._state_tag)
            self._state_pushed = set()

    def _notify_armed(self) -> None:
        """Eine Nachricht beim Scharfschalten.

        "Scharf geschaltet" an: diese Nachricht, ergänzt um die Lücken. Sonst – nur wenn es
        Lücken gibt – der "Hinweis beim Scharfschalten". Nie beide.
        """
        if self.ctx.profile is None:
            return
        lang = self.lang
        profile = self.profile_name(self.ctx.profile.profile_id)
        by = by_text(lang, self.changed_by)
        lines, open_names = self._arm_gaps()
        gaps = "; ".join(lines)
        values: dict[str, Any] = {"profil": profile, "wer": self.changed_by}
        if lines:
            values |= {"offen": ", ".join(open_names), "grund": gaps}
        reason, self._auto_arm_reason = self._auto_arm_reason, None
        tail = f" {tr(lang, 'arm_gaps_tail', items=gaps)}" if lines else ""
        if notify_enabled(self.entry.options, NotifyEvent.ARMED, push_disarm=self.push_disarm):
            message = (
                tr(lang, "auto_armed", profile=profile, reason=reason)
                if reason is not None
                else tr(lang, "armed", profile=profile, by=by)
            )
            self._state_push(NotifyEvent.ARMED, tr(lang, "armed_title"), message + tail, values)
        elif reason is not None and self._automation_notify_on():
            # Nur die Automatik-Nachricht (mit den Lücken), nicht zusätzlich den Hinweis
            title, message = auto_armed_message(profile, reason, lang)
            self._state_push(
                NotifyEvent.AUTOMATION,
                title,
                message + tail,
                {"profil": profile, "grund": reason},
            )
        elif lines:
            message = tr(lang, "arm_gaps", profile=profile, by=by, items=gaps)
            self._state_push(NotifyEvent.ARM_HINT, tr(lang, "arm_hint_title"), message, values)
        else:
            self._clear_state_push()  # alte Unscharf-Nachricht weg
        if lines:
            persistent_notification.async_create(
                self.hass,
                tr(lang, "arm_gaps", profile=profile, by=by, items=gaps),
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
            self._notify_armed()
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
        if effect.new is AlarmState.DISARMED and effect.old is not AlarmState.DISARMED:
            self._notify_disarmed(by)

    def _automation_notify_on(self) -> bool:
        return notify_enabled(
            self.entry.options, NotifyEvent.AUTOMATION, push_disarm=self.push_disarm
        )

    def _notify_disarmed(self, by: str) -> None:
        """Eine Nachricht beim Unscharfschalten – sie ersetzt die Scharf-Nachricht; wer keine
        Unscharf-Nachricht bekommt, bei dem verschwindet die alte einfach."""
        lang = self.lang
        self._auto_arm_reason = None
        reason, self._auto_disarm_reason = self._auto_disarm_reason, None
        if self._via_push is not None:
            # Push-Knopf: Rückmeldung an die Alarm-Empfänger, ersetzt die Scharf-Nachricht
            actor, targets = self._via_push
            self._state_replace(
                self.notifier.send(
                    targets,
                    tr(lang, "disarmed_title"),
                    tr(lang, "push_disarmed", who=actor),
                    test_mode=self.ctx.test_mode,
                    data={"tag": self._state_tag},
                )
            )
            return
        profile = self.profile_name(reason[0]) if reason is not None else ""
        if notify_enabled(self.entry.options, NotifyEvent.DISARMED, push_disarm=self.push_disarm):
            message = (
                tr(lang, "auto_disarmed", profile=profile, reason=reason[1])
                if reason is not None
                else tr(lang, "disarmed", by=by)
            )
            self._state_push(
                NotifyEvent.DISARMED,
                tr(lang, "disarmed_title"),
                message,
                {"wer": self.changed_by},
            )
        elif reason is not None and self._automation_notify_on():
            title, message = auto_disarmed_message(profile, reason[1], lang)
            self._state_push(
                NotifyEvent.AUTOMATION, title, message, {"profil": profile, "grund": reason[1]}
            )
        else:
            self._clear_state_push()

    @callback
    def auto_arm(self, profile_id: str, reason: str) -> None:
        """Automatik schaltet scharf: der Grund steht dann in der einen Scharf-Nachricht."""
        self._auto_arm_reason = reason
        try:
            self.arm(profile_id, changed_by=tr(self.lang, "automation_actor"))
        finally:
            if self.ctx.state is AlarmState.DISARMED:
                self._auto_arm_reason = None  # gescheitert

    @callback
    def auto_disarm(self, profile_id: str, reason: str) -> None:
        """Automatik schaltet unscharf: der Grund steht in der einen Unscharf-Nachricht."""
        self._auto_disarm_reason = (profile_id, reason)
        try:
            self.disarm_trusted(changed_by=tr(self.lang, "automation_actor"))
        finally:
            self._auto_disarm_reason = None

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
        # Ins Log nur, was passiert ist – wer quittiert hat, steht im Logbuch (ADR 0020)
        _LOGGER.warning(
            "Alarm quittiert (Profil %s), bleibt scharf; bis zum Schließen nicht überwacht: %s",
            effect.profile_id,
            sorted(effect.bypassed_until_closed) or "-",
        )
        targets = parse_reaction(self.entry.options, effect.profile_id).notify
        # Ersetzt die Alarm-Nachricht (gleicher tag) und verschwindet beim Unscharfschalten
        sent = set(
            self.notifier.notify(
                NotifyEvent.ALARM_ENDED,
                tr(lang, "alarm_ended_title"),
                message,
                profile_targets=targets,
                profile_speakers=self._profile_speakers(effect.profile_id),
                values={"wer": self.changed_by, "profil": name},
                data={"tag": PUSH_TAG},
                test_mode=self.ctx.test_mode,
            )
        )
        if stale := self._pushed_targets - sent:
            self.notifier.clear(stale, PUSH_TAG)
        self._pushed_targets = sent
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
            display_name(self.hass, effect.sensor_key)
            + (tr(lang, "vibration_suffix") if self.is_vibration(effect.sensor_key) else ""),
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
            self.homecoming.entry_finished(
                in_time=effect.new is AlarmState.DISARMED,
                passage=effect.new is AlarmState.ARMED,  # Durchgang: bleibt scharf
            )

    @callback
    def _cancel_speech_repeat(self) -> None:
        if self._speech_repeat is not None:
            self._speech_repeat()
            self._speech_repeat = None

    def _entry_seconds(self, seconds: int) -> tuple[int, list[str]]:
        """Eingangsverzögerung – länger, wenn sich vorher jemand aus „Bei Rückkehr“ genähert hat.

        Nur verlängern, nie kürzen (ADR 0015). Rückgabe: Sekunden und wer sich genähert hat.
        """
        profile = self.ctx.profile
        extra, near = self.automation.entry_extension(
            profile.profile_id if profile else None, dt_util.utcnow().timestamp()
        )
        return (extra, near) if extra > seconds else (seconds, [])

    @callback
    def _start_timer(self, effect: StartTimer) -> None:
        self._cancel_timer()
        seconds = effect.seconds
        if effect.kind is TimerKind.ENTRY_DELAY:
            self._entry_token = effect.token
            seconds, near = self._entry_seconds(seconds)
            # Ausgangserkennung (ADR 0014): stille Wartezeit statt Eingangsverzögerung
            if self.exit.active:
                seconds = max(seconds, self.exit.seconds)
            if near:
                self.fire_event(
                    {
                        "type": "EntryDelayExtended",
                        "profile_id": self.ctx.profile.profile_id if self.ctx.profile else None,
                        "seconds": seconds,
                        "normal": effect.seconds,
                        "persons": near,
                    }
                )
        self.delay_ends_at = dt_util.utcnow() + timedelta(seconds=seconds)

        @callback
        def _elapsed(_now: datetime) -> None:
            self._timer_cancel = None
            self.delay_ends_at = None
            self._dispatch(self._timer_event(effect.kind, effect.token))

        self._timer_cancel = async_call_later(self.hass, seconds, _elapsed)

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
