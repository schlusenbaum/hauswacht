# Durchgang – rein oder raus, ohne unscharf zu schalten

**Deutsch** | [English](en/passage.md)

> **Vorabversion 0.59.0b3.** Alle Wege sind dabei: Keypad, Aktion, Push-Knopf „Reinlassen“,
> automatisch per Handy, Türschloss, NFC-Aufkleber und Kartenleser.

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

Im Profil unter **Durchgang** (Einstellungsseite → Profile, oder im Einstellungsdialog beim
Profil):

| Einstellung | Bedeutung | Standard |
|---|---|---|
| Durchgang erlauben | Ohne das gibt es in diesem Profil keinen Durchgang | aus |
| Durchgangszeit | Rausgehen: so lange ist die Tür frei. Reinkommen: so lange darf die Tür offen stehen, bevor die Warnung kommt | 5 Minuten (1–60) |
| Rausgehen: welche Tür | **Nur die erste Tür, die aufgeht** – alle anderen bleiben scharf. Oder **alle Eingangstüren** | nur die erste |
| Rausgehen: Ende | **Nach Ablauf der Zeit** (man kann mehrmals raus und rein) oder **schon, wenn ich zurück bin und die Tür zu ist** (die Tür ging zum zweiten Mal zu: raus und zurück) | nach Ablauf der Zeit |
| Melder auf dem Weg | Außenmelder, die auf dem Weg auslösen würden – z. B. ein Bewegungsmelder in der Einfahrt, am Gartentor oder an den Mülltonnen | keine |
| Reinkommen: Weg noch frei nach dem Schließen | So lange bleiben die Melder auf dem Weg noch frei, nachdem die Tür zu ist | 60 Sekunden |
| Handy-Reinlassen: diese Personen | Diese Personen lässt Hauswacht ohne PIN herein, wenn ihr Handy heimkommt – siehe [Reinlassen per Handy](#reinlassen-per-handy) | keine (aus) |
| Handy darf so lange vor der Tür „zuhause“ melden | Zeitfenster für das Handy-Reinlassen | 5 Minuten (1–30) |

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

Unter **„Handy-Reinlassen: diese Personen“** wählst du Personen, die Hauswacht **ohne PIN**
hereinlässt, wenn ihr Handy heimkommt. Die Erkennung ist dieselbe wie bei
[„Unscharf mit Türbeleg“](profile.md#unscharf-bei-rückkehr) – nur dass am Ende nicht unscharf
geschaltet, sondern hereingelassen wird:

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
- **Nicht zusammen mit „Unscharf mit Türbeleg“** im selben Profil: Dieselbe Heimkehr kann nicht
  zugleich unscharf schalten und nur reinlassen. Die Einstellung lässt nur eins zu.
- **Welche Eingangsverzögerung brauche ich?** Meldet sich das Handy oft erst nach dem Öffnen,
  muss die Eingangsverzögerung so lange reichen. Die
  [Heimkehr-Beobachtung](beobachtung.md#empfehlung-für-unscharf-mit-türbeleg) rechnet das je
  Person aus – der Wert gilt hier genauso.

> **Restrisiko:** Wer das Handy einer freigegebenen Person **und** Zugang zur Tür hat (z. B.
> Handy und Schlüssel gestohlen), kommt ohne Alarm herein. Für Profile wie „Urlaub“ deshalb
> besser keine Personen eintragen.

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
