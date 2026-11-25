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


async def test_apply_profile_save_return(hass: HomeAssistant, hass_ws_client: Any) -> None:
    """„Bei Rückkehr“ (0.61): eigene Personenliste, ohne Person wird abgelehnt."""
    hass.states.async_set("person.anna", "not_home", {"friendly_name": "Anna"})
    await setup_entry(hass, make_entry())
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    edit = data["profile_edit"]
    assert edit["choices"]["return_modes"] == ["off", "auto_only", "door", "always", "passage"]
    night = next(p for p in edit["profiles"] if p["id"] == "night")
    assert night["return"] == {
        "mode": "off",
        "persons": [],
        "window": 5,
        "approach_delay": 0,
        "approach_valid": 15,
    }
    refused = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="profile_save",
        data={**night, "return": {"mode": "door", "persons": [], "window": 5}},
    )
    assert refused["errors"] == {"return": "return_needs_persons"}
    back = {
        "mode": "door",
        "persons": ["person.anna"],
        "window": 7,
        "approach_delay": 0,
        "approach_valid": 15,
    }
    result = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="profile_save",
        data={**night, "return": back},
    )
    assert result["ok"] is True, result
    await hass.async_block_till_done()
    assert _options(hass)["profiles"]["night"]["return"] == back


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


async def test_person_save_with_pin_and_delete(hass: HomeAssistant, hass_ws_client: Any) -> None:
    await setup_entry(hass, make_entry())
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    assert "people" in data
    bad = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="user_save",
        data={"name": "Anna", "new_pin": "12"},
    )
    assert bad["errors"] == {"new_pin": "invalid_pin"}
    result = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="user_save",
        data={"name": "Anna", "new_pin": "4711", "valid_until": "2030-01-01T18:00"},
    )
    assert result["ok"] is True, result
    await hass.async_block_till_done()
    anna = _options(hass)["users"][result["id"]]
    assert anna["pin_digest"]
    assert anna["valid_until"].startswith("2030-01-01T18:00")
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    listed = next(u for u in data["people"]["users"] if u["id"] == result["id"])
    assert listed["has_pin"] is True
    assert "4711" not in str(data)
    assert listed["valid_until"] == "2030-01-01T18:00"
    deleted = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=data["revision"],
        action="user_delete",
        data={"id": result["id"]},
    )
    assert deleted["ok"] is True
    await hass.async_block_till_done()
    assert result["id"] not in _options(hass).get("users", {})


async def _apply(
    hass_ws_client: Any, hass: HomeAssistant, action: str, data: dict[str, Any]
) -> dict[str, Any]:
    current = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    result = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/settings/apply",
        revision=current["revision"],
        action=action,
        data=data,
    )
    await hass.async_block_till_done()
    return result


async def test_system_settings(hass: HomeAssistant, hass_ws_client: Any) -> None:
    await setup_entry(hass, make_entry())
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    assert data["system"]["restart"]["behavior"] == "restore"
    refused = await _apply(hass_ws_client, hass, "restart_save", {"behavior": "armed"})
    assert refused["errors"] == {"base": "restart_needs_profile"}
    ok = await _apply(
        hass_ws_client,
        hass,
        "restart_save",
        {"behavior": "armed", "profiles": {"main": "night"}},
    )
    assert ok["ok"] is True, ok
    assert _options(hass)["restart_profiles"] == {"main": "night"}
    assert (await _apply(hass_ws_client, hass, "silence_save", {"hours": 12}))["ok"]
    assert _options(hass)["stale_after_hours"] == 12
    area = await _apply(hass_ws_client, hass, "area_save", {"name": "Garage"})
    assert area["ok"] is True, area
    assert "garage" in _options(hass)["areas"]
    gone = await _apply(hass_ws_client, hass, "area_delete", {"id": area["id"]})
    assert gone["ok"] is True
    assert area["id"] not in _options(hass).get("areas", {})


async def test_pin_rules_master_pin(hass: HomeAssistant, hass_ws_client: Any) -> None:
    await setup_entry(hass, make_entry())
    bad = await _apply(hass_ws_client, hass, "pin_rules_save", {"master_pin": "12"})
    assert bad["errors"] == {"master_pin": "invalid_pin"}
    ok = await _apply(
        hass_ws_client,
        hass,
        "pin_rules_save",
        {"master_pin": "123456", "buttons_without_pin": True},
    )
    assert ok["ok"] is True, ok
    assert _options(hass)["users"]["master"]["pin_digest"]
    assert _options(hass)["buttons_without_pin"] is True
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    assert data["system"]["pin_rules"]["master"] is True
    assert "123456" not in str(data)


async def test_siren_tone_and_test_settings(hass: HomeAssistant, hass_ws_client: Any) -> None:
    """Nur Einstellungen – keine Sirene wird geschaltet."""
    hass.states.async_set(
        "siren.flur",
        "off",
        {"supported_features": 1 | 2 | 4, "available_tones": ["burglar", "fire"]},
    )
    await setup_entry(hass, make_entry())
    assert (await _apply(hass_ws_client, hass, "sirens_save", {"sirens": ["siren.flur"]}))["ok"]
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    item = data["sirens"]["items"][0]
    assert {"tone": "fire", "fire": True} in item["tones"]
    refused = await _apply(
        hass_ws_client, hass, "siren_tone_save", {"siren": "siren.flur", "tone": "fire"}
    )
    assert refused["errors"] == {"tone": "siren_tone_fire"}
    ok = await _apply(
        hass_ws_client,
        hass,
        "siren_tone_save",
        {"siren": "siren.flur", "tone": "fire", "allow_fire_tone": True, "confirm_fire_tone": True},
    )
    assert ok["ok"] is True, ok
    assert _options(hass)["siren_tones"] == {"siren.flur": "fire"}
    assert _options(hass)["siren_fire_tone_ok"] == ["siren.flur"]
    test = await _apply(
        hass_ws_client, hass, "siren_test_save", {"reminder_months": 6, "prewarn": True}
    )
    assert test["ok"] is True
    assert _options(hass)["siren_test"] == {"reminder_months": 6, "prewarn": True}
    assert hass.states.get("siren.flur").state == "off"


async def test_control_card_speech_always(hass: HomeAssistant, hass_ws_client: Any) -> None:
    hass.states.async_set("event.taster", "unknown", {"event_types": ["single", "double"]})
    await setup_entry(hass, make_entry())
    keypad = await _apply(
        hass_ws_client,
        hass,
        "control_save",
        {
            "kind": "keypad",
            "name": "Keypad Flur",
            "topic": "zigbee2mqtt/Keypad Flur",
            "arm_night_zones": "night",
        },
    )
    assert keypad["ok"] is True, keypad
    stored = _options(hass)["controls"][keypad["id"]]
    assert stored["buttons"] == {"arm_night_zones": "night"}
    missing = await _apply(hass_ws_client, hass, "control_save", {"kind": "keypad", "name": "X"})
    assert missing["errors"] == {"keypad_device": "control_keypad_topic"}
    generic = await _apply(
        hass_ws_client,
        hass,
        "control_save",
        {"kind": "generic_keypad", "name": "Keypad Garage", "buttons": {"Away": "away"}},
    )
    assert generic["ok"] is True, generic
    stored = _options(hass)["controls"][generic["id"]]
    assert stored["kind"] == "generic_keypad"
    assert stored["buttons"] == {"away": "away"}
    reserved = await _apply(
        hass_ws_client,
        hass,
        "control_save",
        {"kind": "generic_keypad", "name": "Y", "buttons": {"disarm": "away"}},
    )
    assert reserved["errors"] == {"base": "control_button_reserved"}
    button = await _apply(
        hass_ws_client,
        hass,
        "control_save",
        {
            "kind": "button",
            "name": "Taster",
            "entity": "event.taster",
            "presses": {"single": "away"},
        },
    )
    assert button["ok"] is True, button
    assert _options(hass)["controls"][button["id"]]["presses"] == {"single": "away"}
    person = await _apply(hass_ws_client, hass, "user_save", {"name": "Anna"})
    card = await _apply(
        hass_ws_client, hass, "card_add", {"card": "04A1B2C3", "user": person["id"], "name": "Blau"}
    )
    assert card["ok"] is True, card
    assert "04A1B2C3" in _options(hass)["users"][person["id"]]["tags"]
    off = await _apply(
        hass_ws_client,
        hass,
        "card_save",
        {"tag": "04A1B2C3", "user": person["id"], "active": False},
    )
    assert off["ok"] is True
    assert _options(hass)["users"][person["id"]]["tags_disabled"] == ["04A1B2C3"]
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/new_cards")
    assert data["cards"][0]["tag"] == "04A1B2C3"
    speech = await _apply(
        hass_ws_client,
        hass,
        "speech_save",
        {
            "speakers": [],
            "repeat": 30,
            "quiet_enabled": True,
            "quiet_start": "22:30",
            "quiet_end": "06:00",
        },
    )
    assert speech["ok"] is True, speech
    assert _options(hass)["speech"]["quiet"] == {"enabled": True, "start": "22:30", "end": "06:00"}
    bad = await _apply(
        hass_ws_client,
        hass,
        "speech_event_save",
        {"event": "alarm", "enabled": True, "mode": "speak", "text": "{foo}"},
    )
    assert bad["errors"] == {"text": "invalid_template"}
    always = await _apply(
        hass_ws_client,
        hass,
        "always_save",
        {
            "zones": [],
            "sensors": [],
            "sirens_settings": {"sirens_enabled": True, "siren_tone": "fire", "reaction_time": 60},
        },
    )
    assert always["ok"] is True, always
    stored_always = _options(hass)["always_active"]
    assert stored_always["sirens_enabled"] is True
    assert stored_always["siren_tone"] == "burglar"  # Brandton hier nie
    assert stored_always["reaction_time"] == 60


async def test_sensor_stale_limit_on_page(hass: HomeAssistant, hass_ws_client: Any) -> None:
    await setup_entry(hass, make_entry())
    result = await _apply(
        hass_ws_client,
        hass,
        "sensor_save",
        {"entity": MOTION, "group": "keller", "type": "motion", "stale": {"mode": "off"}},
    )
    assert result["ok"] is True, result
    assert _options(hass)["stale_overrides"] == {MOTION: 0}
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    assert data["system"]["silence"]["overrides"] == {MOTION: 0}
    overview = await _ws(hass_ws_client, hass, type="hauswacht/overview")
    assert overview["monitoring"]["stale_overrides"][0]["hours"] == 0


async def test_advisor_checks_draft_without_saving(
    hass: HomeAssistant, hass_ws_client: Any
) -> None:
    """Gemeinsame Prüfung (ADR 0017): prüft den Entwurf, speichert nichts, schaltet nichts."""
    # Anna ohne Koordinaten: kann nie als weg erkannt werden
    hass.states.async_set("person.anna", "home", {"friendly_name": "Anna"})
    await setup_entry(hass, make_entry())
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    stored = await _ws(hass_ws_client, hass, type="hauswacht/advisor/check", language="de")
    assert stored == {"findings": [], "item": None}
    night = next(p for p in data["profile_edit"]["profiles"] if p["id"] == "night")
    night["automation"]["auto_away_persons"] = ["person.anna"]
    draft = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/advisor/check",
        action="profile_save",
        data=night,
        language="de",
    )
    assert draft["item"] == "night"
    assert [(f["code"], f["level"], f["profile"]) for f in draft["findings"]] == [
        ("away_never", "error", "night")
    ]
    assert "Anna" in draft["findings"][0]["text"]
    # Nichts gespeichert
    after = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    assert after["revision"] == data["revision"]
    # Gespeichert: der Fehler steht auch in den Prüfhinweisen
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
    overview = await _ws(hass_ws_client, hass, type="hauswacht/overview")
    codes = [f["code"] for f in overview["findings"]]
    assert "advisor_away_never" in codes
    # Mit „Tür + Signal“ für Anna (Seitenblatt Anwesenheit) passt es
    fixed = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/advisor/check",
        action="homecoming_save",
        data={
            "observe": False,
            "persons": [],
            "ssids": [],
            "signals": {},
            "proof_weak": ["person.anna"],
        },
    )
    assert fixed["findings"] == []


async def test_advisor_apply_fix_with_safeguards(hass: HomeAssistant, hass_ws_client: Any) -> None:
    """Check-up (ADR 0017): nur aktuelle Vorschläge, abschwächende nur mit Bestätigung."""
    hass.states.async_set("person.anna", "home", {"friendly_name": "Anna"})
    entry = make_entry({"profiles": {"night": {"auto_away_persons": ["person.anna"]}}})
    await setup_entry(hass, entry)
    before = dict(_options(hass)["profiles"]["night"])
    check = await _ws(hass_ws_client, hass, type="hauswacht/advisor/check", language="de")
    (finding,) = check["findings"]
    assert finding["code"] == "away_never"
    remove, weak = finding["fixes"]
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")

    async def apply(fix: dict[str, Any], **extra: Any) -> dict[str, Any]:
        return await _ws(
            hass_ws_client,
            hass,
            type="hauswacht/advisor/apply",
            revision=extra.pop("revision", data["revision"]),
            fix=fix,
            **extra,
        )

    assert (await apply(remove, revision="alt"))["errors"] == {"base": "changed_elsewhere"}
    # Nur, was der Assistent gerade selbst vorschlägt
    other = {**remove, "path": "entry_delay", "op": "set", "value": 1}
    assert (await apply(other))["errors"] == {"base": "fix_not_offered"}
    # Abschwächend („Tür + Signal“): nur mit Bestätigung
    assert weak["weakens"] is True
    assert (await apply(weak))["errors"] == {"base": "confirm_needed"}
    assert "away_proof_weak" not in _options(hass) or not _options(hass)["away_proof_weak"]
    # Person aus „alle weg“ nehmen: genau diese eine Änderung
    result = await apply(remove)
    assert result["ok"] is True, result
    await hass.async_block_till_done()
    after = _options(hass)["profiles"]["night"]
    assert after["auto_away_persons"] == []
    assert after["entry_delay"] == before.get("entry_delay", after["entry_delay"])
    assert after["zones"] == before["zones"]
    again = await _ws(hass_ws_client, hass, type="hauswacht/advisor/check")
    assert again["findings"] == []
    # Der alte Vorschlag gilt nicht mehr
    assert (await apply(remove, revision=result["revision"]))["errors"] == {
        "base": "fix_not_offered"
    }


async def test_advisor_apply_refused_while_armed(hass: HomeAssistant, hass_ws_client: Any) -> None:
    hass.states.async_set("person.anna", "home", {"friendly_name": "Anna"})
    await setup_entry(
        hass, make_entry({"profiles": {"night": {"auto_away_persons": ["person.anna"]}}})
    )
    check = await _ws(hass_ws_client, hass, type="hauswacht/advisor/check")
    fix = check["findings"][0]["fixes"][0]
    data = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    await hass.services.async_call(
        "hauswacht", "arm", {"entity_id": PANEL, "profile": "home"}, blocking=True
    )
    await hass.async_block_till_done()
    result = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/advisor/apply",
        revision=data["revision"],
        fix=fix,
    )
    assert result == {"ok": False, "errors": {"base": "disarm_first"}}
    assert _options(hass)["profiles"]["night"]["auto_away_persons"] == ["person.anna"]


async def test_advisor_scenarios_only_calculated(hass: HomeAssistant, hass_ws_client: Any) -> None:
    """Szenario-Vorschau: gerechnet mit den echten Einstellungen – nichts wird geschaltet."""
    await setup_entry(hass, make_entry())
    before = hass.states.get(PANEL)
    assert before is not None
    result = await _ws(hass_ws_client, hass, type="hauswacht/advisor/scenarios", language="de")
    found = {s["key"]: s for s in result["scenarios"]}
    door = next(s for key, s in found.items() if key == f"burglary_door:away:{DOOR}")
    assert door["result"] == "ok"
    assert door["summary"].startswith("Alarm nach")
    after = hass.states.get(PANEL)
    assert after is not None
    assert after.state == before.state  # nichts geschaltet


async def test_frozen_location_does_not_count(hass: HomeAssistant, hass_ws_client: Any) -> None:
    """0.64.0b5: eine Ortung, die 24 Stunden exakt gleich bleibt, zählt nicht als Ortung."""
    from custom_components.hauswacht.presence_proof import DATA_FROZEN  # noqa: PLC0415

    gps = "device_tracker.anna_gps"
    # Draußen, weit weg von Zuhause
    fake = {"latitude": 10.0, "longitude": 10.0, "gps_accuracy": 5, "friendly_name": "Fake"}
    hass.states.async_set(gps, "not_home", fake)
    hass.states.async_set(
        "person.anna", "not_home", {"friendly_name": "Anna", "device_trackers": [gps]}
    )
    entry = make_entry({"profiles": {"night": {"auto_away_persons": ["person.anna"]}}})
    await setup_entry(hass, entry)
    first = await _ws(hass_ws_client, hass, type="hauswacht/advisor/check", language="de")
    assert first["findings"] == []  # Anna kann geortet werden
    # Gemerkt: dieselben Koordinaten schon seit 25 Stunden (statt die Uhr vorzustellen)
    store = hass.data[DATA_FROZEN]
    lat, lon, since = store.data.seen[gps]
    store.data.seen[gps] = (lat, lon, since - 25 * 3600)
    later = await _ws(hass_ws_client, hass, type="hauswacht/advisor/check", language="de")
    codes = {f["code"] for f in later["findings"]}
    assert codes == {"away_never", "location_frozen"}
    # Bewegt sie sich wieder, zählt sie sofort wieder
    hass.states.async_set(gps, "not_home", {**fake, "latitude": 10.0001})
    await hass.async_block_till_done()
    moved = await _ws(hass_ws_client, hass, type="hauswacht/advisor/check", language="de")
    assert moved["findings"] == []


async def test_goals_plan_and_apply(hass: HomeAssistant, hass_ws_client: Any) -> None:
    """Einrichten nach Zielen (0.65): Plan ohne Speichern, Übernehmen mit Sicherungen."""
    hass.states.async_set(
        "person.anna", "home", {"friendly_name": "Anna", "latitude": 1.0, "longitude": 1.0}
    )
    await setup_entry(hass, make_entry())
    start = await _ws(hass_ws_client, hass, type="hauswacht/goals/start")
    assert start["targets"]["night"]["id"] == "night"
    assert start["targets"]["away"]["id"] == "away"
    anna = next(p for p in start["persons"] if p["id"] == "person.anna")
    assert anna["detectable"] is True
    door = next(x for x in start["sensors"] if x["id"] == DOOR)
    assert (door["kind"], door["group"]) == ("door", "aussen")
    assert DOOR in start["answers"]["sensors"]["entry_doors"]
    answers = start["answers"]
    answers["goals"] = ["away"]
    answers["away"]["persons"] = ["person.anna"]
    before = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    planned = await _ws(
        hass_ws_client, hass, type="hauswacht/goals/plan", answers=answers, language="de"
    )
    plan = planned["plan"]
    assert plan["errors"] == []
    assert plan["profiles"] == ["away"]
    away = next(step for step in plan["steps"] if step["profile"] == "away")
    labels = [c["label"] for c in away["changes"]]
    assert "Scharf, wenn alle weg" in labels
    assert any(s["key"].startswith("all_leave:away") for s in planned["scenarios"])
    # Nur gerechnet – nichts gespeichert
    after_plan = await _ws(hass_ws_client, hass, type="hauswacht/settings/get")
    assert after_plan["revision"] == before["revision"]
    refused = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/goals/apply",
        revision="alt",
        answers=answers,
    )
    assert refused["errors"] == {"base": "changed_elsewhere"}
    result = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/goals/apply",
        revision=start["revision"],
        answers=answers,
    )
    assert result["ok"] is True, result
    await hass.async_block_till_done()
    assert _options(hass)["profiles"]["away"]["auto_away_persons"] == ["person.anna"]
    assert not _options(hass).get("sirens_hardware_enabled")


async def test_goals_overwrite_needs_confirm(hass: HomeAssistant, hass_ws_client: Any) -> None:
    hass.states.async_set(
        "person.anna", "home", {"friendly_name": "Anna", "latitude": 1.0, "longitude": 1.0}
    )
    entry = make_entry(
        {"profiles": {"away": {"return": {"mode": "auto_only", "persons": ["person.anna"]}}}}
    )
    await setup_entry(hass, entry)
    start = await _ws(hass_ws_client, hass, type="hauswacht/goals/start")
    answers = start["answers"]
    answers["goals"] = ["return"]
    answers["return"] = {"persons": ["person.anna"], "mode": "door"}

    async def apply(**extra: Any) -> dict[str, Any]:
        return await _ws(
            hass_ws_client,
            hass,
            type="hauswacht/goals/apply",
            revision=start["revision"],
            answers=answers,
            **extra,
        )

    assert (await apply())["errors"] == {"base": "confirm_needed"}
    assert _options(hass)["profiles"]["away"]["return"]["mode"] == "auto_only"
    result = await apply(confirm=True)
    assert result["ok"] is True, result
    await hass.async_block_till_done()
    assert _options(hass)["profiles"]["away"]["return"]["mode"] == "door"


async def test_goals_apply_refused_while_armed(hass: HomeAssistant, hass_ws_client: Any) -> None:
    await setup_entry(hass, make_entry())
    start = await _ws(hass_ws_client, hass, type="hauswacht/goals/start")
    await hass.services.async_call(
        "hauswacht", "arm", {"entity_id": PANEL, "profile": "home"}, blocking=True
    )
    await hass.async_block_till_done()
    answers = start["answers"]
    answers["goals"] = ["night"]
    result = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/goals/apply",
        revision=start["revision"],
        answers=answers,
    )
    assert result == {"ok": False, "errors": {"base": "disarm_first"}}


async def test_goals_garage_creates_area(hass: HomeAssistant, hass_ws_client: Any) -> None:
    """0.65.0b3: Ziel Garage legt einen eigenen Bereich mit Bedienfeld an – nichts geschaltet."""
    await setup_entry(hass, make_entry())
    start = await _ws(hass_ws_client, hass, type="hauswacht/goals/start")
    answers = start["answers"]
    answers["goals"] = ["garage"]
    answers["garage"] = {"sensors": [WINDOW], "away": False}
    planned = await _ws(hass_ws_client, hass, type="hauswacht/goals/plan", answers=answers)
    assert planned["plan"]["errors"] == []
    assert planned["plan"]["needs_confirm"] is True  # Fenster verlässt die Gruppe Außen
    result = await _ws(
        hass_ws_client,
        hass,
        type="hauswacht/goals/apply",
        revision=start["revision"],
        answers=answers,
        confirm=True,
    )
    assert result["ok"] is True, result
    await hass.async_block_till_done()
    options = _options(hass)
    assert options["areas"]["garage"]["name"] == "Garage"
    assert options["zones"]["garage"]["entities"] == [WINDOW]
    assert options["profiles"]["garage"]["area"] == "garage"
    # Das Haus überwacht das Fenster weiter (Profile mit „Außen“ haben jetzt auch „Garage“)
    assert "garage" in options["profiles"]["home"]["zones"]
    state = hass.states.get("alarm_control_panel.hauswacht_garage")
    assert state is not None
    assert state.state == "disarmed"
