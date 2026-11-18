"""Integrationstests: Websocket-Befehle der Einstellungsseite (ADR 0011 Stufe 2).

Nur Einstellungen werden geändert; es werden keine Sirenen oder Geräte angesprochen.
"""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from .conftest import DOOR, MOTION, PANEL, WINDOW, make_entry, setup_entry


async def _ws(hass_ws_client: Any, hass: HomeAssistant, **msg: Any) -> dict[str, Any]:
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(msg)
    response = await client.receive_json()
    assert response["success"], response
    return response["result"]  # type: ignore[no-any-return]


def _options(hass: HomeAssistant) -> Any:
    return hass.config_entries.async_entries("hauswacht")[0].options


async def test_get_lists_groups_and_entities(hass: HomeAssistant, hass_ws_client: Any) -> None:
    await setup_entry(hass, make_entry())
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    assert data["editable"] is True
    assert {g["id"] for g in data["groups"]} == {"aussen", "keller"}
    assert data["sensor_types"][DOOR] == "door"
    assert any(e["id"] == WINDOW for e in data["entities"])
    assert len(data["revision"]) == 16


async def test_apply_saves_group_with_types(hass: HomeAssistant, hass_ws_client: Any) -> None:
    await setup_entry(hass, make_entry())
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    result = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="group_save",
        data={
            "id": "keller",
            "name": "Keller",
            "entities": [MOTION],
            "types": {MOTION: "door"},
        },
    )
    assert result["ok"] is True
    await hass.async_block_till_done()
    assert _options(hass)["sensor_types"][MOTION] == "door"
    # Die alte Revision gilt nicht mehr
    again = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="group_delete",
        data={"id": "keller"},
    )
    assert again == {"ok": False, "errors": {"base": "changed_elsewhere"}}


async def test_apply_reports_field_errors(hass: HomeAssistant, hass_ws_client: Any) -> None:
    await setup_entry(hass, make_entry())
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    result = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="group_save",
        data={"name": "Doppelt", "entities": [DOOR]},
    )
    assert result["ok"] is False
    assert result["errors"] == {"base": "zone_overlap"}
    assert result["details"]["conflicts"] == {DOOR: "Außen"}


async def test_apply_refused_while_armed(hass: HomeAssistant, hass_ws_client: Any) -> None:
    await setup_entry(hass, make_entry())
    await hass.services.async_call(
        "hauswacht", "arm", {"entity_id": PANEL, "profile": "home"}, blocking=True
    )
    await hass.async_block_till_done()
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    assert data["editable"] is False
    result = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="group_delete",
        data={"id": "keller"},
    )
    assert result == {"ok": False, "errors": {"base": "disarm_first"}}
    assert "keller" in _options(hass)["zones"]


async def test_apply_special_and_always(hass: HomeAssistant, hass_ws_client: Any) -> None:
    hass.states.async_set("input_number.test", "0")
    await setup_entry(hass, make_entry())
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    result = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="strength_save",
        data={"entity": "input_number.test", "threshold": 25, "group": "keller"},
    )
    assert result["ok"] is True
    await hass.async_block_till_done()
    assert "input_number.test" in _options(hass)["zones"]["keller"]["entities"]
    # Nach dem Neuladen holt die Seite die Einstellungen (und die Revision) neu
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    result = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="always_save",
        data={"zones": [], "sensors": [WINDOW]},
    )
    assert result["ok"] is True, result
    await hass.async_block_till_done()
    assert _options(hass)["always_active"]["sensors"] == [WINDOW]


async def test_apply_sensor_excluded_in_profile(hass: HomeAssistant, hass_ws_client: Any) -> None:
    await setup_entry(hass, make_entry())
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    assert {p["id"] for p in data["profiles"]} >= {"home", "night"}
    result = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="sensor_save",
        data={"entity": MOTION, "group": "keller", "type": "motion", "excluded": ["night"]},
    )
    assert result["ok"] is True, result
    await hass.async_block_till_done()
    assert _options(hass)["profiles"]["night"]["excluded"] == [MOTION]


async def test_apply_profile_save_new_and_delete(hass: HomeAssistant, hass_ws_client: Any) -> None:
    await setup_entry(hass, make_entry())
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    edit = data["profile_edit"]
    night = next(p for p in edit["profiles"] if p["id"] == "night")
    changed = {**night, "entry_delay": 45, "excluded": [MOTION]}
    result = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="profile_save",
        data=changed,
    )
    assert result["ok"] is True, result
    await hass.async_block_till_done()
    stored = _options(hass)["profiles"]["night"]
    assert stored["entry_delay"] == 45
    assert stored["excluded"] == [MOTION]
    # Neues Profil aus den Vorgaben; gleicher Knopf wie "Nacht" wird abgelehnt
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    new = {**data["profile_edit"]["defaults"], "name": "Garten", "panel_mode": "night"}
    refused = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="profile_save",
        data=new,
    )
    assert refused["errors"] == {"panel_mode": "panel_mode_taken"}
    new["panel_mode"] = "none"
    new["zones"] = ["aussen"]
    created = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="profile_save",
        data=new,
    )
    assert created["ok"] is True, created
    await hass.async_block_till_done()
    assert _options(hass)["profiles"]["garten"]["zones"] == ["aussen"]
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    deleted = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="profile_delete",
        data={"id": "garten"},
    )
    assert deleted["ok"] is True
    await hass.async_block_till_done()
    assert "garten" not in _options(hass)["profiles"]


async def test_profile_persons_show_in_overview_after_reload(
    hass: HomeAssistant, hass_ws_client: Any
) -> None:
    hass.states.async_set("person.anna", "home", {"friendly_name": "Anna"})
    await setup_entry(hass, make_entry())
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    night = next(p for p in data["profile_edit"]["profiles"] if p["id"] == "night")
    night["automation"]["auto_away_persons"] = ["person.anna"]
    result = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="profile_save",
        data=night,
    )
    assert result["ok"] is True, result
    await hass.async_block_till_done()
    # Nach dem Neuladen läuft Hauswacht mit genau dem gespeicherten Stand
    fresh = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    assert fresh["loaded_revision"] == result["revision"] == fresh["revision"]
    overview = await _ws(hass_ws_client, hass, type="hauswacht/overview")
    profile = next(p for p in overview["profiles"] if p["id"] == "night")
    assert profile["auto"]["away_persons"] == ["Anna"]


async def test_sirens_release_needs_confirmation(hass: HomeAssistant, hass_ws_client: Any) -> None:
    """Nur Einstellungen – es wird keine Sirene geschaltet."""
    hass.states.async_set("siren.flur", "off", {"friendly_name": "Flur"})
    await setup_entry(hass, make_entry())
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    assert any(c["id"] == "siren.flur" for c in data["sirens"]["candidates"])
    payload = {"sirens": ["siren.flur"], "hardware_enabled": True, "allow_switch": False}
    refused = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="sirens_save",
        data=payload,
    )
    assert refused["errors"] == {"base": "confirm_hardware_required"}
    assert not _options(hass).get("sirens_hardware_enabled")
    result = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="sirens_save",
        data={**payload, "confirm_hardware": True},
    )
    assert result["ok"] is True, result
    await hass.async_block_till_done()
    assert _options(hass)["sirens"] == ["siren.flur"]
    assert _options(hass)["sirens_hardware_enabled"] is True
    assert hass.states.get("siren.flur").state == "off"


async def test_notify_settings_and_event_text(hass: HomeAssistant, hass_ws_client: Any) -> None:
    await setup_entry(hass, make_entry())
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    events = {e["event"]: e for e in data["notify"]["events"]}
    assert "alarm" in events
    result = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="notify_save",
        data={
            "notify_system": ["notify.anna"],
            "notify_in_test_mode": True,
            "critical_alerts": False,
            "event_armed": {"enabled": False, "targets": []},
            "reminder": {"reminder_persons": [], "reminder_profile": "night", "reminder_delay": 20},
        },
    )
    assert result["ok"] is True, result
    await hass.async_block_till_done()
    options = _options(hass)
    assert options["notify_system"] == ["notify.anna"]
    assert options["events"]["armed"]["enabled"] is False
    assert options["reminder_profile"] == "night"
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    bad = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="notify_text_save",
        data={"event": "armed", "title": "", "message": "{foo}"},
    )
    assert bad["errors"] == {"message": "invalid_template"}
    assert "{foo}" in bad["details"]["message"]
    good = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="notify_text_save",
        data={"event": "armed", "title": "Scharf", "message": "{profil} ist scharf"},
    )
    assert good["ok"] is True, good
    await hass.async_block_till_done()
    armed = _options(hass)["events"]["armed"]
    assert armed["message"] == "{profil} ist scharf"
    assert armed["enabled"] is False
    fresh = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    text = next(e for e in fresh["notify"]["events"] if e["event"] == "armed")
    assert text["preview"]
    assert "{" not in text["preview"]


async def test_rule_check_converts_between_form_and_yaml(
    hass: HomeAssistant, hass_ws_client: Any
) -> None:
    await setup_entry(hass, make_entry())
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    assert "rules" in data["rule_edit"]
    form = {
        "name": "Tür dann Keller",
        "result": "alarm",
        "steps": [
            {"any": [{"sensor": DOOR}], "within": 90},
            {"any": [{"group": "Keller"}], "within": 60},
        ],
    }
    checked = await _ws(hass_ws_client, hass, type="hauswacht/settings/rule_check", rule=form)
    assert checked["ok"] is True, checked
    assert checked["ui"] is True
    assert "Keller" in checked["yaml"]
    assert "90" in checked["text"]
    # YAML zurück ins Formular
    back = await _ws(
        hass_ws_client, hass, type="hauswacht/settings/rule_check", yaml=checked["yaml"]
    )
    assert back["rule"] == checked["rule"]
    # Verschachtelt: nur YAML
    nested = (
        "name: Komplex\nsteps:\n  - all:\n      - any:\n          - group: Keller\n"
        f"      - sensor: {DOOR}\n"
    )
    complex_rule = await _ws(
        hass_ws_client, hass, type="hauswacht/settings/rule_check", yaml=nested
    )
    assert complex_rule["parsed"] is True
    assert complex_rule["ui"] is False
    broken = await _ws(
        hass_ws_client, hass, type="hauswacht/settings/rule_check", yaml="name: [kaputt"
    )
    assert broken["parsed"] is False
    assert broken["messages"]


async def test_apply_rule_save_yaml_and_delete(hass: HomeAssistant, hass_ws_client: Any) -> None:
    await setup_entry(hass, make_entry())
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    text = (
        "name: Tür dann Keller\nresult: notify\nsteps:\n"
        f"  - any:\n      - sensor: {DOOR}\n    within: 90\n"
        "  - any:\n      - group: Keller\n"
    )
    result = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="rule_save",
        data={"yaml": text, "profiles": ["night"]},
    )
    assert result["ok"] is True, result
    rule_id = result["id"]
    await hass.async_block_till_done()
    options = _options(hass)
    assert options["rules"][rule_id]["result"] == "notify"
    assert options["rules"][rule_id]["steps"][1]["any"] == [{"group": "keller"}]
    assert rule_id in options["profiles"]["night"]["rules"]
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    listed = next(r for r in data["rule_edit"]["rules"] if r["id"] == rule_id)
    assert listed["profiles"] == ["night"]
    taken = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="rule_save",
        data={"rule": listed["rule"]},
    )
    assert taken["errors"] == {"name": "rule_name_taken"}
    deleted = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="rule_delete",
        data={"id": rule_id},
    )
    assert deleted["ok"] is True
    await hass.async_block_till_done()
    assert rule_id not in _options(hass)["rules"]
    assert rule_id not in _options(hass)["profiles"]["night"].get("rules", [])
