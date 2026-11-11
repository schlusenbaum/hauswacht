/*
 * Hauswacht Test – Dashboard-Karte zum Simulieren der Hauswacht-Sensoren.
 *
 * Wird von der Integration Hauswacht automatisch geladen. Zeigt alle Sensoren aus den
 * Hauswacht-Zonen mit Knöpfen "Auf/Zu", "Bewegung/Ruhe", "Manipulation/OK",
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
    missing: "Hauswacht-Testsensor nicht gefunden (Hauswacht 0.17.1 oder neuer nötig).",
    empty: "Keine Sensoren in den Hauswacht-Zonen.",
    real: "Echt",
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
    status: {
      disarmed: "",
      monitored: "überwacht",
      in_rule: "nur in Auslöseregeln:",
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
    ruleResult: { alarm: "sofort Alarm", entry_delay: "Eingangsverzögerung" },
  },
  en: {
    title: "Test",
    testOff: "Simulation only works in test mode. In test mode no siren sounds and notifications carry \"[TEST]\".",
    testOn: "Test mode on – no sirens. Simulated for Hauswacht only; devices and other automations notice nothing.",
    enable: "Turn on test mode",
    disable: "Turn off test mode",
    reset: "All real",
    missing: "Hauswacht test sensor not found (Hauswacht 0.17.1 or newer required).",
    empty: "No sensors in the Hauswacht zones.",
    real: "Real",
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
    status: {
      disarmed: "",
      monitored: "monitored",
      in_rule: "only in trigger rules:",
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
    ruleResult: { alarm: "alarm immediately", entry_delay: "entry delay" },
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
    const signature = [ids.simulation, ids.panel, ids.testMode, ...sensors.map((s) => s.entity_id)].join(",");
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
      if (entityId.startsWith("alarm_control_panel.")) found.panel = entityId;
    }
    return found;
  }

  _sensors(entityId) {
    const state = entityId && this._hass.states[entityId];
    const list = state && state.attributes.sensors;
    return Array.isArray(list) ? list : [];
  }

  _kind(sensor) {
    if (sensor.role === "tamper_24h" || sensor.device_class === "tamper") return "tamper";
    if (MOTION_CLASSES.includes(sensor.device_class)) return "motion";
    if (OPEN_CLASSES.includes(sensor.device_class)) return "open";
    return "other";
  }

  _stateText(sensor, value) {
    if (value === null || value === undefined) return "–";
    const kind = this._kind(sensor);
    const specific = { open: "openStates", motion: "motionStates", tamper: "tamperStates" }[kind];
    const map = (specific && this._t(specific)) || {};
    return map[value] || this._t("states")[value] || value;
  }

  _build(sensors) {
    this._built = true;
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
    actions.append(this._toggle, this._reset);
    card.appendChild(actions);

    if (!sensors.length) {
      const empty = document.createElement("div");
      empty.className = "hint";
      empty.textContent = this._t("empty");
      card.appendChild(empty);
      return;
    }
    for (const sensor of sensors) card.appendChild(this._row(sensor));
  }

  _row(sensor) {
    const row = document.createElement("div");
    row.className = "row";
    const icon = document.createElement("ha-icon");
    const kind = this._kind(sensor);
    icon.setAttribute("icon", ICONS[sensor.device_class] || ICONS[kind] || "mdi:checkbox-blank-circle-outline");
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
      name.textContent = `${rule.name} → ${(this._t("ruleResult") || {})[rule.result] || rule.result}`;
      const state = document.createElement("span");
      if (rule.done > 0 && rule.deadline) {
        const left = Math.max(0, Math.ceil((Date.parse(rule.deadline) - Date.now()) / 1000));
        state.textContent =
          this._t("ruleStep").replace("{done}", rule.done).replace("{steps}", rule.steps) + ` · ${left} s`;
        row.classList.add("active");
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

  _testMode() {
    const sim = this._ids.simulation && this._hass.states[this._ids.simulation];
    return Boolean(sim && sim.attributes.test_mode);
  }

  _call(domain, service, data) {
    this._hass.callService(domain, service, data).catch((err) => {
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
    if (!this._hint) return;
    const testMode = this._testMode();
    this._hint.textContent = testMode ? this._t("testOn") : this._t("testOff");
    this._hint.classList.toggle("on", testMode);
    this._toggle.textContent = testMode ? this._t("disable") : this._t("enable");
    this._toggle.disabled = !this._ids.testMode;
    this._reset.disabled = !testMode;

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
        : this._stateText(sensor, sensor.real);
      let statusText = (this._t("status") || {})[sensor.status] || "";
      if (sensor.status === "in_rule" && Array.isArray(sensor.rules)) {
        statusText += " " + sensor.rules.join(", ");
      }
      item.status.textContent = statusText;
      item.status.style.display = statusText ? "" : "none";
      item.status.className =
        "status" +
        (["bypassed_until_closed", "bypassed", "tamper_alarm"].includes(sensor.status) ? " warn" : "") +
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
    documentationURL: "https://github.com/schlusenbaum/hauswacht/blob/main/docs/dashboard.md",
  });
}
