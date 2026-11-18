"""Integrationstests: Einrichtungsassistent bei der Erstinstallation und im Einstellungsdialog.

Alle Melder sind Testzustände; es wird nichts geschaltet.
"""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.hauswacht.const import DOMAIN

from .conftest import DEVICE_CLASSES, DOOR, MOTION, WINDOW, make_entry, setup_entry

PHONE = "mobile_app_annas_handy"
SIREN = "siren.flur"

TERRACE = "binary_sensor.terrassentuer"
SMOKE = "binary_sensor.rauchmelder_flur"


def _sensors(hass: HomeAssistant) -> None:
    for entity_id in (DOOR, WINDOW, MOTION):
        hass.states.async_set(entity_id, "off", {"device_class": DEVICE_CLASSES[entity_id]})
    hass.states.async_set(TERRACE, "off", {"device_class": "door"})
    hass.states.async_set(SMOKE, "off", {"device_class": "smoke"})


async def _cfg(hass: HomeAssistant, flow: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    return await hass.config_entries.flow.async_configure(  # type: ignore[no-any-return]
        flow["flow_id"], data
    )


async def _opt(hass: HomeAssistant, flow: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    return await hass.config_entries.options.async_configure(  # type: ignore[no-any-return]
        flow["flow_id"], data
    )


async def _skip_part2(hass: HomeAssistant, flow: dict[str, Any], configure: Any) -> dict[str, Any]:
    """Empfänger, Sirenen, Benutzer, Bedienteile überspringen."""
    assert flow["step_id"] == "wizard_recipients"
    flow = await configure(hass, flow, {"recipients": []})
    assert flow["step_id"] == "wizard_sirens"
    flow = await configure(hass, flow, {"sirens": []})
    assert flow["step_id"] == "wizard_users"
    flow = await configure(hass, flow, {})
    assert flow["step_id"] == "wizard_controls"
    flow = await configure(hass, flow, {})
    if flow["step_id"] == "wizard_trial_ask":  # Einstellungsdialog: Probelauf angeboten
        flow = await configure(hass, flow, {"next_step_id": "wizard_summary"})
    return flow  # type: ignore[no-any-return]


def _default(flow: dict[str, Any], key: str) -> Any:
    for marker in flow["data_schema"].schema:
        if str(marker) == key:
            return marker.default()
    raise KeyError(key)


async def test_first_install_with_wizard(hass: HomeAssistant) -> None:
    _sensors(hass)
    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    flow = await _cfg(hass, flow, {"next_step_id": "wizard"})
    assert flow["step_id"] == "wizard"
    assert flow["menu_options"] == ["wizard_intro", "wizard_area_question"]
    flow = await _cfg(hass, flow, {"next_step_id": "wizard_intro"})
    assert flow["step_id"] == "wizard_intro"
    flow = await _cfg(hass, flow, {})
    assert flow["step_id"] == "wizard_area_question"
    flow = await _cfg(hass, flow, {"next_step_id": "wizard_sensors"})
    assert flow["step_id"] == "wizard_sensors"
    # Vorschlag: Türen, Fenster, Bewegung – kein Rauchmelder
    suggested = _default(flow, "sensors")
    assert set(suggested) == {DOOR, WINDOW, MOTION, TERRACE}
    flow = await _cfg(hass, flow, {"sensors": suggested})
    assert flow["type"] is FlowResultType.MENU
    assert flow["step_id"] == "wizard_mode"
    flow = await _cfg(hass, flow, {"next_step_id": "wizard_mode_zones"})
    assert flow["step_id"] == "wizard_groups"
    assert set(_default(flow, "outside")) == {DOOR, WINDOW, TERRACE}
    assert _default(flow, "inside") == [MOTION]
    assert set(_default(flow, "entry_doors")) == {DOOR, TERRACE}
    flow = await _cfg(
        hass,
        flow,
        {
            "outside_name": "Außen",
            "outside": [DOOR, WINDOW, TERRACE],
            "entry_doors": [DOOR],
            "inside_name": "Innen",
            "inside": [MOTION],
        },
    )
    assert flow["step_id"] == "wizard_profiles"
    assert _default(flow, "night_zones") == ["aussen"]
    flow = await _cfg(
        hass,
        flow,
        {
            "away": True,
            "away_zones": ["aussen", "innen"],
            "exit_delay": 45,
            "entry_delay": 20,
            "night": True,
            "night_zones": ["aussen"],
        },
    )
    flow = await _skip_part2(hass, flow, _cfg)
    assert flow["step_id"] == "wizard_summary"
    summary = flow["description_placeholders"]["summary"]
    assert "Away" in summary
    flow = await _cfg(hass, flow, {})
    assert flow["type"] is FlowResultType.CREATE_ENTRY
    options = flow["result"].options
    by_mode = {p["panel_mode"]: p for p in options["profiles"].values()}
    assert options["zones"]["aussen"]["entities"] == sorted([DOOR, WINDOW, TERRACE])
    assert options["sensor_types"] == {TERRACE: "other"}
    assert by_mode["away"]["exit_delay"] == 45
    assert by_mode["away"]["name"] == "Away"  # Sprache von Home Assistant (Tests: Englisch)
    assert by_mode["night"]["exit_delay"] == 0
    assert by_mode["night"]["zones"] == ["aussen"]
    assert "sirens_hardware_enabled" not in options


async def test_first_install_skip_everything(hass: HomeAssistant) -> None:
    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    flow = await _cfg(hass, flow, {"next_step_id": "wizard"})
    flow = await _cfg(hass, flow, {"next_step_id": "wizard_area_question"})
    flow = await _cfg(hass, flow, {"next_step_id": "wizard_sensors"})
    flow = await _cfg(hass, flow, {"sensors": []})
    flow = await _cfg(hass, flow, {"next_step_id": "wizard_recipients"})
    flow = await _skip_part2(hass, flow, _cfg)
    assert flow["step_id"] == "wizard_summary"
    assert "⚠️" in flow["description_placeholders"]["summary"]
    flow = await _cfg(hass, flow, {})
    assert flow["type"] is FlowResultType.CREATE_ENTRY
    assert flow["result"].options == {}


async def test_rules_only_at_first_install_points_to_later(hass: HomeAssistant) -> None:
    _sensors(hass)
    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    flow = await _cfg(hass, flow, {"next_step_id": "wizard"})
    flow = await _cfg(hass, flow, {"next_step_id": "wizard_area_question"})
    flow = await _cfg(hass, flow, {"next_step_id": "wizard_sensors"})
    flow = await _cfg(hass, flow, {"sensors": [DOOR]})
    flow = await _cfg(hass, flow, {"next_step_id": "wizard_mode_rules"})
    assert flow["step_id"] == "wizard_rules_later"
    flow = await _cfg(hass, flow, {})
    # keine Gruppen, keine Regeln -> keine Profile möglich, weiter mit den Empfängern
    assert flow["step_id"] == "wizard_recipients"


async def test_wizard_in_settings_adds_and_returns_from_rule_wizard(
    hass: HomeAssistant,
) -> None:
    _sensors(hass)
    entry = make_entry()
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    assert flow["menu_options"][0] == "wizard"
    flow = await _opt(hass, flow, {"next_step_id": "wizard"})
    flow = await _opt(hass, flow, {"next_step_id": "wizard_sensors"})
    # schon gruppierte Melder werden nicht noch einmal vorgeschlagen
    assert _default(flow, "sensors") == [TERRACE]
    flow = await _opt(hass, flow, {"sensors": [TERRACE]})
    flow = await _opt(hass, flow, {"next_step_id": "wizard_mode_both"})
    flow = await _opt(
        hass,
        flow,
        {"outside_name": "Terrasse", "outside": [TERRACE], "entry_doors": [], "inside": []},
    )
    assert flow["step_id"] == "wizard_rules"
    assert entry.options["zones"]["terrasse"]["entities"] == [TERRACE]  # sofort gespeichert
    # Regel-Assistent und zurück
    flow = await _opt(hass, flow, {"next_step_id": "rule_add"})
    assert flow["step_id"] == "rule_meta"
    flow = await _opt(hass, flow, {"name": "Terrasse, dann Keller", "result": "alarm"})
    flow = await _opt(hass, flow, {"sensors": [TERRACE], "within": 60})
    flow = await _opt(hass, flow, {"next_step_id": "rule_step_add"})
    flow = await _opt(hass, flow, {"sensors": [MOTION]})
    flow = await _opt(hass, flow, {"next_step_id": "rule_save"})
    assert flow["step_id"] == "wizard_rules"
    assert "Terrasse, dann Keller" in flow["description_placeholders"]["rules"]
    flow = await _opt(hass, flow, {"next_step_id": "wizard_profiles"})
    assert flow["step_id"] == "wizard_profiles"
    # vorhandene Profile mit denselben Knöpfen werden ergänzt, nicht verdoppelt
    flow = await _opt(
        hass,
        flow,
        {
            "away": True,
            "away_zones": ["aussen", "keller", "terrasse"],
            "away_rules": ["terrasse_dann_keller"],
            "exit_delay": 60,
            "entry_delay": 30,
            "night": False,
        },
    )
    flow = await _skip_part2(hass, flow, _opt)
    assert flow["step_id"] == "wizard_summary"
    profiles = entry.options["profiles"]
    assert len(profiles) == 5  # nichts verdoppelt
    assert profiles["away"]["zones"] == ["aussen", "keller", "terrasse"]
    assert profiles["away"]["rules"] == ["terrasse_dann_keller"]
    assert profiles["night"]["zones"] == ["aussen", "keller"]  # abgewählt = unverändert
    flow = await _opt(hass, flow, {})
    assert flow["step_id"] == "init"


async def test_profile_needs_group_or_rule(hass: HomeAssistant) -> None:
    _sensors(hass)
    entry = make_entry()
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    flow = await _opt(hass, flow, {"next_step_id": "wizard"})
    flow = await _opt(hass, flow, {"next_step_id": "wizard_sensors"})
    flow = await _opt(hass, flow, {"sensors": []})
    flow = await _opt(hass, flow, {"next_step_id": "wizard_mode_zones"})
    flow = await _opt(hass, flow, {"outside": [], "inside": []})
    assert flow["step_id"] == "wizard_profiles"
    flow = await _opt(
        hass, flow, {"away": True, "away_zones": [], "night": False, "night_zones": []}
    )
    assert flow["errors"] == {"away_zones": "wizard_profile_empty"}


async def test_zone_overlap_is_shown(hass: HomeAssistant) -> None:
    _sensors(hass)
    entry = make_entry()
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    flow = await _opt(hass, flow, {"next_step_id": "wizard"})
    flow = await _opt(hass, flow, {"next_step_id": "wizard_sensors"})
    flow = await _opt(hass, flow, {"sensors": [DOOR]})
    flow = await _opt(hass, flow, {"next_step_id": "wizard_mode_zones"})
    flow = await _opt(hass, flow, {"outside_name": "Tür", "outside": [DOOR], "inside": []})
    assert flow["errors"] == {"base": "zone_overlap"}
    assert "Außen" in flow["description_placeholders"]["conflicts"]


async def _to_recipients(hass: HomeAssistant) -> tuple[Any, dict[str, Any]]:
    _sensors(hass)
    entry = make_entry()
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    flow = await _opt(hass, flow, {"next_step_id": "wizard"})
    flow = await _opt(hass, flow, {"next_step_id": "wizard_sensors"})
    flow = await _opt(hass, flow, {"sensors": []})
    flow = await _opt(hass, flow, {"next_step_id": "wizard_recipients"})
    assert flow["step_id"] == "wizard_recipients"
    return entry, flow


async def test_recipients_and_test_message_only_on_request(hass: HomeAssistant) -> None:
    pushes = async_mock_service(hass, "notify", PHONE)
    entry, flow = await _to_recipients(hass)
    assert _default(flow, "recipients") == [PHONE]  # Handy-App vorgewählt
    flow = await _opt(hass, flow, {"recipients": [PHONE]})
    assert flow["step_id"] == "wizard_recipients_test"
    assert entry.options["notify_system"] == [PHONE]
    assert pushes == []  # nichts ohne Knopfdruck
    flow = await _opt(hass, flow, {"next_step_id": "wizard_send_test"})
    assert flow["step_id"] == "wizard_recipients_test"
    assert len(pushes) == 1
    assert PHONE in flow["description_placeholders"]["result"]
    flow = await _opt(hass, flow, {"next_step_id": "wizard_sirens"})
    assert flow["step_id"] == "wizard_sirens"


async def test_sirens_are_added_but_never_released(hass: HomeAssistant) -> None:
    hass.states.async_set(SIREN, "off")
    turn_on = async_mock_service(hass, "siren", "turn_on")
    entry, flow = await _to_recipients(hass)
    flow = await _opt(hass, flow, {"recipients": []})
    assert _default(flow, "sirens") == [SIREN]
    flow = await _opt(hass, flow, {"sirens": [SIREN], "profiles": ["away", "night"]})
    # im Einstellungsdialog: Sirenentest anbieten (nur auf Knopfdruck)
    assert flow["step_id"] == "wizard_sirens_test"
    assert flow["menu_options"] == ["siren_test", "wizard_users"]
    assert entry.options["sirens"] == [SIREN]
    assert entry.options.get("sirens_hardware_enabled", False) is False
    assert SIREN in entry.options["profiles"]["away"]["sirens"]
    assert SIREN in entry.options["profiles"]["night"]["sirens"]
    assert "sirens" not in entry.options["profiles"]["home"]
    assert turn_on == []
    flow = await _opt(hass, flow, {"next_step_id": "wizard_users"})
    assert flow["step_id"] == "wizard_users"


async def test_users_with_pin(hass: HomeAssistant) -> None:
    entry, flow = await _to_recipients(hass)
    flow = await _opt(hass, flow, {"recipients": []})
    flow = await _opt(hass, flow, {"sirens": []})
    flow = await _opt(hass, flow, {"name": "Anna", "pin": "12"})
    assert flow["errors"] == {"pin": "invalid_pin"}
    assert not entry.options.get("users")
    flow = await _opt(hass, flow, {"name": "Anna", "pin": "2468"})
    assert flow["step_id"] == "wizard_users_more"
    assert "Anna" in flow["description_placeholders"]["users"]
    stored = next(iter(entry.options["users"].values()))
    assert stored["name"] == "Anna"
    assert "pin_digest" in stored
    assert "2468" not in str(entry.options)
    flow = await _opt(hass, flow, {"next_step_id": "wizard_users"})
    flow = await _opt(hass, flow, {"name": "anna"})
    assert flow["errors"] == {"name": "user_name_taken"}
    flow = await _opt(hass, flow, {})
    assert flow["step_id"] == "wizard_controls"
    flow = await _opt(hass, flow, {})
    # Einstellungsdialog: Probelauf angeboten, Testmodus ist aus -> erst darum bitten
    assert flow["step_id"] == "wizard_trial_ask"
    flow = await _opt(hass, flow, {"next_step_id": "wizard_summary"})
    assert flow["step_id"] == "wizard_summary"


async def test_area_question_at_first_install(hass: HomeAssistant) -> None:
    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    flow = await _cfg(hass, flow, {"next_step_id": "wizard"})
    flow = await _cfg(hass, flow, {"next_step_id": "wizard_area_question"})
    assert flow["menu_options"] == ["wizard_sensors", "wizard_area_hint"]
    flow = await _cfg(hass, flow, {"next_step_id": "wizard_area_hint"})
    assert flow["step_id"] == "wizard_area_hint"
    flow = await _cfg(hass, flow, {})
    assert flow["step_id"] == "wizard_sensors"


async def test_restart_offers_chapters_and_new_area(hass: HomeAssistant) -> None:
    _sensors(hass)
    entry = make_entry()
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    flow = await _opt(hass, flow, {"next_step_id": "wizard"})
    assert flow["step_id"] == "wizard_chapters"
    assert "wizard_trial" in flow["menu_options"]
    flow = await _opt(hass, flow, {"next_step_id": "wizard_new_area"})
    flow = await _opt(hass, flow, {"name": "Einliegerwohnung"})
    assert flow["step_id"] == "wizard_sensors"
    assert entry.options["areas"]["einliegerwohnung"]["name"] == "Einliegerwohnung"
    flow = await _opt(hass, flow, {"sensors": [TERRACE]})
    flow = await _opt(hass, flow, {"next_step_id": "wizard_mode_zones"})
    flow = await _opt(
        hass,
        flow,
        {"outside_name": "Wohnung", "outside": [TERRACE], "entry_doors": [TERRACE], "inside": []},
    )
    flow = await _opt(
        hass,
        flow,
        {
            "away": True,
            "away_zones": ["wohnung"],
            "exit_delay": 30,
            "entry_delay": 30,
            "night": False,
        },
    )
    assert flow["step_id"] == "wizard_recipients"
    new = [p for p in entry.options["profiles"].values() if p.get("area") == "einliegerwohnung"]
    assert len(new) == 1
    assert new[0]["panel_mode"] == "away"
    assert new[0]["zones"] == ["wohnung"]
    assert "Einliegerwohnung" in new[0]["name"]
    # Hauptbereich unverändert
    assert entry.options["profiles"]["away"]["zones"] == ["aussen", "keller"]
    # Name doppelt
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    flow = await _opt(hass, flow, {"next_step_id": "wizard"})
    flow = await _opt(hass, flow, {"next_step_id": "wizard_new_area"})
    flow = await _opt(hass, flow, {"name": "einliegerwohnung"})
    assert flow["errors"] == {"name": "area_name_taken"}


async def test_trial_run_asks_for_test_mode_and_ticks_sensors(hass: HomeAssistant) -> None:
    _sensors(hass)
    entry = make_entry()
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    flow = await _opt(hass, flow, {"next_step_id": "wizard"})
    flow = await _opt(hass, flow, {"next_step_id": "wizard_trial"})
    # Testmodus aus: bitten, nicht selbst einschalten
    assert flow["step_id"] == "wizard_trial_ask"
    test_mode = "switch.hauswacht_test_mode"
    state = hass.states.get(test_mode)
    assert state is not None
    assert state.state == "off"
    await hass.services.async_call("switch", "turn_on", {"entity_id": test_mode}, blocking=True)
    flow = await _opt(hass, flow, {"next_step_id": "wizard_trial"})
    assert flow["step_id"] == "wizard_trial_run"
    assert flow["description_placeholders"]["seen"] == "0"
    total = int(flow["description_placeholders"]["total"])
    assert total >= 3
    hass.states.async_set(DOOR, "on", {"device_class": "door"})
    await hass.async_block_till_done()
    flow = await _opt(hass, flow, {"next_step_id": "wizard_trial"})
    assert flow["description_placeholders"]["seen"] == "1"
    assert "✅" in flow["description_placeholders"]["sensors"]
    flow = await _opt(hass, flow, {"next_step_id": "wizard_summary"})
    assert flow["step_id"] == "wizard_summary"


async def test_wizard_sets_schedule_and_keeps_other_automation(hass: HomeAssistant) -> None:
    _sensors(hass)
    hass.states.async_set("schedule.nacht", "off")
    entry = make_entry({"profiles": {"night": {"auto_away_persons": ["person.anna"]}}})
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    flow = await _opt(hass, flow, {"next_step_id": "wizard"})
    flow = await _opt(hass, flow, {"next_step_id": "wizard_profiles"})
    assert flow["step_id"] == "wizard_profiles"
    flow = await _opt(
        hass,
        flow,
        {
            "away": False,
            "night": True,
            "night_zones": ["aussen"],
            "night_schedule": "schedule.nacht",
        },
    )
    assert flow["step_id"] == "wizard_recipients"
    night = entry.options["profiles"]["night"]
    assert night["auto_schedule"] == "schedule.nacht"
    assert night["auto_away_persons"] == ["person.anna"]  # übrige Automatik bleibt
    # erneut: Feld ist vorbelegt
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    flow = await _opt(hass, flow, {"next_step_id": "wizard"})
    flow = await _opt(hass, flow, {"next_step_id": "wizard_profiles"})
    marker = next(m for m in flow["data_schema"].schema if str(m) == "night_schedule")
    assert marker.description == {"suggested_value": "schedule.nacht"}
