# Settings page "Hauswacht" in the sidebar

[Deutsch](../einstellungsseite.md) | **English**

> **Pre-release:** the page grows in stages. In this stage it **shows** the whole setup;
> **editing** is still done in the settings dialog (button "Edit in the dialog" at the top
> right). The next stages bring editing directly to the page.

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

## Good to know

- The page **switches nothing** – neither sirens nor devices – and in this stage does not change
  any settings either.
- It shows the state at the time of opening; "Reload" (arrow at the top) fetches the current one.
- The same content is available for printing in the card [Hauswacht overview](overview.md).
- The page also works on a phone; wide tables can be scrolled sideways.
