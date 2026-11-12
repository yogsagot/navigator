"""What OK means in *Country support*: the ``[country]`` section's new values."""

from __future__ import annotations

import time
from typing import Any

from navkit.i18n import tr
from navml.calendars import SYSTEMS, plain

from navigator.lib.config import country
from navigator.settings import CountryData
from navigator.widgets.setup.settings_page import SettingsPage
from navigator.widgets.shell.calendar_window.calendar_window import view_captions

#: The *Time* buttons in DN's order, 12 hours first.
HOURS = ("12h", "24h")


def calendar_names() -> dict[str, str]:
    """*Calendar system*'s choices by their captions, in the setting's order."""
    return {tr("Language's own") if key == "auto" else SYSTEMS[key].name(): key for key in CountryData.CALENDARS}


class CountryPage(SettingsPage):
    """``[country]``: the order a date is written in, or a format of one's
    own, 12 or 24 hours, the day a calendar's week starts on, and the
    calendar Utilities > Calendar shows its month in, and how."""

    def __init__(self, **kwargs: Any) -> None:
        # *Date format* and *First day* say what they edit (``key:``); the
        # rest are read here: *Time* lists 12 hours first, as DN did, where
        # the setting's choices put 24 first.
        super().__init__(**kwargs)
        self.time_format.value = HOURS.index(self.section.time_format)
        self.time_format.tooltip = self.section.tooltip("time_format")
        self.custom_date.value = self.section.custom_date
        self.custom_date.tooltip = self.section.tooltip("custom_date")
        self.calendars = calendar_names()
        self.calendar.choices = list(self.calendars)
        self.calendar.value = next(name for name, key in self.calendars.items() if key == self.section.calendar)
        self.calendar.tooltip = self.section.tooltip("calendar")
        self.views = {plain(caption): key for key, caption in view_captions().items()}
        self.calendar_view.choices = list(self.views)
        self.calendar_view.value = next(name for name, key in self.views.items() if key == self.section.calendar_view)
        self.calendar_view.tooltip = self.section.tooltip("calendar_view")

    def chosen_format(self) -> str:
        """The date format the buttons and the line say, before OK."""
        choice = CountryData.DATES[self.date_format.value]
        return self.custom_date.value.strip() if choice == "custom" else country.PRESETS[choice]

    def sample(self) -> str:
        """Now, as a panel's *Date* column would show it with these choices."""
        return country.stamp_in(time.time(), self.chosen_format(), HOURS[self.time_format.value] == "12h")

    def example_text(self) -> str:
        """The line under the choices: :meth:`sample`, said as an example."""
        return tr("Example: {stamp}").format(stamp=self.sample())

    def accept(self) -> dict[str, Any]:
        return {
            **super().accept(),
            # Kept whichever order is chosen, so *Custom* comes back to it.
            "custom_date": self.custom_date.value.strip() or self.section.custom_date,
            "time_format": HOURS[self.time_format.value],
            "calendar": self.calendars.get(self.calendar.value, self.section.calendar),
            "calendar_view": self.views.get(self.calendar_view.value, self.section.calendar_view),
        }
