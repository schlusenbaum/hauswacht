"""Anlagenübersicht nach außen: WebSocket-Befehl für die Karte und Reparatur-Hinweise.

- ``hauswacht/overview`` (nur Administratoren) liefert die Übersicht samt Prüfhinweisen.
- Wichtige Prüfhinweise erscheinen zusätzlich unter Einstellungen → Reparaturen; sie werden beim
  Start (verzögert, bis die Melder ihren Zustand haben) und danach stündlich aktualisiert.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.event import async_call_later, async_track_time_interval

from .const import DOMAIN
from .overview import build_overview

if TYPE_CHECKING:
    from .runtime import HauswachtRuntime

WS_TYPE = f"{DOMAIN}/overview"
ISSUE_PREFIX = "check_"
ISSUE_TRANSLATION = "check_finding"
REFRESH = timedelta(hours=1)
FIRST_DELAY = 120  # s nach dem Start: Melder und Funkstille sollen erst ankommen
DATA_WS = f"{DOMAIN}_ws_registered"


def issue_id(finding: dict[str, Any]) -> str:
    key = re.sub(r"[^a-z0-9]+", "_", str(finding.get("key", "")).lower()).strip("_")
    return f"{ISSUE_PREFIX}{finding['code']}" + (f"_{key}"[:60] if key else "")


def _main(hass: HomeAssistant) -> HauswachtRuntime | None:
    for entry in hass.config_entries.async_loaded_entries(DOMAIN):
        runtime = getattr(entry, "runtime_data", None)
        if runtime is not None:
            return runtime  # type: ignore[no-any-return]
    return None


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): WS_TYPE})
@callback
def ws_overview(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    main = _main(hass)
    if main is None:
        connection.send_error(msg["id"], "not_loaded", "Hauswacht ist nicht geladen.")
        return
    connection.send_result(msg["id"], build_overview(main))


@callback
def async_register_websocket(hass: HomeAssistant) -> None:
    if hass.data.get(DATA_WS):
        return
    websocket_api.async_register_command(hass, ws_overview)
    hass.data[DATA_WS] = True


class IssueReporter:
    """Hält die Reparatur-Hinweise mit den wichtigen Prüfhinweisen in Einklang."""

    def __init__(self, hass: HomeAssistant, main: HauswachtRuntime) -> None:
        self.hass = hass
        self.main = main
        self._unsubs: list[CALLBACK_TYPE] = []

    @callback
    def async_start(self) -> None:
        self._unsubs.append(async_call_later(self.hass, FIRST_DELAY, self._refresh))
        self._unsubs.append(
            async_track_time_interval(self.hass, self._refresh, REFRESH, name="hauswacht_checks")
        )

    @callback
    def async_stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()

    @callback
    def _refresh(self, _now: datetime | None = None) -> None:
        self.refresh()

    @callback
    def refresh(self) -> list[str]:
        """Wichtige Hinweise anlegen, erledigte entfernen. Liefert die aktiven IDs."""
        findings = [f for f in build_overview(self.main)["findings"] if f["important"]]
        wanted = {issue_id(f): f for f in findings}
        registry = ir.async_get(self.hass)
        for (domain, existing), _issue in list(registry.issues.items()):
            if domain == DOMAIN and existing.startswith(ISSUE_PREFIX) and existing not in wanted:
                ir.async_delete_issue(self.hass, DOMAIN, existing)
        for issue, finding in wanted.items():
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                issue,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=ISSUE_TRANSLATION,
                translation_placeholders={"hint": finding["text"], "where": finding["where"]},
            )
        return sorted(wanted)
