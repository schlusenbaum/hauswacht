"""Auslöseregeln anlegen, ändern, löschen – für die Einstellungsseite (ADR 0011).

Eingabe ist die Regel in der Form des YAML-Editors (Meldergruppen per **Name**, siehe
``core.rules.to_editable``). Die Einstellungsseite schickt sie so – egal ob sie im Formular oder
als YAML bearbeitet wurde. Gespeichert wird die interne Form (Meldergruppen per ID).

Fehler:

- ``name``: ``rule_name_required`` / ``rule_name_taken``
- ``base``: ``rule_yaml_invalid`` mit dem Grund in ``details["message"]`` (Aufbau falsch)
- ``base``: ``rule_invalid`` mit den Fundstellen in ``details["findings"]`` (Regel könnte nie
  sinnvoll auslösen, z. B. leerer Schritt)
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from ..rules import Finding, RuleError, from_editable, parse_rules, validate_rule
from ..sensors import Zone, parse_zones, slugify
from . import Change, copy_options, failed

OPT_RULES = "rules"
OPT_PROFILES = "profiles"


def _finding_data(findings: Iterable[Finding]) -> list[dict[str, Any]]:
    return [{"code": f.code, "rule": f.rule, "step": f.step, "detail": f.detail} for f in findings]


def check_rule(
    options: Mapping[str, Any],
    rule_id: str | None,
    editable: Any,
    *,
    labels: Mapping[str, frozenset[str]],
) -> tuple[Change, Any]:
    """Regel prüfen, ohne zu speichern: ``(Change, Regel)``. Bei Erfolg ``Change.options`` =
    nur die Speicherform der Regel (``{"stored": …}``) und ``item_id`` = Regel-ID."""
    zones: dict[str, Zone] = parse_zones(options)
    rules = parse_rules(options)
    name = str(editable.get("name") or "").strip() if isinstance(editable, Mapping) else ""
    new_id = rule_id or slugify(name or "regel", existing=rules.keys())
    # Ohne Namen trotzdem prüfen (für den Satz beim Tippen) – gemeldet wird der Name danach
    parse_input = {**editable, "name": name or "…"} if isinstance(editable, Mapping) else editable
    try:
        rule, stored = from_editable(parse_input, zones, new_id)
    except RuleError as err:
        return failed({"base": "rule_yaml_invalid"}, message=str(err)), None
    if not name:
        return failed({"name": "rule_name_required"}), rule
    if any(r.name == rule.name and r.rule_id != new_id for r in rules.values()):
        return failed({"name": "rule_name_taken"}), rule
    problems = validate_rule(rule, zones, labels)
    if problems:
        return failed({"base": "rule_invalid"}, findings=_finding_data(problems)), rule
    return Change(options={"stored": stored}, item_id=new_id), rule


def save_rule(
    options: Mapping[str, Any],
    rule_id: str | None,
    editable: Any,
    *,
    labels: Mapping[str, frozenset[str]],
    profiles: Iterable[str] | None = None,
) -> Change:
    """Regel speichern. ``profiles``: in welchen Profilen sie gilt (``None`` = unverändert)."""
    if rule_id is not None and rule_id not in options.get(OPT_RULES, {}):
        return failed({"base": "unknown_rule"})
    checked, _rule = check_rule(options, rule_id, editable, labels=labels)
    if not checked.ok or checked.options is None or checked.item_id is None:
        return checked
    new_id = checked.item_id
    new = copy_options(options)
    stored = {k: dict(v) for k, v in options.get(OPT_RULES, {}).items()}
    stored[new_id] = checked.options["stored"]
    new[OPT_RULES] = stored
    if profiles is not None:
        chosen = set(profiles)
        all_profiles = {k: dict(v) for k, v in options.get(OPT_PROFILES, {}).items()}
        for profile_id, settings in all_profiles.items():
            current = [r for r in settings.get("rules", []) or [] if isinstance(r, str)]
            if profile_id in chosen and new_id not in current:
                settings["rules"] = [*current, new_id]
            elif profile_id not in chosen and new_id in current:
                settings["rules"] = [r for r in current if r != new_id]
        new[OPT_PROFILES] = all_profiles
    return Change(options=new, item_id=new_id)


def delete_rule(options: Mapping[str, Any], rule_id: str) -> Change:
    """Regel löschen – auch aus allen Profilen."""
    if rule_id not in options.get(OPT_RULES, {}):
        return failed({"base": "unknown_rule"})
    new = copy_options(options)
    new[OPT_RULES] = {k: v for k, v in options.get(OPT_RULES, {}).items() if k != rule_id}
    profiles = {k: dict(v) for k, v in options.get(OPT_PROFILES, {}).items()}
    for settings in profiles.values():
        if "rules" in settings:
            settings["rules"] = [r for r in settings["rules"] if r != rule_id]
    new[OPT_PROFILES] = profiles
    return Change(options=new, item_id=rule_id)
