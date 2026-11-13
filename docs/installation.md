# Installation und erste Schritte

> **Stand 0.40.0:** Die echte Sirenenansteuerung ist nach der Installation **gesperrt** und
> muss bewusst freigegeben werden – bis dahin kann Hauswacht keinen Ton auslösen.

## Voraussetzungen

- Home Assistant **2026.10** oder neuer
- Marketplace (ab Home Assistant 2026.11), [HACS](https://hacs.xyz) (bis 2026.10) oder manuelle
  Installation
- Sensoren mit „offen/zu“ in Home Assistant (Tür-, Fenster-, Bewegungsmelder …)
- Optional: Sirenen (`siren.…`), die Home-Assistant-App für Push-Nachrichten, Zigbee2MQTT für
  Keypads

Hauswacht braucht keine Cloud und keine weiteren Integrationen.

## Installation

Hauswacht steht (noch) nicht im Katalog von Marketplace bzw. HACS. Das Repository wird deshalb
einmal über seinen Link eingebunden; danach kommen Updates wie gewohnt.

**Marketplace** (Home Assistant 2026.11 und neuer):

1. Einstellungen → **Marketplace**. Beim ersten Mal den Hinweis zu Community-Projekten lesen und
   bestätigen.
2. Hinzufügen per Link (*Add from link*) → `https://github.com/schlusenbaum/hauswacht`. Dafür
   muss im Marketplace ein GitHub-Konto verbunden sein – Home Assistant fragt beim ersten Mal
   danach.
3. Hauswacht öffnen → **Herunterladen**.
4. Home Assistant neu starten.

**HACS** (bis Home Assistant 2026.10):

1. HACS → Menü (⋮) → **Benutzerdefinierte Repositories** →
   `https://github.com/schlusenbaum/hauswacht`, Typ **Integration** → Hinzufügen.
2. Hauswacht suchen → **Herunterladen**.
3. Home Assistant neu starten.

Wer von HACS kommt: Beim Wechsel auf 2026.11 übernimmt der Marketplace die installierten
Repositories, Hauswacht muss nicht neu eingebunden werden.

Installiert wird die Datei `hauswacht.zip` aus dem jeweiligen
[Release](https://github.com/schlusenbaum/hauswacht/releases). Neue Versionen erscheinen als
Update.

**Manuell:** `hauswacht.zip` aus dem neuesten
[Release](https://github.com/schlusenbaum/hauswacht/releases) nach
`/config/custom_components/hauswacht` entpacken und Home Assistant neu starten.

**Einrichten:** Der Knopf öffnet die eigene Home-Assistant-Instanz direkt beim Einrichten von
Hauswacht (beim ersten Mal fragt [My Home Assistant](https://my.home-assistant.io) einmal nach
deren Adresse):

[![Hauswacht einrichten](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=hauswacht)

Oder von Hand: Einstellungen → Geräte & Dienste → **Integration hinzufügen → Hauswacht**.
Hauswacht lässt sich nur einmal einrichten; mehrere Anlagenteile werden über
[Bereiche](profile.md#bereiche) abgebildet.

## Das Einstellungsmenü

Alle Einstellungen liegen unter **Einstellungen → Geräte & Dienste → Hauswacht →
Konfigurieren**. Sie lassen sich nur ändern, wenn **alle Bereiche unscharf** sind.

| Menü | Inhalt | Seite |
|---|---|---|
| **Alarmauslösung** → Meldergruppen | Melder zusammenfassen und ihren Typ festlegen | [Melder](melder.md) |
| **Alarmauslösung** → Auslöseregeln | Abfolgen von Meldern („Tür, dann Keller“) | [Auslöseregeln](ausloeseregeln.md) |
| **Alarmauslösung** → Immer aktiv | Melder, die auch unscharf melden | [Melder](melder.md#immer-aktive-melder) |
| **Alarmauslösung** → Melder aus anderem Sensor erstellen | Assistent: Messwert → Schwellenwert-Helfer → Melder | [Melder](melder.md#melder-aus-anderem-sensor-erstellen) |
| **Alarmprofile** | Profile anlegen und bearbeiten | [Profile](profile.md) |
| **Alarmgeber – Sirenen** | Sirenen, Freigabe, Sirenentest | [Sirenen](sirenen.md) |
| **Benachrichtigungen** | Empfänger, Ereignisse, eigene Texte, Sprachausgabe | [Benachrichtigungen](benachrichtigungen.md) |
| **Systemeinstellungen** → Bereiche | Haus, Garage … | [Bereiche](profile.md#bereiche) |
| **Systemeinstellungen** → Benutzer und PINs | Personen, Ausweise, Rechte, PIN-Regeln | [Benutzer](benutzer.md) |
| **Systemeinstellungen** → Bedienteile | Keypads, NFC-Aufkleber, RFID-Leser | [Bedienteile](bedienteile.md) |
| **Systemeinstellungen** → Funkstille von Sensoren | Wann ein Sensor als ausgefallen gilt | [Melder](melder.md#funkstille-von-sensoren) |
| **Systemeinstellungen** → Funknetz und Gateways überwachen | Zigbee2MQTT, MQTT … | [Melder](melder.md#funknetz-und-gateways-überwachen) |
| **Systemeinstellungen** → Heimkehr-Beobachtung | Messen, schaltet nichts | [Beobachtungen](beobachtung.md) |

So funktioniert der Dialog:

- Jede Änderung wird beim Bestätigen eines Formulars **sofort gespeichert** („✅ Gespeichert“).
- Untermenüs haben **„← Zurück“**, das Hauptmenü **„Fertig – schließen“**.
- Formulare haben in Home Assistant keinen Zurück-Knopf: unverändert bestätigen oder den Dialog
  schließen – bereits Gespeichertes bleibt.
- Wird die Anlage scharf geschaltet, während der Dialog offen ist, speichert Hauswacht nichts
  mehr.

## In fünf Schritten zur ersten Scharfschaltung

1. **Meldergruppe anlegen:** Alarmauslösung → Meldergruppen → Meldergruppe anlegen, z. B.
   „Außen“ mit allen Tür- und Fensterkontakten. Danach die vorgeschlagenen
   [Typen](melder.md#typen) prüfen – meist passen sie.
2. **Alarmprofil anlegen:** Alarmprofile → Alarmprofil anlegen, z. B. „Nacht“ mit Knopf
   „Nacht“, Meldergruppe „Außen“. Verzögerungen erst einmal lassen. Sirenen: noch keine oder
   „Stiller Alarm“.
3. **Benachrichtigung:** Benachrichtigungen → Empfänger und Ereignisse → das eigene Handy
   (`mobile_app_…`) als allgemeinen Empfänger wählen.
4. **Ausprobieren im Testmodus:** Karte [„Hauswacht Test“](testmodus.md#karte-hauswacht-test)
   aufs Dashboard, Testmodus an, „Nacht“ scharf schalten, eine Tür simulieren. Es ertönt keine
   Sirene, andere Automationen merken nichts.
5. **Echt:** Testmodus aus, scharf schalten. Sirenen erst freigeben, wenn alles passt – siehe
   [Sirenen](sirenen.md).

Danach nach Bedarf: [Benutzer und PINs](benutzer.md), [Bedienteile](bedienteile.md),
[Auslöseregeln](ausloeseregeln.md), [Bereiche](profile.md#bereiche).

## Was Hauswacht anlegt

Ein Gerät **„Hauswacht“** mit Bedienfeld, Profilauswahl, Knöpfen, Testmodus, Systemstatus und
Profil-Einstellungen; je weiterem Bereich ein Gerät „Hauswacht <Bereich>“. Die vollständige
Liste steht in der [Referenz](referenz.md#entitäten). Auf der Geräteseite führt ein Link zu
dieser Anleitung.

## Verhalten nach einem Neustart

Hauswacht startet **immer unscharf**. War die Anlage vorher scharf, kommt die Meldung
„Hauswacht: nach Neustart unscharf“. Ein früherer Alarm wird nie unkontrolliert wieder
aufgenommen. Der Testmodus bleibt erhalten, simulierte Sensoren nicht. Der Zähler für falsche
PIN-Eingaben beginnt bei null.

## Updates

- Updates kommen über den Marketplace bzw. HACS. Danach Home Assistant neu starten.
- Die eigenen Karten werden automatisch neu geladen; zeigt eine Karte noch die alte Version,
  die Seite neu laden (in der App: Einstellungen → Companion App → Frontend-Cache
  zurücksetzen).
- Einstellungen aus älteren Versionen werden beim Start automatisch übernommen. Was sich
  geändert hat, steht im [CHANGELOG](../CHANGELOG.md).

Besondere Hinweise für sehr alte Versionen:

- **Von 0.7.x auf 0.8.0:** Die fünf festen Profile wurden zu normalen Profilen mit gleichem
  Namen, Knopf und allen Einstellungen.
- **Von 0.2.0:** Zuerst Meldergruppen anlegen und den Profilen zuordnen, sonst verweigert
  Hauswacht das Scharfschalten.

## Entfernen

Einstellungen → Geräte & Dienste → Hauswacht → ⋮ → **Löschen**, danach im Marketplace bzw. in HACS entfernen.
Hauswacht hat nichts an Geräten, Automationen oder Skripten verändert; es bleibt nichts zurück
außer eventuell selbst angelegten Schwellenwert-Helfern (unter Helfer).
