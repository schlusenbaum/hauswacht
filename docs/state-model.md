# Zustandsmodell

Implementierung: `custom_components/hauswacht/core/state_machine.py`

## Zustände

| Zustand | Bedeutung |
|---|---|
| `disarmed` | Unscharf |
| `arming` | Ausgangsverzögerung läuft |
| `armed` | Scharf |
| `pending` | Eingangsverzögerung läuft |
| `triggered` | Alarm, Reaktionsphase läuft (Sirenen/Benachrichtigungen) |
| `alarm_hold` | Reaktionsphase vorbei, Alarm noch nicht quittiert |

Der **Systemzustand** (ok, degraded, fault, starting) ist eine eigene Achse und wird nicht
in der Zustandsmaschine geführt.

## Sensorrollen

| Rolle | Verhalten im scharfen Zustand |
|---|---|
| `entry` | Startet die Eingangsverzögerung (bei Verzögerung 0: sofortiger Alarm) |
| `instant` | Sofortiger Alarm, auch während einer laufenden Eingangsverzögerung |
| `follower` | Wartet, wenn eine Eingangsverzögerung läuft, sonst sofortiger Alarm |
| `tamper_24h` | Wird immer gemeldet; löst nur Alarm aus, wenn das Profil das vorsieht |

## Übergänge

| Von | Ereignis | Bedingung | Nach |
|---|---|---|---|
| disarmed | ArmRequested | Bereitschaft OK, Ausgangsverzögerung > 0 | arming |
| disarmed | ArmRequested | Bereitschaft OK, keine Ausgangsverzögerung | armed |
| disarmed | ArmRequested | Policy verweigert | bleibt (Rejected) |
| disarmed | ArmRequested | Bestätigung nötig | bleibt (ConfirmationRequired) |
| arming | Sensor (außer Tamper) | – | bleibt (ignoriert) |
| arming | ExitDelayElapsed | erneute Prüfung OK | armed |
| arming | ExitDelayElapsed | neue Probleme, nicht automatisch überbrückbar | disarmed (ArmingAborted) |
| armed | entry | Eingangsverzögerung > 0 | pending |
| armed | entry (ohne Verzögerung), instant, follower | – | triggered |
| pending | entry, follower | – | bleibt |
| pending | instant | – | triggered |
| pending | EntryDelayElapsed | – | triggered |
| triggered | ReactionTimeElapsed | – | alarm_hold |
| alarm_hold | Sensor | Zyklen < Maximum | triggered (neuer Zyklus) |
| arming/armed/pending/triggered/alarm_hold | DisarmRequested | Code gültig | disarmed |
| beliebig | Startup | – | **disarmed** |
| armed/pending/alarm_hold | tamper_24h | Profil: `tamper_triggers_alarm` | triggered |

## Regeln

- **Keine direkten Zustandssetzer.** Der Zustand ändert sich nur über Ereignisse.
- **Profilwechsel nur aus `disarmed`.** Scharfschalten aus einem anderen Zustand wird
  abgelehnt.
- **Timer-Tokens.** Jeder Timer trägt ein Token. Läuft ein Timer ab, dessen Token nicht mehr
  aktuell ist (z. B. nach Unscharfschaltung oder Neustart), wird das Ereignis ignoriert.
- **Überbrückte Sensoren** (bewusst bestätigt oder `bypass_auto`) lösen im scharfen Zustand
  nicht aus.
- **Erneute Prüfung am Ende der Ausgangsverzögerung.** Bereits bestätigte Überbrückungen
  bleiben gültig. Neue Probleme können dann nicht mehr bestätigt werden, die Scharfschaltung
  wird abgebrochen (sichere Seite).
- **Unscharf während `triggered`** erzeugt `StopReaction`. Ob tatsächlich etwas
  ausgeschaltet wird, entscheidet der Sirenen-Guard (Brandsperre).
- **Testmodus** lässt sich nur im Zustand `disarmed` umschalten und bleibt über Neustarts
  erhalten. Alle Reaktionen tragen das Testmodus-Kennzeichen.
- **Neustart:** immer `disarmed`. War die Anlage vorher scharf, entsteht
  `RestartedDisarmed`, damit eine Benachrichtigung verschickt werden kann.

## Offene Punkte für spätere Versionen

- Fehlversuche bei der Code-Eingabe zählen und ggf. sperren (0.2.0).
- Bewertung von Sensorausfällen im scharfen Zustand („Ausfall = Alarm“ pro Sensor, 0.3.0).
