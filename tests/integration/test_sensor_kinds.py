"""Integrationstests: weitere Sensorarten als Melder und Kamerabild in der Alarm-Nachricht.

Alle Zustände sind Testzustände; es gibt keine Geräte, keine Kamera und keine Sirenen.
"""

from __future__ import annotations

from typing import Any

import pytest
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from pytest_homeassistant_custom_component.common import async_mock_service

from .conftest import DOOR, MOTION, PANEL, TAMPER, TEST_MODE, WINDOW, make_entry, setup_entry

LOCK = "lock.haustuer_schloss"
COVER = "cover.garagentor"
BELL = "event.klingel"
VIBRATION = "sensor.erschuetterung"
PHONE = "mobile_app_testhandy"
CAMERA = "camera.einfahrt"
FLUR = "camera.flur"

OPTIONS: dict[str, Any] = {
    "zones": {
        "aussenhaut": {
            "name": "Außenhaut",
            "entities": [DOOR, WINDOW, TAMPER, LOCK, COVER, BELL, VIBRATION],
            "label": None,
        },
        "keller": {"name": "Keller", "entities": [MOTION], "label": None},
    },
    "sensor_thresholds": {VIBRATION: {"above": 5}},
}


async def _service(hass: HomeAssistant, domain: str, service: str, **data: Any) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)
    await hass.async_block_till_done()


def _panel(hass: HomeAssistant) -> str:
    state = hass.states.get(PANEL)
    assert state is not None
    return state.state


async def _setup(hass: HomeAssistant, **options: Any) -> None:
    hass.states.async_set(LOCK, "locked")
    hass.states.async_set(COVER, "closed", {"device_class": "garage"})
    hass.states.async_set(BELL, "2026-11-11T20:00:00.000+00:00", {"device_class": "doorbell"})
    hass.states.async_set(VIBRATION, "0.4")
    await setup_entry(hass, make_entry({**OPTIONS, **options}))


async def test_unlocked_lock_starts_entry_delay(hass: HomeAssistant) -> None:
    await _setup(hass)
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    hass.states.async_set(LOCK, "unlocked")
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.PENDING


async def test_open_cover_blocks_arming(hass: HomeAssistant) -> None:
    await _setup(hass)
    hass.states.async_set(COVER, "open", {"device_class": "garage"})
    await hass.async_block_till_done()
    with pytest.raises(ServiceValidationError):
        await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    assert _panel(hass) == AlarmControlPanelState.DISARMED


async def test_threshold_sensor_triggers_instantly(hass: HomeAssistant) -> None:
    await _setup(hass)
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    hass.states.async_set(VIBRATION, "4.9")
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    hass.states.async_set(VIBRATION, "7.2")
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.TRIGGERED


async def test_event_triggers_but_restart_does_not(hass: HomeAssistant) -> None:
    await _setup(hass)
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    # Neustart: unavailable -> alter Zeitpunkt löst nicht aus
    hass.states.async_set(BELL, "unavailable")
    await hass.async_block_till_done()
    hass.states.async_set(BELL, "2026-11-11T20:00:00.000+00:00", {"device_class": "doorbell"})
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    # Neues Ereignis löst aus
    hass.states.async_set(BELL, "2026-11-11T21:00:00.000+00:00", {"device_class": "doorbell"})
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.TRIGGERED


async def test_event_is_never_open(hass: HomeAssistant) -> None:
    await _setup(hass)
    hass.states.async_set(BELL, "2026-11-11T21:00:00.000+00:00", {"device_class": "doorbell"})
    await hass.async_block_till_done()
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_simulated_event_is_a_pulse(hass: HomeAssistant) -> None:
    await _setup(hass)
    await _service(hass, "switch", "turn_on", entity_id=TEST_MODE)
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    await _service(hass, "hauswacht", "simulate_state", entity_id=PANEL, sensor=BELL, state="on")
    assert _panel(hass) == AlarmControlPanelState.TRIGGERED
    runtime = hass.config_entries.async_entries("hauswacht")[0].runtime_data
    assert runtime.simulated(BELL) is None  # nicht dauerhaft "offen"


async def test_alarm_push_carries_camera_image(hass: HomeAssistant) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    await _setup(
        hass,
        notify_system=[PHONE],
        profiles={"night": {"camera": CAMERA}},
        sensor_cameras={WINDOW: FLUR},
    )
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    hass.states.async_set(WINDOW, "on", {"device_class": "window"})
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.TRIGGERED
    alarm = [c for c in push if "data" in c.data and "image" in c.data["data"]]
    assert alarm, push
    # Kamera am Melder hat Vorrang vor der des Profils
    assert alarm[0].data["data"]["image"] == f"/api/camera_proxy/{FLUR}"


async def test_profile_camera_used_without_sensor_camera(hass: HomeAssistant) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    await _setup(hass, notify_system=[PHONE], profiles={"night": {"camera": CAMERA}})
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    hass.states.async_set(VIBRATION, "9")
    await hass.async_block_till_done()
    images = [c.data["data"].get("image") for c in push if "data" in c.data]
    assert f"/api/camera_proxy/{CAMERA}" in images


async def test_alarm_images_only_when_enabled(hass: HomeAssistant) -> None:
    snapshots = async_mock_service(hass, "camera", "snapshot")
    await _setup(hass, profiles={"night": {"camera": CAMERA, "save_snapshots": True}})
    hass.config.allowlist_external_dirs = {hass.config.path("media")}
    hass.config.media_dirs = {"local": hass.config.path("media")}
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    hass.states.async_set(WINDOW, "on", {"device_class": "window"})
    await hass.async_block_till_done()
    assert len(snapshots) == 1
    assert snapshots[0].data["entity_id"] == CAMERA
    assert snapshots[0].data["filename"].endswith("_kuechenfenster_1.jpg")


async def test_sensor_detail_threshold_and_camera(hass: HomeAssistant) -> None:
    entry = make_entry(OPTIONS)
    hass.states.async_set(VIBRATION, "0.4")
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    for step in ("system", "sensor_behaviour"):
        flow = await hass.config_entries.options.async_configure(
            flow["flow_id"], {"next_step_id": step}
        )
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"stale_after_hours": 0, "entity": VIBRATION}
    )
    assert flow["step_id"] == "sensor_detail"
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"role": "auto", "above": 3, "below": 8}
    )
    assert flow["errors"] == {"base": "threshold_range"}
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"role": "auto", "above": 8, "camera": CAMERA}
    )
    assert flow["type"] == "menu"
    assert entry.options["sensor_thresholds"] == {VIBRATION: {"above": 8.0}}
    assert entry.options["sensor_cameras"] == {VIBRATION: CAMERA}
