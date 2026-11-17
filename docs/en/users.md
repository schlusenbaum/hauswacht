# Users, PINs and lockout

[Deutsch](../benutzer.md) | **English**

## The most important thing first

> ⚠️ **Either everyone gets a PIN – or nobody.**
> As soon as **one** PIN exists (including the master PIN), the alarm panel and Alexa require a
> PIN for disarming – **from everyone**. Whoever has none can then only disarm via dashboard
> buttons (if "Allow dashboard buttons despite PIN" is on under PIN rules), the push button, their
> RFID card or the card ["Hauswacht Alarm"](dashboard.md#no-forced-pin). A shared family PIN is
> allowed. If a **Hauswacht user** has no PIN, Home Assistant shows the hint "Not every user has a
> PIN" under **Settings → Repairs**. Home Assistant accounts without a Hauswacht user – e.g. for
> Grafana, MQTT or a wall tablet – do not count.
>
> **With a master PIN**, users without an own PIN can still disarm at the panel – with the master
> PIN. The hint is then called "Users without an own PIN" and names them; the logbook shows
> "Master-PIN" instead of their name. If this is intended, you can ignore the hint in Repairs.

**RFID cards are independent of the PIN:** cards do not make the alarm panel require a PIN. So
without any PINs, everyone switches on the dashboard without a PIN, and still with a card at the
keypad.

| Goal | How to set it up |
|---|---|
| Dashboard without PIN, keypad with card | no PINs, cards with the users |
| Keypad also with a number code, dashboard still without PIN | PINs or master PIN, on the dashboard the card ["Hauswacht Alarm"](dashboard.md#card-hauswacht-alarm) – it switches without PIN for linked accounts |
| … and a wall tablet only with PIN | give the tablet its own Home Assistant account without a Hauswacht user (or "Require PIN in the alarm card" for the user) |
| Everything with PIN | a PIN for every person (shared allowed) |

## Users

**System settings → Users and PINs.** The menu has:

| Menu item | What for |
|---|---|
| Add / edit / delete user | name, rights, validity, Home Assistant account |
| **Cards and tags** | all cards, fingers and lock IDs: learn, name, assign to a user, disable, delete – see [Control devices → Learning cards](control-devices.md#learning-cards) |
| **PINs** | set, change, remove PIN and duress PIN per user – see [PINs](#pins) |
| PIN rules | master PIN, PIN when arming … – see [PIN rules](#pin-rules) |

Every person gets a user:

| Field | Meaning |
|---|---|
| Name | suggestions from the Home Assistant users, or free (e.g. "Cleaner"). Shown as "changed by" on the alarm panel, in the logbook and in push messages |
| Active | off = credentials blocked without deleting them |
| May arm / May disarm / May end alarm | rights (with "All areas alike") |
| May arm anyway at the keypad | bypass open sensors with a second key press, see [Arm anyway at the keypad](control-devices.md#arm-anyway-at-the-keypad). Default on – switch off e.g. for children or guests |
| Rights apply to | only with several areas, see [Rights](#rights) |
| Home Assistant account | links the alarm card, push button, dashboard buttons and NFC stickers to this user. Set automatically if a Home Assistant user was chosen as the name |
| Require PIN in the alarm card | for this user's Home Assistant account in the card ["Hauswacht Alarm"](dashboard.md#no-forced-pin), e.g. for a tablet account. Default off |
| Valid from / until | for guests: outside this time, the credentials are blocked |

At the top, the user dialog shows the status, e.g. "2 cards · PIN set". You change cards and PINs
themselves in their own lists. If a user is deleted, their cards are deleted too.

- **Shared PIN:** several users may have the same PIN ("shared PIN (Christian, Petra)"). An
  action is allowed if **at least one** of these users may do it.
- **Blocked or expired credential:** rejected like a wrong one; in addition a system message
  "blocked credential" is sent.
- **Without PIN** (push button, dashboard buttons, NFC sticker): if the Home Assistant account is
  linked to a user, that user's name and rights apply; otherwise the account name is shown and
  everything is allowed (NFC stickers always require a linked user).
- The automation (time, presence) appears as "Automation".

## PINs

**Users and PINs → PINs.** The list shows who has a PIN or duress PIN and when the PIN last
switched:

```
Christian – PIN · duress PIN · last 07:10
Anna – PIN · last 15.11.2026
Guest – no PIN
```

Tap a user: **New PIN** (4–8 digits), **Remove PIN**, **New duress PIN**, **Remove duress PIN**.
Empty fields change nothing.

PINs are stored as a hash only – Hauswacht can never show them, not here either. Whoever has
forgotten their PIN gets a new one.

**Example:** Petra is to get a PIN. Users and PINs → PINs → "Petra – no PIN" → New PIN `2580` →
submit. The list now shows "Petra – PIN · never used".

## Rights

Without further areas, the three checkboxes apply. With several areas, choose **"Rights apply
to"** for the user:

- **All areas alike:** the checkboxes apply everywhere.
- **Per area:** after saving, a page follows where you choose for each area: arm, disarm, end
  alarm. An area without a selection is blocked for the user.

A keypad for all areas only disarms the areas in which the user may do so.

## PIN rules

**System settings → Users and PINs → PIN rules:**

| Setting | Meaning |
|---|---|
| **Master PIN** | a PIN without its own user, with all rights in all areas (e.g. for Alexa or as a family code at the keypad). Appears as "Master PIN" in the user list; the logbook then only says "Master PIN", not who it was |
| **Require PIN to arm** | default off |
| **End alarm without PIN** | button "End alarm" also with a PIN set (default off) |
| **Alarm card: require PIN for Home Assistant accounts without a Hauswacht user** | default on. Only applies in the card ["Hauswacht Alarm"](dashboard.md#no-forced-pin); linked accounts switch there without PIN |
| **Allow dashboard buttons despite PIN** | "Disarm now", "End alarm" and the arm buttons keep working. The PIN then only protects the alarm panel, keypads and voice assistants – only logged-in Home Assistant users get to the buttons anyway |

- Whether a master PIN is set up is shown at the top of the menu "Users and PINs" and in the PIN
  rules: "Master PIN: ✅ set up" or "– none". The PIN itself is never shown.
- PINs have 4–8 digits and are stored as a hash only.
- Without a PIN, the system must **not** be exposed to voice assistants.
- A PIN from versions before 0.16.1 became the user "Main user" during the update.

## Lockout after wrong entries

Protection against trying out codes. The rules are built in (not configurable):

| Wrong entries in a row | Consequence |
| --- | --- |
| 1–2 | nothing (only counted) |
| 3–4 | system message to the configured recipients, again on every further failed attempt |
| 5 | entry **locked for 1 minute** |
| 6 | 2 minutes |
| 7 | 4 minutes |
| 8 | 8 minutes |
| from 9 | **15 minutes** (maximum) |

Important to know:

- **Shared for everything:** one counter for all areas and all ways of entry – alarm panel on the
  dashboard, keypads, RFID readers, Alexa. Whoever mistypes at the keypad also locks the alarm
  panel.
- **During the lockout every entry is rejected** – even a correct PIN or a correct card. The
  keypad shows "invalid", the alarm panel "Too many wrong PIN entries. Please wait … seconds."
- **The counter is reset** by
  - a correct entry (PIN or card) outside the lockout,
  - the button **"Reset failed attempts"** in the card "Hauswacht Test" (shows the number;
    administrators only) or the action `hauswacht.reset_code_lock` (administrators only),
  - a restart of Home Assistant or a reload of Hauswacht,
  - **time:** failed attempts expire **24 hours after the last failed attempt**. Two wrong entries
    today and three the day after tomorrow therefore cause no lockout. The period runs from the
    last failed attempt – not at midnight, otherwise you could make twice as many attempts just
    before and just after midnight. A running lockout ends after its duration regardless.
- **What does not count:** unknown cards (codes that cannot be a PIN – so cards can be learned)
  and entries without a code (e.g. a keypad key without PIN/card).
- **What is reported separately:** a blocked or expired PIN or card (e.g. a guest outside their
  validity) – system message "blocked credential"; it also counts as a failed attempt.
- **If you are locked out yourself and the alarm is running:** disarming still works via the
  button "Disarm now" on the dashboard or the push button, as long as "Allow dashboard buttons
  despite PIN" is on or no PIN exists. The lockout only affects code entry.
- **Show the state:** attributes `code_failures` (number) and `code_locked_until` (end of the
  lockout) of the alarm panel; every failed attempt fires the event `hauswacht_event` with
  `type: InvalidCode`.
- **Worked example:** a 4-digit PIN has 10,000 possibilities. Someone trying continuously stays
  at a 15-minute lockout per attempt and would need several weeks on average. Someone who always
  waits a day to let the counter expire only manages 4 attempts per day without lockout – so
  years. And from the 3rd attempt on, a message is sent every time.

## Duress PIN

Whoever is forced to switch off the system enters their **duress PIN**:

- The system switches **completely normally**; the alarm panel, logbook and dashboard look
  inconspicuous ("changed by Petra").
- Secretly, an emergency call with the highest priority goes to the **duress alarm recipients**
  (Notifications). No siren, no visible message, never via speakers.
- The duress PIN also works if the user would otherwise not have the right, and also at the
  keypad.
- It must not equal any normal PIN or any other duress PIN; this is checked when saving.
- **Be sure to add recipients** – without recipients it has no effect apart from the normal
  switching.
