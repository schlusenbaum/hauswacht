"""Einstellungsregeln: Sirenen, Empfänger, Benutzer und PINs."""

from __future__ import annotations

from typing import Any

from custom_components.hauswacht.core.changes.notifications import (
    save_event_text,
    save_notify_settings,
    set_general_recipients,
)
from custom_components.hauswacht.core.changes.sirens import save_sirens
from custom_components.hauswacht.core.changes.users import (
    delete_user,
    save_user,
    set_area_rights,
    set_pins,
    unique_user_id,
)
from custom_components.hauswacht.core.pin import PinHash, hash_pin, verify_pin

# --- Sirenen ---------------------------------------------------------------


def _siren_options() -> dict[str, Any]:
    return {
        "sirens": ["siren.flur", "siren.garten"],
        "sirens_hardware_enabled": False,
        "siren_tones": {"siren.flur": "alarm", "siren.garten": "alarm"},
        "siren_fire_tone_ok": ["siren.garten"],
        "profiles": {"night": {"sirens": ["siren.flur", "siren.garten"]}},
    }


def test_release_needs_confirmation() -> None:
    change = save_sirens(_siren_options(), {"sirens_hardware_enabled": True})
    assert change.errors == {"base": "confirm_hardware_required"}
    confirmed = save_sirens(
        _siren_options(), {"sirens_hardware_enabled": True, "confirm_hardware": True}
    )
    assert confirmed.options is not None
    assert confirmed.options["sirens_hardware_enabled"] is True


def test_assistant_only_sirens_keeps_release() -> None:
    options = {**_siren_options(), "sirens_hardware_enabled": True}
    change = save_sirens(options, {"sirens": ["siren.flur"]})
    assert change.options is not None
    assert change.options["sirens_hardware_enabled"] is True


def test_removed_siren_is_cleaned_everywhere() -> None:
    change = save_sirens(_siren_options(), {"sirens": ["siren.flur", "siren.flur"]})
    assert change.options is not None
    assert change.options["sirens"] == ["siren.flur"]
    assert change.options["siren_tones"] == {"siren.flur": "alarm"}
    assert change.options["siren_fire_tone_ok"] == []
    assert change.options["profiles"]["night"]["sirens"] == ["siren.flur"]


def test_switches_only_with_expert_option() -> None:
    data = {"sirens": ["siren.flur", "switch.relais"]}
    plain = save_sirens(_siren_options(), data)
    assert plain.options is not None
    assert plain.options["sirens"] == ["siren.flur"]
    expert = save_sirens(_siren_options(), {**data, "sirens_allow_switch": True})
    assert expert.options is not None
    assert expert.options["sirens"] == ["siren.flur", "switch.relais"]


# --- Empfänger ---------------------------------------------------------------


def test_general_recipients_without_duplicates() -> None:
    change = set_general_recipients({}, ["mobile_app_a", "mobile_app_b", "mobile_app_a"])
    assert change.options == {"notify_system": ["mobile_app_a", "mobile_app_b"]}


def test_notify_settings_keep_own_texts() -> None:
    options = {
        "events": {
            "alarm": {"enabled": True, "targets": [], "title": "Eigener Titel"},
            "armed": {"enabled": False},
        },
        "reminder_profile": "night",
    }
    data = {
        "notify_system": ["mobile_app_a"],
        "event_alarm": {"enabled": True, "targets": ["mobile_app_b"]},
        "reminder": {"reminder_persons": ["person.anna"]},
    }
    change = save_notify_settings(options, data)
    assert change.options is not None
    events = change.options["events"]
    assert events["alarm"] == {
        "enabled": True,
        "targets": ["mobile_app_b"],
        "title": "Eigener Titel",
    }
    assert events["armed"] == {"enabled": False}
    assert change.options["critical_alerts"] is True
    assert change.options["reminder_delay"] == 15
    assert "reminder_profile" not in change.options


def test_event_text_saved_checked_and_cleared() -> None:
    options = {"events": {"armed": {"enabled": True, "targets": ["notify.a"]}}}
    change = save_event_text(options, "armed", " Scharf ", "{profil} ist scharf ({who})")
    assert change.ok
    assert change.options is not None
    stored = change.options["events"]["armed"]
    assert stored == {
        "enabled": True,
        "targets": ["notify.a"],
        "title": "Scharf",
        "message": "{profil} ist scharf ({who})",
    }
    assert options["events"]["armed"] == {"enabled": True, "targets": ["notify.a"]}
    # Leer = wieder der Text von Hauswacht
    cleared = save_event_text(change.options, "armed", "", "")
    assert cleared.options is not None
    assert cleared.options["events"]["armed"] == {"enabled": True, "targets": ["notify.a"]}


def test_event_text_errors() -> None:
    bad = save_event_text({}, "armed", "", "{foo} da", lang="en")
    assert bad.errors == {"message": "invalid_template"}
    assert "{foo}" in bad.details["message"]
    assert save_event_text({}, "nope", "", "").errors == {"event": "unknown_event"}


# --- Benutzer ---------------------------------------------------------------


def _users() -> dict[str, Any]:
    pin = hash_pin("1357")
    duress = hash_pin("9999")
    return {
        "users": {
            "anna": {
                "name": "Anna",
                "pin_salt": pin.salt,
                "pin_digest": pin.digest,
                "duress_salt": duress.salt,
                "duress_digest": duress.digest,
                "tags": ["04A1"],
            }
        },
        "action_codes": {"licht": {"name": "Licht", "code": "7777", "key": "arm_day_zones"}},
    }


def test_new_user_and_unique_id() -> None:
    change = save_user(
        _users(), None, {"name": "Bernd", "valid_until": "2026-12-01T00:00:00+01:00"}
    )
    assert change.item_id == "bernd"
    assert change.options is not None
    stored = change.options["users"]["bernd"]
    assert stored["can_force_arm"] is True
    assert stored["rights"] == "all"
    assert stored["valid_until"] == "2026-12-01T00:00:00+01:00"
    assert unique_user_id("Anna", {"anna": {}}) == "anna_2"


def test_user_name_rules_and_edit_keeps_credentials() -> None:
    assert save_user(_users(), None, {"name": "anna"}).errors == {"name": "user_name_taken"}
    assert save_user(_users(), None, {"name": "  "}).errors == {"name": "user_name_required"}
    change = save_user(_users(), "anna", {"name": "Anna", "can_force_arm": False}, ha_user="x")
    assert change.options is not None
    stored = change.options["users"]["anna"]
    assert stored["tags"] == ["04A1"]
    assert "pin_digest" in stored
    assert stored["ha_user"] == "x"
    assert stored["can_force_arm"] is False


def test_area_rights_and_back_to_all() -> None:
    change = set_area_rights(_users(), "anna", {"haus": ["arm", "unbekannt"], "wohnung": []})
    assert change.options is not None
    stored = change.options["users"]["anna"]
    assert stored["rights"] == "per_area"
    assert stored["area_rights"] == {"haus": ["arm"], "wohnung": []}
    back = save_user(change.options, "anna", {"name": "Anna", "rights": "all"})
    assert back.options is not None
    assert "area_rights" not in back.options["users"]["anna"]


def test_delete_user() -> None:
    change = delete_user(_users(), "anna")
    assert change.options is not None
    assert change.options["users"] == {}


def test_pin_rules() -> None:
    def errors(**data: Any) -> dict[str, str]:
        return dict(set_pins(_users(), "anna", data).errors)

    assert errors(new_pin="12") == {"new_pin": "invalid_pin"}
    assert errors(new_pin="2468", new_duress_pin="2468") == {"new_duress_pin": "duress_equals_pin"}
    assert errors(new_pin="7777") == {"new_pin": "pin_is_action_code"}
    assert errors(new_pin="9999") == {"new_pin": "pin_is_duress"}
    other = save_user(_users(), None, {"name": "Bernd"}).options
    assert other is not None
    clash = set_pins(other, "bernd", {"new_duress_pin": "1357"})
    assert clash.errors == {"new_duress_pin": "duress_conflict"}
    assert clash.details["conflict"] == "Anna"


def test_set_and_remove_pins() -> None:
    change = set_pins(_users(), "anna", {"new_pin": "2468", "remove_duress_pin": True})
    assert change.options is not None
    stored = change.options["users"]["anna"]
    assert "duress_digest" not in stored
    assert verify_pin("2468", PinHash(stored["pin_salt"], stored["pin_digest"]))
    removed = set_pins(change.options, "anna", {"remove_pin": True})
    assert removed.options is not None
    assert "pin_digest" not in removed.options["users"]["anna"]
