/*
 * Visueller Editor für alle Hauswacht-Karten.
 *
 * Jede Karte liefert über `static getConfigElement()` dieses Element und beschreibt ihre
 * Felder mit `static editorSchema(hass, info, lang, config)` (Schema für ha-form, wie die eingebauten
 * Karten). Optional: `editorToForm(config)` / `editorFromForm(data)` zum Umrechnen (z. B.
 * Farben als #rrggbb in der Konfiguration, als [r, g, b] im Farbwähler).
 *
 * Wird von der Integration automatisch geladen.
 */

(() => {
  if (customElements.get("hauswacht-card-editor")) return;

  // ha-form ist nicht immer schon geladen: über eine Standardkarte nachladen
  let formReady = null;
  const ensureForm = () => {
    if (customElements.get("ha-form")) return Promise.resolve();
    if (!formReady) {
      formReady = (async () => {
        try {
          const helpers = await window.loadCardHelpers();
          const card = await helpers.createCardElement({ type: "entities", entities: [] });
          if (card && card.constructor.getConfigElement) await card.constructor.getConfigElement();
        } catch (err) {
          /* ha-form kommt dann mit dem Editor-Dialog */
        }
        await customElements.whenDefined("ha-form");
      })();
    }
    return formReady;
  };

  class HauswachtCardEditor extends HTMLElement {
    constructor() {
      super();
      this._config = {};
      this._info = null;
    }

    set cardTag(tag) {
      this._tag = tag;
    }

    setConfig(config) {
      this._config = { ...(config || {}) };
      this._render();
    }

    set hass(hass) {
      const first = !this._hass;
      this._hass = hass;
      if (this._form) this._form.hass = hass;
      if (first) this._load();
    }

    get _card() {
      return customElements.get(this._tag);
    }

    _lang() {
      return ((this._hass && this._hass.language) || "en").startsWith("de") ? "de" : "en";
    }

    async _load() {
      await ensureForm();
      const card = this._card;
      if (card && card.editorNeedsInfo) {
        try {
          this._info = await this._hass.callWS({ type: "hauswacht/alarm/info" });
        } catch (err) {
          this._info = null;
        }
      }
      this._render();
    }

    _render() {
      const card = this._card;
      if (!this._hass || !card || !customElements.get("ha-form")) return;
      const lang = this._lang();
      const { schema, labels, helpers } = card.editorSchema(this._hass, this._info, lang, this._config);
      if (!this._form) {
        this._form = document.createElement("ha-form");
        this._form.addEventListener("value-changed", (ev) => this._changed(ev.detail.value));
        this.appendChild(this._form);
      }
      this._form.hass = this._hass;
      this._form.schema = schema;
      this._form.data = card.editorToForm ? card.editorToForm(this._config) : this._config;
      this._form.computeLabel = (field) => (labels && labels[field.name]) || field.name;
      this._form.computeHelper = (field) => (helpers && helpers[field.name]) || undefined;
    }

    _changed(data) {
      const card = this._card;
      const next = card.editorFromForm ? card.editorFromForm(data, this._config) : { ...data };
      // Leere Werte und Standardwerte nicht in die YAML-Konfiguration schreiben
      for (const [key, value] of Object.entries(next)) {
        if (value === undefined || value === null || value === "" || (Array.isArray(value) && !value.length)) {
          delete next[key];
        }
      }
      const defaults = (card.editorDefaults && card.editorDefaults()) || {};
      for (const [key, value] of Object.entries(defaults)) {
        if (next[key] === value) delete next[key];
      }
      this._config = { type: this._config.type, ...next };
      this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this._config }, bubbles: true, composed: true }));
    }
  }

  customElements.define("hauswacht-card-editor", HauswachtCardEditor);

  window.hauswachtEditor = (tag) => {
    const el = document.createElement("hauswacht-card-editor");
    el.cardTag = tag;
    return el;
  };
})();
