# Melder und Meldergruppen

## Welche Melder gehen?

Hauswacht überwacht nur Entitäten, die **offen/zu** kennen:

| Art | gilt als offen bzw. ausgelöst bei |
|---|---|
| Binärsensor (`binary_sensor`) | an |
| Schloss (`lock`) | entriegelt, öffnet, offen, blockiert |
| Abdeckung (`cover`, z. B. Garagentor) | offen, öffnet, schließt |

Alles andere wird über einen **Helfer** in Home Assistant zum Binärsensor:

- **Messwerte** (Temperatur, Feuchte, Leistung …): mit dem Assistenten
  [Melder aus anderem Sensor erstellen](#melder-aus-anderem-sensor-erstellen).
- **Kameras:** Die meisten Kamera-Integrationen liefern Bewegung, Person oder Fahrzeug schon als
  Binärsensoren – die direkt verwenden.
- **Ereignisse** (z. B. Klingel, `event.…`): ein Vorlagen-Binärsensor, der kurz „an“ ist:

```yaml
template:
  - trigger:
      - trigger: state
        entity_id: event.klingel
        not_from: unavailable
    binary_sensor:
      - name: Klingel gedrückt
        state: "on"
        auto_off: "00:00:05"
```

## Meldergruppen

**Alarmauslösung → Meldergruppen → Meldergruppe anlegen.**

Eine **Meldergruppe** fasst Melder zusammen, die immer gemeinsam scharf werden. Profile schalten
ganze Meldergruppen scharf, nicht einzelne Melder. Typisch:

| Meldergruppe | Melder | scharf in den Profilen |
|---|---|---|
| Außen | alle Tür- und Fensterkontakte, ihre Sabotagekontakte | Zuhause, Nacht, Abwesend |
| Innen / Keller | Bewegungs- und Präsenzmelder | Nacht (Keller), Abwesend |

- Hauswacht überwacht nur Melder, die in einer Meldergruppe stehen (oder unter
  [Immer aktiv](#immer-aktive-melder)).
- **Jeder Melder gehört zu genau einer Meldergruppe.** Steht er schon in einer anderen, lässt
  sich die Gruppe nicht speichern; die Meldung nennt Melder und Gruppe.
- Welche Melder eine Gruppe am Ende umfasst, zeigt das Attribut `zones` am Bedienfeld.

Melder kommen auf zwei Wegen in eine Gruppe, beide lassen sich kombinieren:

- **Direkt auswählen** im Feld „Sensoren“.
- **Per Label:** Alle Melder, die dieses Label **direkt an der Entität** tragen, gehören
  automatisch dazu. Labels am Gerät zählen bewusst nicht – sonst kämen Batterie- oder
  Verbindungssensoren desselben Geräts mit.

Die überwachten Melder werden beim Scharfschalten festgehalten. Wird im scharfen Zustand ein
Label entfernt, bleibt der Melder bis zum Unscharfschalten überwacht.

## Typen

Der **Typ** legt fest, *wie* ein Melder reagiert; *wann* er scharf ist, legen Meldergruppe und
Alarmprofil fest. Nach dem Speichern einer Meldergruppe zeigt Hauswacht alle ihre Melder mit dem
vorgeschlagenen Typ – meist passt er, sonst direkt dort ändern.

| Typ | Vorschlag bei | Verhalten |
|---|---|---|
| **Tür** | Tür, Garagentor, Öffnung, Schloss, Tor | Startet die Eingangsverzögerung; kann Ausgangstür für [Scharf durch Schließen](profile.md#scharf-durch-schließen-der-tür) sein |
| **Fenster** | Fenster | Sofort Alarm |
| **Bewegung** | Bewegung, Anwesenheit, Präsenz | Wartet, wenn gerade eine Eingangsverzögerung läuft, sonst sofort Alarm |
| **Manipulation** | Manipulation (Sabotage) | Wird immer gemeldet, auch unscharf; Alarm je nach Profil |
| **Technik** | Feuchte, Gas, Kälte, Hitze, Kohlenmonoxid | Immer aktiv, nie Teil der Scharfschaltung, kein Einbruchalarm – nur Benachrichtigung (siehe unten) |
| **Sonstiges** | alles andere (Vibration, Rollladen …) | Sicherheitshalber sofort Alarm |

Beispiel: Ein Fenster, durch das man das Haus betritt, bekommt den Typ **Tür**. Rauchmelder
schlägt Hauswacht bewusst nicht als „Technik“ vor – Brandschutz bleibt Sache der Rauchmelder.

## Melder aus anderem Sensor erstellen

**Alarmauslösung → Melder aus anderem Sensor erstellen.** Beispiel Frostwächter:

| Feld | Beispiel |
|---|---|
| Messwert | `sensor.temperatur_heizungskeller` |
| Name des neuen Melders | Frost Heizungskeller |
| Unterer Grenzwert | 5 (löst unter 5 °C aus) |
| Oberer Grenzwert | leer |
| Hysterese | 1 (wieder „normal“ erst ab 6 °C – kein ständiges Hin und Her) |
| Typ | Technik |
| Einsetzen in | Immer aktiv (oder eine Meldergruppe) |

Hauswacht legt damit einen **Schwellenwert-Helfer** an (`binary_sensor.frost_heizungskeller`,
unter Einstellungen → Geräte & Dienste → Helfer änderbar und löschbar) und trägt ihn gleich mit
Typ ein. Es wird nur ein neuer Helfer angelegt – bestehende Helfer, Automationen oder Skripte
bleiben unverändert.

## Immer aktive Melder

**Alarmauslösung → Immer aktiv.** Melder, die **auch im unscharfen Zustand** melden – z. B.
Tresor, Waffenschrank, Gartenhaus, Panikknopf. Meldergruppen und/oder einzelne Melder.

| Zustand | Reaktion |
|---|---|
| unscharf (Standard) | **wichtige Benachrichtigung** (durchbricht „Nicht stören“) und Meldung in Home Assistant – kein Alarm, keine Sirene |
| unscharf mit „Sirenen verwenden“ | Alarm mit den hier gewählten Sirenen, Ton und Dauer; Anzeige „Alarm“ (Profil „Immer aktiv“). „Alarm beenden“ führt zurück nach unscharf |
| scharf | sofort Alarm mit der Reaktion des aktiven Profils |

Melder vom Typ **Technik** in einer Meldergruppe sind automatisch immer aktiv. Sie lösen auch
scharf **keinen Einbruchalarm** aus, sondern nur die Benachrichtigung (bzw. mit „Sirenen
verwenden“ den Alarm „Immer aktiv“). Sie blockieren das Scharfschalten nicht.

Hardware-Freigabe, Testmodus und Brandsperre gelten wie immer. In der Testkarte tragen diese
Melder den Hinweis „immer aktiv“.

## Funkstille von Sensoren

**Systemeinstellungen → Funkstille von Sensoren.**

- Ein Melder ist **nicht verfügbar**, wenn er fehlt oder `unavailable` bzw. `unknown` meldet.
- Optional gilt er auch als **ausgefallen**, wenn er sich so viele Stunden nicht gemeldet hat
  (Standard: aus). Batteriesensoren melden sich teils nur alle paar Stunden – großzügig wählen.
- Als „letzter Kontakt“ zählt der „Zuletzt gesehen“-Sensor desselben Geräts (bei Zigbee2MQTT
  `sensor.<gerät>_last_seen`), falls vorhanden und aktiviert. Sonst die letzte Aktualisierung in
  Home Assistant – die wird allerdings bei jedem Neustart erneuert. Das Attribut
  `last_contact` zeigt den Wert je Melder.
- Fällt ein überwachter Melder im scharfen Zustand aus, kommt „Hauswacht: Sensor ausgefallen“
  und das Ereignis `SensorUnavailable`.
- Was beim Scharfschalten mit ausgefallenen Meldern passiert, legt das Alarmprofil fest
  (verweigern oder nach Bestätigung erlauben).

### Funkstille-Beobachtung: der richtige Wert aus euren Daten

Hauswacht merkt sich je Melder die **längste Pause zwischen zwei Lebenszeichen** (jede Minute
geprüft, über Neustarts gespeichert; Pausen über einen Neustart zählen nicht). Im Formular steht
dann z. B.:

> Beobachtet seit 14 Tagen. Längste Pause: Türkontakt vorne 1 h 52 min. **Empfehlung: 3 h.**

Die Empfehlung ist die längste Pause × 1,5, auf volle Stunden aufgerundet – frühestens nach 3
Tagen Beobachtung. Eingetragen wird der Wert von dir; die Beobachtung ändert nichts. Der
Diagnose-Sensor `sensor.hauswacht_funkstille_beobachtung` zeigt Empfehlung und Pausen.

## Funknetz und Gateways überwachen

**Systemeinstellungen → Funknetz und Gateways überwachen.** Binärsensoren, die melden, ob ein
Funknetz oder Gateway läuft. Fällt so ein System aus, können alle Melder dahinter nichts mehr
melden.

- Für Zigbee2MQTT: `binary_sensor.zigbee2mqtt_bridge_connection_state`. Fällt MQTT aus, wird er
  ebenfalls „nicht verfügbar“ – deckt also beides ab.
- Geräteklasse „Problem“: „an“ = Störung. Alle anderen (z. B. „Verbindung“): „an“ = in Ordnung.
- Ist ein Indikator aus oder nicht verfügbar, zeigt der Systemstatus **Störung**. Scharfschalten
  wird dann wie bei ausgefallenen Meldern behandelt.
- Fällt ein System im scharfen Zustand aus, kommt „Hauswacht: Störung“; die Anlage bleibt
  scharf.
- Kommen die Melder nach einem Ausfall geschlossen zurück, gibt es keinen Alarm. Kommt ein
  Melder **offen** zurück, löst er aus – ein verpasstes Öffnen wird so nachgeholt.
