# Einrichtungsassistent

**Deutsch** | [English](en/setup-wizard.md)

Der Einrichtungsassistent führt Schritt für Schritt durch die Einrichtung – ohne Vorwissen. Er
erklärt kurz, wie Hauswacht arbeitet, schlägt Melder, Meldergruppen und Alarmprofile vor und
zeigt am Ende, was eingerichtet ist und was noch fehlt.

## Starten

- **Bei der Installation:** Nach „Integration hinzufügen → Hauswacht“ fragt Hauswacht
  „Mit dem Einrichtungsassistenten (empfohlen)“ oder „Ohne Assistent“. Mit Assistent wird die
  Anlage am Ende mit allem angelegt, was du ausgewählt hast.
- **Später:** Einstellungen → Geräte & Dienste → Hauswacht → **Konfigurieren →
  Einrichtungsassistent**. Hier speichert jeder Schritt sofort; brichst du ab, bleibt das
  Bisherige erhalten.

Was schon eingerichtet ist, bleibt erhalten – der Assistent **ergänzt nur**. Du kannst ihn so oft
starten, wie du willst, z. B. wenn neue Fenster dazukommen.

**Erneuter Start:** Ist schon etwas eingerichtet, zeigt der Assistent zuerst eine
**Kapitel-Auswahl** – Einführung, Neue Melder suchen, Meldergruppen, Auslöseregeln, Alarmprofile,
Empfänger, Sirenen, Benutzer, Weiteren Bereich einrichten, Probelauf, Zusammenfassung. Von dort
geht es Schritt für Schritt weiter; jeder Schritt bleibt überspringbar.

*Beispiel:* Zwei neue Fensterkontakte sind dazugekommen → Einrichtungsassistent → „Neue Melder
suchen“ → die beiden Fenster sind vorgeschlagen → Meldergruppen → neue Gruppe oder überspringen.

**Jeden Schritt kannst du überspringen.** Was fehlt, steht am Ende in der Zusammenfassung.

## Die Schritte

### 1. Einführung (überspringbar)

Eine Seite „So arbeitet Hauswacht“: je Baustein ein Satz und ein Beispiel – Melder,
Meldergruppen, Auslöseregeln, Alarmprofile, Sirenen und Empfänger, Benutzer und Bedienteile.
Wer das kennt, wählt „Einführung überspringen“.

### 2. Getrennte Bereiche? (nur bei der ersten Einrichtung)

„Gibt es getrennte Wohnungen?“ – die meisten Häuser brauchen **einen** Bereich. Bei „Ja“ (z. B.
eine Einliegerwohnung, die unabhängig scharf geschaltet wird) richtest du zuerst den
Hauptbereich ein und startest den Assistenten danach erneut mit **„Weiteren Bereich
einrichten“**: Name des Bereichs, dann Melder, Meldergruppen und Profile für ihn. Die Profile
heißen dann z. B. „Abwesend (Einliegerwohnung)“. Mehr unter [Bereiche](profile.md#bereiche).

### 2a. Melder

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
| **Später festlegen** | Jetzt keine Gruppen und Regeln – weiter mit Empfängern und Sirenen. |

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

**Gekippte Fenster nachts erlauben:** Gibt es [Melder mit Kippstellung](melder.md#melder-mit-kippstellung-gekippt),
fragt der Assistent beim Nachtprofil, ob gekippte Fenster erlaubt sind (vorgeschlagen: ja). Dann
darf das Schlafzimmerfenster nachts gekippt bleiben – ganz öffnen löst aus. „Abwesend“ bleibt
streng: gekippt zählt dort wie offen.

**Nach Zeitplan (optional):** Für jedes der beiden Profile kannst du einen
**Zeitplan-Helfer** wählen. Beginnt ein Zeitblock, wird das Profil scharf; endet er, unscharf –
so gehen **je Wochentag andere Zeiten**, z. B. „Nacht“ Mo–Do 22:30–6:00 und Fr–Sa 0:30–8:00.
Den Zeitplan legst du selbst an: Einstellungen → Geräte & Dienste → **Helfer** → Helfer
erstellen → **Zeitplan** (Hauswacht kann Zeitpläne nicht selbst anlegen). Das geht auch später –
dann den Assistenten erneut starten und „Alarmprofile“ wählen, oder im Profil unter Automatik.
Leer = keine Zeitsteuerung; ein schon gewählter Zeitplan bleibt. Details:
[Je Wochentag andere Zeiten](profile.md#je-wochentag-andere-zeiten-zeitplan).

### 7. Empfänger

Wer bekommt die Nachrichten von Hauswacht (Alarm, scharf, unscharf, Störungen)? Handys mit der
Home-Assistant-App (`mobile_app_…`) sind vorgewählt. Feinheiten wie Empfänger je Ereignis stellst
du später unter [Benachrichtigungen](benachrichtigungen.md) ein.

Danach kannst du eine **Test-Nachricht** schicken – nur, wenn du den Knopf drückst. Der
Assistent zeigt, an wen sie ging und wo es nicht geklappt hat.

*Beispiel:* `mobile_app_annas_handy` ausgewählt → „Test-Nachricht senden“ → auf dem Handy
erscheint „Hauswacht: Test-Nachricht aus dem Einrichtungsassistenten“. Kommt nichts an, die
Benachrichtigungen der App prüfen.

### 8. Sirenen

Vorgeschlagen werden alle Sirenen aus Home Assistant. **In diesen Profilen verwenden:** die
gewählten Sirenen kommen zu den Sirenen dieser Profile dazu (vorhandene bleiben).

Die echte Sirenenansteuerung bleibt **gesperrt**, bis du sie bewusst freigibst – unter
[Alarmgeber – Sirenen → Sirenen und Freigabe](sirenen.md). Der Assistent gibt nichts frei; im
Testmodus heult ohnehin keine Sirene.

Im Einstellungsdialog bietet der Assistent danach den **Sirenentest** an: jede Sirene einzeln,
kurz und leise, mit Bestätigung vor jedem Ton – wie im [Sirenentest](sirenen.md). Danach geht
es zurück in den Assistenten. Bei der Installation gibt es den Sirenentest noch nicht.

### 9. Benutzer

Name und – optional – ein **PIN** (4–8 Ziffern). Danach kannst du weitere Benutzer anlegen.
Heißt ein Benutzer wie ein Home-Assistant-Konto, wird er damit verknüpft; die
[Alarmkarte](dashboard.md) erkennt ihn dann ohne PIN-Eingabe.

> **Achtung:** Sobald **ein** PIN existiert, verlangt das Bedienfeld (auch Alexa) zum
> Unscharfschalten einen PIN – von allen. Also allen einen PIN geben oder keinem. Mehr unter
> [Benutzer und PINs](benutzer.md).

Rechte je Bereich, Gültigkeit, Karten und Bedrohungs-PIN stellst du später im
Einstellungsdialog ein. Name leer lassen = überspringen.

### 10. Bedienteile

Nur ein Hinweis: Keypads, Karten, Aufkleber, Leser, Taster und Türschlösser richtest du unter
Systemeinstellungen → [Bedienteile](bedienteile.md) ein.

### 11. Probelauf (nur im Einstellungsdialog)

Im Probelauf öffnest du Türen und Fenster und läufst an Bewegungsmeldern vorbei – Hauswacht hakt
jeden Melder der Meldergruppen ab, den es erkennt (✅), mit „Erkannt: 3 von 5“. **Aktualisieren**
zeigt den neuen Stand.

Dafür muss der **Testmodus an** sein. Der Assistent schaltet ihn **nicht** selbst ein, sondern
bittet darum: auf der Karte [„Hauswacht Test“](testmodus.md#karte-hauswacht-test) oder mit dem
Schalter „Testmodus“. Danach „Testmodus ist an – Probelauf starten“. Der Probelauf liest nur;
er schaltet nichts scharf und löst keinen Alarm aus.

Bleibt ein Melder auf ⬜, obwohl du ihn ausgelöst hast: Batterie, Funkverbindung und das Gerät in
Home Assistant prüfen. Nach dem Probelauf den Testmodus wieder ausschalten.

### 12. Zusammenfassung

Zwei Listen:

- **✅ Eingerichtet:** Meldergruppen, Regeln und für jedes Profil, was es überwacht.
- **⚠️ Noch offen:** z. B. „Keine Empfänger – ein Alarm erreicht noch niemanden“, „Keine
  Sirenen“, „Sirenen eingetragen, aber noch nicht freigegeben“, „Keine Benutzer – bedient wird
  nur über die App“ – jeweils mit dem Menü, in dem du es nachholst.

Die Anlage startet bzw. bleibt **unscharf**.

## Was der Assistent nie nebenbei tut

- Er gibt **keine Sirenen frei** und schaltet den Testmodus nicht aus.
- Er schaltet **keine Geräte**. Sirenentest und Test-Nachricht gibt es nur auf Knopfdruck.
- Er ändert keine Rauchmelder, Automationen oder Skripte.
- Er überschreibt nichts: Vorhandenes wird nur ergänzt.

## Danach

1. **Im Testmodus ausprobieren** – mit dem Probelauf und einmal richtig scharf schalten
   ([Testmodus](testmodus.md)).
2. Wenn alles passt: **Sirenen freigeben** ([Sirenen](sirenen.md)).
3. Nach Bedarf [Benutzer und PINs](benutzer.md) verfeinern, [Bedienteile](bedienteile.md)
   einrichten.
