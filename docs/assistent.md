# Einrichtungsassistent

**Deutsch** | [English](en/setup-wizard.md)

Der Einrichtungsassistent führt Schritt für Schritt durch die Einrichtung – ohne Vorwissen. Er
erklärt kurz, wie Hauswacht arbeitet, schlägt Melder, Meldergruppen und Alarmprofile vor und
zeigt am Ende, was eingerichtet ist und was noch fehlt.

> **Vorabversion:** Der Assistent ist neu und erscheint zuerst in Testversionen. Er deckt bisher
> Melder, Meldergruppen, Auslöseregeln und Alarmprofile ab. Empfänger, Sirenen, Benutzer und ein
> Probelauf folgen; bis dahin richtest du sie im [Einstellungsdialog](installation.md#das-einstellungsmenü) ein.

## Starten

- **Bei der Installation:** Nach „Integration hinzufügen → Hauswacht“ fragt Hauswacht
  „Mit dem Einrichtungsassistenten (empfohlen)“ oder „Ohne Assistent“. Mit Assistent wird die
  Anlage am Ende mit allem angelegt, was du ausgewählt hast.
- **Später:** Einstellungen → Geräte & Dienste → Hauswacht → **Konfigurieren →
  Einrichtungsassistent**. Hier speichert jeder Schritt sofort; brichst du ab, bleibt das
  Bisherige erhalten.

Was schon eingerichtet ist, bleibt erhalten – der Assistent **ergänzt nur**. Du kannst ihn so oft
starten, wie du willst, z. B. wenn neue Fenster dazukommen.

**Jeden Schritt kannst du überspringen.** Was fehlt, steht am Ende in der Zusammenfassung.

## Die Schritte

### 1. Einführung (überspringbar)

Eine Seite „So arbeitet Hauswacht“: je Baustein ein Satz und ein Beispiel – Melder,
Meldergruppen, Auslöseregeln, Alarmprofile, Sirenen und Empfänger, Benutzer und Bedienteile.
Wer das kennt, wählt „Einführung überspringen“.

### 2. Melder

Hauswacht sucht in Home Assistant alle **Türen, Fenster und Bewegungsmelder**, die noch in keiner
Meldergruppe stehen, und listet sie nach Etage und Raum auf. Alle Vorschläge sind ausgewählt –
nimm weg, was nicht überwacht werden soll.

*Beispiel:* Gefunden werden „Erdgeschoss › Küche: Fenster Küche“, „Erdgeschoss › Flur:
Bewegung Flur“ und „Haustür“. Das Fenster im Gästeklo soll nicht überwacht werden → abwählen.

Rauch-, Wasser- und Batterie-Sensoren schlägt Hauswacht bewusst nicht vor. Leer lassen =
überspringen.

### 3. Wie soll überwacht werden?

| Wahl | Wann sinnvoll |
|---|---|
| **Mit Meldergruppen (empfohlen)** | Für die meisten Häuser: Jeder Melder in einer Gruppe löst im scharfen Profil Alarm aus. |
| **Nur mit Auslöseregeln** | Für Fortgeschrittene: Alarm erst, wenn mehreres zusammenkommt ([Auslöseregeln](ausloeseregeln.md)). |
| **Mit beidem** | Gruppen für Türen und Fenster, Regeln zusätzlich, z. B. für Bewegungsmelder. |
| **Später festlegen** | Jetzt nichts anlegen – weiter zur Zusammenfassung. |

### 4. Meldergruppen

Vorschlag: Türen und Fenster in die Gruppe **„Außen“**, Bewegungsmelder in die Gruppe
**„Innen“**. Namen und Mitglieder kannst du ändern; eine leere Gruppe wird nicht angelegt.

**Eingangstüren:** Türen, durch die man heimkommt. Nur sie bekommen die
[Eingangsverzögerung](profile.md) – wer heimkommt, hat ein paar Sekunden zum Unscharfschalten.
Andere Türen lösen sofort aus.

*Beispiel:* Haustür und Terrassentür sind gefunden. Heim kommt man nur durch die Haustür → nur
die Haustür als Eingangstür lassen. Die Terrassentür löst dann sofort aus (Typ „Sonstiges“, in
der Meldergruppe änderbar).

Ein Melder kann nur in **einer** Gruppe stehen. Steht er schon in einer anderen, nennt der
Assistent ihn mit der Gruppe.

### 5. Auslöseregeln (nur bei „Auslöseregeln“ oder „beidem“)

Im Einstellungsdialog öffnet „Neue Auslöseregel anlegen“ den
[Regel-Assistenten](ausloeseregeln.md). Nach dem Speichern (oder Abbrechen) kommst du zurück und
kannst weitere Regeln anlegen oder zu den Profilen weitergehen.

Bei der **Installation** gibt es den Regel-Assistenten noch nicht: Regeln legst du danach unter
Konfigurieren → Einrichtungsassistent an.

### 6. Alarmprofile

Vorschlag:

- **Abwesend** – niemand ist zu Hause: alle Meldergruppen (und Regeln). Nach dem Scharfschalten
  bleibt die **Ausgangsverzögerung** zum Verlassen des Hauses, beim Heimkommen die
  **Eingangsverzögerung** zum Unscharfschalten. Vorgabe: 60 und 30 Sekunden.
- **Nacht** – alle schlafen: nur Gruppen ohne Bewegungsmelder (z. B. „Außen“), damit man sich im
  Haus bewegen kann. Keine Ausgangsverzögerung.

Abwählen = nicht anlegen. Gibt es schon ein Profil mit dem Knopf „Abwesend“ bzw. „Nacht“,
**ergänzt** der Assistent dieses (Meldergruppen, Regeln, Verzögerungen) statt ein zweites
anzulegen. Alles andere am Profil (Sirenen, Empfänger, Automatik …) bleibt, wie es ist.

Ein ausgewähltes Profil braucht mindestens eine Meldergruppe oder Regel.

### 7. Zusammenfassung

Zwei Listen:

- **✅ Eingerichtet:** Meldergruppen, Regeln und für jedes Profil, was es überwacht.
- **⚠️ Noch offen:** z. B. „Keine Empfänger – ein Alarm erreicht noch niemanden“, „Keine
  Sirenen“, „Keine Benutzer – bedient wird nur über die App“ – jeweils mit dem Menü, in dem du
  es nachholst.

Die Anlage startet bzw. bleibt **unscharf**.

## Was der Assistent nie nebenbei tut

- Er gibt **keine Sirenen frei** und schaltet den Testmodus nicht aus.
- Er schaltet **keine Geräte** und verschickt keine Nachrichten.
- Er ändert keine Rauchmelder, Automationen oder Skripte.
- Er überschreibt nichts: Vorhandenes wird nur ergänzt.

## Danach

1. **Empfänger** eintragen: Benachrichtigungen → Einstellungen ([Benachrichtigungen](benachrichtigungen.md)).
2. **Im Testmodus ausprobieren** ([Testmodus](testmodus.md)).
3. Nach Bedarf [Sirenen](sirenen.md), [Benutzer und PINs](benutzer.md),
   [Bedienteile](bedienteile.md).
