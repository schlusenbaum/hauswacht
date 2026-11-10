"""Hauswacht – profilbasierte Einbruchmeldeanlage für Home Assistant.

Hinweis: Home-Assistant-Module werden hier bewusst erst innerhalb der Funktionen
importiert. So bleibt die reine Kernlogik (``core``) auch ohne installiertes
Home Assistant importier- und testbar.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

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
    from .runtime import HauswachtRuntime  # noqa: PLC0415

    runtime = HauswachtRuntime(hass, entry)
    await runtime.async_start()
    entry.runtime_data = runtime
    entry.async_on_unload(runtime.async_stop)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    from homeassistant.loader import async_get_integration  # noqa: PLC0415

    from .frontend import async_register_card  # noqa: PLC0415

    integration = await async_get_integration(hass, entry.domain)
    await async_register_card(hass, str(integration.version or "0"))
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: HauswachtConfigEntry) -> bool:
    """Version 1 (feste Profile) -> 2 (frei definierbare Profile) -> 3 (PIN als Benutzer)."""
    from .core.profiles import migrate_v1_options  # noqa: PLC0415
    from .core.users import migrate_legacy_pin  # noqa: PLC0415

    if entry.version == 1:
        hass.config_entries.async_update_entry(
            entry, options=migrate_v1_options(entry.options), version=2
        )
    if entry.version == 2:
        hass.config_entries.async_update_entry(
            entry, options=migrate_legacy_pin(entry.options), version=3
        )
    return entry.version == 3


async def async_unload_entry(hass: HomeAssistant, entry: HauswachtConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_options_updated(hass: HomeAssistant, entry: HauswachtConfigEntry) -> None:
    # Optionen lassen sich nur im unscharfen Zustand ändern (siehe Options Flow),
    # deshalb ist ein Neuladen hier gefahrlos.
    await hass.config_entries.async_reload(entry.entry_id)
