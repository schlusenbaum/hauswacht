# Referenz

**Deutsch** | [English](en/reference.md)

Alles, was Hauswacht für eigene Automationen, Skripte und Karten bereitstellt: **Entitäten**,
**Attribute des Bedienfelds**, **Ereignisse** und **Aktionen**. Wer erst wissen will, *was er
wofür nimmt*, beginnt beim Spickzettel **[Automationen: was nehme ich wofür?](automationen.md)**;
fertige Automationen stehen unter **[Beispiele](beispiele.md)**.

> **Entitäts-IDs** hängen von der Sprache ab, in der Home Assistant beim Einrichten von Hauswacht
> lief – deshalb stehen hier beide. Für **weitere Bereiche** kommt der Bereichsname hinter
> „hauswacht“, z. B. `alarm_control_panel.hauswacht_garage`. Wer eine Entität umbenannt hat oder
> sie bei einer älteren Version anders hieß: Maßgeblich ist, was unter Einstellungen → Geräte &
> Dienste → Entitäten steht.

## Entitäten

„Je Bereich“ = gibt es für jeden [Bereich](profile.md#bereiche) einmal, sonst einmal für die
ganze Anlage.

### Bedienung

| Entität (Deutsch) | Entität (Englisch) | Je Bereich | Zweck |
|---|---|---|---|
| `alarm_control_panel.hauswacht` | `alarm_control_panel.hauswacht` | ja | Bedienfeld: Knöpfe der Profile mit Bedienfeld-Knopf, Unscharf. Zustände `disarmed`, `arming`, `armed_home`/`armed_away`/`armed_night`/`armed_vacation`/`armed_custom_bypass` (je nach Knopf des Profils), `pending`, `triggered`. Attribute siehe [unten](#attribute-des-bedienfelds) |
| `alarm_control_panel.hauswacht_alle` | `alarm_control_panel.hauswacht_all` | – | Nur mit mehreren Bereichen: „Alle Bereiche“; Attribute `areas` (Zustand und Profil je Bereich), `test_mode` |
| `select.hauswacht_profil` | `select.hauswacht_profile` | ja | Profil für die Knöpfe „Scharf schalten“; scharf: das aktive Profil |
| `button.hauswacht_scharf_schalten` | `button.hauswacht_arm` | ja | Gewähltes Profil scharf schalten |
| `button.hauswacht_trotzdem_scharf_schalten` | `button.hauswacht_arm_anyway` | ja | Gewähltes Profil scharf schalten, offene Melder überbrücken |
| `button.hauswacht_unscharf_schalten` | `button.hauswacht_disarm_now` | ja | Sofort unscharf, auch während eines Alarms |
| `button.hauswacht_alarm_beenden` | `button.hauswacht_end_alarm` | ja | Nur den Alarm beenden, Profil bleibt scharf |
| `switch.hauswacht_testmodus` | `switch.hauswacht_test_mode` | – | [Testmodus](testmodus.md) |
| `switch.hauswacht_gastmodus` | `switch.hauswacht_guest_mode` | – | [Gastmodus](profile.md#gastmodus) für alle Bereiche; Attribut `areas` mit Ende je Bereich |
| `event.hauswacht_aktions_code` | `event.hauswacht_action_code` | – | Nur mit [Aktions-Codes](bedienteile.md#aktions-codes) der Aktion „Ereignis“: Ereignistyp = Name des Codes; Attribute `keypad`, `test` |
| `sensor.hauswacht_<keypad>_anzeige` | `sensor.hauswacht_<keypad>_display` | – | Je [allgemeinem Keypad](bedienteile.md#keypad-allgemein): was das Keypad zeigen soll – `disarmed`, `exit_delay`, `armed_home`/`armed_away`/`armed_night`/`armed_vacation`/`armed_custom_bypass`, `entry_delay`, `triggered`, `test_alarm`, `fire`. Attribute `keypad`, `area`, `profile`, `delay_ends`, `delay_seconds`, `test_mode`, `changed_by`, `buttons`, `last_result`, `last_result_at` |

### Zustand und Diagnose

| Entität (Deutsch) | Entität (Englisch) | Je Bereich | Zweck |
|---|---|---|---|
| `binary_sensor.hauswacht_offene_sensoren` | `binary_sensor.hauswacht_open_sensors` | ja | `on`, sobald ein Melder einer Meldergruppe offen ist; Attribute `sensors` (IDs), `names`, `tilted` (gerade gekippt) |
| `sensor.hauswacht_systemstatus` | `sensor.hauswacht_system_status` | – | `ok` · `degraded` (Melder ausgefallen) · `fault` (Funknetz/Gateway gestört); Attribute `faulty_infrastructure`, `unavailable_sensors` |
| `sensor.hauswacht_letzter_sirenentest` | `sensor.hauswacht_last_siren_test` | – | Letzter Sirenentest; je Sirene Datum und „gehört?“ in den Attributen |
| `sensor.hauswacht_funkstille_beobachtung` | `sensor.hauswacht_radio_silence_observation` | – | [Beobachtung](beobachtung.md): Empfehlung für die maximale Funkstille, längste Pausen je Melder |
| `sensor.hauswacht_heimkehr_beobachtung` | `sensor.hauswacht_homecoming_observation` | – | [Beobachtung](beobachtung.md): Anzahl ausgewerteter Heimkehrten; Attribute `sources`, `recent`, `entry_times`, `door_proof` |
| `button.hauswacht_heimkehr_bericht` | `button.hauswacht_homecoming_report` | – | Bericht der Heimkehr-Beobachtung als Meldung in Home Assistant |
| `sensor.hauswacht_simulierte_sensoren` | `sensor.hauswacht_simulated_sensors` | – | Grundlage der Testkarte (ausgeblendet) |

### Profil-Einstellungen (Kategorie Konfiguration)

Diese Entitäten zeigen und ändern die Einstellungen **des Profils, das in
`select.hauswacht_profil_bearbeiten` gewählt ist** – praktisch für die Karte „Hauswacht
Einstellungen“, für Automationen selten nötig.

| Entität (Deutsch) | Entität (Englisch) | Zweck |
|---|---|---|
| `select.hauswacht_profil_bearbeiten` | `select.hauswacht_edit_profile` | Welches Profil die folgenden Entitäten zeigen |
| `number.hauswacht_ausgangsverzogerung` | `number.hauswacht_exit_delay` | Ausgangsverzögerung (s) |
| `number.hauswacht_eingangsverzogerung` | `number.hauswacht_entry_delay` | Eingangsverzögerung (s) |
| `number.hauswacht_dauer_der_alarmreaktion` | `number.hauswacht_alarm_reaction_time` | Dauer der Alarmreaktion (s) |
| `number.hauswacht_alarmzyklen` | `number.hauswacht_alarm_cycles` | Höchstzahl Alarmzyklen |
| `number.hauswacht_wartezeit_bei_abwesenheit` | `number.hauswacht_away_delay` | Automatik: Wartezeit, wenn alle weg sind |
| `number.hauswacht_turbeleg_ortung_vor_der_tur` | `number.hauswacht_door_proof_location_before_door` | [Bei Rückkehr](profile.md#bei-rückkehr): Zeitfenster Handy und Tür (seit 0.61 heißt die Entität „Bei Rückkehr: Zeitfenster Handy und Tür“; bei bestehenden Installationen bleibt die ID) |
| `select.hauswacht_unscharf_bei_ruckkehr` | `select.hauswacht_disarm_on_arrival` | [Bei Rückkehr](profile.md#bei-rückkehr): Nichts, Unscharf nur wenn automatisch scharf, Unscharf mit Türbeleg, Unscharf auch nach Scharfschalten von Hand, Reinlassen (seit 0.61 heißt die Entität „Bei Rückkehr“; bei bestehenden Installationen bleibt die ID) |
| `select.hauswacht_offene_sensoren_beim_scharfschalten` | `select.hauswacht_open_sensors_when_arming` | Verhalten bei offenen Meldern |
| `select.hauswacht_ausgefallene_sensoren_beim_scharfschalten` | `select.hauswacht_unavailable_sensors_when_arming` | Verhalten bei ausgefallenen Meldern |
| `select.hauswacht_sirenenton` | `select.hauswacht_siren_tone` | Sirenenton |
| `select.hauswacht_sirenenlautstarke` | `select.hauswacht_siren_volume` | Sirenenlautstärke |
| `switch.hauswacht_stiller_alarm` | `switch.hauswacht_silent_alarm` | Stiller Alarm |
| `switch.hauswacht_sabotage_lost_alarm_aus` | `switch.hauswacht_tamper_triggers_alarm` | Sabotage löst Alarm aus |
| `switch.hauswacht_gekippte_fenster_erlaubt` | `switch.hauswacht_tilted_windows_allowed` | Gekippte Fenster erlaubt – nur, wenn es [Melder mit Kippstellung](melder.md#melder-mit-kippstellung-gekippt) gibt |
| `time.hauswacht_automatisch_scharf_um` | `time.hauswacht_arm_automatically_at` | Automatik: scharf um |
| `time.hauswacht_automatisch_unscharf_um` | `time.hauswacht_disarm_automatically_at` | Automatik: unscharf um |

## Attribute des Bedienfelds

Das Bedienfeld (`alarm_control_panel.hauswacht`, je Bereich) trägt den ganzen Zustand der Anlage
in seinen Attributen. Für Automationen ist **`phase`** der wichtigste Auslöser.

| Attribut | Bedeutung | Beispielwert |
|---|---|---|
| `phase` | Zustand unabhängig vom Profil: `disarmed` (unscharf), `arming` (Ausgangsverzögerung), `armed` (scharf), `pending` (Eingangsverzögerung), `triggered` (**Alarm**, Reaktion läuft), `alarm_hold` (Alarm vorbei, noch nicht quittiert) | `armed` |
| `profile`, `profile_name` | Aktives Profil (Kennung, Name); unscharf: leer | `night`, `Nacht` |
| `area`, `area_name` | Bereich | `main`, `Haus` |
| `changed_by` | Wer zuletzt geschaltet hat (Benutzer und Weg) | `Anna (Keypad Flur)` |
| `test_mode` | Testmodus an | `false` |
| `guest_mode`, `guest_until` | Gastmodus an, Ende (leer = bis zum Ausschalten) | `true`, `2026-11-20T18:00:00+01:00` |
| `timer`, `timer_ends_at` | Laufende Zeit (`exit_delay`, `entry_delay`, `reaction`) und ihr Ende | `entry_delay`, `…T22:31:05+01:00` |
| `trigger_sensor` | Melder, der den Alarm (bzw. die Eingangsverzögerung) ausgelöst hat | `binary_sensor.haustuer` |
| `alarm_cycles` | Wie oft in diesem Alarm schon ausgelöst wurde | `1` |
| `monitored_sensors` | Gerade scharf überwachte Melder | `[…]` |
| `open_sensors`, `unavailable_sensors` | Offene bzw. ausgefallene Melder aller Meldergruppen | `["binary_sensor.fenster_bad"]` |
| `tilted_sensors` | Gerade gekippte [Melder mit Kippstellung](melder.md#melder-mit-kippstellung-gekippt). Erlaubt das Profil gekippte Fenster, stehen sie nicht in `open_sensors` | `["sensor.fenster_schlafzimmer_opening_state"]` |
| `open_rule_sensors` | Offene Melder, die im aktiven Profil nur in Auslöseregeln vorkommen | `[]` |
| `bypassed_sensors`, `bypassed_until_closed` | Überbrückte Melder (bis unscharf bzw. bis zum Schließen) | `[]` |
| `passage` | Laufender [Durchgang](durchgang.md): `direction` (`in` reinkommen, `out` rausgehen), `until` (Ende beim Rausgehen), `by`, `doors` (benutzte Türen), `doors_allowed` (beim Rausgehen noch erlaubte Türen), `sensors` (gerade vom Durchgang überbrückt); sonst leer | `{"direction": "out", "until": "…", …}` |
| `zones` | Meldergruppen mit ihren tatsächlichen Meldern | `{"Außen": […]}` |
| `last_contact` | Letzter Kontakt je Melder | `{…}` |
| `sirens_hardware_enabled` | Echte Sirenenansteuerung freigegeben | `true` |
| `last_siren_decision` | Letzte Sirenenentscheidung (wie Ereignis [`SirenDecision`](#sirenen)) | `{"action": "activate", …}` |
| `code_failures`, `code_locked_until` | Falsche Eingaben, Ende einer laufenden Sperre | `2`, `null` |

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
zusätzlich die Tür geöffnet. Viele weitere fertige Automationen – Licht bei Alarm, Kamerabild aufs
Handy, Rollläden, Statuslicht, Heizung bei Abwesenheit – stehen unter [Beispiele](beispiele.md).

## Ereignisse

Hauswacht meldet Vorgänge als Home-Assistant-Ereignis **`hauswacht_event`**. Das Feld **`type`**
nennt die Art, die übrigen Felder stehen in den Tabellen unten.

```yaml
triggers:
  - trigger: event
    event_type: hauswacht_event
    event_data:
      type: TamperDetected
actions:
  - action: notify.mobile_app_annas_handy
    data:
      message: "Sabotage an {{ trigger.event.data.sensor_key }}"
```

Gut zu wissen:

- **Selbst ansehen:** Entwicklerwerkzeuge → Ereignisse → bei „Ereignis abonnieren“
  `hauswacht_event` eintragen → „Zuhören starten“ – dann zeigt jede Aktion an der Anlage ihr
  Ereignis mit allen Feldern.
- **Testmodus:** Alle Ereignisse kommen **auch im Testmodus**. Ob er an ist, steht im Attribut
  `test_mode` des Bedienfelds; einige Ereignisse haben dafür ein eigenes Feld (`test_mode`,
  `test`). Eigene Alarm-Automationen deshalb immer mit der Bedingung `test_mode: false`.
- **Bereich:** **Jedes** Ereignis nennt seinen Bereich: `area` (Kennung, `main` = Hauptbereich,
  `all` = ganze Anlage, z. B. Funknetz, Sirenentest oder ein Bedienteil für alle Bereiche) und
  `area_name` (Anzeigename, z. B. „Garage“). So reagiert eine Automation nur auf einen Bereich:

  ```yaml
  triggers:
    - trigger: event
      event_type: hauswacht_event
      event_data:
        type: TamperDetected
        area: garage
  ```

  Bei Bedienteilen (Keypad, Taster, Türschloss, Notruf-Taste) ist `area` der Bereich des
  **Bedienteils** – ein Bedienteil „für alle Bereiche“ meldet `all`.
- **Melder** stehen als Entitäts-ID in `sensor_key` bzw. als Liste in `sensors`,
  `open_sensors` …; den Anzeigenamen liefert `state_attr(…, 'friendly_name')`.
- Mengen (z. B. `open_sensors`) kommen als **Liste**.
- **Melder mit Kippstellung:** Ereignisse mit `sensor_key` haben bei diesen Meldern zusätzlich
  `position` – `open`, `tilted` oder `closed` (siehe
  [Melder mit Kippstellung](melder.md#melder-mit-kippstellung-gekippt)).

### Zustand und Alarm

*Dazu in jedem Ereignis: `area`, `area_name` (siehe [oben](#ereignisse)).*

| `type` | Wann | Felder |
|---|---|---|
| `StateChanged` | Zustand des Bedienfelds hat gewechselt | `old`, `new` (Werte wie `phase`), `cause` (Grund, siehe unten) |
| `ActivateReaction` | **Alarm beginnt** (bzw. nächster Alarmzyklus) | `profile_id`, `cycle` (1, 2, …), `sensor_key` (Auslöser), `test_mode` |
| `StopReaction` | Alarmreaktion endet (Zeit abgelaufen, unscharf oder Alarm beendet) | `profile_id`, `test_mode` |
| `AlarmAcknowledged` | Alarm mit „Alarm beenden“ quittiert, Profil bleibt scharf | `profile_id`, `bypassed_until_closed` (noch offene Melder, überbrückt bis zum Schließen) |
| `Rejected` | Schalten abgelehnt | `reason` (`not_ready` = offene/ausgefallene Melder, `not_disarmed` = schon scharf, `invalid_code`, `test_mode_change_requires_disarmed`), `open_sensors`, `unavailable_sensors` |
| `ConfirmationRequired` | Scharfschalten braucht Bestätigung („trotzdem scharf“) | `open_sensors`, `unavailable_sensors` |
| `SensorsBypassed` | Melder überbrückt (z. B. „trotzdem scharf“) | `sensors` |
| `SensorsRestored` | Überbrückte Melder wieder zu, werden wieder überwacht | `sensors` |
| `ArmingAborted` | Scharfschalten am Ende der Ausgangsverzögerung abgebrochen (noch offen/ausgefallen) | `open_sensors`, `unavailable_sensors` |
| `TamperDetected` | Sabotage gemeldet | `sensor_key`, `state` (Zustand der Anlage in dem Moment) |
| `VibrationCounted` | [Erschütterung](melder.md#erschütterungsmelder) gezählt, reicht aber noch nicht für einen Alarm (Fehlalarmschutz) | `sensor_key`, `count` (bisher im Zeitfenster), `needed` (nötig), `window` (Sekunden) |
| `AlwaysActiveTriggered` | [Immer aktiver](melder.md#immer-aktive-melder) Melder ausgelöst | `sensor_key` |
| `ArmedByClosingDoor` | [Scharf durch Schließen der Tür](profile.md#scharf-durch-schließen-der-tür) | – |
| `PassageGranted` | [Durchgang](durchgang.md) begonnen, Anlage bleibt scharf | `direction` (`in`/`out`), `door` (beim Reinkommen die geöffnete Tür), `path` (frei gewordene Wegmelder), `by` |
| `PassageDoorUsed` | Rausgehen: diese Tür ist jetzt die Durchgangstür | `door` |
| `PassageEnded` | Durchgang (oder sein Weg) vorbei, Melder werden wieder überwacht | `restored` (wieder überwacht), `still_open` (noch offen – frei, bis sie zu sind) |
| `PassageDoorOpen` | Tür nach dem Durchgang noch offen – wird nicht überwacht, bis sie zu ist | `doors` |
| `TestModeChanged` | Testmodus ein/aus | `enabled` |

**Gründe (`cause`) in `StateChanged`:** `arm_requested` (scharf geschaltet), `exit_delay_elapsed`
(Ausgangsverzögerung vorbei), `disarm_requested` (unscharf geschaltet), `entry_sensor`
(Eingangstür → Eingangsverzögerung), `entry_delay_elapsed`, `instant_sensor`, `follower_sensor`,
`tamper_24h_sensor`, `tamper`, `instant_during_entry_delay`, `retrigger` (erneut ausgelöst),
`always_active`, `reaction_time_elapsed` (→ `alarm_hold`), `alarm_acknowledged`,
`exit_check_failed` (Scharfschalten abgebrochen), `always_alarm_ended`, `restored` (nach
Neustart), `startup`, `passage` (Eingangsverzögerung durch einen [Durchgang](durchgang.md)
beendet, bleibt scharf).

### Neustart

*Dazu in jedem Ereignis: `area`, `area_name` (siehe [oben](#ereignisse)).*

| `type` | Wann | Felder |
|---|---|---|
| `RestoredAfterRestart` | Nach einem Neustart wiederhergestellt | `profile_id`, `entry_delay`, `alarm_was_active` |
| `RestartedDisarmed` | Nach einem Neustart unscharf (Einstellung „immer unscharf“ oder Profil gelöscht) | `previous_profile_id` |

### Profil-Automatik und Anwesenheit

*Dazu in jedem Ereignis: `area`, `area_name` (siehe [oben](#ereignisse)).*

`reason` nennt den Anlass: `Uhrzeit`, `Zeitplan`, `alle weg`, `Rückkehr`, `Rückkehr mit
Türbeleg`, `Neustart`.

| `type` | Wann | Felder |
|---|---|---|
| `AutoArmScheduled` | Alle weg – Scharfschalten nach Wartezeit geplant | `profile_id`, `minutes` |
| `AutoArmCancelled` | Geplantes Scharfschalten abgebrochen (jemand zurück) | `profile_id` |
| `AutoArmed` | Automatisch scharf geschaltet | `profile_id`, `reason` |
| `AutoArmSkipped` | Nicht scharf geschaltet (nicht unscharf, Gastmodus …) | `profile_id`, `reason`, ggf. `guest_mode: true` |
| `AutoArmFailed` | Scharfschalten gescheitert (z. B. offene Fenster) | `profile_id`, `reason`, `details` |
| `AutoDisarmed` | Automatisch unscharf | `profile_id`, `reason` |
| `AutoDisarmSkipped` | Nicht unscharf (z. B. Alarm läuft, anderes Profil scharf) | `profile_id`, `reason` |
| `ArrivalNoted` | „Unscharf mit Türbeleg“: Rückkehr erkannt, Profil scharf | `profile_id`, `persons` |
| `PhoneArrivalNoted` | [Bei Rückkehr: Reinlassen](durchgang.md#reinlassen-per-handy): Heimkehr erkannt (vorher mindestens 5 Minuten weg), Profil scharf | `profile_id`, `persons` |
| `DoorNoted` | „Unscharf mit Türbeleg“: Eingangstür erkannt | `profile_id`, `door` |
| `EntryDelayExtended` | [Annäherung](profile.md#annäherung-verlängert-die-eingangsverzögerung): Eingangsverzögerung verlängert, weil sich eine Person aus „Bei Rückkehr“ genähert hat | `profile_id`, `seconds`, `normal`, `persons` |

### Bedienung

*Dazu in jedem Ereignis: `area`, `area_name` (siehe [oben](#ereignisse)).*

| `type` | Wann | Felder |
|---|---|---|
| `InvalidCode` | Falscher PIN bzw. unbekannte Karte | `failures` (Zahl in Folge), `lock_seconds` (Sperre, 0 = keine) |
| `CodeLockReset` | Falsche Eingaben zurückgesetzt | `by`, `failures` |
| `MqttRetainedCommand` | Ein gespeicherter Befehl (retain) an eine [MQTT-Schnittstelle](bedienteile.md#mqtt-schnittstelle) wurde ignoriert | `control` |
| `UnknownKeypad` | Ein [allgemeines Keypad](bedienteile.md#keypad-allgemein), das in Hauswacht nicht angelegt ist, hat sich gemeldet | `keypad` (gesendete Kennung) |
| `ActionCode` | [Aktions-Code](bedienteile.md#aktions-codes) eingegeben | `name`, `action` (`event`, `arm`, `silent_emergency`), `control` (Keypad), `test` |
| `ButtonPressed` | [Taster](bedienteile.md#taster) gedrückt | `control`, `press` (`single`, `double`, `long`), `profile` (leer = Druckart nicht belegt) |
| `LockIdentified` | [Türschloss](bedienteile.md#türschloss-z-b-nuki): Kennung empfangen | `control`, `intent` (`UNLOCK`, `LOCK` oder leer), `identity`, `reason` (`ok`, `not_by_person`, `no_id`) |
| `LockIgnored` | Türschloss: Kennung nicht verwendet | `control`, `intent`, `reason` (`unknown_id`, `disabled_id`) |
| `GuestMode` | [Gastmodus](profile.md#gastmodus) ein/aus | `on`, `until` (leer = bis zum Ausschalten), `by` |
| `Panic` | Notruf-Taste mit Alarm | `control` |
| `Emergency` | Notruf-Taste gedrückt (vor der Reaktion) | `control`, `mode` (`off`, `silent`, `alarm`) |

### Störungen

*Dazu in jedem Ereignis: `area`, `area_name` (siehe [oben](#ereignisse)).*

| `type` | Wann | Felder |
|---|---|---|
| `SensorUnavailable` | Überwachter Melder ausgefallen | `sensor_key` |
| `InfrastructureFault` | Funknetz oder Gateway gestört | `indicator` (Entität, die das meldet), `armed` |
| `InfrastructureRecovered` | … wieder in Ordnung | `indicator`, `armed` |

### Auslöseregeln

*Dazu in jedem Ereignis: `area`, `area_name` (siehe [oben](#ereignisse)).*

| `type` | Wann | Felder |
|---|---|---|
| `RuleStep` | Schritt einer [Auslöseregel](ausloeseregeln.md) erfüllt | `sensor_key` |
| `RuleFired` | Regel vollständig erfüllt | `rule`, `name`, `sensor_key` |
| `RuleExpired` | Regel nur teilweise erfüllt, Zeit abgelaufen | `rule`, `sensor_key` (erster Melder) |
| `RuleConditionsNotMet` | Regel erfüllt, aber Bedingungen nicht – kein Alarm | `rule`, `sensor_key` |
| `ArmedWithGaps` | Scharf, aber nicht alles überwacht (siehe [Hinweis beim Scharfschalten](benachrichtigungen.md)) | `bypassed` (überbrückt, weil offen), `unavailable` (ausgefallen, in Kauf genommen), `rule_sensors` (offen, nur in Regeln) |
| `OpenRuleSensors` | Beim Scharfschalten offene Melder, die nur in Regeln vorkommen | `sensors` |

### Sirenen

*Dazu in jedem Ereignis: `area`, `area_name` (siehe [oben](#ereignisse)).*

| `type` | Wann | Felder |
|---|---|---|
| `SirenDecision` | Hauswacht hat über Sirenen entschieden | `action` (`activate`, `stop`, `stop_restored` = nach Neustart aus), `sent` (angesteuerte Sirenen), `blocked` (Sirene → Grund: `test_mode`, `hardware_disabled`, `fire_lock`, `unknown_device`, `not_allowed_for_burglar`, `no_burglar_tone`, …) |
| `SirenTest` | Schritt eines [Sirenentests](sirenen.md) | `step` (`started`, `stopped`, `blocked`, `result`), `siren`, je nach Schritt `by`, `seconds`, `volume`, `reason`, `heard` |

### Für die Fehlersuche

*Dazu in jedem Ereignis: `area`, `area_name` (siehe [oben](#ereignisse)).*

Diese Ereignisse zeigen Abläufe im Inneren. Als Auslöser für Automationen taugen sie selten.

| `type` | Wann | Felder |
|---|---|---|
| `SensorSimulated` | Testmodus: Melder simuliert | `sensor_key`, `state` |
| `NotificationSuppressed` | Benachrichtigung unterdrückt (z. B. Testmodus) | `targets`, `title` |
| `SpeechSuppressed` | Ansage unterdrückt (z. B. Testmodus) | `event`, `entities` |
| `StartTimer` | Verzögerung gestartet | `kind` (`exit_delay`, `entry_delay`, `reaction`), `token`, `seconds` |
| `CancelTimer` | Verzögerung abgebrochen | `token` |
| `Ignored` | Eingabe ohne Wirkung | `reason` (z. B. `already_disarmed`, `exit_delay`, `stale_timer`) |

## Aktionen

Alle Aktionen richten sich an ein Bedienfeld (`target: entity_id: alarm_control_panel.hauswacht`).

| Aktion | Felder | Zweck |
|---|---|---|
| `hauswacht.arm` | `profile` (Name oder Kennung), `confirm` (offene Melder bestätigen), `code` | Profil scharf schalten |
| `hauswacht.guest_mode` | `on`, `until` (Zeitpunkt, leer = bis zum Ausschalten) | [Gastmodus](profile.md#gastmodus) ein/aus; Ziel ein Bereich oder „Alle“ |
| `hauswacht.passage` | `code` (PIN oder Karte; nötig, wenn PINs eingerichtet sind) | [Durchgang](durchgang.md): in der Eingangsverzögerung reinlassen, sonst rausgehen – bleibt scharf |
| `hauswacht.simulate_trigger` | `sensor` | Testmodus: Melder kurz auslösen |
| `hauswacht.simulate_state` | `sensor`, `state` (`on`, `off`, `tilted` – nur Melder mit Kippstellung, `unavailable`, `real`) | Testmodus: Melderzustand simulieren |
| `hauswacht.simulate_reset` | – | Testmodus: alle Simulationen zurück |
| `hauswacht.siren_test` | `siren`, `duration`, `volume`, `tone` | Echte Sirene kurz testen (nur Administratoren) |
| `hauswacht.siren_test_result` | `siren`, `heard` | Ergebnis eines Sirenentests speichern (nur Administratoren) |
| `hauswacht.siren_test_stop` | – | Laufenden Sirenentest abbrechen (nur Administratoren) |
| `hauswacht.reset_code_lock` | – | Falsche Eingaben und Sperre zurücksetzen (nur Administratoren) |

Ohne Ziel-Entität:

| Aktion | Felder | Zweck |
|---|---|---|
| `hauswacht.keypad_input` | `keypad` (Kennung, Name oder Anzeige-Entität), `button` (`disarm`, `emergency` oder eigene Taste), `code`, `force` | Eingabe eines [allgemeinen Keypads](bedienteile.md#keypad-allgemein); gibt das Ergebnis zurück (`result`, `display`, `open_sensors`, `can_force`, `lock_seconds`). Nur Automationen, Skripte und Administratoren |

Dazu die Standardaktionen des Bedienfelds: `alarm_control_panel.alarm_disarm` (unscharf, mit
`code`, wenn ein PIN verlangt wird) und `alarm_arm_home`/`away`/`night`/`vacation`/
`custom_bypass` (das Profil mit diesem Knopf).

```yaml
action: hauswacht.arm
target:
  entity_id: alarm_control_panel.hauswacht
data:
  profile: Nacht
  confirm: false
```

Für Karten gibt es zusätzlich WebSocket-Befehle:

| Befehl | Zweck |
|---|---|
| `hauswacht/overview` | [Anlagenübersicht](uebersicht.md) samt Prüfhinweisen (nur Administratoren) |
| `hauswacht/homecoming/report` | Heimkehr-Bericht zum Herunterladen: `filename`, `markdown`, `csv` (nur Administratoren) |
| `hauswacht/alarm/info` | [Alarmkarte](dashboard.md#karte-hauswacht-alarm): Bereiche, Profile, PIN-Bedarf und Rechte des angemeldeten Kontos |
| `hauswacht/alarm/action` | Alarmkarte: `area`, `action` (`arm`, `disarm`, `end_alarm`), `profile`, `code`, `force`; Antwort `ok` bzw. `error`, `message`, `can_force` |
| `hauswacht/alarm/guest` | Alarmkarte: Gastmodus `areas`, `on`, `until` |
