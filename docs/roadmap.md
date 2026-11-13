# Roadmap

## Erreicht

| Version | Inhalt |
|---|---|
| 0.1–0.5 | Zustandsmaschine und Sirenen-Guard als reine Logik, Integrationsgerüst, Melder und Profile, Testmodus und Simulation, Überwachung von Funknetz und Gateways, Benachrichtigungen, Sirenen (Freigabe standardmäßig aus) |
| 0.6–0.9 | Beispiel-Dashboard, Schutz gegen PIN-Raten, frei definierbare Profile, Automatik (Uhrzeit, Anwesenheit) |
| 0.10–0.15 | Heimkehr-Beobachtung, Push-Knopf „Unscharf schalten“, Alarm beenden (Profil bleibt scharf), Profil-Einstellungen als Entitäten, Karte „Hauswacht Einstellungen“ |
| 0.16–0.18 | Benutzer mit eigenem PIN, Bedrohungs-PIN, Benachrichtigungen pro Ereignis, Testkarte |
| 0.19–0.21 | Auslöseregeln (Assistent und YAML, Ausnahmen, Bedingungen), immer aktive Melder, Scharf durch Schließen der Tür |
| 0.22 | Bereiche mit eigenem Bedienfeld und „Alle Bereiche“ |
| 0.23 | Sprachausgabe über Lautsprecher, eigene Texte mit Platzhaltern |
| 0.25 | Nur Melder mit offen/zu, Melder-Typen, Ausnahmen im Profil, Assistent „Melder aus anderem Sensor“ |
| 0.26 | Sirenentest (einzeln, kurz, leise, mit Bestätigung) – erfolgreich mit echten Sirenen erprobt |
| 0.27 | Funkstille-Beobachtung, zusätzliche Heimkehr-Signale, „Tür auf bis unscharf“ |
| 0.28 | Bedienteile: Zigbee2MQTT-Keypads mit Rückmeldung, NFC-Aufkleber, RFID-Leser, Notruf-Taste |
| 0.29 | Benutzer-Rechte je Bereich |
| 0.30–0.32 | RFID-Karten unabhängig vom PIN, Anlernen über Keypad (nur unscharf, Anlernzeit), Zufallsnummern erkannt, Falscheingaben zurücksetzen, Fehlversuche verfallen nach 24 h |
| 0.33 | Aufgeräumte Dokumentation, Screenshots, Issue-Vorlagen |
| 0.34 | Anlagenübersicht (Karte, Druck, Notfallblatt), Prüfhinweise mit Reparaturen, Diagnose-Datei |
| 0.35 | Karte „Hauswacht Alarm“ ohne PIN-Zwang (Konto als Ausweis, PIN je Konto einstellbar) |
| 0.36 | Heimkehr-Bericht zum Herunterladen (Markdown und CSV) |
| 0.37 | Visueller Editor für alle Karten; Alarmkarte anpassbar (Profile, Größe, Anzeigen, Farben, Rückfragen) |
| 0.38 | Benachrichtigungen, Push-Knöpfe und Berichte auf Englisch (folgen der Sprache von Home Assistant) |

Details zu jeder Version: [CHANGELOG](../CHANGELOG.md).

## Geplant

| Wann | Inhalt |
|---|---|
| später | Dokumentation auf Englisch |
| später | ZHA- und Z-Wave-Keypads |
| später | Entscheidung über eine Heimkehr-Automatik (mit Belegen) anhand der Heimkehr-Beobachtung |
| 1.0.0 | Stabil, Doku vollständig, Aufnahme in die HACS-Standardliste |
| irgendwann | Kameras: Bild in der Nachricht, Kamera-Erkennung als eigener Melder-Typ – in Ruhe neu konzipieren |
| 1.x | Weitere Ausweise (z. B. Fingerabdruck), weitere Automatik-Bedingungen, wiederkehrende Gäste-Zeiten |

## Grundsätze

- **Hauswacht schaltet keine Geräte** – außer Sirenen (nach Freigabe) und den Zustandsanzeigen
  eingerichteter Keypads.
- **Brandalarm hat Vorrang**, Testmodus sperrt Sirenen technisch, nach einem Neustart unscharf.
- **PIN optional**, Sprachassistenten nur mit PIN. Freigabe für Alexa & Co. über die normale
  Entitätsfreigabe von Home Assistant.
- Größere Bausteine erst mit Konzept, dann umsetzen. Entscheidungen mit Begründung stehen in den
  [ADRs](entwicklung/adr/README.md).

## Wichtige Entscheidungen

- **Bereiche:** frei benannt, eine Zustandsmaschine je Bereich; Alarmprofile gehören zu einem
  Bereich, Meldergruppen und Regeln sind gemeinsame Bausteine
  ([ADR 0007](entwicklung/adr/0007-bereiche.md)).
- **Auslöseregeln** statt Zonen-Bestätigung: ODER-verknüpft, können sich nicht gegenseitig
  aushebeln ([ADR 0006](entwicklung/adr/0006-regeln.md)).
- **Namen:** „Zonen“ heißen „Meldergruppen“, „Regeln“ heißen „Auslöseregeln“; interne
  Schlüssel (`zones`, `rules`) bleiben.
- **Ausweise:** PIN und RFID-Karte gehören zum Benutzer, Aufkleber und Leser zu den
  Bedienteilen ([ADR 0005](entwicklung/adr/0005-ausweise.md)).

## Versionierung und Releases

- Semantic Versioning. 0.x: Schnittstellen dürfen sich ändern. Ab 1.0.0 Breaking Changes nur in
  Major-Versionen, immer mit Migration der Einstellungen.
- `main` ist immer grün; Änderungen über Pull Requests.
- Releases als Git-Tag + GitHub-Release; HACS liest die Releases.
