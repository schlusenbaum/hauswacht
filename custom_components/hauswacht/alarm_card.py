"""Alarmkarte: Scharf- und Unscharfschalten aus dem Dashboard, ohne PIN-Zwang.

Die Karte "Hauswacht Alarm" schaltet nicht über die Alarm-Schnittstelle von Home Assistant
(die verlangt von allen einen PIN, sobald irgendeiner existiert), sondern über zwei eigene
WebSocket-Befehle. Ausweis ist das angemeldete Home-Assistant-Konto:

- Konto einem Hauswacht-Benutzer zugeordnet: dessen Rechte je Bereich; PIN nur, wenn beim
  Benutzer "In der Alarmkarte PIN verlangen" an ist (z. B. Wandtablet).
- Konto ohne Benutzer: PIN, solange unter PIN-Regeln "Alarmkarte: PIN für Konten ohne
  Hauswacht-Benutzer" an ist (Standard).
- Gibt es gar keinen PIN, fragt die Karte nie danach.

Wer einen PIN eingeben muss, durchläuft dieselbe Prüfung wie am Bedienfeld (Sperre nach
Falscheingaben, Bedrohungs-PIN). Zusätzlich braucht das Konto das Recht, das Bedienfeld des
Bereichs zu steuern (Home-Assistant-Berechtigungen).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.auth.models import User as HaUser
from homeassistant.auth.permissions.const import POLICY_CONTROL
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .core.areas import MAIN_AREA
from .core.profiles import profile_info
from .core.state_machine import AlarmState
from .core.users import Action, card_needs_pin, find_by_ha_user
from .core.users import label as users_label

if TYPE_CHECKING:
    from .runtime import HauswachtRuntime

WS_INFO = f"{DOMAIN}/alarm/info"
WS_ACTION = f"{DOMAIN}/alarm/action"
DATA_WS = f"{DOMAIN}_alarm_ws_registered"
ACTIONS = ("arm", "disarm", "end_alarm")
_IN_ALARM = (AlarmState.TRIGGERED, AlarmState.ALARM_HOLD)


def _main(hass: HomeAssistant) -> HauswachtRuntime | None:
    for entry in hass.config_entries.async_loaded_entries(DOMAIN):
        runtime = getattr(entry, "runtime_data", None)
        if runtime is not None:
            return runtime  # type: ignore[no-any-return]
    return None


def panel_entity_id(hass: HomeAssistant, area: HauswachtRuntime) -> str | None:
    """Bedienfeld des Bereichs (über die eindeutige ID, nicht über den Namen)."""
    entry_id = area.entry.entry_id
    unique = (
        f"{entry_id}_panel" if area.area_id == MAIN_AREA else f"{entry_id}_{area.area_id}_panel"
    )
    return er.async_get(hass).async_get_entity_id("alarm_control_panel", DOMAIN, unique)


def _may_control(hass: HomeAssistant, user: HaUser, area: HauswachtRuntime) -> str | None:
    """Bedienfeld-ID, wenn das Konto es steuern darf – sonst None."""
    entity_id = panel_entity_id(hass, area)
    if entity_id is None:
        return None
    if not user.permissions.check_entity(entity_id, POLICY_CONTROL):
        return None
    return entity_id


def build_info(hass: HomeAssistant, main: HauswachtRuntime, user: HaUser) -> dict[str, Any]:
    """Was die Karte für dieses Konto zeigen soll: Bereiche, Profile, PIN-Bedarf, Rechte."""
    needs_pin = card_needs_pin(main.users, user.id, unlinked_pin=main.card_unlinked_pin)
    linked = find_by_ha_user(main.users, user.id)
    now = dt_util.utcnow().timestamp()
    options = main.entry.options
    areas = []
    for area in main.areas.values():
        entity_id = _may_control(hass, user, area)
        if entity_id is None:
            continue
        if needs_pin or linked is None:
            # Wer es ist, entscheidet erst der PIN – bzw. Konto ohne Benutzer: alles erlaubt
            may = dict.fromkeys(ACTIONS, True)
        else:
            valid = linked.valid_at(now)
            may = {a.value: valid and linked.may_in(a, area.area_id) for a in Action}
        areas.append(
            {
                "id": area.area_id,
                "name": area.area_name,
                "entity_id": entity_id,
                "profiles": [
                    {
                        "id": pid,
                        "name": area.profile_name(pid),
                        "icon": profile_info(options, pid).icon,
                    }
                    for pid in area.profiles
                ],
                "pin": {
                    "arm": needs_pin and area.code_arm_required,
                    "disarm": needs_pin,
                    "end_alarm": needs_pin and area.end_alarm_needs_code,
                },
                "may": may,
            }
        )
    return {
        "user": linked.name if linked is not None else user.name,
        "linked": linked is not None,
        "pin": needs_pin,
        "areas": areas,
    }


async def _actor(
    area: HauswachtRuntime,
    user: HaUser,
    actions: list[Action],
    *,
    pin: bool,
    code: str | None,
) -> str | None:
    """Wer schaltet? Mit PIN wie am Bedienfeld, sonst über das Konto (mit dessen Rechten)."""
    if pin:
        if not code:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="card_pin_required"
            )
        identity = await area.async_identify(code, actions[0])
        if not identity.duress:
            for action in actions:
                area.check_allowed(identity.users, action)
        return users_label(identity.users, area.lang)
    actor: str | None = None
    for action in actions:
        actor = await area.async_actor_for_user(user.id, action)
    return actor


async def async_card_action(  # noqa: PLR0913
    hass: HomeAssistant,
    main: HauswachtRuntime,
    user: HaUser,
    *,
    area_id: str,
    action: str,
    profile: str | None = None,
    code: str | None = None,
    force: bool = False,
) -> None:
    """Eine Aktion der Karte ausführen; Fehler als HomeAssistantError (mit Klartext)."""
    area = main.areas.get(area_id)
    if area is None or _may_control(hass, user, area) is None:
        raise ServiceValidationError(translation_domain=DOMAIN, translation_key="card_no_access")
    needs_pin = card_needs_pin(main.users, user.id, unlinked_pin=main.card_unlinked_pin)
    in_alarm = area.ctx.state in _IN_ALARM
    if action == "arm":
        if not profile:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="unknown_profile",
                translation_placeholders={"profile": "-"},
            )
        actor = await _actor(
            area, user, [Action.ARM], pin=needs_pin and area.code_arm_required, code=code
        )
        area.arm(profile, confirmed=force, changed_by=actor)
    elif action == "end_alarm":
        actor = await _actor(
            area, user, [Action.END_ALARM], pin=needs_pin and area.end_alarm_needs_code, code=code
        )
        area.end_alarm(actor)
    else:  # disarm: auch während eines Alarms ganz unscharf
        wanted = [Action.DISARM, Action.END_ALARM] if in_alarm else [Action.DISARM]
        actor = await _actor(area, user, wanted, pin=needs_pin, code=code)
        if in_alarm:
            area.disarm_now(actor)
        else:
            area.disarm_trusted(actor)


@websocket_api.websocket_command({vol.Required("type"): WS_INFO})
@callback
def ws_info(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    main = _main(hass)
    if main is None:
        connection.send_error(msg["id"], "not_loaded", "Hauswacht ist nicht geladen.")
        return
    connection.send_result(msg["id"], build_info(hass, main, connection.user))


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_ACTION,
        vol.Required("area"): str,
        vol.Required("action"): vol.In(ACTIONS),
        vol.Optional("profile"): str,
        vol.Optional("code"): vol.Any(str, None),
        vol.Optional("force", default=False): bool,
    }
)
@websocket_api.async_response
async def ws_action(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    main = _main(hass)
    if main is None:
        connection.send_error(msg["id"], "not_loaded", "Hauswacht ist nicht geladen.")
        return
    try:
        await async_card_action(
            hass,
            main,
            connection.user,
            area_id=msg["area"],
            action=msg["action"],
            profile=msg.get("profile"),
            code=msg.get("code"),
            force=msg["force"],
        )
    except HomeAssistantError as err:
        key = getattr(err, "translation_key", None) or "error"
        connection.send_result(
            msg["id"],
            {
                "ok": False,
                "error": key,
                "message": str(err) or key,
                "can_force": key == "confirmation_required",
            },
        )
        return
    connection.send_result(msg["id"], {"ok": True})


@callback
def async_register_alarm_websocket(hass: HomeAssistant) -> None:
    if hass.data.get(DATA_WS):
        return
    websocket_api.async_register_command(hass, ws_info)
    websocket_api.async_register_command(hass, ws_action)
    hass.data[DATA_WS] = True
