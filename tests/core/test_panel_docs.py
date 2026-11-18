"""Die Verweise der Einstellungsseite in die Anleitung zeigen auf echte Seiten und Anker."""

from __future__ import annotations

import re
from pathlib import Path

from .test_docs import _anchors

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
SCRIPT = ROOT / "custom_components" / "hauswacht" / "frontend" / "hauswacht-panel-docs.js"


def _targets() -> list[tuple[Path, str]]:
    text = SCRIPT.read_text(encoding="utf-8")
    found: list[tuple[Path, str]] = []
    for de, en in re.findall(r'\[\s*"([^"]+\.md[^"]*)",\s*"([^"]+\.md[^"]*)"', text):
        for base, ref in ((DOCS, de), (DOCS / "en", en)):
            page, _, anchor = ref.partition("#")
            found.append((base / page, anchor))
    return found


def test_every_doc_link_exists() -> None:
    targets = _targets()
    assert len(targets) > 60
    problems = [
        f"{path.relative_to(ROOT)}#{anchor}"
        for path, anchor in targets
        if not path.exists() or (anchor and anchor not in _anchors(path))
    ]
    assert not problems, problems


def test_help_keys_used_by_panel_exist() -> None:
    script = SCRIPT.read_text(encoding="utf-8")
    keys = set(re.findall(r"^  (\w+): \[", script, flags=re.MULTILINE))
    frontend = SCRIPT.parent
    used: set[str] = set()
    for name in ("hauswacht-panel.js", "hauswacht-panel-alarm.js", "hauswacht-panel-rules.js"):
        text = (frontend / name).read_text(encoding="utf-8")
        text = re.sub(r'===\s*"\w+"', "", text)  # Vergleiche sind keine Schlüssel
        for line in re.findall(r"(?:decorate\(|const help = |helpKey: )[^\n]*", text):
            used |= set(re.findall(r'"(\w+)"', line))
        for block in re.findall(r"(?:PART_HELP|EDITOR_HELP) = \{([^}]*)\}", text, flags=re.DOTALL):
            used |= set(re.findall(r':\s*"(\w+)"', block))
    panel = (frontend / "hauswacht-panel.js").read_text(encoding="utf-8")
    used |= set(re.findall(r'_card\([^;]*?,\s*"(\w+)"\)', panel))
    missing = sorted(u for u in used if u not in keys)
    assert not missing, missing
