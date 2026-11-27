"""Anwesenheit je Person (ADR 0021) – rein, ohne Home Assistant.

Je Person lässt sich festlegen, welche Signale fürs **Ankommen** und welche fürs **Weggehen**
zählen, und wie Weggehen erkannt wird:

- ``all`` („alle müssen weg sein“, Standard): wie bisher – alle Weggehen-Signale sagen weg, dazu
  ein Beleg (ADR 0015, 0018).
- ``one`` („eines reicht“): Eine Eingangstür war auf, und danach – höchstens im Zeitfenster für
  „Tür + Signal“ – wechselte eines der Weggehen-Signale von „da“ auf „weg“ und ist noch weg.
  Die Tür ersetzt den Beleg. Ohne Tür (abschaltbar, unsicher) reicht der Wechsel allein.

Gespeichert wird nur, was **abweicht**: abgewählte Signale je Spalte, Personen mit „eines
reicht“ und Personen, bei denen keine Tür nötig ist. Wer nichts einstellt, hat
``PersonRules()`` – damit verhält sich alles genau wie vor ADR 0021.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

MODE_ALL = "all"
MODE_ONE = "one"
MODES = (MODE_ALL, MODE_ONE)

OPT_ARRIVE_OFF = "presence_arrive_off"  # {person: [Signale, die fürs Ankommen nicht zählen]}
OPT_LEAVE_OFF = "presence_leave_off"  # {person: [Signale, die fürs Weggehen nicht zählen]}
OPT_LEAVE_MODE = "presence_leave_mode"  # {person: "one"} – fehlt: "all"
OPT_LEAVE_NO_DOOR = "presence_leave_no_door"  # [Personen, bei denen „eines reicht“ ohne Tür gilt]


@dataclass(frozen=True)
class PersonRules:
    arrive_off: frozenset[str] = frozenset()
    leave_off: frozenset[str] = frozenset()
    mode: str = MODE_ALL
    door: bool = True  # nur für „eines reicht“: vorher muss eine Tür auf gewesen sein

    def arrives(self, entity_id: str) -> bool:
        return entity_id not in self.arrive_off

    def leaves(self, entity_id: str) -> bool:
        return entity_id not in self.leave_off

    @property
    def is_default(self) -> bool:
        """Verhält sich wie vor ADR 0021 (alle Signale in beiden Spalten, „alle müssen“)."""
        return not self.arrive_off and not self.leave_off and self.mode == MODE_ALL


DEFAULT_RULES = PersonRules()


@dataclass(frozen=True)
class Signal:
    """Ein Signal einer Person: zuhause (True), weg (False), unbekannt (None), seit wann."""

    entity_id: str
    value: bool | None
    since: float


def _entities(value: Any) -> frozenset[str]:
    if not isinstance(value, list):
        return frozenset()
    return frozenset(e for e in value if isinstance(e, str) and e)


def parse_presence_rules(options: Mapping[str, Any]) -> dict[str, PersonRules]:
    """Regeln je Person aus den Optionen – nur Personen, die etwas abweichend eingestellt haben."""
    arrive = options.get(OPT_ARRIVE_OFF, {})
    leave = options.get(OPT_LEAVE_OFF, {})
    modes = options.get(OPT_LEAVE_MODE, {})
    no_door_raw = options.get(OPT_LEAVE_NO_DOOR, [])
    arrive = arrive if isinstance(arrive, Mapping) else {}
    leave = leave if isinstance(leave, Mapping) else {}
    modes = modes if isinstance(modes, Mapping) else {}
    no_door = _entities(no_door_raw)
    persons = {
        p for p in (*arrive.keys(), *leave.keys(), *modes.keys(), *no_door) if isinstance(p, str)
    }
    rules: dict[str, PersonRules] = {}
    for person in sorted(persons):
        mode = modes.get(person)
        rule = PersonRules(
            arrive_off=_entities(arrive.get(person)),
            leave_off=_entities(leave.get(person)),
            mode=mode if mode in MODES else MODE_ALL,
            door=person not in no_door,
        )
        if rule != DEFAULT_RULES:
            rules[person] = rule
    return rules


def dump_presence_rules(rules: Mapping[str, PersonRules]) -> dict[str, Any]:
    """Regeln zurück in Optionen (nur Abweichungen, sortiert – für stabile Vergleiche)."""
    arrive = {p: sorted(r.arrive_off) for p, r in sorted(rules.items()) if r.arrive_off}
    leave = {p: sorted(r.leave_off) for p, r in sorted(rules.items()) if r.leave_off}
    modes = {p: r.mode for p, r in sorted(rules.items()) if r.mode != MODE_ALL}
    no_door = sorted(p for p, r in rules.items() if not r.door)
    return {
        OPT_ARRIVE_OFF: arrive,
        OPT_LEAVE_OFF: leave,
        OPT_LEAVE_MODE: modes,
        OPT_LEAVE_NO_DOOR: no_door,
    }
