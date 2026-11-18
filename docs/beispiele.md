# Beispiele: Hauswacht mit anderen Geräten verbinden

**Deutsch** | [English](en/examples.md)

Hauswacht schaltet selbst nur **Sirenen** und verschickt Nachrichten und Ansagen. Alles andere –
Licht, Kameras, Rollläden, Heizung, Türschloss – erledigen **eigene Automationen**, die auf
Hauswacht reagieren. Diese Seite sammelt fertige Beispiele zum Abschreiben.

So übernimmst du ein Beispiel: Einstellungen → Automationen & Szenen → **Automation erstellen** →
⋮ → **In YAML bearbeiten** → Beispiel einfügen → Entitäten, Bereiche und Dienste an deine
anpassen → Speichern.

## Die Bausteine

| Baustein | Wofür | Beispiel |
|---|---|---|
| Attribut **`phase`** des Bedienfelds | Der einfachste Auslöser: `disarmed` (unscharf), `arming` (Ausgangsverzögerung), `armed` (scharf), `pending` (Eingangsverzögerung), `triggered` (**Alarm läuft**), `alarm_hold` (Alarm vorbei, noch nicht quittiert) | `to: triggered` |
| Attribut **`test_mode`** | Im Testmodus nichts Echtes schalten – **in jede Alarm-Automation** als Bedingung | `state: false` |
| Attribute **`profile_name`**, **`trigger_sensor`**, **`changed_by`** | Welches Profil scharf ist, welcher Melder ausgelöst hat, wer geschaltet hat | in Nachrichten |
| Ereignis **`hauswacht_event`** | Besondere Vorgänge, Feld `type`: z. B. `TamperDetected`, `SensorUnavailable`, `ButtonPressed`, `ActionCode` | siehe [Referenz](referenz.md#ereignisse) |

> **Bedienfeld:** In den Beispielen heißt es `alarm_control_panel.hauswacht`. Mit
> [Bereichen](profile.md#bereiche) hat jeder Bereich sein eigenes Bedienfeld – dann das passende
> eintragen.

## Bei Alarm

### Alle Lichter an – und danach wieder wie vorher

Vor dem Einschalten merkt sich eine Szene, welche Lichter wie an waren. Nach dem Unscharfschalten
stellt sie das wieder her.

```yaml
alias: Hauswacht – bei Alarm Licht an
triggers:
  - trigger: state
    entity_id: alarm_control_panel.hauswacht
    attribute: phase
    to: triggered
conditions:
  - condition: state
    entity_id: alarm_control_panel.hauswacht
    attribute: test_mode
    state: false
actions:
  - action: scene.create
    data:
      scene_id: vor_dem_alarm
      snapshot_entities:
        - light.flur
        - light.wohnzimmer
        - light.garten
  - action: light.turn_on
    target:
      entity_id:
        - light.flur
        - light.wohnzimmer
        - light.garten
    data:
      brightness_pct: 100
```

```yaml
alias: Hauswacht – nach Alarm Licht wie vorher
triggers:
  - trigger: state
    entity_id: alarm_control_panel.hauswacht
    attribute: phase
    from: [triggered, alarm_hold]
    to: disarmed
actions:
  - action: scene.turn_on
    target:
      entity_id: scene.vor_dem_alarm
```

*Tipp:* Statt einzelner Lampen geht auch `area_id: [flur, wohnzimmer]` – dann aber auch in
`snapshot_entities` alle Lampen dieser Räume eintragen.

### Kamera: Schnappschuss aufs Handy

Die Kamera nimmt ein Bild auf, das Handy zeigt es direkt in der Benachrichtigung – mit dem Melder,
der ausgelöst hat.

```yaml
alias: Hauswacht – bei Alarm Kamerabild senden
triggers:
  - trigger: state
    entity_id: alarm_control_panel.hauswacht
    attribute: phase
    to: triggered
conditions:
  - condition: state
    entity_id: alarm_control_panel.hauswacht
    attribute: test_mode
    state: false
actions:
  - action: camera.snapshot
    target:
      entity_id: camera.einfahrt
    data:
      filename: /media/hauswacht/alarm.jpg
  - action: notify.mobile_app_annas_handy
    data:
      title: Einbruchalarm
      message: >
        Ausgelöst: {{ state_attr('alarm_control_panel.hauswacht', 'trigger_sensor') }}
        ({{ state_attr('alarm_control_panel.hauswacht', 'profile_name') }})
      data:
        image: /media/local/hauswacht/alarm.jpg
```

- `/media/hauswacht/…` ist der Ordner, `/media/local/hauswacht/…` derselbe Ordner aus Sicht der
  App.
- Meldet `camera.snapshot` „not allowed“, den Ordner in der `configuration.yaml` unter
  `homeassistant: allowlist_external_dirs:` eintragen.
- **Video statt Bild:** `camera.record` mit `filename: /media/hauswacht/alarm.mp4` und
  `duration: 30` – das dauert 30 Sekunden, also als letzte Aktion.
- Kameras, die nur bei Abwesenheit aufzeichnen sollen, schaltest du über den Bewegungsmodus der
  Kamera-Integration ein – siehe [Heizung und Kamera bei Abwesenheit](#heizung-und-kamera-bei-abwesenheit).

### Rollläden hoch, Musik aus

Hochgefahrene Rollläden machen den Einbrecher von außen sichtbar; laute Musik würde die Sirene
übertönen.

```yaml
alias: Hauswacht – bei Alarm Rollläden hoch, Musik aus
triggers:
  - trigger: state
    entity_id: alarm_control_panel.hauswacht
    attribute: phase
    to: triggered
conditions:
  - condition: state
    entity_id: alarm_control_panel.hauswacht
    attribute: test_mode
    state: false
actions:
  - action: cover.open_cover
    target:
      area_id: [wohnzimmer, kueche]
  - action: media_player.media_stop
    target:
      entity_id: media_player.wohnzimmer
```

### Licht blinken lassen

Viele Lampen (z. B. Hue, Zigbee) können blinken – auffälliger als Dauerlicht.

```yaml
alias: Hauswacht – bei Alarm Außenlicht blinkt
triggers:
  - trigger: state
    entity_id: alarm_control_panel.hauswacht
    attribute: phase
    to: triggered
conditions:
  - condition: state
    entity_id: alarm_control_panel.hauswacht
    attribute: test_mode
    state: false
actions:
  - repeat:
      while:
        - condition: state
          entity_id: alarm_control_panel.hauswacht
          attribute: phase
          state: triggered
      sequence:
        - action: light.toggle
          target:
            entity_id: light.aussen
        - delay: 1
  - action: light.turn_on
    target:
      entity_id: light.aussen
```

Die Schleife endet von selbst, sobald der Alarm vorbei ist; danach bleibt das Licht an.

## Scharf und unscharf

### Statuslicht: rot = scharf, grün = unscharf

Eine Lampe oder LED (z. B. WLED-Streifen im Flur) zeigt den Zustand.

```yaml
alias: Hauswacht – Statuslicht
triggers:
  - trigger: state
    entity_id: alarm_control_panel.hauswacht
    attribute: phase
actions:
  - choose:
      - conditions:
          - condition: state
            entity_id: alarm_control_panel.hauswacht
            attribute: phase
            state: [armed, arming, pending]
        sequence:
          - action: light.turn_on
            target:
              entity_id: light.status_flur
            data:
              color_name: red
              brightness_pct: 30
      - conditions:
          - condition: state
            entity_id: alarm_control_panel.hauswacht
            attribute: phase
            state: [triggered, alarm_hold]
        sequence:
          - action: light.turn_on
            target:
              entity_id: light.status_flur
            data:
              color_name: red
              brightness_pct: 100
              flash: long
    default:
      - action: light.turn_on
        target:
          entity_id: light.status_flur
        data:
          color_name: green
          brightness_pct: 10
```

### Haustür abschließen, wenn scharf

Siehe [Referenz – Beispiel: Automation, wenn scharf](referenz.md#beispiel-automation-wenn-scharf).
Das **Aufschließen** besser nicht an das Unscharfschalten koppeln.

### Heizung und Kamera bei Abwesenheit

Bei „Abwesend“ oder „Urlaub“: Heizung auf Abwesend, Innenkameras zeichnen auf. Nach dem
Unscharfschalten wieder zurück.

```yaml
alias: Hauswacht – Abwesenheit
triggers:
  - trigger: state
    entity_id: alarm_control_panel.hauswacht
    attribute: phase
    to: armed
    id: scharf
  - trigger: state
    entity_id: alarm_control_panel.hauswacht
    attribute: phase
    to: disarmed
    id: unscharf
actions:
  - choose:
      - conditions:
          - condition: trigger
            id: scharf
          - condition: template
            value_template: >
              {{ state_attr('alarm_control_panel.hauswacht', 'profile_name')
                 in ['Abwesend', 'Urlaub'] }}
        sequence:
          - action: climate.set_preset_mode
            target:
              entity_id: climate.wohnzimmer
            data:
              preset_mode: away
          - action: switch.turn_on
            target:
              entity_id: switch.kamera_wohnzimmer_aufnahme
      - conditions:
          - condition: trigger
            id: unscharf
        sequence:
          - action: climate.set_preset_mode
            target:
              entity_id: climate.wohnzimmer
            data:
              preset_mode: home
          - action: switch.turn_off
            target:
              entity_id: switch.kamera_wohnzimmer_aufnahme
```

`switch.kamera_wohnzimmer_aufnahme` steht für den Aufnahme- bzw. Bewegungserkennungs-Schalter
deiner Kamera-Integration (z. B. Reolink, UniFi Protect) – Name anpassen.

### Willkommenslicht beim Heimkommen

Wer abends heimkommt und unscharf schaltet, bekommt Licht im Flur.

```yaml
alias: Hauswacht – Willkommenslicht
triggers:
  - trigger: state
    entity_id: alarm_control_panel.hauswacht
    attribute: phase
    from: pending
    to: disarmed
conditions:
  - condition: sun
    after: sunset
    before: sunrise
actions:
  - action: light.turn_on
    target:
      entity_id: light.flur
```

`from: pending` heißt: unscharf während der Eingangsverzögerung – also wirklich beim Heimkommen.

## Störungen und Sabotage

### Sabotage aufs Handy (auch wenn unscharf)

Hauswacht meldet Sabotage ohnehin; diese Automation schickt zusätzlich eine kritische
Benachrichtigung an ein bestimmtes Handy.

```yaml
alias: Hauswacht – Sabotage kritisch melden
triggers:
  - trigger: event
    event_type: hauswacht_event
    event_data:
      type: TamperDetected
actions:
  - action: notify.mobile_app_annas_handy
    data:
      title: Sabotage
      message: >
        {{ state_attr(trigger.event.data.sensor_key, 'friendly_name')
           or trigger.event.data.sensor_key }} meldet Sabotage.
      data:
        # iPhone: kritische Benachrichtigung (durchbricht „Nicht stören“)
        push:
          sound:
            name: default
            critical: 1
            volume: 1.0
        # Android: sofort zustellen
        ttl: 0
        priority: high
```

Was genau im Ereignis steht, zeigt Entwicklerwerkzeuge → Ereignisse → `hauswacht_event` →
„Zuhören starten“.

### Anlage gestört: Lampe orange

```yaml
alias: Hauswacht – Störung anzeigen
triggers:
  - trigger: state
    entity_id: sensor.hauswacht_systemstatus
actions:
  - if:
      - condition: state
        entity_id: sensor.hauswacht_systemstatus
        state: ok
    then:
      - action: light.turn_off
        target:
          entity_id: light.stoerung
    else:
      - action: light.turn_on
        target:
          entity_id: light.stoerung
        data:
          color_name: orange
```

`ok` = alles in Ordnung, `degraded` = ein Melder ist ausgefallen, `fault` = Funknetz oder Gateway
gestört.

## Zeitsteuerung

Für „scharf zu bestimmten Zeiten“ brauchst du keine eigene Automation: Die Profil-Automatik kann
feste Uhrzeiten und – für **je Wochentag andere Zeiten** – einen Zeitplan-Helfer, siehe
[Je Wochentag andere Zeiten](profile.md#je-wochentag-andere-zeiten-zeitplan). Dabei gelten die
Sicherheitsregeln der Automatik (Gastmodus, offene Fenster, nie während eines Alarms) von selbst.

## Bedienen auf anderen Wegen

### Gastmodus aus dem Kalender

Steht im Kalender „Gäste“, ist der Gastmodus bis zum Ende des Termins an – keine automatische
Scharfschaltung, keine Erinnerungen.

```yaml
alias: Hauswacht – Gastmodus aus Kalender
triggers:
  - trigger: calendar
    event: start
    entity_id: calendar.familie
conditions:
  - condition: template
    value_template: "{{ 'Gäste' in trigger.calendar_event.summary }}"
actions:
  - action: hauswacht.guest_mode
    target:
      entity_id: alarm_control_panel.hauswacht
    data:
      "on": true
      until: "{{ trigger.calendar_event.end }}"
```

### Keypad-Code startet etwas

Mit einem [Aktions-Code](bedienteile.md#aktions-codes) (z. B. 7777 + Haus) startest du beliebige
Automationen – Beispiele dort: Außenlicht, Garagentor, Szene.

### Taster schaltet etwas zusätzlich

Ein [Taster](bedienteile.md#taster) meldet jeden Druck als `ButtonPressed`:

```yaml
alias: Hauswacht – Taster auch für das Flurlicht
triggers:
  - trigger: event
    event_type: hauswacht_event
    event_data:
      type: ButtonPressed
      control: Taster Haustür
actions:
  - action: light.toggle
    target:
      entity_id: light.flur
```

## Was du lieber nicht automatisierst

- **Nicht automatisch aufschließen**, wenn unscharf geschaltet wird – wer fälschlich unscharf
  schaltet, hätte sonst zusätzlich die Tür geöffnet.
- **Rauchmelder- und Brandfunktionen nicht** mit Einbruch-Automationen mischen.
- **Immer die Testmodus-Bedingung** in Alarm-Automationen – sonst gehen beim Probelauf die Lichter
  an und Kameras zeichnen auf.
- **Keine eigenen Sirenen-Automationen:** Sirenen gehören in Hauswacht (Sperren, Testmodus,
  Brandvorrang) – siehe [Sirenen](sirenen.md).
