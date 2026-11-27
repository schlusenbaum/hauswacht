// Hauswacht – Einstellungsseite in der Seitenleiste (ADR 0011), Stufe 1: alles auf einen Blick.
//
// Nur stabile Bausteine: eigene Web-Component, ha-card, ha-icon und die Farben des Themas.
// Die Abschnitte kommen aus der Karte "Hauswacht Übersicht" (dieselben Texte und Daten über
// den Websocket-Befehl hauswacht/overview, nur für Administratoren). Bearbeitet wird in dieser
// Stufe noch im Einstellungsdialog. Bearbeiten (ab Stufe 2) über eigene Seitenblätter:
// hauswacht-panel-edit.js (Melder), -profile.js (Profile), -rules.js (Auslöseregeln),
// -alarm.js (Alarmgeber, Benachrichtigungen).

// Profilzeile „Anwesenheit“: was die Automatik und „Bei Rückkehr“ gerade machen (ADR 0016)
function hauswachtProfileLine(p, t, now) {
  const mmss = (until) => {
    const left = Math.max(0, Math.round(until - now));
    return `${Math.floor(left / 60)}:${String(left % 60).padStart(2, "0")}`;
  };
  const parts = [];
  if (p.other_armed) parts.push(t.otherArmed.replace("{other}", p.other_armed));
  else if (p.armed) {
    parts.push((t.armedStates[p.state] || t.armedStates.armed) + (p.state === "armed" && p.auto ? ` ${t.auto}` : ""));
  } else if (p.due) parts.push(t.due.replace("{time}", mmss(p.due)));
  else if (p.away_persons) parts.push(t.whenAway.replace("{names}", (p.waiting || []).join(", ") || "–"));
  else parts.push(t.notArmed);
  const r = p["return"];
  if (r && !p.other_armed) {
    let text = t.ret.replace("{mode}", t.modes[r.mode] || r.mode);
    if (r.active && r.mode === "auto_only" && !p.auto) text += ` – ${t.notNow}`;
    else if (r.arrival_until && !r.door_until) text += ` – ${t.waitDoor.replace("{time}", mmss(r.arrival_until))}`;
    else if (r.door_until && !r.arrival_until) text += ` – ${t.waitHome.replace("{time}", mmss(r.door_until))}`;
    parts.push(text);
  }
  return parts.join(". ");
}

const TEXTS = {
  de: {
    title: "Hauswacht",
    loading: "Lade …",
    refresh: "Neu laden",
    hint: "Die ganze Einrichtung auf einen Blick – und alles direkt hier bearbeiten. Auch der Sirenentest geht hier (Reiter Alarmgeber) – mit Rückfrage, nur für Administratoren. Neu hier? Im Reiter „Dokumentation“ erklärt „So entscheidet Hauswacht“ die Abläufe in Bildern.",
    addRule: "Auslöseregel anlegen",
    addPerson: "Person anlegen",
    noPeople: "Noch keine Person. Ohne Personen schaltet jeder ohne PIN – mit Personen bekommt jede ihren PIN, ihre Karten und ihre Rechte.",
    inactive: "inaktiv",
    pin: "PIN",
    duressPin: "Bedrohungs-PIN",
    cardsN: "Karten",
    allRights: "alle Rechte",
    perArea: "Rechte je Bereich",
    noControls: "Noch kein Bedienteil.",
    unknownKeypad: "Unbekanntes Keypad „{k}“ hat sich um {t} gemeldet – noch nicht angelegt, deshalb abgelehnt.",
    createKeypad: "Anlegen",
    addControl: "Bedienteil anlegen",
    cardsTitle: "Karten, Anhänger und Schloss-Kennungen",
    noCards: "Noch keine Karte.",
    addCard: "Neue Karte anlernen",
    cardsNeedPerson: "Karten gehören immer einer Person – erst eine Person anlegen.",
    pinRules: "PIN-Regeln und Master-PIN",
    tonesTitle: "Ton je Sirene",
    speechTitle: "Sprachausgabe",
    noSpeaker: "kein Lautsprecher",
    quietLine: "Nachtruhe {a}–{b}",
    addHelper: "Melder aus Messwert erstellen",
    toneLabel: "Ton",
    toneAuto: "automatisch",
    fireReleased: "Brandton als Experte freigegeben",
    smokeDetector: "Rauchmelder (nie Brandton)",
    noSirens: "Noch keine Sirene eingetragen.",
    testTitle: "Sirenentest",
    testEvery: "Erinnerung alle {m} Monate",
    testOff: "keine Erinnerung",
    prewarnOn: "mit Vorwarnung",
    testCard: "Den Test startest du hier unten oder in der Karte „Hauswacht Test“. Sonst schaltet die Seite nie eine Sirene.",
    stWarn: "🔊 Hier ertönt eine echte Sirene – kurz und leise (3 s). Nur testen, wenn du vor Ort bist und Mitbewohner informiert sind.",
    stOk: "Ich bin vor Ort, Mitbewohner sind informiert",
    stLast: "Zuletzt getestet:",
    stNever: "Noch nie getestet",
    stTest: "Testen …",
    stAsk: "Sirene ertönt jetzt 3 s leise. Wirklich starten?",
    stStart: "Ja, starten",
    stCancel: "Abbrechen",
    stRunning: "Läuft … Rauchmelder mit Batterie reagieren oft erst nach einigen Sekunden – kurz warten.",
    stStop: "Stopp",
    stHeard: "Hast du die Sirene gehört?",
    stYes: "Ja, gehört",
    stNo: "Nein",
    stNone: "Keine Sirenen eingerichtet.",
    stAdmin: "Den Sirenentest dürfen nur Administratoren starten.",
    stBlocked: { siren_test_running: "Ein Sirenentest läuft gerade.", siren_test_armed: "Nur möglich, wenn alle Bereiche unscharf sind." },
    switchTitle: "Sirene aus Schalter erstellen",
    switchHint: "Für Sirenen, die in Home Assistant nur als Schalter erscheinen: legt den Helfer „Gerätetyp eines Schalters ändern“ an und trägt die Sirene ein.",
    masterSet: "Master-PIN gesetzt",
    masterNone: "kein Master-PIN",
    pinArm: "PIN auch zum Scharfschalten",
    addCode: "Aktions-Code anlegen",
    noKeypad: "Aktions-Codes gibt es nur mit Keypad – erst unter Bedienteile ein Keypad anlegen.",
    noCodes: "Noch kein Aktions-Code.",
    allKeypads: "alle Keypads",
    learnTime: "Anlernzeit für Karten: {m} min",
    restart: "Verhalten nach Neustart",
    behaviors: { restore: "Vorherigen Zustand wiederherstellen", armed: "Immer scharf", disarmed: "Immer unscharf" },
    continueAlarm: "laufender Alarm wird fortgesetzt",
    silence: "Funkstille von Sensoren",
    staleOwnTitle: "eigene Funkstille-Grenze",
    staleNever: "nie prüfen",
    staleGeneralL: "Allgemein",
    staleAdviceL: "Empfehlung {h} h (ohne Melder mit eigenem Wert)",
    measTitle: "Messungen",
    measOff: "Die Beobachtung ist aus – es wird nichts gemessen.",
    measSince: "Heimkommen gemessen seit {s} ({d} Tage, {n} Türöffnungen) · Weggehen gemessen seit {w} ({x} Tage)",
    measPerson: "Person",
    measHome: "Heimgekommen (mit Tür)",
    measLeft: "Rausgegangen mit Tür",
    measLongest: "längste Zeit bis „weg“",
    measPauses: "Schweigepausen (längste)",
    measExplain: "Was bedeuten die Spalten?",
    infoLabel: "Erklärung",
    measInfo: {
      measHome: "Wie oft die Person heimgekommen ist; in Klammern, wie oft dabei eine Eingangstür aufging.",
      measLeft: "Wie oft alle Signale der Person „weg“ meldeten und bis zu 15 Minuten vorher eine Eingangstür aufging – echtes Rausgehen.",
      measLongest: "Längste Zeit von „Tür auf“ bis alle Signale „weg“ melden. Daraus kommt die Empfehlung, wie lange Hauswacht später nach dem Rausgehen warten müsste.",
      measPauses: "Schweigepause: Alle Signale meldeten „weg“, aber in den 15 Minuten davor ging keine Eingangstür auf. Meist schläft das Handy oder das WLAN hakt – die Person ist zuhause. Es kann auch ein echtes Weggehen sein, dessen Signal erst nach mehr als 15 Minuten kam, oder ein Weggehen durch eine Tür ohne Kontakt. In Klammern die längste Pause in Minuten.",
    },
    measEntryDoor: "Eingang",
    measEntries: "Eingänge",
    measEntryLongest: "längste Zeit bis unscharf",
    measEntryAdvice: "Empfehlung Eingangsverzögerung",
    measShow: "Bericht anzeigen",
    measHide: "Bericht ausblenden",
    measSaveMd: "Bericht speichern",
    measSaveCsv: "Tabelle speichern (CSV)",
    measResetArrival: "Heimkommen zurücksetzen",
    measAskArrival: "Messung „Heimkommen“ löschen und neu beginnen? Weggehen und Eingänge bleiben erhalten.",
    measResetLeaving: "Weggehen zurücksetzen",
    presenceNow: {
      title: "Wer gilt gerade als zuhause?",
      hint: "Stand beim Öffnen der Seite oder nach „Aktualisieren“. Im Testmodus kannst du die Anwesenheit in der Testkarte simulieren.",
      states: { home: "zuhause", away: "weg", unknown: "unbekannt" },
      sim: "simuliert",
      home: "laut {by}",
      noProof: "kein Beleg – zählt nicht als weg",
      missNoFix: "es fehlt eine Ortung: Ortung mit Standort einrichten, ein Geofence-Signal als Ortung markieren oder „Tür + Signal“ erlauben (System → Anwesenheit)",
      missFix: "Ortung nicht frisch genug oder nicht außerhalb (Zeitfenster {w} min)",
      missWeak: "Tür + Signal: letzte Tür {door}, Signal weg {left} – beides muss innerhalb von {w} min zusammenkommen",
      entity: "eigener Auslöser, Zustand „{s}“",
      never: "nie",
      refresh: "Aktualisieren",
      unclear: "unklar: {by}",
      proofs: { fresh: "frische Ortung außerhalb", door: "Tür + Ortung außerhalb", weak: "Tür + Signal (unsicher)", one_door: "Tür + eines der Signale", one: "eines der Signale (ohne Tür, unsicher)", trigger: "eigener Auslöser", simulated: "simuliert", other: "Beleg vorhanden" },
      line: {
        otherArmed: "nicht nötig, „{other}“ ist scharf",
        armedStates: { armed: "ist scharf", arming: "wird scharf (Ausgangsverzögerung)", pending: "Eingangsverzögerung läuft", triggered: "Alarm", alarm_hold: "Alarm" },
        auto: "(automatisch)",
        due: "alle weg, wird scharf in {time}",
        whenAway: "wird scharf, wenn alle weg sind. Noch nicht weg: {names}",
        notArmed: "nicht scharf",
        ret: "Bei Rückkehr: {mode}",
        modes: { auto_only: "unscharf, nur wenn automatisch scharf", door: "unscharf mit Türbeleg", always: "unscharf, auch nach Scharfschalten von Hand", passage: "reinlassen (Durchgang)" },
        notNow: "greift jetzt nicht, weil von Hand scharf geschaltet",
        waitDoor: "Heimkehr erkannt, wartet auf die Tür (noch {time})",
        waitHome: "Tür gesehen, wartet auf eine Heimkehr (noch {time})",
      },
    },
    exitTitle: "Vorbereitung Ausgangserkennung",
    exitIntro: "Nur Messung, schaltet nichts. Gezählt wird erst 15 Minuten nach einer Türöffnung.",
    exitCols: {
      sign: "Lebenszeichen vor dem Rausgehen",
      confirm: "„noch da“ nach der Tür (typisch / längste)",
      missing: "ohne „noch da“",
      echo: "„zuhause“ nach dem Rausgehen",
    },
    exitInfo: {
      sign: "Wie oft beim Rausgehen kurz vorher (bis 3 Minuten) ein Signal der Person „zuhause“ meldete – von allen Malen, die sie durch eine Tür rausging. Nur mit so einem Lebenszeichen kann die Ausgangserkennung die Person später erkennen.",
      confirm: "Die Person bleibt zuhause (mit Lebenszeichen kurz vorher), während eine Tür aufgeht: So schnell meldet sich danach ein Signal wieder mit „zuhause“. So lange bliebe ein Einbruch mit Ausgangserkennung höchstens still.",
      missing: "Wie oft sich in diesem Fall 15 Minuten lang gar kein Signal mit „zuhause“ meldete – von allen Malen. Dann käme der Alarm erst am Ende der Wartezeit.",
      echo: "Wie oft Signale nach dem Öffnen noch „zuhause“ meldeten, obwohl die Person gerade rausging – in Klammern bis wie lange. Typisch für Ping mit Nachlaufzeit. Die Ausgangserkennung muss das berücksichtigen.",
    },
    measResetAll: "Alle Messungen zurücksetzen",
    measResetSilence: "Messung zurücksetzen",
    measAskLeaving: "Messung „Weggehen“ löschen und neu beginnen? Heimkommen und Eingänge bleiben erhalten.",
    measAskAll: "Alle Messungen der Heimkehr-Beobachtung löschen (Heimkehr, Eingänge, Weggehen) und neu beginnen? Einstellungen bleiben unverändert.",
    measAskSilence: "Funkstille-Messung aller Melder löschen und neu beginnen? Eigene Werte je Melder bleiben unverändert.",
    measDone: "Messung zurückgesetzt.",
    measSilenceSince: "gemessen seit {s}",
    staleTableHint: "Beobachtung je Melder seit {d} Tagen. Auf einen Melder klicken, um ihm einen eigenen Wert zu geben.",
    staleSensor: "Melder",
    staleLongest: "Längste Pause",
    staleAdviceCol: "Empfehlung",
    staleOwnCol: "Eigener Wert",
    silenceOff: "aus",
    hoursN: "{h} Stunden",
    network: "Funknetz und Gateways",
    homecoming: "Anwesenheit und Heimkehr-Beobachtung",
    observeOn: "Beobachtung läuft",
    observeOff: "Beobachtung aus",
    ssidsL: "Heim-WLAN",
    areas: "Bereiche",
    addArea: "Bereich anlegen",
    page: "Einstellungsseite",
    export: "Konfiguration herunterladen",
    exportText: "Eine Datei (JSON) mit allen Einstellungen, dem aktuellen Zustand, den Messungen und dem Check-up – für die Fehlersuche. Personen, Benutzer, Karten, Empfänger, WLAN-Namen und Geräte stehen darin nur als Platzhalter (Person 1, Karte 1 …), PINs und Codes als ***. Koordinaten sind nie dabei. Melder-, Zonen- und Profilnamen bleiben – bitte vor dem Weitergeben kurz drüberschauen.",
    exportBtn: "Herunterladen",
    pageOn: "in der Seitenleiste sichtbar",
    pageOff: "in der Seitenleiste ausgeblendet – erreichbar über die Geräteseite oder /hauswacht-settings",
    noRules: "Noch keine Auslöseregel. Eine Regel löst erst bei einer Abfolge aus, z. B. „Haustür, dann innerhalb von 60 s Keller“.",
    yamlOnly: "nur YAML",
    inProfiles: "Profile",
    inNoProfile: "in keinem Profil – wirkt nicht",
    editSirens: "Sirenen bearbeiten",
    editNotify: "Empfänger und Ereignisse bearbeiten",
    texts: "Eigene Texte",
    textsHint: "Titel und Text je Ereignis selbst formulieren – „Bearbeiten“ zeigt den Text von Hauswacht als Vorlage, mit Platzhaltern wie {melder}. „Standardtext“ setzt zurück.",
    ownText: "eigener Text",
    defaultText: "Text von Hauswacht",
    edit: "Bearbeiten",
    clickHint: "Auf einen Melder klicken: Gruppe, Typ, Immer aktiv und Ausnahmen je Profil ändern.",
    addGroup: "Meldergruppe anlegen",
    addProfile: "Alarmprofil anlegen",
    addTilt: "Kippstellung hinzufügen",
    addStrength: "Erschütterungsstärke hinzufügen",
    armedNote: "Ändern geht nur, wenn alle Bereiche unscharf sind.",
    saved: "Gespeichert.",
    asst: {
      title: "Check-up",
      intro: "Der Assistent prüft, ob deine Einstellungen zusammenpassen – auch mit den Messwerten aus der Beobachtung. Er ändert nichts von selbst: Jeden Vorschlag übernimmst du einzeln, nach einer Vorschau.",
      allGood: "Alles passt zusammen – der Assistent hat nichts gefunden.",
      count: "{e} Fehler · {w} Warnungen · {t} Tipps",
      levels: { error: "Fehler", warning: "Warnung", tip: "Tipp" },
      general: "Allgemein",
      why: "Warum?",
      preview: "Das ändert sich",
      inProfile: "Profil {p}",
      inSystem: "System → Anwesenheit",
      before: "bisher",
      after: "neu",
      add: "kommt dazu",
      remove: "fällt weg",
      weakens: "Achtung: Dieser Vorschlag macht die Anlage an einer Stelle nachgiebiger. Lies unter „Warum?“, weshalb er trotzdem sinnvoll sein kann.",
      confirm: "Ich habe das verstanden und möchte es übernehmen.",
      apply: "Übernehmen",
      cancel: "Abbrechen",
      applied: "Übernommen. Hauswacht lädt mit der neuen Einstellung.",
      recheck: "Neu prüfen",
      unavailable: "Der Check-up ist gerade nicht verfügbar. Bitte die Seite neu laden.",
      errors: {
        disarm_first: "Ändern geht nur, wenn alle Bereiche unscharf sind.",
        changed_elsewhere: "Inzwischen wurde etwas anderes geändert – der Check-up ist neu geladen. Bitte noch einmal ansehen.",
        fix_not_offered: "Dieser Vorschlag gilt nicht mehr (vermutlich schon behoben) – der Check-up ist neu geladen.",
        confirm_needed: "Bitte erst bestätigen.",
        failed: "Übernehmen hat nicht geklappt.",
      },
      goalsTitle: "Einrichten nach Zielen",
      goalsIntro: "Sag, was Hauswacht für dich tun soll – nachts absichern, automatisch scharf, wenn alle weg sind, beim Heimkommen unscharf. Der Assistent schlägt die Einstellungen vor und zeigt vor dem Übernehmen genau, was sich ändert.",
      goalsOpen: "Einrichten nach Zielen",
      scTitle: "Was passiert, wenn …?",
      scIntro: "Typische Situationen, durchgespielt mit deinen Einstellungen und Messwerten – mit denselben Regeln wie im Echtbetrieb, aber mit ausgedachter Uhr. Es wird nichts geschaltet.",
      scLoading: "Wird durchgespielt …",
      scNone: "Noch nichts durchzuspielen – die Profile haben keine Türen, Fenster oder Automatik.",
      scCount: "{b} unerwünscht · {w} mit Haken · {o} in Ordnung",
      scSteps: "Ablauf",
      scSimple: "Vereinfacht: Jede Person hat ein Handy, das „zuhause“ oder „weg“ meldet, und – wenn Hauswacht eine kennt – eine Ortung. Gemessene Zeiten zählen ab 3 Messungen.",
    },
    adminOnly: "Diese Seite ist nur für Administratoren.",
    error: "Fehler",
    tabs: {
      overview: "Übersicht",
      assistant: "Assistent",
      sensors: "Melder",
      profiles: "Profile",
      rules: "Auslöseregeln",
      sirens: "Alarmgeber",
      notifications: "Benachrichtigungen",
      people: "Personen und Bedienteile",
      system: "System",
      docs: "Dokumentation",
    },
    docsIntro: "Die Anleitung zu deiner Version ({v}) – öffnet sich in einem neuen Fenster. Das „?“ an jedem Abschnitt springt direkt an die passende Stelle.",
    docsAll: "Alle Seiten im Überblick",
    noGroup: "Ohne Meldergruppe",
    sensorsCount: "Melder",
    vibrationRule: "Erschütterung: Alarm bei {n} Meldungen in {s} s",
    special: "Besondere Melder",
    tilt: "Melder mit Kippstellung",
    tiltLine: "zu: {c} · gekippt: {t}",
    strength: "Erschütterungsstärken",
    strengthLine: "ab {v}",
    noSpecial: "Noch keine – mit den Knöpfen unten anlegen.",
    group: "Gruppe",
    none: "keine",
    noMatch: "Noch kein Melder – „+ Meldergruppe anlegen“.",
    reloadHint: "Die Seite konnte nicht angezeigt werden. Bitte den Browser bzw. die App einmal neu laden (nach einem Update hält der Browser oft noch die alte Version).",
  },
  en: {
    title: "Hauswacht",
    loading: "Loading …",
    refresh: "Reload",
    hint: "The whole setup at a glance – and edit everything right here. The siren test also works here (tab Alarm devices) – with confirmation, administrators only. New here? In the tab “Documentation”, “How Hauswacht decides” explains the flows in pictures.",
    addRule: "Add trigger rule",
    addPerson: "Add person",
    noPeople: "No person yet. Without people anyone operates without a PIN – with people, each gets their PIN, cards and rights.",
    inactive: "inactive",
    pin: "PIN",
    duressPin: "duress PIN",
    cardsN: "cards",
    allRights: "all rights",
    perArea: "rights per area",
    noControls: "No control device yet.",
    unknownKeypad: "Unknown keypad \"{k}\" reported at {t} – not set up yet, so it was refused.",
    createKeypad: "Set up",
    addControl: "Add control device",
    cardsTitle: "Cards, tags and lock IDs",
    noCards: "No card yet.",
    addCard: "Learn a new card",
    cardsNeedPerson: "Cards always belong to a person – add a person first.",
    pinRules: "PIN rules and master PIN",
    tonesTitle: "Tone per siren",
    speechTitle: "Speech",
    noSpeaker: "no speaker",
    quietLine: "quiet hours {a}–{b}",
    addHelper: "Create sensor from a measurement",
    toneLabel: "Tone",
    toneAuto: "automatic",
    fireReleased: "fire tone released by an expert",
    smokeDetector: "smoke detector (never fire tone)",
    noSirens: "No siren registered yet.",
    testTitle: "Siren test",
    testEvery: "Reminder every {m} months",
    testOff: "no reminder",
    prewarnOn: "with pre-warning",
    testCard: "Start the test down here or in the card “Hauswacht Test”. Otherwise the page never switches a siren.",
    stWarn: "🔊 A real siren sounds here – short and quiet (3 s). Only test when you are on site and housemates are informed.",
    stOk: "I am on site, housemates are informed",
    stLast: "Last tested:",
    stNever: "Never tested",
    stTest: "Test …",
    stAsk: "The siren will sound quietly for 3 s. Really start?",
    stStart: "Yes, start",
    stCancel: "Cancel",
    stRunning: "Running … battery smoke detectors often react only after a few seconds – wait a moment.",
    stStop: "Stop",
    stHeard: "Did you hear the siren?",
    stYes: "Yes, heard",
    stNo: "No",
    stNone: "No sirens set up.",
    stAdmin: "Only administrators may start the siren test.",
    stBlocked: { siren_test_running: "A siren test is running.", siren_test_armed: "Only possible when all areas are disarmed." },
    switchTitle: "Create siren from switch",
    switchHint: "For sirens that appear in Home Assistant only as a switch: creates the helper “change device type of a switch” and registers the siren.",
    masterSet: "master PIN set",
    masterNone: "no master PIN",
    pinArm: "PIN also to arm",
    addCode: "Add action code",
    noKeypad: "Action codes need a keypad – add a keypad under control devices first.",
    noCodes: "No action code yet.",
    allKeypads: "all keypads",
    learnTime: "Learning time for cards: {m} min",
    restart: "Behaviour after restart",
    behaviors: { restore: "Restore the previous state", armed: "Always armed", disarmed: "Always disarmed" },
    continueAlarm: "a running alarm continues",
    silence: "Sensor radio silence",
    staleOwnTitle: "own radio silence limit",
    staleNever: "never check",
    staleGeneralL: "General",
    staleAdviceL: "recommendation {h} h (without sensors with an own value)",
    measTitle: "Measurements",
    measOff: "The observation is off – nothing is being measured.",
    measSince: "Homecoming measured since {s} ({d} days, {n} door openings) · leaving measured since {w} ({x} days)",
    measPerson: "Person",
    measHome: "Came home (with door)",
    measLeft: "Left through a door",
    measLongest: "longest time until “away”",
    measPauses: "Silent pauses (longest)",
    measExplain: "What do the columns mean?",
    infoLabel: "Explanation",
    measInfo: {
      measHome: "How often the person came home; in brackets, how often an entry door opened.",
      measLeft: "How often all signals of the person reported “away” and an entry door opened up to 15 minutes before – real leaving.",
      measLongest: "Longest time from “door open” until all signals report “away”. The recommendation for how long Hauswacht would later have to wait after leaving comes from this.",
      measPauses: "Silent pause: all signals reported “away”, but no entry door opened in the 15 minutes before. Usually the phone sleeps or the Wi-Fi hiccups – the person is home. It can also be a real departure whose signal only came after more than 15 minutes, or leaving through a door without a contact. In brackets the longest pause in minutes.",
    },
    measEntryDoor: "Entry",
    measEntries: "Entries",
    measEntryLongest: "longest time until disarmed",
    measEntryAdvice: "Recommended entry delay",
    measShow: "Show report",
    measHide: "Hide report",
    measSaveMd: "Save report",
    measSaveCsv: "Save table (CSV)",
    measResetArrival: "Reset homecoming",
    measAskArrival: "Delete the “homecoming” measurement and start again? Leaving and entries are kept.",
    measResetLeaving: "Reset leaving",
    presenceNow: {
      title: "Who counts as home right now?",
      hint: "State when the page was opened or after “Refresh”. In test mode you can simulate presence in the test card.",
      states: { home: "home", away: "away", unknown: "unknown" },
      sim: "simulated",
      home: "according to {by}",
      noProof: "no proof – does not count as away",
      missNoFix: "a location is missing: set up a location with position, mark a geofence signal as location or allow “door + signal” (System → Presence)",
      missFix: "location not fresh enough or not outside (time window {w} min)",
      missWeak: "door + signal: last door {door}, signal away {left} – both must come together within {w} min",
      entity: "own trigger, state “{s}”",
      never: "never",
      refresh: "Refresh",
      unclear: "unclear: {by}",
      proofs: { fresh: "fresh location outside", door: "door + location outside", weak: "door + signal (uncertain)", one_door: "door + one of the signals", one: "one of the signals (no door, uncertain)", trigger: "own trigger", simulated: "simulated", other: "proof available" },
      line: {
        otherArmed: "not needed, \"{other}\" is armed",
        armedStates: { armed: "is armed", arming: "arming (exit delay)", pending: "entry delay running", triggered: "alarm", alarm_hold: "alarm" },
        auto: "(automatically)",
        due: "all away, armed in {time}",
        whenAway: "arms when everyone is away. Not away yet: {names}",
        notArmed: "not armed",
        ret: "On return: {mode}",
        modes: { auto_only: "disarm, only if armed automatically", door: "disarm with door proof", always: "disarm, also after arming by hand", passage: "let in (passage)" },
        notNow: "does not apply now, because armed by hand",
        waitDoor: "homecoming seen, waiting for the door ({time} left)",
        waitHome: "door seen, waiting for a homecoming ({time} left)",
      },
    },
    exitTitle: "Preparing exit detection",
    exitIntro: "Measurement only, switches nothing. Counted 15 minutes after a door opening.",
    exitCols: {
      sign: "Sign of life before leaving",
      confirm: "“still here” after the door (typical / longest)",
      missing: "no “still here”",
      echo: "“home” after leaving",
    },
    exitInfo: {
      sign: "How often a signal of the person reported “home” shortly before leaving (up to 3 minutes) – out of all times they left through a door. Only with such a sign of life can exit detection recognise the person later.",
      confirm: "The person stays home (with a sign of life shortly before) while a door opens: this is how fast a signal reports “home” again. A break-in would stay silent for at most this long with exit detection.",
      missing: "How often no signal reported “home” at all for 15 minutes in that case – out of all times. The alarm would then only come at the end of the waiting time.",
      echo: "How often signals still reported “home” after the door opened although the person was just leaving – in brackets for how long. Typical for ping with a grace period. Exit detection has to take this into account.",
    },
    measResetAll: "Reset all measurements",
    measResetSilence: "Reset measurement",
    measAskLeaving: "Delete the “leaving” measurement and start again? Homecoming and entries are kept.",
    measAskAll: "Delete all measurements of the homecoming observation (homecoming, entries, leaving) and start again? Settings stay unchanged.",
    measAskSilence: "Delete the silence measurement of all sensors and start again? Own values per sensor stay unchanged.",
    measDone: "Measurement reset.",
    measSilenceSince: "measured since {s}",
    staleTableHint: "Observation per sensor for {d} days. Click a sensor to give it an own value.",
    staleSensor: "Sensor",
    staleLongest: "Longest pause",
    staleAdviceCol: "Recommendation",
    staleOwnCol: "Own value",
    silenceOff: "off",
    hoursN: "{h} hours",
    network: "Radio networks and gateways",
    homecoming: "Presence and homecoming observation",
    observeOn: "observation running",
    observeOff: "observation off",
    ssidsL: "Home Wi-Fi",
    areas: "Areas",
    addArea: "Add area",
    page: "Settings page",
    export: "Download configuration",
    exportText: "A file (JSON) with all settings, the current state, the measurements and the check-up – for troubleshooting. People, users, cards, recipients, Wi-Fi names and devices only appear as placeholders (Person 1, Card 1 …), PINs and codes as ***. Coordinates are never included. Sensor, zone and profile names stay – please have a quick look before passing it on.",
    exportBtn: "Download",
    pageOn: "visible in the sidebar",
    pageOff: "hidden in the sidebar – reachable from the device page or /hauswacht-settings",
    noRules: "No trigger rule yet. A rule only triggers on a sequence, e.g. “front door, then basement within 60 s”.",
    yamlOnly: "YAML only",
    inProfiles: "Profiles",
    inNoProfile: "in no profile – no effect",
    editSirens: "Edit sirens",
    editNotify: "Edit recipients and events",
    texts: "Own texts",
    textsHint: "Write the title and text per event yourself – “Edit” shows Hauswacht's text as a template, with placeholders like {sensor}. “Default text” resets it.",
    ownText: "own text",
    defaultText: "Hauswacht's text",
    edit: "Edit",
    clickHint: "Click a sensor: change group, type, always active and exclusions per profile.",
    addGroup: "Add sensor group",
    addProfile: "Add alarm profile",
    addTilt: "Add tilt position",
    addStrength: "Add vibration strength",
    armedNote: "Changes are only possible while all areas are disarmed.",
    saved: "Saved.",
    asst: {
      title: "Check-up",
      intro: "The assistant checks whether your settings fit together – including the measurements from the observation. It changes nothing on its own: you apply each suggestion one by one, after a preview.",
      allGood: "Everything fits together – the assistant found nothing.",
      count: "{e} errors · {w} warnings · {t} tips",
      levels: { error: "Error", warning: "Warning", tip: "Tip" },
      general: "General",
      why: "Why?",
      preview: "What changes",
      inProfile: "Profile {p}",
      inSystem: "System → Presence",
      before: "before",
      after: "new",
      add: "is added",
      remove: "is removed",
      weakens: "Caution: this suggestion makes the system more lenient in one place. See “Why?” for why it can still make sense.",
      confirm: "I understand and want to apply it.",
      apply: "Apply",
      cancel: "Cancel",
      applied: "Applied. Hauswacht reloads with the new setting.",
      recheck: "Check again",
      unavailable: "The check-up is not available right now. Please reload the page.",
      errors: {
        disarm_first: "Changes are only possible while all areas are disarmed.",
        changed_elsewhere: "Something else was changed in the meantime – the check-up has been reloaded. Please look again.",
        fix_not_offered: "This suggestion no longer applies (probably already fixed) – the check-up has been reloaded.",
        confirm_needed: "Please confirm first.",
        failed: "Applying did not work.",
      },
      goalsTitle: "Set up by goals",
      goalsIntro: "Tell Hauswacht what it should do for you – secure the night, arm automatically when everyone is away, disarm when coming home. The assistant suggests the settings and shows exactly what changes before you apply.",
      goalsOpen: "Set up by goals",
      scTitle: "What happens if …?",
      scIntro: "Typical situations, played through with your settings and measurements – with the same rules as in real operation, but with a made-up clock. Nothing is switched.",
      scLoading: "Playing it through …",
      scNone: "Nothing to play through yet – the profiles have no doors, windows or automation.",
      scCount: "{b} unwanted · {w} with a catch · {o} fine",
      scSteps: "Sequence",
      scSimple: "Simplified: every person has a phone that reports “home” or “away” and – if Hauswacht knows one – a location. Measured times count from 3 measurements on.",
    },
    adminOnly: "This page is for administrators only.",
    error: "Error",
    tabs: {
      overview: "Overview",
      assistant: "Assistant",
      sensors: "Sensors",
      profiles: "Profiles",
      rules: "Trigger rules",
      sirens: "Alarm devices",
      notifications: "Notifications",
      people: "People and control devices",
      system: "System",
      docs: "Documentation",
    },
    docsIntro: "The documentation for your version ({v}) – opens in a new window. The “?” on every section jumps straight to the right place.",
    docsAll: "All pages at a glance",
    noGroup: "Without sensor group",
    sensorsCount: "sensors",
    vibrationRule: "Vibration: alarm at {n} reports in {s} s",
    special: "Special sensors",
    tilt: "Sensors with tilt position",
    tiltLine: "closed: {c} · tilted: {t}",
    strength: "Vibration strengths",
    strengthLine: "from {v}",
    noSpecial: "None yet – create them with the buttons below.",
    group: "Group",
    none: "none",
    noMatch: "No sensor yet – “+ Add sensor group”.",
    reloadHint: "The page could not be shown. Please reload the browser or app once (after an update the browser often still holds the old version).",
  },
};

const TABS = ["overview", "assistant", "sensors", "profiles", "rules", "sirens", "notifications", "people", "system", "docs"];
// Welche Abschnitte der Übersicht in welchem Reiter stehen
const TAB_PARTS = {
  overview: ["findings", "status"],
  profiles: ["profiles"],
  rules: ["rules"],
  sirens: ["sirens"],
  notifications: ["notifications"],
  people: ["users", "controls", "actionCodes"],
  system: ["monitoring"],
};
// Welche Stelle der Anleitung das „?“ eines Abschnitts öffnet (siehe hauswacht-panel-docs.js)
const PART_HELP = {
  findings: "findings",
  status: "status",
  profiles: "profiles",
  rules: "rules",
  sirens: "sirens",
  notifications: "notifications",
  users: "users",
  controls: "controls",
  actionCodes: "actionCodes",
  monitoring: "network",
};
const EDITOR_HELP = { group: "groups", tilt: "tilt", strength: "strength", always: "always", sensor: "types" };
const STORE_KEY = "hauswacht-panel-tab";

const PANEL_STYLE = `
  :host { display: block; background: var(--primary-background-color); min-height: 100vh; color: var(--primary-text-color); }
  .top { display: flex; align-items: center; gap: 8px; padding: 0 12px; height: 56px;
    background: var(--app-header-background-color, var(--primary-color)); color: var(--app-header-text-color, #fff); }
  .top .t { font-size: 1.25rem; flex: 1; display: flex; align-items: center; gap: 10px; }
  .top button { background: none; border: none; color: inherit; cursor: pointer; padding: 8px; border-radius: 50%; display: flex; }
  .top a, .top .lnk { color: inherit; font: inherit; font-size: .9rem; cursor: pointer; background: none;
    border: 1px solid currentColor; border-radius: 18px; padding: 4px 12px; opacity: .9; text-decoration: none; }
  .tabs { display: flex; gap: 4px; overflow-x: auto; padding: 0 12px;
    background: var(--app-header-background-color, var(--primary-color)); }
  .tabs button { font: inherit; font-size: .95rem; background: none; border: none; cursor: pointer; white-space: nowrap;
    color: var(--app-header-text-color, #fff); opacity: .75; padding: 10px 12px; border-bottom: 3px solid transparent; }
  .tabs button.on { opacity: 1; border-bottom-color: currentColor; }
  .content { max-width: 1100px; margin: 0 auto; padding: 16px; }
  .note { color: var(--secondary-text-color); font-size: .9rem; margin: 0 0 12px; }
  ha-card { margin-bottom: 16px; }
  .tool { display: flex; gap: 8px; flex-wrap: wrap; margin: 6px 0 4px; }
  .sirentest { margin-top: 12px; padding-top: 10px; border-top: 1px solid var(--divider-color); }
  .sirentest .warn { color: var(--error-color); margin-bottom: 6px; }
  .sirentest .st-ok { display: block; margin: 6px 0; cursor: pointer; }
  .meas { margin-top: 12px; padding-top: 10px; border-top: 1px solid var(--divider-color); }
  .meas > .n { font-weight: 500; margin-bottom: 4px; }
  .report { margin-top: 8px; padding: 8px 12px; border-radius: 8px; background: var(--secondary-background-color); overflow-x: auto; }
  pre.report { white-space: pre-wrap; font-size: 12px; }
  button.e { font: inherit; font-size: .85rem; padding: 4px 12px; border-radius: 16px; cursor: pointer;
    border: 1px solid var(--divider-color); background: var(--card-background-color); color: var(--primary-color); }
  a.lnk { color: var(--primary-color); cursor: pointer; }
  a.lnk:hover { text-decoration: underline; }
  tr.grp button.e { margin-left: 8px; padding: 1px 10px; }
  .item button.e { float: right; }
  .ok { color: var(--success-color, #43a047); margin: 0 0 10px; }
  tr.grp td { background: var(--secondary-background-color); font-weight: 500; }
  tr.grp .muted { font-weight: 400; }
  th .info { border: none; background: none; color: var(--primary-color); cursor: help; font: inherit; font-weight: 400; padding: 0 2px; }
  .tip[hidden] { display: none; }
  .tip { display: block; font-size: .85rem; margin: 4px 0 6px; padding: 8px 10px; border-radius: 6px; background: var(--secondary-background-color); }
  details.explain { margin: 6px 0; font-size: .85rem; }
  details.explain summary { cursor: pointer; color: var(--primary-color); }
  details.explain div { margin: 4px 0; }
  h3 { margin: 12px 0 4px; font-size: 1rem; font-weight: 500; }
  .asst { border-left: 4px solid var(--divider-color); border-radius: 6px; padding: 8px 10px; margin: 6px 0; background: var(--secondary-background-color); }
  .asst.error { border-left-color: var(--error-color, #db4437); }
  .asst.warning { border-left-color: var(--warning-color, #ffa600); }
  .asst.tip { border-left-color: var(--info-color, #039be5); }
  .asst.ok { border-left-color: var(--success-color, #43a047); }
  .asst .fixes { margin-top: 6px; display: flex; flex-wrap: wrap; gap: 6px; }
  .asst .preview { border: 1px solid var(--divider-color); border-radius: 8px; padding: 8px 10px; background: var(--card-background-color); width: 100%; }
  .asst .preview div { margin: 3px 0; }
  .asst-warn { color: var(--warning-color, #ffa600); margin: 6px 0; }
  .asst-err { color: var(--error-color, #db4437); margin: 8px 0; }
  .asst label.chk { display: block; margin: 6px 0; cursor: pointer; }
  button.e:disabled { opacity: .5; cursor: not-allowed; }
`;

const escHtml = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

class HauswachtPanel extends HTMLElement {
  constructor() {
    super();
    this._data = null;
    this._error = null;
    try {
      this._tab = localStorage.getItem(STORE_KEY) || "overview";
    } catch (_err) {
      this._tab = "overview";
    }
    if (!TABS.includes(this._tab)) this._tab = "overview";
  }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    if (first) {
      this.attachShadow({ mode: "open" });
      this._start();
      return;
    }
    // Sirenentest: nur den Kasten neu zeichnen, wenn sich der Test-Sensor ändert
    const id = this._sirenTestEntity();
    const state = id ? hass.states[id] : undefined;
    if (state !== this._stState) this._renderSirenTest();
  }

  // --- Sirenentest (echte Sirene!) – gleicher Weg wie die Testkarte -------------------------
  // Alle Sperren prüft Hauswacht im Hintergrund (unscharf, Freigabe, Testmodus aus, keine
  // Brandsperre, nur Einbruchtöne, höchstens 10 s, nur Administratoren). Die Seite ruft nur die
  // Dienste hauswacht.siren_test / siren_test_result / siren_test_stop auf.

  _sirenTestEntity() {
    if (this._stIds === undefined || !this._stIds.sensor) {
      const ids = {};
      for (const [entityId, entry] of Object.entries((this._hass && this._hass.entities) || {})) {
        if (entry.platform !== "hauswacht") continue;
        if (entityId.startsWith("sensor.") && entry.translation_key === "siren_test") ids.sensor = entityId;
        if (entityId.startsWith("alarm_control_panel.") && !ids.panel) ids.panel = entityId;
      }
      this._stIds = ids;
    }
    return this._stIds.sensor;
  }

  _renderSirenTest() {
    const box = this.shadowRoot && this.shadowRoot.getElementById("sirentest");
    if (!box) return;
    const id = this._sirenTestEntity();
    const state = id ? this._hass.states[id] : undefined;
    this._stState = state;
    const info = (state && state.attributes) || {};
    const sirens = Array.isArray(info.sirens) ? info.sirens : [];
    const parts = [`<div class="hint warn">${escHtml(this._t("stWarn"))}</div>`];
    if (!this._hass.user || !this._hass.user.is_admin) {
      box.innerHTML = parts.join("") + `<div class="muted">${escHtml(this._t("stAdmin"))}</div>`;
      return;
    }
    if (!id || !sirens.length) {
      box.innerHTML = parts.join("") + `<div class="muted">${escHtml(this._t("stNone"))}</div>`;
      return;
    }
    if (info.blocked) parts.push(`<div class="muted">⛔ ${escHtml((this._t("stBlocked") || {})[info.blocked] || info.blocked)}</div>`);
    parts.push(`<label class="st-ok"><input type="checkbox" data-st="ok" ${this._stOk ? "checked" : ""}> ${escHtml(this._t("stOk"))}</label>`);
    const ask = this._stAsk;
    for (const unit of sirens) {
      const sid = escHtml(unit.entity_id);
      const mark = unit.heard === true ? " ✅" : unit.heard === false ? " ❌" : "";
      let line = unit.last_test
        ? `${this._t("stLast")} ${new Date(unit.last_test).toLocaleString(this._hass.language)}${mark}`
        : this._t("stNever");
      let buttons = "";
      if (info.running === unit.entity_id) {
        line = this._t("stRunning");
        buttons = `<button class="e" data-st="stop">${escHtml(this._t("stStop"))}</button>`;
      } else if (ask && ask.siren === unit.entity_id && ask.step === "confirm") {
        line = this._t("stAsk");
        buttons = `<button class="e" data-st="start" data-siren="${sid}">${escHtml(this._t("stStart"))}</button><button class="e" data-st="cancel">${escHtml(this._t("stCancel"))}</button>`;
      } else if (ask && ask.siren === unit.entity_id && ask.step === "heard") {
        line = this._t("stHeard");
        buttons = `<button class="e" data-st="heard" data-siren="${sid}" data-heard="1">${escHtml(this._t("stYes"))}</button><button class="e" data-st="heard" data-siren="${sid}" data-heard="0">${escHtml(this._t("stNo"))}</button>`;
      } else {
        const off = info.blocked || ask || !this._stOk ? "disabled" : "";
        buttons = `<button class="e" data-st="ask" data-siren="${sid}" ${off}>${escHtml(this._t("stTest"))}</button>`;
      }
      parts.push(`<div class="item"><div class="tool" style="float:right;margin:0">${buttons}</div><div class="n">${escHtml(unit.name || unit.entity_id)}</div><div class="muted">${escHtml(line)}</div></div>`);
    }
    box.innerHTML = parts.join("");
    box.querySelectorAll("[data-st]").forEach((el) => {
      const kind = el.dataset.st;
      el.addEventListener(kind === "ok" ? "change" : "click", () => this._sirenTestAction(kind, el));
    });
  }

  async _sirenTestAction(kind, el) {
    const panel = this._stIds && this._stIds.panel;
    const siren = el.dataset.siren;
    const redraw = () => this._renderSirenTest();
    if (kind === "ok") {
      this._stOk = el.checked;
      return redraw();
    }
    if (kind === "ask") {
      this._stAsk = { siren, step: "confirm" };
      return redraw();
    }
    if (kind === "cancel") {
      this._stAsk = null;
      return redraw();
    }
    try {
      if (kind === "start") {
        this._stAsk = { siren, step: "heard" };
        redraw();
        await this._hass.callService("hauswacht", "siren_test", { entity_id: panel, siren });
      } else if (kind === "stop") {
        await this._hass.callService("hauswacht", "siren_test_stop", { entity_id: panel });
      } else if (kind === "heard") {
        this._stAsk = null;
        redraw();
        await this._hass.callService("hauswacht", "siren_test_result", { entity_id: panel, siren, heard: el.dataset.heard === "1" });
      }
    } catch (err) {
      if (kind === "start") this._stAsk = null; // abgelehnt (z. B. Testmodus): keine Rückfrage
      this._error = `${this._t("error")}: ${err?.message || err}`;
      this._render();
    }
  }

  set narrow(value) {
    this._narrow = value;
    if (this.shadowRoot && this._ready) this._render();
  }

  set panel(panel) {
    this._panel = panel;
  }

  get _lang() {
    return (this._hass?.language || "en").startsWith("de") ? "de" : "en";
  }

  _t(key) {
    return TEXTS[this._lang][key] ?? TEXTS.en[key] ?? key;
  }

  async _start() {
    this._render();
    // Die Abschnitte stammen aus der Übersichtskarte – sie wird beim Start mitgeladen
    if (!window.HauswachtOverviewView || typeof window.HauswachtOverviewView.prototype._parts !== "function") {
      window.HauswachtOverviewView = undefined;
      const version = this._panel?.config?.version || "0";
      try {
        await import(`/hauswacht/hauswacht-uebersicht-card.js?v=${version}`);
      } catch (_err) {
        // bleibt leer; _load meldet den Fehler
      }
    }
    const version = this._panel?.config?.version || "0";
    try {
      await import(`/hauswacht/hauswacht-panel-docs.js?v=${version}`);
      if (window.HauswachtDocs) window.HauswachtDocs.version = version;
    } catch (_err) {
      // ohne Verweise auf die Anleitung weiter nutzbar
    }
    try {
      await import(`/hauswacht/hauswacht-panel-edit.js?v=${this._panel?.config?.version || "0"}`);
      await import(`/hauswacht/hauswacht-panel-profile.js?v=${this._panel?.config?.version || "0"}`);
      await import(`/hauswacht/hauswacht-panel-alarm.js?v=${this._panel?.config?.version || "0"}`);
      await import(`/hauswacht/hauswacht-panel-rules.js?v=${this._panel?.config?.version || "0"}`);
      await import(`/hauswacht/hauswacht-panel-people.js?v=${this._panel?.config?.version || "0"}`);
      await import(`/hauswacht/hauswacht-panel-system.js?v=${this._panel?.config?.version || "0"}`);
      await import(`/hauswacht/hauswacht-panel-controls.js?v=${this._panel?.config?.version || "0"}`);
      await import(`/hauswacht/hauswacht-panel-goals.js?v=${this._panel?.config?.version || "0"}`);
    } catch (_err) {
      // ohne Bearbeiten weiter nutzbar
    }
    this._ready = true;
    await this._load();
  }

  async _load() {
    this._error = null;
    this._scenarios = undefined;
    try {
      [this._data, this._settings, this._advice] = await Promise.all([
        this._hass.callWS({ type: "hauswacht/overview" }),
        this._hass.callWS({ type: "hauswacht/settings/get" }).catch(() => null),
        this._fetchAdvice(),
      ]);
    } catch (err) {
      this._data = null;
      this._error = err && err.code === "unauthorized" ? this._t("adminOnly") : `${this._t("error")}: ${err?.message || err}`;
    }
    this._render();
  }

  async _reloadAfterSave(expected) {
    // Nach dem Speichern lädt Hauswacht neu. Erst wenn es mit dem neuen Stand läuft
    // (loaded_revision), die Übersicht holen – sonst käme noch der alte Stand (bis 15 s).
    for (let i = 0; i < 20; i++) {
      await new Promise((r) => setTimeout(r, 750));
      try {
        const settings = await this._hass.callWS({ type: "hauswacht/settings/get" });
        if (expected && settings.loaded_revision !== expected && i < 19) continue;
        this._settings = settings;
        this._data = await this._hass.callWS({ type: "hauswacht/overview" });
        this._advice = await this._fetchAdvice();
        this._scenarios = undefined;
        this._error = null;
        break;
      } catch (_err) {
        // noch nicht wieder geladen
      }
    }
    this._render();
  }


  _openEditor(kind, item) {
    if (!customElements.get("hauswacht-sensor-editor") || !this._settings) return;
    const view = this._view();
    const editor = document.createElement("hauswacht-sensor-editor");
    editor.addEventListener("hw-close", () => this._closeEditor());
    editor.addEventListener("hw-saved", (ev) => {
      this._closeEditor();
      this._flash = this._t("saved");
      this._reloadAfterSave(ev.detail?.revision);
    });
    editor.addEventListener("hw-stale", () => this._reloadAfterSave());
    this._editor = editor;
    this.shadowRoot.appendChild(editor);
    editor.open({
      hass: this._hass,
      settings: this._settings,
      typeLabel: (t) => (view ? view._l("type", t) : t),
      kind,
      item,
      helpKey: EDITOR_HELP[kind],
    });
  }

  _openProfileEditor(profileId) {
    if (!customElements.get("hauswacht-profile-editor") || !this._settings?.profile_edit) return;
    const editor = document.createElement("hauswacht-profile-editor");
    editor.addEventListener("hw-close", () => this._closeEditor());
    editor.addEventListener("hw-saved", (ev) => {
      this._closeEditor();
      this._flash = this._t("saved");
      this._reloadAfterSave(ev.detail?.revision);
    });
    editor.addEventListener("hw-stale", () => this._reloadAfterSave());
    this._editor = editor;
    this.shadowRoot.appendChild(editor);
    editor.open({ hass: this._hass, settings: this._settings, profile: profileId || null });
  }

  _openAlarmEditor(kind, event) {
    if (!customElements.get("hauswacht-alarm-editor") || !this._settings?.notify) return;
    const view = this._view();
    const editor = document.createElement("hauswacht-alarm-editor");
    editor.addEventListener("hw-close", () => this._closeEditor());
    editor.addEventListener("hw-saved", (ev) => {
      this._closeEditor();
      this._flash = this._t("saved");
      this._reloadAfterSave(ev.detail?.revision);
    });
    editor.addEventListener("hw-stale", () => this._reloadAfterSave());
    this._editor = editor;
    this.shadowRoot.appendChild(editor);
    editor.open({
      hass: this._hass,
      settings: this._settings,
      kind,
      event,
      siren: event,
      eventLabel: (e) => (view ? view._l("event", e) : e),
    });
  }

  _openRuleEditor(ruleId) {
    const edit = this._settings?.rule_edit;
    if (!customElements.get("hauswacht-rule-editor") || !edit) return;
    const editor = document.createElement("hauswacht-rule-editor");
    editor.addEventListener("hw-close", () => this._closeEditor());
    editor.addEventListener("hw-saved", (ev) => {
      this._closeEditor();
      this._flash = this._t("saved");
      this._reloadAfterSave(ev.detail?.revision);
    });
    editor.addEventListener("hw-stale", () => this._reloadAfterSave());
    this._editor = editor;
    this.shadowRoot.appendChild(editor);
    editor.open({ hass: this._hass, settings: this._settings, rule: ruleId ? edit.rules.find((r) => r.id === ruleId) : null });
  }

  _rulesTab(view) {
    const edit = this._settings?.rule_edit;
    if (!edit) {
      const parts = view._parts();
      return this._card(parts.rules[0], parts.rules[2], "rules");
    }
    const names = Object.fromEntries(edit.rule_choices.profiles.map((p) => [p.id, p.name]));
    const tools = this._armedOr(`<div class="tool">${this._btn("rule:", "+ " + this._t("addRule"))}</div>`);
    const list = edit.rules.length
      ? edit.rules
          .map((r) => {
            const where = r.profiles.length
              ? `${escHtml(this._t("inProfiles"))}: ${escHtml(r.profiles.map((p) => names[p] || p).join(", "))}`
              : `<span class="warn">${escHtml(this._t("inNoProfile"))}</span>`;
            return `<div class="item">${this._btn(`rule:${r.id}`, this._t("edit"))}<div class="n">${escHtml(r.name)}${r.ui ? "" : ` <span class="muted">(${escHtml(this._t("yamlOnly"))})</span>`}</div><div>${escHtml(r.text)}</div><div class="muted">${where}</div></div>`;
          })
          .join("")
      : `<div class="muted">${escHtml(this._t("noRules"))}</div>`;
    return this._card(this._t("tabs").rules, tools + list, "rules");
  }

  _openPersonEditor(personId) {
    if (!customElements.get("hauswacht-person-editor") || !this._settings?.people) return;
    const editor = document.createElement("hauswacht-person-editor");
    editor.addEventListener("hw-close", () => this._closeEditor());
    editor.addEventListener("hw-saved", (ev) => {
      this._closeEditor();
      this._flash = this._t("saved");
      this._reloadAfterSave(ev.detail?.revision);
    });
    editor.addEventListener("hw-stale", () => this._reloadAfterSave());
    this._editor = editor;
    this.shadowRoot.appendChild(editor);
    editor.open({ hass: this._hass, settings: this._settings, person: personId || null });
  }

  _peopleTab(view) {
    const parts = view._parts();
    const people = this._settings?.people;
    let users;
    if (people) {
      const tools = this._armedOr(`<div class="tool">${this._btn("person:", "+ " + this._t("addPerson"))}</div>`);
      const list = people.users.length
        ? people.users
            .map((u) => {
              const bits = [
                u.rights === "per_area" ? this._t("perArea") : this._t("allRights"),
                u.has_pin ? this._t("pin") : null,
                u.has_duress ? this._t("duressPin") : null,
                u.cards ? `${u.cards} ${this._t("cardsN")}` : null,
              ].filter(Boolean);
              return `<div class="item">${this._btn(`person:${u.id}`, this._t("edit"))}<div class="n">${escHtml(u.name)}${u.active ? "" : ` <span class="warn">(${escHtml(this._t("inactive"))})</span>`}</div><div class="muted">${escHtml(bits.join(" · "))}</div></div>`;
            })
            .join("")
        : `<div class="muted">${escHtml(this._t("noPeople"))}</div>`;
      users = this._card(parts.users[0], tools + list, "users");
    } else {
      users = this._card(parts.users[0], parts.users[2], "users");
    }
    const note = "";
    const sys = this._settings?.system;
    if (!sys) {
      return (
        users +
        this._card(parts.controls[0], note + parts.controls[2], "controls") +
        this._card(parts.actionCodes[0], parts.actionCodes[2], "actionCodes")
      );
    }
    const r = sys.pin_rules;
    const pinRules = this._card(
      this._t("pinRules"),
      `<div class="muted">${escHtml([r.master ? this._t("masterSet") : this._t("masterNone"), r.code_arm_required ? this._t("pinArm") : null].filter(Boolean).join(" · "))}</div>` +
        this._armedOr(`<div class="tool">${this._btn("sys:pinrules", this._t("edit"))}</div>`),
      "pinRules"
    );
    const kindLabel = (k) => (view._l ? view._l("kind", k) : k);
    const ctrlList = sys.controls.items.length
      ? sys.controls.items
          .map((c) => `<div class="item">${this._btn(`ctrl:${c.id}`, this._t("edit"))}<div class="n">${escHtml(c.name)} <span class="muted">${escHtml(kindLabel(c.kind))}</span></div></div>`)
          .join("")
      : `<div class="muted">${escHtml(this._t("noControls"))}</div>`;
    const unknown = (sys.controls.unknown_keypads || [])
      .map((u) => `<div class="item">${this._armedOr(this._btn(`ctrlnew:${u.ref}`, this._t("createKeypad")))}<div class="warn">${escHtml(this._fmt("unknownKeypad", { k: u.ref, t: u.when }))}</div></div>`)
      .join("");
    const controls = this._card(
      parts.controls[0],
      unknown +
        ctrlList +
        this._armedOr(`<div class="tool">${this._btn("ctrl:", "+ " + this._t("addControl"))}</div>`) +
        `<div class="muted">${escHtml(this._fmt("learnTime", { m: sys.controls.learn_minutes }))} ${this._btn("sys:learn", this._t("edit"))}</div>`,
      "controls"
    );
    const cardsData = sys.cards;
    const cardList = cardsData.cards.length
      ? cardsData.cards
          .map((c) => `<div class="item">${this._btn(`card:${c.tag}`, this._t("edit"))}<div class="n">${c.active ? "🟢" : "⏸️"} ${escHtml(c.name ? `${c.name} (${c.label})` : c.label)}</div><div class="muted">${escHtml(c.user_name)}</div></div>`)
          .join("")
      : `<div class="muted">${escHtml(this._t("noCards"))}</div>`;
    const cards = this._card(
      this._t("cardsTitle"),
      cardList +
        (cardsData.users.length
          ? this._armedOr(`<div class="tool">${this._btn("cardnew:", "+ " + this._t("addCard"))}</div>`)
          : `<div class="muted">${escHtml(this._t("cardsNeedPerson"))}</div>`),
      "cards"
    );
    const ac = sys.action_codes;
    const keypadName = (id) => (id === ac.all_keypads ? this._t("allKeypads") : (ac.keypads.find((k) => k.id === id) || { name: id }).name);
    const codeList = ac.codes.length
      ? ac.codes
          .map((c) => `<div class="item">${this._btn(`sys:actioncode:${c.id}`, this._t("edit"))}<div class="n">${escHtml(c.name)}</div><div class="muted">${escHtml(`${c.code} + ${view._l("key", c.key)} · ${keypadName(c.keypad)} → ${view._l("codeAction", c.action)}${c.profile ? ` (${(sys.profiles.find((p) => p.id === c.profile) || { name: c.profile }).name})` : ""}`)}</div></div>`)
          .join("")
      : `<div class="muted">${escHtml(this._t("noCodes"))}</div>`;
    const codes = this._card(
      parts.actionCodes[0],
      ac.keypads.length
        ? codeList + this._armedOr(`<div class="tool">${this._btn("sys:actioncode:", "+ " + this._t("addCode"))}</div>`)
        : `<div class="muted">${escHtml(this._t("noKeypad"))}</div>`,
      "actionCodes"
    );
    return users + pinRules + cards + controls + codes;
  }

  _openControlEditor(kind, item, extra = {}) {
    if (!customElements.get("hauswacht-control-editor") || !this._settings?.system) return;
    const editor = document.createElement("hauswacht-control-editor");
    editor.addEventListener("hw-close", () => this._closeEditor());
    editor.addEventListener("hw-saved", (ev) => {
      this._closeEditor();
      this._flash = this._t("saved");
      this._reloadAfterSave(ev.detail?.revision);
    });
    editor.addEventListener("hw-stale", () => this._reloadAfterSave());
    this._editor = editor;
    this.shadowRoot.appendChild(editor);
    editor.open({ hass: this._hass, settings: this._settings, kind, item: item || null, ...extra });
  }

  _openSystemEditor(kind, item) {
    if (!customElements.get("hauswacht-system-editor") || !this._settings?.system) return;
    const editor = document.createElement("hauswacht-system-editor");
    editor.addEventListener("hw-close", () => this._closeEditor());
    editor.addEventListener("hw-saved", (ev) => {
      this._closeEditor();
      this._flash = this._t("saved");
      this._reloadAfterSave(ev.detail?.revision);
    });
    editor.addEventListener("hw-stale", () => this._reloadAfterSave());
    this._editor = editor;
    this.shadowRoot.appendChild(editor);
    const view = this._view();
    editor.open({ hass: this._hass, settings: this._settings, kind, item: item || null, typeLabel: (t) => (view ? view._l("type", t) : t) });
  }

  _silenceHtml(sil) {
    // Allgemeiner Wert und Beobachtung je Melder mit Empfehlung und eigenem Wert
    const general = `<div>${escHtml(this._t("staleGeneralL"))}: ${escHtml(sil.hours ? this._fmt("hoursN", { h: sil.hours }) : this._t("silenceOff"))}${sil.advice ? ` · ${escHtml(this._fmt("staleAdviceL", { h: sil.advice }))}` : ""}</div>`;
    const reset = this._canEdit
      ? `<div class="tool">${sil.since ? `<span class="muted">${escHtml(this._fmt("measSilenceSince", { s: sil.since }))}</span> ` : ""}<button class="e" data-a="reset-silence">${escHtml(this._t("measResetSilence"))}</button></div>`
      : "";
    const rows = Object.entries(sil.sensors || {})
      .map(([id, o]) => {
        const own = id in sil.overrides ? (sil.overrides[id] ? `${sil.overrides[id]} h` : this._t("staleNever")) : "–";
        const tight = sil.overrides[id] && o.advice && sil.overrides[id] < o.advice ? " ⚠️" : "";
        const label = this._canEdit ? `<a class="lnk" data-edit="sensor:${escHtml(id)}">${escHtml(o.name)}</a>` : escHtml(o.name);
        return `<tr><td>${label}</td><td class="nw">${escHtml(o.longest)}</td><td class="nw">${o.advice ? `${o.advice} h` : "–"}</td><td class="nw">${escHtml(own)}${tight}</td></tr>`;
      })
      .join("");
    const table = rows
      ? `<div class="muted" style="margin-top:8px">${escHtml(this._fmt("staleTableHint", { d: sil.days }))}</div><div class="scroll"><table><tr><th>${escHtml(this._t("staleSensor"))}</th><th>${escHtml(this._t("staleLongest"))}</th><th>${escHtml(this._t("staleAdviceCol"))}</th><th>${escHtml(this._t("staleOwnCol"))}</th></tr>${rows}</table></div>`
      : `<div class="muted">${escHtml(sil.observation || "")}</div>`;
    return general + table + reset;
  }

  _presenceNowHtml(st) {
    if (!st || !st.persons || !Object.keys(st.persons).length) return "";
    const t = this._t("presenceNow");
    const why = (row) => {
      const r = row.reason || {};
      if (r.kind === "simulated") return t.sim;
      if (r.kind === "home") return t.home.replace("{by}", (r.by || []).join(", ") || "–");
      if (r.kind === "away") return t.proofs[r.proof] || t.proofs.other;
      if (r.kind === "entity") return t.entity.replace("{s}", r.state ?? "–");
      if (r.kind === "no_proof") {
        // Was fehlt? (ADR 0018)
        const time = (ts) => (ts ? new Date(ts * 1000).toLocaleTimeString(this._lang, { hour: "2-digit", minute: "2-digit" }) : t.never);
        const parts = [t.noProof];
        if (r.located === false && !r.weak) parts.push(t.missNoFix);
        if (r.located) parts.push(t.missFix.replace("{w}", r.window ?? "–"));
        if (r.weak) parts.push(t.missWeak.replace("{door}", time(r.door_at)).replace("{left}", time(r.left_at)).replace("{w}", r.weak_window ?? "–"));
        return parts.join(" – ");
      }
      if (r.kind === "unclear") return t.unclear.replace("{by}", (r.by || []).join(", ") || "–");
      return "";
    };
    const persons = Object.values(st.persons)
      .map((row) => `<div>${escHtml(row.name)}: <b>${escHtml(t.states[row.state] || row.state)}</b> <span class="muted">(${escHtml(why(row))})</span></div>`)
      .join("");
    const now = Date.now() / 1000;
    const profiles = (st.profiles || [])
      .map((p) => `<div class="muted">${escHtml(p.name)} – ${escHtml(hauswachtProfileLine(p, t.line, now))}</div>`)
      .join("");
    const refresh = `<div class="tool"><button class="e" data-presence-refresh>${escHtml(t.refresh)}</button></div>`;
    return `<div class="report"><b>${escHtml(t.title)}</b>${persons}${profiles}<div class="muted">${escHtml(t.hint)}</div>${refresh}</div>`;
  }

  _colHead(label, text, table) {
    // Spaltenkopf mit ⓘ: Mauszeiger zeigt den Text (title), Antippen zeigt ihn unter der Tabelle
    const info = `<button type="button" class="info" data-col-info="${escHtml(table)}" data-text="${escHtml(text)}" title="${escHtml(text)}" aria-label="${escHtml(this._t("infoLabel"))}">ⓘ</button>`;
    return `<th title="${escHtml(text)}">${escHtml(label)} ${info}</th>`;
  }

  _measurementsHtml(m) {
    // Messungen der Heimkehr-Beobachtung: einsehen, speichern, zurücksetzen
    if (!m) return `<div class="muted">${escHtml(this._t("measOff"))}</div>`;
    const dash = (v, unit = "") => (v === null || v === undefined ? "–" : `${v}${unit}`);
    const since = `<div class="muted">${escHtml(this._fmt("measSince", { s: m.since || "–", d: m.days, w: m.departure_since || "–", x: m.departure_days, n: m.doors }))}</div>`;
    const rows = m.persons
      .map((p) => `<tr><td>${escHtml(p.name)}</td><td class="nw">${p.arrivals} (${p.arrivals_with_door})</td><td class="nw">${p.left}</td><td class="nw">${escHtml(dash(p.longest_left, " s"))}</td><td class="nw">${p.pauses}${p.longest_pause !== null ? ` (${p.longest_pause} min)` : ""}</td></tr>`)
      .join("");
    // Spaltenüberschriften mit ⓘ: Mauszeiger zeigt die Erklärung, Antippen klappt sie unter der Tabelle auf
    const head = (key) => this._colHead(this._t(key), this._t("measInfo")[key], "meas");
    const explain = ["measHome", "measLeft", "measLongest", "measPauses"]
      .map((key) => `<div><b>${escHtml(this._t(key))}:</b> ${escHtml(this._t("measInfo")[key])}</div>`)
      .join("");
    const persons = rows
      ? `<div class="scroll"><table><tr><th>${escHtml(this._t("measPerson"))}</th>${head("measHome")}${head("measLeft")}${head("measLongest")}${head("measPauses")}</tr>${rows}</table></div><div class="tip" data-col-tip="meas" hidden></div>
        <details class="explain"><summary>${escHtml(this._t("measExplain"))}</summary>${explain}</details>`
      : "";
    const advice = m.persons
      .map((p) => {
        const warn = p.status === "slow" || p.status === "pauses";
        return `<div class="${warn ? "" : "muted"}">${warn ? "⚠️ " : p.status === "ok" ? "✅ " : ""}${escHtml(p.advice)}</div>`;
      })
      .join("");
    // Vorbereitung Ausgangserkennung (0.63.1): Lebenszeichen rund um die Tür
    const exitPersons = m.persons.filter((p) => p.exit);
    const exitHead = (key) => this._colHead(this._t("exitCols")[key], this._t("exitInfo")[key], "exit");
    const exitRows = exitPersons
      .map((p) => {
        const e = p.exit;
        const confirm = e.confirm_median === null ? "–" : `${e.confirm_median} s / ${e.confirm_max} s`;
        const echo = e.left_echo ? `${e.left_echo} (${e.left_echo_max} s)` : "0";
        return `<tr><td>${escHtml(p.name)}</td><td class="nw">${e.left_with_sign} / ${e.left}</td><td class="nw">${escHtml(confirm)}</td><td class="nw">${e.unconfirmed} / ${e.stayed}</td><td class="nw">${escHtml(echo)}</td></tr>`;
      })
      .join("");
    const exitExplain = ["sign", "confirm", "missing", "echo"]
      .map((key) => `<div><b>${escHtml(this._t("exitCols")[key])}:</b> ${escHtml(this._t("exitInfo")[key])}</div>`)
      .join("");
    const exitText = exitPersons
      .flatMap((p) => p.exit_text || [])
      .map((line) => `<div class="muted">${escHtml(line)}</div>`)
      .join("");
    const exits = exitRows
      ? `<div class="n" style="margin-top:10px">${escHtml(this._t("exitTitle"))}</div><div class="muted">${escHtml(this._t("exitIntro"))}</div>
        <div class="scroll"><table><tr><th>${escHtml(this._t("measPerson"))}</th>${exitHead("sign")}${exitHead("confirm")}${exitHead("missing")}${exitHead("echo")}</tr>${exitRows}</table></div><div class="tip" data-col-tip="exit" hidden></div>
        <details class="explain"><summary>${escHtml(this._t("measExplain"))}</summary>${exitExplain}</details>${exitText}`
      : "";
    const entryRows = m.entries
      .map((e) => `<tr><td>${escHtml(e.door)}</td><td class="nw">${e.count}</td><td class="nw">${escHtml(dash(e.longest, " s"))}</td><td class="nw">${escHtml(dash(e.recommended, " s"))}</td></tr>`)
      .join("");
    const entries = entryRows
      ? `<div class="scroll" style="margin-top:8px"><table><tr><th>${escHtml(this._t("measEntryDoor"))}</th><th>${escHtml(this._t("measEntries"))}</th><th>${escHtml(this._t("measEntryLongest"))}</th><th>${escHtml(this._t("measEntryAdvice"))}</th></tr>${entryRows}</table></div>`
      : "";
    const tools = `<div class="tool">
      <button class="e" data-a="hc-show">${escHtml(this._t(this._report ? "measHide" : "measShow"))}</button>
      <button class="e" data-a="hc-md">⬇ ${escHtml(this._t("measSaveMd"))}</button>
      <button class="e" data-a="hc-csv">⬇ ${escHtml(this._t("measSaveCsv"))}</button>
      ${this._canEdit ? `<button class="e" data-a="reset-arrival">${escHtml(this._t("measResetArrival"))}</button><button class="e" data-a="reset-departure">${escHtml(this._t("measResetLeaving"))}</button><button class="e" data-a="reset-homecoming">${escHtml(this._t("measResetAll"))}</button>` : ""}
    </div>`;
    const report = this._report
      ? customElements.get("ha-markdown")
        ? `<div class="report"><ha-markdown breaks data-report></ha-markdown></div>`
        : `<pre class="report">${escHtml(this._report)}</pre>`
      : "";
    return `<div class="meas"><div class="n">${escHtml(this._t("measTitle"))}</div>${since}${persons}${advice}${exits}${entries}${tools}${report}</div>`;
  }

  async _toggleReport() {
    if (this._report) {
      this._report = null;
      this._render();
      return;
    }
    try {
      const r = await this._hass.callWS({ type: "hauswacht/homecoming/report" });
      this._report = r.markdown;
      this._render();
    } catch (err) {
      this._error = `${this._t("error")}: ${err?.message || err}`;
      this._render();
    }
  }

  async _resetMeasurement(what) {
    const ask = { arrival: "measAskArrival", departure: "measAskLeaving", homecoming: "measAskAll", silence: "measAskSilence" }[what];
    if (!window.confirm(this._t(ask))) return;
    try {
      await this._hass.callWS({ type: "hauswacht/measurements/reset", what });
      this._report = null;
      this._flash = this._t("measDone");
      await this._load();
    } catch (err) {
      this._error = `${this._t("error")}: ${err?.message || err}`;
      this._render();
    }
  }

  _systemTab(view) {
    const parts = view._parts();
    const sys = this._settings?.system;
    const status = this._card(parts.monitoring[0], parts.monitoring[2], "network");
    if (!sys) return status;
    const edit = (kind) => this._armedOr(`<div class="tool">${this._btn(`sys:${kind}`, this._t("edit"))}</div>`);
    const profileName = (id) => (sys.profiles.find((p) => p.id === id) || { name: id }).name;
    const restartText = [
      this._t("behaviors")[sys.restart.behavior],
      sys.restart.behavior === "armed" ? Object.values(sys.restart.profiles).map(profileName).join(", ") : null,
      sys.restart.behavior === "restore" && sys.restart.continue_alarm ? this._t("continueAlarm") : null,
    ].filter(Boolean).join(" · ");
    const name = (list, id) => (list.find((c) => c.id === id) || { name: id }).name;
    const h = sys.homecoming;
    const homeText = [
      h.observe ? this._t("observeOn") : this._t("observeOff"),
      h.persons.map((p) => name(h.person_choices, p)).join(", ") || null,
      h.ssids.length ? `${this._t("ssidsL")}: ${h.ssids.join(", ")}` : null,
    ].filter(Boolean).join(" · ");
    // Messungen (Heimkehr, Eingänge, Weggehen – ADR 0014) mit Bericht, Speichern, Zurücksetzen
    const leaving = this._measurementsHtml(h.measurements);
    const areas = sys.areas
      .map((a) => `<div class="item">${this._btn(`sys:area:${a.id}`, this._t("edit"))}<div class="n">${escHtml(a.name)}</div><div class="muted">${escHtml(a.profiles.join(", ") || "–")}</div></div>`)
      .join("");
    return (
      status +
      this._card(this._t("restart"), `<div>${escHtml(restartText)}</div>${edit("restart")}`, "restart") +
      this._card(this._t("silence"), this._silenceHtml(sys.silence) + edit("silence"), "silence") +
      this._card(this._t("network"), `<div>${escHtml(sys.network.entities.map((e) => name(sys.network.choices, e)).join(", ") || "–")}</div>${edit("network")}`, "network") +
      this._card(this._t("homecoming"), `<div>${escHtml(homeText)}</div>${this._presenceNowHtml(h.status)}${edit("homecoming")}${leaving}`, "homecoming") +
      this._card(this._t("areas"), areas + this._armedOr(`<div class="tool">${this._btn("sys:area:", "+ " + this._t("addArea"))}</div>`), "areas") +
      this._card(this._t("page"), `<div>${escHtml(this._t(sys.settings_page ? "pageOn" : "pageOff"))}</div>${edit("page")}`, "settingsPage") +
      // Konfiguration herunterladen (ADR 0019): nur lesen, mit Platzhaltern
      this._card(this._t("export"), `<div class="muted">${escHtml(this._t("exportText"))}</div><div class="tool"><button class="e" data-a="export">⬇ ${escHtml(this._t("exportBtn"))}</button></div>`, "export")
    );
  }

  // --- Reiter „Assistent“: Check-up (ADR 0017) --------------------------------------------
  // Dieselbe Prüfung wie in den Seitenblättern. Vorschläge werden einzeln übernommen, nach einer
  // Vorschau; abschwächende nur mit Häkchen. Hauswacht prüft beim Übernehmen alles noch einmal
  // (unscharf, Revision, Vorschlag noch aktuell, Bestätigung) – die Seite schaltet nichts.

  async _fetchAdvice() {
    try {
      return await this._hass.callWS({ type: "hauswacht/advisor/check", language: this._lang });
    } catch (_err) {
      return null;
    }
  }

  _asst(key) {
    return this._t("asst")[key];
  }

  _assistantTab() {
    const a = (k) => this._asst(k);
    const help = "assistant";
    if (!this._advice) return this._card(a("title"), `<div class="muted">${escHtml(a("unavailable"))}</div>`, help);
    const findings = this._advice.findings || [];
    const count = (level) => findings.filter((f) => f.level === level).length;
    const summary = findings.length
      ? `<div><b>${escHtml(a("count").replace("{e}", count("error")).replace("{w}", count("warning")).replace("{t}", count("tip")))}</b></div>`
      : `<div class="ok">✓ ${escHtml(a("allGood"))}</div>`;
    const intro = `<div class="muted">${escHtml(a("intro"))}</div>${summary}`;
    const armed = this._settings && !this._settings.editable ? `<div class="muted">${escHtml(this._t("armedNote"))}</div>` : "";
    const msg = armed + (this._asstError ? `<div class="asst-err">${escHtml(this._asstError)}</div>` : "");
    const tools = `<div class="tool"><button class="e" data-asst="recheck">${escHtml(a("recheck"))}</button></div>`;
    // Nach Profil gruppiert, allgemeine Befunde zuletzt
    const profiles = this._settings?.profiles || [];
    const groups = [...profiles.map((p) => [p.id, p.name]), [null, a("general")]];
    const blocks = groups
      .map(([pid, name]) => {
        const items = findings.map((f, i) => [f, i]).filter(([f]) => (f.profile || null) === pid);
        if (!items.length) return "";
        return `<h3>${escHtml(pid ? a("inProfile").replace("{p}", name) : name)}</h3>${items.map(([f, i]) => this._findingHtml(f, i)).join("")}`;
      })
      .join("");
    return this._goalsCard() + this._card(a("title"), intro + msg + blocks + tools, help) + this._scenariosCard();
  }

  _goalsCard() {
    const a = (k) => this._asst(k);
    const button = `<div class="tool">${this._btn("goals:", a("goalsOpen"))}</div>`;
    return this._card(a("goalsTitle"), `<div class="muted">${escHtml(a("goalsIntro"))}</div>${button}`, "goals");
  }

  // --- Szenario-Vorschau „Was passiert, wenn …?“ ------------------------------------------

  async _loadScenarios() {
    this._scLoading = true;
    try {
      const r = await this._hass.callWS({ type: "hauswacht/advisor/scenarios", language: this._lang });
      this._scenarios = r.scenarios || [];
    } catch (_err) {
      this._scenarios = null;
    }
    this._scLoading = false;
    if (this._tab === "assistant") this._render();
  }

  _scenariosCard() {
    const a = (k) => this._asst(k);
    const help = "scenarios";
    if (this._scenarios === undefined) {
      if (!this._scLoading) this._loadScenarios();
      return this._card(a("scTitle"), `<div class="muted">${escHtml(a("scLoading"))}</div>`, help);
    }
    if (this._scenarios === null) return this._card(a("scTitle"), `<div class="muted">${escHtml(a("unavailable"))}</div>`, help);
    const list = this._scenarios;
    const intro = `<div class="muted">${escHtml(a("scIntro"))}</div>`;
    if (!list.length) return this._card(a("scTitle"), intro + `<div>${escHtml(a("scNone"))}</div>`, help);
    const count = (r) => list.filter((x) => x.result === r).length;
    const summary = `<div><b>${escHtml(a("scCount").replace("{b}", count("bad")).replace("{w}", count("warn")).replace("{o}", count("ok")))}</b></div>`;
    const icon = { bad: "❌", warn: "⚠️", ok: "✅" };
    const level = { bad: "error", warn: "warning", ok: "ok" };
    const profiles = this._settings?.profiles || [];
    const blocks = profiles
      .map((p) => {
        const items = list.filter((x) => x.profile === p.id);
        if (!items.length) return "";
        const rows = items
          .map((x) => {
            const steps = x.steps.map((st) => `<div><span class="muted">${escHtml(this._clock(st.t))}</span> ${escHtml(st.text)}</div>`).join("");
            return `<div class="asst ${level[x.result]}"><div>${icon[x.result] || ""} <b>${escHtml(x.title)}</b></div><div>${escHtml(x.summary)}</div>
              <details class="explain"><summary>${escHtml(a("scSteps"))}</summary>${steps}</details></div>`;
          })
          .join("");
        return `<h3>${escHtml(a("inProfile").replace("{p}", p.name))}</h3>${rows}`;
      })
      .join("");
    const simple = `<div class="muted" style="margin-top:10px">${escHtml(a("scSimple"))}</div>`;
    return this._card(a("scTitle"), intro + summary + blocks + simple, help);
  }

  _clock(seconds) {
    // Ausgedachte Uhr: Minuten und Sekunden seit Beginn des Szenarios (h:mm:ss)
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const sec = seconds % 60;
    const pad = (n) => String(n).padStart(2, "0");
    return h ? `${h}:${pad(m)}:${pad(sec)}` : `${m}:${pad(sec)}`;
  }

  _findingHtml(f, i) {
    const a = (k) => this._asst(k);
    const icon = { error: "⛔", warning: "⚠️", tip: "💡" }[f.level] || "";
    const fixes = (f.fixes || [])
      .map((fix, j) => {
        const open = this._asstOpen === `${i}:${j}`;
        const button = `<button class="e" data-asst="open:${i}:${j}">${fix.weakens ? "⚠ " : ""}${escHtml(fix.label)}</button>`;
        if (this._settings && !this._settings.editable) return `<span class="muted">${escHtml(fix.label)}</span>`;
        return open ? this._fixPreview(fix, i, j) : button;
      })
      .join(" ");
    return `<div class="asst ${escHtml(f.level)}"><div>${icon} <b>${escHtml(a("levels")[f.level] || f.level)}:</b> ${escHtml(f.text)}</div>
      <details class="explain"><summary>${escHtml(a("why"))}</summary><div>${escHtml(f.why)}</div></details>
      ${fixes ? `<div class="fixes">${fixes}</div>` : ""}</div>`;
  }

  _fixPreview(fix, i, j) {
    const a = (k) => this._asst(k);
    const where = fix.profile
      ? a("inProfile").replace("{p}", (this._settings?.profiles || []).find((p) => p.id === fix.profile)?.name || fix.profile)
      : a("inSystem");
    const value = typeof fix.value === "string" && fix.value.includes(".") ? this._entityName(fix.value) : fix.value;
    const change =
      fix.op === "set"
        ? `${escHtml(a("before"))}: <b>${escHtml(fix.current ?? "–")}</b> → ${escHtml(a("after"))}: <b>${escHtml(value)}</b>`
        : `<b>${escHtml(value)}</b> ${escHtml(fix.op === "add" ? a("add") : a("remove"))}`;
    const warn = fix.weakens
      ? `<div class="asst-warn">${escHtml(a("weakens"))}</div><label class="chk"><input type="checkbox" data-asst-sure> ${escHtml(a("confirm"))}</label>`
      : "";
    return `<div class="preview"><div><b>${escHtml(a("preview"))}</b> (${escHtml(where)}): ${escHtml(fix.label)}</div><div>${change}</div>${warn}
      <div class="tool"><button class="e" data-asst="apply:${i}:${j}" ${fix.weakens ? "disabled" : ""}>${escHtml(a("apply"))}</button><button class="e" data-asst="close">${escHtml(a("cancel"))}</button></div></div>`;
  }

  _entityName(id) {
    const state = this._hass?.states?.[id];
    return state?.attributes?.friendly_name || id;
  }

  _wireAssistant() {
    const root = this.shadowRoot;
    // ⓘ in Spaltenköpfen: Erklärung unter der Tabelle zeigen, nochmal antippen blendet sie aus
    root.querySelectorAll("[data-col-info]").forEach((btn) =>
      btn.addEventListener("click", (ev) => {
        ev.stopPropagation();
        const tip = root.querySelector(`[data-col-tip="${CSS.escape(btn.dataset.colInfo)}"]`);
        if (!tip) return;
        const same = !tip.hidden && tip.textContent === btn.dataset.text;
        tip.textContent = btn.dataset.text;
        tip.hidden = same;
      })
    );
    // „Wer gilt gerade als zuhause?“ neu holen (nur lesen)
    root.querySelector("[data-presence-refresh]")?.addEventListener("click", async () => {
      try {
        const status = await this._hass.callWS({ type: "hauswacht/presence/status" });
        if (this._settings?.system?.homecoming) this._settings.system.homecoming.status = status;
      } catch (_err) {
        // nur Anzeige
      }
      this._render();
    });
    root.querySelectorAll("[data-asst]").forEach((el) =>
      el.addEventListener("click", () => {
        const [act, i, j] = el.dataset.asst.split(":");
        this._asstError = null;
        if (act === "recheck") this._recheckAdvice();
        else if (act === "open") {
          this._asstOpen = `${i}:${j}`;
          this._render();
        } else if (act === "close") {
          this._asstOpen = null;
          this._render();
        } else if (act === "apply") this._applyFix(Number(i), Number(j));
      })
    );
    const sure = root.querySelector("[data-asst-sure]");
    if (sure) {
      sure.addEventListener("change", () => {
        const button = root.querySelector('[data-asst^="apply:"]');
        if (button) button.disabled = !sure.checked;
      });
    }
  }

  async _recheckAdvice() {
    this._asstOpen = null;
    this._scenarios = undefined; // Vorschau neu durchspielen
    [this._advice, this._settings] = await Promise.all([
      this._fetchAdvice(),
      this._hass.callWS({ type: "hauswacht/settings/get" }).catch(() => this._settings),
    ]);
    this._render();
  }

  async _applyFix(i, j) {
    const finding = (this._advice?.findings || [])[i];
    const fix = finding?.fixes?.[j];
    if (!fix || !this._settings) return;
    const sure = this.shadowRoot.querySelector("[data-asst-sure]");
    let result;
    try {
      result = await this._hass.callWS({
        type: "hauswacht/advisor/apply",
        revision: this._settings.revision,
        fix,
        confirm: Boolean(fix.weakens && sure?.checked),
        language: this._lang,
      });
    } catch (_err) {
      result = { ok: false, errors: { base: "failed" } };
    }
    this._asstOpen = null;
    if (result.ok) {
      this._flash = this._asst("applied");
      this._reloadAfterSave(result.revision);
      return;
    }
    const code = result.errors?.base || "failed";
    this._asstError = this._asst("errors")[code] || `${this._asst("errors").failed} (${code})`;
    if (["changed_elsewhere", "fix_not_offered"].includes(code)) {
      await this._recheckAdvice();
      return;
    }
    this._render();
  }

  _docsTab() {
    const docs = window.HauswachtDocs;
    if (!docs) return `<ha-card><div class="wrap muted">${escHtml(this._t("reloadHint"))}</div></ha-card>`;
    const de = this._lang === "de";
    const list = docs.pages
      .map(([pde, pen, tde, ten, cde, cen]) => `<div class="item"><div class="n"><a class="lnk" href="${escHtml(docs.page(pde, pen, this._lang))}" target="_blank" rel="noreferrer">${escHtml(de ? tde : ten)} ↗</a></div><div class="muted">${escHtml(de ? cde : cen)}</div></div>`)
      .join("");
    const intro = `<div class="muted">${escHtml(this._fmt("docsIntro", { v: docs.version }))}</div>`;
    const all = `<div class="tool"><a class="lnk" href="${escHtml(docs.url("index", this._lang))}" target="_blank" rel="noreferrer">${escHtml(this._t("docsAll"))} ↗</a></div>`;
    return this._card(this._t("tabs").docs, intro + list + all);
  }

  _armedOr(html) {
    return this._settings && !this._settings.editable ? `<div class="muted">${escHtml(this._t("armedNote"))}</div>` : html;
  }

  _sirensTab(view) {
    const parts = view._parts();
    const tools = this._armedOr(`<div class="tool">${this._btn("sirens:", this._t("editSirens"))}</div>`);
    const sir = this._settings?.sirens;
    if (!sir) return this._card(parts.sirens[0], tools + parts.sirens[2], "sirens");
    const tones = sir.items.length
      ? sir.items
          .map((i) => `<div class="item">${this._btn(`tone:${i.id}`, this._t("edit"))}<div class="n">${escHtml(i.name)}</div><div class="muted">${escHtml(this._t("toneLabel"))}: ${escHtml(i.tone || this._t("toneAuto"))}${i.fire_ok ? ` · ${escHtml(this._t("fireReleased"))}` : ""}${i.smoke_detector ? ` · ${escHtml(this._t("smokeDetector"))}` : ""}</div></div>`)
          .join("")
      : `<div class="muted">${escHtml(this._t("noSirens"))}</div>`;
    const months = sir.test.reminder_months;
    const testText = `${months ? this._fmt("testEvery", { m: months }) : this._t("testOff")}${sir.test.prewarn ? ` · ${this._t("prewarnOn")}` : ""}`;
    return (
      this._card(parts.sirens[0], tools + parts.sirens[2], "sirens") +
      this._card(this._t("tonesTitle"), tones, "sirenTone") +
      this._card(this._t("testTitle"), `<div>${escHtml(testText)}</div><div class="muted">${escHtml(this._t("testCard"))}</div>${this._armedOr(`<div class="tool">${this._btn("sirentest:", this._t("edit"))}</div>`)}<div class="sirentest" id="sirentest"></div>`, "sirenTest") +
      this._card(this._t("switchTitle"), `<div class="muted">${escHtml(this._t("switchHint"))}</div>${this._armedOr(`<div class="tool">${this._btn("fromswitch:", "+ " + this._t("switchTitle"))}</div>`)}`, "sirenSwitch")
    );
  }

  _notificationsTab(view) {
    const parts = view._parts();
    const tools = this._armedOr(`<div class="tool">${this._btn("notify:", this._t("editNotify"))}</div>`);
    const events = this._settings?.notify?.events || [];
    const texts = events
      .map((e) => `<div class="item">${this._btn(`text:${e.event}`, this._t("edit"))}<div class="n">${escHtml(view._l("event", e.event))}</div><div class="muted">${escHtml(e.message || e.title ? `${this._t("ownText")}: ${e.title ? e.title + " – " : ""}${e.preview || e.message}` : this._t("defaultText"))}</div></div>`)
      .join("");
    const sp = this._settings?.notify?.speech;
    let speech = "";
    if (sp) {
      const speakerName = (id) => (sp.speaker_choices.find((c) => c.id === id) || { name: id }).name;
      const summary = [
        sp.speakers.length ? sp.speakers.map(speakerName).join(", ") : this._t("noSpeaker"),
        sp.quiet_enabled ? this._fmt("quietLine", { a: sp.quiet_start, b: sp.quiet_end }) : null,
      ].filter(Boolean).join(" · ");
      const events = sp.events
        .map((e) => `<div class="item">${this._btn(`speechevent:${e.event}`, this._t("edit"))}<div class="n">${e.enabled ? "🔊" : "🔇"} ${escHtml(view._l("event", e.event))}</div><div class="muted">${escHtml(e.text || e.default)}</div></div>`)
        .join("");
      speech = this._card(
        this._t("speechTitle"),
        `<div>${escHtml(summary)}</div>${this._armedOr(`<div class="tool">${this._btn("speech:", this._t("edit"))}</div>`)}${events}`,
        "speech"
      );
    }
    return (
      this._card(parts.notifications[0], tools + parts.notifications[2], "notifications") +
      (events.length ? this._card(this._t("texts"), `<div class="muted">${escHtml(this._t("textsHint"))}</div>${texts}`, "texts") : "") +
      speech
    );
  }

  _profilesTab(view) {
    const d = this._data;
    const tools = this._settings && !this._settings.editable
      ? `<div class="muted">${escHtml(this._t("armedNote"))}</div>`
      : `<div class="tool">${this._btn("profile:", "+ " + this._t("addProfile"))}</div>`;
    const cards = d.profiles
      .map((p) => {
        const head = `${escHtml(p.name)}${p.button ? ` <span class="muted">· ${escHtml(view._l("button", p.button))}</span>` : ""}`;
        return `<ha-card><div class="wrap"><div class="head"><div class="t">${head}</div>${this._btn(`profile:${p.id}`, this._t("edit"))}</div>${view._kv(view._profileRows(p))}</div></ha-card>`;
      })
      .join("");
    return this._card(this._t("tabs").profiles, tools, "profiles") + cards;
  }

  _closeEditor() {
    if (this._editor) this._editor.remove();
    this._editor = null;
  }

  _editAction(spec) {
    const [kind, id] = spec.split(":");
    const s = this._settings;
    if (kind === "group") this._openEditor("group", id ? s.groups.find((g) => g.id === id) : null);
    else if (kind === "tilt") this._openEditor("tilt", id ? s.tilt.find((x) => x.entity === id) : null);
    else if (kind === "strength") this._openEditor("strength", id ? s.strength.find((x) => x.entity === id) : null);
    else if (kind === "always") this._openEditor("always", null);
    else if (kind === "sensor") this._openEditor("sensor", { entity: spec.slice(7) });
    else if (kind === "profile") this._openProfileEditor(id);
    else if (kind === "rule") this._openRuleEditor(id);
    else if (kind === "person") this._openPersonEditor(id);
    else if (kind === "ctrl") this._openControlEditor("control", spec.slice(5));
    else if (kind === "card") this._openControlEditor("card", spec.slice(5));
    else if (kind === "cardnew") this._openControlEditor("cardnew");
    else if (kind === "ctrlnew") this._openControlEditor("control", null, { ctrlKind: "generic_keypad", presetName: spec.slice(8) });
    else if (kind === "sys") this._openSystemEditor(id, spec.split(":").slice(2).join(":"));
    else if (kind === "sirens") this._openAlarmEditor("sirens");
    else if (kind === "tone") this._openAlarmEditor("tone", spec.slice(5));
    else if (kind === "sirentest") this._openAlarmEditor("sirentest");
    else if (kind === "speech") this._openAlarmEditor("speech");
    else if (kind === "speechevent") this._openAlarmEditor("speechevent", spec.slice(12));
    else if (kind === "helper") this._openSystemEditor("helper");
    else if (kind === "fromswitch") this._openAlarmEditor("fromswitch");
    else if (kind === "notify") this._openAlarmEditor("notify");
    else if (kind === "text") this._openAlarmEditor("text", id);
    else if (kind === "goals") this._openGoals();
  }

  _openGoals() {
    // Einrichten nach Zielen (ADR 0017, 0.65)
    if (!customElements.get("hauswacht-goals-sheet")) return;
    const sheet = document.createElement("hauswacht-goals-sheet");
    sheet.addEventListener("hw-close", () => this._closeEditor());
    sheet.addEventListener("hw-saved", (ev) => {
      this._closeEditor();
      this._flash = this._t("saved");
      this._reloadAfterSave(ev.detail?.revision);
    });
    this._editor = sheet;
    this.shadowRoot.appendChild(sheet);
    sheet.open({ hass: this._hass });
  }

  get _canEdit() {
    return !!(this._settings && this._settings.editable && customElements.get("hauswacht-sensor-editor"));
  }

  _btn(spec, label) {
    return this._canEdit ? `<button class="e" data-edit="${escHtml(spec)}">${escHtml(label)}</button>` : "";
  }

  _view() {
    // Zeichen-Helfer der Übersichtskarte, ohne sie anzuzeigen
    const View = window.HauswachtOverviewView;
    if (!View || !this._data) return null;
    // Ohne Konstruktor: Die Klasse kann aus einem zweiten Laden der Karte stammen (z. B. nach
    // einem Update ohne Neuladen des Browsers) – dann wäre "new" ein Fehler.
    const view = Object.create(View.prototype);
    view._hass = this._hass;
    view._config = {};
    view._data = this._data;
    return view;
  }

  _fmt(key, values) {
    return Object.entries(values).reduce((text, [k, v]) => text.replace(`{${k}}`, v), this._t(key));
  }

  _sensorsTab(view) {
    const d = this._data;
    const groups = d.groups || [];
    const byGroup = new Map(groups.map((g) => [g.name, []]));
    const loose = [];
    for (const s of d.sensors) {
      if (s.zone && byGroup.has(s.zone)) byGroup.get(s.zone).push(s);
      else loose.push(s);
    }
    const cols = d.profiles.length + 4;
    const name = (s) =>
      this._canEdit && s.entity_id
        ? `<a class="lnk" data-edit="sensor:${escHtml(s.entity_id)}">${escHtml(s.name)}</a>`
        : escHtml(s.name);
    const overrides = this._settings?.system?.silence?.overrides || {};
    const staleMark = (s) => {
      if (!s.entity_id || !(s.entity_id in overrides)) return "";
      const h = overrides[s.entity_id];
      return ` <span class="muted" title="${escHtml(this._t("staleOwnTitle"))}">⏱ ${escHtml(h ? `${h} h` : this._t("staleNever"))}</span>`;
    };
    const row = (s) =>
      `<tr><td>${name(s)}${s.always_active ? ` <span class="muted">(${escHtml(view._t("always"))})</span>` : ""}${staleMark(s)}</td><td>${escHtml(view._l("type", s.type))}</td><td class="${s.state === "unavailable" ? "warn" : ""}">${escHtml(view._l("state", s.state))}</td><td class="nw">${s.battery != null ? `${s.battery} %` : ""}</td>${d.profiles.map((p) => `<td class="c">${view._sensorRole((s.profiles || {})[p.id])}</td>`).join("")}</tr>`;
    let body = "";
    for (const g of groups) {
      const members = byGroup.get(g.name) || [];
      const vibration = members.some((s) => s.type === "vibration") && g.vibration_count > 1
        ? ` · ${escHtml(this._fmt("vibrationRule", { n: g.vibration_count, s: g.vibration_window }))}`
        : "";
      body += `<tr class="grp"><td colspan="${cols}">${escHtml(g.name)} <span class="muted">${g.count} ${escHtml(this._t("sensorsCount"))}${vibration}</span>${this._btn(`group:${g.id}`, this._t("edit"))}</td></tr>`;
      body += members.map(row).join("");
    }
    if (loose.length) {
      body += `<tr class="grp"><td colspan="${cols}">${escHtml(this._t("noGroup"))}</td></tr>` + loose.map(row).join("");
    }
    if (!body) body = `<tr><td colspan="${cols}" class="muted">${escHtml(this._t("noMatch"))}</td></tr>`;
    const tools = this._settings && !this._settings.editable
      ? `<div class="muted">${escHtml(this._t("armedNote"))}</div>`
      : `<div class="tool">${this._btn("group:", "+ " + this._t("addGroup"))}</div>${this._canEdit ? `<div class="muted">${escHtml(this._t("clickHint"))}</div>` : ""}`;
    const matrix = `${tools}
      <div class="muted">${escHtml(view._t("legend"))}</div>
      <div class="scroll"><table>
        <tr><th>${escHtml(view._t("sensors"))}</th><th>${escHtml(view._t("type"))}</th><th>${escHtml(view._t("state"))}</th><th>🔋</th>${d.profiles.map((p) => `<th class="c">${escHtml(p.name)}</th>`).join("")}</tr>
        ${body}
      </table></div>`;
    const special = d.special || { tilt: [], vibration: [] };
    const where = (x) => `${escHtml(this._t("group"))}: ${escHtml(x.group || this._t("none"))}`;
    const tilt = special.tilt.map((x) =>
      `<div class="item">${this._btn(`tilt:${x.entity}`, this._t("edit"))}<div class="n">${escHtml(x.name)}${x.attribute ? ` <span class="muted">(${escHtml(x.attribute)})</span>` : ""}</div><div class="muted">${escHtml(this._fmt("tiltLine", { c: x.closed.join(", ") || "–", t: x.tilted.join(", ") || "–" }))} · ${where(x)}</div></div>`
    ).join("");
    const strength = special.vibration.map((x) =>
      `<div class="item">${this._btn(`strength:${x.entity}`, this._t("edit"))}<div class="n">${escHtml(x.name)}</div><div class="muted">${escHtml(this._fmt("strengthLine", { v: x.threshold }))} · ${where(x)}</div></div>`
    ).join("");
    const specialHtml = tilt || strength
      ? `${tilt ? `<h3>${escHtml(this._t("tilt"))}</h3>${tilt}` : ""}${strength ? `<h3>${escHtml(this._t("strength"))}</h3>${strength}` : ""}`
      : `<div class="muted">${escHtml(this._t("noSpecial"))}</div>`;
    const specialTools = `<div class="tool">${this._btn("tilt:", "+ " + this._t("addTilt"))}${this._btn("strength:", "+ " + this._t("addStrength"))}${this._btn("helper:", "+ " + this._t("addHelper"))}</div>`;
    const parts = view._parts();
    return (
      this._card(view._t("sensors"), matrix, "sensors") +
      this._card(this._t("special"), specialHtml + specialTools, "tilt") +
      this._card(parts.always[0], parts.always[2] + `<div class="tool">${this._btn("always:", this._t("edit"))}</div>`, "always")
    );
  }

  _card(title, body, help) {
    const link = help && window.HauswachtDocs ? window.HauswachtDocs.help(help, this._lang) : "";
    return `<ha-card><div class="wrap"><div class="head"><div class="t">${escHtml(title)}${link}</div></div>${body}</div></ha-card>`;
  }

  _tabBody() {
    try {
      return this._tabContent();
    } catch (err) {
      // Nie still hängen bleiben: Fehler sichtbar machen
      console.error("Hauswacht-Seite:", err);
      return `<ha-card><div class="wrap muted">${escHtml(this._t("reloadHint"))}<br>${escHtml(err?.message || err)}</div></ha-card>`;
    }
  }

  _tabContent() {
    if (this._error) return `<ha-card><div class="wrap muted">${escHtml(this._error)}</div></ha-card>`;
    if (this._data && !window.HauswachtOverviewView) {
      return `<ha-card><div class="wrap muted">${escHtml(this._t("reloadHint"))}</div></ha-card>`;
    }
    const view = this._view();
    if (!view) return `<div class="note">${escHtml(this._t("loading"))}</div>`;
    if (typeof view._parts !== "function") {
      return `<ha-card><div class="wrap muted">${escHtml(this._t("reloadHint"))}</div></ha-card>`;
    }
    if (this._tab === "sensors") return this._sensorsTab(view);
    if (this._tab === "profiles") return this._profilesTab(view);
    if (this._tab === "rules") return this._rulesTab(view);
    if (this._tab === "docs") return this._docsTab();
    if (this._tab === "assistant") return this._assistantTab();
    if (this._tab === "people") return this._peopleTab(view);
    if (this._tab === "system") return this._systemTab(view);
    if (this._tab === "sirens") return this._sirensTab(view);
    if (this._tab === "notifications") return this._notificationsTab(view);
    const parts = view._parts();
    const items = TAB_PARTS[this._tab] || [];
    const asOf = this._tab === "overview"
      ? `${parts.asOf}<div class="tool"><button class="e" data-a="print">🖨 ${escHtml(view._t("print"))}</button><button class="e" data-a="sheet">📄 ${escHtml(view._t("sheet"))}</button></div>`
      : "";
    return asOf + items.map((key) => this._card(parts[key][0], parts[key][2], PART_HELP[key])).join("");
  }

  _render() {
    if (!this.shadowRoot) return;
    const shared = window.HauswachtOverviewStyle || "";
    const menu = this._narrow
      ? `<button data-a="menu" title="Menu"><ha-icon icon="mdi:menu"></ha-icon></button>`
      : "";
    this.shadowRoot.innerHTML = `
      <style>${shared}${PANEL_STYLE}${window.HauswachtDocs?.style || ""}</style>
      <div class="top">
        ${menu}
        <div class="t"><ha-icon icon="mdi:shield-home"></ha-icon>${escHtml(this._t("title"))}</div>
        <button data-a="refresh" title="${escHtml(this._t("refresh"))}"><ha-icon icon="mdi:refresh"></ha-icon></button>
      </div>
      <div class="tabs">${TABS.map((tab) => `<button data-tab="${tab}" class="${tab === this._tab ? "on" : ""}">${escHtml(this._t("tabs")[tab])}</button>`).join("")}</div>
      <div class="content">
        <div class="note">${escHtml(this._t("hint"))}</div>
        ${this._flash ? `<div class="ok">✓ ${escHtml(this._flash)}</div>` : ""}
        ${this._tabBody()}
      </div>`;
    this.shadowRoot.querySelectorAll("[data-tab]").forEach((button) =>
      button.addEventListener("click", () => {
        this._tab = button.dataset.tab;
        try {
          localStorage.setItem(STORE_KEY, this._tab);
        } catch (_err) {
          // nur Bequemlichkeit
        }
        this._render();
      })
    );
    this._renderSirenTest();
    this._wireAssistant();
    // Heimkehr-Bericht in der Einstellungsseite anzeigen (Markdown von Home Assistant)
    const report = this.shadowRoot.querySelector("ha-markdown[data-report]");
    if (report) report.content = this._report || "";
    this.shadowRoot.querySelectorAll("[data-a]").forEach((button) =>
      button.addEventListener("click", () => {
        const action = button.dataset.a;
        if (action === "refresh") this._load();
        else if (action === "menu") this.dispatchEvent(new Event("hass-toggle-menu", { bubbles: true, composed: true }));
        else if (action === "print" || action === "sheet") this._print(action);
        else if (action === "hc-md" || action === "hc-csv") this._downloadHomecoming(action === "hc-csv" ? "csv" : "markdown");
        else if (action === "hc-show") this._toggleReport();
        else if (action === "export") this._downloadExport();
        else if (action.startsWith("reset-")) this._resetMeasurement(action.slice(6));
      })
    );
    this.shadowRoot.querySelectorAll("[data-edit]").forEach((button) =>
      button.addEventListener("click", () => {
        this._flash = null;
        this._editAction(button.dataset.edit);
      })
    );
    if (this._editor) this.shadowRoot.appendChild(this._editor);
  }

  _print(kind) {
    // Drucken wie in der Karte „Hauswacht Übersicht“: ganze Anlage oder Notfallblatt
    const view = this._view();
    if (!view) return;
    view._print(kind === "sheet" ? view._sheetHtml() : view._printHtml());
  }

  async _downloadExport() {
    // Konfiguration herunterladen (ADR 0019) – Hauswacht ersetzt Namen und Geheimnisse vorher
    try {
      const r = await this._hass.callWS({ type: "hauswacht/export", language: this._lang });
      this._saveFile(`${r.filename}.json`, JSON.stringify(r.data, null, 2), "application/json;charset=utf-8");
    } catch (err) {
      this._flash = null;
      this._error = `${this._t("error")}: ${err?.message || err}`;
      this._render();
    }
  }

  _saveFile(name, content, type) {
    const url = URL.createObjectURL(new Blob([content], { type }));
    const link = document.createElement("a");
    link.href = url;
    link.download = name;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  async _downloadHomecoming(kind) {
    // Heimkehr-Bericht (Markdown) oder Tabelle (CSV) herunterladen – wie in der Übersichtskarte
    try {
      const r = await this._hass.callWS({ type: "hauswacht/homecoming/report" });
      const csv = kind === "csv";
      const blob = new Blob([csv ? r.csv : r.markdown], { type: csv ? "text/csv;charset=utf-8" : "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${r.filename}.${csv ? "csv" : "md"}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (err) {
      this._flash = null;
      this._error = `${this._t("error")}: ${err?.message || err}`;
      this._render();
    }
  }
}

if (!customElements.get("hauswacht-panel")) {
  customElements.define("hauswacht-panel", HauswachtPanel);
}
