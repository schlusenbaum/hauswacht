"""Texte für Benachrichtigungen, Push-Knöpfe und Berichte – Deutsch und Englisch.

Rein und ohne Home Assistant. Die Sprache folgt der Sprache von Home Assistant: Deutsch für
``de…``, sonst Englisch. Platzhalter in geschweiften Klammern (``str.format``).

Eigene Texte (Einstellungen → Benachrichtigungen) ersetzen diese Standardtexte; deren Platzhalter
heißen in beiden Sprachen gleich (``{melder}``, ``{profil}`` …).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

DE = "de"
EN = "en"


def lang_of(language: str | None) -> str:
    """Sprache von Home Assistant → ``de`` oder ``en``."""
    return DE if (language or "").lower().startswith("de") else EN


TEXTS: Mapping[str, Mapping[str, str]] = {
    DE: {
        # Wer, Verbindungsstücke
        "by": " von {who}",
        "by_paren": " ({who})",
        "quote": "„{text}“",
        # Push-Knöpfe
        "btn_arm_anyway": "Trotzdem scharf",
        "btn_retry": "Erneut versuchen",
        "btn_arm_now": "Jetzt scharf ({profile})",
        "btn_disarm": "Unscharf schalten",
        "btn_end_alarm": "Alarm beenden",
        # Scharf / unscharf
        "arm_failed_title": "Hauswacht: nicht scharf geschaltet",
        "arm_failed": "Profil {profile}{by}: {reason}",
        "reminder_title": "Hauswacht: Anlage ist unscharf",
        "reminder": "Alle sind seit {minutes} Minuten weg, die Anlage ist aber unscharf.",
        "armed_title": "Hauswacht: scharf",
        "armed": "Profil {profile} scharf geschaltet{by}.",
        "disarmed_title": "Hauswacht: unscharf",
        "disarmed": "Unscharf geschaltet{by}.",
        "push_disarmed": "Unscharf geschaltet über den Push-Knopf von {who}.",
        "push_denied_title": "Hauswacht: nicht erlaubt",
        "push_denied": "Push-Knopf von {who}: dafür fehlt die Berechtigung.",
        "arm_hint_title": "Hauswacht: Hinweis beim Scharfschalten",
        "arm_hint_short_title": "Hauswacht: Hinweis",
        "arm_hint": "Profil {profile} ist scharf. Offen: {items}. Diese Melder können ihre "
        "Auslöseregeln erst auslösen, wenn sie zu und wieder auf gehen.",
        "arm_hint_item": "{sensor} (Auslöseregel {rules})",
        # Alarm
        "alarm_prefix": "EINBRUCHALARM",
        "alarm_prefix_test": "TESTALARM",
        "alarm_title": "Hauswacht: {prefix}",
        "alarm": "{prefix} – ausgelöst durch {sensor} (Profil {profile}).",
        "alarm_sirens": " Sirenen: {sirens}.",
        "alarm_sirens_blocked": " Gesperrte Sirenen ({reasons}).",
        "alarm_rule": " Auslöseregel: {rule}.",
        "alarm_silent": " Stiller Alarm.",
        "entry_title": "Hauswacht: Tür geöffnet",
        "entry": "{sensor} – Eingangsverzögerung {seconds} s läuft (Profil {profile}).",
        "alarm_ended_title": "Hauswacht: Alarm beendet",
        "alarm_ended_disarmed": "Alarm beendet{by}. Die Anlage ist unscharf.",
        "alarm_ended_armed": "Alarm beendet{by}. Profil {profile} bleibt scharf.",
        "alarm_ended_bypassed": " Bis zum Schließen nicht überwacht: {sensors}.",
        "sirens_blocked_title": "Hauswacht: Sirenen gesperrt",
        "sirens_blocked": "Alarm ausgelöst, Sirenen wurden aber nicht angesteuert: {reasons}.",
        "panic_title": "Hauswacht: NOTRUF",
        "panic": "Notruf-Taste am Bedienteil {control} gedrückt.",
        # Ausweise
        "invalid_code_title": "Hauswacht: falscher PIN",
        "invalid_code": "{failures} falsche PIN-Eingaben in Folge.",
        "invalid_code_lock": " Die PIN-Eingabe ist für {seconds} Sekunden gesperrt.",
        "blocked_credential_title": "Hauswacht: gesperrter Ausweis",
        "blocked_credential": "Ein gesperrter oder abgelaufener PIN bzw. eine solche Karte wurde "
        "verwendet: {who}.",
        "duress_title": "BEDROHUNG – Hauswacht",
        "duress": "{who} hat mit dem Bedrohungs-PIN {what}. Möglicherweise Gefahr – bitte "
        "unauffällig reagieren.",
        "duress_arm": "scharf geschaltet",
        "duress_disarm": "unscharf geschaltet",
        "duress_end_alarm": "einen Alarm beendet",
        "sticker_denied_title": "Hauswacht: Aufkleber abgelehnt",
        "sticker_denied": "NFC-Aufkleber {sticker}: Das Handy gehört keinem berechtigten "
        "Hauswacht-Benutzer.",
        "control_denied_title": "Hauswacht: Bedienteil",
        "control_denied": "{control}: {who} wollte {what} – nicht möglich ({result}).",
        "control_arm": "scharf schalten",
        "control_disarm": "unscharf schalten",
        # Störungen
        "fault_title": "Hauswacht: Störung",
        "fault": "Hauswacht ist scharf, aber diese Systeme sind gestört: {systems}. Sensoren "
        "dahinter können nicht melden.",
        "sensor_lost_title": "Hauswacht: Sensor ausgefallen",
        "sensor_lost": "Der überwachte Sensor {sensor} ist nicht mehr verfügbar.",
        "sensor_lost_armed": " Hauswacht ist scharf, kann diesen Bereich aber nicht mehr "
        "überwachen.",
        "tamper_title": "Hauswacht: Manipulation",
        "tamper": "Manipulation gemeldet: {sensor}.",
        "restart_title": "Hauswacht: nach Neustart unscharf",
        "restart": "Home Assistant wurde neu gestartet. Hauswacht war scharf (Profil {profile}) "
        "und ist jetzt UNSCHARF.",
        # Immer aktiv, Auslöseregeln
        "always_title": "Hauswacht: immer aktiver Melder",
        "always": "{sensor} hat ausgelöst (immer aktiv, Anlage unscharf).",
        "rule_notify_title": "Hauswacht: Auslöseregel erfüllt",
        "rule_notify": "Auslöseregel {rule} erfüllt (durch {sensor}) – nur Benachrichtigung, "
        "kein Alarm.",
        "unconfirmed_title": "Hauswacht: unbestätigte Auslösung",
        "unconfirmed": "Auslöseregel {rule} nur teilweise erfüllt ({done} von {total} Schritten, "
        "begonnen mit {sensor}) – kein Alarm.",
        "lone_title": "Hauswacht: Melder löst häufig allein aus",
        "lone": "{sensor} hat innerhalb einer Stunde {count}-mal eine Auslöseregel begonnen, die "
        "nicht erfüllt wurde. Bitte Melder prüfen (Empfindlichkeit, Ausrichtung, Batterie).",
        # Automatik
        "auto_armed_title": "Hauswacht: automatisch scharf",
        "auto_armed": "Profil {profile} wurde automatisch scharf geschaltet ({reason}).",
        "auto_arm_failed_title": "Hauswacht: automatisches Scharfschalten fehlgeschlagen",
        "auto_arm_failed": "Profil {profile} konnte nicht automatisch scharf geschaltet werden "
        "({reason}): {details}",
        "auto_disarmed_title": "Hauswacht: automatisch unscharf",
        "auto_disarmed": "Profil {profile} wurde automatisch unscharf geschaltet ({reason}).",
        "shared_pin": "gemeinsamer PIN ({names})",
        "tpl_too_long": "höchstens {max} Zeichen",
        "tpl_braces": "geschweifte Klammern passen nicht zusammen",
        "tpl_unknown": "unbekannter Platzhalter {field}",
        "tpl_format": "{field}: keine Formatangaben erlaubt",
        "reason_time": "Uhrzeit",
        "automation_actor": "Automatik",
        "reason_away": "alle weg",
        "reason_arrival": "Rückkehr",
        # Sirenentest
        "siren_prewarn_title": "Hauswacht: Sirenentest",
        "siren_prewarn": "Sirenentest {siren} in {seconds} Sekunden ({duration} s, Lautstärke "
        "{volume}).",
        "siren_due_title": "Hauswacht: Sirenentest fällig",
        "siren_due": "Bitte die Sirenen prüfen: {sirens}. Einstellungen → Alarmgeber – Sirenen → "
        "Sirenentest oder Testkarte.",
        # Heimkehr-Beobachtung
        "hc_title": "Hauswacht: Heimkehr-Beobachtung",
        "hc_heading": "Hauswacht: Heimkehr-Beobachtung",
        "hc_created": "Erstellt",
        "hc_off": "Die Heimkehr-Beobachtung ist ausgeschaltet.",
        "hc_none": "Noch keine Heimkehr aufgezeichnet.",
        "hc_summary": "Beobachtet: {days} Tage. Türöffnungen ohne Heimkehr: {door_only}.",
        "hc_col_source": "Quelle",
        "hc_col_arrivals": "Heimkehr",
        "hc_col_with_door": "mit Tür",
        "hc_col_without_door": "ohne Tür",
        "hc_col_delay": "typ. Verzögerung",
        "hc_col_false": "Fehlalarme bei {seconds} s",
        "hc_legend": "**Fehlalarme**: Heimkehr erst nach Ablauf der Eingangsverzögerung erkannt. "
        "**ohne Tür**: Ankunft ohne Türöffnung (meist Falschmeldung der Ortung).",
        "hc_entry_heading": "**Tür auf bis unscharf** (Eingangsverzögerung):",
        "hc_entry_cols": "| Tür | Eingänge | rechtzeitig | zu spät | typisch | längste | "
        "Empfehlung |",
        "hc_recent": "Letzte Heimkehrten",
        "hc_download": "Zum Herunterladen (Bericht und alle Einzelwerte als Tabelle): Karte "
        "„Hauswacht Übersicht“ → Überwachung.",
        "hc_overall": "{person} (gesamt)",
        "hc_earliest": "{person} (frühestes Signal)",
        "hc_no_door": "{who}: Ankunft ohne Türöffnung – würde ignoriert",
        "hc_before": "{who}: {seconds} s VOR dem Öffnen ({door}) erkannt",
        "hc_after": "{who}: {seconds} s nach dem Öffnen ({door}) erkannt – {hint}",
        "hc_enough_from": "reicht ab {seconds} s Eingangsverzögerung",
        "hc_too_late": "zu spät für jede Verzögerung",
        "hc_csv_kind": "Art",
        "hc_csv_time": "Zeitpunkt",
        "hc_csv_who": "Wer / Quelle",
        "hc_csv_door": "Tür",
        "hc_csv_seconds": "Sekunden nach Öffnen",
        "hc_csv_away": "Abwesend (min)",
        "hc_csv_result": "Ergebnis",
        "hc_csv_arrival": "Heimkehr",
        "hc_csv_entry": "Eingang",
        "hc_entry_in_time": "rechtzeitig unscharf (Verzögerung {delay} s)",
        "hc_entry_too_late": "zu spät – Alarm (Verzögerung {delay} s)",
        "hc_filename": "hauswacht-heimkehr",
    },
    EN: {
        "by": " by {who}",
        "by_paren": " ({who})",
        "quote": "“{text}”",
        "btn_arm_anyway": "Arm anyway",
        "btn_retry": "Try again",
        "btn_arm_now": "Arm now ({profile})",
        "btn_disarm": "Disarm",
        "btn_end_alarm": "End alarm",
        "arm_failed_title": "Hauswacht: not armed",
        "arm_failed": "Profile {profile}{by}: {reason}",
        "reminder_title": "Hauswacht: system is disarmed",
        "reminder": "Everyone has been away for {minutes} minutes, but the system is disarmed.",
        "armed_title": "Hauswacht: armed",
        "armed": "Profile {profile} armed{by}.",
        "disarmed_title": "Hauswacht: disarmed",
        "disarmed": "Disarmed{by}.",
        "push_disarmed": "Disarmed via the push button by {who}.",
        "push_denied_title": "Hauswacht: not allowed",
        "push_denied": "Push button by {who}: missing permission.",
        "arm_hint_title": "Hauswacht: note on arming",
        "arm_hint_short_title": "Hauswacht: note",
        "arm_hint": "Profile {profile} is armed. Open: {items}. These sensors can only trigger "
        "their rules after closing and opening again.",
        "arm_hint_item": "{sensor} (trigger rule {rules})",
        "alarm_prefix": "INTRUSION ALARM",
        "alarm_prefix_test": "TEST ALARM",
        "alarm_title": "Hauswacht: {prefix}",
        "alarm": "{prefix} – triggered by {sensor} (profile {profile}).",
        "alarm_sirens": " Sirens: {sirens}.",
        "alarm_sirens_blocked": " Locked sirens ({reasons}).",
        "alarm_rule": " Trigger rule: {rule}.",
        "alarm_silent": " Silent alarm.",
        "entry_title": "Hauswacht: door opened",
        "entry": "{sensor} – entry delay of {seconds} s running (profile {profile}).",
        "alarm_ended_title": "Hauswacht: alarm ended",
        "alarm_ended_disarmed": "Alarm ended{by}. The system is disarmed.",
        "alarm_ended_armed": "Alarm ended{by}. Profile {profile} stays armed.",
        "alarm_ended_bypassed": " Not monitored until closed: {sensors}.",
        "sirens_blocked_title": "Hauswacht: sirens locked",
        "sirens_blocked": "Alarm triggered, but the sirens were not activated: {reasons}.",
        "panic_title": "Hauswacht: EMERGENCY",
        "panic": "Emergency button pressed on {control}.",
        "invalid_code_title": "Hauswacht: wrong PIN",
        "invalid_code": "{failures} wrong PIN entries in a row.",
        "invalid_code_lock": " PIN entry is locked for {seconds} seconds.",
        "blocked_credential_title": "Hauswacht: blocked credential",
        "blocked_credential": "A blocked or expired PIN or card was used: {who}.",
        "duress_title": "DURESS – Hauswacht",
        "duress": "{who} used the duress PIN to {what}. Possible danger – please react discreetly.",
        "duress_arm": "arm",
        "duress_disarm": "disarm",
        "duress_end_alarm": "end an alarm",
        "sticker_denied_title": "Hauswacht: tag rejected",
        "sticker_denied": "NFC tag {sticker}: the phone does not belong to an authorised "
        "Hauswacht user.",
        "control_denied_title": "Hauswacht: control",
        "control_denied": "{control}: {who} tried to {what} – not possible ({result}).",
        "control_arm": "arm",
        "control_disarm": "disarm",
        "fault_title": "Hauswacht: fault",
        "fault": "Hauswacht is armed, but these systems have a fault: {systems}. Sensors behind "
        "them cannot report.",
        "sensor_lost_title": "Hauswacht: sensor lost",
        "sensor_lost": "The monitored sensor {sensor} is no longer available.",
        "sensor_lost_armed": " Hauswacht is armed but can no longer monitor this area.",
        "tamper_title": "Hauswacht: tampering",
        "tamper": "Tampering reported: {sensor}.",
        "restart_title": "Hauswacht: disarmed after restart",
        "restart": "Home Assistant was restarted. Hauswacht was armed (profile {profile}) and is "
        "now DISARMED.",
        "always_title": "Hauswacht: always-active sensor",
        "always": "{sensor} triggered (always active, system disarmed).",
        "rule_notify_title": "Hauswacht: trigger rule met",
        "rule_notify": "Trigger rule {rule} met (by {sensor}) – notification only, no alarm.",
        "unconfirmed_title": "Hauswacht: unconfirmed trigger",
        "unconfirmed": "Trigger rule {rule} only partly met ({done} of {total} steps, started "
        "by {sensor}) – no alarm.",
        "lone_title": "Hauswacht: sensor often triggers alone",
        "lone": "{sensor} started a trigger rule {count} times within an hour without it being "
        "met. Please check the sensor (sensitivity, alignment, battery).",
        "auto_armed_title": "Hauswacht: armed automatically",
        "auto_armed": "Profile {profile} was armed automatically ({reason}).",
        "auto_arm_failed_title": "Hauswacht: automatic arming failed",
        "auto_arm_failed": "Profile {profile} could not be armed automatically ({reason}): "
        "{details}",
        "auto_disarmed_title": "Hauswacht: disarmed automatically",
        "auto_disarmed": "Profile {profile} was disarmed automatically ({reason}).",
        "shared_pin": "shared PIN ({names})",
        "tpl_too_long": "at most {max} characters",
        "tpl_braces": "curly braces do not match",
        "tpl_unknown": "unknown placeholder {field}",
        "tpl_format": "{field}: no format specifications allowed",
        "reason_time": "time",
        "automation_actor": "Automation",
        "reason_away": "everyone away",
        "reason_arrival": "return",
        "siren_prewarn_title": "Hauswacht: siren test",
        "siren_prewarn": "Siren test {siren} in {seconds} seconds ({duration} s, volume {volume}).",
        "siren_due_title": "Hauswacht: siren test due",
        "siren_due": "Please check the sirens: {sirens}. Settings → Alarm devices – sirens → "
        "Siren test, or the test card.",
        "hc_title": "Hauswacht: homecoming observation",
        "hc_heading": "Hauswacht: homecoming observation",
        "hc_created": "Created",
        "hc_off": "The homecoming observation is switched off.",
        "hc_none": "No homecoming recorded yet.",
        "hc_summary": "Observed: {days} days. Door openings without homecoming: {door_only}.",
        "hc_col_source": "Source",
        "hc_col_arrivals": "Homecomings",
        "hc_col_with_door": "with door",
        "hc_col_without_door": "without door",
        "hc_col_delay": "typical delay",
        "hc_col_false": "false alarms at {seconds} s",
        "hc_legend": "**False alarms**: homecoming detected only after the entry delay ran out. "
        "**without door**: arrival without a door opening (usually a location glitch).",
        "hc_entry_heading": "**Door open to disarmed** (entry delay):",
        "hc_entry_cols": "| Door | Entries | in time | too late | typical | longest | "
        "recommended |",
        "hc_recent": "Recent homecomings",
        "hc_download": "To download (report and every single value as a table): card "
        "“Hauswacht Übersicht” (overview) → Monitoring.",
        "hc_overall": "{person} (overall)",
        "hc_earliest": "{person} (earliest signal)",
        "hc_no_door": "{who}: arrival without door opening – would be ignored",
        "hc_before": "{who}: detected {seconds} s BEFORE opening ({door})",
        "hc_after": "{who}: detected {seconds} s after opening ({door}) – {hint}",
        "hc_enough_from": "enough from an entry delay of {seconds} s",
        "hc_too_late": "too late for any delay",
        "hc_csv_kind": "Kind",
        "hc_csv_time": "Time",
        "hc_csv_who": "Who / source",
        "hc_csv_door": "Door",
        "hc_csv_seconds": "Seconds after opening",
        "hc_csv_away": "Away (min)",
        "hc_csv_result": "Result",
        "hc_csv_arrival": "Homecoming",
        "hc_csv_entry": "Entry",
        "hc_entry_in_time": "disarmed in time (delay {delay} s)",
        "hc_entry_too_late": "too late – alarm (delay {delay} s)",
        "hc_filename": "hauswacht-homecoming",
    },
}


def tr(lang: str, key: str, **values: Any) -> str:
    """Text in der Sprache ``lang`` (unbekannte Sprache: Englisch)."""
    return TEXTS.get(lang, TEXTS[EN])[key].format(**values)


def by(lang: str, who: str | None) -> str:
    """ " von Anna" bzw. " by Anna" – leer ohne Namen."""
    return tr(lang, "by", who=who) if who else ""


def quoted(lang: str, text: str) -> str:
    return tr(lang, "quote", text=text)
