# Changelog

Alle relevanten Änderungen an diesem Projekt werden hier dokumentiert.
Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
Versionierung nach [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

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
