"""Konfiguration herunterladen (ADR 0019): Platzhalter statt echter Namen und Geheimnisse."""

from __future__ import annotations

import json
import re

from custom_components.hauswacht.core.export import HIDDEN, pseudonymize

PERSONS = {"person.anna": "Anna", "person.ben": "Ben Beispiel"}

DATA = {
    "homecoming_persons": ["person.anna", "person.ben"],
    "homecoming_signals": {
        "person.anna": ["sensor.handy_von_anna", "device_tracker.annas_iphone"],
        "person.ben": ["device_tracker.ben_handy"],
    },
    "users": {
        "u1": {
            "name": "Clara Muster",
            "pin_digest": "abc123",
            "pin_salt": "salz",
            "tags": ["04AABBCC"],
            "tag_names": {"04AABBCC": "Claras Schlüssel"},
            "ha_user": "deadbeefcafe",
        },
    },
    "notify_system": ["notify.mobile_app_anna_iphone"],
    "homecoming_ssids": ["FritzBox Muster"],
    "action_codes": {"codes": [{"id": "a", "name": "Nacht", "code": "4711", "key": "arm_night"}]},
    "profiles": {
        "night": {"name": "Annas Zimmer", "alarm_targets": ["notify.mobile_app_anna_iphone"]}
    },
    "findings": [
        {"code": "away_never", "text": "Anna kann nie als weg erkannt werden; Clara auch."}
    ],
    "controls": [{"topic": "zigbee2mqtt/flur", "device": "abcd1234ef"}],
    "overview": {"users": [{"name": "Clara Muster", "pin": True, "cards": ["Claras Schlüssel"]}]},
    "zones": {"aussen": ["binary_sensor.haustuer"]},
}

SECRETS = (
    "anna",
    "Ben",
    "Beispiel",
    "Clara",
    "Muster",
    "abc123",
    "salz",
    "04AABBCC",
    "deadbeefcafe",
    "mobile_app",
    "FritzBox",
    "4711",
    "zigbee2mqtt/flur",
    "abcd1234ef",
)


def test_no_real_value_remains() -> None:
    text = json.dumps(pseudonymize(DATA, PERSONS), ensure_ascii=False)
    for secret in SECRETS:
        # als ganzes Wort („Ben“ darf in „Benutzer“ stecken)
        found = re.search(rf"(?<![^\W\d_]){re.escape(secret)}(?![^\W\d_])", text, re.I)
        assert found is None, secret


def test_same_person_same_placeholder_everywhere() -> None:
    out = pseudonymize(DATA, PERSONS)
    assert out["homecoming_persons"] == ["person.person_1", "person.person_2"]
    assert out["homecoming_signals"]["person.person_1"] == [
        "sensor.handy_von_person_1",
        "device_tracker.person_1s_iphone",
    ]
    assert out["homecoming_signals"]["person.person_2"] == ["device_tracker.person_2_handy"]
    assert out["profiles"]["night"]["name"] == "Person 1s Zimmer"
    assert out["findings"][0]["text"].startswith("Person 1 kann nie")
    # Empfänger: gleicher Wert, gleicher Platzhalter, Domäne bleibt
    assert out["notify_system"] == ["notify.empfaenger_1"]
    assert out["profiles"]["night"]["alarm_targets"] == ["notify.empfaenger_1"]


def test_secrets_become_dummies_structure_stays() -> None:
    out = pseudonymize(DATA, PERSONS)
    user = out["users"]["benutzer_1"]
    assert user["name"] == "Benutzer 1"
    assert user["pin_digest"] == HIDDEN
    assert user["pin_salt"] == HIDDEN
    assert user["tags"] == ["karte_1"]
    assert user["tag_names"] == {"karte_1": "Kartenname 1"}
    assert user["ha_user"] == "konto_1"
    assert out["action_codes"]["codes"][0] == {
        "id": "a",
        "name": "Nacht",
        "code": HIDDEN,
        "key": "arm_night",
    }
    assert out["homecoming_ssids"] == ["wlan_1"]
    assert out["controls"] == [{"topic": "topic_1", "device": "geraet_1"}]
    # Wahrheitswerte bleiben („PIN vorhanden“), Fachbegriffe bleiben
    assert out["overview"]["users"][0]["pin"] is True
    assert out["overview"]["users"][0]["name"] == "Benutzer 1"
    assert out["findings"][0]["code"] == "away_never"
    assert out["zones"] == {"aussen": ["binary_sensor.haustuer"]}


def test_names_only_as_whole_words() -> None:
    out = pseudonymize({"a": "Abend bei Benjamin", "b": "Ben kommt"}, {"person.ben": "Ben"})
    assert out == {"a": "Abend bei Benjamin", "b": "Person 1 kommt"}


def test_persons_not_in_home_assistant_are_replaced_too() -> None:
    out = pseudonymize({"persons": ["person.unbekannt"], "x": "siehe person.unbekannt"})
    assert out == {"persons": ["person.person_1"], "x": "siehe person.person_1"}
