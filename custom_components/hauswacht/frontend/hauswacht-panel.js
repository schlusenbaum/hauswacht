// Hauswacht – Einstellungsseite in der Seitenleiste (ADR 0011), Stufe 1: alles auf einen Blick.
//
// Nur stabile Bausteine: eigene Web-Component, ha-card, ha-icon und die Farben des Themas.
// Die Abschnitte kommen aus der Karte "Hauswacht Übersicht" (dieselben Texte und Daten über
// den Websocket-Befehl hauswacht/overview, nur für Administratoren). Bearbeitet wird in dieser
// Stufe noch im Einstellungsdialog. Bearbeiten (ab Stufe 2) über eigene Seitenblätter:
// hauswacht-panel-edit.js (Melder), -profile.js (Profile), -rules.js (Auslöseregeln),
// -alarm.js (Alarmgeber, Benachrichtigungen).

const TEXTS = {
  de: {
    title: "Hauswacht",
    loading: "Lade …",
    refresh: "Neu laden",
    dialog: "Im Dialog bearbeiten",
    hint: "Die ganze Einrichtung auf einen Blick – und alles direkt hier bearbeiten. Der Einstellungsdialog („Im Dialog bearbeiten“) bleibt als zweiter Weg. Auch der Sirenentest geht hier (Reiter Alarmgeber) – mit Rückfrage, nur für Administratoren.",
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
    pageOn: "in der Seitenleiste sichtbar",
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
    adminOnly: "Diese Seite ist nur für Administratoren.",
    error: "Fehler",
    tabs: {
      overview: "Übersicht",
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
    dialog: "Edit in the dialog",
    hint: "The whole setup at a glance – and edit everything right here. The settings dialog (“Edit in the dialog”) stays as a second way. The siren test also works here (tab Alarm devices) – with confirmation, administrators only.",
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
    pageOn: "visible in the sidebar",
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
    adminOnly: "This page is for administrators only.",
    error: "Error",
    tabs: {
      overview: "Overview",
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

const TABS = ["overview", "sensors", "profiles", "rules", "sirens", "notifications", "people", "system", "docs"];
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
  h3 { margin: 12px 0 4px; font-size: 1rem; font-weight: 500; }
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
    } catch (_err) {
      // ohne Bearbeiten weiter nutzbar
    }
    this._ready = true;
    await this._load();
  }

  async _load() {
    this._error = null;
    try {
      [this._data, this._settings] = await Promise.all([
        this._hass.callWS({ type: "hauswacht/overview" }),
        this._hass.callWS({ type: "hauswacht/settings/get" }).catch(() => null),
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

  _measurementsHtml(m) {
    // Messungen der Heimkehr-Beobachtung: einsehen, speichern, zurücksetzen
    if (!m) return `<div class="muted">${escHtml(this._t("measOff"))}</div>`;
    const dash = (v, unit = "") => (v === null || v === undefined ? "–" : `${v}${unit}`);
    const since = `<div class="muted">${escHtml(this._fmt("measSince", { s: m.since || "–", d: m.days, w: m.departure_since || "–", x: m.departure_days, n: m.doors }))}</div>`;
    const rows = m.persons
      .map((p) => `<tr><td>${escHtml(p.name)}</td><td class="nw">${p.arrivals} (${p.arrivals_with_door})</td><td class="nw">${p.left}</td><td class="nw">${escHtml(dash(p.longest_left, " s"))}</td><td class="nw">${p.pauses}${p.longest_pause !== null ? ` (${p.longest_pause} min)` : ""}</td></tr>`)
      .join("");
    const persons = rows
      ? `<div class="scroll"><table><tr><th>${escHtml(this._t("measPerson"))}</th><th>${escHtml(this._t("measHome"))}</th><th>${escHtml(this._t("measLeft"))}</th><th>${escHtml(this._t("measLongest"))}</th><th>${escHtml(this._t("measPauses"))}</th></tr>${rows}</table></div>`
      : "";
    const advice = m.persons
      .map((p) => {
        const warn = p.status === "slow" || p.status === "pauses";
        return `<div class="${warn ? "" : "muted"}">${warn ? "⚠️ " : p.status === "ok" ? "✅ " : ""}${escHtml(p.advice)}</div>`;
      })
      .join("");
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
    return `<div class="meas"><div class="n">${escHtml(this._t("measTitle"))}</div>${since}${persons}${advice}${entries}${tools}${report}</div>`;
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
      this._card(this._t("homecoming"), `<div>${escHtml(homeText)}</div>${edit("homecoming")}${leaving}`, "homecoming") +
      this._card(this._t("areas"), areas + this._armedOr(`<div class="tool">${this._btn("sys:area:", "+ " + this._t("addArea"))}</div>`), "areas") +
      this._card(this._t("page"), `<div>${escHtml(this._t("pageOn"))}</div>${edit("page")}`, "settingsPage")
    );
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
        <button class="lnk" data-a="dialog">${escHtml(this._t("dialog"))}</button>
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
    // Heimkehr-Bericht in der Einstellungsseite anzeigen (Markdown von Home Assistant)
    const report = this.shadowRoot.querySelector("ha-markdown[data-report]");
    if (report) report.content = this._report || "";
    this.shadowRoot.querySelectorAll("[data-a]").forEach((button) =>
      button.addEventListener("click", () => {
        const action = button.dataset.a;
        if (action === "refresh") this._load();
        else if (action === "menu") this.dispatchEvent(new Event("hass-toggle-menu", { bubbles: true, composed: true }));
        else if (action === "dialog") this._navigate("/config/integrations/integration/hauswacht");
        else if (action === "print" || action === "sheet") this._print(action);
        else if (action === "hc-md" || action === "hc-csv") this._downloadHomecoming(action === "hc-csv" ? "csv" : "markdown");
        else if (action === "hc-show") this._toggleReport();
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

  _navigate(path) {
    history.pushState(null, "", path);
    window.dispatchEvent(new CustomEvent("location-changed", { detail: { replace: false } }));
  }
}

if (!customElements.get("hauswacht-panel")) {
  customElements.define("hauswacht-panel", HauswachtPanel);
}
