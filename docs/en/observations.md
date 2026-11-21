# Observations

[Deutsch](../beobachtung.md) | **English**

Hauswacht can measure before you automate. Observations **switch nothing** – they deliver
numbers for your own decisions. The [radio silence observation](sensors.md#radio-silence-observation-the-right-value-from-your-data)
is described with the sensors.

## Homecoming observation

**System settings → Presence and homecoming observation.** Choose persons and switch on "Observe
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
- **Download:** card ["Hauswacht Übersicht"](overview.md) → section **Monitoring** →
  - **Report** – the same report as a Markdown file, plus the last homecomings;
  - **Table (CSV)** – every single homecoming and every entry as one row: time, person and
    source, door, seconds after opening, how long the person was away, result. The file opens
    directly in Excel, Numbers or LibreOffice (comma-separated with an English Home Assistant).
- Only points in time are stored, for at most 60 days.

After two to four weeks the report shows whether a homecoming automation would be reliable for
you, for which persons and location sources, and with which entry delay.

## Additional signals per person

In the second step of the form you choose additional signals per person. The earlier and more
reliable a signal, the better.

The signals **also apply to the profile automation** ("Arm when all of these persons are away",
"Disarm on arrival"). The second step therefore also shows the persons from the automation of the
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

In addition, Hauswacht evaluates the **"earliest signal"** per person: home as soon as any source
reports home. The profile automation decides the same way. (The observation also includes the
person's device trackers individually; the automation uses the person itself and the chosen
signals.)

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
| silent pause | "away" without a door opening before: the phone is asleep, the Wi-Fi hiccups – the person is actually at home |
| longest pause | how long the longest silent pause lasted |

The most important line is **"earliest signal"** per person: it reports "away" only when **all**
signals of the person say "away". This is exactly how the later feature is meant to decide.

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
