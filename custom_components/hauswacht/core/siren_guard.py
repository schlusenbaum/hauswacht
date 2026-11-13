"""Sicherheitslogik für Sirenen (Sirenen-Guard).

Dieses Modul entscheidet – rein und ohne Home Assistant –, welche Sirenenbefehle
tatsächlich gesendet werden dürfen. Der spätere Siren Executor ruft Sirenen-Services
ausschließlich mit den hier freigegebenen Befehlen auf.

Verbindliche Regeln (siehe docs/entwicklung/safety.md):

1. Testmodus aktiv            -> keinerlei Sirenenbefehle.
2. Hardware-Freigabe aus      -> keinerlei Sirenenbefehle (Standard nach Installation).
3. Brand irgendwo aktiv/unklar -> keine Einbruch-Aktivierung an irgendeinem Gerät.
4. Brand irgendwo aktiv/unklar -> kein einziger Ausschaltbefehl an irgendein Gerät.
5. Ausschalten nur für Geräte, die Hauswacht selbst aktiviert hat.
6. Brandtöne (fire, fire_panic) sind für Einbruchalarme verboten.
7. Laufzeit wird auf die gerätseitige Höchstdauer begrenzt; diese wird nie verändert.
8. Ton, Lautstärke und Dauer werden nur gesendet, wenn das Gerät sie unterstützt. Kennt ein
   Gerät den gewünschten Einbruchton nicht, wird ein anderer Einbruchton gewählt – nie ein
   Brandton. Ein Rauchmelder ohne Tonauswahl bekommt keinen Einbruchbefehl, weil er sonst
   seinen Standardton (meist den Brandton) spielen könnte.
9. Eine Sirene, die weder eine Dauer annimmt noch ausgeschaltet werden kann, wird nicht
   eingeschaltet – Hauswacht könnte sie nicht wieder beenden.

"Unklar" heißt: Der Brand-Indikator eines Geräts ist nicht verfügbar oder unbekannt.
Wer nicht beweisen kann, dass es nicht brennt, darf nichts abschalten.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum

# Reihenfolge = Ausweichreihenfolge, wenn ein Gerät den gewünschten Ton nicht kennt
BURGLAR_TONE_ORDER: tuple[str, ...] = ("burglar", "emergency", "police_panic", "emergency_panic")
BURGLAR_TONES: frozenset[str] = frozenset(BURGLAR_TONE_ORDER)
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
    NO_BURGLAR_TONE = "no_burglar_tone"
    CANNOT_LIMIT = "cannot_limit"
    TURN_OFF_UNSUPPORTED = "turn_off_unsupported"


@dataclass(frozen=True)
class SirenCapabilities:
    """Was eine Sirene laut Home Assistant kann (``supported_features``, ``available_tones``).

    Die Standardwerte entsprechen einer voll ausgestatteten Sirene. ``tones`` ist ``None``,
    wenn das Gerät Töne annimmt, aber keine Liste meldet.
    """

    tones_supported: bool = True
    tones: frozenset[str] | None = None
    volume: bool = True
    duration: bool = True
    turn_off: bool = True


@dataclass(frozen=True)
class SirenDevice:
    key: str
    entity_id: str
    fire_state: FireIndicator
    max_duration: int  # gerätseitige Höchstdauer in s (nur gelesen)
    burglar_allowed: bool = True
    capabilities: SirenCapabilities = SirenCapabilities()
    # Gerät hat eigene Brand-Indikatoren (Rauchmelder mit Sirene)
    fire_detector: bool = False
    # Fest eingestellter Ton für diese Sirene (z. B. HmIP-ASIR: "FREQUENCY_RISING_AND_FALLING")
    tone: str | None = None
    # Experten: der eingestellte Ton darf ein Brandton sein. Gilt nie für Rauchmelder
    # (fire_detector) – das prüft der Guard selbst.
    fire_tone_allowed: bool = False


@dataclass(frozen=True)
class GuardContext:
    hardware_enabled: bool
    test_mode: bool
    devices: Mapping[str, SirenDevice]
    activated_by_hauswacht: frozenset[str] = frozenset()
    # Brand an Meldern, die keine registrierte Sirene sind (z. B. ein Rauchmelder in einem
    # anderen Raum). Hier zählt nur ein AKTIVER Brand; ein irgendwo ausgefallener Melder soll
    # die Einbruchsirenen nicht dauerhaft sperren.
    external_fire: FireIndicator = FireIndicator.CLEAR

    @property
    def fire_lock(self) -> bool:
        """True bei Brand irgendwo oder unklarem Brandzustand an einer registrierten Sirene."""
        if self.external_fire is FireIndicator.ACTIVE:
            return True
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


def is_fire_tone(tone: str) -> bool:
    """Brandton? Auch bei herstellereigenen Namen ("FIRE_ALARM", "Brand")."""
    name = tone.lower()
    return tone in FIRE_TONES or "fire" in name or "brand" in name or "smoke" in name


def expert_fire_tone_ok(device: SirenDevice) -> bool:
    """Experten-Freigabe eines Brandtons – nie an einem Gerät mit eigenen Brandsensoren."""
    return device.fire_tone_allowed and not device.fire_detector


def select_tone(requested: str, device: SirenDevice) -> tuple[bool, str | None]:
    """Ton für ein Gerät: (erlaubt, Ton oder None = ohne Tonangabe senden)."""
    caps = device.capabilities
    # Fest eingestellter Ton – sofern das Gerät ihn kennt (bzw. keine Liste meldet)
    preferred = device.tone
    if (
        caps.tones_supported
        and preferred
        and (not is_fire_tone(preferred) or expert_fire_tone_ok(device))
        and (not caps.tones or preferred in caps.tones)
    ):
        return (True, preferred)
    if not caps.tones_supported:
        # Ohne Tonauswahl spielt das Gerät seinen Standardton. Bei Rauchmeldern ist das
        # meist der Brandton – das darf ein Einbruchalarm nie auslösen.
        return (not device.fire_detector, None)
    if not caps.tones:
        return (True, requested)
    for tone in (requested, *BURGLAR_TONE_ORDER):
        if tone in caps.tones and not is_fire_tone(tone):
            return (True, tone)
    return (False, None)


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
        caps = device.capabilities
        if caps.duration and device.max_duration <= 0:
            blocked.append(BlockedCommand(key, BlockReason.INVALID_DURATION))
            continue
        if not caps.duration and not caps.turn_off:
            blocked.append(BlockedCommand(key, BlockReason.CANNOT_LIMIT))
            continue
        allowed, tone = select_tone(request.tone, device)
        if not allowed:
            blocked.append(BlockedCommand(key, BlockReason.NO_BURGLAR_TONE))
            continue
        commands.append(
            SirenCommand(
                action="turn_on",
                device_key=key,
                entity_id=device.entity_id,
                tone=tone,
                volume_level=VOLUME_LEVELS[request.volume] if caps.volume else None,
                duration=min(request.duration, device.max_duration) if caps.duration else None,
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
        elif not device.capabilities.turn_off:
            blocked.append(BlockedCommand(key, BlockReason.TURN_OFF_UNSUPPORTED))
        else:
            commands.append(
                SirenCommand(action="turn_off", device_key=key, entity_id=device.entity_id)
            )
    return GuardDecision(commands=tuple(commands), blocked=tuple(blocked))
