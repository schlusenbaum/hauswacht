/*
 * Hauswacht Alarm – scharf und unscharf schalten, ohne PIN-Zwang.
 *
 * Die Karte schaltet über Hauswacht selbst (WebSocket hauswacht/alarm/*). Ausweis ist das
 * angemeldete Home-Assistant-Konto: Ist es einem Hauswacht-Benutzer zugeordnet, gelten dessen
 * Rechte – ein PIN wird nur verlangt, wo es eingestellt ist (z. B. für ein Wandtablet).
 *
 *   type: custom:hauswacht-alarm-card
 *   title: Alarm                # optional
 *   bereich: garage             # optional: nur dieser Bereich (Kennung oder Name)
 *   groesse: kompakt            # gross (Standard) | kompakt
 *   profile: [night, away]      # optional: nur diese Profilknöpfe, in dieser Reihenfolge
 *   spalten: 2                  # optional: Knöpfe je Zeile (1–4), sonst automatisch
 *   zeige_zuletzt: false        # zeige_offen, zeige_nicht_erreichbar, zeige_testmodus,
 *                               # zeige_balken, zeige_alle_unscharf, blinken (Standard an)
 *   farbe_scharf: "#1565c0"     # farbe_unscharf, farbe_verzoegerung, farbe_alarm
 *   rueckfrage_scharf: true     # rueckfrage_unscharf (Standard aus)
 *
 * Alles lässt sich auch im visuellen Editor einstellen.
 *
 * Wird von der Integration automatisch geladen.
 */

const TEXT = {
  de: {
    disarmed: "Unscharf",
    arming: "Wird scharf",
    armed: "Scharf",
    pending: "Eingangsverzögerung",
    triggered: "Alarm",
    hold: "Alarm (gehalten)",
    unavailable: "Nicht verfügbar",
    disarm: "Unscharf schalten",
    endAlarm: "Alarm beenden",
    disarmAll: "Alle Bereiche unscharf",
    lastBy: "Zuletzt",
    open: "Offen",
    unavailableSensors: "Nicht erreichbar",
    testMode: "Testmodus – Sirenen gesperrt, nichts wird wirklich gemeldet",
    trigger: "Ausgelöst durch",
    enterPin: "PIN eingeben",
    cancel: "Abbrechen",
    ok: "OK",
    clear: "Letzte Ziffer löschen",
    force: "Trotzdem scharf schalten",
    locked: "Gesperrt bis",
    noAreas: "Dieses Konto darf die Alarmanlage nicht bedienen.",
    notLoaded: "Hauswacht ist nicht geladen.",
    loading: "Lade …",
    noProfiles: "Keine Alarmprofile angelegt.",
    notAllowed: "nicht erlaubt",
    done: { arm: "Wird scharf geschaltet", disarm: "Unscharf geschaltet", end_alarm: "Alarm beendet" },
    askArm: "{p} scharf schalten?",
    askDisarm: "Wirklich unscharf schalten?",
    doArm: "Scharf schalten",
  },
  en: {
    disarmed: "Disarmed",
    arming: "Arming",
    armed: "Armed",
    pending: "Entry delay",
    triggered: "Alarm",
    hold: "Alarm (held)",
    unavailable: "Unavailable",
    disarm: "Disarm",
    endAlarm: "End alarm",
    disarmAll: "Disarm all areas",
    lastBy: "Last",
    open: "Open",
    unavailableSensors: "Unreachable",
    testMode: "Test mode – sirens locked, nothing is really reported",
    trigger: "Triggered by",
    enterPin: "Enter PIN",
    cancel: "Cancel",
    ok: "OK",
    clear: "Delete last digit",
    force: "Arm anyway",
    locked: "Locked until",
    noAreas: "This account may not operate the alarm system.",
    notLoaded: "Hauswacht is not loaded.",
    loading: "Loading …",
    noProfiles: "No alarm profiles yet.",
    notAllowed: "not allowed",
    done: { arm: "Arming", disarm: "Disarmed", end_alarm: "Alarm ended" },
    askArm: "Arm {p}?",
    askDisarm: "Really disarm?",
    doArm: "Arm",
  },
};

const ICONS = {
  disarmed: "mdi:shield-off-outline",
  arming: "mdi:shield-sync-outline",
  armed: "mdi:shield-lock",
  pending: "mdi:shield-alert-outline",
  triggered: "mdi:alarm-light",
  unavailable: "mdi:shield-remove-outline",
};

const STYLE = `
  /* Eigene Farben statt der Zustandsfarben von Home Assistant (dort ist z. B. "scharf" grün).
     Anpassbar im Theme über --hauswacht-*-color. */
  :host {
    --hw-ok: var(--hauswacht-disarmed-color, #2e7d32);
    --hw-armed: var(--hauswacht-armed-color, #b71c1c);
    --hw-wait: var(--hauswacht-pending-color, #e65100);
    --hw-alarm: var(--hauswacht-alarm-color, #d50000);
    --hw-off: var(--disabled-color, #9e9e9e);
  }
  ha-card { overflow: hidden; }
  .root { display: contents; }
  .title { padding: 16px 20px 0; font-size: 1.25rem; font-weight: 500; }
  .area + .area { border-top: 1px solid var(--divider-color); }
  .band {
    --c: var(--hw-ok);
    position: relative; display: flex; align-items: center; gap: 18px;
    padding: 22px 20px; color: #fff; background: var(--c);
  }
  .band.arming, .band.pending { --c: var(--hw-wait); }
  .band.armed { --c: var(--hw-armed); }
  .band.triggered { --c: var(--hw-alarm); animation: pulse 1.6s ease-in-out infinite; }
  .band.unavailable { --c: var(--hw-off); }
  @keyframes pulse { 50% { filter: brightness(1.25); } }
  @media (prefers-reduced-motion: reduce) { .band.triggered { animation: none; } }
  .no-pulse .band.triggered { animation: none; }
  .band ha-icon { --mdc-icon-size: 56px; flex: none; }
  .state { min-width: 0; flex: 1; }
  .word { font-size: 2.1rem; line-height: 1.1; font-weight: 600; letter-spacing: -0.01em; }
  .profile { font-weight: 400; opacity: 0.92; }
  .sub { margin-top: 4px; font-size: 0.95rem; opacity: 0.9; }
  .clock { font-size: 2.6rem; font-weight: 300; font-variant-numeric: tabular-nums; flex: none; }
  .drain { position: absolute; left: 0; bottom: 0; height: 5px; background: rgba(255,255,255,0.75); transition: width 1s linear; }
  .notes { padding: 10px 20px 0; display: grid; gap: 6px; font-size: 0.95rem; }
  .note { display: flex; gap: 8px; align-items: flex-start; }
  .note ha-icon { --mdc-icon-size: 20px; color: var(--warning-color, #ff9800); flex: none; }
  .note.info ha-icon { color: var(--info-color, #039be5); }
  .note b { font-weight: 500; }
  .actions { padding: 16px 20px 20px; display: grid; gap: 10px; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); }
  button.act {
    font: inherit; font-size: 1.1rem; font-weight: 500; min-height: 72px; padding: 10px 14px;
    display: flex; align-items: center; gap: 12px; text-align: left; cursor: pointer;
    color: var(--primary-text-color); background: var(--secondary-background-color, #f5f5f5);
    border: 1px solid var(--divider-color); border-radius: 14px;
  }
  button.act ha-icon { --mdc-icon-size: 30px; color: var(--hw-armed); flex: none; }
  button.act.wide { grid-column: 1 / -1; justify-content: center; min-height: 84px; font-size: 1.3rem; }
  button.act.go { background: var(--hw-ok); border-color: var(--hw-ok); color: #fff; }
  button.act.go ha-icon, button.act.stop ha-icon { color: #fff; }
  button.act.stop { background: var(--hw-alarm); border-color: var(--hw-alarm); color: #fff; }
  button.act:disabled { opacity: 0.45; cursor: default; }
  button.act:focus-visible, button.key:focus-visible, button.plain:focus-visible { outline: 3px solid var(--primary-color); outline-offset: 2px; }
  .msg { margin: 0 20px 16px; padding: 10px 14px; border-radius: 10px; background: var(--secondary-background-color, #f5f5f5); }
  .msg.err { color: var(--error-color, #db4437); }
  .pad { padding: 18px 20px 20px; display: grid; gap: 14px; justify-items: center; }
  .pad .what { font-size: 1.15rem; font-weight: 500; }
  .dots { display: flex; gap: 12px; min-height: 18px; }
  .dots span { width: 14px; height: 14px; border-radius: 50%; background: var(--primary-text-color); }
  .keys { display: grid; grid-template-columns: repeat(3, 76px); gap: 12px; }
  button.key {
    font: inherit; font-size: 1.6rem; width: 76px; height: 76px; border-radius: 50%; cursor: pointer;
    color: var(--primary-text-color); background: var(--secondary-background-color, #f5f5f5);
    border: 1px solid var(--divider-color);
  }
  button.key.small { font-size: 1rem; }
  .row { display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; }
  button.plain {
    font: inherit; padding: 12px 22px; border-radius: 12px; cursor: pointer; min-width: 120px;
    border: 1px solid var(--divider-color); background: none; color: var(--primary-text-color);
  }
  button.plain.primary { background: var(--primary-color); border-color: var(--primary-color); color: var(--text-primary-color, #fff); }
  .empty { padding: 20px; }
  /* Kompakt: eine Zeile Zustand, kleinere Knöpfe */
  .compact .band { padding: 12px 16px; gap: 12px; }
  .compact .band ha-icon { --mdc-icon-size: 32px; }
  .compact .word { font-size: 1.3rem; }
  .compact .sub { margin-top: 2px; font-size: 0.85rem; }
  .compact .clock { font-size: 1.5rem; }
  .compact .drain { height: 3px; }
  .compact .notes { padding: 8px 16px 0; font-size: 0.9rem; }
  .compact .actions { padding: 10px 16px 14px; gap: 8px; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); }
  .compact button.act { min-height: 48px; font-size: 1rem; border-radius: 12px; gap: 8px; }
  .compact button.act ha-icon { --mdc-icon-size: 22px; }
  .compact button.act.wide { min-height: 52px; font-size: 1.05rem; }
  @media (max-width: 420px) {
    .band { padding: 18px 16px; gap: 12px; }
    .band ha-icon { --mdc-icon-size: 40px; }
    .word { font-size: 1.6rem; }
    .clock { font-size: 1.9rem; }
    .actions:not(.fixed) { padding: 14px 16px 16px; grid-template-columns: 1fr 1fr; }
    button.act { min-height: 64px; font-size: 1rem; }
    .keys { grid-template-columns: repeat(3, 68px); }
    button.key { width: 68px; height: 68px; }
  }
`;

const esc = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

const DEFAULTS = {
  groesse: "gross",
  zeige_zuletzt: true,
  zeige_offen: true,
  zeige_nicht_erreichbar: true,
  zeige_testmodus: true,
  zeige_balken: true,
  zeige_alle_unscharf: true,
  blinken: true,
  rueckfrage_scharf: false,
  rueckfrage_unscharf: false,
};
const SHOW_KEYS = ["zeige_zuletzt", "zeige_offen", "zeige_nicht_erreichbar", "zeige_testmodus", "zeige_balken", "zeige_alle_unscharf", "blinken"];
const COLORS = {
  farbe_unscharf: "--hw-ok",
  farbe_verzoegerung: "--hw-wait",
  farbe_scharf: "--hw-armed",
  farbe_alarm: "--hw-alarm",
};

// Farbe aus der Konfiguration: #rrggbb, [r, g, b], rgb(…) oder Farbname – sonst ignorieren
const cssColor = (value) => {
  if (Array.isArray(value) && value.length === 3 && value.every((n) => Number.isFinite(Number(n)))) {
    return `rgb(${value.map((n) => Math.max(0, Math.min(255, Math.round(Number(n))))).join(", ")})`;
  }
  const v = String(value ?? "").trim();
  if (/^#[0-9a-f]{3,8}$/i.test(v) || /^rgba?\([0-9.,\s%]+\)$/i.test(v) || /^[a-z]{3,20}$/i.test(v)) return v;
  return null;
};
const toHex = (rgb) => `#${rgb.map((n) => Math.max(0, Math.min(255, Math.round(Number(n)))).toString(16).padStart(2, "0")).join("")}`;
const toRgb = (value) => {
  if (Array.isArray(value)) return value;
  const m = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(String(value || ""));
  return m ? [parseInt(m[1], 16), parseInt(m[2], 16), parseInt(m[3], 16)] : undefined;
};

const EDITOR_TEXT = {
  de: {
    title: "Titel",
    bereich: "Bereich",
    all: "Alle Bereiche",
    groesse: "Größe",
    gross: "Groß (Tablet)",
    kompakt: "Kompakt",
    secProfiles: "Profilknöpfe",
    profile: "Profile und Reihenfolge",
    profileHelp: "Keine Auswahl = alle Profile. Ausgeblendete Profile lassen sich hier nur nicht schalten.",
    spalten: "Knöpfe je Zeile",
    auto: "Automatisch",
    secShow: "Anzeigen",
    zeige_zuletzt: "Wer zuletzt geschaltet hat",
    zeige_offen: "Offene Melder (unscharf)",
    zeige_nicht_erreichbar: "Nicht erreichbare Melder",
    zeige_testmodus: "Hinweis Testmodus",
    zeige_balken: "Ablaufender Balken bei Verzögerung",
    zeige_alle_unscharf: "Knopf „Alle Bereiche unscharf“",
    blinken: "Blinken bei Alarm",
    secColors: "Farben",
    colorsHelp: "Leer = Standardfarbe",
    farbe_unscharf: "Unscharf",
    farbe_verzoegerung: "Verzögerung",
    farbe_scharf: "Scharf",
    farbe_alarm: "Alarm",
    secUse: "Bedienung",
    rueckfrage_scharf: "Rückfrage vor dem Scharfschalten",
    rueckfrage_unscharf: "Rückfrage vor dem Unscharfschalten",
    useHelp: "Gegen versehentliches Tippen, z. B. am Wandtablet. Wird ein PIN verlangt, gibt es keine zusätzliche Frage.",
  },
  en: {
    title: "Title",
    bereich: "Area",
    all: "All areas",
    groesse: "Size",
    gross: "Large (tablet)",
    kompakt: "Compact",
    secProfiles: "Profile buttons",
    profile: "Profiles and order",
    profileHelp: "No selection = all profiles. Hidden profiles just can't be armed from this card.",
    spalten: "Buttons per row",
    auto: "Automatic",
    secShow: "Show",
    zeige_zuletzt: "Who switched last",
    zeige_offen: "Open sensors (disarmed)",
    zeige_nicht_erreichbar: "Unreachable sensors",
    zeige_testmodus: "Test mode notice",
    zeige_balken: "Countdown bar during delays",
    zeige_alle_unscharf: "Button “Disarm all areas”",
    blinken: "Flash during alarm",
    secColors: "Colors",
    colorsHelp: "Empty = default color",
    farbe_unscharf: "Disarmed",
    farbe_verzoegerung: "Delay",
    farbe_scharf: "Armed",
    farbe_alarm: "Alarm",
    secUse: "Operation",
    rueckfrage_scharf: "Ask before arming",
    rueckfrage_unscharf: "Ask before disarming",
    useHelp: "Against accidental taps, e.g. on a wall tablet. No extra question when a PIN is required.",
  },
};

class HauswachtAlarmCard extends HTMLElement {
  // --- Visueller Editor ----------------------------------------------------------

  static getConfigElement() {
    return window.hauswachtEditor("hauswacht-alarm-card");
  }

  static get editorNeedsInfo() {
    return true;
  }

  static editorDefaults() {
    return { ...DEFAULTS };
  }

  static editorSchema(hass, info, lang, config = {}) {
    const t = EDITOR_TEXT[lang] || EDITOR_TEXT.en;
    const areas = (info && info.areas) || [];
    const many = areas.length > 1;
    const chosen = String(config.bereich || "").toLowerCase();
    const shown = chosen ? areas.filter((a) => a.id === chosen || a.name.toLowerCase() === chosen) : areas;
    const profiles = shown.flatMap((a) =>
      a.profiles.map((p) => ({ value: p.id, label: shown.length > 1 ? `${p.name} (${a.name})` : p.name })),
    );
    const bool = (name) => ({ name, selector: { boolean: {} } });
    const schema = [
      { name: "title", selector: { text: {} } },
      ...(many
        ? [{ name: "bereich", selector: { select: { mode: "dropdown", options: [{ value: "alle", label: t.all }, ...areas.map((a) => ({ value: a.id, label: a.name }))] } } }]
        : []),
      { name: "groesse", selector: { select: { mode: "list", options: [{ value: "gross", label: t.gross }, { value: "kompakt", label: t.kompakt }] } } },
      {
        type: "expandable",
        name: "sec_profile",
        title: t.secProfiles,
        flatten: true,
        schema: [
          { name: "profile", selector: { select: { multiple: true, reorder: true, mode: "list", options: profiles } } },
          { name: "spalten", selector: { select: { mode: "dropdown", options: [{ value: "auto", label: t.auto }, ...["1", "2", "3", "4"].map((v) => ({ value: v, label: v }))] } } },
        ],
      },
      { type: "expandable", name: "sec_show", title: t.secShow, flatten: true, schema: SHOW_KEYS.map(bool) },
      {
        type: "expandable",
        name: "sec_colors",
        title: t.secColors,
        flatten: true,
        schema: Object.keys(COLORS).map((name) => ({ name, selector: { color_rgb: {} } })),
      },
      { type: "expandable", name: "sec_use", title: t.secUse, flatten: true, schema: [bool("rueckfrage_scharf"), bool("rueckfrage_unscharf")] },
    ];
    const labels = { ...t };
    const helpers = {
      profile: t.profileHelp,
      farbe_alarm: t.colorsHelp,
      rueckfrage_unscharf: t.useHelp,
    };
    return { schema, labels, helpers };
  }

  static editorToForm(config) {
    const data = { ...DEFAULTS, ...config };
    data.bereich = config.bereich || "alle";
    data.spalten = config.spalten ? String(config.spalten) : "auto";
    for (const key of Object.keys(COLORS)) data[key] = toRgb(config[key]);
    return data;
  }

  static editorFromForm(data) {
    const out = { ...data };
    if (out.bereich === "alle") delete out.bereich;
    if (!out.spalten || out.spalten === "auto") delete out.spalten;
    else out.spalten = Number(out.spalten);
    for (const key of Object.keys(COLORS)) {
      if (Array.isArray(out[key])) out[key] = toHex(out[key]);
    }
    return out;
  }

  // --- Karte ---------------------------------------------------------------------

  _opt(key) {
    const value = this._config[key];
    return value === undefined ? DEFAULTS[key] : value;
  }

  setConfig(config) {
    this._config = config || {};
    this._ui = null; // { kind: "pin" | "confirm", area, action, profile, code, force, message }
    this._msg = null;
    this._signature = "";
    if (this._hass) this._render();
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

  connectedCallback() {
    this._tick = setInterval(() => this._updateClocks(), 1000);
    this._poll = setInterval(() => this._loadInfo(), 60000);
    this._keys = (ev) => this._onKey(ev);
    window.addEventListener("keydown", this._keys);
    if (this._hass) this._loadInfo();
  }

  disconnectedCallback() {
    clearInterval(this._tick);
    clearInterval(this._poll);
    window.removeEventListener("keydown", this._keys);
  }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    if (first) this._loadInfo();
    // Bereich war kurz weg (Einstellungen geändert -> neu geladen): Rechte und Profile neu holen
    const back = (this._areas() || []).some((a) => {
      const was = this._seen && this._seen[a.entity_id];
      const now = hass.states[a.entity_id] && hass.states[a.entity_id].state;
      return was === "unavailable" && now && now !== "unavailable";
    });
    this._seen = {};
    for (const a of this._areas() || []) this._seen[a.entity_id] = hass.states[a.entity_id] && hass.states[a.entity_id].state;
    if (back) this._loadInfo();
    this._render();
  }

  _t(key) {
    const lang = ((this._hass && this._hass.language) || "en").split("-")[0];
    return (TEXT[lang] || TEXT.en)[key];
  }

  async _loadInfo() {
    if (!this._hass) return;
    try {
      this._info = await this._hass.callWS({ type: "hauswacht/alarm/info" });
      this._error = null;
    } catch (err) {
      this._error = (err && err.code) === "not_loaded" ? this._t("notLoaded") : (err && err.message) || String(err);
    }
    this._signature = "";
    this._render();
  }

  _areas() {
    if (!this._info) return null;
    const wanted = this._config.bereich;
    if (!wanted) return this._info.areas;
    const w = String(wanted).toLowerCase();
    return this._info.areas.filter((a) => a.id === w || a.name.toLowerCase() === w);
  }

  _kind(stateObj) {
    if (!stateObj || stateObj.state === "unavailable" || stateObj.state === "unknown") return "unavailable";
    const s = stateObj.state;
    if (s === "disarmed") return "disarmed";
    if (s === "arming") return "arming";
    if (s === "pending") return "pending";
    if (s === "triggered") return "triggered";
    return "armed";
  }

  _nameOf(entityId) {
    const st = this._hass.states[entityId];
    return (st && st.attributes.friendly_name) || entityId;
  }

  _time(iso) {
    try {
      return new Date(iso).toLocaleTimeString(this._hass.language, { hour: "2-digit", minute: "2-digit" });
    } catch (e) {
      return "";
    }
  }

  _remaining(iso) {
    if (!iso) return null;
    const left = Math.max(0, Math.round((new Date(iso).getTime() - Date.now()) / 1000));
    return left;
  }

  _fmt(seconds) {
    const m = Math.floor(seconds / 60);
    const s = String(seconds % 60).padStart(2, "0");
    return `${m}:${s}`;
  }

  _render() {
    if (!this._hass || !this._config) return;
    const areas = this._areas();
    const states = (areas || []).map((a) => {
      const st = this._hass.states[a.entity_id];
      return st ? [st.state, st.last_changed, JSON.stringify(st.attributes)] : ["?"];
    });
    const signature = JSON.stringify([this._config, this._error, this._info, states, this._ui, this._msg, this._busy]);
    if (signature === this._signature) return;
    this._signature = signature;
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
      this.shadowRoot.addEventListener("click", (ev) => this._onClick(ev));
    }
    const classes = [this._opt("groesse") === "kompakt" ? "compact" : "", this._opt("blinken") ? "" : "no-pulse"].join(" ").trim();
    const colors = Object.entries(COLORS)
      .map(([key, prop]) => [prop, cssColor(this._config[key])])
      .filter(([, color]) => color)
      .map(([prop, color]) => `${prop}: ${color};`)
      .join(" ");
    this.shadowRoot.innerHTML = `<style>${STYLE}</style><ha-card class="${classes}"><div class="root" style="${esc(colors)}">${this._body(areas)}</div></ha-card>`;
    this._updateClocks();
  }

  _body(areas) {
    const title = this._config.title ? `<div class="title">${esc(this._config.title)}</div>` : "";
    if (this._error) return `${title}<div class="empty">${esc(this._error)}</div>`;
    if (!areas) return `${title}<div class="empty">${this._t("loading")}</div>`;
    if (!areas.length) return `${title}<div class="empty">${this._t("noAreas")}</div>`;
    const blocks = areas.map((a) => this._area(a, areas.length > 1)).join("");
    const armedCount = areas.filter((a) => this._kind(this._hass.states[a.entity_id]) !== "disarmed").length;
    const all =
      areas.length > 1 && armedCount > 1 && !this._ui && this._opt("zeige_alle_unscharf")
        ? `<div class="actions"><button class="act wide go" data-do="disarm-all"><ha-icon icon="mdi:shield-off"></ha-icon>${this._t("disarmAll")}</button></div>`
        : "";
    const msg = this._msg ? `<div class="msg ${this._msg.err ? "err" : ""}" role="status">${esc(this._msg.text)}</div>` : "";
    return `${title}${blocks}${all}${msg}`;
  }

  _area(area, showName) {
    const st = this._hass.states[area.entity_id];
    const kind = this._kind(st);
    const attrs = (st && st.attributes) || {};
    let word = this._t(kind);
    if (st && st.state === "triggered" && attrs.phase === "alarm_hold") word = this._t("hold");
    const profile = (kind === "armed" || kind === "arming" || kind === "pending") && attrs.profile_name
      ? ` <span class="profile">${esc(attrs.profile_name)}</span>`
      : "";
    const subParts = [];
    if (showName) subParts.push(esc(area.name));
    if (attrs.changed_by && this._opt("zeige_zuletzt")) subParts.push(`${this._t("lastBy")}: ${esc(attrs.changed_by)}, ${esc(this._time(st.last_changed))}`);
    const timer = attrs.timer_ends_at && (kind === "arming" || kind === "pending");
    const band = `<div class="band ${kind}" data-area="${esc(area.id)}">
        <ha-icon icon="${ICONS[kind]}"></ha-icon>
        <div class="state"><div class="word">${esc(word)}${profile}</div>${subParts.length ? `<div class="sub">${subParts.join("<br>")}</div>` : ""}</div>
        ${timer ? `<div class="clock" data-ends="${esc(attrs.timer_ends_at)}"></div>` : ""}
        ${timer && this._opt("zeige_balken") ? `<div class="drain" data-ends="${esc(attrs.timer_ends_at)}" data-from="${esc(st.last_changed)}"></div>` : ""}
      </div>`;
    const ui = this._ui && this._ui.area === area.id ? this._ui : null;
    return `<div class="area">${band}${this._notes(area, kind, attrs)}${ui ? this._dialog(ui) : this._buttons(area, kind)}</div>`;
  }

  _notes(area, kind, attrs) {
    const notes = [];
    if (attrs.test_mode && this._opt("zeige_testmodus")) notes.push(["info", "mdi:test-tube", this._t("testMode")]);
    if (kind === "triggered" && attrs.trigger_sensor) {
      notes.push(["", "mdi:alarm-light-outline", `<b>${this._t("trigger")}:</b> ${esc(this._nameOf(attrs.trigger_sensor))}`]);
    }
    if (kind === "disarmed" && this._opt("zeige_offen") && (attrs.open_sensors || []).length) {
      notes.push(["", "mdi:door-open", `<b>${this._t("open")}:</b> ${attrs.open_sensors.map((e) => esc(this._nameOf(e))).join(", ")}`]);
    }
    if (this._opt("zeige_nicht_erreichbar") && (attrs.unavailable_sensors || []).length) {
      notes.push(["", "mdi:wifi-off", `<b>${this._t("unavailableSensors")}:</b> ${attrs.unavailable_sensors.map((e) => esc(this._nameOf(e))).join(", ")}`]);
    }
    if (attrs.code_locked_until && area.pin.disarm) {
      notes.push(["", "mdi:lock-clock", `${this._t("locked")} ${esc(this._time(attrs.code_locked_until))}`]);
    }
    if (!notes.length) return "";
    return `<div class="notes">${notes.map(([cls, icon, html]) => `<div class="note ${cls}"><ha-icon icon="${icon}"></ha-icon><span>${html}</span></div>`).join("")}</div>`;
  }

  _buttons(area, kind) {
    const busy = this._busy ? "disabled" : "";
    if (kind === "unavailable") return "";
    const cols = Number(this._config.spalten);
    const grid = cols >= 1 && cols <= 4 ? ` fixed" style="grid-template-columns: repeat(${cols}, 1fr)` : "";
    if (kind === "disarmed") {
      const profiles = this._profiles(area);
      if (!profiles.length) return `<div class="empty">${this._t("noProfiles")}</div>`;
      const may = area.may.arm ? "" : "disabled";
      return `<div class="actions${grid}">${profiles
        .map(
          (p) => `<button class="act" data-do="arm" data-area="${esc(area.id)}" data-profile="${esc(p.id)}" ${busy || may}>
            <ha-icon icon="${esc(p.icon || "mdi:shield-lock")}"></ha-icon><span>${esc(p.name)}</span></button>`,
        )
        .join("")}</div>`;
    }
    const out = [];
    if (kind === "triggered") {
      out.push(
        `<button class="act wide stop" data-do="end_alarm" data-area="${esc(area.id)}" ${busy || (area.may.end_alarm ? "" : "disabled")}><ha-icon icon="mdi:alarm-light-off"></ha-icon>${this._t("endAlarm")}</button>`,
      );
    }
    out.push(
      `<button class="act wide go" data-do="disarm" data-area="${esc(area.id)}" ${busy || (area.may.disarm ? "" : "disabled")}><ha-icon icon="mdi:shield-off"></ha-icon>${this._t("disarm")}</button>`,
    );
    return `<div class="actions">${out.join("")}</div>`;
  }

  // Profilknöpfe: alle, oder nur die gewählten in der gewählten Reihenfolge
  _profiles(area) {
    const wanted = Array.isArray(this._config.profile) ? this._config.profile.map(String) : [];
    if (!wanted.length) return area.profiles;
    const own = wanted.map((id) => area.profiles.find((p) => p.id === id)).filter(Boolean);
    // Gilt die Auswahl nur für andere Bereiche, zeigt dieser Bereich alle seine Profile
    return own.length ? own : area.profiles;
  }

  _dialog(ui) {
    if (ui.kind === "ask") {
      return `<div class="pad"><div class="what">${esc(ui.question)}</div>
        <div class="row"><button class="plain" data-do="cancel">${this._t("cancel")}</button>
        <button class="plain primary" data-do="go">${esc(ui.yes)}</button></div></div>`;
    }
    if (ui.kind === "confirm") {
      return `<div class="pad"><div class="what">${esc(ui.message)}</div>
        <div class="row"><button class="plain" data-do="cancel">${this._t("cancel")}</button>
        <button class="plain primary" data-do="force">${this._t("force")}</button></div></div>`;
    }
    const dots = "<span></span>".repeat((ui.code || "").length);
    const keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
      .map((k) => `<button class="key" data-key="${k}">${k}</button>`)
      .join("");
    return `<div class="pad"><div class="what">${esc(ui.title)}</div>
      <div class="dots" aria-label="${(ui.code || "").length}">${dots}</div>
      <div class="keys">${keys}<button class="key small" data-key="back" aria-label="${this._t("clear")}"><ha-icon icon="mdi:backspace-outline"></ha-icon></button>
      <button class="key" data-key="0">0</button><button class="key small" data-do="submit">${this._t("ok")}</button></div>
      <div class="row"><button class="plain" data-do="cancel">${this._t("cancel")}</button></div></div>`;
  }

  _updateClocks() {
    if (!this.shadowRoot) return;
    for (const el of this.shadowRoot.querySelectorAll(".clock")) {
      const left = this._remaining(el.dataset.ends);
      el.textContent = left === null ? "" : this._fmt(left);
    }
    for (const el of this.shadowRoot.querySelectorAll(".drain")) {
      const end = new Date(el.dataset.ends).getTime();
      const start = new Date(el.dataset.from).getTime();
      const share = end > start ? Math.max(0, Math.min(1, (end - Date.now()) / (end - start))) : 0;
      el.style.width = `${(share * 100).toFixed(1)}%`;
    }
  }

  _areaInfo(id) {
    return (this._info && this._info.areas.find((a) => a.id === id)) || null;
  }

  _onClick(ev) {
    const target = ev.composedPath().find((el) => el.dataset && (el.dataset.do || el.dataset.key));
    if (!target || target.disabled) return;
    const { key } = target.dataset;
    if (key) {
      this._pressKey(key);
      return;
    }
    const what = target.dataset.do;
    if (what === "cancel") {
      this._ui = null;
      this._render();
    } else if (what === "submit") {
      this._submitPin();
    } else if (what === "go") {
      const { kind, question, yes, ...req } = this._ui;
      this._run(req);
    } else if (what === "force") {
      const ui = this._ui;
      this._run({ ...ui, force: true });
    } else if (what === "disarm-all") {
      this._disarmAll();
    } else {
      this._start(target.dataset.area, what, target.dataset.profile);
    }
  }

  _onKey(ev) {
    if (!this._ui || this._ui.kind !== "pin") return;
    if (/^[0-9]$/.test(ev.key)) this._pressKey(ev.key);
    else if (ev.key === "Backspace") this._pressKey("back");
    else if (ev.key === "Enter") this._submitPin();
    else if (ev.key === "Escape") {
      this._ui = null;
      this._render();
    } else return;
    ev.preventDefault();
  }

  _pressKey(key) {
    if (!this._ui || this._ui.kind !== "pin") return;
    const code = this._ui.code || "";
    if (key === "clear") this._ui = { ...this._ui, code: "" };
    else if (key === "back") this._ui = { ...this._ui, code: code.slice(0, -1) };
    else if (code.length < 8) this._ui = { ...this._ui, code: code + key };
    this._render();
  }

  _submitPin() {
    if (!this._ui || this._ui.kind !== "pin" || !(this._ui.code || "").length) return;
    this._run(this._ui);
  }

  _start(areaId, action, profile) {
    const area = this._areaInfo(areaId);
    if (!area) return;
    this._msg = null;
    const req = { area: areaId, action, profile, code: null, force: false };
    if (area.pin[action]) {
      const name = profile && (area.profiles.find((p) => p.id === profile) || {}).name;
      const label = action === "arm" ? `${this._t("armed")}: ${name}` : action === "end_alarm" ? this._t("endAlarm") : this._t("disarm");
      this._ui = { kind: "pin", title: `${this._t("enterPin")} – ${label}`, ...req, code: "" };
      this._render();
      return;
    }
    const ask = this._question(area, req);
    if (ask) {
      this._ui = { kind: "ask", ...req, ...ask };
      this._render();
      return;
    }
    this._run(req);
  }

  // Rückfrage vor dem Schalten (nur ohne PIN – der PIN ist schon eine Bestätigung)
  _question(area, req) {
    if (req.action === "arm" && this._opt("rueckfrage_scharf")) {
      const name = (area.profiles.find((p) => p.id === req.profile) || {}).name || "";
      return { question: this._t("askArm").replace("{p}", name), yes: this._t("doArm") };
    }
    if (req.action === "disarm" && this._opt("rueckfrage_unscharf")) {
      return { question: this._t("askDisarm"), yes: this._t("disarm") };
    }
    return null;
  }

  async _send(req) {
    const msg = { type: "hauswacht/alarm/action", area: req.area, action: req.action, force: !!req.force };
    if (req.profile) msg.profile = req.profile;
    if (req.code) msg.code = req.code;
    return this._hass.callWS(msg);
  }

  async _run(req) {
    if (req.all) {
      // "Alle unscharf" mit PIN: derselbe PIN für jeden noch scharfen Bereich
      const areas = (this._areas() || []).filter((a) => this._kind(this._hass.states[a.entity_id]) !== "disarmed");
      for (const a of areas) await this._run({ area: a.id, action: "disarm", code: req.code });
      return;
    }
    this._busy = true;
    this._render();
    let result;
    try {
      result = await this._send(req);
    } catch (err) {
      result = { ok: false, message: (err && err.message) || String(err) };
    }
    this._busy = false;
    if (result.ok) {
      this._ui = null;
      this._flash({ text: this._t("done")[req.action] });
    } else if (result.can_force) {
      this._ui = { kind: "confirm", ...req, message: result.message };
    } else if (result.error === "card_pin_required") {
      // Rechte haben sich geändert: jetzt doch mit PIN
      this._ui = { kind: "pin", title: this._t("enterPin"), ...req, code: "" };
      this._loadInfo();
    } else {
      this._ui = null;
      this._flash({ text: result.message || result.error, err: true });
    }
    this._render();
  }

  async _disarmAll() {
    const areas = (this._areas() || []).filter((a) => this._kind(this._hass.states[a.entity_id]) !== "disarmed");
    const needsPin = areas.find((a) => a.pin.disarm);
    if (needsPin) {
      // Ein PIN für alle: nacheinander mit demselben PIN
      this._ui = { kind: "pin", title: `${this._t("enterPin")} – ${this._t("disarmAll")}`, area: needsPin.id, action: "disarm", all: true, code: "" };
      this._render();
      return;
    }
    if (!areas.length) return;
    if (this._opt("rueckfrage_unscharf")) {
      this._ui = { kind: "ask", area: areas[0].id, action: "disarm", all: true, question: this._t("askDisarm"), yes: this._t("disarmAll") };
      this._render();
      return;
    }
    for (const a of areas) await this._run({ area: a.id, action: "disarm" });
  }

  _flash(msg) {
    this._msg = msg;
    clearTimeout(this._msgTimer);
    this._msgTimer = setTimeout(() => {
      this._msg = null;
      this._render();
    }, msg.err ? 8000 : 3000);
  }
}

if (!customElements.get("hauswacht-alarm-card")) {
  customElements.define("hauswacht-alarm-card", HauswachtAlarmCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "hauswacht-alarm-card",
    name: "Hauswacht Alarm",
    description: "Scharf und unscharf schalten – ohne PIN-Zwang, mit den Rechten des angemeldeten Kontos",
    preview: false,
    documentationURL: "https://github.com/schlusenbaum/hauswacht/blob/main/docs/dashboard.md#karte-hauswacht-alarm",
  });
}
