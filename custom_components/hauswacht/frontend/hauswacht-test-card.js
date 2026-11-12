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

const TEXT = {
  de: {
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
    tamper: ["Manipulation", "OK"],
    other: ["Ein", "Aus"],
    states: { on: "ein", off: "aus", unavailable: "nicht verfügbar", unknown: "unbekannt" },
    openStates: { on: "offen", off: "zu" },
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
      bypassed: "überbrückt",
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
    rules: "Auslöseregeln im aktiven Profil",
    ruleIdle: "nicht begonnen",
    ruleStep: "Schritt {done} von {steps} erfüllt",
    ruleResult: { alarm: "sofort Alarm", entry_delay: "Eingangsverzögerung", notify: "nur Benachrichtigung" },
    ruleBlocked: "gesperrt durch Ausnahme",
  },
  en: {
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
    tamper: ["Tamper", "OK"],
    other: ["On", "Off"],
    states: { on: "on", off: "off", unavailable: "unavailable", unknown: "unknown" },
    openStates: { on: "open", off: "closed" },
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
      bypassed: "bypassed",
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
    rules: "Trigger rules in the active profile",
    ruleIdle: "not started",
    ruleStep: "step {done} of {steps} fulfilled",
    ruleResult: { alarm: "alarm immediately", entry_delay: "entry delay", notify: "notification only" },
    ruleBlocked: "blocked by exception",
  },
};

const OPEN_CLASSES = ["door", "window", "opening", "garage_door"];
const MOTION_CLASSES = ["motion", "occupancy", "presence", "moving", "vibration"];

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
    for (const [value, label] of [
      ["on", labels[0]],
      ["off", labels[1]],
      ["unavailable", this._t("gone")],
      ["real", this._t("real")],
    ]) {
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
    this._phase.textContent = text;
    this._phase.classList.toggle("alarm", phase === "triggered" || phase === "alarm_hold");
    this._phase.classList.toggle("delay", Boolean(delay));
    this._delayRunning = Boolean(delay);
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
    this._setTick(this._delayRunning || waiting);
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
