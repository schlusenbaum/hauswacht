# Alarm profiles and areas

[Deutsch](../profile.md) | **English**

## Alarm profiles

**Settings page → Profiles → Add alarm profile.** There are no predefined profiles – you add as many as
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
| Unavailable sensors when arming | refuse · allow after confirmation · bypass automatically (**experts**). An unavailable sensor (e.g. empty battery) is **monitored again as soon as it reports** – until then it is a gap. "Bypass automatically" arms without asking; the [note on arming](notifications.md#note-on-arming) names it |
| Maximum alarm cycles | How often the alarm may trigger again after an alarm |
| Tamper triggers alarm | Otherwise tampering is only reported |
| Tilted windows allowed | Only with [sensors with tilt position](sensors.md#sensors-with-tilt-position-tilted) (hidden otherwise): a tilted window counts as closed, only opening it fully triggers. **Off** (default): tilted counts as open. Typical: on for "Night", off for "Away" |
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

Safety rules:

- Automatic arming only while the system is disarmed – never on top of another profile.
- Open or failed sensors are **never** confirmed automatically (unless the profile bypasses them
  automatically anyway). If arming fails because of this,
  you get a system message.
- A **running alarm** is never ended automatically. A running entry delay only via
  [On return](#on-return) ("Disarm with door proof", "Disarm, also after arming by hand" or "Let in").
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
3. In the profile under **Automation → Or by schedule (helper)** choose the schedule.

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
**signals** per person – under **Settings page → System → Presence and homecoming observation**,
in the person's box. The [homecoming observation](observations.md#additional-signals-per-person) uses
the same signals; you set them in one place only.

Suitable are e.g. the Wi-Fi sensor of the companion app, Bluetooth (Bermuda), a router tracker,
the direction from the Proximity integration (or Places) or any binary sensor (on = home) – such as a
HomeKit variable "Martin home".

| The person counts as … | when … |
|---|---|
| **home** | any signal reports home (the person itself or one of the signals) |
| **away** | **all** signals reliably report "away" **and** there is proof (from 0.61, see [below](#away-only-with-proof)) |
| unknown | otherwise, e.g. a signal is "unavailable" or the proof is missing – this **never** counts as away |

**Direction (Proximity, Places)** counts with two values only: **"arrived"** = home and
**"away from"** = away. **"Towards"** and **"stationary"** are skipped (from 0.60): someone
approaching is not there yet – otherwise a drive in the area that briefly heads towards home
would already count as a return and e.g. trigger "On return". And "stationary" (e.g. at
the office) does not hold up "all away".

**Example:** Anna is "away" according to her person entity, but her Wi-Fi sensor still reports
the home Wi-Fi. Then Anna is home, and "Arm when all of these persons are away" waits. Only when
the Wi-Fi is gone too does the delay start.

This way a signal that drops out briefly does not arm right away, and the fastest signal
detects the arrival.

#### "Away" only with proof

*From 0.61.* A sleeping phone must not make anybody away. If a phone in the house loses its Wi-Fi
at night, all signals may report "away" – yet the person is there. So someone only counts as
**away** when there is also **proof** that the person is outside:

1. **Door and location:** an entry door opened, and afterwards – at most the time window later
   (default 15 minutes) – the phone was located **outside** the zone "Home". How precise the
   location is does not matter here: the door is the second proof.
2. **Fresh location alone:** the phone is located **outside** right now, the location is
   **fresh** (reported in the last 15 minutes) and **precise enough**. This helps when the door
   opening is missing – e.g. Home Assistant was restarting or it was the patio door without a
   contact.

Anything with coordinates counts as a **location**: the Companion app (GPS), iCloud3, a GPS
tracker, the person itself while located by GPS. **Wi-Fi, ping, router and Bluetooth** have no
coordinates – they only confirm, they are never proof.

**Precise enough** – set under settings page → System → Presence and homecoming observation:

| Setting | "outside" means | Example |
|---|---|---|
| **check precisely** (default, recommended) | further away than the radius of the zone "Home" **plus** the reported inaccuracy | phone in the basement, GPS reports 250 m off with ±300 m inaccuracy → does **not** count |
| **simple** | outside the zone, no matter how inaccurate | the same phone → counts as outside |

**Examples:**

- *Christian drives to work:* front door opens, a minute later the Companion app reports the
  location at the street corner, shortly after the Wi-Fi is gone → **away** (door and location).
- *Niklas's phone sleeps in bed:* at 2 am the Wi-Fi drops, the app has not reported a new
  location for hours → **not away** (no proof). "Arm when all away" does not arm. And since he
  was never "away", there can be no false "homecoming" in the morning either.
- *Home Assistant restarts while Petra is out:* no door opening known, but her phone reports a
  fresh, precise location in town → **away** (fresh location).

Once someone is proven away, that stays so until the person is home again – even if the location
falls asleep afterwards. Doors and locations from before the last homecoming do not count.

**Persons without a location – "also door + signal (uncertain)":** if a person has no location
(e.g. only a Wi-Fi sensor or ping), you can choose **"Proof for 'away': also door + signal
(uncertain)"** for them under settings page → System → Presence and homecoming observation, in
the person's box. Then this also counts as proof: an entry door opened, and **afterwards** – at most
the **time window door + signal** later (default 5 minutes, under "More settings", with a
recommendation from the measurement) – a signal of the person changed from "there" to "away".

| What happens (time window 5 minutes) | Result for Niklas (Wi-Fi only, "uncertain") |
|---|---|
| Front door opens, 2 minutes later his Wi-Fi is gone | **away** |
| At night his Wi-Fi drops, no door | not away – sleeping phone |
| Petra goes out at 7 am, exactly in the 5 minutes after that Niklas's phone falls asleep | **wrongly away** – this is the residual risk |

> **Why "uncertain"?** Hauswacht does not know **who** opened the door. If the phone happens to
> fall asleep shortly after someone else opened the door, the person counts as away. If everyone
> is away then, "arm when all away" arms although the person is home – when they get up, there is
> a false alarm. It does not make a burglary easier. Hence: a warning at the setting, a check hint
> and a short time window. A location stays better (location in the Companion app on "Always").

**Persons without a location and without "door + signal"** (e.g. location switched off in the
Companion app, only a router tracker) **never** count as away. "Arm when all away" waits forever with such a person in the
list – that is the safe side. Hauswacht shows this at the person selection in the profile
("⚠ no location – never counts as away"), under System → Presence and as a
[check hint](overview.md#check-hints). Fix: set the location in the Companion app to
**"Always"** or add a GPS tracker as a signal.

The same applies to the [homecoming observation](observations.md): it counts "away" the same
way, so that measurement and automation match.

### On return

*New in 0.61. Set only on the [settings page](settings-page.md) → Profiles → profile → section
**"On return"**. If something does not fit (e.g. "disarm with door proof" without an entry
door), the [assistant](setup-wizard.md#hints-while-editing-since-0640b2) shows it while you edit.*

Here you decide what happens when a certain person comes home. It is based on the person state in
Home Assistant (usually the phone) plus the person's [signals](#how-hauswacht-knows-who-is-home).
"Coming home" always means: the person was reliably away before and is home now.

| Setting | Effect | Default |
|---|---|---|
| When someone comes home | One of the five levels below | **Nothing** |
| For these persons | Who triggers "On return". Its own list – independent of "Arm when all of these persons are away". Without a person, any level other than "Nothing" cannot be saved | none |
| Time window phone and door (under "More settings") | Only for "Disarm with door proof" and "Let in": how far apart the phone report and the door opening may be. 1–30 minutes. Does **not** delay the alarm, see [What the time window means](#what-the-time-window-means) | 5 minutes |
| Entry delay after approach, approach is valid for (under "More settings") | Only for "Disarm with door proof" and "Let in": more time for the phone if the person approached before – see [approach](#approach-extends-the-entry-delay) | off, 15 minutes |

Next to each field there is an **ⓘ**: hovering shows the explanation, tapping (phone, tablet)
expands it. Below the selection, one sentence says **"This is how it behaves:"** – it changes
right away with the level and the time window.

| Level | What happens | What protects against a wrong location | Good for |
|---|---|---|---|
| **Nothing** | Hauswacht does nothing. Disarm only by PIN, card, keypad or app | – | Vacation |
| **Disarm, only if armed automatically** | One of the persons comes home → disarmed. Only if Hauswacht armed the profile **itself** (e.g. "everyone away") and no door has opened yet | coupling to the automation: armed by hand stays armed | like "As before" up to 0.60 |
| **Disarm with door proof** | One of the persons comes home **and** an entry door opens – both within the time window, in any order. Also during the entry delay, no matter how it was armed | two proofs: location **and** door | "Away" – the **recommendation** for most homes |
| **Disarm, also after arming by hand** | One of the persons comes home (away for at least 5 minutes before) → disarmed at once, no matter how it was armed. No door needed | only the location – hence the warning in the form | if you want convenience and know the risk |
| **Let in (passage)** | An entry door opens and a person's phone reports "home" up to the time window before or while the entry delay is running (away for at least 5 minutes before) → Hauswacht lets them in **without PIN, the profile stays armed** | location **and** door; the rest of the house stays armed | "Night": the others sleep, the system stays on. Details at [let in by phone](passage.md#let-in-by-phone) |

**Example "Night" with let in:** Christian and Petra are asleep, the system is on "Night". Niklas
comes home at 1 am. His phone reports "home" in the driveway, a minute later he unlocks the front
door → no alarm, no PIN, "Night" stays armed. A stranger at the same door gets the normal entry
delay and then the alarm.

**Example "Away" with door proof:** everyone is away, Hauswacht armed automatically. Petra comes
back from shopping, her phone reports "home", she opens the front door → disarmed at once.

> **Why is "Disarm, also after arming by hand" not the recommendation?** Here the phone alone is
> enough. Whoever has a person's phone – or a found phone – comes home and the system is off.
> With "Disarm with door proof" a door has to open as well, and only then does the homecoming
> count.

**After the update to 0.61** Hauswacht takes over your previous settings: "Disarm on arrival"
(As before / With door proof) with the persons from "Arm when all away", and letting in by phone
from the passage. If **both** were on in a profile, **let in** wins – the profile then stays
armed, the safe side – and you get a notification in Home Assistant.

**"Disarm with door proof" in everyday life**

- *The location comes too late:* Christian opens the front door, the entry delay runs. 20
  seconds later his phone reports "home" → Hauswacht disarms before the alarm comes.
- *The location comes early:* the phone already reports "home" at the street corner. Nothing
  happens yet. Two minutes later the front door opens → disarmed at once.
- *Phantom homecoming:* Niklas's phone reports "home" at night although he is out. Without an
  opened door, **nothing** happens.
- *Burglary:* someone opens the door, but nobody has come home → normal entry delay and alarm.

#### Approach extends the entry delay

*From 0.61, only for "Disarm with door proof" and "Let in" – under "More settings".*

Some phones only report "home" once the door is already open – sometimes after 60 or 70 seconds.
With a 30 s entry delay that would mean an alarm. Extending the entry delay for **everyone**
would also give a burglar more time. So Hauswacht uses the **direction** (Proximity integration
or Places, added as a signal of the person under System → Presence):

> If a person from the "On return" list approached in the last **15 minutes** (direction
> "towards") and an entry door then opens, Hauswacht waits **longer** for their phone – e.g. 90 s
> instead of 30 s. Whoever did not approach still only has the normal time.

| Setting | Effect | Default |
|---|---|---|
| Entry delay after approach | seconds in total; 0 = off. Only has an effect when longer than the profile's normal entry delay – it never shortens | 0 (off) |
| Approach is valid for | minutes after "towards" | 15 |

Both fields show a **recommendation from the homecoming observation** with an **"apply"**
button (the persons need to be in the observation for this):

- Extension: longest measured time from "door open" to "home" plus buffer – the same value as the
  [recommendation for "Disarm with door proof"](observations.md#recommendation-for-disarm-with-door-proof).
- Validity: longest time from "towards" to the door plus 5 minutes.

**Example:** entry delay 30 s, after approach 90 s. Christian drives home, Proximity reports
"towards" at 18:02. At 18:06 he opens the front door, his iPhone only reports "home" after 70 s →
disarmed, no alarm. A burglar at 3 am, before whom nobody approached → alarm after 30 s as always.

- The direction **never disarms by itself** and never lets anyone in – it only gives the phone
  more time.
- A door with an instant alarm stays an instant alarm.
- The push message for the entry delay states the extended time; the event `EntryDelayExtended`
  names who approached.

> **Residual risk:** if someone breaks in exactly while a person from the list approaches, they
> have the longer time. That is a narrow, rare window.

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


### Guest mode

Guests, a babysitter or tradesmen are in the house but have no tracking – to Hauswacht the house
looks empty. So that the automation does not arm then, there is the **guest mode**.

**While it is on,** Hauswacht does **not arm** the area **automatically**: neither by time nor
"when everyone is away" nor "always armed after restart". The reminder "nobody home, not armed"
is not sent. Arming **by hand** (keypad, card, tablet, Alexa) still works; "On return"
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

**Settings page → System → Areas.** For systems whose parts are armed **independently** – e.g. garage
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
