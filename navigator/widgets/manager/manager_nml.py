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
from navigator.commands import ArchiveFiles, Calculator, ChangeDrive, DeleteSingle, DiskInfo, EditNamed    # manager.nml:3
from navigator.commands import ExtractArchive, FastRename, FindFile, MakeList, PanelSetup    # manager.nml:4
from navigator.commands import PhoneBook, PrintFile, QuickView, Reanimate, SortBy, SplitCombine    # manager.nml:5
from navigator.commands import InsertName, InsertPath, ToggleDescriptions, ToggleShowMode    # manager.nml:6
from navigator.widgets.directory_tree import DirectoryTree    # manager.nml:7
from navigator.widgets.panel import Panel    # manager.nml:8
from navml.widgets.layout.horizontal_layout import HorizontalLayout    # manager.nml:9
from navml.widgets.window import Window    # manager.nml:10

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
    #: handler in ``manager.py`` is disabled, and greyed on the bar.  The
    #: modified keys below them are the bar's Alt, Ctrl and Shift rows, in
    #: ``StatusDef hcFilePanel``'s order, which is the order the bar shows the
    #: letters in.
    keys = {    # manager.nml:42
        'tab': SwitchPanel,    # manager.nml:43
        'ctrl+enter': InsertName,    # manager.nml:44
        'alt+enter': InsertName,    # manager.nml:45
        'ctrl+shift+enter': InsertPath,    # manager.nml:46
        'alt+shift+enter': InsertPath,    # manager.nml:47
        'f2': UserMenu,    # manager.nml:48
        'f3': View,# manager.nml:49
        'f4': Edit,# manager.nml:50
        'f5': Copy,# manager.nml:51
        'f6': RenameMove,    # manager.nml:52
        'f7': MakeDirectory,    # manager.nml:53
        'f8': Delete,    # manager.nml:54
        'alt+b': SortBy,    # manager.nml:55
        'alt+c': ChangeDrive,    # manager.nml:56
        'alt+s': PanelSetup,    # manager.nml:57
        'alt+l': MakeList,    # manager.nml:58
        'alt+f6': FastRename,    # manager.nml:59
        'alt+f7': FindFile,    # manager.nml:60
        'alt+r': Rescan,    # manager.nml:61
        'alt+t': ChangeDirectory,    # manager.nml:62
        'ctrl+f6': Calculator,    # manager.nml:63
        'ctrl+f9': PrintFile,    # manager.nml:64
        'ctrl+k': ToggleDescriptions,    # manager.nml:65
        'ctrl+l': DiskInfo,    # manager.nml:66
        'ctrl+t': ToggleTree,    # manager.nml:67
        'ctrl+q': QuickView,    # manager.nml:68
        'ctrl+y': ToggleShowMode,    # manager.nml:69
        'ctrl+r': Rescan,    # manager.nml:70
        'shift+f1': ArchiveFiles,    # manager.nml:71
        'shift+f2': ExtractArchive,    # manager.nml:72
        'shift+f3': PhoneBook,    # manager.nml:73
        'shift+f4': EditNamed,    # manager.nml:74
        'shift+f5': SplitCombine,    # manager.nml:75
        'shift+f6': Reanimate,    # manager.nml:76
        'shift+f8': DeleteSingle,    # manager.nml:77
    }

    #: Ids, annotated so the hand-written half completes them.
    panels: HorizontalLayout    # manager.nml:80
    left: Panel    # manager.nml:87
    right: Panel    # manager.nml:91
    tree: DirectoryTree    # manager.nml:98

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_left_execute_file(self, event: _Event) -> bool:    # manager.nml:87
        """``left`` raised an event whose handler is ``on_execute_file``."""
        return False

    async def on_right_execute_file(self, event: _Event) -> bool:    # manager.nml:91
        """``right`` raised an event whose handler is ``on_execute_file``."""
        return False

    async def on_tree_chosen(self, event: _Event) -> bool:    # manager.nml:98
        """``tree`` raised an event whose handler is ``on_chosen``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.panels = HorizontalLayout(parent=self)    # manager.nml:79
        self.left = Panel(parent=self.panels)    # manager.nml:86
        self.right = Panel(parent=self.panels)    # manager.nml:90
        self.tree = DirectoryTree(parent=self.panels)    # manager.nml:97

        self.zoomed = True    # manager.nml:30
        self.min_width = 24    # manager.nml:31
        self.min_height = 5    # manager.nml:32

        self.panels.x = 0    # manager.nml:81
        self.panels.y = 0    # manager.nml:82
        self.panels.width = _bind(lambda _o: _o.parent.width)    # manager.nml:83
        self.panels.height = _bind(lambda _o: _o.parent.height)    # manager.nml:84

        self.left.title_margin = 5    # manager.nml:88
        self.left.on_execute_file = self.on_left_execute_file    # manager.nml:87

        self.right.title_margin = 5    # manager.nml:92
        self.right.on_execute_file = self.on_right_execute_file    # manager.nml:91

        self.tree.on_chosen = self.on_tree_chosen    # manager.nml:98
