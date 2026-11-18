# Automations: what to use for what?

[Deutsch](../automationen.md) | **English**

A cheat sheet for your own automations: for every occasion it says **which trigger** to use and
why. All details (every field, every entity) are in the **[reference](reference.md)**,
ready-made automations under **[examples](examples.md)**.

The examples use the alarm panel `alarm_control_panel.hauswacht` – with [areas](profiles.md#areas)
use the one of the respective area.

## Rules of thumb

1. **For states, the attribute `phase` of the alarm panel** – it is unambiguous, does not depend
   on the profile or its button and is correct after a restart too.
2. **For occurrences, the event `hauswacht_event`** – things that have no state: wrong PIN,
   tampering, button, action code, failure.
3. **Always the condition "test mode off"** in automations that do something real:

   ```yaml
   conditions:
     - condition: state
       entity_id: alarm_control_panel.hauswacht
       attribute: test_mode
       state: false
   ```

4. **Never switch sirens yourself** – Hauswacht does that, with fire lock and test mode lock.

## I want to react when …

### Armed, disarmed, alarm

| … | Use | Note |
|---|---|---|
| an **alarm starts** | attribute `phase` → `triggered` | More robust than the event `ActivateReaction`; the triggering sensor is in `trigger_sensor` |
| an alarm is **over** (reaction time elapsed) | `phase` → `alarm_hold` | Not yet acknowledged – the profile is still armed |
| an alarm has **ended** (in any way) | `phase` **from** `triggered`/`alarm_hold` **to** `disarmed` or `armed` | "End alarm" leads to `armed`, "disarm" to `disarmed` |
| the system is **armed** (any profile) | `phase` → `armed` | Only **after** the exit delay – everyone is outside |
| a **specific profile** is armed | `phase` → `armed` + condition `profile_name` | Profile name exactly as in Hauswacht |
| someone **arms** (exit delay starts) | `phase` → `arming` | End in `timer_ends_at` |
| someone **comes home** (entry delay) | `phase` → `pending` | E.g. hallway light on; end in `timer_ends_at` |
| the system was **disarmed** | `phase` → `disarmed` | `from: pending` = when coming home; who, is in `changed_by` |
| every **state change** with reason | event `StateChanged` | `old`, `new`, `cause` |
| arming was **refused** | event `Rejected` | `reason`, `open_sensors` |
| arming was **aborted** at the end of the exit delay | event `ArmingAborted` | sensors still open in `open_sensors` |

### Tampering, faults, emergency

| … | Use | Note |
|---|---|---|
| **tampering** is reported | event `TamperDetected` | sensor in `sensor_key`; also comes when disarmed |
| a **sensor fails** | event `SensorUnavailable` | or `sensor.hauswacht_system_status` → `degraded` |
| the **radio network/gateway** is faulty | event `InfrastructureFault` (`InfrastructureRecovered` = fine again) | or system status → `fault` |
| a **wrong PIN** was entered | event `InvalidCode` | `failures`, `lock_seconds` (lockout) |
| the **emergency key** was pressed | event `Emergency` | `mode`: `off`, `silent`, `alarm` |
| an **always-active sensor** triggered (e.g. water) | event `AlwaysActiveTriggered` | `sensor_key` |

### Operation and automation

| … | Use | Note |
|---|---|---|
| an **action code** was entered | entity `event.hauswacht_action_code` (event type = name of the code) | Or event `ActionCode` with `name` – see [action codes](control-devices.md#action-codes) |
| a **button** was pressed | event `ButtonPressed` | `control` (name of the button), `press` |
| **guest mode** turns on or off | attribute `guest_mode` or entity `switch.hauswacht_guest_mode` | End in `guest_until`; event `GuestMode` with `by` |
| **test mode** turns on or off | entity `switch.hauswacht_test_mode` or attribute `test_mode` | |
| the **profile automation** armed | event `AutoArmed` | `reason`: `Uhrzeit` (time), `Zeitplan` (schedule), `alle weg` (everyone left) … |
| the profile automation could **not** | event `AutoArmFailed` or `AutoArmSkipped` | `reason`, `details`; `guest_mode: true` = because of guest mode |
| **windows are open** (e.g. hint when leaving) | entity `binary_sensor.hauswacht_open_sensors` | names in the attribute `names` |
| a window is **tilted** ([tilt position](sensors.md#sensors-with-tilt-position-tilted)) | panel attribute `tilted_sensors` | Even if the profile allows tilted; in events field `position` |

## I want to do something …

| … | Use |
|---|---|
| **arm** (a specific profile) | action `hauswacht.arm` with `profile` (and `confirm: true` for "arm anyway") |
| **disarm** | action `alarm_control_panel.alarm_disarm` (with `code` if a PIN is required) |
| **end the alarm**, profile stays armed | `button.press` on `button.hauswacht_end_alarm` |
| **guest mode** on until … | action `hauswacht.guest_mode` with `on: true`, `until` |
| name **the sensor** in a message | `{{ state_attr(state_attr('alarm_control_panel.hauswacht', 'trigger_sensor'), 'friendly_name') }}` |
| **know who** switched | attribute `changed_by`, e.g. "Anna (Keypad hallway)" |

## Common pitfalls

- **Panel state instead of `phase`:** `armed_night`, `armed_away` … depend on the profile's
  button; a profile without a button is `armed_custom_bypass`. `phase` is always `armed`.
- **`triggered` of the alarm panel** also applies during `alarm_hold` – whoever wants to
  distinguish "alarm running" from "alarm over, not acknowledged" uses `phase`.
- **Entity IDs** depend on the language at setup (`switch.hauswacht_testmodus` or
  `switch.hauswacht_test_mode`) – if in doubt, check under Settings → Entities.
- **Events also come in test mode** – without the test mode condition the trial run switches on
  lights and starts camera recordings.
- **Several areas:** every event has `area` (e.g. `garage`, `main`, `all` for the whole system) –
  add it to the trigger under `event_data`; for states use the alarm panel of the area.
- **Look for yourself:** Developer tools → Events → listen to `hauswacht_event` → "Start
  listening" shows every event with all fields; Developer tools → States shows the attributes of
  the alarm panel.
