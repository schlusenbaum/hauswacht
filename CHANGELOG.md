# Changelog

Alle relevanten Änderungen an diesem Projekt werden hier dokumentiert.
Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
Versionierung nach [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

## [0.66.0b9] - 2026-11-27

**Ausgangserkennung – Rausgehen ohne PIN erkennen**
([ADR 0014](docs/entwicklung/adr/0014-ausgangserkennung.md)).

### Neu

- **„Rausgehen ohne PIN erkennen“** je Profil (Abschnitt Durchgang, Standard aus) – das
  Sicherheitsnetz, wenn jemand bei scharfem Profil rausgeht und PIN und Durchgang vergisst. Geht
  eine Eingangstür auf, während jemand nachweislich zuhause ist, läuft statt der
  Eingangsverzögerung eine **stille Wartezeit** (1–5 Minuten, Standard 3). Sagt das Handy einer
  Person in der Zeit 30 Sekunden lang „weg“ (Regeln aus „Welche Signale zählen?“), bleibt das
  Profil scharf und die Tür wird bis zum Schließen überbrückt. Sonst gibt es danach Alarm.
- **Sofort eine Nachricht an alle Alarm-Empfänger** mit **[Alarm jetzt]** und **[Durchlassen]**.
- **Melder im Haus** (empfohlen, nicht Pflicht): Bewegungsmelder, Licht oder Schalter. Ist einer
  eingetragen, gilt die stille Wartezeit nur, wenn er kurz vorher etwas gemeldet hat – ein
  Einbruch von außen bekommt die normale Eingangsverzögerung. Ohne Melder im Haus steht ein
  deutlicher Warnhinweis an der Einstellung, im Check-up und in der Szenario-Vorschau.
- **Schutz gegen WLAN-Ausfall:** Sagen mehrere Personen fast gleichzeitig nur über WLAN „weg“,
  zählt das nicht als rausgegangen.
- Wartezeit über 5 Minuten (bis 15) nur als **Expertenoption** mit Warnhinweis.
- Neue Ereignisse `ExitWaitStarted`, `ExitDetected`, `ExitLetThrough`.
- Anleitung mit Beispiel:
  [Rausgehen ohne PIN erkennen](docs/durchgang.md#rausgehen-ohne-pin-erkennen-ausgangserkennung).

### Doku

- **Fehlersuche:** Der Menüpunkt zum Mitlesen heißt in Home Assistant „Unveränderte Protokolle
  anzeigen“ (englisch „Show raw logs“).
- Assistent (Check-up, Szenarien), „So entscheidet Hauswacht“ und Referenz um die
  Ausgangserkennung ergänzt.

## [0.66.0b8] - 2026-11-27

Durchsicht vor dem Abschluss von 0.66.

### Korrigiert

- **Szenario-Vorschau kennt „eines reicht (nach Tür)“.** „Alle gehen weg“ meldete für Personen
  ohne Ortung „wird nie scharf“, obwohl sie mit „eines reicht“ erkannt werden. Jetzt spielt die
  Vorschau die Regel durch: „Jemand geht kurz raus …“ gibt es auch für diese Personen, und mit
  abgeschaltetem „nach Tür“ zeigt „Handys schlafen ein“ ❌.
- **Einrichten nach Zielen:** Personen mit „eines reicht“ gelten im Schritt „Haushalt“ als „kann
  als weg erkannt werden“.
- **Messung „Lebenszeichen rund um die Tür“:** Der Nachklang nach dem Rausgehen zählt nur noch
  bis „alle Signale weg“. Eine Rückkehr kurz danach wurde bisher als langer Nachklang gezählt.

### Doku

- Fehlersuche „Scharf, wenn alle weg schaltet nicht scharf“: Hinweis auf „Welche Signale zählen?“,
  eigenen Auslöser und Wartezeit. Testmodus: neue Belege „Tür + eines der Signale“. Assistent:
  Szenarien mit „eines reicht“. „So entscheidet Hauswacht“: Zeile „Welche Signale zählen?“.
  README: Anwesenheit je Signal. ADR 0021: umgesetzt, mit Nachtrag.

## [0.66.0b7] - 2026-11-27

### Geändert

- **Nur Irrtümer, die länger als die Wartezeit dauern, zählen als „fälschlich“.** Ein kurzer
  WLAN-Schluckauf hätte nie scharf geschaltet – Hauswacht bricht ab, sobald die Person wieder als
  zuhause gilt. Als Wartezeit gilt die des Profils mit „Scharf, wenn alle weg“ (die kürzeste, wenn
  es mehrere sind), sonst 15 Minuten. Kürzere Wartezeit = strengere Empfehlung. Der Kasten
  erklärt, welche Wartezeit gilt und woher sie kommt.
- **Dauer der Irrtümer** unter jedem Signal, z. B. „2 Irrtümer (längster ~40 s)“, und wie viele
  davon länger als die Wartezeit waren.
- **„Was heißt das fürs Haus?“** sagt, wenn kein Profil bei „alle weg“ scharf schaltet, statt
  leer zu bleiben.

### Korrigiert

- **Kurze Irrtümer wurden übersehen.** Die Tür, kurz bevor ein Signal wegfiel, zählte auch als
  Tür bei dessen Rückkehr. Fiel das WLAN nach einer fremden Tür für ein paar Minuten weg, galt
  das deshalb nicht als Irrtum, und „eines reicht“ sah sicherer aus, als es ist. Jetzt zählen
  bei der Rückkehr nur Türen, die **danach** aufgingen.

## [0.66.0b6] - 2026-11-27

### Geändert

- **Empfehlung probiert alle Kombinationen von Signalen.** Bisher prüfte sie „eines reicht (nach
  Tür)“ nur mit allen angehakten Signalen – ein einziges unruhiges Signal (z. B. Bluetooth) machte
  die Empfehlung zunichte. Jetzt sagt sie konkret, was sich ändern soll („Fürs Weggehen abwählen:
  …“), und „Empfehlung übernehmen“ setzt auch diese Haken.
- **Bleibt es bei „alle müssen weg sein“, steht der Grund da**, z. B. „‚Eines reicht (nach Tür)‘
  mit WLAN wäre schneller gewesen (~52 s), aber 1× vermutlich fälschlich“.
- **Vorläufige Zahlen auch mit weniger als 5 Weggängen** – im selben Kasten wie bei den anderen,
  nur ohne Empfehlung und ohne „Übernehmen“. Bisher stand dort nur eine kleine graue Zeile.
- **„Was heißt das fürs Haus?“ nennt Profile mit eigenem Auslöser** („hier entscheidet die
  Entität, keine Nachrechnung“) statt sie wegzulassen.

## [0.66.0b5] - 2026-11-27

**Anwesenheit je Person**, Teil 2: Messwerte und „Was wäre wenn“
([ADR 0021](docs/entwicklung/adr/0021-anwesenheit-je-person.md)).

### Neu

- **Gemessen** unter jedem Signal in „Welche Signale zählen?“: wie schnell es beim Weggehen „weg“
  sagt und wie oft es sich geirrt hat (z. B. „weg nach ~40 s · 1 Irrtum“). Signale, die beim
  Weggehen meist nicht „weg“ sagen, bekommen den Hinweis, sie fürs Weggehen abzuwählen.
- **Empfehlung je Person** mit Vergleich „Jetzt“ gegen „Mit Empfehlung“: erkannt nach wie
  vielen Sekunden oder Minuten, vermutlich fälschlich wie oft, und was ohne „nach Tür“ passiert
  wäre (mit Fällen nachts). Knopf „Empfehlung übernehmen“. Eine Empfehlung gibt es erst ab
  5 Weggängen.
- **„Was heißt das fürs Haus?“**: je Profil mit „Scharf, wenn alle weg“, wie oft es in den letzten
  14 Tagen scharf geworden wäre und wie lange nach der Tür des Letzten – so wie jetzt, mit den
  Empfehlungen und mit 3 Minuten Wartezeit.
- Alles rechnet **live** mit dem Entwurf nach, sobald du einen Haken setzt. Es wird nichts
  gespeichert und nichts geschaltet. Grundlage sind die Messungen der Heimkehr-Beobachtung (nur
  Uhrzeiten, keine Orte).
- Anleitung mit Beispiel:
  [Gemessen, Empfehlung und „Was wäre wenn“](docs/profile.md#gemessen-empfehlung-und-was-wäre-wenn).

## [0.66.0b4] - 2026-11-27

### Geändert

- **Anwesenheit gilt in allen Bereichen gleich.** Weitere Bereiche (z. B. die Garage) haben für
  „Scharf, wenn alle weg“ und „Bei Rückkehr“ bisher nur die Personen-Entität gesehen – nicht die
  zusätzlichen Signale (WLAN, Ping, Bluetooth …), die Heim-WLANs und die Haken unter
  „Welche Signale zählen?“. Jetzt entscheidet jeder Bereich genau wie das Haus, ob jemand
  zuhause oder weg ist. Bei „alle müssen weg sein“ kann die Garage dadurch etwas später scharf
  werden als bisher, weil jetzt alle Signale weg sein müssen. Gemessen wird weiter nur im
  ersten Bereich ([Bereiche](docs/profile.md#bereiche)).

## [0.66.0b3] - 2026-11-27

Zeigen, was wirklich zählt – vor allem beim **eigenen Auslöser für „alle weg“**.

### Neu

- **„Wofür zählt das?“** unter System → Anwesenheit, bei jeder Person: in welchen Profilen sie bei
  „Scharf, wenn alle weg“ oder „Bei Rückkehr“ steht und ob die Beobachtung sie misst. Bei einem
  Profil mit eigenem Auslöser steht dort, dass sie in diesem Profil nicht zählt. Zählt sie
  nirgends, warnt die Seite.
- **Check-up:** zwei neue Tipps.
  - „Personen werden nicht beachtet“: Ein eigener Auslöser ist gesetzt, aber bei „Scharf, wenn
    alle weg“ sind noch Personen angehakt. Mit Vorschlag, sie abzuwählen.
  - „Einstellungen unter Anwesenheit wirken nirgends“: Für eine Person sind Signale oder Regeln
    eingestellt, aber sie steht in keinem Profil und wird nicht beobachtet.
- **Profil:** Ist ein eigener Auslöser gesetzt, steht unter den Personen ein Hinweis, dass sie für
  „alle weg“ nicht beachtet werden. „So verhält sich das:“ nennt die Entität statt der Personen.
- **Doku:** Tabelle „Was beim eigenen Auslöser noch zählt – und was nicht“ unter
  [Eigener Auslöser](docs/profile.md#eigener-auslöser-für-alle-weg).

### Geändert

- Wer bei Weggehen „eines reicht (nach Tür)“ hat, gilt nicht mehr als „kann nie als weg erkannt
  werden“ – auch ohne Ortung. Der Fehler im Check-up und die Markierung „keine Ortung“ im Profil
  entfallen dann.

## [0.66.0b2] - 2026-11-27

### Korrigiert

- **„Welche Signale zählen?“ passt in die Breite.** Lange Signalnamen (z. B. Bermuda-Tracker)
  haben die Tabelle nach rechts aus dem Seitenblatt geschoben, die Spalte „Jetzt“ war
  abgeschnitten. Jetzt brechen lange Namen um, die Spalten mit den Haken haben eine feste Breite.

## [0.66.0b1] - 2026-11-27

**Anwesenheit je Person**, Teil 1 ([ADR 0021](docs/entwicklung/adr/0021-anwesenheit-je-person.md)).

### Neu

- **„Welche Signale zählen?“** unter System → Anwesenheit, im Kasten jeder Person: eine Tabelle
  mit der Person und allen ihren Signalen. Je Signal ein Haken für **Ankommen** und einer für
  **Weggehen**, dazu, was das Signal **jetzt** sagt. Beispiel: Bluetooth nur fürs Ankommen, weil
  es beim Weggehen noch durch die Tür sieht.
- **„Weggehen erkennen“** je Person:
  - **alle müssen weg sein (sicher)** – wie bisher, mit Beleg;
  - **eines reicht (nach Tür)** – eine Eingangstür war auf, danach sagt eines der
    Weggehen-Signale „weg“. Das reicht, ohne Ortung. Kommt genau dieses Signal zurück, gilt die
    Person wieder als zuhause.
  - **Nur nach einer Eingangstür** lässt sich abschalten, dann mit Warnung.
- **„So verhält sich das:“** unter der Tabelle sagt in Klartext, wann die Person als zuhause und
  wann als weg gilt – und ändert sich sofort mit jedem Haken.
- Anleitung mit Beispiel: [Ankommen und Weggehen je Signal](docs/profile.md#ankommen-und-weggehen-je-signal).

### Unverändert

- Wer nichts einstellt, merkt keinen Unterschied: Alle Haken sind gesetzt, Weggehen steht auf
  „alle müssen weg sein“. Ein Test spielt alle Signalfolgen mit alter und neuer Regel durch.
- Das Haus ist weiter erst leer, wenn **alle** Personen weg sind. Der eigene Auslöser im Profil,
  Durchgang, Ausgangserkennung, „Bei Rückkehr“, 24h-Melder und Brandalarm bleiben, wie sie sind.

Messwerte in der Tabelle und die Empfehlung mit „Was wäre wenn“ folgen in den nächsten
Vorabversionen.

## [0.65.0] - 2026-11-27

Zusammenfassung von 0.65.0b1 bis 0.65.0b9 – **Einrichten nach Zielen, Fehlersuche ohne
Datenpreisgabe** ([ADR 0017](docs/entwicklung/adr/0017-assistent-check-up.md),
[ADR 0018](docs/entwicklung/adr/0018-geofence-und-eigener-ausloeser.md),
[ADR 0019](docs/entwicklung/adr/0019-konfiguration-herunterladen.md),
[ADR 0020](docs/entwicklung/adr/0020-debug-log.md)).

### Neu

- **Einrichten nach Zielen** im Reiter Assistent: Statt Einstellung für Einstellung fragt der
  Assistent, was Hauswacht tun soll – nachts absichern, automatisch scharf, wenn alle weg sind,
  beim Heimkommen unscharf, nachts heimkommen, ohne dass „Nacht“ aus ist. Dazu der Schritt
  „Türen und Fenster“ (Melder aufnehmen, Eingangstüren festlegen) und das Ziel „Garage oder
  Werkstatt getrennt“ als **eigener Bereich**. Vor dem Speichern zeigt ein Plan je Profil
  „bisher → neu“ mit Prüfung und Szenario-Vorschau. Vorhandenes wird nur ergänzt, Abschwächendes
  braucht ein Häkchen, Übernehmen geht nur unscharf
  ([Anleitung](docs/assistent.md#einrichten-nach-zielen-seit-0650b1)).
- **„Zählt als Ortung (Geofence)“:** Ein Signal oder Tracker ohne Koordinaten, das den Standort
  auswertet (z. B. Apple Home), lässt sich je Person als Ortung markieren.
- **Eigener Auslöser für „alle weg“:** Im Profil eine Entität und der Zustand, der „alle weg“
  heißt – statt der Personen. Unbekannt oder nicht verfügbar zählt nie als weg
  ([Profile](docs/profile.md#eigener-auslöser-für-alle-weg)).
- **„Warum nicht scharf?“:** „Wer gilt gerade als zuhause?“ sagt bei „kein Beleg“, was fehlt.
- **Konfiguration herunterladen** (Reiter System): eine JSON-Datei für die Fehlersuche.
  Personen, Benutzer, Karten, Empfänger, WLAN-Namen und Geräte stehen darin nur als
  gleichbleibende Platzhalter, PINs und Codes als `***`, Koordinaten nie
  ([Anleitung](docs/einstellungsseite.md#konfiguration-herunterladen)).
- **Debug-Log:** Mit „Debug-Protokollierung aktivieren“ schreibt Hauswacht jede Entscheidung ins
  Log – Melder mit Grund, Zustandswechsel, Anwesenheit je Person, Automatik, Sirenen,
  Benachrichtigungen (nur Empfänger), Eingaben an Bedienteilen (nur „Ausweis ja/nein“). Namen,
  PINs, Codes, Karten, Koordinaten, WLAN-Namen und Nachrichtentexte stehen nie darin
  ([Anleitung](docs/fehlersuche.md#debug-log-was-hat-hauswacht-entschieden)).

### Geändert

- **Sirenen von Rauchmeldern** werden beim Einrichten angeboten – mit 🔥 und dem Hinweis, dass sie
  nur den Einbruchton bekommen und bei Brand gesperrt sind. Sie werden nur eingetragen, nie
  freigegeben; die Brandfunktion bleibt unverändert.
- **Eigener Auslöser:** Liste und Suche in einem Feld.
- **Keine Benutzernamen mehr im Log**, auch nicht in Info- und Warnzeilen. Tests prüfen alle
  Log-Zeilen von Hauswacht auf festen Text ohne Namen, Codes, Karten, Orte oder Texte.

### Korrigiert

- **ⓘ in den Messtabellen** der Systemseite lassen sich auf Handy und Tablet antippen.
- **Vorbereitet auf Home Assistant 2027.9 und 2027.10:** keine veralteten Zugriffe auf die
  Geräte-Registry mehr.

### Doku

- **Fehlersuche:** Debug-Log Schritt für Schritt, live mitlesen unter System → Protokolle, über
  einen Neustart hinweg per `configuration.yaml`; „Hilfe holen“ nennt, was in einen
  Fehlerbericht gehört.
- **ADR 0021 (Diskussion):** Anwesenheit je Person – Signale fürs Ankommen und Weggehen getrennt
  wählen, „eines reicht (nach Tür)“, Empfehlung mit „Was wäre wenn“. Geplant für 0.66.

## [0.65.0b9] - 2026-11-26

### Neu

- **Debug-Log:** Mit „Debug-Protokollierung aktivieren“ (Einstellungen → Geräte & Dienste →
  Hauswacht) schreibt Hauswacht jetzt jede Entscheidung ins Log. Dazu gehören jeder
  Melderwechsel mit Grund (überwacht, überbrückt, unscharf, nicht im Profil), Ereignis und
  Wirkungen der Zustandsmaschine und die Anwesenheit je Person mit Grund. Ebenso stehen dort
  Automatik-Schritte, Sirenen (gesendet und gesperrt), Benachrichtigungen (nur Empfänger) und
  Eingaben an Bedienteilen (nur „Ausweis ja/nein“). Standardmäßig aus. PINs, Codes, Karten,
  Benutzernamen, Koordinaten, WLAN-Namen und Nachrichtentexte stehen nie darin. Die Anleitung
  steht unter [Fehlersuche](docs/fehlersuche.md#debug-log-was-hat-hauswacht-entschieden)
  ([ADR 0020](docs/entwicklung/adr/0020-debug-log.md)).

### Geändert

- **Keine Benutzernamen mehr im Log:** „Falscheingaben zurückgesetzt“, „Durchgang
  reinkommen/rausgehen“ und „Alarm beendet von …“ nannten bisher den Namen. Die letzte Zeile hat
  dafür den ganzen Nachrichtentext ins Log geschrieben. Jetzt heißt sie „Alarm quittiert (Profil
  …)“. Wer es war, steht weiter im Logbuch. Tests prüfen jetzt alle Log-Zeilen von Hauswacht:
  Der Text steht fest im Code, und es kommen keine Namen, Codes, Karten, Orte oder Texte hinein.

## [0.65.0b8] - 2026-11-26

### Neu

- **Konfiguration herunterladen** (Reiter System, ganz unten): eine JSON-Datei für die
  Fehlersuche mit allen Einstellungen, der Übersicht, „Wer gilt gerade als zuhause?“, den Fakten
  aus Home Assistant (wer geortet werden kann, eingefrorene Ortungen …), den Messungen, dem
  Check-up, den Szenarien und dem Zustand der beteiligten Entitäten. Personen, Benutzer, Karten,
  Empfänger, WLAN-Namen, MQTT-Topics, Geräte-IDs und Konten stehen darin nur als
  **gleichbleibende Platzhalter** (`person.person_1`, „Person 1“, `karte_1` …), auch in
  Entitäts-IDs wie `sensor.handy_von_person_1`. PIN-Hashes und Aktions-Codes werden zu `***`,
  Koordinaten sind nie dabei. Eine Fassung ohne Platzhalter gibt es bewusst nicht. Der Knopf liest
  nur und ist nur für Administratoren
  ([ADR 0019](docs/entwicklung/adr/0019-konfiguration-herunterladen.md)).

## [0.65.0b7] - 2026-11-26

### Korrigiert

- **ⓘ in den Messtabellen der Systemseite lassen sich antippen.** Bei „Heimkehr messen“ und
  „Vorbereitung Ausgangserkennung“ zeigten die ⓘ an den Spaltenköpfen ihre Erklärung nur mit dem
  Mauszeiger; auf Handy und Tablet passierte nichts. Jetzt erscheint die Erklärung nach dem
  Antippen direkt unter der Tabelle, nochmal Antippen blendet sie aus – wie bei allen anderen ⓘ.

## [0.65.0b6] - 2026-11-26

### Korrigiert

- **Vorbereitet auf Home Assistant 2027.9 und 2027.10:** Die Geräteauswahl der Bedienteile nutzt
  keine veralteten Zugriffe auf die Geräte-Registry mehr (`device_registry.devices` wie ein
  Wörterbuch, `DeviceEntry.config_entries`). Home Assistant hatte dazu Warnungen ins Log
  geschrieben; ab 2027.9 bzw. 2027.10 wäre die Auswahl sonst ausgefallen. Für dich ändert sich
  nichts.

## [0.65.0b5] - 2026-11-26

### Geändert

- **Eigener Auslöser für „alle weg“: Liste und Suche in einem.** Ein Klick ins Feld zeigt alle
  passenden Entitäten zum Durchblättern, sortiert nach Art (Schalter, Gruppen, Binärsensoren);
  Tippen filtert nach Name oder Entitäts-ID. Darunter steht, welche Entität gewählt ist, mit
  „Entfernen“.

## [0.65.0b4] - 2026-11-26

Geofence als Ortung, eigener Auslöser für „alle weg“, „Warum nicht scharf?“
([ADR 0018](docs/entwicklung/adr/0018-geofence-und-eigener-ausloeser.md)). Anlass: Rückmeldung aus
dem Test – „Scharf, wenn alle weg“ griff mit Geofence-Trackern ohne Koordinaten nie.

### Neu

- **„Zählt als Ortung (Geofence)“:** Unter System → Anwesenheit lässt sich je Person ein Signal oder
  Tracker ohne Koordinaten als Ortung markieren – für Quellen, die den Standort auswerten (z. B.
  Anwesenheit aus Apple Home über einen Template-Tracker). „Weg“ ist dann ein Beleg wie eine
  frische, genaue Ortung. Nicht für WLAN, Ping oder Bluetooth (Hinweis an der Einstellung).
- **Eigener Auslöser für „alle weg“:** Im Profil unter Automatik → „Mehr Einstellungen“ eine
  Entität (Schalter, Binärsensor, Gruppe) und den Zustand, der „alle weg“ heißt. Sie gilt statt
  der Personen; unbekannt oder nicht verfügbar zählt nie als weg. Hauswacht prüft dann nicht
  selbst – dazu eine Warnung im Assistenten und an der Einstellung.
- **„Warum nicht scharf?“:** „Wer gilt gerade als zuhause?“ sagt bei „kein Beleg“, was fehlt
  (keine Ortung, Ortung nicht frisch oder nicht draußen, bei „Tür + Signal“ letzte Tür und wann das
  Signal wegfiel), mit Knopf **Aktualisieren**.

## [0.65.0b3] - 2026-11-25

Garage als eigener **Bereich** statt als Profil.

### Geändert

- **„Garage oder Werkstatt getrennt“ legt einen eigenen Bereich an** (mit eigenem Bedienfeld
  `alarm_control_panel.hauswacht_garage`) – unabhängig vom Haus scharf, z. B. nachts, während im
  Haus jemand wach ist. In 0.65.0b2 war die Garage ein Profil im Haus; da in einem Bereich immer
  nur ein Profil aktiv ist, schlossen sich „Garage“ und „Nacht“ gegenseitig aus.
- Im Bereich Garage: Meldergruppe „Garage“ und ein Profil mit dem Knopf „Abwesend“ („Alle Bereiche
  → Abwesend“ schaltet die Garage mit); auf Wunsch „Scharf, wenn alle weg“ mit denselben Personen
  wie im Haus und Uhrzeiten. Ein vorhandener Bereich „Garage“ wird ergänzt.
- **Melder in beiden Bereichen:** Melder aus einer Haus-Gruppe kommen in die Gruppe „Garage“; jedes
  Haus-Profil, das die bisherige Gruppe überwacht, bekommt „Garage“ dazu – im Haus ändert sich
  nichts.
- Die Ziele „Nachts absichern“ und „Abwesend“ meinen immer die Profile des Hauses (Hauptbereich),
  nie die eines anderen Bereichs. Ein Profil hat im Plan genau einen Schritt.

## [0.65.0b2] - 2026-11-25

Einrichten nach Zielen: Türen und Fenster, Garage getrennt, Rauchmelder als Sirenen.

### Neu

- **Schritt „Türen und Fenster“** (nach Etage und Raum): Melder, die noch in keiner Meldergruppe
  stehen, aufnehmen (nichts vorausgewählt – überwacht wird nur, was du wählst) – Türen und Fenster in die Gruppe für außen, Bewegungsmelder in die für innen
  (vorhanden oder neu „Außen“/„Innen“). Dazu festlegen, welche Türen **Eingangstüren** mit
  Eingangsverzögerung sind; alle anderen lösen sofort aus (z. B. Terrassentür).
- **Ziel „Garage oder Werkstatt getrennt“:** eigene Meldergruppe und eigenes Profil „Garage“ mit
  den gewählten Meldern, auf Wunsch auch im Abwesend-Profil. Melder aus anderen Gruppen wechseln
  in die Garage (im Plan markiert); eine Gruppe wird nie leer geräumt.

### Geändert

- **Sirenen von Rauchmeldern werden beim Einrichten angeboten** – mit 🔥 und dem Hinweis, dass sie
  als Einbruchsirene nur den Einbruchton bekommen und bei Brand gesperrt sind. Sie werden nur
  eingetragen, nie freigegeben; die Brandfunktion bleibt unverändert. In 0.65.0b1 wurden sie gar
  nicht angeboten – in Häusern, deren einzige Sirenen Rauchmelder sind, stand dort dann „Keine
  Sirene gefunden“.

## [0.65.0b1] - 2026-11-25

**Einrichten nach Zielen** im Reiter Assistent ([ADR 0017](docs/entwicklung/adr/0017-assistent-check-up.md)).

### Neu

- **Einrichten nach Zielen:** Statt Einstellung für Einstellung fragt der Assistent, was Hauswacht
  tun soll – in fünf Schritten: Haushalt (wer kann als weg erkannt werden), Ziele, Rückfragen,
  Sirenen und Empfänger, Plan.
- **Ziele:** nachts absichern (Profil „Nacht“, auf Wunsch mit Uhrzeiten); automatisch scharf, wenn
  alle weg sind (Profil „Abwesend“); beim Heimkommen unscharf („Bei Rückkehr“, empfohlen mit
  Türbeleg, Eingangsverzögerung nach euren Messungen); nachts heimkommen, ohne dass „Nacht“ aus
  ist (Reinlassen). Fehlt das Profil, legt der Assistent es an.
- **Plan vor dem Speichern:** je Profil „bisher → neu“, Hinweise, die Prüfung und die
  Szenario-Vorschau für die Einstellungen, wie sie danach wären. Vorhandenes wird nur ergänzt;
  was überschrieben würde oder die Anlage nachgiebiger macht, ist mit ⚠ markiert und braucht ein
  Häkchen.
- **Sicherungen:** Übernehmen nur unscharf; Hauswacht rechnet den Plan aus den Antworten neu
  (dieselben Regeln wie im Seitenblatt). Sirenen werden nur eingetragen, nie freigegeben;
  Rauchmelder-Sirenen werden nie angeboten.
- Doku: [Einrichten nach Zielen](docs/assistent.md#einrichten-nach-zielen-seit-0650b1) mit Beispiel.

## [0.64.0] - 2026-11-25

Zusammenfassung von 0.64.0b1 bis 0.64.0b5 – **der Assistent**
([ADR 0017](docs/entwicklung/adr/0017-assistent-check-up.md)).

### Neu

- **Hinweise beim Bearbeiten:** Im Seitenblatt eines Alarmprofils und unter System → Anwesenheit
  zeigt der Assistent schon vor dem Speichern, was nicht zusammenpasst – mit Begründung, Messwert
  und Vorschlag. Nur Hinweis: Speichern geht trotzdem. Fehler stehen auch in den Prüfhinweisen.
- **Prüfungen:** Person ohne Ortung in „Scharf, wenn alle weg“ oder „Bei Rückkehr“;
  „Unscharf, nur wenn automatisch scharf“ ohne Automatik; Türbeleg/Reinlassen ohne Eingangstür;
  Eingangsverzögerung kürzer als gemessen (auch für den Türbeleg einer Person); Verlängerung bei
  Annäherung ohne Richtungs-Signal; „Tür + Signal“ trotz Ortung; eingefrorene Ortung.
- **Reiter „Assistent“ mit Check-up:** alle Befunde auf einen Blick, nach Profil sortiert.
  Vorschläge einzeln übernehmen, mit Vorschau „bisher → neu“; abschwächende Vorschläge (⚠) nur
  mit Häkchen. Übernehmen nur unscharf, nur aktuelle Vorschläge, über denselben Weg wie im
  Seitenblatt.
- **Szenario-Vorschau „Was passiert, wenn …?“:** Einbruch durch jede Tür und ein Fenster, jede
  Person kommt heim (mit gemessener Zeit), alle gehen weg, Handys schlafen ein, kurz raus bei
  „Tür + Signal“ – durchgespielt mit denselben Regeln wie im Echtbetrieb, ausgedachte Uhr, nichts
  wird geschaltet. Ergebnis ✅ / ⚠️ / ❌ mit Ablauf Schritt für Schritt.
- **Eingefrorene Ortung:** 24 Stunden exakt dieselbe Position außerhalb von Zuhause zählt nicht
  als Beleg für „weg“ (vorgetäuschter Standort, hängende App) – bis sie sich wieder bewegt.

### Geändert

- Die Entscheidungen der Profil-Automatik stehen an einer Stelle im Kern
  (`core/automation_engine.py`) – Echtbetrieb und Vorschau nutzen dieselben Regeln.
- „Scharf, wenn alle weg“ plant nur noch, solange die Anlage unscharf ist (keine doppelten
  `AutoArmScheduled`/`AutoArmSkipped` mehr nach dem automatischen Scharfschalten).

### Korrigiert

- Installationsanleitung nannte beim Wegfall des alten Einstellungsdialogs die falsche Version.

## [0.64.0b5] - 2026-11-25

Eingefrorene Ortung erkennen; „alle weg“ plant nach dem Scharfschalten nicht mehr neu.

### Neu

- **Ortung, die sich nie bewegt:** Meldet eine Ortung seit mindestens 24 Stunden exakt dieselbe
  Position außerhalb von Zuhause (vorgetäuschter Standort, hängende App), zählt sie nicht mehr als
  Beleg für „weg“ und nicht als „kann geortet werden“ – bis sie sich wieder bewegt. Hauswacht
  merkt sich das auch über einen Neustart hinweg. Der Assistent zeigt dazu eine Warnung (Check-up
  und Seitenblatt Anwesenheit). Ortungen zuhause sind nie betroffen.

### Geändert

- **„Scharf, wenn alle weg“ plant nur noch, solange die Anlage unscharf ist.** Bisher wurde nach
  dem automatischen Scharfschalten bei jeder Signaländerung neu geplant und nach der Wartezeit
  wieder verworfen (Ereignisse `AutoArmScheduled` und `AutoArmSkipped` im Logbuch). Gefunden mit
  der Szenario-Vorschau. Am Verhalten ändert sich sonst nichts: Wird aus der Ferne unscharf
  geschaltet, während alle weg sind, plant die nächste Signaländerung wie bisher neu.

## [0.64.0b4] - 2026-11-25

Szenario-Vorschau „Was passiert, wenn …?“ im Reiter Assistent ([ADR 0017](docs/entwicklung/adr/0017-assistent-check-up.md)).

### Neu

- **Was passiert, wenn …?** Unter dem Check-up spielt Hauswacht typische Situationen mit deinen
  Einstellungen und Messwerten durch – mit denselben Regeln wie im Echtbetrieb (Zustandsmaschine,
  Automatik, Beleg für „weg“), aber mit ausgedachter Uhr. Es wird nichts geschaltet.
- Szenarien je Profil: Einbruch durch jede Eingangstür und durch ein Fenster; jede Person aus
  „Bei Rückkehr“ kommt heim (mit ihrer gemessenen Zeit nach der Tür, ab 3 Messungen); alle gehen
  weg; alle sind zuhause und die Handys schlafen ein (auch: WLAN fällt aus); bei „Tür + Signal“:
  jemand geht kurz raus, und dabei schläft ein Handy ein.
- Jedes Szenario mit Ergebnis ✅ / ⚠️ / ❌, einem Satz dazu und dem Ablauf Schritt für Schritt.
- Doku: [Was passiert, wenn …?](docs/assistent.md#was-passiert-wenn--seit-0640b4) mit allen
  Szenarien, Beispiel und dem, was vereinfacht ist.

## [0.64.0b3] - 2026-11-25

Neuer Reiter **Assistent** mit dem Check-up ([ADR 0017](docs/entwicklung/adr/0017-assistent-check-up.md)).

### Neu

- **Check-up:** Der Reiter „Assistent“ auf der Einstellungsseite zeigt alle Befunde des
  Assistenten auf einen Blick – für alle Profile und die allgemeinen Einstellungen, nach Profil
  sortiert, mit Zusammenfassung („1 Fehler · 2 Warnungen · 0 Tipps“ oder „Alles passt zusammen“)
  und Knopf „Neu prüfen“.
- **Vorschläge einzeln übernehmen, mit Vorschau:** Ein Klick zeigt, wo und was sich ändert
  („bisher 30 → neu 50“, „kommt dazu“, „fällt weg“). Erst „Übernehmen“ speichert genau diese eine
  Änderung. Vorschläge mit ⚠ (machen die Anlage nachgiebiger) brauchen zusätzlich ein Häkchen.
- **Sicherungen beim Übernehmen:** nur, wenn alle Bereiche unscharf sind; nur ein Vorschlag, den
  der Assistent gerade jetzt selbst macht; hat sich inzwischen etwas geändert, wird nichts
  gespeichert und der Check-up lädt neu. Gespeichert wird über denselben Weg wie im Seitenblatt.
- Doku: [Check-up im Reiter „Assistent“](docs/assistent.md#check-up-im-reiter-assistent-seit-0640b3).

## [0.64.0b2] - 2026-11-25

Der Assistent schaut beim Bearbeiten mit ([ADR 0017](docs/entwicklung/adr/0017-assistent-check-up.md)).

### Neu

- **Hinweise des Assistenten im Seitenblatt:** Im Seitenblatt eines Alarmprofils und unter
  System → Anwesenheit erscheint über „Speichern“ ein Kasten **Assistent**, sobald etwas nicht
  zusammenpasst – geprüft wird der Entwurf, wie er nach dem Speichern wäre. Nur Hinweis:
  Speichern geht trotzdem. Jeder Hinweis sagt, was nicht passt, und unter „Warum?“ die
  Begründung, mit Messwert aus der Beobachtung, wenn es einen gibt.
- Erste Prüfungen: Person ohne Ortung in „Scharf, wenn alle weg“ (Profil wird nie scharf) oder
  in „Bei Rückkehr“; „Unscharf, nur wenn automatisch scharf“ ohne Automatik; Türbeleg oder
  Reinlassen ohne Eingangstür; Eingangsverzögerung kürzer als gemessen nötig (auch für den
  Türbeleg einer Person); Verlängerung bei Annäherung ohne Richtungs-Signal; „Tür + Signal“
  trotz Ortung. Messwerte zählen ab 3 Messungen.
- **Vorschläge als Knopf:** Ein Klick ändert nur den Entwurf, gespeichert wird erst mit
  „Speichern“. Vorschläge, die die Anlage nachgiebiger machen (z. B. längere
  Eingangsverzögerung), sind mit ⚠ markiert und brauchen eine ausdrückliche Bestätigung.
- Fehler des Assistenten stehen auch in den **Prüfhinweisen**.
- Doku: [Assistent und Einrichtung](docs/assistent.md#hinweise-beim-bearbeiten-seit-0640b2) mit
  allen Prüfungen und Beispielen.

### Korrigiert

- Installationsanleitung: „Seit 0.63.2 gibt es den früheren Einstellungsdialog nicht mehr“ nannte
  in 0.64.0b1 versehentlich die falsche Version.

## [0.64.0b1] - 2026-11-25

Erster Schritt zum Assistenten mit Check-up und Szenario-Vorschau
([ADR 0017](docs/entwicklung/adr/0017-assistent-check-up.md)) – **ohne sichtbare Änderung**.

### Geändert

- Die Entscheidungen der Profil-Automatik („alle weg“, „Bei Rückkehr“, Türbeleg, Reinlassen,
  Annäherung) stehen jetzt an einer Stelle im Kern (`core/automation_engine.py`). Der Echtbetrieb
  und die kommende Szenario-Vorschau nutzen damit **dieselben** Regeln. Das Verhalten ist
  unverändert – alle bisherigen Tests laufen unverändert durch, dazu neue Tests für jede Regel.

## [0.63.2] - 2026-11-25

Zusammenfassung von 0.63.2b1 – **die Einstellungsseite ist der einzige Weg**.

### Geändert

- Der frühere Einstellungsdialog ist entfallen; „Konfigurieren“ zeigt nur noch einen Link zur
  Einstellungsseite und ändert nichts. Deine Einstellungen bleiben unverändert.
- Installation in einem Schritt mit Link zur Einstellungsseite.
- Hinweise in Home Assistant und die ganze Doku nennen die Stellen auf der Einstellungsseite.

### Entfernt

- Einrichtungsassistent im Dialog – ein neuer auf der Einstellungsseite ist geplant.

## [0.63.2b1] - 2026-11-25

### Geändert

- **Die Einstellungsseite ist der einzige Weg.** Der frühere Einstellungsdialog (Einstellungen →
  Geräte & Dienste → Hauswacht → **Konfigurieren**) ist entfallen. „Konfigurieren“ zeigt nur noch
  einen Hinweis mit Link zur Einstellungsseite und ändert nichts. Die Seite kann alles, was der
  Dialog konnte; **deine Einstellungen bleiben unverändert**.
- **Installation:** ein einziger Schritt mit Link zur Einstellungsseite. Eingerichtet wird danach
  alles auf der Seite – der Weg dahin steht unter
  [In fünf Schritten zur ersten Scharfschaltung](docs/installation.md#in-fünf-schritten-zur-ersten-scharfschaltung).
- Einstellungsseite: Der Knopf „Im Dialog bearbeiten“ ist weg; der Hinweis oben verweist auf
  „So entscheidet Hauswacht“.
- Hinweise in Home Assistant (Reparaturen, Fehlermeldungen) nennen jetzt die Stelle auf der
  Einstellungsseite statt des Dialogs.
- Doku überall auf die Einstellungsseite umgestellt (Installation, Melder, Profile, Auslöseregeln,
  Sirenen, Benachrichtigungen, Benutzer, Bedienteile, Durchgang, Beobachtung, Fehlersuche).

### Entfernt

- **Einrichtungsassistent im Dialog.** Ein neuer Assistent direkt auf der Einstellungsseite ist
  geplant – siehe [Einrichtungsassistent](docs/assistent.md).

## [0.63.1] - 2026-11-25

Zusammenfassung von 0.63.1b1.

### Hinzugefügt

- **Doku-Seite [So entscheidet Hauswacht](docs/so-entscheidet-hauswacht.md)**: der Überblick in
  Bildern – Tür auf, Automatik, Heimkommen, zuhause oder weg, was Hauswacht nie von selbst tut,
  wo man was einstellt.
- **Messung „Lebenszeichen rund um die Tür“** (Vorbereitung der Ausgangserkennung): Lebenszeichen
  vor dem Rausgehen, „noch da“ nach der Tür, „zuhause“ nach dem Rausgehen – schaltet nichts.
  Doku: [Lebenszeichen rund um die Tür](docs/beobachtung.md#lebenszeichen-rund-um-die-tür).

## [0.63.1b1] - 2026-11-25

### Hinzugefügt

- **Neue Doku-Seite [So entscheidet Hauswacht](docs/so-entscheidet-hauswacht.md)**: der Überblick
  in Bildern – was passiert, wenn bei scharfer Anlage eine Tür aufgeht, wann die Automatik
  schaltet, was beim Heimkommen passiert, wann jemand als zuhause oder weg gilt, was Hauswacht
  nie von selbst tut und wo man was einstellt. Auch im Reiter „Dokumentation“ der
  Einstellungsseite.
- **Messung „Lebenszeichen rund um die Tür“** (Vorbereitung der Ausgangserkennung, ADR 0014) in
  der Heimkehr-Beobachtung – schaltet nichts:
  - **Lebenszeichen vor dem Rausgehen:** Hatte, wer rausgeht, kurz vorher ein Signal mit
    „zuhause“? Nur dann kann die Ausgangserkennung die Person später erkennen.
  - **„Noch da“ nach der Tür:** Wie schnell meldet sich das Handy von jemandem, der zuhause
    bleibt, nach dem Öffnen wieder? So lange bliebe ein Einbruch höchstens still.
  - **„Zuhause“ nach dem Rausgehen:** Melden Signale nach dem Öffnen noch „zuhause“, obwohl die
    Person gerade geht (z. B. Ping mit Nachlaufzeit)?
  Zu sehen auf der Einstellungsseite (System → Anwesenheit → Messungen, Tabelle „Vorbereitung
  Ausgangserkennung“), im Bericht und im Attribut `exit_checks`. Gemessen wird ab diesem Update;
  „Weggehen zurücksetzen“ löscht auch diese Messung. Doku:
  [Lebenszeichen rund um die Tür](docs/beobachtung.md#lebenszeichen-rund-um-die-tür).

## [0.63.0] - 2026-11-24

Zusammenfassung von 0.63.0b1 bis 0.63.0b3 – **Anwesenheit testen** ([ADR 0016](docs/entwicklung/adr/0016-anwesenheit-testen.md)).

### Hinzugefügt

- **Block „Anwesenheit“ in der Testkarte**: je Person zuhause, weg oder unbekannt und warum
  (welches Signal, welcher Beleg, „kein Beleg“) – auch ohne Testmodus.
- **Zeile je Profil**: was Automatik und „Bei Rückkehr“ gerade machen – „wird scharf, wenn
  alle weg sind. Noch nicht weg: …“, „alle weg, wird scharf in 4:12“, „ist scharf
  (automatisch)“, „Heimkehr erkannt, wartet auf die Tür (noch 4:30)“, „nicht nötig, ‚Nacht‘
  ist scharf“.
- **Anwesenheit simulieren** im Testmodus: Zuhause, Weg, Weg ohne Beleg, Nähert sich, Echt –
  nur für Hauswacht; Testmodus aus oder Neustart setzt alles zurück.
- **„Wartezeit überspringen“** für eine laufende „alle weg“-Wartezeit.
- Einstellungsseite, System → Anwesenheit: **„Wer gilt gerade als zuhause?“**.
- Aktionen `hauswacht.simulate_presence`, `hauswacht.skip_wait`, Ereignis `PresenceSimulated`.
- Doku: [Anwesenheit testen](docs/testmodus.md#anwesenheit-testen) mit Beispielen.

### Geändert

- **Simulierte Eingangstüren zählen wie echte**: für „Bei Rückkehr“ (Türbeleg, Durchgang)
  und als Beleg für „weg“ (Tür + Signal).

## [0.63.0b3] - 2026-11-24

### Behoben

- **Simulierte Türen zählen jetzt wie echte**: Eine im Testmodus auf „Auf“ gestellte (oder
  kurz ausgelöste) Eingangstür gilt auch für „Bei Rückkehr“ (Türbeleg, Durchgang) und als
  Beleg für „weg“ (Tür + Signal). Vorher kam sie nur in der Alarmlogik an – „Unscharf mit
  Türbeleg“ ließ sich im Testmodus nicht ausprobieren.

### Geändert

- Testkarte und Einstellungsseite: klarere **Zeile je Profil**. Statt „wartet auf: Christian“
  steht dort jetzt zum Beispiel „Abwesend – wird scharf, wenn alle weg sind. Noch nicht weg:
  Christian“, „ist scharf (automatisch)“ oder „nicht nötig, ‚Nacht‘ ist scharf“.
- Die Zeile zeigt auch, worauf **„Bei Rückkehr“** gerade wartet: „Heimkehr erkannt, wartet
  auf die Tür (noch 4:30)“ oder „Tür gesehen, wartet auf eine Heimkehr (noch 4:50)“.

## [0.63.0b2] - 2026-11-24

### Behoben

- Testkarte: Nach „Nähert sich“ und dann „Zuhause“ stand weiter „nähert sich“ hinter der
  Person. Wer zuhause ist, nähert sich nicht mehr – der Hinweis verschwindet jetzt. Nach
  „Weg“, „Weg ohne Beleg“ oder „Echt“ wird eine simulierte Annäherung ganz verworfen.

## [0.63.0b1] - 2026-11-24

### Hinzugefügt

- **Anwesenheit in der Testkarte** (ADR 0016): Block „Anwesenheit“ mit jeder Person – zuhause,
  weg oder unbekannt und **warum** (welches Signal, welcher Beleg, „kein Beleg“). Darüber je
  Profil mit Automatik, was „alle weg“ gerade macht („scharf in 4:12“ oder „wartet auf …“).
  Sichtbar auch ohne Testmodus.
- **Anwesenheit simulieren** im Testmodus: Zuhause, Weg, Weg ohne Beleg, Nähert sich, Echt –
  nur für Hauswacht, Personen in Home Assistant bleiben unverändert. Testmodus aus oder
  Neustart setzt alles zurück.
- Knopf **„Wartezeit überspringen“** beendet eine laufende „alle weg“-Wartezeit sofort.
- Aktionen `hauswacht.simulate_presence` und `hauswacht.skip_wait`, Ereignis
  `PresenceSimulated`.
- Einstellungsseite, System → Anwesenheit: **„Wer gilt gerade als zuhause?“** mit demselben
  Stand.
- Doku: [Anwesenheit testen](docs/testmodus.md#anwesenheit-testen).

## [0.62.0] - 2026-11-24

**Erklärungen direkt an jeder Einstellung** (getestet über die Vorabversionen 0.62.0b1 bis b3).

### Hinzugefügt
- Einstellungsseite: **ⓘ an den Feldern** in allen Seitenblättern – Profile, System, Melder,
  Auslöseregeln, Alarmgeber und Benachrichtigungen, Personen, Bedienteile. Mauszeiger drauf
  zeigt die Erklärung, Antippen klappt sie auf.
- **„So verhält sich das:“** – ein Satz, der sich beim Einstellen sofort ändert: im Profil
  (Zeiten, Scharfschalten, Reaktion, Automatik, Bei Rückkehr, Scharf durch Schließen, Durchgang)
  und im System (Neustart, Funkstille, PIN-Regeln, Aktions-Codes, Melder aus Messwert,
  Anlernzeit).
- Roadmap: ADR 0016 „Anwesenheit in der Testkarte“ für 0.63; die Ausgangserkennung rückt auf
  0.64.

### Geändert
- Profil: Selten geänderte Felder stehen unter **„Mehr Einstellungen“**; Ausgangstüren und
  Durchgangszeiten erscheinen erst, wenn der Schalter dazu an ist.

### Behoben
- Sirenentest: falsche Beschriftung am Feld „Erinnerung, wenn eine Sirene so lange nicht
  getestet wurde“.

## [0.62.0b3] - 2026-11-24

**Vorabversion: Erklärungen überall** (Roadmap 0.62, Schritt 3).

### Hinzugefügt
- Einstellungsseite: **ⓘ an den Feldern** auch bei Meldergruppen und Meldern (Kippstellung,
  Erschütterung, Immer aktiv), Auslöseregeln, Alarmgebern und Benachrichtigungen (Sirenen,
  Empfänger, Ansagen, Erinnerung), Personen und Bedienteilen (Keypad, Aufkleber, Leser, Taster,
  Türschloss, Karten).

### Behoben
- Alarmgeber → Sirenentest: Das Feld „Erinnerung, wenn eine Sirene so lange nicht getestet
  wurde“ trug die falsche Beschriftung („Erinnerung „Alle weg, aber nicht scharf““).

## [0.62.0b2] - 2026-11-24

**Vorabversion: Erklärungen in den Systemeinstellungen** (Roadmap 0.62, Schritt 2).

### Hinzugefügt
- Einstellungsseite → System: **ⓘ an jedem Feld** in allen Seitenblättern (Neustart,
  Funkstille, Funknetz, Anwesenheit, Bereiche, PIN-Regeln, Aktions-Codes, Melder aus Messwert,
  Anlernzeit).
- **„So verhält sich das:“** bei Neustart, Funkstille, PIN-Regeln, Aktions-Codes, Melder aus
  Messwert und Anlernzeit – ändert sich mit den Einstellungen.
- Roadmap: ADR 0016 „Anwesenheit in der Testkarte“ für 0.63; die Ausgangserkennung rückt auf 0.64.

## [0.62.0b1] - 2026-11-24

**Vorabversion: Erklärungen im Profil** (Roadmap 0.62, Schritt 1).

### Hinzugefügt
- Einstellungsseite → Profil: **ⓘ an jedem Feld** (Mauszeiger oder antippen) mit einer
  Erklärung in einfacher Sprache.
- Je Abschnitt der Satz **„So verhält sich das:“**, der sich beim Einstellen sofort ändert
  (Zeiten, Scharfschalten, Reaktion, Automatik, Bei Rückkehr, Scharf durch Schließen, Durchgang).

### Geändert
- Selten geänderte Felder stehen unter **„Mehr Einstellungen“** zum Aufklappen (Symbol, Dauer
  der Alarmreaktion, Alarmzyklen, ausgefallene Melder, Manipulation, Ton, Lautstärke,
  Lautsprecher, Zeitplan, Beruhigungszeit, Durchgang „welche Tür“ und „Ende“).
- Ausgangstüren und Durchgangszeiten erscheinen erst, wenn der Schalter dazu an ist.

## [0.61.0] - 2026-11-24

**„Bei Rückkehr“ je Profil, „weg“ nur mit Beleg, Annäherung verlängert die
Eingangsverzögerung, Einstellungsseite ausblenden statt abschalten** (ADR 0015 und ADR 0011
Nachtrag, getestet über die Vorabversionen 0.61.0b1 bis b5).

### Sicherheit
- **„weg“ nur mit Beleg:** Ein schlafendes Handy macht niemanden mehr abwesend. Eine Person gilt
  für „Scharf, wenn alle weg“, „Bei Rückkehr“ und das Reinlassen erst als weg, wenn alle Signale
  „weg“ melden **und** es einen Beleg gibt: Eingangstür auf und danach (bis 15 Minuten) Ortung
  außerhalb, oder eine frische (letzte 15 Minuten), genaue Ortung außerhalb. WLAN, Ping, Router
  und Bluetooth bestätigen nur. Damit gibt es auch keine falsche „Heimkehr“ mehr, wenn nachts das
  WLAN eines Handys im Haus wegfällt. Die Heimkehr-Beobachtung zählt genauso.
- Korrekturen aus 0.60.1 (HACS-Review): Attribute maskieren, Personen-IDs in der Diagnose
  schwärzen.

### Hinzugefügt
- **„Bei Rückkehr“** je Profil – eine Einstellung statt zwei: Nichts · Unscharf, nur wenn
  automatisch scharf · Unscharf mit Türbeleg · Unscharf, auch nach Scharfschalten von Hand (nur
  Handy, mit Warnung) · Reinlassen (Durchgang, das Profil bleibt scharf). Eigene Personenliste;
  ⓘ-Erklärungen, der Satz „So verhält sich das:“ und „Mehr Einstellungen“ auf der
  Einstellungsseite.
- **Annäherung verlängert die Eingangsverzögerung** (bei „Unscharf mit Türbeleg“ und
  „Reinlassen“): Hat sich eine Person aus der Liste vorher genähert (Richtung „nähert sich“),
  wartet Hauswacht nach dem Öffnen länger auf ihr Handy; Empfehlungen aus der Messung zum
  Übernehmen; Ereignis `EntryDelayExtended`.
- **„Wann gilt jemand als weg?“** unter System → Anwesenheit: Ortung genau prüfen oder einfach,
  Zeitfenster für den Beleg; je Person **„auch Tür + Signal (unsicher)“** für Personen ohne
  Ortung, mit Warnhinweis und Prüfhinweis; Hinweis „⚠ keine Ortung – gilt nie als weg“.
- Messungen: ⓘ an jeder Spalte und „Was bedeuten die Spalten?“; Doku „Was ist eine
  Schweigepause?“.

### Geändert
- Die Einstellungsseite gibt es immer; die Einstellung heißt „In der Seitenleiste zeigen“. Der
  Link auf der Geräteseite und ganz oben im Dialog „Konfigurieren“ führt zur Einstellungsseite.
- „Unscharf bei Rückkehr“ und das Handy-Reinlassen sind nach „Bei Rückkehr“ umgezogen (nur auf
  der Einstellungsseite). Bestehende Einstellungen werden übernommen; waren beide an, gewinnt
  „Reinlassen“, mit Benachrichtigung.

### Behoben
- Weggehen: Ein „weg“ ohne Tür in den ersten 15 Minuten nach dem Zurücksetzen zählt nicht mehr
  als Schweigepause.

## [0.61.0b5] - 2026-11-24

**Vorabversion: Messungen besser erklärt.**

### Behoben
- Weggehen: Ein „weg“ ohne Tür in den ersten 15 Minuten nach dem Zurücksetzen aller Messungen
  (oder dem Start der Beobachtung) zählt nicht mehr als Schweigepause. Die Tür kann kurz vor dem
  Zurücksetzen aufgegangen sein – bisher wurde ein ganz normales Weggehen so zur langen Pause.

### Hinzugefügt
- Einstellungsseite → Messungen: ⓘ an jeder Spalte (Mauszeiger) und „Was bedeuten die
  Spalten?“ zum Aufklappen.
- Doku: neuer Abschnitt „Was ist eine Schweigepause?“ mit den drei typischen Ursachen (Handy
  schläft, Signal zu langsam, Tür ohne Kontakt), Beispiel und Tipp für iCloud3.

## [0.61.0b4] - 2026-11-23

**Vorabversion: Einstellungsseite ausblenden statt abschalten** (ADR 0011 Nachtrag 0.61, Schritt 4
von 4).

### Geändert
- Die Einstellungsseite gibt es jetzt **immer** (nur Administratoren). Die Einstellung heißt
  „**In der Seitenleiste zeigen**“: Ausgeblendet verschwindet nur der Eintrag in der Seitenleiste.
- Der Link auf der **Geräteseite** von Hauswacht führt jetzt zur Einstellungsseite (bisher zur
  Anleitung auf GitHub – die steht auf der Seite im Reiter „Dokumentation“).
- Dialog „Konfigurieren“: ganz oben ein Link zur Einstellungsseite; die Hinweise auf
  „Bei Rückkehr“ verlinken direkt dorthin.

### Sicherheit
- Korrekturen aus 0.60.1 übernommen (HACS-Review: Attribute maskieren, Personen-IDs in der
  Diagnose schwärzen).

## [0.61.0b3] - 2026-11-23

**Vorabversion: Annäherung verlängert die Eingangsverzögerung** (ADR 0015, Schritt 3 von 4).

### Hinzugefügt
- „Bei Rückkehr“ → „Mehr Einstellungen“ (nur „Unscharf mit Türbeleg“ und „Reinlassen“):
  **Eingangsverzögerung nach Annäherung** (Sekunden, 0 = aus) und **Annäherung gilt** (Minuten,
  Standard 15). Hat sich eine Person aus der Liste vorher genähert (Richtung „nähert sich“ aus
  „Nähe“ oder Places), wartet Hauswacht nach dem Öffnen länger auf ihr Handy – z. B. 90 s statt
  30 s. Wer sich nicht genähert hat, hat weiter nur die normale Zeit. Die Richtung schaltet nie
  selbst unscharf.
- Empfehlungen aus der Heimkehr-Beobachtung mit Knopf „übernehmen“, ⓘ-Erklärungen, Warnung,
  wenn der Wert nicht länger als die normale Eingangsverzögerung ist; der Satz „So verhält sich
  das:“ nennt die Verlängerung.
- Ereignis `EntryDelayExtended`; die Push-Nachricht zur Eingangsverzögerung nennt die
  verlängerte Zeit.

## [0.61.0b2] - 2026-11-23

**Vorabversion: „weg“ nur mit Beleg** (ADR 0015, Schritt 2 von 4).

### Sicherheit
- **Ein schlafendes Handy macht niemanden mehr abwesend.** Eine Person gilt für die Automatik
  („Scharf, wenn alle weg“, „Bei Rückkehr“, Reinlassen) erst als weg, wenn alle Signale „weg“
  melden **und** es einen Beleg gibt: eine Eingangstür ging auf und danach (bis 15 Minuten) wurde
  das Handy außerhalb geortet – oder das Handy ist frisch (letzte 15 Minuten) und genau genug
  außerhalb geortet. WLAN, Ping, Router und Bluetooth bestätigen nur. Damit gibt es auch keine
  falsche „Heimkehr“ mehr, nachdem nachts das WLAN eines Handys im Haus weggefallen ist.

### Hinzugefügt
- Systemeinstellungen → Anwesenheit und Heimkehr-Beobachtung: **„Wann gilt jemand als weg?“** –
  Ortung **genau prüfen** (Entfernung größer als Zonenradius plus Ungenauigkeit, Standard) oder
  **einfach** (außerhalb der Zone); **Zeitfenster für den Beleg** (Standard 15 Minuten) mit
  Empfehlung aus der Messung „Weggehen“ und Knopf „übernehmen“; ⓘ je Feld und „So verhält sich das:“.
- Je Person **„Beleg für ‚weg‘“**: nur Ortung (sicher, Standard) oder **auch Tür + Signal
  (unsicher)** – für Personen ohne Ortung: Eingangstür auf und danach (bis 5 Minuten,
  einstellbar, mit Empfehlung aus der Messung) wechselt ein Signal (WLAN, Ping, Bluetooth) auf
  „weg“. Mit Warnhinweis und Prüfhinweis.
- Hinweis „⚠ keine Ortung – gilt nie als weg“ an der Personenauswahl im Profil, in den
  Systemeinstellungen und als Prüfhinweis.

### Geändert
- Die Heimkehr-Beobachtung zählt „weg“ in der Zeile „alle Signale“ genauso mit Beleg.
- Personen, die nur per Router, WLAN oder Ping erfasst werden, gelten nicht mehr als weg.


## [0.61.0b1] - 2026-11-23

**Vorabversion: „Bei Rückkehr“ je Profil** (ADR 0015, Schritt 1 von 4).

### Hinzugefügt
- **Bei Rückkehr** – eine Einstellung je Profil statt zwei verstreuter: was passiert, wenn eine
  Person heimkommt. Fünf Stufen: **Nichts**, **Unscharf, nur wenn automatisch scharf** (wie bisher
  „Wie bisher“), **Unscharf mit Türbeleg**, **Unscharf, auch nach Scharfschalten von Hand** (neu,
  nur Handy, mit Warnung) und **Reinlassen (Durchgang)** (bisher Handy-Reinlassen beim Durchgang;
  das Profil bleibt scharf, „Durchgang erlauben“ muss nicht an sein).
- Eigene Personenliste für „Bei Rückkehr“ – unabhängig von „Scharf, wenn alle weg“.
- Auf der Einstellungsseite: Abschnitt **Bei Rückkehr** mit **ⓘ** je Feld (Mauszeiger oder
  antippen), dem Satz **„So verhält sich das:“**, einer Warnung bei „auch nach Scharfschalten von
  Hand“ und dem Zeitfenster unter **„Mehr Einstellungen“**.
- Die Signale unter „Anwesenheit und Heimkehr“ zeigen auch die Personen aus „Bei Rückkehr“.

### Geändert
- Die Felder „Unscharf bei Rückkehr“, „Türbeleg-Fenster“ sowie Personen und Zeitfenster des
  Handy-Reinlassens sind aus dem Optionen-Dialog und der Durchgang-Einstellung verschwunden;
  der Dialog verweist auf die Einstellungsseite.
- Die Entitäten heißen jetzt „Bei Rückkehr“ und „Bei Rückkehr: Zeitfenster Handy und Tür“
  (bestehende Entitäts-IDs bleiben).
- Übersichtskarte: Zeile „Bei Rückkehr“ je Profil.

### Migration
- Bestehende Einstellungen werden beim Update übernommen (Config-Eintrag 5.2). Waren in einem
  Profil „Unscharf bei Rückkehr“ **und** Handy-Reinlassen an, gewinnt **Reinlassen** (das Profil
  bleibt scharf); dazu kommt eine Benachrichtigung. Die alten Schlüssel bleiben stehen, damit ein
  Zurückgehen auf 0.60 funktioniert.

## [0.60.1] - 2026-11-23

**Korrekturen aus dem HACS-Review.**

### Sicherheit
- Einstellungsseite: Werte aus anderen Integrationen (z. B. Ereignis-Typen von Knöpfen) werden
  jetzt auch in HTML-Attributen maskiert. Ein Wert mit Anführungszeichen konnte vorher fremdes
  HTML in die Seite einschleusen.
- Diagnose-Datei: Personen-IDs (`person.…`) aus dem Durchgang, aus Bedingungen von
  Auslöseregeln und aus der Empfehlung „Weggehen“ werden geschwärzt.

## [0.60.0] - 2026-11-23

**Beobachtung „Weggehen“, Messungen und Sirenentest auf der Einstellungsseite, Sicherheitskorrektur
bei der Richtung** (ADR 0014, getestet über die Vorabversionen 0.60.0b1 bis b8).

### Sicherheit
- **Profil-Automatik:** Die Richtung (Nähe, Places) „nähert sich“ galt als „zuhause“. Eine Fahrt
  in der Umgebung konnte so „Unscharf bei Rückkehr“ auslösen oder beim Durchgang per Handy als
  Ankunft zählen. Richtungs-Sensoren zählen jetzt nur mit „angekommen“ (zuhause) und „entfernt
  sich“ (weg); „nähert sich“ und „steht“ werden übergangen – „steht“ hält damit auch „Scharf, wenn
  alle weg“ nicht mehr auf.

### Hinzugefügt
- **Beobachtung „Weggehen“** (schaltet nichts): je Signal und Person, wie lange es nach dem
  Öffnen einer Tür bis „weg“ dauert, und **Schweigepausen** ohne Tür (schlafendes Handy,
  WLAN-Aussetzer); Pausen mehrerer Personen gleichzeitig als möglicher WLAN-Ausfall gekennzeichnet.
- **Empfehlung je Person** für „Rausgehen ohne PIN erkennen“: Wartezeit (1–15 min) oder
  Warnhinweis mit Tipp – im Bericht, auf der Einstellungsseite und als Prüfhinweis; Attribute
  `departure`, `leaving_advice`, `departure_days`; Zeilen „Weggehen“ in der CSV-Tabelle.
- **Messungen auf der Einstellungsseite** (System → Anwesenheit und Heimkehr-Beobachtung): Beginn
  der Messung, Tabelle je Person, Empfehlungen, Eingänge je Tür; Knöpfe **Bericht anzeigen**,
  **Bericht speichern**, **Tabelle speichern (CSV)**, **Heimkommen / Weggehen / Alle Messungen
  zurücksetzen**; bei der Funkstille **Messung zurücksetzen** (nur Administratoren, mit Rückfrage,
  ändert keine Einstellung).
- **Sirenentest auf der Einstellungsseite** (Alarmgeber → Sirenentest): Häkchen „Ich bin vor
  Ort“, Rückfrage, Stopp, „Gehört?“ – gleiche Sperren wie in der Testkarte, die ihn weiterhin hat
  (ADR 0011, Nachtrag). Ein Test hält fest, dass die Seite sonst keine Dienste aufruft.

### Geändert
- Das **frühestes Signal** und die Kombination **„alle Signale“** der Beobachtung zählen genau
  wie die Profil-Automatik – so zeigt die Empfehlung für „Unscharf mit Türbeleg“, was die
  Automatik wirklich braucht. „Nähert sich“ ist keine Heimkehr mehr, ein Spaziergang zählt nicht
  mehr als zweimal Rausgehen.
- Richtungssensoren der Zusatz-Integration **Places** werden verstanden („towards home“, „away
  from home“).

### Behoben
- **Beobachtung schneller:** Die Auswertung lief bei Wochen voller Daten bei jeder Signaländerung
  mehrere Sekunden und bremste dabei Home Assistant. Jetzt per Nachschlagen statt „jede mit jeder“
  und nur einmal je Änderung – Millisekunden statt Sekunden.
- Ein Eingang per **Durchgang** zählte als „zu spät – Alarm“; jetzt „per Durchgang reingelassen“,
  ohne in die Statistik einzugehen.
- Einstellungsseite: Wurde beim Speichern etwas abgelehnt, stand die Meldung oft außer Sicht;
  jetzt rückt sie ins Bild. Im Profil-Dialog stehen die Meldungen zu „Unscharf bei Rückkehr“
  direkt am Auswahlfeld.
- Funkstille zurücksetzen speichert den Stand nach dem ersten Abgleich, nicht einen leeren.

### Dokumentation
- Beobachtungen: Abschnitte „Weggehen“ und „Messungen auf der Einstellungsseite“;
  Einstellungsseite: Sirenentest; Profile: Richtung in der Automatik; Roadmap – deutsch und
  englisch.

> Nach dem Update: Einstellungen → System → Messungen → **Alle Messungen zurücksetzen**, damit
> Werte aus den Vorabversionen die Empfehlungen nicht verfälschen.


## [0.60.0b9] - 2026-11-23

### Behoben
- Einstellungsseite: Wurde beim Speichern etwas abgelehnt, stand die Meldung oft unten außer
  Sicht – es sah aus, als würde nicht gespeichert. Jetzt rückt die erste Fehlermeldung nach dem
  Speichern ins Bild (alle Dialoge).
- Profil-Dialog: Die Meldungen zu **„Unscharf bei Rückkehr“** stehen jetzt direkt unter dem
  Auswahlfeld, mit Hinweis, was nötig ist (Personen bei „Scharf, wenn alle diese Personen weg
  sind“; „mit Türbeleg“ nicht zusammen mit Handy-Reinlassen beim Durchgang).

## [0.60.0b8] - 2026-11-23

### Behoben
- Heimkehr-Beobachtung: Ein Eingang, bei dem man per **Durchgang** (z. B. per Handy) reingelassen
  wurde, zählte als „zu spät – Alarm“. Er steht jetzt als „per Durchgang reingelassen“ in der
  Tabelle und zählt weder als rechtzeitig noch als zu spät.

## [0.60.0b7] - 2026-11-23

### Behoben
- Heimkehr-Beobachtung: Eine Fahrt in der Umgebung zählte als Heimkommen, sobald die Richtung
  (Nähe, Places) kurz „nähert sich“ meldete. Das **frühestes Signal** zählt jetzt nur echte
  Heimkehrten (ein Anwesenheits-Signal meldet wieder „zuhause“); „nähert sich“ bis zu 15 Minuten
  davor macht den Zeitpunkt nur früher. Nach dem Update **Heimkommen zurücksetzen**.
- **Sicherheit – Profil-Automatik:** Die Richtung (Nähe, Places) „nähert sich“ galt als „zuhause“.
  Eine Fahrt in der Umgebung konnte so „Unscharf bei Rückkehr“ auslösen oder beim Durchgang per
  Handy als Ankunft zählen. Jetzt zählen Richtungs-Sensoren nur mit „angekommen“ (zuhause) und
  „entfernt sich“ (weg); „nähert sich“ und „steht“ werden übergangen – „steht“ hält damit auch
  „Scharf, wenn alle weg“ nicht mehr auf.

## [0.60.0b6] - 2026-11-22

### Hinzugefügt
- **Sirenentest auf der Einstellungsseite:** Reiter Alarmgeber → Karte „Sirenentest“. Jede Sirene
  mit letztem Test (✅/❌); Häkchen „Ich bin vor Ort, Mitbewohner sind informiert“, Rückfrage vor
  dem Ton, Stopp, „Gehört?“. Nur für Administratoren. Gleicher Weg und gleiche Sperren wie in der
  Testkarte, die den Test weiterhin hat (ADR 0011, Nachtrag).

## [0.60.0b5] - 2026-11-22

### Behoben
- Weggehen: Ein Spaziergang zählte als zweimal Rausgehen. Die Kombination je Person heißt jetzt
  **„alle Signale“** und lässt Richtungs-Sensoren (Nähe, Places) weg – „nähert sich“ draußen gilt
  nicht mehr als „zurück“, „steht“ hält das „weg“ nicht mehr auf. Rückkehr und Dauer der
  Schweigepausen werden für diese Kombination direkt mitgeschrieben.
  Nach dem Update **Weggehen zurücksetzen**, damit alte Doppelzählungen verschwinden.

## [0.60.0b4] - 2026-11-22

### Hinzugefügt
- Messungen: eigener Knopf **Heimkommen zurücksetzen** – beginnt nur die Heimkehr-Auswertung neu
  (Heimkehrten, Türöffnungen, Empfehlung „Unscharf mit Türbeleg“); Weggehen und Eingänge bleiben.
  WebSocket `hauswacht/measurements/reset` mit `what: arrival`.

## [0.60.0b3] - 2026-11-22

**Vorabversion: Messungen auf der Einstellungsseite.**

### Hinzugefügt
- Einstellungsseite → System → Karte „Anwesenheit und Heimkehr-Beobachtung“: neuer Block
  **Messungen** – seit wann gemessen wird, Tabelle je Person (Heimkehr, Rausgehen, längste Zeit
  bis „weg“, Schweigepausen), Empfehlung je Person (✅/⚠️) und die Eingänge je Tür.
- Knöpfe **Bericht anzeigen** (direkt auf der Seite), **Bericht speichern**, **Tabelle speichern
  (CSV)**, **Weggehen zurücksetzen** und **Alle Messungen zurücksetzen** (mit Rückfrage).
- Karte „Funkstille von Sensoren“: Beginn der Messung und **Messung zurücksetzen**.
- WebSocket-Befehl `hauswacht/measurements/reset` (nur Administratoren). Zurücksetzen ändert keine
  Einstellung und schaltet nichts.

## [0.60.0b2] - 2026-11-21

**Vorabversion: Beobachtung „Weggehen“ – Korrekturen.**

### Behoben
- Die Mindestdauer von 2 Tagen für die Empfehlung zählt jetzt ab Beginn der Messung „Weggehen“,
  nicht ab Start der Heimkehr-Beobachtung. Neues Attribut `departure_days`.
- Richtungssensoren der Zusatz-Integration **Places** werden verstanden: „towards home“ =
  zuhause, „away from home“ = weg. Bisher galten beide als „weg“ – auch für die Profil-Automatik.

## [0.60.0b1] - 2026-11-21

**Vorabversion: Beobachtung „Weggehen“** (ADR 0014, Messung für die spätere Ausgangserkennung).

### Hinzugefügt
- Die Heimkehr-Beobachtung misst jetzt auch das **Weggehen** – sie schaltet weiterhin nichts:
  - je Signal und Person: wie lange es nach dem Öffnen einer Eingangstür dauert, bis „weg“
    gemeldet wird (Tür bis zu 15 Minuten vorher);
  - **Schweigepausen:** „weg“, ohne dass vorher eine Tür aufging (schlafendes Handy,
    WLAN-Aussetzer) – wie oft und wie lange; gleichzeitige Pausen mehrerer Personen werden als
    möglicher WLAN-Ausfall gekennzeichnet.
- **Empfehlung je Person** für „Rausgehen ohne PIN erkennen“: empfohlene Wartezeit (1–15 min)
  oder ein **Warnhinweis** mit Tipp (z. B. Companion App mit WLAN-Sensor), wenn das Rausgehen
  zu langsam erkannt wird oder alle Signale zu lange schweigen. Im Bericht, auf der
  Einstellungsseite (Karte „Anwesenheit und Heimkehr-Beobachtung“) und als Prüfhinweis.
- Neue Attribute `departure` und `leaving_advice` am Sensor „Heimkehr-Beobachtung“; jede Messung
  als Zeile „Weggehen“ in der CSV-Tabelle.

### Dokumentation
- Beobachtungen: neuer Abschnitt „Weggehen“ mit Beispiel und Lesehilfe; Prüfhinweise ergänzt –
  deutsch und englisch.

## [0.59.0] - 2026-11-21

**Durchgang – rein oder raus, ohne unscharf zu schalten** (ADR 0013, getestet über die
Vorabversionen 0.59.0b1 bis b3).

### Hinzugefügt
- **Durchgang** je Profil (Standard aus): Das Profil bleibt scharf, nur eine Tür (und frei
  gewählte Melder auf dem Weg) ist kurz frei – nachts heimkommen, kurz den Müll rausbringen.
  - **Reinkommen:** in der Eingangsverzögerung PIN oder Karte und **irgendeine Profil-Taste**;
    die geöffnete Tür ist frei, bis sie zu ist, die Melder auf dem Weg noch eine Nachlaufzeit
    länger. Jede neue Türöffnung braucht einen eigenen Ausweis.
  - **Rausgehen:** solange scharf, PIN oder Karte und **irgendeine Profil-Taste** (es wird nie
    umgeschaltet). Die erste Eingangstür, die danach aufgeht, ist für die Durchgangszeit frei
    (Standard 5 Minuten); alle anderen bleiben scharf.
  - Tür am Ende noch offen: **Warnung statt Alarm**, wieder überwacht, sobald sie zu ist.
- Weitere Wege: eigene **Durchgang-Taste**, Aktion **`hauswacht.passage`**, Push-Knopf
  **„Reinlassen“**, **Handy-Reinlassen** mit eigener Personenliste, **Türschloss** („Aufschließen
  bei scharf: Durchgang, sonst unscharf“), **NFC-Aufkleber** und **RFID-Leser** (Aktion
  „Durchgang“).
- Benachrichtigung **„Durchgang“**, Hinweis auf der Alarm-Karte, Attribut `passage`, Ereignisse
  für Automationen. Immer mit Ausweis, Recht wie „unscharf schalten“, Bedrohungs-PIN wirkt still.

### Dokumentation
- Neue Seite **Durchgang** mit Beispielen und Restrisiko; ADR 0013; ADR 0014 „Ausgangserkennung“
  (vorgeschlagen) und Roadmap 0.60/0.61 – deutsch und englisch.


## [0.59.0b3] - 2026-11-21

**Vorabversion: Durchgang – Türschloss, NFC-Aufkleber, Kartenleser** (ADR 0013, Stufe 3).

### Hinzugefügt
- **Türschloss:** neue Einstellung „Aufschließen bei scharf“ – **unscharf schalten** (wie
  bisher, Standard) oder **Durchgang, wenn das Profil ihn erlaubt – sonst unscharf**.
  Aufschließen in der Eingangsverzögerung lässt herein, vorher öffnet es den Durchgang zum
  Rausgehen.
- **NFC-Aufkleber und RFID-Leser:** neue Aktion **„Durchgang“** mit derselben Regel.

### Dokumentation
- Durchgang: Abschnitt „Türschloss, NFC-Aufkleber, Kartenleser“ mit Beispiel; Bedienteile –
  deutsch und englisch.


## [0.59.0b2] - 2026-11-21

**Vorabversion: Durchgang – Reinlassen per Push-Knopf und per Handy** (ADR 0013, Stufe 2).

### Hinzugefügt
- **Push-Knopf „Reinlassen“** neben „Unscharf“ in der Nachricht zur Eingangsverzögerung (wenn
  „Unscharf über Push-Knopf“ an ist und das Profil den Durchgang erlaubt). Wer tippt, braucht das
  Recht „unscharf schalten“.
- **Handy-Reinlassen** je Profil mit eigener Personenliste: Kommt eine dieser Personen heim
  (vorher mindestens 5 Minuten sicher weg) und geht eine Eingangstür auf, lässt Hauswacht sie
  ohne PIN herein – wenn das Handy bis zu x Minuten vor dem Öffnen (Standard 5) oder noch
  während der Eingangsverzögerung „zuhause“ meldet. Kommt es später, bleibt der Alarm ein Alarm.
  Eine Heimkehr lässt einmal rein. Nachricht „Finja (Handy) hereingelassen …“.
- „Unscharf mit Türbeleg“ und Handy-Reinlassen schließen sich im selben Profil aus (Prüfung auf
  der Einstellungsseite und im Dialog).
- Ereignis `PhoneArrivalNoted`.

### Dokumentation
- Durchgang: Abschnitte „Reinlassen per Push-Knopf“ und „Reinlassen per Handy“ mit Tabelle der
  Zeitabläufe und Restrisiko; Referenz – deutsch und englisch.


## [0.59.0b1] - 2026-11-21

**Vorabversion: Durchgang – rein oder raus, ohne unscharf zu schalten** (ADR 0013, Stufe 1).

### Hinzugefügt
- **Durchgang** je Profil (Standard aus): Das Profil bleibt scharf, nur eine Tür (und frei
  gewählte Melder auf dem Weg) ist kurz frei.
  - **Reinkommen:** In der Eingangsverzögerung PIN oder Karte und **irgendeine Profil-Taste**
    (oder die Durchgang-Taste) am Keypad – kein Alarm, das laufende Profil bleibt. Die geöffnete
    Tür ist frei, bis sie zu ist; die Melder auf dem Weg noch eine Nachlaufzeit länger
    (Standard 60 s). Jede neue Türöffnung braucht einen eigenen Ausweis.
  - **Rausgehen** (z. B. Müll): PIN oder Karte und **irgendeine Profil-Taste**, solange scharf
    ist (es wird nie auf ein anderes Profil umgeschaltet), oder die Durchgang-Taste. Die erste
    Eingangstür, die danach aufgeht, ist für die Durchgangszeit frei (Standard 5 Minuten) – alle
    anderen bleiben scharf (einstellbar: alle Eingangstüren). Ende nach Ablauf der Zeit oder
    schon, wenn man zurück und die Tür zu ist (einstellbar).
  - Ist eine Tür am Ende noch offen: **kein Alarm**, sondern eine deutliche Warnung; sie wird
    wieder überwacht, sobald sie zu ist.
- **Taste „Durchgang“** bei jedem Keypad frei wählbar (Zigbee2MQTT-Keypad, Keypad (allgemein),
  MQTT-Schnittstelle) – statt eines Profils; nötig ist sie nicht.
- **Aktion `hauswacht.passage`** (mit PIN) für Dashboard-Knöpfe und Automationen.
- **Benachrichtigung „Durchgang“** (Standard an): „… hereingelassen – Profil Nacht bleibt
  scharf“ (ersetzt die Nachricht zur Eingangsverzögerung), „Durchgang für 5 Minuten“, Warnung
  „noch offen“. Ereignisse `PassageGranted`, `PassageDoorUsed`, `PassageEnded`,
  `PassageDoorOpen`; Attribut `passage` am Bedienfeld und an der Anzeige-Entität allgemeiner
  Keypads; Hinweis auf der Alarm-Karte.
- Immer mit Ausweis (auch bei „Tasten ohne PIN“), Recht wie „unscharf schalten“. Bedrohungs-PIN:
  nach außen ein normaler Durchgang, still der Bedrohungsalarm. Kein Durchgang während eines
  Alarms oder der Ausgangsverzögerung.

### Dokumentation
- Neue Seite **Durchgang** mit Beispielen; Bedienteile, Benachrichtigungen, Referenz, README,
  Roadmap, ADR 0013 – deutsch und englisch.


## [0.58.3] - 2026-11-20

**Code-Entität der Keypads nur noch nach deiner Bestätigung abschalten.**

### Geändert
- **Code-Entität der Keypads (Zigbee2MQTT):** Hauswacht hat die Entität, in der Zigbee2MQTT den
  am Keypad getippten Code ablegt (z. B. `sensor.keypad_flur_action_code`), bisher selbst
  deaktiviert. Sie gehört aber der MQTT-Integration. Jetzt erscheint stattdessen unter
  Einstellungen → Reparaturen „Hauswacht: PINs vom Keypad landen im Verlauf“: Mit **Beheben**
  und Bestätigen wird sie deaktiviert, mit **Ignorieren** bleibt sie, wie sie ist. Schon früher
  deaktivierte Entitäten bleiben deaktiviert; wer eine bewusst wieder eingeschaltet hat, wird
  nicht erneut gefragt.

### Dokumentation
- Bedienteile, Installation (Entfernen), Roadmap – deutsch und englisch.

## [0.58.2] - 2026-11-20

**Jede Meldung nur einmal – und alte verschwinden.**

### Behoben
- **Automatisch scharf/unscharf kam doppelt** – „Scharf geschaltet (Automatik)“ und zusätzlich
  „Automatisch scharf geschaltet (Uhrzeit)“, ebenso beim Unscharfschalten. Jetzt kommt eine
  Nachricht: Ist „Scharf geschaltet“ bzw. „Unscharf geschaltet“ an, steht der Grund darin, sonst
  kommt nur die Automatik-Nachricht. Sie ersetzen einander wie das normale Scharf/Unscharf.
- **Unscharf über den Push-Knopf:** Die Rückmeldung blieb dauerhaft stehen; jetzt ersetzt sie die
  Scharf-Nachricht.
- **Ausgefallene Melder** wurden bei jedem Ausfall neu gemeldet und nie weggeräumt, mit dem
  technischen Namen (`binary_sensor.…`). Jetzt: eine Nachricht je Melder, mit seinem Namen; sie
  verschwindet, sobald er sich wieder meldet. Hauswacht wartet dafür 10 Sekunden – ist er bis
  dahin zurück, kommt nichts. Fällt gleichzeitig das Funknetz aus (z. B. Zigbee2MQTT), kommt nur
  die Störungsmeldung statt zusätzlich einer für jeden Melder.
- **Taster, Kartenleser, NFC-Aufkleber, Türschloss:** Scheitert das Scharfschalten, kam neben
  „Scharfschalten nicht möglich“ (mit Knöpfen) noch „Bedienteil abgelehnt“. Jetzt nur die erste.
- **„Alarm beendet“** (scharf bleibt) ersetzt jetzt die Alarm-Nachricht und verschwindet beim
  Unscharfschalten, statt stehen zu bleiben.

### Dokumentation
- Benachrichtigungen: neuer Abschnitt „Jede Meldung nur einmal“ mit Beispiel – deutsch und
  englisch.

## [0.58.1] - 2026-11-19

**Jedes Handy nur einmal unter den Empfängern.**

### Behoben
- **Handys standen doppelt in der Empfängerliste** – einmal als Dienst der Home-Assistant-App
  (technischer Name, z. B. „2211133g xiaomi13“), einmal als Benachrichtigungs-Entität („Xiaomi 13
  Christian“). Jetzt steht jedes Handy einmal da, als Dienst mit dem Namen aus Home Assistant –
  nur der Dienst kann Knöpfe, Aufräumen und wichtige Hinweise. Früher gewählte App-Entitäten
  stellt Hauswacht einmalig auf den Dienst desselben Handys um und schickt bis dahin schon
  darüber.

### Dokumentation
- Benachrichtigungen: „Jedes Handy nur einmal“ – deutsch und englisch.

## [0.58.0] - 2026-11-19

**Jedes Keypad anbinden** – ein Eingang für alle Keypads, fertige Vorlagen und eine
MQTT-Schnittstelle (ADR 0012, getestet über die Vorabversionen 0.58.0b1 bis b5).

### Hinzugefügt
- **Keypad (allgemein):** neue Art von Bedienteil für Keypads, die Hauswacht nicht selbst kennt –
  ZHA, Z-Wave (z. B. Ring Keypad), deCONZ, ESPHome, Node-RED. Ein Blueprint oder eine Automation
  meldet Taste und PIN/Karte mit der neuen Aktion **`hauswacht.keypad_input`** und bekommt eine
  **Antwort** zurück (`ok`, `invalid_code`, `locked`, `not_ready` mit den offenen Meldern,
  `pending` …). Ausgewertet wird genau wie am Zigbee2MQTT-Keypad: Rechte, Sperre,
  Bedrohungs-PIN, Karte und PIN, Aktions-Codes, „trotzdem scharf“, Notruf. Tasten mit freien
  Namen.
- **Anzeige-Entität je Keypad**: was das Keypad zeigen soll – unscharf, Verzögerungen (mit Ende
  für einen Countdown), scharf, Alarm. Im Testmodus nie „Alarm“ (`test_alarm`), Brand mit eigenem
  Zustand und Vorrang.
- **Nur angelegte Keypads werden angenommen**; ein unbekanntes erscheint auf der
  Einstellungsseite mit „Anlegen“. Die Aktion dürfen nur Automationen, Skripte, Geräte und
  Administratoren aufrufen; doppelte Funkmeldungen zählen einmal.
- **Fertige Vorlagen** (ungetestet – eigene Verantwortung): Blueprint **Ring Keypad v2**
  (Z-Wave JS) und ein **ESPHome-Beispiel** für ein selbst gebautes Keypad – mit Versionsnummer,
  importierbar direkt von der Einstellungsseite (neuer Tab, installierte Version).
- **MQTT-Schnittstelle** für Geräte und Programme, die nur MQTT sprechen (Wand-Tablet-Apps,
  Tasmota- oder Arduino-Eigenbauten, Node-RED): Befehle auf `…/set` als Text oder JSON; Zustand
  (Wörter wie die MQTT-Alarmzentrale von Home Assistant, anpassbar), Details, Antwort und
  Verfügbarkeit. Gespeicherte Befehle (retain) werden nie ausgeführt; jeder Befehl steht im Log
  (ohne PIN).
- **„Wie gut erprobt?“** in der Anleitung der Bedienteile: Erprobt, Getestet oder Ungetestet.

### Geändert
- **Warnungen zu falschen PINs** ersetzen einander auf dem Handy – es bleibt nur die letzte;
  beim Zurücksetzen der Falscheingaben verschwindet sie.

### Dokumentation
- Bedienteile: „Keypad (allgemein)“ mit Beispiel-Automationen und dem Hinweis, wie PINs aus der
  Datenbank von Home Assistant herausbleiben; „Fertige Vorlagen“ (inkl. Stand bei ZHA-Keypads);
  „MQTT-Schnittstelle“ mit Topics, Befehlen, Zustandswörtern, „Ausprobieren ohne Gerät“ und
  „Den Broker absichern“. Dazu Benachrichtigungen, Referenz, Einstellungsseite, README, Roadmap,
  ADR 0012 – deutsch und englisch.

### Intern
- Keypad-Kern aus der Zigbee2MQTT-Anbindung herausgelöst (`ControlManager.async_input`); das
  Zigbee2MQTT-Keypad antwortet unverändert. Neue reine Module `core/keypad_input.py` und
  `core/mqtt_keypad.py`. Integrationstest lädt den Ring-Blueprint in Home Assistant. Statischer
  Test: Hauswacht sendet per MQTT nur an die Anzeige von Zigbee2MQTT-Keypads und an die eigenen
  Topics einer MQTT-Schnittstelle.

## [0.57.2] - 2026-11-19

**Sirenentest mit Batterie-Rauchmeldern** (getestet über die Vorabversion 0.57.2b1).

### Behoben
- **Sirenentest klappte bei Batterie-Rauchmeldern oft erst beim zweiten Mal.** Solche Geräte
  (z. B. Develco über Zigbee2MQTT) holen Befehle erst nach einigen Sekunden ab. Hauswacht schickte
  das „Aus“ schon nach 3,5 s – kam es zusammen mit dem „Ein“ an, blieb der Melder still. Jetzt
  schickt der Test bei Sirenen, die die Dauer selbst einhalten, nur „Ein für 3 s“ und das
  Sicherheits-„Aus“ erst 12 s später. Die Frage „gehört?“ kommt danach; die Testkarte zeigt
  währenddessen einen Hinweis. Sirenen ohne eigene Dauer bleiben wie bisher.

### Dokumentation
- Sirenen (Sirenentest, Verzögerung im Alarmfall), Fehlersuche – deutsch und englisch.

## [0.57.1] - 2026-11-19

**„Trotzdem scharf“ am Keypad repariert, eine Nachricht beim Scharfschalten** (getestet über die
Vorabversionen 0.57.1b1 und b2).

### Behoben
- **Trotzdem scharf am Keypad** ging nicht, wenn der zweite Druck ohne PIN kam – und gar nicht,
  wenn Scharfschalten ohne PIN erlaubt ist: Ein Druck ohne PIN löschte die gemerkte Bestätigung.
  Jetzt bestätigt **dieselbe Taste innerhalb von 10 Sekunden** den ersten Druck – **mit oder ohne
  PIN** bzw. Karte. Kam der erste Druck mit PIN, gilt der zweite im Namen dieser Person (Recht
  „trotzdem scharf“ nötig). Ohne PIN geht es nur, wenn Scharfschalten ohne PIN erlaubt ist.
  „Verweigern“ bleibt verweigern.
- Die Anleitung versprach eine Meldung „scharf, überbrückt: …“ – sie wurde nie verschickt.

### Hinzugefügt
- **Rückmeldung über Lücken beim Scharfschalten:** überbrückte offene Melder („trotzdem scharf“
  oder automatisch), ausgefallene Melder (werden wieder überwacht, sobald sie sich melden) und
  offene Melder, die nur in Auslöseregeln vorkommen – egal ob über Keypad, Karte, Push-Knopf oder
  Automatik. Neues Ereignis `ArmedWithGaps`.
- **Ausgefallene Sensoren beim Scharfschalten: „automatisch überbrücken“** als Expertenoption je
  Profil – scharf ohne Rückfrage; der Melder wird wieder überwacht, sobald er sich meldet.

### Geändert
- **Eine Nachricht beim Scharfschalten statt zwei:** Ist „Scharf geschaltet“ an, stehen die
  Lücken in dieser Nachricht; der eigene Hinweis kommt nur, wenn sie aus ist.
- **Alte Nachrichten räumen sich auf:** Scharf- und Unscharf-Nachricht ersetzen einander auf dem
  Handy (Home-Assistant-App); bekommt man beim Unscharfschalten keine Nachricht, verschwindet die
  Scharf-Nachricht.

### Dokumentation
- Bedienteile (Trotzdem scharf am Keypad), Profile, Benachrichtigungen (Hinweis beim
  Scharfschalten, Aufräumen), Referenz – deutsch und englisch.

## [0.57.0] - 2026-11-18

**Einstellungsseite „Hauswacht“ in der Seitenleiste** – die ganze Einrichtung auf einen Blick und
alles direkt bearbeiten, zusätzlich zum Einstellungsdialog (ADR 0011, getestet über die
Vorabversionen 0.57.0b1 bis b14).

### Hinzugefügt
- **Einstellungsseite** (nur Administratoren) mit den Reitern Übersicht, Melder, Profile,
  Auslöseregeln, Alarmgeber, Benachrichtigungen, Personen und Bedienteile, System und
  Dokumentation. Bearbeitet wird in Seitenblättern rechts – mit denselben Regeln und Prüfungen
  wie im Dialog. Gespeichert wird nur, wenn alle Bereiche unscharf sind; hat jemand zwischendurch
  woanders etwas geändert, wird nichts überschrieben. Ausblenden unter System →
  Einstellungsseite.
- **Melder:** Matrix „Melder × Profile“ nach Meldergruppen; Meldergruppen mit Typ je Melder,
  Label und Fehlalarmschutz; einzelnen Melder bearbeiten (Gruppe, Typ, Immer aktiv, Ausnahmen je
  Profil); Melder mit Kippstellung, Erschütterungsstärken, Immer aktiv mit Sirenen für den
  unscharfen Zustand, Melder aus Messwert erstellen. Die Melder-Auswahl zeigt sofort alle
  passenden Melder, ohne Namen kennen zu müssen.
- **Profile:** anlegen, ändern, löschen – alle Einstellungen wie im Dialog, mit Link zum Anlegen
  eines Zeitplans.
- **Auslöseregeln** mit Umschalter **Formular / YAML**; komplexe Regeln nur als YAML. Beim
  Bearbeiten steht immer als Satz da, was die Regel bewirkt.
- **Alarmgeber:** Sirenen und Freigabe (nur mit Bestätigung), Ton je Sirene mit Brandton-Sperre,
  Sirenentest-Erinnerung, Sirene aus Schalter erstellen. Die Seite schaltet nie eine Sirene; der
  Sirenentest bleibt in der Testkarte.
- **Benachrichtigungen:** Empfänger, Ereignisse, Erinnerung; **eigene Texte** starten mit dem Text
  von Hauswacht als Vorlage, mit Vorschau und „↺ Standardtext“; **Sprachausgabe** mit
  Lautsprechern, Nachtruhe und Text je Ereignis.
- **Personen** mit Rechten je Bereich, Gültigkeit und PINs (nie sichtbar); **Karten anlernen** auf
  der Seite (hinhalten oder Nummer eintippen); **Bedienteile** anlegen und einstellen; PIN-Regeln
  und Master-PIN; Aktions-Codes.
- **System:** Verhalten nach Neustart, Funkstille, Funknetz, Anwesenheit und Heimkehr, Bereiche.
- **Funkstille je Melder:** eigene Grenze oder „nie prüfen“, Beobachtung und Empfehlung je Melder
  („Empfehlung übernehmen“) – auf der Seite und im Dialog. Melder mit eigenem Wert zählen für die
  allgemeine Empfehlung nicht mehr mit. Neuer Prüfhinweis, wenn ein eigener Wert zu knapp ist.
- **„?“ an jedem Abschnitt** öffnet die Anleitung an der passenden Stelle – für genau die
  installierte Version; Reiter **Dokumentation** mit allen Seiten.
- Übersicht auf der Seite mit **Drucken**, **Notfallblatt** und Download des Heimkehr-Berichts.

### Geändert
- **„Verhalten nach Neustart“ gilt nur noch nach einem echten Neustart von Home Assistant.** Wird
  nur Hauswacht neu geladen (z. B. nach dem Speichern von Einstellungen), bleibt der Zustand, wie
  er war.
- Platzhalter-Texte räumen leere Klammern besser auf (kein Leerzeichen mehr vor dem Punkt).

### Behoben
- „Nach Neustart immer scharf“: Beim Neuladen lief der Timer der alten Instanz weiter und ließ sich
  nicht stoppen.

### Dokumentation
- Neue Seite „Einstellungsseite“; Melder (Funkstille je Melder), Benachrichtigungen (eigene Texte
  als Vorlage), Installation (Neustart), Auslöseregeln, README, Roadmap – deutsch und englisch.

### Intern
- Logikschicht erweitert (`core/changes/`: Regeln, Sirenen, Sprachausgabe, Karten, Bedienteile,
  System, Aktions-Codes, Benutzer); Karten und Bedienteile nutzt jetzt auch der Dialog.
  Websocket-Befehle `hauswacht/settings/get`, `…/apply`, `…/rule_check`, `…/new_cards` (nur
  Administratoren). Kern- und Integrationstests; Test, dass jeder Doku-Link der Seite existiert.

## [0.56.0] - 2026-11-18

Fenster richtig überwachen: gekippte Fenster und Erschütterung (ADR 0010, getestet über die
Vorabversionen 0.56.0b1 und b2).

### Hinzugefügt
- **Melder mit Kippstellung („gekippt“):** Fenstersensoren und Fenstergriffe mit drei
  Stellungen – zu, gekippt, offen – werden direkt unterstützt, ohne Vorlagen-Helfer. Neuer
  Menüpunkt **Alarmauslösung → Besondere Melder**: Quelle wählen (Sensor mit Text-Zustand, z. B.
  `opening_state` von Zigbee2MQTT; Attribut, z. B. `window_state` eines Fenstergriffs; oder ein
  Auswahl-Helfer zum Ausprobieren), Werte für zu und gekippt zuordnen (Vorschlag automatisch),
  optional gleich in eine Meldergruppe nehmen. Unbekannte Werte zählen sicherheitshalber als
  offen, ein Ausfall wird wie bei jedem Melder erkannt.
- **Profil-Einstellung „Gekippte Fenster erlaubt“** (Formular und Schalter im Dashboard, nur mit
  Meldern mit Kippstellung): an = gekippt zählt als zu, erst ganz öffnen löst aus (typisch
  „Nacht“); aus (Standard) = gekippt zählt wie offen. Der Einrichtungsassistent fragt beim
  Nachtprofil danach.
- **„Trotzdem scharf“ mit gekipptem Fenster:** Wird ein so überbrücktes Fenster danach ganz
  geöffnet, löst es aus.
- **Melder-Typ „Erschütterung“** (Vorschlag für Geräteklasse Vibration): sofort Alarm im
  scharfen Profil, **blockiert das Scharfschalten nie**; ein ausgefallener Erschütterungssensor
  zählt weiter wie jeder ausgefallene Melder. Texte sagen „(Erschütterung)“.
- **Fehlalarmschutz je Meldergruppe:** „Alarm bei N Meldungen eines Melders innerhalb von S
  Sekunden“ – Standard 1 Meldung, Empfehlung 2 in 60 Sekunden, mit Erklärung im Dialog. Gezählt
  wird je Melder. Neues Ereignis `VibrationCounted` für Meldungen, die noch nicht reichen.
- **Erschütterungsstärke als Zahl** (Besondere Melder): Zahlensensor oder Zahlenwert-Helfer mit
  Schwelle wird ohne Helfer zum Erschütterungsmelder; jede Meldung ab der Schwelle zählt, auch
  bei gleichbleibendem Wert. Keine Zahl = ausgefallen.
- Bedienfeld-Attribut `tilted_sensors`, Attribut `tilted` an „Offene Sensoren“, Feld `position`
  (`open`/`tilted`/`closed`) in Ereignissen, „(gekippt)“ in Meldungen; Testkarte mit Knöpfen
  **Gekippt** und **Erschütterung**/**Ruhe**, Aktion `hauswacht.simulate_state` mit `tilted`;
  Anlagenübersicht mit Zustand „gekippt“ und Typ „Erschütterung“.

### Geändert
- Erschütterungssensoren mit Geräteklasse Vibration, deren Typ nie geändert wurde, sind jetzt
  vom Typ **Erschütterung** statt „Sonstiges“. Unterschied: Sie blockieren das Scharfschalten
  nicht mehr, ausgelöst wird wie bisher bei der ersten Meldung. Wer den Typ selbst gewählt hat,
  behält ihn.

### Dokumentation
- Melder: neue Abschnitte „Melder mit Kippstellung (gekippt)“ und „Erschütterungsmelder“ mit
  Einrichtung, Bewertungstabelle, Fehlalarmschutz und Sicherheitsregeln; Typen, Profile,
  Assistent, Referenz, Spickzettel Automationen, Testmodus, README; Beispiel „Es regnet und ein
  Fenster ist gekippt“ – alles deutsch und englisch.

### Intern
- ADR 0010 „Fenster richtig überwachen – Kippstellung und Erschütterung“; neue reine Bausteine
  `core/tilt.py` und `core/vibration.py`, Kern-Ereignis `BypassedSensorOpened`; Kern- und
  Integrationstests.

## [0.55.3] - 2026-11-18

### Geändert
- **Bereit für den Katalog von Marketplace/HACS:** Die Integration nennt jetzt ihre Kategorie
  (*Sicherheit → Alarmanlagen*), damit sie im Marketplace dort zu finden ist. Die Aufnahme in den
  Katalog wird beantragt; bis dahin bleibt die Installation per Link.

### Dokumentation
- Installation (deutsch und englisch) und README: Link, der Hauswacht direkt im Marketplace der
  eigenen Home-Assistant-Instanz öffnet; Hinweis, dass die Aufnahme in den Katalog beantragt ist
  und dann die Suche nach „Hauswacht“ genügt. Badge „Marketplace“ statt „HACS“. Roadmap
  angepasst.

### Intern
- CI prüft zusätzlich mit der HACS-Action (Kategorie Integration) – Voraussetzung für die
  Aufnahme in den Katalog.

## [0.55.2] - 2026-11-18

### Dokumentation
- **Sirenen → Brandschutz** klarer gegliedert: zuerst, was **immer** gilt – auch mit eigenen
  Sirenen und ohne einen in Hauswacht eingetragenen Rauchmelder (Hauswacht prüft alle Rauch-,
  Gas-, Kohlenmonoxid- und Hitzemelder in Home Assistant; bei Brand schaltet es keine Sirene ein
  oder aus, der Einbruchalarm selbst samt Benachrichtigungen läuft weiter; Grenze: nur Melder, die
  in Home Assistant eingebunden und erreichbar sind). Danach, was **zusätzlich** gilt, wenn
  Rauchmelder die Alarmgeber sind. Bisher klang der Abschnitt so, als gelte die Brandsperre nur
  mit Rauchmeldern als Sirenen.

## [0.55.1] - 2026-11-18

### Dokumentation
- **Beispiele:** neuer Abschnitt **„Rauchmelder untereinander vernetzen“** (deutsch und
  englisch) – eigene Automation, die bei Rauch alle Melder piepen lässt, mit Prüfliste (Feuerton,
  Testknopf, Probelauf) und Begründung, warum das bewusst keine Hauswacht-Funktion ist. Verweis
  darauf auf der Seite Sirenen unter Brandschutz. Der Abschnitt sagt gleich zu Beginn, dass er nur
  wichtig ist, wenn man Rauchmelder als Alarmgeber verwendet.

## [0.55.0] - 2026-11-18

### Hinzugefügt
- **Jedes Ereignis nennt seinen Bereich:** Alle `hauswacht_event` tragen jetzt die Felder `area`
  (Kennung des Bereichs, `main` = Hauptbereich, `all` = ganze Anlage) und `area_name`
  (Anzeigename). Mit mehreren Bereichen reagiert eine Automation so gezielt auf einen Bereich,
  z. B. `event_data: {type: TamperDetected, area: garage}`. Ereignisse der ganzen Anlage
  (Funknetz/Gateway, Sirenentest, Zurücksetzen der Sperre, Bedienteile für alle Bereiche) haben
  `area: all`. Bestehende Felder bleiben unverändert – vorhandene Automationen laufen weiter.

### Dokumentation
- **Referenz** (deutsch und englisch) zum vollständigen Nachschlagewerk ausgebaut: alle
  Entitäten mit deutscher **und** englischer Entitäts-ID und „je Bereich“, alle Attribute des
  Bedienfelds mit Beispielwerten, **alle 49 Ereignisse** nach Themen mit ihren Feldern und
  möglichen Werten (u. a. bisher fehlend: `Rejected`, `ConfirmationRequired`,
  `AlarmAcknowledged`, `SensorsRestored`, `TestModeChanged`; Gründe in `StateChanged`), Hinweise zu
  Testmodus und Bereichen, alle Aktionen mit Beispiel.
- Neue Seite **„Automationen: was nehme ich wofür?“** (deutsch und englisch): Spickzettel
  „Ich will reagieren, wenn … → nimm …“, „Ich will etwas tun …“ und häufige Stolperfallen.
- Referenz, Spickzettel, Beispiele und README: Feld `area` in jedem Ereignis, mit Beispiel.
  Über jeder Ereignis-Tabelle der Referenz der Hinweis auf `area`/`area_name`; neues Beispiel
  **„Mehrere Bereiche: Sabotage in der Garage“** (nur Garage → bestimmtes Handy + Garagenlicht);
  Bedienteile-Seite: Keypad-, Taster-, Türschloss-Ereignisse melden den Bereich des Bedienteils
  (`all` bei „für alle Bereiche“).
- **README** (deutsch und englisch): neuer Abschnitt **„Offen für alles: Hauswacht als
  Baustein“** – was Hauswacht an Bedienfeld-Attributen, Ereignissen, Entitäten, Aktionen und
  Knöpfen bereitstellt und was man damit baut (Licht, Kamera, Rollläden, Heizung …), mit Verweis
  auf Beispiele und Referenz. Funktionsliste um Einrichtungsassistent, Zeitplan, Gastmodus und
  Aktions-Codes ergänzt; Schnellstart mit dem Assistenten; „Grenzen, ehrlich gesagt“ (läuft nur
  mit Home Assistant, keine Notrufleitstelle, Funkstörung nur indirekt).


### Intern
- Neuer Test `tests/core/test_reference.py`: Jedes Ereignis, jede Aktion und jedes Attribut des
  Bedienfelds muss in der Referenz stehen (deutsch und englisch) – sonst wird die CI rot.

## [0.54.1] - 2026-11-18

### Behoben
- **Alarmprofil bearbeiten:** Das Feld „Auslöseregeln“ samt Hinweistext erscheint nur noch, wenn
  es überhaupt Auslöseregeln gibt – vorher stand es leer und etwas verloren im Formular.

### Dokumentation
- Alarmprofile (deutsch und englisch): Hinweis, dass das Feld erst mit Auslöseregeln erscheint.

## [0.54.0] - 2026-11-18

### Hinzugefügt
- **Je Wochentag andere Zeiten – Zeitplan-Helfer in der Profil-Automatik:** Unter Automatik →
  **„Oder nach Zeitplan (Helfer)“** wählst du einen Zeitplan von Home Assistant. Beginnt ein
  Zeitblock, wird das Profil scharf; endet er, unscharf. Beispiel „Nacht“: Mo–Do 22:30–6:00,
  Fr–Sa 0:30–8:00 – ohne zweites Profil. Es gelten dieselben Regeln wie für die Uhrzeiten
  (nur aus „unscharf“, Gastmodus, offene Fenster werden nie bestätigt, nie während eines Alarms).
  Blöcke über Mitternacht (bis 24:00 + ab 0:00) gelten als durchgehend; nach einem Neustart holt
  der Zeitplan nichts nach. Die Anlagenübersicht zeigt den Zeitplan im Profil.
- **Einrichtungsassistent:** Im Schritt Alarmprofile lässt sich für „Abwesend“ und „Nacht“
  optional gleich ein Zeitplan wählen (vorbelegt mit dem vorhandenen; leer = unverändert).

### Dokumentation
- Neue Seite **Beispiele** (deutsch und englisch): Hauswacht mit anderen Geräten verbinden –
  bei Alarm Licht an und danach wieder wie vorher, Licht blinken, Kamerabild aufs Handy,
  Rollläden hoch und Musik aus, Statuslicht rot/grün, Heizung und Kamera bei Abwesenheit,
  Willkommenslicht, Sabotage als kritische Benachrichtigung, Störungslampe, Gastmodus aus dem
  Kalender, Taster mit Zusatzfunktion – und was man besser nicht automatisiert.
- Alarmprofile (deutsch und englisch): neuer Abschnitt „Je Wochentag andere Zeiten (Zeitplan)“
  mit Beispiel und Schritt-für-Schritt-Anleitung zum Anlegen des Helfers; ebenso im
  Einrichtungsassistenten, unter Beispiele („Zeitsteuerung“) und in der Fehlersuche („Der Zeitplan
  schaltet nicht“).

## [0.53.2] - 2026-11-17

### Geändert
- **Master-PIN sichtbar:** Das Menü „Benutzer und PINs“ und die PIN-Regeln zeigen jetzt, ob ein
  Master-PIN eingerichtet ist („Master-PIN: ✅ eingerichtet“ bzw. „– keiner“) – ohne eigenen
  Benutzer in der Liste und ohne den PIN selbst. In den PIN-Regeln steht der Master-PIN nicht mehr
  zusätzlich unter „Benutzer mit PIN“.

### Dokumentation
- Benutzer und PINs (deutsch und englisch): Hinweis auf die Anzeige des Master-PINs.

## [0.53.1] - 2026-11-17

### Geändert
- **Menüs zeigen, was es schon gibt:** Oben in den Menüs Meldergruppen, Alarmprofile, Bereiche,
  Benutzer, Bedienteile und Sirenen steht jetzt die Liste der vorhandenen Einträge – z. B.
  „Außen (5 Melder)“, „Nacht – Außen“, „Anna (PIN ✓, 2 Karten)“, „Keypad Flur (Keypad)“; bei den
  Sirenen dazu der Stand der Freigabe. Auslöseregeln, Karten, PINs und Aktions-Codes hatten ihre
  Liste schon.
- **Einrichtungsassistent:** Die Schritte Meldergruppen, Alarmprofile und Sirenen zeigen ebenfalls,
  was schon eingerichtet ist.

### Dokumentation
- Installation (deutsch und englisch): Hinweis auf die Listen in den Menüs.

## [0.53.0] - 2026-11-17

Getestet über die Vorabversionen 0.53.0b1 bis 0.53.0b3.

### Hinzugefügt
- **Einrichtungsassistent** ([Anleitung](docs/assistent.md),
  [ADR 0009](docs/entwicklung/adr/0009-einrichtungsassistent.md)) – führt ohne Vorwissen durch
  die Einrichtung; jeder Schritt ist überspringbar, Vorhandenes wird nur ergänzt:
  - **Start:** Bei der Installation fragt Hauswacht „Mit dem Einrichtungsassistenten
    (empfohlen)“ oder „Ohne Assistent“; später unter Konfigurieren → **Einrichtungsassistent**.
    Ist schon etwas eingerichtet, gibt es eine **Kapitel-Auswahl**.
  - Kurze **Einführung** „So arbeitet Hauswacht“.
  - **Getrennte Bereiche?** Bei der ersten Einrichtung als Frage; weitere Bereiche über
    „Weiteren Bereich einrichten“ mit eigenen Meldern, Gruppen und Profilen.
  - **Melder-Vorschläge:** Türen, Fenster und Bewegungsmelder, die noch in keiner Gruppe stehen,
    nach Etage und Raum.
  - **Überwachungsart:** Meldergruppen, nur Auslöseregeln, beides oder später.
  - **Meldergruppen** „Außen“ und „Innen“ mit Wahl der **Eingangstüren**; **Auslöseregeln** über
    den Regel-Assistenten mit Rückkehr in den Assistenten.
  - **Alarmprofile** „Abwesend“ und „Nacht“ – vorhandene Profile mit demselben Knopf werden
    ergänzt statt verdoppelt.
  - **Empfänger** (Handy-App vorgewählt) mit **Test-Nachricht** auf Knopfdruck.
  - **Sirenen** eintragen und Profilen zuordnen – die **Freigabe bleibt gesperrt**; optional
    der Sirenentest (einzeln, kurz, leise, mit Bestätigung).
  - **Benutzer** mit optionalem PIN; Hinweis zu den **Bedienteilen**.
  - **Probelauf im Testmodus:** Melder auslösen, Hauswacht hakt jeden erkannten ab. Der
    Assistent bittet um den Testmodus, schaltet ihn aber nicht selbst ein.
  - **Zusammenfassung:** was eingerichtet ist und was noch fehlt.
  - Der Assistent gibt keine Sirenen frei, schaltet keine Geräte und sendet nur auf Knopfdruck.

### Intern
- Gemeinsame Logikschicht für Einstellungen (`core/changes/`): Meldergruppen, Alarmprofile,
  Sirenen, Empfänger, Benutzer, PINs und Bereiche werden für Einstellungsdialog und Assistent an
  einer Stelle geprüft und gespeichert. Der Einstellungsdialog verhält sich unverändert.
- Versionsprüfung kennt Vorabversionen (`0.53.0b1`); CI läuft auch auf `entwicklung/**`.

### Dokumentation
- Neue Seite **Einrichtungsassistent** (deutsch und englisch); Installation, Übersicht der
  Anleitung und Roadmap verweisen darauf.
- ADR 0009 „Einrichtungsassistent und gemeinsame Logikschicht“ (umgesetzt).

## [0.52.0] - 2026-11-17

### Hinzugefügt
- **Anlagenübersicht kennt die neuen Funktionen:**
  - **Zustand:** Gastmodus je Bereich – aus, „bis 17.11.2026, 18:30“ oder „bis zum Ausschalten“.
  - **Benutzer:** neue Zeile „Scharf erzwingen am Keypad“ (ja/nein), auch im Ausdruck.
  - **Neuer Abschnitt „Aktions-Codes“:** Name, Code + Taste, Aktion (bei „scharf“ mit Profil),
    Keypad oder „alle Keypads“. Der Code eines **stillen Notrufs** steht nur als „verborgen“ da –
    der Ausdruck soll niemandem verraten, mit welchem Code man unbemerkt Hilfe ruft.
- **Neue Prüfhinweise:**
  - ⚠️ wichtig (auch unter Reparaturen): Aktions-Code „stiller Notruf“, aber das Ereignis „Alarm“
    hat keinen Empfänger – der Notruf erreicht niemanden.
  - ⚠️ Aktions-Code „scharf“, dessen Alarmprofil gelöscht wurde.
  - ℹ️ Aktions-Code für ein Keypad, das es nicht mehr gibt.
  - ℹ️ Gastmodus ist an (mit Ende) – Profil-Automatik und Erinnerungen ruhen.
- **Notfallblatt:** erklärt, wie man am Keypad trotz offenem Fenster scharf schaltet (noch einmal
  dieselbe PIN/Karte und Taste innerhalb von 10 Sekunden) – nur wenn ein Profil das erlaubt und
  mindestens ein Benutzer das Recht hat.

### Geändert
- **Diagnose-Datei:** Aktions-Codes werden auch in der Übersicht entfernt.

### Dokumentation
- Anlagenübersicht (deutsch und englisch): neue Abschnitte, Prüfhinweise und „Was nie in der
  Übersicht steht“ ergänzt; Bedienteile: Hinweis beim stillen Notruf; Roadmap.

## [0.51.2] - 2026-11-17

### Geändert
- **Einstellung „Verhalten nach Neustart“:** Der Hilfetext sagte noch, ein laufender Alarm werde
  „nie fortgesetzt“. Seit 0.51 ist das einstellbar („Laufenden Alarm fortsetzen“, Standard aus) –
  der Text sagt das jetzt, und dass die Alarm-Empfänger eine wichtige Nachricht bekommen.

### Dokumentation
- **Roadmap** (deutsch und englisch) auf den Stand 0.51 gebracht: Versionen 0.46 bis 0.51
  ergänzt, Grundsatz zum Neustart korrigiert (Fortsetzen ist optional), Grundsatz „Aktions-Codes
  schalten nie unscharf“ ergänzt, Geplantes aktualisiert (Systemübersicht um Gastmodus,
  Aktions-Codes und „Scharf erzwingen“ ergänzen; HmIP-ASIR-Ton je Anlass; wiederkehrende
  Gastmodus-Zeiten).

## [0.51.1] - 2026-11-17

### Geändert
- **Gastmodus auf der Alarm-Karte mit freier Zeit:** Neben den schnellen Auswahlen gibt es jetzt
  „Oder bis:“ mit Datum und Uhrzeit nach Wahl (Vorschlag: morgen zur selben Stunde) und
  „Übernehmen“. Ein Zeitpunkt in der Vergangenheit wird abgelehnt.

### Dokumentation
- Profile (deutsch und englisch): Gastmodus mit freier Zeit, Beispiel „bis Sonntag 18 Uhr“.

## [0.51.0] - 2026-11-17

### Hinzugefügt
- **Gastmodus:** Gäste, Babysitter oder Handwerker im Haus, aber ohne Ortung – solange der
  Gastmodus an ist, schaltet Hauswacht **nicht automatisch** scharf (weder nach Uhrzeit noch
  „wenn alle weg“ noch „immer scharf nach Neustart“); die Erinnerung „nicht scharf“ entfällt.
  Von Hand scharf schalten geht weiter. Einschalten über die **Alarm-Karte** (Knopf „Gastmodus“
  mit Dauer: bis zum Ausschalten, 4 Stunden, bis morgen 10 Uhr, 3 Tage – für jeden, ohne PIN),
  den Schalter `switch.hauswacht_gastmodus` (alle Bereiche) oder die Aktion
  `hauswacht.guest_mode` (mit Ende, je Bereich). Standard: alle Bereiche; eine Karte mit
  `bereich:` schaltet nur ihren Bereich. Endet zum gewählten Zeitpunkt von selbst.
- **Laufenden Alarm fortsetzen** (Verhalten nach Neustart, Standard aus): War beim Neustart ein
  Alarm noch in der Reaktionsphase, wird er nach dem Hochfahren erneut ausgelöst – mit allen
  Sirenen-Sperren.

### Geändert
- **Alarm vor dem Neustart** wird jetzt als **Alarm-Nachricht** an die Alarm-Empfänger gemeldet
  (wichtig, mit „Unscharf“-Knopf) statt nur als System-Nachricht.
- Systemübersicht: „Nach Neustart“ zeigt „laufenden Alarm fortsetzen“.

### Dokumentation
- Installation (deutsch und englisch): Abschnitt „Laufenden Alarm fortsetzen“ mit Abwägung;
  Sicherheitsregel Z1 und ADR 0008 ergänzt.
- Profile (deutsch und englisch): Abschnitt „Gastmodus“ mit Beispiel; Dashboard: Knopf
  „Gastmodus“ und neuer Abschnitt „Eine Karte je Bereich (z. B. Einliegerwohnung)“; Referenz um
  Schalter, Attribute, Aktion und Ereignis ergänzt.
- Referenz (deutsch und englisch): Werte des Attributs `phase` erklärt, Beispiel-Automation
  „Haustür abschließen, wenn scharf“ und „Bei Alarm Licht an“.

## [0.50.0] - 2026-11-16

### Hinzugefügt
- **Trotzdem scharf am Keypad:** Sind beim Scharfschalten Melder offen, antwortet das Keypad wie
  bisher „nicht bereit“. Drückt dieselbe Person innerhalb von 10 Sekunden noch einmal dieselbe
  Taste mit ihrer PIN bzw. Karte, schaltet Hauswacht trotzdem scharf und überbrückt die offenen
  Melder – wie „Trotzdem scharf“ in der Karte. Nur in Profilen mit „nach Bestätigung erlauben“;
  „verweigern“ bleibt verweigern.
- Neues Benutzerrecht **„Darf am Keypad trotzdem scharf schalten“** (Standard an, z. B. für
  Kinder abschaltbar).

### Dokumentation
- Bedienteile (deutsch und englisch): Abschnitt „Trotzdem scharf am Keypad“ mit Beispiel; Benutzer
  und Profile ergänzt.
- Aktions-Codes (deutsch und englisch): weitere Beispiele – Ereignis `hauswacht_event` als
  einfacher Auslöser, Licht an/aus mit zwei Tasten, Scharf schalten plus Rollläden, Testmodus
  ausnehmen, „Ausprobieren, was ankommt“ in den Entwicklerwerkzeugen.

## [0.49.1] - 2026-11-16

### Geändert
- **Keypad einrichten ohne MQTT-Topic:** Im Keypad-Formular wählst du jetzt einfach das
  **Keypad-Gerät** aus der Liste; Hauswacht bildet das MQTT-Topic daraus selbst
  (`zigbee2mqtt/<Name in Zigbee2MQTT>`). Das Feld „MQTT-Topic“ bleibt für Experten – z. B. bei
  einem anderen Basis-Topic – und hat Vorrang, wenn es ausgefüllt ist. Vorhandene Keypads behalten
  ihr Topic.

### Dokumentation
- Bedienteile (deutsch und englisch): Keypad-Gerät und Experten-Topic, Hinweis „Keypad in
  Zigbee2MQTT umbenannt?“, Notruf-Taste „aus“ = nichts Sichtbares.

## [0.49.0] - 2026-11-16

### Hinzugefügt
- **Aktions-Codes** (Bedienteile → Aktions-Codes): Code + Funktionstaste am Keypad löst eine
  festgelegte Aktion aus, z. B. „7777 + 🏠 Haus“ = Außenlicht. Beliebig viele, je Code und Taste
  eine Aktion – derselbe Code kann mit verschiedenen Tasten verschiedene Aktionen haben.
  - **Ereignis** für eigene Automationen über die neue Entität `event.hauswacht_aktions_code`
    (Ereignistyp = Name des Codes); Hauswacht selbst schaltet dabei nichts.
  - **Scharf schalten** mit einem Profil.
  - **Stiller Notruf** – wie SOS „still“, aber unauffällig über eine normale Taste.
  - 2–8 Ziffern, für alle oder ein bestimmtes Keypad. Ein Aktions-Code zählt nie als
    Fehlversuch, ist in der PIN-Sperre aber gesperrt. Er ist kein Ausweis und kann nie unscharf
    schalten. Codes und PINs dürfen sich nicht gleichen (wird beim Speichern geprüft).

### Dokumentation
- Bedienteile (deutsch und englisch): Abschnitt „Aktions-Codes“ mit Beispiel-Automation;
  Tastenbelegung des frient-Keypads (Tag = Haus, Nacht = Mond, Alle = Schloss); Referenz um
  Entität und Ereignis ergänzt.

## [0.48.3] - 2026-11-16

### Sicherheit
- **Am Keypad getippte PINs landen nicht mehr im Klartext im Verlauf.** Zigbee2MQTT legt für den
  getippten Code eine eigene Entität an (z. B. `sensor.keypad_flur_action_code`), und Home
  Assistant speichert sie im Verlauf – damit standen alle PINs lesbar im Verlauf und in Backups.
  Hauswacht braucht diese Entität nicht und deaktiviert sie jetzt automatisch für jedes
  eingerichtete Keypad, auch wenn sie erst später entsteht; dazu kommt einmal eine Nachricht.
  Wer sie bewusst wieder einschaltet, wird nicht überstimmt. Bereits gespeicherte Einträge
  verschwinden mit dem normalen Aufräumen des Verlaufs (Standard: 10 Tage) oder sofort über
  „Recorder: Entitäten bereinigen“. **Empfehlung:** PINs ändern, falls Verlauf oder Backups
  anderen zugänglich waren.

### Dokumentation
- Bedienteile, README und Installation (deutsch und englisch): Abschnitt „PINs nicht im
  Verlauf“, Hinweis beim Entfernen.

## [0.48.2] - 2026-11-16

### Behoben
- **Hinweis bei Master-PIN:** Gibt es einen Master-PIN, aber Benutzer ohne eigenen PIN, hieß es
  bisher, sie könnten am Bedienfeld nicht unscharf schalten – das stimmte nicht. Jetzt: „Benutzer
  ohne eigenen PIN“ – sie schalten mit dem Master-PIN, im Logbuch steht dann „Master-PIN“. Gilt
  für den Hinweis unter Reparaturen und für die Prüfhinweise der Übersicht. Der Hinweis lässt
  sich ignorieren, wenn das so gewollt ist.
- Der Master-PIN steht nicht mehr als möglicher Besitzer in der Kartenliste (er ist keine Person).

### Dokumentation
- Benutzer (deutsch und englisch): Absatz zum Master-PIN im Abschnitt „Das Wichtigste vorab“.

## [0.48.1] - 2026-11-16

### Behoben
- **„Neue Karte anlernen“ wartet jetzt immer auf eine Karte, die während des Dialogs gelesen
  wird.** Bisher sprang der Dialog sofort zu einer Karte aus einem früheren, abgebrochenen
  Versuch. Sobald eine Karte gelesen ist, geht es wie bisher sofort weiter; angeboten wird nur
  diese Karte.

### Geändert
- Neuer Eintrag **„⌨️ Kartennummer eintippen“** in der Kartenliste: ohne Warten, mit den zuletzt
  gelesenen unbekannten Karten zur Auswahl. „Neue Karte anlernen“ heißt jetzt „Neue Karte
  anlernen (hinhalten)“; der Wartetext sagt, dass es automatisch weitergeht.

### Dokumentation
- Bedienteile (deutsch und englisch): Anlernen, Eintippen, Hinweis „frient-Keypad: Unscharf
  drücken“, Türschlösser angepasst.

## [0.48.0] - 2026-11-16

### Hinzugefügt
- **Karten und Anhänger an einer Stelle** (Benutzer und PINs → Karten und Anhänger): Liste aller
  RFID-Karten, Anhänger, Finger und Schloss-Kennungen mit Name, Nummer, Besitzer und „zuletzt
  benutzt“ (🟢 aktiv, ⏸️ deaktiviert). Karte antippen: umbenennen, einem anderen Benutzer geben,
  deaktivieren, löschen.
- **Neue Karte anlernen am Stück:** „Halte die neue Karte jetzt ans Keypad …“ – der Dialog wartet
  bis zu 2 Minuten, erkennt die Karte und fragt Name und Benutzer ab. Schon vorher gelesene Karten
  stehen direkt zur Auswahl, Nummern lassen sich weiter eintippen.
- **Karten deaktivieren:** Eine deaktivierte Karte schaltet nichts. Wird sie benutzt, kommt eine
  Nachricht („Die deaktivierte Karte ‚Geldbörse‘ (Christian) wurde an Keypad Flur benutzt“), und
  es zählt als Fehlversuch für die Sperre. Bei Schloss-Kennungen: Nachricht, kein Fehlversuch.
- **PIN-Liste** (Benutzer und PINs → PINs): wer hat PIN bzw. Bedrohungs-PIN, wann zuletzt benutzt;
  Benutzer antippen: PIN bzw. Bedrohungs-PIN setzen, ändern, entfernen. PINs selbst sind nie
  sichtbar.

### Geändert
- Der Benutzer-Dialog enthält keine Karten- und PIN-Felder mehr, sondern zeigt den Stand
  („2 Karten · PIN gesetzt“) mit Verweis auf die beiden Listen. Das Formular „Namen der Karten“
  aus 0.47 entfällt – Namen vergibst du jetzt in der Kartenliste.
- Vorhandene Karten, Namen und PINs bleiben unverändert erhalten; es muss nichts umgestellt
  werden. Wird ein Benutzer gelöscht, werden seine Karten mit gelöscht.
- Systemübersicht: deaktivierte Karten mit ⏸.

### Dokumentation
- Bedienteile (deutsch und englisch): Abschnitt „Karten anlernen“ neu – Kartenliste, Anlernen,
  Bearbeiten/Deaktivieren/Löschen mit Beispielen („Geldbörse weg“); Finger und Türschlösser
  angepasst.
- Benutzer (deutsch und englisch): Menüübersicht, neuer Abschnitt „PINs“ mit Beispiel.

## [0.47.0] - 2026-11-16

### Hinzugefügt
- **Namen für RFID-Karten, Finger und Schloss-Kennungen.** Nach dem Speichern eines Benutzers mit
  Karten folgt das Formular „Namen der Karten“ – ein Feld je Karte, z. B. „Schlüsselbund“ oder
  „Geldbörse“; leer = ohne Namen. Damit
  - steht im Benutzer-Dialog „Schlüsselbund (04A1B2C3)“ statt nur der Nummer – bei Verlust ist
    klar, welche Karte zu löschen ist,
  - zeigen Logbuch, „Geändert von“ und Nachrichten, welche Karte benutzt wurde:
    „Christian · Schlüsselbund (Keypad Flur)“,
  - zeigt die Systemübersicht „Schlüsselbund …B2C3“.
  - Wird eine Karte entfernt, verschwindet ihr Name mit. Die Namen werden in der
    Diagnose-Datei entfernt (sie enthalten die Kartennummern).

### Dokumentation
- Bedienteile (deutsch und englisch): neuer Abschnitt „Karten benennen – und eine verlorene Karte
  löschen“ mit Beispiel; Benutzer und Systemübersicht ergänzt.

## [0.46.0] - 2026-11-16

### Hinzugefügt
- **Sirenen, die beim Neustart noch liefen, werden ausgeschaltet.** Hauswacht merkt sich jetzt
  dauerhaft, welche Sirenen es selbst eingeschaltet hat. Startet Home Assistant mitten in einem
  Alarm neu, schaltet Hauswacht diese Sirenen nach dem Hochfahren aus – und nach der Startphase
  (2 Minuten) ein zweites Mal, falls eine dann noch „an“ meldet. Bisher lief eine Sirene ohne
  eigene Laufzeit (z. B. ein Relais als Sirene) weiter, und auch Unscharfschalten schaltete sie
  nicht mehr aus. Nachricht „Hauswacht: Sirene nach Neustart“ (Ereignis „System“).
  - Nur eigene Sirenen; nie Sirenen, die inzwischen ein neuer Alarm nutzt.
  - Brand geht vor: Meldet ein Rauchmelder Brand, wird nichts ausgeschaltet; Hauswacht meldet das
    und versucht es jede Minute erneut. Auch Unscharfschalten vergisst die Sirene nicht.

### Geändert
- **Ausschalten eigener Sirenen ist auch ohne Sirenenfreigabe erlaubt** – Ausschalten ist immer
  die sichere Richtung. Einschalten bleibt ohne Freigabe gesperrt; Testmodus und Brandsperre
  sperren weiterhin beides. Sicherheitsregel S2 angepasst, S15 neu (deutsch und englisch),
  Nachtrag zu ADR 0008.
- Wiederholte Ausschaltversuche (Brandsperre) richten sich nach dem aktuellen Testmodus, nicht
  nach dem beim ersten Versuch. Sirenen, die sich gar nicht ausschalten lassen, werden nicht
  endlos erneut versucht.

### Dokumentation
- Sirenen (deutsch und englisch): neuer Abschnitt „Sirene lief beim Neustart noch“ mit Beispiel;
  Installation, README und Sicherheitsregeln ergänzt.

### Intern
- Test der Zeitautomatik startet fest um 12:00 (hing von der Uhrzeit des Testlaufs ab).

## [0.45.3] - 2026-11-16

### Behoben
- **Nach einem Neustart offen vorgefundene Melder sind jetzt wirklich bis zum Schließen
  überbrückt** – genau wie nach „Alarm beenden“. Bisher waren sie nur als „überbrückt bis zum
  Schließen“ vermerkt, aber nicht ignoriert: Meldete so ein offenes Fenster nach der Startphase
  kurz „nicht verfügbar“ und dann wieder offen, löste es Alarm aus. Jetzt nicht mehr; nach dem
  Schließen ist es wieder normal überwacht. Das Attribut `bypassed_sensors` am Bedienfeld führt
  diese Melder jetzt ebenfalls auf. Gespeicherte Zustände älterer Versionen werden beim Start
  entsprechend übernommen.

### Dokumentation
- Verhalten nach Neustart (deutsch und englisch): Melder, die **schon beim Wiederherstellen**
  offen gemeldet sind, werden immer bis zum Schließen überbrückt – auch Eingangstüren (mit
  Begründung). Nur Eingangstüren, die sich erst später offen melden, starten die
  Eingangsverzögerung.
- „Immer scharf“: Die Nachricht „automatisch scharf (Neustart)“ kommt über das Ereignis
  „Automatik“, „nicht scharf geschaltet“ über „Scharfschaltung abgelehnt“ – wer diese Ereignisse
  abschaltet, bekommt sie nicht.

## [0.45.2] - 2026-11-16

### Dokumentation
- **Korrektur von 0.45.1:** Die Änderung zu „überbrückt“ war falsch. Richtig ist (wie bis 0.45.0
  beschrieben): Nach „Trotzdem scharf“ sind überbrückte Melder **bis zum Unscharfschalten nicht
  überwacht**, auch wenn sie geschlossen und wieder geöffnet werden. Nur nach „Alarm beenden“ und
  nach einem Neustart gilt „überbrückt bis zum Schließen“. Doku (deutsch und englisch),
  Begriffe, Testmodus, Zustandsmodell und Testkarte entsprechend korrigiert und um ein Beispiel
  ergänzt.
- Richtig bleibt aus 0.45.1: Bestätigte ausgefallene Melder lösen aus, wenn sie offen
  zurückkommen.

## [0.45.1] - 2026-11-16

### Dokumentation
- **„Überbrückt“ richtig beschrieben:** Nach „Trotzdem scharf“ löst der offene Zustand eines
  Melders keinen Alarm aus; sobald er geschlossen wird, ist er wieder normal überwacht – erneutes
  Öffnen löst aus. Bisher stand in der Doku fälschlich „bis zum Unscharfschalten nicht überwacht“.
  Ebenso für bestätigte ausgefallene Melder, die offen zurückkommen. Mit Beispiel (deutsch und
  englisch), Begriffe, Testmodus, Zustandsmodell.
- Testkarte: Der Hinweis „überbrückt“ sagt jetzt, dass der Melder nach „Zu“ wieder überwacht ist.

## [0.45.0] - 2026-11-16

### Neu
- **Verhalten nach Neustart einstellbar** (Systemeinstellungen → Verhalten nach Neustart):
  - **Vorherigen Zustand wiederherstellen (neuer Standard):** War die Anlage scharf, ist sie nach
    dem Neustart sofort wieder scharf – gleiches Profil, gleiche überbrückte Melder, ohne erneute
    Prüfung und ohne Ausgangsverzögerung. Eine laufende Eingangsverzögerung beginnt neu. Ein
    laufender Alarm wird nie fortgesetzt (keine Sirenen), die Anlage ist scharf und meldet ihn.
    Nachricht „Hauswacht: nach Neustart wieder scharf“.
  - **Immer scharf** mit festem Profil je Bereich: etwa eine Minute nach dem Hochfahren normal
    scharf geschaltet (mit Prüfung offener Melder).
  - **Immer unscharf:** das bisherige Verhalten.
- **Startphase nach dem Wiederherstellen** (2 Minuten): keine Ausfallmeldungen für Melder, die
  beim Hochfahren kurz fehlen; Melder, die offen gemeldet werden, werden bis zum Schließen
  überbrückt und gemeldet („offen nach Neustart“) statt nachts Alarm auszulösen – Eingangstüren
  starten stattdessen die Eingangsverzögerung.
- Die Profil-Automatik merkt sich über den Neustart, ob sie scharf geschaltet hatte.
- Übersicht-Karte zeigt die Einstellung unter „Überwachung“; neues Ereignis
  `RestoredAfterRestart`.

### Geändert
- **Standardverhalten nach Neustart:** bisher immer unscharf, jetzt „vorherigen Zustand
  wiederherstellen“. Wer das alte Verhalten möchte, wählt „Immer unscharf“. Das gilt schon für
  den ersten Neustart nach dem Update: War die Anlage beim Update scharf, ist sie danach wieder
  scharf.
- Sicherheitsregeln Z1/Z2 angepasst; ADR 0008 löst ADR 0004 ab.

### Dokumentation
- Installation: „Verhalten nach einem Neustart“ mit Tabelle, Startphase, Beispiel (deutsch und
  englisch); Fehlersuche, Profile, Referenz, Sicherheitsregeln, Roadmap, Zustandsmodell.

## [0.44.3] - 2026-11-15

### Behoben
- **„Unscharf um“ über Nacht mit Wochentagen:** Bei einem Profil über Nacht (z. B. scharf
  23:00, unscharf 06:30) mit Tagen Mo–Fr blieb die Anlage nach Freitagnacht das ganze Wochenende
  scharf, weil Samstag kein aktiver Tag ist. Jetzt gehört der Morgen zur Nacht davor: Hauswacht
  schaltet auch am Morgen nach einem aktiven Tag unscharf. Tagesprofile sind unverändert.

### Dokumentation
- Profile: „Uhrzeiten, über Nacht und scharf von Hand“ mit Wochenbeispiel und dem Verhalten,
  wenn ein Profil mit Uhrzeiten von Hand scharf geschaltet wird (deutsch und englisch).

## [0.44.2] - 2026-11-15

### Behoben
- Reparatur-Hinweis „nicht alle Personen haben einen PIN“ nannte auch Home-Assistant-Konten,
  die gar keine Hauswacht-Benutzer sind – z. B. Dienstkonten für Grafana oder MQTT und ein
  Wandtablet-Konto, dem die Doku bewusst keinen Benutzer gibt. Jetzt zählen nur noch
  Hauswacht-Benutzer ohne PIN (gemeldet im simon42-Forum). Der Hinweis heißt jetzt „nicht alle
  Benutzer haben einen PIN“ und nennt die Alarmkarte als weiteren Ausweg; „an/aus“ erscheint auf
  Englisch als „on/off“.

## [0.44.1] - 2026-11-15

### Dokumentation
- **Fingerabdruck-Leser mit ESPHome** (Bedienteile, deutsch und englisch): ESP32 mit
  R503-Sensor, vollständige ESPHome-Konfiguration, Finger anlernen und dem Benutzer zuordnen –
  in Hauswacht als RFID-Leser, ohne neue Funktion. Dazu der Hinweis, dass Fingerabdrücke am Nuki
  Keypad 2.0 wie Keypad-Codes angelernt werden.

## [0.44.0] - 2026-11-15

### Dokumentation
- **Anleitung auf Englisch:** alle Nutzerseiten und die Sicherheitsregeln unter `docs/en/`,
  mit den Begriffen der englischen Oberfläche und den englischen Entitäts-IDs. Jede Seite
  verlinkt oben ihr Gegenstück in der anderen Sprache („Deutsch | English“).
- **README auf Englisch** (`README.en.md`) statt der aufklappbaren Zusammenfassung; das
  deutsche README bleibt die Startseite.
- Tests stellen sicher, dass es zu jeder deutschen Seite die englische gibt, dass beide
  einander verlinken und dass alle Links und Anker stimmen.
- Profile: Hinweis zu Profilen namens „Unscharf“ ohne Verweis auf andere Integrationen.

### Geändert
- Einstellungen: Der Menüpunkt „Bedienteile“ nennt jetzt auch Taster und Türschlösser.

## [0.43.0] - 2026-11-15

### Neu
- **Taster als Bedienteil:** Ein Taster (Ereignis-Entität, z. B. von Zigbee2MQTT, Hue,
  Shelly, Matter, oder ein Aktions-Sensor) schaltet je Druckart ein Alarmprofil scharf – mit
  dessen Ausgangsverzögerung. Ein Taster weist niemanden aus und schaltet deshalb **nur
  scharf**, nie unscharf, nie über ein anderes Profil hinweg. Verlangen die PIN-Regeln einen
  PIN zum Scharfschalten, schaltet er nicht (Systemmeldung).
- **Türschloss als Bedienteil:** unscharf, wenn ein bekannter Benutzer aufschließt – mit dessen
  Rechten je Bereich. Quellen: **Nuki über MQTT** (`lockActionEvent`: Auth-ID bzw. Keypad-Code)
  oder **allgemein** (Sensor oder Ereignis mit der Kennung). Hauswacht verlangt zusätzlich, dass
  das Schloss in Home Assistant innerhalb von 30 s wirklich aufschließt. Nie unscharf bei
  unbekannter oder fehlender Kennung, Knopf innen, Zeitsteuerung, automatischem Abschließen,
  Aufschließen über Home Assistant/HomeKit/MQTT oder bloßem Öffnen der Tür. Optional:
  **Abschließen von außen** schaltet ein Profil scharf.
- Schloss-Kennungen gehören wie RFID-Karten zum Benutzer und werden genauso angelernt (Feld
  „RFID-Karten und Schloss-Kennungen“, Anzeige z. B. „Nuki-Benutzer 52653“).
- Übersicht-Karte zeigt Taster und Türschlösser; neue Ereignisse `ButtonPressed`,
  `LockIdentified`, `LockIgnored`.

### Dokumentation
- Bedienteile: Abschnitte „Taster“ und „Türschloss (z. B. Nuki)“ mit Einrichtung Schritt für
  Schritt, Aufbau der Nuki-Nachricht, Anlernen, „Abschließen = scharf“ und allgemeiner Quelle;
  Fehlersuche für Taster und Schloss; Referenz der Ereignisse.
- README: Hinweis, dass Hauswacht mit viel Hilfe von KI (Claude) entstanden ist.

## [0.42.1] - 2026-11-15

### Geändert
- „Unscharf mit Türbeleg“: Das Zeitfenster heißt jetzt „so lange vor der Tür darf das Handy
  ‚zuhause‘ melden“ (Entität `number.hauswacht_turbeleg_ortung_vor_der_tur`, vorher
  `…_turbeleg_zeitfenster` – nur der Name für neue Installationen; bestehende Entitäts-IDs
  bleiben). Die Beschreibung sagt deutlich: Das Zeitfenster verzögert den Alarm nicht.

### Dokumentation
- Profile: neuer Abschnitt „Was das Zeitfenster bedeutet“ mit Beispieltabelle (Handy vor bzw.
  nach der Tür, ohne Handy); Fehlersuche präzisiert.

## [0.42.0] - 2026-11-15

### Neu
- **Anwesenheit aus mehreren Signalen:** Die zusätzlichen Signale je Person (WLAN-Sensor,
  Bluetooth, Router, „Nähe“, beliebiger Binärsensor wie eine HomeKit-Variable) gelten jetzt
  auch für die Profil-Automatik. Zuhause, sobald ein Signal zuhause meldet; weg erst, wenn
  alle sicher weg melden – unbekannt oder nicht verfügbar zählt nie als weg. Eingestellt an
  einer Stelle: Systemeinstellungen → **Anwesenheit und Heimkehr-Beobachtung**. Der
  Signal-Schritt zeigt auch die Personen aus der Automatik der Profile.
- **„Unscharf bei Rückkehr“ in drei Stufen:** Aus (Standard), Wie bisher (nur nach
  automatischem Scharfschalten) und neu **Mit Türbeleg**: Rückkehr einer Person und Öffnen
  einer Eingangstür innerhalb eines Zeitfensters (Standard 5 Minuten), egal in welcher
  Reihenfolge – auch während der Eingangsverzögerung und unabhängig davon, wie scharf
  geschaltet wurde. Geister-Heimkehrten ohne Tür bewirken nichts; ein laufender Alarm wird nie
  beendet.
- **Empfehlung für die Eingangsverzögerung:** Der Heimkehr-Bericht nennt je Person, welche
  Eingangsverzögerung „Mit Türbeleg“ bräuchte (Attribut `door_proof`).
- Neue Ereignisse `ArrivalNoted` und `DoorNoted`.

### Geändert
- Der Schalter „Unscharf beim Heimkommen“ (`switch.hauswacht_unscharf_beim_heimkommen`) ist
  durch die Auswahl **„Unscharf bei Rückkehr“** (`select.hauswacht_unscharf_bei_ruckkehr`)
  ersetzt; dazu kommt `number.hauswacht_turbeleg_zeitfenster`. Bestehende Einstellungen werden
  übernommen („an“ = „Wie bisher“), der alte Schalter wird entfernt. Wer ihn im Dashboard
  oder in Automationen nutzt, stellt auf die Auswahl um.

### Dokumentation
- Profile: „Woran Hauswacht erkennt, wer zuhause ist“ und „Unscharf bei Rückkehr“ mit
  Alltagsbeispielen; Beobachtungen: Empfehlung lesen; Fehlersuche, Referenz (Entitäten und
  Ereignisse der Automatik), Roadmap (Wünsche aus dem simon42-Forum).

## [0.41.2] - 2026-11-15

### Behoben
- **Keypad einrichten:** Der Dialog zeigte statt der Beschreibung „Translation error:
  UNCLOSED_TAG“. Ursache war `<Topic>` im deutschen Text, das Home Assistant als HTML-Tag
  liest. Ein Test verhindert spitze Klammern in Übersetzungen künftig.

### Dokumentation
- Deutlicher Hinweis: „Unscharf“ ist kein Alarmprofil; Keypad-Tasten nur mit Profilen zum
  Scharfschalten belegen. MQTT-Topic genau wie in Zigbee2MQTT schreiben.

## [0.41.1] - 2026-11-13

### Dokumentation
- Sirenen-Seite überarbeitet: Überblick über das Sirenen-Menü, Einrichtung Schritt für Schritt,
  Beispiele (Homematic IP Alarmsirene, Außensirene mit Ton „fire“, Sirene am Schaltaktor) und
  eine Tabelle aller Gründe, warum eine Sirene nicht geklingelt hat.
- Fehlersuche: Alarmkarte fragt nach PIN, ausgegraute Knöpfe, Sirene nur als Schalter,
  gesperrter Brandton, Sprache der Meldungen.
- Benutzerdialog: Das Feld „Home-Assistant-Konto“ nennt jetzt auch die Alarmkarte.

## [0.41.0] - 2026-11-13

### Hinzugefügt
- **Brandton als Experten-Freigabe** (Ton je Sirene): Täuscht der Name – z. B. heißt der einzige
  laute Ton einer Außensirene „fire“ –, lässt sich dieser eine Ton mit eigener Bestätigung für
  Einbruch freigeben. Nie für Rauchmelder mit Sirene (Geräte mit eigenen Brandsensoren); die
  Brandsperre gilt weiter. Die Übersicht zeigt die Freigabe als Hinweis.

## [0.40.0] - 2026-11-13

### Hinzugefügt
- **Ton je Sirene:** Für Sirenen mit eigenen Tonnamen – z. B. die Homematic IP Alarmsirene
  (HmIP-ASIR) mit `FREQUENCY_RISING_AND_FALLING` – lässt sich der Ton festlegen (Alarmgeber –
  Sirenen → Ton je Sirene). Auswahl aus den Tönen, die das Gerät meldet; Brandtöne bleiben
  gesperrt. Gilt bei Alarm und Sirenentest.
- **Assistent „Sirene aus Schalter erstellen“:** macht aus einem Schalter (`switch.…`) über den
  Home-Assistant-Helfer „Gerätetyp eines Schalters ändern“ eine Sirene und trägt sie gleich ein.
- **Experten: Schalter direkt als Sirene** (Sirenen und Freigabe): Hauswacht schaltet den
  Schalter bei Alarm ein und nach der Alarmdauer aus – mit Freigabe, Brandsperre und Testmodus.
- **Prüfhinweis** (wichtig, auch unter Reparaturen): Sirene kennt keinen Einbruchton und bliebe
  bei einem Alarm stumm.

### Geändert
- Brandtöne werden auch an herstellereigenen Namen erkannt („fire“, „smoke“, „Brand“).

## [0.39.0] - 2026-11-13

### Hinzugefügt
- **Englische Platzhalter** für eigene Texte und Ansagen: `{area}`, `{profile}`, `{sensor}`,
  `{open}`, `{who}`, `{seconds}`, `{time}`, `{rule}`, `{reason}` – gleichwertig zu den deutschen
  (`{bereich}`, `{profil}`, `{melder}` …), auch gemischt. Der Einstellungsdialog nennt sie in der
  Sprache von Home Assistant; Fehler in eigenen Texten werden ebenfalls übersetzt.

### Geändert
- „gemeinsamer PIN (A, B)“ heißt bei englischer Sprache „shared PIN (A, B)“.
- Die englischen Standardansagen nutzen die englischen Platzhalter.

## [0.38.0] - 2026-11-13

### Hinzugefügt
- **Englische Benachrichtigungen:** Alle Meldungen von Hauswacht – Push-Nachrichten, Meldungen
  in Home Assistant, Knöpfe in der Push-Nachricht („Disarm“, „Arm anyway“ …), Bedrohungsalarm,
  Sirenentest, Heimkehr-Bericht und CSV-Tabelle – folgen jetzt der Sprache von Home Assistant:
  Deutsch bei deutscher Einstellung, sonst Englisch. Bisher waren sie immer deutsch.
- Die englische CSV-Tabelle nutzt Komma statt Semikolon (passend zu englischem Excel).

### Geändert
- Bei englischer Sprache heißen die Quellen der Heimkehr-Beobachtung im Sensor-Attribut
  `sources` jetzt „(overall)“ bzw. „(earliest signal)“ statt „(gesamt)“ bzw. „(frühestes
  Signal)“.

### Dokumentation
- README: Status „Beta“ und eine kurze englische Zusammenfassung (aufklappbar).

## [0.37.0] - 2026-11-13

### Hinzugefügt
- **Visueller Editor für alle Hauswacht-Karten** – kein „Visueller Editor wird nicht
  unterstützt“ mehr.
- **Karte „Hauswacht Alarm“ anpassbar:**
  - Bereich, Größe (groß fürs Tablet oder kompakt)
  - welche Profilknöpfe in welcher Reihenfolge, Knöpfe je Zeile
  - was angezeigt wird: wer zuletzt geschaltet hat, offene und nicht erreichbare Melder,
    Testmodus, Countdown-Balken, „Alle Bereiche unscharf“, Blinken bei Alarm
  - eigene Farben je Zustand (Vorrang vor dem Theme)
  - Rückfrage vor dem Scharf- bzw. Unscharfschalten, z. B. fürs Wandtablet (Standard aus; mit
    PIN keine zusätzliche Frage)
- „Unscharf schalten“, „Alarm beenden“ und die PIN-Regeln bleiben bewusst nicht einstellbar.

## [0.36.0] - 2026-11-13

### Hinzugefügt
- **Heimkehr-Bericht zum Herunterladen:** In der Karte „Hauswacht Übersicht“ unter Überwachung
  gibt es den Bericht als Markdown-Datei und alle Einzelwerte als **Tabelle (CSV)** – jede
  Heimkehr und jeder Eingang mit Zeitpunkt, Quelle, Tür, Sekunden nach dem Öffnen, Abwesenheit
  und Ergebnis. Die CSV öffnet sich direkt in Excel (Semikolon, UTF-8).
- Die Benachrichtigung des Knopfs „Heimkehr-Bericht“ weist auf den Download hin.
- WebSocket-Befehl `hauswacht/homecoming/report` (nur Administratoren).

### Dokumentation
- README schlanker: die Befehle für Entwickler stehen jetzt nur noch unter
  [Tests](docs/entwicklung/testing.md).
- Installation über den Marketplace (ab Home Assistant 2026.11) und HACS beschrieben, mit Knopf
  „Integration einrichten“ (My Home Assistant) in README und Installationsanleitung.

## [0.35.1] - 2026-11-13

### Geändert
- **Karte „Hauswacht Alarm“:** feste Farben (grün unscharf, orange Verzögerung, rot scharf,
  leuchtend rot Alarm) statt der Zustandsfarben von Home Assistant, in denen „scharf“ grün ist.
  Anpassbar im Theme über `hauswacht-*-color`.

### Hinzugefügt
- **Beispiel-Dashboard „Alarmanlage“** (`examples/dashboard/hauswacht-dashboard.yaml`): Ansicht
  „Alarm“ mit Alarmkarte, Türen und Fenster, Bewegung, Rauchmeldern, Technik und Verlauf;
  Ansicht „Verwaltung“ mit Übersicht, Einstellungen und Testkarte.

## [0.35.0] - 2026-11-13

### Hinzugefügt
- **Karte „Hauswacht Alarm“** zum Scharf- und Unscharfschalten, groß fürs Tablet: Zustand in
  Farbe mit Countdown und ablaufendem Balken, ein Knopf je Alarmprofil, „Unscharf schalten“,
  im Alarm zusätzlich „Alarm beenden“ und der auslösende Melder. Offene Melder stehen vor dem
  Scharfschalten da; verlangt das Profil eine Bestätigung, gibt es „Trotzdem scharf schalten“.
  Mehrere Bereiche untereinander mit „Alle Bereiche unscharf“.
- **Ohne PIN-Zwang:** Die Karte nimmt das angemeldete Home-Assistant-Konto als Ausweis.
  Zugeordnete Konten schalten ohne PIN mit den Rechten ihres Benutzers, auch wenn es PINs
  (z. B. fürs Keypad) gibt. Einen PIN verlangt sie nur
  - beim Benutzer mit „In der Alarmkarte PIN verlangen“ (z. B. Wandtablet) und
  - für Konten ohne Hauswacht-Benutzer (PIN-Regel, Standard an).
  Mit PIN gelten Sperre, Bedrohungs-PIN und Rechte wie am Bedienfeld.
- Übersicht zeigt die neuen Einstellungen; WebSocket-Befehle `hauswacht/alarm/info` und
  `hauswacht/alarm/action`.

## [0.34.0] - 2026-11-13

### Hinzugefügt
- **Karte „Hauswacht Übersicht“** (nur Administratoren): die ganze Konfiguration auf einen
  Blick – Zustand, Alarmprofile, Melder × Profil (einzeln scharf / nur in Regeln /
  ausgenommen) mit Batterie, Auslöseregeln im Klartext, Sirenen mit letztem Test, Benutzer
  (ohne PINs, Karten gekürzt), Bedienteile, Benachrichtigungen, Überwachung.
- **Drucken** als A4 (volles Programm) und **Notfallblatt** für Familie und Gäste.
- **Prüfhinweise:** Hauswacht findet Lücken (Melder in keinem Profil scharf, Profil erreicht
  niemanden), Vergessenes (Sirene nie getestet, Bedrohungs-PIN ohne Empfänger, abgelaufene
  Gäste) und Widersprüche (Funkstille knapper als empfohlen, Benutzer ohne PIN). Wichtige
  Hinweise erscheinen zusätzlich unter Einstellungen → Reparaturen und verschwinden von selbst,
  wenn sie behoben sind.
- **Diagnose-Datei** für Fehlerberichte, ohne PINs, Karten, Personen und Empfänger.
- WebSocket-Befehl `hauswacht/overview` (nur Administratoren).

## [0.33.0] - 2026-11-12

### Dokumentation
- **Neu gegliedert:** Statt einer langen Anleitung jetzt einzelne Seiten unter `docs/` –
  Installation, Melder, Alarmprofile und Bereiche, Auslöseregeln, Bedienung und Dashboard,
  Benutzer und PINs, Bedienteile, Sirenen, Benachrichtigungen, Testmodus, Beobachtungen,
  Referenz (alle Entitäten, Attribute, Aktionen, Ereignisse) und **Fehlersuche**.
- **README** neu: Überblick, Funktionen, Schnellstart, Sicherheit; mit Bildern der Karten.
- Entwicklerdoku nach `docs/entwicklung/` verschoben, ADR-Übersicht, Roadmap gestrafft.
- Neue Seite **Bedienteile** mit Karten anlernen, Zufallsnummern, Reihenfolge am Keypad.
- Test prüft, dass alle Links und Anker in der Doku stimmen.

### Hinzugefügt
- Issue-Vorlagen für Fehler und Wünsche (mit Hinweis, keine persönlichen Daten zu posten).

### Geändert
- Karten: „Zonen“ heißen auch dort „Meldergruppen“; die Testkarte verlinkt auf die Seite
  Testmodus.
- Geräte weiterer Bereiche hängen über `via_device_id` am Hauswacht-Gerät (die alte Angabe
  `via_device` entfällt ab Home Assistant 2027.8).

### Entfernt
- Ungenutzter Code im Sirenentest.

## [0.32.3] - 2026-11-12

### Geändert
- **Fehlversuche verfallen:** 24 Stunden nach dem letzten Fehlversuch beginnt die Zählung
  wieder bei null (gleitend, nicht um Mitternacht). Bisher galten sie bis zur nächsten
  richtigen Eingabe oder bis zum Neustart. Eine laufende Sperre endet unverändert nach ihrer
  Dauer.

## [0.32.2] - 2026-11-12

### Dokumentation
- Neuer Abschnitt **„Sperre nach falschen Eingaben“** in der Installationsanleitung: Stufen als
  Tabelle, was zählt und was nicht, Zurücksetzen, Verhalten während der Sperre und bei
  laufendem Alarm. Kurzfassung auch im Dialog „PIN-Regeln“.

## [0.32.1] - 2026-11-12

### Behoben
- **Zufallsnummern** (4-Byte-UID mit `08` am Anfang, z. B. Handys oder Ausweise im
  Datenschutz-Modus) werden nicht mehr zum Anlernen angeboten – sie ändern sich bei jedem
  Lesen. Der Benutzer-Dialog zeigt stattdessen einen Hinweis und lehnt das Speichern solcher
  Nummern ab.

## [0.32.0] - 2026-11-12

### Hinzugefügt
- **Anlernzeit für neue Karten** (Bedienteile → Anlernen neuer Karten): Standard 5 Minuten,
  1–60 Minuten oder 0 = Anlernen aus.

### Geändert
- Unbekannte Karten werden nur gemerkt, wenn alle Bereiche unscharf sind, und nach Ablauf der
  Anlernzeit vergessen. Wird eine angebotene neue Karte erst danach gespeichert, lehnt der
  Dialog das ab („erneut an das Keypad halten“). Eingetippte Karten-IDs sind davon nicht
  betroffen.

## [0.31.0] - 2026-11-12

### Hinzugefügt
- **Falscheingaben zurücksetzen:** Knopf in der Karte „Hauswacht Test“ (mit Anzahl) und Dienst
  `hauswacht.reset_code_lock` – setzt Zähler und PIN-Sperre zurück. Nur für Administratoren.
- Attribute `code_failures` und `code_locked_until` am Bedienfeld.

### Geändert
- Unbekannte Karten (Codes, die kein PIN sein können) zählen nicht mehr als Fehleingabe –
  Anlernen löst keine Sperre mehr aus.

## [0.30.0] - 2026-11-12

### Hinzugefügt
- **Karten anlernen:** Eine unbekannte Karte einmal an ein Keypad oder einen Leser halten – sie
  erscheint dann beim Benutzer unter „RFID-Karten/-Anhänger“ als „neu“ zur Auswahl. Codes mit
  4–8 Ziffern (mögliche PINs) werden nie angezeigt.

### Geändert
- „RFID-Karten/-Anhänger“ ist jetzt eine Auswahl mit beliebig vielen Einträgen statt eines
  Textfelds (eigene IDs lassen sich weiter eintippen).
- Dokumentiert und getestet: Karten sind unabhängig vom PIN. Benutzer ohne PIN schalten mit
  ihrer Karte am Keypad; das Bedienfeld bleibt ohne PINs PIN-frei.

## [0.29.0] - 2026-11-12

### Hinzugefügt
- **Rechte je Bereich:** Beim Benutzer wählbar, ob die Rechte für alle Bereiche gleich gelten
  oder je Bereich einzeln (scharf, unscharf, Alarm beenden). Ein Bereich ohne Auswahl ist für
  den Benutzer gesperrt. Eine bisherige Beschränkung auf Bereiche wird als Vorbelegung
  übernommen und gilt unverändert weiter, bis der Benutzer neu gespeichert wird.

### Geändert
- Unscharf schalten über ein Bedienteil für mehrere Bereiche schaltet nur die Bereiche, in
  denen der Benutzer unscharf schalten darf (vorher: Abbruch beim ersten gesperrten Bereich).
- NFC-Aufkleber prüfen die Rechte des Handy-Besitzers je Bereich.

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
