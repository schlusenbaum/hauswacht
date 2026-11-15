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
