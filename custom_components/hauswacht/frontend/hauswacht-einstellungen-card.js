/*
 * Hauswacht Einstellungen – Dashboard-Karte für die Profil-Einstellungen.
 *
 * Wird von der Integration Hauswacht automatisch geladen (kein Eintrag unter
 * "Ressourcen" nötig). Die Karte findet die Einstellungs-Entitäten selbst über
 * ihre Plattform (hauswacht) und ihren Übersetzungsschlüssel – Umbenennen der
 * Entitäten schadet also nicht.
 *
 * Konfiguration (alles optional):
 *   type: custom:hauswacht-einstellungen-card
 *   title: Einstellungen
 */

const DOMAIN = "hauswacht";

const TEXT = {
  de: {
    title: "Einstellungen",
    profile: "Profil bearbeiten",
    times: "Zeiten",
    alarm: "Alarm",
    arming: "Beim Scharfschalten",
    automation: "Automatik",
    locked: "Nur im unscharfen Zustand änderbar.",
    more: "Zonen, Sirenen, Namen und Wochentage: Einstellungen → Geräte & Dienste → Hauswacht → Konfigurieren.",
    missing: "Keine Hauswacht-Einstellungen gefunden (Hauswacht 0.14.0 oder neuer nötig).",
    off: "aus",
  },
  en: {
    title: "Settings",
    profile: "Edit profile",
    times: "Times",
    alarm: "Alarm",
    arming: "When arming",
    automation: "Automation",
    locked: "Can only be changed while disarmed.",
    more: "Zones, sirens, names and weekdays: Settings → Devices & services → Hauswacht → Configure.",
    missing: "No Hauswacht settings found (Hauswacht 0.14.0 or newer required).",
    off: "off",
  },
};

// Gruppen und Reihenfolge; Schlüssel = translation_key der Entitäten
const GROUPS = [
  { title: "times", keys: ["setting_exit_delay", "setting_entry_delay", "setting_reaction_time", "setting_max_alarm_cycles"] },
  { title: "alarm", keys: ["setting_silent", "setting_tamper_triggers_alarm", "setting_siren_tone", "setting_siren_volume"] },
  { title: "arming", keys: ["setting_open_policy", "setting_unavailable_policy"] },
  { title: "automation", keys: ["setting_auto_arm_time", "setting_auto_disarm_time", "setting_auto_away_delay", "setting_auto_disarm_on_arrival"] },
];

const STYLE = `
  ha-card { padding: 16px; }
  .title { font-size: 1.2em; font-weight: 500; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
  .hint { color: var(--secondary-text-color); font-size: 0.9em; margin: 4px 0 8px; }
  .locked { color: var(--warning-color); }
  .group { margin-top: 16px; }
  .group-title { color: var(--secondary-text-color); font-size: 0.85em; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 4px; }
  .row { display: flex; align-items: center; justify-content: space-between; gap: 12px; min-height: 44px; border-bottom: 1px solid var(--divider-color); }
  .row:last-child { border-bottom: none; }
  .label { display: flex; align-items: center; gap: 10px; flex: 1; min-width: 0; }
  .label ha-icon { color: var(--state-icon-color, var(--secondary-text-color)); flex: none; }
  .label span { overflow: hidden; text-overflow: ellipsis; }
  .control { display: flex; align-items: center; gap: 6px; flex: none; }
  select, input[type=time] {
    font: inherit; color: var(--primary-text-color); background: var(--secondary-background-color, transparent);
    border: 1px solid var(--divider-color); border-radius: 8px; padding: 6px 8px; max-width: 200px;
  }
  button.step {
    width: 32px; height: 32px; border-radius: 50%; border: 1px solid var(--divider-color);
    background: none; color: var(--primary-text-color); font-size: 1.1em; cursor: pointer;
  }
  button.step:disabled { opacity: 0.4; cursor: default; }
  .value { min-width: 64px; text-align: center; }
  .switch { width: 44px; height: 24px; position: relative; display: inline-block; }
  .switch input { opacity: 0; width: 0; height: 0; }
  .slider { position: absolute; inset: 0; background: var(--disabled-color, #bdbdbd); border-radius: 12px; transition: .2s; cursor: pointer; }
  .slider:before { content: ""; position: absolute; width: 18px; height: 18px; left: 3px; top: 3px; background: white; border-radius: 50%; transition: .2s; }
  .switch input:checked + .slider { background: var(--primary-color); }
  .switch input:checked + .slider:before { transform: translateX(20px); }
  .switch input:disabled + .slider { opacity: 0.5; cursor: default; }
  .disabled { opacity: 0.6; }
`;

class HauswachtEinstellungenCard extends HTMLElement {
  setConfig(config) {
    this._config = config || {};
    this._built = false;
  }

  static getStubConfig() {
    return {};
  }

  getCardSize() {
    return 10;
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6 };
  }

  set hass(hass) {
    this._hass = hass;
    const entities = this._findEntities();
    const signature = Object.keys(entities).sort().join(",");
    if (!this._built || signature !== this._signature) {
      this._signature = signature;
      this._entities = entities;
      this._build();
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
      if (entry.platform !== DOMAIN || !entry.translation_key) continue;
      found[entry.translation_key] = entityId;
    }
    return found;
  }

  _name(entityId) {
    // Anzeigename ohne Gerätenamen ("Hauswacht Eingangsverzögerung" -> "Eingangsverzögerung").
    // Bewusst ohne hass.formatEntityName: dessen Aufruf hat sich zwischen Versionen geändert.
    const state = this._hass.states[entityId];
    const name = (state && state.attributes.friendly_name) || entityId;
    const entry = (this._hass.entities || {})[entityId];
    const device = entry && entry.device_id && (this._hass.devices || {})[entry.device_id];
    const prefix = device && (device.name_by_user || device.name);
    if (prefix && name.startsWith(prefix + " ")) return name.slice(prefix.length + 1);
    return name.replace(/^Hauswacht\s+/, "");
  }

  _optionLabel(state, option) {
    if (typeof this._hass.formatEntityState === "function") {
      try {
        return this._hass.formatEntityState(state, option);
      } catch (e) {
        /* Rohwert */
      }
    }
    return option;
  }

  _build() {
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
    title.innerHTML = `<ha-icon icon="mdi:tune-variant"></ha-icon><span></span>`;
    title.querySelector("span").textContent = this._config.title || this._t("title");
    card.appendChild(title);

    if (!this._entities.edit_profile) {
      const hint = document.createElement("div");
      hint.className = "hint";
      hint.textContent = this._t("missing");
      card.appendChild(hint);
      this._rows = [];
      return;
    }

    this._lockHint = document.createElement("div");
    this._lockHint.className = "hint locked";
    this._lockHint.textContent = this._t("locked");
    card.appendChild(this._lockHint);

    this._rows = [];
    card.appendChild(this._row("edit_profile"));
    for (const group of GROUPS) {
      const keys = group.keys.filter((k) => this._entities[k]);
      if (!keys.length) continue;
      const box = document.createElement("div");
      box.className = "group";
      const head = document.createElement("div");
      head.className = "group-title";
      head.textContent = this._t(group.title);
      box.appendChild(head);
      for (const key of keys) box.appendChild(this._row(key));
      card.appendChild(box);
    }

    const more = document.createElement("div");
    more.className = "hint";
    more.style.marginTop = "12px";
    more.textContent = this._t("more");
    card.appendChild(more);
  }

  _row(key) {
    const entityId = this._entities[key];
    const domain = entityId.split(".")[0];
    const row = document.createElement("div");
    row.className = "row";
    const label = document.createElement("div");
    label.className = "label";
    const icon = document.createElement("ha-icon");
    label.appendChild(icon);
    const text = document.createElement("span");
    label.appendChild(text);
    row.appendChild(label);
    const control = document.createElement("div");
    control.className = "control";
    row.appendChild(control);

    const item = { key, entityId, domain, row, icon, text, control };
    if (domain === "number") {
      item.minus = this._stepButton("−", () => this._step(item, -1));
      item.value = document.createElement("span");
      item.value.className = "value";
      item.plus = this._stepButton("+", () => this._step(item, 1));
      control.append(item.minus, item.value, item.plus);
    } else if (domain === "select") {
      item.select = document.createElement("select");
      item.select.addEventListener("change", () =>
        this._call("select", "select_option", entityId, { option: item.select.value })
      );
      control.appendChild(item.select);
    } else if (domain === "switch") {
      const wrap = document.createElement("label");
      wrap.className = "switch";
      item.input = document.createElement("input");
      item.input.type = "checkbox";
      item.input.addEventListener("change", () =>
        this._call("switch", item.input.checked ? "turn_on" : "turn_off", entityId)
      );
      const slider = document.createElement("span");
      slider.className = "slider";
      wrap.append(item.input, slider);
      control.appendChild(wrap);
    } else if (domain === "time") {
      item.input = document.createElement("input");
      item.input.type = "time";
      item.input.addEventListener("change", () => {
        if (item.input.value) {
          this._call("time", "set_value", entityId, { time: `${item.input.value}:00` });
        }
      });
      control.appendChild(item.input);
    }
    this._rows.push(item);
    return row;
  }

  _stepButton(label, handler) {
    const button = document.createElement("button");
    button.className = "step";
    button.textContent = label;
    button.addEventListener("click", handler);
    return button;
  }

  _step(item, direction) {
    const state = this._hass.states[item.entityId];
    if (!state) return;
    const step = Number(state.attributes.step) || 1;
    const min = Number(state.attributes.min);
    const max = Number(state.attributes.max);
    let value = Number(state.state) + direction * step;
    if (!Number.isNaN(min)) value = Math.max(min, value);
    if (!Number.isNaN(max)) value = Math.min(max, value);
    this._call("number", "set_value", item.entityId, { value });
  }

  _call(domain, service, entityId, data = {}) {
    this._hass.callService(domain, service, { entity_id: entityId, ...data }).catch((err) => {
      // Fehlermeldung von Home Assistant anzeigen (z. B. "nur im unscharfen Zustand")
      this.dispatchEvent(
        new CustomEvent("hass-notification", {
          detail: { message: (err && err.message) || String(err) },
          bubbles: true,
          composed: true,
        })
      );
      this._update();
    });
  }

  _update() {
    if (!this._rows || !this._hass) return;
    let anyUnavailable = false;
    for (const item of this._rows) {
      const state = this._hass.states[item.entityId];
      const unavailable = !state || state.state === "unavailable";
      if (unavailable && item.key !== "edit_profile") anyUnavailable = true;
      item.row.classList.toggle("disabled", unavailable);
      item.text.textContent = this._name(item.entityId);
      item.icon.setAttribute("icon", (state && state.attributes.icon) || "mdi:cog-outline");
      if (!state) continue;
      if (item.domain === "number") {
        const unit = state.attributes.unit_of_measurement;
        item.value.textContent = unavailable ? "–" : `${state.state}${unit ? " " + unit : ""}`;
        item.minus.disabled = unavailable;
        item.plus.disabled = unavailable;
      } else if (item.domain === "select") {
        const options = state.attributes.options || [];
        if (item.select.dataset.options !== options.join("|")) {
          item.select.dataset.options = options.join("|");
          item.select.innerHTML = "";
          for (const option of options) {
            const el = document.createElement("option");
            el.value = option;
            el.textContent = this._optionLabel(state, option);
            item.select.appendChild(el);
          }
        }
        if (this.shadowRoot.activeElement !== item.select) item.select.value = state.state;
        item.select.disabled = unavailable;
      } else if (item.domain === "switch") {
        item.input.checked = state.state === "on";
        item.input.disabled = unavailable;
      } else if (item.domain === "time") {
        const value = /^\d{2}:\d{2}/.test(state.state) ? state.state.slice(0, 5) : "";
        if (this.shadowRoot.activeElement !== item.input) item.input.value = value;
        item.input.disabled = unavailable;
      }
    }
    if (this._lockHint) this._lockHint.style.display = anyUnavailable ? "" : "none";
  }
}

if (!customElements.get("hauswacht-einstellungen-card")) {
  customElements.define("hauswacht-einstellungen-card", HauswachtEinstellungenCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "hauswacht-einstellungen-card",
    name: "Hauswacht Einstellungen",
    description: "Profil-Einstellungen der Hauswacht (Verzögerungen, stiller Alarm, Uhrzeiten …)",
    preview: false,
    documentationURL: "https://github.com/schlusenbaum/hauswacht/blob/main/docs/dashboard.md",
  });
}
