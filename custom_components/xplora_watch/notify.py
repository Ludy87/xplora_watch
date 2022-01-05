"""Support for Xplora® Watch notifications."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.notify import BaseNotificationService
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import DATA_XPLORA

from pyxplora_api import pyxplora_api as PXA

_LOGGER = logging.getLogger(__name__)

def get_service(
    hass: HomeAssistant,
    config: ConfigType,
    discovery_info: DiscoveryInfoType | None = None,
) -> XploraNotificationService:
    _LOGGER.debug("set Notify Controller")
    controller = hass.data[DATA_XPLORA][0]

    _LOGGER.debug("set Service")
    sv = XploraNotificationService()
    sv.setup(controller)

    return sv

class XploraNotificationService(BaseNotificationService):

    def __init__(self) -> None:
        _LOGGER.debug("init Notify Service")

    def setup(self, controller: PXA.PyXploraApi) -> None:
        _LOGGER.debug("init Setup")
        self._controller = controller

    def send_message(self, message: str = "", **kwargs: Any) -> None:
        _LOGGER.debug("sent message {message}")
        self._controller.sendText(message)
