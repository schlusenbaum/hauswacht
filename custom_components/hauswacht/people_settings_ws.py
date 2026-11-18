"""Einstellungsseite, Stufe 5: Personen – Benutzer, Rechte, PINs (ADR 0011).

PINs werden **nie** angezeigt oder zurückgegeben – nur, ob einer gesetzt ist. Neue PINs kommen
über den Websocket (nur Administratoren) und werden wie im Dialog sofort gehasht.
Karten anlernen und der Master-PIN bleiben im Dialog.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import MASTER_USER_ID
from .core.areas import multi_area, parse_areas
from .core.changes.users import RIGHT_VALUES
from .core.users import RIGHTS_ALL, RIGHTS_PER_AREA


async def ha_user_choices(hass: HomeAssistant) -> list[dict[str, str]]:
    """Aktive Home-Assistant-Konten (ohne System-Benutzer) zum Verknüpfen."""
    users = await hass.auth.async_get_users()
    return [
        {"id": u.id, "name": u.name or u.id}
        for u in users
        if u.is_active and not u.system_generated
    ]


def to_iso(value: Any) -> str | None:
    """Datum/Uhrzeit von der Seite (lokale Zeit von Home Assistant) als ISO-Text mit Zeitzone."""
    if not value:
        return None
    parsed = dt_util.parse_datetime(str(value))
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt_util.get_default_time_zone())
    return parsed.isoformat()


def _local_input(value: Any) -> str:
    """Gespeicherte Zeit für ein Feld "datetime-local" (Zeitzone von Home Assistant)."""
    if not isinstance(value, str) or not value:
        return ""
    parsed = dt_util.parse_datetime(value)
    return dt_util.as_local(parsed).strftime("%Y-%m-%dT%H:%M") if parsed else ""


def _scope(data: Mapping[str, Any]) -> str:
    """Bisherige Einschränkung auf Bereiche (vor 0.29) zählt als "je Bereich"."""
    if data.get("rights") in (RIGHTS_ALL, RIGHTS_PER_AREA):
        return str(data["rights"])
    return RIGHTS_PER_AREA if data.get("areas") else RIGHTS_ALL


def _area_rights(data: Mapping[str, Any], area_ids: list[str]) -> dict[str, list[str]]:
    stored = data.get("area_rights")
    if isinstance(stored, Mapping) and data.get("rights") == RIGHTS_PER_AREA:
        return {a: [r for r in stored.get(a, []) or [] if r in RIGHT_VALUES] for a in area_ids}
    general = [
        right
        for right, key in zip(RIGHT_VALUES, ("can_arm", "can_disarm", "can_end_alarm"), strict=True)
        if data.get(key, True)
    ]
    limited = data.get("areas") if isinstance(data.get("areas"), list) else []
    return {a: list(general) if not limited or a in limited else [] for a in area_ids}


def build_people_settings(
    options: Mapping[str, Any], ha_users: list[dict[str, str]]
) -> dict[str, Any]:
    areas = parse_areas(options)
    area_ids = list(areas)
    users = []
    for user_id, data in options.get("users", {}).items():
        if user_id == MASTER_USER_ID or not isinstance(data, Mapping):
            continue  # Master-PIN ist keine Person
        users.append(
            {
                "id": user_id,
                "name": str(data.get("name") or user_id),
                "active": bool(data.get("active", True)),
                "can_arm": bool(data.get("can_arm", True)),
                "can_disarm": bool(data.get("can_disarm", True)),
                "can_end_alarm": bool(data.get("can_end_alarm", True)),
                "can_force_arm": bool(data.get("can_force_arm", True)),
                "card_pin": bool(data.get("card_pin", False)),
                "ha_user": data.get("ha_user"),
                "valid_from": _local_input(data.get("valid_from")),
                "valid_until": _local_input(data.get("valid_until")),
                "rights": _scope(data),
                "area_rights": _area_rights(data, area_ids),
                # Nur ob gesetzt – nie der PIN selbst
                "has_pin": bool(data.get("pin_digest")),
                "has_duress": bool(data.get("duress_digest")),
                "cards": len(data.get("tags", []) or []) + len(data.get("tags_disabled", []) or []),
            }
        )
    return {
        "users": users,
        "ha_users": ha_users,
        "areas": [{"id": a.area_id, "name": a.name} for a in areas.values()],
        "multi_area": multi_area(options),
        "rights": list(RIGHT_VALUES),
        "master_pin": MASTER_USER_ID in options.get("users", {}),
    }
