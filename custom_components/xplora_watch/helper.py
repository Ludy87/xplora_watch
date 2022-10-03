"""HelperClasses Xplora® Watch Version 2."""
from __future__ import annotations

import logging
from geopy import distance

from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE
from homeassistant.core import HomeAssistant

from .const import HOME

_LOGGER = logging.getLogger(__name__)


def get_location_distance_meter(hass: HomeAssistant, lat_lng: tuple[float, float]) -> int:
    home_zone = hass.states.get(HOME).attributes
    return int(
        distance.distance(
            (home_zone[ATTR_LATITUDE], home_zone[ATTR_LONGITUDE]),
            lat_lng,
        ).m
    )


def get_location_distance(home_lat_lng: tuple[float, float], lat_lng: tuple[float, float], radius: int) -> bool:
    if radius >= int(distance.distance(home_lat_lng, lat_lng).m):
        return True
    else:
        return False


def set_service_yaml(hass: HomeAssistant, watches: list[str]) -> None:
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
            f.write("      description: Choose your watch to receive the message.\n")
            f.write("      required: true\n")
            f.write("      selector:\n")
            f.write("        select:\n")
            f.write("          options:\n")
            for watch in watches:
                f.write(f'            - "{watch}"\n')
            f.write("see:\n")
            f.write("  name: Track Watch\n")
            f.write("  description: Manually update all information from your watch\n")
            f.write("  fields:\n")
            f.write("    target:\n")
            f.write("      name: Watch\n")
            f.write("      description: Select your watch to update data.\n")
            f.write("      required: true\n")
            f.write('      default: "all"\n')
            f.write("      selector:\n")
            f.write("        select:\n")
            f.write("          options:\n")
            f.write("            - all\n")
            for watch in watches:
                f.write(f'            - "{watch}"\n')

    except IOError:
        _LOGGER.exception("Error writing service definition to path '%s'", path)
