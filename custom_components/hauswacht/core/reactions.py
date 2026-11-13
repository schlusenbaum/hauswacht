"""Alarmreaktionen (reine Logik): Sirenen und Benachrichtigungen je Profil.

Die Reaktion eines Profils ist Konfiguration. Ob und welche Sirenen tatsächlich angesteuert
werden, entscheidet ausschließlich der Sirenen-Guard (siehe siren_guard.py).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from .siren_guard import BURGLAR_TONES, VOLUME_LEVELS, FireIndicator
from .texts import DE, tr

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


def alarm_message(
    profile_id: str, sensor: str, *, test_mode: bool, lang: str = DE
) -> tuple[str, str]:
    prefix = tr(lang, "alarm_prefix_test" if test_mode else "alarm_prefix")
    return (
        tr(lang, "alarm_title", prefix=prefix),
        tr(lang, "alarm", prefix=prefix, sensor=sensor, profile=profile_id),
    )


def fault_message(indicators: Iterable[str], lang: str = DE) -> tuple[str, str]:
    return (
        tr(lang, "fault_title"),
        tr(lang, "fault", systems=", ".join(sorted(indicators))),
    )


def sensor_lost_message(sensor: str, lang: str = DE) -> tuple[str, str]:
    return (tr(lang, "sensor_lost_title"), tr(lang, "sensor_lost", sensor=sensor))


def restart_message(previous_profile: str, lang: str = DE) -> tuple[str, str]:
    return (tr(lang, "restart_title"), tr(lang, "restart", profile=previous_profile))


def tamper_message(sensor: str, lang: str = DE) -> tuple[str, str]:
    return (tr(lang, "tamper_title"), tr(lang, "tamper", sensor=sensor))


def blocked_message(reasons: Iterable[str], lang: str = DE) -> tuple[str, str]:
    return (
        tr(lang, "sirens_blocked_title"),
        tr(lang, "sirens_blocked", reasons=", ".join(sorted(set(reasons)))),
    )


def invalid_code_message(
    failures: int, lock_seconds: int | None, lang: str = DE
) -> tuple[str, str]:
    text = tr(lang, "invalid_code", failures=failures)
    if lock_seconds:
        text += tr(lang, "invalid_code_lock", seconds=lock_seconds)
    return (tr(lang, "invalid_code_title"), text)


def auto_armed_message(profile_name: str, reason: str, lang: str = DE) -> tuple[str, str]:
    return (
        tr(lang, "auto_armed_title"),
        tr(lang, "auto_armed", profile=profile_name, reason=reason),
    )


def auto_arm_failed_message(
    profile_name: str, reason: str, details: str, lang: str = DE
) -> tuple[str, str]:
    return (
        tr(lang, "auto_arm_failed_title"),
        tr(lang, "auto_arm_failed", profile=profile_name, reason=reason, details=details),
    )


def auto_disarmed_message(profile_name: str, reason: str, lang: str = DE) -> tuple[str, str]:
    return (
        tr(lang, "auto_disarmed_title"),
        tr(lang, "auto_disarmed", profile=profile_name, reason=reason),
    )
