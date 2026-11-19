"""Integrationstests: allgemeines Keypad (ADR 0012) – Aktion keypad_input und Anzeige-Entität.

Kein echtes Gerät: Die Tests rufen die Aktion so auf, wie es ein Blueprint oder eine Automation
tun würde. Es gibt keine Sirenen.
"""

from __future__ import annotations

from typing import Any

import pytest
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import Context, HomeAssistant
from homeassistant.exceptions import Unauthorized
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockUser, async_capture_events

from custom_components.hauswacht.const import DOMAIN, EVENT_HAUSWACHT
from custom_components.hauswacht.core.pin import hash_pin

from .conftest import PANEL, WINDOW, make_entry, set_sensor, setup_entry

PIN = "1357"
CARD = "04A1B2C3"


def _options(**keypad: Any) -> dict[str, Any]:
    hashed = hash_pin(PIN)
    return {
        "users": {
            "anna": {
                "name": "Anna",
                "pin_salt": hashed.salt,
                "pin_digest": hashed.digest,
                "tags": [CARD],
            }
        },
        "controls": {
            "flur": {
                "name": "Keypad Flur",
                "kind": "generic_keypad",
                "buttons": {"night": "night", "home": "home"},
                **keypad,
            }
        },
    }


async def _setup(hass: HomeAssistant, **keypad: Any) -> Any:
    entry = make_entry(_options(**keypad))
    await setup_entry(hass, entry)
    return entry


async def _input(
    hass: HomeAssistant, context: Context | None = None, **data: Any
) -> dict[str, Any]:
    response = await hass.services.async_call(
        DOMAIN,
        "keypad_input",
        {"keypad": "flur", **data},
        blocking=True,
        return_response=True,
        context=context,
    )
    await hass.async_block_till_done()
    assert isinstance(response, dict)
    return response


def _panel(hass: HomeAssistant) -> str:
    state = hass.states.get(PANEL)
    assert state is not None
    return state.state


def _display_entity(hass: HomeAssistant, entry: Any) -> str:
    entity_id = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{entry.entry_id}_keypad_flur"
    )
    assert entity_id is not None
    return entity_id


async def test_arm_and_disarm_with_response_and_display(hass: HomeAssistant) -> None:
    entry = await _setup(hass)
    display = _display_entity(hass, entry)
    assert hass.states.get(display).state == "disarmed"  # type: ignore[union-attr]
    answer = await _input(hass, button="Night", code=PIN)
    assert answer["result"] == "ok"
    assert answer["display"] == "armed_night"
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    state = hass.states.get(display)
    assert state is not None
    assert state.state == "armed_night"
    assert state.attributes["last_result"] == "ok"
    assert PIN not in str(state.attributes)
    answer = await _input(hass, button="disarm", code=CARD)
    assert answer["result"] == "ok"
    assert _panel(hass) == AlarmControlPanelState.DISARMED
    panel = hass.states.get(PANEL)
    assert panel is not None
    assert panel.attributes["changed_by"] == "Anna (Keypad Flur)"


async def test_wrong_pin_and_duplicates(hass: HomeAssistant) -> None:
    await _setup(hass)
    await _input(hass, button="night", code=PIN)
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    answer = await _input(hass, button="disarm", code="0000")
    assert answer["result"] == "invalid_code"
    # Gleiche Eingabe sofort noch einmal (Funk sendet doppelt): zählt nur einmal
    again = await _input(hass, button="disarm", code="0000")
    assert again["result"] == "invalid_code"
    assert len([e for e in events if e.data.get("type") == "InvalidCode"]) == 1
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_disarm_needs_credential(hass: HomeAssistant) -> None:
    await _setup(hass)
    await _input(hass, button="night", code=PIN)
    answer = await _input(hass, button="disarm")
    assert answer["result"] == "invalid_code"
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_not_ready_names_open_sensors(hass: HomeAssistant) -> None:
    await _setup(hass)
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    answer = await _input(hass, button="night", code=PIN)
    assert answer["result"] == "not_ready"
    assert answer["open_sensors"]
    assert _panel(hass) == AlarmControlPanelState.DISARMED


async def test_unknown_button_and_keypad(hass: HomeAssistant) -> None:
    entry = await _setup(hass)
    answer = await _input(hass, button="away", code=PIN)
    assert answer["result"] == "unknown_button"
    events = async_capture_events(hass, EVENT_HAUSWACHT)
    answer = await _input(hass, keypad="garage", button="night", code=PIN)
    assert answer["result"] == "unknown_keypad"
    assert any(e.data.get("type") == "UnknownKeypad" for e in events)
    assert _panel(hass) == AlarmControlPanelState.DISARMED
    # Beim Anlegen steht das gemeldete Keypad schon im Formular
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    for step in ("system", "controls", "control_add_generic_keypad"):
        flow = await hass.config_entries.options.async_configure(
            flow["flow_id"], {"next_step_id": step}
        )
    assert flow["step_id"] == "control_generic_keypad"
    assert "`garage`" in flow["description_placeholders"]["unknown"]


async def test_display_entity_as_keypad_reference(hass: HomeAssistant) -> None:
    entry = await _setup(hass)
    answer = await _input(hass, keypad=_display_entity(hass, entry), button="home", code=PIN)
    assert answer["result"] == "ok"
    assert _panel(hass) == AlarmControlPanelState.ARMED_HOME


async def test_normal_users_may_not_call(
    hass: HomeAssistant, hass_read_only_user: MockUser, hass_admin_user: MockUser
) -> None:
    await _setup(hass)
    with pytest.raises(Unauthorized):
        await _input(hass, Context(user_id=hass_read_only_user.id), button="emergency")
    answer = await _input(hass, Context(user_id=hass_admin_user.id), button="home", code=PIN)
    assert answer["result"] == "ok"


async def test_emergency_off_reports_unknown_button(hass: HomeAssistant) -> None:
    await _setup(hass)
    answer = await _input(hass, button="emergency")
    assert answer["result"] == "unknown_button"
    assert _panel(hass) == AlarmControlPanelState.DISARMED


async def test_options_add_generic_keypad(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    for step in ("system", "controls", "control_add_generic_keypad"):
        flow = await hass.config_entries.options.async_configure(
            flow["flow_id"], {"next_step_id": step}
        )
    assert flow["step_id"] == "control_generic_keypad"
    base = {"name": "Keypad Garage", "area": "__all__", "login": "pin_or_card", "emergency": "off"}
    flow = await hass.config_entries.options.async_configure(flow["flow_id"], base)
    assert flow["errors"] == {"base": "control_no_buttons"}
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {**base, "button_1": "disarm", "profile_1": "night"}
    )
    assert flow["errors"] == {"base": "control_button_reserved"}
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {**base, "button_1": "Away", "profile_1": "away"}
    )
    assert flow["type"] == "menu"
    stored = entry.options["controls"]["keypad_garage"]
    assert stored["kind"] == "generic_keypad"
    assert stored["buttons"] == {"away": "away"}


async def test_wrong_pin_warnings_replace_each_other(hass: HomeAssistant) -> None:
    from pytest_homeassistant_custom_component.common import async_mock_service  # noqa: PLC0415

    push = async_mock_service(hass, "notify", "mobile_app_handy")
    entry = make_entry({**_options(), "notify_system": ["mobile_app_handy"]})
    await setup_entry(hass, entry)
    for code in ("0001", "0002", "0003", "0004"):  # verschieden: keine doppelte Meldung
        await _input(hass, button="night", code=code)
    warnings = [c for c in push if c.data["message"] != "clear_notification"]
    assert warnings
    assert all(c.data["data"]["tag"] == "hauswacht_code" for c in warnings)
