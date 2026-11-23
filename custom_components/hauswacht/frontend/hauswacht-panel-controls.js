// Hauswacht – Einstellungsseite: Bedienteile und Karten (ADR 0011).
//
// Seitenblatt <hauswacht-control-editor> mit den Arten
// - control: Keypad (Zigbee2MQTT oder allgemein), NFC-Aufkleber, RFID-Leser, Taster,
//   Türschloss anlegen und einstellen,
// - card: eine Karte umbenennen, anderem Benutzer geben, deaktivieren, löschen,
// - cardnew: neue Karte anlernen – hinhalten (die Seite fragt alle 2 Sekunden nach) oder
//   Nummer eintippen.
// Dieselben Regeln wie im Dialog (core/changes/controls.py, core/changes/cards.py).

const CT = {
  de: {
    save: "Speichern",
    saving: "Speichere …",
    cancel: "Abbrechen",
    del: "Löschen",
    delSure: "Wirklich löschen?",
    none: "–",
    kinds: { keypad: "Keypad (Zigbee2MQTT)", generic_keypad: "Keypad (allgemein: ZHA, Z-Wave, ESPHome …)", mqtt_keypad: "MQTT-Schnittstelle (Tablet, Eigenbau, Node-RED …)", sticker: "NFC-Aufkleber (Companion App)", reader: "RFID-/NFC-Leser", button: "Taster", lock: "Türschloss" },
    newTitle: "Bedienteil anlegen",
    editTitle: "Bedienteil bearbeiten",
    kind: "Art",
    name: "Name",
    area: "Bereich",
    allAreas: "Alle Bereiche",
    keypadDevice: "Keypad-Gerät (aus Zigbee2MQTT)",
    topic: "MQTT-Topic (nur für Experten, leer = aus dem Gerät)",
    passageKey: "Durchgang (rein/raus, bleibt scharf)",
    keys: { arm_day_zones: "Taste „Tag“ → Alarmprofil", arm_night_zones: "Taste „Nacht“ → Alarmprofil", arm_all_zones: "Taste „Alle“ → Alarmprofil" },
    login: "Anmeldung",
    logins: { pin_or_card: "PIN oder Karte", card: "Karte", card_and_pin: "Karte und PIN" },
    emergency: "Notruf-Taste",
    emergencies: { off: "Aus", silent: "Stiller Notruf (Push)", alarm: "Alarm" },
    tag: "Aufkleber-ID (Einstellungen → Bereiche, Labels & Zonen → Tags)",
    device: "Lesegerät",
    action: "Aktion",
    actions: { disarm: "Unscharf schalten", arm: "Scharf schalten", toggle: "Umschalten (scharf ↔ unscharf)", passage: "Durchgang (wenn das Profil ihn erlaubt, sonst unscharf)" },
    lockUnlock: "Aufschließen bei scharf",
    unlocks: { disarm: "Unscharf schalten", passage: "Durchgang, wenn das Profil ihn erlaubt – sonst unscharf" },
    profile: "Alarmprofil (für scharf/umschalten)",
    entity: "Taster (Ereignis oder Aktions-Sensor)",
    presses: "Druckart → Alarmprofil",
    pressesHint: "Der Taster schaltet nur scharf, nie unscharf. Leer = diese Druckart tut nichts.",
    pressValue: "Druckart (Wert des Sensors, z. B. single)",
    lockEntity: "Schloss",
    source: "Wer hat aufgeschlossen? (Quelle)",
    sources: { nuki_mqtt: "Nuki über MQTT (lockActionEvent)", generic: "Allgemein (Sensor oder Ereignis)" },
    lockTopic: "Nuki: MQTT-Topic des Schlosses (z. B. nuki/3A1B2C4D)",
    who: "Allgemein: Sensor oder Ereignis mit der Kennung",
    lockProfile: "Optional: beim Abschließen scharf schalten (Alarmprofil)",
    pick: "Namen tippen oder aus der Liste wählen",
    ident: "Kennung für Automationen",
    identNew: "Die Kennung wird beim Speichern aus dem Namen gebildet.",
    genButtons: "Tasten → Alarmprofil",
    genButtonsHint: "Name der Taste, wie ihn dein Blueprint bzw. deine Automation als „button“ sendet (z. B. away). „disarm“ (unscharf) und „emergency“ (Notruf) gibt es immer.",
    genButton: "Tastenname",
    templates: "Fertige Vorlagen (ungetestet – eigene Verantwortung)",
    mqttTopic: "Basis-Topic (z. B. hauswacht/flur)",
    mqttButtons: "Befehlswörter → Alarmprofil",
    mqttButtonsHint: "Das Wort, das dein Gerät sendet, z. B. ARM_AWAY (wird zu arm_away). Unscharf und Notruf haben eigene Wörter (unten).",
    mqttWord: "Befehlswort",
    disarmWord: "Befehlswort für Unscharf",
    panicWord: "Befehlswort für Notruf",
    codeField: "Name des Code-Felds im JSON",
    words: "Eigene Zustandswörter (für Experten, eine Zeile je Zustand, z. B. armed_away: ARMED_AWAY)",
    mqttTopics: "Hauswacht hört auf {t}/set und sendet an {t}/state, /attributes, /response und /availability.",
    ringImport: "Ring Keypad v2: Blueprint importieren ↗",
    espExample: "ESPHome-Beispiel ansehen ↗",
    templatesHint: "Öffnet in einem neuen Tab, in genau deiner Hauswacht-Version.",
    hints: {
      mqtt_keypad: "Getestet – automatische Tests, noch ohne Rückmeldung mit echten Geräten. Für Geräte und Programme, die nur MQTT sprechen. Gespeicherte Befehle (retain) führt Hauswacht nie aus. Wer auf den Broker schreiben darf, darf an die Anlage – Broker-Zugang absichern.",
      generic_keypad: "Getestet – automatische Tests, noch ohne Rückmeldung mit echten Geräten. Für Keypads, die Hauswacht nicht selbst kennt: Ein Blueprint oder eine Automation meldet Taste und PIN/Karte mit der Aktion hauswacht.keypad_input. Was das Keypad zeigen soll, steht in der Entität „Name Anzeige“.",
      keypad: "Hauswacht empfängt Taste, PIN oder Karte und bestätigt jede Eingabe; danach zeigt das Keypad den Zustand. Den Sabotage-Kontakt des Keypads in eine Meldergruppe aufnehmen (Typ Manipulation).",
      sticker: "Ausgewiesen wird mit dem Handy: Das angemeldete Home-Assistant-Konto muss einer Person zugeordnet sein.",
      reader: "Ein fester Leser, der in Home Assistant „Tag gescannt“ auslöst (z. B. ESPHome mit PN532/RC522). Ausgewiesen wird mit den Karten der Personen.",
      button: "Schaltet ein Alarmprofil scharf – nie unscharf, weil ein Taster niemanden ausweist.",
      lock: "Schaltet unscharf, wenn ein bekannter Benutzer aufschließt. Hauswacht schaltet das Schloss selbst nie. Kennungen: einmal aufschließen, solange alles unscharf ist – sie erscheinen dann unter „Neue Karte anlernen“.",
    },
    cardTitle: "Karte",
    cardNewTitle: "Neue Karte anlernen",
    cardName: "Name (z. B. Schlüsselanhänger blau)",
    owner: "Gehört",
    active: "Aktiv",
    lastUsed: "Zuletzt benutzt",
    never: "noch nie",
    hold: "Halte die Karte jetzt an ein Keypad oder einen Leser – sie erscheint hier von selbst.",
    learnOff: "Anlernen ist aus (Anlernzeit 0). Stell die Anlernzeit unter Bedienteile ein – oder tippe die Nummer ein.",
    found: "Gelesene unbekannte Karten",
    noneYet: "Noch keine neue Karte gelesen …",
    readAt: "gelesen an {s} um {t}",
    typeIn: "Oder Nummer eintippen",
    random: "An {s} wurde um {t} eine Zufallsnummer gelesen (z. B. ein Handy). Sie ändert sich bei jedem Lesen und taugt nicht als Ausweis.",
    chosen: "Gewählte Karte",
    errors: {
      control_no_buttons: "Mindestens eine Taste mit Alarmprofil eintragen.",
      control_button_reserved: "„disarm“ und „emergency“ sind feste Tasten – bitte einen anderen Namen wählen.",
      control_keypad_topic: "Bitte das Keypad-Gerät wählen oder das MQTT-Topic eintragen.",
      control_profile_required: "Für „scharf“ bzw. „umschalten“ ein Alarmprofil wählen.",
      control_tag: "Bitte die Aufkleber-ID angeben.",
      control_device: "Bitte das Lesegerät wählen.",
      control_entity: "Bitte eine Entität wählen.",
      control_who: "Für die allgemeine Quelle einen Sensor oder ein Ereignis mit der Kennung wählen.",
      control_topic: "Bitte das MQTT-Topic angeben.",
      control_profile_area: "Das Alarmprofil gehört zu einem anderen Bereich als das Bedienteil.",
      button_no_press: "Mindestens eine Druckart einem Alarmprofil zuordnen.",
      card_missing: "Bitte eine Karte wählen oder die Nummer eintippen.",
      tag_taken: "Diese Karte gehört schon: {c}",
      tag_random: "Das ist eine Zufallsnummer (z. B. ein Handy) – sie taugt nicht als Ausweis.",
      user_missing: "Bitte eine Person wählen.",
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
    kinds: { keypad: "Keypad (Zigbee2MQTT)", generic_keypad: "Keypad (generic: ZHA, Z-Wave, ESPHome …)", mqtt_keypad: "MQTT interface (tablet, home-made, Node-RED …)", sticker: "NFC sticker (companion app)", reader: "RFID/NFC reader", button: "Button", lock: "Door lock" },
    newTitle: "Add control device",
    editTitle: "Edit control device",
    kind: "Type",
    name: "Name",
    area: "Area",
    allAreas: "All areas",
    keypadDevice: "Keypad device (from Zigbee2MQTT)",
    topic: "MQTT topic (experts only, empty = from the device)",
    passageKey: "Passage (in/out, stays armed)",
    keys: { arm_day_zones: "Key “day” → alarm profile", arm_night_zones: "Key “night” → alarm profile", arm_all_zones: "Key “all” → alarm profile" },
    login: "Login",
    logins: { pin_or_card: "PIN or card", card: "Card", card_and_pin: "Card and PIN" },
    emergency: "Emergency key",
    emergencies: { off: "Off", silent: "Silent emergency (push)", alarm: "Alarm" },
    tag: "Sticker ID (Settings → Areas, labels & zones → Tags)",
    device: "Reader device",
    action: "Action",
    actions: { disarm: "Disarm", arm: "Arm", toggle: "Toggle (armed ↔ disarmed)", passage: "Passage (if the profile allows it, otherwise disarm)" },
    lockUnlock: "Unlocking while armed",
    unlocks: { disarm: "Disarm", passage: "Passage if the profile allows it – otherwise disarm" },
    profile: "Alarm profile (for arm/toggle)",
    entity: "Button (event or action sensor)",
    presses: "Press type → alarm profile",
    pressesHint: "The button only arms, never disarms. Empty = this press type does nothing.",
    pressValue: "Press type (value of the sensor, e.g. single)",
    lockEntity: "Lock",
    source: "Who unlocked? (source)",
    sources: { nuki_mqtt: "Nuki via MQTT (lockActionEvent)", generic: "Generic (sensor or event)" },
    lockTopic: "Nuki: MQTT topic of the lock (e.g. nuki/3A1B2C4D)",
    who: "Generic: sensor or event with the ID",
    lockProfile: "Optional: arm when locking (alarm profile)",
    ident: "ID for automations",
    identNew: "The ID is made from the name when saving.",
    genButtons: "Buttons → alarm profile",
    genButtonsHint: "Name of the button as your blueprint or automation sends it as \"button\" (e.g. away). \"disarm\" and \"emergency\" always exist.",
    genButton: "Button name",
    templates: "Ready-made templates (untested – own responsibility)",
    mqttTopic: "Base topic (e.g. hauswacht/hallway)",
    mqttButtons: "Command words → alarm profile",
    mqttButtonsHint: "The word your device sends, e.g. ARM_AWAY (becomes arm_away). Disarm and emergency have their own words (below).",
    mqttWord: "Command word",
    disarmWord: "Command word for disarm",
    panicWord: "Command word for emergency",
    codeField: "Name of the code field in JSON",
    words: "Own state words (for experts, one line per state, e.g. armed_away: ARMED_AWAY)",
    mqttTopics: "Hauswacht listens on {t}/set and sends to {t}/state, /attributes, /response and /availability.",
    ringImport: "Ring Keypad v2: import blueprint ↗",
    espExample: "View ESPHome example ↗",
    templatesHint: "Opens in a new tab, in exactly your Hauswacht version.",
    pick: "Type a name or pick from the list",
    hints: {
      mqtt_keypad: "Tested – automated tests, no feedback with real devices yet. For devices and programs that only speak MQTT. Hauswacht never executes stored commands (retain). Whoever may write to the broker may operate the system – secure broker access.",
      generic_keypad: "Tested – automated tests, no feedback with real devices yet. For keypads Hauswacht does not know itself: a blueprint or automation reports button and PIN/card with the action hauswacht.keypad_input. What the keypad should show is in the entity \"name display\".",
      keypad: "Hauswacht receives key, PIN or card and confirms every entry; then the keypad shows the state. Add the keypad's tamper contact to a sensor group (type tamper).",
      sticker: "Identification is the phone: the logged-in Home Assistant account must be linked to a person.",
      reader: "A fixed reader that fires “tag scanned” in Home Assistant (e.g. ESPHome with PN532/RC522). Identification uses the people's cards.",
      button: "Arms an alarm profile – never disarms, because a button identifies nobody.",
      lock: "Disarms when a known user unlocks. Hauswacht never operates the lock itself. IDs: unlock once while everything is disarmed – they then appear under “learn a new card”.",
    },
    cardTitle: "Card",
    cardNewTitle: "Learn a new card",
    cardName: "Name (e.g. blue key fob)",
    owner: "Belongs to",
    active: "Active",
    lastUsed: "Last used",
    never: "never",
    hold: "Hold the card to a keypad or reader now – it appears here by itself.",
    learnOff: "Learning is off (learning time 0). Set the learning time under control devices – or type in the number.",
    found: "Unknown cards read",
    noneYet: "No new card read yet …",
    readAt: "read at {s} at {t}",
    typeIn: "Or type in the number",
    random: "A random ID was read at {s} at {t} (e.g. a phone). It changes on every read and cannot be used as a credential.",
    chosen: "Chosen card",
    errors: {
      control_no_buttons: "Enter at least one button with an alarm profile.",
      control_button_reserved: "\"disarm\" and \"emergency\" are fixed buttons – please choose another name.",
      control_keypad_topic: "Please choose the keypad device or enter the MQTT topic.",
      control_profile_required: "Choose an alarm profile for “arm” or “toggle”.",
      control_tag: "Please enter the sticker ID.",
      control_device: "Please choose the reader device.",
      control_entity: "Please choose an entity.",
      control_who: "For the generic source, choose a sensor or event with the ID.",
      control_topic: "Please enter the MQTT topic.",
      control_profile_area: "The alarm profile belongs to a different area than the control device.",
      button_no_press: "Assign at least one press type to an alarm profile.",
      card_missing: "Please choose a card or type in the number.",
      tag_taken: "This card already belongs to: {c}",
      tag_random: "This is a random ID (e.g. a phone) – it cannot be used as a credential.",
      user_missing: "Please choose a person.",
      disarm_first: "Disarm all areas first – then saving works.",
      changed_elsewhere: "Something was changed elsewhere in the meantime. The page reloads – please try again.",
      failed: "Saving failed.",
    },
  },
};

const ce = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

class HauswachtControlEditor extends HTMLElement {
  // open({hass, settings, kind, item, ctrlKind, presetName}) – kind: control | card | cardnew
  open(options) {
    Object.assign(this, options);
    const sys = this.settings.system;
    this._errors = {};
    this._details = {};
    this._busy = false;
    this._sure = false;
    if (this.kind === "control") {
      const found = sys.controls.items.find((c) => c.id === this.item);
      this._draft = found
        ? JSON.parse(JSON.stringify(found))
        : { kind: this.ctrlKind || "keypad", name: this.presetName || "", area: sys.controls.choices.all_areas, buttons: {}, presses: {}, login: "", action: "disarm", source: "nuki_mqtt" };
      this._draft.buttons = this._draft.buttons || {};
      this._draft.presses = this._draft.presses || {};
      // Taster ohne eigene Druckarten: drei freie Zeilen
      this._pressRows = Object.entries(this._draft.presses);
      while (this._pressRows.length < 3) this._pressRows.push(["", ""]);
      // Allgemeines Keypad: vier Tasten mit freiem Namen (Vorschlag home/away/night)
      const free = ["generic_keypad", "mqtt_keypad"].includes(this._draft.kind);
      this._btnRows = free ? Object.entries(this._draft.buttons) : [];
      if (!this._btnRows.length) this._btnRows = this._defaultButtons(this._draft.kind);
      while (this._btnRows.length < 4) this._btnRows.push(["", ""]);
    } else if (this.kind === "card") {
      const card = sys.cards.cards.find((c) => c.tag === this.item) || {};
      this._card = card;
      this._draft = { name: card.name || "", user: card.user, active: card.active !== false, delete: false };
    } else {
      this._cards = sys.cards;
      this._draft = { card: "", typed: "", user: sys.cards.users[0]?.id || "", name: "", active: true };
      this._poll();
    }
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this._render();
  }

  disconnectedCallback() {
    clearTimeout(this._timer);
  }

  async _poll() {
    // Neue Karte: alle 2 Sekunden nachsehen, ob eine unbekannte Karte gelesen wurde
    clearTimeout(this._timer);
    this._timer = setTimeout(async () => {
      if (this.kind !== "cardnew") return;
      try {
        const fresh = await this.hass.callWS({ type: "hauswacht/settings/new_cards" });
        const before = this._cards.unknown.map((u) => u.tag).join();
        this._cards = fresh;
        if (fresh.unknown.map((u) => u.tag).join() !== before) {
          this._collect();
          if (!this._draft.card && fresh.unknown.length) this._draft.card = fresh.unknown[fresh.unknown.length - 1].tag;
          this._render();
        }
      } catch (_err) {
        // nächste Runde
      }
      if (this.isConnected) this._poll();
    }, 2000);
  }

  get _lang() {
    return (this.hass?.language || "en").startsWith("de") ? "de" : "en";
  }

  _t(key) {
    return CT[this._lang][key] ?? CT.en[key] ?? key;
  }

  _err(key) {
    const code = this._errors[key];
    if (!code) return "";
    const text = (this._t("errors")[code] || code).replace("{c}", this._details.conflict || "");
    return `<div class="err">${ce(text)}</div>`;
  }

  _select(field, value, entries) {
    return `<select data-f="${field}">${entries.map(([v, l]) => `<option value="${ce(v)}" ${String(v) === String(value ?? "") ? "selected" : ""}>${ce(l)}</option>`).join("")}</select>`;
  }

  _profiles(withNone = true, passage = false) {
    const list = this.settings.system.profiles.map((p) => [p.id, p.name]);
    // Keypad-Tasten: auch "Durchgang" (ADR 0013)
    if (passage) list.push(["__passage__", this._t("passageKey")]);
    return withNone ? [["", this._t("none")], ...list] : list;
  }

  // Auswahl aus vielen Einträgen: Eingabe mit Vorschlägen (Name oder ID)
  _picker(field, value, choices, listId) {
    const shown = (choices.find((c) => c.id === value) || { name: value || "" }).name;
    return `<input data-pick="${field}" list="${listId}" value="${ce(shown)}" placeholder="${ce(this._t("pick"))}">
      <datalist id="${listId}">${choices.map((c) => `<option value="${ce(c.name)}">${ce(c.id)}</option>`).join("")}</datalist>`;
  }

  _wordsText(words) {
    if (typeof words === "string") return words;
    return Object.entries(words || {}).map(([k, v]) => `${k}: ${v}`).join("\n");
  }

  _defaultButtons(kind) {
    const names = kind === "mqtt_keypad" ? ["arm_away", "arm_home", "arm_night"] : ["home", "away", "night"];
    return names.map((b) => [b, ""]);
  }

  // Fertige Vorlagen für allgemeine Keypads – immer in einem neuen Tab
  _templates() {
    const docs = window.HauswachtDocs;
    if (!docs?.blueprintImport) return "";
    const link = (href, text) => `<a href="${ce(href)}" target="_blank" rel="noreferrer noopener">${ce(text)}</a>`;
    return `<div class="box"><b>${ce(this._t("templates"))}</b>
      <div>${link(docs.blueprintImport("ring_keypad_v2.yaml"), this._t("ringImport"))}</div>
      <div>${link(docs.file("blueprints/esphome/hauswacht_keypad.yaml"), this._t("espExample"))}</div>
      <div class="muted">${ce(this._t("templatesHint"))}</div></div>`;
  }

  _controlForm() {
    const d = this._draft;
    const sys = this.settings.system;
    const ch = sys.controls.choices;
    const areas = [[ch.all_areas, this._t("allAreas")], ...sys.areas.map((a) => [a.id, a.name])];
    let fields = "";
    if (d.kind === "keypad") {
      fields = `<label>${ce(this._t("keypadDevice"))}</label>${this._picker("keypad_device", d.keypad_device, ch.mqtt_devices, "hw-mqtt")}${this._err("keypad_device")}
        <label>${ce(this._t("topic"))}</label><input data-f="topic" value="${ce(d.topic || "")}">
        ${ch.arm_keys.map((k) => `<label>${ce(this._t("keys")[k] || k)}</label>${this._select(`btn:${k}`, d.buttons[k] || "", this._profiles(true, true))}`).join("")}
        <label>${ce(this._t("login"))}</label>${this._select("login", d.login || "pin_or_card", ["pin_or_card", "card_and_pin"].map((v) => [v, this._t("logins")[v]]))}
        <label>${ce(this._t("emergency"))}</label>${this._select("emergency", d.emergency || "off", ["off", "silent", "alarm"].map((v) => [v, this._t("emergencies")[v]]))}`;
    } else if (d.kind === "mqtt_keypad") {
      const rows = this._btnRows
        .map(([b, pid], i) => `<div class="inline"><div style="flex:1"><label>${ce(this._t("mqttWord"))}</label><input data-gb="${i}" value="${ce(b)}"></div><div style="flex:1"><label>&nbsp;</label>${this._select(`gp:${i}`, pid, this._profiles(true, true))}</div></div>`)
        .join("");
      const topic = d.topic || "hauswacht/…";
      fields = `<label>${ce(this._t("mqttTopic"))}</label><input data-f="topic" value="${ce(d.topic || "")}">${this._err("topic")}
        <div class="muted">${ce(this._t("mqttTopics").replaceAll("{t}", topic))}</div>
        <label>${ce(this._t("mqttButtons"))}</label><div class="muted">${ce(this._t("mqttButtonsHint"))}</div>${rows}
        <label>${ce(this._t("disarmWord"))}</label><input data-f="disarm_word" value="${ce(d.disarm_word || "DISARM")}">
        <label>${ce(this._t("panicWord"))}</label><input data-f="panic_word" value="${ce(d.panic_word || "PANIC")}">
        <label>${ce(this._t("codeField"))}</label><input data-f="code_field" value="${ce(d.code_field || "code")}">
        <label>${ce(this._t("login"))}</label>${this._select("login", d.login || "pin_or_card", ["pin_or_card", "card_and_pin"].map((v) => [v, this._t("logins")[v]]))}
        <label>${ce(this._t("emergency"))}</label>${this._select("emergency", d.emergency || "off", ["off", "silent", "alarm"].map((v) => [v, this._t("emergencies")[v]]))}
        <label>${ce(this._t("words"))}</label><textarea data-f="words" rows="4">${ce(this._wordsText(d.words))}</textarea>`;
    } else if (d.kind === "generic_keypad") {
      const rows = this._btnRows
        .map(([b, pid], i) => `<div class="inline"><div style="flex:1"><label>${ce(this._t("genButton"))}</label><input data-gb="${i}" value="${ce(b)}"></div><div style="flex:1"><label>&nbsp;</label>${this._select(`gp:${i}`, pid, this._profiles(true, true))}</div></div>`)
        .join("");
      fields = `<div class="box">${ce(this._t("ident"))}: ${this.item ? `<code>${ce(this.item)}</code>` : ce(this._t("identNew"))}</div>
        <label>${ce(this._t("genButtons"))}</label><div class="muted">${ce(this._t("genButtonsHint"))}</div>${rows}
        ${this._templates()}
        <label>${ce(this._t("login"))}</label>${this._select("login", d.login || "pin_or_card", ["pin_or_card", "card_and_pin"].map((v) => [v, this._t("logins")[v]]))}
        <label>${ce(this._t("emergency"))}</label>${this._select("emergency", d.emergency || "off", ["off", "silent", "alarm"].map((v) => [v, this._t("emergencies")[v]]))}`;
    } else if (d.kind === "sticker" || d.kind === "reader") {
      fields = (d.kind === "sticker"
        ? `<label>${ce(this._t("tag"))}</label><input data-f="tag" value="${ce(d.tag || "")}">${this._err("tag")}`
        : `<label>${ce(this._t("device"))}</label>${this._picker("device", d.device, ch.devices, "hw-dev")}${this._err("device")}
           <label>${ce(this._t("login"))}</label>${this._select("login", d.login || "card", ["card", "card_and_pin"].map((v) => [v, this._t("logins")[v]]))}`) +
        `<label>${ce(this._t("action"))}</label>${this._select("action", d.action || "disarm", ["disarm", "arm", "toggle", "passage"].map((v) => [v, this._t("actions")[v]]))}
        <label>${ce(this._t("profile"))}</label>${this._select("profile", d.profile || "", this._profiles())}${this._err("profile")}`;
    } else if (d.kind === "button") {
      const types = ch.event_types[d.entity] || [];
      const rows = types.length
        ? types.map((t) => `<label>${ce(t)}</label>${this._select(`press:${t}`, d.presses[t] || "", this._profiles())}`).join("")
        : this._pressRows.map(([p, pid], i) => `<div class="inline"><div style="flex:1"><label>${ce(this._t("pressValue"))}</label><input data-pv="${i}" value="${ce(p)}"></div><div style="flex:1"><label>&nbsp;</label>${this._select(`pp:${i}`, pid, this._profiles())}</div></div>`).join("");
      fields = `<label>${ce(this._t("entity"))}</label>${this._picker("entity", d.entity, ch.button_entities, "hw-btn")}${this._err("entity")}
        <label>${ce(this._t("presses"))}</label><div class="muted">${ce(this._t("pressesHint"))}</div>${rows}`;
    } else if (d.kind === "lock") {
      fields = `<label>${ce(this._t("lockEntity"))}</label>${this._picker("entity", d.entity, ch.locks, "hw-lock")}${this._err("entity")}
        <label>${ce(this._t("source"))}</label>${this._select("source", d.source || "nuki_mqtt", ["nuki_mqtt", "generic"].map((v) => [v, this._t("sources")[v]]))}
        ${(d.source || "nuki_mqtt") === "nuki_mqtt"
          ? `<label>${ce(this._t("lockTopic"))}</label><input data-f="topic" value="${ce(d.topic || "")}">${this._err("topic")}`
          : `<label>${ce(this._t("who"))}</label>${this._picker("who", d.who, ch.who_entities, "hw-who")}${this._err("who")}`}
        <label>${ce(this._t("lockProfile"))}</label>${this._select("profile", d.profile || "", this._profiles())}
        <label>${ce(this._t("lockUnlock"))}</label>${this._select("action", d.action || "disarm", ["disarm", "passage"].map((v) => [v, this._t("unlocks")[v]]))}`;
    }
    const kindSelect = this.item
      ? `<div class="muted">${ce(this._t("kinds")[d.kind])}</div>`
      : `<label>${ce(this._t("kind"))}</label>${this._select("kind", d.kind, ch.kinds.map((k) => [k, this._t("kinds")[k]]))}`;
    return `<h2>${ce(this.item ? this._t("editTitle") : this._t("newTitle"))}</h2>${kindSelect}
      <div class="muted">${ce(this._t("hints")[d.kind] || "")}</div>
      <label>${ce(this._t("name"))}</label><input data-f="name" value="${ce(d.name || "")}">
      <label>${ce(this._t("area"))}</label>${this._select("area", d.area || ch.all_areas, areas)}
      ${fields}${this._err("base")}`;
  }

  _cardForm() {
    const d = this._draft;
    const c = this._card;
    const users = this.settings.system.cards.users.map((u) => [u.id, u.name]);
    return `<h2>${ce(this._t("cardTitle"))}: ${ce(c.label)}</h2>
      <div class="muted">${ce(this._t("lastUsed"))}: ${ce(c.last_used ? new Date(c.last_used).toLocaleString(this._lang) : this._t("never"))}</div>
      <label>${ce(this._t("cardName"))}</label><input data-f="name" value="${ce(d.name)}">
      <label>${ce(this._t("owner"))}</label>${this._select("user", d.user, users)}
      <div class="chk" style="margin-top:10px"><input type="checkbox" data-b="active" ${d.active ? "checked" : ""}><span>${ce(this._t("active"))}</span></div>${this._err("base")}`;
  }

  _cardNewForm() {
    const d = this._draft;
    const cards = this._cards;
    const users = cards.users.map((u) => [u.id, u.name]);
    const found = cards.unknown.length
      ? cards.unknown
          .map((u) => `<div class="chk"><input type="radio" name="card" value="${ce(u.tag)}" ${d.card === u.tag ? "checked" : ""}><span><b>${ce(u.label)}</b> <span class="muted">${ce(this._t("readAt").replace("{s}", u.source).replace("{t}", u.when))}</span></span></div>`)
          .join("")
      : `<div class="muted">${ce(this._t("noneYet"))}</div>`;
    const random = cards.random_seen
      ? `<div class="warn">${ce(this._t("random").replace("{s}", cards.random_seen.source).replace("{t}", cards.random_seen.when))}</div>`
      : "";
    return `<h2>${ce(this._t("cardNewTitle"))}</h2>
      <div class="box"><b>${ce(cards.learn_minutes ? this._t("hold") : this._t("learnOff"))}</b>
        <label>${ce(this._t("found"))}</label>${found}${random}</div>
      <label>${ce(this._t("typeIn"))}</label><input data-f="typed" value="${ce(d.typed)}">${this._err("card")}
      <label>${ce(this._t("owner"))}</label>${this._select("user", d.user, users)}${this._err("user")}
      <label>${ce(this._t("cardName"))}</label><input data-f="name" value="${ce(d.name)}">
      <div class="chk" style="margin-top:10px"><input type="checkbox" data-b="active" ${d.active ? "checked" : ""}><span>${ce(this._t("active"))}</span></div>${this._err("base")}`;
  }

  _collect() {
    const root = this.shadowRoot;
    if (!root) return;
    const d = this._draft;
    const ch = this.settings.system.controls.choices;
    const lists = { keypad_device: ch.mqtt_devices, device: ch.devices, entity: d.kind === "lock" ? ch.locks : ch.button_entities, who: ch.who_entities };
    root.querySelectorAll("[data-f]").forEach((el) => {
      const field = el.dataset.f;
      if (field.startsWith("btn:")) {
        if (el.value) d.buttons[field.slice(4)] = el.value;
        else delete d.buttons[field.slice(4)];
      } else if (field.startsWith("press:")) {
        if (el.value) d.presses[field.slice(6)] = el.value;
        else delete d.presses[field.slice(6)];
      } else if (field.startsWith("pp:")) {
        this._pressRows[Number(field.slice(3))][1] = el.value;
      } else if (field.startsWith("gp:")) {
        this._btnRows[Number(field.slice(3))][1] = el.value;
      } else d[field] = el.value;
    });
    root.querySelectorAll("[data-pv]").forEach((el) => (this._pressRows[Number(el.dataset.pv)][0] = el.value));
    root.querySelectorAll("[data-gb]").forEach((el) => (this._btnRows[Number(el.dataset.gb)][0] = el.value));
    root.querySelectorAll("[data-pick]").forEach((el) => {
      const field = el.dataset.pick;
      const value = el.value.trim();
      const match = (lists[field] || []).find((c) => c.name === value || c.id === value);
      d[field] = match ? match.id : value;
    });
    root.querySelectorAll("[data-b]").forEach((el) => (d[el.dataset.b] = el.checked));
    const radio = root.querySelector('input[name="card"]:checked');
    if (radio) d.card = radio.value;
  }

  _payload() {
    const d = this._draft;
    if (this.kind === "card") return ["card_save", { tag: this.item, name: d.name, user: d.user, active: d.active }];
    if (this.kind === "cardnew") return ["card_add", { card: d.typed.trim() || d.card, user: d.user, name: d.name, active: d.active }];
    const data = { ...d, id: this.item };
    if (d.kind === "button") {
      const types = this.settings.system.controls.choices.event_types[d.entity] || [];
      data.presses = types.length ? d.presses : Object.fromEntries(this._pressRows.filter(([p, pid]) => p.trim() && pid));
    }
    if (d.kind === "keypad") Object.assign(data, d.buttons);
    if (["generic_keypad", "mqtt_keypad"].includes(d.kind)) data.buttons = Object.fromEntries(this._btnRows.filter(([b, pid]) => b.trim() && pid).map(([b, pid]) => [b.trim(), pid]));
    return ["control_save", data];
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
      clearTimeout(this._timer);
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
    const body = this.kind === "control" ? this._controlForm() : this.kind === "card" ? this._cardForm() : this._cardNewForm();
    const canDelete = (this.kind === "control" && this.item) || this.kind === "card";
    const style = `textarea { font: inherit; box-sizing: border-box; width: 100%; padding: 7px 10px; border-radius: 6px; border: 1px solid var(--divider-color); background: var(--card-background-color); color: var(--primary-text-color); }
      .warn { border: 1px solid var(--warning-color, #ffa600); border-radius: 8px; padding: 8px 10px; margin: 8px 0; font-size: .9rem; }`;
    this.shadowRoot.innerHTML = `<style>${(window.HauswachtEditStyle || "") + style}</style><div class="sheet">${body}
      <div class="bar"><button class="b p" data-act="save" ${this._busy ? "disabled" : ""}>${ce(this._busy ? this._t("saving") : this._t("save"))}</button>
      <button class="b" data-act="cancel">${ce(this._t("cancel"))}</button>
      ${canDelete ? `<button class="b d" data-act="delete">${ce(this._sure ? this._t("delSure") : this._t("del"))}</button>` : ""}</div></div>`;
    this.shadowRoot.querySelector(".sheet").scrollTop = top;
    const help = this.kind === "control" ? this._draft.kind : this.kind === "card" ? "card" : "cardNew";
    window.HauswachtDocs?.decorate(this.shadowRoot, help, this._lang);
    const root = this.shadowRoot;
    this.onclick = (ev) => {
      if (ev.composedPath()[0] === this) this._close();
    };
    root.querySelector('[data-act="cancel"]').addEventListener("click", () => this._close());
    root.querySelector('[data-act="save"]').addEventListener("click", () => {
      this._collect();
      const [action, data] = this._payload();
      this._apply(action, data);
    });
    const del = root.querySelector('[data-act="delete"]');
    if (del) {
      del.addEventListener("click", () => {
        this._collect();
        if (!this._sure) {
          this._sure = true;
          this._render();
          return;
        }
        if (this.kind === "card") this._apply("card_save", { tag: this.item, delete: true });
        else this._apply("control_delete", { id: this.item });
      });
    }
    // Felder, die andere ein- oder ausblenden
    root.querySelectorAll('[data-f="kind"], [data-f="source"], [data-pick="entity"]').forEach((el) =>
      el.addEventListener("change", () => {
        const before = this._draft?.kind;
        this._collect();
        // Andere Art gewählt und noch keine Taste belegt: passende Vorschläge
        if (el.dataset.f === "kind" && before !== this._draft.kind && this._btnRows.every(([, pid]) => !pid)) {
          this._btnRows = this._defaultButtons(this._draft.kind);
          while (this._btnRows.length < 4) this._btnRows.push(["", ""]);
        }
        this._render();
      })
    );
  }

  _close() {
    clearTimeout(this._timer);
    this.dispatchEvent(new CustomEvent("hw-close", { bubbles: true, composed: true }));
  }
}

if (!customElements.get("hauswacht-control-editor")) {
  customElements.define("hauswacht-control-editor", HauswachtControlEditor);
}
