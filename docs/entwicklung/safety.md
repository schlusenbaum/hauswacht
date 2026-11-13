# Sicherheitsregeln

Diese Regeln sind verbindlich. Sie dürfen nicht vereinfacht werden, um die Implementierung zu
erleichtern. Jede Regel ist durch Tests abgesichert.

## Sirenen

Implementierung: `custom_components/hauswacht/core/siren_guard.py`
Tests: `tests/core/test_siren_guard.py`, `tests/core/test_static_safety.py`, `tests/integration/test_reactions.py`

| Nr. | Regel | Grund |
|---|---|---|
| S1 | Testmodus aktiv → keinerlei Sirenenbefehle | Fehlbedienung im Test darf keinen echten Alarm auslösen |
| S2 | Hardware-Freigabe aus → keinerlei Sirenenbefehle. Standard nach Installation: **aus** | Sirenen erst nach bewusster Freigabe |
| S3 | Brand an irgendeinem Melder **aktiv** oder an einer registrierten Sirene **unklar** → keine Einbruch-Aktivierung | Brandalarm hat Vorrang, kein verwirrender Einbruchton während einer Evakuierung |
| S4 | Brand an irgendeinem Melder **aktiv** oder an einer registrierten Sirene **unklar** → kein einziger Ausschaltbefehl | Ein Stoppbefehl könnte einen lokalen Brandalarm stumm schalten (nicht ausgeschlossen) |
| S5 | Ausschalten nur für Geräte, die Hauswacht selbst aktiviert hat | Fremde Alarme werden nie beeinflusst |
| S6 | Brandtöne (`fire`, `fire_panic`) sind für Einbruchalarme verboten | Eindeutige Unterscheidung der Alarmarten |
| S7 | Laufzeit wird auf die gerätseitige Höchstdauer begrenzt; diese wird **nie verändert** | Gerätewert kann das Brandverhalten beeinflussen |
| S8 | Sirenen-Services werden nur im Siren Executor aufgerufen | Ein einziger, prüfbarer Pfad |
| S9 | Fremde Abschalt-Scripts (z. B. ein Script, das alle Rauchmelder abschaltet) werden nie verwendet | Würde einen Brandalarm beenden |
| S10 | Ton, Lautstärke und Dauer nur senden, wenn die Sirene sie unterstützt; fehlender Einbruchton → anderer Einbruchton, nie ein Brandton; nur Brandtöne → keine Ansteuerung | Abgelehnte Befehle ließen die Sirene stumm |
| S11 | Rauchmelder ohne Tonauswahl → keine Einbruch-Ansteuerung | Ihr Standardton ist meist der Brandton |
| S12 | Sirene ohne Dauer **und** ohne Ausschalten → keine Ansteuerung; Sirene ohne Ausschalten → kein Ausschaltbefehl | Hauswacht muss jeden Ton selbst begrenzen können |
| S13 | Ende der Reaktionszeit und Unscharfschalten → eigene Sirenen ausschalten. Hat die Brandsperre das verhindert, wird es jede Minute erneut versucht, bis der Guard es erlaubt | Sirenen ohne eigene Laufzeit verstummen sonst nie |
| S14 | Sirenentest: gleicher Weg wie ein Alarm (S1–S12 gelten); zusätzlich nur unscharf, eine Sirene, höchstens 10 s, nur Administratoren; Scharfschalten währenddessen gesperrt | Prüfen ohne Sonderweg, an dem die Regeln nicht gelten |

### Umsetzung (ab 0.5.0)

- `siren_executor.py` ist die einzige Datei, die Sirenen-Dienste aufruft; ein statischer Test
  prüft das per Syntaxbaum.
- Ab 0.40 können Experten Schalter als Sirene eintragen. Auch `switch.turn_on`/`turn_off` ruft
  ausschließlich der Executor auf – nach demselben Guard (statischer Test). Ein Schalter gilt
  als Sirene ohne Ton, Lautstärke und Dauer.
- Der Assistent „Sirene aus Schalter erstellen“ legt nur einen Helfer `switch_as_x` an und
  schaltet nichts; der Helfer-Assistent für Melder legt nur `threshold`-Helfer an (statischer
  Test).
- Brand-Indikatoren einer registrierten Sirene werden über das Gerät erkannt: Binärsensoren mit
  Geräteklasse Rauch, Gas, CO oder Hitze sowie Testknopf-Sensoren (`…_test`). Deaktivierte
  Indikatoren zählen als „unklar“.
- Melder ohne registrierte Sirene zählen nur, wenn sie **aktiv** Brand melden; ein irgendwo
  ausgefallener Melder sperrt die Einbruchsirenen nicht dauerhaft.

### Was heißt „unklar“?

Der Brand-Indikator eines Geräts (z. B. sein Rauch-Binärsensor oder Testknopf-Sensor) ist
`unavailable` oder `unknown`. Hauswacht kann dann nicht beweisen, dass es nicht brennt, und
verhält sich wie bei einem aktiven Brand.

### Bekannte Grenzen

- Viele Zigbee-Sirenen melden `assumed_state`. Home Assistant kann dann **nicht bestätigen**,
  dass eine Sirene tatsächlich hörbar ist. Die Oberfläche zeigt deshalb nur „Befehl gesendet“.
- Batteriebetriebene Geräte können Befehle verzögert empfangen. Das wird beim ersten
  freigegebenen Praxistest gemessen und dokumentiert.
- Ob ein Stoppbefehl einen autonom ausgelösten Brandalarm beeinflusst, ist geräteabhängig und
  nicht dokumentiert. Hauswacht geht immer vom ungünstigsten Fall aus (Regel S4).

## Zustandsmaschine

| Nr. | Regel |
|---|---|
| Z1 | Nach jedem Start ist die Anlage unscharf. Ein früherer Alarm wird nie wieder aufgenommen. |
| Z2 | War die Anlage vor dem Neustart scharf, wird das gemeldet. |
| Z3 | Der Testmodus lässt sich nur im unscharfen Zustand umschalten. |
| Z4 | Abgelaufene Timer aus einem früheren Zustand oder vor einem Neustart bewirken nichts. |
| Z5 | Der Anlagenzustand ändert sich nur über Ereignisse der Zustandsmaschine. |

## Entwicklung

- Während der Entwicklung werden keine Sirenen ausgelöst und keine Geräte geschaltet.
- Zugriffe auf eine produktive Home-Assistant-Instanz sind nur lesend und nur nach Freigabe
  erlaubt.
- Echte Sirenentests erfolgen erst nach ausdrücklicher Freigabe, mit Ankündigung und bei
  Anwesenheit der Bewohner.

## Heimkehr und Push-Knopf

| Nr. | Regel | Grund |
|---|---|---|
| H1 | Die Heimkehr-Beobachtung schaltet nichts: keine Dienste, kein Scharf/Unscharf, kein Alarm (statischer Test) | Erst messen, dann entscheiden |
| H2 | Ein Push-Knopf gilt nur für die Scharfschaltung, in der er verschickt wurde | Alte Benachrichtigungen dürfen eine spätere Scharfschaltung nicht aufheben |
| H3 | Der Push-Knopf wirkt nur mit einem aktiven, nicht systemeigenen Home-Assistant-Benutzer | Nur angemeldete Handys |
| H6 | Profil-Einstellungen über Entitäten nur im unscharfen Zustand | Im scharfen Zustand darf niemand die Anlage schwächen |
| H7 | Bedrohungs-PIN: Aktion läuft normal, Notruf nur per Push an eigene Empfänger, nichts Sichtbares in Home Assistant | Der Täter könnte danebenstehen |
| H8 | PIN-Prüfung im Hintergrund, PINs nie im Klartext; gesperrte/abgelaufene PINs werden wie falsche behandelt | Kein Hängen, nichts verraten |
| H5 | Knopf „Unscharf schalten“ bei eingestelltem PIN nie verfügbar; „Alarm beenden“ ohne PIN nur mit ausdrücklicher Option | Unscharfschalten bleibt immer durch den PIN geschützt |
| H4 | Push-Knopf standardmäßig aus | Bewusste Entscheidung, auch wegen Android (keine Gerätesperre für Knöpfe) |
