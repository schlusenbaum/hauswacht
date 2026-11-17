# Setup wizard

[Deutsch](../assistent.md) | **English**

The setup wizard guides you step by step through the setup – no prior knowledge needed. It
briefly explains how Hauswacht works, suggests sensors, sensor groups and alarm profiles, and
shows at the end what is set up and what is still missing.

> **Pre-release:** the wizard is new and appears in test versions first. So far it covers
> sensors, sensor groups, trigger rules and alarm profiles. Recipients, sirens, users and a trial
> run will follow; until then you set them up in the [settings dialog](installation.md#the-settings-menu).

## Starting

- **During installation:** after "Add integration → Hauswacht", Hauswacht asks "With the setup
  wizard (recommended)" or "Without the wizard". With the wizard, the system is created at the
  end with everything you chose.
- **Later:** Settings → Devices & services → Hauswacht → **Configure → Setup wizard**. Here every
  step saves immediately; if you cancel, what you did so far is kept.

Whatever is already set up is kept – the wizard **only adds**. You can start it as often as you
like, e.g. when new windows are added.

**You can skip every step.** Whatever is missing appears in the summary at the end.

## The steps

### 1. Introduction (can be skipped)

A page "How Hauswacht works": one sentence and one example per building block – sensors, sensor
groups, trigger rules, alarm profiles, sirens and recipients, users and control devices. If you
know this, choose "Skip the introduction".

### 2. Sensors

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
| **Decide later** | Create nothing now – go to the summary. |

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

### 7. Summary

Two lists:

- **✅ Set up:** sensor groups, rules and for each profile what it watches.
- **⚠️ Still open:** e.g. "No recipients – an alarm reaches nobody yet", "No sirens", "No users –
  operated via the app only" – each with the menu where you add it.

The system starts or stays **disarmed**.

## What the wizard never does on the side

- It does **not release sirens** and does not switch off test mode.
- It switches **no devices** and sends no messages.
- It does not change smoke detectors, automations or scripts.
- It overwrites nothing: existing settings are only added to.

## Afterwards

1. Add **recipients**: Notifications → Settings ([notifications](notifications.md)).
2. **Try it in test mode** ([test mode](test-mode.md)).
3. As needed [sirens](sirens.md), [users and PINs](users.md), [control devices](control-devices.md).
