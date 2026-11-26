# ADR 0020: Debug-Log

- Status: angenommen (0.65.0b9)
- Anlass: Die Datei aus „Konfiguration herunterladen“ (ADR 0019) ist eine Momentaufnahme. Sie
  beantwortet nicht, *was vorhin passiert ist*, zum Beispiel warum gestern Abend nicht scharf
  geschaltet wurde. Hauswacht hatte bis dahin keine einzige Debug-Zeile. „Debug-Protokollierung
  aktivieren“ in Home Assistant brachte also nichts.

## Verworfen: Entscheidungsprotokoll im Export

Ein eingebauter Verlauf (Ringpuffer), der mit „Konfiguration herunterladen“ mitkommt, wurde
verworfen. Ein Verlauf mit Uhrzeiten ist ein **Bewegungsprofil**: Wann ging wer aus dem Haus, wann
war das Haus leer. Hauswacht soll keinen eingebauten Weg anbieten, so etwas weiterzugeben, auch
nicht mit Platzhaltern. Auch Hauswachts Warnungen und Fehler aus dem HA-Log kommen nicht in den
Export: Das ist Freitext mit Uhrzeiten, den die Platzhalter nicht sicher erfassen.

## Entscheidung

1. **Debug-Zeilen über das normale Logging von Home Assistant.** Sie sind standardmäßig aus und
   erscheinen nur, wenn man in HA „Debug-Protokollierung aktivieren“ einschaltet. Sie bleiben
   lokal; Hauswacht verschickt nichts.
2. **Eine Zeile je Entscheidung**, nach dem Muster Eingang → Entscheidung mit Grund → Aktion
   und Ergebnis:
   - jeder Melderwechsel mit Rolle und Grund (überwacht, überbrückt, unscharf, nicht im Profil);
   - Zustandsmaschine: Ereignis → Wirkungen;
   - Anwesenheit je Person bei einer Änderung, mit Grund;
   - Aktionen der Automatik und übersprungene Schritte;
   - Sirenenentscheidungen (gesendet und gesperrt);
   - Benachrichtigungen (Ereignis und Empfänger-IDs);
   - Eingaben an Bedienteilen (Taste, Ausweis ja/nein, Ergebnis).
3. **Kurz und ohne Geheimnisse.** `core/debug_log.py` (`describe`) beschreibt Datenklassen und
   Wörterbücher. Felder aus `SECRET_FIELDS` lässt es immer weg: Namen, Codes, Karten, Orte,
   WLAN, Titel und Texte. Zeitpunkte erscheinen als Uhrzeit, lange Listen werden gekürzt.
   Aufwendige Zeilen werden nur gebaut, wenn Debug an ist (`isEnabledFor`).
4. **Statischer Test für alle Log-Zeilen**, auch Info und Warnung: Kein `_LOGGER`-Aufruf darf
   `code`, `pin`, `tag`, `card`, `latitude`, `longitude`, `ssid`, `title`, `message`, `text`,
   `by`, `identity` … ausgeben. Erlaubt ist nur die Frage „gibt es einen?“ als Bedingung
   (`"mit Ausweis" if code else ""`). Außerdem muss der Text jeder Log-Zeile fest im Code
   stehen; eine fertige Nachricht als Text ist verboten. Dabei fielen vier bestehende Zeilen
   auf, die einen Benutzernamen ins Log schrieben: Falscheingaben zurückgesetzt, Durchgang rein
   und raus, und „Alarm beendet von …“, die den ganzen Nachrichtentext loggte. Sie nennen keinen
   Namen mehr; wer es war, steht weiter im Logbuch.

## Folgen

- Fehler lassen sich einer von vier Ebenen zuordnen: Melder, Deutung, Ausführung, Home Assistant.
- Entitäts-IDs bleiben im Log, sie enthalten oft Namen. Die Doku sagt deutlich, was man vor dem
  Teilen ersetzen sollte und dass ein Log ein zeitlicher Ablauf ist.
- Neue Log-Zeilen fallen unter denselben Test. Neue Felder mit Namen oder Geheimnissen gehören
  in `SECRET_FIELDS`.
