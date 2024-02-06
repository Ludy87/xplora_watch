"""Reads watch status from Xplora® Watch Version 2."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ID, CONF_NAME, PERCENTAGE, EntityCategory, UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import (
    ATTR_TRACKER_LAT,
    ATTR_TRACKER_LNG,
    ATTR_WATCH,
    CONF_TYPES,
    CONF_WATCHES,
    DOMAIN,
    SENSOR_BATTERY,
    SENSOR_DISTANCE,
    SENSOR_MESSAGE,
    SENSOR_STEP_DAY,
    SENSOR_XCOIN,
)
from .coordinator import XploraDataUpdateCoordinator
from .entity import XploraBaseEntity
from .helper import get_location_distance_meter

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=SENSOR_BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_STEP_DAY,
        icon="mdi:run",
        native_unit_of_measurement="step",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_XCOIN,
        icon="mdi:hand-coin",
        native_unit_of_measurement="💰",
        device_class=SensorDeviceClass.MONETARY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_MESSAGE,
        icon="mdi:message",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=SENSOR_DISTANCE,
        native_unit_of_measurement=UnitOfLength.METERS,
        device_class=SensorDeviceClass.DISTANCE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the Xplora® Watch Version 2 sensors from config entry."""
    coordinator: XploraDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities: list[XploraSensor] = []
    for description in SENSOR_TYPES:
        for watch in coordinator.controller.watchs:
            options = config_entry.options
            if not options or not isinstance(watch, dict):
                _LOGGER.debug("%s %s - no config options", watch, config_entry.entry_id)
                continue

            ward: dict[str, Any] = watch.get("ward", None)
            if ward is None:
                continue

            wuid = ward.get(ATTR_ID, None)
            if wuid is None:
                continue

            conf_watches = options.get(CONF_WATCHES, None)
            conf_tyes = options.get(CONF_TYPES, None)

            if conf_watches is None or conf_tyes is None or wuid not in conf_watches or description.key not in conf_tyes:
                continue

            entities.append(XploraSensor(config_entry, coordinator, ward, wuid, description))

    async_add_entities(entities)


class XploraSensor(XploraBaseEntity, SensorEntity):
    """A sensor implementation for Xplora® Watch."""

    def __init__(
        self,
        config_entry: ConfigEntry,
        coordinator: XploraDataUpdateCoordinator,
        ward: dict[str, Any],
        wuid: str,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize a sensor for an Xplora® Watch."""
        super().__init__(config_entry, description, coordinator, wuid)
        if self.watch_uid not in self.coordinator.data:
            return

        self._attr_name: str = f"{ward.get(CONF_NAME)} {ATTR_WATCH} {description.key} ({coordinator.username})".replace(
            "_", " "
        ).title()

        self._attr_unique_id = (
            f"{ward.get(CONF_NAME)}_{ATTR_WATCH}_{description.key}_{wuid}_{coordinator.user_id}".replace(" ", "_")
            .replace("-", "_")
            .lower()
        )
        _LOGGER.debug("Updating sensor: %s | Typ: %s | Watch_ID ...%s", self._attr_name, description.key, wuid[25:])

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if self.entity_description.key == SENSOR_BATTERY:
            return self.coordinator.data[self.watch_uid].get(SENSOR_BATTERY, None)
        if self.entity_description.key == SENSOR_STEP_DAY:
            return self.coordinator.data[self.watch_uid].get(SENSOR_STEP_DAY, 0)
        if self.entity_description.key == SENSOR_XCOIN:
            return self.coordinator.data[self.watch_uid].get(SENSOR_XCOIN, 0)
        if self.entity_description.key == SENSOR_MESSAGE:
            return self.coordinator.data[self.watch_uid].get("unreadMsg", 0)
        if self.entity_description.key == SENSOR_DISTANCE:
            lat = self.coordinator.data[self.watch_uid].get(ATTR_TRACKER_LAT, None)
            lng = self.coordinator.data[self.watch_uid].get(ATTR_TRACKER_LNG, None)
            if lat and lng:
                lat_lng: tuple[float, float] = (float(lat), float(lng))
                return get_location_distance_meter(self.hass, lat_lng)
            return -1
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state attributes that should be added to SENSOR_STATE."""
        data = super().extra_state_attributes or {}
        if (
            self.entity_description.key is SENSOR_MESSAGE
            and self.coordinator.data
            and self.coordinator.data.get(self.watch_uid, None)
            and SENSOR_MESSAGE in self.coordinator.data[self.watch_uid]
            and self.coordinator.data[self.watch_uid].get(SENSOR_MESSAGE, None)
        ):
            return dict(data, **self.coordinator.data[self.watch_uid].get(SENSOR_MESSAGE))
        return dict(data, **{"user": self.coordinator.controller.getUserName()})
