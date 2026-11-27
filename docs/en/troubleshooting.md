# Troubleshooting

[Deutsch](../fehlersuche.md) | **English**

## Arming

**"Arming rejected" – why?**
The message names the reason: open sensors, failed sensors, a fault of a radio network/gateway, or
a profile without sensor groups. Open sensors are also shown by
`binary_sensor.hauswacht_open_sensors_in_sensor_groups`. If the profile allows "after
confirmation", use [Arm anyway](dashboard.md#arm-anyway).

**The alarm panel does not show my button.**
Only profiles with an assigned alarm panel button appear there. All others via the selection list
"Profile" + "Arm".

**After a restart the system is disarmed (or armed), I wanted it differently.**
This is set under settings page → System → [Behaviour after restart](installation.md#behaviour-after-a-restart).
The default is "restore the previous state". Disarmed despite restoring means: the system was
disarmed before, or the profile has been deleted in the meantime (then you get a message).

**After a restart a window is listed as "bypassed until closed".**
It was reported open at startup. Hauswacht cannot tell whether it was already open before, so it
bypasses it instead of triggering an alarm. As soon as it is closed, it is monitored normally
again.

**The schedule does not arm (or does not disarm).**
- Arming only from **disarmed** – if another profile was already armed, nothing happens.
- In **guest mode** Hauswacht does not arm automatically (message "skipped").
- **Open windows** are never confirmed automatically – then you get the message "not armed".
- Disarming only if **exactly this profile** is armed, and never during entry delay or an alarm.
- **Restart** during a block change: the schedule catches up on nothing; the behaviour after
  restart applies.
- Check the schedule itself: Developer tools → States → `schedule.…` must change from `off` to
  `on` at the desired time. Events `AutoArmed`/`AutoArmSkipped` with `reason: Zeitplan` show what
  Hauswacht made of it. More: [different times per weekday](profiles.md#different-times-per-weekday-schedule).

**Settings cannot be changed.**
Only possible while **all areas are disarmed**.

**"Arm when all of these persons are away" does not arm although everyone is away.**
A person only counts as away when the person itself **and all** their additional signals report
"away". A signal that is "unavailable" or "unknown" holds the automation back. Check under settings page →
System → Presence and homecoming observation which signals are selected, and their state under
Developer tools → States.
Since 0.61 "away" also needs **proof**: door and then a location outside, or a fresh, precise
location outside (["away" only with proof](profiles.md#away-only-with-proof)). If the person shows
"⚠ no location", a location with coordinates is missing – set the location in the Companion app
to "Always". If the GPS in the house often reports "outside" but inaccurately, "check precisely"
stays the right choice; if "away" is never detected although the location is right, lengthen the
time window for the proof.
*From 0.66:* under "Which signals count?" each person shows what was measured. A signal that
"mostly does not report 'away'" when leaving (e.g. Bluetooth through the door) holds "all must be
away" back – then untick **Leaving** for it or apply the recommendation. If the profile has an
**own trigger**, the persons do not count there at all
([more](profiles.md#own-trigger-for-all-away)). And: arming only happens after the **waiting
time** in the profile (default 15 minutes).

**"On return – Disarm with door proof" does not disarm.**
Is the person ticked under "On return" → "For these persons"? Since 0.61 that list is independent
of "Arm when all away".
Both are needed: the person was reliably **away** before and now reports **home**, and an **entry
door** (role "entry") opens – while the profile is armed or the entry delay is running. The
location may be at most the time window (default 5 minutes) **before** the door; **after** the
door it has to come within the entry delay. If the location only came after the entry delay had
run out, the alarm is already running – and that is never ended automatically. Then extend the
entry delay; the [homecoming report](observations.md#recommendation-for-disarm-with-door-proof)
names the value needed. Under Developer tools → Events → listen to `hauswacht_event` you see
`ArrivalNoted` (arrival detected) and `DoorNoted` (door detected).

## PIN and operation

**The dashboard suddenly asks for a PIN.**
As soon as any PIN exists (including the master PIN), the alarm panel of Home Assistant (tile,
alarm card of Home Assistant) requires it from everyone for disarming. Remedy: use the card
["Hauswacht Alarm"](dashboard.md#card-hauswacht-alarm) – it switches without PIN for accounts
linked to a Hauswacht user. See also [Users](users.md#the-most-important-thing-first).

**The card "Hauswacht Alarm" asks me for the PIN.**
It asks if

- your Home Assistant account is **not linked to a Hauswacht user** (Users and PINs → user →
  "Home Assistant account (for alarm card, push and dashboard buttons)") and "Alarm card: require
  PIN for Home Assistant accounts without a Hauswacht user" is on under PIN rules (default), or
- **"Require PIN in the alarm card"** is on for the linked user (meant for a wall tablet).

Arming only asks if "Require PIN to arm" is on. Details: [No forced PIN](dashboard.md#no-forced-pin).

**The card "Hauswacht Alarm" shows "This account may not operate the alarm system."**
The account may not control the alarm panel in Home Assistant (e.g. an account with read-only
rights). An administrator can change that under Settings → People.

**A button in the alarm card is greyed out.**
The linked user lacks the right for it in this area (user → rights), or their validity has
expired.

**"Too many wrong PIN entries".**
The [lockout](users.md#lockout-after-wrong-entries) is running (1–15 minutes). Administrators reset
it in the test card with "Reset failed attempts". Failed attempts expire 24 hours after the last
one.

**The buttons "Disarm now"/"End alarm" are unavailable.**
With a PIN set, buttons cannot ask for the PIN and are locked – unless the PIN rules allow them.

## Keypad and cards

**The keypad reacts, but Hauswacht gets no code.**
Check in Zigbee2MQTT at the keypad under "State" or in the log: if it says `action_code: ""`, the
keypad does not send the code.

- Mind the order: first type the PIN or hold up the card, **then** the key.
- If that does not help, **remove and re-pair** the keypad in Zigbee2MQTT (just taking out the
  battery is sometimes not enough). Then give it the old device name again, so the MQTT topic in
  Hauswacht is right again.

**A card is not offered for learning.**

- Were all areas disarmed? Has the learning time (default 5 minutes) run out?
- Is it a **random ID** (4 bytes, starts with `08`, e.g. a phone)? It changes on every read and is
  unsuitable – a hint appears while learning.
- Does the card have only 4–8 digits? Then it could be a PIN and is never shown – type the ID in.
- Does the card already belong to a user?

**The keypad does not beep.**
Hauswacht answers every key press. If there is no acknowledgement, it is usually the keypad itself
(see above: re-pair). With debug logging for MQTT, the answer to `<topic>/set` is visible in the HA
log.

**Can I disarm with just a card, without a key?**
Not with a Zigbee keypad – it only sends the card number with a key press. For that there is the
[RFID reader](control-devices.md#rfid-reader) or the [NFC sticker](control-devices.md#nfc-sticker-companion-app).

**The button does not arm.**

- Is a profile already armed? Then the button does nothing.
- Is the press type assigned to a profile? With an action sensor, the entered value has to match
  the sensor's value exactly (Developer tools → States, press once).
- Do the PIN rules require a PIN for arming? Then a system message comes – a button cannot enter a
  PIN.
- Under Developer tools → Events → listen to `hauswacht_event`: does pressing produce
  `ButtonPressed` with the right press type (`press`)?

**The door lock does not disarm.**

- Is the ID entered with the user? Hauswacht reports unknown IDs with a system message while
  armed. Learning only works while everything is disarmed.
- May the user disarm in this area, and is the user valid?
- Does the lock change to "unlocked" in Home Assistant? Without this change (within 30 s),
  nothing happens – on purpose.
- Nuki: is the MQTT topic right (e.g. `nuki/3A1B2C4D`, without `/lockActionEvent`)? Check with an
  MQTT program (e.g. MQTT Explorer) whether five numbers appear under `nuki/…/lockActionEvent`
  when unlocking. The second must be `0` – button inside, time control or unlocking via Home
  Assistant never count.
- In `hauswacht_event`, `LockIdentified` shows the detected ID (`identity`) and the reason
  (`reason`: `not_by_person`, `no_id`).

## Sirens

**No siren sounds on an alarm.**
The attribute `last_siren_decision` of the alarm panel names the reason – all reasons in plain
language under [Why didn't a siren sound?](sirens.md#why-didnt-a-siren-sound). Common:

- Real siren control not enabled yet (settings page → Alarm devices → Edit sirens).
- Test mode on.
- Profile set to "Silent alarm" or without sirens.
- Fire lock: a smoke detector reports fire or is unavailable.
- `no_burglar_tone`: the siren has its own tone names (e.g. Homematic IP alarm siren) – set the
  tone under [Tone per siren](sirens.md#tone-per-siren).
- The siren cannot be limited, see [Which sirens work?](sirens.md#which-sirens-work).

**The siren test sometimes only works the second time.**
Typical for battery smoke detectors via Zigbee: they only fetch commands after a few seconds. Up
to 0.57.1, Hauswacht sent the "off" after 3.5 s already – if it arrived together with the "on",
the detector stayed silent. Since 0.57.2 the test waits longer with such sirens, see
[siren test](sirens.md#siren-test). If it still does not sound: check in Zigbee2MQTT whether the
detector is reachable (last seen, link quality).

**My siren only exists as a switch in Home Assistant.**
[Create siren from switch](sirens.md#create-siren-from-switch) turns it into a siren.
Alternatively the [expert feature](sirens.md#experts-switch-directly-as-siren).

**Tone per siren: "A fire tone is locked for burglar alarms".**
Intended – see [Fire tone as expert release](sirens.md#fire-tone-as-expert-release). With smoke
detectors, a fire tone for burglary is never possible.

## Sensors

**The log says "Hauswacht ignores entities without open/closed".**
A measurement sensor (e.g. temperature) is in a sensor group or trigger rule. Hauswacht only
monitors sensors with open/closed – remove it, or turn it into a threshold sensor with
[Create a sensor from another sensor](sensors.md#create-a-sensor-from-another-sensor).

**A sensor constantly counts as failed.**
The maximum radio silence is too tight for this battery sensor. The
[radio silence observation](sensors.md#radio-silence-observation-the-right-value-from-your-data)
recommends a suitable value.

## Cards on the dashboard

**A Hauswacht card shows the old version after an update.**
Reload the page; in the app, Settings → Companion app → Reset frontend cache.

**Editing a card says "Visual editor not supported".**
This concerns versions before 0.37. After the update, reload the page (see above).

**The overview shows "administrators only".**
The [system overview](overview.md) contains security information and is therefore for
administrators only.

## Language

**Messages come in English (or German), I want the other language.**
Hauswacht follows the language of Home Assistant (Settings → System → General → Language): German
with a German setting, otherwise English. Messages follow a change at once; entity names and IDs
stay as they were created when setting up. Custom texts are sent as entered.

## Debug log: what did Hauswacht decide?

*From 0.65.0b9.* When Hauswacht does something you did not expect, the debug log shows step by
step **what came in, what Hauswacht made of it and what it did**. That way almost every error can
be assigned to one of four causes:

1. **The sensor or signal reports something wrong.** The log shows a different state than
   expected, or none at all.
2. **Hauswacht interprets it differently than you thought.** The line names the reason, e.g. "im
   Profil night nicht überwacht" (not monitored in profile night) or "Anwesenheit person.… =
   unklar" (presence unclear).
3. **Hauswacht decides correctly, but the action fails.** Then you see e.g. a blocked siren or a
   notification without recipients.
4. **Home Assistant or another integration has a problem.** Then errors of other integrations
   appear in the log.

The debug log is **off** by default; without switching it on, Hauswacht writes none of these
lines.

**Switching it on and downloading – step by step:**

1. In Home Assistant open **Settings → Devices & services** and click **Hauswacht**.
2. Tap **⋮** at the top right and choose **Enable debug logging**.
3. Reproduce the problem (e.g. arm, open the door) or wait until it happens.
4. Again **⋮ → Disable debug logging**. Home Assistant then offers a file with all log lines
   since switching it on for download.

**Reading along live without switching off:** **Settings → System → Logs**, at the top right
**⋮ → Show full logs** and type `hauswacht` into the search field. New lines appear there as
soon as something happens.

**Across a restart:** if the error happens during or right after a restart (e.g. "behaviour
after restart"), switch on the debug log in `configuration.yaml` and restart Home Assistant:

```yaml
logger:
  logs:
    custom_components.hauswacht: debug
```

If your `configuration.yaml` already has a `logger:` section, only add the line under `logs:`.
After troubleshooting remove the line again and restart – otherwise Home Assistant keeps writing
more to the log.

**How much and how long?** Debug costs hardly any computing time but makes the log bigger. Only
leave it on as long as you need it for troubleshooting.

**What the lines look like** (examples; the log lines are in German):

```
Bereich main: Melder binary_sensor.kuechenfenster off → on (instant, überwacht, löst aus)
Bereich main: SensorTriggered(sensor_key=binary_sensor.kuechenfenster, role=instant) → StateChanged(old=armed, new=triggered, cause=instant_sensor), ActivateReaction(profile_id=night, cycle=1, sensor_key=binary_sensor.kuechenfenster, test_mode=False)
Sirenen activate: gesendet ['turn_on siren.flur'], gesperrt {'keller': 'fire_lock'}
Benachrichtigung alarm: Empfänger ['notify.mobile_app_…'], gesendet ['notify.mobile_app_…']
Bereich main: Melder binary_sensor.haustuer off → on (entry, unscharf, nicht immer aktiv)
Bereich main: Anwesenheit person.… = unklar {kind=no_proof, located=False, weak=False, window=15, …}
Bereich main: AutoArmSkipped (Profil away) {reason=away}
Bedienteil a1b2c3: Taste arm_away, Ausweis ja, trotzdem nein → ok
```

| Line | What it shows |
|---|---|
| `Melder … (…)` (sensor) | Every change of a sensor, with its role and whether it counts right now (monitored, bypassed, disarmed, not in the profile) |
| `Bereich …: input → effects` (area) | What the state machine makes of an event: arming, delays, alarm, refusal with reason (`Rejected`, `Ignored`) |
| `Anwesenheit … = …` (presence) | When presence changes: home (zuhause), away (weg) or unclear (unklar), with the reason (proof, what is missing) |
| `Automatik …` (automation) | What "arm when everyone is away", schedules and "on return" do, or why not |
| `Sirenen …` (sirens) | Which sirens got a command (gesendet) and which were blocked (gesperrt, e.g. fire lock) |
| `Benachrichtigung …` (notification) | Which recipients a message went to – without title and text |
| `Bedienteil …` (control device) | Key and result of an input – only "credential yes/no" (Ausweis ja/nein), never the code |

**Privacy – what is never in the log:** PINs, codes and card numbers, user names, coordinates,
Wi-Fi names and the texts of notifications. A test checks on every change that no log line of
Hauswacht contains such values – also without debug. Hauswacht sends the log nowhere; it stays on
your Home Assistant.

**Please check before passing it on:** the log names **entity IDs**, and they often contain names
(`person.anna`, `notify.mobile_app_annas_iphone`). It is also a **timeline**: whoever reads it
sees e.g. when the front door opened and when someone counted as away. Before posting, replace
names in entity IDs (e.g. `person.anna` → `person.person_1`, the same everywhere) and only send
the period that matters. For the settings themselves there is
[Download configuration](settings-page.md#download-configuration) – there Hauswacht replaces names
automatically.

## Getting help

For an [issue](https://github.com/schlusenbaum/hauswacht/issues) or a forum post, this helps
most (questions in English are welcome):

1. **What happened, what did you expect?** In one or two sentences, with the approximate time.
2. **The file from [Download configuration](settings-page.md#download-configuration)** (System
   tab, at the very bottom). It contains versions, settings and the current state; names are
   already replaced by placeholders.
3. **The relevant lines from the [debug log](#debug-log-what-did-hauswacht-decide)**, only for
   the period that matters.

Please remove names in entity IDs, IP addresses, tokens and other personal data from logs first.
