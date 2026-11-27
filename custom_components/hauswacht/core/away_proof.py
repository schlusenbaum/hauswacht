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
# Unsicherer Beleg „Tür + Signal“ je Person (Nachtrag 0.61 zu ADR 0015)
OPT_AWAY_WEAK = "away_proof_weak"
# Signale, die als Ortung zählen (Geofence ohne Koordinaten, z. B. Apple Home) – ADR 0018
OPT_AWAY_GEOFENCE = "away_proof_geofence"
OPT_AWAY_WEAK_WINDOW = "away_proof_weak_window"
DEFAULT_WEAK_WINDOW = 5  # Minuten
MAX_WEAK_WINDOW = 30

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
    # Personen, bei denen auch „Tür + Signal weg“ reicht (unsicher), und dessen Zeitfenster
    weak: frozenset[str] = frozenset()
    weak_window: int = DEFAULT_WEAK_WINDOW  # Minuten
    # Signale, die als Ortung zählen (Geofence) – ADR 0018
    geofence: frozenset[str] = frozenset()

    @property
    def seconds(self) -> float:
        return self.window * 60.0

    @property
    def weak_seconds(self) -> float:
        return self.weak_window * 60.0


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
    raw_weak = options.get(OPT_AWAY_WEAK, [])
    weak = (
        frozenset(p for p in raw_weak if isinstance(p, str))
        if isinstance(raw_weak, list)
        else frozenset()
    )
    try:
        weak_window = int(options.get(OPT_AWAY_WEAK_WINDOW, DEFAULT_WEAK_WINDOW))
    except (TypeError, ValueError):
        weak_window = DEFAULT_WEAK_WINDOW
    weak_window = min(max(weak_window, 1), MAX_WEAK_WINDOW)
    raw_geo = options.get(OPT_AWAY_GEOFENCE, [])
    geofence = (
        frozenset(e for e in raw_geo if isinstance(e, str))
        if isinstance(raw_geo, list)
        else frozenset()
    )
    return ProofSettings(window, str(accuracy), weak, weak_window, geofence)


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


def geofence_fix(state: str | None, at: float) -> Fix | None:
    """Ortung aus einem Geofence-Signal ohne Koordinaten (ADR 0018).

    Nicht „home“ heißt draußen – sicher, denn ein Geofence wertet den Standort aus (anders als
    WLAN oder Ping). Unbekannt oder nicht verfügbar ortet nichts.
    """
    if state is None or state in _NOT_LOCATED:
        return None
    outside = state != "home"
    return Fix(outside, outside, at)


# Anwesenheit simulieren – nur Testmodus, nur für Hauswacht (ADR 0016)
SIM_HOME = "home"
SIM_AWAY = "away"  # weg mit Beleg
SIM_AWAY_NO_PROOF = "away_no_proof"  # alle Signale weg, aber kein Beleg (schlafendes Handy)
SIM_APPROACHING = "approaching"  # weg und nähert sich (Richtung)
SIM_REAL = "real"  # zurück auf die echten Signale
SIM_VALUES = (SIM_HOME, SIM_AWAY, SIM_AWAY_NO_PROOF, SIM_APPROACHING, SIM_REAL)

PROOF_FRESH = "fresh"  # frische, genaue Ortung allein
PROOF_DOOR = "door"  # Tür und danach Ortung außerhalb
PROOF_WEAK = "weak"  # Tür und danach Signal weg (unsicher)


def proven_away(
    fixes: Iterable[Fix],
    doors: Iterable[float],
    now: float,
    settings: ProofSettings,
    since: float | None = None,
) -> bool:
    """Gibt es einen Beleg, dass die Person draußen ist? (siehe ``proof_kind``)"""
    return proof_kind(fixes, doors, now, settings, since) is not None


def proof_kind(
    fixes: Iterable[Fix],
    doors: Iterable[float],
    now: float,
    settings: ProofSettings,
    since: float | None = None,
) -> str | None:
    """Welcher Beleg, dass die Person draußen ist – ``PROOF_FRESH``, ``PROOF_DOOR`` oder ``None``.

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
            return PROOF_FRESH  # frische, genaue Ortung allein
        if fix.outside_zone and any(d <= fix.at <= d + window for d in opened):
            return PROOF_DOOR  # Tür und danach Ortung außerhalb
    return None


DOOR_MEMORY = 24 * 3600  # Türöffnungen so lange merken (Sekunden)
DOOR_MAX = 200


def prune_doors(doors: Iterable[float], now: float) -> list[float]:
    """Türöffnungen der letzten 24 Stunden (höchstens 200) behalten."""
    return [d for d in doors if now - d <= DOOR_MEMORY][-DOOR_MAX:]


def weak_proof(
    doors: Iterable[float], left: Iterable[float], settings: ProofSettings, since: float | None
) -> bool:
    """Unsicherer Beleg: eine Tür ging auf, und danach (höchstens ``weak_window`` später)
    wechselte ein Signal der Person von „da“ auf „weg“ (WLAN, Ping, Bluetooth …).

    Ein Signal, das ohne Tür wegfällt (schlafendes Handy), belegt nichts. Unsicher, weil
    jemand anderes die Tür geöffnet haben kann, während das Handy zufällig einschläft.
    """
    start = since if since is not None else float("-inf")
    opened = [d for d in doors if d >= start]
    window = settings.weak_seconds
    return any(d <= t <= d + window for t in left if t >= start for d in opened)


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
        self._left: dict[str, list[float]] = {}  # Person -> wann ein Signal „weg“ wurde
        self._kind: dict[str, tuple[str, float]] = {}  # Person -> (Beleg, Zeitpunkt) – Anzeige

    def note_door(self, now: float) -> None:
        self.doors = prune_doors([*self.doors, now], now)

    def note_signal_left(self, person: str, now: float) -> None:
        """Ein Signal der Person wechselte von „da“ auf „weg“ (für „Tür + Signal“)."""
        self._left[person] = prune_doors([*self._left.get(person, []), now], now)

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
        since = self._home_since.get(person)
        kind = proof_kind(fixes, self.doors, now, self.settings, since)
        if kind is None and person in self.settings.weak:
            left = self._left.get(person, [])
            kind = PROOF_WEAK if weak_proof(self.doors, left, self.settings, since) else None
        if kind is not None:
            self._proven.add(person)
            self._kind[person] = (kind, now)
            return False
        return None

    def mark_proven(self, person: str, kind: str, now: float) -> None:
        """Beleg von außen setzen (Simulation im Testmodus)."""
        self._home.discard(person)
        self._proven.add(person)
        self._kind[person] = (kind, now)

    def forget(self, person: str) -> None:
        """Beleg vergessen (Simulation beendet) – danach zählen wieder nur echte Signale."""
        self._proven.discard(person)
        self._kind.pop(person, None)

    def kind(self, person: str) -> tuple[str, float] | None:
        """Welcher Beleg für „weg“ gilt (für die Anzeige)."""
        return self._kind.get(person) if person in self._proven else None

    def proven(self, person: str) -> bool:
        return person in self._proven

    def last_left(self, person: str) -> float | None:
        """Wann zuletzt ein Signal der Person auf „weg“ wechselte (Anzeige „was fehlt“)."""
        left = self._left.get(person)
        return left[-1] if left else None

    def last_door(self) -> float | None:
        return self.doors[-1] if self.doors else None


# --- Ortung, die sich nie bewegt (0.64.0b5) --------------------------------------------------

# So lange exakt dieselben Koordinaten außerhalb von Zuhause: die Ortung gilt als eingefroren
FROZEN_AFTER = 24 * 3600  # Sekunden
_DIGITS = 6  # Koordinaten auf etwa 10 cm vergleichen


class FrozenLocations:
    """Merkt sich je Ortung, seit wann sie exakt dieselben Koordinaten meldet.

    Eine echte Ortung schwankt immer ein wenig. Meldet sie über ``FROZEN_AFTER`` hinweg exakt
    dieselbe Position außerhalb von Zuhause, ist der Standort vorgetäuscht oder die App hängt –
    dann zählt sie nicht als Beleg für „weg“ (sichere Seite: niemand gilt fälschlich als weg).
    Bewegt sie sich wieder, zählt sie sofort wieder.
    """

    def __init__(self) -> None:
        self.seen: dict[str, tuple[float, float, float]] = {}  # Entität -> (lat, lon, seit)

    def see(self, entity_id: str, latitude: float, longitude: float, now: float) -> bool:
        """Koordinaten notieren. ``True``, wenn sich der Stand geändert hat (speichern)."""
        lat, lon = round(latitude, _DIGITS), round(longitude, _DIGITS)
        known = self.seen.get(entity_id)
        if known is not None and known[0] == lat and known[1] == lon:
            return False
        self.seen[entity_id] = (lat, lon, now)
        return True

    def frozen_for(self, entity_id: str, now: float) -> float | None:
        """Seit wie vielen Sekunden eingefroren – ``None``, wenn (noch) nicht eingefroren."""
        known = self.seen.get(entity_id)
        if known is None:
            return None
        seconds = now - known[2]
        return seconds if seconds >= FROZEN_AFTER else None

    def dump(self) -> dict[str, list[float]]:
        return {k: [v[0], v[1], v[2]] for k, v in self.seen.items()}

    def load(self, data: Any) -> None:
        if not isinstance(data, Mapping):
            return
        for entity_id, value in data.items():
            if (
                isinstance(entity_id, str)
                and isinstance(value, list | tuple)
                and len(value) == 3
                and all(_number(v) is not None for v in value)
            ):
                self.seen[entity_id] = (float(value[0]), float(value[1]), float(value[2]))
