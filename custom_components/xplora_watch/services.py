"""Support for Xplora® Watch Version 2 send message and manually refresh."""
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, callback

import homeassistant.helpers.config_validation as cv

from .const import ATTR_SERVICE_MSG, ATTR_SERVICE_SEE, ATTR_SERVICE_SEND_MSG, ATTR_SERVICE_TARGET, DOMAIN
from .coordinator import XploraDataUpdateCoordinator


BASE_NOTIFY_SERVICE_SCHEMA = vol.Schema(
    {vol.Required(ATTR_SERVICE_TARGET): vol.All(cv.ensure_list, [cv.string]), vol.Required(ATTR_SERVICE_MSG): cv.string},
    extra=vol.ALLOW_EXTRA,
)
BASE_SEE_SERVICE_SCHEMA = vol.Schema(
    {vol.Optional(ATTR_SERVICE_TARGET): vol.All(cv.ensure_list, [cv.string])}, extra=vol.ALLOW_EXTRA
)

_LOGGER = logging.getLogger(__name__)


@callback
def async_setup_services(hass: HomeAssistant, coordinator: XploraDataUpdateCoordinator) -> None:
    """Set up services for Xplora® Watch integration."""

    notify_service = XploraNotificationService(hass, coordinator)
    see_service = XploraSeeService(hass, coordinator)

    async def async_see(service: ServiceCall) -> None:
        kwargs = dict(service.data)
        _LOGGER.debug(kwargs)
        await see_service.async_see(kwargs[ATTR_SERVICE_TARGET] if ATTR_SERVICE_TARGET in kwargs else ["all"])

    async def async_send_xplora_message(service: ServiceCall) -> None:
        kwargs = dict(service.data)
        _LOGGER.debug(kwargs)
        await notify_service.async_send_message(kwargs[ATTR_SERVICE_MSG], kwargs[ATTR_SERVICE_TARGET])

    hass.services.async_register(DOMAIN, ATTR_SERVICE_SEND_MSG, async_send_xplora_message, schema=BASE_NOTIFY_SERVICE_SCHEMA)
    hass.services.async_register(DOMAIN, ATTR_SERVICE_SEE, async_see, schema=BASE_SEE_SERVICE_SCHEMA)


@callback
def async_unload_services(hass: HomeAssistant) -> None:
    """Unload Xplora® Watch send_message services."""
    hass.services.async_remove(DOMAIN, ATTR_SERVICE_SEND_MSG)
    hass.services.async_remove(DOMAIN, ATTR_SERVICE_SEE)


class XploraService:
    def __init__(self, hass: HomeAssistant, coordinator: XploraDataUpdateCoordinator) -> None:
        self._hass = hass
        self._controller = coordinator.controller
        self._coordinator = coordinator


class XploraSeeService(XploraService):
    def __init__(self, hass: HomeAssistant, coordinator: XploraDataUpdateCoordinator) -> None:
        super().__init__(hass, coordinator)

    async def async_see(self, targets: list[str] = None, **kwargs):
        if "all" in targets[0]:
            targets = self._controller.getWatchUserIDs()
        await self._coordinator._async_update_watch_data(targets)
        self._coordinator._schedule_refresh()
        self._coordinator.async_update_listeners()


class XploraNotificationService(XploraService):
    def __init__(self, hass: HomeAssistant, coordinator: XploraDataUpdateCoordinator) -> None:
        super().__init__(hass, coordinator)

    async def async_send_message(self, message="", target=None, **kwargs):
        """Send a message to one Watch."""
        msg = message.strip()
        _LOGGER.debug(f"sent message '{msg}' to {target}")
        if not target:
            _LOGGER.warning("No watch id!")
        if len(msg) > 0:
            for watch_id in target:
                if not await self._controller.sendText(text=msg, wuid=watch_id):
                    _LOGGER.error("Message cannot send!")
        else:
            _LOGGER.warning("Your message is empty!")
