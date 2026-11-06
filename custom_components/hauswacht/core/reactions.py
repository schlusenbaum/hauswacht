"""Alarmreaktionen (reine Logik): Sirenen und Benachrichtigungen je Profil.

Die Reaktion eines Profils ist Konfiguration. Ob und welche Sirenen tatsächlich angesteuert
werden, entscheidet ausschließlich der Sirenen-Guard (siehe siren_guard.py).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from .siren_guard import BURGLAR_TONES, VOLUME_LEVELS, FireIndicator

DEFAULT_TONE = "burglar"
DEFAULT_VOLUME = "high"
FIRE_DEVICE_CLASSES = frozenset({"smoke", "gas", "carbon_monoxide", "heat"})
UNAVAILABLE_STATES = frozenset({"unavailable", "unknown"})


@dataclass(frozen=True)
class Reaction:
    sirens: tuple[str, ...] = ()
    tone: str = DEFAULT_TONE
    volume: str = DEFAULT_VOLUME
    notify: tuple[str, ...] = ()
    silent: bool = False  # stiller Alarm: nur Benachrichtigungen

    @property
    def siren_targets(self) -> tuple[str, ...]:
        return () if self.silent else self.sirens


def _str_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list | tuple):
        return ()
    return tuple(dict.fromkeys(str(v) for v in value if isinstance(v, str)))


def parse_reaction(options: Mapping[str, Any], profile_id: str) -> Reaction:
    stored: Mapping[str, Any] = options.get("profiles", {}).get(profile_id, {})
    registered = set(_str_tuple(options.get("sirens", [])))
    tone = stored.get("siren_tone", DEFAULT_TONE)
    volume = stored.get("siren_volume", DEFAULT_VOLUME)
    return Reaction(
        # Nur registrierte Sirenen sind erlaubt – ein Profil kann keine fremden Geräte nennen.
        sirens=tuple(s for s in _str_tuple(stored.get("sirens", [])) if s in registered),
        tone=tone if tone in BURGLAR_TONES else DEFAULT_TONE,
        volume=volume if volume in VOLUME_LEVELS else DEFAULT_VOLUME,
        notify=_str_tuple(stored.get("notify", [])),
        silent=bool(stored.get("silent", False)),
    )


# --- Brand-Indikatoren -------------------------------------------------------


def is_fire_indicator(entity_id: str, device_class: str | None) -> bool:
    """Brand-Indikator am Sirenengerät: Rauch/Gas/CO/Hitze oder Testknopf eines Melders."""
    if not entity_id.startswith("binary_sensor."):
        return False
    return device_class in FIRE_DEVICE_CLASSES or entity_id.endswith("_test")


def fire_state(indicator_states: Iterable[str | None]) -> FireIndicator:
    """Zusammengefasster Brandzustand eines Geräts.

    Ein aktiver Indikator -> ACTIVE. Ein nicht verfügbarer Indikator -> UNKNOWN
    (wird vom Guard wie Brand behandelt). Keine Indikatoren -> CLEAR (reine Sirene).
    """
    result = FireIndicator.CLEAR
    for state in indicator_states:
        if state == "on":
            return FireIndicator.ACTIVE
        if state is None or state in UNAVAILABLE_STATES:
            result = FireIndicator.UNKNOWN
    return result


def parse_max_duration(state: str | None, fallback: int) -> int:
    """Gerätseitige Höchstdauer aus dem Zustand einer Zahl-Entität (nur gelesen)."""
    try:
        value = int(float(state)) if state is not None else 0
    except ValueError:
        return fallback
    return value if value > 0 else fallback


# --- Nachrichtentexte --------------------------------------------------------


def alarm_message(profile_id: str, sensor: str, *, test_mode: bool) -> tuple[str, str]:
    prefix = "TESTALARM" if test_mode else "EINBRUCHALARM"
    return (f"Hauswacht: {prefix}", f"{prefix} – ausgelöst durch {sensor} (Profil {profile_id}).")


def fault_message(indicators: Iterable[str]) -> tuple[str, str]:
    return (
        "Hauswacht: Störung",
        "Hauswacht ist scharf, aber diese Systeme sind gestört: "
        f"{', '.join(sorted(indicators))}. Sensoren dahinter können nicht melden.",
    )


def sensor_lost_message(sensor: str) -> tuple[str, str]:
    return (
        "Hauswacht: Sensor ausgefallen",
        f"Der überwachte Sensor {sensor} ist nicht mehr verfügbar.",
    )


def restart_message(previous_profile: str) -> tuple[str, str]:
    return (
        "Hauswacht: nach Neustart unscharf",
        f"Home Assistant wurde neu gestartet. Hauswacht war scharf (Profil {previous_profile}) "
        "und ist jetzt UNSCHARF.",
    )


def tamper_message(sensor: str) -> tuple[str, str]:
    return ("Hauswacht: Manipulation", f"Manipulation gemeldet: {sensor}.")


def blocked_message(reasons: Iterable[str]) -> tuple[str, str]:
    return (
        "Hauswacht: Sirenen gesperrt",
        "Alarm ausgelöst, Sirenen wurden aber nicht angesteuert: "
        f"{', '.join(sorted(set(reasons)))}.",
    )
