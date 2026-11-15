# Sensors and sensor groups

[Deutsch](../melder.md) | **English**

## Which sensors work?

Hauswacht only monitors entities that know **open/closed**:

| Kind | counts as open or triggered when |
|---|---|
| Binary sensor (`binary_sensor`) | on |
| Lock (`lock`) | unlocked, opening, open, jammed |
| Cover (`cover`, e.g. garage door) | open, opening, closing |

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

- **Select directly** in the field "Sensors".
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
| **Other** | everything else (vibration, shutter …) | Instant alarm, to be on the safe side |

Example: a window through which you enter the house gets the type **Door**. Hauswacht
deliberately does not suggest smoke detectors as "Technical" – fire protection stays the job of
the smoke detectors.

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
gaps.

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
