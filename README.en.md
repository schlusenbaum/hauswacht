<img src="docs/images/hauswacht-icon.svg" alt="Hauswacht" width="96" align="right">

# Hauswacht

[Deutsch](README.md) | **English**

[![Release](https://img.shields.io/github/v/release/schlusenbaum/hauswacht?include_prereleases&sort=semver)](https://github.com/schlusenbaum/hauswacht/releases)
[![Downloads](https://img.shields.io/github/downloads/schlusenbaum/hauswacht/total?label=Downloads)](https://github.com/schlusenbaum/hauswacht/releases)
[![Marketplace](https://img.shields.io/badge/Marketplace-Custom-41BDF5.svg)](https://www.home-assistant.io/integrations/marketplace/)
[![CI](https://github.com/schlusenbaum/hauswacht/actions/workflows/ci.yml/badge.svg)](https://github.com/schlusenbaum/hauswacht/actions/workflows/ci.yml)

**Intrusion alarm system for Home Assistant** ("Hauswacht" means "house watch") – freely
definable alarm profiles, trigger rules like "door, then basement", users with PIN and RFID card,
Zigbee keypads, sirens with a fire lock, and a test mode in which no siren can go off. And because
Hauswacht provides everything it knows as entities, attributes and events, you connect it with
**everything Home Assistant can do** – lights, cameras, shutters, heating, speakers.

> **Status: 0.57.0b13 – beta.** In use in my own home; feedback is very welcome. Real siren control
> is **locked** after installation and has to be enabled deliberately.

Everything you see in Home Assistant – setup dialogs, entities, cards, notifications, push
buttons, announcements and reports – is available in **English and German** and follows the
language of Home Assistant. The [documentation](docs/en/README.md) is available in English too.

<p align="center">
  <img src="https://raw.githubusercontent.com/schlusenbaum/hauswacht/main/docs/images/alarm-karte.png" alt="Card Hauswacht Alarm: disarmed, arming, PIN entry, alarm" width="800">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/schlusenbaum/hauswacht/main/docs/images/test-karte.png" alt="Card Hauswacht Test" width="420">
  <img src="https://raw.githubusercontent.com/schlusenbaum/hauswacht/main/docs/images/einstellungen-karte.png" alt="Card Hauswacht Einstellungen (settings)" width="380">
</p>

(The screenshots show the German interface.)

## What Hauswacht can do

- **Setup wizard** – guides you through the setup without prior knowledge: short introduction,
  sensor suggestions by room, sensor groups, profiles, recipients, sirens, users and a trial run
  in test mode; every step can be skipped.
- **Alarm profiles instead of fixed modes** – "Home", "Night", "Vacation" … as many as you like,
  each with its own sensor groups, delays, sirens and recipients. Automatic arming by time or when
  everyone has left – with presence from several signals per person (Wi-Fi, Bluetooth, router,
  proximity …) – and disarm on arrival with door proof. Different times per weekday via a
  schedule; **guest mode** so visitors are not locked out.
- **Tilted windows and vibration** – window sensors and handles with three positions (closed,
  tilted, open): tilted allowed at night, opening fully triggers; when away, tilted counts as
  open. Vibration sensors with false alarm protection ("2 knocks in 60 seconds"), also as a number.
- **Trigger rules** – alarm only on a sequence ("door, then basement within 2 minutes"), with
  exceptions and conditions; in a wizard or as YAML.
- **Alarm card without forced PIN** – a large card for the tablet: state with countdown, one
  button per profile, open sensors with "Arm anyway". Whoever is logged in switches with their own
  rights; it only asks for a PIN where configured – e.g. on the wall tablet in the hallway.
- **Areas** – house and garage armed independently, with their own alarm panel and "All areas".
- **Users and credentials** – PIN and any number of RFID cards per person, rights per area,
  guests with validity, duress PIN with silent emergency call, lockout against guessing.
- **Control devices** – Zigbee keypads via Zigbee2MQTT with feedback on the device, learning
  cards directly at the keypad, NFC stickers with the Home Assistant app, RFID readers, buttons
  (arm only) and door locks (e.g. Nuki: disarm when a known user unlocks). **Action codes** at
  the keypad (e.g. 7777 + Home) start your own automations or a silent emergency call.
- **Notifications** – per event with their own recipients and texts, critical alerts break
  through Do Not Disturb, buttons "Disarm" and "Arm anyway" in the push message, announcements
  via speakers (e.g. Echo).
- **Sirens with common sense** – controlled only according to their capabilities, never during a
  fire, a fire tone only as an expert release and never on smoke detectors; tone per siren (e.g.
  Homematic IP alarm siren), sirens on a switch via a wizard; siren test individually, briefly and
  quietly.
- **Honest about faults** – failed sensors, radio silence and outages of Zigbee2MQTT or MQTT are
  made visible instead of hidden.
- **Test mode and test card** – play everything through safely, without siren, without other
  automations noticing.
- **Settings page** in the sidebar – everything at a glance, with a matrix "sensor ×
  profile", edit everything right there, with a "?" to the matching place in the docs; in addition to
  the dialog (pre-release).
- **System overview** – the whole configuration at a glance, printable, with an emergency sheet
  for the family and check hints that find gaps and forgotten items.
- **Observe instead of guess** – homecoming and radio silence observation deliver numbers before
  you automate anything.

## Open to everything: Hauswacht as a building block

Hauswacht itself only switches sirens and sends messages – but it **provides everything an alarm
system knows**, so that you can connect whatever you like with your own automations:

| Hauswacht provides | For example |
|---|---|
| **Alarm panel** per area with state and attributes: `phase` (disarmed, arming, armed, entry delay, **alarm**, alarm over), active profile, triggering sensor, who switched, test mode, guest mode | "On alarm: lights on" |
| **Events** `hauswacht_event` for almost everything, each with its area: armed, disarmed, alarm, tampering, sensor failed, wrong PIN, button, action code, time automation … | "On tampering: critical push message" |
| **Entities**: open sensors, system status, test and guest mode, buttons, profile settings, action code event | "Status light red while armed" |
| **Actions** and **buttons**: arm with profile (also "arm anyway"), disarm, end alarm, guest mode, siren test, simulate sensors in test mode | "Guest mode from the calendar" |

This makes Hauswacht the core of much an alarm system should do: on alarm **lights on** and back
as before afterwards, **camera image to the phone**, **shutters up**, music off, **heating down**
while away, welcome light when coming home, lock the front door when arming – each with a
ready-made template in the **[examples](docs/en/examples.md)**. Which trigger to use for what is
shown by the cheat sheet **[automations](docs/en/automations.md)**; all entities, attributes and
events with their fields are in the **[reference](docs/en/reference.md)**. In test mode this stays silent thanks to the
attribute `test_mode`.

## Quick start

1. **Add the repository** and download Hauswacht, then restart Home Assistant:
   - **Marketplace** (from Home Assistant 2026.11): [open directly](https://my.home-assistant.io/redirect/marketplace_repository/?owner=schlusenbaum&repository=hauswacht&category=integration) or Settings →
     Marketplace → *Add from link* → `https://github.com/schlusenbaum/hauswacht`
   - **HACS** (up to 2026.10): HACS → ⋮ → **Custom repositories** →
     `https://github.com/schlusenbaum/hauswacht`, type **Integration**

   Hauswacht is not (yet) in the catalogue (inclusion requested), hence the detour via the link –
   [step by step](docs/en/installation.md#installation).
2. Set up Hauswacht:

   [![Set up Hauswacht](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=hauswacht)

3. **With the setup wizard** (offered during setup): choose sensors, accept sensor groups and
   profiles, enter your phone as recipient. Alternatively everything by hand under Configure.
4. Put the card **"Hauswacht Test"** on a dashboard, test mode on, play it through.
5. Test mode off – done. Enable sirens only once everything works.

In detail: [Installation and first steps](docs/en/installation.md).

## Documentation

| | |
|---|---|
| [Installation and first steps](docs/en/installation.md) | installation, menu, the first five steps |
| [Setup wizard](docs/en/setup-wizard.md) | guided setup, every step can be skipped, trial run |
| [Sensors and sensor groups](docs/en/sensors.md) | which sensors, types, always active, radio silence |
| [Alarm profiles and areas](docs/en/profiles.md) | profiles, automation, presence, disarm on arrival, arm by closing the door, areas |
| [Trigger rules](docs/en/trigger-rules.md) | sequences, exceptions, conditions, YAML |
| [Operation and dashboard](docs/en/dashboard.md) | arm/disarm, alarm card, ending an alarm, cards |
| [Users, PINs and lockout](docs/en/users.md) | users, rights, PIN rules, duress PIN |
| [Control devices](docs/en/control-devices.md) | keypads, learning cards, NFC, RFID readers, fingerprint, buttons, door locks |
| [Sirens](docs/en/sirens.md) | compatibility, release, tone per siren, siren from switch, siren test, "why didn't it sound?", fire protection |
| [Notifications](docs/en/notifications.md) | events, custom texts, speech |
| [System overview](docs/en/overview.md) | overview, printing, emergency sheet, check hints |
| [Automations: what to use for what?](docs/en/automations.md) | cheat sheet: the right trigger for every occasion |
| [Examples](docs/en/examples.md) | connect other devices: lights, camera, shutters, status light, heating … |
| [Test mode](docs/en/test-mode.md) · [Observations](docs/en/observations.md) · [Reference](docs/en/reference.md) · [Troubleshooting](docs/en/troubleshooting.md) | |

Everything at a glance: [docs/en/](docs/en/README.md).

## Requirements

- Home Assistant **2026.10** or newer
- Sensors with open/closed (door, window, motion sensors …) – independent of the manufacturer
- Optional: sirens (`siren`, or switches via a wizard), Home Assistant app, Zigbee2MQTT for keypads
- No cloud, no other integrations needed

## Safety

- **Fire alarm always has priority:** as long as a smoke detector reports fire or its state is
  unclear, Hauswacht switches no siren on and none off.
- **Test mode locks sirens technically**, not just in the display. The siren release is off after
  installation.
- **After a restart as before** – armed stays armed (configurable: always armed or always
  disarmed); by default a previous alarm is not continued (configurable), otherwise sirens never go on because of it – and its own
  sirens that were still sounding at the restart are switched off afterwards.
- **Hauswacht switches no devices** except sirens (including switches added as sirens) and the
  display of configured keypads – a test makes sure of this. Hauswacht only reads door locks, it
  never operates them.
- **PINs not in plain text in the history:** Hauswacht automatically disables the entity in which
  Zigbee2MQTT puts the code typed at the keypad.

The binding rules: [Safety rules](docs/en/development/safety.md).

> **Note:** Hauswacht is a hobby project and **not a certified security system** (no VdS or EN
> 50131 certification). It replaces neither a professional intrusion alarm system nor tested smoke
> detectors.

**Limits, honestly:**

- Hauswacht only works **while Home Assistant is running** – without power, network or radio
  there is no alarm. A UPS for Home Assistant, router and radio gateway makes sense; sirens with
  their own battery keep sounding once they are running.
- **No monitoring centre:** Hauswacht notifies you and your recipients – it does not call a
  security service by itself (possible with your own automations, e.g. telephony services).
- Hauswacht detects **radio jamming** only indirectly – via radio silence and failed sensors.

## How Hauswacht came about

Hauswacht was built with **a lot of help from AI**: large parts of the code, the tests and the
documentation were written by **Claude** (Anthropic). The ideas, concepts, safety rules and
decisions are mine.

It is tested in two ways: **in my own home with real hardware** – door and window contacts,
motion and presence sensors, a Zigbee keypad and sirens – and additionally with **automated
tests** that every change has to pass before it is merged. The automated tests also play through
cases you would not want to try at home, such as an alarm while a smoke detector reports fire.

Other homes have other devices – that is why feedback from other installations is especially
valuable.

## Contributing

Bugs and wishes are welcome as an [issue](https://github.com/schlusenbaum/hauswacht/issues), in
English or German – feedback on further siren and keypad models is especially welcome. If you want
to work on the code: [safety rules](docs/en/development/safety.md); architecture and
[tests](docs/entwicklung/testing.md) are documented in German for now.

## Support

If you like Hauswacht, I'd be happy about a coffee:

[![Buy me a coffee](https://img.buymeacoffee.com/button-api/?text=Buy%20me%20a%20coffee&emoji=&slug=schlusenbaum&button_colour=FFDD00&font_colour=000000&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff)](https://www.buymeacoffee.com/schlusenbaum)

## License

[MIT](LICENSE)
