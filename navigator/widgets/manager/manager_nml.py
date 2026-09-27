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

from navkit.events import Event as _Event
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navigator.commands import ChangeDirectory, Copy, Delete, Edit, MakeDirectory, RenameMove    # manager.nml:1
from navigator.commands import Rescan, SwitchPanel, ToggleTree, UserMenu, View    # manager.nml:2
from navigator.widgets.directory_tree import DirectoryTree    # manager.nml:3
from navigator.widgets.panel import Panel    # manager.nml:4
from navml.widgets.layout.horizontal_layout import HorizontalLayout    # manager.nml:5
from navml.widgets.window import Window    # manager.nml:6

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
    keys = {    # manager.nml:35
        'tab': SwitchPanel,    # manager.nml:36
        'alt+r': Rescan,    # manager.nml:37
        'ctrl+r': Rescan,    # manager.nml:38
        'ctrl+t': ToggleTree,    # manager.nml:39
        'alt+t': ChangeDirectory,    # manager.nml:40
        'f2': UserMenu,    # manager.nml:41
        'f3': View,# manager.nml:42
        'f4': Edit,# manager.nml:43
        'f5': Copy,# manager.nml:44
        'f6': RenameMove,    # manager.nml:45
        'f7': MakeDirectory,    # manager.nml:46
        'f8': Delete,    # manager.nml:47
    }

    #: Ids, annotated so the hand-written half completes them.
    panels: HorizontalLayout    # manager.nml:50
    left: Panel    # manager.nml:57
    right: Panel    # manager.nml:61
    tree: DirectoryTree    # manager.nml:68

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_tree_chosen(self, event: _Event) -> bool:    # manager.nml:68
        """``tree`` raised an event whose handler is ``on_chosen``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.panels = HorizontalLayout(parent=self)    # manager.nml:49
        self.left = Panel(parent=self.panels)    # manager.nml:56
        self.right = Panel(parent=self.panels)    # manager.nml:60
        self.tree = DirectoryTree(parent=self.panels)    # manager.nml:67

        self.zoomed = True    # manager.nml:26
        self.min_width = 24    # manager.nml:27
        self.min_height = 5    # manager.nml:28

        self.panels.x = 0    # manager.nml:51
        self.panels.y = 0    # manager.nml:52
        self.panels.width = _bind(lambda _o: _o.parent.width)    # manager.nml:53
        self.panels.height = _bind(lambda _o: _o.parent.height)    # manager.nml:54

        self.left.title_margin = 5    # manager.nml:58

        self.right.title_margin = 5    # manager.nml:62

        self.tree.on_chosen = self.on_tree_chosen    # manager.nml:68
