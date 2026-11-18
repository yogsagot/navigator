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
from navigator.widgets.help.help_viewer import HelpViewer    # help_window.nml:2
from navml.commands import ZoomWindow    # help_window.nml:3
from navml.widgets.dialog.dialog import Dialog    # help_window.nml:4
from navml.widgets.dialog.scroll_bar import ScrollBar    # help_window.nml:5

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

    Alt+Z zooms it to the whole screen and back.  Departures: no bar along
    the bottom frame -- a page is wrapped to the width, so there is nothing to
    scroll to -- the right one only while the page is longer than the window
    (as the viewer's), and neither dragging nor Ctrl+F5's resize, a modal
    here being a fixed box.
    """

    #: The document this class was generated from.
    __navml_source__ = "help_window.nml"

    #: The keys this component binds, read through key_table().
    keys = {    # help_window.nml:33
        'f1': HelpOnHelp,    # help_window.nml:34
        'shift+f1': HelpIndex,    # help_window.nml:35
        'tab': NextTopic,    # help_window.nml:36
        'shift+tab': PreviousTopic,    # help_window.nml:37
        'enter': GoToReference,    # help_window.nml:38
        'alt+f1': GoBack,    # help_window.nml:39
        'alt+z': ZoomWindow,    # help_window.nml:40
    }

    #: Whether it fills the screen: Alt+Z, ``cmZoom``.
    zoomed: bool = _reactive(False)    # help_window.nml:26

    #: Ids, annotated so the hand-written half completes them.
    viewer: HelpViewer    # help_window.nml:51
    bar: ScrollBar    # help_window.nml:59

    #: The commands this component handles itself.
    async def on_next_topic(self, event: _Any) -> bool:    # help_window.nml:44
        """``NextTopic``."""
        self.viewer.step(1)
        return True

    async def on_previous_topic(self, event: _Any) -> bool:    # help_window.nml:45
        """``PreviousTopic``."""
        self.viewer.step(-1)
        return True

    async def on_go_to_reference(self, event: _Any) -> bool:    # help_window.nml:46
        """``GoToReference``."""
        self.viewer.follow()
        return True

    async def on_go_back(self, event: _Any) -> bool:    # help_window.nml:47
        """``GoBack``."""
        self.viewer.back()
        return True

    async def on_zoom_window(self, event: _Any) -> bool:    # help_window.nml:48
        """``ZoomWindow``."""
        self.toggle_zoom()
        return True

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_bar_scroll(self, event: _Event) -> bool:    # help_window.nml:59
        """``bar`` raised an event whose handler is ``on_scroll``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.viewer = HelpViewer(parent=self)    # help_window.nml:50
        self.bar = ScrollBar(parent=self)    # help_window.nml:58

        self.modal_width = _bind(    # help_window.nml:28
            lambda _o: (_o.parent.width if _o.zoomed else max(min(72, _o.parent.width), _o.parent.width * 4 // 5)) if _o.parent is not None else 72
        )
        self.modal_height = _bind(    # help_window.nml:29
            lambda _o: (max(3, _o.parent.height - 2) if _o.zoomed else max(min(20, _o.parent.height), _o.parent.height * 4 // 5)) if _o.parent is not None else 20
        )
        self.title = _bind(lambda _o: _tr('Help'), yielding=True)    # help_window.nml:30
        self.buttons = 'none'    # help_window.nml:31

        self.viewer.x = 2    # help_window.nml:53
        self.viewer.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # help_window.nml:54
        self.viewer.y = 1    # help_window.nml:55
        self.viewer.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # help_window.nml:56

        self.bar.width = 1    # help_window.nml:60
        self.bar.visible = _bind(    # help_window.nml:65
            lambda _o: self.viewer.total > self.viewer.height
        )
        self.bar.value = _bind(lambda _o: self.viewer.top)    # help_window.nml:66
        self.bar.maximum = _bind(    # help_window.nml:67
            lambda _o: max(0, self.viewer.total - self.viewer.height)
        )
        self.bar.page = _bind(lambda _o: max(1, self.viewer.height))    # help_window.nml:68
        self.bar.x = _bind(lambda _o: max(0, _o.parent.width - _o.width))    # help_window.nml:62
        self.bar.y = 1    # help_window.nml:63
        self.bar.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # help_window.nml:64
        self.bar.on_scroll = self.on_bar_scroll    # help_window.nml:59

        self._navml_built(__class__)
