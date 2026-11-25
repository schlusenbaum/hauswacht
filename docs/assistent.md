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
| Eine Person in **„Scharf, wenn alle weg“** kann nie als weg erkannt werden (keine Ortung, „Tür + Signal“ aus) – das Profil wird so **nie** automatisch scharf | ⛔ Fehler | Person aus der Liste nehmen, oder ⚠ „Tür + Signal“ für sie erlauben |
| **„Unscharf, nur wenn automatisch scharf“**, aber das Profil hat keine Automatik (keine Uhrzeit, kein Zeitplan, kein „alle weg“) | ⛔ Fehler | – |
| **„Unscharf mit Türbeleg“** oder **„Reinlassen“**, aber das Profil hat keine Eingangstür (Melder vom Typ Tür) | ⛔ Fehler | – |
| Eine Person in **„Bei Rückkehr“** kann nie als weg erkannt werden – für sie greift „Bei Rückkehr“ nie | ⚠️ Warnung | Person aus der Liste nehmen, oder ⚠ „Tür + Signal“ erlauben |
| **Eingangsverzögerung** kürzer als gemessen nötig (Tür auf → unscharf, mit Puffer) | ⚠️ Warnung | ⚠ Eingangsverzögerung auf den gemessenen Wert |
| **Eingangsverzögerung** reicht nicht für den **Türbeleg** einer Person (Handy meldet „zuhause“ erst nach der Tür) | ⚠️ Warnung | ⚠ Eingangsverzögerung auf den gemessenen Wert |
| **„Eingangsverzögerung bei Annäherung“** ist an, aber keine Person der Liste hat ein Richtungs-Signal | ⚠️ Warnung | Verlängerung ausschalten |
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
| **Einbruch durch ein Fenster** | Profil hat Fenster | Profil scharf, ein Fenster geht auf |
| **… kommt heim** | je Person aus „Bei Rückkehr“ | Alle gehen weg (schaltet „alle weg“, ist das Profil automatisch scharf, sonst von Hand), zwei Stunden später kommt die Person heim. Das Handy meldet sich 30 s **vor** der Tür – oder, wenn gemessen, so spät **nach** der Tür wie bei euch beobachtet |
| **Alle gehen weg** | Profil hat „Scharf, wenn alle weg“ | Alle gehen nacheinander durch die Tür, danach meldet das Handy „weg“ |
| **Alle sind zuhause, die Handys schlafen ein** | Profil hat „Scharf, wenn alle weg“ | Alle Handys melden „weg“, ohne dass eine Tür aufgeht (auch: WLAN fällt aus) |
| **Jemand geht kurz raus – dabei schläft das Handy von … ein** | je Person mit „Tür + Signal“ | Die anderen sind unterwegs. Jemand öffnet kurz die Tür (Paket, Müll), kurz danach schläft das Handy der Person ein |

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

## Was kommt

Als Nächstes folgt die **Einrichtung nach Zielen**. Sie soll

- nach **Zielen** fragen statt nach Einstellungen („nachts absichern“, „automatisch scharf, wenn
  alle weg sind“, „beim Heimkommen unscharf“),
- euren Haushalt kennen (Personen, Handys, Signale, Messwerte) und daraus Empfehlungen geben,
- mit Beispielen aus dem eigenen Haus erklären, was die Einstellungen bewirken.

Den Stand siehst du in der [Roadmap](roadmap.md).
