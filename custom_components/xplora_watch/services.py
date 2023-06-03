"""Support for Xplora® Watch Version 2 send/read message, manually refresh and shutdown."""
from __future__ import annotations

import logging
from typing import Dict

import voluptuous as vol
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
from .helper import encoded_base64_string_to_file, encoded_base64_string_to_mp3_file

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
async def async_setup_services(hass: HomeAssistant, coordinator: XploraDataUpdateCoordinator) -> None:
    """Set up services for Xplora® Watch integration."""

    delete_message_from_app_service = XploraDeleteMessageFromAppService(hass, coordinator)
    shutdown_service = XploraShutdownService(hass, coordinator)
    sensor_update_service = XploraMessageSensorUpdateService(hass, coordinator)
    notify_service = XploraMessageService(hass, coordinator)
    see_service = XploraSeeService(hass, coordinator)

    async def async_see(service: ServiceCall) -> None:
        kwargs = dict(service.data)
        await see_service.async_see(kwargs[ATTR_SERVICE_TARGET] if ATTR_SERVICE_TARGET in kwargs else ["all"])

    async def async_delete_message_from_app(service: ServiceCall) -> None:
        kwargs = dict(service.data)
        await delete_message_from_app_service.async_delete_message_from_app(
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
    async def async_see(self, targets: list[str] | None = None, **kwargs):
        """Update all information from Watch"""
        if isinstance(targets, list):
            if "all" in targets:
                targets = self._coordinator.controller.getWatchUserIDs()
            _LOGGER.debug("update all information: %s", {", ".join(targets)})
            await self._coordinator._async_update_data(targets)
            # await self._coordinator.async_refresh()
        else:
            _LOGGER.warning("No watch id or type %s not allow!", type(targets))


class XploraDeleteMessageFromAppService(XploraService):
    async def async_delete_message_from_app(self, message_id="", targets: list[str] | None = None, **kwargs):
        """Delete a message to one Watch."""
        if isinstance(targets, list):
            msg_id = message_id.strip()
            if "all" in targets:
                targets = self._coordinator.controller.getWatchUserIDs()
            if not msg_id:
                _LOGGER.warning("You must provide an ID!")
            else:
                for watch_id in targets:
                    _LOGGER.debug("remove message %s from %s", msg_id, watch_id)
                    if not await self._coordinator.controller.deleteMessageFromApp(wuid=watch_id, msgId=msg_id):
                        _LOGGER.error("Message cannot deleted!")
        else:
            _LOGGER.warning("No watch id or type %s not allow!", type(targets))


class XploraMessageService(XploraService):
    async def async_send_message(self, message="", targets: list[str] | None = None, **kwargs):
        """Send message to Watch."""
        if isinstance(targets, list):
            msg = message.strip()
            if "all" in targets:
                targets = self._coordinator.controller.getWatchUserIDs()
            if not msg:
                _LOGGER.warning("Message is empty!")
            else:
                for watch_id in targets:
                    _LOGGER.debug("Sending message '%s' to '%s'", msg, watch_id)
                    if not await self._coordinator.controller.sendText(text=msg, wuid=watch_id):
                        _LOGGER.error("Message cannot send!")
        else:
            _LOGGER.warning("No watch id or type %s not allowed!", type(targets))


class XploraMessageSensorUpdateService(XploraService):
    async def async_read_message(self, targets: list[str] | None = None, **kwargs):
        """Read the messages from account"""
        if not isinstance(targets, list):
            _LOGGER.warning("No watch id or type %s not allowed!", type(targets))
            return
        old_state: Dict[str, any] = self._coordinator.data
        options = self._coordinator.config_entry.options
        limit: int = options.get(CONF_MESSAGE, 10)
        show_remove_msg = options.get(CONF_REMOVE_MESSAGE, False)
        if "all" in targets:
            targets = self._coordinator.controller.getWatchUserIDs()
        for watch in targets:
            res_chats = await self._coordinator.message_data(watch, limit, show_remove_msg)
            if res_chats:
                for chat in res_chats.get("list"):
                    chat_type = chat.get("type")
                    msg_id = chat.get("msgId")
                    if chat_type == "VOICE":
                        await self._fetch_chat_voice(watch, msg_id)
                    elif chat_type == "SHORT_VIDEO":
                        await self._fetch_chat_short_video(watch, msg_id)
                    elif chat_type == "IMAGE":
                        await self._fetch_chat_image(watch, msg_id)
                new_data_msg: Dict[str, any] = old_state.get(watch, {}) if isinstance(old_state, dict) else {}
                if new_data_msg:
                    new_data_msg.update({SENSOR_MESSAGE: res_chats})
                    old_state.update({watch: new_data_msg})
        await self._coordinator._async_update_data(new_data=old_state)

    async def _fetch_chat_voice(self, watch_id: str, msg_id: str) -> None:
        voice: Dict[str, any] = await self._coordinator.controller._gql_handler.fetchChatVoice_a(watch_id, msg_id)
        encoded_base64_string_to_mp3_file(self._hass, voice.get("fetchChatVoice"), msg_id)

    async def _fetch_chat_short_video(self, watch_id: str, msg_id: str) -> None:
        video: Dict[str, any] = await self._coordinator.controller._gql_handler.fetchChatShortVideo_a(watch_id, msg_id)
        encoded_base64_string_to_file(self._hass, video.get("fetchChatShortVideo"), msg_id, "mp4", "video")
        thumb: Dict[str, any] = await self._coordinator.controller._gql_handler.fetchChatShortVideoCover_a(watch_id, msg_id)
        encoded_base64_string_to_file(self._hass, thumb.get("fetchChatShortVideoCover"), msg_id, "jpeg", "video/thumb")

    async def _fetch_chat_image(self, watch, msg_id):
        image = await self._coordinator.controller._gql_handler.fetchChatImage_a(watch, msg_id)
        encoded_base64_string_to_file(self._hass, image.get("fetchChatImage"), msg_id, "jpeg", "image")


class XploraShutdownService(XploraService):
    async def async_shutdown(self, targets: list[str] | None = None, **kwargs):
        """turn off watch"""
        if isinstance(targets, list):
            if "all" in targets:
                targets = self._coordinator.controller.getWatchUserIDs()
            for watch in targets:
                try:
                    _LOGGER.debug("Shutdown result: %s", await self._coordinator.controller.shutdown(watch))
                except NoAdminError as error:
                    _LOGGER.exception("Shutdown failed! Error: %s", error)
        else:
            _LOGGER.warning("No watch ID or type %s not allowed!", type(targets))
