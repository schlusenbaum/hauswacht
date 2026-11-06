"""Konstanten der Hauswacht-Integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "hauswacht"
NAME: Final = "Hauswacht"

STORAGE_VERSION: Final = 1
EVENT_HAUSWACHT: Final = "hauswacht_event"

# Optionen
OPT_PIN_SALT: Final = "pin_salt"
OPT_PIN_DIGEST: Final = "pin_digest"
OPT_CODE_ARM_REQUIRED: Final = "code_arm_required"
OPT_PROFILES: Final = "profiles"
OPT_ZONES: Final = "zones"
OPT_SENSOR_ROLES: Final = "sensor_roles"
OPT_STALE_AFTER_HOURS: Final = "stale_after_hours"
ROLE_AUTO: Final = "auto"

NOTIFICATION_RESTART: Final = "hauswacht_restart"
NOTIFICATION_ALARM: Final = "hauswacht_alarm"
