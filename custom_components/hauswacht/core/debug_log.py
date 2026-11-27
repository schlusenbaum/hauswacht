"""Debug-Log (ADR 0020): Entscheidungen kurz und ohne Geheimnisse beschreiben.

Reiner Kern ohne Home Assistant. ``describe`` macht aus Ereignissen, Wirkungen und Aktionen
(Datenklassen, Wörterbücher, Mengen) eine kurze Zeile wie
``SensorTriggered(sensor_key=binary_sensor.haustuer, role=entry)``.

Datenschutz: Felder, die Namen, Codes, Karten, Orte oder Nachrichtentexte enthalten können,
werden **nie** ausgegeben – egal, wie sie belegt sind (``SECRET_FIELDS``). Entitäts-IDs,
Zustände, Zeiten und Gründe bleiben; daran sieht man, was Hauswacht entschieden hat.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import MISSING, fields, is_dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

SECRET_FIELDS = frozenset(
    {
        # Personen- und Benutzernamen
        "by",
        "changed_by",
        "user",
        "user_id",
        "user_name",
        "identity",
        "name",
        "names",
        "person_name",
        # Codes, PINs, Karten
        "code",
        "codes",
        "pin",
        "pin_digest",
        "pin_salt",
        "tag",
        "tags",
        "card",
        "cards",
        # Orte und Netze
        "latitude",
        "longitude",
        "ssid",
        "ssids",
        # Nachrichten (Freitext, Namen darin)
        "title",
        "message",
        "text",
        "values",
        "details",
    }
)

_MAX_ITEMS = 12
_EPOCH_2020 = 1_577_836_800
_MAX_LEN = 480


def describe(value: Any) -> str:
    """Kurze, geheimnisfreie Beschreibung für eine Debug-Zeile."""
    return _short(_render(value, 0))


def _render(value: Any, depth: int) -> str:
    if depth > 3:
        return "…"
    if is_dataclass(value) and not isinstance(value, type):
        if hasattr(value, "profile_id") and type(value).__name__ == "ProfileRuntime":
            return str(value.profile_id)  # Profil: nur die Kennung
        parts = []
        for item in fields(value):
            if item.name in SECRET_FIELDS or item.name.startswith("_"):
                continue
            current = getattr(value, item.name)
            if _is_default(item, current):
                continue
            parts.append(f"{item.name}={_render(current, depth + 1)}")
        return f"{type(value).__name__}({', '.join(parts)})"
    if isinstance(value, Mapping):
        parts = [
            f"{k}={_render(v, depth + 1)}" for k, v in value.items() if str(k) not in SECRET_FIELDS
        ]
        return (
            "{" + ", ".join(parts[:_MAX_ITEMS]) + (", …" if len(parts) > _MAX_ITEMS else "") + "}"
        )
    if isinstance(value, set | frozenset):
        return _items(sorted(value, key=str), depth)
    if isinstance(value, list | tuple):
        return _items(list(value), depth)
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, int | float) and not isinstance(value, bool) and value > _EPOCH_2020:
        # Zeitpunkt (Sekunden seit 1970) lesbar als Uhrzeit UTC
        return datetime.fromtimestamp(value, UTC).strftime("%H:%M:%S UTC")
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def _items(values: list[Any], depth: int) -> str:
    shown = [_render(v, depth + 1) for v in values[:_MAX_ITEMS]]
    more = f", … (+{len(values) - _MAX_ITEMS})" if len(values) > _MAX_ITEMS else ""
    return "[" + ", ".join(shown) + more + "]"


def _is_default(item: Any, current: Any) -> bool:
    if item.default is not MISSING:
        return bool(current == item.default)
    if item.default_factory is not MISSING:
        return bool(current == item.default_factory())
    return False


def _short(text: str) -> str:
    return text if len(text) <= _MAX_LEN else text[:_MAX_LEN] + " …"
