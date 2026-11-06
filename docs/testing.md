# Tests

Alle Tests laufen **ohne Home Assistant, ohne Geräte und ohne Sirenen**.

```bash
pytest          # Tests
mypy            # Typprüfung (strict)
ruff check .    # Lint
```

## Vorhanden

| Datei | Inhalt |
|---|---|
| `tests/core/test_state_machine.py` | Alle Zustandsübergänge, Verzögerungen, Policies, Re-Trigger, Tamper, Neustart, Testmodus, veraltete Timer |
| `tests/core/test_siren_guard.py` | Alle Sperren einzeln und als vollständige Kombinationsmatrix (Hardware × Testmodus × Brandzustand) |
| `tests/core/test_static_safety.py` | Keine verbotenen Aufrufe im Code, keine HA-Importe im Kern, Sirenen-Services nur im Executor |
| `tests/core/test_profiles_and_pin.py` | Profile aus Optionen (inkl. ungültiger Werte), PIN-Format, Hash und Prüfung |
| `tests/core/test_sensors.py` | Zonen, Labels, Rollen aus Geräteklasse, Bereitschaft (offen, ausgefallen, Funkstille), Auslöseerkennung, Profilverhalten |
| `tests/integration/test_sensors.py` | Mit Home Assistant: Auslösung je Rolle, Eingangsverzögerung, Profil-Zonen, Bereitschaft, Bestätigung, Labels (auch Label-Entfernung im scharfen Zustand), Rollen-Ausnahmen, Zonen-Optionen |
| `tests/core/test_infrastructure.py` | Indikatoren und Systemstatus |
| `tests/integration/test_system.py` | Mit Home Assistant: Systemstatus, Störung verweigert Scharfschalten, Ausfall und Wiederkehr von Zigbee2MQTT ohne Fehlalarm, Simulation nur im Testmodus |
| `tests/integration/test_integration.py` | Mit Home Assistant: Einrichtung, Entladen, Scharf/Unscharf mit Verzögerung, PIN, Testmodus, Neustart und Neuladen im scharfen Zustand, Options Flow |

## Geplant

| Version | Tests |
|---|---|
| 0.2.x | Store-Migration, sobald sich das Speicherformat ändert |
| 0.5.0 | Executor mit gemockten Services: im Testmodus und ohne Hardware-Freigabe **kein** Aufruf; Brand während Einbruchalarm; gleichzeitige Alarme; Benachrichtigungen |
