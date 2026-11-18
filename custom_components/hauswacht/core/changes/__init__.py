"""Einstellungsregeln: Änderungen an den Einstellungen prüfen und anwenden.

Rein und ohne Home Assistant. Jede Funktion bekommt die bisherigen Einstellungen und eine
Eingabe und liefert ein :class:`Change`: entweder die neuen Einstellungen (fertig zum Speichern)
oder Fehler. Einstellungsdialog und Einrichtungsassistent rufen dieselben Funktionen auf – eine
Regel steht so an genau einer Stelle (ADR 0009).

Die Funktionen ändern die übergebenen Einstellungen nie, sie liefern immer eine Kopie.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Change:
    """Ergebnis einer Änderung.

    - ``options``: neue Einstellungen, ``None`` bei Fehlern
    - ``errors``: Feld -> Fehlerschlüssel (wie in den Übersetzungen), ``"base"`` = allgemein
    - ``details``: Zusatzangaben für die Fehlermeldung (z. B. welche Melder kollidieren)
    - ``item_id``: ID des angelegten oder geänderten Eintrags
    """

    options: dict[str, Any] | None = None
    errors: Mapping[str, str] = field(default_factory=dict)
    details: Mapping[str, Any] = field(default_factory=dict)
    item_id: str | None = None

    @property
    def ok(self) -> bool:
        return self.options is not None and not self.errors


def failed(errors: Mapping[str, str], **details: Any) -> Change:
    return Change(errors=dict(errors), details=details)


def copy_options(options: Mapping[str, Any]) -> dict[str, Any]:
    """Flache Kopie – verschachtelte Teile werden beim Ändern selbst kopiert."""
    return dict(options)


def options_revision(options: Mapping[str, Any]) -> str:
    """Prüfsumme der Einstellungen – ändert sich mit jeder Änderung, egal von wo."""
    raw = json.dumps(options, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
