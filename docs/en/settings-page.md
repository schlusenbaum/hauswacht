# Settings page "Hauswacht" in the sidebar

[Deutsch](../einstellungsseite.md) | **English**

> The page **shows** the whole setup, and you edit **everything** directly on it. Since 0.63.2 it
> is the **only way** – the former settings dialog is gone. The page switches nothing – the only
> exception is the **siren test** (tab Alarm devices, card "Siren test"), with confirmation and
> for administrators only.

The page **Hauswacht** in the Home Assistant sidebar shows everything at a glance: which sensors
are in which group, in which profile they are armed, who gets which message – and you change it
right there.

- Visible to **administrators** only.
- **Open it:** from the sidebar, from the link in the device info on the Hauswacht device page,
  via **Configure** on the integration (shows a link to here) or directly at
  `/hauswacht-settings` (e.g. `http://homeassistant.local:8123/hauswacht-settings`).
- **Hide instead of switch off** (from 0.61): the page always exists. Under System → **Settings
  page** you only choose whether it is shown in the sidebar. When hidden, you reach it the ways
  above. Every user can also hide it for themselves via "Edit sidebar" in Home Assistant.
- **New here?** In the tab **Documentation**, [How Hauswacht decides](how-hauswacht-decides.md)
  explains the flows in pictures.
- **Explanations right at the field** (from 0.62): in all side sheets – profiles, sensors,
  trigger rules, sirens and notifications, persons, controls, system – the fields have an **ⓘ**.
  Hovering shows the explanation, tapping (phone, tablet) expands it. Where it helps, a sentence
  **"This is how it behaves:"** describes what the setting currently does.

## The tabs

| Tab | Content |
|---|---|
| **Overview** | Check hints (e.g. "profile without recipients") and the state per area; buttons **Print** and **Emergency sheet** as in the card [Hauswacht overview](overview.md) |
| **Sensors** | All sensors **by sensor group**, with type, state and battery – and one column per profile (matrix, see below). Below that [special sensors](sensors.md#sensors-with-tilt-position-tilted) and [always active](sensors.md#always-active-sensors) |
| **Profiles** | Every profile with groups, rules, times, reaction, recipients and automation |
| **Trigger rules** | Every rule as a sentence and where it applies |
| **Alarm devices** | Sirens with their capabilities and the last test |
| **Notifications** | Recipients per event, speakers, quiet time |
| **People and control devices** | People with rights and credentials (PINs are never shown), PIN rules and master PIN, control devices, action codes |
| **System** | Monitoring, restart, radio silence, radio networks, presence and homecoming, areas, settings page |
| **Documentation** | All pages of this documentation with a short description |

The page remembers the last selected tab (in this browser only).

## Documentation straight from the page

Next to every heading – on the page and in every side sheet – there is a small **"?"**. It opens
the documentation in a new window, right at the matching place: the "?" at "Always active" for
example at [always-active sensors](sensors.md#always-active-sensors), the one in the sheet of a
trigger rule at [trigger rules](trigger-rules.md) (in YAML mode at
[expert mode](trigger-rules.md#expert-mode-yaml)).

The tab **Documentation** lists all pages. The links point to the documentation of **exactly the
installed version** (on GitHub, German or English by the language of Home Assistant) – so you
never read about something your version cannot do yet.

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
("alarm at 2 reports in 60 s").

Example: if the motion sensor in the hallway shows **–** in the column "Night", it is excluded at
night – you can walk through the hallway at night without an alarm.

## Editing sensors

The tab **Sensors** has the buttons for editing. A click opens a side sheet on the right; **Save**
applies immediately, **Cancel** or a click next to it discards.

| What | Where | What you set |
|---|---|---|
| **Single sensor** | Click the sensor's **name** in the table | **Sensor group** (move it or take it out), **type**, **always active** and per profile whether it **triggers on its own** there – untick = excluded in this profile (e.g. hallway motion sensor at night). Plus the **radio silence** of this sensor (as general, own value, never check) with observation and "use recommendation" – see [own limit per sensor](sensors.md#own-limit-per-sensor). If the sensor is in its group via a label, change the group via the label on the entity |
| **Sensor group** | "+ Add sensor group" or "Edit" at the group | Name, sensors (search field → click), **type per sensor**, additionally a label. If vibration sensors are included, the **false alarm protection** appears (reports until alarm, time window) with the button "Use recommendation" (2 in 60 s). Deleting also removes the group from all profiles |
| **Sensor with tilt position** | Special sensors → "+ Add tilt position" or "Edit" | Source (search field), optionally an attribute, then for every known value **open / tilted / closed** – type further values and press Enter. Optionally add it to a group right away |
| **Vibration strength** | Special sensors → "+ Add vibration strength" | Sensor (search field, the current value is shown) and threshold; optionally add it to a group right away |
| **Always active** | "Edit" under always active | Tick whole groups, add or remove single sensors. Below that **sirens when triggered while disarmed**: off = only a message; on = alarm with the chosen sirens, tone (burglar tones only), volume and duration |
| **Sensor from a measurement** | Special sensors → "+ Create sensor from a measurement" | Measurement (`sensor.…`, e.g. temperature), name, upper and/or lower limit, hysteresis, type and where to (group or always active). Hauswacht creates a threshold helper for it – see [create a sensor from another sensor](sensors.md#create-a-sensor-from-another-sensor) |

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

Saved safely:

- **Checked:** every change goes through the same settings rules. A sensor in two groups, a group
  without a name, "tilted" and "closed" for the same value – that is refused with a message at
  the field.
- **Only disarmed:** if an area is armed, the buttons are missing; at the top it says "Changes are
  only possible while all areas are disarmed".
- **Nothing gets overwritten:** if someone changed something on another device
  in the meantime, the page does not save but reloads – then simply try again.
- After saving, Hauswacht reloads its settings (a second or two), then the page shows the new
  state with "✓ Saved."

## Editing profiles

The tab **Profiles** lists every profile with its values; **"Edit"** opens the side sheet,
**"+ Add alarm profile"** an empty one with the usual defaults (30 s delay, 180 s alarm …).

**Explanations right at the field** (from 0.62):

- Every field has an **ⓘ**: hovering shows the explanation, tapping (phone, tablet) expands it.
- Below the most important fields of a section there is the sentence **"This is how it
  behaves:"**. It changes right away when you set something – e.g. "After arming you have 30 s
  to leave. If you then open an entry door, you have 30 s to disarm …".
- Rarely changed fields are under **"More settings"** to expand: icon; duration of the alarm
  reaction and alarm cycles; failed sensors and tampering; tone, volume and speakers; schedule;
  settle time; for the passage "which door" and "end".
- Fields that only make sense with a switch (exit doors, passage times) only appear when the
  switch is on.

| Section | Content |
|---|---|
| **General** | Name, button on the alarm panel, area (only with several areas); under "More settings" the icon (e.g. `mdi:weather-night`) |
| **What is monitored** | Sensor groups (every sensor triggers on its own), **excluded** – the list shows exactly the sensors of the ticked groups –, trigger rules, "Tilted windows allowed" (only with [sensors with tilt position](sensors.md#sensors-with-tilt-position-tilted)) |
| **Times** | Exit and entry delay, duration of the alarm reaction, maximum alarm cycles |
| **When arming** | Open sensors, failed sensors, tampering triggers an alarm |
| **Reaction on alarm** | Sirens (those registered under alarm devices), tone, volume, silent alarm, recipients, additional speakers |
| **Automation** | Arm at / disarm at, weekdays, schedule, persons ("everyone away"), waiting time – see [automation](profiles.md#automation). **"Create schedule ↗"** opens the helpers in a new window ("Create helper" → "Schedule"); then **"Refresh list"** – your entries in the profile are kept |
| **On return** *(new in 0.61, only here)* | What happens when someone comes home: level (Nothing, Disarm only if armed automatically, Disarm with door proof, Disarm also after arming by hand, Let in), its own list of persons, under **"More settings"** the time window phone and door plus the [entry delay after approach](profiles.md#approach-extends-the-entry-delay) with its validity and recommendations to apply. With an **ⓘ** per field, the sentence **"This is how it behaves:"** and a warning for "also after arming by hand" – see [On return](profiles.md#on-return) |
| **Arm by closing the door** | On/off, exit doors (the sensors of type door in the chosen groups), settle time |
| **Passage** | Allow passage, times, which door, sensors on the way – see [passage](passage.md). Letting in by phone has moved to "On return" |

These rules apply: a name is needed and must be unique, every button only
once per area, "On return" (except "Nothing") only with at least one person. **Delete** asks once.

## Editing trigger rules

The tab **Trigger rules** lists every rule as a sentence, below it the profiles in which it applies
("in no profile – no effect" if none). **"Edit"** opens the side sheet, **"+ Add trigger rule"** a
new one with two empty steps. What a trigger rule is: see [trigger rules](trigger-rules.md).

At the top of the sheet you switch between **Form** and **YAML**. Below, while editing, it always
says **what the rule does**, e.g. "front door, then within 90 s group Basement → alarm
immediately" – and what does not fit (e.g. "A sensor is in step 2 and in the step before.").

**Form** – for simple rules:

| Field | Content |
|---|---|
| **Name, result** | Alarm immediately · Entry delay, then alarm · Notification only |
| **Step 1, 2, …** | "What has to happen?" – one of them / all of them / at least … of them; plus sensor groups (ticks) and single sensors (type a name or pick from the list). "Time until the next step" in seconds. Move with ↑ ↓, remove with ✕, "+ Step" for more (up to 10) |
| **Not if before …** | Tick, choose sensors or groups and the period before – see [exception](trigger-rules.md#exception-not-if-before-) |
| **Applies in the profiles** | A tick per profile – the same as "trigger rules" in the profile |

**YAML** – for everything, including complex rules (nested expressions, conditions "only if …").
Structure as in [expert mode](trigger-rules.md#expert-mode-yaml): sensor groups by name, sensors by
entity ID. Example:

```yaml
name: Door then basement
result: alarm
steps:
  - any:
      - sensor: binary_sensor.front_door
    within: 90
  - any:
      - group: Basement
```

- From form to YAML always works. Back to the form only if the rule is simple enough.
- **Complex rules are YAML only** – the "Form" button is greyed out, and the list says
  "(YAML only)".
- **Conditions** ("only if …") are shown in the form; they can only be changed in YAML.
- Only a valid rule is saved: a name is needed and must be unique, no empty step,
  not the same sensor in two consecutive steps. **Delete** asks once and also removes the rule
  from all profiles.

## Editing people

The tab **People and control devices** lists every person with their rights and credentials ("all
rights · PIN · 2 cards"). **"Edit"** opens the side sheet, **"+ Add person"** an empty one. What
people, PINs and rights are: see [users, PINs and lockout](users.md).

| Field | Content |
|---|---|
| **Name** | Suggestions from the Home Assistant accounts. If the person has the same name as an account, they are linked |
| **Active** | Off = the person cannot switch anything (e.g. temporarily blocked) |
| **May …** | arm, disarm, end an alarm. With several areas optionally **per area** – then one box per area |
| **Arm anyway at the keypad** | bypass open sensors, see [arm anyway at the keypad](control-devices.md#arm-anyway-at-the-keypad) |
| **PIN in the alarm card** | e.g. for a wall tablet that is always logged in |
| **Valid from / until** | for guests or tradespeople; outside this time the person is refused |
| **Home Assistant account** | link explicitly (otherwise automatically by name) |
| **PIN** | New PIN and new [duress PIN](users.md#duress-pin), 4 to 8 digits each; empty = keep. Set PINs can be removed here |

- **PINs are never shown** – not even here. The page only shows "PIN set" or "No PIN".
- The [PIN rules](users.md#pin-rules) apply: a PIN must not be another person's
  duress PIN or an action code. If something does not fit, **nothing** is saved and the field
  shows the reason.
- **Delete** asks once.

Further down in the same tab:

| Section | On the page |
|---|---|
| **PIN rules and master PIN** | PIN also to arm, end an alarm without PIN, dashboard buttons despite PIN, PIN in the alarm card for accounts without a person; set or remove the [master PIN](users.md#pins) (never visible) |
| **[Cards, tags and lock IDs](control-devices.md#learning-cards)** | every card with person and state (🟢 active, ⏸️ disabled). **"Edit":** rename, give to another person, disable, delete. **"+ Learn a new card":** hold the card to a keypad or reader – it appears in the sheet by itself (the page checks every 2 seconds) – or type in the number; then choose the person. Random IDs (e.g. phones) are refused. Lock IDs appear the same way when someone unlocks once while everything is disarmed |
| **[Control devices](control-devices.md)** | add, set up, delete – keypad (Zigbee2MQTT device or topic, profile per key, login, emergency key), [keypad (generic)](control-devices.md#keypad-generic) (buttons with a free name, ID for automations, import [ready-made templates](control-devices.md#ready-made-templates) – opens in a new tab; if an **unknown keypad** reported, it is listed at the top of the section with **"Set up"**), [MQTT interface](control-devices.md#mqtt-interface) (base topic, command words, state words), NFC sticker, RFID reader, button (profile per press type; press types of event entities appear by themselves) and door lock (source, Nuki topic or ID sensor, optionally arm when locking). Plus the **learning time for cards** |
| **[Action codes](control-devices.md#action-codes)** | add, change, delete: name, code (2–8 digits), key, keypad, action (event, arm with profile, silent emergency). Only with a keypad. An action code must not equal a PIN – this is checked |

## Editing the system

The tab **System** shows the monitoring state at the top – with the buttons **homecoming
report** and **table** to download the [homecoming observation](observations.md#homecoming-observation).
Below it one card per topic with **"Edit"**. From 0.62, every side sheet has an **ⓘ** with an
explanation behind every field and, where it helps, a sentence **"This is how it behaves:"** –
e.g. for the PIN rules ("Disarming on the panel, keypad and by voice only with a PIN. Arming works
without a PIN …"), the radio silence, action codes, the sensor from a value ("Below 5 the sensor
reports "problem", normal again above 6.") and the learning time.

| Card | Content |
|---|---|
| **Behaviour after restart** | Restore the previous state · always armed (with a profile per area) · always disarmed; "continue a running alarm" – see [behaviour after a restart](installation.md#behaviour-after-a-restart) |
| **Sensor radio silence** | General value (hours until "failed", 0 = off) and a table **per sensor**: longest gap, recommendation, own value – click a sensor to give it an own value. See [radio silence](sensors.md#sensor-radio-silence) Below it: since when it measures; **Reset measurement** deletes the measurement of all sensors and starts again |
| **Radio networks and gateways** | Status sensors, e.g. the Zigbee2MQTT bridge – see [radio networks](sensors.md#monitor-radio-networks-and-gateways) |
| **Presence and homecoming observation** | Observation on/off, persons, home Wi-Fi(s), additional signals per person – see [homecoming observation](observations.md#homecoming-observation). Below that **"When does someone count as away?"** (from 0.61, only here): location outside **check precisely** or **simple**, under "More settings" the **time window for the proof** (default 15 minutes) with a recommendation from the "leaving" measurement and an **apply** button; per person **"Proof for 'away'"**: location only (safe) or also door + signal (uncertain, with a warning and its own time window); warning for persons without a location – see ["away" only with proof](profiles.md#away-only-with-proof). From 0.63 the card also shows **"Who counts as home right now?"**: home/away/unknown per person with the reason, and per profile one line about what the automation and "On return" are doing right now – see [Testing presence](test-mode.md#testing-presence). Below it the block **Measurements**: view, save, reset – see [Measurements on the settings page](observations.md#measurements-on-the-settings-page) |
| **Areas** | add, rename, icon, delete (only without profiles) – see [areas](profiles.md#areas) |
| **Settings page** | **Show in the sidebar** on/off. When hidden, only the sidebar entry disappears – the page stays reachable from the device page, "Configure" on the integration and `/hauswacht-settings` |

## Editing alarm devices

In the tab **Alarm devices**, **"Edit sirens"** opens the side sheet:

- **Registered sirens** – remove with ✕; below, all other sirens (`siren.…`) to tap. When a
  siren is removed, it also disappears from the profiles and its tone is forgotten.
- **Real siren control enabled** – only then can sirens really sound on an alarm. When **turning
  it on**, a warning and a second tick **"I understand …"** appear; without this tick nothing is
  saved ("Please confirm to enable."). Turning it off works any time without asking.
- **Experts: also allow switches as sirens** – after saving, `switch.…` entities also appear in
  the list (see [create siren from switch](sirens.md#create-siren-from-switch)).

Below in the same tab:

| Card | On the page |
|---|---|
| **[Tone per siren](sirens.md#tone-per-siren)** | "Edit" per siren: the tones the device reports, "automatic" (burglar tone) or an own name. **Fire tones** are blocked; only as an expert with the tick "allow fire tone for intrusion" **and** an explicit confirmation – never for sirens with their own smoke detectors |
| **[Siren test](sirens.md#siren-test)** | Reminder (off, every 3 / 6 months, yearly) and pre-warning "siren test in 10 seconds". Below it the **test itself**, see below |
| **[Create siren from switch](sirens.md#create-siren-from-switch)** | Choose the switch and confirm it is a pure alarm siren: Hauswacht creates the helper "change device type of a switch" (type siren) and registers the siren. The switch is **not** switched |

### Siren test on the page (real siren!)

At the bottom of the card **Siren test** each siren is listed with its last test (date, ✅ heard,
❌ not heard). How to test:

1. Tick **"I am on site, housemates are informed"**. Only then can the buttons be pressed.
2. Press **Test …** at a siren.
3. Question "The siren will sound quietly for 3 s. Really start?" → **Yes, start** or
   **Cancel**.
4. While it sounds, **Stop** is ready. Battery smoke detectors often react only after a few
   seconds.
5. "Did you hear the siren?" → **Yes, heard** or **No**. The result is stored with the date.

It is the same way as in the [test card](sirens.md#siren-test), which still has it too. Hauswacht
checks all locks in the background – no matter where you start: all areas disarmed, hardware
release on, test mode off, no fire lock, burglar tones only, at most 10 s. If something is
blocked, the card shows the reason (⛔). Only **administrators** may start it.

## Editing notifications

The tab **Notifications** has two buttons:

**"Edit recipients and events"** – all notification settings on one sheet:

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
**Speech** – further down in the same tab: speakers (default for all events), repetition of the
alarm announcement, quiet hours from–to; per event on/off, announcement or speak, own speakers,
"also during quiet hours" and the text (with preview and "↺ default text"). See
[speech](notifications.md#speech-speakers).

## Good to know

- The page **switches nothing** – no devices, no sirens; the only exception is the
  [siren test](#siren-test-on-the-page-real-siren) with confirmation. It only changes settings, and only
  the ones you save. It only creates helpers when you explicitly want it ("create siren from
  switch", "create sensor from a measurement").
- There is currently no **setup wizard**; a new one on this page is planned – see [setup wizard](setup-wizard.md).
- It shows the state at the time of opening; "Reload" (arrow at the top) fetches the current one.
- The same content is available for printing in the card [Hauswacht overview](overview.md).
- The page also works on a phone; wide tables can be scrolled sideways.
