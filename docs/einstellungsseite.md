# Einstellungsseite „Hauswacht“ in der Seitenleiste

**Deutsch** | [English](en/settings-page.md)

> **Vorabversion:** Die Seite **zeigt** die ganze Einrichtung und du bearbeitest **alles** direkt
> auf ihr. Der Einstellungsdialog (Knopf „Im Dialog bearbeiten“ oben rechts) bleibt als zweiter
> Weg. Nur den **Sirenentest** startest du bewusst in der Karte „Hauswacht Test“ – die Seite
> schaltet nie eine Sirene.

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
| **Übersicht** | Prüfhinweise (z. B. „Profil ohne Empfänger“) und der Zustand je Bereich; Knöpfe **Drucken** und **Notfallblatt** wie in der Karte [Hauswacht Übersicht](uebersicht.md) |
| **Melder** | Alle Melder **nach Meldergruppen**, mit Typ, Zustand und Batterie – und je Profil eine Spalte (Matrix, siehe unten). Darunter [Besondere Melder](melder.md#melder-mit-kippstellung-gekippt) und [Immer aktiv](melder.md#immer-aktive-melder) |
| **Profile** | Jedes Profil mit Gruppen, Regeln, Zeiten, Reaktion, Empfängern und Automatik |
| **Auslöseregeln** | Jede Regel als Satz und wo sie gilt |
| **Alarmgeber** | Sirenen mit ihren Fähigkeiten und dem letzten Test |
| **Benachrichtigungen** | Empfänger je Ereignis, Lautsprecher, Ruhezeit |
| **Personen und Bedienteile** | Personen mit Rechten und Ausweisen (PINs werden nie angezeigt), PIN-Regeln und Master-PIN, Bedienteile, Aktions-Codes |
| **System** | Überwachung, Neustart, Funkstille, Funknetz, Anwesenheit und Heimkehr, Bereiche, Einstellungsseite |
| **Dokumentation** | Alle Seiten dieser Anleitung mit kurzer Beschreibung |

Die Seite merkt sich den zuletzt gewählten Reiter (nur in diesem Browser).

## Anleitung direkt aus der Seite

Neben jeder Überschrift – auf der Seite und in jedem Seitenblatt – steht ein kleines **„?“**. Es
öffnet die Anleitung in einem neuen Fenster, genau an der passenden Stelle: das „?“ bei „Immer
aktiv“ zum Beispiel bei [Immer aktive Melder](melder.md#immer-aktive-melder), das im Blatt einer
Auslöseregel bei [Auslöseregeln](ausloeseregeln.md) (im YAML-Modus beim
[Expertenmodus](ausloeseregeln.md#expertenmodus-yaml)).

Der Reiter **Dokumentation** listet alle Seiten. Die Links zeigen auf die Anleitung **genau der
installierten Version** (auf GitHub, deutsch oder englisch nach der Sprache von Home Assistant) –
du liest also nie über etwas, das deine Version noch nicht kann.

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
(„Alarm bei 2 Meldungen in 60 s“).

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
| **Immer aktiv** | „Bearbeiten“ unter Immer aktiv | Ganze Gruppen ankreuzen, einzelne Melder hinzufügen oder entfernen. Darunter **Sirenen, wenn unscharf ausgelöst**: aus = nur Nachricht; an = Alarm mit den gewählten Sirenen, Ton (nur Einbruchtöne), Lautstärke und Dauer |
| **Melder aus Messwert** | Besondere Melder → „+ Melder aus Messwert erstellen“ | Messwert (`sensor.…`, z. B. Temperatur), Name, oberer und/oder unterer Grenzwert, Hysterese, Typ und wohin (Gruppe oder Immer aktiv). Hauswacht legt dafür einen Schwellenwert-Helfer an – siehe [Melder aus anderem Sensor erstellen](melder.md#melder-aus-anderem-sensor-erstellen) |

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

## Auslöseregeln bearbeiten

Im Reiter **Auslöseregeln** steht jede Regel als Satz, darunter die Profile, in denen sie gilt
(„in keinem Profil – wirkt nicht“, wenn keins). **„Bearbeiten“** öffnet das Seitenblatt,
**„+ Auslöseregel anlegen“** ein neues mit zwei leeren Schritten. Was eine Auslöseregel ist, steht
unter [Auslöseregeln](ausloeseregeln.md).

Oben im Blatt schaltest du um zwischen **Formular** und **YAML**. Darunter steht beim Bearbeiten
immer, **was die Regel bewirkt**, z. B. „Haustür, dann innerhalb von 90 s Meldergruppe Keller →
sofort Alarm“ – und was nicht passt (z. B. „Ein Melder steht in Schritt 2 und im Schritt davor.“).

**Formular** – für einfache Regeln:

| Feld | Inhalt |
|---|---|
| **Name, Ergebnis** | Sofort Alarm · Eingangsverzögerung, dann Alarm · Nur Benachrichtigung |
| **Schritt 1, 2, …** | „Was muss passieren?“ – einer davon / alle davon / mindestens … davon; dazu Meldergruppen (Haken) und einzelne Melder (Namen tippen oder aus der Liste wählen). „Zeit bis zum nächsten Schritt“ in Sekunden. Mit ↑ ↓ verschieben, mit ✕ entfernen, „+ Schritt“ für weitere (bis 10) |
| **Nicht, wenn vorher …** | Haken setzen, Melder oder Gruppen wählen und den Zeitraum davor – siehe [Ausnahme](ausloeseregeln.md#ausnahme-nicht-wenn-vorher-) |
| **Gilt in den Profilen** | Haken je Profil – dasselbe wie „Auslöseregeln“ im Profil |

**YAML** – für alles, auch komplexe Regeln (verschachtelte Ausdrücke, Bedingungen „nur wenn …“).
Aufbau wie im [Expertenmodus](ausloeseregeln.md#expertenmodus-yaml): Meldergruppen per Name,
Melder per Entitäts-ID. Beispiel:

```yaml
name: Tür dann Keller
result: alarm
steps:
  - any:
      - sensor: binary_sensor.haustuer
    within: 90
  - any:
      - group: Keller
```

- Vom Formular zu YAML geht immer. Zurück zum Formular geht nur, wenn die Regel einfach genug ist.
- **Komplexe Regeln gehen nur als YAML** – der Knopf „Formular“ ist dann ausgegraut, und in der
  Liste steht „(nur YAML)“.
- **Bedingungen** („nur wenn …“) zeigt das Formular an; ändern lassen sie sich nur im YAML.
- Gespeichert wird nur, was auch der Dialog speichern würde: Name nötig und eindeutig, kein
  leerer Schritt, nicht derselbe Melder in zwei Schritten hintereinander. **Löschen** fragt einmal
  nach und nimmt die Regel auch aus allen Profilen.

## Personen bearbeiten

Im Reiter **Personen und Bedienteile** steht jede Person mit ihren Rechten und Ausweisen („alle
Rechte · PIN · 2 Karten“). **„Bearbeiten“** öffnet das Seitenblatt, **„+ Person anlegen“** ein
leeres. Was Personen, PINs und Rechte sind, steht unter [Benutzer, PINs und Sperre](benutzer.md).

| Feld | Inhalt |
|---|---|
| **Name** | Vorschläge aus den Home-Assistant-Konten. Heißt die Person wie ein Konto, wird sie damit verknüpft (wie im Dialog) |
| **Aktiv** | Aus = die Person kann nichts schalten (z. B. vorübergehend gesperrt) |
| **Darf …** | scharf schalten, unscharf schalten, Alarm beenden. Bei mehreren Bereichen wahlweise **je Bereich** – dann ein Kasten je Bereich |
| **Trotzdem scharf am Keypad** | offene Melder überbrücken, siehe [Trotzdem scharf am Keypad](bedienteile.md#trotzdem-scharf-am-keypad) |
| **PIN in der Alarmkarte** | z. B. für ein Wandtablet, das immer angemeldet ist |
| **Gültig ab / bis** | für Gäste oder Handwerker; außerhalb der Zeit wird die Person abgewiesen |
| **Home-Assistant-Konto** | ausdrücklich verknüpfen (sonst automatisch nach Name) |
| **PIN** | Neuer PIN und neue [Bedrohungs-PIN](benutzer.md#bedrohungs-pin), jeweils 4 bis 8 Ziffern; leer = nicht ändern. Gesetzte PINs lassen sich hier entfernen |

- **PINs werden nie angezeigt** – auch hier nicht. Die Seite zeigt nur „PIN gesetzt“ oder „Kein
  PIN“.
- Es gelten die [PIN-Regeln](benutzer.md#pin-regeln) wie im Dialog: Ein PIN darf keine
  Bedrohungs-PIN einer anderen Person und kein Aktions-Code sein. Passt etwas nicht, wird **gar
  nichts** gespeichert und das Feld zeigt den Grund.
- **Löschen** fragt einmal nach.

Im selben Reiter darunter:

| Abschnitt | Auf der Seite |
|---|---|
| **PIN-Regeln und Master-PIN** | PIN auch zum Scharfschalten, Alarm beenden ohne PIN, Dashboard-Knöpfe trotz PIN, PIN in der Alarmkarte für Konten ohne Person; [Master-PIN](benutzer.md#pins) setzen oder entfernen (nie sichtbar) |
| **[Karten, Anhänger und Schloss-Kennungen](bedienteile.md#karten-anlernen)** | jede Karte mit Person und Zustand (🟢 aktiv, ⏸️ deaktiviert). **„Bearbeiten“:** umbenennen, anderer Person geben, deaktivieren, löschen. **„+ Neue Karte anlernen“:** Karte an ein Keypad oder einen Leser halten – sie erscheint im Blatt von selbst (die Seite fragt alle 2 Sekunden nach) – oder die Nummer eintippen; dann Person wählen. Zufallsnummern (z. B. Handys) werden abgelehnt. Schloss-Kennungen erscheinen genauso, wenn jemand einmal aufschließt, solange alles unscharf ist |
| **[Bedienteile](bedienteile.md)** | anlegen, einstellen, löschen – Keypad (Zigbee2MQTT-Gerät oder Topic, Profil je Taste, Anmeldung, Notruf-Taste), NFC-Aufkleber, RFID-Leser, Taster (Profil je Druckart; Druckarten von Ereignis-Entitäten erscheinen von selbst) und Türschloss (Quelle, Nuki-Topic oder Kennungs-Sensor, optional scharf beim Abschließen). Dazu die **Anlernzeit für Karten** |
| **[Aktions-Codes](bedienteile.md#aktions-codes)** | anlegen, ändern, löschen: Name, Code (2–8 Ziffern), Taste, Keypad, Aktion (Ereignis, Scharf schalten mit Profil, stiller Notruf). Gibt es nur mit Keypad. Ein Aktions-Code darf keinem PIN gleichen – das wird geprüft |

## System bearbeiten

Im Reiter **System** steht oben der Zustand der Überwachung – mit den Knöpfen **Heimkehr-Bericht**
und **Tabelle** zum Herunterladen der [Heimkehr-Beobachtung](beobachtung.md#heimkehr-beobachtung).
Darunter je Thema eine Karte mit **„Bearbeiten“**:

| Karte | Inhalt |
|---|---|
| **Verhalten nach Neustart** | Vorherigen Zustand wiederherstellen · immer scharf (mit Profil je Bereich) · immer unscharf; „Laufenden Alarm fortsetzen“ – siehe [Verhalten nach einem Neustart](installation.md#verhalten-nach-einem-neustart) |
| **Funkstille von Sensoren** | Stunden bis „ausgefallen“ (0 = aus), dazu die Beobachtung – siehe [Funkstille](melder.md#funkstille-von-sensoren) |
| **Funknetz und Gateways** | Statussensoren, z. B. die Zigbee2MQTT-Bridge – siehe [Funknetz](melder.md#funknetz-und-gateways-überwachen) |
| **Anwesenheit und Heimkehr-Beobachtung** | Beobachtung an/aus, Personen, Heim-WLAN(s), zusätzliche Signale je Person – siehe [Heimkehr-Beobachtung](beobachtung.md#heimkehr-beobachtung) |
| **Bereiche** | anlegen, umbenennen, Symbol, löschen (nur ohne Profile) – siehe [Bereiche](profile.md#bereiche) |
| **Einstellungsseite** | diese Seite ausblenden. Danach verschwindet sie; wieder einblenden im Dialog unter Systemeinstellungen → Einstellungsseite |

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

Darunter im selben Reiter:

| Karte | Auf der Seite |
|---|---|
| **[Ton je Sirene](sirenen.md#ton-je-sirene)** | je Sirene „Bearbeiten“: die Töne, die das Gerät meldet, „automatisch“ (Einbruchton) oder ein eigener Name. **Brandtöne** sind gesperrt; nur als Experte mit Haken „Brandton für Einbruch erlauben“ **und** ausdrücklicher Bestätigung – für Sirenen mit eigenen Rauchmeldern nie |
| **[Sirenentest](sirenen.md#sirenentest)** | Erinnerung (aus, alle 3 / 6 Monate, jährlich) und Vorwarnung „Sirenentest in 10 Sekunden“. Den Test selbst startest du in der Testkarte |
| **[Sirene aus Schalter erstellen](sirenen.md#sirene-aus-schalter-erstellen)** | Schalter wählen und bestätigen, dass es eine reine Alarmsirene ist: Hauswacht legt den Helfer „Gerätetyp eines Schalters ändern“ (Typ Sirene) an und trägt die Sirene ein. Der Schalter wird dabei **nicht** geschaltet |

Einen **Sirenentest** gibt es auf der Seite bewusst nicht – nur in der
[Testkarte](sirenen.md#sirenentest).

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
**Sprachausgabe** – darunter im selben Reiter: Lautsprecher (Standard für alle Ereignisse),
Wiederholung der Alarm-Durchsage, Nachtruhe von–bis; je Ereignis an/aus, Durchsage oder Sprechen,
eigene Lautsprecher, „auch in der Nachtruhe“ und der Text (mit Vorschau und „↺ Standardtext“).
Siehe [Sprachausgabe](benachrichtigungen.md#sprachausgabe-lautsprecher).

## Gut zu wissen

- Die Seite **schaltet nichts** – weder Sirenen noch Geräte. Sie ändert nur Einstellungen, und
  nur die, die du speicherst. Helfer legt sie nur an, wenn du es ausdrücklich willst („Sirene aus
  Schalter erstellen“, „Melder aus Messwert erstellen“).
- Der **Einrichtungsassistent** bleibt im Dialog (Knopf „Im Dialog bearbeiten“ → Einrichtungsassistent).
- Gezeigt wird der Stand beim Öffnen; „Neu laden“ (Pfeil oben) holt den aktuellen.
- Dieselben Inhalte gibt es zum Ausdrucken in der Karte [Hauswacht Übersicht](uebersicht.md).
- Auf dem Handy geht die Seite auch; breite Tabellen lassen sich seitlich schieben.
