"""Tests: eigene Texte (Platzhalter) und Sprachausgabe-Einstellungen."""

from __future__ import annotations

from datetime import time

import pytest

from custom_components.hauswacht.core.messages import (
    TemplateError,
    check_template,
    default_speech,
    placeholder_names,
    render,
)
from custom_components.hauswacht.core.notify_events import NotifyEvent
from custom_components.hauswacht.core.speech import (
    Candidate,
    in_quiet_hours,
    parse_speech,
    pick_entity,
    profile_speakers,
    speakers_for,
)


def test_render_fills_and_tidies() -> None:
    assert render("Alarm {bereich} durch {melder} .", {"melder": "Fenster"}) == (
        "Alarm durch Fenster."
    )
    assert render("{text}", {"text": "Standard"}) == "Standard"


@pytest.mark.parametrize(
    "template",
    ["{unbekannt}", "{melder:>10}", "{melder!r}", "offen {", "x" * 501],
)
def test_check_template_rejects(template: str) -> None:
    with pytest.raises(TemplateError):
        check_template(template)


def test_broken_template_falls_back_to_text() -> None:
    assert render("{kaputt}", {"text": "Standard"}) == "Standard"


def test_every_event_has_valid_default_speech() -> None:
    for event in NotifyEvent:
        check_template(default_speech(event))
        check_template(default_speech(event, german=False))


def test_parse_speech_defaults() -> None:
    config = parse_speech({})
    assert config.speakers == ()
    assert config.repeat == 0
    assert config.events[NotifyEvent.ALARM].enabled
    assert config.events[NotifyEvent.ALARM].mode == "announce"
    assert not config.events[NotifyEvent.ARMED].enabled
    assert config.events[NotifyEvent.ALARM].in_quiet
    assert not config.events[NotifyEvent.ARM_FAILED].in_quiet


def test_repeat_bounds() -> None:
    assert parse_speech({"speech": {"repeat": 3}}).repeat == 10
    assert parse_speech({"speech": {"repeat": 9999}}).repeat == 300
    assert parse_speech({"speech": {"repeat": "x"}}).repeat == 0


def test_quiet_hours_over_midnight() -> None:
    config = parse_speech(
        {"speech": {"quiet": {"enabled": True, "start": "22:00", "end": "07:00"}}}
    )
    assert in_quiet_hours(config, time(23, 0))
    assert in_quiet_hours(config, time(6, 59))
    assert not in_quiet_hours(config, time(7, 0))
    assert not in_quiet_hours(parse_speech({}), time(23, 0))


def test_speakers_for_quiet_and_profile() -> None:
    options = {
        "speech": {
            "speakers": ["d1"],
            "quiet": {"enabled": True, "start": "22:00", "end": "07:00"},
            "events": {"armed": {"enabled": True}, "fault": {"enabled": True, "speakers": ["d3"]}},
        }
    }
    config = parse_speech(options)
    night, day = time(23, 0), time(12, 0)
    assert speakers_for(config, NotifyEvent.ARMED, now=night) == ()
    assert speakers_for(config, NotifyEvent.ARMED, now=day) == ("d1",)
    assert speakers_for(config, NotifyEvent.ALARM, now=night, profile_speakers=["d2"]) == ("d2",)
    assert speakers_for(config, NotifyEvent.ARMED, now=day, profile_speakers=["d2"]) == ("d1",)
    assert speakers_for(config, NotifyEvent.FAULT, now=day) == ("d3",)
    assert speakers_for(config, NotifyEvent.DISARMED, now=day) == ()


def test_pick_entity_by_mode() -> None:
    echo = [
        Candidate("notify.echo_sprechen", "X-speak"),
        Candidate("notify.echo_durchsagen", "X-announce"),
    ]
    assert pick_entity(echo, "announce") == "notify.echo_durchsagen"
    assert pick_entity(echo, "speak") == "notify.echo_sprechen"
    single = [Candidate("notify.wohnung_durchsagen", "G-announce")]
    assert pick_entity(single, "speak") == "notify.wohnung_durchsagen"
    assert pick_entity([Candidate("notify.handy", "abc", "speak")], "speak") == "notify.handy"
    assert pick_entity([], "speak") is None


def test_profile_speakers() -> None:
    options = {"profiles": {"p": {"speakers": ["d1", "d1", 3]}}}
    assert profile_speakers(options, "p") == ("d1",)
    assert profile_speakers(options, "x") == ()
    assert profile_speakers(options, None) == ()


# --- 0.39: englische Platzhalter ------------------------------------------------------


def test_english_placeholder_names_work_everywhere() -> None:
    check_template("Alarm: {sensor} ({profile}) by {who}")
    check_template("Alarm: {melder} ({profile})")  # gemischt geht auch
    values = {"melder": "Haustür", "profil": "Nacht", "wer": "Anna"}
    assert (
        render("Alarm: {sensor} ({profile}) by {who}", values) == "Alarm: Haustür (Nacht) by Anna"
    )
    assert render("Alarm: {melder}", values) == "Alarm: Haustür"
    assert "{sensor}" not in "".join(placeholder_names("de"))
    assert placeholder_names("en")[:3] == ("area", "profile", "sensor")


def test_template_errors_in_english() -> None:
    with pytest.raises(TemplateError, match="unknown placeholder"):
        check_template("{foo}", "en")
    with pytest.raises(TemplateError, match="unbekannter Platzhalter"):
        check_template("{foo}")
