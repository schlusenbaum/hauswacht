# Changelog

Alle relevanten Änderungen an diesem Projekt werden hier dokumentiert.
Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
Versionierung nach [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

## [0.28.0] - 2026-11-12

### Hinzugefügt
- **Bedienteile** (Systemeinstellungen → Bedienteile), beliebig viele, je Bereich oder für
  alle Bereiche:
  - **Keypads über Zigbee2MQTT** (Zigbee-Standard für Alarm-Bedienteile, z. B. frient
    KEPZB-110): Tasten je Alarmprofil, Bestätigung jeder Eingabe, laufende Zustandsanzeige,
    Anmeldung „PIN oder Karte“ bzw. „Karte und PIN“, Notruf-Taste (aus, still, Alarm).
  - **NFC-Aufkleber** mit der Companion App: nur mit dem Handy eines berechtigten Benutzers;
    Aktion je Aufkleber (unscharf, scharf, umschalten).
  - **RFID-/NFC-Leser** (Ereignis „Tag gescannt“, z. B. ESPHome): Karte oder Karte und PIN.
- **RFID-Karten/-Anhänger** als Ausweis am Benutzer, mit gemeinsamem Schutz gegen
  Durchprobieren.

### Geändert
- Rückmeldung an Keypads per MQTT ist die einzige Sendung an Geräte außer Sirenen und
  Benachrichtigungen (statisch geprüft).

## [0.27.0] - 2026-11-12

### Hinzugefügt
- **Funkstille-Beobachtung:** längste Pause zwischen Lebenszeichen je Melder, Empfehlung für
  „Maximale Funkstille“ im Formular und als Diagnose-Sensor. Schaltet nichts.
- **Heimkehr-Beobachtung:** zusätzliche Signale je Person (WLAN-Sensor der Companion App mit
  Heim-WLANs, Bluetooth/Bermuda, Router, Annäherung über „Nähe“, Binärsensoren), Auswertung
  „frühestes Signal“ je Person, größeres Zeitfenster für Annäherung.
- **Tür auf bis unscharf:** gemessene Zeiten je Tür mit Empfehlung für die
  Eingangsverzögerung (Attribut `entry_times`, Bericht).

### Geändert
- Roadmap: Zigbee-Bedienteil als 0.28.0; Kameras für „irgendwann“.
- Entitäten ohne offen/zu (z. B. Messwerte aus 0.24 in alten Auslöseregeln) werden nicht mehr
  beobachtet; das Protokoll nennt sie.

## [0.26.0] - 2026-11-12

### Hinzugefügt
- **Sirenentest** (Alarmgeber – Sirenen): Sirenen wählen, je Sirene „testen?“ mit
  Vorabprüfung ohne Ton, kurzer leiser Ton (Standard 3 s, höchstens 10 s), danach „gehört?“.
  Gleicher sicherer Weg wie ein Alarm (Hardware-Freigabe, kein Testmodus, Brandsperre,
  Einbruchtöne); nur unscharf und nur für Administratoren; Scharfschalten währenddessen
  gesperrt, Unscharf schalten bricht ab.
- Erinnerung „Sirenentest fällig“ (aus, 3, 6, 12 Monate) und optionale Vorwarnung.
- Diagnose-Sensor „Letzter Sirenentest“ mit Ergebnis je Sirene.
- Testkarte: Sirenentest eingeklappt mit Sicherheitsabfrage.
- Aktionen `hauswacht.siren_test`, `siren_test_result`, `siren_test_stop`.

### Geändert
- „Alarmgeber – Sirenen“ ist ein Untermenü (Sirenen und Freigabe, Sirenentest, Erinnerung).
- Simulations-Aktionen akzeptieren auch Schlösser und Abdeckungen.

## [0.25.0] - 2026-11-12

### Hinzugefügt
- **Melder-Typen** (Tür, Fenster, Bewegung, Manipulation, Technik, Sonstiges): nach dem Speichern
  einer Meldergruppe zeigt Hauswacht alle Melder mit vorgeschlagenem Typ, direkt dort änderbar.
- **Technik-Melder** (Wasser, Gas, Frost …) sind automatisch immer aktiv, nie Teil der
  Scharfschaltung und lösen keinen Einbruchalarm aus.
- **Ausgenommene Melder** im Alarmprofil; das Profil zeigt, welche Melder scharf werden.
- Assistent **„Melder aus anderem Sensor erstellen“**: legt aus einem Messwert einen
  Schwellenwert-Helfer (mit Hysterese) an und setzt ihn gleich als Melder ein.

### Geändert
- Nur noch Melder mit „offen/zu“: Binärsensoren, Schlösser und Abdeckungen. Messwerte,
  Ereignisse, Helfer und Schalter aus 0.24.0 entfallen (Umweg über Home-Assistant-Helfer).
- „Sensorverhalten“ heißt jetzt „Funkstille von Sensoren“; Rollen-Ausnahmen werden zu Typen
  (automatische Übernahme).
- Beispiele und Doku: „Außen“ statt „Außenhaut“.

### Entfernt
- Kamerabild in der Alarm-Nachricht und „Alarmbilder speichern“ (kommt später neu konzipiert).

## [0.24.0] - 2026-11-11

### Hinzugefügt
- **Weitere Melderarten:** Schlösser (`lock`, entriegelt/blockiert), Abdeckungen (`cover`, z. B.
  Garagentor offen), Ereignisse (`event`, z. B. Klingel oder Kamera-Erkennung), Messwerte
  (`sensor` mit Schwellwert, z. B. Erschütterung) und Helfer/Schalter. Jede Art hat eine
  passende Standardrolle; die Testkarte zeigt und simuliert sie.
- **Melder bearbeiten** (Sensorverhalten): Rolle, Schwellwert und Kamera je Melder.
- **Kamerabild in der Alarm-Nachricht:** Kamera je Alarmprofil oder je Melder; das aktuelle Bild
  hängt an Alarm- und Eingangsverzögerungs-Nachricht.
- **Alarmbilder speichern:** auf Wunsch 3 Bilder im Abstand von 2 s unter Medien → hauswacht.

### Geändert
- Funkstille-Prüfung gilt nicht für Ereignisse, Helfer und Schalter (sie haben keine
  Lebenszeichen).

## [0.23.1] - 2026-11-11

### Hinzugefügt
- Empfänger können jetzt auch **Benachrichtigungs-Entitäten** sein (`notify.…`), z. B. von
  WhatsApp-, Telegram- oder E-Mail-Integrationen – mit Titel und Text, ohne Knöpfe.
  Lautsprecher erscheinen dort nicht (sie gehören zur Sprachausgabe).

### Geändert
- Der Bedrohungsalarm geht nie an Lautsprecher, auch wenn einer als Empfänger eingetragen wäre.

## [0.23.0] - 2026-11-11

### Hinzugefügt
- **Sprachausgabe** über Lautsprecher, z. B. Echo-Geräte (Integration „Alexa Devices“): je
  Ereignis an/aus, **Durchsage** (mit Gong) oder **Sprechen**, eigene Lautsprecher und Text.
  Hauswacht wählt am Gerät die passende Entität.
- Alarm-Durchsage **wiederholen** alle N Sekunden, bis der Alarm beendet ist.
- **Nachtruhe** (von–bis): nur Ereignisse mit „Auch in der Nachtruhe ansagen“.
- „Zusätzliche Lautsprecher“ pro Alarmprofil für Alarm, Eingangsverzögerung und „Alarm beendet“.
- **Eigene Texte** für Push-Nachrichten und Sprachausgabe mit Platzhaltern (`{melder}`,
  `{profil}`, `{bereich}`, `{wer}`, `{sekunden}`, `{uhrzeit}` …), Prüfung beim Speichern und
  Vorschau.

### Geändert
- Menü „Benachrichtigungen“ ist jetzt ein Untermenü: Empfänger und Ereignisse, eigene Texte,
  Sprachausgabe.
- Stille Alarme werden nie angesagt, der Bedrohungsalarm nie über Lautsprecher.

## [0.22.1] - 2026-11-11

### Behoben
- Gelöschte Bereiche blieben als Gerät „Hauswacht <Name>“ mit Entitäten in der Integration
  stehen; ebenso „Alle Bereiche“, wenn nur noch ein Bereich übrig war. Beides wird jetzt beim
  Neuladen entfernt. Verwaiste Bereichsgeräte lassen sich außerdem von Hand löschen.

## [0.22.0] - 2026-11-11

### Hinzugefügt
- **Bereiche** (Systemeinstellungen → Bereiche): frei benannte Teile der Anlage, die unabhängig
  scharf geschaltet werden (z. B. Garage scharf, Haus unscharf). Jedes Alarmprofil gehört zu
  einem Bereich; Meldergruppen und Auslöseregeln sind für alle Bereiche nutzbar.
- Je weiterem Bereich ein eigenes Gerät „Hauswacht <Name>“ mit Bedienfeld, Profilauswahl,
  Knöpfen und „Offene Sensoren“; dazu das Bedienfeld **„Alle Bereiche“**.
- Benutzer lassen sich auf Bereiche beschränken (leer = alle).
- Benachrichtigungen nennen den Bereich; die Testkarte zeigt, welcher Bereich einen Melder
  gerade überwacht und zu welchem Bereich eine laufende Regel gehört.

### Geändert
- Bedienfeld-Knöpfe sind nur noch **je Bereich** eindeutig.
- Optionen und Profil-Einstellungen lassen sich nur ändern, wenn alle Bereiche unscharf sind.
- Ohne weitere Bereiche bleibt alles wie bisher (gleiche Entitäts-IDs, keine Migration nötig).
- Funknetz- und Gateway-Überwachung meldet nur einmal (im ersten Bereich).

## [0.21.0] - 2026-11-11

### Hinzugefügt
- **Immer aktive Melder** (Alarmauslösung → Immer aktiv): lösen auch unscharf aus. Standard ist
  eine wichtige Benachrichtigung ohne Alarm; optional ein Alarm mit eigenen Sirenen, den „Alarm
  beenden“ nach unscharf zurückführt. Scharf lösen sie sofort mit der Reaktion des Profils aus.
- **Scharf durch Schließen der Tür** (pro Alarmprofil, optional): Die Ausgangsverzögerung endet,
  sobald eine Ausgangstür geschlossen ist und die Beruhigungszeit (Standard 5 s) zu bleibt.
  Ausgangstüren dürfen dann beim Scharfschalten offen sein.
- Benachrichtigungs-Ereignis „Immer aktiver Melder“ (wichtig, standardmäßig an); Testkarte zeigt
  „immer aktiv“.

## [0.20.1] - 2026-11-11

### Hinzugefügt
- Bedingungen können `if_unknown: not_met` tragen: Lässt sich die Bedingung nicht auswerten,
  gilt sie dann als nicht erfüllt („im Zweifel kein Alarm“). Standard bleibt `met`.

## [0.20.0] - 2026-11-11

### Hinzugefügt
- **Expertenmodus für Auslöseregeln:** ganze Regel als YAML bearbeiten oder neu anlegen, mit
  Prüfung und Fehlern mit Fundstelle. Meldergruppen per Name, Umbenennen ist folgenlos.
- **Verschachtelung:** `any` / `all` / `count` beliebig ineinander (z. B. „Keller ODER (Flur UND
  Büro)“). Eine Meldergruppe steht für ihre einzelnen Melder.
- **Ausnahme „Nicht, wenn vorher …“** (`unless` + `before`), auch im Assistenten; die Testkarte
  zeigt „gesperrt durch Ausnahme“.
- **Bedingungen** (`conditions`): Uhrzeit/Wochentage, Person in Zone, Zustand, Zahlenwert, `and` /
  `or` / `not`. Nicht auswertbar = erfüllt (sichere Seite).
- **Ergebnis „nur Benachrichtigung“** (`notify`) mit eigenem Benachrichtigungs-Ereignis.

### Geändert
- Neue Speicherform der Auslöseregeln; Regeln aus 0.19 werden weiter gelesen und beim nächsten
  Speichern umgestellt.

## [0.19.3] - 2026-11-11

### Geändert
- Neue Namen: **Zonen** heißen jetzt **Meldergruppen**, **Regeln** heißen **Auslöseregeln**.
  Beide liegen im neuen Menüpunkt **Alarmauslösung**. Im Alarmprofil heißen die Felder
  „Meldergruppen – jeder Melder löst allein aus“ und „Auslöseregeln“.
- Texte in Optionen, Meldungen, Testkarte und Anleitung angeglichen. Gespeicherte Einstellungen,
  Entitäts-IDs und Attributnamen bleiben unverändert.

## [0.19.2] - 2026-11-11

### Geändert
- Regeln werden mit einem **Assistenten** angelegt: Name und Ergebnis → Schritt für Schritt →
  Übersicht mit „Weiteren Schritt hinzufügen“, „Schritt bearbeiten“, „Letzten Schritt
  entfernen“, „Fertig – speichern“. Bis zu 10 Schritte statt 4.
- Jede Regel wird als **Satz** beschrieben („eine(r) von Tür vorne / Tür hinten, dann innerhalb
  von 120 s Zone Keller → Eingangsverzögerung, dann Alarm“) – im Assistenten, in der
  Regelliste und in der Testkarte.
- Deutlich ausführlichere Erklärung von Schritten, „einer / alle / mindestens N“ und der
  Reihenfolge in den Formularen und in der Anleitung.

## [0.19.1] - 2026-11-11

### Hinzugefügt
- Hinweis beim Scharfschalten, wenn Melder offen sind, die im Profil nur in Regeln vorkommen
  (z. B. ein offenes Fenster): Sie können ihre Regel erst auslösen, wenn sie zu und wieder auf
  gehen. Als Benachrichtigung (neues Ereignis „Hinweis beim Scharfschalten“, standardmäßig an)
  und als Meldung in Home Assistant, die beim Unscharfschalten verschwindet. Attribut
  `open_rule_sensors` am Bedienfeld.

## [0.19.0] - 2026-11-11

### Hinzugefügt
- **Regeln – Abfolgen von Meldern** (neuer Menüpunkt): z. B. „Haustür, dann innerhalb von
  120 s Keller“. Bis zu vier Schritte, je Schritt „einer davon“ (ODER), „alle davon“ (UND) oder
  „mindestens N verschiedene“; Zeit bis zum nächsten Schritt; Ergebnis sofort Alarm oder
  Eingangsverzögerung. Regeln stehen für sich und werden im Alarmprofil ausgewählt.
- Prüfung beim Speichern: Regeln, die nie auslösen können, werden abgelehnt; Hinweise, wenn eine
  Regel in einem Profil nichts bewirkt.
- Testkarte: Fortschritt jeder Regel des aktiven Profils mit Countdown; Melder „nur in Regeln“.
- Die Alarmmeldung nennt die erfüllte Regel.

### Geändert
- Im Alarmprofil heißen die Zonen jetzt „Allein auslösende Zonen“. Melder, die nur in Regeln
  vorkommen, verhindern das Scharfschalten nicht.
- „Unbestätigte Auslösung“ und „Melder löst häufig allein aus“ beziehen sich auf Regeln, die
  begonnen, aber nicht erfüllt wurden.

### Entfernt
- Die Zonen-Option „Alarm erst, wenn ein zweiter Melder bestätigt“ (0.18.0). Eine eingeschaltete
  Option wird beim Update automatisch zur Regel „Bestätigung <Zone>“.

## [0.18.0] - 2026-11-11

### Hinzugefügt
- **Bestätigung durch einen zweiten Melder** als Zonen-Option: Ein Bewegungs-, Präsenz- oder
  Fenstermelder allein löst keinen Alarm aus, erst wenn ein anderer Melder derselben Zone im
  Zeitfenster (Standard 120 s) ebenfalls auslöst. Derselbe Melder zweimal zählt nicht; ist kein
  zweiter Melder verfügbar, gibt es sofort Alarm. Türen und Manipulation sind nicht betroffen.
- Benachrichtigungen „Unbestätigte Auslösung“ und „Melder löst häufig allein aus“ (3× in einer
  Stunde), beide standardmäßig aus.
- Testkarte: „wartet auf zweiten Melder“ mit Countdown, Hinweis bei Zonen mit Bestätigung.

## [0.17.6] - 2026-11-11

### Geändert
- „Offene Sensoren“ heißt „Offene Sensoren in den Zonen“ und zeigt „Offen“ / „Alles zu“.
- „Simulierte Sensoren“ heißt „Testkarte: simulierte Sensoren“, zählt in „Sensoren“ und ist bei
  Neuinstallationen standardmäßig ausgeblendet (die Testkarte funktioniert trotzdem).
- Die Entitäts-IDs bleiben unverändert.

### Hinzugefügt
- Link zur Anleitung auf der Geräteseite von Hauswacht.
- Erstes offizielles Release: `hauswacht.zip` hängt an jedem Release (HACS installiert daraus
  und zählt die Downloads); der Tag muss zur Manifest-Version passen. Abzeichen für Release,
  Downloads, HACS und CI im README.

## [0.17.5] - 2026-11-11

### Geändert
- Optionen: Nach dem Speichern eines Formulars bleibt der Dialog offen und kehrt ins Menü
  zurück („✅ Gespeichert“). Untermenüs haben „← Zurück“, das Hauptmenü „Fertig – schließen“.
- Wird die Anlage scharf geschaltet, während der Optionsdialog offen ist, wird nichts mehr
  gespeichert (vorher hätte das Speichern die Integration im scharfen Zustand neu geladen).

## [0.17.4] - 2026-11-11

### Geändert
- Optionen neu gegliedert: **Zonen**, **Alarmprofile**, **Alarmgeber – Sirenen**,
  **Benachrichtigungen** und **Systemeinstellungen**. Unter Systemeinstellungen: Benutzer und
  PINs (mit den PIN-Regeln), Sensorverhalten (Rollen-Ausnahmen und Funkstille in einem
  Formular), Funknetz und Gateways überwachen (bisher „Systemüberwachung“),
  Heimkehr-Beobachtung.

## [0.17.3] - 2026-11-11

### Geändert
- Optionen verständlicher: „Zonen – welche Sensoren überwacht werden“ mit Erklärung und
  Beispielen (Außenhaut, Innen/Keller), klarere Feldnamen; „Sensorrollen – Ausnahmen“,
  „Funkstille von Sensoren“, „Systemüberwachung (Zigbee, MQTT …)“. Im Profil erklärt
  „Überwachte Zonen“, was scharf ist.

### Hinzugefügt
- Ein Sensor kann nur noch in **einer** Zone sein (auch über Labels). Beim Speichern einer
  Zone nennt die Meldung Sensor und bisherige Zone.

## [0.17.2] - 2026-11-11

### Hinzugefügt
- Karte „Hauswacht Test“: Zustand der Anlage mit Profil und Countdown der Ein-/Ausgangs-
  verzögerung; pro Sensor der Hinweis „überwacht“, „nicht im aktiven Profil“, „überbrückt bis
  zum Schließen“ bzw. bei Manipulationssensoren „löst Alarm aus“ / „nur Meldung“.
- Attribut `status` je Sensor am Sensor „Simulierte Sensoren“.

## [0.17.1] - 2026-11-11

### Hinzugefügt
- **Karte „Hauswacht Test“** (`custom:hauswacht-test-card`): alle Sensoren der Hauswacht-Zonen
  mit Knöpfen Auf/Zu, Bewegung/Ruhe, Manipulation/OK, Weg (nicht verfügbar) und Echt; Testmodus
  ein/aus und „Alle echt“ direkt in der Karte.
- Aktionen `hauswacht.simulate_state` und `hauswacht.simulate_reset`, Sensor „Simulierte
  Sensoren“.
- Simulation nur im Testmodus (keine Sirenen) und nur für Hauswacht: Zustände in Home
  Assistant bleiben unverändert. Testmodus aus oder Neustart = alles wieder echt.

## [0.17.0] - 2026-11-10

### Hinzugefügt
- **Benachrichtigungen pro Ereignis** (Alarm, Tür geöffnet, Alarm beendet, scharf, unscharf,
  Scharfschaltung abgelehnt, Automatik, Störung, System, Erinnerung): an/aus und eigene
  Empfänger; sonst gehen sie an die allgemeinen Empfänger.
- **Wichtige Hinweise:** Alarm und Bedrohung durchbrechen „Nicht stören“ (iPhone kritischer
  Hinweis, Android Kanal `alarm_stream`); abschaltbar.
- **Scharfschaltung abgelehnt** mit Knöpfen „Trotzdem scharf“ (nur wenn Überbrücken erlaubt
  ist) und „Erneut versuchen“.
- **Erinnerung „Alle weg, Anlage unscharf“** mit Knopf „Jetzt scharf“ – Hauswacht schaltet
  dabei nichts selbst.

### Geändert
- „Dienste für Systemmeldungen“ heißen jetzt „Allgemeine Empfänger“.
- Scharf- und Unscharf-Meldungen sind neu und standardmäßig aus; die bisherige Systemmeldung
  „Automatisch scharf schalten fehlgeschlagen“ ist jetzt „Scharfschaltung abgelehnt“.

## [0.16.3] - 2026-11-10

### Hinzugefügt
- Reparatur-Hinweis „Nicht alle Personen haben einen PIN“, sobald es PINs gibt, aber Benutzer
  oder Home-Assistant-Konten ohne PIN – mit Namen und Auswegen.
- Deutlicher Hinweis in den Formularen „Benutzer und PINs“, „Benutzer“, „PIN-Regeln“ und in
  der Anleitung: Ein PIN gilt beim Unscharfschalten für alle.

## [0.16.2] - 2026-11-10

### Hinzugefügt
- **Master-PIN** unter PIN-Regeln: einfacher PIN ohne eigene Benutzer (intern Benutzer
  „Master-PIN“ mit allen Rechten).
- Option **„Dashboard-Knöpfe trotz PIN erlauben“**: Der PIN schützt dann nur Bedienfeld und
  Sprachassistenten.

## [0.16.1] - 2026-11-10

### Geändert
- Benutzer anlegen: Das Namensfeld schlägt die Home-Assistant-Benutzer vor (freie Namen
  weiter möglich); ein gewählter Home-Assistant-Benutzer wird automatisch verknüpft.
- Menüpunkt „PIN“ heißt jetzt „PIN-Regeln“ und enthält nur noch „PIN auch zum
  Scharfschalten“ und „Alarm ohne PIN beenden“. PINs gehören zu den Benutzern.
- Migration (Version 3): Ein vorhandener einzelner PIN wird zum Benutzer „Hauptbenutzer“.

## [0.16.0] - 2026-11-10

### Hinzugefügt
- **Benutzer und PINs** (Konfigurieren → Benutzer und PINs): Name, eigener PIN, Rechte
  (scharf, unscharf, Alarm beenden), aktiv/gesperrt, Zuordnung zu einem Home-Assistant-Konto.
- **Gemeinsame PINs** erlaubt; Anzeige „gemeinsamer PIN (…)“, erlaubt, wenn einer darf.
- **Gäste-Zeitraum** („gültig von/bis“).
- **Bedrohungs-PIN** mit heimlichem Notruf an eigene Empfänger.
- „Geändert von“ am Bedienfeld (Benutzer, gemeinsamer PIN, Home-Assistant-Konto oder
  „Automatik“), auch in den Push-Nachrichten.

### Geändert
- PIN-Prüfung läuft im Hintergrund (kein kurzes Hängen von Home Assistant).
- Der bisherige einzelne PIN gilt als Benutzer „Hauptbenutzer“.

## [0.15.1] - 2026-11-10

### Behoben
- Karte „Hauswacht Einstellungen“ zeigte statt der Namen nur „entity“.
- Fehlende Symbole bei Ausgangs- und Eingangsverzögerung.

## [0.15.0] - 2026-11-10

### Hinzugefügt
- Dashboard-Karte **„Hauswacht Einstellungen“** (`custom:hauswacht-einstellungen-card`):
  alle Profil-Einstellungen aus 0.14.0 in einer Karte. Wird von der Integration automatisch
  geladen und erscheint im Kartenauswahl-Dialog.

## [0.14.0] - 2026-11-10

### Hinzugefügt
- **Profil-Einstellungen als Entitäten** für Dashboards: „Profil bearbeiten“ wählt das Profil,
  dazu Verzögerungen, Reaktionszeit, Alarmzyklen, Wartezeit, Verhalten bei offenen/ausgefallenen
  Sensoren, Sirenenton, Lautstärke, stiller Alarm, Sabotage, Unscharf beim Heimkommen und die
  Uhrzeiten der Automatik. Änderungen nur im unscharfen Zustand.

### Sicherheit
- Statischer Test verschärft: Hauswacht darf ausschließlich Dienste von `siren` (nur im
  Sirenen-Executor) und `notify` aufrufen.

## [0.13.1] - 2026-11-07

### Geändert
- Meldung „Scharfschaltung verweigert“ nennt gestörte Infrastruktur jetzt getrennt
  („Gestört: …“) statt unter „Nicht verfügbar“, und alle Sensoren mit Namen und Raum.

## [0.13.0] - 2026-11-06

### Hinzugefügt
- Option **„Alarm ohne PIN beenden“** (unter PIN, standardmäßig aus): Der Knopf
  „Alarm beenden“ funktioniert dann auch bei eingestelltem PIN. Unscharfschalten verlangt
  weiter den PIN.

## [0.12.0] - 2026-11-06

### Hinzugefügt
- Knopf **„Unscharf schalten“**: sofort unscharf, auch während eines Alarms.
- Knopf **„Alarm beenden“**: nur den Alarm beenden, das Profil bleibt scharf.
- Beide Knöpfe sind nicht verfügbar, wenn ein PIN eingestellt ist (Knöpfe können keinen PIN
  abfragen).

## [0.11.0] - 2026-11-06

### Geändert
- **Unscharf während eines Alarms beendet nur den Alarm**, das Profil bleibt scharf.
  Sirenen gehen aus (Brandsperre gilt), Sensoren, die gerade offen sind, werden überbrückt,
  bis sie wieder schließen. Erst ein zweites Unscharf schaltet unscharf. Gilt für Karte,
  Bedienfeld, Push-Knopf und Automationen; ein eingestellter PIN wird abgefragt.
- Push-Knopf heißt während eines Alarms „Alarm beenden“.
- Neues Attribut `bypassed_until_closed` am Bedienfeld.

### Behoben
- Test der Uhrzeit-Automatik hing von der Tageszeit ab, zu der die Tests liefen.

## [0.10.1] - 2026-11-06

### Behoben
- Profile ließen sich seit 0.9.0 nicht speichern („Nicht alle Pflichtfelder sind ausgefüllt“),
  solange der Bereich „Automatik“ zugeklappt war. Die Felder darin sind jetzt alle freiwillig
  und werden vorbelegt. Ein neuer Test bildet die Vorbelegung der Oberfläche nach und prüft,
  dass das Formular unverändert abgeschickt werden kann.

## [0.10.0] - 2026-11-06

### Hinzugefügt
- **Push-Knopf „Unscharf schalten“** (Option unter „Benachrichtigungen“, standardmäßig aus):
  Beim Öffnen einer Eingangstür im scharfen Zustand und beim Alarm bekommen die
  Alarm-Empfänger eine Benachrichtigung mit Knopf direkt in der Benachrichtigung. Gilt nur
  für die laufende Scharfschaltung und nur für angemeldete Home-Assistant-Benutzer; auf dem
  iPhone nur mit entsperrtem Gerät. Nach dem Unscharfschalten wird die Benachrichtigung
  entfernt.
- **Heimkehr-Beobachtung** (neuer Menüpunkt, standardmäßig aus): zeichnet Türöffnungen und
  Heimkehrten pro Person und Ortungsquelle auf und berechnet, wie zuverlässig eine
  automatische Heimkehr wäre (Verzögerung zur Tür, Ankünfte ohne Tür, Fehlalarme je
  Eingangsverzögerung). **Schaltet nichts.** Sensor „Heimkehr-Beobachtung“ und Knopf
  „Heimkehr-Bericht“.

### Geändert
- Alarmmeldungen nennen den auslösenden Sensor mit Namen und Raum statt der Entitäts-ID.

## [0.9.3] - 2026-11-06

### Behoben
- Sirenen, die nur Ein und Aus kennen, liefen bis zum Unscharfschalten – oder nach dem Ende
  der Reaktionszeit sogar endlos weiter. Hauswacht schaltet die eigenen Sirenen jetzt am Ende
  der Reaktionszeit aus und beim Unscharfschalten auch aus dem Zustand „Alarm gehalten“.
- Hat die Brandsperre das Ausschalten verhindert, versucht Hauswacht es jede Minute erneut,
  bis kein Brand mehr gemeldet wird. Solange es brennt, wird nie ausgeschaltet.

## [0.9.2] - 2026-11-06

### Geändert
- **Sirenen nach ihren Fähigkeiten ansteuern:** Hauswacht liest `supported_features` und
  `available_tones` und sendet Ton, Lautstärke und Dauer nur, wenn die Sirene sie unterstützt.
  Damit funktionieren auch einfache Sirenen ohne Rauchmelder.
- Kennt eine Sirene den gewählten Einbruchton nicht, wird ein anderer Einbruchton gewählt –
  nie ein Brandton.

### Sicherheit
- Rauchmelder ohne Tonauswahl, Sirenen mit nur Brandtönen und Sirenen, die sich weder zeitlich
  begrenzen noch ausschalten lassen, werden für Einbruchalarme nicht angesteuert (Grund in
  `last_siren_decision`). Sirenen ohne Ausschaltfunktion bekommen keinen Ausschaltbefehl.

### Dokumentation
- Neuer Abschnitt „Geräte und Kompatibilität“: getestetes Sirenenmodell (Develco SMSZB-120 über
  Zigbee2MQTT) und Anforderungen an andere Sirenen.

## [0.9.1] - 2026-11-06

### Geändert
- Offene Sensoren werden mit Raum angezeigt (Attribut `names` von
  `binary_sensor.hauswacht_offene_sensoren`, z. B. „Küche: Fensterkontakt links“). Steht der
  Raum schon im Namen, wird er nicht wiederholt.
- Beispielkarte vereinfacht: Scharfschalten nur noch über Profilauswahl und „Scharf schalten“,
  im scharfen Zustand ein Knopf „Unscharf schalten“ (mit PIN-Abfrage, falls eingestellt).

## [0.9.0] - 2026-11-06

### Hinzugefügt
- **Automatik pro Profil** (aufklappbarer Bereich „Automatik“ im Profil):
  - scharf und/oder unscharf zu einer Uhrzeit, wahlweise nur an bestimmten Wochentagen
  - scharf, wenn alle ausgewählten Personen weg sind – nach einer einstellbaren Wartezeit
    (Standard 15 Minuten), damit kurze WLAN-Aussetzer von Handys nicht scharf schalten
  - optional unscharf, sobald eine dieser Personen heimkommt – nur wenn das Profil vorher
    automatisch scharf geschaltet wurde
- Sicherheitsregeln der Automatik: nur aus „unscharf“ heraus, nie offene Sensoren überbrücken,
  nie einen laufenden Alarm oder eine Eingangsverzögerung beenden; Personen mit unbekanntem
  Aufenthalt gelten nicht als weg.
- Systemmeldungen und Ereignisse: `AutoArmed`, `AutoArmFailed`, `AutoArmScheduled`,
  `AutoArmCancelled`, `AutoArmSkipped`, `AutoDisarmed`, `AutoDisarmSkipped`.
- **Integrationssymbol** für helles und dunkles Design (ab Home Assistant 2026.3).

## [0.8.0] - 2026-11-06

### Geändert (Breaking)
- **Profile sind jetzt frei definierbar.** Es gibt keine eingebauten Profile mehr; bei einer
  Neuinstallation legst du bereits das erste Profil selbst an. Jedes Profil hat Name, Symbol,
  optional einen Knopf am Bedienfeld und alle bisherigen Einstellungen.
- Jeder Bedienfeld-Knopf (Zuhause, Nacht, Abwesend, Urlaub, Benutzerdefiniert) kann höchstens
  einem Profil zugeordnet sein. Das Bedienfeld bietet nur zugeordnete Knöpfe an. Profile ohne
  Knopf erscheinen im scharfen Zustand als „benutzerdefiniert“.
- `hauswacht.arm` akzeptiert den Profilnamen oder die ID.

### Hinzugefügt
- Auswahlliste **„Profil“** und Knöpfe **„Scharf schalten“** und **„Trotzdem scharf
  schalten“** für das gewählte Profil – so ist jedes Profil bedienbar, auch ohne Knopf.
- Im scharfen Zustand zeigt das Bedienfeld das Symbol des aktiven Profils; neues Attribut
  `profile_name`.

### Migration
- Bestehende Installationen: Die bisherigen fünf Profile werden mit ihren Einstellungen als
  normale Profile übernommen (Zuhause, Nacht, Abwesend, Urlaub, Individuell) und lassen sich
  danach umbenennen, ändern oder löschen.

## [0.7.0] - 2026-11-06

### Hinzugefügt
- **Profil „Individuell“:** fünftes, frei belegbares Profil (Zonen, Zeiten, Sirenen,
  Benachrichtigungen), erscheint am Bedienfeld als „benutzerdefiniert“ (`armed_custom_bypass`).
- **Schutz gegen PIN-Raten:** Ab der 5. falschen Eingabe in Folge ist die PIN-Eingabe
  gesperrt (60 s, danach jeweils doppelt so lange, höchstens 15 min). Ab der 3. falschen
  Eingabe geht eine Systemmeldung raus. Ereignis `InvalidCode`.

## [0.6.0] - 2026-11-06

### Hinzugefügt
- **Beispielkarte** `examples/dashboard/hauswacht-karte.yaml` nur mit Standardkarten:
  Bedienkachel, „Trotzdem scharf schalten“-Knöpfe mit Rückfrage (nur sichtbar, wenn
  unscharf und Sensoren offen sind) und Systemstatus bei Problemen.
- Binärsensor **„Offene Sensoren“** (`binary_sensor.hauswacht_offene_sensoren`) mit den
  Attributen `sensors` und `names`.
- Anleitung `docs/dashboard.md`.

## [0.5.1] - 2026-11-06

### Behoben
- Systemindikatoren der Geräteklasse „Problem“ (z. B. ein Störungssensor) wurden falsch herum
  gewertet: „aus“ (alles in Ordnung) galt als Störung. Hauswacht berücksichtigt jetzt die
  Geräteklasse: bei „Problem“ und „Sicherheit“ bedeutet „an“ Störung, sonst „in Ordnung“.

## [0.5.0] - 2026-11-06

### Hinzugefügt
- **Sirenen:** Registrierung unter Konfigurieren → Sirenen. Die echte Ansteuerung ist
  standardmäßig **gesperrt** und lässt sich nur mit ausdrücklicher Bestätigung freigeben.
- **Reaktion je Profil:** welche Sirenen, Ton (Einbruch, Notfall, Polizei-Panik,
  Notfall-Panik), Lautstärke, stiller Alarm, wer benachrichtigt wird.
- **Brandschutz:** Brand-Indikatoren (Rauch, Testknopf) werden am Sirenengerät automatisch
  erkannt. Meldet irgendein Rauchmelder Brand oder ist der Brandzustand einer registrierten
  Sirene unklar, schaltet Hauswacht keine Sirene ein **und keine aus**.
- Laufzeit wird auf die gerätseitige Höchstdauer begrenzt; dieser Wert wird nur gelesen.
- **Push-Benachrichtigungen** über notify-Dienste (z. B. Home-Assistant-App) mit hoher
  Priorität: Alarm je Profil, Systemmeldungen (Störung, Sensorausfall, Manipulation,
  Neustart) an eigene Empfänger.
- **Testmodus:** nie Sirenen; Push nur, wenn „Auch im Testmodus benachrichtigen“ an ist,
  dann mit „[TEST]“ im Titel.
- Ereignis `SirenDecision` und Attribute `sirens_hardware_enabled`, `last_siren_decision`.

### Sicherheit
- Statischer Test prüft per Syntaxbaum, dass nur der Siren Executor Sirenen-Dienste aufruft
  und keine Gerätewerte geschrieben werden.

## [0.4.0] - 2026-11-06

### Hinzugefügt
- **Simulation im Testmodus:** Aktion `hauswacht.simulate_trigger` löst einen konfigurierten
  Sensor virtuell aus, ohne ein Gerät zu verändern. Nur bei eingeschaltetem Testmodus möglich.
  So lassen sich komplette Abläufe (Eingangsverzögerung, Alarm, Unscharfschalten) gefahrlos
  durchspielen.
- **Systemüberwachung:** Infrastruktur-Indikatoren (z. B. Verbindungsstatus der
  Zigbee2MQTT-Bridge) sind in den Optionen wählbar. Ist ein Indikator aus oder nicht
  verfügbar, meldet Hauswacht eine Störung und behandelt das Scharfschalten wie bei
  ausgefallenen Sensoren.
- **Systemstatus-Entität** `sensor.hauswacht_systemstatus`: OK, Sensoren ausgefallen, Störung.
- Ereignisse `InfrastructureFault`, `InfrastructureRecovered`, `SensorSimulated`.
- Hinweis „Hauswacht: Störung“, wenn im scharfen Zustand ein System ausfällt.

### Getestet
- Ausfall und Wiederkehr von Zigbee2MQTT im scharfen Zustand ohne Fehlalarm; ein nach dem
  Ausfall offen zurückkehrender Sensor löst dagegen aus (sichere Seite).

## [0.3.1] - 2026-11-06

### Behoben
- Die Funkstille-Prüfung nutzte den Zeitstempel von Home Assistant. Der wird bei jedem
  Neustart erneuert, sodass ein ausgefallener Sensor danach stundenlang als lebendig galt.
  Hauswacht verwendet jetzt den gerätseitigen „Zuletzt gesehen“-Wert (z. B. `last_seen` von
  Zigbee2MQTT) desselben Geräts, sofern vorhanden.

### Hinzugefügt
- Attribut `last_contact` am Bedienfeld: letzter Kontakt je Sensor.

## [0.3.0] - 2026-11-06

### Hinzugefügt
- **Sensoren und Zonen:** Zonen bestehen aus direkt gewählten Binärsensoren und optional allen
  Binärsensoren mit einem bestimmten Label (Label direkt an der Entität).
- **Rollen automatisch aus der Geräteklasse:** Tür → Eingang (verzögert), Fenster → sofort,
  Bewegung/Präsenz → Mitläufer, Manipulation → 24 h. Ausnahmen pro Sensor einstellbar.
- **Profile wählen Zonen** und legen fest, wie mit offenen und ausgefallenen Sensoren
  umgegangen wird (verweigern / nach Bestätigung / automatisch überbrücken), wie viele
  Alarmzyklen erlaubt sind und ob Manipulation Alarm auslöst.
- **Bereitschaftsprüfung** beim Scharfschalten und am Ende der Ausgangsverzögerung.
- Optionale **Funkstille-Prüfung:** Ein Sensor, der sich zu lange nicht meldet, gilt als
  ausgefallen (Standard: aus).
- **Ausfallmeldung**, wenn ein überwachter Sensor im scharfen Zustand nicht mehr verfügbar ist.
- Aktion **`hauswacht.arm`** mit `confirm`, um offene oder ausgefallene Sensoren bewusst zu
  bestätigen.
- Neue Attribute am Bedienfeld: `zones`, `monitored_sensors`, `open_sensors`,
  `unavailable_sensors`.

### Geändert
- Ein Profil ohne zugeordnete Sensoren lässt sich nicht mehr scharf schalten.
- Standard für Alarmzyklen: 3.

### Upgrade-Hinweis
- Nach dem Update haben die Profile noch keine Zonen und lassen sich deshalb erst scharf
  schalten, wenn unter **Konfigurieren → Zonen und Sensoren** Zonen angelegt und unter
  **Profile** zugeordnet wurden.

### Hinweis
- Weiterhin keine Sirenen und keine Push-Benachrichtigungen. Ein Alarm erscheint als Hinweis
  in Home Assistant und als Ereignis `hauswacht_event`.

## [0.2.0] - 2026-11-06

### Hinzugefügt
- Installierbare Home-Assistant-Integration (HACS), eine Instanz pro Installation.
- `alarm_control_panel` mit den Profilen Zuhause, Nacht, Abwesend und Urlaub.
- Testmodus-Schalter (nur unscharf umschaltbar, bleibt über Neustarts erhalten).
- Optionen: PIN (4–8 Ziffern, nur als Hash gespeichert, optional auch zum Scharfschalten)
  und Zeiten je Profil. Änderungen nur im unscharfen Zustand.
- Hinweis nach Neustart, wenn die Anlage vorher scharf war.
- Ereignis `hauswacht_event` für jede Aktion der Zustandsmaschine.
- Integrationstests mit Home Assistant und Hassfest in der CI.

### Geändert
- Tests aufgeteilt in `tests/core` (ohne HA) und `tests/integration` (mit HA).
- GitHub-Actions auf aktuelle Versionen angehoben.

### Hinweis
- Noch keine Sensoren, Sirenen oder Push-Benachrichtigungen. Ein Alarm kann in dieser
  Version noch nicht durch Sensoren ausgelöst werden.

## [0.1.0] - 2026-11-06

### Hinzugefügt
- Projektgerüst: README, MIT-Lizenz, CI (Ruff, Mypy, Pytest).
- Zustandsmaschine als reine Logik (`core/state_machine.py`): Scharf-/Unscharfschaltung,
  Aus- und Eingangsverzögerung, Sensorrollen (entry, instant, follower, tamper_24h),
  Bereitschaftsprüfung mit Policies, Re-Trigger mit Zyklusgrenze, Testmodus,
  Neustart immer unscharf, Timer-Absicherung über Tokens.
- Sirenen-Guard als reine Logik (`core/siren_guard.py`): Testmodus- und Hardware-Sperre,
  globale Brandsperre (auch bei unklarem Zustand), Ausschalten nur eigener Geräte,
  Verbot von Brandtönen, Begrenzung auf gerätseitige Höchstdauer.
- Statische Sicherheitstests (keine Rauchmelder-Scripts, keine number-Schreibzugriffe,
  keine HA-Importe im Kern, keine direkten Sirenen-Aufrufe).
- Dokumentation: Architektur, Zustandsmodell, Sicherheit, Tests, Roadmap, ADRs 0001–0004.

### Hinweis
- Noch nicht in Home Assistant installierbar.
