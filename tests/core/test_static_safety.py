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
# Experten-Funktion "Schalter als Sirene": switch-Dienste ausschließlich im Siren Executor
EXECUTOR_ONLY_DOMAINS = {"SWITCH_DOMAIN"}


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
    allowed = ALLOWED_SERVICE_DOMAINS | (
        EXECUTOR_ONLY_DOMAINS if path.name == "siren_executor.py" else set()
    )
    bad = [(line, domain) for line, domain in calls if domain not in allowed]
    assert not bad, f"{path.name}: unerlaubte Dienstaufrufe {bad}"


def test_switch_services_only_from_guarded_executor() -> None:
    """Schalter werden nur über den Executor geschaltet – also nur nach dem Guard."""
    text = (SOURCE_ROOT / "siren_executor.py").read_text(encoding="utf-8")
    assert 'SWITCH_DOMAIN = "switch"' in text
    for path in SOURCES:
        if path.name != "siren_executor.py":
            source = path.read_text(encoding="utf-8")
            assert "SWITCH_DOMAIN" not in source, path.name
            assert "switch.turn_" not in source, path.name


def test_only_threshold_and_switch_as_x_helpers_are_created() -> None:
    """Die Einstellungsseite legt ausschließlich Schwellenwert-Helfer bzw. "Schalter als Sirene" an.

    Seit 0.63.2 gibt es keinen Einstellungsdialog mehr – die Installation startet keine Abläufe.
    """
    assert "async_init" not in (SOURCE_ROOT / "config_flow.py").read_text(encoding="utf-8")
    text = (SOURCE_ROOT / "settings_ws.py").read_text(encoding="utf-8")
    tree = ast.parse(text)
    inits = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "async_init"
    ]
    domains = sorted(
        i.args[0].value
        for i in inits
        if isinstance(i.args[0], ast.Constant) and isinstance(i.args[0].value, str)
    )
    assert len(inits) == len(domains) == 2
    assert domains == ["switch_as_x", "threshold"]
    for path in SOURCES:
        if path.name not in ("settings_ws.py", "config_flow.py"):
            assert ".flow.async_init" not in path.read_text(encoding="utf-8"), path.name


def test_controls_only_send_keypad_state() -> None:
    """Bedienteile senden nur zweierlei per MQTT:

    - die Zustandsanzeige (arm_mode) an <keypad-topic>/set eines Zigbee2MQTT-Keypads,
    - an die eigenen Topics einer MQTT-Schnittstelle: state, attributes, response, availability –
      nie an ihr Befehls-Topic set.
    """
    text = (SOURCE_ROOT / "controls.py").read_text(encoding="utf-8")
    tree = ast.parse(text)
    publishes = [
        ast.unparse(node)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "async_publish"
    ]
    assert len(publishes) == 2
    keypad = [p for p in publishes if "f'{keypad.topic}/set'" in p]
    assert len(keypad) == 1
    assert "json.dumps({'arm_mode': arm_mode})" in keypad[0]
    interface = [p for p in publishes if "f'{interface.topic}/{suffix}'" in p]
    assert len(interface) == 1
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "_mqtt_publish"
    ]
    assert calls
    allowed = {"TOPIC_STATE", "TOPIC_ATTRIBUTES", "TOPIC_RESPONSE", "TOPIC_AVAILABILITY"}
    for call in calls:
        suffix = call.args[1]
        assert isinstance(suffix, ast.Name), ast.unparse(call)
        assert suffix.id in allowed, ast.unparse(call)
    assert "async_call(" not in text
    for path in SOURCE_ROOT.rglob("*.py"):
        if path.name != "controls.py":
            assert "async_publish" not in path.read_text(encoding="utf-8"), path.name


def test_no_deprecated_device_registry_access() -> None:
    """HA 2027.9/2027.10: kein ``devices.values()``/``.get()``, kein ``config_entries`` am Gerät."""
    import re  # noqa: PLC0415
    from pathlib import Path  # noqa: PLC0415

    root = Path(__file__).parents[2] / "custom_components" / "hauswacht"
    bad = re.compile(r"\.devices\.(values|items|keys|get|get_entries)\(|device\.config_entries\b")
    found = [
        f"{path.name}:{n}"
        for path in root.glob("*.py")
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if bad.search(line) and "executor" not in line
    ]
    assert found == []


# Datenschutz im Log (ADR 0020): Diese Werte landen nie in einer Log-Zeile. Erlaubt ist nur die
# Frage „gibt es einen?“ als Bedingung, z. B. ``"mit Ausweis" if code else ""``.
LOG_SECRETS = {
    "code",
    "codes",
    "pin",
    "pin_digest",
    "pin_salt",
    "tag",
    "tags",
    "card",
    "cards",
    "latitude",
    "longitude",
    "ssid",
    "ssids",
    "title",
    "message",
    "text",
    "filled",
    "values",
    "identity",
    "user_name",
    "person_name",
    "by",  # Benutzername („von wem“) – steht im Logbuch, nicht im Log
    "changed_by",
}


def _log_calls(tree: ast.AST) -> list[ast.Call]:
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "_LOGGER"
    ]


def _used_names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.IfExp):
        # Bedingung darf ein Geheimnis prüfen; ausgegeben werden nur die beiden Zweige
        return _used_names(node.body) + _used_names(node.orelse)
    found = []
    if isinstance(node, ast.Name):
        found.append(node.id)
    elif isinstance(node, ast.Attribute):
        found.append(node.attr)
    for child in ast.iter_child_nodes(node):
        found.extend(_used_names(child))
    return found


@pytest.mark.parametrize("path", SOURCES, ids=lambda p: str(p.relative_to(SOURCE_ROOT)))
def test_no_secrets_in_log_lines(path: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    bad = [
        f"{path.name}:{call.lineno} {name}"
        for call in _log_calls(tree)
        for arg in [*call.args[1:], *(k.value for k in call.keywords)]
        for name in _used_names(arg)
        if name in LOG_SECRETS
    ]
    assert not bad, bad


def test_log_secret_check_catches_a_pin() -> None:
    tree = ast.parse(
        '_LOGGER.debug("PIN %s", user.pin)\n_LOGGER.info("x %s", "ja" if code else "")'
    )
    names = [n for call in _log_calls(tree) for a in call.args[1:] for n in _used_names(a)]
    assert "pin" in names
    assert "code" not in names
