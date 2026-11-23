// Hauswacht – Einstellungsseite, Stufe 5: System, PIN-Regeln, Aktions-Codes, Bedienteile (ADR 0011).
//
// Seitenblatt <hauswacht-system-editor> mit den Arten restart, silence, network, homecoming,
// area, page, pinrules, actioncode, learn. Gespeichert wird über
// hauswacht/settings/apply – dieselben Regeln wie im Dialog.

const ST = {
  de: {
    save: "Speichern",
    saving: "Speichere …",
    cancel: "Abbrechen",
    del: "Löschen",
    delSure: "Wirklich löschen?",
    none: "–",
    restart: "Verhalten nach Neustart",
    behavior: "Nach einem Neustart von Home Assistant",
    behaviors: {
      restore: "Vorherigen Zustand wiederherstellen (Standard)",
      armed: "Immer scharf (mit festem Profil)",
      disarmed: "Immer unscharf",
    },
    behaviorHint: {
      restore: "War die Anlage scharf, ist sie sofort wieder scharf – mit demselben Profil, ohne erneute Prüfung. Eine laufende Eingangsverzögerung beginnt neu.",
      armed: "Etwa eine Minute nach dem Hochfahren wird das gewählte Profil normal scharf geschaltet – mit Prüfung offener Melder. Für Ferienhaus oder unbewohnte Bereiche.",
      disarmed: "Nach dem Neustart ist die Anlage unscharf. War sie scharf, kommt eine Nachricht.",
    },
    continueAlarm: "Laufenden Alarm fortsetzen (Sirenen laufen weiter)",
    continueHint: "Standard: aus – nach dem Neustart keine Sirenen, die Alarm-Empfänger bekommen eine wichtige Nachricht.",
    restartProfile: "Alarmprofil für „immer scharf“",
    silence: "Funkstille von Sensoren",
    hours: "Maximale Funkstille (Stunden, 0 = aus)",
    silenceHint: "Hat sich ein Melder so lange nicht gemeldet, gilt er beim Scharfschalten als ausgefallen. Batteriesensoren melden sich teils nur alle paar Stunden – großzügig wählen. Melder, die sich seltener melden (z. B. manche Batterie-Türkontakte), bekommen besser einen eigenen Wert: Reiter Melder → Melder anklicken → Funkstille.",
    observation: "Beobachtung",
    network: "Funknetz und Gateways",
    networkHint: "Sensoren, die melden, ob ein Funknetz oder Gateway läuft (z. B. Zigbee2MQTT-Bridge). Fällt es aus, meldet Hauswacht eine Störung. Art „Problem“: an = Störung, sonst: an = in Ordnung.",
    addEntity: "Sensor hinzufügen – Namen tippen oder aus der Liste wählen",
    homecoming: "Anwesenheit und Heimkehr-Beobachtung",
    observe: "Heimkehr beobachten (schaltet nichts, misst nur)",
    persons: "Personen für die Beobachtung",
    ssids: "Heim-WLAN(s), durch Komma getrennt",
    signals: "Zusätzliche Signale je Person",
    signalsHint: "Gelten auch für die Profil-Automatik („alle weg“, „Rückkehr“) – z. B. WLAN-Sensor der Companion App.",
    area: "Bereich",
    areaNew: "Bereich anlegen",
    name: "Name",
    icon: "Symbol (z. B. mdi:garage)",
    areaProfiles: "Profile in diesem Bereich",
    page: "Einstellungsseite",
    pageShow: "Seite „Hauswacht“ in der Seitenleiste anzeigen",
    pageWarn: "Ausgeblendet verschwindet diese Seite nach dem Speichern. Wieder einblenden: im Dialog unter Systemeinstellungen → Einstellungsseite.",
    pinrules: "PIN-Regeln und Master-PIN",
    pinUsers: "Personen mit PIN",
    master: "Master-PIN",
    masterSet: "Master-PIN gesetzt",
    masterNone: "Kein Master-PIN",
    masterNew: "Neuer Master-PIN (4–8 Ziffern, leer = nicht ändern)",
    masterRemove: "Master-PIN entfernen",
    masterHint: "Ein einfacher PIN ohne eigene Person, z. B. damit Alexa nur mit PIN unscharf schaltet.",
    codeArm: "PIN auch zum Scharfschalten verlangen",
    endNoPin: "Alarm beenden ohne PIN",
    buttonsNoPin: "Dashboard-Knöpfe trotz PIN erlauben",
    cardPinUnlinked: "Alarmkarte: PIN für Konten ohne Hauswacht-Person verlangen",
    pinWarn: "Sobald ein PIN existiert, verlangt das Bedienfeld (und Alexa) zum Unscharfschalten einen PIN – von allen.",
    actioncode: "Aktions-Code",
    actioncodeNew: "Aktions-Code anlegen",
    code: "Code (2–8 Ziffern)",
    key: "Taste",
    keys: { arm_day_zones: "🏠 Haus (Tag)", arm_night_zones: "🌙 Nacht", arm_all_zones: "🔒 Schloss (Alle)", disarm: "🔓 offenes Schloss (Unscharf)" },
    keypad: "Keypad",
    allKeypads: "Alle Keypads",
    action: "Aktion",
    actions: { event: "Ereignis für eigene Automation", arm: "Scharf schalten mit Profil …", silent_emergency: "Stiller Notruf" },
    profile: "Alarmprofil",
    codeHint: "Kein Ausweis: Ein Aktions-Code kann nie unscharf schalten und darf keinem PIN gleichen. Derselbe Code darf mit verschiedenen Tasten verschiedene Aktionen haben.",
    learn: "Anlernzeit für neue Karten",
    helper: "Melder aus Messwert erstellen",
    helperInfo: "Macht aus einem Messwert (z. B. Temperatur, Feuchte, Leistung) einen Melder: Hauswacht legt einen Schwellenwert-Helfer in Home Assistant an (danach unter Einstellungen → Geräte & Dienste → Helfer änderbar und löschbar) und setzt ihn gleich ein. Bestehendes bleibt unverändert.",
    source: "Messwert",
    helperName: "Name des neuen Melders",
    upper: "Oberer Grenzwert (löst aus, wenn darüber)",
    lower: "Unterer Grenzwert (löst aus, wenn darunter)",
    hysteresis: "Hysterese (Abstand, ab dem wieder „normal“ gilt)",
    type: "Typ",
    target: "Einsetzen in",
    targetAlways: "Immer aktiv",
    minutes: "Minuten (0 = Anlernen aus)",
    learnHint: "So lange merkt sich Hauswacht eine unbekannte Karte, die an einem Keypad oder Leser gelesen wurde, zum Anlernen. 0 = Anlernen aus.",
    errors: {
      restart_needs_profile: "„Immer scharf“ braucht mindestens ein Alarmprofil.",
      area_has_profiles: "Diesem Bereich gehören noch Alarmprofile – erst die Profile löschen oder einem anderen Bereich zuordnen.",
      area_name_taken: "Diesen Namen hat bereits ein anderer Bereich.",
      area_name_required: "Bitte einen Namen angeben.",
      invalid_pin: "PIN: 4 bis 8 Ziffern.",
      pin_is_action_code: "Diese Ziffern sind schon ein Aktions-Code.",
      pin_is_duress: "Dieser PIN ist schon Bedrohungs-PIN von: {c}",
      user_name_required: "Bitte einen Namen eingeben.",
      action_code_name_taken: "Diesen Namen hat schon ein anderer Aktions-Code.",
      action_code_invalid: "Bitte 2 bis 8 Ziffern eingeben.",
      action_code_taken: "Diesen Code mit dieser Taste gibt es schon („{c}“).",
      action_code_profile_missing: "Bitte ein Alarmprofil wählen.",
      action_code_is_pin: "Dieser Code ist schon ein PIN oder Bedrohungs-PIN – bitte einen anderen wählen.",
      helper_no_limit: "Bitte einen oberen und/oder unteren Grenzwert angeben.",
      helper_range: "Der untere Grenzwert muss kleiner sein als der obere.",
      helper_name: "Bitte einen Namen angeben.",
      helper_failed: "Der Helfer konnte nicht angelegt werden (siehe Protokoll).",
      control_entity: "Bitte einen Messwert (sensor.…) wählen.",
      invalid: "Ungültiger Wert.",
      disarm_first: "Erst alle Bereiche unscharf schalten – dann lässt sich speichern.",
      changed_elsewhere: "Inzwischen wurde woanders etwas geändert. Die Seite lädt neu – bitte noch einmal.",
      failed: "Speichern fehlgeschlagen.",
    },
  },
  en: {
    save: "Save",
    saving: "Saving …",
    cancel: "Cancel",
    del: "Delete",
    delSure: "Really delete?",
    none: "–",
    restart: "Behaviour after restart",
    behavior: "After a restart of Home Assistant",
    behaviors: {
      restore: "Restore the previous state (default)",
      armed: "Always armed (with a fixed profile)",
      disarmed: "Always disarmed",
    },
    behaviorHint: {
      restore: "If the system was armed, it is armed again right away – same profile, no new check. A running entry delay starts over.",
      armed: "About a minute after start-up the chosen profile is armed normally – with the check for open sensors. For holiday homes or unoccupied areas.",
      disarmed: "After the restart the system is disarmed. If it was armed, you get a message.",
    },
    continueAlarm: "Continue a running alarm (sirens keep sounding)",
    continueHint: "Default: off – after the restart no sirens, the alarm recipients get an important message.",
    restartProfile: "Alarm profile for “always armed”",
    silence: "Sensor radio silence",
    hours: "Maximum radio silence (hours, 0 = off)",
    silenceHint: "If a sensor has not reported for this long, it counts as failed when arming. Battery sensors sometimes only report every few hours – choose generously. Sensors that report less often (e.g. some battery door contacts) are better given an own value: tab sensors → click the sensor → radio silence.",
    observation: "Observation",
    network: "Radio networks and gateways",
    networkHint: "Sensors that report whether a radio network or gateway is running (e.g. Zigbee2MQTT bridge). If it fails, Hauswacht reports a fault. Class “problem”: on = fault, otherwise: on = OK.",
    addEntity: "Add sensor – type a name or pick from the list",
    homecoming: "Presence and homecoming observation",
    observe: "Observe homecoming (switches nothing, only measures)",
    persons: "Persons for the observation",
    ssids: "Home Wi-Fi(s), separated by commas",
    signals: "Additional signals per person",
    signalsHint: "Also apply to the profile automation (“everyone away”, “arrival”) – e.g. the Wi-Fi sensor of the companion app.",
    area: "Area",
    areaNew: "Add area",
    name: "Name",
    icon: "Icon (e.g. mdi:garage)",
    areaProfiles: "Profiles in this area",
    page: "Settings page",
    pageShow: "Show the page “Hauswacht” in the sidebar",
    pageWarn: "When hidden, this page disappears after saving. To show it again: in the dialog under system settings → settings page.",
    pinrules: "PIN rules and master PIN",
    pinUsers: "People with PIN",
    master: "Master PIN",
    masterSet: "Master PIN set",
    masterNone: "No master PIN",
    masterNew: "New master PIN (4–8 digits, empty = keep)",
    masterRemove: "Remove master PIN",
    masterHint: "A simple PIN without a person of its own, e.g. so that Alexa only disarms with a PIN.",
    codeArm: "Also require the PIN to arm",
    endNoPin: "End an alarm without PIN",
    buttonsNoPin: "Allow dashboard buttons despite PIN",
    cardPinUnlinked: "Alarm card: require PIN for accounts without a Hauswacht person",
    pinWarn: "As soon as one PIN exists, the alarm panel (and Alexa) requires a PIN to disarm – from everyone.",
    actioncode: "Action code",
    actioncodeNew: "Add action code",
    code: "Code (2–8 digits)",
    key: "Key",
    keys: { arm_day_zones: "🏠 House (day)", arm_night_zones: "🌙 Night", arm_all_zones: "🔒 Lock (all)", disarm: "🔓 Open lock (disarm)" },
    keypad: "Keypad",
    allKeypads: "All keypads",
    action: "Action",
    actions: { event: "Event for your own automation", arm: "Arm with profile …", silent_emergency: "Silent emergency" },
    profile: "Alarm profile",
    codeHint: "Not a credential: an action code can never disarm and must not equal a PIN. The same code may have different actions with different keys.",
    learn: "Learning time for new cards",
    helper: "Create sensor from a measurement",
    helperInfo: "Turns a measurement (e.g. temperature, humidity, power) into a sensor: Hauswacht creates a threshold helper in Home Assistant (afterwards changeable and deletable under Settings → Devices & services → Helpers) and puts it to use right away. Nothing existing is changed.",
    source: "Measurement",
    helperName: "Name of the new sensor",
    upper: "Upper limit (triggers when above)",
    lower: "Lower limit (triggers when below)",
    hysteresis: "Hysteresis (distance before “normal” applies again)",
    type: "Type",
    target: "Use in",
    targetAlways: "Always active",
    minutes: "Minutes (0 = learning off)",
    learnHint: "This long Hauswacht remembers an unknown card read at a keypad or reader for learning. 0 = learning off.",
    errors: {
      restart_needs_profile: "“Always armed” needs at least one alarm profile.",
      area_has_profiles: "This area still has alarm profiles – delete them or move them to another area first.",
      area_name_taken: "Another area already has this name.",
      area_name_required: "Please enter a name.",
      invalid_pin: "PIN: 4 to 8 digits.",
      pin_is_action_code: "These digits are already an action code.",
      pin_is_duress: "This PIN is already the duress PIN of: {c}",
      user_name_required: "Please enter a name.",
      action_code_name_taken: "Another action code already has this name.",
      action_code_invalid: "Please enter 2 to 8 digits.",
      action_code_taken: "This code with this key already exists (“{c}”).",
      action_code_profile_missing: "Please choose an alarm profile.",
      action_code_is_pin: "This code is already a PIN or duress PIN – please choose another one.",
      helper_no_limit: "Please enter an upper and/or lower limit.",
      helper_range: "The lower limit must be below the upper one.",
      helper_name: "Please enter a name.",
      helper_failed: "The helper could not be created (see log).",
      control_entity: "Please choose a measurement (sensor.…).",
      invalid: "Invalid value.",
      disarm_first: "Disarm all areas first – then saving works.",
      changed_elsewhere: "Something was changed elsewhere in the meantime. The page reloads – please try again.",
      failed: "Saving failed.",
    },
  },
};

const HELP = {
  restart: "restart",
  silence: "silence",
  network: "network",
  homecoming: "homecoming",
  area: "areas",
  page: "settingsPage",
  pinrules: "pinRules",
  actioncode: "actionCodes",
  learn: "cards",
  helper: "helper",
};

const se = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

class HauswachtSystemEditor extends HTMLElement {
  // open({hass, settings, kind, item}) – item: ID (Bereich, Aktions-Code, Bedienteil) oder null
  open(options) {
    Object.assign(this, options);
    const sys = this.settings.system;
    this._errors = {};
    this._details = {};
    this._busy = false;
    this._sure = false;
    const copy = (v) => JSON.parse(JSON.stringify(v));
    const kind = this.kind;
    if (kind === "restart") this._draft = copy(sys.restart);
    else if (kind === "silence") this._draft = copy(sys.silence);
    else if (kind === "network") this._draft = copy(sys.network);
    else if (kind === "homecoming") this._draft = copy(sys.homecoming);
    else if (kind === "page") this._draft = { enabled: sys.settings_page };
    else if (kind === "pinrules") this._draft = { ...copy(sys.pin_rules), master_pin: "", remove_master_pin: false };
    else if (kind === "learn") this._draft = { minutes: sys.controls.learn_minutes };
    else if (kind === "helper") this._draft = { source: "", name: "", upper: "", lower: "", hysteresis: 0, type: "technical", target: "__always__" };
    else if (kind === "area") this._draft = copy(sys.areas.find((a) => a.id === this.item) || { name: "", icon: "mdi:home-outline", profiles: [] });
    else if (kind === "actioncode") {
      this._draft = copy(
        sys.action_codes.codes.find((c) => c.id === this.item) || {
          name: "", code: "", key: "arm_day_zones", keypad: sys.action_codes.all_keypads, action: "event", profile: null,
        }
      );
    }
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this._render();
  }

  get _lang() {
    return (this.hass?.language || "en").startsWith("de") ? "de" : "en";
  }

  _t(key) {
    return ST[this._lang][key] ?? ST.en[key] ?? key;
  }

  _err(key) {
    const code = this._errors[key];
    if (!code) return "";
    const text = (this._t("errors")[code] || code).replace("{c}", this._details.conflict || "");
    return `<div class="err">${se(text)}</div>`;
  }

  _chk(field, checked, label) {
    return `<div class="chk"><input type="checkbox" data-b="${se(field)}" ${checked ? "checked" : ""}><span>${se(label)}</span></div>`;
  }

  _select(field, value, entries) {
    return `<select data-f="${se(field)}">${entries.map(([v, l]) => `<option value="${se(v)}" ${v === value ? "selected" : ""}>${se(l)}</option>`).join("")}</select>`;
  }

  // Liste von Entitäten mit ✕ und Eingabe mit Vorschlägen
  _entityList(where, list, choices) {
    const name = (id) => (choices.find((c) => c.id === id) || { name: id }).name;
    const chips = list.map((id, i) => `<span class="chip" title="${se(id)}">${se(name(id))}<button class="x" data-rm="${where}:${i}">✕</button></span>`).join("");
    return `<div class="chips">${chips}</div><input list="hw-sys-${where.split(":")[0]}" data-add="${se(where)}" placeholder="${se(this._t("addEntity"))}">`;
  }

  // Eine Entität wählen: Eingabe mit Vorschlägen (Name oder ID)
  _entityPick(field, value, choices) {
    this._picks = { ...(this._picks || {}), [field]: choices };
    const shown = (choices.find((c) => c.id === value) || { name: value || "" }).name;
    return `<input data-pick="${se(field)}" list="hw-sys-pick-${field}" value="${se(shown)}" placeholder="${se(this._t("addEntity"))}">${this._datalist(`pick-${field}`, choices)}`;
  }

  _datalist(id, choices) {
    return `<datalist id="hw-sys-${id}">${choices.map((c) => `<option value="${se(c.id)}">${se(c.name)}</option>`).join("")}</datalist>`;
  }

  _form() {
    const d = this._draft;
    const sys = this.settings.system;
    const k = this.kind;
    if (k === "restart") {
      const areas = sys.areas.filter((a) => sys.profiles.some((p) => p.area === a.id));
      const perArea = d.behavior === "armed"
        ? areas.map((a) => {
            const entries = [["", this._t("none")], ...sys.profiles.filter((p) => p.area === a.id).map((p) => [p.id, p.name])];
            return `<label>${se(this._t("restartProfile"))}${areas.length > 1 ? ` – ${se(a.name)}` : ""}</label><select data-rp="${se(a.id)}">${entries.map(([v, l]) => `<option value="${se(v)}" ${v === (d.profiles[a.id] || "") ? "selected" : ""}>${se(l)}</option>`).join("")}</select>`;
          }).join("")
        : "";
      return `<h2>${se(this._t("restart"))}</h2>
        <label>${se(this._t("behavior"))}</label>${this._select("behavior", d.behavior, d.behaviors.map((b) => [b, this._t("behaviors")[b]]))}
        <div class="muted">${se(this._t("behaviorHint")[d.behavior] || "")}</div>${perArea}${this._err("base")}
        ${d.behavior === "restore" ? `${this._chk("continue_alarm", d.continue_alarm, this._t("continueAlarm"))}<div class="muted">${se(this._t("continueHint"))}</div>` : ""}`;
    }
    if (k === "silence") {
      return `<h2>${se(this._t("silence"))}</h2>
        <label>${se(this._t("hours"))}</label><input class="small" type="number" min="0" max="${d.max}" data-f="hours" value="${se(d.hours)}">
        <div class="muted">${se(this._t("silenceHint"))}</div>
        ${d.observation ? `<label>${se(this._t("observation"))}</label><div class="muted">${se(d.observation)}</div>` : ""}`;
    }
    if (k === "network") {
      return `<h2>${se(this._t("network"))}</h2><div class="muted">${se(this._t("networkHint"))}</div>
        ${this._entityList("net", d.entities, d.choices)}${this._datalist("net", d.choices)}`;
    }
    if (k === "homecoming") {
      const persons = [...new Set([...d.persons, ...d.signal_persons])];
      const signals = persons
        .map((p, i) => `<div class="box"><b>${se((d.person_choices.find((c) => c.id === p) || { name: p }).name)}</b>${this._entityList(`sig:${i}`, d.signals[p] || [], d.signal_choices)}</div>`)
        .join("");
      return `<h2>${se(this._t("homecoming"))}</h2>
        ${this._chk("observe", d.observe, this._t("observe"))}
        <label>${se(this._t("persons"))}</label>${this._entityList("per", d.persons, d.person_choices)}${this._datalist("per", d.person_choices)}
        <label>${se(this._t("ssids"))}</label><input data-f="ssids" value="${se(d.ssids.join(", "))}">
        <label>${se(this._t("signals"))}</label><div class="muted">${se(this._t("signalsHint"))}</div>${signals}${this._datalist("sig", d.signal_choices)}`;
    }
    if (k === "area") {
      return `<h2>${se(this.item ? this._t("area") : this._t("areaNew"))}</h2>
        <label>${se(this._t("name"))}</label><input data-f="name" value="${se(d.name)}">${this._err("name")}
        <label>${se(this._t("icon"))}</label><input data-f="icon" value="${se(d.icon)}">
        ${this.item ? `<label>${se(this._t("areaProfiles"))}</label><div class="muted">${se(d.profiles.join(", ") || this._t("none"))}</div>` : ""}${this._err("base")}`;
    }
    if (k === "page") {
      return `<h2>${se(this._t("page"))}</h2>${this._chk("enabled", d.enabled, this._t("pageShow"))}
        ${d.enabled ? "" : `<div class="warn">${se(this._t("pageWarn"))}</div>`}`;
    }
    if (k === "pinrules") {
      return `<h2>${se(this._t("pinrules"))}</h2>
        <div class="muted">${se(this._t("pinUsers"))}: ${se(d.pin_users.join(", ") || this._t("none"))}</div>
        <div class="warn">${se(this._t("pinWarn"))}</div>
        ${this._chk("code_arm_required", d.code_arm_required, this._t("codeArm"))}
        ${this._chk("end_alarm_without_pin", d.end_alarm_without_pin, this._t("endNoPin"))}
        ${this._chk("buttons_without_pin", d.buttons_without_pin, this._t("buttonsNoPin"))}
        ${this._chk("card_pin_unlinked", d.card_pin_unlinked, this._t("cardPinUnlinked"))}
        <div class="box"><b>${se(this._t("master"))}</b> <span class="muted">${se(d.master ? this._t("masterSet") : this._t("masterNone"))}</span>
          <div class="muted">${se(this._t("masterHint"))}</div>
          <label>${se(this._t("masterNew"))}</label><input type="password" inputmode="numeric" autocomplete="new-password" data-f="master_pin" value="${se(d.master_pin)}">${this._err("master_pin")}
          ${d.master ? this._chk("remove_master_pin", d.remove_master_pin, this._t("masterRemove")) : ""}</div>`;
    }
    if (k === "actioncode") {
      const ac = sys.action_codes;
      const keypads = [[ac.all_keypads, this._t("allKeypads")], ...ac.keypads.map((x) => [x.id, x.name])];
      return `<h2>${se(this.item ? this._t("actioncode") : this._t("actioncodeNew"))}</h2>
        <div class="muted">${se(this._t("codeHint"))}</div>
        <label>${se(this._t("name"))}</label><input data-f="name" value="${se(d.name)}">${this._err("name")}
        <label>${se(this._t("code"))}</label><input class="small" inputmode="numeric" data-f="code" value="${se(d.code)}">${this._err("code")}
        <label>${se(this._t("key"))}</label>${this._select("key", d.key, ac.keys.map((x) => [x, this._t("keys")[x] || x]))}
        <label>${se(this._t("keypad"))}</label>${this._select("keypad", d.keypad, keypads)}
        <label>${se(this._t("action"))}</label>${this._select("action", d.action, ac.actions.map((x) => [x, this._t("actions")[x] || x]))}
        ${d.action === "arm" ? `<label>${se(this._t("profile"))}</label>${this._select("profile", d.profile || "", [["", this._t("none")], ...sys.profiles.map((p) => [p.id, p.name])])}${this._err("profile")}` : ""}`;
    }
    if (k === "helper") {
      const sensors = this.settings.entities.filter((e) => e.domain === "sensor").map((e) => ({ id: e.id, name: `${e.name} (${e.state})` }));
      const types = this.settings.types.map((t) => [t, this.typeLabel ? this.typeLabel(t) : t]);
      const targets = [["__always__", this._t("targetAlways")], ...this.settings.groups.map((g) => [g.id, g.name])];
      return `<h2>${se(this._t("helper"))}</h2><div class="muted">${se(this._t("helperInfo"))}</div>
        <label>${se(this._t("source"))}</label>${this._entityPick("source", d.source, sensors)}${this._err("source")}
        <label>${se(this._t("helperName"))}</label><input data-f="name" value="${se(d.name)}">${this._err("name")}
        <div class="inline"><div><label>${se(this._t("upper"))}</label><input class="small" type="number" step="any" data-f="upper" value="${se(d.upper)}"></div>
        <div><label>${se(this._t("lower"))}</label><input class="small" type="number" step="any" data-f="lower" value="${se(d.lower)}"></div></div>
        <label>${se(this._t("hysteresis"))}</label><input class="small" type="number" step="any" min="0" data-f="hysteresis" value="${se(d.hysteresis)}">
        <label>${se(this._t("type"))}</label>${this._select("type", d.type, types)}
        <label>${se(this._t("target"))}</label>${this._select("target", d.target, targets)}`;
    }
    return `<h2>${se(this._t("learn"))}</h2>
      <label>${se(this._t("minutes"))}</label><input class="small" type="number" min="0" max="${this.settings.system.controls.learn_max}" data-f="minutes" value="${se(d.minutes)}">
      <div class="muted">${se(this._t("learnHint"))}</div>`;
  }

  _collect() {
    const root = this.shadowRoot;
    const d = this._draft;
    root.querySelectorAll("[data-f]").forEach((el) => (d[el.dataset.f] = el.value));
    root.querySelectorAll("[data-b]").forEach((el) => (d[el.dataset.b] = el.checked));
    root.querySelectorAll("[data-pick]").forEach((el) => {
      const value = el.value.trim();
      const match = (this._picks?.[el.dataset.pick] || []).find((c) => c.name === value || c.id === value);
      d[el.dataset.pick] = match ? match.id : value;
    });
    root.querySelectorAll("[data-rp]").forEach((el) => {
      if (el.value) d.profiles[el.dataset.rp] = el.value;
      else delete d.profiles[el.dataset.rp];
    });
    if (this.kind === "homecoming" && typeof d.ssids === "string") {
      d.ssids = d.ssids.split(",").map((s) => s.trim()).filter(Boolean);
    }
  }

  _list(where) {
    const d = this._draft;
    const [kind, index] = where.split(":");
    if (kind === "net") return d.entities;
    if (kind === "per") return d.persons;
    const persons = [...new Set([...d.persons, ...d.signal_persons])];
    const person = persons[Number(index)];
    d.signals[person] = d.signals[person] || [];
    return d.signals[person];
  }

  _choices(where) {
    const d = this._draft;
    const kind = where.split(":")[0];
    return kind === "net" ? d.choices : kind === "per" ? d.person_choices : d.signal_choices;
  }

  _payload() {
    const d = this._draft;
    switch (this.kind) {
      case "restart":
        return ["restart_save", { behavior: d.behavior, continue_alarm: d.continue_alarm, profiles: d.profiles }];
      case "silence":
        return ["silence_save", { hours: Number(d.hours) }];
      case "network":
        return ["network_save", { entities: d.entities }];
      case "homecoming":
        return ["homecoming_save", { observe: d.observe, persons: d.persons, ssids: d.ssids, signals: d.signals }];
      case "area":
        return ["area_save", { id: this.item, name: d.name, icon: d.icon }];
      case "page":
        return ["settings_page_save", { enabled: d.enabled }];
      case "pinrules":
        return ["pin_rules_save", d];
      case "actioncode":
        return ["action_code_save", { ...d, id: this.item }];
      case "learn":
        return ["learn_save", { minutes: Number(d.minutes) }];
      case "helper":
        return ["helper_create", { ...d, upper: d.upper === "" ? null : Number(d.upper), lower: d.lower === "" ? null : Number(d.lower), hysteresis: Number(d.hysteresis || 0) }];
      default:
        return null;
    }
  }

  get _canDelete() {
    return (this.kind === "area" && this.item && this.item !== "main") || (this.kind === "actioncode" && this.item);
  }

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
    this._details = result.details || {};
    if (this._errors.base === "changed_elsewhere") this.dispatchEvent(new CustomEvent("hw-stale", { bubbles: true, composed: true }));
    this._render();
    window.HauswachtRevealError?.(this.shadowRoot); // Fehlermeldung ins Bild holen
  }

  _render() {
    const top = this.shadowRoot.querySelector(".sheet")?.scrollTop || 0;
    const canSave = this._payload() !== null;
    const style = `.chips { display: flex; flex-wrap: wrap; gap: 6px; margin: 4px 0; }
      .chip { display: inline-flex; align-items: center; gap: 2px; border: 1px solid var(--divider-color); border-radius: 14px; padding: 2px 4px 2px 10px; font-size: .9rem; }
      .chip .x { font-size: 1rem; padding: 0 4px; }
      .warn { border: 1px solid var(--warning-color, #ffa600); border-radius: 8px; padding: 8px 10px; margin: 8px 0; font-size: .9rem; }`;
    this.shadowRoot.innerHTML = `<style>${(window.HauswachtEditStyle || "") + style}</style><div class="sheet">${this._form()}
      ${["restart", "area"].includes(this.kind) ? "" : this._err("base")}
      ${this.kind === "helper" ? ["upper", "lower", "hysteresis", "type", "target"].map((k) => this._err(k)).join("") : ""}
      <div class="bar">${canSave ? `<button class="b p" data-act="save" ${this._busy ? "disabled" : ""}>${se(this._busy ? this._t("saving") : this._t("save"))}</button>` : ""}
      <button class="b" data-act="cancel">${se(this._t("cancel"))}</button>
      ${this._canDelete ? `<button class="b d" data-act="delete">${se(this._sure ? this._t("delSure") : this._t("del"))}</button>` : ""}</div></div>`;
    this.shadowRoot.querySelector(".sheet").scrollTop = top;
    window.HauswachtDocs?.decorate(this.shadowRoot, HELP[this.kind], this._lang);
    this._wire();
  }

  _wire() {
    const root = this.shadowRoot;
    const redraw = () => {
      this._collect();
      this._render();
    };
    this.onclick = (ev) => {
      if (ev.composedPath()[0] === this) this._close();
    };
    root.querySelector('[data-act="cancel"]').addEventListener("click", () => this._close());
    const save = root.querySelector('[data-act="save"]');
    if (save) {
      save.addEventListener("click", () => {
        this._collect();
        const [action, data] = this._payload();
        this._apply(action, data);
      });
    }
    const del = root.querySelector('[data-act="delete"]');
    if (del) {
      del.addEventListener("click", () => {
        this._collect();
        if (!this._sure) {
          this._sure = true;
          this._render();
          return;
        }
        const action = { area: "area_delete", actioncode: "action_code_delete" }[this.kind];
        this._apply(action, { id: this.item });
      });
    }
    root.querySelectorAll("[data-rm]").forEach((el) =>
      el.addEventListener("click", () => {
        this._collect();
        const [kind, a, b] = el.dataset.rm.split(":");
        const where = b === undefined ? kind : `${kind}:${a}`;
        const index = Number(b === undefined ? a : b);
        this._list(where).splice(index, 1);
        this._render();
      })
    );
    root.querySelectorAll("[data-add]").forEach((el) =>
      el.addEventListener("change", () => {
        this._collect();
        const where = el.dataset.add;
        const value = el.value.trim();
        const match = this._choices(where).find((c) => c.id === value || c.name.toLowerCase() === value.toLowerCase());
        if (!match) return;
        const list = this._list(where);
        if (!list.includes(match.id)) list.push(match.id);
        this._render();
      })
    );
    // Auswahl, die andere Felder ein- oder ausblendet
    root.querySelectorAll('[data-f="behavior"], [data-f="action"], [data-b="enabled"]').forEach((el) => el.addEventListener("change", redraw));
  }

  _close() {
    this.dispatchEvent(new CustomEvent("hw-close", { bubbles: true, composed: true }));
  }
}

if (!customElements.get("hauswacht-system-editor")) {
  customElements.define("hauswacht-system-editor", HauswachtSystemEditor);
}
