# Roadmap

**Deutsch** | [English](en/roadmap.md)

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
| 0.38–0.39 | Benachrichtigungen, Push-Knöpfe, Berichte und Platzhalter auf Englisch (folgen der Sprache von Home Assistant) |
| 0.40–0.41 | Ton je Sirene (z. B. HmIP-ASIR), Assistent „Sirene aus Schalter erstellen“, Schalter als Sirene und Brandton-Freigabe für Experten |
| 0.42 | Zusätzliche Anwesenheits-Signale je Person für die Profil-Automatik, „Unscharf bei Rückkehr“ mit Türbeleg, Empfehlung der Eingangsverzögerung aus der Heimkehr-Beobachtung |
| 0.43 | Taster als Bedienteil (nur scharf), Türschloss als Bedienteil (Nuki über MQTT oder allgemein: unscharf beim Aufschließen durch einen bekannten Benutzer, optional scharf beim Abschließen) |
| 0.44 | Dokumentation auf Englisch (Anleitung und Sicherheitsregeln), englisches README |
| 0.45 | Verhalten nach Neustart einstellbar: vorherigen Zustand wiederherstellen (Standard), immer scharf, immer unscharf |
| 0.46 | Sirenen, die vor einem Neustart liefen, werden danach ausgeschaltet (nicht während eines Brandes) |
| 0.47 | Namen für RFID-Karten, Finger und Schloss-Kennungen („Schlüsselbund“) – in Nachrichten, Logbuch und Systemübersicht |
| 0.48 | Eigene Dialoge „Karten“ und „PINs“ mit Übersicht wer was hat, Karten deaktivieren, „zuletzt benutzt“, neue Karte am Keypad anlernen ohne Warten; die Code-Entität des Keypads wird deaktiviert (der eingegebene Code stand dort im Klartext; seit 0.58.3 erst nach Bestätigung über eine Reparatur) |
| 0.49 | Aktions-Codes: Code + Taste am Keypad startet eigene Automationen (Ereignis-Entität), schaltet Meldergruppen scharf oder löst einen stillen Notruf aus; Keypad als Gerät auswählen statt MQTT-Topic eintippen |
| 0.50 | Scharf erzwingen am Keypad: bei offenen Meldern innerhalb von 10 s noch einmal bestätigen (Recht je Benutzer) |
| 0.51 | Gastmodus (Schalter, Dienst, Alarmkarte; bis Uhrzeit oder bis aus) – keine Profil-Automatik und keine Erinnerungen; laufenden Alarm nach Neustart fortsetzen (Einstellung, Standard aus); „Alarm vor dem Neustart“ als wichtige Alarm-Nachricht |
| 0.52 | Anlagenübersicht zeigt Gastmodus, Aktions-Codes und das Recht „Scharf erzwingen“; neue Prüfhinweise (stiller Notruf ohne Empfänger, Aktions-Code mit gelöschtem Profil/Keypad, Gastmodus an); Notfallblatt erklärt „trotzdem scharf“ am Keypad |
| 0.53 | [Einrichtungsassistent](assistent.md): kurze Einführung, Melder-Vorschläge nach Etage und Raum, Meldergruppen oder Auslöseregeln, Profile, Empfänger mit Test-Nachricht, Sirenen (ohne Freigabe), Benutzer, Probelauf im Testmodus, weitere Bereiche, Kapitel-Auswahl – jeder Schritt überspringbar; Einstellungsregeln im Kern ([ADR 0009](entwicklung/adr/0009-einrichtungsassistent.md)) |
| 0.54 | Profil-Automatik nach Zeitplan-Helfer: je Wochentag andere Zeiten ohne zweites Profil; Doku-Seite [Beispiele](beispiele.md) für eigene Automationen (Licht, Kamera, Rollläden …) |
| 0.55 | Jedes Ereignis nennt seinen Bereich (`area`, `area_name`); vollständige [Referenz](referenz.md) und Spickzettel [Automationen](automationen.md); bereit für den Katalog von Marketplace/HACS |
| 0.56 | [Gekippte Fenster](melder.md#melder-mit-kippstellung-gekippt) je Profil erlaubt oder wie offen; [Erschütterungsmelder](melder.md#erschütterungsmelder) mit Fehlalarmschutz, auch als Zahl ([ADR 0010](entwicklung/adr/0010-fenster-kippstellung-erschuetterung.md)) |
| 0.57 | [Einstellungsseite](einstellungsseite.md) in der Seitenleiste: alles auf einen Blick, Matrix „Melder × Profile“, alles direkt bearbeiten (Melder, Profile, Auslöseregeln als Formular oder YAML, Sirenen mit Ton, Benachrichtigungen, Personen, Karten, Bedienteile, PIN-Regeln, Aktions-Codes, System), Reiter Dokumentation und „?“ an jedem Abschnitt; [Funkstille je Melder](melder.md#eigene-grenze-je-melder); „Verhalten nach Neustart“ nur bei echtem Neustart ([ADR 0011](entwicklung/adr/0011-einstellungsseite.md)) |
| 0.58 | [Keypads allgemein anbinden](entwicklung/adr/0012-keypads-allgemein.md): ein Eingang für jedes Keypad (Z-Wave, ESPHome, Node-RED …) mit Antwort und Anzeige-Entität, Blueprint Ring Keypad v2 und ESPHome-Beispiel, [MQTT-Schnittstelle](bedienteile.md#mqtt-schnittstelle); Warnungen zu falschen PINs räumen sich auf |
| 0.59 | [Durchgang](durchgang.md) – rein oder raus, ohne unscharf zu schalten ([ADR 0013](entwicklung/adr/0013-durchgang.md)): am Keypad mit jeder Profil-Taste, per Push-Knopf „Reinlassen“, automatisch per Handy, Türschloss, NFC-Aufkleber, Kartenleser |
| 0.60 | Beobachtung [Weggehen](beobachtung.md#weggehen-vorbereitung-für-rausgehen-ohne-pin-erkennen) mit Empfehlung je Person ([ADR 0014](entwicklung/adr/0014-ausgangserkennung.md)); [Messungen](beobachtung.md#messungen-auf-der-einstellungsseite) auf der Einstellungsseite ansehen, speichern, zurücksetzen; [Sirenentest](einstellungsseite.md#sirenentest-auf-der-seite-echte-sirene) auch auf der Einstellungsseite; Sicherheitskorrektur: Richtung „nähert sich“ zählt nicht mehr als „zuhause“ |
| 0.61 | „[Bei Rückkehr](profile.md#bei-rückkehr)“ je Profil (nichts, unscharf, mit Türbeleg, reinlassen) mit eigener Personenliste ([ADR 0015](entwicklung/adr/0015-rueckkehr.md)); [„weg“ nur mit Beleg](profile.md#weg-nur-mit-beleg) – keine falschen Heimkehrten durch schlafende Handys, für Personen ohne Ortung „Tür + Signal“; [Annäherung](profile.md#annäherung-verlängert-die-eingangsverzögerung) verlängert die Eingangsverzögerung; Erklärungen direkt an der Einstellung (ⓘ, „So verhält sich das“); Einstellungsseite ausblenden statt abschalten, Aufruf über die Geräteseite; [Schweigepausen](beobachtung.md#was-ist-eine-schweigepause) erklärt |
| 0.62 | Erklärungen direkt an jeder Einstellung: ⓘ an den Feldern in allen Seitenblättern, der Satz „So verhält sich das:“ und „Mehr Einstellungen“ ([Einstellungsseite](einstellungsseite.md)) |
| 0.63 | [Anwesenheit testen](testmodus.md#anwesenheit-testen) ([ADR 0016](entwicklung/adr/0016-anwesenheit-testen.md)): je Person sehen, warum sie für Hauswacht zuhause, weg oder unbekannt ist, und je Profil, was Automatik und „Bei Rückkehr“ gerade machen (Testkarte und Einstellungsseite); im Testmodus Zuhause, Weg, Weg ohne Beleg, Nähert sich simulieren und „Wartezeit überspringen“; simulierte Türen zählen wie echte. 0.63.1: Doku-Seite [So entscheidet Hauswacht](so-entscheidet-hauswacht.md), Messung „Lebenszeichen rund um die Tür“. 0.63.2: Einstellungsseite ist der einzige Weg – der alte Einstellungsdialog und sein Assistent sind entfallen |

Details zu jeder Version: [CHANGELOG](../CHANGELOG.md).

## Geplant

| Wann | Inhalt |
|---|---|
| 0.64 | Reiter **Assistent** mit **Check-up** ([ADR 0017](entwicklung/adr/0017-assistent-check-up.md)): prüft das Zusammenspiel der Einstellungen mit euren Messwerten, schlägt Verbesserungen vor (einzeln übernehmen); Hinweise direkt in den Seitenblättern; **Szenario-Vorschau** „Was passiert, wenn …?“ mit derselben Logik wie im Echtbetrieb |
| 0.65 | Assistent: **Einrichten nach Zielen** – „nachts absichern“, „automatisch scharf, wenn alle weg sind“, „beim Heimkommen unscharf“ … |
| 0.66 | Ausgangserkennung: wer den PIN beim Rausgehen vergisst, löst keinen Alarm aus, wenn sein Handy kurz danach „weg“ ist – der Alarm wird nur aufgeschoben, nie ohne Beleg unterdrückt |
| bei Bedarf | ZHA-Keypads (frient, Xfinity, Centralite) mit Geräteanpassung für ZHA – sobald jemand mit so einem Gerät mittesten kann |
| demnächst | Ton der HmIP-ASIR je Anlass automatisch wählen (Einbruch, Brand, Test) – wird geprüft |
| später | Entwickler-Dokumentation (Architektur, Tests, ADRs) auf Englisch; englische Screenshots |
| 1.0.0 | Stabil, Doku vollständig (Aufnahme in den Katalog von Marketplace/HACS ist seit 0.55.3 beantragt) |
| irgendwann | Kameras: Bild in der Nachricht, Kamera-Erkennung als eigener Melder-Typ – in Ruhe neu konzipieren |
| 1.x | Eigene Art „Fingerabdruck-Leser“ (Namen je Finger, Mindest-Übereinstimmung) – heute schon über RFID-Leser bzw. Nuki Keypad 2.0 möglich; weitere Automatik-Bedingungen, wiederkehrende Gastmodus-Zeiten (z. B. jeden Dienstag 8–12 Uhr) |

## Grundsätze

- **Hauswacht schaltet keine Geräte** – außer Sirenen (nach Freigabe; für Experten auch als
  Sirene eingetragene Schalter) und den Zustandsanzeigen eingerichteter Keypads.
- **Brandalarm hat Vorrang**, Testmodus sperrt Sirenen technisch. Ein Alarm wird nach einem
  Neustart standardmäßig nicht fortgesetzt; wer das will, schaltet „Laufenden Alarm fortsetzen“
  ein – auch dann gehen Sirenen nur über alle Sirenen-Sperren.
- **Aktions-Codes schalten nie unscharf** und zählen nie als Fehlversuch.
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
