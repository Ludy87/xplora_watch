"""Support for Xplora® Watch Version 2 tracking."""
from __future__ import annotations

from typing import Any


from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ID, ATTR_LATITUDE, ATTR_LONGITUDE, CONF_NAME, STATE_HOME, STATE_NOT_HOME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

import logging

from .coordinator import XploraDataUpdateCoordinator
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
    CONF_HOME_LATITUDE,
    CONF_HOME_LONGITUDE,
    CONF_HOME_RADIUS,
    CONF_TYPES,
    CONF_WATCHES,
    DEVICE_TRACKER_SAFZONES,
    DEVICE_TRACKER_WATCH,
    DOMAIN,
    HOME,
)
from .entity import XploraBaseEntity
from .helper import get_location_distance, get_location_distance_meter

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Xplora® Watch Version 2 tracker from config entry."""
    coordinator: XploraDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities: list[XploraDeviceTracker] = []

    for watch in coordinator.controller.watchs:
        if config_entry.options:
            ward: dict[str, Any] = watch.get("ward")
            uid = ward.get(ATTR_ID)
            if uid in config_entry.options.get(CONF_WATCHES):
                sw_version = await coordinator.controller.getWatches(uid)
                if DEVICE_TRACKER_SAFZONES in config_entry.options.get(CONF_TYPES):
                    safeZones = await coordinator.controller.getWatchSafeZones(uid)
                    for safeZone in safeZones:
                        entities.append(XploraSafezoneTracker(hass, safeZone, coordinator, ward, sw_version, uid))
                if DEVICE_TRACKER_WATCH in config_entry.options.get(CONF_TYPES):
                    entities.append(
                        XploraDeviceTracker(
                            hass,
                            coordinator=coordinator,
                            uid=uid,
                            ward=ward,
                            sw_version=sw_version,
                            config_entry=config_entry,
                        )
                    )
        else:
            _LOGGER.debug(f"{watch} {config_entry.entry_id}")
    async_add_entities(entities)


class XploraSafezoneTracker(XploraBaseEntity, TrackerEntity, RestoreEntity):

    _attr_force_update: bool = False
    _attr_icon: str | None = "mdi:crosshairs-gps"

    def __init__(
        self,
        hass: HomeAssistant,
        safezone: dict[str, Any],
        coordinator: XploraDataUpdateCoordinator,
        ward: dict[str, Any],
        sw_version: dict[str, Any],
        uid: str,
    ) -> None:
        super().__init__(coordinator, ward, sw_version, uid)
        self._safezone = safezone
        self._hass = hass
        self._attr_name = f"Safezone {safezone[CONF_NAME]} {self.watch_uid}"
        self._attr_unique_id = f'safezone_{safezone["vendorId"]}'

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        return self._safezone[ATTR_TRACKER_LAT]

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        return self._safezone[ATTR_TRACKER_LNG]

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
    def extra_state_attributes(self) -> dict[str, Any]:
        data = super().extra_state_attributes or {}
        return dict(
            data,
            **{ATTR_TRACKER_ADDR: self._safezone[ATTR_TRACKER_ADDR]},
        )


class XploraDeviceTracker(XploraBaseEntity, TrackerEntity, RestoreEntity):
    """Xplora® Watch Version 2 device tracker."""

    _attr_force_update: bool = False
    _attr_icon: str | None = "mdi:watch"

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: XploraDataUpdateCoordinator,
        uid: str,
        ward: dict[str, Any],
        sw_version: dict[str, Any],
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the Tracker."""
        super().__init__(coordinator, ward, sw_version=sw_version, uid=uid)
        self._hass = hass
        self._attr_name = f"{self._ward.get(CONF_NAME)} Watch Tracker {self.watch_uid}"
        self._attr_unique_id = uid
        self._config_entry = config_entry

    @property
    def battery_level(self) -> int | None:
        """Return battery value of the device."""
        return self._coordinator.watch_entry[self.watch_uid]["battery"]

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        return self._coordinator.watch_entry[self.watch_uid][ATTR_TRACKER_LAT]

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        return self._coordinator.watch_entry[self.watch_uid][ATTR_TRACKER_LNG]

    @property
    def source_type(self) -> SourceType | str:
        """Return the source type, eg gps or router, of the device."""
        return self._coordinator.watch_entry[self.watch_uid]["locateType"]

    @property
    def location_accuracy(self) -> int:
        """Return the gps accuracy of the device."""
        return self._coordinator.watch_entry[self.watch_uid]["location_accuracy"]

    @property
    def location_name(self) -> str | None:
        """Return a location name for the current location of the device."""
        return self._coordinator.watch_entry[self.watch_uid]["location_name"]

    @property
    def entity_picture(self) -> str:
        """Return the entity picture to use in the frontend, if any."""
        return self._coordinator.watch_entry[self.watch_uid]["entity_picture"]

    @property
    def state(self) -> str | None:
        """Return the state of the device."""
        _options = self._config_entry.options
        latitude = self._coordinator.watch_entry[self.watch_uid][ATTR_TRACKER_LAT]
        longitude = self._coordinator.watch_entry[self.watch_uid][ATTR_TRACKER_LNG]
        home_raduis = self.hass.states.get(HOME).attributes["radius"]
        if self.latitude is not None and self.longitude is not None:
            zone_state = get_location_distance(
                (
                    _options.get(CONF_HOME_LATITUDE, self.hass.states.get(HOME).attributes[ATTR_LATITUDE]),
                    _options.get(CONF_HOME_LONGITUDE, self.hass.states.get(HOME).attributes[ATTR_LONGITUDE]),
                ),
                (latitude, longitude),
                _options.get(CONF_HOME_RADIUS, home_raduis),
            )
            if zone_state is False:
                state = STATE_NOT_HOME
            else:
                state = STATE_HOME
            return state

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = super().extra_state_attributes or {}
        lat_lng: tuple[float, float] = (
            float(self._coordinator.watch_entry[self.watch_uid][ATTR_TRACKER_LAT]),
            float(self._coordinator.watch_entry[self.watch_uid][ATTR_TRACKER_LNG]),
        )
        distanceToHome = get_location_distance_meter(self._hass, lat_lng)
        return dict(
            data,
            **{
                ATTR_TRACKER_DISTOHOME: distanceToHome,
                ATTR_TRACKER_ADDR: self._coordinator.watch_entry[self.watch_uid]["location_name"],
                ATTR_TRACKER_LAST_TRACK: self._coordinator.watch_entry[self.watch_uid]["lastTrackTime"],
                ATTR_TRACKER_IMEI: self._coordinator.watch_entry[self.watch_uid][ATTR_TRACKER_IMEI],
                ATTR_TRACKER_POI: self._coordinator.watch_entry[self.watch_uid][ATTR_TRACKER_POI],
                ATTR_TRACKER_LICENCE: self._coordinator.watch_entry[self.watch_uid][ATTR_TRACKER_LICENCE],
            },
        )
