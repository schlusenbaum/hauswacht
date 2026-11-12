# Bedienung und Dashboard

## Scharf und unscharf schalten

| Weg | Scharf | Unscharf |
|---|---|---|
| **Bedienfeld** (`alarm_control_panel.hauswacht`, z. B. als Kachel oder Alarmkarte) | Knöpfe der Profile, denen ein Knopf zugeordnet ist | „Unscharf“ – mit PIN, sobald irgendein PIN existiert |
| **Auswahlliste + Knopf** (`select.hauswacht_profil`, `button.hauswacht_scharf_schalten`) | jedes Profil, auch ohne Knopf | – |
| **Knopf „Unscharf schalten“** (`button.hauswacht_unscharf_schalten`) | – | sofort, ohne PIN-Abfrage (siehe unten) |
| **Push-Nachricht** | „Jetzt scharf“ (Erinnerung), „Trotzdem scharf“ / „Erneut versuchen“ | Knopf „Unscharf schalten“ bzw. „Alarm beenden“, siehe [Benachrichtigungen](benachrichtigungen.md#push-knopf-unscharf-schalten) |
| **Bedienteile** | Keypad-Taste + PIN/Karte, NFC-Aufkleber, RFID-Leser | ebenso, siehe [Bedienteile](bedienteile.md) |
| **Automatik** | Uhrzeit, alle weg | Uhrzeit, Heimkehr – siehe [Automatik](profile.md#automatik) |
| **Aktion** | `hauswacht.arm` mit Profilnamen | `alarm_control_panel.alarm_disarm` |
| **Sprachassistent** | über das Bedienfeld | über das Bedienfeld, nur mit PIN freigeben |

Beim Scharfschalten prüft Hauswacht offene und ausgefallene Melder nach den Regeln des Profils.
Wird abgelehnt, nennt die Meldung die Melder; mit einer Push-Nachricht kommen die Knöpfe
„Trotzdem scharf“ und „Erneut versuchen“.

### Trotzdem scharf schalten

Erlaubt ein Profil offene oder ausgefallene Melder nur „nach Bestätigung“, verweigert das normale
Bedienfeld das Scharfschalten. Bestätigen geht mit dem Knopf **„Trotzdem scharf schalten“**
(`button.hauswacht_trotzdem_scharf_schalten`, für das gewählte Profil) oder der Aktion:

```yaml
action: hauswacht.arm
target:
  entity_id: alarm_control_panel.hauswacht
data:
  profile: Nacht
  confirm: true
```

Offene Melder werden dabei **überbrückt**, also bis zum Unscharfschalten nicht überwacht. Steht
das Profil auf „verweigern“, lehnt Hauswacht auch die Bestätigung ab.

## Alarm beenden

**„Unscharf schalten“ während eines Alarms beendet nur den Alarm** – egal ob über Karte,
Bedienfeld, Push-Nachricht oder Automation:

- Sirenen aus (die Brandsperre gilt weiter), Anzeige wieder „Scharf“ mit demselben Profil.
- Was in diesem Moment offen ist (z. B. die Tür, durch die jemand kam), wird **überbrückt, bis es
  wieder geschlossen ist**, und danach wieder überwacht. Alle anderen Melder bleiben scharf.
- Meldung „Alarm beendet … bleibt scharf. Bis zum Schließen nicht überwacht: …“.
- **Erst ein zweites „Unscharf schalten“ schaltet wirklich unscharf.**
- Ist ein PIN eingestellt, wird er auch zum Beenden abgefragt.

Zwei Knöpfe für Dashboards:

| Knopf | Wirkung |
|---|---|
| **Unscharf schalten** (`button.hauswacht_unscharf_schalten`) | Sofort unscharf – auch während eines Alarms, ohne Zwischenschritt |
| **Alarm beenden** (`button.hauswacht_alarm_beenden`) | Nur während eines Alarms: Alarm aus, Profil bleibt scharf |

Knöpfe können keinen PIN abfragen. Sobald ein PIN existiert, sind sie deshalb **nicht
verfügbar** – außer unter [PIN-Regeln](benutzer.md#pin-regeln) ist „Dashboard-Knöpfe trotz PIN
erlauben“ (alle Knöpfe) bzw. „Alarm ohne PIN beenden“ (nur „Alarm beenden“) an.

> Abwägung: Wer ein entsperrtes Dashboard in der Hand hat, kann dann ohne PIN bedienen. An die
> Knöpfe kommen aber nur angemeldete Home-Assistant-Benutzer, und nach „Alarm beenden“ bleibt
> die Anlage scharf – jeder weitere Melder löst sofort wieder aus.

## Beispielkarte

[`examples/dashboard/hauswacht-karte.yaml`](../examples/dashboard/hauswacht-karte.yaml) nutzt nur
Standardkarten von Home Assistant (ab 2026.5) und funktioniert in jeder Ansichtsart.

**Einfügen:** Dashboard bearbeiten → Karte hinzufügen → ganz unten **Manuell** → Inhalt der
Datei einfügen → Speichern. Die Entitäts-IDs gelten für eine deutschsprachige Instanz; die
englischen stehen oben in der Datei.

| Teil | Wann sichtbar | Zweck |
|---|---|---|
| Kachel „Hauswacht“ | immer | Zustand mit Symbol des aktiven Profils |
| „Profil“ und „Scharf schalten“ | nur unscharf | Profil wählen und scharf schalten |
| „Offen: …“ und „Trotzdem scharf“ | nur unscharf **und** Melder offen | Offene Melder mit Raum; gewähltes Profil mit Bestätigung scharf schalten |
| „Unscharf schalten“ | scharf, Verzögerung oder Alarm | während eines Alarms beendet er nur den Alarm |
| Kachel „Hauswacht-System“ | nur wenn der Systemstatus nicht OK ist | Hinweis auf ausgefallene Melder oder Störungen |

Die Symbolleiste mit allen Bedienfeld-Knöpfen (`alarm-modes`) ist weiter möglich, doppelt aber
die Profilauswahl.

## Karte „Hauswacht Einstellungen“

![Karte Hauswacht Einstellungen](images/einstellungen-karte.png)

Hauswacht bringt die Karte mit; sie wird automatisch geladen (kein Eintrag unter „Ressourcen“).
Dashboard bearbeiten → **Karte hinzufügen** → **„Hauswacht Einstellungen“** – oder in YAML:

```yaml
type: custom:hauswacht-einstellungen-card
title: Einstellungen   # optional
```

Die Karte zeigt die [Profil-Einstellungen](#profil-einstellungen-im-dashboard) des gewählten
Profils und findet die Entitäten selbst; umbenannte Entitäten stören nicht. Im scharfen Zustand
sind alle Einstellungen gesperrt.

## Karte „Hauswacht Test“

Zum gefahrlosen Durchspielen im Testmodus, mit Sirenentest und „Falscheingaben zurücksetzen“ –
siehe [Testmodus und Testkarte](testmodus.md#karte-hauswacht-test).

## Profil-Einstellungen im Dashboard

Kleinigkeiten lassen sich ohne den Einstellungsdialog ändern. Die Entitäten stehen am Gerät
„Hauswacht“ unter **Konfiguration**:

1. **Profil bearbeiten** (`select.hauswacht_profil_bearbeiten`): welches Profil die folgenden
   Einstellungen zeigen und ändern.
2. Zahlen: Ausgangs- und Eingangsverzögerung, Dauer der Alarmreaktion, Alarmzyklen, Wartezeit
   bei Abwesenheit.
3. Auswahl: offene bzw. ausgefallene Sensoren beim Scharfschalten, Sirenenton, Lautstärke.
4. Schalter: Stiller Alarm, Sabotage löst Alarm aus, Unscharf beim Heimkommen.
5. Uhrzeiten: Automatisch scharf um / unscharf um.

- Änderungen nur im unscharfen Zustand; scharf sind die Einstellungen „nicht verfügbar“.
- Jede Änderung wird sofort gespeichert und im Logbuch mit Benutzer festgehalten.
- Name, Symbol, Knopf, Meldergruppen, Sirenen, Empfänger, Personen und Wochentage sowie das
  **Entfernen** einer Uhrzeit gehen nur im Einstellungsdialog.
- Tipp: Eine Dashboard-Seite dafür nur für Administratoren sichtbar machen.

## Eigene Karten

Nützliche Entitäten – alle weiteren in der [Referenz](referenz.md):

| Entität | Inhalt |
|---|---|
| `alarm_control_panel.hauswacht` | Zustand; Attribute `profile_name`, `timer_ends_at`, `open_sensors`, `bypassed_sensors` … |
| `binary_sensor.hauswacht_offene_sensoren` | „Offen“, sobald ein Melder einer Meldergruppe offen ist; Attribut `names` (mit Raum) |
| `sensor.hauswacht_systemstatus` | `ok`, `degraded`, `fault` |
| `select.hauswacht_profil` | Gewähltes bzw. aktives Profil |
| `switch.hauswacht_testmodus` | Testmodus |
