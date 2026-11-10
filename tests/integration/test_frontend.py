"""Integrationstests: Die Dashboard-Karte wird automatisch bereitgestellt."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant

from custom_components.hauswacht.frontend import CARD_FILE, DATA_KEY, async_register_card


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
    config = http.async_register_static_paths.await_args.args[0][0]
    assert config.url_path == f"/hauswacht/{CARD_FILE}"
    assert Path(config.path).is_file()
    add_js.assert_called_once_with(hass, f"/hauswacht/{CARD_FILE}?v=1.2.3")
    assert hass.data[DATA_KEY] is True


async def test_card_skipped_without_frontend(hass: HomeAssistant) -> None:
    await async_register_card(hass, "1.0.0")
    assert DATA_KEY not in hass.data


def test_card_file_defines_custom_element() -> None:
    source = (
        Path(__file__).resolve().parents[2]
        / "custom_components"
        / "hauswacht"
        / "frontend"
        / CARD_FILE
    ).read_text(encoding="utf-8")
    assert 'customElements.define("hauswacht-einstellungen-card"' in source
    assert "window.customCards" in source
