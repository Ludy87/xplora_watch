"""HelperClasses Xplora® Watch Version 2."""

from __future__ import annotations

import base64
import json
import logging
import os
import shutil
from typing import Any

from geopy import distance
from pydub import AudioSegment

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE, CONF_LANGUAGE
from homeassistant.core import HomeAssistant
from homeassistant.loader import DATA_CUSTOM_COMPONENTS
from homeassistant.util.yaml import save_yaml
from homeassistant.util.yaml.loader import load_yaml

from .const import (
    ATTR_SERVICE_DELETE_MSG,
    ATTR_SERVICE_READ_MSG,
    ATTR_SERVICE_SEE,
    ATTR_SERVICE_SEND_MSG,
    ATTR_SERVICE_SHUTDOWN,
    DEFAULT_LANGUAGE,
    DOMAIN,
    HOME,
)
from .coordinator import XploraDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


def get_location_distance_meter(hass: HomeAssistant, lat_lng: tuple[float, float]) -> int:
    """Get the distance in meters between two lat / lng points."""
    home_zone = hass.states.get(HOME).attributes
    return int(
        distance.distance(
            (home_zone[ATTR_LATITUDE], home_zone[ATTR_LONGITUDE]),
            lat_lng,
        ).m
    )


def is_distance_in_radius(home_lat_lng: tuple[float, float], lat_lng: tuple[float, float], radius: int) -> bool:
    """Checks if distance is within radius of home."""
    if radius >= int(distance.distance(home_lat_lng, lat_lng).m):
        return True
    else:
        return False


def encoded_base64_string_to_file(hass: HomeAssistant, base64_string: str, file_name: str, file_type: str, file_dir: str):
    """Convert base64 encoded string to file."""
    media_path = hass.config.path(f"www/{file_dir}")
    if not os.path.exists(f"{media_path}/{file_name}.{file_type}"):
        try:
            decoded_data = base64.b64decode(base64_string.encode())
            with open(f"{media_path}/{file_name}.{file_type}", "wb") as f:
                f.write(decoded_data)
        except AttributeError:
            return


def encoded_base64_string_to_mp3_file(hass: HomeAssistant, base64_string: str, file_name: str):
    """Convert base64 encoded string to mp3 file."""
    media_path = hass.config.path("www/voice")
    if not os.path.exists(f"{media_path}/{file_name}.mp3"):
        decoded_data = base64.b64decode(base64_string.encode())
        with open(f"{media_path}/{file_name}.amr", "wb") as f:
            f.write(decoded_data)
        if os.path.exists(f"{media_path}/{file_name}.amr"):
            sound = AudioSegment.from_file(f"{media_path}/{file_name}.amr", format="amr")
            sound.export(f"{media_path}/{file_name}.mp3", format="mp3")
            os.remove(f"{media_path}/{file_name}.amr")


async def create_www_directory(hass: HomeAssistant):
    """Create www directory."""
    paths = [
        hass.config.path("www"),  # http://homeassistant.local:8123/local
        hass.config.path("www/image"),  # http://homeassistant.local:8123/local/image/<filename>.jpeg
        hass.config.path("www/video"),  # http://homeassistant.local:8123/local/video/<filename>.mp4
        hass.config.path("www/video/thumb"),  # http://homeassistant.local:8123/local/video/thumb/<filename>.jpeg
        hass.config.path("www/voice"),  # http://homeassistant.local:8123/local/voice/<filename>.mp3
        hass.config.path(f"www/{DOMAIN}"),  # http://homeassistant.local:8123/local/xplora_watch/*
    ]

    def mkdir() -> None:
        """Create a directory."""
        for path in paths:
            if not os.path.exists(path):
                _LOGGER.debug("Creating directory: %s", path)
                os.makedirs(path, exist_ok=True)

    await hass.async_add_executor_job(mkdir)


def move_emojis_directory(hass: HomeAssistant):
    """Move emojis directory to www directory."""
    src_path = hass.config.path(f"{DATA_CUSTOM_COMPONENTS}/{DOMAIN}/emojis")
    dst_path = hass.config.path(f"www/{DOMAIN}")
    if os.path.exists(src_path):
        if os.path.exists(f"{dst_path}/emojis"):
            shutil.rmtree(f"{dst_path}/emojis")
        shutil.move(src_path, dst_path)


async def create_service_yaml_file(hass: HomeAssistant, entry: ConfigEntry, watches: list[str]) -> None:
    """Create a service.yaml file."""

    path = hass.config.path(f"{DATA_CUSTOM_COMPONENTS}/{DOMAIN}/services.yaml")
    _LOGGER.debug("set services.yaml path: %s", path)

    language = entry.options.get(CONF_LANGUAGE, entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE))
    path_json = hass.config.path(f"{DATA_CUSTOM_COMPONENTS}/{DOMAIN}/jsons/service_{language}.json")
    _LOGGER.debug("services_%s.json path: %s", language, path_json)
    try:
        with open(path_json, encoding="utf8") as json_file:
            configuration: dict[str, str] = json.load(json_file)

        yaml_service = load_yaml(path)
        if (
            isinstance(yaml_service, dict)
            and yaml_service.get("see", {})
            and yaml_service.get("see", {}).get("fields", None)
            and yaml_service.get("see", {}).get("fields", {}).get("user", None)
        ):
            configuration = yaml_service

        def set_watches(configurations: Any, names: list[str], watches: list[str]) -> dict[str, str]:
            """Set the watches for the configuration."""
            for name in names:
                option_watches: list[str] = configurations[name]["fields"]["target"]["selector"]["select"]["options"]
                configurations[name]["fields"]["target"]["selector"]["select"]["options"] = sorted(
                    set(option_watches + watches), reverse=True
                )
                user: list[str] = configurations[name]["fields"]["user"]["selector"]["select"]["options"]
                coordinator: XploraDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
                username = coordinator.controller.getUserName()

                name_list = user
                search_name = username

                user = [name for name in name_list if search_name not in name]

                user.append(f"{entry.entry_id} ({username})")
                configurations[name]["fields"]["user"]["selector"]["select"]["options"] = sorted(set(user))
            return configurations

        configuration = set_watches(
            configuration,
            [ATTR_SERVICE_SEND_MSG, ATTR_SERVICE_SEE, ATTR_SERVICE_READ_MSG, ATTR_SERVICE_SHUTDOWN, ATTR_SERVICE_DELETE_MSG],
            watches,
        )

        save_yaml(path, configuration)

    except OSError:
        _LOGGER.exception("Error writing service definition to path '%s'", path)
    except KeyError as error:
        _LOGGER.exception("Key '%s' from service.yaml not found", error)
