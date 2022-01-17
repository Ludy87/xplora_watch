"""Support for Xplora® Watch tracking."""
from __future__ import annotations

from collections.abc import Awaitable, Callable
import logging
from datetime import datetime

from .const import (
    CONF_START_TIME,
    CONF_TRACKER_SCAN_INTERVAL,
    CONF_TYPES,
    DATA_XPLORA,
    DEVICE_TRACKER_WATCH,
    XPLORA_CONTROLLER,
    DEVICE_TRACKER_LAT,
    DEVICE_TRACKER_LNG,
    DEVICE_TRACKER_RAD,
    DEVICE_TRACKER_COUNTRY,
    DEVICE_TRACKER_COUNTRY_ABBR,
    DEVICE_TRACKER_PROVINCE,
    DEVICE_TRACKER_CITY,
    DEVICE_TRACKER_ADDR,
    DEVICE_TRACKER_POI,
    DEVICE_TRACKER_ISINSAFEZONE,
    DEVICE_TRACKER_SAFEZONELABEL,
)
from pyxplora_api import pyxplora_api_async as PXA

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

    api: PXA.PyXploraApi = hass.data[DATA_XPLORA][discovery_info[XPLORA_CONTROLLER]]
    scan_interval = hass.data[CONF_TRACKER_SCAN_INTERVAL][discovery_info[XPLORA_CONTROLLER]]
    start_time = hass.data[CONF_START_TIME][discovery_info[XPLORA_CONTROLLER]]
    _types = hass.data[CONF_TYPES][discovery_info[XPLORA_CONTROLLER]]

    if DEVICE_TRACKER_WATCH not in _types:
        return False

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
        self._hass = hass
        self._scan_interval = scan_interval
        self._async_see = async_see
        self._api: PXA.PyXploraApi = api
        self.connected = False
        self._watch_location = None
        self._start_time = start_time
        self._first = True

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
            attr[DEVICE_TRACKER_LAT] = device_info["lat"]
        if device_info.get("lng", None):
            attr[DEVICE_TRACKER_LNG] = device_info["lng"]
        if device_info.get("rad", None):
            attr[DEVICE_TRACKER_RAD] = device_info["rad"]
        if device_info.get("country", None):
            attr[DEVICE_TRACKER_COUNTRY] = device_info["country"]
        if device_info.get("countryAbbr", None):
            attr[DEVICE_TRACKER_COUNTRY_ABBR] = device_info["countryAbbr"]
        if device_info.get("province", None):
            attr[DEVICE_TRACKER_PROVINCE] = device_info["province"]
        if device_info.get("city", None):
            attr[DEVICE_TRACKER_CITY] = device_info["city"]
        if device_info.get("addr", None):
            attr[DEVICE_TRACKER_ADDR] = device_info["addr"]
        if device_info.get("poi", None):
            attr[DEVICE_TRACKER_POI] = device_info["poi"]
        if device_info.get("isInSafeZone", None):
            attr[DEVICE_TRACKER_ISINSAFEZONE] = device_info["isInSafeZone"]
        if device_info.get("safeZoneLabel", None):
            attr[DEVICE_TRACKER_SAFEZONELABEL] = device_info["safeZoneLabel"]
        await self._async_see(
            source_type=await self._api.getWatchLocateType_async(),
            dev_id=slugify(await self._api.getWatchUserName_async() + " Watch Tracker"),
            gps=(device_info.get("lat"), device_info.get("lng")),
            gps_accuracy=device_info.get("rad"),
            battery=await self._api.getWatchBattery_async(),
            attributes=attr,
            icon="mdi:watch",
            #picture=f"https://api.myxplora.com/file?id={self._api.getWatchUserIcon_async()}",
        )
