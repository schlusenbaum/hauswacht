# Installation und Bedienung

> **Stand 0.27.0:** Alle Grundfunktionen sind enthalten. Die echte Sirenenansteuerung ist
> **standardmäßig gesperrt** und muss bewusst freigegeben werden.

## Voraussetzungen

- Home Assistant 2026.10 oder neuer
- HACS (nur für öffentliche Repositories) oder manuelle Installation

## Installation

**Über HACS:** Menü (⋮) → Benutzerdefinierte Repositories →
`https://github.com/schlusenbaum/hauswacht`, Typ **Integration** → Hauswacht herunterladen →
Home Assistant neu starten. HACS installiert die Datei `hauswacht.zip` aus dem jeweiligen
[Release](https://github.com/schlusenbaum/hauswacht/releases); Updates erscheinen in HACS,
sobald ein neues Release veröffentlicht ist.

**Manuell:** `hauswacht.zip` aus dem neuesten
[Release](https://github.com/schlusenbaum/hauswacht/releases) laden und nach
`/config/custom_components/hauswacht` entpacken, dann Home Assistant neu starten.

Danach: **Einstellungen → Geräte & Dienste → Integration hinzufügen → Hauswacht.**
Hauswacht kann nur einmal eingerichtet werden.

## Entitäten

| Entität | Zweck |
|---|---|
| `alarm_control_panel.hauswacht` | Bedienfeld mit den Knöpfen, denen ein Profil zugeordnet ist, und Unscharf |
| `select.hauswacht_profil` | Auswahl des Profils für die Knöpfe „Scharf schalten“ |
| `button.hauswacht_scharf_schalten` | Gewähltes Profil scharf schalten |
| `button.hauswacht_trotzdem_scharf_schalten` | Gewähltes Profil scharf schalten und offene Sensoren überbrücken |
| `switch.hauswacht_testmodus` | Testmodus (Name je nach Sprache der Instanz) |
| `sensor.hauswacht_systemstatus` | Systemstatus: OK · Sensoren ausgefallen · Störung |
| `binary_sensor.hauswacht_offene_sensoren` | „Offene Sensoren in den Meldergruppen“: „Offen“, sobald ein Sensor einer Meldergruppe offen ist (welche: Attribut `names`), sonst „Alles zu“ |
| `alarm_control_panel.hauswacht_<bereich>` | nur mit [Bereichen](#bereiche): Bedienfeld je weiterem Bereich, dazu `alarm_control_panel.hauswacht_alle` („Alle Bereiche“) |
| `sensor.hauswacht_simulierte_sensoren` | „Testkarte: simulierte Sensoren“ – Grundlage der Karte „Hauswacht Test“, standardmäßig ausgeblendet |

Eine fertige Bedienkarte steht in [docs/dashboard.md](dashboard.md).

## Einrichtung in drei Schritten

Alle Einstellungen liegen unter **Einstellungen → Geräte & Dienste → Hauswacht →
Konfigurieren** und lassen sich nur im **unscharfen** Zustand ändern. Das Menü:

| Menüpunkt | Inhalt |
|---|---|
| **Alarmauslösung** → Meldergruppen | Melder zusammenfassen, die zusammengehören (Türen, Fenster, Keller …) |
| **Alarmauslösung** → Auslöseregeln | Abfolgen von Meldern („Tür, dann Keller“) |
| **Alarmauslösung** → Immer aktiv | Melder, die auch unscharf auslösen |
| **Alarmauslösung** → Melder aus anderem Sensor erstellen | Assistent: Messwert → Schwellenwert-Helfer → Melder |
| Alarmprofile | Welche Meldergruppen allein auslösen, welche Auslöseregeln gelten, Verzögerungen, Reaktion |
| Alarmgeber – Sirenen | Welche Sirenen Hauswacht verwenden darf, Hardware-Freigabe, Sirenentest |
| Benachrichtigungen | Empfänger und Ereignisse |
| **Systemeinstellungen** → Benutzer und PINs (mit PIN-Regeln) | Personen, PINs, Rechte, Master-PIN |
| **Systemeinstellungen** → Funkstille von Sensoren | maximale Funkstille |
| **Systemeinstellungen** → Funknetz und Gateways überwachen | Zigbee2MQTT-Bridge, MQTT … |
| **Systemeinstellungen** → Heimkehr-Beobachtung | Auswertung, schaltet nichts |

Jede Änderung wird beim Bestätigen eines Formulars **sofort gespeichert**, danach geht es
zurück ins Menü („✅ Gespeichert“). Untermenüs haben **„← Zurück“**, das Hauptmenü
**„Fertig – schließen“**. Formulare selbst haben in Home Assistant keinen Zurück-Knopf: Wer
ein Formular ohne Änderung verlassen will, bestätigt es unverändert oder schließt den Dialog
(bereits Gespeichertes bleibt). Wird die Anlage scharf geschaltet, während der Dialog offen
ist, speichert Hauswacht nichts mehr.

### 1. Meldergruppen anlegen

**Alarmauslösung → Meldergruppen → Meldergruppe anlegen.**

Eine **Meldergruppe** ist eine Gruppe von Sensoren, die immer gemeinsam überwacht werden. Profile
schalten ganze Meldergruppen scharf, nicht einzelne Sensoren. Typisch:

| Meldergruppe | Sensoren | scharf in den Profilen |
|---|---|---|
| Außen | alle Tür- und Fensterkontakte, ihre Manipulationssensoren | Zuhause, Nacht, Abwesend |
| Innen / Keller | Bewegungs- und Präsenzmelder | Nacht (Keller), Abwesend |

- Nur Sensoren in einer Meldergruppe überwacht Hauswacht.
- **Jeder Sensor gehört zu genau einer Meldergruppe.** Ist ein Sensor schon in einer anderen Meldergruppe,
  lässt sich die Meldergruppe nicht speichern; die Meldung nennt Sensor und Meldergruppe.
- Wie ein Melder reagiert, legt sein **Typ** fest – nach dem Speichern der Gruppe zeigt Hauswacht
  alle Melder mit vorgeschlagenem Typ, siehe [Typen prüfen](#3-typen-prüfen).

Sensoren kommen auf zwei Wegen in eine Meldergruppe, beide lassen sich kombinieren:

- **Direkt auswählen:** Im Feld „Sensoren“ mehrere Melder anhaken.
- **Per Label (optional):** Ein Label wählen. Alle Melder, die dieses Label **direkt an
  der Entität** tragen, gehören dann automatisch dazu. Labels am Gerät zählen bewusst nicht,
  sonst kämen auch Batterie- oder Verbindungssensoren desselben Geräts mit in die Meldergruppe.

Welche Sensoren eine Meldergruppe am Ende umfasst, zeigt das Attribut `zones` am Bedienfeld.

#### Welche Melder gehen?

Nur Melder, die „offen/zu“ kennen:

| Art | gilt als offen/ausgelöst bei |
|---|---|
| Binärsensor (`binary_sensor`) | an |
| Schloss (`lock`) | entriegelt, öffnet, offen, blockiert |
| Abdeckung (`cover`, z. B. Garagentor) | offen, öffnet, schließt |

Alles andere wird über einen **Home-Assistant-Helfer** zum Binärsensor:

- **Messwerte** (Temperatur, Feuchte, Leistung …): mit dem Assistenten
  [Melder aus anderem Sensor erstellen](#melder-aus-anderem-sensor-erstellen) – er legt einen
  Schwellenwert-Helfer mit Hysterese an.
- **Kameras:** Die meisten Kamera-Integrationen liefern Bewegung, Person oder Fahrzeug bereits als
  Binärsensoren – die direkt nehmen.
- **Ereignisse** (z. B. Klingel, `event.…`): über einen Vorlagen-Binärsensor in YAML, der kurz
  „an“ ist:

```yaml
template:
  - trigger:
      - trigger: state
        entity_id: event.klingel
        not_from: unavailable
    binary_sensor:
      - name: Klingel gedrückt
        state: "on"
        auto_off: "00:00:05"
```

#### Melder aus anderem Sensor erstellen

**Alarmauslösung → Melder aus anderem Sensor erstellen.** Beispiel Frostwächter:

| Feld | Beispiel |
|---|---|
| Messwert | `sensor.temperatur_heizungskeller` |
| Name des neuen Melders | Frost Heizungskeller |
| Unterer Grenzwert | 5 (löst unter 5 °C aus) |
| Oberer Grenzwert | leer |
| Hysterese | 1 (wieder „normal“ erst ab 6 °C – kein ständiges Hin und Her) |
| Typ | Technik |
| Einsetzen in | Immer aktiv (oder eine Meldergruppe) |

Hauswacht legt damit einen **Schwellenwert-Helfer** in Home Assistant an
(`binary_sensor.frost_heizungskeller`, zu finden unter Einstellungen → Geräte & Dienste → Helfer,
dort änderbar und löschbar) und trägt ihn gleich mit Typ ein. Es wird nur ein neuer Helfer
angelegt – bestehende Helfer, Automationen oder Skripte bleiben unverändert.

### 2. Profile anlegen

**Alarmprofile → Alarmprofil anlegen.** Es gibt keine vorgegebenen Profile – du legst jedes selbst an,
so viele du brauchst. Pro Profil:

| Einstellung | Bedeutung |
|---|---|
| Name, Symbol | Wie das Profil in Auswahlliste, Meldungen und am Bedienfeld erscheint |
| Knopf am Bedienfeld | Optional: Zuhause, Nacht, Abwesend, Urlaub oder Benutzerdefiniert. Jeder Knopf gehört höchstens einem Profil |
| Meldergruppen – jeder Melder löst allein aus | Jeder Melder dieser Meldergruppen löst für sich aus (Tür mit Eingangsverzögerung, Fenster sofort …) |
| Ausgenommene Melder | Melder aus diesen Gruppen, die in diesem Profil **nicht** einzeln auslösen (z. B. Bewegung Flur OG in „Nacht“); in Auslöseregeln zählen sie weiter |
| Auslöseregeln | Zusätzlich: Abfolgen von Meldern, siehe [Auslöseregeln](#auslöseregeln) |
| Ausgangs- / Eingangsverzögerung | Zeit zum Verlassen bzw. zum Unscharfschalten nach dem Betreten (Standard je 30 s) |
| Dauer der Alarmreaktion | Wie lange ein Alarmzyklus dauert (Standard 180 s) |
| Offene Sensoren beim Scharfschalten | Verweigern · nach Bestätigung erlauben · automatisch überbrücken |
| Ausgefallene Sensoren beim Scharfschalten | Verweigern · nach Bestätigung erlauben |
| Maximale Alarmzyklen | Wie oft nach einem Alarm erneut ausgelöst werden darf |
| Manipulation löst Alarm aus | Sonst wird Manipulation nur gemeldet |
| Sirenen, Ton, Lautstärke, stiller Alarm | Reaktion bei Alarm (siehe [Sirenen](#sirenen)) |
| Benachrichtigen (Alarm) | Wer bei einem Alarm eine Push-Nachricht bekommt |

Oben im Formular steht, welche Melder in diesem Profil derzeit scharf werden; nach dem Speichern
zeigt das Menü die aktualisierte Liste.

Ein Profil ohne Meldergruppen und ohne Auslöseregeln lässt sich **nicht** scharf schalten. So entsteht nie der Eindruck,
das Haus sei geschützt, obwohl nichts überwacht wird.

### Auslöseregeln

**Konfigurieren → Alarmauslösung → Auslöseregeln.** Eine Auslöseregel löst erst bei einer **Abfolge**
von Meldern aus. Auslöseregeln stehen für sich; im Alarmprofil wählst du unter **Auslöseregeln**, welche
gelten. Dieselbe Auslöseregel kann in mehreren Profilen stecken.

**So ist eine Auslöseregel aufgebaut:**

```
Schritt 1 erfüllt ──(Zeit von Schritt 1)──▶ Schritt 2 erfüllt ──(Zeit von Schritt 2)──▶ … ──▶ Alarm
```

- Eine Auslöseregel besteht aus **Schritten**, die **nacheinander** passieren müssen. Schritt 2 zählt
  erst, wenn Schritt 1 erfüllt ist – und nur innerhalb der Zeit, die bei Schritt 1 steht.
  Melder von Schritt 2, die **vor** Schritt 1 auslösen, zählen nicht. So entsteht die
  Reihenfolge.
- In jedem Schritt wählst du Melder (Sensoren und/oder Meldergruppen – eine Meldergruppe heißt „irgendein Melder
  der Meldergruppe“) und legst fest, wann **dieser Schritt** erfüllt ist. Diese Einstellung gilt nur für
  diesen Schritt:

| Dieser Schritt ist erfüllt, wenn … | Beispiel mit „Tür vorne“ + „Tür hinten“ |
|---|---|
| **einer davon** auslöst (ODER) | eine der beiden Türen geht auf |
| **alle davon** auslösen, Reihenfolge egal (UND) | beide Türen gehen auf, egal welche zuerst |
| **mindestens N verschiedene** auslösen | z. B. mindestens 2 von 4 Kellermeldern |

- **Zeit bis zum nächsten Schritt:** Ab dem Moment, in dem der Schritt erfüllt ist, hat der
  nächste Schritt so viel Zeit. Verstreicht sie, verfällt alles; der nächste Schritt 1 beginnt
  von vorn. Jedes neue Auslösen eines Schritt-1-Melders startet die Zeit neu.
- Was in **beliebiger Reihenfolge** passieren darf, gehört in **einen** Schritt mit „alle davon“;
  eine **feste Reihenfolge** sind **mehrere** Schritte:

| Wunsch | So einstellen |
|---|---|
| erst Tür, dann Keller | Schritt 1: Tür · Schritt 2: Keller |
| Tür und Keller, Reihenfolge egal | Schritt 1: Tür + Keller, „alle davon“ |
| eine der Türen, dann Keller **und** Büro (egal welches zuerst) | Schritt 1: beide Türen, „einer davon“ · Schritt 2: Keller + Büro, „alle davon“ |

**Anlegen mit dem Assistenten:** Name und Ergebnis → Schritt 1 → Übersicht mit „Weiteren
Schritt hinzufügen“, „Schritt bearbeiten“, „Letzten Schritt entfernen“, „Fertig – speichern“
(bis zu 10 Schritte). Über jedem Schritt und in der Übersicht steht die Auslöseregel als Satz, z. B.
„eine(r) von Tür vorne / Tür hinten, dann innerhalb von 120 s Meldergruppe Keller → Eingangsverzögerung,
dann Alarm“. Gespeichert wird erst mit „Fertig – speichern“; Probleme stehen in der Übersicht.

Ergebnis einer erfüllten Auslöseregel: **sofort Alarm** oder **Eingangsverzögerung, dann Alarm**
(Zeit aus dem Alarmprofil – z. B. damit jemand, der heimkommt und gleich in den Keller geht,
noch unscharf schalten kann).

Beispiel Profil „Nacht“ (allein auslösend: nichts):

| Auslöseregel | Schritte | Ergebnis |
|---|---|---|
| Tür, dann Keller | Haustür → (120 s) → Keller-Melder | Eingangsverzögerung |
| Fenster, dann Keller | Fenster → (60 s) → Keller-Melder | sofort Alarm |

| Ablauf | Ergebnis |
|---|---|
| Tür auf, dann nach oben | kein Alarm |
| später in den Keller (zwei Melder reagieren) | kein Alarm |
| Tür auf, dann Keller | Eingangsverzögerung, dann Alarm |
| Fenster auf (lüften) | kein Alarm |
| Fenster auf, dann Keller | Alarm |
| erst Keller, dann Fenster auf | kein Alarm – die Reihenfolge zählt |

- **Auslöseregeln sind mit ODER verknüpft.** Eine Auslöseregel kann einen Alarm nur auslösen, nie den Alarm
  einer anderen Auslöseregel verhindern. Lösen zwei Auslöseregeln gleichzeitig aus, gilt das strengere
  Ergebnis (sofort Alarm).
- **Derselbe Melder zählt nicht doppelt:** „mindestens 2 verschiedene“ heißt zwei verschiedene
  Melder; ein Melder darf nicht in zwei aufeinanderfolgenden Schritten stehen.
- **Scharfschalten:** Melder, die im Profil nur in Auslöseregeln vorkommen, verhindern das
  Scharfschalten nicht. Ein offenes Fenster zählt erst, wenn es zu und wieder auf geht – wird
  es nachträglich geschlossen, beginnt das nächste Öffnen die Auslöseregel ganz normal. Ist beim
  Scharfschalten ein solcher Melder offen, kommt ein **Hinweis** (Benachrichtigung „Hinweis
  beim Scharfschalten“, standardmäßig an, und eine Meldung in Home Assistant): Bis zum Schließen
  ist er eine Lücke, z. B. kann jemand durch das offene Fenster einsteigen, ohne Schritt 1
  auszulösen. Das Attribut `open_rule_sensors` am Bedienfeld zeigt, welche es gerade sind.
- **Prüfung beim Speichern:** Auslöseregeln, die nie auslösen können, lassen sich nicht speichern.
  Hinweise erscheinen, wenn eine Auslöseregel in einem Profil nichts bewirkt – etwa weil ihr erster
  Melder dort schon allein auslöst oder weil eine kürzere Auslöseregel immer vorher auslöst.
- **Schwachstelle bewusst bedenken:** Wer keinen weiteren Schritt auslöst, bleibt unbemerkt
  (Tür auf, dann nur nach oben). Abhilfe: mehr Melder in den späteren Schritten.
- Manipulation wird immer gemeldet; Brandsperre, Testmodus und Sirenenfreigabe gelten für jede
  Auslöseregel. In der Testkarte siehst du, wie weit jede Auslöseregel des aktiven Profils ist.
- Unvollständige Auslöseregeln meldet Hauswacht auf Wunsch („Unbestätigte Auslösung“, „Melder löst
  häufig allein aus“ – beide standardmäßig aus).
- Die Meldergruppen-Option „zweiter Melder bestätigt“ aus 0.18.0 wurde beim Update automatisch zu
  einer Auslöseregel „Bestätigung <Meldergruppe>“ (Schritt: mindestens 2 verschiedene Melder der Meldergruppe).

#### Ausnahme „Nicht, wenn vorher …“

In der Übersicht des Assistenten: **„Nicht, wenn vorher … (Ausnahme)“**. Die Auslöseregel gilt
nicht, wenn einer der gewählten Melder in der angegebenen Zeit **vor Schritt 1** ausgelöst hat.
Beispiel: „Fenster, dann Keller“ mit Ausnahme „Flur-Bewegungsmelder, 300 s“ – wer schon drinnen
unterwegs war und dann ein Fenster öffnet, löst nichts aus. Die Ausnahme wirkt **nur auf diese
Auslöseregel**. Die Testkarte zeigt „gesperrt durch Ausnahme · 4:10“.

#### Expertenmodus (YAML)

**Auslöseregeln → „Neue Auslöseregel als YAML“** oder in der Übersicht **„Als YAML
bearbeiten“**. Auslöseregeln mit Verschachtelung oder Bedingungen öffnen beim Bearbeiten direkt
den YAML-Editor. Beim Speichern prüft Hauswacht die Regel und nennt Fehler mit Fundstelle.

```yaml
name: Einstieg durchs Fenster
result: alarm                 # alarm | entry_delay | notify (nur Benachrichtigung)
steps:
  - any: [group: Fenster]     # einer davon
    within: 60                # Zeit bis zum nächsten Schritt
  - any:                      # Keller ODER (Flur UND Büro)
      - group: Keller
      - all: [sensor: binary_sensor.bwm_flur, sensor: binary_sensor.tuer_buero]
unless:                       # nicht, wenn das in den 300 s vor Schritt 1 passiert ist
  any: [group: Flur]
  before: 300
conditions:                   # nur wenn alle erfüllt sind
  - time: {after: "22:00", before: "06:00"}
  - person: {entity: person.niklas, in: not_home}
```

| Baustein | Bedeutung |
|---|---|
| `sensor: binary_sensor.x` | dieser Melder |
| `group: Keller` | steht für **die einzelnen Melder** der Meldergruppe: `any` = irgendeiner, `all` = alle, `count` = N verschiedene |
| `any: [...]` / `all: [...]` / `count: N` + `of: [...]` | einer · alle (Reihenfolge egal) · mindestens N – beliebig verschachtelt |
| `within: 120` | Zeit bis zum nächsten Schritt (Sekunden) |
| `result:` | `alarm`, `entry_delay` (Eingangsverzögerung, dann Alarm) oder `notify` (nur Benachrichtigung) |
| `unless:` + `before:` | Ausnahme: nicht, wenn der Ausdruck in dieser Zeit vor Schritt 1 erfüllt war |
| `conditions:` | Liste; alle müssen erfüllt sein |

Bedingungen:

| Bedingung | Beispiel |
|---|---|
| Uhrzeit, Wochentage | `time: {after: "22:00", before: "06:00", weekdays: [mon, tue, wed, thu, fri]}` (auch über Mitternacht) |
| Person in Zone | `person: {entity: person.niklas, in: home}` – `home`, `not_home` oder `zone.schule` |
| Zustand | `state: {entity: input_boolean.urlaub, is: "on"}` (auch Liste: `is: [on, auto]`) |
| Zahlenwert | `numeric: {entity: sensor.temperatur, above: 5, below: 30}` – optional `attribute: temperature` |
| Logik | `and: [...]`, `or: [...]`, `not: {...}` |

**Sichere Seite:** Lässt sich eine Bedingung nicht auswerten (Entität fehlt, ist nicht verfügbar,
liefert keine Zahl), gilt sie als **erfüllt** – im Zweifel löst die Regel aus. Bedingungen werden
erst geprüft, wenn alle Schritte passiert sind; ein ausgefallener Sensor löst also nie selbst
etwas aus, er kann nur keinen Alarm mehr verhindern.

Soll eine Bedingung im Zweifel **keinen** Alarm erlauben, ergänze `if_unknown: not_met`:

```yaml
conditions:
  - numeric: {entity: sensor.temperatur_wohnzimmer, below: 30}
    if_unknown: not_met      # Sensor ausgefallen = Bedingung nicht erfüllt = kein Alarm
```

`if_unknown` geht an jeder Bedingung, auch an `and`/`or`/`not`. Vorsicht: Mit `not_met` legt ein
ausgefallener Sensor die Regel still. Bedingungen,
Ausnahmen und Ergebnis wirken nur auf die eigene Auslöseregel; andere Auslöseregeln und allein
auslösende Meldergruppen bleiben unberührt.

**Bedienen:** Profile mit Knopf über das Bedienfeld; jedes Profil – auch ohne Knopf – über die
Auswahlliste **Profil** und den Knopf **Scharf schalten**, oder per Aktion
`hauswacht.arm` mit dem Profilnamen. Profile ohne eigenen Knopf zeigt das Bedienfeld im
scharfen Zustand als „benutzerdefiniert“; das Attribut `profile_name` nennt das Profil.

### Automatik

Im Profil gibt es den aufklappbaren Bereich **Automatik**. Alle Felder sind optional – leer
heißt: diese Automatik ist aus.

| Einstellung | Wirkung |
|---|---|
| Scharf um / Unscharf um | Uhrzeit, zu der das Profil scharf bzw. unscharf geschaltet wird |
| An diesen Tagen | Gilt für beide Uhrzeiten; leer = täglich |
| Scharf, wenn alle diese Personen weg sind | Sind alle gewählten Personen nicht zu Hause, wird nach der Wartezeit scharf geschaltet |
| Wartezeit | Standard 15 Minuten. Kommt in dieser Zeit jemand zurück, wird nichts geschaltet |
| Unscharf, wenn eine dieser Personen heimkommt | Nur wenn das Profil vorher **automatisch** scharf geschaltet wurde |

Sicherheitsregeln:

- Automatisch scharf geschaltet wird nur, wenn die Anlage unscharf ist – nie über ein anderes
  Profil hinweg.
- Offene oder ausgefallene Sensoren werden automatisch **nie** bestätigt. Klappt das
  Scharfschalten deshalb nicht, kommt eine Systemmeldung.
- Ein laufender Alarm oder eine laufende Eingangsverzögerung wird nie automatisch beendet.
- Eine Person mit unbekanntem oder nicht verfügbarem Aufenthalt gilt **nicht** als weg.
- Nach einem Neustart ist die Anlage unscharf; die Anwesenheits-Automatik greift erst beim
  nächsten Wechsel einer Person.
- Hinweis zu „Unscharf bei Rückkehr“: Wer das Handy einer der Personen hat, schaltet damit
  unscharf. Für „Abwesend“ oder „Urlaub“ deshalb gut überlegen.

Handys, die nur über das WLAN erkannt werden (Ping am Router), melden im Standby manchmal kurz
„weg“. Die Wartezeit fängt das ab.

### 3. Typen prüfen

Der **Typ** legt fest, *wie* ein Melder reagiert; *wann* er scharf ist, legen Meldergruppe und
Alarmprofil fest. Nach dem Speichern einer Meldergruppe zeigt Hauswacht alle ihre Melder mit dem
vorgeschlagenen Typ – meist passt er, sonst direkt dort ändern.

| Typ | Vorschlag bei | Verhalten |
|---|---|---|
| Tür | Tür, Garagentor, Öffnung, Schloss, Tor | Startet die Eingangsverzögerung; kann Ausgangstür für „Scharf durch Schließen“ sein |
| Fenster | Fenster | Sofortiger Alarm |
| Bewegung | Bewegung, Anwesenheit, Präsenz | Wartet, wenn gerade eine Eingangsverzögerung läuft, sonst sofortiger Alarm |
| Manipulation | Manipulation | Wird immer gemeldet, auch unscharf |
| Technik (Wasser, Gas, Frost …) | Feuchte, Gas, Kälte, Hitze, Kohlenmonoxid | Immer aktiv, auch unscharf; nie Teil der Scharfschaltung, kein Einbruchalarm – standardmäßig nur Benachrichtigung (siehe [Immer aktive Melder](#immer-aktive-melder)) |
| Sonstiges | alles andere (z. B. Vibration, Rollladen) | Sicherheitshalber sofortiger Alarm |

Beispiel: Ein Fenster, durch das man das Haus betritt, bekommt den Typ **Tür**. Rauchmelder
schlägt Hauswacht bewusst nicht als „Technik“ vor – Brandschutz bleibt Sache der Rauchmelder.

## Immer aktive Melder

**Alarmauslösung → Immer aktiv.** Melder, die **auch im unscharfen Zustand** auslösen – z. B.
Tresor, Waffenschrank, Gartenhaus, Panikknopf. Meldergruppen und/oder einzelne Sensoren.

| Zustand | Reaktion |
|---|---|
| unscharf (Standard) | nur eine **wichtige Benachrichtigung** (durchbricht „Nicht stören“, Ereignis „Immer aktiver Melder“) und eine Meldung in Home Assistant – kein Alarm, keine Sirene |
| unscharf mit „Sirenen verwenden“ | Alarm mit den hier gewählten Sirenen, Ton und Dauer; die Anlage zeigt „Alarm“ (Profil „Immer aktiv“). **„Alarm beenden“ führt zurück nach unscharf.** |
| scharf | sofortiger Alarm mit der Reaktion des aktiven Alarmprofils |

Hardware-Freigabe, Testmodus und Brandsperre gelten wie immer. In der Testkarte tragen diese
Melder den Hinweis „immer aktiv“.

Melder vom Typ **Technik** in einer Meldergruppe sind automatisch immer aktiv. Anders als oben
lösen sie auch im scharfen Zustand **keinen Einbruchalarm** aus, sondern nur die Benachrichtigung
(bzw. mit „Sirenen verwenden“ den Alarm „Immer aktiv“). Sie blockieren das Scharfschalten nicht.

## Bereiche

**Systemeinstellungen → Bereiche.** Für Anlagen, deren Teile **unabhängig** scharf geschaltet
werden – z. B. Garage oder Gartenhaus scharf, während im Haus jemand ist. Die Namen sind frei
wählbar; ohne weitere Bereiche ändert sich nichts.

- Der **erste Bereich** (Standardname „Haus“) ist die bisherige Anlage. Er lässt sich umbenennen,
  aber nicht löschen; seine Entitäts-IDs bleiben unverändert. Immer aktive Melder,
  Heimkehr-Beobachtung und die Erinnerung „Alle weg“ gehören zu ihm.
- **Jedes Alarmprofil gehört zu genau einem Bereich** (Feld „Bereich“ im Alarmprofil, sobald es
  zwei Bereiche gibt). Die Bedienfeld-Knöpfe sind je Bereich frei: Haus und Garage dürfen beide
  einen Knopf „Abwesend“ haben.
- **Meldergruppen und Auslöseregeln** sind Bausteine für alle Bereiche. Ein Melder darf in
  mehreren Bereichen vorkommen; es lösen nur die Bereiche aus, die gerade scharf sind.
- Jeder weitere Bereich bekommt ein eigenes Gerät **„Hauswacht <Name>“** mit Bedienfeld
  (`alarm_control_panel.hauswacht_garage`), Profilauswahl, Knöpfen „Scharf schalten“,
  „Trotzdem scharf schalten“, „Unscharf schalten“, „Alarm beenden“ und „Offene Sensoren“.
- **„Alle Bereiche“** (`alarm_control_panel.hauswacht_alle`): Ein Knopf schaltet jeden Bereich
  mit dem Profil, das dort diesem Knopf zugeordnet ist; Bereiche ohne ein solches Profil bleiben,
  wie sie sind. „Unscharf“ schaltet alle Bereiche unscharf (während eines Alarms: Alarm beenden).
  Scheitert ein Bereich (z. B. Fenster offen), werden die übrigen trotzdem geschaltet, und die
  Meldung nennt, was nicht ging. Zustand: Alarm > Eingangsverzögerung > Ausgangsverzögerung >
  unscharf (alle) > gemeinsamer scharfer Zustand; teilweise oder unterschiedlich scharf zeigt
  „Scharf (benutzerdefiniert)“, Details im Attribut `areas`.
- **Benutzer** lassen sich auf Bereiche beschränken (Feld „Bereiche“, leer = alle).
- **PIN-Sperre, Testmodus und Sirenen** gelten gemeinsam: Der Testmodus lässt sich nur umschalten,
  wenn alle Bereiche unscharf sind; eine Sirene, die zwei Bereiche gleichzeitig nutzen, bleibt an,
  bis beide ihren Alarm beendet haben.
- **Benachrichtigungen** tragen den Bereichsnamen im Titel, z. B. „Hauswacht: Alarm (Garage)“.
- Einstellungen lassen sich nur ändern, wenn **alle** Bereiche unscharf sind.
- Ein Bereich lässt sich nur löschen, wenn ihm kein Alarmprofil mehr gehört.

## Scharf durch Schließen der Tür

Im Alarmprofil unter **„Scharf durch Schließen der Tür“** (aufklappbar, optional):

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
  Profils (z. B. Scharfschaltung abgebrochen).
- Ohne die Option ändert sich nichts.

## Funkstille von Sensoren

**Systemeinstellungen → Funkstille von Sensoren.**


- Ein Sensor ist **nicht verfügbar**, wenn er fehlt oder `unavailable` bzw. `unknown` meldet.
- Optional gilt ein Sensor auch dann als
  ausgefallen, wenn er sich so viele Stunden nicht gemeldet hat. Batteriesensoren melden sich
  teils nur alle paar Stunden, der Wert sollte deshalb großzügig sein. Standard: aus.
- Als „letzter Kontakt“ zählt der „Zuletzt gesehen“-Sensor desselben Geräts (bei Zigbee2MQTT
  `sensor.<gerät>_last_seen`), falls vorhanden und aktiviert. Sonst nimmt Hauswacht den
  Zeitpunkt der letzten Aktualisierung in Home Assistant – der wird allerdings bei jedem
  Neustart erneuert. Das Attribut `last_contact` zeigt den Wert je Sensor.
- Fällt ein überwachter Sensor im scharfen Zustand aus, erscheint ein Hinweis
  „Hauswacht: Sensor ausgefallen“ und ein Ereignis `SensorUnavailable`.
- Die überwachten Sensoren werden beim Scharfschalten festgehalten. Wird während des scharfen
  Zustands ein Label entfernt, bleibt der Sensor bis zum Unscharfschalten überwacht.

### Funkstille-Beobachtung: der richtige Wert aus euren Daten

Hauswacht merkt sich je Melder die **längste Pause zwischen zwei Lebenszeichen** (geprüft
jede Minute, über Neustarts hinweg gespeichert; Pausen über einen Neustart zählen nicht). Im
Formular „Funkstille von Sensoren“ steht dann z. B.:

> Beobachtet seit 14 Tagen. Längste Pause: Türkontakt vorne 1 h 52 min. **Empfehlung: 3 h.**

Die Empfehlung ist die längste Pause mal 1,5, auf volle Stunden aufgerundet – frühestens nach
3 Tagen Beobachtung. Den Wert trägst du selbst ein; die Beobachtung ändert nichts. Der
Diagnose-Sensor **„Funkstille-Beobachtung“** zeigt die Empfehlung und je Melder die längste
Pause.

## Funknetz und Gateways überwachen

Unter **Konfigurieren → Systemeinstellungen → Funknetz und Gateways überwachen** wählst du
Binärsensoren, die melden, ob ein Funknetz oder Gateway läuft. Fällt so ein System aus, können
alle Sensoren dahinter nichts mehr melden. Bei Sensoren der Geräteklasse „Problem“ bedeutet „an“ Störung, bei allen
anderen (z. B. „Verbindung“) bedeutet „an“ in Ordnung. Für Zigbee2MQTT ist das
`binary_sensor.zigbee2mqtt_bridge_connection_state`. Fällt MQTT aus, wird dieser Sensor
ebenfalls „nicht verfügbar“, deckt also beides ab.

- Ist ein Indikator aus oder nicht verfügbar, zeigt der Systemstatus **Störung**.
- Scharfschalten wird dann wie bei ausgefallenen Sensoren behandelt (je nach Profil
  verweigert oder nach Bestätigung erlaubt).
- Fällt ein System im scharfen Zustand aus, erscheint der Hinweis „Hauswacht: Störung“.
  Die Anlage bleibt scharf.
- Kommen die Sensoren nach einem Ausfall geschlossen zurück, gibt es keinen Alarm. Kommt ein
  Sensor offen zurück, löst er aus – ein verpasstes Öffnen wird so nachgeholt.

## Sirenen

**Konfigurieren → Alarmgeber – Sirenen.**

> Getestet ist bisher nur der Rauchwarnmelder Develco SMSZB-120 über Zigbee2MQTT. Andere
> Sirenen werden nach ihren Fähigkeiten angesteuert, siehe
> [README](../README.md#geräte-und-kompatibilität).

1. Sirenen auswählen, die Hauswacht für Einbruchalarme verwenden darf.
2. In jedem Profil festlegen, welche dieser Sirenen ertönen, mit welchem Ton und welcher
   Lautstärke – oder „Stiller Alarm“ für nur Benachrichtigungen.
3. Erst wenn alles getestet ist: **„Echte Sirenenansteuerung erlauben“** einschalten und die
   Bestätigung anhaken. Ohne diese Freigabe sendet Hauswacht nie einen Sirenenbefehl.

Die Laufzeit entspricht der „Dauer der Alarmreaktion“ des Profils. Danach – und beim
Beenden des Alarms – schaltet Hauswacht die Sirenen aus, die es selbst eingeschaltet hat. Das ist
für Sirenen wichtig, die nur Ein und Aus kennen. Sirenen mit eigener Laufzeit (z. B. Rauchmelder
mit Höchstdauer) bekommen die Dauer zusätzlich mitgeschickt, höchstens aber die Höchstdauer
des Geräts. Diese Höchstdauer wird nur gelesen, nie verändert.

### Sirenentest

**Alarmgeber – Sirenen → Sirenentest (echte Sirene!).** Prüft jede Sirene einzeln, kurz und
leise – über denselben sicheren Weg wie ein echter Alarm.

1. Sirenen wählen (mehrere werden **nacheinander** getestet), Ton (nur Einbruchtöne),
   Lautstärke (Standard **leise**) und Dauer (Standard **3 s**, höchstens **10 s**); anhaken
   „Ich bin vor Ort, Mitbewohner sind informiert“.
2. Für jede Sirene fragt Hauswacht „Sirene … testen?“ und zeigt eine **Vorabprüfung ohne Ton**:
   was gesendet würde (Ton, Lautstärke, Dauer) oder warum es nicht geht. Antwort: testen,
   überspringen oder beenden.
3. Nach dem Ton: „Hast du die Sirene gehört?“ – das Ergebnis wird mit Datum gespeichert
   (Diagnose-Sensor „Letzter Sirenentest“, je Sirene in den Attributen).

Voraussetzungen – der Sirenen-Guard prüft sie wie bei einem Alarm, ohne Ausnahme:

- alle Bereiche **unscharf**, kein Alarm
- **Hardware-Freigabe an**
- **Testmodus aus** – der Testmodus sperrt Sirenen grundsätzlich; der Sirenentest ist bewusst
  kein Testmodus, sondern ein echtes, kurzes Einschalten
- **keine Brandsperre** (kein Rauchmelder aktiv oder unklar), nur Einbruchtöne
- Sirene ist für Einbruch freigegeben und kann begrenzt werden

Die Dauer wird dreifach begrenzt: als Dauer an das Gerät (wenn es das kann), durch einen eigenen
Ausschaltbefehl nach Ablauf und durch die feste Obergrenze von 10 s. Während des Tests ist
**Scharfschalten gesperrt**; **Unscharf schalten** bricht den Test ab. Bei Brand greift Hauswacht
nicht ein – dann gilt die Brandsperre.

**Alarmgeber – Sirenen → Sirenentest – Erinnerung und Vorwarnung:**

| Einstellung | Bedeutung |
|---|---|
| Erinnerung | aus, alle 3 oder 6 Monate, jährlich: meldet „Sirenentest fällig“ (höchstens einmal pro Woche), wenn eine Sirene so lange nicht erfolgreich getestet wurde |
| Vorwarnung vor dem Test | schickt vor dem ersten Ton „Sirenentest … in 10 Sekunden“ an die allgemeinen Empfänger |

Dasselbe als Aktionen (nur für Administratoren): `hauswacht.siren_test` (Felder `siren`,
`duration`, `volume`, `tone`), `hauswacht.siren_test_result` (`siren`, `heard`) und
`hauswacht.siren_test_stop`. In der Testkarte gibt es den Sirenentest eingeklappt mit
Sicherheitsabfrage, siehe [Karte „Hauswacht Test“](#karte-hauswacht-test).

### Brandschutz

Sind die Sirenen zugleich Rauchmelder, erkennt Hauswacht deren Rauch- und
Testknopf-Sensoren automatisch.

- Meldet **irgendein** Rauchmelder in Home Assistant Brand, schaltet Hauswacht keine Sirene
  ein und keine aus.
- Ist der Brandzustand einer **registrierten** Sirene unklar (Sensor nicht verfügbar oder
  deaktiviert), gilt dasselbe.
- Wurde während eines Einbruchalarms Brand gemeldet, schaltet auch das Unscharfschalten keine
  Sirene ab. Sirenen mit eigener Laufzeit verstummen nach ihrer Höchstdauer. Alle anderen
  schaltet Hauswacht aus, sobald kein Brand mehr gemeldet wird (Prüfung jede Minute).
- Fremde Abschalt-Skripte (z. B. „alle Rauchmelder aus“) verwendet Hauswacht nie.

Das Attribut `last_siren_decision` am Bedienfeld zeigt nach jedem Alarm, welche Sirenen
angesteuert und welche aus welchem Grund gesperrt wurden.

## Benachrichtigungen

**Konfigurieren → Benachrichtigungen** mit den Punkten „Empfänger und Ereignisse“, „Eigene
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

### Eigene Texte und Platzhalter

**Benachrichtigungen → Eigene Texte für Push-Nachrichten:** Titel und Text je Ereignis selbst
formulieren; leer = Standardtext. Dieselben Platzhalter gelten für die Sprachausgabe:

| Platzhalter | Inhalt |
|---|---|
| `{bereich}` | Bereichsname (leer bei nur einem Bereich) |
| `{profil}` | Alarmprofil |
| `{melder}` | auslösender Melder mit Raum |
| `{offen}` | offene Melder |
| `{wer}` | wer geschaltet hat |
| `{sekunden}` | Eingangsverzögerung in Sekunden |
| `{uhrzeit}` | aktuelle Uhrzeit |
| `{regel}` | Auslöseregel |
| `{grund}` | Grund, z. B. warum das Scharfschalten scheiterte |
| `{text}` | der Standardtext von Hauswacht (im Titel: der Standardtitel) |

Beispiel: `Einbruch {bereich}: {melder} ({profil}, {uhrzeit})`. Unbekannte Platzhalter oder
Klammerfehler lassen sich nicht speichern; nach dem Speichern zeigt das Menü eine Vorschau mit
Beispielwerten. Nicht vorhandene Werte bleiben leer. Die Knöpfe in Push-Nachrichten bleiben
unverändert.

### Sprachausgabe (Lautsprecher)

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

### Scharfschaltung abgelehnt: „Trotzdem scharf“ / „Erneut versuchen“

Wird das Scharfschalten abgelehnt (z. B. Fenster offen), kommt eine Benachrichtigung mit dem
Grund und den Knöpfen:

- **„Trotzdem scharf“** – nur wenn das Profil offene Sensoren nach Rückfrage überbrücken darf
  („Offene Sensoren beim Scharfschalten: Nach Bestätigung erlauben“). Offene Sensoren werden bis zum Schließen überbrückt.
- **„Erneut versuchen“** – prüft noch einmal (z. B. nachdem das Fenster zu ist). Klappt es
  wieder nicht, kommt eine neue Benachrichtigung.

Die Knöpfe gelten 15 Minuten und je einmal, brauchen einen angemeldeten Home-Assistant-Benutzer
mit dem Recht „Scharf schalten“ und wirken nur, wenn die Anlage noch unscharf ist.

### Erinnerung „Alle weg, Anlage unscharf“

**Konfigurieren → Benachrichtigungen → Erinnerung „Alle weg“:** Personen, Profil, Wartezeit.

Sind alle gewählten Personen weg und die Anlage ist unscharf, kommt nach der Wartezeit
**einmal** eine Erinnerung mit dem Knopf **„Jetzt scharf (Profil)“**. Hauswacht schaltet
dabei **nichts selbst** – die sichere Alternative zum automatischen Scharfschalten.
Unbekannter Aufenthalt zählt nicht als weg. Kommt jemand heim, beginnt alles von vorn. Der
Knopf gilt 2 Stunden.

### Push-Knopf „Unscharf schalten“

**Konfigurieren → Benachrichtigungen → „Knopf ‚Unscharf schalten‘ / ‚Alarm beenden‘ in Benachrichtigungen“.**

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

## Alarm beenden

**„Unscharf schalten“ während eines Alarms beendet nur den Alarm** – egal ob über die Karte,
das Bedienfeld, die Push-Nachricht oder eine Automation:

- Sirenen aus (Brandsperre gilt), Anzeige wieder „Scharf“ mit demselben Profil.
- Was in diesem Moment offen ist (z. B. die Tür, durch die jemand kam), wird **überbrückt, bis
  es wieder geschlossen ist**, und danach automatisch wieder überwacht. Alle anderen Sensoren
  bleiben scharf.
- Benachrichtigung „Alarm beendet … bleibt scharf. Bis zum Schließen nicht überwacht: …“.
- **Erst ein zweites „Unscharf schalten“ schaltet die Anlage wirklich unscharf.**
- Ist ein PIN eingestellt, wird er auch zum Beenden des Alarms abgefragt.
- In der Push-Nachricht heißt der Knopf während eines Alarms **„Alarm beenden“**.

Für Dashboards gibt es zusätzlich zwei Knöpfe (Entitäten):

| Knopf | Wirkung |
|---|---|
| **Unscharf schalten** (`button.hauswacht_unscharf_schalten`) | Sofort unscharf – auch während eines Alarms, ohne Zwischenschritt |
| **Alarm beenden** (`button.hauswacht_alarm_beenden`) | Nur während eines Alarms: Alarm aus, Profil bleibt scharf; sonst ohne Wirkung |

Knöpfe können keinen PIN abfragen. Ist ein PIN eingestellt, ist „Unscharf schalten“ **nicht
verfügbar** – dann über das Bedienfeld bedienen. „Alarm beenden“ bleibt mit PIN verfügbar, wenn
unter **Konfigurieren → Systemeinstellungen → Benutzer und PINs → PIN-Regeln** die Option **„Alarm ohne PIN beenden“** an ist (standardmäßig aus).

> Abwägung: Mit der Option kann jeder, der ein entsperrtes Dashboard in der Hand hat, die
> Sirenen abstellen. Die Anlage bleibt aber scharf, die Alarm-Nachricht ist schon verschickt,
> und jeder weitere Melder löst sofort wieder aus. Der Melder, der ausgelöst hat, bleibt bis zum
> Schließen überbrückt.

## Profil-Einstellungen im Dashboard

Kleinigkeiten lassen sich ohne die Integration ändern. Die Entitäten stehen am Gerät
„Hauswacht“ unter **Konfiguration** und können auf ein Dashboard gelegt werden:

1. **Profil bearbeiten** (`select.hauswacht_profil_bearbeiten`): welches Profil die
   folgenden Einstellungen zeigen und ändern.
2. Zahlen: Ausgangs- und Eingangsverzögerung, Dauer der Alarmreaktion, Alarmzyklen,
   Wartezeit bei Abwesenheit.
3. Auswahl: Verhalten bei offenen bzw. ausgefallenen Sensoren, Sirenenton, Lautstärke.
4. Schalter: Stiller Alarm, Sabotage löst Alarm aus, Unscharf beim Heimkommen.
5. Uhrzeiten: Automatisch scharf um / unscharf um.

- Änderungen sind **nur im unscharfen Zustand** möglich; im scharfen Zustand sind die
  Einstellungen „nicht verfügbar“.
- Jede Änderung wird sofort gespeichert und im Logbuch mit Benutzer festgehalten.
- Name, Symbol, Bedienfeld-Knopf, Meldergruppen, Sirenen, Benachrichtigungsziele, Personen und
  Wochentage sowie das **Entfernen** einer Uhrzeit gehen nur in der Integration.
- Tipp: Eine Dashboard-Seite dafür nur für Administratoren sichtbar machen.

### Karte „Hauswacht Einstellungen“

Hauswacht bringt eine fertige Karte mit allen diesen Einstellungen mit. Sie wird automatisch
geladen – kein Eintrag unter „Ressourcen“ nötig.

Dashboard bearbeiten → **Karte hinzufügen** → **„Hauswacht Einstellungen“** – oder in YAML:

```yaml
type: custom:hauswacht-einstellungen-card
title: Einstellungen   # optional
```

Die Karte findet die Einstellungs-Entitäten selbst; umbenannte Entitäten stören nicht. Im
scharfen Zustand sind alle Einstellungen gesperrt. Nach einem Update von Hauswacht ggf. die
Seite neu laden (in der App: Einstellungen → Frontend-Cache zurücksetzen).

## Heimkehr-Beobachtung

**Konfigurieren → Systemeinstellungen → Heimkehr-Beobachtung.** Personen auswählen und „Heimkehr beobachten“
einschalten.

Hauswacht zeichnet dann auf, wann eine **Eingangstür** (Sensoren mit der Rolle „entry“)
geöffnet wird und wann eine Person als **heimgekommen** erkannt wird – für die Person insgesamt
und für jede ihrer Ortungsquellen einzeln (z. B. Router, App, iCloud). Daraus berechnet
Hauswacht, wie eine automatische Heimkehr bei euch funktionieren würde.

> Die Beobachtung **schaltet nichts**: kein Unscharf, kein Alarm, keine Benachrichtigung.
> Ein Test stellt sicher, dass dieser Teil des Codes keine Aktionen aufrufen kann.

Ausgewertet wird jede Heimkehr nach mindestens 5 Minuten Abwesenheit:

| Wert | Bedeutung |
|---|---|
| mit Tür | Innerhalb von 5 Minuten wurde eine Eingangstür geöffnet |
| ohne Tür | Keine Türöffnung – meist eine Falschmeldung der Ortung |
| Verzögerung | Sekunden zwischen Türöffnung und erkannter Heimkehr (negativ = vorher erkannt) |
| Fehlalarme bei X s | So oft wäre die Heimkehr erst nach einer Eingangsverzögerung von X Sekunden erkannt worden |

- **Sensor „Heimkehr-Beobachtung“**: Anzahl ausgewerteter Heimkehrten; die Zahlen pro Quelle
  stehen im Attribut `sources`, die letzten zehn Heimkehrten im Attribut `recent`, die Zeiten
  „Tür auf bis unscharf“ im Attribut `entry_times`.
- **Knopf „Heimkehr-Bericht“**: erstellt eine Übersicht als Benachrichtigung in Home Assistant.
- Gespeichert werden nur Zeitpunkte, höchstens 60 Tage lang.

Nach zwei bis vier Wochen zeigt der Bericht, ob eine Heimkehr-Automatik bei euch zuverlässig
wäre, für welche Personen und Ortungsquellen, und mit welcher Eingangsverzögerung.

### Zusätzliche Signale je Person

Im zweiten Schritt des Formulars wählst du je Person weitere Signale. Je früher und
zuverlässiger ein Signal, desto besser:

| Signal | Woher | gilt als „zuhause“ |
|---|---|---|
| WLAN-Sensor | Companion App: Android „WLAN-Verbindung“ (`sensor.<handy>_wifi_connection`, unter Einstellungen → Companion App → Sensoren verwalten aktivieren), iPhone „SSID“ (`sensor.<handy>_ssid`, Standort „Immer“ + „Genauer Standort“) | verbunden mit einem der **Heim-WLANs** (Feld im ersten Schritt, durch Komma getrennt) |
| Bluetooth | z. B. Bermuda mit dem BLE-Sender der Android-App | `device_tracker` = zuhause |
| Router | z. B. FRITZ!Box Tools (ohne App, aber träge) | `device_tracker` = zuhause |
| Annäherung | Integration **„Nähe“** (Einstellungen → Geräte & Dienste → Integration hinzufügen → Nähe; Zone Zuhause, Personen): Sensor `sensor.<nähe>_<person>_direction_of_travel` | nähert sich oder angekommen; Fenster 15 min statt 5 min, weil die Annäherung oft Minuten vor der Tür kommt |
| Binärsensor | beliebig | an |

Zusätzlich wertet Hauswacht je Person das **„frühestes Signal“** aus: zuhause, sobald
irgendeine Quelle zuhause meldet. So siehst du, ob eine ODER-Kombination früh genug wäre –
eine UND-Kombination (zwei Belege) wäre sicherer, aber langsamer.

### Tür auf bis unscharf

Läuft eine Eingangsverzögerung, misst Hauswacht, wie lange es bis zum Unscharfschalten dauert
(oder ob es zu spät war). Je Tür: Anzahl, rechtzeitig, zu spät, typische und längste Zeit und
eine **Empfehlung für die Eingangsverzögerung** (längste Zeit plus 25 %, mindestens 5 s, auf
5 s aufgerundet). Hilfreich z. B., um den Platz für ein Bedienteil an der Wand zu prüfen.

## Testmodus und Simulation

Im **Testmodus** laufen alle Abläufe wie im Ernstfall, Alarme sind aber als Testalarm
gekennzeichnet. Sirenen werden im Testmodus **nie** angesteuert – auch nicht bei
freigegebener Hardware. Benachrichtigungen nur, wenn ausdrücklich erlaubt.

Mit der Aktion **`hauswacht.simulate_trigger`** kannst du einen Sensor virtuell auslösen, ohne
eine Tür oder ein Fenster zu öffnen. Das geht nur bei eingeschaltetem Testmodus:

```yaml
action: hauswacht.simulate_trigger
target:
  entity_id: alarm_control_panel.hauswacht
data:
  sensor: binary_sensor.turkontakt_vorne_contact
```

Die Simulation verhält sich genau wie eine echte Auslösung: Eine Tür startet die
Eingangsverzögerung, ein Fenster löst sofort aus, ein Sensor außerhalb des aktiven Profils wird
ignoriert. Der echte Sensorzustand bleibt unverändert.

### Karte „Hauswacht Test“

Zum bequemen Durchspielen: Dashboard bearbeiten → **Karte hinzufügen** → **„Hauswacht Test“**
– oder in YAML:

```yaml
type: custom:hauswacht-test-card
title: Test   # optional
```

Die Karte zeigt **alle Sensoren aus den Hauswacht-Zonen** mit Raum, echtem Zustand und Knöpfen:

| Sensorart | Knöpfe |
|---|---|
| Tür, Fenster, Öffnung, Garagentor | **Auf** / **Zu** |
| Bewegung, Präsenz, Belegung | **Bewegung** / **Ruhe** |
| Manipulation (Sabotage) | **Manipulation** / **OK** |
| alle | **Weg** (nicht verfügbar), **Echt** (zurück auf den echten Wert) |

Oben schaltest du den Testmodus ein und aus; **„Alle echt“** setzt alle Sensoren zurück.

Oben zeigt die Karte den Zustand der Anlage mit Profil, bei Ein- und Ausgangsverzögerung mit
Countdown. Unter jedem Sensor steht, was Hauswacht gerade mit ihm macht:

| Hinweis | Bedeutung |
|---|---|
| überwacht | löst im aktiven Profil aus |
| nicht im aktiven Profil | wird ignoriert (z. B. Keller beim Profil „Zuhause“) |
| nur in Auslöseregeln: … | gehört im aktiven Profil nur zu diesen Auslöseregeln |

Darüber zeigt die Karte die **Auslöseregeln des aktiven Profils**: „nicht begonnen“ oder „Schritt 1
von 2 erfüllt · 85 s“.
| überbrückt bis zum Schließen | war beim Beenden eines Alarms offen; erst nach **Zu** wieder überwacht – ein zweites **Auf** ändert an einer offenen Tür nichts |
| Manipulation löst Alarm aus / nur Meldung | je nach Profil-Einstellung „Manipulation löst Alarm aus“; unscharf immer nur Meldung |

- Simulieren geht **nur im Testmodus**. Im Testmodus lösen **keine Sirenen** aus.
- Der simulierte Zustand gilt **nur für Hauswacht**: Scharfschalten, offene Sensoren,
  Eingangsverzögerung, Alarm, Manipulation, Ausfall – alles wie echt. Das Gerät und sein
  Zustand in Home Assistant bleiben unverändert, **andere Automationen merken nichts**.
- Solange ein Sensor simuliert wird, zählt sein echter Zustand für Hauswacht nicht (er wird
  in der Karte angezeigt). „Echt“ übernimmt den echten Wert – ist das Fenster in Wirklichkeit
  offen und die Anlage scharf, gibt es dann einen Testalarm.
- **Testmodus aus = alles wieder echt.** Nach einem Neustart sind Simulationen ebenfalls weg.

Dasselbe als Aktionen: `hauswacht.simulate_state` (Felder `sensor` und `state`: `on`, `off`,
`unavailable`, `real`) und `hauswacht.simulate_reset`.

**Sirenentest in der Karte:** Ganz unten, **eingeklappt**, steht „🔊 Sirenentest (echte
Sirene!)“. Aufgeklappt zeigt er jede Sirene mit dem letzten Test. „Testen …“ fragt erst nach
(„Sirene ertönt jetzt 3 s. Wirklich starten?“), danach „Gehört? Ja/Nein“. Das ist **keine
Simulation**: Es ertönt die echte Sirene (3 s, leise) – deshalb im Testmodus gesperrt und nur
für Administratoren. Alles Weitere wie unter [Sirenentest](#sirenentest).

## Scharfschalten mit Bestätigung

Erlaubt ein Profil offene oder ausgefallene Sensoren nur „nach Bestätigung“, verweigert das
normale Bedienfeld das Scharfschalten und nennt die betroffenen Sensoren. Bestätigen kannst du
mit der Aktion **`hauswacht.arm`**:

```yaml
action: hauswacht.arm
target:
  entity_id: alarm_control_panel.hauswacht
data:
  profile: Nacht
  confirm: true
```

Einfacher geht es mit dem Knopf **Trotzdem scharf schalten** für das in der Auswahlliste
gewählte Profil.

Offene Sensoren werden dabei **überbrückt**, also bis zum Unscharfschalten nicht überwacht.

## Attribute des Bedienfelds

| Attribut | Bedeutung |
|---|---|
| `profile`, `phase` | Aktives Profil, interner Zustand |
| `test_mode` | Testmodus aktiv |
| `timer`, `timer_ends_at` | Laufende Verzögerung und ihr Ende |
| `trigger_sensor`, `alarm_cycles` | Auslösender Sensor, Anzahl Alarmzyklen |
| `zones` | Meldergruppen mit ihren tatsächlichen Sensoren |
| `monitored_sensors` | Gerade scharf überwachte Sensoren |
| `open_sensors`, `unavailable_sensors` | Offene bzw. ausgefallene Sensoren aller Meldergruppen |
| `bypassed_sensors` | Überbrückte Sensoren |
| `last_contact` | Letzter Kontakt je Sensor |

## PIN-Regeln

PINs gehören zu den Benutzern (siehe „Benutzer und PINs“). Unter **Konfigurieren → Systemeinstellungen → Benutzer und PINs → PIN-Regeln**:

- **Master-PIN** (optional): ein einfacher PIN ohne eigene Benutzer, z. B. damit
  Sprachassistenten wie Alexa nur mit PIN unscharf schalten. Erscheint in der Benutzerliste als
  „Master-PIN“ mit allen Rechten.
- **PIN auch zum Scharfschalten verlangen**
- **Alarm ohne PIN beenden** (Knopf „Alarm beenden“ auch mit PIN)
- **Dashboard-Knöpfe trotz PIN erlauben:** „Unscharf schalten“, „Alarm beenden“ und die
  Scharf-Knöpfe funktionieren weiter. Der PIN schützt dann nur noch das Bedienfeld und
  Sprachassistenten – an die Knöpfe kommen ohnehin nur angemeldete Home-Assistant-Benutzer.

Allgemein:

- 4 bis 8 Ziffern, wird nur als Hash gespeichert.
- Sobald es einen PIN gibt, ist er zum Unscharfschalten am Bedienfeld immer nötig.
- Nach 5 falschen Eingaben in Folge ist die Eingabe 1 Minute gesperrt, bei weiteren
  Fehlversuchen jeweils doppelt so lange (höchstens 15 Minuten). Ab der 3. falschen Eingabe
  geht eine Systemmeldung an die eingetragenen Empfänger.
- Ohne PIN darf die Anlage nicht für Sprachassistenten (z. B. Alexa) freigegeben werden.
- Ein PIN aus Versionen vor 0.16.1 wurde beim Update automatisch zum Benutzer
  „Hauptbenutzer“.

## Benutzer und PINs

> ⚠️ **Wichtig: Entweder alle bekommen einen PIN – oder keiner.**
> Sobald **ein** PIN existiert (auch der Master-PIN), verlangt das Bedienfeld – und Alexa –
> zum Unscharfschalten einen PIN, **von allen**. Wer keinen PIN hat, kann dann nur noch über
> die Dashboard-Knöpfe (nur wenn unter PIN-Regeln „Dashboard-Knöpfe trotz PIN erlauben“ an ist)
> oder den Push-Knopf unscharf schalten. Ein gemeinsamer Familien-PIN ist erlaubt.
> Fehlt jemandem ein PIN, zeigt Home Assistant unter **Einstellungen → Reparaturen** den
> Hinweis „Nicht alle Personen haben einen PIN“ mit den Namen.
> Zeitgesteuerte Profile und die Anwesenheits-Automatik brauchen keinen PIN.

**Konfigurieren → Systemeinstellungen → Benutzer und PINs.** Jede Person bekommt einen Benutzer:

| Feld | Bedeutung |
|---|---|
| Name | Vorschläge aus den Home-Assistant-Benutzern oder frei (z. B. „Putzhilfe“). Erscheint als „geändert von“ am Bedienfeld, im Logbuch und in Push-Nachrichten |
| PIN | 4–8 Ziffern, nur als Hash gespeichert |
| Bedrohungs-PIN | siehe unten |
| Aktiv | aus = PIN gesperrt, ohne ihn zu löschen |
| Darf scharf schalten / unscharf schalten / Alarm beenden | Rechte |
| Home-Assistant-Konto | ordnet Push-Knopf und Dashboard-Knöpfe diesem Benutzer zu (mit seinen Rechten). Wird automatisch gesetzt, wenn als Name ein Home-Assistant-Benutzer gewählt wurde |
| Gültig von / bis | für Gäste: außerhalb dieser Zeit ist der PIN gesperrt |

- **Gemeinsamer PIN:** Mehrere Benutzer dürfen denselben PIN haben. Dann steht dort
  „gemeinsamer PIN (Christian, Petra)“. Eine Aktion ist erlaubt, wenn **mindestens einer**
  dieser Benutzer sie darf.
- **Gesperrter oder abgelaufener PIN:** wird abgelehnt wie ein falscher PIN; zusätzlich geht
  eine Systemmeldung an die Empfänger der Systemmeldungen.
- **Ohne PIN** (Push-Knopf, Dashboard-Knöpfe): Ist das Home-Assistant-Konto einem Benutzer
  zugeordnet, gelten dessen Name und Rechte; sonst erscheint der Name des Kontos und alles ist
  erlaubt.
- Automatik (Uhrzeit, Anwesenheit) erscheint als „Automatik“.

### Bedrohungs-PIN

Wer gezwungen wird, die Anlage auszuschalten, gibt seinen **Bedrohungs-PIN** ein:

- Die Anlage schaltet **ganz normal**; Bedienfeld, Logbuch und Dashboard sehen **unauffällig**
  aus („geändert von Petra“).
- Heimlich geht ein Notruf mit höchster Priorität an die **Empfänger Bedrohungsalarm**
  (Konfigurieren → Benachrichtigungen). Keine Sirene, keine sichtbare Meldung in Home Assistant.
- Der Bedrohungs-PIN wirkt auch, wenn der Benutzer das Recht sonst nicht hätte.
- Er darf keinem normalen PIN und keinem anderen Bedrohungs-PIN gleichen; das wird beim
  Speichern geprüft.
- **Unbedingt Empfänger eintragen** – ohne Empfänger hat der Bedrohungs-PIN keine Wirkung außer
  dem normalen Schalten.

## Verhalten nach einem Neustart

Hauswacht startet **immer unscharf**. War die Anlage vorher scharf, erscheint ein Hinweis
„Hauswacht: nach Neustart unscharf“. Der Testmodus bleibt erhalten.

## Ereignisse für eigene Automationen

Jede Aktion wird als Ereignis `hauswacht_event` gemeldet. Das Feld `type` nennt die Art:
`StateChanged`, `ActivateReaction` (Alarm), `StopReaction`, `TamperDetected`,
`SensorUnavailable`, `SensorsBypassed`, `ArmingAborted`, `RestartedDisarmed`,
`InfrastructureFault`, `InfrastructureRecovered`, `SensorSimulated`, `SirenDecision`,
`NotificationSuppressed` und weitere.

## Upgrade

- **Von 0.7.x auf 0.8.0:** Die bisherigen fünf festen Profile werden automatisch zu normalen
  Profilen mit gleichem Namen, Knopf und allen Einstellungen. Du kannst sie danach umbenennen,
  ändern oder löschen.
- **Von 0.2.0:** Lege zuerst Meldergruppen an und ordne sie den Profilen zu, sonst verweigert
  Hauswacht das Scharfschalten.
