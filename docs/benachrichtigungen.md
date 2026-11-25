# Benachrichtigungen und Sprachausgabe

**Deutsch** | [English](en/notifications.md)

## Empfänger

[Einstellungsseite](einstellungsseite.md#benachrichtigungen-bearbeiten) → Reiter
**Benachrichtigungen** mit „Empfänger und Ereignisse bearbeiten“, „Eigene Texte“ und der
[Sprachausgabe](#sprachausgabe-lautsprecher).

- **Allgemeine Empfänger:** notify-Dienste, z. B. `mobile_app_…` der Home-Assistant-App, und
  **Benachrichtigungs-Entitäten** (`notify.…`), z. B. von WhatsApp-, Telegram- oder
  E-Mail-Integrationen. Sie bekommen jede Meldung, für die beim Ereignis keine eigenen Empfänger
  eingetragen sind.
- **Entitäten bekommen nur Titel und Text** („– nur Text“ in der Auswahl): keine Knöpfe, kein
  Durchbrechen von „Nicht stören“. Gut als zusätzlicher Kanal (z. B. Familiengruppe), die
  Home-Assistant-App bleibt das eigentliche Alarmsignal. Lautsprecher (Durchsage/Sprechen)
  erscheinen hier nicht, sie stehen unter „Sprachausgabe“; der Bedrohungsalarm geht nie an
  Lautsprecher.
- **Jedes Handy nur einmal:** Die Home-Assistant-App bietet für jedes Handy einen Dienst
  (`mobile_app_…`) und inzwischen zusätzlich eine Benachrichtigungs-Entität. Hauswacht zeigt nur
  den Dienst – mit dem Namen des Handys aus Home Assistant, z. B. „Xiaomi 13 Christian“ statt
  „2211133g xiaomi13“ –, denn nur er kann Knöpfe, Aufräumen und wichtige Hinweise. Früher
  gewählte App-Entitäten stellt Hauswacht einmalig auf den Dienst desselben Handys um.
- **Pro Ereignis** (aufklappbare Bereiche): an/aus und eigene Empfänger.

**Sprache:** Benachrichtigungen, Push-Knöpfe, Ansagen und Berichte kommen in der Sprache von
Home Assistant – Deutsch, wenn Home Assistant auf Deutsch steht, sonst Englisch. Eigene Texte
werden so verschickt, wie sie eingetragen sind.

## Ereignisse

| Ereignis | Standard | Empfänger |
|---|---|---|
| Alarm | an, **wichtig** | zuerst „Benachrichtigen (Alarm)“ des Profils |
| Tür geöffnet (Eingangsverzögerung) | nur mit Push-Knopf | zuerst die des Profils |
| Alarm beendet | an | zuerst die des Profils |
| Scharf geschaltet / Unscharf geschaltet | aus | Ereignis, sonst allgemein |
| Scharfschaltung abgelehnt | an, mit Knöpfen | Ereignis, sonst allgemein |
| Automatik (automatisch scharf/unscharf) – nur, wenn „Scharf/Unscharf geschaltet“ aus ist, [siehe unten](#jede-meldung-nur-einmal) | an | Ereignis, sonst allgemein |
| Störung (Sensor ausgefallen, Manipulation, Infrastruktur) | an | Ereignis, sonst allgemein |
| System (Neustart, PIN gesperrt, falscher PIN) | an | Ereignis, sonst allgemein |
| Erinnerung „Alle weg“ | an, sobald eingerichtet | Ereignis, sonst allgemein |
| [Hinweis beim Scharfschalten](#hinweis-beim-scharfschalten) (scharf, aber nicht alles überwacht) | an | Ereignis, sonst allgemein |
| Immer aktiver Melder (unscharf, ohne Sirene) | an, **wichtig** | Ereignis, sonst allgemein |
| Auslöseregel „nur Benachrichtigung“ erfüllt | an | Ereignis, sonst allgemein |
| Unbestätigte Auslösung (Auslöseregel nur teilweise erfüllt, kein Alarm) | aus | Ereignis, sonst allgemein |
| Melder löst häufig allein aus (3× in einer Stunde eine Auslöseregel begonnen) | aus | Ereignis, sonst allgemein |
| [Durchgang](durchgang.md) (hereingelassen, rausgehen, Tür danach noch offen) | an | Ereignis, sonst allgemein |

- **Bedrohungsalarm** ist kein Ereignis zum Abschalten: immer an, eigene Empfänger
  („Empfänger Bedrohungsalarm“).
- **Wichtige Hinweise:** Alarm und Bedrohung durchbrechen „Nicht stören“ (Option „Alarm und
  Bedrohung als wichtige Hinweise“, Standard an). iPhone: kritischer Hinweis – beim ersten Mal
  in der App erlauben. Android: Kanal `alarm_stream`, klingt auch im lautlosen Modus. Alle
  anderen Meldungen gehen mit hoher Priorität, aber normal raus.
- **Alte Nachrichten räumen sich auf** und **nichts kommt doppelt** – siehe
  [Jede Meldung nur einmal](#jede-meldung-nur-einmal).
- Im Testmodus werden Benachrichtigungen nur verschickt, wenn „Auch im Testmodus
  benachrichtigen“ an ist. Der Titel beginnt dann mit „[TEST]“.

### Jede Meldung nur einmal

Hauswacht schickt zu einem Vorgang **eine** Nachricht und räumt alte Nachrichten wieder weg
(Home-Assistant-App). Benachrichtigungs-Entitäten (z. B. Telegram, WhatsApp) können Nachrichten
nicht zurückziehen – dort bleiben sie stehen.

| Vorgang | Was auf dem Handy passiert |
|---|---|
| Scharf, unscharf, Hinweis beim Scharfschalten | **Ersetzen einander** – es steht immer nur die neueste da. Wer beim Unscharfschalten keine Nachricht bekommt, bei dem verschwindet die Scharf-Nachricht einfach. |
| **Automatisch** scharf/unscharf (Uhrzeit, alle weg, Rückkehr …) | Ist „Scharf geschaltet“ bzw. „Unscharf geschaltet“ an, steht der Grund **in dieser Nachricht** – es kommt keine zweite „Automatik“-Nachricht. Ist es aus, kommt nur die Automatik-Nachricht. Beide ersetzen einander wie oben. |
| Unscharf über den **Push-Knopf** | Die Rückmeldung „unscharf geschaltet von …“ ersetzt die Scharf-Nachricht. |
| Alarm | Verschwindet beim Unscharfschalten. Wird nur der Alarm beendet und es bleibt scharf, **ersetzt** „Alarm beendet“ die Alarm-Nachricht – und verschwindet beim Unscharfschalten. |
| „Scharfschalten nicht möglich“ | Verschwindet, sobald es geklappt hat. Bei Taster, Kartenleser, NFC-Aufkleber und Türschloss kommt **nur** diese Nachricht, keine zusätzliche „Bedienteil abgelehnt“. |
| **Melder ausgefallen** (während scharf) | Eine Nachricht **je Melder**, mit seinem Namen. Fällt er erneut aus, bevor er wieder da war, kommt keine zweite. Meldet er sich wieder, **verschwindet** sie. Hauswacht wartet 10 Sekunden: Ist der Melder bis dahin wieder da, kommt gar nichts. Fällt gleichzeitig die [überwachte Funknetz](melder.md#funknetz-und-gateways-überwachen) aus (z. B. Zigbee2MQTT), kommt nur die Störungsmeldung – nicht zusätzlich eine für jeden Melder. |
| Falscher PIN | Warnungen ersetzen einander (es bleibt nur die letzte) und verschwinden, wenn die Falscheingaben zurückgesetzt werden. |

**Beispiel:** Profil „Nacht“ schaltet um 00:30 automatisch scharf, „Scharf geschaltet“ ist an.
Auf dem Handy steht eine Nachricht: „Hauswacht: scharf – Profil Nacht wurde automatisch scharf
geschaltet (Uhrzeit).“ Um 06:00 wird sie ersetzt durch „Hauswacht: unscharf – Profil Nacht wurde
automatisch unscharf geschaltet (Uhrzeit).“

## Eigene Texte und Platzhalter

**Einstellungsseite → Benachrichtigungen → Eigene Texte → Bearbeiten:** Titel und Text je Ereignis selbst
formulieren. Im Feld steht zuerst der **Text von Hauswacht** als Vorlage – mit Platzhaltern statt
Werten, z. B. `Profil {profil} scharf geschaltet ({wer}).` Einfach ändern und speichern. Bleibt die
Vorlage **unverändert** (oder das Feld leer), wird nichts gespeichert und Hauswacht schickt seinen
eigenen Text. Wo dieser je nach Lage anders aussieht (z. B. Störungen), steht `{text}` in der
Vorlage – das ist der vollständige Text von Hauswacht.

> **Gut zu wissen:** Ein eigener Text ersetzt den ganzen Text von Hauswacht. Beim Alarm hängt
> Hauswacht sonst z. B. noch an, welche Sirenen laufen. Wer das behalten will, schreibt `{text}`
> mit hinein, z. B. `{text} Bitte Nachbarn anrufen.`

Zurück zum Text von Hauswacht: auf der [Einstellungsseite](einstellungsseite.md#benachrichtigungen-bearbeiten)
der Knopf **„↺ Standardtext“**. Dieselben Platzhalter gelten für die
Sprachausgabe:

| Platzhalter | englisch | Inhalt |
|---|---|---|
| `{bereich}` | `{area}` | Bereichsname (leer bei nur einem Bereich) |
| `{profil}` | `{profile}` | Alarmprofil |
| `{melder}` | `{sensor}` | auslösender Melder mit Raum |
| `{offen}` | `{open}` | offene Melder |
| `{wer}` | `{who}` | wer geschaltet hat |
| `{sekunden}` | `{seconds}` | Eingangsverzögerung in Sekunden |
| `{uhrzeit}` | `{time}` | aktuelle Uhrzeit |
| `{regel}` | `{rule}` | Auslöseregel |
| `{grund}` | `{reason}` | Grund, z. B. warum das Scharfschalten scheiterte |
| `{text}` | `{text}` | der Standardtext von Hauswacht (im Titel: der Standardtitel) |

Beide Schreibweisen funktionieren immer, auch gemischt.

Beispiel: `Einbruch {bereich}: {melder} ({profil}, {uhrzeit})`. Unbekannte Platzhalter oder
Klammerfehler lassen sich nicht speichern. Nicht vorhandene Werte bleiben leer. Die Knöpfe in Push-Nachrichten bleiben
unverändert.

## Sprachausgabe (Lautsprecher)

Hauswacht kann Ereignisse über Lautsprecher ansagen, z. B. **Echo-Geräte** über die
Home-Assistant-Integration „Alexa Devices“. Geeignet ist jedes Gerät mit
Benachrichtigungs-Entitäten (`notify.…`).

**Einstellungsseite → Benachrichtigungen → Sprachausgabe → Bearbeiten – Lautsprecher, Wiederholung,
Nachtruhe:**

| Einstellung | Bedeutung |
|---|---|
| Lautsprecher | Geräte, die standardmäßig alle eingeschalteten Ereignisse ansagen |
| Alarm-Durchsage wiederholen alle | wiederholt die Alarm-Durchsage alle N Sekunden (10–300), bis der Alarm beendet ist; 0 = nur einmal |
| Nachtruhe von–bis | in dieser Zeit nur Ereignisse mit „Auch in der Nachtruhe ansagen“ |

**Sprachausgabe – Ereignisse, Art und Texte** (je Ereignis, im selben Seitenblatt):

| Einstellung | Bedeutung |
|---|---|
| Ansagen | an/aus |
| Art | **Durchsage** (mit Gong) oder **Sprechen**; Hauswacht wählt am Gerät die passende Entität |
| Eigene Lautsprecher | statt der Standard-Lautsprecher |
| Auch in der Nachtruhe ansagen | |
| Text | eigener Text mit Platzhaltern, leer = Standardtext |

Standardmäßig an (sobald Lautsprecher gewählt sind): Alarm, Eingangsverzögerung, Scharfschaltung
abgelehnt, immer aktiver Melder. In der Nachtruhe standardmäßig erlaubt: Alarm,
Eingangsverzögerung, immer aktiver Melder.

- **Pro Alarmprofil** gibt es „Zusätzliche Lautsprecher“: Sie sagen Alarm, Eingangsverzögerung
  und „Alarm beendet“ dieses Profils an – statt der Standard-Lautsprecher. Weil jedes Profil zu
  einem Bereich gehört, lässt sich so festlegen, wo ein Alarm in der Garage angesagt wird.
- Bei mehreren Bereichen steht der Bereichsname vor dem Standardtext („Garage: Achtung …“).
- Ein **stiller Alarm** wird nie angesagt, der **Bedrohungsalarm** nie über Lautsprecher.
- **Testmodus:** angesagt wird nur mit „Auch im Testmodus benachrichtigen“, dann mit „Test.“
  vorweg.
- Ist am Echo „Nicht stören“ an, sagt er unter Umständen nichts an. Die Sprachausgabe ergänzt
  Push und Sirene, sie ersetzt sie nicht.

## Scharfschaltung abgelehnt: „Trotzdem scharf“ / „Erneut versuchen“

Wird das Scharfschalten abgelehnt (z. B. Fenster offen), kommt eine Benachrichtigung mit dem
Grund und den Knöpfen:

- **„Trotzdem scharf“** – nur wenn das Profil offene Sensoren nach Rückfrage überbrücken darf
  („Offene Sensoren beim Scharfschalten: Nach Bestätigung erlauben“). Offene Sensoren werden bis zum Schließen überbrückt.
- **„Erneut versuchen“** – prüft noch einmal (z. B. nachdem das Fenster zu ist). Klappt es
  wieder nicht, kommt eine neue Benachrichtigung.

Die Knöpfe gelten 15 Minuten und je einmal, brauchen einen angemeldeten Home-Assistant-Benutzer
mit dem Recht „Scharf schalten“ und wirken nur, wenn die Anlage noch unscharf ist.

## Hinweis beim Scharfschalten

Sobald ein Profil scharf ist, aber **nicht alles überwacht** wird, kommt diese Nachricht – egal ob
über Keypad, Karte, Push-Knopf oder Automatik:

> Profil Nacht ist scharf (Christian, Keypad). Nicht überwacht: Eingang: Türkontakt vorne –
> offen, überbrückt bis zum Unscharfschalten; Kellerfenster – ausgefallen, wird wieder
> überwacht, sobald er sich meldet.

Genannt werden:

| Lücke | Wie lange |
|---|---|
| **Offener Melder, überbrückt** („trotzdem scharf“ oder automatisch überbrückt) | bis zum Unscharfschalten |
| **Ausgefallener Melder**, in Kauf genommen (nach Bestätigung oder automatisch) | bis er sich wieder meldet – dann wird er wieder überwacht |
| **Offener Melder, der nur in Auslöseregeln vorkommt** | bis er zu und wieder auf geht |

**Nur eine Nachricht:** Ist „Scharf geschaltet“ eingeschaltet, stehen die Lücken einfach in
dieser Nachricht („Profil Nacht scharf geschaltet (Christian). Nicht überwacht: …“). Der eigene
Hinweis kommt nur, wenn „Scharf geschaltet“ aus ist.

Dazu ein Eintrag unter Benachrichtigungen in Home Assistant und das Ereignis `ArmedWithGaps`
(siehe [Referenz](referenz.md)). In eigenen Texten: `{offen}` (offene Melder), `{grund}` (alle
Lücken mit Erklärung), `{profil}`, `{wer}`.

## Erinnerung „Alle weg, Anlage unscharf“

**Einstellungsseite → Benachrichtigungen → Empfänger und Ereignisse bearbeiten → Erinnerung „Alle
weg, aber nicht scharf“:** Personen, Profil, Wartezeit.

Sind alle gewählten Personen weg und die Anlage ist unscharf, kommt nach der Wartezeit
**einmal** eine Erinnerung mit dem Knopf **„Jetzt scharf (Profil)“**. Hauswacht schaltet
dabei **nichts selbst** – die sichere Alternative zum automatischen Scharfschalten.
Unbekannter Aufenthalt zählt nicht als weg. Kommt jemand heim, beginnt alles von vorn. Der
Knopf gilt 2 Stunden.

## Push-Knopf „Unscharf schalten“

**Einstellungsseite → Benachrichtigungen → Empfänger und Ereignisse bearbeiten → „Knopf ‚Unscharf
schalten‘ in der Alarm-Nachricht“.**

Ist die Option an, bekommen die Alarm-Empfänger des Profils:

- beim **Öffnen einer Eingangstür** (Eingangsverzögerung läuft) sofort eine Benachrichtigung
  „Tür geöffnet“,
- beim **Alarm** die Alarmmeldung,

jeweils mit dem Knopf **„Unscharf schalten“** direkt in der Benachrichtigung.

- Funktioniert nur mit der **Home-Assistant-App** (`notify.mobile_app_…`).
- Der Knopf gilt nur für die **laufende Scharfschaltung**. Ein alter Knopf aus einer früheren
  Benachrichtigung bewirkt nichts.
- Hauswacht prüft, dass der Knopf von einem angemeldeten Home-Assistant-Benutzer kommt, und
  meldet danach „Unscharf geschaltet über den Push-Knopf von …“.
- **iPhone:** Der Knopf verlangt ein entsperrtes Gerät (Face ID oder Code).
  **Android:** Die App kennt diese Sperre nicht. Wer das Handy in die Hand bekommt, kann den
  Knopf auf dem Sperrbildschirm drücken. Abhilfe: in Android „Sensible Inhalte auf dem
  Sperrbildschirm ausblenden“ für die Home-Assistant-App.
- Der Knopf funktioniert ohne PIN – er ersetzt die PIN-Eingabe durch das angemeldete Handy.
- Nach dem Unscharfschalten wird die Benachrichtigung auf den Handys entfernt.
