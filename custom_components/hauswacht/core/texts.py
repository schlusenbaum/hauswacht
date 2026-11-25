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
        "event_all_areas": "Alle Bereiche",
        "tilted_suffix": " (gekippt)",
        "vibration_suffix": " (Erschütterung)",
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
        "arm_gaps": "Profil {profile} ist scharf{by}. Nicht überwacht: {items}.",
        "arm_gaps_tail": "Nicht überwacht: {items}.",
        "arm_gap_bypassed": "{sensor} – offen, überbrückt bis zum Unscharfschalten",
        "arm_gap_unavailable": "{sensor} – ausgefallen, wird wieder überwacht, sobald er sich "
        "meldet",
        "arm_gap_rule": "{sensor} – offen, Auslöseregel {rules} erst nach Schließen und "
        "erneutem Öffnen",
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
        "action_code_actor": "Aktions-Code „{name}“",
        # Ausweise
        "invalid_code_title": "Hauswacht: falscher PIN",
        "invalid_code": "{failures} falsche PIN-Eingaben in Folge.",
        "invalid_code_lock": " Die PIN-Eingabe ist für {seconds} Sekunden gesperrt.",
        "card_disabled_title": "Hauswacht: deaktivierte Karte benutzt",
        "card_disabled": "Die deaktivierte Karte „{card}“ ({who}) wurde an {where} benutzt. Sie "
        "schaltet nichts; der Versuch zählt als Fehleingabe.",
        "lock_disabled": "Die deaktivierte Schloss-Kennung „{card}“ ({who}) wurde an {where} "
        "benutzt. Hauswacht hat deshalb nichts geschaltet.",
        "blocked_credential_title": "Hauswacht: gesperrter Ausweis",
        "blocked_credential": "Ein gesperrter oder abgelaufener PIN bzw. eine solche Karte wurde "
        "verwendet: {who}.",
        "duress_title": "BEDROHUNG – Hauswacht",
        "duress": "{who} hat mit dem Bedrohungs-PIN {what}. Möglicherweise Gefahr – bitte "
        "unauffällig reagieren.",
        "duress_arm": "scharf geschaltet",
        "duress_disarm": "unscharf geschaltet",
        "duress_end_alarm": "einen Alarm beendet",
        "duress_passage": "einen Durchgang geöffnet (die Anlage bleibt scharf)",
        "passage_title": "Hauswacht: Durchgang",
        "passage_key": "Durchgang (rein/raus, bleibt scharf)",
        "passage_by_phone": "{who} (Handy)",
        "btn_passage": "Reinlassen",
        "passage_in": "{who} hereingelassen ({door}) – Profil {profile} bleibt scharf.",
        "passage_out": "{who}: Durchgang für {minutes} Minuten – Profil {profile} bleibt scharf.",
        "passage_open": "{door} nach dem Durchgang noch offen – wird nicht überwacht, bis sie "
        "zu ist. Profil {profile} bleibt scharf.",
        "sticker_denied_title": "Hauswacht: Aufkleber abgelehnt",
        "sticker_denied": "NFC-Aufkleber {sticker}: Das Handy gehört keinem berechtigten "
        "Hauswacht-Benutzer.",
        "control_denied_title": "Hauswacht: Bedienteil",
        "button_pin_required": "{control}: Scharfschalten verlangt einen PIN (PIN-Regeln) – "
        "ein Taster kann keinen PIN eingeben. Nicht scharf geschaltet.",
        "lock_unknown": "{control}: aufgeschlossen mit einer unbekannten Kennung ({id}) – nicht "
        "unscharf geschaltet.",
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
        "restored_title": "Hauswacht: nach Neustart wieder scharf",
        "restored": "Home Assistant wurde neu gestartet. Hauswacht ist wieder scharf "
        "(Profil {profile}) – wie vor dem Neustart.",
        "restored_entry": " Vor dem Neustart lief die Eingangsverzögerung; sie beginnt neu.",
        "restored_alarm": " Vor dem Neustart lief ein Alarm (ausgelöst von {sensor}). Er wird "
        "nicht fortgesetzt, die Sirenen bleiben aus; die Anlage ist scharf.",
        "restored_alarm_resumed": " Vor dem Neustart lief ein Alarm (ausgelöst von {sensor}). Er "
        "wird fortgesetzt, sobald Home Assistant hochgefahren ist.",
        "restored_alarm_title": "Hauswacht: Alarm vor dem Neustart",
        "restored_open_title": "Hauswacht: offen nach Neustart",
        "restored_open": "Beim Hochfahren offen und deshalb bis zum Schließen überbrückt: "
        "{sensors}.",
        "restart_actor": "Neustart",
        "sirens_restart_off_title": "Hauswacht: Sirene nach Neustart",
        "sirens_restart_off": "Lief beim Neustart noch für einen Alarm und wurde ausgeschaltet: "
        "{sirens}.",
        "sirens_restart_fire": "Lief beim Neustart noch für einen Alarm, wird wegen der "
        "Brandsperre aber noch nicht ausgeschaltet: {sirens}. Hauswacht versucht es jede Minute "
        "erneut.",
        "reason_restart": "Neustart",
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
        "on": "an",
        "off": "aus",
        "shared_pin": "gemeinsamer PIN ({names})",
        "tpl_too_long": "höchstens {max} Zeichen",
        "tpl_braces": "geschweifte Klammern passen nicht zusammen",
        "tpl_unknown": "unbekannter Platzhalter {field}",
        "tpl_format": "{field}: keine Formatangaben erlaubt",
        "reason_time": "Uhrzeit",
        "reason_schedule": "Zeitplan",
        "automation_actor": "Automatik",
        "guest_title": "Hauswacht: Gastmodus",
        "guest_on": "Gastmodus an für {area} – bis {until}. Hauswacht schaltet bis dahin nicht "
        "automatisch scharf.",
        "guest_off": "Gastmodus aus für {area} – die Automatik schaltet wieder scharf.",
        "guest_until_off": "zum Ausschalten",
        "guest_skipped": "Gastmodus an – „{profile}“ wurde nicht automatisch scharf geschaltet.",
        "reason_away": "alle weg",
        "reason_arrival": "Rückkehr",
        "reason_arrival_door": "Rückkehr mit Türbeleg",
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
        "dep_all": "{person} (alle Signale)",
        "hc_proof_heading": "**Unscharf mit Türbeleg** – nötige Eingangsverzögerung je Person:",
        "hc_proof_line": "- {person}: mindestens {seconds} s (längste Erkennung nach dem "
        "Öffnen: {late} s; {count} Heimkehrten mit Tür, {phantom} ohne Tür – die würden "
        "ignoriert)",
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
        "hc_entry_passage": "per Durchgang reingelassen, blieb scharf – zählt nicht mit",
        "hc_filename": "hauswacht-heimkehr",
        # Beobachtung Weggehen (ADR 0014)
        "exit_heading": "**Vorbereitung Ausgangserkennung** – Lebenszeichen rund um die Tür",
        "exit_cols": "| Person | Lebenszeichen vor dem Rausgehen | „noch da“ nach der Tür "
        "(typisch / längste) | ohne „noch da“ | „zuhause“ nach dem Rausgehen |",
        "exit_legend": "**Lebenszeichen vor dem Rausgehen**: Beim Rausgehen meldete kurz vorher "
        "(bis 3 Minuten) ein Signal „zuhause“. Nur dann kann die Ausgangserkennung die Person "
        "später erkennen. **„noch da“ nach der Tür**: Jemand mit Lebenszeichen bleibt zuhause, "
        "während eine Tür aufgeht – so schnell meldet sich ein Signal wieder mit „zuhause“. So "
        "lange bliebe ein Einbruch höchstens still. **„zuhause“ nach dem Rausgehen**: Signale "
        "meldeten nach dem Öffnen noch „zuhause“, obwohl die Person gerade rausging (z. B. Ping "
        "mit Nachlaufzeit).",
        "exit_sign": "{name}: beim Rausgehen {count} von {total}× mit Lebenszeichen kurz vorher.",
        "exit_confirm": "{name}: bleibt zuhause, während eine Tür aufgeht – meldet sich typisch "
        "nach {median} s, spätestens nach {longest} s wieder.",
        "exit_confirm_missing": "{name}: bleibt zuhause, während eine Tür aufgeht – meldet sich "
        "typisch nach {median} s wieder, aber {missing} von {total}× 15 Minuten lang gar nicht.",
        "exit_echo": "{name}: nach dem Rausgehen meldeten Signale {count}× noch „zuhause“ "
        "(bis {longest} s nach dem Öffnen).",
        "dep_heading": "**Weggehen** – wie schnell melden die Signale „weg“?",
        "dep_cols": "| Quelle | Rausgehen mit Tür | typisch bis „weg“ | längste | "
        "Schweigepausen | längste Pause |",
        "dep_legend": "**Rausgehen mit Tür**: Eine Tür ging bis zu 15 Minuten vorher auf. "
        "**Schweigepause**: „weg“, ohne dass vorher eine Tür aufging – das Handy hat nur "
        "geschwiegen (schläft, WLAN-Aussetzer).",
        "dep_advice_heading": "**Rausgehen ohne PIN erkennen** – Empfehlung je Person:",
        "dep_status_few": "{name}: noch zu wenig gemessen ({count}× Rausgehen) – die "
        "Empfehlung kommt nach mindestens 3× Rausgehen und 2 Tagen.",
        "dep_status_none": "{name}: noch nicht weggegangen, seit gemessen wird.",
        "dep_status_ok": "{name}: Rausgehen wird zuverlässig erkannt – empfohlene Wartezeit "
        "{minutes} min (aus {count}× Rausgehen).",
        "dep_status_slow": "{name}: Die Signale merken das Rausgehen erst nach bis zu {needed} "
        "min – länger als die längste Wartezeit (15 min). Tipp: ein schnelleres Signal "
        "einrichten, z. B. den WLAN-Sensor der Companion App.",
        "dep_status_pauses": "{name}: Alle Signale haben {pauses}× länger als {minutes} min "
        "geschwiegen, ohne dass eine Tür aufging. So wäre Rausgehen nicht sicher von einem "
        "Einbruch zu unterscheiden. Tipp: ein zweites Signal einrichten, z. B. die Companion App "
        "mit WLAN-Sensor.",
        "dep_left": "{who}: {seconds} s nach dem Öffnen ({door}) „weg“",
        "dep_pause": "{who}: Schweigepause ohne Tür, {minutes} min",
        "dep_pause_open": "{who}: Schweigepause ohne Tür, seit {minutes} min",
        "dep_pause_shared": "{who}: Schweigepause ohne Tür, {minutes} min – gleichzeitig bei "
        "anderen (WLAN-Ausfall?)",
        "dep_pause_shared_open": "{who}: Schweigepause ohne Tür, seit {minutes} min – "
        "gleichzeitig bei anderen (WLAN-Ausfall?)",
        "dep_csv_kind": "Weggehen",
    },
    EN: {
        "by": " by {who}",
        "event_all_areas": "All areas",
        "tilted_suffix": " (tilted)",
        "vibration_suffix": " (vibration)",
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
        "arm_gaps": "Profile {profile} is armed{by}. Not monitored: {items}.",
        "arm_gaps_tail": "Not monitored: {items}.",
        "arm_gap_bypassed": "{sensor} – open, bypassed until disarming",
        "arm_gap_unavailable": "{sensor} – unavailable, monitored again as soon as it reports",
        "arm_gap_rule": "{sensor} – open, trigger rule {rules} only after closing and opening "
        "again",
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
        "action_code_actor": "action code “{name}”",
        "invalid_code_title": "Hauswacht: wrong PIN",
        "invalid_code": "{failures} wrong PIN entries in a row.",
        "invalid_code_lock": " PIN entry is locked for {seconds} seconds.",
        "card_disabled_title": "Hauswacht: disabled card used",
        "card_disabled": "The disabled card “{card}” ({who}) was used at {where}. It switches "
        "nothing; the attempt counts as a wrong entry.",
        "lock_disabled": "The disabled lock ID “{card}” ({who}) was used at {where}. Hauswacht "
        "therefore switched nothing.",
        "blocked_credential_title": "Hauswacht: blocked credential",
        "blocked_credential": "A blocked or expired PIN or card was used: {who}.",
        "duress_title": "DURESS – Hauswacht",
        "duress": "{who} used the duress PIN to {what}. Possible danger – please react discreetly.",
        "duress_arm": "arm",
        "duress_disarm": "disarm",
        "duress_end_alarm": "end an alarm",
        "duress_passage": "open a passage (the system stays armed)",
        "passage_title": "Hauswacht: passage",
        "passage_key": "Passage (in/out, stays armed)",
        "passage_by_phone": "{who} (phone)",
        "btn_passage": "Let in",
        "passage_in": "{who} let in ({door}) – profile {profile} stays armed.",
        "passage_out": "{who}: passage for {minutes} minutes – profile {profile} stays armed.",
        "passage_open": "{door} still open after the passage – not monitored until it is "
        "closed. Profile {profile} stays armed.",
        "sticker_denied_title": "Hauswacht: tag rejected",
        "sticker_denied": "NFC tag {sticker}: the phone does not belong to an authorised "
        "Hauswacht user.",
        "control_denied_title": "Hauswacht: control",
        "button_pin_required": "{control}: arming requires a PIN (PIN rules) – a button cannot "
        "enter a PIN. Not armed.",
        "lock_unknown": "{control}: unlocked with an unknown ID ({id}) – not disarmed.",
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
        "restored_title": "Hauswacht: armed again after restart",
        "restored": "Home Assistant was restarted. Hauswacht is armed again (profile {profile}) "
        "– as before the restart.",
        "restored_entry": " The entry delay was running before the restart; it starts again.",
        "restored_alarm": " An alarm was running before the restart (triggered by {sensor}). It "
        "is not continued and the sirens stay off; the system is armed.",
        "restored_alarm_resumed": " An alarm was running before the restart (triggered by "
        "{sensor}). It is resumed as soon as Home Assistant has started.",
        "restored_alarm_title": "Hauswacht: alarm before the restart",
        "restored_open_title": "Hauswacht: open after restart",
        "restored_open": "Open at startup and therefore bypassed until closed: {sensors}.",
        "restart_actor": "restart",
        "sirens_restart_off_title": "Hauswacht: siren after restart",
        "sirens_restart_off": "Was still on for an alarm at the restart and has been switched "
        "off: {sirens}.",
        "sirens_restart_fire": "Was still on for an alarm at the restart, but is not switched off "
        "yet because of the fire lock: {sirens}. Hauswacht tries again every minute.",
        "reason_restart": "restart",
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
        "on": "on",
        "off": "off",
        "shared_pin": "shared PIN ({names})",
        "tpl_too_long": "at most {max} characters",
        "tpl_braces": "curly braces do not match",
        "tpl_unknown": "unknown placeholder {field}",
        "tpl_format": "{field}: no format specifications allowed",
        "reason_time": "time",
        "reason_schedule": "schedule",
        "automation_actor": "Automation",
        "guest_title": "Hauswacht: guest mode",
        "guest_on": "Guest mode on for {area} – until {until}. Until then Hauswacht does not arm "
        "automatically.",
        "guest_off": "Guest mode off for {area} – the automation arms again.",
        "guest_until_off": "switched off",
        "guest_skipped": "Guest mode on – “{profile}” was not armed automatically.",
        "reason_away": "everyone away",
        "reason_arrival": "return",
        "reason_arrival_door": "return with door opening",
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
        "dep_all": "{person} (all signals)",
        "hc_proof_heading": "**Disarm with door proof** – entry delay needed per person:",
        "hc_proof_line": "- {person}: at least {seconds} s (latest detection after opening: "
        "{late} s; {count} homecomings with door, {phantom} without door – those would be "
        "ignored)",
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
        "hc_entry_passage": "let in by passage, stayed armed – not counted",
        "hc_filename": "hauswacht-homecoming",
        # Departure observation (ADR 0014)
        "exit_heading": "**Preparing exit detection** – signs of life around the door",
        "exit_cols": "| Person | sign of life before leaving | “still here” after the door "
        "(typical / longest) | no “still here” | “home” after leaving |",
        "exit_legend": "**Sign of life before leaving**: when leaving, a signal reported "
        "“home” shortly before (up to 3 minutes). Only then can exit detection recognise the "
        "person later. **“Still here” after the door**: someone with a sign of life stays home "
        "while a door opens – this is how fast a signal reports “home” again. A break-in would "
        "stay silent for at most that long. **“Home” after leaving**: signals still reported "
        "“home” after the door opened although the person was just leaving (e.g. ping with a "
        "grace period).",
        "exit_sign": "{name}: when leaving, {count} of {total}× with a sign of life shortly "
        "before.",
        "exit_confirm": "{name}: stays home while a door opens – reports again typically after "
        "{median} s, at the latest after {longest} s.",
        "exit_confirm_missing": "{name}: stays home while a door opens – reports again typically "
        "after {median} s, but {missing} of {total}× not at all for 15 minutes.",
        "exit_echo": "{name}: after leaving, signals still reported “home” {count}× (up to "
        "{longest} s after the door opened).",
        "dep_heading": "**Leaving** – how fast do the signals report “away”?",
        "dep_cols": "| Source | Left through a door | typical until “away” | longest | "
        "silent pauses | longest pause |",
        "dep_legend": "**Left through a door**: a door opened up to 15 minutes before. "
        "**Silent pause**: “away” without a door opening before – the phone was only silent "
        "(asleep, Wi-Fi hiccup).",
        "dep_advice_heading": "**Detect leaving without PIN** – recommendation per person:",
        "dep_status_few": "{name}: not enough data yet ({count}× leaving) – the recommendation "
        "comes after at least 3× leaving and 2 days.",
        "dep_status_none": "{name}: has not left yet since the measurement started.",
        "dep_status_ok": "{name}: leaving is detected reliably – recommended waiting time "
        "{minutes} min (from {count}× leaving).",
        "dep_status_slow": "{name}: the signals notice leaving only after up to {needed} min – "
        "longer than the longest waiting time (15 min). Tip: set up a faster signal, e.g. the "
        "Wi-Fi sensor of the Companion app.",
        "dep_status_pauses": "{name}: all signals were silent {pauses}× for longer than "
        "{minutes} min without a door opening. Leaving could not be told apart from a break-in "
        "reliably. Tip: set up a second signal, e.g. the Companion app with its Wi-Fi sensor.",
        "dep_left": "{who}: “away” {seconds} s after opening ({door})",
        "dep_pause": "{who}: silent pause without door, {minutes} min",
        "dep_pause_open": "{who}: silent pause without door, for {minutes} min so far",
        "dep_pause_shared": "{who}: silent pause without door, {minutes} min – at the same time "
        "as others (Wi-Fi outage?)",
        "dep_pause_shared_open": "{who}: silent pause without door, for {minutes} min so far – "
        "at the same time as others (Wi-Fi outage?)",
        "dep_csv_kind": "Leaving",
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
