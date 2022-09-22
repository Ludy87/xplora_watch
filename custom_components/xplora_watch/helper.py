"""HelperClasses Xplora® Watch Version 2."""
from __future__ import annotations

from datetime import datetime, timedelta
from geopy import distance

from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE
from homeassistant.core import HomeAssistant

from .const import HOME

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


def get_location_distance_meter(hass: HomeAssistant, lat_lng: tuple[float, float]) -> int:
    home_zone = hass.states.get(HOME).attributes
    return int(
        distance.distance(
            (home_zone[ATTR_LATITUDE], home_zone[ATTR_LONGITUDE]),
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


def service_yaml(hass: HomeAssistant, watches: list[str]):
    path = hass.config.path("custom_components/xplora_watch/services.yaml")
    _LOGGER.debug("services.yaml path: %s", path)
    try:
        with open(path, "w+") as f:
            f.write("# Please do not change the file, it will be overwritten!\n\n")
            f.write("send_message:\n")
            f.write("  name: Send message\n")
            f.write("  description: Send a notification.\n")
            f.write("  fields:\n")
            f.write("    message:\n")
            f.write("      name: Message\n")
            f.write("      description: Message body of the notification.\n")
            f.write("      required: true\n")
            f.write("      example: The window has been open for 10 minutes.\n")
            f.write("      selector:\n")
            f.write("        text:\n")
            f.write("    target:\n")
            f.write("      name: Watch\n")
            f.write("      description: An array of pre-authorized chat_ids to send the notification to.\n")
            f.write("      required: true\n")
            f.write("      selector:\n")
            f.write("        select:\n")
            f.write("          options:\n")
            for watch in watches:
                f.write(f"            - {watch}\n")
    except IOError:
        _LOGGER.exception("Error writing service definition to path '%s'", path)
