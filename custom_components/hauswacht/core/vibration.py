"""Erschütterungsmelder (rein, ohne Home Assistant) – ADR 0010 Teil B.

- Melder vom Typ **Erschütterung** lösen sofort aus, blockieren das Scharfschalten aber nie:
  Erschütterung ist ein Vorgang, kein offener Zustand.
- **Fehlalarmschutz je Meldergruppe:** Alarm erst bei N Meldungen eines Melders innerhalb von
  S Sekunden (Standard 1 Meldung – empfohlen 2 in 60 s).
- **Erschütterungsstärke als Zahl:** Ein Zahlensensor (oder ``input_number`` zum Testen) mit
  Schwelle wird direkt zum Erschütterungsmelder – jede Meldung über der Schwelle zählt.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .sensor_types import NOT_AVAILABLE_STATES, OFF, ON, UNAVAILABLE

OPT_VIBRATION_SOURCES = "vibration_sources"

DEFAULT_COUNT = 1
RECOMMENDED_COUNT = 2
MAX_COUNT = 5
DEFAULT_WINDOW = 60
RECOMMENDED_WINDOW = 60
MIN_WINDOW = 5
MAX_WINDOW = 600

# Domains für die Stärke als Zahl
STRENGTH_DOMAINS: tuple[str, ...] = ("sensor", "input_number", "number")


@dataclass(frozen=True)
class VibrationSource:
    entity_id: str
    threshold: float


@dataclass(frozen=True)
class VibrationRule:
    """Fehlalarmschutz einer Meldergruppe."""

    count: int = DEFAULT_COUNT
    window: int = DEFAULT_WINDOW


def parse_vibration_sources(options: Mapping[str, Any]) -> dict[str, VibrationSource]:
    raw = options.get(OPT_VIBRATION_SOURCES, {})
    result: dict[str, VibrationSource] = {}
    if not isinstance(raw, Mapping):
        return result
    for entity_id, data in raw.items():
        if not isinstance(data, Mapping) or "." not in str(entity_id):
            continue
        try:
            threshold = float(data.get("threshold"))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
        result[str(entity_id)] = VibrationSource(entity_id=str(entity_id), threshold=threshold)
    return result


def strength(state: str | None) -> float | None:
    """Zahl aus dem Zustand; None, wenn keine Zahl."""
    if state is None or state in NOT_AVAILABLE_STATES:
        return None
    try:
        return float(state)
    except ValueError:
        return None


def position(source: VibrationSource, state: str | None) -> str | None:
    """Stellung: ``on`` (über der Schwelle), ``off``, nicht verfügbar oder None (fehlt)."""
    if state is None:
        return None
    if state in NOT_AVAILABLE_STATES:
        return UNAVAILABLE if state == "" else state
    value = strength(state)
    if value is None:
        return UNAVAILABLE  # keine Zahl: lieber "nicht verfügbar" als "ruhig"
    return ON if value >= source.threshold else OFF


def _bounded(value: Any, default: int, low: int, high: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return number if low <= number <= high else default


def zone_rule(zone: Mapping[str, Any] | None) -> VibrationRule:
    zone = zone or {}
    return VibrationRule(
        count=_bounded(zone.get("vibration_count"), DEFAULT_COUNT, 1, MAX_COUNT),
        window=_bounded(zone.get("vibration_window"), DEFAULT_WINDOW, MIN_WINDOW, MAX_WINDOW),
    )


def rule_for(options: Mapping[str, Any], entity_id: str) -> VibrationRule:
    """Fehlalarmschutz für einen Melder: aus seiner (direkt gewählten) Meldergruppe."""
    zones = options.get("zones", {})
    if isinstance(zones, Mapping):
        for zone in zones.values():
            if isinstance(zone, Mapping) and entity_id in (zone.get("entities") or []):
                return zone_rule(zone)
    return VibrationRule()


def rule_for_zone_id(options: Mapping[str, Any], zone_id: str) -> VibrationRule:
    zones = options.get("zones", {})
    zone = zones.get(zone_id) if isinstance(zones, Mapping) else None
    return zone_rule(zone if isinstance(zone, Mapping) else None)


@dataclass
class VibrationCounter:
    """Zählt Meldungen je Melder; meldet, wenn genug im Zeitfenster zusammenkommen."""

    hits: dict[str, list[float]] = field(default_factory=dict)

    def record(self, entity_id: str, now: float, rule: VibrationRule) -> tuple[bool, int]:
        """Meldung zählen. Ergebnis: (Alarm ja/nein, Zahl der Meldungen im Fenster)."""
        if rule.count <= 1:
            self.hits.pop(entity_id, None)
            return True, 1
        recent = [t for t in self.hits.get(entity_id, []) if now - t <= rule.window]
        recent.append(now)
        if len(recent) >= rule.count:
            self.hits.pop(entity_id, None)
            return True, len(recent)
        self.hits[entity_id] = recent
        return False, len(recent)

    def reset(self) -> None:
        self.hits.clear()


def save_vibration_source(
    options: Mapping[str, Any], entity_id: str, *, threshold: float
) -> dict[str, Any]:
    new = copy.deepcopy(dict(options))
    sources = dict(new.get(OPT_VIBRATION_SOURCES, {}) or {})
    sources[entity_id] = {"threshold": float(threshold)}
    new[OPT_VIBRATION_SOURCES] = dict(sorted(sources.items()))
    return new


def delete_vibration_source(options: Mapping[str, Any], entity_id: str) -> dict[str, Any]:
    """Erschütterungsstärke entfernen – auch aus Meldergruppen und Immer aktiv."""
    new = copy.deepcopy(dict(options))
    sources = dict(new.get(OPT_VIBRATION_SOURCES, {}) or {})
    sources.pop(entity_id, None)
    new[OPT_VIBRATION_SOURCES] = sources
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


def save_zone_rule(
    options: Mapping[str, Any], zone_id: str, *, count: int, window: int
) -> dict[str, Any]:
    new = copy.deepcopy(dict(options))
    zones = new.get("zones", {})
    if zone_id not in zones:
        raise ValueError(zone_id)
    zones[zone_id]["vibration_count"] = _bounded(count, DEFAULT_COUNT, 1, MAX_COUNT)
    zones[zone_id]["vibration_window"] = _bounded(window, DEFAULT_WINDOW, MIN_WINDOW, MAX_WINDOW)
    return new
