// Hauswacht – Einstellungsseite, Stufe 4: Alarmgeber und Benachrichtigungen (ADR 0011).
//
// Seitenblatt <hauswacht-alarm-editor> mit drei Arten: sirens (Sirenen und Freigabe),
// notify (Empfänger, Ereignisse, Erinnerung), text (eigener Text eines Ereignisses).
// Gespeichert wird über hauswacht/settings/apply – dieselben Funktionen wie im Dialog.
// Sirenen werden hier nie geschaltet; einen Sirenentest gibt es nur in der Testkarte.

const AT = {
  de: {
    save: "Speichern",
    saving: "Speichere …",
    cancel: "Abbrechen",
    sirensTitle: "Sirenen",
    registered: "Eingetragene Sirenen",
    noSirens: "Noch keine Sirene eingetragen – unten auswählen.",
    add: "Sirene hinzufügen",
    noCandidates: "Keine weiteren Sirenen gefunden.",
    hardware: "Echte Sirenenansteuerung freigegeben",
    hardwareWarn: "Achtung: Mit der Freigabe können eingetragene Sirenen bei einem Alarm wirklich ertönen. Vorher im Testmodus alles durchspielen. Brandalarm hat immer Vorrang; im Testmodus bleiben Sirenen gesperrt.",
    confirm: "Ich habe verstanden – Sirenen dürfen ab jetzt wirklich ertönen",
    allowSwitch: "Experten: auch Schalter als Sirene erlauben (switch.…)",
    allowSwitchNote: "Nach dem Speichern erscheinen Schalter in der Auswahl.",
    tones: "Ton je Sirene und Brandton-Freigabe stellst du im Dialog ein (Alarmgeber → Ton je Sirene). Einen Sirenentest gibt es nur in der Testkarte.",
    toneAuto: "automatisch",
    tone: "Ton",
    notifyTitle: "Benachrichtigungen",
    general: "Allgemeine Empfänger (für alle Ereignisse ohne eigene Empfänger)",
    testMode: "Auch im Testmodus benachrichtigen",
    pushDisarm: "Knopf „Unscharf schalten“ in der Alarm-Nachricht",
    critical: "Wichtige Nachrichten durchbrechen „Nicht stören“",
    duress: "Bedrohungs-PIN meldet still an",
    events: "Ereignisse",
    eventOn: "an",
    own: "eigene Empfänger",
    ownNone: "allgemeine Empfänger",
    reminder: "Erinnerung „Alle weg, aber nicht scharf“",
    reminderPersons: "Personen",
    reminderProfile: "Vorgeschlagenes Profil",
    noProfile: "– keins –",
    reminderDelay: "Nach (Minuten)",
    textTitle: "Eigener Text",
    title: "Titel (leer = Text von Hauswacht)",
    message: "Text (leer = Text von Hauswacht)",
    placeholders: "Platzhalter",
    preview: "Vorschau mit Beispielwerten",
    none: "–",
    errors: {
      confirm_hardware_required: "Zum Freigeben bitte bestätigen.",
      invalid_template: "Text fehlerhaft:",
      disarm_first: "Erst alle Bereiche unscharf schalten – dann lässt sich speichern.",
      changed_elsewhere: "Inzwischen wurde woanders etwas geändert. Die Seite lädt neu – bitte noch einmal.",
      failed: "Speichern fehlgeschlagen.",
    },
  },
  en: {
    save: "Save",
    saving: "Saving …",
    cancel: "Cancel",
    sirensTitle: "Sirens",
    registered: "Registered sirens",
    noSirens: "No siren registered yet – choose below.",
    add: "Add siren",
    noCandidates: "No further sirens found.",
    hardware: "Real siren control enabled",
    hardwareWarn: "Caution: once enabled, registered sirens can really sound on an alarm. Play everything through in test mode first. Fire alarm always takes priority; in test mode sirens stay locked.",
    confirm: "I understand – sirens may really sound from now on",
    allowSwitch: "Experts: also allow switches as sirens (switch.…)",
    allowSwitchNote: "After saving, switches appear in the list.",
    tones: "Tone per siren and the fire tone release are set in the dialog (alarm devices → tone per siren). A siren test is only available in the test card.",
    toneAuto: "automatic",
    tone: "Tone",
    notifyTitle: "Notifications",
    general: "General recipients (for all events without own recipients)",
    testMode: "Also notify in test mode",
    pushDisarm: "Button “Disarm” in the alarm message",
    critical: "Important messages break through “Do not disturb”",
    duress: "Duress PIN silently reports to",
    events: "Events",
    eventOn: "on",
    own: "own recipients",
    ownNone: "general recipients",
    reminder: "Reminder “all away, but not armed”",
    reminderPersons: "Persons",
    reminderProfile: "Suggested profile",
    noProfile: "– none –",
    reminderDelay: "After (minutes)",
    textTitle: "Own text",
    title: "Title (empty = Hauswacht's text)",
    message: "Text (empty = Hauswacht's text)",
    placeholders: "Placeholders",
    preview: "Preview with example values",
    none: "–",
    errors: {
      confirm_hardware_required: "Please confirm to enable.",
      invalid_template: "Text has an error:",
      disarm_first: "Disarm all areas first – then saving works.",
      changed_elsewhere: "Something was changed elsewhere in the meantime. The page reloads – please try again.",
      failed: "Saving failed.",
    },
  },
};

const ALARM_STYLE = `
  .warn { border: 1px solid var(--error-color, #db4437); border-radius: 8px; padding: 8px 10px; margin: 8px 0;
    color: var(--error-color, #db4437); font-size: .9rem; }
  details { border-bottom: 1px solid var(--divider-color); padding: 6px 0; }
  summary { cursor: pointer; display: flex; gap: 8px; align-items: center; }
  summary .n { flex: 1; }
  summary input { width: auto; margin: 0; }
  textarea { font: inherit; width: 100%; box-sizing: border-box; min-height: 90px; padding: 7px 10px; border-radius: 6px;
    border: 1px solid var(--divider-color); background: var(--card-background-color); color: var(--primary-text-color); }
  code { font-size: .85rem; }
`;

const ae = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

class HauswachtAlarmEditor extends HTMLElement {
  // open({hass, settings, kind, event, eventLabel}) – kind: sirens | notify | text
  open(options) {
    Object.assign(this, options);
    this._errors = {};
    this._details = {};
    this._busy = false;
    const s = this.settings;
    if (this.kind === "sirens") {
      this._draft = { sirens: [...s.sirens.registered], hardware_enabled: s.sirens.hardware_enabled, allow_switch: s.sirens.allow_switch, confirm_hardware: false };
    } else if (this.kind === "notify") {
      const n = s.notify;
      this._draft = {
        general: [...n.general], test_mode: n.test_mode, push_disarm: n.push_disarm, critical: n.critical, duress: [...n.duress],
        events: n.events.map((e) => ({ event: e.event, enabled: e.enabled, targets: [...e.targets] })),
        reminder: { ...n.reminder, persons: [...n.reminder.persons] },
      };
    } else {
      const ev = s.notify.events.find((e) => e.event === this.event) || {};
      this._draft = { title: ev.title || "", message: ev.message || "", preview: ev.preview || "" };
    }
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this._render();
  }

  get _lang() {
    return (this.hass?.language || "en").startsWith("de") ? "de" : "en";
  }

  _t(key) {
    return AT[this._lang][key] ?? AT.en[key] ?? key;
  }

  _err(key) {
    const k = this._errors[key];
    if (!k) return "";
    const extra = k === "invalid_template" && this._details.message ? ` ${this._details.message}` : "";
    return `<div class="err">${ae((this._t("errors")[k] || k) + extra)}</div>`;
  }

  _checks(attr, chosen, items) {
    return items.length
      ? items.map(([v, l]) => `<div class="chk"><input type="checkbox" ${attr}="${ae(v)}" ${chosen.includes(v) ? "checked" : ""}><span>${ae(l)}</span></div>`).join("")
      : `<div class="muted">${ae(this._t("none"))}</div>`;
  }

  _notifyItems() {
    const choices = this.settings.notify.choices.notify;
    const known = new Set(choices.map((c) => c.id));
    const extra = [...this._draft.general, ...this._draft.duress, ...this._draft.events.flatMap((e) => e.targets)]
      .filter((id) => !known.has(id))
      .map((id) => ({ id, name: id }));
    return [...choices, ...extra].map((c) => [c.id, c.name]);
  }

  // --- Formulare ---------------------------------------------------------------

  _sirensForm() {
    const s = this.settings.sirens;
    const d = this._draft;
    const name = (id) => (s.candidates.find((c) => c.id === id) || { name: id }).name;
    const rows = d.sirens
      .map((id) => `<div class="row"><div class="n">${ae(name(id))}<small>${ae(id)} · ${ae(this._t("tone"))}: ${ae(s.tones[id] || this._t("toneAuto"))}</small></div><button class="x" data-remove="${ae(id)}">✕</button></div>`)
      .join("");
    const free = s.candidates.filter((c) => !d.sirens.includes(c.id));
    const list = free.length
      ? `<div class="results">${free.map((c) => `<div data-pick="${ae(c.id)}">${ae(c.name)}<br><small>${ae(c.id)} · ${ae(c.state)}</small></div>`).join("")}</div>`
      : `<div class="muted">${ae(this._t("noCandidates"))}</div>`;
    const turningOn = d.hardware_enabled && !s.hardware_enabled;
    return `
      <h2>${ae(this._t("sirensTitle"))}</h2>
      <label>${ae(this._t("registered"))}</label>${rows || `<div class="muted">${ae(this._t("noSirens"))}</div>`}
      <label>${ae(this._t("add"))}</label>${list}
      <div class="chk" style="margin-top:14px"><input type="checkbox" data-b="hardware_enabled" ${d.hardware_enabled ? "checked" : ""}><span><b>${ae(this._t("hardware"))}</b></span></div>
      ${turningOn ? `<div class="warn">${ae(this._t("hardwareWarn"))}</div><div class="chk"><input type="checkbox" data-b="confirm_hardware" ${d.confirm_hardware ? "checked" : ""}><span>${ae(this._t("confirm"))}</span></div>` : ""}
      ${this._err("base")}
      <div class="chk"><input type="checkbox" data-b="allow_switch" ${d.allow_switch ? "checked" : ""}><span>${ae(this._t("allowSwitch"))}</span></div>
      ${d.allow_switch && !s.allow_switch ? `<div class="muted">${ae(this._t("allowSwitchNote"))}</div>` : ""}
      <div class="muted" style="margin-top:10px">${ae(this._t("tones"))}</div>`;
  }

  _notifyForm() {
    const d = this._draft;
    const items = this._notifyItems();
    const label = (v) => (this.eventLabel ? this.eventLabel(v) : v);
    const name = (id) => (items.find(([v]) => v === id) || [id, id])[1];
    const events = d.events
      .map((e, i) => `<details><summary><input type="checkbox" data-ev-on="${i}" ${e.enabled ? "checked" : ""}><span class="n">${ae(label(e.event))}</span><span class="muted">${ae(e.targets.length ? e.targets.map(name).join(", ") : this._t("ownNone"))}</span></summary>
        <div class="muted">${ae(this._t("own"))}</div>${this._checks(`data-ev-t="${i}" data-v`, e.targets, items)}</details>`)
      .join("");
    const c = this.settings.notify.choices;
    return `
      <h2>${ae(this._t("notifyTitle"))}</h2>
      <label>${ae(this._t("general"))}</label>${this._checks("data-g", d.general, items)}
      <div class="chk" style="margin-top:10px"><input type="checkbox" data-b="test_mode" ${d.test_mode ? "checked" : ""}><span>${ae(this._t("testMode"))}</span></div>
      <div class="chk"><input type="checkbox" data-b="push_disarm" ${d.push_disarm ? "checked" : ""}><span>${ae(this._t("pushDisarm"))}</span></div>
      <div class="chk"><input type="checkbox" data-b="critical" ${d.critical ? "checked" : ""}><span>${ae(this._t("critical"))}</span></div>
      <label>${ae(this._t("duress"))}</label>${this._checks("data-du", d.duress, items)}
      <label>${ae(this._t("events"))}</label>${events}
      <label>${ae(this._t("reminder"))}</label>
      <div class="muted">${ae(this._t("reminderPersons"))}</div>${this._checks("data-rp", d.reminder.persons, c.persons.map((p) => [p.id, p.name]))}
      <label>${ae(this._t("reminderProfile"))}</label><select data-r="profile"><option value="">${ae(this._t("noProfile"))}</option>${c.profiles.map((p) => `<option value="${ae(p.id)}" ${p.id === d.reminder.profile ? "selected" : ""}>${ae(p.name)}</option>`).join("")}</select>
      <label>${ae(this._t("reminderDelay"))}</label><input class="small" type="number" min="1" max="240" data-r="delay" value="${ae(d.reminder.delay)}">`;
  }

  _textForm() {
    const d = this._draft;
    const ph = this.settings.notify.placeholders.map((p) => `<code>${ae(p)}</code>`).join(" ");
    return `
      <h2>${ae(this._t("textTitle"))}: ${ae(this.eventLabel ? this.eventLabel(this.event) : this.event)}</h2>
      <label>${ae(this._t("title"))}</label><input data-tx="title" value="${ae(d.title)}">${this._err("title")}
      <label>${ae(this._t("message"))}</label><textarea data-tx="message">${ae(d.message)}</textarea>${this._err("message")}
      <label>${ae(this._t("placeholders"))}</label><div class="muted">${ph}</div>
      ${d.preview ? `<label>${ae(this._t("preview"))}</label><div class="muted">${ae(d.preview)}</div>` : ""}`;
  }

  // --- Lesen, Speichern --------------------------------------------------------

  _collect() {
    const root = this.shadowRoot;
    const d = this._draft;
    root.querySelectorAll("[data-b]").forEach((el) => (d[el.dataset.b] = el.checked));
    if (this.kind === "notify") {
      d.general = [...root.querySelectorAll("[data-g]")].filter((el) => el.checked).map((el) => el.dataset.g);
      d.duress = [...root.querySelectorAll("[data-du]")].filter((el) => el.checked).map((el) => el.dataset.du);
      root.querySelectorAll("[data-ev-on]").forEach((el) => (d.events[Number(el.dataset.evOn)].enabled = el.checked));
      d.events.forEach((e, i) => {
        e.targets = [...root.querySelectorAll(`[data-ev-t="${i}"]`)].filter((el) => el.checked).map((el) => el.dataset.v);
      });
      d.reminder.persons = [...root.querySelectorAll("[data-rp]")].filter((el) => el.checked).map((el) => el.dataset.rp);
      const profile = root.querySelector('[data-r="profile"]');
      const delay = root.querySelector('[data-r="delay"]');
      d.reminder.profile = profile ? profile.value || null : d.reminder.profile;
      d.reminder.delay = delay ? Number(delay.value) : d.reminder.delay;
    }
    if (this.kind === "text") {
      root.querySelectorAll("[data-tx]").forEach((el) => (d[el.dataset.tx] = el.value));
    }
  }

  _payload() {
    const d = this._draft;
    if (this.kind === "sirens") return ["sirens_save", { ...d }];
    if (this.kind === "text") return ["notify_text_save", { event: this.event, title: d.title, message: d.message }];
    const data = {
      notify_system: d.general,
      notify_in_test_mode: d.test_mode,
      push_disarm: d.push_disarm,
      critical_alerts: d.critical,
      duress_notify: d.duress,
      reminder: { reminder_persons: d.reminder.persons, reminder_profile: d.reminder.profile, reminder_delay: d.reminder.delay },
    };
    for (const e of d.events) data[`event_${e.event}`] = { enabled: e.enabled, targets: e.targets };
    return ["notify_save", data];
  }

  async _apply() {
    this._busy = true;
    this._render();
    const [action, data] = this._payload();
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
    this._details = result.details || {};
    if (this._errors.base === "changed_elsewhere") this.dispatchEvent(new CustomEvent("hw-stale", { bubbles: true, composed: true }));
    this._render();
  }

  _render() {
    const body = this.kind === "sirens" ? this._sirensForm() : this.kind === "notify" ? this._notifyForm() : this._textForm();
    const top = this.shadowRoot.querySelector(".sheet")?.scrollTop || 0;
    this.shadowRoot.innerHTML = `<style>${(window.HauswachtEditStyle || "") + ALARM_STYLE}</style><div class="sheet">${body}${this.kind === "notify" ? this._err("base") : ""}
      <div class="bar"><button class="b p" data-act="save" ${this._busy ? "disabled" : ""}>${ae(this._busy ? this._t("saving") : this._t("save"))}</button>
      <button class="b" data-act="cancel">${ae(this._t("cancel"))}</button></div></div>`;
    this.shadowRoot.querySelector(".sheet").scrollTop = top;
    this.onclick = (ev) => {
      if (ev.composedPath()[0] === this) this._close();
    };
    const root = this.shadowRoot;
    root.querySelector('[data-act="cancel"]').addEventListener("click", () => this._close());
    root.querySelector('[data-act="save"]').addEventListener("click", () => {
      this._collect();
      this._apply();
    });
    root.querySelectorAll("[data-pick]").forEach((el) =>
      el.addEventListener("click", () => {
        this._collect();
        this._draft.sirens.push(el.dataset.pick);
        this._render();
      })
    );
    root.querySelectorAll("[data-remove]").forEach((el) =>
      el.addEventListener("click", () => {
        this._collect();
        this._draft.sirens = this._draft.sirens.filter((x) => x !== el.dataset.remove);
        this._render();
      })
    );
    root.querySelectorAll('[data-b="hardware_enabled"], [data-b="allow_switch"]').forEach((el) =>
      el.addEventListener("change", () => {
        this._collect();
        this._render();
      })
    );
    // Haken im Kopf eines Ereignisses soll es nicht auf- und zuklappen
    root.querySelectorAll("[data-ev-on]").forEach((el) => el.addEventListener("click", (ev) => ev.stopPropagation()));
  }

  _close() {
    this.dispatchEvent(new CustomEvent("hw-close", { bubbles: true, composed: true }));
  }
}

if (!customElements.get("hauswacht-alarm-editor")) {
  customElements.define("hauswacht-alarm-editor", HauswachtAlarmEditor);
}
