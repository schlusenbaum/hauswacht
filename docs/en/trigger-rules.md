# Trigger rules

[Deutsch](../ausloeseregeln.md) | **English**

**Alarm triggering → Trigger rules.** A trigger rule only triggers on a **sequence** of sensors –
e.g. "door, then basement". Trigger rules stand on their own; in the alarm profile you choose
under **Trigger rules** which ones apply. The same rule can be part of several profiles.

What for? At night, not every door should cause an instant alarm (someone briefly steps out),
but "door open and then motion in the basement" should. Sensors that trigger **alone** in the
profile need no rule.

## Structure

```
Step 1 fulfilled ──(time of step 1)──▶ Step 2 fulfilled ──(time of step 2)──▶ … ──▶ Alarm
```

- A trigger rule consists of **steps** that have to happen **one after another**. Step 2 only
  counts once step 1 is fulfilled – and only within the time set for step 1. Sensors of step 2
  that trigger **before** step 1 do not count. This creates the order.
- In each step you choose sensors (sensors and/or sensor groups – a sensor group means "any
  sensor of the sensor group") and decide when **this step** is fulfilled. This setting applies
  to this step only:

| This step is fulfilled when … | Example with "front door" + "back door" |
|---|---|
| **one of them triggers** (OR) | one of the two doors opens |
| **all of them trigger**, any order (AND) | both doors open, no matter which first |
| **at least N different ones** trigger | e.g. at least 2 of 4 basement sensors |

- **Time until the next step:** from the moment the step is fulfilled, the next step has this
  much time. If it runs out, everything expires; the next step 1 starts from scratch. Every new
  triggering of a step-1 sensor restarts the time.
- What may happen in **any order** belongs into **one** step with "all of them"; a **fixed
  order** means **several** steps:

| Wish | How to set it |
|---|---|
| first door, then basement | Step 1: door · Step 2: basement |
| door and basement, any order | Step 1: door + basement, "all of them" |
| one of the doors, then basement **and** office (no matter which first) | Step 1: both doors, "one of them" · Step 2: basement + office, "all of them" |

## Creating with the wizard

Name and result → step 1 → overview with "Add another step", "Edit a step", "Remove last step",
"Done – save" (up to 10 steps). Above each step and in the overview, the trigger rule is shown
as a sentence, e.g. "one of front door / back door, then within 120 s sensor group Basement →
entry delay, then alarm". It is only saved with "Done – save"; problems are shown in the
overview.

Result of a fulfilled trigger rule: **alarm immediately**, **entry delay, then alarm** or (in
YAML mode) **notification only** (time from the alarm profile – e.g. so that someone who comes
home and goes straight to the basement can still disarm).

## Example

Profile "Night" – no sensor group triggers alone, only these rules:

| Trigger rule | Steps | Result |
|---|---|---|
| Door, then basement | front door → (120 s) → basement sensors | entry delay |
| Window, then basement | window → (60 s) → basement sensors | alarm immediately |

| Sequence | Result |
|---|---|
| door open, then upstairs | no alarm |
| later into the basement (two sensors react) | no alarm |
| door open, then basement | entry delay, then alarm |
| window open (airing) | no alarm |
| window open, then basement | alarm |
| first basement, then window open | no alarm – the order counts |

## Good to know

- **Trigger rules are combined with OR.** A trigger rule can only cause an alarm, never prevent
  the alarm of another trigger rule. If two trigger rules trigger at the same time, the stricter
  result applies (alarm immediately).
- **The same sensor does not count twice:** "at least 2 different ones" means two different
  sensors; a sensor may not be in two consecutive steps.
- **Arming:** sensors that only appear in trigger rules of the profile do not prevent arming.
  An open window only counts once it closes and opens again – if it is closed later, the next
  opening starts the trigger rule as usual. If such a sensor is open when arming, you get a
  **hint** (notification "Hint when arming", on by default, and a message in Home Assistant):
  until it is closed it is a gap, e.g. someone can climb in through the open window without
  triggering step 1. The attribute `open_rule_sensors` of the alarm panel shows which ones they
  currently are.
- **Check when saving:** trigger rules that can never trigger cannot be saved. Hints appear if a
  trigger rule has no effect in a profile – for example because its first sensor already
  triggers alone there, or because a shorter trigger rule always triggers first.
- **Consider the weak spot deliberately:** whoever triggers no further step stays unnoticed
  (door open, then only upstairs). Remedy: more sensors in the later steps.
- Tampering is always reported; fire lock, test mode and siren enabling apply to every trigger
  rule. In the test card you see how far each trigger rule of the active profile has got.
- Hauswacht reports incomplete trigger rules on request: events "Unconfirmed trigger" and
  "Sensor often triggers alone" under [Notifications](notifications.md) (both off by default).
- From older versions: the group option "second sensor confirms" (0.18.0) was converted
  automatically to the trigger rule "Confirmation &lt;sensor group&gt;".

## Exception "Not if before …"

In the overview of the wizard: **"Not if before … (exception)"**. The trigger rule does not
apply if one of the selected sensors triggered within the given time **before step 1**.
Example: "Window, then basement" with the exception "hallway motion sensor, 300 s" – whoever was
already moving around inside and then opens a window triggers nothing. The exception applies
**only to this trigger rule**. The test card shows "blocked by exception · 4:10".

## Expert mode (YAML)

**Trigger rules → "New trigger rule as YAML"**, or **"Edit as YAML"** in the overview. Trigger
rules with nesting or conditions open the YAML editor directly when edited. When saving,
Hauswacht checks the rule and names errors with their location.

```yaml
name: Entry through the window
result: alarm                 # alarm | entry_delay | notify (notification only)
steps:
  - any: [group: Windows]     # one of them
    within: 60                # time until the next step
  - any:                      # basement OR (hallway AND office)
      - group: Basement
      - all: [sensor: binary_sensor.motion_hallway, sensor: binary_sensor.door_office]
unless:                       # not if this happened in the 300 s before step 1
  any: [group: Hallway]
  before: 300
conditions:                   # only if all are met
  - time: {after: "22:00", before: "06:00"}
  - person: {entity: person.niklas, in: not_home}
```

| Building block | Meaning |
|---|---|
| `sensor: binary_sensor.x` | this sensor |
| `group: Basement` | stands for **the individual sensors** of the sensor group: `any` = any one, `all` = all, `count` = N different ones |
| `any: [...]` / `all: [...]` / `count: N` + `of: [...]` | one · all (any order) · at least N – nested as you like |
| `within: 120` | time until the next step (seconds) |
| `result:` | `alarm`, `entry_delay` (entry delay, then alarm) or `notify` (notification only) |
| `unless:` + `before:` | exception: not if the expression was fulfilled within this time before step 1 |
| `conditions:` | list; all must be met |

Conditions:

| Condition | Example |
|---|---|
| Time, weekdays | `time: {after: "22:00", before: "06:00", weekdays: [mon, tue, wed, thu, fri]}` (also across midnight) |
| Person in zone | `person: {entity: person.niklas, in: home}` – `home`, `not_home` or `zone.school` |
| State | `state: {entity: input_boolean.vacation, is: "on"}` (also a list: `is: [on, auto]`) |
| Numeric value | `numeric: {entity: sensor.temperature, above: 5, below: 30}` – optional `attribute: temperature` |
| Logic | `and: [...]`, `or: [...]`, `not: {...}` |

**Safe side:** if a condition cannot be evaluated (entity missing, unavailable, no number), it
counts as **met** – when in doubt, the rule triggers. Conditions are only checked once all steps
have happened; a failed sensor therefore never triggers anything itself, it can only no longer
prevent an alarm.

If a condition should allow **no** alarm when in doubt, add `if_unknown: not_met`:

```yaml
conditions:
  - numeric: {entity: sensor.temperature_living_room, below: 30}
    if_unknown: not_met      # sensor failed = condition not met = no alarm
```

`if_unknown` works on every condition, also on `and`/`or`/`not`. Careful: with `not_met`, a
failed sensor silences the rule. Conditions, exceptions and result only affect their own trigger
rule; other trigger rules and sensor groups that trigger alone stay unaffected.
