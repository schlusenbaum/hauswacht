# Assistent und Einrichtung

**Deutsch** | [English](en/setup-wizard.md)

> **Seit 0.63.2 gibt es den früheren Einrichtungsassistenten nicht mehr.** Er lebte im
> Einstellungsdialog (Einstellungen → Geräte & Dienste → Hauswacht → Konfigurieren), und den gibt
> es nicht mehr – alles wird auf der [Einstellungsseite](einstellungsseite.md) eingerichtet.
> Deine Einstellungen bleiben dabei unverändert.

## Wie richte ich Hauswacht jetzt ein?

1. Zuerst den Überblick lesen: [So entscheidet Hauswacht](so-entscheidet-hauswacht.md) – was
   passiert, wenn eine Tür aufgeht, wann die Automatik schaltet, was beim Heimkommen passiert.
2. Dann der kürzeste Weg zur ersten Scharfschaltung:
   [In fünf Schritten](installation.md#in-fünf-schritten-zur-ersten-scharfschaltung) – Meldergruppe,
   Alarmprofil, Benachrichtigung, Testmodus, echt.
3. Alles Weitere nach Bedarf, jeweils auf der Einstellungsseite: [Benutzer und PINs](benutzer.md),
   [Bedienteile](bedienteile.md), [Auslöseregeln](ausloeseregeln.md), [Sirenen](sirenen.md),
   [Anwesenheit und Automatik](profile.md#automatik).

Jedes Feld auf der Einstellungsseite hat ein **ⓘ** mit Erklärung, und wo es hilft, steht ein Satz
**„So verhält sich das:“** mit einem Beispiel.

## Hinweise beim Bearbeiten (seit 0.64.0b2)

Der Assistent schaut **mit**, während du einstellst. Im Seitenblatt eines **Alarmprofils** und im
Seitenblatt **System → Anwesenheit** steht über „Speichern“ ein Kasten **Assistent**, sobald
etwas nicht zusammenpasst. Geprüft wird dein **Entwurf** – also so, wie es nach dem Speichern
wäre. Gespeichert wird dabei nichts, geschaltet auch nicht.

- Der Kasten ist **nur ein Hinweis**. Speichern geht trotzdem – du entscheidest.
- Jeder Hinweis sagt in einem Satz, **was** nicht passt. Unter **„Warum?“** steht die Begründung,
  wenn es sie gibt mit **Messwert** aus der [Beobachtung](beobachtung.md).
- Viele Hinweise haben einen **Vorschlag** als Knopf. Ein Klick ändert nur den Entwurf im
  Seitenblatt – gespeichert wird erst mit **Speichern**.
- Vorschläge mit **⚠** machen die Anlage an einer Stelle **nachgiebiger** (z. B. eine längere
  Eingangsverzögerung = späterer Alarm). Die musst du in einer Rückfrage ausdrücklich bestätigen.
- Gehört ein Vorschlag an eine andere Stelle (z. B. „Tür + Signal“ beim Profil), steht er nur als
  Text da: „Vorschlag: … (an anderer Stelle ändern)“.

Hinweise der Stufe **Fehler** stehen zusätzlich in den [Prüfhinweisen](uebersicht.md#prüfhinweise)
– also auch dann, wenn du gerade kein Seitenblatt offen hast.

### Was geprüft wird

| Hinweis | Stufe | Vorschlag |
|---|---|---|
| Eine Person in **„Scharf, wenn alle weg“** kann nie als weg erkannt werden (keine Ortung, „Tür + Signal“ aus, Weggehen nicht auf „eines reicht“) – das Profil wird so **nie** automatisch scharf | ⛔ Fehler | Person aus der Liste nehmen, oder ⚠ „Tür + Signal“ für sie erlauben |
| **„Unscharf, nur wenn automatisch scharf“**, aber das Profil hat keine Automatik (keine Uhrzeit, kein Zeitplan, kein „alle weg“) | ⛔ Fehler | – |
| **„Unscharf mit Türbeleg“** oder **„Reinlassen“**, aber das Profil hat keine Eingangstür (Melder vom Typ Tür) | ⛔ Fehler | – |
| Eine Person in **„Bei Rückkehr“** kann nie als weg erkannt werden – für sie greift „Bei Rückkehr“ nie | ⚠️ Warnung | Person aus der Liste nehmen, oder ⚠ „Tür + Signal“ erlauben |
| **Eingangsverzögerung** kürzer als gemessen nötig (Tür auf → unscharf, mit Puffer) | ⚠️ Warnung | ⚠ Eingangsverzögerung auf den gemessenen Wert |
| **Eingangsverzögerung** reicht nicht für den **Türbeleg** einer Person (Handy meldet „zuhause“ erst nach der Tür) | ⚠️ Warnung | ⚠ Eingangsverzögerung auf den gemessenen Wert |
| **„Eingangsverzögerung bei Annäherung“** ist an, aber keine Person der Liste hat ein Richtungs-Signal | ⚠️ Warnung | Verlängerung ausschalten |
| Eine **Ortung meldet seit mindestens 24 Stunden exakt dieselbe Position** außerhalb von Zuhause (vorgetäuscht oder hängende App) – sie zählt nicht als Beleg ([mehr](profile.md#weg-nur-mit-beleg)) | ⚠️ Warnung | – (bei dauerhaft falscher Ortung: unter System → Anwesenheit aus den Signalen nehmen) |
| **„Scharf, wenn alle weg“ folgt einem eigenen Auslöser** (Entität statt Personen) – Hauswacht prüft dann nicht selbst ([mehr](profile.md#eigener-auslöser-für-alle-weg)) | ⚠️ Warnung | – |
| **Ausgangserkennung** ist an, aber das Profil hat keine Eingangsverzögerung – sie greift nie ([mehr](durchgang.md#rausgehen-ohne-pin-erkennen-ausgangserkennung), ab 0.66.0b9) | ⛔ Fehler | – |
| **Ausgangserkennung ohne Melder im Haus** – auch ein Einbruch durch die Eingangstür gibt erst nach der Wartezeit Alarm, solange jemand zuhause ist (ab 0.66.0b9) | ⚠️ Warnung | – (Melder im Haus im Profil eintragen) |
| Ein **eigener Auslöser** ist gesetzt, aber bei „Scharf, wenn alle weg“ sind noch Personen angehakt – sie werden nicht beachtet ([mehr](profile.md#eigener-auslöser-für-alle-weg), ab 0.66.0b3) | 💡 Tipp | Personen abwählen |
| Für eine Person ist unter **Anwesenheit** etwas eingestellt (Signale, Haken, „Weggehen erkennen“), aber sie zählt **nirgends**: in keinem „Scharf, wenn alle weg“ ohne eigenen Auslöser, in keinem „Bei Rückkehr“, nicht in der Beobachtung (ab 0.66.0b3) | 💡 Tipp | – |
| **„Tür + Signal“** ist an, obwohl die Person eine Ortung hat | 💡 Tipp | „Tür + Signal“ ausschalten |

Messwerte zählen erst ab **3 Messungen** – vorher sagt der Assistent dazu nichts.

**Beispiel:** Im Profil „Abwesend“ steht Ben in „Scharf, wenn alle weg“. Ben teilt seinen Standort
nicht. Der Assistent zeigt:

> ⛔ **Fehler:** Profil Abwesend: Ben kann nie als weg erkannt werden – „Scharf, wenn alle weg“
> schaltet dieses Profil nie.
> [Ben aus „Scharf, wenn alle weg“ nehmen]
> Vorschlag: Für Ben „Tür + Signal“ erlauben (unsicher) (an anderer Stelle ändern)

**Beispiel mit Messung:** Eingangsverzögerung 30 s, an der Haustür hat das Unscharfschalten in
5 Messungen bis zu 36 s gedauert:

> ⚠️ **Warnung:** Profil Abwesend: Eingangsverzögerung 30 s ist kürzer als gemessen nötig (45 s).
> [⚠ Eingangsverzögerung auf 45 s setzen]

## Check-up im Reiter „Assistent“ (seit 0.64.0b3)

Auf der [Einstellungsseite](einstellungsseite.md) gibt es den Reiter **Assistent**. Dort steht der
**Check-up**: alle Befunde des Assistenten auf einen Blick – dieselbe Prüfung wie in den
Seitenblättern (siehe oben), aber für **alle** Profile und die allgemeinen Einstellungen auf
einmal, ohne dass du ein Seitenblatt öffnen musst.

- Oben steht die Zusammenfassung, z. B. „1 Fehler · 2 Warnungen · 0 Tipps“ – oder „Alles passt
  zusammen“.
- Darunter die Befunde, **nach Profil** sortiert; allgemeine Befunde (z. B. „Tür + Signal“)
  stehen unter **Allgemein**.
- **Neu prüfen** holt den aktuellen Stand, z. B. nachdem neue Messwerte dazugekommen sind.

### Einen Vorschlag übernehmen

1. Klick auf den Vorschlag (z. B. „Eingangsverzögerung auf 50 s setzen“). Es öffnet sich eine
   **Vorschau**: wo sich etwas ändert (Profil oder System → Anwesenheit) und was – bei Zahlen
   „bisher → neu“, bei Listen „kommt dazu“ oder „fällt weg“.
2. **Übernehmen** speichert genau diese eine Änderung. Hauswacht lädt danach neu, und der
   Check-up ist aktualisiert.
3. **Abbrechen** schließt die Vorschau, es ändert sich nichts.

Vorschläge mit **⚠** machen die Anlage an einer Stelle nachgiebiger (z. B. längere
Eingangsverzögerung = späterer Alarm, oder „Tür + Signal“ = unsicherer Beleg für „weg“). Bei
ihnen ist **Übernehmen** erst möglich, wenn du das Häkchen „Ich habe das verstanden …“ setzt.

**Beispiel:** Profil Nacht, Eingangsverzögerung 30 s. An der Haustür hat das Unscharfschalten in 4
Messungen bis zu 36 s gedauert. Der Check-up zeigt:

> ⚠️ **Warnung:** Profil Nacht: Eingangsverzögerung 30 s ist kürzer als gemessen nötig (50 s).
> [⚠ Eingangsverzögerung auf 50 s setzen]

Klick darauf zeigt „bisher: **30** → neu: **50**“, den Warnhinweis und das Häkchen. Erst mit
Häkchen und **Übernehmen** wird gespeichert.

### Was der Assistent dabei garantiert

- Er ändert **nichts von selbst** – nur, was du einzeln übernimmst.
- Er schaltet nichts, löst keine Sirene aus und fasst Rauchmelder und Brandalarm nicht an.
- Übernehmen geht nur, wenn **alle Bereiche unscharf** sind.
- Hauswacht prüft beim Übernehmen noch einmal, ob der Vorschlag **jetzt noch** gilt. Hat sich
  inzwischen etwas geändert (auch an anderer Stelle), wird nichts gespeichert, und der Check-up
  lädt neu.
- Gespeichert wird über denselben Weg wie im Seitenblatt – mit allen Prüfungen, die dort gelten.

## Was passiert, wenn …? (seit 0.64.0b4)

Unter dem Check-up steht im Reiter **Assistent** die **Szenario-Vorschau**. Hauswacht spielt typische
Situationen mit **deinen** Einstellungen und Messwerten durch – mit **denselben Regeln wie im
Echtbetrieb** (Zustandsmaschine, Automatik, Beleg für „weg“), aber mit einer ausgedachten Uhr. Es
wird nichts geschaltet, keine Sirene, keine Benachrichtigung.

Jedes Szenario hat ein Ergebnis:

| Zeichen | Bedeutung |
|---|---|
| ✅ | So soll es sein (z. B. „Alarm nach 30 s“, „Unscharf, sobald die Tür aufgeht“) |
| ⚠️ | Funktioniert, aber mit Haken (z. B. nur mit unsicherem Beleg, oder PIN nötig) |
| ❌ | Unerwünscht (z. B. Fehlalarm beim Heimkommen, Einbruch ohne Alarm, wird nie scharf) |

Unter **„Ablauf“** steht Schritt für Schritt, was passiert – mit der Zeit seit Beginn (Minuten:
Sekunden).

### Die Szenarien

Je Profil, soweit es passt:

| Szenario | Wann | Was durchgespielt wird |
|---|---|---|
| **Einbruch durch die Tür …** | je Eingangstür des Profils | Profil scharf, die Tür geht auf, niemand schaltet unscharf |
| **Einbruch durch die Tür …, während jemand zuhause ist** | Profil hat die Ausgangserkennung an (ab 0.66.0b9) | Ohne Melder im Haus: ⚠️ Sirene erst nach der Wartezeit. Mit Melder im Haus: ✅ normale Eingangsverzögerung, weil niemand von innen kam |
| **Einbruch durch ein Fenster** | Profil hat Fenster | Profil scharf, ein Fenster geht auf |
| **… kommt heim** | je Person aus „Bei Rückkehr“ | Alle gehen weg (schaltet „alle weg“, ist das Profil automatisch scharf, sonst von Hand), zwei Stunden später kommt die Person heim. Das Handy meldet sich 30 s **vor** der Tür – oder, wenn gemessen, so spät **nach** der Tür wie bei euch beobachtet |
| **Alle gehen weg** | Profil hat „Scharf, wenn alle weg“ | Alle gehen nacheinander durch die Tür, danach meldet das Handy „weg“. Personen mit „eines reicht (nach Tür)“ gelten damit als weg, auch ohne Ortung (ab 0.66.0b8) |
| **Alle sind zuhause, die Handys schlafen ein** | Profil hat „Scharf, wenn alle weg“ | Alle Handys melden „weg“, ohne dass eine Tür aufgeht (auch: WLAN fällt aus). Ist bei jemandem „nach Tür“ abgeschaltet, wird das Profil hier scharf – ❌ |
| **Jemand geht kurz raus – dabei schläft das Handy von … ein** | je Person mit „Tür + Signal“ oder „eines reicht (nach Tür)“ (ab 0.66.0b8) | Die anderen sind unterwegs. Jemand öffnet kurz die Tür (Paket, Müll), kurz danach schläft das Handy der Person ein |

**Beispiel:** Profil Nacht mit „Unscharf mit Türbeleg“ für Anna, Eingangsverzögerung 30 s. Annas
Handy hat sich in drei Heimkehrten bis zu 38 s nach der Tür gemeldet. Die Vorschau zeigt:

> ❌ **Anna kommt heim** – Fehlalarm nach 30 s: das Handy meldet sich zu spät. Abhilfe: längere
> Eingangsverzögerung (Vorschlag im Check-up).

Nach dem Übernehmen des Vorschlags (50 s) zeigt dieselbe Vorschau:

> ✅ **Anna kommt heim** – Unscharf nach 38 s – ohne PIN, ohne Alarm.

### Was vereinfacht ist

- Jede Person hat **ein** Handy, das „zuhause“ oder „weg“ meldet (WLAN, Ping …), und – wenn Hauswacht
  eine kennt – **eine Ortung**, die drinnen oder draußen ist. Wie eure Signale im Einzelnen
  heißen, spielt keine Rolle.
- Gemessene Zeiten zählen erst ab **3 Messungen**.
- Gastmodus, Durchgang von Hand, offene Melder beim Scharfschalten und Bedienteile kommen in den
  Szenarien nicht vor.

## Einrichten nach Zielen (seit 0.65.0b1)

Statt Einstellung für Einstellung fragt der Assistent, **was Hauswacht für dich tun soll**. Im Reiter
**Assistent** → **Einrichten nach Zielen** öffnet sich ein Seitenblatt mit sechs Schritten:

1. **Haushalt:** Welche Personen Home Assistant kennt und ob sie als „weg“ erkannt werden können
   (✓ Ortung, „Tür + Signal“ bzw. „eines reicht“, ✓ Richtung, ⚠ Ortung eingefroren, ⚠ kann nicht als weg erkannt
   werden). Nur Anzeige – Ortung und „Tür + Signal“ stellst du unter System → Anwesenheit ein.
2. **Türen und Fenster** (*seit 0.65.0b2*), sortiert nach Etage und Raum:
   - **Noch in keiner Meldergruppe:** Türen, Fenster und Bewegungsmelder, die Home Assistant kennt,
     aber noch nicht überwacht werden. **Nichts ist vorausgewählt** – solche Melder sind oft für
     Licht oder Heizung da (Bewegungsmelder fürs Licht, Kühlschranktür); überwacht wird nur, was
     du ausdrücklich wählst. Türen und Fenster kommen in eine Gruppe
     für außen (die vorhandene mit den meisten Türen und Fenstern oder eine neue „Außen“),
     Bewegungsmelder in eine Gruppe für innen (vorhanden oder neu „Innen“).
   - **Eingangstüren:** Welche Türen haben eine **Eingangsverzögerung** (du kommst rein und
     schaltest in dieser Zeit unscharf)? Alle anderen Türen und Fenster lösen **sofort** aus –
     z. B. eine Terrassentür, die nur von innen geöffnet wird. Vorausgewählt ist, was heute schon
     so eingestellt ist.
3. **Ziele** (mehrere möglich), jeweils mit dem Hinweis, welches Profil es betrifft („ergänzt das
   Profil Nacht“ oder „legt das Profil Nacht neu an“):

   | Ziel | Was eingestellt wird |
   |---|---|
   | **Nachts absichern** | Profil mit dem Knopf „Nacht“: Meldergruppen (vorgeschlagen: alle ohne Bewegungsmelder), auf Wunsch „Scharf um“ und „Unscharf um“ |
   | **Automatisch scharf, wenn alle weg sind** | Profil mit dem Knopf „Abwesend“: Meldergruppen, „Scharf, wenn alle weg“ mit Personen und Wartezeit |
   | **Beim Heimkommen unscharf** | „Bei Rückkehr“ im Abwesend-Profil: Personen und wie sicher (empfohlen: Türbeleg); die Eingangsverzögerung nach euren Messungen |
   | **Nachts heimkommen, ohne dass „Nacht“ aus ist** | „Bei Rückkehr: Reinlassen“ im Nacht-Profil – wer heimkommt, wird reingelassen, das Profil bleibt scharf |
   | **Garage oder Werkstatt getrennt** (*seit 0.65.0b3*) | Eigener [Bereich](profile.md#bereiche) „Garage“ mit eigenem Bedienfeld (`alarm_control_panel.hauswacht_garage`) – unabhängig vom Haus scharf, z. B. nachts, während im Haus noch jemand wach ist. Dazu eine Meldergruppe „Garage“ und im Bereich ein Profil mit dem Knopf „Abwesend“, sodass „Alle Bereiche → Abwesend“ die Garage mitschaltet. Auf Wunsch „Scharf, wenn alle weg“ (dieselben Personen wie im Haus) und Uhrzeiten. Gibt es den Bereich schon, wird er ergänzt |

4. **Rückfragen** je Ziel – vorausgefüllt mit dem, was schon eingestellt ist, sonst mit
   Vorschlägen. Personen, die nicht als weg erkannt werden können, sind mit ⚠ markiert.
5. **Sirenen und Empfänger** für die betroffenen Profile. Sirenen werden **nur eingetragen, nie
   freigegeben** – die Freigabe bleibt ein eigener Schritt unter Alarmgeber. Sirenen von
   **Rauchmeldern** stehen mit 🔥 und dem Hinweis da: Als Einbruchsirene bekommen sie nur den
   Einbruchton, nie den Brandton, und bei einem Brand schaltet Hauswacht sie nicht ab. Die
   Brandfunktion des Rauchmelders bleibt unverändert.
6. **Plan:** je Profil „bisher → neu“, Hinweise, was der Assistent danach prüft, und die
   [Szenario-Vorschau](#was-passiert-wenn--seit-0640b4) für die Einstellungen, wie sie danach
   wären. Erst **Übernehmen** speichert.

### Was der Assistent beim Einrichten garantiert

- Vorhandenes wird **nur ergänzt**: Listen (Meldergruppen, Personen, Sirenen, Empfänger) werden
  erweitert, andere Einstellungen des Profils bleiben, wie sie sind.
- Was **überschrieben** würde (z. B. „Bei Rückkehr“ von „Unscharf, nur wenn automatisch scharf“
  auf „Unscharf mit Türbeleg“) oder die Anlage **nachgiebiger** macht (z. B. längere
  Eingangsverzögerung), ist im Plan mit ⚠ markiert. Übernehmen geht dann erst mit dem Häkchen
  „Ich habe die markierten Änderungen gesehen …“.
- Übernehmen geht nur, wenn **alle Bereiche unscharf** sind. Hauswacht rechnet den Plan dabei aus
  deinen Antworten **neu** – mit denselben Regeln wie im Seitenblatt. Hat sich inzwischen etwas
  geändert, wird nichts gespeichert.
- **Garage:** Melder aus einer Gruppe des Hauses kommen in die Gruppe „Garage“, und jedes Profil des
  Hauses, das die bisherige Gruppe überwacht, bekommt die Gruppe „Garage“ dazu – im Haus ändert
  sich also nichts, die Melder sind in beiden Bereichen. Eine Meldergruppe wird nie leer geräumt,
  und Melder, die über ein Label in einer Gruppe stecken, werden nicht verschoben.
- Ohne Antwort zu den Eingangstüren bleiben die Typen der Melder, wie sie sind.
- Es wird nichts geschaltet, keine Sirene freigegeben, an der Brandfunktion der Rauchmelder nichts
  geändert und keine Automation angelegt.

**Beispiel:** Es gibt schon die Profile „Zuhause“ und „Abwesend“, aber keins für die Nacht. Du
wählst „Nachts absichern“ (Scharf um 22:30) und „Beim Heimkommen unscharf“ für Anna mit Türbeleg.
Der Plan zeigt:

> **Neues Profil Nacht** – Meldergruppen: → Außen · Ausgangsverzögerung → 0 s ·
> Eingangsverzögerung → 30 s · Scharf um → 22:30
>
> **Profil Abwesend** – Bei Rückkehr: Nichts → Unscharf mit Türbeleg · Bei Rückkehr – Personen:
> – → Anna · Eingangsverzögerung: 30 s → 50 s ⚠ nachgiebiger
>
> Gut zu wissen: Eingangsverzögerung 50 s aus euren Messungen (längste gemessene Zeit plus Puffer).

Wegen des ⚠ setzt du das Häkchen, dann **Übernehmen**.

## Was kommt

- **0.66:** Ausgangserkennung – wer den PIN beim Rausgehen vergisst, löst keinen Alarm aus, wenn
  sein Handy kurz danach „weg“ ist. Die Szenarien oben werden dafür die Sicherheitstabelle: Rein
  darf dadurch nicht unsicherer werden.

Den Stand siehst du in der [Roadmap](roadmap.md).
