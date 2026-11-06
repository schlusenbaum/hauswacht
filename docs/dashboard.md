# Dashboard

Hauswacht braucht keine Zusatzkarten. Die Beispielkarte
[`examples/dashboard/hauswacht-karte.yaml`](../examples/dashboard/hauswacht-karte.yaml)
nutzt nur Standardkarten von Home Assistant und funktioniert in jeder Ansichtsart.

## Einfügen

Dashboard bearbeiten → **Karte hinzufügen** → ganz unten **Manuell** → Inhalt der Datei
einfügen → Speichern. Die Knöpfe sind Kurzbefehl-Karten (`shortcut`, ab Home Assistant 2026.5).

Die Entitäts-IDs in der Datei gelten für eine deutschsprachige Instanz; die englischen Namen
stehen oben in der Datei.

## Was die Karte zeigt

| Teil | Wann sichtbar | Zweck |
|---|---|---|
| Kachel „Hauswacht“ | immer | Zustand mit Symbol des aktiven Profils |
| Kachel „Profil“ und „Scharf schalten“ | nur unscharf | Profil wählen und scharf schalten – der einzige Weg zum Scharfschalten auf der Karte |
| „Offen: …“ und „Trotzdem scharf“ | nur unscharf **und** Sensoren offen | Offene Sensoren mit Raum (z. B. „Küche: Fensterkontakt links“); gewähltes Profil mit Bestätigung scharf schalten, offene Sensoren werden überbrückt |
| Knopf „Unscharf schalten“ | scharf, Verzögerung oder Alarm | Unscharf schalten; ist ein PIN eingestellt, fragt Home Assistant ihn ab |
| Kachel „Hauswacht-System“ | nur wenn der Systemstatus nicht OK ist | Hinweis auf ausgefallene Sensoren oder Störungen |

Die Symbolleiste mit den Bedienfeld-Knöpfen (`alarm-modes` mit allen Modi) ist weiter
möglich, doppelt aber die Profilauswahl. Wer sie trotzdem will, ergänzt sie an der
Zustandskachel.

## Trotzdem scharf schalten

Die normalen Knöpfe verweigern das Scharfschalten, solange Sensoren offen sind – so schaltet
niemand versehentlich mit offenem Fenster scharf. „Trotzdem scharf“ fragt vorher nach und
drückt dann `button.hauswacht_trotzdem_scharf_schalten` für das gewählte Profil.

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
| `binary_sensor.hauswacht_offene_sensoren` | an, sobald ein Sensor einer Zone offen ist; Attribute `sensors` (Entitäts-IDs), `names` (Anzeigenamen mit Raum) |
| `sensor.hauswacht_systemstatus` | `ok`, `degraded`, `fault`; Attribute `faulty_infrastructure`, `unavailable_sensors` |
| `switch.hauswacht_testmodus` | Testmodus |
| `select.hauswacht_profil` | Gewähltes Profil (im scharfen Zustand: aktives Profil) |
| `button.hauswacht_scharf_schalten`, `button.hauswacht_trotzdem_scharf_schalten` | Gewähltes Profil scharf schalten (ohne / mit Bestätigung) |
