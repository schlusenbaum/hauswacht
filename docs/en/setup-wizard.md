# Setup wizard

[Deutsch](../assistent.md) | **English**

The setup wizard guides you step by step through the setup – no prior knowledge needed. It
briefly explains how Hauswacht works, suggests sensors, sensor groups and alarm profiles, and
shows at the end what is set up and what is still missing.

## Starting

- **During installation:** after "Add integration → Hauswacht", Hauswacht asks "With the setup
  wizard (recommended)" or "Without the wizard". With the wizard, the system is created at the
  end with everything you chose.
- **Later:** Settings → Devices & services → Hauswacht → **Configure → Setup wizard**. Here every
  step saves immediately; if you cancel, what you did so far is kept.

Whatever is already set up is kept – the wizard **only adds**. You can start it as often as you
like, e.g. when new windows are added.

**Starting again:** if something is already set up, the wizard first shows a **chapter
selection** – introduction, look for new sensors, sensor groups, trigger rules, alarm profiles,
recipients, sirens, users, set up another area, trial run, summary. From there it goes on step by
step; every step can still be skipped.

*Example:* two new window contacts were added → setup wizard → "Look for new sensors" → both
windows are suggested → sensor groups → new group or skip.

**You can skip every step.** Whatever is missing appears in the summary at the end.

## The steps

### 1. Introduction (can be skipped)

A page "How Hauswacht works": one sentence and one example per building block – sensors, sensor
groups, trigger rules, alarm profiles, sirens and recipients, users and control devices. If you
know this, choose "Skip the introduction".

### 2. Separate areas? (first setup only)

"Are there separate flats?" – most homes need **one** area. With "Yes" (e.g. a granny flat that is
armed independently) you first set up the main area and then start the wizard again with **"Set
up another area"**: name of the area, then sensors, sensor groups and profiles for it. The
profiles are then called e.g. "Away (Granny flat)". More under [areas](profiles.md#areas).

### 2a. Sensors

Hauswacht looks in Home Assistant for all **doors, windows and motion sensors** that are not in a
sensor group yet and lists them by floor and room. All suggestions are selected – remove what
should not be monitored.

*Example:* found are "Ground floor › Kitchen: kitchen window", "Ground floor › Hallway: hallway
motion" and "Front door". The window in the guest toilet should not be monitored → untick it.

Hauswacht deliberately does not suggest smoke, water or battery sensors. Leave empty = skip.

### 3. How should monitoring work?

| Choice | When it makes sense |
|---|---|
| **With sensor groups (recommended)** | For most homes: every sensor in a group triggers an alarm in an armed profile. |
| **With trigger rules only** | For advanced users: alarm only when several things come together ([trigger rules](trigger-rules.md)). |
| **With both** | Groups for doors and windows, rules in addition, e.g. for motion sensors. |
| **Decide later** | No groups and rules now – continue with recipients and sirens. |

### 4. Sensor groups

Suggestion: doors and windows in the group **"Outside"**, motion sensors in the group
**"Inside"**. You can change names and members; an empty group is not created.

**Entry doors:** doors through which you come home. Only they get the
[entry delay](profiles.md) – whoever comes home has a few seconds to disarm. Other doors trigger
immediately.

*Example:* front door and terrace door are found. You only come home through the front door →
keep only the front door as entry door. The terrace door then triggers immediately (type
"Other", changeable in the sensor group).

A sensor can only be in **one** group. If it is already in another one, the wizard names it with
the group.

### 5. Trigger rules (only with "trigger rules" or "both")

In the settings dialog, "Create a new trigger rule" opens the [rule wizard](trigger-rules.md).
After saving (or cancelling) you come back and can create more rules or continue to the profiles.

During **installation** the rule wizard is not available yet: you create rules afterwards under
Configure → Setup wizard.

### 6. Alarm profiles

Suggestion:

- **Away** – nobody is home: all sensor groups (and rules). After arming you have the **exit
  delay** to leave the house, when coming home the **entry delay** to disarm. Default: 60 and 30
  seconds.
- **Night** – everyone is asleep: only groups without motion sensors (e.g. "Outside"), so you can
  move around the house. No exit delay.

Unticked = not created. If a profile with the button "Away" or "Night" already exists, the wizard
**adds to** it (sensor groups, rules, delays) instead of creating a second one. Everything else
in the profile (sirens, recipients, automation …) stays as it is.

A selected profile needs at least one sensor group or rule.

**Allow tilted windows at night:** if there are [sensors with tilt position](sensors.md#sensors-with-tilt-position-tilted),
the wizard asks for the night profile whether tilted windows are allowed (suggested: yes). Then
the bedroom window may stay tilted at night – opening it fully triggers. "Away" stays strict:
tilted counts as open there.

**By schedule (optional):** for each of the two profiles you can choose a **schedule helper**.
When a time block starts, the profile is armed; when it ends, disarmed – this gives **different
times per weekday**, e.g. "Night" Mon–Thu 22:30–6:00 and Fri–Sat 0:30–8:00. You create the
schedule yourself: Settings → Devices & services → **Helpers** → Create helper → **Schedule**
(Hauswacht cannot create schedules itself). This also works later – start the wizard again and
choose "Alarm profiles", or in the profile under Automation. Empty = no time control; a schedule
already chosen stays. Details: [different times per weekday](profiles.md#different-times-per-weekday-schedule).

### 7. Recipients

Who gets the messages from Hauswacht (alarm, armed, disarmed, faults)? Phones with the Home
Assistant app (`mobile_app_…`) are preselected. Details such as recipients per event you set
later under [notifications](notifications.md).

Afterwards you can send a **test message** – only when you press the button. The wizard shows to
whom it went and where it failed.

*Example:* `mobile_app_annas_phone` selected → "Send test message" → the phone shows "Hauswacht:
Test message from the setup wizard". If nothing arrives, check the app's notification settings.

### 8. Sirens

All sirens in Home Assistant are suggested. **Use in these profiles:** the chosen sirens are added
to the sirens of these profiles (existing ones stay).

Real siren control stays **locked** until you deliberately release it – under
[Alarm devices – sirens → Sirens and release](sirens.md). The wizard releases nothing; in test
mode no siren sounds anyway.

In the settings dialog the wizard then offers the **siren test**: each siren individually,
briefly and quietly, with a confirmation before each sound – like the [siren test](sirens.md).
Afterwards you return to the wizard. During installation the siren test is not available yet.

### 9. Users

Name and – optionally – a **PIN** (4–8 digits). Afterwards you can add more users. If a user has
the same name as a Home Assistant account, it is linked to it; the [alarm card](dashboard.md)
then recognises them without a PIN.

> **Note:** as soon as **one** PIN exists, the panel (and Alexa) requires a PIN to disarm – from
> everyone. So give everyone a PIN or no one. More under [users and PINs](users.md).

Rights per area, validity, cards and duress PIN you set later in the settings dialog. Leave the
name empty = skip.

### 10. Control devices

Only a hint: keypads, cards, stickers, readers, buttons and door locks are set up under System
settings → [control devices](control-devices.md).

### 11. Trial run (settings dialog only)

In the trial run you open doors and windows and walk past motion sensors – Hauswacht ticks off
every sensor of the sensor groups it detects (✅), with "Detected: 3 of 5". **Refresh** shows the
new status.

For this **test mode must be on**. The wizard does **not** switch it on itself but asks you to:
in the card ["Hauswacht Test"](test-mode.md#card-hauswacht-test) or with the switch "Test mode".
Then "Test mode is on – start the trial run". The trial run only reads; it does not arm and
triggers no alarm.

If a sensor stays ⬜ although you triggered it: check battery, radio connection and the device in
Home Assistant. After the trial run switch test mode off again.

### 12. Summary

Two lists:

- **✅ Set up:** sensor groups, rules and for each profile what it watches.
- **⚠️ Still open:** e.g. "No recipients – an alarm reaches nobody yet", "No sirens", "Sirens
  added but not released yet", "No users – operated via the app only" – each with the menu where
  you add it.

The system starts or stays **disarmed**.

## What the wizard never does on the side

- It does **not release sirens** and does not switch off test mode.
- It switches **no devices**. Siren test and test message only happen when you press the button.
- It does not change smoke detectors, automations or scripts.
- It overwrites nothing: existing settings are only added to.

## Afterwards

1. **Try it in test mode** – with the trial run and by arming once for real
   ([test mode](test-mode.md)).
2. Once everything works: **release the sirens** ([sirens](sirens.md)).
3. As needed refine [users and PINs](users.md), set up [control devices](control-devices.md).
