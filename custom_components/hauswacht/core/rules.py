"""Regeln: Alarm erst bei einer Abfolge von Meldern ("Tür, dann Keller").

Rein und ohne Home Assistant. Eine Regel besteht aus Schritten. Jeder Schritt nennt Melder
(einzelne Sensoren und/oder Zonen) und eine Art:

- ``any``   – einer davon löst aus,
- ``all``   – alle davon lösen aus (Reihenfolge innerhalb des Schritts egal),
- ``count`` – mindestens N verschiedene davon lösen aus.

Die Zeit an einem Schritt ist die Zeit bis zum nächsten Schritt: Der nächste Schritt muss
innerhalb dieser Sekunden nach dem vorigen vollständig erfüllt sein. Beim ersten Schritt mit
``all``/``count`` gilt sie zusätzlich dafür, wie nah die Melder des Schritts beieinander liegen.

Regeln sind mit ODER verknüpft: Eine Regel kann einen Alarm nur auslösen, nie den Alarm einer
anderen Regel verhindern. Ergebnis einer erfüllten Regel ist ``alarm`` (sofort) oder
``entry_delay`` (Eingangsverzögerung des Profils, dann Alarm).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .sensors import Zone, resolve_zone

MAX_STEPS = 10
DEFAULT_WITHIN = 60
MAX_WITHIN = 3600
MAX_HISTORY_AGE = 2 * MAX_WITHIN * MAX_STEPS
MAX_HISTORY = 500


class StepMode(StrEnum):
    ANY = "any"
    ALL = "all"
    COUNT = "count"


class RuleResult(StrEnum):
    ALARM = "alarm"
    ENTRY_DELAY = "entry_delay"


@dataclass(frozen=True)
class Step:
    sensors: frozenset[str] = frozenset()
    zones: tuple[str, ...] = ()
    mode: StepMode = StepMode.ANY
    count: int = 2
    within: int = DEFAULT_WITHIN


@dataclass(frozen=True)
class Rule:
    rule_id: str
    name: str
    steps: tuple[Step, ...]
    result: RuleResult = RuleResult.ALARM


# --- Einlesen ----------------------------------------------------------------


def _int(value: Any, default: int, low: int, high: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return min(max(number, low), high)


def parse_step(data: Mapping[str, Any]) -> Step:
    sensors = data.get("sensors", [])
    zones = data.get("zones", [])
    try:
        mode = StepMode(str(data.get("mode", StepMode.ANY)))
    except ValueError:
        mode = StepMode.ANY
    return Step(
        sensors=frozenset(s for s in sensors if isinstance(s, str))
        if isinstance(sensors, list)
        else frozenset(),
        zones=tuple(z for z in zones if isinstance(z, str)) if isinstance(zones, list) else (),
        mode=mode,
        count=_int(data.get("count"), 2, 1, 99),
        within=_int(data.get("within"), DEFAULT_WITHIN, 1, MAX_WITHIN),
    )


def parse_rules(options: Mapping[str, Any]) -> dict[str, Rule]:
    raw = options.get("rules", {})
    rules: dict[str, Rule] = {}
    if not isinstance(raw, Mapping):
        return rules
    for rule_id, data in raw.items():
        if not isinstance(data, Mapping):
            continue
        steps_raw = data.get("steps", [])
        steps = (
            tuple(parse_step(s) for s in steps_raw if isinstance(s, Mapping))
            if isinstance(steps_raw, list)
            else ()
        )
        try:
            result = RuleResult(str(data.get("result", RuleResult.ALARM)))
        except ValueError:
            result = RuleResult.ALARM
        rules[str(rule_id)] = Rule(
            rule_id=str(rule_id),
            name=str(data.get("name") or rule_id),
            steps=tuple(s for s in steps if s.sensors or s.zones)[:MAX_STEPS],
            result=result,
        )
    return rules


def profile_rule_ids(options: Mapping[str, Any], profile_id: str) -> list[str]:
    """Regeln, die ein Profil verwendet (Reihenfolge wie gespeichert)."""
    profiles = options.get("profiles", {})
    profile = profiles.get(profile_id, {}) if isinstance(profiles, Mapping) else {}
    raw = profile.get("rules", []) if isinstance(profile, Mapping) else []
    return [r for r in raw if isinstance(r, str)] if isinstance(raw, list) else []


def step_members(
    step: Step, zones: Mapping[str, Zone], labels: Mapping[str, frozenset[str]]
) -> frozenset[str]:
    members = set(step.sensors)
    for zone_id in step.zones:
        if (zone := zones.get(zone_id)) is not None:
            members |= resolve_zone(zone, labels)
    return frozenset(members)


def rule_members(
    rule: Rule, zones: Mapping[str, Zone], labels: Mapping[str, frozenset[str]]
) -> list[frozenset[str]]:
    return [step_members(step, zones, labels) for step in rule.steps]


def _needed(step: Step, members: frozenset[str]) -> int:
    if step.mode is StepMode.ALL:
        return len(members)
    if step.mode is StepMode.COUNT:
        return step.count
    return 1


# --- Prüfung -----------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    code: str
    rule: str  # Name der Regel
    step: int | None = None  # 1-basiert
    detail: str = ""


def validate_rule(rule: Rule, members: Sequence[frozenset[str]]) -> list[Finding]:
    """Fehler, die das Speichern verhindern: die Regel könnte nie (sinnvoll) auslösen."""
    errors: list[Finding] = []
    if not rule.steps:
        return [Finding("rule_no_steps", rule.name)]
    for number, (step, mine) in enumerate(zip(rule.steps, members, strict=True), start=1):
        if not mine:
            errors.append(Finding("rule_step_empty", rule.name, number))
            continue
        if step.mode is StepMode.COUNT and step.count > len(mine):
            errors.append(
                Finding("rule_count_too_high", rule.name, number, f"{step.count}/{len(mine)}")
            )
    for number in range(1, len(members)):
        if members[number - 1] & members[number]:
            errors.append(Finding("rule_same_sensor_next_step", rule.name, number + 1))
    return errors


def profile_findings(
    single: frozenset[str],
    rules: Sequence[Rule],
    members: Mapping[str, Sequence[frozenset[str]]],
) -> list[Finding]:
    """Hinweise (Speichern trotzdem möglich): Regeln, die im Profil nichts bewirken."""
    findings: list[Finding] = []
    for rule in rules:
        mine = members.get(rule.rule_id, [])
        if not rule.steps or not mine:
            continue
        first = mine[0]
        if rule.steps[0].mode is StepMode.ANY and first and first <= single:
            findings.append(Finding("rule_redundant_single", rule.name))
        elif len(rule.steps) == 1 and rule.steps[0].mode is StepMode.ANY:
            findings.append(Finding("rule_single_step_any", rule.name))
    for shorter in rules:
        for longer in rules:
            if shorter is longer or len(shorter.steps) >= len(longer.steps):
                continue
            if _is_prefix(shorter, longer, members):
                findings.append(Finding("rule_contained", longer.name, detail=shorter.name))
    return findings


def _is_prefix(
    shorter: Rule, longer: Rule, members: Mapping[str, Sequence[frozenset[str]]]
) -> bool:
    short_members = members.get(shorter.rule_id, [])
    long_members = members.get(longer.rule_id, [])
    for index, step in enumerate(shorter.steps):
        other = longer.steps[index]
        if (step.mode, step.count) != (other.mode, other.count):
            return False
        if short_members[index] != long_members[index]:
            return False
        if index < len(shorter.steps) - 1 and step.within < other.within:
            return False
    return True


# --- Auswertung --------------------------------------------------------------


@dataclass(frozen=True)
class Trigger:
    index: int
    sensor: str
    at: float


@dataclass(frozen=True)
class Progress:
    rule_id: str
    done: int  # erfüllte Schritte
    total: int
    deadline: float  # bis dahin muss der nächste Schritt kommen
    first_sensor: str


def _completions(
    step: Step,
    mine: frozenset[str],
    triggers: Sequence[Trigger],
    previous: Sequence[Trigger] | None,
    window: int,
) -> list[Trigger]:
    """Auslösungen, mit denen der Schritt vollständig erfüllt ist.

    ``previous`` = Erfüllungen des vorigen Schritts (None beim ersten), ``window`` = Zeit
    vom vorigen Schritt bis hierher (beim ersten Schritt: Abstand der Melder untereinander).
    """
    need = _needed(step, mine)
    done: list[Trigger] = []
    candidates = [t for t in triggers if t.sensor in mine]
    for current in candidates:
        if previous is None:
            if need == 1:
                done.append(current)
                continue
            seen = {
                t.sensor
                for t in candidates
                if t.index <= current.index and current.at - t.at <= window
            }
            if len(seen) >= need:
                done.append(current)
            continue
        for before in previous:
            if before.index >= current.index or current.at - before.at > window:
                continue
            seen = {t.sensor for t in candidates if before.index < t.index <= current.index}
            if len(seen) >= need:
                done.append(current)
                break
    return done


@dataclass
class RuleEngine:
    rules: tuple[Rule, ...] = ()
    members: dict[str, list[frozenset[str]]] = field(default_factory=dict)
    triggers: list[Trigger] = field(default_factory=list)
    _next: int = 0

    def watched(self) -> frozenset[str]:
        sensors: set[str] = set()
        for mine in self.members.values():
            for step in mine:
                sensors |= step
        return frozenset(sensors)

    def reset(self) -> None:
        self.triggers.clear()

    def _prune(self, now: float) -> None:
        self.triggers = [t for t in self.triggers if now - t.at <= MAX_HISTORY_AGE][-MAX_HISTORY:]

    def _chain(self, rule: Rule) -> list[list[Trigger]]:
        """Erfüllungen je Schritt (Liste pro Schritt)."""
        mine = self.members.get(rule.rule_id, [])
        result: list[list[Trigger]] = []
        previous: list[Trigger] | None = None
        for number, step in enumerate(rule.steps):
            window = rule.steps[number - 1].within if number else step.within
            done = _completions(step, mine[number], self.triggers, previous, window)
            result.append(done)
            if not done:
                break
            previous = done
        return result

    def record(self, sensor: str, now: float) -> list[Rule]:
        """Auslösung merken; liefert die Regeln, die genau damit erfüllt sind."""
        if sensor not in self.watched():
            return []
        self._prune(now)
        trigger = Trigger(index=self._next, sensor=sensor, at=now)
        self._next += 1
        self.triggers.append(trigger)
        fired = []
        for rule in self.rules:
            chain = self._chain(rule)
            if len(chain) == len(rule.steps) and any(t.index == trigger.index for t in chain[-1]):
                fired.append(rule)
        return fired

    def progress(self, now: float) -> dict[str, Progress]:
        """Regeln, die teilweise erfüllt sind und noch erfüllt werden können."""
        found: dict[str, Progress] = {}
        for rule in self.rules:
            chain = self._chain(rule)
            for number in range(len(chain) - 1, -1, -1):
                done = chain[number]
                if not done or number >= len(rule.steps) - 1:
                    continue
                latest = max(done, key=lambda t: t.at)
                deadline = latest.at + rule.steps[number].within
                if deadline > now:
                    first = chain[0][0].sensor if chain and chain[0] else latest.sensor
                    found[rule.rule_id] = Progress(
                        rule_id=rule.rule_id,
                        done=number + 1,
                        total=len(rule.steps),
                        deadline=deadline,
                        first_sensor=first,
                    )
                    break
        return found


def build_engine(
    rules: Iterable[Rule], zones: Mapping[str, Zone], labels: Mapping[str, frozenset[str]]
) -> RuleEngine:
    chosen = tuple(rules)
    return RuleEngine(
        rules=chosen,
        members={rule.rule_id: rule_members(rule, zones, labels) for rule in chosen},
    )


# --- Migration ---------------------------------------------------------------


def migrate_zone_confirmation(options: Mapping[str, Any]) -> dict[str, Any]:
    """0.18.0: Zonen-Option "zweiter Melder bestätigt" -> Regel "mindestens 2 verschiedene".

    Profile, die die Zone überwacht haben, bekommen statt der Zone die Regel.
    """
    new = dict(options)
    zones = {k: dict(v) for k, v in options.get("zones", {}).items() if isinstance(v, Mapping)}
    rules = {k: dict(v) for k, v in options.get("rules", {}).items() if isinstance(v, Mapping)}
    profiles = {
        k: dict(v) for k, v in options.get("profiles", {}).items() if isinstance(v, Mapping)
    }
    for zone_id, zone in zones.items():
        confirm = zone.pop("confirm", False)
        window = zone.pop("confirm_window", 120)
        if not confirm:
            continue
        rule_id = f"bestaetigung_{zone_id}"
        rules[rule_id] = {
            "name": f"Bestätigung {zone.get('name') or zone_id}",
            "steps": [
                {"zones": [zone_id], "mode": "count", "count": 2, "within": window},
            ],
            "result": "alarm",
        }
        for profile in profiles.values():
            if zone_id in profile.get("zones", []):
                profile["zones"] = [z for z in profile["zones"] if z != zone_id]
                profile["rules"] = [*profile.get("rules", []), rule_id]
    new["zones"] = zones
    new["rules"] = rules
    new["profiles"] = profiles
    return new


# --- Klartext ----------------------------------------------------------------

_TEXT = {
    "de": {
        "or": " / ",
        "and": " und ",
        "one_of": "eine(r) von {m}",
        "all_of": "{m} (alle, beliebige Reihenfolge)",
        "count_of": "mindestens {n} verschiedene von {m}",
        "zone": "Zone {z}",
        "then": ", dann innerhalb von {s} s ",
        "alarm": "sofort Alarm",
        "entry_delay": "Eingangsverzögerung, dann Alarm",
        "empty": "(noch keine Schritte)",
    },
    "en": {
        "or": " / ",
        "and": " and ",
        "one_of": "one of {m}",
        "all_of": "{m} (all, any order)",
        "count_of": "at least {n} different of {m}",
        "zone": "zone {z}",
        "then": ", then within {s} s ",
        "alarm": "alarm immediately",
        "entry_delay": "entry delay, then alarm",
        "empty": "(no steps yet)",
    },
}


def describe_step(
    step: Step,
    sensor_name: Callable[[str], str],
    zone_name: Callable[[str], str],
    language: str = "de",
) -> str:
    text = _TEXT.get(language, _TEXT["en"])
    parts = [sensor_name(s) for s in sorted(step.sensors)]
    parts += [text["zone"].format(z=zone_name(z)) for z in step.zones]
    single_zone = not step.sensors and len(step.zones) == 1
    if step.mode is StepMode.ALL and len(parts) > 1:
        return text["all_of"].format(m=text["and"].join(parts))
    if step.mode is StepMode.COUNT:
        return text["count_of"].format(n=step.count, m=text["or"].join(parts))
    if len(parts) == 1 or single_zone:
        return parts[0] if parts else "–"
    return text["one_of"].format(m=text["or"].join(parts))


def describe_rule(
    rule: Rule,
    sensor_name: Callable[[str], str],
    zone_name: Callable[[str], str],
    language: str = "de",
) -> str:
    """Die Regel als ein Satz, z. B. "Tür hinten, dann innerhalb von 120 s Zone Keller → …"."""
    text = _TEXT.get(language, _TEXT["en"])
    if not rule.steps:
        return text["empty"]
    sentence = describe_step(rule.steps[0], sensor_name, zone_name, language)
    for previous, step in zip(rule.steps, rule.steps[1:], strict=False):
        sentence += text["then"].format(s=previous.within)
        sentence += describe_step(step, sensor_name, zone_name, language)
    return f"{sentence} → {text[rule.result.value]}"
