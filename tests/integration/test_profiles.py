"""Integrationstests: frei definierbare Profile, Migration, Auswahlliste und Knöpfe."""

from __future__ import annotations

from typing import Any

import pytest
import voluptuous as vol
from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType, section
from homeassistant.exceptions import ServiceValidationError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.hauswacht.const import DOMAIN

from .conftest import DOOR, PANEL, WINDOW, all_closed, make_entry, set_sensor, setup_entry

SELECT = "select.hauswacht_profile"
ARM = "button.hauswacht_arm"
ARM_ANYWAY = "button.hauswacht_arm_anyway"

ZONES = {"aussenhaut": {"name": "Außenhaut", "entities": [DOOR, WINDOW], "label": None}}


async def _service(hass: HomeAssistant, domain: str, service: str, **data: Any) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)
    await hass.async_block_till_done()


def _state(hass: HomeAssistant, entity_id: str = PANEL) -> Any:
    state = hass.states.get(entity_id)
    assert state is not None
    return state


async def _setup_plain(hass: HomeAssistant, options: dict[str, Any]) -> MockConfigEntry:
    """Eintrag ganz ohne die Testprofile aus conftest."""
    all_closed(hass)
    entry = MockConfigEntry(domain=DOMAIN, title="Hauswacht", data={}, options=options, version=2)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


# --- Keine Standardprofile --------------------------------------------------


async def test_new_installation_has_no_profiles(hass: HomeAssistant) -> None:
    await _setup_plain(hass, {})
    panel = _state(hass)
    assert panel.attributes["supported_features"] == 0
    assert _state(hass, SELECT).attributes["options"] == []
    with pytest.raises(ServiceValidationError):
        await _service(hass, "button", "press", entity_id=ARM)


# --- Migration --------------------------------------------------------------


async def test_migration_from_fixed_profiles(hass: HomeAssistant) -> None:
    all_closed(hass)
    old = MockConfigEntry(
        domain=DOMAIN,
        title="Hauswacht",
        data={},
        version=1,
        options={"zones": ZONES, "profiles": {"night": {"zones": ["aussenhaut"]}}},
    )
    old.add_to_hass(hass)
    assert await hass.config_entries.async_setup(old.entry_id)
    await hass.async_block_till_done()
    assert old.version == 4
    assert list(old.options["profiles"]) == ["home", "night", "away", "vacation", "custom"]
    assert old.options["profiles"]["night"]["name"] == "Nacht"
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    assert _state(hass).state == AlarmControlPanelState.ARMED_NIGHT


# --- Eigene Profile ---------------------------------------------------------


async def test_profile_without_button(hass: HomeAssistant) -> None:
    options = {
        "zones": ZONES,
        "profiles": {
            "garten": {
                "name": "Garten",
                "icon": "mdi:flower",
                "exit_delay": 0,
                "zones": ["aussenhaut"],
            },
        },
    }
    await _setup_plain(hass, options)
    assert _state(hass).attributes["supported_features"] == 0
    assert _state(hass, SELECT).state == "Garten"
    await _service(hass, "button", "press", entity_id=ARM)
    panel = _state(hass)
    assert panel.state == AlarmControlPanelState.ARMED_CUSTOM_BYPASS
    assert panel.attributes["profile_name"] == "Garten"
    assert panel.attributes["icon"] == "mdi:flower"


async def test_only_assigned_buttons_are_offered(hass: HomeAssistant) -> None:
    options = {
        "zones": ZONES,
        "profiles": {
            "nacht_eg": {
                "name": "Nacht EG",
                "panel_mode": "night",
                "exit_delay": 0,
                "zones": ["aussenhaut"],
            },
        },
    }
    await _setup_plain(hass, options)
    features = _state(hass).attributes["supported_features"]
    assert features == AlarmControlPanelEntityFeature.ARM_NIGHT
    with pytest.raises(ServiceValidationError):
        await _service(hass, "alarm_control_panel", "alarm_arm_away", entity_id=PANEL)


async def test_arm_by_name_via_action(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    await _service(hass, "hauswacht", "arm", entity_id=PANEL, profile="nacht")
    assert _state(hass).attributes["profile"] == "night"


async def test_select_and_buttons(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry({"profiles": {"home": {"open_policy": "confirm"}}}))
    await _service(hass, "select", "select_option", entity_id=SELECT, option="Zuhause")
    assert _state(hass, SELECT).state == "Zuhause"

    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    with pytest.raises(ServiceValidationError):
        await _service(hass, "button", "press", entity_id=ARM)
    await _service(hass, "button", "press", entity_id=ARM_ANYWAY)
    panel = _state(hass)
    assert panel.state == AlarmControlPanelState.ARMED_HOME
    assert panel.attributes["bypassed_sensors"] == [WINDOW]

    # Im scharfen Zustand lässt sich das Profil nicht wechseln
    with pytest.raises(ServiceValidationError):
        await _service(hass, "select", "select_option", entity_id=SELECT, option="Nacht")


# --- Optionen ---------------------------------------------------------------


async def _open_profile_form(hass: HomeAssistant, entry: MockConfigEntry) -> dict[str, Any]:
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "profiles"}
    )
    return await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "profile_add"}
    )


async def test_options_flow_add_profile(hass: HomeAssistant) -> None:
    entry = await _setup_plain(hass, {"zones": ZONES})
    flow = await _open_profile_form(hass, entry)
    assert flow["step_id"] == "profile_settings"
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"],
        {
            "name": "Nacht EG",
            "icon": "mdi:weather-night",
            "panel_mode": "night",
            "zones": ["aussenhaut"],
        },
    )
    assert flow["type"] is FlowResultType.MENU
    await hass.async_block_till_done()
    profile = entry.options["profiles"]["nacht_eg"]
    assert profile["name"] == "Nacht EG"
    assert profile["panel_mode"] == "night"
    assert profile["zones"] == ["aussenhaut"]


async def test_options_flow_rejects_duplicate_name_and_button(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    flow = await _open_profile_form(hass, entry)
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"name": "nacht", "icon": "mdi:moon-waning-crescent", "panel_mode": "away"}
    )
    assert flow["errors"] == {"name": "profile_name_taken", "panel_mode": "panel_mode_taken"}


async def test_options_flow_delete_profile(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "profiles"}
    )
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "profile_delete"}
    )
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"profile": "vacation"}
    )
    assert flow["type"] is FlowResultType.MENU
    await hass.async_block_till_done()
    assert "vacation" not in entry.options["profiles"]
    features = _state(hass).attributes["supported_features"]
    assert not features & AlarmControlPanelEntityFeature.ARM_VACATION


def _initial_form_data(schema: vol.Schema) -> dict[str, Any]:
    """Nachbildung der Vorbelegung im Home-Assistant-Frontend (computeInitialHaFormData)."""
    data: dict[str, Any] = {}
    for key, value in schema.schema.items():
        name = str(key)
        suggested = (key.description or {}).get("suggested_value")
        if suggested is not None:
            data[name] = suggested
        elif key.default is not vol.UNDEFINED:
            data[name] = key.default()
        elif isinstance(value, section):
            nested = _initial_form_data(value.schema)
            if isinstance(key, vol.Required) or nested:
                data[name] = nested
    return data


def _missing_required(schema: vol.Schema, data: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for key, value in schema.schema.items():
        name = str(key)
        if isinstance(value, section):
            missing += _missing_required(value.schema, data.get(name) or {})
        elif isinstance(key, vol.Required) and data.get(name) in (None, ""):
            missing.append(name)
    return missing


@pytest.mark.parametrize("profile", ["night", "custom"])
async def test_profile_form_can_be_submitted_unchanged(hass: HomeAssistant, profile: str) -> None:
    """Regression: "OK" darf nicht an unbefüllten Pflichtfeldern im Bereich Automatik scheitern."""
    entry = make_entry()
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "profiles"}
    )
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "profile_edit"}
    )
    flow = await hass.config_entries.options.async_configure(flow["flow_id"], {"profile": profile})
    assert flow["step_id"] == "profile_settings"
    schema = flow["data_schema"]
    data = _initial_form_data(schema)
    assert _missing_required(schema, data) == []

    flow = await hass.config_entries.options.async_configure(flow["flow_id"], data)
    assert flow["type"] is FlowResultType.MENU
