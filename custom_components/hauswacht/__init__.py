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
    "event",
    "number",
    "select",
    "sensor",
    "switch",
    "time",
]


async def async_setup_entry(hass: HomeAssistant, entry: HauswachtConfigEntry) -> bool:
    from .core.areas import MAIN_AREA, parse_areas  # noqa: PLC0415
    from .presence_proof import async_load_frozen  # noqa: PLC0415
    from .runtime import HauswachtRuntime  # noqa: PLC0415

    # Ortungen, die sich nie bewegen (0.64.0b5) – vor dem Start der Automatik laden
    await async_load_frozen(hass)
    runtime = HauswachtRuntime(hass, entry)
    # Weitere Bereiche: je eine eigene Runtime, der Hauptbereich hält sie
    for area_id in parse_areas(entry.options):
        if area_id != MAIN_AREA:
            runtime.areas[area_id] = HauswachtRuntime(hass, entry, area_id, main=runtime)
    for area in runtime.areas.values():
        await area.async_start()
        entry.async_on_unload(area.async_stop)
    entry.runtime_data = runtime
    # Hauswacht-Gerät zuerst anlegen: Geräte weiterer Bereiche verweisen per ID darauf
    from homeassistant.helpers import device_registry as dr  # noqa: PLC0415

    from .const import DOMAIN, NAME  # noqa: PLC0415
    from .entity import PAGE_URL  # noqa: PLC0415

    # Felder einzeln übergeben: DeviceInfo zu entpacken ist ab Home Assistant 2027.12 nicht
    # mehr erlaubt (DeviceInfo ist dann eine Datenklasse)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name=NAME,
        manufacturer="Hauswacht",
        model="Einbruchmeldeanlage",
        entry_type=dr.DeviceEntryType.SERVICE,
        configuration_url=PAGE_URL,
    )
    runtime.device_id = device.id
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _async_remove_stale_areas(hass, entry)
    from homeassistant.loader import async_get_integration  # noqa: PLC0415

    from .alarm_card import async_register_alarm_websocket  # noqa: PLC0415
    from .frontend import async_register_card  # noqa: PLC0415
    from .keypad_service import async_register_keypad_service  # noqa: PLC0415
    from .review import async_register_websocket  # noqa: PLC0415
    from .settings_ws import async_register_settings_websocket  # noqa: PLC0415

    # Aktion ohne Ziel-Entität (bleibt registriert; ohne geladene Anlage lehnt sie ab)
    async_register_keypad_service(hass)
    async_register_websocket(hass)
    async_register_alarm_websocket(hass)
    async_register_settings_websocket(hass)
    integration = await async_get_integration(hass, entry.domain)
    await async_register_card(hass, str(integration.version or "0"))
    from .const import OPT_SETTINGS_PAGE  # noqa: PLC0415
    from .frontend import async_register_panel, async_remove_panel  # noqa: PLC0415

    # Die Seite gibt es immer; die Einstellung blendet sie nur in der Seitenleiste aus (0.61)
    await async_register_panel(
        hass,
        str(integration.version or "0"),
        sidebar=bool(entry.options.get(OPT_SETTINGS_PAGE, True)),
    )
    entry.async_on_unload(lambda: async_remove_panel(hass))
    from homeassistant.core import callback  # noqa: PLC0415
    from homeassistant.helpers.start import async_at_started  # noqa: PLC0415

    @callback
    def _after_start(_hass: HomeAssistant) -> None:
        _migrate_app_targets(hass, entry)

    entry.async_on_unload(async_at_started(hass, _after_start))
    return True


def _migrate_app_targets(hass: HomeAssistant, entry: HauswachtConfigEntry) -> None:
    """Früher gewählte App-Entitäten einmalig durch den App-Dienst ersetzen (gleiches Handy,
    aber mit Knöpfen und Aufräumen). Erst nach dem Start: dann gibt es alle App-Entitäten."""
    from .core.notify_events import replace_targets  # noqa: PLC0415
    from .notify_targets import app_entity_aliases  # noqa: PLC0415

    new = replace_targets(entry.options, app_entity_aliases(hass))
    if new is not None:
        hass.config_entries.async_update_entry(entry, options=new)


def _async_remove_stale_areas(hass: HomeAssistant, entry: HauswachtConfigEntry) -> None:
    """Geräte gelöschter Bereiche entfernen (ihre Entitäten verschwinden damit auch), ebenso
    das Bedienfeld "Alle Bereiche", wenn es nur noch einen Bereich gibt."""
    from homeassistant.helpers import device_registry as dr  # noqa: PLC0415
    from homeassistant.helpers import entity_registry as er  # noqa: PLC0415

    from .const import DOMAIN  # noqa: PLC0415
    from .core.areas import retired_entity, stale_all_panel, stale_area_device  # noqa: PLC0415

    areas = set(entry.runtime_data.areas)
    entities = er.async_get(hass)
    for entity in er.async_entries_for_config_entry(entities, entry.entry_id):
        if stale_all_panel(entity.unique_id, entry.entry_id, areas) or retired_entity(
            entity.unique_id, entry.entry_id
        ):
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
    -> 4 (Bestätigung durch zweiten Melder als Regel) -> 5 (Melder-Typen statt Rollen)
    -> 5.2 („Bei Rückkehr“ je Profil, ADR 0015; die alten Schlüssel bleiben für ältere
    Versionen stehen, deshalb nur eine Unterversion)."""
    from .core.profiles import migrate_v1_options  # noqa: PLC0415
    from .core.returning import migrate_return  # noqa: PLC0415
    from .core.rules import migrate_zone_confirmation  # noqa: PLC0415
    from .core.sensor_types import migrate_roles_to_types  # noqa: PLC0415
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
    if entry.version == 4:
        hass.config_entries.async_update_entry(
            entry, options=migrate_roles_to_types(entry.options), version=5
        )
    if entry.version == 5 and entry.minor_version < 2:
        options, both = migrate_return(entry.options)
        hass.config_entries.async_update_entry(entry, options=options, minor_version=2)
        if both:
            _notify_return_migrated(hass, entry, both)
    return entry.version == 5


def _notify_return_migrated(
    hass: HomeAssistant, entry: HauswachtConfigEntry, profile_ids: list[str]
) -> None:
    """Hinweis nach dem Update: „Unscharf bei Rückkehr“ und Handy-Reinlassen waren beide an."""
    from homeassistant.components import persistent_notification  # noqa: PLC0415

    profiles = entry.options.get("profiles", {})
    names = ", ".join(str(profiles.get(pid, {}).get("name") or pid) for pid in profile_ids)
    german = (hass.config.language or "en").startswith("de")
    persistent_notification.async_create(
        hass,
        (
            f"In {names} waren „Unscharf bei Rückkehr“ und Handy-Reinlassen beide eingeschaltet. "
            "Seit 0.61 gibt es dafür eine Einstellung „Bei Rückkehr“ – eingestellt ist jetzt "
            "„reinlassen“ (das Profil bleibt scharf). Ändern: Einstellungsseite → Profil → "
            "Bei Rückkehr."
        )
        if german
        else (
            f"In {names}, “disarm on return” and letting in by phone were both switched on. "
            "Since 0.61 there is one setting “On return” – it is now set to “let in” (the "
            "profile stays armed). Change it: settings page → profile → On return."
        ),
        title="Hauswacht",
        notification_id=f"hauswacht_return_{entry.entry_id}",
    )


async def async_unload_entry(hass: HomeAssistant, entry: HauswachtConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_options_updated(hass: HomeAssistant, entry: HauswachtConfigEntry) -> None:
    # Optionen lassen sich nur im unscharfen Zustand ändern (siehe Options Flow),
    # deshalb ist ein Neuladen hier gefahrlos.
    await hass.config_entries.async_reload(entry.entry_id)
