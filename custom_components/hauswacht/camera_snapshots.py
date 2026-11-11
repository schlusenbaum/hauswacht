"""Alarmbilder speichern: einige Kamerabilder unter Medien/hauswacht.

Einziger Ort, an dem Hauswacht einen anderen Dienst als Sirene/Benachrichtigung aufruft –
und zwar nur ``camera.snapshot``: Das liest ein Bild und schaltet nichts.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_call_later
from homeassistant.util import dt as dt_util

from .core.sensor_types import SNAPSHOT_COUNT, SNAPSHOT_INTERVAL

_LOGGER = logging.getLogger(__name__)

CAMERA_DOMAIN = "camera"
SNAPSHOT_SERVICE = "snapshot"


def media_folder(hass: HomeAssistant) -> str:
    base = hass.config.media_dirs.get("local") or hass.config.path("media")
    return f"{base}/hauswacht"


@callback
def save_alarm_images(hass: HomeAssistant, camera: str, sensor: str) -> list[CALLBACK_TYPE]:
    """Sofort ein Bild, dann weitere im Abstand. Liefert die Abbruch-Funktionen der Timer."""
    folder = media_folder(hass)
    if not hass.config.is_allowed_path(folder):
        _LOGGER.warning("Alarmbilder: Ordner %s ist nicht freigegeben", folder)
        return []
    stamp = dt_util.now().strftime("%Y%m%d-%H%M%S")
    name = sensor.split(".", 1)[-1] or "alarm"

    async def _take(number: int) -> None:
        try:
            await hass.services.async_call(
                "camera",
                "snapshot",
                {"entity_id": camera, "filename": f"{folder}/{stamp}_{name}_{number + 1}.jpg"},
                blocking=True,
            )
        except Exception:
            _LOGGER.exception("Alarmbild von %s konnte nicht gespeichert werden", camera)

    def _later(number: int) -> Callable[[datetime], None]:
        @callback
        def _run(_now: datetime) -> None:
            hass.async_create_task(_take(number), f"hauswacht_snapshot_{number}")

        return _run

    hass.async_create_task(_take(0), "hauswacht_snapshot_0")
    return [
        async_call_later(hass, SNAPSHOT_INTERVAL * number, _later(number))
        for number in range(1, SNAPSHOT_COUNT)
    ]
