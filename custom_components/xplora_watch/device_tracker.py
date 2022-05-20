"""Support for Xplora® Watch tracking."""
from __future__ import annotations

import logging

from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from typing import Any, Dict, List

import aiohttp
from .geocoder import OpenCageGeocodeUA

from homeassistant.components.device_tracker import SOURCE_TYPE_GPS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import slugify

from geopy import distance

from .const import (
    ATTR_TRACKER_ADDR,
    ATTR_TRACKER_CITY,
    ATTR_TRACKER_COUNTRY,
    ATTR_TRACKER_COUNTRY_ABBR,
    ATTR_TRACKER_DISTOHOME,
    ATTR_TRACKER_ISINSAFEZONE,
    ATTR_TRACKER_LAST_TRACK,
    ATTR_TRACKER_LAT,
    ATTR_TRACKER_LATITUDE,
    ATTR_TRACKER_LON,
    ATTR_TRACKER_LONGITUDE,
    ATTR_TRACKER_POI,
    ATTR_TRACKER_PROVINCE,
    ATTR_TRACKER_RAD,
    ATTR_TRACKER_SAFEZONEADRESS,
    ATTR_TRACKER_SAFEZONEGROUPNAME,
    ATTR_TRACKER_SAFEZONELABEL,
    ATTR_TRACKER_SAFEZONENAME,
    ATTR_TRACKER_TIME,
    CONF_OPENCAGE_APIKEY,
    CONF_SAFEZONES,
    CONF_TRACKER_SCAN_INTERVAL,
    CONF_TYPES,
    CONF_WATCHUSER_ID,
    DATA_XPLORA,
    DEVICE_TRACKER_WATCH,
    XPLORA_CONTROLLER,
)
from .helper import XploraDevice

from pyxplora_api import pyxplora_api_async as PXA

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

    if DEVICE_TRACKER_WATCH not in hass.data[CONF_TYPES][discovery_info[XPLORA_CONTROLLER]]:
        return False
    _LOGGER.debug("set Tracker")

    controller: PXA.PyXploraApi = hass.data[DATA_XPLORA][discovery_info[XPLORA_CONTROLLER]]
    opencage: str = hass.data[CONF_OPENCAGE_APIKEY][discovery_info[XPLORA_CONTROLLER]]
    scan_interval: timedelta = hass.data[CONF_TRACKER_SCAN_INTERVAL][discovery_info[XPLORA_CONTROLLER]]
    start_time: float = datetime.timestamp(datetime.now())
    watch_ids: List[str] = hass.data[CONF_WATCHUSER_ID][discovery_info[XPLORA_CONTROLLER]]

    if hass.data[CONF_SAFEZONES][discovery_info[XPLORA_CONTROLLER]] == "show":
        _LOGGER.debug("show safezone")
        for watch_id in watch_ids:
            i = 1
            for safeZone in await controller.getWatchSafeZones(watch_id):
                if safeZone:
                    lat = float(safeZone.get("lat", "0.0"))
                    lng = float(safeZone.get("lng", "0.0"))
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
                        dev_id=slugify("Safezone " + str(i) + " " + watch_id),
                        gps=(lat, lng),
                        gps_accuracy=rad,
                        host_name=safeZone.get("name") + " " + watch_id,
                        attributes=attr,
                        icon="mdi:crosshairs-gps",
                    )
                    i += 1

    _LOGGER.debug("set WatchScanner")
    scanner = WatchScanner(
        hass,
        async_see,
        controller,
        scan_interval,
        start_time,
        watch_ids,
        opencage,
    )
    return await scanner.async_init()


class WatchScanner(XploraDevice):
    def __init__(
        self,
        hass,
        async_see,
        controller,
        scan_interval,
        start_time,
        watch_ids,
        opencage,
    ) -> None:
        """Initialize."""
        super().__init__(scan_interval, start_time)
        self.connected = False
        self._controller: PXA.PyXploraApi = controller
        self._watch_ids = watch_ids
        self._async_see = async_see
        self._hass: HomeAssistant = hass
        self._watch_location: Dict[str, Any] = {}
        self._opencage = opencage

    async def async_init(self) -> bool:
        """Further initialize connection to Xplora® API."""
        _LOGGER.debug("set async_init")
        await self._controller.init()
        for watch_id in self._watch_ids:
            username = self._controller.getWatchUserNames(watch_id)
            if username is None:
                _LOGGER.error("Can not connect to Xplora® API")
                return False

        await self._async_update()
        track_update = timedelta(seconds=10)
        async_track_time_interval(self._hass, self._async_update, track_update)
        return True

    async def _async_update(self, now=None) -> None:
        """Update info from Xplora® API."""
        self.xtn = self._hass.states.get("input_boolean.xplora_track_now")  # tracking ever 10 sec

        if self.xtn:
            if self.xtn.state == "on":
                _LOGGER.warning("don't forget this one to disable input_boolean.xplora_track_now!")
                await self._update()

        xts_state = "on"
        self.xts = self._hass.states.get("input_boolean.xplora_tracker_switch")  # disable tracking
        if self.xts:
            xts_state = self.xts.state

        if (self._update_timer() and xts_state == "on") or self._first:
            _LOGGER.debug("xplora_tracker_switch")
            await self._update()

    async def _update(self) -> None:
        self._first = False
        self._start_time = datetime.timestamp(datetime.now())
        for watch_id in self._watch_ids:
            if await self._controller.getWatchBattery(watch_id) == -1:
                _LOGGER.warn(f"no Data from Xplora Server: Watch ID {watch_id}, restart your Watch and try again!")
                continue
            _LOGGER.debug(f"Updating device data {watch_id}")
            self._watch_location = await self._controller.getWatchLastLocation(wuid=watch_id, withAsk=True)
            self._hass.async_create_task(self.import_device_data(watch_id))

    def get_location_distance(self, watch_c: tuple[float, float]) -> int:
        home_zone = self._hass.states.get("zone.home").attributes
        return int(distance.distance((home_zone[ATTR_TRACKER_LATITUDE], home_zone[ATTR_TRACKER_LONGITUDE]), watch_c).m)

    async def import_device_data(self, watch_id: str) -> None:
        """Import device data from Xplora® API."""
        watch_location_info: Dict[str, Any] = self._watch_location
        attr: Dict[str, Any] = {}
        if watch_location_info.get("lat"):
            attr[ATTR_TRACKER_LATITUDE] = float(watch_location_info.get("lat", "0.0"))
            attr[ATTR_TRACKER_LAT] = watch_location_info.get("lat", "0.0")
        if watch_location_info.get("lng"):
            attr[ATTR_TRACKER_LONGITUDE] = float(watch_location_info.get("lng", "0.0"))
            attr[ATTR_TRACKER_LON] = watch_location_info.get("lng", "0.0")
        if watch_location_info.get("rad", -1):
            attr[ATTR_TRACKER_RAD] = watch_location_info["rad"]
        if watch_location_info.get(ATTR_TRACKER_COUNTRY, ""):
            attr[ATTR_TRACKER_COUNTRY] = watch_location_info[ATTR_TRACKER_COUNTRY]
        if watch_location_info.get(ATTR_TRACKER_COUNTRY_ABBR, ""):
            attr[ATTR_TRACKER_COUNTRY_ABBR] = watch_location_info[ATTR_TRACKER_COUNTRY_ABBR]
        if watch_location_info.get(ATTR_TRACKER_PROVINCE, ""):
            attr[ATTR_TRACKER_PROVINCE] = watch_location_info[ATTR_TRACKER_PROVINCE]
        if watch_location_info.get(ATTR_TRACKER_CITY, ""):
            attr[ATTR_TRACKER_CITY] = watch_location_info[ATTR_TRACKER_CITY]

        if self._opencage == "":
            timeout = aiohttp.ClientTimeout(total=12)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    "https://nominatim.openstreetmap.org/reverse?lat={}&lon={}&format=json".format(
                        attr[ATTR_TRACKER_LATITUDE], attr[ATTR_TRACKER_LONGITUDE]
                    )
                ) as response:
                    await session.close()
                    res: Dict[str, Any] = await response.json()
                    address: Dict[str, str] = res.get("address", [])
                    if address:
                        watch_location_info[ATTR_TRACKER_COUNTRY] = address.get(ATTR_TRACKER_COUNTRY, "")
                        attr[ATTR_TRACKER_ADDR] = "{} {}, {} {}, {}, {}".format(
                            address.get("road", ""),
                            address.get("house_number", ""),
                            address.get("postcode", ""),
                            address.get(ATTR_TRACKER_CITY, ""),
                            address.get("state", ""),
                            address.get(ATTR_TRACKER_COUNTRY, ""),
                        )
                        attr["licence"] = res.get("licence", None)
                        _LOGGER.debug("load address from openstreetmap{} {}".format(attr["licence"], watch_id))
        if not attr.get("licence", None):
            _LOGGER.debug("load address from OpenCageData {}".format(watch_id))
            async with OpenCageGeocodeUA(self._opencage) as geocoder:
                results: List[Any] = await geocoder.reverse_geocode_async(
                    watch_location_info.get("lat", "0.0"),
                    watch_location_info.get("lng", "0.0"),
                    no_annotations=1,
                    pretty=1,
                    no_record=1,
                    no_dedupe=1,
                    limit=1,
                    abbrv=1,
                )
                attr[ATTR_TRACKER_ADDR] = results[0]["formatted"]

        if watch_location_info.get(ATTR_TRACKER_POI, ""):
            attr[ATTR_TRACKER_POI] = watch_location_info[ATTR_TRACKER_POI]
        if watch_location_info.get(ATTR_TRACKER_ISINSAFEZONE, ""):
            attr[ATTR_TRACKER_ISINSAFEZONE] = watch_location_info[ATTR_TRACKER_ISINSAFEZONE]
        if watch_location_info.get(ATTR_TRACKER_SAFEZONELABEL, ""):
            attr[ATTR_TRACKER_SAFEZONELABEL] = watch_location_info[ATTR_TRACKER_SAFEZONELABEL]

        attr[ATTR_TRACKER_LAST_TRACK] = datetime.fromtimestamp(watch_location_info.get(ATTR_TRACKER_TIME, "")).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        lat_lng: tuple[float, float] = (
            float(watch_location_info.get("lat", "0.0")),
            float(watch_location_info.get("lng", "0.0")),
        )
        distanceToHome = self.get_location_distance(lat_lng)
        attr[ATTR_TRACKER_DISTOHOME] = distanceToHome

        await self._async_see(
            source_type=SOURCE_TYPE_GPS,
            dev_id=slugify(self._controller.getWatchUserNames(wuid=watch_id) + " Watch Tracker " + watch_id),
            gps=lat_lng,
            gps_accuracy=watch_location_info.get("rad", 0),
            battery=await self._controller.getWatchBattery(wuid=watch_id),
            host_name=f"{self._controller.getWatchUserNames(wuid=watch_id)} Watch Tracker {watch_id}",
            attributes=attr,
            icon="mdi:watch",
            picture=(self._controller.getWatchUserIcons(wuid=watch_id)),
        )
