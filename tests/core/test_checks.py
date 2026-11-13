"""Prüfhinweise auf der Anlagenübersicht."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from custom_components.hauswacht.core.checks import run_checks

NOW = datetime(2026, 11, 13, 9, 0, tzinfo=UTC)


def _overview(**changes: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "system": {"test_mode": False, "sirens_enabled": True},
        "profiles": [
            {
                "name": "Nacht",
                "zones": ["Außen"],
                "rules": [],
                "sirens": ["Sirene Flur"],
                "silent": False,
                "alarm_targets": ["handy"],
            }
        ],
        "sensors": [
            {
                "entity_id": "binary_sensor.tuer",
                "name": "Haustür",
                "zone": "Außen",
                "type": "door",
                "state": "closed",
                "last_contact": NOW.isoformat(),
                "battery": 80,
                "always_active": False,
                "profiles": {"night": "armed"},
            }
        ],
        "rules": [],
        "sirens": [
            {
                "entity_id": "siren.flur",
                "name": "Sirene Flur",
                "last_test": (NOW - timedelta(days=10)).isoformat(),
                "heard": True,
            }
        ],
        "users": [],
        "pin_rules": {"any_pin": False},
        "notifications": {"duress_targets": 0},
        "monitoring": {
            "stale_after_hours": 6,
            "recommended_hours": 3,
            "infrastructure": [{"name": "Zigbee2MQTT", "ok": True}],
        },
    }
    base.update(changes)
    return base


def _codes(findings: list[dict[str, Any]]) -> list[str]:
    return [f["code"] for f in findings]


def test_clean_configuration_has_no_findings() -> None:
    assert run_checks(_overview(), now=NOW) == []


def test_profile_reaching_nobody_is_important() -> None:
    profile = {"name": "Urlaub", "zones": ["Außen"], "rules": [], "sirens": [], "alarm_targets": []}
    findings = run_checks(_overview(profiles=[profile]), now=NOW)
    assert findings[0]["code"] == "profile_unheard"
    assert findings[0]["important"] is True
    assert "Urlaub" in findings[0]["text"]


def test_silent_profile_with_recipients_is_only_info() -> None:
    profile = {
        "name": "Nacht",
        "zones": ["Außen"],
        "rules": [],
        "sirens": ["Sirene"],
        "silent": True,
        "alarm_targets": ["handy"],
    }
    findings = run_checks(_overview(profiles=[profile]), now=NOW)
    assert _codes(findings) == ["profile_no_siren"]
    assert findings[0]["severity"] == "info"


def test_sensor_in_group_but_armed_nowhere() -> None:
    sensor = {
        "entity_id": "binary_sensor.wc",
        "name": "Fenster WC",
        "zone": "Außen",
        "type": "window",
        "state": "closed",
        "profiles": {"night": "excluded"},
    }
    findings = run_checks(_overview(sensors=[sensor]), now=NOW)
    assert _codes(findings) == ["sensor_unused"]


def test_sensor_only_in_rule_or_technical_is_fine() -> None:
    in_rule = {
        "entity_id": "binary_sensor.keller",
        "name": "Keller",
        "zone": "Keller",
        "type": "motion",
        "state": "closed",
        "profiles": {"night": "rule"},
    }
    technical = {
        "entity_id": "binary_sensor.frost",
        "name": "Frost",
        "zone": "Technik",
        "type": "technical",
        "state": "closed",
        "profiles": {},
    }
    assert run_checks(_overview(sensors=[in_rule, technical]), now=NOW) == []


def test_unavailable_sensor_becomes_important_after_a_day() -> None:
    def sensor(hours: int) -> dict[str, Any]:
        return {
            "entity_id": "binary_sensor.tuer",
            "name": "Haustür",
            "zone": "Außen",
            "type": "door",
            "state": "unavailable",
            "last_contact": (NOW - timedelta(hours=hours)).isoformat(),
            "profiles": {"night": "armed"},
        }

    short = run_checks(_overview(sensors=[sensor(2)]), now=NOW)
    assert _codes(short) == ["sensor_unavailable"]
    assert not short[0]["important"]
    assert "seit 2 h" in short[0]["text"]
    long = run_checks(_overview(sensors=[sensor(30)]), now=NOW)
    assert long[0]["important"]


def test_battery_low() -> None:
    sensor = dict(_overview()["sensors"][0], battery=7)
    assert _codes(run_checks(_overview(sensors=[sensor]), now=NOW)) == ["battery_low"]


def test_siren_tests() -> None:
    never = {"entity_id": "siren.a", "name": "A", "last_test": None}
    old = {
        "entity_id": "siren.b",
        "name": "B",
        "last_test": (NOW - timedelta(days=200)).isoformat(),
    }
    silent = {"entity_id": "siren.c", "name": "C", "last_test": NOW.isoformat(), "heard": False}
    codes = _codes(run_checks(_overview(sirens=[never, old, silent]), now=NOW))
    assert sorted(codes) == ["siren_not_heard", "siren_test_old", "siren_untested"]


def test_duress_pin_without_recipients_never_names_the_user() -> None:
    users = [{"name": "Petra", "pin": True, "active": True}]
    findings = run_checks(_overview(users=users), duress_configured=True, now=NOW)
    assert findings[0]["code"] == "duress_no_targets"
    assert findings[0]["important"]
    assert "Petra" not in findings[0]["text"]
    with_targets = _overview(users=users, notifications={"duress_targets": 1})
    assert run_checks(with_targets, duress_configured=True, now=NOW) == []


def test_users_without_pin_and_expired_guests() -> None:
    users = [
        {"name": "Christian", "pin": True, "active": True},
        {"name": "Petra", "pin": False, "active": True},
        {"name": "Gast", "pin": False, "active": True, "expired": True},
    ]
    findings = run_checks(_overview(users=users, pin_rules={"any_pin": True}), now=NOW)
    assert sorted(_codes(findings)) == ["user_expired", "user_without_pin"]


def test_monitoring_hints() -> None:
    off = _overview(
        monitoring={"stale_after_hours": 0, "recommended_hours": 4, "infrastructure": []}
    )
    findings = run_checks(off, now=NOW)
    assert sorted(_codes(findings)) == ["no_infrastructure", "silence_off"]
    assert "Empfehlung: 4 h" in findings[[f["code"] for f in findings].index("silence_off")]["text"]
    tight = _overview(
        monitoring={
            "stale_after_hours": 2,
            "recommended_hours": 6,
            "infrastructure": [{"name": "Z2M", "ok": False}],
        }
    )
    assert sorted(_codes(run_checks(tight, now=NOW))) == ["infrastructure_fault", "silence_tight"]


def test_system_and_rules() -> None:
    overview = _overview(
        system={"test_mode": True, "sirens_enabled": False},
        rules=[{"name": "Tür, dann Keller", "profiles": []}],
    )
    assert sorted(_codes(run_checks(overview, now=NOW))) == [
        "rule_unused",
        "sirens_locked",
        "test_mode",
    ]


def test_english_and_order() -> None:
    profile = {"name": "Away", "zones": [], "rules": [], "sirens": [], "alarm_targets": []}
    findings = run_checks(
        _overview(profiles=[profile], rules=[{"name": "R", "profiles": []}]), "en", now=NOW
    )
    assert findings[0]["code"] == "profile_unheard"  # wichtig zuerst
    assert findings[-1]["severity"] == "info"
    assert findings[0]["text"].startswith("Profile Away")
