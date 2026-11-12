# navml: generated
"""Generated from ``calendar_window.nml``.

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
from navml.commands import CloseWindow    # calendar_window.nml:1
from navml.widgets.dialog.button import Button    # calendar_window.nml:2
from navml.widgets.dialog.commands import ChooseMonth, ChooseYear, GoToToday, NextMonth, NextYear, PreviousMonth, PreviousYear, SwapCalendars    # calendar_window.nml:3
from navml.widgets.dialog.date_button import CalendarView    # calendar_window.nml:4
from navml.widgets.menu.menu_item import MenuItem    # calendar_window.nml:5
from navml.widgets.menu.menu_line import MenuLine    # calendar_window.nml:6
from navml.widgets.menu.sub_menu import SubMenu    # calendar_window.nml:7
from navml.widgets.window import Window    # calendar_window.nml:8
from navigator.lib.config import country    # calendar_window.nml:9

__navml_component__ = "CalendarWindow"

__all__ = ["CalendarWindow"]


class CalendarWindow(Window, _Component):
    """Utilities > Calendar: Turbo Vision's ``TCalendarWindow`` (TVDEMO), not DOS

    Navigator's -- DN 1.51 had no calendar; a departure, asked for.

    A month on the desktop, one window at a time: the month and year between
    the arrows that turn it, the weekdays, six weeks with today marked.  It is
    navml's ``CalendarView``, the one a date line's ``▐↓▌`` drops, so it pages
    and picks a month or a year the same way; here it only shows, as TVDEMO's
    did.  *Go to current date* (Alt+D, or ``T`` in the month) brings today
    back under the cursor -- not TVDEMO's, asked for.  Under the weeks the
    day under the cursor is spelled in *Country support*'s date format, as a
    date line's drop-down spells it in the line's.
    Esc closes it.

    **The month can be in another calendar** (``navml.calendars``: Julian,
    Hebrew, Islamic, Persian, Indian national, Ethiopian, Coptic), paged and
    picked in its own months and years, the Gregorian day still spelled under
    them -- not TVDEMO's, whose month was Gregorian only; asked for with the
    Hebrew, Arabic, Chinese and Japanese catalogues.  Which one is *Calendar
    system*'s choice on the menu, else *Country support*'s (``[country]
    calendar``, the language's own by default).  *View* says what of it is shown
    beside the Gregorian (``[country] calendar_view`` by default): its month
    alone, the day spelled in it under the Gregorian month, its month with the
    Gregorian day spelled under, or the two months side by side, the calendar
    on the left and the Gregorian on the right, one day under both cursors.  ``C`` swaps the month between
    the calendar and the Gregorian (not beside each other, where both show).  Its month alone, or the two,
    spell nothing under them: the grids already say the day.
    """

    #: The document this class was generated from.
    __navml_source__ = "calendar_window.nml"

    #: T is the month's own key too; here it also works while the button has
    #: the keyboard, which the month's table is not on the way out from.
    keys = {    # calendar_window.nml:52
        'escape': CloseWindow,    # calendar_window.nml:53
        't': GoToToday,    # calendar_window.nml:54
        'shift+t': GoToToday,    # calendar_window.nml:55
        'c': SwapCalendars,    # calendar_window.nml:56
        'shift+c': SwapCalendars,    # calendar_window.nml:57
    }

    #: The calendar the menu chose, a key of ``navml.calendars.SYSTEMS``;
    #: empty, *Country support*'s.
    chosen: str = _reactive('')    # calendar_window.nml:41

    #: What of it is shown, a ``CountryData.VIEWS`` key; empty, *Country
    #: support*'s.
    display: str = _reactive('')    # calendar_window.nml:44

    #: *Selected calendar only* swapped by ``C`` to the Gregorian alone.
    swapped: bool = _reactive(False)    # calendar_window.nml:46

    #: Ids, annotated so the hand-written half completes them.
    month: CalendarView    # calendar_window.nml:70
    other: CalendarView    # calendar_window.nml:85
    today_button: Button    # calendar_window.nml:98
    calendar_menu: SubMenu    # calendar_window.nml:112
    system_menu: SubMenu    # calendar_window.nml:128
    view_menu: SubMenu    # calendar_window.nml:131

    #: The commands this component handles itself.
    async def on_go_to_today(self, event: _Any) -> bool:    # calendar_window.nml:61
        """``GoToToday``."""
        self.go_to_today()
        return True

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.month = CalendarView(parent=self)    # calendar_window.nml:69
        self.other = CalendarView(parent=self)    # calendar_window.nml:84
        self.today_button = Button(parent=self)    # calendar_window.nml:97
        self.calendar_menu = SubMenu(parent=self)    # calendar_window.nml:111
        _w1 = MenuItem(parent=self.calendar_menu)    # calendar_window.nml:114
        _w2 = MenuItem(parent=self.calendar_menu)    # calendar_window.nml:115
        _w3 = MenuItem(parent=self.calendar_menu)    # calendar_window.nml:116
        _w4 = MenuItem(parent=self.calendar_menu)    # calendar_window.nml:117
        _w5 = MenuLine(parent=self.calendar_menu)    # calendar_window.nml:118
        _w6 = MenuItem(parent=self.calendar_menu)    # calendar_window.nml:119
        _w7 = MenuItem(parent=self.calendar_menu)    # calendar_window.nml:120
        _w8 = MenuLine(parent=self.calendar_menu)    # calendar_window.nml:121
        _w9 = MenuItem(parent=self.calendar_menu)    # calendar_window.nml:122
        _w10 = MenuItem(parent=self.calendar_menu)    # calendar_window.nml:123
        _w11 = MenuLine(parent=self.calendar_menu)    # calendar_window.nml:124
        self.system_menu = SubMenu(parent=self.calendar_menu)    # calendar_window.nml:127
        self.view_menu = SubMenu(parent=self.calendar_menu)    # calendar_window.nml:130
        _w12 = MenuLine(parent=self.calendar_menu)    # calendar_window.nml:132
        _w13 = MenuItem(parent=self.calendar_menu)    # calendar_window.nml:133

        self.title = _bind(lambda _o: _tr('Calendar'), yielding=True)    # calendar_window.nml:38
        self.zoomable = False    # calendar_window.nml:47
        self.resizable = False    # calendar_window.nml:48

        self.month.x = 2    # calendar_window.nml:71
        self.month.y = 1    # calendar_window.nml:72
        self.month.width = 22    # calendar_window.nml:73
        self.month.height = _bind(    # calendar_window.nml:74
            lambda _o: 2 + self.rows() + self.spelled_rows()
        )
        self.month.compact = True    # calendar_window.nml:75
        self.month.can_focus = True    # calendar_window.nml:76
        self.month.first_weekday = _bind(lambda _o: country.first_weekday())    # calendar_window.nml:77
        self.month.system = _bind(    # calendar_window.nml:78
            lambda _o: 'gregorian' if self.gregorian_grid() else self.calendar_system()
        )
        self.month.date_format = _bind(    # calendar_window.nml:79
            lambda _o: '' if self.calendar_view() in ('only', 'both') else country.date_format()
        )
        self.month.label = _bind(    # calendar_window.nml:80
            lambda _o: self.calendar_system() if self.calendar_view() == 'gregorian_grid' else 'gregorian'
        )

        self.other.x = 27    # calendar_window.nml:86
        self.other.y = 1    # calendar_window.nml:87
        self.other.width = 22    # calendar_window.nml:88
        self.other.height = _bind(    # calendar_window.nml:89
            lambda _o: 2 + self.rows() + self.spelled_rows()
        )
        self.other.compact = True    # calendar_window.nml:90
        self.other.can_focus = True    # calendar_window.nml:91
        self.other.visible = _bind(lambda _o: self.both())    # calendar_window.nml:92
        self.other.first_weekday = _bind(lambda _o: country.first_weekday())    # calendar_window.nml:93
        self.other.system = 'gregorian'    # calendar_window.nml:94

        self.today_button.text = _bind(    # calendar_window.nml:99
            lambda _o: _tr('Go to current ~d~ate'),
            yielding=True,
        )
        self.today_button.x = 2    # calendar_window.nml:100
        self.today_button.y = _bind(    # calendar_window.nml:101
            lambda _o: 1 + 2 + self.rows() + self.spelled_rows() + 1
        )
        self.today_button.width = 23    # calendar_window.nml:102
        self.today_button.height = 2    # calendar_window.nml:103

        async def _on_click(event):    # calendar_window.nml:104
            self.go_to_today()
            return True
        self.today_button.on_click = _on_click

        self.calendar_menu.text = _bind(    # calendar_window.nml:111
            lambda _o: _tr('~C~alendar'),
            yielding=True,
        )
        self.calendar_menu.after = 'File'    # calendar_window.nml:111
        self.calendar_menu.tooltip = _bind(    # calendar_window.nml:113
            lambda _o: _tr('Move between months and years'),
            yielding=True,
        )

        _w1.text = _bind(lambda _o: _tr('~P~revious month'), yielding=True)    # calendar_window.nml:114
        _w1.command = PreviousMonth    # calendar_window.nml:114
        _w1.key = 'PgUp'    # calendar_window.nml:114

        _w2.text = _bind(lambda _o: _tr('~N~ext month'), yielding=True)    # calendar_window.nml:115
        _w2.command = NextMonth    # calendar_window.nml:115
        _w2.key = 'PgDn'    # calendar_window.nml:115

        _w3.text = _bind(lambda _o: _tr('P~r~evious year'), yielding=True)    # calendar_window.nml:116
        _w3.command = PreviousYear    # calendar_window.nml:116
        _w3.key = 'Ctrl-PgUp'    # calendar_window.nml:116

        _w4.text = _bind(lambda _o: _tr('Ne~x~t year'), yielding=True)    # calendar_window.nml:117
        _w4.command = NextYear    # calendar_window.nml:117
        _w4.key = 'Ctrl-PgDn'    # calendar_window.nml:117

        _w6.text = _bind(lambda _o: _tr('Choose ~m~onth...'), yielding=True)    # calendar_window.nml:119
        _w6.command = ChooseMonth    # calendar_window.nml:119
        _w6.key = 'M'    # calendar_window.nml:119

        _w7.text = _bind(lambda _o: _tr('Choose ~y~ear...'), yielding=True)    # calendar_window.nml:120
        _w7.command = ChooseYear    # calendar_window.nml:120
        _w7.key = 'Y'    # calendar_window.nml:120

        _w9.text = _bind(lambda _o: _tr('Go to current ~d~ate'), yielding=True)    # calendar_window.nml:122
        _w9.command = GoToToday    # calendar_window.nml:122
        _w9.key = 'T'    # calendar_window.nml:122

        _w10.text = _bind(lambda _o: _tr('S~w~ap calendars'), yielding=True)    # calendar_window.nml:123
        _w10.command = SwapCalendars    # calendar_window.nml:123
        _w10.key = 'C'    # calendar_window.nml:123

        self.system_menu.text = _bind(    # calendar_window.nml:127
            lambda _o: _tr('Calendar ~s~ystem'),
            yielding=True,
        )

        self.view_menu.text = _bind(    # calendar_window.nml:130
            lambda _o: _tr('Calendar ~v~iew'),
            yielding=True,
        )

        _w13.text = _bind(lambda _o: _tr('~C~lose'), yielding=True)    # calendar_window.nml:133
        _w13.command = CloseWindow    # calendar_window.nml:133
