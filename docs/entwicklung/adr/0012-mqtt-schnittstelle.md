# ADR 0012: MQTT-Schnittstelle – Hauswacht für Wand-Tablets, ESP-Bedienteile und fremde Keypads

- Status: vorgeschlagen
- Datum: 2026-11-19

## Kontext

Hauswacht spricht heute schon MQTT – aber nur mit Geräten, die es selbst kennt:
Zigbee2MQTT-Keypads (Tasten lesen, Zustand anzeigen) und Nuki-Schlösser. Alles andere muss den
Umweg über Home Assistant gehen (Bedienfeld-Entität, Karten, Automationen).

Viele Geräte und Programme können aber MQTT, ohne Home Assistant zu kennen:

- **Wand-Tablets** mit Apps wie „MQTT Alarm Panel“ oder Kiosk-Browsern mit MQTT,
- **selbst gebaute Bedienteile** (ESPHome, Tasmota, Arduino) mit Tastenfeld, Display, LEDs,
  Summer,
- **Keypads anderer Hersteller**, die über eine Brücke (z. B. Node-RED, eigene Firmware) MQTT
  sprechen,
- **andere Systeme**: Node-RED, eine zweite Zentrale, eine Gebäudeleittechnik, ein Logger.

Für diese Geräte gibt es einen weit verbreiteten Standard aus Home Assistant selbst
(„MQTT-Alarmzentrale“): Zustand als Text (`disarmed`, `armed_away`, `pending`, `triggered` …)
auf einem Topic, Befehle als Text (`ARM_AWAY`, `DISARM` …) auf einem zweiten Topic, Code
optional als JSON. Wer diesen Standard spricht, funktioniert mit sehr vielen fertigen Geräten.

Der Wunsch ist **maximale Flexibilität**: fertige Geräte ohne Anpassung anschließen, eigene Geräte
mit allen Details versorgen (offene Melder, Restzeit, Alarmgrund), Wörter und Topics frei
anpassen.

Gleichzeitig gilt: Über MQTT **steuert etwas von außen die Alarmanlage**. Wer auf den Broker
schreiben darf, darf an die Anlage. Das darf nicht leichter sein als am Keypad.

## Entscheidung

### 1. Die MQTT-Schnittstelle ist ein Bedienteil

Neue Bedienteil-Art **„MQTT-Schnittstelle“** – neben Keypad, Aufkleber, Leser, Taster und Schloss.

- Man kann **mehrere** anlegen, z. B. eine für das Tablet im Flur (nur Bereich „Haus“), eine für
  das ESP-Bedienteil in der Garage (nur Bereich „Garage“), eine nur zum Mitlesen für Node-RED.
- Jede hat ein eigenes **Basis-Topic** (Standard `hauswacht/<name>`), einen **Bereich** (oder alle
  Bereiche), eigene **Tasten → Profile**, eine eigene **Anmeldung** und ein eigenes **Format**.
- Weil es ein Bedienteil ist, gilt alles, was für Bedienteile schon gilt: Rechte je Bereich,
  Gültigkeit der Person, PIN-Regeln, Fehlversuche und Sperre, Bedrohungs-PIN, Aktions-Codes,
  „trotzdem scharf“ per zweitem Befehl, Bestätigungsereignis, „zuletzt benutzt“, Anzeige in
  Übersicht und Einstellungsseite.
- Eingerichtet wird auf der **Einstellungsseite** (Reiter Personen und Bedienteile) und im
  **Dialog** – wie jedes Bedienteil.

### 2. Drei Stufen je Schnittstelle

| Stufe | Hauswacht sendet | Hauswacht nimmt an |
|---|---|---|
| **Nur senden** (Standard) | Zustand, Details, Ereignisse | nichts |
| **Scharf schalten** | wie oben | Scharf-Befehle |
| **Voll** | wie oben | Scharf- und Unscharf-Befehle, Alarm beenden |

Eine neue Schnittstelle beginnt immer mit **„Nur senden“**. Befehle anzunehmen ist ein bewusster
zweiter Schritt.

### 3. Topics

Für eine Schnittstelle mit Basis-Topic `hauswacht/flur`:

| Topic | Richtung | Gespeichert (retain) | Inhalt |
|---|---|---|---|
| `hauswacht/flur/state` | raus | ja | Zustand als Text, z. B. `armed_away` |
| `hauswacht/flur/attributes` | raus | ja | Details als JSON (siehe unten) |
| `hauswacht/flur/event` | raus | nein | Ereignisse als JSON |
| `hauswacht/flur/availability` | raus | ja | `online` / `offline` |
| `hauswacht/flur/set` | rein | – | Befehle |
| `hauswacht/flur/response` | raus | nein | Antwort auf einen Befehl |

Bei „alle Bereiche“ gibt es zusätzlich je Bereich `…/<bereich>/state`, `…/<bereich>/attributes`
und `…/<bereich>/set`. `…/state` zeigt dann den **zusammengefassten** Zustand (wie heute am
Keypad: Alarm vor Eingangsverzögerung vor Ausgangsverzögerung vor scharf vor unscharf).

Jedes Topic lässt sich einzeln umbenennen oder abschalten – für Geräte mit fest eingebauten
Topics.

### 4. Zustand (`state`)

Standardwerte wie die Bedienfeld-Entität von Home Assistant: `disarmed`, `armed_home`,
`armed_away`, `armed_night`, `armed_vacation`, `armed_custom_bypass`, `arming`, `pending`,
`triggered`. Welcher `armed_…`-Wert zu einem Profil gehört, steht schon heute am Profil
(„Knopf am Bedienfeld“).

### 5. Details (`attributes`)

JSON mit allem, was ein eigenes Gerät anzeigen möchte:

```json
{
  "state": "pending",
  "area": "haus",
  "profile": "abwesend",
  "profile_name": "Abwesend",
  "ready": false,
  "open_sensors": ["Haustür"],
  "delay_remaining": 23,
  "delay_total": 30,
  "alarm_kind": "burglary",
  "alarm_sensor": "Terrassentür",
  "changed_by": "Christian (Tablet Flur)",
  "changed_at": "2026-11-19T06:48:00+01:00",
  "code_locked_seconds": 0,
  "fire": false
}
```

- `ready` und `open_sensors`: Kann jetzt scharf geschaltet werden? Was ist offen? (Für das
  Profil, das die Taste „Abwesend“ schalten würde.)
- `delay_remaining` / `delay_total`: Restzeit der Verzögerung für Countdown-Anzeigen.
- `alarm_kind`: `burglary`, `fire`, `panic`, `always_active`, `tamper` …
- `fire`: Brandalarm aktiv – Bedienteile sollen das anders zeigen als einen Einbruch.
- **Nie enthalten**: PINs, Kartennummern, Benutzerkennungen.

### 6. Befehle (`set`)

Drei Formen, alle gleichzeitig verstanden:

1. **Text** (Standard der MQTT-Alarmzentrale): `ARM_AWAY`, `ARM_HOME`, `ARM_NIGHT`,
   `ARM_VACATION`, `ARM_CUSTOM_BYPASS`, `DISARM`, `PANIC`.
2. **JSON kurz**: `{"action": "ARM_AWAY", "code": "1234"}` – das Feld für den Code heißt
   einstellbar `code` (Standard).
3. **JSON voll** (Hauswacht): `{"action": "arm", "profile": "abwesend", "code": "1234",
   "force": true, "id": "a17"}` – Profil direkt, „trotzdem scharf“, Vorgangsnummer.

Welches Profil `ARM_AWAY`, `ARM_HOME` usw. schaltet, stellt man je Schnittstelle ein (wie die
Tasten am Keypad). Vorschlag: das Profil, das am Bedienfeld auf dem Knopf „Abwesend“ bzw. „Zuhause“ liegt.

Ein Code ohne Taste (`{"code": "4711"}` oder Code + Taste) kann ein **Aktions-Code** sein –
dieselben Regeln wie am Keypad: nie unscharf, kein Fehlversuch, in der Sperre gesperrt.

### 7. Antwort (`response`)

Jeder Befehl bekommt eine Antwort, mit derselben `id`, wenn eine mitkam:

```json
{"id": "a17", "result": "not_ready", "open_sensors": ["Küchenfenster"], "can_force": true}
```

`result`: `ok`, `invalid_code`, `not_ready`, `not_allowed`, `already_disarmed`, `locked`
(mit `lock_seconds`), `disabled` (Stufe erlaubt den Befehl nicht), `unknown_command`.

### 8. Ereignisse (`event`)

Die Ereignisse von Hauswacht (`hauswacht_event`) des Bereichs, als JSON – z. B. Alarm ausgelöst,
Melder offen beim Scharfschalten, falscher PIN, Sirenen-Test, Funkstille. Auswahl je
Schnittstelle (alle / nur wichtige / aus). Gefiltert wie überall: keine PINs, keine
Kartennummern.

### 9. Format frei anpassen

Für Geräte mit eigenen Wörtern lässt sich jede Schnittstelle umstellen:

- **Zustandswörter** umbenennen, z. B. `armed_away` → `ARMED_AWAY` oder `2`.
- **Befehlswörter** umbenennen, z. B. `ARM_AWAY` → `away` oder `A`.
- **Code-Feld** umbenennen (`code`, `pin`, `user_code` …).
- **Topics** umbenennen oder einzelne abschalten.
- **Gespeichert (retain)** je Topic.

Vorlagen (Jinja) gibt es bewusst nicht – Umbenennen deckt fertige Geräte ab, und wer mehr
braucht, nimmt das volle JSON oder Node-RED.

### 10. Sicherheit

- **Standard: aus.** MQTT-Integration muss in Home Assistant eingerichtet sein; ohne MQTT bleibt
  die Art ausgegraut mit Hinweis.
- **Unscharf immer nur mit PIN oder Karte** – auch wenn die Anlage sonst „Alarm ohne PIN
  beenden“ oder „Tasten ohne PIN“ erlaubt. Auf dem Broker kann jeder schreiben, der Zugang hat;
  ein Taster an der Wand ist etwas anderes als ein Netzwerk.
- **Scharf ohne PIN** nur, wenn die Schnittstelle das ausdrücklich erlaubt (eigener Schalter,
  aus).
- **Gespeicherte Befehle werden ignoriert.** Eine Nachricht mit retain-Flag auf `set` wird nie
  ausgeführt – sonst würde ein altes `DISARM` nach jedem Neustart erneut ankommen. Hauswacht
  meldet das als Prüfhinweis.
- **Fehlversuche zählen** wie am Keypad und führen zur gemeinsamen Sperre. Die Sperre gilt für
  alle Bedienteile.
- **Bedrohungs-PIN** funktioniert: schaltet unscharf und löst den stillen Notruf aus; die Antwort
  ist `ok` wie sonst.
- **PANIC** (Notruf) ist eine eigene Freigabe je Schnittstelle (aus) mit Wahl „still“ oder
  „laut“ – wie die Notruf-Taste am Keypad.
- **Keine Geräte**: Die Schnittstelle schaltet selbst nichts. Sie sendet Nachrichten und ruft
  dieselben Funktionen auf wie ein Keypad – Sirenen gehen weiter nur über alle Sirenen-Sperren.
- **Kein PIN im Klartext** in Protokoll, Ereignissen, Antworten oder Diagnose.
- **Doku-Pflicht:** Die Anleitung erklärt Broker-Benutzer und Zugriffsrechte (ACL) – das Tablet
  darf nur `hauswacht/flur/#` lesen und `hauswacht/flur/set` schreiben – und TLS.
- **Prüfungen** in der Übersicht: Schnittstelle mit „Voll“, aber Broker ohne Anmeldung nicht
  erkennbar → Hinweis auf die Anleitung; retain-Befehl gesehen; Basis-Topic doppelt;
  Basis-Topic überschneidet sich mit einem Zigbee2MQTT-Keypad.

### 11. Verfügbarkeit

Beim Start sendet Hauswacht `online` und den aktuellen Zustand (gespeichert), beim Beenden
`offline`. Bricht Home Assistant ab, bleibt `online` stehen – Geräte sollen deshalb zusätzlich
den Status des Brokers bzw. `homeassistant/status` beachten (steht in der Anleitung).

## Umsetzung in Stufen

| Vorabversion | Inhalt |
|---|---|
| 0.58.0b1 | Art „MQTT-Schnittstelle“, Stufe „Nur senden“: `state`, `attributes`, `event`, `availability`; Einrichten auf Seite und im Dialog; Doku mit Beispielen |
| 0.58.0b2 | Befehle (`set`) und Antworten (`response`): Text, JSON kurz, JSON voll; Stufen „Scharf schalten“ und „Voll“; Aktions-Codes; „trotzdem scharf“; PANIC; retain-Schutz |
| 0.58.0b3 | Format anpassen (Wörter, Code-Feld, Topics, retain), alle Bereiche mit Unter-Topics, Prüfungen; Beispiele für Tablet-App, ESPHome und Node-RED |

Die Logik (Befehl auswerten, Antwort bauen, Wörter umsetzen, Details zusammenstellen) kommt in den
reinen Kern (`core/mqtt_interface.py`) und wird ohne Home Assistant getestet. Der MQTT-Teil
(abonnieren, senden) bleibt dünn und hängt am vorhandenen `ControlManager`.

## Verworfene Alternativen

- **Nur die Bedienfeld-Entität über die MQTT-Statestream-Integration von Home Assistant
  veröffentlichen.** Liefert nur den Zustand, keine Befehle, keine Antworten, keine Details.
- **Eine einzige, feste Schnittstelle für die ganze Anlage.** Zu wenig: verschiedene Geräte
  brauchen verschiedene Bereiche, Wörter und Rechte.
- **MQTT-Discovery für Home Assistant.** Hauswacht ist schon in Home Assistant; Discovery würde
  doppelte Entitäten erzeugen.
- **Jinja-Vorlagen für Nachrichten.** Mächtig, aber fehleranfällig und schwer zu prüfen; das
  volle JSON plus Umbenennen reicht für fertige und eigene Geräte.
- **Unscharf ohne PIN als Option.** Bewusst nicht: zu gefährlich bei einem Netzwerk-Zugang.

## Folgen

- Fertige Geräte, die den Standard der MQTT-Alarmzentrale sprechen, funktionieren ohne
  Anpassung.
- Eigene Geräte bekommen alle Details, die die Karten in Home Assistant auch haben.
- Die Sicherheitsregeln bleiben an einer Stelle: MQTT ist nur ein weiterer Weg in dieselbe
  Prüfung wie Keypad und Karte.
- Mehr Einstellungen bei den Bedienteilen – deshalb sinnvolle Standards und „Nur senden“ als
  Start.
