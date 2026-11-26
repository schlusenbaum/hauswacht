"""Konfiguration herunterladen (ADR 0019): echte Namen und Geheimnisse durch Platzhalter ersetzen.

Reiner Kern ohne Home Assistant. Hinein kommt ein beliebiges JSON-artiges Gebilde (Einstellungen,
Übersicht, Zustand …), heraus kommt dasselbe Gebilde, in dem

- Personen zu ``person.person_1`` / „Person 1“ werden – **gleichbleibend**: dieselbe Person
  heißt überall gleich, auch in Entitäts-IDs (``sensor.handy_von_anna`` →
  ``sensor.handy_von_person_1``);
- Benutzer zu ``benutzer_1`` / „Benutzer 1“, Karten zu ``karte_1``, Empfänger zu
  ``notify.empfaenger_1``, Lautsprecher, WLAN-Namen, MQTT-Topics, Geräte-IDs und Konten ebenso;
- PIN-Hashes, Salze und Aktions-Codes zu ``***``.

Die Struktur bleibt erhalten, damit man beim Debuggen sieht, *was* wie eingestellt ist – nur nicht,
*wer* oder *welcher Code*. Eine ungeschwärzte Fassung gibt es bewusst nicht.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

HIDDEN = "***"

# Schlüssel, deren Text-Werte nie im Klartext erscheinen (Wahrheitswerte bleiben)
SECRET_KEYS = frozenset(
    {"pin_salt", "pin_digest", "duress_salt", "duress_digest", "master_pin", "pin_hash"}
)

# Schlüssel → Art des Platzhalters. Alle Texte darunter (auch in Listen und Unter-Einträgen)
# werden ersetzt; Schlüssel von Unter-Einträgen bleiben.
CATEGORY_KEYS: Mapping[str, str] = {
    "tags": "karte",
    "tags_disabled": "karte",
    "tag": "karte",
    "cards": "karte",
    "ha_user": "konto",
    "notify": "empfaenger",
    "notify_system": "empfaenger",
    "duress_notify": "empfaenger",
    "targets": "empfaenger",
    "alarm_targets": "empfaenger",
    "general": "empfaenger",
    "duress": "empfaenger",
    "speakers": "lautsprecher",
    "homecoming_ssids": "wlan",
    "ssids": "wlan",
    "topic": "topic",
    "device": "geraet",
    "device_id": "geraet",
}

_PERSON = re.compile(r"\bperson\.[a-z0-9_]+")
_ENTITY = re.compile(r"^([a-z_]+)\.[a-z0-9_]+$")
_MIN_WORD = 3


@dataclass
class Pseudonymizer:
    """Ersetzt gleichbleibend: derselbe echte Wert bekommt immer denselben Platzhalter."""

    # Personen-ID → Anzeigename (aus Home Assistant), damit auch Namen in Texten verschwinden
    person_names: Mapping[str, str] = field(default_factory=dict)
    _exact: dict[str, str] = field(default_factory=dict)
    _count: dict[str, int] = field(default_factory=dict)
    _words: dict[str, int] = field(default_factory=dict)  # Wort (klein) → Personen-Nummer
    _user_words: dict[str, int] = field(default_factory=dict)  # Wort (klein) → Benutzer-Nummer
    _patterns: list[tuple[re.Pattern[str], Mapping[str, int], str, str]] = field(
        default_factory=list
    )
    _secrets: list[tuple[str, str]] = field(default_factory=list)

    # --- Platzhalter vergeben -------------------------------------------------------------------

    def _next(self, kind: str) -> int:
        self._count[kind] = self._count.get(kind, 0) + 1
        return self._count[kind]

    def _placeholder(self, kind: str, value: str) -> str:
        if value in self._exact:
            return self._exact[value]
        number = self._next(kind)
        match = _ENTITY.match(value)
        result = f"{match.group(1)}.{kind}_{number}" if match else f"{kind}_{number}"
        self._exact[value] = result
        return result

    def _person(self, person_id: str) -> str:
        if person_id not in self._exact:
            number = self._next("person")
            self._exact[person_id] = f"person.person_{number}"
            words = [person_id.split(".", 1)[1], *_words(self.person_names.get(person_id, ""))]
            for word in words:
                if len(word) >= _MIN_WORD:
                    self._words.setdefault(word.lower(), number)
        return self._exact[person_id]

    def _user(self, user_id: str, name: str) -> tuple[str, str]:
        # Gleicher Name = gleicher Benutzer (Einstellungen und Übersicht nennen ihn verschieden)
        key = f"\0user:{name.strip().lower() or user_id}"
        if key not in self._exact:
            number = self._next("benutzer")
            self._exact[key] = str(number)
            for word in _words(name):
                if len(word) >= _MIN_WORD:
                    self._user_words.setdefault(word.lower(), number)
        number = int(self._exact[key])
        return f"benutzer_{number}", f"Benutzer {number}"

    # --- Durchlauf -----------------------------------------------------------------------------

    def run(self, data: Any) -> Any:
        """Erst alle Personen und Benutzer einsammeln (feste Nummern), dann ersetzen."""
        for person_id in sorted(self.person_names):
            self._person(person_id)
        self._collect(data)
        self._prepare()
        return self._walk(data, None, False)

    def _prepare(self) -> None:
        self._patterns = [
            (_word_pattern(words), words, slug, label)
            for words, slug, label in (
                (self._words, "person_{n}", "Person {n}"),
                (self._user_words, "benutzer_{n}", "Benutzer {n}"),
            )
            if words
        ]

    def _known_secrets(self) -> list[tuple[str, str]]:
        # Bekannte Geheimnisse, die in längeren Texten stecken (z. B. ein Empfänger im Satz)
        if len(self._secrets) != len(self._exact):
            self._secrets = sorted(self._exact.items(), key=lambda x: -len(x[0]))
        return [(s, p) for s, p in self._secrets if len(s) >= 5 and not s.startswith("\0")]

    def _collect(self, data: Any) -> None:
        if isinstance(data, Mapping):
            for key, value in data.items():
                if isinstance(key, str):
                    self._collect_text(key)
                if key == "users":
                    self._collect_users(value)
                self._collect(value)
        elif isinstance(data, list | tuple):
            for item in data:
                self._collect(item)
        elif isinstance(data, str):
            self._collect_text(data)

    def _collect_text(self, text: str) -> None:
        for person_id in sorted(set(_PERSON.findall(text))):
            self._person(person_id)

    def _collect_users(self, users: Any) -> None:
        if isinstance(users, Mapping):
            for user_id, data in users.items():
                name = data.get("name", "") if isinstance(data, Mapping) else ""
                self._user(str(user_id), str(name or ""))
        elif isinstance(users, list):
            for index, data in enumerate(users):
                name = data.get("name", "") if isinstance(data, Mapping) else ""
                self._user(f"#{index}:{name}", str(name or ""))

    def _walk(self, data: Any, key: str | None, in_codes: bool) -> Any:
        if isinstance(data, Mapping):
            if key == "users":
                return self._walk_users(data)
            return {
                self._text(str(k)): self._value(str(k), v, key, in_codes) for k, v in data.items()
            }
        if isinstance(data, list | tuple):
            if key == "users":
                return self._walk_user_list(data)
            return [self._walk(item, key, in_codes) for item in data]
        if isinstance(data, str):
            return self._text(data)
        return data

    def _value(self, key: str, value: Any, parent: str | None, in_codes: bool) -> Any:
        codes = in_codes or key == "action_codes"
        if key in SECRET_KEYS or (codes and key == "code"):
            return _hide(value)
        if key in CATEGORY_KEYS:
            return self._category(CATEGORY_KEYS[key], value)
        if key == "tag_names" and isinstance(value, Mapping):
            return {
                self._placeholder("karte", str(k)): f"Kartenname {i}"
                for i, k in enumerate(value, 1)
            }
        return self._walk(value, key, codes)

    def _category(self, kind: str, value: Any) -> Any:
        if isinstance(value, str):
            return self._placeholder(kind, value) if value else value
        if isinstance(value, Mapping):
            return {self._text(str(k)): self._category(kind, v) for k, v in value.items()}
        if isinstance(value, list | tuple):
            return [self._category(kind, item) for item in value]
        return value

    def _walk_users(self, users: Mapping[str, Any]) -> dict[str, Any]:
        result = {}
        for user_id, data in users.items():
            name = data.get("name", "") if isinstance(data, Mapping) else ""
            slug, label = self._user(str(user_id), str(name or ""))
            # Fester Hauptbenutzer o. Ä. ohne eigenen Namen: Kennung behalten
            new_id = slug if name else self._text(str(user_id))
            body = self._walk(data, None, False)
            if isinstance(body, dict) and name:
                body["name"] = label
            result[new_id] = body
        return result

    def _walk_user_list(self, users: list[Any] | tuple[Any, ...]) -> list[Any]:
        result = []
        for index, data in enumerate(users):
            name = data.get("name", "") if isinstance(data, Mapping) else ""
            body = self._walk(data, None, False)
            if isinstance(body, dict) and name:
                body["name"] = self._user(f"#{index}:{name}", str(name))[1]
            result.append(body)
        return result

    def _text(self, text: str) -> str:
        if text in self._exact:
            return self._exact[text]
        text = _PERSON.sub(lambda m: self._person(m.group(0)), text)
        for secret, placeholder in self._known_secrets():
            if secret in text:
                text = text.replace(secret, placeholder)
        for pattern, words, slug, label in self._patterns:
            text = _replace_words(text, pattern, words, slug, label)
        return text


def _hide(value: Any) -> Any:
    if isinstance(value, str):
        return HIDDEN if value else value
    if isinstance(value, Mapping):
        return {k: _hide(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_hide(v) for v in value]
    return value  # Zahlen und Wahrheitswerte („PIN vorhanden: ja“) bleiben


def _words(name: str) -> Iterable[str]:
    return re.findall(r"[^\W_]+", name)


def _word_pattern(words: Mapping[str, int]) -> re.Pattern[str]:
    # Ganzes Wort: kein Buchstabe davor oder danach – Unterstrich und Ziffern zählen als Grenze
    # (``handy_von_anna``), ein angehängtes „s“ auch („Annas Zimmer“)
    names = "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True))
    return re.compile(rf"(?<![^\W\d_])(?:{names})(?=s?(?![^\W\d_]))", re.IGNORECASE)


def _replace_words(
    text: str, pattern: re.Pattern[str], words: Mapping[str, int], slug: str, label: str
) -> str:
    def swap(match: re.Match[str]) -> str:
        found = match.group(0)
        number = words[found.lower()]
        return (slug if found.islower() else label).format(n=number)

    return pattern.sub(swap, text)


def pseudonymize(data: Any, person_names: Mapping[str, str] | None = None) -> Any:
    """Kurzform: ``data`` mit Platzhaltern statt echter Namen und Geheimnisse."""
    return Pseudonymizer(person_names=dict(person_names or {})).run(data)
