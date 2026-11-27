"""Integrationstests: Ausgangserkennung (ADR 0014) – Rausgehen ohne PIN erkennen.

Kein echtes Gerät: Sensoren und Handys sind Testzustände, notify ist eine Attrappe. Keine Sirenen.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    async_capture_events,
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.hauswacht.const import DOMAIN, EVENT_HAUSWACHT

from .conftest import DOOR, MOTION, PANEL, make_entry, set_sensor, setup_entry

BEN = "person.ben"
WLAN = "binary_sensor.ben_wlan"
PHONE = "mobile_app_testhandy"


def _options(**exit_detect: Any) -> dict[str, Any]:
    return {
        "notify_system": [PHONE],
        "homecoming_signals": {BEN: [WLAN]},
        "presence_leave_mode": {BEN: "one"},
        "profiles": {
            "night": {
                "entry_delay": 30,
                "exit_detect": {"enabled": True, "wait": 3, **exit_detect},
            }
        },
    }


async def _setup(hass: HomeAssistant, **exit_detect: Any) -> list[ServiceCall]:
    push = async_mock_service(hass, "notify", PHONE)
    hass.states.async_set(BEN, "home")
    hass.states.async_set(WLAN, "on")
    await setup_entry(hass, make_entry(_options(**exit_detect)))
    await hass.services.async_call(
        "alarm_control_panel", "alarm_arm_night", {"entity_id": PANEL}, blocking=True
    )
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    return push


def _panel(hass: HomeAssistant) -> str:
    state = hass.states.get(PANEL)
    assert state is not None
    return state.state


async def _wait(hass: HomeAssistant, freezer: FrozenDateTimeFactory, seconds: float) -> None:
    """Uhr in kleinen Schritten vorstellen (Prüfung alle 5 Sekunden)."""
    step = 5.0
    passed = 0.0
    while passed < seconds:
        freezer.tick(timedelta(seconds=step))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        passed += step


async def _door(hass: HomeAssistant) -> None:
    set_sensor(hass, DOOR, "on")
    await hass.async_block_till_done()


async def test_person_goes_out_stays_armed(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    push = await _setup(hass)
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    await _door(hass)
    assert _panel(hass) == AlarmControlPanelState.PENDING
    assert any(e.data.get("type") == "ExitWaitStarted" for e in events)
    # sofortige Nachricht mit „Alarm jetzt“
    first = [c for c in push if c.data.get("message") != "clear_notification"]
    assert first
    actions = first[-1].data["data"]["actions"]
    assert actions[0]["title"] in ("Alarm jetzt", "Alarm now")
    await _wait(hass, freezer, 20)
    hass.states.async_set(WLAN, "off")  # Bens Handy verliert das WLAN
    await hass.async_block_till_done()
    await _wait(hass, freezer, 40)  # 30 s Puffer
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    assert any(e.data.get("type") == "ExitDetected" for e in events)
    await _wait(hass, freezer, 300)
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT  # kein Alarm danach


async def test_nobody_goes_out_alarm_after_wait(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    await _setup(hass)
    await _door(hass)
    await _wait(hass, freezer, 60)
    assert _panel(hass) == AlarmControlPanelState.PENDING  # nicht nach 30 s: stille Wartezeit
    await _wait(hass, freezer, 130)
    assert _panel(hass) == AlarmControlPanelState.TRIGGERED


async def test_short_hiccup_is_not_going_out(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    await _setup(hass)
    await _door(hass)
    hass.states.async_set(WLAN, "off")
    await hass.async_block_till_done()
    await _wait(hass, freezer, 10)
    hass.states.async_set(WLAN, "on")  # nach 10 s wieder da
    await hass.async_block_till_done()
    await _wait(hass, freezer, 60)
    assert _panel(hass) == AlarmControlPanelState.PENDING


async def test_inside_sensor_without_motion_normal_entry_delay(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    await _setup(hass, inside=[MOTION])
    await _door(hass)
    await _wait(hass, freezer, 35)
    assert _panel(hass) == AlarmControlPanelState.TRIGGERED  # drinnen keine Bewegung


async def test_nobody_home_normal_entry_delay(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    await _setup(hass)
    hass.states.async_set(WLAN, "off")
    hass.states.async_set(BEN, "not_home")
    await hass.async_block_till_done()
    await _door(hass)
    await _wait(hass, freezer, 35)
    assert _panel(hass) == AlarmControlPanelState.TRIGGERED


async def test_alarm_now(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    await _setup(hass)
    await _door(hass)
    entry = hass.config_entries.async_entries("hauswacht")[0]
    entry.runtime_data.exit_alarm_now()
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.TRIGGERED


async def test_inside_sensor_in_test_card_and_simulation(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Melder im Haus erscheint in der Testkarte (je nach Profil) und lässt sich simulieren."""
    light = "light.treppe"
    hass.states.async_set(light, "off")
    async_mock_service(hass, "notify", PHONE)
    hass.states.async_set(BEN, "home")
    hass.states.async_set(WLAN, "on")
    entry = make_entry(_options(inside=[light]))
    await setup_entry(hass, entry)
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": "switch.hauswacht_test_mode"}, blocking=True
    )
    await hass.services.async_call(
        "alarm_control_panel", "alarm_arm_night", {"entity_id": PANEL}, blocking=True
    )
    await hass.async_block_till_done()
    sim_id = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{entry.entry_id}_simulation"
    )
    assert sim_id is not None
    rows = {r["entity_id"]: r for r in hass.states.get(sim_id).attributes["sensors"]}
    assert rows[light]["status"] == "exit_inside"
    await hass.services.async_call(
        DOMAIN,
        "simulate_state",
        {"entity_id": PANEL, "sensor": light, "state": "on"},
        blocking=True,
    )
    await hass.async_block_till_done()
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    await _sim(hass, DOOR, "on")
    # Melder im Haus meldete vorher: automatischer Durchgang, bleibt scharf (Entscheidung C)
    assert any(e.data.get("type") == "ExitPassage" for e in events)
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    # Mülleimer: Tür zu, nach 2 Minuten wieder auf (zurück) – kein Alarm
    await _sim(hass, DOOR, "off")
    await _wait(hass, freezer, 120)
    await _sim(hass, DOOR, "on")
    await _sim(hass, DOOR, "off")
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    # nach der Durchgangszeit (Standard 5 min) ist die Tür wieder scharf
    await _wait(hass, freezer, 240)
    await _sim(hass, DOOR, "on")
    assert _panel(hass) == AlarmControlPanelState.PENDING


async def _sim(hass: HomeAssistant, sensor: str, state: str) -> None:
    await hass.services.async_call(
        DOMAIN,
        "simulate_state",
        {"entity_id": PANEL, "sensor": sensor, "state": state},
        blocking=True,
    )
    await hass.async_block_till_done()


async def test_alarm_now_during_automatic_passage(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    light = "light.treppe"
    hass.states.async_set(light, "off")
    async_mock_service(hass, "notify", PHONE)
    hass.states.async_set(BEN, "home")
    hass.states.async_set(WLAN, "on")
    await setup_entry(hass, make_entry(_options(inside=[light])))
    await hass.services.async_call(
        "alarm_control_panel", "alarm_arm_night", {"entity_id": PANEL}, blocking=True
    )
    await hass.async_block_till_done()
    hass.states.async_set(light, "on")  # echtes Licht im Haus geht an
    await hass.async_block_till_done()
    await _door(hass)
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    entry = hass.config_entries.async_entries("hauswacht")[0]
    entry.runtime_data.exit_alarm_now()
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.TRIGGERED


async def test_automatic_passage_ends_when_phone_away(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Ben geht raus, sein Handy ortet „weg“: Durchgang endet sofort, Tür wieder scharf."""
    light = "light.treppe"
    hass.states.async_set(light, "off")
    async_mock_service(hass, "notify", PHONE)
    hass.states.async_set(BEN, "home")
    hass.states.async_set(WLAN, "on")
    await setup_entry(hass, make_entry(_options(inside=[light])))
    await hass.services.async_call(
        "alarm_control_panel", "alarm_arm_night", {"entity_id": PANEL}, blocking=True
    )
    await hass.async_block_till_done()
    hass.states.async_set(light, "on")
    await hass.async_block_till_done()
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    await _door(hass)
    assert any(e.data.get("type") == "ExitPassage" for e in events)
    state = hass.states.get(PANEL)
    assert state is not None
    assert state.attributes["exit_detection"]["mode"] == "passage"
    assert BEN in state.attributes["exit_detection"]["persons"]
    set_sensor(hass, DOOR, "off")
    await hass.async_block_till_done()
    hass.states.async_set(WLAN, "off")  # Bens Handy ist weg
    await hass.async_block_till_done()
    await _wait(hass, freezer, 40)  # 30 s Puffer
    assert any(e.data.get("type") == "ExitDetected" for e in events)
    state = hass.states.get(PANEL)
    assert state is not None
    assert state.attributes["exit_detection"] is None
    # Durchgang vorbei: Tür auf -> Eingangsverzögerung
    await _door(hass)
    assert _panel(hass) == AlarmControlPanelState.PENDING
