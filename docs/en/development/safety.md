# Safety rules

[Deutsch](../../entwicklung/safety.md) | **English**

These rules are binding. They must not be simplified to make the implementation easier. Every
rule is covered by tests.

## Sirens

Implementation: `custom_components/hauswacht/core/siren_guard.py`
Tests: `tests/core/test_siren_guard.py`, `tests/core/test_static_safety.py`, `tests/integration/test_reactions.py`

| No. | Rule | Reason |
|---|---|---|
| S1 | test mode active → no siren commands at all | a mistake during a test must not cause a real alarm |
| S2 | hardware release off → no switch-on command. Default after installation: **off**. Switching off its own sirens (S5) stays allowed (from 0.46) | sirens only after a deliberate release; switching off is the safe direction |
| S3 | fire **active** at any sensor, or **unclear** at a registered siren → no burglar activation | the fire alarm has priority, no confusing burglar tone during an evacuation |
| S4 | fire **active** at any sensor, or **unclear** at a registered siren → not a single switch-off command | a stop command could silence a local fire alarm (cannot be ruled out) |
| S5 | switching off only for devices Hauswacht activated itself | other alarms are never affected |
| S6 | fire tones (`fire`, `fire_panic`) are forbidden for burglar alarms | clear distinction between the kinds of alarm |
| S7 | the running time is limited to the device's maximum duration; this is **never changed** | the device value can affect the fire behaviour |
| S8 | siren services are only called in the siren executor | one single, verifiable path |
| S9 | other switch-off scripts (e.g. a script that switches off all smoke detectors) are never used | would end a fire alarm |
| S10 | send tone, volume and duration only if the siren supports them; missing burglar tone → another burglar tone, never a fire tone; fire tones only → no control; exception from 0.41: expert release of a configured tone, never on smoke detectors | rejected commands would leave the siren silent |
| S11 | smoke detector without tone selection → no burglar control | its default tone is usually the fire tone |
| S12 | siren without duration **and** without switching off → no control; siren without switching off → no switch-off command | Hauswacht must be able to limit every sound itself |
| S13 | end of the reaction time and disarming → switch off own sirens. If the fire lock prevented this, it is retried every minute until the guard allows it | sirens without their own running time would otherwise never go quiet |
| S14 | siren test: same path as an alarm (S1–S12 apply); in addition only disarmed, one siren, at most 10 s, administrators only; arming locked meanwhile | checking without a special path where the rules do not apply |
| S15 | sirens switched on by Hauswacht and not yet switched off are saved. After a restart they are switched off (after startup, a second time after the startup phase if still "on") – according to S1, S4, S5; never sirens a new alarm uses by then (from 0.46) | sirens without their own running time would otherwise never go quiet after a restart, not even when disarming |

### Implementation (from 0.5.0)

- `siren_executor.py` is the only file that calls siren services; a static test checks this via
  the syntax tree.
- From 0.40, experts can add switches as sirens. `switch.turn_on`/`turn_off` are also called
  exclusively by the executor – after the same guard (static test). A switch counts as a siren
  without tone, volume and duration.
- From 0.41, experts can release the configured tone of a siren as a fire tone (exception to S10,
  separate confirmation). The guard only allows this for exactly this tone and never for devices
  with their own fire indicators; the fire lock is not affected by it.
- The wizard "Create siren from switch" only creates a `switch_as_x` helper and switches nothing;
  the helper wizard for sensors only creates `threshold` helpers (static test).
- Fire indicators of a registered siren are detected via the device: binary sensors with device
  class smoke, gas, CO or heat, and test button sensors (`…_test`). Disabled indicators count as
  "unclear".
- Sensors without a registered siren only count if they **actively** report fire; a failed
  sensor somewhere does not lock the burglar sirens permanently.

### What does "unclear" mean?

The fire indicator of a device (e.g. its smoke binary sensor or test button sensor) is
`unavailable` or `unknown`. Hauswacht then cannot prove that there is no fire and behaves as with
an active fire.

### Known limits

- Many Zigbee sirens report `assumed_state`. Home Assistant then **cannot confirm** that a siren
  is actually audible. The interface therefore only shows "command sent".
- Battery-powered devices can receive commands with a delay. This is measured and documented in
  the first released practical test.
- Whether a stop command affects an autonomously triggered fire alarm depends on the device and is
  not documented. Hauswacht always assumes the worst case (rule S4).

## State machine

| No. | Rule |
|---|---|
| Z1 | After a start, a previous alarm is not continued and sirens are not switched on because of it – only exception (from 0.51): the setting "Resume a running alarm" (default off) triggers an alarm that was still in its reaction phase again after startup, with all siren locks (S1–S5). The message about an alarm before the restart goes as an alarm message to the alarm recipients. Whether the system is armed afterwards is decided by the setting "Behaviour after restart" (from 0.45): restore (default, without check and exit delay; a running entry delay starts again), always armed (checked normally, after startup) or always disarmed. |
| Z2 | Every restart while armed is reported ("armed again" or "disarmed"). During the startup phase (2 min), sensors reported open are bypassed until closed instead of triggering (entry doors: entry delay); failure messages only afterwards. |
| Z3 | Test mode can only be switched while disarmed. |
| Z4 | Expired timers from an earlier state or from before a restart have no effect. |
| Z5 | The system state only changes via events of the state machine. |

## Development

- No sirens are triggered and no devices are switched during development.
- Access to a productive Home Assistant instance is read-only and only after approval.
- Real siren tests only take place after explicit approval, with an announcement and with the
  residents present.

## Homecoming and push button

| No. | Rule | Reason |
|---|---|---|
| H1 | the homecoming observation switches nothing: no services, no arming/disarming, no alarm (static test) | first measure, then decide |
| H2 | a push button only applies to the arming in which it was sent | old notifications must not cancel a later arming |
| H3 | the push button only works with an active, non-system Home Assistant user | only logged-in phones |
| H6 | profile settings via entities only while disarmed | while armed, nobody may weaken the system |
| H7 | duress PIN: the action runs normally, emergency call only by push to its own recipients, nothing visible in Home Assistant | the offender could be standing next to you |
| H8 | PIN check in the background, PINs never in plain text; blocked/expired PINs are treated like wrong ones | no hanging, nothing revealed |
| H5 | button "Disarm now" never available with a PIN set; "End alarm" without PIN only with an explicit option | disarming always stays protected by the PIN |
| H4 | push button off by default | deliberate decision, also because of Android (no device lock for buttons) |
| H9 | automatic disarming on arrival only "as before" (after its own arming) or with door proof (arrival after reliable absence AND entry door within the time window); a running alarm is never ended; default off | a wrong location alone must never disarm |
| H10 | a button only arms – never disarms, never "end alarm", never over an armed profile, not if a PIN is required for arming | a button identifies nobody |
| H11 | a door lock only disarms with a known ID (the user's rights) AND actual unlocking in Home Assistant (≤ 30 s); never with the button inside, time control, automation, HomeKit/MQTT or merely opening; Hauswacht never operates the lock | some locks also report wrong codes |
