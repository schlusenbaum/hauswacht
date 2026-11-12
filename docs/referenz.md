# Referenz

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

### Zustand und Diagnose

| Entität | Zweck |
|---|---|
| `binary_sensor.hauswacht_offene_sensoren` | „Offen“, sobald ein Melder einer Meldergruppe offen ist; Attribute `sensors`, `names` |
| `sensor.hauswacht_systemstatus` | `ok` · `degraded` (Melder ausgefallen) · `fault` (Störung); Attribute `faulty_infrastructure`, `unavailable_sensors` |
| `sensor.hauswacht_letzter_sirenentest` | Letzter Sirenentest; je Sirene Datum und „gehört?“ in den Attributen |
| `sensor.hauswacht_funkstille_beobachtung` | Empfehlung für die maximale Funkstille, längste Pausen je Melder |
| `sensor.hauswacht_heimkehr_beobachtung` | Anzahl ausgewerteter Heimkehrten; Attribute `sources`, `recent`, `entry_times` |
| `button.hauswacht_heimkehr_bericht` | Bericht der Heimkehr-Beobachtung als Meldung in Home Assistant |
| `sensor.hauswacht_simulierte_sensoren` | Grundlage der Testkarte (ausgeblendet) |

### Profil-Einstellungen (Kategorie Konfiguration)

| Entität | Zweck |
|---|---|
| `select.hauswacht_profil_bearbeiten` | Welches Profil die folgenden Entitäten zeigen und ändern |
| `number.hauswacht_ausgangsverzogerung`, `number.hauswacht_eingangsverzogerung` | Verzögerungen |
| `number.hauswacht_dauer_der_alarmreaktion`, `number.hauswacht_alarmzyklen` | Alarmreaktion |
| `number.hauswacht_wartezeit_bei_abwesenheit` | Automatik |
| `select.hauswacht_offene_sensoren_beim_scharfschalten`, `select.hauswacht_ausgefallene_sensoren_beim_scharfschalten` | Verhalten beim Scharfschalten |
| `select.hauswacht_sirenenton`, `select.hauswacht_sirenenlautstarke` | Sirene |
| `switch.hauswacht_stiller_alarm`, `switch.hauswacht_sabotage_lost_alarm_aus`, `switch.hauswacht_unscharf_beim_heimkommen` | Schalter |
| `time.hauswacht_automatisch_scharf_um`, `time.hauswacht_automatisch_unscharf_um` | Uhrzeiten |

## Attribute des Bedienfelds

| Attribut | Bedeutung |
|---|---|
| `area`, `area_name` | Bereich |
| `profile`, `profile_name` | Aktives Profil (Kennung, Name) |
| `phase` | Interner Zustand |
| `changed_by` | Wer zuletzt geschaltet hat, z. B. „Anna (Keypad Flur)“ |
| `test_mode` | Testmodus aktiv |
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

## Aktionen

| Aktion | Felder | Zweck |
|---|---|---|
| `hauswacht.arm` | `profile`, `confirm`, `code` | Profil scharf schalten, optional mit Bestätigung offener Melder |
| `hauswacht.simulate_trigger` | `sensor` | Testmodus: Melder kurz auslösen |
| `hauswacht.simulate_state` | `sensor`, `state` (`on`, `off`, `unavailable`, `real`) | Testmodus: Melderzustand simulieren |
| `hauswacht.simulate_reset` | – | Testmodus: alle Simulationen zurück |
| `hauswacht.siren_test` | `siren`, `duration`, `volume`, `tone` | Echte Sirene kurz testen (nur Administratoren) |
| `hauswacht.siren_test_result` | `siren`, `heard` | Ergebnis eines Sirenentests speichern (nur Administratoren) |
| `hauswacht.siren_test_stop` | – | Laufenden Sirenentest abbrechen (nur Administratoren) |
| `hauswacht.reset_code_lock` | – | Falsche Eingaben und Sperre zurücksetzen (nur Administratoren) |

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
| `RestartedDisarmed` | Nach einem Neustart unscharf |
| `AlwaysActiveTriggered` | Immer aktiver Melder ausgelöst |
| `ArmedByClosingDoor` | Scharf durch Schließen der Tür |
| `RuleStep`, `RuleFired`, `RuleExpired`, `RuleConditionsNotMet`, `OpenRuleSensors` | Auslöseregeln |
| `InvalidCode`, `CodeLockReset` | Falsche Eingabe (mit `failures`, `lock_seconds`), Zähler zurückgesetzt |
| `Panic`, `Emergency` | Notruf-Taste am Keypad |
| `SirenDecision`, `SirenTest` | Sirenenentscheidung, Schritte eines Sirenentests |
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
