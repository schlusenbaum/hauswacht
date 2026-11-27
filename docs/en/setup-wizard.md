# Assistant and setup

[Deutsch](../assistent.md) | **English**

> **Since 0.63.2 the former setup wizard is gone.** It lived in the settings dialog (Settings →
> Devices & services → Hauswacht → Configure), which no longer exists – everything is set up on
> the [settings page](settings-page.md). Your settings stay unchanged.

## How do I set up Hauswacht now?

1. Read the overview first: [How Hauswacht decides](how-hauswacht-decides.md) – what happens when
   a door opens, when the automation switches, what happens when someone comes home.
2. Then the shortest way to the first arming:
   [five steps](installation.md#five-steps-to-the-first-arming) – sensor group, alarm profile,
   notification, test mode, for real.
3. Everything else as needed, each on the settings page: [Users and PINs](users.md),
   [Control devices](control-devices.md), [Trigger rules](trigger-rules.md), [Sirens](sirens.md),
   [Presence and automation](profiles.md#automation).

Every field on the settings page has an **ⓘ** with an explanation, and where it helps, a sentence
**"This is how it behaves:"** with an example.

## Hints while editing (since 0.64.0b2)

The assistant **watches along** while you set things up. In the side sheet of an **alarm
profile** and in the side sheet **System → Presence** a box **Assistant** appears above "Save"
as soon as something does not fit. It checks your **draft** – as it would be after saving.
Nothing is saved and nothing is switched.

- The box is **only a hint**. You can still save – you decide.
- Each hint says in one sentence **what** does not fit. **"Why?"** shows the reason, with a
  **measurement** from the [observation](observations.md) where there is one.
- Many hints have a **suggestion** as a button. A click only changes the draft in the side
  sheet – it is saved only with **Save**.
- Suggestions marked **⚠** make the system **more lenient** in one place (e.g. a longer entry
  delay = a later alarm). You have to confirm them explicitly.
- If a suggestion belongs somewhere else (e.g. "door + signal" in a profile), it is shown as text
  only: "Suggestion: … (change it elsewhere)".

Hints of level **error** also appear in the [check hints](overview.md#check-hints) – so you see
them even when no side sheet is open.

### What is checked

| Hint | Level | Suggestion |
|---|---|---|
| A person in **"arm when all away"** can never be detected as away (no location, "door + signal" off, leaving not set to "one is enough") – the profile **never** arms automatically | ⛔ Error | Remove the person, or ⚠ allow "door + signal" for them |
| **"Disarm only if armed automatically"**, but the profile has no automation (no time, no schedule, no "all away") | ⛔ Error | – |
| **"Disarm with door proof"** or **"Let in"**, but the profile has no entry door (sensor of type door) | ⛔ Error | – |
| A person in **"On return"** can never be detected as away – "On return" never applies to them | ⚠️ Warning | Remove the person, or ⚠ allow "door + signal" |
| **Entry delay** shorter than measured (door open → disarmed, with buffer) | ⚠️ Warning | ⚠ Set the entry delay to the measured value |
| **Entry delay** too short for the **door proof** of a person (the phone reports "home" only after the door) | ⚠️ Warning | ⚠ Set the entry delay to the measured value |
| **"Entry delay when approaching"** is on, but no person in the list has a direction signal | ⚠️ Warning | Turn off the extension |
| A **location has reported exactly the same position for at least 24 hours** outside home (faked or stuck app) – it does not count as proof ([more](profiles.md#away-only-with-proof)) | ⚠️ Warning | – (if permanently wrong: remove it from the signals under System → Presence) |
| **"Arm when all away" follows an own trigger** (entity instead of persons) – Hauswacht does not check itself ([more](profiles.md#own-trigger-for-all-away)) | ⚠️ Warning | – |
| **Exit detection** is on, but the profile has no entry delay – it never applies ([more](passage.md#detect-going-out-without-a-pin-exit-detection), from 0.66.0b9) | ⛔ Error | – |
| **Exit detection without a sensor in the house** – a break-in through the entry door also only gives an alarm after the waiting time while someone is home (from 0.66.0b9) | ⚠️ Warning | – (add a sensor in the house in the profile) |
| For a person an **own trigger** decides instead of the signals – Hauswacht does not check this person itself ([more](profiles.md#own-trigger-per-person), from 0.66.0b11) | ⚠️ Warning | – |
| An **own trigger** is set, but persons are still ticked in "arm when all away" – they are ignored ([more](profiles.md#own-trigger-for-all-away), from 0.66.0b3) | 💡 Tip | Untick the persons |
| Something is set for a person under **Presence** (signals, ticks, "detect leaving"), but the person counts **nowhere**: in no "arm when all away" without own trigger, in no "On return", not in the observation (from 0.66.0b3) | 💡 Tip | – |
| **"Door + signal"** is on although the person has a location | 💡 Tip | Turn off "door + signal" |

Measurements count only from **3 measurements** on – before that the assistant says nothing
about them.

**Example:** In the profile "Away", Ben is in "arm when all away". Ben does not share his
location. The assistant shows:

> ⛔ **Error:** Profile Away: Ben can never be detected as away – "arm when all away" never arms
> this profile.
> [Remove Ben from "arm when all away"]
> Suggestion: Allow "door + signal" for Ben (uncertain) (change it elsewhere)

**Example with a measurement:** entry delay 30 s; at the front door, disarming took up to 36 s in
5 measurements:

> ⚠️ **Warning:** Profile Away: entry delay 30 s is shorter than measured (45 s).
> [⚠ Set entry delay to 45 s]

## Check-up in the Assistant tab (since 0.64.0b3)

The [settings page](settings-page.md) has the tab **Assistant**. It shows the **check-up**: all of
the assistant's findings at a glance – the same check as in the side sheets (see above), but for
**all** profiles and the general settings at once, without opening a side sheet.

- At the top there is a summary, e.g. "1 error · 2 warnings · 0 tips" – or "Everything fits
  together".
- Below are the findings, sorted **by profile**; general findings (e.g. "door + signal") are under
  **General**.
- **Check again** fetches the current state, e.g. after new measurements came in.

### Applying a suggestion

1. Click the suggestion (e.g. "Set entry delay to 50 s"). A **preview** opens: where something
   changes (profile or System → Presence) and what – for numbers "before → new", for lists "is
   added" or "is removed".
2. **Apply** saves exactly this one change. Hauswacht then reloads, and the check-up is updated.
3. **Cancel** closes the preview; nothing changes.

Suggestions marked **⚠** make the system more lenient in one place (e.g. a longer entry delay = a
later alarm, or "door + signal" = an uncertain proof of "away"). For them, **Apply** only works
after you tick "I understand …".

**Example:** profile Night, entry delay 30 s. At the front door, disarming took up to 36 s in 4
measurements. The check-up shows:

> ⚠️ **Warning:** Profile Night: entry delay 30 s is shorter than measured (50 s).
> [⚠ Set entry delay to 50 s]

Clicking it shows "before: **30** → new: **50**", the warning and the tick box. Only with the tick
and **Apply** is it saved.

### What the assistant guarantees

- It changes **nothing on its own** – only what you apply one by one.
- It switches nothing, triggers no siren and never touches smoke detectors or the fire alarm.
- Applying only works while **all areas are disarmed**.
- When you apply, Hauswacht checks again whether the suggestion **still** holds. If something
  changed in the meantime (even elsewhere), nothing is saved and the check-up reloads.
- Saving uses the same path as the side sheet – with all the checks that apply there.

## What happens if …? (since 0.64.0b4)

Below the check-up, the tab **Assistant** shows the **scenario preview**. Hauswacht plays typical
situations through with **your** settings and measurements – with **the same rules as in real
operation** (state machine, automation, proof of "away"), but with a made-up clock. Nothing is
switched, no siren, no notification.

Every scenario has a result:

| Sign | Meaning |
|---|---|
| ✅ | As it should be (e.g. "alarm after 30 s", "disarmed as soon as the door opens") |
| ⚠️ | Works, but with a catch (e.g. only with an uncertain proof, or a PIN is needed) |
| ❌ | Unwanted (e.g. false alarm when coming home, burglary without alarm, never arms) |

**"Sequence"** shows step by step what happens – with the time since the start (minutes:seconds).

### The scenarios

Per profile, where it fits:

| Scenario | When | What is played through |
|---|---|---|
| **Burglary through the door …** | per entry door of the profile | Profile armed, the door opens, nobody disarms |
| **Burglary through the door … while someone is home** | profile has exit detection on (from 0.66.0b9) | Without a sensor in the house: ⚠️ siren only after the waiting time. With a sensor in the house: ✅ normal entry delay, because nobody came from inside |
| **Burglary through a window** | profile has windows | Profile armed, a window opens |
| **… comes home** | per person in "On return" | Everyone leaves (if "all away" arms the profile, it is armed automatically, otherwise by hand); two hours later the person comes home. The phone reports 30 s **before** the door – or, if measured, as late **after** the door as observed in your home |
| **Everyone leaves** | profile has "arm when all away" | Everyone leaves through the door one after another, then the phone reports "away". Persons with "one is enough (after a door)" thus count as away, even without a location (from 0.66.0b8) |
| **Everyone is home, the phones go to sleep** | profile has "arm when all away" | All phones report "away" without any door opening (also: Wi-Fi outage). If "after a door" is switched off for someone, the profile arms here – ❌ |
| **Someone steps out briefly – meanwhile the phone of … goes to sleep** | per person with "door + signal" or "one is enough (after a door)" (from 0.66.0b8) | The others are out. Someone opens the door briefly (parcel, rubbish), shortly after that the person's phone goes to sleep |

**Example:** profile Night with "disarm with door proof" for Anna, entry delay 30 s. Anna's phone
reported up to 38 s after the door in three homecomings. The preview shows:

> ❌ **Anna comes home** – False alarm after 30 s: the phone reports too late. Fix: a longer entry
> delay (suggestion in the check-up).

After applying the suggestion (50 s), the same preview shows:

> ✅ **Anna comes home** – Disarmed after 38 s – without PIN, without alarm.

### What is simplified

- Every person has **one** phone that reports "home" or "away" (Wi-Fi, ping …) and – if Hauswacht
  knows one – **one location** that is inside or outside. What your signals are called does not
  matter.
- Measured times count only from **3 measurements** on.
- Guest mode, manual passage, open sensors when arming and control devices are not part of the
  scenarios.

## Set up by goals (since 0.65.0b1)

Instead of setting by setting, the assistant asks **what Hauswacht should do for you**. In the tab
**Assistant** → **Set up by goals**, a side sheet with six steps opens:

1. **Household:** which people Home Assistant knows and whether they can be detected as "away"
   (✓ location, "door + signal" or "one is enough", ✓ direction, ⚠ location frozen, ⚠ cannot be detected as away).
   Display only – set up locations and "door + signal" under System → Presence.
2. **Doors and windows** (*since 0.65.0b2*), sorted by floor and room:
   - **Not in any sensor group yet:** doors, windows and motion sensors that Home Assistant knows
     but that are not monitored yet. **Nothing is pre-selected** – such sensors are often there
     for lights or heating (motion sensors for lights, fridge door); only what you explicitly
     choose is monitored. Doors and windows go into an outside group
     (the existing one with the most doors and windows, or a new "Outside"), motion sensors into
     an inside group (existing or a new "Inside").
   - **Entry doors:** which doors have an **entry delay** (you come in and disarm during that
     time)? All other doors and windows trigger **immediately** – e.g. a patio door that is only
     opened from inside. Pre-selected is what is set up today.
3. **Goals** (several possible), each with a note on which profile it affects ("extends the
   profile Night" or "creates the profile Night"):

   | Goal | What is set up |
   |---|---|
   | **Secure the night** | Profile with the button "Night": sensor groups (suggested: all without motion sensors), optionally "Arm at" and "Disarm at" |
   | **Arm automatically when everyone is away** | Profile with the button "Away": sensor groups, "arm when all away" with persons and waiting time |
   | **Disarm when coming home** | "On return" in the Away profile: persons and how safe (recommended: door proof); the entry delay from your measurements |
   | **Come home at night without turning "Night" off** | "On return: let in" in the Night profile – whoever comes home is let in, the profile stays armed |
   | **Garage or workshop separately** (*since 0.65.0b3*) | Own [area](profiles.md#areas) "Garage" with its own alarm panel (`alarm_control_panel.hauswacht_garage`) – armed independently of the house, e.g. at night while someone in the house is still awake. Plus a sensor group "Garage" and, in the area, a profile with the button "Away", so "All areas → Away" arms the garage too. Optionally "arm when all away" (same persons as the house) and times. If the area exists already, it is extended |

4. **Questions** per goal – pre-filled with what is already set up, otherwise with suggestions.
   Persons who cannot be detected as away are marked with ⚠.
5. **Sirens and recipients** for the affected profiles. Sirens are **only registered, never
   enabled** – enabling stays a separate step under Alarm devices. Sirens of **smoke detectors**
   are shown with 🔥 and the note: as a burglar siren they only get the burglar tone, never the
   fire tone, and Hauswacht does not switch them off during a fire. The smoke detector's fire
   function stays unchanged.
6. **Plan:** per profile "before → new", hints, what the assistant checks afterwards, and the
   [scenario preview](#what-happens-if--since-0640b4) for the settings as they would be afterwards.
   Only **Apply** saves.

### What the assistant guarantees when setting up

- Existing settings are **only extended**: lists (sensor groups, persons, sirens, recipients) are
  extended, the profile's other settings stay as they are.
- Whatever would be **overwritten** (e.g. "On return" from "disarm only if armed automatically" to
  "disarm with door proof") or makes the system **more lenient** (e.g. a longer entry delay) is
  marked with ⚠ in the plan. Then Apply only works after ticking "I have seen the marked
  changes …".
- Applying only works while **all areas are disarmed**. Hauswacht **recomputes** the plan from
  your answers – with the same rules as in the side sheet. If something changed in the meantime,
  nothing is saved.
- **Garage:** sensors from a house group move to the group "Garage", and every house profile that
  monitors the previous group gets the group "Garage" too – so nothing changes for the house, the
  sensors are in both areas. A sensor group is never emptied, and sensors that are in a group via
  a label are not moved.
- Without an answer about entry doors, the sensor types stay as they are.
- Nothing is switched, no siren is enabled, nothing about the smoke detectors' fire function is
  changed and no automation is created.

**Example:** the profiles "Home" and "Away" exist, but none for the night. You choose "Secure the
night" (arm at 22:30) and "Disarm when coming home" for Anna with door proof. The plan shows:

> **New profile Night** – Sensor groups: → Outside · Exit delay → 0 s · Entry delay → 30 s ·
> Arm at → 22:30
>
> **Profile Away** – On return: Nothing → Disarm with door proof · On return – persons: – → Anna ·
> Entry delay: 30 s → 50 s ⚠ more lenient
>
> Good to know: entry delay 50 s from your measurements (longest measured time plus a buffer).

Because of the ⚠ you tick the box, then **Apply**.

## What comes next

- **0.66:** exit detection – whoever forgets the PIN when leaving does not trigger an alarm if
  their phone is "away" shortly afterwards. The scenarios above become the safety table for it:
  coming in must not become less safe.

You can follow the status in the [roadmap](roadmap.md).
