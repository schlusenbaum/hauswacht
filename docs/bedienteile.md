# Bedienteile: Keypads, Karten, NFC-Aufkleber, RFID-Leser, Taster, Türschlösser

**Deutsch** | [English](en/control-devices.md)

**Einstellungsseite → Personen und Bedienteile → Bedienteile.** Beliebig viele Bedienteile, jedes für einen **Bereich**
oder für **alle Bereiche**. Ausgewiesen wird immer mit den **Ausweisen der Benutzer** (PIN,
RFID-Karte, Schloss-Kennung): Rechte, Gültigkeit, Sperre nach falschen Eingaben und Bedrohungs-PIN gelten wie am
Bedienfeld. „Geändert von“ zeigt z. B. „Anna (Keypad Flur)“.

| Bedienteil | Ausweis | Typisch für |
|---|---|---|
| [Keypad (Zigbee2MQTT)](#keypad-zigbee2mqtt) | PIN und/oder RFID-Karte + Taste | Wand neben der Haustür |
| [Keypad (allgemein)](#keypad-allgemein) | PIN und/oder RFID-Karte + Taste | Keypads über ZHA, Z-Wave, ESPHome, Node-RED … |
| [MQTT-Schnittstelle](#mqtt-schnittstelle) | PIN und/oder RFID-Karte + Befehl | Wand-Tablets, Eigenbauten und Programme, die nur MQTT sprechen |
| [NFC-Aufkleber](#nfc-aufkleber-companion-app) | das eigene Handy (Home-Assistant-App) | Bewohner mit App |
| [RFID-Leser](#rfid-leser) | RFID-Karte, ohne Taste | Karte vorhalten und fertig |
| [Fingerabdruck-Leser](#fingerabdruck-leser-esphome) | gespeicherter Finger (wie eine Karte) | Finger auflegen, z. B. im Flur |
| [Taster](#taster) | **keiner** – schaltet deshalb nur scharf | Taster im Hausflur: drücken, rausgehen |
| [Türschloss](#türschloss-z-b-nuki) | wer aufgeschlossen hat (Nuki-Benutzer, Keypad-Code …) | Aufschließen = unscharf |

## Wie gut erprobt?

Nicht jedes Bedienteil konnten wir an echter Hardware prüfen. Damit du weißt, worauf du dich
verlassen kannst:

| Kennzeichen | Bedeutung | Bedienteile |
|---|---|---|
| **Erprobt** | automatische Tests **und** im Alltag mit echter Hardware geprüft | Keypad (Zigbee2MQTT), RFID-Karten am Keypad |
| **Getestet** | automatische Tests, aber noch ohne Rückmeldung mit echter Hardware | Keypad (allgemein), MQTT-Schnittstelle, NFC-Aufkleber, RFID-Leser, Fingerabdruck-Leser, Taster, Türschloss (Nuki und allgemein) |
| **Ungetestet – eigene Verantwortung** | nach Hersteller-Doku gebaut, nie am Gerät geprüft | [Vorlagen](#fertige-vorlagen): Blueprint Ring Keypad v2, ESPHome-Beispiel |

Läuft bei dir etwas aus „Getestet“ oder „Ungetestet“ zuverlässig? Eine kurze Rückmeldung als
[GitHub-Issue](https://github.com/schlusenbaum/hauswacht/issues) mit Gerät und Firmware hilft
allen – dann steigt es auf.

Wo die Sicherheit von **deiner eigenen Einrichtung** abhängt, liegt sie in deiner
Verantwortung: Zugang zum MQTT-Broker (gilt für Zigbee2MQTT genauso), PINs in der Datenbank von
Home Assistant (siehe [PINs außerhalb von Hauswacht](#pins-außerhalb-von-hauswacht)), selbst
geschriebene oder geänderte Übersetzer.

## Keypad (Zigbee2MQTT)

Für Alarm-Keypads nach dem Zigbee-Standard für Bedienteile (IAS ACE) – z. B. frient/Develco
KEPZB-110 und KEYZB-110, Linkind, Centralite, Heiman. Voraussetzung: Zigbee2MQTT und die
MQTT-Integration in Home Assistant. Andere Keypads (ZHA, Z-Wave, ESPHome …): siehe
[Keypad (allgemein)](#keypad-allgemein).

**Einrichten:**

1. Keypad in Zigbee2MQTT anlernen und sinnvoll benennen, z. B. „Keypad“. Der Name ist Teil des
   MQTT-Topics.
2. **Einstellungsseite → Personen und Bedienteile → Bedienteil anlegen → Keypad (Zigbee2MQTT):**

| Einstellung | Bedeutung |
|---|---|
| Name | z. B. „Keypad Flur“ – erscheint in „geändert von“, etwa „Anna (Keypad Flur)“ |
| Bereich | ein Bereich oder alle |
| Keypad-Gerät | das Keypad aus der Liste (Geräte von Zigbee2MQTT bzw. MQTT). Daraus bildet Hauswacht das MQTT-Topic selbst: `zigbee2mqtt/<Name in Zigbee2MQTT>`, z. B. `zigbee2mqtt/Alarm-Tastatur` |
| MQTT-Topic (nur für Experten) | **leer lassen** = automatisch aus dem Keypad-Gerät. Nur nötig, wenn in Zigbee2MQTT ein anderes Basis-Topic als `zigbee2mqtt` eingestellt ist oder das Gerät nicht in der Liste auftaucht. Dann: Basis-Topic + Gerätename, genau wie in Zigbee2MQTT geschrieben (Groß-/Kleinschreibung, Bindestriche), ohne `/set`. Ein eingetragenes Topic hat Vorrang |
| Tasten „Tag“, „Nacht“, „Alle“ | je ein Alarmprofil zum **Scharfschalten**, z. B. Tag → „Zuhause“, Nacht → „Nacht“, Alle → „Abwesend“; Tasten ohne Profil antworten „nicht bereit“. Beim frient-Keypad: **Tag = 🏠 Haus**, **Nacht = 🌙 Mond**, **Alle = 🔒 Schloss**. Unscharf schaltet die eigene Taste 🔓 (offenes Schloss) – kein Profil dafür anlegen. Tasten mehrfach belegen: [Aktions-Codes](#aktions-codes) |
| Taste für den Durchgang | Statt eines Profils kann eine Taste **„Durchgang (rein/raus, bleibt scharf)“** bekommen – nicht nötig: Ist der Durchgang im Profil an, öffnet ohnehin **jede** Profil-Taste mit PIN oder Karte den Durchgang, solange scharf ist oder die Eingangsverzögerung läuft (es wird nie umgeschaltet). Siehe [Durchgang](durchgang.md) |
| Anmeldung | **PIN oder Karte** oder **Karte und PIN** (beide Ausweise desselben Benutzers innerhalb von 30 s; der erste wird mit „nicht bereit“ quittiert) |
| Notruf-Taste | **aus** (Standard – dann passiert beim Drücken von SOS nichts Sichtbares), **still** (wichtige Push-Nachricht) oder **Alarm** (zusätzlich sofortiger Alarm – unscharf mit den Sirenen unter „Immer aktiv“, scharf mit denen des aktiven Profils) |

**Keypad in Zigbee2MQTT umbenannt?** Dann ändert sich auch sein MQTT-Topic. Keypad in Hauswacht
einmal bearbeiten und absenden – das Topic wird aus dem neuen Namen gebildet. Steht ein eigenes
Topic im Expertenfeld, dieses anpassen.

3. Den **Sabotagekontakt** des Keypads (`binary_sensor.<keypad>_tamper`) in eine Meldergruppe
   aufnehmen (Typ Manipulation) – sinnvollerweise erst, wenn es fest an der Wand hängt, und
   dann in den Profilen auswählen.
4. Optional: Batterie in [Battery Notes](https://github.com/andrew-codechimp/HA-Battery-Notes)
   eintragen (frient KEPZB-110: 4 × AA).

**Bedienen:** erst **PIN tippen oder Karte vorhalten**, dann die **Taste** drücken (Unscharf,
Tag, Nacht, Alle). Das Keypad schickt Code bzw. Kartennummer nur zusammen mit einem
Tastendruck – Karte vorhalten allein schaltet nichts (dafür gibt es den
[RFID-Leser](#rfid-leser)).

**Rückmeldung:** Hauswacht antwortet auf jeden Tastendruck (gültig, ungültiger Ausweis, nicht
bereit – z. B. Fenster offen –, schon unscharf) und zeigt danach laufend den Zustand an:
Ausgangs- und Eingangsverzögerung, scharf (Tag/Nacht/alle), Alarm. Dafür sendet Hauswacht an
`<Topic>/set` (`arm_mode`) – **nur** Zustandsanzeigen an eingerichtete Keypads; ein Test stellt
sicher, dass Hauswacht sonst nirgends hin sendet.

### Trotzdem scharf am Keypad

Ist beim Scharfschalten noch ein Melder offen (z. B. ein gekipptes Fenster) oder ausgefallen,
antwortet das Keypad **„nicht bereit“**. Erlaubt das Profil das **nach Bestätigung**, bestätigst
du am Keypad so:

1. Taste drücken, z. B. 🌙 Nacht – mit PIN bzw. Karte oder, wenn Scharfschalten ohne PIN erlaubt
   ist, auch ohne → „nicht bereit“.
2. **Innerhalb von 10 Sekunden** noch einmal **dieselbe Taste** – mit oder ohne PIN bzw. Karte.
3. Hauswacht schaltet **trotzdem scharf** und überbrückt die offenen Melder bis zum
   Unscharfschalten – wie „Trotzdem scharf“ in der Karte. Du bekommst den
   [Hinweis beim Scharfschalten](benachrichtigungen.md#hinweis-beim-scharfschalten), was nicht
   überwacht wird.

Bedingungen:

- Profil-Einstellung „Offene Sensoren beim Scharfschalten“ bzw. „Ausgefallene Sensoren beim
  Scharfschalten“ = **nach Bestätigung erlauben**. Bei **verweigern** bleibt es auch beim
  zweiten Druck bei „nicht bereit“; bei **automatisch überbrücken** braucht es keinen zweiten
  Druck.
- Kam der erste Druck mit PIN oder Karte, braucht die Person das Recht **„Darf am Keypad trotzdem
  scharf schalten“** (Standard an; je Person abschaltbar, z. B. für Kinder). Der zweite
  Druck darf dann ohne PIN kommen – er gilt im Namen dieser Person.
- Kommt der zweite Druck mit einem **anderen** PIN, muss es dieselbe Person sein. Ein falscher
  PIN wird wie immer abgelehnt.
- **Ohne PIN** geht es nur, wenn Scharfschalten ohne PIN erlaubt ist („PIN auch zum
  Scharfschalten“ aus). Dann kann jeder am Keypad auch trotzdem scharf schalten – so wie er ja
  auch ohne PIN scharf schalten kann.
- Drückt dazwischen jemand eine andere Taste, verfällt die Bestätigung.
- Bei Anmeldung „Karte und PIN“ meldest du dich für den ersten Druck mit beidem an.

**Beispiel:** Abends ist das Badfenster gekippt. Anna tippt `2580` + 🌙 → „nicht bereit“. Sie
drückt sofort noch einmal 🌙 → das Keypad zeigt die Ausgangsverzögerung, Hauswacht meldet
„Profil Nacht ist scharf (Anna, Keypad Flur). Nicht überwacht: Badfenster – offen, überbrückt bis
zum Unscharfschalten“.

**PINs nicht im Verlauf:** Zigbee2MQTT legt für den am Keypad getippten Code eine eigene
Entität an, z. B. `sensor.keypad_flur_action_code`. Home Assistant speichert sie im Verlauf –
also jede PIN im Klartext, auch in Backups. Hauswacht braucht sie nicht. Weil die Entität der
MQTT-Integration gehört, ändert Hauswacht sie **nicht selbst**, sondern zeigt unter
**Einstellungen → Reparaturen** die Meldung „Hauswacht: PINs vom Keypad landen im Verlauf“
(auch wenn die Entität erst später entsteht):

- **Beheben** → bestätigen: Hauswacht deaktiviert die Entität (wie Einstellungen → Entitäten →
  Deaktivieren).
- **Ignorieren**: Die Entität bleibt, wie sie ist.

Schaltest du sie danach bewusst wieder ein, fragt Hauswacht nicht noch einmal. Deaktivierst du
sie selbst, verschwindet die Meldung von allein. Bereits gespeicherte Einträge löscht Home
Assistant mit dem normalen Aufräumen des Verlaufs (Standard: 10 Tage) – sofort geht es mit der
Aktion „Recorder: Entitäten bereinigen“ für diese Entität.

Wo das Keypad hängen sollte, damit man es in der Eingangsverzögerung erreicht, hilft die
Messung [„Tür auf bis unscharf“](beobachtung.md#tür-auf-bis-unscharf).

## Keypad (allgemein)

> **Getestet** – mit automatischen Tests geprüft, aber noch ohne Rückmeldung mit echten Geräten.
> Siehe [Wie gut erprobt?](#wie-gut-erprobt).

Für Keypads, die Hauswacht **nicht selbst** kennt: ZHA-Keypads (z. B. frient, Xfinity,
Centralite), Z-Wave-Keypads (z. B. Ring Keypad v2), deCONZ, selbst gebaute Bedienteile mit
ESPHome, Abläufe in Node-RED – kurz: alles, was Home Assistant erreicht.

**So funktioniert es:** Hauswacht spricht nicht direkt mit dem Gerät. Dazwischen sitzt ein
kleiner **Übersetzer** – eine Automation (später auch fertige Blueprints), ein Ablauf in
Node-RED oder das Gerät selbst. Er übersetzt in beide Richtungen:

```
Keypad ──Taste + PIN──► Übersetzer ──hauswacht.keypad_input──► Hauswacht
Keypad ◄──LEDs, Töne──  Übersetzer ◄──sensor.…_anzeige──────── Hauswacht
```

Hauswacht wertet die Eingabe **genau wie beim Zigbee2MQTT-Keypad** aus: Rechte, Gültigkeit,
Sperre nach falschen Eingaben, Bedrohungs-PIN, Karte und PIN, Aktions-Codes, „trotzdem scharf“,
Notruf, Anlernen unbekannter Karten.

### Einrichten

**[Einstellungsseite](einstellungsseite.md) → Personen und Bedienteile → Bedienteil anlegen →
Keypad (allgemein):**

| Einstellung | Bedeutung |
|---|---|
| Name | z. B. „Keypad Flur“ – erscheint in „geändert von“, etwa „Anna (Keypad Flur)“ |
| Bereich | ein Bereich oder alle |
| Tasten | bis zu vier Tasten mit **freiem Namen** und je einem Alarmprofil, z. B. `home` → „Zuhause“, `away` → „Abwesend“, `night` → „Nacht“. Der Name ist das, was dein Übersetzer als `button` sendet. `disarm` (unscharf) und `emergency` (Notruf) gibt es immer – dafür nichts eintragen |
| Anmeldung | **PIN oder Karte** oder **Karte und PIN** |
| Notruf-Taste | aus, still oder Alarm – wie beim [Zigbee2MQTT-Keypad](#keypad-zigbee2mqtt) |

Die **Kennung** des Keypads (z. B. `keypad_flur`) wird beim Speichern aus dem Namen gebildet und
steht danach im Seitenblatt unter „Kennung für Automationen“. Mit ihr meldet der Übersetzer
Eingaben. Statt der Kennung gehen auch der Name oder die Anzeige-Entität.

**Unbekanntes Keypad hat sich gemeldet:** Ruft ein Übersetzer mit einer Kennung auf, die es in
Hauswacht nicht gibt, lehnt Hauswacht ab (Ergebnis `unknown_keypad`). Auf der Einstellungsseite
steht dann unter Bedienteile „Unbekanntes Keypad … hat sich gemeldet“ mit einem Knopf zum Anlegen
– die Kennung ist schon eingetragen, nur noch Tasten und Bereich wählen. So kann kein unbekanntes Gerät etwas schalten.

### Die Aktion `hauswacht.keypad_input`

| Feld | Bedeutung | Beispiel |
|---|---|---|
| `keypad` | Kennung, Name oder Anzeige-Entität des Keypads | `keypad_flur` |
| `button` | `disarm`, `emergency` oder eine eigene Taste | `away` |
| `code` | getippter PIN oder gelesene Kartennummer | `2580` |
| `force` | „trotzdem scharf“ – offene Melder überbrücken, wenn Profil und Benutzer das erlauben | `true` |

Die Aktion **antwortet**. In einer Automation holst du die Antwort mit `response_variable`:

| Antwort | Bedeutung |
|---|---|
| `result` | `ok` · `invalid_code` (falscher Ausweis **oder** keine Rechte – bewusst nicht zu unterscheiden) · `locked` (zu viele Fehlversuche) · `not_ready` (z. B. Fenster offen) · `pending` (Karte und PIN: erster Ausweis erkannt, zweiter fehlt) · `already_disarmed` · `unknown_button` · `unknown_keypad` |
| `display` | was das Keypad jetzt zeigen soll (wie die Anzeige-Entität) |
| `open_sensors` | bei `not_ready`: welche Melder es verhindern, z. B. `["Küchenfenster"]` |
| `can_force` | bei `not_ready`: „trotzdem scharf“ wäre möglich (zweimal dieselbe Eingabe oder `force: true`) |
| `lock_seconds` | bei `locked`: wie lange die Sperre noch dauert |

**Doppelte Meldungen:** Funkgeräte senden manchmal doppelt. Dieselbe Eingabe vom selben Keypad
innerhalb von 2 Sekunden wertet Hauswacht nur einmal aus – ein doppelt gesendeter falscher PIN
zählt nicht doppelt.

**Wer darf die Aktion aufrufen?** Automationen, Skripte, Geräte (z. B. ESPHome) und
Administratoren. Normale Benutzer nicht – sie bedienen über die Hauswacht-Karte. Sonst könnte
jeder angemeldete Benutzer z. B. einen Notruf ohne PIN auslösen.

### Die Anzeige-Entität

Jedes allgemeine Keypad bekommt eine Entität **„Keypad Flur Anzeige“**
(`sensor.hauswacht_keypad_flur_anzeige`). Dein Übersetzer reagiert auf ihre Änderungen und
steuert damit das Gerät:

| Zustand | Bedeutung | Typisch am Keypad |
|---|---|---|
| `disarmed` | unscharf | grün / aus |
| `exit_delay` | Ausgangsverzögerung läuft | Piepen, Countdown |
| `armed_home`, `armed_away`, `armed_night`, `armed_vacation`, `armed_custom_bypass` | scharf (je nach Knopf des Profils) | rot |
| `entry_delay` | Eingangsverzögerung – jetzt PIN eingeben | schnelles Piepen |
| `triggered` | Einbruchalarm | Alarm |
| `test_alarm` | Alarm im **Testmodus** | nur anzeigen, **keine** Sirene |
| `fire` | Brand erkannt (hat Vorrang vor allem anderen) | Brandanzeige |

Im Testmodus zeigt die Entität **nie** `triggered`, sondern `test_alarm`. So kann ein Keypad mit
eingebauter Sirene im Testmodus nicht versehentlich losheulen.

Attribute: `delay_ends` und `delay_seconds` (Ende bzw. Rest der Verzögerung – für einen
Countdown), `profile`, `changed_by`, `test_mode`, `buttons`, `last_result` (Ergebnis der letzten
Eingabe) und `last_result_at`. **Nie** enthalten: PINs und Kartennummern.

### Beispiel: Übersetzer als Automation

Ein selbst gebautes ESPHome-Keypad sendet beim Drücken einer Taste ein Ereignis
`esphome.keypad_flur` mit `button` und `code`. Die erste Automation gibt die Eingabe an
Hauswacht weiter und lässt bei einem Fehler den Summer des Keypads kurz piepen:

```yaml
alias: Keypad Flur → Hauswacht
mode: queued
triggers:
  - trigger: event
    event_type: esphome.keypad_flur
actions:
  - action: hauswacht.keypad_input
    data:
      keypad: keypad_flur
      button: "{{ trigger.event.data.button }}"
      code: "{{ trigger.event.data.code }}"
    response_variable: antwort
  - if: "{{ antwort.result not in ['ok', 'pending'] }}"
    then:
      - action: esphome.keypad_flur_beep  # Fehlerton (eigene Aktion des Geräts)
```

Die zweite Automation zeigt am Keypad, was Hauswacht meldet – auch nach einem Neustart:

```yaml
alias: Hauswacht → Keypad Flur
mode: restart
triggers:
  - trigger: state
    entity_id: sensor.hauswacht_keypad_flur_anzeige
    not_to: [unknown, unavailable]
  - trigger: homeassistant
    event: start
conditions:
  - condition: not
    conditions:
      - condition: state
        entity_id: sensor.hauswacht_keypad_flur_anzeige
        state: [unknown, unavailable]
actions:
  - action: esphome.keypad_flur_show  # eigene Aktion des Geräts
    data:
      mode: "{{ states('sensor.hauswacht_keypad_flur_anzeige') }}"
```

Ein ESPHome-Gerät kann die Aktion auch **direkt** aufrufen (`homeassistant.action` mit
`action: hauswacht.keypad_input`) und die Anzeige-Entität selbst lesen – dann braucht es gar
keine Automation. In der ESPHome-Integration muss dafür „Gerät darf Home-Assistant-Aktionen
ausführen“ eingeschaltet sein.

### Fertige Vorlagen

> **Ungetestet – Nutzung auf eigene Verantwortung.** Die Vorlagen sind nach der Dokumentation
> der Geräte und der Community gebaut, aber nie an einem echten Gerät geprüft. Läuft eine bei dir?
> Bitte kurz als [GitHub-Issue](https://github.com/schlusenbaum/hauswacht/issues) melden (Gerät,
> Firmware) – dann steigt sie zu „Getestet von der Community“ auf.

| Gerät | Vorlage | Was sie tut |
|---|---|---|
| **Ring Keypad v2** (Z-Wave JS) | Blueprint [ring_keypad_v2.yaml](https://github.com/schlusenbaum/hauswacht/blob/main/blueprints/automation/hauswacht/ring_keypad_v2.yaml) – [![Blueprint importieren](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fschlusenbaum%2Fhauswacht%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fhauswacht%2Fring_keypad_v2.yaml) | Unscharf, Abwesend (Taste `away`), Zuhause (Taste `home`), Polizei-Taste lang drücken = Notruf. Fehlerton bei falschem PIN, Enter blinkt bei „nicht bereit“. Lichter und Töne nach der Anzeige-Entität, mit Countdown bei den Verzögerungen. Im Testmodus nur das Medizin-Licht, kein Alarmton |
| **Selbstbau mit ESPHome** (4×4-Tastenfeld, zwei LEDs) | Beispiel [hauswacht_keypad.yaml](https://github.com/schlusenbaum/hauswacht/blob/main/blueprints/esphome/hauswacht_keypad.yaml) | PIN + A/B/C/D, ruft die Aktion direkt auf – ohne Automation. LEDs nach der Anzeige-Entität. Zum Anpassen (Pins, Kennung, Entität) |

**Ring Keypad einrichten:**

1. In Hauswacht ein „Keypad (allgemein)“ anlegen, mit den Tasten `away` und `home` und je einem
   Alarmprofil.
2. Blueprint importieren (Knopf oben), daraus eine Automation erstellen: das Ring Keypad und die
   Anzeige-Entität des Hauswacht-Keypads wählen, speichern.
3. Ausprobieren: PIN tippen, „Zuhause“ drücken.

**Am bequemsten von der Einstellungsseite:** Beim „Keypad (allgemein)“ steht unter den Tasten
„Ring Keypad v2: Blueprint importieren“. Der Knopf öffnet sich in einem **neuen Tab** und holt
den Blueprint aus **genau deiner Hauswacht-Version** – auch bei Vorabversionen. Der Knopf hier in
der Anleitung holt immer die neueste veröffentlichte Version (GitHub öffnet ihn im selben Tab;
mit Strg- bzw. ⌘-Klick in einem neuen).

Die Vorlage trägt eine **Versionsnummer** (in der Beschreibung). Gibt es eine neue, im Blueprint
„Blueprint erneut importieren“ wählen.

**ZHA-Keypads (frient, Xfinity, Centralite …):** ZHA verbindet diese Keypads mit einem eigenen
kleinen Bedienfeld in ZHA – Tasten und PIN kommen dann nicht bei einer Automation an. Damit sie
mit Hauswacht gehen, braucht es eine Geräteanpassung für ZHA (Quirk). Eine Vorlage dafür gibt es
noch nicht. Wer so ein Keypad hat und mittesten mag: bitte ein Issue aufmachen. Mit
**Zigbee2MQTT** gehen dieselben Keypads schon heute direkt – siehe
[Keypad (Zigbee2MQTT)](#keypad-zigbee2mqtt).

### PINs außerhalb von Hauswacht

Hauswacht speichert PINs nie im Klartext. **Dein Übersetzer aber schon möglicherweise:**

- Meldet ein Gerät den PIN als **Ereignis** (z. B. `zha_event`, `zwave_js_notification` oder
  wie im Beispiel `esphome.keypad_flur`), speichert Home Assistant dieses Ereignis in seiner
  Datenbank – mit dem PIN, auch in Backups.
- Die **Ablaufverfolgung** (Trace) der Automation enthält den PIN ebenfalls.

Das kann Hauswacht nicht verhindern. Was hilft:

```yaml
# configuration.yaml – Ereignisse mit PINs nicht in der Datenbank speichern
recorder:
  exclude:
    event_types:
      - esphome.keypad_flur
```

Achtung: Damit fehlen **alle** Ereignisse dieses Typs in der Datenbank – bei `zha_event` z. B.
auch die anderer ZHA-Geräte. Und in der Automation die Zahl gespeicherter Abläufe klein halten
(`trace: stored_traces:` mit einer kleinen Zahl).

## MQTT-Schnittstelle

> **Getestet** – mit automatischen Tests geprüft, aber noch ohne Rückmeldung mit echten Geräten.
> Siehe [Wie gut erprobt?](#wie-gut-erprobt).

Für Geräte und Programme, die **nur MQTT** sprechen und Home Assistant nicht kennen:
Wand-Tablet-Apps für MQTT-Alarmzentralen, Tasmota- oder Arduino-Eigenbauten, Node-RED, andere
Systeme. Eine MQTT-Schnittstelle ist ein Keypad – Hauswacht wertet ihre Befehle **genau wie am
Zigbee2MQTT-Keypad** aus (Rechte, Sperre, Bedrohungs-PIN, Karte und PIN, Aktions-Codes,
„trotzdem scharf“, Notruf).

### Einrichten

**[Einstellungsseite](einstellungsseite.md) → Personen und Bedienteile → Bedienteil anlegen →
MQTT-Schnittstelle:**

| Einstellung | Bedeutung |
|---|---|
| Name, Bereich | wie bei jedem Bedienteil |
| Basis-Topic | z. B. `hauswacht/flur` – darunter liegen alle Topics (siehe unten). Nicht unter `zigbee2mqtt`, keine `+` oder `#`; jede Schnittstelle braucht ihr eigenes |
| Befehlswörter → Alarmprofil | das Wort, das dein Gerät zum Scharfschalten sendet, und das Profil dazu, z. B. `ARM_AWAY` → „Abwesend“, `ARM_HOME` → „Zuhause“, `ARM_NIGHT` → „Nacht“. Groß/klein und Leerzeichen sind egal |
| Befehlswort für Unscharf / Notruf | Standard `DISARM` bzw. `PANIC` |
| Name des Code-Felds im JSON | Standard `code` – manche Geräte schicken `pin` |
| Anmeldung, Notruf-Taste | wie beim [Zigbee2MQTT-Keypad](#keypad-zigbee2mqtt) |
| Eigene Zustandswörter | für Experten: eine Zeile je Zustand, z. B. `armed_away: ARMED_AWAY` |

### Topics

| Topic | Richtung | Gespeichert (retain) | Inhalt |
|---|---|---|---|
| `hauswacht/flur/set` | an Hauswacht | – | Befehl |
| `hauswacht/flur/state` | von Hauswacht | ja | Zustand als Wort |
| `hauswacht/flur/attributes` | von Hauswacht | ja | Details als JSON |
| `hauswacht/flur/response` | von Hauswacht | nein | Antwort auf jeden Befehl |
| `hauswacht/flur/availability` | von Hauswacht | ja | `online` / `offline` |

**Befehle** gehen als Text oder JSON:

```
ARM_AWAY
DISARM
{"action": "ARM_NIGHT", "code": "2580"}
{"action": "ARM_NIGHT", "code": "2580", "force": true, "id": 17}
```

`force` heißt „trotzdem scharf“ (nur mit dem Recht dazu), `id` kommt in der Antwort zurück.
Unscharf geht – wie am Keypad – nur mit PIN oder Karte. **Gespeicherte Befehle (retain) führt
Hauswacht nie aus** – sonst käme ein altes `DISARM` nach jedem Neustart erneut an. Hauswacht
meldet so etwas mit dem Ereignis `MqttRetainedCommand`.

**Zustand:** Standardwörter wie die MQTT-Alarmzentrale von Home Assistant – damit passen viele
fertige Tablet-Apps ohne Anpassung:

| Hauswacht | Wort |
|---|---|
| unscharf | `disarmed` |
| Ausgangsverzögerung | `arming` |
| scharf | `armed_home`, `armed_away`, `armed_night`, `armed_vacation`, `armed_custom_bypass` (je nach Knopf des Profils) |
| Eingangsverzögerung | `pending` |
| Alarm, Brand | `triggered` |
| Alarm im Testmodus | `test_alarm` – **nie** `triggered`, damit ein Gerät mit eigener Sirene im Testmodus nicht losheult |

**Antwort** (JSON) – dieselben Ergebnisse wie bei der [Aktion `hauswacht.keypad_input`](#keypad-allgemein):

```json
{"keypad": "tablet_flur", "result": "not_ready", "display": "disarmed",
 "open_sensors": ["Küchenfenster"], "can_force": true, "lock_seconds": 0, "id": 17}
```

**Details** (`attributes`, JSON): `state`, `display` (Zustand wie bei der Anzeige-Entität),
`area`, `profile`, `delay_ends`, `delay_seconds`, `test_mode`, `changed_by`, `buttons`,
`last_result`. **Nie** enthalten: PINs, Kartennummern.

### Ausprobieren ohne Gerät

Mit einem MQTT-Programm, z. B. dem Add-on **MQTT Explorer**:

1. Im Bereich **Publish** ins Feld **Topic** von Hand `hauswacht/flur/set` eintippen. Das Topic
   gibt es vorher nicht – es entsteht beim ersten Senden. Hauswacht selbst sendet nie auf `set`,
   es hört dort nur zu.
2. Format **json**, Nachricht `{"action": "ARM_NIGHT", "code": "2580", "id": 1}`, **retain aus**,
   senden.
3. Unter `hauswacht/flur/response` steht die Antwort, unter `…/state` der neue Zustand. Zurück mit
   `{"action": "DISARM", "code": "2580"}`.

Im Log von Home Assistant steht jeder Befehl (ohne PIN), z. B. „MQTT-Schnittstelle Tablet Flur:
Befehl arm_night mit Ausweis → ok“ – sichtbar, wenn für Hauswacht die Protokollstufe „Info“ oder
feiner eingestellt ist.

### Sicherheit: den Broker absichern

**Wer auf den Broker schreiben darf, darf an die Anlage** – genau wie bei Zigbee2MQTT-Keypads
schon heute. Deshalb:

- Jedes Gerät bekommt einen **eigenen Broker-Benutzer** mit Passwort.
- **Zugriffsrechte (ACL)** so eng wie möglich, z. B. für das Tablet im Flur:
  ```
  user tablet_flur
  topic read hauswacht/flur/#
  topic write hauswacht/flur/set
  ```
  Beim Mosquitto-Add-on von Home Assistant stehen diese Regeln in einer eigenen ACL-Datei (siehe
  Dokumentation des Add-ons).
- Kein anonymer Zugang, Broker nicht ins Internet freigeben; außerhalb des Heimnetzes nur mit
  TLS.
- Getippte PINs laufen im Klartext über den Broker – auch das spricht für TLS und eigene Benutzer.

## Aktions-Codes

**Einstellungsseite → Personen und Bedienteile → Aktions-Codes.** Ein Aktions-Code ist ein **Code plus eine
Funktionstaste** am Keypad, z. B. **7777 + 🏠 Haus**. Er löst eine festgelegte Aktion aus – so
lassen sich die Tasten des Keypads mehrfach belegen:

```
➕ Neuer Aktions-Code
Außenlicht – 7777 + 🏠 Haus · alle Keypads → Ereignis
Licht aus – 7777 + 🌙 Nacht · alle Keypads → Ereignis
Garagenlicht – 42 + 🔒 Schloss · Keypad Flur → Ereignis
Notruf – 9111 + 🌙 Nacht · alle Keypads → stiller Notruf
```

| Feld | Bedeutung |
|---|---|
| Name | z. B. „Außenlicht“ – erscheint im Logbuch und ist bei „Ereignis“ der Ereignistyp |
| Code | **2–8 Ziffern**. Darf keinem PIN, Bedrohungs-PIN oder Master-PIN gleichen (umgekehrt genauso) |
| Taste | 🏠 Haus, 🌙 Nacht, 🔒 Schloss oder 🔓 offenes Schloss. SOS geht nicht – sie schickt keinen Code mit |
| Keypad | alle oder ein bestimmtes |
| Aktion | **Ereignis** für eine eigene Automation, **Scharf schalten** mit einem Profil oder **stiller Notruf** |

Derselbe Code darf mit verschiedenen Tasten verschiedene Aktionen haben. Code + Taste darf es
aber nur einmal geben. Einen Eintrag antippen: ändern oder löschen.

**Am Keypad:** Code tippen, dann die Taste drücken. Das Keypad bekommt eine positive Rückmeldung
und zeigt danach wieder den Zustand. Ein Aktions-Code zählt **nie als Fehlversuch** – während
einer [PIN-Sperre](benutzer.md#sperre-nach-falschen-eingaben) ist er aber ebenfalls gesperrt.
Ist ein Code mit einer Taste als Aktions-Code eingerichtet, hat er Vorrang vor der normalen
Belegung der Taste.

**Kein Ausweis:** Ein Aktions-Code gehört keiner Person und ist nicht geheim – wer ihn kennt oder
errät, löst die Aktion aus. Deshalb kann er **nie unscharf schalten**, und du solltest nichts
Sicherheitskritisches damit auslösen (z. B. Türöffner, Garagentor).

### Aktion „Ereignis“: eigene Automation

Sobald es einen Aktions-Code mit „Ereignis“ gibt, hat Hauswacht die Entität
**`event.hauswacht_aktions_code`** („Hauswacht Aktions-Code“; bei englischer Sprache
`event.hauswacht_action_code`). Bei jedem Aktions-Code meldet sie ein Ereignis mit dem **Namen**
des Codes als Ereignistyp. Hauswacht selbst schaltet dabei nichts – was passiert, bestimmt deine
Automation.

**Beispiel – 7777 + Haus schaltet das Außenlicht für 5 Minuten ein:**

1. Aktions-Code anlegen: Name „Außenlicht“, Code `7777`, Taste 🏠 Haus, Aktion Ereignis.
2. Neue Automation. Auslöser: Zustand von „Hauswacht Aktions-Code“ (jedes Ereignis ändert ihn).
   Bedingung: Attribut „Ereignistyp“ ist „Außenlicht“. In YAML:

```yaml
triggers:
  - trigger: state
    entity_id: event.hauswacht_aktions_code
conditions:
  - condition: state
    entity_id: event.hauswacht_aktions_code
    attribute: event_type
    state: Außenlicht
actions:
  - action: light.turn_on
    target:
      entity_id: light.aussen
  - delay: "00:05:00"
  - action: light.turn_off
    target:
      entity_id: light.aussen
```

Warum nicht direkt „Attribut ändert sich auf Außenlicht“? Wird derselbe Code zweimal
hintereinander getippt, bleibt der Ereignistyp gleich – die Automation liefe dann nur beim ersten
Mal. Der Zustand (Zeitpunkt des letzten Ereignisses) ändert sich dagegen jedes Mal.

Die Entität hat außerdem die Attribute `keypad` (welches Keypad) und `test` (Testmodus an).

### Weitere Beispiele

**Ausprobieren, was ankommt:** Entwicklerwerkzeuge → Ereignisse → bei „Auf Ereignisse hören“
`hauswacht_event` eintragen → „Zuhören starten“ → am Keypad den Code tippen und die Taste
drücken. Es erscheint z. B.:

```yaml
event_type: hauswacht_event
data:
  type: ActionCode
  name: Außenlicht
  action: event
  control: Keypad Flur
  test: false
  area: all            # Keypad für alle Bereiche; sonst der Bereich des Keypads, z. B. garage
  area_name: Alle Bereiche
```

`area` ist der Bereich des **Bedienteils**: ein Keypad „für alle Bereiche“ meldet `all`, eines
für die Garage `garage`. Wer im Auslöser nach `area` filtert, muss deshalb den Bereich des Keypads
nehmen – nicht den Bereich, den der Code scharf schaltet.

Dieses Ereignis `hauswacht_event` kommt bei **jedem** Aktions-Code – auch bei „Scharf schalten“
und „stiller Notruf“. Als Auslöser ist es oft einfacher als die Entität, weil ein einziger
Auslöser genügt:

**A – Außenlicht mit nur einem Auslöser** (gleiche Wirkung wie oben):

```yaml
alias: Außenlicht per Keypad
triggers:
  - trigger: event
    event_type: hauswacht_event
    event_data:
      type: ActionCode
      name: Außenlicht
actions:
  - action: light.turn_on
    target:
      entity_id: light.aussen
  - delay: "00:05:00"
  - action: light.turn_off
    target:
      entity_id: light.aussen
mode: restart
```

Im Automations-Editor: Auslöser → **Manuelles Ereignis empfangen** → Ereignistyp
`hauswacht_event`, Ereignisdaten `type: ActionCode` und `name: Außenlicht`. `mode: restart`
sorgt dafür, dass ein erneuter Code die 5 Minuten neu startet.

**B – Ein Code, zwei Tasten: Licht an und aus.** Zwei Aktions-Codes anlegen: „Licht an“
(`7777` + 🏠 Haus) und „Licht aus“ (`7777` + 🌙 Nacht), beide mit Aktion Ereignis. Eine
Automation für beide:

```yaml
alias: Wohnzimmerlicht per Keypad
triggers:
  - trigger: event
    event_type: hauswacht_event
    event_data:
      type: ActionCode
      name: Licht an
    id: an
  - trigger: event
    event_type: hauswacht_event
    event_data:
      type: ActionCode
      name: Licht aus
    id: aus
actions:
  - choose:
      - conditions:
          - condition: trigger
            id: an
        sequence:
          - action: light.turn_on
            target:
              entity_id: light.wohnzimmer
      - conditions:
          - condition: trigger
            id: aus
        sequence:
          - action: light.turn_off
            target:
              entity_id: light.wohnzimmer
```

**C – Scharf schalten und gleichzeitig etwas anderes tun.** Aktions-Code „Gute Nacht“ (`11` +
🔒 Schloss) mit Aktion **Scharf schalten → Nacht**. Hauswacht schaltet scharf; diese Automation
fährt zusätzlich die Rollläden herunter:

```yaml
alias: Gute Nacht per Keypad
triggers:
  - trigger: event
    event_type: hauswacht_event
    event_data:
      type: ActionCode
      name: Gute Nacht
actions:
  - action: cover.close_cover
    target:
      area_id: wohnzimmer
```

**Testmodus ausnehmen:** Soll im [Testmodus](testmodus.md) nichts passieren, diese Bedingung
ergänzen:

```yaml
conditions:
  - condition: template
    value_template: "{{ not trigger.event.data.test }}"
```

### Aktion „Scharf schalten“ und „stiller Notruf“

- **Scharf schalten:** schaltet das gewählte Profil scharf, genau wie die Taste mit Profil – mit
  Prüfung offener Melder und Ausgangsverzögerung. Im Logbuch steht z. B. „Aktions-Code ‚Nacht per
  Code‘ (Keypad Flur)“. Das gilt auch, wenn unter PIN-Regeln „PIN beim Scharfschalten“ an ist:
  Wer einen Aktions-Code zum Scharfschalten anlegt, will genau das.
- **Stiller Notruf:** wichtige Push-Nachricht „Notruf am Keypad Flur“ an die Alarm-Empfänger –
  wie die SOS-Taste auf „still“, aber unauffällig über eine normale Taste. Keine Sirene, keine
  Anzeige am Keypad. Hat das Ereignis „Alarm“ keinen Empfänger, meldet die
  [Anlagenübersicht](uebersicht.md#prüfhinweise) das als wichtigen Hinweis (auch unter
  Reparaturen). In der Übersicht und im Ausdruck steht dieser Code nur als „verborgen“.

## Karten anlernen

RFID-Karten, Anhänger, Finger am [Fingerabdruck-Leser](#fingerabdruck-leser-esphome) und
Kennungen von [Türschlössern](#türschloss-z-b-nuki) verwaltest du an einer Stelle:
**Einstellungsseite → Personen und Bedienteile → Karten, Anhänger und Schloss-Kennungen.** Im Folgenden heißt all das
einfach „Karte“.

### Die Kartenliste

Die Liste zeigt jede Karte mit Name, Nummer, Besitzer und wann sie zuletzt geschaltet hat:

```
➕ Neue Karte anlernen (hinhalten)
⌨️ Kartennummer eintippen
🟢 Schlüsselbund (04A1B2C3) – Christian · zuletzt 07:12
🟢 Geldbörse (0011223344) – Christian · zuletzt 02.11.2026
⏸️ Ersatzkarte (A1B2C3D4E5) – Anna · deaktiviert
🟢 Nuki-App (Nuki-Benutzer 4711) – Anna · noch nie benutzt
```

🟢 = aktiv, ⏸️ = deaktiviert. „Zuletzt“ zeigt bei heute die Uhrzeit, sonst das Datum.

### Neue Karte anlernen

1. Alle Bereiche unscharf.
2. **Karten, Anhänger und Schloss-Kennungen → + Neue Karte anlernen.** Die Seite zeigt: *„Halte
   die Karte jetzt an ein Keypad oder einen Leser – sie erscheint hier von selbst.“* Bei einem
   Türschloss: einmal mit der neuen Kennung aufschließen.
3. **Sobald die Karte gelesen ist, geht es sofort weiter:** „✅ Karte erkannt“. Gib einen
   **Namen** ein (z. B. „Schlüsselbund“), wähle den **Benutzer**, speichern.

Am frient-Keypad reicht Hinhalten allein nicht – erst mit **Unscharf** schickt es die Nummer.
Statt hinzuhalten kannst du die Nummer auch eintippen.

Es zählt nur eine Karte, die **während** des Anlernens gelesen wird. Eine Karte aus einem früheren,
abgebrochenen Versuch wird nicht vorausgewählt.

**⌨️ Kartennummer eintippen:** ohne Warten. Hier stehen die zuletzt gelesenen unbekannten Karten
(innerhalb der Anlernzeit) als „neu, gelesen an Keypad um 18:04“ zur Auswahl, oder du tippst die
Nummer ein.

**Beispiel:** Anna bekommt einen neuen Anhänger. Karten und Anhänger → Neue Karte anlernen →
Anhänger ans Keypad im Flur halten, Unscharf drücken → „✅ Karte erkannt: 04C3D2E1“ → Name
„Schlüsselbund“, Benutzer „Anna“ → Absenden. Ab jetzt schaltet Annas Anhänger, und im Logbuch
steht „Anna · Schlüsselbund (Keypad Flur)“.

### Karte bearbeiten, deaktivieren, löschen

In der Liste eine Karte antippen:

| Feld | Bedeutung |
|---|---|
| Name der Karte | z. B. „Schlüsselbund“, „Geldbörse“, „Daumen rechts“, „Nuki-App“. Leer = ohne Namen |
| Gehört | Benutzer – hier gibst du eine Karte auch an jemand anderen weiter |
| Aktiv | aus = **deaktiviert**: die Karte schaltet nichts mehr, bleibt aber bekannt |
| Karte löschen | endgültig; danach wird sie wie eine unbekannte Karte abgelehnt |

**Deaktivierte Karte wird benutzt:** Sie schaltet nichts, am Keypad erscheint „ungültig“, und es
zählt als Fehlversuch für die [Sperre](benutzer.md#sperre-nach-falschen-eingaben). Du bekommst
eine Nachricht: *„Die deaktivierte Karte ‚Geldbörse‘ (Christian) wurde an Keypad Flur benutzt.“*
Bei einer deaktivierten Schloss-Kennung schaltet Hauswacht ebenfalls nichts und meldet es (ein
Türschloss zählt nicht als Fehlversuch).

**Beispiel – Geldbörse weg:** Christian vermisst seine Geldbörse mit dem Anhänger darin. Karten
und Anhänger → „Geldbörse (0011223344) – Christian“ → **Aktiv aus** → Absenden. Taucht die
Geldbörse wieder auf: Aktiv wieder an. Bleibt sie verschwunden: **Karte löschen**. Versucht in
der Zwischenzeit jemand, mit dem Anhänger unscharf zu schalten, weißt du es sofort.

Mit Namen zeigen außerdem Logbuch, Bedienfeld („Geändert von“) und Nachrichten, **welche** Karte
benutzt wurde – „Christian · Schlüsselbund (Keypad Flur)“ – und die
[Systemübersicht](uebersicht.md) zeigt „Schlüsselbund …B2C3“ (deaktivierte mit ⏸).

### Regeln beim Anlernen

- Die Anlernzeit ist einstellbar unter **Personen und Bedienteile → Bedienteile → Anlernzeit für
  neue Karten** (1–60 Minuten, 0 = Anlernen aus). Danach wird die Karte vergessen und muss noch
  einmal hingehalten werden.
- Unbekannte Karten zählen nicht als Fehlversuch für die [Sperre](benutzer.md#sperre-nach-falschen-eingaben).
- Kartennummern lassen sich auch eintippen (z. B. `041B4932E82880`; Groß-/Kleinschreibung und
  Trennzeichen egal). Codes mit 4–8 Ziffern könnten PINs sein und werden nie zum Anlernen
  angeboten – solche Karten-IDs eintippen.
- Eine Karte gehört genau einem Benutzer.

**Welche Karten gehen?** Das frient-Keypad liest 13,56-MHz-Karten nach ISO 14443 A (z. B. MIFARE
Classic, MIFARE DESFire, NTAG-Anhänger, viele Firmenausweise) und meldet deren feste Nummer
(UID).

**Nicht geeignet sind Zufallsnummern:** Handys und manche Ausweise im Datenschutz-Modus melden
bei jedem Lesen eine **andere** Nummer – erkennbar an 4 Byte, die mit `08` beginnen
(z. B. `+08837CF0`). Hauswacht bietet sie nicht zum Anlernen an, lehnt sie beim Speichern ab und
zeigt beim Anlernen einen Hinweis.

## NFC-Aufkleber (Companion App)

Ein NFC-Aufkleber an der Tür, gescannt mit der Home-Assistant-App. Der Aufkleber sagt nur **wo
und was** – ausgewiesen wird mit dem **Handy**: Das angemeldete Home-Assistant-Konto muss einem
berechtigten Hauswacht-Benutzer zugeordnet sein. Ein kopierter Aufkleber allein nützt also
nichts.

| Einstellung | Bedeutung |
|---|---|
| Aufkleber-ID | unter Einstellungen → Bereiche, Labels & Zonen → Tags (nach dem ersten Scannen) |
| Aktion | unscharf schalten, scharf schalten (Profil), umschalten (scharf ↔ unscharf) oder **Durchgang** (erlaubt das scharfe Profil ihn: [Durchgang](durchgang.md), sonst unscharf) |

Das Handy muss entsperrt sein. Kein Tastendruck nötig.

## RFID-Leser

Ein fester Leser, der das Home-Assistant-Ereignis „Tag gescannt“ auslöst – z. B. ein ESP32 mit
PN532 oder RC522 über ESPHome. Anders als beim Keypad reicht **Karte vorhalten**.

| Einstellung | Bedeutung |
|---|---|
| Geräte-ID | steht im Ereignis „Tag gescannt“ (`device_id`) |
| Aktion | unscharf schalten, scharf schalten (Profil), umschalten oder **Durchgang** (erlaubt das scharfe Profil ihn: [Durchgang](durchgang.md), sonst unscharf) |
| Anmeldung | **Karte** oder **Karte und PIN** (danach innerhalb von 30 s PIN desselben Benutzers an einem Keypad im selben Bereich) |

„Umschalten“ ist bequem, kann aber auch versehentlich scharf schalten. Einfache 125-kHz-Karten
sind leicht kopierbar – besser 13,56-MHz-Karten oder NFC per Handy.

### Fingerabdruck-Leser (ESPHome)

Ein Fingerabdruck-Sensor an einem ESP32 meldet den erkannten Finger wie eine Karte. In Hauswacht
ist er deshalb einfach ein **RFID-Leser** – ein Finger ist ein Ausweis wie eine Karte.

**Was du brauchst:**

| Teil | Beispiel | Preis etwa |
|---|---|---|
| Mikrocontroller | ESP32-Board (z. B. ESP32-DevKitC) | 5–10 € |
| Fingerabdruck-Sensor | **R503** (rund, mit LED-Ring; auch R307, ZFM-20) | 15–25 € |
| Software | [ESPHome](https://esphome.io/components/fingerprint_grow.html) (Komponente `fingerprint_grow`) | kostenlos |

Verkabelung: 3,3 V und GND vom ESP32; TX des Sensors an den RX-Pin des ESP32, RX des Sensors
an den TX-Pin; den WAKEUP-Draht an einen freien Pin (`sensing_pin`), damit der Sensor ein
Auflegen sofort erkennt.

**ESPHome-Konfiguration** (Gerät hier `fingerabdruck-flur`, Pins anpassen):

```yaml
esphome:
  name: fingerabdruck-flur

esp32:
  board: esp32dev

uart:
  rx_pin: GPIO16      # an TX des Sensors
  tx_pin: GPIO17      # an RX des Sensors
  baud_rate: 57600

fingerprint_grow:
  sensing_pin: GPIO4  # WAKEUP des Sensors
  on_finger_scan_matched:
    - if:
        condition:
          lambda: 'return confidence > 50;'
        then:
          - homeassistant.tag_scanned: !lambda 'return "FINGER" + to_string(finger_id);'
          - fingerprint_grow.aura_led_control:
              state: FLASHING
              speed: 25
              color: BLUE
              count: 2
  on_finger_scan_unmatched:
    - fingerprint_grow.aura_led_control:
        state: FLASHING
        speed: 25
        color: RED
        count: 2

api:
  actions:
    - action: finger_anlernen
      variables:
        finger_id: int
      then:
        - fingerprint_grow.enroll:
            finger_id: !lambda 'return finger_id;'
            num_scans: 2
    - action: finger_loeschen
      variables:
        finger_id: int
      then:
        - fingerprint_grow.delete:
            finger_id: !lambda 'return finger_id;'

sensor:
  - platform: fingerprint_grow
    fingerprint_count:
      name: "Gespeicherte Finger"
    last_finger_id:
      name: "Letzter Finger"
    last_confidence:
      name: "Letzte Übereinstimmung"
```

**Einrichten:**

1. **Finger im Sensor speichern:** Entwicklerwerkzeuge → Aktionen →
   `esphome.fingerabdruck_flur_finger_anlernen` mit `finger_id: 1` → zweimal denselben Finger
   auflegen. Für jeden Finger eine eigene Nummer (Platz 1, 2, 3 …). Am besten eine kleine Liste
   führen: 1 = Anna, rechter Zeigefinger; 2 = Anna, linker Zeigefinger; 3 = Ben …
2. **In Hauswacht:** Einstellungsseite → Personen und Bedienteile → **Bedienteil anlegen → RFID-/NFC-Leser** →
   Lesegerät „fingerabdruck-flur“ → Aktion z. B. „unscharf schalten“.
3. **Finger dem Benutzer zuordnen** wie eine [Karte](#neue-karte-anlernen): alles unscharf,
   Benutzer und PINs → Karten und Anhänger → Neue Karte anlernen (hinhalten) → Finger auflegen → „✅ Karte
   erkannt: FINGER1“ → Name „Zeigefinger rechts“, Benutzer „Anna“ → speichern. Oder `FINGER1`
   eintippen.

Gut zu wissen:

- **Kommt nichts an?** Unter Entwicklerwerkzeuge → Ereignisse `tag_scanned` anhören und einen
  Finger auflegen. Bleibt es still: Einstellungen → Geräte & Dienste → ESPHome → das Gerät →
  Konfigurieren → **„Dem Gerät erlauben, Home-Assistant-Aktionen auszuführen“** einschalten.
- Die Fingerabdrücke selbst bleiben **im Sensor**. Home Assistant und Hauswacht sehen nur die
  Nummer des Platzes („FINGER1“).
- Ein **unbekannter Finger** schickt nichts – er zählt deshalb auch nicht als Fehlversuch.
- `confidence > 50` ist die Mindest-Übereinstimmung; höher = weniger Fehlerkennungen, aber
  öfter „nicht erkannt“. Zusätzlich lässt sich am Sensor `security_level` (1–5) einstellen.
- Die LED zeigt nur, ob der **Sensor** den Finger erkannt hat – nicht, ob Hauswacht unscharf
  geschaltet hat (z. B. fehlendes Recht oder Sperre). Das zeigen Keypad, Alarmkarte und Logbuch.
- **Mehr Sicherheit:** Anmeldung „Karte und PIN“ – nach dem Finger innerhalb von 30 s den PIN am
  Keypad.
- **Sicherheit des Lesers:** Wer den ESP32 oder sein WLAN übernimmt, kann jede Nummer schicken.
  Den Leser deshalb **innen** anbringen (z. B. im Flur in Reichweite der Eingangsverzögerung),
  ESPHome mit API-Schlüssel und Passwort betreiben und das Gehäuse gegen Öffnen sichern. Außen an
  der Tür ist ein Schloss mit eigenem Fingerabdruck-Leser (z. B. Nuki Keypad 2.0, siehe
  [Türschloss](#türschloss-z-b-nuki)) die robustere Wahl.
- Ein **verlorener oder verletzter Finger**: den Platz im Sensor löschen
  (`esphome.fingerabdruck_flur_finger_loeschen`) und die Kennung beim Benutzer entfernen.

> Diese Anleitung folgt der ESPHome-Dokumentation; mit echter Hardware erprobt ist sie bei
> Hauswacht noch nicht. Rückmeldungen gern als [Issue](https://github.com/schlusenbaum/hauswacht/issues).


## Taster

Ein Taster – z. B. ein Zigbee-Taster im Hausflur – schaltet ein Alarmprofil **scharf**, mit der
Ausgangsverzögerung des Profils. Drücken, rausgehen, fertig.

> Ein Taster weist **niemanden** aus: Wer davorsteht, ist unbekannt. Deshalb schaltet er **nur
> scharf** – nie unscharf, und er beendet nie einen Alarm.

**Einrichten:** Einstellungsseite → Personen und Bedienteile → **Bedienteil anlegen → Taster**.

1. Name, Bereich und den **Taster** wählen:
   - eine **Ereignis-Entität** (`event.…`) – so liefern Zigbee2MQTT (neuere Versionen), Hue,
     Shelly und Matter ihre Taster, oder
   - einen **Aktions-Sensor** (`sensor.…_action`), wie ihn ältere Zigbee2MQTT-Versionen anlegen.
2. Im zweiten Schritt legst du fest, welche **Druckart** welches Profil schaltet:
   - Bei einer Ereignis-Entität zeigt Hauswacht die Druckarten des Geräts selbst an (z. B.
     `single`, `double`, `long`). Leer lassen = diese Druckart tut nichts.
   - Bei einem Aktions-Sensor trägst du den **Wert** ein, den der Sensor beim Drücken annimmt.
     So findest du ihn: Entwicklerwerkzeuge → Zustände → Sensor suchen → Taster drücken → der
     Wert erscheint kurz (z. B. `single`, `double`, `hold`).

**Beispiel:** Taster im Flur, einfach → „Abwesend“, doppelt → „Nacht“. Im Logbuch steht
„geändert von: Taster Flur“.

Gut zu wissen:

- Ist schon ein Profil scharf, tut der Taster nichts – er schaltet nie über ein anderes Profil
  hinweg um.
- Sind Melder offen, gilt die Einstellung des Profils (z. B. „verweigern“) – dann kommt die
  übliche Meldung „nicht scharf geschaltet“.
- Verlangen die PIN-Regeln einen **PIN zum Scharfschalten**, schaltet der Taster **nicht** –
  er kann keinen PIN eingeben. Hauswacht schickt dann eine Systemmeldung.
- Kommt der Taster nach einem Funkausfall wieder, zählt das nicht als Drücken.
- Jedes Drücken meldet das Ereignis `ButtonPressed` (siehe [Referenz](referenz.md#bedienung-1)).
  Dessen Feld `area` ist der Bereich des Tasters – bei einem Taster „für alle Bereiche“ `all`.
  Dasselbe gilt für Türschloss und Notruf-Taste.
- Ein Taster **außen** an der Tür ist nicht verboten, aber dann kann jeder Vorbeigehende scharf
  schalten (und wer drinnen ist, löst später Alarm aus). Besser innen anbringen.

## Türschloss (z. B. Nuki)

Ein elektronisches Türschloss schaltet **unscharf, wenn ein bekannter Benutzer aufschließt** –
mit dessen Rechten je Bereich. Im Logbuch steht z. B. „Anna (Haustür-Schloss)“. Optional
schaltet **Abschließen von außen** ein Profil scharf.

Mit **„Aufschließen bei scharf: Durchgang“** bleibt die Anlage scharf, wenn das scharfe Profil
einen [Durchgang](durchgang.md) erlaubt: Aufschließen in der Eingangsverzögerung lässt herein,
Aufschließen vorher öffnet den Durchgang zum Rausgehen (die erste Tür, die danach aufgeht).
Erlaubt das Profil keinen Durchgang (z. B. „Abwesend“), schaltet Aufschließen wie bisher
unscharf.

Dafür muss das Schloss sagen, **wer** aufgeschlossen hat. Das bloße Öffnen der Tür oder
„aufgeschlossen“ ohne Person reicht nie.

> Hauswacht **liest nur mit** und schaltet das Schloss selbst nie.

### Was Hauswacht verlangt

Hauswacht schaltet nur unscharf, wenn **beides** zusammenkommt, höchstens 30 Sekunden
auseinander:

1. eine **Kennung** vom Schloss, die einem Hauswacht-Benutzer gehört (z. B. sein
   Nuki-App-Zugang oder sein Keypad-Code), und
2. das Schloss wechselt in Home Assistant wirklich auf **„aufgeschlossen“** bzw. „offen“.

Warum beides? Manche Nuki-Modelle melden auch einen **falsch** eingetippten Keypad-Code als
Aufschließen (ein bekannter Firmware-Fehler). Ohne tatsächliche Bewegung des Schlosses passiert
deshalb nichts.

**Nie unscharf**

| Situation | Warum |
|---|---|
| Kennung unbekannt oder fehlt | Wer es war, ist nicht klar (Hauswacht meldet das per Systemmeldung, wenn scharf) |
| Drehknauf oder Knopf am Schloss (innen) | kein Ausweis |
| Zeitsteuerung, automatisches Abschließen | keine Person |
| Aufschließen über Home Assistant, HomeKit oder MQTT | kein Ausweis an der Tür |
| Tür geht nur auf | kein Aufschließen |
| Benutzer darf nicht unscharf schalten oder ist abgelaufen | Rechte gelten wie am Bedienfeld |

### Einrichten mit Nuki über MQTT

Voraussetzung: Nuki Smart Lock (3.0 Pro, 4. oder 5. Generation) mit eingeschaltetem **MQTT**
in der Nuki-App und die MQTT-Integration in Home Assistant. Das Schloss selbst ist meist schon
über MQTT oder die Nuki-Integration als `lock.…` in Home Assistant.

1. **Einstellungsseite → Personen und Bedienteile → Bedienteil anlegen → Türschloss.**
2. Ausfüllen:

| Einstellung | Beispiel | Bedeutung |
|---|---|---|
| Name | Haustür-Schloss | erscheint im Logbuch |
| Bereich | Haus | welcher Bereich unscharf wird |
| Schloss | `lock.haustuer` | die Entität in Home Assistant |
| Quelle | Nuki über MQTT | |
| MQTT-Topic | `nuki/3A1B2C4D` | Basis-Topic des Schlosses (die Nuki-ID in Hex), **ohne** `/lockActionEvent` |
| Beim Abschließen scharf | leer oder „Abwesend“ | optional, siehe unten |

Hauswacht liest dann `nuki/3A1B2C4D/lockActionEvent`. Das Nuki schickt dort bei jeder Aktion
fünf Zahlen, z. B. `1,0,52653,0,0`:

| Stelle | Bedeutung | Beispiel |
|---|---|---|
| 1 | Aktion: 1 = aufschließen, 2 = abschließen, 3 = öffnen, 4 = Lock 'n' Go, 6 = voll abschließen | `1` |
| 2 | Auslöser: 0 = App/Bluetooth, Keypad, Fob; 2 = Knopf am Schloss; 3 = Zeitsteuerung; 6 = automatisch; 171 = HomeKit/Matter; 172 = MQTT | `0` |
| 3 | Auth-ID: wer (App-Zugang) | `52653` |
| 4 | Code-ID: welcher Keypad-Code (0 = keiner) | `0` |
| 5 | Zusatz (z. B. Fingerabdruck, Auto-Unlock) | `0` |

Hauswacht zählt nur Auslöser **0**. Aus Code-ID bzw. Auth-ID wird die Kennung, die beim
Benutzer erscheint: „Nuki-Keypad-Code 8192“ bzw. „Nuki-Benutzer 52653“ (gespeichert als
`NUKICODE8192` bzw. `NUKIAUTH52653`).

**Fingerabdruck am Nuki Keypad 2.0:** Ein Fingerabdruck kommt wie ein Keypad-Code an (eigene
Code-ID, an Stelle 5 eine `2` für „Fingerabdruck“). Er wird also genauso als „Nuki-Keypad-Code …“
angelernt – das ist der einfachste Weg zu einem Fingerabdruck an der Haustür.

### Kennungen anlernen

Wie bei [Karten](#karten-anlernen):

1. Alle Bereiche unscharf.
2. Personen und Bedienteile → Karten, Anhänger und Schloss-Kennungen → **Neue Karte anlernen**.
3. Mit der App, dem Keypad-Code oder dem Fingerabdruck **einmal aufschließen** – die Seite
   zeigt die Kennung sofort → Name z. B. „Nuki-App“, Benutzer wählen → speichern.

Schon vorher aufgeschlossen? Dann „Kartennummer eintippen“: Dort steht die Kennung als
„Nuki-Benutzer 52653 (neu, gelesen an Haustür-Schloss um 18:04)“ zur Auswahl.

Am besten jede Person einzeln anlernen, damit klar ist, welche Kennung zu wem gehört. Jeder
Keypad-Code und jeder App-Zugang ist eine eigene Kennung; ein Benutzer kann mehrere haben.

### Abschließen = scharf (optional)

Ist ein Profil eingetragen, schaltet **Abschließen von außen** durch einen bekannten Benutzer
mit Recht zum Scharfschalten dieses Profil scharf – aber nur, wenn alles unscharf ist.
Automatisches Abschließen, Zeitsteuerung und der Knopf innen zählen nicht.

> Achtung: „Von außen“ heißt für Nuki nur „per App, Keypad oder Fob“. Wer abends **im Bett per
> App** abschließt, schaltet damit ebenfalls scharf. Für die Haustür daher eher ein Profil wie
> „Abwesend“ wählen und die App dafür nicht von innen nutzen – oder das Feld leer lassen.

### Andere Schlösser (allgemeine Quelle)

Für Schlösser, die den Benutzer als **Sensor** oder **Ereignis** in Home Assistant zeigen
(z. B. einen Sensor „zuletzt geöffnet von“ oder ein Ereignis mit dem Benutzernamen):

| Einstellung | Beispiel |
|---|---|
| Quelle | Allgemein |
| Sensor oder Ereignis mit der Kennung | `sensor.haustuer_benutzer` |

Ändert sich der Wert (bzw. kommt ein Ereignis) und schließt das Schloss innerhalb von
30 Sekunden auf, gilt der Wert als Kennung – z. B. „Anna“ wird zu `LOCKANNA`. Angelernt wird
wie oben.

Wichtig: Der Sensor darf seinen Wert **nur beim Aufschließen** ändern. Zeigt er z. B. auch
an, wer zuletzt **abgeschlossen** hat, würde das Abschließen von Anna und ein späteres
Aufschließen durch einen Unbekannten zusammengezählt, wenn beides innerhalb von 30 Sekunden
passiert.

## Sicherheit

- Eine reine Kartennummer ist kein starker Schutz: Wer sie ausliest (z. B. im Vorbeigehen), kann
  sie kopieren. Für mehr Sicherheit „Karte und PIN“ verwenden.
- Am Keypad schützt der nötige Tastendruck davor, dass eine Karte in der Jackentasche etwas
  schaltet.
- Verlorene Karte: beim Benutzer entfernen oder den Benutzer auf „Aktiv: aus“ stellen.
- Der Bedrohungs-PIN wirkt auch am Keypad.
- **MQTT-Schnittstelle:** dieselben Regeln wie am Keypad; gespeicherte Befehle werden nie
  ausgeführt. Den Broker absichern – siehe [Sicherheit: den Broker absichern](#sicherheit-den-broker-absichern).
- **Allgemeines Keypad:** Es gelten dieselben Regeln wie am Zigbee2MQTT-Keypad – unscharf nur mit
  PIN oder Karte. Nur angelegte Keypads werden angenommen, und nur Automationen, Skripte, Geräte
  und Administratoren dürfen die Aktion aufrufen. Ob der PIN irgendwo im Klartext landet, hängt
  vom Übersetzer ab – siehe [PINs außerhalb von Hauswacht](#pins-außerhalb-von-hauswacht).
- **Türschloss:** Wer das Handy mit der Nuki-App **und** den Zugang dazu hat, schaltet mit dem
  Aufschließen unscharf – genau wie er die Tür öffnen kann. Verlorenes Handy: in der Nuki-App
  den Zugang sperren **und** die Kennung beim Benutzer entfernen.
- **Taster:** schalten nur scharf; sie sind kein Ausweis.
