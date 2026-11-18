// Hauswacht – Einstellungsseite in der Seitenleiste (ADR 0011), Stufe 1: alles auf einen Blick.
//
// Nur stabile Bausteine: eigene Web-Component, ha-card, ha-icon und die Farben des Themas.
// Die Abschnitte kommen aus der Karte "Hauswacht Übersicht" (dieselben Texte und Daten über
// den Websocket-Befehl hauswacht/overview, nur für Administratoren). Bearbeitet wird in dieser
// Stufe noch im Einstellungsdialog.

const TEXTS = {
  de: {
    title: "Hauswacht",
    loading: "Lade …",
    refresh: "Neu laden",
    dialog: "Im Dialog bearbeiten",
    hint: "Diese Seite zeigt die ganze Einrichtung auf einen Blick. Bearbeiten kommt Schritt für Schritt dazu – bis dahin über „Im Dialog bearbeiten“.",
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
    },
    search: "Melder suchen …",
    noGroup: "Ohne Meldergruppe",
    sensorsCount: "Melder",
    vibrationRule: "Erschütterung: Alarm bei {n} Meldungen in {s} s",
    special: "Besondere Melder",
    tilt: "Melder mit Kippstellung",
    tiltLine: "zu: {c} · gekippt: {t}",
    strength: "Erschütterungsstärken",
    strengthLine: "ab {v}",
    noSpecial: "Keine – anlegen im Dialog unter Alarmauslösung → Besondere Melder.",
    group: "Gruppe",
    none: "keine",
    noMatch: "Kein Melder passt zur Suche.",
  },
  en: {
    title: "Hauswacht",
    loading: "Loading …",
    refresh: "Reload",
    dialog: "Edit in the dialog",
    hint: "This page shows the whole setup at a glance. Editing is added step by step – until then use “Edit in the dialog”.",
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
    },
    search: "Search sensors …",
    noGroup: "Without sensor group",
    sensorsCount: "sensors",
    vibrationRule: "Vibration: alarm at {n} reports in {s} s",
    special: "Special sensors",
    tilt: "Sensors with tilt position",
    tiltLine: "closed: {c} · tilted: {t}",
    strength: "Vibration strengths",
    strengthLine: "from {v}",
    noSpecial: "None – create them in the dialog under Alarm triggering → Special sensors.",
    group: "Group",
    none: "none",
    noMatch: "No sensor matches the search.",
  },
};

const TABS = ["overview", "sensors", "profiles", "rules", "sirens", "notifications", "people", "system"];
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
  .search { width: 100%; box-sizing: border-box; font: inherit; padding: 8px 12px; margin: 4px 0 10px;
    border: 1px solid var(--divider-color); border-radius: 8px; background: var(--card-background-color); color: var(--primary-text-color); }
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
    this._search = "";
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
    if (!window.HauswachtOverviewView) {
      const version = this._panel?.config?.version || "0";
      try {
        await import(`/hauswacht/hauswacht-uebersicht-card.js?v=${version}`);
      } catch (_err) {
        // bleibt leer; _load meldet den Fehler
      }
    }
    this._ready = true;
    await this._load();
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

  _view() {
    // Zeichen-Helfer der Übersichtskarte, ohne sie anzuzeigen
    const View = window.HauswachtOverviewView;
    if (!View || !this._data) return null;
    const view = new View();
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
    const term = this._search.trim().toLowerCase();
    const groups = d.groups || [];
    const byGroup = new Map(groups.map((g) => [g.name, []]));
    const loose = [];
    for (const s of d.sensors) {
      if (term && !String(s.name).toLowerCase().includes(term)) continue;
      if (s.zone && byGroup.has(s.zone)) byGroup.get(s.zone).push(s);
      else loose.push(s);
    }
    const cols = d.profiles.length + 4;
    const row = (s) =>
      `<tr><td>${escHtml(s.name)}${s.always_active ? ` <span class="muted">(${escHtml(view._t("always"))})</span>` : ""}</td><td>${escHtml(view._l("type", s.type))}</td><td class="${s.state === "unavailable" ? "warn" : ""}">${escHtml(view._l("state", s.state))}</td><td class="nw">${s.battery != null ? `${s.battery} %` : ""}</td>${d.profiles.map((p) => `<td class="c">${view._sensorRole((s.profiles || {})[p.id])}</td>`).join("")}</tr>`;
    let body = "";
    for (const g of groups) {
      const members = byGroup.get(g.name) || [];
      if (!members.length && term) continue;
      const vibration = members.some((s) => s.type === "vibration") && g.vibration_count > 1
        ? ` · ${escHtml(this._fmt("vibrationRule", { n: g.vibration_count, s: g.vibration_window }))}`
        : "";
      body += `<tr class="grp"><td colspan="${cols}">${escHtml(g.name)} <span class="muted">${g.count} ${escHtml(this._t("sensorsCount"))}${vibration}</span></td></tr>`;
      body += members.map(row).join("");
    }
    if (loose.length) {
      body += `<tr class="grp"><td colspan="${cols}">${escHtml(this._t("noGroup"))}</td></tr>` + loose.map(row).join("");
    }
    if (!body) body = `<tr><td colspan="${cols}" class="muted">${escHtml(this._t("noMatch"))}</td></tr>`;
    const matrix = `
      <input class="search" type="search" placeholder="${escHtml(this._t("search"))}" value="${escHtml(this._search)}">
      <div class="muted">${escHtml(view._t("legend"))}</div>
      <div class="scroll"><table>
        <tr><th>${escHtml(view._t("sensors"))}</th><th>${escHtml(view._t("type"))}</th><th>${escHtml(view._t("state"))}</th><th>🔋</th>${d.profiles.map((p) => `<th class="c">${escHtml(p.name)}</th>`).join("")}</tr>
        ${body}
      </table></div>`;
    const special = d.special || { tilt: [], vibration: [] };
    const where = (x) => `${escHtml(this._t("group"))}: ${escHtml(x.group || this._t("none"))}`;
    const tilt = special.tilt.map((x) =>
      `<div class="item"><div class="n">${escHtml(x.name)}${x.attribute ? ` <span class="muted">(${escHtml(x.attribute)})</span>` : ""}</div><div class="muted">${escHtml(this._fmt("tiltLine", { c: x.closed.join(", ") || "–", t: x.tilted.join(", ") || "–" }))} · ${where(x)}</div></div>`
    ).join("");
    const strength = special.vibration.map((x) =>
      `<div class="item"><div class="n">${escHtml(x.name)}</div><div class="muted">${escHtml(this._fmt("strengthLine", { v: x.threshold }))} · ${where(x)}</div></div>`
    ).join("");
    const specialHtml = tilt || strength
      ? `${tilt ? `<h3>${escHtml(this._t("tilt"))}</h3>${tilt}` : ""}${strength ? `<h3>${escHtml(this._t("strength"))}</h3>${strength}` : ""}`
      : `<div class="muted">${escHtml(this._t("noSpecial"))}</div>`;
    const parts = view._parts();
    return (
      this._card(view._t("sensors"), matrix) +
      this._card(this._t("special"), specialHtml) +
      this._card(parts.always[0], parts.always[2])
    );
  }

  _card(title, body) {
    return `<ha-card><div class="wrap"><div class="head"><div class="t">${escHtml(title)}</div></div>${body}</div></ha-card>`;
  }

  _tabBody() {
    if (this._error) return `<ha-card><div class="wrap muted">${escHtml(this._error)}</div></ha-card>`;
    const view = this._view();
    if (!view) return `<div class="note">${escHtml(this._t("loading"))}</div>`;
    if (this._tab === "sensors") return this._sensorsTab(view);
    const parts = view._parts();
    const items = TAB_PARTS[this._tab] || [];
    const asOf = this._tab === "overview" ? parts.asOf : "";
    return asOf + items.map((key) => this._card(parts[key][0], parts[key][2])).join("");
  }

  _render() {
    if (!this.shadowRoot) return;
    const shared = window.HauswachtOverviewStyle || "";
    const menu = this._narrow
      ? `<button data-a="menu" title="Menu"><ha-icon icon="mdi:menu"></ha-icon></button>`
      : "";
    this.shadowRoot.innerHTML = `
      <style>${shared}${PANEL_STYLE}</style>
      <div class="top">
        ${menu}
        <div class="t"><ha-icon icon="mdi:shield-home"></ha-icon>${escHtml(this._t("title"))}</div>
        <button data-a="refresh" title="${escHtml(this._t("refresh"))}"><ha-icon icon="mdi:refresh"></ha-icon></button>
        <button class="lnk" data-a="dialog">${escHtml(this._t("dialog"))}</button>
      </div>
      <div class="tabs">${TABS.map((tab) => `<button data-tab="${tab}" class="${tab === this._tab ? "on" : ""}">${escHtml(this._t("tabs")[tab])}</button>`).join("")}</div>
      <div class="content">
        <div class="note">${escHtml(this._t("hint"))}</div>
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
    this.shadowRoot.querySelectorAll("[data-a]").forEach((button) =>
      button.addEventListener("click", () => {
        const action = button.dataset.a;
        if (action === "refresh") this._load();
        else if (action === "menu") this.dispatchEvent(new Event("hass-toggle-menu", { bubbles: true, composed: true }));
        else if (action === "dialog") this._navigate("/config/integrations/integration/hauswacht");
      })
    );
    const search = this.shadowRoot.querySelector("input.search");
    if (search) {
      search.addEventListener("input", () => {
        this._search = search.value;
        const pos = search.selectionStart;
        this._render();
        const again = this.shadowRoot.querySelector("input.search");
        if (again) {
          again.focus();
          again.setSelectionRange(pos, pos);
        }
      });
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
