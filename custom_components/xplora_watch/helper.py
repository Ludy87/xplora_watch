"""HelperClasses Xplora® Watch."""
from __future__ import annotations

from datetime import datetime
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.helpers.restore_state import RestoreEntity


class XploraUpdateTime:
    def __init__(self, scan_interval, start_time) -> None:
        self._first = True
        self._start_time = start_time
        self._scan_interval = scan_interval

    def _update_timer(self) -> int:
        return (int(datetime.timestamp(datetime.now()) - self._start_time) > self._scan_interval.total_seconds())


class XploraDevice(XploraUpdateTime, TrackerEntity, RestoreEntity):
    """Representation of a Xplora® device."""
    def __init__(self, scan_interval, start_time) -> None:
        """Set up the Xplora® device."""
        super().__init__(scan_interval, start_time)
