"""Support for Xplora® Watch Version 2 tracking."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.components.device_tracker.const import (
    ATTR_BATTERY,
    ATTR_LOCATION_NAME,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ID, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    ATTR_SERVICE_USER,
    ATTR_TRACKER_ADDR,
    ATTR_TRACKER_DISTOHOME,
    ATTR_TRACKER_IMEI,
    ATTR_TRACKER_LAST_TRACK,
    ATTR_TRACKER_LAT,
    ATTR_TRACKER_LICENCE,
    ATTR_TRACKER_LNG,
    ATTR_TRACKER_POI,
    ATTR_TRACKER_RAD,
    ATTR_WATCH,
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
    entities: list[XploraDeviceTracker | XploraSafezoneTracker] = []

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

        if (
            conf_watches is None
            or conf_tyes is None
            or wuid not in conf_watches
            or (DEVICE_TRACKER_SAFZONES not in conf_tyes and DEVICE_TRACKER_WATCH not in conf_tyes)
        ):
            continue

        if DEVICE_TRACKER_SAFZONES in conf_tyes:
            safe_zones = await coordinator.controller.getWatchSafeZones(wuid)
            for safe_zone in safe_zones:
                entities.append(XploraSafezoneTracker(config_entry, safe_zone, coordinator, wuid, ward))
        if DEVICE_TRACKER_WATCH in config_entry.options.get(CONF_TYPES):
            image = coordinator.data[wuid].get("entity_picture", None)
            session = async_get_clientsession(hass)
            resp = await session.get(url=image, timeout=5)
            if image is None or resp.status != 200:
                image = "https://s3.eu-central-1.amazonaws.com/kids360uc/default_icon.png"
            entities.append(XploraDeviceTracker(hass, config_entry, coordinator, wuid, ward, image))
    async_add_entities(entities)


class XploraSafezoneTracker(XploraBaseEntity, TrackerEntity, RestoreEntity):
    """Creates a safezone tracker."""

    _attr_force_update: bool = False
    _attr_icon: str | None = "mdi:crosshairs-gps"

    def __init__(
        self,
        config_entry: ConfigEntry,
        safezone: dict[str, Any],
        coordinator: XploraDataUpdateCoordinator,
        wuid: str,
        ward: dict[str, Any],
    ) -> None:
        """Initialize XploraSafezoneTracker instance."""
        super().__init__(config_entry, None, coordinator, wuid)
        self._safezone = safezone

        self._attr_name = (
            f"{ward.get(CONF_NAME)} {ATTR_WATCH} Safezone {safezone[CONF_NAME]} ({coordinator.username})".replace(
                "_", " "
            ).title()
        )

        self._attr_unique_id = (
            f'{ward.get(CONF_NAME)}_{ATTR_WATCH}_safezone_{safezone["vendorId"]}_{wuid}_{coordinator.user_id}'.replace(
                " ", "_"
            )
            .replace("-", "_")
            .lower()
        )

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
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state attributes that should be added to SAFEZONE_STATE."""
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
        ward: dict[str, Any],
        image: str,
    ) -> None:
        """Initialize the Tracker."""
        super().__init__(config_entry, None, coordinator, wuid)
        if self.watch_uid not in coordinator.data:
            return

        self._hass = hass

        self._attr_name = f"{ward.get(CONF_NAME)} {ATTR_WATCH} Tracker ({coordinator.username})".replace("_", " ").title()

        self._attr_unique_id = (
            f"{ward.get(CONF_NAME)}_{ATTR_WATCH}_Tracker_{wuid}_{coordinator.user_id}".replace(" ", "_")
            .replace("-", "_")
            .lower()
        )

        self._attr_entity_picture = image

    @property
    def battery_level(self) -> int | None:
        """Return battery value of the device."""
        return self.coordinator.data[self.watch_uid].get(ATTR_BATTERY, None)

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        return self.coordinator.data[self.watch_uid].get(ATTR_TRACKER_LAT, None)

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        return self.coordinator.data[self.watch_uid].get(ATTR_TRACKER_LNG, None)

    @property
    def source_type(self) -> SourceType | str:
        """Return the source type, eg gps or router, of the device."""
        return SourceType.GPS

    @property
    def location_accuracy(self) -> int:
        """Return the gps accuracy of the device."""
        return self.coordinator.data[self.watch_uid].get("location_accuracy", 0)

    @property
    def address(self) -> str | None:
        """Return a location name for the current location of the device."""
        return self.coordinator.data[self.watch_uid].get(ATTR_LOCATION_NAME, None)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state attributes that should be added to DEVICE_STATE."""
        data = super().extra_state_attributes or {}
        distance_to_home = None

        if self.coordinator.data[self.watch_uid].get(ATTR_TRACKER_LAT, None) and self.coordinator.data[self.watch_uid].get(
            ATTR_TRACKER_LNG, None
        ):
            lat_lng: tuple[float, float] = (
                float(self.coordinator.data[self.watch_uid].get(ATTR_TRACKER_LAT, None)),
                float(self.coordinator.data[self.watch_uid].get(ATTR_TRACKER_LNG, None)),
            )
            distance_to_home = get_location_distance_meter(self._hass, lat_lng)

        return dict(
            data,
            **{
                ATTR_SERVICE_USER: self.coordinator.username,
                ATTR_TRACKER_DISTOHOME: distance_to_home,
                ATTR_TRACKER_ADDR: (
                    self.coordinator.data[self.watch_uid].get(ATTR_LOCATION_NAME, None) if distance_to_home else None
                ),
                ATTR_TRACKER_LAST_TRACK: (
                    self.coordinator.data[self.watch_uid].get("lastTrackTime", None) if distance_to_home else None
                ),
                ATTR_TRACKER_IMEI: self.coordinator.data[self.watch_uid].get(ATTR_TRACKER_IMEI, None),
                ATTR_TRACKER_POI: self.coordinator.data[self.watch_uid].get(ATTR_TRACKER_POI, None),
                ATTR_TRACKER_LICENCE: self.coordinator.data[self.watch_uid].get(ATTR_TRACKER_LICENCE, None),
            },
        )
