# Beobachtungen

**Deutsch** | [English](en/observations.md)

Hauswacht kann messen, bevor man automatisiert. Beobachtungen **schalten nichts** – sie
liefern Zahlen für eigene Entscheidungen. Die [Funkstille-Beobachtung](melder.md#funkstille-beobachtung-der-richtige-wert-aus-euren-daten)
steht bei den Meldern.

## Heimkehr-Beobachtung

**Systemeinstellungen → Anwesenheit und Heimkehr-Beobachtung.** Personen auswählen und
„Heimkehr beobachten“ einschalten.

Hauswacht zeichnet dann auf, wann eine **Eingangstür** (Sensoren mit der Rolle „entry“)
geöffnet wird und wann eine Person als **heimgekommen** erkannt wird – für die Person insgesamt
und für jede ihrer Ortungsquellen einzeln (z. B. Router, App, iCloud). Daraus berechnet
Hauswacht, wie eine automatische Heimkehr bei euch funktionieren würde.

> Die Beobachtung **schaltet nichts**: kein Unscharf, kein Alarm, keine Benachrichtigung.
> Ein Test stellt sicher, dass dieser Teil des Codes keine Aktionen aufrufen kann.

Ausgewertet wird jede Heimkehr nach mindestens 5 Minuten Abwesenheit:

| Wert | Bedeutung |
|---|---|
| mit Tür | Innerhalb von 5 Minuten wurde eine Eingangstür geöffnet |
| ohne Tür | Keine Türöffnung – meist eine Falschmeldung der Ortung |
| Verzögerung | Sekunden zwischen Türöffnung und erkannter Heimkehr (negativ = vorher erkannt) |
| Fehlalarme bei X s | So oft wäre die Heimkehr erst nach einer Eingangsverzögerung von X Sekunden erkannt worden |

- **Sensor „Heimkehr-Beobachtung“**: Anzahl ausgewerteter Heimkehrten; die Zahlen pro Quelle
  stehen im Attribut `sources`, die letzten zehn Heimkehrten im Attribut `recent`, die Zeiten
  „Tür auf bis unscharf“ im Attribut `entry_times`.
- **Knopf „Heimkehr-Bericht“**: erstellt eine Übersicht als Benachrichtigung in Home Assistant.
- **Ansehen, speichern, zurücksetzen:** auf der Einstellungsseite, siehe
  [Messungen auf der Einstellungsseite](#messungen-auf-der-einstellungsseite).
- **Herunterladen:** auch in der Karte [„Hauswacht Übersicht“](uebersicht.md) → Abschnitt **Überwachung** →
  - **Bericht** – derselbe Bericht als Markdown-Datei, dazu die letzten Heimkehrten;
  - **Tabelle (CSV)** – jede einzelne Heimkehr und jeder Eingang als Zeile: Zeitpunkt, Person
    und Quelle, Tür, Sekunden nach dem Öffnen, wie lange die Person weg war, Ergebnis. Die
    Datei öffnet sich direkt in Excel, Numbers oder LibreOffice (Semikolon, Umlaute korrekt).
- Gespeichert werden nur Zeitpunkte, höchstens 60 Tage lang.

Nach zwei bis vier Wochen zeigt der Bericht, ob eine Heimkehr-Automatik bei euch zuverlässig
wäre, für welche Personen und Ortungsquellen, und mit welcher Eingangsverzögerung.

### Messungen auf der Einstellungsseite

Alles, was die Heimkehr-Beobachtung misst, steht auch auf der
[Einstellungsseite](einstellungsseite.md) → **System** → Karte **Anwesenheit und
Heimkehr-Beobachtung** → Block **Messungen**:

- **Seit wann:** „Heimkommen gemessen seit 07.11.2026 (15 Tage, 84 Türöffnungen) · Weggehen
  gemessen seit 21.11.2026 (1 Tag)“.
- **Tabelle je Person:**

  | Person | Heimgekommen (mit Tür) | Rausgegangen mit Tür | längste Zeit bis „weg“ | Schweigepausen (längste) |
  |---|---|---|---|---|
  | Christian | 23 (21) | 4 | 95 s | 2 (6 min) |

  Gezählt wird das **frühestes Signal** je Person (alle Signale zusammen).
- **Empfehlung je Person** für „Rausgehen ohne PIN erkennen“: ✅ zuverlässig mit Wartezeit,
  ⚠️ Warnhinweis mit Tipp, oder grau „noch zu wenig gemessen“.
- **Eingänge:** je Tür, wie oft die Eingangsverzögerung lief, die längste Zeit bis unscharf und
  die empfohlene Eingangsverzögerung (siehe [Tür auf bis unscharf](#tür-auf-bis-unscharf)).

Darunter die Knöpfe:

| Knopf | Was passiert |
|---|---|
| **Bericht anzeigen** | Zeigt den ganzen Bericht direkt auf der Seite (noch einmal drücken: ausblenden) |
| **Bericht speichern** | Lädt den Bericht als Markdown-Datei herunter |
| **Tabelle speichern (CSV)** | Lädt jede einzelne Messung als Tabelle herunter |
| **Heimkommen zurücksetzen** | Beginnt nur die Messung „Heimkommen“ neu (Heimkehrten, Türöffnungen, Empfehlung „Unscharf mit Türbeleg“); Weggehen und Eingänge bleiben |
| **Weggehen zurücksetzen** | Löscht nur die Messung „Weggehen“ und beginnt sie neu; Heimkommen und Eingänge bleiben |
| **Alle Messungen zurücksetzen** | Löscht Heimkommen, Eingänge und Weggehen und beginnt neu |

Zurücksetzen fragt vorher nach, ändert **keine Einstellung** und schaltet nichts. Sinnvoll z. B.
nach dem Einrichten neuer Signale (Companion App), damit alte Werte die Empfehlung nicht
verfälschen. Tipp: vorher **Tabelle speichern**, wenn du die alten Werte behalten willst.
Die Knöpfe zum Zurücksetzen sehen nur Administratoren.

## Zusätzliche Signale je Person

Im zweiten Schritt des Formulars wählst du je Person weitere Signale. Je früher und
zuverlässiger ein Signal, desto besser.

Die Signale gelten **auch für die Profil-Automatik** („Scharf, wenn alle weg“, „Unscharf bei
Rückkehr“). Der zweite Schritt zeigt deshalb auch die Personen aus der Automatik der Profile,
selbst wenn die Beobachtung aus ist. Wie die Automatik die Signale verbindet, steht unter
[Profile → Woran Hauswacht erkennt, wer zuhause ist](profile.md#woran-hauswacht-erkennt-wer-zuhause-ist).

| Signal | Woher | gilt als „zuhause“ |
|---|---|---|
| WLAN-Sensor | Companion App: Android „WLAN-Verbindung“ (`sensor.<handy>_wifi_connection`, unter Einstellungen → Companion App → Sensoren verwalten aktivieren), iPhone „SSID“ (`sensor.<handy>_ssid`, Standort „Immer“ + „Genauer Standort“) | verbunden mit einem der **Heim-WLANs** (Feld im ersten Schritt, durch Komma getrennt) |
| Bluetooth | z. B. Bermuda mit dem BLE-Sender der Android-App | `device_tracker` = zuhause |
| Router | z. B. FRITZ!Box Tools (ohne App, aber träge) | `device_tracker` = zuhause |
| Annäherung | Integration **„Nähe“** (Einstellungen → Geräte & Dienste → Integration hinzufügen → Nähe; Zone Zuhause, Personen): Sensor `sensor.<nähe>_<person>_direction_of_travel` | nähert sich oder angekommen; Fenster 15 min statt 5 min, weil die Annäherung oft Minuten vor der Tür kommt |
| Annäherung (Places) | Zusatz-Integration **Places** (HACS): Sensor `sensor.places_<person>_direction_of_travel` | „towards home“ = zuhause, „away from home“ = weg, „stationary“ zählt nicht (ab 0.60) |
| Binärsensor | beliebig | an |

Zusätzlich wertet Hauswacht je Person das **„frühestes Signal“** aus: zuhause, sobald
irgendeine Quelle zuhause meldet. So entscheidet auch die Profil-Automatik. (Die Beobachtung
nimmt dabei auch die Geräte-Tracker der Person einzeln dazu; die Automatik nutzt die Person
selbst und die gewählten Signale.)

### Empfehlung für „Unscharf mit Türbeleg“

Sobald es Heimkehrten **mit Tür** gibt, enthält der Bericht einen Abschnitt **„Unscharf mit
Türbeleg – nötige Eingangsverzögerung je Person“**. Beispiel:

```
- Christian: mindestens 60 s (längste Erkennung nach dem Öffnen: 48 s; 30 Heimkehrten mit
  Tür, 2 ohne Tür – die würden ignoriert)
- Niklas: mindestens 5 s (längste Erkennung nach dem Öffnen: 0 s; 22 Heimkehrten mit Tür,
  23 ohne Tür – die würden ignoriert)
```

So liest du das:

- **mindestens … s:** Mit dieser Eingangsverzögerung hätte „Mit Türbeleg“ bei jeder
  beobachteten Heimkehr rechtzeitig unscharf geschaltet (längste Verspätung plus 25 %
  Puffer, mindestens 5 s). Die Eingangsverzögerung selbst stellst du im Profil ein – für
  das Aufschließen ohne Handy brauchst du ohnehin genug Zeit.
- **ohne Tür:** Geister-Heimkehrten. „Mit Türbeleg“ ignoriert sie.
- Den Wert findest du auch im Attribut `door_proof` des Sensors „Heimkehr-Beobachtung“.

## Tür auf bis unscharf

Läuft eine Eingangsverzögerung, misst Hauswacht, wie lange es bis zum Unscharfschalten dauert
(oder ob es zu spät war). Je Tür: Anzahl, rechtzeitig, zu spät, typische und längste Zeit und
eine **Empfehlung für die Eingangsverzögerung** (längste Zeit plus 25 %, mindestens 5 s, auf
5 s aufgerundet). Hilfreich z. B., um den Platz für ein Bedienteil an der Wand zu prüfen.

## Weggehen (Vorbereitung für „Rausgehen ohne PIN erkennen“)

Ab 0.60 misst die Heimkehr-Beobachtung auch das **Weggehen**. Das ist die Messung für eine
spätere Funktion ([ADR 0014](entwicklung/adr/0014-ausgangserkennung.md)): Wer bei scharfem
Profil vergisst, den PIN einzugeben, und durch die Haustür rausgeht, soll keinen Alarm
auslösen – weil sein Handy kurz danach „weg“ meldet. Dafür muss Hauswacht wissen, **wie schnell**
eure Handys „weg“ melden und **wie oft sie einfach nur schweigen**. Auch diese Messung
**schaltet nichts**.

Es gilt ein einfacher Grundsatz: **Ohne geöffnete Tür kann niemand weggehen.**

| Wert | Bedeutung |
|---|---|
| Rausgehen mit Tür | Eine Quelle meldet „weg“, und bis zu 15 Minuten vorher ging eine Eingangstür auf |
| typisch / längste bis „weg“ | Zeit von „Tür auf“ bis „weg“ |
| Schweigepause | „weg“, ohne dass vorher eine Tür aufging: Das Handy schläft, das WLAN hakt – die Person ist in Wahrheit zuhause |
| längste Pause | wie lange die längste Schweigepause gedauert hat |

Wichtig ist vor allem die Zeile **„frühestes Signal“** je Person: Sie meldet erst „weg“, wenn
**alle** Signale der Person „weg“ sagen. Genau so soll die spätere Funktion entscheiden.

### Empfehlung je Person

Der Bericht endet mit **„Rausgehen ohne PIN erkennen – Empfehlung je Person“**. Dieselben
Sätze stehen auf der Einstellungsseite in der Karte **Anwesenheit und Heimkehr-Beobachtung**,
und Empfehlung bzw. Warnhinweis erscheinen zusätzlich als [Prüfhinweis](uebersicht.md#prüfhinweise) (Tab **Übersicht**). Beispiel:

```
- Christian: Rausgehen wird zuverlässig erkannt – empfohlene Wartezeit 3 min (aus 12× Rausgehen).
- Niklas: Alle Signale haben 9× länger als 4 min geschwiegen, ohne dass eine Tür aufging.
  So wäre Rausgehen nicht sicher von einem Einbruch zu unterscheiden. Tipp: ein zweites
  Signal einrichten, z. B. die Companion App mit WLAN-Sensor.
- Finja: noch zu wenig gemessen (1× Rausgehen) – die Empfehlung kommt nach mindestens
  3× Rausgehen und 2 Tagen.
```

So liest du das:

- **empfohlene Wartezeit:** längste gemessene Zeit von „Tür auf“ bis „weg“ plus Puffer (25 %,
  mindestens 1 Minute), auf ganze Minuten aufgerundet, zwischen 1 und 15 Minuten. So lange
  würde Hauswacht später still warten, bevor es Alarm gibt.
- **zuverlässig:** Die Person ist mindestens 3× durch eine Tür rausgegangen, das Weggehen
  wurde mindestens 2 Tage gemessen (gezählt ab der Installation von 0.60, nicht ab dem Start der
  Heimkehr-Beobachtung; Attribut `departure_days`), und es gab **keine** Schweigepause, die länger war als die
  Wartezeit.
- **Warnhinweis „geschwiegen“:** Alle Signale der Person waren schon länger als die Wartezeit
  still, ohne dass eine Tür aufging. Fiele so eine Pause in die Wartezeit nach einem Einbruch,
  hielte Hauswacht das für „Rausgehen“. Abhilfe: ein zusätzliches Signal, das nicht schläft –
  am besten der WLAN-Sensor der Companion App. Ein reiner Ping aufs iPhone reicht meist nicht,
  weil schlafende iPhones nicht antworten.
- **Warnhinweis „zu spät“:** Die Signale merken das Rausgehen erst nach mehr als 15 Minuten.
  Abhilfe: ein schnelleres Signal (WLAN-Sensor oder Bluetooth).
- **Schweigepausen bei mehreren Personen gleichzeitig** (innerhalb einer Minute) sehen nach
  einem WLAN- oder Router-Ausfall aus. Sie zählen für die Empfehlung nicht mit, weil die spätere
  Funktion so einen Fall eigens abfängt. Im Bericht stehen sie trotzdem.

Personen mit Warnhinweis werden später **nicht ausgeschlossen** – der Hinweis zeigt nur, dass
die Erkennung für sie unsicher wäre.

Die Werte stehen auch in den Attributen `departure` (je Quelle), `leaving_advice` (je Person) und
`departure_days` (Tage seit Beginn der Messung)
des Sensors „Heimkehr-Beobachtung“, und jede einzelne Messung als Zeile „Weggehen“ in der
**Tabelle (CSV)**.

> Gut zu wissen: Fällt eine Schweigepause zufällig in die 15 Minuten nach einer Türöffnung
> (jemand anderes geht raus), zählt sie als „Rausgehen mit Tür“ mit langer Zeit. Wirkt eine
> Empfehlung zu hoch, lohnt ein Blick in die CSV-Tabelle.
