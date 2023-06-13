"""Reads watch status from Xplora® Watch Version 2."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity, BinarySensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ID, ATTR_LATITUDE, ATTR_LONGITUDE, CONF_NAME, STATE_OFF, STATE_ON, EntityCategory
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
from .helper import is_distance_in_radius

_LOGGER = logging.getLogger(__name__)

BINARY_SENSOR_TYPES: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key=BINARY_SENSOR_CHARGING,
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BinarySensorEntityDescription(
        key=BINARY_SENSOR_SAFEZONE,
        device_class=BinarySensorDeviceClass.SAFETY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BinarySensorEntityDescription(
        key=BINARY_SENSOR_STATE,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
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
            options = config_entry.options
            if not options or not isinstance(watch, dict):
                _LOGGER.debug("%s %s", watch, config_entry.entry_id)
                continue

            ward: dict[str, any] = watch.get("ward", None)
            if ward is None:
                continue

            wuid = ward.get(ATTR_ID, None)
            if wuid is None:
                continue

            conf_watches = options.get(CONF_WATCHES, None)
            conf_tyes = options.get(CONF_TYPES, None)

            if conf_watches is None or conf_tyes is None or wuid not in conf_watches or description.key not in conf_tyes:
                continue

            sw_version = await coordinator.controller.getWatches(wuid)
            entities.append(XploraBinarySensor(config_entry, coordinator, ward, sw_version, wuid, description))

    async_add_entities(entities)


class XploraBinarySensor(XploraBaseEntity, BinarySensorEntity):
    def __init__(
        self,
        config_entry: ConfigEntry,
        coordinator: XploraDataUpdateCoordinator,
        ward: dict[str, any],
        sw_version: dict[str, any],
        wuid: str,
        description: BinarySensorEntityDescription,
    ) -> None:
        super().__init__(config_entry, description, coordinator, ward, sw_version, wuid)
        if self.watch_uid not in self.coordinator.data:
            return

        i = (self._options.get(CONF_WATCHES, []).index(wuid) + 1) if self._options.get(CONF_WATCHES, []) else -1
        if i == -1:
            return
        _wuid: str = self._options.get(f"{CONF_WATCHES}_{i}", "")
        if _wuid.find("=") != -1:
            friendly_name = _wuid.split("=")
            if friendly_name[0] == wuid:
                self._attr_name: str = f'{friendly_name[1]} {description.key.replace("_", " ")}'.title()
            else:
                self._attr_name: str = f'{ward.get(CONF_NAME)} {ATTR_WATCH} {description.key.replace("_", " ")} {wuid}'.title()
        else:
            self._attr_name: str = f'{ward.get(CONF_NAME)} {ATTR_WATCH} {description.key.replace("_", " ")} {wuid}'.title()

        self._attr_unique_id = f"{ward.get(CONF_NAME)}-{ATTR_WATCH}-{description.key}-{wuid}"
        _LOGGER.debug(
            "Updating binary_sensor: %s | Typ: %s | %s Watch_ID %s",
            self._attr_name[:-33] if _wuid.find("=") == -1 else self._attr_name,
            description.key,
            i,
            wuid[25:],
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self.entity_description.key == BINARY_SENSOR_CHARGING:
            return self.coordinator.data[self.watch_uid].get("isCharging", None)
        if self.entity_description.key == BINARY_SENSOR_STATE:
            return self.coordinator.data[self.watch_uid].get("isOnline", None)
        if self.entity_description.key == BINARY_SENSOR_SAFEZONE:
            if self._options.get(CONF_HOME_SAFEZONE, STATE_OFF) == STATE_ON:
                latitude = self.coordinator.data[self.watch_uid].get(ATTR_TRACKER_LAT, None)
                longitude = self.coordinator.data[self.watch_uid].get(ATTR_TRACKER_LNG, None)
                home_latitude = self.hass.states.get(HOME).attributes[ATTR_LATITUDE]
                home_longitude = self.hass.states.get(HOME).attributes[ATTR_LONGITUDE]
                home_raduis = self.hass.states.get(HOME).attributes["radius"]
                if is_distance_in_radius(
                    (
                        self._options.get(CONF_HOME_LATITUDE, home_latitude),
                        self._options.get(CONF_HOME_LONGITUDE, home_longitude),
                    ),
                    (latitude, longitude),
                    self._options.get(CONF_HOME_RADIUS, home_raduis),
                ):
                    return False
            return self.coordinator.data[self.watch_uid].get("isSafezone", None)
        return False

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend, if any."""
        if self.entity_description.key == BINARY_SENSOR_CHARGING and not self.coordinator.data[self.watch_uid].get(
            "isCharging", None
        ):
            return "mdi:battery-unknown"
        if hasattr(self, "_attr_icon"):
            return self._attr_icon
        if hasattr(self, "entity_description"):
            return self.entity_description.icon
        return None

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        data = super().extra_state_attributes or {}
        return dict(data, **{})
