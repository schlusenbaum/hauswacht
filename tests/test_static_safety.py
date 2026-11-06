"""Statische Sicherheitsprüfungen über den gesamten Integrationscode.

Diese Tests verhindern, dass sicherheitskritische Muster unbemerkt in den Code
gelangen – unabhängig davon, ob es für sie bereits Laufzeittests gibt.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SOURCE_ROOT = Path(__file__).resolve().parent.parent / "custom_components" / "hauswacht"
SOURCES = sorted(SOURCE_ROOT.rglob("*.py"))
CORE_SOURCES = sorted((SOURCE_ROOT / "core").rglob("*.py"))

FORBIDDEN_SNIPPETS = {
    # Script, das ALLE Rauchmelder-Sirenen abschaltet – würde einen Brandalarm beenden.
    "rauchmelder_alarm_aus": "Fremdes Rauchmelder-Script darf nie aufgerufen werden",
    # Die gerätseitige Höchstdauer der Rauchmelder darf nie verändert werden.
    'max_duration"': "Gerätewert max_duration darf nicht geschrieben werden",
    "number.set_value": "Hauswacht schreibt keine number-Entitäten",
}


def test_sources_exist() -> None:
    assert SOURCES, "Keine Quelldateien gefunden"


@pytest.mark.parametrize("path", SOURCES, ids=lambda p: str(p.relative_to(SOURCE_ROOT)))
def test_no_forbidden_snippets(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for snippet, why in FORBIDDEN_SNIPPETS.items():
        assert snippet not in text, f"{path.name}: {why}"


@pytest.mark.parametrize("path", CORE_SOURCES, ids=lambda p: p.name)
def test_core_has_no_home_assistant_imports(path: Path) -> None:
    """Die Kernlogik muss ohne Home Assistant testbar bleiben."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for name in names:
            assert not name.startswith("homeassistant"), f"{path.name} importiert {name}"


@pytest.mark.parametrize("path", SOURCES, ids=lambda p: str(p.relative_to(SOURCE_ROOT)))
def test_siren_services_only_in_executor(path: Path) -> None:
    """Sirenen-Services dürfen nur an einer Stelle aufgerufen werden.

    Ab 0.5.0 ist das ausschließlich ``siren_executor.py``. Bis dahin darf es
    nirgends einen Aufruf geben.
    """
    if path.name == "siren_executor.py":
        return
    text = path.read_text(encoding="utf-8")
    message = f"{path.name} spricht Sirenen-Services direkt an"
    assert '"siren"' not in text, message
    assert "'siren'" not in text, message
    assert "siren.turn_" not in text, message
