# Dokumentation

Hauswacht ist eine Einbruchmeldeanlage als Integration für Home Assistant. Diese Seiten
erklären Einrichtung und Bedienung – von der Installation bis zum Keypad an der Wand.

## Für Anwender

| Seite | Inhalt |
|---|---|
| [Installation und erste Schritte](installation.md) | Voraussetzungen, Installation über Marketplace oder HACS, das Einstellungsmenü, der kürzeste Weg zur ersten Scharfschaltung, Updates |
| [Melder und Meldergruppen](melder.md) | Welche Sensoren gehen, Meldergruppen, Typen (Tür, Fenster, Bewegung …), immer aktive Melder, Funkstille, Funknetz und Gateways |
| [Alarmprofile und Bereiche](profile.md) | Profile anlegen, Verzögerungen, Reaktion, Automatik, Scharf durch Schließen der Tür, mehrere Bereiche (z. B. Haus und Garage) |
| [Auslöseregeln](ausloeseregeln.md) | Abfolgen wie „Tür, dann Keller“, Ausnahmen, Bedingungen, YAML-Expertenmodus |
| [Bedienung und Dashboard](dashboard.md) | Scharf und unscharf schalten, Alarm beenden, Beispielkarte, Karten „Hauswacht Einstellungen“ und „Hauswacht Test“ |
| [Benutzer, PINs und Sperre](benutzer.md) | Benutzer, Rechte je Bereich, PIN-Regeln, Master-PIN, Sperre nach falschen Eingaben, Bedrohungs-PIN |
| [Bedienteile](bedienteile.md) | Zigbee-Keypads, RFID-Karten anlernen, NFC-Aufkleber, RFID-Leser |
| [Sirenen](sirenen.md) | Welche Sirenen gehen, Freigabe, Sirenentest, Brandschutz |
| [Benachrichtigungen und Sprachausgabe](benachrichtigungen.md) | Empfänger je Ereignis, eigene Texte, Ansagen über Lautsprecher, Push-Knöpfe |
| [Testmodus und Testkarte](testmodus.md) | Alles gefahrlos durchspielen: Sensoren simulieren, ohne Sirene |
| [Beobachtungen](beobachtung.md) | Heimkehr-Beobachtung und „Tür auf bis unscharf“ – messen, bevor man automatisiert |
| [Anlagenübersicht](uebersicht.md) | Karte mit der ganzen Konfiguration, Drucken, Notfallblatt, Prüfhinweise, Diagnose-Datei |
| [Referenz](referenz.md) | Alle Entitäten, Attribute, Aktionen und Ereignisse |
| [Fehlersuche](fehlersuche.md) | Häufige Fragen und Probleme |

## Für Entwickler

| Seite | Inhalt |
|---|---|
| [Architektur](entwicklung/architecture.md) | Reiner Kern und Home-Assistant-Schicht |
| [Zustandsmodell](entwicklung/state-model.md) | Zustände, Ereignisse, Übergänge |
| [Sicherheitsregeln](entwicklung/safety.md) | Verbindliche Regeln für Sirenen und Brandalarm |
| [Tests](entwicklung/testing.md) | Teststrategie |
| [Architekturentscheidungen](entwicklung/adr/README.md) | ADRs mit Begründung |
| [Roadmap](roadmap.md) | Was fertig ist, was kommt |
| [Änderungen](../CHANGELOG.md) | Alle Versionen |

## Begriffe

| Begriff | Bedeutung |
|---|---|
| **Melder** | Ein Sensor, den Hauswacht überwacht: Tür- und Fensterkontakt, Bewegungsmelder, Sabotagekontakt, Schloss, Garagentor … |
| **Meldergruppe** | Melder, die zusammengehören und gemeinsam scharf werden (z. B. „Außen“, „Keller“) |
| **Alarmprofil** | Eine Art, scharf zu schalten (z. B. „Nacht“): welche Meldergruppen, welche Verzögerungen, welche Sirenen |
| **Auslöseregel** | Alarm erst bei einer Abfolge von Meldern („Tür, dann Keller“) |
| **Bereich** | Ein unabhängig scharf schaltbarer Teil der Anlage (z. B. Garage) |
| **Bedienfeld** | Die Alarm-Entität in Home Assistant (`alarm_control_panel.hauswacht`) |
| **Bedienteil** | Ein Gerät zum Bedienen: Keypad, NFC-Aufkleber, RFID-Leser |
| **Ausweis** | PIN oder RFID-Karte eines Benutzers |
| **Überbrückt** | Ein Melder wird vorübergehend nicht überwacht (z. B. offenes Fenster nach „Trotzdem scharf“) |
