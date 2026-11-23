"""Prüfhinweise: Hauswacht schaut die eigene Konfiguration kritisch an.

Rein und ohne Home Assistant: Eingabe ist die Anlagenübersicht (ein JSON-artiges Dict, siehe
``overview.py``), Ausgabe eine Liste von Hinweisen::

    {"code": "...", "key": "...", "severity": "warning" | "info", "important": bool,
     "text": "...", "where": "..."}

``important`` = auch als Reparatur-Hinweis in Home Assistant zeigen. Das bleibt bewusst wenigen
Fällen vorbehalten (Alarm erreicht niemanden, Bedrohungs-PIN oder stiller Notruf wirkungslos,
Melder lange ausgefallen), damit die Reparaturliste nicht zugemüllt wird.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

SIREN_TEST_MAX_DAYS = 183  # ein halbes Jahr
UNAVAILABLE_IMPORTANT_HOURS = 24
BATTERY_LOW = 10

TEXTS: Mapping[str, Mapping[str, tuple[str, str]]] = {
    # code: {lang: (Text, Wo ändern)}
    "test_mode": {
        "de": ("Der Testmodus ist an – im Ernstfall gibt es keine Sirenen.", "Testkarte"),
        "en": ("Test mode is on – no sirens in a real alarm.", "Test card"),
    },
    "sirens_locked": {
        "de": (
            "Profile nutzen Sirenen, aber die echte Sirenenansteuerung ist noch nicht freigegeben.",
            "Alarmgeber – Sirenen",
        ),
        "en": (
            "Profiles use sirens, but real siren control is not enabled yet.",
            "Alarm devices – sirens",
        ),
    },
    "profile_empty": {
        "de": ("Profil {name}: keine Meldergruppen und keine Auslöseregeln.", "Alarmprofile"),
        "en": ("Profile {name}: no sensor groups and no trigger rules.", "Alarm profiles"),
    },
    "profile_unheard": {
        "de": (
            "Profil {name}: keine Sirene und kein Empfänger – ein Alarm erreicht niemanden.",
            "Alarmprofile / Benachrichtigungen",
        ),
        "en": (
            "Profile {name}: no siren and no recipient – an alarm reaches nobody.",
            "Alarm profiles / notifications",
        ),
    },
    "profile_no_siren": {
        "de": ("Profil {name}: keine Sirene (nur Benachrichtigung).", "Alarmprofile"),
        "en": ("Profile {name}: no siren (notification only).", "Alarm profiles"),
    },
    "sensor_unused": {
        "de": (
            "{name} steht in einer Meldergruppe, ist aber in keinem Alarmprofil scharf.",
            "Alarmprofile",
        ),
        "en": ("{name} is in a sensor group but armed in no alarm profile.", "Alarm profiles"),
    },
    "sensor_unavailable": {
        "de": ("{name} ist nicht verfügbar{since}.", "Gerät prüfen"),
        "en": ("{name} is unavailable{since}.", "Check the device"),
    },
    "battery_low": {
        "de": ("{name}: Batterie {battery} %.", "Batterie wechseln"),
        "en": ("{name}: battery {battery} %.", "Replace the battery"),
    },
    "siren_no_tone": {
        "de": (
            "Sirene {name} kennt keinen der Einbruchtöne – sie bliebe bei einem Alarm stumm.",
            "Alarmgeber – Sirenen → Ton je Sirene",
        ),
        "en": (
            "Siren {name} knows none of the burglar tones – it would stay silent in an alarm.",
            "Alarm devices – sirens → Tone per siren",
        ),
    },
    "siren_fire_tone": {
        "de": (
            "Sirene {name}: Brandton {tone} ist für Einbruch freigegeben (Experten).",
            "Alarmgeber – Sirenen → Ton je Sirene",
        ),
        "en": (
            "Siren {name}: fire tone {tone} is released for burglar alarms (experts).",
            "Alarm devices – sirens → Tone per siren",
        ),
    },
    "siren_untested": {
        "de": ("Sirene {name} wurde noch nie getestet.", "Testkarte → Sirenentest"),
        "en": ("Siren {name} has never been tested.", "Test card → siren test"),
    },
    "siren_test_old": {
        "de": ("Sirene {name}: letzter Test vor {days} Tagen.", "Testkarte → Sirenentest"),
        "en": ("Siren {name}: last test {days} days ago.", "Test card → siren test"),
    },
    "siren_not_heard": {
        "de": ("Sirene {name} wurde beim letzten Test nicht gehört.", "Sirene prüfen"),
        "en": ("Siren {name} was not heard in the last test.", "Check the siren"),
    },
    "duress_no_targets": {
        "de": (
            "Ein Bedrohungs-PIN ist eingerichtet, aber es gibt keine Empfänger – er ist "
            "wirkungslos.",
            "Benachrichtigungen → Bedrohungsalarm",
        ),
        "en": (
            "A duress PIN is set up but has no recipients – it has no effect.",
            "Notifications → duress alarm",
        ),
    },
    "user_expired": {
        "de": ("{name}: Gültigkeit abgelaufen – Benutzer noch nötig?", "Benutzer und PINs"),
        "en": ("{name}: validity expired – still needed?", "Users and PINs"),
    },
    "user_master_pin_only": {
        "de": (
            "{name} hat keinen eigenen PIN und schaltet am Bedienfeld mit dem Master-PIN – im "
            "Logbuch steht dann „Master-PIN“ statt {name}.",
            "Benutzer und PINs → PINs",
        ),
        "en": (
            "{name} has no own PIN and uses the master PIN at the panel – the logbook then shows "
            "“Master-PIN” instead of {name}.",
            "Users and PINs → PINs",
        ),
    },
    "user_without_pin": {
        "de": (
            "{name} hat keinen PIN, andere schon – das Bedienfeld verlangt auch von {name} einen.",
            "Benutzer und PINs → PINs",
        ),
        "en": (
            "{name} has no PIN but others do – the panel asks {name} for one too.",
            "Users and PINs → PINs",
        ),
    },
    "silence_off": {
        "de": (
            "Funkstille-Erkennung ist aus{advice}.",
            "Systemeinstellungen → Funkstille von Sensoren",
        ),
        "en": ("Silence detection is off{advice}.", "System settings → sensor silence"),
    },
    "silence_tight_sensor": {
        "de": (
            "„{name}“: eigene Funkstille-Grenze {hours} h, die Beobachtung empfiehlt für diesen "
            "Melder {advice} h – sonst drohen Fehlmeldungen „ausgefallen“.",
            "Einstellungsseite → Melder (oder Systemeinstellungen → Funkstille von Sensoren)",
        ),
        "en": (
            "“{name}”: own silence limit {hours} h, observation recommends {advice} h for this "
            "sensor – expect false 'unavailable' reports.",
            "Settings page → sensors (or system settings → sensor silence)",
        ),
    },
    "silence_tight": {
        "de": (
            "Funkstille-Grenze {hours} h, die Beobachtung empfiehlt {advice} h – sonst drohen "
            "Fehlmeldungen „ausgefallen“.",
            "Systemeinstellungen → Funkstille von Sensoren",
        ),
        "en": (
            "Silence limit {hours} h, observation recommends {advice} h – expect false "
            "'unavailable' reports.",
            "System settings → sensor silence",
        ),
    },
    "no_infrastructure": {
        "de": (
            "Kein Funknetz/Gateway überwacht – fällt z. B. Zigbee2MQTT aus, merkt Hauswacht das "
            "erst über die Funkstille.",
            "Systemeinstellungen → Funknetz und Gateways",
        ),
        "en": (
            "No radio network/gateway monitored – a failing Zigbee2MQTT is only noticed via "
            "silence.",
            "System settings → networks and gateways",
        ),
    },
    "infrastructure_fault": {
        "de": ("Störung: {name}.", "Gateway prüfen"),
        "en": ("Fault: {name}.", "Check the gateway"),
    },
    "guest_mode": {
        "de": (
            "Gastmodus ist an ({area}, {until}) – die Profil-Automatik schaltet nicht scharf, "
            "Erinnerungen ruhen.",
            "Alarm-Karte / Schalter Gastmodus",
        ),
        "en": (
            "Guest mode is on ({area}, {until}) – the profile automation does not arm, reminders "
            "are paused.",
            "Alarm card / guest mode switch",
        ),
    },
    "action_code_profile_missing": {
        "de": (
            "Aktions-Code {name}: das Alarmprofil gibt es nicht mehr – der Code schaltet nichts "
            "scharf.",
            "Bedienteile – Aktions-Codes",
        ),
        "en": (
            "Action code {name}: the alarm profile no longer exists – the code arms nothing.",
            "Control devices – action codes",
        ),
    },
    "action_code_keypad_missing": {
        "de": (
            "Aktions-Code {name}: das Keypad gibt es nicht mehr – der Code wirkt nirgends.",
            "Bedienteile – Aktions-Codes",
        ),
        "en": (
            "Action code {name}: the keypad no longer exists – the code works nowhere.",
            "Control devices – action codes",
        ),
    },
    "silent_emergency_no_targets": {
        "de": (
            "Aktions-Code {name} löst einen stillen Notruf aus, aber für „Alarm“ ist kein "
            "Empfänger eingetragen – der Notruf erreicht niemanden.",
            "Benachrichtigungen",
        ),
        "en": (
            "Action code {name} triggers a silent emergency, but “Alarm” has no recipient – "
            "the emergency reaches nobody.",
            "Notifications",
        ),
    },
    "away_no_fix": {
        "de": (
            "{name} kann nicht als weg erkannt werden – keine Ortung mit Koordinaten. "
            "„Scharf, wenn alle weg“ wartet dann für immer, „Bei Rückkehr“ löst nie aus. Tipp: "
            "in der Companion App den Standort auf „Immer“ stellen oder einen GPS-Tracker als "
            "Signal eintragen.",
            "Systemeinstellungen → Anwesenheit und Heimkehr-Beobachtung",
        ),
        "en": (
            "{name} cannot be detected as away – no location with coordinates. “Arm when all "
            "away” then waits forever, “On return” never triggers. Tip: set the location in the "
            "Companion app to “Always” or add a GPS tracker as a signal.",
            "System settings → presence and homecoming observation",
        ),
    },
    "away_weak": {
        "de": (
            "{name}: „weg“ gilt auch mit Tür + Signal (unsicher). Öffnet jemand anderes die Tür, "
            "während {name}s Handy zufällig einschläft, gilt {name} fälschlich als weg – "
            "„Scharf, wenn alle weg“ kann dann scharf schalten, obwohl {name} zuhause ist.",
            "Systemeinstellungen → Anwesenheit und Heimkehr-Beobachtung",
        ),
        "en": (
            "{name}: “away” also counts with door + signal (uncertain). If someone else opens the "
            "door while {name}'s phone happens to fall asleep, {name} wrongly counts as away – "
            "“arm when all away” may then arm although {name} is home.",
            "System settings → presence and homecoming observation",
        ),
    },
    "leaving_ok": {
        "de": (
            "Heimkehr-Beobachtung: {name} – Rausgehen wird zuverlässig erkannt, empfohlene "
            "Wartezeit {minutes} min (aus {count}× Rausgehen).",
            "Systemeinstellungen → Anwesenheit und Heimkehr-Beobachtung",
        ),
        "en": (
            "Homecoming observation: {name} – leaving is detected reliably, recommended waiting "
            "time {minutes} min (from {count}× leaving).",
            "System settings → presence and homecoming observation",
        ),
    },
    "leaving_slow": {
        "de": (
            "Heimkehr-Beobachtung: Bei {name} merken die Signale das Rausgehen erst nach bis zu "
            "{needed} min – zu spät. Tipp: ein schnelleres Signal einrichten, z. B. den "
            "WLAN-Sensor der Companion App.",
            "Systemeinstellungen → Anwesenheit und Heimkehr-Beobachtung",
        ),
        "en": (
            "Homecoming observation: for {name} the signals notice leaving only after up to "
            "{needed} min – too late. Tip: set up a faster signal, e.g. the Wi-Fi sensor of the "
            "Companion app.",
            "System settings → presence and homecoming observation",
        ),
    },
    "leaving_pauses": {
        "de": (
            "Heimkehr-Beobachtung: Bei {name} haben alle Signale {pauses}× länger als {minutes} "
            "min geschwiegen, ohne dass eine Tür aufging – Rausgehen ist so nicht sicher "
            "erkennbar. Tipp: ein zweites Signal einrichten, z. B. die Companion App mit "
            "WLAN-Sensor.",
            "Systemeinstellungen → Anwesenheit und Heimkehr-Beobachtung",
        ),
        "en": (
            "Homecoming observation: for {name} all signals were silent {pauses}× for longer "
            "than {minutes} min without a door opening – leaving cannot be detected reliably. "
            "Tip: set up a second signal, e.g. the Companion app with its Wi-Fi sensor.",
            "System settings → presence and homecoming observation",
        ),
    },
    "rule_unused": {
        "de": ("Auslöseregel {name} wird in keinem Profil verwendet.", "Alarmprofile"),
        "en": ("Trigger rule {name} is used in no profile.", "Alarm profiles"),
    },
}


def _finding(
    code: str,
    language: str,
    *,
    severity: str = "info",
    important: bool = False,
    key: str = "",
    **values: Any,
) -> dict[str, Any]:
    text, where = TEXTS[code][language if language in ("de", "en") else "en"]
    return {
        "code": code,
        "key": key,
        "severity": severity,
        "important": important,
        "text": text.format(**values),
        "where": where,
    }


def _parse(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _hours_since(value: Any, now: datetime) -> float | None:
    parsed = _parse(value)
    return (now - parsed).total_seconds() / 3600 if parsed else None


def _system(overview: Mapping[str, Any], lang: str) -> list[dict[str, Any]]:
    found = []
    system = overview.get("system", {})
    if system.get("test_mode"):
        found.append(_finding("test_mode", lang, severity="warning"))
    if not system.get("sirens_enabled") and any(p.get("sirens") for p in overview["profiles"]):
        found.append(_finding("sirens_locked", lang))
    return found


def _profiles(overview: Mapping[str, Any], lang: str) -> list[dict[str, Any]]:
    found = []
    for profile in overview.get("profiles", []):
        name = profile["name"]
        if not profile.get("zones") and not profile.get("rules"):
            found.append(_finding("profile_empty", lang, severity="warning", key=name, name=name))
        audible = profile.get("sirens") and not profile.get("silent")
        if not audible and not profile.get("alarm_targets"):
            found.append(
                _finding(
                    "profile_unheard", lang, severity="warning", important=True, key=name, name=name
                )
            )
        elif not audible:
            found.append(_finding("profile_no_siren", lang, key=name, name=name))
    return found


def _sensors(overview: Mapping[str, Any], lang: str, now: datetime) -> list[dict[str, Any]]:
    found = []
    for sensor in overview.get("sensors", []):
        name = sensor["name"]
        key = sensor["entity_id"]
        technical = sensor.get("type") == "technical"
        if (
            sensor.get("zone")
            and not technical
            and not sensor.get("always_active")
            and not any(r in ("armed", "rule") for r in sensor.get("profiles", {}).values())
        ):
            found.append(_finding("sensor_unused", lang, severity="warning", key=key, name=name))
        if sensor.get("state") == "unavailable":
            hours = _hours_since(sensor.get("last_contact"), now)
            long = hours is not None and hours >= UNAVAILABLE_IMPORTANT_HOURS
            since = ""
            if hours is not None and hours >= 1:
                since = f" (seit {round(hours)} h)" if lang == "de" else f" (for {round(hours)} h)"
            found.append(
                _finding(
                    "sensor_unavailable",
                    lang,
                    severity="warning",
                    important=long,
                    key=key,
                    name=name,
                    since=since,
                )
            )
        battery = sensor.get("battery")
        if isinstance(battery, int | float) and battery < BATTERY_LOW:
            found.append(
                _finding(
                    "battery_low", lang, severity="warning", key=key, name=name, battery=battery
                )
            )
    return found


def _sirens(overview: Mapping[str, Any], lang: str, now: datetime) -> list[dict[str, Any]]:
    found = []
    for siren in overview.get("sirens", []):
        name = siren["name"]
        key = siren["entity_id"]
        if siren.get("burglar_tone") is False:
            found.append(
                _finding(
                    "siren_no_tone", lang, severity="warning", important=True, key=key, name=name
                )
            )
        if siren.get("fire_tone_override"):
            found.append(
                _finding(
                    "siren_fire_tone",
                    lang,
                    severity="warning",
                    key=key,
                    name=name,
                    tone=siren.get("tone"),
                )
            )
        tested = _parse(siren.get("last_test"))
        if tested is None:
            found.append(_finding("siren_untested", lang, key=key, name=name))
            continue
        days = (now - tested).days
        if days > SIREN_TEST_MAX_DAYS:
            found.append(_finding("siren_test_old", lang, key=key, name=name, days=days))
        if siren.get("heard") is False:
            found.append(_finding("siren_not_heard", lang, severity="warning", key=key, name=name))
    return found


def _users(overview: Mapping[str, Any], lang: str, duress: bool) -> list[dict[str, Any]]:
    found = []
    if duress and not overview.get("notifications", {}).get("duress_targets"):
        found.append(_finding("duress_no_targets", lang, severity="warning", important=True))
    any_pin = overview.get("pin_rules", {}).get("any_pin")
    master = overview.get("pin_rules", {}).get("master_pin")
    for user in overview.get("users", []):
        name = user["name"]
        if user.get("expired"):
            found.append(_finding("user_expired", lang, key=name, name=name))
        if any_pin and user.get("active") and not user.get("pin") and not user.get("expired"):
            code = "user_master_pin_only" if master else "user_without_pin"
            found.append(_finding(code, lang, key=name, name=name))
    return found


def _monitoring(overview: Mapping[str, Any], lang: str) -> list[dict[str, Any]]:
    found = []
    monitoring = overview.get("monitoring", {})
    hours = monitoring.get("stale_after_hours") or 0
    advice = monitoring.get("recommended_hours")
    if not hours:
        text = ""
        if advice:
            text = f" (Empfehlung: {advice} h)" if lang == "de" else f" (recommended: {advice} h)"
        found.append(_finding("silence_off", lang, advice=text))
    elif advice and hours < advice:
        found.append(_finding("silence_tight", lang, hours=hours, advice=advice))
    for own in monitoring.get("stale_overrides", []):
        own_hours, own_advice = own.get("hours") or 0, own.get("recommended")
        if own_hours and own_advice and own_hours < own_advice:
            found.append(
                _finding(
                    "silence_tight_sensor",
                    lang,
                    key=own["name"],
                    name=own["name"],
                    hours=own_hours,
                    advice=own_advice,
                )
            )
    for name in monitoring.get("homecoming", {}).get("weak_proof", []):
        found.append(_finding("away_weak", lang, key=name, name=name))
    for name in monitoring.get("homecoming", {}).get("no_fix", []):
        found.append(_finding("away_no_fix", lang, severity="warning", key=name, name=name))
    for person in monitoring.get("homecoming", {}).get("leaving", []):
        status = person.get("status")
        if status not in ("ok", "slow", "pauses"):
            continue  # noch zu wenig gemessen
        found.append(
            _finding(
                "leaving_" + status,
                lang,
                severity="info" if status == "ok" else "warning",
                key=person["name"],
                name=person["name"],
                minutes=person.get("wait_minutes"),
                needed=person.get("needed_minutes"),
                count=person.get("with_door"),
                pauses=person.get("pauses_longer"),
            )
        )
    infrastructure = monitoring.get("infrastructure", [])
    if not infrastructure:
        found.append(_finding("no_infrastructure", lang))
    for item in infrastructure:
        if not item.get("ok"):
            found.append(
                _finding(
                    "infrastructure_fault",
                    lang,
                    severity="warning",
                    key=item["name"],
                    name=item["name"],
                )
            )
    return found


def _guest(overview: Mapping[str, Any], lang: str) -> list[dict[str, Any]]:
    found = []
    for area in overview.get("areas", []):
        if not area.get("guest"):
            continue
        until = _parse(area.get("guest_until"))
        if until is None:
            text = "bis zum Ausschalten" if lang == "de" else "until switched off"
        else:
            # guest_until kommt in Ortszeit (mit Versatz) aus der Übersicht
            fmt = "%d.%m. %H:%M" if lang == "de" else "%d %b %H:%M"
            text = ("bis " if lang == "de" else "until ") + until.strftime(fmt)
        found.append(_finding("guest_mode", lang, key=area["name"], area=area["name"], until=text))
    return found


def _action_codes(overview: Mapping[str, Any], lang: str) -> list[dict[str, Any]]:
    found = []
    alarm = next(
        (e for e in overview.get("notifications", {}).get("events", []) if e["event"] == "alarm"),
        None,
    )
    for code in overview.get("action_codes", []):
        name = code["name"]
        if code.get("profile_missing"):
            found.append(
                _finding(
                    "action_code_profile_missing", lang, severity="warning", key=name, name=name
                )
            )
        if code.get("keypad_missing"):
            found.append(_finding("action_code_keypad_missing", lang, key=name, name=name))
        if code.get("action") == "silent_emergency" and not (alarm and alarm.get("targets")):
            found.append(
                _finding(
                    "silent_emergency_no_targets",
                    lang,
                    severity="warning",
                    important=True,
                    key=name,
                    name=name,
                )
            )
    return found


def _rules(overview: Mapping[str, Any], lang: str) -> list[dict[str, Any]]:
    return [
        _finding("rule_unused", lang, key=rule["name"], name=rule["name"])
        for rule in overview.get("rules", [])
        if not rule.get("profiles")
    ]


def run_checks(
    overview: Mapping[str, Any],
    language: str = "de",
    *,
    duress_configured: bool = False,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Alle Prüfhinweise, wichtige zuerst, dann Warnungen, dann Hinweise."""
    now = now or datetime.now(UTC)
    found = [
        *_system(overview, language),
        *_profiles(overview, language),
        *_users(overview, language, duress_configured),
        *_sensors(overview, language, now),
        *_sirens(overview, language, now),
        *_monitoring(overview, language),
        *_rules(overview, language),
        *_guest(overview, language),
        *_action_codes(overview, language),
    ]
    order = {"warning": 0, "info": 1}
    return sorted(found, key=lambda f: (not f["important"], order.get(f["severity"], 2)))
