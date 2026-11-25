// Hauswacht – Einstellungsseite: „Einrichten nach Zielen“ (ADR 0017, 0.65).
//
// Ein Seitenblatt mit Schritten: Haushalt → Ziele → Rückfragen → Sirenen und Empfänger → Plan.
// Die Seite schickt nur die Antworten. Hauswacht rechnet daraus den Plan („bisher → neu“), die
// Szenario-Vorschau und die Prüfung – und beim Übernehmen alles noch einmal neu (unscharf,
// Revision, Bestätigung bei Überschreiben oder Abschwächen). Es wird nichts geschaltet und keine
// Sirene freigegeben.

const GOALS_TEXT = {
  de: {
    title: "Einrichten nach Zielen",
    steps: ["Haushalt", "Ziele", "Rückfragen", "Sirenen und Empfänger", "Plan"],
    back: "Zurück",
    next: "Weiter",
    cancel: "Abbrechen",
    apply: "Übernehmen",
    applying: "Wird übernommen …",
    loading: "Wird geladen …",
    computing: "Plan wird gerechnet …",
    householdIntro: "Diese Personen kennt Home Assistant. Ob jemand als „weg“ erkannt werden kann, hängt von der Ortung ab – ein schlafendes Handy macht niemanden abwesend.",
    located: "Ortung",
    weak: "Tür + Signal (unsicher)",
    direction: "Richtung („nähert sich“)",
    frozen: "Ortung eingefroren",
    undetectable: "kann nicht als weg erkannt werden",
    householdHint: "Ortung und „Tür + Signal“ stellst du unter System → Anwesenheit ein.",
    goalsIntro: "Was soll Hauswacht für dich tun? Mehrere Ziele sind möglich. Vorhandenes wird nur ergänzt – was überschrieben würde, siehst du im Plan.",
    goal: {
      night: ["Nachts absichern", "Ein Profil für die Nacht: Türen und Fenster scharf, drinnen darf man sich bewegen. Auf Wunsch zu festen Uhrzeiten."],
      away: ["Automatisch scharf, wenn alle weg sind", "Sobald alle gewählten Personen sicher weg sind, wird das Abwesend-Profil nach einer Wartezeit scharf."],
      return: ["Beim Heimkommen unscharf", "Kommt jemand heim, wird das Abwesend-Profil unscharf – ohne PIN, wenn Handy und Tür zusammenpassen."],
      night_return: ["Nachts heimkommen, ohne dass „Nacht“ aus ist", "Wer nachts heimkommt, wird reingelassen – das Nacht-Profil bleibt scharf."],
    },
    targetNew: "legt das Profil „{p}“ neu an",
    targetChange: "ergänzt das Profil „{p}“",
    groups: "Meldergruppen",
    motionHint: "mit Bewegungsmeldern – nachts meist nicht",
    armTime: "Scharf um (leer = von Hand)",
    disarmTime: "Unscharf um (leer = von Hand)",
    persons: "Personen",
    delay: "Wartezeit, bis scharf geschaltet wird (Minuten)",
    mode: "Wie sicher?",
    modes: {
      door: "Unscharf mit Türbeleg (empfohlen) – Handy zuhause und Eingangstür auf, beides im Zeitfenster",
      passage: "Reinlassen – das Profil bleibt scharf, die Tür ist frei",
      auto_only: "Unscharf, nur wenn automatisch scharf geschaltet wurde",
      always: "Unscharf, auch nach Scharfschalten von Hand (ohne Tür – unsicherer)",
    },
    sirens: "Sirenen",
    sirensHint: "Gewählte Sirenen werden in die Profile eingetragen. Neue werden nur eingetragen – die Freigabe der echten Sirenenansteuerung bleibt ein eigener Schritt unter Alarmgeber.",
    released: "Freigabe: an",
    notReleased: "Freigabe: aus – im Ernstfall bleibt es still, bis du sie unter Alarmgeber freigibst",
    registered: "schon eingetragen",
    noSirens: "Keine Sirene gefunden (Rauchmelder werden nie angeboten).",
    notify: "Empfänger",
    noNotify: "Kein Empfänger gefunden.",
    planIntro: "Das würde sich ändern. Gespeichert wird erst mit „Übernehmen“.",
    before: "bisher",
    after: "neu",
    overwrite: "überschreibt",
    weakens: "nachgiebiger",
    notes: "Gut zu wissen",
    errors: "Bitte korrigieren",
    findings: "Der Assistent prüft danach",
    scenarios: "Was passiert dann, wenn …?",
    noChanges: "Nichts zu ändern – das ist schon so eingestellt.",
    confirm: "Ich habe die markierten Änderungen gesehen und möchte sie übernehmen.",
    applied: "Übernommen.",
    fail: {
      disarm_first: "Ändern geht nur, wenn alle Bereiche unscharf sind.",
      changed_elsewhere: "Inzwischen wurde etwas anderes geändert – bitte den Assistenten neu öffnen.",
      confirm_needed: "Bitte die markierten Änderungen bestätigen.",
      plan_invalid: "Der Plan lässt sich so nicht übernehmen – siehe Hinweise.",
      failed: "Übernehmen hat nicht geklappt.",
    },
    armedNote: "Ändern geht nur, wenn alle Bereiche unscharf sind – den Plan kannst du trotzdem ansehen.",
  },
  en: {
    title: "Set up by goals",
    steps: ["Household", "Goals", "Questions", "Sirens and recipients", "Plan"],
    back: "Back",
    next: "Next",
    cancel: "Cancel",
    apply: "Apply",
    applying: "Applying …",
    loading: "Loading …",
    computing: "Computing the plan …",
    householdIntro: "Home Assistant knows these people. Whether someone can be detected as “away” depends on a location – a sleeping phone makes nobody absent.",
    located: "location",
    weak: "door + signal (uncertain)",
    direction: "direction (“approaching”)",
    frozen: "location frozen",
    undetectable: "cannot be detected as away",
    householdHint: "Set up locations and “door + signal” under System → Presence.",
    goalsIntro: "What should Hauswacht do for you? Several goals are possible. Existing settings are only extended – the plan shows what would be overwritten.",
    goal: {
      night: ["Secure the night", "A profile for the night: doors and windows armed, moving around inside is fine. Optionally at fixed times."],
      away: ["Arm automatically when everyone is away", "As soon as all chosen persons are surely away, the Away profile arms after a waiting time."],
      return: ["Disarm when coming home", "When someone comes home, the Away profile is disarmed – without PIN if phone and door match."],
      night_return: ["Come home at night without turning “Night” off", "Whoever comes home at night is let in – the Night profile stays armed."],
    },
    targetNew: "creates the profile “{p}”",
    targetChange: "extends the profile “{p}”",
    groups: "Sensor groups",
    motionHint: "with motion sensors – usually not at night",
    armTime: "Arm at (empty = by hand)",
    disarmTime: "Disarm at (empty = by hand)",
    persons: "Persons",
    delay: "Waiting time until arming (minutes)",
    mode: "How safe?",
    modes: {
      door: "Disarm with door proof (recommended) – phone home and entry door open, both within the time window",
      passage: "Let in – the profile stays armed, the door is free",
      auto_only: "Disarm only if armed automatically",
      always: "Disarm, also after arming by hand (without door – less safe)",
    },
    sirens: "Sirens",
    sirensHint: "Chosen sirens are added to the profiles. New ones are only registered – enabling real siren control stays a separate step under Alarm devices.",
    released: "Enabled: on",
    notReleased: "Enabled: off – in an emergency it stays silent until you enable it under Alarm devices",
    registered: "already registered",
    noSirens: "No siren found (smoke detectors are never offered).",
    notify: "Recipients",
    noNotify: "No recipient found.",
    planIntro: "This would change. Nothing is saved until you press “Apply”.",
    before: "before",
    after: "new",
    overwrite: "overwrites",
    weakens: "more lenient",
    notes: "Good to know",
    errors: "Please correct",
    findings: "The assistant checks afterwards",
    scenarios: "What happens then if …?",
    noChanges: "Nothing to change – this is already set up.",
    confirm: "I have seen the marked changes and want to apply them.",
    applied: "Applied.",
    fail: {
      disarm_first: "Changes are only possible while all areas are disarmed.",
      changed_elsewhere: "Something else was changed in the meantime – please open the assistant again.",
      confirm_needed: "Please confirm the marked changes.",
      plan_invalid: "The plan cannot be applied like this – see the hints.",
      failed: "Applying did not work.",
    },
    armedNote: "Changes are only possible while all areas are disarmed – you can still look at the plan.",
  },
};

const GOALS_STYLE = `
  .stepper { display: flex; flex-wrap: wrap; gap: 4px; margin: 0 0 12px; font-size: .8rem; }
  .stepper span { padding: 2px 8px; border-radius: 10px; background: var(--secondary-background-color); color: var(--secondary-text-color); }
  .stepper span.on { background: var(--primary-color); color: var(--text-primary-color, #fff); }
  .person, .goal { border: 1px solid var(--divider-color); border-radius: 8px; padding: 8px 10px; margin: 6px 0; }
  .goal label { display: flex; gap: 8px; align-items: flex-start; color: var(--primary-text-color); font-size: 1rem; margin: 0; cursor: pointer; }
  .badges { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; }
  .badge { font-size: .78rem; padding: 1px 8px; border-radius: 10px; border: 1px solid var(--divider-color); }
  .badge.ok { border-color: var(--success-color, #43a047); }
  .badge.bad { border-color: var(--warning-color, #ffa600); }
  .sec { font-weight: 500; margin: 16px 0 4px; }
  .step { border: 1px solid var(--divider-color); border-radius: 8px; padding: 8px 10px; margin: 8px 0; }
  .step table { width: 100%; border-collapse: collapse; font-size: .9rem; }
  .step td { padding: 3px 4px; vertical-align: top; border-top: 1px solid var(--divider-color); }
  .mark { color: var(--warning-color, #ffa600); white-space: nowrap; }
  .list div { margin: 3px 0; }
  .err { color: var(--error-color, #db4437); }
  .sc { margin: 4px 0; }
  .chk { display: flex; gap: 6px; align-items: center; margin: 3px 0; }
`;

const ge = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

class HauswachtGoalsSheet extends HTMLElement {
  // open({hass}) – lädt Haushalt und Vorschläge, dann Schritt für Schritt
  async open(options) {
    Object.assign(this, options);
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this._step = 0;
    this._info = null;
    this._plan = null;
    this._message = null;
    this._busy = false;
    this._render();
    try {
      this._info = await this.hass.callWS({ type: "hauswacht/goals/start" });
      this._answers = JSON.parse(JSON.stringify(this._info.answers));
    } catch (err) {
      this._message = `${err?.message || err}`;
    }
    this._render();
  }

  get _lang() {
    return (this.hass?.language || "en").startsWith("de") ? "de" : "en";
  }

  _t(key) {
    return (GOALS_TEXT[this._lang] || GOALS_TEXT.en)[key];
  }

  _name(list, id) {
    return (list.find((x) => x.id === id) || { name: id }).name;
  }

  // --- Schritte ------------------------------------------------------------------------

  _household() {
    const rows = this._info.persons
      .map((p) => {
        const badges = [
          p.located ? `<span class="badge ok">✓ ${ge(this._t("located"))}</span>` : "",
          p.weak ? `<span class="badge">${ge(this._t("weak"))}</span>` : "",
          p.direction ? `<span class="badge ok">✓ ${ge(this._t("direction"))}</span>` : "",
          p.frozen ? `<span class="badge bad">⚠ ${ge(this._t("frozen"))}</span>` : "",
          p.detectable ? "" : `<span class="badge bad">⚠ ${ge(this._t("undetectable"))}</span>`,
        ].join("");
        return `<div class="person"><b>${ge(p.name)}</b><div class="badges">${badges}</div></div>`;
      })
      .join("");
    return `<div class="muted">${ge(this._t("householdIntro"))}</div>${rows}<div class="muted">${ge(this._t("householdHint"))}</div>`;
  }

  _target(goal) {
    const key = ["night", "night_return"].includes(goal) ? "night" : "away";
    const target = this._info.targets[key];
    const fallback = { night: this._lang === "de" ? "Nacht" : "Night", away: this._lang === "de" ? "Abwesend" : "Away" }[key];
    return target ? this._t("targetChange").replace("{p}", target.name) : this._t("targetNew").replace("{p}", fallback);
  }

  _goals() {
    const chosen = this._answers.goals;
    const rows = this._info.goals
      .map((g) => {
        const [title, text] = this._t("goal")[g];
        return `<div class="goal"><label><input type="checkbox" data-goal="${g}" ${chosen.includes(g) ? "checked" : ""}><span><b>${ge(title)}</b><br><span class="muted">${ge(text)}</span><br><span class="muted">→ ${ge(this._target(g))}</span></span></label></div>`;
      })
      .join("");
    return `<div class="muted">${ge(this._t("goalsIntro"))}</div>${rows}`;
  }

  // attr: z. B. 'data-q="night.zones"' (Rückfragen, ID in data-id) oder "data-s" (ID im Attribut)
  _checks(attr, items, selected, extra = () => "") {
    const mark = (x) => (attr.includes("=") ? `${attr} data-id="${ge(x.id)}"` : `${attr}="${ge(x.id)}"`);
    return items
      .map((x) => `<div class="chk"><input type="checkbox" ${mark(x)} ${selected.includes(x.id) ? "checked" : ""}><span>${ge(x.name)}${extra(x)}</span></div>`)
      .join("");
  }

  _personExtra(p) {
    return p.detectable ? "" : ` <span class="mark">⚠ ${ge(this._t("undetectable"))}</span>`;
  }

  _questions() {
    const a = this._answers;
    const g = a.goals;
    const info = this._info;
    const motion = (x) => (x.motion ? ` <span class="muted">(${ge(this._t("motionHint"))})</span>` : "");
    const parts = [];
    const needsNight = g.includes("night") || (g.includes("night_return") && !info.targets.night);
    const needsAway = g.includes("away") || (g.includes("return") && !info.targets.away);
    if (needsNight) {
      parts.push(`<div class="sec">${ge(this._t("goal").night[0])}</div>
        <label>${ge(this._t("groups"))}</label>${this._checks('data-q="night.zones"', info.groups, a.night.zones, motion)}
        ${g.includes("night") ? `<div class="two"><div><label>${ge(this._t("armTime"))}</label><input type="time" data-v="night.arm_time" value="${ge(a.night.arm_time || "")}"></div>
        <div><label>${ge(this._t("disarmTime"))}</label><input type="time" data-v="night.disarm_time" value="${ge(a.night.disarm_time || "")}"></div></div>` : ""}`);
    }
    if (g.includes("night_return")) {
      parts.push(`<div class="sec">${ge(this._t("goal").night_return[0])}</div>
        <label>${ge(this._t("persons"))}</label>${this._checks('data-q="night_return.persons"', info.persons, a.night_return.persons, (p) => this._personExtra(p))}`);
    }
    if (needsAway) {
      parts.push(`<div class="sec">${ge(this._t("goal").away[0])}</div>
        <label>${ge(this._t("groups"))}</label>${this._checks('data-q="away.zones"', info.groups, a.away.zones)}
        ${g.includes("away") ? `<label>${ge(this._t("persons"))}</label>${this._checks('data-q="away.persons"', info.persons, a.away.persons, (p) => this._personExtra(p))}
        <label>${ge(this._t("delay"))}</label><input class="small" type="number" min="1" max="240" data-v="away.delay" value="${ge(a.away.delay)}">` : ""}`);
    }
    if (g.includes("return")) {
      const modes = info.return_modes.map((m) => `<option value="${m}" ${m === a.return.mode ? "selected" : ""}>${ge(this._t("modes")[m])}</option>`).join("");
      parts.push(`<div class="sec">${ge(this._t("goal").return[0])}</div>
        <label>${ge(this._t("persons"))}</label>${this._checks('data-q="return.persons"', info.persons, a.return.persons, (p) => this._personExtra(p))}
        <label>${ge(this._t("mode"))}</label><select data-v="return.mode">${modes}</select>`);
    }
    return parts.join("");
  }

  _reaction() {
    const info = this._info;
    const a = this._answers;
    const sirens = info.sirens.length
      ? this._checks("data-s", info.sirens, a.sirens, (s) => (s.registered ? ` <span class="muted">(${ge(this._t("registered"))})</span>` : ""))
      : `<div class="muted">${ge(this._t("noSirens"))}</div>`;
    const notify = info.notify.length ? this._checks("data-n", info.notify, a.notify) : `<div class="muted">${ge(this._t("noNotify"))}</div>`;
    const release = info.hardware_enabled ? this._t("released") : this._t("notReleased");
    return `<div class="sec">${ge(this._t("sirens"))}</div><div class="muted">${ge(this._t("sirensHint"))}</div>${sirens}<div class="muted">${ge(release)}</div>
      <div class="sec">${ge(this._t("notify"))}</div>${notify}`;
  }

  _planHtml() {
    if (!this._plan) return `<div class="muted">${ge(this._t("computing"))}</div>`;
    const { plan, scenarios, findings } = this._plan;
    const errors = plan.errors.length ? `<div class="sec err">${ge(this._t("errors"))}</div><div class="list">${plan.errors.map((e) => `<div class="err">${ge(e)}</div>`).join("")}</div>` : "";
    const steps = plan.steps
      .map((s) => {
        const rows = s.changes
          .map((c) => {
            const marks = [c.overwrite ? this._t("overwrite") : "", c.weakens ? this._t("weakens") : ""].filter(Boolean).join(", ");
            return `<tr><td>${ge(c.label)}</td><td class="muted">${ge(c.before)}</td><td>→ <b>${ge(c.after)}</b>${marks ? ` <span class="mark">⚠ ${ge(marks)}</span>` : ""}</td></tr>`;
          })
          .join("");
        return `<div class="step"><b>${ge(s.title)}</b>${rows ? `<table>${rows}</table>` : `<div class="muted">${ge(this._t("noChanges"))}</div>`}</div>`;
      })
      .join("");
    const notes = plan.notes.length ? `<div class="sec">${ge(this._t("notes"))}</div><div class="list">${plan.notes.map((n) => `<div>${ge(n)}</div>`).join("")}</div>` : "";
    const icon = { error: "⛔", warning: "⚠️", tip: "💡", bad: "❌", warn: "⚠️", ok: "✅" };
    const found = findings.length ? `<div class="sec">${ge(this._t("findings"))}</div><div class="list">${findings.map((f) => `<div>${icon[f.level] || ""} ${ge(f.text)}</div>`).join("")}</div>` : "";
    const sc = scenarios.length ? `<div class="sec">${ge(this._t("scenarios"))}</div>${scenarios.map((s) => `<div class="sc">${icon[s.result] || ""} <b>${ge(s.title)}</b> – ${ge(s.summary)}</div>`).join("")}` : "";
    const confirm = plan.needs_confirm && !plan.errors.length ? `<label class="chk"><input type="checkbox" data-confirm> ${ge(this._t("confirm"))}</label>` : "";
    return `${errors}<div class="muted">${ge(this._t("planIntro"))}</div>${steps}${notes}${found}${sc}${confirm}`;
  }

  // --- Ablauf --------------------------------------------------------------------------

  _collect() {
    const root = this.shadowRoot;
    const a = this._answers;
    if (!a) return;
    if (this._step === 1) a.goals = [...root.querySelectorAll("[data-goal]")].filter((el) => el.checked).map((el) => el.dataset.goal);
    if (this._step === 2) {
      root.querySelectorAll("[data-q]").forEach((el) => {
        const [sec, key] = el.dataset.q.split(".");
        a[sec][key] = [...root.querySelectorAll(`[data-q="${CSS.escape(el.dataset.q)}"]`)].filter((x) => x.checked).map((x) => x.dataset.id);
      });
      root.querySelectorAll("[data-v]").forEach((el) => {
        const [sec, key] = el.dataset.v.split(".");
        a[sec][key] = el.type === "number" ? Number(el.value) : el.value || null;
      });
    }
    if (this._step === 3) {
      a.sirens = [...root.querySelectorAll("[data-s]")].filter((el) => el.checked).map((el) => el.dataset.s);
      a.notify = [...root.querySelectorAll("[data-n]")].filter((el) => el.checked).map((el) => el.dataset.n);
    }
  }

  async _computePlan() {
    this._plan = null;
    this._render();
    try {
      this._plan = await this.hass.callWS({ type: "hauswacht/goals/plan", answers: this._answers, language: this._lang });
    } catch (err) {
      this._message = `${err?.message || err}`;
    }
    this._render();
  }

  async _apply() {
    const sure = this.shadowRoot.querySelector("[data-confirm]");
    this._busy = true;
    this._message = null;
    this._render();
    let result;
    try {
      result = await this.hass.callWS({
        type: "hauswacht/goals/apply",
        revision: this._info.revision,
        answers: this._answers,
        confirm: Boolean(sure?.checked),
        language: this._lang,
      });
    } catch (_err) {
      result = { ok: false, errors: { base: "failed" } };
    }
    this._busy = false;
    if (result.ok) {
      this.dispatchEvent(new CustomEvent("hw-saved", { bubbles: true, composed: true, detail: { revision: result.revision } }));
      return;
    }
    const code = result.errors?.base || "failed";
    this._message = this._t("fail")[code] || `${this._t("fail").failed} (${code})`;
    this._render();
  }

  _render() {
    const style = (window.HauswachtEditStyle || "") + GOALS_STYLE;
    const top = this.shadowRoot.querySelector(".sheet")?.scrollTop || 0;
    let body;
    if (!this._info) body = `<div class="muted">${ge(this._message || this._t("loading"))}</div>`;
    else body = [() => this._household(), () => this._goals(), () => this._questions(), () => this._reaction(), () => this._planHtml()][this._step]();
    const steps = this._t("steps").map((s, i) => `<span class="${i === this._step ? "on" : ""}">${i + 1}. ${ge(s)}</span>`).join("");
    const last = this._step === 4;
    const armed = this._info && !this._info.editable ? `<div class="muted">${ge(this._t("armedNote"))}</div>` : "";
    const canApply = last && this._plan && !this._plan.plan.errors.length && this._info.editable && !this._busy;
    const needsGoal = this._step === 1 && this._answers && !this._answers.goals.length;
    this.shadowRoot.innerHTML = `<style>${style}</style><div class="sheet">
      <h2>${ge(this._t("title"))}</h2><div class="stepper">${steps}</div>
      ${body}${armed}
      ${this._message && this._info ? `<div class="err">${ge(this._message)}</div>` : ""}
      <div class="bar">
        ${this._step > 0 ? `<button class="b" data-act="back">${ge(this._t("back"))}</button>` : ""}
        ${!last && this._info ? `<button class="b p" data-act="next" ${needsGoal ? "disabled" : ""}>${ge(this._t("next"))}</button>` : ""}
        ${last ? `<button class="b p" data-act="apply" ${canApply ? "" : "disabled"}>${ge(this._busy ? this._t("applying") : this._t("apply"))}</button>` : ""}
        <button class="b" data-act="cancel">${ge(this._t("cancel"))}</button>
      </div></div>`;
    this.shadowRoot.querySelector(".sheet").scrollTop = top;
    window.HauswachtDocs?.decorate(this.shadowRoot, "goals", this._lang);
    this._wire();
  }

  _wire() {
    const root = this.shadowRoot;
    this.onclick = (ev) => {
      if (ev.composedPath()[0] === this) this._close();
    };
    root.querySelectorAll("[data-act]").forEach((btn) =>
      btn.addEventListener("click", () => {
        const act = btn.dataset.act;
        this._message = null;
        if (act === "cancel") return this._close();
        this._collect();
        if (act === "back") {
          this._step = Math.max(0, this._step - 1);
          root.querySelector(".sheet").scrollTop = 0;
          return this._render();
        }
        if (act === "next") {
          this._step += 1;
          root.querySelector(".sheet").scrollTop = 0;
          if (this._step === 4) return this._computePlan();
          return this._render();
        }
        if (act === "apply") return this._apply();
        return undefined;
      })
    );
    // Ziele an/aus: „Weiter“ gleich freigeben bzw. sperren
    root.querySelectorAll("[data-goal]").forEach((el) =>
      el.addEventListener("change", () => {
        this._collect();
        this._render();
      })
    );
    const sure = root.querySelector("[data-confirm]");
    const apply = root.querySelector('[data-act="apply"]');
    if (sure && apply) {
      apply.disabled = true;
      sure.addEventListener("change", () => (apply.disabled = !sure.checked || this._busy));
    }
  }

  _close() {
    this.dispatchEvent(new CustomEvent("hw-close", { bubbles: true, composed: true }));
  }
}

if (!customElements.get("hauswacht-goals-sheet")) {
  customElements.define("hauswacht-goals-sheet", HauswachtGoalsSheet);
}
