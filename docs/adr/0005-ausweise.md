# ADR 0005: Ausweise – PIN heute, RFID/NFC und Fingerabdruck später

- Status: angenommen (Umsetzung von RFID/NFC und Fingerabdruck offen, Roadmap 1.x)
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

## Sicherheitsregeln für die Umsetzung

- Das Lesegerät meldet nur eine Kennung und entscheidet nie selbst; die Entscheidung fällt in
  Hauswacht.
- Kennungen werden wie PINs nicht im Klartext gespeichert (Hash), sofern das Gerät die Kennung
  nicht ohnehin offen überträgt.
- Fehlversuche zählen in denselben Schutz gegen Durchprobieren wie PIN-Fehler.
- Dokumentation weist darauf hin, dass einfache 125-kHz-Karten kopierbar sind; empfohlen werden
  13,56-MHz-Karten (z. B. MIFARE DESFire) oder NFC per Handy.
