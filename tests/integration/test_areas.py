"""Integrationstests: Bereiche (unabhängig scharf schaltbar, frei benannt).

Alle Sensoren sind Testzustände; es sind keine Sirenen eingerichtet.
"""

from __future__ import annotations

from typing import Any

import pytest
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.hauswacht.const import DOMAIN

from .conftest import PANEL, WINDOW, ZONE_OPTIONS, make_entry, set_sensor, setup_entry

GATE = "binary_sensor.garagenfenster"
GARAGE_PANEL = "alarm_control_panel.hauswacht_garage"
ALL_PANEL = "alarm_control_panel.hauswacht_alle"

AREA_OPTIONS: dict[str, Any] = {
    "areas": {"garage": {"name": "Garage", "icon": "mdi:garage"}},
    "zones": {
        **ZONE_OPTIONS["zones"],
        "garage": {"name": "Garage", "entities": [GATE], "label": None},
    },
    "profiles": {
        "garage_away": {
            "name": "Garage scharf",
            "area": "garage",
            "panel_mode": "away",
            "exit_delay": 0,
            "zones": ["garage"],
        },
    },
}


async def _service(hass: HomeAssistant, domain: str, service: str, **data: Any) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)
    await hass.async_block_till_done()


def _state(hass: HomeAssistant, entity_id: str) -> str:
    state = hass.states.get(entity_id)
    assert state is not None, entity_id
    return state.state


async def _setup(hass: HomeAssistant) -> Any:
    hass.states.async_set(GATE, "off", {"device_class": "window"})
    entry = make_entry(AREA_OPTIONS)
    await setup_entry(hass, entry)
    return entry


async def test_single_area_has_no_extra_entities(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    assert hass.states.get(PANEL) is not None
    assert hass.states.get(ALL_PANEL) is None
    assert hass.states.get(GARAGE_PANEL) is None


async def test_area_entities_and_device(hass: HomeAssistant) -> None:
    entry = await _setup(hass)
    for entity_id in (
        PANEL,
        GARAGE_PANEL,
        ALL_PANEL,
        "binary_sensor.hauswacht_garage_offene_sensoren",
        "binary_sensor.hauswacht_offene_sensoren",
    ):
        assert hass.states.get(entity_id) is not None, entity_id
    # Hauptbereich behält seine IDs, der Bereich hat ein eigenes Gerät
    registry = er.async_get(hass)
    garage = registry.async_get(GARAGE_PANEL)
    assert garage is not None
    assert garage.unique_id == f"{entry.entry_id}_garage_panel"
    device = dr.async_get(hass).async_get(garage.device_id or "")
    assert device is not None
    assert device.name == "Hauswacht Garage"
    main = registry.async_get(PANEL)
    assert main is not None
    assert main.unique_id == f"{entry.entry_id}_panel"
    # Profilauswahl je Bereich nur mit den eigenen Profilen
    selects = [
        s
        for s in hass.states.async_all("select")
        if s.attributes.get("options") == ["Garage scharf"]
    ]
    assert len(selects) == 1
    attrs = hass.states.get(GARAGE_PANEL)
    assert attrs is not None
    assert attrs.attributes["area_name"] == "Garage"


async def test_areas_arm_independently(hass: HomeAssistant) -> None:
    await _setup(hass)
    await _service(hass, "alarm_control_panel", "alarm_arm_away", entity_id=GARAGE_PANEL)
    assert _state(hass, GARAGE_PANEL) == AlarmControlPanelState.ARMED_AWAY
    assert _state(hass, PANEL) == AlarmControlPanelState.DISARMED
    # Fenster im Haus: Haus ist unscharf, die Garage überwacht es nicht
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    assert _state(hass, GARAGE_PANEL) == AlarmControlPanelState.ARMED_AWAY
    assert _state(hass, PANEL) == AlarmControlPanelState.DISARMED
    # Garagenfenster: Alarm nur in der Garage
    hass.states.async_set(GATE, "on", {"device_class": "window"})
    await hass.async_block_till_done()
    assert _state(hass, GARAGE_PANEL) == AlarmControlPanelState.TRIGGERED
    assert _state(hass, PANEL) == AlarmControlPanelState.DISARMED
    assert _state(hass, ALL_PANEL) == AlarmControlPanelState.TRIGGERED
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=GARAGE_PANEL)
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=GARAGE_PANEL)
    assert _state(hass, GARAGE_PANEL) == AlarmControlPanelState.DISARMED


async def test_garage_panel_only_offers_its_buttons(hass: HomeAssistant) -> None:
    await _setup(hass)
    with pytest.raises(ServiceValidationError):
        await _service(hass, "alarm_control_panel", "alarm_arm_home", entity_id=GARAGE_PANEL)
    assert _state(hass, GARAGE_PANEL) == AlarmControlPanelState.DISARMED


async def test_all_panel_arms_each_area_with_its_profile(hass: HomeAssistant) -> None:
    await _setup(hass)
    await _service(hass, "alarm_control_panel", "alarm_arm_away", entity_id=ALL_PANEL)
    # Haus: Ausgangsverzögerung 60 s, Garage sofort scharf
    assert _state(hass, PANEL) == AlarmControlPanelState.ARMING
    assert _state(hass, GARAGE_PANEL) == AlarmControlPanelState.ARMED_AWAY
    assert _state(hass, ALL_PANEL) == AlarmControlPanelState.ARMING
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=ALL_PANEL)
    assert _state(hass, PANEL) == AlarmControlPanelState.DISARMED
    assert _state(hass, GARAGE_PANEL) == AlarmControlPanelState.DISARMED
    assert _state(hass, ALL_PANEL) == AlarmControlPanelState.DISARMED


async def test_all_panel_skips_areas_without_profile(hass: HomeAssistant) -> None:
    await _setup(hass)
    await _service(hass, "alarm_control_panel", "alarm_arm_home", entity_id=ALL_PANEL)
    assert _state(hass, PANEL) == AlarmControlPanelState.ARMED_HOME
    assert _state(hass, GARAGE_PANEL) == AlarmControlPanelState.DISARMED
    # Teilweise scharf
    assert _state(hass, ALL_PANEL) == AlarmControlPanelState.ARMED_CUSTOM_BYPASS


async def test_all_panel_reports_partial_failure(hass: HomeAssistant) -> None:
    await _setup(hass)
    hass.states.async_set(GATE, "on", {"device_class": "window"})
    await hass.async_block_till_done()
    with pytest.raises(ServiceValidationError):
        await _service(hass, "alarm_control_panel", "alarm_arm_away", entity_id=ALL_PANEL)
    # Haus wurde trotzdem geschaltet, die Garage nicht (Fenster offen)
    assert _state(hass, PANEL) == AlarmControlPanelState.ARMING
    assert _state(hass, GARAGE_PANEL) == AlarmControlPanelState.DISARMED


async def test_options_locked_while_any_area_armed(hass: HomeAssistant) -> None:
    entry = await _setup(hass)
    await _service(hass, "alarm_control_panel", "alarm_arm_away", entity_id=GARAGE_PANEL)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    assert flow["type"] == "abort"
    assert flow["reason"] == "disarm_first"


async def test_options_add_area_and_assign_profile(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    for step in ("system", "areas", "area_add"):
        flow = await hass.config_entries.options.async_configure(
            flow["flow_id"], {"next_step_id": step}
        )
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"name": "Gartenhaus", "icon": "mdi:greenhouse"}
    )
    assert flow["step_id"] == "areas"
    assert entry.options["areas"]["gartenhaus"]["name"] == "Gartenhaus"
    # Gleicher Name ein zweites Mal: Fehler
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "area_add"}
    )
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"name": "gartenhaus", "icon": "mdi:greenhouse"}
    )
    assert flow["errors"] == {"name": "area_name_taken"}
    await hass.async_block_till_done()
    assert hass.states.get("alarm_control_panel.hauswacht_gartenhaus") is not None
    assert hass.states.get(ALL_PANEL) is not None


async def test_options_area_with_profiles_cannot_be_deleted(hass: HomeAssistant) -> None:
    entry = await _setup(hass)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    for step in ("system", "areas", "area_delete"):
        flow = await hass.config_entries.options.async_configure(
            flow["flow_id"], {"next_step_id": step}
        )
    flow = await hass.config_entries.options.async_configure(flow["flow_id"], {"area": "garage"})
    assert flow["errors"] == {"area": "area_has_profiles"}


async def test_panel_mode_unique_per_area_only(hass: HomeAssistant) -> None:
    """Garage und Haus dürfen beide einen "Abwesend"-Knopf haben."""
    entry = await _setup(hass)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    for step in ("profiles", "profile_edit"):
        flow = await hass.config_entries.options.async_configure(
            flow["flow_id"], {"next_step_id": step}
        )
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"profile": "garage_away"}
    )
    assert flow["step_id"] == "profile_settings"
    schema_keys = [str(k) for k in flow["data_schema"].schema]
    assert "area" in schema_keys
    # Der Garage den Knopf "Zuhause" geben, der im Haus schon belegt ist: erlaubt
    defaults = {str(k): k.default() for k in flow["data_schema"].schema if callable(k.default)}
    defaults.update({"panel_mode": "home"})
    flow = await hass.config_entries.options.async_configure(flow["flow_id"], defaults)
    assert flow["type"] == "menu"
    assert entry.options["profiles"]["garage_away"]["panel_mode"] == "home"
    assert entry.options["profiles"]["garage_away"]["area"] == "garage"


async def test_simulation_reaches_every_area(hass: HomeAssistant) -> None:
    await _setup(hass)
    await _service(hass, "switch", "turn_on", entity_id="switch.hauswacht_test_mode")
    await _service(hass, "alarm_control_panel", "alarm_arm_away", entity_id=GARAGE_PANEL)
    await _service(hass, DOMAIN, "simulate_state", entity_id=PANEL, sensor=GATE, state="on")
    assert _state(hass, GARAGE_PANEL) == AlarmControlPanelState.TRIGGERED
    assert _state(hass, PANEL) == AlarmControlPanelState.DISARMED
    # Testmodus lässt sich nicht ausschalten, solange ein Bereich scharf ist
    with pytest.raises(ServiceValidationError):
        await _service(hass, "switch", "turn_off", entity_id="switch.hauswacht_test_mode")
