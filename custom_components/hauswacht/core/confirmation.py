"""Bestätigung durch einen zweiten Melder (Zonen-Option "Alarm erst bei zwei Meldern").

Rein und ohne Home Assistant. Ein Melder einer bestätigungspflichtigen Zone löst allein
keinen Alarm aus. Erst wenn ein ANDERER Melder derselben Zone innerhalb des Zeitfensters
auslöst, gilt die Auslösung als bestätigt. Derselbe Melder zweimal zählt nicht – ein
flatternder Melder ist genau das, was die Option abfangen soll.

Sichere Seite: Ist in der Zone gerade kein anderer bestätigungsfähiger Melder verfügbar,
wäre eine Bestätigung unmöglich – dann löst der Melder sofort aus.

Rollen: Nur "sofort" und "Mitläufer" brauchen eine Bestätigung. Türen (Eingang) starten
weiter sofort die Eingangsverzögerung, Manipulation wird immer gemeldet.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .state_machine import SensorRole

CONFIRMABLE_ROLES = frozenset({SensorRole.INSTANT, SensorRole.FOLLOWER})

FREQUENT_COUNT = 3  # so oft allein ausgelöst ...
FREQUENT_PERIOD = 3600  # ... innerhalb dieser Zeit (s) = "löst häufig allein aus"


@dataclass(frozen=True)
class Pending:
    zone_id: str
    since: float
    until: float


@dataclass
class ConfirmationTracker:
    pending: dict[str, Pending] = field(default_factory=dict)  # Melder -> wartet seit/bis

    def reset(self) -> None:
        self.pending.clear()

    def expire(self, now: float) -> list[str]:
        """Abgelaufene, unbestätigte Auslösungen entfernen und zurückgeben."""
        expired = [s for s, p in self.pending.items() if p.until <= now]
        for sensor in expired:
            del self.pending[sensor]
        return expired

    def check(
        self, sensor: str, zone_id: str, window: int, now: float, *, others_available: int
    ) -> bool:
        """True = Alarm auslösen (bestätigt oder Bestätigung unmöglich), False = warten."""
        self.expire(now)
        if others_available < 1:
            return True
        if any(s != sensor and p.zone_id == zone_id for s, p in self.pending.items()):
            for other in [s for s, p in self.pending.items() if p.zone_id == zone_id]:
                del self.pending[other]
            return True
        previous = self.pending.get(sensor)
        since = previous.since if previous else now
        self.pending[sensor] = Pending(zone_id=zone_id, since=since, until=now + window)
        return False


@dataclass
class LoneTriggerCounter:
    """Zählt unbestätigte Einzelauslösungen je Melder ("löst häufig allein aus")."""

    times: dict[str, list[float]] = field(default_factory=dict)

    def record(self, sensor: str, now: float) -> bool:
        """True, wenn der Melder jetzt die Schwelle erreicht (dann beginnt die Zählung neu)."""
        recent = [t for t in self.times.get(sensor, []) if now - t <= FREQUENT_PERIOD]
        recent.append(now)
        if len(recent) >= FREQUENT_COUNT:
            self.times[sensor] = []
            return True
        self.times[sensor] = recent
        return False
