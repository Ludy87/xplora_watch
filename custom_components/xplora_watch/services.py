"""Support for Xplora® Watch Version 2 send/read message, manually refresh and shutdown."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from pyxplora_api import pyxplora_api_async as PXA
from pyxplora_api.exception_classes import NoAdminError

import homeassistant.helpers.config_validation as cv
from homeassistant.core import HomeAssistant, ServiceCall, callback

from .const import (
    ATTR_SERVICE_DELETE_MSG,
    ATTR_SERVICE_MSG,
    ATTR_SERVICE_MSGID,
    ATTR_SERVICE_READ_MSG,
    ATTR_SERVICE_SEE,
    ATTR_SERVICE_SEND_MSG,
    ATTR_SERVICE_SHUTDOWN,
    ATTR_SERVICE_TARGET,
    CONF_MESSAGE,
    CONF_REMOVE_MESSAGE,
    DOMAIN,
    SENSOR_MESSAGE,
)
from .coordinator import XploraDataUpdateCoordinator

BASE_SHUTDOWN_SERVICE_SCHEMA = vol.Schema(
    {vol.Required(ATTR_SERVICE_TARGET): vol.All(cv.ensure_list, [cv.string])}, extra=vol.ALLOW_EXTRA
)
BASE_DELETE_MESSAGE_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_SERVICE_TARGET): vol.All(cv.ensure_list, [cv.string]),
        vol.Required(ATTR_SERVICE_MSGID): cv.string,
    },
    extra=vol.ALLOW_EXTRA,
)
BASE_READ_MESSAGE_SERVICE_SCHEMA = vol.Schema(
    {vol.Required(ATTR_SERVICE_TARGET): vol.All(cv.ensure_list, [cv.string])}, extra=vol.ALLOW_EXTRA
)
BASE_SEND_MESSAGE_SERVICE_SCHEMA = vol.Schema(
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

    delete_chat_message_from_app_service = XploraDeleteMessageFromAppService(hass, coordinator)
    shutdown_service = XploraShutdownService(hass, coordinator)
    sensor_update_service = XploraMessageSensorUpdateService(hass, coordinator)
    notify_service = XploraMessageService(hass, coordinator)
    see_service = XploraSeeService(hass, coordinator)

    async def async_see(service: ServiceCall) -> None:
        kwargs = dict(service.data)
        await see_service.async_see(kwargs[ATTR_SERVICE_TARGET] if ATTR_SERVICE_TARGET in kwargs else ["all"])

    async def async_delete_message_from_app(service: ServiceCall) -> None:
        kwargs = dict(service.data)
        await delete_chat_message_from_app_service.async_delete_message_from_app(
            kwargs[ATTR_SERVICE_MSGID], kwargs[ATTR_SERVICE_TARGET]
        )

    async def async_send_message(service: ServiceCall) -> None:
        kwargs = dict(service.data)
        await notify_service.async_send_message(kwargs[ATTR_SERVICE_MSG], kwargs[ATTR_SERVICE_TARGET])

    async def async_read_message(service: ServiceCall) -> None:
        kwargs = dict(service.data)
        await sensor_update_service.async_read_message(kwargs[ATTR_SERVICE_TARGET])

    async def async_shutdown(service: ServiceCall) -> None:
        kwargs = dict(service.data)
        await shutdown_service.async_shutdown(kwargs[ATTR_SERVICE_TARGET])

    hass.services.async_register(DOMAIN, ATTR_SERVICE_SHUTDOWN, async_shutdown, schema=BASE_SHUTDOWN_SERVICE_SCHEMA)
    hass.services.async_register(
        DOMAIN, ATTR_SERVICE_DELETE_MSG, async_delete_message_from_app, schema=BASE_DELETE_MESSAGE_SERVICE_SCHEMA
    )
    hass.services.async_register(DOMAIN, ATTR_SERVICE_READ_MSG, async_read_message, schema=BASE_READ_MESSAGE_SERVICE_SCHEMA)
    hass.services.async_register(DOMAIN, ATTR_SERVICE_SEND_MSG, async_send_message, schema=BASE_SEND_MESSAGE_SERVICE_SCHEMA)
    hass.services.async_register(DOMAIN, ATTR_SERVICE_SEE, async_see, schema=BASE_SEE_SERVICE_SCHEMA)


@callback
def async_unload_services(hass: HomeAssistant) -> None:
    """Unload Xplora® Watch send_message services."""
    hass.services.async_remove(DOMAIN, ATTR_SERVICE_SHUTDOWN)
    hass.services.async_remove(DOMAIN, ATTR_SERVICE_DELETE_MSG)
    hass.services.async_remove(DOMAIN, ATTR_SERVICE_READ_MSG)
    hass.services.async_remove(DOMAIN, ATTR_SERVICE_SEND_MSG)
    hass.services.async_remove(DOMAIN, ATTR_SERVICE_SEE)


class XploraService:
    def __init__(self, hass: HomeAssistant, coordinator: XploraDataUpdateCoordinator) -> None:
        self._hass = hass
        self._coordinator = coordinator


class XploraSeeService(XploraService):
    def __init__(self, hass: HomeAssistant, coordinator: XploraDataUpdateCoordinator) -> None:
        super().__init__(hass, coordinator)

    async def async_see(self, targets: list[str] | None = None, **kwargs):
        """Update all information from Watch"""
        _controller: PXA.PyXploraApi = await self._coordinator.init()
        if isinstance(targets, list):
            if "all" in targets:
                targets = _controller.getWatchUserIDs()
            _LOGGER.debug(f"update all information for '{targets}'")
            await self._coordinator._async_update_watch_data(targets)
            self._coordinator._schedule_refresh()
            self._coordinator.async_update_listeners()
        else:
            _LOGGER.warning(f"No watch id or type '{type(targets)}' not allow!")


class XploraDeleteMessageFromAppService(XploraService):
    def __init__(self, hass: HomeAssistant, coordinator: XploraDataUpdateCoordinator) -> None:
        super().__init__(hass, coordinator)

    async def async_delete_message_from_app(self, message_id="", targets: list[str] | None = None, **kwargs):
        """Delete a message to one Watch."""
        _controller: PXA.PyXploraApi = await self._coordinator.init()
        if isinstance(targets, list):
            msg_id = message_id.strip()
            if "all" in targets:
                targets = _controller.getWatchUserIDs()
            if len(msg_id) > 0:
                for watch_id in targets:  # HIER GEHTS WEITER
                    _LOGGER.debug(f"remove message '{msg_id}' from '{watch_id}'")
                    if not await _controller.deleteMessageFromApp(wuid=watch_id, msgId=msg_id):
                        _LOGGER.error("Message cannot deleted!")
            else:
                _LOGGER.warning("You must provide an ID!")
        else:
            _LOGGER.warning(f"No watch id or type '{type(targets)}' not allow!")


class XploraMessageService(XploraService):
    def __init__(self, hass: HomeAssistant, coordinator: XploraDataUpdateCoordinator) -> None:
        super().__init__(hass, coordinator)

    async def async_send_message(self, message="", targets: list[str] | None = None, **kwargs):
        """Send a message to one Watch."""
        _controller: PXA.PyXploraApi = await self._coordinator.init()
        if isinstance(targets, list):
            msg = message.strip()
            if "all" in targets:
                targets = _controller.getWatchUserIDs()
            _LOGGER.debug(f"sent message '{msg}' to '{targets}'")
            if len(msg) > 0:
                for watch_id in targets:
                    if not await _controller.sendText(text=msg, wuid=watch_id):
                        _LOGGER.error("Message cannot send!")
            else:
                _LOGGER.warning("Your message is empty!")
        else:
            _LOGGER.warning(f"No watch id or type '{type(targets)}' not allow!")


class XploraMessageSensorUpdateService(XploraService):
    def __init__(self, hass: HomeAssistant, coordinator: XploraDataUpdateCoordinator) -> None:
        super().__init__(hass, coordinator)

    async def async_read_message(self, targets: list[str] | None = None, **kwargs):
        """Read the messages from account"""
        _controller: PXA.PyXploraApi = await self._coordinator.init()
        if isinstance(targets, list):
            old_state: dict[str, Any] = self._coordinator.data
            options = self._coordinator.config_entry.options
            limit = options.get(CONF_MESSAGE, 10)
            show_remove_msg = options.get(CONF_REMOVE_MESSAGE, False)
            if "all" in targets:
                targets = _controller.getWatchUserIDs()
            for watch in targets:
                w: dict[str, Any] = old_state.get(watch, None)
                if w:
                    await _controller.init(True)
                    res_chats = await _controller.getWatchChatsRaw(watch, limit=limit, show_del_msg=show_remove_msg)
                    w.update({SENSOR_MESSAGE: (res_chats)})
                old_state.update({watch: w})
            self._coordinator.async_set_updated_data(old_state)
        else:
            _LOGGER.warning(f"No watch id or type '{type(targets)}' not allow!")


class XploraShutdownService(XploraService):
    def __init__(self, hass: HomeAssistant, coordinator: XploraDataUpdateCoordinator) -> None:
        super().__init__(hass, coordinator)

    async def async_shutdown(self, targets: list[str] | None = None, **kwargs):
        """turn off watch"""
        _controller: PXA.PyXploraApi = await self._coordinator.init()
        if isinstance(targets, list):
            if "all" in targets:
                targets = _controller.getWatchUserIDs()
            for watch in targets:
                await _controller.init(True)
                try:
                    _LOGGER.debug(f"Shutdown: {await _controller.shutdown(watch)}")
                except NoAdminError as err:
                    _LOGGER.exception(f" Shutdown fail! You have '{err}' Account!")
        else:
            _LOGGER.warning(f"No watch id or type '{type(targets)}' not allow!")
