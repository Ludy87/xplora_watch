"""Support for Xplora® Watch Version 2."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ENTITY_ID, CONF_NAME, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import aiohttp_client, discovery
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.typing import ConfigType

from .const import DATA_HASS_CONFIG, DOMAIN
from .coordinator import XploraDataUpdateCoordinator
from .helper import create_service_yaml_file, create_www_directory, move_emojis_directory
from .services import async_setup_services, async_unload_services

PLATFORMS = [Platform.BINARY_SENSOR, Platform.DEVICE_TRACKER, Platform.NOTIFY, Platform.SENSOR, Platform.SWITCH]

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, hass_config: ConfigType) -> bool:
    """Set up the Xplora® Watch Version 2 component."""
    _LOGGER.debug("Set up the Xplora® Watch Version 2 component")
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][DATA_HASS_CONFIG] = hass_config
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configure based on config entry."""
    _LOGGER.debug("Configure based on config entry %s", entry.entry_id)

    # Create and initialize a session for the entity process.
    coordinator: XploraDataUpdateCoordinator = XploraDataUpdateCoordinator(hass, entry)
    session = aiohttp_client.async_get_clientsession(hass)

    await coordinator.init(session=session)
    _LOGGER.debug("pyxplora_api lib version: %s", coordinator.controller.version())

    await _async_migrate_entries(hass, entry, coordinator.user_id)

    await coordinator.async_config_entry_first_refresh()
    wuids = coordinator.controller.getWatchUserIDs()
    username = coordinator.username

    for wuid in wuids:
        if not await coordinator.controller.isAdmin(wuid):
            watch_name = coordinator.controller.getWatchUserNames(wuid)
            _LOGGER.info("%s is not an admin for the watch from %s (%s)!", username, watch_name, wuid)

    hass.data.setdefault(DOMAIN, {})

    hass.data[DOMAIN][entry.entry_id] = coordinator
    await async_setup_services(hass, entry.entry_id)
    watches = await coordinator.controller.setDevices()

    await create_www_directory(hass)
    move_emojis_directory(hass)
    await create_service_yaml_file(hass, entry, watches)

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
    _LOGGER.debug("Unload a config entry")
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


async def _async_migrate_entries(hass: HomeAssistant, config_entry: ConfigEntry, new_uid: str) -> bool:
    """Migrate old entry."""
    entity_registry = er.async_get(hass)

    @callback
    def update_unique_id(entry: er.RegistryEntry) -> dict[str, str] | None:
        if (
            new_uid in str(entry.unique_id)
            and "_" in str(entry.unique_id)
            and "-" not in str(entry.unique_id)
            and " " not in str(entry.unique_id)
        ):
            return None
        elif new_uid in str(entry.unique_id) and "-" in str(entry.unique_id):
            new_unique_id = f"{entry.unique_id}".replace("-", "_").replace(" ", "_").lower()
        else:
            # "{ward.get(CONF_NAME)}-{ATTR_WATCH}-{description.key}-{wuid}"                            old
            # "{ward.get(CONF_NAME)}_{ATTR_WATCH}_{description.key}_{wuid}_{self.coordinator.user_id}" new
            new_unique_id = f"{entry.unique_id}_{new_uid}".replace("-", "_").replace(" ", "_").lower()

        _LOGGER.debug(
            "change unique_id - entity: '%s' unique_id from '%s' to '%s'", entry.entity_id, entry.unique_id, new_unique_id
        )
        if existing_entity_id := entity_registry.async_get_entity_id(entry.domain, entry.platform, new_unique_id):
            _LOGGER.debug("Cannot change unique_id to '%s', already exists for '%s'", new_unique_id, existing_entity_id)
            return None
        return {"new_unique_id": new_unique_id}

    await er.async_migrate_entries(hass, config_entry.entry_id, update_unique_id)

    return True
