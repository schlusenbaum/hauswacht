# Documentation

[Deutsch](../README.md) | **English**

Hauswacht is an intrusion alarm system as an integration for Home Assistant. These pages explain
setup and operation – from installation to the keypad on the wall.

Everything you see in Home Assistant (dialogs, entities, cards, notifications) is available in
English and German and follows the language of Home Assistant. The terms on these pages are the
ones of the English interface.

## For users

| Page | Content |
|---|---|
| [How Hauswacht decides](how-hauswacht-decides.md) | **Overview first:** what happens when a door opens, when the automation switches, what happens when someone comes home, when someone counts as home or away – as pictures with examples |
| [Installation and first steps](installation.md) | requirements, installation via Marketplace or HACS, the settings page, the shortest way to the first arming, updates |
| [Setup wizard](setup-wizard.md) | the former wizard was removed in 0.63.2 – how to set up now, and what comes next |
| [Sensors and sensor groups](sensors.md) | which sensors work, sensor groups, types (door, window, motion …), always-active sensors, radio silence, radio networks and gateways |
| [Alarm profiles and areas](profiles.md) | creating profiles, delays, reaction, automation and presence, disarm on arrival, arm by closing the door, several areas (e.g. house and garage) |
| [Trigger rules](trigger-rules.md) | sequences like "door, then basement", exceptions, conditions, YAML expert mode |
| [Operation and dashboard](dashboard.md) | arming and disarming, ending an alarm, card "Hauswacht Alarm", example dashboard, profile settings |
| [Users, PINs and lockout](users.md) | users, rights per area, PIN rules, master PIN, lockout after wrong entries, duress PIN |
| [Passage](passage.md) | In or out without disarming: coming home at night, briefly taking out the bins – the profile stays armed |
| [Control devices](control-devices.md) | Zigbee keypads, learning RFID cards, NFC stickers, RFID readers, fingerprint readers, buttons, door locks (Nuki) |
| [Sirens](sirens.md) | which sirens work, release, tone per siren, siren from switch, siren test, reasons for a silent siren, fire protection |
| [Notifications and speech](notifications.md) | recipients per event, custom texts, announcements via speakers, push buttons |
| [Test mode and test card](test-mode.md) | play everything through safely: simulate sensors, no siren |
| [Observations](observations.md) | homecoming observation and "door open to disarmed" – measure before automating |
| [Settings page](settings-page.md) | page "Hauswacht" in the sidebar: the whole setup at a glance, matrix "sensor × profile" |
| [System overview](overview.md) | card with the whole configuration, printing, emergency sheet, check hints, diagnostics file |
| [Automations: what to use for what?](automations.md) | cheat sheet: the right trigger for every occasion (`phase`, event, entity) and the most common pitfalls |
| [Examples](examples.md) | connect Hauswacht to other devices: lights on alarm and back as before, camera image to the phone, shutters, status light, heating while away, guest mode from the calendar … |
| [Reference](reference.md) | look-up: all entities (German and English IDs), attributes of the alarm panel, all events with their fields, actions |
| [Troubleshooting](troubleshooting.md) | common questions and problems |

## For developers

| Page | Content |
|---|---|
| [Safety rules](development/safety.md) | binding rules for sirens and fire alarms |
| [Roadmap](roadmap.md) | what is done, what is coming |
| [Architecture](../entwicklung/architecture.md), [state model](../entwicklung/state-model.md), [tests](../entwicklung/testing.md), [ADRs](../entwicklung/adr/README.md) | German only for now |
| [Changes](../../CHANGELOG.md) | all versions (German) |

## Terms

| Term | Meaning |
|---|---|
| **Sensor** | an entity Hauswacht monitors: door and window contact, motion sensor, tamper contact, lock, garage door … |
| **Sensor group** | sensors that belong together and are armed together (e.g. "Outside", "Basement") |
| **Alarm profile** | a way of arming (e.g. "Night"): which sensor groups, which delays, which sirens |
| **Trigger rule** | alarm only on a sequence of sensors ("door, then basement") |
| **Area** | an independently armable part of the system (e.g. garage) |
| **Alarm panel** | the alarm entity in Home Assistant (`alarm_control_panel.hauswacht`) |
| **Control device** | a device for operating: keypad, NFC sticker, RFID reader, button, door lock |
| **Credential** | a user's PIN, RFID card or lock ID |
| **Bypassed** | a sensor is temporarily not monitored: after "Arm anyway" until disarming, after "End alarm" or a restart until it is closed |
