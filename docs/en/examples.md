# Examples: connecting Hauswacht to other devices

[Deutsch](../beispiele.md) | **English**

Hauswacht itself only switches **sirens** and sends messages and announcements. Everything else –
lights, cameras, shutters, heating, door lock – is done by **your own automations** that react to
Hauswacht. This page collects ready-made examples to copy.

Which trigger to use for what is in the cheat sheet
[automations: what to use for what?](automations.md); every field in the [reference](reference.md).

How to use an example: Settings → Automations & scenes → **Create automation** → ⋮ → **Edit in
YAML** → paste the example → adjust entities, areas and services to yours → Save.

## The building blocks

| Building block | What for | Example |
|---|---|---|
| Panel attribute **`phase`** | The simplest trigger: `disarmed`, `arming` (exit delay), `armed`, `pending` (entry delay), `triggered` (**alarm running**), `alarm_hold` (alarm over, not yet acknowledged) | `to: triggered` |
| Attribute **`test_mode`** | Switch nothing real in test mode – add it as a condition **to every alarm automation** | `state: false` |
| Attributes **`profile_name`**, **`trigger_sensor`**, **`changed_by`** | Which profile is armed, which sensor triggered, who switched | in messages |
| Event **`hauswacht_event`** | Special occurrences, field `type`: e.g. `TamperDetected`, `SensorUnavailable`, `ButtonPressed`, `ActionCode` | see [reference](reference.md#events) |

> **Panel:** the examples use `alarm_control_panel.hauswacht`. With [areas](profiles.md#areas)
> every area has its own panel – then use the matching one. Every event names its area in the
> field `area` (e.g. `garage`).

## On alarm

### All lights on – and back to how they were afterwards

Before switching on, a scene remembers which lights were on and how. After disarming it restores
that.

```yaml
alias: Hauswacht – lights on alarm
triggers:
  - trigger: state
    entity_id: alarm_control_panel.hauswacht
    attribute: phase
    to: triggered
conditions:
  - condition: state
    entity_id: alarm_control_panel.hauswacht
    attribute: test_mode
    state: false
actions:
  - action: scene.create
    data:
      scene_id: before_alarm
      snapshot_entities:
        - light.hallway
        - light.living_room
        - light.garden
  - action: light.turn_on
    target:
      entity_id:
        - light.hallway
        - light.living_room
        - light.garden
    data:
      brightness_pct: 100
```

```yaml
alias: Hauswacht – lights as before after alarm
triggers:
  - trigger: state
    entity_id: alarm_control_panel.hauswacht
    attribute: phase
    from: [triggered, alarm_hold]
    to: disarmed
actions:
  - action: scene.turn_on
    target:
      entity_id: scene.before_alarm
```

*Tip:* instead of single lamps you can use `area_id: [hallway, living_room]` – but then list all
lamps of these rooms in `snapshot_entities` too.

### Camera: snapshot to the phone

The camera takes a picture, the phone shows it right in the notification – together with the
sensor that triggered.

```yaml
alias: Hauswacht – send camera image on alarm
triggers:
  - trigger: state
    entity_id: alarm_control_panel.hauswacht
    attribute: phase
    to: triggered
conditions:
  - condition: state
    entity_id: alarm_control_panel.hauswacht
    attribute: test_mode
    state: false
actions:
  - action: camera.snapshot
    target:
      entity_id: camera.driveway
    data:
      filename: /media/hauswacht/alarm.jpg
  - action: notify.mobile_app_annas_phone
    data:
      title: Burglary alarm
      message: >
        Triggered: {{ state_attr('alarm_control_panel.hauswacht', 'trigger_sensor') }}
        ({{ state_attr('alarm_control_panel.hauswacht', 'profile_name') }})
      data:
        image: /media/local/hauswacht/alarm.jpg
```

- `/media/hauswacht/…` is the folder, `/media/local/hauswacht/…` the same folder as seen by the
  app.
- If `camera.snapshot` reports "not allowed", add the folder in `configuration.yaml` under
  `homeassistant: allowlist_external_dirs:`.
- **Video instead of a picture:** `camera.record` with `filename: /media/hauswacht/alarm.mp4` and
  `duration: 30` – this takes 30 seconds, so make it the last action.
- Cameras that should only record while you are away are switched via the camera integration's
  recording switch – see [heating and camera while away](#heating-and-camera-while-away).

### Shutters up, music off

Raised shutters make the intruder visible from outside; loud music would drown out the siren.

```yaml
alias: Hauswacht – shutters up, music off on alarm
triggers:
  - trigger: state
    entity_id: alarm_control_panel.hauswacht
    attribute: phase
    to: triggered
conditions:
  - condition: state
    entity_id: alarm_control_panel.hauswacht
    attribute: test_mode
    state: false
actions:
  - action: cover.open_cover
    target:
      area_id: [living_room, kitchen]
  - action: media_player.media_stop
    target:
      entity_id: media_player.living_room
```

### Flashing light

Many lamps (e.g. Hue, Zigbee) can flash – more noticeable than a steady light.

```yaml
alias: Hauswacht – outdoor light flashes on alarm
triggers:
  - trigger: state
    entity_id: alarm_control_panel.hauswacht
    attribute: phase
    to: triggered
conditions:
  - condition: state
    entity_id: alarm_control_panel.hauswacht
    attribute: test_mode
    state: false
actions:
  - repeat:
      while:
        - condition: state
          entity_id: alarm_control_panel.hauswacht
          attribute: phase
          state: triggered
      sequence:
        - action: light.toggle
          target:
            entity_id: light.outdoor
        - delay: 1
  - action: light.turn_on
    target:
      entity_id: light.outdoor
```

The loop ends by itself as soon as the alarm is over; the light then stays on.

## Armed and disarmed

### Status light: red = armed, green = disarmed

A lamp or LED (e.g. a WLED strip in the hallway) shows the state.

```yaml
alias: Hauswacht – status light
triggers:
  - trigger: state
    entity_id: alarm_control_panel.hauswacht
    attribute: phase
actions:
  - choose:
      - conditions:
          - condition: state
            entity_id: alarm_control_panel.hauswacht
            attribute: phase
            state: [armed, arming, pending]
        sequence:
          - action: light.turn_on
            target:
              entity_id: light.status_hallway
            data:
              color_name: red
              brightness_pct: 30
      - conditions:
          - condition: state
            entity_id: alarm_control_panel.hauswacht
            attribute: phase
            state: [triggered, alarm_hold]
        sequence:
          - action: light.turn_on
            target:
              entity_id: light.status_hallway
            data:
              color_name: red
              brightness_pct: 100
              flash: long
    default:
      - action: light.turn_on
        target:
          entity_id: light.status_hallway
        data:
          color_name: green
          brightness_pct: 10
```

### Lock the front door when armed

See [reference – example: automation when armed](reference.md#example-automation-when-armed).
Better **not** couple unlocking to disarming.

### Heating and camera while away

With "Away" or "Holiday": heating to away, indoor cameras record. Back again after disarming.

```yaml
alias: Hauswacht – away
triggers:
  - trigger: state
    entity_id: alarm_control_panel.hauswacht
    attribute: phase
    to: armed
    id: armed
  - trigger: state
    entity_id: alarm_control_panel.hauswacht
    attribute: phase
    to: disarmed
    id: disarmed
actions:
  - choose:
      - conditions:
          - condition: trigger
            id: armed
          - condition: template
            value_template: >
              {{ state_attr('alarm_control_panel.hauswacht', 'profile_name')
                 in ['Away', 'Holiday'] }}
        sequence:
          - action: climate.set_preset_mode
            target:
              entity_id: climate.living_room
            data:
              preset_mode: away
          - action: switch.turn_on
            target:
              entity_id: switch.camera_living_room_recording
      - conditions:
          - condition: trigger
            id: disarmed
        sequence:
          - action: climate.set_preset_mode
            target:
              entity_id: climate.living_room
            data:
              preset_mode: home
          - action: switch.turn_off
            target:
              entity_id: switch.camera_living_room_recording
```

`switch.camera_living_room_recording` stands for the recording or motion detection switch of your
camera integration (e.g. Reolink, UniFi Protect) – adjust the name.

### Welcome light when coming home

Whoever comes home in the evening and disarms gets light in the hallway.

```yaml
alias: Hauswacht – welcome light
triggers:
  - trigger: state
    entity_id: alarm_control_panel.hauswacht
    attribute: phase
    from: pending
    to: disarmed
conditions:
  - condition: sun
    after: sunset
    before: sunrise
actions:
  - action: light.turn_on
    target:
      entity_id: light.hallway
```

`from: pending` means: disarmed during the entry delay – so really when coming home.

## Faults and tampering

### Tampering to the phone (even when disarmed)

Hauswacht reports tampering anyway; this automation additionally sends a critical notification
to a specific phone.

```yaml
alias: Hauswacht – report tampering as critical
triggers:
  - trigger: event
    event_type: hauswacht_event
    event_data:
      type: TamperDetected
actions:
  - action: notify.mobile_app_annas_phone
    data:
      title: Tampering
      message: >
        {{ state_attr(trigger.event.data.sensor_key, 'friendly_name')
           or trigger.event.data.sensor_key }} reports tampering.
      data:
        # iPhone: critical notification (breaks through "Do not disturb")
        push:
          sound:
            name: default
            critical: 1
            volume: 1.0
        # Android: deliver immediately
        ttl: 0
        priority: high
```

What exactly is in the event is shown by Developer tools → Events → `hauswacht_event` → "Start
listening".

### Several areas: tampering in the garage

With [areas](profiles.md#areas) every event names its area in `area` (ID) and `area_name`
(display name). Here tampering **only in the garage** goes to Peter's phone, and the garage light
goes on. Tampering in the house does not trigger this automation.

```yaml
alias: Hauswacht – tampering garage
triggers:
  - trigger: event
    event_type: hauswacht_event
    event_data:
      type: TamperDetected
      area: garage
conditions:
  - condition: state
    entity_id: alarm_control_panel.hauswacht_garage
    attribute: test_mode
    state: false
actions:
  - action: light.turn_on
    target:
      entity_id: light.garage
  - action: notify.mobile_app_peters_phone
    data:
      title: "Tampering – {{ trigger.event.data.area_name }}"
      message: >
        {{ state_attr(trigger.event.data.sensor_key, 'friendly_name')
           or trigger.event.data.sensor_key }} reports tampering.
```

- The ID (`garage`) is shown in the [reference](reference.md#events) or when listening to
  `hauswacht_event`; it stays the same even if you rename the area.
- `area: all` is used by events of the whole system (e.g. radio network faulty) and by control
  devices for all areas. Whoever means **all** areas simply leaves out `area`.
- The panel of the area is called e.g. `alarm_control_panel.hauswacht_garage` – if in doubt, check
  under Settings → Entities.

### System faulty: lamp orange

```yaml
alias: Hauswacht – show fault
triggers:
  - trigger: state
    entity_id: sensor.hauswacht_system_status
actions:
  - if:
      - condition: state
        entity_id: sensor.hauswacht_system_status
        state: ok
    then:
      - action: light.turn_off
        target:
          entity_id: light.fault
    else:
      - action: light.turn_on
        target:
          entity_id: light.fault
        data:
          color_name: orange
```

`ok` = everything fine, `degraded` = a sensor has failed, `fault` = radio network or gateway
faulty. (With German as Home Assistant language the entity is called
`sensor.hauswacht_systemstatus`.)

## Time control

For "armed at certain times" you need no automation of your own: the profile automation supports
fixed times and – for **different times per weekday** – a schedule helper, see
[different times per weekday](profiles.md#different-times-per-weekday-schedule). The safety rules
of the automation (guest mode, open windows, never during an alarm) then apply by themselves.

## Operating in other ways

### Guest mode from the calendar

If the calendar says "Guests", guest mode is on until the end of the event – no automatic arming,
no reminders.

```yaml
alias: Hauswacht – guest mode from calendar
triggers:
  - trigger: calendar
    event: start
    entity_id: calendar.family
conditions:
  - condition: template
    value_template: "{{ 'Guests' in trigger.calendar_event.summary }}"
actions:
  - action: hauswacht.guest_mode
    target:
      entity_id: alarm_control_panel.hauswacht
    data:
      "on": true
      until: "{{ trigger.calendar_event.end }}"
```

### A keypad code starts something

With an [action code](control-devices.md#action-codes) (e.g. 7777 + Home) you start any
automation – examples there: outdoor light, garage door, scene.

### A button switches something in addition

A [button](control-devices.md#button) reports every press as `ButtonPressed`:

```yaml
alias: Hauswacht – button also for the hallway light
triggers:
  - trigger: event
    event_type: hauswacht_event
    event_data:
      type: ButtonPressed
      control: Front door button
actions:
  - action: light.toggle
    target:
      entity_id: light.hallway
```

## Interconnecting smoke detectors

> **Only relevant if you use smoke detectors as alarm devices** – i.e. you also use the siren of
> your smoke detectors as a [siren for Hauswacht](sirens.md). Then the smoke detectors are part of
> your alarm system, and this section shows how fire and burglary alarms stay cleanly separated.
> If you have separate sirens and nothing to do with smoke detectors in Hauswacht, you can skip
> this section – interconnecting is then purely a Home Assistant topic.

Many wireless smoke detectors (e.g. via Zigbee) are **not** connected with each other: if there
is a fire in the living room, only the living room detector beeps – upstairs in the bedroom you
may not hear it. A small automation of your own then makes **all** detectors sound on smoke.

> **This is deliberately not a Hauswacht feature.** Fire protection must not depend on anything –
> not on test mode, not on the siren release, not on an update of the alarm system. An automation
> of your own with a few lines has none of these dependencies. Hauswacht stays out of it: if any
> smoke detector reports fire, Hauswacht switches no siren on and none off (see
> [fire protection](sirens.md#fire-protection)).

```yaml
alias: Smoke detectors – alert all detectors on smoke
mode: single
triggers:
  - trigger: state
    entity_id:
      - binary_sensor.smoke_detector_living_room_smoke
      - binary_sensor.smoke_detector_hallway_smoke
      - binary_sensor.smoke_detector_bedroom_smoke
    to: "on"
actions:
  - action: siren.turn_on
    continue_on_error: true
    target:
      entity_id:
        - siren.smoke_detector_living_room
        - siren.smoke_detector_hallway
        - siren.smoke_detector_bedroom
  - action: notify.mobile_app_annas_phone
    data:
      title: Fire!
      message: "{{ trigger.to_state.name }} reports smoke."
```

**Very important – check yourself before use:**

- **The right tone:** many smoke detector sirens have several tones (e.g. fire and burglary).
  Which ones exist is shown by Developer tools → States → the siren → attribute
  `available_tones`. Then enter the fire tone under `data:` with `tone:`.
- **The test button:** if the test button on the detector also sets the smoke sensor to "on", all
  detectors beep when testing. Then exclude the test button sensor with a condition or live with
  it.
- **Trial run:** try it once, announced to everyone in the house – with the test button or test
  spray, depending on the detector's manual.
- **`continue_on_error: true`** makes sure a failed detector does not stop the others.
- **No replacement for the detectors themselves:** every detector still beeps on its own. The
  interconnection via Home Assistant is only added on top – and only works as long as Home
  Assistant and the radio network are running.
- **Switching off** on a false alarm: e.g. a script with `siren.turn_off` on all detectors. With
  real smoke the affected detector simply triggers again. This script is **only** for fire alarms
  – you end a burglary alarm via Hauswacht.

## What you better not automate

- **Do not unlock automatically** when disarming – whoever disarms by mistake would also have
  opened the door.
- **Do not mix smoke detector and fire functions** with burglary automations.
- **Always add the test mode condition** to alarm automations – otherwise the trial run switches
  on lights and starts camera recordings.
- **No siren automations of your own:** sirens belong in Hauswacht (locks, test mode, fire
  priority) – see [sirens](sirens.md).
