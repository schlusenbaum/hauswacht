"""Einstellungsseite: Sie schaltet keine Geräte – einzige Ausnahme ist der Sirenentest.

ADR 0011, Abschnitt 5: Die Seite ruft keine Dienste auf außer den drei Sirenentest-Diensten von
Hauswacht (deren Sperren im Hintergrund geprüft werden). Dieser Test hält das fest.
"""

from __future__ import annotations

import re
from pathlib import Path

FRONTEND = Path(__file__).parents[2] / "custom_components" / "hauswacht" / "frontend"
ALLOWED = {"siren_test", "siren_test_result", "siren_test_stop"}


def test_settings_page_calls_only_siren_test_services() -> None:
    calls: dict[str, set[str]] = {}
    for path in sorted(FRONTEND.glob("hauswacht-panel*.js")):
        text = path.read_text(encoding="utf-8")
        found = re.findall(r"callService\(\s*\"([a-z_]+)\",\s*\"([a-z_]+)\"", text)
        assert text.count("callService(") == len(found), f"{path.name}: unklarer Dienstaufruf"
        for domain, service in found:
            assert domain == "hauswacht", f"{path.name}: {domain}.{service}"
            calls.setdefault(path.name, set()).add(service)
    assert set(calls) <= {"hauswacht-panel.js"}
    assert calls.get("hauswacht-panel.js", set()) <= ALLOWED
