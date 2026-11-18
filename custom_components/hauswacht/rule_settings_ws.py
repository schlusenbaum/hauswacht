"""Einstellungsseite: Auslöseregeln (ADR 0011).

- Liste der Regeln mit Satz, Profilen und ob sie sich im Formular bearbeiten lassen.
- ``hauswacht/settings/rule_check``: Regel prüfen, ohne zu speichern. Wandelt zwischen Formular
  (Objekt) und YAML-Text um, liefert den Satz („… dann innerhalb von 60 s … → sofort Alarm“) und
  die Probleme. Damit schaltet die Seite zwischen Formular und YAML um.

Formular geht nur für **einfache** Regeln (keine verschachtelten Ausdrücke, „Nicht, wenn
vorher …“ nur als „einer davon“) – komplexe Regeln bearbeitet man als YAML. Bedingungen
(``conditions``) zeigt das Formular nur an; ändern lassen sie sich im YAML.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util.yaml import dump, parse_yaml

from .const import DOMAIN
from .core.changes.rules import check_rule
from .core.rules import (
    DEFAULT_WITHIN,
    MAX_STEPS,
    MAX_UNLESS,
    MAX_WITHIN,
    Rule,
    describe_rule,
    parse_rules,
    profile_rule_ids,
    to_editable,
    wizard_editable,
)
from .core.sensor_types import MONITORED_DOMAINS
from .core.sensors import parse_zones
from .names import display_name
from .runtime import entities_by_label

WS_RULE_CHECK = f"{DOMAIN}/settings/rule_check"


def _finding_texts(lang: str) -> dict[str, str]:
    from .config_flow import FINDING_TEXTS_DE, FINDING_TEXTS_EN  # noqa: PLC0415

    return FINDING_TEXTS_DE if lang == "de" else FINDING_TEXTS_EN


def _lang(hass: HomeAssistant) -> str:
    return "de" if (hass.config.language or "").startswith("de") else "en"


def _sentence(hass: HomeAssistant, options: Mapping[str, Any], rule: Rule) -> str:
    zones = parse_zones(options)
    return describe_rule(
        rule,
        lambda e: display_name(hass, e),
        lambda z: zones[z].name if z in zones else z,
        _lang(hass),
    )


def _editable(options: Mapping[str, Any], rule: Rule) -> dict[str, Any]:
    zones = parse_zones(options)
    return to_editable(rule, lambda z: zones[z].name if z in zones else z)


def _yaml(data: Any) -> str:
    return str(dump(data))


def build_rule_settings(hass: HomeAssistant, main: Any) -> dict[str, Any]:
    options = main.entry.options
    profiles = options.get("profiles", {})
    rules = []
    for rule in parse_rules(options).values():
        editable = _editable(options, rule)
        rules.append(
            {
                "id": rule.rule_id,
                "name": rule.name,
                "text": _sentence(hass, options, rule),
                "profiles": [
                    pid for pid in profiles if rule.rule_id in profile_rule_ids(options, pid)
                ],
                "ui": wizard_editable(rule),
                "rule": editable,
                "yaml": _yaml(editable),
            }
        )
    sensors = [
        {"id": s.entity_id, "name": display_name(hass, s.entity_id)}
        for s in hass.states.async_all(list(MONITORED_DOMAINS))
    ]
    return {
        "rules": rules,
        "rule_choices": {
            "groups": [z.name for z in parse_zones(options).values()],
            "profiles": [
                {"id": pid, "name": data.get("name", pid)} for pid, data in profiles.items()
            ],
            "sensors": sorted(sensors, key=lambda s: str(s["name"]).casefold()),
            "results": ["alarm", "entry_delay", "notify"],
        },
        "rule_limits": {
            "steps": MAX_STEPS,
            "within": MAX_WITHIN,
            "default_within": DEFAULT_WITHIN,
            "unless": MAX_UNLESS,
        },
    }


def check(hass: HomeAssistant, main: Any, msg: Mapping[str, Any]) -> dict[str, Any]:
    """Regel aus Objekt oder YAML prüfen und in beide Formen bringen.

    Die Prüftexte sind dieselben wie im Dialog."""
    options = main.entry.options
    lang = _lang(hass)
    raw: Any = msg.get("rule")
    if msg.get("yaml") is not None:
        try:
            raw = parse_yaml(str(msg["yaml"]))
        except HomeAssistantError as err:
            prefix = "YAML fehlerhaft" if lang == "de" else "YAML error"
            return {
                "ok": False,
                "parsed": False,
                "errors": {"base": "rule_yaml_invalid"},
                "messages": [f"{prefix}: {err}"],
            }
    change, rule = check_rule(
        options, msg.get("rule_id") or None, raw, labels=entities_by_label(hass)
    )
    result: dict[str, Any] = {
        "ok": change.ok,
        "parsed": rule is not None,
        "errors": dict(change.errors),
        "messages": [],
    }
    if "message" in change.details:
        result["messages"].append(str(change.details["message"]))
    texts = _finding_texts(lang)
    for finding in change.details.get("findings", []):
        result["messages"].append(
            texts.get(finding["code"], finding["code"]).format(
                rule=finding["rule"], step=finding["step"] or "", detail=finding["detail"]
            )
        )
    if rule is not None:
        editable = _editable(options, rule)
        result.update(
            rule=editable,
            yaml=_yaml(editable),
            text=_sentence(hass, options, rule),
            ui=wizard_editable(rule),
        )
    return result


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_RULE_CHECK,
        vol.Optional("rule_id"): vol.Any(str, None),
        vol.Optional("rule"): vol.Any(dict, None),
        vol.Optional("yaml"): vol.Any(str, None),
    }
)
@callback
def ws_rule_check(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    from .settings_ws import _main  # noqa: PLC0415

    main = _main(hass)
    if main is None:
        connection.send_error(msg["id"], "not_loaded", "Hauswacht ist nicht geladen.")
        return
    connection.send_result(msg["id"], check(hass, main, msg))
