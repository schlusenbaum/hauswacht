"""Gemeinsame Prüfung der Einstellungen (ADR 0017) – rein, ohne Home Assistant.

Der Assistent schaut die Einstellungen an und sagt, was **nicht zusammenpasst**: Einstellungen,
die nie greifen, sich widersprechen oder laut Messung zu knapp sind. Dieselbe Prüfung läuft an
drei Stellen:

1. live in den Seitenblättern (Profil, Anwesenheit) – schon **vor** dem Speichern, nur Hinweis;
2. in den Prüfhinweisen (nur Befunde der Stufe „Fehler“);
3. im Check-up des Reiters „Assistent“ (ab 0.64.0b3).

Ein Befund::

    {"code": "...", "key": "...", "level": "error" | "warning" | "tip", "profile": id | None,
     "text": "...", "why": "...", "fixes": [Fix, ...]}

- ``text``: was nicht passt, in einem Satz
- ``why``: warum das wichtig ist – mit Messwert, wenn es einen gibt
- ``fixes``: Vorschläge. Ein Vorschlag ändert genau **einen** Wert::

      {"label": "...", "profile": id | None, "path": "entry_delay", "op": "set" | "add" | "remove",
       "value": ..., "weakens": bool}

  ``profile`` = None heißt: allgemeine Einstellung (System). ``weakens`` = der Vorschlag macht
  die Anlage an einer Stelle nachgiebiger (z. B. längere Eingangsverzögerung) – das muss
  ausdrücklich bestätigt werden.

Die Prüfung schaltet nichts und ändert nichts. Was Home Assistant weiß (wer geortet werden kann,
Messwerte der Heimkehr-Beobachtung, Eingangstüren je Profil), kommt als :class:`Facts` herein.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .automation import parse_automation
from .away_proof import parse_proof_settings
from .exit_detection import parse_exit
from .presence_rules import leaves_by_door, parse_presence_rules
from .profiles import profile_ids, profile_info, profile_settings
from .returning import RETURN_AUTO_ONLY, parse_return

ERROR = "error"
WARNING = "warning"
TIP = "tip"
LEVELS = (ERROR, WARNING, TIP)

# So viele Messungen braucht eine Empfehlung, bevor der Assistent sich darauf beruft
MIN_SAMPLES = 3

OP_SET = "set"
OP_ADD = "add"
OP_REMOVE = "remove"


@dataclass(frozen=True)
class Measured:
    """Ein Messwert: nötige Sekunden (mit Puffer), längste Messung und Anzahl Messungen."""

    seconds: int
    longest: int
    count: int


@dataclass(frozen=True)
class Facts:
    """Was nur Home Assistant weiß – für die Prüfung vorab eingesammelt."""

    # Personen mit einer Ortung (Koordinaten) – ohne den unsicheren Beleg „Tür + Signal“
    located: frozenset[str] = frozenset()
    # Personen mit einem Richtungs-Signal („nähert sich“, z. B. Nähe/Proximity)
    direction: frozenset[str] = frozenset()
    # Eingangstüren (Typ Tür) je Profil
    entry_doors: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    # Fenster (Typ Fenster) je Profil – für die Szenario-Vorschau
    windows: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    # Gemessen: nötige Eingangsverzögerung je Tür (Tür auf → unscharf, mit Puffer)
    entry_needed: Mapping[str, Measured] = field(default_factory=dict)
    # Gemessen: nötige Eingangsverzögerung je Person für „Unscharf mit Türbeleg“
    proof_needed: Mapping[str, Measured] = field(default_factory=dict)
    # Eingefrorene Ortungen je Person: Entität -> seit wie vielen Sekunden (0.64.0b5)
    frozen: Mapping[str, Mapping[str, float]] = field(default_factory=dict)
    # Anzeigenamen (Personen, Türen, Ortungen)
    names: Mapping[str, str] = field(default_factory=dict)

    def name(self, entity_id: str) -> str:
        return self.names.get(entity_id, entity_id)


# --- Texte ------------------------------------------------------------------------------------

TEXTS: Mapping[str, Mapping[str, Mapping[str, str]]] = {
    "away_never": {
        "de": {
            "text": "Profil {profile_name}: {person} kann nie als weg erkannt werden – "
            "„Scharf, wenn alle weg“ schaltet dieses Profil nie.",
            "why": "Für {person} gibt es keine Ortung mit Koordinaten, und der unsichere Beleg "
            "„Tür + Signal“ ist für {person} aus. Ohne Beleg gilt niemand als weg – ein "
            "schlafendes Handy soll niemanden abwesend machen.",
        },
        "en": {
            "text": "Profile {profile_name}: {person} can never be detected as away – "
            "“arm when all away” never arms this profile.",
            "why": "There is no location with coordinates for {person}, and the uncertain proof "
            "“door + signal” is off for {person}. Without proof nobody counts as away – a "
            "sleeping phone must not make anyone absent.",
        },
    },
    "away_entity": {
        "de": {
            "text": "Profil {profile_name}: „Scharf, wenn alle weg“ folgt der Entität „{entity}“ "
            "– Hauswacht prüft dabei nicht selbst, ob wirklich alle weg sind.",
            "why": "Zeigt „{entity}“ den Zustand „{state}“, schaltet Hauswacht nach der Wartezeit "
            "scharf – egal, was Handys und Ortungen sagen. Ist jemand zuhause und die Entität "
            "irrt sich, gibt es einen Fehlalarm. Die Prüfung mit Beleg (ein schlafendes Handy "
            "macht niemanden abwesend) gilt hier nicht.",
        },
        "en": {
            "text": "Profile {profile_name}: “arm when all away” follows the entity “{entity}” – "
            "Hauswacht does not check itself whether everyone is really away.",
            "why": "When “{entity}” shows the state “{state}”, Hauswacht arms after the waiting "
            "time – whatever phones and locations say. If someone is home and the entity is "
            "wrong, there is a false alarm. The check with proof (a sleeping phone makes nobody "
            "absent) does not apply here.",
        },
    },
    "return_never": {
        "de": {
            "text": "Profil {profile_name}: „Bei Rückkehr“ greift für {person} nie.",
            "why": "Für {person} gibt es keine Ortung mit Koordinaten, und „Tür + Signal“ ist "
            "aus. {person} gilt deshalb nie als weg – und wer nie weg war, kommt auch nie heim.",
        },
        "en": {
            "text": "Profile {profile_name}: “On return” never applies to {person}.",
            "why": "There is no location with coordinates for {person}, and “door + signal” is "
            "off. {person} therefore never counts as away – and who was never away never "
            "comes home.",
        },
    },
    "auto_only_without_automation": {
        "de": {
            "text": "Profil {profile_name}: „Unscharf, nur wenn automatisch scharf“ greift nie.",
            "why": "Das Profil hat keine Automatik (keine Uhrzeit, kein Zeitplan, kein „Scharf, "
            "wenn alle weg“). Es wird also nie automatisch scharf – und damit bei Rückkehr nie "
            "unscharf.",
        },
        "en": {
            "text": "Profile {profile_name}: “disarm only if armed automatically” never applies.",
            "why": "The profile has no automation (no time, no schedule, no “arm when all "
            "away”). It is never armed automatically – so it is never disarmed on return.",
        },
    },
    "return_without_door": {
        "de": {
            "text": "Profil {profile_name}: „{mode}“ braucht eine Eingangstür – "
            "das Profil hat keine.",
            "why": "Diese Auswahl wartet auf das Öffnen einer Eingangstür (Melder vom Typ Tür in "
            "den Meldergruppen des Profils). Ohne Tür passiert bei Rückkehr nichts.",
        },
        "en": {
            "text": "Profile {profile_name}: “{mode}” needs an entry door – the profile has none.",
            "why": "This option waits for an entry door to open (a sensor of type door in the "
            "profile's sensor groups). Without a door nothing happens on return.",
        },
    },
    "entry_too_short": {
        "de": {
            "text": "Profil {profile_name}: Eingangsverzögerung {delay} s ist kürzer als gemessen "
            "nötig ({needed} s).",
            "why": "An der Tür {door} hat das Unscharfschalten bis zu {longest} s gedauert "
            "({count} Messungen). Mit Puffer sind das {needed} s. Ist die Zeit zu knapp, gibt es "
            "Fehlalarme beim Heimkommen.",
        },
        "en": {
            "text": "Profile {profile_name}: entry delay {delay} s is shorter than measured "
            "({needed} s).",
            "why": "At the door {door} disarming took up to {longest} s ({count} "
            "measurements). With a buffer that is {needed} s. If the time is too short, coming "
            "home causes false alarms.",
        },
    },
    "proof_too_short": {
        "de": {
            "text": "Profil {profile_name}: Eingangsverzögerung {delay} s reicht für den Türbeleg "
            "von {person} nicht ({needed} s).",
            "why": "Das Handy von {person} hat nach dem Öffnen der Tür bis zu {longest} s "
            "gebraucht, um „zuhause“ zu melden ({count} Heimkehrten). Bei „{mode}“ entscheidet "
            "genau dieses Signal – kommt es nach dem Ende der Eingangsverzögerung, gibt es Alarm.",
        },
        "en": {
            "text": "Profile {profile_name}: entry delay {delay} s is too short for the door proof "
            "of {person} ({needed} s).",
            "why": "After the door opened, the phone of {person} took up to {longest} s to "
            "report “home” ({count} homecomings). With “{mode}” exactly this signal decides – "
            "if it comes after the entry delay ends, the alarm goes off.",
        },
    },
    "approach_without_direction": {
        "de": {
            "text": "Profil {profile_name}: „Eingangsverzögerung bei Annäherung“ greift nie.",
            "why": "Keine Person aus „Bei Rückkehr“ hat ein Richtungs-Signal (z. B. Nähe mit "
            "„nähert sich“). Ohne dieses Signal wird die Eingangsverzögerung nie verlängert.",
        },
        "en": {
            "text": "Profile {profile_name}: “entry delay when approaching” never applies.",
            "why": "No person in “On return” has a direction signal (e.g. proximity with "
            "“towards”). Without that signal the entry delay is never extended.",
        },
    },
    "location_frozen": {
        "de": {
            "text": "{person}: Die Ortung „{entity}“ meldet seit {duration} exakt dieselbe "
            "Position außerhalb von Zuhause – Hauswacht zählt sie nicht als Beleg für „weg“.",
            "why": "Eine echte Ortung schwankt immer ein wenig. Exakt gleiche Koordinaten über so "
            "lange Zeit deuten auf einen vorgetäuschten Standort oder eine hängende App hin. "
            "Damit niemand fälschlich als weg gilt (und das Haus scharf wird, obwohl jemand da "
            "ist), ignoriert Hauswacht diese Ortung, bis sie sich wieder bewegt. Ist sie dauerhaft "
            "falsch, nimm sie unter System → Anwesenheit aus den Signalen der Person.",
        },
        "en": {
            "text": "{person}: the location “{entity}” has reported exactly the same position "
            "outside home for {duration} – Hauswacht does not count it as proof of “away”.",
            "why": "A real location always varies a little. Exactly the same coordinates for "
            "that long point to a faked location or a stuck app. So that nobody counts as away "
            "by mistake (and the house is armed while someone is there), Hauswacht ignores this "
            "location until it moves again. If it is permanently wrong, remove it from the "
            "person's signals under System → Presence.",
        },
    },
    "exit_no_inside": {
        "de": {
            "text": "Profil {profile_name}: Die Ausgangserkennung läuft ohne Melder im Haus – auch "
            "ein Einbruch durch die Eingangstür gibt erst nach {m} min Alarm, solange jemand "
            "zuhause ist.",
            "why": "Ohne Melder im Haus kann Hauswacht nicht unterscheiden, ob jemand von innen "
            "kam. Die Nachricht mit „Alarm jetzt“ kommt sofort, die Sirene erst nach der "
            "Wartezeit. Ein Bewegungsmelder im Flur oder an der Treppe oder das Treppenlicht als "
            "„Melder im Haus“ beschränkt die Wartezeit auf Öffnungen von innen.",
        },
        "en": {
            "text": "Profile {profile_name}: exit detection runs without a sensor in the house – "
            "a break-in through the entry door also only gives an alarm after {m} min while "
            "someone is home.",
            "why": "Without a sensor in the house Hauswacht cannot tell whether someone came from "
            "inside. The message with “Alarm now” comes immediately, the siren only after the "
            "waiting time. A motion sensor in the hallway or on the stairs or the stair light as "
            "“sensor in the house” limits the waiting time to openings from inside.",
        },
    },
    "exit_no_delay": {
        "de": {
            "text": "Profil {profile_name}: Die Ausgangserkennung ist an, aber das Profil hat "
            "keine Eingangsverzögerung – sie greift so nie.",
            "why": "Die stille Wartezeit ersetzt die Eingangsverzögerung. Ohne sie löst eine "
            "Eingangstür sofort aus, und es gibt nichts aufzuschieben.",
        },
        "en": {
            "text": "Profile {profile_name}: exit detection is on, but the profile has no entry "
            "delay – so it never applies.",
            "why": "The silent waiting time replaces the entry delay. Without it an entry door "
            "triggers immediately and there is nothing to postpone.",
        },
    },
    "away_persons_ignored": {
        "de": {
            "text": "Profil {profile_name}: Die Personen bei „Scharf, wenn alle weg“ werden "
            "nicht beachtet – es gilt der eigene Auslöser „{entity}“.",
            "why": "Ist ein eigener Auslöser gesetzt, entscheidet nur er, ob in diesem Profil alle "
            "weg sind. Die angehakten Personen ({persons}) und ihre Signale unter Anwesenheit "
            "spielen dafür keine Rolle. Das ist kein Fehler, aber leicht misszuverstehen.",
        },
        "en": {
            "text": "Profile {profile_name}: the persons in “arm when all away” are ignored – the "
            "own trigger “{entity}” applies.",
            "why": "When an own trigger is set, only it decides whether everyone is away in this "
            "profile. The ticked persons ({persons}) and their signals under Presence play no "
            "part in that. This is not an error, but easy to misunderstand.",
        },
    },
    "presence_unused": {
        "de": {
            "text": "{person}: Die Einstellungen unter Anwesenheit wirken zurzeit nirgends.",
            "why": "{person} steht in keinem Profil bei „Scharf, wenn alle weg“ (ohne eigenen "
            "Auslöser) und bei keinem „Bei Rückkehr“, und die Heimkehr-Beobachtung misst "
            "{person} nicht. Signale, Haken und „Weggehen erkennen“ ändern so nichts.",
        },
        "en": {
            "text": "{person}: the settings under Presence currently have no effect anywhere.",
            "why": "{person} is not in “arm when all away” of any profile (without an own "
            "trigger), not in any “On return”, and the homecoming observation does not measure "
            "{person}. Signals, ticks and “detect leaving” therefore change nothing.",
        },
    },
    "weak_not_needed": {
        "de": {
            "text": "{person}: „Tür + Signal“ ist an, obwohl es eine Ortung gibt.",
            "why": "Der unsichere Beleg ist für Personen ohne Ortung gedacht. Mit Ortung reicht "
            "der sichere Beleg; „Tür + Signal“ kann dann ein schlafendes Handy fälschlich als "
            "weg zählen.",
        },
        "en": {
            "text": "{person}: “door + signal” is on although there is a location.",
            "why": "The uncertain proof is meant for persons without a location. With a "
            "location the safe proof is enough; “door + signal” can then count a sleeping "
            "phone as away by mistake.",
        },
    },
}

FIX_TEXTS: Mapping[str, Mapping[str, str]] = {
    "remove_away_person": {
        "de": "{person} aus „Scharf, wenn alle weg“ nehmen",
        "en": "Remove {person} from “arm when all away”",
    },
    "allow_weak": {
        "de": "Für {person} „Tür + Signal“ erlauben (unsicher)",
        "en": "Allow “door + signal” for {person} (uncertain)",
    },
    "remove_return_person": {
        "de": "{person} aus „Bei Rückkehr“ nehmen",
        "en": "Remove {person} from “On return”",
    },
    "set_entry_delay": {
        "de": "Eingangsverzögerung auf {value} s setzen",
        "en": "Set entry delay to {value} s",
    },
    "approach_off": {
        "de": "Verlängerung bei Annäherung ausschalten",
        "en": "Turn off the extension when approaching",
    },
    "clear_away_persons": {
        "de": "Personen bei „Scharf, wenn alle weg“ abwählen (sie werden ohnehin nicht beachtet)",
        "en": "Untick the persons in “arm when all away” (they are ignored anyway)",
    },
    "weak_off": {
        "de": "„Tür + Signal“ für {person} ausschalten",
        "en": "Turn off “door + signal” for {person}",
    },
}

MODE_NAMES: Mapping[str, Mapping[str, str]] = {
    "door": {"de": "Unscharf mit Türbeleg", "en": "Disarm with door proof"},
    "passage": {"de": "Reinlassen", "en": "Let in"},
}


def _lang(language: str) -> str:
    return "de" if language == "de" else "en"


def _fix(  # noqa: PLR0913
    kind: str,
    lang: str,
    *,
    profile: str | None,
    path: str,
    op: str,
    value: Any,
    weakens: bool = False,
    current: Any = None,
    **values: Any,
) -> dict[str, Any]:
    return {
        "label": FIX_TEXTS[kind][lang].format(value=value, **values),
        "profile": profile,
        "path": path,
        "op": op,
        "value": value,
        "current": current,  # bisheriger Wert (nur bei "set") – für die Vorschau „vorher → nachher“
        "weakens": weakens,
    }


def _finding(  # noqa: PLR0913
    code: str,
    level: str,
    lang: str,
    *,
    key: str,
    profile: str | None = None,
    fixes: list[dict[str, Any]] | None = None,
    **values: Any,
) -> dict[str, Any]:
    texts = TEXTS[code][lang]
    return {
        "code": code,
        "key": key,
        "level": level,
        "profile": profile,
        "text": texts["text"].format(**values),
        "why": texts["why"].format(**values),
        "fixes": fixes or [],
    }


# --- Prüfungen je Profil -------------------------------------------------------------------


def _away(
    options: Mapping[str, Any], pid: str, facts: Facts, lang: str, pname: str
) -> list[dict[str, Any]]:
    weak = parse_proof_settings(options).weak | leaves_by_door(options)
    auto = parse_automation(options, pid)
    if auto.away_entity:
        entity_found = [
            _finding(
                "away_entity",
                WARNING,
                lang,
                key=pid,
                profile=pid,
                profile_name=pname,
                entity=facts.name(auto.away_entity),
                state=auto.away_entity_state,
            )
        ]
        if auto.away_persons:
            entity_found.append(
                _finding(
                    "away_persons_ignored",
                    TIP,
                    lang,
                    key=pid,
                    profile=pid,
                    profile_name=pname,
                    entity=facts.name(auto.away_entity),
                    persons=", ".join(facts.name(p) for p in auto.away_persons),
                    fixes=[
                        _fix(
                            "clear_away_persons",
                            lang,
                            profile=pid,
                            path="automation.auto_away_persons",
                            op=OP_SET,
                            value=[],
                            current=list(auto.away_persons),
                        )
                    ],
                )
            )
        return entity_found
    found = []
    for person in auto.away_persons:
        if person in facts.located or person in weak:
            continue
        name = facts.name(person)
        found.append(
            _finding(
                "away_never",
                ERROR,
                lang,
                key=f"{pid}:{person}",
                profile=pid,
                profile_name=pname,
                person=name,
                fixes=[
                    _fix(
                        "remove_away_person",
                        lang,
                        profile=pid,
                        path="automation.auto_away_persons",
                        op=OP_REMOVE,
                        value=person,
                        person=name,
                    ),
                    _fix(
                        "allow_weak",
                        lang,
                        profile=None,
                        path="away_proof_weak",
                        op=OP_ADD,
                        value=person,
                        weakens=True,
                        person=name,
                    ),
                ],
            )
        )
    return found


def _return(
    options: Mapping[str, Any], pid: str, facts: Facts, lang: str, pname: str
) -> list[dict[str, Any]]:
    back = parse_return(options, pid)
    if not back.active:
        return []
    found: list[dict[str, Any]] = []
    weak = parse_proof_settings(options).weak | leaves_by_door(options)
    for person in back.persons:
        if person in facts.located or person in weak:
            continue
        name = facts.name(person)
        found.append(
            _finding(
                "return_never",
                WARNING,
                lang,
                key=f"{pid}:{person}",
                profile=pid,
                profile_name=pname,
                person=name,
                fixes=[
                    _fix(
                        "remove_return_person",
                        lang,
                        profile=pid,
                        path="return.persons",
                        op=OP_REMOVE,
                        value=person,
                        person=name,
                    ),
                    _fix(
                        "allow_weak",
                        lang,
                        profile=None,
                        path="away_proof_weak",
                        op=OP_ADD,
                        value=person,
                        weakens=True,
                        person=name,
                    ),
                ],
            )
        )
    if back.mode == RETURN_AUTO_ONLY and not parse_automation(options, pid).enabled:
        found.append(
            _finding(
                "auto_only_without_automation",
                ERROR,
                lang,
                key=pid,
                profile=pid,
                profile_name=pname,
            )
        )
    if back.with_door and not facts.entry_doors.get(pid):
        found.append(
            _finding(
                "return_without_door",
                ERROR,
                lang,
                key=pid,
                profile=pid,
                profile_name=pname,
                mode=MODE_NAMES[back.mode][lang],
            )
        )
    if back.extends and not any(p in facts.direction for p in back.persons):
        found.append(
            _finding(
                "approach_without_direction",
                WARNING,
                lang,
                key=pid,
                profile=pid,
                profile_name=pname,
                fixes=[
                    _fix(
                        "approach_off",
                        lang,
                        profile=pid,
                        path="return.approach_delay",
                        op=OP_SET,
                        value=0,
                        current=back.approach_delay,
                    )
                ],
            )
        )
    return found


def _exit(options: Mapping[str, Any], pid: str, lang: str, pname: str) -> list[dict[str, Any]]:
    """Ausgangserkennung (ADR 0014): ohne Eingangsverzögerung wirkungslos, ohne Melder im Haus
    verzögert sie auch einen Einbruch."""
    config = parse_exit(options, pid)
    if not config.enabled:
        return []
    if not profile_settings(options, pid)["entry_delay"]:
        return [_finding("exit_no_delay", ERROR, lang, key=pid, profile=pid, profile_name=pname)]
    if not config.inside:
        return [
            _finding(
                "exit_no_inside",
                WARNING,
                lang,
                key=pid,
                profile=pid,
                profile_name=pname,
                m=config.wait,
            )
        ]
    return []


def _delays(
    options: Mapping[str, Any], pid: str, facts: Facts, lang: str, pname: str
) -> list[dict[str, Any]]:
    delay = profile_settings(options, pid)["entry_delay"]
    found: list[dict[str, Any]] = []
    doors = [
        (door, m)
        for door in facts.entry_doors.get(pid, ())
        if (m := facts.entry_needed.get(door)) is not None and m.count >= MIN_SAMPLES
    ]
    if doors:
        door, measured = max(doors, key=lambda d: d[1].seconds)
        if measured.seconds > delay:
            found.append(
                _finding(
                    "entry_too_short",
                    WARNING,
                    lang,
                    key=pid,
                    profile=pid,
                    profile_name=pname,
                    delay=delay,
                    needed=measured.seconds,
                    longest=measured.longest,
                    count=measured.count,
                    door=facts.name(door),
                    fixes=[
                        _fix(
                            "set_entry_delay",
                            lang,
                            profile=pid,
                            path="entry_delay",
                            op=OP_SET,
                            value=measured.seconds,
                            weakens=True,
                            current=delay,
                        )
                    ],
                )
            )
    back = parse_return(options, pid)
    if not back.with_door or not facts.entry_doors.get(pid):
        return found
    persons = [
        (p, m)
        for p in back.persons
        if (m := facts.proof_needed.get(p)) is not None and m.count >= MIN_SAMPLES
    ]
    if not persons:
        return found
    person, measured = max(persons, key=lambda p: p[1].seconds)
    if measured.seconds > delay:
        found.append(
            _finding(
                "proof_too_short",
                WARNING,
                lang,
                key=pid,
                profile=pid,
                profile_name=pname,
                delay=delay,
                needed=measured.seconds,
                longest=measured.longest,
                count=measured.count,
                person=facts.name(person),
                mode=MODE_NAMES[back.mode][lang],
                fixes=[
                    _fix(
                        "set_entry_delay",
                        lang,
                        profile=pid,
                        path="entry_delay",
                        op=OP_SET,
                        value=measured.seconds,
                        weakens=True,
                        current=delay,
                    )
                ],
            )
        )
    return found


def _duration(seconds: float, lang: str) -> str:
    hours = int(seconds // 3600)
    if hours < 48:
        return f"{hours} Stunden" if lang == "de" else f"{hours} hours"
    days = hours // 24
    return f"{days} Tagen" if lang == "de" else f"{days} days"


def _frozen(facts: Facts, lang: str) -> list[dict[str, Any]]:
    return [
        _finding(
            "location_frozen",
            WARNING,
            lang,
            key=entity,
            person=facts.name(person),
            entity=facts.name(entity),
            duration=_duration(seconds, lang),
        )
        for person in sorted(facts.frozen)
        for entity, seconds in sorted(facts.frozen[person].items())
    ]


USE_AWAY = "away"  # „Scharf, wenn alle weg“
USE_AWAY_IGNORED = "away_ignored"  # angehakt, aber das Profil hat einen eigenen Auslöser
USE_RETURN = "return"  # „Bei Rückkehr“
USE_OBSERVE = "observe"  # Heimkehr-Beobachtung


def person_uses(options: Mapping[str, Any], person: str) -> list[tuple[str, str | None]]:
    """Wofür die Anwesenheit einer Person zählt: (Art, Profil-ID oder None)."""
    uses: list[tuple[str, str | None]] = []
    for pid in profile_ids(options):
        auto = parse_automation(options, pid)
        if person in auto.away_persons:
            uses.append((USE_AWAY_IGNORED if auto.away_entity else USE_AWAY, pid))
        back = parse_return(options, pid)
        if back.active and person in back.persons:
            uses.append((USE_RETURN, pid))
    observed = options.get("homecoming_persons", [])
    if options.get("homecoming_observe") and isinstance(observed, list) and person in observed:
        uses.append((USE_OBSERVE, None))
    return uses


def _configured_persons(options: Mapping[str, Any]) -> list[str]:
    """Personen, für die unter Anwesenheit etwas eingestellt ist (Signale oder Regeln)."""
    signals = options.get("homecoming_signals", {})
    found = [p for p, e in signals.items() if e] if isinstance(signals, Mapping) else []
    found.extend(parse_presence_rules(options))
    return sorted({p for p in found if isinstance(p, str)})


def _system(options: Mapping[str, Any], facts: Facts, lang: str) -> list[dict[str, Any]]:
    found = _frozen(facts, lang)
    for person in _configured_persons(options):
        if any(kind != USE_AWAY_IGNORED for kind, _pid in person_uses(options, person)):
            continue
        found.append(_finding("presence_unused", TIP, lang, key=person, person=facts.name(person)))
    for person in sorted(parse_proof_settings(options).weak):
        if person not in facts.located:
            continue
        name = facts.name(person)
        found.append(
            _finding(
                "weak_not_needed",
                TIP,
                lang,
                key=person,
                person=name,
                fixes=[
                    _fix(
                        "weak_off",
                        lang,
                        profile=None,
                        path="away_proof_weak",
                        op=OP_REMOVE,
                        value=person,
                        person=name,
                    )
                ],
            )
        )
    return found


def advise(options: Mapping[str, Any], facts: Facts, language: str = "de") -> list[dict[str, Any]]:
    """Alle Befunde: Fehler zuerst, dann Warnungen, dann Tipps."""
    lang = _lang(language)
    found: list[dict[str, Any]] = []
    for pid in profile_ids(options):
        pname = profile_info(options, pid).name
        found.extend(_away(options, pid, facts, lang, pname))
        found.extend(_return(options, pid, facts, lang, pname))
        found.extend(_delays(options, pid, facts, lang, pname))
        found.extend(_exit(options, pid, lang, pname))
    found.extend(_system(options, facts, lang))
    return sorted(found, key=lambda f: LEVELS.index(f["level"]))


def errors(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Nur die Fehler – die stehen auch in den Prüfhinweisen."""
    return [f for f in findings if f["level"] == ERROR]


# --- Vorschlag übernehmen (Check-up) -----------------------------------------------------------

FIX_KEYS = ("profile", "path", "op", "value")


def find_fix(
    findings: list[dict[str, Any]], wanted: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    """Den Vorschlag unter den **aktuellen** Befunden suchen.

    Übernommen wird nur, was der Assistent gerade selbst vorschlägt – so lässt sich über diesen
    Weg nichts anderes ändern, und ein veralteter Vorschlag (inzwischen behoben) greift nicht.
    """
    for finding in findings:
        for fix in finding["fixes"]:
            if all(fix.get(k) == wanted.get(k) for k in FIX_KEYS):
                return finding, fix
    return None


def patch(target: dict[str, Any], path: str, op: str, value: Any) -> None:
    """Einen Vorschlag in ein Formular (Profil oder Anwesenheit) eintragen: ``a.b`` = Pfad."""
    *parents, last = path.split(".")
    node = target
    for key in parents:
        child = node.get(key)
        if not isinstance(child, dict):
            child = {}
            node[key] = child
        node = child
    if op == OP_SET:
        node[last] = value
        return
    items = [v for v in node.get(last) or [] if v != value]
    if op == OP_ADD:
        items.append(value)
    node[last] = items
