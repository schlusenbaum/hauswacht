"""Die Versionsangaben in README und Anleitung müssen zur Integration passen."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _manifest_version() -> str:
    manifest = ROOT / "custom_components" / "hauswacht" / "manifest.json"
    return str(json.loads(manifest.read_text(encoding="utf-8"))["version"])


def test_pyproject_matches_manifest() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == _manifest_version()


def test_readme_status_matches_manifest() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    match = re.search(r"\*\*Status: (\d+\.\d+\.\d+)", text)
    assert match is not None
    assert match.group(1) == _manifest_version()


def test_installation_status_matches_manifest() -> None:
    text = (ROOT / "docs" / "installation.md").read_text(encoding="utf-8")
    match = re.search(r"\*\*Stand (\d+\.\d+\.\d+):", text)
    assert match is not None
    assert match.group(1) == _manifest_version()


def test_changelog_has_current_version() -> None:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    first = re.search(r"^## \[(\d+\.\d+\.\d+)\]", text, re.MULTILINE)
    assert first is not None
    assert first.group(1) == _manifest_version()
