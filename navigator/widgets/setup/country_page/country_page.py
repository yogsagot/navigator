"""What OK means in *Country support*: the ``[country]`` section's new values."""

from __future__ import annotations

import time
from typing import Any

from navkit.i18n import tr
from navkit.reactive import bind
from navkit.widget import Widget

from navigator.lib.config import country
from navigator.settings import SETTINGS, CountryData

#: The *Time* buttons in DN's order, 12 hours first.
HOURS = ("12h", "24h")


class CountryPage(Widget):
    """``[country]``: the order a date is written in, or a format of one's
    own, 12 or 24 hours, and the day a calendar's week starts on."""

    def __init__(self, section: CountryData | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.section = section or SETTINGS.country
        self.date_format.value = CountryData.DATES.index(self.section.date_format)
        self.date_format.tooltip = self.section.tooltip("date_format")
        self.time_format.value = HOURS.index(self.section.time_format)
        self.time_format.tooltip = self.section.tooltip("time_format")
        self.custom_date.value = self.section.custom_date
        self.custom_date.tooltip = self.section.tooltip("custom_date")
        self.first_day.value = CountryData.WEEKS.index(self.section.first_day)
        self.first_day.tooltip = self.section.tooltip("first_day")
        self.example.text = bind(lambda w: tr("Example: {stamp}").format(stamp=self.sample()))

    def chosen_format(self) -> str:
        """The date format the buttons and the line say, before OK."""
        choice = CountryData.DATES[self.date_format.value]
        return self.custom_date.value.strip() if choice == "custom" else country.PRESETS[choice]

    def sample(self) -> str:
        """Now, as a panel's *Date* column would show it with these choices."""
        return country.stamp_in(time.time(), self.chosen_format(), HOURS[self.time_format.value] == "12h")

    def accept(self) -> dict[str, Any]:
        return {
            "date_format": CountryData.DATES[self.date_format.value],
            # Kept whichever order is chosen, so *Custom* comes back to it.
            "custom_date": self.custom_date.value.strip() or self.section.custom_date,
            "time_format": HOURS[self.time_format.value],
            "first_day": CountryData.WEEKS[self.first_day.value],
        }
