"""Sicherheitslogik für Sirenen (Sirenen-Guard).

Dieses Modul entscheidet – rein und ohne Home Assistant –, welche Sirenenbefehle
tatsächlich gesendet werden dürfen. Der spätere Siren Executor ruft Sirenen-Services
ausschließlich mit den hier freigegebenen Befehlen auf.

Verbindliche Regeln (siehe docs/safety.md):

1. Testmodus aktiv            -> keinerlei Sirenenbefehle.
2. Hardware-Freigabe aus      -> keinerlei Sirenenbefehle (Standard nach Installation).
3. Brand irgendwo aktiv/unklar -> keine Einbruch-Aktivierung an irgendeinem Gerät.
4. Brand irgendwo aktiv/unklar -> kein einziger Ausschaltbefehl an irgendein Gerät.
5. Ausschalten nur für Geräte, die Hauswacht selbst aktiviert hat.
6. Brandtöne (fire, fire_panic) sind für Einbruchalarme verboten.
7. Laufzeit wird auf die gerätseitige Höchstdauer begrenzt; diese wird nie verändert.

"Unklar" heißt: Der Brand-Indikator eines Geräts ist nicht verfügbar oder unbekannt.
Wer nicht beweisen kann, dass es nicht brennt, darf nichts abschalten.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum

BURGLAR_TONES: frozenset[str] = frozenset(
    {"burglar", "emergency", "police_panic", "emergency_panic"}
)
FIRE_TONES: frozenset[str] = frozenset({"fire", "fire_panic"})

VOLUME_LEVELS: Mapping[str, float] = {
    "low": 0.25,
    "medium": 0.5,
    "high": 0.75,
    "very_high": 1.0,
}


class FireIndicator(StrEnum):
    CLEAR = "clear"  # nachweislich kein Brand, kein Test
    ACTIVE = "active"  # Rauch erkannt oder Testknopf gedrückt
    UNKNOWN = "unknown"  # Indikator nicht verfügbar -> wie ACTIVE behandeln


class BlockReason(StrEnum):
    TEST_MODE = "test_mode"
    HARDWARE_DISABLED = "hardware_disabled"
    FIRE_LOCK = "fire_lock"
    INVALID_TONE = "invalid_tone"
    INVALID_VOLUME = "invalid_volume"
    INVALID_DURATION = "invalid_duration"
    UNKNOWN_DEVICE = "unknown_device"
    NOT_ALLOWED_FOR_BURGLAR = "not_allowed_for_burglar"
    NOT_ACTIVATED_BY_HAUSWACHT = "not_activated_by_hauswacht"


@dataclass(frozen=True)
class SirenDevice:
    key: str
    entity_id: str
    fire_state: FireIndicator
    max_duration: int  # gerätseitige Höchstdauer in s (nur gelesen)
    burglar_allowed: bool = True


@dataclass(frozen=True)
class GuardContext:
    hardware_enabled: bool
    test_mode: bool
    devices: Mapping[str, SirenDevice]
    activated_by_hauswacht: frozenset[str] = frozenset()

    @property
    def fire_lock(self) -> bool:
        """True, sobald irgendein Gerät Brand meldet oder sein Zustand unklar ist."""
        return any(d.fire_state is not FireIndicator.CLEAR for d in self.devices.values())


@dataclass(frozen=True)
class ActivateRequest:
    targets: tuple[str, ...]
    tone: str
    volume: str
    duration: int


@dataclass(frozen=True)
class SirenCommand:
    action: str  # "turn_on" | "turn_off"
    device_key: str
    entity_id: str
    tone: str | None = None
    volume_level: float | None = None
    duration: int | None = None


@dataclass(frozen=True)
class BlockedCommand:
    device_key: str
    reason: BlockReason


@dataclass(frozen=True)
class GuardDecision:
    commands: tuple[SirenCommand, ...] = ()
    blocked: tuple[BlockedCommand, ...] = ()


def _block_all(targets: Iterable[str], reason: BlockReason) -> GuardDecision:
    return GuardDecision(blocked=tuple(BlockedCommand(t, reason) for t in targets))


def _global_block(ctx: GuardContext) -> BlockReason | None:
    if ctx.test_mode:
        return BlockReason.TEST_MODE
    if not ctx.hardware_enabled:
        return BlockReason.HARDWARE_DISABLED
    if ctx.fire_lock:
        return BlockReason.FIRE_LOCK
    return None


def decide_activation(ctx: GuardContext, request: ActivateRequest) -> GuardDecision:
    """Entscheidet, welche Einbruch-Sirenen eingeschaltet werden dürfen."""
    targets = tuple(dict.fromkeys(request.targets))  # Duplikate entfernen, Reihenfolge halten

    reason = _global_block(ctx)
    if reason is not None:
        return _block_all(targets, reason)
    if request.tone not in BURGLAR_TONES:
        return _block_all(targets, BlockReason.INVALID_TONE)
    if request.volume not in VOLUME_LEVELS:
        return _block_all(targets, BlockReason.INVALID_VOLUME)
    if request.duration <= 0:
        return _block_all(targets, BlockReason.INVALID_DURATION)

    commands: list[SirenCommand] = []
    blocked: list[BlockedCommand] = []
    for key in targets:
        device = ctx.devices.get(key)
        if device is None:
            blocked.append(BlockedCommand(key, BlockReason.UNKNOWN_DEVICE))
            continue
        if not device.burglar_allowed:
            blocked.append(BlockedCommand(key, BlockReason.NOT_ALLOWED_FOR_BURGLAR))
            continue
        if device.max_duration <= 0:
            blocked.append(BlockedCommand(key, BlockReason.INVALID_DURATION))
            continue
        commands.append(
            SirenCommand(
                action="turn_on",
                device_key=key,
                entity_id=device.entity_id,
                tone=request.tone,
                volume_level=VOLUME_LEVELS[request.volume],
                duration=min(request.duration, device.max_duration),
            )
        )
    return GuardDecision(commands=tuple(commands), blocked=tuple(blocked))


def decide_stop(ctx: GuardContext, targets: Iterable[str] | None = None) -> GuardDecision:
    """Entscheidet, welche Sirenen ausgeschaltet werden dürfen.

    Ohne ``targets`` sind alle Geräte gemeint, die Hauswacht selbst aktiviert hat.
    """
    wanted = (
        tuple(sorted(ctx.activated_by_hauswacht))
        if targets is None
        else tuple(dict.fromkeys(targets))
    )

    reason = _global_block(ctx)
    if reason is not None:
        return _block_all(wanted, reason)

    commands: list[SirenCommand] = []
    blocked: list[BlockedCommand] = []
    for key in wanted:
        device = ctx.devices.get(key)
        if device is None:
            blocked.append(BlockedCommand(key, BlockReason.UNKNOWN_DEVICE))
        elif key not in ctx.activated_by_hauswacht:
            blocked.append(BlockedCommand(key, BlockReason.NOT_ACTIVATED_BY_HAUSWACHT))
        else:
            commands.append(
                SirenCommand(action="turn_off", device_key=key, entity_id=device.entity_id)
            )
    return GuardDecision(commands=tuple(commands), blocked=tuple(blocked))
