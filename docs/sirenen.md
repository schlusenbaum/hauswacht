# Sirenen

> **Sicherheit zuerst:** Nach der Installation sendet Hauswacht **keinen** Sirenenbefehl. Erst
> die bewusste Freigabe („Echte Sirenenansteuerung erlauben“) schaltet das frei. Im Testmodus
> sind Sirenen immer gesperrt. Ein Brand hat immer Vorrang.

## Welche Sirenen gehen?

Jede Home-Assistant-Entität der Domain `siren` (Schalter über einen [Assistenten](#sirene-aus-schalter-erstellen)) – Innen- und Außensirenen genauso wie
Rauchwarnmelder mit Sirene. Hauswacht liest vor jedem Alarm, was eine Sirene kann
(`supported_features`, `available_tones`), und sendet nur das:

| Fähigkeit der Sirene | Verhalten |
|---|---|
| Tonauswahl mit Einbruchton | Gewählter Ton; fehlt er, ein anderer Einbruchton (`burglar`, `emergency`, `police_panic`, `emergency_panic`) – **nie ein Brandton** |
| Tonauswahl nur mit Brandtönen | Sirene wird für Einbruch **nicht** verwendet |
| Keine Tonauswahl | Einfache Sirene: ohne Tonangabe. **Rauchmelder** ohne Tonauswahl werden nicht verwendet, weil ihr Standardton meist der Brandton ist |
| Lautstärke, Dauer | Nur gesendet, wenn unterstützt |
| Nur Ein und Aus | Hauswacht schaltet sie nach der Reaktionszeit und beim Unscharfschalten selbst aus |
| Weder Dauer noch Ausschalten | Sirene wird nicht verwendet – Hauswacht könnte sie nicht beenden |
| Höchstdauer (`number.<sirene>_max_duration`, Zigbee2MQTT) | Dauer wird darauf begrenzt; fehlt sie, gelten 240 Sekunden |
| Brandsensor am selben Gerät | Gerätebezogene Brandsperre; ein aktiver Brand an einem beliebigen Melder sperrt immer |
| Eigene Tonnamen (z. B. Homematic IP Alarmsirene HmIP-ASIR) | erst nach Wahl des Tons ([Ton je Sirene](#ton-je-sirene)) |
| Nur als Schalter (`switch.…`) vorhanden | über den [Assistenten](#sirene-aus-schalter-erstellen) oder als [Experten-Funktion](#experten-schalter-direkt-als-sirene) |

**Erprobt** ist der Rauchwarnmelder **Develco/frient SMSZB-120** („Smoke detector with siren“)
über Zigbee2MQTT – auch mit echtem [Sirenentest](#sirenentest). Andere Modelle erst mit Testmodus
und Sirenentest prüfen. Rückmeldungen zu weiteren Modellen sind willkommen
([Issue](https://github.com/schlusenbaum/hauswacht/issues)).

Warum eine Sirene nicht angesteuert wurde, steht nach jedem Alarm im Attribut
`last_siren_decision` am Bedienfeld.

## Einrichten

**Alarmgeber – Sirenen.**

1. Sirenen auswählen, die Hauswacht für Einbruchalarme verwenden darf.
2. In jedem Profil festlegen, welche dieser Sirenen ertönen, mit welchem Ton und welcher
   Lautstärke – oder „Stiller Alarm“ für nur Benachrichtigungen.
3. Erst wenn alles getestet ist: **„Echte Sirenenansteuerung erlauben“** einschalten und die
   Bestätigung anhaken. Ohne diese Freigabe sendet Hauswacht nie einen Sirenenbefehl.

Die Laufzeit entspricht der „Dauer der Alarmreaktion“ des Profils. Danach – und beim
Beenden des Alarms – schaltet Hauswacht die Sirenen aus, die es selbst eingeschaltet hat. Das ist
für Sirenen wichtig, die nur Ein und Aus kennen. Sirenen mit eigener Laufzeit (z. B. Rauchmelder
mit Höchstdauer) bekommen die Dauer zusätzlich mitgeschickt, höchstens aber die Höchstdauer
des Geräts. Diese Höchstdauer wird nur gelesen, nie verändert.

## Ton je Sirene

Normalerweise wählt Hauswacht selbst einen Einbruchton (`burglar`, `emergency` …). Manche
Sirenen nennen ihre Töne anders – findet Hauswacht keinen bekannten Einbruchton, bleibt die
Sirene aus Sicherheitsgründen aus (Grund „kein Einbruchton“), und die
[Übersicht](uebersicht.md#prüfhinweise) meldet das als wichtigen Prüfhinweis.

**Alarmgeber – Sirenen → Ton je Sirene** → Sirene wählen → einen der Töne wählen, die das Gerät
selbst meldet. Der Ton gilt bei Alarm und beim Sirenentest. Brandtöne (mit „fire“, „smoke“ oder
„Brand“ im Namen) sind nie erlaubt. Danach einen kurzen, leisen [Sirenentest](#sirenentest)
machen.

**Beispiel Homematic IP Alarmsirene (HmIP-ASIR, HmIP-ASIR-2, HmIP-ASIR-O)** über die Integration
Homematic(IP) Local: Die Sirene erscheint als `siren.…` und bleibt stumm, wenn sie nicht Ton
**und** Dauer bekommt. Als Ton z. B. `FREQUENCY_RISING_AND_FALLING` wählen; die Dauer schickt
Hauswacht automatisch mit (Alarmdauer des Profils).

## Sirene aus Schalter erstellen

Manche Sirenen erscheinen in Home Assistant nur als Schalter (`switch.…`). Home Assistant kann
daraus selbst eine Sirene machen – der Helfer **„Gerätetyp eines Schalters ändern“**. Hauswacht
hat dafür einen Assistenten:

**Alarmgeber – Sirenen → Sirene aus Schalter erstellen** → Schalter wählen → bestätigen, dass es
eine reine Alarmsirene ist.

- Der Assistent legt den Helfer an und trägt die neue Sirene gleich ein. Der Schalter wird dabei
  **nicht** geschaltet; Home Assistant blendet ihn aus und zeigt die Sirene.
- Die neue Sirene kennt nur ein und aus: Hauswacht schaltet sie bei Alarm ein und nach der
  Alarmdauer wieder aus. Freigabe, Brandsperre, Testmodus und Sirenentest gelten wie immer.
- Rückgängig: den Helfer unter Einstellungen → Geräte & Dienste → Helfer löschen.

> Bei einem Schalter weiß Hauswacht nicht, was das Gerät beim Einschalten tut. Nur echte
> Alarmsirenen so einbinden – nie Rauchmelder oder andere Geräte.

### Experten: Schalter direkt als Sirene

Wer keinen Helfer möchte: **Sirenen und Freigabe → „Experten: Schalter direkt als Sirene
zulassen“** einschalten. Danach lassen sich in derselben Liste auch Schalter auswählen. Hauswacht
schaltet sie genauso wie eine einfache Sirene (`switch.turn_on` bei Alarm, `switch.turn_off`
nach der Alarmdauer), mit denselben Sperren. Wird die Experten-Funktion wieder ausgeschaltet,
fallen die Schalter aus der Liste.

## Sirenentest

**Alarmgeber – Sirenen → Sirenentest (echte Sirene!).** Prüft jede Sirene einzeln, kurz und
leise – über denselben sicheren Weg wie ein echter Alarm.

1. Sirenen wählen (mehrere werden **nacheinander** getestet), Ton (nur Einbruchtöne),
   Lautstärke (Standard **leise**) und Dauer (Standard **3 s**, höchstens **10 s**); anhaken
   „Ich bin vor Ort, Mitbewohner sind informiert“.
2. Für jede Sirene fragt Hauswacht „Sirene … testen?“ und zeigt eine **Vorabprüfung ohne Ton**:
   was gesendet würde (Ton, Lautstärke, Dauer) oder warum es nicht geht. Antwort: testen,
   überspringen oder beenden.
3. Nach dem Ton: „Hast du die Sirene gehört?“ – das Ergebnis wird mit Datum gespeichert
   (Diagnose-Sensor „Letzter Sirenentest“, je Sirene in den Attributen).

Voraussetzungen – der Sirenen-Guard prüft sie wie bei einem Alarm, ohne Ausnahme:

- alle Bereiche **unscharf**, kein Alarm
- **Hardware-Freigabe an**
- **Testmodus aus** – der Testmodus sperrt Sirenen grundsätzlich; der Sirenentest ist bewusst
  kein Testmodus, sondern ein echtes, kurzes Einschalten
- **keine Brandsperre** (kein Rauchmelder aktiv oder unklar), nur Einbruchtöne
- Sirene ist für Einbruch freigegeben und kann begrenzt werden

Die Dauer wird dreifach begrenzt: als Dauer an das Gerät (wenn es das kann), durch einen eigenen
Ausschaltbefehl nach Ablauf und durch die feste Obergrenze von 10 s. Während des Tests ist
**Scharfschalten gesperrt**; **Unscharf schalten** bricht den Test ab. Bei Brand greift Hauswacht
nicht ein – dann gilt die Brandsperre.

**Alarmgeber – Sirenen → Sirenentest – Erinnerung und Vorwarnung:**

| Einstellung | Bedeutung |
|---|---|
| Erinnerung | aus, alle 3 oder 6 Monate, jährlich: meldet „Sirenentest fällig“ (höchstens einmal pro Woche), wenn eine Sirene so lange nicht erfolgreich getestet wurde |
| Vorwarnung vor dem Test | schickt vor dem ersten Ton „Sirenentest … in 10 Sekunden“ an die allgemeinen Empfänger |

Dasselbe als Aktionen (nur für Administratoren): `hauswacht.siren_test` (Felder `siren`,
`duration`, `volume`, `tone`), `hauswacht.siren_test_result` (`siren`, `heard`) und
`hauswacht.siren_test_stop`. In der Testkarte gibt es den Sirenentest eingeklappt mit
Sicherheitsabfrage, siehe [Karte „Hauswacht Test“](testmodus.md#karte-hauswacht-test).

## Brandschutz

Sind die Sirenen zugleich Rauchmelder, erkennt Hauswacht deren Rauch- und
Testknopf-Sensoren automatisch.

- Meldet **irgendein** Rauchmelder in Home Assistant Brand, schaltet Hauswacht keine Sirene
  ein und keine aus.
- Ist der Brandzustand einer **registrierten** Sirene unklar (Sensor nicht verfügbar oder
  deaktiviert), gilt dasselbe.
- Wurde während eines Einbruchalarms Brand gemeldet, schaltet auch das Unscharfschalten keine
  Sirene ab. Sirenen mit eigener Laufzeit verstummen nach ihrer Höchstdauer. Alle anderen
  schaltet Hauswacht aus, sobald kein Brand mehr gemeldet wird (Prüfung jede Minute).
- Fremde Abschalt-Skripte (z. B. „alle Rauchmelder aus“) verwendet Hauswacht nie.

Das Attribut `last_siren_decision` am Bedienfeld zeigt nach jedem Alarm, welche Sirenen
angesteuert und welche aus welchem Grund gesperrt wurden.

Die verbindlichen Regeln dahinter stehen unter [Sicherheitsregeln](entwicklung/safety.md).
