"""Ausgangserkennung – Rausgehen ohne PIN erkennen (ADR 0014) – rein, ohne Home Assistant.

Ein Profil ist scharf (z. B. „Nacht“), Ben geht raus und vergisst PIN und Durchgang. Statt der
Eingangsverzögerung läuft dann eine **stille Wartezeit**. Sagen in der Zeit die Signale einer
Person, die vorher zuhause war, „weg“ (nach ihren Regeln aus ADR 0021) und bleibt das mindestens
30 Sekunden so, ist sie rausgegangen: kein Alarm, das Profil bleibt scharf. Sonst gibt es am Ende
der Wartezeit Alarm.

Gespeichert im Profil unter ``exit_detect``::

    {"enabled": bool, "wait": Minuten, "expert": bool, "inside": [Entitäten]}

- ``wait``: 1–5 Minuten; bis 15 nur mit ``expert`` (Expertenoption mit Warnhinweis).
- ``inside``: „Melder im Haus“ (empfohlen, nicht Pflicht). Ist einer gesetzt, gilt die Wartezeit
  nur, wenn er höchstens 2 Minuten vor dem Öffnen etwas gemeldet hat.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from .presence_rules import MODE_ONE, PersonRules, Signal

DEFAULT_WAIT = 3  # min
MAX_WAIT = 5  # min: so lange bliebe ein Einbruch höchstens still
MAX_WAIT_EXPERT = 15  # min: nur als Expertenoption
INSIDE_RECENT = 120  # s: so kurz vor dem Öffnen muss der Melder im Haus etwas gemeldet haben
CONFIRM = 30  # s: so lange muss „weg“ halten, bevor es als rausgegangen zählt
SHARED = 60  # s: mehrere Personen so nah beieinander nur über WLAN „weg“ = WLAN-Ausfall


@dataclass(frozen=True)
class ExitConfig:
    enabled: bool = False
    wait: int = DEFAULT_WAIT  # Minuten
    expert: bool = False
    inside: frozenset[str] = frozenset()


def _int(value: Any, default: int, low: int, high: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return min(max(number, low), high)


def parse_exit(options: Mapping[str, Any], profile_id: str | None) -> ExitConfig:
    """Einstellungen eines Profils (fehlt etwas: Standard, aus)."""
    profiles = options.get("profiles", {})
    stored = profiles.get(profile_id, {}) if isinstance(profiles, Mapping) and profile_id else {}
    raw = stored.get("exit_detect", {}) if isinstance(stored, Mapping) else {}
    if not isinstance(raw, Mapping):
        return ExitConfig()
    expert = bool(raw.get("expert", False))
    inside = raw.get("inside", [])
    return ExitConfig(
        enabled=bool(raw.get("enabled", False)),
        wait=_int(raw.get("wait"), DEFAULT_WAIT, 1, MAX_WAIT_EXPERT if expert else MAX_WAIT),
        expert=expert,
        inside=frozenset(e for e in inside if isinstance(e, str) and e)
        if isinstance(inside, list)
        else frozenset(),
    )


def exit_from_input(data: Mapping[str, Any]) -> dict[str, Any]:
    """Gespeicherte Form aus dem Formular (Abschnitt ``exit_detect``)."""
    config = parse_exit({"profiles": {"p": {"exit_detect": dict(data)}}}, "p")
    return {
        "enabled": config.enabled,
        "wait": config.wait,
        "expert": config.expert,
        "inside": sorted(config.inside),
    }


def inside_ok(config: ExitConfig, inside_last: Iterable[float], opened_at: float) -> bool:
    """Darf die Wartezeit starten? Ohne Melder im Haus immer; mit nur nach Bewegung drinnen."""
    if not config.inside:
        return True
    return any(0 <= opened_at - t <= INSIDE_RECENT for t in inside_last)


def can_leave(rules: PersonRules, signals: Iterable[Signal]) -> bool:
    """War die Person beim Öffnen nachweislich zuhause – sagt ein Weggehen-Signal „zuhause“?

    Nur dann kann Hauswacht erkennen, dass sie rausgeht (ihr Handy wird danach „weg“).
    """
    return any(s.value is True for s in signals if rules.leaves(s.entity_id))


def gone(rules: PersonRules, signals: Iterable[Signal], opened_at: float) -> list[str]:
    """Welche Weggehen-Signale belegen gerade, dass die Person rausgegangen ist?

    Mit denselben Regeln wie die Anwesenheit (ADR 0021): „eines reicht“ – ein Weggehen-Signal ist
    seit dem Öffnen auf „weg“ gewechselt; „alle müssen“ – alle Weggehen-Signale sagen „weg“ (die
    Tür ist der Beleg, eine Ortung braucht es hier nicht). Unbekannt zählt nie als weg.
    Leere Liste: nicht rausgegangen.
    """
    leave = [s for s in signals if rules.leaves(s.entity_id)]
    if not leave:
        return []
    if rules.mode == MODE_ONE:
        return [s.entity_id for s in leave if s.value is False and s.since >= opened_at - 60]
    if all(s.value is False for s in leave):
        return [s.entity_id for s in leave]
    return []


@dataclass
class ExitWatch:
    """Eine laufende stille Wartezeit: wer war zuhause, wer sagt seit wann „weg“."""

    opened_at: float
    door: str | None
    candidates: frozenset[str]  # Personen, die beim Öffnen nachweislich zuhause waren
    gone_since: dict[str, float] = field(default_factory=dict)
    wlan_only: dict[str, bool] = field(default_factory=dict)

    def note(self, person: str, gone: bool, now: float, *, wlan_only: bool = False) -> None:
        """Stand einer Person: sagen ihre Weggehen-Signale gerade „weg“?"""
        if person not in self.candidates:
            return
        if not gone:
            self.gone_since.pop(person, None)  # Aussetzer: wieder da
            self.wlan_only.pop(person, None)
            return
        self.gone_since.setdefault(person, now)
        self.wlan_only[person] = wlan_only

    def _shared_outage(self, person: str) -> bool:
        """Sind mehrere gleichzeitig nur über WLAN „weg“? Dann ist eher das WLAN ausgefallen."""
        if not self.wlan_only.get(person):
            return False
        start = self.gone_since[person]
        return any(
            other != person and self.wlan_only.get(other) and abs(t - start) <= SHARED
            for other, t in self.gone_since.items()
        )

    def left(self, now: float) -> str | None:
        """Wer ist (mindestens 30 Sekunden lang) rausgegangen? ``None``: niemand."""
        for person, since in sorted(self.gone_since.items(), key=lambda i: i[1]):
            if now - since >= CONFIRM and not self._shared_outage(person):
                return person
        return None
