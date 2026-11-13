<img src="docs/images/hauswacht-icon.svg" alt="Hauswacht" width="96" align="right">

# Hauswacht

[![Release](https://img.shields.io/github/v/release/schlusenbaum/hauswacht?include_prereleases&sort=semver)](https://github.com/schlusenbaum/hauswacht/releases)
[![Downloads](https://img.shields.io/github/downloads/schlusenbaum/hauswacht/total?label=Downloads)](https://github.com/schlusenbaum/hauswacht/releases)
[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/docs/faq/custom_repositories/)
[![CI](https://github.com/schlusenbaum/hauswacht/actions/workflows/ci.yml/badge.svg)](https://github.com/schlusenbaum/hauswacht/actions/workflows/ci.yml)

**Einbruchmeldeanlage für Home Assistant** – frei definierbare Alarmprofile, Auslöseregeln wie
„Tür, dann Keller“, Benutzer mit PIN und RFID-Karte, Zigbee-Keypads, Sirenen mit Brandsperre
und ein Testmodus, in dem garantiert keine Sirene losgeht.

> **Status: 0.35.1 – Entwicklungsversion**, im eigenen Haus im Einsatz. Die echte
> Sirenenansteuerung ist nach der Installation **gesperrt** und muss bewusst freigegeben werden.

<p align="center">
  <img src="https://raw.githubusercontent.com/schlusenbaum/hauswacht/main/docs/images/alarm-karte.png" alt="Karte Hauswacht Alarm: unscharf, wird scharf, PIN-Eingabe, Alarm" width="800">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/schlusenbaum/hauswacht/main/docs/images/test-karte.png" alt="Karte Hauswacht Test" width="420">
  <img src="https://raw.githubusercontent.com/schlusenbaum/hauswacht/main/docs/images/einstellungen-karte.png" alt="Karte Hauswacht Einstellungen" width="380">
</p>

## Was Hauswacht kann

- **Alarmprofile statt fester Modi** – „Zuhause“, „Nacht“, „Urlaub“ … beliebig viele, jedes mit
  eigenen Meldergruppen, Verzögerungen, Sirenen und Empfängern. Automatisch scharf nach Uhrzeit
  oder wenn alle weg sind.
- **Auslöseregeln** – Alarm erst bei einer Abfolge („Tür, dann Keller innerhalb von 2 Minuten“),
  mit Ausnahmen und Bedingungen; im Assistenten oder als YAML.
- **Alarmkarte ohne PIN-Zwang** – große Karte fürs Tablet: Zustand mit Countdown, ein Knopf je
  Profil, offene Melder mit „Trotzdem scharf“. Wer angemeldet ist, schaltet mit seinen Rechten;
  einen PIN verlangt sie nur, wo es eingestellt ist – z. B. am Wandtablet im Flur.
- **Bereiche** – Haus und Garage unabhängig scharf, mit eigenem Bedienfeld und „Alle Bereiche“.
- **Benutzer und Ausweise** – PIN und beliebig viele RFID-Karten je Person, Rechte je Bereich,
  Gäste mit Gültigkeit, Bedrohungs-PIN mit stillem Notruf, Sperre gegen Durchprobieren.
- **Bedienteile** – Zigbee-Keypads über Zigbee2MQTT mit Rückmeldung am Gerät, Karten direkt am
  Keypad anlernen, NFC-Aufkleber mit der Home-Assistant-App, RFID-Leser.
- **Benachrichtigungen** – pro Ereignis mit eigenen Empfängern und Texten, wichtige Hinweise
  durchbrechen „Nicht stören“, Knöpfe „Unscharf schalten“ und „Trotzdem scharf“ in der
  Push-Nachricht, Ansagen über Lautsprecher (z. B. Echo).
- **Sirenen mit Verstand** – angesteuert nur nach ihren Fähigkeiten, nie mit Brandton, nie
  während eines Brandes; Sirenentest einzeln, kurz und leise.
- **Ehrlich bei Störungen** – ausgefallene Melder, Funkstille und Ausfälle von Zigbee2MQTT oder
  MQTT werden sichtbar statt verschwiegen.
- **Testmodus und Testkarte** – alles gefahrlos durchspielen, ohne Sirene, ohne dass andere
  Automationen etwas merken.
- **Anlagenübersicht** – die ganze Konfiguration auf einen Blick, zum Drucken, mit Notfallblatt
  für die Familie und Prüfhinweisen, die Lücken und Vergessenes finden.
- **Beobachten statt raten** – Heimkehr- und Funkstille-Beobachtung liefern Zahlen, bevor man
  etwas automatisiert.

## Schnellstart

1. **HACS** → ⋮ → Benutzerdefinierte Repositories → `https://github.com/schlusenbaum/hauswacht`
   (Typ Integration) → Hauswacht herunterladen → Home Assistant neu starten.
2. Einstellungen → Geräte & Dienste → **Integration hinzufügen → Hauswacht**.
3. **Konfigurieren:** eine Meldergruppe mit den Tür- und Fensterkontakten anlegen, ein
   Alarmprofil (z. B. „Nacht“) anlegen, das Handy als Empfänger eintragen.
4. Karte **„Hauswacht Test“** aufs Dashboard, Testmodus an, durchspielen.
5. Testmodus aus – fertig. Sirenen erst freigeben, wenn alles passt.

Ausführlich: [Installation und erste Schritte](docs/installation.md).

## Dokumentation

| | |
|---|---|
| [Installation und erste Schritte](docs/installation.md) | Installation, Menü, die ersten fünf Schritte |
| [Melder und Meldergruppen](docs/melder.md) | Welche Sensoren, Typen, immer aktiv, Funkstille |
| [Alarmprofile und Bereiche](docs/profile.md) | Profile, Automatik, Scharf durch Türschließen, Bereiche |
| [Auslöseregeln](docs/ausloeseregeln.md) | Abfolgen, Ausnahmen, Bedingungen, YAML |
| [Bedienung und Dashboard](docs/dashboard.md) | Scharf/unscharf, Alarmkarte, Alarm beenden, Karten |
| [Benutzer, PINs und Sperre](docs/benutzer.md) | Benutzer, Rechte, PIN-Regeln, Bedrohungs-PIN |
| [Bedienteile](docs/bedienteile.md) | Keypads, Karten anlernen, NFC, RFID-Leser |
| [Sirenen](docs/sirenen.md) | Kompatibilität, Freigabe, Sirenentest, Brandschutz |
| [Benachrichtigungen](docs/benachrichtigungen.md) | Ereignisse, eigene Texte, Sprachausgabe |
| [Anlagenübersicht](docs/uebersicht.md) | Übersicht, Drucken, Notfallblatt, Prüfhinweise |
| [Testmodus](docs/testmodus.md) · [Beobachtungen](docs/beobachtung.md) · [Referenz](docs/referenz.md) · [Fehlersuche](docs/fehlersuche.md) | |

Alles auf einen Blick: [docs/](docs/README.md).

## Voraussetzungen

- Home Assistant **2026.10** oder neuer
- Melder mit offen/zu (Tür-, Fenster-, Bewegungsmelder …) – herstellerunabhängig
- Optional: Sirenen (`siren`), Home-Assistant-App, Zigbee2MQTT für Keypads
- Keine Cloud, keine weiteren Integrationen nötig

## Sicherheit

- **Brandalarm hat immer Vorrang:** Solange ein Rauchmelder Brand meldet oder sein Zustand unklar
  ist, schaltet Hauswacht keine Sirene ein und keine aus.
- **Testmodus sperrt Sirenen technisch**, nicht nur in der Anzeige. Die Sirenenfreigabe ist nach
  der Installation aus.
- **Nach einem Neustart unscharf** – ein früherer Alarm wird nie unkontrolliert wieder
  aufgenommen.
- **Hauswacht schaltet keine Geräte** außer Sirenen und der Anzeige eingerichteter Keypads – ein
  Test stellt das sicher.

Die verbindlichen Regeln: [Sicherheitsregeln](docs/entwicklung/safety.md).

> **Hinweis:** Hauswacht ist ein Hobbyprojekt und **kein zertifiziertes Sicherheitssystem**
> (keine VdS- oder EN-50131-Zertifizierung). Es ersetzt weder eine professionelle
> Einbruchmeldeanlage noch geprüfte Rauchwarnmelder.

## Mitmachen

Fehler und Wünsche gern als [Issue](https://github.com/schlusenbaum/hauswacht/issues) –
Rückmeldungen zu weiteren Sirenen- und Keypad-Modellen sind besonders willkommen.

```bash
pip install ruff mypy pytest
ruff check . && ruff format --check . && mypy && pytest tests/core

# Integrationstests (installiert Home Assistant als Testumgebung)
pip install pytest-homeassistant-custom-component
pytest tests/integration -o asyncio_mode=auto
```

Kein Test braucht echte Geräte. Mehr unter [Entwicklung](docs/README.md#für-entwickler).

## Unterstützen

Wenn dir Hauswacht gefällt, freue ich mich über einen Kaffee:

[![Buy me a coffee](https://img.buymeacoffee.com/button-api/?text=Buy%20me%20a%20coffee&emoji=&slug=schlusenbaum&button_colour=FFDD00&font_colour=000000&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff)](https://www.buymeacoffee.com/schlusenbaum)

## Lizenz

[MIT](LICENSE)
