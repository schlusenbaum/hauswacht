# ADR 0005: Ausweise – PIN heute, RFID/NFC und Fingerabdruck später

- Status: angenommen; RFID-Karten, NFC-Aufkleber und Zigbee-Keypads umgesetzt in 0.28.0,
  Fingerabdruck offen
- Datum: 2026-11-10

## Entscheidung

Ein **Benutzer** (seit 0.16) ist die einzige Stelle für Identität und Rechte. PIN und
Bedrohungs-PIN sind seine ersten **Ausweise**. Spätere Ausweise werden *zusätzlich* am
Benutzer gespeichert, ohne das Modell zu ändern:

| Ausweis | Speicherung am Benutzer | Quelle in Home Assistant |
|---|---|---|
| PIN, Bedrohungs-PIN | Hash (PBKDF2) | Bedienfeld, Dienst `hauswacht.arm` |
| RFID/NFC | Kennung(en), optional als Bedrohungs-Kennung markiert | Ereignis `tag_scanned` (Home-Assistant-App, ESPHome), Zigbee-Tastenfelder |
| Fingerabdruck | Finger-Nummer(n) je Lesegerät, optional als Bedrohungs-Finger | ESPHome (z. B. Fingerabdruck-Sensor), Ereignis/Entität |

Für **alle** Ausweise gelten gleich: Rechte, aktiv/gesperrt, Gäste-Zeitraum, gemeinsame
Nutzung („gemeinsamer …“), Bedrohungs-Funktion, „geändert von“.

**Lesegeräte** werden einzeln eingetragen; je Lesegerät wird festgelegt, was eine gültige
Eingabe bewirkt (z. B. „umschalten: scharf ↔ unscharf, im Alarm Alarm beenden“ oder „Profil X
scharf schalten“). Optional zwei Faktoren (Ausweis + PIN) je Lesegerät.

## Begründung

- Rechte und Sperren an einer Stelle: Wird ein Benutzer gesperrt, sind alle seine Ausweise
  gesperrt.
- Hauswacht bindet keine Hardware direkt an, sondern nur, was Home Assistant ohnehin meldet –
  damit funktioniert jedes Gerät, das Home Assistant kennt.

## Umsetzung 0.28.0

- **Bedienteile** (Keypad, NFC-Aufkleber, RFID-Leser) sind getrennt von den Ausweisen. Ein
  **NFC-Aufkleber ist kein Ausweis**: Er bestimmt Ort und Aktion; ausgewiesen wird mit dem Handy
  (Home-Assistant-Konto eines Hauswacht-Benutzers).
- RFID-Kennungen werden normalisiert im Klartext gespeichert, weil Leser und Keypads sie offen
  übertragen (siehe Regel unten).
- Keypads (Zigbee2MQTT) brauchen eine Rückmeldung. Das ist die einzige Sendung an ein Gerät
  außer Sirenen und Benachrichtigungen: `arm_mode` an `<topic>/set`, nur an eingerichtete
  Keypads (statischer Test).

## Sicherheitsregeln für die Umsetzung

- Das Lesegerät meldet nur eine Kennung und entscheidet nie selbst; die Entscheidung fällt in
  Hauswacht.
- Kennungen werden wie PINs nicht im Klartext gespeichert (Hash), sofern das Gerät die Kennung
  nicht ohnehin offen überträgt.
- Fehlversuche zählen in denselben Schutz gegen Durchprobieren wie PIN-Fehler.
- Dokumentation weist darauf hin, dass einfache 125-kHz-Karten kopierbar sind; empfohlen werden
  13,56-MHz-Karten (z. B. MIFARE DESFire) oder NFC per Handy.
