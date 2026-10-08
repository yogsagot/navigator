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

from navml.component import Component as _Component
from navml.commands import CloseWindow    # calendar_window.nml:1
from navml.widgets.dialog.button import Button    # calendar_window.nml:2
from navml.widgets.dialog.date_button import CalendarView    # calendar_window.nml:3
from navml.widgets.window import Window    # calendar_window.nml:4

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
    back under the cursor -- not TVDEMO's, asked for.  Esc closes it.
    """

    #: The document this class was generated from.
    __navml_source__ = "calendar_window.nml"

    #: The keys this component binds, read through key_table().
    keys = {    # calendar_window.nml:20
        'escape': CloseWindow,    # calendar_window.nml:21
    }

    #: Ids, annotated so the hand-written half completes them.
    month: CalendarView    # calendar_window.nml:24
    today_button: Button    # calendar_window.nml:32

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_today_button_click(self, event: _Event) -> bool:    # calendar_window.nml:32
        """``today_button`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.month = CalendarView(parent=self)    # calendar_window.nml:23
        self.today_button = Button(parent=self)    # calendar_window.nml:31

        self.title = 'Calendar'    # calendar_window.nml:16
        self.zoomable = False    # calendar_window.nml:17
        self.resizable = False    # calendar_window.nml:18

        self.month.x = 2    # calendar_window.nml:25
        self.month.y = 1    # calendar_window.nml:26
        self.month.width = 22    # calendar_window.nml:27
        self.month.height = 8    # calendar_window.nml:28
        self.month.can_focus = True    # calendar_window.nml:29

        self.today_button.text = 'Go to current ~d~ate'    # calendar_window.nml:33
        self.today_button.x = 2    # calendar_window.nml:34
        self.today_button.y = 10    # calendar_window.nml:35
        self.today_button.width = 23    # calendar_window.nml:36
        self.today_button.height = 2    # calendar_window.nml:37
        self.today_button.on_click = self.on_today_button_click    # calendar_window.nml:32
