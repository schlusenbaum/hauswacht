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
OPT_INFRASTRUCTURE: Final = "infrastructure"
OPT_SIRENS: Final = "sirens"
OPT_SIRENS_HARDWARE_ENABLED: Final = "sirens_hardware_enabled"
OPT_NOTIFY_SYSTEM: Final = "notify_system"
OPT_NOTIFY_IN_TEST_MODE: Final = "notify_in_test_mode"
OPT_PUSH_DISARM: Final = "push_disarm"
# "Alarm beenden" (Sirene aus, bleibt scharf) auch bei eingestelltem PIN ohne PIN erlauben
OPT_END_ALARM_WITHOUT_PIN: Final = "end_alarm_without_pin"
OPT_HOMECOMING_OBSERVE: Final = "homecoming_observe"
OPT_HOMECOMING_PERSONS: Final = "homecoming_persons"

# Aktions-Knopf in der Push-Benachrichtigung (Home-Assistant-App)
PUSH_ACTION_EVENT: Final = "mobile_app_notification_action"
PUSH_ACTION_PREFIX: Final = "HAUSWACHT_DISARM_"
PUSH_TAG: Final = "hauswacht"

NOTIFICATION_RESTART: Final = "hauswacht_restart"
NOTIFICATION_ALARM: Final = "hauswacht_alarm"
NOTIFICATION_FAULT: Final = "hauswacht_fault"
