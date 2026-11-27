# Durchgang – rein oder raus, ohne unscharf zu schalten

**Deutsch** | [English](en/passage.md)

Ein **Durchgang** lässt eine Tür kurz frei – das Profil **bleibt scharf**. Alle anderen Melder
lösen weiter aus.

Zwei typische Fälle:

- **Jemand kommt nachts heim.** „Nacht“ ist scharf, Finja öffnet die Haustür, die
  Eingangsverzögerung läuft. Sie gibt am Keypad ihren PIN ein und drückt eine Profil-Taste –
  kein Alarm, und das Haus bleibt in „Nacht“. Niemand muss danach wieder scharf schalten.
- **Kurz raus, z. B. den Müll rausbringen.** PIN und eine Profil-Taste am Keypad – dann
  darf eine Haustür 5 Minuten lang auf und zu gehen. Alles andere bleibt scharf, auch die
  Hintertür.

Gedacht ist der Durchgang für Profile, die **nur die Außenhaut** überwachen (Türen, Fenster).
Melder **im Haus** (z. B. Bewegungsmelder im Flur) bleiben scharf – der Durchgang hilft dann nur
an den Außentüren.

## Einschalten

Im Profil unter **Durchgang** (Einstellungsseite → Profile → Bearbeiten):

| Einstellung | Bedeutung | Standard |
|---|---|---|
| Durchgang erlauben | Ohne das gibt es in diesem Profil keinen Durchgang | aus |
| Durchgangszeit | Rausgehen: so lange ist die Tür frei. Reinkommen: so lange darf die Tür offen stehen, bevor die Warnung kommt | 5 Minuten (1–60) |
| Rausgehen: welche Tür | **Nur die erste Tür, die aufgeht** – alle anderen bleiben scharf. Oder **alle Eingangstüren** | nur die erste |
| Rausgehen: Ende | **Nach Ablauf der Zeit** (man kann mehrmals raus und rein) oder **schon, wenn ich zurück bin und die Tür zu ist** (die Tür ging zum zweiten Mal zu: raus und zurück) | nach Ablauf der Zeit |
| Melder auf dem Weg | Außenmelder, die auf dem Weg auslösen würden – z. B. ein Bewegungsmelder in der Einfahrt, am Gartentor oder an den Mülltonnen | keine |
| Reinkommen: Weg noch frei nach dem Schließen | So lange bleiben die Melder auf dem Weg noch frei, nachdem die Tür zu ist | 60 Sekunden |

Als **Tür** zählen alle Melder mit der Rolle **Eingang** (sie starten die Eingangsverzögerung).
Eine eigene Taste brauchst du nicht: Während das Profil scharf ist oder die Eingangsverzögerung
läuft, öffnet **jede Profil-Taste** mit PIN oder Karte den Durchgang. Hast du eine Taste frei,
kannst du ihr beim Keypad statt eines Profils **„Durchgang (rein/raus, bleibt scharf)“** geben
(siehe [Bedienteile](bedienteile.md)).

## Reinkommen

So läuft es ab:

1. Die Haustür geht auf, die Eingangsverzögerung läuft.
2. Am Keypad: **PIN oder Karte** und **irgendeine Profil-Taste** (oder die Durchgang-Taste).
   Wer heimkommt, weiß ja oft nicht, welches Profil gerade aktiv ist – deshalb zählt jede.
   Das **laufende** Profil bleibt; es wird nicht gewechselt.
3. Die Eingangsverzögerung endet, die Anlage bleibt scharf. Die **geöffnete Tür** ist frei,
   **bis sie wieder zu ist**. Die Melder auf dem Weg sind frei, bis die Tür zu ist und dann noch
   die Nachlaufzeit (Standard 60 Sekunden).
4. Die Nachricht „Finja (Keypad Flur) hereingelassen (Haustür) – Profil Nacht bleibt scharf“
   ersetzt die Nachricht zur Eingangsverzögerung.

Mit PIN und **„Unscharf“** wird wie bisher ganz unscharf geschaltet.

### Reinlassen per Push-Knopf

Ist „Unscharf über Push-Knopf“ an (siehe [Benachrichtigungen](benachrichtigungen.md)), hat die
Nachricht zur Eingangsverzögerung neben **[Unscharf]** auch **[Reinlassen]** – sofern das Profil
den Durchgang erlaubt. Wer tippt, muss als Home-Assistant-Benutzer **unscharf schalten** dürfen
(wie beim Knopf „Unscharf“).

Beispiele: Finja steht an der Tür und tippt selbst auf „Reinlassen“. Oder du liegst im Bett, das
Handy zeigt „Haustür geöffnet“, du siehst, dass es Niklas ist, und tippst „Reinlassen“. Es muss
während der Eingangsverzögerung passieren; danach ist es ein Alarm.

### Reinlassen per Handy

*Seit 0.61 eingestellt unter [Bei Rückkehr](profile.md#bei-rückkehr) → Stufe
**„Reinlassen (Durchgang)“** (Einstellungsseite → Profil). Personen und Zeitfenster stehen dort;
„Durchgang erlauben“ muss dafür nicht eingeschaltet sein.*

Bei „Reinlassen (Durchgang)“ lässt Hauswacht die gewählten Personen **ohne PIN** herein, wenn
ihr Handy heimkommt. Die Erkennung ist dieselbe wie bei
[„Unscharf mit Türbeleg“](profile.md#bei-rückkehr) – nur dass am Ende nicht unscharf
geschaltet, sondern hereingelassen wird; das Profil bleibt scharf:

- Die Person **kommt heim**: Sie war vorher **mindestens 5 Minuten sicher weg** und ist jetzt
  zuhause (Personen-Entität plus die Signale unter „Anwesenheit und Heimkehr“). Ein Handy, das
  die ganze Nacht im Haus liegt, öffnet also nichts.
- Eine **Eingangstür** geht auf.
- Das Handy meldet sich **bis zu x Minuten vor dem Öffnen** (Zeitfenster, Standard 5 Minuten)
  **oder danach, solange die Eingangsverzögerung läuft**.

| Was passiert | Ergebnis (Eingangsverzögerung 30 s, Zeitfenster 5 Minuten) |
|---|---|
| Handy meldet „zuhause“, 2 Minuten später geht die Tür auf | Beim Öffnen **hereingelassen** |
| Tür geht auf, 20 s später meldet das Handy „zuhause“ | Nach 20 s **hereingelassen** |
| Tür geht auf, das Handy meldet sich erst nach 45 s | Nach 30 s **Alarm** wie immer; das Handy beendet ihn nicht |
| Handy meldet „zuhause“, erst 7 Minuten später geht die Tür auf | Zu lange her: normale Eingangsverzögerung |
| Person war nur 2 Minuten weg | Zählt nicht als Heimkehr: normale Eingangsverzögerung |

- **Eine Heimkehr lässt einmal rein.** Für die nächste Türöffnung muss das Handy erst wieder weg
  gewesen sein.
- Die Nachricht lautet z. B. „Finja (Handy) hereingelassen (Haustür) – Profil Nacht bleibt
  scharf“ – ein Reinlassen, das nicht stimmt, fällt so sofort auf.
- **Nur eins von beiden:** „Bei Rückkehr“ hat genau eine Stufe – entweder „Unscharf mit
  Türbeleg“ oder „Reinlassen“. Dieselbe Heimkehr kann nicht zugleich unscharf schalten und nur
  reinlassen.
- **Welche Eingangsverzögerung brauche ich?** Meldet sich das Handy oft erst nach dem Öffnen,
  muss die Eingangsverzögerung so lange reichen. Die
  [Heimkehr-Beobachtung](beobachtung.md#empfehlung-für-unscharf-mit-türbeleg) rechnet das je
  Person aus – der Wert gilt hier genauso.

> **Restrisiko:** Wer das Handy einer freigegebenen Person **und** Zugang zur Tür hat (z. B.
> Handy und Schlüssel gestohlen), kommt ohne Alarm herein. Für Profile wie „Urlaub“ deshalb
> „Bei Rückkehr“ auf **Nichts** lassen.

**Kommen zwei nacheinander**, braucht jede neue Türöffnung ihren eigenen Ausweis: Ist die Tür
nach Finja zu, ist sie wieder scharf. Kommt Niklas drei Minuten später, läuft für ihn wieder die
Eingangsverzögerung.

## Rausgehen

1. Vorher am Keypad: **PIN oder Karte** und **irgendeine Profil-Taste** – oder die
   Durchgang-Taste, falls du eine hast. Solange das Profil scharf ist, schaltet eine Profil-Taste
   **nie** auf ein anderes Profil um; wer wechseln will, schaltet erst unscharf. So geht der
   Durchgang auch, wenn alle Tasten mit Profilen belegt sind.
2. Die Nachricht „Christian (Keypad Flur): Durchgang für 5 Minuten – Profil Nacht bleibt scharf“
   kommt.
3. Die **erste Eingangstür, die jetzt aufgeht**, ist für die Durchgangszeit frei – du kannst
   mehrmals raus und rein. Alle anderen Türen bleiben scharf (Einstellung „alle Eingangstüren“:
   jede).
4. Die Melder auf dem Weg sind die ganze Zeit frei.
5. Am Ende (Zeit um, oder – je nach Einstellung – du bist zurück und die Tür ist zu) wird alles
   wieder überwacht.

**Beispiel:** Profil „Nacht“, Durchgangszeit 5 Minuten, „nur die erste Tür“. Du drückst PIN und
Durchgang, gehst vorne raus. Während du an den Tonnen stehst, öffnet jemand die Hintertür → ganz
normal Eingangsverzögerung und Alarm. Die Hintertür war nie frei.

## Tür nach dem Durchgang noch offen

Ist eine Tür am Ende noch offen, gibt es **keinen Alarm**, sondern eine **Warnung**:

> Haustür nach dem Durchgang noch offen – wird nicht überwacht, bis sie zu ist. Profil Nacht
> bleibt scharf.

Die Tür bleibt frei, **bis sie zu ist** – danach wird sie wieder überwacht. Das gilt auch für
einen Melder auf dem Weg, der am Ende noch Bewegung meldet.

> **Achtung bei Kontakten, die fälschlich „offen“ melden:** Dann bleibt die Tür unbewacht,
> obwohl sie zu ist. Die Warnung zeigt das. Prüfe den Kontakt (oft sitzt der Magnet zu weit weg).

## Rausgehen ohne PIN erkennen (Ausgangserkennung)

*Ab 0.66.0b9* ([ADR 0014](entwicklung/adr/0014-ausgangserkennung.md)). Das Sicherheitsnetz für
alle, die den Durchgang vergessen.

**Beispiel:** „Nacht“ ist scharf. Ben geht morgens um 6 Uhr zur Arbeit und vergisst PIN und
Durchgang. Ohne Ausgangserkennung läuft die Eingangsverzögerung ab, und es gibt Alarm – Ben ist
längst an der Bushaltestelle. Mit Ausgangserkennung merkt Hauswacht, dass Bens Handy kurz nach
der Tür „weg“ ist, und lässt „Nacht“ einfach scharf.

**Einschalten:** Einstellungsseite → Profile → Profil (z. B. „Nacht“) → Abschnitt **Durchgang** →
**„Rausgehen ohne PIN erkennen“**. Standard: aus. Die Eingangstür braucht eine
Eingangsverzögerung (Typ Tür), sonst gibt es nichts aufzuschieben.

Es gibt zwei Wege – je nachdem, ob ein **Melder im Haus** eingetragen ist:

| | Mit Melder im Haus (empfohlen) | Ohne Melder im Haus |
|---|---|---|
| Woran Hauswacht erkennt, dass jemand rausgeht | Der Melder im Haus meldete kurz vor dem Öffnen etwas – jemand kam **von innen** | Das Handy einer Person, die zuhause war, sagt danach „weg“ |
| Was dann passiert | **Automatischer Durchgang:** Die Tür ist für die Durchgangszeit frei – raus **und wieder rein** | Stille Wartezeit; erst wenn das Handy „weg“ sagt, bleibt das Profil scharf |
| Mülleimer, Briefkasten (Handy bleibt im WLAN) | ✅ kein Alarm | ❌ Alarm nach der Wartezeit – dafür den Durchgang nutzen |
| Zur Arbeit | ✅ | ✅ |
| Einbruch von außen | normale Eingangsverzögerung (drinnen hat sich nichts bewegt) | Sirene erst nach der Wartezeit |

### Mit Melder im Haus: automatischer Durchgang

*Ab 0.66.0b12.* Hat der Melder im Haus **höchstens 2 Minuten vor dem Öffnen** etwas gemeldet, kam
jemand von innen. Dann passiert dasselbe wie mit der Durchgang-Taste „rausgehen“: Die Tür, die
aufging, ist für die **Durchgangszeit** des Profils (Standard 5 Minuten) frei – raus und wieder
rein, so oft man will. Das Profil bleibt scharf, alles andere wird weiter überwacht. Ein Handy
braucht es dafür nicht.

Alle Alarm-Empfänger bekommen sofort: „Haustür von innen geöffnet (Melder im Haus) – Durchgang für
5 min, Nacht bleibt scharf. Wenn das keiner von euch war: **[Alarm jetzt]**“.

*Beispiel:* Der Bewegungsmelder an der Treppe ist als Melder im Haus eingetragen, „Nacht“ ist
scharf. Anna geht die Treppe runter, bringt den Müll raus und kommt nach 2 Minuten zurück – kein
Alarm. Wer nach der Durchgangszeit zurückkommt, braucht wie sonst PIN, Karte oder „Bei Rückkehr“.

> Restrisiko: Bricht genau in diesen Minuten jemand von außen durch **dieselbe** Tür ein, kommt er
> ohne Alarm herein. Wer drinnen ist, bekommt aber sofort die Nachricht mit [Alarm jetzt].

### Ohne Melder im Haus: stille Wartezeit

Eine Eingangstür geht auf, das Profil ist scharf, und **mindestens eine Person ist nachweislich
zuhause** – eines ihrer Weggehen-Signale sagt gerade „zuhause“ (siehe
[Welche Signale zählen?](profile.md#ankommen-und-weggehen-je-signal)). Dann:

1. Statt der Eingangsverzögerung läuft eine **stille Wartezeit** (Standard 3 Minuten). Keine
   Sirene.
2. **Sofort** bekommen **alle Alarm-Empfänger** eine wichtige Nachricht: „Tür geöffnet – war das
   jemand von euch?“ mit den Knöpfen **[Alarm jetzt]** und **[Durchlassen]**.
3. Hauswacht schaut, ob die Weggehen-Signale einer dieser Personen „weg“ sagen – mit ihren Regeln
   unter „Welche Signale zählen?“: bei **„eines reicht“** ein Signal, bei **„alle müssen weg
   sein“** alle (die Tür gilt hier als Beleg, eine Ortung braucht es nicht).
4. Bleibt das **30 Sekunden** so, ist die Person **rausgegangen**: kein Alarm, das Profil bleibt
   scharf, die Tür wird bis zum Schließen überbrückt. Alle Alarm-Empfänger bekommen „Ben ist
   rausgegangen – Nacht bleibt scharf“. Kommt das Signal in den 30 Sekunden zurück, war es ein
   Aussetzer.
5. Ist bis zum Ende der Wartezeit **niemand** rausgegangen: **Alarm** – wie nach der
   Eingangsverzögerung.
6. **[Alarm jetzt]** löst sofort aus (jeder Empfänger darf das). **[Durchlassen]** (nur mit
   Push-Knopf und gültigem Benutzer), PIN, Karte oder Keypad beenden die Wartezeit ebenfalls.

### Melder im Haus – empfohlen

> ⚠️ **Ohne Melder im Haus gilt die stille Wartezeit für jede Öffnung der Eingangstür, solange
> jemand zuhause ist – auch für einen Einbruch.** Die Sirene käme dann erst nach der Wartezeit.
> Die Nachricht mit [Alarm jetzt] kommt trotzdem sofort.

Darum: Trag einen **Melder im Haus** ein – einen Bewegungsmelder im Flur oder an der Treppe, das
Treppenlicht, einen Schalter. Er muss nicht scharf sein. Bricht jemand nachts die Haustür auf,
ohne dass vorher drinnen etwas gemeldet hat, läuft die normale Eingangsverzögerung – Alarm wie
immer.

**Ausprobieren** ohne Sirene im [Testmodus](testmodus.md#so-funktioniert-die-simulation): Melder
im Haus in der Testkarte auf „an“, dann die Tür auf „offen“ → das Profil bleibt scharf, die Tür
ist frei. Ohne Melder im Haus: Tür auf, dann unter „Anwesenheit testen“ die Person auf „weg“.

Der Assistent zeigt im Check-up eine Warnung, solange die Ausgangserkennung ohne Melder im Haus
läuft, und die Szenario-Vorschau spielt „Einbruch durch die Haustür, während jemand zuhause ist“
durch.

### Wartezeit

| Einstellung | Wert |
|---|---|
| **Wartezeit** (nur ohne Melder im Haus) | 1 bis 5 Minuten, Standard 3. So lange bliebe ein Einbruch ohne Melder im Haus höchstens still. Die Messung „Weggehen“ zeigt unter System → Anwesenheit, wie schnell eure Handys nach der Tür „weg“ sagen |
| **Länger als 5 Minuten** (unter „Mehr Einstellungen“, Expertenoption) | bis 15 Minuten – mit deutlichem Warnhinweis |

### Was sicher bleibt

- **Wer nicht zuhause war, kann nicht rausgehen.** Sagt beim Öffnen niemand „zuhause“, gilt die
  normale Eingangsverzögerung.
- **WLAN-Ausfall:** Sagen mehrere Personen fast gleichzeitig nur über WLAN-abhängige Signale
  (Ping, Router, WLAN-Sensor der App) „weg“, ist eher das WLAN weg – das zählt **nicht** als
  rausgegangen. Bluetooth und Ortung zählen weiter.
- **Durchgang hat Vorrang:** Wer ihn nutzt, für den läuft alles wie bisher.
- Die Ausgangserkennung **schaltet nie unscharf**, hält keine laufende Sirene an und ändert
  nichts an Brandalarm, 24h-Meldern, Sabotage und Fenstern.

## Was sonst gilt

| Fall | Verhalten |
|---|---|
| **Ausweis** | Immer nötig – auch wenn „Tasten ohne PIN“ an ist. Falsche PINs zählen zur Sperre wie sonst |
| **Recht** | Wer **unscharf schalten** darf (im Bereich), darf auch einen Durchgang öffnen |
| **Bedrohungs-PIN** | Nach außen ein normaler Durchgang; still geht der Bedrohungsalarm an die Bedrohungs-Empfänger |
| **Gastmodus** | Durchgang funktioniert normal |
| **Testmodus** | Durchgang funktioniert normal – zum gefahrlosen Ausprobieren |
| **Laufender Alarm** | Kein Durchgang – dafür gibt es „Alarm beenden“ |
| **Ausgangsverzögerung** | Kein Durchgang |
| **Unscharf schalten** | Beendet jeden Durchgang |
| **Mehrere Bereiche** | Der Durchgang gilt im Bereich des Keypads; läuft dort irgendwo die Eingangsverzögerung, wird nur dort hereingelassen |
| **Neustart** | Ein laufender Durchgang endet; offene Türen werden wie nach jedem Neustart behandelt |
| **Auslöseregeln** | Was der Durchgang freigibt, zählt auch für Regeln nicht |

## Anzeige und Nachrichten

- Das Bedienfeld bleibt „scharf – Nacht“. Die Alarm-Karte zeigt darunter „Durchgang bis 22:35 –
  frei: Haustür, Bewegung Einfahrt“.
- Attribut `passage` am Bedienfeld und an der Anzeige-Entität allgemeiner Keypads (siehe
  [Referenz](referenz.md#attribute-des-bedienfelds)).
- Nachrichten über das Ereignis **„Durchgang“** unter [Benachrichtigungen](benachrichtigungen.md)
  (Standard: an). „Durchgang für 5 Minuten“ und die Warnung „noch offen“ ersetzen einander und
  verschwinden, wenn der Durchgang ohne Warnung endet oder unscharf geschaltet wird.
- Ereignisse für Automationen: `PassageGranted`, `PassageDoorUsed`, `PassageEnded`,
  `PassageDoorOpen` (siehe [Referenz](referenz.md#ereignisse)).

## Türschloss, NFC-Aufkleber, Kartenleser

Beim [Türschloss](bedienteile.md#türschloss-z-b-nuki) stellst du **„Aufschließen bei scharf:
Durchgang“** ein, beim [NFC-Aufkleber](bedienteile.md#nfc-aufkleber-companion-app) und
[RFID-Leser](bedienteile.md#rfid-leser) die **Aktion „Durchgang“**. Dann gilt:

| Zustand | Aufschließen, Aufkleber scannen oder Karte vorhalten |
|---|---|
| Eingangsverzögerung läuft, Profil erlaubt Durchgang | **Reinkommen** – Tür frei, bis sie zu ist |
| Scharf, Profil erlaubt Durchgang | **Rausgehen** – die erste Tür, die danach aufgeht, ist frei |
| Scharf, Profil erlaubt **keinen** Durchgang | **Unscharf** wie bisher |
| Unscharf | nichts |

Beispiel: Das Nuki an der Haustür steht auf „Durchgang“. Nachts ist „Nacht“ scharf (mit
Durchgang): Finja schließt mit ihrer Nuki-App auf – Hauswacht lässt sie herein, „Nacht“ bleibt.
Tagsüber ist „Abwesend“ scharf (ohne Durchgang): Aufschließen schaltet unscharf.

## Per Aktion oder Dashboard-Knopf

```yaml
action: hauswacht.passage
target:
  entity_id: alarm_control_panel.hauswacht
data:
  code: "1234"   # nötig, wenn PINs eingerichtet sind
```

Läuft die Eingangsverzögerung, wird hereingelassen, sonst beginnt ein Durchgang zum Rausgehen.
Geht gerade kein Durchgang (Profil erlaubt ihn nicht, unscharf, Alarm), meldet die Aktion das als
Fehler.
