# navml: generated
"""Generated from ``help_window.nml``.

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
from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component
from navigator.widgets.help.commands import GoBack, GoToReference, HelpIndex, HelpOnHelp, NextTopic, PreviousTopic    # help_window.nml:1
from navigator.widgets.help.commands import ScrollLeft, ScrollLineDown, ScrollLineUp, ScrollPageDown, ScrollPageUp    # help_window.nml:2
from navigator.widgets.help.commands import ScrollRight, ScrollToBottom, ScrollToTop    # help_window.nml:3
from navigator.widgets.help.help_viewer import HelpViewer    # help_window.nml:4
from navml.commands import SizeMoveWindow, ZoomWindow    # help_window.nml:5
from navml.widgets.dialog.dialog import Dialog    # help_window.nml:6
from navml.widgets.dialog.scroll_bar import ScrollBar    # help_window.nml:7

__navml_component__ = "HelpWindow"

__all__ = ["HelpWindow"]


class HelpWindow(Dialog, _Component):
    """F1: DOS Navigator's ``THelpWindow`` (``HELPFILE.PAS``).

    ``R.Assign(0, 0, 72, 20)``, centred, titled *Help*, and run modally
    (``DNUTIL.PAS``'s ``cmHelp``: ``ExecView``) -- so it opens over a dialog
    and Esc goes back to it.  The viewer is ``R.Grow(-2, -1)``, the scroll bar
    on the right frame.  The keys are ``StatusDef hcHelp``'s.

    **Four fifths of a large screen, a departure, asked for**: DN's 72 by 20
    was most of its 80 by 25; here the window is 80% of the terminal's width
    and of its height, and never smaller than DN's where the screen has the
    room -- so an 80 by 24 terminal still gets DN's 72 by 20.

    Alt+Z zooms it to the whole screen and back; Ctrl+F5 moves and sizes it
    with the keyboard (``cmResize``), as it does a window on the desktop.  A
    modal's geometry is bound, so the mode does not assign it: it writes
    ``placed``, which the bindings read (``help_window.py``).  There is no
    dragging with the mouse.

    Departures: the bars are there only while there is something to scroll to
    (as the viewer's) -- the right one while the page is longer than the
    window, the bottom one while a code block is wider than it, a page being
    wrapped to the width otherwise.

    Every key is in the table, the scrolling ones too, so that all of them are
    in ``keybindings.ini`` (its ``[help]`` section).
    """

    #: The document this class was generated from.
    __navml_source__ = "help_window.nml"

    #: The keys this component binds, read through key_table().
    keys = {    # help_window.nml:47
        'f1': HelpOnHelp,    # help_window.nml:48
        'shift+f1': HelpIndex,    # help_window.nml:49
        'tab': NextTopic,    # help_window.nml:50
        'shift+tab': PreviousTopic,    # help_window.nml:51
        'enter': GoToReference,    # help_window.nml:52
        'alt+f1': GoBack,    # help_window.nml:53
        'alt+z': ZoomWindow,    # help_window.nml:54
        'ctrl+f5': SizeMoveWindow,    # help_window.nml:55
        'up': ScrollLineUp,    # help_window.nml:56
        'down': ScrollLineDown,    # help_window.nml:57
        'pageup': ScrollPageUp,    # help_window.nml:58
        'pagedown': ScrollPageDown,    # help_window.nml:59
        'home': ScrollToTop,    # help_window.nml:60
        'end': ScrollToBottom,    # help_window.nml:61
        'left': ScrollLeft,    # help_window.nml:62
        'right': ScrollRight,    # help_window.nml:63
    }

    #: Whether it fills the screen: Alt+Z, ``cmZoom``.
    zoomed: bool = _reactive(False)    # help_window.nml:36

    #: Where Ctrl+F5 put it, ``(x, y, width, height)``; None while it is
    #: where and as large as it opened.  Kept on the screen by what reads it.
    placed = _reactive(None)    # help_window.nml:40

    #: Ids, annotated so the hand-written half completes them.
    viewer: HelpViewer    # help_window.nml:83
    bar: ScrollBar    # help_window.nml:91
    hbar: ScrollBar    # help_window.nml:105

    #: The commands this component handles itself.
    async def on_next_topic(self, event: _Any) -> bool:    # help_window.nml:67
        """``NextTopic``."""
        self.viewer.step(1)
        return True

    async def on_previous_topic(self, event: _Any) -> bool:    # help_window.nml:68
        """``PreviousTopic``."""
        self.viewer.step(-1)
        return True

    async def on_go_to_reference(self, event: _Any) -> bool:    # help_window.nml:69
        """``GoToReference``."""
        self.viewer.follow()
        return True

    async def on_go_back(self, event: _Any) -> bool:    # help_window.nml:70
        """``GoBack``."""
        self.viewer.back()
        return True

    async def on_zoom_window(self, event: _Any) -> bool:    # help_window.nml:71
        """``ZoomWindow``."""
        self.toggle_zoom()
        return True

    async def on_size_move_window(self, event: _Any) -> bool:    # help_window.nml:72
        """``SizeMoveWindow``."""
        self.begin_move()
        return True

    async def on_scroll_line_up(self, event: _Any) -> bool:    # help_window.nml:73
        """``ScrollLineUp``."""
        self.viewer.scroll_by(-1)
        return True

    async def on_scroll_line_down(self, event: _Any) -> bool:    # help_window.nml:74
        """``ScrollLineDown``."""
        self.viewer.scroll_by(1)
        return True

    async def on_scroll_page_up(self, event: _Any) -> bool:    # help_window.nml:75
        """``ScrollPageUp``."""
        self.viewer.scroll_by(-self.viewer.page_rows())
        return True

    async def on_scroll_page_down(self, event: _Any) -> bool:    # help_window.nml:76
        """``ScrollPageDown``."""
        self.viewer.scroll_by(self.viewer.page_rows())
        return True

    async def on_scroll_to_top(self, event: _Any) -> bool:    # help_window.nml:77
        """``ScrollToTop``."""
        self.viewer.scroll_to(0)
        return True

    async def on_scroll_to_bottom(self, event: _Any) -> bool:    # help_window.nml:78
        """``ScrollToBottom``."""
        self.viewer.scroll_to(self.viewer.total)
        return True

    async def on_scroll_left(self, event: _Any) -> bool:    # help_window.nml:79
        """``ScrollLeft``."""
        self.viewer.scroll_sideways(-1)
        return True

    async def on_scroll_right(self, event: _Any) -> bool:    # help_window.nml:80
        """``ScrollRight``."""
        self.viewer.scroll_sideways(1)
        return True

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_bar_scroll(self, event: _Event) -> bool:    # help_window.nml:91
        """``bar`` raised an event whose handler is ``on_scroll``."""
        return False

    async def on_hbar_scroll(self, event: _Event) -> bool:    # help_window.nml:105
        """``hbar`` raised an event whose handler is ``on_scroll``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.viewer = HelpViewer(parent=self)    # help_window.nml:82
        self.bar = ScrollBar(parent=self)    # help_window.nml:90
        self.hbar = ScrollBar(parent=self)    # help_window.nml:104

        self.modal_width = _bind(    # help_window.nml:42
            lambda _o: (_o.parent.width if _o.zoomed else _o.placed_size(_o.parent.width, _o.parent.height)[0] if _o.placed else max(min(72, _o.parent.width), _o.parent.width * 4 // 5)) if _o.parent is not None else 72
        )
        self.modal_height = _bind(    # help_window.nml:43
            lambda _o: (max(3, _o.parent.height - 2) if _o.zoomed else _o.placed_size(_o.parent.width, _o.parent.height)[1] if _o.placed else max(min(20, _o.parent.height), _o.parent.height * 4 // 5)) if _o.parent is not None else 20
        )
        self.title = _bind(lambda _o: _tr('Help'), yielding=True)    # help_window.nml:44
        self.buttons = 'none'    # help_window.nml:45

        self.viewer.x = 2    # help_window.nml:85
        self.viewer.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # help_window.nml:86
        self.viewer.y = 1    # help_window.nml:87
        self.viewer.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # help_window.nml:88

        self.bar.width = 1    # help_window.nml:92
        self.bar.visible = _bind(    # help_window.nml:97
            lambda _o: self.viewer.total > self.viewer.height
        )
        self.bar.value = _bind(lambda _o: self.viewer.top)    # help_window.nml:98
        self.bar.maximum = _bind(    # help_window.nml:99
            lambda _o: max(0, self.viewer.total - self.viewer.height)
        )
        self.bar.page = _bind(lambda _o: max(1, self.viewer.height))    # help_window.nml:100
        self.bar.x = _bind(lambda _o: max(0, _o.parent.width - _o.width))    # help_window.nml:94
        self.bar.y = 1    # help_window.nml:95
        self.bar.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # help_window.nml:96
        self.bar.on_scroll = self.on_bar_scroll    # help_window.nml:91

        self.hbar.orientation = 'horizontal'    # help_window.nml:106
        self.hbar.height = 1    # help_window.nml:107
        self.hbar.visible = _bind(    # help_window.nml:112
            lambda _o: self.viewer.span > self.viewer.width
        )
        self.hbar.value = _bind(lambda _o: self.viewer.left)    # help_window.nml:113
        self.hbar.maximum = _bind(    # help_window.nml:114
            lambda _o: max(0, self.viewer.span - self.viewer.width)
        )
        self.hbar.page = _bind(lambda _o: max(1, self.viewer.width))    # help_window.nml:115
        self.hbar.x = 2    # help_window.nml:109
        self.hbar.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # help_window.nml:110
        self.hbar.y = _bind(lambda _o: max(0, _o.parent.height - _o.height))    # help_window.nml:111
        self.hbar.on_scroll = self.on_hbar_scroll    # help_window.nml:105

        self._navml_built(__class__)
