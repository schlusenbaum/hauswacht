# Sensors and sensor groups

[Deutsch](../melder.md) | **English**

## Which sensors work?

Hauswacht only monitors entities that know **open/closed**:

| Kind | counts as open or triggered when |
|---|---|
| Binary sensor (`binary_sensor`) | on |
| Lock (`lock`) | unlocked, opening, open, jammed |
| Cover (`cover`, e.g. garage door) | open, opening, closing |
| [Sensor with tilt position](#sensors-with-tilt-position-tilted) (sensor with a text state, attribute or select helper) | open – tilted depending on the profile |
| [Vibration strength](#vibration-strength-as-a-number) (number sensor or number helper) | value at or above the configured threshold |

Everything else becomes a binary sensor via a **helper** in Home Assistant:

- **Measured values** (temperature, humidity, power …): with the wizard
  [Create a sensor from another sensor](#create-a-sensor-from-another-sensor).
- **Cameras:** most camera integrations already provide motion, person or vehicle as binary
  sensors – use those directly.
- **Events** (e.g. a doorbell, `event.…`): a template binary sensor that is "on" for a moment:

```yaml
template:
  - trigger:
      - trigger: state
        entity_id: event.doorbell
        not_from: unavailable
    binary_sensor:
      - name: Doorbell pressed
        state: "on"
        auto_off: "00:00:05"
```

## Sensor groups

**Alarm triggering → Sensor groups → Add sensor group.**

A **sensor group** combines sensors that are always armed together. Profiles arm whole sensor
groups, not single sensors. Typical:

| Sensor group | Sensors | armed in the profiles |
|---|---|---|
| Outside | all door and window contacts, their tamper contacts | Home, Night, Away |
| Inside / Basement | motion and presence sensors | Night (basement), Away |

- Hauswacht only monitors sensors that are in a sensor group (or under
  [Always active](#always-active-sensors)).
- **Each sensor belongs to exactly one sensor group.** If it is already in another one, the
  group cannot be saved; the message names the sensor and the group.
- Which sensors a group finally contains is shown in the attribute `zones` of the alarm panel.

Sensors get into a group in two ways, which can be combined:

- **Select directly** in the field "Sensors". [Sensors with tilt position](#sensors-with-tilt-position-tilted)
  and [vibration strengths](#vibration-strength-as-a-number) have their own field below ("Special
  sensors" – it appears as soon as there are any).
- **By label:** all sensors that carry this label **directly on the entity** belong to the
  group automatically. Labels on the device deliberately do not count – otherwise battery or
  connectivity sensors of the same device would be included.

The monitored sensors are fixed when arming. If a label is removed while armed, the sensor stays
monitored until disarming.

## Types

The **type** decides *how* a sensor reacts; *when* it is armed is decided by the sensor group and
the alarm profile. After saving a sensor group, Hauswacht shows all its sensors with the
suggested type – usually it fits, otherwise change it right there.

| Type | Suggested for | Behaviour |
|---|---|---|
| **Door** | door, garage door, opening, lock, gate | Starts the entry delay; can be an exit door for [arming by closing the door](profiles.md#arm-by-closing-the-door) |
| **Window** | window | Instant alarm |
| **Motion** | motion, occupancy, presence | Waits if an entry delay is running, otherwise instant alarm |
| **Tamper** | tamper | Always reported, even when disarmed; alarm depending on the profile |
| **Technical** | moisture, gas, cold, heat, carbon monoxide | Always active, never part of arming, no intrusion alarm – notification only (see below) |
| **Vibration** | vibration, [vibration strength](#vibration-strength-as-a-number) | Instant alarm – with adjustable [false alarm protection](#vibration-sensors); never blocks arming |
| **Other** | everything else (shutter …) | Instant alarm, to be on the safe side |

Example: a window through which you enter the house gets the type **Door**. Hauswacht
deliberately does not suggest smoke detectors as "Technical" – fire protection stays the job of
the smoke detectors.

## Sensors with tilt position (tilted)

Many window sensors report not only open or closed but **three positions**: **closed**,
**tilted** and **open** – e.g. sensors in the window rebate (such as Senoro.Win via Zigbee2MQTT)
or window handles (such as Homematic IP). Hauswacht can handle all three. The big advantage: in
every alarm profile you decide whether a **tilted window is allowed**.

> **Example:** at night the bedroom window is tilted – in the profile "Night" that is allowed,
> the system can be armed. If someone opens the window **fully**, there is an alarm. In the
> profile "Away" the same tilted window counts as open – you are told about it when leaving.

### Setting up

**Alarm triggering → Special sensors → Add sensor with tilt position.**

1. **Choose the source.** Where the position comes from differs per device:

   | Device provides … | Example | How to enter it |
   |---|---|---|
   | a sensor with a text state | `sensor.bedroom_window_opening_state` = `open` / `tilted` / `closed` | just choose the entity |
   | an attribute on an entity | `binary_sensor.bathroom_window_handle`, attribute `window_state` = `OPEN` / `TILTED` / `CLOSED` | choose the entity, enter the attribute `window_state` |
   | nothing – you want to try it first | "Dropdown" (select) helper "Test window" with *open*, *tilted*, *closed* | choose the helper |

   Which values and attributes a device has is shown by Developer tools → States.
2. **Assign values.** Hauswacht shows the known values and suggests the assignment
   (`closed`/`zu`/`geschlossen` → closed, `tilted`/`gekippt` → tilted). Check, add values if
   needed (missing values can be typed in), save.
3. **Add it to a sensor group** – directly in the second step or later under sensor groups (own
   field "Sensors with tilt position"). The type is automatically **window** and can be changed
   like for every sensor.
4. **Decide in the profiles** where tilted is allowed: setting **"Tilted windows allowed"** (see
   [alarm profiles](profiles.md#alarm-profiles)). Default is **off**.

### How Hauswacht judges the positions

| Change | Profile with "tilted allowed" | Profile without (default) |
|---|---|---|
| closed → tilted | nothing | trigger (like opening) |
| tilted → open | **trigger** | nothing – was already "open" |
| open → tilted | nothing | nothing |
| tilted or open → closed | nothing | nothing |
| arming while tilted | allowed | like an open window (refuse, "arm anyway" …) |

**Safety rules:**

- **Unknown values count as open**, never as closed – also values the device only reports later
  (e.g. "gap ventilation"). Whoever wants to treat such a value as tilted adds it to the
  assignment.
- **Failure is detected** like for every sensor: if the sensor is unavailable or the attribute is
  missing, it counts as failed (radio silence check, event `SensorUnavailable`, setting "Failed
  sensors when arming"). A home-made template helper would usually report a failure as "closed".
- **"Arm anyway" with a tilted window:** the window is bypassed – but only in the tilted
  position. If it is then **opened fully**, it triggers. Only once it was closed does the bypass
  end as for every sensor.
- In **trigger rules** a sensor with tilt position counts as soon as it is open in the active
  profile: with "tilted allowed" only when fully opened, otherwise already when tilted.

### Where you see the position

- **Panel:** attribute `tilted_sensors` (currently tilted). If the profile allows tilted
  windows, they are **not** in `open_sensors`.
- **Messages:** "Not armed: Bedroom: window (tilted)".
- **Events:** events with `sensor_key` additionally have `position` for these sensors (`open`,
  `tilted`, `closed`), see [reference](reference.md#events).
- **Test card:** shows "tilted" and has its own button **Tilted** for simulating in test mode.
- **System overview:** state "tilted".

**Edit and remove** under Alarm triggering → Special sensors. Removing also takes the sensor out
of all sensor groups; nothing changes on the device.

> **Vibration at the window:** many of these sensors also report vibration (prying, glass
> breakage) as a number – this becomes a [vibration sensor](#vibration-sensors). Together both
> are strong: at night the window is tilted and allowed – whoever pries at it triggers via the
> vibration **before** the window is open.

## Vibration sensors

Vibration sensors (e.g. Aqara or Tuya via Zigbee2MQTT, device class "vibration") report knocks on
windows and doors – i.e. prying or a smashed pane. Hauswacht gives them their own type
**vibration**:

- **Instant alarm** in the armed profile (no entry delay).
- **Never blocks arming.** Vibration is an event, not an open state – a sensor that is still
  "on" for a minute after a knock does not prevent arming. A **failed** vibration sensor, on the
  other hand, counts like every failed sensor.
- **Texts** say "… (vibration)".
- **Disarmed** nothing happens. Whoever wants to be informed then too adds the sensor under
  [always active](#always-active-sensors).

### False alarm protection: how many vibrations until the alarm?

Vibration sensors are sensitive: a slammed door, a passing truck, a thunderstorm or a ball
against the pane can trigger them. That is why Hauswacht asks when saving a sensor group with
vibration sensors:

**"Alarm at N reports of one sensor within S seconds"**

| Setting | Effect |
|---|---|
| **1 report** (default) | Every vibration triggers immediately – the most sensitive |
| **2 reports in 60 s** (recommendation) | A single knock does not trigger. Someone prying or smashing a pane almost always causes several knocks in quick succession. Price: a single, very strong blow alone does not trigger |
| 3 – 5 reports | Only for very restless spots (e.g. door to the street) |

- Counting is **per sensor**: a thunderstorm that shakes every window once does not cause an
  alarm.
- Every report that is not yet enough appears as the event `VibrationCounted` (with `count`,
  `needed`, `window`) – handy for checking the setting.
- **Mind the hold time:** many vibration sensors stay "on" for a while after a report (often
  60–90 seconds) and report no second one during that time. For "2 in 60 seconds" the hold time
  must be clearly shorter – with Zigbee2MQTT it is often adjustable as a device option (e.g. 5–10
  seconds).
- To change: edit the sensor group → save → the question comes again after the types.

### Vibration strength as a number

Some sensors don't report an "on/off" vibration but a **strength as a number** (e.g.
`sensor.bathroom_window_vibration` of a window sensor). This becomes a sensor without helpers:

**Alarm triggering → Special sensors → Add vibration strength.**

1. Choose the sensor (to try it without hardware: **Number** helper, `input_number`).
2. Enter the **threshold**: from this value on it counts as a vibration. Best watch the value
   under Developer tools → States and knock lightly on the window – choose the threshold a bit
   above the idle value and below a strong knock.
3. Optionally add it to a sensor group right away. The type is automatically **vibration**.

**Every report at or above the threshold counts** – even if the number stays the same (Home
Assistant also reports unchanged values). If the value is not a number or the sensor is
unavailable, the sensor counts as failed.

**Combining with trigger rules:** "vibration, then window open within one minute" works as a
[trigger rule](trigger-rules.md) – e.g. if single vibrations should not be enough, but the
combination should.

## Create a sensor from another sensor

**Alarm triggering → Create a sensor from another sensor.** Example frost guard:

| Field | Example |
|---|---|
| Measurement | `sensor.temperature_boiler_room` |
| Name of the new sensor | Frost boiler room |
| Lower limit | 5 (triggers below 5 °C) |
| Upper limit | empty |
| Hysteresis | 1 (back to "normal" only from 6 °C – no constant back and forth) |
| Type | Technical |
| Use in | Always active (or a sensor group) |

Hauswacht creates a **threshold helper** with this (`binary_sensor.frost_boiler_room`, can be
changed and deleted under Settings → Devices & services → Helpers) and adds it with its type
right away. Only a new helper is created – existing helpers, automations or scripts stay
unchanged.

## Always-active sensors

**Alarm triggering → Always active.** Sensors that report **even while disarmed** – e.g. a safe,
gun cabinet, garden shed, panic button. Sensor groups and/or single sensors.

| State | Reaction |
|---|---|
| disarmed (default) | **critical notification** (breaks through Do Not Disturb) and a message in Home Assistant – no alarm, no siren |
| disarmed with "Use sirens" | alarm with the sirens, tone and duration chosen here; display "Alarm" (profile "Always active"). "End alarm" returns to disarmed |
| armed | instant alarm with the reaction of the active profile |

Sensors of type **Technical** in a sensor group are always active automatically. Even when armed
they trigger **no intrusion alarm**, only the notification (or, with "Use sirens", the alarm
"Always active"). They do not block arming.

Hardware enabling, test mode and fire lock apply as always. In the test card these sensors are
marked "always active".

## Sensor radio silence

**System settings → Sensor radio silence.**

- A sensor is **unavailable** if it is missing or reports `unavailable` or `unknown`.
- Optionally it also counts as **failed** if it has not reported for this many hours (default:
  off). Battery sensors sometimes report only every few hours – choose generously.
- "Last contact" is the "last seen" sensor of the same device (for Zigbee2MQTT
  `sensor.<device>_last_seen`), if it exists and is enabled. Otherwise the last update in Home
  Assistant – which is renewed at every restart, though. The attribute `last_contact` shows the
  value per sensor.
- If a monitored sensor fails while armed, you get "Hauswacht: sensor lost" and the event
  `SensorUnavailable`.
- What happens with failed sensors when arming is decided by the alarm profile (refuse or allow
  after confirmation).

### Radio silence observation: the right value from your data

Hauswacht remembers for each sensor the **longest gap between two signs of life** (checked every
minute, stored across restarts; gaps across a restart do not count). The form then shows, for
example:

> Observed for 14 days. Longest gap: front door contact 1 h 52 min. **Recommendation: 3 h.**

The recommendation is the longest gap × 1.5, rounded up to full hours – at the earliest after 3
days of observation. You enter the value yourself; the observation changes nothing. The
diagnostic sensor `sensor.hauswacht_radio_silence_observation` shows the recommendation and the
gaps – also the **recommendation per sensor** (`recommended_hours`).

### Own limit per sensor

If a single sensor reports much less often than the others – e.g. a battery door contact that
only transmits on changes – it would pull the general value up for everyone. A failed motion
sensor would then only be noticed after many hours. Better: give this sensor an **own value**.

| Setting | Effect |
|---|---|
| **As general** | The general value applies (default) |
| **Own value** | Own hours (1–168) for exactly this sensor |
| **Never check** | For sensors that only report on changes. They never count as failed because of silence; "unavailable" is still detected |

- **Settings page:** tab sensors → click the sensor → **radio silence**. It shows the observation
  for exactly this sensor and the button **"use recommendation"**. In the tab system, the card
  "sensor radio silence" shows all sensors with longest gap, recommendation and own value (⚠️ if
  the own value is below the recommendation). In the sensor table an own value appears as
  "⏱ 24 h" or "⏱ never check" after the name.
- **Dialog:** system settings → sensor radio silence → below, choose "set an own value for a
  sensor".
- Sensors with an own value no longer count for the **general recommendation**. Example: the back
  door stays silent for up to 16 hours, all others at most 2 hours. With an own value for the back
  door (24 h), the observation recommends 3 h in general instead of 24 h.
- If an own value is below the recommendation for this sensor, the
  [system overview](overview.md#check-hints) reports it as a check hint.

## Monitor radio networks and gateways

**System settings → Monitor radio networks and gateways.** Binary sensors that report whether a
radio network or gateway is running. If such a system fails, none of the sensors behind it can
report anything.

- For Zigbee2MQTT: `binary_sensor.zigbee2mqtt_bridge_connection_state`. If MQTT fails, it also
  becomes "unavailable" – so it covers both.
- Device class "problem": "on" = fault. All others (e.g. "connectivity"): "on" = OK.
- If an indicator is off or unavailable, the system status shows **Fault**. Arming is then
  handled like with failed sensors.
- If a system fails while armed, you get "Hauswacht: fault"; the system stays armed.
- If the sensors come back closed after an outage, there is no alarm. If a sensor comes back
  **open**, it triggers – a missed opening is caught up this way.
