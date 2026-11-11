"""Melder, die häufig Regeln beginnen, die nicht erfüllt werden ("löst häufig allein aus").

Rein und ohne Home Assistant.
"""

from __future__ import annotations

from dataclasses import dataclass, field

FREQUENT_COUNT = 3  # so oft allein ausgelöst ...
FREQUENT_PERIOD = 3600  # ... innerhalb dieser Zeit (s) = "löst häufig allein aus"


@dataclass
class LoneTriggerCounter:
    """Zählt unbestätigte Einzelauslösungen je Melder."""

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
