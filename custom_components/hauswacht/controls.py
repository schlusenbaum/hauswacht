"""Bedienteile: Zigbee2MQTT-Keypads, NFC-Aufkleber (Companion App), RFID-Leser, Taster
und Türschlösser.

Einziger Ort, an dem Hauswacht an ein anderes Gerät als Sirenen/Benachrichtigungen sendet:
die Rückmeldung an eingerichtete Keypads per MQTT (``<topic>/set`` mit ``arm_mode``) – nur
Zustandsanzeigen, nichts anderes (statischer Test). Gehört zum Hauptbereich und bedient je nach
Einstellung einen Bereich oder alle.

Taster schalten nur scharf. Türschlösser schalten unscharf, wenn ein bekannter Benutzer
aufschließt: Kennung (Nuki-MQTT oder beliebiger Sensor) UND Zustandswechsel des Schlosses in
Home Assistant, höchstens 30 s auseinander. Hauswacht schaltet das Schloss selbst nie.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable, Iterable
from functools import partial
from typing import TYPE_CHECKING, Any

from homeassistant.core import CALLBACK_TYPE, Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

from .const import EVENT_HAUSWACHT
from .core.alarm_states import panel_value
from .core.controls import (
    ALL_AREAS,
    KEY_DISARM,
    KEY_EMERGENCY,
    LOCK,
    REPLY_ALREADY_DISARMED,
    REPLY_INVALID_CODE,
    REPLY_NOT_READY,
    UNLOCK,
    Control,
    ControlKind,
    Emergency,
    LockEvent,
    LockSource,
    Login,
    PendingLogin,
    fresh_cards,
    generic_identity,
    is_new_press,
    is_random_uid,
    keypad_for_topic,
    keypad_mode,
    learn_minutes,
    lock_confirmed,
    lock_intent,
    looks_like_card,
    normalize_tag,
    parse_controls,
    parse_nuki_event,
    press_value,
    reader_for,
    remember_card,
    second_factor_ok,
    sticker_for,
    tag_intent,
)
from .core.notify_events import NotifyEvent
from .core.profiles import find_profile
from .core.texts import tr
from .core.users import (
    Action,
    Identity,
    disabled_tag,
    find_by_ha_user,
    identity_label,
    match_tag,
    tag_credential,
)

if TYPE_CHECKING:
    from .runtime import HauswachtRuntime

_LOGGER = logging.getLogger(__name__)

TAG_SCANNED = "tag_scanned"
MQTT_DOMAIN = "mqtt"


class ControlManager:
    def __init__(self, hass: HomeAssistant, runtime: HauswachtRuntime) -> None:
        self.hass = hass
        self.runtime = runtime  # Hauptbereich
        self.controls = parse_controls(runtime.entry.options)
        self._unsubs: list[CALLBACK_TYPE] = []
        self._transactions: dict[str, Any] = {}
        self._pending: dict[str, PendingLogin] = {}
        self._shown: dict[str, str] = {}
        # Zuletzt gelesene unbekannte Karten (zum Anlernen beim Benutzer): ID -> (wo, wann)
        self.unknown_cards: dict[str, tuple[str, float]] = {}
        # Zuletzt gelesene Zufallsnummer (z. B. Handy): (wo, wann) – nur für einen Hinweis
        self.random_seen: tuple[str, float] | None = None
        # Wer gerade auf eine neue Karte wartet ("Neue Karte anlernen" im Einstellungsdialog)
        self._card_waiters: list[Callable[[str], None]] = []
        # Türschlösser: letzte Kennung bzw. letzter Zustandswechsel (je Schloss)
        self._lock_ident: dict[str, tuple[LockEvent, float]] = {}
        self._lock_state: dict[str, tuple[str, float]] = {}

    # --- Start/Stopp ----------------------------------------------------------

    async def async_start(self) -> None:
        if not self.controls:
            return
        kinds = {c.kind for c in self.controls.values()}
        if kinds & {ControlKind.STICKER, ControlKind.READER}:
            self._unsubs.append(self.hass.bus.async_listen(TAG_SCANNED, self._on_tag))
        keypads = [c for c in self.controls.values() if c.kind is ControlKind.KEYPAD and c.topic]
        nuki = [
            c
            for c in self.controls.values()
            if c.kind is ControlKind.LOCK and c.source is LockSource.NUKI_MQTT and c.topic
        ]
        if keypads or nuki:
            if MQTT_DOMAIN not in self.hass.config.components:
                _LOGGER.warning("Keypads und Nuki über MQTT brauchen die MQTT-Integration")
            else:
                await self._subscribe(keypads)
                await self._subscribe_nuki(nuki)
        watched = self._watched_entities()
        if watched:
            self._unsubs.append(
                async_track_state_change_event(self.hass, sorted(watched), self._on_entity)
            )
        for area in self.runtime.areas.values():
            self._unsubs.append(area.add_listener(self._update_keypads))
        self._update_keypads()

    async def _subscribe(self, keypads: Iterable[Control]) -> None:
        from homeassistant.components import mqtt  # noqa: PLC0415

        for keypad in keypads:
            self._unsubs.append(await mqtt.async_subscribe(self.hass, keypad.topic, self._on_mqtt))

    async def _subscribe_nuki(self, locks: Iterable[Control]) -> None:
        from homeassistant.components import mqtt  # noqa: PLC0415

        for lock in locks:
            self._unsubs.append(
                await mqtt.async_subscribe(
                    self.hass, f"{lock.topic}/lockActionEvent", partial(self._on_nuki, lock)
                )
            )

    @callback
    def _on_nuki(self, control: Control, message: Any) -> None:
        self.lock_identified(control, parse_nuki_event(message.payload))

    def _watched_entities(self) -> set[str]:
        """Taster, Schlösser und "Wer"-Sensoren, deren Zustände Hauswacht mitliest."""
        watched: set[str] = set()
        for control in self.controls.values():
            if control.kind in (ControlKind.BUTTON, ControlKind.LOCK) and control.entity:
                watched.add(control.entity)
            if (
                control.kind is ControlKind.LOCK
                and control.source is LockSource.GENERIC
                and control.who
            ):
                watched.add(control.who)
        return watched

    @callback
    def async_stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()

    # --- Bereiche -------------------------------------------------------------

    def _areas(self, control: Control) -> list[HauswachtRuntime]:
        areas = self.runtime.areas
        if control.area == ALL_AREAS:
            return list(areas.values())
        return [areas[control.area]] if control.area in areas else []

    def _area_of_profile(self, control: Control, profile: str) -> HauswachtRuntime | None:
        for area in self._areas(control):
            if find_profile(area.options, profile) is not None:
                return area
        return None

    # --- Keypads (Zigbee2MQTT) ------------------------------------------------

    @callback
    def _on_mqtt(self, message: Any) -> None:
        keypad = keypad_for_topic(self.controls, message.topic)
        if keypad is None:
            return
        try:
            data = json.loads(message.payload)
        except (TypeError, ValueError):
            return
        if not isinstance(data, dict):
            return
        action = data.get("action")
        if not isinstance(action, str) or not action:
            return
        transaction = data.get("action_transaction")
        key = f"{action}:{transaction}:{data.get('action_code')}"
        if transaction is not None and self._transactions.get(keypad.control_id) == key:
            return  # gleiche Anfrage nochmals im Zustandsbericht
        self._transactions[keypad.control_id] = key
        code = data.get("action_code")
        self.hass.async_create_task(
            self.async_keypad_action(
                keypad, action, str(code) if code not in (None, "") else None, transaction
            ),
            f"hauswacht_keypad_{keypad.control_id}",
        )

    async def async_keypad_action(
        self, keypad: Control, action: str, code: str | None, transaction: Any
    ) -> str:
        """Tastendruck am Keypad auswerten. Liefert die Antwort an das Keypad."""
        if action == KEY_EMERGENCY:
            await self._emergency(keypad)
            return "emergency"
        if action != KEY_DISARM and action not in keypad.buttons:
            return await self._reply(keypad, transaction, REPLY_NOT_READY)
        wanted = Action.DISARM if action == KEY_DISARM else Action.ARM
        identity = await self._login(keypad, code, wanted)
        # Falscher Ausweis wird immer abgelehnt; ohne Ausweis nur scharf, wenn kein PIN nötig
        if identity is None and (code or wanted is Action.DISARM or self.runtime.code_arm_required):
            return await self._reply(keypad, transaction, REPLY_INVALID_CODE)
        if identity == "pending":
            return await self._reply(keypad, transaction, REPLY_NOT_READY)
        result = self._execute(keypad, wanted, keypad.buttons.get(action), identity)
        return await self._reply(keypad, transaction, action if result == "ok" else result)

    async def _login(self, control: Control, code: str | None, action: Action) -> Any:
        """Ausweis prüfen. None = kein/ungültiger Ausweis, "pending" = erster von zweien."""
        if not code:
            return None
        try:
            identity = await self.runtime.async_identify(code, action, source=control.name)
        except HomeAssistantError:
            self._learn(code, control)
            return None
        if control.login is not Login.CARD_AND_PIN or identity.duress:
            return identity
        user_ids = frozenset(u.user_id for u in identity.users)
        now = time.monotonic()
        if second_factor_ok(self._pending.get(control.area), user_ids, identity.kind, now):
            self._pending.pop(control.area, None)
            return identity
        self._pending[control.area] = PendingLogin(user_ids, identity.kind, now)
        return "pending"

    def _learn(self, code: str, control: Control) -> None:
        """Unbekannte Karte zum Anlernen merken – nur unscharf und nur, wenn Anlernen an ist."""
        minutes = learn_minutes(self.runtime.entry.options)
        if not minutes or not self.runtime.all_disarmed or not looks_like_card(code):
            return
        tag = normalize_tag(code)
        if any(tag in u.tags or tag in u.disabled_tags for u in self.runtime.users):
            return  # Karte gehört schon jemandem (z. B. gesperrter Gast, deaktivierte Karte)
        now = dt_util.utcnow().timestamp()
        if is_random_uid(code):
            self.random_seen = (control.name, now)  # nicht anlernbar, nur Hinweis
            return
        self.unknown_cards = remember_card(
            fresh_cards(self.unknown_cards, now, minutes), code, control.name, now
        )
        self._card_read(tag)

    def learnable_cards(self) -> dict[str, tuple[str, float]]:
        """Unbekannte Karten, die noch angelernt werden dürfen (abgelaufene fallen weg)."""
        minutes = learn_minutes(self.runtime.entry.options)
        self.unknown_cards = fresh_cards(self.unknown_cards, dt_util.utcnow().timestamp(), minutes)
        return dict(self.unknown_cards) if minutes else {}

    def recent_random(self) -> tuple[str, float] | None:
        """Zufallsnummer innerhalb der Anlernzeit gelesen? Dann (wo, wann) für den Hinweis."""
        minutes = learn_minutes(self.runtime.entry.options)
        if self.random_seen is None or not minutes:
            return None
        if dt_util.utcnow().timestamp() - self.random_seen[1] > minutes * 60:
            return None
        return self.random_seen

    def _execute(
        self,
        control: Control,
        action: Action,
        profile: str | None,
        identity: Identity | None,
        actor: str | None = None,
    ) -> str:
        """Unscharf oder scharf schalten. Liefert "ok" oder eine Keypad-Antwort."""
        if identity is not None:
            actor = identity_label(identity, self.runtime.lang)
        changed_by = f"{actor} ({control.name})" if actor else control.name
        if action is Action.DISARM:
            targets = [a for a in self._areas(control) if not a.is_disarmed]
            if not targets:
                return REPLY_ALREADY_DISARMED
            if identity is not None and not identity.duress:
                # Nur die Bereiche, in denen der Benutzer unscharf schalten darf
                targets = [a for a in targets if a.permits(identity.users, action)]
                if not targets:
                    return REPLY_INVALID_CODE
            for area in targets:
                area.disarm_trusted(changed_by=changed_by)
            return "ok"
        area = self._area_of_profile(control, profile) if profile else None
        if area is None or profile is None:
            return REPLY_NOT_READY
        try:
            if identity is not None and not identity.duress:
                area.check_allowed(identity.users, action)
            area.arm(profile, changed_by=changed_by)
        except HomeAssistantError:
            return REPLY_NOT_READY
        return "ok"

    async def _reply(self, keypad: Control, transaction: Any, mode: str) -> str:
        """Antwort auf eine Keypad-Anfrage (gleiche Vorgangsnummer)."""
        payload: dict[str, Any] = {"mode": mode}
        if transaction is not None:
            payload["transaction"] = transaction
        await self._publish(keypad, payload)
        self._shown.pop(keypad.control_id, None)
        self._update_keypads()
        return mode

    async def _publish(self, keypad: Control, arm_mode: dict[str, Any]) -> None:
        """Einzige Sendung an ein Gerät: Zustandsanzeige an ein eingerichtetes Keypad."""
        if MQTT_DOMAIN not in self.hass.config.components or not keypad.topic:
            return
        from homeassistant.components import mqtt  # noqa: PLC0415

        await mqtt.async_publish(
            self.hass, f"{keypad.topic}/set", json.dumps({"arm_mode": arm_mode})
        )

    @callback
    def _update_keypads(self) -> None:
        """Keypads zeigen den aktuellen Zustand ihres Bereichs (bzw. aller Bereiche)."""
        for keypad in self.controls.values():
            if keypad.kind is not ControlKind.KEYPAD:
                continue
            states = [panel_value(a.ctx, a.options) for a in self._areas(keypad)]
            if not states:
                continue
            mode = keypad_mode(_combined(states))
            if self._shown.get(keypad.control_id) == mode:
                continue
            self._shown[keypad.control_id] = mode
            self.hass.async_create_task(
                self._publish(keypad, {"mode": mode}), f"hauswacht_keypad_show_{keypad.control_id}"
            )

    async def _emergency(self, keypad: Control) -> None:
        """Notruf-Taste: je Bedienteil aus, stiller Notruf (Push) oder Alarm."""
        self.hass.bus.async_fire(
            EVENT_HAUSWACHT,
            {"type": "Emergency", "control": keypad.name, "mode": keypad.emergency.value},
        )
        if keypad.emergency is Emergency.OFF:
            return
        self.runtime.notifier.notify(
            NotifyEvent.ALARM,
            tr(self.runtime.lang, "panic_title"),
            tr(self.runtime.lang, "panic", control=keypad.name),
            values={"melder": keypad.name},
            test_mode=self.runtime.ctx.test_mode,
            speak=keypad.emergency is Emergency.ALARM,
        )
        if keypad.emergency is Emergency.ALARM:
            for area in self._areas(keypad):
                area.panic(f"control:{keypad.control_id}", keypad.name)

    # --- NFC-Aufkleber und RFID-Leser (Ereignis tag_scanned) ------------------

    @callback
    def _on_tag(self, event: Event[Any]) -> None:
        tag_id = str(event.data.get("tag_id") or "")
        device_id = event.data.get("device_id")
        user_id = event.context.user_id
        self.hass.async_create_task(
            self.async_tag_scanned(tag_id, device_id, user_id), "hauswacht_tag_scanned"
        )

    async def async_tag_scanned(
        self, tag_id: str, device_id: str | None, user_id: str | None
    ) -> str:
        """Aufkleber (mit Handy eines bekannten Benutzers) oder Karte am festen Leser."""
        sticker = sticker_for(self.controls, tag_id)
        if sticker is not None:
            return self._sticker(sticker, user_id)
        reader = reader_for(self.controls, device_id)
        if reader is not None:
            return await self._reader(reader, tag_id)
        return "ignored"

    def _armed(self, control: Control) -> bool:
        return any(not a.is_disarmed for a in self._areas(control))

    def _sticker(self, sticker: Control, user_id: str | None) -> str:
        """NFC-Aufkleber: nur mit dem Handy eines bekannten, berechtigten Benutzers."""
        user = find_by_ha_user(self.runtime.users, user_id)
        intent = tag_intent(sticker.action, self._armed(sticker))
        action = Action.DISARM if intent == "disarm" else Action.ARM
        if user is None or not any(user.may_in(action, a.area_id) for a in self._areas(sticker)):
            self.runtime.notifier.send_system(
                tr(self.runtime.lang, "sticker_denied_title"),
                tr(self.runtime.lang, "sticker_denied", sticker=sticker.name),
            )
            return "rejected"
        result = self._execute(sticker, action, sticker.profile, Identity("phone", (user,)))
        self._confirm(sticker, action, result, user.name)
        return result

    async def _reader(self, reader: Control, tag_id: str) -> str:
        """Fester Leser: Karte eines Benutzers (allein oder mit PIN an einem Keypad)."""
        intent = tag_intent(reader.action, self._armed(reader))
        action = Action.DISARM if intent == "disarm" else Action.ARM
        identity = await self._login(reader, tag_id, action)
        if identity == "pending":
            return "pending"
        if identity is None:
            return "rejected"
        result = self._execute(reader, action, reader.profile, identity)
        self._confirm(reader, action, result, identity_label(identity, self.runtime.lang))
        return result

    def _confirm(self, control: Control, action: Action, result: str, who: str) -> None:
        if result == "ok":
            return  # Scharf/Unscharf melden die normalen Benachrichtigungen
        lang = self.runtime.lang
        what = tr(lang, "control_disarm" if action is Action.DISARM else "control_arm")
        self.runtime.notifier.send_system(
            tr(lang, "control_denied_title"),
            tr(lang, "control_denied", control=control.name, who=who, what=what, result=result),
        )

    # --- Taster und Türschlösser ------------------------------------------------

    @callback
    def _on_entity(self, event: Event[EventStateChangedData]) -> None:
        entity_id = event.data["entity_id"]
        old = event.data["old_state"]
        new = event.data["new_state"]
        old_value = old.state if old is not None else None
        new_value = new.state if new is not None else None
        for control in self.controls.values():
            if control.kind is ControlKind.BUTTON and control.entity == entity_id:
                if is_new_press(old_value, new_value) and new is not None:
                    domain = entity_id.split(".", 1)[0]
                    press = press_value(domain, new_value, new.attributes.get("event_type"))
                    if press is not None:
                        self.button_pressed(control, press)
            elif control.kind is ControlKind.LOCK:
                if control.entity == entity_id:
                    intent = lock_intent(old_value, new_value)
                    if intent is not None:
                        self.lock_moved(control, intent)
                if control.source is LockSource.GENERIC and control.who == entity_id:
                    self._generic_who(control, entity_id, old, new)

    def _generic_who(self, control: Control, entity_id: str, old: Any, new: Any) -> None:
        """Allgemeine Quelle: neuer Wert des "Wer"-Sensors bzw. neues Ereignis."""
        if new is None or old is None or old.state == "unavailable":
            return
        if old.state == new.state:
            return
        value = new.attributes.get("event_type") if entity_id.startswith("event.") else new.state
        identity = generic_identity(value)
        if identity is None:
            return
        # Die Richtung (auf/zu) kommt vom Schloss selbst
        self.lock_identified(control, LockEvent(intent="", identity=identity))

    @callback
    def button_pressed(self, control: Control, press: str) -> str:
        """Taster: Druckart -> Profil scharf schalten. Nie unscharf, nie "Alarm beenden"."""
        profile = control.presses.get(press)
        self._fire("ButtonPressed", control, press=press, profile=profile)
        if profile is None:
            return "ignored"
        area = self._area_of_profile(control, profile)
        if area is None:
            return "ignored"
        if not area.is_disarmed:
            return "already_armed"  # nie über ein scharfes Profil hinweg umschalten
        if area.code_arm_required:
            lang = self.runtime.lang
            self.runtime.notifier.send_system(
                tr(lang, "control_denied_title"),
                tr(lang, "button_pin_required", control=control.name),
            )
            return "pin_required"
        result = self._execute(control, Action.ARM, profile, None)
        self._confirm(control, Action.ARM, result, control.name)
        return result

    @callback
    def lock_identified(self, control: Control, event: LockEvent | None) -> None:
        """Kennung vom Schloss (Nuki-MQTT oder "Wer"-Sensor)."""
        if event is None:
            return
        self._fire(
            "LockIdentified",
            control,
            intent=event.intent or None,
            identity=event.identity,
            reason=event.reason,
        )
        if event.identity is None:
            self._lock_ident.pop(control.control_id, None)
            return
        self._lock_ident[control.control_id] = (event, time.monotonic())
        self._match_lock(control)

    @callback
    def lock_moved(self, control: Control, intent: str) -> None:
        """Schloss in Home Assistant auf- bzw. zugeschlossen."""
        self._lock_state[control.control_id] = (intent, time.monotonic())
        self._match_lock(control)

    def _match_lock(self, control: Control) -> None:
        ident = self._lock_ident.get(control.control_id)
        state = self._lock_state.get(control.control_id)
        if ident is None or state is None:
            return
        event, ident_at = ident
        intent, state_at = state
        if event.intent not in ("", intent) or not lock_confirmed(ident_at, state_at):
            return
        # Beides verbraucht: dieselbe Kennung zählt nur einmal
        self._lock_ident.pop(control.control_id, None)
        self._lock_state.pop(control.control_id, None)
        assert event.identity is not None
        self._lock_action(control, intent, event.identity)

    def _lock_action(self, control: Control, intent: str, identity: str) -> str:
        now = dt_util.utcnow().timestamp()
        users = match_tag(identity, self.runtime.users, now).users
        lang = self.runtime.lang
        disabled = disabled_tag(identity, self.runtime.users)
        if not users and disabled is not None:
            owner, card_name = disabled
            self.runtime.notifier.send_system(
                tr(lang, "card_disabled_title"),
                tr(
                    lang,
                    "lock_disabled",
                    card=card_name or identity,
                    who=owner.name,
                    where=control.name,
                ),
            )
            self._fire("LockIgnored", control, intent=intent, reason="disabled_id")
            return "disabled"
        if not users:
            self._learn_lock(identity, control)
            if intent == UNLOCK and self._armed(control):
                self.runtime.notifier.send_system(
                    tr(lang, "control_denied_title"),
                    tr(lang, "lock_unknown", control=control.name, id=identity),
                )
            self._fire("LockIgnored", control, intent=intent, reason="unknown_id")
            return "unknown"
        found = Identity("lock", users, credential=tag_credential(identity, users))
        self.runtime.main.note_used(f"card:{identity}")
        who = identity_label(found, lang)
        if intent == UNLOCK:
            if not self._armed(control):
                return "already_disarmed"
            result = self._execute(control, Action.DISARM, None, found)
            self._confirm(control, Action.DISARM, result, who)
            return result
        if intent == LOCK and control.profile:
            area = self._area_of_profile(control, control.profile)
            if area is None or not area.is_disarmed:
                return "ignored"
            result = self._execute(control, Action.ARM, control.profile, found)
            self._confirm(control, Action.ARM, result, who)
            return result
        return "ignored"

    def _learn_lock(self, identity: str, control: Control) -> None:
        """Unbekannte Schloss-Kennung zum Anlernen anbieten – nur wenn alles unscharf ist."""
        minutes = learn_minutes(self.runtime.entry.options)
        if not minutes or not self.runtime.all_disarmed:
            return
        now = dt_util.utcnow().timestamp()
        self.unknown_cards = remember_card(
            fresh_cards(self.unknown_cards, now, minutes), identity, control.name, now
        )
        self._card_read(identity)

    def wait_for_card(self, waiter: Callable[[str], None]) -> Callable[[], None]:
        """Bei der nächsten neu gelesenen (anlernbaren) Karte ``waiter`` aufrufen."""
        self._card_waiters.append(waiter)

        def _remove() -> None:
            if waiter in self._card_waiters:
                self._card_waiters.remove(waiter)

        return _remove

    def _card_read(self, tag: str) -> None:
        for waiter in list(self._card_waiters):
            waiter(tag)

    def _fire(self, kind: str, control: Control, **data: Any) -> None:
        self.hass.bus.async_fire(EVENT_HAUSWACHT, {"type": kind, "control": control.name, **data})

    # --- Anzeige ----------------------------------------------------------------

    def attributes(self) -> dict[str, Any]:
        return {
            control.name: {"kind": control.kind.value, "area": control.area}
            for control in self.controls.values()
        }


def _combined(states: list[str]) -> str:
    """Mehrere Bereiche -> ein Zustand fürs Keypad (Alarm vor Verzögerung vor scharf)."""
    for wanted in ("triggered", "pending", "arming"):
        if wanted in states:
            return wanted
    armed = [s for s in states if s != "disarmed"]
    if not armed:
        return "disarmed"
    return armed[0] if len(set(armed)) == 1 else "armed_away"
