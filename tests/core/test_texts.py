"""Texte für Benachrichtigungen: beide Sprachen vollständig und gleich aufgebaut."""

from __future__ import annotations

import string

from custom_components.hauswacht.core.homecoming import csv_header, to_csv
from custom_components.hauswacht.core.reactions import alarm_message, invalid_code_message
from custom_components.hauswacht.core.texts import DE, EN, TEXTS, by, lang_of, tr


def _fields(text: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


def test_same_keys_and_placeholders_in_both_languages() -> None:
    assert set(TEXTS[DE]) == set(TEXTS[EN])
    for key in TEXTS[DE]:
        assert _fields(TEXTS[DE][key]) == _fields(TEXTS[EN][key]), key


def test_language_follows_home_assistant() -> None:
    assert lang_of("de") == DE
    assert lang_of("de-CH") == DE
    assert lang_of("en") == EN
    assert lang_of("fr") == EN
    assert lang_of(None) == EN


def test_messages_in_both_languages() -> None:
    assert alarm_message("Nacht", "Haustür", test_mode=False) == (
        "Hauswacht: EINBRUCHALARM",
        "EINBRUCHALARM – ausgelöst durch Haustür (Profil Nacht).",
    )
    title, text = alarm_message("Night", "Front door", test_mode=True, lang=EN)
    assert title == "Hauswacht: TEST ALARM"
    assert text == "TEST ALARM – triggered by Front door (profile Night)."
    assert invalid_code_message(3, 60, EN)[1] == (
        "3 wrong PIN entries in a row. PIN entry is locked for 60 seconds."
    )
    assert tr(EN, "armed", profile="Night", by=by(EN, "Anna")) == "Profile Night armed by Anna."
    assert tr(DE, "disarmed", by=by(DE, None)) == "Unscharf geschaltet."


def test_csv_language() -> None:
    assert csv_header(EN)[0] == "Kind"
    assert to_csv([csv_header(EN)], delimiter=",").startswith("﻿Kind,Time,")
