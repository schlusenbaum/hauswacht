"""Integrationstests: Regeln ("Tür, dann Keller") pro Alarmprofil.

Alle Sensoren sind Testzustände, notify-Dienste sind ATTRAPPEN, Sirenen nicht freigegeben.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.hauswacht.const import DOMAIN

from .conftest import DOOR, MOTION, PANEL, TAMPER, WINDOW, make_entry, set_sensor, setup_entry

MOTION2 = "binary_sensor.bwm_flur"
PHONE = "mobile_app_testhandy"

ZONES = {
    "tueren": {"name": "Türen", "entities": [DOOR], "label": None},
    "fenster": {"name": "Fenster", "entities": [WINDOW, TAMPER], "label": None},
    "keller": {"name": "Keller", "entities": [MOTION, MOTION2], "label": None},
}
RULES = {
    "tuer_keller": {
        "name": "Tür, dann Keller",
        "steps": [{"sensors": [DOOR], "within": 120}, {"zones": ["keller"]}],
        "result": "entry_delay",
    },
    "fenster_keller": {
        "name": "Fenster, dann Keller",
        "steps": [{"zones": ["fenster"], "within": 60}, {"zones": ["keller"]}],
        "result": "alarm",
    },
}


def _options(**extra: Any) -> dict[str, Any]:
    night = {"zones": [], "rules": ["tuer_keller", "fenster_keller"], "entry_delay": 30}
    night["notify"] = [PHONE]
    return {"zones": ZONES, "rules": RULES, "profiles": {"night": night}, **extra}


async def _service(hass: HomeAssistant, domain: str, service: str, **data: Any) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)
    await hass.async_block_till_done()


def _panel(hass: HomeAssistant) -> str:
    state = hass.states.get(PANEL)
    assert state is not None
    return state.state


def _motion2(hass: HomeAssistant, state: str) -> None:
    hass.states.async_set(MOTION2, state, {"device_class": "motion"})


async def _set(hass: HomeAssistant, entity_id: str, state: str) -> None:
    if entity_id == MOTION2:
        _motion2(hass, state)
    else:
        set_sensor(hass, entity_id, state)
    await hass.async_block_till_done()


async def _setup(hass: HomeAssistant, **extra: Any) -> list[Any]:
    push = async_mock_service(hass, "notify", PHONE)
    _motion2(hass, "off")
    await setup_entry(hass, make_entry(_options(**extra)))
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    return push


async def _wait(hass: HomeAssistant, freezer: FrozenDateTimeFactory, seconds: int) -> None:
    freezer.tick(timedelta(seconds=seconds))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


async def test_door_alone_and_cellar_alone_do_not_trigger(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    await _setup(hass)
    await _set(hass, DOOR, "on")
    await _wait(hass, freezer, 130)  # Niklas geht nach oben
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    await _set(hass, MOTION, "on")  # später in den Keller: zwei Melder reagieren
    await _set(hass, MOTION2, "on")
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_door_then_cellar_starts_entry_delay(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    await _setup(hass)
    await _set(hass, DOOR, "on")
    await _wait(hass, freezer, 40)
    await _set(hass, MOTION, "on")
    assert _panel(hass) == AlarmControlPanelState.PENDING


async def test_window_then_cellar_alarm_with_rule_name(hass: HomeAssistant) -> None:
    push = await _setup(hass)
    await _set(hass, WINDOW, "on")
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT  # lüften: kein Alarm
    await _set(hass, MOTION2, "on")
    assert _panel(hass) == AlarmControlPanelState.TRIGGERED
    assert any("Auslöseregel: Fenster, dann Keller" in c.data["message"] for c in push)


async def test_order_matters(hass: HomeAssistant) -> None:
    await _setup(hass)
    await _set(hass, MOTION, "on")  # jemand drinnen …
    await _set(hass, WINDOW, "on")  # … öffnet das Fenster
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_open_rule_sensor_does_not_block_arming(hass: HomeAssistant) -> None:
    _motion2(hass, "off")
    await setup_entry(hass, make_entry(_options()))
    await _set(hass, WINDOW, "on")
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_disarm_forgets_started_rules(hass: HomeAssistant) -> None:
    await _setup(hass)
    await _set(hass, WINDOW, "on")
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL)
    await _set(hass, WINDOW, "off")
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    await _set(hass, MOTION, "on")
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_unconfirmed_notification_when_enabled(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    events = {"unconfirmed": {"enabled": True, "targets": []}}
    push = await _setup(hass, notify_system=[PHONE], events=events)
    await _set(hass, DOOR, "on")
    await _wait(hass, freezer, 125)
    titles = [c.data["title"] for c in push]
    assert "Hauswacht: unbestätigte Auslösung" in titles
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_unconfirmed_off_by_default(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    push = await _setup(hass, notify_system=[PHONE])
    await _set(hass, DOOR, "on")
    await _wait(hass, freezer, 125)
    assert push == []


async def test_test_card_shows_rule_progress(hass: HomeAssistant) -> None:
    await _setup(hass)
    await _set(hass, DOOR, "on")
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    entity_id = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{entry.entry_id}_simulation"
    )
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state is not None
    rules = {r["name"]: r for r in state.attributes["rules"]}
    assert rules["Tür, dann Keller"]["done"] == 1
    assert rules["Tür, dann Keller"]["deadline"]
    assert rules["Fenster, dann Keller"]["done"] == 0
    rows = {r["entity_id"]: r for r in state.attributes["sensors"]}
    assert rows[MOTION]["status"] == "in_rule"
    assert set(rows[MOTION]["rules"]) == {"Tür, dann Keller", "Fenster, dann Keller"}


async def test_migration_turns_zone_confirmation_into_rule(hass: HomeAssistant) -> None:
    options = {
        "zones": {**ZONES, "keller": {**ZONES["keller"], "confirm": True, "confirm_window": 90}},
        "profiles": {
            "night": {"name": "Nacht", "panel_mode": "night", "exit_delay": 0, "zones": ["keller"]}
        },
    }
    entry = MockConfigEntry(domain=DOMAIN, title="Hauswacht", data={}, options=options, version=3)
    _motion2(hass, "off")
    await setup_entry(hass, entry)
    assert entry.version == 4
    assert entry.options["profiles"]["night"]["zones"] == []
    assert entry.options["profiles"]["night"]["rules"] == ["bestaetigung_keller"]
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    await _set(hass, MOTION, "on")
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    await _set(hass, MOTION2, "on")
    assert _panel(hass) == AlarmControlPanelState.TRIGGERED


async def _flow(hass: HomeAssistant, entry: MockConfigEntry, *steps: str) -> dict[str, Any]:
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    for step in steps:
        flow = await hass.config_entries.options.async_configure(
            flow["flow_id"], {"next_step_id": step}
        )
    return flow  # type: ignore[no-any-return]


async def _go(hass: HomeAssistant, flow: dict[str, Any], step: str) -> dict[str, Any]:
    return await hass.config_entries.options.async_configure(  # type: ignore[no-any-return]
        flow["flow_id"], {"next_step_id": step}
    )


async def _submit(
    hass: HomeAssistant, flow: dict[str, Any], data: dict[str, Any]
) -> dict[str, Any]:
    return await hass.config_entries.options.async_configure(  # type: ignore[no-any-return]
        flow["flow_id"], data
    )


async def test_rule_wizard(hass: HomeAssistant) -> None:
    _motion2(hass, "off")
    entry = make_entry({"zones": ZONES})
    await setup_entry(hass, entry)
    flow = await _flow(hass, entry, "triggering", "rules", "rule_add")
    assert flow["step_id"] == "rule_meta"
    flow = await _submit(hass, flow, {"name": "Tür, dann Keller", "result": "entry_delay"})
    assert flow["step_id"] == "rule_step"
    assert flow["description_placeholders"]["step"] == "1"
    flow = await _submit(hass, flow, {})  # leerer Schritt
    assert flow["errors"] == {"base": "step_empty"}
    flow = await _submit(hass, flow, {"sensors": [DOOR, MOTION], "within": 60})
    assert flow["step_id"] == "rule_overview"
    flow = await _go(hass, flow, "rule_step_add")
    assert flow["description_placeholders"]["step"] == "2"
    flow = await _submit(hass, flow, {"sensors": [MOTION]})
    # MOTION steht in Schritt 1 und 2: nicht speicherbar, Grund in der Übersicht
    assert flow["description_placeholders"]["problems"]
    flow = await _go(hass, flow, "rule_save")
    assert flow["step_id"] == "rule_overview"
    assert not entry.options.get("rules")
    # Schritt 1 korrigieren
    flow = await _go(hass, flow, "rule_step_edit")
    flow = await _submit(hass, flow, {"step": "1"})
    assert flow["step_id"] == "rule_step"
    flow = await _submit(hass, flow, {"sensors": [DOOR], "within": 120})
    assert flow["description_placeholders"]["problems"] == ""
    assert "→" in flow["description_placeholders"]["rule_text"]
    flow = await _go(hass, flow, "rule_save")
    assert flow["step_id"] == "rules"
    rule = next(iter(entry.options["rules"].values()))
    assert rule["name"] == "Tür, dann Keller"
    assert rule["result"] == "entry_delay"
    assert rule["steps"] == [
        {"any": [{"sensor": DOOR}], "within": 120},
        {"any": [{"sensor": MOTION}], "within": 60},
    ]
    assert "Tür, dann Keller" in flow["description_placeholders"]["rules"]


async def test_rule_wizard_edit_and_cancel(hass: HomeAssistant) -> None:
    _motion2(hass, "off")
    entry = make_entry({"zones": ZONES, "rules": RULES})
    await setup_entry(hass, entry)
    flow = await _flow(hass, entry, "triggering", "rules", "rule_edit")
    flow = await _submit(hass, flow, {"rule": "tuer_keller"})
    assert flow["step_id"] == "rule_overview"
    flow = await _go(hass, flow, "rule_step_remove")
    flow = await _go(hass, flow, "rule_cancel")
    assert flow["step_id"] == "rules"
    assert len(entry.options["rules"]["tuer_keller"]["steps"]) == 2  # nichts gespeichert


async def test_profile_rule_hint_when_redundant(hass: HomeAssistant) -> None:
    _motion2(hass, "off")
    entry = make_entry({"zones": ZONES, "rules": RULES})
    await setup_entry(hass, entry)
    flow = await _flow(hass, entry, "profiles", "profile_edit")
    flow = await hass.config_entries.options.async_configure(flow["flow_id"], {"profile": "night"})
    data = {
        "name": "Nacht",
        "icon": "mdi:weather-night",
        "panel_mode": "night",
        "zones": ["tueren"],
        "rules": ["tuer_keller"],
    }
    flow = await hass.config_entries.options.async_configure(flow["flow_id"], data)
    assert flow["type"] is FlowResultType.MENU
    assert entry.options["profiles"]["night"]["rules"] == ["tuer_keller"]
    assert "Tür, dann Keller" in flow["description_placeholders"]["saved"]


async def test_hint_for_open_rule_sensor_when_armed(hass: HomeAssistant) -> None:
    from homeassistant.components.persistent_notification import (  # noqa: PLC0415
        _async_get_or_create_notifications,
    )

    push = async_mock_service(hass, "notify", PHONE)
    _motion2(hass, "off")
    await setup_entry(hass, make_entry(_options(notify_system=[PHONE])))
    await _set(hass, WINDOW, "on")
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    hints = [c for c in push if c.data["title"] == "Hauswacht: Hinweis beim Scharfschalten"]
    assert len(hints) == 1
    assert "Fenster, dann Keller" in hints[0].data["message"]
    state = hass.states.get(PANEL)
    assert state is not None
    assert state.attributes["open_rule_sensors"] == [WINDOW]
    assert "hauswacht_arm_hint" in _async_get_or_create_notifications(hass)

    # Nachträglich geschlossen: Öffnen beginnt die Regel wieder
    await _set(hass, WINDOW, "off")
    assert hass.states.get(PANEL).attributes["open_rule_sensors"] == []  # type: ignore[union-attr]
    await _set(hass, WINDOW, "on")
    await _set(hass, MOTION, "on")
    assert _panel(hass) == AlarmControlPanelState.TRIGGERED

    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL)
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL)
    assert "hauswacht_arm_hint" not in _async_get_or_create_notifications(hass)


async def test_no_hint_when_rule_sensors_closed(hass: HomeAssistant) -> None:
    push = await _setup(hass, notify_system=[PHONE])
    assert not [c for c in push if "Hinweis" in c.data["title"]]


YAML_RULE = {
    "name": "Fenster, dann drinnen",
    "result": "alarm",
    "steps": [
        {"any": [{"group": "Fenster"}], "within": 60},
        {
            "any": [
                {"group": "Keller"},
                {"all": [{"sensor": DOOR}, {"sensor": "binary_sensor.buero"}]},
            ]
        },
    ],
    "unless": {"any": [{"sensor": MOTION2}], "before": 300},
    "conditions": [{"state": {"entity": "input_boolean.scharf_erlaubt", "is": "on"}}],
}


async def test_rule_yaml_add_validates_and_saves(hass: HomeAssistant) -> None:
    _motion2(hass, "off")
    entry = make_entry({"zones": ZONES})
    await setup_entry(hass, entry)
    flow = await _flow(hass, entry, "triggering", "rules", "rule_yaml_add")
    assert flow["step_id"] == "rule_yaml"
    bad = {**YAML_RULE, "steps": [{"any": [{"group": "Fensterr"}]}]}
    flow = await _submit(hass, flow, {"rule": bad})
    assert flow["errors"] == {"base": "rule_yaml_invalid"}
    assert "Fensterr" in flow["description_placeholders"]["problem"]
    flow = await _submit(hass, flow, {"rule": YAML_RULE})
    assert flow["step_id"] == "rules"
    stored = entry.options["rules"]["fenster_dann_drinnen"]
    assert stored["steps"][0] == {"any": [{"group": "fenster"}], "within": 60}
    assert stored["unless"]["before"] == 300
    assert stored["conditions"] == YAML_RULE["conditions"]
    # verschachtelte Regel: Bearbeiten öffnet direkt den YAML-Editor
    flow = await _flow(hass, entry, "triggering", "rules", "rule_edit")
    flow = await _submit(hass, flow, {"rule": "fenster_dann_drinnen"})
    assert flow["step_id"] == "rule_yaml"


def _yaml_options(rule: dict[str, Any], **extra: Any) -> dict[str, Any]:
    night = {"zones": [], "rules": ["r"], "entry_delay": 30, "notify": [PHONE]}
    return {"zones": ZONES, "rules": {"r": rule}, "profiles": {"night": night}, **extra}


async def _arm_with(hass: HomeAssistant, rule: dict[str, Any], **extra: Any) -> list[Any]:
    push = async_mock_service(hass, "notify", PHONE)
    _motion2(hass, "off")
    await setup_entry(hass, make_entry(_yaml_options(rule, **extra)))
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    return push


STORED = {
    "name": "Fenster, dann Keller",
    "result": "alarm",
    "steps": [
        {"any": [{"group": "fenster"}], "within": 60},
        {"any": [{"group": "keller"}]},
    ],
}


async def test_condition_not_met_no_alarm(hass: HomeAssistant) -> None:
    hass.states.async_set("input_boolean.urlaub", "off")
    rule = {**STORED, "conditions": [{"state": {"entity": "input_boolean.urlaub", "is": "on"}}]}
    await _arm_with(hass, rule)
    await _set(hass, WINDOW, "on")
    await _set(hass, MOTION, "on")
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    hass.states.async_set("input_boolean.urlaub", "on")
    await _set(hass, WINDOW, "off")
    await _set(hass, MOTION, "off")
    await _set(hass, WINDOW, "on")
    await _set(hass, MOTION, "on")
    assert _panel(hass) == AlarmControlPanelState.TRIGGERED


async def test_unknown_condition_counts_as_met(hass: HomeAssistant) -> None:
    rule = {**STORED, "conditions": [{"not": {"state": {"entity": "switch.fehlt", "is": "on"}}}]}
    await _arm_with(hass, rule)
    await _set(hass, WINDOW, "on")
    await _set(hass, MOTION, "on")
    assert _panel(hass) == AlarmControlPanelState.TRIGGERED


async def test_unless_blocks_rule(hass: HomeAssistant) -> None:
    rule = {**STORED, "unless": {"any": [{"sensor": MOTION2}], "before": 300}}
    await _arm_with(hass, rule)
    await _set(hass, MOTION2, "on")  # jemand drinnen
    await _set(hass, WINDOW, "on")
    await _set(hass, MOTION, "on")
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_notify_result_only_notifies(hass: HomeAssistant) -> None:
    push = await _arm_with(hass, {**STORED, "result": "notify"}, notify_system=[PHONE])
    await _set(hass, WINDOW, "on")
    await _set(hass, MOTION, "on")
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    assert any(c.data["title"] == "Hauswacht: Auslöseregel erfüllt" for c in push)


async def test_wizard_unless(hass: HomeAssistant) -> None:
    _motion2(hass, "off")
    entry = make_entry({"zones": ZONES, "rules": RULES})
    await setup_entry(hass, entry)
    flow = await _flow(hass, entry, "triggering", "rules", "rule_edit")
    flow = await _submit(hass, flow, {"rule": "fenster_keller"})
    flow = await _go(hass, flow, "rule_unless")
    assert flow["step_id"] == "rule_unless"
    flow = await _submit(hass, flow, {"sensors": [MOTION2], "before": 120})
    assert "120 s" in flow["description_placeholders"]["rule_text"]
    flow = await _go(hass, flow, "rule_save")
    stored = entry.options["rules"]["fenster_keller"]
    assert stored["unless"] == {"any": [{"sensor": MOTION2}], "before": 120}
