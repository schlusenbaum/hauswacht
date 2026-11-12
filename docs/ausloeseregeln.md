# Auslöseregeln

**Alarmauslösung → Auslöseregeln.** Eine Auslöseregel löst erst bei einer **Abfolge** von
Meldern aus – z. B. „Tür, dann Keller“. Auslöseregeln stehen für sich; im Alarmprofil wählst du
unter **Auslöseregeln**, welche gelten. Dieselbe Regel kann in mehreren Profilen stecken.

Wozu? Nachts soll nicht jede Tür sofort Alarm geben (jemand geht kurz raus), wohl aber „Tür auf
und dann Bewegung im Keller“. Melder, die im Profil **allein** auslösen, brauchen keine Regel.

## Aufbau

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

## Anlegen mit dem Assistenten

Name und Ergebnis → Schritt 1 → Übersicht mit „Weiteren
Schritt hinzufügen“, „Schritt bearbeiten“, „Letzten Schritt entfernen“, „Fertig – speichern“
(bis zu 10 Schritte). Über jedem Schritt und in der Übersicht steht die Auslöseregel als Satz, z. B.
„eine(r) von Tür vorne / Tür hinten, dann innerhalb von 120 s Meldergruppe Keller → Eingangsverzögerung,
dann Alarm“. Gespeichert wird erst mit „Fertig – speichern“; Probleme stehen in der Übersicht.

Ergebnis einer erfüllten Auslöseregel: **sofort Alarm**, **Eingangsverzögerung, dann Alarm**
oder (im YAML-Modus) **nur Benachrichtigung**
(Zeit aus dem Alarmprofil – z. B. damit jemand, der heimkommt und gleich in den Keller geht,
noch unscharf schalten kann).

## Beispiel

Profil „Nacht“ – keine Meldergruppe löst allein aus, nur diese Regeln:

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

## Gut zu wissen

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
- Unvollständige Auslöseregeln meldet Hauswacht auf Wunsch: Ereignisse „Unbestätigte
  Auslösung“ und „Melder löst häufig allein aus“ unter
  [Benachrichtigungen](benachrichtigungen.md) (beide standardmäßig aus).
- Aus älteren Versionen: Die Gruppen-Option „zweiter Melder bestätigt“ (0.18.0) wurde automatisch
  zur Auslöseregel „Bestätigung <Meldergruppe>“.

## Ausnahme „Nicht, wenn vorher …“

In der Übersicht des Assistenten: **„Nicht, wenn vorher … (Ausnahme)“**. Die Auslöseregel gilt
nicht, wenn einer der gewählten Melder in der angegebenen Zeit **vor Schritt 1** ausgelöst hat.
Beispiel: „Fenster, dann Keller“ mit Ausnahme „Flur-Bewegungsmelder, 300 s“ – wer schon drinnen
unterwegs war und dann ein Fenster öffnet, löst nichts aus. Die Ausnahme wirkt **nur auf diese
Auslöseregel**. Die Testkarte zeigt „gesperrt durch Ausnahme · 4:10“.

## Expertenmodus (YAML)

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
