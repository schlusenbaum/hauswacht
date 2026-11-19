"""Fehler mit Zusatzdaten für Bedienteile."""

from __future__ import annotations

from typing import Any

from homeassistant.exceptions import ServiceValidationError


class ArmRefused(ServiceValidationError):
    """Scharfschalten abgelehnt – mit den Meldern, die es verhindert haben.

    ``confirmable``: Das Profil erlaubt "trotzdem scharf" nach Bestätigung.
    """

    def __init__(self, *, open_sensors: tuple[str, ...], confirmable: bool, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.open_sensors = open_sensors
        self.confirmable = confirmable
