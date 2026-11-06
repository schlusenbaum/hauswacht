"""Infrastruktur-Überwachung und Systemstatus (reine Logik).

Infrastruktur-Indikatoren sind Binärsensoren, die "on" melden, solange ein System läuft –
z. B. der Verbindungsstatus der Zigbee2MQTT-Bridge. Fällt ein Indikator aus oder meldet er
"off", ist die Anlage gestört: Sensoren hinter diesem System können nicht mehr melden.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum

HEALTHY_STATE = "on"


class SystemStatus(StrEnum):
    OK = "ok"  # alles verfügbar
    DEGRADED = "degraded"  # einzelne Sensoren nicht verfügbar
    FAULT = "fault"  # Infrastruktur gestört


@dataclass(frozen=True)
class SystemReport:
    status: SystemStatus
    faulty_infrastructure: frozenset[str]
    unavailable_sensors: frozenset[str]


def is_healthy(state: str | None) -> bool:
    return state == HEALTHY_STATE


def faulty_indicators(states: Mapping[str, str | None]) -> frozenset[str]:
    return frozenset(entity_id for entity_id, state in states.items() if not is_healthy(state))


def system_report(
    infrastructure_states: Mapping[str, str | None],
    unavailable_sensors: Iterable[str],
) -> SystemReport:
    faulty = faulty_indicators(infrastructure_states)
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
