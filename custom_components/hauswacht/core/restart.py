"""Verhalten nach einem Neustart von Home Assistant (oder Neuladen von Hauswacht).

Einstellung unter Systemeinstellungen → Verhalten nach Neustart:

- ``restore`` (Standard): Zustand von vorher wiederherstellen. War die Anlage scharf, ist sie
  es sofort wieder – mit demselben Profil und denselben überbrückten Meldern, ohne Prüfung und
  ohne Ausgangsverzögerung. Lief eine Eingangsverzögerung, beginnt sie neu. Ein laufender Alarm
  wird nicht fortgesetzt (keine Sirenen); die Anlage ist danach scharf und meldet ihn als
  Alarm-Nachricht. Mit ``restart_continue_alarm`` (Standard aus) wird ein Alarm, der noch in
  der Reaktionsphase war, nach dem Hochfahren erneut ausgelöst.
- ``armed``: immer mit einem festen Profil je Bereich scharf schalten – normal, mit Prüfung
  offener Melder, sobald Home Assistant hochgefahren ist. Bereiche ohne Profil bleiben unscharf.
- ``disarmed``: immer unscharf (Verhalten bis 0.44), mit Nachricht, wenn vorher scharf war.

Reine Logik ohne Home Assistant – die Runtime führt den Plan aus.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

RESTORE = "restore"
ARMED = "armed"
DISARMED = "disarmed"
BEHAVIORS: tuple[str, ...] = (RESTORE, ARMED, DISARMED)
DEFAULT_BEHAVIOR = RESTORE

OPT_RESTART_BEHAVIOR = "restart_behavior"
OPT_RESTART_PROFILES = "restart_profiles"  # {Bereichs-ID: Profil-ID} für "armed"
OPT_RESTART_CONTINUE_ALARM = "restart_continue_alarm"  # laufenden Alarm fortsetzen (Standard aus)

# So lange nach dem Wiederherstellen gelten Melder, die erst beim Hochfahren melden, als
# "Startphase": keine Ausfallmeldungen, offen vorgefundene Melder werden überbrückt.
STARTUP_GRACE = 120.0  # Sekunden
# "armed": so lange nach dem Hochfahren warten, damit Funkmelder wieder melden
ARM_AFTER_START = 60.0  # Sekunden

# Gespeicherte Zustände (AlarmState-Werte), aus denen wiederhergestellt wird
_ENTRY_STATES = frozenset({"pending"})
_ALARM_STATES = frozenset({"triggered", "alarm_hold"})


class RestartKind(StrEnum):
    DISARMED = "disarmed"  # unscharf bleiben
    RESTORE = "restore"  # Zustand wiederherstellen
    ARM = "arm"  # festes Profil normal scharf schalten


@dataclass(frozen=True)
class RestartPlan:
    kind: RestartKind
    profile_id: str | None = None
    entry_delay: bool = False  # Eingangsverzögerung lief -> neu starten
    alarm_was_active: bool = False  # Alarm lief (Reaktionsphase oder noch nicht quittiert)
    alarm_in_reaction: bool = False  # Alarm war noch in der Reaktionsphase (Sirenen liefen)
    trigger_sensor: str | None = None
    bypassed: frozenset[str] = frozenset()
    bypassed_until_closed: frozenset[str] = frozenset()
    accepted_unavailable: frozenset[str] = frozenset()
    auto_armed_by: str | None = None
    # Nachricht "nach Neustart unscharf" (Profil, das vorher scharf war)
    report_disarmed: str | None = None


def restart_behavior(options: Mapping[str, Any]) -> str:
    value = options.get(OPT_RESTART_BEHAVIOR)
    return str(value) if value in BEHAVIORS else DEFAULT_BEHAVIOR


def continue_alarm(options: Mapping[str, Any]) -> bool:
    """Laufenden Alarm nach dem Neustart fortsetzen? (nur bei "wiederherstellen")"""
    return bool(options.get(OPT_RESTART_CONTINUE_ALARM, False))


def restart_profile(options: Mapping[str, Any], area_id: str) -> str | None:
    profiles = options.get(OPT_RESTART_PROFILES)
    if not isinstance(profiles, Mapping):
        return None
    value = profiles.get(area_id)
    return str(value) if isinstance(value, str) and value else None


def _ids(value: Any) -> frozenset[str]:
    if not isinstance(value, list | tuple | set | frozenset):
        return frozenset()
    return frozenset(v for v in value if isinstance(v, str) and v)


def saved_state(  # noqa: PLR0913
    *,
    profile_id: str | None,
    state: str,
    bypassed: Collection[str],
    bypassed_until_closed: Collection[str],
    accepted_unavailable: Collection[str],
    trigger_sensor: str | None,
    auto_armed_by: str | None,
) -> dict[str, Any] | None:
    """Was für ein Wiederherstellen gespeichert wird (None = unscharf)."""
    if profile_id is None or state == "disarmed":
        return None
    return {
        "profile": profile_id,
        "state": state,
        "bypassed": sorted(bypassed),
        "bypassed_until_closed": sorted(bypassed_until_closed),
        "accepted_unavailable": sorted(accepted_unavailable),
        "trigger_sensor": trigger_sensor,
        "auto_armed_by": auto_armed_by,
    }


def plan_restart(  # noqa: PLR0913
    behavior: str,
    *,
    saved: Mapping[str, Any] | None,
    previous_profile: str | None,
    fixed_profile: str | None,
    known_profiles: Collection[str],
    reload: bool = False,
) -> RestartPlan:
    """Was nach dem Start passieren soll.

    ``saved``: Zustand vor dem Neustart (ab 0.45); ``previous_profile``: das früher allein
    gespeicherte scharfe Profil (Aktualisierung von älteren Versionen).

    ``reload``: Hauswacht wurde nur neu geladen (z. B. nach dem Speichern von Einstellungen),
    Home Assistant lief weiter. Dann gilt die Einstellung "nach Neustart" nicht – der bisherige
    Zustand bleibt, wie er war (sonst wäre die Anlage bei "immer scharf" nach jeder Änderung
    eine Minute später scharf bzw. bei "immer unscharf" plötzlich unscharf).
    """
    if reload:
        behavior = RESTORE
    if behavior == ARMED:
        if fixed_profile is not None and fixed_profile in known_profiles:
            return RestartPlan(RestartKind.ARM, profile_id=fixed_profile)
        return RestartPlan(RestartKind.DISARMED, report_disarmed=previous_profile)
    if behavior != RESTORE:
        return RestartPlan(RestartKind.DISARMED, report_disarmed=previous_profile)

    data: Mapping[str, Any] = saved if isinstance(saved, Mapping) else {}
    profile_id = data.get("profile") or previous_profile
    if not isinstance(profile_id, str) or not profile_id:
        return RestartPlan(RestartKind.DISARMED)  # war unscharf
    if profile_id not in known_profiles:
        # Profil inzwischen gelöscht: lieber unscharf und melden als irgendetwas scharf
        return RestartPlan(RestartKind.DISARMED, report_disarmed=profile_id)
    state = str(data.get("state") or "armed")
    trigger = data.get("trigger_sensor")
    auto = data.get("auto_armed_by")
    return RestartPlan(
        RestartKind.RESTORE,
        profile_id=profile_id,
        entry_delay=state in _ENTRY_STATES,
        alarm_was_active=state in _ALARM_STATES,
        alarm_in_reaction=state == "triggered",
        trigger_sensor=trigger if isinstance(trigger, str) else None,
        bypassed=_ids(data.get("bypassed")),
        bypassed_until_closed=_ids(data.get("bypassed_until_closed")),
        accepted_unavailable=_ids(data.get("accepted_unavailable")),
        auto_armed_by=auto if isinstance(auto, str) else None,
    )
