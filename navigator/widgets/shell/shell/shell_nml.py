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
from navigator.widgets.shell.job_mark import JobMark    # shell.nml:5
from navigator.widgets.shell.macro_mark import MacroMark    # shell.nml:6
from navigator.widgets.shell.main_menu import MainMenu    # shell.nml:7
from navigator.widgets.shell.root_mark import RootMark    # shell.nml:8
from navigator.widgets.shell.trash_can import TrashCan    # shell.nml:9
from navigator.lib.config import country    # shell.nml:10
from navigator.settings import SETTINGS    # shell.nml:11
from navml.widgets.desktop import Desktop    # shell.nml:12
from navml.widgets.layout.dock_layout import DockLayout    # shell.nml:13
from navml.widgets.window_strip import WindowStrip    # shell.nml:14

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
    console_visible: bool = _reactive(False)    # shell.nml:40

    #: Ids, annotated so the hand-written half completes them.
    console: Console    # shell.nml:43
    desktop: Desktop    # shell.nml:46
    menu: MainMenu    # shell.nml:62
    window_strip: WindowStrip    # shell.nml:77
    clock: Clock    # shell.nml:96
    root_mark: RootMark    # shell.nml:109
    macro_mark: MacroMark    # shell.nml:122
    job_mark: JobMark    # shell.nml:137
    trash: TrashCan    # shell.nml:148
    keybar: KeyBar    # shell.nml:156
    key_root_mark: RootMark    # shell.nml:169
    command_line: CommandLine    # shell.nml:187

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_desktop_opened(self, event: _Event) -> bool:    # shell.nml:46
        """``desktop`` raised an event whose handler is ``on_opened``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.console = Console(parent=self)    # shell.nml:42
        self.desktop = Desktop(parent=self)    # shell.nml:45
        self.menu = MainMenu(parent=self)    # shell.nml:61
        self.window_strip = WindowStrip(parent=self)    # shell.nml:76
        self.clock = Clock(parent=self)    # shell.nml:95
        self.root_mark = RootMark(parent=self)    # shell.nml:108
        self.macro_mark = MacroMark(parent=self)    # shell.nml:121
        self.job_mark = JobMark(parent=self)    # shell.nml:136
        self.trash = TrashCan(parent=self)    # shell.nml:147
        self.keybar = KeyBar(parent=self)    # shell.nml:155
        self.key_root_mark = RootMark(parent=self)    # shell.nml:168
        self.command_line = CommandLine(parent=self)    # shell.nml:186

        self.desktop.visible = _bind(lambda _o: not _o.parent.console_visible)    # shell.nml:47

        async def _on_emptied(event):    # shell.nml:49
            self.show_console()
            return True
        self.desktop.on_emptied = _on_emptied
        self.desktop.on_opened = self.on_desktop_opened    # shell.nml:46

        self.menu.context = _bind(    # shell.nml:63
            lambda _o: None if _o.parent.console_visible else self.desktop.active_window
        )
        self.menu.width = _bind(lambda _o: _o.parent.width)    # shell.nml:64
        self.menu.height = 1    # shell.nml:65
        self.menu.inline_style = _bind(    # shell.nml:66
            lambda _o: 'dock: none' if SETTINGS.interface.hide_menu_bar else 'dock: top; basis: 1'
        )
        self.menu.visible = _bind(    # shell.nml:67
            lambda _o: not SETTINGS.interface.hide_menu_bar or _o.current >= 0
        )
        self.menu.reserve = _bind(    # shell.nml:68
            lambda _o: max(0, _o.width - self.clock.x + 1) if self.clock.visible else 0
        )

        self.window_strip.desktop = _bind(lambda _o: _o.parent.desktop)    # shell.nml:78
        self.window_strip.align = 'right'    # shell.nml:79
        self.window_strip.x = _bind(    # shell.nml:80
            lambda _o: self.menu.item_span(len(self.menu.entries()))[0] + 1 + (self.job_mark.width if self.job_mark.visible else 0)
        )
        self.window_strip.y = 0    # shell.nml:81
        self.window_strip.height = 1    # shell.nml:82
        self.window_strip.labels = _bind(    # shell.nml:86
            lambda _o: SETTINGS.interface.window_strip == 'full'
        )
        self.window_strip.visible = _bind(    # shell.nml:87
            lambda _o: SETTINGS.interface.window_strip != 'off' and (not SETTINGS.interface.hide_menu_bar) and (not _o.parent.console_visible)
        )
        self.window_strip.width = _bind(    # shell.nml:84
            lambda _o: max(0, (self.macro_mark.x - 1 if self.macro_mark.visible and self.macro_mark.width else self.root_mark.x - 1 if self.root_mark.visible and self.root_mark.width else self.clock.x - 1 if self.clock.visible and self.clock.width else _o.parent.width - 1) - _o.x)
        )
        self.window_strip.inline_style = 'dock: none'    # shell.nml:88

        self.clock.visible = _bind(lambda _o: SETTINGS.interface.clock)    # shell.nml:97
        self.clock.width = _bind(lambda _o: 7 if country.twelve_hours() else 5)    # shell.nml:98
        self.clock.y = 0    # shell.nml:99
        self.clock.x = _bind(lambda _o: max(0, _o.parent.width - _o.width))    # shell.nml:101
        self.clock.inline_style = 'dock: none'    # shell.nml:102

        self.root_mark.y = 0    # shell.nml:110
        self.root_mark.width = _bind(lambda _o: _o.natural_width)    # shell.nml:111
        self.root_mark.visible = _bind(    # shell.nml:115
            lambda _o: _o.open and (not SETTINGS.interface.hide_menu_bar) and (not _o.parent.console_visible)
        )
        self.root_mark.x = _bind(    # shell.nml:113
            lambda _o: max(0, (self.clock.x - 1 if self.clock.visible and self.clock.width else _o.parent.width) - _o.width)
        )
        self.root_mark.inline_style = 'dock: none'    # shell.nml:116

        self.macro_mark.y = 0    # shell.nml:123
        self.macro_mark.width = _bind(lambda _o: _o.natural_width)    # shell.nml:124
        self.macro_mark.visible = _bind(    # shell.nml:128
            lambda _o: _o.slot > 0 and (not SETTINGS.interface.hide_menu_bar) and (not _o.parent.console_visible)
        )
        self.macro_mark.x = _bind(    # shell.nml:126
            lambda _o: max(0, (self.root_mark.x - 1 if self.root_mark.visible and self.root_mark.width else self.clock.x - 1 if self.clock.visible and self.clock.width else _o.parent.width - 1) - _o.width)
        )
        self.macro_mark.inline_style = 'dock: none'    # shell.nml:129

        self.job_mark.x = _bind(lambda _o: self.strip_start() - _o.width)    # shell.nml:138
        self.job_mark.y = 0    # shell.nml:139
        self.job_mark.width = _bind(lambda _o: _o.natural_width)    # shell.nml:140
        self.job_mark.visible = _bind(    # shell.nml:141
            lambda _o: _o.busy and (not SETTINGS.interface.hide_menu_bar) and (not _o.parent.console_visible)
        )
        self.job_mark.inline_style = 'dock: none'    # shell.nml:142

        self.trash.desktop = _bind(lambda _o: _o.parent.desktop)    # shell.nml:149
        self.trash.inline_style = 'dock: none'    # shell.nml:150

        self.keybar.visible = _bind(    # shell.nml:157
            lambda _o: not SETTINGS.interface.hide_status_line
        )
        self.keybar.reserve = _bind(    # shell.nml:159
            lambda _o: self.key_root_mark.width + 1 if self.key_root_mark.visible else 0
        )
        self.keybar.inline_style = 'dock: bottom; basis: 1'    # shell.nml:160

        self.key_root_mark.open = _bind(lambda _o: self.root_mark.open)    # shell.nml:170
        self.key_root_mark.y = _bind(lambda _o: self.keybar.y)    # shell.nml:171
        self.key_root_mark.width = _bind(lambda _o: _o.natural_width)    # shell.nml:172
        self.key_root_mark.visible = _bind(    # shell.nml:175
            lambda _o: _o.open and self.keybar.visible and (SETTINGS.interface.hide_menu_bar or _o.parent.console_visible)
        )
        self.key_root_mark.x = _bind(    # shell.nml:174
            lambda _o: max(0, _o.parent.width - _o.width)
        )
        self.key_root_mark.inline_style = 'dock: none'    # shell.nml:176

        self.command_line.prompt = _bind(lambda _o: _o.parent.command_prompt)    # shell.nml:188
        self.command_line.prompt_cells = _bind(    # shell.nml:189
            lambda _o: _o.parent.command_prompt_cells
        )
        self.command_line.visible = _bind(    # shell.nml:190
            lambda _o: not SETTINGS.interface.hide_command_line and (not SETTINGS.interface.auto_hide_command_line or _o.value != '')
        )
        self.command_line.inline_style = 'dock: bottom; basis: 1'    # shell.nml:191
