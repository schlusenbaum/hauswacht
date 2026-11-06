<img src="docs/images/hauswacht-icon.svg" alt="Hauswacht" width="96" align="right">

# Hauswacht

**Profilbasierte Einbruchmeldeanlage für Home Assistant** – frei konfigurierbare Profile,
Sensor- und Sirenenauswahl pro Profil, strikte Trennung vom Brandalarm und ein technisch
gesperrter Testmodus.

> **Status: 0.9.1 – Entwicklungsversion.**
> Alle Grundfunktionen sind enthalten: Profile, Zonen, Sensoren, Systemüberwachung,
> Simulation, Push-Benachrichtigungen und Sirenen. Die **Sirenenansteuerung ist standardmäßig
> gesperrt** und muss bewusst freigegeben werden. Siehe [Installation](docs/installation.md) und
> [Roadmap](docs/roadmap.md).

## Ziele

- **Profile statt fester Modi:** beliebig viele, frei benannte Profile mit eigenem Symbol.
  Jedes Profil legt Sensoren, Verzögerungen und Alarmreaktionen selbst fest und kann einem
  Knopf des Home-Assistant-Bedienfelds zugeordnet werden.
- **Datengetrieben:** Neue Profile, Sensoren und Reaktionen sind Konfiguration, kein Code.
- **Eine maßgebliche Zustandsmaschine:** Kein Geflecht aus Automationen, die sich gegenseitig
  beeinflussen.
- **Brandalarm hat immer Vorrang:** Hauswacht schaltet niemals eine Sirene ab, solange ein
  Rauchmelder Brand meldet oder sein Zustand unklar ist.
- **Sicherer Testmodus:** Im Testmodus können keine echten Sirenen ausgelöst werden – technisch
  erzwungen, nicht nur angezeigt.
- **Ehrlich bei Störungen:** Nicht verfügbare Sensoren und Infrastrukturausfälle (MQTT,
  Zigbee2MQTT, Bluetooth) werden sichtbar gemacht statt verschwiegen.
- **Nach Neustart unscharf:** Ein früherer Alarm wird nie unkontrolliert wieder aufgenommen.

## Wichtiger Hinweis

Hauswacht ist ein Hobbyprojekt und **kein zertifiziertes Sicherheitssystem** (keine VdS- oder
EN-50131-Zertifizierung). Es ersetzt weder eine professionelle Einbruchmeldeanlage noch
geprüfte Rauchwarnmelder. Die Rauchmelder behalten ihre eigenständige Brandmeldefunktion.

## Geräte und Kompatibilität

> **Getestet ist bisher nur ein Sirenenmodell:** Rauchwarnmelder **Develco SMSZB-120**
> („Smoke detector with siren“) über **Zigbee2MQTT**. Auch damit ist der echte Sirenentest
> noch offen (geplant für 0.10.0); bis dahin ist nur die Logik mit nachgebildeten Geräten
> geprüft.

**Sensoren** (Tür-, Fenster-, Bewegungs- und Präsenzmelder, Sabotagekontakte) sind
herstellerunabhängig: Hauswacht nutzt jeden `binary_sensor` mit passender Geräteklasse.

**Sirenen** sind Home-Assistant-Entitäten der Domain `siren`. Hauswacht ist auf Sirenen
ausgelegt, die gleichzeitig **Rauchwarnmelder** sind – daher die Brandsperre. Für andere
Sirenen gilt derzeit:

| Eigenschaft | Erwartet | Bei abweichenden Geräten |
|---|---|---|
| Ton | Die Sirene versteht einen der Töne `burglar`, `emergency`, `police_panic`, `emergency_panic` | Der Befehl kann von Home Assistant abgelehnt werden – die Sirene bleibt dann **stumm** |
| Lautstärke und Dauer | Die Sirene unterstützt `volume_level` und `duration` | wie oben |
| Höchstdauer | `number.<sirene>_max_duration` am selben Gerät (Zigbee2MQTT) | Hauswacht nimmt 240 Sekunden an |
| Brandanzeige | Rauch-, Gas-, CO- oder Hitze-Binärsensor am selben Gerät | Keine gerätebezogene Brandsperre; ein aktiver Brand an einem beliebigen Melder sperrt trotzdem |

Reine Innen- oder Außensirenen ohne Rauchmelder können also funktionieren, sind aber **nicht
getestet**. Wer andere Geräte einsetzt: vorher mit Testmodus und Simulation prüfen, dann die
Sirene bei Anwesenheit einmal bewusst auslösen und `last_siren_decision` am Bedienfeld
ansehen. Rückmeldungen zu weiteren Modellen sind willkommen.

## Dokumentation

| Dokument | Inhalt |
|---|---|
| [docs/installation.md](docs/installation.md) | Installation, Einstellungen, Bedienung |
| [docs/dashboard.md](docs/dashboard.md) | Beispielkarte und nützliche Entitäten |
| [docs/architecture.md](docs/architecture.md) | Gesamtarchitektur und Module |
| [docs/state-model.md](docs/state-model.md) | Zustände, Ereignisse, Übergänge |
| [docs/safety.md](docs/safety.md) | Sicherheitsregeln für Sirenen und Brandalarm |
| [docs/testing.md](docs/testing.md) | Teststrategie und Testliste |
| [docs/roadmap.md](docs/roadmap.md) | Meilensteine und Versionsplanung |
| [docs/adr/](docs/adr/) | Architekturentscheidungen mit Begründung |

## Voraussetzungen

- Home Assistant 2026.10 oder neuer
- Installation über HACS (benutzerdefiniertes Repository)
- Keine weiteren Abhängigkeiten von Drittanbieter-Integrationen

## Entwicklung

```bash
pip install ruff mypy pytest
ruff check . && ruff format --check .
mypy
pytest tests/core

# Integrationstests (installiert Home Assistant als Testumgebung)
pip install pytest-homeassistant-custom-component
pytest tests/integration -o asyncio_mode=auto
```

Kein Test braucht echte Geräte. Die Kerntests laufen sogar ohne Home Assistant.

## Unterstützen

Wenn dir Hauswacht gefällt, freue ich mich über einen Kaffee:

[![Buy me a coffee](https://img.buymeacoffee.com/button-api/?text=Buy%20me%20a%20coffee&emoji=&slug=schlusenbaum&button_colour=FFDD00&font_colour=000000&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff)](https://www.buymeacoffee.com/schlusenbaum)

## Lizenz

[MIT](LICENSE)
