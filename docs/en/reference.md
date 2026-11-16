# Reference

[Deutsch](../referenz.md) | **English**

Entity IDs apply to a Home Assistant instance that was set to **English** when Hauswacht was
added. On a German instance they are German (e.g. `switch.hauswacht_testmodus` instead of
`switch.hauswacht_test_mode`) – the [German reference](../referenz.md) lists them. Renaming an
entity later does not change its ID. For further areas, the area name comes after "hauswacht",
e.g. `alarm_control_panel.hauswacht_garage`.

## Entities

### Operation

| Entity | Purpose |
|---|---|
| `alarm_control_panel.hauswacht` | alarm panel: buttons of the profiles with an alarm panel button, disarm |
| `alarm_control_panel.hauswacht_all_areas` | only with several areas: "All areas" |
| `select.hauswacht_profile` | profile for the "Arm" buttons (armed: active profile) |
| `button.hauswacht_arm` | arm the selected profile |
| `button.hauswacht_arm_anyway` | arm the selected profile, bypass open sensors |
| `button.hauswacht_disarm_now` | disarm immediately, also during an alarm |
| `button.hauswacht_end_alarm` | only end the alarm, profile stays armed |
| `switch.hauswacht_test_mode` | test mode |

### State and diagnostics

| Entity | Purpose |
|---|---|
| `binary_sensor.hauswacht_open_sensors_in_sensor_groups` | "Open" as soon as a sensor of a sensor group is open; attributes `sensors`, `names` |
| `sensor.hauswacht_system_status` | `ok` · `degraded` (sensors failed) · `fault`; attributes `faulty_infrastructure`, `unavailable_sensors` |
| `sensor.hauswacht_last_siren_test` | last siren test; per siren date and "heard?" in the attributes |
| `sensor.hauswacht_radio_silence_observation` | recommendation for the maximum radio silence, longest gaps per sensor |
| `sensor.hauswacht_homecoming_observation` | number of evaluated homecomings; attributes `sources`, `recent`, `entry_times`, `door_proof` |
| `button.hauswacht_homecoming_report` | report of the homecoming observation as a message in Home Assistant (to download: card "Hauswacht Übersicht") |
| `sensor.hauswacht_test_card_simulated_sensors` | basis of the test card (hidden) |

### Profile settings (category configuration)

| Entity | Purpose |
|---|---|
| `select.hauswacht_edit_profile` | which profile the following entities show and change |
| `number.hauswacht_exit_delay`, `number.hauswacht_entry_delay` | delays |
| `number.hauswacht_alarm_reaction_time`, `number.hauswacht_alarm_cycles` | alarm reaction |
| `number.hauswacht_away_delay`, `number.hauswacht_door_proof_location_before_door` | automation |
| `select.hauswacht_disarm_on_arrival` | automation: Off, As before, With door proof (replaces the switch "Disarm on arrival" since 0.42) |
| `select.hauswacht_open_sensors_when_arming`, `select.hauswacht_unavailable_sensors_when_arming` | behaviour when arming |
| `select.hauswacht_siren_tone`, `select.hauswacht_siren_volume` | siren |
| `switch.hauswacht_silent_alarm`, `switch.hauswacht_tamper_triggers_alarm` | switches |
| `time.hauswacht_arm_automatically_at`, `time.hauswacht_disarm_automatically_at` | times |

## Attributes of the alarm panel

| Attribute | Meaning |
|---|---|
| `area`, `area_name` | area |
| `profile`, `profile_name` | active profile (ID, name) |
| `phase` | internal state |
| `changed_by` | who switched last, e.g. "Anna (Keypad hallway)" |
| `test_mode` | test mode active |
| `timer`, `timer_ends_at` | running delay and its end |
| `trigger_sensor`, `alarm_cycles` | triggering sensor, number of alarm cycles |
| `zones` | sensor groups with their actual sensors |
| `monitored_sensors` | sensors currently monitored while armed |
| `open_sensors`, `unavailable_sensors` | open or failed sensors of all sensor groups |
| `open_rule_sensors` | open sensors that only appear in trigger rules of the active profile |
| `bypassed_sensors`, `bypassed_until_closed` | bypassed sensors (until disarmed or until closed) |
| `last_contact` | last contact per sensor |
| `sirens_hardware_enabled` | real siren control enabled |
| `last_siren_decision` | which sirens were controlled on the last alarm, or why they were blocked |
| `code_failures`, `code_locked_until` | wrong entries, end of a running lockout |
| `areas` | only "All areas": state per area |

## Actions

| Action | Fields | Purpose |
|---|---|---|
| `hauswacht.arm` | `profile`, `confirm`, `code` | arm a profile, optionally confirming open sensors |
| `hauswacht.simulate_trigger` | `sensor` | test mode: trigger a sensor briefly |
| `hauswacht.simulate_state` | `sensor`, `state` (`on`, `off`, `unavailable`, `real`) | test mode: simulate a sensor state |
| `hauswacht.simulate_reset` | – | test mode: reset all simulations |
| `hauswacht.siren_test` | `siren`, `duration`, `volume`, `tone` | briefly test a real siren (administrators only) |
| `hauswacht.siren_test_result` | `siren`, `heard` | store the result of a siren test (administrators only) |
| `hauswacht.siren_test_stop` | – | stop a running siren test (administrators only) |
| `hauswacht.reset_code_lock` | – | reset wrong entries and lockout (administrators only) |

For cards there are also WebSocket commands:

| Command | Purpose |
|---|---|
| `hauswacht/overview` | [system overview](overview.md) including check hints (administrators only) |
| `hauswacht/homecoming/report` | homecoming report for download: `filename`, `markdown`, `csv` (administrators only) |
| `hauswacht/alarm/info` | [alarm card](dashboard.md#card-hauswacht-alarm): areas, profiles, PIN need and rights of the logged-in account |
| `hauswacht/alarm/action` | alarm card: `area`, `action` (`arm`, `disarm`, `end_alarm`), `profile`, `code`, `force`; answer `ok` or `error`, `message`, `can_force` |

All actions are directed at an alarm panel (`target: entity_id: alarm_control_panel.hauswacht`).
Disarming works with the standard action `alarm_control_panel.alarm_disarm`.

## Events

Hauswacht reports processes as the event **`hauswacht_event`**. The field `type` names the kind,
e.g.:

| `type` | When |
|---|---|
| `StateChanged` | state of the alarm panel changed |
| `ActivateReaction`, `StopReaction` | alarm reaction starts or ends |
| `ArmingAborted` | arming aborted |
| `SensorsBypassed` | sensors bypassed |
| `TamperDetected` | tampering |
| `SensorUnavailable` | monitored sensor failed |
| `InfrastructureFault`, `InfrastructureRecovered` | radio network/gateway failed or back |
| `RestartedDisarmed` | disarmed after a restart (setting "always disarmed", or profile deleted) |
| `RestoredAfterRestart` | restored after a restart (with `profile_id`, `entry_delay`, `alarm_was_active`) |
| `AlwaysActiveTriggered` | always-active sensor triggered |
| `ArmedByClosingDoor` | armed by closing the door |
| `AutoArmScheduled`, `AutoArmCancelled`, `AutoArmed`, `AutoArmSkipped`, `AutoArmFailed` | profile automation: arming scheduled, cancelled, done, skipped, failed (with `profile_id`, `reason`) |
| `AutoDisarmed`, `AutoDisarmSkipped` | profile automation: disarmed, or not (e.g. alarm running) |
| `ButtonPressed` | button pressed (with `control`, `press`, `profile`) |
| `LockIdentified`, `LockIgnored` | door lock: ID received (with `intent`, `identity`, `reason`) or not used (e.g. `unknown_id`) |
| `ArrivalNoted`, `DoorNoted` | "Disarm with door proof": arrival (with `persons`) or entry door (with `door`) detected while the profile is armed |
| `RuleStep`, `RuleFired`, `RuleExpired`, `RuleConditionsNotMet`, `OpenRuleSensors` | trigger rules |
| `InvalidCode`, `CodeLockReset` | wrong entry (with `failures`, `lock_seconds`), counter reset |
| `Panic`, `Emergency` | emergency key on the keypad |
| `SirenDecision`, `SirenTest` | siren decision (`action`: `activate`, `stop`, `stop_restored` = switch off after restart), steps of a siren test |
| `SensorSimulated` | test mode: sensor simulated |
| `NotificationSuppressed`, `SpeechSuppressed` | notification or announcement suppressed (e.g. test mode, quiet hours) |

Example trigger for your own automation:

```yaml
triggers:
  - trigger: event
    event_type: hauswacht_event
    event_data:
      type: TamperDetected
```
