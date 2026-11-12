# Alarmprofile und Bereiche

## Alarmprofile

**Alarmprofile → Alarmprofil anlegen.** Es gibt keine vorgegebenen Profile – du legst so viele
an, wie du brauchst, z. B. „Zuhause“, „Nacht“, „Abwesend“, „Urlaub“.

| Einstellung | Bedeutung |
|---|---|
| Name, Symbol | Wie das Profil in Auswahlliste, Meldungen und am Bedienfeld erscheint |
| Knopf am Bedienfeld | Optional: Zuhause, Nacht, Abwesend, Urlaub oder Benutzerdefiniert. Jeder Knopf gehört höchstens einem Profil (je Bereich) |
| Bereich | Nur bei mehreren [Bereichen](#bereiche) |
| Meldergruppen – jeder Melder löst allein aus | Jeder Melder dieser Gruppen löst für sich aus (Tür mit Eingangsverzögerung, Fenster sofort …) |
| Ausgenommene Melder | Melder dieser Gruppen, die in diesem Profil **nicht** einzeln auslösen (z. B. Bewegung Flur OG in „Nacht“); in Auslöseregeln zählen sie weiter |
| Auslöseregeln | Zusätzlich: Abfolgen von Meldern, siehe [Auslöseregeln](ausloeseregeln.md) |
| Ausgangs- / Eingangsverzögerung | Zeit zum Verlassen bzw. zum Unscharfschalten nach dem Betreten (Standard je 30 s) |
| Dauer der Alarmreaktion | Wie lange ein Alarmzyklus dauert (Standard 180 s) |
| Offene Sensoren beim Scharfschalten | verweigern · nach Bestätigung erlauben · automatisch überbrücken |
| Ausgefallene Sensoren beim Scharfschalten | verweigern · nach Bestätigung erlauben |
| Maximale Alarmzyklen | Wie oft nach einem Alarm erneut ausgelöst werden darf |
| Manipulation löst Alarm aus | Sonst wird Manipulation nur gemeldet |
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
| An diesen Tagen | Gilt für beide Uhrzeiten; leer = täglich |
| Scharf, wenn alle diese Personen weg sind | Sind alle gewählten Personen nicht zu Hause, wird nach der Wartezeit scharf geschaltet |
| Wartezeit | Standard 15 Minuten. Kommt in dieser Zeit jemand zurück, wird nichts geschaltet |
| Unscharf, wenn eine dieser Personen heimkommt | Nur wenn das Profil vorher **automatisch** scharf geschaltet wurde |

Sicherheitsregeln:

- Automatisch scharf nur, wenn die Anlage unscharf ist – nie über ein anderes Profil hinweg.
- Offene oder ausgefallene Melder werden automatisch **nie** bestätigt. Klappt das
  Scharfschalten deshalb nicht, kommt eine Systemmeldung.
- Ein laufender Alarm oder eine laufende Eingangsverzögerung wird nie automatisch beendet.
- Eine Person mit unbekanntem oder nicht verfügbarem Aufenthalt gilt **nicht** als weg.
- Nach einem Neustart ist die Anlage unscharf; die Anwesenheits-Automatik greift erst beim
  nächsten Wechsel einer Person.
- „Unscharf bei Rückkehr“: Wer das Handy einer der Personen hat, schaltet damit unscharf. Für
  „Abwesend“ oder „Urlaub“ gut überlegen. Wie zuverlässig das bei euch wäre, misst die
  [Heimkehr-Beobachtung](beobachtung.md).

Handys, die nur über das WLAN erkannt werden (Ping am Router), melden im Standby manchmal kurz
„weg“. Die Wartezeit fängt das ab.

Statt automatisch scharf zu schalten, kann Hauswacht auch nur erinnern: siehe
[Erinnerung „Alle weg“](benachrichtigungen.md#erinnerung-alle-weg-anlage-unscharf).

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
