"""Gemeinsame Basis der Einstellungs-Entitäten für das bearbeitete Profil."""

from __future__ import annotations

from homeassistant.const import EntityCategory

from .entity import HauswachtEntity
from .runtime import HauswachtConfigEntry


class ProfileSettingEntity(HauswachtEntity):
    """Zeigt und ändert eine Einstellung des Profils aus "Profil bearbeiten".

    Nur im unscharfen Zustand verfügbar: Im scharfen Zustand darf niemand z. B. die
    Eingangsverzögerung hochdrehen.
    """

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry: HauswachtConfigEntry, key: str) -> None:
        super().__init__(entry, f"setting_{key}")
        self._key = key
        self._attr_translation_key = f"setting_{key}"

    @property
    def available(self) -> bool:
        return self.runtime.is_disarmed and self.runtime.edit_profile is not None

    @property
    def _profile_id(self) -> str:
        profile_id = self.runtime.edit_profile
        assert profile_id is not None
        return profile_id
