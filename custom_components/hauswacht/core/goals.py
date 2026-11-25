"""Einrichten nach Zielen (ADR 0017, Abschnitt 5) – rein, ohne Home Assistant.

Statt Einstellungen fragt der Assistent nach **Zielen**:

- ``night`` – nachts absichern (Profil mit dem Knopf „Nacht“)
- ``away`` – automatisch scharf, wenn alle weg sind (Profil mit dem Knopf „Abwesend“)
- ``return`` – beim Heimkommen unscharf („Bei Rückkehr“ im Abwesend-Profil)
- ``night_return`` – nachts heimkommen, ohne dass „Nacht“ aus ist („Reinlassen“ im Nacht-Profil)

Dazu Sirenen (nur **eintragen**, nie freigeben) und Empfänger für die betroffenen Profile.

Aus den Antworten entsteht ein **Plan**: je betroffenem Profil die Änderungen „bisher → neu“.
Vorhandenes wird nur ergänzt; was überschrieben würde (oder die Anlage nachgiebiger macht, z. B.
eine längere Eingangsverzögerung), ist markiert und braucht eine Bestätigung. Gerechnet wird über
dieselbe Logikschicht wie im Seitenblatt (``save_profile`` im Assistenten-Modus, ``save_sirens``)
– mit allen ihren Prüfungen. Diese Datei schaltet nichts und speichert nichts.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from .advisor import MIN_SAMPLES, Facts
from .automation import DEFAULT_AWAY_DELAY, MAX_AWAY_DELAY, parse_automation, parse_time
from .away_proof import parse_proof_settings
from .changes import Change
from .changes.profiles import save_profile
from .changes.sirens import save_sirens
from .profiles import (
    DEFAULT_ENTRY_DELAY,
    MAX_DELAY,
    profile_behaviour,
    profile_for_mode,
    profile_info,
    profile_settings,
)
from .reactions import parse_reaction
from .returning import (
    RETURN_ALWAYS,
    RETURN_AUTO_ONLY,
    RETURN_DOOR,
    RETURN_OFF,
    RETURN_PASSAGE,
    WITH_DOOR,
    parse_return,
    return_to_storage,
)
from .sensors import parse_zones

NIGHT = "night"
AWAY = "away"
RETURN = "return"
NIGHT_RETURN = "night_return"
GOALS = (NIGHT, AWAY, RETURN, NIGHT_RETURN)
RETURN_CHOICES = (RETURN_DOOR, RETURN_PASSAGE, RETURN_AUTO_ONLY, RETURN_ALWAYS)
AWAY_EXIT_DELAY = 60  # Sekunden, neues Abwesend-Profil
NIGHT_EXIT_DELAY = 0  # nachts ist man drinnen

NEW_PROFILE: Mapping[str, Mapping[str, Any]] = {
    NIGHT: {"icon": "mdi:weather-night", "de": "Nacht", "en": "Night"},
    AWAY: {"icon": "mdi:shield-lock-outline", "de": "Abwesend", "en": "Away"},
}

LABELS: Mapping[str, Mapping[str, str]] = {
    "de": {
        "name": "Name",
        "zones": "Meldergruppen",
        "exit_delay": "Ausgangsverzögerung",
        "entry_delay": "Eingangsverzögerung",
        "auto_arm_time": "Scharf um",
        "auto_disarm_time": "Unscharf um",
        "auto_away_persons": "Scharf, wenn alle weg",
        "auto_away_delay": "Wartezeit „alle weg“",
        "return_mode": "Bei Rückkehr",
        "return_persons": "Bei Rückkehr – Personen",
        "sirens": "Sirenen",
        "notify": "Empfänger",
        "registered": "Eingetragene Sirenen (nicht freigegeben)",
        "seconds": "{v} s",
        "minutes": "{v} min",
        "none": "–",
        "t_sirens": "Sirenen eintragen",
        "t_new": "Neues Profil {name}",
        "t_profile": "Profil {name}",
        "mode_off": "Nichts",
        "mode_auto_only": "Unscharf, nur wenn automatisch scharf",
        "mode_door": "Unscharf mit Türbeleg",
        "mode_always": "Unscharf, auch nach Scharfschalten von Hand",
        "mode_passage": "Reinlassen",
        "n_undetectable": "{person} kann nie als weg erkannt werden (keine Ortung, „Tür + Signal“ "
        "aus). „Scharf, wenn alle weg“ würde so nie scharf schalten, „Bei Rückkehr“ nie greifen. "
        "Abhilfe: unter System → Anwesenheit eine Ortung oder „Tür + Signal“ einrichten.",
        "n_measured": "Eingangsverzögerung {v} s aus euren Messungen (längste gemessene Zeit plus "
        "Puffer).",
        "n_hardware": "Sirenen werden nur eingetragen. Die Freigabe der echten Sirenenansteuerung "
        "bleibt ein eigener Schritt unter Alarmgeber.",
        "e_no_goal": "Bitte mindestens ein Ziel wählen.",
        "e_night_zones": "Nachts absichern: bitte mindestens eine Meldergruppe wählen.",
        "e_away_zones": "Abwesend: bitte mindestens eine Meldergruppe wählen.",
        "e_away_persons": "Automatisch scharf, wenn alle weg: bitte mindestens eine Person wählen.",
        "e_return_persons": "Beim Heimkommen unscharf: bitte mindestens eine Person wählen.",
        "e_night_return_persons": "Nachts heimkommen: bitte mindestens eine Person wählen.",
        "e_return_mode": "Beim Heimkommen unscharf: unbekannte Auswahl.",
        "e_time": "Ungültige Uhrzeit (Format HH:MM).",
        "e_save": "Der Plan lässt sich so nicht speichern: {detail}",
    },
    "en": {
        "name": "Name",
        "zones": "Sensor groups",
        "exit_delay": "Exit delay",
        "entry_delay": "Entry delay",
        "auto_arm_time": "Arm at",
        "auto_disarm_time": "Disarm at",
        "auto_away_persons": "Arm when all away",
        "auto_away_delay": "Waiting time “all away”",
        "return_mode": "On return",
        "return_persons": "On return – persons",
        "sirens": "Sirens",
        "notify": "Recipients",
        "registered": "Registered sirens (not enabled)",
        "seconds": "{v} s",
        "minutes": "{v} min",
        "none": "–",
        "t_sirens": "Register sirens",
        "t_new": "New profile {name}",
        "t_profile": "Profile {name}",
        "mode_off": "Nothing",
        "mode_auto_only": "Disarm only if armed automatically",
        "mode_door": "Disarm with door proof",
        "mode_always": "Disarm, also after arming by hand",
        "mode_passage": "Let in",
        "n_undetectable": "{person} can never be detected as away (no location, “door + signal” "
        "off). “Arm when all away” would never arm, “On return” would never apply. Fix: set up a "
        "location or “door + signal” under System → Presence.",
        "n_measured": "Entry delay {v} s from your measurements (longest measured time plus a "
        "buffer).",
        "n_hardware": "Sirens are only registered. Enabling real siren control stays a separate "
        "step under Alarm devices.",
        "e_no_goal": "Please choose at least one goal.",
        "e_night_zones": "Secure the night: please choose at least one sensor group.",
        "e_away_zones": "Away: please choose at least one sensor group.",
        "e_away_persons": "Arm when all away: please choose at least one person.",
        "e_return_persons": "Disarm when coming home: please choose at least one person.",
        "e_night_return_persons": "Coming home at night: please choose at least one person.",
        "e_return_mode": "Disarm when coming home: unknown choice.",
        "e_time": "Invalid time (format HH:MM).",
        "e_save": "The plan cannot be saved like this: {detail}",
    },
}


@dataclass(frozen=True)
class Household:
    """Was nur Home Assistant weiß – vorab eingesammelt."""

    persons: tuple[str, ...] = ()
    facts: Facts = field(default_factory=Facts)
    # Meldergruppen mit Bewegungsmeldern (nachts meist nicht scharf – man bewegt sich im Haus)
    motion_groups: frozenset[str] = frozenset()
    # Sirenen, die angeboten werden (eingetragene und weitere, nie Rauchmelder)
    sirens: tuple[str, ...] = ()
    # Empfänger (IDs wie auf der Einstellungsseite)
    notify: tuple[str, ...] = ()
    # Anzeigenamen für Sirenen und Empfänger (Personen und Melder stehen in facts.names)
    names: Mapping[str, str] = field(default_factory=dict)

    def name(self, key: str) -> str:
        return self.names.get(key) or self.facts.name(key)


def _lang(language: str) -> str:
    return "de" if language == "de" else "en"


def detectable(options: Mapping[str, Any], hh: Household) -> frozenset[str]:
    """Personen, die als weg erkannt werden können (Ortung oder „Tür + Signal“)."""
    weak = parse_proof_settings(options).weak
    return frozenset(p for p in hh.persons if p in hh.facts.located or p in weak)


def targets(options: Mapping[str, Any]) -> dict[str, str | None]:
    """Welche vorhandenen Profile die Ziele betreffen (über den Knopf des Bedienfelds)."""
    return {NIGHT: profile_for_mode(options, NIGHT), AWAY: profile_for_mode(options, AWAY)}


# --- Vorschläge (vorausgefüllte Antworten) ---------------------------------------------------


def suggestions(options: Mapping[str, Any], hh: Household) -> dict[str, Any]:
    """Antworten, wie sie der Assistent vorschlägt – aus dem, was schon eingestellt ist."""
    zones = list(parse_zones(options))
    found = targets(options)
    night, away = found[NIGHT], found[AWAY]
    can = detectable(options, hh)
    people = [p for p in hh.persons if p in can]
    night_zones = [z for z in zones if z not in hh.motion_groups] or zones
    result: dict[str, Any] = {
        "goals": [],
        NIGHT: {"zones": night_zones, "arm_time": None, "disarm_time": None},
        AWAY: {"zones": zones, "persons": people, "delay": DEFAULT_AWAY_DELAY},
        RETURN: {"persons": people, "mode": RETURN_DOOR},
        NIGHT_RETURN: {"persons": people},
        "sirens": [],
        "notify": [],
    }
    if night is not None:
        auto = parse_automation(options, night)
        result[NIGHT] = {
            "zones": list(profile_behaviour(options, night).zones),
            "arm_time": _hhmm(auto.arm_time),
            "disarm_time": _hhmm(auto.disarm_time),
        }
        back = parse_return(options, night)
        if back.mode == RETURN_PASSAGE and back.persons:
            result[NIGHT_RETURN] = {"persons": list(back.persons)}
    if away is not None:
        auto = parse_automation(options, away)
        result[AWAY] = {
            "zones": list(profile_behaviour(options, away).zones),
            "persons": list(auto.away_persons) or people,
            "delay": auto.away_delay,
        }
        back = parse_return(options, away)
        if back.active and back.mode in RETURN_CHOICES:
            result[RETURN] = {"persons": list(back.persons), "mode": back.mode}
    existing = [pid for pid in (night, away) if pid is not None]
    registered = [s for s in options.get("sirens", []) if isinstance(s, str)]
    sirens = [s for pid in existing for s in parse_reaction(options, pid).sirens]
    result["sirens"] = list(dict.fromkeys(sirens or registered))
    result["notify"] = list(
        dict.fromkeys(n for pid in existing for n in parse_reaction(options, pid).notify)
    )
    return result


def _hhmm(value: Any) -> str | None:
    return value.strftime("%H:%M") if value is not None else None


# --- Plan ----------------------------------------------------------------------------------


@dataclass
class _Builder:
    options: Mapping[str, Any]
    hh: Household
    lang: str
    labels: Mapping[str, frozenset[str]]
    steps: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def t(self, key: str, **values: Any) -> str:
        return LABELS[self.lang][key].format(**values)

    def names(self, items: Iterable[str]) -> str:
        zones = parse_zones(self.options)
        shown = [zones[i].name if i in zones else self.hh.name(i) for i in items]
        return ", ".join(shown) or self.t("none")


def _strings(value: Any, allowed: Iterable[str] | None = None) -> list[str]:
    if not isinstance(value, list | tuple):
        return []
    ok = set(allowed) if allowed is not None else None
    return list(dict.fromkeys(v for v in value if isinstance(v, str) and (ok is None or v in ok)))


def _automation(options: Mapping[str, Any], pid: str | None) -> dict[str, Any]:
    """Die ganze Automatik eines Profils (der Assistenten-Modus braucht sie vollständig)."""
    if pid is None:
        return {"auto_away_delay": DEFAULT_AWAY_DELAY}
    auto = parse_automation(options, pid)
    return {
        "auto_arm_time": _hhmm(auto.arm_time),
        "auto_disarm_time": _hhmm(auto.disarm_time),
        "auto_weekdays": sorted(auto.weekdays),
        "auto_schedule": auto.schedule,
        "auto_away_persons": list(auto.away_persons),
        "auto_away_delay": auto.away_delay,
    }


def _needed_entry_delay(hh: Household, persons: Iterable[str], mode: str) -> int | None:
    """Gemessen nötige Eingangsverzögerung (Türen, und bei Türbeleg/Reinlassen je Person)."""
    values = [m.seconds for m in hh.facts.entry_needed.values() if m.count >= MIN_SAMPLES]
    if mode in WITH_DOOR:
        values += [
            m.seconds
            for p in persons
            if (m := hh.facts.proof_needed.get(p)) is not None and m.count >= MIN_SAMPLES
        ]
    return min(max(values), MAX_DELAY) if values else None


def _payload(b: _Builder, goal: str, pid: str | None, answers: Mapping[str, Any]) -> dict[str, Any]:
    """Änderungen für das Profil eines Ziels (Nacht oder Abwesend) – nur, was sich ändert."""
    options = b.options
    goals = set(answers["goals"])
    zones = list(parse_zones(options))
    data: dict[str, Any] = {}
    if pid is None:
        spec = NEW_PROFILE[goal]
        data |= {
            "name": spec[b.lang],
            "icon": spec["icon"],
            "panel_mode": goal,
            "exit_delay": NIGHT_EXIT_DELAY if goal == NIGHT else AWAY_EXIT_DELAY,
            "entry_delay": DEFAULT_ENTRY_DELAY,
        }
    else:
        data["name"] = profile_info(options, pid).name
    own = answers.get(goal) or {}
    if goal in goals or pid is None:
        data["zones"] = _strings(own.get("zones"), zones)
    automation = _automation(options, pid)
    back = (
        return_to_storage(parse_return(options, pid))
        if pid
        else return_to_storage(parse_return({}, None))
    )
    if goal == NIGHT and NIGHT in goals:
        for key in ("arm_time", "disarm_time"):
            value = own.get(key) or None
            if value is not None and parse_time(value) is None:
                b.errors.append(b.t("e_time"))
            automation[f"auto_{key}"] = value
        data["automation"] = automation
    if goal == NIGHT and NIGHT_RETURN in goals:
        back["mode"] = RETURN_PASSAGE
        back["persons"] = _strings((answers.get(NIGHT_RETURN) or {}).get("persons"), b.hh.persons)
        data["return"] = back
    if goal == AWAY and AWAY in goals:
        automation["auto_away_persons"] = _strings(own.get("persons"), b.hh.persons)
        try:
            delay = int(own.get("delay", DEFAULT_AWAY_DELAY))
        except (TypeError, ValueError):
            delay = DEFAULT_AWAY_DELAY
        automation["auto_away_delay"] = min(max(delay, 1), MAX_AWAY_DELAY)
        data["automation"] = automation
    if goal == AWAY and RETURN in goals:
        _away_return(b, pid, answers, data, back)
    _reaction(b, pid, answers, data)
    return data


def _away_return(
    b: _Builder,
    pid: str | None,
    answers: Mapping[str, Any],
    data: dict[str, Any],
    back: dict[str, Any],
) -> None:
    """„Beim Heimkommen unscharf“ – und die Eingangsverzögerung nach euren Messungen."""
    ret = answers.get(RETURN) or {}
    mode = ret.get("mode", RETURN_DOOR)
    if mode not in RETURN_CHOICES:
        b.errors.append(b.t("e_return_mode"))
        mode = RETURN_DOOR
    back["mode"] = mode
    back["persons"] = _strings(ret.get("persons"), b.hh.persons)
    data["return"] = back
    current = profile_settings(b.options, pid)["entry_delay"] if pid else DEFAULT_ENTRY_DELAY
    needed = _needed_entry_delay(b.hh, back["persons"], mode)
    if needed is not None and needed > current:
        data["entry_delay"] = needed
        b.notes.append(b.t("n_measured", v=needed))


def _reaction(
    b: _Builder, pid: str | None, answers: Mapping[str, Any], data: dict[str, Any]
) -> None:
    """Sirenen und Empfänger: ergänzen, nie wegnehmen."""
    reaction = parse_reaction(b.options, pid) if pid else None
    sirens = _strings(answers.get("sirens"), b.hh.sirens)
    notify = _strings(answers.get("notify"), b.hh.notify)
    if sirens:
        data["sirens"] = list(dict.fromkeys([*(reaction.sirens if reaction else ()), *sirens]))
    if notify:
        data["notify"] = list(dict.fromkeys([*(reaction.notify if reaction else ()), *notify]))


def _check(b: _Builder, answers: Mapping[str, Any]) -> None:
    goals = set(answers["goals"])
    if not goals:
        b.errors.append(b.t("e_no_goal"))
    required = (
        (NIGHT, NIGHT, "zones", "e_night_zones"),
        (AWAY, AWAY, "zones", "e_away_zones"),
        (AWAY, AWAY, "persons", "e_away_persons"),
        (RETURN, RETURN, "persons", "e_return_persons"),
        (NIGHT_RETURN, NIGHT_RETURN, "persons", "e_night_return_persons"),
    )
    found = targets(b.options)
    # Ein neues Profil braucht Meldergruppen, auch wenn nur „Heimkommen“ gewählt ist
    if found[NIGHT] is None and NIGHT_RETURN in goals:
        goals.add(NIGHT)
    if found[AWAY] is None and RETURN in goals:
        goals.add(AWAY)
    for goal, section, key, error in required:
        if goal in goals and not _strings((answers.get(section) or {}).get(key)):
            b.errors.append(b.t(error))
    can = detectable(b.options, b.hh)
    chosen: list[str] = []
    for goal in (AWAY, RETURN):
        if goal in goals:
            chosen += _strings((answers.get(goal) or {}).get("persons"))
    for person in dict.fromkeys(chosen):
        if person not in can:
            b.notes.append(b.t("n_undetectable", person=b.hh.name(person)))


def normalize(answers: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(answers)
    result["goals"] = [g for g in _strings(answers.get("goals")) if g in GOALS]
    return result


def build(
    options: Mapping[str, Any],
    hh: Household,
    answers: Mapping[str, Any],
    language: str = "de",
    *,
    labels: Mapping[str, frozenset[str]] | None = None,
) -> tuple[dict[str, Any], Mapping[str, Any] | None]:
    """Plan aus den Antworten – und die Einstellungen, wie sie danach wären (oder ``None``).

    Plan::

        {"steps": [{"title": "...", "profile": id | None, "new": bool,
                    "changes": [{"label", "before", "after", "overwrite", "weakens"}]}],
         "notes": ["..."], "errors": ["..."], "needs_confirm": bool, "profiles": [id, ...]}
    """
    answers = normalize(answers)
    b = _Builder(options, hh, _lang(language), labels or {})
    _check(b, answers)
    if b.errors:
        return _plan(b, []), None
    current: Mapping[str, Any] = options
    goals = set(answers["goals"])
    # 1. Sirenen eintragen (nie freigeben)
    registered = [s for s in options.get("sirens", []) if isinstance(s, str)]
    new_sirens = [s for s in _strings(answers.get("sirens"), hh.sirens) if s not in registered]
    if new_sirens:
        change = save_sirens(current, {"sirens": [*registered, *new_sirens]})
        if not _ok(b, change):
            return _plan(b, []), None
        current = change.options  # type: ignore[assignment]
        b.steps.append(
            {
                "title": b.t("t_sirens"),
                "profile": None,
                "new": False,
                "changes": [
                    _diff(b, "registered", registered, [*registered, *new_sirens], kind="list")
                ],
            }
        )
        b.notes.append(b.t("n_hardware"))
    # 2. Profile für die Ziele
    touched: list[str] = []
    found = targets(options)
    wanted = {
        NIGHT: bool(goals & {NIGHT, NIGHT_RETURN}),
        AWAY: bool(goals & {AWAY, RETURN}),
    }
    for goal in (NIGHT, AWAY):
        if not wanted[goal]:
            continue
        pid = found[goal]
        b.options = current
        data = _payload(b, goal, pid, answers)
        if b.errors:
            return _plan(b, []), None
        before = _snapshot(current, pid)
        change = save_profile(current, pid, data, entities_by_label=labels, partial=True)
        if not _ok(b, change):
            return _plan(b, []), None
        current = change.options  # type: ignore[assignment]
        new_id = change.item_id or pid or ""
        touched.append(new_id)
        after = _snapshot(current, new_id)
        b.steps.append(_profile_step(b, pid, new_id, before, after))
    b.options = options
    return _plan(b, touched), current


def _ok(b: _Builder, change: Change) -> bool:
    if change.ok and change.options is not None:
        return True
    detail = ", ".join(f"{k}: {v}" for k, v in dict(change.errors).items())
    b.errors.append(b.t("e_save", detail=detail))
    return False


def _plan(b: _Builder, touched: list[str]) -> dict[str, Any]:
    needs = any(c["overwrite"] or c["weakens"] for s in b.steps for c in s["changes"])
    return {
        "steps": b.steps,
        "notes": list(dict.fromkeys(b.notes)),
        "errors": list(dict.fromkeys(b.errors)),
        "needs_confirm": needs,
        "profiles": touched,
    }


# --- Vorher / nachher ----------------------------------------------------------------------

_FIELDS = (
    ("name", "text"),
    ("zones", "list"),
    ("exit_delay", "seconds"),
    ("entry_delay", "seconds"),
    ("auto_arm_time", "text"),
    ("auto_disarm_time", "text"),
    ("auto_away_persons", "list"),
    ("auto_away_delay", "minutes"),
    ("return_mode", "mode"),
    ("return_persons", "list"),
    ("sirens", "list"),
    ("notify", "list"),
)


def _snapshot(options: Mapping[str, Any], pid: str | None) -> dict[str, Any]:
    if pid is None or pid not in options.get("profiles", {}):
        return {}
    times = profile_settings(options, pid)
    auto = parse_automation(options, pid)
    back = parse_return(options, pid)
    reaction = parse_reaction(options, pid)
    return {
        "name": profile_info(options, pid).name,
        "zones": list(profile_behaviour(options, pid).zones),
        "exit_delay": times["exit_delay"],
        "entry_delay": times["entry_delay"],
        "auto_arm_time": _hhmm(auto.arm_time),
        "auto_disarm_time": _hhmm(auto.disarm_time),
        "auto_away_persons": list(auto.away_persons),
        "auto_away_delay": auto.away_delay,
        "return_mode": back.mode if back.active else RETURN_OFF,
        "return_persons": list(back.persons) if back.active else [],
        "sirens": list(reaction.sirens),
        "notify": list(reaction.notify),
    }


def _show(b: _Builder, kind: str, value: Any) -> str:
    if value is None or value in ("", []):
        return b.t("none")
    if kind == "list":
        return b.names(value)
    if kind == "seconds":
        return b.t("seconds", v=value)
    if kind == "minutes":
        return b.t("minutes", v=value)
    if kind == "mode":
        return b.t(f"mode_{value}")
    return str(value)


def _diff(b: _Builder, key: str, before: Any, after: Any, *, kind: str) -> dict[str, Any]:
    empty = before in (None, "", [], RETURN_OFF)
    if kind == "list":
        overwrite = not empty and not set(before) <= set(after)
    else:
        overwrite = not empty and before != after
    weakens = (key == "entry_delay" and isinstance(before, int) and after > before) or (
        key == "return_mode" and after == RETURN_ALWAYS and before != RETURN_ALWAYS
    )
    return {
        "label": b.t(key),
        "before": _show(b, kind, before),
        "after": _show(b, kind, after),
        "overwrite": overwrite,
        "weakens": weakens,
    }


def _profile_step(
    b: _Builder, pid: str | None, new_id: str, before: Mapping[str, Any], after: Mapping[str, Any]
) -> dict[str, Any]:
    changes = []
    for key, kind in _FIELDS:
        old, new = before.get(key), after.get(key)
        if pid is not None and old == new:
            continue
        if pid is None and new in (None, "", [], RETURN_OFF):
            continue
        if key == "auto_away_delay" and not after.get("auto_away_persons"):
            continue  # ohne „alle weg“ spielt die Wartezeit keine Rolle
        changes.append(_diff(b, key, old if pid is not None else None, new, kind=kind))
    name = after.get("name", new_id)
    return {
        "title": b.t("t_new" if pid is None else "t_profile", name=name),
        "profile": new_id,
        "new": pid is None,
        "changes": changes,
    }
