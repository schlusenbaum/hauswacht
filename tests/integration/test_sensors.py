"""Integrationstests: Sensoren, Zonen, Labels und Alarmauslösung in Home Assistant.

Alle Sensoren sind Testzustände. Es werden keine Sirenen oder Geräte angesprochen.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import label_registry as lr
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
    async_fire_time_changed,
)

from custom_components.hauswacht.const import EVENT_HAUSWACHT

from .conftest import (
    DOOR,
    MOTION,
    PANEL,
    TAMPER,
    WINDOW,
    make_entry,
    set_sensor,
    setup_entry,
)

OG_WINDOW = "binary_sensor.fenster_og"


async def _service(hass: HomeAssistant, domain: str, service: str, **data: Any) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)
    await hass.async_block_till_done()


async def _advance(hass: HomeAssistant, seconds: int) -> None:
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=seconds))
    await hass.async_block_till_done()


async def _sensor(hass: HomeAssistant, entity_id: str, state: str) -> None:
    set_sensor(hass, entity_id, state)
    await hass.async_block_till_done()


def _state(hass: HomeAssistant) -> str:
    state = hass.states.get(PANEL)
    assert state is not None
    return state.state


def _attr(hass: HomeAssistant, name: str) -> Any:
    state = hass.states.get(PANEL)
    assert state is not None
    return state.attributes[name]


async def _arm_night(hass: HomeAssistant) -> None:
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    assert _state(hass) == AlarmControlPanelState.ARMED_NIGHT


# --- Auslösung --------------------------------------------------------------


async def test_door_starts_entry_delay_then_alarm(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    await _arm_night(hass)
    await _sensor(hass, DOOR, "on")
    assert _state(hass) == AlarmControlPanelState.PENDING
    assert _attr(hass, "timer") == "entry_delay"
    await _advance(hass, 31)
    assert _state(hass) == AlarmControlPanelState.TRIGGERED
    assert _attr(hass, "trigger_sensor") == DOOR
    alarms = [e for e in events if e.data["type"] == "ActivateReaction"]
    assert len(alarms) == 1
    assert alarms[0].data["test_mode"] is False


async def test_disarm_within_entry_delay_prevents_alarm(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    await _arm_night(hass)
    await _sensor(hass, DOOR, "on")
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL)
    await _advance(hass, 60)
    assert _state(hass) == AlarmControlPanelState.DISARMED


async def test_window_triggers_immediately(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    await _arm_night(hass)
    await _sensor(hass, WINDOW, "on")
    assert _state(hass) == AlarmControlPanelState.TRIGGERED


async def test_motion_during_entry_delay_waits(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    await _arm_night(hass)
    await _sensor(hass, DOOR, "on")
    await _sensor(hass, MOTION, "on")
    assert _state(hass) == AlarmControlPanelState.PENDING


async def test_motion_alone_triggers(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    await _arm_night(hass)
    await _sensor(hass, MOTION, "on")
    assert _state(hass) == AlarmControlPanelState.TRIGGERED


async def test_sensor_outside_profile_is_ignored(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    await _service(hass, "alarm_control_panel", "alarm_arm_home", entity_id=PANEL)
    assert _state(hass) == AlarmControlPanelState.ARMED_HOME
    await _sensor(hass, MOTION, "on")  # Keller gehört nicht zu "Zuhause"
    assert _state(hass) == AlarmControlPanelState.ARMED_HOME


async def test_nothing_happens_when_disarmed(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    await _sensor(hass, DOOR, "on")
    await _sensor(hass, WINDOW, "on")
    assert _state(hass) == AlarmControlPanelState.DISARMED


async def test_alarm_in_test_mode_is_marked(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    await _service(hass, "switch", "turn_on", entity_id="switch.hauswacht_test_mode")
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    await _arm_night(hass)
    await _sensor(hass, WINDOW, "on")
    alarms = [e for e in events if e.data["type"] == "ActivateReaction"]
    assert alarms[0].data["test_mode"] is True


async def test_tamper_reported_while_disarmed(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    await _sensor(hass, TAMPER, "on")
    assert [e for e in events if e.data["type"] == "TamperDetected"]
    assert _state(hass) == AlarmControlPanelState.DISARMED


# --- Bereitschaft -----------------------------------------------------------


async def test_open_window_refuses_arming(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    await _sensor(hass, WINDOW, "on")
    assert _attr(hass, "open_sensors") == [WINDOW]
    with pytest.raises(ServiceValidationError):
        await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    assert _state(hass) == AlarmControlPanelState.DISARMED


async def test_unavailable_sensor_refuses_arming(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    await _sensor(hass, MOTION, "unavailable")
    with pytest.raises(ServiceValidationError):
        await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    # "Zuhause" überwacht den Keller nicht und darf deshalb scharf werden
    await _service(hass, "alarm_control_panel", "alarm_arm_home", entity_id=PANEL)
    assert _state(hass) == AlarmControlPanelState.ARMED_HOME


async def test_missing_sensor_entity_counts_as_unavailable(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry(), sensors=False)
    with pytest.raises(ServiceValidationError):
        await _service(hass, "alarm_control_panel", "alarm_arm_home", entity_id=PANEL)


async def test_confirm_bypasses_open_window(hass: HomeAssistant) -> None:
    entry = make_entry({"profiles": {"night": {"open_policy": "confirm"}}})
    await setup_entry(hass, entry)
    await _sensor(hass, WINDOW, "on")
    with pytest.raises(ServiceValidationError):
        await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    await _service(hass, "hauswacht", "arm", entity_id=PANEL, profile="night", confirm=True)
    assert _state(hass) == AlarmControlPanelState.ARMED_NIGHT
    assert _attr(hass, "bypassed_sensors") == [WINDOW]
    await _sensor(hass, WINDOW, "off")
    await _sensor(hass, WINDOW, "on")  # überbrückt: kein Alarm
    assert _state(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_profile_without_zones_cannot_be_armed(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry({"profiles": {"home": {"zones": []}}}))
    with pytest.raises(ServiceValidationError):
        await _service(hass, "alarm_control_panel", "alarm_arm_home", entity_id=PANEL)


async def test_window_opened_during_exit_delay_aborts(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    await _service(hass, "alarm_control_panel", "alarm_arm_away", entity_id=PANEL)
    assert _state(hass) == AlarmControlPanelState.ARMING
    await _sensor(hass, WINDOW, "on")
    assert _state(hass) == AlarmControlPanelState.ARMING  # während Ausgang kein Alarm
    await _advance(hass, 61)
    assert _state(hass) == AlarmControlPanelState.DISARMED


async def test_sensor_lost_while_armed_is_reported(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry())
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    await _arm_night(hass)
    await _sensor(hass, MOTION, "unavailable")
    assert [e for e in events if e.data["type"] == "SensorUnavailable"]
    assert _state(hass) == AlarmControlPanelState.ARMED_NIGHT


# --- Labels -----------------------------------------------------------------


async def test_label_adds_sensor_to_zone(hass: HomeAssistant) -> None:
    label = lr.async_get(hass).async_create("Hauswacht Garten")
    registry = er.async_get(hass)
    entry_reg = registry.async_get_or_create(
        "binary_sensor", "test", "gartentuer", suggested_object_id="gartentuer"
    )
    registry.async_update_entity(entry_reg.entity_id, labels={label.label_id})
    hass.states.async_set(entry_reg.entity_id, "off", {"device_class": "door"})

    options = {
        "zones": {
            "garten": {"name": "Garten", "entities": [], "label": label.label_id},
        },
        "profiles": {"home": {"zones": ["garten"]}},
    }
    await setup_entry(hass, make_entry(options))
    assert _attr(hass, "zones") == {"Garten": [entry_reg.entity_id]}

    await _service(hass, "alarm_control_panel", "alarm_arm_home", entity_id=PANEL)
    assert _attr(hass, "monitored_sensors") == [entry_reg.entity_id]
    hass.states.async_set(entry_reg.entity_id, "on", {"device_class": "door"})
    await hass.async_block_till_done()
    assert _state(hass) == AlarmControlPanelState.PENDING


async def test_label_change_does_not_drop_armed_sensor(hass: HomeAssistant) -> None:
    label = lr.async_get(hass).async_create("Hauswacht Garten")
    registry = er.async_get(hass)
    reg = registry.async_get_or_create("binary_sensor", "test", "gtor", suggested_object_id="gtor")
    registry.async_update_entity(reg.entity_id, labels={label.label_id})
    hass.states.async_set(reg.entity_id, "off", {"device_class": "window"})
    options = {
        "zones": {"garten": {"name": "Garten", "entities": [], "label": label.label_id}},
        "profiles": {"home": {"zones": ["garten"]}},
    }
    await setup_entry(hass, make_entry(options))
    await _service(hass, "alarm_control_panel", "alarm_arm_home", entity_id=PANEL)

    registry.async_update_entity(reg.entity_id, labels=set())  # Label entfernt
    await hass.async_block_till_done()
    hass.states.async_set(reg.entity_id, "on", {"device_class": "window"})
    await hass.async_block_till_done()
    assert _state(hass) == AlarmControlPanelState.TRIGGERED


# --- Rollen-Ausnahmen -------------------------------------------------------


async def test_role_override_makes_window_delayed(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry({"sensor_roles": {WINDOW: "entry"}}))
    await _arm_night(hass)
    await _sensor(hass, WINDOW, "on")
    assert _state(hass) == AlarmControlPanelState.PENDING


# --- Optionen ---------------------------------------------------------------


async def test_options_flow_add_zone_and_assign(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "zones"}
    )
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "zone_add"}
    )
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"name": "Leer", "entities": []}
    )
    assert flow["errors"] == {"base": "zone_empty"}
    # Ein Sensor darf nur in einer Zone sein: das Küchenfenster steckt schon in "Außenhaut"
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"name": "Obergeschoss", "entities": [WINDOW, OG_WINDOW]}
    )
    assert flow["errors"] == {"base": "zone_overlap"}
    assert "Außenhaut" in flow["description_placeholders"]["conflicts"]
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"name": "Obergeschoss", "entities": [OG_WINDOW]}
    )
    assert flow["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.options["zones"]["obergeschoss"]["entities"] == [OG_WINDOW]


async def test_options_flow_edit_zone_keeps_own_sensors(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "zones"}
    )
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "zone_edit"}
    )
    flow = await hass.config_entries.options.async_configure(flow["flow_id"], {"zone": "keller"})
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"name": "Keller", "entities": [MOTION, DOOR]}
    )
    assert flow["errors"] == {"base": "zone_overlap"}
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"name": "Keller", "entities": [MOTION]}
    )
    assert flow["type"] is FlowResultType.CREATE_ENTRY


async def test_options_flow_delete_zone_removes_it_from_profiles(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "zones"}
    )
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "zone_delete"}
    )
    flow = await hass.config_entries.options.async_configure(flow["flow_id"], {"zone": "keller"})
    assert flow["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert "keller" not in entry.options["zones"]
    assert entry.options["profiles"]["night"]["zones"] == ["aussenhaut"]


async def test_options_flow_role_override(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "roles"}
    )
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"entity": WINDOW, "role": "entry"}
    )
    assert flow["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.options["sensor_roles"] == {WINDOW: "entry"}


async def test_options_flow_monitoring(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "monitoring"}
    )
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"stale_after_hours": 26}
    )
    assert flow["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options["stale_after_hours"] == 26


# --- Letzter Kontakt (last_seen) --------------------------------------------


def _device_with_last_seen(hass: HomeAssistant) -> tuple[str, str]:
    """Legt ein Testgerät mit Kontakt und Zigbee2MQTT-artigem last_seen-Sensor an."""
    source = MockConfigEntry(domain="test")
    source.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=source.entry_id, identifiers={("test", "kontakt1")}
    )
    registry = er.async_get(hass)
    contact = registry.async_get_or_create(
        "binary_sensor",
        "test",
        "0x1_contact",
        suggested_object_id="testkontakt",
        device_id=device.id,
        config_entry=source,
    )
    last_seen = registry.async_get_or_create(
        "sensor",
        "test",
        "0x1_last_seen_zigbee2mqtt",
        suggested_object_id="testkontakt_last_seen",
        device_id=device.id,
        config_entry=source,
        original_device_class="timestamp",
    )
    return contact.entity_id, last_seen.entity_id


@pytest.mark.parametrize(("hours_ago", "armable"), [(3, False), (0.1, True)])
async def test_stale_check_uses_device_last_seen(
    hass: HomeAssistant, hours_ago: float, armable: bool
) -> None:
    contact, last_seen = _device_with_last_seen(hass)
    hass.states.async_set(contact, "off", {"device_class": "window"})  # gerade "frisch" in HA
    seen = dt_util.utcnow() - timedelta(hours=hours_ago)
    hass.states.async_set(last_seen, seen.isoformat(), {"device_class": "timestamp"})
    options = {
        "zones": {"og": {"name": "OG", "entities": [contact], "label": None}},
        "profiles": {"home": {"zones": ["og"]}},
        "stale_after_hours": 1,
    }
    await setup_entry(hass, make_entry(options))
    assert _attr(hass, "last_contact")[contact] is not None

    if armable:
        await _service(hass, "alarm_control_panel", "alarm_arm_home", entity_id=PANEL)
        assert _state(hass) == AlarmControlPanelState.ARMED_HOME
    else:
        assert _attr(hass, "unavailable_sensors") == [contact]
        with pytest.raises(ServiceValidationError):
            await _service(hass, "alarm_control_panel", "alarm_arm_home", entity_id=PANEL)
