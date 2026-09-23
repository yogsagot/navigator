# navml: generated
"""Generated from ``shell.nml``.

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
from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component
from navigator.widgets.console import Console    # shell.nml:1
from navigator.widgets.keybar import KeyBar    # shell.nml:2
from navigator.widgets.menubar import MenuBar    # shell.nml:3
from navml.widgets.desktop import Desktop    # shell.nml:4

__navml_component__ = "Shell"

__all__ = ["Shell"]


class Shell(_Component):
    """The Navigator screen: menu bar, the console, the desktop over it, key bar.

    The band between the two bars holds two layers, and the order of the
    children is the whole of how they stack.  The console is the bottom one and
    is **always showing** -- it is the background the windows float over, as the
    user screen was in DOS Navigator.  The desktop is the layer above it and
    holds every window; it paints nothing of its own, so the console shows
    between them.  Ctrl+O hides the desktop, which is one reactive flag and one
    ``visible`` line.  The key bar is last so nothing covers it, and a modal is
    overlaid on this root, which puts it above the desktop by construction.
    """

    #: The document this class was generated from.
    __navml_source__ = "shell.nml"

    #: Whether Ctrl+O has put the windows away.  One flag that the desktop's
    #: ``visible`` line reads, which is the whole of Ctrl+O.
    console_visible: bool = _reactive(False)    # shell.nml:19

    #: Ids, annotated so the hand-written half completes them.
    menu: MenuBar    # shell.nml:22
    console: Console    # shell.nml:29
    desktop: Desktop    # shell.nml:36
    keybar: KeyBar    # shell.nml:44

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_desktop_emptied(self, event: _Event) -> bool:    # shell.nml:36
        """``desktop`` raised an event whose handler is ``on_emptied``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.menu = MenuBar(parent=self)    # shell.nml:21
        self.console = Console(parent=self)    # shell.nml:28
        self.desktop = Desktop(parent=self)    # shell.nml:35
        self.keybar = KeyBar(parent=self)    # shell.nml:43

        self.menu.x = 0    # shell.nml:23
        self.menu.y = 0    # shell.nml:24
        self.menu.width = _bind(lambda _o: _o.parent.width)    # shell.nml:25
        self.menu.height = 1    # shell.nml:26

        self.console.x = 0    # shell.nml:30
        self.console.y = 1    # shell.nml:31
        self.console.width = _bind(lambda _o: _o.parent.width)    # shell.nml:32
        self.console.height = _bind(lambda _o: max(1, _o.parent.height - 2))    # shell.nml:33

        self.desktop.x = 0    # shell.nml:37
        self.desktop.y = 1    # shell.nml:38
        self.desktop.width = _bind(lambda _o: _o.parent.width)    # shell.nml:39
        self.desktop.height = _bind(lambda _o: max(1, _o.parent.height - 2))    # shell.nml:40
        self.desktop.visible = _bind(lambda _o: not _o.parent.console_visible)    # shell.nml:41
        self.desktop.on_emptied = self.on_desktop_emptied    # shell.nml:36

        self.keybar.x = 0    # shell.nml:45
        self.keybar.y = _bind(lambda _o: max(1, _o.parent.height - 1))    # shell.nml:46
        self.keybar.width = _bind(lambda _o: _o.parent.width)    # shell.nml:47
        self.keybar.height = 1    # shell.nml:48
