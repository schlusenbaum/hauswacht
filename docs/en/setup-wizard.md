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
| A person in **"arm when all away"** can never be detected as away (no location, "door + signal" off) – the profile **never** arms automatically | ⛔ Error | Remove the person, or ⚠ allow "door + signal" for them |
| **"Disarm only if armed automatically"**, but the profile has no automation (no time, no schedule, no "all away") | ⛔ Error | – |
| **"Disarm with door proof"** or **"Let in"**, but the profile has no entry door (sensor of type door) | ⛔ Error | – |
| A person in **"On return"** can never be detected as away – "On return" never applies to them | ⚠️ Warning | Remove the person, or ⚠ allow "door + signal" |
| **Entry delay** shorter than measured (door open → disarmed, with buffer) | ⚠️ Warning | ⚠ Set the entry delay to the measured value |
| **Entry delay** too short for the **door proof** of a person (the phone reports "home" only after the door) | ⚠️ Warning | ⚠ Set the entry delay to the measured value |
| **"Entry delay when approaching"** is on, but no person in the list has a direction signal | ⚠️ Warning | Turn off the extension |
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

## What comes next

Next, the tab **Assistant** gets a **preview** of what would happen in typical situations
(burglary, coming home, phone asleep …) – with the same logic as in real operation. After that
comes **setup by goals**. It is meant to

- ask for **goals** instead of settings ("secure the night", "arm automatically when everyone is
  away", "disarm when coming home"),
- know your household (people, phones, signals, measurements) and give recommendations from that,
- explain with examples from your own home what the settings do.

You can follow the status in the [roadmap](roadmap.md).
