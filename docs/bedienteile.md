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
| MQTT-Topic | Basis-Topic + Gerätename in Zigbee2MQTT, z. B. `zigbee2mqtt/Keypad` – genau wie in Zigbee2MQTT geschrieben (Groß-/Kleinschreibung, Bindestriche), ohne `/set` |
| Tasten „Tag“, „Nacht“, „Alle“ | je ein Alarmprofil zum **Scharfschalten**, z. B. Tag → „Zuhause“, Nacht → „Nacht“, Alle → „Abwesend“; Tasten ohne Profil antworten „nicht bereit“. Unscharf schaltet die eigene Unscharf-Taste – kein Profil dafür anlegen |
| Anmeldung | **PIN oder Karte** oder **Karte und PIN** (beide Ausweise desselben Benutzers innerhalb von 30 s; der erste wird mit „nicht bereit“ quittiert) |
| Notruf-Taste | **aus**, **still** (wichtige Push-Nachricht) oder **Alarm** (zusätzlich sofortiger Alarm – unscharf mit den Sirenen unter „Immer aktiv“, scharf mit denen des aktiven Profils) |

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

Wo das Keypad hängen sollte, damit man es in der Eingangsverzögerung erreicht, hilft die
Messung [„Tür auf bis unscharf“](beobachtung.md#tür-auf-bis-unscharf).

## Karten anlernen

RFID-Karten und -Anhänger gehören zu den **Benutzern** (Feld „RFID-Karten und
Schloss-Kennungen“, beliebig viele je Benutzer). Kennungen von [Türschlössern](#türschloss-z-b-nuki)
lernst du genauso an.

1. Alle Bereiche unscharf.
2. Neue Karte ans Keypad halten und **Unscharf** drücken (bzw. an den Leser halten). Hauswacht
   lehnt sie ab, merkt sie sich aber.
3. Innerhalb der **Anlernzeit** (Standard 5 Minuten): Benutzer bearbeiten → „RFID-Karten und
   Schloss-Kennungen“ → die Karte steht dort als „neu, gelesen an Keypad um 18:04“ → auswählen,
   speichern.

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
3. **Finger dem Benutzer zuordnen** wie eine [Karte](#karten-anlernen): alles unscharf, Finger
   auflegen, dann Benutzer bearbeiten → „RFID-Karten und Schloss-Kennungen“ → „FINGER1 (neu,
   gelesen an …)“ auswählen, speichern. Oder `FINGER1` eintippen.

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
2. Mit der App, dem Keypad-Code oder dem Fingerabdruck **einmal aufschließen**.
3. Innerhalb der Anlernzeit: Benutzer bearbeiten → „RFID-Karten und Schloss-Kennungen“ → dort
   steht z. B. „Nuki-Benutzer 52653 (neu, gelesen an Haustür-Schloss um 18:04)“ → auswählen,
   speichern.

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
