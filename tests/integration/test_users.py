"""Integrationstests: Benutzer, gemeinsame PINs, Rechte, Gäste, Bedrohungs-PIN."""

from __future__ import annotations

from typing import Any

import pytest
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.components.persistent_notification import (
    _async_get_or_create_notifications,
)
from homeassistant.core import Context, HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from pytest_homeassistant_custom_component.common import MockUser, async_mock_service

from custom_components.hauswacht.const import PUSH_ACTION_EVENT
from custom_components.hauswacht.core.pin import hash_pin

from .conftest import PANEL, WINDOW, make_entry, set_sensor, setup_entry

PHONE = "mobile_app_testhandy"
WATCH = "mobile_app_notfall"


def user(name: str, pin: str | None = None, duress: str | None = None, **extra: Any) -> dict:
    data: dict[str, Any] = {"name": name, **extra}
    if pin:
        hashed = hash_pin(pin)
        data["pin_salt"], data["pin_digest"] = hashed.salt, hashed.digest
    if duress:
        hashed = hash_pin(duress)
        data["duress_salt"], data["duress_digest"] = hashed.salt, hashed.digest
    return data


async def _service(hass: HomeAssistant, domain: str, service: str, **data: Any) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)
    await hass.async_block_till_done()


def _panel(hass: HomeAssistant) -> Any:
    state = hass.states.get(PANEL)
    assert state is not None
    return state


async def _arm(hass: HomeAssistant) -> None:
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    assert _panel(hass).state == AlarmControlPanelState.ARMED_NIGHT


async def test_own_pin_shows_user(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry({"users": {"p": user("Petra", "1357")}}))
    assert _panel(hass).attributes["code_format"] == "number"
    await _arm(hass)
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL, code="1357")
    state = _panel(hass)
    assert state.state == AlarmControlPanelState.DISARMED
    assert state.attributes["changed_by"] == "Petra"


async def test_shared_pin(hass: HomeAssistant) -> None:
    users = {"c": user("Christian", "2468"), "p": user("Petra", "2468")}
    await setup_entry(hass, make_entry({"users": users}))
    await _arm(hass)
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL, code="2468")
    assert _panel(hass).attributes["changed_by"] == "gemeinsamer PIN (Christian, Petra)"


async def test_rights_any_user(hass: HomeAssistant) -> None:
    users = {
        "n": user("Niklas", "1111", can_disarm=False),
        "c": user("Christian", "2222", can_disarm=False),
        "p": user("Petra", "2222"),
    }
    await setup_entry(hass, make_entry({"users": users}))
    await _arm(hass)
    with pytest.raises(ServiceValidationError):
        await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL, code="1111")
    assert _panel(hass).state == AlarmControlPanelState.ARMED_NIGHT
    # gemeinsamer PIN: Petra darf, also erlaubt
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL, code="2222")
    assert _panel(hass).state == AlarmControlPanelState.DISARMED


@pytest.mark.parametrize(
    "extra",
    [
        {"active": False},
        {"valid_until": "2000-01-01T00:00:00+00:00"},
        {"valid_from": "2999-01-01T00:00:00+00:00"},
    ],
)
async def test_blocked_or_expired_pin(hass: HomeAssistant, extra: dict) -> None:
    system = async_mock_service(hass, "notify", PHONE)
    options = {"users": {"g": user("Gast", "4444", **extra)}, "notify_system": [PHONE]}
    await setup_entry(hass, make_entry(options))
    await _arm(hass)
    with pytest.raises(ServiceValidationError):
        await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL, code="4444")
    assert _panel(hass).state == AlarmControlPanelState.ARMED_NIGHT
    assert any("Gast" in c.data["message"] for c in system)


async def test_duress_pin_disarms_and_alerts_silently(hass: HomeAssistant) -> None:
    alert = async_mock_service(hass, "notify", WATCH)
    options = {
        "users": {"p": user("Petra", "1357", duress="7531")},
        "duress_notify": [WATCH],
    }
    await setup_entry(hass, make_entry(options))
    await _arm(hass)
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL, code="7531")
    state = _panel(hass)
    assert state.state == AlarmControlPanelState.DISARMED
    assert state.attributes["changed_by"] == "Petra"  # unauffällig
    assert len(alert) == 1
    assert "Bedrohungs-PIN" in alert[0].data["message"]
    notifications = _async_get_or_create_notifications(hass)
    assert not any("BEDROHUNG" in str(n) for n in notifications.values())


async def test_duress_works_even_without_right(hass: HomeAssistant) -> None:
    async_mock_service(hass, "notify", WATCH)
    options = {
        "users": {"n": user("Niklas", "1111", duress="9999", can_disarm=False)},
        "duress_notify": [WATCH],
    }
    await setup_entry(hass, make_entry(options))
    await _arm(hass)
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL, code="9999")
    assert _panel(hass).state == AlarmControlPanelState.DISARMED


async def test_linked_user_rights_for_push(hass: HomeAssistant, hass_admin_user: MockUser) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    options = {
        "push_disarm": True,
        "profiles": {"night": {"notify": [PHONE]}},
        "users": {"n": user("Niklas", can_end_alarm=False, ha_user=hass_admin_user.id)},
    }
    await setup_entry(hass, make_entry(options))
    await _arm(hass)
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    action = push[0].data["data"]["actions"][0]["action"]
    hass.bus.async_fire(
        PUSH_ACTION_EVENT, {"action": action}, context=Context(user_id=hass_admin_user.id)
    )
    await hass.async_block_till_done()
    assert _panel(hass).state == AlarmControlPanelState.TRIGGERED
    assert any("Berechtigung" in c.data["message"] for c in push[1:])


async def test_user_management_in_options(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)

    async def flow_to_user_settings(step: str) -> dict:
        flow = await hass.config_entries.options.async_init(entry.entry_id)
        flow = await hass.config_entries.options.async_configure(
            flow["flow_id"], {"next_step_id": "users"}
        )
        return await hass.config_entries.options.async_configure(
            flow["flow_id"], {"next_step_id": step}
        )

    flow = await flow_to_user_settings("user_add")
    result = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"name": "Petra", "new_pin": "1357", "new_duress_pin": "7531"}
    )
    await hass.async_block_till_done()
    assert result["type"] == "create_entry"
    stored = entry.options["users"]["petra"]
    assert stored["name"] == "Petra"
    assert stored["pin_digest"]
    assert stored["duress_digest"]
    assert "1357" not in stored.values()  # nie im Klartext
    assert "new_pin" not in stored

    # Bedrohungs-PIN gleich einem normalen PIN: Fehler
    flow = await flow_to_user_settings("user_add")
    result = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"name": "Niklas", "new_pin": "2222", "new_duress_pin": "1357"}
    )
    assert result["errors"] == {"new_duress_pin": "duress_conflict"}

    # gleicher normaler PIN wie Petra: erlaubt
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"name": "Niklas", "new_pin": "1357"}
    )
    await hass.async_block_till_done()
    assert result["type"] == "create_entry"
    assert set(entry.options["users"]) == {"petra", "niklas"}


async def test_automation_shows_automatik(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    entry.runtime_data.arm("night", changed_by="Automatik")
    await hass.async_block_till_done()
    assert _panel(hass).attributes["changed_by"] == "Automatik"


async def test_name_suggests_ha_users_and_links(
    hass: HomeAssistant, hass_admin_user: MockUser
) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "users"}
    )
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "user_add"}
    )
    name_selector = flow["data_schema"].schema["name"]
    assert hass_admin_user.name in name_selector.config["options"]
    assert name_selector.config["custom_value"] is True
    result = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"name": hass_admin_user.name}
    )
    await hass.async_block_till_done()
    assert result["type"] == "create_entry"
    stored = next(iter(entry.options["users"].values()))
    assert stored["ha_user"] == hass_admin_user.id


async def _pin_rules(hass: HomeAssistant, entry: Any, data: dict) -> None:
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "code"}
    )
    result = await hass.config_entries.options.async_configure(flow["flow_id"], data)
    await hass.async_block_till_done()
    assert result["type"] == "create_entry"


async def test_master_pin(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    await _pin_rules(hass, entry, {"master_pin": "8642"})
    assert entry.options["users"]["master"]["name"] == "Master-PIN"
    assert _panel(hass).attributes["code_format"] == "number"
    await _arm(hass)
    with pytest.raises(ServiceValidationError):
        await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL)
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL, code="8642")
    assert _panel(hass).attributes["changed_by"] == "Master-PIN"
    # entfernen
    await _pin_rules(hass, entry, {"remove_master_pin": True})
    assert "master" not in entry.options["users"]
    assert _panel(hass).attributes.get("code_format") is None


async def test_buttons_allowed_despite_pin(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    await _pin_rules(hass, entry, {"master_pin": "8642", "buttons_without_pin": True})
    disarm_now = hass.states.get("button.hauswacht_disarm_now")
    assert disarm_now is not None
    assert disarm_now.state != "unavailable"
    await _arm(hass)
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    await _service(hass, "button", "press", entity_id="button.hauswacht_end_alarm")
    assert _panel(hass).state == AlarmControlPanelState.ARMED_NIGHT
    await _service(hass, "button", "press", entity_id="button.hauswacht_disarm_now")
    assert _panel(hass).state == AlarmControlPanelState.DISARMED
