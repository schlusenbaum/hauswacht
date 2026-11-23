# ADR 0014: Ausgangserkennung – Rausgehen ohne PIN erkennen

- Status: vorgeschlagen (Messung umgesetzt in 0.60.0, Umsetzung der Ausgangserkennung in 0.63 – vorher kommt ADR 0015)
- Datum: 2026-11-21
- Baut auf: [ADR 0013 Durchgang](0013-durchgang.md)

## Kontext

„Nacht“ ist scharf, Niklas geht aus dem Haus und **vergisst den PIN**. Die Haustür geht auf,
die Eingangsverzögerung läuft (30 s) – Niklas ist schon draußen, kommt nicht mehr ans Keypad,
bemerkt auch keine Push-Nachricht. Ergebnis: Alarm, Sirene, Nachbarn.

Hauswacht kann nicht unterscheiden, ob jemand **rein- oder rausgeht** – es sieht nur „Tür auf“.
Ein Bewegungsmelder im Haus (Hinweis „kommt von innen“) ist nicht überall vorhanden.

Was hilft: Die Anwesenheits-Signale jeder Person (Ping, WLAN der Companion App, Bluetooth über
Bermuda, GPS/Zone, Router), die Hauswacht schon für „Anwesenheit und Heimkehr“ kennt. **Wer
rausgeht, dessen Handy wird kurz danach „weg“.**

Grundsatz aus der Diskussion: **Ohne geöffnete Tür kann niemand weggehen.** Ein Handy, das
schweigt, ohne dass eine Tür aufging, ist zuhause (es schläft).

## Entscheidung

### 1. Alarm aufschieben, nie unterdrücken ohne Beleg

Neue Einstellung je Profil **„Rausgehen ohne PIN erkennen“** (Standard aus). Ist sie an und
geht eine Eingangstür auf, während mindestens eine Person **nachweislich zuhause** ist (frisches
Lebenszeichen eines ihrer Signale kurz vor dem Öffnen), dann:

1. Statt der Eingangsverzögerung beginnt eine **stille Wartezeit** (Standard 5 Minuten,
   einstellbar 1–15, mit Empfehlung aus der Messung). Keine Sirene.
2. **Sofort** kommt eine kritische Benachrichtigung: „Haustür geöffnet – wenn das keiner von euch
   war: **[Alarm jetzt]**“, dazu **[Durchlassen]**.
3. Während der Wartezeit bewertet Hauswacht je Person, die vor dem Öffnen zuhause war:
   - **Irgendein Signal sagt „zuhause“** (Ping antwortet, WLAN verbunden, Bluetooth sieht das
     Handy …) → die Person ist noch da.
   - **Alle Signale sagen „weg“ oder schweigen – über die ganze Wartezeit** → die Person ist
     rausgegangen.
4. Ende der Wartezeit:
   - mindestens eine Person ist rausgegangen → **kein Alarm**; die Tür wird wieder überwacht,
     sobald sie zu ist; Nachricht „Niklas (Handy) ist rausgegangen – Nacht bleibt scharf“.
   - sonst → **Alarm** (wie nach der Eingangsverzögerung).
5. PIN/Karte am Keypad, [Durchlassen] oder [Alarm jetzt] beenden die Wartezeit sofort.

Die Wartezeit muss länger sein als die längste Pause, in der eure Handys nachts schlafen und
nicht antworten: Ein schlafendes Handy meldet sich in der Zeit wieder (→ noch da → Alarm), ein
Handy, das das Haus verlassen hat, bleibt still.

### 2. Ohne Bewegungsmelder: bei jedem Öffnen

Ohne Melder im Haus gilt die Wartezeit für **jede** Türöffnung, solange jemand nachweislich
zuhause ist – **auch für einen echten Einbruch**: Der Alarm kommt dann erst nach der Wartezeit.
Das ist bewusst so gewählt; die Einstellung sagt es deutlich, und [Alarm jetzt] erlaubt jedem
Wachen, sofort auszulösen.

Optional **„Melder im Haus“** (z. B. Bewegungsmelder im Flur, nicht scharf): Ist er gesetzt,
gilt die Wartezeit nur, wenn er kurz vor dem Öffnen Bewegung gemeldet hat; sonst die normale
Eingangsverzögerung.

### 3. Schutz gegen Ausfall von WLAN oder Router

Fällt das WLAN aus, melden alle Handys gleichzeitig „weg“. Deshalb:

- Melden **mehrere Personen gleichzeitig** „weg“ und **nur** über WLAN-abhängige Signale (Ping,
  WLAN-Verbindung, Router), zählt das **nicht** als Beleg → Alarm.
- Vom WLAN unabhängige Signale (Bluetooth, GPS/Zone) zählen weiter.
- Empfehlung in der Doku: Router bzw. Fritzbox als [Infrastruktur](../../melder.md) überwachen.

### 4. Messung zuerst (0.60)

Die Heimkehr-Beobachtung wird um das **Weggehen** erweitert. Je Person und Signal:

- **Wie schnell** meldet es „weg“, nachdem die Person durch eine Tür rausgegangen ist?
- **Schweigepausen nachts**: Wie oft und wie lange meldet es „weg“ bzw. antwortet nicht, obwohl
  keine Tür aufging?

Daraus je Person: **Empfehlung für die Wartezeit** und ob sie **zuverlässig erkennbar** ist.
Nicht zuverlässig erkennbare Personen werden nicht ausgeschlossen, bekommen aber einen
**Warnhinweis** – und in den Empfehlungen der Einstellungsseite den Tipp, ein besseres Signal
einzurichten (z. B. Companion App mit WLAN-Sensor statt nur Ping).

### 5. Reihenfolge

| Version | Inhalt |
|---|---|
| 0.59.0 | Durchgang (ADR 0013) ausprobieren und veröffentlichen |
| 0.60 | Messung „Weggehen“ in der Beobachtung, Empfehlungen und Warnhinweise; ein, zwei Wochen laufen lassen |
| 0.63 | Ausgangserkennung mit den gemessenen Werten |

## Abwägung

- **Nur Ping:** schlafende iPhones antworten nicht → falsches „weg“ → ein Einbrecher käme ohne
  Alarm durch. Verworfen; alle Signale zusammen, ein Lebenszeichen genügt für „noch da“.
- **Alarm ganz unterdrücken, sobald jemand zuhause ist:** zu unsicher. Verworfen.
- **Längere Eingangsverzögerung für alle:** hilft Niklas, verzögert aber auch jeden Einbruch –
  ohne den Beleg „Handy ist weg“. Verworfen zugunsten der Wartezeit mit Beleg.
- **Nur mit Bewegungsmelder:** sicherer, aber nicht überall vorhanden. Als Option eingeplant.

## Folgen

- Bei Profilen mit eingeschalteter Ausgangserkennung kommt der Alarm bei einem echten Einbruch
  später (bis zur Wartezeit), solange jemand zuhause ist. Steht deutlich in Einstellung und
  Doku.
- Die Beobachtung sammelt mehr Daten (weiterhin nur Zeiten und Zählungen, keine Orte).
