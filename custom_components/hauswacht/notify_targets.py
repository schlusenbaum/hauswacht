"""Empfänger für Benachrichtigungen – jedes Handy nur einmal.

Die Home-Assistant-App (mobile_app) bietet für jedes Handy zwei Wege:

- den Dienst ``notify.mobile_app_<gerät>`` – mit Knöpfen, Ersetzen/Wegräumen per ``tag`` und
  wichtigen Hinweisen,
- seit einiger Zeit zusätzlich eine Benachrichtigungs-Entität ``notify.<gerät>`` – nur Titel und
  Text.

In der Auswahl stand dasselbe Handy deshalb doppelt, einmal mit dem technischen Dienstnamen
(„2211133g xiaomi13“) und einmal mit dem Namen aus Home Assistant („Xiaomi 13 Christian“).
Hauswacht zeigt jetzt nur den Dienst – mit dem schönen Namen der Entität – und schickt auch an
früher gewählte App-Entitäten über den Dienst, damit Knöpfe und Aufräumen funktionieren.
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import slugify

from .core.speech import Candidate, is_speaker

NOTIFY_DOMAIN = "notify"
MOBILE_APP = "mobile_app"
SKIPPED_SERVICES = frozenset({"send_message", "notify", "persistent_notification"})


def app_service_of(hass: HomeAssistant, entity_id: str) -> str | None:
    """Zu einer App-Benachrichtigungs-Entität den passenden Dienst (ohne ``notify.``)."""
    entry = er.async_get(hass).async_get(entity_id)
    if entry is None or entry.platform != MOBILE_APP or entry.config_entry_id is None:
        return None
    config = hass.config_entries.async_get_entry(entry.config_entry_id)
    name = config.data.get("device_name") if config is not None else None
    if not isinstance(name, str) or not name:
        return None
    service = f"mobile_app_{slugify(name)}"
    return service if hass.services.has_service(NOTIFY_DOMAIN, service) else None


def app_entity_aliases(hass: HomeAssistant) -> dict[str, str]:
    """App-Entität -> Dienst, für alle Handys, die beides haben."""
    aliases: dict[str, str] = {}
    for state in hass.states.async_all(NOTIFY_DOMAIN):
        if (service := app_service_of(hass, state.entity_id)) is not None:
            aliases[state.entity_id] = service
    return aliases


def notify_choices(hass: HomeAssistant) -> list[dict[str, str]]:
    """Auswahl der Empfänger: ``{"id", "name", "kind"}`` – kind ``app`` oder ``text``.

    - Dienste (z. B. die App) mit Knöpfen; Handys mit dem Namen aus Home Assistant.
    - Benachrichtigungs-Entitäten anderer Integrationen (WhatsApp, Telegram, E-Mail …) – nur
      Titel und Text. Lautsprecher fehlen (die stehen unter Sprachausgabe), App-Entitäten auch
      (ihr Handy steht schon als Dienst da).
    """
    aliases = app_entity_aliases(hass)
    names = {
        service: (hass.states.get(entity_id).name if hass.states.get(entity_id) else service)  # type: ignore[union-attr]
        for entity_id, service in aliases.items()
    }
    services = hass.services.async_services_for_domain(NOTIFY_DOMAIN)
    choices = [
        {
            "id": s,
            "name": names.get(s) or s.removeprefix("mobile_app_").replace("_", " "),
            "kind": "app",
        }
        for s in services
        if s not in SKIPPED_SERVICES
    ]
    registry = er.async_get(hass)
    for state in hass.states.async_all(NOTIFY_DOMAIN):
        if state.entity_id in aliases:
            continue
        entry = registry.async_get(state.entity_id)
        candidate = Candidate(
            state.entity_id,
            entry.unique_id if entry else "",
            entry.translation_key if entry else None,
        )
        if not is_speaker(candidate):
            choices.append({"id": state.entity_id, "name": state.name, "kind": "text"})
    return sorted(choices, key=lambda c: c["name"].casefold())


def canonical_targets(hass: HomeAssistant, targets: list[str]) -> list[str]:
    """Früher gewählte App-Entitäten durch ihren Dienst ersetzen (ohne Doppelte)."""
    aliases = app_entity_aliases(hass)
    return list(dict.fromkeys(aliases.get(t, t) for t in targets))
