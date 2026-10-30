# navml: generated
"""The merged surface of ``navigator.widgets.setup.country_page.country_page``."""

from typing import Any as _Any

from navml.component import Component as _Component
from navml.widgets.dialog.choice_field import ChoiceField
from navml.widgets.dialog.field import Field
from navml.widgets.dialog.label import Label
from navml.widgets.dialog.radio_buttons import RadioButtons
from navml.widgets.dialog.static_text import StaticText

import time
from typing import Any
from navkit.i18n import tr
from navkit.reactive import bind
from navkit.widget import Widget
from navml.calendars import SYSTEMS, plain
from navigator.lib.config import country
from navigator.settings import SETTINGS, CountryData
from navigator.widgets.shell.calendar_window.calendar_window import view_captions


class CountryPage(_Component):
    title: str
    date_caption: Label
    date_format: RadioButtons
    time_caption: Label
    time_format: RadioButtons
    week_caption: Label
    first_day: RadioButtons
    calendar: ChoiceField
    calendar_view: ChoiceField
    custom_date: Field
    custom_hint: StaticText
    example: StaticText
    def __init__(self, section: CountryData | None = ..., **kwargs: Any) -> None: ...
    def chosen_format(self) -> str: ...
    def sample(self) -> str: ...
    def accept(self) -> dict[str, Any]: ...
