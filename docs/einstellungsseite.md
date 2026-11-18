# Einstellungsseite „Hauswacht“ in der Seitenleiste

**Deutsch** | [English](en/settings-page.md)

> **Vorabversion:** Die Seite wächst in Stufen. Sie **zeigt** die ganze Einrichtung an;
> **Melder**, **Alarmprofile**, **Alarmgeber** und **Benachrichtigungen** bearbeitest du schon
> direkt auf der Seite. Auslöseregeln, Personen und System bearbeitest du noch im
> Einstellungsdialog (Knopf „Im Dialog bearbeiten“ oben rechts) – das folgt in den nächsten
> Stufen.

Der Einstellungsdialog zeigt immer nur einen Schritt. Die Seite **Hauswacht** in der
Seitenleiste von Home Assistant zeigt dagegen alles auf einen Blick: welche Melder in welcher
Gruppe stecken, in welchem Profil sie scharf sind, wer welche Nachricht bekommt.

- Nur für **Administratoren** sichtbar.
- **Zusätzlich** zum Dialog und zum [Einrichtungsassistenten](assistent.md) – alle Wege nutzen
  dieselben Einstellungen. Was im Dialog geändert wird, steht nach „Neu laden“ sofort auf der
  Seite.
- Ausblenden: Konfigurieren → System → **Einstellungsseite in der Seitenleiste** → Haken weg.

## Die Reiter

| Reiter | Inhalt |
|---|---|
| **Übersicht** | Prüfhinweise (z. B. „Profil ohne Empfänger“) und der Zustand je Bereich |
| **Melder** | Alle Melder **nach Meldergruppen**, mit Typ, Zustand und Batterie – und je Profil eine Spalte (Matrix, siehe unten). Darunter [Besondere Melder](melder.md#melder-mit-kippstellung-gekippt) und [Immer aktiv](melder.md#immer-aktive-melder) |
| **Profile** | Jedes Profil mit Gruppen, Regeln, Zeiten, Reaktion, Empfängern und Automatik |
| **Auslöseregeln** | Jede Regel als Satz und wo sie gilt |
| **Alarmgeber** | Sirenen mit ihren Fähigkeiten und dem letzten Test |
| **Benachrichtigungen** | Empfänger je Ereignis, Lautsprecher, Ruhezeit |
| **Personen und Bedienteile** | Benutzer mit Rechten und Ausweisen (PINs werden nie angezeigt), Bedienteile, Aktions-Codes |
| **System** | Funkstille, Funknetz, Anlernen, Neustart, Heimkehr |

Die Seite merkt sich den zuletzt gewählten Reiter (nur in diesem Browser).

## Die Matrix „Melder × Profile“

Im Reiter **Melder** steht jeder Melder in einer Zeile, darüber seine Meldergruppe. Für jedes
Profil gibt es eine Spalte:

| Zeichen | Bedeutung |
|---|---|
| ✓ | löst in diesem Profil **allein** aus |
| R | zählt nur in **Auslöseregeln** dieses Profils |
| – | in diesem Profil **ausgenommen** |
| leer | wird in diesem Profil nicht überwacht |

Gruppen mit Erschütterungsmeldern zeigen ihren [Fehlalarmschutz](melder.md#erschütterungsmelder)
(„Alarm bei 2 Meldungen in 60 s“). Das **Suchfeld** filtert nach dem Namen.

Beispiel: Steht beim Bewegungsmelder im Flur in der Spalte „Nacht“ ein **–**, ist er nachts
ausgenommen – du kannst nachts durch den Flur gehen, ohne Alarm.

## Melder bearbeiten

Im Reiter **Melder** gibt es die Knöpfe zum Bearbeiten. Ein Klick öffnet rechts ein
Seitenblatt; **Speichern** übernimmt sofort, **Abbrechen** oder ein Klick daneben verwirft.

| Was | Wo | Was du einstellst |
|---|---|---|
| **Einzelner Melder** | Auf den **Namen** des Melders in der Tabelle klicken | **Meldergruppe** (verschieben oder herausnehmen), **Typ**, **Immer aktiv** und je Profil, ob er dort **allein auslöst** – Haken weg = in diesem Profil ausgenommen (z. B. Bewegungsmelder Flur nachts). Steckt der Melder über ein Label in seiner Gruppe, wechselst du die Gruppe über das Label an der Entität |
| **Meldergruppe** | „+ Meldergruppe anlegen“ bzw. „Bearbeiten“ an der Gruppe | Name, Melder (Suchfeld → anklicken), **Typ je Melder**, zusätzlich ein Label. Sind Erschütterungsmelder dabei, erscheint der **Fehlalarmschutz** (Meldungen bis zum Alarm, Zeitfenster) mit Knopf „Empfehlung übernehmen“ (2 in 60 s). Löschen nimmt die Gruppe auch aus allen Profilen |
| **Melder mit Kippstellung** | Besondere Melder → „+ Kippstellung hinzufügen“ bzw. „Bearbeiten“ | Quelle (Suchfeld), optional Attribut, dann je bekanntem Wert **offen / gekippt / zu** – weitere Werte eintippen und Enter. Optional gleich in eine Gruppe |
| **Erschütterungsstärke** | Besondere Melder → „+ Erschütterungsstärke hinzufügen“ | Sensor (Suchfeld, der aktuelle Wert steht daneben) und Schwelle; optional gleich in eine Gruppe |
| **Immer aktiv** | „Bearbeiten“ unter Immer aktiv | Ganze Gruppen ankreuzen, einzelne Melder hinzufügen oder entfernen. Sirenen für „Immer aktiv“ bleiben im Dialog |

**Melder finden, ohne ihre Namen zu kennen:** Beim Hinzufügen zeigt die Liste sofort alle
**passenden** Melder (Tür, Fenster, Bewegung, Erschütterung, Wasser … sowie Schlösser und
Garagentore), sortiert nach Raum – zum Anklicken. Das Suchfeld grenzt die Liste nur ein.
Darunter zwei Schalter:

- **Auch andere Entitäten zeigen** – z. B. Binärsensoren ohne passende Geräteklasse (Verbindung,
  Update …), die sonst ausgeblendet sind.
- **Auch Melder zeigen, die schon in einer Gruppe sind** – mit Angabe der Gruppe („in Außen“).
  Normalerweise ausgeblendet, denn ein Melder gehört zu genau einer Gruppe.

Bei Besonderen Meldern zeigt die Liste passende Quellen: für die Kippstellung Auswahl-Helfer und
Sensoren mit Werten wie „tilted“ oder Namen mit „Fenster“, „Griff“ …; für die
Erschütterungsstärke Zahlenwert-Helfer und Sensoren mit „vibration“ im Namen.

So sicher wie der Dialog:

- **Dieselben Regeln:** Die Seite nutzt dieselbe Prüfung wie der Dialog. Ein Melder in zwei
  Gruppen, eine Gruppe ohne Namen, „gekippt“ und „zu“ für denselben Wert – das wird mit einer
  Meldung am Feld abgelehnt.
- **Nur unscharf:** Ist ein Bereich scharf, fehlen die Knöpfe; oben steht „Ändern geht nur, wenn
  alle Bereiche unscharf sind“.
- **Nichts überschreiben:** Hat jemand zwischendurch im Dialog oder auf einem anderen Gerät etwas
  geändert, speichert die Seite nicht, sondern lädt neu – dann einfach noch einmal.
- Nach dem Speichern lädt Hauswacht seine Einstellungen neu (ein, zwei Sekunden), danach zeigt
  die Seite den neuen Stand mit „✓ Gespeichert.“

## Profile bearbeiten

Im Reiter **Profile** steht jedes Profil mit seinen Werten; **„Bearbeiten“** öffnet das
Seitenblatt, **„+ Alarmprofil anlegen“** ein leeres mit den üblichen Vorgaben (30 s Verzögerung,
180 s Alarm …). Die Abschnitte entsprechen dem Dialog:

| Abschnitt | Inhalt |
|---|---|
| **Allgemein** | Name, Symbol (z. B. `mdi:weather-night`), Knopf am Bedienfeld, Bereich (nur bei mehreren Bereichen) |
| **Was wird überwacht** | Meldergruppen (jeder Melder löst allein aus), **Ausgenommene** – die Liste zeigt genau die Melder der angehakten Gruppen –, Auslöseregeln, „Gekippte Fenster erlaubt“ (nur mit [Meldern mit Kippstellung](melder.md#melder-mit-kippstellung-gekippt)) |
| **Zeiten** | Ausgangs- und Eingangsverzögerung, Dauer der Alarmreaktion, Höchstzahl Alarmzyklen |
| **Beim Scharfschalten** | Offene Melder, ausgefallene Melder, Manipulation löst Alarm aus |
| **Reaktion bei Alarm** | Sirenen (die unter Alarmgeber eingetragenen), Ton, Lautstärke, stiller Alarm, Empfänger, zusätzliche Lautsprecher |
| **Automatik** | Scharf um / unscharf um, Wochentage, Zeitplan, Personen („alle weg“), Wartezeit, unscharf bei Rückkehr, Türbeleg-Fenster – siehe [Automatik](profile.md#automatik). **„Zeitplan anlegen ↗“** öffnet die Helfer in einem neuen Fenster („Helfer erstellen“ → „Zeitplan“); danach **„Liste aktualisieren“** – deine Eingaben im Profil bleiben dabei erhalten |
| **Scharf durch Schließen der Tür** | An/aus, Ausgangstüren (die Melder vom Typ Tür in den gewählten Gruppen), Beruhigungszeit |

Es gelten dieselben Regeln wie im Dialog: Name nötig und eindeutig, jeder Knopf nur einmal je
Bereich, „Unscharf bei Rückkehr“ nur mit Personen. **Löschen** fragt einmal nach.

## Alarmgeber bearbeiten

Im Reiter **Alarmgeber** öffnet **„Sirenen bearbeiten“** das Seitenblatt:

- **Eingetragene Sirenen** – mit ✕ austragen; darunter alle weiteren Sirenen (`siren.…`) zum
  Antippen. Wird eine Sirene ausgetragen, verschwindet sie auch aus den Profilen und ihr Ton wird
  vergessen – wie im Dialog.
- **Echte Sirenenansteuerung freigegeben** – erst damit können Sirenen bei einem Alarm wirklich
  ertönen. Beim **Einschalten** erscheint ein Warnhinweis und ein zweiter Haken **„Ich habe
  verstanden …“**; ohne diesen Haken wird nicht gespeichert („Zum Freigeben bitte bestätigen.“).
  Ausschalten geht jederzeit ohne Nachfrage.
- **Experten: auch Schalter als Sirene erlauben** – nach dem Speichern stehen auch `switch.…` in
  der Auswahl (siehe [Sirene aus Schalter erstellen](sirenen.md#sirene-aus-schalter-erstellen)).

Den **Ton je Sirene** und die Brandton-Freigabe stellst du weiter im Dialog ein
([Ton je Sirene](sirenen.md#ton-je-sirene)). Einen **Sirenentest** gibt es auf der Seite bewusst
nicht – nur in der [Testkarte](sirenen.md#sirenentest).

## Benachrichtigungen bearbeiten

Im Reiter **Benachrichtigungen** gibt es zwei Knöpfe:

**„Empfänger und Ereignisse bearbeiten“** – alles aus „Benachrichtigungen – Einstellungen“ im
Dialog auf einem Blatt:

| Abschnitt | Inhalt |
|---|---|
| **Allgemeine Empfänger** | bekommen alle Ereignisse, die keine eigenen Empfänger haben |
| **Schalter** | Auch im Testmodus benachrichtigen · Knopf „Unscharf schalten“ in der Alarm-Nachricht · Wichtige Nachrichten durchbrechen „Nicht stören“ |
| **Bedrohungs-PIN meldet still an** | wer bei einer Bedrohungs-PIN still benachrichtigt wird |
| **Ereignisse** | je Ereignis ein Haken (an/aus); aufklappen → **eigene Empfänger**. Rechts steht, wer es bekommt – „allgemeine Empfänger“, wenn keine eigenen angehakt sind |
| **Erinnerung** | Personen, vorgeschlagenes Profil, nach wie vielen Minuten – siehe [Erinnerung](benachrichtigungen.md#erinnerung-alle-weg-anlage-unscharf) |

Die Empfänger je **Profil** (wer bei Alarm in diesem Profil benachrichtigt wird) stellst du im
Profil ein (Abschnitt „Reaktion bei Alarm“).

**„Eigene Texte“** – darunter steht jedes Ereignis mit „Text von Hauswacht“ oder deinem eigenen
Text. „Bearbeiten“ öffnet Titel und Text – beim ersten Mal steht dort der **Text von Hauswacht als
Vorlage** (z. B. `Profil {profil} scharf geschaltet ({wer}).`), die du einfach änderst. Die
**Vorschau** mit Beispielwerten ändert sich beim Tippen mit. Platzhalter wie `{melder}` oder
`{profil}` stehen darunter. Ein Tippfehler wird abgelehnt, z. B. „Text fehlerhaft: Unbekannter
Platzhalter {foo}“.

- **„↺ Standardtext“** setzt Titel und Text auf die Vorlage zurück; speichern – fertig.
- Vorlage **unverändert** gespeichert = es bleibt beim Text von Hauswacht (nichts wird
  gespeichert).
- `{text}` ist der vollständige Text von Hauswacht. Ein eigener Text ersetzt ihn ganz – beim Alarm
  z. B. auch den Zusatz, welche Sirenen laufen. Zum Behalten `{text}` mit hineinschreiben.

Beispiel:

```text
Titel:  Alarm im {bereich}
Text:   {melder} hat um {uhrzeit} ausgelöst (Profil {profil}).
```

Mehr dazu unter [Eigene Texte und Platzhalter](benachrichtigungen.md#eigene-texte-und-platzhalter).
Sprachausgabe und Nachtruhe stellst du noch im Dialog ein.

## Gut zu wissen

- Die Seite **schaltet nichts** – weder Sirenen noch Geräte. Sie ändert nur Einstellungen, und
  nur die, die du speicherst.
- Gezeigt wird der Stand beim Öffnen; „Neu laden“ (Pfeil oben) holt den aktuellen.
- Dieselben Inhalte gibt es zum Ausdrucken in der Karte [Hauswacht Übersicht](uebersicht.md).
- Auf dem Handy geht die Seite auch; breite Tabellen lassen sich seitlich schieben.
