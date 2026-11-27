# Installation and first steps

[Deutsch](../installation.md) | **English**

> **As of 0.66.0b4:** Real siren control is **locked** after installation and has to be enabled
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

Hauswacht is not (yet) in the Marketplace or HACS catalogue – inclusion has been requested, and
the review usually takes months. Until then you add the repository once via its link; after that,
updates arrive as usual. Once Hauswacht is in the catalogue, simply search for "Hauswacht" in the
Marketplace.

**Quickest:** [open Hauswacht in the Marketplace](https://my.home-assistant.io/redirect/marketplace_repository/?owner=schlusenbaum&repository=hauswacht&category=integration) – the link opens your own Home
Assistant instance directly at Hauswacht (the first time, My Home Assistant asks once for its
address). Or by hand:

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

During setup Hauswacht only creates the entry. **Everything is set up on the settings page** – the
dialog shows a link to it.

## The settings page

All settings are on the page **Hauswacht** in the sidebar (administrators only) – see
[settings page](settings-page.md). It shows the whole setup at a glance, and you edit everything
right there. Saving only works while **all areas are disarmed**.

> **Since 0.63.2** the former settings dialog (Settings → Devices & services → Hauswacht →
> **Configure**) is gone. "Configure" only shows a link to the settings page. The page can do
> everything the dialog could; your settings stay unchanged.

| Tab | Content | More |
|---|---|---|
| **Overview** | Check hints and state per area | [System overview](overview.md) |
| **Sensors** | Sensor groups and types, sensors with tilt position, vibration, sensor from a measurement, always active | [Sensors](sensors.md) |
| **Profiles** | Alarm profiles with delays, reaction, automation, on return, passage | [Profiles](profiles.md) |
| **Trigger rules** | Sequences of sensors ("door, then basement") | [Trigger rules](trigger-rules.md) |
| **Alarm devices** | Sirens and release, siren from switch, tone per siren, siren test | [Sirens](sirens.md) |
| **Notifications** | Recipients, events, own texts, speech | [Notifications](notifications.md) |
| **People and control devices** | People, PINs, rights, PIN rules, cards, keypads, NFC stickers, RFID readers, buttons, door locks, action codes | [Users](users.md), [Control devices](control-devices.md) |
| **System** | Behaviour after restart, radio silence, radio networks and gateways, presence and homecoming observation, areas, page in the sidebar | [below](#behaviour-after-a-restart), [Observations](observations.md), [Areas](profiles.md#areas) |
| **Documentation** | This documentation | – |

If you set up Hauswacht for the first time, best read
[How Hauswacht decides](how-hauswacht-decides.md) first – it shows the flows as pictures.

## Five steps to the first arming

Everything on the [settings page](settings-page.md):

1. **Add a sensor group:** tab **Sensors** → **Add sensor group**, e.g. "Outside" with all door
   and window contacts. Then check the suggested [types](sensors.md#types) – usually they fit.
2. **Add an alarm profile:** tab **Profiles** → **Add alarm profile**, e.g. "Night" with the
   button "Night", sensor group "Outside". Leave the delays as they are for now. Sirens: none
   yet, or "Silent alarm".
3. **Notification:** tab **Notifications** → **Edit recipients and events** → choose your own
   phone (`mobile_app_…`) as general recipient.
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
The complete list is in the [reference](reference.md#entities). On the device page, the link in the
device info leads to the [settings page](settings-page.md) (from 0.61; these instructions are
there in the **Documentation** tab).

## Behaviour after a restart

**Settings page → System → Behaviour after restart.** What happens when Home Assistant restarts – e.g.
after an update, a nightly backup or a power cut. Three options:

| Setting | What happens after the restart | Meant for |
|---|---|---|
| **Restore the previous state** (default) | if the system was armed, it is armed again right away; if it was disarmed, it stays disarmed | almost everyone |
| **Always armed** (with a fixed profile) | about one minute after startup, the chosen profile is armed normally | holiday homes, unoccupied areas |
| **Always disarmed** | always disarmed; if the system was armed, you get the message "disarmed after restart" | whoever prefers to decide themselves (behaviour up to 0.44) |

**Only after a real restart of Home Assistant.** If only Hauswacht is reloaded – e.g. after
saving settings – the state always stays as it was: "always armed" then does not arm, "always
disarmed" does not disarm.

### Restoring in detail

The system is armed again **at once** – with the same profile and the same bypassed sensors. It
is **not checked again** and there is **no exit delay**: the system was already armed. You get
the message "Hauswacht: armed again after restart".

What was running when Home Assistant restarted:

| Running at the time … | After the restart |
|---|---|
| nothing (armed) | armed |
| the **exit delay** | armed – a restart takes longer than the delay, whoever wanted to leave is long gone |
| the **entry delay** | the entry delay **starts again**. Whoever just came home could not disarm during the restart, neither at the keypad nor in the app – without a new delay, the first movement in the hallway would cause an instant alarm |
| an **alarm** | **not continued** (default): no sirens, the system is armed. The alarm recipients get an **important message** "Hauswacht: alarm before the restart" (breaks through Do Not Disturb, with a "Disarm" button) that names the triggering sensor. With "Resume a running alarm" see below |

**Sensors at startup.** After a restart, radio sensors report back one by one – many are briefly
"unavailable". That is why there is a **startup phase of two minutes** after restoring (counted
from the moment Home Assistant has finished starting):

- **No failure messages** during this time. If a sensor is still missing after the startup
  phase, you get the message "sensor lost".
- **Sensors that come back closed:** nothing happens.
- **Sensors that come back open:** Hauswacht cannot tell whether the window was already open
  before the restart or was opened during it. Therefore:
  - **Entry doors** (type door) start the **entry delay** – maybe someone is just coming home
    who can then disarm.
  - **All others** (windows, motion …) are **bypassed until closed** instead of causing a siren
    alarm at night. After the startup phase you get the message "Hauswacht: open after restart"
    with the names. If such a sensor briefly reports "unavailable" and then open again, there is
    still no alarm. As soon as it closes, it is monitored normally again.
- **Sensors already reported open when the state is restored** (their gateway was faster than
  Hauswacht) are **always bypassed until closed – entry doors too**. A door that is already open
  when Hauswacht starts was more likely forgotten than just opened; an entry delay would otherwise
  sound the siren at night after 30 seconds.
- Sensors that were bypassed before the restart stay bypassed.

**Example:** the system is armed "Night", at 3:00 Home Assistant restarts for a backup. At 3:02
Hauswacht is armed again, profile "Night", and sends "armed again after restart (Night)". The
tilted bathroom window was already bypassed before and stays bypassed.

The profile automation also remembers whether it had armed – "On return – Disarm, only if armed
automatically" keeps working after a restart.

### Always armed

For each area you choose a profile (e.g. "Away"). About **one minute** after Home Assistant has
started – so the radio sensors report again –, it is armed **quite normally**: with the check of
open and failed sensors according to the rules of the profile, and with exit delay. If this fails
(e.g. window open), you get the usual message "not armed". Areas without a profile stay disarmed.
The logbook says "Automation", the message "armed automatically (restart)". Like every automation
message, it is sent via the event **"Automation"** in the [notifications](notifications.md)
(default: on) – if you switched this event off, you don't get it. "Not armed" is sent via the
event "Arming rejected" (default: on).

> "Always armed" also arms if the system was disarmed **before** the restart – e.g. because
> someone was home. For an occupied house, "Restore" is therefore the better choice.

### Resume a running alarm

**Settings page → System → Behaviour after restart → "Resume a running alarm"** (default off, only
together with "Restore the previous state").

| | Off (default) | On |
|---|---|---|
| Alarm was still running (sirens on) | no alarm, system armed, important message to the alarm recipients | as soon as Home Assistant has started, the alarm is **triggered again** – like a new alarm with the reaction of the profile, the alarm time starts over |
| Alarm was already over (sirens off, only not yet acknowledged) | no alarm, message | no alarm, message |

Trade-off: "On" is right if a burglary should keep being reported loudly even after Home
Assistant crashed. "Off" prevents a false alarm from starting the sirens a second time after a
nightly restart (e.g. for a backup). Even with "Off", the system is armed afterwards: if someone
keeps moving in the house, the next sensor triggers a new alarm at once.

When resuming, too: sirens only via the usual locks – not in test mode, not without the siren
release, never during a fire. The [overview](overview.md) shows the setting under "After
restart".

### Always the same

Whatever the setting:

- A previous **alarm is not continued** – except with "Resume a running alarm" (see below);
  otherwise sirens never go on because of a restart. Sirens that
  Hauswacht had switched on for the alarm and that are still sounding are switched off after
  startup ([details](sirens.md#siren-was-still-on-at-a-restart)).
- **Test mode** is kept, simulated sensors are not.
- The counter of wrong PIN entries starts at zero.
- If the profile has been deleted in the meantime, the system stays disarmed and reports this.
- With several areas, this applies to each area separately.

The [overview](overview.md) shows the setting under "Monitoring".

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
except threshold helpers you may have created yourself (under Helpers). If you confirmed the
[repair for the keypads' code entity](control-devices.md), that entity (e.g.
`sensor.keypad_hallway_action_code`) stays disabled – enable it again under Settings → Entities
if needed.
