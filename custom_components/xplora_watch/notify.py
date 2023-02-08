"""Send Message to watch from Xplora® Watch Version 2."""
from __future__ import annotations

import logging

from homeassistant.components.notify import ATTR_TARGET, BaseNotificationService
from homeassistant.const import CONF_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import DOMAIN
from .coordinator import XploraDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


def get_service(
    hass: HomeAssistant, config: ConfigType, discovery_info: DiscoveryInfoType | None = None
) -> BaseNotificationService:
    """Set up notification service."""
    coordinator: XploraDataUpdateCoordinator = hass.data[DOMAIN][(discovery_info or {})[CONF_ENTITY_ID]]
    return XploraNotifyService(hass, coordinator)


class XploraNotifyService(BaseNotificationService):
    def __init__(self, hass: HomeAssistant, coordinator: XploraDataUpdateCoordinator) -> None:
        _LOGGER.debug("init Notify Service")
        self._controller = coordinator.controller

    async def async_send_message(self, message="", **kwargs):
        """Send message to user."""
        targets = kwargs.get(ATTR_TARGET, None)
        if not targets:
            _LOGGER.warning("No watch id!")
            return
        msg = message.strip()
        if not msg:
            _LOGGER.warning("Message is empty!")
            return
        for watch_id in targets:
            if not await self._controller.sendText(text=msg, wuid=watch_id):
                _LOGGER.error(f"Failed to send message '{msg}' to {watch_id}")
