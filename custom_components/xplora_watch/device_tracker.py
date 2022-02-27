"""Support for Xplora® Watch tracking."""
from __future__ import annotations

from collections.abc import Awaitable, Callable
import logging
from datetime import datetime

from math import radians, cos
import numpy as np
import itertools

from .const import (
    ATTR_TRACKER_ADDR,
    ATTR_TRACKER_CITY,
    ATTR_TRACKER_COUNTRY,
    ATTR_TRACKER_COUNTRY_ABBR,
    ATTR_TRACKER_DISTOHOME,
    ATTR_TRACKER_ISINSAFEZONE,
    ATTR_TRACKER_LAT,
    ATTR_TRACKER_LNG,
    ATTR_TRACKER_POI,
    ATTR_TRACKER_PROVINCE,
    ATTR_TRACKER_RAD,
    ATTR_TRACKER_SAFEZONEADRESS,
    ATTR_TRACKER_SAFEZONEGROUPNAME,
    ATTR_TRACKER_SAFEZONELABEL,
    ATTR_TRACKER_SAFEZONENAME,
    CONF_CHILD_PHONENUMBER,
    CONF_SAFEZONES,
    CONF_TRACKER_SCAN_INTERVAL,
    CONF_TYPES,
    DATA_XPLORA,
    DEVICE_TRACKER_WATCH,
    XPLORA_CONTROLLER,
)
from .helper import XploraDevice
from pyxplora_api import pyxplora_api_async as PXA

from homeassistant.components.device_tracker import SOURCE_TYPE_GPS
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

    controller: PXA.PyXploraApi = hass.data[DATA_XPLORA][discovery_info[XPLORA_CONTROLLER]]
    child_no = hass.data[CONF_CHILD_PHONENUMBER][discovery_info[XPLORA_CONTROLLER]]
    scan_interval = hass.data[CONF_TRACKER_SCAN_INTERVAL][discovery_info[XPLORA_CONTROLLER]]
    start_time = datetime.timestamp(datetime.now())

    if hass.data[CONF_SAFEZONES][discovery_info[XPLORA_CONTROLLER]] == "show":
        for id in child_no:
            i = 1
            for safeZone in await controller.getSafeZones_async(id):
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
                        dev_id=slugify("Safezone " + str(i) + " " + id),
                        gps=(lat, lng),
                        gps_accuracy=rad,
                        host_name=safeZone.get("name") + " " + id,
                        attributes=attr,
                        icon="mdi:crosshairs-gps",
                    )
                    i += 1

    _LOGGER.debug(f"set WatchScanner")
    scanner = WatchScanner(
        hass,
        async_see,
        controller,
        scan_interval,
        start_time,
        child_no,
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
        child_no,
    ) -> None:
        """Initialize."""
        super().__init__(scan_interval, start_time)
        self.connected = False
        self._controller: PXA.PyXploraApi = controller
        self._child_no = child_no
        self._async_see = async_see
        self._hass = hass
        self._watch_location = None

    async def async_init(self) -> bool:
        """Further initialize connection to Xplora® API."""
        _LOGGER.debug(f"set async_init")
        await self._controller.init_async()
        for id in self._child_no:
            username = await self._controller.getWatchUserName_async(id)
            if username is None:
                _LOGGER.error("Can not connect to Xplora® API")
                return False

        await self._async_update()
        async_track_time_interval(self._hass, self._async_update, self._scan_interval)
        return True

    async def _async_update(self, now=None) -> None:
        """Update info from Xplora® API."""
        xts_state = 'on'
        xts = self._hass.states.get('input_boolean.xplora_tracker_switch')
        if xts:
            xts_state = xts.state
        if (self._update_timer() and xts_state == 'on') or self._first:
            self._first = False
            self._start_time = datetime.timestamp(datetime.now())
            for id in self._child_no:
                _LOGGER.debug("Updating device data")
                self._watch_location = await self._controller.getWatchLastLocation_async(True, watchID=id)
                self._hass.async_create_task(self.import_device_data(id))

    def get_location(self):
        home_zone = self._hass.states.get('zone.home').attributes
        lots = np.array(list(itertools.repeat((home_zone[ATTR_TRACKER_LAT], home_zone[ATTR_TRACKER_LNG]), 100000)))
        return lots

    def get_shortest_in(self, needle, haystack):
        dlat = np.radians(haystack[:,0]) - radians(needle[0])
        dlon = np.radians(haystack[:,1]) - radians(needle[1])
        a = np.square(np.sin(dlat/2.0)) + cos(radians(needle[0])) * np.cos(np.radians(haystack[:,0])) * np.square(np.sin(dlon/2.0))
        great_circle_distance = 2 * np.arcsin(np.minimum(np.sqrt(a), np.repeat(1, len(a))))
        d = 3956.0 * great_circle_distance
        return np.min(d)

    async def import_device_data(self, id) -> None:
        """Import device data from Xplora® API."""
        device_info = self._watch_location
        attr = {}
        if device_info.get("lat", None):
            attr[ATTR_TRACKER_LAT] = device_info["lat"]
        if device_info.get("lng", None):
            attr[ATTR_TRACKER_LNG] = device_info["lng"]
        if device_info.get("rad", None):
            attr[ATTR_TRACKER_RAD] = device_info["rad"]
        if device_info.get(ATTR_TRACKER_COUNTRY, None):
            attr[ATTR_TRACKER_COUNTRY] = device_info[ATTR_TRACKER_COUNTRY]
        if device_info.get(ATTR_TRACKER_COUNTRY_ABBR, None):
            attr[ATTR_TRACKER_COUNTRY_ABBR] = device_info[ATTR_TRACKER_COUNTRY_ABBR]
        if device_info.get(ATTR_TRACKER_PROVINCE, None):
            attr[ATTR_TRACKER_PROVINCE] = device_info[ATTR_TRACKER_PROVINCE]
        if device_info.get(ATTR_TRACKER_CITY, None):
            attr[ATTR_TRACKER_CITY] = device_info[ATTR_TRACKER_CITY]
        if device_info.get(ATTR_TRACKER_ADDR, None):
            attr[ATTR_TRACKER_ADDR] = device_info[ATTR_TRACKER_ADDR]
        if device_info.get(ATTR_TRACKER_POI, None):
            attr[ATTR_TRACKER_POI] = device_info[ATTR_TRACKER_POI]
        if device_info.get(ATTR_TRACKER_ISINSAFEZONE, None):
            attr[ATTR_TRACKER_ISINSAFEZONE] = device_info[ATTR_TRACKER_ISINSAFEZONE]
        if device_info.get(ATTR_TRACKER_SAFEZONELABEL, None):
            attr[ATTR_TRACKER_SAFEZONELABEL] = device_info[ATTR_TRACKER_SAFEZONELABEL]

        attr['last Track'] = datetime.now()
        distanceToHome = self.get_shortest_in((float(device_info.get("lat")), float(device_info.get("lng"))), self.get_location())
        attr[ATTR_TRACKER_DISTOHOME] = distanceToHome
        if distanceToHome > attr[ATTR_TRACKER_RAD]:
            source_type = SOURCE_TYPE_GPS
        else:
            source_type = device_info.get("locateTypec", await self._controller.getWatchLocateType_async(id))

        await self._async_see(
            source_type=source_type,
            dev_id=slugify(await self._controller.getWatchUserName_async(id) + " Watch Tracker " + id),
            gps=(device_info.get("lat"), device_info.get("lng")),
            gps_accuracy=device_info.get("rad"),
            battery=await self._controller.getWatchBattery_async(id),
            host_name=f"{await self._controller.getWatchUserName_async(id)} Watch Tracker {id}",
            attributes=attr,
            icon="mdi:watch",
            picture=(await self._controller.getWatchUserIcon_async(id)),
        )
