# ADR 0017: Assistent auf der Einstellungsseite – Check-up, Szenarien, Einrichten nach Zielen

- Status: umgesetzt (0.64: Check-up, Hinweise in den Seitenblättern, Szenario-Vorschau; 0.65: Einrichten nach Zielen)
- Datum: 2026-11-25
- Baut auf: [ADR 0009](0009-einrichtungsassistent.md) (gemeinsame Logikschicht),
  [ADR 0011](0011-einstellungsseite.md) (Einstellungsseite, Nachtrag 0.63.2),
  [ADR 0015](0015-rueckkehr.md) (Bei Rückkehr, „weg“ nur mit Beleg),
  [ADR 0014](0014-ausgangserkennung.md) (Ausgangserkennung)

## Kontext

Hauswacht ist mächtig geworden: Profile mit Automatik, Anwesenheit aus mehreren Signalen, „weg“ nur
mit Beleg, Bei Rückkehr, Annäherung, Durchgang, Messungen. Jede Einstellung ist erklärt (ⓘ, „So
verhält sich das“), und die Doku-Seite [So entscheidet Hauswacht](../../so-entscheidet-hauswacht.md)
zeigt die Abläufe als Bilder. Trotzdem verliert man den Überblick, **wie die Einstellungen
zusammenspielen** – und ob eine Einstellung eine andere unbemerkt aushebelt.

Typische Fallen, die heute erst im Alltag auffallen:

- Eine Person ohne Ortung steht in „Scharf, wenn alle weg“ – das Profil wird **nie** scharf.
- Die Eingangsverzögerung ist kürzer als die gemessene Zeit von der Tür bis zum Keypad.
- „Annäherung verlängert die Eingangsverzögerung“ ist eingestellt, aber niemand hat einen
  Richtungssensor.
- „Bei Rückkehr: Unscharf mit Türbeleg“, aber das Handy der Person meldet laut Messung erst nach
  der Eingangsverzögerung „zuhause“.

Der alte Assistent (0.53 bis 0.63.1, im Dialog) kannte nur Melder, Gruppen und Profile. Er ist mit
0.63.2 entfallen.

## Entscheidung

### 1. Eigener Reiter „Assistent“ mit zwei Wegen

Die Einstellungsseite bekommt den Reiter **Assistent** (vor „Dokumentation“). Oben zwei Wege:

- **Check-up** – „Wie gut ist meine Anlage eingestellt?“ Für bestehende Anlagen. **Kommt zuerst.**
- **Einrichten** – „Was soll Hauswacht für euch tun?“ Für neue Anlagen und neue Wünsche.

Beide zeigen am Ende dieselbe **Szenario-Vorschau** (Abschnitt 4).

### 2. Eine gemeinsame Prüfung – überall

Neu im Kern: `core/advisor.py` (rein, ohne Home Assistant). Eingabe: die Einstellungen, der
Zustand der Personen-Signale (welche Signalart je Person: Ortung, WLAN, Ping, Bluetooth, Richtung)
und die Messungen der Beobachtung. Ausgabe: **Befunde**:

| Feld | Inhalt |
|---|---|
| `code`, `key` | was und wo (wie bei den Prüfhinweisen) |
| `level` | **Fehler** (wirkt nicht wie gedacht, z. B. „wird nie scharf“), **Warnung** (unsicher oder knapp), **Tipp** (geht besser) |
| `text` | ein Satz in einfacher Sprache, mit Namen aus dem eigenen Haus |
| `why` | warum – mit Messwert, wenn es einen gibt („gemessen: bis 38 s, eingestellt: 30 s“) |
| `fix` | optional: ein **Vorschlag** als fertige Änderung (über `core/changes`), z. B. „Eingangsverzögerung auf 50 s“ |
| `weakens` | `true`, wenn der Vorschlag die Sicherheit verringert (z. B. „Tür + Signal“ erlauben, längere Verzögerung) |

Genutzt an drei Stellen – **eine Regel, eine Stelle**:

1. **Check-up** (Reiter Assistent): alle Befunde, sortiert nach Fehler → Warnung → Tipp.
2. **Seitenblätter**: Vor dem Speichern prüft die Seite die geplante Änderung und zeigt neue
   Befunde direkt am Feld („Niklas hat keine Ortung – mit ihm in der Liste wird ‚Nacht‘ nie
   automatisch scharf.“). Speichern bleibt möglich – es ist ein Hinweis, kein Verbot.
3. **Prüfhinweise** (Übersicht, Reparaturen): Die bestehenden Prüfhinweise (`core/checks.py`)
   bleiben; Befunde der Stufe „Fehler“ erscheinen zusätzlich dort.

Messwerte zählen nur, wenn die Messung genug Daten hat (wie bei den Empfehlungen heute); sonst steht
„noch zu wenig gemessen“ statt einer Zahl.

### 3. Check-up: Befund für Befund, nie automatisch

- Jeder Befund mit Vorschlag hat **„Ansehen“**: Was sich ändert (vorher → nachher) und die
  Szenarien, die sich dadurch ändern. Dann **„Übernehmen“** – einzeln, nie alles auf einmal.
- Vorschläge mit `weakens` brauchen eine **ausdrückliche Bestätigung** mit dem Satz, was schwächer
  wird („Ein Einbrecher hätte dann 50 statt 30 Sekunden.“).
- Gespeichert wird über `core/changes` wie überall – nur unscharf, mit Revision.
- „Später“ blendet einen Befund aus, bis sich die Einstellungen oder Messwerte ändern.

### 4. Szenario-Vorschau: „Was passiert, wenn …?“

Neu im Kern: `core/scenarios.py`. Ein **Szenario** ist eine kurze Abfolge von Ereignissen mit
Zeiten, z. B.:

> 23:00 Petra nähert sich · 23:04 Haustür auf · 23:04:20 Petras Handy „zuhause“

Die Simulation spielt das gegen die **aktuellen** (oder die vorgeschlagenen) Einstellungen durch
und liefert den Ablauf als Sätze mit Ergebnis:

> ✅ Eingangsverzögerung 90 s (Annäherung) → 23:04:20 Heimkehr + Tür → unscharf, kein Alarm

**Dieselbe Logik wie im Echtbetrieb.** Die Simulation darf keine zweite Kopie der Regeln sein,
sonst zeigt sie etwas anderes, als die Anlage tut. Deshalb wird vorher die Entscheidungslogik, die
heute noch in `automation_runner.py` steckt (alle weg, Bei Rückkehr, Türbeleg, Annäherung), als
reine Funktionen in den Kern verschoben; Laufzeit und Simulation rufen dieselben Funktionen auf.
Die Zustandsmaschine liegt schon im Kern.

**Standard-Szenarien**, aus den Einstellungen und Messwerten erzeugt (nicht von Hand
geschrieben):

| Szenario | Erwartung |
|---|---|
| Einbruch nachts durch jede Eingangstür, niemand kommt heim | Alarm nach der Eingangsverzögerung |
| Einbruch durch ein Fenster / einen Melder mit Sofortalarm | sofort Alarm |
| Jede Person kommt heim (mit ihrer **gemessenen** längsten Zeit Tür → zuhause) | je nach „Bei Rückkehr“: unscharf ohne Alarm |
| Alle gehen nacheinander (gemessene Zeit bis „weg mit Beleg“) | Profil mit Automatik wird scharf |
| Handy schläft (Signal schweigt ohne Tür) | niemand gilt als weg, nichts passiert |
| WLAN fällt aus (alle WLAN-Signale gleichzeitig weg) | niemand gilt als weg |

Jede Zeile zeigt ✅ (wie erwartet), ⚠️ (knapp, z. B. weniger als 10 s Reserve) oder ❌ (anders als
erwartet, z. B. „Petra: Alarm nach 30 s – ihr Handy braucht bis 38 s“). Ein ❌ ist zugleich ein
Befund der Prüfung (Abschnitt 2).

Die Standard-Szenarien werden außerdem die **Sicherheitstabelle** für die Ausgangserkennung
(ADR 0014): Jede Änderung muss alle „Rein“-Szenarien unverändert lassen – geprüft als automatische
Tests.

### 5. Einrichten nach Zielen (nach dem Check-up)

Fragen in dieser Reihenfolge, jede überspringbar:

1. **Haushalt:** Personen aus Home Assistant, je Person die gefundenen Signale (Ortung, WLAN, Ping,
   Bluetooth, Richtung) mit Einordnung („sicherer Beleg für weg“ / „nur zuhause“).
2. **Türen und Fenster:** Vorschläge nach Etage und Raum (`core/wizard.py` bleibt dafür).
3. **Ziele** (mehrere möglich): nachts absichern · automatisch scharf, wenn alle weg sind · beim
   Heimkommen unscharf · nachts heimkommen, ohne dass „Nacht“ aus ist · Garage oder Werkstatt
   getrennt.
4. **Rückfragen je Ziel**, z. B. bei „beim Heimkommen unscharf“: wer, und wie sicher (Türbeleg
   empfohlen).

Daraus entsteht ein **Plan** (Liste von Änderungen). Vorschau mit Szenarien wie in Abschnitt 4,
dann **„Übernehmen“**. Vorhandenes wird nur **ergänzt**; was überschrieben würde, steht in der
Vorschau und braucht eine Bestätigung.

Erster Umfang: Melder und Meldergruppen, Profile, Anwesenheit mit Automatik und Bei Rückkehr,
Empfänger, Sirenen (eintragen – **nie freigeben**). Später: Bedienteile, Karten, Auslöseregeln,
Bereiche.

### 6. Was der Assistent nie tut

- Er **schaltet nichts** – keine Sirene, kein Scharf/Unscharf, kein Gerät.
- Er **gibt Sirenen nie frei**; die Freigabe bleibt ein eigener, bewusster Schritt.
- Er ändert **nichts ohne „Übernehmen“**, und nur, wenn alle Bereiche unscharf sind.
- Er fasst **Rauchmelder und Brandalarm** nicht an. *Nachtrag 0.65.0b2:* Sirenen von
  Rauchmeldern bietet er beim Einrichten an (deutlich gekennzeichnet), trägt sie aber nur als
  Einbruchsirene ein – nur Einbruchton, bei Brand gesperrt; die Brandfunktion bleibt unverändert.
  In manchen Häusern sind die Rauchmelder die einzigen Sirenen.
- Er legt keine Helfer, Automationen oder Skripte an.

### 7. Reihenfolge

| Version | Inhalt |
|---|---|
| 0.64 | Entscheidungslogik in den Kern verschieben (ohne Verhaltensänderung, abgesichert durch die bestehenden Tests), gemeinsame Prüfung, Hinweise in den Seitenblättern, Reiter „Assistent“ mit Check-up und Szenario-Vorschau |
| 0.65 | Einrichten nach Zielen |
| 0.66 | Ausgangserkennung (ADR 0014) – mit den Szenarien als Sicherheitstabelle |

## Abwägung

- **Nur bessere Prüfhinweise, kein Assistent:** zu wenig – Hinweise sagen, *dass* etwas nicht
  passt, aber nicht, *was passieren würde*. Die Szenarien machen das Zusammenspiel sichtbar.
- **Szenarien später:** verworfen. Gerade sie geben den Überblick, der fehlt, und sie sind die
  Grundlage, um bei der Ausgangserkennung nichts auszuhebeln.
- **Eigene Regeln in der Simulation:** verworfen – zwei Kopien laufen auseinander. Deshalb zuerst
  die Logik in den Kern.
- **Vorschläge automatisch übernehmen:** verworfen. Jede Änderung einzeln, mit Vorschau;
  Schwächungen nur mit ausdrücklicher Bestätigung.
- **Knopf statt Reiter:** Ein Reiter ist immer sichtbar und lädt zum regelmäßigen Check-up ein;
  ein überlagerndes Fenster wäre auf dem Handy eng.

## Folgen

- Der Umzug der Entscheidungslogik in den Kern ist der riskanteste Teil. Er kommt **zuerst und
  allein** (eigene Vorabversion ohne neue Funktionen), damit ein Fehler dort nicht im Neuen
  untergeht.
- Die Seitenblätter fragen vor dem Speichern die Prüfung ab – eine Websocket-Anfrage mehr je
  Speichern.
- Die Ausgangserkennung rückt auf 0.66.
