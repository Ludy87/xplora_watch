"""Support for Xplora® Watch Version 2 send message and manually refresh."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.core import HomeAssistant, ServiceCall, callback

from .const import (
    ATTR_SERVICE_MSG,
    ATTR_SERVICE_READ_MSG,
    ATTR_SERVICE_SEE,
    ATTR_SERVICE_SEND_MSG,
    ATTR_SERVICE_TARGET,
    CONF_MESSAGE,
    DOMAIN,
    SENSOR_MESSAGE,
)
from .coordinator import XploraDataUpdateCoordinator

BASE_READ_MESSAGE_SERVICE_SCHEMA = vol.Schema(
    {vol.Required(ATTR_SERVICE_TARGET): vol.All(cv.ensure_list, [cv.string])}, extra=vol.ALLOW_EXTRA
)
BASE_NOTIFY_SERVICE_SCHEMA = vol.Schema(
    {vol.Required(ATTR_SERVICE_TARGET): vol.All(cv.ensure_list, [cv.string]), vol.Required(ATTR_SERVICE_MSG): cv.string},
    extra=vol.ALLOW_EXTRA,
)
BASE_SEE_SERVICE_SCHEMA = vol.Schema(
    {vol.Required(ATTR_SERVICE_TARGET): vol.All(cv.ensure_list, [cv.string])}, extra=vol.ALLOW_EXTRA
)

_LOGGER = logging.getLogger(__name__)


@callback
def async_setup_services(hass: HomeAssistant, coordinator: XploraDataUpdateCoordinator) -> None:
    """Set up services for Xplora® Watch integration."""

    sensor_update_service = XploraMessageSensorUpdateService(hass, coordinator)
    notify_service = XploraMessageService(hass, coordinator)
    see_service = XploraSeeService(hass, coordinator)

    async def async_see(service: ServiceCall) -> None:
        kwargs = dict(service.data)
        await see_service.async_see(kwargs[ATTR_SERVICE_TARGET] if ATTR_SERVICE_TARGET in kwargs else ["all"])

    async def async_send_xplora_message(service: ServiceCall) -> None:
        kwargs = dict(service.data)
        await notify_service.async_send_message(kwargs[ATTR_SERVICE_MSG], kwargs[ATTR_SERVICE_TARGET])

    async def async_read_message(service: ServiceCall) -> None:
        kwargs = dict(service.data)
        await sensor_update_service.async_read_message(kwargs[ATTR_SERVICE_TARGET])

    hass.services.async_register(DOMAIN, ATTR_SERVICE_READ_MSG, async_read_message, schema=BASE_READ_MESSAGE_SERVICE_SCHEMA)
    hass.services.async_register(DOMAIN, ATTR_SERVICE_SEND_MSG, async_send_xplora_message, schema=BASE_NOTIFY_SERVICE_SCHEMA)
    hass.services.async_register(DOMAIN, ATTR_SERVICE_SEE, async_see, schema=BASE_SEE_SERVICE_SCHEMA)


@callback
def async_unload_services(hass: HomeAssistant) -> None:
    """Unload Xplora® Watch send_message services."""
    hass.services.async_remove(DOMAIN, ATTR_SERVICE_READ_MSG)
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

    async def async_see(self, targets=None, **kwargs):
        if isinstance(targets, list):
            if "all" in targets:
                targets = self._controller.getWatchUserIDs()
            _LOGGER.debug(f"update all information for '{targets}'")
            await self._coordinator._async_update_watch_data(targets)
            self._coordinator._schedule_refresh()
            self._coordinator.async_update_listeners()
        else:
            _LOGGER.warning(f"No watch id or type '{type(targets)}' not allow!")


class XploraMessageService(XploraService):
    def __init__(self, hass: HomeAssistant, coordinator: XploraDataUpdateCoordinator) -> None:
        super().__init__(hass, coordinator)

    async def async_send_message(self, message="", targets=None, **kwargs):
        """Send a message to one Watch."""
        if isinstance(targets, list):
            msg = message.strip()
            if "all" in targets:
                targets = self._controller.getWatchUserIDs()
            _LOGGER.debug(f"sent message '{msg}' to '{targets}'")
            if len(msg) > 0:
                for watch_id in targets:
                    if not await self._controller.sendText(text=msg, wuid=watch_id):
                        _LOGGER.error("Message cannot send!")
            else:
                _LOGGER.warning("Your message is empty!")
        else:
            _LOGGER.warning(f"No watch id or type '{type(targets)}' not allow!")


class XploraMessageSensorUpdateService(XploraService):
    def __init__(self, hass: HomeAssistant, coordinator: XploraDataUpdateCoordinator) -> None:
        super().__init__(hass, coordinator)

    async def async_read_message(self, targets: list[str] | None = None, **kwargs):
        if isinstance(targets, list):
            old_state: dict[str, Any] = self._coordinator.data
            options = self._coordinator.config_entry.options
            limit = options.get(CONF_MESSAGE, 10)
            if "all" in targets:
                targets = self._controller.getWatchUserIDs()
            for watch in targets:
                w: dict[str, Any] = old_state.get(watch, None)
                if w:
                    await self._controller.init(True)
                    w.update({SENSOR_MESSAGE: (await self._controller.getWatchChatsRaw(watch, limit=limit)).get("chatsNew")})
                old_state.update({watch: w})
            self._coordinator.async_set_updated_data(old_state)
        else:
            _LOGGER.warning(f"No watch id or type '{type(targets)}' not allow!")
