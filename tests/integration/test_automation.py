"""Integrationstests: Automatik pro Profil (Uhrzeit, Anwesenheit)."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import ServiceValidationError
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    async_capture_events,
    async_fire_time_changed,
)

from custom_components.hauswacht.const import EVENT_HAUSWACHT

from .conftest import DOOR, PANEL, TEST_MODE, WINDOW, make_entry, set_sensor, setup_entry

A = "person.a"
B = "person.b"


async def _service(hass: HomeAssistant, domain: str, service: str, **data: Any) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)
    await hass.async_block_till_done()


def _state(hass: HomeAssistant) -> str:
    state = hass.states.get(PANEL)
    assert state is not None
    return state.state


async def _at(hass: HomeAssistant, hour: int, minute: int, days: int = 1) -> None:
    """Simuliert die Uhrzeit an einem künftigen Tag (geplante Zeitpunkte liegen in der Zukunft)."""
    moment = (dt_util.now() + timedelta(days=days)).replace(
        hour=hour, minute=minute, second=0, microsecond=0
    )
    async_fire_time_changed(hass, moment)
    await hass.async_block_till_done()


def _next(after: Any, hour: int, minute: int) -> Any:
    """Nächstes Vorkommen einer Uhrzeit nach ``after`` (unabhängig von der Tageszeit des Tests)."""
    moment = after.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return moment if moment > after else moment + timedelta(days=1)


async def _fire(hass: HomeAssistant, moment: Any) -> None:
    async_fire_time_changed(hass, moment)
    await hass.async_block_till_done()


async def _later(hass: HomeAssistant, minutes: int) -> None:
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=minutes))
    await hass.async_block_till_done()


# Ortung weit weg vom Zuhause – „weg“ braucht seit 0.61 einen Beleg (ADR 0015)
FAR = {"latitude": 0.0, "longitude": 0.0, "gps_accuracy": 10}


async def _person(hass: HomeAssistant, entity_id: str, state: str) -> None:
    hass.states.async_set(entity_id, state, FAR if state not in ("home", "unknown") else {})
    await hass.async_block_till_done()


async def _setup(hass: HomeAssistant, extra: dict[str, Any] | None = None, **auto: Any) -> None:
    hass.states.async_set(A, "home")
    hass.states.async_set(B, "home")
    await setup_entry(
        hass, make_entry({"profiles": {"away": {**auto, "exit_delay": 0}}, **(extra or {})})
    )


# --- Uhrzeit ----------------------------------------------------------------


async def test_arm_and_disarm_by_time(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    # Fester Start um 12:00: Läuft der Test vor 06:30, lägen sonst beide geplanten Zeitpunkte
    # im ersten Schritt, und das Ergebnis hinge wieder von der Tageszeit des Testlaufs ab.
    freezer.move_to(dt_util.now().replace(hour=12, minute=0, second=0, microsecond=0))
    await _setup(hass, auto_arm_time="23:00:00", auto_disarm_time="06:30:00")
    # Die Uhr wirklich vorstellen und dabei nie über einen geplanten Zeitpunkt springen: Sonst
    # feuern Scharf und Unscharf im selben Schritt, und das Ergebnis hängt von der Tageszeit des
    # Testlaufs ab. Ein 06:30 vor dem ersten 23:00 ist harmlos (unscharf bleibt unscharf).
    arm_at = _next(dt_util.now(), 23, 0)
    freezer.move_to(arm_at)
    await _fire(hass, arm_at)
    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY
    disarm_at = _next(arm_at, 6, 30)
    freezer.move_to(disarm_at)
    await _fire(hass, disarm_at)
    assert _state(hass) == AlarmControlPanelState.DISARMED
    again = _next(disarm_at, 23, 0)
    freezer.move_to(again)
    await _fire(hass, again)
    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY


async def test_time_on_other_weekday_does_nothing(hass: HomeAssistant) -> None:
    today = dt_util.now().weekday()
    other = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"][(today + 1) % 7]
    await _setup(hass, auto_arm_time="23:00:00", auto_weekdays=[other])
    await _at(hass, 23, 0)
    assert _state(hass) == AlarmControlPanelState.DISARMED


async def test_automatic_arming_never_overrides_other_profile(hass: HomeAssistant) -> None:
    await _setup(hass, auto_arm_time="23:00:00")
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    await _at(hass, 23, 0)
    assert _state(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_disarm_time_does_not_end_running_alarm(hass: HomeAssistant) -> None:
    await _setup(hass, auto_disarm_time="06:30:00")
    await _service(hass, "alarm_control_panel", "alarm_arm_away", entity_id=PANEL)
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    await _at(hass, 6, 30, days=2)
    assert _state(hass) == AlarmControlPanelState.TRIGGERED


async def test_automatic_arming_fails_with_open_window(hass: HomeAssistant) -> None:
    await _setup(hass, auto_arm_time="23:00:00")
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    await _at(hass, 23, 0)
    assert _state(hass) == AlarmControlPanelState.DISARMED
    assert [e for e in events if e.data["type"] == "AutoArmFailed"]


# --- Anwesenheit ------------------------------------------------------------


async def test_arm_when_all_away_after_delay(hass: HomeAssistant) -> None:
    await _setup(hass, auto_away_persons=[A, B], auto_away_delay=15)
    await _person(hass, A, "not_home")
    await _person(hass, B, "Arbeit")
    await _later(hass, 10)
    assert _state(hass) == AlarmControlPanelState.DISARMED
    await _later(hass, 16)
    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY


async def test_return_within_delay_cancels(hass: HomeAssistant) -> None:
    await _setup(hass, auto_away_persons=[A, B], auto_away_delay=15)
    await _person(hass, A, "not_home")
    await _person(hass, B, "not_home")
    await _later(hass, 5)
    await _person(hass, B, "home")  # z. B. Handy war nur kurz aus dem WLAN
    await _later(hass, 20)
    assert _state(hass) == AlarmControlPanelState.DISARMED


# --- 0.61: „weg“ nur mit Beleg (ADR 0015) -------------------------------------


async def test_away_without_location_never_arms(hass: HomeAssistant) -> None:
    """Nur „nicht zuhause“ ohne Koordinaten (Router, WLAN): kein Beleg, nie weg."""
    await _setup(hass, auto_away_persons=[A], auto_away_delay=1)
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    hass.states.async_set(A, "not_home")
    await hass.async_block_till_done()
    await _later(hass, 5)
    assert _state(hass) == AlarmControlPanelState.DISARMED
    assert not [e for e in events if e.data["type"] == "AutoArmScheduled"]


async def test_gps_jump_in_house_needs_door(hass: HomeAssistant) -> None:
    """Ungenaue Ortung kurz neben dem Haus zählt nur nach einer Türöffnung."""
    near = {
        "latitude": hass.config.latitude + 0.002,  # gut 200 m daneben
        "longitude": hass.config.longitude,
        "gps_accuracy": 300,
    }
    await _setup(hass, auto_away_persons=[A], auto_away_delay=1)
    hass.states.async_set(A, "not_home", near)
    await hass.async_block_till_done()
    await _later(hass, 5)
    assert _state(hass) == AlarmControlPanelState.DISARMED  # GPS-Sprung im Haus
    hass.states.async_set(A, "home")
    await hass.async_block_till_done()
    set_sensor(hass, DOOR, "on")
    await hass.async_block_till_done()
    set_sensor(hass, DOOR, "off")
    hass.states.async_set(A, "not_home", near)  # nach der Tür geortet
    await hass.async_block_till_done()
    await _later(hass, 2)
    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY


async def test_weak_proof_door_then_wifi_gone(hass: HomeAssistant) -> None:
    """„Tür + Signal“ (unsicher): ohne Ortung weg, wenn das WLAN nach der Tür wegfällt."""
    hass.states.async_set(SIGNAL, "on")
    weak = {"homecoming_signals": {A: [SIGNAL]}, "away_proof_weak": [A]}
    await _setup(hass, weak, auto_away_persons=[A], auto_away_delay=1)
    hass.states.async_set(A, "not_home")  # Person ohne Koordinaten (z. B. Router)
    hass.states.async_set(SIGNAL, "off")  # WLAN fällt ohne Tür weg: schlafendes Handy
    await hass.async_block_till_done()
    await _later(hass, 3)
    assert _state(hass) == AlarmControlPanelState.DISARMED
    hass.states.async_set(SIGNAL, "on")
    await hass.async_block_till_done()
    set_sensor(hass, DOOR, "on")
    await hass.async_block_till_done()
    set_sensor(hass, DOOR, "off")
    hass.states.async_set(SIGNAL, "off")  # nach der Tür
    await hass.async_block_till_done()
    await _later(hass, 3)
    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY


async def test_simple_accuracy_counts_gps_jump(hass: HomeAssistant) -> None:
    near = {
        "latitude": hass.config.latitude + 0.002,
        "longitude": hass.config.longitude,
        "gps_accuracy": 300,
    }
    await _setup(hass, {"away_proof_accuracy": "simple"}, auto_away_persons=[A], auto_away_delay=1)
    hass.states.async_set(A, "not_home", near)
    await hass.async_block_till_done()
    await _later(hass, 2)
    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY


async def test_unknown_person_is_not_away(hass: HomeAssistant) -> None:
    await _setup(hass, auto_away_persons=[A, B], auto_away_delay=1)
    await _person(hass, A, "not_home")
    await _person(hass, B, "unknown")
    await _later(hass, 5)
    assert _state(hass) == AlarmControlPanelState.DISARMED


async def test_disarm_on_arrival_only_if_armed_automatically(hass: HomeAssistant) -> None:
    await _setup(hass, auto_away_persons=[A, B], auto_away_delay=1, auto_disarm_on_arrival=True)
    await _person(hass, A, "not_home")
    await _person(hass, B, "not_home")
    await _later(hass, 2)
    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY
    await _person(hass, A, "home")
    assert _state(hass) == AlarmControlPanelState.DISARMED


async def test_arrival_does_not_disarm_manual_arming(hass: HomeAssistant) -> None:
    await _setup(hass, auto_away_persons=[A, B], auto_disarm_on_arrival=True)
    await _person(hass, A, "not_home")
    await _person(hass, B, "not_home")
    await _service(hass, "alarm_control_panel", "alarm_arm_away", entity_id=PANEL)
    await _person(hass, A, "home")
    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY


# --- Optionen ---------------------------------------------------------------


async def test_options_flow_saves_automation(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "profiles"}
    )
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "profile_edit"}
    )
    flow = await hass.config_entries.options.async_configure(flow["flow_id"], {"profile": "night"})
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"],
        {
            "name": "Nacht",
            "automation": {
                "auto_arm_time": "22:45:00",
                "auto_weekdays": ["fri", "sat"],
                "auto_away_delay": 20,
            },
        },
    )
    assert flow["type"] is FlowResultType.MENU
    night = entry.options["profiles"]["night"]
    assert night["auto_arm_time"] == "22:45:00"
    assert night["auto_weekdays"] == ["fri", "sat"]
    assert night["auto_away_delay"] == 20
    assert night["zones"] == ["aussen", "keller"]


# --- 0.42: Unscharf mit Türbeleg ----------------------------------------------

SIGNAL = "binary_sensor.a_wlan"


async def _door(hass: HomeAssistant) -> None:
    """Haustür auf (und wieder zu); die Prüfung läuft nach der Reaktion der Anlage."""
    set_sensor(hass, DOOR, "on")
    await hass.async_block_till_done()
    await hass.async_block_till_done()
    set_sensor(hass, DOOR, "off")
    await hass.async_block_till_done()


async def _armed_and_away(hass: HomeAssistant, **auto: Any) -> None:
    await _setup(hass, auto_away_persons=[A, B], auto_arrival_mode="door", **auto)
    await _person(hass, A, "not_home")
    await _person(hass, B, "not_home")
    await _service(hass, "alarm_control_panel", "alarm_arm_away", entity_id=PANEL)
    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY


async def test_door_proof_disarms_during_entry_delay(hass: HomeAssistant) -> None:
    """Tür zuerst, Ortung 20 s später: noch in der Eingangsverzögerung unscharf."""
    await _armed_and_away(hass)
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    await _door(hass)
    assert _state(hass) == AlarmControlPanelState.PENDING
    await _person(hass, A, "home")
    assert _state(hass) == AlarmControlPanelState.DISARMED
    disarmed = [e for e in events if e.data["type"] == "AutoDisarmed"]
    assert disarmed[0].data["reason"] == "Rückkehr mit Türbeleg"


DIRECTION = "sensor.nahe_a_direction_of_travel"


async def _seconds(hass: HomeAssistant, seconds: int) -> None:
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=seconds))
    await hass.async_block_till_done()


async def _approach_setup(hass: HomeAssistant) -> list[Any]:
    hass.states.async_set(DIRECTION, "stationary")
    back = {"mode": "door", "persons": [A], "window": 5, "approach_delay": 90}
    await _setup(hass, {"homecoming_signals": {A: [DIRECTION]}}, entry_delay=30, **{"return": back})
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    await _service(hass, "alarm_control_panel", "alarm_arm_away", entity_id=PANEL)
    return events


async def test_approach_extends_entry_delay(hass: HomeAssistant) -> None:
    """ADR 0015: „nähert sich“ vorher → 90 s statt 30 s Eingangsverzögerung."""
    events = await _approach_setup(hass)
    hass.states.async_set(DIRECTION, "towards")
    await hass.async_block_till_done()
    await _door(hass)
    assert _state(hass) == AlarmControlPanelState.PENDING
    extended = [e for e in events if e.data["type"] == "EntryDelayExtended"]
    assert extended[0].data["seconds"] == 90
    assert extended[0].data["persons"] == [A]
    await _seconds(hass, 45)
    assert _state(hass) == AlarmControlPanelState.PENDING  # normal wäre schon Alarm
    await _seconds(hass, 95)
    assert _state(hass) == AlarmControlPanelState.TRIGGERED


async def test_no_approach_keeps_normal_entry_delay(hass: HomeAssistant) -> None:
    events = await _approach_setup(hass)
    await _door(hass)
    await _seconds(hass, 35)
    assert _state(hass) == AlarmControlPanelState.TRIGGERED
    assert not [e for e in events if e.data["type"] == "EntryDelayExtended"]


async def test_door_proof_arrival_first_then_door(hass: HomeAssistant) -> None:
    """Ortung vor der Tür (manuell scharf geschaltet): unscharf, sobald die Tür aufgeht."""
    await _armed_and_away(hass)
    await _person(hass, A, "home")
    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY  # ohne Tür passiert nichts
    await _later(hass, 3)
    await _door(hass)
    assert _state(hass) == AlarmControlPanelState.DISARMED


async def test_phantom_arrival_without_door_does_nothing(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    await _armed_and_away(hass)
    await _person(hass, A, "home")
    freezer.tick(timedelta(minutes=10))
    await _later(hass, 0)
    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY
    # Eine Tür weit außerhalb des Zeitfensters zählt nicht als Beleg
    await _door(hass)
    assert _state(hass) == AlarmControlPanelState.PENDING


async def test_door_without_arrival_still_alarms(hass: HomeAssistant) -> None:
    await _armed_and_away(hass)
    await _door(hass)
    assert _state(hass) == AlarmControlPanelState.PENDING
    await _later(hass, 2)
    assert _state(hass) == AlarmControlPanelState.TRIGGERED


async def test_door_proof_never_ends_running_alarm(hass: HomeAssistant) -> None:
    await _armed_and_away(hass)
    await _door(hass)
    await _later(hass, 2)
    assert _state(hass) == AlarmControlPanelState.TRIGGERED
    await _person(hass, A, "home")
    assert _state(hass) == AlarmControlPanelState.TRIGGERED


async def test_door_proof_needs_known_absence(hass: HomeAssistant) -> None:
    """Wer die ganze Zeit zuhause war, "kommt nicht heim" – die Tür allein schaltet nichts."""
    await _setup(hass, auto_away_persons=[A, B], auto_arrival_mode="door")
    await _person(hass, B, "not_home")
    await _service(hass, "alarm_control_panel", "alarm_arm_away", entity_id=PANEL)
    await _door(hass)
    await _person(hass, A, "home")  # unverändert zuhause
    assert _state(hass) == AlarmControlPanelState.PENDING


async def test_signal_keeps_person_home(hass: HomeAssistant) -> None:
    """Zusätzliches Signal meldet zuhause: nicht "alle weg", also nicht scharf."""
    hass.states.async_set(SIGNAL, "on")
    await _setup(
        hass,
        {"homecoming_signals": {A: [SIGNAL]}},
        auto_away_persons=[A, B],
        auto_away_delay=1,
    )
    await _person(hass, A, "not_home")
    await _person(hass, B, "not_home")
    await _later(hass, 3)
    assert _state(hass) == AlarmControlPanelState.DISARMED
    await _person(hass, SIGNAL, "off")
    await _later(hass, 3)
    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY


async def test_unavailable_signal_is_not_away(hass: HomeAssistant) -> None:
    hass.states.async_set(SIGNAL, "unavailable")
    await _setup(
        hass,
        {"homecoming_signals": {A: [SIGNAL]}},
        auto_away_persons=[A, B],
        auto_away_delay=1,
    )
    await _person(hass, A, "not_home")
    await _person(hass, B, "not_home")
    await _later(hass, 3)
    assert _state(hass) == AlarmControlPanelState.DISARMED


async def test_earliest_signal_counts_as_arrival(hass: HomeAssistant) -> None:
    """Das WLAN meldet zuhause, bevor die Person umschaltet: Das genügt als Rückkehr."""
    hass.states.async_set(SIGNAL, "off")
    await _setup(
        hass,
        {"homecoming_signals": {A: [SIGNAL]}},
        auto_away_persons=[A, B],
        auto_arrival_mode="door",
    )
    await _person(hass, A, "not_home")
    await _person(hass, B, "not_home")
    await _service(hass, "alarm_control_panel", "alarm_arm_away", entity_id=PANEL)
    await _door(hass)
    await _person(hass, SIGNAL, "on")
    assert _state(hass) == AlarmControlPanelState.DISARMED


async def test_options_flow_keeps_return_settings(hass: HomeAssistant) -> None:
    """„Bei Rückkehr“ gibt es nur auf der Einstellungsseite – der Dialog lässt es stehen."""
    hass.states.async_set(A, "home")
    back = {"mode": "door", "persons": [A], "window": 3, "approach_delay": 0, "approach_valid": 15}
    entry = make_entry({"profiles": {"away": {"return": back}}})
    await setup_entry(hass, entry)

    async def _edit(automation: dict[str, Any]) -> Any:
        flow = await hass.config_entries.options.async_init(entry.entry_id)
        flow = await hass.config_entries.options.async_configure(
            flow["flow_id"], {"next_step_id": "profiles"}
        )
        flow = await hass.config_entries.options.async_configure(
            flow["flow_id"], {"next_step_id": "profile_edit"}
        )
        flow = await hass.config_entries.options.async_configure(
            flow["flow_id"], {"profile": "away"}
        )
        return await hass.config_entries.options.async_configure(
            flow["flow_id"], {"name": "Abwesend", "automation": automation}
        )

    flow = await _edit({"auto_away_persons": [B]})
    assert flow["type"] is FlowResultType.MENU
    away = entry.options["profiles"]["away"]
    assert away["return"] == back
    assert away["auto_away_persons"] == [B]
    assert "auto_arrival_mode" not in away


async def test_old_settings_are_migrated_to_return(hass: HomeAssistant) -> None:
    """Update auf 0.61: „Unscharf bei Rückkehr“ wird zu „Bei Rückkehr“ (Version 5.2)."""
    entry = make_entry(
        {
            "profiles": {
                "away": {
                    "auto_away_persons": [A],
                    "auto_arrival_mode": "door",
                    "auto_arrival_window": 4,
                }
            }
        }
    )
    await setup_entry(hass, entry)
    assert entry.minor_version == 2
    away = entry.options["profiles"]["away"]
    assert away["return"] == {
        "mode": "door",
        "persons": [A],
        "window": 4,
        "approach_delay": 0,
        "approach_valid": 15,
    }
    assert away["auto_arrival_mode"] == "door"  # bleibt für ältere Versionen stehen
    from homeassistant.components.persistent_notification import (  # noqa: PLC0415
        _async_get_or_create_notifications,
    )

    notes = _async_get_or_create_notifications(hass)
    assert not any(key.startswith("hauswacht_return_") for key in notes)


# --- Gastmodus ----------------------------------------------------------------


async def test_guest_mode_blocks_automatic_arming(hass: HomeAssistant) -> None:
    await _setup(hass, auto_away_persons=[A, B], auto_away_delay=5)
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": "switch.hauswacht_guest_mode"}, blocking=True
    )
    state = hass.states.get("switch.hauswacht_guest_mode")
    assert state is not None
    assert state.state == "on"
    panel = hass.states.get(PANEL)
    assert panel is not None
    assert panel.attributes["guest_mode"] is True
    assert panel.attributes["guest_until"] is None  # bis zum Ausschalten
    await _person(hass, A, "not_home")
    await _person(hass, B, "not_home")
    await _later(hass, 6)
    assert _state(hass) == AlarmControlPanelState.DISARMED
    # von Hand geht weiterhin
    await hass.services.async_call(
        "hauswacht", "arm", {"entity_id": PANEL, "profile": "away"}, blocking=True
    )
    assert _state(hass) != AlarmControlPanelState.DISARMED


async def test_guest_mode_until_ends_by_itself(hass: HomeAssistant) -> None:
    await _setup(hass, auto_away_persons=[A, B], auto_away_delay=5)
    until = dt_util.now() + timedelta(hours=1)
    await hass.services.async_call(
        "hauswacht", "guest_mode", {"entity_id": PANEL, "until": until}, blocking=True
    )
    panel = hass.states.get(PANEL)
    assert panel is not None
    assert panel.attributes["guest_mode"] is True
    assert panel.attributes["guest_until"] is not None
    await _later(hass, 61)
    panel = hass.states.get(PANEL)
    assert panel is not None
    assert panel.attributes["guest_mode"] is False
    # danach greift die Automatik wieder
    await _person(hass, A, "not_home")
    await _person(hass, B, "not_home")
    await _later(hass, 6)
    assert _state(hass) != AlarmControlPanelState.DISARMED


async def test_guest_mode_from_alarm_card(hass: HomeAssistant, hass_ws_client: Any) -> None:
    await _setup(hass)
    client = await hass_ws_client(hass)
    until = (dt_util.utcnow() + timedelta(hours=4)).isoformat()
    await client.send_json({"id": 1, "type": "hauswacht/alarm/guest", "on": True, "until": until})
    result = await client.receive_json()
    assert result["result"]["ok"] is True
    panel = hass.states.get(PANEL)
    assert panel is not None
    assert panel.attributes["guest_mode"] is True
    await client.send_json({"id": 2, "type": "hauswacht/alarm/guest", "on": False})
    result = await client.receive_json()
    assert result["result"]["ok"] is True
    panel = hass.states.get(PANEL)
    assert panel is not None
    assert panel.attributes["guest_mode"] is False


# --- Zeitplan-Helfer -----------------------------------------------------------

SCHEDULE = "schedule.nacht"


async def _schedule(hass: HomeAssistant, state: str, next_in: float | None = None) -> None:
    attrs = {}
    if next_in is not None:
        attrs["next_event"] = (dt_util.now() + timedelta(seconds=next_in)).isoformat()
    hass.states.async_set(SCHEDULE, state, attrs)
    await hass.async_block_till_done()


async def test_schedule_arms_and_disarms(hass: HomeAssistant) -> None:
    hass.states.async_set(SCHEDULE, "off")
    await _setup(hass, auto_schedule=SCHEDULE)
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    await _schedule(hass, "on", next_in=3600)
    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY
    assert any(e.data["type"] == "AutoArmed" and e.data["reason"] == "Zeitplan" for e in events)
    await _schedule(hass, "off", next_in=3600)
    assert _state(hass) == AlarmControlPanelState.DISARMED


async def test_schedule_gap_at_midnight_is_continuous(hass: HomeAssistant) -> None:
    hass.states.async_set(SCHEDULE, "off")
    await _setup(hass, auto_schedule=SCHEDULE)
    await _schedule(hass, "on", next_in=3600)
    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY
    # Block bis 24:00, nächster ab 0:00: kurz "aus" -> bleibt scharf
    await _schedule(hass, "off", next_in=1)
    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY


async def test_schedule_after_restart_does_not_arm(hass: HomeAssistant) -> None:
    hass.states.async_set(SCHEDULE, "unavailable")
    await _setup(hass, auto_schedule=SCHEDULE)
    await _schedule(hass, "on")
    assert _state(hass) == AlarmControlPanelState.DISARMED


async def test_schedule_respects_guest_mode(hass: HomeAssistant) -> None:
    hass.states.async_set(SCHEDULE, "off")
    await _setup(hass, auto_schedule=SCHEDULE)
    await _service(hass, "hauswacht", "guest_mode", entity_id=PANEL, **{"on": True})
    await _schedule(hass, "on")
    assert _state(hass) == AlarmControlPanelState.DISARMED


async def test_schedule_end_leaves_other_profile_armed(hass: HomeAssistant) -> None:
    hass.states.async_set(SCHEDULE, "on")
    await _setup(hass, auto_schedule=SCHEDULE)
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    assert _state(hass) == AlarmControlPanelState.ARMED_NIGHT
    await _schedule(hass, "off")
    assert _state(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_direction_towards_is_no_arrival(hass: HomeAssistant) -> None:
    """Richtung "nähert sich" macht niemanden zuhause – keine Rückkehr, kein Unscharf."""
    direction = "sensor.home_bewegung_von_a"
    hass.states.async_set(direction, "away_from")
    await _setup(
        hass,
        {"homecoming_signals": {A: [direction]}},
        auto_away_persons=[A, B],
        auto_away_delay=1,
        auto_disarm_on_arrival=True,
    )
    await _person(hass, A, "not_home")
    await _person(hass, B, "not_home")
    await _later(hass, 2)
    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY
    # Fahrt in der Umgebung Richtung Zuhause: bleibt scharf
    await _person(hass, direction, "towards")
    await _later(hass, 1)
    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY
    # Angekommen in der Zone: das ist ein Beleg
    await _person(hass, direction, "arrived")
    assert _state(hass) == AlarmControlPanelState.DISARMED


async def test_direction_stationary_does_not_block_all_away(hass: HomeAssistant) -> None:
    """Richtung "steht" (z. B. im Büro) hält "alle weg" nicht auf."""
    direction = "sensor.home_bewegung_von_a"
    hass.states.async_set(direction, "stationary")
    await _setup(
        hass, {"homecoming_signals": {A: [direction]}}, auto_away_persons=[A, B], auto_away_delay=1
    )
    await _person(hass, A, "not_home")
    await _person(hass, B, "not_home")
    await _later(hass, 3)
    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY


# --- 0.63: Anwesenheit in der Testkarte (ADR 0016) ----------------------------


async def _sim_presence(hass: HomeAssistant, person: str, state: str) -> None:
    await _service(
        hass, "hauswacht", "simulate_presence", entity_id=PANEL, person=person, state=state
    )


def _presence(hass: HomeAssistant) -> dict[str, Any]:
    sim = next(s for s in hass.states.async_all("sensor") if "presence" in s.attributes)
    return sim.attributes["presence"]


async def _test_mode(hass: HomeAssistant, on: bool = True) -> None:
    await _service(hass, "switch", "turn_on" if on else "turn_off", entity_id=TEST_MODE)


async def test_presence_status_shows_reason(hass: HomeAssistant) -> None:
    await _setup(hass, auto_away_persons=[A, B], auto_away_delay=15)
    hass.states.async_set(A, "not_home")  # ohne Ortung: kein Beleg
    await hass.async_block_till_done()
    status = _presence(hass)
    assert status["persons"][A]["reason"]["kind"] == "no_proof"
    assert status["persons"][B]["state"] == "home"
    assert status["test_mode"] is False


async def test_simulate_presence_requires_test_mode(hass: HomeAssistant) -> None:
    await _setup(hass, auto_away_persons=[A, B], auto_away_delay=15)
    with pytest.raises(ServiceValidationError):
        await _sim_presence(hass, A, "away")


async def test_simulate_unknown_person_rejected(hass: HomeAssistant) -> None:
    await _setup(hass, auto_away_persons=[A, B], auto_away_delay=15)
    await _test_mode(hass)
    with pytest.raises(ServiceValidationError):
        await _sim_presence(hass, "person.fremd", "away")


async def test_simulated_away_arms_after_skip_wait(hass: HomeAssistant) -> None:
    await _setup(hass, auto_away_persons=[A, B], auto_away_delay=15)
    await _test_mode(hass)
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    await _sim_presence(hass, A, "away")
    await _sim_presence(hass, B, "away")
    assert hass.states.get(A).state == "home"  # Person in Home Assistant unverändert
    status = _presence(hass)
    assert status["persons"][A]["reason"]["kind"] == "simulated"
    assert status["profiles"][0]["due"]
    assert _state(hass) == AlarmControlPanelState.DISARMED
    await _service(hass, "hauswacht", "skip_wait", entity_id=PANEL)
    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY
    assert [e for e in events if e.data["type"] == "PresenceSimulated"]


async def test_simulated_away_without_proof_never_arms(hass: HomeAssistant) -> None:
    await _setup(hass, auto_away_persons=[A, B], auto_away_delay=1)
    await _test_mode(hass)
    await _sim_presence(hass, A, "away_no_proof")
    await _sim_presence(hass, B, "away_no_proof")
    await _later(hass, 5)
    assert _state(hass) == AlarmControlPanelState.DISARMED
    assert len(_presence(hass)["profiles"][0]["waiting"]) == 2


async def test_test_mode_off_resets_presence(hass: HomeAssistant) -> None:
    await _setup(hass, auto_away_persons=[A, B], auto_away_delay=15)
    await _test_mode(hass)
    await _sim_presence(hass, A, "away")
    await _sim_presence(hass, B, "away")
    assert _presence(hass)["profiles"][0]["due"]
    await _test_mode(hass, on=False)
    status = _presence(hass)
    assert status["persons"][A]["state"] == "home"
    assert not status["profiles"][0]["due"]
    await _later(hass, 20)
    assert _state(hass) == AlarmControlPanelState.DISARMED


async def test_simulated_return_disarms(hass: HomeAssistant) -> None:
    await _setup(hass, auto_away_persons=[A, B], auto_away_delay=15, auto_disarm_on_arrival=True)
    await _test_mode(hass)
    await _sim_presence(hass, A, "away")
    await _sim_presence(hass, B, "away")
    await _service(hass, "hauswacht", "skip_wait", entity_id=PANEL)
    assert _state(hass) == AlarmControlPanelState.ARMED_AWAY
    await _sim_presence(hass, A, "home")
    assert _state(hass) == AlarmControlPanelState.DISARMED
