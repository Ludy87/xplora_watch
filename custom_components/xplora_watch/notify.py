"""Support for Xplora® Watch notifications."""
from __future__ import annotations

import logging

from typing import Any

from homeassistant.components.notify import BaseNotificationService, ATTR_TARGET
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import DATA_XPLORA

from pyxplora_api import pyxplora_api_async as PXA

_LOGGER = logging.getLogger(__name__)


async def async_get_service(
    hass: HomeAssistant,
    config: ConfigType,
    discovery_info: DiscoveryInfoType | None = None,
) -> XploraNotificationService:
    _LOGGER.debug("set Notify Controller")
    controller: PXA.PyXploraApi = hass.data[DATA_XPLORA][0]
    _LOGGER.debug("set Service Notify")
    sv = XploraNotificationService()
    sv.setup(controller)

    return sv


class XploraNotificationService(BaseNotificationService):

    def __init__(self) -> None:
        _LOGGER.debug("init Notify Service")

    def setup(self, controller: PXA.PyXploraApi) -> None:
        _LOGGER.debug("init Setup")
        self._controller = controller

    async def async_send_message(self, message: str = "", **kwargs: Any) -> None:
        msg = message.strip()
        target = kwargs[ATTR_TARGET]
        _LOGGER.debug(f"sent message {msg} to {target}")
        if not target:
            _LOGGER.warning("No child phonenumber!")
        if len(msg):
            ids = await self._controller.getWatchUserID_async(kwargs[ATTR_TARGET])
            if not ids:
                _LOGGER.warning("Dont find child phonenumber!")
                return
            for id in ids:
                _LOGGER.debug(await self._controller.sendText(msg, id))
        else:
            _LOGGER.warning("Your message is empty!")
