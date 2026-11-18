# Beispiele: Hauswacht mit anderen Geräten verbinden

**Deutsch** | [English](en/examples.md)

Hauswacht schaltet selbst nur **Sirenen** und verschickt Nachrichten und Ansagen. Alles andere –
Licht, Kameras, Rollläden, Heizung, Türschloss – erledigen **eigene Automationen**, die auf
Hauswacht reagieren. Diese Seite sammelt fertige Beispiele zum Abschreiben.

Welchen Auslöser du wofür nimmst, steht im Spickzettel
[Automationen: was nehme ich wofür?](automationen.md); jedes Feld in der [Referenz](referenz.md).

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
> eintragen. Jedes Ereignis nennt seinen Bereich im Feld `area` (z. B. `garage`).

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

### Mehrere Bereiche: Sabotage in der Garage

Mit [Bereichen](profile.md#bereiche) nennt jedes Ereignis seinen Bereich in `area` (Kennung) und
`area_name` (Anzeigename). Hier geht Sabotage **nur in der Garage** an Peters Handy, und das
Garagenlicht geht an. Sabotage im Haus löst diese Automation nicht aus.

```yaml
alias: Hauswacht – Sabotage Garage
triggers:
  - trigger: event
    event_type: hauswacht_event
    event_data:
      type: TamperDetected
      area: garage
conditions:
  - condition: state
    entity_id: alarm_control_panel.hauswacht_garage
    attribute: test_mode
    state: false
actions:
  - action: light.turn_on
    target:
      entity_id: light.garage
  - action: notify.mobile_app_peters_handy
    data:
      title: "Sabotage – {{ trigger.event.data.area_name }}"
      message: >
        {{ state_attr(trigger.event.data.sensor_key, 'friendly_name')
           or trigger.event.data.sensor_key }} meldet Sabotage.
```

- Die Kennung (`garage`) steht in der [Referenz](referenz.md#ereignisse) bzw. beim Zuhören auf
  `hauswacht_event`; sie bleibt gleich, auch wenn du den Bereich umbenennst.
- `area: all` haben Ereignisse der ganzen Anlage (z. B. Funknetz gestört) und Bedienteile für alle
  Bereiche. Wer **alle** Bereiche meinen will, lässt `area` einfach weg.
- Das Bedienfeld des Bereichs heißt z. B. `alarm_control_panel.hauswacht_garage` – im Zweifel
  unter Einstellungen → Entitäten nachsehen.

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

## Fenster mit Kippstellung

Für [Melder mit Kippstellung](melder.md#melder-mit-kippstellung-gekippt). Gekippte Fenster
stehen im Attribut `tilted_sensors` des Bedienfelds – auch wenn das Profil sie erlaubt.

### Es regnet und ein Fenster ist gekippt

```yaml
alias: Hauswacht – Regen bei gekipptem Fenster
triggers:
  - trigger: state
    entity_id: binary_sensor.regensensor
    to: "on"
conditions:
  - condition: template
    value_template: >
      {{ state_attr('alarm_control_panel.hauswacht', 'tilted_sensors') | count > 0 }}
actions:
  - action: notify.mobile_app_annas_handy
    data:
      title: Es regnet
      message: >
        Gekippt:
        {{ state_attr('alarm_control_panel.hauswacht', 'tilted_sensors')
           | map('state_attr', 'friendly_name') | join(', ') }}
```

Statt eines Regensensors geht auch die Wettervorhersage (`weather.…` wechselt auf `rainy`).

### Nachts gekippt erlauben, tagsüber nicht – automatisch

Das regelt die Profil-Einstellung **„Gekippte Fenster erlaubt“** von selbst: an bei „Nacht“, aus
bei „Abwesend“. Eine eigene Automation ist dafür nicht nötig.

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

## Rauchmelder untereinander vernetzen

> **Nur wichtig, wenn du Rauchmelder als Alarmgeber verwendest** – also die Sirene deiner
> Rauchmelder auch als [Sirene für Hauswacht](sirenen.md) nutzt. Dann gehören die Rauchmelder zu
> deiner Alarmanlage, und hier steht, wie Brand- und Einbruchalarm sauber getrennt bleiben. Hast
> du eigene Sirenen und mit Rauchmeldern in Hauswacht nichts zu tun, kannst du diesen Abschnitt
> überspringen – das Vernetzen ist dann ein reines Home-Assistant-Thema.

Viele Funk-Rauchmelder (z. B. über Zigbee) sind **nicht** untereinander verbunden: Brennt es im
Wohnzimmer, piept nur der Melder im Wohnzimmer – oben im Schlafzimmer hört man ihn vielleicht
nicht. Eine kleine eigene Automation lässt dann bei Rauch **alle** Melder mitlaufen.

> **Das ist bewusst keine Funktion von Hauswacht.** Brandschutz darf von nichts abhängen – nicht
> vom Testmodus, nicht von der Freigabe der Sirenen, nicht von einem Update der Alarmanlage. Eine
> eigene Automation mit wenigen Zeilen hat diese Abhängigkeiten nicht. Hauswacht hält sich dabei
> heraus: Meldet irgendein Rauchmelder Brand, schaltet Hauswacht keine Sirene ein und keine aus
> (siehe [Brandschutz](sirenen.md#brandschutz)).

```yaml
alias: Rauchmelder – bei Rauch alle Melder alarmieren
mode: single
triggers:
  - trigger: state
    entity_id:
      - binary_sensor.rauchmelder_wohnzimmer_smoke
      - binary_sensor.rauchmelder_flur_smoke
      - binary_sensor.rauchmelder_schlafzimmer_smoke
    to: "on"
actions:
  - action: siren.turn_on
    continue_on_error: true
    target:
      entity_id:
        - siren.rauchmelder_wohnzimmer
        - siren.rauchmelder_flur
        - siren.rauchmelder_schlafzimmer
  - action: notify.mobile_app_annas_handy
    data:
      title: Feuer!
      message: "{{ trigger.to_state.name }} meldet Rauch."
```

**Ganz wichtig – vor dem Einsatz selbst prüfen:**

- **Der richtige Ton:** Viele Rauchmelder-Sirenen haben mehrere Töne (z. B. Feuer und Einbruch).
  Welche es gibt, zeigt Entwicklerwerkzeuge → Zustände → die Sirene → Attribut
  `available_tones`. Den Feuerton dann unter `data:` mit `tone:` eintragen.
- **Der Testknopf:** Setzt der Testknopf am Melder auch den Rauch-Sensor auf „an“, piepen beim
  Testen alle Melder. Dann den Testknopf-Sensor als Bedingung ausschließen oder damit leben.
- **Probelauf:** Einmal mit Ankündigung an alle im Haus ausprobieren – mit Testknopf oder
  Prüfspray, je nach Anleitung des Melders.
- **`continue_on_error: true`** sorgt dafür, dass ein ausgefallener Melder die anderen nicht
  aufhält.
- **Kein Ersatz für die Melder selbst:** Jeder Melder piept weiterhin von sich aus. Die
  Vernetzung über Home Assistant kommt nur dazu – und funktioniert nur, solange Home Assistant und
  das Funknetz laufen.
- **Abschalten** bei Fehlalarm: z. B. ein Skript mit `siren.turn_off` auf alle Melder. Bei echtem
  Rauch löst der betroffene Melder einfach wieder aus. Dieses Skript ist **nur** für Brandalarm –
  einen Einbruchalarm beendest du über Hauswacht.

## Was du lieber nicht automatisierst

- **Nicht automatisch aufschließen**, wenn unscharf geschaltet wird – wer fälschlich unscharf
  schaltet, hätte sonst zusätzlich die Tür geöffnet.
- **Rauchmelder- und Brandfunktionen nicht** mit Einbruch-Automationen mischen.
- **Immer die Testmodus-Bedingung** in Alarm-Automationen – sonst gehen beim Probelauf die Lichter
  an und Kameras zeichnen auf.
- **Keine eigenen Sirenen-Automationen:** Sirenen gehören in Hauswacht (Sperren, Testmodus,
  Brandvorrang) – siehe [Sirenen](sirenen.md).
