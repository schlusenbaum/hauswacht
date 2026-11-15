# Installation and first steps

[Deutsch](../installation.md) | **English**

> **As of 0.44.3:** Real siren control is **locked** after installation and has to be enabled
> deliberately – until then Hauswacht cannot make a sound.

## Requirements

- Home Assistant **2026.10** or newer
- Marketplace (from Home Assistant 2026.11), [HACS](https://hacs.xyz) (up to 2026.10) or manual
  installation
- Sensors with "open/closed" in Home Assistant (door, window, motion sensors …)
- Optional: sirens (`siren.…`), the Home Assistant app for push messages, Zigbee2MQTT for
  keypads

Hauswacht needs no cloud and no other integrations.

## Installation

Hauswacht is not (yet) in the Marketplace or HACS catalogue. You therefore add the repository
once via its link; after that, updates arrive as usual.

**Marketplace** (Home Assistant 2026.11 and newer):

1. Settings → **Marketplace**. The first time, read and confirm the note about community
   projects.
2. *Add from link* → `https://github.com/schlusenbaum/hauswacht`. This needs a GitHub account
   connected to the Marketplace – Home Assistant asks for it the first time.
3. Open Hauswacht → **Download**.
4. Restart Home Assistant.

**HACS** (up to Home Assistant 2026.10):

1. HACS → menu (⋮) → **Custom repositories** → `https://github.com/schlusenbaum/hauswacht`,
   type **Integration** → Add.
2. Search for Hauswacht → **Download**.
3. Restart Home Assistant.

Coming from HACS: when you update to 2026.11, the Marketplace takes over the installed
repositories; Hauswacht does not have to be added again.

What gets installed is the file `hauswacht.zip` from the respective
[release](https://github.com/schlusenbaum/hauswacht/releases). New versions show up as an
update.

**Manual:** unpack `hauswacht.zip` from the latest
[release](https://github.com/schlusenbaum/hauswacht/releases) to
`/config/custom_components/hauswacht` and restart Home Assistant.

**Set up:** this button opens your own Home Assistant directly at the Hauswacht setup (the first
time, [My Home Assistant](https://my.home-assistant.io) asks once for its address):

[![Set up Hauswacht](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=hauswacht)

Or by hand: Settings → Devices & services → **Add integration → Hauswacht**. Hauswacht can be
set up only once; several parts of a property are handled with [areas](profiles.md#areas).

## The settings menu

All settings are under **Settings → Devices & services → Hauswacht → Configure**. They can only
be changed while **all areas are disarmed**.

| Menu | Content | Page |
|---|---|---|
| **Alarm triggering** → Sensor groups | Group sensors and set their type | [Sensors](sensors.md) |
| **Alarm triggering** → Trigger rules | Sequences of sensors ("door, then basement") | [Trigger rules](trigger-rules.md) |
| **Alarm triggering** → Always active | Sensors that report even when disarmed | [Sensors](sensors.md#always-active-sensors) |
| **Alarm triggering** → Create a sensor from another sensor | Wizard: measured value → threshold helper → sensor | [Sensors](sensors.md#create-a-sensor-from-another-sensor) |
| **Alarm profiles** | Add and edit profiles | [Profiles](profiles.md) |
| **Alarm devices – sirens** | Sirens and enabling, create siren from switch, tone per siren, siren test | [Sirens](sirens.md) |
| **Notifications** | Recipients, events, custom texts, speech | [Notifications](notifications.md) |
| **System settings** → Areas | House, garage … | [Areas](profiles.md#areas) |
| **System settings** → Users and PINs | People, credentials, rights, PIN rules | [Users](users.md) |
| **System settings** → Control devices | Keypads, NFC stickers, RFID readers, buttons, door locks | [Control devices](control-devices.md) |
| **System settings** → Sensor radio silence | When a sensor counts as failed | [Sensors](sensors.md#sensor-radio-silence) |
| **System settings** → Monitor radio networks and gateways | Zigbee2MQTT, MQTT … | [Sensors](sensors.md#monitor-radio-networks-and-gateways) |
| **System settings** → Presence and homecoming observation | Signals per person (for automation and observation); measure homecomings | [Profiles](profiles.md#how-hauswacht-knows-who-is-home), [Observations](observations.md) |

How the dialog works:

- Every change is **saved immediately** when you submit a form ("✅ Saved").
- Submenus have **"← Back"**, the main menu has **"Done – close"**.
- Forms in Home Assistant have no back button: submit unchanged or close the dialog – what was
  already saved stays.
- If the system is armed while the dialog is open, Hauswacht no longer saves anything.

## Five steps to the first arming

1. **Add a sensor group:** Alarm triggering → Sensor groups → Add sensor group, e.g. "Outside"
   with all door and window contacts. Then check the suggested [types](sensors.md#types) –
   usually they fit.
2. **Add an alarm profile:** Alarm profiles → Add alarm profile, e.g. "Night" with the button
   "Night", sensor group "Outside". Leave the delays as they are for now. Sirens: none yet, or
   "Silent alarm".
3. **Notification:** Notifications → Recipients and events → choose your own phone
   (`mobile_app_…`) as general recipient.
4. **Try it in test mode:** put the card ["Hauswacht Test"](test-mode.md#card-hauswacht-test)
   on a dashboard, switch test mode on, arm "Night", simulate a door. No siren sounds, other
   automations notice nothing.
5. **For real:** test mode off, arm. Enable sirens only once everything works – see
   [Sirens](sirens.md).

Then as needed: [Users and PINs](users.md), [Control devices](control-devices.md),
[Trigger rules](trigger-rules.md), [Areas](profiles.md#areas).

## What Hauswacht creates

One device **"Hauswacht"** with alarm panel, profile selection, buttons, test mode, system
status and profile settings; one more device "Hauswacht &lt;area&gt;" for each additional area.
The complete list is in the [reference](reference.md#entities). On the device page, a link
leads to these instructions.

## Behaviour after a restart

Hauswacht **always starts disarmed**. If the system was armed before, you get the message
"Hauswacht: disarmed after restart". A previous alarm is never resumed on its own. Test mode is
kept, simulated sensors are not. The counter for wrong PIN entries starts at zero.

## Updates

- Updates come via the Marketplace or HACS. Restart Home Assistant afterwards.
- The Hauswacht cards are reloaded automatically; if a card still shows the old version, reload
  the page (in the app: Settings → Companion app → Reset frontend cache).
- Settings from older versions are taken over automatically at startup. What changed is in the
  [CHANGELOG](../../CHANGELOG.md) (German).

Special notes for very old versions:

- **From 0.7.x to 0.8.0:** the five fixed profiles became normal profiles with the same name,
  button and all settings.
- **From 0.2.0:** first add sensor groups and assign them to the profiles, otherwise Hauswacht
  refuses to arm.

## Removing

Settings → Devices & services → Hauswacht → ⋮ → **Delete**, then remove it in the Marketplace or
in HACS. Hauswacht has not changed any devices, automations or scripts; nothing is left behind
except threshold helpers you may have created yourself (under Helpers).
