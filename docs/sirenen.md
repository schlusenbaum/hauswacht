# Sirenen

> **Sicherheit zuerst:** Nach der Installation sendet Hauswacht **keinen** Sirenenbefehl. Erst
> die bewusste Freigabe („Echte Sirenenansteuerung erlauben“) schaltet das frei. Im Testmodus
> sind Sirenen immer gesperrt. Ein Brand hat immer Vorrang.

**Kurz erklärt:** Bei einem Alarm schaltet Hauswacht die Sirenen des Profils ein – mit einem
Einbruchton, der gewählten Lautstärke und für die „Dauer der Alarmreaktion“. Danach, beim
Beenden des Alarms und beim Unscharfschalten schaltet Hauswacht sie wieder aus. Vorher prüft ein
eigener Sicherheitsbaustein (der „Sirenen-Guard“) jedes Mal: Ist die Ansteuerung freigegeben?
Ist der Testmodus aus? Meldet kein Rauchmelder Brand? Hat die Sirene einen Einbruchton? Erst dann
geht ein Befehl raus.

## Das Menü „Alarmgeber – Sirenen“

Einstellungen → Geräte & Dienste → Hauswacht → **Konfigurieren → Alarmgeber – Sirenen**:

| Menüpunkt | Wofür | Abschnitt |
|---|---|---|
| **Sirenen und Freigabe** | Welche Sirenen Hauswacht verwenden darf; echte Ansteuerung freigeben; Experten: Schalter zulassen | [Einrichten](#einrichten) |
| **Sirene aus Schalter erstellen** | Assistent für Sirenen, die nur als Schalter (`switch.…`) erscheinen | [Sirene aus Schalter erstellen](#sirene-aus-schalter-erstellen) |
| **Ton je Sirene** | Ton für Sirenen mit eigenen Tonnamen festlegen (z. B. Homematic IP) | [Ton je Sirene](#ton-je-sirene) |
| **Sirenentest (echte Sirene!)** | Jede Sirene einzeln, kurz und leise prüfen | [Sirenentest](#sirenentest) |
| **Sirenentest – Erinnerung und Vorwarnung** | Regelmäßig an den Test erinnern; Vorwarnung vor dem Ton | [Sirenentest](#sirenentest) |

## Welche Sirenen gehen?

Jede Home-Assistant-Entität der Domain `siren` – Innen- und Außensirenen genauso wie
Rauchwarnmelder mit Sirene. Sirenen, die nur als Schalter erscheinen, lassen sich mit einem
[Assistenten](#sirene-aus-schalter-erstellen) einbinden.

Hauswacht liest vor jedem Alarm, was eine Sirene kann (`supported_features`,
`available_tones`), und sendet nur das:

| Fähigkeit der Sirene | Verhalten |
|---|---|
| Tonauswahl mit Einbruchton | Ton des Profils; fehlt er, ein anderer Einbruchton (`burglar`, `emergency`, `police_panic`, `emergency_panic`) – **nie automatisch ein Brandton** |
| Tonauswahl mit eigenen Tonnamen (z. B. HmIP-ASIR) | erst nach Wahl des Tons unter [Ton je Sirene](#ton-je-sirene); bis dahin bleibt sie aus |
| Tonauswahl nur mit Brandtönen | für Einbruch **nicht** verwendet – außer mit der [Experten-Freigabe](#brandton-als-experten-freigabe) (nie bei Rauchmeldern) |
| Keine Tonauswahl | Einfache Sirene: ohne Tonangabe. **Rauchmelder** ohne Tonauswahl werden nicht verwendet, weil ihr Standardton meist der Brandton ist |
| Lautstärke, Dauer | nur gesendet, wenn die Sirene sie unterstützt |
| Nur Ein und Aus | Hauswacht schaltet sie nach der Alarmdauer und beim Unscharfschalten selbst aus |
| Weder Dauer noch Ausschalten | nicht verwendet – Hauswacht könnte sie nicht beenden |
| Höchstdauer (`number.<sirene>_max_duration`, Zigbee2MQTT) | Dauer wird darauf begrenzt; fehlt sie, gelten 240 Sekunden |
| Brandsensor am selben Gerät (Rauchmelder) | gerätebezogene Brandsperre; ein aktiver Brand an einem beliebigen Melder sperrt immer |
| Nur als Schalter (`switch.…`) vorhanden | über den [Assistenten](#sirene-aus-schalter-erstellen) oder als [Experten-Funktion](#experten-schalter-direkt-als-sirene) |

**Erprobt** ist der Rauchwarnmelder **Develco/frient SMSZB-120** („Smoke detector with siren“)
über Zigbee2MQTT – auch mit echtem [Sirenentest](#sirenentest). Andere Modelle erst mit Testmodus
und Sirenentest prüfen. Rückmeldungen zu weiteren Modellen sind willkommen
([Issue](https://github.com/schlusenbaum/hauswacht/issues)).

## Einrichten

1. **Sirenen und Freigabe:** Sirenen auswählen, die Hauswacht für Einbruchalarme verwenden darf.
   „Echte Sirenenansteuerung erlauben“ noch **aus** lassen.
2. **Ton prüfen:** Kennt eine Sirene keinen der üblichen Einbruchtöne, unter
   [Ton je Sirene](#ton-je-sirene) den Ton festlegen. Die [Übersicht](uebersicht.md) weist darauf
   hin („bliebe bei Alarm stumm“).
3. **Profile:** In jedem Alarmprofil festlegen, welche dieser Sirenen ertönen, mit welchem Ton und
   welcher Lautstärke – oder „Stiller Alarm“ für nur Benachrichtigungen. Die Laufzeit ist die
   „Dauer der Alarmreaktion“ des Profils.
4. **Freigeben:** Erst wenn alles passt, **„Echte Sirenenansteuerung erlauben“** einschalten und
   die Bestätigung anhaken. Ohne diese Freigabe sendet Hauswacht nie einen Sirenenbefehl.
5. **Testen:** Jede Sirene einmal mit dem [Sirenentest](#sirenentest) prüfen.

Nach der Alarmdauer – und beim Beenden des Alarms – schaltet Hauswacht die Sirenen aus, die es
selbst eingeschaltet hat. Das ist für Sirenen wichtig, die nur Ein und Aus kennen. Sirenen mit
eigener Laufzeit (z. B. Rauchmelder mit Höchstdauer) bekommen die Dauer zusätzlich mitgeschickt,
höchstens aber die Höchstdauer des Geräts. Diese Höchstdauer wird nur gelesen, nie verändert.

## Ton je Sirene

Normalerweise wählt Hauswacht selbst einen Einbruchton (`burglar`, `emergency` …). Manche
Sirenen nennen ihre Töne anders. Findet Hauswacht keinen bekannten Einbruchton, bleibt die
Sirene aus Sicherheitsgründen aus (Grund `no_burglar_tone`), und die
[Übersicht](uebersicht.md#prüfhinweise) meldet das als wichtigen Prüfhinweis – auch unter
Einstellungen → Reparaturen.

**So geht's:** Alarmgeber – Sirenen → **Ton je Sirene** → Sirene wählen → Ton wählen.

- Die Liste zeigt genau die Töne, die die Sirene selbst meldet; der Dialog nennt sie zusätzlich
  im Text. „Automatisch (Standard-Einbruchton)“ hebt die Einstellung wieder auf.
- Der Ton gilt **bei jedem Alarm** dieser Sirene (unabhängig vom Ton im Profil) und **beim
  Sirenentest**.
- Brandtöne – erkennbar an „fire“, „smoke“ oder „Brand“ im Namen – sind gesperrt, außer mit der
  [Experten-Freigabe](#brandton-als-experten-freigabe).
- Danach einen kurzen, leisen [Sirenentest](#sirenentest) machen.

### Beispiel: Homematic IP Alarmsirene (HmIP-ASIR, HmIP-ASIR-2, HmIP-ASIR-O)

Über die Integration „Homematic(IP) Local“ erscheint die Alarmsirene als `siren.…`. Sie bleibt
stumm, wenn sie nicht gleichzeitig **Ton und Dauer** bekommt, und ihre Töne heißen z. B.
`FREQUENCY_RISING`, `FREQUENCY_RISING_AND_FALLING` oder `DISARMED`.

1. Alarmgeber – Sirenen → Sirenen und Freigabe → die Alarmsirene auswählen.
2. Ton je Sirene → Alarmsirene → **`FREQUENCY_RISING_AND_FALLING`** (oder einen anderen
   Alarmton der Sirene).
3. Im Profil die Alarmsirene bei den Sirenen eintragen.
4. Sirenentest mit 3 Sekunden. Die Dauer schickt Hauswacht automatisch mit.

Ob ein Ton laut ist, verrät nur der Test – Töne wie `DISARMED` oder `LOW_BATTERY` sind kurze
Quittungstöne und für einen Alarm ungeeignet.

### Brandton als Experten-Freigabe

Brandtöne sind für Einbruch gesperrt, aus zwei Gründen:

- **Falsche Reaktion:** Wer nachts einen Brandton hört, verlässt das Haus – womöglich genau
  dorthin, wo der Einbrecher ist. Beim Einbruchton bleibt man eher drin und ruft Hilfe.
- **Der Brandton verliert seinen Wert:** Ertönt er auch bei Einbruch- oder Fehlalarmen, wird er
  bei echtem Feuer weniger ernst genommen.

Manchmal täuscht aber der Name. **Beispiel:** Eine Außensirene hat nur zwei Töne, `chime` (leise
Klingel) und `fire` – und `fire` ist schlicht ihr lauter Sirenenton. Dann:

1. Ton je Sirene → Außensirene → Ton **`fire`** (in der Liste als „Brandton“ markiert).
2. **„Experten: Brandton für Einbruch erlauben“** einschalten.
3. Die Bestätigung anhaken: „Diese Sirene ist kein Rauchmelder, und alle im Haus kennen den Ton
   als Einbruchalarm“.

Was dabei gilt:

- Die Freigabe gilt nur für **diesen einen Ton an dieser einen Sirene**. Hauswacht weicht nie von
  sich aus auf einen Brandton aus.
- **Nie für Rauchmelder mit Sirene** (Geräte mit eigenen Rauch-, Hitze- oder
  Testknopf-Sensoren): Dort bietet der Dialog die Freigabe gar nicht an, und der Sirenen-Guard
  lehnt sie zusätzlich ab.
- Die **Brandsperre bleibt:** Meldet irgendwo ein Rauchmelder Brand, schaltet Hauswacht keine
  Sirene – egal mit welchem Ton.
- Die [Übersicht](uebersicht.md#prüfhinweise) zeigt die Freigabe dauerhaft als Hinweis, damit
  sie nicht in Vergessenheit gerät.

## Sirene aus Schalter erstellen

Manche Sirenen erscheinen in Home Assistant nur als Schalter (`switch.…`), z. B. eine Sirene an
einem Homematic-Schaltaktor. Home Assistant kann daraus selbst eine Sirene machen: mit dem Helfer
**„Gerätetyp eines Schalters ändern“**. Hauswacht hat dafür einen Assistenten.

**Beispiel:** Die Außensirene hängt an `switch.schaltaktor_garage`.

1. Alarmgeber – Sirenen → **Sirene aus Schalter erstellen**.
2. Schalter `switch.schaltaktor_garage` wählen.
3. Bestätigen: „Das ist eine reine Alarmsirene, kein Rauchmelder“.
4. Fertig: Der Dialog zeigt z. B. „Angelegt: siren.schaltaktor_garage“, und die neue Sirene steht schon
   in der Liste unter „Sirenen und Freigabe“.
5. Die Sirene im Profil eintragen und mit dem Sirenentest prüfen.

Gut zu wissen:

- Der Schalter wird dabei **nicht** geschaltet. Home Assistant blendet ihn aus und zeigt
  stattdessen die Sirene; in Automationen funktioniert der Schalter weiter.
- Die neue Sirene kennt nur Ein und Aus: Hauswacht schaltet sie bei Alarm ein und nach der
  Alarmdauer wieder aus. Freigabe, Brandsperre, Testmodus und Sirenentest gelten wie bei jeder
  Sirene.
- **Rückgängig:** den Helfer unter Einstellungen → Geräte & Dienste → Helfer löschen. Dann ist der
  Schalter wieder sichtbar.

> Bei einem Schalter weiß Hauswacht nicht, was das Gerät beim Einschalten tut. Nur echte
> Alarmsirenen so einbinden – nie Rauchmelder, Licht oder andere Geräte.

### Experten: Schalter direkt als Sirene

Wer keinen Helfer anlegen möchte, kann Schalter auch direkt eintragen:

1. Alarmgeber – Sirenen → **Sirenen und Freigabe** → **„Experten: Schalter direkt als Sirene
   zulassen“** einschalten und speichern.
2. Der Dialog öffnet sich erneut; jetzt bietet die Sirenenliste auch Schalter an.
3. Schalter auswählen, speichern, im Profil eintragen, Sirenentest machen.

Hauswacht schaltet einen solchen Schalter genauso wie eine einfache Sirene: `switch.turn_on` bei
Alarm, `switch.turn_off` nach der Alarmdauer und beim Unscharfschalten – mit denselben Sperren
(Freigabe, Testmodus, Brandsperre). Wird die Experten-Funktion wieder ausgeschaltet, fallen die
Schalter aus der Liste.

Der Assistent ist meist die bessere Wahl: Die Sirene sieht dann überall in Home Assistant wie
eine Sirene aus.

## Sirenentest

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

Ist für eine Sirene unter [Ton je Sirene](#ton-je-sirene) ein Ton eingestellt, testet Hauswacht
mit diesem Ton – so prüft der Test genau das, was auch bei einem Alarm passiert.

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
Sicherheitsabfrage, siehe [Karte „Hauswacht Test“](testmodus.md#karte-hauswacht-test).

## Warum hat eine Sirene nicht geklingelt?

Nach jedem Alarm und jedem Sirenentest steht im Attribut **`last_siren_decision`** am Bedienfeld
(Entwicklerwerkzeuge → Zustände → `alarm_control_panel.hauswacht`), welche Sirenen angesteuert
wurden (`sent`) und welche aus welchem Grund nicht (`blocked`). Beispiel:

```yaml
last_siren_decision:
  action: activate
  sent:
    - siren.flur
  blocked:
    siren.alarmsirene: no_burglar_tone
```

Hier hat die Flursirene geklingelt, die Alarmsirene nicht, weil sie keinen Einbruchton kennt.
Die Gründe im Klartext:

| Grund | Bedeutung | Was tun? |
|---|---|---|
| `hardware_disabled` | Echte Sirenenansteuerung ist nicht freigegeben | Sirenen und Freigabe → freigeben |
| `test_mode` | Testmodus ist an | Testmodus aus |
| `fire_lock` | Ein Rauchmelder meldet Brand, oder der Brandzustand einer registrierten Sirene ist unklar (Sensor nicht verfügbar) | Rauchmelder prüfen; bei Brand ist das gewollt |
| `no_burglar_tone` | Die Sirene kennt keinen Einbruchton (oder nur Brandtöne) | [Ton je Sirene](#ton-je-sirene) |
| `cannot_limit` | Die Sirene kann weder eine Dauer noch Ausschalten | Andere Sirene verwenden |
| `invalid_duration` | Höchstdauer des Geräts ist 0 | Höchstdauer am Gerät prüfen |
| `unknown_device` | Sirene steht im Profil, ist aber nicht (mehr) eingetragen | Sirenen und Freigabe prüfen |
| `invalid_tone`, `invalid_volume` | Ton bzw. Lautstärke im Profil ungültig | Profil neu speichern |
| `not_activated_by_hauswacht` | Ausschalten einer Sirene, die Hauswacht nicht eingeschaltet hat | nichts – Hauswacht schaltet nur eigene Sirenen aus |

Dieselbe Entscheidung kommt als Ereignis `hauswacht_event` mit `type: SirenDecision`, siehe
[Referenz](referenz.md#ereignisse).

## Brandschutz

Sind die Sirenen zugleich Rauchmelder, erkennt Hauswacht deren Rauch- und
Testknopf-Sensoren automatisch.

- Meldet **irgendein** Rauchmelder in Home Assistant Brand, schaltet Hauswacht keine Sirene
  ein und keine aus.
- Ist der Brandzustand einer **registrierten** Sirene unklar (Sensor nicht verfügbar oder
  deaktiviert), gilt dasselbe.
- Wurde während eines Einbruchalarms Brand gemeldet, schaltet auch das Unscharfschalten keine
  Sirene ab. Sirenen mit eigener Laufzeit verstummen nach ihrer Höchstdauer. Alle anderen
  schaltet Hauswacht aus, sobald kein Brand mehr gemeldet wird (Prüfung jede Minute).
- Ein Rauchmelder spielt bei Einbruch nie seinen Brandton – auch nicht mit der
  [Experten-Freigabe](#brandton-als-experten-freigabe).
- Fremde Abschalt-Skripte (z. B. „alle Rauchmelder aus“) verwendet Hauswacht nie.

Die verbindlichen Regeln dahinter stehen unter [Sicherheitsregeln](entwicklung/safety.md).
