// Hauswacht – Einstellungsseite, Stufe 2: Melder bearbeiten (ADR 0011).
//
// Ein eigenes Element <hauswacht-sensor-editor> als Seitenblatt: Meldergruppen (mit Typen und
// Fehlalarmschutz), Melder mit Kippstellung, Erschütterungsstärken, Immer aktiv.
// Gespeichert wird über hauswacht/settings/apply – dieselben Regeln wie im Dialog.
// Nur stabile Bausteine: eigene Elemente, ha-icon, Farben des Themas. Keine internen
// Formular-Bausteine von Home Assistant.

const ET = {
  de: {
    save: "Speichern",
    cancel: "Abbrechen",
    delete: "Löschen",
    deleteConfirm: "Wirklich löschen?",
    saving: "Speichere …",
    groupNew: "Meldergruppe anlegen",
    groupEdit: "Meldergruppe bearbeiten",
    name: "Name",
    label: "Zusätzlich alle Melder mit diesem Label",
    noLabel: "– kein Label –",
    members: "Melder",
    noMembers: "Noch keine Melder – unten suchen und hinzufügen.",
    add: "Melder hinzufügen",
    search: "Name oder Entität suchen …",
    remove: "Entfernen",
    type: "Typ",
    vibTitle: "Fehlalarmschutz für Erschütterung",
    vibText: "Alarm erst bei so vielen Meldungen eines Melders innerhalb der Zeit. Empfehlung: 2 in 60 Sekunden – ein einzelner Stoß (Tür knallt, Lkw) löst dann nicht aus, Aufhebeln erzeugt fast immer mehrere. Die Haltezeit des Sensors muss kürzer sein als das Zeitfenster.",
    vibCount: "Meldungen bis zum Alarm",
    vibWindow: "innerhalb von (Sekunden)",
    vibRecommend: "Empfehlung übernehmen",
    tiltNew: "Melder mit Kippstellung",
    tiltEntity: "Quelle (Sensor, Auswahl-Helfer oder Entität mit Attribut)",
    attribute: "Attribut (leer = Zustand selbst)",
    values: "Werte zuordnen – alles Unbekannte zählt als offen",
    valueOpen: "offen",
    valueTilted: "gekippt",
    valueClosed: "zu",
    moreValue: "weiteren Wert eintippen und Enter",
    noValues: "Keine Werte bekannt – unten eintippen.",
    strengthNew: "Erschütterungsstärke",
    strengthEntity: "Sensor mit der Stärke als Zahl",
    threshold: "Schwelle (ab diesem Wert = Erschütterung)",
    current: "gerade",
    group: "In Meldergruppe aufnehmen",
    noGroupChoice: "– keine –",
    alwaysTitle: "Immer aktiv",
    alwaysText: "Diese Melder melden auch im unscharfen Zustand (z. B. Wasser, Tresor). Sirenen dafür stellst du im Dialog ein.",
    alwaysGroups: "Ganze Meldergruppen",
    alwaysSensors: "Einzelne Melder",
    chosen: "gewählt",
    errors: {
      zone_name_required: "Bitte einen Namen eingeben.",
      zone_empty: "Mindestens einen Melder oder ein Label wählen.",
      zone_overlap: "Diese Melder stecken schon in einer anderen Gruppe:",
      unknown_type: "Unbekannter Typ.",
      out_of_range: "Wert außerhalb des erlaubten Bereichs.",
      tilt_no_closed: "Mindestens ein Wert muss „zu“ bedeuten.",
      tilt_overlap: "Ein Wert kann nicht zugleich zu und gekippt sein.",
      required: "Bitte ausfüllen.",
      disarm_first: "Erst alle Bereiche unscharf schalten – dann lässt sich speichern.",
      changed_elsewhere: "Inzwischen wurde woanders etwas geändert. Die Seite lädt neu – bitte noch einmal.",
      unknown_group: "Diese Gruppe gibt es nicht mehr.",
      failed: "Speichern fehlgeschlagen.",
    },
  },
  en: {
    save: "Save",
    cancel: "Cancel",
    delete: "Delete",
    deleteConfirm: "Really delete?",
    saving: "Saving …",
    groupNew: "Add sensor group",
    groupEdit: "Edit sensor group",
    name: "Name",
    label: "Also all sensors with this label",
    noLabel: "– no label –",
    members: "Sensors",
    noMembers: "No sensors yet – search below and add.",
    add: "Add sensor",
    search: "Search name or entity …",
    remove: "Remove",
    type: "Type",
    vibTitle: "False alarm protection for vibration",
    vibText: "Alarm only after this many reports of one sensor within the time. Recommendation: 2 in 60 seconds – a single knock (door slams, truck) then does not trigger, prying almost always causes several. The sensor's hold time must be shorter than the time window.",
    vibCount: "Reports until alarm",
    vibWindow: "within (seconds)",
    vibRecommend: "Use recommendation",
    tiltNew: "Sensor with tilt position",
    tiltEntity: "Source (sensor, select helper or entity with attribute)",
    attribute: "Attribute (empty = the state itself)",
    values: "Assign values – everything unknown counts as open",
    valueOpen: "open",
    valueTilted: "tilted",
    valueClosed: "closed",
    moreValue: "type another value and press Enter",
    noValues: "No values known – type them below.",
    strengthNew: "Vibration strength",
    strengthEntity: "Sensor with the strength as a number",
    threshold: "Threshold (from this value = vibration)",
    current: "currently",
    group: "Add to sensor group",
    noGroupChoice: "– none –",
    alwaysTitle: "Always active",
    alwaysText: "These sensors also report while disarmed (e.g. water, safe). Sirens for them are set in the dialog.",
    alwaysGroups: "Whole sensor groups",
    alwaysSensors: "Single sensors",
    chosen: "chosen",
    errors: {
      zone_name_required: "Please enter a name.",
      zone_empty: "Choose at least one sensor or a label.",
      zone_overlap: "These sensors are already in another group:",
      unknown_type: "Unknown type.",
      out_of_range: "Value out of the allowed range.",
      tilt_no_closed: "At least one value must mean “closed”.",
      tilt_overlap: "A value cannot mean both closed and tilted.",
      required: "Please fill in.",
      disarm_first: "Disarm all areas first – then saving works.",
      changed_elsewhere: "Something was changed elsewhere in the meantime. The page reloads – please try again.",
      unknown_group: "This group no longer exists.",
      failed: "Saving failed.",
    },
  },
};

const SENSOR_DOMAINS = ["binary_sensor", "lock", "cover"];
const TILT_DOMAINS = ["sensor", "input_select", "select", "binary_sensor", "lock", "cover"];
const STRENGTH_DOMAINS = ["sensor", "input_number", "number"];
const KNOWN_CLOSED = ["closed", "close", "geschlossen", "zu"];
const KNOWN_TILTED = ["tilted", "tilt", "gekippt", "kippstellung"];

const EDIT_STYLE = `
  :host { position: fixed; inset: 0; z-index: 10; display: flex; justify-content: flex-end; background: rgba(0,0,0,.35); }
  .sheet { width: min(560px, 100%); height: 100%; overflow-y: auto; box-sizing: border-box; padding: 16px 18px 80px;
    background: var(--card-background-color, #fff); color: var(--primary-text-color); box-shadow: -2px 0 8px rgba(0,0,0,.2); }
  h2 { margin: 4px 0 12px; font-size: 1.2rem; font-weight: 500; }
  label { display: block; font-size: .85rem; color: var(--secondary-text-color); margin: 12px 0 4px; }
  input, select { font: inherit; box-sizing: border-box; width: 100%; padding: 7px 10px; border-radius: 6px;
    border: 1px solid var(--divider-color); background: var(--card-background-color); color: var(--primary-text-color); }
  input.small { width: 110px; }
  .row { display: flex; gap: 8px; align-items: center; padding: 6px 0; border-bottom: 1px solid var(--divider-color); }
  .row .n { flex: 1; min-width: 0; }
  .row .n small { display: block; color: var(--secondary-text-color); overflow: hidden; text-overflow: ellipsis; }
  .row select { width: 160px; }
  .x { background: none; border: none; cursor: pointer; color: var(--secondary-text-color); font-size: 1.2rem; padding: 2px 6px; }
  .results { max-height: 240px; overflow-y: auto; border: 1px solid var(--divider-color); border-radius: 6px; margin-top: 4px; }
  .results div { padding: 6px 10px; cursor: pointer; border-bottom: 1px solid var(--divider-color); }
  .results div:hover { background: var(--secondary-background-color); }
  .results small { color: var(--secondary-text-color); }
  .box { border: 1px solid var(--divider-color); border-radius: 8px; padding: 10px 12px; margin-top: 14px; }
  .muted { color: var(--secondary-text-color); font-size: .85rem; }
  .err { color: var(--error-color, #db4437); font-size: .9rem; margin-top: 6px; }
  .bar { position: sticky; bottom: -80px; display: flex; gap: 8px; padding: 14px 0; background: var(--card-background-color); }
  button.b { font: inherit; padding: 8px 16px; border-radius: 18px; cursor: pointer; border: 1px solid var(--divider-color);
    background: var(--card-background-color); color: var(--primary-text-color); }
  button.p { background: var(--primary-color); border-color: var(--primary-color); color: var(--text-primary-color, #fff); }
  button.d { margin-left: auto; color: var(--error-color, #db4437); }
  .inline { display: flex; gap: 10px; align-items: flex-end; flex-wrap: wrap; }
  .inline > div { flex: none; }
  .chk { display: flex; gap: 8px; align-items: center; padding: 4px 0; }
  .chk input { width: auto; }
`;

const e = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

class HauswachtSensorEditor extends HTMLElement {
  // open({hass, settings, typeLabel, kind, item}) – kind: group | tilt | strength | always
  open(options) {
    Object.assign(this, options);
    this._errors = {};
    this._details = {};
    this._busy = false;
    this._query = "";
    this._draft = this._initial();
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this._render();
  }

  get _lang() {
    return (this.hass?.language || "en").startsWith("de") ? "de" : "en";
  }

  _t(key) {
    return ET[this._lang][key] ?? ET.en[key] ?? key;
  }

  _entity(id) {
    return (this.settings.entities || []).find((x) => x.id === id) || { id, name: id, domain: id.split(".")[0] };
  }

  _initial() {
    const s = this.settings;
    if (this.kind === "group") {
      const g = this.item;
      const types = {};
      for (const id of g?.entities || []) types[id] = s.sensor_types[id] || this._entity(id).suggested || "other";
      return {
        id: g?.id || null,
        name: g?.name || "",
        label: g?.label || "",
        entities: [...(g?.entities || [])],
        types,
        vibration_count: g?.vibration_count ?? 1,
        vibration_window: g?.vibration_window ?? 60,
      };
    }
    if (this.kind === "tilt") {
      const t = this.item;
      const map = {};
      for (const v of t?.closed || []) map[v] = "closed";
      for (const v of t?.tilted || []) map[v] = "tilted";
      return { entity: t?.entity || "", attribute: t?.attribute || "", map, group: "", existing: !!t };
    }
    if (this.kind === "strength") {
      const v = this.item;
      return { entity: v?.entity || "", threshold: v?.threshold ?? "", group: "", existing: !!v };
    }
    return { zones: [...(s.always.zones || [])], sensors: [...(s.always.sensors || [])] };
  }

  // --- Auswahl --------------------------------------------------------------------

  _pickerHtml(domains, exclude, extraIds = []) {
    const q = this._query.trim().toLowerCase();
    let list = "";
    if (q) {
      const hits = (this.settings.entities || [])
        .filter((x) => (domains.includes(x.domain) || extraIds.includes(x.id)) && !exclude.includes(x.id))
        .filter((x) => x.name.toLowerCase().includes(q) || x.id.toLowerCase().includes(q))
        .slice(0, 40);
      list = `<div class="results">${hits.map((x) => `<div data-pick="${e(x.id)}">${e(x.name)}<br><small>${e(x.id)} · ${e(x.state)}</small></div>`).join("") || `<div class="muted">–</div>`}</div>`;
    }
    return `<input class="q" type="search" placeholder="${e(this._t("search"))}" value="${e(this._query)}">${list}`;
  }

  _groupSelect(name, current) {
    return `<select data-f="${name}"><option value="">${e(this._t("noGroupChoice"))}</option>${this.settings.groups.map((g) => `<option value="${e(g.id)}" ${g.id === current ? "selected" : ""}>${e(g.name)}</option>`).join("")}</select>`;
  }

  _err(field) {
    const key = this._errors[field];
    if (!key) return "";
    let text = this._t("errors")[key] || key;
    if (key === "zone_overlap" && this._details.conflicts) {
      text += " " + Object.entries(this._details.conflicts).map(([id, zone]) => `${this._entity(id).name} (${zone})`).join(", ");
    }
    return `<div class="err">${e(text)}</div>`;
  }

  // --- Formulare ------------------------------------------------------------------

  _groupForm() {
    const d = this._draft;
    const special = [...this.settings.tilt.map((x) => x.entity), ...this.settings.strength.map((x) => x.entity)];
    const members = d.entities
      .map((id) => {
        const x = this._entity(id);
        const options = this.settings.types.map((t) => `<option value="${t}" ${d.types[id] === t ? "selected" : ""}>${e(this.typeLabel(t))}</option>`).join("");
        return `<div class="row"><div class="n">${e(x.name)}<small>${e(id)}</small></div><select data-type="${e(id)}" title="${e(this._t("type"))}">${options}</select><button class="x" data-remove="${e(id)}" title="${e(this._t("remove"))}">✕</button></div>`;
      })
      .join("");
    const hasVibration = d.entities.some((id) => d.types[id] === "vibration");
    const vib = hasVibration
      ? `<div class="box"><b>${e(this._t("vibTitle"))}</b><div class="muted">${e(this._t("vibText"))}</div>
          <div class="inline"><div><label>${e(this._t("vibCount"))}</label><input class="small" type="number" min="1" max="5" data-f="vibration_count" value="${e(d.vibration_count)}"></div>
          <div><label>${e(this._t("vibWindow"))}</label><input class="small" type="number" min="5" max="600" data-f="vibration_window" value="${e(d.vibration_window)}"></div>
          <div><button class="b" data-a="recommend">${e(this._t("vibRecommend"))}</button></div></div>
          ${this._err("vibration_count")}${this._err("vibration_window")}</div>`
      : "";
    const labels = `<select data-f="label"><option value="">${e(this._t("noLabel"))}</option>${(this.settings.labels || []).map((l) => `<option value="${e(l.id)}" ${l.id === d.label ? "selected" : ""}>${e(l.name)}</option>`).join("")}</select>`;
    return `
      <h2>${e(d.id ? this._t("groupEdit") : this._t("groupNew"))}</h2>
      <label>${e(this._t("name"))}</label><input data-f="name" value="${e(d.name)}">${this._err("name")}
      <label>${e(this._t("members"))}</label>${members || `<div class="muted">${e(this._t("noMembers"))}</div>`}${this._err("base")}${this._err("types")}
      <label>${e(this._t("add"))}</label>${this._pickerHtml(SENSOR_DOMAINS, d.entities, special)}
      <label>${e(this._t("label"))}</label>${labels}
      ${vib}`;
  }

  _knownValues(entityId, attribute) {
    const st = this.hass.states[entityId];
    const values = [];
    if (st) {
      if (attribute) {
        if (st.attributes[attribute] != null) values.push(String(st.attributes[attribute]));
      } else {
        if (Array.isArray(st.attributes.options)) values.push(...st.attributes.options.map(String));
        if (!["unknown", "unavailable", ""].includes(st.state)) values.push(st.state);
      }
    }
    for (const v of Object.keys(this._draft.map)) values.push(v);
    return [...new Set(values)];
  }

  _tiltForm() {
    const d = this._draft;
    const values = d.entity ? this._knownValues(d.entity, d.attribute) : [];
    for (const v of values) {
      if (!(v in d.map)) {
        const low = v.toLowerCase();
        d.map[v] = KNOWN_CLOSED.includes(low) ? "closed" : KNOWN_TILTED.includes(low) ? "tilted" : "open";
      }
    }
    const rows = values
      .map(
        (v) => `<div class="row"><div class="n">${e(v)}</div><select data-value="${e(v)}">${["open", "tilted", "closed"].map((k) => `<option value="${k}" ${d.map[v] === k ? "selected" : ""}>${e(this._t(k === "open" ? "valueOpen" : k === "tilted" ? "valueTilted" : "valueClosed"))}</option>`).join("")}</select></div>`
      )
      .join("");
    const source = d.entity
      ? `<div class="row"><div class="n">${e(this._entity(d.entity).name)}<small>${e(d.entity)}</small></div>${d.existing ? "" : `<button class="x" data-a="clear-entity">✕</button>`}</div>`
      : this._pickerHtml(TILT_DOMAINS, []);
    return `
      <h2>${e(this._t("tiltNew"))}</h2>
      <label>${e(this._t("tiltEntity"))}</label>${source}${this._err("entity")}
      <label>${e(this._t("attribute"))}</label><input data-f="attribute" value="${e(d.attribute)}">
      <label>${e(this._t("values"))}</label>${rows || `<div class="muted">${e(this._t("noValues"))}</div>`}
      <input data-f="more" placeholder="${e(this._t("moreValue"))}">${this._err("closed")}${this._err("tilted")}
      ${d.existing ? "" : `<label>${e(this._t("group"))}</label>${this._groupSelect("group", d.group)}`}`;
  }

  _strengthForm() {
    const d = this._draft;
    const st = d.entity && this.hass.states[d.entity];
    const source = d.entity
      ? `<div class="row"><div class="n">${e(this._entity(d.entity).name)}<small>${e(d.entity)} · ${e(this._t("current"))}: ${e(st ? st.state : "–")}</small></div>${d.existing ? "" : `<button class="x" data-a="clear-entity">✕</button>`}</div>`
      : this._pickerHtml(STRENGTH_DOMAINS, []);
    return `
      <h2>${e(this._t("strengthNew"))}</h2>
      <label>${e(this._t("strengthEntity"))}</label>${source}${this._err("entity")}
      <label>${e(this._t("threshold"))}</label><input class="small" type="number" step="any" data-f="threshold" value="${e(d.threshold)}">${this._err("threshold")}
      ${d.existing ? "" : `<label>${e(this._t("group"))}</label>${this._groupSelect("group", d.group)}`}`;
  }

  _alwaysForm() {
    const d = this._draft;
    const groups = this.settings.groups
      .map((g) => `<div class="chk"><input type="checkbox" data-zone="${e(g.id)}" ${d.zones.includes(g.id) ? "checked" : ""}><span>${e(g.name)}</span></div>`)
      .join("");
    const sensors = d.sensors
      .map((id) => `<div class="row"><div class="n">${e(this._entity(id).name)}<small>${e(id)}</small></div><button class="x" data-remove="${e(id)}">✕</button></div>`)
      .join("");
    return `
      <h2>${e(this._t("alwaysTitle"))}</h2><div class="muted">${e(this._t("alwaysText"))}</div>
      <label>${e(this._t("alwaysGroups"))}</label>${groups || "–"}
      <label>${e(this._t("alwaysSensors"))}</label>${sensors}
      ${this._pickerHtml(SENSOR_DOMAINS, d.sensors)}${this._err("base")}`;
  }

  // --- Lesen, Speichern -----------------------------------------------------------

  _collect() {
    const root = this.shadowRoot;
    const d = this._draft;
    root.querySelectorAll("[data-f]").forEach((el) => {
      const key = el.dataset.f;
      if (key !== "more") d[key] = el.value;
    });
    root.querySelectorAll("[data-type]").forEach((el) => {
      d.types[el.dataset.type] = el.value;
    });
    root.querySelectorAll("[data-value]").forEach((el) => {
      d.map[el.dataset.value] = el.value;
    });
    if (this.kind === "always") {
      d.zones = [...root.querySelectorAll("[data-zone]")].filter((el) => el.checked).map((el) => el.dataset.zone);
    }
  }

  _payload() {
    const d = this._draft;
    if (this.kind === "group") {
      const types = {};
      for (const id of d.entities) types[id] = d.types[id];
      const data = { id: d.id, name: d.name, entities: d.entities, label: d.label || null, types };
      if (d.entities.some((id) => d.types[id] === "vibration")) {
        data.vibration_count = Number(d.vibration_count);
        data.vibration_window = Number(d.vibration_window);
      }
      return ["group_save", data];
    }
    if (this.kind === "tilt") {
      const closed = Object.keys(d.map).filter((v) => d.map[v] === "closed");
      const tilted = Object.keys(d.map).filter((v) => d.map[v] === "tilted");
      return ["tilt_save", { entity: d.entity, attribute: d.attribute || null, closed, tilted, group: d.group || null }];
    }
    if (this.kind === "strength") {
      return ["strength_save", { entity: d.entity, threshold: d.threshold === "" ? null : Number(d.threshold), group: d.group || null }];
    }
    return ["always_save", { zones: d.zones, sensors: d.sensors }];
  }

  async _apply(action, data) {
    this._busy = true;
    this._render();
    let result;
    try {
      result = await this.hass.callWS({ type: "hauswacht/settings/apply", revision: this.settings.revision, action, data });
    } catch (err) {
      result = { ok: false, errors: { base: "failed" }, message: err?.message };
    }
    this._busy = false;
    if (result.ok) {
      this.dispatchEvent(new CustomEvent("hw-saved", { bubbles: true, composed: true }));
      return;
    }
    this._errors = result.errors || { base: "failed" };
    this._details = result.details || {};
    if (this._errors.base === "changed_elsewhere") {
      this.dispatchEvent(new CustomEvent("hw-stale", { bubbles: true, composed: true }));
    }
    this._render();
  }

  _deleteAction() {
    if (this.kind === "group" && this._draft.id) return ["group_delete", { id: this._draft.id }];
    if (this.kind === "tilt" && this._draft.existing) return ["tilt_delete", { entity: this._draft.entity }];
    if (this.kind === "strength" && this._draft.existing) return ["strength_delete", { entity: this._draft.entity }];
    return null;
  }

  _render() {
    const body =
      this.kind === "group" ? this._groupForm() : this.kind === "tilt" ? this._tiltForm() : this.kind === "strength" ? this._strengthForm() : this._alwaysForm();
    const del = this._deleteAction();
    this.shadowRoot.innerHTML = `<style>${EDIT_STYLE}</style><div class="sheet">${body}
      <div class="bar"><button class="b p" data-a="save" ${this._busy ? "disabled" : ""}>${e(this._busy ? this._t("saving") : this._t("save"))}</button>
      <button class="b" data-a="cancel">${e(this._t("cancel"))}</button>
      ${del ? `<button class="b d" data-a="delete">${e(this._t("delete"))}</button>` : ""}</div></div>`;
    this._wire();
  }

  _rerender(focusQuery = false) {
    this._collect();
    this._render();
    if (focusQuery) {
      const q = this.shadowRoot.querySelector("input.q");
      if (q) {
        q.focus();
        q.setSelectionRange(q.value.length, q.value.length);
      }
    }
  }

  _wire() {
    const root = this.shadowRoot;
    // Klick neben das Blatt schließt es
    this.onclick = (ev) => {
      if (ev.composedPath()[0] === this) this._close();
    };
    root.querySelectorAll("[data-a]").forEach((btn) =>
      btn.addEventListener("click", () => {
        const a = btn.dataset.a;
        if (a === "cancel") this._close();
        else if (a === "save") {
          this._collect();
          this._apply(...this._payload());
        } else if (a === "delete") {
          if (window.confirm(this._t("deleteConfirm"))) this._apply(...this._deleteAction());
        } else if (a === "recommend") {
          this._collect();
          this._draft.vibration_count = 2;
          this._draft.vibration_window = 60;
          this._render();
        } else if (a === "clear-entity") {
          this._collect();
          this._draft.entity = "";
          this._draft.map = {};
          this._render();
        }
      })
    );
    const q = root.querySelector("input.q");
    if (q) {
      q.addEventListener("input", () => {
        this._query = q.value;
        this._rerender(true);
      });
    }
    root.querySelectorAll("[data-pick]").forEach((el) =>
      el.addEventListener("click", () => {
        this._collect();
        const id = el.dataset.pick;
        const d = this._draft;
        if (this.kind === "group") {
          d.entities.push(id);
          d.types[id] = this.settings.sensor_types[id] || this._entity(id).suggested || "other";
          if (this.settings.tilt.some((x) => x.entity === id)) d.types[id] = "window";
          if (this.settings.strength.some((x) => x.entity === id)) d.types[id] = "vibration";
        } else if (this.kind === "always") d.sensors.push(id);
        else d.entity = id;
        this._query = "";
        this._render();
      })
    );
    root.querySelectorAll("[data-remove]").forEach((el) =>
      el.addEventListener("click", () => {
        this._collect();
        const id = el.dataset.remove;
        if (this.kind === "group") this._draft.entities = this._draft.entities.filter((x) => x !== id);
        else this._draft.sensors = this._draft.sensors.filter((x) => x !== id);
        this._render();
      })
    );
    root.querySelectorAll("[data-type]").forEach((el) => el.addEventListener("change", () => this._rerender()));
    const attr = root.querySelector('[data-f="attribute"]');
    if (attr && this.kind === "tilt") attr.addEventListener("change", () => this._rerender());
    const more = root.querySelector('[data-f="more"]');
    if (more) {
      more.addEventListener("keydown", (ev) => {
        if (ev.key !== "Enter" || !more.value.trim()) return;
        ev.preventDefault();
        this._collect();
        const v = more.value.trim();
        const low = v.toLowerCase();
        this._draft.map[v] = KNOWN_CLOSED.includes(low) ? "closed" : KNOWN_TILTED.includes(low) ? "tilted" : "open";
        this._render();
      });
    }
  }

  _close() {
    this.dispatchEvent(new CustomEvent("hw-close", { bubbles: true, composed: true }));
  }
}

if (!customElements.get("hauswacht-sensor-editor")) {
  customElements.define("hauswacht-sensor-editor", HauswachtSensorEditor);
}
