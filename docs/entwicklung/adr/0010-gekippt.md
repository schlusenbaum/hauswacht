# ADR 0010: Melder mit Kippstellung („gekippt“)

- Status: vorgeschlagen (Entwicklung auf dem Zweig `entwicklung/gekippt`)
- Datum: 2026-11-18

## Kontext

Hauswacht kennt bisher nur Melder mit zwei Zuständen: offen oder zu. Intern wird alles auf
`on`/`off` abgebildet (`core/sensor_types.normalize`); Binärsensoren, Schlösser und Abdeckungen
sind erlaubt, alles andere muss vorher über einen Home-Assistant-Helfer zu einem Binärsensor
werden.

Immer mehr Fenstersensoren melden aber **drei** Zustände – zu, gekippt, offen – z. B. Senoro.Win
(Zigbee2MQTT: `sensor.…_opening_state` mit `open`/`tilted`/`closed`), Fenstergriffe von
Homematic IP (Attribut `window_state` mit `OPEN`/`TILTED`/`CLOSED`) oder Drehgriffe anderer
Hersteller. Heute geht das nur über einen Template-Helfer, und der hat zwei Schwächen:

1. **Ausfall wird verschluckt:** Ist der Sensor nicht verfügbar, liefert ein einfacher
   Template-Helfer „aus“ – Hauswacht hält das Fenster für zu.
2. **Die Kippstellung geht verloren:** Der Helfer kann nur „offen“ oder „zu“. Gerade das
   gekippte Fenster ist im Alltag der häufigste Fall: nachts im Schlafzimmer gekippt ist gewollt,
   beim Verlassen des Hauses nicht.

## Entscheidung

### 1. Neue Melderart „Melder mit Kippstellung“

Ein Melder mit Kippstellung hat drei Stellungen: **zu**, **gekippt**, **offen**. Als Quelle
dienen:

| Quelle | Beispiel |
|---|---|
| Sensor mit Text-Zustand | `sensor.fenster_schlafzimmer_opening_state` (Senoro) |
| Attribut einer Entität | `binary_sensor.fenstergriff_bad`, Attribut `window_state` (Homematic IP) |
| `input_select` / `select` | Helfer „Testfenster“ mit *offen / gekippt / zu* – zum Ausprobieren ohne Hardware |

Angelegt wird ein solcher Melder unter **Alarmauslösung → Melder mit Kippstellung**:

1. Entität wählen, optional ein Attribut.
2. Hauswacht zeigt die bekannten Werte (Optionen des Sensors bzw. des Auswahl-Helfers, sonst der
   aktuelle Wert) und schlägt die Zuordnung vor: `closed`, `close`, `geschlossen`, `zu` → zu;
   `tilted`, `tilt`, `gekippt` → gekippt; alles andere → offen. Groß-/Kleinschreibung egal.
3. Bestätigen. Danach ist der Melder in den Meldergruppen wählbar wie jeder andere und bekommt
   wie bisher einen Typ (Vorschlag: Fenster).

Gespeichert wird in `options["tilt_sensors"][entity_id] = {"attribute": …, "closed": […],
"tilted": […]}`. Was nicht als zu oder gekippt eingetragen ist, zählt als offen.

**Sicherheitsregeln:**

- Ein **unbekannter Wert** zählt als **offen**, nie als zu.
- `unavailable`, `unknown`, ein fehlendes Attribut oder eine fehlende Entität zählen als **nicht
  verfügbar** – mit der bestehenden Ausfall-Erkennung, Funkstille-Prüfung und
  Ereignis `SensorUnavailable`.

### 2. Gekippt je Profil

Neue Profil-Einstellung **„Gekippte Fenster“**:

| Wert | Bedeutung |
|---|---|
| **gelten als offen** (Standard) | wie bisher: blockiert das Scharfschalten bzw. „trotzdem scharf“ |
| **sind erlaubt** | gekippt zählt als zu – erst **ganz öffnen** löst aus |

Standard ist bewusst „gelten als offen“: Für Versicherung und Einbrecher ist ein gekipptes
Fenster ein offenes Fenster. „Erlaubt“ muss man für ein Profil ausdrücklich einschalten (typisch:
Nacht). Die Einstellung erscheint wie die anderen Profil-Einstellungen auch als Entität
(Kategorie Konfiguration) und lässt sich im Dashboard umschalten.

### 3. Technische Umsetzung: zwei Schritte statt einem

1. **Normalisieren** (`normalize`): Rohzustand → `on` (offen), `off` (zu), **`tilted`** (gekippt)
   oder nicht verfügbar. Für Melder ohne Kippstellung ändert sich nichts.
2. **Bewerten im aktiven Profil** (neu, rein im Kern): `tilted` → `off`, wenn das Profil gekippte
   Fenster erlaubt, sonst → `on`.

Alles danach – Bereitschaft, Auslösung (`is_trigger`), Verzögerungen, Regeln, Überbrücken –
arbeitet wie bisher auf `on`/`off`. Daraus folgt:

| Wechsel | Gekippt erlaubt | Gekippt = offen |
|---|---|---|
| zu → gekippt | nichts | Auslösung |
| gekippt → offen | **Auslösung** | nichts (war schon offen) |
| offen → gekippt | nichts | nichts |
| gekippt/offen → zu | nichts | nichts |

### 4. Überbrücken bei „trotzdem scharf“

Heute bleibt ein überbrückter Melder überbrückt, bis er zu ist. Bei der Kippstellung wäre das
eine Lücke: Wird ein **gekipptes** Fenster (Profil „gekippt = offen“) per „trotzdem scharf“
überbrückt und danach **ganz geöffnet**, gäbe es keinen Alarm.

Entscheidung: Hauswacht merkt sich die **Stellung beim Überbrücken**. Wechselt ein überbrückter
Melder von gekippt nach **offen**, löst er aus. Zu → Ende der Überbrückung wie bisher.

### 5. Was mitwächst

- **Bedienfeld:** neues Attribut `tilted_sensors` (gerade gekippt). Bei erlaubter Kippstellung
  stehen diese Melder **nicht** in `open_sensors`.
- **Ereignisse:** Ereignisse mit `sensor_key` bekommen bei Meldern mit Kippstellung zusätzlich
  `position` (`open`, `tilted`, `closed`). Neue Felder nur zusätzlich – bestehende Automationen
  laufen weiter.
- **Texte:** Nachrichten, Ansagen und Hinweise sagen „gekippt“ statt „offen“, z. B. „Nicht scharf:
  Schlafzimmer gekippt“ oder „Schlafzimmer gekippt (erlaubt)“.
- **Testkarte und Testmodus:** zeigen die Stellung; Simulieren kann alle drei Stellungen.
- **Auslöseregeln:** Ein Schritt mit einem solchen Melder kann „wird geöffnet“ (ganz offen) oder
  „wird gekippt oder geöffnet“ heißen.
- **Einrichtungsassistent:** erkennt Sensoren mit Kippstellung (bekannte Werte) und fragt beim
  Nachtprofil „Gekippte Fenster erlauben?“.
- **Diagnose** und Übersicht: Stellung und Zuordnung je Melder.
- **Doku (deutsch und englisch):** Melder, Profile, Referenz (Attribut, Feld `position`,
  Profil-Entität), Spickzettel Automationen, Beispiele (z. B. „Gekippt und es regnet“),
  Assistent, Testkarte, README-Funktionsliste.

### 6. Nicht Teil dieses Bausteins

- Ausnahme je Meldergruppe („gekippt erlaubt nur im Obergeschoss“) – später, falls gebraucht.
- Erschütterung/Glasbruch des Senoro – geht schon heute über „Melder aus anderem Sensor
  erstellen“; wird in der Doku als Beispiel gezeigt.
- Weitere Zwischenstellungen (z. B. „Spaltlüftung“): werden der Stellung gekippt oder offen
  zugeordnet.

## Abwägung

- **Template-Helfer dokumentieren statt einbauen:** weniger Code, aber Ausfall wird verschluckt
  und die Kippstellung geht verloren. Verworfen.
- **Gekippt als eigener Melder-Typ:** vermischt *wie* ein Melder reagiert (Typ) mit *was* er
  meldet (Stellung). Verworfen – die Stellung ist eine Eigenschaft der Quelle, die Bewertung eine
  des Profils.
- **Einstellung je Melder statt je Profil:** zu fein für den Anfang und schwer zu überblicken. Je
  Profil deckt den Hauptfall (nachts erlaubt) ab.

## Folgen

- Bestehende Einrichtungen bleiben unverändert: keine Migration, neue Optionen nur zusätzlich.
- Der Kern bekommt einen kleinen zusätzlichen Schritt (Bewertung im Profil); alle bisherigen
  Pfade arbeiten weiter auf `on`/`off` und bleiben durch die vorhandenen Tests abgesichert.
- Entwicklung auf `entwicklung/gekippt`, Vorabversionen 0.56.0b1 …, getestet mit einem
  `input_select`-Helfer als Testfenster; Merge erst nach Freigabe.
