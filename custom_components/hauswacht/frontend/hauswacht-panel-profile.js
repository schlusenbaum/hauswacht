// Hauswacht – Einstellungsseite, Stufe 3: Alarmprofile bearbeiten (ADR 0011).
//
// Seitenblatt <hauswacht-profile-editor> mit allen Einstellungen eines Profils, in Abschnitten
// wie im Dialog. Gespeichert wird über hauswacht/settings/apply (save_profile – dieselbe
// Prüfung wie im Dialog). Nur stabile Bausteine: eigene Elemente, Farben des Themas.

const PT = {
  de: {
    titleNew: "Alarmprofil anlegen",
    titleEdit: "Alarmprofil bearbeiten",
    save: "Speichern",
    saving: "Speichere …",
    cancel: "Abbrechen",
    delete: "Löschen",
    deleteConfirm: "Profil wirklich löschen?",
    secGeneral: "Allgemein",
    secWatch: "Was wird überwacht",
    secTimes: "Zeiten",
    secArming: "Beim Scharfschalten",
    secReaction: "Reaktion bei Alarm",
    secAuto: "Automatik",
    secClose: "Scharf durch Schließen der Tür",
    secPassage: "Durchgang – rein oder raus, bleibt scharf",
    passageOn: "Durchgang erlauben",
    passageHint: "Gedacht für Profile, die nur die Außenhaut überwachen: Melder im Haus bleiben scharf – der Durchgang hilft nur an den Außentüren. Reinkommen: in der Eingangsverzögerung PIN oder Karte und eine Profil-Taste (oder die Durchgang-Taste) am Keypad. Rausgehen: solange scharf, PIN oder Karte und irgendeine Profil-Taste (es wird nie umgeschaltet) oder die Durchgang-Taste.",
    passageDuration: "Durchgangszeit (Minuten)",
    passageOutDoors: "Rausgehen: welche Tür",
    passageOutEnd: "Rausgehen: Ende",
    passagePath: "Melder auf dem Weg (z. B. Bewegungsmelder in der Einfahrt)",
    passagePathAfter: "Reinkommen: Weg noch frei nach dem Schließen (s)",
    outDoors: { first: "nur die erste Tür, die aufgeht", all: "alle Eingangstüren" },
    outEnd: { time: "nach Ablauf der Zeit", returned: "schon, wenn ich zurück bin und die Tür zu ist" },
    name: "Name",
    icon: "Symbol (z. B. mdi:weather-night)",
    button: "Knopf am Bedienfeld",
    area: "Bereich",
    zones: "Meldergruppen – jeder Melder löst allein aus",
    excluded: "Ausgenommen (lösen in diesem Profil nicht allein aus)",
    noMembers: "Erst Meldergruppen wählen.",
    rules: "Auslöseregeln",
    tilt: "Gekippte Fenster erlaubt (gekippt zählt als zu, erst ganz öffnen löst aus)",
    exit: "Ausgangsverzögerung (s)",
    entry: "Eingangsverzögerung (s)",
    reaction: "Dauer der Alarmreaktion (s)",
    cycles: "Höchstzahl Alarmzyklen",
    openPolicy: "Offene Melder beim Scharfschalten",
    unavailablePolicy: "Ausgefallene Melder beim Scharfschalten",
    tamper: "Manipulation (Sabotage) löst Alarm aus",
    sirens: "Sirenen",
    noSirens: "Keine Sirenen eingetragen (Reiter Alarmgeber).",
    tone: "Ton",
    volume: "Lautstärke",
    silent: "Stiller Alarm (keine Sirene, nur Benachrichtigung)",
    notify: "Benachrichtigen bei Alarm",
    speakers: "Zusätzliche Lautsprecher (Ansagen)",
    armTime: "Scharf um",
    disarmTime: "Unscharf um",
    weekdays: "An diesen Tagen (keiner = täglich)",
    schedule: "Oder nach Zeitplan",
    noSchedule: "– kein Zeitplan –",
    scheduleCreate: "Zeitplan anlegen ↗",
    scheduleHint: "Öffnet die Helfer in einem neuen Fenster: „Helfer erstellen“ → „Zeitplan“. Danach hier „Liste aktualisieren“ – deine Eingaben bleiben erhalten.",
    refreshLists: "↻ Liste aktualisieren",
    awayEntity: "Eigener Auslöser für „alle weg“ (statt der Personen oben)",
    awayEntityNone: "Keiner – es gelten die Personen oben.",
    awayEntitySearch: "Name oder Entität suchen …",
    awayEntityChosen: "Gewählt:",
    awayEntityClear: "Entfernen",
    awayEntityState: "Dieser Zustand heißt „alle weg“",
    awayEntityStates: { on: "an (on)", off: "aus (off)", not_home: "nicht zuhause (not_home, z. B. Personengruppe)" },
    awayEntityWarn: "Damit prüft Hauswacht nicht mehr selbst, ob wirklich alle weg sind: Zeigt die Entität den Zustand, wird nach der Wartezeit scharf geschaltet – egal, was Handys und Ortungen sagen. Irrt sich die Entität, während jemand zuhause ist, gibt es einen Fehlalarm. Unbekannt oder nicht verfügbar zählt nie als weg.",
    persons: "Scharf, wenn alle diese Personen weg sind",
    awayDelay: "Wartezeit, wenn alle weg sind (min)",
    passagePhoneMoved: "Handy-Reinlassen ist umgezogen: oben bei „Bei Rückkehr“ → „Reinlassen (Durchgang)“.",
    secReturn: "Bei Rückkehr",
    returnIntro: "Was Hauswacht tut, wenn eine bestimmte Person nach Hause kommt. Grundlage ist der Personen-Status in Home Assistant (meist das Handy).",
    returnMode: "Wenn jemand heimkommt",
    returnPersons: "Für diese Personen",
    returnWindow: "Zeitfenster Handy und Tür (Minuten)",
    returnWindowRec: "Empfehlung: 5 Minuten. Länger macht es bequemer, aber auch etwas unsicherer.",
    returnAlwaysWarn: "Achtung: In diesem Modus reicht das Handy allein. Wer das Handy einer Person hat (oder es verliert und jemand findet es), kann nach Hause kommen und die Anlage schaltet unscharf – ohne Tür, ohne PIN. Sicherer ist „Unscharf mit Türbeleg“.",
    moreSettings: "Mehr Einstellungen",
    howLabel: "So verhält sich das:",
    infoLabel: "Erklärung",
    approachDelay: "Eingangsverzögerung nach Annäherung (Sekunden, 0 = aus)",
    approachValid: "Annäherung gilt (Minuten)",
    approachDelayRec: "Empfehlung aus der Messung: {r} s (längste Zeit „Tür auf“ bis „zuhause“ plus Puffer).",
    approachDelayRecDefault: "Noch keine Messung. Typisch: 60–120 s. Empfehlung kommt, sobald die Personen in der Heimkehr-Beobachtung sind und ein paar Mal heimgekommen sind.",
    approachValidRec: "Empfehlung aus der Messung: {r} min (längste Zeit „nähert sich“ bis zur Tür plus 5 min).",
    approachValidRecDefault: "Empfehlung: 15 Minuten.",
    approachTooShort: "Wirkt nicht: nicht länger als die normale Eingangsverzögerung ({n} s). Verlängert wird nur, nie verkürzt.",
    approachHow: "Hat sich eine der Personen in den letzten {v} Minuten genähert (Richtung „nähert sich“), wartet Hauswacht nach dem Öffnen {s} s statt {n} s auf das Handy. Wer sich nicht genähert hat – etwa ein Einbrecher –, hat weiter nur {n} s.",
    apply: "übernehmen",
    noFix: "⚠ keine Ortung – gilt nie als weg",
    noFixHint: "Hauswacht findet für diese Person keine Ortung mit Koordinaten (z. B. Companion App mit Standort). Ohne Ortung außerhalb gilt sie nie als weg: „Scharf, wenn alle weg“ wartet dann für immer, „Bei Rückkehr“ löst nie aus. Abhilfe: in der Companion App den Standort auf „Immer“ stellen oder unter System → Anwesenheit einen GPS-Tracker als Signal eintragen.",
    returnModes: { off: "Nichts", auto_only: "Unscharf, nur wenn automatisch scharf", door: "Unscharf mit Türbeleg", always: "Unscharf, auch nach Scharfschalten von Hand", passage: "Reinlassen (Durchgang)" },
    returnHow: {
      off: "Hauswacht tut nichts, wenn jemand heimkommt. Unscharf geht nur per PIN, Karte, Keypad oder App.",
      auto_only: "Kommt eine der Personen heim, schaltet Hauswacht unscharf – aber nur, wenn das Profil vorher automatisch scharf geworden ist (zum Beispiel, weil alle weg waren). Hast du von Hand scharf geschaltet, bleibt es scharf.",
      door: "Meldet das Handy einer Person „zuhause“ und geht höchstens {w} Minuten davor oder danach eine Eingangstür auf, schaltet Hauswacht unscharf – auch wenn von Hand scharf geschaltet wurde. Ohne Türöffnung passiert nichts. Beispiel: Du fährst in die Einfahrt, das Handy meldet „zuhause“, du schließt die Haustür auf – unscharf, kein Alarm.",
      always: "Meldet das Handy einer Person „zuhause“ und war sie vorher mindestens 5 Minuten weg, schaltet Hauswacht sofort unscharf – egal wie scharf geschaltet wurde. Eine Tür muss dafür nicht aufgehen.",
      passage: "Geht eine Eingangstür auf und meldet das Handy einer Person bis zu {w} Minuten vorher oder noch während der Eingangsverzögerung „zuhause“ (vorher mindestens 5 Minuten weg), lässt Hauswacht sie ohne PIN herein. Das Profil bleibt scharf – wie beim Durchgang. Kommt das Handy nicht rechtzeitig, gibt es Alarm wie immer.",
    },
    how: {
      times: "Nach dem Scharfschalten hast du {exit} s zum Verlassen. Öffnest du danach eine Eingangstür, hast du {entry} s zum Unscharfschalten. Ein Alarm läuft {reaction} s, insgesamt höchstens {cycles}×, bis jemand unscharf schaltet.",
      open: { refuse: "Ist beim Scharfschalten etwas offen, schaltet Hauswacht nicht scharf.", confirm: "Ist beim Scharfschalten etwas offen, fragt Hauswacht nach („Trotzdem scharf“).", bypass_auto: "Ist beim Scharfschalten etwas offen, wird es ohne Rückfrage überbrückt – das ist eine Lücke, bis es zu ist." },
      unavailable: { refuse: "Ein ausgefallener Melder verhindert das Scharfschalten.", confirm: "Bei einem ausgefallenen Melder fragt Hauswacht nach.", bypass_auto: "Ein ausgefallener Melder wird ohne Rückfrage überbrückt (Experten)." },
      tamperOn: "Manipulation löst Alarm aus.",
      tamperOff: "Manipulation wird nur gemeldet.",
      sirens: "Bei einem Alarm gehen {n} Sirene(n) an.",
      noSirens: "Bei einem Alarm geht keine Sirene an.",
      silent: "Stiller Alarm: keine Sirene.",
      notify: "{n} Empfänger bekommen eine Push-Nachricht.",
      noNotify: "Niemand bekommt eine Push-Nachricht – bitte mindestens einen Empfänger wählen.",
      autoOff: "Keine Automatik: Dieses Profil schaltest du nur von Hand.",
      autoSchedule: "Scharf und unscharf nach dem Zeitplan.",
      daily: "täglich",
      autoArm: "Scharf um {t} ({days}).",
      autoDisarm: "Unscharf um {t} ({days}).",
      autoAway: "Scharf, wenn alle {n} Personen {m} Minuten sicher weg sind.",
      closeOff: "Aus: Nach dem Scharfschalten läuft immer die volle Ausgangsverzögerung.",
      closeOn: "Tür auf, raus, Tür zu – {s} s später ist die Anlage scharf, statt nach {exit} s Ausgangsverzögerung.",
      closeNoDoors: "An, aber noch keine Ausgangstür gewählt.",
      passageOff: "Aus: Wer rein oder raus will, schaltet unscharf.",
      passageOn: "Rein oder raus ohne unscharf: Die Tür ist {m} Minuten frei, {which}, Ende {end}. {n} Melder auf dem Weg sind frei, nach dem Schließen noch {after} s. Alles andere bleibt scharf.",
      passageWhich: { first: "nur die erste Tür", all: "alle Eingangstüren" },
      passageEnd: { time: "nach Ablauf der Zeit", returned: "sobald du zurück bist" },
    },
    info: {
      name: "So heißt das Profil in der Auswahl, in Nachrichten und am Bedienfeld. Bitte kein Profil „Unscharf“ anlegen – unscharf ist der Grundzustand, kein Profil.",
      icon: "Symbol des Profils, z. B. mdi:shield-moon. Leer lassen geht auch.",
      panel_mode: "Welcher Knopf am Bedienfeld (Alarmkarte, Keypad-Taste) dieses Profil scharf schaltet. Jeder Knopf gehört höchstens einem Profil. Ohne Knopf erreichst du das Profil über die Auswahlliste „Profil“.",
      area: "Nur bei mehreren Bereichen: zu welchem Bereich (z. B. Haus, Garage) das Profil gehört.",
      zones: "Jeder Melder dieser Gruppen löst in diesem Profil allein aus – eine Tür mit Eingangsverzögerung, ein Fenster sofort. Ohne Gruppe und ohne Auslöseregel lässt sich das Profil nicht scharf schalten.",
      excluded: "Melder aus den gewählten Gruppen, die in diesem Profil NICHT allein auslösen – z. B. der Bewegungsmelder im Flur oben bei „Nacht“. In Auslöseregeln zählen sie weiter.",
      rules: "Zusätzlich zu den Gruppen: Abfolgen von Meldern, die gemeinsam einen Alarm auslösen (z. B. erst Gartentor, dann Terrassentür).",
      tilt_allowed: "An: Ein gekipptes Fenster zählt als zu, erst ganz öffnen löst aus – typisch für „Nacht“. Aus: gekippt zählt wie offen – typisch für „Abwesend“.",
      exit_delay: "So viele Sekunden hast du nach dem Scharfschalten, um das Haus zu verlassen. Erst danach wird überwacht. 0 = sofort scharf.",
      entry_delay: "So viele Sekunden hast du nach dem Öffnen einer Eingangstür, um unscharf zu schalten, bevor Alarm kommt. Fenster und andere Melder lösen trotzdem sofort aus.",
      reaction_time: "So lange laufen Sirenen und Ansagen bei einem Alarm. Danach gehen die Sirenen aus; die Anlage bleibt im Alarmzustand, bis jemand unscharf schaltet.",
      max_alarm_cycles: "Wie viele Alarme insgesamt, bis jemand unscharf schaltet. Löst nach dem ersten Alarm erneut ein Melder aus, beginnt ein neuer Durchlauf – höchstens so oft. Schützt Nachbarn vor endlosem Sirenenlärm.",
      open_policy: "Was passiert, wenn beim Scharfschalten noch ein Fenster oder eine Tür offen ist: verweigern (sicher), nach Bestätigung erlauben („Trotzdem scharf“) oder automatisch überbrücken. Überbrückte Melder sind eine Lücke, bis sie geschlossen werden.",
      unavailable_policy: "Was passiert, wenn ein Melder beim Scharfschalten nicht erreichbar ist (z. B. leere Batterie). Ein ausgefallener Melder ist eine Lücke, bis er sich wieder meldet. „Automatisch überbrücken“ nur, wenn du weißt, was du tust.",
      tamper_triggers_alarm: "An: Manipulation (Gehäuse geöffnet, Sabotage) löst Alarm aus, wenn das Profil scharf ist. Aus: Manipulation wird nur gemeldet. Gemeldet wird sie immer, auch unscharf.",
      sirens: "Diese Sirenen gehen bei einem Alarm an. Ohne Freigabe „Echte Sirenenansteuerung erlauben“ (System) sendet Hauswacht keinen Sirenenbefehl.",
      silent: "Stiller Alarm: keine Sirene, nur Benachrichtigungen. Gut, wenn z. B. ein Hund im Haus ist oder du erst selbst nachsehen willst.",
      notify: "Diese Empfänger bekommen bei einem Alarm in diesem Profil eine Push-Nachricht.",
      siren_tone: "Welcher Ton bei einem Einbruch läuft. Ein Brandton wird nie automatisch gewählt.",
      siren_volume: "Lautstärke der Sirenen in diesem Profil – nur bei Sirenen, die das unterstützen.",
      speakers: "Zusätzliche Lautsprecher für Ansagen dieses Profils (z. B. „Achtung, Einbruch“).",
      auto_arm_time: "Uhrzeit, zu der Hauswacht dieses Profil scharf schaltet – nur wenn die Anlage dann unscharf ist. Leer = aus.",
      auto_disarm_time: "Uhrzeit, zu der Hauswacht dieses Profil unscharf schaltet – auch wenn du es von Hand scharf geschaltet hast, aber nie während Eingangsverzögerung oder Alarm. Leer = aus.",
      auto_weekdays: "An diesen Tagen gelten die Uhrzeiten. Keiner angehakt = täglich. Liegt „Unscharf um“ vor „Scharf um“ (über Nacht), gehört der Morgen zur Nacht davor.",
      auto_schedule: "Für je Wochentag andere Zeiten: ein Zeitplan-Helfer von Home Assistant. Beginn eines Zeitblocks = scharf, Ende = unscharf. Die Wochentage oben gelten dafür nicht.",
      auto_away_persons: "Sind alle gewählten Personen sicher weg (mit Beleg, siehe System → Anwesenheit), schaltet Hauswacht nach der Wartezeit scharf. Unbekannt oder nicht verfügbar zählt nie als weg.",
      auto_away_delay: "So lange müssen alle weg sein, bevor scharf geschaltet wird. Kommt in der Zeit jemand zurück, passiert nichts. Fängt auch kurze Aussetzer von Handys ab.",
      close_enabled: "An: Nach dem Scharfschalten genügt es, durch eine Ausgangstür zu gehen und sie zu schließen – dann ist die Anlage scharf, ohne die volle Ausgangsverzögerung abzuwarten. Die Ausgangstüren dürfen beim Scharfschalten offen sein.",
      close_doors: "Durch diese Türen gehst du beim Verlassen, z. B. Haustür vorne und hinten.",
      close_settle: "So lange muss die Tür nach dem Schließen zu bleiben, bevor scharf geschaltet wird. Geht sie vorher wieder auf, beginnt die Zeit neu.",
      passage_enabled: "An: In diesem Profil darf man rein oder raus, ohne unscharf zu schalten – mit PIN und Profil-Taste am Keypad, per Push-Knopf „Reinlassen“, Türschloss oder „Bei Rückkehr: Reinlassen“. Alles andere bleibt scharf.",
      passage_duration: "Rausgehen: so lange ist die Tür frei. Reinkommen: so lange darf die Tür offen stehen, bevor eine Warnung kommt.",
      passage_path_after: "Reinkommen: so lange bleiben die Melder auf dem Weg noch frei, nachdem die Tür zu ist.",
      passage_path: "Außenmelder, die auf dem Weg auslösen würden – z. B. Bewegungsmelder in der Einfahrt oder an den Mülltonnen. Sie sind während des Durchgangs frei.",
      passage_out_doors: "Rausgehen: nur die erste Tür, die aufgeht, ist frei (sicherer) – oder alle Eingangstüren.",
      passage_out_end: "Rausgehen endet nach Ablauf der Zeit (mehrmals raus und rein möglich) – oder schon, wenn du zurück bist und die Tür zu ist.",
      mode: "Wähle, wie Hauswacht reagiert, wenn eine der Personen unten heimkommt. „Unscharf mit Türbeleg“ ist für die meisten Häuser die beste Wahl: Es braucht das Handy UND eine Tür. „Reinlassen (Durchgang)“ passt zu Nachtprofilen, in denen der Rest im Haus scharf bleiben soll.",
      persons: "Nur diese Personen lösen „Bei Rückkehr“ aus. Die Liste ist unabhängig von „Scharf, wenn alle diese Personen weg sind“. Ohne Person lässt sich der Modus nicht speichern.",
      approachDelay: "Braucht einen Richtungs-Sensor der Person (Integration „Nähe“ oder Places) unter System → Anwesenheit. Meldet er „nähert sich“ und geht danach eine Eingangstür auf, bekommt die Person so viel Zeit, bis ihr Handy „zuhause“ meldet. Die Richtung allein schaltet nie unscharf. Nur länger als die normale Eingangsverzögerung wirkt.",
      approachValid: "So lange nach „nähert sich“ gilt die Annäherung. Zu kurz: Wer langsam kommt (Parkplatz suchen), bekommt keine Verlängerung. Zu lang: Die längere Zeit gilt auch noch für eine spätere Türöffnung.",
      window: "So weit dürfen Handy-Meldung „zuhause“ und Türöffnung auseinanderliegen. Manche Handys melden erst spät. Zu kurz: Hauswacht erkennt dich nicht. Zu lang: ein größeres Fenster für Fremde.",
    },
    closeOn: "Ausgangsverzögerung endet, sobald die Tür zu ist",
    doors: "Ausgangstüren",
    noDoors: "In den gewählten Gruppen gibt es keine Melder vom Typ Tür.",
    settle: "Beruhigungszeit (s)",
    none: "–",
    modes: { none: "kein Knopf", home: "Zuhause", night: "Nacht", away: "Abwesend", vacation: "Urlaub", custom: "Benutzerdefiniert" },
    policy: { refuse: "verweigern", confirm: "nach Bestätigung erlauben", bypass_auto: "automatisch überbrücken" },
    experts: " (Experten – wird wieder überwacht, sobald er sich meldet)",
    tones: { burglar: "Einbruch", emergency: "Notfall", police_panic: "Polizei-Panik", emergency_panic: "Notfall-Panik" },
    volumes: { low: "leise", medium: "mittel", high: "laut", very_high: "sehr laut" },
    days: { mon: "Mo", tue: "Di", wed: "Mi", thu: "Do", fri: "Fr", sat: "Sa", sun: "So" },
    errors: {
      profile_name_required: "Bitte einen Namen eingeben.",
      profile_name_taken: "Diesen Namen gibt es schon.",
      panel_mode_taken: "Diesen Knopf hat in diesem Bereich schon ein anderes Profil.",
      excluded_not_in_groups: "Ausgenommene Melder müssen in den gewählten Gruppen sein.",
      return_needs_persons: "„Bei Rückkehr“ braucht mindestens eine Person – bitte bei „Für diese Personen“ eine ankreuzen.",
      unknown_profile: "Dieses Profil gibt es nicht mehr.",
      disarm_first: "Erst alle Bereiche unscharf schalten – dann lässt sich speichern.",
      changed_elsewhere: "Inzwischen wurde woanders etwas geändert. Die Seite lädt neu – bitte noch einmal.",
      failed: "Speichern fehlgeschlagen.",
    },
  },
  en: {
    titleNew: "Add alarm profile",
    titleEdit: "Edit alarm profile",
    save: "Save",
    saving: "Saving …",
    cancel: "Cancel",
    delete: "Delete",
    deleteConfirm: "Really delete the profile?",
    secGeneral: "General",
    secWatch: "What is monitored",
    secTimes: "Times",
    secArming: "When arming",
    secReaction: "Reaction on alarm",
    secAuto: "Automation",
    secClose: "Arm by closing the door",
    secPassage: "Passage – in or out, stays armed",
    passageOn: "Allow passage",
    passageHint: "Meant for profiles that only watch the outer shell: sensors inside stay armed – the passage only helps at the outer doors. Coming in: during the entry delay, PIN or card and any profile key (or the passage key) at the keypad. Going out: while armed, PIN or card and any profile key (never switches profile) or the passage key.",
    passageDuration: "Passage time (minutes)",
    passageOutDoors: "Going out: which door",
    passageOutEnd: "Going out: end",
    passagePath: "Sensors on the way (e.g. motion sensor in the driveway)",
    passagePathAfter: "Coming in: way still free after closing (s)",
    outDoors: { first: "only the first door that opens", all: "all entry doors" },
    outEnd: { time: "when the time is up", returned: "as soon as I am back and the door is closed" },
    name: "Name",
    icon: "Icon (e.g. mdi:weather-night)",
    button: "Button on the alarm panel",
    area: "Area",
    zones: "Sensor groups – every sensor triggers on its own",
    excluded: "Excluded (do not trigger on their own in this profile)",
    noMembers: "Choose sensor groups first.",
    rules: "Trigger rules",
    tilt: "Tilted windows allowed (tilted counts as closed, only opening fully triggers)",
    exit: "Exit delay (s)",
    entry: "Entry delay (s)",
    reaction: "Duration of the alarm reaction (s)",
    cycles: "Maximum alarm cycles",
    openPolicy: "Open sensors when arming",
    unavailablePolicy: "Failed sensors when arming",
    tamper: "Tampering triggers an alarm",
    sirens: "Sirens",
    noSirens: "No sirens registered (tab alarm devices).",
    tone: "Tone",
    volume: "Volume",
    silent: "Silent alarm (no siren, notification only)",
    notify: "Notify on alarm",
    speakers: "Additional speakers (announcements)",
    armTime: "Arm at",
    disarmTime: "Disarm at",
    weekdays: "On these days (none = daily)",
    schedule: "Or by schedule",
    noSchedule: "– no schedule –",
    scheduleCreate: "Create schedule ↗",
    scheduleHint: "Opens the helpers in a new window: “Create helper” → “Schedule”. Then “Refresh list” here – your entries are kept.",
    refreshLists: "↻ Refresh list",
    awayEntity: "Own trigger for “all away” (instead of the persons above)",
    awayEntityNone: "None – the persons above apply.",
    awayEntitySearch: "Search name or entity …",
    awayEntityChosen: "Chosen:",
    awayEntityClear: "Remove",
    awayEntityState: "This state means “all away”",
    awayEntityStates: { on: "on", off: "off", not_home: "not home (not_home, e.g. a person group)" },
    awayEntityWarn: "Hauswacht then no longer checks itself whether everyone is really away: when the entity shows the state, it arms after the waiting time – whatever phones and locations say. If the entity is wrong while someone is home, there is a false alarm. Unknown or unavailable never counts as away.",
    persons: "Arm when all these persons are away",
    awayDelay: "Waiting time when everyone is away (min)",
    passagePhoneMoved: "Letting in by phone has moved: above at “On return” → “Let in (passage)”.",
    secReturn: "On return",
    returnIntro: "What Hauswacht does when a certain person comes home. It is based on the person state in Home Assistant (usually the phone).",
    returnMode: "When someone comes home",
    returnPersons: "For these persons",
    returnWindow: "Time window phone and door (minutes)",
    returnWindowRec: "Recommendation: 5 minutes. Longer is more convenient, but also a bit less secure.",
    returnAlwaysWarn: "Caution: in this mode the phone alone is enough. Whoever has a person's phone (or finds a lost one) can come home and the system disarms – without door, without PIN. “Disarm with door proof” is safer.",
    moreSettings: "More settings",
    howLabel: "This is how it behaves:",
    infoLabel: "Explanation",
    approachDelay: "Entry delay after approach (seconds, 0 = off)",
    approachValid: "Approach is valid for (minutes)",
    approachDelayRec: "Recommendation from the measurement: {r} s (longest time “door open” to “home” plus buffer).",
    approachDelayRecDefault: "No measurement yet. Typical: 60–120 s. A recommendation appears once the persons are in the homecoming observation and have come home a few times.",
    approachValidRec: "Recommendation from the measurement: {r} min (longest time “approaching” to the door plus 5 min).",
    approachValidRecDefault: "Recommendation: 15 minutes.",
    approachTooShort: "Has no effect: not longer than the normal entry delay ({n} s). It only extends, never shortens.",
    approachHow: "If one of the persons approached in the last {v} minutes (direction “towards”), Hauswacht waits {s} s instead of {n} s for the phone after the door opens. Whoever did not approach – such as a burglar – still only has {n} s.",
    apply: "apply",
    noFix: "⚠ no location – never counts as away",
    noFixHint: "Hauswacht finds no location with coordinates for this person (e.g. Companion app with location). Without a location outside, the person never counts as away: “arm when all away” then waits forever, “On return” never triggers. Fix: set the location in the Companion app to “Always” or add a GPS tracker as a signal under System → Presence.",
    returnModes: { off: "Nothing", auto_only: "Disarm, only if armed automatically", door: "Disarm with door proof", always: "Disarm, also after arming by hand", passage: "Let in (passage)" },
    returnHow: {
      off: "Hauswacht does nothing when someone comes home. Disarming only by PIN, card, keypad or app.",
      auto_only: "If one of the persons comes home, Hauswacht disarms – but only if the profile was armed automatically before (for example because everyone was away). If you armed by hand, it stays armed.",
      door: "If a person's phone reports “home” and an entry door opens at most {w} minutes before or after, Hauswacht disarms – even if armed by hand. Without a door opening nothing happens. Example: you drive into the driveway, the phone reports “home”, you unlock the front door – disarmed, no alarm.",
      always: "If a person's phone reports “home” and the person was away for at least 5 minutes before, Hauswacht disarms right away – no matter how it was armed. No door needs to open.",
      passage: "If an entry door opens and a person's phone reports “home” up to {w} minutes before or while the entry delay is still running (away for at least 5 minutes before), Hauswacht lets them in without PIN. The profile stays armed – like a passage. If the phone is too late, the alarm comes as always.",
    },
    how: {
      times: "After arming you have {exit} s to leave. If you then open an entry door, you have {entry} s to disarm. An alarm runs {reaction} s, at most {cycles}× in total until someone disarms.",
      open: { refuse: "If something is open when arming, Hauswacht does not arm.", confirm: "If something is open when arming, Hauswacht asks (“Arm anyway”).", bypass_auto: "If something is open when arming, it is bypassed without asking – a gap until it is closed." },
      unavailable: { refuse: "A failed sensor prevents arming.", confirm: "With a failed sensor Hauswacht asks.", bypass_auto: "A failed sensor is bypassed without asking (experts)." },
      tamperOn: "Tampering triggers an alarm.",
      tamperOff: "Tampering is only reported.",
      sirens: "During an alarm {n} siren(s) go on.",
      noSirens: "During an alarm no siren goes on.",
      silent: "Silent alarm: no siren.",
      notify: "{n} recipient(s) get a push message.",
      noNotify: "Nobody gets a push message – please choose at least one recipient.",
      autoOff: "No automation: you arm this profile by hand only.",
      autoSchedule: "Armed and disarmed by the schedule.",
      daily: "daily",
      autoArm: "Arm at {t} ({days}).",
      autoDisarm: "Disarm at {t} ({days}).",
      autoAway: "Arm when all {n} persons have been reliably away for {m} minutes.",
      closeOff: "Off: after arming, the full exit delay always runs.",
      closeOn: "Door open, out, door closed – {s} s later the system is armed instead of after the {exit} s exit delay.",
      closeNoDoors: "On, but no exit door chosen yet.",
      passageOff: "Off: whoever wants to go in or out disarms.",
      passageOn: "In or out without disarming: the door is free for {m} minutes, {which}, ending {end}. {n} sensor(s) on the way are free, after closing for {after} s more. Everything else stays armed.",
      passageWhich: { first: "only the first door", all: "all entry doors" },
      passageEnd: { time: "when the time is up", returned: "as soon as you are back" },
    },
    info: {
      name: "How the profile is called in the list, in messages and on the panel. Please do not create a profile “Disarmed” – disarmed is the basic state, not a profile.",
      icon: "Icon of the profile, e.g. mdi:shield-moon. Leaving it empty is fine.",
      panel_mode: "Which button on the panel (alarm card, keypad key) arms this profile. Each button belongs to at most one profile. Without a button you reach the profile via the “Profile” list.",
      area: "Only with several areas: which area (e.g. house, garage) the profile belongs to.",
      zones: "Every sensor of these groups triggers on its own in this profile – a door with entry delay, a window at once. Without a group and without a trigger rule the profile cannot be armed.",
      excluded: "Sensors from the chosen groups that do NOT trigger on their own in this profile – e.g. the motion sensor in the upstairs hallway for “Night”. They still count in trigger rules.",
      rules: "In addition to the groups: sequences of sensors that trigger an alarm together (e.g. first the garden gate, then the patio door).",
      tilt_allowed: "On: a tilted window counts as closed, only fully opening triggers – typical for “Night”. Off: tilted counts as open – typical for “Away”.",
      exit_delay: "This many seconds you have after arming to leave the house. Monitoring only starts afterwards. 0 = armed at once.",
      entry_delay: "This many seconds you have after opening an entry door to disarm before the alarm comes. Windows and other sensors still trigger at once.",
      reaction_time: "This long sirens and announcements run during an alarm. Afterwards the sirens go off; the system stays in the alarm state until someone disarms.",
      max_alarm_cycles: "How many alarms in total until someone disarms. If a sensor triggers again after the first alarm, a new round starts – at most this often. Protects the neighbours from endless siren noise.",
      open_policy: "What happens when a window or door is still open when arming: refuse (safe), allow after confirmation (“Arm anyway”) or bypass automatically. Bypassed sensors are a gap until they are closed.",
      unavailable_policy: "What happens when a sensor cannot be reached when arming (e.g. empty battery). A failed sensor is a gap until it reports again. “Bypass automatically” only if you know what you are doing.",
      tamper_triggers_alarm: "On: tampering (case opened, sabotage) triggers an alarm while the profile is armed. Off: tampering is only reported. It is always reported, also when disarmed.",
      sirens: "These sirens go on during an alarm. Without the release “Allow real siren control” (System), Hauswacht sends no siren command.",
      silent: "Silent alarm: no siren, only notifications. Good e.g. when a dog is in the house or you want to check yourself first.",
      notify: "These recipients get a push message during an alarm in this profile.",
      siren_tone: "Which tone plays for a burglary. A fire tone is never chosen automatically.",
      siren_volume: "Volume of the sirens in this profile – only for sirens that support it.",
      speakers: "Additional speakers for announcements of this profile (e.g. “Attention, burglary”).",
      auto_arm_time: "Time at which Hauswacht arms this profile – only if the system is disarmed then. Empty = off.",
      auto_disarm_time: "Time at which Hauswacht disarms this profile – also if you armed it by hand, but never during the entry delay or an alarm. Empty = off.",
      auto_weekdays: "The times apply on these days. None ticked = daily. If “Disarm at” is before “Arm at” (overnight), the morning belongs to the night before.",
      auto_schedule: "For different times per weekday: a schedule helper of Home Assistant. Start of a time block = armed, end = disarmed. The weekdays above do not apply to it.",
      auto_away_persons: "When all chosen persons are reliably away (with proof, see System → Presence), Hauswacht arms after the waiting time. Unknown or unavailable never counts as away.",
      auto_away_delay: "This long everyone has to be away before arming. If someone comes back in that time, nothing happens. Also absorbs short dropouts of phones.",
      close_enabled: "On: after arming it is enough to go through an exit door and close it – then the system is armed without waiting for the full exit delay. The exit doors may be open when arming.",
      close_doors: "You leave through these doors, e.g. front and back door.",
      close_settle: "This long the door has to stay closed after closing before arming. If it opens again before, the time starts over.",
      passage_enabled: "On: in this profile you may go in or out without disarming – with PIN and profile key on the keypad, the push button “Let in”, a door lock or “On return: let in”. Everything else stays armed.",
      passage_duration: "Going out: this long the door is free. Coming in: this long the door may stand open before a warning comes.",
      passage_path_after: "Coming in: this long the sensors on the way stay free after the door is closed.",
      passage_path: "Outdoor sensors that would trigger on the way – e.g. motion sensors in the driveway or at the bins. They are free during the passage.",
      passage_out_doors: "Going out: only the first door that opens is free (safer) – or all entry doors.",
      passage_out_end: "Going out ends when the time is up (in and out several times possible) – or already when you are back and the door is closed.",
      mode: "Choose how Hauswacht reacts when one of the persons below comes home. “Disarm with door proof” is the best choice for most homes: it needs the phone AND a door. “Let in (passage)” suits night profiles in which the rest of the house should stay armed.",
      persons: "Only these persons trigger “On return”. The list is independent of “Arm when all these persons are away”. Without a person the mode cannot be saved.",
      approachDelay: "Needs a direction sensor of the person (Proximity integration or Places) under System → Presence. If it reports “towards” and an entry door opens afterwards, the person gets this much time until their phone reports “home”. The direction alone never disarms. Only longer than the normal entry delay has an effect.",
      approachValid: "How long an approach stays valid after “towards”. Too short: whoever comes slowly (looking for parking) gets no extension. Too long: the longer time also applies to a later door opening.",
      window: "How far apart the phone reporting “home” and the door opening may be. Some phones report late. Too short: Hauswacht does not recognise you. Too long: a bigger window for strangers.",
    },
    closeOn: "Exit delay ends as soon as the door is closed",
    doors: "Exit doors",
    noDoors: "The chosen groups contain no sensors of type door.",
    settle: "Settle time (s)",
    none: "–",
    modes: { none: "no button", home: "Home", night: "Night", away: "Away", vacation: "Vacation", custom: "Custom" },
    policy: { refuse: "refuse", confirm: "allow after confirmation", bypass_auto: "bypass automatically" },
    experts: " (experts – monitored again as soon as it reports)",
    tones: { burglar: "Burglar", emergency: "Emergency", police_panic: "Police panic", emergency_panic: "Emergency panic" },
    volumes: { low: "low", medium: "medium", high: "high", very_high: "very high" },
    days: { mon: "Mon", tue: "Tue", wed: "Wed", thu: "Thu", fri: "Fri", sat: "Sat", sun: "Sun" },
    errors: {
      profile_name_required: "Please enter a name.",
      profile_name_taken: "This name already exists.",
      panel_mode_taken: "Another profile in this area already has this button.",
      excluded_not_in_groups: "Excluded sensors must be in the chosen groups.",
      return_needs_persons: "“On return” needs at least one person – please tick one at “For these persons”.",
      unknown_profile: "This profile no longer exists.",
      disarm_first: "Disarm all areas first – then saving works.",
      changed_elsewhere: "Something was changed elsewhere in the meantime. The page reloads – please try again.",
      failed: "Saving failed.",
    },
  },
};

const PROFILE_STYLE = `
  .sec { font-weight: 500; margin: 18px 0 2px; padding-top: 10px; border-top: 1px solid var(--divider-color); }
  .two { display: grid; grid-template-columns: 1fr 1fr; gap: 0 12px; }
  .days { display: flex; gap: 10px; flex-wrap: wrap; }
  .days .chk { padding: 2px 0; }
  .tool { display: flex; gap: 8px; flex-wrap: wrap; }
  a.b { text-decoration: none; font-size: .9rem; padding: 6px 14px; }
  .nofix { margin-left: 8px; font-size: .85rem; color: var(--warning-color, #ff9800); cursor: help; }
  .info { border: none; background: none; color: var(--primary-color); cursor: help; font-size: 1rem; padding: 0 2px; }
  .tip[hidden] { display: none; }
  .tip { display: block; font-weight: normal; font-size: .85rem; margin: 4px 0 6px; padding: 8px 10px; border-radius: 6px; background: var(--secondary-background-color); }
  .how { margin: 8px 0 4px; font-size: .9rem; }
  .warn { margin: 6px 0; padding: 8px 10px; border-radius: 6px; border-left: 3px solid var(--warning-color, #ff9800); background: var(--secondary-background-color); font-size: .9rem; }
  details.more { margin-top: 10px; }
  details.more summary { cursor: pointer; color: var(--primary-color); }
`;

const pe = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

class HauswachtProfileEditor extends HTMLElement {
  // open({hass, settings, profile}) – profile = null: neues Profil
  open(options) {
    Object.assign(this, options);
    const edit = this.settings.profile_edit;
    const base = this.profile ? edit.profiles.find((p) => p.id === this.profile) : null;
    this._draft = JSON.parse(JSON.stringify(base || edit.defaults));
    this._errors = {};
    this._busy = false;
    this._opened = new Set(); // offene „Mehr Einstellungen“
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this._render();
  }

  get _lang() {
    return (this.hass?.language || "en").startsWith("de") ? "de" : "en";
  }

  _t(key) {
    return PT[this._lang][key] ?? PT.en[key] ?? key;
  }

  _name(id) {
    const x = (this.settings.entities || []).find((y) => y.id === id);
    return x ? x.name : id;
  }

  // --- Bausteine ---------------------------------------------------------------

  // Beschriftung mit ⓘ, wenn es zu diesem Feld eine Erklärung gibt (0.62)
  _label(key, label) {
    return `<label>${pe(label)}${this._info(key, true)}</label>`;
  }

  _text(key, value, label) {
    return `${this._label(key, label)}<input data-k="${pe(key)}" value="${pe(value ?? "")}">${this._err(key)}`;
  }

  _num(key, value, label, min, max) {
    return `<div>${this._label(key, label)}<input type="number" min="${min}" max="${max}" data-k="${pe(key)}" data-num="1" value="${pe(value)}"></div>`;
  }

  _select(key, value, label, options) {
    return `${this._label(key, label)}<select data-k="${pe(key)}">${options.map(([v, l]) => `<option value="${pe(v)}" ${v === value ? "selected" : ""}>${pe(l)}</option>`).join("")}</select>${this._err(key)}`;
  }

  _check(key, value, label) {
    return `<div class="chk"><input type="checkbox" data-k="${pe(key)}" data-bool="1" ${value ? "checked" : ""}><span>${pe(label)}${this._info(key, true)}</span></div>`;
  }

  _multi(key, chosen, items, label, empty) {
    const body = items.length
      ? items.map(([v, l]) => `<div class="chk"><input type="checkbox" data-m="${pe(key)}" value="${pe(v)}" ${chosen.includes(v) ? "checked" : ""}><span>${pe(l)}</span></div>`).join("")
      : `<div class="muted">${pe(empty || this._t("none"))}</div>`;
    return `${this._label(key, label)}${body}${this._err(key)}`;
  }

  // „Mehr Einstellungen“ zum Aufklappen; bleibt beim Neuzeichnen offen
  // Eigener Auslöser für „alle weg“: Suchfeld statt langer Liste (Name oder Entitäts-ID tippen)
  _awayEntityPick(c, a) {
    const choices = c.away_entities || [];
    const current = choices.find((x) => x.id === a.auto_away_entity);
    const shown = current ? current.name : a.auto_away_entity || "";
    const options = choices.map((x) => `<option value="${pe(x.name)}">${pe(x.id)}</option>`).join("");
    const chosen = a.auto_away_entity
      ? `<div class="muted">${pe(this._t("awayEntityChosen"))} ${pe(a.auto_away_entity)} <button type="button" class="b" data-act="away-entity-clear">${pe(this._t("awayEntityClear"))}</button></div>`
      : `<div class="muted">${pe(this._t("awayEntityNone"))}</div>`;
    return `<input data-awayent list="hw-prof-awayent" value="${pe(shown)}" placeholder="${pe(this._t("awayEntitySearch"))}" autocomplete="off"><datalist id="hw-prof-awayent">${options}</datalist>${chosen}`;
  }

  _awayEntityValue(text) {
    // Getippt oder gewählt: Name (eindeutig) oder Entitäts-ID; leer = kein eigener Auslöser
    const value = (text || "").trim();
    if (!value) return null;
    const choices = this.settings?.profile_edit?.choices?.away_entities || [];
    const lower = value.toLowerCase();
    const hit = choices.find((x) => x.id === value) || choices.find((x) => x.name.toLowerCase() === lower);
    if (hit) return hit.id;
    return /^[a-z_]+\.[a-z0-9_]+$/.test(value) ? value : this._draft.automation.auto_away_entity || null;
  }

  _more(id, body) {
    return `<details class="more" data-more="${pe(id)}" ${this._opened.has(id) ? "open" : ""}><summary>${pe(this._t("moreSettings"))}</summary>${body}</details>`;
  }

  // „So verhält sich das:“ – ein Satz, der sich mit den Werten sofort ändert
  _how(id) {
    const text = this._howText(id);
    return text ? `<div class="how"><b>${pe(this._t("howLabel"))}</b> <span data-how="${pe(id)}">${pe(text)}</span></div>` : "";
  }

  _howText(id) {
    const d = this._draft;
    const h = this._t("how") || {};
    const fill = (text, values) => Object.entries(values).reduce((acc, [k, v]) => acc.replaceAll(`{${k}}`, String(v)), text || "");
    if (id === "return") return this._returnHow(d.return);
    if (id === "times") {
      return fill(h.times, { exit: d.exit_delay, entry: d.entry_delay, reaction: d.reaction_time, cycles: d.max_alarm_cycles });
    }
    if (id === "arming") {
      return [h.open?.[d.open_policy], h.unavailable?.[d.unavailable_policy], d.tamper_triggers_alarm ? h.tamperOn : h.tamperOff].filter(Boolean).join(" ");
    }
    if (id === "reaction") {
      const sirens = d.silent || !d.sirens.length ? h.noSirens : fill(h.sirens, { n: d.sirens.length });
      const notify = d.notify.length ? fill(h.notify, { n: d.notify.length }) : h.noNotify;
      return `${d.silent ? h.silent : sirens} ${notify}`;
    }
    if (id === "auto") {
      const a = d.automation;
      const parts = [];
      if (a.auto_schedule) parts.push(h.autoSchedule);
      else if (a.auto_arm_time || a.auto_disarm_time) {
        const days = a.auto_weekdays.length ? a.auto_weekdays.map((w) => (this._t("days") || {})[w] || w).join(", ") : h.daily;
        if (a.auto_arm_time) parts.push(fill(h.autoArm, { t: a.auto_arm_time, days }));
        if (a.auto_disarm_time) parts.push(fill(h.autoDisarm, { t: a.auto_disarm_time, days }));
      }
      if (a.auto_away_persons.length) parts.push(fill(h.autoAway, { n: a.auto_away_persons.length, m: a.auto_away_delay }));
      return parts.length ? parts.join(" ") : h.autoOff;
    }
    if (id === "close") {
      const c = d.arm_on_close;
      if (!c.enabled) return h.closeOff;
      return c.doors.length ? fill(h.closeOn, { s: c.settle, exit: d.exit_delay }) : h.closeNoDoors;
    }
    if (id === "passage") {
      const p = d.passage;
      if (!p.enabled) return h.passageOff;
      return fill(h.passageOn, { m: p.duration, which: (h.passageWhich || {})[p.out_doors] || "", end: (h.passageEnd || {})[p.out_end] || "", n: p.path.length, after: p.path_after });
    }
    return "";
  }

  _err(key) {
    const k = this._errors[key];
    return k ? `<div class="err">${pe(this._t("errors")[k] || k)}</div>` : "";
  }

  _members(zones) {
    const s = this.settings;
    const ids = new Set();
    for (const g of s.groups) {
      if (!zones.includes(g.id)) continue;
      for (const id of g.entities || []) ids.add(id);
      for (const id of s.label_members?.[g.id] || []) ids.add(id);
    }
    return [...ids].sort((a, b) => this._name(a).localeCompare(this._name(b)));
  }

  // --- Formular ----------------------------------------------------------------

  _form() {
    const d = this._draft;
    const c = this.settings.profile_edit.choices;
    const lim = this.settings.profile_edit.limits;
    const a = d.automation;
    const close = d.arm_on_close;
    const pass = d.passage;
    const members = this._members(d.zones);
    const doors = members.filter((id) => (this.settings.sensor_types[id] || "") === "door");
    const t = (group, v) => (this._t(group) || {})[v] || v;
    const areas = c.areas.length > 1 ? this._select("area", d.area, this._t("area"), c.areas.map((x) => [x.id, x.name])) : "";
    const inf = (key) => this._info(key, true);
    return `
      <h2>${pe(this.profile ? this._t("titleEdit") : this._t("titleNew"))}</h2>
      <div class="sec">${pe(this._t("secGeneral"))}</div>
      ${this._text("name", d.name, this._t("name"))}
      ${this._select("panel_mode", d.panel_mode, this._t("button"), c.panel_modes.map((m) => [m, t("modes", m)]))}
      ${areas}
      ${this._more("general", this._text("icon", d.icon, this._t("icon")))}
      <div class="sec">${pe(this._t("secWatch"))}</div>
      ${this._multi("zones", d.zones, this.settings.groups.map((g) => [g.id, g.name]), this._t("zones"))}
      ${this._multi("excluded", d.excluded, members.map((id) => [id, this._name(id)]), this._t("excluded"), this._t("noMembers"))}
      ${c.rules.length ? this._multi("rules", d.rules, c.rules.map((r) => [r.id, r.name]), this._t("rules")) : ""}
      ${c.tilt ? this._check("tilt_allowed", d.tilt_allowed, this._t("tilt")) : ""}
      <div class="sec">${pe(this._t("secTimes"))}</div>
      <div class="two">${this._num("exit_delay", d.exit_delay, this._t("exit"), 0, lim.delay)}${this._num("entry_delay", d.entry_delay, this._t("entry"), 0, lim.delay)}</div>
      ${this._how("times")}
      ${this._more("times", `<div class="two">${this._num("reaction_time", d.reaction_time, this._t("reaction"), 1, lim.reaction)}${this._num("max_alarm_cycles", d.max_alarm_cycles, this._t("cycles"), 1, lim.cycles)}</div>`)}
      <div class="sec">${pe(this._t("secArming"))}</div>
      ${this._select("open_policy", d.open_policy, this._t("openPolicy"), c.open_policies.map((p) => [p, t("policy", p)]))}
      ${this._how("arming")}
      ${this._more("arming", `${this._select("unavailable_policy", d.unavailable_policy, this._t("unavailablePolicy"), c.unavailable_policies.map((p) => [p, t("policy", p) + (p === "bypass_auto" ? this._t("experts") : "")]))}
      ${this._check("tamper_triggers_alarm", d.tamper_triggers_alarm, this._t("tamper"))}`)}
      <div class="sec">${pe(this._t("secReaction"))}</div>
      ${this._multi("sirens", d.sirens, c.sirens.map((x) => [x.id, x.name]), this._t("sirens"), this._t("noSirens"))}
      ${this._check("silent", d.silent, this._t("silent"))}
      ${this._multi("notify", d.notify, c.notify.map((x) => [x.id, x.name]), this._t("notify"))}
      ${this._how("reaction")}
      ${this._more("reaction", `<div class="two"><div>${this._select("siren_tone", d.siren_tone, this._t("tone"), c.tones.map((x) => [x, t("tones", x)]))}</div>
      <div>${this._select("siren_volume", d.siren_volume, this._t("volume"), c.volumes.map((x) => [x, t("volumes", x)]))}</div></div>
      ${this._multi("speakers", d.speakers, c.speakers.map((x) => [x.id, x.name]), this._t("speakers"))}`)}
      <div class="sec">${pe(this._t("secAuto"))}</div>
      <div class="two"><div><label>${pe(this._t("armTime"))}${inf("auto_arm_time")}</label><input type="time" data-a="auto_arm_time" value="${pe(a.auto_arm_time || "")}"></div>
      <div><label>${pe(this._t("disarmTime"))}${inf("auto_disarm_time")}</label><input type="time" data-a="auto_disarm_time" value="${pe(a.auto_disarm_time || "")}"></div></div>
      <label>${pe(this._t("weekdays"))}${inf("auto_weekdays")}</label><div class="days">${c.weekdays.map((w) => `<div class="chk"><input type="checkbox" data-am="auto_weekdays" value="${w}" ${a.auto_weekdays.includes(w) ? "checked" : ""}><span>${pe(t("days", w))}</span></div>`).join("")}</div>
      <label>${pe(this._t("persons"))}${inf("auto_away_persons")}</label>${c.persons.map((x) => `<div class="chk"><input type="checkbox" data-am="auto_away_persons" value="${pe(x.id)}" ${a.auto_away_persons.includes(x.id) ? "checked" : ""}><span>${pe(x.name)}</span>${this._noFix(x)}</div>`).join("") || `<div class="muted">${pe(this._t("none"))}</div>`}
      <label>${pe(this._t("awayDelay"))}${inf("auto_away_delay")}</label><input class="small" type="number" min="1" max="${lim.away_delay}" data-a="auto_away_delay" data-num="1" value="${pe(a.auto_away_delay)}">
      ${this._how("auto")}
      ${this._more("auto", `<label>${pe(this._t("awayEntity"))}</label>${this._awayEntityPick(c, a)}
      ${a.auto_away_entity ? `<label>${pe(this._t("awayEntityState"))}</label><select data-a="auto_away_entity_state">${Object.entries(this._t("awayEntityStates")).map(([v, l]) => `<option value="${v}" ${v === (a.auto_away_entity_state || "on") ? "selected" : ""}>${pe(l)}</option>`).join("")}</select><div class="warn">${pe(this._t("awayEntityWarn"))}</div>` : ""}
      <label>${pe(this._t("schedule"))}${inf("auto_schedule")}</label><select data-a="auto_schedule"><option value="">${pe(this._t("noSchedule"))}</option>${c.schedules.map((x) => `<option value="${pe(x.id)}" ${x.id === a.auto_schedule ? "selected" : ""}>${pe(x.name)}</option>`).join("")}</select>
      <div class="tool" style="margin-top:6px"><a class="b" href="/config/helpers" target="_blank" rel="noopener">${pe(this._t("scheduleCreate"))}</a><button class="b" data-act="refresh">${pe(this._t("refreshLists"))}</button></div>
      <div class="muted">${pe(this._t("scheduleHint"))}</div>`)}
${this._returnSection(c, lim, t)}
      <div class="sec">${pe(this._t("secClose"))}</div>
      <div class="chk"><input type="checkbox" data-c="enabled" ${close.enabled ? "checked" : ""}><span>${pe(this._t("closeOn"))}${inf("close_enabled")}</span></div>
      ${close.enabled ? `<label>${pe(this._t("doors"))}${inf("close_doors")}</label>${doors.map((id) => `<div class="chk"><input type="checkbox" data-cm="doors" value="${pe(id)}" ${close.doors.includes(id) ? "checked" : ""}><span>${pe(this._name(id))}</span></div>`).join("") || `<div class="muted">${pe(this._t("noDoors"))}</div>`}` : ""}
      ${this._how("close")}
      ${close.enabled ? this._more("close", `<label>${pe(this._t("settle"))}${inf("close_settle")}</label><input class="small" type="number" min="1" max="${lim.settle}" data-c="settle" data-num="1" value="${pe(close.settle)}">`) : ""}
      <div class="sec">${pe(this._t("secPassage"))}</div>
      <div class="chk"><input type="checkbox" data-p="enabled" ${pass.enabled ? "checked" : ""}><span>${pe(this._t("passageOn"))}${inf("passage_enabled")}</span></div>
      <div class="muted">${pe(this._t("passageHint"))}</div>
      ${pass.enabled ? `<div class="two"><div><label>${pe(this._t("passageDuration"))}${inf("passage_duration")}</label><input type="number" min="1" max="${lim.passage_duration}" data-p="duration" data-num="1" value="${pe(pass.duration)}"></div>
      <div><label>${pe(this._t("passagePathAfter"))}${inf("passage_path_after")}</label><input type="number" min="0" max="${lim.passage_after}" data-p="path_after" data-num="1" value="${pe(pass.path_after)}"></div></div>
      <label>${pe(this._t("passagePath"))}${inf("passage_path")}</label>${members.map((id) => `<div class="chk"><input type="checkbox" data-pm="path" value="${pe(id)}" ${pass.path.includes(id) ? "checked" : ""}><span>${pe(this._name(id))}</span></div>`).join("") || `<div class="muted">${pe(this._t("noMembers"))}</div>`}` : ""}
      ${this._how("passage")}
      ${pass.enabled ? this._more("passage", `<label>${pe(this._t("passageOutDoors"))}${inf("passage_out_doors")}</label><select data-p="out_doors">${["first", "all"].map((v) => `<option value="${v}" ${v === pass.out_doors ? "selected" : ""}>${pe(t("outDoors", v))}</option>`).join("")}</select>
      <label>${pe(this._t("passageOutEnd"))}${inf("passage_out_end")}</label><select data-p="out_end">${["time", "returned"].map((v) => `<option value="${v}" ${v === pass.out_end ? "selected" : ""}>${pe(t("outEnd", v))}</option>`).join("")}</select>`) : ""}
      <div class="muted">${pe(this._t("passagePhoneMoved"))}</div>
      ${this._err("base")}`;
  }

  // --- Bei Rückkehr (ADR 0015) ----------------------------------------------------

  _info(key, optional = false) {
    // ⓘ: Mauszeiger drauf zeigt den Text, Tippen klappt ihn auf
    const text = this._t("info")[key] || "";
    if (optional && !text) return "";
    return ` <button type="button" class="info" data-info="${pe(key)}" title="${pe(text)}" aria-label="${pe(this._t("infoLabel"))}">ⓘ</button><span class="tip" data-tip="${pe(key)}" hidden>${pe(text)}</span>`;
  }

  _noFix(person) {
    // Ohne Ortung gilt die Person nie als weg („weg“ nur mit Beleg, ADR 0015)
    return person.locatable === false ? `<span class="nofix" title="${pe(this._t("noFixHint"))}">${pe(this._t("noFix"))}</span>` : "";
  }

  _returnHow(back) {
    let text = ((this._t("returnHow") || {})[back.mode] || "").replace("{w}", String(back.window));
    const normal = Number(this._draft.entry_delay) || 0;
    if (["door", "passage"].includes(back.mode) && back.approach_delay > normal) {
      text += " " + this._t("approachHow").replace("{v}", String(back.approach_valid)).replace("{s}", String(back.approach_delay)).replaceAll("{n}", String(normal));
    }
    return text;
  }

  _approachRec(back) {
    // Empfehlungen aus der Heimkehr-Beobachtung für die Personen der Liste
    const advice = this.settings.profile_edit.return_advice || {};
    const rows = back.persons.map((p) => advice[p]).filter(Boolean);
    const delays = rows.map((r) => r.entry_delay).filter((v) => v);
    const valid = rows.map((r) => r.approach_minutes).filter((v) => v);
    return {
      delay: delays.length ? Math.max(...delays) : null,
      valid: valid.length ? Math.min(Math.max(...valid), this.settings.profile_edit.limits.approach_valid) : null,
    };
  }

  _recLine(field, value, current, textMeasured, textDefault) {
    const text = value === null ? textDefault : textMeasured.replace("{r}", String(value));
    const button = value !== null && Number(current) !== value ? ` <button type="button" class="b" data-rec="${pe(field)}" data-value="${value}">${pe(this._t("apply"))}</button>` : "";
    return `<div class="muted">${pe(text)}${button}</div>`;
  }

  _approachFields(back, lim) {
    const rec = this._approachRec(back);
    const normal = Number(this._draft.entry_delay) || 0;
    const weak = back.approach_delay > 0 && back.approach_delay <= normal;
    return `
        <label>${pe(this._t("approachDelay"))} ${this._info("approachDelay")}</label>
        <input class="small" type="number" min="0" max="${lim.approach_delay}" data-r="approach_delay" data-num="1" value="${pe(back.approach_delay)}">
        ${this._recLine("approach_delay", rec.delay, back.approach_delay, this._t("approachDelayRec"), this._t("approachDelayRecDefault"))}
        ${weak ? `<div class="warn">${pe(this._t("approachTooShort").replace("{n}", String(normal)))}</div>` : ""}
        ${back.approach_delay > 0 ? `<label>${pe(this._t("approachValid"))} ${this._info("approachValid")}</label>
        <input class="small" type="number" min="1" max="${lim.approach_valid}" data-r="approach_valid" data-num="1" value="${pe(back.approach_valid)}">
        ${this._recLine("approach_valid", rec.valid, back.approach_valid, this._t("approachValidRec"), this._t("approachValidRecDefault"))}` : ""}`;
  }

  _returnSection(c, lim, t) {
    const back = this._draft.return;
    const persons = c.persons.map((x) => `<div class="chk"><input type="checkbox" data-rm="persons" value="${pe(x.id)}" ${back.persons.includes(x.id) ? "checked" : ""}><span>${pe(x.name)}</span>${this._noFix(x)}</div>`).join("") || `<div class="muted">${pe(this._t("none"))}</div>`;
    const usesWindow = ["door", "passage"].includes(back.mode);
    return `
      <div class="sec">${pe(this._t("secReturn"))}</div>
      <div class="muted">${pe(this._t("returnIntro"))}</div>
      <label>${pe(this._t("returnMode"))} ${this._info("mode")}</label>
      <select data-r="mode">${c.return_modes.map((m) => `<option value="${m}" ${m === back.mode ? "selected" : ""}>${pe(t("returnModes", m))}</option>`).join("")}</select>
      ${this._how("return")}
      ${back.mode === "always" ? `<div class="warn">${pe(this._t("returnAlwaysWarn"))}</div>` : ""}
      ${back.mode === "off" ? "" : `<label>${pe(this._t("returnPersons"))} ${this._info("persons")}</label>${persons}`}
      ${this._err("return")}
      ${usesWindow ? this._more("return", `
        <label>${pe(this._t("returnWindow"))} ${this._info("window")}</label>
        <input class="small" type="number" min="1" max="${lim.return_window}" data-r="window" data-num="1" value="${pe(back.window)}">
        <div class="muted">${pe(this._t("returnWindowRec"))}</div>
        ${this._approachFields(back, lim)}`) : ""}`;
  }

  _collect() {
    const root = this.shadowRoot;
    const d = this._draft;
    const val = (el) => (el.dataset.bool ? el.checked : el.dataset.num ? Number(el.value) : el.value);
    root.querySelectorAll("[data-k]").forEach((el) => (d[el.dataset.k] = val(el)));
    const multi = {};
    root.querySelectorAll("[data-m]").forEach((el) => {
      multi[el.dataset.m] = multi[el.dataset.m] || [];
      if (el.checked) multi[el.dataset.m].push(el.value);
    });
    for (const key of ["zones", "excluded", "rules", "sirens", "notify", "speakers"]) {
      if (key in multi) d[key] = multi[key];
      else if (["excluded", "rules"].includes(key) && !root.querySelector(`[data-m="${key}"]`)) d[key] = key === "excluded" ? [] : d[key];
    }
    root.querySelectorAll("[data-a]").forEach((el) => (d.automation[el.dataset.a] = el.dataset.num ? Number(el.value) : el.value || null));
    const awayEnt = root.querySelector("[data-awayent]");
    if (awayEnt) d.automation.auto_away_entity = this._awayEntityValue(awayEnt.value);
    const am = {};
    root.querySelectorAll("[data-am]").forEach((el) => {
      am[el.dataset.am] = am[el.dataset.am] || [];
      if (el.checked) am[el.dataset.am].push(el.value);
    });
    d.automation.auto_weekdays = am.auto_weekdays || [];
    d.automation.auto_away_persons = am.auto_away_persons || [];
    root.querySelectorAll("[data-c]").forEach((el) => {
      d.arm_on_close[el.dataset.c] = el.type === "checkbox" ? el.checked : Number(el.value);
    });
    const doors = [...root.querySelectorAll('[data-cm="doors"]')];
    d.arm_on_close.doors = doors.filter((el) => el.checked).map((el) => el.value);
    root.querySelectorAll("[data-p]").forEach((el) => {
      d.passage[el.dataset.p] = el.type === "checkbox" ? el.checked : el.dataset.num ? Number(el.value) : el.value;
    });
    d.passage.path = [...root.querySelectorAll('[data-pm="path"]')].filter((el) => el.checked).map((el) => el.value);
    root.querySelectorAll("[data-r]").forEach((el) => (d.return[el.dataset.r] = el.dataset.num ? Number(el.value) : el.value));
    if (root.querySelector('[data-rm="persons"]')) {
      d.return.persons = [...root.querySelectorAll('[data-rm="persons"]')].filter((el) => el.checked).map((el) => el.value);
    }
    root.querySelectorAll("details[data-more]").forEach((el) => (el.open ? this._opened.add(el.dataset.more) : this._opened.delete(el.dataset.more)));
    // Ausgenommene nur aus den gewählten Gruppen
    const members = this._members(d.zones);
    d.excluded = d.excluded.filter((id) => members.includes(id));
  }

  async _apply(action, data) {
    this._busy = true;
    this._render();
    let result;
    try {
      result = await this.hass.callWS({ type: "hauswacht/settings/apply", revision: this.settings.revision, action, data });
    } catch (err) {
      result = { ok: false, errors: { base: "failed" } };
    }
    this._busy = false;
    if (result.ok) {
      this.dispatchEvent(new CustomEvent("hw-saved", { bubbles: true, composed: true, detail: { revision: result.revision } }));
      return;
    }
    this._errors = result.errors || { base: "failed" };
    if (this._errors.base === "changed_elsewhere") {
      this.dispatchEvent(new CustomEvent("hw-stale", { bubbles: true, composed: true }));
    }
    this._render();
    window.HauswachtRevealError?.(this.shadowRoot); // Fehlermeldung ins Bild holen
  }

  _payload() {
    const d = { ...this._draft };
    if (this.settings.profile_edit.choices.areas.length <= 1) delete d.area;
    d.id = this.profile;
    return d;
  }

  _render() {
    const style = (window.HauswachtEditStyle || "") + PROFILE_STYLE + (window.HauswachtAdvisor?.style || "");
    this.shadowRoot.innerHTML = `<style>${style}</style><div class="sheet">${this._form()}
      <div class="advice" data-advice></div>
      <div class="bar"><button class="b p" data-act="save" ${this._busy ? "disabled" : ""}>${pe(this._busy ? this._t("saving") : this._t("save"))}</button>
      <button class="b" data-act="cancel">${pe(this._t("cancel"))}</button>
      ${this.profile ? `<button class="b d" data-act="delete">${pe(this._t("delete"))}</button>` : ""}</div></div>`;
    window.HauswachtDocs?.decorate(this.shadowRoot, this.helpKey || "profiles", this._lang);
    this.onclick = (ev) => {
      if (ev.composedPath()[0] === this) this._close();
    };
    this.shadowRoot.querySelectorAll("[data-act]").forEach((btn) =>
      btn.addEventListener("click", () => {
        const act = btn.dataset.act;
        if (act === "cancel") this._close();
        else if (act === "refresh") this._refreshChoices();
        else if (act === "save") {
          this._collect();
          this._apply("profile_save", this._payload());
        } else if (act === "delete" && window.confirm(this._t("deleteConfirm"))) {
          this._apply("profile_delete", { id: this.profile });
        }
      })
    );
    // ⓘ antippen klappt die Erklärung auf
    this.shadowRoot.querySelectorAll("[data-info]").forEach((btn) =>
      btn.addEventListener("click", () => {
        const tip = this.shadowRoot.querySelector(`[data-tip="${CSS.escape(btn.dataset.info)}"]`);
        if (tip) tip.hidden = !tip.hidden;
      })
    );
    // „So verhält sich das:“ zieht bei jeder Eingabe sofort mit (0.62)
    const sheet = this.shadowRoot.querySelector(".sheet");
    const refreshHow = () => {
      this._collect();
      this.shadowRoot.querySelectorAll("[data-how]").forEach((el) => (el.textContent = this._howText(el.dataset.how)));
    };
    sheet.addEventListener("input", refreshHow);
    sheet.addEventListener("change", refreshHow);
    // Hinweise des Assistenten ziehen bei jeder Eingabe nach (ADR 0017)
    sheet.addEventListener("input", () => this._scheduleAdvice());
    sheet.addEventListener("change", () => this._scheduleAdvice());
    this._showAdvice();
    this._scheduleAdvice();
    // Verlängerung an/aus blendet die Gültigkeit ein; Empfehlung übernehmen
    const redraw = () => {
      const top = this.shadowRoot.querySelector(".sheet").scrollTop;
      this._collect();
      this._render();
      this.shadowRoot.querySelector(".sheet").scrollTop = top;
    };
    this.shadowRoot.querySelector('[data-r="approach_delay"]')?.addEventListener("change", redraw);
    this.shadowRoot.querySelector("[data-awayent]")?.addEventListener("change", redraw);
    this.shadowRoot.querySelector('[data-act="away-entity-clear"]')?.addEventListener("click", () => {
      this._collect();
      this._draft.automation.auto_away_entity = null;
      const top = this.shadowRoot.querySelector(".sheet").scrollTop;
      this._render();
      this.shadowRoot.querySelector(".sheet").scrollTop = top;
    });
    this.shadowRoot.querySelectorAll("[data-rec]").forEach((btn) =>
      btn.addEventListener("click", () => {
        this._collect();
        this._draft.return[btn.dataset.rec] = Number(btn.dataset.value);
        const top = this.shadowRoot.querySelector(".sheet").scrollTop;
        this._render();
        this.shadowRoot.querySelector(".sheet").scrollTop = top;
      })
    );
    // Gruppen ändern die Listen "Ausgenommen" und "Ausgangstüren", der Modus bei Rückkehr die Felder
    this.shadowRoot.querySelectorAll('[data-m="zones"], [data-r="mode"], [data-c="enabled"], [data-p="enabled"]').forEach((el) =>
      el.addEventListener("change", () => {
        const top = this.shadowRoot.querySelector(".sheet").scrollTop;
        this._collect();
        this._render();
        this.shadowRoot.querySelector(".sheet").scrollTop = top;
      })
    );
  }

  // --- Hinweise des Assistenten (gemeinsame Prüfung, ADR 0017) ----------------------

  _scheduleAdvice() {
    clearTimeout(this._adviceTimer);
    this._adviceTimer = setTimeout(() => this._advise(), 500);
  }

  async _advise() {
    const advisor = window.HauswachtAdvisor;
    if (!advisor || !this.isConnected || !this.shadowRoot.querySelector("[data-advice]")) return;
    this._collect();
    const seq = (this._adviceSeq = (this._adviceSeq || 0) + 1);
    // Geprüft wird der Entwurf, wie er nach „Speichern“ wäre – gespeichert wird nichts
    const result = await advisor.check(this.hass, "profile_save", this._payload(), this._lang);
    if (seq !== this._adviceSeq) return; // inzwischen neuere Eingabe
    this._advice = (result.findings || []).filter((f) => f.profile && f.profile === result.item);
    this._showAdvice();
  }

  _showAdvice() {
    const advisor = window.HauswachtAdvisor;
    const box = this.shadowRoot.querySelector("[data-advice]");
    if (!advisor || !box) return;
    // Hier lässt sich nur das eigene Profil ändern; allgemeine Vorschläge stehen nur als Text da
    box.innerHTML = advisor.render(this._advice || [], this._lang, (fix) => fix.profile !== null);
    box.querySelectorAll("[data-advfix]").forEach((btn) =>
      btn.addEventListener("click", () => {
        const [i, j] = btn.dataset.advfix.split(":").map(Number);
        const finding = this._advice[i];
        const fix = finding.fixes[j];
        if (!advisor.confirm(fix, finding, this._lang)) return;
        this._collect();
        advisor.apply(this._draft, fix.path, fix);
        const top = this.shadowRoot.querySelector(".sheet").scrollTop;
        this._render();
        this.shadowRoot.querySelector(".sheet").scrollTop = top;
      })
    );
  }

  async _refreshChoices() {
    // Auswahllisten neu holen (z. B. neuer Zeitplan) – Eingaben bleiben
    this._collect();
    try {
      const fresh = await this.hass.callWS({ type: "hauswacht/settings/get" });
      this.settings.profile_edit.choices = fresh.profile_edit.choices;
      this.settings.entities = fresh.entities;
    } catch (_err) {
      // bleibt bei der alten Liste
    }
    const top = this.shadowRoot.querySelector(".sheet").scrollTop;
    this._render();
    this.shadowRoot.querySelector(".sheet").scrollTop = top;
  }

  _close() {
    this.dispatchEvent(new CustomEvent("hw-close", { bubbles: true, composed: true }));
  }
}

if (!customElements.get("hauswacht-profile-editor")) {
  customElements.define("hauswacht-profile-editor", HauswachtProfileEditor);
}
