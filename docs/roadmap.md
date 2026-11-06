# Roadmap

| Version | Inhalt | Echte Geräte |
|---|---|---|
| 0.1.0 ✅ | Repo, CI, Zustandsmaschine und Sirenen-Guard als reine Logik mit Tests | nein |
| 0.2.0 ✅ | Integrationsgerüst (manifest, Config Flow), `alarm_control_panel`, Scharf/Unscharf, Store, Neustartverhalten | nein |
| 0.3.0 ✅ | Datenmodell: Sensor-Register, Zonen, Profile; Bereitschaftsprüfung; Verfügbarkeit und veraltete Werte | nur lesen |
| 0.4.0 ✅ | Testmodus komplett, Simulation, Infrastruktur-Überwachung (MQTT, Z2M, BLE) | nur lesen |
| **0.5.0** ✅ | Reaktionen, Benachrichtigungen, Siren Executor (Hardware-Freigabe aus) | Push ja, Sirenen nein |
| 0.6.0 | Beispiel-Dashboard (Standardkarten, Smartphone) | – |
| 0.7.0 | Installation in einer echten Instanz, Betrieb im Testmodus | nach Freigabe |
| 0.8.0 | Kontrollierter Sirenentest | nach Freigabe, bei Anwesenheit |
| 1.0.0 | Stabil, Doku vollständig, HACS-tauglich, Veröffentlichung | – |
| 1.x | Automatische Scharfschaltung, Anwesenheit, Keypad, RFID/NFC | – |

## Entscheidungen

- **PIN:** optional und einstellbar (2026-11-06).
- **Sprachassistenten:** standardmäßig nicht freigegeben. Eine spätere Freigabe (z. B. Alexa
  über Home Assistant Cloud) muss ohne Codeänderung möglich sein: Sie erfolgt über die normale
  Entitätsfreigabe von Home Assistant. Unscharfschalten per Sprache nur mit PIN.

## Versionierung und Releases

- Semantic Versioning. 0.x: Schnittstellen dürfen sich ändern. Ab 1.0.0 Breaking Changes nur
  in Major-Versionen, immer mit Store-Migration.
- Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).
- `main` ist immer grün. Größere Änderungen über Feature-Branches und Pull Requests.
- Releases als Git-Tag + GitHub-Release; HACS liest die Releases.
