"""Die Referenz muss alles nennen, was Hauswacht für Automationen bereitstellt.

Kommt ein neues Ereignis, eine Aktion oder ein Attribut des Bedienfelds dazu und fehlt es in der
Referenz (deutsch oder englisch), schlägt dieser Test fehl.
"""

from __future__ import annotations

import re
import types
from pathlib import Path

import pytest

from custom_components.hauswacht.core import state_machine

ROOT = Path(__file__).resolve().parents[2]
CODE = ROOT / "custom_components" / "hauswacht"
REFERENCES = [ROOT / "docs" / "referenz.md", ROOT / "docs" / "en" / "reference.md"]

EVENT_PATTERNS = [
    re.compile(r'"type":\s*"([A-Z]\w+)"'),
    re.compile(r'_event\(\s*"([A-Z]\w+)"'),
    re.compile(r'_fire\(\s*"([A-Z]\w+)"'),
]


def _event_types() -> set[str]:
    found: set[str] = set()
    for path in CODE.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for pattern in EVENT_PATTERNS:
            found.update(pattern.findall(text))
    # Effekte des Zustandsautomaten werden alle als Ereignis gemeldet
    effect = state_machine.Effect
    assert isinstance(effect, types.UnionType)
    found.update(t.__name__ for t in effect.__args__)
    return found


def _services() -> set[str]:
    text = (CODE / "services.yaml").read_text(encoding="utf-8")
    return set(re.findall(r"^([a-z_]+):\s*$", text, re.MULTILINE))


def _panel_attributes() -> set[str]:
    text = (CODE / "alarm_control_panel.py").read_text(encoding="utf-8")
    keys: set[str] = set()
    for block in re.findall(r"def extra_state_attributes.*?\n    def ", text, re.DOTALL):
        keys.update(re.findall(r'"([a-z_]+)":', block))
    keys.discard("state")  # nur innerhalb von "areas"
    guard = (CODE / "runtime.py").read_text(encoding="utf-8")
    match = re.search(r"def code_guard_info.*?return \{(.*?)\}", guard, re.DOTALL)
    assert match, "code_guard_info nicht gefunden"
    keys.update(re.findall(r'"([a-z_]+)":', match.group(1)))
    return keys


def test_event_types_found() -> None:
    types_ = _event_types()
    assert {"StateChanged", "TamperDetected", "ActionCode", "LockIdentified", "AutoArmed"} <= types_


@pytest.mark.parametrize("reference", REFERENCES, ids=lambda p: p.name)
def test_every_event_is_documented(reference: Path) -> None:
    text = reference.read_text(encoding="utf-8")
    missing = sorted(t for t in _event_types() if f"`{t}`" not in text)
    assert not missing, f"In {reference.name} fehlen Ereignisse: {missing}"


@pytest.mark.parametrize("reference", REFERENCES, ids=lambda p: p.name)
def test_every_action_is_documented(reference: Path) -> None:
    text = reference.read_text(encoding="utf-8")
    missing = sorted(s for s in _services() if f"`hauswacht.{s}`" not in text)
    assert not missing, f"In {reference.name} fehlen Aktionen: {missing}"


@pytest.mark.parametrize("reference", REFERENCES, ids=lambda p: p.name)
def test_every_panel_attribute_is_documented(reference: Path) -> None:
    text = reference.read_text(encoding="utf-8")
    missing = sorted(a for a in _panel_attributes() if f"`{a}`" not in text)
    assert not missing, f"In {reference.name} fehlen Attribute: {missing}"
