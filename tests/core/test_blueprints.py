"""Blueprints im Repo: gekennzeichnet und versioniert (ADR 0012).

Ob Home Assistant sie lesen und ausführen kann, prüfen die Integrationstests.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2] / "blueprints"
BLUEPRINTS = sorted((ROOT / "automation" / "hauswacht").glob("*.yaml"))


def test_there_are_blueprints() -> None:
    assert BLUEPRINTS


@pytest.mark.parametrize("path", BLUEPRINTS, ids=lambda p: p.name)
def test_blueprint_is_marked_and_versioned(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert "UNGETESTET" in text
    assert f"blueprints/automation/hauswacht/{path.name}" in text  # source_url
    version = re.search(r"^  blueprint_version: (\d+)$", text, re.MULTILINE)
    assert version is not None
    assert f"Version {version.group(1)}." in text  # steht auch in der Beschreibung
    assert "hauswacht.keypad_input" in text


def test_esphome_example_is_marked() -> None:
    text = (ROOT / "esphome" / "hauswacht_keypad.yaml").read_text(encoding="utf-8")
    assert "UNGETESTET" in text
    assert "hauswacht.keypad_input" in text
