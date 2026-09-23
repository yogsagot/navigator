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
from navigator.widgets.panel import Panel    # manager.nml:1
from navml.widgets.window import Window    # manager.nml:2

__navml_component__ = "Manager"

__all__ = ["Manager"]


class Manager(Window, _Component):
    """The file manager: two panels, in a window on the desktop.

    DOS Navigator's ``TDoubleWindow``, and **frameless**: the two panels'
    frames are the window's frame, so there is nothing to draw around them.
    The close and zoom icons go on the panels' top edges and the resize grip on
    the right panel's corner, which ``Window.render_after`` paints over them.

    The panels' geometry is bound to the window's, and the window's is not
    bound to anything: a drag assigns it, and the panels follow because what
    they read is reactive.  The window opens zoomed, filling the desktop, which
    is what the desktop looked like before there was one.

    Where the two panels open is not here: a panel *navigates* its ``path``, and
    markup can only bind, so binding it would make ``enter()`` an error rather
    than a move.  The hand-written half seeds both instead -- see
    ``manager.py``.
    """

    #: The document this class was generated from.
    __navml_source__ = "manager.nml"

    #: Ids, annotated so the hand-written half completes them.
    left: Panel    # manager.nml:26
    right: Panel    # manager.nml:34

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.left = Panel(parent=self)    # manager.nml:25
        self.right = Panel(parent=self)    # manager.nml:33

        self.zoomed = True    # manager.nml:21
        self.min_width = 24    # manager.nml:22
        self.min_height = 5    # manager.nml:23

        self.left.x = 0    # manager.nml:27
        self.left.y = 0    # manager.nml:28
        self.left.width = _bind(lambda _o: _o.parent.width // 2)    # manager.nml:29
        self.left.height = _bind(lambda _o: _o.parent.height)    # manager.nml:30
        self.left.title_margin = 5    # manager.nml:31

        self.right.x = _bind(lambda _o: _o.parent.width // 2)    # manager.nml:35
        self.right.y = 0    # manager.nml:36
        self.right.width = _bind(    # manager.nml:37
            lambda _o: _o.parent.width - _o.parent.width // 2
        )
        self.right.height = _bind(lambda _o: _o.parent.height)    # manager.nml:38
        self.right.title_margin = 5    # manager.nml:39
