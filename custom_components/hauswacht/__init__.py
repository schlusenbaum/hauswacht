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

PLATFORMS: list[str] = ["alarm_control_panel", "binary_sensor", "sensor", "switch"]


async def async_setup_entry(hass: HomeAssistant, entry: HauswachtConfigEntry) -> bool:
    from .runtime import HauswachtRuntime  # noqa: PLC0415

    runtime = HauswachtRuntime(hass, entry)
    await runtime.async_start()
    entry.runtime_data = runtime
    entry.async_on_unload(runtime.async_stop)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: HauswachtConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_options_updated(hass: HomeAssistant, entry: HauswachtConfigEntry) -> None:
    # Optionen lassen sich nur im unscharfen Zustand ändern (siehe Options Flow),
    # deshalb ist ein Neuladen hier gefahrlos.
    await hass.config_entries.async_reload(entry.entry_id)
