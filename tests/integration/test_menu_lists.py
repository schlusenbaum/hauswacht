"""Integrationstests: Menüs zeigen, was es schon gibt."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from custom_components.hauswacht.core.pin import hash_pin

from .conftest import make_entry, setup_entry


async def _menu(hass: HomeAssistant, entry: Any, *steps: str) -> dict[str, Any]:
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    for step in steps:
        flow = await hass.config_entries.options.async_configure(
            flow["flow_id"], {"next_step_id": step}
        )
    return flow  # type: ignore[no-any-return]


async def test_menus_list_existing_items(hass: HomeAssistant) -> None:
    entry = make_entry(
        {
            "users": {"anna": {"name": "Anna"}},
            "controls": {"flur": {"name": "Keypad Flur", "kind": "keypad", "topic": "z2m/kp"}},
            "areas": {"garage": {"name": "Garage"}},
            "sirens": ["siren.flur"],
        }
    )
    await setup_entry(hass, entry)
    zones = (await _menu(hass, entry, "triggering", "zones"))["description_placeholders"]
    assert "Außen" in zones["items"]
    assert "Keller" in zones["items"]
    profiles = (await _menu(hass, entry, "profiles"))["description_placeholders"]["items"]
    assert "Nacht" in profiles
    assert "Außen" in profiles  # was das Profil überwacht
    assert (
        "Garage"
        in (await _menu(hass, entry, "system", "areas"))["description_placeholders"]["items"]
    )
    users = (await _menu(hass, entry, "system", "users"))["description_placeholders"]["items"]
    assert "Anna" in users
    controls = (await _menu(hass, entry, "system", "controls"))["description_placeholders"]
    assert "Keypad Flur" in controls["items"]
    sirens = (await _menu(hass, entry, "sirens"))["description_placeholders"]["items"]
    assert "siren.flur" in sirens or "flur" in sirens.casefold()
    assert "off" in sirens or "aus" in sirens


async def test_empty_lists_show_dash(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    users = (await _menu(hass, entry, "system", "users"))["description_placeholders"]["items"]
    assert users.startswith("**Existing users:** –")


async def test_master_pin_status_without_showing_a_user(hass: HomeAssistant) -> None:
    pin = hash_pin("2468")
    entry = make_entry(
        {
            "users": {
                "master": {"name": "Master-PIN", "pin_salt": pin.salt, "pin_digest": pin.digest}
            }
        }
    )
    await setup_entry(hass, entry)
    users = (await _menu(hass, entry, "system", "users"))["description_placeholders"]["items"]
    assert "Master PIN:** ✅" in users
    assert "Master-PIN (" not in users  # kein eigener Benutzer in der Liste
    code = (await _menu(hass, entry, "system", "users", "code"))["description_placeholders"]
    assert "✅" in code["master"]
    assert code["pin_users"] == "–"
    assert "2468" not in str(code)


async def test_master_pin_none(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    users = (await _menu(hass, entry, "system", "users"))["description_placeholders"]["items"]
    assert "Master PIN:** – none" in users
