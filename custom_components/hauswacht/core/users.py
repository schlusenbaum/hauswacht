"""Benutzer mit eigenem oder gemeinsamem PIN, Rechten, Gültigkeitszeitraum und Bedrohungs-PIN.

Rein und ohne Home Assistant.

- Mehrere Benutzer dürfen denselben PIN haben. Dann zeigt Hauswacht "gemeinsamer PIN (A, B)".
- Rechte: Eine Aktion ist erlaubt, wenn MINDESTENS EINER der zum PIN passenden Benutzer sie
  darf (sonst sperrt man sich mit einem gemeinsamen PIN leicht selbst aus).
- Rechte gelten wahlweise für alle Bereiche gleich (``rights: all``) oder je Bereich einzeln
  (``rights: per_area`` mit ``area_rights: {bereich: [arm, disarm, end_alarm]}``). Ein Bereich
  ohne Eintrag ist dann gesperrt. Ältere Einträge mit ``areas: [...]`` gelten weiter: die
  allgemeinen Rechte, aber nur in diesen Bereichen.
- Gäste: Außerhalb von "gültig von … bis …" gilt ein Benutzer als gesperrt.
- Bedrohungs-PIN: führt die Aktion ganz normal aus und löst heimlich einen Notruf aus.
  Er darf keinem normalen PIN gleichen (das prüft der Options-Dialog beim Speichern).
- Der bisherige einzelne PIN (vor 0.16) gilt weiter als Benutzer "Hauptbenutzer".
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from .pin import PinHash, verify_pin

LEGACY_USER_ID = "_main"
LEGACY_USER_NAME = "Hauptbenutzer"


class Action(StrEnum):
    ARM = "arm"
    DISARM = "disarm"
    END_ALARM = "end_alarm"


RIGHTS_ALL = "all"
RIGHTS_PER_AREA = "per_area"


@dataclass(frozen=True)
class User:
    user_id: str
    name: str
    pin: PinHash | None = None
    duress_pin: PinHash | None = None
    active: bool = True
    can_arm: bool = True
    can_disarm: bool = True
    can_end_alarm: bool = True
    ha_user: str | None = None
    valid_from: float | None = None  # Zeitstempel (UTC)
    valid_until: float | None = None
    areas: tuple[str, ...] = ()  # vorbereitet für Bereiche; leer = alle
    tags: tuple[str, ...] = ()  # RFID-Karten/-Anhänger (normalisierte IDs)
    # Rechte je Bereich (Bereich -> erlaubte Aktionen); None = allgemeine Rechte für alle
    area_rights: tuple[tuple[str, frozenset[Action]], ...] | None = None

    def may(self, action: Action) -> bool:
        return {
            Action.ARM: self.can_arm,
            Action.DISARM: self.can_disarm,
            Action.END_ALARM: self.can_end_alarm,
        }[action]

    def may_in(self, action: Action, area_id: str) -> bool:
        """Darf der Benutzer die Aktion in diesem Bereich?"""
        if self.area_rights is not None:
            return action in dict(self.area_rights).get(area_id, frozenset())
        return (not self.areas or area_id in self.areas) and self.may(action)

    def valid_at(self, now: float) -> bool:
        if not self.active:
            return False
        if self.valid_from is not None and now < self.valid_from:
            return False
        return not (self.valid_until is not None and now > self.valid_until)


@dataclass(frozen=True)
class Identity:
    """Ergebnis einer Ausweisprüfung (bzw. Handy eines bekannten Benutzers)."""

    kind: str  # "card" | "pin" | "phone"
    users: tuple[User, ...]
    duress: bool = False


@dataclass(frozen=True)
class PinMatch:
    users: tuple[User, ...] = ()  # gültige Benutzer mit diesem (normalen) PIN
    duress: tuple[User, ...] = ()  # gültige Benutzer mit diesem Bedrohungs-PIN
    blocked: tuple[User, ...] = ()  # PIN passt, Benutzer aber gesperrt bzw. abgelaufen

    @property
    def ok(self) -> bool:
        return bool(self.users or self.duress)


def _pin(data: Mapping[str, Any], prefix: str) -> PinHash | None:
    salt = data.get(f"{prefix}_salt")
    digest = data.get(f"{prefix}_digest")
    if isinstance(salt, str) and isinstance(digest, str) and salt and digest:
        return PinHash(salt=salt, digest=digest)
    return None


def _timestamp(value: Any) -> float | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value).timestamp()
    except ValueError:
        return None


def _area_rights(data: Mapping[str, Any]) -> tuple[tuple[str, frozenset[Action]], ...] | None:
    if data.get("rights") != RIGHTS_PER_AREA:
        return None
    raw = data.get("area_rights")
    if not isinstance(raw, Mapping):
        return ()
    result: list[tuple[str, frozenset[Action]]] = []
    for area_id, actions in raw.items():
        if not isinstance(actions, list):
            continue
        valid = frozenset(Action(a) for a in actions if a in {x.value for x in Action})
        result.append((str(area_id), valid))
    return tuple(result)


def _tags(value: Any) -> tuple[str, ...]:
    items = value if isinstance(value, list) else str(value or "").split(",")
    normalized = ("".join(ch for ch in str(i).upper() if ch.isalnum()) for i in items)
    return tuple(dict.fromkeys(t for t in normalized if t))


def match_tag(tag: str | None, users: Iterable[User], now: float) -> PinMatch:
    """Welche Benutzer haben diese RFID-Karte? (Gleiche Struktur wie beim PIN.)"""
    wanted = "".join(ch for ch in str(tag or "").upper() if ch.isalnum())
    if not wanted:
        return PinMatch()
    valid: list[User] = []
    blocked: list[User] = []
    for user in users:
        if wanted in user.tags:
            (valid if user.valid_at(now) else blocked).append(user)
    return PinMatch(users=tuple(valid), blocked=tuple(blocked))


def parse_users(options: Mapping[str, Any]) -> tuple[User, ...]:
    users: list[User] = []
    legacy = _pin(options, "pin")
    if legacy is not None:
        users.append(User(user_id=LEGACY_USER_ID, name=LEGACY_USER_NAME, pin=legacy))
    stored = options.get("users", {})
    if not isinstance(stored, Mapping):
        return tuple(users)
    for user_id, data in stored.items():
        if not isinstance(data, Mapping):
            continue
        areas = data.get("areas", [])
        users.append(
            User(
                user_id=str(user_id),
                name=str(data.get("name") or user_id),
                pin=_pin(data, "pin"),
                duress_pin=_pin(data, "duress"),
                active=bool(data.get("active", True)),
                can_arm=bool(data.get("can_arm", True)),
                can_disarm=bool(data.get("can_disarm", True)),
                can_end_alarm=bool(data.get("can_end_alarm", True)),
                ha_user=data.get("ha_user") if isinstance(data.get("ha_user"), str) else None,
                valid_from=_timestamp(data.get("valid_from")),
                valid_until=_timestamp(data.get("valid_until")),
                areas=tuple(a for a in areas if isinstance(a, str))
                if isinstance(areas, list)
                else (),
                tags=_tags(data.get("tags")),
                area_rights=_area_rights(data),
            )
        )
    return tuple(users)


def has_codes(users: Iterable[User]) -> bool:
    """Gibt es mindestens einen PIN? Dann verlangt das Bedienfeld einen PIN."""
    return any(u.pin is not None or u.duress_pin is not None for u in users)


def tag_conflicts(users: Iterable[User]) -> dict[str, list[str]]:
    """Karten, die mehreren Benutzern zugeordnet sind (Karte -> Namen)."""
    owners: dict[str, list[str]] = {}
    for user in users:
        for tag in user.tags:
            owners.setdefault(tag, []).append(user.name)
    return {tag: names for tag, names in owners.items() if len(names) > 1}


def match_pin(
    code: str | None,
    users: Iterable[User],
    now: float,
    verify: Callable[[str | None, PinHash | None], bool] = verify_pin,
) -> PinMatch:
    """Welche Benutzer passen zum eingegebenen PIN? (Rechenintensiv: im Hintergrund aufrufen.)"""
    if not code:
        return PinMatch()
    valid: list[User] = []
    duress: list[User] = []
    blocked: list[User] = []
    for user in users:
        if user.pin is not None and verify(code, user.pin):
            (valid if user.valid_at(now) else blocked).append(user)
        if user.duress_pin is not None and verify(code, user.duress_pin):
            (duress if user.valid_at(now) else blocked).append(user)
    return PinMatch(users=tuple(valid), duress=tuple(duress), blocked=tuple(blocked))


def allowed(users: Iterable[User], action: Action) -> bool:
    """Erlaubt, wenn mindestens einer der Benutzer die Aktion darf."""
    return any(u.may(action) for u in users)


def allowed_in(users: Iterable[User], action: Action, area_id: str) -> bool:
    """Erlaubt in diesem Bereich, wenn mindestens einer der Benutzer die Aktion dort darf."""
    return any(u.may_in(action, area_id) for u in users)


def label(users: Iterable[User]) -> str:
    names = sorted({u.name for u in users})
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    return f"gemeinsamer PIN ({', '.join(names)})"


def find_by_ha_user(users: Iterable[User], ha_user_id: str | None) -> User | None:
    if not ha_user_id:
        return None
    return next((u for u in users if u.ha_user == ha_user_id), None)


def pin_conflicts(
    code: str,
    users: Iterable[User],
    *,
    kind: str,
    exclude: str | None = None,
    verify: Callable[[str | None, PinHash | None], bool] = verify_pin,
) -> list[str]:
    """Namen der Benutzer, mit denen ``code`` kollidieren würde.

    kind="pin": ein neuer normaler PIN darf keinem Bedrohungs-PIN gleichen (auch nicht dem
    eigenen).
    kind="duress": ein neuer Bedrohungs-PIN darf keinem normalen und keinem anderen
    Bedrohungs-PIN gleichen. ``exclude`` = Benutzer, der gerade bearbeitet wird (sein eigener
    Bedrohungs-PIN wird ja ersetzt).
    """
    conflicts: list[str] = []
    for user in users:
        if kind == "pin":
            if user.duress_pin is not None and verify(code, user.duress_pin):
                conflicts.append(user.name)
        elif (user.pin is not None and verify(code, user.pin)) or (
            user.duress_pin is not None
            and user.user_id != exclude
            and verify(code, user.duress_pin)
        ):
            conflicts.append(user.name)
    return conflicts


def migrate_legacy_pin(options: Mapping[str, Any]) -> dict[str, Any]:
    """Optionen ab Version 3: Der alte einzelne PIN wird zum Benutzer "Hauptbenutzer"."""
    new = dict(options)
    salt = new.pop("pin_salt", None)
    digest = new.pop("pin_digest", None)
    if not (isinstance(salt, str) and isinstance(digest, str) and salt and digest):
        return new
    users = dict(new.get("users", {})) if isinstance(new.get("users"), Mapping) else {}
    user_id = "hauptbenutzer"
    while user_id in users:
        user_id += "_alt"
    users[user_id] = {"name": LEGACY_USER_NAME, "pin_salt": salt, "pin_digest": digest}
    new["users"] = users
    return new


def people_without_pin(
    users: Iterable[User], ha_users: Mapping[str, str], *, ignore: Iterable[str] = ()
) -> list[str]:
    """Wer kann am Bedienfeld nicht unscharf schalten, weil er keinen PIN hat?

    Nur relevant, wenn es überhaupt PINs gibt. ``ha_users``: ID -> Name der
    Home-Assistant-Benutzer. Ein Home-Assistant-Benutzer gilt als versorgt, wenn ein
    Hauswacht-Benutzer mit PIN mit ihm verknüpft ist oder seinen Namen trägt.
    """
    users = list(users)
    if not has_codes(users):
        return []
    skip = set(ignore)
    with_pin = [u for u in users if u.pin is not None]
    missing = [u.name for u in users if u.pin is None and u.user_id not in skip]
    linked = {u.ha_user for u in with_pin if u.ha_user}
    named = {u.name.casefold() for u in with_pin}
    pinless_names = {u.name.casefold() for u in users if u.pin is None}
    for ha_id, ha_name in ha_users.items():
        if ha_id in linked or ha_name.casefold() in named or ha_name.casefold() in pinless_names:
            continue
        missing.append(ha_name)
    return sorted(set(missing), key=str.casefold)
