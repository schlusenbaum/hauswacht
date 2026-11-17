# Roadmap

[Deutsch](../roadmap.md) | **English**

## Achieved

| Version | Content |
|---|---|
| 0.1–0.5 | state machine and siren guard as pure logic, integration framework, sensors and profiles, test mode and simulation, monitoring of radio networks and gateways, notifications, sirens (release off by default) |
| 0.6–0.9 | example dashboard, protection against PIN guessing, freely definable profiles, automation (time, presence) |
| 0.10–0.15 | homecoming observation, push button "Disarm", end alarm (profile stays armed), profile settings as entities, card "Hauswacht Einstellungen" |
| 0.16–0.18 | users with their own PIN, duress PIN, notifications per event, test card |
| 0.19–0.21 | trigger rules (wizard and YAML, exceptions, conditions), always-active sensors, arm by closing the door |
| 0.22 | areas with their own alarm panel and "All areas" |
| 0.23 | speech via speakers, custom texts with placeholders |
| 0.25 | only sensors with open/closed, sensor types, exclusions in the profile, wizard "Create a sensor from another sensor" |
| 0.26 | siren test (individually, brief, quiet, with confirmation) – successfully tried with real sirens |
| 0.27 | radio silence observation, additional homecoming signals, "door open to disarmed" |
| 0.28 | control devices: Zigbee2MQTT keypads with feedback, NFC stickers, RFID readers, emergency key |
| 0.29 | user rights per area |
| 0.30–0.32 | RFID cards independent of the PIN, learning via keypad (only disarmed, learning time), random IDs detected, reset failed attempts, failed attempts expire after 24 h |
| 0.33 | tidied-up documentation, screenshots, issue templates |
| 0.34 | system overview (card, print, emergency sheet), check hints with repairs, diagnostics file |
| 0.35 | card "Hauswacht Alarm" without forced PIN (account as credential, PIN per account configurable) |
| 0.36 | homecoming report for download (Markdown and CSV) |
| 0.37 | visual editor for all cards; alarm card customisable (profiles, size, displays, colours, confirmations) |
| 0.38–0.39 | notifications, push buttons, reports and placeholders in English (follow the language of Home Assistant) |
| 0.40–0.41 | tone per siren (e.g. HmIP-ASIR), wizard "Create siren from switch", switches as sirens and fire tone release for experts |
| 0.42 | additional presence signals per person for the profile automation, "Disarm on arrival" with door proof, entry delay recommendation from the homecoming observation |
| 0.43 | button as control device (arms only), door lock as control device (Nuki via MQTT or generic: disarm when a known user unlocks, optionally arm when locking) |
| 0.44 | documentation in English (user guide and safety rules), English README |
| 0.45 | configurable behaviour after restart: restore the previous state (default), always armed, always disarmed |
| 0.46 | sirens that were on before a restart are switched off afterwards (not during a fire) |
| 0.47 | names for RFID cards, fingers and lock IDs ("key ring") – in messages, logbook and system overview |
| 0.48 | separate dialogs "Cards" and "PINs" with an overview of who has what, disable cards, "last used", learn a new card at the keypad without waiting; the keypad's code entity is disabled automatically (it showed the entered code in plain text) |
| 0.49 | action codes: code + key at the keypad starts your own automations (event entity), arms sensor groups or triggers a silent emergency; pick the keypad as a device instead of typing the MQTT topic |
| 0.50 | force arm at the keypad: with open sensors, confirm again within 10 s (right per user) |
| 0.51 | guest mode (switch, service, alarm card; until a time or until switched off) – no profile automation and no reminders; resume a running alarm after a restart (setting, default off); "alarm before the restart" as an important alarm message |
| 0.52 | system overview shows guest mode, action codes and the right "Force arm"; new check hints (silent emergency without recipient, action code with deleted profile/keypad, guest mode on); emergency sheet explains "arm anyway" at the keypad |

Details for every version: [CHANGELOG](../../CHANGELOG.md) (German).

## Planned

| When | Content |
|---|---|
| soon | choose the HmIP-ASIR tone automatically per occasion (burglary, fire, test) – being looked into |
| later | developer documentation (architecture, tests, ADRs) in English; English screenshots |
| later | ZHA and Z-Wave keypads |
| 1.0.0 | stable, documentation complete, inclusion in the HACS default list |
| some day | cameras: picture in the message, camera detection as its own sensor type – to be designed afresh |
| 1.x | dedicated kind "fingerprint reader" (names per finger, minimum match) – already possible today via RFID reader or Nuki Keypad 2.0; further automation conditions, recurring guest mode times (e.g. every Tuesday 8–12) |

## Principles

- **Hauswacht switches no devices** – except sirens (after release; for experts also switches
  added as sirens) and the state displays of configured keypads.
- **Fire alarm has priority**, test mode locks sirens technically. By default an alarm is not
  continued after a restart; if you want that, switch on "Resume a running alarm" – even then
  sirens only go on through all siren locks.
- **Action codes never disarm** and never count as a failed attempt.
- **PIN optional**, voice assistants only with PIN. Exposure to Alexa & co. via the normal entity
  exposure of Home Assistant.
- Larger building blocks first get a concept, then are implemented. Decisions with their reasons
  are in the [ADRs](../entwicklung/adr/README.md) (German).

## Important decisions

- **Areas:** freely named, one state machine per area; alarm profiles belong to an area, sensor
  groups and rules are shared building blocks
  ([ADR 0007](../entwicklung/adr/0007-bereiche.md), German).
- **Trigger rules** instead of zone confirmation: combined with OR, cannot cancel each other out
  ([ADR 0006](../entwicklung/adr/0006-regeln.md), German).
- **Names:** in German, "zones" are called "Meldergruppen" (sensor groups) and "rules"
  "Auslöseregeln" (trigger rules); internal keys (`zones`, `rules`) stay.
- **Credentials:** PIN and RFID card belong to the user, stickers and readers to the control
  devices ([ADR 0005](../entwicklung/adr/0005-ausweise.md), German).

## Versioning and releases

- Semantic Versioning. 0.x: interfaces may change. From 1.0.0, breaking changes only in major
  versions, always with migration of the settings.
- `main` is always green; changes via pull requests.
- Releases as Git tag + GitHub release; HACS reads the releases.
