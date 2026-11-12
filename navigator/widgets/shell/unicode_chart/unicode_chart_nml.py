# navml: generated
"""Generated from ``unicode_chart.nml``.

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
from navml.widgets.dialog.button import Button    # unicode_chart.nml:1
from navml.widgets.dialog.dialog import Dialog    # unicode_chart.nml:2
from navml.widgets.dialog.history import History    # unicode_chart.nml:3
from navml.widgets.dialog.input_line import InputLine    # unicode_chart.nml:4
from navml.widgets.dialog.label import Label    # unicode_chart.nml:5
from navml.widgets.dialog.list_viewer import ListViewer    # unicode_chart.nml:6
from navml.widgets.dialog.radio_buttons import RadioButtons    # unicode_chart.nml:7
from navml.widgets.dialog.static_text import StaticText    # unicode_chart.nml:8
from navigator.widgets.shell.unicode_grid import UnicodeGrid    # unicode_chart.nml:9

__navml_component__ = "UnicodeChart"

__all__ = ["UnicodeChart"]


class UnicodeChart(Dialog, _Component):
    """Utilities > *Character table* (Ctrl+B) and the editor's Ctrl+P on a

    Unicode terminal: every character, found by name or by group.  Not DOS
    Navigator's, whose *ASCII Chart* (``AsciiChart``) charted code page 437 and
    is still what the ASCII glyph tier gets; a departure, by request.

    The search line across the top; down the left, how to group -- blocks,
    general categories, and in the Nerd tier the Nerd Font sets -- over the
    groups, and under them a line that filters them by name; the grid of the group chosen on the right; the character under its
    cursor described across the bottom, beside *Insert*, *Copy* and *Cancel*.
    Sized to the screen as *Choose Directory* is, never smaller than an
    80 by 25 screen allows, every control placed against the dialog's edges.
    ``Dialog``'s own row of buttons and its message are not this layout, and
    the hand-written half hides them.
    """

    #: The document this class was generated from.
    __navml_source__ = "unicode_chart.nml"

    #: Ids, annotated so the hand-written half completes them.
    search_caption: Label    # unicode_chart.nml:33
    search: InputLine    # unicode_chart.nml:41
    history: History    # unicode_chart.nml:47
    grouping: RadioButtons    # unicode_chart.nml:59
    groups: ListViewer    # unicode_chart.nml:66
    filter: InputLine    # unicode_chart.nml:74
    clear_filter: Button    # unicode_chart.nml:82
    grid: UnicodeGrid    # unicode_chart.nml:91
    info: StaticText    # unicode_chart.nml:101
    insert_button: Button    # unicode_chart.nml:110
    copy_button: Button    # unicode_chart.nml:122
    abandon: Button    # unicode_chart.nml:132

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_abandon_click(self, event: _Event) -> bool:    # unicode_chart.nml:132
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.search_caption = Label(parent=self)    # unicode_chart.nml:32
        self.search = InputLine(parent=self)    # unicode_chart.nml:40
        self.history = History(parent=self)    # unicode_chart.nml:46
        self.grouping = RadioButtons(parent=self)    # unicode_chart.nml:58
        self.groups = ListViewer(parent=self)    # unicode_chart.nml:65
        self.filter = InputLine(parent=self)    # unicode_chart.nml:73
        self.clear_filter = Button(parent=self)    # unicode_chart.nml:81
        self.grid = UnicodeGrid(parent=self)    # unicode_chart.nml:90
        self.info = StaticText(parent=self)    # unicode_chart.nml:100
        self.insert_button = Button(parent=self)    # unicode_chart.nml:109
        self.copy_button = Button(parent=self)    # unicode_chart.nml:121
        self.abandon = Button(parent=self)    # unicode_chart.nml:131

        self.modal_width = _bind(    # unicode_chart.nml:25
            lambda _o: max(76, min(_o.parent.width - 4, 120)) if _o.parent is not None else 76
        )
        self.modal_height = _bind(    # unicode_chart.nml:26
            lambda _o: max(22, min(_o.parent.height - 2, 50)) if _o.parent is not None else 22
        )
        self.title = _bind(lambda _o: _tr('Character Table'), yielding=True)    # unicode_chart.nml:27
        self.buttons = 'none'    # unicode_chart.nml:28
        self.buttons_row = _bind(    # unicode_chart.nml:30
            lambda _o: (self.insert_button, self.copy_button, self.abandon)
        )

        self.search_caption.x = 2    # unicode_chart.nml:34
        self.search_caption.y = 2    # unicode_chart.nml:35
        self.search_caption.width = 8    # unicode_chart.nml:36
        self.search_caption.text = _bind(    # unicode_chart.nml:37
            lambda _o: _tr('~S~earch'),
            yielding=True,
        )
        self.search_caption.link = _bind(lambda _o: self.search)    # unicode_chart.nml:38

        self.search.x = 10    # unicode_chart.nml:42
        self.search.y = 2    # unicode_chart.nml:43
        self.search.width = _bind(lambda _o: max(1, _o.parent.width - 16))    # unicode_chart.nml:44

        self.history.link = _bind(lambda _o: self.search)    # unicode_chart.nml:48
        self.history.history_id = 'charsearch'    # unicode_chart.nml:49
        self.history.y = 2    # unicode_chart.nml:50
        self.history.width = 3    # unicode_chart.nml:51
        self.history.height = 1    # unicode_chart.nml:52
        self.history.x = _bind(    # unicode_chart.nml:54
            lambda _o: max(0, _o.parent.width - 2 - _o.width)
        )

        self.grouping.x = 2    # unicode_chart.nml:60
        self.grouping.y = 4    # unicode_chart.nml:61
        self.grouping.width = 24    # unicode_chart.nml:62
        self.grouping.height = _bind(lambda _o: max(1, len(_o.items)))    # unicode_chart.nml:63

        self.groups.x = 2    # unicode_chart.nml:67
        self.groups.y = _bind(lambda _o: 5 + self.grouping.height)    # unicode_chart.nml:68
        self.groups.width = 24    # unicode_chart.nml:69
        self.groups.height = _bind(    # unicode_chart.nml:70
            lambda _o: max(3, _o.parent.height - 11 - self.grouping.height)
        )

        self.filter.x = 2    # unicode_chart.nml:75
        self.filter.width = 20    # unicode_chart.nml:76
        self.filter.y = _bind(lambda _o: self.groups.y + self.groups.height)    # unicode_chart.nml:78

        self.clear_filter.flat = True    # unicode_chart.nml:83
        self.clear_filter.x = 23    # unicode_chart.nml:84
        self.clear_filter.y = _bind(lambda _o: self.filter.y)    # unicode_chart.nml:85
        self.clear_filter.width = 3    # unicode_chart.nml:86
        self.clear_filter.height = 1    # unicode_chart.nml:87

        async def _on_click(event):    # unicode_chart.nml:88
            self.clear_filter_line()
            return True
        self.clear_filter.on_click = _on_click

        self.grid.x = 27    # unicode_chart.nml:92
        self.grid.y = 4    # unicode_chart.nml:93
        self.grid.width = _bind(lambda _o: max(4, _o.parent.width - 29))    # unicode_chart.nml:94
        self.grid.height = _bind(lambda _o: max(3, _o.parent.height - 9))    # unicode_chart.nml:95

        async def _on_chosen(event):    # unicode_chart.nml:96
            self.take()
            return True
        self.grid.on_chosen = _on_chosen

        self.info.name = 'info'    # unicode_chart.nml:102
        self.info.height = 2    # unicode_chart.nml:103
        self.info.x = 2    # unicode_chart.nml:105
        self.info.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # unicode_chart.nml:106
        self.info.y = _bind(    # unicode_chart.nml:107
            lambda _o: max(0, _o.parent.height - 3 - _o.height)
        )

        self.insert_button.text = _bind(    # unicode_chart.nml:111
            lambda _o: _tr('~I~nsert'),
            yielding=True,
        )
        self.insert_button.default = True    # unicode_chart.nml:112
        self.insert_button.width = 12    # unicode_chart.nml:113
        self.insert_button.height = 2    # unicode_chart.nml:114
        self.insert_button.x = _bind(    # unicode_chart.nml:116
            lambda _o: max(0, _o.parent.width - 29 - _o.width)
        )
        self.insert_button.y = _bind(    # unicode_chart.nml:117
            lambda _o: max(0, _o.parent.height - 1 - _o.height)
        )

        async def _on_click(event):    # unicode_chart.nml:118
            self.take()
            return True
        self.insert_button.on_click = _on_click

        self.copy_button.text = _bind(lambda _o: _tr('Co~p~y'), yielding=True)    # unicode_chart.nml:123
        self.copy_button.width = 12    # unicode_chart.nml:124
        self.copy_button.height = 2    # unicode_chart.nml:125
        self.copy_button.x = _bind(    # unicode_chart.nml:127
            lambda _o: max(0, _o.parent.width - 16 - _o.width)
        )
        self.copy_button.y = _bind(    # unicode_chart.nml:128
            lambda _o: max(0, _o.parent.height - 1 - _o.height)
        )

        async def _on_click(event):    # unicode_chart.nml:129
            self.copy_out()
            return True
        self.copy_button.on_click = _on_click

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # unicode_chart.nml:133
        self.abandon.width = 12    # unicode_chart.nml:134
        self.abandon.height = 2    # unicode_chart.nml:135
        self.abandon.x = _bind(    # unicode_chart.nml:137
            lambda _o: max(0, _o.parent.width - 3 - _o.width)
        )
        self.abandon.y = _bind(    # unicode_chart.nml:138
            lambda _o: max(0, _o.parent.height - 1 - _o.height)
        )
        self.abandon.on_click = self.on_abandon_click    # unicode_chart.nml:132
