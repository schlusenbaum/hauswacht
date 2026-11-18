# Alarm profiles and areas

[Deutsch](../profile.md) | **English**

## Alarm profiles

**Alarm profiles → Add alarm profile.** There are no predefined profiles – you add as many as
you need, e.g. "Home", "Night", "Away", "Vacation".

> **Every profile is a way of arming.** "Disarmed" is not a profile but the basic state –
> reached with "Disarm" on the alarm panel, the disarm key on the keypad or the alarm card. A
> profile called "Disarmed" would arm the system. If you add one out of habit (e.g. from other
> alarm integrations), please delete it again.

| Setting | Meaning |
|---|---|
| Name, icon | How the profile appears in the selection list, messages and on the alarm panel |
| Alarm panel button | Optional: Home, Night, Away, Vacation or Custom. Each button belongs to at most one profile (per area) |
| Area | Only with several [areas](#areas) |
| Sensor groups – each sensor triggers alone | Each sensor of these groups triggers on its own (door with entry delay, window instantly …) |
| Excluded sensors | Sensors of these groups that do **not** trigger on their own in this profile (e.g. upstairs hallway motion in "Night"); they still count in trigger rules |
| Trigger rules | In addition: sequences of sensors, see [Trigger rules](trigger-rules.md). The field only appears once trigger rules exist |
| Exit / entry delay | Time to leave, or to disarm after entering (default 30 s each) |
| Alarm reaction time | How long one alarm cycle lasts (default 180 s) |
| Open sensors when arming | refuse · allow after confirmation · bypass automatically. Confirm: "Arm anyway" in the card or push – or at the keypad [the same key once more](control-devices.md#arm-anyway-at-the-keypad) |
| Unavailable sensors when arming | refuse · allow after confirmation |
| Maximum alarm cycles | How often the alarm may trigger again after an alarm |
| Tamper triggers alarm | Otherwise tampering is only reported |
| Tilted windows allowed | Only with [sensors with tilt position](sensors.md#sensors-with-tilt-position-tilted) (hidden otherwise): a tilted window counts as closed, only opening it fully triggers. **Off** (default): tilted counts as open. Typical: on for "Night", off for "Away". The [setup wizard](setup-wizard.md#6-alarm-profiles) asks about it for the night profile |
| Sirens, tone, volume, silent alarm | Reaction on alarm, see [Sirens](sirens.md) |
| Notify (alarm) | Who gets a push message on an alarm |
| Additional speakers | Announcements of this profile, see [Speech](notifications.md#speech-speakers) |
| Automation | Time and presence, see [below](#automation) |
| Arm by closing the door | see [below](#arm-by-closing-the-door) |

The top of the form shows which sensors are currently armed in this profile.

A profile **without sensor groups and without trigger rules** cannot be armed – so you never get
the impression that the house is protected while nothing is monitored.

**Operating:** profiles with a button via the alarm panel; every profile – also without a button
– via the selection list "Profile" and the button "Arm", or the action `hauswacht.arm`. While
armed, the alarm panel shows profiles without their own button as "custom"; the attribute
`profile_name` names the profile.

The most important values can also be changed on the dashboard, see
[Profile settings on the dashboard](dashboard.md#profile-settings-on-the-dashboard).

## Automation

In the profile, expandable under **Automation**. All fields are optional – empty means: off.

| Setting | Effect |
|---|---|
| Arm at / Disarm at | Time at which the profile is armed or disarmed |
| Or by schedule (helper) | For **different times per weekday**: a schedule helper; start of a time block = armed, end = disarmed, see [below](#different-times-per-weekday-schedule) |
| On these days | Days on which the times apply; empty = every day. Overnight see [below](#times-overnight-and-manual-arming) |
| Arm when all of these persons are away | If all selected persons are away, the profile is armed after the delay |
| Delay before arming | Default 15 minutes. If someone comes back during this time, nothing is switched |
| Disarm when one of these persons arrives home | **Off** (default), **As before** or **With door proof**, see [below](#disarm-on-arrival) |
| Door proof: how long before the door the phone may report "home" | Only for "With door proof". Default 5 minutes, 1–30. Does **not** delay the alarm, see [What the time window means](#what-the-time-window-means) |

Safety rules:

- Automatic arming only while the system is disarmed – never on top of another profile.
- Open or failed sensors are **never** confirmed automatically. If arming fails because of this,
  you get a system message.
- A **running alarm** is never ended automatically. A running entry delay only with door proof.
- A person whose location is unknown or unavailable does **not** count as away.
- After a restart, the [behaviour after restart](installation.md#behaviour-after-a-restart)
  applies (default: previous state); the presence automation only acts on the next change of a
  person.

Phones that are only detected via Wi-Fi (ping by the router) sometimes briefly report "away" in
standby. The delay catches that.

Instead of arming automatically, Hauswacht can also just remind you: see
[Reminder "everyone away"](notifications.md#reminder-everyone-away-system-disarmed).

### Times, overnight and manual arming

**Overnight:** if "Disarm at" is before "Arm at" (e.g. arm 23:00, disarm 06:30), the morning
belongs to the night before. Hauswacht then also disarms on the morning **after** an active day.

Example "Night", arm 23:00, disarm 06:30, days Mon–Fri:

| When | What happens |
|---|---|
| Friday 23:00 | armed (Friday is active) |
| Saturday 06:30 | **disarmed** – the night started on Friday |
| Saturday 23:00 | nothing (Saturday is not active) |
| Sunday 06:30 | nothing – Saturday and Sunday are not active |
| Monday 06:30 | disarmed (Monday is active) |

A daytime profile (e.g. arm 07:30, disarm 16:00) only applies on the chosen days.

**Manual arming:** a profile with times can be armed by hand at any time. Then:

- **"Arm at"** does nothing if the system is already armed – Hauswacht never switches over an
  armed profile.
- **"Disarm at"** disarms the profile, no matter who armed it (not during an entry delay or an
  alarm).
- A **different** profile, armed by hand, is not ended by "Disarm at" – the time only applies to
  its own profile.

Example: "Night" armed by hand at 22:00 → 23:00 nothing → 06:30 disarmed.


### Different times per weekday (schedule)

"Arm at" and "Disarm at" apply equally on all selected days. If you need **different times on
different days**, use a Home Assistant **schedule helper** instead of a second profile:

1. Settings → Devices & services → **Helpers** → Create helper → **Schedule**, name e.g. "Night".
2. In the schedule, drag the time blocks per weekday during which the profile should be armed.
3. In the profile under **Automation → Or by schedule (helper)** choose the schedule – or in the
   [setup wizard](setup-wizard.md) in the step alarm profiles.

You create the schedule yourself: Home Assistant offers integrations no official way to create
schedules, and Hauswacht does not reach into internal parts that may change with updates. Later
you change the times directly in the schedule – you don't need to open Hauswacht for that.

*Example "Night":*

| Day | Time block in the schedule | What happens |
|---|---|---|
| Mon–Thu | 22:30–24:00 and 0:00–6:00 | 22:30 armed, 6:00 disarmed |
| Fri | 0:00–6:00 | 6:00 disarmed (no block on Friday evening) |
| Sat | 0:30–8:00 | 0:30 armed, 8:00 disarmed |
| Sun | 0:30–8:00 and 22:30–24:00 | 0:30 armed, 8:00 disarmed, 22:30 armed |

A block across midnight is entered in the schedule as two blocks (until 24:00 and from 0:00);
Home Assistant shows it as continuous – Hauswacht does not switch in between.

The same rules apply as for the times:

- **Arming** only from "disarmed"; in **guest mode** nothing is armed. Open sensors are never
  confirmed – you get a message instead.
- **Disarming** only if exactly this profile is armed – never during entry delay or an alarm. If
  you armed the profile by hand, the end of the block still disarms it.
- The automation weekdays do **not** apply to the schedule – the schedule has its own.
- **After a restart** the schedule catches up on nothing: if a block started or ended during the
  restart, the [behaviour after restart](installation.md#behaviour-after-a-restart) applies. This
  way a system disarmed by hand is not armed again by a restart.
- Times and schedule can be combined, but usually only one of them makes sense.

### How Hauswacht knows who is home

The basis is the **person** in Home Assistant (`person.…`). In addition you can choose more
**signals** per person – under **System settings → Presence and homecoming observation**, in the
second step. The [homecoming observation](observations.md#additional-signals-per-person) uses
the same signals; you set them in one place only.

Suitable are e.g. the Wi-Fi sensor of the companion app, Bluetooth (Bermuda), a router tracker,
the direction from the Proximity integration or any binary sensor (on = home) – such as a
HomeKit variable "Martin home".

| The person counts as … | when … |
|---|---|
| **home** | any signal reports home (the person itself or one of the signals) |
| **away** | **all** signals reliably report "away" |
| unknown | otherwise, e.g. a signal is "unavailable" – this **never** counts as away |

**Example:** Anna is "away" according to her person entity, but her Wi-Fi sensor still reports
the home Wi-Fi. Then Anna is home, and "Arm when all of these persons are away" waits. Only when
the Wi-Fi is gone too does the delay start.

This way a signal that drops out briefly does not arm right away, and the fastest signal
detects the arrival.

### Disarm on arrival

Three levels, default is **Off**:

| Level | When disarmed | What protects against a wrong location |
|---|---|---|
| **Off** | never | – |
| **As before** | One of the persons arrives home – only if Hauswacht armed the profile **itself** and no door has opened yet (not during the entry delay) | coupling to "Arm when all of these persons are away" |
| **With door proof** | One of the persons arrives home **and** an entry door is opened – both within the time window, in any order. Also during the entry delay, no matter how the system was armed | two proofs: location **and** door |

**"With door proof" in everyday life**

- *The location comes too late:* Christian opens the front door, the entry delay runs. 20
  seconds later his phone reports "home" → Hauswacht disarms before the alarm comes.
- *The location comes early:* the phone already reports "home" at the street corner. Nothing
  happens yet. Two minutes later the front door opens → disarmed at once.
- *Phantom homecoming:* Niklas's phone reports "home" at night although he is out. Without an
  opened door, **nothing** happens.
- *Burglary:* someone opens the door, but nobody has come home → normal entry delay and alarm.

#### What the time window means

The time window **never delays the alarm**. When the alarm comes is decided by the **entry
delay** alone – exactly as without this feature. The time window only says how far apart the
location and the door opening may be to count as **one** homecoming.

Example with 30 seconds entry delay and 5 minutes time window:

| What happens | Result |
|---|---|
| Phone reports "home", the door opens 2 minutes later | **Disarmed at once** when the door opens, no countdown |
| Phone reports "home", the door opens only 7 minutes later | Too long ago: normal entry delay, alarm after 30 s (unless someone disarms) |
| Door opens, 20 s later the phone reports "home" | **Disarmed** after 20 s (still within the entry delay) |
| Door opens, the phone reports only after 45 s | **Alarm** after 30 s as always; the phone does not end it |
| Door opens, no phone reports (burglar, or you without your phone) | **Alarm** after 30 s as always |

In short: the phone may report up to 5 minutes **before** the door. If it reports **after** the
door, this has to happen within the entry delay.

Precisely:

- **Arriving home** means: the person was reliably away before and is home now. Whoever was home
  all the time does not "arrive home".
- Arrival and door only count while the profile is **armed** or the **entry delay** is running –
  not during the exit delay.
- All **entry doors** (sensors with the role "entry") count as a door. A door that triggers an
  instant alarm is no proof.
- A running **alarm** is never ended.
- After disarming, both proofs expire; they are not collected for later.

**Which entry delay do I need?** If the location only comes after the door opens, the entry
delay has to last that long. The [homecoming observation](observations.md#recommendation-for-disarm-with-door-proof)
calculates this per person and suggests a value.

> **Remaining risk:** whoever has the phone of one of the persons **and** access to the door
> (e.g. phone and key stolen) disarms with it. For "Vacation" better choose **Off**.

The level "As before" corresponds to the former switch "Disarm on arrival"; existing settings
are taken over.

### Guest mode

Guests, a babysitter or tradesmen are in the house but have no tracking – to Hauswacht the house
looks empty. So that the automation does not arm then, there is the **guest mode**.

**While it is on,** Hauswacht does **not arm** the area **automatically**: neither by time nor
"when everyone is away" nor "always armed after restart". The reminder "nobody home, not armed"
is not sent. Arming **by hand** (keypad, card, tablet, Alexa) still works; "Disarm on arrival"
works normally. If the automation wants to arm, you get the message "Guest mode on – “Night” was
not armed automatically".

**Switching it on:**

- **Alarm card:** button **👥 Guest mode** → for how long: quickly *until I switch it off*,
  *4 hours*, *until tomorrow 10 am* or *3 days* – or **freely**: choose date and time under "Or
  until:" (suggested is tomorrow at the same hour) and "Apply". The card then shows "Guest mode
  on – until …" and the button "End guest mode". Everyone who may use the card can switch it –
  without a PIN.
- **Switch** `switch.hauswacht_guest_mode`: on/off for **all** areas, until switched off.
- **Action** `hauswacht.guest_mode` – also with an end time and for single areas:

```yaml
action: hauswacht.guest_mode
target:
  entity_id: alarm_control_panel.hauswacht   # or alarm_control_panel.hauswacht_all
data:
  "on": true
  until: "2026-11-20 12:00:00"   # leave out = until switched off
```

**Areas:** the default is **all areas**. An alarm card with `bereich: granny_flat` switches the
guest mode only for this area – so the granny flat can have guests while the house is armed
automatically as usual.

**Example with a free time:** the in-laws stay until Sunday 6 pm. 👥 Guest mode → Or until:
*Sunday, 18:00* → Apply.

**Example:** on Friday evening the babysitter comes. On the tablet: 👥 Guest mode → *until
tomorrow 10 am*. The parents leave – Hauswacht does not arm "Away", and at 11 pm not "Night"
either. On Saturday at 10 am the guest mode ends by itself, the automation applies again.

Switching on and off is in the logbook (event `GuestMode`) and is sent as a message via the event
"Automation".

## Arm by closing the door

In the profile, expandable under **"Arm by closing the door"**:

| Setting | Meaning |
|---|---|
| Arm as soon as the exit door is closed | on/off (default off) |
| Exit doors | e.g. front and back door |
| Settle time after closing | the door has to stay closed this long after closing (default 5 s, 1–60 s) |

Sequence: arm → exit delay runs → door open, out, door closed → after the settle time the system
is armed without waiting for the full exit delay. If the door opens again during the settle
time, it starts over.

- If the option is on, the **exit doors may be open when arming**. Other open sensors are checked
  as usual.
- If the exit doors are still open at the end of the exit delay, the normal check of the profile
  applies.

## Areas

**System settings → Areas.** For systems whose parts are armed **independently** – e.g. garage
armed while someone is in the house. Without further areas nothing changes.

- The **first area** (default name "House") is the main system. It can be renamed but not
  deleted; its entity IDs stay unchanged. Always-active sensors, homecoming observation,
  reminder "everyone away" and siren test belong to it.
- **Each alarm profile belongs to exactly one area.** The alarm panel buttons are free per area:
  house and garage may both have a button "Away".
- **Sensor groups and trigger rules** are building blocks for all areas. A sensor may appear in
  several areas; only the areas that are currently armed trigger.
- Each further area gets its own device **"Hauswacht &lt;name&gt;"** with alarm panel
  (`alarm_control_panel.hauswacht_garage`), profile selection and buttons.
- **"All areas"** (`alarm_control_panel.hauswacht_all_areas`): a button arms every area with the
  profile assigned to this button there; areas without such a profile stay as they are.
  "Disarm" disarms all areas (during an alarm: end alarm). If one area fails (e.g. window open),
  the others are switched anyway, and the message names what did not work. The most important
  state is shown: alarm > entry delay > exit delay > all disarmed > common armed state;
  differently armed areas show "Armed (custom)", details in the attribute `areas`.
- **User rights** apply either to all areas alike or per area, see
  [Users](users.md#rights).
- **Shared by all areas:** PIN lockout, test mode and sirens. Test mode can only be switched
  while all areas are disarmed; a siren used by two areas at the same time stays on until both
  have ended their alarm.
- **Notifications** carry the area name in the title, e.g. "Hauswacht: alarm (Garage)".
- An area can only be deleted when no alarm profile belongs to it any more. Its device and
  entities disappear with it.
