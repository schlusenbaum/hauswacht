"""Dashboard-Karten von Hauswacht (Alarm, Einstellungen, Test, Übersicht): beim Start bereit.

Die Karten liegen als JavaScript-Dateien in diesem Ordner. Hauswacht stellt sie unter
``/hauswacht/…`` bereit und meldet sie beim Frontend an – ein Eintrag unter
"Ressourcen" ist nicht nötig.
"""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

CARD_FILE = "hauswacht-einstellungen-card.js"
TEST_CARD_FILE = "hauswacht-test-card.js"
OVERVIEW_CARD_FILE = "hauswacht-uebersicht-card.js"
ALARM_CARD_FILE = "hauswacht-alarm-card.js"
CARD_FILES = (CARD_FILE, TEST_CARD_FILE, OVERVIEW_CARD_FILE, ALARM_CARD_FILE)
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

    folder = Path(__file__).parent
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(f"{URL_BASE}/{name}", str(folder / name), cache_headers=False)
            for name in CARD_FILES
        ]
    )
    # Version im Pfad: Nach einem Update lädt der Browser die neue Karte statt der alten
    for name in CARD_FILES:
        add_extra_js_url(hass, f"{URL_BASE}/{name}?v={version}")
    hass.data[DATA_KEY] = True
    _LOGGER.debug("Karten %s bereitgestellt", ", ".join(CARD_FILES))
