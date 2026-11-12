# ADR 0007: Bereiche

**Status:** angenommen (2026-11-11)

## Kontext

Nicht jede Anlage ist ein einziges Haus: Garage, Gartenhaus oder eine Einliegerwohnung sollen
scharf sein, während im Haus jemand ist – und umgekehrt. Hauswacht soll auch für andere Nutzer
taugen, deshalb sind die Bereiche **frei benannt** und nicht fest vorgegeben.

## Entscheidung

- **Eine Zustandsmaschine je Bereich** (eine Runtime je Bereich). Der erste Bereich (`main`) ist
  die bisherige Anlage und hält die übrigen; seine Entitäts-IDs und sein Speicher bleiben gleich.
  Weitere Bereiche speichern unter eigenem Schlüssel.
- **Alarmprofile gehören zu genau einem Bereich** (`profile.area`, fehlt = erster Bereich).
  Meldergruppen und Auslöseregeln bleiben gemeinsame Bausteine; ein Melder darf in mehreren
  Bereichen vorkommen, ausgewertet wird er von jedem scharfen Bereich.
- **Gemeinsam** für alle Bereiche: Testmodus (nur umschaltbar, wenn alle unscharf), PIN-Sperre
  gegen Durchprobieren, Simulation der Testkarte und die **Sirenen-Belegung**: Eine Sirene geht
  erst aus, wenn kein Bereich sie mehr nutzt. Brandsperre und Sirenen-Guard bleiben unverändert.
- **Nur im ersten Bereich:** immer aktive Melder, Heimkehr-Beobachtung, Erinnerung „Alle weg“.
- **Bedienfeld „Alle Bereiche“** ab zwei Bereichen: arbeitet die Bereiche einzeln ab und meldet
  Teilerfolge, statt alles oder nichts zu schalten – ein offenes Garagenfenster soll das Haus nicht
  ungeschützt lassen.
- **Benutzer** können auf Bereiche beschränkt werden (leer = alle).
- Keine Migration: Fehlt `areas`, gibt es nur den ersten Bereich.

## Alternativen

- **Mehrere Hauswacht-Einträge:** einfach, aber getrennte PINs, Benutzer, Sirenen und kein
  „Alle“; gemeinsame Sirenen könnten sich gegenseitig abschalten.
- **Bereiche als Teil der Profile ohne eigene Zustandsmaschine:** Nur ein Profil kann scharf sein;
  unabhängiges Schalten wäre nicht möglich.

## Folgen

- Mehr Entitäten bei mehreren Bereichen; ohne Bereiche bleibt alles wie bisher.
- Optionen ändern lädt alle Bereiche neu und ist deshalb nur möglich, wenn alle unscharf sind.
