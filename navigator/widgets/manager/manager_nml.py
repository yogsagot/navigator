# navml: generated
"""Generated from ``manager.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navigator.commands import Copy, Delete, Edit, MakeDirectory, RenameMove    # manager.nml:1
from navigator.commands import Rescan, SwitchPanel, UserMenu, View    # manager.nml:2
from navigator.widgets.panel import Panel    # manager.nml:3
from navml.widgets.layout.horizontal_layout import HorizontalLayout    # manager.nml:4
from navml.widgets.window import Window    # manager.nml:5

__navml_component__ = "Manager"

__all__ = ["Manager"]


class Manager(Window, _Component):
    """The file manager: two panels, in a window on the desktop.

    DOS Navigator's ``TDoubleWindow``, and **frameless**: the two panels'
    frames are the window's frame, so there is nothing to draw around them.
    The close and zoom icons go on the panels' top edges and the resize grip on
    the right panel's corner, which ``Window.render_after`` paints over them.

    The panels share a row that is bound to the window's size, and the
    window's is not bound to anything: a drag assigns it, and the row
    re-arranges the panels because the size it reads is reactive.  Two panels
    that say nothing split it evenly, the odd column going to the right one.  The window opens zoomed, filling the desktop, which
    is what the desktop looked like before there was one.

    Where the two panels open is not here: a panel *navigates* its ``path``, and
    markup can only bind, so binding it would make ``enter()`` an error rather
    than a move.  The hand-written half seeds both instead -- see
    ``manager.py``.
    """

    #: The document this class was generated from.
    __navml_source__ = "manager.nml"

    #: The panel keys.  Up, down, the pages and Enter are not here: they move
    #: *within* a panel and are ``ListViewer``'s, reached first along the
    #: focus path.  What is here needs the window -- which panel, and what to
    #: do in it.  F2 to F8 are the key bar's panel half; every one without a
    #: handler in ``manager.py`` is disabled, and greyed on the bar.
    keys = {    # manager.nml:34
        'tab': SwitchPanel,    # manager.nml:35
        'ctrl+r': Rescan,    # manager.nml:36
        'f2': UserMenu,    # manager.nml:37
        'f3': View,# manager.nml:38
        'f4': Edit,# manager.nml:39
        'f5': Copy,# manager.nml:40
        'f6': RenameMove,    # manager.nml:41
        'f7': MakeDirectory,    # manager.nml:42
        'f8': Delete,    # manager.nml:43
    }

    #: Ids, annotated so the hand-written half completes them.
    panels: HorizontalLayout    # manager.nml:46
    left: Panel    # manager.nml:53
    right: Panel    # manager.nml:57

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.panels = HorizontalLayout(parent=self)    # manager.nml:45
        self.left = Panel(parent=self.panels)    # manager.nml:52
        self.right = Panel(parent=self.panels)    # manager.nml:56

        self.zoomed = True    # manager.nml:25
        self.min_width = 24    # manager.nml:26
        self.min_height = 5    # manager.nml:27

        self.panels.x = 0    # manager.nml:47
        self.panels.y = 0    # manager.nml:48
        self.panels.width = _bind(lambda _o: _o.parent.width)    # manager.nml:49
        self.panels.height = _bind(lambda _o: _o.parent.height)    # manager.nml:50

        self.left.title_margin = 5    # manager.nml:54

        self.right.title_margin = 5    # manager.nml:58
