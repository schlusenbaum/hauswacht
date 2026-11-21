# Durchgang – rein oder raus, ohne unscharf zu schalten

**Deutsch** | [English](en/passage.md)

> **Vorabversion 0.59.0b1.** Reinkommen und Rausgehen am Keypad und per Aktion. Push-Knopf
> „Reinlassen“, automatisches Reinlassen per Handy sowie Türschloss, NFC-Aufkleber und
> Kartenleser folgen in den nächsten Vorabversionen.

Ein **Durchgang** lässt eine Tür kurz frei – das Profil **bleibt scharf**. Alle anderen Melder
lösen weiter aus.

Zwei typische Fälle:

- **Jemand kommt nachts heim.** „Nacht“ ist scharf, Finja öffnet die Haustür, die
  Eingangsverzögerung läuft. Sie gibt am Keypad ihren PIN ein und drückt eine Profil-Taste –
  kein Alarm, und das Haus bleibt in „Nacht“. Niemand muss danach wieder scharf schalten.
- **Kurz raus, z. B. den Müll rausbringen.** PIN und die Taste „Durchgang“ am Keypad – dann
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

Als **Tür** zählen alle Melder mit der Rolle **Eingang** (sie starten die Eingangsverzögerung).
Die Taste für den Durchgang legst du beim Keypad fest: Statt eines Profils wählst du
**„Durchgang (rein/raus, bleibt scharf)“** – bei jedem Keypad frei wählbar (siehe
[Bedienteile](bedienteile.md)).

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

**Kommen zwei nacheinander**, braucht jede neue Türöffnung ihren eigenen Ausweis: Ist die Tür
nach Finja zu, ist sie wieder scharf. Kommt Niklas drei Minuten später, läuft für ihn wieder die
Eingangsverzögerung.

## Rausgehen

1. Vorher am Keypad: **PIN oder Karte** und die **Durchgang-Taste**.
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
