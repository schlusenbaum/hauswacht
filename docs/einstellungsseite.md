# Einstellungsseite „Hauswacht“ in der Seitenleiste

**Deutsch** | [English](en/settings-page.md)

> **Vorabversion:** Die Seite wächst in Stufen. In dieser Stufe **zeigt** sie die ganze
> Einrichtung an; **bearbeitet** wird weiter im Einstellungsdialog (Knopf „Im Dialog
> bearbeiten“ oben rechts). Die nächsten Stufen bringen das Bearbeiten direkt auf der Seite.

Der Einstellungsdialog zeigt immer nur einen Schritt. Die Seite **Hauswacht** in der
Seitenleiste von Home Assistant zeigt dagegen alles auf einen Blick: welche Melder in welcher
Gruppe stecken, in welchem Profil sie scharf sind, wer welche Nachricht bekommt.

- Nur für **Administratoren** sichtbar.
- **Zusätzlich** zum Dialog und zum [Einrichtungsassistenten](assistent.md) – alle Wege nutzen
  dieselben Einstellungen. Was im Dialog geändert wird, steht nach „Neu laden“ sofort auf der
  Seite.
- Ausblenden: Konfigurieren → System → **Einstellungsseite in der Seitenleiste** → Haken weg.

## Die Reiter

| Reiter | Inhalt |
|---|---|
| **Übersicht** | Prüfhinweise (z. B. „Profil ohne Empfänger“) und der Zustand je Bereich |
| **Melder** | Alle Melder **nach Meldergruppen**, mit Typ, Zustand und Batterie – und je Profil eine Spalte (Matrix, siehe unten). Darunter [Besondere Melder](melder.md#melder-mit-kippstellung-gekippt) und [Immer aktiv](melder.md#immer-aktive-melder) |
| **Profile** | Jedes Profil mit Gruppen, Regeln, Zeiten, Reaktion, Empfängern und Automatik |
| **Auslöseregeln** | Jede Regel als Satz und wo sie gilt |
| **Alarmgeber** | Sirenen mit ihren Fähigkeiten und dem letzten Test |
| **Benachrichtigungen** | Empfänger je Ereignis, Lautsprecher, Ruhezeit |
| **Personen und Bedienteile** | Benutzer mit Rechten und Ausweisen (PINs werden nie angezeigt), Bedienteile, Aktions-Codes |
| **System** | Funkstille, Funknetz, Anlernen, Neustart, Heimkehr |

Die Seite merkt sich den zuletzt gewählten Reiter (nur in diesem Browser).

## Die Matrix „Melder × Profile“

Im Reiter **Melder** steht jeder Melder in einer Zeile, darüber seine Meldergruppe. Für jedes
Profil gibt es eine Spalte:

| Zeichen | Bedeutung |
|---|---|
| ✓ | löst in diesem Profil **allein** aus |
| R | zählt nur in **Auslöseregeln** dieses Profils |
| – | in diesem Profil **ausgenommen** |
| leer | wird in diesem Profil nicht überwacht |

Gruppen mit Erschütterungsmeldern zeigen ihren [Fehlalarmschutz](melder.md#erschütterungsmelder)
(„Alarm bei 2 Meldungen in 60 s“). Das **Suchfeld** filtert nach dem Namen.

Beispiel: Steht beim Bewegungsmelder im Flur in der Spalte „Nacht“ ein **–**, ist er nachts
ausgenommen – du kannst nachts durch den Flur gehen, ohne Alarm.

## Gut zu wissen

- Die Seite **schaltet nichts** – weder Sirenen noch Geräte – und ändert in dieser Stufe auch
  keine Einstellungen.
- Gezeigt wird der Stand beim Öffnen; „Neu laden“ (Pfeil oben) holt den aktuellen.
- Dieselben Inhalte gibt es zum Ausdrucken in der Karte [Hauswacht Übersicht](uebersicht.md).
- Auf dem Handy geht die Seite auch; breite Tabellen lassen sich seitlich schieben.
