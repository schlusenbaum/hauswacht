# Observations

[Deutsch](../beobachtung.md) | **English**

Hauswacht can measure before you automate. Observations **switch nothing** – they deliver
numbers for your own decisions. The [radio silence observation](sensors.md#radio-silence-observation-the-right-value-from-your-data)
is described with the sensors.

## Homecoming observation

**Settings page → System → Presence and homecoming observation → Edit.** Choose persons and switch on "Observe
homecoming".

Hauswacht then records when an **entry door** (sensors with the role "entry") is opened and when
a person is detected as **home** – for the person as a whole and for each of their location
sources individually (e.g. router, app, iCloud). From this, Hauswacht calculates how an automatic
homecoming would work for you.

> The observation **switches nothing**: no disarming, no alarm, no notification. A test makes sure
> that this part of the code cannot call any actions.

Every homecoming after at least 5 minutes of absence is evaluated:

| Value | Meaning |
|---|---|
| with door | an entry door was opened within 5 minutes |
| without door | no door opening – usually a false report of the location |
| delay | seconds between door opening and detected homecoming (negative = detected before) |
| false alarms at X s | how often the homecoming would only have been detected after an entry delay of X seconds |

- **Sensor "Homecoming observation"**: number of evaluated homecomings; the numbers per source are
  in the attribute `sources`, the last ten homecomings in the attribute `recent`, the times "door
  open to disarmed" in the attribute `entry_times`.
- **Button "Homecoming report"**: creates an overview as a notification in Home Assistant.
- **View, save, reset:** on the settings page, see
  [Measurements on the settings page](#measurements-on-the-settings-page).
- **Download:** also in the card ["Hauswacht Übersicht"](overview.md) → section **Monitoring** →
  - **Report** – the same report as a Markdown file, plus the last homecomings;
  - **Table (CSV)** – every single homecoming and every entry as one row: time, person and
    source, door, seconds after opening, how long the person was away, result. The file opens
    directly in Excel, Numbers or LibreOffice (comma-separated with an English Home Assistant).
- Only points in time are stored, for at most 60 days.

After two to four weeks the report shows whether a homecoming automation would be reliable for
you, for which persons and location sources, and with which entry delay.

### Measurements on the settings page

Everything the homecoming observation measures is also shown on the
[settings page](settings-page.md) → **System** → card **Presence and homecoming observation** →
block **Measurements**:

- **Since when:** "Homecoming measured since 2026-11-07 (15 days, 84 door openings) · leaving
  measured since 2026-11-21 (1 day)".
- **Table per person:**

  | Person | Came home (with door) | Left through a door | longest time until "away" | Silent pauses (longest) |
  |---|---|---|---|---|
  | Christian | 23 (21) | 4 | 95 s | 2 (6 min) |

  Each column heading has an **ⓘ** (hover over it); below, **"What do the columns mean?"**
  expands all explanations – on the phone too. A **silent pause** is an "away" without a door
  before it, see [What is a silent pause?](#what-is-a-silent-pause).
  Homecoming counts the **earliest signal** per person, leaving counts **all signals** together
  – both as the profile automation counts (see [Leaving](#leaving-preparation-for-detect-leaving-without-pin)).
- **Recommendation per person** for "detect leaving without PIN": ✅ reliable with waiting time,
  ⚠️ warning with a tip, or grey "not enough data yet".
- **Entries:** per door, how often the entry delay ran, the longest time until disarmed and the
  recommended entry delay (see [Door open to disarmed](#door-open-to-disarmed)).

Below it the buttons:

| Button | What happens |
|---|---|
| **Show report** | shows the whole report directly on the page (press again: hide) |
| **Save report** | downloads the report as a Markdown file |
| **Save table (CSV)** | downloads every single measurement as a table |
| **Reset homecoming** | starts only the "homecoming" measurement again (homecomings, door openings, recommendation "Disarm with door proof"); leaving and entries are kept |
| **Reset leaving** | deletes only the "leaving" measurement and starts it again; homecoming and entries are kept |
| **Reset all measurements** | deletes homecoming, entries and leaving and starts again |

Resetting asks first, changes **no setting** and switches nothing. Useful e.g. after setting up
new signals (Companion app), so that old values do not distort the recommendation. Tip: **save
the table** first if you want to keep the old values. Only administrators see the reset buttons.

## Additional signals per person

In the side sheet "Presence and homecoming observation" you choose additional signals per person. The earlier and more
reliable a signal, the better.

The signals **also apply to the profile automation** ("Arm when all of these persons are away",
"On return"). The second step therefore also shows the persons from the automation of the
profiles, even if the observation is off. How the automation combines the signals is described
under [Profiles → How Hauswacht knows who is home](profiles.md#how-hauswacht-knows-who-is-home).

| Signal | From where | counts as "home" |
|---|---|---|
| Wi-Fi sensor | companion app: Android "Wi-Fi connection" (`sensor.<phone>_wifi_connection`, enable under Settings → Companion app → Manage sensors), iPhone "SSID" (`sensor.<phone>_ssid`, location "Always" + "Precise location") | connected to one of the **home Wi-Fi networks** (field in the first step, comma-separated) |
| Bluetooth | e.g. Bermuda with the BLE transmitter of the Android app | `device_tracker` = home |
| Router | e.g. FRITZ!Box Tools (no app needed, but slow) | `device_tracker` = home |
| Approach | integration **"Proximity"** (Settings → Devices & services → Add integration → Proximity; zone Home, persons): sensor `sensor.<proximity>_<person>_direction_of_travel` | towards or arrived; window 15 min instead of 5 min, because the approach often comes minutes before the door |
| Approach (Places) | add-on integration **Places** (HACS): sensor `sensor.places_<person>_direction_of_travel` | "towards home" = home, "away from home" = away, "stationary" does not count (from 0.60) |
| Binary sensor | any | on |

In addition, Hauswacht evaluates the **"earliest signal"** per person: the moment the person counts
as home again – **exactly as the profile automation decides**: person, ping, Wi-Fi, Bluetooth …
and the direction (Proximity, Places) only with **"arrived"**. **"Towards" does not count** –
otherwise every drive in the area that briefly heads towards home would count as coming home. So
the recommendation for "Disarm with door proof" (below) shows what the automation really needs
(from 0.60). How early the approach comes is still shown in the direction sensor's own line. The
observation also includes the person's device trackers individually.

### Recommendation for "Disarm with door proof"

As soon as there are homecomings **with door**, the report contains a section **"Disarm with door
proof – entry delay needed per person"**. Example:

```
- Christian: at least 60 s (latest detection after opening: 48 s; 30 homecomings with
  door, 2 without door – those would be ignored)
- Niklas: at least 5 s (latest detection after opening: 0 s; 22 homecomings with door,
  23 without door – those would be ignored)
```

How to read it:

- **at least … s:** with this entry delay, "With door proof" would have disarmed in time for
  every observed homecoming (latest delay plus 25 % buffer, at least 5 s). You set the entry
  delay itself in the profile – you need enough time anyway for unlocking without a phone.
- **without door:** phantom homecomings. "With door proof" ignores them.
- You also find the value in the attribute `door_proof` of the sensor "Homecoming observation".

## Door open to disarmed

While an entry delay runs, Hauswacht measures how long it takes until disarming (or whether it
was too late). Per door: number, in time, too late, typical and longest time and a
**recommendation for the entry delay** (longest time plus 25 %, at least 5 s, rounded up to 5 s).
Helpful e.g. to check the place for a control device on the wall.

If you are let in by [passage](passage.md) (e.g. by phone), the system stays armed and nobody has
to disarm. Such an entry appears in the CSV table as "let in by passage", but counts **neither as
in time nor as too late** (from 0.60).

## Leaving (preparation for "detect leaving without PIN")

From 0.60 on, the homecoming observation also measures **leaving**. This is the measurement for a
later feature ([ADR 0014](../entwicklung/adr/0014-ausgangserkennung.md), German): whoever forgets to enter the
PIN while a profile is armed and walks out of the front door should not trigger an alarm –
because their phone reports "away" shortly after. For that, Hauswacht has to know **how fast**
your phones report "away" and **how often they are simply silent**. This measurement also
**switches nothing**.

One simple principle applies: **Nobody can leave without a door opening.**

| Value | Meaning |
|---|---|
| left through a door | a source reports "away", and an entry door opened up to 15 minutes before |
| typical / longest until "away" | time from "door open" to "away" |
| silent pause | "away" without a door opening before: usually a sleeping phone – see [What is a silent pause?](#what-is-a-silent-pause) |
| longest pause | how long the longest silent pause lasted |

The most important line is **"all signals"** per person: it reports "away" only when no signal of
the person says "home" any more (silent signals count as away) **and** there is proof – door and
then a location outside, or a fresh, precise location outside (from 0.61, exactly like the
automation, see ["away" only with proof](profiles.md#away-only-with-proof)). It reports "back" as
soon as one reports "home" again. A sleeping phone therefore no longer shows up in this line as
leaving and homecoming. The lines of the individual signals keep measuring without proof – there
you see how often a signal alone reports "away".

**Direction sensors** (Proximity integration, Places) count here as in the profile automation only
with **"arrived"** (home) and **"away from"** (away). "Towards" and "stationary" are skipped – so
someone on the way back outside does not count as "back", and a walk does not count as leaving
twice. They also appear as a line of their own in the table.

### What is a silent pause?

A **silent pause** is an "away" **without a door before it**: all signals of a person report
"away", but **no entry door** opened in the 15 minutes before (or at most 1 minute after). The
number in brackets on the settings page is the longest such pause in minutes – that is how long
the person counted as "away" until a signal reported "home" again.

Since nobody can leave without a door, a silent pause is usually a **sleeping phone**. But there
are three typical causes – the table (CSV) or the person's history in Home Assistant helps to
look it up:

| Cause | How to recognise it | What helps |
|---|---|---|
| **Phone asleep** – Wi-Fi off, ping gets no answer, the person is home | The person was home during that time, often at night | a signal that does not sleep (Wi-Fi sensor of the Companion app), or location "Always" |
| **Signal too slow** – the person really left, but their last signal only reported "away" after more than 15 minutes | A door opened shortly before the pause, just more than 15 minutes before | a faster signal; with iCloud3, add the Companion app as "Mobile App" (otherwise iCloud3 only notices leaving the zone at its next poll) |
| **Door without a contact** – out through the garage, basement or patio | No door in the history, but the person was out | add the door with a contact as an entry door |

**Example:** Finja goes through the front door at 17:07. Her iPhone only reports the location
"Town" at 17:22:52 – 15½ minutes later. Hauswacht finds no door in the 15 minutes before and
counts a silent pause, although she really left (cause "signal too slow").

Why it matters: for the later [exit detection](#leaving-preparation-for-detect-leaving-without-pin)
Hauswacht waits silently after a door opening for the phone to report "away". If a phone happens
to fall asleep exactly then, a burglary would look like "leaving". That is why Hauswacht warns
when silent pauses are longer than the waiting time.

**After a reset** (from 0.61): an "away" without a door in the first 15 minutes after resetting
all measurements (or starting the observation) does **not** count as a silent pause. The door may
have opened shortly before the reset – Hauswacht does not know, so it leaves this "away" out.

### Recommendation per person

The report ends with **"Detect leaving without PIN – recommendation per person"**. The same
sentences are shown on the settings page in the card **Presence and homecoming observation**, and
the recommendation or warning also appears as a [check hint](overview.md#check-hints) (tab
**Overview**). Example:

```
- Christian: leaving is detected reliably – recommended waiting time 3 min (from 12× leaving).
- Niklas: all signals were silent 9× for longer than 4 min without a door opening. Leaving
  could not be told apart from a break-in reliably. Tip: set up a second signal, e.g. the
  Companion app with its Wi-Fi sensor.
- Finja: not enough data yet (1× leaving) – the recommendation comes after at least
  3× leaving and 2 days.
```

How to read it:

- **recommended waiting time:** longest measured time from "door open" to "away" plus a buffer
  (25 %, at least 1 minute), rounded up to whole minutes, between 1 and 15 minutes. Later,
  Hauswacht would wait silently this long before raising the alarm.
- **reliable:** the person left through a door at least 3 times, leaving has been measured for at
  least 2 days (counted from installing 0.60, not from the start of the homecoming observation;
  attribute `departure_days`), and there was **no** silent pause longer than the waiting time.
- **Warning "silent":** all signals of the person were already quiet for longer than the waiting
  time without a door opening. If such a pause fell into the waiting time after a break-in,
  Hauswacht would take it for "leaving". Remedy: an additional signal that does not sleep – best
  the Wi-Fi sensor of the Companion app. A plain ping to an iPhone is usually not enough, because
  sleeping iPhones do not answer.
- **Warning "too late":** the signals notice leaving only after more than 15 minutes. Remedy: a
  faster signal (Wi-Fi sensor or Bluetooth).
- **Silent pauses of several persons at the same time** (within one minute) look like a Wi-Fi or
  router outage. They do not count for the recommendation, because the later feature catches
  such a case separately. They still appear in the report.

Persons with a warning will **not be excluded** later – the warning only shows that detection
would be uncertain for them.

The values are also in the attributes `departure` (per source), `leaving_advice` (per person) and
`departure_days` (days since the measurement started)
of the sensor "Homecoming observation", and every single measurement as a "Leaving" row in the
**table (CSV)**.

> Good to know: if a silent pause happens to fall into the 15 minutes after a door opening
> (someone else goes out), it counts as "left through a door" with a long time. If a
> recommendation looks too high, have a look at the CSV table.

### Signs of life around the door

*From 0.63.1 – measurement only, switches nothing.*

For the later exit detection it is not enough to know how fast "away" comes. Two more questions
decide whether it protects you at all. So at **every door opening** the observation records, per
person, when their signals last reported "home" and when they did so again afterwards. A **sign
of life** is any "home" report of one of the person's signals, even if the value does not change
(e.g. ping answering again at every poll). The person entity itself and direction sensors do not
count.

**a) Sign of life before leaving.** Exit detection will only work for people whose phone
reported "home" shortly before the door opened (up to 3 minutes). If the phone is usually already
asleep when the person leaves, exit detection will rarely help them.

> *Example:* "Niklas: when leaving, 2 of 9× with a sign of life shortly before." – His iPhone is
> usually already asleep when he leaves. Exit detection would rarely recognise him.

**b) "Still here" after the door.** Someone with a sign of life stays home while a door opens
(e.g. a burglar – or someone else goes out). How fast does one of their signals report "home"
again? On a break-in, exit detection will raise the alarm as soon as everyone who was home has
reported again. **A break-in would stay silent for at most this long.**

> *Example:* "Christian: stays home while a door opens – reports again typically after 20 s, at
> the latest after 45 s." – A break-in would stay silent for at most 45 s.
>
> "Finja: … reports again typically after 60 s, but 3 of 12× not at all for 15 minutes." – In
> those cases the alarm would only come at the end of the waiting time.

The cross-check: **"home" after leaving.** Do the signals of someone who is just leaving still
report "home" for a while after the door opened? This happens with ping, for example: the ping
integration only reports a phone as "away" after a grace period (usually 3 minutes). Exit
detection has to classify such reports correctly later – the measurement shows how long they last.

**Where you see this:**

- Settings page → System → Presence → **Measurements**: table **"Preparing exit detection"**
  with ⓘ at every column and the sentences per person (only from 3 measurements).
- In the report, the section **"Preparing exit detection"**.
- Attribute `exit_checks` of the sensor "Homecoming observation".

| Column | Meaning |
|---|---|
| Sign of life before leaving | with sign of life / all times left through a door |
| "still here" after the door | typical / longest time until the next "home" when the person stayed |
| no "still here" | how often nothing came for 15 minutes / all times |
| "home" after leaving | how often and for how long "home" still came after the door opened |

A door opening only counts **15 minutes later** – before that, it is still open whether someone
left. "Reset leaving" also clears this measurement.
