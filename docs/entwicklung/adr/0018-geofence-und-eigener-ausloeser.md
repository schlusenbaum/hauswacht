# ADR 0018: Geofence als Ortung, eigener Auslöser für „alle weg“, „Warum nicht scharf?“

- Status: angenommen (0.65.0b4)
- Anlass: Rückmeldung eines Testers (simon42-Forum): „Scharf, wenn alle weg“ greift bei ihm nicht
  zuverlässig, obwohl Alarmo mit denselben Auslösern läuft.

## Ausgangslage

Seit ADR 0015 gilt jemand nur **mit Beleg** als weg: frische Ortung mit Koordinaten außerhalb,
Tür + Ortung, oder (unsicher, nur wenn erlaubt) „Tür + Signal“. Ein schlafendes Handy oder ein
WLAN-Aussetzer macht so niemanden abwesend.

Manche Haushalte haben aber **Geofence-Tracker ohne Koordinaten**: z. B. die Anwesenheit aus Apple
Home, über einen Template-Device-Tracker nach Home Assistant gebracht. Die melden nur „home“ oder
„not_home“ – ermittelt aber vom Standort des Handys, nicht vom WLAN. Für Hauswacht sind das bisher
einfache Signale: ohne Koordinaten kein Beleg. Mit „Tür + Signal“ greift es nur, wenn der
Geofence-Austritt im Zeitfenster nach der Tür kommt – Geofences melden oft später.

Alarmo nimmt einfach „not_home“. Das ist bequemer, aber genau das, was ADR 0015 vermeiden will.

## Entscheidung

### 1. „Zählt als Ortung“ je Signal (Geofence)

Unter System → Anwesenheit lässt sich jedes Signal einer Person als **Ortung** markieren
(`away_proof_geofence`: Liste von Entitäten). Ein solches Signal zählt wie eine genaue Ortung:

- Zustand nicht „home“ (und nicht unbekannt/nicht verfügbar) = **draußen**, sicher;
- frisch ist sie, solange ihre letzte Meldung im Zeitfenster für den Beleg liegt
  (wie bei Koordinaten);
- die Person gilt damit als „kann geortet werden“ (Assistent, Check-up, Szenarien).

Markieren soll man nur Quellen, die den **Standort** auswerten (Geofence). Ein WLAN- oder
Ping-Signal als Ortung zu markieren hebelt den Schutz gegen schlafende Handys aus – darauf weist
die Seite beim Markieren hin, und die Doku sagt es deutlich.

### 2. Eigener Auslöser für „alle weg“

Je Profil kann statt Personen eine **eigene Entität** „alle weg“ melden (`auto_away_entity`, dazu
`auto_away_entity_state`: welcher Zustand „alle weg“ heißt, Standard „on“). Ist sie gesetzt, gilt
sie **statt** der Personen: Zeigt sie den gewählten Zustand, ist „alle weg“ erfüllt, sonst nicht;
unbekannt oder nicht verfügbar zählt nie als weg. Wartezeit, Sicherheitsregeln (nur aus
„unscharf“, offene Melder nie automatisch bestätigt) bleiben gleich.

Damit prüft Hauswacht nicht mehr selbst, ob wirklich alle weg sind – die Verantwortung liegt bei
der Entität. Der Assistent zeigt dazu eine **Warnung** im Check-up und im Profil. Die
Szenario-Vorschau spielt „alle gehen weg“ und „Handys schlafen ein“ für solche Profile nicht
durch (sie kennt die Regeln der Entität nicht) und sagt das.

„Bei Rückkehr“ bleibt bei Personen.

### 3. „Warum nicht scharf?“

Die Anzeige „Wer gilt gerade als zuhause?“ unter System → Anwesenheit sagt bei „kein Beleg“
zusätzlich, **was fehlt**: keine Ortung (mit Hinweis auf „Tür + Signal“ oder „zählt als Ortung“),
Ortung zu alt oder nicht draußen, oder bei „Tür + Signal“ die letzte Tür und wann das Signal
wegfiel (mit Zeitfenster). Sie lässt sich mit einem Knopf aktualisieren.

## Folgen

- Geofence-Tracker funktionieren ohne Umweg, und der Schutz vor schlafenden Handys bleibt für
  alle anderen Signale.
- Wer seine eigene Logik hat, kann sie nutzen – mit klarer Warnung.
- Rein darf dadurch nicht unsicherer werden: „Bei Rückkehr“ und die Eingangsverzögerung sind
  davon nicht berührt.
