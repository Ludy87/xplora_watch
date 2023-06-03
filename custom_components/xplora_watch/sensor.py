"""Reads watch status from Xplora® Watch Version 2."""
from __future__ import annotations

import logging
from typing import Dict

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
        device_class=SensorDeviceClass.ENUM,
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

            ward: Dict[str, any] = watch.get("ward", None)
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
            entities.append(XploraSensor(config_entry, coordinator, ward, sw_version, wuid, description))

    async_add_entities(entities)


class XploraSensor(XploraBaseEntity, SensorEntity):
    def __init__(
        self,
        config_entry: ConfigEntry,
        coordinator: XploraDataUpdateCoordinator,
        ward: Dict[str, any],
        sw_version: Dict[str, any],
        wuid: str,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(config_entry, description, coordinator, ward, sw_version, wuid)
        if self.watch_uid not in self.coordinator.data:
            return
        self._watch_data: Dict[str, any] = self.coordinator.data[self.watch_uid]

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
            "Updating sensor: %s | Typ: %s | %s Watch_ID %s",
            self._attr_name[:-33] if _wuid.find("=") == -1 else self._attr_name,
            description.key,
            i,
            wuid[25:],
        )

    @property
    def native_value(self) -> StateType:
        if self.entity_description.key == SENSOR_BATTERY:
            return self._watch_data.get(SENSOR_BATTERY, None)
        if self.entity_description.key == SENSOR_STEP_DAY:
            return self._watch_data.get(SENSOR_STEP_DAY, 0)
        if self.entity_description.key == SENSOR_XCOIN:
            return self._watch_data.get(SENSOR_XCOIN, 0)
        if self.entity_description.key == SENSOR_MESSAGE:
            return self._watch_data.get("unreadMsg", 0)
        if self.entity_description.key == SENSOR_DISTANCE:
            lat = self._watch_data.get(ATTR_TRACKER_LAT, None)
            lng = self._watch_data.get(ATTR_TRACKER_LNG, None)
            if lat and lng:
                lat_lng: tuple[float, float] = (float(lat), float(lng))
                return get_location_distance_meter(self.hass, lat_lng)
            return -1
        return None

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        data = super().extra_state_attributes or {}
        if (
            (self.entity_description.key != SENSOR_MESSAGE and not self.coordinator.data)
            or self.watch_uid not in self.coordinator.data
            or SENSOR_MESSAGE not in self._watch_data
            or self._watch_data.get(SENSOR_MESSAGE, None)
        ):
            return dict(data, **{})
        return dict(data, **self._watch_data.get(SENSOR_MESSAGE))
