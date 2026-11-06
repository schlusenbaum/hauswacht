"""Infrastruktur-Überwachung und Systemstatus (reine Logik).

Infrastruktur-Indikatoren sind Binärsensoren, die den Zustand eines Systems melden – z. B.
der Verbindungsstatus der Zigbee2MQTT-Bridge. Die Bedeutung von "on" hängt von der
Geräteklasse ab: Bei "Problem"-Sensoren heißt "on" Störung, bei allen anderen (Verbindung,
läuft, …) heißt "on" in Ordnung. Ein nicht verfügbarer Indikator gilt immer als Störung.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum

HEALTHY_STATE = "on"
UNAVAILABLE_STATES = frozenset({"unavailable", "unknown"})
# Geräteklassen, bei denen "on" einen Fehler bedeutet
INVERTED_DEVICE_CLASSES = frozenset({"problem", "safety"})


class SystemStatus(StrEnum):
    OK = "ok"  # alles verfügbar
    DEGRADED = "degraded"  # einzelne Sensoren nicht verfügbar
    FAULT = "fault"  # Infrastruktur gestört


@dataclass(frozen=True)
class SystemReport:
    status: SystemStatus
    faulty_infrastructure: frozenset[str]
    unavailable_sensors: frozenset[str]


def is_healthy(state: str | None, device_class: str | None = None) -> bool:
    if state is None or state in UNAVAILABLE_STATES:
        return False
    if device_class in INVERTED_DEVICE_CLASSES:
        return state == "off"
    return state == HEALTHY_STATE


def faulty_indicators(
    states: Mapping[str, str | None],
    device_classes: Mapping[str, str | None] | None = None,
) -> frozenset[str]:
    classes = device_classes or {}
    return frozenset(
        entity_id
        for entity_id, state in states.items()
        if not is_healthy(state, classes.get(entity_id))
    )


def system_report(
    infrastructure_states: Mapping[str, str | None],
    unavailable_sensors: Iterable[str],
    device_classes: Mapping[str, str | None] | None = None,
) -> SystemReport:
    faulty = faulty_indicators(infrastructure_states, device_classes)
    unavailable = frozenset(unavailable_sensors)
    if faulty:
        status = SystemStatus.FAULT
    elif unavailable:
        status = SystemStatus.DEGRADED
    else:
        status = SystemStatus.OK
    return SystemReport(
        status=status, faulty_infrastructure=faulty, unavailable_sensors=unavailable
    )
