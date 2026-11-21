# Passage – in or out without disarming

[Deutsch](../durchgang.md) | **English**

A **passage** frees a door briefly – the profile **stays armed**. All other sensors still
trigger.

Two typical cases:

- **Someone comes home at night.** "Night" is armed, Finja opens the front door, the entry delay
  runs. She enters her PIN at the keypad and presses a profile key – no alarm, and the house stays
  in "Night". Nobody has to arm again afterwards.
- **Briefly out, e.g. taking out the bins.** PIN and a profile key at the keypad – then a
  front door may open and close for 5 minutes. Everything else stays armed, including the back
  door.

The passage is meant for profiles that **only watch the outer shell** (doors, windows). Sensors
**inside** (e.g. motion sensors in the hallway) stay armed – the passage then only helps at the
outer doors.

## Switching it on

In the profile under **Passage** (settings page → Profiles, or in the settings dialog for the
profile):

| Setting | Meaning | Default |
|---|---|---|
| Allow passage | Without it there is no passage in this profile | off |
| Passage time | Going out: how long the door is free. Coming in: how long the door may stay open before the warning comes | 5 minutes (1–60) |
| Going out: which door | **Only the first door that opens** – all others stay armed. Or **all entry doors** | only the first |
| Going out: end | **When the time is up** (you can go out and in several times) or **as soon as I am back and the door is closed** (the door closed for the second time: out and back) | when the time is up |
| Sensors on the way | Outdoor sensors that would trigger on the way – e.g. a motion sensor in the driveway, at the garden gate or at the bins | none |
| Coming in: way still free after closing | How long the sensors on the way stay free after the door is closed | 60 seconds |
| Let in by phone: these persons | Hauswacht lets these persons in without PIN when their phone comes home – see [let in by phone](#let-in-by-phone) | none (off) |
| Phone may report "home" this long before the door | Time window for letting in by phone | 5 minutes (1–30) |

All sensors with the role **entry** count as a **door** (they start the entry delay). You do not
need an extra key: while the profile is armed or the entry delay runs, **any profile key** with
PIN or card opens the passage. If you have a free key, you can give it **"Passage (in/out, stays
armed)"** instead of a profile at the keypad (see [control devices](control-devices.md)).

## Coming in

This is how it works:

1. The front door opens, the entry delay runs.
2. At the keypad: **PIN or card** and **any profile key** (or the passage key). People coming
   home often do not know which profile is active – so every key counts. The **running** profile
   stays; it is not changed.
3. The entry delay ends, the system stays armed. The **opened door** is free **until it is closed
   again**. The sensors on the way are free until the door is closed plus the follow-up time
   (default 60 seconds).
4. The message "Finja (Keypad hallway) let in (front door) – profile Night stays armed" replaces
   the message about the entry delay.

PIN and **"Disarm"** disarms completely, as before.

### Let in by push button

If "disarm via push button" is on (see [notifications](notifications.md)), the message about the
entry delay has **[Let in]** next to **[Disarm]** – if the profile allows the passage. Whoever taps
must be allowed to **disarm** as a Home Assistant user (as with the "Disarm" button).

Examples: Finja is at the door and taps "Let in" herself. Or you are in bed, the phone shows
"front door opened", you see it is Niklas and tap "Let in". It has to happen during the entry
delay; after that it is an alarm.

### Let in by phone

Under **"Let in by phone: these persons"** you choose persons that Hauswacht lets in **without
PIN** when their phone comes home. The detection is the same as for
["disarm with door proof"](profiles.md#disarm-on-arrival) – only that at the end the person is let
in instead of disarming:

- The person **comes home**: they were **safely away for at least 5 minutes** before and are home
  now (person entity plus the signals under "Presence and homecoming"). A phone lying in the house
  all night opens nothing.
- An **entry door** opens.
- The phone reports **up to x minutes before the opening** (time window, default 5 minutes)
  **or afterwards, while the entry delay is running**.

| What happens | Result (entry delay 30 s, time window 5 minutes) |
|---|---|
| Phone reports "home", 2 minutes later the door opens | **Let in** on opening |
| Door opens, 20 s later the phone reports "home" | **Let in** after 20 s |
| Door opens, the phone only reports after 45 s | **Alarm** after 30 s as always; the phone does not end it |
| Phone reports "home", the door only opens 7 minutes later | Too long ago: normal entry delay |
| The person was only away for 2 minutes | Does not count as coming home: normal entry delay |

- **One homecoming lets in once.** For the next door opening the phone must have been away again
  first.
- The message reads e.g. "Finja (phone) let in (front door) – profile Night stays armed" – a wrong
  let-in is noticed at once.
- **Not together with "disarm with door proof"** in the same profile: the same homecoming cannot
  disarm and only let in at the same time. The setting only allows one of them.
- **Which entry delay do I need?** If the phone often reports only after the opening, the entry
  delay has to be long enough. The
  [homecoming observation](observations.md#recommendation-for-disarm-with-door-proof) calculates
  this per person – the value applies here just the same.

> **Residual risk:** whoever has the phone of an allowed person **and** access to the door (e.g.
> phone and key stolen) gets in without alarm. For profiles like "Vacation", better enter no
> persons.

**If two come one after the other**, every new door opening needs its own credential: once the
door is closed after Finja, it is armed again. If Niklas comes three minutes later, the entry
delay runs again for him.

## Going out

1. First, at the keypad: **PIN or card** and **any profile key** – or the passage key if you
   have one. While the profile is armed, a profile key **never** switches to another profile;
   to change, disarm first. So the passage also works if all keys are assigned to profiles.
2. The message "Christian (Keypad hallway): passage for 5 minutes – profile Night stays armed"
   comes.
3. The **first entry door that opens now** is free for the passage time – you can go out and in
   several times. All other doors stay armed (setting "all entry doors": every one).
4. The sensors on the way are free the whole time.
5. At the end (time up, or – depending on the setting – you are back and the door is closed)
   everything is monitored again.

**Example:** profile "Night", passage time 5 minutes, "only the first door". You press PIN and
passage, go out the front. While you are at the bins, someone opens the back door → normal entry
delay and alarm. The back door was never free.

## Door still open after the passage

If a door is still open at the end, there is **no alarm** but a **warning**:

> Front door still open after the passage – not monitored until it is closed. Profile Night stays
> armed.

The door stays free **until it is closed** – then it is monitored again. The same applies to a
sensor on the way that still reports motion at the end.

> **Careful with contacts that wrongly report "open":** then the door stays unmonitored although
> it is closed. The warning shows this. Check the contact (often the magnet is too far away).

## What else applies

| Case | Behaviour |
|---|---|
| **Credential** | Always needed – even if "keys without PIN" is on. Wrong PINs count towards the lock as usual |
| **Right** | Whoever may **disarm** (in the area) may also open a passage |
| **Duress PIN** | Looks like a normal passage; the duress alarm silently goes to the duress recipients |
| **Guest mode** | Passage works normally |
| **Test mode** | Passage works normally – to try it out safely |
| **Running alarm** | No passage – use "End alarm" |
| **Exit delay** | No passage |
| **Disarming** | Ends every passage |
| **Several areas** | The passage applies in the keypad's area; if the entry delay runs anywhere there, only that area lets in |
| **Restart** | A running passage ends; open doors are handled as after every restart |
| **Trigger rules** | What the passage frees does not count for rules either |

## Display and messages

- The panel stays "armed – Night". The alarm card shows below "Passage until 22:35 – free: front
  door, motion driveway".
- Attribute `passage` on the panel and on the display entity of generic keypads (see
  [reference](reference.md#attributes-of-the-alarm-panel)).
- Messages via the event **"Passage"** under [notifications](notifications.md) (default: on).
  "Passage for 5 minutes" and the warning "still open" replace each other and disappear when the
  passage ends without a warning or the system is disarmed.
- Events for automations: `PassageGranted`, `PassageDoorUsed`, `PassageEnded`,
  `PassageDoorOpen` (see [reference](reference.md#events)).

## Door lock, NFC tags, card readers

For the [door lock](control-devices.md#door-lock-eg-nuki) set **"Unlocking while armed:
passage"**, for [NFC stickers](control-devices.md#nfc-sticker-companion-app) and
[RFID readers](control-devices.md#rfid-reader) the **action "passage"**. Then:

| State | Unlocking, scanning the tag or holding the card |
|---|---|
| Entry delay running, profile allows passage | **Coming in** – door free until it is closed |
| Armed, profile allows passage | **Going out** – the first door that opens afterwards is free |
| Armed, profile allows **no** passage | **Disarm** as before |
| Disarmed | nothing |

Example: the Nuki at the front door is set to "passage". At night "Night" is armed (with
passage): Finja unlocks with her Nuki app – Hauswacht lets her in, "Night" stays. During the day
"Away" is armed (without passage): unlocking disarms.

## Via action or dashboard button

```yaml
action: hauswacht.passage
target:
  entity_id: alarm_control_panel.hauswacht
data:
  code: "1234"   # needed if PINs are set up
```

While the entry delay runs, the person is let in, otherwise a passage for going out starts. If no
passage is possible right now (profile does not allow it, disarmed, alarm), the action reports an
error.
