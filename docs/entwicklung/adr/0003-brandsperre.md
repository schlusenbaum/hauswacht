# ADR 0003: Globale Brandsperre, auch bei unklarem Zustand

- Status: angenommen
- Datum: 2026-11-06

## Kontext

Die Sirenen sind zugleich Rauchmelder. Es ist nicht dokumentiert, ob ein Stoppbefehl über
Zigbee einen autonom ausgelösten Brandalarm stumm schaltet. Die Geräte melden ihren
Sirenenzustand nur angenommen (`assumed_state`).

## Entscheidung

Sobald **irgendein** Gerät Brand meldet (Rauch oder Testknopf) oder sein Brand-Indikator
nicht verfügbar ist, gilt eine globale Brandsperre:

- keine Einbruch-Aktivierung an irgendeinem Gerät,
- kein einziger Ausschaltbefehl an irgendein Gerät.

Einbruchsirenen laufen bevorzugt über die mitgegebene Dauer aus, sodass ein Stoppbefehl im
Normalfall nicht nötig ist. Die gerätseitige Höchstdauer wird nie verändert.

## Begründung

Ein fälschlich nicht gestoppter Einbruchton ist ärgerlich; ein fälschlich gestoppter
Brandalarm ist lebensgefährlich. Bei Unklarheit gilt deshalb die strengste Annahme.

## Folgen

- Bei ausgefallenem Brand-Indikator kann ein laufender Einbruchton nicht per Unscharfschaltung
  beendet werden; er endet spätestens nach der gerätseitigen Höchstdauer.
- Die Oberfläche muss den Grund („Brandsperre aktiv“) klar anzeigen.
