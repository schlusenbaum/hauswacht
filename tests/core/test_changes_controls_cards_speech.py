"""Einstellungsregeln: Bedienteile, Karten, Sprachausgabe, Melder aus Messwert, Sirenentöne."""

from __future__ import annotations

from typing import Any

from custom_components.hauswacht.core.changes.cards import add_card, edit_card
from custom_components.hauswacht.core.changes.controls import save_control
from custom_components.hauswacht.core.changes.sensors import (
    TARGET_ALWAYS,
    check_threshold_helper,
    place_new_sensor,
    save_always,
)
from custom_components.hauswacht.core.changes.sirens import (
    save_siren_test_settings,
    save_siren_tone,
)
from custom_components.hauswacht.core.changes.speech import (
    save_speech_event,
    save_speech_settings,
)
from custom_components.hauswacht.core.messages import default_speech
from custom_components.hauswacht.core.notify_events import NotifyEvent


def _options() -> dict[str, Any]:
    return {
        "areas": {"garage": {"name": "Garage"}},
        "profiles": {"away": {"name": "Abwesend"}, "g": {"name": "Garage", "area": "garage"}},
        "zones": {"keller": {"name": "Keller", "entities": []}},
        "users": {"anna": {"name": "Anna"}, "bob": {"name": "Bob"}},
        "sirens": ["siren.flur"],
    }


def test_controls() -> None:
    options = _options()
    reader = save_control(options, None, {"kind": "reader", "name": "Leser", "action": "arm"})
    assert reader.errors == {"device": "control_device", "profile": "control_profile_required"}
    wrong_area = save_control(
        options,
        None,
        {
            "kind": "sticker",
            "name": "Tür",
            "tag": "abc",
            "area": "main",
            "action": "arm",
            "profile": "g",
        },
    )
    assert wrong_area.errors == {"base": "control_profile_area"}
    button = save_control(
        options, None, {"kind": "button", "name": "Taster", "entity": "event.t", "presses": {}}
    )
    assert button.errors == {"base": "button_no_press"}
    ok = save_control(
        options,
        None,
        {
            "kind": "button",
            "name": "Taster",
            "entity": "event.t",
            "presses": {"single": "away", "x": "nix"},
        },
    )
    assert ok.options is not None
    assert ok.options["controls"][ok.item_id]["presses"] == {"single": "away"}
    assert save_control(options, "gibtsnicht", {"kind": "button"}).errors == {
        "base": "unknown_control"
    }


def test_cards() -> None:
    options = _options()
    assert add_card(options, {"card": "", "user": "anna"}).errors == {"card": "card_missing"}
    added = add_card(options, {"card": "04a1b2c3", "user": "anna", "name": "Blau"})
    assert added.options is not None
    tag = added.item_id
    assert tag
    assert added.options["users"]["anna"]["tags"] == [tag]
    taken = add_card(added.options, {"card": tag, "user": "bob"})
    assert taken.errors == {"card": "tag_taken"}
    assert taken.details["conflict"] == "Anna"
    moved = edit_card(added.options, tag, {"user": "bob", "active": False})
    assert moved.options is not None
    assert moved.options["users"]["anna"]["tags"] == []
    assert moved.options["users"]["bob"]["tags_disabled"] == [tag]
    deleted = edit_card(moved.options, tag, {"delete": True})
    assert deleted.options is not None
    assert deleted.options["users"]["bob"]["tags_disabled"] == []


def test_speech() -> None:
    options = _options()
    change = save_speech_settings(
        options, {"repeat": 5, "quiet_start": "25:00", "quiet_end": "6:5"}
    )
    assert change.options is not None
    speech = change.options["speech"]
    assert speech["repeat"] == 10  # Mindestwert
    assert speech["quiet"]["start"] == "22:00"  # ungültig -> Standard
    unchanged = save_speech_event(
        options,
        "alarm",
        {"enabled": True, "mode": "speak", "text": default_speech(NotifyEvent.ALARM)},
    )
    assert unchanged.options is not None
    assert unchanged.options["speech"]["events"]["alarm"]["text"] == ""
    assert save_speech_event(options, "alarm", {"mode": "laut"}).errors == {"mode": "invalid"}


def test_threshold_helper_and_placement() -> None:
    options = _options()
    errors, _ = check_threshold_helper(options, {"source": "sensor.t", "name": "Frost"})
    assert errors == {"base": "helper_no_limit"}
    errors, payload = check_threshold_helper(
        options, {"source": "sensor.t", "name": "Frost", "lower": "3", "target": "keller"}
    )
    assert errors == {}
    assert payload["lower"] == 3.0
    placed = place_new_sensor(options, "binary_sensor.frost", "technical", TARGET_ALWAYS)
    assert placed.options is not None
    assert placed.options["always_active"]["sensors"] == ["binary_sensor.frost"]
    assert placed.options["sensor_types"]["binary_sensor.frost"] == "technical"


def test_siren_tone_and_always_sirens() -> None:
    options = _options()
    assert save_siren_tone(options, "siren.flur", "fire", smoke_detector=True).errors == {
        "tone": "siren_tone_fire_detector"
    }
    auto = save_siren_tone(options, "siren.flur", "_auto")
    assert auto.options is not None
    assert auto.options["siren_tones"] == {}
    assert save_siren_test_settings(options, 5, False).errors == {"reminder_months": "invalid"}
    always = save_always(
        options,
        zones=[],
        sensors=[],
        sirens={
            "sirens_enabled": True,
            "sirens": ["siren.flur", "siren.fremd"],
            "siren_tone": "fire",
        },
    )
    assert always.options is not None
    stored = always.options["always_active"]
    assert stored["sirens"] == ["siren.flur"]
    assert stored["siren_tone"] == "burglar"
