# ADR 0006: Regeln – Abfolgen von Meldern

**Status:** angenommen (2026-11-11)

## Kontext

Ein Melder allein ist nicht immer ein Einbruch: Wer heimkommt, öffnet die Tür und geht nach
oben; wer im Haus ist, löst im Keller zwei Melder aus; wer lüftet, öffnet ein Fenster. Ein
Einbruch zeigt sich oft erst an einer **Abfolge**: Tür, dann Keller; Fenster, dann Bewegung.
Die Zonen-Option „zweiter Melder bestätigt“ (0.18.0) reichte dafür nicht: Zwei Kellermelder
sind auch bei einem Bewohner im Keller fast sicher.

## Entscheidung

- **Regelsammlung** unabhängig von den Profilen. Eine Regel hat bis zu vier Schritte; jeder
  Schritt nennt Melder (Sensoren und/oder Zonen) und ist erfüllt, wenn **einer**, **alle** oder
  **mindestens N verschiedene** davon auslösen. Die Zeit an einem Schritt ist die Zeit bis zum
  nächsten Schritt. Ergebnis: sofort Alarm oder Eingangsverzögerung.
- **Profile** wählen „allein auslösende“ Zonen (bisheriges Verhalten) und Regeln.
- **ODER-Verknüpfung:** Eine Regel kann nur auslösen, nie den Alarm einer anderen verhindern.
  Damit können sich Regeln nicht gegenseitig aushebeln. Bei mehreren Treffern gilt das
  strengere Ergebnis.
- **Ein Regel-Kern** (`core/rules.py`, rein, ohne Home Assistant) für den einfachen Modus
  (Formular, 0.19) und den Expertenmodus (YAML, 0.20). Das Ergebnis geht als normale
  Auslösung in die bestehende Zustandsmaschine (Rolle „sofort“ bzw. „Eingang“) – Brandsperre,
  Testmodus und Sirenen-Guard bleiben unverändert zuständig.
- **Prüfung:** Regeln, die nie auslösen können, lassen sich nicht speichern; Regeln, die in einem
  Profil nichts bewirken, werden als Hinweis gemeldet.
- **Scharfschalten:** Melder, die nur in Regeln vorkommen, blockieren das Scharfschalten nicht.
- Die Zonen-Option aus 0.18.0 entfällt; Migration (Eintragsversion 4) macht daraus eine Regel
  „mindestens 2 verschiedene Melder der Zone“.

## Alternativen

- **Eigene Gruppen quer zu den Zonen:** zweites Zuordnungssystem, weniger mächtig als Abfolgen.
- **Logik in Home-Assistant-Automationen** („Alarm auslösen“-Aktion): maximal frei, widerspricht
  aber dem Grundsatz einer maßgeblichen Zustandsmaschine; Testkarte und Prüfungen wären blind.
  Höchstens später als Notausgang.

## Folgen

- Bewusst in Kauf genommen: Wer keinen späteren Schritt auslöst, bleibt in einem reinen
  Regel-Profil unbemerkt. Die Anleitung weist darauf hin.
- Die Testkarte zeigt den Fortschritt jeder Regel; unvollständige Regeln können gemeldet werden.
