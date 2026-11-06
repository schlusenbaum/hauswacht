"""PIN-Verwaltung (reine Logik).

Der PIN wird nie im Klartext gespeichert, sondern als PBKDF2-Hash mit zufälligem Salt.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass

PIN_MIN_LENGTH = 4
PIN_MAX_LENGTH = 8
_ITERATIONS = 200_000


@dataclass(frozen=True)
class PinHash:
    salt: str  # hex
    digest: str  # hex


def is_valid_pin_format(pin: str) -> bool:
    """Nur Ziffern, 4 bis 8 Stellen (passt zu Keypads und Sprachassistenten)."""
    return pin.isdigit() and pin.isascii() and PIN_MIN_LENGTH <= len(pin) <= PIN_MAX_LENGTH


def _digest(pin: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, _ITERATIONS)


def hash_pin(pin: str, salt: bytes | None = None) -> PinHash:
    if not is_valid_pin_format(pin):
        raise ValueError("Ungültiges PIN-Format")
    salt = salt if salt is not None else secrets.token_bytes(16)
    return PinHash(salt=salt.hex(), digest=_digest(pin, salt).hex())


def verify_pin(pin: str | None, stored: PinHash | None) -> bool:
    """Prüft einen eingegebenen PIN. Ohne gespeicherten PIN ist jede Eingabe gültig."""
    if stored is None:
        return True
    if not pin or not pin.isdigit():
        return False
    try:
        salt = bytes.fromhex(stored.salt)
        expected = bytes.fromhex(stored.digest)
    except ValueError:
        return False  # beschädigter Eintrag: sichere Seite
    return hmac.compare_digest(_digest(pin, salt), expected)
