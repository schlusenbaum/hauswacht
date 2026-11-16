# Installation und erste Schritte

**Deutsch** | [English](en/installation.md)

> **Stand 0.45.3:** Die echte Sirenenansteuerung ist nach der Installation **gesperrt** und
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
| **Alarmgeber – Sirenen** | Sirenen und Freigabe, Sirene aus Schalter erstellen, Ton je Sirene, Sirenentest | [Sirenen](sirenen.md) |
| **Benachrichtigungen** | Empfänger, Ereignisse, eigene Texte, Sprachausgabe | [Benachrichtigungen](benachrichtigungen.md) |
| **Systemeinstellungen** → Bereiche | Haus, Garage … | [Bereiche](profile.md#bereiche) |
| **Systemeinstellungen** → Benutzer und PINs | Personen, Ausweise, Rechte, PIN-Regeln | [Benutzer](benutzer.md) |
| **Systemeinstellungen** → Bedienteile | Keypads, NFC-Aufkleber, RFID-Leser, Taster, Türschlösser | [Bedienteile](bedienteile.md) |
| **Systemeinstellungen** → Funkstille von Sensoren | Wann ein Sensor als ausgefallen gilt | [Melder](melder.md#funkstille-von-sensoren) |
| **Systemeinstellungen** → Funknetz und Gateways überwachen | Zigbee2MQTT, MQTT … | [Melder](melder.md#funknetz-und-gateways-überwachen) |
| **Systemeinstellungen** → Verhalten nach Neustart | Wiederherstellen (Standard), immer scharf, immer unscharf | [unten](#verhalten-nach-einem-neustart) |
| **Systemeinstellungen** → Anwesenheit und Heimkehr-Beobachtung | Signale je Person (für Automatik und Beobachtung); Heimkehr messen | [Profile](profile.md#woran-hauswacht-erkennt-wer-zuhause-ist), [Beobachtungen](beobachtung.md) |

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

**Systemeinstellungen → Verhalten nach Neustart.** Was passiert, wenn Home Assistant neu startet
– etwa nach einem Update, einer nächtlichen Sicherung oder einem Stromausfall – oder Hauswacht
neu geladen wird. Drei Möglichkeiten:

| Einstellung | Was nach dem Neustart passiert | Gedacht für |
|---|---|---|
| **Vorherigen Zustand wiederherstellen** (Standard) | War die Anlage scharf, ist sie es sofort wieder; war sie unscharf, bleibt sie unscharf | fast alle |
| **Immer scharf** (mit festem Profil) | etwa eine Minute nach dem Hochfahren wird das gewählte Profil normal scharf geschaltet | Ferienhaus, unbewohnte Bereiche |
| **Immer unscharf** | immer unscharf; war die Anlage scharf, kommt die Nachricht „nach Neustart unscharf“ | wer lieber selbst entscheidet (Verhalten bis 0.44) |

### Wiederherstellen im Detail

Die Anlage ist **sofort** wieder scharf – mit demselben Profil und denselben überbrückten
Meldern. Sie wird dabei **nicht neu geprüft** und es läuft **keine Ausgangsverzögerung**: Die
Anlage war ja schon scharf. Du bekommst die Nachricht „Hauswacht: nach Neustart wieder scharf“.

Was gerade lief, als Home Assistant neu startete:

| Lief gerade … | Nach dem Neustart |
|---|---|
| nichts (scharf) | scharf |
| die **Ausgangsverzögerung** | scharf – ein Neustart dauert länger als die Verzögerung, wer gehen wollte, ist längst draußen |
| die **Eingangsverzögerung** | die Eingangsverzögerung **beginnt neu**. Wer gerade heimkam, konnte während des Neustarts weder am Keypad noch in der App unscharf schalten – ohne neue Verzögerung gäbe es bei der ersten Bewegung im Flur sofort Alarm |
| ein **Alarm** | **nicht fortgesetzt**: keine Sirenen, die Anlage ist scharf. Die Nachricht nennt, welcher Melder den Alarm ausgelöst hatte |

**Melder beim Hochfahren.** Nach einem Neustart melden sich Funkmelder erst nach und nach – viele
sind kurz „nicht verfügbar“. Deshalb gibt es nach dem Wiederherstellen eine **Startphase von zwei
Minuten** (ab dem Moment, in dem Home Assistant fertig hochgefahren ist):

- **Keine Ausfallmeldungen** in dieser Zeit. Fehlt ein Melder nach der Startphase noch, kommt
  die Meldung „Sensor ausgefallen“.
- **Melder, die geschlossen zurückkommen:** nichts passiert.
- **Melder, die offen zurückkommen:** Hauswacht kann nicht unterscheiden, ob das Fenster schon
  vor dem Neustart offen war oder währenddessen geöffnet wurde. Deshalb:
  - **Eingangstüren** (Typ Tür) starten die **Eingangsverzögerung** – vielleicht kommt gerade
    jemand heim, der dann unscharf schalten kann.
  - **Alle anderen** (Fenster, Bewegung …) werden **bis zum Schließen überbrückt** statt nachts
    einen Sirenenalarm auszulösen. Nach der Startphase kommt die Nachricht „Hauswacht: offen nach
    Neustart“ mit den Namen. Meldet so ein Melder zwischendurch kurz „nicht verfügbar“ und dann
    wieder offen, gibt es trotzdem keinen Alarm. Sobald er schließt, ist er wieder normal
    überwacht.
- **Melder, die schon beim Wiederherstellen offen gemeldet sind** (ihr Gateway war schneller als
  Hauswacht), werden **immer bis zum Schließen überbrückt – auch Eingangstüren**. Eine Tür, die
  schon offen steht, wenn Hauswacht startet, ist eher vergessen als gerade geöffnet; eine
  Eingangsverzögerung würde sonst nachts nach 30 Sekunden die Sirene auslösen.
- Melder, die vor dem Neustart überbrückt waren, bleiben überbrückt.

**Beispiel:** Die Anlage ist nachts auf „Nacht“ scharf, um 3:00 startet Home Assistant für eine
Sicherung neu. Um 3:02 ist Hauswacht wieder scharf, Profil „Nacht“, und schickt „nach Neustart
wieder scharf (Nacht)“. Das gekippte Badfenster war schon vorher überbrückt und bleibt es.

Auch die Profil-Automatik merkt sich, ob sie scharf geschaltet hatte – „Unscharf bei Rückkehr –
wie bisher“ funktioniert nach einem Neustart also weiter.

### Immer scharf

Für jeden Bereich wählst du ein Profil (z. B. „Abwesend“). Etwa **eine Minute** nachdem Home
Assistant hochgefahren ist – damit die Funkmelder wieder melden –, wird es **ganz normal** scharf
geschaltet: mit Prüfung offener und ausgefallener Melder nach den Regeln des Profils und mit
Ausgangsverzögerung. Klappt es nicht (z. B. Fenster offen), kommt die übliche Nachricht „nicht
scharf geschaltet“. Bereiche ohne Profil bleiben unscharf. Im Logbuch steht „Automatik“, die
Nachricht „automatisch scharf (Neustart)“. Sie kommt wie jede Automatik-Nachricht über das
Ereignis **„Automatik“** in den [Benachrichtigungen](benachrichtigungen.md) (Standard: an) – wer
dieses Ereignis ausgeschaltet hat, bekommt sie nicht. „Nicht scharf geschaltet“ kommt über das
Ereignis „Scharfschaltung abgelehnt“ (Standard: an).

> „Immer scharf“ schaltet auch scharf, wenn die Anlage **vor** dem Neustart unscharf war – z. B.
> weil jemand zuhause war. Für ein bewohntes Haus ist deshalb „Wiederherstellen“ die bessere
> Wahl.

### Immer gleich

Unabhängig von der Einstellung gilt:

- Ein früherer **Alarm wird nie fortgesetzt**, Sirenen gehen durch einen Neustart nie an.
- Der **Testmodus** bleibt erhalten, simulierte Sensoren nicht.
- Der Zähler für falsche PIN-Eingaben beginnt bei null.
- Wurde das Profil inzwischen gelöscht, bleibt die Anlage unscharf und meldet das.
- Bei mehreren Bereichen gilt das für jeden Bereich einzeln.

Die [Übersicht](uebersicht.md) zeigt die Einstellung unter „Überwachung“.

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
