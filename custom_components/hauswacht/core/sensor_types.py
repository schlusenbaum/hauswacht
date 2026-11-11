"""Weitere Sensorarten als Melder: Zustände auf "on"/"off" abbilden.

Rein und ohne Home Assistant. Hauswacht rechnet intern nur mit "on" (offen/ausgelöst) und
"off" (zu/ruhig); alles andere (``unavailable``, ``unknown``, fehlt) gilt als nicht verfügbar.
Diese Abbildung passiert an einer Stelle, bevor Zustände bewertet werden.

| Art | "on" (löst aus) | Standardrolle |
|---|---|---|
| ``binary_sensor`` | ``on`` | nach Geräteklasse |
| ``input_boolean``, ``switch`` | ``on`` | sofort |
| ``lock`` | entriegelt, öffnet, offen, blockiert | Eingangsverzögerung |
| ``cover`` | offen, öffnet, schließt | Tor/Tür: Eingangsverzögerung, sonst sofort |
| ``sensor`` | Wert über/unter dem eingestellten Schwellwert | sofort |
| ``event`` | jedes neue Ereignis (Klingel, Kamera-Erkennung …) | sofort |

``event``-Entitäten sind nie "offen": Jedes neue Ereignis ist eine kurze Auslösung.
Ein ``sensor`` ohne Schwellwert löst nie aus.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .state_machine import SensorRole

ON, OFF = "on", "off"
UNAVAILABLE = "unavailable"
NOT_AVAILABLE_STATES = frozenset({"unavailable", "unknown", ""})

MONITORED_DOMAINS: tuple[str, ...] = (
    "binary_sensor",
    "lock",
    "cover",
    "event",
    "sensor",
    "input_boolean",
    "switch",
)

LOCK_ON = frozenset({"unlocked", "unlocking", "open", "opening", "jammed"})
LOCK_OFF = frozenset({"locked", "locking"})
COVER_ON = frozenset({"open", "opening", "closing"})
COVER_OFF = frozenset({"closed"})
COVER_ENTRY_CLASSES = frozenset({"door", "garage", "gate"})

# Arten ohne regelmäßige Lebenszeichen: keine Funkstille-Prüfung
NO_HEARTBEAT_DOMAINS = frozenset({"event", "input_boolean", "switch"})


def domain_of(entity_id: str) -> str:
    return entity_id.split(".", 1)[0]


def is_monitorable(entity_id: str) -> bool:
    return domain_of(entity_id) in MONITORED_DOMAINS


@dataclass(frozen=True)
class Threshold:
    above: float | None = None
    below: float | None = None

    @property
    def configured(self) -> bool:
        return self.above is not None or self.below is not None


def _number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_thresholds(options: Mapping[str, Any]) -> dict[str, Threshold]:
    raw = options.get("sensor_thresholds", {})
    result: dict[str, Threshold] = {}
    if not isinstance(raw, Mapping):
        return result
    for entity_id, data in raw.items():
        if not isinstance(data, Mapping):
            continue
        threshold = Threshold(above=_number(data.get("above")), below=_number(data.get("below")))
        if threshold.configured:
            result[str(entity_id)] = threshold
    return result


def parse_cameras(options: Mapping[str, Any]) -> dict[str, str]:
    """Kamera je Melder (für das Bild in der Alarm-Nachricht)."""
    raw = options.get("sensor_cameras", {})
    if not isinstance(raw, Mapping):
        return {}
    return {
        str(entity_id): camera
        for entity_id, camera in raw.items()
        if isinstance(camera, str) and camera.startswith("camera.")
    }


def normalize(
    entity_id: str, state: str | None, thresholds: Mapping[str, Threshold] | None = None
) -> str | None:
    """Rohzustand -> "on", "off", "unavailable" oder None (Entität fehlt)."""
    if state is None:
        return None
    if state in NOT_AVAILABLE_STATES:
        return UNAVAILABLE if state == "" else state
    domain = domain_of(entity_id)
    if domain == "lock":
        if state in LOCK_ON:
            return ON
        return OFF if state in LOCK_OFF else UNAVAILABLE
    if domain == "cover":
        if state in COVER_ON:
            return ON
        return OFF if state in COVER_OFF else UNAVAILABLE
    if domain == "event":
        return OFF  # nie "offen"; Auslösung über event_triggered()
    if domain == "sensor":
        threshold = (thresholds or {}).get(entity_id)
        value = _number(state)
        if value is None:
            return UNAVAILABLE
        if threshold is None:
            return OFF
        above = threshold.above is not None and value > threshold.above
        below = threshold.below is not None and value < threshold.below
        return ON if above or below else OFF
    return state  # binary_sensor, input_boolean, switch: on/off


def event_triggered(entity_id: str, old: str | None, new: str | None) -> bool:
    """Neues Ereignis einer ``event``-Entität?

    Der Zustand ist der Zeitpunkt des letzten Ereignisses. Ein Wechsel aus ``unavailable`` zählt
    nicht (das ist der Neustart, der den alten Zeitpunkt wiederherstellt).
    """
    if domain_of(entity_id) != "event" or new is None or new in NOT_AVAILABLE_STATES:
        return False
    if old is None or old == "unavailable":
        return False
    return old != new


def default_role_for(entity_id: str, device_class: str | None) -> SensorRole | None:
    """Standardrolle für andere Arten als ``binary_sensor`` (None = nach Geräteklasse)."""
    domain = domain_of(entity_id)
    if domain == "lock":
        return SensorRole.ENTRY
    if domain == "cover":
        return SensorRole.ENTRY if device_class in COVER_ENTRY_CLASSES else SensorRole.INSTANT
    if domain in ("event", "sensor", "input_boolean", "switch"):
        return SensorRole.INSTANT
    return None


def profile_camera(options: Mapping[str, Any], profile_id: str | None) -> tuple[str | None, bool]:
    """Kamera eines Alarmprofils (Standard für das Alarmbild) und ob Bilder gespeichert werden."""
    profiles = options.get("profiles", {})
    profile = profiles.get(profile_id, {}) if isinstance(profiles, Mapping) and profile_id else {}
    if not isinstance(profile, Mapping):
        return None, False
    camera = profile.get("camera")
    camera = camera if isinstance(camera, str) and camera.startswith("camera.") else None
    return camera, bool(profile.get("save_snapshots", False))


def camera_for(
    sensor: str | None,
    sensor_cameras: Mapping[str, str],
    profile_camera_id: str | None,
) -> str | None:
    """Kamera des auslösenden Melders hat Vorrang vor der des Profils."""
    if sensor and sensor in sensor_cameras:
        return sensor_cameras[sensor]
    return profile_camera_id


SNAPSHOT_COUNT = 3
SNAPSHOT_INTERVAL = 2.0  # Sekunden
