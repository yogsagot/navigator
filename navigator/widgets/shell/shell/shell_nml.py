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
from navigator.widgets.shell.clock import Clock    # shell.nml:1
from navigator.widgets.shell.command_line import CommandLine    # shell.nml:2
from navigator.widgets.shell.console import Console    # shell.nml:3
from navigator.widgets.shell.keybar import KeyBar    # shell.nml:4
from navigator.widgets.shell.main_menu import MainMenu    # shell.nml:5
from navml.widgets.desktop import Desktop    # shell.nml:6
from navml.widgets.layout.dock_layout import DockLayout    # shell.nml:7
from navml.widgets.window_strip import WindowStrip    # shell.nml:8

__navml_component__ = "Shell"

__all__ = ["Shell"]


class Shell(DockLayout, _Component):
    """The Navigator screen: the console, the desktop over it, the menu bar and

    clock over that, the command line, key bar.

    The band between the two bars holds two layers, and the order of the
    children is the whole of how they stack.  The console is the bottom one and
    is **always showing** -- it is the background the windows float over, as the
    user screen was in DOS Navigator.  The desktop is the layer above it and
    holds every window; it paints nothing of its own, so the console shows
    between them.  Ctrl+O hides the desktop, which is one reactive flag and one
    ``visible`` line.  The key bar is last so nothing covers it, and a modal is
    overlaid on this root, which puts it above the desktop by construction.

    The bars dock against the top and bottom edges, and the two layers both
    *fill*, which a dock layout gives them as one shared rectangle -- it places
    every fill after every edge, so the key bar can come last in the child
    order, and so last in the paint, and still be carved off first.

    The command line docks after the key bar, which is what puts it on the row
    above it: edges are carved in child order, so the key bar takes the last
    row and the line the one left at the bottom.  DOS Navigator's
    ``InitCommandLine`` put it there, and gave up that row from the desktop.
    """

    #: The document this class was generated from.
    __navml_source__ = "shell.nml"

    #: Whether Ctrl+O has put the windows away.  One flag that the desktop's
    #: ``visible`` line reads, which is the whole of Ctrl+O.
    console_visible: bool = _reactive(False)    # shell.nml:34

    #: Ids, annotated so the hand-written half completes them.
    console: Console    # shell.nml:37
    desktop: Desktop    # shell.nml:40
    menu: MainMenu    # shell.nml:53
    window_strip: WindowStrip    # shell.nml:63
    clock: Clock    # shell.nml:75
    keybar: KeyBar    # shell.nml:84
    command_line: CommandLine    # shell.nml:94

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_desktop_emptied(self, event: _Event) -> bool:    # shell.nml:40
        """``desktop`` raised an event whose handler is ``on_emptied``."""
        return False

    async def on_desktop_opened(self, event: _Event) -> bool:    # shell.nml:40
        """``desktop`` raised an event whose handler is ``on_opened``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.console = Console(parent=self)    # shell.nml:36
        self.desktop = Desktop(parent=self)    # shell.nml:39
        self.menu = MainMenu(parent=self)    # shell.nml:52
        self.window_strip = WindowStrip(parent=self)    # shell.nml:62
        self.clock = Clock(parent=self)    # shell.nml:74
        self.keybar = KeyBar(parent=self)    # shell.nml:83
        self.command_line = CommandLine(parent=self)    # shell.nml:93

        self.desktop.visible = _bind(lambda _o: not _o.parent.console_visible)    # shell.nml:41
        self.desktop.on_emptied = self.on_desktop_emptied    # shell.nml:40
        self.desktop.on_opened = self.on_desktop_opened    # shell.nml:40

        self.menu.context = _bind(    # shell.nml:54
            lambda _o: None if _o.parent.console_visible else self.desktop.active_window
        )
        self.menu.width = _bind(lambda _o: _o.parent.width)    # shell.nml:55
        self.menu.height = 1    # shell.nml:56

        self.window_strip.desktop = _bind(lambda _o: _o.parent.desktop)    # shell.nml:64
        self.window_strip.align = 'right'    # shell.nml:65
        self.window_strip.y = 0    # shell.nml:66
        self.window_strip.height = 1    # shell.nml:67
        self.window_strip.inline_style = 'dock: none'    # shell.nml:68

        self.clock.x = _bind(lambda _o: max(0, _o.parent.width - _o.width))    # shell.nml:76
        self.clock.y = 0    # shell.nml:77
        self.clock.inline_style = 'dock: none'    # shell.nml:78

        self.keybar.inline_style = 'dock: bottom; basis: 1'    # shell.nml:85

        self.command_line.prompt = _bind(lambda _o: _o.parent.command_prompt)    # shell.nml:95
        self.command_line.prompt_cells = _bind(    # shell.nml:96
            lambda _o: _o.parent.command_prompt_cells
        )
        self.command_line.inline_style = 'dock: bottom; basis: 1'    # shell.nml:97
