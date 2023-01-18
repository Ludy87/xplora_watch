"""Entity for Xplora® Watch Version 2 tracking."""
from __future__ import annotations

import logging
from collections.abc import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo, EntityDescription
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DEVICE_NAME, DOMAIN, MANUFACTURER, TRACKER_UPDATE_STR
from .coordinator import XploraDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class XploraBaseEntity(CoordinatorEntity[XploraDataUpdateCoordinator], RestoreEntity):
    """Common base for Xplora® entities."""

    _attr_attribution = ATTRIBUTION
    _attr_force_update = False

    def __init__(
        self,
        config_entry: ConfigEntry,
        description: EntityDescription,
        coordinator: XploraDataUpdateCoordinator,
        ward: dict[str, any],
        sw_version: dict[str, any],
        wuid: str,
    ) -> None:
        """Initialize entity."""
        super().__init__(coordinator)
        if description is not None:
            self.entity_description = description
        self._data = config_entry.data
        self._options = config_entry.options

        self._ward: dict[str, any] = ward
        self.sw_version: dict[str, any] = sw_version
        self.watch_uid = wuid
        self._unsub_dispatchers: list[Callable[[], None]] = []

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, wuid)},
            manufacturer=MANUFACTURER,
            model=self.coordinator.data[wuid]["model"],
            name=f"{DEVICE_NAME} {wuid}",
            sw_version=self.sw_version.get("osVersion", "n/a"),
            via_device=(DOMAIN, wuid),
        )

    def _states(self, status) -> bool:
        if status == "DISABLE":
            return False
        return True

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        if state := await self.async_get_last_state():
            self._state = state.state
        self._unsub_dispatchers.append(async_dispatcher_connect(self.hass, TRACKER_UPDATE_STR, self._async_receive_data))

    async def async_will_remove_from_hass(self) -> None:
        """Clean up after entity before removal."""
        await super().async_will_remove_from_hass()
        for unsub in self._unsub_dispatchers:
            unsub()
        _LOGGER.debug("When entity is remove on hass.")
        self._unsub_dispatchers = []

    @callback
    def _async_receive_data(self, device, location, location_name) -> None:
        """Update device data."""
        _LOGGER.debug("Update device data.\n%s\n%s" % device, self._name)
        if device != self._name:
            return
        self._location_name = location_name
        self._location = location
        self.async_write_ha_state()
