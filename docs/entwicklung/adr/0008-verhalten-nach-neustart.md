# ADR 0008: Verhalten nach Neustart einstellbar

- Status: angenommen
- Datum: 2026-11-16
- Löst ab: [ADR 0004](0004-neustart-unscharf.md)

## Kontext

Bis 0.44 war die Anlage nach jedem Start unscharf (ADR 0004). In der Praxis startet Home
Assistant aber regelmäßig neu – nach Updates oder für nächtliche Sicherungen. Eine Anlage, die
dabei unbemerkt unscharf wird, schützt genau dann nicht, wenn alle schlafen oder weg sind. Die
Nachricht „nach Neustart unscharf“ ist um 3 Uhr nachts keine Hilfe.

## Entscheidung

Einstellung „Verhalten nach Neustart“ mit drei Möglichkeiten:

1. **Vorherigen Zustand wiederherstellen** (Standard): Profil, Zustand und überbrückte Melder
   werden laufend gespeichert und nach dem Start wiederhergestellt – ohne erneute Prüfung und
   ohne Ausgangsverzögerung. Eine laufende Eingangsverzögerung beginnt neu (wer gerade heimkam,
   konnte während des Neustarts nicht unscharf schalten). Ein Alarm wird nie fortgesetzt.
2. **Immer scharf** mit einem festen Profil je Bereich: normal scharf schalten (mit Prüfung),
   eine Minute nachdem Home Assistant hochgefahren ist.
3. **Immer unscharf**: Verhalten von ADR 0004.

**Startphase** nach dem Wiederherstellen (2 Minuten ab „Home Assistant gestartet“): keine
Ausfallmeldungen; Melder, die erstmals offen gemeldet werden, werden bis zum Schließen überbrückt
– außer Eingangstüren, die die Eingangsverzögerung starten. Danach Sammelmeldung.

## Begründung

- Wiederherstellen entspricht dem, was Bewohner erwarten: Ein Neustart ist kein Grund, den Schutz
  aufzugeben.
- Kein Fortsetzen eines Alarms und kein Sirenenstart durch einen Neustart – das war der Kern von
  ADR 0004 und bleibt.
- Offen gemeldete Melder in der Startphase: Hauswacht kann nicht unterscheiden, ob ein Fenster
  vor oder während des Neustarts geöffnet wurde (nach einem Update von 0.44 fehlt zudem die Liste
  der überbrückten Melder). Ein nächtlicher Sirenenalarm wegen eines gekippten Fensters wäre
  schlimmer als eine kurze, gemeldete Überbrückung bis zum Schließen. Eingangstüren bekommen die
  Eingangsverzögerung, damit Heimkehrende unscharf schalten können.
- „Immer scharf“ prüft normal und wartet auf die Funkmelder, weil vorher niemand die Anlage
  bewusst scharf geschaltet hat.

## Bewusst akzeptierte Folgen

- Wer während eines Neustarts ein Fenster öffnet, löst keinen Alarm aus, solange es offen bleibt;
  es wird aber gemeldet, und alle anderen Melder bleiben scharf.
- Nach dem Wiederherstellen werden offene oder ausgefallene Melder nicht erneut geprüft.

## Nachtrag 0.46: Sirenen, die beim Neustart noch liefen

Bis 0.45 merkte sich Hauswacht nur im Arbeitsspeicher, welche Sirenen es eingeschaltet hatte. Nach
einem Neustart mitten im Alarm lief eine Sirene ohne eigene Laufzeit (z. B. ein Relais als
Sirene) weiter, und auch Unscharfschalten schaltete sie nicht mehr aus.

Entscheidung:

- Die eigenen eingeschalteten und noch auszuschaltenden Sirenen werden gespeichert.
- Nach dem Hochfahren schaltet Hauswacht sie aus; nach der Startphase ein zweites Mal, falls eine
  dann noch „an“ meldet (z. B. vorher nicht erreichbar). Sie gelten bis dahin als „noch
  auszuschalten“ – auch Unscharfschalten vergisst sie nicht.
- Es gelten Testmodus-Sperre, Brandsperre (dann jede Minute erneut) und „nur eigene Sirenen“.
  Die Hardware-Freigabe sperrt Ausschalten nicht mehr (Sicherheitsregel S2 angepasst, S15 neu):
  Ausschalten ist die sichere Richtung.
- Sirenen, die inzwischen ein neuer Alarm nutzt, werden nie ausgeschaltet.
