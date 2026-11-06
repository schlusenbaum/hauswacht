# Tests

Alle Tests laufen **ohne Home Assistant, ohne Geräte und ohne Sirenen**.

```bash
pytest          # Tests
mypy            # Typprüfung (strict)
ruff check .    # Lint
```

## Vorhanden (0.1.0)

| Datei | Inhalt |
|---|---|
| `tests/test_state_machine.py` | Alle Zustandsübergänge, Verzögerungen, Policies, Re-Trigger, Tamper, Neustart, Testmodus, veraltete Timer |
| `tests/test_siren_guard.py` | Alle Sperren einzeln und als vollständige Kombinationsmatrix (Hardware × Testmodus × Brandzustand) |
| `tests/test_static_safety.py` | Keine verbotenen Aufrufe im Code, keine HA-Importe im Kern, Sirenen-Services nur im Executor |

## Geplant

| Version | Tests |
|---|---|
| 0.2.0 | Integrationstests mit `pytest-homeassistant-custom-component`: Einrichtung, Entität, Neustart aus jedem Zustand, Store-Migration |
| 0.3.0 | Profile und Zonen, offene/nicht verfügbare Sensoren, veraltete Werte (`last_seen`), Profilwechsel |
| 0.4.0 | Ausfall und Wiederkehr von MQTT, Zigbee2MQTT und Bluetooth ohne Fehlalarm; Simulation kompletter Abläufe im Testmodus |
| 0.5.0 | Executor mit gemockten Services: im Testmodus und ohne Hardware-Freigabe **kein** Aufruf; Brand während Einbruchalarm; gleichzeitige Alarme; Benachrichtigungen |
