# ADR 0015: Rückkehr neu geregelt – „Bei Rückkehr“, „weg“ nur mit Beleg, Annäherung

- Status: vorgeschlagen (Umsetzung in 0.61)
- Datum: 2026-11-23
- Baut auf: [ADR 0013 Durchgang](0013-durchgang.md), [ADR 0014 Ausgangserkennung](0014-ausgangserkennung.md)
- Ändert: [ADR 0011 Einstellungsseite](0011-einstellungsseite.md) (Nachtrag 0.61)

## Kontext

Was bei einer Rückkehr passiert, ist heute an zwei Stellen eines Profils eingestellt, die sich
gegenseitig ausschließen:

- **Automatik → „Unscharf bei Rückkehr“** (aus, „wie bisher“, „mit Türbeleg“). Es gilt für die
  Personen von **„Scharf, wenn alle diese Personen weg sind“**. Wer unscharf bei Rückkehr will,
  bekommt dadurch zwangsläufig auch das automatische Scharfschalten.
- **Durchgang → Handy-Reinlassen** mit eigener Personenliste.

„Mit Türbeleg“ und Handy-Reinlassen gehen im selben Profil nicht zusammen (ADR 0013). Das merkt
man erst beim Speichern – im Betrieb sah das aus, als würde das Profil nicht gespeichert.

Die Beobachtung (0.58–0.60) hat außerdem gezeigt:

- **Falsche Heimkehrten:** Ein Handy, das nachts schweigt, gilt heute als „weg“. Meldet es sich
  wieder, sieht das aus wie eine Heimkehr (Finjas Ping schwieg bis zu 12 Stunden, Niklas' bis zu
  7½). Deshalb ist „unscharf bei Rückkehr“ heute nur abgesichert möglich.
- **Späte Erkennung:** Das Handy meldet „zuhause“ manchmal erst lange nach der Tür (gemessen bis
  70 s). Mit 30 s Eingangsverzögerung gäbe es bei „mit Türbeleg“ oder „reinlassen“ Alarm.
- **Richtung:** „nähert sich“ kommt oft Minuten vor der Tür, heißt aber nicht „ist da“ (Fahrten in
  der Umgebung). Seit 0.60 zählt es deshalb nicht mehr als „zuhause“ – und ist damit fast nutzlos.

Die Einstellungen werden umfangreich; ohne gute Erklärung setzt man sie kaum richtig.

## Entscheidung

### 1. „Bei Rückkehr“ – eine Einstellung je Profil

Neuer Abschnitt **„Bei Rückkehr“** im Profil. Eine Auswahl, eine eigene Personenliste:

| Auswahl | Was passiert, wenn eine Person der Liste heimkommt |
|---|---|
| **nichts** | nichts (Standard) |
| **unscharf, nur wenn automatisch scharf** | unscharf – aber nur, wenn die Automatik scharf geschaltet hat (wie heute „wie bisher“) |
| **unscharf mit Türbeleg** | unscharf, wenn Handy-Ankunft und Türöffnung im Zeitfenster liegen (wie heute) |
| **unscharf, auch nach Scharfschalten von Hand** | unscharf bei Rückkehr, egal wer scharf geschaltet hat, **ohne Tür** – mit Warnhinweis (siehe Restrisiko) |
| **reinlassen (Durchgang)** | das Profil bleibt scharf, die Tür, durch die man kommt, ist frei (wie heute Handy-Reinlassen) |

- **Personenliste:** eigenständig, unabhängig von „Scharf, wenn alle weg“.
- **Zeitfenster** zwischen Handy-Ankunft und Tür: Standard 5 Minuten, einstellbar (wie heute).
- **Je Profil, nicht je Person:** Was sinnvoll ist, hängt von der Lage ab (nachts schlafen andere
  → reinlassen; alle weg → unscharf), nicht davon, wer heimkommt.
- Damit gibt es keinen Widerspruch mehr zwischen Türbeleg und Handy-Reinlassen: Es gilt immer
  genau eine Auswahl.
- **Durchgang:** Handy-Reinlassen zieht hierher um. Keypad, Push-Knopf „Reinlassen“, Türschloss,
  NFC-Aufkleber und Kartenleser bleiben beim Durchgang.
- **Umstellung beim Update:** „Unscharf bei Rückkehr“ und Handy-Reinlassen werden automatisch in
  „Bei Rückkehr“ übernommen (mit den Personen der bisherigen Liste). Es geht nichts verloren. War
  beides gesetzt (z. B. „wie bisher“ und Handy-Reinlassen), gewinnt **„reinlassen“** mit dessen
  Personenliste – es lässt das Profil scharf, also die sichere Seite. Ein Hinweis nach dem Update
  sagt, was umgestellt wurde.

### 2. „weg“ nur mit Beleg – für die ganze Automatik

Grundsatz aus ADR 0014: **Ohne geöffnete Tür kann niemand weggehen.**

Eine Person gilt für die Automatik erst als **weg**, wenn

1. eine **Eingangstür aufging** und
2. das Handy danach **außerhalb geortet** wurde – innerhalb von 15 Minuten (einstellbar).

| Zählt als „außerhalb geortet“ | Bestätigt nur, reicht allein nicht |
|---|---|
| GPS bzw. Zone „nicht zuhause“ (Companion App, iCloud3 …) | WLAN getrennt |
| die Person „nicht zuhause“, wenn das aus einer Ortung kommt | Ping antwortet nicht |
| | Bluetooth sieht das Handy nicht |

- Ein schlafendes Handy macht niemanden abwesend – also gibt es auch **keine falsche Heimkehr**.
- Gilt für **„Scharf, wenn alle weg“**, **„Bei Rückkehr“** (jede Auswahl) und das Reinlassen.
- **Wer nicht außerhalb geortet werden kann** (z. B. Standort in der App abgeschaltet), gilt nie
  als weg. Hinweis direkt an der Einstellung („Niklas kann nicht als weg erkannt werden – keine
  Ortung“) und als Prüfhinweis. „Scharf, wenn alle weg“ wartet mit so einer Person in der Liste
  für immer – das ist die sichere Seite.
- **Zurück** ist eine Person, sobald ein Signal wieder „zuhause“ meldet (wie heute, Richtung nur
  mit „angekommen“).

### 3. Annäherung verlängert die Eingangsverzögerung

Die Richtung (Nähe, Places) schaltet **nie** selbst unscharf. Sie gibt dem echten Signal mehr Zeit:

> Hat sich eine Person aus der Liste „Bei Rückkehr“ in den letzten **15 Minuten** genähert und
> geht dann eine Tür auf, wartet Hauswacht **länger** auf ihr Handy-Signal, z. B. 90 s statt 30 s.
> Ein Einbrecher, vor dem sich niemand genähert hat, hat weiter nur die normale Zeit.

- Gilt nur bei **„unscharf mit Türbeleg“** und **„reinlassen“** – nur dort entscheidet das
  Handy-Signal nach der Tür.
- **Verlängerung:** je Profil einstellbar, mit Empfehlung aus der Messung (längste Zeit von
  „Tür auf“ bis „zuhause“ der Personen, plus Puffer) und Knopf „übernehmen“.
- **Gültigkeit** der Annäherung: Standard 15 Minuten, einstellbar, mit Empfehlung aus der Messung
  (Zeit von „nähert sich“ bis zur Tür).
- Die Beobachtung zeigt dafür je Person die passenden Werte.

### 4. Erklärungen direkt an der Einstellung (für die neuen Einstellungen in 0.61)

- **ⓘ je Feld:** mit der Maus ein kurzer Text beim Darüberfahren; Antippen oder Anklicken klappt
  ihn unter dem Feld auf (Handy, Tablet). Ein, zwei Sätze.
- **„So verhält sich das“:** ein Klartext-Satz je Abschnitt, der sich mit der Einstellung ändert,
  z. B. „Kommt Christian oder Petra heim und geht innerhalb von 5 Minuten eine Tür auf, wird
  ‚Nacht‘ nicht unscharf, sondern die Tür ist frei – das Haus bleibt scharf. Hat sich das Handy
  vorher genähert, wartet Hauswacht bis zu 90 s auf das Handy-Signal.“
- **Empfehlung am Feld** mit Knopf „übernehmen“; **Warnung am Feld**, nicht erst beim Speichern.
- **„Mehr Einstellungen“** zum Aufklappen: immer sichtbar sind Auswahl und Personen; Zeitfenster,
  Gültigkeit und Verlängerung liegen darunter.
- Die übrigen Einstellungen bekommen das in 0.62.

### 5. Nur auf der Einstellungsseite

„Bei Rückkehr“ gibt es nur auf der Einstellungsseite. Der Einstellungsdialog zeigt an dieser Stelle
einen Hinweis mit Link zur Seite (Nachtrag 0.61 zu ADR 0011).

## Restrisiko

- **unscharf, auch nach Scharfschalten von Hand:** Wer wirklich weg war, zurückkommt, aber nicht
  hereingeht (steht in der Einfahrt, fährt wieder los), schaltet das Haus unscharf – und es bleibt
  leer und unscharf. Darum mit Warnhinweis und nicht Standard. Mit Türbeleg oder „reinlassen“
  passiert das nicht.
- **reinlassen und Türbeleg:** Öffnet im Zeitfenster jemand anderes eine Tür, während das Handy
  vor dem Haus ist, wird er reingelassen bzw. es wird unscharf (wie heute, siehe Durchgang).
- **Annäherung:** Einbruch genau dann, wenn sich eine Person aus der Liste nähert – der Alarm
  kommt um die Verlängerung später.
- **Gestohlenes Handy:** wirkt wie die Person selbst (wie heute).

## Abwägung

- **Aktion je Person** (z. B. Eltern unscharf, Kinder reinlassen): verworfen – die Lage (Profil)
  entscheidet, nicht die Person; je Profil ist einfacher.
- **„weg“ wie bisher, wenn alle Signale weg melden:** verworfen – schlafende Handys erzeugen
  falsche Heimkehrten.
- **Eingangsverzögerung für alle verlängern:** verworfen – schenkt auch jedem Einbrecher die Zeit.
- **„nähert sich“ wieder als „zuhause“:** verworfen (Sicherheitskorrektur 0.60).
- **Nur Mouseover als Erklärung:** verworfen – am Handy und Tablet gibt es kein Darüberfahren.

## Folgen

- Bestehende Profile werden beim Update umgestellt; das Verhalten bleibt gleich, außer dass „weg“
  jetzt einen Beleg braucht. Wer keine Ortung außerhalb hat, wird nicht mehr automatisch als weg
  erkannt – Hinweis in der Einstellung und als Prüfhinweis.
- Die Beobachtung zählt „weg“ und „zurück“ ebenfalls mit Beleg, damit Messung und Automatik
  übereinstimmen.
- Doku: Profile, Durchgang, Beobachtungen, Einstellungsseite, Referenz (Optionen, Ereignisse) –
  deutsch und englisch, mit Beispielen.

## Reihenfolge

| Version | Inhalt |
|---|---|
| 0.61 | diese ADR; Nachtrag ADR 0011 (Seite ausblenden statt abschalten, Aufruf über das Gerät, neue Einstellungen nur auf der Seite) |
| 0.62 | ⓘ, „So verhält sich das“ und „Mehr Einstellungen“ für alle übrigen Einstellungen |
| 0.63 | Ausgangserkennung ([ADR 0014](0014-ausgangserkennung.md)) |
| später | Einrichtungsassistent auf die Seite; Dialog nur noch Wegweiser |
