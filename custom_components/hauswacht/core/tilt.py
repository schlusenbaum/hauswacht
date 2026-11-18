"""Melder mit Kippstellung (rein, ohne Home Assistant) – siehe ADR 0010.

Ein Melder mit Kippstellung meldet drei Stellungen: zu, gekippt, offen. Quelle ist der Zustand
einer Entität (z. B. ``sensor.fenster_opening_state`` mit ``open``/``tilted``/``closed`` oder ein
``input_select``) oder ein Attribut (z. B. ``window_state`` eines Fenstergriffs).

Zwei Schritte:

1. :func:`position` bildet den Rohwert auf ``on`` (offen), ``off`` (zu), ``tilted`` (gekippt)
   oder nicht verfügbar ab. Unbekannte Werte zählen sicherheitshalber als **offen**.
2. :func:`judge` bewertet die Stellung im aktiven Profil: Erlaubt das Profil gekippte Fenster,
   wird ``tilted`` zu ``off``, sonst zu ``on``. Alles danach arbeitet wie bisher mit on/off.
"""

from __future__ import annotations

import copy
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from .sensor_types import NOT_AVAILABLE_STATES, OFF, ON, UNAVAILABLE, SensorType, parse_types

TILTED = "tilted"

# Stellung -> Wert im Ereignisfeld ``position``
POSITION_NAMES = {ON: "open", OFF: "closed", TILTED: "tilted"}

OPT_TILT_SENSORS = "tilt_sensors"

# Vorschläge für die Zuordnung (Groß-/Kleinschreibung egal)
KNOWN_CLOSED = frozenset({"closed", "close", "geschlossen", "zu"})
KNOWN_TILTED = frozenset({"tilted", "tilt", "gekippt", "kippstellung"})

# Domains, deren Zustand als Stellung taugt (Attribute gehen bei jeder Entität)
STATE_DOMAINS: tuple[str, ...] = ("sensor", "input_select", "select")


@dataclass(frozen=True)
class TiltSource:
    entity_id: str
    attribute: str | None = None
    closed: frozenset[str] = frozenset()
    tilted: frozenset[str] = frozenset()


def _fold(value: Any) -> str:
    return str(value).strip().casefold()


def parse_tilt_sources(options: Mapping[str, Any]) -> dict[str, TiltSource]:
    raw = options.get(OPT_TILT_SENSORS, {})
    result: dict[str, TiltSource] = {}
    if not isinstance(raw, Mapping):
        return result
    for entity_id, data in raw.items():
        if not isinstance(data, Mapping) or "." not in str(entity_id):
            continue
        attribute = data.get("attribute")
        result[str(entity_id)] = TiltSource(
            entity_id=str(entity_id),
            attribute=str(attribute) if attribute else None,
            closed=frozenset(_fold(v) for v in data.get("closed", []) or []),
            tilted=frozenset(_fold(v) for v in data.get("tilted", []) or []),
        )
    return result


def raw_value(
    source: TiltSource, state: str | None, attributes: Mapping[str, Any] | None
) -> str | None:
    """Rohwert der Quelle: Zustand oder Attribut. None = Entität fehlt."""
    if state is None:
        return None
    if state in NOT_AVAILABLE_STATES:
        return UNAVAILABLE if state == "" else state
    if source.attribute is None:
        return state
    value = (attributes or {}).get(source.attribute)
    if value is None or str(value) == "":
        return UNAVAILABLE  # Attribut fehlt: lieber "nicht verfügbar" als "zu"
    return str(value)


def position(
    source: TiltSource, state: str | None, attributes: Mapping[str, Any] | None = None
) -> str | None:
    """Stellung: ``on`` (offen), ``off`` (zu), ``tilted``, ``unavailable``/``unknown`` oder None."""
    value = raw_value(source, state, attributes)
    if value is None:
        return None
    if value in NOT_AVAILABLE_STATES or value == UNAVAILABLE:
        return value
    folded = _fold(value)
    if folded in source.closed:
        return OFF
    if folded in source.tilted:
        return TILTED
    return ON  # unbekannt oder offen: sichere Seite


def judge(value: str | None, *, tilt_allowed: bool) -> str | None:
    """Stellung im Profil bewerten: gekippt -> zu (erlaubt) oder offen."""
    if value == TILTED:
        return OFF if tilt_allowed else ON
    return value


def known_values(
    state: str | None, attributes: Mapping[str, Any] | None, attribute: str | None
) -> list[str]:
    """Mögliche Werte einer Quelle (für den Zuordnungsdialog), in Reihenfolge, ohne Doppelte."""
    attributes = attributes or {}
    values: list[str] = []
    if attribute is None:
        options = attributes.get("options")
        if isinstance(options, list | tuple):
            values += [str(o) for o in options]
        if state is not None and state not in NOT_AVAILABLE_STATES:
            values.append(state)
    else:
        current = attributes.get(attribute)
        if current is not None and str(current) != "":
            values.append(str(current))
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if _fold(value) not in seen:
            seen.add(_fold(value))
            unique.append(value)
    return unique


def suggest(values: Iterable[str]) -> tuple[list[str], list[str]]:
    """Vorschlag: (Werte für zu, Werte für gekippt). Der Rest zählt als offen."""
    closed = [v for v in values if _fold(v) in KNOWN_CLOSED]
    tilted = [v for v in values if _fold(v) in KNOWN_TILTED]
    return closed, tilted


def looks_like_tilt(values: Iterable[str]) -> bool:
    """Erkennt eine Quelle mit Kippstellung (Assistent): zu und gekippt kommen vor."""
    folded = {_fold(v) for v in values}
    return bool(folded & KNOWN_CLOSED) and bool(folded & KNOWN_TILTED)


def save_tilt_source(
    options: Mapping[str, Any],
    entity_id: str,
    *,
    attribute: str | None,
    closed: Iterable[str],
    tilted: Iterable[str],
) -> dict[str, Any]:
    """Neue Optionen mit einem (geänderten) Melder mit Kippstellung."""
    closed_list = sorted({str(v) for v in closed}, key=str.casefold)
    tilted_list = sorted({str(v) for v in tilted} - set(closed_list), key=str.casefold)
    if not closed_list:
        raise ValueError("no_closed_value")
    new = copy.deepcopy(dict(options))
    sources = dict(new.get(OPT_TILT_SENSORS, {}) or {})
    sources[entity_id] = {
        "attribute": attribute or None,
        "closed": closed_list,
        "tilted": tilted_list,
    }
    new[OPT_TILT_SENSORS] = dict(sorted(sources.items()))
    return new


def delete_tilt_source(options: Mapping[str, Any], entity_id: str) -> dict[str, Any]:
    """Melder mit Kippstellung entfernen – auch aus Meldergruppen und Immer aktiv."""
    new = copy.deepcopy(dict(options))
    sources = dict(new.get(OPT_TILT_SENSORS, {}) or {})
    sources.pop(entity_id, None)
    new[OPT_TILT_SENSORS] = sources
    zones = new.get("zones", {})
    if isinstance(zones, Mapping):
        for zone in zones.values():
            if isinstance(zone, dict) and isinstance(zone.get("entities"), list):
                zone["entities"] = [e for e in zone["entities"] if e != entity_id]
    always = new.get("always_active")
    if isinstance(always, dict) and isinstance(always.get("sensors"), list):
        always["sensors"] = [e for e in always["sensors"] if e != entity_id]
    types = new.get("sensor_types")
    if isinstance(types, dict):
        types.pop(entity_id, None)
    return new


def types_with_tilt(options: Mapping[str, Any]) -> dict[str, SensorType]:
    """Gewählte Typen; Melder mit Kippstellung ohne eigene Wahl sind Fenster."""
    types = parse_types(options)
    for entity_id in parse_tilt_sources(options):
        types.setdefault(entity_id, SensorType.WINDOW)
    return types
