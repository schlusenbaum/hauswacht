"""Integrationstests: Funkstille-Beobachtung (schaltet nichts)."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.hauswacht.const import DOMAIN

from .conftest import DOOR, make_entry, set_sensor, setup_entry


async def test_silence_sensor_and_form(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    runtime = entry.runtime_data
    assert runtime.silence is not None
    set_sensor(hass, DOOR, "on")
    await hass.async_block_till_done()
    runtime.silence.sample()
    sensor = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_silence")
    assert sensor is not None
    state = hass.states.get(sensor)
    assert state is not None
    assert "sensors" in state.attributes
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    for step in ("system", "sensor_behaviour"):
        flow = await hass.config_entries.options.async_configure(
            flow["flow_id"], {"next_step_id": step}
        )
    assert "Beobachtet seit" in flow["description_placeholders"]["observation"] or (
        "Observed" in flow["description_placeholders"]["observation"]
    )
