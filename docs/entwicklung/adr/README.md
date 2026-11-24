# Architekturentscheidungen (ADR)

Wichtige Entscheidungen mit Kontext, Abwägung und Folgen.

| Nr. | Entscheidung |
|---|---|
| [0001](0001-custom-integration.md) | Umsetzung als Custom Integration statt reiner Packages |
| [0002](0002-reiner-kern.md) | Reiner Kern nach dem Muster „Ereignis rein, Effekte raus“ |
| [0003](0003-brandsperre.md) | Globale Brandsperre, auch bei unklarem Zustand |
| [0004](0004-neustart-unscharf.md) | Nach Neustart immer unscharf (abgelöst durch 0008) |
| [0005](0005-ausweise.md) | Ausweise: PIN und RFID-Karte am Benutzer, Aufkleber und Leser als Bedienteile |
| [0006](0006-regeln.md) | Auslöseregeln – Abfolgen von Meldern |
| [0007](0007-bereiche.md) | Bereiche |
| [0008](0008-verhalten-nach-neustart.md) | Verhalten nach Neustart einstellbar, Standard: wiederherstellen |
| [0009](0009-einrichtungsassistent.md) | Einrichtungsassistent und gemeinsame Logikschicht |
| [0010](0010-fenster-kippstellung-erschuetterung.md) | Fenster richtig überwachen: Kippstellung („gekippt“) je Profil und Erschütterung als eigener Typ |
| [0011](0011-einstellungsseite.md) | Einstellungsseite in der Seitenleiste – zusätzlich zum Dialog |
| [0012](0012-keypads-allgemein.md) | Keypads allgemein anbinden – ein Eingang für alle Geräte, Blueprints und MQTT |
| [0013](0013-durchgang.md) | Durchgang – rein oder raus, ohne unscharf zu schalten |
| [0014](0014-ausgangserkennung.md) | Ausgangserkennung – Rausgehen ohne PIN erkennen (vorgeschlagen) |
| [0015](0015-rueckkehr.md) | Rückkehr neu geregelt – „Bei Rückkehr“, „weg“ nur mit Beleg, Annäherung (umgesetzt in 0.61.0, Nachtrag „Tür + Signal“) |
| [0016](0016-anwesenheit-testen.md) | Anwesenheit in der Testkarte – simulieren und sehen, warum (angenommen, 0.63) |
