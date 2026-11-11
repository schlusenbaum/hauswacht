"""Bedingungen für Auslöseregeln ("nur wenn …").

Rein und ohne Home Assistant: Zustände kommen über eine Funktion ``get(entity_id)``, die
``(state, attributes)`` oder ``None`` (gibt es nicht) liefert.

Grundsatz **sichere Seite**: Lässt sich eine Bedingung nicht auswerten (Entität fehlt, ist
``unavailable``/``unknown`` oder liefert keine Zahl), gilt die Bedingung als **erfüllt** – im
Zweifel löst die Regel also aus. Das gilt für den Gesamtausdruck; ``not`` dreht ein
"unbekannt" nicht in "falsch" um.

Formate (wie im YAML-Editor):

- ``time:    {after: "22:00", before: "06:00", weekdays: [mon, tue, …]}``
- ``state:   {entity: switch.x, is: "on"}``          (``is`` auch als Liste)
- ``numeric: {entity: sensor.t, above: 5, below: 30, attribute: temperature}``
- ``person:  {entity: person.niklas, in: home}``      (``home``, ``not_home`` oder ``zone.xyz``)
- ``and: [...]``, ``or: [...]``, ``not: {...}``
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, time
from typing import Any

UNKNOWN_STATES = frozenset({"unavailable", "unknown", ""})
WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
KINDS = ("time", "state", "numeric", "person", "and", "or", "not")

StateGetter = Callable[[str], tuple[str, Mapping[str, Any]] | None]


class ConditionError(ValueError):
    """Bedingung ist falsch aufgebaut (Text nennt die Stelle)."""


def _parse_time(value: Any, where: str) -> time:
    try:
        hours, minutes = str(value).split(":")[:2]
        return time(int(hours), int(minutes))
    except (ValueError, TypeError) as err:
        raise ConditionError(f"{where}: Uhrzeit wie 22:00 erwartet, nicht {value!r}") from err


def _number(value: Any, where: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as err:
        raise ConditionError(f"{where}: Zahl erwartet, nicht {value!r}") from err


def _entity(data: Mapping[str, Any], where: str, domain: str | None = None) -> str:
    entity = data.get("entity")
    if not isinstance(entity, str) or "." not in entity:
        raise ConditionError(f"{where}: 'entity' fehlt oder ist keine Entitäts-ID")
    if domain and not entity.startswith(f"{domain}."):
        raise ConditionError(f"{where}: {entity} ist keine {domain}-Entität")
    return entity


def check(condition: Any, where: str = "Bedingung") -> None:
    """Aufbau prüfen; wirft ConditionError mit Fundstelle."""
    if not isinstance(condition, Mapping) or len(condition) != 1:
        raise ConditionError(f"{where}: genau eine Art erwartet ({', '.join(KINDS)})")
    kind, body = next(iter(condition.items()))
    here = f"{where} ({kind})"
    if kind in ("and", "or"):
        if not isinstance(body, list) or not body:
            raise ConditionError(f"{here}: Liste von Bedingungen erwartet")
        for number, item in enumerate(body, start=1):
            check(item, f"{here} {number}")
        return
    if kind == "not":
        check(body, here)
        return
    if not isinstance(body, Mapping):
        raise ConditionError(f"{here}: Angaben fehlen")
    allowed = {
        "time": {"after", "before", "weekdays"},
        "state": {"entity", "is"},
        "numeric": {"entity", "above", "below", "attribute"},
        "person": {"entity", "in"},
    }.get(kind)
    if allowed is None:
        raise ConditionError(f"{where}: unbekannte Art {kind!r} ({', '.join(KINDS)})")
    unknown = set(body) - allowed
    if unknown:
        raise ConditionError(f"{here}: unbekannte Angabe(n) {', '.join(sorted(unknown))}")
    if kind == "time":
        if not ({"after", "before", "weekdays"} & set(body)):
            raise ConditionError(f"{here}: 'after', 'before' oder 'weekdays' angeben")
        for key in ("after", "before"):
            if key in body:
                _parse_time(body[key], f"{here} {key}")
        days = body.get("weekdays", [])
        if not isinstance(days, list) or any(d not in WEEKDAYS for d in days):
            raise ConditionError(f"{here}: weekdays aus {', '.join(WEEKDAYS)}")
    elif kind == "state":
        _entity(body, here)
        if "is" not in body:
            raise ConditionError(f"{here}: 'is' fehlt")
    elif kind == "numeric":
        _entity(body, here)
        if "above" not in body and "below" not in body:
            raise ConditionError(f"{here}: 'above' und/oder 'below' angeben")
        for key in ("above", "below"):
            if key in body:
                _number(body[key], f"{here} {key}")
    elif kind == "person":
        _entity(body, here, "person")
        where_to = body.get("in")
        if not isinstance(where_to, str) or not (
            where_to in ("home", "not_home") or where_to.startswith("zone.")
        ):
            raise ConditionError(f"{here}: 'in' muss home, not_home oder zone.… sein")


def entities(condition: Mapping[str, Any]) -> set[str]:
    """Alle Entitäten, die eine Bedingung liest."""
    kind, body = next(iter(condition.items()))
    if kind in ("and", "or"):
        return set().union(*(entities(c) for c in body))
    if kind == "not":
        return entities(body)
    found = {body["entity"]} if isinstance(body, Mapping) and "entity" in body else set()
    if kind == "person" and str(body.get("in", "")).startswith("zone."):
        found.add(body["in"])
    return found


def _time_ok(body: Mapping[str, Any], now: datetime) -> bool:
    days = body.get("weekdays")
    if days and WEEKDAYS[now.weekday()] not in days:
        return False
    current = now.time()
    after = _parse_time(body["after"], "after") if "after" in body else None
    before = _parse_time(body["before"], "before") if "before" in body else None
    if after and before:
        if after <= before:
            return after <= current < before
        return current >= after or current < before  # über Mitternacht
    if after:
        return current >= after
    if before:
        return current < before
    return True


def evaluate(condition: Mapping[str, Any], get: StateGetter, now: datetime) -> bool | None:
    """True/False, oder None = lässt sich nicht auswerten."""
    kind, body = next(iter(condition.items()))
    if kind == "and":
        results = [evaluate(c, get, now) for c in body]
        if False in results:
            return False
        return None if None in results else True
    if kind == "or":
        results = [evaluate(c, get, now) for c in body]
        if True in results:
            return True
        return None if None in results else False
    if kind == "not":
        inner = evaluate(body, get, now)
        return None if inner is None else not inner
    if kind == "time":
        return _time_ok(body, now)
    found = get(body["entity"])
    if found is None or found[0] in UNKNOWN_STATES:
        return None
    state, attributes = found
    if kind == "state":
        wanted = body["is"]
        options = [str(w) for w in wanted] if isinstance(wanted, list) else [str(wanted)]
        return state in options
    if kind == "numeric":
        raw = attributes.get(body["attribute"]) if "attribute" in body else state
        try:
            value = float(raw)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None
        if "above" in body and not value > float(body["above"]):
            return False
        return not ("below" in body and not value < float(body["below"]))
    if kind == "person":
        target = str(body["in"])
        if target in ("home", "not_home"):
            return state == target if target == "home" else state != "home"
        zone = get(target)
        if zone is None:
            return None
        return state == str(zone[1].get("friendly_name", target))
    return None


def all_met(conditions: Sequence[Mapping[str, Any]], get: StateGetter, now: datetime) -> bool:
    """Alle Bedingungen erfüllt? Unbekannt zählt als erfüllt (sichere Seite)."""
    if not conditions:
        return True
    return evaluate({"and": list(conditions)}, get, now) is not False


def describe(condition: Mapping[str, Any], name: Callable[[str], str], german: bool = True) -> str:
    kind, body = next(iter(condition.items()))
    word = {"and": " und " if german else " and ", "or": " oder " if german else " or "}
    if kind in word:
        return "(" + word[kind].join(describe(c, name, german) for c in body) + ")"
    if kind == "not":
        return ("nicht " if german else "not ") + describe(body, name, german)
    if kind == "time":
        parts = []
        if "after" in body or "before" in body:
            parts.append(f"{body.get('after', '00:00')}–{body.get('before', '24:00')}")
        if body.get("weekdays"):
            parts.append(",".join(body["weekdays"]))
        return " ".join(parts)
    entity = name(body["entity"])
    if kind == "state":
        wanted = body["is"]
        shown = "/".join(map(str, wanted)) if isinstance(wanted, list) else str(wanted)
        return f"{entity} = {shown}"
    if kind == "numeric":
        bounds = []
        if "above" in body:
            bounds.append(f"> {body['above']}")
        if "below" in body:
            bounds.append(f"< {body['below']}")
        return f"{entity} {' und '.join(bounds) if german else ' and '.join(bounds)}"
    target = str(body["in"])
    places = {"home": "zuhause" if german else "home", "not_home": "weg" if german else "away"}
    return f"{entity} in {places.get(target) or name(target)}"
