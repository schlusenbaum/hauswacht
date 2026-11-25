# ADR 0011: Einstellungsseite in der Seitenleiste – zusätzlich zum Dialog

- Status: umgesetzt in 0.57.0 (Vorabversionen 0.57.0b1–b14; alle fünf Stufen; alles lässt sich auf der
  Seite einstellen; seit 0.60 auch der Sirenentest, siehe Nachtrag)
- Datum: 2026-11-18

## Kontext

Alle Einstellungen laufen bisher über den Einstellungsdialog von Home Assistant (Options-Flow)
und den Einrichtungsassistenten (ADR 0009). Der Dialog ist update-sicher und gut getestet, aber
mit jeder Funktion gewachsen: Alarmauslösung (Meldergruppen, Auslöseregeln, Immer aktiv,
Besondere Melder, Melder aus anderem Sensor), Alarmprofile, Sirenen, Benachrichtigungen und unter
System noch Bereiche, Benutzer, Bedienteile, Funkstille, Funknetz, Heimkehr und Neustart.

Das Problem ist weniger das Ändern als der **Überblick**: Ein Dialog zeigt immer nur einen
Schritt. Wer wissen will „welche Melder sind in welcher Gruppe, welches Profil nutzt sie, wer
bekommt welche Nachricht?“, muss sich durch viele Menüs klicken. Der Assistent hilft beim Start,
nicht beim Pflegen einer gewachsenen Anlage.

ADR 0009 hat ein eigenes Panel bewusst nach hinten geschoben und vorher die gemeinsame
Logikschicht (`core/changes/`) gebaut – genau damit ein Panel später dieselben Regeln nutzen
kann, ohne sie zu verdoppeln. Diese Voraussetzung ist jetzt zum großen Teil erfüllt.

## Entscheidung

### 1. Eine Einstellungsseite – zusätzlich, nicht statt

Hauswacht bekommt eine eigene Seite in der Seitenleiste von Home Assistant: **„Hauswacht“**.

- **Dialog und Assistent bleiben vollständig erhalten.** Alle drei Wege schreiben in dieselben
  Einstellungen (die Optionen des Konfigurationseintrags) – was auf der Seite geändert wird, steht
  sofort im Dialog und umgekehrt. Es gibt keinen zweiten Datenbestand.
- Sichtbar nur für **Administratoren** (wie der Dialog).
- Wer die Seite nicht mag, blendet sie aus (Einstellung unter System) – der Dialog reicht weiter
  für alles.

### 2. Aufbau: erst Überblick, dann Bearbeiten

Oben Reiter, darunter Listen mit dem Wichtigsten auf einen Blick; ein Klick öffnet das Bearbeiten
in einem Seitenblatt (Formular rechts bzw. auf dem Handy als ganze Seite).

| Reiter | Liste zeigt | Bearbeiten |
|---|---|---|
| **Übersicht** | Zustand je Bereich, Prüfungen und Hinweise (wie die Anlagenübersicht), offene Punkte („Profil ohne Empfänger“, „Sirene nicht freigegeben“) | – (Sprünge in die Reiter) |
| **Melder** | Meldergruppen mit ihren Meldern (Typ, Zustand, Batterie, in welchen Profilen scharf), Besondere Melder, Immer aktiv | Gruppen, Typen, Fehlalarmschutz, Besondere Melder, Immer aktiv |
| **Profile** | Profile mit Gruppen, Regeln, Zeiten, Automatik, Sirenen, Empfängern | alles wie im Dialog |
| **Auslöseregeln** | Regeln als Satz („Tür, dann Keller innerhalb von 2 Minuten“), wo sie gelten | Regeln |
| **Alarmgeber** | Sirenen mit Freigabe, Ton, letzter Test | Auswahl, Ton je Sirene (Freigabe siehe unten) |
| **Benachrichtigungen** | je Ereignis: an/aus, Empfänger, Text | Empfänger, Texte, Ansagen |
| **Personen und Bedienteile** | Benutzer mit Rechten und Ausweisen (ohne PINs), Bedienteile, Aktions-Codes | wie im Dialog |
| **System** | Bereiche, Funkstille, Funknetz, Heimkehr, Neustart | wie im Dialog |

Der Kern ist die **Matrix „Melder × Profile“** im Reiter Melder: für jeden Melder auf einen
Blick, in welchem Profil er allein auslöst, ausgenommen ist oder nur in Regeln zählt – genau das,
was im Dialog heute am schwersten zu sehen ist.

### 3. Technik: update-sicher, ohne Bauschritt

- Die Integration meldet die Seite selbst an (`panel_custom`, Modul aus dem eigenen Ordner wie die
  Karten). Kein Eintrag in der `configuration.yaml`, keine Ressource.
- **Nur stabile Bausteine:** wie bei den Karten reine Web-Components, `ha-card`, `ha-icon` und
  die Farbvariablen des Themas (hell/dunkel automatisch). **Keine** internen Formular-Bausteine
  des Home-Assistant-Frontends (Selektoren, `ha-form`) – die ändern sich zwischen Versionen und
  würden die Seite bei Updates brechen.
- Daraus folgt: eine **eigene Melder-Auswahl** (Suchfeld über alle Entitäten mit Namen, Bereich
  und Filter nach Art) statt der Auswahl von Home Assistant. Sie wird einmal gebaut und überall
  genutzt.
- Kein Build-Werkzeug, keine Fremdbibliothek: eine JavaScript-Datei je Reiter-Gruppe, wie die
  bestehenden Karten. Texte deutsch und englisch nach der Sprache von Home Assistant.

### 4. Datenweg: dieselbe Logik wie Dialog und Assistent

Zwei eigene Websocket-Befehle (nur für Administratoren):

- `hauswacht/settings/get` – Einstellungen plus Aufbereitetes (Namen, Bereiche, Typen,
  Zustände, Prüfungen), dazu eine **Revision** (Prüfsumme der Einstellungen).
- `hauswacht/settings/apply` – `{bereich, aktion, id, daten, revision}`. Der Befehl ruft die
  **Funktion der Logikschicht** auf (z. B. `save_zone`, `save_profile`) und speichert deren
  Ergebnis. Fehler kommen je Feld zurück und stehen direkt am Feld.

Regeln:

- **Gleiche Prüfungen wie im Dialog** – sie stehen nur einmal, in `core/changes/`.
- **Nur unscharf:** Ist ein Bereich scharf, zeigt die Seite alles, lässt aber nichts ändern
  (wie der Dialog).
- **Revision:** Hat jemand zwischendurch im Dialog oder auf einem anderen Gerät etwas geändert,
  wird nicht überschrieben, sondern „inzwischen geändert – neu laden“ gemeldet.

Wo die Logikschicht noch fehlt (Auslöseregeln, Immer aktiv, Besondere Melder, Bedienteile,
Aktions-Codes, System), wird sie **zuerst** nachgezogen – unsichtbar für Nutzer, Dialog-Tests
sichern das ab (wie in ADR 0009).

### 5. Sicherheit

- **Sirenen-Freigabe** nur mit derselben ausdrücklichen Bestätigung wie im Dialog; **kein
  Sirenentest** auf der Seite (dafür bleibt die Testkarte mit ihren Sperren).
- Die Seite **schaltet keine Geräte** und ändert nichts an Rauchmeldern oder Brandfunktionen.
- **PINs** lassen sich setzen, aber nie anzeigen (gespeichert sind ohnehin nur Prüfwerte).
- Nichts Geheimes im Browser-Speicher; die Seite hält nur den angezeigten Stand.

### 6. Reihenfolge

1. **Seite und Übersicht** (nur lesen): Reiter Übersicht und Melder mit der Matrix
   „Melder × Profile“, Links in den Dialog. Schon das löst den größten Teil der
   Unübersichtlichkeit.
2. **Bearbeiten: Melder** – Meldergruppen, Typen, Fehlalarmschutz, Besondere Melder, Immer aktiv;
   dazu die eigene Melder-Auswahl.
3. **Bearbeiten: Profile.**
4. **Auslöseregeln, Alarmgeber, Benachrichtigungen.**
5. **Personen und Bedienteile, System.**

Jede Stufe ist eine Vorabversion auf dem Entwicklungszweig; zusammengeführt wird, wenn eine Stufe
im Alltag passt. Die Doku (deutsch und englisch) bekommt eine eigene Seite „Einstellungsseite“
und wächst mit.

## Abwägung

- **Nur den Dialog aufräumen** (Menüs umsortieren, mehr „Vorhanden“-Listen): hilft etwas, aber ein
  Dialog zeigt immer nur einen Schritt – der Überblick fehlt weiter. Wird trotzdem gemacht, wo es
  nebenbei passt.
- **Seite statt Dialog:** riskant – fällt die Seite nach einem Update aus, gäbe es keinen Weg
  mehr. Verworfen; der Dialog bleibt der sichere Weg.
- **Formular-Bausteine von Home Assistant nutzen** (`ha-form`, Selektoren): schneller gebaut,
  sieht „original“ aus, bricht aber bei Änderungen im Frontend. Verworfen zugunsten eigener,
  schlichter Bausteine.
- **Framework mit Bauschritt** (z. B. eine Komponentenbibliothek, gebündelt): bequemer, aber
  Build-Kette, größere Dateien und Abhängigkeiten. Verworfen; die Karten zeigen, dass es ohne
  geht.

## Folgen

- Mehr JavaScript zu pflegen. Abgesichert durch: Websocket-Tests (Integrationstests), eine
  Syntax- und Ladeprüfung der Dateien und Bildschirmfotos der Seite in den Tests (Chromium im
  CI), damit Brüche bei Home-Assistant-Updates früh auffallen.
- Die Logikschicht wird vollständig – auch Dialog und Assistent profitieren davon.
- Keine Migration: Die Seite liest und schreibt die vorhandenen Einstellungen.

## Nachtrag 0.60: Sirenentest auch auf der Seite

- Datum: 2026-11-22

Der Sirenentest war bewusst nur in der Testkarte (Abschnitt 5). Wunsch aus dem Betrieb: alles an
einem Ort. **Entscheidung:** Die Karte „Sirenentest“ im Reiter Alarmgeber bekommt den Test
**zusätzlich** – die Testkarte behält ihn.

- Gleicher Weg wie die Testkarte: die Dienste `hauswacht.siren_test`, `siren_test_result` und
  `siren_test_stop`. Alle Sperren liegen im Hintergrund und gelten unverändert (unscharf,
  Freigabe, Testmodus aus, keine Brandsperre, nur Einbruchtöne, höchstens 10 s, Administratoren).
- Zusätzlich auf der Seite: Häkchen „Ich bin vor Ort, Mitbewohner sind informiert“, dann je
  Sirene eine Rückfrage vor dem Ton; nur für Administratoren sichtbar bedienbar.
- „Die Seite schaltet keine Geräte“ gilt weiter – mit dieser einen Ausnahme. Ein Test
  (`tests/core/test_panel_safety.py`) hält fest, dass die Seite keine anderen Dienste aufruft.

## Nachtrag 0.61: Seite ausblenden statt abschalten, Dialog wird zum Wegweiser

- Datum: 2026-11-23
- Zusammen mit [ADR 0015](0015-rueckkehr.md)

Die Einstellungen werden umfangreicher. Der Dialog kann nur Beschreibungstexte zeigen – kein ⓘ,
keinen Klartext-Satz „So verhält sich das“, keine Warnung am Feld – und jede Einstellung doppelt
zu bauen kostet viel und lässt beide Wege auseinanderlaufen. **Entscheidung:** Die Seite ist der
Hauptweg; der Dialog wird nach und nach zum Wegweiser.

- **Neue Einstellungen nur auf der Seite** (ab „Bei Rückkehr“ in 0.61). Der Dialog zeigt an der
  Stelle einen Hinweis mit Link zur Seite. Was es im Dialog heute gibt, funktioniert vorerst
  weiter.
- **Ausblenden statt abschalten:** „In der Seitenleiste zeigen: ja/nein“ ersetzt das Abschalten
  der Seite. Die Seite gibt es immer (nur Administratoren). Jeder Benutzer kann sie außerdem über
  „Seitenleiste bearbeiten“ in Home Assistant selbst ausblenden.
- **Aufruf ohne Seitenleiste:** über einen Knopf auf der **Geräteseite** von Hauswacht (Link zur
  Gerätekonfiguration – bisher führte er zur Doku auf GitHub, die Doku ist auf der Seite im Reiter
  Dokumentation) und als Erstes im Dialog „Konfigurieren“.
- **Ziel:** Über kurz oder lang bleibt im Dialog nur das Hinzufügen der Integration und der Link
  zur Seite; auch der Einrichtungsassistent zieht auf die Seite. Notfall-Schalter im Dialog
  (z. B. Sirenen-Freigabe aus) nur, wenn sie sich als nötig erweisen – lädt die Seite nicht, ist
  ohnehin etwas grundsätzlich kaputt.
- Ändert Abschnitt 1 („zusätzlich, nicht statt“) und die Abwägung („der Dialog bleibt der sichere
  Weg“): Die Seite wird der Hauptweg, der Dialog schrumpft schrittweise.

## Nachtrag 0.63.2: Der Dialog ist nur noch Wegweiser

Das Ziel aus dem Nachtrag 0.61 ist erreicht: Der Einstellungsdialog und der Einrichtungsassistent
darin sind entfallen.

- **Installation:** ein einziger Schritt mit Hinweis und Link zur Einstellungsseite; die
  Integration wird ohne Einstellungen angelegt.
- **„Konfigurieren“:** zeigt nur noch einen Hinweis mit Link zur Seite und ändert nichts.
- **Begründung:** Die Seite kann alles, was der Dialog konnte (vor dem Entfernen Punkt für Punkt
  geprüft). Zwei Wege bedeuteten doppelte Formulare und doppelte Tests – und die Gefahr, dass beide
  auseinanderlaufen. Die Einstellungsregeln in `core/changes/` waren schon die gemeinsame Logik;
  die Tests dazu bleiben.
- **Kein Notfall-Schalter im Dialog:** Bisher hat sich keiner als nötig erwiesen. Lädt die Seite
  nicht, ist ohnehin etwas grundsätzlich kaputt (siehe oben).
- **Assistent:** Ein neuer Assistent auf der Seite ist geplant (eigenes ADR). Die reinen
  Vorschläge in `core/wizard.py` bleiben dafür erhalten.
