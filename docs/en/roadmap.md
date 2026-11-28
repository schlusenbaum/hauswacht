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
| 0.48 | separate dialogs "Cards" and "PINs" with an overview of who has what, disable cards, "last used", learn a new card at the keypad without waiting; the keypad's code entity is disabled (it showed the entered code in plain text; since 0.58.3 only after you confirm a repair) |
| 0.49 | action codes: code + key at the keypad starts your own automations (event entity), arms sensor groups or triggers a silent emergency; pick the keypad as a device instead of typing the MQTT topic |
| 0.50 | force arm at the keypad: with open sensors, confirm again within 10 s (right per user) |
| 0.51 | guest mode (switch, service, alarm card; until a time or until switched off) – no profile automation and no reminders; resume a running alarm after a restart (setting, default off); "alarm before the restart" as an important alarm message |
| 0.52 | system overview shows guest mode, action codes and the right "Force arm"; new check hints (silent emergency without recipient, action code with deleted profile/keypad, guest mode on); emergency sheet explains "arm anyway" at the keypad |
| 0.53 | [setup wizard](setup-wizard.md): short introduction, sensor suggestions by floor and room, sensor groups or trigger rules, profiles, recipients with test message, sirens (without release), users, trial run in test mode, further areas, chapter selection – every step can be skipped; settings rules in the core ([ADR 0009](../entwicklung/adr/0009-einrichtungsassistent.md), German) |
| 0.54 | profile automation by schedule helper: different times per weekday without a second profile; docs page [examples](examples.md) for your own automations (lights, camera, shutters …) |
| 0.55 | Every event names its area (`area`, `area_name`); complete [reference](reference.md) and cheat sheet [automations](automations.md); ready for the Marketplace/HACS catalogue |
| 0.56 | [Tilted windows](sensors.md#sensors-with-tilt-position-tilted) allowed per profile or counted as open; [vibration sensors](sensors.md#vibration-sensors) with false alarm protection, also as a number ([ADR 0010](../entwicklung/adr/0010-fenster-kippstellung-erschuetterung.md)) |
| 0.57 | [Settings page](settings-page.md) in the sidebar: everything at a glance, matrix "sensor × profile", edit everything directly (sensors, profiles, trigger rules as form or YAML, sirens with tone, notifications, people, cards, control devices, PIN rules, action codes, system), tab documentation and "?" at every section; [radio silence per sensor](sensors.md#own-limit-per-sensor); "behaviour after restart" only on a real restart ([ADR 0011](../entwicklung/adr/0011-einstellungsseite.md)) |
| 0.58 | [Generic keypads](../entwicklung/adr/0012-keypads-allgemein.md): one input for every keypad (Z-Wave, ESPHome, Node-RED …) with response and display entity, blueprint Ring Keypad v2 and ESPHome example, [MQTT interface](control-devices.md#mqtt-interface); wrong-PIN warnings tidy themselves up |
| 0.59 | [Passage](passage.md) – in or out without disarming ([ADR 0013](../entwicklung/adr/0013-durchgang.md)): at the keypad with any profile key, push button "Let in", automatically by phone, door lock, NFC tags, card readers |
| 0.60 | Observation [leaving](observations.md#leaving-preparation-for-detect-leaving-without-pin) with a recommendation per person ([ADR 0014](../entwicklung/adr/0014-ausgangserkennung.md)); [measurements](observations.md#measurements-on-the-settings-page) on the settings page to view, save and reset; [siren test](settings-page.md#siren-test-on-the-page-real-siren) also on the settings page; safety fix: direction "towards" no longer counts as "home" |
| 0.61 | "[On return](profiles.md#on-return)" per profile (nothing, disarm, with door proof, let in) with its own person list ([ADR 0015](../entwicklung/adr/0015-rueckkehr.md), German); ["away" only with proof](profiles.md#away-only-with-proof) – no false homecomings from sleeping phones, "door + signal" for persons without a location; [approach](profiles.md#approach-extends-the-entry-delay) lengthens the entry delay; explanations right at the setting (ⓘ, "this is how it behaves"); hide the settings page instead of switching it off, open it from the device page; [silent pauses](observations.md#what-is-a-silent-pause) explained |
| 0.62 | Explanations right at every setting: ⓘ at the fields in all side sheets, the sentence "This is how it behaves:" and "More settings" ([settings page](settings-page.md)) |
| 0.63 | [Testing presence](test-mode.md#testing-presence) ([ADR 0016](../entwicklung/adr/0016-anwesenheit-testen.md), German): see per person why they are home, away or unknown for Hauswacht, and per profile what the automation and "On return" are doing right now (test card and settings page); in test mode simulate home, away, away without proof, approaching and "skip waiting time"; simulated doors count like real ones. 0.63.1: docs page [How Hauswacht decides](how-hauswacht-decides.md), measurement "signs of life around the door". 0.63.2: the settings page is the only way – the old settings dialog and its wizard were removed |
| 0.64 | Tab **[Assistant](setup-wizard.md)** ([ADR 0017](../entwicklung/adr/0017-assistent-check-up.md), German): [hints while editing](setup-wizard.md#hints-while-editing-since-0640b2) right in the side sheets (what does not fit, with reason and measurement), [check-up](setup-wizard.md#check-up-in-the-assistant-tab-since-0640b3) with suggestions to apply one by one (preview, lenient ones only with confirmation), [scenario preview "What happens if …?"](setup-wizard.md#what-happens-if--since-0640b4) with the same rules as in real operation; a [frozen location](profiles.md#away-only-with-proof) does not count as proof; "all away" only plans while disarmed |
| 0.65 | [Set up by goals](setup-wizard.md#set-up-by-goals-since-0650b1) in the Assistant tab – secure the night, arm automatically when everyone is away, disarm when coming home, doors and windows, garage as its own area, with a plan "before → after" before saving; geofence as location, [own trigger for "all away"](profiles.md#own-trigger-for-all-away), "Why not armed?" ([ADR 0018](../entwicklung/adr/0018-geofence-und-eigener-ausloeser.md), German); [download configuration](settings-page.md#download-configuration) with placeholders instead of names ([ADR 0019](../entwicklung/adr/0019-konfiguration-herunterladen.md), German); [debug log](troubleshooting.md#debug-log-what-did-hauswacht-decide) without names and secrets ([ADR 0020](../entwicklung/adr/0020-debug-log.md), German) |
| 0.66 | [Presence per person](profiles.md#arriving-and-leaving-per-signal): arriving and leaving per signal, "one is enough (after a door)", measurements, recommendation and "what if", [own trigger per person](profiles.md#own-trigger-per-person) ([ADR 0021](../entwicklung/adr/0021-anwesenheit-je-person.md), German); [detect going out without a PIN](passage.md#detect-going-out-without-a-pin-exit-detection) – automatic passage with a sensor in the house, otherwise silent waiting time with phone check, [Alarm now] ([ADR 0014](../entwicklung/adr/0014-ausgangserkennung.md), German) |

Details for every version: [CHANGELOG](../../CHANGELOG.md) (German).

## Planned

| When | Content |
|---|---|
| 0.67 | **Privacy: no more stored coordinates.** Today, the "frozen location" detection keeps the last position of each tracker (rounded to 6 digits) in `.storage/hauswacht.frozen_locations`. In future only a short check value (hash) of the rounded position – "did not move" can be detected just as well, without a location lying around in a file. The old file is converted on update (suggestion from the forum) |
| 0.67 | **Delete single measurements:** remove outliers (e.g. a homecoming where the phone took 755 s) from the measurement on purpose, instead of resetting "arriving" completely – with a preview of what changes in recommendations and hints |
| 0.67 | **Check links in the docs:** all links between the documentation pages (German and English), anchors to sections, links from README, settings page, assistant and hints into the docs, and external links – fix broken ones and add an automatic check to the tests so it stays that way |
| on demand | ZHA keypads (frient, Xfinity, Centralite) with a device adaptation for ZHA – as soon as someone with such a device can help testing |
| soon | choose the HmIP-ASIR tone automatically per occasion (burglary, fire, test) – being looked into |
| later | developer documentation (architecture, tests, ADRs) in English; English screenshots |
| 1.0.0 | stable, documentation complete (inclusion in the Marketplace/HACS catalogue requested since 0.55.3) |
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
