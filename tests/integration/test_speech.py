"""Integrationstests: Sprachausgabe über Lautsprecher und eigene Texte.

Lautsprecher sind ATTRAPPEN: ein Testgerät mit zwei Benachrichtigungs-Entitäten (Durchsage und
Sprechen) wie bei Echo-Geräten. notify.send_message ist gemockt, es wird nichts angesagt.
Sirenen sind keine eingerichtet.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
    async_mock_service,
)

from .conftest import PANEL, TEST_MODE, WINDOW, make_entry, set_sensor, setup_entry

PHONE = "mobile_app_testhandy"
ANNOUNCE = "notify.echo_test_durchsagen"
SPEAK = "notify.echo_test_sprechen"


async def _service(hass: HomeAssistant, domain: str, service: str, **data: Any) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)
    await hass.async_block_till_done()


def _speaker(hass: HomeAssistant) -> str:
    """Testgerät wie ein Echo: Entitäten mit Kennung …-announce und …-speak."""
    source = MockConfigEntry(domain="alexa_devices", title="Test")
    source.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=source.entry_id, identifiers={("alexa_devices", "echo1")}, name="Echo Test"
    )
    registry = er.async_get(hass)
    for suffix, object_id in (
        ("announce", "echo_test_durchsagen"),
        ("speak", "echo_test_sprechen"),
    ):
        registry.async_get_or_create(
            "notify",
            "alexa_devices",
            f"ECHO1-{suffix}",
            suggested_object_id=object_id,
            device_id=device.id,
            config_entry=source,
        )
    return device.id


def _spoken(calls: list[ServiceCall]) -> list[tuple[list[str], str]]:
    result = []
    for call in calls:
        entities = call.data["entity_id"]
        result.append(
            (list(entities) if isinstance(entities, list) else [entities], call.data["message"])
        )
    return result


async def _setup(hass: HomeAssistant, speech: dict[str, Any], **options: Any) -> list[ServiceCall]:
    calls = async_mock_service(hass, "notify", "send_message")
    device = _speaker(hass)
    speech = {"speakers": [device], **speech}
    await setup_entry(hass, make_entry({"speech": speech, **options}))
    return calls


async def _alarm(hass: HomeAssistant) -> None:
    await _service(hass, "alarm_control_panel", "alarm_arm_night", entity_id=PANEL)
    set_sensor(hass, WINDOW, "on")
    await hass.async_block_till_done()
    assert hass.states.get(PANEL).state == AlarmControlPanelState.TRIGGERED  # type: ignore[union-attr]


async def test_alarm_is_announced(hass: HomeAssistant) -> None:
    calls = await _setup(hass, {})
    await _alarm(hass)
    spoken = _spoken(calls)
    assert len(spoken) == 1
    entities, message = spoken[0]
    assert entities == [ANNOUNCE]
    assert message.startswith("Attention, burglar alarm!") or message.startswith("Achtung")
    assert "kuechenfenster" in message.casefold() or "küchenfenster" in message.casefold()


async def test_mode_speak_uses_speak_entity(hass: HomeAssistant) -> None:
    calls = await _setup(hass, {"events": {"alarm": {"mode": "speak", "text": "Alarm {profil}"}}})
    await _alarm(hass)
    assert _spoken(calls) == [([SPEAK], "Alarm Nacht")]


async def test_silent_alarm_is_not_announced(hass: HomeAssistant) -> None:
    calls = await _setup(hass, {}, profiles={"night": {"silent": True}})
    await _alarm(hass)
    assert calls == []


async def test_disabled_event_and_armed_default_off(hass: HomeAssistant) -> None:
    calls = await _setup(hass, {"events": {"alarm": {"enabled": False}}})
    await _alarm(hass)  # scharf: standardmäßig keine Ansage, Alarm: abgeschaltet
    assert calls == []


async def test_quiet_hours(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    freezer.move_to("2026-11-11T12:00:00+00:00")
    speech = {
        "quiet": {"enabled": True, "start": "00:00", "end": "23:59"},
        "events": {"armed": {"enabled": True}},
    }
    calls = await _setup(hass, speech)
    await _alarm(hass)
    # "scharf" fällt in die Nachtruhe, der Alarm darf trotzdem
    assert len(calls) == 1
    assert "Nacht" not in _spoken(calls)[0][1] or "alarm" in _spoken(calls)[0][1].casefold()


async def test_test_mode_suppresses_speech(hass: HomeAssistant) -> None:
    calls = await _setup(hass, {})
    await _service(hass, "switch", "turn_on", entity_id=TEST_MODE)
    await _alarm(hass)
    assert calls == []


async def test_test_mode_speech_when_allowed(hass: HomeAssistant) -> None:
    calls = await _setup(hass, {}, notify_in_test_mode=True)
    await _service(hass, "switch", "turn_on", entity_id=TEST_MODE)
    await _alarm(hass)
    assert len(calls) == 1
    assert _spoken(calls)[0][1].startswith("Test. ")


async def test_alarm_announcement_repeats_until_ended(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    calls = await _setup(hass, {"repeat": 20})
    await _alarm(hass)
    assert len(calls) == 1
    for _ in range(2):
        freezer.tick(timedelta(seconds=20))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
    assert len(calls) == 3
    await _service(hass, "alarm_control_panel", "alarm_disarm", entity_id=PANEL)
    count = len(calls)
    for _ in range(3):
        freezer.tick(timedelta(seconds=20))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
    assert len(calls) == count


async def test_profile_speakers_override(hass: HomeAssistant) -> None:
    calls = async_mock_service(hass, "notify", "send_message")
    device = _speaker(hass)
    other = dr.async_get(hass).async_get_or_create(
        config_entry_id=hass.config_entries.async_entries("alexa_devices")[0].entry_id,
        identifiers={("alexa_devices", "echo2")},
        name="Echo Zwei",
    )
    er.async_get(hass).async_get_or_create(
        "notify",
        "alexa_devices",
        "ECHO2-announce",
        suggested_object_id="echo_zwei_durchsagen",
        device_id=other.id,
    )
    await setup_entry(
        hass,
        make_entry(
            {"speech": {"speakers": [device]}, "profiles": {"night": {"speakers": [other.id]}}}
        ),
    )
    await _alarm(hass)
    assert _spoken(calls)[0][0] == ["notify.echo_zwei_durchsagen"]


async def test_custom_push_text(hass: HomeAssistant) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    options = {
        "notify_system": [PHONE],
        "events": {"alarm": {"title": "EINBRUCH", "message": "Einbruch: {melder} ({profil})"}},
    }
    await setup_entry(hass, make_entry(options))
    await _alarm(hass)
    assert push[0].data["title"] == "EINBRUCH"
    assert push[0].data["message"].startswith("Einbruch: ")
    assert push[0].data["message"].endswith("(Nacht)")


async def test_options_speech_and_invalid_template(hass: HomeAssistant) -> None:
    entry = make_entry()
    await setup_entry(hass, entry)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "notifications"}
    )
    assert "speech" in flow["menu_options"]
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "speech_events"}
    )
    flow = await hass.config_entries.options.async_configure(flow["flow_id"], {"event": "armed"})
    assert flow["step_id"] == "speech_event_edit"
    data = {"enabled": True, "mode": "speak", "speakers": [], "in_quiet": False}
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {**data, "text": "Scharf {gibtsnicht}"}
    )
    assert flow["errors"] == {"text": "invalid_template"}
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {**data, "text": "Scharf: {profil}"}
    )
    assert flow["step_id"] == "notifications"
    assert entry.options["speech"]["events"]["armed"]["text"] == "Scharf: {profil}"
    # Eigener Push-Text: leer speichern löscht ihn wieder
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "notify_texts"}
    )
    flow = await hass.config_entries.options.async_configure(flow["flow_id"], {"event": "alarm"})
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"message": "Alarm: {melder}"}
    )
    assert entry.options["events"]["alarm"]["message"] == "Alarm: {melder}"
    flow = await hass.config_entries.options.async_configure(
        flow["flow_id"], {"next_step_id": "notify_texts"}
    )
    flow = await hass.config_entries.options.async_configure(flow["flow_id"], {"event": "alarm"})
    flow = await hass.config_entries.options.async_configure(flow["flow_id"], {})
    assert "message" not in entry.options["events"]["alarm"]
