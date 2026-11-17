# ADR 0009: Einrichtungsassistent und gemeinsame Logikschicht

- Status: vorgeschlagen (Konzept, noch nicht umgesetzt)
- Datum: 2026-11-17

## Kontext

Die Einstellungen von Hauswacht laufen über den Einstellungsdialog von Home Assistant
(Options-Flow): ein Menü mit vielen Unterdialogen. Das ist update-sicher und gut getestet, aber
für Einsteiger steif – man muss vorher wissen, was Meldergruppen, Profile und Auslöseregeln sind
und in welcher Reihenfolge man sie anlegt.

Ein eigenes Einstellungs-Panel (wie bei anderen Alarm-Integrationen) wurde erwogen und **nach
hinten verschoben**: Es hängt an internen Bausteinen des Home-Assistant-Frontends, die sich bei
Updates ändern können, und verdoppelt die Pflege. Für Einsteiger hilft ein Assistent mehr.

Ziel: Hauswacht soll auch für absolute Laien einrichtbar sein – **ohne** Fortgeschrittene
einzuengen.

## Entscheidung

### 1. Ein Einrichtungsassistent im Einstellungsdialog

Der Assistent ist ein eigener Zweig des bestehenden Einstellungsdialogs (Menüpunkt
„Einrichtungsassistent“ ganz oben), kein eigenes Frontend. Damit gilt alles, was den Dialog
sicher macht, auch für den Assistenten:

- nur im unscharfen Zustand,
- **jeder Schritt speichert sofort** – wer abbricht, verliert nichts und macht später weiter,
- dieselben Texte in Deutsch und Englisch über die Übersetzungsdateien.

Der Dialog bleibt vollständig erhalten. Assistent und Dialog sind zwei Wege zu denselben
Einstellungen; was der Assistent anlegt, lässt sich im Dialog ändern und umgekehrt.

Nach der Installation weist Hauswacht auf den Assistenten hin (Text im Installationsschritt und
ein Hinweis, solange noch nichts eingerichtet ist).

### 2. Kurze Einführung vorab

Erste Seite „So arbeitet Hauswacht“ – je Baustein ein Satz und ein Beispiel:

| Baustein | Satz | Beispiel |
|---|---|---|
| Melder | alles, was „offen/zu“ oder „Bewegung“ meldet | Haustür, Fenster Küche, Bewegungsmelder Flur |
| Meldergruppen | Melder, die zusammengehören | „Außen“ = Türen und Fenster, „Innen“ = Bewegungsmelder |
| Auslöseregeln | für Fortgeschrittene: Alarm erst, wenn mehreres zusammenkommt | Haustür auf, danach innerhalb einer Minute Bewegung im Keller |
| Alarmprofile | Situationen, in denen scharf geschaltet wird | „Abwesend“ überwacht alles, „Nacht“ nur außen |
| Sirenen und Empfänger | wer oder was bei Alarm Lärm macht oder Nachricht bekommt | Sirene Flur, Handy Anna |
| Benutzer und Bedienteile | wer schalten darf und womit | PIN, Karte, Keypad, App |

Darunter: „Jeden Schritt kannst du überspringen und später nachholen.“ Knopf **„Einführung
überspringen“**.

### 3. Schritte und Weichen

Jeder Schritt hat **„Überspringen“**. Pflicht ist nur, was technisch zwingend ist (z. B. ein
Name für ein Profil). Wird der Assistent erneut gestartet, zeigt zuerst eine **Kapitel-Auswahl**,
was schon eingerichtet ist, und man springt direkt zu einem Kapitel. Jeder Schritt zeigt das
Vorhandene und **ergänzt statt zu überschreiben**.

| Kapitel | Inhalt | Weiche / Vorschlag |
|---|---|---|
| Bereiche | ein Haus oder mehrere Bereiche (z. B. Einliegerwohnung) | Standard: ein Bereich; Laien sehen nur die Frage „Gibt es getrennte Wohnungen?“ |
| Melder | Vorschläge aus Home Assistant: Türen, Fenster, Garagentore, Bewegung – geordnet nach Etagen und Räumen | alles Erkannte vorgewählt, Häkchen wegnehmen; Typ wird erkannt, änderbar |
| Überwachungsart | **„Wie soll überwacht werden?“** – mit Meldergruppen (einfach) · nur mit Auslöseregeln · beides · später | bestimmt, welche der beiden nächsten Kapitel erscheinen |
| Meldergruppen | Vorschlag „Außen“ (Türen/Fenster) und „Innen“ (Bewegung) | nur bei Meldergruppen oder beidem |
| Auslöseregeln | Sprung in den vorhandenen Regel-Assistenten, danach zurück | nur bei Auslöseregeln oder beidem |
| Alarmprofile | Vorschläge „Abwesend“ (alles, mit Verzögerungen) und „Nacht“ (nur außen); Eingangstüren festlegen | Vorschläge abwählbar, Zeiten mit einem Satz erklärt |
| Empfänger | Handys mit der Home-Assistant-App werden erkannt | **Test-Nachricht** nur auf Knopfdruck |
| Sirenen | auswählen, Ton (wo möglich) | kurzer, leiser **Test nur mit Bestätigung** wie im Sirenentest; **Freigabe** siehe unten |
| Benutzer | Namen, PIN, optional Karte | überspringbar (Bedienung nur über die App) |
| Bedienteile | Keypad, Aufkleber, Leser | Sprung in die vorhandenen Dialoge |
| Probelauf | im **Testmodus**: „Öffne jetzt die Haustür“ – die Liste hakt jeden Melder ab, der sich gemeldet hat | Sirenen sind im Testmodus technisch gesperrt |
| Zusammenfassung | „Eingerichtet ist … / noch offen ist …“ mit denselben **Prüfhinweisen** wie die Anlagenübersicht; nächste Schritte (Alarmkarte aufs Dashboard) | – |

**Überspringen ist sicher:** Wer viel überspringt, bekommt keinen Fehler, sondern eine ehrliche
Zusammenfassung. Ein Profil, das niemanden erreicht, wird dort genauso benannt wie in der
Übersicht.

### 4. Was der Assistent nie nebenbei tut

- Die **Freigabe der Sirenen** und das **Ausschalten des Testmodus** sind eigene Schritte mit
  ausdrücklicher Bestätigung – nie Teil von „Weiter, weiter, fertig“.
- Er schaltet keine Geräte außer dem bestätigten Sirenentest (kurz, leise, einzeln) und sendet
  Nachrichten nur auf Knopfdruck.
- Er ändert keine Rauchmelder, Automationen oder Skripte.
- Vorschläge werden nur übernommen, wenn man das Kapitel bestätigt – ein übersprungenes Kapitel
  legt nichts an.

### 5. Gemeinsame Logikschicht

Heute stecken im Einstellungsdialog (rund 4000 Zeilen) Formulare **und** Regeln vermischt: rund
60 Stellen prüfen Eingaben selbst (Name doppelt, Aktions-Code ist ein PIN, Ausnahme nicht in
einer Gruppe …) und schreiben selbst in die Einstellungen.

Die Regeln wandern in den reinen Kern (`core/`), als Funktionen nach dem Muster:

```python
result = add_action_code(options, {"name": "Licht", "code": "7777", "key": "arm_day_zones"})
result.options  # neue Einstellungen, fertig zum Speichern – oder
result.errors   # {"code": "action_code_is_pin"}
```

Dialog und Assistent zeigen nur noch Formulare und rufen dieselben Funktionen auf. Eine Regel
steht an genau einer Stelle und wird im Kern einmal gründlich getestet. Ein späteres Panel kann
dieselben Funktionen nutzen.

Der Umbau ist **unsichtbar**: Der Dialog verhält sich exakt wie vorher; die bestehenden
Dialog-Tests sichern das ab. Er geschieht Stück für Stück, zuerst für die Teile, die der
Assistent braucht.

## Reihenfolge

1. **Logikschicht** für Melder, Meldergruppen, Profile, Empfänger, Sirenen-Auswahl, Benutzer –
   je Bereich ein kleiner Pull Request, ohne sichtbare Änderung.
2. **Assistent, Teil 1:** Einführung, Melder, Überwachungsart, Meldergruppen, Auslöseregeln
   (Sprung), Profile, Zusammenfassung.
3. **Assistent, Teil 2:** Empfänger mit Test-Nachricht, Sirenen, Benutzer, Bedienteile.
4. **Assistent, Teil 3:** Probelauf im Testmodus, Kapitel-Auswahl beim erneuten Start.
5. Dokumentation (deutsch und englisch) wächst mit jedem Teil: eigene Seite „Einrichtung mit dem
   Assistenten“, Installationsanleitung verweist darauf.

Das Einstellungs-Panel kommt frühestens danach und bekommt ein eigenes Konzept.

## Folgen

- Einsteiger kommen ohne Vorwissen zu einer funktionierenden Anlage; Fortgeschrittene können
  jedes Kapitel überspringen oder weiter nur den Dialog nutzen.
- Mehr Arbeit je neuer Funktion: Sie muss im Dialog und – wo sinnvoll – im Assistenten
  erscheinen. Durch die gemeinsame Logikschicht ist das nur Formular-Arbeit.
- Der Kern wächst um die Einstellungsregeln und wird dadurch besser testbar.
- Grenzen des Einstellungsdialogs bleiben (keine echten Tabellen, keine Live-Ansicht außer über
  Fortschrittsschritte). Der Probelauf wird deshalb eine Liste mit „Aktualisieren“ bzw. ein
  Warteschritt wie beim Anlernen von Karten.

## Offene Fragen (vor dem Bau klären)

- Soll der Assistent nach der Installation **automatisch** starten oder nur angeboten werden?
- Soll der Probelauf den Testmodus selbst einschalten (mit Hinweis) oder darum bitten?
- Bereiche im Assistenten nur als Ja/Nein-Frage oder vollständig?
