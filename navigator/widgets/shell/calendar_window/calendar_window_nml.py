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

from navkit.events import Event as _Event
from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navml.commands import CloseWindow    # calendar_window.nml:1
from navml.widgets.dialog.button import Button    # calendar_window.nml:2
from navml.widgets.dialog.commands import ChooseMonth, ChooseYear, GoToToday, NextMonth, NextYear, PreviousMonth, PreviousYear    # calendar_window.nml:3
from navml.widgets.dialog.date_button import CalendarView    # calendar_window.nml:4
from navml.widgets.menu.menu_item import MenuItem    # calendar_window.nml:5
from navml.widgets.menu.menu_line import MenuLine    # calendar_window.nml:6
from navml.widgets.menu.sub_menu import SubMenu    # calendar_window.nml:7
from navml.widgets.window import Window    # calendar_window.nml:8

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
    date line's drop-down spells it in the line's (bound in ``__init__``).
    Esc closes it.
    """

    #: The document this class was generated from.
    __navml_source__ = "calendar_window.nml"

    #: T is the month's own key too; here it also works while the button has
    #: the keyboard, which the month's table is not on the way out from.
    keys = {    # calendar_window.nml:29
        'escape': CloseWindow,    # calendar_window.nml:30
        't': GoToToday,    # calendar_window.nml:31
        'shift+t': GoToToday,    # calendar_window.nml:32
    }

    #: Ids, annotated so the hand-written half completes them.
    month: CalendarView    # calendar_window.nml:35
    today_button: Button    # calendar_window.nml:43
    calendar_menu: SubMenu    # calendar_window.nml:56

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_today_button_click(self, event: _Event) -> bool:    # calendar_window.nml:43
        """``today_button`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.month = CalendarView(parent=self)    # calendar_window.nml:34
        self.today_button = Button(parent=self)    # calendar_window.nml:42
        self.calendar_menu = SubMenu(parent=self)    # calendar_window.nml:55
        _w1 = MenuItem(parent=self.calendar_menu)    # calendar_window.nml:60
        _w2 = MenuItem(parent=self.calendar_menu)    # calendar_window.nml:64
        _w3 = MenuItem(parent=self.calendar_menu)    # calendar_window.nml:68
        _w4 = MenuItem(parent=self.calendar_menu)    # calendar_window.nml:72
        _w5 = MenuLine(parent=self.calendar_menu)    # calendar_window.nml:76
        _w6 = MenuItem(parent=self.calendar_menu)    # calendar_window.nml:77
        _w7 = MenuItem(parent=self.calendar_menu)    # calendar_window.nml:81
        _w8 = MenuLine(parent=self.calendar_menu)    # calendar_window.nml:85
        _w9 = MenuItem(parent=self.calendar_menu)    # calendar_window.nml:86
        _w10 = MenuLine(parent=self.calendar_menu)    # calendar_window.nml:90
        _w11 = MenuItem(parent=self.calendar_menu)    # calendar_window.nml:91

        self.title = _bind(lambda _o: _tr('Calendar'), yielding=True)    # calendar_window.nml:23
        self.zoomable = False    # calendar_window.nml:24
        self.resizable = False    # calendar_window.nml:25

        self.month.x = 2    # calendar_window.nml:36
        self.month.y = 1    # calendar_window.nml:37
        self.month.width = 22    # calendar_window.nml:38
        self.month.height = 9    # calendar_window.nml:39
        self.month.can_focus = True    # calendar_window.nml:40

        self.today_button.text = _bind(    # calendar_window.nml:44
            lambda _o: _tr('Go to current ~d~ate'),
            yielding=True,
        )
        self.today_button.x = 2    # calendar_window.nml:45
        self.today_button.y = 11    # calendar_window.nml:46
        self.today_button.width = 23    # calendar_window.nml:47
        self.today_button.height = 2    # calendar_window.nml:48
        self.today_button.on_click = self.on_today_button_click    # calendar_window.nml:43

        self.calendar_menu.text = _bind(    # calendar_window.nml:57
            lambda _o: _tr('~C~alendar'),
            yielding=True,
        )
        self.calendar_menu.tooltip = _bind(    # calendar_window.nml:58
            lambda _o: _tr('Move between months and years'),
            yielding=True,
        )
        self.calendar_menu.after = 'File'    # calendar_window.nml:59

        _w1.text = _bind(lambda _o: _tr('~P~revious month'), yielding=True)    # calendar_window.nml:61
        _w1.command = PreviousMonth    # calendar_window.nml:62
        _w1.key = 'PgUp'    # calendar_window.nml:63

        _w2.text = _bind(lambda _o: _tr('~N~ext month'), yielding=True)    # calendar_window.nml:65
        _w2.command = NextMonth    # calendar_window.nml:66
        _w2.key = 'PgDn'    # calendar_window.nml:67

        _w3.text = _bind(lambda _o: _tr('P~r~evious year'), yielding=True)    # calendar_window.nml:69
        _w3.command = PreviousYear    # calendar_window.nml:70
        _w3.key = 'Ctrl-PgUp'    # calendar_window.nml:71

        _w4.text = _bind(lambda _o: _tr('Ne~x~t year'), yielding=True)    # calendar_window.nml:73
        _w4.command = NextYear    # calendar_window.nml:74
        _w4.key = 'Ctrl-PgDn'    # calendar_window.nml:75

        _w6.text = _bind(lambda _o: _tr('Choose ~m~onth...'), yielding=True)    # calendar_window.nml:78
        _w6.command = ChooseMonth    # calendar_window.nml:79
        _w6.key = 'M'    # calendar_window.nml:80

        _w7.text = _bind(lambda _o: _tr('Choose ~y~ear...'), yielding=True)    # calendar_window.nml:82
        _w7.command = ChooseYear    # calendar_window.nml:83
        _w7.key = 'Y'    # calendar_window.nml:84

        _w9.text = _bind(lambda _o: _tr('Go to current ~d~ate'), yielding=True)    # calendar_window.nml:87
        _w9.command = GoToToday    # calendar_window.nml:88
        _w9.key = 'T'    # calendar_window.nml:89

        _w11.text = _bind(lambda _o: _tr('~C~lose'), yielding=True)    # calendar_window.nml:92
        _w11.command = CloseWindow    # calendar_window.nml:93
