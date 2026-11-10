"""Dashboard-Karte "Hauswacht Einstellungen": wird beim Start automatisch bereitgestellt.

Die Karte liegt als JavaScript-Datei in diesem Ordner. Hauswacht stellt sie unter
``/hauswacht/…`` bereit und meldet sie beim Frontend an – ein Eintrag unter
"Ressourcen" ist nicht nötig.
"""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

CARD_FILE = "hauswacht-einstellungen-card.js"
URL_BASE = "/hauswacht"
DATA_KEY = "hauswacht_frontend_registered"


async def async_register_card(hass: HomeAssistant, version: str) -> None:
    """Einmal pro Home-Assistant-Start; ohne Frontend (z. B. in Tests) still überspringen."""
    if hass.data.get(DATA_KEY) or getattr(hass, "http", None) is None:
        return
    if "frontend" not in hass.config.components:
        return
    from homeassistant.components.frontend import add_extra_js_url  # noqa: PLC0415
    from homeassistant.components.http import StaticPathConfig  # noqa: PLC0415

    path = Path(__file__).parent / CARD_FILE
    await hass.http.async_register_static_paths(
        [StaticPathConfig(f"{URL_BASE}/{CARD_FILE}", str(path), cache_headers=False)]
    )
    # Version im Pfad: Nach einem Update lädt der Browser die neue Karte statt der alten
    add_extra_js_url(hass, f"{URL_BASE}/{CARD_FILE}?v={version}")
    hass.data[DATA_KEY] = True
    _LOGGER.debug("Karte %s bereitgestellt", CARD_FILE)
