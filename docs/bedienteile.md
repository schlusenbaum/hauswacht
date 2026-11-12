# Bedienteile: Keypads, Karten, NFC-Aufkleber, RFID-Leser

**Systemeinstellungen → Bedienteile.** Beliebig viele Bedienteile, jedes für einen **Bereich**
oder für **alle Bereiche**. Ausgewiesen wird immer mit den **Ausweisen der Benutzer** (PIN,
RFID-Karte): Rechte, Gültigkeit, Sperre nach falschen Eingaben und Bedrohungs-PIN gelten wie am
Bedienfeld. „Geändert von“ zeigt z. B. „Anna (Keypad Flur)“.

| Bedienteil | Ausweis | Typisch für |
|---|---|---|
| [Keypad](#keypad-zigbee2mqtt) | PIN und/oder RFID-Karte + Taste | Wand neben der Haustür |
| [NFC-Aufkleber](#nfc-aufkleber-companion-app) | das eigene Handy (Home-Assistant-App) | Bewohner mit App |
| [RFID-Leser](#rfid-leser) | RFID-Karte, ohne Taste | Karte vorhalten und fertig |

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
| Name | z. B. „Keypad Flur“ – erscheint in „geändert von“ |
| Bereich | ein Bereich oder alle |
| MQTT-Topic | Basis-Topic + Gerätename in Zigbee2MQTT, z. B. `zigbee2mqtt/Keypad` |
| Tasten „Tag“, „Nacht“, „Alle“ | je ein Alarmprofil; Tasten ohne Profil antworten „nicht bereit“ |
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

RFID-Karten und -Anhänger gehören zu den **Benutzern** (Feld „RFID-Karten/-Anhänger“, beliebig
viele je Benutzer).

1. Alle Bereiche unscharf.
2. Neue Karte ans Keypad halten und **Unscharf** drücken (bzw. an den Leser halten). Hauswacht
   lehnt sie ab, merkt sie sich aber.
3. Innerhalb der **Anlernzeit** (Standard 5 Minuten): Benutzer bearbeiten → „RFID-Karten/
   -Anhänger“ → die Karte steht dort als „neu, gelesen an Keypad um 18:04“ → auswählen,
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

## Sicherheit

- Eine reine Kartennummer ist kein starker Schutz: Wer sie ausliest (z. B. im Vorbeigehen), kann
  sie kopieren. Für mehr Sicherheit „Karte und PIN“ verwenden.
- Am Keypad schützt der nötige Tastendruck davor, dass eine Karte in der Jackentasche etwas
  schaltet.
- Verlorene Karte: beim Benutzer entfernen oder den Benutzer auf „Aktiv: aus“ stellen.
- Der Bedrohungs-PIN wirkt auch am Keypad.
