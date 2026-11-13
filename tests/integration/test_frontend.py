"""Integrationstests: Die Dashboard-Karte wird automatisch bereitgestellt."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant

from custom_components.hauswacht.frontend import (
    CARD_FILE,
    CARD_FILES,
    DATA_KEY,
    EDITOR_FILE,
    TEST_CARD_FILE,
    async_register_card,
)


async def test_card_registered_once(hass: HomeAssistant) -> None:
    hass.config.components.add("frontend")
    http = MagicMock()
    http.async_register_static_paths = AsyncMock()
    with (
        patch.object(hass, "http", http),
        patch("homeassistant.components.frontend.add_extra_js_url") as add_js,
    ):
        await async_register_card(hass, "1.2.3")
        await async_register_card(hass, "1.2.3")  # zweiter Aufruf: nichts doppelt

    assert http.async_register_static_paths.await_count == 1
    configs = http.async_register_static_paths.await_args.args[0]
    assert [c.url_path for c in configs] == [f"/hauswacht/{name}" for name in CARD_FILES]
    assert all(Path(c.path).is_file() for c in configs)
    urls = [call.args[1] for call in add_js.call_args_list]
    assert urls == [f"/hauswacht/{name}?v=1.2.3" for name in CARD_FILES]
    assert hass.data[DATA_KEY] is True


async def test_card_skipped_without_frontend(hass: HomeAssistant) -> None:
    await async_register_card(hass, "1.0.0")
    assert DATA_KEY not in hass.data


def _source(name: str) -> str:
    folder = Path(__file__).resolve().parents[2] / "custom_components" / "hauswacht" / "frontend"
    return (folder / name).read_text(encoding="utf-8")


def test_test_card_only_simulates() -> None:
    source = _source(TEST_CARD_FILE)
    assert 'customElements.define("hauswacht-test-card"' in source
    # Die Testkarte ruft nur Hauswacht-Dienste und den Testmodus-Schalter auf – nie direkt
    # Sirenen. Der Sirenentest läuft über hauswacht.siren_test (Guard, nur Administratoren).
    assert '"siren"' not in source
    assert "siren." not in source
    assert "formatEntityName(" not in source


def test_card_file_defines_custom_element() -> None:
    source = _source(CARD_FILE)
    assert 'customElements.define("hauswacht-einstellungen-card"' in source
    assert "window.customCards" in source
    # Regression 0.15.0: formatEntityName lieferte je nach Version nur "entity"
    assert "formatEntityName(" not in source


def test_every_card_has_visual_editor() -> None:
    assert CARD_FILES[0] == EDITOR_FILE  # gemeinsamer Editor zuerst
    for name in CARD_FILES[1:]:
        source = _source(name)
        assert "static getConfigElement()" in source, name
        assert "static editorSchema(" in source, name
    assert 'customElements.define("hauswacht-card-editor"' in _source(EDITOR_FILE)


def test_alarm_card_editor_keeps_safety_out_of_card_config() -> None:
    """Unscharf/Alarm beenden nicht ausblendbar, PIN-Regeln nicht in der Karte."""
    source = _source("hauswacht-alarm-card.js")
    start = source.index("const DEFAULTS = {")
    defaults = source[start : source.index("};", start)]
    for forbidden in ("pin", "unscharf_knopf", "alarm_beenden", "end_alarm"):
        assert forbidden not in defaults, forbidden
