"""Support for Xplora® Watch Version 2 send/read message, manually refresh and shutdown."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant, ServiceCall, callback
import homeassistant.helpers.config_validation as cv
from pyxplora_api.exception_classes import NoAdminError
import voluptuous as vol

from .const import (
    ATTR_SERVICE_DELETE_MSG,
    ATTR_SERVICE_MSG,
    ATTR_SERVICE_MSGID,
    ATTR_SERVICE_READ_MSG,
    ATTR_SERVICE_SEE,
    ATTR_SERVICE_SEND_MSG,
    ATTR_SERVICE_SHUTDOWN,
    ATTR_SERVICE_TARGET,
    ATTR_SERVICE_USER,
    CONF_MESSAGE,
    CONF_REMOVE_MESSAGE,
    DOMAIN,
    SENSOR_MESSAGE,
)
from .coordinator import XploraDataUpdateCoordinator
from .helper import encoded_base64_string_to_file, encoded_base64_string_to_mp3_file

BASE_SHUTDOWN_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_SERVICE_TARGET): vol.All(cv.ensure_list, [cv.string]),
        vol.Required(ATTR_SERVICE_USER): vol.All(cv.ensure_list, [cv.string]),
    },
    extra=vol.ALLOW_EXTRA,
)
BASE_DELETE_MESSAGE_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_SERVICE_TARGET): vol.All(cv.ensure_list, [cv.string]),
        vol.Required(ATTR_SERVICE_MSGID): cv.string,
        vol.Required(ATTR_SERVICE_USER): vol.All(cv.ensure_list, [cv.string]),
    },
    extra=vol.ALLOW_EXTRA,
)
BASE_READ_MESSAGE_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_SERVICE_TARGET): vol.All(cv.ensure_list, [cv.string]),
        vol.Required(ATTR_SERVICE_USER): vol.All(cv.ensure_list, [cv.string]),
    },
    extra=vol.ALLOW_EXTRA,
)
BASE_SEND_MESSAGE_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_SERVICE_TARGET): vol.All(cv.ensure_list, [cv.string]),
        vol.Required(ATTR_SERVICE_MSG): cv.string,
        vol.Required(ATTR_SERVICE_USER): vol.All(cv.ensure_list, [cv.string]),
    },
    extra=vol.ALLOW_EXTRA,
)
BASE_SEE_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_SERVICE_TARGET): vol.All(cv.ensure_list, [cv.string]),
        vol.Required(ATTR_SERVICE_USER): vol.All(cv.ensure_list, [cv.string]),
    },
    extra=vol.ALLOW_EXTRA,
)

_LOGGER = logging.getLogger(__name__)


@callback
async def async_setup_services(hass: HomeAssistant, entry_id: str) -> None:
    """Set up services for Xplora® Watch integration."""

    delete_message_from_app_service = XploraDeleteMessageFromAppService(hass, entry_id)
    shutdown_service = XploraShutdownService(hass, entry_id)
    sensor_update_service = XploraMessageSensorUpdateService(hass, entry_id)
    notify_service = XploraMessageService(hass, entry_id)
    see_service = XploraSeeService(hass, entry_id)

    async def async_see(service: ServiceCall) -> None:
        kwargs = dict(service.data)
        await see_service.async_see(kwargs.get(ATTR_SERVICE_TARGET, ["all"]), kwargs=kwargs)

    async def async_delete_message_from_app(service: ServiceCall) -> None:
        kwargs = dict(service.data)
        await delete_message_from_app_service.async_delete_message_from_app(
            kwargs[ATTR_SERVICE_MSGID], kwargs[ATTR_SERVICE_TARGET], kwargs=kwargs
        )

    async def async_send_message(service: ServiceCall) -> None:
        kwargs = dict(service.data)
        await notify_service.async_send_message(kwargs[ATTR_SERVICE_MSG], kwargs[ATTR_SERVICE_TARGET], kwargs=kwargs)

    async def async_read_message(service: ServiceCall) -> None:
        kwargs = dict(service.data)
        await sensor_update_service.async_read_message(kwargs[ATTR_SERVICE_TARGET], kwargs=kwargs)

    async def async_shutdown(service: ServiceCall) -> None:
        kwargs = dict(service.data)
        await shutdown_service.async_shutdown(kwargs[ATTR_SERVICE_TARGET], kwargs=kwargs)

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
    """Common base for Xplora® service."""

    def __init__(self, hass: HomeAssistant, entry_id) -> None:
        """Initialize the entry."""
        self._hass = hass
        self._entry_id = entry_id


class XploraSeeService(XploraService):
    """Create a service that can be update information from Watch."""

    async def async_see(self, targets: list[str] | None = None, **kwargs):
        """Update watch information."""
        entry_id = str(kwargs["kwargs"]["user"][0]).split(" ", maxsplit=1)[0]
        coordinator: XploraDataUpdateCoordinator = self._hass.data[DOMAIN][entry_id]
        if isinstance(targets, list):
            if "all" in targets:
                targets = coordinator.controller.getWatchUserIDs()
            _LOGGER.debug("%s: update all information: %s", coordinator.controller.getUserName(), {", ".join(targets)})
            await coordinator.async_update_xplora_data(targets)
            # await self._coordinator.async_refresh()
        else:
            _LOGGER.warning("No watch id or type %s not allow!", type(targets))


class XploraDeleteMessageFromAppService(XploraService):
    """Create a service that can be remove message from Watch."""

    async def async_delete_message_from_app(self, message_id="", targets: list[str] | None = None, **kwargs):
        """Delete a message to one Watch."""
        entry_id = str(kwargs["kwargs"]["user"][0]).split(" ", maxsplit=1)[0]
        coordinator: XploraDataUpdateCoordinator = self._hass.data[DOMAIN][entry_id]
        if isinstance(targets, list):
            msg_id = message_id.strip()
            if "all" in targets:
                targets = coordinator.controller.getWatchUserIDs()
            if not msg_id:
                _LOGGER.warning("You must provide an ID!")
            else:
                for watch_id in targets:
                    _LOGGER.debug("remove message %s from %s", msg_id, watch_id)
                    if not await coordinator.controller.deleteMessageFromApp(wuid=watch_id, msgId=msg_id):
                        _LOGGER.error("Message cannot deleted!")
        else:
            _LOGGER.warning("No watch id or type %s not allow!", type(targets))


class XploraMessageService(XploraService):
    """Create a service that can be send message to Watch."""

    async def async_send_message(self, message="", targets: list[str] | None = None, **kwargs):
        """Send message to Watch."""
        entry_id = str(kwargs["kwargs"]["user"][0]).split(" ", maxsplit=1)[0]
        coordinator: XploraDataUpdateCoordinator = self._hass.data[DOMAIN][entry_id]
        if isinstance(targets, list):
            msg = message.strip()
            if "all" in targets:
                targets = coordinator.controller.getWatchUserIDs()
            if not msg:
                _LOGGER.warning("Message is empty!")
            else:
                for watch_id in targets:
                    _LOGGER.debug("Sending message '%s' to '%s'", msg, watch_id)
                    if not await coordinator.controller.sendText(text=msg, wuid=watch_id):
                        _LOGGER.error("Message cannot send!")
        else:
            _LOGGER.warning("No watch id or type %s not allowed!", type(targets))


class XploraMessageSensorUpdateService(XploraService):
    """Create a service that can be used to read messages from Watch."""

    coordinator: XploraDataUpdateCoordinator

    async def async_read_message(self, targets: list[str] | None = None, **kwargs):
        """Read the messages from account."""
        entry_id = str(kwargs["kwargs"]["user"][0]).split(" ", maxsplit=1)[0]
        self.coordinator = self._hass.data[DOMAIN][entry_id]
        if not isinstance(targets, list):
            _LOGGER.warning("No watch id or type %s not allowed!", type(targets))
            return
        old_state: dict[str, Any] = self.coordinator.data
        options = self.coordinator.config_entry.options
        limit: int = options.get(CONF_MESSAGE, 10)
        show_remove_msg = options.get(CONF_REMOVE_MESSAGE, False)
        if "all" in targets:
            targets = self.coordinator.controller.getWatchUserIDs()
        for watch in targets:
            res_chats = await self.coordinator.message_data(watch, limit, show_remove_msg)
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
                new_data_msg: dict[str, Any] = old_state.get(watch, {}) if isinstance(old_state, dict) else {}
                if new_data_msg:
                    new_data_msg.update({SENSOR_MESSAGE: res_chats})
                    old_state.update({watch: new_data_msg})
        await self.coordinator.async_update_xplora_data(new_data=old_state)

    async def _fetch_chat_voice(self, watch_id: str, msg_id: str) -> None:
        voice = await self.coordinator.controller.get_chat_voice(watch_id, msg_id)
        if voice:
            encoded_base64_string_to_mp3_file(self._hass, voice, msg_id)

    async def _fetch_chat_short_video(self, watch_id: str, msg_id: str) -> None:
        video = await self.coordinator.controller.get_short_video(watch_id, msg_id)
        if video:
            encoded_base64_string_to_file(self._hass, video, msg_id, "mp4", "video")
        thumb = await self.coordinator.controller.get_short_video_cover(watch_id, msg_id)
        if thumb:
            encoded_base64_string_to_file(self._hass, thumb, msg_id, "jpeg", "video/thumb")

    async def _fetch_chat_image(self, watch, msg_id):
        image = await self.coordinator.controller.get_chat_image(watch, msg_id)
        if image:
            encoded_base64_string_to_file(self._hass, image, msg_id, "jpeg", "image")


class XploraShutdownService(XploraService):
    """Create a service that shuts down Xplora."""

    async def async_shutdown(self, targets: list[str] | None = None, **kwargs):
        """Turn off watch."""
        entry_id = str(kwargs["kwargs"]["user"][0]).split(" ", maxsplit=1)[0]
        coordinator: XploraDataUpdateCoordinator = self._hass.data[DOMAIN][entry_id]
        if isinstance(targets, list):
            if "all" in targets:
                targets = coordinator.controller.getWatchUserIDs()
            for watch in targets:
                try:
                    _LOGGER.debug("Shutdown result: %s", await coordinator.controller.shutdown(watch))
                except NoAdminError as error:
                    _LOGGER.exception("Shutdown failed! Error: %s", error)
        else:
            _LOGGER.warning("No watch ID or type %s not allowed!", type(targets))
