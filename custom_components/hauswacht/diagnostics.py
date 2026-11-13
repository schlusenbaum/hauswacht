"""Diagnose-Datei (Einstellungen → Geräte & Dienste → Hauswacht → ⋮ → Diagnose herunterladen).

Für Fehlerberichte: Einstellungen und Übersicht – ohne PINs, Kartennummern, Namen von Personen,
Empfängern und Netzwerken.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .overview import build_overview

if TYPE_CHECKING:
    from .runtime import HauswachtConfigEntry

REDACT = {
    # Ausweise
    "pin_salt",
    "pin_digest",
    "duress_salt",
    "duress_digest",
    "tags",
    "tag",
    "cards",
    # Personen, Konten, Empfänger, Netzwerke
    "users",
    "ha_user",
    "notify",
    "notify_system",
    "duress_notify",
    "reminder_persons",
    "homecoming_persons",
    "homecoming_signals",
    "homecoming_ssids",
    "auto_away_persons",
    "away_persons",
    "speakers",
    "targets",
    "alarm_targets",
    "general",
    "topic",
    "device",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: HauswachtConfigEntry
) -> dict[str, Any]:
    main = entry.runtime_data
    overview = build_overview(main)
    return {
        "version": entry.version,
        "options": async_redact_data(dict(entry.options), REDACT),
        "overview": async_redact_data(overview, REDACT),
    }
