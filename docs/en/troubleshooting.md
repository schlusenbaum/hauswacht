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
This is set under System settings → [Behaviour after restart](installation.md#behaviour-after-a-restart).
The default is "restore the previous state". Disarmed despite restoring means: the system was
disarmed before, or the profile has been deleted in the meantime (then you get a message).

**After a restart a window is listed as "bypassed until closed".**
It was reported open at startup. Hauswacht cannot tell whether it was already open before, so it
bypasses it instead of triggering an alarm. As soon as it is closed, it is monitored normally
again.

**Settings cannot be changed.**
Only possible while **all areas are disarmed**.

**"Arm when all of these persons are away" does not arm although everyone is away.**
A person only counts as away when the person itself **and all** their additional signals report
"away". A signal that is "unavailable" or "unknown" holds the automation back. Check under System
settings → Presence and homecoming observation which signals are selected, and their state under
Developer tools → States.

**"Disarm on arrival – with door proof" does not disarm.**
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
  unsuitable – the user dialog then shows a hint.
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

- Real siren control not enabled yet (Alarm devices – sirens).
- Test mode on.
- Profile set to "Silent alarm" or without sirens.
- Fire lock: a smoke detector reports fire or is unavailable.
- `no_burglar_tone`: the siren has its own tone names (e.g. Homematic IP alarm siren) – set the
  tone under [Tone per siren](sirens.md#tone-per-siren).
- The siren cannot be limited, see [Which sirens work?](sirens.md#which-sirens-work).

**My siren only exists as a switch in Home Assistant.**
The wizard [Create siren from switch](sirens.md#create-siren-from-switch) turns it into a siren.
Alternatively the [expert feature](sirens.md#experts-switch-directly-as-siren).

**Tone per siren: "A fire tone is locked for burglar alarms".**
Intended – see [Fire tone as expert release](sirens.md#fire-tone-as-expert-release). With smoke
detectors, a fire tone for burglary is never possible.

## Sensors

**The log says "Hauswacht ignores entities without open/closed".**
A measurement sensor (e.g. temperature) is in a sensor group or trigger rule. Hauswacht only
monitors sensors with open/closed – remove it, or turn it into a threshold sensor with the wizard
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

## Getting help

An [issue](https://github.com/schlusenbaum/hauswacht/issues) with the Hauswacht version, the Home
Assistant version and the relevant log lines helps most. Questions in English are welcome. Please
remove names, IP addresses, tokens and other personal data from logs first.
