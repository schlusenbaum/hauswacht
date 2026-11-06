"""Knöpfe: "Scharf schalten", "Trotzdem scharf schalten", "Unscharf schalten", "Alarm beenden".

"Trotzdem scharf schalten" bestätigt offene bzw. ausgefallene Sensoren – sofern das Profil
das erlaubt. Ist zum Scharfschalten ein PIN verlangt, funktionieren die Knöpfe nicht; dann
die Aktion hauswacht.arm mit code verwenden.

"Unscharf schalten" schaltet sofort unscharf – auch während eines Alarms. "Alarm beenden"
beendet nur den Alarm, das Profil bleibt scharf. Knöpfe können keinen PIN abfragen: Ist ein
PIN eingestellt, sind beide nicht verfügbar; dann über das Bedienfeld bedienen.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN
from .entity import HauswachtEntity
from .runtime import HauswachtConfigEntry


@dataclass(frozen=True)
class _ArmButton:
    key: str
    icon: str
    confirm: bool


BUTTONS = (
    _ArmButton("arm_selected", "mdi:shield-lock-outline", confirm=False),
    _ArmButton("arm_selected_confirmed", "mdi:shield-alert-outline", confirm=True),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HauswachtConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities(
        [
            *(HauswachtArmButton(entry, desc) for desc in BUTTONS),
            HauswachtDisarmButton(entry),
            HauswachtEndAlarmButton(entry),
            HomecomingReportButton(entry),
        ]
    )


class HauswachtArmButton(HauswachtEntity, ButtonEntity):
    def __init__(self, entry: HauswachtConfigEntry, description: _ArmButton) -> None:
        super().__init__(entry, description.key)
        self._description = description
        self._attr_translation_key = description.key
        self._attr_icon = description.icon

    async def async_press(self) -> None:
        if self.runtime.code_arm_required:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="button_needs_code"
            )
        self.runtime.arm_selected(confirmed=self._description.confirm)


class HauswachtDisarmButton(HauswachtEntity, ButtonEntity):
    """Sofort unscharf – auch während eines Alarms (ohne Zwischenschritt "Alarm beenden")."""

    _attr_translation_key = "disarm_now"
    _attr_icon = "mdi:shield-off-outline"

    def __init__(self, entry: HauswachtConfigEntry) -> None:
        super().__init__(entry, "disarm_now")

    @property
    def available(self) -> bool:
        return self.runtime.pin is None

    async def async_press(self) -> None:
        if self.runtime.pin is not None:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="button_needs_code_disarm"
            )
        self.runtime.disarm_now()


class HauswachtEndAlarmButton(HauswachtEntity, ButtonEntity):
    """Nur den Alarm beenden, das Profil bleibt scharf."""

    _attr_translation_key = "end_alarm"
    _attr_icon = "mdi:bell-off-outline"

    def __init__(self, entry: HauswachtConfigEntry) -> None:
        super().__init__(entry, "end_alarm")

    @property
    def available(self) -> bool:
        return self.runtime.pin is None

    async def async_press(self) -> None:
        if self.runtime.pin is not None:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="button_needs_code_disarm"
            )
        self.runtime.end_alarm()


class HomecomingReportButton(HauswachtEntity, ButtonEntity):
    """Erstellt den Bericht der Heimkehr-Beobachtung als Benachrichtigung in Home Assistant."""

    _attr_translation_key = "homecoming_report"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:file-chart-outline"

    def __init__(self, entry: HauswachtConfigEntry) -> None:
        super().__init__(entry, "homecoming_report")

    async def async_press(self) -> None:
        self.runtime.homecoming.create_report()
