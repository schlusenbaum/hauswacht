# ADR 0016: Anwesenheit in der Testkarte – simulieren und sehen, warum

- Status: angenommen (Umsetzung in 0.63)
- Datum: 2026-11-24
- Baut auf: [ADR 0015 Rückkehr](0015-rueckkehr.md); Testmodus und Simulation der Melder (Testkarte)

## Kontext

Seit 0.61 hängt viel an der Anwesenheit: „Scharf, wenn alle weg“, „Bei Rückkehr“ (unscharf mit
Türbeleg, reinlassen), „weg“ nur mit Beleg, Annäherung. Ausprobieren lässt sich das heute nur in
echt – rausgehen, warten, wiederkommen. Und wenn es nicht schaltet, sieht man nicht, **warum**:
Ein Tester im Forum (Martin) ging aus dem Haus, „Abwesend“ wurde nicht scharf – ob seine Frau
noch als zuhause galt, ein Signal „nicht verfügbar“ war oder der Beleg fehlte, war nirgends zu
sehen.

Für Melder gibt es die Testkarte schon: Im Testmodus lassen sie sich simulieren, nur für
Hauswacht, ohne dass Geräte oder andere Automationen etwas merken.

## Entscheidung

### 1. Abschnitt „Anwesenheit“ – Status immer sichtbar

In der Testkarte und auf der Einstellungsseite (System → Anwesenheit und Heimkehr-Beobachtung)
steht jede Person, die in einer Profil-Automatik vorkommt („Scharf, wenn alle weg“, „Bei
Rückkehr“), mit ihrem Status **für Hauswacht** und dem Grund:

| Status | Beispiel für den Grund |
|---|---|
| zuhause | „WLAN: zuhause“ |
| weg | „Beleg: Tür + Ortung außerhalb (17:22)“, „Beleg: frische Ortung“, „Beleg: Tür + Signal“ |
| unbekannt | „alle Signale weg, aber kein Beleg“, „Ping nicht verfügbar“ |
| nähert sich | „Richtung: nähert sich (vor 3 min) – verlängerte Eingangsverzögerung bis 18:17“ |

Darunter je Profil, was die Automatik daraus macht: „Abwesend: alle weg → scharf in 14:32“,
„Abwesend: wartet auf Petra (unbekannt)“. Das gilt **auch ohne Testmodus** (nur ansehen, ohne
Knöpfe) – es ist das Werkzeug zur Fehlersuche.

### 2. Simulieren – nur im Testmodus

Knöpfe je Person:

| Knopf | Wirkung für Hauswacht |
|---|---|
| **Zuhause** | Person gilt als zuhause |
| **Weg** | Person gilt als weg **mit Beleg** |
| **Weg ohne Beleg** | alle Signale „weg“, aber kein Beleg – wie ein schlafendes Handy; damit prüft man, dass dann **nicht** scharf geschaltet wird |
| **Nähert sich** | Richtung „nähert sich“ – für die verlängerte Eingangsverzögerung |
| **Echt** | zurück auf die echten Signale |

Dazu **„Wartezeit überspringen“**, solange bei einem Profil „scharf in …“ läuft. Die Wartezeit
selbst wird im Testmodus **nicht** verkürzt – getestet wird das echte Verhalten, nur schneller.

Regeln wie bei den Meldern:

- Nur im Testmodus; **Testmodus aus = alles echt**, nach einem Neustart ebenso.
- Gilt **nur für Hauswacht**: Die Personen und Geräte in Home Assistant bleiben unverändert,
  andere Automationen merken nichts.
- Simulierte An- und Abwesenheit fließt **nicht in die Messungen** der Heimkehr-Beobachtung –
  sonst wären die Empfehlungen verfälscht.
- Sirenen bleiben im Testmodus wie immer technisch gesperrt.
- Dasselbe als Aktion (`hauswacht.simulate_presence`) für eigene Testabläufe.

### 3. Nicht in diesem Schritt

- **Uhrzeit-Automatik** („Scharf um“, Zeitplan) simulieren – vorerst nicht; nur Anwesenheit.
- Wartezeit im Testmodus verkürzen – bewusst nicht (siehe oben).

## Folgen

- Die Simulation setzt dort an, wo Hauswacht die Anwesenheit bewertet (Automatik und
  Beobachtung): Ein simulierter Wert ersetzt die Bewertung der echten Signale für diese Person.
  „Weg“ setzt den Beleg, „Weg ohne Beleg“ ausdrücklich keinen.
- Die Statusanzeige braucht den **Grund** je Person – die Bewertung muss ihn mitliefern (welches
  Signal zuhause meldet, welcher Beleg gilt, welches Signal fehlt).
- Reihenfolge: 0.62 Erklärungen, **0.63 diese Testkarte**, 0.64 Ausgangserkennung (ADR 0014).
