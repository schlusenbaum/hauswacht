/*
 * Hauswacht Test – Dashboard-Karte zum Simulieren der Hauswacht-Sensoren.
 *
 * Wird von der Integration Hauswacht automatisch geladen. Zeigt alle Sensoren aus den
 * Hauswacht-Meldergruppen mit Knöpfen "Auf/Zu", "Bewegung/Ruhe", "Manipulation/OK",
 * "Weg" (nicht verfügbar) und "Echt" (zurück auf den echten Wert).
 *
 * Sicherheit: Simulieren geht nur im Testmodus. Im Testmodus lösen keine Sirenen aus.
 * Simuliert wird nur für Hauswacht – Gerät und Zustand in Home Assistant bleiben
 * unverändert, andere Automationen merken nichts. Testmodus aus = alles wieder echt.
 *
 * Konfiguration (alles optional):
 *   type: custom:hauswacht-test-card
 *   title: Test
 */

const DOMAIN = "hauswacht";

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

const TEXT = {
  de: {
    presence: {
      title: "Anwesenheit",
      states: { home: "zuhause", away: "weg", unknown: "unbekannt" },
      approaching: "nähert sich",
      buttons: { home: "Zuhause", away: "Weg", away_no_proof: "Weg ohne Beleg", approaching: "Nähert sich", real: "Echt" },
      reasonSim: "simuliert (nur für Hauswacht)",
      reasonHome: "zuhause laut: {by}",
      reasonNoProof: "alle Signale „weg“, aber kein Beleg – zählt nicht als weg",
      reasonEntity: "eigener Auslöser, Zustand „{s}“",
      reasonUnclear: "unklar: {by}",
      proofs: { fresh: "Beleg: frische Ortung außerhalb", door: "Beleg: Tür + Ortung außerhalb", weak: "Beleg: Tür + Signal (unsicher)", one_door: "Beleg: Tür + eines der Signale", one: "Beleg: eines der Signale (ohne Tür, unsicher)", trigger: "eigener Auslöser", simulated: "Beleg: simuliert", other: "Beleg vorhanden" },
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
      skip: "Wartezeit überspringen",
    },
    title: "Test",
    testOff: "Simulieren geht nur im Testmodus. Im Testmodus lösen keine Sirenen aus, und Benachrichtigungen tragen „[TEST]“.",
    testOn: "Testmodus an – keine Sirenen. Simuliert wird nur für Hauswacht; Geräte und andere Automationen merken nichts.",
    enable: "Testmodus einschalten",
    disable: "Testmodus ausschalten",
    reset: "Alle echt",
    codeReset: "Falscheingaben zurücksetzen",
    codeLocked: "gesperrt",
    missing: "Hauswacht-Testsensor nicht gefunden (Hauswacht 0.17.1 oder neuer nötig).",
    empty: "Keine Melder in den Hauswacht-Meldergruppen.",
    real: "Echt",
    sirenTitle: "🔊 Sirenentest (echte Sirene!)",
    sirenWarn: "Hier ertönt eine echte Sirene – kurz und leise (3 s). Nur testen, wenn du vor Ort bist und Mitbewohner informiert sind. Im Testmodus ist der Sirenentest gesperrt.",
    sirenNone: "Keine Sirenen eingerichtet.",
    sirenLast: "Zuletzt getestet:",
    sirenNever: "Noch nie getestet",
    sirenTest: "Testen …",
    sirenConfirm: "Sirene ertönt jetzt 3 s. Wirklich starten?",
    sirenYesStart: "Ja, starten",
    sirenCancel: "Abbrechen",
    sirenHeard: "Hast du die Sirene gehört?",
    sirenStop: "Stopp",
    sirenRunning: "Läuft … Rauchmelder mit Batterie reagieren oft erst nach einigen Sekunden – kurz warten.",
    yes: "Ja",
    no: "Nein",
    sirenBlocked: {
      siren_test_running: "Ein Sirenentest läuft gerade.",
      siren_test_armed: "Nur möglich, wenn alle Bereiche unscharf sind.",
    },
    gone: "Weg",
    realValue: "echt",
    simulated: "simuliert",
    panel: "Anlage",
    open: ["Auf", "Zu"],
    motion: ["Bewegung", "Ruhe"],
    vibration: ["Erschütterung", "Ruhe"],
    vibrationStates: { on: "Erschütterung", off: "Ruhe" },
    tamper: ["Manipulation", "OK"],
    other: ["Ein", "Aus"],
    states: { on: "ein", off: "aus", unavailable: "nicht verfügbar", unknown: "unbekannt" },
    openStates: { on: "offen", off: "zu", tilted: "gekippt" },
    tiltLabel: "Gekippt",
    motionStates: { on: "Bewegung", off: "Ruhe" },
    tamperStates: { on: "Manipulation", off: "OK" },
    lock: ["Entriegelt", "Verriegelt"],
    lockStates: { on: "entriegelt", off: "verriegelt" },
    status: {
      disarmed: "",
      monitored: "überwacht",
      in_rule: "nur in Auslöseregeln:",
      always_active: "immer aktiv – löst auch unscharf aus",
      not_monitored: "nicht im aktiven Profil – wird ignoriert",
      exit_inside: "Melder im Haus für „Rausgehen ohne PIN erkennen“ – löst selbst nichts aus",
      bypassed: "überbrückt – bis zum Unscharfschalten nicht überwacht",
      bypassed_until_closed: "überbrückt bis zum Schließen – erst „Zu“, dann wieder überwacht",
      tamper_alarm: "Manipulation löst Alarm aus",
      tamper_message: "Manipulation: nur Meldung, kein Alarm",
    },
    phase: {
      disarmed: "unscharf",
      arming: "Ausgangsverzögerung",
      armed: "scharf",
      pending: "Eingangsverzögerung",
      triggered: "ALARM",
      alarm_hold: "Alarm (Sirenen aus, noch nicht beendet)",
    },
    profile: "Profil",
    exit: {
      passage: "Ausgangserkennung: Durchgang (Melder im Haus) – Tür frei, noch {t}.",
      wait: "Ausgangserkennung: stille Wartezeit – Alarm in {t}, wenn niemand rausgeht.",
      watched: "Beobachtet: {who}.",
      gone: "{who} „weg“ seit {s} s (zählt ab 30 s)",
    },
    exitInsideToo: "auch Melder im Haus für „Rausgehen ohne PIN erkennen“",
    rules: "Auslöseregeln im aktiven Profil",
    ruleIdle: "nicht begonnen",
    ruleStep: "Schritt {done} von {steps} erfüllt",
    ruleResult: { alarm: "sofort Alarm", entry_delay: "Eingangsverzögerung", notify: "nur Benachrichtigung" },
    ruleBlocked: "gesperrt durch Ausnahme",
  },
  en: {
    presence: {
      title: "Presence",
      states: { home: "home", away: "away", unknown: "unknown" },
      approaching: "approaching",
      buttons: { home: "Home", away: "Away", away_no_proof: "Away without proof", approaching: "Approaching", real: "Real" },
      reasonSim: "simulated (for Hauswacht only)",
      reasonHome: "home according to: {by}",
      reasonNoProof: "all signals “away”, but no proof – does not count as away",
      reasonEntity: "own trigger, state “{s}”",
      reasonUnclear: "unclear: {by}",
      proofs: { fresh: "Proof: fresh location outside", door: "Proof: door + location outside", weak: "Proof: door + signal (uncertain)", one_door: "Proof: door + one of the signals", one: "Proof: one of the signals (no door, uncertain)", trigger: "own trigger", simulated: "Proof: simulated", other: "Proof available" },
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
      skip: "Skip waiting time",
    },
    title: "Test",
    testOff: "Simulation only works in test mode. In test mode no siren sounds and notifications carry \"[TEST]\".",
    testOn: "Test mode on – no sirens. Simulated for Hauswacht only; devices and other automations notice nothing.",
    enable: "Turn on test mode",
    disable: "Turn off test mode",
    reset: "All real",
    codeReset: "Reset failed attempts",
    codeLocked: "locked",
    missing: "Hauswacht test sensor not found (Hauswacht 0.17.1 or newer required).",
    empty: "No sensors in the Hauswacht sensor groups.",
    real: "Real",
    sirenTitle: "🔊 Siren test (real siren!)",
    sirenWarn: "A real siren sounds here – short and quiet (3 s). Only test when you are on site and housemates are informed. The siren test is blocked in test mode.",
    sirenNone: "No sirens set up.",
    sirenLast: "Last tested:",
    sirenNever: "Never tested",
    sirenTest: "Test …",
    sirenConfirm: "The siren will sound for 3 s. Really start?",
    sirenYesStart: "Yes, start",
    sirenCancel: "Cancel",
    sirenHeard: "Did you hear the siren?",
    sirenStop: "Stop",
    sirenRunning: "Running … battery smoke detectors often react only after a few seconds – wait a moment.",
    yes: "Yes",
    no: "No",
    sirenBlocked: {
      siren_test_running: "A siren test is running.",
      siren_test_armed: "Only possible when all areas are disarmed.",
    },
    gone: "Gone",
    realValue: "real",
    simulated: "simulated",
    panel: "System",
    open: ["Open", "Closed"],
    motion: ["Motion", "Clear"],
    vibration: ["Vibration", "Calm"],
    vibrationStates: { on: "vibration", off: "calm" },
    tamper: ["Tamper", "OK"],
    other: ["On", "Off"],
    states: { on: "on", off: "off", unavailable: "unavailable", unknown: "unknown" },
    openStates: { on: "open", off: "closed", tilted: "tilted" },
    tiltLabel: "Tilted",
    motionStates: { on: "motion", off: "clear" },
    tamperStates: { on: "tamper", off: "OK" },
    lock: ["Unlocked", "Locked"],
    lockStates: { on: "unlocked", off: "locked" },
    status: {
      disarmed: "",
      monitored: "monitored",
      in_rule: "only in trigger rules:",
      always_active: "always active – triggers even when disarmed",
      not_monitored: "not in the active profile – ignored",
      exit_inside: "sensor in the house for “detect going out without a PIN” – triggers nothing itself",
      bypassed: "bypassed – not monitored until disarming",
      bypassed_until_closed: "bypassed until closed – press \"Closed\" to monitor again",
      tamper_alarm: "tamper triggers an alarm",
      tamper_message: "tamper: message only, no alarm",
    },
    phase: {
      disarmed: "disarmed",
      arming: "exit delay",
      armed: "armed",
      pending: "entry delay",
      triggered: "ALARM",
      alarm_hold: "alarm (sirens off, not ended yet)",
    },
    profile: "Profile",
    exit: {
      passage: "Exit detection: passage (sensor in the house) – door free, {t} left.",
      wait: "Exit detection: silent waiting time – alarm in {t} if nobody goes out.",
      watched: "Watched: {who}.",
      gone: "{who} “away” for {s} s (counts from 30 s)",
    },
    exitInsideToo: "also sensor in the house for “detect going out without a PIN”",
    rules: "Trigger rules in the active profile",
    ruleIdle: "not started",
    ruleStep: "step {done} of {steps} fulfilled",
    ruleResult: { alarm: "alarm immediately", entry_delay: "entry delay", notify: "notification only" },
    ruleBlocked: "blocked by exception",
  },
};

const OPEN_CLASSES = ["door", "window", "opening", "garage_door"];
const MOTION_CLASSES = ["motion", "occupancy", "presence", "moving"];

const ICONS = {
  door: "mdi:door",
  garage_door: "mdi:garage",
  window: "mdi:window-closed-variant",
  opening: "mdi:square-rounded-outline",
  motion: "mdi:motion-sensor",
  occupancy: "mdi:home-account",
  presence: "mdi:account-eye",
  vibration: "mdi:vibrate",
  tamper: "mdi:shield-alert-outline",
  lock: "mdi:lock-outline",
  cover: "mdi:garage-variant",
};

const STYLE = `
  ha-card { padding: 16px; }
  .title { font-size: 1.2em; font-weight: 500; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
  .panel { color: var(--secondary-text-color); font-size: 0.9em; margin-left: auto; font-weight: normal; }
  .hint { color: var(--secondary-text-color); font-size: 0.9em; margin: 4px 0 8px; }
  .hint.on { color: var(--warning-color); }
  .actions { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
  button {
    font: inherit; font-size: 0.9em; cursor: pointer; border-radius: 8px; padding: 6px 10px;
    border: 1px solid var(--divider-color); background: none; color: var(--primary-text-color);
  }
  button:disabled { opacity: 0.4; cursor: default; }
  button.primary { background: var(--primary-color); color: var(--text-primary-color, #fff); border-color: var(--primary-color); }
  .row { display: flex; align-items: center; gap: 10px; padding: 6px 0; border-bottom: 1px solid var(--divider-color); flex-wrap: wrap; }
  .row:last-child { border-bottom: none; }
  .row ha-icon { color: var(--state-icon-color, var(--secondary-text-color)); flex: none; }
  .row.sim ha-icon { color: var(--warning-color); }
  .info { flex: 1; min-width: 140px; }
  .name { overflow: hidden; text-overflow: ellipsis; }
  .state { color: var(--secondary-text-color); font-size: 0.85em; }
  .row.sim .state { color: var(--warning-color); }
  .status { font-size: 0.85em; color: var(--secondary-text-color); }
  .status.warn { color: var(--warning-color); }
  .status.muted { opacity: 0.7; }
  .phase { margin: 0 0 8px; padding: 8px 12px; border-radius: 8px; background: var(--secondary-background-color, rgba(127,127,127,.1)); }
  .rules { margin: 0 0 8px; font-size: 0.9em; }
  .rules .head { color: var(--secondary-text-color); font-size: 0.85em; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 2px; }
  .rules .rule { display: flex; justify-content: space-between; gap: 8px; padding: 2px 0; }
  .rules .rule.active { color: var(--warning-color); }
  .presence .btns { display: flex; gap: 4px; flex-wrap: wrap; }
  .presence button.active { border-color: var(--primary-color); color: var(--primary-color); }
  .presence button.skip { margin-top: 4px; }
  .rules .rule-text { color: var(--secondary-text-color); font-size: 0.85em; margin: 0 0 4px; }
  .phase.alarm { background: var(--error-color); color: var(--text-primary-color, #fff); }
  .phase.delay { background: var(--warning-color); color: var(--text-primary-color, #fff); }
  .sirens { margin-top: 12px; border-top: 1px solid var(--divider-color); padding-top: 8px; }
  .sirens summary { cursor: pointer; font-weight: 500; color: var(--error-color); }
  .seg { display: flex; flex: none; }
  .seg button { border-radius: 0; margin-left: -1px; padding: 6px 8px; }
  .seg button:first-child { border-radius: 8px 0 0 8px; margin-left: 0; }
  .seg button:last-child { border-radius: 0 8px 8px 0; }
  .seg button.active { background: var(--primary-color); color: var(--text-primary-color, #fff); border-color: var(--primary-color); }
`;

class HauswachtTestCard extends HTMLElement {
  setConfig(config) {
    this._config = config || {};
    this._built = false;
  }

  static getStubConfig() {
    return {};
  }

  // Visueller Editor: nur der Titel
  static getConfigElement() {
    return window.hauswachtEditor("hauswacht-test-card");
  }

  static editorSchema(hass, info, lang) {
    const de = lang === "de";
    return {
      schema: [{ name: "title", selector: { text: {} } }],
      labels: { title: de ? "Titel" : "Title" },
      helpers: { title: de ? "Leer = „Hauswacht Test“" : "Empty = “Hauswacht test”" },
    };
  }

  getCardSize() {
    return 8;
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6 };
  }

  set hass(hass) {
    this._hass = hass;
    const ids = this._findEntities();
    const sensors = this._sensors(ids.simulation);
    const signature = [ids.simulation, ids.panel, ids.testMode, ids.sirenTest, ...sensors.map((s) => s.entity_id)].join(",");
    if (!this._built || signature !== this._signature) {
      this._signature = signature;
      this._ids = ids;
      this._build(sensors);
    }
    this._update();
  }

  _t(key) {
    const lang = (this._hass && this._hass.language) || "en";
    return (TEXT[lang.split("-")[0]] || TEXT.en)[key];
  }

  _findEntities() {
    const found = {};
    const registry = (this._hass && this._hass.entities) || {};
    for (const [entityId, entry] of Object.entries(registry)) {
      if (entry.platform !== DOMAIN) continue;
      if (entityId.startsWith("sensor.") && entry.translation_key === "simulation") found.simulation = entityId;
      if (entityId.startsWith("switch.") && entry.translation_key === "test_mode") found.testMode = entityId;
      if (entityId.startsWith("alarm_control_panel.") && !found.panel) found.panel = entityId;
      if (entityId.startsWith("sensor.") && entry.translation_key === "siren_test") found.sirenTest = entityId;
    }
    return found;
  }

  _sensors(entityId) {
    const state = entityId && this._hass.states[entityId];
    const list = state && state.attributes.sensors;
    return Array.isArray(list) ? list : [];
  }

  _kind(sensor) {
    if (sensor.tilt) return "open";
    if (sensor.type === "vibration") return "vibration";
    if (sensor.kind === "lock") return "lock";
    if (sensor.kind === "cover") return "open";
    if (sensor.role === "tamper_24h" || sensor.device_class === "tamper") return "tamper";
    if (MOTION_CLASSES.includes(sensor.device_class)) return "motion";
    if (OPEN_CLASSES.includes(sensor.device_class)) return "open";
    return "other";
  }

  _stateText(sensor, value) {
    if (value === null || value === undefined) return "–";
    const kind = this._kind(sensor);
    const specific = {
      open: "openStates",
      motion: "motionStates",
      tamper: "tamperStates",
      vibration: "vibrationStates",
      lock: "lockStates",
    }[kind];
    const map = (specific && this._t(specific)) || {};
    return map[value] || this._t("states")[value] || value;
  }

  _rawText(sensor) {
    // Schloss- bzw. Torzustand zusätzlich zur Bewertung zeigen
    if (!sensor.raw || !["lock", "cover"].includes(sensor.kind)) return "";
    return ` (${sensor.raw})`;
  }

  _build(sensors) {
    this._built = true;
    this._sirenKey = null;
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    const root = this.shadowRoot;
    root.innerHTML = "";
    const style = document.createElement("style");
    style.textContent = STYLE;
    root.appendChild(style);
    const card = document.createElement("ha-card");
    root.appendChild(card);

    const title = document.createElement("div");
    title.className = "title";
    title.innerHTML = `<ha-icon icon="mdi:test-tube"></ha-icon><span></span>`;
    title.querySelector("span").textContent = this._config.title || this._t("title");
    card.appendChild(title);
    this._phase = document.createElement("div");
    this._phase.className = "phase";
    card.appendChild(this._phase);
    this._rulesBox = document.createElement("div");
    this._rulesBox.className = "rules";
    card.appendChild(this._rulesBox);

    this._rows = [];
    if (!this._ids.simulation) {
      const hint = document.createElement("div");
      hint.className = "hint";
      hint.textContent = this._t("missing");
      card.appendChild(hint);
      this._appendSirens(card);
      return;
    }

    this._hint = document.createElement("div");
    this._hint.className = "hint";
    card.appendChild(this._hint);

    const actions = document.createElement("div");
    actions.className = "actions";
    this._toggle = document.createElement("button");
    this._toggle.className = "primary";
    this._toggle.addEventListener("click", () => {
      if (!this._ids.testMode) return;
      const on = this._testMode();
      this._call("switch", on ? "turn_off" : "turn_on", { entity_id: this._ids.testMode });
    });
    this._reset = document.createElement("button");
    this._reset.textContent = this._t("reset");
    this._reset.addEventListener("click", () =>
      this._call(DOMAIN, "simulate_reset", { entity_id: this._ids.panel })
    );
    // Falscheingaben (PIN/Karte) zurücksetzen – nur Administratoren, sonst Fehlermeldung
    this._codeReset = document.createElement("button");
    this._codeReset.addEventListener("click", () =>
      this._call(DOMAIN, "reset_code_lock", { entity_id: this._ids.panel })
    );
    actions.append(this._toggle, this._reset, this._codeReset);
    card.appendChild(actions);
    // Anwesenheit (ADR 0016): Status je Person, im Testmodus simulieren
    this._presenceBox = document.createElement("div");
    this._presenceBox.className = "presence";
    this._presenceSig = null;
    card.appendChild(this._presenceBox);

    if (!sensors.length) {
      const empty = document.createElement("div");
      empty.className = "hint";
      empty.textContent = this._t("empty");
      card.appendChild(empty);
      this._appendSirens(card);
      return;
    }
    for (const sensor of sensors) card.appendChild(this._row(sensor));
    this._appendSirens(card);
  }

  // --- Sirenentest: echte Sirene, eingeklappt und nur mit Sicherheitsabfrage ---------------

  _appendSirens(card) {
    this._sirenBox = null;
    if (!this._ids.sirenTest) return;
    const box = document.createElement("details");
    box.className = "sirens";
    box.open = Boolean(this._sirenOpen);
    box.addEventListener("toggle", () => {
      this._sirenOpen = box.open;
    });
    const summary = document.createElement("summary");
    summary.textContent = this._t("sirenTitle");
    const body = document.createElement("div");
    box.append(summary, body);
    card.appendChild(box);
    this._sirenBox = body;
    this._sirenAsk = this._sirenAsk || null; // { siren, step: "confirm" | "heard" }
  }

  _sirenInfo() {
    const state = this._ids.sirenTest && this._hass.states[this._ids.sirenTest];
    return (state && state.attributes) || {};
  }

  _updateSirens() {
    const body = this._sirenBox;
    if (!body) return;
    const info = this._sirenInfo();
    const sirens = Array.isArray(info.sirens) ? info.sirens : [];
    const key = JSON.stringify([info, this._sirenAsk]);
    if (key === this._sirenKey) return;
    this._sirenKey = key;
    body.innerHTML = "";
    const warn = document.createElement("div");
    warn.className = "hint on";
    warn.textContent = this._t("sirenWarn");
    body.appendChild(warn);
    if (info.blocked) {
      const blocked = document.createElement("div");
      blocked.className = "hint";
      blocked.textContent = (this._t("sirenBlocked") || {})[info.blocked] || info.blocked;
      body.appendChild(blocked);
    }
    if (!sirens.length) {
      const none = document.createElement("div");
      none.className = "hint";
      none.textContent = this._t("sirenNone");
      body.appendChild(none);
      return;
    }
    for (const unit of sirens) {
      const row = document.createElement("div");
      row.className = "row";
      const text = document.createElement("div");
      text.className = "info";
      const name = document.createElement("div");
      name.className = "name";
      name.textContent = unit.name || unit.entity_id;
      const last = document.createElement("div");
      last.className = "state";
      const mark = unit.heard === true ? " ✅" : unit.heard === false ? " ❌" : "";
      last.textContent = unit.last_test
        ? `${this._t("sirenLast")} ${new Date(unit.last_test).toLocaleString(this._hass.language)}${mark}`
        : this._t("sirenNever");
      text.append(name, last);
      const actions = document.createElement("div");
      actions.className = "seg";
      const ask = this._sirenAsk && this._sirenAsk.siren === unit.entity_id ? this._sirenAsk : null;
      const button = (label, handler, primary) => {
        const b = document.createElement("button");
        b.textContent = label;
        if (primary) b.className = "primary";
        b.addEventListener("click", handler);
        actions.appendChild(b);
        return b;
      };
      if (info.running === unit.entity_id) {
        last.textContent = this._t("sirenRunning");
        button(this._t("sirenStop"), () => this._call(DOMAIN, "siren_test_stop", { entity_id: this._ids.panel }), true);
      } else if (ask && ask.step === "confirm") {
        last.textContent = this._t("sirenConfirm");
        button(this._t("sirenYesStart"), () => {
          this._sirenAsk = { siren: unit.entity_id, step: "heard" };
          this._sirenKey = null;
          this._call(DOMAIN, "siren_test", { entity_id: this._ids.panel, siren: unit.entity_id }, () => {
            this._sirenAsk = null; // abgelehnt (z. B. Testmodus): keine Rückfrage
            this._sirenKey = null;
            this._updateSirens();
          });
        }, true);
        button(this._t("sirenCancel"), () => {
          this._sirenAsk = null;
          this._sirenKey = null;
          this._updateSirens();
        });
      } else if (ask && ask.step === "heard") {
        last.textContent = this._t("sirenHeard");
        const answer = (heard) => () => {
          this._sirenAsk = null;
          this._sirenKey = null;
          this._call(DOMAIN, "siren_test_result", {
            entity_id: this._ids.panel,
            siren: unit.entity_id,
            heard,
          });
        };
        button(this._t("yes"), answer(true), true);
        button(this._t("no"), answer(false));
      } else {
        const start = button(this._t("sirenTest"), () => {
          this._sirenAsk = { siren: unit.entity_id, step: "confirm" };
          this._sirenKey = null;
          this._updateSirens();
        });
        start.disabled = Boolean(info.blocked) || Boolean(this._sirenAsk);
      }
      row.append(text, actions);
      body.appendChild(row);
    }
  }


  _row(sensor) {
    const row = document.createElement("div");
    row.className = "row";
    const icon = document.createElement("ha-icon");
    const kind = this._kind(sensor);
    icon.setAttribute(
      "icon",
      ICONS[sensor.device_class] || ICONS[sensor.kind] || ICONS[kind] || "mdi:checkbox-blank-circle-outline"
    );
    const info = document.createElement("div");
    info.className = "info";
    const name = document.createElement("div");
    name.className = "name";
    name.textContent = sensor.name || sensor.entity_id;
    const state = document.createElement("div");
    state.className = "state";
    const status = document.createElement("div");
    status.className = "status";
    info.append(name, state, status);

    const labels = this._t(kind);
    const seg = document.createElement("div");
    seg.className = "seg";
    const buttons = {};
    const choices = [["on", labels[0]]];
    // Melder mit Kippstellung: dritte Stellung "gekippt"
    if (sensor.tilt) choices.push(["tilted", this._t("tiltLabel")]);
    choices.push(["off", labels[1]], ["unavailable", this._t("gone")], ["real", this._t("real")]);
    for (const [value, label] of choices) {
      const button = document.createElement("button");
      button.textContent = label;
      button.addEventListener("click", () =>
        this._call(DOMAIN, "simulate_state", {
          entity_id: this._ids.panel,
          sensor: sensor.entity_id,
          state: value,
        })
      );
      buttons[value] = button;
      seg.appendChild(button);
    }
    row.append(icon, info, seg);
    this._rows.push({ entityId: sensor.entity_id, row, state, status, buttons });
    return row;
  }

  _updatePhase() {
    if (!this._phase) return;
    const panel = this._ids.panel && this._hass.states[this._ids.panel];
    if (!panel) {
      this._phase.style.display = "none";
      return;
    }
    this._phase.style.display = "";
    const attrs = panel.attributes || {};
    const phase = attrs.phase || panel.state;
    let text = (this._t("phase") || {})[phase] || panel.state;
    if (attrs.profile_name && phase !== "disarmed") text += ` · ${this._t("profile")} ${attrs.profile_name}`;
    const delay = (phase === "pending" || phase === "arming") && attrs.timer_ends_at;
    if (delay) {
      const left = Math.max(0, Math.ceil((Date.parse(attrs.timer_ends_at) - Date.now()) / 1000));
      text += ` · ${left} s`;
    }
    // Ausgangserkennung (ADR 0014): was gerade läuft
    const ex = attrs.exit_detection;
    let exitRunning = false;
    if (ex && ex.mode) {
      const name = (id) => (this._hass.states[id] && this._hass.states[id].attributes.friendly_name) || id;
      const left = ex.until ? Math.max(0, Math.ceil((Date.parse(ex.until) - Date.now()) / 1000)) : null;
      const clock = left === null ? "" : `${Math.floor(left / 60)}:${String(left % 60).padStart(2, "0")}`;
      const e = this._t("exit");
      let line = (ex.mode === "passage" ? e.passage : e.wait).replace("{t}", clock);
      if (ex.persons && ex.persons.length) line += " " + e.watched.replace("{who}", ex.persons.map(name).join(", "));
      const gone = Object.entries(ex.gone || {});
      if (gone.length) {
        line += " " + gone.map(([p, since]) => e.gone.replace("{who}", name(p)).replace("{s}", Math.max(0, Math.round((Date.now() - Date.parse(since)) / 1000)))).join(", ");
      }
      text += `\n${line}`;
      exitRunning = true;
    }
    this._phase.textContent = text;
    this._phase.style.whiteSpace = "pre-line";
    this._phase.classList.toggle("alarm", phase === "triggered" || phase === "alarm_hold");
    this._phase.classList.toggle("delay", Boolean(delay) || exitRunning);
    this._delayRunning = Boolean(delay) || exitRunning;
  }

  _updateRules() {
    if (!this._rulesBox) return false;
    const sim = this._ids.simulation && this._hass.states[this._ids.simulation];
    const rules = (sim && Array.isArray(sim.attributes.rules) && sim.attributes.rules) || [];
    this._rulesBox.style.display = rules.length ? "" : "none";
    this._rulesBox.innerHTML = "";
    if (!rules.length) return false;
    const head = document.createElement("div");
    head.className = "head";
    head.textContent = this._t("rules");
    this._rulesBox.appendChild(head);
    let running = false;
    for (const rule of rules) {
      const row = document.createElement("div");
      row.className = "rule";
      const name = document.createElement("span");
      const area = rule.area ? ` [${rule.area}]` : "";
      name.textContent = `${rule.name}${area} → ${(this._t("ruleResult") || {})[rule.result] || rule.result}`;
      const state = document.createElement("span");
      if (rule.done > 0 && rule.deadline) {
        const left = Math.max(0, Math.ceil((Date.parse(rule.deadline) - Date.now()) / 1000));
        state.textContent =
          this._t("ruleStep").replace("{done}", rule.done).replace("{steps}", rule.steps) + ` · ${left} s`;
        row.classList.add("active");
        running = true;
      } else if (rule.blocked_until) {
        const left = Math.max(0, Math.ceil((Date.parse(rule.blocked_until) - Date.now()) / 1000));
        const mins = Math.floor(left / 60);
        state.textContent = `${this._t("ruleBlocked")} · ${mins}:${String(left % 60).padStart(2, "0")}`;
        running = true;
      } else {
        state.textContent = this._t("ruleIdle");
      }
      row.append(name, state);
      this._rulesBox.appendChild(row);
      if (rule.text) {
        const text = document.createElement("div");
        text.className = "rule-text";
        text.textContent = rule.text;
        this._rulesBox.appendChild(text);
      }
    }
    return running;
  }

  _setTick(needed) {
    // Countdowns jede Sekunde neu zeichnen, solange etwas läuft
    if (needed && !this._tick) {
      this._tick = setInterval(() => this._update(), 1000);
    } else if (!needed && this._tick) {
      clearInterval(this._tick);
      this._tick = null;
    }
  }

  disconnectedCallback() {
    if (this._tick) {
      clearInterval(this._tick);
      this._tick = null;
    }
  }

  _updateCodeReset() {
    if (!this._codeReset) return;
    const panel = this._ids.panel && this._hass.states[this._ids.panel];
    const failures = (panel && panel.attributes.code_failures) || 0;
    const until = panel && panel.attributes.code_locked_until;
    const locked = until && new Date(until) > new Date();
    let text = `${this._t("codeReset")} (${failures})`;
    if (locked) text += ` · ${this._t("codeLocked")}`;
    this._codeReset.textContent = text;
    this._codeReset.disabled = !failures;
  }

  _testMode() {
    const sim = this._ids.simulation && this._hass.states[this._ids.simulation];
    return Boolean(sim && sim.attributes.test_mode);
  }

  // --- Anwesenheit (ADR 0016) ---------------------------------------------------

  _presenceReason(row) {
    const r = row.reason || {};
    const t = this._t("presence");
    const time = (ts) => (ts ? new Date(ts * 1000).toLocaleTimeString(this._hass.language || "de", { hour: "2-digit", minute: "2-digit" }) : "");
    if (r.kind === "simulated") return t.reasonSim;
    if (r.kind === "home") return t.reasonHome.replace("{by}", (r.by || []).join(", ") || "–");
    if (r.kind === "away") return (t.proofs[r.proof] || t.proofs.other) + (r.at ? ` (${time(r.at)})` : "");
    if (r.kind === "no_proof") return t.reasonNoProof;
    if (r.kind === "entity") return t.reasonEntity.replace("{s}", r.state ?? "–");
    if (r.kind === "unclear") return t.reasonUnclear.replace("{by}", (r.by || []).join(", ") || "–");
    return "";
  }

  _updatePresence(testMode) {
    const box = this._presenceBox;
    if (!box) return;
    const sim = this._ids.simulation && this._hass.states[this._ids.simulation];
    const data = sim && sim.attributes.presence;
    const persons = data && data.persons ? Object.entries(data.persons) : [];
    const profiles = (data && data.profiles) || [];
    // Sekundentakt nur, wenn ein Countdown läuft – sonst nicht ständig neu zeichnen
    const ticking = profiles.some((p) => p.due || (p["return"] && (p["return"].arrival_until || p["return"].door_until)));
    const signature = JSON.stringify([testMode, persons, profiles, ticking ? Math.floor(Date.now() / 1000) : 0]);
    if (signature === this._presenceSig) return ticking;
    this._presenceSig = signature;
    const t = this._t("presence");
    if (!persons.length && !profiles.length) {
      box.innerHTML = "";
      return false;
    }
    const esc = (v) => String(v ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
    const buttons = ["home", "away", "away_no_proof", "approaching", "real"];
    const rows = persons
      .map(([id, row]) => {
        const approach = row.approach_at ? ` · ${t.approaching}` : "";
        const current = row.simulated || "real";
        const btns = buttons
          .map((b) => `<button data-person="${esc(id)}" data-state="${b}" class="${testMode && current === b ? "active" : ""}" ${testMode ? "" : "disabled"}>${esc(t.buttons[b])}</button>`)
          .join("");
        return `<div class="row ${row.simulated ? "sim" : ""}"><ha-icon icon="${row.state === "home" ? "mdi:home-account" : row.state === "away" ? "mdi:account-arrow-right" : "mdi:account-question"}"></ha-icon>
          <div class="info"><div class="name">${esc(row.name)}: <b>${esc(t.states[row.state])}</b>${esc(approach)}</div>
          <div class="state">${esc(this._presenceReason(row))}</div></div>
          <div class="btns">${btns}</div></div>`;
      })
      .join("");
    const now = Date.now() / 1000;
    const plan = profiles
      .map((p) => `<div class="rule"><span><b>${esc(p.name)}</b> – ${esc(hauswachtProfileLine(p, t.line, now))}</span></div>`)
      .join("");
    const anyDue = profiles.some((p) => p.due);
    box.innerHTML = `<div class="rules"><div class="head">${esc(t.title)}</div>${plan}
      ${anyDue ? `<button class="skip" ${testMode ? "" : "disabled"}>${esc(t.skip)}</button>` : ""}</div>${rows}`;
    box.querySelectorAll("button[data-person]").forEach((btn) =>
      btn.addEventListener("click", () =>
        this._call(DOMAIN, "simulate_presence", { entity_id: this._ids.panel, person: btn.dataset.person, state: btn.dataset.state })
      )
    );
    box.querySelector("button.skip")?.addEventListener("click", () => this._call(DOMAIN, "skip_wait", { entity_id: this._ids.panel }));
    return ticking;
  }

  _call(domain, service, data, onError) {
    this._hass.callService(domain, service, data).catch((err) => {
      if (onError) onError();
      this.dispatchEvent(
        new CustomEvent("hass-notification", {
          detail: { message: (err && err.message) || String(err) },
          bubbles: true,
          composed: true,
        })
      );
    });
  }

  _update() {
    if (!this._hass || !this._ids) return;
    this._updatePhase();
    this._updateSirens();
    if (!this._hint) return;
    const testMode = this._testMode();
    this._hint.textContent = testMode ? this._t("testOn") : this._t("testOff");
    this._hint.classList.toggle("on", testMode);
    this._toggle.textContent = testMode ? this._t("disable") : this._t("enable");
    this._toggle.disabled = !this._ids.testMode;
    this._reset.disabled = !testMode;
    this._updateCodeReset();
    const presenceTicking = this._updatePresence(testMode);

    let waiting = this._updateRules();
    const byId = {};
    for (const sensor of this._sensors(this._ids.simulation)) byId[sensor.entity_id] = sensor;
    for (const item of this._rows) {
      const sensor = byId[item.entityId];
      if (!sensor) continue;
      const simulated = sensor.simulated;
      const isSim = simulated !== null && simulated !== undefined;
      item.row.classList.toggle("sim", isSim);
      item.state.textContent = isSim
        ? `${this._t("simulated")}: ${this._stateText(sensor, simulated)} · ${this._t("realValue")}: ${this._stateText(sensor, sensor.real)}`
        : this._stateText(sensor, sensor.real) + this._rawText(sensor);
      let statusText = (this._t("status") || {})[sensor.status] || "";
      if (sensor.status === "in_rule" && Array.isArray(sensor.rules)) {
        statusText += " " + sensor.rules.join(", ");
      }
      if (sensor.exit_inside && sensor.status !== "exit_inside") {
        statusText = statusText ? `${statusText} · ${this._t("exitInsideToo")}` : this._t("exitInsideToo");
      }
      if (statusText && sensor.area) statusText += ` [${sensor.area}]`;
      item.status.textContent = statusText;
      item.status.style.display = statusText ? "" : "none";
      item.status.className =
        "status" +
        (["bypassed_until_closed", "bypassed", "tamper_alarm", "always_active"].includes(sensor.status) ? " warn" : "") +
        (["not_monitored", "tamper_message"].includes(sensor.status) ? " muted" : "");
      for (const [value, button] of Object.entries(item.buttons)) {
        button.disabled = !testMode || !this._ids.panel;
        button.classList.toggle("active", testMode && (isSim ? value === simulated : value === "real"));
      }
    }
    this._setTick(this._delayRunning || waiting || presenceTicking);
  }
}

if (!customElements.get("hauswacht-test-card")) {
  customElements.define("hauswacht-test-card", HauswachtTestCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "hauswacht-test-card",
    name: "Hauswacht Test",
    description: "Sensoren der Hauswacht im Testmodus simulieren (Tür auf/zu, Bewegung, Manipulation …)",
    preview: false,
    documentationURL: "https://github.com/schlusenbaum/hauswacht/blob/main/docs/testmodus.md",
  });
}
