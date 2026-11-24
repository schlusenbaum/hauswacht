"""Integrationstests: Durchgang (ADR 0013) – rein oder raus, ohne unscharf zu schalten.

Kein echtes Gerät: Das Keypad ist die Aktion ``hauswacht.keypad_input`` (allgemeines Keypad),
Sensoren sind Testzustände, notify ist eine Attrappe. Keine Sirenen.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import Context, HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockUser,
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.hauswacht.const import (
    DOMAIN,
    PUSH_ACTION_EVENT,
    PUSH_PASSAGE_PREFIX,
    PUSH_PASSAGE_TAG,
    PUSH_TAG,
)
from custom_components.hauswacht.core.passage import PASSAGE_TARGET
from custom_components.hauswacht.core.pin import hash_pin

from .conftest import DOOR, MOTION, PANEL, WINDOW, make_entry, set_sensor, setup_entry

PIN = "1357"
DURESS = "9999"
PHONE = "mobile_app_testhandy"
ALERT = "mobile_app_notfall"


def _options(**passage: Any) -> dict[str, Any]:
    hashed, duress = hash_pin(PIN), hash_pin(DURESS)
    return {
        "users": {
            "anna": {
                "name": "Anna",
                "pin_salt": hashed.salt,
                "pin_digest": hashed.digest,
                "duress_salt": duress.salt,
                "duress_digest": duress.digest,
            }
        },
        "controls": {
            "flur": {
                "name": "Keypad Flur",
                "kind": "generic_keypad",
                "buttons": {"night": "night", "home": "home", "pass": PASSAGE_TARGET},
            }
        },
        "notify_system": [PHONE],
        "duress_notify": [ALERT],
        "profiles": {
            "night": {
                "entry_delay": 30,
                "passage": {
                    "enabled": True,
                    "duration": 5,
                    "path": [MOTION],
                    "path_after": 10,
                    **passage,
                },
            }
        },
    }


async def _setup(hass: HomeAssistant, **passage: Any) -> list[ServiceCall]:
    push = async_mock_service(hass, "notify", PHONE)
    await setup_entry(hass, make_entry(_options(**passage)))
    return push


async def _key(hass: HomeAssistant, button: str, code: str | None = PIN) -> dict[str, Any]:
    response = await hass.services.async_call(
        DOMAIN,
        "keypad_input",
        {"keypad": "flur", "button": button, "code": code},
        blocking=True,
        return_response=True,
    )
    await hass.async_block_till_done()
    assert isinstance(response, dict)
    return response


async def _arm_night(hass: HomeAssistant) -> None:
    await _key(hass, "night")
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT


async def _set(hass: HomeAssistant, entity_id: str, state: str) -> None:
    set_sensor(hass, entity_id, state)
    await hass.async_block_till_done()


async def _later(hass: HomeAssistant, seconds: float) -> None:
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=seconds))
    await hass.async_block_till_done()


def _panel(hass: HomeAssistant) -> str:
    state = hass.states.get(PANEL)
    assert state is not None
    return state.state


def _passage(hass: HomeAssistant) -> Any:
    state = hass.states.get(PANEL)
    assert state is not None
    return state.attributes["passage"]


def _messages(calls: list[ServiceCall]) -> list[ServiceCall]:
    return [c for c in calls if c.data["message"] != "clear_notification"]


# --- Reinkommen ------------------------------------------------------------------


async def test_coming_in_with_any_profile_key_stays_armed(hass: HomeAssistant) -> None:
    push = await _setup(hass)
    await _arm_night(hass)
    await _set(hass, DOOR, "on")
    assert _panel(hass) == AlarmControlPanelState.PENDING
    answer = await _key(hass, "home")  # andere Profil-Taste: trotzdem nur reinlassen
    assert answer["result"] == "ok"
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    assert _passage(hass)["direction"] == "in"
    assert _passage(hass)["doors"] == [DOOR]
    message = _messages(push)[-1]
    assert "let in" in message.data["message"]
    assert message.data["data"]["tag"] == PUSH_TAG  # ersetzt die Eingangs-Nachricht
    # Weg (Bewegung) frei, Fenster nicht
    await _set(hass, MOTION, "on")
    await _set(hass, MOTION, "off")
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    # Tür zu -> Weg noch 10 s frei, danach wieder überwacht
    await _set(hass, DOOR, "off")
    await _set(hass, MOTION, "on")
    await _set(hass, MOTION, "off")
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    await _later(hass, 11)
    assert _passage(hass) is None
    await _set(hass, MOTION, "on")
    assert _panel(hass) == AlarmControlPanelState.TRIGGERED


async def test_coming_in_door_watched_again_after_closing(hass: HomeAssistant) -> None:
    await _setup(hass)
    await _arm_night(hass)
    await _set(hass, DOOR, "on")
    await _key(hass, "home")  # gleiche Eingabe binnen 2 s zählt nur einmal: andere Taste
    await _set(hass, DOOR, "off")
    await _set(hass, DOOR, "on")  # nächste Person: eigener Ausweis nötig
    assert _panel(hass) == AlarmControlPanelState.PENDING


async def test_window_still_triggers_during_passage(hass: HomeAssistant) -> None:
    await _setup(hass)
    await _arm_night(hass)
    await _set(hass, DOOR, "on")
    await _key(hass, "home")
    await _set(hass, WINDOW, "on")
    assert _panel(hass) == AlarmControlPanelState.TRIGGERED


async def test_passage_needs_credential(hass: HomeAssistant) -> None:
    await _setup(hass)
    await _arm_night(hass)
    await _set(hass, DOOR, "on")
    answer = await _key(hass, "night", code=None)
    assert answer["result"] == "invalid_code"
    answer = await _key(hass, "night", code="0000")
    assert answer["result"] == "invalid_code"
    assert _panel(hass) == AlarmControlPanelState.PENDING


async def test_disarm_still_disarms_during_entry_delay(hass: HomeAssistant) -> None:
    await _setup(hass)
    await _arm_night(hass)
    await _set(hass, DOOR, "on")
    await _key(hass, "disarm")
    assert _panel(hass) == AlarmControlPanelState.DISARMED


async def test_profile_without_passage_keeps_old_behaviour(hass: HomeAssistant) -> None:
    await _setup(hass, enabled=False)
    await _arm_night(hass)
    await _set(hass, DOOR, "on")
    answer = await _key(hass, "home")
    assert answer["result"] != "ok"
    assert _panel(hass) == AlarmControlPanelState.PENDING
    answer = await _key(hass, "pass")
    assert answer["result"] == "not_ready"


async def test_duress_pin_lets_in_and_alerts_silently(hass: HomeAssistant) -> None:
    alert = async_mock_service(hass, "notify", ALERT)
    await _setup(hass)
    await _arm_night(hass)
    await _set(hass, DOOR, "on")
    answer = await _key(hass, "night", code=DURESS)
    assert answer["result"] == "ok"
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    assert alert
    assert "passage" in alert[-1].data["message"]


# --- Rausgehen -------------------------------------------------------------------


async def test_going_out_frees_first_door_for_the_time(hass: HomeAssistant) -> None:
    push = await _setup(hass)
    await _arm_night(hass)
    answer = await _key(hass, "pass")
    assert answer["result"] == "ok"
    assert _passage(hass)["direction"] == "out"
    assert _messages(push)[-1].data["data"]["tag"] == PUSH_PASSAGE_TAG
    for state in ("on", "off", "on", "off"):  # raus und wieder rein
        await _set(hass, DOOR, state)
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    await _set(hass, MOTION, "on")  # Weg frei
    await _set(hass, MOTION, "off")
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    await _later(hass, 5 * 60 + 1)
    assert _passage(hass) is None
    await _set(hass, DOOR, "on")  # vorbei: wieder Eingangsverzögerung
    assert _panel(hass) == AlarmControlPanelState.PENDING


async def test_going_out_with_any_profile_key_when_armed(hass: HomeAssistant) -> None:
    """Alle Tasten belegt: scharf ist jede Profil-Taste "lass mich kurz raus" – nie umschalten."""
    await _setup(hass)
    await _arm_night(hass)
    answer = await _key(hass, "home")
    assert answer["result"] == "ok"
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT  # nicht auf "Zuhause" gewechselt
    assert _passage(hass)["direction"] == "out"
    await _set(hass, DOOR, "on")
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_profile_key_without_passage_does_not_switch(hass: HomeAssistant) -> None:
    await _setup(hass, enabled=False)
    await _arm_night(hass)
    answer = await _key(hass, "home")
    assert answer["result"] != "ok"
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    assert _passage(hass) is None


async def test_going_out_door_open_at_end_warns(hass: HomeAssistant) -> None:
    push = await _setup(hass)
    await _arm_night(hass)
    await _key(hass, "pass")
    await _set(hass, DOOR, "on")
    await _later(hass, 5 * 60 + 1)
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT  # kein Alarm
    warning = _messages(push)[-1]
    assert "still open" in warning.data["message"]
    assert warning.data["data"]["tag"] == PUSH_PASSAGE_TAG
    await _set(hass, DOOR, "off")  # zu: wieder überwacht
    await _set(hass, DOOR, "on")
    assert _panel(hass) == AlarmControlPanelState.PENDING


async def test_going_out_ends_when_back(hass: HomeAssistant) -> None:
    await _setup(hass, out_end="returned")
    await _arm_night(hass)
    await _key(hass, "pass")
    for state in ("on", "off", "on", "off"):  # raus, zu, zurück, zu
        await _set(hass, DOOR, state)
    assert _passage(hass) is None
    await _set(hass, DOOR, "on")
    assert _panel(hass) == AlarmControlPanelState.PENDING


async def test_disarm_ends_passage(hass: HomeAssistant) -> None:
    await _setup(hass)
    await _arm_night(hass)
    await _key(hass, "pass")
    await _key(hass, "disarm")
    assert _panel(hass) == AlarmControlPanelState.DISARMED
    assert _passage(hass) is None


# --- Aktion ----------------------------------------------------------------------


async def test_passage_action(hass: HomeAssistant) -> None:
    await _setup(hass)
    with pytest.raises(ServiceValidationError):  # unscharf: kein Durchgang
        await hass.services.async_call(
            DOMAIN, "passage", {"entity_id": PANEL, "code": PIN}, blocking=True
        )
    await _arm_night(hass)
    await _set(hass, DOOR, "on")
    with pytest.raises(ServiceValidationError):  # falscher PIN
        await hass.services.async_call(
            DOMAIN, "passage", {"entity_id": PANEL, "code": "0000"}, blocking=True
        )
    await hass.services.async_call(
        DOMAIN, "passage", {"entity_id": PANEL, "code": PIN}, blocking=True
    )
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    assert _passage(hass)["direction"] == "in"


# --- Push-Knopf "Reinlassen" (0.59.0b2) ----------------------------------------------


async def test_push_button_lets_in(hass: HomeAssistant, hass_admin_user: MockUser) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    options = _options()
    options["push_disarm"] = True
    options["profiles"]["night"]["notify"] = [PHONE]
    await setup_entry(hass, make_entry(options))
    await _arm_night(hass)
    await _set(hass, DOOR, "on")
    actions = [a["action"] for c in push for a in c.data.get("data", {}).get("actions", [])]
    let_in = next(a for a in actions if a.startswith(PUSH_PASSAGE_PREFIX))
    hass.bus.async_fire(
        PUSH_ACTION_EVENT, {"action": let_in}, context=Context(user_id=hass_admin_user.id)
    )
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    assert _passage(hass)["direction"] == "in"


async def test_push_button_only_with_passage(hass: HomeAssistant) -> None:
    push = async_mock_service(hass, "notify", PHONE)
    options = _options(enabled=False)
    options["push_disarm"] = True
    options["profiles"]["night"]["notify"] = [PHONE]
    await setup_entry(hass, make_entry(options))
    await _arm_night(hass)
    await _set(hass, DOOR, "on")
    actions = [a["action"] for c in push for a in c.data.get("data", {}).get("actions", [])]
    assert actions
    assert not any(a.startswith(PUSH_PASSAGE_PREFIX) for a in actions)


# --- Handy-Reinlassen (0.59.0b2) -----------------------------------------------------

FINJA = "person.finja"
# Ortung weit weg – „weg“ braucht seit 0.61 einen Beleg (ADR 0015)
FAR = {"latitude": 0.0, "longitude": 0.0, "gps_accuracy": 10}


async def _phone_setup(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> list[ServiceCall]:
    hass.states.async_set(FINJA, "not_home", {"friendly_name": "Finja", **FAR})
    push = await _setup(hass, persons=[FINJA], window=5)
    await _arm_night(hass)
    freezer.tick(timedelta(minutes=6))  # lange genug weg
    return push


async def test_phone_after_door_lets_in(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    push = await _phone_setup(hass, freezer)
    await _set(hass, DOOR, "on")
    assert _panel(hass) == AlarmControlPanelState.PENDING
    hass.states.async_set(FINJA, "home", {"friendly_name": "Finja"})
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    assert "Finja (phone)" in _messages(push)[-1].data["message"]


async def test_phone_before_door_lets_in_once(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    await _phone_setup(hass, freezer)
    hass.states.async_set(FINJA, "home", {"friendly_name": "Finja"})
    await hass.async_block_till_done()
    freezer.tick(timedelta(minutes=2))
    await _set(hass, DOOR, "on")
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    await _set(hass, DOOR, "off")
    await _set(hass, DOOR, "on")  # dieselbe Heimkehr lässt nicht noch einmal rein
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.PENDING


async def test_phone_too_early_or_short_away_does_not_let_in(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    await _phone_setup(hass, freezer)
    hass.states.async_set(FINJA, "home", {"friendly_name": "Finja"})
    await hass.async_block_till_done()
    freezer.tick(timedelta(minutes=6))  # Zeitfenster 5 Minuten vorbei
    await _set(hass, DOOR, "on")
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.PENDING
    await _key(hass, "home")  # mit PIN rein
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    await _set(hass, DOOR, "off")
    # Kurz weg (1 Minute) und zurück: zählt nicht als Heimkehr
    hass.states.async_set(FINJA, "not_home", {"friendly_name": "Finja", **FAR})
    await hass.async_block_till_done()
    freezer.tick(timedelta(minutes=1))
    hass.states.async_set(FINJA, "home", {"friendly_name": "Finja"})
    await hass.async_block_till_done()
    await _set(hass, DOOR, "on")
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.PENDING


async def test_return_passage_lets_in_without_passage_switch(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """„Bei Rückkehr: reinlassen“ (0.61) braucht den Durchgang selbst nicht eingeschaltet."""
    hass.states.async_set(FINJA, "not_home", {"friendly_name": "Finja", **FAR})
    options = _options(enabled=False)
    options["profiles"]["night"]["return"] = {"mode": "passage", "persons": [FINJA], "window": 5}
    async_mock_service(hass, "notify", PHONE)
    await setup_entry(hass, make_entry(options))
    await _arm_night(hass)
    freezer.tick(timedelta(minutes=6))
    await _set(hass, DOOR, "on")
    assert _panel(hass) == AlarmControlPanelState.PENDING
    hass.states.async_set(FINJA, "home", {"friendly_name": "Finja"})
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT


async def test_migration_passage_wins_and_explains(hass: HomeAssistant) -> None:
    """Waren „Unscharf bei Rückkehr“ und Handy-Reinlassen beide an, gewinnt reinlassen."""
    options = _options(persons=[FINJA], window=4)
    options["profiles"]["night"].update(auto_away_persons=[FINJA], auto_arrival_mode="door")
    entry = make_entry(options)
    await setup_entry(hass, entry)
    back = entry.options["profiles"]["night"]["return"]
    assert back == {
        "mode": "passage",
        "persons": [FINJA],
        "window": 4,
        "approach_delay": 0,
        "approach_valid": 15,
    }
    from homeassistant.components.persistent_notification import (  # noqa: PLC0415
        _async_get_or_create_notifications,
    )

    notes = _async_get_or_create_notifications(hass)
    assert any(key.startswith("hauswacht_return_") for key in notes)


# --- NFC-Aufkleber und Kartenleser (0.59.0b3) ------------------------------------------

STICKER = "AA-BB-CC"
CARD = "04A1B2C3"


async def _tag_setup(hass: HomeAssistant, user_id: str) -> None:
    options = _options()
    options["users"]["anna"].update({"ha_user": user_id, "tags": [CARD]})
    options["controls"].update(
        {
            "tuer": {
                "name": "Aufkleber Tür",
                "kind": "sticker",
                "tag": STICKER,
                "action": "passage",
            },
            "leser": {"name": "Leser", "kind": "reader", "device": "reader1", "action": "passage"},
        }
    )
    async_mock_service(hass, "notify", PHONE)
    await setup_entry(hass, make_entry(options))


async def test_sticker_passage(hass: HomeAssistant, hass_admin_user: MockUser) -> None:
    await _tag_setup(hass, hass_admin_user.id)
    await _arm_night(hass)
    hass.bus.async_fire(
        "tag_scanned",
        {"tag_id": "aa:bb:cc", "device_id": "x"},
        context=Context(user_id=hass_admin_user.id),
    )
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    assert _passage(hass)["direction"] == "out"


async def test_reader_passage_lets_in(hass: HomeAssistant, hass_admin_user: MockUser) -> None:
    await _tag_setup(hass, hass_admin_user.id)
    await _arm_night(hass)
    await _set(hass, DOOR, "on")
    hass.bus.async_fire("tag_scanned", {"tag_id": CARD, "device_id": "reader1"})
    await hass.async_block_till_done()
    assert _panel(hass) == AlarmControlPanelState.ARMED_NIGHT
    assert _passage(hass)["direction"] == "in"
