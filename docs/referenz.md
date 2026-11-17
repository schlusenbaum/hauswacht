# Referenz

**Deutsch** | [English](en/reference.md)

Entitäts-IDs gelten für eine deutschsprachige Home-Assistant-Instanz (auf Englisch z. B.
`switch.hauswacht_test_mode`). Für weitere Bereiche kommt der Bereichsname hinter „hauswacht“,
z. B. `alarm_control_panel.hauswacht_garage`.

## Entitäten

### Bedienung

| Entität | Zweck |
|---|---|
| `alarm_control_panel.hauswacht` | Bedienfeld: Knöpfe der Profile mit Bedienfeld-Knopf, Unscharf |
| `alarm_control_panel.hauswacht_alle` | Nur mit mehreren Bereichen: „Alle Bereiche“ |
| `select.hauswacht_profil` | Profil für die Knöpfe „Scharf schalten“ (scharf: aktives Profil) |
| `button.hauswacht_scharf_schalten` | Gewähltes Profil scharf schalten |
| `button.hauswacht_trotzdem_scharf_schalten` | Gewähltes Profil scharf schalten, offene Melder überbrücken |
| `button.hauswacht_unscharf_schalten` | Sofort unscharf, auch während eines Alarms |
| `button.hauswacht_alarm_beenden` | Nur den Alarm beenden, Profil bleibt scharf |
| `switch.hauswacht_testmodus` | Testmodus |
| `switch.hauswacht_gastmodus` | [Gastmodus](profile.md#gastmodus) für alle Bereiche (an = keine automatische Scharfschaltung); Attribut `areas` mit Ende je Bereich |
| `event.hauswacht_aktions_code` | Nur mit [Aktions-Codes](bedienteile.md#aktions-codes) der Aktion „Ereignis“: Ereignistyp = Name des Codes, Attribute `keypad`, `test` |

### Zustand und Diagnose

| Entität | Zweck |
|---|---|
| `binary_sensor.hauswacht_offene_sensoren` | „Offen“, sobald ein Melder einer Meldergruppe offen ist; Attribute `sensors`, `names` |
| `sensor.hauswacht_systemstatus` | `ok` · `degraded` (Melder ausgefallen) · `fault` (Störung); Attribute `faulty_infrastructure`, `unavailable_sensors` |
| `sensor.hauswacht_letzter_sirenentest` | Letzter Sirenentest; je Sirene Datum und „gehört?“ in den Attributen |
| `sensor.hauswacht_funkstille_beobachtung` | Empfehlung für die maximale Funkstille, längste Pausen je Melder |
| `sensor.hauswacht_heimkehr_beobachtung` | Anzahl ausgewerteter Heimkehrten; Attribute `sources`, `recent`, `entry_times`, `door_proof` |
| `button.hauswacht_heimkehr_bericht` | Bericht der Heimkehr-Beobachtung als Meldung in Home Assistant (zum Herunterladen: Karte „Hauswacht Übersicht“) |
| `sensor.hauswacht_simulierte_sensoren` | Grundlage der Testkarte (ausgeblendet) |

### Profil-Einstellungen (Kategorie Konfiguration)

| Entität | Zweck |
|---|---|
| `select.hauswacht_profil_bearbeiten` | Welches Profil die folgenden Entitäten zeigen und ändern |
| `number.hauswacht_ausgangsverzogerung`, `number.hauswacht_eingangsverzogerung` | Verzögerungen |
| `number.hauswacht_dauer_der_alarmreaktion`, `number.hauswacht_alarmzyklen` | Alarmreaktion |
| `number.hauswacht_wartezeit_bei_abwesenheit`, `number.hauswacht_turbeleg_ortung_vor_der_tur` | Automatik |
| `select.hauswacht_unscharf_bei_ruckkehr` | Automatik: Aus, Wie bisher, Mit Türbeleg (ersetzt seit 0.42 den Schalter „Unscharf beim Heimkommen“) |
| `select.hauswacht_offene_sensoren_beim_scharfschalten`, `select.hauswacht_ausgefallene_sensoren_beim_scharfschalten` | Verhalten beim Scharfschalten |
| `select.hauswacht_sirenenton`, `select.hauswacht_sirenenlautstarke` | Sirene |
| `switch.hauswacht_stiller_alarm`, `switch.hauswacht_sabotage_lost_alarm_aus` | Schalter |
| `time.hauswacht_automatisch_scharf_um`, `time.hauswacht_automatisch_unscharf_um` | Uhrzeiten |

## Attribute des Bedienfelds

| Attribut | Bedeutung |
|---|---|
| `area`, `area_name` | Bereich |
| `profile`, `profile_name` | Aktives Profil (Kennung, Name) |
| `phase` | Zustand unabhängig vom Profil: `disarmed` (unscharf), `arming` (Ausgangsverzögerung), `armed` (scharf), `pending` (Eingangsverzögerung), `triggered` (Alarm), `alarm_hold` (Alarm vorbei, noch nicht quittiert) – siehe [Beispiel](#beispiel-automation-wenn-scharf) |
| `changed_by` | Wer zuletzt geschaltet hat, z. B. „Anna (Keypad Flur)“ |
| `test_mode` | Testmodus aktiv |
| `guest_mode`, `guest_until` | Gastmodus aktiv, Ende (leer = bis zum Ausschalten) |
| `timer`, `timer_ends_at` | Laufende Verzögerung und ihr Ende |
| `trigger_sensor`, `alarm_cycles` | Auslösender Melder, Anzahl Alarmzyklen |
| `zones` | Meldergruppen mit ihren tatsächlichen Meldern |
| `monitored_sensors` | Gerade scharf überwachte Melder |
| `open_sensors`, `unavailable_sensors` | Offene bzw. ausgefallene Melder aller Meldergruppen |
| `open_rule_sensors` | Offene Melder, die im aktiven Profil nur in Auslöseregeln vorkommen |
| `bypassed_sensors`, `bypassed_until_closed` | Überbrückte Melder (bis unscharf bzw. bis zum Schließen) |
| `last_contact` | Letzter Kontakt je Melder |
| `sirens_hardware_enabled` | Echte Sirenenansteuerung freigegeben |
| `last_siren_decision` | Welche Sirenen beim letzten Alarm angesteuert bzw. warum gesperrt wurden |
| `code_failures`, `code_locked_until` | Falsche Eingaben, Ende einer laufenden Sperre |
| `areas` | Nur „Alle Bereiche“: Zustand je Bereich |

### Beispiel: Automation, wenn scharf

`phase` ist der einfachste Auslöser für eigene Automationen, weil er nicht davon abhängt, welchen
Bedienfeld-Knopf ein Profil hat. Welches Profil scharf ist, steht in `profile_name`.

**Haustür abschließen, sobald „Abwesend“ oder „Urlaub“ scharf ist** (also nach der
Ausgangsverzögerung, wenn alle draußen sind):

```yaml
alias: Haustür abschließen, wenn Hauswacht scharf
triggers:
  - trigger: state
    entity_id: alarm_control_panel.hauswacht
    attribute: phase
    to: armed
conditions:
  - condition: template
    value_template: >
      {{ state_attr('alarm_control_panel.hauswacht', 'profile_name') in ['Abwesend', 'Urlaub'] }}
actions:
  - action: lock.lock
    target:
      entity_id: lock.haustuer
```

Die Profilnamen müssen genau so geschrieben sein wie in Hauswacht. Das **Aufschließen** besser
nicht automatisch an das Unscharfschalten koppeln: Wer fälschlich unscharf schaltet, hätte sonst
zusätzlich die Tür geöffnet.

**Bei Alarm: alle Lichter an und eine zusätzliche Nachricht** – Hauswacht schaltet selbst nur
Sirenen; alles andere erledigt eine eigene Automation:

```yaml
alias: Bei Einbruchalarm Licht an
triggers:
  - trigger: state
    entity_id: alarm_control_panel.hauswacht
    attribute: phase
    to: triggered
conditions:
  # im Testmodus nichts schalten
  - condition: state
    entity_id: alarm_control_panel.hauswacht
    attribute: test_mode
    state: false
actions:
  - action: light.turn_on
    target:
      area_id: [wohnzimmer, flur, kueche]
  - action: notify.telegram_familie
    data:
      message: >
        Einbruchalarm ({{ state_attr('alarm_control_panel.hauswacht', 'profile_name') }})!
```

Lichter, Bereiche und den Benachrichtigungsdienst an deine anpassen. Später kämen hier z. B.
Kamera-Schnappschüsse dazu. `triggered` gilt für die Reaktionsphase; ist sie vorbei, wechselt
`phase` auf `alarm_hold` (Alarm noch nicht quittiert).

## Aktionen

| Aktion | Felder | Zweck |
|---|---|---|
| `hauswacht.arm` | `profile`, `confirm`, `code` | Profil scharf schalten, optional mit Bestätigung offener Melder |
| `hauswacht.guest_mode` | `on`, `until` | [Gastmodus](profile.md#gastmodus) ein/aus, optional mit Ende; Ziel ein Bereich oder „Alle“ |
| `hauswacht.simulate_trigger` | `sensor` | Testmodus: Melder kurz auslösen |
| `hauswacht.simulate_state` | `sensor`, `state` (`on`, `off`, `unavailable`, `real`) | Testmodus: Melderzustand simulieren |
| `hauswacht.simulate_reset` | – | Testmodus: alle Simulationen zurück |
| `hauswacht.siren_test` | `siren`, `duration`, `volume`, `tone` | Echte Sirene kurz testen (nur Administratoren) |
| `hauswacht.siren_test_result` | `siren`, `heard` | Ergebnis eines Sirenentests speichern (nur Administratoren) |
| `hauswacht.siren_test_stop` | – | Laufenden Sirenentest abbrechen (nur Administratoren) |
| `hauswacht.reset_code_lock` | – | Falsche Eingaben und Sperre zurücksetzen (nur Administratoren) |

Für Karten gibt es zusätzlich WebSocket-Befehle:

| Befehl | Zweck |
|---|---|
| `hauswacht/overview` | [Anlagenübersicht](uebersicht.md) samt Prüfhinweisen (nur Administratoren) |
| `hauswacht/homecoming/report` | Heimkehr-Bericht zum Herunterladen: `filename`, `markdown`, `csv` (nur Administratoren) |
| `hauswacht/alarm/info` | [Alarmkarte](dashboard.md#karte-hauswacht-alarm): Bereiche, Profile, PIN-Bedarf und Rechte des angemeldeten Kontos |
| `hauswacht/alarm/action` | Alarmkarte: `area`, `action` (`arm`, `disarm`, `end_alarm`), `profile`, `code`, `force`; Antwort `ok` bzw. `error`, `message`, `can_force` |

Alle Aktionen richten sich an ein Bedienfeld (`target: entity_id: alarm_control_panel.hauswacht`).
Unscharf schalten geht mit der Standardaktion `alarm_control_panel.alarm_disarm`.

## Ereignisse

Hauswacht meldet Vorgänge als Ereignis **`hauswacht_event`**. Das Feld `type` nennt die Art,
z. B.:

| `type` | Wann |
|---|---|
| `StateChanged` | Zustand des Bedienfelds geändert |
| `ActivateReaction`, `StopReaction` | Alarmreaktion beginnt bzw. endet |
| `ArmingAborted` | Scharfschalten abgebrochen |
| `SensorsBypassed` | Melder überbrückt |
| `TamperDetected` | Manipulation |
| `SensorUnavailable` | Überwachter Melder ausgefallen |
| `InfrastructureFault`, `InfrastructureRecovered` | Funknetz/Gateway ausgefallen bzw. wieder da |
| `RestartedDisarmed` | Nach einem Neustart unscharf (Einstellung „immer unscharf“, oder Profil gelöscht) |
| `RestoredAfterRestart` | Nach einem Neustart wiederhergestellt (mit `profile_id`, `entry_delay`, `alarm_was_active`) |
| `AlwaysActiveTriggered` | Immer aktiver Melder ausgelöst |
| `ArmedByClosingDoor` | Scharf durch Schließen der Tür |
| `AutoArmScheduled`, `AutoArmCancelled`, `AutoArmed`, `AutoArmSkipped`, `AutoArmFailed` | Profil-Automatik: Scharfschalten geplant, abgebrochen, erfolgt, übersprungen, fehlgeschlagen (mit `profile_id`, `reason`) |
| `AutoDisarmed`, `AutoDisarmSkipped` | Profil-Automatik: unscharf geschaltet bzw. nicht (z. B. Alarm läuft) |
| `ButtonPressed` | Taster gedrückt (mit `control`, `press`, `profile`) |
| `LockIdentified`, `LockIgnored` | Türschloss: Kennung empfangen (mit `intent`, `identity`, `reason`) bzw. nicht verwendet (z. B. `unknown_id`, `disabled_id` = deaktivierte Kennung) |
| `ArrivalNoted`, `DoorNoted` | „Unscharf mit Türbeleg“: Rückkehr (mit `persons`) bzw. Eingangstür (mit `door`) erkannt, während das Profil scharf ist |
| `RuleStep`, `RuleFired`, `RuleExpired`, `RuleConditionsNotMet`, `OpenRuleSensors` | Auslöseregeln |
| `InvalidCode`, `CodeLockReset` | Falsche Eingabe (mit `failures`, `lock_seconds`), Zähler zurückgesetzt |
| `Panic`, `Emergency` | Notruf-Taste am Keypad |
| `GuestMode` | Gastmodus ein/aus (mit `area`, `on`, `until`, `by`) |
| `ActionCode` | Aktions-Code eingegeben (mit `name`, `action`, `control`, `test`) |
| `SirenDecision`, `SirenTest` | Sirenenentscheidung (`action`: `activate`, `stop`, `stop_restored` = nach Neustart ausschalten), Schritte eines Sirenentests |
| `SensorSimulated` | Testmodus: Melder simuliert |
| `NotificationSuppressed`, `SpeechSuppressed` | Benachrichtigung bzw. Ansage unterdrückt (z. B. Testmodus, Nachtruhe) |

Beispiel-Auslöser für eine eigene Automation:

```yaml
triggers:
  - trigger: event
    event_type: hauswacht_event
    event_data:
      type: TamperDetected
```
