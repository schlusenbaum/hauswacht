# ADR 0019: Konfiguration herunterladen (Fehlersuche)

- Status: angenommen (0.65.0b8)
- Anlass: Fehlersuche bei einem Tester (simon42-Forum). Seine Geofence-Tracker hatten keine
  Koordinaten, also hatte Hauswacht für ihn nie einen Beleg für „weg“. Um das herauszufinden,
  brauchte es viele Rückfragen. Die Diagnose-Datei von Home Assistant half nicht: Sie entfernt
  Personen ganz, also sah man nicht, welcher Tracker zu wem gehört.

## Ausgangslage

Die Diagnose-Datei (seit 0.34, `diagnostics.py`) enthält die Einstellungen und die Übersicht.
Personen, Empfänger, Karten usw. werden darin **entfernt** (`async_redact_data` →
`**REDACTED**`). Für Fehlerberichte über Anwesenheit fehlt damit genau das Wichtigste:
- wer welche Ortung und welche Signale hat;
- was Hauswacht gerade über jede Person denkt;
- welche Fakten aus Home Assistant kommen: Ortung, Richtung, eingefrorene Ortungen.

## Entscheidung

1. **Eigener Knopf** „Konfiguration herunterladen“ im Reiter System der Einstellungsseite. Die
   Diagnose-Datei bleibt, wie sie ist.
2. **Inhalt** (Websocket `hauswacht/export`, nur Administratoren, nur lesen):
   - Versionen, alle Einstellungen, Übersicht;
   - „Wer gilt gerade als zuhause?“ (`presence_overview`);
   - Fakten (`build_facts`), Messungen, Check-up, Szenarien;
   - Zustand der eigenen Entitäten und aller Entitäten, die in den Einstellungen vorkommen,
     samt den Trackern der Personen.
   Von fremden Entitäten nur ausgewählte Attribute: `device_class`, `source_type`, `in_zones`,
   `gps_accuracy`, Einheit, Name, `device_trackers`. Koordinaten nie, nur `has_coordinates`.
   Ein Abschnitt, der scheitert, steht als Fehler in der Datei, statt die ganze Datei zu
   verhindern.
3. **Platzhalter statt Entfernen** (reiner Kern `core/export.py`). Gleichbleibende Zuordnung:
   - Personen werden zu `person.person_1` und „Person 1“, auch innerhalb von Entitäts-IDs und
     Sätzen. Ersetzt werden ganze Wörter (Unterstrich zählt als Grenze, angehängtes „s“ erlaubt).
   - Benutzer werden zu `benutzer_1`. Gleicher Name heißt gleicher Benutzer, auch zwischen
     Einstellungen und Übersicht.
   - Aus Karten, Empfängern, Lautsprechern, WLAN-Namen, MQTT-Topics, Geräte-IDs und HA-Konten
     werden `karte_1`, `notify.empfaenger_1` usw. Bei Entitäts-IDs bleibt die Domäne.
   - PIN-Hashes, Salze und Aktions-Codes werden zu `***`. Wahrheitswerte wie „PIN vorhanden“
     bleiben.
4. **Keine ungeschwärzte Fassung.** So eine Datei landet zu leicht versehentlich im Forum.

## Folgen

- Fehlerberichte zur Anwesenheit lassen sich aus einer Datei nachvollziehen.
- Namen von Meldern, Zonen, Bereichen und Profilen bleiben, weil man sie zum Verstehen braucht.
  Was darin persönlich ist, aber kein Personenname in Home Assistant, bleibt stehen. Die Doku
  und die Karte bitten darum, vor dem Weitergeben drüberzuschauen.
- Neue Einstellungen mit Geheimnissen müssen in `SECRET_KEYS` oder `CATEGORY_KEYS` von
  `core/export.py` eingetragen werden. Tests prüfen mit Beispieldaten, dass kein echter Wert in
  der Datei steht.
