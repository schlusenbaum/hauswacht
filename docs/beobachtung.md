# Beobachtungen

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
- **Herunterladen:** Karte [„Hauswacht Übersicht“](uebersicht.md) → Abschnitt **Überwachung** →
  - **Bericht** – derselbe Bericht als Markdown-Datei, dazu die letzten Heimkehrten;
  - **Tabelle (CSV)** – jede einzelne Heimkehr und jeder Eingang als Zeile: Zeitpunkt, Person
    und Quelle, Tür, Sekunden nach dem Öffnen, wie lange die Person weg war, Ergebnis. Die
    Datei öffnet sich direkt in Excel, Numbers oder LibreOffice (Semikolon, Umlaute korrekt).
- Gespeichert werden nur Zeitpunkte, höchstens 60 Tage lang.

Nach zwei bis vier Wochen zeigt der Bericht, ob eine Heimkehr-Automatik bei euch zuverlässig
wäre, für welche Personen und Ortungsquellen, und mit welcher Eingangsverzögerung.

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
