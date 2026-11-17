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
