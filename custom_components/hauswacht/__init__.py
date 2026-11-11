"""Hauswacht – profilbasierte Einbruchmeldeanlage für Home Assistant.

Hinweis: Home-Assistant-Module werden hier bewusst erst innerhalb der Funktionen
importiert. So bleibt die reine Kernlogik (``core``) auch ohne installiertes
Home Assistant importier- und testbar.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .runtime import HauswachtConfigEntry

PLATFORMS: list[str] = [
    "alarm_control_panel",
    "binary_sensor",
    "button",
    "number",
    "select",
    "sensor",
    "switch",
    "time",
]


async def async_setup_entry(hass: HomeAssistant, entry: HauswachtConfigEntry) -> bool:
    from .core.areas import MAIN_AREA, parse_areas  # noqa: PLC0415
    from .runtime import HauswachtRuntime  # noqa: PLC0415

    runtime = HauswachtRuntime(hass, entry)
    # Weitere Bereiche: je eine eigene Runtime, der Hauptbereich hält sie
    for area_id in parse_areas(entry.options):
        if area_id != MAIN_AREA:
            runtime.areas[area_id] = HauswachtRuntime(hass, entry, area_id, main=runtime)
    for area in runtime.areas.values():
        await area.async_start()
        entry.async_on_unload(area.async_stop)
    entry.runtime_data = runtime
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _async_remove_stale_areas(hass, entry)
    from homeassistant.loader import async_get_integration  # noqa: PLC0415

    from .frontend import async_register_card  # noqa: PLC0415

    integration = await async_get_integration(hass, entry.domain)
    await async_register_card(hass, str(integration.version or "0"))
    return True


def _async_remove_stale_areas(hass: HomeAssistant, entry: HauswachtConfigEntry) -> None:
    """Geräte gelöschter Bereiche entfernen (ihre Entitäten verschwinden damit auch), ebenso
    das Bedienfeld "Alle Bereiche", wenn es nur noch einen Bereich gibt."""
    from homeassistant.helpers import device_registry as dr  # noqa: PLC0415
    from homeassistant.helpers import entity_registry as er  # noqa: PLC0415

    from .const import DOMAIN  # noqa: PLC0415
    from .core.areas import stale_all_panel, stale_area_device  # noqa: PLC0415

    areas = set(entry.runtime_data.areas)
    entities = er.async_get(hass)
    for entity in er.async_entries_for_config_entry(entities, entry.entry_id):
        if stale_all_panel(entity.unique_id, entry.entry_id, areas):
            entities.async_remove(entity.entity_id)
    devices = dr.async_get(hass)
    for device in dr.async_entries_for_config_entry(devices, entry.entry_id):
        if any(
            domain == DOMAIN and stale_area_device(ident, entry.entry_id, areas)
            for domain, ident in device.identifiers
        ):
            devices.async_remove_device(device.id)


async def async_remove_config_entry_device(
    hass: HomeAssistant, entry: HauswachtConfigEntry, device: Any
) -> bool:
    """Gerät von Hand löschen erlauben – aber nur für Bereiche, die es nicht mehr gibt."""
    from .const import DOMAIN  # noqa: PLC0415
    from .core.areas import stale_area_device  # noqa: PLC0415

    areas = set(entry.runtime_data.areas)
    return any(
        domain == DOMAIN and stale_area_device(ident, entry.entry_id, areas)
        for domain, ident in device.identifiers
    )


async def async_migrate_entry(hass: HomeAssistant, entry: HauswachtConfigEntry) -> bool:
    """Version 1 (feste Profile) -> 2 (frei definierbare Profile) -> 3 (PIN als Benutzer)
    -> 4 (Bestätigung durch zweiten Melder als Regel)."""
    from .core.profiles import migrate_v1_options  # noqa: PLC0415
    from .core.rules import migrate_zone_confirmation  # noqa: PLC0415
    from .core.users import migrate_legacy_pin  # noqa: PLC0415

    if entry.version == 1:
        hass.config_entries.async_update_entry(
            entry, options=migrate_v1_options(entry.options), version=2
        )
    if entry.version == 2:
        hass.config_entries.async_update_entry(
            entry, options=migrate_legacy_pin(entry.options), version=3
        )
    if entry.version == 3:
        hass.config_entries.async_update_entry(
            entry, options=migrate_zone_confirmation(entry.options), version=4
        )
    return entry.version == 4


async def async_unload_entry(hass: HomeAssistant, entry: HauswachtConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_options_updated(hass: HomeAssistant, entry: HauswachtConfigEntry) -> None:
    # Optionen lassen sich nur im unscharfen Zustand ändern (siehe Options Flow),
    # deshalb ist ein Neuladen hier gefahrlos.
    await hass.config_entries.async_reload(entry.entry_id)
