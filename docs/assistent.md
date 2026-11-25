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

## Was kommt

Als Nächstes bekommt die Einstellungsseite einen eigenen Reiter **Assistent**: zuerst ein
**Check-up** aller Einstellungen auf einen Blick (dieselbe Prüfung wie oben), dann eine
**Vorschau**, was in typischen Situationen passieren würde (Einbruch, Heimkommen, Handy schläft …).
Danach folgt die **Einrichtung nach Zielen**. Sie soll

- nach **Zielen** fragen statt nach Einstellungen („nachts absichern“, „automatisch scharf, wenn
  alle weg sind“, „beim Heimkommen unscharf“),
- euren Haushalt kennen (Personen, Handys, Signale, Messwerte) und daraus Empfehlungen geben,
- mit Beispielen aus dem eigenen Haus erklären, was die Einstellungen bewirken.

Den Stand siehst du in der [Roadmap](roadmap.md).
