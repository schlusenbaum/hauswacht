"""Einrichten nach Zielen (ADR 0017, Abschnitt 5) – rein, ohne Home Assistant.

Statt Einstellungen fragt der Assistent nach **Zielen**:

- ``night`` – nachts absichern (Profil mit dem Knopf „Nacht“)
- ``away`` – automatisch scharf, wenn alle weg sind (Profil mit dem Knopf „Abwesend“)
- ``return`` – beim Heimkommen unscharf („Bei Rückkehr“ im Abwesend-Profil)
- ``night_return`` – nachts heimkommen, ohne dass „Nacht“ aus ist („Reinlassen“ im Nacht-Profil)
- ``garage`` – Garage oder Werkstatt getrennt: eigener **Bereich** „Garage“ (eigenes Bedienfeld,
  unabhängig vom Haus schaltbar) mit eigener Meldergruppe und einem Profil mit dem Knopf
  „Abwesend“. Melder aus Gruppen des Hauses wechseln in die Gruppe „Garage“; die Profile des
  Hauses, die sie bisher überwacht haben, bekommen die Gruppe „Garage“ dazu (im Haus ändert sich
  also nichts) – seit 0.65.0b3

Dazu (seit 0.65.0b2) **Türen und Fenster**: noch nicht eingeordnete Melder in Meldergruppen
aufnehmen und festlegen, welche Türen Eingangstüren sind (mit Eingangsverzögerung) – und Sirenen
(nur **eintragen**, nie freigeben; auch Sirenen von Rauchmeldern, die als Einbruchsirene nur den
Einbruchton bekommen und bei Brand gesperrt sind) und Empfänger für die betroffenen Profile.

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
from .areas import MAIN_AREA, parse_areas, profile_area
from .automation import DEFAULT_AWAY_DELAY, MAX_AWAY_DELAY, parse_automation, parse_time
from .away_proof import parse_proof_settings
from .changes import Change
from .changes.areas import save_area
from .changes.profiles import save_profile
from .changes.sirens import save_sirens
from .changes.zones import save_zone
from .presence_rules import leaves_by_door
from .profiles import (
    DEFAULT_ENTRY_DELAY,
    MAX_DELAY,
    profile_behaviour,
    profile_info,
    profile_infos,
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
GARAGE = "garage"
GOALS = (NIGHT, AWAY, RETURN, NIGHT_RETURN, GARAGE)
# Platzhalter für Meldergruppen, die erst der Plan anlegt (in den Antworten bei „zones“)
NEW_GROUP = "new"
OUTSIDE = "@outside"
INSIDE = "@inside"
GARAGE_ZONE = "@garage"
KIND_DOOR = "door"
KIND_WINDOW = "window"
KIND_MOTION = "motion"
GARAGE_DELAY = 30  # Sekunden, Aus- und Eingangsverzögerung eines neuen Garagen-Profils
GARAGE_ICON = "mdi:garage"
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
        "auto_away_entity": "Eigener Auslöser „alle weg“",
        "return_mode": "Bei Rückkehr",
        "return_persons": "Bei Rückkehr – Personen",
        "sirens": "Sirenen",
        "notify": "Empfänger",
        "registered": "Eingetragene Sirenen (nicht freigegeben)",
        "group": "Gruppe {name}",
        "entry_doors": "Eingangstüren (mit Eingangsverzögerung)",
        "outside": "Außen",
        "inside": "Innen",
        "garage": "Garage",
        "t_sensors": "Türen, Fenster und Bewegungsmelder",
        "t_garage": "Garage oder Werkstatt",
        "n_smoke": "Rauchmelder als Einbruchsirene: Sie bekommen nur den Einbruchton, nie den "
        "Brandton, und bei einem Brand schaltet Hauswacht sie nicht ab. Die Brandfunktion des "
        "Rauchmelders bleibt unverändert.",
        "n_moved": "{sensor} kommt aus der Gruppe {group} in die Gruppe Garage. Die Profile des "
        "Hauses, die {group} überwachen, bekommen die Gruppe Garage dazu – im Haus ändert sich "
        "nichts.",
        "t_area": "Neuer Bereich {name}",
        "area_device": "Eigenes Gerät",
        "area_device_v": "Hauswacht {name} – mit Bedienfeld, Profilauswahl und Knöpfen",
        "e_group_empty": "Gruppe {name} hätte danach keinen Melder mehr – bitte nicht alle Melder "
        "in die Garage verschieben oder die Gruppe erst löschen.",
        "e_garage_sensors": "Garage oder Werkstatt: bitte mindestens einen Melder wählen.",
        "e_label_member": "{sensor} steckt über ein Label in einer Gruppe und lässt sich hier "
        "nicht verschieben.",
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
        "auto_away_entity": "Own trigger “all away”",
        "return_mode": "On return",
        "return_persons": "On return – persons",
        "sirens": "Sirens",
        "notify": "Recipients",
        "registered": "Registered sirens (not enabled)",
        "group": "Group {name}",
        "entry_doors": "Entry doors (with entry delay)",
        "outside": "Outside",
        "inside": "Inside",
        "garage": "Garage",
        "t_sensors": "Doors, windows and motion sensors",
        "t_garage": "Garage or workshop",
        "n_smoke": "Smoke detectors as burglar sirens: they only get the burglar tone, never the "
        "fire tone, and Hauswacht does not switch them off during a fire. The smoke detector's "
        "fire function stays unchanged.",
        "n_moved": "{sensor} moves from the group {group} to the group Garage. The house profiles "
        "that monitor {group} get the group Garage too – nothing changes for the house.",
        "t_area": "New area {name}",
        "area_device": "Own device",
        "area_device_v": "Hauswacht {name} – with alarm panel, profile selection and buttons",
        "e_group_empty": "Group {name} would have no sensor left – please do not move all of its "
        "sensors to the garage, or delete the group first.",
        "e_garage_sensors": "Garage or workshop: please choose at least one sensor.",
        "e_label_member": "{sensor} is in a group via a label and cannot be moved here.",
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
class SensorInfo:
    """Ein Melder (Tür, Fenster, Bewegung) aus Home Assistant."""

    entity_id: str
    name: str
    kind: str  # aktueller Typ: door, window, motion …
    default: str  # Typ nach Geräteklasse (gespeichert wird nur eine Abweichung davon)
    place: str = ""  # „Erdgeschoss › Küche“
    group: str | None = None  # Meldergruppe (oder keine)
    via_label: bool = False  # über ein Label in der Gruppe (dann nicht verschiebbar)


@dataclass(frozen=True)
class Household:
    """Was nur Home Assistant weiß – vorab eingesammelt."""

    persons: tuple[str, ...] = ()
    facts: Facts = field(default_factory=Facts)
    # Meldergruppen mit Bewegungsmeldern (nachts meist nicht scharf – man bewegt sich im Haus)
    motion_groups: frozenset[str] = frozenset()
    # Sirenen, die angeboten werden (eingetragene und weitere)
    sirens: tuple[str, ...] = ()
    # Davon Sirenen von Rauchmeldern (nur Einbruchton, bei Brand gesperrt)
    smoke: frozenset[str] = frozenset()
    # Türen, Fenster und Bewegungsmelder
    sensors: tuple[SensorInfo, ...] = ()
    # Empfänger (IDs wie auf der Einstellungsseite)
    notify: tuple[str, ...] = ()
    # Anzeigenamen für Sirenen und Empfänger (Personen und Melder stehen in facts.names)
    names: Mapping[str, str] = field(default_factory=dict)

    def name(self, key: str) -> str:
        return self.names.get(key) or self.facts.name(key)


def _lang(language: str) -> str:
    return "de" if language == "de" else "en"


def detectable(options: Mapping[str, Any], hh: Household) -> frozenset[str]:
    """Personen, die als weg erkannt werden können (Ortung, „Tür + Signal“ oder „eines reicht“)."""
    weak = parse_proof_settings(options).weak | leaves_by_door(options)
    return frozenset(p for p in hh.persons if p in hh.facts.located or p in weak)


def _mode_in_area(options: Mapping[str, Any], mode: str, area: str) -> str | None:
    for info in profile_infos(options):
        if info.panel_mode == mode and profile_area(options, info.profile_id) == area:
            return info.profile_id
    return None


def targets(options: Mapping[str, Any]) -> dict[str, str | None]:
    """Welche vorhandenen Profile die Ziele betreffen (Knopf des Bedienfelds im Haus)."""
    return {
        NIGHT: _mode_in_area(options, NIGHT, MAIN_AREA),
        AWAY: _mode_in_area(options, AWAY, MAIN_AREA),
    }


# --- Vorschläge (vorausgefüllte Antworten) ---------------------------------------------------


def suggestions(options: Mapping[str, Any], hh: Household) -> dict[str, Any]:
    """Antworten, wie sie der Assistent vorschlägt – aus dem, was schon eingestellt ist."""
    zones = list(parse_zones(options))
    found = targets(options)
    night, away = found[NIGHT], found[AWAY]
    can = detectable(options, hh)
    people = [p for p in hh.persons if p in can]
    night_zones = [z for z in zones if z not in hh.motion_groups] or list(zones)
    result: dict[str, Any] = {
        "goals": [],
        NIGHT: {"zones": night_zones, "arm_time": None, "disarm_time": None},
        AWAY: {"zones": list(zones), "persons": people, "delay": DEFAULT_AWAY_DELAY},
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
            "persons": [p for p in auto.away_persons if p in hh.persons] or people,
            "delay": auto.away_delay,
        }
        back = parse_return(options, away)
        if back.active and back.mode in RETURN_CHOICES:
            result[RETURN] = {"persons": list(back.persons), "mode": back.mode}
    sensors = sensor_suggestions(options, hh)
    result["sensors"] = sensors
    result[GARAGE] = {"sensors": [], "away": True, "arm_time": None, "disarm_time": None}
    free = [s for s in hh.sensors if s.group is None]
    # Neue Gruppen gleich in die Profile: Türen/Fenster nachts und abwesend, Bewegung nur abwesend
    if any(s.kind != KIND_MOTION for s in free) and sensors["outside"] == NEW_GROUP:
        result[NIGHT]["zones"].append(OUTSIDE)
        result[AWAY]["zones"].append(OUTSIDE)
    if any(s.kind == KIND_MOTION for s in free) and sensors["inside"] == NEW_GROUP:
        result[AWAY]["zones"].append(INSIDE)
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


def _best_group(hh: Household, kinds: set[str]) -> str:
    """Die Gruppe mit den meisten Meldern dieser Art – sonst eine neue."""
    counts: dict[str, int] = {}
    for sensor in hh.sensors:
        if sensor.group is not None and sensor.kind in kinds:
            counts[sensor.group] = counts.get(sensor.group, 0) + 1
    return max(counts, key=lambda g: counts[g]) if counts else NEW_GROUP


def sensor_suggestions(options: Mapping[str, Any], hh: Household) -> dict[str, Any]:
    """Türen, Fenster, Bewegung: Ziel-Gruppen für freie Melder, Eingangstüren wie bisher."""
    zones = parse_zones(options)
    outside = _best_group(hh, {KIND_DOOR, KIND_WINDOW})
    inside = _best_group(hh, {KIND_MOTION})
    return {
        # Nichts vorausgewählt: freie Melder sind oft für Licht oder Heizung da (Kühlschranktür,
        # Bewegungsmelder fürs Licht) – überwacht wird nur, was du ausdrücklich wählst
        "add": [],
        "outside": outside if outside in zones else NEW_GROUP,
        "inside": inside if inside in zones else NEW_GROUP,
        "entry_doors": [s.entity_id for s in hh.sensors if s.kind == KIND_DOOR],
    }


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
    touched: list[str] = field(default_factory=list)
    # Platzhalter neuer Gruppen -> echte ID
    mapping: dict[str, str] = field(default_factory=dict)
    # Gruppen, aus denen Melder in die Garage wechseln (deren Haus-Profile bekommen „Garage“ dazu)
    garage_from: set[str] = field(default_factory=set)
    start: Mapping[str, Any] = field(default_factory=dict)  # Einstellungen vor dem Plan
    # Profil -> Index seines Schritts im Plan und Stand vor dem ersten Ändern
    profile_index: dict[str, int] = field(default_factory=dict)
    profile_before: dict[str, dict[str, Any]] = field(default_factory=dict)

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
        "auto_away_entity": auto.away_entity,
        "auto_away_entity_state": auto.away_entity_state,
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
        if not data["zones"]:
            b.errors.append(b.t("e_night_zones" if goal == NIGHT else "e_away_zones"))
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
        automation["auto_away_entity"] = None  # Ziel mit Personen ersetzt einen eigenen Auslöser
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
    if GARAGE in goals and not _strings((answers.get(GARAGE) or {}).get("sensors")):
        b.errors.append(b.t("e_garage_sensors"))
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

    Reihenfolge: Sirenen eintragen, Melder (Gruppen, Eingangstüren, Garage), Garagen-Profil,
    Profile der Ziele. Jeder Schritt rechnet über die Logikschicht weiter.
    """
    answers = normalize(answers)
    b = _Builder(options, hh, _lang(language), labels or {}, start=options)
    _check(b, answers)
    if b.errors:
        return _plan(b), None
    current: Mapping[str, Any] | None = options
    stages = (_stage_sirens, _stage_sensors, _stage_garage, _stage_profiles, _stage_house_keep)
    for stage in stages:
        current = stage(b, current, answers)  # type: ignore[arg-type]
        if current is None or b.errors:
            return _plan(b), None
    b.options = options
    return _plan(b), current


def _stage_sirens(
    b: _Builder, current: Mapping[str, Any], answers: dict[str, Any]
) -> Mapping[str, Any] | None:
    """Sirenen eintragen (nie freigeben)."""
    registered = [s for s in current.get("sirens", []) if isinstance(s, str)]
    chosen = _strings(answers.get("sirens"), b.hh.sirens)
    if any(s in b.hh.smoke for s in chosen):
        b.notes.append(b.t("n_smoke"))
    new_sirens = [s for s in chosen if s not in registered]
    if not new_sirens:
        return current
    change = save_sirens(current, {"sirens": [*registered, *new_sirens]})
    if not _ok(b, change):
        return None
    after = [s for s in change.options.get("sirens", []) if isinstance(s, str)]  # type: ignore[union-attr]
    b.steps.append(
        {
            "title": b.t("t_sirens"),
            "profile": None,
            "new": False,
            "changes": [_diff(b, "registered", registered, after, kind="list")],
        }
    )
    b.notes.append(b.t("n_hardware"))
    return change.options


def _entry_types(
    b: _Builder, current: Mapping[str, Any], relevant: list[SensorInfo], entry: set[str]
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Eingangstüren: Tür (mit Eingangsverzögerung) oder sofort auslösend."""
    types = dict(current.get("sensor_types", {}) or {})
    before = [s.entity_id for s in relevant if s.kind == KIND_DOOR]
    after: list[str] = []
    for sensor in relevant:
        if sensor.entity_id in entry:
            want = KIND_DOOR
        elif sensor.kind == KIND_DOOR:
            want = "other"  # keine Eingangstür mehr: löst sofort aus
        else:
            want = sensor.kind
        if want == KIND_DOOR:
            after.append(sensor.entity_id)
        if want == sensor.default:
            types.pop(sensor.entity_id, None)
        else:
            types[sensor.entity_id] = want
    new = dict(current)
    new["sensor_types"] = types
    if sorted(before) == sorted(after):
        return new, None
    row = _diff(b, "entry_doors", before, after, kind="list")
    grouped = {s.entity_id for s in relevant if s.group is not None}
    # Eine schon überwachte Tür bekommt eine Eingangsverzögerung = späterer Alarm
    row["weakens"] = any(e not in before and e in grouped for e in after)
    return new, row


def _group_add(
    b: _Builder, current: Mapping[str, Any], target: str, name: str, items: list[str]
) -> tuple[Mapping[str, Any] | None, str, dict[str, Any] | None]:
    """Melder in eine Gruppe aufnehmen (vorhanden oder neu, gleichnamige wird ergänzt)."""
    zones = parse_zones(current)
    if target not in zones:
        target = next((z for z, v in zones.items() if v.name.casefold() == name.casefold()), "")
    zone = zones.get(target)
    before = sorted(zone.entities) if zone else []
    data = {
        "name": zone.name if zone else name,
        "entities": [*before, *items],
        "label": zone.label if zone else None,
    }
    change = save_zone(current, target or None, data, entities_by_label=b.labels)
    if not _ok(b, change):
        return None, target, None
    gid = str(change.item_id)
    label = b.t("group", name=data["name"])
    row = _diff(b, "group", before or None, [*before, *items], kind="list", label=label)
    return change.options, gid, row


def _stage_sensors(
    b: _Builder, current: Mapping[str, Any], answers: dict[str, Any]
) -> Mapping[str, Any] | None:
    """Freie Melder in Gruppen, Eingangstüren, Melder für die Garage."""
    known = {s.entity_id: s for s in b.hh.sensors}
    sens = answers.get("sensors") or {}
    garage = _strings((answers.get(GARAGE) or {}).get("sensors"), known)
    if GARAGE not in answers["goals"]:
        garage = []
    add = [e for e in _strings(sens.get("add"), known) if known[e].group is None]
    add = [e for e in add if e not in garage]
    rows: list[dict[str, Any]] = []
    # 1. Eingangstüren – für alle Türen/Fenster, die danach überwacht sind
    watched = {e for e, s in known.items() if s.group is not None} | set(add) | set(garage)
    relevant = [
        known[e]
        for e in watched
        if KIND_DOOR in (known[e].kind, known[e].default)
        or KIND_WINDOW in (known[e].kind, known[e].default)
        or known[e].kind == "other"
    ]
    # Ohne Antwort zu den Eingangstüren bleibt alles, wie es ist (nie stillschweigend ändern)
    if isinstance(sens.get("entry_doors"), list):
        entry = set(_strings(sens.get("entry_doors"), known))
        current, row = _entry_types(b, current, sorted(relevant, key=lambda s: s.name), entry)
        if row:
            rows.append(row)
    # 2. Garage: aus den bisherigen Gruppen nehmen
    moved = _garage_out(b, current, [known[e] for e in garage], rows)
    if moved is None:
        return None
    current = moved
    # 3. Freie Melder: Türen/Fenster nach „Außen“, Bewegung nach „Innen“
    groups = (
        (OUTSIDE, sens.get("outside"), "outside", [e for e in add if known[e].kind != KIND_MOTION]),
        (INSIDE, sens.get("inside"), "inside", [e for e in add if known[e].kind == KIND_MOTION]),
        (GARAGE_ZONE, None, "garage", garage),
    )
    for placeholder, target, name_key, items in groups:
        if not items:
            continue
        new, gid, row = _group_add(b, current, str(target or ""), b.t(name_key), items)
        if new is None:
            return None
        current = new
        b.mapping[placeholder] = gid
        if row:
            rows.append(row)
    if rows:
        b.steps.append({"title": b.t("t_sensors"), "profile": None, "new": False, "changes": rows})
    _map_zones(b, answers)
    return current


def _garage_out(
    b: _Builder, current: Mapping[str, Any], sensors: list[SensorInfo], rows: list[dict[str, Any]]
) -> Mapping[str, Any] | None:
    by_group: dict[str, list[str]] = {}
    for sensor in sensors:
        if sensor.group is None:
            continue
        if sensor.via_label:
            b.errors.append(b.t("e_label_member", sensor=sensor.name))
            return None
        by_group.setdefault(sensor.group, []).append(sensor.entity_id)
    zones = parse_zones(current)
    for gid, removed in by_group.items():
        zone = zones.get(gid)
        if zone is None:
            continue
        rest = sorted(zone.entities - set(removed))
        if not rest and not zone.label:
            b.errors.append(b.t("e_group_empty", name=zone.name))
            return None
        data = {"name": zone.name, "entities": rest, "label": zone.label}
        change = save_zone(current, gid, data, entities_by_label=b.labels)
        if not _ok(b, change):
            return None
        current = change.options  # type: ignore[assignment]
        label = b.t("group", name=zone.name)
        row = _diff(b, "group", sorted(zone.entities), rest, kind="list", label=label)
        rows.append(row)
        b.garage_from.add(gid)
        for entity_id in removed:
            b.notes.append(b.t("n_moved", sensor=b.hh.name(entity_id), group=zone.name))
    return current


def _map_zones(b: _Builder, answers: dict[str, Any]) -> None:
    """Platzhalter neuer Gruppen in den Antworten durch die echten IDs ersetzen."""
    for goal in (NIGHT, AWAY):
        own = dict(answers.get(goal) or {})
        zones = _strings(own.get("zones"))
        mapped = [b.mapping.get(z, z) for z in zones]
        own["zones"] = [z for z in mapped if not z.startswith("@")]
        answers[goal] = own


def _garage_area(b: _Builder, current: Mapping[str, Any]) -> tuple[Mapping[str, Any] | None, str]:
    """Bereich „Garage“ – vorhandener gleichen Namens oder neu."""
    name = b.t("garage")
    found = next(
        (a.area_id for a in parse_areas(current).values() if a.name.casefold() == name.casefold()),
        None,
    )
    if found is not None:
        return current, found
    change = save_area(current, None, {"name": name, "icon": GARAGE_ICON})
    if not _ok(b, change):
        return None, ""
    area_id = str(change.item_id)
    b.steps.append(
        {
            "title": b.t("t_area", name=name),
            "profile": None,
            "new": True,
            "changes": [
                _diff(b, "area_device", None, b.t("area_device_v", name=name), kind="text")
            ],
        }
    )
    return change.options, area_id


def _stage_garage(
    b: _Builder, current: Mapping[str, Any], answers: dict[str, Any]
) -> Mapping[str, Any] | None:
    """Bereich „Garage“ mit Profil (Knopf „Abwesend“) – vorhandene werden ergänzt."""
    gid = b.mapping.get(GARAGE_ZONE)
    if GARAGE not in answers["goals"] or gid is None:
        return current
    with_area, area_id = _garage_area(b, current)
    if with_area is None:
        return None
    current = with_area
    own = answers.get(GARAGE) or {}
    pid = _mode_in_area(current, AWAY, area_id)
    data: dict[str, Any] = {"name": profile_info(current, pid).name if pid else b.t("garage")}
    if pid is None:
        taken = {i.name.casefold() for i in profile_infos(current)}
        if data["name"].casefold() in taken:
            data["name"] = f"{data['name']} 2"
        data |= {
            "icon": GARAGE_ICON,
            "area": area_id,
            "panel_mode": AWAY,
            "exit_delay": GARAGE_DELAY,
            "entry_delay": GARAGE_DELAY,
            "zones": [gid],
        }
    else:
        zones = list(profile_behaviour(current, pid).zones)
        data["zones"] = zones if gid in zones else [*zones, gid]
    automation = _automation(current, pid)
    for key in ("arm_time", "disarm_time"):
        value = own.get(key) or None
        if value is not None and parse_time(value) is None:
            b.errors.append(b.t("e_time"))
        automation[f"auto_{key}"] = value
    if own.get("away"):
        # Wie das Haus: dieselben Personen (aus dem Ziel „alle weg“ oder die erkennbaren)
        away = answers.get(AWAY) or {}
        persons = _strings(away.get("persons"), b.hh.persons) or sorted(detectable(b.options, b.hh))
        automation["auto_away_persons"] = persons
        automation["auto_away_delay"] = int(away.get("delay") or DEFAULT_AWAY_DELAY)
    data["automation"] = automation
    if b.errors:
        return None
    b.options = current
    _reaction(b, pid, answers, data)
    return _save_profile_step(b, current, pid, data)


def _stage_house_keep(
    b: _Builder, current: Mapping[str, Any], answers: dict[str, Any]
) -> Mapping[str, Any] | None:
    """Profile des Hauses, die die bisherige Gruppe überwacht haben, bekommen „Garage“ dazu."""
    gid = b.mapping.get(GARAGE_ZONE)
    if gid is None or not b.garage_from:
        return current
    for info in profile_infos(current):
        pid = info.profile_id
        if profile_area(current, pid) != MAIN_AREA:
            continue
        zones = list(profile_behaviour(current, pid).zones)
        if gid in zones or not b.garage_from & set(zones):
            continue
        new = _save_profile_step(b, current, pid, {"name": info.name, "zones": [*zones, gid]})
        if new is None:
            return None
        current = new
    return current


def _save_profile_step(
    b: _Builder, current: Mapping[str, Any], pid: str | None, data: dict[str, Any]
) -> Mapping[str, Any] | None:
    """Profil speichern (Assistenten-Modus) – ein Profil hat im Plan genau einen Schritt."""
    snapshot = _snapshot(current, pid)
    change = save_profile(current, pid, data, entities_by_label=b.labels, partial=True)
    if not _ok(b, change):
        return None
    new_id = change.item_id or pid or ""
    b.touched.append(new_id)
    before = b.profile_before.setdefault(new_id, snapshot)
    is_new = new_id not in b.start.get("profiles", {})
    after = _snapshot(change.options or {}, new_id)
    step = _profile_step(b, None if is_new else new_id, new_id, before, after)
    if new_id in b.profile_index:
        b.steps[b.profile_index[new_id]] = step
    else:
        b.profile_index[new_id] = len(b.steps)
        b.steps.append(step)
    return change.options


def _stage_profiles(
    b: _Builder, current: Mapping[str, Any], answers: dict[str, Any]
) -> Mapping[str, Any] | None:
    """Profile für die Ziele (Nacht, Abwesend) im Haus."""
    goals = set(answers["goals"])
    found = targets(b.options)
    wanted = {NIGHT: bool(goals & {NIGHT, NIGHT_RETURN}), AWAY: bool(goals & {AWAY, RETURN})}
    for goal in (NIGHT, AWAY):
        if not wanted[goal]:
            continue
        pid = found[goal]
        b.options = current
        data = _payload(b, goal, pid, answers)
        if b.errors:
            return None
        new = _save_profile_step(b, current, pid, data)
        if new is None:
            return None
        current = new
    return current


def _ok(b: _Builder, change: Change) -> bool:
    if change.ok and change.options is not None:
        return True
    detail = ", ".join(f"{k}: {v}" for k, v in dict(change.errors).items())
    b.errors.append(b.t("e_save", detail=detail))
    return False


def _plan(b: _Builder) -> dict[str, Any]:
    needs = any(c["overwrite"] or c["weakens"] for s in b.steps for c in s["changes"])
    return {
        "steps": b.steps,
        "notes": list(dict.fromkeys(b.notes)),
        "errors": list(dict.fromkeys(b.errors)),
        "needs_confirm": needs,
        "profiles": list(dict.fromkeys(b.touched)),
    }


# --- Vorher / nachher ----------------------------------------------------------------------

_FIELDS = (
    ("name", "text"),
    ("zones", "list"),
    ("exit_delay", "seconds"),
    ("entry_delay", "seconds"),
    ("auto_arm_time", "text"),
    ("auto_disarm_time", "text"),
    ("auto_away_entity", "list1"),
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
        "auto_away_entity": auto.away_entity,
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
    if kind == "list1":
        return b.names([value])
    if kind == "seconds":
        return b.t("seconds", v=value)
    if kind == "minutes":
        return b.t("minutes", v=value)
    if kind == "mode":
        return b.t(f"mode_{value}")
    return str(value)


def _diff(  # noqa: PLR0913
    b: _Builder, key: str, before: Any, after: Any, *, kind: str, label: str | None = None
) -> dict[str, Any]:
    empty = before in (None, "", [], RETURN_OFF)
    if kind == "list":
        overwrite = not empty and not set(before) <= set(after)
    else:
        overwrite = not empty and before != after
    weakens = (key == "entry_delay" and isinstance(before, int) and after > before) or (
        key == "return_mode" and after == RETURN_ALWAYS and before != RETURN_ALWAYS
    )
    return {
        "label": label or b.t(key),
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
