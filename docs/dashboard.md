# Dashboard

Hauswacht braucht keine Zusatzkarten. Die Beispielkarte
[`examples/dashboard/hauswacht-karte.yaml`](../examples/dashboard/hauswacht-karte.yaml)
nutzt nur Standardkarten von Home Assistant und funktioniert in jeder Ansichtsart.

## Einfügen

Dashboard bearbeiten → **Karte hinzufügen** → ganz unten **Manuell** → Inhalt der Datei
einfügen → Speichern. Die Knöpfe sind Kurzbefehl-Karten (`shortcut`, ab Home Assistant 2026.5).

Die Entitäts-IDs in der Datei gelten für eine deutschsprachige Instanz. Auf Englisch heißen
zwei davon anders: `binary_sensor.hauswacht_open_sensors` und
`sensor.hauswacht_system_status`.

## Was die Karte zeigt

| Teil | Wann sichtbar | Zweck |
|---|---|---|
| Kachel „Hauswacht“ | immer | Zustand und Knöpfe für Zuhause, Nacht, Abwesend, Urlaub, Unscharf |
| „Offen: … – trotzdem scharf schalten“ | nur unscharf **und** Sensoren offen | Liste der offenen Sensoren und vier Knöpfe zum Scharfschalten mit Bestätigung |
| Kachel „Hauswacht-System“ | nur wenn der Systemstatus nicht OK ist | Hinweis auf ausgefallene Sensoren oder Störungen |

## Trotzdem scharf schalten

Die normalen Knöpfe auf der Kachel verweigern das Scharfschalten, solange Sensoren offen
sind – so schaltet niemand versehentlich mit offenem Fenster scharf. Die Knöpfe
„trotzdem scharf schalten“ fragen vorher nach und rufen dann die Aktion `hauswacht.arm` mit
`confirm: true` auf.

- Offene Sensoren werden dabei **überbrückt** und bis zum Unscharfschalten nicht überwacht.
- Das funktioniert nur für Profile, bei denen „Offene Sensoren beim Scharfschalten“ auf
  „Nach Bestätigung erlauben“ oder „Automatisch überbrücken“ steht. Bei „verweigern“ lehnt
  Hauswacht auch die Bestätigung ab.
- Ist für das Scharfschalten ein PIN verlangt, gelingt das über diese Knöpfe nicht; dann die
  Aktion mit `code` aufrufen.

## Eigene Karten

Nützliche Entitäten und Attribute:

| Entität | Inhalt |
|---|---|
| `alarm_control_panel.hauswacht` | Zustand; Attribute `profile`, `timer_ends_at`, `open_sensors`, `unavailable_sensors`, `bypassed_sensors`, `zones`, `last_contact`, `last_siren_decision` |
| `binary_sensor.hauswacht_offene_sensoren` | an, sobald ein Sensor einer Zone offen ist; Attribute `sensors`, `names` |
| `sensor.hauswacht_systemstatus` | `ok`, `degraded`, `fault`; Attribute `faulty_infrastructure`, `unavailable_sensors` |
| `switch.hauswacht_testmodus` | Testmodus |
