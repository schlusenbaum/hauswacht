# Hauswacht

**Profilbasierte Einbruchmeldeanlage für Home Assistant** – frei konfigurierbare Profile,
Sensor- und Sirenenauswahl pro Profil, strikte Trennung vom Brandalarm und ein technisch
gesperrter Testmodus. Ohne Alarmo.

> **Status: 0.1.0 – Entwicklungsstand, nicht installierbar.**
> Diese Version enthält nur die Kernlogik (Zustandsmaschine und Sirenen-Sicherheitslogik)
> mit Tests. Die Home-Assistant-Anbindung folgt mit 0.2.0. Siehe [Roadmap](docs/roadmap.md).

## Ziele

- **Profile statt fester Modi:** Zuhause, Nacht, Abwesend, Urlaub und beliebig viele eigene
  Profile. Jedes Profil legt Sensoren, Verzögerungen und Alarmreaktionen selbst fest.
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

## Dokumentation

| Dokument | Inhalt |
|---|---|
| [docs/architecture.md](docs/architecture.md) | Gesamtarchitektur und Module |
| [docs/state-model.md](docs/state-model.md) | Zustände, Ereignisse, Übergänge |
| [docs/safety.md](docs/safety.md) | Sicherheitsregeln für Sirenen und Brandalarm |
| [docs/testing.md](docs/testing.md) | Teststrategie und Testliste |
| [docs/roadmap.md](docs/roadmap.md) | Meilensteine und Versionsplanung |
| [docs/adr/](docs/adr/) | Architekturentscheidungen mit Begründung |

## Voraussetzungen (geplant)

- Home Assistant 2026.11 oder neuer
- Installation über HACS (benutzerdefiniertes Repository)
- Keine weiteren Abhängigkeiten von Drittanbieter-Integrationen

## Entwicklung

```bash
pip install ruff mypy pytest
ruff check . && ruff format --check .
mypy
pytest
```

Alle Tests laufen ohne Home Assistant und ohne echte Geräte.

## Lizenz

[MIT](LICENSE)
