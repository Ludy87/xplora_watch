"""Support for Xplora® Watch tracking."""
from __future__ import annotations

from collections.abc import Awaitable, Callable
import logging
from datetime import datetime

from .const import (
    ATTR_TRACKER_LAT,
    ATTR_TRACKER_LNG,
    ATTR_TRACKER_RAD,
    ATTR_TRACKER_COUNTRY,
    ATTR_TRACKER_COUNTRY_ABBR,
    ATTR_TRACKER_PROVINCE,
    ATTR_TRACKER_CITY,
    ATTR_TRACKER_ADDR,
    ATTR_TRACKER_POI,
    ATTR_TRACKER_ISINSAFEZONE,
    ATTR_TRACKER_SAFEZONEADRESS,
    ATTR_TRACKER_SAFEZONEGROUPNAME,
    ATTR_TRACKER_SAFEZONELABEL,
    ATTR_TRACKER_SAFEZONENAME,
    CONF_SAFEZONES,
    CONF_START_TIME,
    CONF_TRACKER_SCAN_INTERVAL,
    CONF_TYPES,
    DATA_XPLORA,
    DEVICE_TRACKER_WATCH,
    XPLORA_CONTROLLER,
)
from pyxplora_api import pyxplora_api_async as PXA

from homeassistant.components.device_tracker.const import SOURCE_TYPE_GPS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import slugify

_LOGGER = logging.getLogger(__name__)

async def async_setup_scanner(
    hass: HomeAssistant,
    config: ConfigType,
    async_see: Callable[..., Awaitable[None]],
    discovery_info: DiscoveryInfoType | None = None,
) -> bool:
    """Validate the configuration and return a Xplora® scanner."""
    if discovery_info is None:
        return False
    _LOGGER.debug(f"set Tracker")

    if DEVICE_TRACKER_WATCH not in hass.data[CONF_TYPES][discovery_info[XPLORA_CONTROLLER]]:
        return False

    api: PXA.PyXploraApi = hass.data[DATA_XPLORA][discovery_info[XPLORA_CONTROLLER]]
    scan_interval = hass.data[CONF_TRACKER_SCAN_INTERVAL][discovery_info[XPLORA_CONTROLLER]]
    start_time = hass.data[CONF_START_TIME][discovery_info[XPLORA_CONTROLLER]]

    if hass.data[CONF_SAFEZONES][discovery_info[XPLORA_CONTROLLER]]:
        i = 1
        for safeZone in await api.getSafeZones_async():
            if safeZone:
                lat = safeZone.get("lat")
                lng = safeZone.get("lng")
                rad = safeZone.get("rad")
                attr = {}
                if safeZone.get("name", None):
                    attr[ATTR_TRACKER_SAFEZONENAME] = safeZone.get("name")
                if safeZone.get("address", None):
                    attr[ATTR_TRACKER_SAFEZONEADRESS] = safeZone.get("address")
                if safeZone.get("groupName", None):
                    attr[ATTR_TRACKER_SAFEZONEGROUPNAME] = safeZone.get("groupName")
                await async_see(
                    source_type=SOURCE_TYPE_GPS,
                    dev_id=slugify("Safezone " + str(i)),
                    gps=(lat, lng),
                    gps_accuracy=rad,
                    attributes=attr,
                    icon="mdi:crosshairs-gps",
                )
                i += 1

    _LOGGER.debug(f"set WatchScanner")
    scanner = WatchScanner(
        hass,
        async_see,
        api,
        scan_interval,
        start_time,
    )

    return await scanner.async_init()

class WatchScanner:
    def __init__(
        self,
        hass,
        async_see,
        api,
        scan_interval,
        start_time,
    ) -> None:
        """Initialize."""
        self.connected = False
        self._api: PXA.PyXploraApi = api
        self._async_see = async_see
        self._first = True
        self._hass = hass
        self._scan_interval = scan_interval
        self._start_time = start_time
        self._watch_location = None

    def __update_timer(self) -> int:
        return (int(datetime.timestamp(datetime.now()) - self._start_time) > self._scan_interval.total_seconds())

    async def async_init(self) -> bool:
        """Further initialize connection to Xplora® API."""
        _LOGGER.debug(f"set async_init")
        await self._api.init_async()
        username = await self._api.getWatchUserName_async()
        if username is None:
            _LOGGER.error("Can not connect to Xplora® API")
            return False

        await self._async_update()
        async_track_time_interval(self._hass, self._async_update, self._scan_interval)
        return True

    async def _async_update(self, now=None) -> None:
        """Update info from Xplora® API."""
        if self.__update_timer() or self._first:
            self._first = False
            self._start_time = datetime.timestamp(datetime.now())
            _LOGGER.debug("Updating device data")
            self._watch_location = await self._api.getWatchLastLocation_async()
            self._hass.async_create_task(self.import_device_data())

    async def import_device_data(self) -> None:
        """Import device data from Xplora® API."""
        device_info = self._watch_location
        attr = {}
        if device_info.get("lat", None):
            attr[ATTR_TRACKER_LAT] = device_info["lat"]
        if device_info.get("lng", None):
            attr[ATTR_TRACKER_LNG] = device_info["lng"]
        if device_info.get("rad", None):
            attr[ATTR_TRACKER_RAD] = device_info["rad"]
        if device_info.get("country", None):
            attr[ATTR_TRACKER_COUNTRY] = device_info["country"]
        if device_info.get("countryAbbr", None):
            attr[ATTR_TRACKER_COUNTRY_ABBR] = device_info["countryAbbr"]
        if device_info.get("province", None):
            attr[ATTR_TRACKER_PROVINCE] = device_info["province"]
        if device_info.get("city", None):
            attr[ATTR_TRACKER_CITY] = device_info["city"]
        if device_info.get("addr", None):
            attr[ATTR_TRACKER_ADDR] = device_info["addr"]
        if device_info.get("poi", None):
            attr[ATTR_TRACKER_POI] = device_info["poi"]
        if device_info.get("isInSafeZone", None):
            attr[ATTR_TRACKER_ISINSAFEZONE] = device_info["isInSafeZone"]
        if device_info.get("safeZoneLabel", None):
            attr[ATTR_TRACKER_SAFEZONELABEL] = device_info["safeZoneLabel"]
        await self._async_see(
            source_type=await self._api.getWatchLocateType_async(),
            dev_id=slugify(await self._api.getWatchUserName_async() + " Watch Tracker"),
            gps=(device_info.get("lat"), device_info.get("lng")),
            gps_accuracy=device_info.get("rad"),
            battery=await self._api.getWatchBattery_async(),
            attributes=attr,
            icon="mdi:watch",
            picture=(await self._api.getWatchUserIcon_async()),
        )
