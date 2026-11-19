// Hauswacht – Einstellungsseite, Stufe 3: Alarmprofile bearbeiten (ADR 0011).
//
// Seitenblatt <hauswacht-profile-editor> mit allen Einstellungen eines Profils, in Abschnitten
// wie im Dialog. Gespeichert wird über hauswacht/settings/apply (save_profile – dieselbe
// Prüfung wie im Dialog). Nur stabile Bausteine: eigene Elemente, Farben des Themas.

const PT = {
  de: {
    titleNew: "Alarmprofil anlegen",
    titleEdit: "Alarmprofil bearbeiten",
    save: "Speichern",
    saving: "Speichere …",
    cancel: "Abbrechen",
    delete: "Löschen",
    deleteConfirm: "Profil wirklich löschen?",
    secGeneral: "Allgemein",
    secWatch: "Was wird überwacht",
    secTimes: "Zeiten",
    secArming: "Beim Scharfschalten",
    secReaction: "Reaktion bei Alarm",
    secAuto: "Automatik",
    secClose: "Scharf durch Schließen der Tür",
    name: "Name",
    icon: "Symbol (z. B. mdi:weather-night)",
    button: "Knopf am Bedienfeld",
    area: "Bereich",
    zones: "Meldergruppen – jeder Melder löst allein aus",
    excluded: "Ausgenommen (lösen in diesem Profil nicht allein aus)",
    noMembers: "Erst Meldergruppen wählen.",
    rules: "Auslöseregeln",
    tilt: "Gekippte Fenster erlaubt (gekippt zählt als zu, erst ganz öffnen löst aus)",
    exit: "Ausgangsverzögerung (s)",
    entry: "Eingangsverzögerung (s)",
    reaction: "Dauer der Alarmreaktion (s)",
    cycles: "Höchstzahl Alarmzyklen",
    openPolicy: "Offene Melder beim Scharfschalten",
    unavailablePolicy: "Ausgefallene Melder beim Scharfschalten",
    tamper: "Manipulation (Sabotage) löst Alarm aus",
    sirens: "Sirenen",
    noSirens: "Keine Sirenen eingetragen (Reiter Alarmgeber).",
    tone: "Ton",
    volume: "Lautstärke",
    silent: "Stiller Alarm (keine Sirene, nur Benachrichtigung)",
    notify: "Benachrichtigen bei Alarm",
    speakers: "Zusätzliche Lautsprecher (Ansagen)",
    armTime: "Scharf um",
    disarmTime: "Unscharf um",
    weekdays: "An diesen Tagen (keiner = täglich)",
    schedule: "Oder nach Zeitplan",
    noSchedule: "– kein Zeitplan –",
    scheduleCreate: "Zeitplan anlegen ↗",
    scheduleHint: "Öffnet die Helfer in einem neuen Fenster: „Helfer erstellen“ → „Zeitplan“. Danach hier „Liste aktualisieren“ – deine Eingaben bleiben erhalten.",
    refreshLists: "↻ Liste aktualisieren",
    persons: "Scharf, wenn alle diese Personen weg sind",
    awayDelay: "Wartezeit, wenn alle weg sind (min)",
    arrival: "Unscharf bei Rückkehr",
    arrivalWindow: "Türbeleg: Rückkehr bis Türöffnung (min)",
    closeOn: "Ausgangsverzögerung endet, sobald die Tür zu ist",
    doors: "Ausgangstüren",
    noDoors: "In den gewählten Gruppen gibt es keine Melder vom Typ Tür.",
    settle: "Beruhigungszeit (s)",
    none: "–",
    modes: { none: "kein Knopf", home: "Zuhause", night: "Nacht", away: "Abwesend", vacation: "Urlaub", custom: "Benutzerdefiniert" },
    policy: { refuse: "verweigern", confirm: "nach Bestätigung erlauben", bypass_auto: "automatisch überbrücken" },
    experts: " (Experten – wird wieder überwacht, sobald er sich meldet)",
    tones: { burglar: "Einbruch", emergency: "Notfall", police_panic: "Polizei-Panik", emergency_panic: "Notfall-Panik" },
    volumes: { low: "leise", medium: "mittel", high: "laut", very_high: "sehr laut" },
    days: { mon: "Mo", tue: "Di", wed: "Mi", thu: "Do", fri: "Fr", sat: "Sa", sun: "So" },
    arrivalModes: { off: "aus", auto_only: "wie bisher (Anwesenheit)", door: "mit Türbeleg" },
    errors: {
      profile_name_required: "Bitte einen Namen eingeben.",
      profile_name_taken: "Diesen Namen gibt es schon.",
      panel_mode_taken: "Diesen Knopf hat in diesem Bereich schon ein anderes Profil.",
      excluded_not_in_groups: "Ausgenommene Melder müssen in den gewählten Gruppen sein.",
      arrival_needs_persons: "„Unscharf bei Rückkehr“ braucht Personen.",
      unknown_profile: "Dieses Profil gibt es nicht mehr.",
      disarm_first: "Erst alle Bereiche unscharf schalten – dann lässt sich speichern.",
      changed_elsewhere: "Inzwischen wurde woanders etwas geändert. Die Seite lädt neu – bitte noch einmal.",
      failed: "Speichern fehlgeschlagen.",
    },
  },
  en: {
    titleNew: "Add alarm profile",
    titleEdit: "Edit alarm profile",
    save: "Save",
    saving: "Saving …",
    cancel: "Cancel",
    delete: "Delete",
    deleteConfirm: "Really delete the profile?",
    secGeneral: "General",
    secWatch: "What is monitored",
    secTimes: "Times",
    secArming: "When arming",
    secReaction: "Reaction on alarm",
    secAuto: "Automation",
    secClose: "Arm by closing the door",
    name: "Name",
    icon: "Icon (e.g. mdi:weather-night)",
    button: "Button on the alarm panel",
    area: "Area",
    zones: "Sensor groups – every sensor triggers on its own",
    excluded: "Excluded (do not trigger on their own in this profile)",
    noMembers: "Choose sensor groups first.",
    rules: "Trigger rules",
    tilt: "Tilted windows allowed (tilted counts as closed, only opening fully triggers)",
    exit: "Exit delay (s)",
    entry: "Entry delay (s)",
    reaction: "Duration of the alarm reaction (s)",
    cycles: "Maximum alarm cycles",
    openPolicy: "Open sensors when arming",
    unavailablePolicy: "Failed sensors when arming",
    tamper: "Tampering triggers an alarm",
    sirens: "Sirens",
    noSirens: "No sirens registered (tab alarm devices).",
    tone: "Tone",
    volume: "Volume",
    silent: "Silent alarm (no siren, notification only)",
    notify: "Notify on alarm",
    speakers: "Additional speakers (announcements)",
    armTime: "Arm at",
    disarmTime: "Disarm at",
    weekdays: "On these days (none = daily)",
    schedule: "Or by schedule",
    noSchedule: "– no schedule –",
    scheduleCreate: "Create schedule ↗",
    scheduleHint: "Opens the helpers in a new window: “Create helper” → “Schedule”. Then “Refresh list” here – your entries are kept.",
    refreshLists: "↻ Refresh list",
    persons: "Arm when all these persons are away",
    awayDelay: "Waiting time when everyone is away (min)",
    arrival: "Disarm on arrival",
    arrivalWindow: "Door proof: arrival until door opening (min)",
    closeOn: "Exit delay ends as soon as the door is closed",
    doors: "Exit doors",
    noDoors: "The chosen groups contain no sensors of type door.",
    settle: "Settle time (s)",
    none: "–",
    modes: { none: "no button", home: "Home", night: "Night", away: "Away", vacation: "Vacation", custom: "Custom" },
    policy: { refuse: "refuse", confirm: "allow after confirmation", bypass_auto: "bypass automatically" },
    experts: " (experts – monitored again as soon as it reports)",
    tones: { burglar: "Burglar", emergency: "Emergency", police_panic: "Police panic", emergency_panic: "Emergency panic" },
    volumes: { low: "low", medium: "medium", high: "high", very_high: "very high" },
    days: { mon: "Mon", tue: "Tue", wed: "Wed", thu: "Thu", fri: "Fri", sat: "Sat", sun: "Sun" },
    arrivalModes: { off: "off", auto_only: "as before (presence)", door: "with door proof" },
    errors: {
      profile_name_required: "Please enter a name.",
      profile_name_taken: "This name already exists.",
      panel_mode_taken: "Another profile in this area already has this button.",
      excluded_not_in_groups: "Excluded sensors must be in the chosen groups.",
      arrival_needs_persons: "“Disarm on arrival” needs persons.",
      unknown_profile: "This profile no longer exists.",
      disarm_first: "Disarm all areas first – then saving works.",
      changed_elsewhere: "Something was changed elsewhere in the meantime. The page reloads – please try again.",
      failed: "Saving failed.",
    },
  },
};

const PROFILE_STYLE = `
  .sec { font-weight: 500; margin: 18px 0 2px; padding-top: 10px; border-top: 1px solid var(--divider-color); }
  .two { display: grid; grid-template-columns: 1fr 1fr; gap: 0 12px; }
  .days { display: flex; gap: 10px; flex-wrap: wrap; }
  .days .chk { padding: 2px 0; }
  .tool { display: flex; gap: 8px; flex-wrap: wrap; }
  a.b { text-decoration: none; font-size: .9rem; padding: 6px 14px; }
`;

const pe = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

class HauswachtProfileEditor extends HTMLElement {
  // open({hass, settings, profile}) – profile = null: neues Profil
  open(options) {
    Object.assign(this, options);
    const edit = this.settings.profile_edit;
    const base = this.profile ? edit.profiles.find((p) => p.id === this.profile) : null;
    this._draft = JSON.parse(JSON.stringify(base || edit.defaults));
    this._errors = {};
    this._busy = false;
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this._render();
  }

  get _lang() {
    return (this.hass?.language || "en").startsWith("de") ? "de" : "en";
  }

  _t(key) {
    return PT[this._lang][key] ?? PT.en[key] ?? key;
  }

  _name(id) {
    const x = (this.settings.entities || []).find((y) => y.id === id);
    return x ? x.name : id;
  }

  // --- Bausteine ---------------------------------------------------------------

  _text(key, value, label) {
    return `<label>${pe(label)}</label><input data-k="${key}" value="${pe(value ?? "")}">${this._err(key)}`;
  }

  _num(key, value, label, min, max) {
    return `<div><label>${pe(label)}</label><input type="number" min="${min}" max="${max}" data-k="${key}" data-num="1" value="${pe(value)}"></div>`;
  }

  _select(key, value, label, options) {
    return `<label>${pe(label)}</label><select data-k="${key}">${options.map(([v, l]) => `<option value="${pe(v)}" ${v === value ? "selected" : ""}>${pe(l)}</option>`).join("")}</select>${this._err(key)}`;
  }

  _check(key, value, label) {
    return `<div class="chk"><input type="checkbox" data-k="${key}" data-bool="1" ${value ? "checked" : ""}><span>${pe(label)}</span></div>`;
  }

  _multi(key, chosen, items, label, empty) {
    const body = items.length
      ? items.map(([v, l]) => `<div class="chk"><input type="checkbox" data-m="${key}" value="${pe(v)}" ${chosen.includes(v) ? "checked" : ""}><span>${pe(l)}</span></div>`).join("")
      : `<div class="muted">${pe(empty || this._t("none"))}</div>`;
    return `<label>${pe(label)}</label>${body}${this._err(key)}`;
  }

  _err(key) {
    const k = this._errors[key];
    return k ? `<div class="err">${pe(this._t("errors")[k] || k)}</div>` : "";
  }

  _members(zones) {
    const s = this.settings;
    const ids = new Set();
    for (const g of s.groups) {
      if (!zones.includes(g.id)) continue;
      for (const id of g.entities || []) ids.add(id);
      for (const id of s.label_members?.[g.id] || []) ids.add(id);
    }
    return [...ids].sort((a, b) => this._name(a).localeCompare(this._name(b)));
  }

  // --- Formular ----------------------------------------------------------------

  _form() {
    const d = this._draft;
    const c = this.settings.profile_edit.choices;
    const lim = this.settings.profile_edit.limits;
    const a = d.automation;
    const close = d.arm_on_close;
    const members = this._members(d.zones);
    const doors = members.filter((id) => (this.settings.sensor_types[id] || "") === "door");
    const t = (group, v) => (this._t(group) || {})[v] || v;
    const areas = c.areas.length > 1 ? this._select("area", d.area, this._t("area"), c.areas.map((x) => [x.id, x.name])) : "";
    return `
      <h2>${pe(this.profile ? this._t("titleEdit") : this._t("titleNew"))}</h2>
      <div class="sec">${pe(this._t("secGeneral"))}</div>
      ${this._text("name", d.name, this._t("name"))}
      ${this._text("icon", d.icon, this._t("icon"))}
      ${this._select("panel_mode", d.panel_mode, this._t("button"), c.panel_modes.map((m) => [m, t("modes", m)]))}
      ${areas}
      <div class="sec">${pe(this._t("secWatch"))}</div>
      ${this._multi("zones", d.zones, this.settings.groups.map((g) => [g.id, g.name]), this._t("zones"))}
      ${this._multi("excluded", d.excluded, members.map((id) => [id, this._name(id)]), this._t("excluded"), this._t("noMembers"))}
      ${c.rules.length ? this._multi("rules", d.rules, c.rules.map((r) => [r.id, r.name]), this._t("rules")) : ""}
      ${c.tilt ? this._check("tilt_allowed", d.tilt_allowed, this._t("tilt")) : ""}
      <div class="sec">${pe(this._t("secTimes"))}</div>
      <div class="two">${this._num("exit_delay", d.exit_delay, this._t("exit"), 0, lim.delay)}${this._num("entry_delay", d.entry_delay, this._t("entry"), 0, lim.delay)}
      ${this._num("reaction_time", d.reaction_time, this._t("reaction"), 1, lim.reaction)}${this._num("max_alarm_cycles", d.max_alarm_cycles, this._t("cycles"), 1, lim.cycles)}</div>
      <div class="sec">${pe(this._t("secArming"))}</div>
      ${this._select("open_policy", d.open_policy, this._t("openPolicy"), c.open_policies.map((p) => [p, t("policy", p)]))}
      ${this._select("unavailable_policy", d.unavailable_policy, this._t("unavailablePolicy"), c.unavailable_policies.map((p) => [p, t("policy", p) + (p === "bypass_auto" ? this._t("experts") : "")]))}
      ${this._check("tamper_triggers_alarm", d.tamper_triggers_alarm, this._t("tamper"))}
      <div class="sec">${pe(this._t("secReaction"))}</div>
      ${this._multi("sirens", d.sirens, c.sirens.map((x) => [x.id, x.name]), this._t("sirens"), this._t("noSirens"))}
      <div class="two"><div>${this._select("siren_tone", d.siren_tone, this._t("tone"), c.tones.map((x) => [x, t("tones", x)]))}</div>
      <div>${this._select("siren_volume", d.siren_volume, this._t("volume"), c.volumes.map((x) => [x, t("volumes", x)]))}</div></div>
      ${this._check("silent", d.silent, this._t("silent"))}
      ${this._multi("notify", d.notify, c.notify.map((x) => [x.id, x.name]), this._t("notify"))}
      ${this._multi("speakers", d.speakers, c.speakers.map((x) => [x.id, x.name]), this._t("speakers"))}
      <div class="sec">${pe(this._t("secAuto"))}</div>
      <div class="two"><div><label>${pe(this._t("armTime"))}</label><input type="time" data-a="auto_arm_time" value="${pe(a.auto_arm_time || "")}"></div>
      <div><label>${pe(this._t("disarmTime"))}</label><input type="time" data-a="auto_disarm_time" value="${pe(a.auto_disarm_time || "")}"></div></div>
      <label>${pe(this._t("weekdays"))}</label><div class="days">${c.weekdays.map((w) => `<div class="chk"><input type="checkbox" data-am="auto_weekdays" value="${w}" ${a.auto_weekdays.includes(w) ? "checked" : ""}><span>${pe(t("days", w))}</span></div>`).join("")}</div>
      <label>${pe(this._t("schedule"))}</label><select data-a="auto_schedule"><option value="">${pe(this._t("noSchedule"))}</option>${c.schedules.map((x) => `<option value="${pe(x.id)}" ${x.id === a.auto_schedule ? "selected" : ""}>${pe(x.name)}</option>`).join("")}</select>
      <div class="tool" style="margin-top:6px"><a class="b" href="/config/helpers" target="_blank" rel="noopener">${pe(this._t("scheduleCreate"))}</a><button class="b" data-act="refresh">${pe(this._t("refreshLists"))}</button></div>
      <div class="muted">${pe(this._t("scheduleHint"))}</div>
      <label>${pe(this._t("persons"))}</label>${c.persons.map((x) => `<div class="chk"><input type="checkbox" data-am="auto_away_persons" value="${pe(x.id)}" ${a.auto_away_persons.includes(x.id) ? "checked" : ""}><span>${pe(x.name)}</span></div>`).join("") || `<div class="muted">${pe(this._t("none"))}</div>`}
      <div class="two"><div><label>${pe(this._t("awayDelay"))}</label><input type="number" min="1" max="${lim.away_delay}" data-a="auto_away_delay" data-num="1" value="${pe(a.auto_away_delay)}"></div>
      <div><label>${pe(this._t("arrivalWindow"))}</label><input type="number" min="1" max="${lim.arrival_window}" data-a="auto_arrival_window" data-num="1" value="${pe(a.auto_arrival_window)}"></div></div>
      <label>${pe(this._t("arrival"))}</label><select data-a="auto_arrival_mode">${c.arrival_modes.map((m) => `<option value="${m}" ${m === a.auto_arrival_mode ? "selected" : ""}>${pe(t("arrivalModes", m))}</option>`).join("")}</select>
      <div class="sec">${pe(this._t("secClose"))}</div>
      <div class="chk"><input type="checkbox" data-c="enabled" ${close.enabled ? "checked" : ""}><span>${pe(this._t("closeOn"))}</span></div>
      <label>${pe(this._t("doors"))}</label>${doors.map((id) => `<div class="chk"><input type="checkbox" data-cm="doors" value="${pe(id)}" ${close.doors.includes(id) ? "checked" : ""}><span>${pe(this._name(id))}</span></div>`).join("") || `<div class="muted">${pe(this._t("noDoors"))}</div>`}
      <label>${pe(this._t("settle"))}</label><input class="small" type="number" min="1" max="${lim.settle}" data-c="settle" data-num="1" value="${pe(close.settle)}">
      ${this._err("base")}`;
  }

  _collect() {
    const root = this.shadowRoot;
    const d = this._draft;
    const val = (el) => (el.dataset.bool ? el.checked : el.dataset.num ? Number(el.value) : el.value);
    root.querySelectorAll("[data-k]").forEach((el) => (d[el.dataset.k] = val(el)));
    const multi = {};
    root.querySelectorAll("[data-m]").forEach((el) => {
      multi[el.dataset.m] = multi[el.dataset.m] || [];
      if (el.checked) multi[el.dataset.m].push(el.value);
    });
    for (const key of ["zones", "excluded", "rules", "sirens", "notify", "speakers"]) {
      if (key in multi) d[key] = multi[key];
      else if (["excluded", "rules"].includes(key) && !root.querySelector(`[data-m="${key}"]`)) d[key] = key === "excluded" ? [] : d[key];
    }
    root.querySelectorAll("[data-a]").forEach((el) => (d.automation[el.dataset.a] = el.dataset.num ? Number(el.value) : el.value || null));
    const am = {};
    root.querySelectorAll("[data-am]").forEach((el) => {
      am[el.dataset.am] = am[el.dataset.am] || [];
      if (el.checked) am[el.dataset.am].push(el.value);
    });
    d.automation.auto_weekdays = am.auto_weekdays || [];
    d.automation.auto_away_persons = am.auto_away_persons || [];
    root.querySelectorAll("[data-c]").forEach((el) => {
      d.arm_on_close[el.dataset.c] = el.type === "checkbox" ? el.checked : Number(el.value);
    });
    const doors = [...root.querySelectorAll('[data-cm="doors"]')];
    d.arm_on_close.doors = doors.filter((el) => el.checked).map((el) => el.value);
    // Ausgenommene nur aus den gewählten Gruppen
    const members = this._members(d.zones);
    d.excluded = d.excluded.filter((id) => members.includes(id));
  }

  async _apply(action, data) {
    this._busy = true;
    this._render();
    let result;
    try {
      result = await this.hass.callWS({ type: "hauswacht/settings/apply", revision: this.settings.revision, action, data });
    } catch (err) {
      result = { ok: false, errors: { base: "failed" } };
    }
    this._busy = false;
    if (result.ok) {
      this.dispatchEvent(new CustomEvent("hw-saved", { bubbles: true, composed: true, detail: { revision: result.revision } }));
      return;
    }
    this._errors = result.errors || { base: "failed" };
    if (this._errors.base === "changed_elsewhere") {
      this.dispatchEvent(new CustomEvent("hw-stale", { bubbles: true, composed: true }));
    }
    this._render();
  }

  _payload() {
    const d = { ...this._draft };
    if (this.settings.profile_edit.choices.areas.length <= 1) delete d.area;
    d.id = this.profile;
    return d;
  }

  _render() {
    const style = (window.HauswachtEditStyle || "") + PROFILE_STYLE;
    this.shadowRoot.innerHTML = `<style>${style}</style><div class="sheet">${this._form()}
      <div class="bar"><button class="b p" data-act="save" ${this._busy ? "disabled" : ""}>${pe(this._busy ? this._t("saving") : this._t("save"))}</button>
      <button class="b" data-act="cancel">${pe(this._t("cancel"))}</button>
      ${this.profile ? `<button class="b d" data-act="delete">${pe(this._t("delete"))}</button>` : ""}</div></div>`;
    window.HauswachtDocs?.decorate(this.shadowRoot, this.helpKey || "profiles", this._lang);
    this.onclick = (ev) => {
      if (ev.composedPath()[0] === this) this._close();
    };
    this.shadowRoot.querySelectorAll("[data-act]").forEach((btn) =>
      btn.addEventListener("click", () => {
        const act = btn.dataset.act;
        if (act === "cancel") this._close();
        else if (act === "refresh") this._refreshChoices();
        else if (act === "save") {
          this._collect();
          this._apply("profile_save", this._payload());
        } else if (act === "delete" && window.confirm(this._t("deleteConfirm"))) {
          this._apply("profile_delete", { id: this.profile });
        }
      })
    );
    // Gruppen ändern die Listen "Ausgenommen" und "Ausgangstüren"
    this.shadowRoot.querySelectorAll('[data-m="zones"]').forEach((el) =>
      el.addEventListener("change", () => {
        const top = this.shadowRoot.querySelector(".sheet").scrollTop;
        this._collect();
        this._render();
        this.shadowRoot.querySelector(".sheet").scrollTop = top;
      })
    );
  }

  async _refreshChoices() {
    // Auswahllisten neu holen (z. B. neuer Zeitplan) – Eingaben bleiben
    this._collect();
    try {
      const fresh = await this.hass.callWS({ type: "hauswacht/settings/get" });
      this.settings.profile_edit.choices = fresh.profile_edit.choices;
      this.settings.entities = fresh.entities;
    } catch (_err) {
      // bleibt bei der alten Liste
    }
    const top = this.shadowRoot.querySelector(".sheet").scrollTop;
    this._render();
    this.shadowRoot.querySelector(".sheet").scrollTop = top;
  }

  _close() {
    this.dispatchEvent(new CustomEvent("hw-close", { bubbles: true, composed: true }));
  }
}

if (!customElements.get("hauswacht-profile-editor")) {
  customElements.define("hauswacht-profile-editor", HauswachtProfileEditor);
}
