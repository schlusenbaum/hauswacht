// Hauswacht – Einstellungsseite, Stufe 5: System, PIN-Regeln, Aktions-Codes, Bedienteile (ADR 0011).
//
// Seitenblatt <hauswacht-system-editor> mit den Arten restart, silence, network, homecoming,
// area, page, pinrules, actioncode, learn. Gespeichert wird über
// hauswacht/settings/apply – dieselben Regeln wie im Dialog.

const ST = {
  de: {
    save: "Speichern",
    saving: "Speichere …",
    cancel: "Abbrechen",
    del: "Löschen",
    delSure: "Wirklich löschen?",
    none: "–",
    restart: "Verhalten nach Neustart",
    behavior: "Nach einem Neustart von Home Assistant",
    behaviors: {
      restore: "Vorherigen Zustand wiederherstellen (Standard)",
      armed: "Immer scharf (mit festem Profil)",
      disarmed: "Immer unscharf",
    },
    behaviorHint: {
      restore: "War die Anlage scharf, ist sie sofort wieder scharf – mit demselben Profil, ohne erneute Prüfung. Eine laufende Eingangsverzögerung beginnt neu.",
      armed: "Etwa eine Minute nach dem Hochfahren wird das gewählte Profil normal scharf geschaltet – mit Prüfung offener Melder. Für Ferienhaus oder unbewohnte Bereiche.",
      disarmed: "Nach dem Neustart ist die Anlage unscharf. War sie scharf, kommt eine Nachricht.",
    },
    continueAlarm: "Laufenden Alarm fortsetzen (Sirenen laufen weiter)",
    continueHint: "Standard: aus – nach dem Neustart keine Sirenen, die Alarm-Empfänger bekommen eine wichtige Nachricht.",
    restartProfile: "Alarmprofil für „immer scharf“",
    silence: "Funkstille von Sensoren",
    hours: "Maximale Funkstille (Stunden, 0 = aus)",
    silenceHint: "Hat sich ein Melder so lange nicht gemeldet, gilt er beim Scharfschalten als ausgefallen. Batteriesensoren melden sich teils nur alle paar Stunden – großzügig wählen. Melder, die sich seltener melden (z. B. manche Batterie-Türkontakte), bekommen besser einen eigenen Wert: Reiter Melder → Melder anklicken → Funkstille.",
    observation: "Beobachtung",
    network: "Funknetz und Gateways",
    networkHint: "Sensoren, die melden, ob ein Funknetz oder Gateway läuft (z. B. Zigbee2MQTT-Bridge). Fällt es aus, meldet Hauswacht eine Störung. Art „Problem“: an = Störung, sonst: an = in Ordnung.",
    addEntity: "Sensor hinzufügen – Namen tippen oder aus der Liste wählen",
    homecoming: "Anwesenheit und Heimkehr-Beobachtung",
    observe: "Heimkehr beobachten (schaltet nichts, misst nur)",
    persons: "Personen für die Beobachtung",
    ssids: "Heim-WLAN(s), durch Komma getrennt",
    signals: "Zusätzliche Signale je Person",
    signalsHint: "Gelten auch für die Profil-Automatik („alle weg“, „Rückkehr“) – z. B. WLAN-Sensor der Companion App.",
    presTitle: "Welche Signale zählen?",
    presSignal: "Signal",
    presArrive: "Ankommen",
    presLeave: "Weggehen",
    presNow: "Jetzt",
    presPersonRow: "{name} (Person)",
    presNowVals: { home: "zuhause", away: "weg", unknown: "unbekannt", direction: "nur Richtung" },
    presMode: "Weggehen erkennen",
    presModes: { all: "alle müssen weg sein (sicher)", one: "eines reicht (nach Tür)" },
    presDoor: "Nur nach einer Eingangstür (empfohlen)",
    presNoDoorWarn: "Unsicher: Ohne Tür reicht ein einziges Signal, das „weg“ sagt. Schläft das Handy nachts ein, gilt {name} als weg – „Scharf, wenn alle weg“ kann dann scharf schalten, obwohl {name} zuhause ist.",
    presNoArrive: "Kein Signal fürs Ankommen: {name} wird nie als zuhause erkannt.",
    presNoLeave: "Kein Signal fürs Weggehen: {name} wird nie als weg erkannt.",
    presOr: " oder ",
    presAnd: ", ",
    presHowArrive: "Ankommen: {name} gilt als zuhause, sobald {list} „zuhause“ sagt.",
    presHowAll: "Weggehen: {name} gilt als weg, wenn alle diese Signale „weg“ sagen – {list} – und es einen Beleg gibt (siehe „Wann gilt jemand als weg?“ unten).",
    presHowOne: "Weggehen: {name} gilt als weg, sobald eine Eingangstür auf war und danach (bis {w} Minuten) {list} „weg“ sagt. Kommt genau dieses Signal wieder auf „zuhause“, gilt {name} wieder als zuhause.",
    presHowOneNoDoor: "Weggehen: {name} gilt als weg, sobald {list} „weg“ sagt – auch ohne Tür. Kommt genau dieses Signal wieder auf „zuhause“, gilt {name} wieder als zuhause.",
    presHowStale: "Ein Signal, das nur fürs Ankommen zählt (z. B. Bluetooth, das durch die Tür sieht), hält {name} beim Weggehen nicht zuhause. Es zählt erst wieder, wenn es zwischendurch weg war.",
    presHowAlso: "Daneben gilt auch hier: Sagen alle Weggehen-Signale „weg“ und gibt es einen Beleg, ist {name} ebenfalls weg.",
    proofKind: "Beleg für „weg“",
    proofKinds: { fix: "nur Ortung (sicher)", weak: "auch Tür + Signal (unsicher)" },
    geofence: "Zählt als Ortung (Geofence)",
    geofenceHint: "Nur für Quellen, die den Standort des Handys auswerten – z. B. die Anwesenheit aus Apple Home oder ein Template-Tracker, der darauf beruht. Sie melden „zuhause“ oder „weg“ ohne Koordinaten. Nicht für WLAN, Ping oder Bluetooth: Die werden weg, wenn das Handy schläft – als Ortung markiert, würde ein schlafendes Handy die Person abwesend machen.",
    geofenceNone: "Keine Quelle ohne Koordinaten – Signale mit Koordinaten zählen ohnehin als Ortung.",
    proofWeakWarn: "Unsicher: Weg gilt auch, wenn eine Eingangstür aufgeht und kurz danach ein Signal dieser Person (WLAN, Ping, Bluetooth) von „da“ auf „weg“ wechselt. Öffnet jemand anderes die Tür, während dieses Handy zufällig einschläft, gilt die Person fälschlich als weg – „Scharf, wenn alle weg“ kann dann scharf schalten, obwohl sie zuhause ist. Nur wählen, wenn es für die Person keine Ortung gibt.",
    weakWindow: "Zeitfenster Tür + Signal (Minuten)",
    weakRecDefault: "Empfehlung: 5 Minuten.",
    weakRecMeasured: "Empfehlung: {r} Minuten – gemessen: ein Signal meldete „weg“ bis zu {m} Minuten nach der Tür, plus 2 Minuten Puffer.",
    proofTitle: "Wann gilt jemand als weg?",
    proofIntro: "Gilt für die Profil-Automatik („Scharf, wenn alle weg“, „Bei Rückkehr“) und die Beobachtung. Ein schlafendes Handy (WLAN weg) macht niemanden abwesend – es braucht einen Beleg: eine Ortung außerhalb (Companion App, iCloud3, GPS-Tracker). WLAN, Ping und Bluetooth bestätigen nur – außer du stellst bei einer Person oben „auch Tür + Signal“ ein.",
    proofAccuracy: "Ortung außerhalb prüfen",
    proofAccuracies: { strict: "genau prüfen (empfohlen)", simple: "einfach" },
    proofWindow: "Zeitfenster für den Beleg (Minuten)",
    proofRecDefault: "Empfehlung: 15 Minuten.",
    proofRecMeasured: "Empfehlung: {r} Minuten – gemessen: Weggehen dauerte bis zu {m} Minuten, plus 5 Minuten Puffer.",
    proofNoFix: "{names}: keine Ortung mit Koordinaten gefunden – gilt nie als weg. „Scharf, wenn alle weg“ wartet dann für immer. Abhilfe: Standort in der Companion App auf „Immer“ oder einen GPS-Tracker als Signal eintragen.",
    proofHow: {
      strict: "Weg ist jemand, wenn alle Signale „weg“ melden UND entweder eine Eingangstür aufging und das Handy danach (bis {w} Minuten) außerhalb geortet wurde, ODER das Handy gerade frisch (letzte {w} Minuten) und sicher außerhalb geortet ist – weiter weg als der Radius der Zone „Zuhause“ plus die gemeldete Ungenauigkeit. Ein GPS-Sprung im Haus zählt also nicht.",
      simple: "Weg ist jemand, wenn alle Signale „weg“ melden UND entweder eine Eingangstür aufging und das Handy danach (bis {w} Minuten) außerhalb geortet wurde, ODER das Handy gerade frisch (letzte {w} Minuten) außerhalb der Zone „Zuhause“ ist – egal wie ungenau. Achtung: Ein GPS-Sprung im Haus kann so als „weg“ zählen.",
    },
    proofInfo: {
      accuracy: "„Genau prüfen“ rechnet die Entfernung zum Zuhause aus und zieht die Ungenauigkeit des GPS ab. Ein Handy im Haus, dessen GPS 300 m daneben liegt, gilt damit nicht als weg. „Einfach“ nimmt nur die Zone – nur wählen, wenn eure Ortung sehr ungenaue Werte meldet und sonst nie „weg“ erkannt wird.",
      weak: "„Nur Ortung“: weg nur mit Ortung außerhalb (sicher). „Auch Tür + Signal“: zusätzlich weg, wenn eine Tür aufgeht und danach ein Signal der Person (WLAN, Ping, Bluetooth) auf „weg“ wechselt – für Personen ohne Ortung, z. B. wenn der Standort in der App aus ist. Ein Handy, das ohne Tür einschläft, macht auch hier niemanden abwesend.",
      weakWindow: "So lange nach der Türöffnung darf das Signal auf „weg“ wechseln. Kurz halten: Je länger, desto eher fällt zufällig ein schlafendes Handy in das Fenster, nachdem jemand anderes die Tür geöffnet hat.",
      window: "Wie lange nach einer Türöffnung die Ortung außerhalb kommen darf – und wie alt eine Ortung höchstens sein darf, um allein zu zählen. Zu kurz: Wer weggeht, wird erst spät oder gar nicht als weg erkannt. Zu lang: eine alte Ortung kann zu lange zählen.",
    },
    fieldInfo: {
      behavior: "Was nach einem Neustart von Home Assistant (Update, Stromausfall) passiert. „Vorherigen Zustand“ passt für die meisten.",
      continue_alarm: "Lief beim Neustart ein Alarm: An = er läuft weiter, die Sirenen gehen wieder an. Aus = keine Sirenen, aber eine wichtige Nachricht an die Alarm-Empfänger.",
      restart_profile: "Dieses Profil wird nach jedem Neustart scharf geschaltet – mit Prüfung offener Melder.",
      hours: "Ein Melder, der sich so lange nicht gemeldet hat, gilt beim Scharfschalten als ausgefallen (Lücke). 0 schaltet die Prüfung aus.",
      network: "Fällt Zigbee, Z-Wave oder ein Gateway aus, melden die Melder nichts mehr – ohne dass man es merkt. Mit diesen Sensoren erkennt Hauswacht den Ausfall und meldet eine Störung.",
      observe: "Misst nur, schaltet nichts: wann eure Handys beim Heimkommen und Weggehen reagieren. Daraus kommen die Empfehlungen (Eingangsverzögerung, Zeitfenster, Wartezeit).",
      persons: "Diese Personen werden beobachtet. Personen aus den Profil-Automatiken kommen automatisch dazu.",
      ssids: "Name eures WLANs (wie im Handy angezeigt). Ein WLAN-Sensor der Companion App gilt als „zuhause“, wenn das Handy in einem dieser Netze ist.",
      presence: "Je Signal zwei Haken: „Ankommen“ – zählt das Signal, um zu erkennen, dass die Person heimkommt? „Weggehen“ – zählt es, um zu erkennen, dass sie weg ist? Beispiel: Bluetooth fürs Ankommen ja, fürs Weggehen nein, weil es oft noch durch die Tür sieht. „Jetzt“ zeigt, was das Signal gerade sagt.",
      presMode: "„Alle müssen weg sein“: wie bisher – alle Weggehen-Signale sagen „weg“, dazu ein Beleg (Ortung außerhalb oder Tür + Ortung). Sicher, aber oft langsam: Es zählt das langsamste Signal. „Eines reicht (nach Tür)“: Eine Eingangstür war auf, danach sagt eines der Weggehen-Signale „weg“ – das reicht. Schnell, aber nur so gut wie das schnellste Signal: Wähle es nur, wenn die Signale dieser Person sich selten irren.",
      presDoor: "Empfohlen. Ohne Tür reicht ein Signal, das „weg“ sagt – auch nachts, wenn das Handy einschläft.",
      signals: "Weitere Hinweise, ob eine Person zuhause ist: WLAN-Sensor der App, Ping, Bluetooth, Richtung („Nähe“, Places), weitere Tracker. Ein einziges „zuhause“ reicht für zuhause; für „weg“ müssen alle weg sein.",
      area_name: "Name des Bereichs, z. B. „Garage“. Jeder Bereich hat sein eigenes Bedienfeld und eigene Profile.",
      area_icon: "Symbol des Bereichs, z. B. mdi:garage.",
      code_arm_required: "An: Auch zum Scharfschalten braucht es einen PIN (Bedienfeld, Keypad, Sprachassistent). Aus: Scharfschalten geht ohne PIN, unscharf immer nur mit.",
      end_alarm_without_pin: "An: Der Knopf „Alarm beenden“ (Sirenen aus, die Anlage bleibt scharf) geht ohne PIN.",
      buttons_without_pin: "An: Die Dashboard-Knöpfe (Unscharf, Alarm beenden, Scharf) gehen ohne PIN. Der PIN schützt dann nur Bedienfeld, Keypads und Sprachassistenten – an die Knöpfe kommen ohnehin nur angemeldete Benutzer.",
      card_pin_unlinked: "Gilt nur für die Karte „Hauswacht Alarm“: Konten, die einer Hauswacht-Person zugeordnet sind, schalten dort ohne PIN. An = alle anderen Konten brauchen einen PIN.",
      master_pin: "Ein PIN ohne eigene Person, mit allen Rechten – z. B. für Alexa oder als Familien-Code am Keypad. Im Logbuch steht dann nur „Master-PIN“.",
      ac_name: "Name des Codes, z. B. „Garagentor auf“ – erscheint im Ereignis und im Logbuch.",
      ac_code: "Die Ziffern, die man am Keypad tippt. Darf keinem PIN gleichen.",
      ac_key: "Mit dieser Taste wird der Code am Keypad abgeschickt.",
      ac_keypad: "An welchem Keypad der Code gilt.",
      ac_action: "Was der Code auslöst: ein Ereignis für eine eigene Automation, Scharfschalten mit einem Profil oder einen stillen Notruf. Unscharf schalten kann ein Aktions-Code nie.",
      source: "Der Messwert, der überwacht werden soll – z. B. Temperatur im Heizungskeller oder Leistung der Gefriertruhe.",
      upper: "Liegt der Messwert darüber, meldet der neue Melder „Problem“. Leer = keine obere Grenze.",
      lower: "Liegt der Messwert darunter, meldet der neue Melder „Problem“. Leer = keine untere Grenze.",
      hysteresis: "Abstand, ab dem wieder „normal“ gilt – verhindert ständiges Hin und Her um die Grenze.",
      type: "Welche Art Melder daraus wird (z. B. technischer Alarm, Frost, Wasser) – bestimmt Symbol und Text der Meldung.",
      target: "In welche Meldergruppe der neue Melder kommt. „Immer aktiv“ meldet auch unscharf.",
      minutes: "So lange merkt sich Hauswacht eine unbekannte Karte zum Anlernen.",
    },
    how: {
      silence: "Meldet sich ein Melder {h} Stunden nicht, gilt er beim Scharfschalten als ausgefallen.",
      silenceOff: "Aus: Hauswacht prüft nicht, ob sich Melder lange nicht gemeldet haben.",
      pinOff: "Es gibt noch keinen PIN: Unscharfschalten geht ohne PIN.",
      pinOn: "Unscharf schalten am Bedienfeld, Keypad und per Sprache nur mit PIN.",
      armPin: "Auch zum Scharfschalten wird ein PIN verlangt.",
      armNoPin: "Scharfschalten geht ohne PIN.",
      buttonsFree: "Die Dashboard-Knöpfe gehen ohne PIN.",
      endFree: "„Alarm beenden“ geht ohne PIN, die anderen Dashboard-Knöpfe brauchen einen.",
      buttonsPin: "Auch die Dashboard-Knöpfe brauchen einen PIN.",
      action: { event: "Hauswacht feuert ein Ereignis – deine eigene Automation entscheidet, was passiert.", arm: "Hauswacht schaltet das gewählte Profil scharf, als hätte jemand die Profil-Taste gedrückt.", silent_emergency: "Stiller Notruf: keine Sirene, aber eine wichtige Nachricht an die Alarm-Empfänger – z. B. wenn jemand dich zwingt, die Anlage zu bedienen." },
      upper: "Über {v} meldet der Melder „Problem“, wieder normal unter {b}.",
      lower: "Unter {v} meldet der Melder „Problem“, wieder normal über {b}.",
      helperEmpty: "Bitte mindestens eine Grenze eintragen.",
      learn: "Eine unbekannte Karte bleibt {m} Minuten zum Anlernen gemerkt.",
      learnOff: "Anlernen ist aus.",
    },
    infoLabel: "Erklärung",
    howLabel: "So verhält sich das:",
    moreSettings: "Mehr Einstellungen",
    apply: "übernehmen",
    area: "Bereich",
    areaNew: "Bereich anlegen",
    name: "Name",
    icon: "Symbol (z. B. mdi:garage)",
    areaProfiles: "Profile in diesem Bereich",
    page: "Einstellungsseite",
    pageShow: "In der Seitenleiste zeigen",
    pageHint: "Die Seite gibt es immer (nur Administratoren). Hier stellst du nur ein, ob sie in der Seitenleiste steht. Jeder Benutzer kann sie außerdem über „Seitenleiste bearbeiten“ für sich ausblenden.",
    pageWarn: "Ausgeblendet verschwindet nur der Eintrag in der Seitenleiste. Du erreichst die Seite weiter über die Geräteseite von Hauswacht (Link in der Geräteinfo), über „Konfigurieren“ bei der Integration oder direkt unter /hauswacht-settings – am besten als Lesezeichen speichern.",
    pinrules: "PIN-Regeln und Master-PIN",
    pinUsers: "Personen mit PIN",
    master: "Master-PIN",
    masterSet: "Master-PIN gesetzt",
    masterNone: "Kein Master-PIN",
    masterNew: "Neuer Master-PIN (4–8 Ziffern, leer = nicht ändern)",
    masterRemove: "Master-PIN entfernen",
    masterHint: "Ein einfacher PIN ohne eigene Person, z. B. damit Alexa nur mit PIN unscharf schaltet.",
    codeArm: "PIN auch zum Scharfschalten verlangen",
    endNoPin: "Alarm beenden ohne PIN",
    buttonsNoPin: "Dashboard-Knöpfe trotz PIN erlauben",
    cardPinUnlinked: "Alarmkarte: PIN für Konten ohne Hauswacht-Person verlangen",
    pinWarn: "Sobald ein PIN existiert, verlangt das Bedienfeld (und Alexa) zum Unscharfschalten einen PIN – von allen.",
    actioncode: "Aktions-Code",
    actioncodeNew: "Aktions-Code anlegen",
    code: "Code (2–8 Ziffern)",
    key: "Taste",
    keys: { arm_day_zones: "🏠 Haus (Tag)", arm_night_zones: "🌙 Nacht", arm_all_zones: "🔒 Schloss (Alle)", disarm: "🔓 offenes Schloss (Unscharf)" },
    keypad: "Keypad",
    allKeypads: "Alle Keypads",
    action: "Aktion",
    actions: { event: "Ereignis für eigene Automation", arm: "Scharf schalten mit Profil …", silent_emergency: "Stiller Notruf" },
    profile: "Alarmprofil",
    codeHint: "Kein Ausweis: Ein Aktions-Code kann nie unscharf schalten und darf keinem PIN gleichen. Derselbe Code darf mit verschiedenen Tasten verschiedene Aktionen haben.",
    learn: "Anlernzeit für neue Karten",
    helper: "Melder aus Messwert erstellen",
    helperInfo: "Macht aus einem Messwert (z. B. Temperatur, Feuchte, Leistung) einen Melder: Hauswacht legt einen Schwellenwert-Helfer in Home Assistant an (danach unter Einstellungen → Geräte & Dienste → Helfer änderbar und löschbar) und setzt ihn gleich ein. Bestehendes bleibt unverändert.",
    source: "Messwert",
    helperName: "Name des neuen Melders",
    upper: "Oberer Grenzwert (löst aus, wenn darüber)",
    lower: "Unterer Grenzwert (löst aus, wenn darunter)",
    hysteresis: "Hysterese (Abstand, ab dem wieder „normal“ gilt)",
    type: "Typ",
    target: "Einsetzen in",
    targetAlways: "Immer aktiv",
    minutes: "Minuten (0 = Anlernen aus)",
    learnHint: "So lange merkt sich Hauswacht eine unbekannte Karte, die an einem Keypad oder Leser gelesen wurde, zum Anlernen. 0 = Anlernen aus.",
    errors: {
      restart_needs_profile: "„Immer scharf“ braucht mindestens ein Alarmprofil.",
      area_has_profiles: "Diesem Bereich gehören noch Alarmprofile – erst die Profile löschen oder einem anderen Bereich zuordnen.",
      area_name_taken: "Diesen Namen hat bereits ein anderer Bereich.",
      area_name_required: "Bitte einen Namen angeben.",
      invalid_pin: "PIN: 4 bis 8 Ziffern.",
      pin_is_action_code: "Diese Ziffern sind schon ein Aktions-Code.",
      pin_is_duress: "Dieser PIN ist schon Bedrohungs-PIN von: {c}",
      user_name_required: "Bitte einen Namen eingeben.",
      action_code_name_taken: "Diesen Namen hat schon ein anderer Aktions-Code.",
      action_code_invalid: "Bitte 2 bis 8 Ziffern eingeben.",
      action_code_taken: "Diesen Code mit dieser Taste gibt es schon („{c}“).",
      action_code_profile_missing: "Bitte ein Alarmprofil wählen.",
      action_code_is_pin: "Dieser Code ist schon ein PIN oder Bedrohungs-PIN – bitte einen anderen wählen.",
      helper_no_limit: "Bitte einen oberen und/oder unteren Grenzwert angeben.",
      helper_range: "Der untere Grenzwert muss kleiner sein als der obere.",
      helper_name: "Bitte einen Namen angeben.",
      helper_failed: "Der Helfer konnte nicht angelegt werden (siehe Protokoll).",
      control_entity: "Bitte einen Messwert (sensor.…) wählen.",
      invalid: "Ungültiger Wert.",
      disarm_first: "Erst alle Bereiche unscharf schalten – dann lässt sich speichern.",
      changed_elsewhere: "Inzwischen wurde woanders etwas geändert. Die Seite lädt neu – bitte noch einmal.",
      failed: "Speichern fehlgeschlagen.",
    },
  },
  en: {
    save: "Save",
    saving: "Saving …",
    cancel: "Cancel",
    del: "Delete",
    delSure: "Really delete?",
    none: "–",
    restart: "Behaviour after restart",
    behavior: "After a restart of Home Assistant",
    behaviors: {
      restore: "Restore the previous state (default)",
      armed: "Always armed (with a fixed profile)",
      disarmed: "Always disarmed",
    },
    behaviorHint: {
      restore: "If the system was armed, it is armed again right away – same profile, no new check. A running entry delay starts over.",
      armed: "About a minute after start-up the chosen profile is armed normally – with the check for open sensors. For holiday homes or unoccupied areas.",
      disarmed: "After the restart the system is disarmed. If it was armed, you get a message.",
    },
    continueAlarm: "Continue a running alarm (sirens keep sounding)",
    continueHint: "Default: off – after the restart no sirens, the alarm recipients get an important message.",
    restartProfile: "Alarm profile for “always armed”",
    silence: "Sensor radio silence",
    hours: "Maximum radio silence (hours, 0 = off)",
    silenceHint: "If a sensor has not reported for this long, it counts as failed when arming. Battery sensors sometimes only report every few hours – choose generously. Sensors that report less often (e.g. some battery door contacts) are better given an own value: tab sensors → click the sensor → radio silence.",
    observation: "Observation",
    network: "Radio networks and gateways",
    networkHint: "Sensors that report whether a radio network or gateway is running (e.g. Zigbee2MQTT bridge). If it fails, Hauswacht reports a fault. Class “problem”: on = fault, otherwise: on = OK.",
    addEntity: "Add sensor – type a name or pick from the list",
    homecoming: "Presence and homecoming observation",
    observe: "Observe homecoming (switches nothing, only measures)",
    persons: "Persons for the observation",
    ssids: "Home Wi-Fi(s), separated by commas",
    signals: "Additional signals per person",
    signalsHint: "Also apply to the profile automation (“everyone away”, “arrival”) – e.g. the Wi-Fi sensor of the companion app.",
    presTitle: "Which signals count?",
    presSignal: "Signal",
    presArrive: "Arriving",
    presLeave: "Leaving",
    presNow: "Now",
    presPersonRow: "{name} (person)",
    presNowVals: { home: "home", away: "away", unknown: "unknown", direction: "direction only" },
    presMode: "Detect leaving",
    presModes: { all: "all must be away (safe)", one: "one is enough (after a door)" },
    presDoor: "Only after an entry door (recommended)",
    presNoDoorWarn: "Uncertain: without a door, a single signal reporting “away” is enough. If the phone falls asleep at night, {name} counts as away – “arm when everyone is away” may then arm although {name} is home.",
    presNoArrive: "No signal for arriving: {name} is never detected as home.",
    presNoLeave: "No signal for leaving: {name} is never detected as away.",
    presOr: " or ",
    presAnd: ", ",
    presHowArrive: "Arriving: {name} counts as home as soon as {list} reports “home”.",
    presHowAll: "Leaving: {name} counts as away when all these signals report “away” – {list} – and there is proof (see “When does someone count as away?” below).",
    presHowOne: "Leaving: {name} counts as away as soon as an entry door was open and afterwards (up to {w} minutes) {list} reports “away”. If exactly that signal comes back to “home”, {name} counts as home again.",
    presHowOneNoDoor: "Leaving: {name} counts as away as soon as {list} reports “away” – even without a door. If exactly that signal comes back to “home”, {name} counts as home again.",
    presHowStale: "A signal that only counts for arriving (e.g. Bluetooth, which sees through the door) does not keep {name} home when leaving. It counts again once it was away in between.",
    presHowAlso: "In addition: if all leaving signals report “away” and there is proof, {name} is away as well.",
    proofKind: "Proof for “away”",
    proofKinds: { fix: "location only (safe)", weak: "also door + signal (uncertain)" },
    geofence: "Counts as location (geofence)",
    geofenceHint: "Only for sources that evaluate the phone's position – e.g. presence from Apple Home or a template tracker based on it. They report “home” or “away” without coordinates. Not for Wi-Fi, ping or Bluetooth: those turn away when the phone sleeps – marked as location, a sleeping phone would make the person absent.",
    geofenceNone: "No source without coordinates – signals with coordinates count as location anyway.",
    proofWeakWarn: "Uncertain: away also counts when an entry door opens and shortly after a signal of this person (Wi-Fi, ping, Bluetooth) changes from “there” to “away”. If someone else opens the door while this phone happens to fall asleep, the person wrongly counts as away – “arm when all away” may then arm although the person is home. Only choose this if there is no location for the person.",
    weakWindow: "Time window door + signal (minutes)",
    weakRecDefault: "Recommendation: 5 minutes.",
    weakRecMeasured: "Recommendation: {r} minutes – measured: a signal reported “away” up to {m} minutes after the door, plus 2 minutes buffer.",
    proofTitle: "When does someone count as away?",
    proofIntro: "Applies to the profile automation (“arm when all away”, “On return”) and the observation. A sleeping phone (Wi-Fi gone) makes nobody away – it needs proof: a location outside (Companion app, iCloud3, GPS tracker). Wi-Fi, ping and Bluetooth only confirm – unless you set “also door + signal” for a person above.",
    proofAccuracy: "Check location outside",
    proofAccuracies: { strict: "check precisely (recommended)", simple: "simple" },
    proofWindow: "Time window for the proof (minutes)",
    proofRecDefault: "Recommendation: 15 minutes.",
    proofRecMeasured: "Recommendation: {r} minutes – measured: leaving took up to {m} minutes, plus 5 minutes buffer.",
    proofNoFix: "{names}: no location with coordinates found – never counts as away. “Arm when all away” then waits forever. Fix: set the location in the Companion app to “Always” or add a GPS tracker as a signal.",
    proofHow: {
      strict: "Someone is away when all signals report “away” AND either an entry door opened and the phone was located outside afterwards (up to {w} minutes), OR the phone is freshly (last {w} minutes) and surely located outside – further away than the radius of the zone “Home” plus the reported inaccuracy. So a GPS jump inside the house does not count.",
      simple: "Someone is away when all signals report “away” AND either an entry door opened and the phone was located outside afterwards (up to {w} minutes), OR the phone is freshly (last {w} minutes) outside the zone “Home” – no matter how inaccurate. Caution: a GPS jump inside the house may count as “away” this way.",
    },
    proofInfo: {
      accuracy: "“Check precisely” calculates the distance to home and takes the GPS inaccuracy into account. A phone in the house whose GPS is 300 m off does not count as away. “Simple” only uses the zone – choose it only if your location reports very inaccurate values and away is otherwise never detected.",
      weak: "“Location only”: away only with a location outside (safe). “Also door + signal”: additionally away when a door opens and afterwards a signal of the person (Wi-Fi, ping, Bluetooth) changes to “away” – for persons without a location, e.g. when location is switched off in the app. A phone falling asleep without a door makes nobody away here either.",
      weakWindow: "How long after the door opening the signal may change to “away”. Keep it short: the longer it is, the more likely a sleeping phone falls into the window by chance after someone else opened the door.",
      window: "How long after a door opening the location outside may come – and how old a location may be at most to count on its own. Too short: someone leaving is detected late or not at all. Too long: an old location may count for too long.",
    },
    fieldInfo: {
      behavior: "What happens after a restart of Home Assistant (update, power cut). “Restore previous state” suits most.",
      continue_alarm: "If an alarm was running at the restart: on = it continues, the sirens go on again. Off = no sirens, but an important message to the alarm recipients.",
      restart_profile: "This profile is armed after every restart – with a check for open sensors.",
      hours: "A sensor that has not reported for this long counts as failed when arming (a gap). 0 switches the check off.",
      network: "If Zigbee, Z-Wave or a gateway fails, sensors stop reporting – without anyone noticing. With these sensors Hauswacht detects the failure and reports a fault.",
      observe: "Only measures, switches nothing: when your phones react when coming home and leaving. The recommendations (entry delay, time window, waiting time) come from this.",
      persons: "These persons are observed. Persons from the profile automations are added automatically.",
      ssids: "Name of your Wi-Fi (as shown on the phone). A Wi-Fi sensor of the Companion app counts as “home” when the phone is in one of these networks.",
      presence: "Two ticks per signal: “Arriving” – does the signal count to detect that the person comes home? “Leaving” – does it count to detect that they are away? Example: Bluetooth yes for arriving, no for leaving, because it often still sees through the door. “Now” shows what the signal currently reports.",
      presMode: "“All must be away”: as before – all leaving signals report “away”, plus proof (location outside or door + location). Safe, but often slow: the slowest signal decides. “One is enough (after a door)”: an entry door was open, afterwards one of the leaving signals reports “away” – that is enough. Fast, but only as good as the fastest signal: choose it only if this person's signals are rarely wrong.",
      presDoor: "Recommended. Without a door, one signal reporting “away” is enough – even at night when the phone falls asleep.",
      signals: "More hints whether a person is home: Wi-Fi sensor of the app, ping, Bluetooth, direction (Proximity, Places), further trackers. A single “home” is enough for home; for “away” all must be away.",
      area_name: "Name of the area, e.g. “Garage”. Every area has its own panel and its own profiles.",
      area_icon: "Icon of the area, e.g. mdi:garage.",
      code_arm_required: "On: arming also needs a PIN (panel, keypad, voice assistant). Off: arming works without a PIN, disarming always needs one.",
      end_alarm_without_pin: "On: the button “End alarm” (sirens off, the system stays armed) works without a PIN.",
      buttons_without_pin: "On: the dashboard buttons (Disarm, End alarm, Arm) work without a PIN. The PIN then only protects the panel, keypads and voice assistants – only logged-in users can reach the buttons anyway.",
      card_pin_unlinked: "Only for the card “Hauswacht Alarm”: accounts linked to a Hauswacht person switch there without a PIN. On = all other accounts need a PIN.",
      master_pin: "A PIN without its own person, with all rights – e.g. for Alexa or as a family code on the keypad. The logbook then only says “Master PIN”.",
      ac_name: "Name of the code, e.g. “Open garage door” – shown in the event and the logbook.",
      ac_code: "The digits typed on the keypad. Must not equal any PIN.",
      ac_key: "The code is sent with this key on the keypad.",
      ac_keypad: "On which keypad the code applies.",
      ac_action: "What the code triggers: an event for your own automation, arming with a profile or a silent emergency call. An action code can never disarm.",
      source: "The value to watch – e.g. the temperature in the boiler room or the power of the freezer.",
      upper: "If the value is above, the new sensor reports “problem”. Empty = no upper limit.",
      lower: "If the value is below, the new sensor reports “problem”. Empty = no lower limit.",
      hysteresis: "Distance from which “normal” applies again – prevents constant back and forth around the limit.",
      type: "Which kind of sensor it becomes (e.g. technical alarm, frost, water) – decides icon and message text.",
      target: "Which sensor group the new sensor goes into. “Always active” also reports when disarmed.",
      minutes: "This long Hauswacht remembers an unknown card for learning.",
    },
    how: {
      silence: "If a sensor does not report for {h} hours, it counts as failed when arming.",
      silenceOff: "Off: Hauswacht does not check whether sensors have been silent for long.",
      pinOff: "There is no PIN yet: disarming works without a PIN.",
      pinOn: "Disarming on the panel, keypad and by voice only with a PIN.",
      armPin: "Arming also requires a PIN.",
      armNoPin: "Arming works without a PIN.",
      buttonsFree: "The dashboard buttons work without a PIN.",
      endFree: "“End alarm” works without a PIN, the other dashboard buttons need one.",
      buttonsPin: "The dashboard buttons need a PIN too.",
      action: { event: "Hauswacht fires an event – your own automation decides what happens.", arm: "Hauswacht arms the chosen profile as if someone had pressed the profile key.", silent_emergency: "Silent emergency call: no siren, but an important message to the alarm recipients – e.g. when someone forces you to operate the system." },
      upper: "Above {v} the sensor reports “problem”, normal again below {b}.",
      lower: "Below {v} the sensor reports “problem”, normal again above {b}.",
      helperEmpty: "Please enter at least one limit.",
      learn: "An unknown card is remembered for {m} minutes for learning.",
      learnOff: "Learning is off.",
    },
    infoLabel: "Explanation",
    howLabel: "This is how it behaves:",
    moreSettings: "More settings",
    apply: "apply",
    area: "Area",
    areaNew: "Add area",
    name: "Name",
    icon: "Icon (e.g. mdi:garage)",
    areaProfiles: "Profiles in this area",
    page: "Settings page",
    pageShow: "Show in the sidebar",
    pageHint: "The page always exists (administrators only). Here you only choose whether it is shown in the sidebar. Every user can also hide it for themselves via “Edit sidebar”.",
    pageWarn: "When hidden, only the sidebar entry disappears. You still reach the page from the Hauswacht device page (link in the device info), from “Configure” on the integration or directly at /hauswacht-settings – best saved as a bookmark.",
    pinrules: "PIN rules and master PIN",
    pinUsers: "People with PIN",
    master: "Master PIN",
    masterSet: "Master PIN set",
    masterNone: "No master PIN",
    masterNew: "New master PIN (4–8 digits, empty = keep)",
    masterRemove: "Remove master PIN",
    masterHint: "A simple PIN without a person of its own, e.g. so that Alexa only disarms with a PIN.",
    codeArm: "Also require the PIN to arm",
    endNoPin: "End an alarm without PIN",
    buttonsNoPin: "Allow dashboard buttons despite PIN",
    cardPinUnlinked: "Alarm card: require PIN for accounts without a Hauswacht person",
    pinWarn: "As soon as one PIN exists, the alarm panel (and Alexa) requires a PIN to disarm – from everyone.",
    actioncode: "Action code",
    actioncodeNew: "Add action code",
    code: "Code (2–8 digits)",
    key: "Key",
    keys: { arm_day_zones: "🏠 House (day)", arm_night_zones: "🌙 Night", arm_all_zones: "🔒 Lock (all)", disarm: "🔓 Open lock (disarm)" },
    keypad: "Keypad",
    allKeypads: "All keypads",
    action: "Action",
    actions: { event: "Event for your own automation", arm: "Arm with profile …", silent_emergency: "Silent emergency" },
    profile: "Alarm profile",
    codeHint: "Not a credential: an action code can never disarm and must not equal a PIN. The same code may have different actions with different keys.",
    learn: "Learning time for new cards",
    helper: "Create sensor from a measurement",
    helperInfo: "Turns a measurement (e.g. temperature, humidity, power) into a sensor: Hauswacht creates a threshold helper in Home Assistant (afterwards changeable and deletable under Settings → Devices & services → Helpers) and puts it to use right away. Nothing existing is changed.",
    source: "Measurement",
    helperName: "Name of the new sensor",
    upper: "Upper limit (triggers when above)",
    lower: "Lower limit (triggers when below)",
    hysteresis: "Hysteresis (distance before “normal” applies again)",
    type: "Type",
    target: "Use in",
    targetAlways: "Always active",
    minutes: "Minutes (0 = learning off)",
    learnHint: "This long Hauswacht remembers an unknown card read at a keypad or reader for learning. 0 = learning off.",
    errors: {
      restart_needs_profile: "“Always armed” needs at least one alarm profile.",
      area_has_profiles: "This area still has alarm profiles – delete them or move them to another area first.",
      area_name_taken: "Another area already has this name.",
      area_name_required: "Please enter a name.",
      invalid_pin: "PIN: 4 to 8 digits.",
      pin_is_action_code: "These digits are already an action code.",
      pin_is_duress: "This PIN is already the duress PIN of: {c}",
      user_name_required: "Please enter a name.",
      action_code_name_taken: "Another action code already has this name.",
      action_code_invalid: "Please enter 2 to 8 digits.",
      action_code_taken: "This code with this key already exists (“{c}”).",
      action_code_profile_missing: "Please choose an alarm profile.",
      action_code_is_pin: "This code is already a PIN or duress PIN – please choose another one.",
      helper_no_limit: "Please enter an upper and/or lower limit.",
      helper_range: "The lower limit must be below the upper one.",
      helper_name: "Please enter a name.",
      helper_failed: "The helper could not be created (see log).",
      control_entity: "Please choose a measurement (sensor.…).",
      invalid: "Invalid value.",
      disarm_first: "Disarm all areas first – then saving works.",
      changed_elsewhere: "Something was changed elsewhere in the meantime. The page reloads – please try again.",
      failed: "Saving failed.",
    },
  },
};

const HELP = {
  restart: "restart",
  silence: "silence",
  network: "network",
  homecoming: "homecoming",
  area: "areas",
  page: "settingsPage",
  pinrules: "pinRules",
  actioncode: "actionCodes",
  learn: "cards",
  helper: "helper",
};

const se = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

// Befunde der gemeinsamen Prüfung, die zum Seitenblatt „Anwesenheit“ gehören
const PRESENCE_CODES = ["away_never", "return_never", "weak_not_needed", "approach_without_direction", "location_frozen"];

class HauswachtSystemEditor extends HTMLElement {
  // open({hass, settings, kind, item}) – item: ID (Bereich, Aktions-Code, Bedienteil) oder null
  open(options) {
    Object.assign(this, options);
    const sys = this.settings.system;
    this._errors = {};
    this._details = {};
    this._busy = false;
    this._sure = false;
    const copy = (v) => JSON.parse(JSON.stringify(v));
    const kind = this.kind;
    if (kind === "restart") this._draft = copy(sys.restart);
    else if (kind === "silence") this._draft = copy(sys.silence);
    else if (kind === "network") this._draft = copy(sys.network);
    else if (kind === "homecoming") this._draft = copy(sys.homecoming);
    else if (kind === "page") this._draft = { enabled: sys.settings_page };
    else if (kind === "pinrules") this._draft = { ...copy(sys.pin_rules), master_pin: "", remove_master_pin: false };
    else if (kind === "learn") this._draft = { minutes: sys.controls.learn_minutes };
    else if (kind === "helper") this._draft = { source: "", name: "", upper: "", lower: "", hysteresis: 0, type: "technical", target: "__always__" };
    else if (kind === "area") this._draft = copy(sys.areas.find((a) => a.id === this.item) || { name: "", icon: "mdi:home-outline", profiles: [] });
    else if (kind === "actioncode") {
      this._draft = copy(
        sys.action_codes.codes.find((c) => c.id === this.item) || {
          name: "", code: "", key: "arm_day_zones", keypad: sys.action_codes.all_keypads, action: "event", profile: null,
        }
      );
    }
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this._render();
  }

  get _lang() {
    return (this.hass?.language || "en").startsWith("de") ? "de" : "en";
  }

  _t(key) {
    return ST[this._lang][key] ?? ST.en[key] ?? key;
  }

  _err(key) {
    const code = this._errors[key];
    if (!code) return "";
    const text = (this._t("errors")[code] || code).replace("{c}", this._details.conflict || "");
    return `<div class="err">${se(text)}</div>`;
  }

  // --- „weg“ nur mit Beleg (ADR 0015) ---------------------------------------------

  // Beschriftung mit ⓘ (0.62)
  _lab(key, label) {
    return `<label>${se(label)}${this._info(key, "", true)}</label>`;
  }

  // „So verhält sich das:“
  _howLine(text) {
    return text ? `<div class="how"><b>${se(this._t("howLabel"))}</b> ${se(text)}</div>` : "";
  }

  _info(key, suffix = "", optional = false) {
    // ⓘ: Mauszeiger drauf zeigt den Text, Tippen klappt ihn auf
    const text = this._t("proofInfo")[key] || this._t("fieldInfo")[key] || "";
    if (optional && !text) return "";
    const id = suffix ? `${key}:${suffix}` : key;
    return ` <button type="button" class="info" data-info="${se(id)}" title="${se(text)}" aria-label="${se(this._t("infoLabel"))}">ⓘ</button><span class="tip" data-tip="${se(id)}" hidden>${se(text)}</span>`;
  }

  _pinHow(d) {
    const h = this._t("how");
    const parts = [d.pin_users.length || d.master ? h.pinOn : h.pinOff];
    if (d.pin_users.length || d.master) {
      parts.push(d.code_arm_required ? h.armPin : h.armNoPin);
      parts.push(d.buttons_without_pin ? h.buttonsFree : d.end_alarm_without_pin ? h.endFree : h.buttonsPin);
    }
    return parts.join(" ");
  }

  _helperHow(d) {
    const h = this._t("how");
    const parts = [];
    if (d.upper !== "" && d.upper !== null) parts.push(h.upper.replace("{v}", d.upper).replace("{b}", Number(d.upper) - Number(d.hysteresis || 0)));
    if (d.lower !== "" && d.lower !== null) parts.push(h.lower.replace("{v}", d.lower).replace("{b}", Number(d.lower) + Number(d.hysteresis || 0)));
    return parts.length ? parts.join(" ") : h.helperEmpty;
  }

  _proofRecommend(d) {
    // Aus der Messung „Weggehen“: längste Zeit Tür → weg, plus 5 Minuten Puffer
    const longest = Math.max(0, ...((d.measurements?.persons || []).map((p) => p.longest_left || 0)));
    if (!longest) return { minutes: 15, measured: null };
    return { minutes: Math.min(d.proof_max_window, Math.max(15, Math.ceil(longest / 60) + 5)), measured: Math.ceil(longest / 60) };
  }

  _presRule(person, d) {
    d.presence = d.presence || {};
    d.presence[person] = d.presence[person] || { arrive_off: [], leave_off: [], mode: "all", door: true };
    return d.presence[person];
  }

  _presenceTable(person, d) {
    // Anwesenheit je Person (ADR 0021): je Signal Ankommen/Weggehen, Weggehen-Regel, Klartext
    const rule = this._presRule(person, d);
    const pname = (d.person_choices.find((c) => c.id === person) || { name: person }).name;
    const sname = (id) => (id === person ? this._t("presPersonRow").replace("{name}", pname) : (d.signal_choices.find((c) => c.id === id) || { name: id }).name);
    const rows = [person, ...(d.signals[person] || [])];
    const nowText = (id) => {
      const v = (d.signal_now || {})[id];
      const vals = this._t("presNowVals");
      return v === true ? vals.home : v === false ? vals.away : v === "direction" ? vals.direction : vals.unknown;
    };
    const key = (id) => se(`${person}|${id}`);
    const body = rows
      .map((id) => `<tr><td title="${se(id)}">${se(sname(id))}</td>
        <td class="c"><input type="checkbox" data-pa="${key(id)}" ${rule.arrive_off.includes(id) ? "" : "checked"} aria-label="${se(this._t("presArrive"))}"></td>
        <td class="c"><input type="checkbox" data-pl="${key(id)}" ${rule.leave_off.includes(id) ? "" : "checked"} aria-label="${se(this._t("presLeave"))}"></td>
        <td>${se(nowText(id))}</td></tr>`)
      .join("");
    const modes = this._t("presModes");
    const one = rule.mode === "one";
    return `<div class="pres"><b>${se(this._t("presTitle"))}</b>${this._info("presence", person)}
      <table class="pt"><thead><tr><th>${se(this._t("presSignal"))}</th><th>${se(this._t("presArrive"))}</th><th>${se(this._t("presLeave"))}</th><th>${se(this._t("presNow"))}</th></tr></thead><tbody>${body}</tbody></table>
      <label>${se(this._t("presMode"))} ${this._info("presMode", person)}</label>
      <select data-pmode="${se(person)}">${["all", "one"].map((m) => `<option value="${m}" ${rule.mode === m ? "selected" : ""}>${se(modes[m])}</option>`).join("")}</select>
      ${one ? `<div class="chk"><input type="checkbox" data-pdoor="${se(person)}" ${rule.door ? "checked" : ""}><span>${se(this._t("presDoor"))}${this._info("presDoor", person)}</span></div>` : ""}
      ${one && !rule.door ? `<div class="warn">${se(this._t("presNoDoorWarn").replaceAll("{name}", pname))}</div>` : ""}
      ${this._presenceWarn(person, pname, rows, rule)}
      <div class="how"><b>${se(this._t("howLabel"))}</b> ${se(this._presenceHow(person, pname, rows, rule, sname, d))}</div></div>`;
  }

  _presenceWarn(person, pname, rows, rule) {
    const out = [];
    if (!rows.some((id) => !rule.arrive_off.includes(id))) out.push(this._t("presNoArrive"));
    if (!rows.some((id) => !rule.leave_off.includes(id))) out.push(this._t("presNoLeave"));
    return out.map((t) => `<div class="warn">${se(t.replaceAll("{name}", pname))}</div>`).join("");
  }

  _presenceHow(person, pname, rows, rule, sname, d) {
    const arrive = rows.filter((id) => !rule.arrive_off.includes(id)).map(sname);
    const leave = rows.filter((id) => !rule.leave_off.includes(id)).map(sname);
    const parts = [];
    if (arrive.length) parts.push(this._t("presHowArrive").replace("{list}", arrive.join(this._t("presOr"))));
    if (leave.length) {
      if (rule.mode === "one") {
        const text = rule.door ? this._t("presHowOne") : this._t("presHowOneNoDoor");
        parts.push(text.replace("{list}", leave.join(this._t("presOr"))).replace("{w}", String(d.proof_weak_window)));
        parts.push(this._t("presHowAlso"));
      } else {
        parts.push(this._t("presHowAll").replace("{list}", leave.join(this._t("presAnd"))));
      }
    }
    if (rows.some((id) => !rule.arrive_off.includes(id) && rule.leave_off.includes(id))) parts.push(this._t("presHowStale"));
    return parts.join(" ").replaceAll("{name}", pname);
  }

  _weakPick(person, d) {
    // Beleg für „weg“ je Person: nur Ortung (sicher) oder auch Tür + Signal (unsicher)
    const weak = d.proof_weak.includes(person);
    const opts = [["fix", this._t("proofKinds").fix], ["weak", this._t("proofKinds").weak]];
    return `<label>${se(this._t("proofKind"))} ${this._info("weak", person)}</label>
      <select data-weak="${se(person)}">${opts.map(([v, l]) => `<option value="${v}" ${(v === "weak") === weak ? "selected" : ""}>${se(l)}</option>`).join("")}</select>
      ${weak ? `<div class="warn">${se(this._t("proofWeakWarn"))}</div>` : ""}`;
  }

  _geofencePick(person, d) {
    // Signale/Tracker ohne Koordinaten, die als Ortung zählen sollen (ADR 0018)
    const known = (d.geofence_choices || {})[person] || [];
    const extra = (d.signals[person] || []).filter((id) => !known.some((c) => c.id === id)).map((id) => ({ id, name: (d.signal_choices.find((c) => c.id === id) || { name: id }).name }));
    const items = [...known, ...extra];
    const geo = d.proof_geofence || [];
    const rows = items.length
      ? items.map((x) => `<div class="chk"><input type="checkbox" data-geo="${se(x.id)}" ${geo.includes(x.id) ? "checked" : ""}><span>${se(x.name)}</span></div>`).join("")
      : `<div class="muted">${se(this._t("geofenceNone"))}</div>`;
    return `<details class="geo"${items.some((x) => geo.includes(x.id)) ? " open" : ""}><summary>${se(this._t("geofence"))}</summary><div class="muted">${se(this._t("geofenceHint"))}</div>${rows}</details>`;
  }

  _weakRecommend(d) {
    // Längste Zeit „Tür auf“ → ein einzelnes Signal „weg“ bei den Personen mit Tür + Signal, plus 2 min
    const rows = (d.measurements?.persons || []).filter((p) => d.proof_weak.includes(p.id));
    const longest = Math.max(0, ...rows.map((p) => p.longest_signal_left || 0));
    if (!longest) return { minutes: 5, measured: null };
    return { minutes: Math.min(d.proof_weak_max, Math.max(3, Math.ceil(longest / 60) + 2)), measured: Math.ceil(longest / 60) };
  }

  _proofHow(d) {
    const text = this._t("proofHow")[d.proof_accuracy] || "";
    return text.replaceAll("{w}", String(d.proof_window));
  }

  _proofForm(d) {
    const rec = this._proofRecommend(d);
    const recText = rec.measured === null ? this._t("proofRecDefault") : this._t("proofRecMeasured").replace("{m}", rec.measured).replace("{r}", rec.minutes);
    const noFix = d.no_fix.length ? `<div class="warn">${se(this._t("proofNoFix").replace("{names}", d.no_fix.join(", ")))}</div>` : "";
    return `<div class="box"><b>${se(this._t("proofTitle"))}</b>
        <div class="muted">${se(this._t("proofIntro"))}</div>
        <label>${se(this._t("proofAccuracy"))} ${this._info("accuracy")}</label>${this._select("proof_accuracy", d.proof_accuracy, d.proof_accuracies.map((x) => [x, this._t("proofAccuracies")[x] || x]))}
        <div class="how"><b>${se(this._t("howLabel"))}</b> <span data-how>${se(this._proofHow(d))}</span></div>
        ${noFix}
        <details class="more" ${this._moreOpen ? "open" : ""}><summary>${se(this._t("moreSettings"))}</summary>
          <label>${se(this._t("proofWindow"))} ${this._info("window")}</label>
          <input class="small" type="number" min="1" max="${d.proof_max_window}" data-f="proof_window" value="${se(d.proof_window)}">
          <div class="muted">${se(recText)} ${Number(d.proof_window) === rec.minutes ? "" : `<button type="button" class="b" data-act="proof-rec" data-field="proof_window" data-value="${rec.minutes}">${se(this._t("apply"))}</button>`}</div>
          ${d.proof_weak.length || Object.values(d.presence || {}).some((r) => r.mode === "one") ? this._weakWindow(d) : ""}
        </details></div>`;
  }

  _weakWindow(d) {
    const rec = this._weakRecommend(d);
    const recText = rec.measured === null ? this._t("weakRecDefault") : this._t("weakRecMeasured").replace("{m}", rec.measured).replace("{r}", rec.minutes);
    return `<label>${se(this._t("weakWindow"))} ${this._info("weakWindow")}</label>
          <input class="small" type="number" min="1" max="${d.proof_weak_max}" data-f="proof_weak_window" value="${se(d.proof_weak_window)}">
          <div class="muted">${se(recText)} ${Number(d.proof_weak_window) === rec.minutes ? "" : `<button type="button" class="b" data-act="proof-rec" data-field="proof_weak_window" data-value="${rec.minutes}">${se(this._t("apply"))}</button>`}</div>`;
  }

  _chk(field, checked, label) {
    return `<div class="chk"><input type="checkbox" data-b="${se(field)}" ${checked ? "checked" : ""}><span>${se(label)}${this._info(field, "", true)}</span></div>`;
  }

  _select(field, value, entries) {
    return `<select data-f="${se(field)}">${entries.map(([v, l]) => `<option value="${se(v)}" ${v === value ? "selected" : ""}>${se(l)}</option>`).join("")}</select>`;
  }

  // Liste von Entitäten mit ✕ und Eingabe mit Vorschlägen
  _entityList(where, list, choices) {
    const name = (id) => (choices.find((c) => c.id === id) || { name: id }).name;
    const chips = list.map((id, i) => `<span class="chip" title="${se(id)}">${se(name(id))}<button class="x" data-rm="${where}:${i}">✕</button></span>`).join("");
    return `<div class="chips">${chips}</div><input list="hw-sys-${where.split(":")[0]}" data-add="${se(where)}" placeholder="${se(this._t("addEntity"))}">`;
  }

  // Eine Entität wählen: Eingabe mit Vorschlägen (Name oder ID)
  _entityPick(field, value, choices) {
    this._picks = { ...(this._picks || {}), [field]: choices };
    const shown = (choices.find((c) => c.id === value) || { name: value || "" }).name;
    return `<input data-pick="${se(field)}" list="hw-sys-pick-${field}" value="${se(shown)}" placeholder="${se(this._t("addEntity"))}">${this._datalist(`pick-${field}`, choices)}`;
  }

  _datalist(id, choices) {
    return `<datalist id="hw-sys-${id}">${choices.map((c) => `<option value="${se(c.id)}">${se(c.name)}</option>`).join("")}</datalist>`;
  }

  _form() {
    const d = this._draft;
    const sys = this.settings.system;
    const k = this.kind;
    if (k === "restart") {
      const areas = sys.areas.filter((a) => sys.profiles.some((p) => p.area === a.id));
      const perArea = d.behavior === "armed"
        ? areas.map((a) => {
            const entries = [["", this._t("none")], ...sys.profiles.filter((p) => p.area === a.id).map((p) => [p.id, p.name])];
            return `<label>${se(this._t("restartProfile"))}${areas.length > 1 ? ` – ${se(a.name)}` : ""}${this._info("restart_profile", a.id, true)}</label><select data-rp="${se(a.id)}">${entries.map(([v, l]) => `<option value="${se(v)}" ${v === (d.profiles[a.id] || "") ? "selected" : ""}>${se(l)}</option>`).join("")}</select>`;
          }).join("")
        : "";
      return `<h2>${se(this._t("restart"))}</h2>
        ${this._lab("behavior", this._t("behavior"))}${this._select("behavior", d.behavior, d.behaviors.map((b) => [b, this._t("behaviors")[b]]))}
        ${this._howLine(this._t("behaviorHint")[d.behavior] || "")}${perArea}${this._err("base")}
        ${d.behavior === "restore" ? `${this._chk("continue_alarm", d.continue_alarm, this._t("continueAlarm"))}<div class="muted">${se(this._t("continueHint"))}</div>` : ""}`;
    }
    if (k === "silence") {
      return `<h2>${se(this._t("silence"))}</h2>
        ${this._lab("hours", this._t("hours"))}<input class="small" type="number" min="0" max="${d.max}" data-f="hours" value="${se(d.hours)}">
        ${this._howLine(Number(d.hours) > 0 ? this._t("how").silence.replace("{h}", d.hours) : this._t("how").silenceOff)}
        <div class="muted">${se(this._t("silenceHint"))}</div>
        ${d.observation ? `<label>${se(this._t("observation"))}</label><div class="muted">${se(d.observation)}</div>` : ""}`;
    }
    if (k === "network") {
      return `<h2>${se(this._t("network"))}${this._info("network", "", true)}</h2><div class="muted">${se(this._t("networkHint"))}</div>
        ${this._entityList("net", d.entities, d.choices)}${this._datalist("net", d.choices)}`;
    }
    if (k === "homecoming") {
      const persons = [...new Set([...d.persons, ...d.signal_persons])];
      const signals = persons
        .map((p, i) => `<div class="box"><b>${se((d.person_choices.find((c) => c.id === p) || { name: p }).name)}</b>${this._entityList(`sig:${i}`, d.signals[p] || [], d.signal_choices)}${this._presenceTable(p, d)}${this._presRule(p, d).mode === "one" ? "" : this._weakPick(p, d)}${this._geofencePick(p, d)}</div>`)
        .join("");
      return `<h2>${se(this._t("homecoming"))}</h2>
        ${this._chk("observe", d.observe, this._t("observe"))}
        ${this._lab("persons", this._t("persons"))}${this._entityList("per", d.persons, d.person_choices)}${this._datalist("per", d.person_choices)}
        ${this._lab("ssids", this._t("ssids"))}<input data-f="ssids" value="${se(d.ssids.join(", "))}">
        ${this._lab("signals", this._t("signals"))}<div class="muted">${se(this._t("signalsHint"))}</div>${signals}${this._datalist("sig", d.signal_choices)}
        ${this._proofForm(d)}`;
    }
    if (k === "area") {
      return `<h2>${se(this.item ? this._t("area") : this._t("areaNew"))}</h2>
        ${this._lab("area_name", this._t("name"))}<input data-f="name" value="${se(d.name)}">${this._err("name")}
        ${this._lab("area_icon", this._t("icon"))}<input data-f="icon" value="${se(d.icon)}">
        ${this.item ? `<label>${se(this._t("areaProfiles"))}</label><div class="muted">${se(d.profiles.join(", ") || this._t("none"))}</div>` : ""}${this._err("base")}`;
    }
    if (k === "page") {
      return `<h2>${se(this._t("page"))}</h2><div class="muted">${se(this._t("pageHint"))}</div>${this._chk("enabled", d.enabled, this._t("pageShow"))}
        ${d.enabled ? "" : `<div class="warn">${se(this._t("pageWarn"))}</div>`}`;
    }
    if (k === "pinrules") {
      return `<h2>${se(this._t("pinrules"))}</h2>
        <div class="muted">${se(this._t("pinUsers"))}: ${se(d.pin_users.join(", ") || this._t("none"))}</div>
        <div class="warn">${se(this._t("pinWarn"))}</div>
        ${this._chk("code_arm_required", d.code_arm_required, this._t("codeArm"))}
        ${this._chk("end_alarm_without_pin", d.end_alarm_without_pin, this._t("endNoPin"))}
        ${this._chk("buttons_without_pin", d.buttons_without_pin, this._t("buttonsNoPin"))}
        ${this._chk("card_pin_unlinked", d.card_pin_unlinked, this._t("cardPinUnlinked"))}
        ${this._howLine(this._pinHow(d))}
        <div class="box"><b>${se(this._t("master"))}</b> <span class="muted">${se(d.master ? this._t("masterSet") : this._t("masterNone"))}</span>
          <div class="muted">${se(this._t("masterHint"))}</div>
          ${this._lab("master_pin", this._t("masterNew"))}<input type="password" inputmode="numeric" autocomplete="new-password" data-f="master_pin" value="${se(d.master_pin)}">${this._err("master_pin")}
          ${d.master ? this._chk("remove_master_pin", d.remove_master_pin, this._t("masterRemove")) : ""}</div>`;
    }
    if (k === "actioncode") {
      const ac = sys.action_codes;
      const keypads = [[ac.all_keypads, this._t("allKeypads")], ...ac.keypads.map((x) => [x.id, x.name])];
      return `<h2>${se(this.item ? this._t("actioncode") : this._t("actioncodeNew"))}</h2>
        <div class="muted">${se(this._t("codeHint"))}</div>
        ${this._lab("ac_name", this._t("name"))}<input data-f="name" value="${se(d.name)}">${this._err("name")}
        ${this._lab("ac_code", this._t("code"))}<input class="small" inputmode="numeric" data-f="code" value="${se(d.code)}">${this._err("code")}
        ${this._lab("ac_key", this._t("key"))}${this._select("key", d.key, ac.keys.map((x) => [x, this._t("keys")[x] || x]))}
        ${this._lab("ac_keypad", this._t("keypad"))}${this._select("keypad", d.keypad, keypads)}
        ${this._lab("ac_action", this._t("action"))}${this._select("action", d.action, ac.actions.map((x) => [x, this._t("actions")[x] || x]))}
        ${this._howLine((this._t("how").action || {})[d.action] || "")}
        ${d.action === "arm" ? `<label>${se(this._t("profile"))}</label>${this._select("profile", d.profile || "", [["", this._t("none")], ...sys.profiles.map((p) => [p.id, p.name])])}${this._err("profile")}` : ""}`;
    }
    if (k === "helper") {
      const sensors = this.settings.entities.filter((e) => e.domain === "sensor").map((e) => ({ id: e.id, name: `${e.name} (${e.state})` }));
      const types = this.settings.types.map((t) => [t, this.typeLabel ? this.typeLabel(t) : t]);
      const targets = [["__always__", this._t("targetAlways")], ...this.settings.groups.map((g) => [g.id, g.name])];
      return `<h2>${se(this._t("helper"))}</h2><div class="muted">${se(this._t("helperInfo"))}</div>
        ${this._lab("source", this._t("source"))}${this._entityPick("source", d.source, sensors)}${this._err("source")}
        <label>${se(this._t("helperName"))}</label><input data-f="name" value="${se(d.name)}">${this._err("name")}
        <div class="inline"><div>${this._lab("upper", this._t("upper"))}<input class="small" type="number" step="any" data-f="upper" value="${se(d.upper)}"></div>
        <div>${this._lab("lower", this._t("lower"))}<input class="small" type="number" step="any" data-f="lower" value="${se(d.lower)}"></div></div>
        ${this._lab("hysteresis", this._t("hysteresis"))}<input class="small" type="number" step="any" min="0" data-f="hysteresis" value="${se(d.hysteresis)}">
        ${this._howLine(this._helperHow(d))}
        ${this._lab("type", this._t("type"))}${this._select("type", d.type, types)}
        ${this._lab("target", this._t("target"))}${this._select("target", d.target, targets)}`;
    }
    return `<h2>${se(this._t("learn"))}</h2>
      ${this._lab("minutes", this._t("minutes"))}<input class="small" type="number" min="0" max="${this.settings.system.controls.learn_max}" data-f="minutes" value="${se(d.minutes)}">
      ${this._howLine(Number(d.minutes) > 0 ? this._t("how").learn.replace("{m}", d.minutes) : this._t("how").learnOff)}
      <div class="muted">${se(this._t("learnHint"))}</div>`;
  }

  _collect() {
    const root = this.shadowRoot;
    const d = this._draft;
    root.querySelectorAll("[data-f]").forEach((el) => (d[el.dataset.f] = el.value));
    root.querySelectorAll("[data-b]").forEach((el) => (d[el.dataset.b] = el.checked));
    root.querySelectorAll("[data-pick]").forEach((el) => {
      const value = el.value.trim();
      const match = (this._picks?.[el.dataset.pick] || []).find((c) => c.name === value || c.id === value);
      d[el.dataset.pick] = match ? match.id : value;
    });
    root.querySelectorAll("[data-rp]").forEach((el) => {
      if (el.value) d.profiles[el.dataset.rp] = el.value;
      else delete d.profiles[el.dataset.rp];
    });
    if (this.kind === "homecoming" && typeof d.ssids === "string") {
      d.ssids = d.ssids.split(",").map((s) => s.trim()).filter(Boolean);
    }
    if (this.kind === "homecoming") {
      d.proof_window = Number(d.proof_window) || 15;
      d.proof_weak_window = Number(d.proof_weak_window) || 5;
      root.querySelectorAll("[data-weak]").forEach((el) => {
        const p = el.dataset.weak;
        d.proof_weak = d.proof_weak.filter((x) => x !== p);
        if (el.value === "weak") d.proof_weak.push(p);
      });
      const geo = [...root.querySelectorAll("[data-geo]")];
      if (geo.length) {
        const shown = new Set(geo.map((el) => el.dataset.geo));
        d.proof_geofence = [...(d.proof_geofence || []).filter((id) => !shown.has(id)), ...geo.filter((el) => el.checked).map((el) => el.dataset.geo)];
      }
      const more = root.querySelector("details.more");
      if (more) this._moreOpen = more.open;
      // Anwesenheit je Person (ADR 0021)
      const flip = (attr, field) =>
        root.querySelectorAll(`[${attr}]`).forEach((el) => {
          const raw = el.getAttribute(attr);
          const cut = raw.indexOf("|");
          const rule = this._presRule(raw.slice(0, cut), d);
          const id = raw.slice(cut + 1);
          rule[field] = rule[field].filter((x) => x !== id);
          if (!el.checked) rule[field].push(id);
        });
      flip("data-pa", "arrive_off");
      flip("data-pl", "leave_off");
      root.querySelectorAll("[data-pmode]").forEach((el) => (this._presRule(el.dataset.pmode, d).mode = el.value));
      root.querySelectorAll("[data-pdoor]").forEach((el) => (this._presRule(el.dataset.pdoor, d).door = el.checked));
    }
  }

  _list(where) {
    const d = this._draft;
    const [kind, index] = where.split(":");
    if (kind === "net") return d.entities;
    if (kind === "per") return d.persons;
    const persons = [...new Set([...d.persons, ...d.signal_persons])];
    const person = persons[Number(index)];
    d.signals[person] = d.signals[person] || [];
    return d.signals[person];
  }

  _choices(where) {
    const d = this._draft;
    const kind = where.split(":")[0];
    return kind === "net" ? d.choices : kind === "per" ? d.person_choices : d.signal_choices;
  }

  _payload() {
    const d = this._draft;
    switch (this.kind) {
      case "restart":
        return ["restart_save", { behavior: d.behavior, continue_alarm: d.continue_alarm, profiles: d.profiles }];
      case "silence":
        return ["silence_save", { hours: Number(d.hours) }];
      case "network":
        return ["network_save", { entities: d.entities }];
      case "homecoming":
        return ["homecoming_save", { observe: d.observe, persons: d.persons, ssids: d.ssids, signals: d.signals, proof_window: d.proof_window, proof_accuracy: d.proof_accuracy, proof_weak: d.proof_weak, proof_weak_window: d.proof_weak_window, proof_geofence: d.proof_geofence || [], presence: d.presence || {} }];
      case "area":
        return ["area_save", { id: this.item, name: d.name, icon: d.icon }];
      case "page":
        return ["settings_page_save", { enabled: d.enabled }];
      case "pinrules":
        return ["pin_rules_save", d];
      case "actioncode":
        return ["action_code_save", { ...d, id: this.item }];
      case "learn":
        return ["learn_save", { minutes: Number(d.minutes) }];
      case "helper":
        return ["helper_create", { ...d, upper: d.upper === "" ? null : Number(d.upper), lower: d.lower === "" ? null : Number(d.lower), hysteresis: Number(d.hysteresis || 0) }];
      default:
        return null;
    }
  }

  get _canDelete() {
    return (this.kind === "area" && this.item && this.item !== "main") || (this.kind === "actioncode" && this.item);
  }

  async _apply(action, data) {
    this._busy = true;
    this._render();
    let result;
    try {
      result = await this.hass.callWS({ type: "hauswacht/settings/apply", revision: this.settings.revision, action, data });
    } catch (_err) {
      result = { ok: false, errors: { base: "failed" } };
    }
    this._busy = false;
    if (result.ok) {
      this.dispatchEvent(new CustomEvent("hw-saved", { bubbles: true, composed: true, detail: { revision: result.revision } }));
      return;
    }
    this._errors = result.errors || { base: "failed" };
    this._details = result.details || {};
    if (this._errors.base === "changed_elsewhere") this.dispatchEvent(new CustomEvent("hw-stale", { bubbles: true, composed: true }));
    this._render();
    window.HauswachtRevealError?.(this.shadowRoot); // Fehlermeldung ins Bild holen
  }

  _render() {
    const top = this.shadowRoot.querySelector(".sheet")?.scrollTop || 0;
    const canSave = this._payload() !== null;
    const style = `.chips { display: flex; flex-wrap: wrap; gap: 6px; margin: 4px 0; }
      .chip { display: inline-flex; align-items: center; gap: 2px; border: 1px solid var(--divider-color); border-radius: 14px; padding: 2px 4px 2px 10px; font-size: .9rem; }
      .chip .x { font-size: 1rem; padding: 0 4px; }
      .warn { border: 1px solid var(--warning-color, #ffa600); border-radius: 8px; padding: 8px 10px; margin: 8px 0; font-size: .9rem; }
      .info { border: none; background: none; color: var(--primary-color); cursor: help; font-size: 1rem; padding: 0 2px; }
      .tip[hidden] { display: none; }
      .tip { display: block; font-size: .85rem; margin: 4px 0 6px; padding: 8px 10px; border-radius: 6px; background: var(--secondary-background-color); font-weight: normal; }
      .how { margin: 8px 0 4px; font-size: .9rem; }
      details.more { margin-top: 10px; }
      .pres { margin: 10px 0; }
      table.pt { width: 100%; border-collapse: collapse; margin: 6px 0; font-size: .9rem; }
      table.pt th, table.pt td { text-align: left; padding: 4px 6px; border-bottom: 1px solid var(--divider-color); }
      table.pt th:nth-child(2), table.pt th:nth-child(3), table.pt td.c { text-align: center; }
      details.more summary { cursor: pointer; color: var(--primary-color); }`;
    this.shadowRoot.innerHTML = `<style>${(window.HauswachtEditStyle || "") + style + (window.HauswachtAdvisor?.style || "")}</style><div class="sheet">${this._form()}
      ${this.kind === "homecoming" ? `<div class="advice" data-advice></div>` : ""}
      ${["restart", "area"].includes(this.kind) ? "" : this._err("base")}
      ${this.kind === "helper" ? ["upper", "lower", "hysteresis", "type", "target"].map((k) => this._err(k)).join("") : ""}
      <div class="bar">${canSave ? `<button class="b p" data-act="save" ${this._busy ? "disabled" : ""}>${se(this._busy ? this._t("saving") : this._t("save"))}</button>` : ""}
      <button class="b" data-act="cancel">${se(this._t("cancel"))}</button>
      ${this._canDelete ? `<button class="b d" data-act="delete">${se(this._sure ? this._t("delSure") : this._t("del"))}</button>` : ""}</div></div>`;
    this.shadowRoot.querySelector(".sheet").scrollTop = top;
    window.HauswachtDocs?.decorate(this.shadowRoot, HELP[this.kind], this._lang);
    this._wire();
    if (this.kind === "homecoming") {
      this._showAdvice();
      this._scheduleAdvice();
    }
  }

  // --- Hinweise des Assistenten (gemeinsame Prüfung, ADR 0017) ----------------------
  // Hier geht es um Personen: wer als weg erkannt werden kann, und „Tür + Signal“.

  _scheduleAdvice() {
    clearTimeout(this._adviceTimer);
    this._adviceTimer = setTimeout(() => this._advise(), 500);
  }

  async _advise() {
    const advisor = window.HauswachtAdvisor;
    if (!advisor || !this.isConnected || !this.shadowRoot.querySelector("[data-advice]")) return;
    this._collect();
    const seq = (this._adviceSeq = (this._adviceSeq || 0) + 1);
    const [action, data] = this._payload();
    const result = await advisor.check(this.hass, action, data, this._lang);
    if (seq !== this._adviceSeq) return;
    this._advice = (result.findings || []).filter((f) => PRESENCE_CODES.includes(f.code));
    this._showAdvice();
  }

  _showAdvice() {
    const advisor = window.HauswachtAdvisor;
    const box = this.shadowRoot.querySelector("[data-advice]");
    if (!advisor || !box) return;
    // Hier lässt sich nur „Tür + Signal“ ändern; Profil-Vorschläge stehen nur als Text da
    box.innerHTML = advisor.render(this._advice || [], this._lang, (fix) => fix.path === "away_proof_weak");
    box.querySelectorAll("[data-advfix]").forEach((btn) =>
      btn.addEventListener("click", () => {
        const [i, j] = btn.dataset.advfix.split(":").map(Number);
        const finding = this._advice[i];
        const fix = finding.fixes[j];
        if (!advisor.confirm(fix, finding, this._lang)) return;
        this._collect();
        advisor.apply(this._draft, "proof_weak", fix);
        this._render();
      })
    );
  }

  _wire() {
    const root = this.shadowRoot;
    const redraw = () => {
      this._collect();
      this._render();
    };
    this.onclick = (ev) => {
      if (ev.composedPath()[0] === this) this._close();
    };
    root.querySelector('[data-act="cancel"]').addEventListener("click", () => this._close());
    const save = root.querySelector('[data-act="save"]');
    if (save) {
      save.addEventListener("click", () => {
        this._collect();
        const [action, data] = this._payload();
        this._apply(action, data);
      });
    }
    const del = root.querySelector('[data-act="delete"]');
    if (del) {
      del.addEventListener("click", () => {
        this._collect();
        if (!this._sure) {
          this._sure = true;
          this._render();
          return;
        }
        const action = { area: "area_delete", actioncode: "action_code_delete" }[this.kind];
        this._apply(action, { id: this.item });
      });
    }
    root.querySelectorAll("[data-rm]").forEach((el) =>
      el.addEventListener("click", () => {
        this._collect();
        const [kind, a, b] = el.dataset.rm.split(":");
        const where = b === undefined ? kind : `${kind}:${a}`;
        const index = Number(b === undefined ? a : b);
        this._list(where).splice(index, 1);
        this._render();
      })
    );
    root.querySelectorAll("[data-add]").forEach((el) =>
      el.addEventListener("change", () => {
        this._collect();
        const where = el.dataset.add;
        const value = el.value.trim();
        const match = this._choices(where).find((c) => c.id === value || c.name.toLowerCase() === value.toLowerCase());
        if (!match) return;
        const list = this._list(where);
        if (!list.includes(match.id)) list.push(match.id);
        this._render();
      })
    );
    // ⓘ antippen klappt die Erklärung auf
    root.querySelectorAll("[data-info]").forEach((btn) =>
      btn.addEventListener("click", () => {
        const tip = root.querySelector(`[data-tip="${CSS.escape(btn.dataset.info)}"]`);
        if (tip) tip.hidden = !tip.hidden;
      })
    );
    // Empfehlung übernehmen; Erklärsatz zieht mit
    root.querySelectorAll('[data-act="proof-rec"]').forEach((btn) =>
      btn.addEventListener("click", (ev) => {
        this._collect();
        this._draft[ev.currentTarget.dataset.field] = Number(ev.currentTarget.dataset.value);
        this._render();
      })
    );
    root.querySelectorAll("[data-weak]").forEach((el) => el.addEventListener("change", redraw));
    root.querySelectorAll("[data-pa], [data-pl], [data-pmode], [data-pdoor]").forEach((el) => el.addEventListener("change", redraw));
    root.querySelectorAll("[data-geo]").forEach((el) => el.addEventListener("change", () => this._scheduleAdvice?.()));
    root.querySelector('[data-f="proof_window"]')?.addEventListener("input", (ev) => {
      const how = root.querySelector("[data-how]");
      if (how) how.textContent = this._proofHow({ ...this._draft, proof_window: Number(ev.target.value) || this._draft.proof_window });
    });
    root.querySelector('[data-f="proof_accuracy"]')?.addEventListener("change", redraw);
    // Auswahl, die andere Felder ein- oder ausblendet
    root.querySelectorAll('[data-f="behavior"], [data-f="action"], [data-b="enabled"]').forEach((el) => el.addEventListener("change", redraw));
    // „So verhält sich das:“ nach jeder Änderung neu (0.62)
    if (["pinrules", "silence", "learn", "helper"].includes(this.kind)) {
      root.querySelectorAll("[data-b], [data-f]").forEach((el) => el.addEventListener("change", redraw));
    }
  }

  _close() {
    this.dispatchEvent(new CustomEvent("hw-close", { bubbles: true, composed: true }));
  }
}

if (!customElements.get("hauswacht-system-editor")) {
  customElements.define("hauswacht-system-editor", HauswachtSystemEditor);
}
