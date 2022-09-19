from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, callback

import homeassistant.helpers.config_validation as cv

from .const import DOMAIN
from .coordinator import XploraDataUpdateCoordinator

ATTR_MSG = "message"
ATTR_TARGET = "target"


BASE_SERVICE_SCHEMA = vol.Schema(
    {vol.Required(ATTR_TARGET): vol.All(cv.ensure_list, [cv.string]), vol.Required(ATTR_MSG): cv.string},
    extra=vol.ALLOW_EXTRA,
)

_LOGGER = logging.getLogger(__name__)


@callback
def async_setup_services(hass: HomeAssistant, coordinator: XploraDataUpdateCoordinator) -> None:
    """Set up services for UniFi integration."""

    notify_service = XploraNotificationService(hass, coordinator)

    async def async_send_xplora_message(service: ServiceCall) -> None:
        kwargs = dict(service.data)
        _LOGGER.debug(kwargs)
        await notify_service.async_send_message(kwargs[ATTR_MSG], kwargs[ATTR_TARGET])

    hass.services.async_register(DOMAIN, "send_message", async_send_xplora_message, schema=BASE_SERVICE_SCHEMA)


@callback
def async_unload_services(hass: HomeAssistant) -> None:
    """Unload UniFi Network services."""
    hass.services.async_remove(DOMAIN, "send_message")


class XploraNotificationService:
    def __init__(self, hass: HomeAssistant, coordinator: XploraDataUpdateCoordinator) -> None:
        self._hass = hass
        self._controller = coordinator.controller

    async def async_send_message(self, message="", target=None, **kwargs):
        """Send a message to one or multiple pre-allowed chat IDs."""
        msg = message.strip()
        _LOGGER.debug(f"sent message '{msg}' to {target}")
        if not target:
            _LOGGER.warning("No waatch id!")
        if len(msg) > 0:
            for watch_id in target:
                if not await self._controller.sendText(text=msg, wuid=watch_id):
                    _LOGGER.error("Message cannot send!")
        else:
            _LOGGER.warning("Your message is empty!")
