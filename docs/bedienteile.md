# Bedienteile: Keypads, Karten, NFC-Aufkleber, RFID-Leser, Taster, Türschlösser

**Deutsch** | [English](en/control-devices.md)

**Systemeinstellungen → Bedienteile.** Beliebig viele Bedienteile, jedes für einen **Bereich**
oder für **alle Bereiche**. Ausgewiesen wird immer mit den **Ausweisen der Benutzer** (PIN,
RFID-Karte, Schloss-Kennung): Rechte, Gültigkeit, Sperre nach falschen Eingaben und Bedrohungs-PIN gelten wie am
Bedienfeld. „Geändert von“ zeigt z. B. „Anna (Keypad Flur)“.

| Bedienteil | Ausweis | Typisch für |
|---|---|---|
| [Keypad](#keypad-zigbee2mqtt) | PIN und/oder RFID-Karte + Taste | Wand neben der Haustür |
| [NFC-Aufkleber](#nfc-aufkleber-companion-app) | das eigene Handy (Home-Assistant-App) | Bewohner mit App |
| [RFID-Leser](#rfid-leser) | RFID-Karte, ohne Taste | Karte vorhalten und fertig |
| [Fingerabdruck-Leser](#fingerabdruck-leser-esphome) | gespeicherter Finger (wie eine Karte) | Finger auflegen, z. B. im Flur |
| [Taster](#taster) | **keiner** – schaltet deshalb nur scharf | Taster im Hausflur: drücken, rausgehen |
| [Türschloss](#türschloss-z-b-nuki) | wer aufgeschlossen hat (Nuki-Benutzer, Keypad-Code …) | Aufschließen = unscharf |

## Keypad (Zigbee2MQTT)

Für Alarm-Keypads nach dem Zigbee-Standard für Bedienteile (IAS ACE) – z. B. frient/Develco
KEPZB-110 und KEYZB-110, Linkind, Centralite, Heiman. Voraussetzung: Zigbee2MQTT und die
MQTT-Integration in Home Assistant. ZHA- und Z-Wave-Keypads sind geplant.

**Einrichten:**

1. Keypad in Zigbee2MQTT anlernen und sinnvoll benennen, z. B. „Keypad“. Der Name ist Teil des
   MQTT-Topics.
2. **Systemeinstellungen → Bedienteile → Keypad hinzufügen:**

| Einstellung | Bedeutung |
|---|---|
| Name | z. B. „Keypad Flur“ – erscheint in „geändert von“, etwa „Anna (Keypad Flur)“ |
| Bereich | ein Bereich oder alle |
| Keypad-Gerät | das Keypad aus der Liste (Geräte von Zigbee2MQTT bzw. MQTT). Daraus bildet Hauswacht das MQTT-Topic selbst: `zigbee2mqtt/<Name in Zigbee2MQTT>`, z. B. `zigbee2mqtt/Alarm-Tastatur` |
| MQTT-Topic (nur für Experten) | **leer lassen** = automatisch aus dem Keypad-Gerät. Nur nötig, wenn in Zigbee2MQTT ein anderes Basis-Topic als `zigbee2mqtt` eingestellt ist oder das Gerät nicht in der Liste auftaucht. Dann: Basis-Topic + Gerätename, genau wie in Zigbee2MQTT geschrieben (Groß-/Kleinschreibung, Bindestriche), ohne `/set`. Ein eingetragenes Topic hat Vorrang |
| Tasten „Tag“, „Nacht“, „Alle“ | je ein Alarmprofil zum **Scharfschalten**, z. B. Tag → „Zuhause“, Nacht → „Nacht“, Alle → „Abwesend“; Tasten ohne Profil antworten „nicht bereit“. Beim frient-Keypad: **Tag = 🏠 Haus**, **Nacht = 🌙 Mond**, **Alle = 🔒 Schloss**. Unscharf schaltet die eigene Taste 🔓 (offenes Schloss) – kein Profil dafür anlegen. Tasten mehrfach belegen: [Aktions-Codes](#aktions-codes) |
| Anmeldung | **PIN oder Karte** oder **Karte und PIN** (beide Ausweise desselben Benutzers innerhalb von 30 s; der erste wird mit „nicht bereit“ quittiert) |
| Notruf-Taste | **aus** (Standard – dann passiert beim Drücken von SOS nichts Sichtbares), **still** (wichtige Push-Nachricht) oder **Alarm** (zusätzlich sofortiger Alarm – unscharf mit den Sirenen unter „Immer aktiv“, scharf mit denen des aktiven Profils) |

**Keypad in Zigbee2MQTT umbenannt?** Dann ändert sich auch sein MQTT-Topic. Keypad in Hauswacht
einmal bearbeiten und absenden – das Topic wird aus dem neuen Namen gebildet. Steht ein eigenes
Topic im Expertenfeld, dieses anpassen.

3. Den **Sabotagekontakt** des Keypads (`binary_sensor.<keypad>_tamper`) in eine Meldergruppe
   aufnehmen (Typ Manipulation) – sinnvollerweise erst, wenn es fest an der Wand hängt, und
   dann in den Profilen auswählen.
4. Optional: Batterie in [Battery Notes](https://github.com/andrew-codechimp/HA-Battery-Notes)
   eintragen (frient KEPZB-110: 4 × AA).

**Bedienen:** erst **PIN tippen oder Karte vorhalten**, dann die **Taste** drücken (Unscharf,
Tag, Nacht, Alle). Das Keypad schickt Code bzw. Kartennummer nur zusammen mit einem
Tastendruck – Karte vorhalten allein schaltet nichts (dafür gibt es den
[RFID-Leser](#rfid-leser)).

**Rückmeldung:** Hauswacht antwortet auf jeden Tastendruck (gültig, ungültiger Ausweis, nicht
bereit – z. B. Fenster offen –, schon unscharf) und zeigt danach laufend den Zustand an:
Ausgangs- und Eingangsverzögerung, scharf (Tag/Nacht/alle), Alarm. Dafür sendet Hauswacht an
`<Topic>/set` (`arm_mode`) – **nur** Zustandsanzeigen an eingerichtete Keypads; ein Test stellt
sicher, dass Hauswacht sonst nirgends hin sendet.

**PINs nicht im Verlauf:** Zigbee2MQTT legt für den am Keypad getippten Code eine eigene
Entität an, z. B. `sensor.keypad_flur_action_code`. Home Assistant speichert sie im Verlauf –
also jede PIN im Klartext, auch in Backups. Hauswacht braucht sie nicht und **deaktiviert sie
automatisch**, sobald das Keypad eingerichtet ist (auch wenn sie erst später entsteht). Du
bekommst dazu einmal eine Nachricht. Schaltest du sie bewusst wieder ein (Einstellungen →
Entitäten), lässt Hauswacht sie in Ruhe. Bereits gespeicherte Einträge löscht Home Assistant mit
dem normalen Aufräumen des Verlaufs (Standard: 10 Tage) – sofort geht es mit der Aktion
„Recorder: Entitäten bereinigen“ für diese Entität.

Wo das Keypad hängen sollte, damit man es in der Eingangsverzögerung erreicht, hilft die
Messung [„Tür auf bis unscharf“](beobachtung.md#tür-auf-bis-unscharf).

## Aktions-Codes

**Systemeinstellungen → Bedienteile → Aktions-Codes.** Ein Aktions-Code ist ein **Code plus eine
Funktionstaste** am Keypad, z. B. **7777 + 🏠 Haus**. Er löst eine festgelegte Aktion aus – so
lassen sich die Tasten des Keypads mehrfach belegen:

```
➕ Neuer Aktions-Code
Außenlicht – 7777 + 🏠 Haus · alle Keypads → Ereignis
Licht aus – 7777 + 🌙 Nacht · alle Keypads → Ereignis
Garagenlicht – 42 + 🔒 Schloss · Keypad Flur → Ereignis
Notruf – 9111 + 🌙 Nacht · alle Keypads → stiller Notruf
```

| Feld | Bedeutung |
|---|---|
| Name | z. B. „Außenlicht“ – erscheint im Logbuch und ist bei „Ereignis“ der Ereignistyp |
| Code | **2–8 Ziffern**. Darf keinem PIN, Bedrohungs-PIN oder Master-PIN gleichen (umgekehrt genauso) |
| Taste | 🏠 Haus, 🌙 Nacht, 🔒 Schloss oder 🔓 offenes Schloss. SOS geht nicht – sie schickt keinen Code mit |
| Keypad | alle oder ein bestimmtes |
| Aktion | **Ereignis** für eine eigene Automation, **Scharf schalten** mit einem Profil oder **stiller Notruf** |

Derselbe Code darf mit verschiedenen Tasten verschiedene Aktionen haben. Code + Taste darf es
aber nur einmal geben. Einen Eintrag antippen: ändern oder löschen.

**Am Keypad:** Code tippen, dann die Taste drücken. Das Keypad bekommt eine positive Rückmeldung
und zeigt danach wieder den Zustand. Ein Aktions-Code zählt **nie als Fehlversuch** – während
einer [PIN-Sperre](benutzer.md#sperre-nach-falschen-eingaben) ist er aber ebenfalls gesperrt.
Ist ein Code mit einer Taste als Aktions-Code eingerichtet, hat er Vorrang vor der normalen
Belegung der Taste.

**Kein Ausweis:** Ein Aktions-Code gehört keiner Person und ist nicht geheim – wer ihn kennt oder
errät, löst die Aktion aus. Deshalb kann er **nie unscharf schalten**, und du solltest nichts
Sicherheitskritisches damit auslösen (z. B. Türöffner, Garagentor).

### Aktion „Ereignis“: eigene Automation

Sobald es einen Aktions-Code mit „Ereignis“ gibt, hat Hauswacht die Entität
**`event.hauswacht_aktions_code`** („Hauswacht Aktions-Code“; bei englischer Sprache
`event.hauswacht_action_code`). Bei jedem Aktions-Code meldet sie ein Ereignis mit dem **Namen**
des Codes als Ereignistyp. Hauswacht selbst schaltet dabei nichts – was passiert, bestimmt deine
Automation.

**Beispiel – 7777 + Haus schaltet das Außenlicht für 5 Minuten ein:**

1. Aktions-Code anlegen: Name „Außenlicht“, Code `7777`, Taste 🏠 Haus, Aktion Ereignis.
2. Neue Automation. Auslöser: Zustand von „Hauswacht Aktions-Code“ (jedes Ereignis ändert ihn).
   Bedingung: Attribut „Ereignistyp“ ist „Außenlicht“. In YAML:

```yaml
triggers:
  - trigger: state
    entity_id: event.hauswacht_aktions_code
conditions:
  - condition: state
    entity_id: event.hauswacht_aktions_code
    attribute: event_type
    state: Außenlicht
actions:
  - action: light.turn_on
    target:
      entity_id: light.aussen
  - delay: "00:05:00"
  - action: light.turn_off
    target:
      entity_id: light.aussen
```

Warum nicht direkt „Attribut ändert sich auf Außenlicht“? Wird derselbe Code zweimal
hintereinander getippt, bleibt der Ereignistyp gleich – die Automation liefe dann nur beim ersten
Mal. Der Zustand (Zeitpunkt des letzten Ereignisses) ändert sich dagegen jedes Mal.

Die Entität hat außerdem die Attribute `keypad` (welches Keypad) und `test` (Testmodus an).

### Weitere Beispiele

**Ausprobieren, was ankommt:** Entwicklerwerkzeuge → Ereignisse → bei „Auf Ereignisse hören“
`hauswacht_event` eintragen → „Zuhören starten“ → am Keypad den Code tippen und die Taste
drücken. Es erscheint z. B.:

```yaml
event_type: hauswacht_event
data:
  type: ActionCode
  name: Außenlicht
  action: event
  control: Keypad Flur
  test: false
```

Dieses Ereignis `hauswacht_event` kommt bei **jedem** Aktions-Code – auch bei „Scharf schalten“
und „stiller Notruf“. Als Auslöser ist es oft einfacher als die Entität, weil ein einziger
Auslöser genügt:

**A – Außenlicht mit nur einem Auslöser** (gleiche Wirkung wie oben):

```yaml
alias: Außenlicht per Keypad
triggers:
  - trigger: event
    event_type: hauswacht_event
    event_data:
      type: ActionCode
      name: Außenlicht
actions:
  - action: light.turn_on
    target:
      entity_id: light.aussen
  - delay: "00:05:00"
  - action: light.turn_off
    target:
      entity_id: light.aussen
mode: restart
```

Im Automations-Editor: Auslöser → **Manuelles Ereignis empfangen** → Ereignistyp
`hauswacht_event`, Ereignisdaten `type: ActionCode` und `name: Außenlicht`. `mode: restart`
sorgt dafür, dass ein erneuter Code die 5 Minuten neu startet.

**B – Ein Code, zwei Tasten: Licht an und aus.** Zwei Aktions-Codes anlegen: „Licht an“
(`7777` + 🏠 Haus) und „Licht aus“ (`7777` + 🌙 Nacht), beide mit Aktion Ereignis. Eine
Automation für beide:

```yaml
alias: Wohnzimmerlicht per Keypad
triggers:
  - trigger: event
    event_type: hauswacht_event
    event_data:
      type: ActionCode
      name: Licht an
    id: an
  - trigger: event
    event_type: hauswacht_event
    event_data:
      type: ActionCode
      name: Licht aus
    id: aus
actions:
  - choose:
      - conditions:
          - condition: trigger
            id: an
        sequence:
          - action: light.turn_on
            target:
              entity_id: light.wohnzimmer
      - conditions:
          - condition: trigger
            id: aus
        sequence:
          - action: light.turn_off
            target:
              entity_id: light.wohnzimmer
```

**C – Scharf schalten und gleichzeitig etwas anderes tun.** Aktions-Code „Gute Nacht“ (`11` +
🔒 Schloss) mit Aktion **Scharf schalten → Nacht**. Hauswacht schaltet scharf; diese Automation
fährt zusätzlich die Rollläden herunter:

```yaml
alias: Gute Nacht per Keypad
triggers:
  - trigger: event
    event_type: hauswacht_event
    event_data:
      type: ActionCode
      name: Gute Nacht
actions:
  - action: cover.close_cover
    target:
      area_id: wohnzimmer
```

**Testmodus ausnehmen:** Soll im [Testmodus](testmodus.md) nichts passieren, diese Bedingung
ergänzen:

```yaml
conditions:
  - condition: template
    value_template: "{{ not trigger.event.data.test }}"
```

### Aktion „Scharf schalten“ und „stiller Notruf“

- **Scharf schalten:** schaltet das gewählte Profil scharf, genau wie die Taste mit Profil – mit
  Prüfung offener Melder und Ausgangsverzögerung. Im Logbuch steht z. B. „Aktions-Code ‚Nacht per
  Code‘ (Keypad Flur)“. Das gilt auch, wenn unter PIN-Regeln „PIN beim Scharfschalten“ an ist:
  Wer einen Aktions-Code zum Scharfschalten anlegt, will genau das.
- **Stiller Notruf:** wichtige Push-Nachricht „Notruf am Keypad Flur“ an die Alarm-Empfänger –
  wie die SOS-Taste auf „still“, aber unauffällig über eine normale Taste. Keine Sirene, keine
  Anzeige am Keypad.

## Karten anlernen

RFID-Karten, Anhänger, Finger am [Fingerabdruck-Leser](#fingerabdruck-leser-esphome) und
Kennungen von [Türschlössern](#türschloss-z-b-nuki) verwaltest du an einer Stelle:
**Systemeinstellungen → Benutzer und PINs → Karten und Anhänger.** Im Folgenden heißt all das
einfach „Karte“.

### Die Kartenliste

Die Liste zeigt jede Karte mit Name, Nummer, Besitzer und wann sie zuletzt geschaltet hat:

```
➕ Neue Karte anlernen (hinhalten)
⌨️ Kartennummer eintippen
🟢 Schlüsselbund (04A1B2C3) – Christian · zuletzt 07:12
🟢 Geldbörse (0011223344) – Christian · zuletzt 02.11.2026
⏸️ Ersatzkarte (A1B2C3D4E5) – Anna · deaktiviert
🟢 Nuki-App (Nuki-Benutzer 4711) – Anna · noch nie benutzt
```

🟢 = aktiv, ⏸️ = deaktiviert. „Zuletzt“ zeigt bei heute die Uhrzeit, sonst das Datum.

### Neue Karte anlernen

1. Alle Bereiche unscharf.
2. **Karten und Anhänger → ➕ Neue Karte anlernen (hinhalten).** Der Dialog zeigt: *„Halte die
   neue Karte jetzt an ein Keypad (und drücke Unscharf) oder an einen Leser“*. Bei einem
   Türschloss: einmal mit der neuen Kennung aufschließen.
3. **Sobald die Karte gelesen ist, geht es sofort weiter:** „✅ Karte erkannt“. Gib einen
   **Namen** ein (z. B. „Schlüsselbund“), wähle den **Benutzer**, speichern.

Am frient-Keypad reicht Hinhalten allein nicht – erst mit **Unscharf** schickt es die Nummer.
Kommt 2 Minuten lang keine Karte, geht der Dialog ohne Karte weiter.

Es zählt nur eine Karte, die **während** des Dialogs gelesen wird. Eine Karte aus einem früheren,
abgebrochenen Versuch wird nicht vorausgewählt.

**⌨️ Kartennummer eintippen:** ohne Warten. Hier stehen die zuletzt gelesenen unbekannten Karten
(innerhalb der Anlernzeit) als „neu, gelesen an Keypad um 18:04“ zur Auswahl, oder du tippst die
Nummer ein.

**Beispiel:** Anna bekommt einen neuen Anhänger. Karten und Anhänger → Neue Karte anlernen →
Anhänger ans Keypad im Flur halten, Unscharf drücken → „✅ Karte erkannt: 04C3D2E1“ → Name
„Schlüsselbund“, Benutzer „Anna“ → Absenden. Ab jetzt schaltet Annas Anhänger, und im Logbuch
steht „Anna · Schlüsselbund (Keypad Flur)“.

### Karte bearbeiten, deaktivieren, löschen

In der Liste eine Karte antippen:

| Feld | Bedeutung |
|---|---|
| Name der Karte | z. B. „Schlüsselbund“, „Geldbörse“, „Daumen rechts“, „Nuki-App“. Leer = ohne Namen |
| Gehört | Benutzer – hier gibst du eine Karte auch an jemand anderen weiter |
| Aktiv | aus = **deaktiviert**: die Karte schaltet nichts mehr, bleibt aber bekannt |
| Karte löschen | endgültig; danach wird sie wie eine unbekannte Karte abgelehnt |

**Deaktivierte Karte wird benutzt:** Sie schaltet nichts, am Keypad erscheint „ungültig“, und es
zählt als Fehlversuch für die [Sperre](benutzer.md#sperre-nach-falschen-eingaben). Du bekommst
eine Nachricht: *„Die deaktivierte Karte ‚Geldbörse‘ (Christian) wurde an Keypad Flur benutzt.“*
Bei einer deaktivierten Schloss-Kennung schaltet Hauswacht ebenfalls nichts und meldet es (ein
Türschloss zählt nicht als Fehlversuch).

**Beispiel – Geldbörse weg:** Christian vermisst seine Geldbörse mit dem Anhänger darin. Karten
und Anhänger → „Geldbörse (0011223344) – Christian“ → **Aktiv aus** → Absenden. Taucht die
Geldbörse wieder auf: Aktiv wieder an. Bleibt sie verschwunden: **Karte löschen**. Versucht in
der Zwischenzeit jemand, mit dem Anhänger unscharf zu schalten, weißt du es sofort.

Mit Namen zeigen außerdem Logbuch, Bedienfeld („Geändert von“) und Nachrichten, **welche** Karte
benutzt wurde – „Christian · Schlüsselbund (Keypad Flur)“ – und die
[Systemübersicht](uebersicht.md) zeigt „Schlüsselbund …B2C3“ (deaktivierte mit ⏸).

### Regeln beim Anlernen

- Die Anlernzeit ist einstellbar unter **Bedienteile → Anlernen neuer Karten** (1–60 Minuten,
  0 = Anlernen aus). Danach wird die Karte vergessen; wer zu spät speichert, bekommt einen
  Hinweis und hält die Karte noch einmal hin.
- Unbekannte Karten zählen nicht als Fehlversuch für die [Sperre](benutzer.md#sperre-nach-falschen-eingaben).
- Kartennummern lassen sich auch eintippen (z. B. `041B4932E82880`; Groß-/Kleinschreibung und
  Trennzeichen egal). Codes mit 4–8 Ziffern könnten PINs sein und werden nie zum Anlernen
  angeboten – solche Karten-IDs eintippen.
- Eine Karte gehört genau einem Benutzer.

**Welche Karten gehen?** Das frient-Keypad liest 13,56-MHz-Karten nach ISO 14443 A (z. B. MIFARE
Classic, MIFARE DESFire, NTAG-Anhänger, viele Firmenausweise) und meldet deren feste Nummer
(UID).

**Nicht geeignet sind Zufallsnummern:** Handys und manche Ausweise im Datenschutz-Modus melden
bei jedem Lesen eine **andere** Nummer – erkennbar an 4 Byte, die mit `08` beginnen
(z. B. `+08837CF0`). Hauswacht bietet sie nicht zum Anlernen an, lehnt sie beim Speichern ab und
zeigt im Benutzer-Dialog einen Hinweis.

## NFC-Aufkleber (Companion App)

Ein NFC-Aufkleber an der Tür, gescannt mit der Home-Assistant-App. Der Aufkleber sagt nur **wo
und was** – ausgewiesen wird mit dem **Handy**: Das angemeldete Home-Assistant-Konto muss einem
berechtigten Hauswacht-Benutzer zugeordnet sein. Ein kopierter Aufkleber allein nützt also
nichts.

| Einstellung | Bedeutung |
|---|---|
| Aufkleber-ID | unter Einstellungen → Bereiche, Labels & Zonen → Tags (nach dem ersten Scannen) |
| Aktion | unscharf schalten, scharf schalten (Profil) oder umschalten (scharf ↔ unscharf) |

Das Handy muss entsperrt sein. Kein Tastendruck nötig.

## RFID-Leser

Ein fester Leser, der das Home-Assistant-Ereignis „Tag gescannt“ auslöst – z. B. ein ESP32 mit
PN532 oder RC522 über ESPHome. Anders als beim Keypad reicht **Karte vorhalten**.

| Einstellung | Bedeutung |
|---|---|
| Geräte-ID | steht im Ereignis „Tag gescannt“ (`device_id`) |
| Aktion | unscharf schalten, scharf schalten (Profil) oder umschalten |
| Anmeldung | **Karte** oder **Karte und PIN** (danach innerhalb von 30 s PIN desselben Benutzers an einem Keypad im selben Bereich) |

„Umschalten“ ist bequem, kann aber auch versehentlich scharf schalten. Einfache 125-kHz-Karten
sind leicht kopierbar – besser 13,56-MHz-Karten oder NFC per Handy.

### Fingerabdruck-Leser (ESPHome)

Ein Fingerabdruck-Sensor an einem ESP32 meldet den erkannten Finger wie eine Karte. In Hauswacht
ist er deshalb einfach ein **RFID-Leser** – ein Finger ist ein Ausweis wie eine Karte.

**Was du brauchst:**

| Teil | Beispiel | Preis etwa |
|---|---|---|
| Mikrocontroller | ESP32-Board (z. B. ESP32-DevKitC) | 5–10 € |
| Fingerabdruck-Sensor | **R503** (rund, mit LED-Ring; auch R307, ZFM-20) | 15–25 € |
| Software | [ESPHome](https://esphome.io/components/fingerprint_grow.html) (Komponente `fingerprint_grow`) | kostenlos |

Verkabelung: 3,3 V und GND vom ESP32; TX des Sensors an den RX-Pin des ESP32, RX des Sensors
an den TX-Pin; den WAKEUP-Draht an einen freien Pin (`sensing_pin`), damit der Sensor ein
Auflegen sofort erkennt.

**ESPHome-Konfiguration** (Gerät hier `fingerabdruck-flur`, Pins anpassen):

```yaml
esphome:
  name: fingerabdruck-flur

esp32:
  board: esp32dev

uart:
  rx_pin: GPIO16      # an TX des Sensors
  tx_pin: GPIO17      # an RX des Sensors
  baud_rate: 57600

fingerprint_grow:
  sensing_pin: GPIO4  # WAKEUP des Sensors
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
    - action: finger_anlernen
      variables:
        finger_id: int
      then:
        - fingerprint_grow.enroll:
            finger_id: !lambda 'return finger_id;'
            num_scans: 2
    - action: finger_loeschen
      variables:
        finger_id: int
      then:
        - fingerprint_grow.delete:
            finger_id: !lambda 'return finger_id;'

sensor:
  - platform: fingerprint_grow
    fingerprint_count:
      name: "Gespeicherte Finger"
    last_finger_id:
      name: "Letzter Finger"
    last_confidence:
      name: "Letzte Übereinstimmung"
```

**Einrichten:**

1. **Finger im Sensor speichern:** Entwicklerwerkzeuge → Aktionen →
   `esphome.fingerabdruck_flur_finger_anlernen` mit `finger_id: 1` → zweimal denselben Finger
   auflegen. Für jeden Finger eine eigene Nummer (Platz 1, 2, 3 …). Am besten eine kleine Liste
   führen: 1 = Anna, rechter Zeigefinger; 2 = Anna, linker Zeigefinger; 3 = Ben …
2. **In Hauswacht:** Systemeinstellungen → Bedienteile → **RFID-/NFC-Leser hinzufügen** →
   Lesegerät „fingerabdruck-flur“ → Aktion z. B. „unscharf schalten“.
3. **Finger dem Benutzer zuordnen** wie eine [Karte](#neue-karte-anlernen): alles unscharf,
   Benutzer und PINs → Karten und Anhänger → Neue Karte anlernen (hinhalten) → Finger auflegen → „✅ Karte
   erkannt: FINGER1“ → Name „Zeigefinger rechts“, Benutzer „Anna“ → speichern. Oder `FINGER1`
   eintippen.

Gut zu wissen:

- **Kommt nichts an?** Unter Entwicklerwerkzeuge → Ereignisse `tag_scanned` anhören und einen
  Finger auflegen. Bleibt es still: Einstellungen → Geräte & Dienste → ESPHome → das Gerät →
  Konfigurieren → **„Dem Gerät erlauben, Home-Assistant-Aktionen auszuführen“** einschalten.
- Die Fingerabdrücke selbst bleiben **im Sensor**. Home Assistant und Hauswacht sehen nur die
  Nummer des Platzes („FINGER1“).
- Ein **unbekannter Finger** schickt nichts – er zählt deshalb auch nicht als Fehlversuch.
- `confidence > 50` ist die Mindest-Übereinstimmung; höher = weniger Fehlerkennungen, aber
  öfter „nicht erkannt“. Zusätzlich lässt sich am Sensor `security_level` (1–5) einstellen.
- Die LED zeigt nur, ob der **Sensor** den Finger erkannt hat – nicht, ob Hauswacht unscharf
  geschaltet hat (z. B. fehlendes Recht oder Sperre). Das zeigen Keypad, Alarmkarte und Logbuch.
- **Mehr Sicherheit:** Anmeldung „Karte und PIN“ – nach dem Finger innerhalb von 30 s den PIN am
  Keypad.
- **Sicherheit des Lesers:** Wer den ESP32 oder sein WLAN übernimmt, kann jede Nummer schicken.
  Den Leser deshalb **innen** anbringen (z. B. im Flur in Reichweite der Eingangsverzögerung),
  ESPHome mit API-Schlüssel und Passwort betreiben und das Gehäuse gegen Öffnen sichern. Außen an
  der Tür ist ein Schloss mit eigenem Fingerabdruck-Leser (z. B. Nuki Keypad 2.0, siehe
  [Türschloss](#türschloss-z-b-nuki)) die robustere Wahl.
- Ein **verlorener oder verletzter Finger**: den Platz im Sensor löschen
  (`esphome.fingerabdruck_flur_finger_loeschen`) und die Kennung beim Benutzer entfernen.

> Diese Anleitung folgt der ESPHome-Dokumentation; mit echter Hardware erprobt ist sie bei
> Hauswacht noch nicht. Rückmeldungen gern als [Issue](https://github.com/schlusenbaum/hauswacht/issues).


## Taster

Ein Taster – z. B. ein Zigbee-Taster im Hausflur – schaltet ein Alarmprofil **scharf**, mit der
Ausgangsverzögerung des Profils. Drücken, rausgehen, fertig.

> Ein Taster weist **niemanden** aus: Wer davorsteht, ist unbekannt. Deshalb schaltet er **nur
> scharf** – nie unscharf, und er beendet nie einen Alarm.

**Einrichten:** Systemeinstellungen → Bedienteile → **Taster hinzufügen**.

1. Name, Bereich und den **Taster** wählen:
   - eine **Ereignis-Entität** (`event.…`) – so liefern Zigbee2MQTT (neuere Versionen), Hue,
     Shelly und Matter ihre Taster, oder
   - einen **Aktions-Sensor** (`sensor.…_action`), wie ihn ältere Zigbee2MQTT-Versionen anlegen.
2. Im zweiten Schritt legst du fest, welche **Druckart** welches Profil schaltet:
   - Bei einer Ereignis-Entität zeigt Hauswacht die Druckarten des Geräts selbst an (z. B.
     `single`, `double`, `long`). Leer lassen = diese Druckart tut nichts.
   - Bei einem Aktions-Sensor trägst du den **Wert** ein, den der Sensor beim Drücken annimmt.
     So findest du ihn: Entwicklerwerkzeuge → Zustände → Sensor suchen → Taster drücken → der
     Wert erscheint kurz (z. B. `single`, `double`, `hold`).

**Beispiel:** Taster im Flur, einfach → „Abwesend“, doppelt → „Nacht“. Im Logbuch steht
„geändert von: Taster Flur“.

Gut zu wissen:

- Ist schon ein Profil scharf, tut der Taster nichts – er schaltet nie über ein anderes Profil
  hinweg um.
- Sind Melder offen, gilt die Einstellung des Profils (z. B. „verweigern“) – dann kommt die
  übliche Meldung „nicht scharf geschaltet“.
- Verlangen die PIN-Regeln einen **PIN zum Scharfschalten**, schaltet der Taster **nicht** –
  er kann keinen PIN eingeben. Hauswacht schickt dann eine Systemmeldung.
- Kommt der Taster nach einem Funkausfall wieder, zählt das nicht als Drücken.
- Ein Taster **außen** an der Tür ist nicht verboten, aber dann kann jeder Vorbeigehende scharf
  schalten (und wer drinnen ist, löst später Alarm aus). Besser innen anbringen.

## Türschloss (z. B. Nuki)

Ein elektronisches Türschloss schaltet **unscharf, wenn ein bekannter Benutzer aufschließt** –
mit dessen Rechten je Bereich. Im Logbuch steht z. B. „Anna (Haustür-Schloss)“. Optional
schaltet **Abschließen von außen** ein Profil scharf.

Dafür muss das Schloss sagen, **wer** aufgeschlossen hat. Das bloße Öffnen der Tür oder
„aufgeschlossen“ ohne Person reicht nie.

> Hauswacht **liest nur mit** und schaltet das Schloss selbst nie.

### Was Hauswacht verlangt

Hauswacht schaltet nur unscharf, wenn **beides** zusammenkommt, höchstens 30 Sekunden
auseinander:

1. eine **Kennung** vom Schloss, die einem Hauswacht-Benutzer gehört (z. B. sein
   Nuki-App-Zugang oder sein Keypad-Code), und
2. das Schloss wechselt in Home Assistant wirklich auf **„aufgeschlossen“** bzw. „offen“.

Warum beides? Manche Nuki-Modelle melden auch einen **falsch** eingetippten Keypad-Code als
Aufschließen (ein bekannter Firmware-Fehler). Ohne tatsächliche Bewegung des Schlosses passiert
deshalb nichts.

**Nie unscharf**

| Situation | Warum |
|---|---|
| Kennung unbekannt oder fehlt | Wer es war, ist nicht klar (Hauswacht meldet das per Systemmeldung, wenn scharf) |
| Drehknauf oder Knopf am Schloss (innen) | kein Ausweis |
| Zeitsteuerung, automatisches Abschließen | keine Person |
| Aufschließen über Home Assistant, HomeKit oder MQTT | kein Ausweis an der Tür |
| Tür geht nur auf | kein Aufschließen |
| Benutzer darf nicht unscharf schalten oder ist abgelaufen | Rechte gelten wie am Bedienfeld |

### Einrichten mit Nuki über MQTT

Voraussetzung: Nuki Smart Lock (3.0 Pro, 4. oder 5. Generation) mit eingeschaltetem **MQTT**
in der Nuki-App und die MQTT-Integration in Home Assistant. Das Schloss selbst ist meist schon
über MQTT oder die Nuki-Integration als `lock.…` in Home Assistant.

1. **Systemeinstellungen → Bedienteile → Türschloss hinzufügen.**
2. Ausfüllen:

| Einstellung | Beispiel | Bedeutung |
|---|---|---|
| Name | Haustür-Schloss | erscheint im Logbuch |
| Bereich | Haus | welcher Bereich unscharf wird |
| Schloss | `lock.haustuer` | die Entität in Home Assistant |
| Quelle | Nuki über MQTT | |
| MQTT-Topic | `nuki/3A1B2C4D` | Basis-Topic des Schlosses (die Nuki-ID in Hex), **ohne** `/lockActionEvent` |
| Beim Abschließen scharf | leer oder „Abwesend“ | optional, siehe unten |

Hauswacht liest dann `nuki/3A1B2C4D/lockActionEvent`. Das Nuki schickt dort bei jeder Aktion
fünf Zahlen, z. B. `1,0,52653,0,0`:

| Stelle | Bedeutung | Beispiel |
|---|---|---|
| 1 | Aktion: 1 = aufschließen, 2 = abschließen, 3 = öffnen, 4 = Lock 'n' Go, 6 = voll abschließen | `1` |
| 2 | Auslöser: 0 = App/Bluetooth, Keypad, Fob; 2 = Knopf am Schloss; 3 = Zeitsteuerung; 6 = automatisch; 171 = HomeKit/Matter; 172 = MQTT | `0` |
| 3 | Auth-ID: wer (App-Zugang) | `52653` |
| 4 | Code-ID: welcher Keypad-Code (0 = keiner) | `0` |
| 5 | Zusatz (z. B. Fingerabdruck, Auto-Unlock) | `0` |

Hauswacht zählt nur Auslöser **0**. Aus Code-ID bzw. Auth-ID wird die Kennung, die beim
Benutzer erscheint: „Nuki-Keypad-Code 8192“ bzw. „Nuki-Benutzer 52653“ (gespeichert als
`NUKICODE8192` bzw. `NUKIAUTH52653`).

**Fingerabdruck am Nuki Keypad 2.0:** Ein Fingerabdruck kommt wie ein Keypad-Code an (eigene
Code-ID, an Stelle 5 eine `2` für „Fingerabdruck“). Er wird also genauso als „Nuki-Keypad-Code …“
angelernt – das ist der einfachste Weg zu einem Fingerabdruck an der Haustür.

### Kennungen anlernen

Wie bei [Karten](#karten-anlernen):

1. Alle Bereiche unscharf.
2. Benutzer und PINs → Karten und Anhänger → **Neue Karte anlernen (hinhalten)**.
3. Mit der App, dem Keypad-Code oder dem Fingerabdruck **einmal aufschließen** – der Dialog
   erkennt die Kennung sofort → Name z. B. „Nuki-App“, Benutzer wählen → speichern.

Schon vorher aufgeschlossen? Dann „Kartennummer eintippen“: Dort steht die Kennung als
„Nuki-Benutzer 52653 (neu, gelesen an Haustür-Schloss um 18:04)“ zur Auswahl.

Am besten jede Person einzeln anlernen, damit klar ist, welche Kennung zu wem gehört. Jeder
Keypad-Code und jeder App-Zugang ist eine eigene Kennung; ein Benutzer kann mehrere haben.

### Abschließen = scharf (optional)

Ist ein Profil eingetragen, schaltet **Abschließen von außen** durch einen bekannten Benutzer
mit Recht zum Scharfschalten dieses Profil scharf – aber nur, wenn alles unscharf ist.
Automatisches Abschließen, Zeitsteuerung und der Knopf innen zählen nicht.

> Achtung: „Von außen“ heißt für Nuki nur „per App, Keypad oder Fob“. Wer abends **im Bett per
> App** abschließt, schaltet damit ebenfalls scharf. Für die Haustür daher eher ein Profil wie
> „Abwesend“ wählen und die App dafür nicht von innen nutzen – oder das Feld leer lassen.

### Andere Schlösser (allgemeine Quelle)

Für Schlösser, die den Benutzer als **Sensor** oder **Ereignis** in Home Assistant zeigen
(z. B. einen Sensor „zuletzt geöffnet von“ oder ein Ereignis mit dem Benutzernamen):

| Einstellung | Beispiel |
|---|---|
| Quelle | Allgemein |
| Sensor oder Ereignis mit der Kennung | `sensor.haustuer_benutzer` |

Ändert sich der Wert (bzw. kommt ein Ereignis) und schließt das Schloss innerhalb von
30 Sekunden auf, gilt der Wert als Kennung – z. B. „Anna“ wird zu `LOCKANNA`. Angelernt wird
wie oben.

Wichtig: Der Sensor darf seinen Wert **nur beim Aufschließen** ändern. Zeigt er z. B. auch
an, wer zuletzt **abgeschlossen** hat, würde das Abschließen von Anna und ein späteres
Aufschließen durch einen Unbekannten zusammengezählt, wenn beides innerhalb von 30 Sekunden
passiert.

## Sicherheit

- Eine reine Kartennummer ist kein starker Schutz: Wer sie ausliest (z. B. im Vorbeigehen), kann
  sie kopieren. Für mehr Sicherheit „Karte und PIN“ verwenden.
- Am Keypad schützt der nötige Tastendruck davor, dass eine Karte in der Jackentasche etwas
  schaltet.
- Verlorene Karte: beim Benutzer entfernen oder den Benutzer auf „Aktiv: aus“ stellen.
- Der Bedrohungs-PIN wirkt auch am Keypad.
- **Türschloss:** Wer das Handy mit der Nuki-App **und** den Zugang dazu hat, schaltet mit dem
  Aufschließen unscharf – genau wie er die Tür öffnen kann. Verlorenes Handy: in der Nuki-App
  den Zugang sperren **und** die Kennung beim Benutzer entfernen.
- **Taster:** schalten nur scharf; sie sind kein Ausweis.
