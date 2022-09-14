"""Support for Xplora® Watch Version 2"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_flow
from homeassistant.helpers.typing import ConfigType

import logging

from .const import (
    DATA_HASS_CONFIG,
    DOMAIN,
)
from .coordinator import XploraDataUpdateCoordinator

PLATFORMS = [
    Platform.DEVICE_TRACKER,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.SWITCH,
]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, hass_config: ConfigType) -> bool:
    """Set up the Xplora® Watch Version 2 component."""
    _LOGGER.debug("Set up the Xplora® Watch Version 2 component.")
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][DATA_HASS_CONFIG] = hass_config
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configure based on config entry."""
    _LOGGER.debug("Configure based on config entry.")
    coordinator = XploraDataUpdateCoordinator(hass, entry)
    await coordinator.init()
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    for platform in PLATFORMS:
        hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, platform))

    entry.async_on_unload(entry.add_update_listener(options_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unload a config entry.")
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def options_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle options update."""
    _LOGGER.debug("Configuration options updated, reloading Xplora® Watch Version 2 integration")
    await hass.config_entries.async_reload(config_entry.entry_id)


async_remove_entry = config_entry_flow.webhook_async_remove_entry
