# Tests

Kein Test braucht echte Geräte oder Sirenen. Die Kernlogik wird ohne Home Assistant getestet,
die Integrationstests mit einer Home-Assistant-Testumgebung.

```bash
pip install ruff mypy pytest
ruff check . && ruff format --check . && mypy && pytest tests/core

# Integrationstests (installiert Home Assistant als Testumgebung)
pip install pytest-homeassistant-custom-component
pytest tests/integration -o asyncio_mode=auto
```

Dieselben Prüfungen laufen bei jedem Pull Request in der CI, dazu Hassfest.

## Vorhanden

| Datei | Inhalt |
|---|---|
| `tests/core/test_state_machine.py` | Alle Zustandsübergänge, Verzögerungen, Policies, Re-Trigger, Tamper, Neustart, Testmodus, veraltete Timer |
| `tests/core/test_siren_guard.py` | Alle Sperren einzeln und als vollständige Kombinationsmatrix (Hardware × Testmodus × Brandzustand) |
| `tests/core/test_static_safety.py` | Keine verbotenen Aufrufe im Code, keine HA-Importe im Kern, Sirenen-Services nur im Executor |
| `tests/core/test_profiles_and_pin.py` | Profile aus Optionen (inkl. ungültiger Werte), PIN-Format, Hash und Prüfung |
| `tests/core/test_sensors.py` | Zonen, Labels, Rollen aus Geräteklasse, Bereitschaft (offen, ausgefallen, Funkstille), Auslöseerkennung, Profilverhalten |
| `tests/integration/test_sensors.py` | Mit Home Assistant: Auslösung je Rolle, Eingangsverzögerung, Profil-Zonen, Bereitschaft, Bestätigung, Labels (auch Label-Entfernung im scharfen Zustand), Melder-Typen, Zonen-Optionen |
| `tests/integration/test_sensor_types.py` | Mit Home Assistant: Schloss und Abdeckung, Typen (Technik immer aktiv, nie scharf), Ausnahmen im Profil, Typen-Formular, Helfer-Assistent, Migration auf Version 5 |
| `tests/core/test_infrastructure.py` | Indikatoren und Systemstatus |
| `tests/integration/test_system.py` | Mit Home Assistant: Systemstatus, Störung verweigert Scharfschalten, Ausfall und Wiederkehr von Zigbee2MQTT ohne Fehlalarm, Simulation nur im Testmodus |
| `tests/core/test_rules.py` | Regel-Kern: Abfolgen, ODER/UND/mindestens N, Verschachtelung, Ausnahme, Zeitfenster, Fortschritt, Prüfung, YAML-Umwandlung, alte Speicherform, Migration |
| `tests/core/test_conditions.py` | Bedingungen: Uhrzeit über Mitternacht, Wochentage, Person/Zone, Zustand, Zahlenwert, Logik, nicht auswertbar = erfüllt, Aufbauprüfung |
| `tests/integration/test_rules.py` | Mit Home Assistant: Tür allein / Keller allein kein Alarm, Tür → Keller Eingangsverzögerung, Fenster → Keller Alarm, Reihenfolge, Scharfschalten trotz offenem Regelmelder, Migration, Optionen |
| `tests/integration/test_always_active.py` | Mit Home Assistant: immer aktive Melder (unscharf nur Benachrichtigung, mit Sirene Alarm und zurück nach unscharf, scharf sofortiger Alarm), Scharf durch Schließen der Tür (Beruhigungszeit, offene Tür am Ende bricht ab) |
| `tests/integration/test_simulation.py` | Mit Home Assistant: Sensorzustände simulieren (nur Testmodus, Zustand in Home Assistant unverändert, echte Änderungen während der Simulation ignoriert, Zurücksetzen bewertet den echten Wert, Testmodus aus löscht alles, keine Sirene) |
| `tests/core/test_reactions.py` | Reaktion je Profil, Brand-Indikatoren, Höchstdauer, Texte |
| `tests/integration/test_reactions.py` | Mit Home Assistant und **Attrappen-Diensten**: Hardware-Sperre, Testmodus, Brand am eigenen/fremden Melder, Brand während Alarm, keine Schreibzugriffe, Push, Freigabe nur mit Bestätigung |
| `tests/integration/test_profiles.py` | Mit Home Assistant: keine Standardprofile, Migration der festen Profile, Profile ohne Knopf, nur zugeordnete Knöpfe, Auswahlliste und Knöpfe, Profilverwaltung in den Optionen |
| `tests/core/test_automation.py` | Uhrzeiten, Wochentage, „alle weg“ (unbekannt zählt nicht als weg) |
| `tests/integration/test_automation.py` | Mit Home Assistant: scharf/unscharf nach Uhrzeit und Wochentag, nie über ein anderes Profil, kein Abbruch laufender Alarme, Wartezeit bei Abwesenheit, Rückkehr, Optionen |
| `tests/core/test_homecoming.py` | Heimkehr-Auswertung: Anwesenheit, Verzögerung zur Tür, Fehlalarme je Eingangsverzögerung, Bericht |
| `tests/integration/test_homecoming.py` | Mit Home Assistant: Push-Knopf (gültig, veraltet, ohne Benutzer, standardmäßig aus), Beobachtung schaltet nichts, Bericht |
| `tests/integration/test_acknowledge.py` | Mit Home Assistant: Unscharf während des Alarms beendet nur den Alarm, Überbrückung bis zum Schließen, Push-Knopf „Alarm beenden“ |
| `tests/core/test_profile_settings.py` | Profil-Einstellungen lesen/schreiben, Grenzen, keine Brandtöne, keine Listen |
| `tests/integration/test_profile_settings.py` | Mit Home Assistant: Profil bearbeiten, Werte ändern, Sperre im scharfen Zustand |
| `tests/core/test_users.py` | Benutzer, gemeinsame PINs, Rechte, Gäste-Zeitraum, Bedrohungs-PIN, Konflikte |
| `tests/core/test_checks.py` | Prüfhinweise: Lücken, Vergessenes, Widersprüche; Bedrohungs-PIN ohne Namen |
| `tests/integration/test_alarm_card.py` | Alarmkarte: ohne PINs frei, zugeordnetes Konto ohne PIN mit Namen und Rechten, fremdes Konto bzw. Tablet mit PIN, falscher PIN, „Trotzdem scharf“, kein Zugriff für Nur-Lesen-Konten |
| `tests/integration/test_overview.py` | Übersicht per WebSocket (nur Admins, nichts Geheimes), Reparaturen kommen und gehen, Diagnose geschwärzt |
| `tests/core/test_docs.py` | Dokumentation: keine toten Links oder Anker, jede Seite im Inhaltsverzeichnis |
| `tests/core/test_versions.py` | Versionsangaben in README, Anleitung, pyproject und CHANGELOG passen zum Manifest |
| `tests/integration/test_users.py` | Mit Home Assistant: „geändert von“, gemeinsamer PIN, Rechte, gesperrt/abgelaufen, Bedrohungs-PIN unauffällig, Push mit Rechten, Benutzerverwaltung |
| `tests/integration/test_integration.py` | Mit Home Assistant: Einrichtung, Entladen, Scharf/Unscharf mit Verzögerung, PIN, Testmodus, Neustart und Neuladen im scharfen Zustand, Options Flow |

## Geplant

| Version | Tests |
|---|---|
| 0.2.x | Store-Migration, sobald sich das Speicherformat ändert |

## Release

Ein veröffentlichtes GitHub-Release startet `.github/workflows/release.yml`: Der Workflow prüft,
dass der Tag (`vX.Y.Z`) zur Version im Manifest passt, packt `custom_components/hauswacht` in
`hauswacht.zip` und hängt die Datei an das Release. HACS installiert aus dieser ZIP und zählt
die Downloads (Abzeichen im README).
