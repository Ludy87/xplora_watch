"""Reads watch status from Xplora® Watch Version 2."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity, BinarySensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ID, ATTR_LATITUDE, ATTR_LONGITUDE, CONF_NAME, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_TRACKER_LAT,
    ATTR_TRACKER_LNG,
    ATTR_WATCH,
    BINARY_SENSOR_CHARGING,
    BINARY_SENSOR_SAFEZONE,
    BINARY_SENSOR_STATE,
    CONF_HOME_LATITUDE,
    CONF_HOME_LONGITUDE,
    CONF_HOME_RADIUS,
    CONF_HOME_SAFEZONE,
    CONF_TYPES,
    CONF_WATCHES,
    DOMAIN,
    HOME,
)
from .coordinator import XploraDataUpdateCoordinator
from .entity import XploraBaseEntity
from .helper import get_location_distance

_LOGGER = logging.getLogger(__name__)

BINARY_SENSOR_TYPES: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(key=BINARY_SENSOR_CHARGING, device_class=BinarySensorDeviceClass.BATTERY_CHARGING),
    BinarySensorEntityDescription(key=BINARY_SENSOR_SAFEZONE, device_class=BinarySensorDeviceClass.SAFETY),
    BinarySensorEntityDescription(key=BINARY_SENSOR_STATE, device_class=BinarySensorDeviceClass.CONNECTIVITY),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Xplora® Watch Version 2 binary sensors from config entry."""
    coordinator: XploraDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities: list[XploraBinarySensor] = []
    for description in BINARY_SENSOR_TYPES:
        for watch in coordinator.controller.watchs:
            if config_entry.options:
                ward: dict[str, Any] = watch.get("ward")
                wuid = ward.get(ATTR_ID, "")
                if wuid in config_entry.options.get(CONF_WATCHES, []):
                    if description.key in config_entry.options.get(CONF_TYPES, []):
                        sw_version = await coordinator.controller.getWatches(wuid)
                        entities.append(XploraBinarySensor(config_entry, coordinator, ward, sw_version, wuid, description))
            else:
                _LOGGER.debug(f"{watch} {config_entry.entry_id}")
    async_add_entities(entities)


class XploraBinarySensor(XploraBaseEntity, BinarySensorEntity):

    _attr_force_update = False

    def __init__(
        self,
        config_entry: ConfigEntry,
        coordinator: XploraDataUpdateCoordinator,
        ward: dict[str, Any],
        sw_version: dict[str, Any],
        wuid: str,
        description: BinarySensorEntityDescription,
    ) -> None:
        super().__init__(config_entry, description, coordinator, ward, sw_version, wuid)
        _wuid: str = ""
        for i in range(1, len(config_entry.options.get(CONF_WATCHES, [])) + 1):
            _wuid = config_entry.options.get(f"{CONF_WATCHES}_{i}", "")
            if _wuid.find("=") != -1:
                friendly_name = _wuid.split("=")
                if friendly_name[0] == wuid:
                    self._attr_name: str = f"{friendly_name[1]} {description.key}".title()
                else:
                    self._attr_name: str = f"{ward.get(CONF_NAME)} {ATTR_WATCH} {description.key} {wuid}".title()
            else:
                self._attr_name: str = f"{ward.get(CONF_NAME)} {ATTR_WATCH} {description.key} {wuid}".title()

        self._attr_unique_id = f"{ward.get(CONF_NAME)}-{ATTR_WATCH}-{description.key}-{wuid}"
        self._config_entry = config_entry
        _LOGGER.debug(
            "Updating binary_sensor: %s | %s | Watch_ID %s",
            self._attr_name[:-33] if _wuid.find("=") == -1 else self._attr_name,
            description.key,
            wuid[25:],
        )

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        if self.entity_description.key == BINARY_SENSOR_CHARGING:
            return self._coordinator.data[self.watch_uid]["isCharging"]
        if self.entity_description.key == BINARY_SENSOR_STATE:
            return self._coordinator.data[self.watch_uid]["isOnline"]
        if self.entity_description.key == BINARY_SENSOR_SAFEZONE:
            _options = self._config_entry.options
            if _options.get(CONF_HOME_SAFEZONE, STATE_OFF) == STATE_ON:
                latitude = self._coordinator.data[self.watch_uid][ATTR_TRACKER_LAT]
                longitude = self._coordinator.data[self.watch_uid][ATTR_TRACKER_LNG]
                home_latitude = self.hass.states.get(HOME).attributes[ATTR_LATITUDE]
                home_longitude = self.hass.states.get(HOME).attributes[ATTR_LONGITUDE]
                home_raduis = self.hass.states.get(HOME).attributes["radius"]
                if get_location_distance(
                    (
                        _options.get(CONF_HOME_LATITUDE, home_latitude),
                        _options.get(CONF_HOME_LONGITUDE, home_longitude),
                    ),
                    (latitude, longitude),
                    _options.get(CONF_HOME_RADIUS, home_raduis),
                ):
                    return False
            return self._coordinator.data[self.watch_uid]["isSafezone"]
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = super().extra_state_attributes or {}
        return dict(data, **{})
