"""Sirenen eintragen und die echte Sirenenansteuerung freigeben."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from . import Change, copy_options, failed

OPT_SIRENS = "sirens"
OPT_HARDWARE = "sirens_hardware_enabled"
OPT_ALLOW_SWITCH = "sirens_allow_switch"
OPT_TONES = "siren_tones"
OPT_FIRE_TONE_OK = "siren_fire_tone_ok"
OPT_PROFILES = "profiles"
CONFIRM_HARDWARE = "confirm_hardware"


def save_sirens(options: Mapping[str, Any], data: Mapping[str, Any]) -> Change:
    """Sirenenliste, Freigabe und Experten-Schalter speichern.

    Fehlt ein Feld in ``data``, bleibt der gespeicherte Wert (der Assistent übergibt z. B. nur
    ``sirens``). Regeln:

    - Die **Freigabe** einschalten geht nur mit ``confirm_hardware`` – nie nebenbei.
    - Ohne Experten-Schalter fallen Schalter (``switch.…``) aus der Liste.
    - Töne, Brandton-Freigaben und Profile behalten nur noch eingetragene Sirenen.
    """
    was_enabled = bool(options.get(OPT_HARDWARE, False))
    enable = bool(data.get(OPT_HARDWARE, was_enabled))
    allow_switch = bool(data.get(OPT_ALLOW_SWITCH, options.get(OPT_ALLOW_SWITCH, False)))
    if enable and not was_enabled and not data.get(CONFIRM_HARDWARE):
        return failed({"base": "confirm_hardware_required"})
    raw = data[OPT_SIRENS] if OPT_SIRENS in data else options.get(OPT_SIRENS, [])
    sirens = sorted({str(s) for s in raw or []})
    if not allow_switch:
        sirens = [s for s in sirens if not s.startswith("switch.")]
    new = copy_options(options)
    new[OPT_SIRENS] = sirens
    new[OPT_HARDWARE] = enable
    new[OPT_ALLOW_SWITCH] = allow_switch
    new[OPT_TONES] = {k: v for k, v in dict(options.get(OPT_TONES, {})).items() if k in sirens}
    new[OPT_FIRE_TONE_OK] = [x for x in options.get(OPT_FIRE_TONE_OK, []) if x in sirens]
    profiles = {k: dict(v) for k, v in options.get(OPT_PROFILES, {}).items()}
    for settings in profiles.values():
        if "sirens" in settings:
            settings["sirens"] = [s for s in settings["sirens"] if s in sirens]
    new[OPT_PROFILES] = profiles
    return Change(options=new)


AUTO_TONE = "_auto"  # Ton je Sirene: Standard-Einbruchton
OPT_SIREN_TEST = "siren_test"


def save_siren_tone(  # noqa: PLR0913
    options: Mapping[str, Any],
    siren: str,
    tone: str,
    *,
    allow_fire: bool = False,
    confirm_fire: bool = False,
    smoke_detector: bool = False,
) -> Change:
    """Ton je Sirene. Brandtöne nur als Experten-Freigabe mit eigener Bestätigung – und nie für
    Sirenen mit eigenen Brandsensoren (Rauchmelder). Fehler wie im Dialog."""
    from ..siren_guard import is_fire_tone  # noqa: PLC0415

    if siren not in options.get(OPT_SIRENS, []):
        return failed({"base": "unknown_siren"})
    tone = str(tone or "").strip()
    fire = bool(tone) and tone != AUTO_TONE and is_fire_tone(tone)
    if fire and smoke_detector:
        return failed({"tone": "siren_tone_fire_detector"})
    if fire and not allow_fire:
        return failed({"tone": "siren_tone_fire"})
    if fire and not confirm_fire:
        return failed({"confirm_fire_tone": "siren_tone_fire_confirm"})
    tones = dict(options.get(OPT_TONES, {}))
    fire_ok = {s for s in options.get(OPT_FIRE_TONE_OK, []) if isinstance(s, str)}
    if tone in ("", AUTO_TONE):
        tones.pop(siren, None)
    else:
        tones[siren] = tone
    if fire:
        fire_ok.add(siren)
    else:
        fire_ok.discard(siren)
    new = copy_options(options)
    new[OPT_TONES] = tones
    new[OPT_FIRE_TONE_OK] = sorted(fire_ok)
    return Change(options=new, item_id=siren)


def save_siren_test_settings(
    options: Mapping[str, Any], reminder_months: Any, prewarn: bool
) -> Change:
    """Sirenentest: Erinnerung (Monate, 0 = aus) und Vorwarnung."""
    from ..siren_test import REMINDER_CHOICES  # noqa: PLC0415

    try:
        months = int(reminder_months or 0)
    except (TypeError, ValueError):
        return failed({"reminder_months": "invalid"})
    if months not in REMINDER_CHOICES:
        return failed({"reminder_months": "invalid"})
    new = copy_options(options)
    new[OPT_SIREN_TEST] = {"reminder_months": months, "prewarn": bool(prewarn)}
    return Change(options=new)
