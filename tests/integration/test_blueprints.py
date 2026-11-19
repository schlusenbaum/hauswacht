"""Integrationstests: Blueprints für allgemeine Keypads (ADR 0012).

Kein echtes Gerät: Das Ring Keypad ist nur ein Ereignis ``zwave_js_notification``, und
``zwave_js.set_value`` ist gemockt – so prüfen die Tests die Übersetzung in beide Richtungen.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.hauswacht.const import DOMAIN
from custom_components.hauswacht.core.pin import hash_pin

from .conftest import PANEL, make_entry, setup_entry

BLUEPRINTS = Path(__file__).parents[2] / "blueprints" / "automation" / "hauswacht"
PIN = "1357"
DEVICE = "ring_keypad_device"


async def _setup(hass: HomeAssistant) -> tuple[list[Any], str]:
    hashed = hash_pin(PIN)
    entry = make_entry(
        {
            "users": {
                "anna": {"name": "Anna", "pin_salt": hashed.salt, "pin_digest": hashed.digest}
            },
            "controls": {
                "flur": {
                    "name": "Keypad Flur",
                    "kind": "generic_keypad",
                    "buttons": {"home": "home", "away": "away"},
                }
            },
        }
    )
    await setup_entry(hass, entry)
    display = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{entry.entry_id}_keypad_flur"
    )
    assert display is not None
    target = Path(hass.config.path("blueprints", "automation", "hauswacht"))
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy(BLUEPRINTS / "ring_keypad_v2.yaml", target / "ring_keypad_v2.yaml")
    set_value = async_mock_service(hass, "zwave_js", "set_value")
    assert await async_setup_component(
        hass,
        "automation",
        {
            "automation": [
                {
                    "use_blueprint": {
                        "path": "hauswacht/ring_keypad_v2.yaml",
                        "input": {"keypad": DEVICE, "display": display},
                    }
                }
            ]
        },
    )
    await hass.async_block_till_done()
    return set_value, display


async def _press(hass: HomeAssistant, event_type: int, code: str | None) -> None:
    hass.bus.async_fire(
        "zwave_js_notification",
        {
            "device_id": DEVICE,
            "command_class": 111,
            "event_type": event_type,
            "event_data": code,
        },
    )
    await hass.async_block_till_done()
    await hass.async_block_till_done()


def _indicators(set_value: list[Any]) -> list[int]:
    return [int(c.data["property"]) for c in set_value]


async def test_ring_keypad_arms_disarms_and_shows_state(hass: HomeAssistant) -> None:
    set_value, _display = await _setup(hass)
    await _press(hass, 6, PIN)  # Zuhause + PIN
    state = hass.states.get(PANEL)
    assert state is not None
    assert state.state == AlarmControlPanelState.ARMED_HOME
    assert 10 in _indicators(set_value)  # Keypad zeigt "scharf Zuhause"
    await _press(hass, 3, "0000")  # falscher PIN
    assert hass.states.get(PANEL).state == AlarmControlPanelState.ARMED_HOME  # type: ignore[union-attr]
    assert _indicators(set_value)[-1] == 9  # Fehlerton
    await _press(hass, 3, PIN)
    assert hass.states.get(PANEL).state == AlarmControlPanelState.DISARMED  # type: ignore[union-attr]
    assert _indicators(set_value)[-1] == 2  # unscharf


async def test_ring_keypad_ignores_other_keys(hass: HomeAssistant) -> None:
    set_value, _display = await _setup(hass)
    before = len(set_value)
    await _press(hass, 0, None)  # Keypad aufgeweckt
    await _press(hass, 25, None)  # Abbrechen
    assert len(set_value) == before
    assert hass.states.get(PANEL).state == AlarmControlPanelState.DISARMED  # type: ignore[union-attr]
