"""Reads watch status from Xplora® Watch Version 2."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ID, CONF_NAME, PERCENTAGE, UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
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
        state_class=SensorStateClass.TOTAL,
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
    for desc in SENSOR_TYPES:
        for watch in coordinator.controller.watchs:
            ward = watch.get("ward")
            wuid = ward.get(ATTR_ID, "")
            if (
                config_entry.options
                and wuid in config_entry.options.get(CONF_WATCHES, [])
                and desc.key in config_entry.options.get(CONF_TYPES, [])
            ):
                sw_version = await coordinator.controller.getWatches(wuid)
                entities.append(XploraSensor(config_entry, coordinator, ward, sw_version, wuid, desc))
            elif not config_entry.options:
                _LOGGER.debug(f"{watch} {config_entry.entry_id}")
    async_add_entities(entities)


class XploraSensor(XploraBaseEntity, SensorEntity):
    def __init__(
        self,
        config_entry: ConfigEntry,
        coordinator: XploraDataUpdateCoordinator,
        ward: dict[str, Any],
        sw_version: dict[str, Any],
        wuid: str,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(config_entry, description, coordinator, ward, sw_version, wuid)
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
            "Updating sensor: %s | %s | %s Watch_ID %s",
            self._attr_name[:-33] if _wuid.find("=") == -1 else self._attr_name,
            description.key,
            i,
            wuid[25:],
        )

    @property
    def native_value(self) -> StateType:
        if self.entity_description.key == SENSOR_BATTERY:
            return self.coordinator.data[self.watch_uid][SENSOR_BATTERY]
        if self.entity_description.key == SENSOR_STEP_DAY:
            return self.coordinator.data[self.watch_uid][SENSOR_STEP_DAY]
        if self.entity_description.key == SENSOR_XCOIN:
            return self.coordinator.data[self.watch_uid][SENSOR_XCOIN]
        if self.entity_description.key == SENSOR_MESSAGE:
            return self.coordinator.data[self.watch_uid]["unreadMsg"]
        if self.entity_description.key == SENSOR_DISTANCE:
            if (
                self.coordinator.data[self.watch_uid][ATTR_TRACKER_LAT] is not None
                and self.coordinator.data[self.watch_uid][ATTR_TRACKER_LNG] is not None
            ):
                lat_lng: tuple[float, float] = (
                    float(self.coordinator.data[self.watch_uid][ATTR_TRACKER_LAT]),
                    float(self.coordinator.data[self.watch_uid][ATTR_TRACKER_LNG]),
                )
                return get_location_distance_meter(self.hass, lat_lng)
            else:
                return -1
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = super().extra_state_attributes or {}
        if self.entity_description.key == SENSOR_MESSAGE and self.coordinator.data:
            if self.watch_uid in self.coordinator.data:
                if SENSOR_MESSAGE in self.coordinator.data[self.watch_uid]:
                    if self.coordinator.data[self.watch_uid][SENSOR_MESSAGE]:
                        return dict(data, **self.coordinator.data[self.watch_uid][SENSOR_MESSAGE])
        return dict(data, **{})
