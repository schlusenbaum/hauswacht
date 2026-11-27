"""Messung für die Ausgangserkennung (ADR 0014, 0.63.1) – SCHALTET NICHTS.

Bei jeder Türöffnung hält die Heimkehr-Beobachtung je Person fest:

- ``age``: Wie lange ist das letzte **Lebenszeichen** her (ein Signal meldet „zuhause“)?
  Ohne Signal „zuhause“ beim Öffnen: ``None``.
- ``confirm``: Wann meldet sich danach zum ersten Mal ein Signal mit „zuhause“?
- ``last``: Wann zum letzten Mal (innerhalb von 15 Minuten nach dem Öffnen)?

Daraus zwei Antworten, von denen abhängt, ob die Ausgangserkennung bei euch schützt:

a) **Lebenszeichen vor dem Rausgehen:** Hatte, wer rausgegangen ist, kurz vorher ein
   Lebenszeichen? Nur dann kann die Ausgangserkennung ihn später erkennen.
b) **„Noch da“ nach dem Öffnen:** Wie schnell meldet sich das Handy von jemandem, der
   zuhause bleibt, wieder? So lange bliebe ein Einbruch höchstens still. Und: Melden die
   Signale von jemandem, der gerade rausgeht, noch eine Weile „zuhause“ (z. B. Ping mit
   Nachlaufzeit)? Dann würde die Ausgangserkennung ihn fälschlich für „noch da“ halten.

Ob jemand rausgegangen ist, entscheidet die Messung „Weggehen“ (``core/departure.py``).
"""

from __future__ import annotations

import statistics
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .departure import WAIT_MAX, DepartureVerdict
from .homecoming import EARLIEST
from .texts import DE, tr

LIFE_SIGN_FRESH = 180  # s: so alt darf das letzte Lebenszeichen beim Öffnen höchstens sein
CHECK_WINDOW = WAIT_MAX  # s: so lange nach dem Öffnen wird auf Lebenszeichen geachtet
MIN_CHECKS = 3  # so oft muss etwas gemessen sein, bevor ein Satz dazu erscheint


@dataclass(frozen=True)
class PersonCheck:
    age: float | None  # s seit dem letzten Lebenszeichen beim Öffnen; None = keins
    confirm: float | None  # s bis zum ersten Lebenszeichen danach; None = keins
    last: float | None  # s bis zum letzten Lebenszeichen danach (im Fenster)

    @property
    def fresh(self) -> bool:
        return self.age is not None and self.age <= LIFE_SIGN_FRESH


@dataclass(frozen=True)
class ExitCheck:
    at: float
    sensor: str
    persons: Mapping[str, PersonCheck]


def parse_checks(raw: Iterable[Mapping[str, Any]]) -> list[ExitCheck]:
    """Gespeicherte Einträge lesen; Unbrauchbares wird übersprungen."""
    checks: list[ExitCheck] = []
    for item in raw:
        try:
            persons = {
                str(person): PersonCheck(
                    age=_opt(values.get("age")),
                    confirm=_opt(values.get("confirm")),
                    last=_opt(values.get("last")),
                )
                for person, values in dict(item.get("persons", {})).items()
                if isinstance(values, Mapping)
            }
            checks.append(
                ExitCheck(at=float(item["at"]), sensor=str(item["sensor"]), persons=persons)
            )
        except (KeyError, TypeError, ValueError):
            continue
    return checks


def _opt(value: Any) -> float | None:
    return None if value is None else float(value)


def note_life_sign(record: dict[str, Any], person: str, now: float) -> bool:
    """Ein Lebenszeichen nach dem Öffnen eintragen. True, wenn sich etwas geändert hat."""
    entry = record.get("persons", {}).get(person)
    if entry is None:
        return False
    delay = round(now - float(record["at"]), 1)
    if delay < 0 or delay > CHECK_WINDOW:
        return False
    if entry.get("confirm") is None:
        entry["confirm"] = delay
    entry["last"] = delay
    return True


def _left_doors(verdicts: Iterable[DepartureVerdict]) -> dict[str, dict[float, float]]:
    """Je Person: Türöffnungen, durch die sie rausgegangen ist -> Sekunden bis „alle weg“."""
    left: dict[str, dict[float, float]] = {}
    for v in verdicts:
        if v.door is None or not v.departure.source.endswith(EARLIEST):
            continue
        left.setdefault(v.departure.person, {})[v.door.at] = max(0.0, v.delay or 0.0)
    return left


def exit_check_stats(
    checks: Sequence[ExitCheck], verdicts: Iterable[DepartureVerdict], now: float
) -> dict[str, dict[str, Any]]:
    """Je Person die Kennzahlen a) und b). Nur abgeschlossene Messungen (älter als 15 min)."""
    left = _left_doors(verdicts)
    result: dict[str, dict[str, Any]] = {}
    done = [c for c in checks if now - c.at >= CHECK_WINDOW]
    persons = {p for c in done for p in c.persons}
    for person in sorted(persons):
        gone = left.get(person, {})
        out = [c.persons[person] for c in done if person in c.persons and c.at in gone]
        # Nachklang: nur bis alle Signale weg waren (0.66.0b8). Ein Lebenszeichen danach ist
        # die Rückkehr, kein Nachklang – vorher zählte z. B. eine Rückkehr nach 6 min mit.
        out_until = [
            (c.persons[person], gone[c.at])
            for c in done
            if person in c.persons and c.at in gone and c.persons[person].fresh
        ]
        stay = [
            c.persons[person]
            for c in done
            if person in c.persons and c.at not in gone and c.persons[person].fresh
        ]
        out_ages = [p.age for p in out if p.age is not None]
        out_fresh = [p for p in out if p.fresh]
        echoes = [min(p.last, until) for p, until in out_until if p.last is not None]
        confirms = [p.confirm for p in stay if p.confirm is not None]
        result[person] = {
            # a) Lebenszeichen vor dem Rausgehen
            "left": len(out),
            "left_with_sign": len(out_fresh),
            "sign_age_median": round(statistics.median(out_ages)) if out_ages else None,
            # b1) Wer zuhause bleibt: wie schnell kommt „noch da“?
            "stayed": len(stay),
            "confirm_median": round(statistics.median(confirms)) if confirms else None,
            "confirm_max": round(max(confirms)) if confirms else None,
            "unconfirmed": len(stay) - len(confirms),
            # b2) Wer rausgeht: melden seine Signale danach noch „zuhause“?
            "left_echo": len(echoes),
            "left_echo_max": round(max(echoes)) if echoes else None,
        }
    return result


def exit_check_text(values: Mapping[str, Any], name: str, lang: str = DE) -> list[str]:
    """Sätze je Person für Bericht und Einstellungsseite (leer, solange zu wenig gemessen)."""
    lines: list[str] = []
    if values["left"] >= MIN_CHECKS:
        lines.append(
            tr(lang, "exit_sign", name=name, count=values["left_with_sign"], total=values["left"])
        )
    if values["stayed"] >= MIN_CHECKS:
        key = "exit_confirm_missing" if values["unconfirmed"] else "exit_confirm"
        lines.append(
            tr(
                lang,
                key,
                name=name,
                median=values["confirm_median"] if values["confirm_median"] is not None else "–",
                longest=values["confirm_max"] if values["confirm_max"] is not None else "–",
                missing=values["unconfirmed"],
                total=values["stayed"],
            )
        )
    if values["left_echo"]:
        lines.append(
            tr(
                lang,
                "exit_echo",
                name=name,
                count=values["left_echo"],
                longest=values["left_echo_max"],
            )
        )
    return lines


def exit_check_lines(
    stats: Mapping[str, Mapping[str, Any]], names: Mapping[str, str], lang: str = DE
) -> list[str]:
    """Abschnitt für den Bericht (leer, solange nichts gemessen ist)."""
    if not stats:
        return []
    lines = [tr(lang, "exit_heading"), "", tr(lang, "exit_cols"), "|---|---|---|---|---|"]
    for person in sorted(stats, key=lambda p: names.get(p, p)):
        v = stats[person]
        confirm = (
            f"{v['confirm_median']} s / {v['confirm_max']} s"
            if v["confirm_median"] is not None
            else "–"
        )
        echo = f"{v['left_echo']} ({v['left_echo_max']} s)" if v["left_echo"] else "0"
        lines.append(
            f"| {names.get(person, person)} | {v['left_with_sign']} / {v['left']} | "
            f"{confirm} | {v['unconfirmed']} / {v['stayed']} | {echo} |"
        )
    lines += ["", tr(lang, "exit_legend")]
    sentences = [
        "- " + line
        for person in sorted(stats, key=lambda p: names.get(p, p))
        for line in exit_check_text(stats[person], names.get(person, person), lang)
    ]
    if sentences:
        lines += ["", *sentences]
    return lines
