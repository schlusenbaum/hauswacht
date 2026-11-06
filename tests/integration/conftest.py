"""Gemeinsame Fixtures für Integrationstests mit Home Assistant.

Diese Tests brauchen ``pytest-homeassistant-custom-component`` und laufen in der CI.
Ist das Paket nicht installiert, werden sie gar nicht erst eingesammelt.
"""

from __future__ import annotations

import importlib.util
from typing import Any

import pytest

PANEL = "alarm_control_panel.hauswacht"
TEST_MODE = "switch.hauswacht_test_mode"

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
        return MockConfigEntry(domain=DOMAIN, title="Hauswacht", data={}, options=options or {})

    async def setup_entry(hass: HomeAssistant, entry: MockConfigEntry) -> None:
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
