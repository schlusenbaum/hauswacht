<img src="docs/images/hauswacht-icon.svg" alt="Hauswacht" width="96" align="right">

# Hauswacht

[![Release](https://img.shields.io/github/v/release/schlusenbaum/hauswacht?include_prereleases&sort=semver)](https://github.com/schlusenbaum/hauswacht/releases)
[![Downloads](https://img.shields.io/github/downloads/schlusenbaum/hauswacht/total?label=Downloads)](https://github.com/schlusenbaum/hauswacht/releases)
[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/docs/faq/custom_repositories/)
[![CI](https://github.com/schlusenbaum/hauswacht/actions/workflows/ci.yml/badge.svg)](https://github.com/schlusenbaum/hauswacht/actions/workflows/ci.yml)

**Profilbasierte Einbruchmeldeanlage für Home Assistant** – frei konfigurierbare Alarmprofile,
Sensor- und Sirenenauswahl pro Profil, strikte Trennung vom Brandalarm und ein technisch
gesperrter Testmodus.

> **Status: 0.32.0 – Entwicklungsversion.**
> Alle Grundfunktionen sind enthalten: Meldergruppen, Alarmprofile, Auslöseregeln („Tür, dann Keller“), Benutzer und PINs (auch Gäste und
> Bedrohungs-PIN), Bereiche (z. B. Haus und Garage getrennt scharf), Benachrichtigungen pro Ereignis mit Knöpfen und eigenen Texten, Sprachausgabe über Lautsprecher (z. B. Echo), Überwachung von Funknetz und
> Gateways, Testmodus mit Testkarte und Sirenen. Die **Sirenenansteuerung ist standardmäßig
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
> noch offen (geplant für 0.23.0); bis dahin ist nur die Logik mit nachgebildeten Geräten
> geprüft.

**Sensoren** (Tür-, Fenster-, Bewegungs- und Präsenzmelder, Sabotagekontakte) sind
herstellerunabhängig: Hauswacht nutzt jeden `binary_sensor` mit passender Geräteklasse.

**Sirenen** sind Home-Assistant-Entitäten der Domain `siren`, auch reine Innen- oder
Außensirenen ohne Rauchmelder. Hauswacht liest vor jedem Alarm, was eine Sirene kann
(`supported_features`, `available_tones`), und sendet nur das:

| Fähigkeit der Sirene | Verhalten |
|---|---|
| Tonauswahl mit Einbruchton | Gewählter Ton; fehlt er, ein anderer Einbruchton (`burglar`, `emergency`, `police_panic`, `emergency_panic`) – **nie ein Brandton** |
| Tonauswahl nur mit Brandtönen | Sirene wird für Einbruch **nicht** verwendet |
| Keine Tonauswahl | Einfache Sirene: ohne Tonangabe. **Rauchmelder** ohne Tonauswahl werden nicht verwendet, weil ihr Standardton meist der Brandton ist |
| Lautstärke, Dauer | Nur gesendet, wenn unterstützt |
| Nur Ein und Aus | Hauswacht schaltet sie nach der Reaktionszeit und beim Unscharfschalten selbst aus |
| Weder Dauer noch Ausschalten | Sirene wird nicht verwendet – Hauswacht könnte sie nicht beenden |
| Höchstdauer (`number.<sirene>_max_duration`, Zigbee2MQTT) | Dauer wird darauf begrenzt; fehlt sie, gelten 240 Sekunden |
| Brandsensor am selben Gerät | Gerätebezogene Brandsperre; ein aktiver Brand an einem beliebigen Melder sperrt immer |

Warum eine Sirene nicht angesteuert wurde, steht nach jedem Alarm im Attribut
`last_siren_decision` am Bedienfeld. Andere Modelle als das getestete vorher mit Testmodus und
Simulation prüfen und die Sirene dann bei Anwesenheit einmal bewusst auslösen. Rückmeldungen
zu weiteren Modellen sind willkommen.

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
