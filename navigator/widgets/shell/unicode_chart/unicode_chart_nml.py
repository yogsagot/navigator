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
    search_caption: Label    # unicode_chart.nml:30
    search: InputLine    # unicode_chart.nml:39
    history: History    # unicode_chart.nml:46
    grouping: RadioButtons    # unicode_chart.nml:57
    groups: ListViewer    # unicode_chart.nml:64
    filter: InputLine    # unicode_chart.nml:72
    clear_filter: Button    # unicode_chart.nml:80
    grid: UnicodeGrid    # unicode_chart.nml:88
    info: StaticText    # unicode_chart.nml:97
    insert_button: Button    # unicode_chart.nml:105
    copy_button: Button    # unicode_chart.nml:115
    abandon: Button    # unicode_chart.nml:123

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_clear_filter_click(self, event: _Event) -> bool:    # unicode_chart.nml:80
        """``clear_filter`` raised an event whose handler is ``on_click``."""
        return False

    async def on_grid_chosen(self, event: _Event) -> bool:    # unicode_chart.nml:88
        """``grid`` raised an event whose handler is ``on_chosen``."""
        return False

    async def on_insert_button_click(self, event: _Event) -> bool:    # unicode_chart.nml:105
        """``insert_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_copy_button_click(self, event: _Event) -> bool:    # unicode_chart.nml:115
        """``copy_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # unicode_chart.nml:123
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.search_caption = Label(parent=self)    # unicode_chart.nml:29
        self.search = InputLine(parent=self)    # unicode_chart.nml:38
        self.history = History(parent=self)    # unicode_chart.nml:45
        self.grouping = RadioButtons(parent=self)    # unicode_chart.nml:56
        self.groups = ListViewer(parent=self)    # unicode_chart.nml:63
        self.filter = InputLine(parent=self)    # unicode_chart.nml:71
        self.clear_filter = Button(parent=self)    # unicode_chart.nml:79
        self.grid = UnicodeGrid(parent=self)    # unicode_chart.nml:87
        self.info = StaticText(parent=self)    # unicode_chart.nml:96
        self.insert_button = Button(parent=self)    # unicode_chart.nml:104
        self.copy_button = Button(parent=self)    # unicode_chart.nml:114
        self.abandon = Button(parent=self)    # unicode_chart.nml:122

        self.modal_width = _bind(    # unicode_chart.nml:25
            lambda _o: max(76, min(_o.parent.width - 4, 120)) if _o.parent is not None else 76
        )
        self.modal_height = _bind(    # unicode_chart.nml:26
            lambda _o: max(22, min(_o.parent.height - 2, 50)) if _o.parent is not None else 22
        )
        self.title = _bind(lambda _o: _tr('Character Table'), yielding=True)    # unicode_chart.nml:27

        self.search_caption.x = 2    # unicode_chart.nml:31
        self.search_caption.y = 2    # unicode_chart.nml:32
        self.search_caption.width = 8    # unicode_chart.nml:33
        self.search_caption.height = 1    # unicode_chart.nml:34
        self.search_caption.text = _bind(    # unicode_chart.nml:35
            lambda _o: _tr('~S~earch'),
            yielding=True,
        )
        self.search_caption.link = _bind(lambda _o: self.search)    # unicode_chart.nml:36

        self.search.x = 10    # unicode_chart.nml:40
        self.search.y = 2    # unicode_chart.nml:41
        self.search.width = _bind(lambda _o: max(1, _o.parent.width - 16))    # unicode_chart.nml:42
        self.search.height = 1    # unicode_chart.nml:43

        self.history.link = _bind(lambda _o: self.search)    # unicode_chart.nml:47
        self.history.history_id = 'charsearch'    # unicode_chart.nml:48
        self.history.x = _bind(lambda _o: max(0, _o.parent.width - 5))    # unicode_chart.nml:49
        self.history.y = 2    # unicode_chart.nml:50
        self.history.width = 3    # unicode_chart.nml:51
        self.history.height = 1    # unicode_chart.nml:52

        self.grouping.x = 2    # unicode_chart.nml:58
        self.grouping.y = 4    # unicode_chart.nml:59
        self.grouping.width = 24    # unicode_chart.nml:60
        self.grouping.height = _bind(lambda _o: max(1, len(_o.items)))    # unicode_chart.nml:61

        self.groups.x = 2    # unicode_chart.nml:65
        self.groups.y = _bind(lambda _o: 5 + self.grouping.height)    # unicode_chart.nml:66
        self.groups.width = 24    # unicode_chart.nml:67
        self.groups.height = _bind(    # unicode_chart.nml:68
            lambda _o: max(3, _o.parent.height - 11 - self.grouping.height)
        )

        self.filter.x = 2    # unicode_chart.nml:73
        self.filter.y = _bind(lambda _o: self.groups.y + self.groups.height)    # unicode_chart.nml:74
        self.filter.width = 20    # unicode_chart.nml:75
        self.filter.height = 1    # unicode_chart.nml:76

        self.clear_filter.flat = True    # unicode_chart.nml:81
        self.clear_filter.x = 23    # unicode_chart.nml:82
        self.clear_filter.y = _bind(lambda _o: self.filter.y)    # unicode_chart.nml:83
        self.clear_filter.width = 3    # unicode_chart.nml:84
        self.clear_filter.height = 1    # unicode_chart.nml:85
        self.clear_filter.on_click = self.on_clear_filter_click    # unicode_chart.nml:80

        self.grid.x = 27    # unicode_chart.nml:89
        self.grid.y = 4    # unicode_chart.nml:90
        self.grid.width = _bind(lambda _o: max(4, _o.parent.width - 29))    # unicode_chart.nml:91
        self.grid.height = _bind(lambda _o: max(3, _o.parent.height - 9))    # unicode_chart.nml:92
        self.grid.on_chosen = self.on_grid_chosen    # unicode_chart.nml:88

        self.info.name = 'info'    # unicode_chart.nml:98
        self.info.x = 2    # unicode_chart.nml:99
        self.info.y = _bind(lambda _o: max(0, _o.parent.height - 5))    # unicode_chart.nml:100
        self.info.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # unicode_chart.nml:101
        self.info.height = 2    # unicode_chart.nml:102

        self.insert_button.text = _bind(    # unicode_chart.nml:106
            lambda _o: _tr('~I~nsert'),
            yielding=True,
        )
        self.insert_button.default = True    # unicode_chart.nml:107
        self.insert_button.x = _bind(lambda _o: max(0, _o.parent.width - 41))    # unicode_chart.nml:108
        self.insert_button.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # unicode_chart.nml:109
        self.insert_button.width = 12    # unicode_chart.nml:110
        self.insert_button.height = 2    # unicode_chart.nml:111
        self.insert_button.on_click = self.on_insert_button_click    # unicode_chart.nml:105

        self.copy_button.text = _bind(lambda _o: _tr('Co~p~y'), yielding=True)    # unicode_chart.nml:116
        self.copy_button.x = _bind(lambda _o: max(0, _o.parent.width - 28))    # unicode_chart.nml:117
        self.copy_button.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # unicode_chart.nml:118
        self.copy_button.width = 12    # unicode_chart.nml:119
        self.copy_button.height = 2    # unicode_chart.nml:120
        self.copy_button.on_click = self.on_copy_button_click    # unicode_chart.nml:115

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # unicode_chart.nml:124
        self.abandon.x = _bind(lambda _o: max(0, _o.parent.width - 15))    # unicode_chart.nml:125
        self.abandon.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # unicode_chart.nml:126
        self.abandon.width = 12    # unicode_chart.nml:127
        self.abandon.height = 2    # unicode_chart.nml:128
        self.abandon.on_click = self.on_abandon_click    # unicode_chart.nml:123
