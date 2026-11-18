"""Karten, Anhänger und Schloss-Kennungen der Benutzer: anlernen, umbenennen, zuweisen,
deaktivieren, löschen.

Gespeichert beim Benutzer: ``tags`` (aktiv), ``tags_disabled`` (deaktiviert), ``tag_names``
(Name je Karte). Eine Karte gehört immer genau einem Benutzer.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..controls import is_random_uid, normalize_tag
from . import Change, copy_options, failed

OPT_USERS = "users"


def all_cards(users: Mapping[str, Any]) -> list[tuple[str, str, str, bool]]:
    """Alle Karten: (Karte, Benutzer-ID, Name, aktiv), sortiert nach Benutzer und Name."""
    rows: list[tuple[str, str, str, bool]] = []
    for uid, data in users.items():
        if not isinstance(data, Mapping):
            continue
        names = data.get("tag_names") if isinstance(data.get("tag_names"), Mapping) else {}
        assert isinstance(names, Mapping)
        rows.extend((t, uid, str(names.get(t, "")), True) for t in data.get("tags", []) or [])
        rows.extend(
            (t, uid, str(names.get(t, "")), False) for t in data.get("tags_disabled", []) or []
        )
    return sorted(
        rows,
        key=lambda r: (str(users[r[1]].get("name", r[1])).casefold(), r[2].casefold(), r[0]),
    )


def remove_card(users: dict[str, Any], tag: str) -> None:
    """Karte bei allen Benutzern entfernen (aktiv, deaktiviert, Name)."""
    for uid, data in list(users.items()):
        if not isinstance(data, Mapping):
            continue
        new = dict(data)
        new["tags"] = [t for t in new.get("tags", []) or [] if t != tag]
        disabled = [t for t in new.get("tags_disabled", []) or [] if t != tag]
        if disabled or "tags_disabled" in new:
            new["tags_disabled"] = disabled
        names = new.get("tag_names")
        if isinstance(names, dict):
            new["tag_names"] = {k: v for k, v in names.items() if k != tag}
        users[uid] = new


def put_card(users: dict[str, Any], tag: str, user_id: str, name: str, *, active: bool) -> None:
    """Karte einem Benutzer geben (vorher bei allen entfernen)."""
    remove_card(users, tag)
    data = dict(users[user_id])
    key = "tags" if active else "tags_disabled"
    data[key] = [*list(data.get(key, []) or []), tag]
    names = dict(data.get("tag_names") or {})
    if name:
        names[tag] = name
    data["tag_names"] = names
    users[user_id] = data


def tag_owner(tags: list[str], user_id: str | None, stored: Mapping[str, Any]) -> str | None:
    """Gehört eine dieser Karten schon einem anderen Benutzer? Dann dessen Name."""
    for other_id, other in stored.items():
        own = set(other.get("tags", []) or []) | set(other.get("tags_disabled", []) or [])
        if other_id != user_id and set(tags) & own:
            return str(other.get("name", other_id))
    return None


def add_card(options: Mapping[str, Any], data: Mapping[str, Any]) -> Change:
    """Neue Karte: ``data``: card (Nummer), user, name, active.

    Fehler: ``card_missing``, ``tag_taken`` (``details["conflict"]`` = Besitzer),
    ``tag_random`` (Zufallsnummer, z. B. Handy), ``user_missing``.
    """
    users: dict[str, Any] = dict(options.get(OPT_USERS, {}))
    tag = normalize_tag(data.get("card"))
    if not tag:
        return failed({"card": "card_missing"})
    if (owner := tag_owner([tag], None, users)) is not None:
        return failed({"card": "tag_taken"}, conflict=owner)
    if is_random_uid(tag):
        return failed({"card": "tag_random"}, conflict=tag)
    if data.get("user") not in users:
        return failed({"user": "user_missing"})
    put_card(
        users,
        tag,
        str(data["user"]),
        str(data.get("name") or "").strip(),
        active=bool(data.get("active", True)),
    )
    new = copy_options(options)
    new[OPT_USERS] = users
    return Change(options=new, item_id=tag)


def edit_card(options: Mapping[str, Any], tag: str, data: Mapping[str, Any]) -> Change:
    """Karte umbenennen, anderem Benutzer geben, (de)aktivieren oder löschen (``delete``)."""
    users: dict[str, Any] = dict(options.get(OPT_USERS, {}))
    row = next((r for r in all_cards(users) if r[0] == tag), None)
    if row is None:
        return failed({"base": "unknown_card"})
    if data.get("delete"):
        remove_card(users, tag)
    else:
        target = data.get("user") if data.get("user") in users else row[1]
        put_card(
            users,
            tag,
            str(target),
            str(data.get("name") or "").strip(),
            active=bool(data.get("active", True)),
        )
    new = copy_options(options)
    new[OPT_USERS] = users
    return Change(options=new, item_id=tag)
