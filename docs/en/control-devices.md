# Control devices: keypads, cards, NFC stickers, RFID readers, buttons, door locks

[Deutsch](../bedienteile.md) | **English**

**System settings → Control devices.** Any number of control devices, each for one **area** or
for **all areas**. Identification always uses the **users' credentials** (PIN, RFID card, lock
ID): rights, validity, lockout after wrong entries and duress PIN apply as on the alarm panel.
"Changed by" shows e.g. "Anna (Keypad hallway)".

| Control device | Credential | Typical for |
|---|---|---|
| [Keypad](#keypad-zigbee2mqtt) | PIN and/or RFID card + key | wall next to the front door |
| [NFC sticker](#nfc-sticker-companion-app) | your own phone (Home Assistant app) | residents with the app |
| [RFID reader](#rfid-reader) | RFID card, no key | hold up the card and done |
| [Fingerprint reader](#fingerprint-reader-esphome) | stored finger (like a card) | place a finger, e.g. in the hallway |
| [Button](#button) | **none** – so it only arms | button in the hallway: press, leave |
| [Door lock](#door-lock-eg-nuki) | who unlocked (Nuki user, keypad code …) | unlocking = disarmed |

## Keypad (Zigbee2MQTT)

For alarm keypads according to the Zigbee standard for control devices (IAS ACE) – e.g.
frient/Develco KEPZB-110 and KEYZB-110, Linkind, Centralite, Heiman. Requires Zigbee2MQTT and the
MQTT integration in Home Assistant. ZHA and Z-Wave keypads are planned.

**Setting up:**

1. Pair the keypad in Zigbee2MQTT and give it a sensible name, e.g. "Keypad". The name is part of
   the MQTT topic.
2. **System settings → Control devices → Add keypad:**

| Setting | Meaning |
|---|---|
| Name | e.g. "Keypad hallway" – appears in "changed by", e.g. "Anna (Keypad hallway)" |
| Area | one area or all |
| MQTT topic | base topic + device name in Zigbee2MQTT, e.g. `zigbee2mqtt/Keypad` – written exactly as in Zigbee2MQTT (upper/lower case, hyphens), without `/set` |
| Keys "Day", "Night", "All" | one alarm profile each for **arming**, e.g. Day → "Home", Night → "Night", All → "Away"; keys without a profile answer "not ready". The keypad's own disarm key disarms – do not create a profile for it |
| Login | **PIN or card** or **card and PIN** (both credentials of the same user within 30 s; the first is acknowledged with "not ready") |
| Emergency key | **off**, **silent** (critical push message) or **alarm** (additionally an instant alarm – disarmed with the sirens under "Always active", armed with those of the active profile) |

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

Where the keypad should hang so that you reach it during the entry delay is shown by the
measurement ["Door open to disarmed"](observations.md#door-open-to-disarmed).

## Learning cards

RFID cards and fobs belong to the **users** (field "RFID cards and lock IDs", any number per
user). IDs of [door locks](#door-lock-eg-nuki) are learned the same way.

1. All areas disarmed.
2. Hold the new card to the keypad and press **Disarm** (or hold it to the reader). Hauswacht
   rejects it but remembers it.
3. Within the **learning time** (default 5 minutes): edit user → "RFID cards and lock IDs" → the
   card is listed as "new, read at Keypad at 18:04" → select it, save.
4. Hauswacht then asks for the **names of the cards** – e.g. "key ring". Leaving it empty is fine
   too.

### Naming cards – and deleting a lost card

If a user has cards or lock IDs, the form **"Names of the cards"** follows after saving their
settings: one field per card, labelled with its ID. An empty field means: no name. The same goes
for fingers at the [fingerprint reader](#fingerprint-reader-esphome) ("right thumb") and lock IDs
("Nuki app").

With names

- the user dialog shows **"key ring (04A1B2C3)"** instead of just the number,
- the logbook, the alarm panel ("changed by") and messages show **which** card was used:
  "Christian · key ring (Keypad hallway)",
- the [system overview](overview.md) shows "key ring …B2C3".

**Example – card lost:** Christian has two tags, "key ring" and "wallet". The wallet is gone. Edit
user → Christian → in the field "RFID cards and lock IDs" click the ✕ at **"wallet (…)"** → save →
simply confirm the next form (names). From now on the card switches nothing, its name is deleted
too. Whoever finds it and holds it up is rejected as an unknown card.

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
3. **Assign the finger to the user** like a [card](#learning-cards): everything disarmed, place
   the finger, then edit user → "RFID cards and lock IDs" → select "FINGER1 (new, read at …)",
   save. Or type `FINGER1`.

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
2. **Unlock once** with the app, the keypad code or the fingerprint.
3. Within the learning time: edit user → "RFID cards and lock IDs" → there you find e.g. "Nuki
   user 52653 (new, read at Front door lock at 18:04)" → select it, save.

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
- **Door lock:** whoever has the phone with the Nuki app **and** its access disarms by unlocking –
  just as they can open the door. Lost phone: block the access in the Nuki app **and** remove the
  ID from the user.
- **Buttons:** only arm; they are no credential.
