"""Tests: Benachrichtigungen pro Ereignis."""

from __future__ import annotations

from custom_components.hauswacht.core.notify_events import (
    CRITICAL_DATA,
    NORMAL_DATA,
    NotifyEvent,
    enabled,
    push_data,
    route,
)

SYSTEM = ["notify.alle"]


def test_defaults() -> None:
    assert route({}, NotifyEvent.ALARM, system_targets=SYSTEM) == ("notify.alle",)
    assert route({}, NotifyEvent.ARMED, system_targets=SYSTEM) == ()  # standardmäßig aus
    assert route({}, NotifyEvent.FAULT, system_targets=SYSTEM) == ("notify.alle",)


def test_entry_follows_push_button_unless_set() -> None:
    assert not enabled({}, NotifyEvent.ENTRY, push_disarm=False)
    assert enabled({}, NotifyEvent.ENTRY, push_disarm=True)
    options = {"events": {"entry": {"enabled": True}}}
    assert enabled(options, NotifyEvent.ENTRY, push_disarm=False)


def test_profile_targets_first_for_alarm() -> None:
    options = {"events": {"alarm": {"targets": ["notify.event"]}}}
    assert route(
        options, NotifyEvent.ALARM, system_targets=SYSTEM, profile_targets=["notify.profil"]
    ) == ("notify.profil",)
    assert route(options, NotifyEvent.ALARM, system_targets=SYSTEM) == ("notify.event",)
    # Profil-Empfänger gelten nur für Alarm und Tür
    assert route(
        {}, NotifyEvent.FAULT, system_targets=SYSTEM, profile_targets=["notify.profil"]
    ) == ("notify.alle",)


def test_switch_off_and_own_targets() -> None:
    options = {
        "events": {
            "alarm_ended": {"enabled": False},
            "armed": {"enabled": True, "targets": ["notify.a", "notify.a", 3]},
        }
    }
    assert route(options, NotifyEvent.ALARM_ENDED, system_targets=SYSTEM) == ()
    assert route(options, NotifyEvent.ARMED, system_targets=SYSTEM) == ("notify.a",)


def test_broken_options_fall_back() -> None:
    options = {"events": {"fault": "kaputt"}}
    assert route(options, NotifyEvent.FAULT, system_targets=SYSTEM) == ("notify.alle",)
    assert route({"events": "x"}, NotifyEvent.FAULT, system_targets=SYSTEM) == ("notify.alle",)


def test_critical_data() -> None:
    assert push_data(NotifyEvent.ALARM, critical_allowed=True) is CRITICAL_DATA
    assert push_data(None, critical_allowed=True) is CRITICAL_DATA  # Bedrohung
    assert push_data(NotifyEvent.ALARM, critical_allowed=False) is NORMAL_DATA
    assert push_data(NotifyEvent.FAULT, critical_allowed=True) is NORMAL_DATA
