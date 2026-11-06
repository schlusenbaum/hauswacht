# ADR 0004: Nach Neustart immer unscharf

- Status: angenommen
- Datum: 2026-11-06

## Entscheidung

Nach jedem Start von Home Assistant bzw. der Integration ist die Anlage unscharf. Ein früherer
Alarm wird nie wieder aufgenommen. War die Anlage vorher scharf, wird eine Benachrichtigung
ausgelöst. Der Testmodus bleibt dagegen erhalten.

## Begründung

Ein unkontrolliertes Wiederaufnehmen kann nach Wartungsarbeiten oder Updates zu Fehlalarmen
führen. Der Testmodus ist die sicherere Einstellung und darf deshalb erhalten bleiben.

## Bewusst akzeptierte Folge

Ein Stromausfall oder Absturz während einer Abwesenheit hinterlässt ein unscharfes Haus. Die
Benachrichtigung „Anlage nach Neustart unscharf – vorher: <Profil>“ macht das sichtbar.
