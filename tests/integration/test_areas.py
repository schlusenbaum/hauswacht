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
from custom_components.hauswacht.core.pin import hash_pin

from .conftest import PANEL, WINDOW, ZONE_OPTIONS, make_entry, set_sensor, setup_entry

GATE = "binary_sensor.garagenfenster"
GARAGE_PANEL = "alarm_control_panel.hauswacht_garage"
ALL_PANEL = "all_panel"  # über die unique_id gesucht (ID hängt von der Sprache ab)

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
    if "entity_id" in data:
        data["entity_id"] = _eid(hass, data["entity_id"])
    await hass.services.async_call(domain, service, data, blocking=True)
    await hass.async_block_till_done()


def _eid(hass: HomeAssistant, entity_id: str) -> str:
    """Panel "Alle" über die unique_id finden, sonst die ID unverändert."""
    if entity_id != ALL_PANEL:
        return entity_id
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    found = er.async_get(hass).async_get_entity_id(
        "alarm_control_panel", DOMAIN, f"{entry.entry_id}_all_panel"
    )
    assert found is not None, "Bedienfeld Alle fehlt"
    return found


def _state(hass: HomeAssistant, entity_id: str) -> str:
    entity_id = _eid(hass, entity_id)
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
    assert not [s for s in hass.states.async_all("alarm_control_panel") if s.entity_id != PANEL]
    assert hass.states.get(GARAGE_PANEL) is None


async def test_area_entities_and_device(hass: HomeAssistant) -> None:
    entry = await _setup(hass)
    for entity_id in (PANEL, GARAGE_PANEL, _eid(hass, ALL_PANEL)):
        assert hass.states.get(entity_id) is not None, entity_id
    open_sensors = [
        s.entity_id
        for s in hass.states.async_all("binary_sensor")
        if s.entity_id.startswith("binary_sensor.hauswacht")
    ]
    assert len(open_sensors) == 2
    assert any(e.startswith("binary_sensor.hauswacht_garage_") for e in open_sensors)
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
    assert _eid(hass, ALL_PANEL)


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


async def test_deleted_area_leaves_no_device(hass: HomeAssistant) -> None:
    """Gelöschter Bereich: Gerät, Entitäten und "Alle Bereiche" verschwinden."""
    entry = make_entry({"areas": {"garage": {"name": "Garage"}}})
    await setup_entry(hass, entry)
    assert hass.states.get(GARAGE_PANEL) is not None
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    for step in ("system", "areas", "area_delete"):
        flow = await hass.config_entries.options.async_configure(
            flow["flow_id"], {"next_step_id": step}
        )
    flow = await hass.config_entries.options.async_configure(flow["flow_id"], {"area": "garage"})
    assert flow["step_id"] == "areas"
    await hass.async_block_till_done()
    assert "garage" not in entry.options.get("areas", {})
    registry = er.async_get(hass)
    assert registry.async_get(GARAGE_PANEL) is None
    assert (
        registry.async_get_entity_id("alarm_control_panel", DOMAIN, f"{entry.entry_id}_all_panel")
        is None
    )
    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    assert [d.name for d in devices] == ["Hauswacht"]
    assert hass.states.get(PANEL) is not None


def _anna(**rights: Any) -> dict[str, Any]:
    hashed = hash_pin("1357")
    return {"name": "Anna", "pin_salt": hashed.salt, "pin_digest": hashed.digest, **rights}


async def test_user_rights_per_area(hass: HomeAssistant) -> None:
    hass.states.async_set(GATE, "off", {"device_class": "window"})
    rights = {"rights": "per_area", "area_rights": {"main": ["arm"], "garage": ["arm", "disarm"]}}
    await setup_entry(hass, make_entry({**AREA_OPTIONS, "users": {"anna": _anna(**rights)}}))
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL, code="1357")
    assert _state(hass, PANEL) == AlarmControlPanelState.ARMED_NIGHT
    with pytest.raises(ServiceValidationError):
        await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL, code="1357")
    assert _state(hass, PANEL) == AlarmControlPanelState.ARMED_NIGHT
    await _service(
        hass, "alarm_control_panel", "alarm_arm_away", entity_id=GARAGE_PANEL, code="1357"
    )
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=GARAGE_PANEL, code="1357")
    assert _state(hass, GARAGE_PANEL) == AlarmControlPanelState.DISARMED


async def test_options_user_rights_per_area(hass: HomeAssistant) -> None:
    hass.states.async_set(GATE, "off", {"device_class": "window"})
    entry = make_entry({**AREA_OPTIONS, "users": {"anna": _anna(areas=["garage"])}})
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    for step in ("system", "users", "user_edit"):
        flow = await hass.config_entries.options.async_configure(
            flow["flow_id"], {"next_step_id": step}
        )
    flow = await hass.config_entries.options.async_configure(flow["flow_id"], {"user": "anna"})
    assert flow["step_id"] == "user_settings"
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"name": "Anna", "rights": "per_area"}
    )
    assert flow["step_id"] == "user_area_rights"
    # Vorbelegung aus der alten Bereichsliste: Garage alles, Haus nichts
    defaults = {str(k): k.default() for k in flow["data_schema"].schema}
    assert defaults == {"Haus": [], "Garage": ["arm", "disarm", "end_alarm"]}
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"Haus": ["arm"], "Garage": ["disarm"]}
    )
    assert flow["type"] == "menu"
    stored = entry.options["users"]["anna"]
    assert stored["rights"] == "per_area"
    assert stored["area_rights"] == {"main": ["arm"], "garage": ["disarm"]}
    assert "areas" not in stored
    assert stored["pin_digest"]  # PIN bleibt erhalten

    # Zurück auf "alle Bereiche gleich"
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "user_edit"}
    )
    flow = await hass.config_entries.options.async_configure(flow["flow_id"], {"user": "anna"})
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"name": "Anna", "rights": "all"}
    )
    assert flow["type"] == "menu"
    stored = entry.options["users"]["anna"]
    assert stored["rights"] == "all"
    assert "area_rights" not in stored


async def test_area_device_hangs_below_main_device(hass: HomeAssistant) -> None:
    hass.states.async_set(GATE, "off", {"device_class": "window"})
    entry = make_entry(AREA_OPTIONS)
    await setup_entry(hass, entry)
    by_identifier = {
        identifier: device
        for device in dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
        for identifier in device.identifiers
    }
    main = by_identifier.get((DOMAIN, entry.entry_id))
    area = by_identifier.get((DOMAIN, f"{entry.entry_id}_garage"))
    assert main is not None
    assert area is not None
    assert area.via_device_id == main.id
