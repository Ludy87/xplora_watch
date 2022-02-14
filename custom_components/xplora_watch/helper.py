"""HelperClasses Xplora® Watch."""
from __future__ import annotations

from datetime import datetime

from homeassistant.core import HomeAssistant

class XploraUpdateTime:
    def __init__(self, scan_interval, start_time) -> None:
        self._first = True
        self._start_time = start_time
        self._scan_interval = scan_interval

    def _update_timer(self) -> int:
        return (int(datetime.timestamp(datetime.now()) - self._start_time) > self._scan_interval.total_seconds())


class XploraDevice(XploraUpdateTime):
    """Representation of a Xplora® device."""

    hass: HomeAssistant

    def __init__(self, scan_interval, start_time) -> None:
        """Set up the MySensors device."""
        super().__init__(scan_interval, start_time)

    @property
    def unique_id(self) -> str:
        """Return a unique ID for use in home assistant."""
        return "{self.gateway_id}-{self.node_id}-{self.child_id}-{self.value_type}"
