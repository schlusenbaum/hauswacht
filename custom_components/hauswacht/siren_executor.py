"""Siren Executor – die EINZIGE Stelle in Hauswacht, die Sirenen-Dienste aufruft.

Jeder Befehl geht vorher durch den Sirenen-Guard (core/siren_guard.py). Der Guard sperrt
Sirenen im Testmodus, ohne Hardware-Freigabe und bei Brand (siehe docs/entwicklung/safety.md).
Gerätewerte wie die Höchstdauer werden nur gelesen, nie geschrieben.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.siren import SirenEntityFeature
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_time_interval

from .const import EVENT_HAUSWACHT, OPT_SIREN_TONES, OPT_SIRENS, OPT_SIRENS_HARDWARE_ENABLED
from .core.reactions import FIRE_DEVICE_CLASSES, fire_state, is_fire_indicator, parse_max_duration
from .core.siren_guard import (
    ActivateRequest,
    BlockReason,
    FireIndicator,
    GuardContext,
    GuardDecision,
    SirenCapabilities,
    SirenCommand,
    SirenDevice,
    decide_activation,
    decide_stop,
)

_LOGGER = logging.getLogger(__name__)

SIREN_DOMAIN = "siren"
SWITCH_DOMAIN = "switch"
# Ein Schalter kann nur ein und aus: kein Ton, keine Lautstärke, keine eigene Laufzeit
SWITCH_CAPABILITIES = SirenCapabilities(
    tones_supported=False, tones=None, volume=False, duration=False, turn_off=True
)
DEFAULT_MAX_DURATION = 240  # s, falls das Gerät keine Höchstdauer meldet
MAX_DURATION_SUFFIX = "_max_duration"
# Abstand der Wiederholversuche, wenn die Brandsperre das Ausschalten verhindert hat
RETRY_STOP_INTERVAL = timedelta(seconds=60)


class SirenExecutor:
    def __init__(
        self,
        hass: HomeAssistant,
        options: Mapping[str, Any],
        *,
        owner: str = "main",
        owners: dict[str, set[str]] | None = None,
    ) -> None:
        self.hass = hass
        # Bereiche teilen Sirenen: Wer eine Sirene noch braucht, verhindert das Ausschalten
        # durch einen anderen Bereich (gilt nur zwischen Bereichen, nie gegen die Brandsperre).
        self.owner = owner
        self.owners: dict[str, set[str]] = owners if owners is not None else {}
        self.sirens: tuple[str, ...] = tuple(
            dict.fromkeys(s for s in options.get(OPT_SIRENS, []) if isinstance(s, str))
        )
        self.hardware_enabled = bool(options.get(OPT_SIRENS_HARDWARE_ENABLED, False))
        tones = options.get(OPT_SIREN_TONES, {})
        self.tones: dict[str, str] = (
            {str(k): str(v) for k, v in tones.items() if v} if isinstance(tones, Mapping) else {}
        )
        self.activated: set[str] = set()
        # Eigene Sirenen, deren Ausschalten die Brandsperre verhindert hat
        self.pending_stop: set[str] = set()
        self._unsub_retry: CALLBACK_TYPE | None = None
        self.last_result: dict[str, Any] = {}

    # --- Lagebild ------------------------------------------------------------

    def _state(self, entity_id: str) -> str | None:
        state = self.hass.states.get(entity_id)
        return state.state if state else None

    def devices(self) -> dict[str, SirenDevice]:
        registry = er.async_get(self.hass)
        devices: dict[str, SirenDevice] = {}
        for siren in self.sirens:
            indicators: list[str | None] = []
            max_state: str | None = None
            entry = registry.async_get(siren)
            if entry is not None and entry.device_id is not None:
                for sibling in er.async_entries_for_device(
                    registry, entry.device_id, include_disabled_entities=True
                ):
                    device_class = sibling.device_class or sibling.original_device_class
                    if is_fire_indicator(sibling.entity_id, device_class):
                        # Deaktivierte Indikatoren haben keinen Zustand -> "unklar" -> Sperre
                        indicators.append(self._state(sibling.entity_id))
                    elif sibling.entity_id.startswith("number.") and sibling.entity_id.endswith(
                        MAX_DURATION_SUFFIX
                    ):
                        max_state = self._state(sibling.entity_id)
            devices[siren] = SirenDevice(
                key=siren,
                entity_id=siren,
                fire_state=fire_state(indicators),
                max_duration=parse_max_duration(max_state, DEFAULT_MAX_DURATION),
                capabilities=self.capabilities(siren),
                fire_detector=bool(indicators),
                tone=self.tones.get(siren),
            )
        return devices

    def capabilities(self, entity_id: str) -> SirenCapabilities:
        """Fähigkeiten laut ``supported_features`` und ``available_tones`` der Sirene.

        Ist die Sirene gerade nicht verfügbar, gelten die Standardwerte; ein Befehl an eine
        nicht verfügbare Sirene schlägt ohnehin fehl.
        """
        if entity_id.startswith(f"{SWITCH_DOMAIN}."):
            # Experten: Schalter als Sirene – nur ein und aus, Hauswacht schaltet selbst ab
            return SWITCH_CAPABILITIES
        state = self.hass.states.get(entity_id)
        if state is None or "supported_features" not in state.attributes:
            return SirenCapabilities()
        try:
            features = SirenEntityFeature(int(state.attributes["supported_features"]))
        except (TypeError, ValueError):
            return SirenCapabilities()
        available = state.attributes.get("available_tones")
        tones: set[str] = set()
        if isinstance(available, Mapping):
            # Home Assistant nimmt Schlüssel oder Namen an
            tones.update(str(k) for k in available)
            tones.update(str(v) for v in available.values())
        elif isinstance(available, (list, tuple)):
            tones.update(str(v) for v in available)
        return SirenCapabilities(
            tones_supported=SirenEntityFeature.TONES in features,
            tones=frozenset(tones) or None,
            volume=SirenEntityFeature.VOLUME_SET in features,
            duration=SirenEntityFeature.DURATION in features,
            turn_off=SirenEntityFeature.TURN_OFF in features,
        )

    def external_fire(self) -> FireIndicator:
        """Brand an irgendeinem Melder in Home Assistant (nur aktive Meldungen zählen)."""
        for state in self.hass.states.async_all("binary_sensor"):
            if state.attributes.get("device_class") in FIRE_DEVICE_CLASSES and state.state == "on":
                return FireIndicator.ACTIVE
        return FireIndicator.CLEAR

    def guard_context(self, *, test_mode: bool) -> GuardContext:
        return GuardContext(
            hardware_enabled=self.hardware_enabled,
            test_mode=test_mode,
            devices=self.devices(),
            activated_by_hauswacht=frozenset(self.activated),
            external_fire=self.external_fire(),
        )

    # --- Befehle ------------------------------------------------------------

    @callback
    def activate(
        self, targets: tuple[str, ...], tone: str, volume: str, duration: int, *, test_mode: bool
    ) -> GuardDecision:
        decision = decide_activation(
            self.guard_context(test_mode=test_mode),
            ActivateRequest(targets=targets, tone=tone, volume=volume, duration=duration),
        )
        for command in decision.commands:
            self._send(command)
            self.activated.add(command.device_key)
            self.pending_stop.discard(command.device_key)
            self.owners.setdefault(command.device_key, set()).add(self.owner)
        self._report("activate", decision)
        return decision

    @callback
    def stop(self, *, test_mode: bool) -> GuardDecision:
        # Sirenen, die ein anderer Bereich noch braucht, nur freigeben, nicht ausschalten
        shared = {key for key in self.activated if self.owners.get(key, set()) - {self.owner}}
        for key in shared:
            self.owners[key].discard(self.owner)
            self.activated.discard(key)
        decision = decide_stop(self.guard_context(test_mode=test_mode))
        for command in decision.commands:
            self.owners.pop(command.device_key, None)
        for command in decision.commands:
            self._send(command)
            self.activated.discard(command.device_key)
            self.pending_stop.discard(command.device_key)
        for blocked in decision.blocked:
            if blocked.reason is BlockReason.FIRE_LOCK:
                # Nicht vergessen: Sirenen ohne eigene Laufzeit liefen sonst endlos weiter.
                self.pending_stop.add(blocked.device_key)
        self._report("stop", decision)
        self._schedule_retry(test_mode=test_mode)
        return decision

    @callback
    def _schedule_retry(self, *, test_mode: bool) -> None:
        if self.pending_stop and self._unsub_retry is None:

            @callback
            def _retry(_now: datetime) -> None:
                self.stop(test_mode=test_mode)

            self._unsub_retry = async_track_time_interval(
                self.hass, _retry, RETRY_STOP_INTERVAL, name="hauswacht_siren_retry_stop"
            )
        elif not self.pending_stop:
            self.cancel_retry()

    @callback
    def cancel_retry(self) -> None:
        if self._unsub_retry is not None:
            self._unsub_retry()
            self._unsub_retry = None

    @callback
    def reset(self) -> None:
        """Nach dem Unscharfschalten: Merkliste leeren.

        Sirenen, deren Ausschalten noch aussteht (Brandsperre), bleiben gemerkt und werden
        ausgeschaltet, sobald der Guard es erlaubt.
        """
        self.activated &= self.pending_stop

    @callback
    def _send(self, command: SirenCommand) -> None:
        data: dict[str, Any] = {"entity_id": command.entity_id}
        if command.action == "turn_on":
            # Nur senden, was das Gerät unterstützt (None = weglassen)
            optional = {
                "tone": command.tone,
                "volume_level": command.volume_level,
                "duration": command.duration,
            }
            data.update({k: v for k, v in optional.items() if v is not None})
        _LOGGER.warning("Sirenenbefehl %s an %s", command.action, command.entity_id)

        # Experten: Schalter als Sirene – nur switch.turn_on / switch.turn_off, ohne Daten
        is_switch = command.entity_id.startswith(f"{SWITCH_DOMAIN}.")

        async def _call() -> None:
            try:
                if is_switch:
                    await self.hass.services.async_call(
                        SWITCH_DOMAIN,
                        command.action,
                        {"entity_id": command.entity_id},
                        blocking=True,
                    )
                else:
                    await self.hass.services.async_call(
                        SIREN_DOMAIN, command.action, data, blocking=True
                    )
            except Exception:
                _LOGGER.exception("Sirenenbefehl an %s fehlgeschlagen", command.entity_id)

        self.hass.async_create_task(_call(), f"hauswacht_siren_{command.entity_id}")

    @callback
    def _report(self, action: str, decision: GuardDecision) -> None:
        self.last_result = {
            "action": action,
            "sent": [c.entity_id for c in decision.commands],
            "blocked": {b.device_key: b.reason.value for b in decision.blocked},
        }
        self.hass.bus.async_fire(EVENT_HAUSWACHT, {"type": "SirenDecision", **self.last_result})
