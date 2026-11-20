# Control devices: keypads, cards, NFC stickers, RFID readers, buttons, door locks

[Deutsch](../bedienteile.md) | **English**

**System settings → Control devices.** Any number of control devices, each for one **area** or
for **all areas**. Identification always uses the **users' credentials** (PIN, RFID card, lock
ID): rights, validity, lockout after wrong entries and duress PIN apply as on the alarm panel.
"Changed by" shows e.g. "Anna (Keypad hallway)".

| Control device | Credential | Typical for |
|---|---|---|
| [Keypad (Zigbee2MQTT)](#keypad-zigbee2mqtt) | PIN and/or RFID card + key | wall next to the front door |
| [Keypad (generic)](#keypad-generic) | PIN and/or RFID card + key | keypads via ZHA, Z-Wave, ESPHome, Node-RED … |
| [MQTT interface](#mqtt-interface) | PIN and/or RFID card + command | wall tablets, home-made devices and programs that only speak MQTT |
| [NFC sticker](#nfc-sticker-companion-app) | your own phone (Home Assistant app) | residents with the app |
| [RFID reader](#rfid-reader) | RFID card, no key | hold up the card and done |
| [Fingerprint reader](#fingerprint-reader-esphome) | stored finger (like a card) | place a finger, e.g. in the hallway |
| [Button](#button) | **none** – so it only arms | button in the hallway: press, leave |
| [Door lock](#door-lock-eg-nuki) | who unlocked (Nuki user, keypad code …) | unlocking = disarmed |

## How well proven?

Not every control device could be checked with real hardware. So you know what you can rely on:

| Label | Meaning | Control devices |
|---|---|---|
| **Proven** | automated tests **and** checked in everyday use with real hardware | Keypad (Zigbee2MQTT), RFID cards at the keypad |
| **Tested** | automated tests, but no feedback with real hardware yet | Keypad (generic), MQTT interface, NFC sticker, RFID reader, fingerprint reader, button, door lock (Nuki and generic) |
| **Untested – own responsibility** | built from the manufacturer's docs, never checked on the device | [Templates](#ready-made-templates): blueprint Ring Keypad v2, ESPHome example |

Does something from "Tested" or "Untested" work reliably for you? A short note as a
[GitHub issue](https://github.com/schlusenbaum/hauswacht/issues) with device and firmware helps
everyone – then it moves up.

Where security depends on **your own setup**, it is your responsibility: access to the MQTT
broker (the same for Zigbee2MQTT), PINs in Home Assistant's database (see
[PINs outside Hauswacht](#pins-outside-hauswacht)), translators you wrote or changed yourself.

## Keypad (Zigbee2MQTT)

For alarm keypads according to the Zigbee standard for control devices (IAS ACE) – e.g.
frient/Develco KEPZB-110 and KEYZB-110, Linkind, Centralite, Heiman. Requires Zigbee2MQTT and the
MQTT integration in Home Assistant. Other keypads (ZHA, Z-Wave, ESPHome …): see
[Keypad (generic)](#keypad-generic).

**Setting up:**

1. Pair the keypad in Zigbee2MQTT and give it a sensible name, e.g. "Keypad". The name is part of
   the MQTT topic.
2. **System settings → Control devices → Add keypad:**

| Setting | Meaning |
|---|---|
| Name | e.g. "Keypad hallway" – appears in "changed by", e.g. "Anna (Keypad hallway)" |
| Area | one area or all |
| Keypad device | the keypad from the list (devices of Zigbee2MQTT or MQTT). Hauswacht builds the MQTT topic from it: `zigbee2mqtt/<name in Zigbee2MQTT>`, e.g. `zigbee2mqtt/Alarm-Keypad` |
| MQTT topic (experts only) | **leave empty** = automatically from the keypad device. Only needed if a base topic other than `zigbee2mqtt` is set in Zigbee2MQTT or the device does not appear in the list. Then: base topic + device name, written exactly as in Zigbee2MQTT (upper/lower case, hyphens), without `/set`. An entered topic takes precedence |
| Keys "Day", "Night", "All" | one alarm profile each for **arming**, e.g. Day → "Home", Night → "Night", All → "Away"; keys without a profile answer "not ready". On the frient keypad: **Day = 🏠 house**, **Night = 🌙 moon**, **All = 🔒 lock**. The keypad's own key 🔓 (open lock) disarms – do not create a profile for it. Assigning keys several times: [action codes](#action-codes) |
| Login | **PIN or card** or **card and PIN** (both credentials of the same user within 30 s; the first is acknowledged with "not ready") |
| Emergency key | **off** (default – then pressing SOS does nothing visible), **silent** (critical push message) or **alarm** (additionally an instant alarm – disarmed with the sirens under "Always active", armed with those of the active profile) |

**Keypad renamed in Zigbee2MQTT?** Then its MQTT topic changes too. Edit the keypad in Hauswacht
once and submit – the topic is built from the new name. If a custom topic is in the expert field,
adjust it.

3. Add the keypad's **tamper contact** (`binary_sensor.<keypad>_tamper`) to a sensor group (type
   Tamper) – sensibly only once it hangs firmly on the wall, and then select it in the profiles.
4. Optional: enter the battery in [Battery Notes](https://github.com/andrew-codechimp/HA-Battery-Notes)
   (frient KEPZB-110: 4 × AA).

**Operating:** first **type the PIN or hold up the card**, then press the **key** (Disarm, Day,
Night, All). The keypad only sends the code or card number together with a key press – holding
up a card alone switches nothing (that is what the [RFID reader](#rfid-reader) is for).

**Feedback:** Hauswacht answers every key press (valid, invalid credential, not ready – e.g.
window open –, already disarmed) and then continuously shows the state: exit and entry delay,
armed (day/night/all), alarm. For this Hauswacht sends to `<topic>/set` (`arm_mode`) – **only**
state displays to configured keypads; a test makes sure that Hauswacht sends nowhere else.

### Arm anyway at the keypad

If a sensor is still open (e.g. a tilted window) or unavailable when arming, the keypad answers
**"not ready"**. If the profile allows this **after confirmation**, you confirm at the keypad
like this:

1. Press the key, e.g. 🌙 night – with a PIN or card or, if arming without a PIN is allowed, also
   without → "not ready".
2. **Within 10 seconds** press **the same key** once more – with or without a PIN or card.
3. Hauswacht **arms anyway** and bypasses the open sensors until disarming – like "Arm anyway"
   in the card. You get the [note on arming](notifications.md#note-on-arming) saying what is not
   monitored.

Conditions:

- Profile setting "Open sensors when arming" or "Unavailable sensors when arming" = **allow
  after confirmation**. With **refuse** it stays "not ready" also on the second press; with
  **bypass automatically** no second press is needed.
- If the first press came with a PIN or card, the person needs the right **"May arm anyway at
  the keypad"** (default on; can be switched off in the user dialog, e.g. for children). The
  second press may then come without a PIN – it counts in this person's name.
- If the second press comes with a **different** PIN, it must be the same person. A wrong PIN is
  rejected as always.
- **Without a PIN** this only works if arming without a PIN is allowed ("PIN also for arming"
  off). Then anyone at the keypad can also arm anyway – just as they can arm without a PIN.
- If someone presses another key in between, the confirmation expires.
- With login "card and PIN", log in with both for the first press.

**Example:** in the evening the bathroom window is tilted. Anna types `2580` + 🌙 → "not ready".
She immediately presses 🌙 again → the keypad shows the exit delay, Hauswacht reports "Profile
Night is armed (Anna, Keypad hallway). Not monitored: bathroom window – open, bypassed until
disarming".

**PINs not in the history:** Zigbee2MQTT creates its own entity for the code typed at the keypad,
e.g. `sensor.keypad_hallway_action_code`. Home Assistant stores it in the history – i.e. every PIN
in plain text, also in backups. Hauswacht does not need it. Because the entity belongs to the MQTT
integration, Hauswacht does **not change it itself** but shows the issue "Hauswacht: PINs from
the keypad end up in the history" under **Settings → Repairs** (also if the entity only appears
later):

- **Fix** → confirm: Hauswacht disables the entity (like Settings → Entities → Disable).
- **Ignore**: the entity stays as it is.

If you deliberately enable it again afterwards, Hauswacht does not ask again. If you disable it
yourself, the issue disappears on its own. Home Assistant deletes entries already stored with the
normal history purge (default: 10 days) – at once with the action "Recorder: Purge entities" for
this entity.

Where the keypad should hang so that you reach it during the entry delay is shown by the
measurement ["Door open to disarmed"](observations.md#door-open-to-disarmed).

## Keypad (generic)

> **Tested** – checked with automated tests, but no feedback with real devices yet.
> See [How well proven?](#how-well-proven).

For keypads Hauswacht does **not** know itself: ZHA keypads (e.g. frient, Xfinity, Centralite),
Z-Wave keypads (e.g. Ring Keypad v2), deCONZ, home-made control devices with ESPHome, flows in
Node-RED – in short: anything Home Assistant can reach.

**How it works:** Hauswacht does not talk to the device directly. In between sits a small
**translator** – an automation (later also ready-made blueprints), a Node-RED flow or the device
itself. It translates in both directions:

```
Keypad ──button + PIN──► translator ──hauswacht.keypad_input──► Hauswacht
Keypad ◄──LEDs, beeps──  translator ◄──sensor.…_display───────── Hauswacht
```

Hauswacht evaluates the input **exactly like at the Zigbee2MQTT keypad**: rights, validity,
lockout after wrong entries, duress PIN, card and PIN, action codes, "arm anyway", emergency,
learning unknown cards.

### Setting up

**System settings → Control devices → Add keypad (generic)** – or on the
[settings page](settings-page.md) in the tab People and control devices:

| Setting | Meaning |
|---|---|
| Name | e.g. "Keypad hallway" – shows in "changed by", e.g. "Anna (Keypad hallway)" |
| Area | one area or all |
| Buttons | up to four buttons with a **free name** and an alarm profile each, e.g. `home` → "Home", `away` → "Away", `night` → "Night". The name is what your translator sends as `button`. `disarm` and `emergency` always exist – enter nothing for them |
| Login | **PIN or card** or **card and PIN** |
| Emergency button | off, silent or alarm – like at the [Zigbee2MQTT keypad](#keypad-zigbee2mqtt) |

After saving, the form shows the keypad's **ID**, e.g. `keypad_hallway`. The translator reports
inputs with it. Instead of the ID, the name or the display entity work too.

**Unknown keypad reported:** If a translator calls with an ID that does not exist in Hauswacht,
Hauswacht refuses (result `unknown_keypad`). The next "Add keypad (generic)" already has the
reported ID in the form – just pick buttons and area. So no unknown device can switch anything.

### The action `hauswacht.keypad_input`

| Field | Meaning | Example |
|---|---|---|
| `keypad` | ID, name or display entity of the keypad | `keypad_hallway` |
| `button` | `disarm`, `emergency` or an own button | `away` |
| `code` | typed PIN or card number read | `2580` |
| `force` | "arm anyway" – bypass open sensors if the profile and the user allow it | `true` |

The action **responds**. In an automation you get the response with `response_variable`:

| Response | Meaning |
|---|---|
| `result` | `ok` · `invalid_code` (wrong credential **or** no rights – deliberately indistinguishable) · `locked` (too many failed attempts) · `not_ready` (e.g. window open) · `pending` (card and PIN: first credential recognised, second missing) · `already_disarmed` · `unknown_button` · `unknown_keypad` |
| `display` | what the keypad should show now (like the display entity) |
| `open_sensors` | with `not_ready`: which sensors prevent it, e.g. `["Kitchen window"]` |
| `can_force` | with `not_ready`: "arm anyway" would be possible (same input twice or `force: true`) |
| `lock_seconds` | with `locked`: how long the lockout lasts |

**Duplicate messages:** Radio devices sometimes send twice. The same input from the same keypad
within 2 seconds is evaluated only once – a wrong PIN sent twice does not count twice.

**Who may call the action?** Automations, scripts, devices (e.g. ESPHome) and administrators.
Not normal users – they use the Hauswacht card. Otherwise any logged-in user could trigger e.g.
an emergency without a PIN.

### The display entity

Each generic keypad gets an entity **"Keypad hallway display"**
(`sensor.hauswacht_keypad_hallway_display`). Your translator reacts to its changes and controls
the device with them:

| State | Meaning | Typical at the keypad |
|---|---|---|
| `disarmed` | disarmed | green / off |
| `exit_delay` | exit delay running | beeping, countdown |
| `armed_home`, `armed_away`, `armed_night`, `armed_vacation`, `armed_custom_bypass` | armed (depending on the profile's button) | red |
| `entry_delay` | entry delay – enter the PIN now | fast beeping |
| `triggered` | burglary alarm | alarm |
| `test_alarm` | alarm in **test mode** | show only, **no** siren |
| `fire` | fire detected (takes precedence over everything) | fire display |

In test mode the entity **never** shows `triggered`, but `test_alarm`. So a keypad with a
built-in siren cannot go off by accident in test mode.

Attributes: `delay_ends` and `delay_seconds` (end and rest of the delay – for a countdown),
`profile`, `changed_by`, `test_mode`, `buttons`, `last_result` (result of the last input) and
`last_result_at`. **Never** included: PINs and card numbers.

### Example: translator as an automation

A home-made ESPHome keypad fires an event `esphome.keypad_hallway` with `button` and `code` when a
button is pressed. The first automation passes the input on to Hauswacht and lets the keypad's
buzzer beep briefly on an error:

```yaml
alias: Keypad hallway → Hauswacht
mode: queued
triggers:
  - trigger: event
    event_type: esphome.keypad_hallway
actions:
  - action: hauswacht.keypad_input
    data:
      keypad: keypad_hallway
      button: "{{ trigger.event.data.button }}"
      code: "{{ trigger.event.data.code }}"
    response_variable: answer
  - if: "{{ answer.result not in ['ok', 'pending'] }}"
    then:
      - action: esphome.keypad_hallway_beep  # error tone (the device's own action)
```

The second automation shows on the keypad what Hauswacht reports – also after a restart:

```yaml
alias: Hauswacht → Keypad hallway
mode: restart
triggers:
  - trigger: state
    entity_id: sensor.hauswacht_keypad_hallway_display
    not_to: [unknown, unavailable]
  - trigger: homeassistant
    event: start
conditions:
  - condition: not
    conditions:
      - condition: state
        entity_id: sensor.hauswacht_keypad_hallway_display
        state: [unknown, unavailable]
actions:
  - action: esphome.keypad_hallway_show  # the device's own action
    data:
      mode: "{{ states('sensor.hauswacht_keypad_hallway_display') }}"
```

An ESPHome device can also call the action **directly** (`homeassistant.action` with
`action: hauswacht.keypad_input`) and read the display entity itself – then no automation is
needed at all. In the ESPHome integration, "Allow the device to perform Home Assistant actions"
must be switched on for that.

### Ready-made templates

> **Untested – use at your own responsibility.** The templates are built from the device and
> community documentation, but never checked on a real device. Does one work for you? Please
> report briefly as a [GitHub issue](https://github.com/schlusenbaum/hauswacht/issues) (device,
> firmware) – then it moves up to "tested by the community".

| Device | Template | What it does |
|---|---|---|
| **Ring Keypad v2** (Z-Wave JS) | Blueprint [ring_keypad_v2.yaml](https://github.com/schlusenbaum/hauswacht/blob/main/blueprints/automation/hauswacht/ring_keypad_v2.yaml) – [![Import blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fschlusenbaum%2Fhauswacht%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fhauswacht%2Fring_keypad_v2.yaml) | Disarm, Away (button `away`), Home (button `home`), hold the police button = emergency. Error tone on a wrong PIN, Enter blinks on "not ready". Lights and sounds follow the display entity, with a countdown during the delays. In test mode only the medical light, no alarm sound |
| **Home-made with ESPHome** (4×4 keypad, two LEDs) | Example [hauswacht_keypad.yaml](https://github.com/schlusenbaum/hauswacht/blob/main/blueprints/esphome/hauswacht_keypad.yaml) | PIN + A/B/C/D, calls the action directly – no automation. LEDs follow the display entity. To adapt (pins, ID, entity) |

**Setting up the Ring Keypad:**

1. In Hauswacht, add a "Keypad (generic)" with the buttons `away` and `home` and an alarm profile
   each.
2. Import the blueprint (button above) and create an automation from it: choose the Ring Keypad and
   the display entity of the Hauswacht keypad, save.
3. Try it: type the PIN, press "Home".

**Most convenient from the settings page:** with the "Keypad (generic)", "Ring Keypad v2: import
blueprint" is listed below the buttons. It opens in a **new tab** and fetches the blueprint from
**exactly your Hauswacht version** – also for pre-releases. The button here in the guide always
fetches the latest released version (GitHub opens it in the same tab; Ctrl- or ⌘-click opens a
new one).

The template carries a **version number** (in the description). If there is a new one, choose
"Re-import blueprint" in the blueprint.

**ZHA keypads (frient, Xfinity, Centralite …):** ZHA connects these keypads to a small alarm panel
of its own in ZHA – buttons and PIN then never reach an automation. To work with Hauswacht, a
device adaptation for ZHA (quirk) is needed. There is no template for this yet. If you have such
a keypad and want to help testing: please open an issue. With **Zigbee2MQTT** the same keypads
already work directly today – see [Keypad (Zigbee2MQTT)](#keypad-zigbee2mqtt).

### PINs outside Hauswacht

Hauswacht never stores PINs in plain text. **Your translator, however, may:**

- If a device reports the PIN as an **event** (e.g. `zha_event`, `zwave_js_notification` or, as
  in the example, `esphome.keypad_hallway`), Home Assistant stores this event in its database –
  with the PIN, also in backups.
- The automation's **trace** contains the PIN as well.

Hauswacht cannot prevent this. What helps:

```yaml
# configuration.yaml – do not store events with PINs in the database
recorder:
  exclude:
    event_types:
      - esphome.keypad_hallway
```

Note: this removes **all** events of this type from the database – with `zha_event`, for example,
also those of other ZHA devices. And keep the number of stored traces in the automation small
(`trace: stored_traces:` with a small number).

## MQTT interface

> **Tested** – checked with automated tests, but no feedback with real devices yet.
> See [How well proven?](#how-well-proven).

For devices and programs that **only speak MQTT** and do not know Home Assistant: wall tablet apps
for MQTT alarm panels, Tasmota or Arduino home-made devices, Node-RED, other systems. An MQTT
interface is a keypad – Hauswacht evaluates its commands **exactly like at the Zigbee2MQTT
keypad** (rights, lockout, duress PIN, card and PIN, action codes, "arm anyway", emergency).

### Setting up

**System settings → Control devices → Add MQTT interface** – or on the
[settings page](settings-page.md) in the tab People and control devices:

| Setting | Meaning |
|---|---|
| Name, area | as with every control device |
| Base topic | e.g. `hauswacht/hallway` – all topics live below it (see below). Not below `zigbee2mqtt`, no `+` or `#`; each interface needs its own |
| Command words → alarm profile | the word your device sends to arm, and the profile for it, e.g. `ARM_AWAY` → "Away", `ARM_HOME` → "Home", `ARM_NIGHT` → "Night". Case and spaces do not matter |
| Command word for disarm / emergency | default `DISARM` and `PANIC` |
| Name of the code field in JSON | default `code` – some devices send `pin` |
| Login, emergency button | as with the [Zigbee2MQTT keypad](#keypad-zigbee2mqtt) |
| Own state words | for experts: one line per state, e.g. `armed_away: ARMED_AWAY` |

### Topics

| Topic | Direction | Stored (retain) | Content |
|---|---|---|---|
| `hauswacht/hallway/set` | to Hauswacht | – | command |
| `hauswacht/hallway/state` | from Hauswacht | yes | state as a word |
| `hauswacht/hallway/attributes` | from Hauswacht | yes | details as JSON |
| `hauswacht/hallway/response` | from Hauswacht | no | response to every command |
| `hauswacht/hallway/availability` | from Hauswacht | yes | `online` / `offline` |

**Commands** as text or JSON:

```
ARM_AWAY
DISARM
{"action": "ARM_NIGHT", "code": "2580"}
{"action": "ARM_NIGHT", "code": "2580", "force": true, "id": 17}
```

`force` means "arm anyway" (only with the right for it), `id` comes back in the response. As at
the keypad, disarming only works with a PIN or card. **Hauswacht never executes stored commands
(retain)** – otherwise an old `DISARM` would arrive again after every restart. Hauswacht reports
such a message with the event `MqttRetainedCommand`.

**State:** default words like Home Assistant's MQTT alarm panel – so many ready-made tablet apps
fit without changes:

| Hauswacht | Word |
|---|---|
| disarmed | `disarmed` |
| exit delay | `arming` |
| armed | `armed_home`, `armed_away`, `armed_night`, `armed_vacation`, `armed_custom_bypass` (depending on the profile's button) |
| entry delay | `pending` |
| alarm, fire | `triggered` |
| alarm in test mode | `test_alarm` – **never** `triggered`, so a device with its own siren cannot go off in test mode |

**Response** (JSON) – the same results as with the [action `hauswacht.keypad_input`](#keypad-generic):

```json
{"keypad": "tablet_hallway", "result": "not_ready", "display": "disarmed",
 "open_sensors": ["Kitchen window"], "can_force": true, "lock_seconds": 0, "id": 17}
```

**Details** (`attributes`, JSON): `state`, `display` (state as with the display entity), `area`,
`profile`, `delay_ends`, `delay_seconds`, `test_mode`, `changed_by`, `buttons`, `last_result`.
**Never** included: PINs, card numbers.

### Trying it out without a device

With an MQTT program, e.g. the **MQTT Explorer** add-on:

1. In the **Publish** area, type `hauswacht/hallway/set` into the **topic** field by hand. The topic
   does not exist beforehand – it comes into being with the first message. Hauswacht itself never
   sends on `set`, it only listens there.
2. Format **json**, message `{"action": "ARM_NIGHT", "code": "2580", "id": 1}`, **retain off**,
   send.
3. The response is under `hauswacht/hallway/response`, the new state under `…/state`. Back with
   `{"action": "DISARM", "code": "2580"}`.

Home Assistant's log shows every command (without the PIN), e.g. "MQTT-Schnittstelle Tablet
hallway: Befehl arm_night mit Ausweis → ok" – visible if the log level for Hauswacht is "info" or
finer.

### Security: secure the broker

**Whoever may write to the broker may operate the system** – just like with Zigbee2MQTT keypads
today. Therefore:

- Each device gets its **own broker user** with a password.
- **Access rights (ACL)** as narrow as possible, e.g. for the tablet in the hallway:
  ```
  user tablet_hallway
  topic read hauswacht/hallway/#
  topic write hauswacht/hallway/set
  ```
  With Home Assistant's Mosquitto add-on, these rules go into a separate ACL file (see the add-on's
  documentation).
- No anonymous access, do not expose the broker to the internet; outside the home network only
  with TLS.
- Typed PINs travel over the broker in plain text – another reason for TLS and separate users.

## Action codes

**System settings → Control devices → Action codes.** An action code is a **code plus a function
key** at the keypad, e.g. **7777 + 🏠 house**. It triggers a fixed action – this way the keys of
the keypad can be assigned several times:

```
➕ New action code
outdoor light – 7777 + 🏠 house · all keypads → event
light off – 7777 + 🌙 night · all keypads → event
garage light – 42 + 🔒 lock · Keypad hallway → event
emergency – 9111 + 🌙 night · all keypads → silent emergency
```

| Field | Meaning |
|---|---|
| Name | e.g. "outdoor light" – shown in the logbook and, for "event", the event type |
| Code | **2–8 digits**. Must not equal a PIN, duress PIN or master PIN (and vice versa) |
| Key | 🏠 house, 🌙 night, 🔒 lock or 🔓 open lock. SOS does not work – it sends no code |
| Keypad | all or a specific one |
| Action | **Event** for your own automation, **Arm** with a profile or **silent emergency** |

The same code may have different actions with different keys. Code + key may exist only once,
though. Tap an entry: change or delete it.

**At the keypad:** type the code, then press the key. The keypad gets a positive response and
then shows the state again. An action code **never counts as a failed attempt** – during a
[PIN lockout](users.md#lockout-after-wrong-entries) it is locked too, though. If a code with a key
is set up as an action code, it takes precedence over the normal assignment of the key.

**Not a credential:** an action code belongs to no person and is not secret – whoever knows or
guesses it triggers the action. That is why it can **never disarm**, and you should not trigger
anything security-critical with it (e.g. door openers, garage door).

### Action "event": your own automation

As soon as there is an action code with "event", Hauswacht has the entity
**`event.hauswacht_action_code`** ("Hauswacht action code"; with German language
`event.hauswacht_aktions_code`). For every action code it reports an event with the **name** of
the code as event type. Hauswacht itself switches nothing – your automation decides what happens.

**Example – 7777 + house switches the outdoor light on for 5 minutes:**

1. Add an action code: name "outdoor light", code `7777`, key 🏠 house, action event.
2. New automation. Trigger: state of "Hauswacht action code" (every event changes it).
   Condition: attribute "event type" is "outdoor light". In YAML:

```yaml
triggers:
  - trigger: state
    entity_id: event.hauswacht_action_code
conditions:
  - condition: state
    entity_id: event.hauswacht_action_code
    attribute: event_type
    state: outdoor light
actions:
  - action: light.turn_on
    target:
      entity_id: light.outdoor
  - delay: "00:05:00"
  - action: light.turn_off
    target:
      entity_id: light.outdoor
```

Why not directly "attribute changes to outdoor light"? If the same code is typed twice in a row,
the event type stays the same – the automation would only run the first time. The state (time of
the last event) changes every time.

The entity also has the attributes `keypad` (which keypad) and `test` (test mode on).

### More examples

**Try out what arrives:** Developer tools → Events → under "Listen to events" enter
`hauswacht_event` → "Start listening" → type the code at the keypad and press the key. You see
e.g.:

```yaml
event_type: hauswacht_event
data:
  type: ActionCode
  name: outdoor light
  action: event
  control: Keypad hallway
  test: false
  area: all            # keypad for all areas; otherwise the keypad's area, e.g. garage
  area_name: All areas
```

`area` is the area of the **control device**: a keypad "for all areas" reports `all`, one for the
garage `garage`. Whoever filters by `area` in the trigger must therefore use the keypad's area –
not the area the code arms.

This event `hauswacht_event` comes with **every** action code – also with "arm" and "silent
emergency". As a trigger it is often simpler than the entity, because a single trigger is
enough:

**A – outdoor light with only one trigger** (same effect as above):

```yaml
alias: Outdoor light via keypad
triggers:
  - trigger: event
    event_type: hauswacht_event
    event_data:
      type: ActionCode
      name: outdoor light
actions:
  - action: light.turn_on
    target:
      entity_id: light.outdoor
  - delay: "00:05:00"
  - action: light.turn_off
    target:
      entity_id: light.outdoor
mode: restart
```

In the automation editor: trigger → **Manual event received** → event type `hauswacht_event`,
event data `type: ActionCode` and `name: outdoor light`. `mode: restart` makes a repeated code
restart the 5 minutes.

**B – one code, two keys: light on and off.** Add two action codes: "light on" (`7777` + 🏠
house) and "light off" (`7777` + 🌙 night), both with action event. One automation for both:

```yaml
alias: Living room light via keypad
triggers:
  - trigger: event
    event_type: hauswacht_event
    event_data:
      type: ActionCode
      name: light on
    id: "on"
  - trigger: event
    event_type: hauswacht_event
    event_data:
      type: ActionCode
      name: light off
    id: "off"
actions:
  - choose:
      - conditions:
          - condition: trigger
            id: "on"
        sequence:
          - action: light.turn_on
            target:
              entity_id: light.living_room
      - conditions:
          - condition: trigger
            id: "off"
        sequence:
          - action: light.turn_off
            target:
              entity_id: light.living_room
```

**C – arm and do something else at the same time.** Action code "good night" (`11` + 🔒 lock)
with action **Arm → Night**. Hauswacht arms; this automation also closes the shutters:

```yaml
alias: Good night via keypad
triggers:
  - trigger: event
    event_type: hauswacht_event
    event_data:
      type: ActionCode
      name: good night
actions:
  - action: cover.close_cover
    target:
      area_id: living_room
```

**Exclude test mode:** if nothing should happen in [test mode](test-mode.md), add this
condition:

```yaml
conditions:
  - condition: template
    value_template: "{{ not trigger.event.data.test }}"
```

### Actions "arm" and "silent emergency"

- **Arm:** arms the chosen profile, just like the key with a profile – with the check of open
  sensors and exit delay. The logbook shows e.g. "action code “night by code” (Keypad hallway)".
  This also applies if "PIN when arming" is on under PIN rules: whoever sets up an action code
  for arming wants exactly that.
- **Silent emergency:** important push message "emergency at Keypad hallway" to the alarm
  recipients – like the SOS key on "silent", but inconspicuously via a normal key. No siren, no
  display on the keypad. If the event "Alarm" has no recipient, the
  [system overview](overview.md#check-hints) reports this as an important hint (also under
  repairs). In the overview and its printout this code only appears as "hidden".

## Learning cards

RFID cards, tags, fingers at the [fingerprint reader](#fingerprint-reader-esphome) and IDs of
[door locks](#door-lock-eg-nuki) are managed in one place: **System settings → Users and PINs →
Cards and tags.** Below, all of this is simply called "card".

### The card list

The list shows every card with name, number, owner and when it last switched:

```
➕ Learn new card (hold it up)
⌨️ Type in card number
🟢 key ring (04A1B2C3) – Christian · last 07:12
🟢 wallet (0011223344) – Christian · last 02.11.2026
⏸️ spare card (A1B2C3D4E5) – Anna · disabled
🟢 Nuki app (Nuki user 4711) – Anna · never used
```

🟢 = active, ⏸️ = disabled. "Last" shows the time for today, otherwise the date.

### Learn a new card

1. All areas disarmed.
2. **Cards and tags → ➕ Learn new card (hold it up).** The dialog shows: *"Hold the new card to
   a keypad now (and press Disarm) or to a reader"*. For a door lock: unlock once with the new
   ID.
3. **As soon as the card has been read, it continues at once:** "✅ Card recognised". Enter a
   **name** (e.g. "key ring"), choose the **user**, save.

At the frient keypad, holding up the card alone is not enough – it only sends the number with
**Disarm**. If no card comes for 2 minutes, the dialog continues without a card.

Only a card read **during** the dialog counts. A card from an earlier, cancelled attempt is not
preselected.

**⌨️ Type in card number:** without waiting. The recently read unknown cards (within the learning
time) are offered here as "new, read at Keypad at 18:04", or you type in the number.

**Example:** Anna gets a new tag. Cards and tags → Learn new card → hold the tag to the keypad in
the hallway, press Disarm → "✅ Card recognised: 04C3D2E1" → name "key ring", user "Anna" →
submit. From now on Anna's tag switches, and the logbook shows "Anna · key ring (Keypad hallway)".

### Edit, disable, delete a card

Tap a card in the list:

| Field | Meaning |
|---|---|
| Name of the card | e.g. "key ring", "wallet", "right thumb", "Nuki app". Empty = no name |
| Belongs to | user – this is also where you hand a card over to someone else |
| Active | off = **disabled**: the card switches nothing any more but stays known |
| Delete card | final; afterwards it is rejected like an unknown card |

**A disabled card is used:** it switches nothing, the keypad shows "invalid", and it counts as a
failed attempt for the [lockout](users.md#lockout-after-wrong-entries). You get a message: *"The
disabled card “wallet” (Christian) was used at Keypad hallway."* With a disabled lock ID,
Hauswacht also switches nothing and reports it (a door lock does not count as a failed attempt).

**Example – wallet gone:** Christian misses his wallet with the tag in it. Cards and tags →
"wallet (0011223344) – Christian" → **Active off** → submit. If the wallet turns up again: active
on again. If it stays lost: **Delete card**. If anyone tries to disarm with the tag in the
meantime, you know at once.

With names, the logbook, the alarm panel ("changed by") and messages also show **which** card
was used – "Christian · key ring (Keypad hallway)" – and the [system overview](overview.md)
shows "key ring …B2C3" (disabled ones with ⏸).

### Rules for learning

- The learning time can be set under **Control devices → Learning new cards** (1–60 minutes,
  0 = learning off). After that the card is forgotten; whoever saves too late gets a hint and
  holds up the card again.
- Unknown cards do not count as a failed attempt for the [lockout](users.md#lockout-after-wrong-entries).
- Card numbers can also be typed in (e.g. `041B4932E82880`; upper/lower case and separators do
  not matter). Codes with 4–8 digits could be PINs and are never offered for learning – type
  such card IDs in.
- A card belongs to exactly one user.

**Which cards work?** The frient keypad reads 13.56 MHz cards according to ISO 14443 A (e.g.
MIFARE Classic, MIFARE DESFire, NTAG tags, many company badges) and reports their fixed number
(UID).

**Random IDs are not suitable:** phones and some badges in privacy mode report a **different**
number on every read – recognisable by 4 bytes starting with `08` (e.g. `+08837CF0`). Hauswacht
does not offer them for learning, rejects them when saving and shows a hint in the user dialog.

## NFC sticker (companion app)

An NFC sticker on the door, scanned with the Home Assistant app. The sticker only says **where
and what** – identification is the **phone**: the logged-in Home Assistant account must be
linked to an authorised Hauswacht user. A copied sticker alone is therefore useless.

| Setting | Meaning |
|---|---|
| Sticker ID | under Settings → Areas, labels & zones → Tags (after the first scan) |
| Action | disarm, arm (profile) or toggle (armed ↔ disarmed) |

The phone must be unlocked. No key press needed.

## RFID reader

A fixed reader that fires the Home Assistant event "Tag scanned" – e.g. an ESP32 with PN532 or
RC522 via ESPHome. Unlike the keypad, **holding up the card** is enough.

| Setting | Meaning |
|---|---|
| Reader device | appears in the event "Tag scanned" (`device_id`) |
| Action | disarm, arm (profile) or toggle |
| Login | **Card** or **card and PIN** (then within 30 s the PIN of the same user at a keypad in the same area) |

"Toggle" is convenient but can also arm by accident. Simple 125 kHz cards are easy to copy –
better use 13.56 MHz cards or NFC via phone.

### Fingerprint reader (ESPHome)

A fingerprint sensor on an ESP32 reports the recognised finger like a card. In Hauswacht it is
therefore simply an **RFID reader** – a finger is a credential like a card.

**What you need:**

| Part | Example | Price approx. |
|---|---|---|
| Microcontroller | ESP32 board (e.g. ESP32-DevKitC) | €5–10 |
| Fingerprint sensor | **R503** (round, with LED ring; also R307, ZFM-20) | €15–25 |
| Software | [ESPHome](https://esphome.io/components/fingerprint_grow.html) (component `fingerprint_grow`) | free |

Wiring: 3.3 V and GND from the ESP32; the sensor's TX to the ESP32's RX pin, the sensor's RX to
the TX pin; the WAKEUP wire to a free pin (`sensing_pin`), so the sensor notices a finger at once.

**ESPHome configuration** (device called `fingerprint-hallway` here, adjust the pins):

```yaml
esphome:
  name: fingerprint-hallway

esp32:
  board: esp32dev

uart:
  rx_pin: GPIO16      # to the sensor's TX
  tx_pin: GPIO17      # to the sensor's RX
  baud_rate: 57600

fingerprint_grow:
  sensing_pin: GPIO4  # the sensor's WAKEUP
  on_finger_scan_matched:
    - if:
        condition:
          lambda: 'return confidence > 50;'
        then:
          - homeassistant.tag_scanned: !lambda 'return "FINGER" + to_string(finger_id);'
          - fingerprint_grow.aura_led_control:
              state: FLASHING
              speed: 25
              color: BLUE
              count: 2
  on_finger_scan_unmatched:
    - fingerprint_grow.aura_led_control:
        state: FLASHING
        speed: 25
        color: RED
        count: 2

api:
  actions:
    - action: enroll_finger
      variables:
        finger_id: int
      then:
        - fingerprint_grow.enroll:
            finger_id: !lambda 'return finger_id;'
            num_scans: 2
    - action: delete_finger
      variables:
        finger_id: int
      then:
        - fingerprint_grow.delete:
            finger_id: !lambda 'return finger_id;'

sensor:
  - platform: fingerprint_grow
    fingerprint_count:
      name: "Enrolled fingers"
    last_finger_id:
      name: "Last finger"
    last_confidence:
      name: "Last confidence"
```

**Setting up:**

1. **Store fingers in the sensor:** Developer tools → Actions →
   `esphome.fingerprint_hallway_enroll_finger` with `finger_id: 1` → place the same finger twice.
   Use a separate number for each finger (slot 1, 2, 3 …). Best keep a small list: 1 = Anna,
   right index finger; 2 = Anna, left index finger; 3 = Ben …
2. **In Hauswacht:** System settings → Control devices → **Add RFID/NFC reader** → reader device
   "fingerprint-hallway" → action e.g. "disarm".
3. **Assign the finger to the user** like a [card](#learn-a-new-card): everything disarmed,
   Users and PINs → Cards and tags → Learn new card → place the finger → "✅ Card recognised:
   FINGER1" → name "right index finger", user "Anna" → save. Or type `FINGER1`.

Good to know:

- **Nothing arrives?** Listen to `tag_scanned` under Developer tools → Events and place a finger.
  If it stays silent: Settings → Devices & services → ESPHome → the device → Configure →
  switch on **"Allow the device to perform Home Assistant actions"**.
- The fingerprints themselves stay **in the sensor**. Home Assistant and Hauswacht only see the
  slot number ("FINGER1").
- An **unknown finger** sends nothing – so it does not count as a failed attempt either.
- `confidence > 50` is the minimum match; higher = fewer false matches, but more often "not
  recognised". In addition, `security_level` (1–5) can be set on the sensor.
- The LED only shows whether the **sensor** recognised the finger – not whether Hauswacht disarmed
  (e.g. missing right or lockout). Keypad, alarm card and logbook show that.
- **More security:** login "card and PIN" – after the finger, the PIN at the keypad within 30 s.
- **Security of the reader:** whoever takes over the ESP32 or its Wi-Fi can send any number. Mount
  the reader **inside** (e.g. in the hallway within reach during the entry delay), run ESPHome
  with an API key and password, and secure the housing against opening. Outside at the door, a
  lock with its own fingerprint reader (e.g. Nuki Keypad 2.0, see [Door lock](#door-lock-eg-nuki))
  is the more robust choice.
- A **lost or injured finger**: delete the slot in the sensor
  (`esphome.fingerprint_hallway_delete_finger`) and remove the ID from the user.

> These instructions follow the ESPHome documentation; they have not yet been tried with real
> hardware for Hauswacht. Feedback welcome as an [issue](https://github.com/schlusenbaum/hauswacht/issues).


## Button

A button – e.g. a Zigbee button in the hallway – **arms** an alarm profile, with the profile's
exit delay. Press, leave, done.

> A button identifies **nobody**: whoever stands in front of it is unknown. That is why it
> **only arms** – never disarms, and it never ends an alarm.

**Setting up:** System settings → Control devices → **Add button**.

1. Choose name, area and the **button**:
   - an **event entity** (`event.…`) – this is how Zigbee2MQTT (newer versions), Hue, Shelly and
     Matter provide their buttons, or
   - an **action sensor** (`sensor.…_action`), as older Zigbee2MQTT versions create them.
2. In the second step you decide which **press type** arms which profile:
   - With an event entity, Hauswacht shows the device's press types itself (e.g. `single`,
     `double`, `long`). Leave empty = this press type does nothing.
   - With an action sensor you enter the **value** the sensor takes when pressed. How to find it:
     Developer tools → States → search for the sensor → press the button → the value appears
     briefly (e.g. `single`, `double`, `hold`).

**Example:** button in the hallway, single → "Away", double → "Night". The logbook shows "changed
by: Button hallway".

Good to know:

- If a profile is already armed, the button does nothing – it never switches over another
  profile.
- If sensors are open, the setting of the profile applies (e.g. "refuse") – you then get the
  usual message "not armed".
- If the PIN rules **require a PIN for arming**, the button does **not** arm – it cannot enter a
  PIN. Hauswacht then sends a system message.
- If the button comes back after a radio outage, that does not count as a press.
- Every press reports the event `ButtonPressed` (see [reference](reference.md#operation-1)).
  Its field `area` is the area of the button – for a button "for all areas" it is `all`. The same
  applies to the door lock and the emergency key.
- A button **outside** at the door is not forbidden, but then anyone passing by can arm (and
  whoever is inside triggers the alarm later). Better mount it inside.

## Door lock (e.g. Nuki)

An electronic door lock **disarms when a known user unlocks** – with that user's rights per area.
The logbook shows e.g. "Anna (Front door lock)". Optionally, **locking from outside** arms a
profile.

For this the lock must tell **who** unlocked. Merely opening the door, or "unlocked" without a
person, is never enough.

> Hauswacht **only reads along** and never operates the lock itself.

### What Hauswacht requires

Hauswacht only disarms if **both** come together, at most 30 seconds apart:

1. an **ID** from the lock that belongs to a Hauswacht user (e.g. their Nuki app access or their
   keypad code), and
2. the lock really changes to **"unlocked"** or "open" in Home Assistant.

Why both? Some Nuki models also report a **wrongly** typed keypad code as unlocking (a known
firmware bug). Without the lock actually moving, nothing happens.

**Never disarms**

| Situation | Why |
|---|---|
| ID unknown or missing | it is not clear who it was (Hauswacht reports this with a system message while armed) |
| Knob or button on the lock (inside) | no credential |
| Time control, automatic locking | no person |
| Unlocking via Home Assistant, HomeKit or MQTT | no credential at the door |
| The door only opens | no unlocking |
| The user may not disarm or has expired | rights apply as on the alarm panel |

### Setting up with Nuki via MQTT

Requires a Nuki Smart Lock (3.0 Pro, 4th or 5th generation) with **MQTT** switched on in the Nuki
app, and the MQTT integration in Home Assistant. The lock itself is usually already in Home
Assistant as `lock.…`, via MQTT or the Nuki integration.

1. **System settings → Control devices → Add door lock.**
2. Fill in:

| Setting | Example | Meaning |
|---|---|---|
| Name | Front door lock | appears in the logbook |
| Area | House | which area is disarmed |
| Lock | `lock.front_door` | the entity in Home Assistant |
| Source | Nuki via MQTT | |
| MQTT topic | `nuki/3A1B2C4D` | base topic of the lock (the Nuki ID in hex), **without** `/lockActionEvent` |
| Arm when locking | empty or "Away" | optional, see below |

Hauswacht then reads `nuki/3A1B2C4D/lockActionEvent`. The Nuki sends five numbers there for every
action, e.g. `1,0,52653,0,0`:

| Position | Meaning | Example |
|---|---|---|
| 1 | action: 1 = unlock, 2 = lock, 3 = unlatch, 4 = lock 'n' go, 6 = full lock | `1` |
| 2 | trigger: 0 = app/Bluetooth, keypad, fob; 2 = button on the lock; 3 = time control; 6 = automatic; 171 = HomeKit/Matter; 172 = MQTT | `0` |
| 3 | auth ID: who (app access) | `52653` |
| 4 | code ID: which keypad code (0 = none) | `0` |
| 5 | extra (e.g. fingerprint, auto unlock) | `0` |

Hauswacht only counts trigger **0**. The code ID or auth ID becomes the ID shown with the user:
"Nuki keypad code 8192" or "Nuki user 52653" (stored as `NUKICODE8192` or `NUKIAUTH52653`).

**Fingerprint on the Nuki Keypad 2.0:** a fingerprint arrives like a keypad code (its own code
ID, a `2` for "fingerprint" in position 5). It is therefore learned the same way as "Nuki keypad
code …" – the simplest way to a fingerprint at the front door.

### Learning IDs

Like [cards](#learning-cards):

1. All areas disarmed.
2. Users and PINs → Cards and tags → **Learn new card (hold it up)**.
3. **Unlock once** with the app, the keypad code or the fingerprint – the dialog recognises the ID
   at once → name e.g. "Nuki app", choose the user → save.

Already unlocked before? Then "Type in card number": the ID is offered there as "Nuki user 52653
(new, read at Front door lock at 18:04)".

Best learn each person separately, so it is clear which ID belongs to whom. Every keypad code and
every app access is its own ID; a user can have several.

### Locking = armed (optional)

If a profile is entered, **locking from outside** by a known user with the right to arm arms this
profile – but only if everything is disarmed. Automatic locking, time control and the button
inside do not count.

> Careful: for Nuki, "from outside" only means "via app, keypad or fob". Whoever locks **from bed
> via the app** in the evening also arms. For the front door, therefore choose a profile like
> "Away" and do not use the app for this from inside – or leave the field empty.

### Other locks (generic source)

For locks that show the user as a **sensor** or **event** in Home Assistant (e.g. a sensor "last
opened by" or an event with the user name):

| Setting | Example |
|---|---|
| Source | Generic |
| Sensor or event with the ID | `sensor.front_door_user` |

If the value changes (or an event arrives) and the lock unlocks within 30 seconds, the value
counts as the ID – e.g. "Anna" becomes `LOCKANNA`. Learning works as above.

Important: the sensor may change its value **only when unlocking**. If it also shows who last
**locked**, Anna locking and a later unlocking by a stranger would be combined if both happen
within 30 seconds.

## Security

- A pure card number is no strong protection: whoever reads it (e.g. in passing) can copy it. For
  more security, use "card and PIN".
- At the keypad, the required key press protects against a card in your jacket pocket switching
  something.
- Lost card: remove it from the user or set the user to "Active: off".
- The duress PIN also works at the keypad.
- **MQTT interface:** the same rules as at the keypad; stored commands are never executed. Secure
  the broker – see [Security: secure the broker](#security-secure-the-broker).
- **Generic keypad:** the same rules apply as at the Zigbee2MQTT keypad – disarm only with a PIN
  or card. Only keypads that are set up are accepted, and only automations, scripts, devices and
  administrators may call the action. Whether the PIN ends up somewhere in plain text depends on
  the translator – see [PINs outside Hauswacht](#pins-outside-hauswacht).
- **Door lock:** whoever has the phone with the Nuki app **and** its access disarms by unlocking –
  just as they can open the door. Lost phone: block the access in the Nuki app **and** remove the
  ID from the user.
- **Buttons:** only arm; they are no credential.
