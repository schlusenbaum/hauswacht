# Architektur

## Überblick

Hauswacht ist eine Home-Assistant-Custom-Integration. Sie besteht aus einem **reinen Kern**
ohne Home-Assistant-Abhängigkeit und einer **Anbindungsschicht**, die den Kern mit Home
Assistant verbindet.

```text
                 Home Assistant
  ┌──────────────────────────────────────────────────────────┐
  │  Sensoren (binary_sensor)      Sirenen (siren)  notify   │
  └───────┬──────────────────────────────▲───────────▲──────┘
          │ Zustandsänderungen           │           │
  ┌───────▼──────────┐            ┌──────┴──────┐ ┌──┴───────┐
  │ Sensorbewertung  │            │   Siren     │ │ Notifier │
  │ (sensor_monitor) │            │  Executor   │ └──▲───────┘
  └───────┬──────────┘            └──────▲──────┘    │
          │ Ereignisse                   │ freigegebene Befehle
  ┌───────▼──────────────────────────────┴───────────┴──────┐
  │                  Kern (ohne Home Assistant)              │
  │  state_machine ──Effekte──► Reaktionsauflösung ──► siren_guard
  │  models (Profile, Reaktionen, Register)                  │
  └──────────────────────────────────────────────────────────┘
          ▲
  ┌───────┴──────────┐   ┌──────────────────────────────┐
  │ alarm_control_   │   │ store (Profile, Register,    │
  │ panel, sensoren  │   │ Schema-Version, Migrationen) │
  └──────────────────┘   └──────────────────────────────┘
```

## Module

| Modul | Version | Aufgabe |
|---|---|---|
| `core/state_machine.py` | 0.1.0 | Einzige maßgebliche Instanz für den Anlagenzustand |
| `core/siren_guard.py` | 0.1.0 | Entscheidet, welche Sirenenbefehle gesendet werden dürfen |
| `core/models.py` | 0.3.0 | Profile, Zonen, Sensor-, Sirenen-, Personen-Register, Reaktionen |
| `store.py` | 0.2.0 | Persistenz im HA-Store, Schema-Version, Migrationen |
| `config_flow.py` | 0.2.0 | Einrichtung und Optionen per Oberfläche |
| `alarm_control_panel.py` | 0.2.0 | Standard-Entität für Bedienung und Status |
| `sensor_monitor.py` | 0.3.0 | Sensorbewertung, Verfügbarkeit, veraltete Werte, Infrastruktur |
| `siren_executor.py` | 0.5.0 | **Einzige Stelle**, die Sirenen-Services aufruft |
| `notifier.py` | 0.5.0 | Benachrichtigungen pro Person |

## Grundprinzipien

1. **Ereignis rein, Effekte raus.** Der Kern führt nichts selbst aus. Er liefert Effekte
   (Timer starten, Reaktion auslösen …), die die Anbindungsschicht ausführt. Dadurch ist der
   Kern vollständig ohne Home Assistant testbar.
2. **Serielle Verarbeitung.** Ereignisse werden über eine Warteschlange nacheinander
   verarbeitet. Gleichzeitige Auslösungen erzeugen keine Wettlaufsituationen.
3. **Ein Pfad zu den Sirenen.** Nur der Siren Executor ruft Sirenen-Services auf, und nur mit
   Befehlen, die der Sirenen-Guard freigegeben hat. Ein statischer Test erzwingt das.
4. **Konfiguration ist Daten.** Profile, Zonen, Sensoren, Sirenen und Reaktionen liegen im
   HA-Store und werden per Oberfläche gepflegt. Im Repository stehen keine Entitäten einer
   einzelnen Installation.
5. **Sichere Seite bei Unklarheit.** Unbekannte Zustände führen zu Sperre oder Warnung, nie
   zu stillschweigendem Weiterlaufen.

## Abbildung auf Home Assistant

| Interner Zustand | `alarm_control_panel` |
|---|---|
| disarmed | `disarmed` |
| arming | `arming` |
| armed | `armed_home` / `armed_night` / `armed_away` / `armed_vacation` / `armed_custom_bypass` (je Profil) |
| pending | `pending` |
| triggered, alarm_hold | `triggered` (Attribut `phase`) |

Zusätzlich: `sensor.hauswacht_system_status` (ok / degraded / fault / starting),
`binary_sensor.hauswacht_test_mode`, Hardware-Freigabestatus.

## Datenmodell (Ausblick 0.3.0)

Profile verweisen auf **Zonen**, nicht auf einzelne Entitäten. Ausnahmen werden über
`include`/`exclude` gepflegt. Reaktionen sind eigene Datensätze, auf die Profile verweisen.
Details stehen im Architekturvorschlag und werden mit 0.3.0 in `docs/configuration.md`
dokumentiert.
