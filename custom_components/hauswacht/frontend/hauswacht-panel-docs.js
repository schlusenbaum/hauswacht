// Hauswacht – Einstellungsseite: Verweise in die Dokumentation (Reiter „Dokumentation“ und „?“
// an jedem Abschnitt). Die Links zeigen auf die Anleitung genau der installierten Version
// (Tag vX.Y.Z auf GitHub), deutsch oder englisch nach der Sprache von Home Assistant.
//
// tests/core/test_panel_docs.py prüft, dass jede Seite und jeder Anker hier wirklich existiert.

const DOC_REPO = "https://github.com/schlusenbaum/hauswacht/blob";

// Schlüssel -> [deutsche Seite#Anker, englische Seite#Anker]
const DOC_LINKS = {
  index: ["README.md", "README.md"],
  settingsPage: ["einstellungsseite.md", "settings-page.md"],
  matrix: ["einstellungsseite.md#die-matrix-melder--profile", "settings-page.md#the-matrix-sensor--profile"],
  sensors: ["melder.md", "sensors.md"],
  groups: ["melder.md#meldergruppen", "sensors.md#sensor-groups"],
  types: ["melder.md#typen", "sensors.md#types"],
  tilt: ["melder.md#melder-mit-kippstellung-gekippt", "sensors.md#sensors-with-tilt-position-tilted"],
  vibration: ["melder.md#erschütterungsmelder", "sensors.md#vibration-sensors"],
  strength: ["melder.md#erschütterungsstärke-als-zahl", "sensors.md#vibration-strength-as-a-number"],
  always: ["melder.md#immer-aktive-melder", "sensors.md#always-active-sensors"],
  silence: ["melder.md#funkstille-von-sensoren", "sensors.md#sensor-radio-silence"],
  network: ["melder.md#funknetz-und-gateways-überwachen", "sensors.md#monitor-radio-networks-and-gateways"],
  profiles: ["profile.md#alarmprofile", "profiles.md#alarm-profiles"],
  automation: ["profile.md#automatik", "profiles.md#automation"],
  areas: ["profile.md#bereiche", "profiles.md#areas"],
  rules: ["ausloeseregeln.md", "trigger-rules.md"],
  rulesYaml: ["ausloeseregeln.md#expertenmodus-yaml", "trigger-rules.md#expert-mode-yaml"],
  sirens: ["sirenen.md", "sirens.md"],
  sirenRelease: ["sirenen.md#einrichten", "sirens.md#setting-up"],
  sirenTone: ["sirenen.md#ton-je-sirene", "sirens.md#tone-per-siren"],
  sirenTest: ["sirenen.md#sirenentest", "sirens.md#siren-test"],
  sirenSwitch: ["sirenen.md#sirene-aus-schalter-erstellen", "sirens.md#create-siren-from-switch"],
  card: ["bedienteile.md#karte-bearbeiten-deaktivieren-löschen", "control-devices.md#edit-disable-delete-a-card"],
  cardNew: ["bedienteile.md#neue-karte-anlernen", "control-devices.md#learn-a-new-card"],
  keypad: ["bedienteile.md#keypad-zigbee2mqtt", "control-devices.md#keypad-zigbee2mqtt"],
  generic_keypad: ["bedienteile.md#keypad-allgemein", "control-devices.md#keypad-generic"],
  mqtt_keypad: ["bedienteile.md#mqtt-schnittstelle", "control-devices.md#mqtt-interface"],
  sticker: ["bedienteile.md#nfc-aufkleber-companion-app", "control-devices.md#nfc-sticker-companion-app"],
  reader: ["bedienteile.md#rfid-leser", "control-devices.md#rfid-reader"],
  button: ["bedienteile.md#taster", "control-devices.md#button"],
  lock: ["bedienteile.md#türschloss-z-b-nuki", "control-devices.md#door-lock-eg-nuki"],
  notifications: ["benachrichtigungen.md", "notifications.md"],
  texts: ["benachrichtigungen.md#eigene-texte-und-platzhalter", "notifications.md#custom-texts-and-placeholders"],
  speech: ["benachrichtigungen.md#sprachausgabe-lautsprecher", "notifications.md#speech-speakers"],
  helper: ["melder.md#melder-aus-anderem-sensor-erstellen", "sensors.md#create-a-sensor-from-another-sensor"],
  reminder: ["benachrichtigungen.md#erinnerung-alle-weg-anlage-unscharf", "notifications.md#reminder-everyone-away-system-disarmed"],
  users: ["benutzer.md#benutzer", "users.md#users"],
  pins: ["benutzer.md#pins", "users.md#pins"],
  pinRules: ["benutzer.md#pin-regeln", "users.md#pin-rules"],
  rights: ["benutzer.md#rechte", "users.md#rights"],
  duress: ["benutzer.md#bedrohungs-pin", "users.md#duress-pin"],
  controls: ["bedienteile.md", "control-devices.md"],
  actionCodes: ["bedienteile.md#aktions-codes", "control-devices.md#action-codes"],
  cards: ["bedienteile.md#karten-anlernen", "control-devices.md#learning-cards"],
  observations: ["beobachtung.md", "observations.md"],
  passage: ["durchgang.md", "passage.md"],
  homecoming: ["beobachtung.md#heimkehr-beobachtung", "observations.md#homecoming-observation"],
  status: ["dashboard.md#scharf-und-unscharf-schalten", "dashboard.md#arming-and-disarming"],
  findings: ["uebersicht.md#prüfhinweise", "overview.md#check-hints"],
  assistant: ["assistent.md#check-up-im-reiter-assistent-seit-0640b3", "setup-wizard.md#check-up-in-the-assistant-tab-since-0640b3"],
  testMode: ["testmodus.md", "test-mode.md"],
  troubleshooting: ["fehlersuche.md", "troubleshooting.md"],
  restart: ["installation.md#verhalten-nach-einem-neustart", "installation.md#behaviour-after-a-restart"],
};

// Reiter „Dokumentation“: [Schlüssel/Seite de, Seite en, Titel de, Titel en, Inhalt de, Inhalt en]
const DOC_PAGES = [
  ["so-entscheidet-hauswacht.md", "how-hauswacht-decides.md", "So entscheidet Hauswacht", "How Hauswacht decides",
    "Überblick: Tür auf, Automatik, Heimkommen, zuhause oder weg – als Bilder",
    "Overview: door opens, automation, coming home, home or away – as pictures"],
  ["installation.md", "installation.md", "Installation und erste Schritte", "Installation and first steps",
    "Installation, die Einstellungsseite, der kürzeste Weg zur ersten Scharfschaltung, Updates",
    "Installation, the settings page, the shortest way to the first arming, updates"],
  ["assistent.md", "setup-wizard.md", "Einrichtungsassistent", "Setup wizard",
    "Früherer Assistent entfallen – so richtest du jetzt ein", "Former wizard removed – how to set up now"],
  ["einstellungsseite.md", "settings-page.md", "Einstellungsseite", "Settings page",
    "Diese Seite: Reiter, Matrix, alles bearbeiten", "This page: tabs, matrix, editing everything"],
  ["melder.md", "sensors.md", "Melder und Meldergruppen", "Sensors and sensor groups",
    "Welche Sensoren gehen, Gruppen, Typen, Kippstellung, Erschütterung, immer aktiv, Funkstille",
    "Which sensors work, groups, types, tilt, vibration, always active, radio silence"],
  ["profile.md", "profiles.md", "Alarmprofile und Bereiche", "Alarm profiles and areas",
    "Verzögerungen, Reaktion, Automatik, Scharf durch Schließen der Tür, mehrere Bereiche",
    "Delays, reaction, automation, arm by closing the door, several areas"],
  ["ausloeseregeln.md", "trigger-rules.md", "Auslöseregeln", "Trigger rules",
    "Abfolgen wie „Tür, dann Keller“, Ausnahmen, Bedingungen, YAML",
    "Sequences like “door, then basement”, exceptions, conditions, YAML"],
  ["dashboard.md", "dashboard.md", "Bedienung und Dashboard", "Operation and dashboard",
    "Scharf und unscharf schalten, Alarm beenden, Karten", "Arming and disarming, ending an alarm, cards"],
  ["benutzer.md", "users.md", "Benutzer, PINs und Sperre", "Users, PINs and lockout",
    "Benutzer, Rechte je Bereich, PIN-Regeln, Sperre, Bedrohungs-PIN",
    "Users, rights per area, PIN rules, lockout, duress PIN"],
  ["durchgang.md", "passage.md", "Durchgang", "Passage",
    "Rein oder raus, ohne unscharf zu schalten", "In or out without disarming"],
  ["bedienteile.md", "control-devices.md", "Bedienteile", "Control devices",
    "Keypads, Karten, NFC-Aufkleber, RFID-Leser, Taster, Türschlösser",
    "Keypads, cards, NFC stickers, RFID readers, buttons, door locks"],
  ["sirenen.md", "sirens.md", "Sirenen", "Sirens",
    "Freigabe, Ton je Sirene, Sirenentest, Brandschutz", "Release, tone per siren, siren test, fire protection"],
  ["benachrichtigungen.md", "notifications.md", "Benachrichtigungen und Sprachausgabe", "Notifications and speech",
    "Empfänger je Ereignis, eigene Texte, Ansagen, Push-Knöpfe",
    "Recipients per event, custom texts, announcements, push buttons"],
  ["testmodus.md", "test-mode.md", "Testmodus und Testkarte", "Test mode and test card",
    "Alles gefahrlos durchspielen, ohne Sirene", "Play everything through safely, without siren"],
  ["beobachtung.md", "observations.md", "Beobachtungen", "Observations",
    "Heimkehr-Beobachtung und „Tür auf bis unscharf“", "Homecoming observation and “door open to disarmed”"],
  ["uebersicht.md", "overview.md", "Anlagenübersicht", "System overview",
    "Drucken, Notfallblatt, Prüfhinweise, Diagnose-Datei", "Printing, emergency sheet, check hints, diagnostics"],
  ["automationen.md", "automations.md", "Automationen", "Automations",
    "Für jeden Anlass der richtige Auslöser", "The right trigger for every occasion"],
  ["beispiele.md", "examples.md", "Beispiele", "Examples",
    "Licht bei Alarm, Kamerabild aufs Handy, Rollläden, Gastmodus …",
    "Light on alarm, camera image to the phone, shutters, guest mode …"],
  ["referenz.md", "reference.md", "Referenz", "Reference",
    "Alle Entitäten, Attribute, Ereignisse und Aktionen", "All entities, attributes, events and actions"],
  ["fehlersuche.md", "troubleshooting.md", "Fehlersuche", "Troubleshooting",
    "Häufige Fragen und Probleme", "Common questions and problems"],
];

function docRef(version) {
  // Vorabversionen und Releases haben ein Tag "v<Version>"; ohne Version: Hauptzweig
  return version && version !== "0" ? `v${version}` : "main";
}

function docUrl(path, lang, version) {
  const base = `${DOC_REPO}/${docRef(version)}/docs/`;
  return lang === "de" ? base + path : `${base}en/${path}`;
}

window.HauswachtDocs = window.HauswachtDocs || {
  version: "0",
  pages: DOC_PAGES,
  // url("tilt", "de") -> Link zur passenden Stelle der Anleitung
  url(key, lang) {
    const entry = DOC_LINKS[key];
    if (!entry) return "";
    return docUrl(lang === "de" ? entry[0] : entry[1], lang, this.version);
  },
  page(dePath, enPath, lang) {
    return docUrl(lang === "de" ? dePath : enPath, lang, this.version);
  },
  // Datei im Repo in genau der installierten Version (z. B. ein Blueprint)
  file(path) {
    return `${DOC_REPO}/${docRef(this.version)}/${path}`;
  },
  // "Blueprint importieren" über my.home-assistant.io – mit der installierten Version, damit
  // auch Vorabversionen ihren Blueprint finden
  blueprintImport(name) {
    const url = this.file(`blueprints/automation/hauswacht/${name}`);
    return `https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=${encodeURIComponent(url)}`;
  },
  // Kleines „?“ mit Link, für Kopfzeilen von Karten und Seitenblättern
  help(key, lang, title) {
    const url = this.url(key, lang);
    if (!url) return "";
    const label = title || (lang === "de" ? "Anleitung" : "Documentation");
    return `<a class="hw-help" href="${url}" target="_blank" rel="noreferrer" title="${label}" aria-label="${label}">?</a>`;
  },
  // „?“ an die Überschrift eines Seitenblatts hängen (nach jedem Zeichnen aufrufen)
  decorate(root, key, lang) {
    const heading = root && key ? root.querySelector("h2") : null;
    if (!heading || heading.querySelector("a.hw-help")) return;
    heading.insertAdjacentHTML("beforeend", this.help(key, lang));
    const style = document.createElement("style");
    style.textContent = this.style;
    root.appendChild(style);
  },
  // ⓘ an Beschriftungen hängen (0.62): entries = [[Beschriftung, Erklärung], …]. Gesucht wird in
  // <label> und in Ankreuzfeldern (.chk span) nach genau diesem Text. Mauszeiger zeigt die
  // Erklärung (title), Antippen klappt sie auf. Nach jedem Zeichnen aufrufen.
  explain(root, entries, lang) {
    if (!root || !entries?.length) return;
    const esc = (v) => String(v).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
    const label = lang === "de" ? "Erklärung" : "Explanation";
    const wanted = new Map(entries.filter(([l, t]) => l && t).map(([l, t]) => [String(l).trim(), t]));
    root.querySelectorAll("label, .chk > span, h3").forEach((el) => {
      if (el.querySelector(".hw-info")) return;
      const text = wanted.get(el.textContent.trim());
      if (!text) return;
      el.insertAdjacentHTML(
        "beforeend",
        ` <button type="button" class="hw-info" title="${esc(text)}" aria-label="${label}">ⓘ</button><span class="hw-tip" hidden>${esc(text)}</span>`
      );
      const button = el.querySelector(".hw-info");
      button.addEventListener("click", (ev) => {
        ev.preventDefault();
        ev.stopPropagation();
        const tip = el.querySelector(".hw-tip");
        tip.hidden = !tip.hidden;
      });
    });
    if (!root.querySelector("style[data-hw-info]")) {
      const style = document.createElement("style");
      style.dataset.hwInfo = "1";
      style.textContent = `
        .hw-info { border: none; background: none; color: var(--primary-color); cursor: help; font-size: 1rem; padding: 0 2px; }
        .hw-tip[hidden] { display: none; }
        .hw-tip { display: block; font-weight: normal; font-size: .85rem; margin: 4px 0 6px; padding: 8px 10px;
          border-radius: 6px; background: var(--secondary-background-color); color: var(--primary-text-color); }`;
      root.appendChild(style);
    }
  },
  style: `
    a.hw-help { display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; flex: none;
      border-radius: 50%; border: 1px solid var(--divider-color); color: var(--primary-color); font-size: .85rem;
      font-weight: 500; text-decoration: none; margin-left: 8px; vertical-align: middle; }
    a.hw-help:hover { background: var(--secondary-background-color); }`,
};
