# Roadmap

| Version | Inhalt | Echte Geräte |
|---|---|---|
| 0.1.0 ✅ | Repo, CI, Zustandsmaschine und Sirenen-Guard als reine Logik mit Tests | nein |
| 0.2.0 ✅ | Integrationsgerüst (manifest, Config Flow), `alarm_control_panel`, Scharf/Unscharf, Store, Neustartverhalten | nein |
| 0.3.0 ✅ | Datenmodell: Sensor-Register, Zonen, Profile; Bereitschaftsprüfung; Verfügbarkeit und veraltete Werte | nur lesen |
| 0.4.0 ✅ | Testmodus komplett, Simulation, Infrastruktur-Überwachung (MQTT, Z2M, BLE) | nur lesen |
| 0.5.0 ✅ | Reaktionen, Benachrichtigungen, Siren Executor (Hardware-Freigabe aus) | Push ja, Sirenen nein |
| 0.6.0 ✅ | Beispiel-Dashboard (Standardkarten, Smartphone) | – |
| 0.7.0 ✅ | Profil „Individuell“, Schutz gegen PIN-Raten | nein |
| 0.8.0 ✅ | Frei definierbare Profile (Name, Symbol, Bedienfeld-Knopf), Auswahlliste und Knöpfe | nein |
| 0.9.0 ✅ | Automatik pro Profil (Uhrzeit, Anwesenheit), Integrationssymbol | nein |
| 0.9.1–0.9.3 ✅ | Raumnamen, Sirenen nach Fähigkeiten, Sirenen-Ende nach Reaktionszeit | nein |
| 0.10.0 ✅ | Heimkehr-Beobachtung (schaltet nichts), Push-Knopf „Unscharf schalten“ | Push ja |
| 0.11.0 ✅ | Alarm beenden, Profil bleibt scharf | nein |
| 0.12.0 ✅ | Knöpfe „Unscharf schalten“ und „Alarm beenden“ | nein |
| 0.13.0 ✅ | Option „Alarm ohne PIN beenden“ | nein |
| 0.14.0 ✅ | Profil-Einstellungen als Entitäten (Dashboard) | nein |
| **0.15.0** ✅ | Karte „Hauswacht Einstellungen“ | nein |
| **0.16.0** ✅ | Benutzer und Codes: mehrere Personen mit eigenem PIN, einzeln sperrbar, „geändert von“ | nein |
| **0.17.0** ✅ | Benachrichtigungen pro Ereignis, wichtige Hinweise, Knöpfe „Trotzdem scharf“ / „Erneut versuchen“, Erinnerung „Alle weg“ | Push ja |
| 0.17.1–0.17.6 ✅ | Testkarte (Sensoren simulieren), Zonen verständlicher und ohne Mehrfachzuordnung, Optionen neu gegliedert mit Zurück, klarere Entitäten | nein |
| **0.18.0** ✅ | Bestätigung durch einen zweiten Melder (Zonen-Option), Meldung unbestätigter und häufiger Einzelauslösungen | nein |
| **0.19.0** ✅ | Regeln: Abfolgen von Meldern (einer/alle/mindestens N, Zeit bis zum nächsten Schritt), Regelsammlung, pro Profil wählbar, Prüfung beim Speichern, Fortschritt in der Testkarte | nein |
| **0.20.0** ✅ | Expertenmodus für Auslöseregeln: YAML-Editor mit Prüfung, Verschachtelung, Ausnahme „nicht, wenn vorher …“ (auch im Assistenten), Bedingungen (Uhrzeit, Person/Zone, Zustand, Zahlenwert, und/oder/nicht), Ergebnis „nur Benachrichtigung“ | nein |
| **0.21.0** ✅ | Immer aktive Melder (unscharf: Benachrichtigung, optional Sirene), Scharf durch Schließen der Tür (optional, Beruhigungszeit) | nein |
| 0.22.0 | Bereiche: mehrere unabhängig scharf schaltbare Bereiche plus „Alle“ | nein |
| 0.23.0 | Kontrollierter Sirenentest, Funkstille-Wert aus echten Daten; Entscheidung über eine Heimkehr-Automatik anhand der Beobachtung | nach Freigabe, bei Anwesenheit |
| 1.0.0 | Stabil, Doku vollständig, HACS-tauglich, Veröffentlichung | – |
| 1.x | Weitere Ausweise am Benutzer: RFID/NFC und Fingerabdruck (siehe ADR 0005), Zigbee-Tastenfelder, weitere Automatik-Bedingungen, wiederkehrende Gäste-Zeiten, eigene Benachrichtigungstexte | – |

## Entscheidungen

- **Namen (2026-11-11):** „Zonen“ heißen „Meldergruppen“, „Regeln“ heißen „Auslöseregeln“;
  beide im Menüpunkt „Alarmauslösung“. Interne Schlüssel (`zones`, `rules`) bleiben.

- **Regeln (2026-11-11):** Statt Zonen-Bestätigung eine Regelsammlung mit Abfolgen von
  Meldern; Profile wählen Regeln aus. Einfacher Modus (Formular) in 0.19, Expertenmodus (YAML)
  in 0.20 – beide auf demselben Regel-Kern. Regeln sind ODER-verknüpft und können sich nicht
  gegenseitig aushebeln. Siehe [ADR 0006](adr/0006-regeln.md).
- **Sensorgruppen (2026-11-11, ersetzt durch Regeln):** als Option der Zone („Alarm erst, wenn ein zweiter Melder
  dieser Zone bestätigt“) statt eigener Gruppen quer zu den Zonen. Nur verschiedene Melder
  zählen; ohne verfügbaren zweiten Melder sofortiger Alarm. Eigene Gruppen lassen sich später
  ergänzen.

- **Ausbau (2026-11-10):** Benutzer und Codes, Benachrichtigungen, Sensorgruppen,
  „immer aktiv“, Scharf durch Türschließen und Bereiche kommen nach und nach – je mit Konzept
  vorab. Benutzer werden so angelegt, dass sie später auf Bereiche beschränkt
  werden können. Geräte schalten bewusst nicht: Hauswacht
  schaltet keine Geräte.

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
