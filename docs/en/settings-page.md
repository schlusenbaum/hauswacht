# Settings page "Hauswacht" in the sidebar

[Deutsch](../einstellungsseite.md) | **English**

> **Pre-release:** the page grows in stages. It **shows** the whole setup; you already edit
> **sensors**, **alarm profiles**, **alarm devices** and **notifications** directly on the page.
> Trigger rules, people and system are still edited in the settings dialog (button "Edit in the
> dialog" at the top right) – that follows in the next stages.

The settings dialog always shows just one step. The page **Hauswacht** in the Home Assistant
sidebar, on the other hand, shows everything at a glance: which sensors are in which group, in
which profile they are armed, who gets which message.

- Visible to **administrators** only.
- **In addition** to the dialog and the [setup wizard](setup-wizard.md) – all ways use the same
  settings. What is changed in the dialog appears on the page right after "Reload".
- To hide it: Configure → System → **Settings page in the sidebar** → untick.

## The tabs

| Tab | Content |
|---|---|
| **Overview** | Check hints (e.g. "profile without recipients") and the state per area |
| **Sensors** | All sensors **by sensor group**, with type, state and battery – and one column per profile (matrix, see below). Below that [special sensors](sensors.md#sensors-with-tilt-position-tilted) and [always active](sensors.md#always-active-sensors) |
| **Profiles** | Every profile with groups, rules, times, reaction, recipients and automation |
| **Trigger rules** | Every rule as a sentence and where it applies |
| **Alarm devices** | Sirens with their capabilities and the last test |
| **Notifications** | Recipients per event, speakers, quiet time |
| **People and control devices** | Users with rights and credentials (PINs are never shown), control devices, action codes |
| **System** | Radio silence, radio network, learning, restart, homecoming |

The page remembers the last selected tab (in this browser only).

## The matrix "sensor × profile"

In the tab **Sensors** every sensor has a row, its sensor group above it. Every profile has a
column:

| Sign | Meaning |
|---|---|
| ✓ | triggers **on its own** in this profile |
| R | only counts in **trigger rules** of this profile |
| – | **excluded** in this profile |
| empty | not monitored in this profile |

Groups with vibration sensors show their [false alarm protection](sensors.md#vibration-sensors)
("alarm at 2 reports in 60 s"). The **search field** filters by name.

Example: if the motion sensor in the hallway shows **–** in the column "Night", it is excluded at
night – you can walk through the hallway at night without an alarm.

## Editing sensors

The tab **Sensors** has the buttons for editing. A click opens a side sheet on the right; **Save**
applies immediately, **Cancel** or a click next to it discards.

| What | Where | What you set |
|---|---|---|
| **Single sensor** | Click the sensor's **name** in the table | **Sensor group** (move it or take it out), **type**, **always active** and per profile whether it **triggers on its own** there – untick = excluded in this profile (e.g. hallway motion sensor at night). If the sensor is in its group via a label, change the group via the label on the entity |
| **Sensor group** | "+ Add sensor group" or "Edit" at the group | Name, sensors (search field → click), **type per sensor**, additionally a label. If vibration sensors are included, the **false alarm protection** appears (reports until alarm, time window) with the button "Use recommendation" (2 in 60 s). Deleting also removes the group from all profiles |
| **Sensor with tilt position** | Special sensors → "+ Add tilt position" or "Edit" | Source (search field), optionally an attribute, then for every known value **open / tilted / closed** – type further values and press Enter. Optionally add it to a group right away |
| **Vibration strength** | Special sensors → "+ Add vibration strength" | Sensor (search field, the current value is shown) and threshold; optionally add it to a group right away |
| **Always active** | "Edit" under always active | Tick whole groups, add or remove single sensors. Sirens for "always active" stay in the dialog |

**Finding sensors without knowing their names:** when adding, the list immediately shows all
**suitable** sensors (door, window, motion, vibration, water … as well as locks and garage doors),
sorted by room – ready to click. The search field only narrows the list. Below it are two
switches:

- **Also show other entities** – e.g. binary sensors without a suitable device class
  (connectivity, update …), which are hidden otherwise.
- **Also show sensors that are already in a group** – with the group named ("in Outside").
  Normally hidden, because a sensor belongs to exactly one group.

For special sensors the list shows suitable sources: for the tilt position select helpers and
sensors with values like "tilted" or names with "window", "handle" …; for the vibration strength
number helpers and sensors with "vibration" in their name.

As safe as the dialog:

- **The same rules:** the page uses the same checks as the dialog. A sensor in two groups, a group
  without a name, "tilted" and "closed" for the same value – that is refused with a message at
  the field.
- **Only disarmed:** if an area is armed, the buttons are missing; at the top it says "Changes are
  only possible while all areas are disarmed".
- **Nothing gets overwritten:** if someone changed something in the dialog or on another device
  in the meantime, the page does not save but reloads – then simply try again.
- After saving, Hauswacht reloads its settings (a second or two), then the page shows the new
  state with "✓ Saved."

## Editing profiles

The tab **Profiles** lists every profile with its values; **"Edit"** opens the side sheet,
**"+ Add alarm profile"** an empty one with the usual defaults (30 s delay, 180 s alarm …). The
sections match the dialog:

| Section | Content |
|---|---|
| **General** | Name, icon (e.g. `mdi:weather-night`), button on the alarm panel, area (only with several areas) |
| **What is monitored** | Sensor groups (every sensor triggers on its own), **excluded** – the list shows exactly the sensors of the ticked groups –, trigger rules, "Tilted windows allowed" (only with [sensors with tilt position](sensors.md#sensors-with-tilt-position-tilted)) |
| **Times** | Exit and entry delay, duration of the alarm reaction, maximum alarm cycles |
| **When arming** | Open sensors, failed sensors, tampering triggers an alarm |
| **Reaction on alarm** | Sirens (those registered under alarm devices), tone, volume, silent alarm, recipients, additional speakers |
| **Automation** | Arm at / disarm at, weekdays, schedule, persons ("everyone away"), waiting time, disarm on arrival, door-proof window – see [automation](profiles.md#automation). **"Create schedule ↗"** opens the helpers in a new window ("Create helper" → "Schedule"); then **"Refresh list"** – your entries in the profile are kept |
| **Arm by closing the door** | On/off, exit doors (the sensors of type door in the chosen groups), settle time |

The same rules as in the dialog apply: a name is needed and must be unique, every button only
once per area, "disarm on arrival" only with persons. **Delete** asks once.

## Editing alarm devices

In the tab **Alarm devices**, **"Edit sirens"** opens the side sheet:

- **Registered sirens** – remove with ✕; below, all other sirens (`siren.…`) to tap. When a
  siren is removed, it also disappears from the profiles and its tone is forgotten – as in the
  dialog.
- **Real siren control enabled** – only then can sirens really sound on an alarm. When **turning
  it on**, a warning and a second tick **"I understand …"** appear; without this tick nothing is
  saved ("Please confirm to enable."). Turning it off works any time without asking.
- **Experts: also allow switches as sirens** – after saving, `switch.…` entities also appear in
  the list (see [create siren from switch](sirens.md#create-siren-from-switch)).

The **tone per siren** and the fire tone release are still set in the dialog
([tone per siren](sirens.md#tone-per-siren)). There is deliberately **no siren test** on the page
– only in the [test card](sirens.md#siren-test).

## Editing notifications

The tab **Notifications** has two buttons:

**"Edit recipients and events"** – everything from "Notifications – settings" in the dialog on
one sheet:

| Section | Content |
|---|---|
| **General recipients** | get every event that has no own recipients |
| **Switches** | Also notify in test mode · button "Disarm" in the alarm message · important messages break through "Do not disturb" |
| **Duress PIN silently reports to** | who is notified silently on a duress PIN |
| **Events** | a tick per event (on/off); expand → **own recipients**. On the right it says who gets it – "general recipients" if no own ones are ticked |
| **Reminder** | persons, suggested profile, after how many minutes – see [reminder](notifications.md#reminder-everyone-away-system-disarmed) |

Recipients per **profile** (who is notified on an alarm in this profile) are set in the profile
(section "Reaction on alarm").

**"Own texts"** – below, every event is listed with "Hauswacht's text" or your own text. "Edit"
opens title and text – the first time they show **Hauswacht's text as a template** (e.g.
`Profile {profile} armed ({who}).`), which you simply change. The **preview** with example values
changes as you type. Placeholders like `{sensor}` or `{profile}` are listed below. A typo is
refused, e.g. "Text has an error: unknown placeholder {foo}".

- **"↺ Default text"** resets title and text to the template; save – done.
- Template saved **unchanged** = Hauswacht's text stays (nothing is saved).
- `{text}` is Hauswacht's complete text. A custom text replaces it entirely – on an alarm e.g.
  also the note which sirens are running. To keep it, include `{text}`.

Example:

```text
Title:  Alarm in {area}
Text:   {sensor} triggered at {time} (profile {profile}).
```

More under [custom texts and placeholders](notifications.md#custom-texts-and-placeholders).
Speech and quiet hours are still set in the dialog.

## Good to know

- The page **switches nothing** – neither sirens nor devices. It only changes settings, and only
  the ones you save.
- It shows the state at the time of opening; "Reload" (arrow at the top) fetches the current one.
- The same content is available for printing in the card [Hauswacht overview](overview.md).
- The page also works on a phone; wide tables can be scrolled sideways.
