"""Send Message to watch from Xplora® Watch Version 2."""
from __future__ import annotations

from homeassistant.components.notify import BaseNotificationService, ATTR_TARGET
from homeassistant.const import CONF_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import DOMAIN
from .coordinator import XploraDataUpdateCoordinator

import logging


_LOGGER = logging.getLogger(__name__)


def get_service(
    hass: HomeAssistant,
    config: ConfigType,
    discovery_info: DiscoveryInfoType | None = None,
) -> BaseNotificationService:
    """Set up notification service."""
    coordinator: XploraDataUpdateCoordinator = hass.data[DOMAIN][(discovery_info or {})[CONF_ENTITY_ID]]
    return XploraNotifyService(hass, coordinator)


class XploraNotifyService(BaseNotificationService):
    def __init__(self, hass: HomeAssistant, coordinator: XploraDataUpdateCoordinator) -> None:
        _LOGGER.debug("init Notify Service")
        self._controller = coordinator.controller

    async def async_send_message(self, message="", **kwargs):
        """Send a message to a user."""
        msg = message.strip()
        target = kwargs[ATTR_TARGET]
        _LOGGER.debug(f"sent message '{msg}' to {target}")
        if not target:
            _LOGGER.warning("No waatch id!")
        if len(msg) > 0:
            for watch_id in target:
                if await self._controller.sendText(text=msg, wuid=watch_id):
                    _LOGGER.error("Message cannot send!")
        else:
            _LOGGER.warning("Your message is empty!")
