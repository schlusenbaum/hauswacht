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

import asyncio
import hashlib
import json
import logging
import time
from collections.abc import Callable, Iterable
from dataclasses import replace
from functools import partial
from typing import TYPE_CHECKING, Any

from homeassistant.core import CALLBACK_TYPE, Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

from .const import DOMAIN, ISSUE_CODE_ENTITIES
from .core.action_codes import ActionCode, CodeAction, find_action_code, parse_action_codes
from .core.alarm_states import panel_value
from .core.code_guard import remaining_lock
from .core.controls import (
    ALL_AREAS,
    ARM_KEYS,
    FREE_BUTTON_KINDS,
    KEY_DISARM,
    KEY_EMERGENCY,
    LOCK,
    NOBODY,
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
    PendingForce,
    PendingLogin,
    force_confirmed,
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
    pending_valid,
    press_value,
    reader_for,
    remember_card,
    second_factor_ok,
    sticker_for,
    tag_intent,
)
from .core.keypad_input import (
    NOT_ALLOWED,
    Display,
    InputOutcome,
    KeypadResult,
    RecentInputs,
    area_display,
    combined_display,
    generic_keypad_for,
    normalize_button,
    public_result,
    remember_unknown,
    z2m_reply,
)
from .core.mqtt_keypad import (
    TOPIC_ATTRIBUTES,
    TOPIC_AVAILABILITY,
    TOPIC_RESPONSE,
    TOPIC_SET,
    TOPIC_STATE,
    MqttCommand,
    parse_command,
    state_word,
)
from .core.notify_events import NotifyEvent
from .core.passage import PASSAGE_TARGET
from .core.profiles import find_profile
from .core.reactions import FIRE_DEVICE_CLASSES
from .core.siren_guard import FireIndicator
from .core.state_machine import AlarmState
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
from .errors import ArmRefused

if TYPE_CHECKING:
    from .runtime import HauswachtRuntime

_LOGGER = logging.getLogger(__name__)

TAG_SCANNED = "tag_scanned"
MQTT_DOMAIN = "mqtt"


def code_entities_to_disable(
    hass: HomeAssistant, topics: Iterable[str], handled: Iterable[str]
) -> list[str]:
    """Code-Entitäten (Zigbee2MQTT) der Hauswacht-Keypads, die noch aktiv sind.

    ``handled``: schon einmal behandelt (abgeschaltet oder bewusst wieder eingeschaltet) –
    danach fragt Hauswacht nicht mehr.
    """
    topics = list(topics)
    done = set(handled)
    ent_reg = er.async_get(hass)
    dev_reg = dr.async_get(hass)
    found: list[str] = []
    for entry in ent_reg.entities.values():
        if (
            entry.platform != MQTT_DOMAIN
            or entry.domain != "sensor"
            or "_action_code_" not in f"{entry.unique_id}_"
            or entry.entity_id in done
            or entry.disabled_by is not None
            or entry.device_id is None
        ):
            continue
        device = dev_reg.async_get(entry.device_id)
        names = {device.name, device.name_by_user} - {None} if device is not None else set()
        if any(t.endswith(f"/{name}") for t in topics for name in names):
            found.append(entry.entity_id)
    return sorted(found)


class ControlManager:
    def __init__(self, hass: HomeAssistant, runtime: HauswachtRuntime) -> None:
        self.hass = hass
        self.runtime = runtime  # Hauptbereich
        self.controls = parse_controls(runtime.entry.options)
        self._action_codes = parse_action_codes(runtime.entry.options)
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
        # Keypad -> erster gescheiterter Scharf-Versuch (für "trotzdem scharf" per zweitem Druck)
        self._force: dict[str, PendingForce] = {}
        # Türschlösser: letzte Kennung bzw. letzter Zustandswechsel (je Schloss)
        self._lock_ident: dict[str, tuple[LockEvent, float]] = {}
        self._lock_state: dict[str, tuple[str, float]] = {}
        # Allgemeine Keypads (ADR 0012): doppelte Meldungen, Reihenfolge, Anzeige, Unbekannte
        self._recent = RecentInputs()
        self._input_locks: dict[str, asyncio.Lock] = {}
        self._last_result: dict[str, tuple[str, str]] = {}
        self._display_listeners: list[Callable[[], None]] = []
        # Unbekannte Keypads, die sich gemeldet haben: Kennung -> Zeitpunkt (zum Anlegen)
        self.unknown_keypads: dict[str, float] = {}
        # MQTT-Schnittstellen und was zuletzt an sie gesendet wurde
        self._interfaces: list[Control] = []
        self._published: dict[str, str] = {}

    # --- Start/Stopp ----------------------------------------------------------

    async def async_start(self) -> None:
        if not any(c.kind is ControlKind.KEYPAD and c.topic for c in self.controls.values()):
            ir.async_delete_issue(self.hass, DOMAIN, ISSUE_CODE_ENTITIES)
        if not self.controls:
            return
        kinds = {c.kind for c in self.controls.values()}
        if kinds & {ControlKind.STICKER, ControlKind.READER}:
            self._unsubs.append(self.hass.bus.async_listen(TAG_SCANNED, self._on_tag))
        keypads = [c for c in self.controls.values() if c.kind is ControlKind.KEYPAD and c.topic]
        if keypads:
            self._check_code_entities()
            self._unsubs.append(
                self.hass.bus.async_listen(
                    er.EVENT_ENTITY_REGISTRY_UPDATED, self._on_registry_updated
                )
            )
        nuki = [
            c
            for c in self.controls.values()
            if c.kind is ControlKind.LOCK and c.source is LockSource.NUKI_MQTT and c.topic
        ]
        interfaces = [
            c for c in self.controls.values() if c.kind is ControlKind.MQTT_KEYPAD and c.topic
        ]
        if keypads or nuki or interfaces:
            if MQTT_DOMAIN not in self.hass.config.components:
                _LOGGER.warning("Keypads und Nuki über MQTT brauchen die MQTT-Integration")
            else:
                await self._subscribe(keypads)
                await self._subscribe_nuki(nuki)
                await self._start_interfaces(interfaces)
        watched = self._watched_entities()
        if watched:
            self._unsubs.append(
                async_track_state_change_event(self.hass, sorted(watched), self._on_entity)
            )
        if any(c.kind in FREE_BUTTON_KINDS for c in self.controls.values()):
            fire = self._fire_indicators()
            if fire:
                self._unsubs.append(
                    async_track_state_change_event(self.hass, fire, self._on_fire_indicator)
                )
        for area in self.runtime.areas.values():
            self._unsubs.append(area.add_listener(self._update_keypads))
        self._update_keypads()

    # --- Getippte Codes nicht im Verlauf speichern ------------------------------

    @callback
    def _on_registry_updated(self, event: Event[Any]) -> None:
        if event.data.get("action") in ("create", "update", "remove"):
            self._check_code_entities()

    @callback
    def _check_code_entities(self) -> None:
        """Code-Entität der Keypads in Zigbee2MQTT: Abschalten **anbieten** (Reparatur).

        Zigbee2MQTT legt für den am Keypad getippten Code eine eigene Entität an
        (``sensor.<keypad>_action_code``). Home Assistant speichert sie im Verlauf – also jede
        PIN im Klartext, auch in Backups. Hauswacht liest das Keypad direkt über MQTT und braucht
        sie nicht. Die Entität gehört aber der MQTT-Integration: Hauswacht ändert sie nicht
        selbst, sondern zeigt eine Reparatur-Meldung; erst wenn du dort bestätigst, wird sie
        deaktiviert (``repairs.py``).
        """
        pending = code_entities_to_disable(
            self.hass,
            [c.topic for c in self.controls.values() if c.kind is ControlKind.KEYPAD],
            self.runtime.main.code_entities_hidden,
        )
        if not pending:
            ir.async_delete_issue(self.hass, DOMAIN, ISSUE_CODE_ENTITIES)
            return
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            ISSUE_CODE_ENTITIES,
            is_fixable=True,
            severity=ir.IssueSeverity.WARNING,
            translation_key=ISSUE_CODE_ENTITIES,
            translation_placeholders={"entities": ", ".join(pending)},
            data={"entities": ",".join(pending)},
        )

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
        for interface in self._interfaces:
            self.hass.async_create_task(
                self._mqtt_publish(interface, TOPIC_AVAILABILITY, "offline", retain=True),
                f"hauswacht_mqtt_offline_{interface.control_id}",
            )
        self._interfaces = []

    # --- MQTT-Schnittstelle (ADR 0012, Stufe 3) ----------------------------------

    async def _start_interfaces(self, interfaces: list[Control]) -> None:
        from homeassistant.components import mqtt  # noqa: PLC0415

        self._interfaces = interfaces
        for interface in interfaces:
            self._unsubs.append(
                await mqtt.async_subscribe(
                    self.hass,
                    f"{interface.topic}/{TOPIC_SET}",
                    partial(self._on_interface_command, interface),
                )
            )
            await self._mqtt_publish(interface, TOPIC_AVAILABILITY, "online", retain=True)
        self._publish_interfaces()

    async def _mqtt_publish(
        self, interface: Control, suffix: str, payload: str, *, retain: bool = False
    ) -> None:
        """Sendung der MQTT-Schnittstelle – nur an ihre eigenen Topics, nie an Geräte."""
        if MQTT_DOMAIN not in self.hass.config.components:
            return
        from homeassistant.components import mqtt  # noqa: PLC0415

        try:
            await mqtt.async_publish(
                self.hass, f"{interface.topic}/{suffix}", payload, retain=retain
            )
        except HomeAssistantError:
            _LOGGER.warning("MQTT-Schnittstelle %s: Senden fehlgeschlagen", interface.name)

    @callback
    def _on_interface_command(self, interface: Control, message: Any) -> None:
        if getattr(message, "retain", False):
            # Gespeicherter Befehl (retain): nie ausführen – sonst käme ein altes DISARM nach
            # jedem Neustart erneut an
            _LOGGER.warning(
                "MQTT-Schnittstelle %s: gespeicherten Befehl (retain) ignoriert", interface.name
            )
            self._fire("MqttRetainedCommand", interface)
            return
        command = parse_command(
            message.payload,
            code_field=interface.code_field,
            disarm_word=interface.disarm_word,
            panic_word=interface.panic_word,
        )
        if command is None:
            _LOGGER.info("MQTT-Schnittstelle %s: unlesbare Nachricht ignoriert", interface.name)
            return
        self.hass.async_create_task(
            self._interface_command(interface, command),
            f"hauswacht_mqtt_{interface.control_id}",
        )

    async def _interface_command(self, interface: Control, command: MqttCommand) -> None:
        answer = await self.async_request(
            interface, command.button, command.code, force=command.force
        )
        answer["display"] = state_word(answer["display"], interface.words)
        if command.request_id is not None:
            answer["id"] = command.request_id
        # Fürs Log von Home Assistant – nie mit PIN oder Karte
        _LOGGER.info(
            "MQTT-Schnittstelle %s: Befehl %s%s → %s",
            interface.name,
            command.button,
            " mit Ausweis" if command.code else "",
            answer["result"],
        )
        await self._mqtt_publish(interface, TOPIC_RESPONSE, json.dumps(answer))

    @callback
    def _publish_interfaces(self) -> None:
        """Zustand und Details an alle MQTT-Schnittstellen – nur bei Änderungen."""
        for interface in self._interfaces:
            display = self.generic_display(interface).value
            attributes = {
                "state": state_word(display, interface.words),
                "display": display,
                **self.generic_attributes(interface),
            }
            stable = {k: v for k, v in attributes.items() if k != "delay_seconds"}
            fingerprint = json.dumps(stable, sort_keys=True, default=str)
            if self._published.get(interface.control_id) == fingerprint:
                continue
            self._published[interface.control_id] = fingerprint
            self.hass.async_create_task(
                self._mqtt_publish(interface, TOPIC_STATE, attributes["state"], retain=True),
                f"hauswacht_mqtt_state_{interface.control_id}",
            )
            self.hass.async_create_task(
                self._mqtt_publish(
                    interface,
                    TOPIC_ATTRIBUTES,
                    json.dumps(attributes, default=str),
                    retain=True,
                ),
                f"hauswacht_mqtt_attributes_{interface.control_id}",
            )

    # --- Allgemeine Keypads (ADR 0012) ------------------------------------------

    def _fire_indicators(self) -> list[str]:
        """Rauch-/Brandmelder in Home Assistant – für die Anzeige "fire"."""
        return sorted(
            s.entity_id
            for s in self.hass.states.async_all("binary_sensor")
            if s.attributes.get("device_class") in FIRE_DEVICE_CLASSES
        )

    @callback
    def _on_fire_indicator(self, event: Event[EventStateChangedData]) -> None:
        self._notify_displays()

    def add_display_listener(self, listener: Callable[[], None]) -> CALLBACK_TYPE:
        self._display_listeners.append(listener)

        @callback
        def remove() -> None:
            if listener in self._display_listeners:
                self._display_listeners.remove(listener)

        return remove

    @callback
    def _notify_displays(self) -> None:
        for listener in list(self._display_listeners):
            listener()
        self._publish_interfaces()

    def resolve_generic(self, ref: str) -> Control | None:
        """Allgemeines Keypad über Kennung, Namen oder Anzeige-Entität."""
        found = generic_keypad_for(self.controls, ref)
        if found is not None or not ref.startswith("sensor."):
            return found
        entry = er.async_get(self.hass).async_get(ref)
        prefix = f"{self.runtime.entry.entry_id}_keypad_"
        if entry is None or not str(entry.unique_id).startswith(prefix):
            return None
        return generic_keypad_for(self.controls, str(entry.unique_id)[len(prefix) :])

    async def async_generic_input(
        self, ref: str, button: str, code: str | None, *, force: bool = False
    ) -> dict[str, Any]:
        """Aktion ``hauswacht.keypad_input``: Eingabe eines allgemeinen Keypads."""
        keypad = self.resolve_generic(ref)
        if keypad is None:
            self.unknown_keypads = remember_unknown(
                self.unknown_keypads, ref, dt_util.utcnow().timestamp()
            )
            self.runtime.fire_event({"type": "UnknownKeypad", "keypad": ref[:64]})
            _LOGGER.warning("Unbekanntes Keypad hat sich gemeldet: %s", ref[:64])
            return {"keypad": ref, "result": KeypadResult.UNKNOWN_KEYPAD.value}
        return await self.async_request(keypad, button, code, force=force)

    async def async_request(
        self, keypad: Control, button: str, code: str | None, *, force: bool = False
    ) -> dict[str, Any]:
        """Eingabe eines Keypads mit freien Tasten (allgemein oder MQTT) – mit Antwort."""
        pressed = normalize_button(button)
        # Der PIN bleibt nicht im Speicher – nur ein Fingerabdruck zum Vergleichen
        fingerprint = hashlib.sha256((code or "").encode()).hexdigest() if code else None
        key = RecentInputs.key(pressed, fingerprint, force)
        lock = self._input_locks.setdefault(keypad.control_id, asyncio.Lock())
        # Doppelte Funkmeldungen gibt es nur bei Keypads über Funk; MQTT liefert jede Nachricht
        # genau so, wie sie gesendet wurde – dort zählt jede Eingabe
        dedupe = keypad.kind is not ControlKind.MQTT_KEYPAD
        async with lock:
            now = time.monotonic()
            outcome = self._recent.duplicate(keypad.control_id, key, now) if dedupe else None
            if outcome is None:
                outcome = await self.async_input(keypad, pressed, code or None, force=force)
                self._recent.remember(keypad.control_id, key, time.monotonic(), outcome)
        result = public_result(outcome)
        self._last_result[keypad.control_id] = (result, dt_util.utcnow().isoformat())
        self._notify_displays()
        return {
            "keypad": keypad.control_id,
            "result": result,
            "display": self.generic_display(keypad).value,
            "open_sensors": list(outcome.open_sensors),
            "can_force": outcome.can_force,
            "lock_seconds": outcome.lock_seconds,
        }

    def generic_display(self, keypad: Control) -> Display:
        """Was ein allgemeines Keypad jetzt anzeigen soll."""
        areas = [
            area_display(panel_value(a.ctx, a.options), test_mode=a.ctx.test_mode)
            for a in self._areas(keypad)
        ]
        fire = self.runtime.sirens.external_fire() is FireIndicator.ACTIVE
        return combined_display(areas, fire=fire)

    def generic_attributes(self, keypad: Control) -> dict[str, Any]:
        """Zusatzangaben der Anzeige-Entität – nie PINs oder Kartennummern."""
        areas = self._areas(keypad)
        ends = [a.delay_ends_at for a in areas if a.delay_ends_at is not None]
        delay_ends = min(ends) if ends else None
        profiles = [
            a.profile_name(a.ctx.profile.profile_id) for a in areas if a.ctx.profile is not None
        ]
        changed = [a.changed_by for a in areas if a.changed_by]
        last = self._last_result.get(keypad.control_id)
        return {
            "keypad": keypad.control_id,
            "area": keypad.area,
            "profile": ", ".join(profiles) or None,
            "delay_ends": delay_ends.isoformat() if delay_ends else None,
            "delay_seconds": (
                max(0, round((delay_ends - dt_util.utcnow()).total_seconds()))
                if delay_ends
                else None
            ),
            "test_mode": any(a.ctx.test_mode for a in areas),
            "changed_by": changed[0] if changed else None,
            "buttons": sorted(keypad.buttons),
            "last_result": last[0] if last else None,
            "last_result_at": last[1] if last else None,
            # Durchgang (ADR 0013): bleibt scharf, nur Tür/Weg kurz frei
            "passage": next((info for a in areas if (info := a.passage_info())), None),
        }

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
        """Tastendruck am Zigbee2MQTT-Keypad auswerten. Liefert die Antwort an das Keypad."""
        outcome = await self.async_input(keypad, action, code)
        mode = z2m_reply(outcome, action, self._keypad_mode(keypad))
        if mode is None:
            return "emergency"
        return await self._reply(keypad, transaction, mode)

    async def async_input(
        self, keypad: Control, button: str, code: str | None, *, force: bool = False
    ) -> InputOutcome:
        """Keypad-Kern: eine Eingabe (Taste + Ausweis) auswerten – für alle Keypads gleich.

        Zigbee2MQTT-Keypad und allgemeines Keypad (ADR 0012) nutzen genau diesen Weg: Anmeldung,
        Rechte, Sperre, Bedrohungs-PIN, Aktions-Codes, "trotzdem scharf", Notruf.
        ``force``: ausdrücklich "trotzdem scharf" (nur mit dem Recht dazu).
        """
        if button == KEY_EMERGENCY:
            await self._emergency(keypad)
            result = (
                KeypadResult.UNKNOWN_BUTTON
                if keypad.emergency is Emergency.OFF
                else KeypadResult.OK
            )
            return InputOutcome(result.value, emergency=True)
        action_code = self._find_action_code(keypad, button, code)
        if action_code is not None:
            # Aktions-Code: kein Ausweis, kein Fehlversuch – in der PIN-Sperre aber gesperrt
            locked = remaining_lock(self.runtime.main._code_guard, time.monotonic())
            if locked:
                return InputOutcome(KeypadResult.LOCKED.value, lock_seconds=locked)
            return self._run_action_code(keypad, action_code)
        if button != KEY_DISARM and button not in keypad.buttons:
            return InputOutcome(KeypadResult.UNKNOWN_BUTTON.value)
        if button != KEY_DISARM and (
            keypad.buttons.get(button) == PASSAGE_TARGET or self._entry_with_passage(keypad)
        ):
            # Durchgang (ADR 0013): eigene Taste, oder in der Eingangsverzögerung jede
            # Profil-Taste ("schon gut, bleib scharf" – das laufende Profil bleibt)
            return await self._passage_input(keypad, code)
        wanted = Action.DISARM if button == KEY_DISARM else Action.ARM
        identity = await self._login(keypad, code, wanted)
        # Zweiter Druck derselben Taste OHNE PIN/Karte bestätigt einen gescheiterten ersten
        # ("trotzdem scharf") – im Namen der Person des ersten Drucks
        confirm = None
        if wanted is Action.ARM and not code:
            pending = self._force.get(keypad.control_id)
            if pending_valid(pending, button, time.monotonic()):
                confirm = pending
                identity = pending.identity if pending is not None else None
        # Falscher Ausweis wird immer abgelehnt; ohne Ausweis nur scharf, wenn kein PIN nötig
        if (
            confirm is None
            and identity is None
            and (code or wanted is Action.DISARM or self.runtime.code_arm_required)
        ):
            locked = remaining_lock(self.runtime.main._code_guard, time.monotonic())
            if locked:
                return InputOutcome(KeypadResult.LOCKED.value, lock_seconds=locked)
            return InputOutcome(KeypadResult.INVALID_CODE.value)
        if identity == "pending":
            return InputOutcome(KeypadResult.PENDING.value)
        may_force = confirm is not None or self._force_users(identity) is not None
        confirmed = (
            confirm is not None
            or (force and may_force)
            or self._force_wanted(keypad, button, identity)
        )
        outcome = self._execute_outcome(
            keypad, wanted, keypad.buttons.get(button), identity, confirmed=confirmed
        )
        self._remember_force(keypad, button, identity, outcome.result)
        if outcome.can_force and not may_force:
            outcome = replace(outcome, can_force=False)
        return outcome

    def _entry_with_passage(self, keypad: Control) -> bool:
        """Läuft in einem Bereich dieses Keypads eine Eingangsverzögerung mit Durchgang?"""
        return any(
            a.ctx.state is AlarmState.PENDING and a.passage_ready for a in self._areas(keypad)
        )

    async def _passage_input(self, keypad: Control, code: str | None) -> InputOutcome:
        """Durchgang am Keypad – immer mit Ausweis (auch bei "Tasten ohne PIN")."""
        identity = await self._login(keypad, code, Action.PASSAGE)
        if identity is None:
            locked = remaining_lock(self.runtime.main._code_guard, time.monotonic())
            if locked:
                return InputOutcome(KeypadResult.LOCKED.value, lock_seconds=locked)
            return InputOutcome(KeypadResult.INVALID_CODE.value)
        if identity == "pending":
            return InputOutcome(KeypadResult.PENDING.value)
        ready = [a for a in self._areas(keypad) if a.passage_ready]
        if not ready:
            return InputOutcome(KeypadResult.NOT_READY.value)
        if not identity.duress:
            # Bedrohungs-PIN: nach außen ein normaler Durchgang (der stille Alarm ist raus)
            ready = [a for a in ready if a.permits(identity.users, Action.PASSAGE)]
            if not ready:
                return InputOutcome(NOT_ALLOWED)
        # Läuft irgendwo eine Eingangsverzögerung, wird nur dort reingelassen
        entering = [a for a in ready if a.ctx.state is AlarmState.PENDING]
        changed_by = f"{identity_label(identity, self.runtime.lang)} ({keypad.name})"
        for area in entering or ready:
            try:
                area.passage(changed_by)
            except HomeAssistantError:
                return InputOutcome(KeypadResult.NOT_READY.value)
        return InputOutcome(KeypadResult.OK.value)

    def _find_action_code(
        self, keypad: Control, button: str, code: str | None
    ) -> ActionCode | None:
        """Aktions-Code zu Code + Taste. Allgemeines Keypad: jede Scharf-Taste zählt als Taste
        "scharf" (die Tasten haben dort freie Namen), "disarm" als "unscharf"."""
        if keypad.kind not in FREE_BUTTON_KINDS:
            return find_action_code(self._action_codes, code, button, keypad.control_id)
        keys = (KEY_DISARM,) if button == KEY_DISARM else ARM_KEYS
        for key in keys:
            found = find_action_code(self._action_codes, code, key, keypad.control_id)
            if found is not None:
                return found
        return None

    def _force_users(self, identity: Any) -> frozenset[str] | None:
        """Wer per zweitem Druck trotzdem scharf schalten darf (sonst None).

        Ohne Ausweis: leere Menge – aber nur, wenn Scharfschalten ohne PIN erlaubt ist.
        """
        if identity is None:
            return None if self.runtime.code_arm_required else NOBODY
        if not isinstance(identity, Identity) or identity.duress:
            return None
        if not any(u.can_force_arm for u in identity.users):
            return None
        return frozenset(u.user_id for u in identity.users)

    def _force_wanted(self, keypad: Control, action: str, identity: Any) -> bool:
        users = self._force_users(identity)
        if users is None or action == KEY_DISARM:
            return False
        pending = self._force.get(keypad.control_id)
        return force_confirmed(pending, action, users, time.monotonic())

    def _remember_force(self, keypad: Control, action: str, identity: Any, result: str) -> None:
        """Nach "nicht bereit" merken: derselbe Druck gleich noch einmal = trotzdem scharf."""
        users = self._force_users(identity)
        if result == KeypadResult.NOT_READY and users is not None and action != KEY_DISARM:
            pending = self._force.get(keypad.control_id)
            if pending_valid(pending, action, time.monotonic()):
                return  # schon bestätigt und trotzdem abgelehnt (z. B. "verweigern"): nicht neu
            self._force[keypad.control_id] = PendingForce(action, users, time.monotonic(), identity)
        else:
            self._force.pop(keypad.control_id, None)

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

    def _execute_and_confirm(
        self,
        control: Control,
        action: Action,
        profile: str | None,
        identity: Identity | None,
        who: str,
    ) -> str:
        """Schalten und bei Ablehnung Bescheid geben – aber nur, wenn das nicht schon die
        Nachricht "Scharfschalten nicht möglich" (mit Knöpfen) getan hat."""
        outcome = self._execute_outcome(control, action, profile, identity)
        result = self._reply_of(outcome, action)
        if not outcome.reported:
            self._confirm(control, action, result, who)
        return result

    @staticmethod
    def _reply_of(outcome: InputOutcome, action: Action) -> str:
        if outcome.result == KeypadResult.OK:
            return "ok"
        if outcome.result == KeypadResult.ALREADY_DISARMED:
            return REPLY_ALREADY_DISARMED
        if outcome.result == NOT_ALLOWED and action is Action.DISARM:
            return REPLY_INVALID_CODE
        return REPLY_NOT_READY

    def _execute_outcome(  # noqa: PLR0913
        self,
        control: Control,
        action: Action,
        profile: str | None,
        identity: Identity | None,
        actor: str | None = None,
        *,
        confirmed: bool = False,
    ) -> InputOutcome:
        """Unscharf oder scharf schalten – mit Einzelheiten für Keypads.

        ``confirmed``: offene Melder überbrücken ("trotzdem scharf"), wenn das Profil das nach
        Bestätigung erlaubt.
        """
        if identity is not None:
            actor = identity_label(identity, self.runtime.lang)
        changed_by = f"{actor} ({control.name})" if actor else control.name
        if action is Action.DISARM:
            targets = [a for a in self._areas(control) if not a.is_disarmed]
            if not targets:
                return InputOutcome(KeypadResult.ALREADY_DISARMED.value)
            if identity is not None and not identity.duress:
                # Nur die Bereiche, in denen der Benutzer unscharf schalten darf
                targets = [a for a in targets if a.permits(identity.users, action)]
                if not targets:
                    return InputOutcome(NOT_ALLOWED)
            for area in targets:
                area.disarm_trusted(changed_by=changed_by)
            return InputOutcome(KeypadResult.OK.value)
        area = self._area_of_profile(control, profile) if profile else None
        if area is None or profile is None:
            return InputOutcome(KeypadResult.NOT_READY.value)
        if (
            identity is not None
            and not identity.duress
            and not area.permits(identity.users, action)
        ):
            return InputOutcome(NOT_ALLOWED)
        try:
            area.arm(profile, confirmed=confirmed, changed_by=changed_by)
        except ArmRefused as err:
            return InputOutcome(
                KeypadResult.NOT_READY.value,
                open_sensors=err.open_sensors,
                can_force=err.confirmable,
                reported=True,
            )
        except HomeAssistantError:
            return InputOutcome(KeypadResult.NOT_READY.value)
        return InputOutcome(KeypadResult.OK.value)

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

    def _keypad_mode(self, keypad: Control) -> str:
        """Aktuelle Anzeige eines Zigbee2MQTT-Keypads (Zustand seines Bereichs bzw. aller)."""
        states = [panel_value(a.ctx, a.options) for a in self._areas(keypad)]
        return keypad_mode(_combined(states))

    @callback
    def _update_keypads(self) -> None:
        """Keypads zeigen den aktuellen Zustand ihres Bereichs (bzw. aller Bereiche)."""
        self._notify_displays()
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

    def _run_action_code(self, keypad: Control, action_code: ActionCode) -> InputOutcome:
        """Aktion eines Aktions-Codes ausführen. Nie unscharf: ein Aktions-Code ist kein Ausweis."""
        actor = tr(self.runtime.lang, "action_code_actor", name=action_code.name)
        self.runtime.fire_event(
            {
                "type": "ActionCode",
                "name": action_code.name,
                "action": action_code.action.value,
                "control": keypad.name,
                "test": self.runtime.ctx.test_mode,
                **self._area_event(keypad),
            },
        )
        if action_code.action is CodeAction.ARM and action_code.profile:
            outcome = self._execute_outcome(
                keypad, Action.ARM, action_code.profile, None, actor=actor
            )
            return replace(outcome, action_code=True, can_force=False)
        if action_code.action is CodeAction.SILENT_EMERGENCY:
            self._silent_emergency(keypad)
        return InputOutcome(KeypadResult.OK.value, action_code=True)

    def _silent_emergency(self, keypad: Control) -> None:
        self.runtime.notifier.notify(
            NotifyEvent.ALARM,
            tr(self.runtime.lang, "panic_title"),
            tr(self.runtime.lang, "panic", control=keypad.name),
            values={"melder": keypad.name},
            test_mode=self.runtime.ctx.test_mode,
            speak=False,
        )

    async def _emergency(self, keypad: Control) -> None:
        """Notruf-Taste: je Bedienteil aus, stiller Notruf (Push) oder Alarm."""
        self.runtime.fire_event(
            {
                "type": "Emergency",
                "control": keypad.name,
                "mode": keypad.emergency.value,
                **self._area_event(keypad),
            },
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
        return self._execute_and_confirm(
            sticker, action, sticker.profile, Identity("phone", (user,)), user.name
        )

    async def _reader(self, reader: Control, tag_id: str) -> str:
        """Fester Leser: Karte eines Benutzers (allein oder mit PIN an einem Keypad)."""
        intent = tag_intent(reader.action, self._armed(reader))
        action = Action.DISARM if intent == "disarm" else Action.ARM
        identity = await self._login(reader, tag_id, action)
        if identity == "pending":
            return "pending"
        if identity is None:
            return "rejected"
        return self._execute_and_confirm(
            reader, action, reader.profile, identity, identity_label(identity, self.runtime.lang)
        )

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
        return self._execute_and_confirm(control, Action.ARM, profile, None, control.name)

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
            return self._execute_and_confirm(control, Action.DISARM, None, found, who)
        if intent == LOCK and control.profile:
            area = self._area_of_profile(control, control.profile)
            if area is None or not area.is_disarmed:
                return "ignored"
            return self._execute_and_confirm(control, Action.ARM, control.profile, found, who)
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

    def _area_event(self, control: Control) -> dict[str, Any]:
        """Bereich eines Bedienteils für hauswacht_event (für alle Bereiche: "all")."""
        if control.area == ALL_AREAS or control.area not in self.runtime.areas:
            return self.runtime.all_areas_event()
        return self.runtime.areas[control.area].event_area

    def _fire(self, kind: str, control: Control, **data: Any) -> None:
        self.runtime.fire_event(
            {"type": kind, "control": control.name, **data, **self._area_event(control)}
        )

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
