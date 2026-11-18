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
# Gemeinsamer visueller Editor aller Karten
EDITOR_FILE = "hauswacht-editor.js"
CARD_FILES = (EDITOR_FILE, CARD_FILE, TEST_CARD_FILE, OVERVIEW_CARD_FILE, ALARM_CARD_FILE)
# Einstellungsseite in der Seitenleiste (ADR 0011) – nur bereitgestellt, nicht auf jeder Seite
PANEL_FILE = "hauswacht-panel.js"
PANEL_EDIT_FILE = "hauswacht-panel-edit.js"
PANEL_PROFILE_FILE = "hauswacht-panel-profile.js"
PANEL_ALARM_FILE = "hauswacht-panel-alarm.js"
PANEL_RULES_FILE = "hauswacht-panel-rules.js"
PANEL_DOCS_FILE = "hauswacht-panel-docs.js"
PANEL_PEOPLE_FILE = "hauswacht-panel-people.js"
PANEL_SYSTEM_FILE = "hauswacht-panel-system.js"
PANEL_FILES = (
    PANEL_FILE,
    PANEL_EDIT_FILE,
    PANEL_PROFILE_FILE,
    PANEL_ALARM_FILE,
    PANEL_RULES_FILE,
    PANEL_DOCS_FILE,
    PANEL_PEOPLE_FILE,
    PANEL_SYSTEM_FILE,
)
PANEL_URL_PATH = "hauswacht-settings"
PANEL_ELEMENT = "hauswacht-panel"
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
            for name in (*CARD_FILES, *PANEL_FILES)
        ]
    )
    # Version im Pfad: Nach einem Update lädt der Browser die neue Karte statt der alten
    for name in CARD_FILES:
        add_extra_js_url(hass, f"{URL_BASE}/{name}?v={version}")
    hass.data[DATA_KEY] = True
    _LOGGER.debug("Karten %s bereitgestellt", ", ".join(CARD_FILES))


async def async_register_panel(hass: HomeAssistant, version: str) -> None:
    """Einstellungsseite in der Seitenleiste anmelden (nur Administratoren)."""
    if getattr(hass, "http", None) is None or "frontend" not in hass.config.components:
        return
    from homeassistant.components import frontend, panel_custom  # noqa: PLC0415

    if PANEL_URL_PATH in hass.data.get(frontend.DATA_PANELS, {}):
        return
    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=PANEL_URL_PATH,
        webcomponent_name=PANEL_ELEMENT,
        sidebar_title="Hauswacht",
        sidebar_icon="mdi:shield-home",
        module_url=f"{URL_BASE}/{PANEL_FILE}?v={version}",
        require_admin=True,
        config={"version": version},
    )


def async_remove_panel(hass: HomeAssistant) -> None:
    """Einstellungsseite wieder entfernen (Entladen oder ausgeschaltet)."""
    if "frontend" not in hass.config.components:
        return
    from homeassistant.components import frontend  # noqa: PLC0415

    if PANEL_URL_PATH in hass.data.get(frontend.DATA_PANELS, {}):
        frontend.async_remove_panel(hass, PANEL_URL_PATH)
