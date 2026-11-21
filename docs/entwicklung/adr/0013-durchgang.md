# ADR 0013: Durchgang – rein oder raus, ohne unscharf zu schalten

- Status: angenommen, in Entwicklung (Zweig `entwicklung/durchgang`); Stufe 1 in 0.59.0b1
- Datum: 2026-11-21

## Kontext

Ein Profil wie „Nacht“ überwacht oft nur die Außenhaut: Haustür, Hintertür, vielleicht Fenster
im Erdgeschoss. Zwei Alltagsfälle passen dazu bisher schlecht:

1. **Jemand kommt nachts heim.** Damit es keinen Alarm gibt, muss heute jemand unscharf schalten
   – am Keypad, per Push-Knopf oder automatisch („Unscharf bei Rückkehr“). Danach ist das ganze
   Haus unscharf, bis jemand wieder scharf schaltet. Das wird oft vergessen.
2. **Man muss kurz raus**, etwa den Müll rausbringen. Heute: unscharf, raus, rein, wieder
   scharf – oder es gibt Alarm.

Was es schon gibt, hilft nicht:

- **„Unscharf bei Rückkehr“** schaltet das ganze Profil ab.
- **„Alarm beenden, scharf bleibt“** gibt es erst, wenn der Alarm schon läuft.
- **„Trotzdem scharf“** überbrückt offene Melder nur beim Scharfschalten.

Gewünscht ist: **Das Profil bleibt scharf, nur eine Tür darf kurz benutzt werden** – nach einem
Ausweis. Profi-Anlagen kennen das als „Durchgang“ bzw. „Einlass ohne Unscharfschaltung“.

## Entscheidung

### 1. Begriff und Grundsatz

Ein **Durchgang** lässt eine Tür (und frei gewählte Außenmelder auf dem Weg) kurz frei. Das
Profil bleibt scharf, alle anderen Melder lösen weiter aus. Zwei Richtungen:

| | **Reinkommen** (Einlass) | **Rausgehen** (Ausgang, z. B. Müll) |
|---|---|---|
| Wann | während der **Eingangsverzögerung** (oder direkt beim Öffnen, wenn das Handy schon vorher als daheim erkannt wurde) | wenn scharf, **vor** dem Öffnen |
| Welche Tür | die Tür, die gerade geöffnet wurde | die **erste** Eingangstür, die nach dem Start aufgeht – alle anderen bleiben scharf (einstellbar: alle Eingangstüren) |
| Wie lange | bis die Tür wieder zu ist | Durchgangszeit (Standard 5 Minuten, einstellbar); Ende einstellbar: nach Ablauf der Zeit oder schon, wenn man zurück ist und die Tür zu ist |
| Melder auf dem Weg | frei ab dem Einlass bis Tür zu **plus Nachlaufzeit** (Standard 60 s) | frei für die ganze Durchgangszeit |

Gedacht ist der Durchgang für **Außensensoren**: Profile, die nur die Außenhaut überwachen, und
Außenmelder auf dem Weg (Bewegungsmelder in der Einfahrt, am Gartentor, an den Mülltonnen).
Profile mit Meldern **im Haus** dürfen ihn trotzdem einschalten; die Einstellung sagt dann
deutlich: „Melder im Haus bleiben scharf – Durchgang hilft nur an den Außentüren.“

### 2. Ausweise

Ohne Ausweis gibt es keinen Durchgang – auch nicht mit „Tasten ohne PIN“.

| Ausweis | Reinkommen | Rausgehen |
|---|---|---|
| **PIN oder Karte am Keypad** + **irgendeine Profil-Taste** (wer heimkommt, weiß oft nicht, welches Profil aktiv ist) | ✅ während der Eingangsverzögerung: „schon gut, bleib scharf“ – das **laufende** Profil bleibt, es wird nicht gewechselt | – |
| **PIN oder Karte** + eigene **Durchgang-Taste** (frei wählbar je Keypad, wie die Profil-Tasten) | ✅ | ✅ |
| **Push-Knopf [Reinlassen]** neben [Unscharf] in der Eingangs-Nachricht (Home-Assistant-Benutzer mit Recht, wie „Unscharf über Push-Knopf“) | ✅ | – |
| **Türschloss** (Nuki): Aufsperren durch einen berechtigten Benutzer, wenn das Schloss auf „Durchgang“ statt „Unscharf“ eingestellt ist | ✅ | ✅ (Aufsperren vor dem Öffnen) |
| **NFC-Aufkleber / Kartenleser** mit der Aktion „Durchgang“ | ✅ | ✅ |
| **Handy** (automatisch, siehe 3.) | ✅ | – |
| Aktion `hauswacht.passage` (Dashboard-Knopf, Automationen; nur Administratoren und Automationen) | ✅ | ✅ |

Für alle gilt wie bisher: Fehlversuche zählen zur Sperre, Rechte je Bereich und Benutzer.

### 3. Handy-Reinlassen (automatisch)

Eigener Block **„Durchgang“** im Profil mit eigener **Personenliste** – unabhängig von „Scharf,
wenn alle weg“. Die Erkennung ist dieselbe wie bei „Unscharf mit Türbeleg“:

- Eine freigegebene Person **kommt heim** (war vorher sicher weg, mindestens 5 Minuten) und
- eine Eingangstür geht auf,
- das Handy meldet sich **bis zu x Minuten vor** dem Öffnen (Zeitfenster, Standard 5 Minuten)
  **oder danach, solange die Eingangsverzögerung läuft**.

Dann lässt Hauswacht rein statt unscharf zu schalten. Kommt das Handy erst nach Ablauf der
Eingangsverzögerung, bleibt der **Alarm ein Alarm** (wird nicht automatisch beendet).

Zusätzlich fest:

- **Eine Heimkehr lässt einmal rein.** Für die nächste Türöffnung muss das Handy erst wieder weg
  gewesen sein.
- **„Unscharf mit Türbeleg“ und Handy-Reinlassen schließen sich im selben Profil aus** – die
  Einstellung lässt nur eins zu und sagt das.
- Die [Heimkehr-Beobachtung](../../beobachtung.md) gilt für beide: Sie sagt je Person, wie lang
  die Eingangsverzögerung sein muss, damit das Handy rechtzeitig erkannt wird.

> **Restrisiko** (steht so in der Doku): Wer das Handy einer freigegebenen Person **und** Zugang
> zur Tür hat, kommt ohne Alarm rein. Die Nachricht „… (Handy) hereingelassen“ macht das sofort
> sichtbar.

### 4. Mehrere Personen und Türen

- Zwei kommen zusammen: ein Einlass, die Tür ist frei, bis sie zu ist.
- Zwei kommen kurz nacheinander: **jede neue Türöffnung braucht ihren eigenen Ausweis.**
- Rausgehen: nur die erste geöffnete Tür wird frei (einstellbar: alle Eingangstüren).
- Mehrere Bereiche: Der Durchgang gilt nur im Bereich der Tür.

### 5. Ende und Warnung

- Ist eine Tür am Ende noch offen, bleibt sie überbrückt, **bis sie zu ist** – kein Alarm,
  sondern eine deutliche **Warnung**: „Hintertür nach Durchgang noch offen – wird nicht
  überwacht, bis sie zu ist.“ (Gerade ein Kontakt, der fälschlich „offen“ meldet, darf nicht
  nachts Alarm auslösen – unbewacht bleibt die Tür dann aber auch; deshalb die deutliche
  Warnung.)
- Melder auf dem Weg, die am Ende noch auslösen (z. B. Bewegung), bleiben ebenfalls überbrückt,
  bis sie wieder in Ruhe sind.
- Unscharf schalten beendet jeden Durchgang.

### 6. Zusammenspiel

| Fall | Verhalten |
|---|---|
| **Bedrohungs-PIN** | Nach außen ein normaler Durchgang (keine Anzeige, kein Ton), im Hintergrund still der Bedrohungsalarm an die Bedrohungs-Empfänger – wie beim Unscharfschalten |
| **Gastmodus** | Durchgang funktioniert normal, auch Handy-Reinlassen |
| **Testmodus** | Durchgang funktioniert normal (zum gefahrlosen Ausprobieren) |
| **Laufender Alarm** | kein Durchgang – dafür gibt es „Alarm beenden“ |
| **Ausgangsverzögerung** | kein Durchgang (nichts zu tun) |
| **Neustart** | Ein laufender Durchgang endet; offene Türen bleiben wie beim Wiederherstellen bis zum Schließen überbrückt |

### 7. Anzeige und Nachrichten

- Das Bedienfeld bleibt im Zustand des Profils (z. B. „scharf – Nacht“). Attribute:
  `passage` (Richtung, Türen, Melder, bis wann). Karte, Einstellungsseite und Keypad-Anzeige
  zeigen „Nacht – Durchgang bis 08:35“.
- Neues Benachrichtigungs-Ereignis **„Durchgang“** (Standard an), z. B. „Finja (Handy)
  hereingelassen – Nacht bleibt scharf“, „Christian: Durchgang 5 Minuten – Nacht bleibt
  scharf“. Die Nachricht ersetzt eine laufende Eingangs-Nachricht. Die Warnung „noch offen“
  kommt über dasselbe Ereignis.
- Ereignisse für Automationen: `PassageGranted`, `PassageStarted`, `PassageEnded`,
  `PassageDoorOpen` (jeweils mit Richtung, Tür, wer, wie).

### 8. Technik

- **Zustandsmaschine (reiner Kern):** zwei neue Ereignisse.
  - `PassageIn(door, path)` – nur in ARMED/PENDING: Eingangsverzögerung abbrechen, zurück nach
    ARMED (Ursache `passage`), Tür bis zum Schließen überbrückt, Wegmelder zeitlich überbrückt.
  - `PassageBypass(sensors)` / `PassageEnd(sensors, still_open)` – zeitliche Überbrückung für
    den Ausgang und das Ende; noch offene Melder wechseln auf „bis zum Schließen“.
  - Kontext bekommt `passage: frozenset[str]` (zeitlich überbrückt). Unscharf leert alles.
- **Runtime:** Zeiten (Durchgangszeit, Nachlauf), „erste Tür“ beim Ausgang, Nachrichten,
  Anzeige.
- **Keypad-Kern (ADR 0012):** neues Tastenziel „Durchgang“; jede Profil-Taste während der
  Eingangsverzögerung = Einlass (das laufende Profil bleibt). Gilt für Zigbee2MQTT-Keypad, allgemeines Keypad,
  MQTT-Schnittstelle.
- **Profil-Optionen** (Block `passage`): `enabled`, `duration` (Minuten), `out_doors`
  (`first`/`all`), `out_end` (`time`/`closed`), `path` (Melder), `path_after` (Sekunden),
  `persons`, `window` (Minuten).
- Prüfungen in `core/changes/`, Einstellungsseite **und** Dialog (ADR 0011).

## Abwägung

- **Ganz unscharf und automatisch wieder scharf** („unscharf für x Minuten“): einfacher, aber
  das ganze Haus wäre in der Zeit offen – auch die Hintertür, während man vorne bei den Tonnen
  steht. Verworfen.
- **Feste Durchgangstür:** sicher, aber unpraktisch, wenn man mal vorne, mal hinten geht.
  Ersetzt durch „erste geöffnete Tür“.
- **Handy-Reinlassen als vierte Stufe von „Unscharf bei Rückkehr“:** weniger Einstellungen,
  aber die Personenliste wäre an „alle weg“ gebunden und der Durchgang auf zwei Stellen
  verteilt. Verworfen zugunsten eines eigenen Blocks.
- **Handy nach Ablauf der Eingangsverzögerung beendet den Alarm:** bequemer, aber die Sirene
  lief dann schon, und das Fenster nützte auch Einbrechern. Verworfen.

## Folgen

- Mehr Einstellungen im Profil – deshalb ein eigener, zugeklappter Block, standardmäßig aus.
- Der Keypad-Kern, die Push-Knöpfe, Schloss, Aufkleber und Leser bekommen ein neues Ziel.
- Doku: neue Seite „Durchgang“ (deutsch und englisch) mit Beispielen, Restrisiko und
  Empfehlung der Eingangsverzögerung.

## Umsetzung in Stufen (Vorabversionen)

| Version | Inhalt |
|---|---|
| 0.59.0b1 | Kern (Zustandsmaschine), Profil-Block mit Prüfungen (Seite und Dialog), Einlass und Ausgang am Keypad (alle Keypad-Arten), Aktion `hauswacht.passage`, Wegmelder, Ende/Warnung, Nachrichten, Anzeige, Doku |
| 0.59.0b2 | Push-Knopf [Reinlassen], Handy-Reinlassen mit eigener Personenliste |
| 0.59.0b3 | Türschloss, NFC-Aufkleber, Kartenleser mit Aktion „Durchgang“ |
| 0.59.0 | nach Test im Alltag |
