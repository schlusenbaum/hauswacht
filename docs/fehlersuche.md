# Fehlersuche

## Scharfschalten

**„Scharfschalten abgelehnt“ – warum?**
Die Meldung nennt den Grund: offene Melder, ausgefallene Melder, Störung von Funknetz/Gateway
oder ein Profil ohne Meldergruppen. Offene Melder zeigt auch
`binary_sensor.hauswacht_offene_sensoren`. Erlaubt das Profil „nach Bestätigung“, geht
[Trotzdem scharf](dashboard.md#trotzdem-scharf-schalten).

**Das Bedienfeld zeigt meinen Knopf nicht.**
Nur Profile mit zugeordnetem Bedienfeld-Knopf erscheinen dort. Alle anderen über Auswahlliste
„Profil“ + „Scharf schalten“.

**Einstellungen lassen sich nicht ändern.**
Nur möglich, wenn **alle Bereiche unscharf** sind.

## PIN und Bedienung

**Das Dashboard fragt plötzlich nach einem PIN.**
Sobald irgendein PIN existiert (auch der Master-PIN), verlangt das Bedienfeld ihn zum
Unscharfschalten von allen. Abhilfe: allen einen PIN geben, oder unter PIN-Regeln „Dashboard-Knöpfe
trotz PIN erlauben“ einschalten und die Hauswacht-Knöpfe statt der Alarmkarte verwenden. Siehe
[Benutzer](benutzer.md#das-wichtigste-vorab).

**„Zu viele falsche PIN-Eingaben“.**
Die [Sperre](benutzer.md#sperre-nach-falschen-eingaben) läuft (1–15 Minuten). Administratoren
setzen sie in der Testkarte mit „Falscheingaben zurücksetzen“ zurück. Fehlversuche verfallen
24 Stunden nach dem letzten.

**Die Knöpfe „Unscharf schalten“/„Alarm beenden“ sind nicht verfügbar.**
Mit PIN können Knöpfe keinen PIN abfragen und sind gesperrt – außer die PIN-Regeln erlauben sie.

## Keypad und Karten

**Das Keypad reagiert, aber Hauswacht bekommt keinen Code.**
In Zigbee2MQTT beim Keypad unter „Zustand“ bzw. im Log nachsehen: Steht dort `action_code: ""`,
schickt das Keypad den Code nicht mit.

- Reihenfolge beachten: erst PIN tippen bzw. Karte vorhalten, **dann** die Taste.
- Hilft das nicht, das Keypad in Zigbee2MQTT **entfernen und neu anlernen** (Batterie raus allein
  reicht manchmal nicht). Danach den alten Gerätenamen wieder vergeben, dann stimmt das
  MQTT-Topic in Hauswacht wieder.

**Eine Karte wird nicht zum Anlernen angeboten.**

- Waren alle Bereiche unscharf? Ist die Anlernzeit (Standard 5 Minuten) abgelaufen?
- Ist es eine **Zufallsnummer** (4 Byte, beginnt mit `08`, z. B. ein Handy)? Die ändert sich bei
  jedem Lesen und ist ungeeignet – der Benutzer-Dialog zeigt dann einen Hinweis.
- Hat die Karte nur 4–8 Ziffern? Dann könnte sie ein PIN sein und wird nie angezeigt – ID
  eintippen.
- Gehört die Karte schon einem Benutzer?

**Das Keypad piept nicht.**
Hauswacht antwortet auf jeden Tastendruck. Kommt keine Quittung, liegt es meist am Keypad selbst
(siehe oben: neu anlernen). Im HA-Log mit Debug für MQTT ist die Antwort an `<Topic>/set` zu
sehen.

**Kann ich nur mit Karte, ohne Taste, unscharf schalten?**
Mit einem Zigbee-Keypad nicht – es schickt die Kartennummer nur mit einem Tastendruck. Dafür gibt
es den [RFID-Leser](bedienteile.md#rfid-leser) oder [NFC-Aufkleber](bedienteile.md#nfc-aufkleber-companion-app).

## Sirenen

**Bei einem Alarm ertönt keine Sirene.**
Das Attribut `last_siren_decision` am Bedienfeld nennt den Grund. Häufig:

- Echte Sirenenansteuerung noch nicht freigegeben (Alarmgeber – Sirenen).
- Testmodus an.
- Profil auf „Stiller Alarm“ oder ohne Sirenen.
- Brandsperre: ein Rauchmelder meldet Brand oder ist nicht verfügbar.
- Die Sirene kann nur Brandtöne oder lässt sich nicht begrenzen, siehe
  [Welche Sirenen gehen?](sirenen.md#welche-sirenen-gehen).

## Melder

**Im Log steht „Hauswacht ignoriert Entitäten ohne offen/zu“.**
Ein Messwert-Sensor (z. B. Temperatur) steht in einer Meldergruppe oder Auslöseregel. Hauswacht
überwacht nur Melder mit offen/zu – entfernen oder mit dem Assistenten
[Melder aus anderem Sensor erstellen](melder.md#melder-aus-anderem-sensor-erstellen) einen
Schwellenwert-Melder daraus machen.

**Ein Melder gilt dauernd als ausgefallen.**
Die maximale Funkstille ist zu knapp für diesen Batteriesensor. Die
[Funkstille-Beobachtung](melder.md#funkstille-beobachtung-der-richtige-wert-aus-euren-daten)
empfiehlt einen passenden Wert.

## Karten im Dashboard

**Eine Hauswacht-Karte zeigt nach einem Update die alte Version.**
Seite neu laden; in der App Einstellungen → Companion App → Frontend-Cache zurücksetzen.

## Hilfe holen

Ein [Issue](https://github.com/schlusenbaum/hauswacht/issues) mit Hauswacht-Version,
Home-Assistant-Version und den passenden Log-Zeilen hilft am meisten. Bitte vorher Namen,
IP-Adressen, Tokens und andere persönliche Daten aus Logs entfernen.
