/*
 * Hauswacht Übersicht – die aktuelle Konfiguration der Anlage auf einen Blick.
 *
 * Bildschirm: Kurzfassung mit aufklappbaren Abschnitten, Prüfhinweise oben.
 * Drucken: das volle Programm als A4-Seite; dazu ein Notfallblatt für die Familie.
 *
 * Nur für Administratoren (die Daten kommen über den WebSocket-Befehl hauswacht/overview).
 * Wird von der Integration automatisch geladen.
 *
 *   type: custom:hauswacht-uebersicht-card
 *   title: Übersicht   # optional
 */

const LANG = {
  de: {
    title: "Übersicht",
    refresh: "Aktualisieren",
    print: "Drucken",
    sheet: "Notfallblatt",
    asOf: "Stand",
    loading: "Lade Übersicht …",
    adminOnly: "Die Übersicht ist nur für Administratoren.",
    error: "Übersicht nicht verfügbar",
    findings: "Prüfhinweise",
    noFindings: "Keine Auffälligkeiten.",
    where: "Ändern",
    status: "Zustand",
    profiles: "Alarmprofile",
    sensors: "Melder",
    rules: "Auslöseregeln",
    always: "Immer aktiv",
    sirens: "Sirenen",
    users: "Benutzer",
    controls: "Bedienteile",
    notifications: "Benachrichtigungen",
    monitoring: "Überwachung",
    pinRules: "PIN-Regeln",
    yes: "ja",
    no: "nein",
    none: "–",
    testMode: "Testmodus",
    sirensEnabled: "Sirenen freigegeben",
    systemStatus: "Systemstatus",
    failures: "Falsche Eingaben",
    lockedUntil: "gesperrt bis",
    area: "Bereich",
    button: "Knopf",
    zones: "Meldergruppen",
    excluded: "Ausgenommen",
    exitDelay: "Ausgangsverzögerung",
    entryDelay: "Eingangsverzögerung",
    reaction: "Alarmreaktion",
    cycles: "Alarmzyklen",
    openPolicy: "Offene Melder",
    unavailablePolicy: "Ausgefallene Melder",
    tamper: "Manipulation löst Alarm aus",
    silent: "Stiller Alarm",
    tone: "Ton",
    volume: "Lautstärke",
    recipients: "Empfänger bei Alarm",
    auto: "Automatik",
    armAt: "scharf um",
    disarmAt: "unscharf um",
    weekdays: "Tage",
    daily: "täglich",
    awayPersons: "scharf, wenn weg",
    after: "nach",
    disarmOnArrival: "unscharf bei Heimkehr",
    armOnClose: "Scharf durch Schließen",
    sensorsArmed: "Melder einzeln scharf",
    group: "Gruppe",
    type: "Typ",
    state: "Zustand",
    lastContact: "Letzter Kontakt",
    battery: "Batterie",
    usedIn: "Verwendet in",
    notUsed: "in keinem Profil",
    tested: "Letzter Test",
    heard: "gehört",
    notHeard: "nicht gehört",
    never: "nie",
    capabilities: "Kann",
    pin: "PIN",
    cards: "Karten",
    rights: "Rechte",
    validity: "Gültig",
    haAccount: "HA-Konto",
    inactive: "inaktiv",
    expired: "abgelaufen",
    masterPin: "Master-PIN",
    anyPin: "PIN verlangt (Bedienfeld)",
    armCode: "PIN auch zum Scharfschalten",
    buttonsNoPin: "Dashboard-Knöpfe trotz PIN",
    topic: "MQTT-Topic",
    login: "Anmeldung",
    emergency: "Notruf-Taste",
    action: "Aktion",
    general: "Allgemeine Empfänger",
    event: "Ereignis",
    speech: "Ansage",
    speakers: "Lautsprecher",
    quiet: "Nachtruhe",
    staleAfter: "Funkstille-Grenze",
    recommended: "Empfehlung",
    observed: "beobachtet",
    days: "Tage",
    off: "aus",
    gateways: "Funknetz und Gateways",
    learn: "Anlernzeit für Karten",
    turnOff: "ausschalten",
    duration: "Dauer",
    printNote:
      "Enthält Sicherheitsinformationen (z. B. was wann nicht überwacht wird) – nicht offen liegen lassen.",
    legend: "✓ einzeln scharf · R nur in Auslöseregeln · – ausgenommen",
    matrix: "Melder × Profil",
    sheetTitle: "Notfallblatt Alarmanlage",
    sheetArm: "Scharf schalten",
    sheetDisarm: "Unscharf schalten",
    sheetAlarm: "Wenn der Alarm losgeht",
    sheetFire: "Bei Brand",
    sheetWho: "Wer benachrichtigt wird",
    sheetKeypad: "Am Keypad: erst PIN tippen oder Karte vorhalten, dann die Taste drücken.",
    sheetPanelArm: "In der Home-Assistant-App: Kachel „Hauswacht“ → Knopf des Profils.",
    sheetPanel: "In der Home-Assistant-App: Kachel „Hauswacht“ → „Unscharf“ bzw. Knopf „Unscharf schalten“.",
    sheetEntry:
      "Nach dem Öffnen der Tür bleiben {s} Sekunden zum Unscharfschalten ({p}).",
    sheetEnd:
      "Unscharf schalten beendet zuerst nur den Alarm – die Anlage bleibt scharf. Ein zweites Mal unscharf schalten schaltet wirklich aus.",
    sheetCycles: "Die Sirene läuft höchstens {s} Sekunden je Alarm.",
    sheetFireText:
      "Rauchmelder haben immer Vorrang. Haus verlassen, Notruf 112. Die Alarmanlage nicht zum Abschalten von Rauchmeldern verwenden.",
    sheetProfiles: "Profile",
    profileLine: "{n}: Knopf „{b}“",
    profileNoButton: "{n}: über „Profil“ + „Scharf schalten“",
  },
  en: {
    title: "Overview",
    refresh: "Refresh",
    print: "Print",
    sheet: "Emergency sheet",
    asOf: "As of",
    loading: "Loading overview …",
    adminOnly: "The overview is for administrators only.",
    error: "Overview not available",
    findings: "Review notes",
    noFindings: "Nothing to report.",
    where: "Change in",
    status: "Status",
    profiles: "Alarm profiles",
    sensors: "Sensors",
    rules: "Trigger rules",
    always: "Always active",
    sirens: "Sirens",
    users: "Users",
    controls: "Control devices",
    notifications: "Notifications",
    monitoring: "Monitoring",
    pinRules: "PIN rules",
    yes: "yes",
    no: "no",
    none: "–",
    testMode: "Test mode",
    sirensEnabled: "Sirens enabled",
    systemStatus: "System status",
    failures: "Wrong entries",
    lockedUntil: "locked until",
    area: "Area",
    button: "Button",
    zones: "Sensor groups",
    excluded: "Excluded",
    exitDelay: "Exit delay",
    entryDelay: "Entry delay",
    reaction: "Alarm reaction",
    cycles: "Alarm cycles",
    openPolicy: "Open sensors",
    unavailablePolicy: "Unavailable sensors",
    tamper: "Tamper triggers alarm",
    silent: "Silent alarm",
    tone: "Tone",
    volume: "Volume",
    recipients: "Alarm recipients",
    auto: "Automation",
    armAt: "arm at",
    disarmAt: "disarm at",
    weekdays: "Days",
    daily: "daily",
    awayPersons: "arm when away",
    after: "after",
    disarmOnArrival: "disarm on arrival",
    armOnClose: "Arm by closing",
    sensorsArmed: "Sensors armed individually",
    group: "Group",
    type: "Type",
    state: "State",
    lastContact: "Last contact",
    battery: "Battery",
    usedIn: "Used in",
    notUsed: "in no profile",
    tested: "Last test",
    heard: "heard",
    notHeard: "not heard",
    never: "never",
    capabilities: "Supports",
    pin: "PIN",
    cards: "Cards",
    rights: "Rights",
    validity: "Valid",
    haAccount: "HA account",
    inactive: "inactive",
    expired: "expired",
    masterPin: "Master PIN",
    anyPin: "PIN required (panel)",
    armCode: "PIN also for arming",
    buttonsNoPin: "Dashboard buttons despite PIN",
    topic: "MQTT topic",
    login: "Login",
    emergency: "Emergency key",
    action: "Action",
    general: "General recipients",
    event: "Event",
    speech: "Announcement",
    speakers: "Speakers",
    quiet: "Quiet hours",
    staleAfter: "Silence limit",
    recommended: "Recommended",
    observed: "observed",
    days: "days",
    off: "off",
    gateways: "Networks and gateways",
    learn: "Card learning time",
    turnOff: "turn off",
    duration: "duration",
    printNote:
      "Contains security information (e.g. what is not monitored when) – do not leave lying around.",
    legend: "✓ armed individually · R only in trigger rules · – excluded",
    matrix: "Sensor × profile",
    sheetTitle: "Alarm system emergency sheet",
    sheetArm: "Arming",
    sheetDisarm: "Disarming",
    sheetAlarm: "When the alarm goes off",
    sheetFire: "In case of fire",
    sheetWho: "Who gets notified",
    sheetKeypad: "At the keypad: first type the PIN or hold the card, then press the key.",
    sheetPanelArm: "In the Home Assistant app: tile “Hauswacht” → the profile's button.",
    sheetPanel: "In the Home Assistant app: tile “Hauswacht” → “Disarm” or button “Disarm”.",
    sheetEntry: "After opening the door you have {s} seconds to disarm ({p}).",
    sheetEnd:
      "Disarming first only ends the alarm – the system stays armed. Disarm a second time to switch it off.",
    sheetCycles: "The siren sounds for at most {s} seconds per alarm.",
    sheetFireText:
      "Smoke detectors always take precedence. Leave the house, call 112. Do not use the alarm system to silence smoke detectors.",
    sheetProfiles: "Profiles",
    profileLine: "{n}: button “{b}”",
    profileNoButton: "{n}: via “Profile” + “Arm”",
  },
};

const LABELS = {
  de: {
    button: { home: "Zuhause", night: "Nacht", away: "Abwesend", vacation: "Urlaub", custom: "Benutzerdefiniert" },
    policy: { refuse: "verweigern", confirm: "nach Bestätigung", bypass_auto: "automatisch überbrücken" },
    type: { door: "Tür", window: "Fenster", motion: "Bewegung", tamper: "Manipulation", technical: "Technik", other: "Sonstiges" },
    state: { open: "offen", closed: "zu", unavailable: "nicht verfügbar" },
    alarm: {
      disarmed: "unscharf", arming: "Ausgangsverzögerung", armed: "scharf", pending: "Eingangsverzögerung",
      triggered: "Alarm", alarm_hold: "Alarm (Sirenen aus)",
    },
    status: { ok: "OK", degraded: "Melder ausgefallen", fault: "Störung" },
    result: { alarm: "sofort Alarm", entry_delay: "Eingangsverzögerung, dann Alarm", notify: "nur Benachrichtigung" },
    right: { arm: "scharf", disarm: "unscharf", end_alarm: "Alarm beenden" },
    kind: { keypad: "Keypad", sticker: "NFC-Aufkleber", reader: "RFID-Leser" },
    login: { pin_or_card: "PIN oder Karte", card: "Karte", card_and_pin: "Karte und PIN" },
    emergency: { off: "aus", silent: "still", alarm: "Alarm" },
    action: { disarm: "unscharf", arm: "scharf", toggle: "umschalten" },
    key: { arm_day_zones: "Tag", arm_night_zones: "Nacht", arm_all_zones: "Alle" },
    tone: { burglar: "Einbruch", emergency: "Notfall", police_panic: "Polizei-Panik", emergency_panic: "Notfall-Panik", fire: "Brand" },
    volume: { low: "leise", medium: "mittel", high: "laut", very_high: "sehr laut" },
    weekday: { mon: "Mo", tue: "Di", wed: "Mi", thu: "Do", fri: "Fr", sat: "Sa", sun: "So" },
    event: {
      alarm: "Alarm", entry: "Eingangsverzögerung", armed: "Scharf geschaltet", disarmed: "Unscharf geschaltet",
      alarm_ended: "Alarm beendet", arm_failed: "Scharfschalten abgelehnt", automation: "Automatik", fault: "Störung",
      system: "System", reminder: "Erinnerung „Alle weg“", always_active: "Immer aktiv", rule_notify: "Regel: nur Meldung",
      arm_hint: "Hinweis beim Scharfschalten", unconfirmed: "Unbestätigte Auslösung", unconfirmed_frequent: "Melder löst häufig allein aus",
    },
  },
  en: {
    button: { home: "Home", night: "Night", away: "Away", vacation: "Vacation", custom: "Custom" },
    policy: { refuse: "refuse", confirm: "after confirmation", bypass_auto: "bypass automatically" },
    type: { door: "Door", window: "Window", motion: "Motion", tamper: "Tamper", technical: "Technical", other: "Other" },
    state: { open: "open", closed: "closed", unavailable: "unavailable" },
    alarm: {
      disarmed: "disarmed", arming: "exit delay", armed: "armed", pending: "entry delay",
      triggered: "alarm", alarm_hold: "alarm (sirens off)",
    },
    status: { ok: "OK", degraded: "sensors unavailable", fault: "fault" },
    result: { alarm: "immediate alarm", entry_delay: "entry delay, then alarm", notify: "notification only" },
    right: { arm: "arm", disarm: "disarm", end_alarm: "end alarm" },
    kind: { keypad: "Keypad", sticker: "NFC sticker", reader: "RFID reader" },
    login: { pin_or_card: "PIN or card", card: "card", card_and_pin: "card and PIN" },
    emergency: { off: "off", silent: "silent", alarm: "alarm" },
    action: { disarm: "disarm", arm: "arm", toggle: "toggle" },
    key: { arm_day_zones: "Day", arm_night_zones: "Night", arm_all_zones: "All" },
    tone: { burglar: "Burglar", emergency: "Emergency", police_panic: "Police panic", emergency_panic: "Emergency panic", fire: "Fire" },
    volume: { low: "low", medium: "medium", high: "high", very_high: "very high" },
    weekday: { mon: "Mon", tue: "Tue", wed: "Wed", thu: "Thu", fri: "Fri", sat: "Sat", sun: "Sun" },
    event: {
      alarm: "Alarm", entry: "Entry delay", armed: "Armed", disarmed: "Disarmed", alarm_ended: "Alarm ended",
      arm_failed: "Arming refused", automation: "Automation", fault: "Fault", system: "System",
      reminder: "Reminder “all away”", always_active: "Always active", rule_notify: "Rule: notification only",
      arm_hint: "Hint when arming", unconfirmed: "Unconfirmed trigger", unconfirmed_frequent: "Sensor triggers often alone",
    },
  },
};

const STYLE = `
  .wrap { padding: 16px; }
  .head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .head .t { font-size: 1.25rem; font-weight: 500; flex: 1; display: flex; align-items: center; gap: 10px; }
  .asof { color: var(--secondary-text-color); font-size: .85rem; margin: 2px 0 10px; }
  button.b { font: inherit; font-size: .9rem; padding: 6px 12px; border-radius: 18px; cursor: pointer;
    border: 1px solid var(--divider-color); background: var(--card-background-color); color: var(--primary-text-color); }
  button.b:hover { border-color: var(--primary-color); }
  .finding { display: flex; gap: 8px; padding: 6px 0; border-bottom: 1px solid var(--divider-color); }
  .finding:last-child { border-bottom: none; }
  .finding .ic { flex: none; }
  .finding .w { color: var(--secondary-text-color); font-size: .85rem; }
  .ok { color: var(--success-color, #43a047); padding: 4px 0; }
  details { border-top: 1px solid var(--divider-color); padding: 8px 0; }
  summary { cursor: pointer; font-weight: 500; list-style: none; display: flex; justify-content: space-between; gap: 8px; }
  summary::-webkit-details-marker { display: none; }
  summary::before { content: "▸"; margin-right: 6px; color: var(--secondary-text-color); }
  details[open] > summary::before { content: "▾"; }
  summary .s { flex: 1; }
  summary .c { color: var(--secondary-text-color); font-weight: 400; font-size: .9rem; text-align: right; }
  .sec { padding: 6px 0 0 18px; }
  .item { padding: 6px 0; border-bottom: 1px solid var(--divider-color); }
  .item:last-child { border-bottom: none; }
  .item .n { font-weight: 500; }
  .kv { display: grid; grid-template-columns: minmax(120px, 40%) 1fr; gap: 2px 12px; font-size: .9rem; margin-top: 4px; }
  .kv .k { color: var(--secondary-text-color); }
  .muted { color: var(--secondary-text-color); font-size: .85rem; }
  .warn { color: var(--warning-color, #ff9800); }
  table { border-collapse: collapse; width: 100%; font-size: .85rem; }
  th, td { text-align: left; padding: 4px 6px; border-bottom: 1px solid var(--divider-color); vertical-align: top; }
  th { color: var(--secondary-text-color); font-weight: 500; }
  td.c, th.c { text-align: center; }
  td.nw { white-space: nowrap; }
  .scroll { overflow-x: auto; }
`;

const PRINT_STYLE = `
  @page { size: A4; margin: 14mm 12mm; }
  * { box-sizing: border-box; }
  body { font-family: "Segoe UI", Roboto, "Noto Sans", Arial, sans-serif; font-size: 10pt; color: #000; margin: 0; }
  h1 { font-size: 16pt; margin: 0 0 2mm; }
  h2 { font-size: 12pt; margin: 6mm 0 2mm; border-bottom: 1px solid #000; padding-bottom: 1mm; break-after: avoid; }
  h3 { font-size: 10.5pt; margin: 3mm 0 1mm; break-after: avoid; }
  .note { border: 1px solid #000; padding: 2mm 3mm; margin: 2mm 0 4mm; font-size: 9pt; }
  .meta { font-size: 9pt; color: #333; }
  table { border-collapse: collapse; width: 100%; margin: 1mm 0 3mm; break-inside: auto; }
  tr { break-inside: avoid; }
  th, td { border: 1px solid #999; padding: 1mm 1.5mm; text-align: left; vertical-align: top; font-size: 9pt; }
  th { background: #eee; }
  td.c, th.c { text-align: center; }
  .kv td:first-child { width: 38%; color: #333; }
  ul { margin: 1mm 0 3mm 5mm; padding: 0; }
  li { margin: 0.5mm 0; }
  .sheet { font-size: 12pt; }
  .sheet h1 { font-size: 20pt; }
  .sheet h2 { font-size: 14pt; }
  .sheet li { margin: 2mm 0; }
`;

const esc = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

class HauswachtUebersichtCard extends HTMLElement {
  setConfig(config) {
    this._config = config || {};
    this._data = null;
    this._error = null;
    if (this.shadowRoot) this._render();
  }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    if (first) {
      this.attachShadow({ mode: "open" });
      this._render();
      this._load();
    }
  }

  static getStubConfig() {
    return {};
  }

  getCardSize() {
    return 6;
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6 };
  }

  get _lang() {
    return (this._hass?.language || "en").startsWith("de") ? "de" : "en";
  }

  _t(key) {
    return LANG[this._lang][key] ?? LANG.en[key] ?? key;
  }

  _l(group, value) {
    return (LABELS[this._lang][group] || {})[value] ?? value ?? this._t("none");
  }

  async _load() {
    this._error = null;
    try {
      this._data = await this._hass.callWS({ type: "hauswacht/overview" });
    } catch (err) {
      this._data = null;
      this._error = err && err.code === "unauthorized" ? this._t("adminOnly") : `${this._t("error")}: ${err?.message || err}`;
    }
    this._render();
  }

  _when(iso) {
    if (!iso) return this._t("never");
    const date = new Date(iso);
    return date.toLocaleString(this._lang === "de" ? "de-DE" : "en-GB", {
      day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit",
    });
  }

  _list(values) {
    return values && values.length ? values.map(esc).join(", ") : this._t("none");
  }

  _yn(value) {
    return value ? this._t("yes") : this._t("no");
  }

  // --- Bausteine (Bildschirm und Druck nutzen dieselben Zeilen) -----------------

  _profileRows(p) {
    const auto = p.auto || {};
    const autoParts = [];
    if (auto.arm_time) autoParts.push(`${this._t("armAt")} ${auto.arm_time}`);
    if (auto.disarm_time) autoParts.push(`${this._t("disarmAt")} ${auto.disarm_time}`);
    if (auto.arm_time || auto.disarm_time)
      autoParts.push(auto.weekdays?.length ? auto.weekdays.map((d) => this._l("weekday", d)).join(" ") : this._t("daily"));
    if (auto.away_persons?.length)
      autoParts.push(`${this._t("awayPersons")}: ${auto.away_persons.join(", ")} (${this._t("after")} ${auto.away_delay} min)`);
    if (auto.disarm_on_arrival) autoParts.push(this._t("disarmOnArrival"));
    const close = p.arm_on_close || {};
    const sirens = p.silent ? `${this._t("silent")}` : this._list(p.sirens);
    return [
      [this._t("area"), esc(p.area)],
      [this._t("button"), esc(p.button ? this._l("button", p.button) : this._t("none"))],
      [this._t("zones"), this._list(p.zones)],
      [this._t("excluded"), this._list(p.excluded)],
      [this._t("rules"), this._list(p.rules)],
      [this._t("sensorsArmed"), esc(p.sensor_count)],
      [`${this._t("exitDelay")} / ${this._t("entryDelay")}`, `${p.exit_delay} s / ${p.entry_delay} s`],
      [`${this._t("reaction")} / ${this._t("cycles")}`, `${p.reaction_time} s / ${p.max_alarm_cycles}`],
      [this._t("openPolicy"), esc(this._l("policy", p.open_policy))],
      [this._t("unavailablePolicy"), esc(this._l("policy", p.unavailable_policy))],
      [this._t("tamper"), this._yn(p.tamper_alarm)],
      [this._t("sirens"), sirens + (p.silent || !p.sirens?.length ? "" : ` (${esc(this._l("tone", p.siren_tone))}, ${esc(this._l("volume", p.siren_volume))})`)],
      [this._t("recipients"), this._list(p.alarm_targets)],
      [this._t("auto"), autoParts.length ? esc(autoParts.join(" · ")) : this._t("off")],
      [this._t("armOnClose"), close.enabled ? `${this._list(close.doors)} (${close.settle} s)` : this._t("off")],
    ];
  }

  _sensorRole(role) {
    return role === "armed" ? "✓" : role === "rule" ? "R" : role === "excluded" ? "–" : "";
  }

  _userRights(u) {
    return Object.entries(u.rights || {})
      .map(([area, rights]) => `${area}: ${rights.length ? rights.map((r) => this._l("right", r)).join(", ") : "–"}`)
      .join("; ");
  }

  _userValidity(u) {
    if (!u.active) return this._t("inactive");
    if (u.expired) return this._t("expired");
    if (!u.valid_from && !u.valid_until) return this._t("yes");
    return `${u.valid_from ? this._when(u.valid_from) : "…"} – ${u.valid_until ? this._when(u.valid_until) : "…"}`;
  }

  _sirenCaps(s) {
    const caps = [];
    if (s.tone_select) caps.push(s.tones?.length ? s.tones.map((t) => this._l("tone", t)).join("/") : this._t("tone"));
    if (s.volume) caps.push(this._t("volume"));
    if (s.duration) caps.push(this._t("duration"));
    if (s.turn_off) caps.push(this._t("turnOff"));
    return caps.join(", ");
  }

  _sirenTest(s) {
    if (!s.last_test) return this._t("never");
    const heard = s.heard === true ? this._t("heard") : s.heard === false ? this._t("notHeard") : "";
    return `${this._when(s.last_test)}${heard ? ` (${heard})` : ""}`;
  }

  _controlDetail(c) {
    if (c.kind === "keypad") {
      const keys = Object.entries(c.buttons || {}).map(([k, p]) => `${this._l("key", k)} → ${p}`).join(", ");
      return `${this._t("topic")}: ${esc(c.topic)} · ${esc(keys || this._t("none"))} · ${this._t("login")}: ${esc(this._l("login", c.login))} · ${this._t("emergency")}: ${esc(this._l("emergency", c.emergency))}`;
    }
    const profile = c.profile ? ` (${esc(c.profile)})` : "";
    const login = c.kind === "reader" ? ` · ${this._t("login")}: ${esc(this._l("login", c.login))}` : "";
    return `${this._t("action")}: ${esc(this._l("action", c.action))}${profile}${login}`;
  }

  _staleText(m) {
    const now = m.stale_after_hours ? `${m.stale_after_hours} h` : this._t("off");
    const rec = m.recommended_hours ? ` · ${this._t("recommended")}: ${m.recommended_hours} h` : "";
    return `${now}${rec} (${this._t("observed")} ${m.observed_days} ${this._t("days")})`;
  }

  // --- Bildschirm ---------------------------------------------------------------

  _section(title, count, body, open = false) {
    return `<details ${open ? "open" : ""}><summary><span class="s">${esc(title)}</span><span class="c">${count}</span></summary><div class="sec">${body}</div></details>`;
  }

  _kv(rows) {
    return `<div class="kv">${rows.map(([k, v]) => `<div class="k">${esc(k)}</div><div>${v}</div>`).join("")}</div>`;
  }

  _screen() {
    const d = this._data;
    const sys = d.system || {};
    const findings = d.findings || [];
    const important = findings.filter((f) => f.severity === "warning").length;
    const findingHtml = findings.length
      ? findings
          .map(
            (f) =>
              `<div class="finding"><span class="ic">${f.severity === "warning" ? "⚠️" : "ℹ️"}</span><div>${esc(f.text)}<div class="w">${this._t("where")}: ${esc(f.where)}</div></div></div>`
          )
          .join("")
      : `<div class="ok">✓ ${this._t("noFindings")}</div>`;
    const statusRows = [
      ...d.areas.map((a) => [a.name, esc(this._l("alarm", a.state) + (a.profile ? ` · ${a.profile}` : ""))]),
      [this._t("testMode"), this._yn(sys.test_mode)],
      [this._t("sirensEnabled"), this._yn(sys.sirens_enabled)],
      [this._t("systemStatus"), esc(this._l("status", sys.status))],
      [this._t("failures"), `${sys.code_failures || 0}${sys.code_locked_until ? ` · ${this._t("lockedUntil")} ${this._when(sys.code_locked_until)}` : ""}`],
    ];
    const profiles = d.profiles
      .map((p) => `<details><summary><span class="s">${esc(p.name)}</span><span class="c">${esc(p.button ? this._l("button", p.button) : "")}</span></summary><div class="sec">${this._kv(this._profileRows(p))}</div></details>`)
      .join("");
    const sensorRows = d.sensors
      .map(
        (s) =>
          `<tr><td>${esc(s.name)}${s.always_active ? ` <span class="muted">(${this._t("always")})</span>` : ""}</td><td>${esc(this._l("type", s.type))}</td><td class="${s.state === "unavailable" ? "warn" : ""}">${esc(this._l("state", s.state))}</td><td class="nw">${s.battery != null ? `${s.battery} %` : ""}</td>${d.profiles.map((p) => `<td class="c">${this._sensorRole((s.profiles || {})[p.id])}</td>`).join("")}</tr>`
      )
      .join("");
    const sensors = `<div class="muted">${this._t("legend")}</div><div class="scroll"><table><tr><th>${this._t("sensors")}</th><th>${this._t("type")}</th><th>${this._t("state")}</th><th>🔋</th>${d.profiles.map((p) => `<th class="c">${esc(p.name)}</th>`).join("")}</tr>${sensorRows}</table></div>`;
    const rules = d.rules
      .map((r) => `<div class="item"><div class="n">${esc(r.name)}</div><div class="muted">${esc(r.text)}</div><div class="muted">${this._t("usedIn")}: ${r.profiles.length ? this._list(r.profiles) : this._t("notUsed")}</div></div>`)
      .join("");
    const sirens = d.sirens
      .map((s) => `<div class="item"><div class="n">${esc(s.name)}</div>${this._kv([[this._t("tested"), esc(this._sirenTest(s))], [this._t("capabilities"), esc(this._sirenCaps(s))]])}</div>`)
      .join("");
    const users = d.users
      .map((u) => `<div class="item"><div class="n">${esc(u.name)}</div>${this._kv([[this._t("pin"), this._yn(u.pin)], [this._t("cards"), u.cards.length ? esc(u.cards.join(", ")) : this._t("none")], [this._t("rights"), esc(this._userRights(u))], [this._t("validity"), esc(this._userValidity(u))], [this._t("haAccount"), this._yn(u.ha_account)]])}</div>`)
      .join("");
    const pr = d.pin_rules || {};
    const pinRules = this._kv([
      [this._t("masterPin"), this._yn(pr.master_pin)],
      [this._t("anyPin"), this._yn(pr.any_pin)],
      [this._t("armCode"), this._yn(pr.arm_requires_code)],
      [this._t("buttonsNoPin"), this._yn(pr.buttons_without_pin)],
    ]);
    const controls = d.controls.length
      ? d.controls.map((c) => `<div class="item"><div class="n">${esc(c.name)} <span class="muted">${esc(this._l("kind", c.kind))}${c.area ? ` · ${esc(c.area)}` : ""}</span></div><div class="muted">${this._controlDetail(c)}</div></div>`).join("")
      : this._t("none");
    const n = d.notifications || {};
    const notify = `${this._kv([[this._t("general"), this._list(n.general)], [this._t("speakers"), this._list(n.speakers)], [this._t("quiet"), esc(n.quiet || this._t("off"))]])}<table><tr><th>${this._t("event")}</th><th>${this._t("recipients")}</th><th class="c">${this._t("speech")}</th></tr>${(n.events || []).map((e) => `<tr><td>${esc(this._l("event", e.event))}</td><td>${this._list(e.targets)}</td><td class="c">${e.speech ? "🔊" : ""}</td></tr>`).join("")}</table>`;
    const m = d.monitoring || {};
    const monitoring = this._kv([
      [this._t("staleAfter"), esc(this._staleText(m))],
      [this._t("gateways"), m.infrastructure?.length ? m.infrastructure.map((i) => `${esc(i.name)} ${i.ok ? "✓" : "⚠️"}`).join(", ") : this._t("none")],
      [this._t("learn"), m.card_learn_minutes ? `${m.card_learn_minutes} min` : this._t("off")],
    ]);
    const always = d.always_active || {};
    const alwaysSensors = d.sensors.filter((s) => s.always_active).map((s) => s.name);
    return `
      <div class="asof">${this._t("asOf")}: ${this._when(d.generated_at)}</div>
      ${this._section(`${this._t("findings")}`, findings.length ? [important ? `⚠️ ${important}` : "", findings.length - important ? `ℹ️ ${findings.length - important}` : ""].filter(Boolean).join(" · ") : "✓", findingHtml, important > 0)}
      ${this._section(this._t("status"), esc(d.areas.map((a) => this._l("alarm", a.state)).join(" · ")), this._kv(statusRows))}
      ${this._section(this._t("profiles"), d.profiles.length, profiles)}
      ${this._section(this._t("sensors"), d.sensors.length, sensors)}
      ${this._section(this._t("rules"), d.rules.length, rules || this._t("none"))}
      ${this._section(this._t("always"), alwaysSensors.length, this._kv([[this._t("sensors"), this._list(alwaysSensors)], [this._t("sirens"), this._list(always.sirens)]]))}
      ${this._section(this._t("sirens"), d.sirens.length, sirens || this._t("none"))}
      ${this._section(this._t("users"), d.users.length, users + `<div class="item"><div class="n">${this._t("pinRules")}</div>${pinRules}</div>`)}
      ${this._section(this._t("controls"), d.controls.length, controls)}
      ${this._section(this._t("notifications"), (n.events || []).length, notify)}
      ${this._section(this._t("monitoring"), "", monitoring)}
    `;
  }

  _render() {
    if (!this.shadowRoot) return;
    const title = this._config?.title || this._t("title");
    let body;
    if (this._error) body = `<div class="muted">${esc(this._error)}</div>`;
    else if (!this._data) body = `<div class="muted">${this._t("loading")}</div>`;
    else body = this._screen();
    this.shadowRoot.innerHTML = `
      <style>${STYLE}</style>
      <ha-card><div class="wrap">
        <div class="head">
          <div class="t"><ha-icon icon="mdi:clipboard-text-outline"></ha-icon><span>${esc(title)}</span></div>
          <button class="b" data-a="refresh">↻ ${this._t("refresh")}</button>
          <button class="b" data-a="print" ${this._data ? "" : "disabled"}>🖨 ${this._t("print")}</button>
          <button class="b" data-a="sheet" ${this._data ? "" : "disabled"}>📄 ${this._t("sheet")}</button>
        </div>
        ${body}
      </div></ha-card>`;
    this.shadowRoot.querySelectorAll("button[data-a]").forEach((btn) =>
      btn.addEventListener("click", () => {
        const a = btn.dataset.a;
        if (a === "refresh") this._load();
        else if (a === "print") this._print(this._printHtml());
        else if (a === "sheet") this._print(this._sheetHtml());
      })
    );
  }

  // --- Druck -------------------------------------------------------------------

  _table(rows) {
    return `<table class="kv">${rows.map(([k, v]) => `<tr><td>${esc(k)}</td><td>${v}</td></tr>`).join("")}</table>`;
  }

  _printHtml() {
    const d = this._data;
    const sys = d.system || {};
    const out = [];
    out.push(`<h1>Hauswacht – ${this._t("title")}</h1><div class="meta">${this._t("asOf")}: ${this._when(d.generated_at)}</div>`);
    out.push(`<div class="note">${this._t("printNote")}</div>`);
    out.push(`<h2>${this._t("findings")}</h2>`);
    out.push(
      d.findings.length
        ? `<ul>${d.findings.map((f) => `<li>${f.severity === "warning" ? "⚠ " : ""}${esc(f.text)} <i>(${this._t("where")}: ${esc(f.where)})</i></li>`).join("")}</ul>`
        : `<p>${this._t("noFindings")}</p>`
    );
    out.push(`<h2>${this._t("status")}</h2>`);
    out.push(
      this._table([
        ...d.areas.map((a) => [a.name, esc(this._l("alarm", a.state) + (a.profile ? ` · ${a.profile}` : ""))]),
        [this._t("testMode"), this._yn(sys.test_mode)],
        [this._t("sirensEnabled"), this._yn(sys.sirens_enabled)],
        [this._t("systemStatus"), esc(this._l("status", sys.status))],
      ])
    );
    out.push(`<h2>${this._t("profiles")}</h2>`);
    for (const p of d.profiles) out.push(`<h3>${esc(p.name)}</h3>${this._table(this._profileRows(p))}`);
    out.push(`<h2>${this._t("matrix")}</h2><div class="meta">${this._t("legend")}</div>`);
    out.push(
      `<table><tr><th>${this._t("sensors")}</th><th>${this._t("group")}</th><th>${this._t("type")}</th><th>${this._t("state")}</th><th>${this._t("lastContact")}</th><th>${this._t("battery")}</th>${d.profiles.map((p) => `<th class="c">${esc(p.name)}</th>`).join("")}</tr>` +
        d.sensors
          .map(
            (s) =>
              `<tr><td>${esc(s.name)}${s.always_active ? ` (${this._t("always")})` : ""}</td><td>${esc(s.zone || "–")}</td><td>${esc(this._l("type", s.type))}</td><td>${esc(this._l("state", s.state))}</td><td>${s.last_contact ? this._when(s.last_contact) : "–"}</td><td>${s.battery != null ? `${s.battery} %` : "–"}</td>${d.profiles.map((p) => `<td class="c">${this._sensorRole((s.profiles || {})[p.id])}</td>`).join("")}</tr>`
          )
          .join("") +
        `</table>`
    );
    out.push(`<h2>${this._t("rules")}</h2>`);
    out.push(
      d.rules.length
        ? `<table><tr><th>${this._t("rules")}</th><th></th><th>${this._t("usedIn")}</th></tr>${d.rules.map((r) => `<tr><td>${esc(r.name)}</td><td>${esc(r.text)}</td><td>${r.profiles.length ? this._list(r.profiles) : this._t("notUsed")}</td></tr>`).join("")}</table>`
        : `<p>${this._t("none")}</p>`
    );
    const alwaysSensors = d.sensors.filter((s) => s.always_active).map((s) => s.name);
    out.push(`<h2>${this._t("always")}</h2>${this._table([[this._t("sensors"), this._list(alwaysSensors)], [this._t("sirens"), this._list(d.always_active?.sirens)]])}`);
    out.push(`<h2>${this._t("sirens")}</h2>`);
    out.push(
      d.sirens.length
        ? `<table><tr><th>${this._t("sirens")}</th><th>${this._t("capabilities")}</th><th>${this._t("tested")}</th></tr>${d.sirens.map((s) => `<tr><td>${esc(s.name)}</td><td>${esc(this._sirenCaps(s))}</td><td>${esc(this._sirenTest(s))}</td></tr>`).join("")}</table>`
        : `<p>${this._t("none")}</p>`
    );
    out.push(`<h2>${this._t("users")}</h2>`);
    out.push(
      `<table><tr><th>${this._t("users")}</th><th>${this._t("pin")}</th><th>${this._t("cards")}</th><th>${this._t("rights")}</th><th>${this._t("validity")}</th><th>${this._t("haAccount")}</th></tr>${d.users.map((u) => `<tr><td>${esc(u.name)}</td><td>${this._yn(u.pin)}</td><td>${u.cards.length ? esc(u.cards.join(", ")) : "–"}</td><td>${esc(this._userRights(u))}</td><td>${esc(this._userValidity(u))}</td><td>${this._yn(u.ha_account)}</td></tr>`).join("")}</table>`
    );
    const pr = d.pin_rules || {};
    out.push(`<h3>${this._t("pinRules")}</h3>${this._table([[this._t("masterPin"), this._yn(pr.master_pin)], [this._t("anyPin"), this._yn(pr.any_pin)], [this._t("armCode"), this._yn(pr.arm_requires_code)], [this._t("buttonsNoPin"), this._yn(pr.buttons_without_pin)]])}`);
    out.push(`<h2>${this._t("controls")}</h2>`);
    out.push(
      d.controls.length
        ? `<table>${d.controls.map((c) => `<tr><td>${esc(c.name)}<br>${esc(this._l("kind", c.kind))}${c.area ? ` · ${esc(c.area)}` : ""}</td><td>${this._controlDetail(c)}</td></tr>`).join("")}</table>`
        : `<p>${this._t("none")}</p>`
    );
    const n = d.notifications || {};
    out.push(`<h2>${this._t("notifications")}</h2>`);
    out.push(this._table([[this._t("general"), this._list(n.general)], [this._t("speakers"), this._list(n.speakers)], [this._t("quiet"), esc(n.quiet || this._t("off"))]]));
    out.push(`<table><tr><th>${this._t("event")}</th><th>${this._t("recipients")}</th><th class="c">${this._t("speech")}</th></tr>${(n.events || []).map((e) => `<tr><td>${esc(this._l("event", e.event))}</td><td>${this._list(e.targets)}</td><td class="c">${e.speech ? "✓" : ""}</td></tr>`).join("")}</table>`);
    const m = d.monitoring || {};
    out.push(`<h2>${this._t("monitoring")}</h2>`);
    out.push(
      this._table([
        [this._t("staleAfter"), esc(this._staleText(m))],
        [this._t("gateways"), m.infrastructure?.length ? m.infrastructure.map((i) => `${esc(i.name)} ${i.ok ? "✓" : "⚠"}`).join(", ") : this._t("none")],
        [this._t("learn"), m.card_learn_minutes ? `${m.card_learn_minutes} min` : this._t("off")],
      ])
    );
    return `<div>${out.join("\n")}</div>`;
  }

  _sheetHtml() {
    const d = this._data;
    const fill = (text, values) => text.replace(/\{(\w)\}/g, (_, k) => esc(values[k] ?? ""));
    const profiles = d.profiles.map((p) =>
      p.button ? fill(this._t("profileLine"), { n: p.name, b: this._l("button", p.button) }) : fill(this._t("profileNoButton"), { n: p.name })
    );
    const keypads = d.controls.some((c) => c.kind === "keypad");
    const keypad = keypads ? [this._t("sheetKeypad")] : [];
    const armHow = [...keypad, this._t("sheetPanelArm")];
    const howTo = [...keypad, this._t("sheetPanel")];
    const byDelay = {};
    for (const p of d.profiles) if (p.entry_delay > 0) (byDelay[p.entry_delay] = byDelay[p.entry_delay] || []).push(p.name);
    const entry = Object.entries(byDelay).map(([s, names]) => fill(this._t("sheetEntry"), { s, p: names.join(", ") }));
    const maxReaction = Math.max(0, ...d.profiles.map((p) => p.reaction_time || 0));
    const who = [...new Set(d.profiles.flatMap((p) => p.alarm_targets || []))];
    return `<div class="sheet">
      <h1>${this._t("sheetTitle")}</h1>
      <div class="meta">${this._t("asOf")}: ${this._when(d.generated_at)}</div>
      <h2>${this._t("sheetArm")}</h2>
      <ul>${armHow.map((t) => `<li>${esc(t)}</li>`).join("")}</ul>
      <h3>${this._t("sheetProfiles")}</h3>
      <ul>${profiles.map((t) => `<li>${t}</li>`).join("")}</ul>
      <h2>${this._t("sheetDisarm")}</h2>
      <ul>${howTo.map((t) => `<li>${esc(t)}</li>`).join("")}${entry.map((t) => `<li>${t}</li>`).join("")}</ul>
      <h2>${this._t("sheetAlarm")}</h2>
      <ul><li>${esc(this._t("sheetEnd"))}</li>${maxReaction ? `<li>${fill(this._t("sheetCycles"), { s: maxReaction })}</li>` : ""}</ul>
      <h3>${this._t("sheetWho")}</h3>
      <ul>${who.length ? who.map((w) => `<li>${esc(w)}</li>`).join("") : `<li>${this._t("none")}</li>`}</ul>
      <h2>${this._t("sheetFire")}</h2>
      <ul><li>${esc(this._t("sheetFireText"))}</li></ul>
    </div>`;
  }

  _print(content) {
    // Eigenes, unsichtbares Dokument: druckt nur die Übersicht, nicht das ganze Dashboard
    const frame = document.createElement("iframe");
    frame.style.cssText = "position:fixed;right:0;bottom:0;width:0;height:0;border:0;";
    document.body.appendChild(frame);
    const doc = frame.contentWindow.document;
    doc.open();
    doc.write(`<!doctype html><html lang="${this._lang}"><head><meta charset="utf-8"><title>Hauswacht</title><style>${PRINT_STYLE}</style></head><body>${content}</body></html>`);
    doc.close();
    setTimeout(() => {
      frame.contentWindow.focus();
      frame.contentWindow.print();
      setTimeout(() => frame.remove(), 1000);
    }, 250);
  }
}

if (!customElements.get("hauswacht-uebersicht-card")) {
  customElements.define("hauswacht-uebersicht-card", HauswachtUebersichtCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "hauswacht-uebersicht-card",
    name: "Hauswacht Übersicht",
    description: "Die ganze Konfiguration der Alarmanlage mit Prüfhinweisen – zum Ansehen und Drucken (nur Administratoren)",
    preview: false,
    documentationURL: "https://github.com/schlusenbaum/hauswacht/blob/main/docs/uebersicht.md",
  });
}
