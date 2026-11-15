"""Übersetzungen ohne spitze Klammern.

Home Assistant liest Texte als ICU-Nachrichten: ``<Topic>`` gilt dort als HTML-Tag und das
Formular zeigt statt der Beschreibung "Translation error: UNCLOSED_TAG".
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

TRANSLATIONS = Path(__file__).parents[2] / "custom_components" / "hauswacht" / "translations"


def _strings(node: Any, path: str = "") -> list[tuple[str, str]]:
    if isinstance(node, dict):
        return [item for key, value in node.items() for item in _strings(value, f"{path}/{key}")]
    return [(path, node)] if isinstance(node, str) else []


@pytest.mark.parametrize("language", ["de", "en"])
def test_no_angle_brackets(language: str) -> None:
    data = json.loads((TRANSLATIONS / f"{language}.json").read_text(encoding="utf-8"))
    bad = [(path, text) for path, text in _strings(data) if re.search(r"[<>]", text)]
    assert bad == []
