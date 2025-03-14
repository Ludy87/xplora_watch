"""Custom Version - Edit by Ludy87.

Geocoder module.
Original Author
author: OpenCage GmbH
email: support@opencagedata.com
https://github.com/OpenCageData/python-opencage-geocoder/
Version: 2.4.0
https://raw.githubusercontent.com/OpenCageData/python-opencage-geocoder/master/LICENSE.txt
"""

from __future__ import annotations  # noqa: I001

import collections
import os
import sys
from datetime import timezone, datetime
from decimal import Decimal

import backoff
import requests
from security import safe_requests

try:
    import aiohttp

    AIOHTTP_AVAILABLE = True

except ImportError:
    AIOHTTP_AVAILABLE = False

DEFAULT_TIMEOUT = 60
DEFAULT_DOMAIN = "api.opencagedata.com"


def backoff_max_time():
    """Get the time in seconds to wait before retrying."""
    return int(os.environ.get("BACKOFF_MAX_TIME", "120"))


class OpenCageGeocodeError(Exception):
    """Base class for all errors/exceptions that can happen when geocoding."""


class InvalidInputError(OpenCageGeocodeError):
    """There was a problem with the input you provided.

    :var bad_value: The value that caused the problem
    """

    def __init__(self, bad_value):
        """Constructor."""
        super().__init__()
        self.bad_value = bad_value

    def __unicode__(self):
        """Convert exception to a string."""
        return "Input must be a unicode string, not " + repr(self.bad_value)[:100]

    __str__ = __unicode__


class UnknownError(OpenCageGeocodeError):
    """There was a problem with the OpenCage server."""


class RateLimitExceededError(OpenCageGeocodeError):
    """Exception raised when account has exceeded it's limit.

    :var datetime reset_time: When your account limit will be reset.
    :var int reset_to: What your account will be reset to.
    """

    def __init__(self, reset_time: datetime, reset_to):
        """Constructor."""
        super().__init__()
        self.reset_time: datetime = reset_time
        self.reset_to = reset_to

    def __unicode__(self):
        """Convert exception to a string."""

        return f"Your rate limit has expired. It will reset to {self.reset_to} on {self.reset_time.isoformat()}"

    __str__ = __unicode__


class NotAuthorizedError(OpenCageGeocodeError):
    """Exception raised when an unautorized API key is used."""

    def __unicode__(self):
        """Convert exception to a string."""
        return "Your API key is not authorized. You may have entered it incorrectly."

    __str__ = __unicode__


class ForbiddenError(OpenCageGeocodeError):
    """Exception raised when a blocked or suspended API key is used."""

    def __unicode__(self):
        """Convert exception to a string."""
        return "Your API key has been blocked or suspended."

    __str__ = __unicode__


class AioHttpError(OpenCageGeocodeError):
    """Exceptions related to async HTTP calls with aiohttp."""


class SSLError(OpenCageGeocodeError):
    """Exception raised when SSL connection to OpenCage server fails."""

    def __unicode__(self):
        """Convert exception to a string."""
        return (
            "SSL Certificate error connecting to OpenCage API. This is usually due to "
            "outdated CA root certificates of the operating system. "
        )

    __str__ = __unicode__


class OpenCageGeocodeUA:
    """Geocoder object.

    Initialize it with your API key:

        >>> geocoder = OpenCageGeocodeUA('your-key-here')

    Query:

        >>> geocoder.geocode("London")

    Reverse geocode a latitude & longitude into a place:

        >>> geocoder.reverse_geocode(51.5104, -0.1021)

    """

    key = ""
    session = None

    def __init__(self, key, protocol="https", domain=DEFAULT_DOMAIN, sslcontext=None):
        """Initialize the geocoder.

        Args:
            key (str): Your API key for OpenCage Geocoder.
            protocol (str, optional): The protocol to use for requests ('http' or 'https'). Defaults to 'https'.
            domain (str, optional): The domain for the OpenCage API. Defaults to DEFAULT_DOMAIN.
            sslcontext: The SSL context to use for secure requests. Defaults to None.
        """
        self.key = key

        if protocol and protocol not in ("http", "https"):
            protocol = "https"
        self.url = protocol + "://" + domain + "/geocode/v1/json"

        # https://docs.aiohttp.org/en/stable/client_advanced.html#ssl-control-for-tcp-sockets
        self.sslcontext = sslcontext

    def __enter__(self):
        """Enters a runtime context, initializing a new requests session."""
        self.session = requests.Session()
        return self

    def __exit__(self, *args):
        """Exits the runtime context, closing the requests session."""
        self.session.close()
        self.session = None
        return False

    async def __aenter__(self):
        """Asynchronously enters a runtime context, initializing a new aiohttp session."""
        if not AIOHTTP_AVAILABLE:
            raise AioHttpError("You must install `aiohttp` to use async methods")

        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        """Asynchronously exits the runtime context, closing the aiohttp session."""
        await self.session.close()
        self.session = None
        return False

    def geocode(self, query, **kwargs):
        """Given a string to search for, return the list (array) of results from OpenCage's Geocoder.

        :param string query: String to search for

        :returns: Dict results
        :raises InvalidInputError: if the query string is not a unicode string
        :raises RateLimitExceededError: if you have exceeded the number of queries you can make.
        :                                  Exception says when you can try again
        :raises UnknownError: if something goes wrong with the OpenCage API

        """

        if self.session and isinstance(self.session, aiohttp.client.ClientSession):
            raise AioHttpError("Cannot use `geocode` in an async context, use `geocode_async`.")

        request = self._parse_request(query, kwargs)
        response = self._opencage_request(request)

        return floatify_latlng(response["results"])

    async def geocode_async(self, query, **kwargs):
        """Aync version of `geocode`.

        Given a string to search for, return the list (array) of results from OpenCage's Geocoder.

        :param string query: String to search for

        :returns: Dict results
        :raises InvalidInputError: if the query string is not a unicode string
        :raises RateLimitExceededError: if exceeded number of queries you can make. You can try again
        :raises UnknownError: if something goes wrong with the OpenCage API
        """

        if not AIOHTTP_AVAILABLE:
            raise AioHttpError("You must install `aiohttp` to use async methods.")

        if not self.session:
            raise AioHttpError("Async methods must be used inside an async context.")

        if not isinstance(self.session, aiohttp.client.ClientSession):
            raise AioHttpError("You must use `geocode_async` in an async context.")

        request = self._parse_request(query, kwargs)
        response = await self._opencage_async_request(request)

        return floatify_latlng(response["results"])

    async def _licenses_async(self, query, **kwargs):
        if not AIOHTTP_AVAILABLE:
            raise AioHttpError("You must install `aiohttp` to use async methods.")

        if not self.session:
            raise AioHttpError("Async methods must be used inside an async context.")

        if not isinstance(self.session, aiohttp.client.ClientSession):
            raise AioHttpError("You must use `geocode_async` in an async context.")

        request = self._parse_request(query, kwargs)
        response = await self._opencage_async_request(request)

        return response["licenses"]

    def reverse_geocode(self, lat, lng, **kwargs):
        """Given a latitude & longitude, return an address for that point from OpenCage's Geocoder.

        :param lat: Latitude
        :param lng: Longitude
        :return: Results from OpenCageData
        :rtype: dict
        :raises RateLimitExceededError: if you have exceeded the number of queries you can make.
        :                                  Exception says when you can try again
        :raises UnknownError: if something goes wrong with the OpenCage API
        """
        return self.geocode(_query_for_reverse_geocoding(lat, lng), **kwargs)

    async def reverse_geocode_async(self, lat, lng, **kwargs):
        """Aync version of `reverse_geocode`.

        Given a latitude & longitude, return an address for that point from OpenCage's Geocoder.

        :param lat: Latitude
        :param lng: Longitude
        :return: Results from OpenCageData
        :rtype: dict
        :raises RateLimitExceededError: if exceeded number of queries you can make. You can try again
        :raises UnknownError: if something goes wrong with the OpenCage API
        """
        return await self.geocode_async(_query_for_reverse_geocoding(lat, lng), **kwargs)

    async def licenses_async(self, lat, lng, **kwargs):
        """Get licenses."""
        return await self._licenses_async(_query_for_reverse_geocoding(lat, lng), **kwargs)

    @backoff.on_exception(
        backoff.expo, (UnknownError, requests.exceptions.RequestException), max_tries=5, max_time=backoff_max_time
    )
    def _opencage_request(self, params):
        if self.session:
            response = self.session.get(self.url, params=params, headers=self._opencage_headers("aiohttp"))
        else:
            response = safe_requests.get(
                self.url, params=params, headers=self._opencage_headers("requests"), timeout=DEFAULT_TIMEOUT
            )

        try:
            response_json = response.json()
        except ValueError as excinfo:
            raise UnknownError("Non-JSON result from server") from excinfo

        if response.status_code == 401:
            raise NotAuthorizedError()

        if response.status_code == 403:
            raise ForbiddenError()

        if response.status_code in (402, 429):
            # Rate limit exceeded
            reset_time = datetime.fromtimestamp(response.json()["rate"]["reset"], tz=timezone.utc)

            raise RateLimitExceededError(reset_to=int(response.json()["rate"]["limit"]), reset_time=reset_time)

        if response.status_code == 500:
            raise UnknownError("500 status code from API")

        if "results" not in response_json:
            raise UnknownError("JSON from API doesn't have a 'results' key")

        return response_json

    def _opencage_headers(self, client):
        if client == "requests":
            client_version = requests.__version__
        elif client == "aiohttp":
            client_version = aiohttp.__version__

        return {
            "User-Agent": (
                "opencage-python/2.4.0 Python/"
                f"{'.'.join(str(x) for x in sys.version_info[0:3])} "
                f"{client}/{client_version}"
            )
        }

    async def _opencage_async_request(self, params):
        try:
            async with self.session.get(self.url, params=params, ssl=self.sslcontext) as response:
                try:
                    response_json = await response.json()
                except ValueError as excinfo:
                    raise UnknownError("Non-JSON result from server") from excinfo

                if response.status == 401:
                    raise NotAuthorizedError()

                if response.status == 403:
                    raise ForbiddenError()

                if response.status in (402, 429):
                    # Rate limit exceeded

                    reset_time = datetime.fromtimestamp(response_json["rate"]["reset"], tz=timezone.utc)

                    raise RateLimitExceededError(reset_to=int(response_json["rate"]["limit"]), reset_time=reset_time)

                if response.status == 500:
                    raise UnknownError("500 status code from API")

                if "results" not in response_json:
                    raise UnknownError("JSON from API doesn't have a 'results' key")

                return response_json
        except aiohttp.ClientSSLError as exp:
            raise SSLError() from exp
        except aiohttp.ClientConnectorCertificateError as exp:
            raise SSLError() from exp

    def _parse_request(self, query, params):
        if not isinstance(query, str):
            raise InvalidInputError(bad_value=query)

        data = {"q": query, "key": self.key}
        data.update(params)  # Add user parameters
        return data


def _query_for_reverse_geocoding(lat, lng):
    """Given a lat & lng, what's the string search query.

    If the API changes, change this function. Only for internal use.
    """
    # have to do some stupid f/Decimal/str stuff to (a) ensure we get as much
    # decimal places as the user already specified and (b) to ensure we don't
    # get e-5 stuff

    return f"{Decimal(str(lat)):f},{Decimal(str(lng)):f}"


def float_if_float(float_string):
    """Given a float string, returns the float value.

    On value error returns the original string.
    """
    try:
        float_val = float(float_string)
        return float_val
    except ValueError:
        return float_string


def floatify_latlng(input_value):
    """Work around a JSON dict with string, not float, lat/lngs.

    Given anything (list/dict/etc) it will return that thing again, *but* any
    dict (at any level) that has only 2 elements lat & lng, will be replaced
    with the lat & lng turned into floats.

    If the API returns the lat/lng as strings, and not numbers, then this
    function will 'clean them up' to be floats.
    """
    if isinstance(input_value, collections.abc.Mapping):
        if len(input_value) == 2 and sorted(input_value.keys()) == ["lat", "lng"]:
            # This dict has only 2 keys 'lat' & 'lon'

            return {"lat": float_if_float(input_value["lat"]), "lng": float_if_float(input_value["lng"])}

        return {key: floatify_latlng(value) for key, value in input_value.items()}

    if isinstance(input_value, collections.abc.MutableSequence):
        return [floatify_latlng(x) for x in input_value]

    return input_value
