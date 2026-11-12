# ADR 0002: Reiner Kern nach dem Muster „Ereignis rein, Effekte raus“

- Status: angenommen
- Datum: 2026-11-06

## Entscheidung

Zustandsmaschine und Sirenen-Guard sind reine Funktionen ohne Home-Assistant-Importe, ohne
Uhr und ohne Nebenwirkungen. Sie erhalten Ereignisse und die aktuelle Zeit und liefern einen
neuen, unveränderlichen Zustand sowie Effekte. Timer werden über Tokens abgesichert.

## Begründung

- Jeder Zustandsübergang ist deterministisch und ohne Home Assistant testbar.
- Wettlaufsituationen mit Timern werden über Tokens ausgeschlossen.
- Die Sicherheitslogik lässt sich als vollständige Kombinationsmatrix testen.

## Folgen

- Eine Anbindungsschicht muss Effekte ausführen und Timer verwalten.
- Ein statischer Test verhindert HA-Importe im Kern.
