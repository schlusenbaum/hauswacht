# Einstellungsseite „Hauswacht“ in der Seitenleiste

**Deutsch** | [English](en/settings-page.md)

> Die Seite **zeigt** die ganze Einrichtung, und du bearbeitest **alles** direkt auf ihr. Seit
> 0.63.2 ist sie der **einzige Weg** – den früheren Einstellungsdialog gibt es nicht mehr.
> Die Seite schaltet nichts – einzige Ausnahme ist der **Sirenentest** (Reiter Alarmgeber,
> Karte „Sirenentest“), mit Rückfrage und nur für Administratoren.

Die Seite **Hauswacht** in der Seitenleiste von Home Assistant zeigt alles auf einen Blick: welche
Melder in welcher Gruppe stecken, in welchem Profil sie scharf sind, wer welche Nachricht bekommt –
und du änderst es an Ort und Stelle.

- Nur für **Administratoren** sichtbar.
- **Öffnen:** über die Seitenleiste, über den Link in der Geräteinfo auf der Geräteseite von
  Hauswacht, über **Konfigurieren** bei der Integration (zeigt einen Link hierher) oder direkt
  unter `/hauswacht-settings` (z. B. `http://homeassistant.local:8123/hauswacht-settings`).
- **Ausblenden statt abschalten** (ab 0.61): Die Seite gibt es immer. Unter System →
  **Einstellungsseite** stellst du nur ein, ob sie in der Seitenleiste steht. Ausgeblendet
  erreichst du sie über die Wege oben. Jeder Benutzer kann sie außerdem über „Seitenleiste
  bearbeiten“ in Home Assistant für sich ausblenden.
- **Neu hier?** Im Reiter **Dokumentation** erklärt
  [So entscheidet Hauswacht](so-entscheidet-hauswacht.md) die Abläufe in Bildern.
- **Erklärungen direkt am Feld** (ab 0.62): In allen Seitenblättern – Profile, Melder,
  Auslöseregeln, Alarmgeber und Benachrichtigungen, Personen, Bedienteile, System – steht hinter
  den Feldern ein **ⓘ**. Mauszeiger drauf zeigt die Erklärung, Antippen (Handy, Tablet) klappt
  sie auf. Wo es hilft, beschreibt ein Satz **„So verhält sich das:“**, was die Einstellung
  gerade bewirkt.

## Die Reiter

| Reiter | Inhalt |
|---|---|
| **Übersicht** | Prüfhinweise (z. B. „Profil ohne Empfänger“) und der Zustand je Bereich; Knöpfe **Drucken** und **Notfallblatt** wie in der Karte [Hauswacht Übersicht](uebersicht.md) |
| **Assistent** | [Einrichten nach Zielen](assistent.md#einrichten-nach-zielen-seit-0650b1), [Check-up](assistent.md#check-up-im-reiter-assistent-seit-0640b3) (was in den Einstellungen nicht zusammenpasst, mit Vorschlägen zum einzelnen Übernehmen) und [„Was passiert, wenn …?“](assistent.md#was-passiert-wenn--seit-0640b4) |
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
| **Einzelner Melder** | Auf den **Namen** des Melders in der Tabelle klicken | **Meldergruppe** (verschieben oder herausnehmen), **Typ**, **Immer aktiv** und je Profil, ob er dort **allein auslöst** – Haken weg = in diesem Profil ausgenommen (z. B. Bewegungsmelder Flur nachts). Dazu die **Funkstille** dieses Melders (wie allgemein, eigener Wert, nie prüfen) mit Beobachtung und „Empfehlung übernehmen“ – siehe [Eigene Grenze je Melder](melder.md#eigene-grenze-je-melder). Steckt der Melder über ein Label in seiner Gruppe, wechselst du die Gruppe über das Label an der Entität |
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

Sicher gespeichert:

- **Geprüft:** Jede Änderung läuft durch dieselben Einstellungsregeln. Ein Melder in zwei
  Gruppen, eine Gruppe ohne Namen, „gekippt“ und „zu“ für denselben Wert – das wird mit einer
  Meldung am Feld abgelehnt.
- **Nur unscharf:** Ist ein Bereich scharf, fehlen die Knöpfe; oben steht „Ändern geht nur, wenn
  alle Bereiche unscharf sind“.
- **Nichts überschreiben:** Hat jemand zwischendurch auf einem anderen Gerät etwas
  geändert, speichert die Seite nicht, sondern lädt neu – dann einfach noch einmal.
- Nach dem Speichern lädt Hauswacht seine Einstellungen neu (ein, zwei Sekunden), danach zeigt
  die Seite den neuen Stand mit „✓ Gespeichert.“

## Profile bearbeiten

Im Reiter **Profile** steht jedes Profil mit seinen Werten; **„Bearbeiten“** öffnet das
Seitenblatt, **„+ Alarmprofil anlegen“** ein leeres mit den üblichen Vorgaben (30 s Verzögerung,
180 s Alarm …).

**Erklärungen direkt am Feld** (ab 0.62):

- Hinter jedem Feld steht ein **ⓘ**: Mauszeiger drauf zeigt die Erklärung, Antippen (Handy,
  Tablet) klappt sie auf.
- Unter den wichtigsten Feldern eines Abschnitts steht der Satz **„So verhält sich das:“**. Er
  ändert sich sofort, wenn du etwas einstellst – z. B. „Nach dem Scharfschalten hast du 30 s zum
  Verlassen. Öffnest du danach eine Eingangstür, hast du 30 s zum Unscharfschalten …“.
- Selten geänderte Felder stehen unter **„Mehr Einstellungen“** zum Aufklappen: Symbol; Dauer
  der Alarmreaktion und Alarmzyklen; ausgefallene Melder und Manipulation; Ton, Lautstärke und
  Lautsprecher; Zeitplan; Beruhigungszeit; beim Durchgang „welche Tür“ und „Ende“.
- Felder, die nur mit einem Schalter Sinn ergeben (Ausgangstüren, Durchgangszeiten), erscheinen
  erst, wenn der Schalter an ist.

| Abschnitt | Inhalt |
|---|---|
| **Allgemein** | Name, Knopf am Bedienfeld, Bereich (nur bei mehreren Bereichen); unter „Mehr Einstellungen“ das Symbol (z. B. `mdi:weather-night`) |
| **Was wird überwacht** | Meldergruppen (jeder Melder löst allein aus), **Ausgenommene** – die Liste zeigt genau die Melder der angehakten Gruppen –, Auslöseregeln, „Gekippte Fenster erlaubt“ (nur mit [Meldern mit Kippstellung](melder.md#melder-mit-kippstellung-gekippt)) |
| **Zeiten** | Ausgangs- und Eingangsverzögerung, Dauer der Alarmreaktion, Höchstzahl Alarmzyklen |
| **Beim Scharfschalten** | Offene Melder, ausgefallene Melder, Manipulation löst Alarm aus |
| **Reaktion bei Alarm** | Sirenen (die unter Alarmgeber eingetragenen), Ton, Lautstärke, stiller Alarm, Empfänger, zusätzliche Lautsprecher |
| **Automatik** | Scharf um / unscharf um, Wochentage, Zeitplan, Personen („alle weg“), Wartezeit – siehe [Automatik](profile.md#automatik). **„Zeitplan anlegen ↗“** öffnet die Helfer in einem neuen Fenster („Helfer erstellen“ → „Zeitplan“); danach **„Liste aktualisieren“** – deine Eingaben im Profil bleiben dabei erhalten |
| **Bei Rückkehr** *(neu in 0.61, nur hier)* | Was passiert, wenn jemand heimkommt: Stufe (Nichts, Unscharf nur wenn automatisch scharf, Unscharf mit Türbeleg, Unscharf auch nach Scharfschalten von Hand, Reinlassen), eigene Personenliste, unter **„Mehr Einstellungen“** das Zeitfenster Handy und Tür sowie die [Eingangsverzögerung nach Annäherung](profile.md#annäherung-verlängert-die-eingangsverzögerung) mit Gültigkeit und Empfehlungen zum Übernehmen. Mit **ⓘ** je Feld, dem Satz **„So verhält sich das:“** und einer Warnung bei „auch nach Scharfschalten von Hand“ – siehe [Bei Rückkehr](profile.md#bei-rückkehr) |
| **Scharf durch Schließen der Tür** | An/aus, Ausgangstüren (die Melder vom Typ Tür in den gewählten Gruppen), Beruhigungszeit |
| **Durchgang** | Durchgang erlauben, Zeiten, welche Tür, Melder auf dem Weg – siehe [Durchgang](durchgang.md). Das Handy-Reinlassen ist zu „Bei Rückkehr“ umgezogen |

Es gelten diese Regeln: Name nötig und eindeutig, jeder Knopf nur einmal je
Bereich, „Bei Rückkehr“ (außer „Nichts“) nur mit mindestens einer Person. **Löschen** fragt einmal nach.

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
- Gespeichert wird nur eine gültige Regel: Name nötig und eindeutig, kein
  leerer Schritt, nicht derselbe Melder in zwei Schritten hintereinander. **Löschen** fragt einmal
  nach und nimmt die Regel auch aus allen Profilen.

## Personen bearbeiten

Im Reiter **Personen und Bedienteile** steht jede Person mit ihren Rechten und Ausweisen („alle
Rechte · PIN · 2 Karten“). **„Bearbeiten“** öffnet das Seitenblatt, **„+ Person anlegen“** ein
leeres. Was Personen, PINs und Rechte sind, steht unter [Benutzer, PINs und Sperre](benutzer.md).

| Feld | Inhalt |
|---|---|
| **Name** | Vorschläge aus den Home-Assistant-Konten. Heißt die Person wie ein Konto, wird sie damit verknüpft |
| **Aktiv** | Aus = die Person kann nichts schalten (z. B. vorübergehend gesperrt) |
| **Darf …** | scharf schalten, unscharf schalten, Alarm beenden. Bei mehreren Bereichen wahlweise **je Bereich** – dann ein Kasten je Bereich |
| **Trotzdem scharf am Keypad** | offene Melder überbrücken, siehe [Trotzdem scharf am Keypad](bedienteile.md#trotzdem-scharf-am-keypad) |
| **PIN in der Alarmkarte** | z. B. für ein Wandtablet, das immer angemeldet ist |
| **Gültig ab / bis** | für Gäste oder Handwerker; außerhalb der Zeit wird die Person abgewiesen |
| **Home-Assistant-Konto** | ausdrücklich verknüpfen (sonst automatisch nach Name) |
| **PIN** | Neuer PIN und neue [Bedrohungs-PIN](benutzer.md#bedrohungs-pin), jeweils 4 bis 8 Ziffern; leer = nicht ändern. Gesetzte PINs lassen sich hier entfernen |

- **PINs werden nie angezeigt** – auch hier nicht. Die Seite zeigt nur „PIN gesetzt“ oder „Kein
  PIN“.
- Es gelten die [PIN-Regeln](benutzer.md#pin-regeln): Ein PIN darf keine
  Bedrohungs-PIN einer anderen Person und kein Aktions-Code sein. Passt etwas nicht, wird **gar
  nichts** gespeichert und das Feld zeigt den Grund.
- **Löschen** fragt einmal nach.

Im selben Reiter darunter:

| Abschnitt | Auf der Seite |
|---|---|
| **PIN-Regeln und Master-PIN** | PIN auch zum Scharfschalten, Alarm beenden ohne PIN, Dashboard-Knöpfe trotz PIN, PIN in der Alarmkarte für Konten ohne Person; [Master-PIN](benutzer.md#pins) setzen oder entfernen (nie sichtbar) |
| **[Karten, Anhänger und Schloss-Kennungen](bedienteile.md#karten-anlernen)** | jede Karte mit Person und Zustand (🟢 aktiv, ⏸️ deaktiviert). **„Bearbeiten“:** umbenennen, anderer Person geben, deaktivieren, löschen. **„+ Neue Karte anlernen“:** Karte an ein Keypad oder einen Leser halten – sie erscheint im Blatt von selbst (die Seite fragt alle 2 Sekunden nach) – oder die Nummer eintippen; dann Person wählen. Zufallsnummern (z. B. Handys) werden abgelehnt. Schloss-Kennungen erscheinen genauso, wenn jemand einmal aufschließt, solange alles unscharf ist |
| **[Bedienteile](bedienteile.md)** | anlegen, einstellen, löschen – Keypad (Zigbee2MQTT-Gerät oder Topic, Profil je Taste, Anmeldung, Notruf-Taste), [Keypad (allgemein)](bedienteile.md#keypad-allgemein) (Tasten mit freiem Namen, Kennung für Automationen, [fertige Vorlagen](bedienteile.md#fertige-vorlagen) importieren – öffnet in einem neuen Tab; hat sich ein **unbekanntes Keypad** gemeldet, steht es oben im Abschnitt mit **„Anlegen“**), [MQTT-Schnittstelle](bedienteile.md#mqtt-schnittstelle) (Basis-Topic, Befehlswörter, Zustandswörter), NFC-Aufkleber, RFID-Leser, Taster (Profil je Druckart; Druckarten von Ereignis-Entitäten erscheinen von selbst) und Türschloss (Quelle, Nuki-Topic oder Kennungs-Sensor, optional scharf beim Abschließen). Dazu die **Anlernzeit für Karten** |
| **[Aktions-Codes](bedienteile.md#aktions-codes)** | anlegen, ändern, löschen: Name, Code (2–8 Ziffern), Taste, Keypad, Aktion (Ereignis, Scharf schalten mit Profil, stiller Notruf). Gibt es nur mit Keypad. Ein Aktions-Code darf keinem PIN gleichen – das wird geprüft |

## System bearbeiten

Im Reiter **System** steht oben der Zustand der Überwachung – mit den Knöpfen **Heimkehr-Bericht**
und **Tabelle** zum Herunterladen der [Heimkehr-Beobachtung](beobachtung.md#heimkehr-beobachtung).
Darunter je Thema eine Karte mit **„Bearbeiten“**. In jedem Seitenblatt steht ab 0.62 hinter
jedem Feld ein **ⓘ** mit Erklärung, und wo es hilft, ein Satz **„So verhält sich das:“** – z. B.
bei den PIN-Regeln („Unscharf schalten am Bedienfeld, Keypad und per Sprache nur mit PIN.
Scharfschalten geht ohne PIN …“), bei der Funkstille, bei Aktions-Codes, beim Melder aus
Messwert („Unter 5 meldet der Melder „Problem“, wieder normal über 6.“) und bei der Anlernzeit.

| Karte | Inhalt |
|---|---|
| **Verhalten nach Neustart** | Vorherigen Zustand wiederherstellen · immer scharf (mit Profil je Bereich) · immer unscharf; „Laufenden Alarm fortsetzen“ – siehe [Verhalten nach einem Neustart](installation.md#verhalten-nach-einem-neustart) |
| **Funkstille von Sensoren** | Allgemeiner Wert (Stunden bis „ausgefallen“, 0 = aus) und eine Tabelle **je Melder**: längste Pause, Empfehlung, eigener Wert – Melder anklicken, um ihm einen eigenen Wert zu geben. Seit wann gemessen wird, steht unten; **Messung zurücksetzen** löscht die Messung aller Melder und beginnt neu. Siehe [Funkstille](melder.md#funkstille-von-sensoren) |
| **Funknetz und Gateways** | Statussensoren, z. B. die Zigbee2MQTT-Bridge – siehe [Funknetz](melder.md#funknetz-und-gateways-überwachen) |
| **Anwesenheit und Heimkehr-Beobachtung** | Beobachtung an/aus, Personen, Heim-WLAN(s), zusätzliche Signale je Person – siehe [Heimkehr-Beobachtung](beobachtung.md#heimkehr-beobachtung). Darunter **„Wann gilt jemand als weg?“** (ab 0.61, nur hier): Ortung außerhalb **genau prüfen** oder **einfach**, unter „Mehr Einstellungen“ das **Zeitfenster für den Beleg** (Standard 15 Minuten) mit Empfehlung aus der Messung „Weggehen“ und Knopf **übernehmen**; je Person **„Beleg für ‚weg‘“**: nur Ortung (sicher) oder auch Tür + Signal (unsicher, mit Warnung und eigenem Zeitfenster); ab 0.65.0b4 je Person **„Zählt als Ortung (Geofence)“** für Quellen ohne Koordinaten, die den Standort auswerten ([mehr](profile.md#weg-nur-mit-beleg)); Warnung für Personen ohne Ortung – siehe [„weg“ nur mit Beleg](profile.md#weg-nur-mit-beleg). Ab 0.63 zeigt die Karte außerdem **„Wer gilt gerade als zuhause?“**: je Person zuhause/weg/unbekannt mit Grund und je Profil eine Zeile, was Automatik und „Bei Rückkehr“ gerade machen; ab 0.65.0b4 bei „kein Beleg“ auch, was fehlt, und ein Knopf **Aktualisieren** – siehe [Anwesenheit testen](testmodus.md#anwesenheit-testen). Darunter der Block **Messungen**: ansehen, speichern, zurücksetzen – siehe [Messungen auf der Einstellungsseite](beobachtung.md#messungen-auf-der-einstellungsseite) |
| **Bereiche** | anlegen, umbenennen, Symbol, löschen (nur ohne Profile) – siehe [Bereiche](profile.md#bereiche) |
| **Einstellungsseite** | **In der Seitenleiste zeigen** an/aus. Ausgeblendet verschwindet nur der Eintrag in der Seitenleiste – die Seite bleibt über die Geräteseite, „Konfigurieren“ bei der Integration und `/hauswacht-settings` erreichbar |
| **Konfiguration herunterladen** | Eine Datei (JSON) für die Fehlersuche, mit Platzhaltern statt Namen und Geheimnissen – siehe [Konfiguration herunterladen](#konfiguration-herunterladen) (ab 0.65.0b8) |

## Konfiguration herunterladen

*Ab 0.65.0b8.* Im Reiter **System** steht ganz unten die Karte **„Konfiguration herunterladen“**.
Der Knopf **⬇ Herunterladen** speichert eine Datei `hauswacht-konfiguration-<Datum>.json`. Sie ist
für die **Fehlersuche** gedacht: Wenn Hauswacht etwas anders macht als erwartet, steht darin alles,
um es nachzuvollziehen – ohne zehnmal nachzufragen. Anhängen z. B. an ein
[Issue](https://github.com/schlusenbaum/hauswacht/issues) oder an einen Forenbeitrag.

**Was drinsteht**

| Abschnitt | Inhalt |
|---|---|
| `versions` | Versionen von Hauswacht, Home Assistant und Python |
| `options` | alle Einstellungen, genau wie gespeichert |
| `overview` | die [Anlagenübersicht](uebersicht.md) mit Prüfhinweisen |
| `presence` | **„Wer gilt gerade als zuhause?“** – je Person mit Grund, je Profil, was die Automatik macht |
| `facts` | was Hauswacht aus Home Assistant weiß: wer geortet werden kann, wer ein Richtungs-Signal hat, eingefrorene Ortungen, Eingangstüren und Fenster je Profil |
| `measurements` | die [Messungen](beobachtung.md#messungen-auf-der-einstellungsseite) (Heimkehr, Weggehen, Eingänge) |
| `findings` | das Ergebnis des [Check-ups](assistent.md) |
| `scenarios` | „Was passiert, wenn …?“ – durchgerechnet mit deinen Einstellungen |
| `entities` | Zustand der eigenen Hauswacht-Entitäten und aller Entitäten, die in den Einstellungen vorkommen (z. B. Melder, Tracker, Signale): Zustand, letzte Änderung, Integration, ausgewählte Attribute wie `source_type` oder `in_zones` |

**Was nicht drinsteht – Platzhalter statt echter Werte**

Hauswacht ersetzt vor dem Speichern alles Persönliche durch **Platzhalter**. Die Zuordnung bleibt
erhalten: Dieselbe Person heißt überall gleich, auch in Entitäts-IDs und Sätzen. So sieht man,
*welcher* Tracker zu *welcher* Person gehört, aber nicht, wer das ist.

| Echt | In der Datei |
|---|---|
| `person.anna`, „Anna“, `sensor.handy_von_anna`, „Annas Zimmer“ | `person.person_1`, „Person 1“, `sensor.handy_von_person_1`, „Person 1s Zimmer“ |
| Benutzer „Ben Beispiel“ | `benutzer_1`, „Benutzer 1“ |
| Kartennummer `04A1B2C3D4`, Kartenname | `karte_1`, „Kartenname 1“ |
| `notify.mobile_app_handy_von_anna` | `notify.empfaenger_1` |
| WLAN-Name, MQTT-Topic, Geräte-ID, HA-Konto, Lautsprecher | `wlan_1`, `topic_1`, `geraet_1`, `konto_1`, `media_player.lautsprecher_1` |
| PIN-Hashes, Salze, Aktions-Codes | `***` |
| Koordinaten | nie dabei – nur `has_coordinates: true/false` |

Eine Fassung ohne Platzhalter gibt es bewusst nicht: So eine Datei landet schnell versehentlich
im Forum.

**Bitte trotzdem kurz drüberschauen:** Namen von Meldern, Zonen, Bereichen und Profilen bleiben
(„Haustür“, „Nacht“), weil man sie zum Verstehen braucht. Steht darin etwas Persönliches, das
nicht der Name einer Person in Home Assistant ist (z. B. „Zimmer von Oma Erika“), bleibt es
stehen – dann vor dem Weitergeben ändern.

Der Knopf liest nur – er schaltet nichts und ändert nichts. Nur Administratoren können ihn nutzen.
Die [Diagnose-Datei](uebersicht.md#diagnose-datei-für-fehlerberichte) von Home Assistant gibt es
weiterhin; die neue Datei enthält mehr (Zustand, Fakten, Check-up) und entfernt Personen nicht,
sondern ersetzt sie durch Platzhalter.

## Alarmgeber bearbeiten

Im Reiter **Alarmgeber** öffnet **„Sirenen bearbeiten“** das Seitenblatt:

- **Eingetragene Sirenen** – mit ✕ austragen; darunter alle weiteren Sirenen (`siren.…`) zum
  Antippen. Wird eine Sirene ausgetragen, verschwindet sie auch aus den Profilen und ihr Ton wird
  vergessen.
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
| **[Sirenentest](sirenen.md#sirenentest)** | Erinnerung (aus, alle 3 / 6 Monate, jährlich) und Vorwarnung „Sirenentest in 10 Sekunden“. Darunter der **Test selbst**, siehe unten |
| **[Sirene aus Schalter erstellen](sirenen.md#sirene-aus-schalter-erstellen)** | Schalter wählen und bestätigen, dass es eine reine Alarmsirene ist: Hauswacht legt den Helfer „Gerätetyp eines Schalters ändern“ (Typ Sirene) an und trägt die Sirene ein. Der Schalter wird dabei **nicht** geschaltet |

### Sirenentest auf der Seite (echte Sirene!)

Unten in der Karte **Sirenentest** steht jede Sirene mit ihrem letzten Test (Datum, ✅ gehört,
❌ nicht gehört). So testest du:

1. Anhaken: **„Ich bin vor Ort, Mitbewohner sind informiert“**. Erst dann lassen sich die Knöpfe
   drücken.
2. Bei einer Sirene **Testen …** drücken.
3. Rückfrage „Sirene ertönt jetzt 3 s leise. Wirklich starten?“ → **Ja, starten** oder
   **Abbrechen**.
4. Während des Tons steht **Stopp** bereit. Rauchmelder mit Batterie reagieren oft erst nach
   einigen Sekunden.
5. „Hast du die Sirene gehört?“ → **Ja, gehört** oder **Nein**. Das Ergebnis wird mit Datum
   gespeichert.

Es ist derselbe Weg wie in der [Testkarte](sirenen.md#sirenentest), die ihn weiterhin auch hat.
Alle Sperren prüft Hauswacht im Hintergrund – unabhängig davon, wo du startest: alle Bereiche
unscharf, Hardware-Freigabe an, Testmodus aus, keine Brandsperre, nur Einbruchtöne, höchstens
10 s. Ist etwas gesperrt, steht der Grund in der Karte (⛔). Starten dürfen nur
**Administratoren**.

## Benachrichtigungen bearbeiten

Im Reiter **Benachrichtigungen** gibt es zwei Knöpfe:

**„Empfänger und Ereignisse bearbeiten“** – alle Einstellungen zu Benachrichtigungen auf einem Blatt:

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

- Die Seite **schaltet nichts** – keine Geräte, keine Sirenen; einzige Ausnahme ist der
  [Sirenentest](#sirenentest-auf-der-seite-echte-sirene) mit Rückfrage. Sie ändert nur Einstellungen, und
  nur die, die du speicherst. Helfer legt sie nur an, wenn du es ausdrücklich willst („Sirene aus
  Schalter erstellen“, „Melder aus Messwert erstellen“).
- Einen **Einrichtungsassistenten** gibt es derzeit nicht; ein neuer auf dieser Seite ist geplant – siehe [Einrichtungsassistent](assistent.md).
- Gezeigt wird der Stand beim Öffnen; „Neu laden“ (Pfeil oben) holt den aktuellen.
- Dieselben Inhalte gibt es zum Ausdrucken in der Karte [Hauswacht Übersicht](uebersicht.md).
- Auf dem Handy geht die Seite auch; breite Tabellen lassen sich seitlich schieben.
