# Alarmprofile und Bereiche

**Deutsch** | [English](en/profiles.md)

## Alarmprofile

**Alarmprofile → Alarmprofil anlegen.** Es gibt keine vorgegebenen Profile – du legst so viele
an, wie du brauchst, z. B. „Zuhause“, „Nacht“, „Abwesend“, „Urlaub“.

> **Jedes Profil ist eine Art, scharf zu schalten.** „Unscharf“ ist kein Profil, sondern der
> Grundzustand – erreichbar über „Unscharf“ am Bedienfeld, die Unscharf-Taste am Keypad oder die
> Alarmkarte. Ein Profil namens „Unscharf“ würde die Anlage scharf schalten. Legst du aus
> Gewohnheit (z. B. von anderen Alarm-Integrationen) eines an, bitte wieder löschen.

| Einstellung | Bedeutung |
|---|---|
| Name, Symbol | Wie das Profil in Auswahlliste, Meldungen und am Bedienfeld erscheint |
| Knopf am Bedienfeld | Optional: Zuhause, Nacht, Abwesend, Urlaub oder Benutzerdefiniert. Jeder Knopf gehört höchstens einem Profil (je Bereich) |
| Bereich | Nur bei mehreren [Bereichen](#bereiche) |
| Meldergruppen – jeder Melder löst allein aus | Jeder Melder dieser Gruppen löst für sich aus (Tür mit Eingangsverzögerung, Fenster sofort …) |
| Ausgenommene Melder | Melder dieser Gruppen, die in diesem Profil **nicht** einzeln auslösen (z. B. Bewegung Flur OG in „Nacht“); in Auslöseregeln zählen sie weiter |
| Auslöseregeln | Zusätzlich: Abfolgen von Meldern, siehe [Auslöseregeln](ausloeseregeln.md). Das Feld erscheint erst, wenn es Auslöseregeln gibt |
| Ausgangs- / Eingangsverzögerung | Zeit zum Verlassen bzw. zum Unscharfschalten nach dem Betreten (Standard je 30 s) |
| Dauer der Alarmreaktion | Wie lange ein Alarmzyklus dauert (Standard 180 s) |
| Offene Sensoren beim Scharfschalten | verweigern · nach Bestätigung erlauben · automatisch überbrücken. Bestätigen: „Trotzdem scharf“ in Karte oder Push – oder am Keypad [dieselbe Taste noch einmal](bedienteile.md#trotzdem-scharf-am-keypad) |
| Ausgefallene Sensoren beim Scharfschalten | verweigern · nach Bestätigung erlauben · automatisch überbrücken (**Experten**). Ein ausgefallener Melder (z. B. leere Batterie) wird **wieder überwacht, sobald er sich meldet** – bis dahin ist er eine Lücke. „Automatisch überbrücken“ schaltet ohne Rückfrage scharf; der [Hinweis beim Scharfschalten](benachrichtigungen.md#hinweis-beim-scharfschalten) nennt ihn |
| Maximale Alarmzyklen | Wie oft nach einem Alarm erneut ausgelöst werden darf |
| Manipulation löst Alarm aus | Sonst wird Manipulation nur gemeldet |
| Gekippte Fenster erlaubt | Nur mit [Meldern mit Kippstellung](melder.md#melder-mit-kippstellung-gekippt) (sonst ausgeblendet): Ein gekipptes Fenster zählt als zu, erst ganz öffnen löst aus. **Aus** (Standard): gekippt zählt wie offen. Typisch: an bei „Nacht“, aus bei „Abwesend“. Der [Einrichtungsassistent](assistent.md#6-alarmprofile) fragt beim Nachtprofil danach |
| Sirenen, Ton, Lautstärke, stiller Alarm | Reaktion bei Alarm, siehe [Sirenen](sirenen.md) |
| Benachrichtigen (Alarm) | Wer bei einem Alarm eine Push-Nachricht bekommt |
| Zusätzliche Lautsprecher | Ansagen dieses Profils, siehe [Sprachausgabe](benachrichtigungen.md#sprachausgabe-lautsprecher) |
| Automatik | Uhrzeit und Anwesenheit, siehe [unten](#automatik) |
| Scharf durch Schließen der Tür | siehe [unten](#scharf-durch-schließen-der-tür) |

Oben im Formular steht, welche Melder in diesem Profil derzeit scharf werden.

Ein Profil **ohne Meldergruppen und ohne Auslöseregeln** lässt sich nicht scharf schalten – so
entsteht nie der Eindruck, das Haus sei geschützt, obwohl nichts überwacht wird.

**Bedienen:** Profile mit Knopf über das Bedienfeld; jedes Profil – auch ohne Knopf – über die
Auswahlliste „Profil“ und den Knopf „Scharf schalten“ oder die Aktion `hauswacht.arm`. Profile
ohne eigenen Knopf zeigt das Bedienfeld im scharfen Zustand als „benutzerdefiniert“; das
Attribut `profile_name` nennt das Profil.

Die wichtigsten Werte lassen sich auch im Dashboard ändern, siehe
[Profil-Einstellungen im Dashboard](dashboard.md#profil-einstellungen-im-dashboard).

## Automatik

Im Profil, aufklappbar unter **Automatik**. Alle Felder sind optional – leer heißt: aus.

| Einstellung | Wirkung |
|---|---|
| Scharf um / Unscharf um | Uhrzeit, zu der das Profil scharf bzw. unscharf geschaltet wird |
| Oder nach Zeitplan (Helfer) | Für **je Wochentag andere Zeiten**: ein Zeitplan-Helfer; Beginn eines Zeitblocks = scharf, Ende = unscharf, siehe [unten](#je-wochentag-andere-zeiten-zeitplan) |
| An diesen Tagen | Tage, an denen die Uhrzeiten gelten; leer = täglich. Über Nacht siehe [unten](#uhrzeiten-über-nacht-und-scharf-von-hand) |
| Scharf, wenn alle diese Personen weg sind | Sind alle gewählten Personen nicht zu Hause, wird nach der Wartezeit scharf geschaltet |
| Wartezeit | Standard 15 Minuten. Kommt in dieser Zeit jemand zurück, wird nichts geschaltet |

Sicherheitsregeln:

- Automatisch scharf nur, wenn die Anlage unscharf ist – nie über ein anderes Profil hinweg.
- Offene oder ausgefallene Melder werden automatisch **nie** bestätigt (außer das Profil
  überbrückt sie ohnehin automatisch). Klappt das
  Scharfschalten deshalb nicht, kommt eine Systemmeldung.
- Ein **laufender Alarm** wird nie automatisch beendet. Eine laufende Eingangsverzögerung nur
  über [Bei Rückkehr](#bei-rückkehr) („Unscharf mit Türbeleg“, „Unscharf, auch nach
  Scharfschalten von Hand“ oder „Reinlassen“).
- Eine Person mit unbekanntem oder nicht verfügbarem Aufenthalt gilt **nicht** als weg.
- Nach einem Neustart gilt das [Verhalten nach Neustart](installation.md#verhalten-nach-einem-neustart)
  (Standard: vorheriger Zustand); die Anwesenheits-Automatik greift erst beim nächsten Wechsel
  einer Person.

Handys, die nur über das WLAN erkannt werden (Ping am Router), melden im Standby manchmal kurz
„weg“. Die Wartezeit fängt das ab.

Statt automatisch scharf zu schalten, kann Hauswacht auch nur erinnern: siehe
[Erinnerung „Alle weg“](benachrichtigungen.md#erinnerung-alle-weg-anlage-unscharf).

### Uhrzeiten, über Nacht und „scharf von Hand“

**Über Nacht:** Liegt „Unscharf um“ vor „Scharf um“ (z. B. scharf 23:00, unscharf 06:30), gehört
der Morgen zur Nacht davor. Hauswacht schaltet dann auch am Morgen **nach** einem aktiven Tag
unscharf.

Beispiel „Nacht“, scharf 23:00, unscharf 06:30, Tage Mo–Fr:

| Wann | Was passiert |
|---|---|
| Freitag 23:00 | scharf (Freitag ist aktiv) |
| Samstag 06:30 | **unscharf** – die Nacht hat am Freitag begonnen |
| Samstag 23:00 | nichts (Samstag ist nicht aktiv) |
| Sonntag 06:30 | nichts – Samstag und Sonntag sind nicht aktiv |
| Montag 06:30 | unscharf (Montag ist aktiv) |

Ein Tagesprofil (z. B. scharf 07:30, unscharf 16:00) gilt nur an den gewählten Tagen.

**Scharf von Hand:** Ein Profil mit Uhrzeiten lässt sich jederzeit auch von Hand scharf
schalten. Dann gilt:

- **„Scharf um“** tut nichts, wenn die Anlage schon scharf ist – Hauswacht schaltet nie über ein
  scharfes Profil hinweg.
- **„Unscharf um“** schaltet das Profil unscharf, egal wer es scharf geschaltet hat (nicht
  während einer Eingangsverzögerung oder eines Alarms).
- Ein **anderes** Profil, von Hand scharf geschaltet, beendet „Unscharf um“ nicht – die Uhrzeit
  gilt nur für ihr eigenes Profil.

Beispiel: „Nacht“ um 22:00 von Hand scharf → 23:00 nichts → 06:30 unscharf.

### Je Wochentag andere Zeiten (Zeitplan)

„Scharf um“ und „Unscharf um“ gelten an allen gewählten Tagen gleich. Brauchst du **an
verschiedenen Tagen verschiedene Zeiten**, nimm statt eines zweiten Profils einen
**Zeitplan-Helfer** von Home Assistant:

1. Einstellungen → Geräte & Dienste → **Helfer** → Helfer erstellen → **Zeitplan**, Name z. B.
   „Nacht“.
2. Im Zeitplan je Wochentag die Zeitblöcke ziehen, in denen das Profil scharf sein soll.
3. Im Profil unter **Automatik → Oder nach Zeitplan (Helfer)** den Zeitplan wählen – oder im
   [Einrichtungsassistenten](assistent.md) im Schritt Alarmprofile.

Den Zeitplan legst du selbst an: Home Assistant bietet Integrationen keinen offiziellen Weg,
Zeitpläne anzulegen, und Hauswacht greift nicht in interne Teile ein, die sich mit Updates ändern
können. Die Zeiten änderst du später direkt im Zeitplan – Hauswacht musst du dafür nicht öffnen.

*Beispiel „Nacht“:*

| Tag | Zeitblock im Zeitplan | Was passiert |
|---|---|---|
| Mo–Do | 22:30–24:00 und 0:00–6:00 | 22:30 scharf, 6:00 unscharf |
| Fr | 0:00–6:00 | 6:00 unscharf (Freitag Abend kein Block) |
| Sa | 0:30–8:00 | 0:30 scharf, 8:00 unscharf |
| So | 0:30–8:00 und 22:30–24:00 | 0:30 scharf, 8:00 unscharf, 22:30 scharf |

Ein Block über Mitternacht wird im Zeitplan als zwei Blöcke eingetragen (bis 24:00 und ab 0:00);
Home Assistant zeigt das als durchgehend an – Hauswacht schaltet dann nicht dazwischen.

Es gelten dieselben Regeln wie für die Uhrzeiten:

- **Scharf** nur aus „unscharf“ heraus; im **Gastmodus** wird nicht scharf geschaltet. Offene
  Melder werden nie bestätigt – dann kommt eine Meldung.
- **Unscharf** nur, wenn genau dieses Profil scharf ist – nie während Eingangsverzögerung oder
  Alarm. Hast du das Profil von Hand scharf geschaltet, schaltet das Ende des Blocks es trotzdem
  unscharf.
- Die Wochentage der Automatik gelten für den Zeitplan **nicht** – der Zeitplan hat seine eigenen.
- **Nach einem Neustart** holt der Zeitplan nichts nach: Hat ein Block während des Neustarts
  begonnen oder geendet, gilt das [Verhalten nach Neustart](installation.md#verhalten-nach-einem-neustart).
  So wird eine von Hand unscharf geschaltete Anlage nicht durch einen Neustart wieder scharf.
- Uhrzeiten und Zeitplan lassen sich kombinieren, sinnvoll ist aber meist nur eins von beiden.

### Woran Hauswacht erkennt, wer zuhause ist

Grundlage ist die **Person** in Home Assistant (`person.…`). Zusätzlich kannst du je Person
weitere **Signale** wählen – unter **Systemeinstellungen → Anwesenheit und
Heimkehr-Beobachtung**, im zweiten Schritt. Dieselben Signale nutzt auch die
[Heimkehr-Beobachtung](beobachtung.md#zusätzliche-signale-je-person); du stellst sie nur an
einer Stelle ein.

Geeignet sind z. B. der WLAN-Sensor der Companion App, Bluetooth (Bermuda), ein Router-Tracker,
die Richtung aus der Integration „Nähe“ (oder „Places“) oder ein beliebiger Binärsensor (an = zuhause) – etwa
eine HomeKit-Variable „Martin zuhause“.

| Die Person gilt als … | wenn … |
|---|---|
| **zuhause** | irgendein Signal zuhause meldet (die Person selbst oder eines der Signale) |
| **weg** | **alle** Signale sicher „weg“ melden |
| unbekannt | sonst, z. B. ein Signal ist „nicht verfügbar“ – das zählt **nie** als weg |

**Richtung (Nähe, Places)** zählt nur mit zwei Werten: **„angekommen“** = zuhause und
**„entfernt sich“** = weg. **„Nähert sich“** und **„steht“** werden übergangen (ab 0.60): Wer
sich nähert, ist noch nicht da – sonst würde eine Fahrt in der Umgebung, die kurz Richtung
Zuhause führt, schon als Rückkehr gelten und z. B. „Bei Rückkehr“ auslösen. Und „steht“
(etwa im Büro) hält „alle weg“ nicht auf.

**Beispiel:** Anna ist laut Person „nicht zuhause“, ihr WLAN-Sensor meldet aber noch das
Heim-WLAN. Dann ist Anna zuhause, „Scharf, wenn alle weg“ wartet. Erst wenn auch das WLAN
weg ist, beginnt die Wartezeit.

So schaltet ein kurz aussetzendes Signal nicht gleich scharf, und das schnellste Signal
erkennt die Rückkehr.

### Bei Rückkehr

*Neu in 0.61. Einstellen nur auf der [Einstellungsseite](einstellungsseite.md) → Profile →
Profil → Abschnitt **„Bei Rückkehr“**.*

Hier legst du fest, was passiert, wenn eine bestimmte Person nach Hause kommt. Grundlage ist der
Personen-Status in Home Assistant (meist das Handy) plus die [Signale](#woran-hauswacht-erkennt-wer-zuhause-ist)
der Person. „Heimkommen“ heißt immer: Die Person war vorher sicher weg und ist jetzt zuhause.

| Einstellung | Wirkung | Standard |
|---|---|---|
| Wenn jemand heimkommt | Eine der fünf Stufen unten | **Nichts** |
| Für diese Personen | Wer „Bei Rückkehr“ auslöst. Eigene Liste – unabhängig von „Scharf, wenn alle diese Personen weg sind“. Ohne Person lässt sich eine Stufe außer „Nichts“ nicht speichern | keine |
| Zeitfenster Handy und Tür (unter „Mehr Einstellungen“) | Nur für „Unscharf mit Türbeleg“ und „Reinlassen“: so weit dürfen Handy-Meldung und Türöffnung auseinanderliegen. 1–30 Minuten. Verzögert den Alarm **nicht**, siehe [Was das Zeitfenster bedeutet](#was-das-zeitfenster-bedeutet) | 5 Minuten |

Neben jedem Feld steht ein **ⓘ**: Mauszeiger drauf zeigt die Erklärung, Antippen (Handy,
Tablet) klappt sie auf. Unter der Auswahl steht in einem Satz **„So verhält sich das:“** – er
ändert sich sofort mit der Stufe und dem Zeitfenster.

| Stufe | Was passiert | Was schützt vor einer falschen Ortung | Gut für |
|---|---|---|---|
| **Nichts** | Hauswacht tut nichts. Unscharf nur per PIN, Karte, Keypad oder App | – | Urlaub |
| **Unscharf, nur wenn automatisch scharf** | Eine der Personen kommt heim → unscharf. Nur wenn Hauswacht das Profil **selbst** scharf geschaltet hat (z. B. „alle weg“) und noch keine Tür aufging | Kopplung an die Automatik: von Hand scharf bleibt scharf | wie bis 0.60 „Wie bisher“ |
| **Unscharf mit Türbeleg** | Eine der Personen kommt heim **und** eine Eingangstür geht auf – beides innerhalb des Zeitfensters, egal in welcher Reihenfolge. Auch in der Eingangsverzögerung, egal wie scharf geschaltet wurde | zwei Belege: Ortung **und** Tür | „Abwesend“ – die **Empfehlung** für die meisten Häuser |
| **Unscharf, auch nach Scharfschalten von Hand** | Eine der Personen kommt heim (vorher mindestens 5 Minuten weg) → sofort unscharf, egal wie scharf geschaltet wurde. Keine Tür nötig | nur die Ortung – deshalb die Warnung im Formular | wenn du bequem willst und das Risiko kennst |
| **Reinlassen (Durchgang)** | Eine Eingangstür geht auf und das Handy einer Person meldet bis zum Zeitfenster davor oder noch in der Eingangsverzögerung „zuhause“ (vorher mindestens 5 Minuten weg) → Hauswacht lässt sie **ohne PIN herein, das Profil bleibt scharf** | Ortung **und** Tür; der Rest im Haus bleibt scharf | „Nacht“: die anderen schlafen, die Anlage bleibt an. Einzelheiten unter [Reinlassen per Handy](durchgang.md#reinlassen-per-handy) |

**Beispiel „Nacht“ mit Reinlassen:** Christian und Petra schlafen, die Anlage steht auf „Nacht“.
Niklas kommt um 1 Uhr heim. Sein Handy meldet in der Einfahrt „zuhause“, eine Minute später
schließt er die Haustür auf → kein Alarm, keine PIN, „Nacht“ bleibt scharf. Ein Fremder an
derselben Tür bekommt die normale Eingangsverzögerung und dann Alarm.

**Beispiel „Abwesend“ mit Türbeleg:** Alle sind weg, Hauswacht hat automatisch scharf
geschaltet. Petra kommt vom Einkaufen, ihr Handy meldet „zuhause“, sie öffnet die Haustür →
sofort unscharf.

> **Warum ist „Unscharf, auch nach Scharfschalten von Hand“ nicht die Empfehlung?** Hier reicht
> das Handy allein. Wer das Handy einer Person hat – oder ein gefundenes Handy –, kommt heim und
> die Anlage ist aus. Bei „Unscharf mit Türbeleg“ muss zusätzlich eine Tür aufgehen, und erst
> dann zählt die Heimkehr.

**Nach dem Update auf 0.61** übernimmt Hauswacht deine bisherigen Einstellungen:
„Unscharf bei Rückkehr“ (Wie bisher / Mit Türbeleg) mit den Personen aus „Scharf, wenn alle weg“
und das Handy-Reinlassen aus dem Durchgang. Waren in einem Profil **beide** an, gewinnt
**Reinlassen** – das Profil bleibt dann scharf, also die sichere Seite –, und du bekommst eine
Benachrichtigung in Home Assistant. Die alten Felder im Optionen-Dialog sind weg; dort steht
ein Hinweis auf die Einstellungsseite.

**„Unscharf mit Türbeleg“ im Alltag**

- *Die Ortung kommt zu spät:* Christian öffnet die Haustür, die Eingangsverzögerung läuft.
  20 Sekunden später meldet sein Handy „zuhause“ → Hauswacht schaltet unscharf, noch bevor
  der Alarm kommt.
- *Die Ortung kommt früh:* Das Handy meldet schon an der Straßenecke „zuhause“. Es passiert
  erst einmal nichts. Zwei Minuten später geht die Haustür auf → sofort unscharf.
- *Geister-Heimkehr:* Niklas’ Handy meldet nachts „zuhause“, obwohl er unterwegs ist. Ohne
  geöffnete Tür passiert **nichts**.
- *Einbruch:* Jemand öffnet die Tür, aber niemand ist heimgekommen → normale
  Eingangsverzögerung und Alarm.

#### Was das Zeitfenster bedeutet

Das Zeitfenster **verzögert den Alarm nie**. Wann der Alarm kommt, bestimmt allein die
**Eingangsverzögerung** – genau wie ohne diese Funktion. Das Zeitfenster sagt nur, wie weit
Ortung und Türöffnung auseinanderliegen dürfen, damit sie als **eine** Heimkehr zählen.

Beispiel mit 30 Sekunden Eingangsverzögerung und 5 Minuten Zeitfenster:

| Was passiert | Ergebnis |
|---|---|
| Handy meldet „zuhause“, 2 Minuten später geht die Tür auf | Beim Öffnen **sofort unscharf**, kein Countdown |
| Handy meldet „zuhause“, erst 7 Minuten später geht die Tür auf | Zu lange her: normale Eingangsverzögerung, nach 30 s Alarm (wenn niemand unscharf schaltet) |
| Tür geht auf, 20 s später meldet das Handy „zuhause“ | Nach 20 s **unscharf** (noch in der Eingangsverzögerung) |
| Tür geht auf, das Handy meldet sich erst nach 45 s | Nach 30 s **Alarm** wie immer; das Handy beendet ihn nicht |
| Tür geht auf, kein Handy meldet sich (Einbrecher, oder du ohne Handy) | Nach 30 s **Alarm** wie immer |

Kurz: Das Handy darf sich bis zu 5 Minuten **vor** der Tür melden. Meldet es sich **nach** der
Tür, muss das innerhalb der Eingangsverzögerung passieren.

Genau genommen gilt:

- **Heimkommen** heißt: Die Person war vorher sicher weg und ist jetzt zuhause. Wer die ganze
  Zeit zuhause war, „kommt nicht heim“.
- Rückkehr und Tür zählen nur, solange das Profil **scharf** ist oder die
  **Eingangsverzögerung** läuft – nicht in der Ausgangsverzögerung.
- Als Tür zählen alle **Eingangstüren** (Melder mit der Rolle „Eingang“). Eine Tür, die sofort
  Alarm auslöst, ist kein Beleg.
- Ein laufender **Alarm** wird nie beendet.
- Nach dem Unscharfschalten verfallen beide Belege; sie werden nicht für später gesammelt.

**Welche Eingangsverzögerung brauche ich?** Kommt die Ortung erst nach dem Öffnen, muss die
Eingangsverzögerung so lange reichen. Die [Heimkehr-Beobachtung](beobachtung.md#empfehlung-für-unscharf-mit-türbeleg)
rechnet das je Person aus und nennt einen Wert.

> **Restrisiko:** Wer das Handy einer der Personen **und** Zugang zur Tür hat (z. B. Handy und
> Schlüssel gestohlen), schaltet damit unscharf. Für „Urlaub“ deshalb besser **Aus**.


### Gastmodus

Gäste, Babysitter oder Handwerker sind im Haus, haben aber keine Ortung – für Hauswacht sieht
das Haus leer aus. Damit die Automatik dann nicht scharf schaltet, gibt es den **Gastmodus**.

**Solange er an ist,** schaltet Hauswacht den Bereich **nicht automatisch** scharf: weder nach
Uhrzeit noch „wenn alle weg“ noch „immer scharf nach Neustart“. Die Erinnerung „niemand zuhause,
nicht scharf“ entfällt. **Von Hand** scharf schalten (Keypad, Karte, Tablet, Alexa) geht
weiterhin; „Bei Rückkehr“ funktioniert normal. Will die Automatik scharf schalten, kommt
die Nachricht „Gastmodus an – ‚Nacht‘ wurde nicht automatisch scharf geschaltet“.

**Einschalten:**

- **Alarm-Karte:** Knopf **👥 Gastmodus** → wie lange: schnell *bis ich ihn ausschalte*,
  *4 Stunden*, *bis morgen 10 Uhr* oder *3 Tage* – oder **frei**: unter „Oder bis:“ Datum und
  Uhrzeit wählen (vorgeschlagen ist morgen zur selben Stunde) und „Übernehmen“. Die Karte zeigt
  dann „Gastmodus an – bis …“ und den Knopf „Gastmodus beenden“. Jeder, der die Karte bedienen
  darf, kann ihn schalten – ohne PIN.
- **Schalter** `switch.hauswacht_gastmodus`: an/aus für **alle** Bereiche, bis zum Ausschalten.
- **Aktion** `hauswacht.guest_mode` – auch mit Ende-Zeitpunkt und für einzelne Bereiche:

```yaml
action: hauswacht.guest_mode
target:
  entity_id: alarm_control_panel.hauswacht   # oder alarm_control_panel.hauswacht_alle
data:
  "on": true
  until: "2026-11-20 12:00:00"   # weglassen = bis zum Ausschalten
```

**Bereiche:** Standard ist **alle Bereiche**. Eine Alarm-Karte mit `bereich: einliegerwohnung`
schaltet den Gastmodus nur für diesen Bereich – so kann die Einliegerwohnung Gäste haben, während
das Haus normal automatisch scharf wird.

**Beispiel mit freier Zeit:** Die Schwiegereltern bleiben bis Sonntag 18 Uhr. 👥 Gastmodus → Oder
bis: *Sonntag, 18:00* → Übernehmen.

**Beispiel:** Freitagabend kommt die Babysitterin. Auf dem Tablet: 👥 Gastmodus → *bis morgen
10 Uhr*. Die Eltern fahren los – Hauswacht schaltet nicht „Abwesend“, um 23 Uhr auch nicht
„Nacht“. Samstag um 10 Uhr endet der Gastmodus von selbst, die Automatik gilt wieder.

Ein- und Ausschalten stehen im Logbuch (Ereignis `GuestMode`) und kommen als Nachricht über das
Ereignis „Automatik“.

## Scharf durch Schließen der Tür

Im Profil, aufklappbar unter **„Scharf durch Schließen der Tür“**:

| Einstellung | Bedeutung |
|---|---|
| Scharf, sobald die Ausgangstür geschlossen ist | an/aus (Standard aus) |
| Ausgangstüren | z. B. Haustür vorne und hinten |
| Beruhigungszeit | so lange muss die Tür nach dem Schließen zu bleiben (Standard 5 s, 1–60 s) |

Ablauf: scharf schalten → Ausgangsverzögerung läuft → Tür auf, raus, Tür zu → nach der
Beruhigungszeit ist die Anlage scharf, ohne die volle Ausgangsverzögerung abzuwarten. Geht die
Tür in der Beruhigungszeit wieder auf, beginnt sie neu.

- Ist die Option an, dürfen die **Ausgangstüren beim Scharfschalten offen** sein. Andere offene
  Melder werden wie gewohnt geprüft.
- Sind die Ausgangstüren am Ende der Ausgangsverzögerung noch offen, gilt die normale Prüfung des
  Profils.

## Bereiche

**Systemeinstellungen → Bereiche.** Für Anlagen, deren Teile **unabhängig** scharf geschaltet
werden – z. B. Garage scharf, während im Haus jemand ist. Ohne weitere Bereiche ändert sich
nichts.

- Der **erste Bereich** (Standardname „Haus“) ist die Hauptanlage. Er lässt sich umbenennen,
  aber nicht löschen; seine Entitäts-IDs bleiben unverändert. Immer aktive Melder,
  Heimkehr-Beobachtung, Erinnerung „Alle weg“ und Sirenentest gehören zu ihm.
- **Jedes Alarmprofil gehört zu genau einem Bereich.** Die Bedienfeld-Knöpfe sind je Bereich
  frei: Haus und Garage dürfen beide einen Knopf „Abwesend“ haben.
- **Meldergruppen und Auslöseregeln** sind Bausteine für alle Bereiche. Ein Melder darf in
  mehreren Bereichen vorkommen; es lösen nur die Bereiche aus, die gerade scharf sind.
- Jeder weitere Bereich bekommt ein eigenes Gerät **„Hauswacht <Name>“** mit Bedienfeld
  (`alarm_control_panel.hauswacht_garage`), Profilauswahl und Knöpfen.
- **„Alle Bereiche“** (`alarm_control_panel.hauswacht_alle`): Ein Knopf schaltet jeden Bereich
  mit dem Profil, das dort diesem Knopf zugeordnet ist; Bereiche ohne ein solches Profil bleiben,
  wie sie sind. „Unscharf“ schaltet alle Bereiche unscharf (während eines Alarms: Alarm
  beenden). Scheitert ein Bereich (z. B. Fenster offen), werden die übrigen trotzdem geschaltet,
  und die Meldung nennt, was nicht ging. Angezeigt wird der wichtigste Zustand: Alarm >
  Eingangsverzögerung > Ausgangsverzögerung > alle unscharf > gemeinsamer scharfer Zustand;
  unterschiedlich scharf zeigt „Scharf (benutzerdefiniert)“, Details im Attribut `areas`.
- **Benutzer-Rechte** gelten wahlweise für alle Bereiche gleich oder je Bereich, siehe
  [Benutzer](benutzer.md#rechte).
- **Gemeinsam für alle Bereiche:** PIN-Sperre, Testmodus und Sirenen. Der Testmodus lässt sich
  nur umschalten, wenn alle Bereiche unscharf sind; eine Sirene, die zwei Bereiche gleichzeitig
  nutzen, bleibt an, bis beide ihren Alarm beendet haben.
- **Benachrichtigungen** tragen den Bereichsnamen im Titel, z. B. „Hauswacht: Alarm (Garage)“.
- Ein Bereich lässt sich nur löschen, wenn ihm kein Alarmprofil mehr gehört. Gerät und
  Entitäten verschwinden dann mit.
