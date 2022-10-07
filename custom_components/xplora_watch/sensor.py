"""Reads watch status from Xplora® Watch Version 2."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ID, CONF_NAME, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_WATCH, CONF_TYPES, CONF_WATCHES, DOMAIN, SENSOR_BATTERY, SENSOR_STEP_DAY, SENSOR_XCOIN
from .coordinator import XploraDataUpdateCoordinator
from .entity import XploraBaseEntity

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(key=SENSOR_BATTERY, native_unit_of_measurement=PERCENTAGE, device_class=SensorDeviceClass.BATTERY),
    SensorEntityDescription(
        key=SENSOR_STEP_DAY, icon="mdi:run", state_class=SensorStateClass.TOTAL, entity_category=EntityCategory.DIAGNOSTIC
    ),
    SensorEntityDescription(
        key=SENSOR_XCOIN, icon="mdi:hand-coin", native_unit_of_measurement="💰", device_class=SensorDeviceClass.MONETARY
    ),
)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the Xplora® Watch Version 2 sensors from config entry."""
    coordinator: XploraDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities: list[XploraSensor] = []

    for description in SENSOR_TYPES:
        for watch in coordinator.controller.watchs:
            if config_entry.options:
                ward: dict[str, any] = watch.get("ward")
                wuid = ward.get(ATTR_ID)
                if wuid in config_entry.options.get(CONF_WATCHES):
                    if description.key in config_entry.options.get(CONF_TYPES):
                        sw_version = await coordinator.controller.getWatches(wuid)
                        entities.append(XploraSensor(config_entry, coordinator, ward, sw_version, wuid, description))
            else:
                _LOGGER.debug(f"{watch} {config_entry.entry_id}")
    async_add_entities(entities)


class XploraSensor(XploraBaseEntity, SensorEntity):

    _attr_force_update = False

    def __init__(
        self,
        config_entry: ConfigEntry,
        coordinator: XploraDataUpdateCoordinator,
        ward: dict[str, any],
        sw_version: dict[str, any],
        wuid: str,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(config_entry, description, coordinator, ward, sw_version, wuid)

        for i in range(1, len(config_entry.options.get(CONF_WATCHES)) + 1):
            _wuid: str = config_entry.options.get(f"{CONF_WATCHES}_{i}")
            if "=" in _wuid:
                friendly_name = _wuid.split("=")
                if friendly_name[0] == wuid:
                    self._attr_name = f'{friendly_name[1]} {description.key.replace("_", " ")}'.title()
                else:
                    self._attr_name = (
                        f'{self._ward.get(CONF_NAME)} {ATTR_WATCH} {description.key.replace("_", " ")} {wuid}'.title()
                    )
            else:
                self._attr_name = (
                    f'{self._ward.get(CONF_NAME)} {ATTR_WATCH} {description.key.replace("_", " ")} {wuid}'.title()
                )

        self._attr_unique_id = f"{self._ward.get(CONF_NAME)}-{ATTR_WATCH}-{description.key}-{wuid}"
        _LOGGER.debug(
            "Updating sensor: %s | %s | Watch_ID %s",
            self._attr_name[:-33] if "=" not in _wuid else self._attr_name,
            self.entity_description.key,
            wuid[25:],
        )

    @property
    def native_value(self) -> int:
        if self.entity_description.key == SENSOR_BATTERY:
            return self._coordinator.data[self.watch_uid][SENSOR_BATTERY]
        if self.entity_description.key == SENSOR_STEP_DAY:
            return self._coordinator.data[self.watch_uid][SENSOR_STEP_DAY]
        if self.entity_description.key == SENSOR_XCOIN:
            return self._coordinator.data[self.watch_uid][SENSOR_XCOIN]
        return None
