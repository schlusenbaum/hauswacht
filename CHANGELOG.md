# Changelog

Alle relevanten Änderungen an diesem Projekt werden hier dokumentiert.
Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
Versionierung nach [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

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
