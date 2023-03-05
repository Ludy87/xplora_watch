"""Support for Xplora® Watch Version 2"""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ENTITY_ID, CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery
from homeassistant.helpers.typing import ConfigType

from .const import DATA_HASS_CONFIG, DOMAIN
from .coordinator import XploraDataUpdateCoordinator
from .helper import create_service_yaml_file, create_www_directory, move_file
from .services import async_setup_services, async_unload_services

PLATFORMS = [Platform.BINARY_SENSOR, Platform.DEVICE_TRACKER, Platform.NOTIFY, Platform.SENSOR, Platform.SWITCH]

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
    wuids = coordinator.controller.getWatchUserIDs()
    for wuid in wuids:
        if not await coordinator.controller.isAdmin(wuid):
            _LOGGER.warning(f"You are no admin for Watch {wuid}!")

    hass.data.setdefault(DOMAIN, {})

    await async_setup_services(hass, coordinator)

    hass.data[DOMAIN][entry.entry_id] = coordinator
    watches = await coordinator.controller.setDevices()

    await create_www_directory(hass)
    move_file(hass)
    create_service_yaml_file(hass, entry, watches)

    for platform in PLATFORMS:
        if platform != Platform.NOTIFY:
            hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, platform))

    hass.async_create_task(
        discovery.async_load_platform(
            hass,
            Platform.NOTIFY,
            DOMAIN,
            {CONF_NAME: DOMAIN, CONF_ENTITY_ID: entry.entry_id},
            hass.data[DOMAIN][DATA_HASS_CONFIG],
        )
    )

    entry.async_on_unload(entry.add_update_listener(options_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unload a config entry.")
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, [platform for platform in PLATFORMS if platform != Platform.NOTIFY]
    )
    async_unload_services(hass)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def options_update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.debug("Configuration options updated, reloading Xplora® Watch Version 2 integration")
    await hass.config_entries.async_reload(config_entry.entry_id)
