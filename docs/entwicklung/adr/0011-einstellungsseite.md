# ADR 0011: Einstellungsseite in der Seitenleiste – zusätzlich zum Dialog

- Status: vorgeschlagen (Konzept auf dem Zweig `entwicklung/einstellungsseite`)
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
