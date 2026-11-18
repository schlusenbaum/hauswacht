"""Standardtexte als Vorlage für eigene Texte (Einstellungsseite)."""

from __future__ import annotations

import pytest

from custom_components.hauswacht.core.changes.notifications import save_event_text
from custom_components.hauswacht.core.default_texts import (
    FULL_TEXT,
    default_message,
    default_title,
    is_default,
)
from custom_components.hauswacht.core.messages import (
    EXAMPLE_VALUES_DE,
    check_template,
    render,
)
from custom_components.hauswacht.core.notify_events import NotifyEvent


@pytest.mark.parametrize("lang", ["de", "en"])
def test_every_template_is_valid(lang: str) -> None:
    for event in NotifyEvent:
        check_template(default_title(event, lang), lang)
        check_template(default_message(event, lang), lang)


def test_templates_match_hauswacht_texts() -> None:
    assert default_title(NotifyEvent.ARMED) == "Hauswacht: scharf"
    armed = default_message(NotifyEvent.ARMED)
    assert render(armed, EXAMPLE_VALUES_DE) == "Profil Abwesend scharf geschaltet (Christian)."
    # Ohne bekannte Person keine leeren Klammern
    assert render(armed, {**EXAMPLE_VALUES_DE, "wer": ""}) == "Profil Abwesend scharf geschaltet."
    assert "{sensor}" in default_message(NotifyEvent.ALARM, "en")
    # Wechselnde Texte: der vollständige Text von Hauswacht
    assert default_message(NotifyEvent.FAULT) == FULL_TEXT
    assert default_title(NotifyEvent.SYSTEM) == FULL_TEXT


def test_unchanged_template_saves_nothing() -> None:
    assert is_default(NotifyEvent.ARMED, "title", " Hauswacht: scharf ")
    assert not is_default(NotifyEvent.ARMED, "title", "Scharf!")
    options = {"events": {"armed": {"enabled": True, "title": "Alt", "message": "Alt"}}}
    change = save_event_text(
        options,
        "armed",
        default_title(NotifyEvent.ARMED),
        default_message(NotifyEvent.ARMED),
    )
    assert change.options is not None
    assert change.options["events"]["armed"] == {"enabled": True}
    # Nur der Text geändert: der Titel bleibt der von Hauswacht
    change = save_event_text(options, "armed", default_title(NotifyEvent.ARMED), "{profil} an")
    assert change.options is not None
    assert change.options["events"]["armed"] == {"enabled": True, "message": "{profil} an"}
