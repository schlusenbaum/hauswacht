# ADR 0014: Ausgangserkennung – Rausgehen ohne PIN erkennen

- Status: angenommen (Messung umgesetzt in 0.60.0, ergänzt in 0.63.1; Ausgangserkennung wird in
  0.66 umgesetzt, Fassung vom 2026-11-27 auf Grundlage von ADR 0021)
- Datum: 2026-11-21, überarbeitet 2026-11-27
- Baut auf: [ADR 0013 Durchgang](0013-durchgang.md),
  [ADR 0021 Anwesenheit je Person](0021-anwesenheit-je-person.md)

## Kontext

„Nacht“ ist scharf, Ben geht früh aus dem Haus und **vergisst den PIN** und den Durchgang. Die
Haustür geht auf, die Eingangsverzögerung läuft (30 s) – Ben ist schon draußen, kommt nicht mehr
ans Keypad, bemerkt auch keine Push-Nachricht. Ergebnis: Alarm, Sirene, alle wach.

Hauswacht kann nicht unterscheiden, ob jemand **rein- oder rausgeht** – es sieht nur „Tür auf“.

Was hilft: die Anwesenheits-Signale jeder Person. **Wer rausgeht, dessen Handy ist kurz danach
„weg“.** Seit ADR 0021 legt jede Person fest, welche Signale fürs Weggehen zählen und ob „eines
reicht (nach Tür)“ – gemessen und mit Empfehlung. Genau das braucht die Ausgangserkennung.

Grundsatz: **Ohne geöffnete Tür kann niemand weggehen.** Und: **Wer nicht zuhause war, kann
nicht rausgehen.**

Was es heute schon gibt: der **Durchgang** (ADR 0013) – Taste am Keypad oder Push-Knopf
„rausgehen“, das Profil bleibt scharf. Die Ausgangserkennung ist das **Sicherheitsnetz** für den
Fall, dass man ihn vergisst.

## Entscheidung

### 1. Einstellung je Profil, Standard aus

Im Profil (Abschnitt Durchgang) **„Rausgehen ohne PIN erkennen“**, Standard **aus**. Gedacht vor
allem für „Nacht“. Wer sie nicht einschaltet, merkt keinen Unterschied.

### 2. Ablauf

Eine **Eingangstür** des Profils geht auf, das Profil ist scharf, und mindestens eine Person hat
ein **frisches Lebenszeichen** (ein Signal sagte bis höchstens 3 Minuten vor dem Öffnen
„zuhause“). Dann:

1. Statt der Eingangsverzögerung beginnt eine **stille Wartezeit**. Keine Sirene.
2. **Sofort** geht eine kritische Benachrichtigung an **alle Alarm-Empfänger** des Profils:
   „Haustür geöffnet – wenn das keiner von euch war: **[Alarm jetzt]**“, dazu **[Durchlassen]**.
3. Während der Wartezeit gelten für jede Person, die vorher zuhause war, **dieselben Regeln wie
   unter „Welche Signale zählen?“** (ADR 0021): ihre Weggehen-Signale, „eines reicht (nach Tür)“
   oder „alle müssen weg sein“. Bei „alle müssen“ reicht hier „alle Weggehen-Signale weg“ –
   einen Ortungs-Beleg verlangt die Ausgangserkennung nicht, die Tür ist der Beleg.
4. **Jemand ist als rausgegangen erkannt** → nach einem kleinen Puffer von **30 Sekunden** (kommt
   das Signal in der Zeit zurück, war es ein Aussetzer) endet die Wartezeit **sofort**: **kein
   Alarm**, das Profil bleibt scharf, die Tür wird wieder überwacht, sobald sie zu ist. Nachricht
   an die Alarm-Empfänger: „Ben ist rausgegangen – Nacht bleibt scharf“.
5. **Niemand ist rausgegangen**, wenn die Wartezeit abläuft → **Alarm** (wie nach der
   Eingangsverzögerung).
6. PIN, Karte, Keypad, **[Durchlassen]** oder **[Alarm jetzt]** beenden die Wartezeit sofort.

### 3. Wartezeit

- Empfehlung aus der Messung „Weggehen“ (wie schnell die Signale nach der Tür „weg“ sagen, mit
  Puffer).
- Einstellbar **1 bis 5 Minuten**. So lange bliebe ein echter Einbruch höchstens still.
- **Länger als 5 Minuten** (bis 15) nur unter „Mehr Einstellungen“ als **Expertenoption** mit
  deutlichem Warnhinweis.

### 4. Melder im Haus – empfohlen, nicht Voraussetzung

Optional je Profil **„Melder im Haus“** (Bewegungsmelder, Treppenlicht, Keypad-Taste …, nicht
scharf). Ist einer gesetzt, gilt die stille Wartezeit **nur**, wenn er kurz vor dem Öffnen (bis
2 Minuten) drinnen etwas gemeldet hat – jemand kam also von innen. Sonst läuft die normale
Eingangsverzögerung, ein Einbruch von außen wird wie bisher behandelt.

**Ohne Melder im Haus** gilt die Wartezeit für **jede** Öffnung der Eingangstür, solange jemand
nachweislich zuhause ist – **auch für einen Einbruch**: Die Sirene käme dann erst nach der
Wartezeit (die Push-Nachricht mit [Alarm jetzt] sofort). Das steht

- als Warnhinweis direkt an der Einstellung,
- als Warnung im Check-up mit der Empfehlung, einen Melder im Haus einzutragen,
- als Szenario in der Vorschau („Einbruch durch die Haustür, während jemand schläft“).

### 5. Schutz gegen Ausfall von WLAN oder Router

Melden **mehrere Personen gleichzeitig** (bis 60 Sekunden auseinander) „weg“ und dabei **nur**
über WLAN-abhängige Signale (Ping, WLAN-Verbindung, Router), zählt das **nicht** als
„rausgegangen“ → Alarm. Vom WLAN unabhängige Signale (Bluetooth, Ortung) zählen weiter.

### 6. Was unberührt bleibt

- Brandalarm, 24h-Melder, Sabotage, Fenster und Türen, die keine Eingangstür sind.
- **Durchgang hat Vorrang:** Wer ihn nutzt, für den läuft alles wie bisher.
- Die Ausgangserkennung schaltet nie unscharf und hält nie eine Sirene an, die schon läuft.
- Im Testmodus wie alles andere: keine Sirene.

### 7. Messung (umgesetzt 0.60 und 0.63.1)

Die Heimkehr-Beobachtung misst das Weggehen (wie schnell „weg“, Schweigepausen ohne Tür) und
„Lebenszeichen rund um die Tür“ (Lebenszeichen vor dem Rausgehen, „noch da“ nach der Tür,
Nachklang). Daraus kommen die Empfehlung für die Wartezeit und die Hinweise, wer zuverlässig
erkannt wird.

## Abwägung

- **Nur Ping:** schlafende iPhones antworten nicht → falsches „weg“. Verworfen; es gelten die
  Weggehen-Signale je Person aus ADR 0021.
- **Alarm ganz unterdrücken, sobald jemand zuhause ist:** zu unsicher. Verworfen.
- **Längere Eingangsverzögerung für alle:** verzögert jeden Einbruch ohne Beleg. Verworfen.
- **Melder im Haus als Voraussetzung:** sicherer, aber nicht überall vorhanden. Verworfen als
  Pflicht, **empfohlen** mit Warnhinweis ohne.
- **Volle Wartezeit abwarten, auch wenn jemand schon rausgegangen ist:** sicherer gegen
  Aussetzer, aber die Tür bliebe lange unüberwacht. Stattdessen 30 Sekunden Puffer.
- **Nachricht nur an Personen, die zuhause sind:** verworfen – alle Alarm-Empfänger sollen sofort
  [Alarm jetzt] drücken können.

## Folgen

- Bei Profilen mit eingeschalteter Ausgangserkennung **ohne Melder im Haus** kommt die Sirene
  bei einem echten Einbruch später (bis zur Wartezeit), solange jemand zuhause ist. Steht
  deutlich in Einstellung, Check-up, Szenario-Vorschau und Doku.
- Der Kern bekommt eine reine Entscheidung „wer ist rausgegangen“ mit denselben Regeln wie die
  Anwesenheit (ADR 0021); Echtbetrieb und Vorschau nutzen sie.
- Doku (deutsch und englisch) mit Beispiel: Ben geht bei scharfer Nacht raus, Annas
  Bewegungsmelder an der Treppe als „Melder im Haus“.
- Tests: Einbruch ohne Lebenszeichen → normale Eingangsverzögerung; mit Melder im Haus ohne
  Bewegung → normale Eingangsverzögerung; Ben geht raus → kein Alarm; niemand geht → Alarm nach
  der Wartezeit; WLAN-Ausfall bei allen → Alarm; Aussetzer kürzer als 30 s → kein „rausgegangen“;
  Durchgang, Brand und 24h unverändert; Wartezeit über 5 Minuten nur als Expertenoption.
