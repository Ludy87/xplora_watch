"""Send Message to watch from Xplora® Watch Version 2."""
from __future__ import annotations

import logging

from homeassistant.components.notify import BaseNotificationService
from homeassistant.components.notify.const import ATTR_DATA, ATTR_TARGET
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import DOMAIN
from .coordinator import XploraDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_get_service(
    hass: HomeAssistant, config: ConfigType, discovery_info: DiscoveryInfoType | None = None
) -> XploraNotifyService:
    """Set up notification service."""
    return XploraNotifyService(hass)


class XploraNotifyService(BaseNotificationService):
    """Implement the notification service for Xplora® Watch."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Init Notify Service."""
        _LOGGER.debug("init Notify Service")
        self._hass = hass

    async def async_send_message(self, message="", **kwargs) -> None:
        """Send message to user."""
        targets = kwargs.get(ATTR_TARGET, {})
        if not targets:
            _LOGGER.warning("No watch id!")
            return None
        data = kwargs.get(ATTR_DATA, {})
        if not data:
            _LOGGER.warning("No data!")
            return None
        user_id = data.get("No user_id")
        coordinator: XploraDataUpdateCoordinator = self._hass.data[DOMAIN][user_id]
        controller = coordinator.controller
        msg = message.strip()
        if not msg:
            _LOGGER.warning("Message is empty!")
            return None
        for watch_id in targets:
            if not await controller.sendText(text=msg, wuid=watch_id):
                _LOGGER.error("Failed to send message '%s' to %s", msg, watch_id)
