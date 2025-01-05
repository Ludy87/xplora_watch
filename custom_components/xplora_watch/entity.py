"""Entity for Xplora® Watch Version 2 tracking."""

from __future__ import annotations

from collections.abc import Callable
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DEVICE_NAME, DOMAIN, MANUFACTURER, TRACKER_UPDATE_STR
from .coordinator import XploraDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class XploraBaseEntity(CoordinatorEntity[XploraDataUpdateCoordinator], RestoreEntity):
    """Common base for Xplora® entities."""

    _attr_attribution = ATTRIBUTION
    _attr_force_update = False
    _state = None

    def __init__(
        self,
        config_entry: ConfigEntry,
        description: EntityDescription | None,
        coordinator: XploraDataUpdateCoordinator,
        wuid: str,
    ) -> None:
        """Initialize entity."""
        super().__init__(coordinator)
        if description is not None:
            self.entity_description = description
        self._config_entry = config_entry
        self._data = config_entry.data
        self._options = config_entry.options

        self.watch_uid = wuid
        self._unsub_dispatchers: list[Callable[[], None]] = []

        self.is_admin = " (Admin)-" if coordinator.is_admin.get(coordinator.user_id + config_entry.entry_id, None) else "-"

        self.watch_name = self.coordinator.controller.getWatchUserNames(wuid=self.watch_uid)

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{self._config_entry.unique_id}_{self.watch_uid}")},
            manufacturer=MANUFACTURER,
            model=coordinator.data[self.watch_uid].get("model", DEVICE_NAME),
            name=f"{coordinator.username}{self.is_admin}{self.watch_name} ({self.watch_uid})",
            sw_version=coordinator.os_version,
            configuration_url="https://github.com/Ludy87/xplora_watch/blob/main/README.md",
        )

    def _states(self, status) -> bool:
        if status == "DISABLE":
            return False
        return True

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()

        # Restore state if available
        if state := await self.async_get_last_state():
            self._state = state.state
        self._unsub_dispatchers.append(async_dispatcher_connect(self.hass, TRACKER_UPDATE_STR, self._async_receive_data))

    async def async_will_remove_from_hass(self) -> None:
        """Clean up after entity before removal."""
        await super().async_will_remove_from_hass()
        for unsub in self._unsub_dispatchers:
            unsub()
        _LOGGER.debug("When entity is removed from hass")
        self._unsub_dispatchers = []

    @callback
    def _async_receive_data(self, device, location, location_name) -> None:
        """Update device data."""
        _LOGGER.debug("Update device data.\n%s\n%s", device, self._name)
        if device != self._name:
            return
        self._location_name = location_name
        self._location = location
        self.async_write_ha_state()
