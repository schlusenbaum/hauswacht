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
    secPassage: "Durchgang – rein oder raus, bleibt scharf",
    passageOn: "Durchgang erlauben",
    passageHint: "Gedacht für Profile, die nur die Außenhaut überwachen: Melder im Haus bleiben scharf – der Durchgang hilft nur an den Außentüren. Reinkommen: in der Eingangsverzögerung PIN oder Karte und eine Profil-Taste (oder die Durchgang-Taste) am Keypad. Rausgehen: solange scharf, PIN oder Karte und irgendeine Profil-Taste (es wird nie umgeschaltet) oder die Durchgang-Taste.",
    passageDuration: "Durchgangszeit (Minuten)",
    passageOutDoors: "Rausgehen: welche Tür",
    passageOutEnd: "Rausgehen: Ende",
    passagePath: "Melder auf dem Weg (z. B. Bewegungsmelder in der Einfahrt)",
    passagePathAfter: "Reinkommen: Weg noch frei nach dem Schließen (s)",
    outDoors: { first: "nur die erste Tür, die aufgeht", all: "alle Eingangstüren" },
    outEnd: { time: "nach Ablauf der Zeit", returned: "schon, wenn ich zurück bin und die Tür zu ist" },
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
    passagePhoneMoved: "Handy-Reinlassen ist umgezogen: oben bei „Bei Rückkehr“ → „Reinlassen (Durchgang)“.",
    secReturn: "Bei Rückkehr",
    returnIntro: "Was Hauswacht tut, wenn eine bestimmte Person nach Hause kommt. Grundlage ist der Personen-Status in Home Assistant (meist das Handy).",
    returnMode: "Wenn jemand heimkommt",
    returnPersons: "Für diese Personen",
    returnWindow: "Zeitfenster Handy und Tür (Minuten)",
    returnWindowRec: "Empfehlung: 5 Minuten. Länger macht es bequemer, aber auch etwas unsicherer.",
    returnAlwaysWarn: "Achtung: In diesem Modus reicht das Handy allein. Wer das Handy einer Person hat (oder es verliert und jemand findet es), kann nach Hause kommen und die Anlage schaltet unscharf – ohne Tür, ohne PIN. Sicherer ist „Unscharf mit Türbeleg“.",
    moreSettings: "Mehr Einstellungen",
    howLabel: "So verhält sich das:",
    infoLabel: "Erklärung",
    approachDelay: "Eingangsverzögerung nach Annäherung (Sekunden, 0 = aus)",
    approachValid: "Annäherung gilt (Minuten)",
    approachDelayRec: "Empfehlung aus der Messung: {r} s (längste Zeit „Tür auf“ bis „zuhause“ plus Puffer).",
    approachDelayRecDefault: "Noch keine Messung. Typisch: 60–120 s. Empfehlung kommt, sobald die Personen in der Heimkehr-Beobachtung sind und ein paar Mal heimgekommen sind.",
    approachValidRec: "Empfehlung aus der Messung: {r} min (längste Zeit „nähert sich“ bis zur Tür plus 5 min).",
    approachValidRecDefault: "Empfehlung: 15 Minuten.",
    approachTooShort: "Wirkt nicht: nicht länger als die normale Eingangsverzögerung ({n} s). Verlängert wird nur, nie verkürzt.",
    approachHow: "Hat sich eine der Personen in den letzten {v} Minuten genähert (Richtung „nähert sich“), wartet Hauswacht nach dem Öffnen {s} s statt {n} s auf das Handy. Wer sich nicht genähert hat – etwa ein Einbrecher –, hat weiter nur {n} s.",
    apply: "übernehmen",
    noFix: "⚠ keine Ortung – gilt nie als weg",
    noFixHint: "Hauswacht findet für diese Person keine Ortung mit Koordinaten (z. B. Companion App mit Standort). Ohne Ortung außerhalb gilt sie nie als weg: „Scharf, wenn alle weg“ wartet dann für immer, „Bei Rückkehr“ löst nie aus. Abhilfe: in der Companion App den Standort auf „Immer“ stellen oder unter System → Anwesenheit einen GPS-Tracker als Signal eintragen.",
    returnModes: { off: "Nichts", auto_only: "Unscharf, nur wenn automatisch scharf", door: "Unscharf mit Türbeleg", always: "Unscharf, auch nach Scharfschalten von Hand", passage: "Reinlassen (Durchgang)" },
    returnHow: {
      off: "Hauswacht tut nichts, wenn jemand heimkommt. Unscharf geht nur per PIN, Karte, Keypad oder App.",
      auto_only: "Kommt eine der Personen heim, schaltet Hauswacht unscharf – aber nur, wenn das Profil vorher automatisch scharf geworden ist (zum Beispiel, weil alle weg waren). Hast du von Hand scharf geschaltet, bleibt es scharf.",
      door: "Meldet das Handy einer Person „zuhause“ und geht höchstens {w} Minuten davor oder danach eine Eingangstür auf, schaltet Hauswacht unscharf – auch wenn von Hand scharf geschaltet wurde. Ohne Türöffnung passiert nichts. Beispiel: Du fährst in die Einfahrt, das Handy meldet „zuhause“, du schließt die Haustür auf – unscharf, kein Alarm.",
      always: "Meldet das Handy einer Person „zuhause“ und war sie vorher mindestens 5 Minuten weg, schaltet Hauswacht sofort unscharf – egal wie scharf geschaltet wurde. Eine Tür muss dafür nicht aufgehen.",
      passage: "Geht eine Eingangstür auf und meldet das Handy einer Person bis zu {w} Minuten vorher oder noch während der Eingangsverzögerung „zuhause“ (vorher mindestens 5 Minuten weg), lässt Hauswacht sie ohne PIN herein. Das Profil bleibt scharf – wie beim Durchgang. Kommt das Handy nicht rechtzeitig, gibt es Alarm wie immer.",
    },
    info: {
      mode: "Wähle, wie Hauswacht reagiert, wenn eine der Personen unten heimkommt. „Unscharf mit Türbeleg“ ist für die meisten Häuser die beste Wahl: Es braucht das Handy UND eine Tür. „Reinlassen (Durchgang)“ passt zu Nachtprofilen, in denen der Rest im Haus scharf bleiben soll.",
      persons: "Nur diese Personen lösen „Bei Rückkehr“ aus. Die Liste ist unabhängig von „Scharf, wenn alle diese Personen weg sind“. Ohne Person lässt sich der Modus nicht speichern.",
      approachDelay: "Braucht einen Richtungs-Sensor der Person (Integration „Nähe“ oder Places) unter System → Anwesenheit. Meldet er „nähert sich“ und geht danach eine Eingangstür auf, bekommt die Person so viel Zeit, bis ihr Handy „zuhause“ meldet. Die Richtung allein schaltet nie unscharf. Nur länger als die normale Eingangsverzögerung wirkt.",
      approachValid: "So lange nach „nähert sich“ gilt die Annäherung. Zu kurz: Wer langsam kommt (Parkplatz suchen), bekommt keine Verlängerung. Zu lang: Die längere Zeit gilt auch noch für eine spätere Türöffnung.",
      window: "So weit dürfen Handy-Meldung „zuhause“ und Türöffnung auseinanderliegen. Manche Handys melden erst spät. Zu kurz: Hauswacht erkennt dich nicht. Zu lang: ein größeres Fenster für Fremde.",
    },
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
    errors: {
      profile_name_required: "Bitte einen Namen eingeben.",
      profile_name_taken: "Diesen Namen gibt es schon.",
      panel_mode_taken: "Diesen Knopf hat in diesem Bereich schon ein anderes Profil.",
      excluded_not_in_groups: "Ausgenommene Melder müssen in den gewählten Gruppen sein.",
      return_needs_persons: "„Bei Rückkehr“ braucht mindestens eine Person – bitte bei „Für diese Personen“ eine ankreuzen.",
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
    secPassage: "Passage – in or out, stays armed",
    passageOn: "Allow passage",
    passageHint: "Meant for profiles that only watch the outer shell: sensors inside stay armed – the passage only helps at the outer doors. Coming in: during the entry delay, PIN or card and any profile key (or the passage key) at the keypad. Going out: while armed, PIN or card and any profile key (never switches profile) or the passage key.",
    passageDuration: "Passage time (minutes)",
    passageOutDoors: "Going out: which door",
    passageOutEnd: "Going out: end",
    passagePath: "Sensors on the way (e.g. motion sensor in the driveway)",
    passagePathAfter: "Coming in: way still free after closing (s)",
    outDoors: { first: "only the first door that opens", all: "all entry doors" },
    outEnd: { time: "when the time is up", returned: "as soon as I am back and the door is closed" },
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
    passagePhoneMoved: "Letting in by phone has moved: above at “On return” → “Let in (passage)”.",
    secReturn: "On return",
    returnIntro: "What Hauswacht does when a certain person comes home. It is based on the person state in Home Assistant (usually the phone).",
    returnMode: "When someone comes home",
    returnPersons: "For these persons",
    returnWindow: "Time window phone and door (minutes)",
    returnWindowRec: "Recommendation: 5 minutes. Longer is more convenient, but also a bit less secure.",
    returnAlwaysWarn: "Caution: in this mode the phone alone is enough. Whoever has a person's phone (or finds a lost one) can come home and the system disarms – without door, without PIN. “Disarm with door proof” is safer.",
    moreSettings: "More settings",
    howLabel: "This is how it behaves:",
    infoLabel: "Explanation",
    approachDelay: "Entry delay after approach (seconds, 0 = off)",
    approachValid: "Approach is valid for (minutes)",
    approachDelayRec: "Recommendation from the measurement: {r} s (longest time “door open” to “home” plus buffer).",
    approachDelayRecDefault: "No measurement yet. Typical: 60–120 s. A recommendation appears once the persons are in the homecoming observation and have come home a few times.",
    approachValidRec: "Recommendation from the measurement: {r} min (longest time “approaching” to the door plus 5 min).",
    approachValidRecDefault: "Recommendation: 15 minutes.",
    approachTooShort: "Has no effect: not longer than the normal entry delay ({n} s). It only extends, never shortens.",
    approachHow: "If one of the persons approached in the last {v} minutes (direction “towards”), Hauswacht waits {s} s instead of {n} s for the phone after the door opens. Whoever did not approach – such as a burglar – still only has {n} s.",
    apply: "apply",
    noFix: "⚠ no location – never counts as away",
    noFixHint: "Hauswacht finds no location with coordinates for this person (e.g. Companion app with location). Without a location outside, the person never counts as away: “arm when all away” then waits forever, “On return” never triggers. Fix: set the location in the Companion app to “Always” or add a GPS tracker as a signal under System → Presence.",
    returnModes: { off: "Nothing", auto_only: "Disarm, only if armed automatically", door: "Disarm with door proof", always: "Disarm, also after arming by hand", passage: "Let in (passage)" },
    returnHow: {
      off: "Hauswacht does nothing when someone comes home. Disarming only by PIN, card, keypad or app.",
      auto_only: "If one of the persons comes home, Hauswacht disarms – but only if the profile was armed automatically before (for example because everyone was away). If you armed by hand, it stays armed.",
      door: "If a person's phone reports “home” and an entry door opens at most {w} minutes before or after, Hauswacht disarms – even if armed by hand. Without a door opening nothing happens. Example: you drive into the driveway, the phone reports “home”, you unlock the front door – disarmed, no alarm.",
      always: "If a person's phone reports “home” and the person was away for at least 5 minutes before, Hauswacht disarms right away – no matter how it was armed. No door needs to open.",
      passage: "If an entry door opens and a person's phone reports “home” up to {w} minutes before or while the entry delay is still running (away for at least 5 minutes before), Hauswacht lets them in without PIN. The profile stays armed – like a passage. If the phone is too late, the alarm comes as always.",
    },
    info: {
      mode: "Choose how Hauswacht reacts when one of the persons below comes home. “Disarm with door proof” is the best choice for most homes: it needs the phone AND a door. “Let in (passage)” suits night profiles in which the rest of the house should stay armed.",
      persons: "Only these persons trigger “On return”. The list is independent of “Arm when all these persons are away”. Without a person the mode cannot be saved.",
      approachDelay: "Needs a direction sensor of the person (Proximity integration or Places) under System → Presence. If it reports “towards” and an entry door opens afterwards, the person gets this much time until their phone reports “home”. The direction alone never disarms. Only longer than the normal entry delay has an effect.",
      approachValid: "How long an approach stays valid after “towards”. Too short: whoever comes slowly (looking for parking) gets no extension. Too long: the longer time also applies to a later door opening.",
      window: "How far apart the phone reporting “home” and the door opening may be. Some phones report late. Too short: Hauswacht does not recognise you. Too long: a bigger window for strangers.",
    },
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
    errors: {
      profile_name_required: "Please enter a name.",
      profile_name_taken: "This name already exists.",
      panel_mode_taken: "Another profile in this area already has this button.",
      excluded_not_in_groups: "Excluded sensors must be in the chosen groups.",
      return_needs_persons: "“On return” needs at least one person – please tick one at “For these persons”.",
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
  .nofix { margin-left: 8px; font-size: .85rem; color: var(--warning-color, #ff9800); cursor: help; }
  .info { border: none; background: none; color: var(--primary-color); cursor: help; font-size: 1rem; padding: 0 2px; }
  .tip { font-size: .85rem; margin: 4px 0 6px; padding: 8px 10px; border-radius: 6px; background: var(--secondary-background-color); }
  .how { margin: 8px 0 4px; font-size: .9rem; }
  .warn { margin: 6px 0; padding: 8px 10px; border-radius: 6px; border-left: 3px solid var(--warning-color, #ff9800); background: var(--secondary-background-color); font-size: .9rem; }
  details.more { margin-top: 10px; }
  details.more summary { cursor: pointer; color: var(--primary-color); }
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
    return `<label>${pe(label)}</label><input data-k="${pe(key)}" value="${pe(value ?? "")}">${this._err(key)}`;
  }

  _num(key, value, label, min, max) {
    return `<div><label>${pe(label)}</label><input type="number" min="${min}" max="${max}" data-k="${pe(key)}" data-num="1" value="${pe(value)}"></div>`;
  }

  _select(key, value, label, options) {
    return `<label>${pe(label)}</label><select data-k="${pe(key)}">${options.map(([v, l]) => `<option value="${pe(v)}" ${v === value ? "selected" : ""}>${pe(l)}</option>`).join("")}</select>${this._err(key)}`;
  }

  _check(key, value, label) {
    return `<div class="chk"><input type="checkbox" data-k="${pe(key)}" data-bool="1" ${value ? "checked" : ""}><span>${pe(label)}</span></div>`;
  }

  _multi(key, chosen, items, label, empty) {
    const body = items.length
      ? items.map(([v, l]) => `<div class="chk"><input type="checkbox" data-m="${pe(key)}" value="${pe(v)}" ${chosen.includes(v) ? "checked" : ""}><span>${pe(l)}</span></div>`).join("")
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
    const pass = d.passage;
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
      <label>${pe(this._t("persons"))}</label>${c.persons.map((x) => `<div class="chk"><input type="checkbox" data-am="auto_away_persons" value="${pe(x.id)}" ${a.auto_away_persons.includes(x.id) ? "checked" : ""}><span>${pe(x.name)}</span>${this._noFix(x)}</div>`).join("") || `<div class="muted">${pe(this._t("none"))}</div>`}
      <label>${pe(this._t("awayDelay"))}</label><input class="small" type="number" min="1" max="${lim.away_delay}" data-a="auto_away_delay" data-num="1" value="${pe(a.auto_away_delay)}">
${this._returnSection(c, lim, t)}
      <div class="sec">${pe(this._t("secClose"))}</div>
      <div class="chk"><input type="checkbox" data-c="enabled" ${close.enabled ? "checked" : ""}><span>${pe(this._t("closeOn"))}</span></div>
      <label>${pe(this._t("doors"))}</label>${doors.map((id) => `<div class="chk"><input type="checkbox" data-cm="doors" value="${pe(id)}" ${close.doors.includes(id) ? "checked" : ""}><span>${pe(this._name(id))}</span></div>`).join("") || `<div class="muted">${pe(this._t("noDoors"))}</div>`}
      <label>${pe(this._t("settle"))}</label><input class="small" type="number" min="1" max="${lim.settle}" data-c="settle" data-num="1" value="${pe(close.settle)}">
      <div class="sec">${pe(this._t("secPassage"))}</div>
      <div class="chk"><input type="checkbox" data-p="enabled" ${pass.enabled ? "checked" : ""}><span>${pe(this._t("passageOn"))}</span></div>
      <div class="muted">${pe(this._t("passageHint"))}</div>
      <div class="two"><div><label>${pe(this._t("passageDuration"))}</label><input type="number" min="1" max="${lim.passage_duration}" data-p="duration" data-num="1" value="${pe(pass.duration)}"></div>
      <div><label>${pe(this._t("passagePathAfter"))}</label><input type="number" min="0" max="${lim.passage_after}" data-p="path_after" data-num="1" value="${pe(pass.path_after)}"></div></div>
      <label>${pe(this._t("passageOutDoors"))}</label><select data-p="out_doors">${["first", "all"].map((v) => `<option value="${v}" ${v === pass.out_doors ? "selected" : ""}>${pe(t("outDoors", v))}</option>`).join("")}</select>
      <label>${pe(this._t("passageOutEnd"))}</label><select data-p="out_end">${["time", "returned"].map((v) => `<option value="${v}" ${v === pass.out_end ? "selected" : ""}>${pe(t("outEnd", v))}</option>`).join("")}</select>
      <label>${pe(this._t("passagePath"))}</label>${members.map((id) => `<div class="chk"><input type="checkbox" data-pm="path" value="${pe(id)}" ${pass.path.includes(id) ? "checked" : ""}><span>${pe(this._name(id))}</span></div>`).join("") || `<div class="muted">${pe(this._t("noMembers"))}</div>`}
      <div class="muted">${pe(this._t("passagePhoneMoved"))}</div>
      ${this._err("base")}`;
  }

  // --- Bei Rückkehr (ADR 0015) ----------------------------------------------------

  _info(key) {
    // ⓘ: Mauszeiger drauf zeigt den Text, Tippen klappt ihn auf
    const text = this._t("info")[key] || "";
    return `<button type="button" class="info" data-info="${pe(key)}" title="${pe(text)}" aria-label="${pe(this._t("infoLabel"))}">ⓘ</button><div class="tip" data-tip="${pe(key)}" hidden>${pe(text)}</div>`;
  }

  _noFix(person) {
    // Ohne Ortung gilt die Person nie als weg („weg“ nur mit Beleg, ADR 0015)
    return person.locatable === false ? `<span class="nofix" title="${pe(this._t("noFixHint"))}">${pe(this._t("noFix"))}</span>` : "";
  }

  _returnHow(back) {
    let text = ((this._t("returnHow") || {})[back.mode] || "").replace("{w}", String(back.window));
    const normal = Number(this._draft.entry_delay) || 0;
    if (["door", "passage"].includes(back.mode) && back.approach_delay > normal) {
      text += " " + this._t("approachHow").replace("{v}", String(back.approach_valid)).replace("{s}", String(back.approach_delay)).replaceAll("{n}", String(normal));
    }
    return text;
  }

  _approachRec(back) {
    // Empfehlungen aus der Heimkehr-Beobachtung für die Personen der Liste
    const advice = this.settings.profile_edit.return_advice || {};
    const rows = back.persons.map((p) => advice[p]).filter(Boolean);
    const delays = rows.map((r) => r.entry_delay).filter((v) => v);
    const valid = rows.map((r) => r.approach_minutes).filter((v) => v);
    return {
      delay: delays.length ? Math.max(...delays) : null,
      valid: valid.length ? Math.min(Math.max(...valid), this.settings.profile_edit.limits.approach_valid) : null,
    };
  }

  _recLine(field, value, current, textMeasured, textDefault) {
    const text = value === null ? textDefault : textMeasured.replace("{r}", String(value));
    const button = value !== null && Number(current) !== value ? ` <button type="button" class="b" data-rec="${pe(field)}" data-value="${value}">${pe(this._t("apply"))}</button>` : "";
    return `<div class="muted">${pe(text)}${button}</div>`;
  }

  _approachFields(back, lim) {
    const rec = this._approachRec(back);
    const normal = Number(this._draft.entry_delay) || 0;
    const weak = back.approach_delay > 0 && back.approach_delay <= normal;
    return `
        <label>${pe(this._t("approachDelay"))} ${this._info("approachDelay")}</label>
        <input class="small" type="number" min="0" max="${lim.approach_delay}" data-r="approach_delay" data-num="1" value="${pe(back.approach_delay)}">
        ${this._recLine("approach_delay", rec.delay, back.approach_delay, this._t("approachDelayRec"), this._t("approachDelayRecDefault"))}
        ${weak ? `<div class="warn">${pe(this._t("approachTooShort").replace("{n}", String(normal)))}</div>` : ""}
        ${back.approach_delay > 0 ? `<label>${pe(this._t("approachValid"))} ${this._info("approachValid")}</label>
        <input class="small" type="number" min="1" max="${lim.approach_valid}" data-r="approach_valid" data-num="1" value="${pe(back.approach_valid)}">
        ${this._recLine("approach_valid", rec.valid, back.approach_valid, this._t("approachValidRec"), this._t("approachValidRecDefault"))}` : ""}`;
  }

  _returnSection(c, lim, t) {
    const back = this._draft.return;
    const persons = c.persons.map((x) => `<div class="chk"><input type="checkbox" data-rm="persons" value="${pe(x.id)}" ${back.persons.includes(x.id) ? "checked" : ""}><span>${pe(x.name)}</span>${this._noFix(x)}</div>`).join("") || `<div class="muted">${pe(this._t("none"))}</div>`;
    const usesWindow = ["door", "passage"].includes(back.mode);
    return `
      <div class="sec">${pe(this._t("secReturn"))}</div>
      <div class="muted">${pe(this._t("returnIntro"))}</div>
      <label>${pe(this._t("returnMode"))} ${this._info("mode")}</label>
      <select data-r="mode">${c.return_modes.map((m) => `<option value="${m}" ${m === back.mode ? "selected" : ""}>${pe(t("returnModes", m))}</option>`).join("")}</select>
      <div class="how"><b>${pe(this._t("howLabel"))}</b> <span data-how>${pe(this._returnHow(back))}</span></div>
      ${back.mode === "always" ? `<div class="warn">${pe(this._t("returnAlwaysWarn"))}</div>` : ""}
      ${back.mode === "off" ? "" : `<label>${pe(this._t("returnPersons"))} ${this._info("persons")}</label>${persons}`}
      ${this._err("return")}
      ${usesWindow ? `<details class="more" ${this._moreOpen ? "open" : ""}><summary>${pe(this._t("moreSettings"))}</summary>
        <label>${pe(this._t("returnWindow"))} ${this._info("window")}</label>
        <input class="small" type="number" min="1" max="${lim.return_window}" data-r="window" data-num="1" value="${pe(back.window)}">
        <div class="muted">${pe(this._t("returnWindowRec"))}</div>
        ${this._approachFields(back, lim)}
      </details>` : ""}`;
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
    root.querySelectorAll("[data-p]").forEach((el) => {
      d.passage[el.dataset.p] = el.type === "checkbox" ? el.checked : el.dataset.num ? Number(el.value) : el.value;
    });
    d.passage.path = [...root.querySelectorAll('[data-pm="path"]')].filter((el) => el.checked).map((el) => el.value);
    root.querySelectorAll("[data-r]").forEach((el) => (d.return[el.dataset.r] = el.dataset.num ? Number(el.value) : el.value));
    if (root.querySelector('[data-rm="persons"]')) {
      d.return.persons = [...root.querySelectorAll('[data-rm="persons"]')].filter((el) => el.checked).map((el) => el.value);
    }
    const more = root.querySelector("details.more");
    if (more) this._moreOpen = more.open;
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
    window.HauswachtRevealError?.(this.shadowRoot); // Fehlermeldung ins Bild holen
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
    // ⓘ antippen klappt die Erklärung auf
    this.shadowRoot.querySelectorAll("[data-info]").forEach((btn) =>
      btn.addEventListener("click", () => {
        const tip = this.shadowRoot.querySelector(`[data-tip="${CSS.escape(btn.dataset.info)}"]`);
        if (tip) tip.hidden = !tip.hidden;
      })
    );
    // Zeitfenster und Annäherung: Erklärsatz sofort mitziehen
    this.shadowRoot.querySelectorAll('[data-r="window"], [data-r="approach_valid"]').forEach((el) =>
      el.addEventListener("input", () => {
        const how = this.shadowRoot.querySelector("[data-how]");
        if (how) how.textContent = this._returnHow({ ...this._draft.return, [el.dataset.r]: Number(el.value) || this._draft.return[el.dataset.r] });
      })
    );
    // Verlängerung an/aus blendet die Gültigkeit ein; Empfehlung übernehmen
    const redraw = () => {
      const top = this.shadowRoot.querySelector(".sheet").scrollTop;
      this._collect();
      this._render();
      this.shadowRoot.querySelector(".sheet").scrollTop = top;
    };
    this.shadowRoot.querySelector('[data-r="approach_delay"]')?.addEventListener("change", redraw);
    this.shadowRoot.querySelectorAll("[data-rec]").forEach((btn) =>
      btn.addEventListener("click", () => {
        this._collect();
        this._draft.return[btn.dataset.rec] = Number(btn.dataset.value);
        const top = this.shadowRoot.querySelector(".sheet").scrollTop;
        this._render();
        this.shadowRoot.querySelector(".sheet").scrollTop = top;
      })
    );
    // Gruppen ändern die Listen "Ausgenommen" und "Ausgangstüren", der Modus bei Rückkehr die Felder
    this.shadowRoot.querySelectorAll('[data-m="zones"], [data-r="mode"]').forEach((el) =>
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
