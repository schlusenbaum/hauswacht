# Beobachtungen

Hauswacht kann messen, bevor man automatisiert. Beobachtungen **schalten nichts** – sie
liefern Zahlen für eigene Entscheidungen. Die [Funkstille-Beobachtung](melder.md#funkstille-beobachtung-der-richtige-wert-aus-euren-daten)
steht bei den Meldern.

## Heimkehr-Beobachtung

**Systemeinstellungen → Heimkehr-Beobachtung.** Personen auswählen und „Heimkehr beobachten“
einschalten.

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
- Gespeichert werden nur Zeitpunkte, höchstens 60 Tage lang.

Nach zwei bis vier Wochen zeigt der Bericht, ob eine Heimkehr-Automatik bei euch zuverlässig
wäre, für welche Personen und Ortungsquellen, und mit welcher Eingangsverzögerung.

## Zusätzliche Signale je Person

Im zweiten Schritt des Formulars wählst du je Person weitere Signale. Je früher und
zuverlässiger ein Signal, desto besser:

| Signal | Woher | gilt als „zuhause“ |
|---|---|---|
| WLAN-Sensor | Companion App: Android „WLAN-Verbindung“ (`sensor.<handy>_wifi_connection`, unter Einstellungen → Companion App → Sensoren verwalten aktivieren), iPhone „SSID“ (`sensor.<handy>_ssid`, Standort „Immer“ + „Genauer Standort“) | verbunden mit einem der **Heim-WLANs** (Feld im ersten Schritt, durch Komma getrennt) |
| Bluetooth | z. B. Bermuda mit dem BLE-Sender der Android-App | `device_tracker` = zuhause |
| Router | z. B. FRITZ!Box Tools (ohne App, aber träge) | `device_tracker` = zuhause |
| Annäherung | Integration **„Nähe“** (Einstellungen → Geräte & Dienste → Integration hinzufügen → Nähe; Zone Zuhause, Personen): Sensor `sensor.<nähe>_<person>_direction_of_travel` | nähert sich oder angekommen; Fenster 15 min statt 5 min, weil die Annäherung oft Minuten vor der Tür kommt |
| Binärsensor | beliebig | an |

Zusätzlich wertet Hauswacht je Person das **„frühestes Signal“** aus: zuhause, sobald
irgendeine Quelle zuhause meldet. So siehst du, ob eine ODER-Kombination früh genug wäre –
eine UND-Kombination (zwei Belege) wäre sicherer, aber langsamer.

## Tür auf bis unscharf

Läuft eine Eingangsverzögerung, misst Hauswacht, wie lange es bis zum Unscharfschalten dauert
(oder ob es zu spät war). Je Tür: Anzahl, rechtzeitig, zu spät, typische und längste Zeit und
eine **Empfehlung für die Eingangsverzögerung** (längste Zeit plus 25 %, mindestens 5 s, auf
5 s aufgerundet). Hilfreich z. B., um den Platz für ein Bedienteil an der Wand zu prüfen.
