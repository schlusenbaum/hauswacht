# Benutzer, PINs und Sperre

## Das Wichtigste vorab

> ⚠️ **Entweder alle bekommen einen PIN – oder keiner.**
> Sobald **ein** PIN existiert (auch der Master-PIN), verlangen das Bedienfeld und Alexa zum
> Unscharfschalten einen PIN – **von allen**. Wer keinen hat, kann dann nur noch über
> Dashboard-Knöpfe (wenn unter PIN-Regeln „Dashboard-Knöpfe trotz PIN erlauben“ an ist), den
> Push-Knopf oder seine RFID-Karte unscharf schalten. Ein gemeinsamer Familien-PIN ist erlaubt.
> Fehlt jemandem ein PIN, zeigt Home Assistant unter **Einstellungen → Reparaturen** den Hinweis
> „Nicht alle Personen haben einen PIN“.

**RFID-Karten sind unabhängig vom PIN:** Karten machen das Bedienfeld nicht PIN-pflichtig. Ganz
ohne PINs schalten also alle im Dashboard ohne PIN, und mit Karte trotzdem am Keypad.

| Ziel | So einrichten |
|---|---|
| Dashboard ohne PIN, Keypad mit Karte | keine PINs, Karten bei den Benutzern |
| Keypad auch mit Zahlencode, Dashboard trotzdem ohne PIN | PINs bzw. Master-PIN, im Dashboard die Karte [„Hauswacht Alarm“](dashboard.md#karte-hauswacht-alarm) – sie schaltet für zugeordnete Konten ohne PIN |
| … und ein Wandtablet nur mit PIN | dem Tablet ein eigenes Home-Assistant-Konto ohne Hauswacht-Benutzer geben (oder beim Benutzer „In der Alarmkarte PIN verlangen“) |
| Alles mit PIN | PIN für jede Person (gemeinsam erlaubt) |

## Benutzer

**Systemeinstellungen → Benutzer und PINs.** Jede Person bekommt einen Benutzer:

| Feld | Bedeutung |
|---|---|
| Name | Vorschläge aus den Home-Assistant-Benutzern oder frei (z. B. „Putzhilfe“). Erscheint als „geändert von“ am Bedienfeld, im Logbuch und in Push-Nachrichten |
| PIN | 4–8 Ziffern, nur als Hash gespeichert. Optional |
| Bedrohungs-PIN | siehe [unten](#bedrohungs-pin) |
| Aktiv | aus = Ausweise gesperrt, ohne sie zu löschen |
| Darf scharf schalten / unscharf schalten / Alarm beenden | Rechte (bei „alle Bereiche gleich“) |
| Rechte gelten für | nur bei mehreren Bereichen, siehe [Rechte](#rechte) |
| Home-Assistant-Konto | ordnet Push-Knopf, Dashboard-Knöpfe und NFC-Aufkleber diesem Benutzer zu. Wird automatisch gesetzt, wenn als Name ein Home-Assistant-Benutzer gewählt wurde |
| In der Alarmkarte PIN verlangen | für das Home-Assistant-Konto dieses Benutzers in der Karte [„Hauswacht Alarm“](dashboard.md#ohne-pin-zwang), z. B. bei einem Tablet-Konto. Standard aus |
| Gültig von / bis | für Gäste: außerhalb dieser Zeit sind die Ausweise gesperrt |
| RFID-Karten/-Anhänger | beliebig viele, siehe [Bedienteile → Karten anlernen](bedienteile.md#karten-anlernen) |

- **Gemeinsamer PIN:** Mehrere Benutzer dürfen denselben PIN haben („gemeinsamer PIN (Christian,
  Petra)“, bei englischer Sprache „shared PIN (…)“). Eine Aktion ist erlaubt, wenn **mindestens einer** dieser Benutzer sie darf.
- **Gesperrter oder abgelaufener Ausweis:** wird abgelehnt wie ein falscher; zusätzlich geht
  eine Systemmeldung „gesperrter Ausweis“ raus.
- **Ohne PIN** (Push-Knopf, Dashboard-Knöpfe, NFC-Aufkleber): Ist das Home-Assistant-Konto einem
  Benutzer zugeordnet, gelten dessen Name und Rechte; sonst erscheint der Name des Kontos und
  alles ist erlaubt (NFC-Aufkleber verlangen immer einen zugeordneten Benutzer).
- Automatik (Uhrzeit, Anwesenheit) erscheint als „Automatik“.

## Rechte

Ohne weitere Bereiche gelten die drei Häkchen. Mit mehreren Bereichen wählst du beim Benutzer
**„Rechte gelten für“**:

- **Alle Bereiche gleich:** die Häkchen gelten überall.
- **Je Bereich einzeln:** Nach dem Speichern folgt eine Seite, auf der du für jeden Bereich
  wählst: scharf, unscharf, Alarm beenden. Ein Bereich ohne Auswahl ist für den Benutzer
  gesperrt.

Ein Keypad für alle Bereiche schaltet beim Unscharfschalten nur die Bereiche, in denen der
Benutzer das darf.

## PIN-Regeln

**Systemeinstellungen → Benutzer und PINs → PIN-Regeln:**

| Einstellung | Bedeutung |
|---|---|
| **Master-PIN** | ein PIN ohne eigenen Benutzer, mit allen Rechten in allen Bereichen (z. B. für Alexa oder als Familien-Code am Keypad). Erscheint in der Benutzerliste als „Master-PIN“; im Logbuch steht dann nur „Master-PIN“, nicht wer es war |
| **PIN auch zum Scharfschalten verlangen** | Standard aus |
| **Alarm ohne PIN beenden** | Knopf „Alarm beenden“ auch mit PIN (Standard aus) |
| **Alarmkarte: PIN für Konten ohne Hauswacht-Benutzer verlangen** | Standard an. Gilt nur in der Karte [„Hauswacht Alarm“](dashboard.md#ohne-pin-zwang); zugeordnete Konten schalten dort ohne PIN |
| **Dashboard-Knöpfe trotz PIN erlauben** | „Unscharf schalten“, „Alarm beenden“ und die Scharf-Knöpfe funktionieren weiter. Der PIN schützt dann nur Bedienfeld, Keypads und Sprachassistenten – an die Knöpfe kommen ohnehin nur angemeldete Home-Assistant-Benutzer |

- PINs haben 4–8 Ziffern und werden nur als Hash gespeichert.
- Ohne PIN darf die Anlage **nicht** für Sprachassistenten freigegeben werden.
- Ein PIN aus Versionen vor 0.16.1 wurde beim Update zum Benutzer „Hauptbenutzer“.

## Sperre nach falschen Eingaben

Schutz gegen Durchprobieren. Die Regeln sind fest eingebaut (nicht einstellbar):

| Falsche Eingaben in Folge | Folge |
| --- | --- |
| 1–2 | nichts (nur gezählt) |
| 3–4 | Systemmeldung an die eingetragenen Empfänger, bei jedem weiteren Fehlversuch erneut |
| 5 | Eingabe **1 Minute** gesperrt |
| 6 | 2 Minuten |
| 7 | 4 Minuten |
| 8 | 8 Minuten |
| ab 9 | **15 Minuten** (Höchstwert) |

Wichtig zu wissen:

- **Gemeinsam für alles:** Ein Zähler für alle Bereiche und alle Eingabewege – Bedienfeld im
  Dashboard, Keypads, RFID-Leser, Alexa. Wer am Keypad falsch tippt, sperrt auch das Bedienfeld.
- **Während der Sperre wird jede Eingabe abgelehnt** – auch ein richtiger PIN und eine
  richtige Karte. Das Keypad zeigt „ungültig“, das Bedienfeld „Zu viele falsche PIN-Eingaben.
  Bitte … Sekunden warten.“
- **Zurückgesetzt** wird der Zähler durch
  - eine richtige Eingabe (PIN oder Karte) außerhalb der Sperre,
  - den Knopf **„Falscheingaben zurücksetzen“** in der Karte „Hauswacht Test“ (zeigt die
    Anzahl; nur Administratoren) oder den Dienst `hauswacht.reset_code_lock` (nur
    Administratoren),
  - einen Neustart von Home Assistant oder ein Neuladen von Hauswacht,
  - **Zeitablauf:** Fehlversuche verfallen **24 Stunden nach dem letzten Fehlversuch**. Zwei
    falsche Eingaben heute und drei übermorgen ergeben also keine Sperre. Die Frist läuft
    gleitend ab dem letzten Fehlversuch – nicht um Mitternacht, sonst könnte man kurz vor und
    kurz nach Mitternacht doppelt so viele Versuche machen. Eine laufende Sperre endet davon
    unabhängig nach ihrer Dauer.
- **Was nicht zählt:** unbekannte Karten (Codes, die kein PIN sein können – so lassen sich
  Karten anlernen) und Eingaben ohne Code (z. B. Keypad-Taste ohne PIN/Karte).
- **Was gesondert gemeldet wird:** ein gesperrter oder abgelaufener PIN bzw. eine solche Karte
  (z. B. Gast außerhalb seiner Gültigkeit) – Systemmeldung „gesperrter Ausweis“; zählt zusätzlich
  als Fehlversuch.
- **Wenn man selbst gesperrt ist und der Alarm läuft:** Unscharf geht weiterhin über den Knopf
  „Unscharf schalten“ im Dashboard bzw. den Push-Knopf, sofern „Dashboard-Knöpfe trotz PIN
  erlauben“ an ist oder kein PIN existiert. Die Sperre betrifft nur die Code-Eingabe.
- **Stand anzeigen:** Attribute `code_failures` (Anzahl) und `code_locked_until` (Ende der
  Sperre) am Bedienfeld; jeder Fehlversuch löst das Ereignis `hauswacht_event` mit
  `type: InvalidCode` aus.
- **Rechenbeispiel:** Ein 4-stelliger PIN hat 10 000 Möglichkeiten. Wer am Stück probiert,
  bleibt bei 15 Minuten Sperre je Versuch und bräuchte im Schnitt mehrere Wochen. Wer immer
  einen Tag wartet, um den Zähler verfallen zu lassen, schafft nur 4 Versuche pro Tag ohne
  Sperre – also Jahre. Und ab dem 3. Versuch kommt jedes Mal eine Meldung.

## Bedrohungs-PIN

Wer gezwungen wird, die Anlage auszuschalten, gibt seinen **Bedrohungs-PIN** ein:

- Die Anlage schaltet **ganz normal**; Bedienfeld, Logbuch und Dashboard sehen unauffällig aus
  („geändert von Petra“).
- Heimlich geht ein Notruf mit höchster Priorität an die **Empfänger Bedrohungsalarm**
  (Benachrichtigungen). Keine Sirene, keine sichtbare Meldung, nie über Lautsprecher.
- Der Bedrohungs-PIN wirkt auch, wenn der Benutzer das Recht sonst nicht hätte, und auch am
  Keypad.
- Er darf keinem normalen PIN und keinem anderen Bedrohungs-PIN gleichen; das wird beim
  Speichern geprüft.
- **Unbedingt Empfänger eintragen** – ohne Empfänger hat er keine Wirkung außer dem normalen
  Schalten.
