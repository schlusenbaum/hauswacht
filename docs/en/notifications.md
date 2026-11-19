# Notifications and speech

[Deutsch](../benachrichtigungen.md) | **English**

## Recipients

**Notifications** with the items "Recipients and events", "Custom texts for push messages" and
two items for [speech](#speech-speakers).

- **General recipients:** notify services, e.g. `mobile_app_…` of the Home Assistant app, and
  **notification entities** (`notify.…`), e.g. from WhatsApp, Telegram or e-mail integrations.
  They get every message for which no own recipients are set for the event.
- **Entities only get title and text** ("– text only" in the selection): no buttons, no breaking
  through Do Not Disturb. Good as an additional channel (e.g. a family group); the Home Assistant
  app stays the actual alarm signal. Speakers (announce/speak) do not appear here, they are under
  "Speech"; the duress alarm never goes to speakers.
- **Per event** (expandable sections): on/off and own recipients.

**Language:** notifications, push buttons, announcements and reports come in the language of Home
Assistant – German if Home Assistant is set to German, otherwise English. Custom texts are sent
as entered.

## Events

| Event | Default | Recipients |
|---|---|---|
| Alarm | on, **critical** | first "Notify (alarm)" of the profile |
| Door opened (entry delay) | only with push button | first those of the profile |
| Alarm ended | on | first those of the profile |
| Armed / Disarmed | off | event, otherwise general |
| Arming rejected | on, with buttons | event, otherwise general |
| Automation (armed/disarmed automatically) | on | event, otherwise general |
| Fault (sensor lost, tampering, infrastructure) | on | event, otherwise general |
| System (restart, PIN locked, wrong PIN) | on | event, otherwise general |
| Reminder "everyone away" | on, once set up | event, otherwise general |
| [Note on arming](#note-on-arming) (armed, but not everything monitored) | on | event, otherwise general |
| Always-active sensor (disarmed, without siren) | on, **critical** | event, otherwise general |
| Trigger rule "notification only" fulfilled | on | event, otherwise general |
| Unconfirmed trigger (trigger rule only partly fulfilled, no alarm) | off | event, otherwise general |
| Sensor often triggers alone (started a trigger rule 3× in one hour) | off | event, otherwise general |

- **Duress alarm** is not an event that can be switched off: always on, own recipients ("Duress
  alarm recipients").
- **Critical alerts:** alarm and duress break through Do Not Disturb (option "Alarm and duress as
  critical alerts", default on). iPhone: critical alert – allow it in the app the first time.
  Android: channel `alarm_stream`, sounds even in silent mode. All other messages go out with
  high priority, but normally.
- **Old messages tidy themselves up** (Home Assistant app): the message on arming (or the note)
  and the one on disarming **replace each other** – the phone always shows only the newest. If
  you get no message on disarming, the armed message simply disappears. Alarm messages disappear
  on disarming, "Arming not possible" as soon as arming worked. Notification entities (e.g.
  Telegram, WhatsApp) cannot withdraw messages.
- In test mode, notifications are only sent if "Also notify in test mode" is on. The title then
  starts with "[TEST]".

## Custom texts and placeholders

**Notifications → Custom texts for push messages:** write title and text per event yourself;
the field first shows **Hauswacht's text** as a template – with placeholders instead of values,
e.g. `Profile {profile} armed ({who}).` Just change it and save. If the template stays
**unchanged** (or the field empty), nothing is saved and Hauswacht sends its own text. Where that
text differs depending on the situation (e.g. faults), the template is `{text}` – that is
Hauswacht's complete text.

> **Good to know:** a custom text replaces Hauswacht's whole text. On an alarm, Hauswacht
> otherwise also adds e.g. which sirens are running. To keep that, include `{text}`, e.g.
> `{text} Please call the neighbours.`

Back to Hauswacht's text: on the [settings page](settings-page.md#editing-notifications) the
button **"↺ Default text"**, in the dialog empty the field. The same placeholders apply to
speech:

| Placeholder | German | Content |
|---|---|---|
| `{area}` | `{bereich}` | area name (empty with only one area) |
| `{profile}` | `{profil}` | alarm profile |
| `{sensor}` | `{melder}` | triggering sensor with room |
| `{open}` | `{offen}` | open sensors |
| `{who}` | `{wer}` | who switched |
| `{seconds}` | `{sekunden}` | entry delay in seconds |
| `{time}` | `{uhrzeit}` | current time |
| `{rule}` | `{regel}` | trigger rule |
| `{reason}` | `{grund}` | reason, e.g. why arming failed |
| `{text}` | `{text}` | Hauswacht's default text (in the title: the default title) |

Both spellings always work, also mixed. The settings dialog names them in the language of Home
Assistant.

Example: `Burglary {area}: {sensor} ({profile}, {time})`. Unknown placeholders or bracket errors
cannot be saved; after saving, the menu shows a preview with example values. Missing values stay
empty. The buttons in push messages stay unchanged.

## Speech (speakers)

Hauswacht can announce events via speakers, e.g. **Echo devices** via the Home Assistant
integration "Alexa Devices". Any device with notification entities (`notify.…`) is suitable.

**Notifications → Speech – speakers, repeat, quiet hours:**

| Setting | Meaning |
|---|---|
| Speakers | devices that announce all enabled events by default |
| Repeat alarm announcement every | repeats the alarm announcement every N seconds (10–300) until the alarm has ended; 0 = only once |
| Quiet hours from–until | during this time, only events with "Also during quiet hours" |

**Notifications → Speech – events, mode and texts** (per event):

| Setting | Meaning |
|---|---|
| Speak | on/off |
| Mode | **Announcement** (with chime) or **Speak**; Hauswacht picks the matching entity on the device |
| Own speakers | instead of the default speakers |
| Also during quiet hours | |
| Text | own text with placeholders, empty = default text (the form shows the default text and a preview) |

On by default (once speakers are chosen): alarm, entry delay, arming rejected, always-active
sensor. Allowed during quiet hours by default: alarm, entry delay, always-active sensor.

- **Per alarm profile** there are "Additional speakers": they announce alarm, entry delay and
  "alarm ended" of this profile – instead of the default speakers. Because every profile belongs
  to an area, this lets you decide where an alarm in the garage is announced.
- With several areas, the area name comes before the default text ("Garage: Attention …").
- A **silent alarm** is never announced, the **duress alarm** never via speakers.
- **Test mode:** only announced with "Also notify in test mode", then with "Test." in front.
- If Do Not Disturb is on at the Echo, it may announce nothing. Speech complements push and siren,
  it does not replace them.

## Arming rejected: "Arm anyway" / "Try again"

If arming is rejected (e.g. window open), a notification comes with the reason and the buttons:

- **"Arm anyway"** – only if the profile may bypass open sensors after confirmation ("Open
  sensors when arming: Allow after confirmation"). Open sensors are bypassed until closed.
- **"Try again"** – checks once more (e.g. after the window has been closed). If it fails again,
  a new notification comes.

The buttons are valid for 15 minutes and once each, need a logged-in Home Assistant user with the
right "May arm", and only work if the system is still disarmed.

## Note on arming

As soon as a profile is armed but **not everything is monitored**, this message comes – whether
via keypad, card, push button or automation:

> Profile Night is armed (Christian, Keypad). Not monitored: Entrance: front door contact – open,
> bypassed until disarming; Basement window – unavailable, monitored again as soon as it reports.

Listed are:

| Gap | How long |
|---|---|
| **Open sensor, bypassed** ("arm anyway" or bypassed automatically) | until disarming |
| **Unavailable sensor**, accepted (after confirmation or automatically) | until it reports again – then it is monitored again |
| **Open sensor that only appears in trigger rules** | until it closes and opens again |

**Only one message:** if "Armed" is switched on, the gaps are simply part of that message
("Profile Night armed (Christian). Not monitored: …"). The separate note only comes if "Armed" is
off.

Plus an entry under notifications in Home Assistant and the event `ArmedWithGaps` (see
[reference](reference.md)). In custom texts: `{open}` (open sensors), `{reason}` (all gaps with
explanation), `{profile}`, `{who}`.

## Reminder "everyone away, system disarmed"

**Notifications → Reminder "everyone away":** persons, profile, delay.

If all selected persons are away and the system is disarmed, a reminder comes **once** after the
delay, with the button **"Arm now (profile)"**. Hauswacht switches **nothing itself** – the safe
alternative to automatic arming. Unknown location does not count as away. If someone comes home,
everything starts over. The button is valid for 2 hours.

## Push button "Disarm"

**Notifications → "Button "Disarm" / "End alarm" in notifications".**

If the option is on, the alarm recipients of the profile get:

- when an **entry door is opened** (entry delay running) a notification "Door opened" right away,
- on **alarm** the alarm message,

each with the button **"Disarm"** directly in the notification.

- Only works with the **Home Assistant app** (`notify.mobile_app_…`).
- The button only applies to the **current arming**. An old button from an earlier notification
  has no effect.
- Hauswacht checks that the button comes from a logged-in Home Assistant user, and then reports
  "Disarmed via the push button by …".
- **iPhone:** the button requires an unlocked device (Face ID or code). **Android:** the app does
  not know this lock. Whoever gets hold of the phone can press the button on the lock screen.
  Remedy: in Android, "Hide sensitive content on the lock screen" for the Home Assistant app.
- The button works without PIN – it replaces the PIN entry with the logged-in phone.
- After disarming, the notification is removed from the phones.
