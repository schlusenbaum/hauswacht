"""Integrationstests: jedes Handy nur einmal unter den Empfängern (App-Dienst statt App-Entität)."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_mock_service

from custom_components.hauswacht.notify_targets import (
    canonical_targets,
    notify_choices,
)

from .conftest import make_entry, setup_entry

ENTITY = "notify.xiaomi_13"
SERVICE = "mobile_app_2211133g_xiaomi13"


def _phone(hass: HomeAssistant) -> list:
    app = MockConfigEntry(domain="mobile_app", data={"device_name": "2211133G Xiaomi13"})
    app.add_to_hass(hass)
    er.async_get(hass).async_get_or_create(
        "notify", "mobile_app", "phone1", config_entry=app, suggested_object_id="xiaomi_13"
    )
    hass.states.async_set(ENTITY, "unknown", {"friendly_name": "Xiaomi 13 Christian"})
    return async_mock_service(hass, "notify", SERVICE)


async def test_phone_listed_once_with_its_name(hass: HomeAssistant) -> None:
    _phone(hass)
    choices = notify_choices(hass)
    phone = [c for c in choices if "13" in c["name"]]
    assert phone == [{"id": SERVICE, "name": "Xiaomi 13 Christian", "kind": "app"}]
    assert canonical_targets(hass, [ENTITY, SERVICE]) == [SERVICE]


async def test_old_entity_target_goes_through_app_service(hass: HomeAssistant) -> None:
    push = _phone(hass)
    entry = make_entry({"notify_system": [ENTITY]})
    await setup_entry(hass, entry)
    await hass.async_block_till_done()
    # Einmalig umgestellt: gleiches Handy, aber über den Dienst (Knöpfe, Aufräumen)
    assert entry.options["notify_system"] == [SERVICE]
    runtime = entry.runtime_data
    runtime.notifier.send_system("Titel", "Text")
    await hass.async_block_till_done()
    assert push
