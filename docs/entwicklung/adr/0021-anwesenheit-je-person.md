# ADR 0021: Anwesenheit je Person – Signale fürs Ankommen und Weggehen, mit „Was wäre wenn“

- Status: Diskussion (geplant für 0.66, noch nichts gebaut)
- Anlass: Rückmeldung aus dem eigenen Haushalt. „Scharf, wenn alle weg“ braucht teilweise mehr als
  15 Minuten, bis sicher feststeht, dass jemand weg ist. Zum Scharfschalten ist das zu lange. Die
  Einstellungen dafür sind auf drei Stellen verteilt und schwer zu durchschauen.

## Ausgangslage

Heute (0.65) entscheidet Hauswacht so:

- **Signale je Person** (System → Anwesenheit & Heimkehr): WLAN-Sensor, Ping, Bluetooth,
  Proximity, Tracker, Binärsensoren. **Zuhause** heißt, irgendein Signal sagt zuhause. **Weg**
  heißt, **alle** Signale sagen weg.
- **„Weg nur mit Beleg“** (ADR 0015, 0018): Zusätzlich braucht es eine frische Ortung außerhalb,
  eine Tür plus Ortung, ein als Ortung markiertes Geofence-Signal oder (unsicher, je Person
  erlaubt) „Tür + Signal“.
- **Profil → Automatik** „Scharf, wenn alle weg“: Personen plus Verzögerung (Standard
  15 Minuten), alternativ ein **eigener Auslöser** (ADR 0018).

Was wir gemessen haben:

- In unserem Haushalt meldet WLAN „weg“ nach etwa 40 s, Ping nach etwa 3 min, die Ortung der
  Handy-App nach 5–10 min, iCloud teils erst nach über 15 min. Weil **alle** Signale weg sein
  müssen, zählt immer das langsamste. Dazu kommt die Verzögerung im Profil.
- Wir haben „das erste Signal, das weg sagt, gewinnt“ (wie bei Alarmo) auf drei Tagen echter Daten
  nachgespielt. Das ergab 22 von 22 Fehlentscheidungen, 10 davon nachts. Mit der Bedingung
  „vorher war eine Tür auf“ waren es nur noch 5 von 5. Einzelne Personen mit nur einem
  unzuverlässigen Signal (nur Ping) irren sich auch dann.
- Bluetooth (Bermuda) sieht durch die Haustür. Es taugt fürs Ankommen, aber nicht fürs Weggehen.

Ergebnis: Ein einziger Regelsatz für alle passt nicht. Schnell und sicher hängen davon ab, welche
Signale eine Person hat und wie zuverlässig sie bei ihr sind. Genau das sieht man heute nicht.

## Entscheidung

### 1. Eine Seite pro Person

Unter System → Anwesenheit & Heimkehr bekommt jede Person eine Tabelle ihrer Signale. Pro Signal
gibt es:

| Spalte | Inhalt |
|---|---|
| **Ankommen** | Haken: zählt dieses Signal fürs Zuhause-Erkennen? |
| **Weggehen** | Haken: zählt dieses Signal fürs Weg-Erkennen? |
| **Jetzt** | aktueller Zustand des Signals |
| **Gemessen** | kurz: wie schnell es „weg“ meldet und wie oft es sich geirrt hat, z. B. „weg nach ~40 s · 0 Irrtümer“ |

Ein Beispiel: Anna nutzt WLAN, Ping, Bluetooth und die Ortung der Handy-App. Bluetooth hakt sie nur
bei **Ankommen** an, die Ortung nur bei **Weggehen**. Ben hat nur Ping und hakt es bei beiden an.

### 2. Regeln

- **Ankommen ist fest „eines reicht“.** Sobald ein angehaktes Signal zuhause sagt, ist die
  Person zuhause. Schnelles Erkennen beim Heimkommen macht nie einen Fehlalarm, es verhindert
  höchstens ein Scharfschalten.
- **Weggehen ist wählbar je Person:**
  - **„alle müssen weg sein“**: wie heute. Die Belege aus „Weg nur mit Beleg“ (Zeitfenster,
    Genauigkeit, Geofence) gelten weiter und wandern auf dieser Seite unter „Erweitert“.
  - **„eines reicht“**: Die Person ist weg, sobald **eine Tür auf und wieder zu war** und danach
    eines der angehakten Signale „weg“ sagt. Die Tür ersetzt hier den Beleg.
- **„Nach Tür“ ist abschaltbar**, aber standardmäßig an. Beim Abschalten erscheint ein
  deutlicher Hinweis: Ohne Tür reicht ein Handy, das nachts einschläft, um jemanden als weg zu
  zählen. In unserer Messung wäre das 10-mal in einer Nacht passiert.
- Unbekannt und nicht verfügbar zählen nie als weg.

### 3. „Was passiert“ in Klartext

Unter jeder Person steht ein Satz, der sich sofort mit den Haken ändert, z. B.:

> **Ankommen:** Anna gilt als zuhause, sobald WLAN, Ping oder Bluetooth sie sehen.
> **Weggehen:** Anna gilt als weg, sobald eine Tür auf und zu war und danach WLAN, Ping oder die
> Ortung „weg“ sagt. Laut Messung meist nach etwa einer Minute.

### 4. Empfehlung mit „Was wäre wenn“

Unter der Tabelle spielt Hauswacht die gespeicherten Messungen mit anderen Einstellungen nach und
zeigt den Vergleich. Er ändert sich **live**, sobald man einen Haken setzt:

```
Empfehlung für Anna: „eines reicht (nach Tür)“

                        Jetzt (alle müssen)   Mit Empfehlung
Als weg erkannt nach    ~9 min                ~45 s
Vermutlich fälschlich   0×                    0×
Grundlage: 6 Weggänge, 14 Tage

Ohne „nach Tür“:  vermutlich fälschlich 4×, davon 3× nachts
```

Für Personen mit nur einem unzuverlässigen Signal empfiehlt Hauswacht „alle müssen“ und sagt
warum, z. B. „Nur Ping, irrt sich etwa 2-mal pro Woche“.

### 5. Zeile fürs ganze Haus

Am Ende der Seite steht, was das für die Profile bedeutet, mit Empfehlung:

> Mit diesen Einstellungen wäre „Abwesend“ in den letzten 14 Tagen 5-mal scharf geworden, jeweils
> etwa 2 Minuten nach dem Letzten (heute etwa 12 Minuten). Vermutlich fälschlich: 0-mal.
> Empfehlung: Verzögerung im Profil von 15 auf 2 Minuten.

Die Empfehlung ist ein Vorschlag. Übernommen wird sie nur, wenn man es ausdrücklich bestätigt.
Abschwächende Vorschläge brauchen wie im Check-up (ADR 0017) eine Bestätigung.

### 6. Was dafür gemessen wird

- Hauswacht schreibt je Person und Signal mit, **wann** es von zuhause auf weg kippt und zurück,
  und **ob kurz davor eine Tür auf war**.
- **Irrtum** heißt: Ein Signal kippt auf weg und kommt **ohne Tür** wieder zurück.
- Gespeichert werden nur Uhrzeiten und Dauern, keine Orte und keine Koordinaten. Die Daten
  bleiben lokal im Speicher der Integration, werden über **14 Tage** ausgewertet und nach
  **30 Tagen** gelöscht. Der Export (ADR 0019) enthält sie nur zusammengefasst und mit
  Platzhaltern.
- Bei zu wenig Daten gibt es **keine Empfehlung**, sondern z. B. „Noch zu wenig Daten (3 von 5
  Weggängen)“.
- „Fälschlich“ ist eine Schätzung. Hauswacht weiß nicht sicher, ob jemand wirklich weg war, und
  schreibt deshalb „vermutlich“.

### 7. Was bleibt, wie es ist

- **Bestehende Einstellungen werden übernommen.** Jedes heutige Signal ist bei Ankommen und
  Weggehen angehakt, Weggehen steht auf „alle müssen“, „Weg nur mit Beleg“ und „Tür + Signal“
  wirken wie bisher. Wer nichts ändert, merkt keinen Unterschied.
- **Der eigene Auslöser je Profil** (ADR 0018) bleibt und gilt weiter statt der Personen.
- **„Haus leer“** heißt weiter: **alle** ausgewählten Personen sind weg. Die Wahl „eines reicht“
  gilt nur innerhalb einer Person, nie zwischen Personen.
- Automatisches Scharfschalten weiterhin nur aus „unscharf“, offene Melder werden nie automatisch
  bestätigt.
- **Durchgang** (ADR 0013), **Ausgangserkennung** (ADR 0014), **Bei Rückkehr** (ADR 0015),
  24h-Melder und Brandalarm werden nicht verändert. Diese Seite entscheidet nur, wer zuhause oder
  weg ist.
- **Ein Bewegungsmelder ist nicht nötig.** Die Seite kommt ohne ihn aus.

## Verworfen

- **„Das erste Signal, das weg sagt, gewinnt“** als Standard: in der Messung fast nur
  Fehlentscheidungen, vor allem nachts.
- **„Irrtum zurücknehmen“** (still unscharf, wenn kurz nach dem automatischen Scharfschalten ein
  Handy ohne Tür wieder zuhause ist): Mit „nach Tür“ und der Regel „alle weg“ bleibt kaum
  Restrisiko. Neue Logik ohne gemessenen Bedarf lassen wir weg. Wenn die Haus-Zeile echte
  Fehlentscheidungen zeigt, kann es nachgerüstet werden.
- **Bewegungsmelder als Pflicht** für schnelles Weggehen: Viele haben keinen. Als optionale
  Ergänzung bleibt er denkbar, ist aber nicht Teil dieser Entscheidung.
- **Modus „schnell/sicher“ je Person an einer eigenen Stelle** plus Innen-Melder je Tür plus
  Rücknahme je Profil: zu viele Orte, zu schwer zu durchschauen.

## Folgen

- Eine neue Ansicht unter System → Anwesenheit & Heimkehr ersetzt die bisherige Signalliste. Die
  Optionen `homecoming_signals`, `away_proof_*` werden übernommen bzw. aufgeteilt, ohne dass sich
  das Verhalten ändert.
- Der Kern bekommt eine reine Funktion für „Was wäre wenn“. Live-Erkennung und Vorschau nutzen
  dieselben Regeln.
- Die Messung „Lebenszeichen rund um die Tür“ zählt heute auch nach einer Rückkehr weiter.
  Das wird dabei behoben: Sie endet beim Weggehen oder bei der Rückkehr.
- Doku: Einstellungsseite, „So entscheidet Hauswacht“, Profile, Fehlersuche, jeweils deutsch und
  englisch, mit Beispielen (Anna, Ben).
- Tests: Übernahme alter Einstellungen ohne Verhaltensänderung, „nach Tür“ an/aus, unbekannt zählt
  nie als weg, „Haus leer“ nur bei allen, eigener Auslöser unverändert, keine Orte im Speicher.

## Offen

- Wie bindet die Ausgangserkennung (ADR 0014) die neue Regel „eines reicht (nach Tür)“ ein?
  Vermutlich gewinnt sie direkt an Tempo. Das klären wir beim Bauen.
- Welche Mindestzahl an Weggängen reicht für eine Empfehlung? Vorschlag: 5.
