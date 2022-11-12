"""Support for Xplora® Watch Version 2 tracking."""
from __future__ import annotations

import logging

from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ID, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    ATTR_TRACKER_ADDR,
    ATTR_TRACKER_DISTOHOME,
    ATTR_TRACKER_IMEI,
    ATTR_TRACKER_LAST_TRACK,
    ATTR_TRACKER_LAT,
    ATTR_TRACKER_LICENCE,
    ATTR_TRACKER_LNG,
    ATTR_TRACKER_POI,
    ATTR_TRACKER_RAD,
    CONF_TYPES,
    CONF_WATCHES,
    DEVICE_TRACKER_SAFZONES,
    DEVICE_TRACKER_WATCH,
    DOMAIN,
)
from .coordinator import XploraDataUpdateCoordinator
from .entity import XploraBaseEntity
from .helper import get_location_distance_meter

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the Xplora® Watch Version 2 tracker from config entry."""
    coordinator: XploraDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities: list[XploraDeviceTracker] = []

    for watch in coordinator.controller.watchs:
        if config_entry.options:
            ward: dict[str, any] = watch.get("ward")
            wuid = ward.get(ATTR_ID)
            if wuid in config_entry.options.get(CONF_WATCHES):
                sw_version = await coordinator.controller.getWatches(wuid)
                if DEVICE_TRACKER_SAFZONES in config_entry.options.get(CONF_TYPES):
                    safeZones = await coordinator.controller.getWatchSafeZones(wuid)
                    for safeZone in safeZones:
                        entities.append(
                            XploraSafezoneTracker(hass, config_entry, safeZone, coordinator, ward, sw_version, wuid)
                        )
                if DEVICE_TRACKER_WATCH in config_entry.options.get(CONF_TYPES):
                    entities.append(XploraDeviceTracker(hass, config_entry, coordinator, wuid, ward, sw_version))
        else:
            _LOGGER.debug(f"{watch} {config_entry.entry_id}")
    async_add_entities(entities)


class XploraSafezoneTracker(XploraBaseEntity, TrackerEntity, RestoreEntity):

    _attr_force_update: bool = False
    _attr_icon: str | None = "mdi:crosshairs-gps"

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        safezone: dict[str, any],
        coordinator: XploraDataUpdateCoordinator,
        ward: dict[str, any],
        sw_version: dict[str, any],
        wuid: str,
    ) -> None:
        super().__init__(config_entry, None, coordinator, ward, sw_version, wuid)
        self._safezone = safezone
        self._hass = hass

        for i in range(1, len(config_entry.options.get(CONF_WATCHES)) + 1):
            _wuid: str = config_entry.options.get(f"{CONF_WATCHES}_{i}")
            if _wuid.find("=") != -1:
                friendly_name = _wuid.split("=")
                if friendly_name[0] == wuid:
                    self._attr_name = f"{friendly_name[1]} Safezone {safezone[CONF_NAME]}"
                else:
                    self._attr_name = f"Safezone {safezone[CONF_NAME]} {wuid}"
            else:
                self._attr_name = f"Safezone {safezone[CONF_NAME]} {wuid}"

        self._attr_unique_id = f'safezone_{safezone["vendorId"]}'

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        return float(self._safezone[ATTR_TRACKER_LAT])

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        return float(self._safezone[ATTR_TRACKER_LNG])

    @property
    def source_type(self) -> SourceType | str:
        """Return the source type, eg gps or router, of the device."""
        return SourceType.GPS

    @property
    def location_accuracy(self) -> int:
        """Return the gps accuracy of the device."""
        return self._safezone[ATTR_TRACKER_RAD]

    @property
    def location_name(self) -> str | None:
        """Return a location name for the current location of the device."""
        return self._safezone[CONF_NAME]

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        data = super().extra_state_attributes or {}
        return dict(
            data,
            **{ATTR_TRACKER_ADDR: self._safezone[ATTR_TRACKER_ADDR]},
        )


class XploraDeviceTracker(XploraBaseEntity, TrackerEntity):
    """Xplora® Watch Version 2 device tracker."""

    _attr_force_update: bool = False
    _attr_icon: str | None = "mdi:watch"

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        coordinator: XploraDataUpdateCoordinator,
        wuid: str,
        ward: dict[str, any],
        sw_version: dict[str, any],
    ) -> None:
        """Initialize the Tracker."""
        super().__init__(config_entry, None, coordinator, ward, sw_version, wuid)
        self._hass = hass

        for i in range(1, len(config_entry.options.get(CONF_WATCHES)) + 1):
            _wuid: str = config_entry.options.get(f"{CONF_WATCHES}_{i}")
            if _wuid.find("=") != -1:
                friendly_name = _wuid.split("=")
                if friendly_name[0] == wuid:
                    self._attr_name = f"{friendly_name[1]} Watch Tracker"
                else:
                    self._attr_name = f"{self._ward.get(CONF_NAME)} Watch Tracker {wuid}"
            else:
                self._attr_name = f"{self._ward.get(CONF_NAME)} Watch Tracker {wuid}"

        self._attr_unique_id = wuid
        self._config_entry = config_entry

    @property
    def battery_level(self) -> int | None:
        """Return battery value of the device."""
        return self._coordinator.data[self.watch_uid]["battery"]

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        return self._coordinator.data[self.watch_uid][ATTR_TRACKER_LAT]

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        return self._coordinator.data[self.watch_uid][ATTR_TRACKER_LNG]

    @property
    def source_type(self) -> SourceType | str:
        """Return the source type, eg gps or router, of the device."""
        return SourceType.GPS

    @property
    def location_accuracy(self) -> int:
        """Return the gps accuracy of the device."""
        return self._coordinator.data[self.watch_uid]["location_accuracy"]

    @property
    def address(self) -> str | None:
        """Return a location name for the current location of the device."""
        return self._coordinator.data[self.watch_uid]["location_name"]

    @property
    def entity_picture(self) -> str:
        """Return the entity picture to use in the frontend, if any."""
        return self._coordinator.data[self.watch_uid]["entity_picture"]

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        data = super().extra_state_attributes or {}
        distanceToHome = None
        if (
            self._coordinator.data[self.watch_uid][ATTR_TRACKER_LAT] is not None
            and self._coordinator.data[self.watch_uid][ATTR_TRACKER_LNG] is not None
        ):
            lat_lng: tuple[float, float] = (
                float(self._coordinator.data[self.watch_uid][ATTR_TRACKER_LAT]),
                float(self._coordinator.data[self.watch_uid][ATTR_TRACKER_LNG]),
            )
            distanceToHome = get_location_distance_meter(self._hass, lat_lng)
        return dict(
            data,
            **{
                ATTR_TRACKER_DISTOHOME: distanceToHome,
                ATTR_TRACKER_ADDR: self.address if distanceToHome else None,
                ATTR_TRACKER_LAST_TRACK: self._coordinator.data[self.watch_uid]["lastTrackTime"] if distanceToHome else None,
                ATTR_TRACKER_IMEI: self._coordinator.data[self.watch_uid][ATTR_TRACKER_IMEI],
                ATTR_TRACKER_POI: self._coordinator.data[self.watch_uid][ATTR_TRACKER_POI],
                ATTR_TRACKER_LICENCE: self._coordinator.data[self.watch_uid][ATTR_TRACKER_LICENCE],
            },
        )
