"""„weg“ nur mit Beleg (ADR 0015, Abschnitt 2) – rein, ohne Home Assistant.

Ein schlafendes Handy darf niemanden abwesend machen. Die Signale einer Person (Personen-Entität,
WLAN, Ping, Bluetooth, Richtung …) sagen „weg“ – das reicht aber erst, wenn es einen **Beleg**
gibt, dass die Person wirklich draußen ist. Belege sind **Ortungen außerhalb** (Entitäten mit
Koordinaten: Companion App, iCloud3, GPS-Tracker, die Person selbst):

1. **Tür und Ortung:** Eine Eingangstür ging auf und danach – höchstens ``window`` später – kam
   eine Ortung außerhalb der Zone „Zuhause“ (egal wie genau).
2. **Frische Ortung allein:** Eine Ortung außerhalb, die sich in den letzten ``window``
   aktualisiert hat und **genau genug** ist:

   - ``strict`` (genau prüfen, Standard): Entfernung zum Zuhause größer als Zonenradius plus
     gemeldete Ungenauigkeit – ein GPS-Sprung im Haus zählt nicht.
   - ``simple`` (einfach): außerhalb der Zone, egal wie ungenau.

WLAN, Ping und Bluetooth haben keine Koordinaten – sie bestätigen nur, reichen allein nie.
Wer gar keine Ortung hat, gilt nie als weg (sichere Seite).
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

ACCURACY_STRICT = "strict"
ACCURACY_SIMPLE = "simple"
ACCURACY_MODES = (ACCURACY_STRICT, ACCURACY_SIMPLE)
DEFAULT_ACCURACY = ACCURACY_STRICT
DEFAULT_WINDOW = 15  # Minuten
MAX_WINDOW = 120

OPT_AWAY_WINDOW = "away_proof_window"
OPT_AWAY_ACCURACY = "away_proof_accuracy"

_NOT_LOCATED = frozenset({"unknown", "unavailable", ""})
_EARTH_RADIUS_M = 6_371_000.0


@dataclass(frozen=True)
class Home:
    """Zone „Zuhause“: Mittelpunkt und Radius in Metern."""

    latitude: float
    longitude: float
    radius: float


@dataclass(frozen=True)
class Fix:
    """Eine Ortung: wo (außerhalb?) und wann sie sich zuletzt aktualisiert hat."""

    outside_zone: bool  # Zustand nicht „home“ (außerhalb der Zone)
    outside_sure: bool  # außerhalb nach der gewählten Genauigkeit
    at: float  # Zeitpunkt der letzten Aktualisierung (Sekunden)


@dataclass(frozen=True)
class ProofSettings:
    window: int = DEFAULT_WINDOW  # Minuten
    accuracy: str = DEFAULT_ACCURACY

    @property
    def seconds(self) -> float:
        return self.window * 60.0


def parse_proof_settings(options: Mapping[str, Any]) -> ProofSettings:
    raw = options.get(OPT_AWAY_WINDOW, DEFAULT_WINDOW)
    try:
        window = int(raw)
    except (TypeError, ValueError):
        window = DEFAULT_WINDOW
    window = min(max(window, 1), MAX_WINDOW)
    accuracy = options.get(OPT_AWAY_ACCURACY)
    if accuracy not in ACCURACY_MODES:
        accuracy = DEFAULT_ACCURACY
    return ProofSettings(window, str(accuracy))


def distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Entfernung zweier Punkte auf der Erde (Haversine), in Metern."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * _EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(a)))


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value) if math.isfinite(value) else None


def is_locator(attributes: Mapping[str, Any]) -> bool:
    """Hat die Entität Koordinaten? Nur dann kann sie „außerhalb geortet“ belegen."""
    return (
        _number(attributes.get("latitude")) is not None
        and _number(attributes.get("longitude")) is not None
    )


def locate(
    state: str | None,
    attributes: Mapping[str, Any],
    at: float,
    *,
    home: Home | None,
    accuracy: str = DEFAULT_ACCURACY,
) -> Fix | None:
    """Ortung aus einem Zustand – ``None``, wenn die Entität nichts ortet."""
    lat = _number(attributes.get("latitude"))
    lon = _number(attributes.get("longitude"))
    if state is None or state in _NOT_LOCATED or lat is None or lon is None:
        return None
    outside_zone = state != "home"
    if accuracy == ACCURACY_SIMPLE or home is None:
        sure = outside_zone
    else:
        spread = max(_number(attributes.get("gps_accuracy")) or 0.0, 0.0)
        sure = distance_m(lat, lon, home.latitude, home.longitude) > home.radius + spread
    return Fix(outside_zone, outside_zone and sure, at)


def proven_away(
    fixes: Iterable[Fix],
    doors: Iterable[float],
    now: float,
    settings: ProofSettings,
    since: float | None = None,
) -> bool:
    """Gibt es einen Beleg, dass die Person draußen ist?

    ``doors``: Zeitpunkte, zu denen eine Eingangstür aufging. ``since``: seit wann die Person
    zuletzt heimgekommen ist – ältere Türen und Ortungen gehören zu einem früheren Weggehen und
    zählen nicht (eine eingefrorene Ortung von gestern belegt nichts).
    """
    window = settings.seconds
    start = since if since is not None else float("-inf")
    opened = [d for d in doors if d >= start]
    for fix in fixes:
        if fix.at < start:
            continue
        if fix.outside_sure and now - fix.at <= window:
            return True  # frische, genaue Ortung allein
        if fix.outside_zone and any(d <= fix.at <= d + window for d in opened):
            return True  # Tür und danach Ortung außerhalb
    return False


DOOR_MEMORY = 24 * 3600  # Türöffnungen so lange merken (Sekunden)
DOOR_MAX = 200


def prune_doors(doors: Iterable[float], now: float) -> list[float]:
    """Türöffnungen der letzten 24 Stunden (höchstens 200) behalten."""
    return [d for d in doors if now - d <= DOOR_MEMORY][-DOOR_MAX:]


class AwayTracker:
    """Merkt sich je Person, ob „weg“ belegt ist (bleibt belegt, bis sie wieder zuhause ist).

    ``judge`` bekommt die Kombination aller Signale (zuhause / weg / unbekannt) und die
    Ortungen der Person und gibt zurück, was für die Automatik gilt:
    ``True`` zuhause, ``False`` weg mit Beleg, ``None`` unbekannt (auch: „weg“ ohne Beleg).
    """

    def __init__(self, settings: ProofSettings | None = None) -> None:
        self.settings = settings or ProofSettings()
        self.doors: list[float] = []
        self._proven: set[str] = set()
        self._home_since: dict[str, float] = {}
        self._home: set[str] = set()

    def note_door(self, now: float) -> None:
        self.doors = prune_doors([*self.doors, now], now)

    def judge(
        self, person: str, combined: bool | None, fixes: Iterable[Fix], now: float
    ) -> bool | None:
        if combined is True:
            if person not in self._home:
                self._home.add(person)
                self._home_since[person] = now
            self._proven.discard(person)
            return True
        self._home.discard(person)
        if combined is None:
            return None
        if person in self._proven:
            return False
        if proven_away(fixes, self.doors, now, self.settings, self._home_since.get(person)):
            self._proven.add(person)
            return False
        return None

    def proven(self, person: str) -> bool:
        return person in self._proven
