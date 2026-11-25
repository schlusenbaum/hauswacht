// Hauswacht – Einstellungsseite, Stufe 2: Melder bearbeiten (ADR 0011).
//
// Ein eigenes Element <hauswacht-sensor-editor> als Seitenblatt: Meldergruppen (mit Typen und
// Fehlalarmschutz), Melder mit Kippstellung, Erschütterungsstärken, Immer aktiv.
// Gespeichert wird über hauswacht/settings/apply – dieselben Regeln wie im Dialog.
// Nur stabile Bausteine: eigene Elemente, ha-icon, Farben des Themas. Keine internen
// Formular-Bausteine von Home Assistant.

const ET = {
  de: {
    info: {
      name: "Name der Meldergruppe, z. B. „Außenhaut“ oder „Innenraum“. Profile wählen Gruppen – nicht einzelne Melder.",
      members: "Die Melder dieser Gruppe mit ihrem Typ. Der Typ entscheidet, wie ein Melder reagiert: Tür mit Eingangsverzögerung, Fenster und Bewegung sofort, Technik (Wasser, Rauch) nie als Einbruch.",
      add: "Melder suchen und hinzufügen. Ein Melder gehört höchstens einer Gruppe.",
      label: "Alle Entitäten mit diesem Label gehören automatisch dazu – praktisch, wenn neue Melder per Label einsortiert werden.",
      type: "Wie der Melder reagiert: Tür = Eingangsverzögerung, Fenster/Bewegung/Glasbruch = sofort, Erschütterung mit Fehlalarmschutz, Technik (Wasser, Rauch, Frost) meldet nur.",
      vibCount: "So viele Meldungen desselben Melders braucht es für einen Alarm. Ein einzelner Stoß (Tür knallt, Lkw) löst dann nicht aus.",
      vibWindow: "In dieser Zeit müssen die Meldungen kommen. Die Haltezeit des Sensors muss kürzer sein.",
      tiltEntity: "Der Sensor, der „offen“, „gekippt“ oder „zu“ meldet – z. B. ein Fenstergriff. Auch ein Auswahl-Helfer oder ein Attribut einer Entität geht.",
      attribute: "Steht der Wert nicht im Zustand, sondern in einem Attribut (z. B. „position“), hier den Namen eintragen.",
      values: "Welcher Wert was bedeutet. Unbekannte Werte zählen als offen – das ist die sichere Seite.",
      group: "In welche Meldergruppe der neue Melder kommt.",
      strengthEntity: "Ein Sensor, der die Stärke einer Erschütterung als Zahl meldet.",
      threshold: "Ab diesem Wert zählt es als Erschütterung. Mit „gerade“ siehst du den aktuellen Wert zum Vergleich.",
      sensorGroup: "Zu welcher Gruppe der Melder gehört – damit gilt er in allen Profilen, die diese Gruppe überwachen.",
      always: "Meldet auch unscharf – z. B. Wasser, Tresor, Waffenschrank. Unscharf gibt es eine Nachricht, scharf den normalen Alarm.",
      profilesTitle: "In welchen Profilen dieser Melder allein auslöst. Haken weg = in diesem Profil ausgenommen; in Auslöseregeln zählt er weiter.",
      alwaysGroups: "Ganze Gruppen, die auch unscharf melden.",
      alwaysSensors: "Einzelne Melder, die auch unscharf melden.",
      alwaysSirensOn: "An: Löst ein immer aktiver Melder unscharf aus, gehen die Sirenen an. Aus: nur eine Nachricht.",
      alwaysTone: "Ton für einen Alarm im unscharfen Zustand.",
      alwaysVolume: "Lautstärke für einen Alarm im unscharfen Zustand.",
      alwaysReaction: "So lange laufen die Sirenen bei einem Alarm im unscharfen Zustand.",
    },
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
    alwaysText: "Diese Melder melden auch im unscharfen Zustand (z. B. Wasser, Tresor). Unscharf gibt es eine Nachricht – oder, wenn unten eingeschaltet, einen Alarm mit Sirene.",
    alwaysSirens: "Sirenen, wenn unscharf ausgelöst",
    alwaysSirensOn: "Unscharf: Alarm mit Sirene (sonst nur Nachricht)",
    alwaysSirensHint: "Scharf lösen immer aktive Melder den normalen Alarm des Profils aus. Technik-Melder (z. B. Wasser) nie Einbruchalarm.",
    alwaysTone: "Ton",
    alwaysVolume: "Lautstärke",
    alwaysReaction: "Dauer (Sekunden)",
    alwaysNoSirens: "Noch keine Sirene eingetragen (Reiter Alarmgeber).",
    tones: { burglar: "Einbruch", emergency: "Notfall", police_panic: "Polizei-Panik", emergency_panic: "Notfall-Panik" },
    volumes: { low: "leise", medium: "mittel", high: "laut", very_high: "sehr laut" },
    alwaysGroups: "Ganze Meldergruppen",
    alwaysSensors: "Einzelne Melder",
    chosen: "gewählt",
    showAll: "Auch andere Entitäten zeigen (nicht nur passende)",
    showAssigned: "Auch Melder zeigen, die schon in einer Gruppe sind",
    inGroup: "in",
    more: "… weitere – Suchfeld eingrenzen",
    nothing: "Nichts gefunden.",
    sensorTitle: "Melder bearbeiten",
    sensorGroup: "Meldergruppe",
    viaLabel: "Kommt über das Label der Gruppe – die Gruppe änderst du über das Label an der Entität.",
    always: "Immer aktiv (meldet auch unscharf)",
    staleTitle: "Funkstille",
    staleHint: "Wie lange dieser Melder schweigen darf, bevor er beim Scharfschalten als ausgefallen gilt.",
    staleGeneral: "Wie allgemein ({h} h)",
    staleGeneralOff: "Wie allgemein (aus)",
    staleOwn: "Eigener Wert",
    staleOff: "Nie prüfen (meldet sich nur bei Änderungen)",
    staleObserved: "Beobachtet: längste Pause {p} bei {n} Meldungen in {d} Tagen.",
    staleAdvice: "Empfehlung für diesen Melder: {h} h.",
    staleAdviceLater: "Eine Empfehlung gibt es nach 3 Tagen Beobachtung.",
    staleNoData: "Für diesen Melder gibt es noch keine Beobachtung.",
    staleTake: "Empfehlung übernehmen ({h} h)",
    profilesTitle: "Löst allein aus in den Profilen",
    profilesHint: "Haken weg = in diesem Profil ausgenommen (zählt nur noch in Auslöseregeln).",
    noProfiles: "Kein Profil nutzt diese Gruppe.",
    errors: {
      stale_hours_invalid: "Bitte 1 bis 168 Stunden angeben.",
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
      group_by_label: "Dieser Melder kommt über ein Label in seine Gruppe.",
      failed: "Speichern fehlgeschlagen.",
    },
  },
  en: {
    info: {
      name: "Name of the sensor group, e.g. “Perimeter” or “Interior”. Profiles choose groups – not single sensors.",
      members: "The sensors of this group with their type. The type decides how a sensor reacts: door with entry delay, window and motion at once, technical (water, smoke) never as burglary.",
      add: "Search and add sensors. A sensor belongs to at most one group.",
      label: "All entities with this label belong to it automatically – handy when new sensors are sorted by label.",
      type: "How the sensor reacts: door = entry delay, window/motion/glass break = at once, vibration with false-alarm protection, technical (water, smoke, frost) only reports.",
      vibCount: "This many reports of the same sensor are needed for an alarm. A single knock (door slams, lorry) then does not trigger.",
      vibWindow: "The reports have to come within this time. The sensor's hold time must be shorter.",
      tiltEntity: "The sensor that reports “open”, “tilted” or “closed” – e.g. a window handle. A select helper or an attribute of an entity works too.",
      attribute: "If the value is not in the state but in an attribute (e.g. “position”), enter its name here.",
      values: "Which value means what. Unknown values count as open – that is the safe side.",
      group: "Which sensor group the new sensor goes into.",
      strengthEntity: "A sensor that reports the strength of a vibration as a number.",
      threshold: "From this value it counts as a vibration. “current” shows the present value for comparison.",
      sensorGroup: "Which group the sensor belongs to – so it applies in all profiles that watch this group.",
      always: "Also reports when disarmed – e.g. water, safe, gun cabinet. Disarmed there is a message, armed the normal alarm.",
      profilesTitle: "In which profiles this sensor triggers on its own. Untick = excluded in this profile; it still counts in trigger rules.",
      alwaysGroups: "Whole groups that also report when disarmed.",
      alwaysSensors: "Single sensors that also report when disarmed.",
      alwaysSirensOn: "On: if an always-active sensor triggers while disarmed, the sirens go on. Off: only a message.",
      alwaysTone: "Tone for an alarm while disarmed.",
      alwaysVolume: "Volume for an alarm while disarmed.",
      alwaysReaction: "This long the sirens run for an alarm while disarmed.",
    },
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
    alwaysText: "These sensors also report while disarmed (e.g. water, safe). Disarmed you get a message – or, if switched on below, an alarm with siren.",
    alwaysSirens: "Sirens when triggered while disarmed",
    alwaysSirensOn: "Disarmed: alarm with siren (otherwise only a message)",
    alwaysSirensHint: "Armed, always-active sensors trigger the profile's normal alarm. Technical sensors (e.g. water) never trigger an intrusion alarm.",
    alwaysTone: "Tone",
    alwaysVolume: "Volume",
    alwaysReaction: "Duration (seconds)",
    alwaysNoSirens: "No siren registered yet (tab alarm devices).",
    tones: { burglar: "Burglar", emergency: "Emergency", police_panic: "Police panic", emergency_panic: "Emergency panic" },
    volumes: { low: "low", medium: "medium", high: "high", very_high: "very high" },
    alwaysGroups: "Whole sensor groups",
    alwaysSensors: "Single sensors",
    chosen: "chosen",
    showAll: "Also show other entities (not only suitable ones)",
    showAssigned: "Also show sensors that are already in a group",
    inGroup: "in",
    more: "… more – narrow down the search",
    nothing: "Nothing found.",
    sensorTitle: "Edit sensor",
    sensorGroup: "Sensor group",
    viaLabel: "Comes in via the group's label – change the group via the label on the entity.",
    always: "Always active (also reports when disarmed)",
    staleTitle: "Radio silence",
    staleHint: "How long this sensor may stay silent before it counts as failed when arming.",
    staleGeneral: "As general ({h} h)",
    staleGeneralOff: "As general (off)",
    staleOwn: "Own value",
    staleOff: "Never check (only reports on changes)",
    staleObserved: "Observed: longest pause {p} with {n} reports in {d} days.",
    staleAdvice: "Recommendation for this sensor: {h} h.",
    staleAdviceLater: "A recommendation is available after 3 days of observation.",
    staleNoData: "No observation for this sensor yet.",
    staleTake: "Use recommendation ({h} h)",
    profilesTitle: "Triggers on its own in the profiles",
    profilesHint: "Untick = excluded in this profile (then only counts in trigger rules).",
    noProfiles: "No profile uses this group.",
    errors: {
      stale_hours_invalid: "Please enter 1 to 168 hours.",
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
      group_by_label: "This sensor comes into its group via a label.",
      failed: "Saving failed.",
    },
  },
};

const SENSOR_DOMAINS = ["binary_sensor", "lock", "cover"];
const TILT_DOMAINS = ["sensor", "input_select", "select", "binary_sensor", "lock", "cover"];
const STRENGTH_DOMAINS = ["sensor", "input_number", "number"];
const KNOWN_CLOSED = ["closed", "close", "geschlossen", "zu"];
// Was ein Melder sein kann – der Rest (Verbindung, Update, Batterie …) nur auf Wunsch
const SENSOR_CLASSES = [
  "door", "window", "opening", "garage_door", "motion", "occupancy", "presence", "moving", "tamper",
  "vibration", "moisture", "gas", "heat", "cold", "carbon_monoxide", "safety", "sound",
];
const TILT_WORDS = ["tilt", "kipp", "opening", "window", "fenster", "griff", "handle"];
const STRENGTH_WORDS = ["vibration", "erschuetter", "erschütter", "strength", "shock"];
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
    this._showAll = false;
    this._showAssigned = false;
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
    if (this.kind === "sensor") {
      const id = this.item.entity;
      const group = this._groupOf(id);
      return {
        entity: id,
        group: group ? group.id : "",
        type: s.sensor_types[id] || this._entity(id).suggested || "other",
        always: (s.always.sensors || []).includes(id),
        excluded: s.profiles.filter((p) => (p.excluded || []).includes(id)).map((p) => p.id),
        ...this._staleInitial(id),
      };
    }
    if (this.kind === "strength") {
      const v = this.item;
      return { entity: v?.entity || "", threshold: v?.threshold ?? "", group: "", existing: !!v };
    }
    const a = s.always;
    return {
      zones: [...(a.zones || [])],
      sensors: [...(a.sensors || [])],
      sirens_enabled: !!a.sirens_enabled,
      sirens: [...(a.sirens || [])],
      siren_tone: a.siren_tone || "burglar",
      siren_volume: a.siren_volume || "high",
      reaction_time: a.reaction_time || 180,
    };
  }

  // --- Auswahl --------------------------------------------------------------------

  // Gruppe, in der ein Melder steckt (direkt oder über das Label)
  _groupOf(id) {
    for (const g of this.settings.groups) {
      if ((g.entities || []).includes(id) || (this.settings.label_members?.[g.id] || []).includes(id)) return g;
    }
    return null;
  }

  _suitable(x, mode) {
    const words = (x.id + " " + x.name).toLowerCase();
    if (mode === "tilt") {
      if (["input_select", "select"].includes(x.domain)) return true;
      const st = this.hass.states[x.id];
      const values = [x.state, ...((st && st.attributes.options) || [])].map((v) => String(v).toLowerCase());
      return values.some((v) => KNOWN_TILTED.includes(v)) || TILT_WORDS.some((w) => words.includes(w));
    }
    if (mode === "strength") {
      if (["input_number", "number"].includes(x.domain)) return true;
      return STRENGTH_WORDS.some((w) => words.includes(w)) && !isNaN(Number(x.state));
    }
    return ["lock", "cover"].includes(x.domain) || SENSOR_CLASSES.includes(x.device_class);
  }

  // Liste zum Anklicken – ohne Eingabe alle passenden, mit Eingabe gefiltert
  _pickerHtml(domains, exclude, extraIds = [], mode = "sensor") {
    const q = this._query.trim().toLowerCase();
    const ownGroup = this.kind === "group" ? this._draft.id : null;
    const candidates = (this.settings.entities || [])
      .filter((x) => (domains.includes(x.domain) || extraIds.includes(x.id)) && !exclude.includes(x.id))
      .filter((x) => this._showAll || extraIds.includes(x.id) || this._suitable(x, mode))
      .filter((x) => {
        if (mode !== "sensor" || this._showAssigned) return true;
        const g = this._groupOf(x.id);
        return !g || g.id === ownGroup;
      })
      .filter((x) => !q || x.name.toLowerCase().includes(q) || x.id.toLowerCase().includes(q));
    const shown = candidates.slice(0, 150);
    const rows = shown
      .map((x) => {
        const g = mode === "sensor" ? this._groupOf(x.id) : null;
        const where = g && g.id !== ownGroup ? ` · ${e(this._t("inGroup"))} ${e(g.name)}` : "";
        return `<div data-pick="${e(x.id)}">${e(x.name)}<br><small>${e(x.id)} · ${e(x.state)}${where}</small></div>`;
      })
      .join("");
    const more = candidates.length > shown.length ? `<div class="muted">${e(this._t("more"))}</div>` : "";
    const toggles = `<div class="chk"><input type="checkbox" data-toggle="all" ${this._showAll ? "checked" : ""}><span>${e(this._t("showAll"))}</span></div>${
      mode === "sensor" ? `<div class="chk"><input type="checkbox" data-toggle="assigned" ${this._showAssigned ? "checked" : ""}><span>${e(this._t("showAssigned"))}</span></div>` : ""
    }`;
    return `<input class="q" type="search" placeholder="${e(this._t("search"))}" value="${e(this._query)}">
      <div class="results">${rows || `<div class="muted">${e(this._t("nothing"))}</div>`}${more}</div>${toggles}`;
  }

  _groupSelect(name, current) {
    return `<select data-f="${e(name)}"><option value="">${e(this._t("noGroupChoice"))}</option>${this.settings.groups.map((g) => `<option value="${e(g.id)}" ${g.id === current ? "selected" : ""}>${e(g.name)}</option>`).join("")}</select>`;
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
      : this._pickerHtml(TILT_DOMAINS, [], [], "tilt");
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
      : this._pickerHtml(STRENGTH_DOMAINS, [], [], "strength");
    return `
      <h2>${e(this._t("strengthNew"))}</h2>
      <label>${e(this._t("strengthEntity"))}</label>${source}${this._err("entity")}
      <label>${e(this._t("threshold"))}</label><input class="small" type="number" step="any" data-f="threshold" value="${e(d.threshold)}">${this._err("threshold")}
      ${d.existing ? "" : `<label>${e(this._t("group"))}</label>${this._groupSelect("group", d.group)}`}`;
  }

  // Funkstille je Melder: allgemeiner Wert, eigene Stunden oder nie prüfen
  _staleInitial(id) {
    const own = this.settings.system?.silence?.overrides?.[id];
    if (own === undefined) return { stale_mode: "default", stale_hours: "" };
    return own === 0 ? { stale_mode: "off", stale_hours: "" } : { stale_mode: "hours", stale_hours: own };
  }

  _staleHtml() {
    const d = this._draft;
    const sil = this.settings.system?.silence;
    if (!sil) return "";
    const obs = sil.sensors?.[d.entity];
    const general = sil.hours ? this._t("staleGeneral").replace("{h}", sil.hours) : this._t("staleGeneralOff");
    const modes = [["default", general], ["hours", this._t("staleOwn")], ["off", this._t("staleOff")]]
      .map(([v, l]) => `<option value="${v}" ${d.stale_mode === v ? "selected" : ""}>${e(l)}</option>`)
      .join("");
    let observed;
    if (!obs) observed = this._t("staleNoData");
    else {
      observed = this._t("staleObserved").replace("{p}", obs.longest).replace("{n}", obs.contacts).replace("{d}", sil.days);
      observed += obs.advice ? ` ${this._t("staleAdvice").replace("{h}", obs.advice)}` : ` ${this._t("staleAdviceLater")}`;
    }
    const take = obs?.advice
      ? `<button class="b" data-a="stale-take">${e(this._t("staleTake").replace("{h}", obs.advice))}</button>`
      : "";
    return `<div class="box"><b>${e(this._t("staleTitle"))}</b>
      <div class="muted">${e(this._t("staleHint"))}</div>
      <div class="inline"><div style="flex:1"><select data-f="stale_mode">${modes}</select></div>
      ${d.stale_mode === "hours" ? `<div><input class="small" type="number" min="1" max="${sil.max}" data-f="stale_hours" value="${e(d.stale_hours)}"> h</div>` : ""}</div>
      ${this._err("stale_hours")}
      <div class="muted" style="margin-top:6px">${e(observed)}</div>${take}</div>`;
  }

  _sensorForm() {
    const d = this._draft;
    const x = this._entity(d.entity);
    const label = this.settings.groups.find((g) => (this.settings.label_members?.[g.id] || []).includes(d.entity));
    const groupSel = label
      ? `<div class="row"><div class="n">${e(label.name)}<small>${e(this._t("viaLabel"))}</small></div></div>`
      : this._groupSelect("group", d.group);
    const types = this.settings.types.map((t) => `<option value="${t}" ${d.type === t ? "selected" : ""}>${e(this.typeLabel(t))}</option>`).join("");
    const group = label ? label.id : d.group;
    const profiles = this.settings.profiles.filter((p) => group && p.zones.includes(group));
    const profileHtml = profiles.length
      ? profiles.map((p) => `<div class="chk"><input type="checkbox" data-profile="${e(p.id)}" ${d.excluded.includes(p.id) ? "" : "checked"}><span>${e(p.name)}</span></div>`).join("") + `<div class="muted">${e(this._t("profilesHint"))}</div>`
      : `<div class="muted">${e(this._t("noProfiles"))}</div>`;
    return `
      <h2>${e(this._t("sensorTitle"))}</h2>
      <div class="row"><div class="n">${e(x.name)}<small>${e(d.entity)} · ${e(x.state || "")}</small></div></div>
      <label>${e(this._t("sensorGroup"))}</label>${groupSel}${this._err("group")}
      <label>${e(this._t("type"))}</label><select data-f="type">${types}</select>${this._err("type")}
      <div class="chk" style="margin-top:12px"><input type="checkbox" data-f-check="always" ${d.always ? "checked" : ""}><span>${e(this._t("always"))}</span></div>
      <label>${e(this._t("profilesTitle"))}</label>${profileHtml}${this._err("base")}
      ${this._staleHtml()}`;
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
      ${this._pickerHtml(SENSOR_DOMAINS, d.sensors)}${this._err("base")}
      ${this._alwaysSirensHtml()}`;
  }

  _alwaysSirensHtml() {
    const d = this._draft;
    const sir = this.settings.sirens;
    const pe = this.settings.profile_edit;
    if (!sir || !pe) return "";
    const name = (id) => (sir.candidates.find((c) => c.id === id) || { name: id }).name;
    const sirens = sir.registered.length
      ? sir.registered.map((id) => `<div class="chk"><input type="checkbox" data-asiren="${e(id)}" ${d.sirens.includes(id) ? "checked" : ""}><span>${e(name(id))}</span></div>`).join("")
      : `<div class="muted">${e(this._t("alwaysNoSirens"))}</div>`;
    const opts = (list, group, value) => list.map((x) => `<option value="${e(x)}" ${x === value ? "selected" : ""}>${e((this._t(group) || {})[x] || x)}</option>`).join("");
    return `<div class="box"><b>${e(this._t("alwaysSirens"))}</b>
      <div class="chk"><input type="checkbox" data-f-check="sirens_enabled" ${d.sirens_enabled ? "checked" : ""}><span>${e(this._t("alwaysSirensOn"))}</span></div>
      <div class="muted">${e(this._t("alwaysSirensHint"))}</div>
      ${d.sirens_enabled ? `${sirens}
        <div class="inline"><div><label>${e(this._t("alwaysTone"))}</label><select data-f="siren_tone">${opts(pe.choices.tones, "tones", d.siren_tone)}</select></div>
        <div><label>${e(this._t("alwaysVolume"))}</label><select data-f="siren_volume">${opts(pe.choices.volumes, "volumes", d.siren_volume)}</select></div>
        <div><label>${e(this._t("alwaysReaction"))}</label><input class="small" type="number" min="1" max="3600" data-f="reaction_time" value="${e(d.reaction_time)}"></div></div>` : ""}
    </div>`;
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
      const on = root.querySelector('[data-f-check="sirens_enabled"]');
      if (on) d.sirens_enabled = on.checked;
      if (root.querySelector("[data-asiren]")) {
        d.sirens = [...root.querySelectorAll("[data-asiren]")].filter((el) => el.checked).map((el) => el.dataset.asiren);
      }
    }
    if (this.kind === "sensor") {
      const always = root.querySelector('[data-f-check="always"]');
      if (always) d.always = always.checked;
      const boxes = [...root.querySelectorAll("[data-profile]")];
      if (boxes.length) {
        const shown = boxes.map((el) => el.dataset.profile);
        d.excluded = [...d.excluded.filter((p) => !shown.includes(p)), ...boxes.filter((el) => !el.checked).map((el) => el.dataset.profile)];
      }
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
    if (this.kind === "sensor") {
      const label = this.settings.groups.find((g) => (this.settings.label_members?.[g.id] || []).includes(d.entity));
      return [
        "sensor_save",
        {
          entity: d.entity,
          group: label ? label.id : d.group || null,
          type: d.type,
          always: d.always,
          excluded: d.excluded,
          stale: { mode: d.stale_mode, hours: d.stale_hours === "" ? null : Number(d.stale_hours) },
        },
      ];
    }
    return [
      "always_save",
      {
        zones: d.zones,
        sensors: d.sensors,
        sirens_settings: {
          sirens_enabled: d.sirens_enabled,
          sirens: d.sirens,
          siren_tone: d.siren_tone,
          siren_volume: d.siren_volume,
          reaction_time: Number(d.reaction_time),
        },
      },
    ];
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
      this.dispatchEvent(new CustomEvent("hw-saved", { bubbles: true, composed: true, detail: { revision: result.revision } }));
      return;
    }
    this._errors = result.errors || { base: "failed" };
    this._details = result.details || {};
    if (this._errors.base === "changed_elsewhere") {
      this.dispatchEvent(new CustomEvent("hw-stale", { bubbles: true, composed: true }));
    }
    this._render();
    window.HauswachtRevealError?.(this.shadowRoot); // Fehlermeldung ins Bild holen
  }

  _deleteAction() {
    if (this.kind === "group" && this._draft.id) return ["group_delete", { id: this._draft.id }];
    if (this.kind === "tilt" && this._draft.existing) return ["tilt_delete", { entity: this._draft.entity }];
    if (this.kind === "strength" && this._draft.existing) return ["strength_delete", { entity: this._draft.entity }];
    return null;
  }

  _render() {
    const body =
      this.kind === "group"
        ? this._groupForm()
        : this.kind === "tilt"
          ? this._tiltForm()
          : this.kind === "strength"
            ? this._strengthForm()
            : this.kind === "sensor"
              ? this._sensorForm()
              : this._alwaysForm();
    const del = this._deleteAction();
    this.shadowRoot.innerHTML = `<style>${EDIT_STYLE}</style><div class="sheet">${body}
      <div class="bar"><button class="b p" data-a="save" ${this._busy ? "disabled" : ""}>${e(this._busy ? this._t("saving") : this._t("save"))}</button>
      <button class="b" data-a="cancel">${e(this._t("cancel"))}</button>
      ${del ? `<button class="b d" data-a="delete">${e(this._t("delete"))}</button>` : ""}</div></div>`;
    window.HauswachtDocs?.decorate(this.shadowRoot, this.helpKey, this._lang);
    // ⓘ an den Beschriftungen (0.62)
    window.HauswachtDocs?.explain?.(this.shadowRoot, Object.entries(this._t("info") || {}).map(([key, text]) => [this._t(key), text]), this._lang);
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
    const staleMode = root.querySelector('[data-f="stale_mode"]');
    if (staleMode) {
      staleMode.addEventListener("change", () => {
        this._collect();
        this._render();
      });
    }
    const sirensOn = root.querySelector('[data-f-check="sirens_enabled"]');
    if (sirensOn) {
      sirensOn.addEventListener("change", () => {
        this._collect();
        this._render();
      });
    }
    root.querySelectorAll("[data-a]").forEach((btn) =>
      btn.addEventListener("click", () => {
        const a = btn.dataset.a;
        if (a === "cancel") this._close();
        else if (a === "save") {
          this._collect();
          this._apply(...this._payload());
        } else if (a === "delete") {
          if (window.confirm(this._t("deleteConfirm"))) this._apply(...this._deleteAction());
        } else if (a === "stale-take") {
          this._collect();
          const obs = this.settings.system?.silence?.sensors?.[this._draft.entity];
          if (obs?.advice) Object.assign(this._draft, { stale_mode: "hours", stale_hours: obs.advice });
          this._render();
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
    root.querySelectorAll("[data-toggle]").forEach((el) =>
      el.addEventListener("change", () => {
        if (el.dataset.toggle === "all") this._showAll = el.checked;
        else this._showAssigned = el.checked;
        this._rerender();
      })
    );
    if (this.kind === "sensor") {
      const g = root.querySelector('[data-f="group"]');
      if (g) g.addEventListener("change", () => this._rerender());
    }
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

// Für weitere Seitenblätter (Profile …): dieselbe Gestaltung
window.HauswachtEditStyle = window.HauswachtEditStyle || EDIT_STYLE;

// Nach einem abgelehnten Speichern: erste Fehlermeldung ins Bild holen. Die Dialoge sind lang;
// ohne das stand die Meldung oft unten außer Sicht, und es sah aus, als würde nicht gespeichert.
window.HauswachtRevealError =
  window.HauswachtRevealError ||
  ((root) => {
    requestAnimationFrame(() => {
      const err = root && root.querySelector(".err, .msgs, .error");
      if (err) err.scrollIntoView({ block: "center", behavior: "smooth" });
    });
  });

// Gemeinsame Prüfung (ADR 0017): Hinweise des Assistenten direkt im Seitenblatt – schon vor dem
// Speichern. Nur Hinweis: Speichern geht trotzdem. Ein Vorschlag ändert nur den Entwurf im
// Seitenblatt; gespeichert wird erst mit „Speichern“.
const ADVISOR_TEXT = {
  de: {
    title: "Assistent",
    level: { error: "Fehler", warning: "Warnung", tip: "Tipp" },
    why: "Warum?",
    elsewhere: "Vorschlag: {label} (an anderer Stelle ändern)",
    weakens: "Dieser Vorschlag macht die Anlage an einer Stelle nachgiebiger:\n\n{label}\n\n{why}\n\nTrotzdem übernehmen? Gespeichert wird erst mit „Speichern“.",
  },
  en: {
    title: "Assistant",
    level: { error: "Error", warning: "Warning", tip: "Tip" },
    why: "Why?",
    elsewhere: "Suggestion: {label} (change it elsewhere)",
    weakens: "This suggestion makes the system more lenient in one place:\n\n{label}\n\n{why}\n\nApply anyway? Nothing is saved until you press “Save”.",
  },
};
const ADVISOR_ICON = { error: "⛔", warning: "⚠️", tip: "💡" };
const ADVISOR_STYLE = `
  .advice { margin: 14px 0 6px; }
  .advice:empty { display: none; }
  .advice h3 { font-size: .95rem; font-weight: 500; margin: 0 0 6px; }
  .adv { border-left: 4px solid var(--divider-color); border-radius: 6px; padding: 8px 10px; margin: 6px 0; background: var(--secondary-background-color); font-size: .9rem; }
  .adv.error { border-left-color: var(--error-color, #db4437); }
  .adv.warning { border-left-color: var(--warning-color, #ffa600); }
  .adv.tip { border-left-color: var(--info-color, #039be5); }
  .adv details { margin-top: 4px; color: var(--secondary-text-color); }
  .adv details summary { cursor: pointer; color: var(--primary-color); }
  .adv .fixes { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }
  .adv .else { color: var(--secondary-text-color); font-size: .85rem; margin-top: 4px; }`;

window.HauswachtAdvisor =
  window.HauswachtAdvisor ||
  (() => {
    const esc = (value) =>
      String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
    const text = (lang) => ADVISOR_TEXT[lang] || ADVISOR_TEXT.en;
    return {
      style: ADVISOR_STYLE,
      // Einstellungen prüfen, wie sie nach „Speichern“ wären (nichts wird gespeichert)
      async check(hass, action, data, lang) {
        try {
          return await hass.callWS({ type: "hauswacht/advisor/check", action, data, language: lang });
        } catch (_err) {
          return { findings: [] }; // Prüfung ist nur ein Hinweis – Fehler stillschweigend
        }
      },
      // canApply(fix): kann dieses Seitenblatt den Vorschlag in den Entwurf übernehmen?
      render(findings, lang, canApply) {
        if (!findings || !findings.length) return "";
        const t = text(lang);
        const rows = findings.map((f, i) => {
          const fixes = (f.fixes || []).map((fix, j) =>
            canApply(fix)
              ? `<button type="button" class="b" data-advfix="${i}:${j}">${fix.weakens ? "⚠ " : ""}${esc(fix.label)}</button>`
              : `<div class="else">${esc(t.elsewhere.replace("{label}", fix.label))}</div>`
          );
          const buttons = fixes.filter((x) => x.startsWith("<button")).join("");
          const notes = fixes.filter((x) => !x.startsWith("<button")).join("");
          return `<div class="adv ${esc(f.level)}"><div>${ADVISOR_ICON[f.level] || ""} <b>${esc(t.level[f.level] || f.level)}:</b> ${esc(f.text)}</div>
            <details><summary>${esc(t.why)}</summary>${esc(f.why)}</details>
            ${buttons ? `<div class="fixes">${buttons}</div>` : ""}${notes}</div>`;
        });
        return `<h3>${esc(t.title)}</h3>${rows.join("")}`;
      },
      // Vorschlag in ein Objekt übernehmen: path „a.b“, op set | add | remove
      apply(target, path, fix) {
        const keys = path.split(".");
        const last = keys.pop();
        let obj = target;
        for (const key of keys) {
          obj[key] = obj[key] || {};
          obj = obj[key];
        }
        if (fix.op === "set") obj[last] = fix.value;
        else if (fix.op === "add") obj[last] = [...new Set([...(obj[last] || []), fix.value])];
        else if (fix.op === "remove") obj[last] = (obj[last] || []).filter((x) => x !== fix.value);
      },
      // Abschwächende Vorschläge brauchen eine ausdrückliche Bestätigung
      confirm(fix, finding, lang) {
        if (!fix.weakens) return true;
        return window.confirm(text(lang).weakens.replace("{label}", fix.label).replace("{why}", finding.why));
      },
    };
  })();
