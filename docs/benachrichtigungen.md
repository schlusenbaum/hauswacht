# Benachrichtigungen und Sprachausgabe

## Empfänger

**Benachrichtigungen** mit den Punkten „Empfänger und Ereignisse“, „Eigene
Texte für Push-Nachrichten“ und zwei Punkten zur [Sprachausgabe](#sprachausgabe-lautsprecher).

- **Allgemeine Empfänger:** notify-Dienste, z. B. `mobile_app_…` der Home-Assistant-App, und
  **Benachrichtigungs-Entitäten** (`notify.…`), z. B. von WhatsApp-, Telegram- oder
  E-Mail-Integrationen. Sie bekommen jede Meldung, für die beim Ereignis keine eigenen Empfänger
  eingetragen sind.
- **Entitäten bekommen nur Titel und Text** („– nur Text“ in der Auswahl): keine Knöpfe, kein
  Durchbrechen von „Nicht stören“. Gut als zusätzlicher Kanal (z. B. Familiengruppe), die
  Home-Assistant-App bleibt das eigentliche Alarmsignal. Lautsprecher (Durchsage/Sprechen)
  erscheinen hier nicht, sie stehen unter „Sprachausgabe“; der Bedrohungsalarm geht nie an
  Lautsprecher.
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
| Automatik (automatisch scharf/unscharf) | an | Ereignis, sonst allgemein |
| Störung (Sensor ausgefallen, Manipulation, Infrastruktur) | an | Ereignis, sonst allgemein |
| System (Neustart, PIN gesperrt, falscher PIN) | an | Ereignis, sonst allgemein |
| Erinnerung „Alle weg“ | an, sobald eingerichtet | Ereignis, sonst allgemein |
| Hinweis beim Scharfschalten (offene Melder, die nur in Auslöseregeln vorkommen) | an | Ereignis, sonst allgemein |
| Immer aktiver Melder (unscharf, ohne Sirene) | an, **wichtig** | Ereignis, sonst allgemein |
| Auslöseregel „nur Benachrichtigung“ erfüllt | an | Ereignis, sonst allgemein |
| Unbestätigte Auslösung (Auslöseregel nur teilweise erfüllt, kein Alarm) | aus | Ereignis, sonst allgemein |
| Melder löst häufig allein aus (3× in einer Stunde eine Auslöseregel begonnen) | aus | Ereignis, sonst allgemein |

- **Bedrohungsalarm** ist kein Ereignis zum Abschalten: immer an, eigene Empfänger
  („Empfänger Bedrohungsalarm“).
- **Wichtige Hinweise:** Alarm und Bedrohung durchbrechen „Nicht stören“ (Option „Alarm und
  Bedrohung als wichtige Hinweise“, Standard an). iPhone: kritischer Hinweis – beim ersten Mal
  in der App erlauben. Android: Kanal `alarm_stream`, klingt auch im lautlosen Modus. Alle
  anderen Meldungen gehen mit hoher Priorität, aber normal raus.
- Im Testmodus werden Benachrichtigungen nur verschickt, wenn „Auch im Testmodus
  benachrichtigen“ an ist. Der Titel beginnt dann mit „[TEST]“.

## Eigene Texte und Platzhalter

**Benachrichtigungen → Eigene Texte für Push-Nachrichten:** Titel und Text je Ereignis selbst
formulieren; leer = Standardtext. Dieselben Platzhalter gelten für die Sprachausgabe:

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

Beide Schreibweisen funktionieren immer, auch gemischt. Der Einstellungsdialog nennt die Namen in
der Sprache von Home Assistant.

Beispiel: `Einbruch {bereich}: {melder} ({profil}, {uhrzeit})`. Unbekannte Platzhalter oder
Klammerfehler lassen sich nicht speichern; nach dem Speichern zeigt das Menü eine Vorschau mit
Beispielwerten. Nicht vorhandene Werte bleiben leer. Die Knöpfe in Push-Nachrichten bleiben
unverändert.

## Sprachausgabe (Lautsprecher)

Hauswacht kann Ereignisse über Lautsprecher ansagen, z. B. **Echo-Geräte** über die
Home-Assistant-Integration „Alexa Devices“. Geeignet ist jedes Gerät mit
Benachrichtigungs-Entitäten (`notify.…`).

**Benachrichtigungen → Sprachausgabe – Lautsprecher, Wiederholung, Nachtruhe:**

| Einstellung | Bedeutung |
|---|---|
| Lautsprecher | Geräte, die standardmäßig alle eingeschalteten Ereignisse ansagen |
| Alarm-Durchsage wiederholen alle | wiederholt die Alarm-Durchsage alle N Sekunden (10–300), bis der Alarm beendet ist; 0 = nur einmal |
| Nachtruhe von–bis | in dieser Zeit nur Ereignisse mit „Auch in der Nachtruhe ansagen“ |

**Benachrichtigungen → Sprachausgabe – Ereignisse, Art und Texte** (je Ereignis):

| Einstellung | Bedeutung |
|---|---|
| Ansagen | an/aus |
| Art | **Durchsage** (mit Gong) oder **Sprechen**; Hauswacht wählt am Gerät die passende Entität |
| Eigene Lautsprecher | statt der Standard-Lautsprecher |
| Auch in der Nachtruhe ansagen | |
| Text | eigener Text mit Platzhaltern, leer = Standardtext (die Form zeigt Standardtext und Vorschau) |

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

## Erinnerung „Alle weg, Anlage unscharf“

**Benachrichtigungen → Erinnerung „Alle weg“:** Personen, Profil, Wartezeit.

Sind alle gewählten Personen weg und die Anlage ist unscharf, kommt nach der Wartezeit
**einmal** eine Erinnerung mit dem Knopf **„Jetzt scharf (Profil)“**. Hauswacht schaltet
dabei **nichts selbst** – die sichere Alternative zum automatischen Scharfschalten.
Unbekannter Aufenthalt zählt nicht als weg. Kommt jemand heim, beginnt alles von vorn. Der
Knopf gilt 2 Stunden.

## Push-Knopf „Unscharf schalten“

**Benachrichtigungen → „Knopf ‚Unscharf schalten‘ / ‚Alarm beenden‘ in Benachrichtigungen“.**

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
