"""Gemeinsame Fixtures für Integrationstests mit Home Assistant.

Diese Tests brauchen ``pytest-homeassistant-custom-component`` und laufen in der CI.
Ist das Paket nicht installiert, werden sie gar nicht erst eingesammelt.

Alle Sensoren sind reine Testzustände (``hass.states.async_set``) – es gibt keine Geräte.
"""

from __future__ import annotations

import importlib.util
from typing import Any

import pytest

PANEL = "alarm_control_panel.hauswacht"
TEST_MODE = "switch.hauswacht_test_mode"

DOOR = "binary_sensor.haustuer"
WINDOW = "binary_sensor.kuechenfenster"
MOTION = "binary_sensor.bwm_keller"
TAMPER = "binary_sensor.kontakt_tamper"

DEVICE_CLASSES = {DOOR: "door", WINDOW: "window", MOTION: "occupancy", TAMPER: "tamper"}

ZONE_OPTIONS: dict[str, Any] = {
    "zones": {
        "aussenhaut": {"name": "Außenhaut", "entities": [DOOR, WINDOW, TAMPER], "label": None},
        "keller": {"name": "Keller", "entities": [MOTION], "label": None},
    },
    "profiles": {
        "home": {"zones": ["aussenhaut"]},
        "night": {"zones": ["aussenhaut", "keller"]},
        "away": {"zones": ["aussenhaut", "keller"]},
        "vacation": {"zones": ["aussenhaut", "keller"]},
        "custom": {"zones": ["keller"]},
    },
}

if importlib.util.find_spec("pytest_homeassistant_custom_component") is None:
    collect_ignore_glob = ["test_*.py"]
else:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.hauswacht.const import DOMAIN

    @pytest.fixture(autouse=True)
    def auto_enable_custom_integrations(enable_custom_integrations: Any) -> None:
        return None

    def make_entry(options: dict[str, Any] | None = None) -> MockConfigEntry:
        merged: dict[str, Any] = {**ZONE_OPTIONS}
        for key, value in (options or {}).items():
            if key == "profiles":
                profiles = {k: dict(v) for k, v in ZONE_OPTIONS["profiles"].items()}
                for profile_id, settings in value.items():
                    profiles.setdefault(profile_id, {}).update(settings)
                merged["profiles"] = profiles
            else:
                merged[key] = value
        return MockConfigEntry(domain=DOMAIN, title="Hauswacht", data={}, options=merged)

    def set_sensor(hass: HomeAssistant, entity_id: str, state: str) -> None:
        hass.states.async_set(entity_id, state, {"device_class": DEVICE_CLASSES.get(entity_id)})

    def all_closed(hass: HomeAssistant) -> None:
        for entity_id in DEVICE_CLASSES:
            set_sensor(hass, entity_id, "off")

    async def setup_entry(
        hass: HomeAssistant, entry: MockConfigEntry, *, sensors: bool = True
    ) -> None:
        if sensors:
            all_closed(hass)
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
