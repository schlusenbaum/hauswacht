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


def test_replace_targets_swaps_app_entities() -> None:
    from custom_components.hauswacht.core.notify_events import replace_targets  # noqa: PLC0415

    aliases = {"notify.xiaomi_13": "mobile_app_xiaomi13"}
    options = {
        "notify_system": ["notify.xiaomi_13", "mobile_app_xiaomi13", "notify.telegram"],
        "duress_notify": ["notify.xiaomi_13"],
        "events": {"alarm": {"enabled": True, "targets": ["notify.xiaomi_13"]}, "armed": {}},
        "profiles": {"night": {"name": "Nacht", "notify": ["notify.xiaomi_13"]}},
    }
    new = replace_targets(options, aliases)
    assert new is not None
    assert new["notify_system"] == ["mobile_app_xiaomi13", "notify.telegram"]
    assert new["duress_notify"] == ["mobile_app_xiaomi13"]
    assert new["events"]["alarm"]["targets"] == ["mobile_app_xiaomi13"]
    assert new["events"]["armed"] == {}
    assert new["profiles"]["night"]["notify"] == ["mobile_app_xiaomi13"]
    assert replace_targets(new, aliases) is None  # nichts mehr zu tun
    assert replace_targets(options, {}) is None
