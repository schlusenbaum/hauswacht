# ADR 0010: Fenster richtig überwachen – Kippstellung und Erschütterung

- Status: umgesetzt in 0.56.0 (entwickelt auf dem Zweig `entwicklung/gekippt`, getestet über die Vorabversionen 0.56.0b1 und b2)
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

Ähnlich lieblos laufen heute **Erschütterungssensoren** (Geräteklasse `vibration`, z. B. Aqara
oder Tuya über Zigbee2MQTT): Sie landen beim Typ „Sonstiges“ und

- lösen bei **jeder einzelnen** Meldung sofort aus – Erschütterungssensoren sind aber
  fehlalarmanfällig (zugeschlagene Tür, Lkw, Gewitter, Haustier),
- **blockieren das Scharfschalten**, solange sie noch „an“ stehen (viele halten „an“ eine Minute),
  als wären sie ein offenes Fenster,
- heißen in Nachrichten „geöffnet“,
- und Sensoren, die nur eine **Stärke als Zahl** liefern (z. B. Senoro `vibration`), gehen nur
  über den Umweg „Melder aus anderem Sensor erstellen“.

Kippstellung und Erschütterung gehören zusammen: Nachts darf das Fenster gekippt sein – wer daran
hebelt, soll trotzdem Alarm auslösen, **bevor** es offen ist.

## Entscheidung

Der Baustein hat zwei Teile, die nacheinander gebaut und getestet werden: **A – Kippstellung**
(Abschnitte 1–5) und **B – Erschütterung** (Abschnitt 6).

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
  Profil-Entität, neuer Typ), Spickzettel Automationen, Beispiele (z. B. „Gekippt und es regnet“,
  „Erschütterung, dann Fenster offen“), Assistent, Testkarte, README-Funktionsliste.

### 6. Teil B: Erschütterung als eigener Melder-Typ

**Neuer Typ „Erschütterung“** neben Tür, Fenster, Bewegung, Manipulation, Technik und Sonstiges.
Vorschlag automatisch für die Geräteklasse `vibration`, änderbar in der Meldergruppe wie jeder Typ.

| Eigenschaft | Verhalten |
|---|---|
| Reaktion | sofort (wie Fenster) – im scharfen Profil, Eingangsverzögerung gilt nicht |
| Scharfschalten | **blockiert nie**: Erschütterung ist ein Vorgang, kein offener Zustand. Ein *ausgefallener* Erschütterungssensor zählt aber wie jeder ausgefallene Melder |
| Zählen | jede **Meldung** zählt einmal: beim Binärsensor jeder Wechsel nach „an“, bei einer Stärke als Zahl jede Meldung über der Schwelle |
| Texte | „Erschütterung am Fenster Bad“ statt „geöffnet“ |
| Unscharf | nichts – wer auch unscharf informiert werden will, nimmt wie bisher **Immer aktiv** (dann Benachrichtigung) |

**Fehlalarmschutz je Meldergruppe:** „Alarm bei **N** Meldungen eines Erschütterungsmelders
innerhalb von **S** Sekunden“.

- **Standard: 1 Meldung** – damit ist nichts schwächer, als man es von einem Melder erwartet.
- **Empfehlung im Formular: 2 Meldungen innerhalb von 60 Sekunden**, mit Erklärung: Ein
  einzelner Stoß (Tür knallt, Lkw, Ball gegen die Scheibe) löst dann keinen Alarm aus – wer ein
  Fenster aufhebelt oder eine Scheibe einschlägt, erzeugt fast immer mehrere Stöße kurz
  hintereinander. Der Preis: ein einzelner, sehr kräftiger Schlag allein löst nicht aus.
- Gezählt wird **je Melder** (nicht über die ganze Gruppe) – ein Gewitter, das alle Fenster
  gleichzeitig einmal anstößt, ergibt so keinen Alarm.
- **Hinweis zur Haltezeit:** Viele Binärsensoren bleiben nach einer Erschütterung eine Weile
  „an“ und melden in dieser Zeit keine zweite. Die Haltezeit muss deshalb deutlich kürzer sein als
  das Zeitfenster (bei Zigbee2MQTT oft als Geräteoption einstellbar). Das steht im Formular und in
  der Doku.

**Stärke als Zahl direkt:** Unter „Melder mit Kippstellung“ (heißt dann **„Besondere Melder“**)
gibt es als zweite Art **„Erschütterungsstärke“**: Zahlensensor (z. B. Senoro `vibration`) oder
`input_number` zum Testen wählen, Schwelle festlegen – fertig, ohne Helfer. Jede gemeldete Zahl
über der Schwelle zählt als eine Meldung, auch wenn der Wert gleich bleibt (Home Assistant meldet
auch unveränderte Werte). Ausfall wird wie bei jedem Melder erkannt.

**Bestehende Einrichtungen:** Sensoren mit Geräteklasse `vibration`, deren Typ nie geändert wurde,
werden zum Typ Erschütterung. Unterschied zu vorher: Sie blockieren das Scharfschalten nicht mehr
und heißen in Texten „Erschütterung“; ausgelöst wird bei 1 Meldung wie bisher. Wer den Typ selbst
auf „Sonstiges“ gestellt hat, behält ihn. Das steht im CHANGELOG.

**Testen ohne Hardware:** im Testmodus über die Testkarte eine Erschütterung simulieren, oder
`input_number` als Stärke-Quelle.

**Zusammenspiel:** Mit Auslöseregeln geht zusätzlich „Erschütterung, dann innerhalb einer Minute
Fenster offen“ – das bleibt wie es ist und wird in den Beispielen gezeigt.

### 7. Nicht Teil dieses Bausteins

- Ausnahme je Meldergruppe („gekippt erlaubt nur im Obergeschoss“) – später, falls gebraucht.
- Glasbruchmelder mit eigener Geräteklasse – laufen als Erschütterung oder Sonstiges, je nach
  Gerät.
- Weitere Zwischenstellungen (z. B. „Spaltlüftung“): werden der Stellung gekippt oder offen
  zugeordnet.

## Abwägung

- **Template-Helfer dokumentieren statt einbauen:** weniger Code, aber Ausfall wird verschluckt
  und die Kippstellung geht verloren. Verworfen.
- **Gekippt als eigener Melder-Typ:** vermischt *wie* ein Melder reagiert (Typ) mit *was* er
  meldet (Stellung). Verworfen – die Stellung ist eine Eigenschaft der Quelle, die Bewertung eine
  des Profils.
- **Erschütterung über Auslöseregeln statt eigenem Typ:** Regeln können „zweimal derselbe
  Melder“ nicht sauber abbilden und blockieren das Scharfschalten nicht weg. Verworfen.
- **Zählen über die ganze Gruppe:** fängt Täter, die an zwei Fenstern rütteln, aber auch jedes
  Gewitter. Verworfen zugunsten „je Melder“.
- **Einstellung je Melder statt je Profil:** zu fein für den Anfang und schwer zu überblicken. Je
  Profil deckt den Hauptfall (nachts erlaubt) ab.

## Folgen

- Bestehende Einrichtungen bleiben unverändert: keine Migration, neue Optionen nur zusätzlich.
- Der Kern bekommt einen kleinen zusätzlichen Schritt (Bewertung im Profil); alle bisherigen
  Pfade arbeiten weiter auf `on`/`off` und bleiben durch die vorhandenen Tests abgesichert.
- Erschütterungssensoren mit Geräteklasse `vibration` blockieren das Scharfschalten nicht mehr
  (siehe Teil B) – die einzige Verhaltensänderung für bestehende Einrichtungen.
- Entwicklung auf `entwicklung/gekippt`, erst Teil A, dann Teil B, Vorabversionen 0.56.0b1 …,
  getestet mit `input_select` (Testfenster) und `input_number` (Erschütterungsstärke) bzw. dem
  Testmodus; Merge erst nach Freigabe.
