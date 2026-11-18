"""Anlagenübersicht: die aktuelle Konfiguration und ihr Zustand als ein JSON-Dokument.

Grundlage für die Karte "Hauswacht Übersicht" (Bildschirm und Druck), die Diagnose-Datei und die
Prüfhinweise. Nur lesen – hier wird nichts geschaltet oder gespeichert.

Bewusst NICHT enthalten: PINs (auch keine Hashes), vollständige Kartennummern und alles zum
Bedrohungs-PIN eines Benutzers (wer einen hat, soll aus einem Ausdruck nicht hervorgehen).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from .const import (
    MASTER_USER_ID,
    OPT_DURESS_NOTIFY,
    OPT_INFRASTRUCTURE,
    OPT_NOTIFY_SYSTEM,
    OPT_PUSH_DISARM,
    OPT_SIRENS_HARDWARE_ENABLED,
)
from .core.action_codes import ALL_KEYPADS, CodeAction, parse_action_codes
from .core.always_active import parse_always_active, parse_arm_on_close
from .core.areas import parse_areas, profile_area
from .core.automation import parse_automation
from .core.checks import run_checks
from .core.controls import learn_minutes, parse_controls
from .core.notify_events import NotifyEvent, enabled, route
from .core.profiles import (
    profile_behaviour,
    profile_info,
    profile_settings,
    stale_after_seconds,
    stale_override_hours,
)
from .core.reactions import parse_reaction
from .core.restart import OPT_RESTART_PROFILES, continue_alarm, restart_behavior
from .core.rules import build_engine, describe_rule, profile_rule_ids
from .core.sensor_types import excluded_sensors
from .core.sensors import resolve_zone
from .core.siren_guard import FireIndicator, SirenDevice, is_fire_tone, select_tone
from .core.speech import parse_speech
from .core.tilt import TILTED, parse_tilt_sources
from .core.users import Action, User
from .core.vibration import parse_vibration_sources, rule_for_zone_id
from .names import display_name, plain_name

if TYPE_CHECKING:
    from .runtime import HauswachtRuntime

UNAVAILABLE = frozenset({"unavailable", "unknown", None})


def _name(hass: HomeAssistant, entity_id: str) -> str:
    return display_name(hass, entity_id)


def _target_name(hass: HomeAssistant, target: str) -> str:
    """Empfänger lesbar: Notify-Entität mit Namen, sonst der Dienstname."""
    if "." in target and (state := hass.states.get(target)) is not None:
        return state.name
    return target.removeprefix("mobile_app_").replace("_", " ")


def _targets(hass: HomeAssistant, targets: Iterable[str]) -> list[str]:
    return [_target_name(hass, t) for t in targets]


def _battery(hass: HomeAssistant, entity_id: str) -> int | None:
    """Batteriestand des Geräts, zu dem der Melder gehört (falls es einen Batteriesensor hat)."""
    registry = er.async_get(hass)
    entry = registry.async_get(entity_id)
    if entry is None or entry.device_id is None:
        return None
    for other in er.async_entries_for_device(registry, entry.device_id):
        if other.domain != "sensor" or other.disabled_by is not None:
            continue
        device_class = other.device_class or other.original_device_class
        if device_class != "battery":
            continue
        state = hass.states.get(other.entity_id)
        try:
            return round(float(state.state)) if state is not None else None
        except ValueError:
            return None
    return None


def _masked(tag: str) -> str:
    return f"…{tag[-4:]}" if len(tag) > 4 else "…"


def _card_text(user: User, tag: str) -> str:
    """ "Schlüsselbund …B2C3" bzw. nur "…B2C3"."""
    return f"{user.tag_name(tag)} {_masked(tag)}" if user.tag_name(tag) else _masked(tag)


def _time(value: Any) -> str | None:
    return value.strftime("%H:%M") if value is not None else None


def _iso(timestamp: float | None) -> str | None:
    return dt_util.utc_from_timestamp(timestamp).isoformat() if timestamp else None


def _profiles(main: HauswachtRuntime) -> list[dict[str, Any]]:
    hass = main.hass
    options = main.entry.options
    areas = parse_areas(options)
    system_targets = options.get(OPT_NOTIFY_SYSTEM, [])
    rows: list[dict[str, Any]] = []
    for area in main.areas.values():
        for profile_id in area.options.get("profiles", {}):
            info = profile_info(options, profile_id)
            settings = profile_settings(options, profile_id)
            behaviour = profile_behaviour(options, profile_id)
            reaction = parse_reaction(options, profile_id)
            auto = parse_automation(options, profile_id)
            close = parse_arm_on_close(options, profile_id)
            alarm_targets = route(
                options,
                NotifyEvent.ALARM,
                system_targets=system_targets,
                profile_targets=reaction.notify,
            )
            rows.append(
                {
                    "id": profile_id,
                    "name": info.name,
                    "icon": info.icon,
                    "button": info.panel_mode,
                    "area": areas[profile_area(options, profile_id)].name,
                    "zones": [area.zones[z].name for z in behaviour.zones if z in area.zones],
                    "excluded": sorted(
                        _name(hass, e) for e in excluded_sensors(options, profile_id)
                    ),
                    "rules": [
                        area.rules[r].name
                        for r in profile_rule_ids(options, profile_id)
                        if r in area.rules
                    ],
                    "exit_delay": settings["exit_delay"],
                    "entry_delay": settings["entry_delay"],
                    "reaction_time": settings["reaction_time"],
                    "max_alarm_cycles": behaviour.max_alarm_cycles,
                    "open_policy": behaviour.open_policy.value,
                    "unavailable_policy": behaviour.unavailable_policy.value,
                    "tamper_alarm": behaviour.tamper_triggers_alarm,
                    "silent": reaction.silent,
                    "sirens": [_name(hass, s) for s in reaction.sirens],
                    "siren_tone": reaction.tone,
                    "siren_volume": reaction.volume,
                    "alarm_targets": _targets(hass, alarm_targets),
                    "auto": {
                        "arm_time": _time(auto.arm_time),
                        "disarm_time": _time(auto.disarm_time),
                        "weekdays": sorted(auto.weekdays),
                        "schedule": _name(hass, auto.schedule) if auto.schedule else None,
                        "away_persons": [plain_name(hass, p) for p in auto.away_persons],
                        "away_delay": auto.away_delay,
                        "disarm_on_arrival": auto.disarm_on_arrival,
                        "arrival_mode": auto.arrival_mode if auto.away_persons else "off",
                        "arrival_window": auto.arrival_window,
                    },
                    "arm_on_close": {
                        "enabled": close.enabled,
                        "doors": sorted(_name(hass, d) for d in close.doors),
                        "settle": close.settle,
                    },
                    "sensor_count": len(area.profile_sensors(profile_id)),
                }
            )
    return rows


def _sensors(main: HauswachtRuntime) -> list[dict[str, Any]]:
    """Alle Melder mit Gruppe, Typ, Zustand und Rolle je Profil (Matrix)."""
    hass = main.hass
    options = main.entry.options
    contacts = main.last_contacts()
    zone_of: dict[str, str] = {}
    for zone_name, members in main.zone_members().items():
        for member in members:
            zone_of.setdefault(member, zone_name)
    always = set()
    for area in main.areas.values():
        always |= set(area.always_sensors)
    # Rolle je Profil: einzeln scharf, nur in Auslöseregeln, ausgenommen
    roles: dict[str, dict[str, str]] = {}
    for area in main.areas.values():
        for profile_id in area.options.get("profiles", {}):
            single = area.profile_sensors(profile_id)
            rules = [
                area.rules[r] for r in profile_rule_ids(options, profile_id) if r in area.rules
            ]
            in_rules = build_engine(rules, area.zones, area._labels).watched()
            excluded = excluded_sensors(options, profile_id)
            for entity_id in single | in_rules | excluded:
                role = (
                    "armed"
                    if entity_id in single
                    else "rule"
                    if entity_id in in_rules
                    else "excluded"
                )
                roles.setdefault(entity_id, {})[profile_id] = role
    entities = set(zone_of) | always | set(roles)
    rows = []
    for entity_id in entities:
        state = hass.states.get(entity_id)
        raw = state.state if state else None
        rows.append(
            {
                "entity_id": entity_id,
                "name": _name(hass, entity_id),
                "zone": zone_of.get(entity_id),
                "type": main.type_of(entity_id).value,
                "state": _overview_state(main, entity_id, raw),
                "last_contact": contacts.get(entity_id),
                "battery": _battery(hass, entity_id),
                "always_active": entity_id in always,
                "profiles": roles.get(entity_id, {}),
            }
        )
    return sorted(rows, key=lambda r: (str(r["zone"] or "~"), str(r["name"]).casefold()))


def _overview_state(main: HauswachtRuntime, entity_id: str, raw: str | None) -> str:
    """Zustand für die Übersicht: open, closed, tilted oder unavailable."""
    if raw in UNAVAILABLE:
        return "unavailable"
    position = main.read_position(entity_id, main.hass.states.get(entity_id))
    if position == TILTED:
        return "tilted"
    if position in UNAVAILABLE:
        return "unavailable"
    return "open" if position == "on" else "closed"


def _rules(main: HauswachtRuntime, language: str) -> list[dict[str, Any]]:
    hass = main.hass
    options = main.entry.options
    used: dict[str, list[str]] = {}
    for area in main.areas.values():
        for profile_id in area.options.get("profiles", {}):
            for rule_id in profile_rule_ids(options, profile_id):
                used.setdefault(rule_id, []).append(profile_info(options, profile_id).name)
    rows = []
    for rule_id, rule in main.rules.items():
        rows.append(
            {
                "name": rule.name,
                "result": rule.result.value,
                "text": describe_rule(
                    rule,
                    lambda e: _name(hass, e),
                    lambda z: main.zones[z].name if z in main.zones else z,
                    language,
                ),
                "profiles": used.get(rule_id, []),
            }
        )
    return rows


def _sirens(main: HauswachtRuntime) -> list[dict[str, Any]]:
    hass = main.hass
    records = main.siren_tester.records if main.siren_tester is not None else {}
    rows = []
    for siren in main.sirens.sirens:
        caps = main.sirens.capabilities(siren)
        record = records.get(siren)
        state = hass.states.get(siren)
        tone = main.sirens.tones.get(siren)
        # Würde die Sirene bei einem Einbruch überhaupt einen erlaubten Ton bekommen?
        probe = SirenDevice(
            key=siren,
            entity_id=siren,
            fire_state=FireIndicator.CLEAR,
            max_duration=1,
            capabilities=caps,
            tone=tone,
            fire_tone_allowed=siren in main.sirens.fire_tone_ok,
        )
        burglar_tone, _ = select_tone("burglar", probe)
        rows.append(
            {
                "entity_id": siren,
                "name": _name(hass, siren),
                "available": state is not None and state.state not in UNAVAILABLE,
                "tones": sorted(caps.tones) if caps.tones else [],
                "tone_select": caps.tones_supported,
                "volume": caps.volume,
                "duration": caps.duration,
                "turn_off": caps.turn_off,
                "tone": tone,
                "burglar_tone": burglar_tone,
                "fire_tone_override": bool(
                    tone and is_fire_tone(tone) and siren in main.sirens.fire_tone_ok
                ),
                "switch": siren.startswith("switch."),
                "last_test": record.at.isoformat() if record else None,
                "heard": record.heard if record else None,
            }
        )
    return rows


def _users(main: HauswachtRuntime) -> list[dict[str, Any]]:
    area_names = {a.area_id: a.name for a in parse_areas(main.entry.options).values()}
    now = dt_util.utcnow().timestamp()
    rows = []
    for user in main.users:
        if user.user_id == MASTER_USER_ID:
            continue
        if user.area_rights is not None:
            rights = {
                area_names.get(area_id, area_id): sorted(a.value for a in actions)
                for area_id, actions in user.area_rights
            }
        else:
            allowed = sorted(a.value for a in Action if user.may(a))
            rights = {area_names.get(a, a): allowed for a in (user.areas or tuple(area_names))}
        rows.append(
            {
                "name": user.name,
                "pin": user.pin is not None,
                "cards": [_card_text(user, t) for t in user.tags]
                + [f"{_card_text(user, t)} ⏸" for t in user.disabled_tags],
                "active": user.active,
                "valid": user.valid_at(now),
                "valid_from": _iso(user.valid_from),
                "valid_until": _iso(user.valid_until),
                "expired": user.valid_until is not None and user.valid_until < now,
                "ha_account": user.ha_user is not None,
                "card_pin": user.card_pin,
                "rights": rights,
                "force_arm": user.can_force_arm,
            }
        )
    return rows


def _controls(main: HauswachtRuntime) -> list[dict[str, Any]]:
    options = main.entry.options
    areas = {a.area_id: a.name for a in parse_areas(options).values()}
    rows = []
    for control in parse_controls(options).values():
        rows.append(
            {
                "name": control.name,
                "kind": control.kind.value,
                "area": areas.get(control.area) if control.area in areas else None,
                "topic": control.topic or None,
                "buttons": {
                    key: profile_info(options, pid).name for key, pid in control.buttons.items()
                },
                "login": control.login.value,
                "emergency": control.emergency.value,
                "action": control.action.value,
                "profile": profile_info(options, control.profile).name if control.profile else None,
                "entity": _name(main.hass, control.entity) if control.entity else None,
                "presses": {
                    press: profile_info(options, pid).name for press, pid in control.presses.items()
                },
                "source": control.source.value,
                "who": _name(main.hass, control.who) if control.who else None,
            }
        )
    return rows


def _action_codes(main: HauswachtRuntime) -> list[dict[str, Any]]:
    """Aktions-Codes. Der Code eines stillen Notrufs wird nicht gezeigt (Ausdruck!)."""
    options = main.entry.options
    keypads = {c.control_id: c.name for c in parse_controls(options).values()}
    rows = []
    for code in parse_action_codes(options):
        silent = code.action is CodeAction.SILENT_EMERGENCY
        profile_ok = True
        profile = None
        if code.action is CodeAction.ARM and code.profile:
            profile_ok = code.profile in (options.get("profiles") or {})
            profile = profile_info(options, code.profile).name if profile_ok else code.profile
        rows.append(
            {
                "name": code.name,
                "code": "•" * len(code.code) if silent else code.code,
                "key": code.key,
                "keypad": None
                if code.keypad == ALL_KEYPADS
                else keypads.get(code.keypad, code.keypad),
                "keypad_missing": code.keypad != ALL_KEYPADS and code.keypad not in keypads,
                "action": code.action.value,
                "profile": profile,
                "profile_missing": not profile_ok,
            }
        )
    return sorted(rows, key=lambda r: str(r["name"]).casefold())


def _notifications(main: HauswachtRuntime) -> dict[str, Any]:
    hass = main.hass
    options = main.entry.options
    system = options.get(OPT_NOTIFY_SYSTEM, [])
    push_disarm = bool(options.get(OPT_PUSH_DISARM, False))
    speech = parse_speech(options)
    events = []
    for event in NotifyEvent:
        if not enabled(options, event, push_disarm=push_disarm):
            continue
        targets = route(options, event, system_targets=system, push_disarm=push_disarm)
        spoken = speech.events.get(event)
        events.append(
            {
                "event": event.value,
                "targets": _targets(hass, targets),
                "speech": bool(spoken and spoken.enabled and (spoken.speakers or speech.speakers)),
            }
        )
    return {
        "general": _targets(hass, system),
        "events": events,
        "speakers": [_name(hass, s) for s in speech.speakers],
        "quiet": f"{_time(speech.quiet_start)}–{_time(speech.quiet_end)}"
        if speech.quiet_enabled
        else None,
        # Nur für die Prüfung, ohne Namen: hat der Bedrohungs-PIN irgendwo Empfänger?
        "duress_targets": len(options.get(OPT_DURESS_NOTIFY, []) or []),
    }


def _monitoring(main: HauswachtRuntime) -> dict[str, Any]:
    hass = main.hass
    options = main.entry.options
    stale = stale_after_seconds(options)
    silence = main.silence
    return {
        "stale_after_hours": round(stale / 3600) if stale else 0,
        "recommended_hours": silence.advice_hours() if silence is not None else None,
        # Eigene Grenzen je Melder (0 = nie prüfen) mit der Empfehlung für diesen Melder
        "stale_overrides": [
            {
                "name": _name(hass, entity),
                "hours": hours,
                "recommended": silence.sensor_advice(entity) if silence is not None else None,
            }
            for entity, hours in stale_override_hours(options).items()
        ],
        "observed_days": round(silence.days(), 1) if silence is not None else 0,
        "infrastructure": [
            {
                "name": _name(hass, e),
                "ok": e not in main.faulty_infrastructure(),
            }
            for e in options.get(OPT_INFRASTRUCTURE, [])
        ],
        "card_learn_minutes": learn_minutes(options),
        "restart": {
            "behavior": restart_behavior(options),
            "continue_alarm": continue_alarm(options),
            "profiles": [
                main.areas[a].profile_name(p)
                for a, p in (options.get(OPT_RESTART_PROFILES) or {}).items()
                if a in main.areas and p in main.areas[a].profiles
            ],
        },
        "homecoming": {
            "enabled": main.homecoming.enabled,
            "days": round(main.homecoming.days(), 1),
            "arrivals": main.homecoming.summary() or 0,
        },
    }


def _groups(main: HauswachtRuntime) -> list[dict[str, Any]]:
    """Meldergruppen mit Melderzahl und Fehlalarmschutz für Erschütterung."""
    options = main.entry.options
    rows = []
    for zone in main.zones.values():
        rule = rule_for_zone_id(options, zone.zone_id)
        rows.append(
            {
                "id": zone.zone_id,
                "name": zone.name,
                "label": zone.label,
                "count": len(resolve_zone(zone, main._labels)),
                "vibration_count": rule.count,
                "vibration_window": rule.window,
            }
        )
    return rows


def _special(main: HauswachtRuntime) -> dict[str, Any]:
    """Besondere Melder: Kippstellung (Zuordnung) und Erschütterungsstärke (Schwelle)."""
    hass = main.hass
    options = main.entry.options
    group_of: dict[str, str] = {}
    for zone_name, members in main.zone_members().items():
        for member in members:
            group_of.setdefault(member, zone_name)
    return {
        "tilt": [
            {
                "entity": s.entity_id,
                "name": _name(hass, s.entity_id),
                "attribute": s.attribute,
                "closed": sorted(s.closed),
                "tilted": sorted(s.tilted),
                "group": group_of.get(s.entity_id),
            }
            for s in parse_tilt_sources(options).values()
        ],
        "vibration": [
            {
                "entity": s.entity_id,
                "name": _name(hass, s.entity_id),
                "threshold": s.threshold,
                "group": group_of.get(s.entity_id),
            }
            for s in parse_vibration_sources(options).values()
        ],
    }


def build_overview(main: HauswachtRuntime) -> dict[str, Any]:
    """Die komplette Übersicht samt Prüfhinweisen (Sprache wie Home Assistant)."""
    hass = main.hass
    options = main.entry.options
    language = "de" if (hass.config.language or "").startswith("de") else "en"
    always = parse_always_active(options)
    users = main.users
    overview: dict[str, Any] = {
        "generated_at": dt_util.utcnow().isoformat(),
        "language": language,
        "system": {
            "test_mode": main.ctx.test_mode,
            "sirens_enabled": bool(options.get(OPT_SIRENS_HARDWARE_ENABLED, False)),
            "status": main.system_report().status.value,
            **main.code_guard_info(),
        },
        "areas": [
            {
                "name": area.area_name,
                "state": area.ctx.state.value,
                "profile": area.profile_name(area.ctx.profile.profile_id)
                if area.ctx.profile is not None
                else None,
                "guest": area.guest_active,
                # Ortszeit, damit der Prüfhinweis die Uhrzeit richtig nennt
                "guest_until": dt_util.as_local(area.guest_ends_at).isoformat()
                if area.guest_ends_at is not None
                else None,
            }
            for area in main.areas.values()
        ],
        "profiles": _profiles(main),
        "sensors": _sensors(main),
        "groups": _groups(main),
        "special": _special(main),
        "rules": _rules(main, language),
        "always_active": {
            "configured": always.configured,
            "sirens": [_name(hass, s) for s in always.sirens] if always.sirens_enabled else [],
        },
        "sirens": _sirens(main),
        "users": _users(main),
        "pin_rules": {
            "master_pin": any(u.user_id == MASTER_USER_ID and u.pin for u in users),
            "any_pin": main.has_codes,
            "arm_requires_code": main.code_arm_required,
            "buttons_without_pin": main.buttons_without_pin,
            "card_pin_unlinked": main.card_unlinked_pin,
        },
        "controls": _controls(main),
        "action_codes": _action_codes(main),
        "notifications": _notifications(main),
        "monitoring": _monitoring(main),
    }
    overview["findings"] = run_checks(
        overview, language, duress_configured=any(u.duress_pin for u in users)
    )
    return overview
