# navml: generated
"""Generated from ``country_page.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind
from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component
from navml.widgets.dialog.choice_field import ChoiceField    # country_page.nml:1
from navml.widgets.dialog.field import Field    # country_page.nml:2
from navml.widgets.dialog.label import Label    # country_page.nml:3
from navml.widgets.dialog.radio_buttons import RadioButtons    # country_page.nml:4
from navml.widgets.dialog.static_text import StaticText    # country_page.nml:5

__navml_component__ = "CountryPage"

__all__ = ["CountryPage"]


class CountryPage(_Component):
    """Options > Configuration > Country support: DOS Navigator's

    ``dlgCountrySetup``, *Country information* (``[country]``, ``CountryData``).

    DN's *Date format* and *Time* where it had them, the date's three orders
    each with its usual separator and a fourth, *Custom*, whose ``strftime``
    format takes the line under them -- a departure, asked for, in place of
    DN's *Date separator* and *Time separator* lines.  The thousands, decimal
    and currency boxes and the uppercase table are left out: nothing here
    writes money, and case is Unicode's.  *Example* is not DN's: the stamp a
    panel's *Date* column would show now, following the choices as they are
    made.  Help is left out, having nothing to show yet.
    """

    #: The document this class was generated from.
    __navml_source__ = "country_page.nml"

    #: The caption on its tab, which *Settings* gives it.
    title: str = _reactive('')    # country_page.nml:20

    #: Ids, annotated so the hand-written half completes them.
    date_caption: Label    # country_page.nml:23
    date_format: RadioButtons    # country_page.nml:32
    time_caption: Label    # country_page.nml:40
    time_format: RadioButtons    # country_page.nml:49
    week_caption: Label    # country_page.nml:58
    first_day: RadioButtons    # country_page.nml:67
    calendar: ChoiceField    # country_page.nml:77
    calendar_view: ChoiceField    # country_page.nml:89
    custom_date: Field    # country_page.nml:98
    custom_hint: StaticText    # country_page.nml:107
    example: StaticText    # country_page.nml:118

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.date_caption = Label(parent=self)    # country_page.nml:22
        self.date_format = RadioButtons(parent=self)    # country_page.nml:31
        self.time_caption = Label(parent=self)    # country_page.nml:39
        self.time_format = RadioButtons(parent=self)    # country_page.nml:48
        self.week_caption = Label(parent=self)    # country_page.nml:57
        self.first_day = RadioButtons(parent=self)    # country_page.nml:66
        self.calendar = ChoiceField(parent=self)    # country_page.nml:76
        self.calendar_view = ChoiceField(parent=self)    # country_page.nml:88
        self.custom_date = Field(parent=self)    # country_page.nml:97
        self.custom_hint = StaticText(parent=self)    # country_page.nml:106
        self.example = StaticText(parent=self)    # country_page.nml:117

        self.date_caption.x = 3    # country_page.nml:24
        self.date_caption.y = 1    # country_page.nml:25
        self.date_caption.width = 14    # country_page.nml:26
        self.date_caption.height = 1    # country_page.nml:27
        self.date_caption.text = _bind(    # country_page.nml:28
            lambda _o: _tr('~D~ate format'),
            yielding=True,
        )
        self.date_caption.link = _bind(lambda _o: self.date_format)    # country_page.nml:29

        self.date_format.x = 3    # country_page.nml:33
        self.date_format.y = 2    # country_page.nml:34
        self.date_format.width = 34    # country_page.nml:35
        self.date_format.height = 4    # country_page.nml:36
        self.date_format.items = _bind(    # country_page.nml:37
            lambda _o: [_tr('~E~uropean  DD-MM-YYYY'), _tr('~U~S        MM/DD/YYYY'), _tr('~I~SO       YYYY-MM-DD'), _tr('~C~ustom')],
            yielding=True,
        )

        self.time_caption.x = 40    # country_page.nml:41
        self.time_caption.y = 1    # country_page.nml:42
        self.time_caption.width = 8    # country_page.nml:43
        self.time_caption.height = 1    # country_page.nml:44
        self.time_caption.text = _bind(lambda _o: _tr('~T~ime'), yielding=True)    # country_page.nml:45
        self.time_caption.link = _bind(lambda _o: self.time_format)    # country_page.nml:46

        self.time_format.x = 40    # country_page.nml:50
        self.time_format.y = 2    # country_page.nml:51
        self.time_format.width = 20    # country_page.nml:52
        self.time_format.height = 2    # country_page.nml:53
        self.time_format.items = _bind(    # country_page.nml:54
            lambda _o: [_tr('~1~2 hour'), _tr('~2~4 hour')],
            yielding=True,
        )

        self.week_caption.x = 40    # country_page.nml:59
        self.week_caption.y = 4    # country_page.nml:60
        self.week_caption.width = 14    # country_page.nml:61
        self.week_caption.height = 1    # country_page.nml:62
        self.week_caption.text = _bind(    # country_page.nml:63
            lambda _o: _tr('~W~eek starts'),
            yielding=True,
        )
        self.week_caption.link = _bind(lambda _o: self.first_day)    # country_page.nml:64

        self.first_day.x = 40    # country_page.nml:68
        self.first_day.y = 5    # country_page.nml:69
        self.first_day.width = 20    # country_page.nml:70
        self.first_day.height = 3    # country_page.nml:71
        self.first_day.items = _bind(    # country_page.nml:72
            lambda _o: [_tr('~M~onday'), _tr('~S~unday'), _tr('S~a~turday')],
            yielding=True,
        )

        self.calendar.x = 3    # country_page.nml:78
        self.calendar.y = 8    # country_page.nml:79
        self.calendar.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # country_page.nml:80
        self.calendar.height = 1    # country_page.nml:81
        self.calendar.label_text = _bind(    # country_page.nml:82
            lambda _o: _tr('Ca~l~endar system'),
            yielding=True,
        )
        self.calendar.label_width = 18    # country_page.nml:85

        self.calendar_view.x = 3    # country_page.nml:90
        self.calendar_view.y = 9    # country_page.nml:91
        self.calendar_view.width = _bind(    # country_page.nml:92
            lambda _o: max(0, _o.parent.width - 6)
        )
        self.calendar_view.height = 1    # country_page.nml:93
        self.calendar_view.label_text = _bind(    # country_page.nml:94
            lambda _o: _tr('Calendar ~v~iew'),
            yielding=True,
        )
        self.calendar_view.label_width = 18    # country_page.nml:95

        self.custom_date.x = 3    # country_page.nml:99
        self.custom_date.y = 10    # country_page.nml:100
        self.custom_date.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # country_page.nml:101
        self.custom_date.height = 1    # country_page.nml:102
        self.custom_date.label_text = _bind(    # country_page.nml:103
            lambda _o: _tr('Custom ~f~ormat'),
            yielding=True,
        )
        self.custom_date.label_width = 18    # country_page.nml:104

        self.custom_hint.x = 3    # country_page.nml:108
        self.custom_hint.y = 11    # country_page.nml:109
        self.custom_hint.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # country_page.nml:110
        self.custom_hint.height = 3    # country_page.nml:113
        self.custom_hint.wrap = True    # country_page.nml:114
        self.custom_hint.text = _bind(    # country_page.nml:115
            lambda _o: _tr("strftime's directives: %d day, %m month, %y or %Y year,\n%b or %B the month's name, %a or %A the weekday's"),
            yielding=True,
        )

        self.example.x = 3    # country_page.nml:119
        self.example.y = 14    # country_page.nml:120
        self.example.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # country_page.nml:121
        self.example.height = 1    # country_page.nml:122
