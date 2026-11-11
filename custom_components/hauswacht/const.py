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
OPT_DURESS_NOTIFY: Final = "duress_notify"
OPT_USERS: Final = "users"
# Alarm und Bedrohung durchbrechen "Nicht stören" (kritische Hinweise)
OPT_CRITICAL_ALERTS: Final = "critical_alerts"
OPT_EVENTS: Final = "events"
OPT_REMINDER_PERSONS: Final = "reminder_persons"
OPT_REMINDER_PROFILE: Final = "reminder_profile"
OPT_REMINDER_DELAY: Final = "reminder_delay"
PUSH_ARM_FORCE_PREFIX: Final = "HAUSWACHT_ARM_FORCE_"
PUSH_ARM_RETRY_PREFIX: Final = "HAUSWACHT_ARM_RETRY_"
PUSH_ARM_NOW_PREFIX: Final = "HAUSWACHT_ARM_NOW_"
PUSH_ARM_TAG: Final = "hauswacht_arm"
# Dashboard-Knöpfe trotz PIN erlauben (PIN schützt dann nur Bedienfeld und Sprachassistenten)
OPT_BUTTONS_WITHOUT_PIN: Final = "buttons_without_pin"
MASTER_USER_ID: Final = "master"
ISSUE_PIN_COVERAGE: Final = "users_without_pin"
MASTER_USER_NAME: Final = "Master-PIN"
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
NOTIFICATION_ARM_HINT: Final = "hauswacht_arm_hint"
