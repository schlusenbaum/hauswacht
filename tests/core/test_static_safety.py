"""Statische Sicherheitsprüfungen über den gesamten Integrationscode.

Diese Tests verhindern, dass sicherheitskritische Muster unbemerkt in den Code
gelangen – unabhängig davon, ob es für sie bereits Laufzeittests gibt.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SOURCE_ROOT = Path(__file__).resolve().parents[2] / "custom_components" / "hauswacht"
SOURCES = sorted(SOURCE_ROOT.rglob("*.py"))
CORE_SOURCES = sorted((SOURCE_ROOT / "core").rglob("*.py"))

FORBIDDEN_SNIPPETS = {
    # Script, das ALLE Rauchmelder-Sirenen abschaltet – würde einen Brandalarm beenden.
    "rauchmelder_alarm_aus": "Fremdes Rauchmelder-Script darf nie aufgerufen werden",
    # Gerätewerte (z. B. die Höchstdauer der Rauchmelder) werden nie geschrieben.
    '"set_value"': "Hauswacht schreibt keine Gerätewerte",
    "SERVICE_SET_VALUE": "Hauswacht schreibt keine Gerätewerte",
    "number.set_value": "Hauswacht schreibt keine Gerätewerte",
}

# Einzige Dienste, die Hauswacht aufrufen darf: Sirenen (nur im Executor) und Benachrichtigungen.
ALLOWED_SERVICE_DOMAINS = {"siren", "SIREN_DOMAIN", "notify", "NOTIFY_DOMAIN"}


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


def _siren_service_calls(tree: ast.AST) -> list[int]:
    """Zeilen mit async_call(...), deren Domain "siren" bzw. SIREN_DOMAIN ist."""
    lines: list[int] = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        if node.func.attr not in {"async_call", "call"} or not node.args:
            continue
        first = node.args[0]
        is_siren = (isinstance(first, ast.Constant) and first.value == "siren") or (
            isinstance(first, ast.Name) and first.id == "SIREN_DOMAIN"
        )
        if is_siren:
            lines.append(node.lineno)
    return lines


@pytest.mark.parametrize("path", SOURCES, ids=lambda p: str(p.relative_to(SOURCE_ROOT)))
def test_siren_services_only_in_executor(path: Path) -> None:
    """Sirenen-Dienste dürfen ausschließlich im Siren Executor aufgerufen werden."""
    text = path.read_text(encoding="utf-8")
    calls = _siren_service_calls(ast.parse(text))
    if path.name == "siren_executor.py":
        return
    assert not calls, f"{path.name} ruft Sirenen-Dienste direkt auf (Zeilen {calls})"
    assert "siren.turn_" not in text, f"{path.name} nennt einen Sirenen-Dienst"


def test_executor_is_the_only_siren_caller_and_uses_the_guard() -> None:
    executor = SOURCE_ROOT / "siren_executor.py"
    text = executor.read_text(encoding="utf-8")
    assert _siren_service_calls(ast.parse(text)), "Executor ruft keine Sirenen auf?"
    assert "decide_activation" in text
    assert "decide_stop" in text


def test_homecoming_observer_switches_nothing() -> None:
    """Die Heimkehr-Beobachtung liest nur: keine Dienste, kein Scharf/Unscharf, kein Alarm."""
    source = (SOURCE_ROOT / "homecoming_observer.py").read_text(encoding="utf-8")
    for forbidden in (
        "async_call",
        "_dispatch",
        "disarm",
        ".arm(",
        "SensorTriggered",
        "sirens",
        "notifier",
    ):
        assert forbidden not in source, forbidden


def _service_call_domains(tree: ast.AST) -> list[tuple[int, str]]:
    calls: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        if node.func.attr not in {"async_call", "call"}:
            continue
        first = node.args[0] if node.args else None
        if isinstance(first, ast.Constant):
            calls.append((node.lineno, str(first.value)))
        elif isinstance(first, ast.Name):
            calls.append((node.lineno, first.id))
        else:
            calls.append((node.lineno, "<dynamisch>"))
    return calls


@pytest.mark.parametrize("path", SOURCES, ids=lambda p: str(p.relative_to(SOURCE_ROOT)))
def test_only_siren_and_notify_services(path: Path) -> None:
    """Hauswacht ruft keine anderen Dienste auf – also schaltet und schreibt es keine Geräte
    (z. B. keine number-Dienste, die die Höchstdauer der Rauchmelder ändern könnten)."""
    calls = _service_call_domains(ast.parse(path.read_text(encoding="utf-8")))
    bad = [(line, domain) for line, domain in calls if domain not in ALLOWED_SERVICE_DOMAINS]
    assert not bad, f"{path.name}: unerlaubte Dienstaufrufe {bad}"


def test_only_threshold_helpers_are_created() -> None:
    """Der Helfer-Assistent legt ausschließlich Schwellenwert-Helfer an."""
    text = (SOURCE_ROOT / "config_flow.py").read_text(encoding="utf-8")
    tree = ast.parse(text)
    inits = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "async_init"
    ]
    assert len(inits) == 1
    first = inits[0].args[0]
    assert isinstance(first, ast.Name)
    assert first.id == "THRESHOLD_DOMAIN"
    assert 'THRESHOLD_DOMAIN = "threshold"' in text


def test_controls_only_send_keypad_state() -> None:
    """Bedienteile: einzige Sendung an Geräte ist arm_mode an <keypad-topic>/set."""
    text = (SOURCE_ROOT / "controls.py").read_text(encoding="utf-8")
    tree = ast.parse(text)
    publishes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "async_publish"
    ]
    assert len(publishes) == 1
    assert "f'{keypad.topic}/set'" in ast.unparse(publishes[0])
    assert "json.dumps({'arm_mode': arm_mode})" in ast.unparse(publishes[0])
    assert "async_call(" not in text
    for path in SOURCE_ROOT.rglob("*.py"):
        if path.name != "controls.py":
            assert "async_publish" not in path.read_text(encoding="utf-8"), path.name
