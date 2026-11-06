# Installation und Bedienung

> **Stand 0.2.0:** Hauswacht kann installiert und scharf/unscharf geschaltet werden.
> Es sind aber noch **keine Sensoren** angebunden und **keine Sirenen oder Push-Nachrichten**
> aktiv. Die Version dient zum Kennenlernen der Bedienung und zum Testen.

## Voraussetzungen

- Home Assistant 2026.10 oder neuer (getestet mit 2026.10.4)
- HACS

## Installation über HACS

1. HACS öffnen → Menü (⋮) → **Benutzerdefinierte Repositories**.
2. Repository `https://github.com/schlusenbaum/hauswacht` mit Typ **Integration** hinzufügen.
   Solange das Repository privat ist, muss HACS Zugriff darauf haben.
3. **Hauswacht** suchen und herunterladen.
4. Home Assistant neu starten.
5. **Einstellungen → Geräte & Dienste → Integration hinzufügen → Hauswacht**.

Hauswacht kann nur einmal eingerichtet werden.

## Was danach vorhanden ist

| Entität | Zweck |
|---|---|
| `alarm_control_panel.hauswacht` | Bedienfeld: Zuhause, Nacht, Abwesend, Urlaub, Unscharf |
| `switch.hauswacht_testmodus` | Testmodus (Name je nach Sprache der Instanz) |

Das Bedienfeld funktioniert mit der normalen Alarm-Karte von Home Assistant.

### Attribute des Bedienfelds

| Attribut | Bedeutung |
|---|---|
| `profile` | Aktives Profil |
| `phase` | Interner Zustand (`arming`, `pending`, `alarm_hold` …) |
| `test_mode` | Testmodus aktiv |
| `timer`, `timer_ends_at` | Laufende Verzögerung und ihr Ende |
| `trigger_sensor`, `alarm_cycles` | Auslösender Sensor, Anzahl Alarmzyklen |
| `bypassed_sensors` | Überbrückte Sensoren |

## Einstellungen

**Einstellungen → Geräte & Dienste → Hauswacht → Konfigurieren.**
Die Einstellungen lassen sich nur im **unscharfen** Zustand ändern.

### PIN

- 4 bis 8 Ziffern, wird nur als Hash gespeichert.
- Mit PIN ist er zum Unscharfschalten immer nötig; optional auch zum Scharfschalten.
- Ohne PIN darf die Anlage nicht für Sprachassistenten (z. B. Alexa) freigegeben werden.

### Profilzeiten

| Profil | Ausgangsverzögerung | Eingangsverzögerung | Alarmreaktion |
|---|---|---|---|
| Zuhause | 0 s | 30 s | 180 s |
| Nacht | 0 s | 30 s | 180 s |
| Abwesend | 60 s | 30 s | 180 s |
| Urlaub | 60 s | 30 s | 180 s |

Alle Werte sind pro Profil änderbar (Verzögerungen 0–600 s, Alarmreaktion 1–900 s).

## Verhalten nach einem Neustart

Hauswacht startet **immer unscharf**. War die Anlage vorher scharf, erscheint ein Hinweis
„Hauswacht: nach Neustart unscharf“. Der Testmodus bleibt erhalten.

## Ereignisse für eigene Automationen

Jede Aktion der Zustandsmaschine wird als Ereignis `hauswacht_event` gemeldet. Das Feld
`type` nennt die Art, z. B. `StateChanged`, `ActivateReaction`, `RestartedDisarmed`,
`TamperDetected`, `ArmingAborted`.
