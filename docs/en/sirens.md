# Sirens

[Deutsch](../sirenen.md) | **English**

> **Safety first:** after installation, Hauswacht sends **no** siren command. Only the deliberate
> release ("Allow real siren control") enables this. In test mode, sirens are always locked. A
> fire always takes precedence.

**In short:** on an alarm, Hauswacht switches on the sirens of the profile – with a burglar tone,
the chosen volume and for the "alarm reaction time". Afterwards, when the alarm ends and when
disarming, Hauswacht switches them off again. Before that, a separate safety component (the
"siren guard") checks every time: is control enabled? Is test mode off? Does no smoke detector
report fire? Does the siren have a burglar tone? Only then is a command sent. Hauswacht may
**switch off** its own sirens even without the release – that is always the safe direction; only
test mode and fire prevent it.

## The menu "Alarm devices – sirens"

Settings → Devices & services → Hauswacht → **Configure → Alarm devices – sirens**:

| Menu item | What for | Section |
|---|---|---|
| **Sirens and enabling** | which sirens Hauswacht may use; enable real control; experts: allow switches | [Setting up](#setting-up) |
| **Create siren from switch** | wizard for sirens that only appear as a switch (`switch.…`) | [Create siren from switch](#create-siren-from-switch) |
| **Tone per siren** | set the tone for sirens with their own tone names (e.g. Homematic IP) | [Tone per siren](#tone-per-siren) |
| **Siren test (real siren!)** | check each siren individually, briefly and quietly | [Siren test](#siren-test) |
| **Siren test – reminder and pre-warning** | remind you of the test regularly; pre-warning before the sound | [Siren test](#siren-test) |

## Which sirens work?

Every Home Assistant entity of the domain `siren` – indoor and outdoor sirens as well as smoke
detectors with a siren. Sirens that only appear as a switch can be added with a
[wizard](#create-siren-from-switch).

Before every alarm, Hauswacht reads what a siren can do (`supported_features`,
`available_tones`) and only sends that:

| Capability of the siren | Behaviour |
|---|---|
| Tone selection with a burglar tone | the profile's tone; if it is missing, another burglar tone (`burglar`, `emergency`, `police_panic`, `emergency_panic`) – **never automatically a fire tone** |
| Tone selection with its own tone names (e.g. HmIP-ASIR) | only after choosing the tone under [Tone per siren](#tone-per-siren); until then it stays off |
| Tone selection with fire tones only | **not** used for burglary – except with the [expert release](#fire-tone-as-expert-release) (never for smoke detectors) |
| No tone selection | simple siren: without a tone. **Smoke detectors** without tone selection are not used, because their default tone is usually the fire tone |
| Volume, duration | only sent if the siren supports them |
| On and off only | Hauswacht switches it off itself after the alarm duration and when disarming |
| Neither duration nor switching off | not used – Hauswacht could not end it |
| Maximum duration (`number.<siren>_max_duration`, Zigbee2MQTT) | duration is limited to it; if it is missing, 240 seconds apply |
| Fire sensor on the same device (smoke detector) | device-related fire lock; an active fire at any sensor always locks |
| Only available as a switch (`switch.…`) | via the [wizard](#create-siren-from-switch) or as an [expert feature](#experts-switch-directly-as-siren) |

**Proven** is the smoke detector **Develco/frient SMSZB-120** ("Smoke detector with siren") via
Zigbee2MQTT – also with a real [siren test](#siren-test). Check other models first with test mode
and siren test. Feedback on further models is welcome
([issue](https://github.com/schlusenbaum/hauswacht/issues)).

## Setting up

1. **Sirens and enabling:** choose the sirens Hauswacht may use for burglar alarms. Leave "Allow
   real siren control" **off** for now.
2. **Check the tone:** if a siren knows none of the usual burglar tones, set the tone under
   [Tone per siren](#tone-per-siren). The [overview](overview.md) points this out ("would stay
   silent on alarm").
3. **Profiles:** in each alarm profile, set which of these sirens sound, with which tone and
   volume – or "Silent alarm" for notifications only. The running time is the profile's "alarm
   reaction time".
4. **Enable:** only when everything fits, switch on **"Allow real siren control"** and tick the
   confirmation. Without this release, Hauswacht never sends a siren command.
5. **Test:** check every siren once with the [siren test](#siren-test).

After the alarm duration – and when the alarm ends – Hauswacht switches off the sirens it
switched on itself. This matters for sirens that only know on and off. Sirens with their own
running time (e.g. smoke detectors with a maximum duration) also get the duration sent, but at
most the device's maximum duration. This maximum duration is only read, never changed.

## Tone per siren

Normally Hauswacht chooses a burglar tone itself (`burglar`, `emergency` …). Some sirens name
their tones differently. If Hauswacht finds no known burglar tone, the siren stays off for safety
reasons (reason `no_burglar_tone`), and the [overview](overview.md#check-hints) reports this as an
important check hint – also under Settings → Repairs.

**How to:** Alarm devices – sirens → **Tone per siren** → choose siren → choose tone.

- The list shows exactly the tones the siren reports itself; the dialog also names them in the
  text. "Automatic (standard burglar tone)" removes the setting again.
- The tone applies **on every alarm** of this siren (regardless of the tone in the profile) and
  **in the siren test**.
- Fire tones – recognisable by "fire", "smoke" or "Brand" in the name – are locked, except with
  the [expert release](#fire-tone-as-expert-release).
- Afterwards, do a short, quiet [siren test](#siren-test).

### Example: Homematic IP alarm siren (HmIP-ASIR, HmIP-ASIR-2, HmIP-ASIR-O)

Via the integration "Homematic(IP) Local" the alarm siren appears as `siren.…`. It stays silent
if it does not get **tone and duration** at the same time, and its tones are called e.g.
`FREQUENCY_RISING`, `FREQUENCY_RISING_AND_FALLING` or `DISARMED`.

1. Alarm devices – sirens → Sirens and enabling → select the alarm siren.
2. Tone per siren → alarm siren → **`FREQUENCY_RISING_AND_FALLING`** (or another alarm tone of
   the siren).
3. Add the alarm siren to the sirens in the profile.
4. Siren test with 3 seconds. Hauswacht sends the duration automatically.

Whether a tone is loud is only revealed by the test – tones like `DISARMED` or `LOW_BATTERY` are
short acknowledgement tones and unsuitable for an alarm.

### Fire tone as expert release

Fire tones are locked for burglary, for two reasons:

- **Wrong reaction:** whoever hears a fire tone at night leaves the house – possibly right to
  where the burglar is. With a burglar tone, people tend to stay inside and call for help.
- **The fire tone loses its value:** if it also sounds on burglar or false alarms, it is taken
  less seriously in a real fire.

Sometimes the name is misleading, though. **Example:** an outdoor siren has only two tones,
`chime` (quiet chime) and `fire` – and `fire` is simply its loud siren tone. Then:

1. Tone per siren → outdoor siren → tone **`fire`** (marked as "fire tone" in the list).
2. Switch on **"Experts: allow a fire tone for burglar alarms"**.
3. Tick the confirmation: "I confirm: this siren is not a smoke detector, and everyone in the
   house knows this tone as the burglar alarm".

What applies:

- The release only applies to **this one tone on this one siren**. Hauswacht never falls back to
  a fire tone on its own.
- **Never for smoke detectors with a siren** (devices with their own smoke, heat or test button
  sensors): the dialog does not offer the release there at all, and the siren guard also rejects
  it.
- The **fire lock stays:** if a smoke detector anywhere reports fire, Hauswacht switches no
  siren – whatever the tone.
- The [overview](overview.md#check-hints) shows the release permanently as a hint, so that it is
  not forgotten.

## Create siren from switch

Some sirens only appear in Home Assistant as a switch (`switch.…`), e.g. a siren on a Homematic
switch actuator. Home Assistant can turn this into a siren itself: with the helper **"Change
device type of a switch"**. Hauswacht has a wizard for this.

**Example:** the outdoor siren is connected to `switch.actuator_garage`.

1. Alarm devices – sirens → **Create siren from switch**.
2. Choose the switch `switch.actuator_garage`.
3. Confirm: "this is a pure alarm siren, not a smoke detector".
4. Done: the dialog shows e.g. "Created: siren.actuator_garage", and the new siren is already in
   the list under "Sirens and enabling".
5. Add the siren to the profile and check it with the siren test.

Good to know:

- The switch is **not** switched in the process. Home Assistant hides it and shows the siren
  instead; in automations, the switch keeps working.
- The new siren only knows on and off: Hauswacht switches it on during an alarm and off again
  after the alarm duration. Release, fire lock, test mode and siren test apply as for every
  siren.
- **Undo:** delete the helper under Settings → Devices & services → Helpers. Then the switch is
  visible again.

> With a switch, Hauswacht does not know what the device does when switched on. Only add real
> alarm sirens this way – never smoke detectors, lights or other devices.

### Experts: switch directly as siren

If you do not want to create a helper, you can also add switches directly:

1. Alarm devices – sirens → **Sirens and enabling** → switch on **"Experts: allow switches
   directly as sirens"** and save.
2. The dialog opens again; now the siren list also offers switches.
3. Select the switch, save, add it to the profile, do a siren test.

Hauswacht switches such a switch exactly like a simple siren: `switch.turn_on` on alarm,
`switch.turn_off` after the alarm duration and when disarming – with the same locks (release,
test mode, fire lock). If the expert feature is switched off again, the switches drop out of the
list.

The wizard is usually the better choice: the siren then looks like a siren everywhere in Home
Assistant.

## Siren test

**Alarm devices – sirens → Siren test (real siren!).** Checks each siren individually, briefly
and quietly – via the same safe path as a real alarm.

1. Choose sirens (several are tested **one after another**), tone (burglar tones only), volume
   (default **low**) and duration (default **3 s**, at most **10 s**); tick "I am on site,
   housemates are informed".
2. For every siren Hauswacht asks "Test siren …?" and shows a **pre-check without sound**: what
   would be sent (tone, volume, duration) or why it is not possible. Answer: test, skip or stop.
3. After the sound: "Heard it?" – the result is stored with the date (diagnostic sensor "Last
   siren test", per siren in the attributes).

If a tone is set for a siren under [Tone per siren](#tone-per-siren), Hauswacht tests with this
tone – so the test checks exactly what happens during an alarm.

Requirements – the siren guard checks them as for an alarm, without exception:

- all areas **disarmed**, no alarm
- **hardware release on**
- **test mode off** – test mode always locks sirens; the siren test is deliberately not test
  mode but a real, short switching on
- **no fire lock** (no smoke detector active or unclear), burglar tones only
- the siren is enabled for burglary and can be limited

The duration is limited three times: as a duration sent to the device (if it supports it), by a
separate switch-off command afterwards, and by the fixed upper limit of 10 s. During the test,
**arming is locked**; **disarming** stops the test. In case of fire, Hauswacht does not interfere
– then the fire lock applies.

**Alarm devices – sirens → Siren test – reminder and pre-warning:**

| Setting | Meaning |
|---|---|
| Reminder | off, every 3 or 6 months, yearly: reports "siren test due" (at most once a week) if a siren has not been tested successfully for that long |
| Pre-warning before the test | sends "Siren test … in 10 seconds" to the general recipients before the first sound |

The same as actions (administrators only): `hauswacht.siren_test` (fields `siren`, `duration`,
`volume`, `tone`), `hauswacht.siren_test_result` (`siren`, `heard`) and
`hauswacht.siren_test_stop`. The test card contains the siren test collapsed, with a safety
prompt, see [Card "Hauswacht Test"](test-mode.md#card-hauswacht-test).

## Why didn't a siren sound?

After every alarm and every siren test, the attribute **`last_siren_decision`** of the alarm
panel (Developer tools → States → `alarm_control_panel.hauswacht`) shows which sirens were
controlled (`sent`) and which were not, and why (`blocked`). Example:

```yaml
last_siren_decision:
  action: activate
  sent:
    - siren.hallway
  blocked:
    siren.alarm_siren: no_burglar_tone
```

Here the hallway siren sounded, the alarm siren did not, because it knows no burglar tone. The
reasons in plain language:

| Reason | Meaning | What to do? |
|---|---|---|
| `hardware_disabled` | real siren control is not enabled | Sirens and enabling → enable |
| `test_mode` | test mode is on | test mode off |
| `fire_lock` | a smoke detector reports fire, or the fire state of a registered siren is unclear (sensor unavailable) | check the smoke detectors; in case of fire this is intended |
| `no_burglar_tone` | the siren knows no burglar tone (or only fire tones) | [Tone per siren](#tone-per-siren) |
| `cannot_limit` | the siren can neither take a duration nor be switched off | use another siren |
| `invalid_duration` | the device's maximum duration is 0 | check the maximum duration on the device |
| `unknown_device` | the siren is in the profile but no longer registered | check Sirens and enabling |
| `invalid_tone`, `invalid_volume` | tone or volume in the profile invalid | save the profile again |
| `not_activated_by_hauswacht` | switching off a siren Hauswacht did not switch on | nothing – Hauswacht only switches off its own sirens |

The same decision comes as the event `hauswacht_event` with `type: SirenDecision`, see
[Reference](reference.md#events).

## Fire protection

If the sirens are smoke detectors at the same time, Hauswacht recognises their smoke and test
button sensors automatically.

- If **any** smoke detector in Home Assistant reports fire, Hauswacht switches no siren on and
  none off.
- If the fire state of a **registered** siren is unclear (sensor unavailable or disabled), the
  same applies.
- If fire was reported during a burglar alarm, even disarming does not switch off any siren.
  Sirens with their own running time go quiet after their maximum duration. Hauswacht switches
  off all others as soon as no fire is reported any more (checked every minute).
- A smoke detector never plays its fire tone for a burglary – not even with the
  [expert release](#fire-tone-as-expert-release).
- Hauswacht never uses other switch-off scripts (e.g. "all smoke detectors off").
- If you use smoke detectors as alarm devices: **interconnecting** them (all beep on smoke) is
  deliberately not done by Hauswacht – it is a small automation of your own, see
  [examples](examples.md#interconnecting-smoke-detectors).

## Siren was still on at a restart

If Home Assistant restarts in the middle of an alarm (crash, power cut, update), a siren without its
own running time – above all a [switch as siren](#create-siren-from-switch) – would otherwise just
keep sounding. That is why Hauswacht permanently remembers which sirens **it has switched on
itself**, and switches them off again after the restart:

- **When:** as soon as Home Assistant has finished starting. After the startup phase (2 minutes),
  Hauswacht checks once more: if one of these sirens still reports "on" (e.g. because it was not
  reachable before), it is switched off a second time. Not after that.
- **Only its own:** sirens switched on by another automation or by a smoke detector are never
  touched.
- **Fire comes first:** if a smoke detector reports fire (or the state of a registered siren is
  unclear), nothing is switched off. You get a message, and Hauswacht tries again every minute
  until no fire is reported any more. Disarming does not make it forget the siren either.
- **Without release:** it is switched off even if the siren release is off by now.
- **New alarm:** if a new alarm after the restart switches the siren on again, it belongs to that
  alarm – the second attempt then does not switch it off.
- **Message:** "Hauswacht: siren after restart – was still on for an alarm at the restart and has
  been switched off: garage siren." (event "System" in the [notifications](notifications.md)).

**Example:** a relay `switch.sirene_garage` is set up as a siren. During an alarm, Home Assistant
crashes and restarts. The relay stays on, the siren is howling. About half a minute later Home
Assistant has started, Hauswacht switches `switch.sirene_garage` off and reports it.

The binding rules behind this are in the [safety rules](development/safety.md).
