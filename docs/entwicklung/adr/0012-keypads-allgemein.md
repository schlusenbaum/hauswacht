# ADR 0012: Keypads allgemein anbinden – ein Eingang für alle Geräte, Blueprints und MQTT

- Status: in Arbeit (0.58)
- Datum: 2026-11-19

## Kontext

Hauswacht bindet heute ein Keypad mit PIN-Eingabe und Rückmeldung direkt an: das
Zigbee2MQTT-Keypad. Viele andere verbreitete Keypads kann es nicht:

- **ZHA** (Frient, Xfinity/Centralite, Heiman): ZHA macht aus dem Keypad ein eigenes kleines
  Bedienfeld,
- **Z-Wave**: das Ring Keypad v2 meldet PIN und Taste als Z-Wave-Benachrichtigung und bekommt
  seine Anzeige über Z-Wave-Werte,
- **deCONZ**, **ESPHome-Eigenbauten**, **Node-RED**,
- Geräte und Programme **ohne Home Assistant**, die nur MQTT sprechen (Wand-Tablet-Apps,
  Tasmota/Arduino, andere Systeme).

Heute behilft man sich mit Automationen, die PIN und Taste an das Bedienfeld weiterreichen. Dabei
geht verloren, **welches** Keypad es war (Bereich, Rechte je Bedienteil), es gibt **keine
Antwort** (falscher PIN, nicht bereit, gesperrt) und die Hauswacht-Funktionen fehlen („trotzdem
scharf“, Aktions-Codes, Karte + PIN, Anlernen von Karten).

Jedes Gerät einzeln einzubauen, hieße: viel gerätespezifischer Code für Geräte, die wir nicht
besitzen und nicht testen können.

## Entscheidung

### 1. Ein allgemeiner Keypad-Eingang

Hauswacht bekommt **einen** Eingang für beliebige Keypads. Jedes Gerät wird über einen kleinen
**Übersetzer** angebunden:

```
Zigbee2MQTT-Keypad ──(eingebauter Übersetzer, wie bisher)──┐
Ring / Frient / …  ──(Blueprint)───────────────────────────┼──► gemeinsamer Keypad-Kern
ESPHome / Node-RED ──(Aktion direkt)───────────────────────┤
MQTT               ──(eingebauter Übersetzer, später)──────┘
```

Der **Keypad-Kern** ist das, was das Zigbee2MQTT-Keypad heute schon macht: Anmeldung (PIN, Karte,
Karte + PIN), Rechte je Bereich, Fehlversuche und Sperre, Bedrohungs-PIN, Aktions-Codes,
„trotzdem scharf“, Notruf, Anlernen unbekannter Karten, Schalten. Er wird aus der
Zigbee2MQTT-Anbindung herausgelöst, damit alle Wege ihn nutzen. **Am Zigbee2MQTT-Keypad ändert
sich für Nutzer nichts.**

### 2. Pflicht-Anmeldung als Bedienteil

Ein allgemeines Keypad ist ein **Bedienteil** der Art Keypad mit der Quelle **„Allgemein“**
(neben „Zigbee2MQTT“). Es hat Name, Bereich, Tasten → Profile, Anmeldung und Notruf – wie das
Zigbee2MQTT-Keypad. Die Tasten haben **freie Namen** (Vorschlag `home`, `away`, `night`), damit
jedes Gerät seine eigenen Tasten melden kann.

Eingaben von unbekannten Keypads werden **abgelehnt**. Damit das Anlegen bequem ist: Meldet sich
ein unbekanntes Keypad, zeigt die Einstellungsseite (und der Dialog) „Unbekanntes Keypad ‚flur‘
hat sich gemeldet – anlegen?“. Ein Klick legt es mit diesem Namen an.

Begründung: Herkunft immer klar, Bereich und Rechte je Keypad, „zuletzt benutzt“ und Protokoll
je Keypad, Prüfungen möglich. Wer gar nichts einrichten will, kann wie bisher das Bedienfeld per
Automation mit PIN schalten – nur ohne die Extras.

### 3. Aktion `hauswacht.keypad_input` mit Antwort

| Feld | Bedeutung |
|---|---|
| `keypad` | Kennung des Keypads (wie in Hauswacht angelegt) |
| `button` | `disarm`, `emergency` oder eine der eigenen Tasten (z. B. `away`); leer = nur Code |
| `code` | PIN oder Kartennummer (optional) |
| `force` | „trotzdem scharf“ (optional, nur mit Recht dazu) |

Die Aktion gibt eine **Antwort** zurück (Antwortdaten von Home Assistant):

```yaml
result: not_ready          # ok | invalid_code | not_ready | not_allowed | already_disarmed
                           # | locked | unknown_keypad | unknown_button | pending
open_sensors: [Küchenfenster]
can_force: true
lock_seconds: 0
display: disarmed          # was das Keypad jetzt zeigen soll
```

- `pending`: erster Ausweis bei „Karte + PIN“ – zweiten Ausweis abwarten.
- Ein Code ohne Taste (oder Code + Taste) kann ein **Aktions-Code** sein – dieselben Regeln wie am
  Zigbee2MQTT-Keypad: nie unscharf, kein Fehlversuch, in der Sperre gesperrt.
- Fehlende Rechte ergeben wie am Keypad `invalid_code` – kein Hinweis, ob der PIN stimmte.

**Wer darf die Aktion aufrufen?** Nur Automationen und Skripte (ohne Benutzer) sowie
Administratoren. Normale Benutzer bedienen über die Hauswacht-Karte – sonst könnte jeder
angemeldete Benutzer einen Notruf ohne PIN auslösen.

**Doppelte Meldungen:** Dieselbe Eingabe vom selben Keypad innerhalb von 2 Sekunden wird nur
einmal ausgewertet; der zweite Aufruf bekommt dieselbe Antwort. So zählt ein doppelt gesendeter
falscher PIN nicht doppelt.

### 4. Anzeige-Entität je Keypad

Jedes allgemeine Keypad bekommt `sensor.<keypad>_anzeige`. Der Blueprint reagiert auf ihre
Änderungen und steuert damit das Gerät (LEDs, Töne, Display).

| Zustand | Bedeutung |
|---|---|
| `disarmed` | unscharf |
| `exit_delay` | Ausgangsverzögerung läuft |
| `armed_home`, `armed_away`, `armed_night`, `armed_vacation`, `armed_custom_bypass` | scharf (Knopf am Bedienfeld des Profils) |
| `entry_delay` | Eingangsverzögerung läuft |
| `triggered` | Einbruchalarm |
| `test_alarm` | Alarm im **Testmodus** – nie `triggered`, damit ein Keypad mit eingebauter Sirene im Testmodus nicht losheult |
| `fire` | Brand erkannt – hat Vorrang vor allem anderen |

Attribute: `delay_ends` (Zeitpunkt), `delay_seconds`, `area`, `profile`, `ready`,
`open_sensors`, `changed_by`, `last_result`. **Nie**: PINs, Kartennummern.

Bei „alle Bereiche“ zeigt die Entität den zusammengefassten Zustand (Brand vor Alarm vor
Eingangsverzögerung vor Ausgangsverzögerung vor scharf vor unscharf) – wie das
Zigbee2MQTT-Keypad heute.

### 5. Blueprints als Adapter

Für verbreitete Geräte liefert Hauswacht **Blueprints** mit (Import-Knopf in der Doku): einer je
Gerät, der beide Richtungen übersetzt (Gerät → Aktion, Anzeige-Entität → Gerät). Der Nutzer wählt
nur sein Gerät und sein Hauswacht-Keypad.

- Blueprints tragen eine **Versionsnummer**; Hauswacht kann melden, wenn ein Blueprint veraltet
  ist.
- Sie ignorieren `unknown`/`unavailable` und senden die Anzeige auch nach einem Neustart.
- Sie halten so wenige Ablaufverfolgungen wie möglich (PINs!).
- Blueprints sind **keine Pflicht**: eigene Automation, Node-RED oder ESPHome-Gerät, das die
  Aktion direkt aufruft, funktionieren genauso.

### 6. MQTT-Schnittstelle (später)

Für Geräte ohne Home Assistant kommt danach eine MQTT-Schnittstelle als weiterer eingebauter
Übersetzer in denselben Kern: Zustand, Details, Ereignisse senden, Befehle (Standard-Wörter wie
`ARM_AWAY`/`DISARM`, Code als JSON) annehmen, Antwort senden; Wörter und Topics frei anpassbar;
Befehle mit retain-Flag werden nie ausgeführt. Sie gilt als Keypad – mit denselben Regeln wie das
Zigbee2MQTT-Keypad.

### 7. Kennzeichnung: was erprobt ist und was nicht

In Doku und Einstellungsseite bekommt jeder Weg ein Kennzeichen:

| Kennzeichen | Bedeutung | Beispiele |
|---|---|---|
| **Erprobt** | automatische Tests + im Alltag mit echter Hardware geprüft | Zigbee2MQTT-Keypad, Karten, Aufkleber, Taster |
| **Getestet** | automatische Tests, ohne Rückmeldung mit echter Hardware | allgemeiner Keypad-Eingang, Nuki, MQTT-Schnittstelle |
| **Ungetestet – eigene Verantwortung** | nach Doku gebaut, nie am Gerät geprüft | Blueprints für Ring, Frient, Xfinity … |

Meldet jemand „läuft mit Gerät X“, steigt ein Blueprint zu „Getestet von der Community“ auf.

### 8. Sicherheit

- **Keine neuen Ausnahmen.** Unscharf nur mit PIN oder Karte, Notruf wie am Keypad – genau die
  Regeln des Zigbee2MQTT-Keypads.
- **Hauswacht schaltet weiter keine Geräte.** Der allgemeine Weg sendet nicht einmal selbst an
  das Keypad – das macht der Blueprint. Sirenen nur über alle Sirenen-Sperren.
- **Testmodus und Brand** haben eigene Anzeigezustände (siehe 4).
- **PINs im Klartext außerhalb von Hauswacht:** Meldet ein Gerät den PIN als Ereignis, speichert
  Home Assistant es in seiner Datenbank, und die Ablaufverfolgung der Automation enthält ihn. Das
  lässt sich von Hauswacht aus nicht verhindern. Die Anleitung erklärt, wie man diese Ereignisse
  aus der Datenbank ausschließt, und sagt es offen.
- **Die Aktion ist ein Vertrag.** Felder und Antworten werden in den Vorabversionen festgezurrt
  und danach nur noch erweitert, nie umbenannt.

## Umsetzung in Stufen

| Vorabversion | Inhalt |
|---|---|
| 0.58.0b1 | Keypad-Kern herauslösen; Keypad-Quelle „Allgemein“, Aktion mit Antwort, Anzeige-Entität, unbekanntes Keypad anlegen; Einstellungsseite und Dialog; Kennzeichnung Erprobt/Getestet/Ungetestet; Doku mit Beispiel-Automation |
| 0.58.0b2 | Blueprints (Ring Keypad v2, Frient und Xfinity/Centralite über ZHA, ESPHome-Beispiel) mit Versionsnummer und Import-Knopf |
| 0.58.0b3 | MQTT-Schnittstelle |

## Verworfene Alternativen

- **Jedes Keypad einzeln in Hauswacht einbauen.** Viel Code für Geräte, die wir nicht besitzen;
  jede Änderung am Gerät bräuchte eine neue Hauswacht-Version.
- **Ohne Anmeldung („Automation ruft mit PIN auf, fertig“).** Keine Herkunft, keine Rechte je
  Keypad, keine Prüfungen – gibt es außerdem schon über das Bedienfeld.
- **Anzeige nur als Ereignis.** Nach einem Neustart wüsste das Keypad nicht, was gilt; eine
  Entität ist dauerhaft, in der Historie sichtbar und leicht zu prüfen.
- **Nur eine MQTT-Schnittstelle.** Würde Geräte in Home Assistant (ZHA, Z-Wave) nicht abdecken.

## Folgen

- Jedes Keypad, das Home Assistant oder MQTT erreicht, kann Hauswacht mit allen Funktionen
  bedienen.
- Die Sicherheitsregeln bleiben an einer Stelle.
- Gerätespezifisches liegt in kleinen, sichtbaren Blueprints, die Nutzer anpassen und verbessern
  können.
- Die Aktion ist eine öffentliche Schnittstelle und muss stabil bleiben.
