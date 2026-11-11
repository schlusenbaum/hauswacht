"""Auslöseregeln: Alarm erst bei einer Abfolge von Meldern ("Tür, dann Keller").

Rein und ohne Home Assistant.

**Aufbau.** Eine Regel besteht aus Schritten, die nacheinander erfüllt sein müssen. Jeder
Schritt ist ein Ausdruck:

- ``any: [...]``            – einer davon (ODER),
- ``all: [...]``            – alle davon, Reihenfolge egal (UND),
- ``count: N, of: [...]``   – mindestens N davon.

Einträge sind ``sensor: binary_sensor.x``, ``group: <Meldergruppe>`` oder wieder ein Ausdruck
(Verschachtelung). Eine **Meldergruppe steht für ihre einzelnen Melder**: ``any: [group: Keller]``
heißt "irgendein Kellermelder", ``all: [group: Fenster]`` "alle Fenster", ``count: 2, of:
[group: Keller]`` "zwei verschiedene Kellermelder".

Die Zeit an einem Schritt (``within``) ist die Zeit bis zum nächsten Schritt. Beim ersten
Schritt mit mehreren nötigen Meldern gilt sie zusätzlich dafür, wie nah diese beieinander liegen.

**Zusätze.** ``unless`` (ein Ausdruck mit ``before``): Die Regel gilt nicht, wenn dieser
Ausdruck in den ``before`` Sekunden vor Schritt 1 erfüllt war. ``conditions``: Die Regel gilt nur,
wenn alle Bedingungen erfüllt sind (siehe conditions.py; unbekannt = erfüllt). Ergebnis
``alarm``, ``entry_delay`` oder ``notify`` (nur Benachrichtigung).

Regeln sind mit ODER verknüpft: ``unless`` und ``conditions`` wirken nur auf die eigene Regel.
Eine Regel kann einen Alarm also nie verhindern, den eine andere Regel auslöst.

**Speicherform.** Meldergruppen werden intern per ID gespeichert (Umbenennen ist folgenlos),
im YAML-Editor per Name angezeigt. Die alte Speicherform aus 0.19 (``sensors``/``zones``/
``mode``/``count``) wird weiter gelesen.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from . import conditions as cond
from .sensors import Zone, resolve_zone

MAX_STEPS = 10
DEFAULT_WITHIN = 60
MAX_WITHIN = 3600
MAX_UNLESS = 24 * 3600
LONG_UNLESS = 1800
MAX_DEPTH = 5
MAX_HISTORY_AGE = 2 * MAX_WITHIN * MAX_STEPS + MAX_UNLESS
MAX_HISTORY = 1000


class StepMode(StrEnum):
    ANY = "any"
    ALL = "all"
    COUNT = "count"


class RuleResult(StrEnum):
    ALARM = "alarm"
    ENTRY_DELAY = "entry_delay"
    NOTIFY = "notify"


STRICTNESS = {RuleResult.ALARM: 2, RuleResult.ENTRY_DELAY: 1, RuleResult.NOTIFY: 0}


# --- Ausdrücke ---------------------------------------------------------------


@dataclass(frozen=True)
class Item:
    kind: str  # "sensor" oder "group"
    ref: str


@dataclass(frozen=True)
class Expr:
    mode: StepMode
    items: tuple[Item | Expr, ...]
    count: int = 1


@dataclass(frozen=True)
class Step:
    expr: Expr
    within: int = DEFAULT_WITHIN


@dataclass(frozen=True)
class Unless:
    expr: Expr
    before: int


@dataclass(frozen=True)
class Rule:
    rule_id: str
    name: str
    steps: tuple[Step, ...]
    result: RuleResult = RuleResult.ALARM
    unless: Unless | None = None
    conditions: tuple[Mapping[str, Any], ...] = ()


class RuleError(ValueError):
    """Regel falsch aufgebaut (Text nennt die Stelle)."""


def _int(value: Any, default: int, low: int, high: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return min(max(number, low), high)


def _parse_items(raw: Any, where: str, depth: int) -> tuple[Item | Expr, ...]:
    if not isinstance(raw, list) or not raw:
        raise RuleError(f"{where}: Liste von Einträgen erwartet")
    items: list[Item | Expr] = []
    for number, entry in enumerate(raw, start=1):
        here = f"{where}, Eintrag {number}"
        if not isinstance(entry, Mapping):
            raise RuleError(f"{here}: 'sensor:', 'group:' oder any/all/count erwartet")
        if "sensor" in entry and len(entry) == 1:
            if not isinstance(entry["sensor"], str) or "." not in entry["sensor"]:
                raise RuleError(f"{here}: Entitäts-ID erwartet")
            items.append(Item("sensor", entry["sensor"]))
        elif "group" in entry and len(entry) == 1:
            items.append(Item("group", str(entry["group"])))
        else:
            items.append(parse_expr(entry, here, depth + 1))
    return tuple(items)


def parse_expr(data: Mapping[str, Any], where: str = "Ausdruck", depth: int = 0) -> Expr:
    """``{any: [...]}``, ``{all: [...]}`` oder ``{count: N, of: [...]}`` (weitere Schlüssel
    wie ``within``/``before`` werden ignoriert)."""
    if depth > MAX_DEPTH:
        raise RuleError(f"{where}: zu tief verschachtelt (höchstens {MAX_DEPTH} Ebenen)")
    kinds = [k for k in ("any", "all", "count") if k in data]
    if len(kinds) != 1:
        raise RuleError(f"{where}: genau eines von any, all oder count erwartet")
    kind = kinds[0]
    if kind == "count":
        try:
            count = int(data["count"])
        except (TypeError, ValueError) as err:
            raise RuleError(f"{where}: count muss eine Zahl sein") from err
        if count < 1:
            raise RuleError(f"{where}: count muss mindestens 1 sein")
        return Expr(StepMode.COUNT, _parse_items(data.get("of"), f"{where} (of)", depth), count)
    return Expr(StepMode(kind), _parse_items(data[kind], f"{where} ({kind})", depth))


def expr_to_data(expr: Expr) -> dict[str, Any]:
    items = [
        {item.kind: item.ref} if isinstance(item, Item) else expr_to_data(item)
        for item in expr.items
    ]
    if expr.mode is StepMode.COUNT:
        return {"count": expr.count, "of": items}
    return {expr.mode.value: items}


def _legacy_step(data: Mapping[str, Any]) -> Step:
    """Speicherform aus 0.19: sensors/zones/mode/count."""
    sensors = [s for s in data.get("sensors", []) or [] if isinstance(s, str)]
    zones = [z for z in data.get("zones", []) or [] if isinstance(z, str)]
    items = tuple([Item("sensor", s) for s in sorted(sensors)] + [Item("group", z) for z in zones])
    try:
        mode = StepMode(str(data.get("mode", StepMode.ANY)))
    except ValueError:
        mode = StepMode.ANY
    count = _int(data.get("count"), 2, 1, 99) if mode is StepMode.COUNT else 1
    return Step(Expr(mode, items, count), _int(data.get("within"), DEFAULT_WITHIN, 1, MAX_WITHIN))


def parse_step(data: Mapping[str, Any], where: str = "Schritt") -> Step:
    if "sensors" in data or "zones" in data or "mode" in data:
        return _legacy_step(data)
    within = _int(data.get("within"), DEFAULT_WITHIN, 1, MAX_WITHIN)
    return Step(parse_expr(data, where), within)


def step_to_data(step: Step) -> dict[str, Any]:
    return {**expr_to_data(step.expr), "within": step.within}


def parse_rule(rule_id: str, data: Mapping[str, Any]) -> Rule:
    """Gespeicherte Regel einlesen; wirft RuleError bei kaputtem Aufbau."""
    steps_raw = data.get("steps", [])
    if not isinstance(steps_raw, list):
        raise RuleError("steps: Liste erwartet")
    steps = []
    for number, raw in enumerate(steps_raw, start=1):
        if not isinstance(raw, Mapping):
            raise RuleError(f"Schritt {number}: any/all/count erwartet")
        step = parse_step(raw, f"Schritt {number}")
        if step.expr.items:
            steps.append(step)
    try:
        result = RuleResult(str(data.get("result", RuleResult.ALARM)))
    except ValueError as err:
        raise RuleError("result: alarm, entry_delay oder notify") from err
    unless = None
    raw_unless = data.get("unless")
    if raw_unless:
        if not isinstance(raw_unless, Mapping) or "before" not in raw_unless:
            raise RuleError("unless: Ausdruck mit 'before' (Sekunden) erwartet")
        unless = Unless(
            parse_expr(raw_unless, "unless"), _int(raw_unless["before"], 300, 1, MAX_UNLESS)
        )
    conditions = data.get("conditions") or []
    if not isinstance(conditions, list):
        raise RuleError("conditions: Liste erwartet")
    for number, condition in enumerate(conditions, start=1):
        try:
            cond.check(condition, f"Bedingung {number}")
        except cond.ConditionError as err:
            raise RuleError(str(err)) from err
    return Rule(
        rule_id=rule_id,
        name=str(data.get("name") or rule_id),
        steps=tuple(steps)[:MAX_STEPS],
        result=result,
        unless=unless,
        conditions=tuple(conditions),
    )


def rule_to_data(rule: Rule) -> dict[str, Any]:
    data: dict[str, Any] = {
        "name": rule.name,
        "result": rule.result.value,
        "steps": [step_to_data(s) for s in rule.steps],
    }
    if rule.unless:
        data["unless"] = {**expr_to_data(rule.unless.expr), "before": rule.unless.before}
    if rule.conditions:
        data["conditions"] = [dict(c) for c in rule.conditions]
    return data


def parse_rules(options: Mapping[str, Any]) -> dict[str, Rule]:
    """Alle gespeicherten Regeln; kaputte werden übersprungen."""
    raw = options.get("rules", {})
    rules: dict[str, Rule] = {}
    if not isinstance(raw, Mapping):
        return rules
    for rule_id, data in raw.items():
        if not isinstance(data, Mapping):
            continue
        try:
            rules[str(rule_id)] = parse_rule(str(rule_id), data)
        except RuleError:
            continue
    return rules


def profile_rule_ids(options: Mapping[str, Any], profile_id: str) -> list[str]:
    """Regeln, die ein Profil verwendet (Reihenfolge wie gespeichert)."""
    profiles = options.get("profiles", {})
    profile = profiles.get(profile_id, {}) if isinstance(profiles, Mapping) else {}
    raw = profile.get("rules", []) if isinstance(profile, Mapping) else []
    return [r for r in raw if isinstance(r, str)] if isinstance(raw, list) else []


# --- Meldergruppen auflösen --------------------------------------------------


def resolve_expr(
    expr: Expr, zones: Mapping[str, Zone], labels: Mapping[str, frozenset[str]]
) -> Expr:
    """Meldergruppen durch ihre einzelnen Melder ersetzen (nur noch ``sensor``-Einträge)."""
    items: list[Item | Expr] = []
    seen: set[str] = set()
    for item in expr.items:
        if isinstance(item, Expr):
            items.append(resolve_expr(item, zones, labels))
            continue
        if item.kind == "sensor":
            sensors: Iterable[str] = [item.ref]
        else:
            zone = zones.get(item.ref)
            sensors = sorted(resolve_zone(zone, labels)) if zone else []
        for sensor in sensors:
            if sensor not in seen:
                seen.add(sensor)
                items.append(Item("sensor", sensor))
    return Expr(expr.mode, tuple(items), expr.count)


def leaves(expr: Expr) -> frozenset[str]:
    found: set[str] = set()
    for item in expr.items:
        found |= leaves(item) if isinstance(item, Expr) else {item.ref}
    return frozenset(found)


def satisfied(expr: Expr, fired: frozenset[str] | set[str]) -> bool:
    if not expr.items:
        return False
    hits = sum(
        1
        for item in expr.items
        if (satisfied(item, fired) if isinstance(item, Expr) else item.ref in fired)
    )
    if expr.mode is StepMode.ANY:
        return hits >= 1
    if expr.mode is StepMode.ALL:
        return hits == len(expr.items)
    return hits >= expr.count


@dataclass(frozen=True)
class Resolved:
    """Regel mit aufgelösten Meldergruppen."""

    rule: Rule
    steps: tuple[Expr, ...]
    unless: Expr | None


def resolve_rule(
    rule: Rule, zones: Mapping[str, Zone], labels: Mapping[str, frozenset[str]]
) -> Resolved:
    return Resolved(
        rule=rule,
        steps=tuple(resolve_expr(s.expr, zones, labels) for s in rule.steps),
        unless=resolve_expr(rule.unless.expr, zones, labels) if rule.unless else None,
    )


def rule_members(
    rule: Rule, zones: Mapping[str, Zone], labels: Mapping[str, frozenset[str]]
) -> list[frozenset[str]]:
    """Melder je Schritt (für Anzeige und Prüfung)."""
    return [leaves(e) for e in resolve_rule(rule, zones, labels).steps]


# --- Prüfung -----------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    code: str
    rule: str  # Name der Regel
    step: int | None = None  # 1-basiert
    detail: str = ""


def _count_errors(expr: Expr, rule: str, step: int | None) -> list[Finding]:
    errors = []
    if expr.mode is StepMode.COUNT and expr.count > len(expr.items):
        errors.append(Finding("rule_count_too_high", rule, step, f"{expr.count}/{len(expr.items)}"))
    for item in expr.items:
        if isinstance(item, Expr):
            if not item.items:
                errors.append(Finding("rule_step_empty", rule, step))
            errors += _count_errors(item, rule, step)
    return errors


def validate_rule(
    rule: Rule, zones: Mapping[str, Zone], labels: Mapping[str, frozenset[str]]
) -> list[Finding]:
    """Fehler, die das Speichern verhindern: die Regel könnte nie (sinnvoll) auslösen."""
    if not rule.steps:
        return [Finding("rule_no_steps", rule.name)]
    resolved = resolve_rule(rule, zones, labels)
    errors: list[Finding] = []
    members = [leaves(e) for e in resolved.steps]
    for number, expr in enumerate(resolved.steps, start=1):
        if not members[number - 1]:
            errors.append(Finding("rule_step_empty", rule.name, number))
            continue
        errors += _count_errors(expr, rule.name, number)
    for number in range(1, len(members)):
        if members[number - 1] & members[number]:
            errors.append(Finding("rule_same_sensor_next_step", rule.name, number + 1))
    if resolved.unless is not None:
        if not leaves(resolved.unless):
            errors.append(Finding("rule_unless_empty", rule.name))
        else:
            errors += _count_errors(resolved.unless, rule.name, None)
    return errors


def profile_findings(
    single: frozenset[str],
    rules: Sequence[Rule],
    zones: Mapping[str, Zone],
    labels: Mapping[str, frozenset[str]],
) -> list[Finding]:
    """Hinweise (Speichern trotzdem möglich): Regeln, die im Profil nichts bewirken."""
    findings: list[Finding] = []
    resolved = {r.rule_id: resolve_rule(r, zones, labels) for r in rules}
    for rule in rules:
        res = resolved[rule.rule_id]
        if not res.steps:
            continue
        first = res.steps[0]
        if first.mode is StepMode.ANY and leaves(first) and leaves(first) <= single:
            findings.append(Finding("rule_redundant_single", rule.name))
        elif len(res.steps) == 1 and first.mode is StepMode.ANY and not rule.conditions:
            findings.append(Finding("rule_single_step_any", rule.name))
        if res.unless is not None and leaves(res.unless) & leaves(first):
            findings.append(Finding("rule_unless_overlaps", rule.name))
        if rule.unless is not None and rule.unless.before > LONG_UNLESS:
            findings.append(Finding("rule_unless_long", rule.name, detail=str(rule.unless.before)))
    for shorter in rules:
        for longer in rules:
            if shorter is longer or len(shorter.steps) >= len(longer.steps):
                continue
            if shorter.unless or shorter.conditions:
                continue
            if _is_prefix(resolved[shorter.rule_id], resolved[longer.rule_id]):
                findings.append(Finding("rule_contained", longer.name, detail=shorter.name))
    return findings


def _is_prefix(shorter: Resolved, longer: Resolved) -> bool:
    for index, expr in enumerate(shorter.steps):
        if expr != longer.steps[index]:
            return False
        if (
            index < len(shorter.steps) - 1
            and shorter.rule.steps[index].within < longer.rule.steps[index].within
        ):
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


Completion = tuple[Trigger, frozenset[int]]  # Erfüllung und mögliche Starts (Schritt 1)


def _completions(
    expr: Expr,
    triggers: Sequence[Trigger],
    previous: Sequence[Completion] | None,
    window: int,
) -> list[Completion]:
    mine = leaves(expr)
    candidates = [t for t in triggers if t.sensor in mine]
    done: list[Completion] = []
    for current in candidates:
        if previous is None:
            fired = {
                t.sensor
                for t in candidates
                if t.index <= current.index and current.at - t.at <= window
            }
            if satisfied(expr, fired):
                done.append((current, frozenset({current.index})))
            continue
        starts: set[int] = set()
        for before, before_starts in previous:
            if before.index >= current.index or current.at - before.at > window:
                continue
            fired = {t.sensor for t in candidates if before.index < t.index <= current.index}
            if satisfied(expr, fired):
                starts |= before_starts
        if starts:
            done.append((current, frozenset(starts)))
    return done


@dataclass
class RuleEngine:
    rules: tuple[Rule, ...] = ()
    resolved: dict[str, Resolved] = field(default_factory=dict)
    triggers: list[Trigger] = field(default_factory=list)
    _next: int = 0

    @property
    def members(self) -> dict[str, list[frozenset[str]]]:
        return {rid: [leaves(e) for e in res.steps] for rid, res in self.resolved.items()}

    def watched(self) -> frozenset[str]:
        sensors: set[str] = set()
        for res in self.resolved.values():
            for expr in res.steps:
                sensors |= leaves(expr)
            if res.unless is not None:
                sensors |= leaves(res.unless)
        return frozenset(sensors)

    def reset(self) -> None:
        self.triggers.clear()

    def _prune(self, now: float) -> None:
        self.triggers = [t for t in self.triggers if now - t.at <= MAX_HISTORY_AGE][-MAX_HISTORY:]

    def _chain(self, rule: Rule) -> list[list[Completion]]:
        res = self.resolved[rule.rule_id]
        result: list[list[Completion]] = []
        previous: list[Completion] | None = None
        for number, expr in enumerate(res.steps):
            window = rule.steps[number - 1].within if number else rule.steps[0].within
            done = _completions(expr, self.triggers, previous, window)
            result.append(done)
            if not done:
                break
            previous = done
        return result

    def _blocked(self, rule: Rule, start: Trigger) -> bool:
        res = self.resolved[rule.rule_id]
        if res.unless is None or rule.unless is None:
            return False
        before = rule.unless.before
        fired = {
            t.sensor for t in self.triggers if start.at - before <= t.at and t.index < start.index
        }
        return satisfied(res.unless, fired)

    def _by_index(self, index: int) -> Trigger | None:
        return next((t for t in self.triggers if t.index == index), None)

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
            if len(chain) != len(rule.steps):
                continue
            for completion, starts in chain[-1]:
                if completion.index != trigger.index:
                    continue
                if any(
                    (start := self._by_index(s)) is not None and not self._blocked(rule, start)
                    for s in starts
                ):
                    fired.append(rule)
                    break
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
                latest = max((c for c, _ in done), key=lambda t: t.at)
                deadline = latest.at + rule.steps[number].within
                if deadline > now:
                    first = chain[0][0][0].sensor if chain and chain[0] else latest.sensor
                    found[rule.rule_id] = Progress(
                        rule_id=rule.rule_id,
                        done=number + 1,
                        total=len(rule.steps),
                        deadline=deadline,
                        first_sensor=first,
                    )
                    break
        return found

    def blocked_until(self, rule: Rule, now: float) -> float | None:
        """Sperrt ``unless`` die Regel gerade? Dann bis wann (ungefähr)."""
        res = self.resolved.get(rule.rule_id)
        if res is None or res.unless is None or rule.unless is None:
            return None
        recent = [t for t in self.triggers if now - t.at < rule.unless.before]
        if not satisfied(res.unless, {t.sensor for t in recent}):
            return None
        mine = leaves(res.unless)
        return max(t.at for t in recent if t.sensor in mine) + rule.unless.before


def build_engine(
    rules: Iterable[Rule], zones: Mapping[str, Zone], labels: Mapping[str, frozenset[str]]
) -> RuleEngine:
    chosen = tuple(rules)
    return RuleEngine(
        rules=chosen,
        resolved={rule.rule_id: resolve_rule(rule, zones, labels) for rule in chosen},
    )


# --- YAML-Editor -------------------------------------------------------------

EDITABLE_KEYS = {"name", "result", "steps", "unless", "conditions"}
STEP_KEYS = {"any", "all", "count", "of", "within"}


def _items_with_names(data: Any, zone_name: Callable[[str], str]) -> Any:
    if isinstance(data, list):
        return [_items_with_names(d, zone_name) for d in data]
    if isinstance(data, Mapping):
        if set(data) == {"group"}:
            return {"group": zone_name(str(data["group"]))}
        return {k: _items_with_names(v, zone_name) for k, v in data.items()}
    return data


def _items_with_ids(data: Any, zone_id: Mapping[str, str], where: str) -> Any:
    if isinstance(data, list):
        return [_items_with_ids(d, zone_id, where) for d in data]
    if isinstance(data, Mapping):
        if set(data) == {"group"}:
            name = str(data["group"])
            found = zone_id.get(name.casefold())
            if found is None:
                raise RuleError(f"{where}: Meldergruppe {name!r} gibt es nicht")
            return {"group": found}
        return {k: _items_with_ids(v, zone_id, where) for k, v in data.items()}
    return data


def to_editable(rule: Rule, zone_name: Callable[[str], str]) -> dict[str, Any]:
    """Regel für den YAML-Editor (Meldergruppen per Name)."""
    data = rule_to_data(rule)
    data["steps"] = [_items_with_names(s, zone_name) for s in data["steps"]]
    if "unless" in data:
        data["unless"] = _items_with_names(data["unless"], zone_name)
    return data


def from_editable(
    data: Any, zones: Mapping[str, Zone], rule_id: str = "regel"
) -> tuple[Rule, dict[str, Any]]:
    """YAML aus dem Editor -> (Regel, Speicherform). Wirft RuleError mit Fundstelle."""
    if not isinstance(data, Mapping):
        raise RuleError("Die Regel muss ein Objekt mit name, result und steps sein")
    unknown = set(data) - EDITABLE_KEYS
    if unknown:
        raise RuleError(f"Unbekannte Angabe(n): {', '.join(sorted(map(str, unknown)))}")
    name = str(data.get("name") or "").strip()
    if not name:
        raise RuleError("name fehlt")
    zone_id = {z.name.casefold(): z.zone_id for z in zones.values()}
    steps = data.get("steps")
    if not isinstance(steps, list) or not steps:
        raise RuleError("steps: mindestens ein Schritt erwartet")
    if len(steps) > MAX_STEPS:
        raise RuleError(f"steps: höchstens {MAX_STEPS} Schritte")
    for number, step in enumerate(steps, start=1):
        if not isinstance(step, Mapping):
            raise RuleError(f"Schritt {number}: any/all/count erwartet")
        extra = set(step) - STEP_KEYS
        if extra:
            raise RuleError(f"Schritt {number}: unbekannte Angabe(n) {', '.join(sorted(extra))}")
    stored = {
        "name": name,
        "result": data.get("result", RuleResult.ALARM.value),
        "steps": [
            _items_with_ids(s, zone_id, f"Schritt {n}") for n, s in enumerate(steps, start=1)
        ],
    }
    if data.get("unless"):
        stored["unless"] = _items_with_ids(data["unless"], zone_id, "unless")
    if data.get("conditions"):
        stored["conditions"] = data["conditions"]
    rule = parse_rule(rule_id, stored)
    if len(rule.steps) != len(steps):
        raise RuleError("Ein Schritt ist leer")
    return rule, rule_to_data(rule)


# --- Assistent ---------------------------------------------------------------


def step_form(step: Step) -> dict[str, Any] | None:
    """Schritt als Formularfelder des Assistenten, oder None (nur als YAML bearbeitbar)."""
    if any(isinstance(i, Expr) for i in step.expr.items):
        return None
    return {
        "sensors": [i.ref for i in step.expr.items if isinstance(i, Item) and i.kind == "sensor"],
        "zones": [i.ref for i in step.expr.items if isinstance(i, Item) and i.kind == "group"],
        "mode": step.expr.mode.value,
        "count": step.expr.count if step.expr.mode is StepMode.COUNT else 2,
        "within": step.within,
    }


def step_from_form(data: Mapping[str, Any]) -> dict[str, Any]:
    items = [{"sensor": s} for s in data.get("sensors") or []]
    items += [{"group": z} for z in data.get("zones") or []]
    mode = str(data.get("mode") or StepMode.ANY.value)
    within = _int(data.get("within"), DEFAULT_WITHIN, 1, MAX_WITHIN)
    if mode == StepMode.COUNT.value:
        return {"count": _int(data.get("count"), 2, 1, 99), "of": items, "within": within}
    return {mode: items, "within": within}


def wizard_editable(rule: Rule) -> bool:
    """Lässt sich die Regel im Assistenten bearbeiten? (keine Verschachtelung)"""
    flat = all(step_form(s) is not None for s in rule.steps)
    unless_flat = rule.unless is None or (
        rule.unless.expr.mode is StepMode.ANY
        and not any(isinstance(i, Expr) for i in rule.unless.expr.items)
    )
    return flat and unless_flat


# --- Klartext ----------------------------------------------------------------

_TEXT = {
    "de": {
        "or": " / ",
        "and": " und ",
        "one_of": "eine(r) von {m}",
        "all_of": "{m} (alle, beliebige Reihenfolge)",
        "count_of": "mindestens {n} von {m}",
        "zone": "Meldergruppe {z}",
        "then": ", dann innerhalb von {s} s ",
        "alarm": "sofort Alarm",
        "entry_delay": "Eingangsverzögerung, dann Alarm",
        "notify": "nur Benachrichtigung",
        "unless": " – nicht, wenn in den {s} s davor {m}",
        "only_if": " – nur wenn {c}",
        "empty": "(noch keine Schritte)",
    },
    "en": {
        "or": " / ",
        "and": " and ",
        "one_of": "one of {m}",
        "all_of": "{m} (all, any order)",
        "count_of": "at least {n} of {m}",
        "zone": "group {z}",
        "then": ", then within {s} s ",
        "alarm": "alarm immediately",
        "entry_delay": "entry delay, then alarm",
        "notify": "notification only",
        "unless": " – not if within the {s} s before {m}",
        "only_if": " – only if {c}",
        "empty": "(no steps yet)",
    },
}


def describe_expr(
    expr: Expr,
    sensor_name: Callable[[str], str],
    zone_name: Callable[[str], str],
    language: str = "de",
) -> str:
    text = _TEXT.get(language, _TEXT["en"])
    parts = []
    for item in expr.items:
        if isinstance(item, Expr):
            parts.append("(" + describe_expr(item, sensor_name, zone_name, language) + ")")
        elif item.kind == "sensor":
            parts.append(sensor_name(item.ref))
        else:
            parts.append(text["zone"].format(z=zone_name(item.ref)))
    if not parts:
        return "–"
    if expr.mode is StepMode.ALL and len(parts) > 1:
        return text["all_of"].format(m=text["and"].join(parts))
    if expr.mode is StepMode.COUNT:
        return text["count_of"].format(n=expr.count, m=text["or"].join(parts))
    if len(parts) == 1:
        return parts[0]
    return text["one_of"].format(m=text["or"].join(parts))


def describe_step(
    step: Step,
    sensor_name: Callable[[str], str],
    zone_name: Callable[[str], str],
    language: str = "de",
) -> str:
    return describe_expr(step.expr, sensor_name, zone_name, language)


def describe_rule(
    rule: Rule,
    sensor_name: Callable[[str], str],
    zone_name: Callable[[str], str],
    language: str = "de",
) -> str:
    """Die Regel als ein Satz, z. B. "Tür hinten, dann innerhalb von 120 s … → …"."""
    text = _TEXT.get(language, _TEXT["en"])
    if not rule.steps:
        return text["empty"]
    sentence = describe_step(rule.steps[0], sensor_name, zone_name, language)
    for previous, step in zip(rule.steps, rule.steps[1:], strict=False):
        sentence += text["then"].format(s=previous.within)
        sentence += describe_step(step, sensor_name, zone_name, language)
    sentence += f" → {text[rule.result.value]}"
    if rule.unless:
        sentence += text["unless"].format(
            s=rule.unless.before,
            m=describe_expr(rule.unless.expr, sensor_name, zone_name, language),
        )
    if rule.conditions:
        german = language == "de"
        joined = (" und " if german else " and ").join(
            cond.describe(c, sensor_name, german) for c in rule.conditions
        )
        sentence += text["only_if"].format(c=joined)
    return sentence


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
