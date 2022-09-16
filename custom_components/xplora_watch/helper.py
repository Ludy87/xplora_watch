"""HelperClasses Xplora® Watch Version 2."""
from __future__ import annotations

from datetime import datetime, timedelta
from geopy import distance

from .const import ATTR_TRACKER_LATITUDE, ATTR_TRACKER_LONGITUDE, HOME

import logging

_LOGGER = logging.getLogger(__name__)


class XploraUpdateTime:
    def __init__(self, scan_interval: timedelta, start_time: float) -> None:
        self._first = True
        self._start_time = start_time
        self._scan_interval = scan_interval

    def _update_timer(self) -> int:
        return int(datetime.timestamp(datetime.now()) - self._start_time) > self._scan_interval.total_seconds()


class XploraDevice(XploraUpdateTime):
    """Representation of a Xplora® device."""

    def __init__(self, scan_interval: timedelta, start_time: float) -> None:
        """Set up the Xplora® device."""
        super().__init__(scan_interval, start_time)


def get_location_distance_meter(hass, lat_lng: tuple[float, float]) -> int:
    home_zone = hass.states.get(HOME).attributes
    return int(
        distance.distance(
            (home_zone[ATTR_TRACKER_LATITUDE], home_zone[ATTR_TRACKER_LONGITUDE]),
            lat_lng,
        ).m
    )


def get_location_distance(home_lat_lng: tuple[float, float], lat_lng: tuple[float, float], radius: int) -> int:
    if radius >= int(
        distance.distance(
            home_lat_lng,
            lat_lng,
        ).m
    ):
        return True
    else:
        return False
