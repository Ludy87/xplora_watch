"""Config flow for Xplora® Watch Version 2."""

from __future__ import annotations

from collections import OrderedDict
import logging
from types import MappingProxyType
from typing import Any

from homeassistant import config_entries, core
from homeassistant.config_entries import ConfigEntry, OptionsFlow, OptionsFlowWithConfigEntry
from homeassistant.const import (
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    CONF_COUNTRY_CODE,
    CONF_EMAIL,
    CONF_LANGUAGE,
    CONF_PASSWORD,
    CONF_RADIUS,
    CONF_SCAN_INTERVAL,
    STATE_OFF,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import aiohttp_client
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
from pyxplora_api.exception_classes import Error, LoginError, PhoneOrEmailFail
from pyxplora_api.pyxplora_api_async import PyXploraApi
from pyxplora_api.status import UserContactType
import voluptuous as vol

from .const import (
    CONF_HOME_LATITUDE,
    CONF_HOME_LONGITUDE,
    CONF_HOME_RADIUS,
    CONF_HOME_SAFEZONE,
    CONF_MAPS,
    CONF_MESSAGE,
    CONF_OPENCAGE_APIKEY,
    CONF_PHONENUMBER,
    CONF_REMOVE_MESSAGE,
    CONF_SIGNIN_TYP,
    CONF_TIMEZONE,
    CONF_TYPES,
    CONF_USERLANG,
    CONF_WATCHES,
    DEFAULT_LANGUAGE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    HOME,
    HOME_SAFEZONE,
    MANUFACTURER,
    MAPS,
    SENSORS,
    SIGNIN,
    SUPPORTED_LANGUAGES,
)
from .const_schema import DATA_SCHEMA_EMAIL, DATA_SCHEMA_PHONE

_LOGGER = logging.getLogger(__name__)


@callback
async def sign_in(hass: core.HomeAssistant, data: dict[str, Any] | MappingProxyType[str, Any]) -> PyXploraApi:
    """Sign in to the Xplora® API."""
    controller: PyXploraApi = PyXploraApi(
        countrycode=data.get(CONF_COUNTRY_CODE, None),
        phoneNumber=data.get(CONF_PHONENUMBER, None),
        password=data.get(CONF_PASSWORD, ""),
        userLang=data.get(CONF_USERLANG, None),
        timeZone=data.get(CONF_TIMEZONE, None),
        email=data.get(CONF_EMAIL, None),
        session=aiohttp_client.async_get_clientsession(hass),
    )
    await controller.init()
    return controller


async def validate_input(hass: core.HomeAssistant, data: dict[str, Any]) -> dict[str, str]:
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """

    account = PyXploraApi(session=aiohttp_client.async_create_clientsession(hass))
    await account.init(signup=False)
    if not await account.checkEmailOrPhoneExist(
        UserContactType.EMAIL if data.get(CONF_EMAIL, None) else UserContactType.PHONE,
        email=data.get(CONF_EMAIL, None),
        countryCode=data.get(CONF_COUNTRY_CODE, None),
        phoneNumber=data.get(CONF_PHONENUMBER, None),
    ):
        raise PhoneOrEmailFail()

    try:
        await sign_in(hass=hass, data=data)
    except LoginError as err:
        raise LoginError(err.error_message) from err

    # Return info that you want to store in the config entry.
    return {"title": f"{MANUFACTURER}"}


def validate_options_input(user_input: dict[str, Any]) -> dict[str, str]:
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    errors = {}
    key: str = user_input[CONF_OPENCAGE_APIKEY]
    maps = user_input[CONF_MAPS]

    if maps == MAPS[1] and len(key) == 0:
        errors["base"] = "api_key_error"

    if not user_input[CONF_WATCHES]:
        errors["base"] = "no_watch"

    # Return info that you want to store in the config entry.
    return errors


class XploraConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Xplora® Watch Version 2."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return XploraOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        return self.async_show_menu(step_id="user", menu_options=["user_email", "user_phone"])

    async def async_step_user_phone(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            unique_id = f"{user_input[CONF_PHONENUMBER]}"

            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            info = None
            try:
                info = await validate_input(self.hass, user_input)
            except PhoneOrEmailFail as error:
                _LOGGER.exception(error)
                errors["base"] = "phone_email_invalid"
            except LoginError as error:
                _LOGGER.exception(error)
                errors["base"] = "pass_invalid"
            except Error as error:
                _LOGGER.exception(error)
                errors["base"] = "cannot_connect"

            if info:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user_phone", data_schema=vol.Schema(DATA_SCHEMA_PHONE), errors=errors, last_step=True
        )

    async def async_step_user_email(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            unique_id = f"{user_input[CONF_EMAIL]}"

            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            info = None
            try:
                info = await validate_input(self.hass, user_input)
            except PhoneOrEmailFail as error:
                _LOGGER.exception(error)
                errors["base"] = "phone_email_invalid"
            except LoginError as error:
                _LOGGER.exception(error)
                errors["base"] = "pass_invalid"
            except Error as error:
                _LOGGER.exception(error)
                errors["base"] = "cannot_connect"

            if info:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user_email", data_schema=vol.Schema(DATA_SCHEMA_EMAIL), errors=errors, last_step=True
        )


class XploraOptionsFlowHandler(OptionsFlowWithConfigEntry):
    """Handle a option flow."""

    def get_options(self, signin_typ, schema, language: str, _options, _home_zone) -> vol.Schema:
        """Set SCHEMA return SCHEMA."""
        return vol.Schema(
            {
                vol.Required(CONF_SIGNIN_TYP, default=signin_typ[0]): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(
                                value=signin,
                                label=signin,
                            )
                            for signin in signin_typ
                        ],
                        multiple=False,
                        mode=SelectSelectorMode.LIST,
                    )
                ),
                **schema,
                vol.Required(CONF_LANGUAGE, default=language): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(
                                value=language_key,
                                label=language_value,
                            )
                            for language_dict in SUPPORTED_LANGUAGES
                            for language_key, language_value in language_dict.items()
                        ],
                        multiple=False,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(CONF_MAPS, default=_options.get(CONF_MAPS, MAPS[0])): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(
                                value=value,
                                label=value,
                            )
                            for value in MAPS
                        ],
                        multiple=False,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(CONF_OPENCAGE_APIKEY, default=_options.get(CONF_OPENCAGE_APIKEY, "")): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)
                ),
                vol.Required(
                    CONF_SCAN_INTERVAL, default=_options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0,
                        max=9999,
                        mode=NumberSelectorMode.SLIDER,
                    ),
                ),
                vol.Required(CONF_HOME_SAFEZONE, default=_options.get(CONF_HOME_SAFEZONE, STATE_OFF)): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(
                                value=value,
                                label=label,
                            )
                            for value, label in HOME_SAFEZONE.get(language, HOME_SAFEZONE[DEFAULT_LANGUAGE]).items()
                        ],
                        multiple=False,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_HOME_LATITUDE, default=_options.get(CONF_HOME_LATITUDE, _home_zone[ATTR_LATITUDE])
                ): cv.latitude,
                vol.Required(
                    CONF_HOME_LONGITUDE, default=_options.get(CONF_HOME_LONGITUDE, _home_zone[ATTR_LONGITUDE])
                ): cv.longitude,
                vol.Required(
                    CONF_HOME_RADIUS, default=_options.get(CONF_HOME_RADIUS, _home_zone[CONF_RADIUS])
                ): cv.positive_int,
                vol.Optional(CONF_TYPES, default=_options.get(CONF_TYPES, [])): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(
                                value=value,
                                label=label,
                            )
                            for value, label in SENSORS.get(language, SENSORS[DEFAULT_LANGUAGE]).items()
                        ],
                        multiple=True,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(CONF_MESSAGE, default=_options.get(CONF_MESSAGE, 10)): NumberSelector(
                    NumberSelectorConfig(
                        min=0,
                        max=100,
                        mode=NumberSelectorMode.SLIDER,
                    ),
                ),
                vol.Required(CONF_REMOVE_MESSAGE, default=_options.get(CONF_REMOVE_MESSAGE, False)): BooleanSelector(),
            }
        )

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle options flow."""
        errors: dict[str, str] = {}
        controller = await sign_in(hass=self.hass, data=self.config_entry.data)
        watches = await controller.setDevices()
        _options = self.config_entry.options

        schema = OrderedDict()
        schema[vol.Required(CONF_WATCHES, default=_options.get(CONF_WATCHES, watches))] = SelectSelector(
            SelectSelectorConfig(
                options=[
                    SelectOptionDict(
                        value=watch,
                        label=watch,
                    )
                    for watch in watches
                ],
                multiple=True,
                mode=SelectSelectorMode.LIST,
            )
        )

        language: str = _options.get(CONF_LANGUAGE, self.config_entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE))

        signin_typ = [
            (
                SIGNIN.get(language, SIGNIN[DEFAULT_LANGUAGE]).get(CONF_EMAIL)
                if CONF_EMAIL in self.config_entry.data
                else SIGNIN.get(language, SIGNIN[DEFAULT_LANGUAGE]).get(CONF_PHONENUMBER)
            )
        ]

        _home_zone = self.hass.states.get(HOME).attributes
        options = self.get_options(signin_typ, schema, language, _options, _home_zone)

        if user_input is not None:
            errors = validate_options_input(user_input)

            if not errors:
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init", data_schema=options, errors=errors)
