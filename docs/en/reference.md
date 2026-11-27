# Reference

[Deutsch](../referenz.md) | **English**

Everything Hauswacht provides for your own automations, scripts and cards: **entities**,
**attributes of the alarm panel**, **events** and **actions**. If you first want to know *what to
use for what*, start with the cheat sheet **[Automations: what to use for what?](automations.md)**;
ready-made automations are under **[examples](examples.md)**.

> **Entity IDs** depend on the language Home Assistant was running in when Hauswacht was set up –
> that is why both are listed here. For **further areas** the area name follows "hauswacht",
> e.g. `alarm_control_panel.hauswacht_garage`. If you renamed an entity or it was called
> differently in an older version: what counts is what is shown under Settings → Devices &
> services → Entities.

## Entities

"Per area" = exists once for every [area](profiles.md#areas), otherwise once for the whole
system.

### Operation

| Entity (German) | Entity (English) | Per area | Purpose |
|---|---|---|---|
| `alarm_control_panel.hauswacht` | `alarm_control_panel.hauswacht` | yes | Alarm panel: buttons of the profiles with a panel button, disarm. States `disarmed`, `arming`, `armed_home`/`armed_away`/`armed_night`/`armed_vacation`/`armed_custom_bypass` (depending on the profile's button), `pending`, `triggered`. Attributes see [below](#attributes-of-the-alarm-panel) |
| `alarm_control_panel.hauswacht_alle` | `alarm_control_panel.hauswacht_all` | – | Only with several areas: "All areas"; attributes `areas` (state and profile per area), `test_mode` |
| `select.hauswacht_profil` | `select.hauswacht_profile` | yes | Profile for the "Arm" buttons; armed: the active profile |
| `button.hauswacht_scharf_schalten` | `button.hauswacht_arm` | yes | Arm the selected profile |
| `button.hauswacht_trotzdem_scharf_schalten` | `button.hauswacht_arm_anyway` | yes | Arm the selected profile, bypass open sensors |
| `button.hauswacht_unscharf_schalten` | `button.hauswacht_disarm_now` | yes | Disarm immediately, also during an alarm |
| `button.hauswacht_alarm_beenden` | `button.hauswacht_end_alarm` | yes | Only end the alarm, the profile stays armed |
| `switch.hauswacht_testmodus` | `switch.hauswacht_test_mode` | – | [Test mode](test-mode.md) |
| `switch.hauswacht_gastmodus` | `switch.hauswacht_guest_mode` | – | [Guest mode](profiles.md#guest-mode) for all areas; attribute `areas` with the end per area |
| `event.hauswacht_aktions_code` | `event.hauswacht_action_code` | – | Only with [action codes](control-devices.md#action-codes) with the action "event": event type = name of the code; attributes `keypad`, `test` |
| `sensor.hauswacht_<keypad>_anzeige` | `sensor.hauswacht_<keypad>_display` | – | Per [generic keypad](control-devices.md#keypad-generic): what the keypad should show – `disarmed`, `exit_delay`, `armed_home`/`armed_away`/`armed_night`/`armed_vacation`/`armed_custom_bypass`, `entry_delay`, `triggered`, `test_alarm`, `fire`. Attributes `keypad`, `area`, `profile`, `delay_ends`, `delay_seconds`, `test_mode`, `changed_by`, `buttons`, `last_result`, `last_result_at` |

### State and diagnostics

| Entity (German) | Entity (English) | Per area | Purpose |
|---|---|---|---|
| `binary_sensor.hauswacht_offene_sensoren` | `binary_sensor.hauswacht_open_sensors` | yes | `on` as soon as a sensor of a sensor group is open; attributes `sensors` (IDs), `names`, `tilted` (currently tilted) |
| `sensor.hauswacht_systemstatus` | `sensor.hauswacht_system_status` | – | `ok` · `degraded` (sensor failed) · `fault` (radio network/gateway faulty); attributes `faulty_infrastructure`, `unavailable_sensors` |
| `sensor.hauswacht_letzter_sirenentest` | `sensor.hauswacht_last_siren_test` | – | Last siren test; per siren date and "heard?" in the attributes |
| `sensor.hauswacht_funkstille_beobachtung` | `sensor.hauswacht_radio_silence_observation` | – | [Observation](observations.md): recommendation for the maximum radio silence, longest gaps per sensor |
| `sensor.hauswacht_heimkehr_beobachtung` | `sensor.hauswacht_homecoming_observation` | – | [Observation](observations.md): number of evaluated homecomings; attributes `sources`, `recent`, `entry_times`, `door_proof` |
| `button.hauswacht_heimkehr_bericht` | `button.hauswacht_homecoming_report` | – | Report of the homecoming observation as a notification in Home Assistant |
| `sensor.hauswacht_simulierte_sensoren` | `sensor.hauswacht_simulated_sensors` | – | Basis of the test card (hidden) |

### Profile settings (category configuration)

These entities show and change the settings **of the profile selected in
`select.hauswacht_edit_profile`** – handy for the card "Hauswacht Settings", rarely needed in
automations.

| Entity (German) | Entity (English) | Purpose |
|---|---|---|
| `select.hauswacht_profil_bearbeiten` | `select.hauswacht_edit_profile` | Which profile the following entities show |
| `number.hauswacht_ausgangsverzogerung` | `number.hauswacht_exit_delay` | Exit delay (s) |
| `number.hauswacht_eingangsverzogerung` | `number.hauswacht_entry_delay` | Entry delay (s) |
| `number.hauswacht_dauer_der_alarmreaktion` | `number.hauswacht_alarm_reaction_time` | Duration of the alarm reaction (s) |
| `number.hauswacht_alarmzyklen` | `number.hauswacht_alarm_cycles` | Maximum number of alarm cycles |
| `number.hauswacht_wartezeit_bei_abwesenheit` | `number.hauswacht_away_delay` | Automation: waiting time when everyone has left |
| `number.hauswacht_turbeleg_ortung_vor_der_tur` | `number.hauswacht_door_proof_location_before_door` | [On return](profiles.md#on-return): time window phone and door (since 0.61 the entity is called "On return: time window phone and door"; existing installations keep the ID) |
| `select.hauswacht_unscharf_bei_ruckkehr` | `select.hauswacht_disarm_on_arrival` | [On return](profiles.md#on-return): Nothing, Disarm only if armed automatically, Disarm with door proof, Disarm also after arming by hand, Let in (since 0.61 the entity is called "On return"; existing installations keep the ID) |
| `select.hauswacht_offene_sensoren_beim_scharfschalten` | `select.hauswacht_open_sensors_when_arming` | Behaviour with open sensors |
| `select.hauswacht_ausgefallene_sensoren_beim_scharfschalten` | `select.hauswacht_unavailable_sensors_when_arming` | Behaviour with failed sensors |
| `select.hauswacht_sirenenton` | `select.hauswacht_siren_tone` | Siren tone |
| `select.hauswacht_sirenenlautstarke` | `select.hauswacht_siren_volume` | Siren volume |
| `switch.hauswacht_stiller_alarm` | `switch.hauswacht_silent_alarm` | Silent alarm |
| `switch.hauswacht_sabotage_lost_alarm_aus` | `switch.hauswacht_tamper_triggers_alarm` | Tampering triggers an alarm |
| `switch.hauswacht_gekippte_fenster_erlaubt` | `switch.hauswacht_tilted_windows_allowed` | Tilted windows allowed – only if there are [sensors with tilt position](sensors.md#sensors-with-tilt-position-tilted) |
| `time.hauswacht_automatisch_scharf_um` | `time.hauswacht_arm_automatically_at` | Automation: arm at |
| `time.hauswacht_automatisch_unscharf_um` | `time.hauswacht_disarm_automatically_at` | Automation: disarm at |

## Attributes of the alarm panel

The alarm panel (`alarm_control_panel.hauswacht`, per area) carries the whole state of the system
in its attributes. For automations **`phase`** is the most important trigger.

| Attribute | Meaning | Example value |
|---|---|---|
| `phase` | State independent of the profile: `disarmed`, `arming` (exit delay), `armed`, `pending` (entry delay), `triggered` (**alarm**, reaction running), `alarm_hold` (alarm over, not yet acknowledged) | `armed` |
| `profile`, `profile_name` | Active profile (ID, name); disarmed: empty | `night`, `Night` |
| `area`, `area_name` | Area | `main`, `House` |
| `changed_by` | Who switched last (user and way) | `Anna (Keypad hallway)` |
| `test_mode` | Test mode on | `false` |
| `guest_mode`, `guest_until` | Guest mode on, end (empty = until switched off) | `true`, `2026-11-20T18:00:00+01:00` |
| `timer`, `timer_ends_at` | Running time (`exit_delay`, `entry_delay`, `reaction`) and its end | `entry_delay`, `…T22:31:05+01:00` |
| `trigger_sensor` | Sensor that triggered the alarm (or the entry delay) | `binary_sensor.front_door` |
| `alarm_cycles` | How often this alarm has triggered so far | `1` |
| `monitored_sensors` | Sensors currently monitored | `[…]` |
| `open_sensors`, `unavailable_sensors` | Open or failed sensors of all sensor groups | `["binary_sensor.bathroom_window"]` |
| `tilted_sensors` | Currently tilted [sensors with tilt position](sensors.md#sensors-with-tilt-position-tilted). If the profile allows tilted windows, they are not in `open_sensors` | `["sensor.bedroom_window_opening_state"]` |
| `open_rule_sensors` | Open sensors that only appear in trigger rules of the active profile | `[]` |
| `bypassed_sensors`, `bypassed_until_closed` | Bypassed sensors (until disarmed or until closed) | `[]` |
| `passage` | Running [passage](passage.md): `direction` (`in` coming in, `out` going out), `until` (end when going out), `by`, `doors` (doors used), `doors_allowed` (doors still allowed when going out), `sensors` (currently bypassed by the passage); otherwise empty | `{"direction": "out", "until": "…", …}` |
| `zones` | Sensor groups with their actual sensors | `{"Outside": […]}` |
| `last_contact` | Last contact per sensor | `{…}` |
| `sirens_hardware_enabled` | Real siren control released | `true` |
| `last_siren_decision` | Last siren decision (like the event [`SirenDecision`](#sirens)) | `{"action": "activate", …}` |
| `code_failures`, `code_locked_until` | Wrong entries, end of a running lockout | `2`, `null` |

### Example: automation when armed

`phase` is the simplest trigger for your own automations, because it does not depend on which
panel button a profile has. Which profile is armed is in `profile_name`.

**Lock the front door as soon as "Away" or "Holiday" is armed** (i.e. after the exit delay, when
everyone is outside):

```yaml
alias: Lock front door when Hauswacht armed
triggers:
  - trigger: state
    entity_id: alarm_control_panel.hauswacht
    attribute: phase
    to: armed
conditions:
  - condition: template
    value_template: >
      {{ state_attr('alarm_control_panel.hauswacht', 'profile_name') in ['Away', 'Holiday'] }}
actions:
  - action: lock.lock
    target:
      entity_id: lock.front_door
```

The profile names must be spelled exactly as in Hauswacht. Better **not** couple **unlocking**
automatically to disarming: whoever disarms by mistake would otherwise also have opened the door.
Many more ready-made automations – lights on alarm, camera image to the phone, shutters, status
light, heating while away – are under [examples](examples.md).

## Events

Hauswacht reports occurrences as the Home Assistant event **`hauswacht_event`**. The field
**`type`** names the kind, the other fields are listed in the tables below.

```yaml
triggers:
  - trigger: event
    event_type: hauswacht_event
    event_data:
      type: TamperDetected
actions:
  - action: notify.mobile_app_annas_phone
    data:
      message: "Tampering at {{ trigger.event.data.sensor_key }}"
```

Good to know:

- **Look for yourself:** Developer tools → Events → enter `hauswacht_event` under "Listen to
  events" → "Start listening" – then every action on the system shows its event with all fields.
- **Test mode:** all events also come **in test mode**. Whether it is on is shown by the
  attribute `test_mode` of the alarm panel; some events have their own field for it (`test_mode`,
  `test`). So always add the condition `test_mode: false` to your own alarm automations.
- **Area:** **every** event names its area: `area` (ID, `main` = main area, `all` = whole system,
  e.g. radio network, siren test or a control device for all areas) and `area_name` (display
  name, e.g. "Garage"). This way an automation reacts to one area only:

  ```yaml
  triggers:
    - trigger: event
      event_type: hauswacht_event
      event_data:
        type: TamperDetected
        area: garage
  ```

  For control devices (keypad, button, door lock, emergency key) `area` is the area of the
  **control device** – a control device "for all areas" reports `all`.
- **Sensors** are given as entity ID in `sensor_key` or as a list in `sensors`, `open_sensors` …;
  the display name is returned by `state_attr(…, 'friendly_name')`.
- Sets (e.g. `open_sensors`) come as a **list**.
- **Sensors with tilt position:** events with `sensor_key` additionally have `position` for these
  sensors – `open`, `tilted` or `closed` (see
  [sensors with tilt position](sensors.md#sensors-with-tilt-position-tilted)).

### State and alarm

*In addition in every event: `area`, `area_name` (see [above](#events)).*

| `type` | When | Fields |
|---|---|---|
| `StateChanged` | State of the alarm panel changed | `old`, `new` (values like `phase`), `cause` (reason, see below) |
| `ActivateReaction` | **Alarm starts** (or next alarm cycle) | `profile_id`, `cycle` (1, 2, …), `sensor_key` (trigger), `test_mode` |
| `StopReaction` | Alarm reaction ends (time over, disarmed or alarm ended) | `profile_id`, `test_mode` |
| `AlarmAcknowledged` | Alarm acknowledged with "End alarm", profile stays armed | `profile_id`, `bypassed_until_closed` (still open sensors, bypassed until closed) |
| `Rejected` | Switching refused | `reason` (`not_ready` = open/failed sensors, `not_disarmed` = already armed, `invalid_code`, `test_mode_change_requires_disarmed`), `open_sensors`, `unavailable_sensors` |
| `ConfirmationRequired` | Arming needs a confirmation ("arm anyway") | `open_sensors`, `unavailable_sensors` |
| `SensorsBypassed` | Sensors bypassed (e.g. "arm anyway") | `sensors` |
| `SensorsRestored` | Bypassed sensors closed again, monitored again | `sensors` |
| `ArmingAborted` | Arming aborted at the end of the exit delay (still open/failed) | `open_sensors`, `unavailable_sensors` |
| `VibrationCounted` | [Vibration](sensors.md#vibration-sensors) counted, but not yet enough for an alarm (false alarm protection) | `sensor_key`, `count` (so far in the time window), `needed`, `window` (seconds) |
| `TamperDetected` | Tampering reported | `sensor_key`, `state` (state of the system at that moment) |
| `AlwaysActiveTriggered` | [Always-active](sensors.md#always-active-sensors) sensor triggered | `sensor_key` |
| `ArmedByClosingDoor` | [Armed by closing the door](profiles.md#arm-by-closing-the-door) | – |
| `PassageGranted` | [Passage](passage.md) started, the system stays armed | `direction` (`in`/`out`), `door` (when coming in: the opened door), `path` (sensors on the way now free), `by` |
| `PassageDoorUsed` | Going out: this door is now the passage door | `door` |
| `PassageEnded` | Passage (or its way) over, sensors are monitored again | `restored` (monitored again), `still_open` (still open – free until closed) |
| `PassageDoorOpen` | Door still open after the passage – not monitored until it is closed | `doors` |
| `TestModeChanged` | Test mode on/off | `enabled` |

**Reasons (`cause`) in `StateChanged`:** `arm_requested` (armed), `exit_delay_elapsed` (exit
delay over), `disarm_requested` (disarmed), `entry_sensor` (entry door → entry delay),
`entry_delay_elapsed`, `instant_sensor`, `follower_sensor`, `tamper_24h_sensor`, `tamper`,
`instant_during_entry_delay`, `retrigger` (triggered again), `always_active`,
`reaction_time_elapsed` (→ `alarm_hold`), `alarm_acknowledged`, `exit_check_failed` (arming
aborted), `always_alarm_ended`, `restored` (after restart), `startup`, `passage` (entry delay
ended by a [passage](passage.md), stays armed).

### Restart

*In addition in every event: `area`, `area_name` (see [above](#events)).*

| `type` | When | Fields |
|---|---|---|
| `RestoredAfterRestart` | Restored after a restart | `profile_id`, `entry_delay`, `alarm_was_active` |
| `RestartedDisarmed` | Disarmed after a restart (setting "always disarmed" or profile deleted) | `previous_profile_id` |

### Profile automation and presence

*In addition in every event: `area`, `area_name` (see [above](#events)).*

`reason` names the occasion (in German, as stored): `Uhrzeit` (time), `Zeitplan` (schedule),
`alle weg` (everyone left), `Rückkehr` (arrival), `Rückkehr mit Türbeleg` (arrival with door
proof), `Neustart` (restart).

| `type` | When | Fields |
|---|---|---|
| `AutoArmScheduled` | Everyone left – arming after the waiting time planned (since 0.64.0b5 only while the system is disarmed) | `profile_id`, `minutes` |
| `AutoArmCancelled` | Planned arming cancelled (someone came back) | `profile_id` |
| `AutoArmed` | Armed automatically | `profile_id`, `reason` |
| `AutoArmSkipped` | Not armed (not disarmed, guest mode …) | `profile_id`, `reason`, possibly `guest_mode: true` |
| `AutoArmFailed` | Arming failed (e.g. open windows) | `profile_id`, `reason`, `details` |
| `AutoDisarmed` | Disarmed automatically | `profile_id`, `reason` |
| `AutoDisarmSkipped` | Not disarmed (e.g. alarm running, another profile armed) | `profile_id`, `reason` |
| `ArrivalNoted` | "Disarm with door proof": arrival detected, profile armed | `profile_id`, `persons` |
| `PhoneArrivalNoted` | [On return: let in](passage.md#let-in-by-phone): arrival detected (away for at least 5 minutes before), profile armed | `profile_id`, `persons` |
| `DoorNoted` | "Disarm with door proof": entry door detected | `profile_id`, `door` |
| `EntryDelayExtended` | [Approach](profiles.md#approach-extends-the-entry-delay): entry delay extended because a person from "On return" approached | `profile_id`, `seconds`, `normal`, `persons` |
| `ExitWaitStarted` | [Exit detection](passage.md#detect-going-out-without-a-pin-exit-detection): silent waiting time instead of the entry delay, because someone was verifiably home | `profile_id`, `door`, `seconds`, `persons` |
| `ExitDetected` | Exit detection: a person went out – the profile stays armed, the door is bypassed until closed | `profile_id`, `door`, `person` |
| `ExitLetThrough` | Exit detection: "Let through" via push – the profile stays armed | `profile_id`, `door`, `person` (empty) |

### Operation

*In addition in every event: `area`, `area_name` (see [above](#events)).*

| `type` | When | Fields |
|---|---|---|
| `InvalidCode` | Wrong PIN or unknown card | `failures` (number in a row), `lock_seconds` (lockout, 0 = none) |
| `CodeLockReset` | Wrong entries reset | `by`, `failures` |
| `MqttRetainedCommand` | A stored command (retain) to an [MQTT interface](control-devices.md#mqtt-interface) was ignored | `control` |
| `UnknownKeypad` | A [generic keypad](control-devices.md#keypad-generic) that is not set up in Hauswacht reported | `keypad` (ID it sent) |
| `ActionCode` | [Action code](control-devices.md#action-codes) entered | `name`, `action` (`event`, `arm`, `silent_emergency`), `control` (keypad), `test` |
| `ButtonPressed` | [Button](control-devices.md#button) pressed | `control`, `press` (`single`, `double`, `long`), `profile` (empty = press type not assigned) |
| `LockIdentified` | [Door lock](control-devices.md#door-lock-eg-nuki): ID received | `control`, `intent` (`UNLOCK`, `LOCK` or empty), `identity`, `reason` (`ok`, `not_by_person`, `no_id`) |
| `LockIgnored` | Door lock: ID not used | `control`, `intent`, `reason` (`unknown_id`, `disabled_id`) |
| `GuestMode` | [Guest mode](profiles.md#guest-mode) on/off | `on`, `until` (empty = until switched off), `by` |
| `Panic` | Emergency key with alarm | `control` |
| `Emergency` | Emergency key pressed (before the reaction) | `control`, `mode` (`off`, `silent`, `alarm`) |

### Faults

*In addition in every event: `area`, `area_name` (see [above](#events)).*

| `type` | When | Fields |
|---|---|---|
| `SensorUnavailable` | Monitored sensor failed | `sensor_key` |
| `InfrastructureFault` | Radio network or gateway faulty | `indicator` (entity reporting it), `armed` |
| `InfrastructureRecovered` | … fine again | `indicator`, `armed` |

### Trigger rules

*In addition in every event: `area`, `area_name` (see [above](#events)).*

| `type` | When | Fields |
|---|---|---|
| `RuleStep` | Step of a [trigger rule](trigger-rules.md) fulfilled | `sensor_key` |
| `RuleFired` | Rule completely fulfilled | `rule`, `name`, `sensor_key` |
| `RuleExpired` | Rule only partly fulfilled, time over | `rule`, `sensor_key` (first sensor) |
| `RuleConditionsNotMet` | Rule fulfilled, but conditions not – no alarm | `rule`, `sensor_key` |
| `ArmedWithGaps` | Armed, but not everything is monitored (see [note on arming](notifications.md)) | `bypassed` (bypassed because open), `unavailable` (unavailable, accepted), `rule_sensors` (open, only in rules) |
| `OpenRuleSensors` | Open sensors on arming that only appear in rules | `sensors` |

### Sirens

*In addition in every event: `area`, `area_name` (see [above](#events)).*

| `type` | When | Fields |
|---|---|---|
| `SirenDecision` | Hauswacht decided about sirens | `action` (`activate`, `stop`, `stop_restored` = off after restart), `sent` (sirens controlled), `blocked` (siren → reason: `test_mode`, `hardware_disabled`, `fire_lock`, `unknown_device`, `not_allowed_for_burglar`, `no_burglar_tone`, …) |
| `SirenTest` | Step of a [siren test](sirens.md) | `step` (`started`, `stopped`, `blocked`, `result`), `siren`, depending on the step `by`, `seconds`, `volume`, `reason`, `heard` |

### For troubleshooting

*In addition in every event: `area`, `area_name` (see [above](#events)).*

These events show internal processes. They rarely make good triggers for automations.

| `type` | When | Fields |
|---|---|---|
| `SensorSimulated` | Test mode: sensor simulated | `sensor_key`, `state` |
| `PresenceSimulated` | Test mode: presence of a person simulated | `person`, `state` |
| `NotificationSuppressed` | Notification suppressed (e.g. test mode) | `targets`, `title` |
| `SpeechSuppressed` | Announcement suppressed (e.g. test mode) | `event`, `entities` |
| `StartTimer` | Delay started | `kind` (`exit_delay`, `entry_delay`, `reaction`), `token`, `seconds` |
| `CancelTimer` | Delay cancelled | `token` |
| `Ignored` | Input without effect | `reason` (e.g. `already_disarmed`, `exit_delay`, `stale_timer`) |

## Actions

All actions are aimed at an alarm panel (`target: entity_id: alarm_control_panel.hauswacht`).

| Action | Fields | Purpose |
|---|---|---|
| `hauswacht.arm` | `profile` (name or ID), `confirm` (confirm open sensors), `code` | Arm a profile |
| `hauswacht.guest_mode` | `on`, `until` (point in time, empty = until switched off) | [Guest mode](profiles.md#guest-mode) on/off; target an area or "All" |
| `hauswacht.passage` | `code` (PIN or card; needed if PINs are set up) | [Passage](passage.md): during the entry delay let in, otherwise go out – stays armed |
| `hauswacht.simulate_trigger` | `sensor` | Test mode: trigger a sensor briefly |
| `hauswacht.simulate_state` | `sensor`, `state` (`on`, `off`, `tilted` – only sensors with tilt position, `unavailable`, `real`) | Test mode: simulate a sensor state |
| `hauswacht.simulate_reset` | – | Test mode: reset all simulations |
| `hauswacht.simulate_presence` | `person`, `state` (`home`, `away`, `away_no_proof`, `approaching`, `real`) | Test mode: simulate a person's presence for Hauswacht, see [testing presence](test-mode.md#testing-presence) |
| `hauswacht.skip_wait` | – | Test mode: end the "arm when all away" waiting time at once |
| `hauswacht.siren_test` | `siren`, `duration`, `volume`, `tone` | Briefly test a real siren (administrators only) |
| `hauswacht.siren_test_result` | `siren`, `heard` | Save the result of a siren test (administrators only) |
| `hauswacht.siren_test_stop` | – | Cancel a running siren test (administrators only) |
| `hauswacht.reset_code_lock` | – | Reset wrong entries and lockout (administrators only) |

Without a target entity:

| Action | Fields | Purpose |
|---|---|---|
| `hauswacht.keypad_input` | `keypad` (ID, name or display entity), `button` (`disarm`, `emergency` or an own button), `code`, `force` | Input of a [generic keypad](control-devices.md#keypad-generic); returns the result (`result`, `display`, `open_sensors`, `can_force`, `lock_seconds`). Automations, scripts and administrators only |

In addition the standard actions of the alarm panel: `alarm_control_panel.alarm_disarm` (disarm,
with `code` if a PIN is required) and `alarm_arm_home`/`away`/`night`/`vacation`/`custom_bypass`
(the profile with this button).

```yaml
action: hauswacht.arm
target:
  entity_id: alarm_control_panel.hauswacht
data:
  profile: Night
  confirm: false
```

For cards there are also WebSocket commands:

| Command | Purpose |
|---|---|
| `hauswacht/overview` | [System overview](overview.md) including check hints (administrators only) |
| `hauswacht/homecoming/report` | Homecoming report for download: `filename`, `markdown`, `csv` (administrators only) |
| `hauswacht/alarm/info` | [Alarm card](dashboard.md#card-hauswacht-alarm): areas, profiles, PIN requirement and rights of the logged-in account |
| `hauswacht/alarm/action` | Alarm card: `area`, `action` (`arm`, `disarm`, `end_alarm`), `profile`, `code`, `force`; answer `ok` or `error`, `message`, `can_force` |
| `hauswacht/alarm/guest` | Alarm card: guest mode `areas`, `on`, `until` |
