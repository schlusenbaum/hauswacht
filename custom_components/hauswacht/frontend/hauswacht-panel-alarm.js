// Hauswacht – Einstellungsseite, Stufe 4: Alarmgeber und Benachrichtigungen (ADR 0011).
//
// Seitenblatt <hauswacht-alarm-editor> mit drei Arten: sirens (Sirenen und Freigabe),
// notify (Empfänger, Ereignisse, Erinnerung), text (eigener Text eines Ereignisses).
// Gespeichert wird über hauswacht/settings/apply – dieselben Funktionen wie im Dialog.
// Die Dialoge hier schalten nie eine Sirene; den Sirenentest gibt es in der Karte „Sirenentest“ der Seite und in der Testkarte.

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
    tones: "Ton je Sirene, Sirenentest-Erinnerung und „Sirene aus Schalter“ stehen auf der Seite unter den Sirenen. Den Sirenentest startest du in der Karte „Sirenentest“ oder in der Testkarte.",
    toneTitle: "Ton für {s}",
    toneKnown: "Töne, die diese Sirene meldet",
    toneNone: "– (diese Sirene meldet keine Töne)",
    toneAutoLong: "Automatisch (Standard-Einbruchton)",
    toneOwn: "Eigener Ton (Name genau wie im Gerät)",
    fireMark: " – Brandton",
    fireInfo: "Brandtöne (mit „fire“, „smoke“ oder „Brand“ im Namen) sind für Einbruch gesperrt: Wer einen Brandton hört, verlässt das Haus – womöglich genau dorthin, wo der Einbrecher ist. Nur falls der Name täuscht, lässt er sich als Experte freigeben. Für Rauchmelder mit Sirene geht das nie.",
    smoke: "Diese Sirene hat eigene Brandsensoren (Rauchmelder) – ein Brandton für Einbruch ist hier nie möglich.",
    allowFire: "Experten: Brandton für Einbruch erlauben",
    confirmFire: "Ich bestätige: Diese Sirene ist kein Rauchmelder, und alle im Haus kennen den Ton als Einbruchalarm",
    toneAfter: "Danach am besten einen kurzen, leisen Sirenentest machen (Karte „Sirenentest“ oder Testkarte).",
    testTitle: "Sirenentest – Erinnerung und Vorwarnung",
    reminder: "Erinnerung, wenn eine Sirene so lange nicht getestet wurde",
    months: { 0: "Aus", 3: "Alle 3 Monate", 6: "Alle 6 Monate", 12: "Jährlich" },
    prewarn: "Vorwarnung „Sirenentest in 10 Sekunden“ an die allgemeinen Empfänger",
    switchTitle: "Sirene aus Schalter erstellen",
    switchInfo: "Manche Sirenen erscheinen in Home Assistant nur als Schalter (switch.…). Hauswacht legt dafür den Home-Assistant-Helfer „Gerätetyp eines Schalters ändern“ mit Typ Sirene an und trägt die neue Sirene gleich ein. Der Schalter wird dabei nicht geschaltet. Rückgängig: den Helfer unter Einstellungen → Geräte & Dienste → Helfer löschen.",
    switchPick: "Schalter der Sirene",
    switchConfirm: "Ich bestätige: Das ist eine reine Alarmsirene, kein Rauchmelder",
    speechTitle: "Sprachausgabe",
    speechInfo: "Lautsprecher sind Geräte mit Benachrichtigungs-Entitäten, z. B. Echo-Geräte (Integration „Alexa Devices“). Ein stiller Alarm wird nie angesagt, der Bedrohungs-Notruf nie über Lautsprecher.",
    speakers: "Lautsprecher (Standard für alle Ereignisse)",
    noSpeakers: "Keine Lautsprecher gefunden.",
    repeat: "Alarm-Durchsage wiederholen alle … Sekunden (0 = nur einmal)",
    quiet: "Nachtruhe (nur ansagen, was beim Ereignis „auch in der Nachtruhe“ erlaubt ist)",
    quietFrom: "von",
    quietTo: "bis",
    speechEvent: "Ansage",
    speechOn: "Ansagen",
    mode: "Art",
    modes: { announce: "Durchsage (mit Gong)", speak: "Sprechen" },
    ownSpeakers: "Eigene Lautsprecher (keine angehakt = Standard)",
    inQuiet: "Auch in der Nachtruhe ansagen",
    speechText: "Text",
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
    title: "Titel",
    message: "Text",
    placeholders: "Platzhalter",
    preview: "Vorschau mit Beispielwerten",
    reset: "↺ Standardtext",
    isDefault: "Das ist der Text von Hauswacht – einfach ändern. Unverändert gespeichert bleibt es beim Text von Hauswacht.",
    isCustom: "Eigener Text. „Standardtext“ setzt ihn auf den Text von Hauswacht zurück.",
    fullText: "{text} steht für den vollständigen Text von Hauswacht, z. B. „{text} – bitte Nachbarn anrufen“.",
    none: "–",
    errors: {
      confirm_hardware_required: "Zum Freigeben bitte bestätigen.",
      siren_tone_fire_detector: "Diese Sirene hat eigene Brandsensoren (Rauchmelder) – ein Brandton für Einbruch ist hier nie erlaubt.",
      siren_tone_fire: "Ein Brandton ist für Einbruch gesperrt – nur mit der Experten-Freigabe unten.",
      siren_tone_fire_confirm: "Bitte die Experten-Freigabe ausdrücklich bestätigen.",
      siren_switch_confirm: "Bitte bestätigen, dass es eine reine Alarmsirene ist.",
      control_entity: "Bitte einen Schalter wählen.",
      helper_failed: "Der Helfer konnte nicht angelegt werden (siehe Protokoll).",
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
    tones: "Tone per siren, the siren test reminder and “siren from switch” are on the page below the sirens. Start the siren test in the card “Siren test” or in the test card.",
    toneTitle: "Tone for {s}",
    toneKnown: "Tones this siren reports",
    toneNone: "– (this siren reports no tones)",
    toneAutoLong: "Automatic (burglar tone)",
    toneOwn: "Own tone (name exactly as in the device)",
    fireMark: " – fire tone",
    fireInfo: "Fire tones (with “fire”, “smoke” or “Brand” in the name) are blocked for intrusion: whoever hears a fire tone leaves the house – possibly right where the burglar is. Only if the name is misleading can it be released as an expert. Never for smoke detectors with a siren.",
    smoke: "This siren has its own fire sensors (smoke detector) – a fire tone for intrusion is never possible here.",
    allowFire: "Experts: allow fire tone for intrusion",
    confirmFire: "I confirm: this siren is not a smoke detector, and everyone in the house knows the tone as the intrusion alarm",
    toneAfter: "Afterwards, best do a short, quiet siren test (card “Siren test” or test card).",
    testTitle: "Siren test – reminder and pre-warning",
    reminder: "Reminder if a siren has not been tested for this long",
    months: { 0: "Off", 3: "Every 3 months", 6: "Every 6 months", 12: "Yearly" },
    prewarn: "Pre-warning “siren test in 10 seconds” to the general recipients",
    switchTitle: "Create siren from switch",
    switchInfo: "Some sirens appear in Home Assistant only as a switch (switch.…). Hauswacht creates the Home Assistant helper “change device type of a switch” with type siren and registers the new siren right away. The switch is not switched. To undo: delete the helper under Settings → Devices & services → Helpers.",
    switchPick: "Switch of the siren",
    switchConfirm: "I confirm: this is a pure alarm siren, not a smoke detector",
    speechTitle: "Speech",
    speechInfo: "Speakers are devices with notification entities, e.g. Echo devices (integration “Alexa Devices”). A silent alarm is never announced, the duress emergency never over speakers.",
    speakers: "Speakers (default for all events)",
    noSpeakers: "No speakers found.",
    repeat: "Repeat the alarm announcement every … seconds (0 = only once)",
    quiet: "Quiet hours (only announce what the event allows “also during quiet hours”)",
    quietFrom: "from",
    quietTo: "to",
    speechEvent: "Announcement",
    speechOn: "Announce",
    mode: "Type",
    modes: { announce: "Announcement (with chime)", speak: "Speak" },
    ownSpeakers: "Own speakers (none ticked = default)",
    inQuiet: "Also announce during quiet hours",
    speechText: "Text",
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
    title: "Title",
    message: "Text",
    placeholders: "Placeholders",
    preview: "Preview with example values",
    reset: "↺ Default text",
    isDefault: "This is Hauswacht's text – just change it. Saved unchanged, Hauswacht's text stays.",
    isCustom: "Own text. “Default text” resets it to Hauswacht's text.",
    fullText: "{text} stands for Hauswacht's complete text, e.g. “{text} – please call the neighbours”.",
    none: "–",
    errors: {
      confirm_hardware_required: "Please confirm to enable.",
      siren_tone_fire_detector: "This siren has its own fire sensors (smoke detector) – a fire tone for intrusion is never allowed here.",
      siren_tone_fire: "A fire tone is blocked for intrusion – only with the expert release below.",
      siren_tone_fire_confirm: "Please confirm the expert release explicitly.",
      siren_switch_confirm: "Please confirm that it is a pure alarm siren.",
      control_entity: "Please choose a switch.",
      helper_failed: "The helper could not be created (see log).",
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
  .pv { border: 1px solid var(--divider-color); border-radius: 8px; padding: 8px 10px; font-size: .9rem; }
  .tool { margin-top: 8px; }
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
    } else if (this.kind === "tone") {
      const item = s.sirens.items.find((i) => i.id === this.siren) || {};
      this._siren = item;
      this._draft = { tone: item.tone || "_auto", own: "", allow_fire_tone: !!item.fire_ok, confirm_fire_tone: false };
      if (item.tone && !item.tones.some((t) => t.tone === item.tone)) this._draft = { ...this._draft, tone: "_own", own: item.tone };
    } else if (this.kind === "speech") {
      const sp = s.notify.speech;
      this._draft = { speakers: [...sp.speakers], repeat: sp.repeat, quiet_enabled: sp.quiet_enabled, quiet_start: sp.quiet_start, quiet_end: sp.quiet_end };
    } else if (this.kind === "speechevent") {
      const ev = s.notify.speech.events.find((e) => e.event === this.event) || {};
      this._speechEvent = ev;
      this._draft = { enabled: ev.enabled, mode: ev.mode, speakers: [...(ev.speakers || [])], in_quiet: ev.in_quiet, text: ev.text || ev.default || "" };
    } else if (this.kind === "sirentest") {
      this._draft = { reminder_months: s.sirens.test.reminder_months, prewarn: s.sirens.test.prewarn };
    } else if (this.kind === "fromswitch") {
      this._draft = { switch: "", confirm: false };
    } else {
      const ev = s.notify.events.find((e) => e.event === this.event) || {};
      this._event = ev;
      this._draft = { title: ev.title || ev.default_title || "", message: ev.message || ev.default_message || "" };
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

  get _isDefault() {
    const ev = this._event || {};
    const same = (text, def) => !text.trim() || text.trim() === (def || "");
    return same(this._draft.title, ev.default_title) && same(this._draft.message, ev.default_message);
  }

  // Wie render() in core/messages.py: Platzhalter füllen, leere Klammern und Leerzeichen aufräumen
  _fill(template) {
    const values = this.settings.notify.examples || {};
    return String(template || "")
      .replace(/\{(\w+)\}/g, (m, name) => (name in values ? values[name] : m))
      .replace(/\(\s*\)/g, "")
      .replace(/[ \t]+/g, " ")
      .replace(/ +([.,;:!?])/g, "$1")
      .trim();
  }

  _previewHtml() {
    const d = this._draft;
    return `<b>${ae(this._fill(d.title))}</b><br>${ae(this._fill(d.message))}`;
  }

  _toneForm() {
    const d = this._draft;
    const it = this._siren;
    const opts = [["_auto", this._t("toneAutoLong")]]
      .concat(it.tones.filter((t) => !t.fire || !it.smoke_detector).map((t) => [t.tone, t.tone + (t.fire ? this._t("fireMark") : "")]))
      .concat([["_own", this._t("toneOwn")]]);
    const select = `<select data-tf="tone">${opts.map(([v, l]) => `<option value="${ae(v)}" ${v === d.tone ? "selected" : ""}>${ae(l)}</option>`).join("")}</select>`;
    const known = it.tones_supported && it.tones.length ? it.tones.map((t) => t.tone).join(", ") : this._t("toneNone");
    const expert = it.smoke_detector
      ? `<div class="warn">${ae(this._t("smoke"))}</div>`
      : `<div class="chk"><input type="checkbox" data-b="allow_fire_tone" ${d.allow_fire_tone ? "checked" : ""}><span>${ae(this._t("allowFire"))}</span></div>
         ${d.allow_fire_tone ? `<div class="chk"><input type="checkbox" data-b="confirm_fire_tone" ${d.confirm_fire_tone ? "checked" : ""}><span>${ae(this._t("confirmFire"))}</span></div>${this._err("confirm_fire_tone")}` : ""}`;
    return `<h2>${ae(this._t("toneTitle").replace("{s}", it.name))}</h2>
      <label>${ae(this._t("toneKnown"))}</label><div class="muted">${ae(known)}</div>
      <label>${ae(this._t("tone"))}</label>${select}
      ${d.tone === "_own" ? `<input data-tf="own" value="${ae(d.own)}" style="margin-top:6px">` : ""}${this._err("tone")}
      <div class="muted" style="margin-top:10px">${ae(this._t("fireInfo"))}</div>${expert}
      <div class="muted" style="margin-top:10px">${ae(this._t("toneAfter"))}</div>`;
  }

  _speakerChecks(attr, chosen) {
    const choices = this.settings.notify.speech.speaker_choices;
    return choices.length
      ? choices.map((c) => `<div class="chk"><input type="checkbox" ${attr}="${ae(c.id)}" ${chosen.includes(c.id) ? "checked" : ""}><span>${ae(c.name)}</span></div>`).join("")
      : `<div class="muted">${ae(this._t("noSpeakers"))}</div>`;
  }

  _speechForm() {
    const d = this._draft;
    return `<h2>${ae(this._t("speechTitle"))}</h2><div class="muted">${ae(this._t("speechInfo"))}</div>
      <label>${ae(this._t("speakers"))}</label>${this._speakerChecks("data-sp", d.speakers)}
      <label>${ae(this._t("repeat"))}</label><input class="small" type="number" min="0" max="${this.settings.notify.speech.max_repeat}" data-tf="repeat" value="${ae(d.repeat)}">
      <div class="chk" style="margin-top:10px"><input type="checkbox" data-b="quiet_enabled" ${d.quiet_enabled ? "checked" : ""}><span>${ae(this._t("quiet"))}</span></div>
      <div class="inline"><div><label>${ae(this._t("quietFrom"))}</label><input class="small" type="time" data-tf="quiet_start" value="${ae(d.quiet_start)}"></div>
      <div><label>${ae(this._t("quietTo"))}</label><input class="small" type="time" data-tf="quiet_end" value="${ae(d.quiet_end)}"></div></div>`;
  }

  _speechEventForm() {
    const d = this._draft;
    const ph = this.settings.notify.placeholders.map((p) => `<code>${ae(p)}</code>`).join(" ");
    const modes = Object.entries(this._t("modes")).map(([v, l]) => `<option value="${v}" ${v === d.mode ? "selected" : ""}>${ae(l)}</option>`).join("");
    return `<h2>${ae(this._t("speechEvent"))}: ${ae(this.eventLabel ? this.eventLabel(this.event) : this.event)}</h2>
      <div class="chk"><input type="checkbox" data-b="enabled" ${d.enabled ? "checked" : ""}><span>${ae(this._t("speechOn"))}</span></div>
      <label>${ae(this._t("mode"))}</label><select data-tf="mode">${modes}</select>
      <label>${ae(this._t("ownSpeakers"))}</label>${this._speakerChecks("data-sp", d.speakers)}
      <div class="chk" style="margin-top:10px"><input type="checkbox" data-b="in_quiet" ${d.in_quiet ? "checked" : ""}><span>${ae(this._t("inQuiet"))}</span></div>
      <label>${ae(this._t("speechText"))}</label><textarea data-tf="text">${ae(d.text)}</textarea>${this._err("text")}
      <div class="tool"><button class="b" data-act="reset-speech">${ae(this._t("reset"))}</button></div>
      <label>${ae(this._t("placeholders"))}</label><div class="muted">${ph}</div>
      <label>${ae(this._t("preview"))}</label><div class="pv" data-preview>${ae(this._fill(d.text))}</div>`;
  }

  _sirenTestForm() {
    const d = this._draft;
    const choices = this.settings.sirens.test.choices
      .map((m) => `<option value="${m}" ${Number(m) === Number(d.reminder_months) ? "selected" : ""}>${ae(this._t("months")[m] || m)}</option>`)
      .join("");
    return `<h2>${ae(this._t("testTitle"))}</h2>
      <label>${ae(this._t("reminder"))}</label><select data-tf="reminder_months">${choices}</select>
      <div class="chk" style="margin-top:10px"><input type="checkbox" data-b="prewarn" ${d.prewarn ? "checked" : ""}><span>${ae(this._t("prewarn"))}</span></div>`;
  }

  _fromSwitchForm() {
    const d = this._draft;
    const list = this.settings.sirens.switches;
    return `<h2>${ae(this._t("switchTitle"))}</h2><div class="muted">${ae(this._t("switchInfo"))}</div>
      <label>${ae(this._t("switchPick"))}</label><select data-tf="switch"><option value="">–</option>${list.map((x) => `<option value="${ae(x.id)}" ${x.id === d.switch ? "selected" : ""}>${ae(x.name)} (${ae(x.id)})</option>`).join("")}</select>${this._err("switch")}
      <div class="chk" style="margin-top:10px"><input type="checkbox" data-b="confirm" ${d.confirm ? "checked" : ""}><span>${ae(this._t("switchConfirm"))}</span></div>${this._err("confirm")}${this._err("base")}`;
  }

  _textForm() {
    const d = this._draft;
    const ph = this.settings.notify.placeholders.map((p) => `<code>${ae(p)}</code>`).join(" ");
    return `
      <h2>${ae(this._t("textTitle"))}: ${ae(this.eventLabel ? this.eventLabel(this.event) : this.event)}</h2>
      <div class="muted" data-state>${ae(this._isDefault ? this._t("isDefault") : this._t("isCustom"))}</div>
      <label>${ae(this._t("title"))}</label><input data-tx="title" value="${ae(d.title)}">${this._err("title")}
      <label>${ae(this._t("message"))}</label><textarea data-tx="message">${ae(d.message)}</textarea>${this._err("message")}
      <div class="tool"><button class="b" data-act="reset">${ae(this._t("reset"))}</button></div>
      <label>${ae(this._t("placeholders"))}</label><div class="muted">${ph}</div>
      <div class="muted">${ae(this._t("fullText"))}</div>
      <label>${ae(this._t("preview"))}</label><div class="pv" data-preview>${this._previewHtml()}</div>`;
  }

  // --- Lesen, Speichern --------------------------------------------------------

  _collect() {
    const root = this.shadowRoot;
    const d = this._draft;
    root.querySelectorAll("[data-b]").forEach((el) => (d[el.dataset.b] = el.checked));
    root.querySelectorAll("[data-tf]").forEach((el) => (d[el.dataset.tf] = el.value));
    if (root.querySelector("[data-sp]")) d.speakers = [...root.querySelectorAll("[data-sp]")].filter((el) => el.checked).map((el) => el.dataset.sp);
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
    if (this.kind === "tone") {
      const tone = d.tone === "_own" ? d.own.trim() : d.tone;
      return ["siren_tone_save", { siren: this._siren.id, tone, allow_fire_tone: d.allow_fire_tone, confirm_fire_tone: d.confirm_fire_tone }];
    }
    if (this.kind === "speech") return ["speech_save", { ...d, repeat: Number(d.repeat) }];
    if (this.kind === "speechevent") return ["speech_event_save", { ...d, event: this.event }];
    if (this.kind === "sirentest") return ["siren_test_save", { reminder_months: Number(d.reminder_months), prewarn: d.prewarn }];
    if (this.kind === "fromswitch") return ["siren_from_switch", { switch: d.switch, confirm: d.confirm }];
    if (this.kind === "text") {
      // Unverändert = Text von Hauswacht (es wird nichts gespeichert)
      const ev = this._event || {};
      const own = (text, def) => (text.trim() === (def || "") ? "" : text);
      return ["notify_text_save", { event: this.event, title: own(d.title, ev.default_title), message: own(d.message, ev.default_message) }];
    }
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
    const forms = {
      sirens: () => this._sirensForm(),
      notify: () => this._notifyForm(),
      tone: () => this._toneForm(),
      sirentest: () => this._sirenTestForm(),
      fromswitch: () => this._fromSwitchForm(),
      speech: () => this._speechForm(),
      speechevent: () => this._speechEventForm(),
    };
    const body = (forms[this.kind] || (() => this._textForm()))();
    const top = this.shadowRoot.querySelector(".sheet")?.scrollTop || 0;
    this.shadowRoot.innerHTML = `<style>${(window.HauswachtEditStyle || "") + ALARM_STYLE}</style><div class="sheet">${body}${this.kind === "notify" ? this._err("base") : ""}
      <div class="bar"><button class="b p" data-act="save" ${this._busy ? "disabled" : ""}>${ae(this._busy ? this._t("saving") : this._t("save"))}</button>
      <button class="b" data-act="cancel">${ae(this._t("cancel"))}</button></div></div>`;
    this.shadowRoot.querySelector(".sheet").scrollTop = top;
    const help = { sirens: "sirens", notify: "notifications", text: "texts", tone: "sirenTone", sirentest: "sirenTest", fromswitch: "sirenSwitch", speech: "speech", speechevent: "speech" }[this.kind];
    window.HauswachtDocs?.decorate(this.shadowRoot, help, this._lang);
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
    root.querySelectorAll('[data-b="hardware_enabled"], [data-b="allow_switch"], [data-b="allow_fire_tone"], [data-tf="tone"]').forEach((el) =>
      el.addEventListener("change", () => {
        this._collect();
        this._render();
      })
    );
    const reset = root.querySelector('[data-act="reset"]');
    if (reset) {
      reset.addEventListener("click", () => {
        this._draft.title = this._event?.default_title || "";
        this._draft.message = this._event?.default_message || "";
        this._errors = {};
        this._render();
      });
    }
    // Vorschau beim Tippen, ohne neu zu zeichnen (sonst springt der Cursor)
    root.querySelectorAll("[data-tx]").forEach((el) =>
      el.addEventListener("input", () => {
        this._draft[el.dataset.tx] = el.value;
        root.querySelector("[data-preview]").innerHTML = this._previewHtml();
        root.querySelector("[data-state]").textContent = this._isDefault ? this._t("isDefault") : this._t("isCustom");
      })
    );
    const resetSpeech = root.querySelector('[data-act="reset-speech"]');
    if (resetSpeech) {
      resetSpeech.addEventListener("click", () => {
        this._collect();
        this._draft.text = this._speechEvent?.default || "";
        this._errors = {};
        this._render();
      });
    }
    const speechText = root.querySelector('textarea[data-tf="text"]');
    if (speechText) {
      speechText.addEventListener("input", () => {
        root.querySelector("[data-preview]").textContent = this._fill(speechText.value);
      });
    }
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
