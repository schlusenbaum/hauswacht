"""Integrationstests: Einrichtungsassistent bei der Erstinstallation und im Einstellungsdialog.

Alle Melder sind Testzustände; es wird nichts geschaltet.
"""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.hauswacht.const import DOMAIN

from .conftest import DEVICE_CLASSES, DOOR, MOTION, WINDOW, make_entry, setup_entry

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
    flow = await _cfg(hass, flow, {"next_step_id": "wizard_intro"})
    assert flow["step_id"] == "wizard_intro"
    flow = await _cfg(hass, flow, {})
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
    assert flow["step_id"] == "wizard_summary"
    summary = flow["description_placeholders"]["summary"]
    assert "Abwesend" in summary or "Away" in summary
    flow = await _cfg(hass, flow, {})
    assert flow["type"] is FlowResultType.CREATE_ENTRY
    options = flow["result"].options
    assert options["zones"]["aussen"]["entities"] == sorted([DOOR, WINDOW, TERRACE])
    assert options["sensor_types"] == {TERRACE: "other"}
    assert options["profiles"]["abwesend"]["exit_delay"] == 45
    assert options["profiles"]["abwesend"]["panel_mode"] == "away"
    assert options["profiles"]["nacht"]["exit_delay"] == 0
    assert options["profiles"]["nacht"]["zones"] == ["aussen"]
    assert "sirens_hardware_enabled" not in options


async def test_first_install_skip_everything(hass: HomeAssistant) -> None:
    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    flow = await _cfg(hass, flow, {"next_step_id": "wizard"})
    flow = await _cfg(hass, flow, {"next_step_id": "wizard_sensors"})
    flow = await _cfg(hass, flow, {"sensors": []})
    flow = await _cfg(hass, flow, {"next_step_id": "wizard_summary"})
    assert flow["step_id"] == "wizard_summary"
    assert "⚠️" in flow["description_placeholders"]["summary"]
    flow = await _cfg(hass, flow, {})
    assert flow["type"] is FlowResultType.CREATE_ENTRY
    assert flow["result"].options == {}


async def test_rules_only_at_first_install_points_to_later(hass: HomeAssistant) -> None:
    _sensors(hass)
    flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    flow = await _cfg(hass, flow, {"next_step_id": "wizard"})
    flow = await _cfg(hass, flow, {"next_step_id": "wizard_sensors"})
    flow = await _cfg(hass, flow, {"sensors": [DOOR]})
    flow = await _cfg(hass, flow, {"next_step_id": "wizard_mode_rules"})
    assert flow["step_id"] == "wizard_rules_later"
    flow = await _cfg(hass, flow, {})
    # keine Gruppen, keine Regeln -> keine Profile möglich, gleich zur Zusammenfassung
    assert flow["step_id"] == "wizard_summary"


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
    assert flow["step_id"] == "wizard_summary"
    profiles = entry.options["profiles"]
    assert "abwesend" not in profiles
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
