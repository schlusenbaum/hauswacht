# ADR 0001: Umsetzung als Custom Integration statt reiner Packages

- Status: angenommen
- Datum: 2026-11-06

## Kontext

Hauswacht soll dynamische Profile, eine einzige maßgebliche Zustandsinstanz, automatisierte
Tests, einen technisch gesperrten Testmodus und eine spätere Veröffentlichung ohne fest
codierte Entitäten bieten.

## Entscheidung

Umsetzung als Python-Custom-Integration (Installation über HACS). Packages werden nur für
optionale, hausindividuelle Ergänzungen verwendet. pyscript wird nicht eingesetzt.

## Begründung

- Beliebig viele Profile sind mit Helfern nur über eine Helfer-Explosion oder JSON in
  `input_text` (max. 255 Zeichen) abbildbar.
- Die Zustandsmaschine kann in einer Integration technisch als einzige Instanz erzwungen
  werden; Helfer könnte jede Automation ändern.
- Automatisierte Tests sind mit Python und `pytest-homeassistant-custom-component` möglich.
- Sensor- und Sirenenzuordnung erfolgt per Oberfläche statt per YAML.
- pyscript wäre eine zusätzliche Drittanbieter-Abhängigkeit mit schlechterer Testbarkeit.

## Folgen

- Höherer Einstiegs- und Wartungsaufwand (Python, Releases, Kompatibilität mit HA-Versionen).
- Die Kernlogik wird bewusst ohne HA-Abhängigkeit geschrieben, um den Testaufwand gering zu
  halten.
