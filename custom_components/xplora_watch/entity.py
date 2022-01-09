"""Entity Xplora® Watch."""

from typing import Any

class XploraSwitchEntity:
    def __init__(self, switch, name) -> None:
        self._switch = switch
        self._name = name

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the device."""
        return self._switch["id"]

    @property
    def name(self) -> str:
        """Return the name of the device."""
        return self._name

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return supported attributes."""
        days = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa']
        weekRepeat = self._switch['weekRepeat']
        weekDays = []
        for day in range(len(weekRepeat)):
            if weekRepeat[day] == "1":
                weekDays.append(days[day])
        return { "Day(s)": ', '.join(weekDays) }
