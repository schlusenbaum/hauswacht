"""Integrationstests: Bereiche (unabhängig scharf schaltbar, frei benannt).

Alle Sensoren sind Testzustände; es sind keine Sirenen eingerichtet.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    async_capture_events,
    async_fire_time_changed,
)

from custom_components.hauswacht.const import DOMAIN, EVENT_HAUSWACHT
from custom_components.hauswacht.core.changes.system import delete_area
from custom_components.hauswacht.core.pin import hash_pin

from .conftest import DOOR, PANEL, WINDOW, ZONE_OPTIONS, make_entry, set_sensor, setup_entry

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
    # Bereich löschen wie auf der Einstellungsseite (dieselben Einstellungsregeln)
    change = delete_area(entry.options, "garage")
    assert not change.errors
    assert change.options is not None
    hass.config_entries.async_update_entry(entry, options=change.options)
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


async def test_every_event_names_its_area(hass: HomeAssistant) -> None:
    """Jedes hauswacht_event trägt area und area_name – wichtig für Automationen je Bereich."""
    await _setup(hass)
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    await _service(hass, "alarm_control_panel", "alarm_arm_away", entity_id=GARAGE_PANEL)
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=GARAGE_PANEL)
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL)
    assert events
    assert all("area" in e.data and "area_name" in e.data for e in events), [
        e.data for e in events if "area" not in e.data
    ]
    garage = [
        e.data for e in events if e.data["type"] == "StateChanged" and e.data["area"] == "garage"
    ]
    house = [
        e.data for e in events if e.data["type"] == "StateChanged" and e.data["area"] == "main"
    ]
    assert garage
    assert house
    assert garage[0]["area_name"] == "Garage"


async def test_system_wide_events_use_all(hass: HomeAssistant) -> None:
    await _setup(hass)
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    await hass.services.async_call(
        "hauswacht", "reset_code_lock", {"entity_id": PANEL}, blocking=True
    )
    reset = next(e.data for e in events if e.data["type"] == "CodeLockReset")
    assert reset["area"] == "all"


async def test_garage_uses_the_same_presence_signals(hass: HomeAssistant) -> None:
    """Ab 0.66.0b4: Die Garage sieht die zusätzlichen Signale und „eines reicht (nach Tür)“."""
    person, wlan = "person.a", "binary_sensor.a_wlan"
    hass.states.async_set(person, "home")
    hass.states.async_set(wlan, "on")
    garage = {
        **AREA_OPTIONS["profiles"]["garage_away"],
        "auto_away_persons": [person],
        "auto_away_delay": 1,
    }
    options = {
        **AREA_OPTIONS,
        "profiles": {"garage_away": garage},
        "homecoming_signals": {person: [wlan]},
        "presence_leave_mode": {person: "one"},
    }
    hass.states.async_set(GATE, "off", {"device_class": "window"})
    await setup_entry(hass, make_entry(options))
    set_sensor(hass, DOOR, "on")  # Haustür (Eingangstür des Hauses)
    await hass.async_block_till_done()
    set_sensor(hass, DOOR, "off")
    hass.states.async_set(wlan, "off")  # danach WLAN weg, person.a sagt weiter „home“
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=3))
    await hass.async_block_till_done()
    assert _state(hass, GARAGE_PANEL) == AlarmControlPanelState.ARMED_AWAY
