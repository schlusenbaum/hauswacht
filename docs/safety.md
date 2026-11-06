# Sicherheitsregeln

Diese Regeln sind verbindlich. Sie dürfen nicht vereinfacht werden, um die Implementierung zu
erleichtern. Jede Regel ist durch Tests abgesichert.

## Sirenen

Implementierung: `custom_components/hauswacht/core/siren_guard.py`
Tests: `tests/test_siren_guard.py`, `tests/test_static_safety.py`

| Nr. | Regel | Grund |
|---|---|---|
| S1 | Testmodus aktiv → keinerlei Sirenenbefehle | Fehlbedienung im Test darf keinen echten Alarm auslösen |
| S2 | Hardware-Freigabe aus → keinerlei Sirenenbefehle. Standard nach Installation: **aus** | Sirenen erst nach bewusster Freigabe |
| S3 | Brand an irgendeinem Gerät **aktiv oder unklar** → keine Einbruch-Aktivierung | Brandalarm hat Vorrang, kein verwirrender Einbruchton während einer Evakuierung |
| S4 | Brand an irgendeinem Gerät **aktiv oder unklar** → kein einziger Ausschaltbefehl | Ein Stoppbefehl könnte einen lokalen Brandalarm stumm schalten (nicht ausgeschlossen) |
| S5 | Ausschalten nur für Geräte, die Hauswacht selbst aktiviert hat | Fremde Alarme werden nie beeinflusst |
| S6 | Brandtöne (`fire`, `fire_panic`) sind für Einbruchalarme verboten | Eindeutige Unterscheidung der Alarmarten |
| S7 | Laufzeit wird auf die gerätseitige Höchstdauer begrenzt; diese wird **nie verändert** | Gerätewert kann das Brandverhalten beeinflussen |
| S8 | Sirenen-Services werden nur im Siren Executor aufgerufen | Ein einziger, prüfbarer Pfad |
| S9 | Fremde Abschalt-Scripts (z. B. ein Script, das alle Rauchmelder abschaltet) werden nie verwendet | Würde einen Brandalarm beenden |

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
