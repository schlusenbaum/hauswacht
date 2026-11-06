# Installation und Bedienung

> **Stand 0.3.0:** Bedienfeld, Profile, Zonen und Sensoren funktionieren. Ein Alarm erscheint
> als Hinweis in Home Assistant und als Ereignis. Es werden **noch keine Sirenen angesteuert
> und keine Push-Nachrichten verschickt.**

## Voraussetzungen

- Home Assistant 2026.10 oder neuer
- HACS (nur für öffentliche Repositories) oder manuelle Installation

## Installation

**Über HACS:** Menü (⋮) → Benutzerdefinierte Repositories →
`https://github.com/schlusenbaum/hauswacht`, Typ **Integration** → Hauswacht herunterladen →
Home Assistant neu starten.

**Manuell:** Den Ordner `custom_components/hauswacht` nach `/config/custom_components/hauswacht`
kopieren und Home Assistant neu starten.

Danach: **Einstellungen → Geräte & Dienste → Integration hinzufügen → Hauswacht.**
Hauswacht kann nur einmal eingerichtet werden.

## Entitäten

| Entität | Zweck |
|---|---|
| `alarm_control_panel.hauswacht` | Bedienfeld: Zuhause, Nacht, Abwesend, Urlaub, Unscharf |
| `switch.hauswacht_testmodus` | Testmodus (Name je nach Sprache der Instanz) |

## Einrichtung in drei Schritten

Alle Einstellungen liegen unter **Einstellungen → Geräte & Dienste → Hauswacht →
Konfigurieren** und lassen sich nur im **unscharfen** Zustand ändern.

### 1. Zonen anlegen

**Zonen und Sensoren → Zone anlegen.** Eine Zone ist eine Gruppe von Sensoren, z. B.
„Außenhaut“ (alle Türen und Fenster) oder „Keller“ (Bewegungsmelder).

Sensoren kommen auf zwei Wegen in eine Zone, beide lassen sich kombinieren:

- **Direkt auswählen:** Im Feld „Sensoren“ mehrere Binärsensoren anhaken.
- **Per Label (optional):** Ein Label wählen. Alle Binärsensoren, die dieses Label **direkt an
  der Entität** tragen, gehören dann automatisch dazu. Labels am Gerät zählen bewusst nicht,
  sonst kämen auch Batterie- oder Verbindungssensoren desselben Geräts mit in die Zone.

Welche Sensoren eine Zone am Ende umfasst, zeigt das Attribut `zones` am Bedienfeld.

### 2. Zonen den Profilen zuordnen

**Profile → Profil wählen.** Dort legst du fest:

| Einstellung | Bedeutung |
|---|---|
| Überwachte Zonen | Welche Zonen in diesem Profil scharf sind |
| Ausgangs- / Eingangsverzögerung | Zeit zum Verlassen bzw. zum Unscharfschalten nach dem Betreten |
| Dauer der Alarmreaktion | Wie lange ein Alarmzyklus dauert |
| Offene Sensoren beim Scharfschalten | Verweigern · nach Bestätigung erlauben · automatisch überbrücken |
| Ausgefallene Sensoren beim Scharfschalten | Verweigern · nach Bestätigung erlauben |
| Maximale Alarmzyklen | Wie oft nach einem Alarm erneut ausgelöst werden darf |
| Manipulation löst Alarm aus | Sonst wird Manipulation nur gemeldet |

Ein Profil ohne Zonen lässt sich **nicht** scharf schalten. So entsteht nie der Eindruck,
das Haus sei geschützt, obwohl nichts überwacht wird.

Standardzeiten:

| Profil | Ausgang | Eingang | Alarmreaktion |
|---|---|---|---|
| Zuhause | 0 s | 30 s | 180 s |
| Nacht | 0 s | 30 s | 180 s |
| Abwesend | 60 s | 30 s | 180 s |
| Urlaub | 60 s | 30 s | 180 s |

### 3. Rollen prüfen (meist nicht nötig)

Die Rolle eines Sensors ergibt sich aus seiner Geräteklasse:

| Geräteklasse | Rolle | Verhalten im scharfen Zustand |
|---|---|---|
| Tür, Garagentor, Öffnung | Eingang | Startet die Eingangsverzögerung |
| Fenster, Vibration | Sofort | Sofortiger Alarm |
| Bewegung, Anwesenheit, Präsenz | Mitläufer | Wartet, wenn gerade eine Eingangsverzögerung läuft, sonst sofortiger Alarm |
| Manipulation | Manipulation (24 h) | Wird immer gemeldet, auch unscharf |
| ohne / andere | Sofort | Sicherheitshalber sofortiger Alarm |

Abweichungen stellst du unter **Sensorrollen (Ausnahmen)** ein, z. B. ein Fenster, durch das
man das Haus betritt, als „Eingang“.

## Sensorüberwachung

- Ein Sensor ist **nicht verfügbar**, wenn er fehlt oder `unavailable` bzw. `unknown` meldet.
- Optional (**Sensorüberwachung → Maximale Funkstille**) gilt ein Sensor auch dann als
  ausgefallen, wenn er sich so viele Stunden nicht gemeldet hat. Batteriesensoren melden sich
  teils nur alle paar Stunden, der Wert sollte deshalb großzügig sein. Standard: aus.
- Fällt ein überwachter Sensor im scharfen Zustand aus, erscheint ein Hinweis
  „Hauswacht: Sensor ausgefallen“ und ein Ereignis `SensorUnavailable`.
- Die überwachten Sensoren werden beim Scharfschalten festgehalten. Wird während des scharfen
  Zustands ein Label entfernt, bleibt der Sensor bis zum Unscharfschalten überwacht.

## Scharfschalten mit Bestätigung

Erlaubt ein Profil offene oder ausgefallene Sensoren nur „nach Bestätigung“, verweigert das
normale Bedienfeld das Scharfschalten und nennt die betroffenen Sensoren. Bestätigen kannst du
mit der Aktion **`hauswacht.arm`**:

```yaml
action: hauswacht.arm
target:
  entity_id: alarm_control_panel.hauswacht
data:
  profile: night
  confirm: true
```

Offene Sensoren werden dabei **überbrückt**, also bis zum Unscharfschalten nicht überwacht.

## Attribute des Bedienfelds

| Attribut | Bedeutung |
|---|---|
| `profile`, `phase` | Aktives Profil, interner Zustand |
| `test_mode` | Testmodus aktiv |
| `timer`, `timer_ends_at` | Laufende Verzögerung und ihr Ende |
| `trigger_sensor`, `alarm_cycles` | Auslösender Sensor, Anzahl Alarmzyklen |
| `zones` | Zonen mit ihren tatsächlichen Sensoren |
| `monitored_sensors` | Gerade scharf überwachte Sensoren |
| `open_sensors`, `unavailable_sensors` | Offene bzw. ausgefallene Sensoren aller Zonen |
| `bypassed_sensors` | Überbrückte Sensoren |

## PIN

- 4 bis 8 Ziffern, wird nur als Hash gespeichert.
- Mit PIN ist er zum Unscharfschalten immer nötig, optional auch zum Scharfschalten.
- Ohne PIN darf die Anlage nicht für Sprachassistenten (z. B. Alexa) freigegeben werden.

## Verhalten nach einem Neustart

Hauswacht startet **immer unscharf**. War die Anlage vorher scharf, erscheint ein Hinweis
„Hauswacht: nach Neustart unscharf“. Der Testmodus bleibt erhalten.

## Ereignisse für eigene Automationen

Jede Aktion wird als Ereignis `hauswacht_event` gemeldet. Das Feld `type` nennt die Art:
`StateChanged`, `ActivateReaction` (Alarm), `StopReaction`, `TamperDetected`,
`SensorUnavailable`, `SensorsBypassed`, `ArmingAborted`, `RestartedDisarmed` und weitere.

## Upgrade von 0.2.0

Nach dem Update haben die Profile noch keine Zonen. Lege zuerst Zonen an und ordne sie den
Profilen zu, sonst verweigert Hauswacht das Scharfschalten.
