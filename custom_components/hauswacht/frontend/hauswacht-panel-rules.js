// Hauswacht – Einstellungsseite: Auslöseregeln bearbeiten (ADR 0011).
//
// Seitenblatt <hauswacht-rule-editor> mit Umschalter Formular / YAML. Einfache Regeln gehen im
// Formular, komplexe (verschachtelte Ausdrücke) nur als YAML. Das Umwandeln und Prüfen macht
// Hauswacht selbst (hauswacht/settings/rule_check) – dieselben Regeln wie im Dialog.
// Gespeichert wird über hauswacht/settings/apply (rule_save, rule_delete).

const RT = {
  de: {
    titleNew: "Auslöseregel anlegen",
    titleEdit: "Auslöseregel bearbeiten",
    form: "Formular",
    yaml: "YAML",
    onlyYaml: "Diese Regel ist zu komplex für das Formular (verschachtelte Ausdrücke) – bearbeiten nur als YAML.",
    sentence: "Das bewirkt die Regel",
    name: "Name",
    result: "Ergebnis",
    results: { alarm: "Sofort Alarm", entry_delay: "Eingangsverzögerung, dann Alarm", notify: "Nur Benachrichtigung" },
    step: "Schritt",
    mode: "Was muss passieren?",
    modes: { any: "einer davon", all: "alle davon (beliebige Reihenfolge)", count: "mindestens … davon" },
    count: "Wie viele?",
    groups: "Meldergruppen",
    sensors: "Einzelne Melder",
    addSensor: "Melder hinzufügen – Namen tippen oder aus der Liste wählen",
    within: "Zeit bis zum nächsten Schritt (Sekunden)",
    addStep: "+ Schritt",
    up: "nach oben",
    down: "nach unten",
    remove: "Schritt entfernen",
    unless: "Nicht, wenn vorher …",
    unlessHint: "Die Regel gilt nicht, wenn einer dieser Melder kurz vor Schritt 1 ausgelöst hat (z. B. Bewegung innen = jemand ist schon im Haus).",
    before: "Zeitraum davor (Sekunden)",
    conditions: "Bedingungen („nur wenn …“) – ändern nur im YAML",
    profiles: "Gilt in den Profilen",
    noProfiles: "Noch in keinem Profil – dann wirkt die Regel nicht.",
    yamlHint: "Gruppen per Name, Melder per Entitäts-ID. Aufbau siehe Doku „Auslöseregeln“.",
    save: "Speichern",
    saving: "Speichere …",
    cancel: "Abbrechen",
    del: "Löschen",
    delSure: "Wirklich löschen?",
    stayYaml: "Zurück zum Formular geht nicht:",
    none: "–",
    errors: {
      rule_name_required: "Bitte einen Namen eingeben.",
      rule_name_taken: "Eine Auslöseregel mit diesem Namen gibt es schon.",
      disarm_first: "Erst alle Bereiche unscharf schalten – dann lässt sich speichern.",
      changed_elsewhere: "Inzwischen wurde woanders etwas geändert. Die Seite lädt neu – bitte noch einmal.",
      failed: "Speichern fehlgeschlagen.",
    },
  },
  en: {
    titleNew: "Add trigger rule",
    titleEdit: "Edit trigger rule",
    form: "Form",
    yaml: "YAML",
    onlyYaml: "This rule is too complex for the form (nested expressions) – edit it as YAML only.",
    sentence: "What the rule does",
    name: "Name",
    result: "Result",
    results: { alarm: "Alarm immediately", entry_delay: "Entry delay, then alarm", notify: "Notification only" },
    step: "Step",
    mode: "What has to happen?",
    modes: { any: "one of them", all: "all of them (any order)", count: "at least … of them" },
    count: "How many?",
    groups: "Sensor groups",
    sensors: "Single sensors",
    addSensor: "Add sensor – type a name or pick from the list",
    within: "Time until the next step (seconds)",
    addStep: "+ Step",
    up: "move up",
    down: "move down",
    remove: "Remove step",
    unless: "Not if before …",
    unlessHint: "The rule does not apply if one of these sensors triggered shortly before step 1 (e.g. motion inside = someone is already home).",
    before: "Period before (seconds)",
    conditions: "Conditions (“only if …”) – change only in YAML",
    profiles: "Applies in the profiles",
    noProfiles: "Not in any profile yet – then the rule has no effect.",
    yamlHint: "Groups by name, sensors by entity ID. Structure: see docs “Trigger rules”.",
    save: "Save",
    saving: "Saving …",
    cancel: "Cancel",
    del: "Delete",
    delSure: "Really delete?",
    stayYaml: "Back to the form is not possible:",
    none: "–",
    errors: {
      rule_name_required: "Please enter a name.",
      rule_name_taken: "A trigger rule with this name already exists.",
      disarm_first: "Disarm all areas first – then saving works.",
      changed_elsewhere: "Something was changed elsewhere in the meantime. The page reloads – please try again.",
      failed: "Saving failed.",
    },
  },
};

const RULE_STYLE = `
  .switch { display: inline-flex; border: 1px solid var(--divider-color); border-radius: 18px; overflow: hidden; margin-bottom: 8px; }
  .switch button { font: inherit; font-size: .9rem; border: none; background: none; padding: 6px 16px; cursor: pointer; color: var(--primary-text-color); }
  .switch button.on { background: var(--primary-color); color: var(--text-primary-color, #fff); }
  .switch button:disabled { opacity: .4; cursor: default; }
  .sentence { border-left: 3px solid var(--primary-color); padding: 6px 10px; margin: 8px 0; background: var(--secondary-background-color); font-size: .95rem; }
  .step .head { display: flex; align-items: center; gap: 4px; }
  .step .head b { flex: 1; }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; margin: 4px 0; }
  .chip { display: inline-flex; align-items: center; gap: 2px; border: 1px solid var(--divider-color); border-radius: 14px; padding: 2px 4px 2px 10px; font-size: .9rem; }
  .chip .x { font-size: 1rem; padding: 0 4px; }
  textarea.y { font-family: var(--code-font-family, monospace); font-size: .9rem; width: 100%; min-height: 320px; box-sizing: border-box;
    padding: 8px 10px; border-radius: 6px; border: 1px solid var(--divider-color); background: var(--card-background-color); color: var(--primary-text-color); tab-size: 2; }
  .grid { display: flex; flex-wrap: wrap; gap: 0 16px; }
`;

const re = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

// --- Umwandeln: YAML-Form (wie im Dialog) <-> Formular ------------------------

function stepToForm(step, within) {
  const mode = "count" in step ? "count" : "all" in step ? "all" : "any";
  const items = mode === "count" ? step.of || [] : step[mode] || [];
  return {
    mode,
    count: mode === "count" ? Number(step.count) || 2 : 2,
    sensors: items.filter((i) => i && i.sensor).map((i) => i.sensor),
    groups: items.filter((i) => i && i.group).map((i) => i.group),
    within: Number(step.within ?? within) || within,
  };
}

function formToStep(form) {
  const items = [...form.sensors.map((s) => ({ sensor: s })), ...form.groups.map((g) => ({ group: g }))];
  const head = form.mode === "count" ? { count: Number(form.count) || 2, of: items } : { [form.mode]: items };
  return { ...head, within: Number(form.within) || 60 };
}

class HauswachtRuleEditor extends HTMLElement {
  // open({hass, settings, rule}) – rule: Eintrag aus settings.rule_edit.rules oder null (neu)
  open(options) {
    Object.assign(this, options);
    const edit = this.settings.rule_edit;
    this._limits = edit.rule_limits;
    this._choices = edit.rule_choices;
    this._errors = {};
    this._messages = [];
    this._busy = false;
    this._sure = false;
    const rule = this.rule;
    this._ruleId = rule ? rule.id : null;
    this._profiles = rule ? [...rule.profiles] : [];
    this._sentence = rule ? rule.text : "";
    this._uiPossible = rule ? rule.ui : true;
    this._yaml = rule ? rule.yaml : "";
    this._mode = this._uiPossible ? "ui" : "yaml";
    this._draft = this._toForm(
      rule ? rule.rule : { name: "", result: "alarm", steps: [{ any: [] }, { any: [] }] }
    );
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this._render();
  }

  get _lang() {
    return (this.hass?.language || "en").startsWith("de") ? "de" : "en";
  }

  _t(key) {
    return RT[this._lang][key] ?? RT.en[key] ?? key;
  }

  _toForm(rule) {
    const within = this._limits.default_within;
    const unless = rule.unless ? stepToForm(rule.unless, within) : null;
    return {
      name: rule.name || "",
      result: rule.result || "alarm",
      steps: (rule.steps || []).map((s) => stepToForm(s, within)),
      unless: unless ? { sensors: unless.sensors, groups: unless.groups, before: Number(rule.unless.before) || 300 } : null,
      conditions: rule.conditions || null,
    };
  }

  _fromForm() {
    const d = this._draft;
    const rule = { name: d.name, result: d.result, steps: d.steps.map(formToStep) };
    if (d.unless && (d.unless.sensors.length || d.unless.groups.length)) {
      rule.unless = {
        any: [...d.unless.sensors.map((s) => ({ sensor: s })), ...d.unless.groups.map((g) => ({ group: g }))],
        before: Number(d.unless.before) || 300,
      };
    }
    if (d.conditions && d.conditions.length) rule.conditions = d.conditions;
    return rule;
  }

  _skeleton() {
    // Vorlage, wenn das Formular noch nicht vollständig ist
    const group = this._choices.groups[0] || "…";
    return `name: ${this._draft.name || (this._lang === "de" ? "Neue Regel" : "New rule")}\nresult: ${this._draft.result}\nsteps:\n  - any:\n      - group: ${group}\n    within: 60\n  - any:\n      - sensor: binary_sensor.…\n    within: 60\n`;
  }

  _sensorName(id) {
    return (this._choices.sensors.find((s) => s.id === id) || { name: id }).name;
  }

  // --- Prüfen beim Bearbeiten ----------------------------------------------------

  async _check(payload) {
    try {
      return await this.hass.callWS({ type: "hauswacht/settings/rule_check", rule_id: this._ruleId, ...payload });
    } catch (_err) {
      return null;
    }
  }

  _payload() {
    return this._mode === "yaml" ? { yaml: this._yaml } : { rule: this._fromForm() };
  }

  _scheduleCheck() {
    clearTimeout(this._timer);
    this._timer = setTimeout(async () => {
      const result = await this._check(this._payload());
      if (!result) return;
      this._sentence = result.text || "";
      // Name fehlt beim Tippen: noch kein Hinweis – erst beim Speichern
      this._messages = result.messages || [];
      if (this._mode === "yaml") this._uiPossible = result.parsed ? !!result.ui : this._uiPossible;
      this._updateInfo();
    }, 450);
  }

  _updateInfo() {
    const root = this.shadowRoot;
    const box = root.querySelector("[data-info]");
    if (box) box.innerHTML = this._infoHtml();
    const formBtn = root.querySelector('[data-mode="ui"]');
    if (formBtn) formBtn.disabled = !this._uiPossible;
  }

  _infoHtml() {
    const sentence = this._sentence
      ? `<label>${re(this._t("sentence"))}</label><div class="sentence">${re(this._sentence)}</div>`
      : "";
    const messages = this._messages.map((m) => `<div class="err">⚠️ ${re(m)}</div>`).join("");
    return sentence + messages;
  }

  async _switchMode(mode) {
    if (mode === this._mode) return;
    this._collect();
    if (mode === "yaml") {
      const result = await this._check({ rule: this._fromForm() });
      this._yaml = result && result.parsed ? result.yaml : this._skeleton();
      this._mode = "yaml";
      this._render();
      return;
    }
    const result = await this._check({ yaml: this._yaml });
    if (!result || !result.parsed) {
      this._messages = [this._t("stayYaml"), ...((result && result.messages) || [])];
      this._updateInfo();
      return;
    }
    if (!result.ui) {
      this._uiPossible = false;
      this._messages = [this._t("onlyYaml")];
      this._render();
      return;
    }
    this._draft = this._toForm(result.rule);
    this._sentence = result.text || "";
    this._messages = result.messages || [];
    this._mode = "ui";
    this._render();
  }

  // --- Formular ------------------------------------------------------------------

  _checks(attr, chosen, items) {
    return items.length
      ? `<div class="grid">${items.map(([v, l]) => `<div class="chk"><input type="checkbox" ${attr}="${re(v)}" ${chosen.includes(v) ? "checked" : ""}><span>${re(l)}</span></div>`).join("")}</div>`
      : `<div class="muted">${re(this._t("none"))}</div>`;
  }

  _sensorChips(where, list) {
    const chips = list.map((id, i) => `<span class="chip" title="${re(id)}">${re(this._sensorName(id))}<button class="x" data-rm="${where}:${i}">✕</button></span>`).join("");
    return `<div class="chips">${chips}</div><input list="hw-rule-sensors" data-add="${where}" placeholder="${re(this._t("addSensor"))}">`;
  }

  _stepHtml(step, i, total) {
    const groups = this._choices.groups.map((g) => [g, g]);
    const modes = Object.entries(this._t("modes"))
      .map(([v, l]) => `<option value="${v}" ${step.mode === v ? "selected" : ""}>${re(l)}</option>`)
      .join("");
    return `<div class="box step">
      <div class="head"><b>${re(this._t("step"))} ${i + 1}</b>
        ${i > 0 ? `<button class="x" title="${re(this._t("up"))}" data-move="${i}:-1">↑</button>` : ""}
        ${i < total - 1 ? `<button class="x" title="${re(this._t("down"))}" data-move="${i}:1">↓</button>` : ""}
        ${total > 1 ? `<button class="x" title="${re(this._t("remove"))}" data-remove-step="${i}">✕</button>` : ""}</div>
      <label>${re(this._t("mode"))}</label>
      <div class="inline"><div><select data-s="${i}:mode">${modes}</select></div>
        ${step.mode === "count" ? `<div><input class="small" type="number" min="1" max="99" data-s="${i}:count" value="${re(step.count)}"></div>` : ""}</div>
      <label>${re(this._t("groups"))}</label>${this._checks(`data-sg="${i}" data-v`, step.groups, groups)}
      <label>${re(this._t("sensors"))}</label>${this._sensorChips(`s${i}`, step.sensors)}
      ${i < total - 1 ? `<label>${re(this._t("within"))}</label><input class="small" type="number" min="1" max="${this._limits.within}" data-s="${i}:within" value="${re(step.within)}">` : ""}
    </div>`;
  }

  _formHtml() {
    const d = this._draft;
    const results = Object.entries(this._t("results"))
      .map(([v, l]) => `<option value="${v}" ${d.result === v ? "selected" : ""}>${re(l)}</option>`)
      .join("");
    const steps = d.steps.map((s, i) => this._stepHtml(s, i, d.steps.length)).join("");
    const canAdd = d.steps.length < this._limits.steps;
    const u = d.unless;
    const unless = `<div class="box">
      <div class="chk"><input type="checkbox" data-unless ${u ? "checked" : ""}><span><b>${re(this._t("unless"))}</b></span></div>
      <div class="muted">${re(this._t("unlessHint"))}</div>
      ${u ? `<label>${re(this._t("groups"))}</label>${this._checks('data-ug="1" data-v', u.groups, this._choices.groups.map((g) => [g, g]))}
        <label>${re(this._t("sensors"))}</label>${this._sensorChips("u", u.sensors)}
        <label>${re(this._t("before"))}</label><input class="small" type="number" min="1" max="${this._limits.unless}" data-ub value="${re(u.before)}">` : ""}
    </div>`;
    const conditions = d.conditions && d.conditions.length
      ? `<div class="box"><b>${re(this._t("conditions"))}</b><pre class="muted">${re(JSON.stringify(d.conditions, null, 1))}</pre></div>`
      : "";
    return `
      <label>${re(this._t("name"))}</label><input data-f="name" value="${re(d.name)}">${this._err("name")}
      <label>${re(this._t("result"))}</label><select data-f="result">${results}</select>
      ${steps}
      ${canAdd ? `<div class="tool" style="margin-top:8px"><button class="b" data-act="add-step">${re(this._t("addStep"))}</button></div>` : ""}
      ${unless}${conditions}`;
  }

  _yamlHtml() {
    return `${this._uiPossible ? "" : `<div class="muted">${re(this._t("onlyYaml"))}</div>`}
      <div class="muted">${re(this._t("yamlHint"))}</div>
      <textarea class="y" spellcheck="false" data-yaml>${re(this._yaml)}</textarea>${this._err("name")}`;
  }

  _err(key) {
    const k = this._errors[key];
    return k ? `<div class="err">${re(this._t("errors")[k] || k)}</div>` : "";
  }

  _collect() {
    if (this._mode === "yaml") {
      const area = this.shadowRoot.querySelector("[data-yaml]");
      if (area) this._yaml = area.value;
      return;
    }
    const root = this.shadowRoot;
    const d = this._draft;
    const name = root.querySelector('[data-f="name"]');
    if (name) d.name = name.value;
    const result = root.querySelector('[data-f="result"]');
    if (result) d.result = result.value;
    root.querySelectorAll("[data-s]").forEach((el) => {
      const [i, key] = el.dataset.s.split(":");
      d.steps[Number(i)][key] = key === "mode" ? el.value : Number(el.value);
    });
    d.steps.forEach((step, i) => {
      step.groups = [...root.querySelectorAll(`[data-sg="${i}"]`)].filter((el) => el.checked).map((el) => el.dataset.v);
    });
    if (d.unless) {
      d.unless.groups = [...root.querySelectorAll('[data-ug="1"]')].filter((el) => el.checked).map((el) => el.dataset.v);
      const before = root.querySelector("[data-ub]");
      if (before) d.unless.before = Number(before.value);
    }
  }

  _collectProfiles() {
    const boxes = this.shadowRoot.querySelectorAll("[data-p]");
    if (boxes.length) this._profiles = [...boxes].filter((el) => el.checked).map((el) => el.dataset.p);
  }

  _addSensor(where, value) {
    const id = value.trim();
    const match = this._choices.sensors.find((s) => s.id === id || s.name.toLowerCase() === id.toLowerCase());
    if (!match) return false;
    const list = where === "u" ? this._draft.unless.sensors : this._draft.steps[Number(where.slice(1))].sensors;
    if (!list.includes(match.id)) list.push(match.id);
    return true;
  }

  // --- Speichern, Löschen ------------------------------------------------------------

  async _apply(action, data) {
    this._busy = true;
    this._render();
    let result;
    try {
      result = await this.hass.callWS({ type: "hauswacht/settings/apply", revision: this.settings.revision, action, data });
    } catch (_err) {
      result = { ok: false, errors: { base: "failed" } };
    }
    this._busy = false;
    if (result.ok) {
      this.dispatchEvent(new CustomEvent("hw-saved", { bubbles: true, composed: true, detail: { revision: result.revision } }));
      return;
    }
    this._errors = result.errors || { base: "failed" };
    const base = this._errors.base;
    if (base === "changed_elsewhere") this.dispatchEvent(new CustomEvent("hw-stale", { bubbles: true, composed: true }));
    if (base && this._t("errors")[base]) {
      this._messages = [this._t("errors")[base]];
    } else if (base) {
      // Texte der Prüfung holen (dieselben wie im Dialog)
      const check = await this._check(this._payload());
      this._messages = (check && check.messages) || [base];
    }
    this._render();
    window.HauswachtRevealError?.(this.shadowRoot); // Fehlermeldung ins Bild holen
  }

  _save() {
    this._collect();
    this._collectProfiles();
    this._errors = {};
    this._apply("rule_save", { id: this._ruleId, ...this._payload(), profiles: this._profiles });
  }

  // --- Zeichnen ------------------------------------------------------------------

  _render() {
    const top = this.shadowRoot.querySelector(".sheet")?.scrollTop || 0;
    const profiles = this._choices.profiles.map((p) => [p.id, p.name]);
    const body = this._mode === "yaml" ? this._yamlHtml() : this._formHtml();
    this.shadowRoot.innerHTML = `<style>${(window.HauswachtEditStyle || "") + RULE_STYLE}</style><div class="sheet">
      <h2>${re(this._ruleId ? this._t("titleEdit") : this._t("titleNew"))}</h2>
      <div class="switch"><button data-mode="ui" class="${this._mode === "ui" ? "on" : ""}" ${this._uiPossible ? "" : "disabled"}>${re(this._t("form"))}</button><button data-mode="yaml" class="${this._mode === "yaml" ? "on" : ""}">${re(this._t("yaml"))}</button></div>
      <div data-info>${this._infoHtml()}</div>
      ${body}
      <label>${re(this._t("profiles"))}</label>${this._checks("data-p", this._profiles, profiles)}
      ${this._profiles.length ? "" : `<div class="muted">${re(this._t("noProfiles"))}</div>`}
      <datalist id="hw-rule-sensors">${this._choices.sensors.map((s) => `<option value="${re(s.id)}">${re(s.name)}</option>`).join("")}</datalist>
      <div class="bar"><button class="b p" data-act="save" ${this._busy ? "disabled" : ""}>${re(this._busy ? this._t("saving") : this._t("save"))}</button>
        <button class="b" data-act="cancel">${re(this._t("cancel"))}</button>
        ${this._ruleId ? `<button class="b d" data-act="delete">${re(this._sure ? this._t("delSure") : this._t("del"))}</button>` : ""}</div>
    </div>`;
    this.shadowRoot.querySelector(".sheet").scrollTop = top;
    window.HauswachtDocs?.decorate(this.shadowRoot, this._mode === "yaml" ? "rulesYaml" : "rules", this._lang);
    this._wire();
    if (!this._checkedOnce) {
      this._checkedOnce = true;
      this._scheduleCheck();
    }
  }

  _wire() {
    const root = this.shadowRoot;
    this.onclick = (ev) => {
      if (ev.composedPath()[0] === this) this._close();
    };
    const redraw = () => {
      this._collect();
      this._collectProfiles();
      this._render();
      this._scheduleCheck();
    };
    root.querySelector('[data-act="cancel"]').addEventListener("click", () => this._close());
    root.querySelector('[data-act="save"]').addEventListener("click", () => this._save());
    const del = root.querySelector('[data-act="delete"]');
    if (del) {
      del.addEventListener("click", () => {
        if (!this._sure) {
          this._sure = true;
          this._collect();
          this._collectProfiles();
          this._render();
          return;
        }
        this._apply("rule_delete", { id: this._ruleId });
      });
    }
    root.querySelectorAll("[data-mode]").forEach((el) =>
      el.addEventListener("click", () => {
        this._collectProfiles();
        this._switchMode(el.dataset.mode);
      })
    );
    const add = root.querySelector('[data-act="add-step"]');
    if (add) {
      add.addEventListener("click", () => {
        this._collect();
        this._draft.steps.push({ mode: "any", count: 2, sensors: [], groups: [], within: this._limits.default_within });
        redraw();
      });
    }
    root.querySelectorAll("[data-move]").forEach((el) =>
      el.addEventListener("click", () => {
        this._collect();
        const [i, dir] = el.dataset.move.split(":").map(Number);
        const steps = this._draft.steps;
        [steps[i], steps[i + dir]] = [steps[i + dir], steps[i]];
        redraw();
      })
    );
    root.querySelectorAll("[data-remove-step]").forEach((el) =>
      el.addEventListener("click", () => {
        this._collect();
        this._draft.steps.splice(Number(el.dataset.removeStep), 1);
        redraw();
      })
    );
    root.querySelectorAll("[data-rm]").forEach((el) =>
      el.addEventListener("click", () => {
        this._collect();
        const [where, index] = el.dataset.rm.split(":");
        const list = where === "u" ? this._draft.unless.sensors : this._draft.steps[Number(where.slice(1))].sensors;
        list.splice(Number(index), 1);
        redraw();
      })
    );
    root.querySelectorAll("[data-add]").forEach((el) =>
      el.addEventListener("change", () => {
        this._collect();
        if (this._addSensor(el.dataset.add, el.value)) redraw();
      })
    );
    const unless = root.querySelector("[data-unless]");
    if (unless) {
      unless.addEventListener("change", () => {
        this._collect();
        this._draft.unless = unless.checked ? { sensors: [], groups: [], before: 300 } : null;
        redraw();
      });
    }
    // Auswahl "mindestens … davon" braucht das Zahlenfeld
    root.querySelectorAll('[data-s$=":mode"]').forEach((el) => el.addEventListener("change", redraw));
    root.querySelectorAll("[data-p]").forEach((el) => el.addEventListener("change", redraw));
    // Alles andere: nur neu prüfen, nicht neu zeichnen (Cursor bleibt)
    root.querySelectorAll("input, select, textarea").forEach((el) => {
      if (el.matches("[data-add], [data-unless], [data-p], [data-s$=':mode']")) return;
      el.addEventListener("input", () => {
        this._collect();
        this._scheduleCheck();
      });
      el.addEventListener("change", () => {
        this._collect();
        this._scheduleCheck();
      });
    });
  }

  _close() {
    clearTimeout(this._timer);
    this.dispatchEvent(new CustomEvent("hw-close", { bubbles: true, composed: true }));
  }
}

if (!customElements.get("hauswacht-rule-editor")) {
  customElements.define("hauswacht-rule-editor", HauswachtRuleEditor);
}
