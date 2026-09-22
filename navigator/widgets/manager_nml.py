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
from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component
from navigator.widgets.console import Console    # manager.nml:1
from navigator.widgets.keybar import KeyBar    # manager.nml:2
from navigator.widgets.menubar import MenuBar    # manager.nml:3
from navigator.widgets.panel import Panel    # manager.nml:4

__navml_component__ = "Manager"

__all__ = ["Manager"]


class Manager(_Component):
    """The Navigator desktop: menu bar, two panels and the key bar.

    The first screen written as markup rather than placed by hand, and it reads
    the way the old ``_place()`` did because that method was written to compile
    to this.  There is no ``layout()`` anywhere: every size that depends on the
    terminal is an expression, so a resize propagates by itself.

    Where the two panels open is not here, and that is the one thing converting
    this screen turned up: a panel *navigates* its ``path``, and markup can only
    bind, so binding it would make ``enter()`` an error rather than a move.  The
    hand-written half seeds all three instead -- see ``manager.py``.
    """

    #: The document this class was generated from.
    __navml_source__ = "manager.nml"

    #: Whether Ctrl+O has swapped the panels for the console.  One flag that
    #: the three ``visible`` lines below read, which is the whole of Ctrl+O.
    console_visible: bool = _reactive(False)    # manager.nml:20

    #: Ids, annotated so the hand-written half completes them.
    menu: MenuBar    # manager.nml:23
    left: Panel    # manager.nml:30
    right: Panel    # manager.nml:39
    console: Console    # manager.nml:50
    keybar: KeyBar    # manager.nml:58

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.menu = MenuBar(parent=self)    # manager.nml:22
        self.left = Panel(parent=self)    # manager.nml:29
        self.right = Panel(parent=self)    # manager.nml:38
        self.console = Console(parent=self)    # manager.nml:49
        self.keybar = KeyBar(parent=self)    # manager.nml:57

        self.menu.x = 0    # manager.nml:24
        self.menu.y = 0    # manager.nml:25
        self.menu.width = _bind(lambda _o: _o.parent.width)    # manager.nml:26
        self.menu.height = 1    # manager.nml:27

        self.left.x = 0    # manager.nml:31
        self.left.y = 1    # manager.nml:32
        self.left.width = _bind(lambda _o: _o.parent.width // 2)    # manager.nml:33
        self.left.height = _bind(lambda _o: max(3, _o.parent.height - 2))    # manager.nml:34
        self.left.visible = _bind(lambda _o: not _o.parent.console_visible)    # manager.nml:35
        self.left.active = True    # manager.nml:36

        self.right.x = _bind(lambda _o: _o.parent.width // 2)    # manager.nml:40
        self.right.y = 1    # manager.nml:41
        self.right.width = _bind(    # manager.nml:42
            lambda _o: _o.parent.width - _o.parent.width // 2
        )
        self.right.height = _bind(lambda _o: max(3, _o.parent.height - 2))    # manager.nml:43
        self.right.visible = _bind(lambda _o: not _o.parent.console_visible)    # manager.nml:44

        self.console.x = 0    # manager.nml:51
        self.console.y = 1    # manager.nml:52
        self.console.width = _bind(lambda _o: _o.parent.width)    # manager.nml:53
        self.console.height = _bind(lambda _o: max(1, _o.parent.height - 2))    # manager.nml:54
        self.console.visible = _bind(lambda _o: _o.parent.console_visible)    # manager.nml:55

        self.keybar.x = 0    # manager.nml:59
        self.keybar.y = _bind(lambda _o: max(1, _o.parent.height - 1))    # manager.nml:60
        self.keybar.width = _bind(lambda _o: _o.parent.width)    # manager.nml:61
        self.keybar.height = 1    # manager.nml:62
