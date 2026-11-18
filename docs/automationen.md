# Automationen: was nehme ich wofür?

**Deutsch** | [English](en/automations.md)

Ein Spickzettel für eigene Automationen: Für jeden Anlass steht hier, **welchen Auslöser** du
nimmst und warum. Alle Einzelheiten (jedes Feld, jede Entität) stehen in der
**[Referenz](referenz.md)**, fertige Automationen unter **[Beispiele](beispiele.md)**.

Die Beispiele nennen das Bedienfeld `alarm_control_panel.hauswacht` – mit
[Bereichen](profile.md#bereiche) das des jeweiligen Bereichs nehmen.

## Faustregeln

1. **Für Zustände das Attribut `phase` des Bedienfelds** – es ist eindeutig, hängt nicht vom
   Profil oder dessen Knopf ab und stimmt auch nach einem Neustart.
2. **Für Vorgänge das Ereignis `hauswacht_event`** – Dinge, die keinen Zustand haben: falscher PIN,
   Sabotage, Taster, Aktions-Code, Ausfall.
3. **Immer die Bedingung „Testmodus aus“** in Automationen, die etwas Echtes tun:

   ```yaml
   conditions:
     - condition: state
       entity_id: alarm_control_panel.hauswacht
       attribute: test_mode
       state: false
   ```

4. **Nie selbst Sirenen schalten** – das macht Hauswacht mit Brandsperre und Testmodus-Sperre.

## Ich will reagieren, wenn …

### Scharf, unscharf, Alarm

| … | Nimm | Hinweis |
|---|---|---|
| ein **Alarm beginnt** | Attribut `phase` → `triggered` | Robuster als das Ereignis `ActivateReaction`; der auslösende Melder steht in `trigger_sensor` |
| ein Alarm **vorbei** ist (Reaktionszeit abgelaufen) | `phase` → `alarm_hold` | Noch nicht quittiert – Profil ist weiter scharf |
| ein Alarm **beendet** ist (egal wie) | `phase` **von** `triggered`/`alarm_hold` **nach** `disarmed` oder `armed` | „Alarm beenden“ führt zu `armed`, „unscharf“ zu `disarmed` |
| die Anlage **scharf** ist (egal welches Profil) | `phase` → `armed` | Erst **nach** der Ausgangsverzögerung – alle sind draußen |
| ein **bestimmtes Profil** scharf ist | `phase` → `armed` + Bedingung `profile_name` | Profilname genau wie in Hauswacht |
| jemand **scharf schaltet** (Ausgangsverzögerung beginnt) | `phase` → `arming` | Ende in `timer_ends_at` |
| jemand **heimkommt** (Eingangsverzögerung) | `phase` → `pending` | Z. B. Flurlicht an; Ende in `timer_ends_at` |
| **unscharf** geschaltet wurde | `phase` → `disarmed` | `from: pending` = beim Heimkommen; wer, steht in `changed_by` |
| jeder **Zustandswechsel** mit Grund | Ereignis `StateChanged` | `old`, `new`, `cause` |
| Scharfschalten **abgelehnt** wurde | Ereignis `Rejected` | `reason`, `open_sensors` |
| Scharfschalten am Ende der Ausgangsverzögerung **abgebrochen** wurde | Ereignis `ArmingAborted` | noch offene Melder in `open_sensors` |

### Sabotage, Störungen, Notruf

| … | Nimm | Hinweis |
|---|---|---|
| **Sabotage** gemeldet wird | Ereignis `TamperDetected` | Melder in `sensor_key`; kommt auch unscharf |
| ein **Melder ausfällt** | Ereignis `SensorUnavailable` | oder `sensor.hauswacht_systemstatus` → `degraded` |
| **Funknetz/Gateway** gestört ist | Ereignis `InfrastructureFault` (`InfrastructureRecovered` = wieder gut) | oder Systemstatus → `fault` |
| ein **falscher PIN** eingegeben wurde | Ereignis `InvalidCode` | `failures`, `lock_seconds` (Sperre) |
| die **Notruf-Taste** gedrückt wurde | Ereignis `Emergency` | `mode`: `off`, `silent`, `alarm` |
| ein **immer aktiver Melder** ausgelöst hat (z. B. Wasser) | Ereignis `AlwaysActiveTriggered` | `sensor_key` |

### Bedienung und Automatik

| … | Nimm | Hinweis |
|---|---|---|
| ein **Aktions-Code** eingegeben wurde | Entität `event.hauswacht_aktions_code` (Ereignistyp = Name des Codes) | Oder Ereignis `ActionCode` mit `name` – siehe [Aktions-Codes](bedienteile.md#aktions-codes) |
| ein **Taster** gedrückt wurde | Ereignis `ButtonPressed` | `control` (Name des Tasters), `press` |
| der **Gastmodus** an- oder ausgeht | Attribut `guest_mode` oder Entität `switch.hauswacht_gastmodus` | Ende in `guest_until`; Ereignis `GuestMode` mit `by` |
| der **Testmodus** an- oder ausgeht | Entität `switch.hauswacht_testmodus` oder Attribut `test_mode` | |
| die **Profil-Automatik** scharf geschaltet hat | Ereignis `AutoArmed` | `reason`: `Uhrzeit`, `Zeitplan`, `alle weg` … |
| die Profil-Automatik es **nicht** konnte | Ereignis `AutoArmFailed` bzw. `AutoArmSkipped` | `reason`, `details`; `guest_mode: true` = wegen Gastmodus |
| **Fenster offen** sind (z. B. Hinweis beim Gehen) | Entität `binary_sensor.hauswacht_offene_sensoren` | Namen im Attribut `names` |
| ein Fenster **gekippt** ist ([Kippstellung](melder.md#melder-mit-kippstellung-gekippt)) | Attribut `tilted_sensors` des Bedienfelds | Auch wenn das Profil gekippt erlaubt; im Ereignis Feld `position` |

## Ich will etwas tun …

| … | Nimm |
|---|---|
| **scharf schalten** (bestimmtes Profil) | Aktion `hauswacht.arm` mit `profile` (und `confirm: true` für „trotzdem scharf“) |
| **unscharf schalten** | Aktion `alarm_control_panel.alarm_disarm` (mit `code`, wenn ein PIN verlangt wird) |
| **Alarm beenden**, Profil bleibt scharf | `button.press` auf `button.hauswacht_alarm_beenden` |
| **Gastmodus** an bis … | Aktion `hauswacht.guest_mode` mit `on: true`, `until` |
| in einer Nachricht **den Melder** nennen | `{{ state_attr(state_attr('alarm_control_panel.hauswacht', 'trigger_sensor'), 'friendly_name') }}` |
| **wissen, wer** geschaltet hat | Attribut `changed_by`, z. B. „Anna (Keypad Flur)“ |

## Häufige Stolperfallen

- **Zustand des Bedienfelds statt `phase`:** `armed_night`, `armed_away` … hängen vom Knopf des
  Profils ab; ein Profil ohne Knopf ist `armed_custom_bypass`. `phase` ist immer `armed`.
- **`triggered` des Bedienfelds** gilt auch während `alarm_hold` – wer zwischen „Alarm läuft“
  und „Alarm vorbei, nicht quittiert“ unterscheiden will, nimmt `phase`.
- **Entitäts-IDs** hängen von der Sprache beim Einrichten ab (`switch.hauswacht_testmodus` bzw.
  `switch.hauswacht_test_mode`) – im Zweifel unter Einstellungen → Entitäten nachsehen.
- **Ereignisse kommen auch im Testmodus** – ohne die Testmodus-Bedingung gehen beim Probelauf
  Lichter an und Kameras zeichnen auf.
- **Mehrere Bereiche:** Jedes Ereignis hat `area` (z. B. `garage`, `main`, `all` für die ganze
  Anlage) – im Auslöser unter `event_data` mit angeben; für Zustände das Bedienfeld des Bereichs
  nehmen.
- **Selbst nachsehen:** Entwicklerwerkzeuge → Ereignisse → `hauswacht_event` abonnieren →
  „Zuhören starten“ zeigt jedes Ereignis mit allen Feldern; Entwicklerwerkzeuge → Zustände zeigt
  die Attribute des Bedienfelds.
