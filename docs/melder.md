# Melder und Meldergruppen

**Deutsch** | [English](en/sensors.md)

## Welche Melder gehen?

Hauswacht überwacht nur Entitäten, die **offen/zu** kennen:

| Art | gilt als offen bzw. ausgelöst bei |
|---|---|
| Binärsensor (`binary_sensor`) | an |
| Schloss (`lock`) | entriegelt, öffnet, offen, blockiert |
| Abdeckung (`cover`, z. B. Garagentor) | offen, öffnet, schließt |
| [Melder mit Kippstellung](#melder-mit-kippstellung-gekippt) (Sensor mit Text-Zustand, Attribut oder Auswahl-Helfer) | offen – gekippt je nach Profil |
| [Erschütterungsstärke](#erschütterungsstärke-als-zahl) (Zahlensensor oder Zahlenwert-Helfer) | Wert ab der eingestellten Schwelle |

Alles andere wird über einen **Helfer** in Home Assistant zum Binärsensor:

- **Messwerte** (Temperatur, Feuchte, Leistung …): mit
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

**Einstellungsseite → Melder → Meldergruppe anlegen.**

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

- **Direkt auswählen** im Feld „Sensoren“. [Melder mit Kippstellung](#melder-mit-kippstellung-gekippt)
  und [Erschütterungsstärken](#erschütterungsstärke-als-zahl) haben ein eigenes Feld darunter
  („Besondere Melder“ – es erscheint, sobald es welche gibt).
- **Per Label:** Alle Melder, die dieses Label **direkt an der Entität** tragen, gehören
  automatisch dazu. Labels am Gerät zählen bewusst nicht – sonst kämen Batterie- oder
  Verbindungssensoren desselben Geräts mit.

Die überwachten Melder werden beim Scharfschalten festgehalten. Wird im scharfen Zustand ein
Label entfernt, bleibt der Melder bis zum Unscharfschalten überwacht.

## Typen

Der **Typ** legt fest, *wie* ein Melder reagiert; *wann* er scharf ist, legen Meldergruppe und
Alarmprofil fest. Im Seitenblatt einer Meldergruppe steht jeder Melder mit dem vorgeschlagenen
Typ – meist passt er, sonst direkt dort ändern.

| Typ | Vorschlag bei | Verhalten |
|---|---|---|
| **Tür** | Tür, Garagentor, Öffnung, Schloss, Tor | Startet die Eingangsverzögerung; kann Ausgangstür für [Scharf durch Schließen](profile.md#scharf-durch-schließen-der-tür) sein |
| **Fenster** | Fenster | Sofort Alarm |
| **Bewegung** | Bewegung, Anwesenheit, Präsenz | Wartet, wenn gerade eine Eingangsverzögerung läuft, sonst sofort Alarm |
| **Manipulation** | Manipulation (Sabotage) | Wird immer gemeldet, auch unscharf; Alarm je nach Profil |
| **Technik** | Feuchte, Gas, Kälte, Hitze, Kohlenmonoxid | Immer aktiv, nie Teil der Scharfschaltung, kein Einbruchalarm – nur Benachrichtigung (siehe unten) |
| **Erschütterung** | Vibration, [Erschütterungsstärke](#erschütterungsstärke-als-zahl) | Sofort Alarm – mit einstellbarem [Fehlalarmschutz](#erschütterungsmelder); blockiert das Scharfschalten nie |
| **Sonstiges** | alles andere (Rollladen …) | Sicherheitshalber sofort Alarm |

Beispiel: Ein Fenster, durch das man das Haus betritt, bekommt den Typ **Tür**. Rauchmelder
schlägt Hauswacht bewusst nicht als „Technik“ vor – Brandschutz bleibt Sache der Rauchmelder.

## Melder mit Kippstellung (gekippt)

Viele Fenstersensoren melden nicht nur offen oder zu, sondern **drei Stellungen**: **zu**,
**gekippt** und **offen** – z. B. Sensoren im Fensterfalz (etwa Senoro.Win über Zigbee2MQTT) oder
Fenstergriffe (etwa Homematic IP). Hauswacht kann mit allen drei umgehen. Der große Vorteil: In
jedem Alarmprofil legst du fest, ob ein **gekipptes Fenster erlaubt** ist.

> **Beispiel:** Nachts ist das Schlafzimmerfenster gekippt – im Profil „Nacht“ ist das erlaubt,
> die Anlage lässt sich scharf schalten. Öffnet jemand das Fenster **ganz**, gibt es Alarm. Im
> Profil „Abwesend“ zählt dasselbe gekippte Fenster wie offen – du wirst beim Gehen darauf
> hingewiesen.

### Einrichten

**Einstellungsseite → Melder → Besondere Melder → + Kippstellung hinzufügen.**

1. **Quelle wählen.** Woher die Stellung kommt, ist je Gerät verschieden:

   | Gerät liefert … | Beispiel | So eintragen |
   |---|---|---|
   | einen Sensor mit Text-Zustand | `sensor.fenster_schlafzimmer_opening_state` = `open` / `tilted` / `closed` | nur die Entität wählen |
   | ein Attribut an einer Entität | `binary_sensor.fenstergriff_bad`, Attribut `window_state` = `OPEN` / `TILTED` / `CLOSED` | Entität wählen, Attribut `window_state` eintragen |
   | nichts – du willst erst ausprobieren | Helfer „Auswahl“ (Dropdown) „Testfenster“ mit *offen*, *gekippt*, *zu* | den Helfer wählen |

   Welche Werte und Attribute ein Gerät hat, zeigt Entwicklerwerkzeuge → Zustände.
2. **Werte zuordnen.** Hauswacht zeigt die bekannten Werte und schlägt die Zuordnung vor
   (`closed`/`zu`/`geschlossen` → zu, `tilted`/`gekippt` → gekippt). Prüfen, bei Bedarf
   ergänzen (fehlende Werte lassen sich eintippen), speichern.
3. **In eine Meldergruppe nehmen** – direkt im zweiten Schritt oder später unter Meldergruppen
   (eigenes Feld „Melder mit Kippstellung“). Der Typ ist automatisch **Fenster** und lässt sich
   wie bei jedem Melder ändern.
4. **In den Profilen festlegen**, wo gekippt erlaubt ist: Einstellung **„Gekippte Fenster
   erlaubt“** (siehe [Alarmprofile](profile.md#alarmprofile)). Standard ist **aus**.

### So bewertet Hauswacht die Stellungen

| Wechsel | Profil mit „gekippt erlaubt“ | Profil ohne (Standard) |
|---|---|---|
| zu → gekippt | nichts | Auslösung (wie Öffnen) |
| gekippt → offen | **Auslösung** | nichts – war schon „offen“ |
| offen → gekippt | nichts | nichts |
| gekippt oder offen → zu | nichts | nichts |
| Scharfschalten, während gekippt | erlaubt | wie ein offenes Fenster (verweigern, „trotzdem scharf“ …) |

**Sicherheitsregeln:**

- **Unbekannte Werte zählen als offen**, nie als zu – auch Werte, die das Gerät erst später
  meldet (z. B. „Spaltlüftung“). Wer so einen Wert als gekippt behandeln will, ergänzt ihn in der
  Zuordnung.
- **Ausfall wird erkannt** wie bei jedem Melder: Ist der Sensor nicht verfügbar oder fehlt das
  Attribut, gilt er als ausgefallen (Funkstille-Prüfung, Ereignis `SensorUnavailable`,
  Einstellung „Ausgefallene Sensoren beim Scharfschalten“). Ein selbst gebauter Vorlagen-Helfer
  würde einen Ausfall dagegen meist als „zu“ melden.
- **„Trotzdem scharf“ mit gekipptem Fenster:** Das Fenster wird überbrückt – aber nur in der
  Stellung gekippt. Wird es danach **ganz geöffnet**, löst es aus. Erst wenn es zu war, gilt die
  Überbrückung als beendet wie bei jedem Melder.
- In **Auslöseregeln** zählt ein Melder mit Kippstellung, sobald er im aktiven Profil als offen
  gilt: mit „gekippt erlaubt“ also erst beim ganzen Öffnen, sonst schon beim Kippen.

### Wo du die Stellung siehst

- **Bedienfeld:** Attribut `tilted_sensors` (gerade gekippt). Erlaubt das Profil gekippte
  Fenster, stehen sie **nicht** in `open_sensors`.
- **Meldungen:** „Nicht scharf geschaltet: Schlafzimmer: Fenster (gekippt)“.
- **Ereignisse:** Ereignisse mit `sensor_key` haben bei diesen Meldern zusätzlich `position`
  (`open`, `tilted`, `closed`), siehe [Referenz](referenz.md#ereignisse).
- **Testkarte:** zeigt „gekippt“ und hat im Testmodus einen eigenen Knopf **Gekippt** zum
  Simulieren.
- **Anlagenübersicht:** Zustand „gekippt“.

**Bearbeiten und entfernen** unter Einstellungsseite → Melder → Besondere Melder. Entfernen nimmt den Melder
auch aus allen Meldergruppen; am Gerät ändert sich nichts.

> **Erschütterung am Fenster:** Viele dieser Sensoren melden auch Erschütterung (Aufhebeln,
> Glasbruch) als Zahl – daraus wird ein [Erschütterungsmelder](#erschütterungsmelder). Zusammen
> sind beide stark: Nachts ist das Fenster gekippt und erlaubt – wer daran hebelt, löst über die
> Erschütterung aus, **bevor** das Fenster offen ist.

## Erschütterungsmelder

Erschütterungssensoren (z. B. Aqara oder Tuya über Zigbee2MQTT, Geräteklasse „Vibration“) melden
Stöße an Fenstern und Türen – also Aufhebeln oder eine eingeschlagene Scheibe. Hauswacht gibt
ihnen den eigenen Typ **Erschütterung**:

- **Sofort Alarm** im scharfen Profil (keine Eingangsverzögerung).
- **Blockiert das Scharfschalten nie.** Erschütterung ist ein Vorgang, kein offener Zustand – ein
  Sensor, der nach einem Stoß noch eine Minute „an“ steht, verhindert das Scharfschalten nicht.
  Ein **ausgefallener** Erschütterungssensor zählt dagegen wie jeder ausgefallene Melder.
- **Texte** sagen „… (Erschütterung)“.
- **Unscharf** passiert nichts. Wer auch dann informiert werden will, nimmt den Melder unter
  [Immer aktiv](#immer-aktive-melder) auf.

### Fehlalarmschutz: wie viele Erschütterungen bis zum Alarm?

Erschütterungssensoren sind empfindlich: Eine zugeschlagene Tür, ein vorbeifahrender Lkw, ein
Gewitter oder ein Ball gegen die Scheibe können auslösen. Deshalb zeigt das Seitenblatt einer
Meldergruppe mit Erschütterungsmeldern den Abschnitt **Fehlalarmschutz für Erschütterung**:

**„Alarm bei N Meldungen eines Melders innerhalb von S Sekunden“**

| Einstellung | Wirkung |
|---|---|
| **1 Meldung** (Standard) | Jede Erschütterung löst sofort aus – am empfindlichsten |
| **2 Meldungen in 60 s** (Empfehlung) | Ein einzelner Stoß löst nicht aus. Wer hebelt oder eine Scheibe einschlägt, erzeugt fast immer mehrere Stöße kurz hintereinander. Preis: Ein einzelner, sehr kräftiger Schlag allein löst nicht aus |
| 3 – 5 Meldungen | Nur bei sehr unruhigen Stellen (z. B. Tür zur Straße) |

- Gezählt wird **je Melder**: Ein Gewitter, das alle Fenster einmal anstößt, ergibt so keinen
  Alarm.
- Jede Meldung, die noch nicht reicht, erscheint als Ereignis `VibrationCounted` (mit `count`,
  `needed`, `window`) – praktisch, um die Einstellung zu prüfen.
- **Haltezeit beachten:** Viele Erschütterungssensoren bleiben nach einer Meldung eine Weile
  „an“ (oft 60–90 Sekunden) und melden in dieser Zeit keine zweite. Für „2 in 60 Sekunden“ muss
  die Haltezeit deutlich kürzer sein – bei Zigbee2MQTT ist sie oft als Geräteoption einstellbar
  (z. B. 5–10 Sekunden).
- Ändern: Einstellungsseite → Melder → Meldergruppe bearbeiten → **Fehlalarmschutz für
  Erschütterung**.

### Erschütterungsstärke als Zahl

Manche Sensoren melden keine „an/aus“-Erschütterung, sondern eine **Stärke als Zahl** (z. B.
`sensor.fenster_bad_vibration` eines Fenstersensors). Daraus wird ohne Helfer ein Melder:

**Einstellungsseite → Melder → Besondere Melder → + Erschütterungsstärke hinzufügen.**

1. Sensor wählen (zum Ausprobieren ohne Hardware: Helfer **Zahlenwert**, `input_number`).
2. **Schwelle** eintragen: ab diesem Wert gilt es als Erschütterung. Am besten den Wert unter
   Entwicklerwerkzeuge → Zustände beobachten und leicht ans Fenster klopfen – die Schwelle etwas
   über dem Ruhewert und unter einem kräftigen Stoß wählen.
3. Optional gleich in eine Meldergruppe nehmen. Der Typ ist automatisch **Erschütterung**.

**Jede Meldung ab der Schwelle zählt** – auch wenn die Zahl gleich bleibt (Home Assistant meldet
auch unveränderte Werte). Ist der Wert keine Zahl oder der Sensor nicht verfügbar, gilt der
Melder als ausgefallen.

**Kombinieren mit Auslöseregeln:** „Erschütterung, dann innerhalb einer Minute Fenster offen“
geht als [Auslöseregel](ausloeseregeln.md) – z. B. wenn einzelne Erschütterungen nicht reichen
sollen, die Kombination aber schon.

## Melder aus anderem Sensor erstellen

**Einstellungsseite → Melder → Besondere Melder → + Melder aus Messwert erstellen.** Beispiel
Frostwächter:

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

**Einstellungsseite → Melder → Immer aktiv → Bearbeiten.** Melder, die **auch im unscharfen Zustand** melden – z. B.
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

**Einstellungsseite → System → Funkstille von Sensoren.**

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
geprüft, über Neustarts gespeichert; Pausen über einen Neustart zählen nicht). Auf der
Einstellungsseite (System → Funkstille von Sensoren) steht dann z. B.:

> Beobachtet seit 14 Tagen. Längste Pause: Türkontakt vorne 1 h 52 min. **Empfehlung: 3 h.**

Die Empfehlung ist die längste Pause × 1,5, auf volle Stunden aufgerundet – frühestens nach 3
Tagen Beobachtung. Eingetragen wird der Wert von dir; die Beobachtung ändert nichts. Der
Diagnose-Sensor `sensor.hauswacht_funkstille_beobachtung` zeigt Empfehlung und Pausen – auch die
**Empfehlung je Melder** (`recommended_hours`).

Neu beginnen (z. B. nach dem Tausch vieler Batterien oder eines Funk-Koordinators):
[Einstellungsseite](einstellungsseite.md) → **System** → Karte **Funkstille von Sensoren** →
**Messung zurücksetzen**. Gelöscht werden nur die gemessenen Pausen; der allgemeine Wert und die
eigenen Werte je Melder bleiben.

### Eigene Grenze je Melder

Meldet sich ein einzelner Melder viel seltener als die anderen – z. B. ein Batterie-Türkontakt,
der nur bei Änderungen funkt –, würde er den allgemeinen Wert für alle hochziehen. Dann fiele ein
ausgefallener Bewegungsmelder erst nach vielen Stunden auf. Besser: diesem Melder einen **eigenen
Wert** geben.

| Einstellung | Wirkung |
|---|---|
| **Wie allgemein** | Es gilt der allgemeine Wert (Standard) |
| **Eigener Wert** | Eigene Stunden (1–168) für genau diesen Melder |
| **Nie prüfen** | Für Melder, die sich nur bei Änderungen melden. Sie gelten nie wegen Funkstille als ausgefallen; „nicht verfügbar“ (`unavailable`) wird weiter erkannt |

- **Einstellungsseite:** Reiter Melder → auf den Melder klicken → **Funkstille**. Dort stehen die
  Beobachtung für genau diesen Melder und der Knopf **„Empfehlung übernehmen“**. Im Reiter System
  zeigt die Karte „Funkstille von Sensoren“ alle Melder mit längster Pause, Empfehlung und eigenem
  Wert (⚠️, wenn der eigene Wert unter der Empfehlung liegt). In der Melder-Tabelle steht ein
  eigener Wert als „⏱ 24 h“ bzw. „⏱ nie prüfen“ hinter dem Namen.
- Melder mit eigenem Wert zählen für die **allgemeine Empfehlung** nicht mehr mit. Beispiel: Die
  Hintertür schweigt bis zu 16 Stunden, alle anderen höchstens 2 Stunden. Mit eigenem Wert für die
  Hintertür (24 h) empfiehlt die Beobachtung allgemein 3 h statt 24 h.
- Liegt ein eigener Wert unter der Empfehlung für diesen Melder, meldet die
  [Anlagenübersicht](uebersicht.md#prüfhinweise) das als Prüfhinweis.

## Funknetz und Gateways überwachen

**Einstellungsseite → System → Funknetz und Gateways.** Binärsensoren, die melden, ob ein
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
