// Hauswacht – Einstellungsseite, Stufe 5: Personen (ADR 0011).
//
// Seitenblatt <hauswacht-person-editor>: Benutzer mit Rechten (für alle Bereiche gleich oder je
// Bereich), Gültigkeit, verknüpftem Home-Assistant-Konto, PIN und Bedrohungs-PIN.
// PINs werden nie angezeigt – nur „gesetzt“ oder „nicht gesetzt“. Karten anlernen und den
// Master-PIN gibt es weiter im Dialog.

const PT = {
  de: {
    titleNew: "Person anlegen",
    titleEdit: "Person bearbeiten",
    name: "Name",
    nameHint: "Heißt die Person wie ein Home-Assistant-Konto, wird sie damit verknüpft.",
    active: "Aktiv (darf bedienen)",
    rights: "Darf …",
    scopeAll: "In allen Bereichen gleich",
    scopePer: "Je Bereich unterschiedlich",
    right: { arm: "scharf schalten", disarm: "unscharf schalten", end_alarm: "Alarm beenden" },
    forceArm: "Darf am Keypad trotzdem scharf schalten (offene Melder überbrücken)",
    cardPin: "In der Alarmkarte PIN verlangen (z. B. Wandtablet, das immer angemeldet ist)",
    validFrom: "Gültig ab (leer = sofort)",
    validUntil: "Gültig bis (leer = unbegrenzt)",
    validHint: "Für Gäste oder Handwerker: außerhalb der Zeit wird die Person abgewiesen.",
    haUser: "Home-Assistant-Konto",
    haAuto: "– automatisch nach Name –",
    pinTitle: "PIN",
    pinSet: "PIN gesetzt",
    pinNone: "Kein PIN",
    duressSet: "Bedrohungs-PIN gesetzt",
    duressNone: "Keine Bedrohungs-PIN",
    newPin: "Neuer PIN (leer = nicht ändern)",
    removePin: "PIN entfernen",
    newDuress: "Neue Bedrohungs-PIN (leer = nicht ändern)",
    removeDuress: "Bedrohungs-PIN entfernen",
    duressHint: "Bedrohungs-PIN: schaltet normal unscharf und meldet still eine Bedrohung.",
    pinRules: "4 bis 8 Ziffern. Der PIN wird nie angezeigt, auch hier nicht.",
    cards: "Karten",
    cardsHint: "Karten anlernen, benennen oder deaktivieren: unten im selben Reiter unter „Karten, Anhänger und Schloss-Kennungen“.",
    save: "Speichern",
    saving: "Speichere …",
    cancel: "Abbrechen",
    del: "Löschen",
    delSure: "Wirklich löschen?",
    errors: {
      user_name_required: "Bitte einen Namen eingeben.",
      user_name_taken: "Diesen Namen gibt es schon.",
      invalid_pin: "PIN: 4 bis 8 Ziffern.",
      duress_equals_pin: "Die Bedrohungs-PIN muss sich vom PIN unterscheiden.",
      pin_is_action_code: "Diese Ziffern sind schon ein Aktions-Code.",
      pin_is_duress: "Dieser PIN ist schon Bedrohungs-PIN von: {c}",
      duress_conflict: "Diese Bedrohungs-PIN ist schon PIN oder Bedrohungs-PIN von: {c}",
      disarm_first: "Erst alle Bereiche unscharf schalten – dann lässt sich speichern.",
      changed_elsewhere: "Inzwischen wurde woanders etwas geändert. Die Seite lädt neu – bitte noch einmal.",
      failed: "Speichern fehlgeschlagen.",
    },
  },
  en: {
    titleNew: "Add person",
    titleEdit: "Edit person",
    name: "Name",
    nameHint: "If the person has the same name as a Home Assistant account, they are linked.",
    active: "Active (may operate)",
    rights: "May …",
    scopeAll: "Same in all areas",
    scopePer: "Different per area",
    right: { arm: "arm", disarm: "disarm", end_alarm: "end an alarm" },
    forceArm: "May arm anyway at the keypad (bypass open sensors)",
    cardPin: "Require PIN in the alarm card (e.g. a wall tablet that is always logged in)",
    validFrom: "Valid from (empty = now)",
    validUntil: "Valid until (empty = unlimited)",
    validHint: "For guests or tradespeople: outside this time the person is refused.",
    haUser: "Home Assistant account",
    haAuto: "– automatic by name –",
    pinTitle: "PIN",
    pinSet: "PIN set",
    pinNone: "No PIN",
    duressSet: "Duress PIN set",
    duressNone: "No duress PIN",
    newPin: "New PIN (empty = keep)",
    removePin: "Remove PIN",
    newDuress: "New duress PIN (empty = keep)",
    removeDuress: "Remove duress PIN",
    duressHint: "Duress PIN: disarms normally and silently reports a threat.",
    pinRules: "4 to 8 digits. The PIN is never shown, not even here.",
    cards: "Cards",
    cardsHint: "Learn, name or disable cards: further down in the same tab under “cards, tags and lock IDs”.",
    save: "Save",
    saving: "Saving …",
    cancel: "Cancel",
    del: "Delete",
    delSure: "Really delete?",
    errors: {
      user_name_required: "Please enter a name.",
      user_name_taken: "This name already exists.",
      invalid_pin: "PIN: 4 to 8 digits.",
      duress_equals_pin: "The duress PIN must differ from the PIN.",
      pin_is_action_code: "These digits are already an action code.",
      pin_is_duress: "This PIN is already the duress PIN of: {c}",
      duress_conflict: "This duress PIN is already a PIN or duress PIN of: {c}",
      disarm_first: "Disarm all areas first – then saving works.",
      changed_elsewhere: "Something was changed elsewhere in the meantime. The page reloads – please try again.",
      failed: "Saving failed.",
    },
  },
};

const pe2 = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

class HauswachtPersonEditor extends HTMLElement {
  // open({hass, settings, person}) – person: ID oder null (neu)
  open(options) {
    Object.assign(this, options);
    const people = this.settings.people;
    const base = this.person ? people.users.find((u) => u.id === this.person) : null;
    const allRights = Object.fromEntries(people.areas.map((a) => [a.id, [...people.rights]]));
    this._draft = base
      ? JSON.parse(JSON.stringify(base))
      : {
          name: "", active: true, can_arm: true, can_disarm: true, can_end_alarm: true, can_force_arm: true,
          card_pin: false, ha_user: null, valid_from: "", valid_until: "", rights: "all", area_rights: allRights,
          has_pin: false, has_duress: false, cards: 0,
        };
    Object.assign(this._draft, { new_pin: "", new_duress_pin: "", remove_pin: false, remove_duress_pin: false });
    this._errors = {};
    this._details = {};
    this._busy = false;
    this._sure = false;
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this._render();
  }

  get _lang() {
    return (this.hass?.language || "en").startsWith("de") ? "de" : "en";
  }

  _t(key) {
    return PT[this._lang][key] ?? PT.en[key] ?? key;
  }

  _err(key) {
    const code = this._errors[key];
    if (!code) return "";
    const text = (this._t("errors")[code] || code).replace("{c}", this._details.conflict || "");
    return `<div class="err">${pe2(text)}</div>`;
  }

  _chk(attr, checked, label) {
    return `<div class="chk"><input type="checkbox" ${attr} ${checked ? "checked" : ""}><span>${pe2(label)}</span></div>`;
  }

  _form() {
    const d = this._draft;
    const people = this.settings.people;
    const taken = new Set(people.users.filter((u) => u.id !== this.person).map((u) => u.name.toLowerCase()));
    const names = people.ha_users.filter((u) => !taken.has(u.name.toLowerCase()));
    const haOptions = [`<option value="">${pe2(this._t("haAuto"))}</option>`]
      .concat(people.ha_users.map((u) => `<option value="${pe2(u.id)}" ${u.id === d.ha_user ? "selected" : ""}>${pe2(u.name)}</option>`))
      .join("");
    const rightsAll = people.rights
      .map((r) => this._chk(`data-b="can_${r}"`, d[`can_${r}`], this._t("right")[r]))
      .join("");
    const perArea = people.areas
      .map((a) => `<div class="box"><b>${pe2(a.name)}</b>${people.rights.map((r) => this._chk(`data-ar="${pe2(a.id)}" data-v="${r}"`, (d.area_rights[a.id] || []).includes(r), this._t("right")[r])).join("")}</div>`)
      .join("");
    const scope = people.multi_area
      ? `<div class="chk"><input type="radio" name="scope" value="all" ${d.rights === "all" ? "checked" : ""}><span>${pe2(this._t("scopeAll"))}</span></div>
         <div class="chk"><input type="radio" name="scope" value="per_area" ${d.rights === "per_area" ? "checked" : ""}><span>${pe2(this._t("scopePer"))}</span></div>`
      : "";
    const pinState = [
      d.has_pin ? this._t("pinSet") : this._t("pinNone"),
      d.has_duress ? this._t("duressSet") : this._t("duressNone"),
    ].join(" · ");
    return `
      <h2>${pe2(this.person ? this._t("titleEdit") : this._t("titleNew"))}</h2>
      <label>${pe2(this._t("name"))}</label><input data-f="name" list="hw-ha-users" value="${pe2(d.name)}">
      <datalist id="hw-ha-users">${names.map((u) => `<option value="${pe2(u.name)}"></option>`).join("")}</datalist>
      <div class="muted">${pe2(this._t("nameHint"))}</div>${this._err("name")}
      ${this._chk('data-b="active"', d.active, this._t("active"))}
      <label>${pe2(this._t("rights"))}</label>${scope}
      ${d.rights === "per_area" && people.multi_area ? perArea : rightsAll}
      ${this._chk('data-b="can_force_arm"', d.can_force_arm, this._t("forceArm"))}
      ${this._chk('data-b="card_pin"', d.card_pin, this._t("cardPin"))}
      <div class="inline"><div><label>${pe2(this._t("validFrom"))}</label><input type="datetime-local" data-f="valid_from" value="${pe2(d.valid_from)}"></div>
        <div><label>${pe2(this._t("validUntil"))}</label><input type="datetime-local" data-f="valid_until" value="${pe2(d.valid_until)}"></div></div>
      <div class="muted">${pe2(this._t("validHint"))}</div>
      <label>${pe2(this._t("haUser"))}</label><select data-f="ha_user">${haOptions}</select>
      <div class="box"><b>${pe2(this._t("pinTitle"))}</b> <span class="muted">${pe2(pinState)}</span>
        <div class="muted">${pe2(this._t("pinRules"))}</div>
        <label>${pe2(this._t("newPin"))}</label><input type="password" inputmode="numeric" autocomplete="new-password" data-f="new_pin" value="${pe2(d.new_pin)}">${this._err("new_pin")}
        ${d.has_pin ? this._chk('data-b="remove_pin"', d.remove_pin, this._t("removePin")) : ""}
        <label>${pe2(this._t("newDuress"))}</label><input type="password" inputmode="numeric" autocomplete="new-password" data-f="new_duress_pin" value="${pe2(d.new_duress_pin)}">${this._err("new_duress_pin")}
        ${d.has_duress ? this._chk('data-b="remove_duress_pin"', d.remove_duress_pin, this._t("removeDuress")) : ""}
        <div class="muted">${pe2(this._t("duressHint"))}</div></div>
      <div class="box"><b>${pe2(this._t("cards"))}</b> <span class="muted">${pe2(d.cards)}</span><div class="muted">${pe2(this._t("cardsHint"))}</div></div>
      ${this._err("base")}`;
  }

  _collect() {
    const root = this.shadowRoot;
    const d = this._draft;
    root.querySelectorAll("[data-f]").forEach((el) => (d[el.dataset.f] = el.value));
    d.ha_user = d.ha_user || null;
    root.querySelectorAll("[data-b]").forEach((el) => (d[el.dataset.b] = el.checked));
    const scope = root.querySelector('input[name="scope"]:checked');
    if (scope) d.rights = scope.value;
    if (root.querySelector("[data-ar]")) {
      for (const area of this.settings.people.areas) {
        d.area_rights[area.id] = [...root.querySelectorAll(`[data-ar="${area.id}"]`)].filter((el) => el.checked).map((el) => el.dataset.v);
      }
    }
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
  }

  _render() {
    const top = this.shadowRoot.querySelector(".sheet")?.scrollTop || 0;
    this.shadowRoot.innerHTML = `<style>${window.HauswachtEditStyle || ""}</style><div class="sheet">${this._form()}
      <div class="bar"><button class="b p" data-act="save" ${this._busy ? "disabled" : ""}>${pe2(this._busy ? this._t("saving") : this._t("save"))}</button>
      <button class="b" data-act="cancel">${pe2(this._t("cancel"))}</button>
      ${this.person ? `<button class="b d" data-act="delete">${pe2(this._sure ? this._t("delSure") : this._t("del"))}</button>` : ""}</div></div>`;
    this.shadowRoot.querySelector(".sheet").scrollTop = top;
    window.HauswachtDocs?.decorate(this.shadowRoot, "users", this._lang);
    const root = this.shadowRoot;
    this.onclick = (ev) => {
      if (ev.composedPath()[0] === this) this._close();
    };
    root.querySelector('[data-act="cancel"]').addEventListener("click", () => this._close());
    root.querySelector('[data-act="save"]').addEventListener("click", () => {
      this._collect();
      const { has_pin, has_duress, cards, ...data } = this._draft;
      this._apply("user_save", { ...data, id: this.person });
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
        this._apply("user_delete", { id: this.person });
      });
    }
    root.querySelectorAll('input[name="scope"]').forEach((el) =>
      el.addEventListener("change", () => {
        this._collect();
        this._render();
      })
    );
  }

  _close() {
    this.dispatchEvent(new CustomEvent("hw-close", { bubbles: true, composed: true }));
  }
}

if (!customElements.get("hauswacht-person-editor")) {
  customElements.define("hauswacht-person-editor", HauswachtPersonEditor);
}
