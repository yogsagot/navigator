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
from navigator.widgets.manager.commands import ArchiveFiles, Calculator, ChangeAttributes, ChangeDirectory    # manager.nml:1
from navigator.widgets.manager.commands import ChangeDrive, ChangeLeft, ChangeRight, CompareDir, Copy, CountLength, Delete, DeleteSingle, DiskInfo, Edit    # manager.nml:2
from navigator.widgets.manager.commands import EditNamed, ExtractArchive, FastRename, FindFile, HideInactive    # manager.nml:3
from navigator.widgets.manager.commands import InvertSelection, MakeDirectory, MakeLink, MakeList, PanelSetup    # manager.nml:4
from navigator.widgets.manager.commands import PrintFile, QuickView, RenameMove, Rescan    # manager.nml:5
from navigator.widgets.manager.commands import SelectGroup, SortBy, SwapPanels, SwitchPanel    # manager.nml:6
from navigator.widgets.manager.commands import ToggleHidden, ToggleMark, ToggleShowMode, ToggleTree    # manager.nml:7
from navigator.widgets.manager.commands import UnselectGroup, UserMenu, View    # manager.nml:8
from navigator.widgets.shell.commands import InsertName, InsertPath, ToggleMarkBySpace    # manager.nml:9
from navml.widgets.dialog.commands import QuickSearch    # manager.nml:10
from navigator.widgets.tree.directory_tree import DirectoryTree    # manager.nml:11
from navigator.widgets.viewer.quick_viewer import QuickViewer    # manager.nml:12
from navigator.widgets.manager.panel import Panel    # manager.nml:13
from navml.widgets.layout.horizontal_layout import HorizontalLayout    # manager.nml:14
from navml.widgets.menu.menu_item import MenuItem    # manager.nml:15
from navml.widgets.menu.menu_line import MenuLine    # manager.nml:16
from navml.widgets.menu.sub_menu import SubMenu    # manager.nml:17
from navml.widgets.window import Window    # manager.nml:18

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
    #: letters in.  Three of DN's are not here, a departure: Ctrl+K's ``descript.ion``
    #: descriptions, Shift+F3's modem phone book and Shift+F6's FAT undelete
    #: (*Reanimator*) can never mean anything on POSIX.
    keys = {    # manager.nml:52
        'tab': SwitchPanel,    # manager.nml:53
        'insert': ToggleMark,    # manager.nml:54
        'space': ToggleMarkBySpace,    # manager.nml:55
        'ctrl+enter': InsertName,    # manager.nml:56
        'alt+enter': InsertName,    # manager.nml:57
        'ctrl+shift+enter': InsertPath,    # manager.nml:58
        'alt+shift+enter': InsertPath,    # manager.nml:59
        'f2': UserMenu,    # manager.nml:60
        'f3': View,# manager.nml:61
        'f4': Edit,# manager.nml:62
        'f5': Copy,# manager.nml:63
        'f6': RenameMove,    # manager.nml:64
        'f7': MakeDirectory,    # manager.nml:65
        'f8': Delete,    # manager.nml:66
        'alt+b': SortBy,    # manager.nml:67
        'alt+c': ChangeDrive,    # manager.nml:68
        'alt+f1': ChangeLeft,    # manager.nml:69
        'alt+f2': ChangeRight,    # manager.nml:70
        'alt+s': PanelSetup,    # manager.nml:71
        'alt+l': MakeList,    # manager.nml:72
        'alt+f6': FastRename,    # manager.nml:73
        'alt+f7': FindFile,    # manager.nml:74
        'alt+r': Rescan,    # manager.nml:75
        'alt+t': ChangeDirectory,    # manager.nml:76
        'alt+e': ChangeAttributes,    # manager.nml:77
        'ctrl+f6': Calculator,    # manager.nml:78
        'ctrl+f9': PrintFile,    # manager.nml:79
        'ctrl+l': DiskInfo,    # manager.nml:80
        'ctrl+p': HideInactive,    # manager.nml:81
        'ctrl+u': SwapPanels,    # manager.nml:82
        'alt+g': CountLength,    # manager.nml:83
        'ctrl+t': ToggleTree,    # manager.nml:84
        'ctrl+q': QuickView,    # manager.nml:85
        'ctrl+y': ToggleShowMode,    # manager.nml:86
        'ctrl+h': ToggleHidden,    # manager.nml:87
        'ctrl+r': Rescan,    # manager.nml:88
        'ctrl+s': QuickSearch,    # manager.nml:89
        'shift+f1': ArchiveFiles,    # manager.nml:90
        'shift+f2': ExtractArchive,    # manager.nml:91
        'shift+f4': EditNamed,    # manager.nml:92
        'shift+f5': MakeLink,    # manager.nml:93
        'shift+f8': DeleteSingle,    # manager.nml:94
    }

    #: Ids, annotated so the hand-written half completes them.
    panels: HorizontalLayout    # manager.nml:97
    left: Panel    # manager.nml:104
    right: Panel    # manager.nml:108
    tree: DirectoryTree    # manager.nml:117
    quick: QuickViewer    # manager.nml:123
    panel_menu: SubMenu    # manager.nml:134

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_left_execute_file(self, event: _Event) -> bool:    # manager.nml:104
        """``left`` raised an event whose handler is ``on_execute_file``."""
        return False

    async def on_right_execute_file(self, event: _Event) -> bool:    # manager.nml:108
        """``right`` raised an event whose handler is ``on_execute_file``."""
        return False

    async def on_tree_chosen(self, event: _Event) -> bool:    # manager.nml:117
        """``tree`` raised an event whose handler is ``on_chosen``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.panels = HorizontalLayout(parent=self)    # manager.nml:96
        self.left = Panel(parent=self.panels)    # manager.nml:103
        self.right = Panel(parent=self.panels)    # manager.nml:107
        self.tree = DirectoryTree(parent=self.panels)    # manager.nml:116
        self.quick = QuickViewer(parent=self.panels)    # manager.nml:122
        self.panel_menu = SubMenu(parent=self)    # manager.nml:133
        _w1 = MenuItem(parent=self.panel_menu)    # manager.nml:137
        _w2 = MenuItem(parent=self.panel_menu)    # manager.nml:140
        _w3 = MenuItem(parent=self.panel_menu)    # manager.nml:143
        _w4 = MenuItem(parent=self.panel_menu)    # manager.nml:146
        _w5 = MenuItem(parent=self.panel_menu)    # manager.nml:150
        _w6 = MenuLine(parent=self.panel_menu)    # manager.nml:152
        _w7 = MenuItem(parent=self.panel_menu)    # manager.nml:153
        _w8 = MenuItem(parent=self.panel_menu)    # manager.nml:156
        _w9 = MenuItem(parent=self.panel_menu)    # manager.nml:159
        _w10 = MenuItem(parent=self.panel_menu)    # manager.nml:163
        _w11 = MenuItem(parent=self.panel_menu)    # manager.nml:167
        _w12 = MenuLine(parent=self.panel_menu)    # manager.nml:171
        _w13 = MenuItem(parent=self.panel_menu)    # manager.nml:172
        _w14 = MenuItem(parent=self.panel_menu)    # manager.nml:176
        _w15 = MenuItem(parent=self.panel_menu)    # manager.nml:179
        _w16 = MenuLine(parent=self.panel_menu)    # manager.nml:183
        _w17 = MenuItem(parent=self.panel_menu)    # manager.nml:184
        _w18 = MenuItem(parent=self.panel_menu)    # manager.nml:188
        _w19 = MenuItem(parent=self.panel_menu)    # manager.nml:192
        _w20 = MenuItem(parent=self.panel_menu)    # manager.nml:196
        _w21 = MenuLine(parent=self.panel_menu)    # manager.nml:199
        _w22 = MenuItem(parent=self.panel_menu)    # manager.nml:200
        _w23 = MenuItem(parent=self.panel_menu)    # manager.nml:203
        _w24 = MenuItem(parent=self.panel_menu)    # manager.nml:207
        _w25 = MenuItem(parent=self.panel_menu)    # manager.nml:211
        _w26 = MenuItem(parent=self.panel_menu)    # manager.nml:215
        _w27 = MenuItem(parent=self.panel_menu)    # manager.nml:218

        self.zoomed = True    # manager.nml:38
        self.min_width = 24    # manager.nml:39
        self.min_height = 5    # manager.nml:40

        self.panels.x = 0    # manager.nml:98
        self.panels.y = 0    # manager.nml:99
        self.panels.width = _bind(lambda _o: _o.parent.width)    # manager.nml:100
        self.panels.height = _bind(lambda _o: _o.parent.height)    # manager.nml:101

        self.left.title_margin = 5    # manager.nml:105
        self.left.on_execute_file = self.on_left_execute_file    # manager.nml:104

        self.right.title_margin = 5    # manager.nml:109
        self.right.on_execute_file = self.on_right_execute_file    # manager.nml:108

        self.tree.type_to_search = False    # manager.nml:118
        self.tree.on_chosen = self.on_tree_chosen    # manager.nml:117

        self.quick.title_margin = 5    # manager.nml:124

        self.panel_menu.text = '~P~anel'    # manager.nml:135
        self.panel_menu.after = 'Utilities'    # manager.nml:136

        _w1.text = '~M~ake list file...'    # manager.nml:138
        _w1.key = 'Alt-L'    # manager.nml:139

        _w2.text = 'Read file ~l~ist'    # manager.nml:141
        _w2.key = 'Alt-V'    # manager.nml:142

        _w3.text = '~C~ompare directories'    # manager.nml:144
        _w3.command = CompareDir    # manager.nml:145

        _w4.text = 'Count directory len~g~th'    # manager.nml:147
        _w4.command = CountLength    # manager.nml:148
        _w4.key = 'Alt-G'    # manager.nml:149

        _w5.text = 'Directory Branc~h~'    # manager.nml:151

        _w7.text = 'Setup c~o~lumns'    # manager.nml:154
        _w7.key = 'Alt-K'    # manager.nml:155

        _w8.text = '~S~etup Panel'    # manager.nml:157
        _w8.key = 'Alt-S'    # manager.nml:158

        _w9.text = 'Sort ~b~y...'    # manager.nml:160
        _w9.command = SortBy    # manager.nml:161
        _w9.key = 'Alt-B'    # manager.nml:162

        _w10.text = 'Vie~w~ mode'    # manager.nml:164
        _w10.command = ToggleShowMode    # manager.nml:165
        _w10.key = 'Ctrl-Y'    # manager.nml:166

        _w11.text = 'Show/hide h~i~dden files'    # manager.nml:168
        _w11.command = ToggleHidden    # manager.nml:169
        _w11.key = 'Ctrl-H'    # manager.nml:170

        _w13.text = 'Director~y~ tree'    # manager.nml:173
        _w13.command = ToggleTree    # manager.nml:174
        _w13.key = 'Ctrl-T'    # manager.nml:175

        _w14.text = 'I~n~fo'    # manager.nml:177
        _w14.key = 'Ctrl-L'    # manager.nml:178

        _w15.text = 'Quic~k~ view'    # manager.nml:180
        _w15.command = QuickView    # manager.nml:181
        _w15.key = 'Ctrl-Q'    # manager.nml:182

        _w17.text = 'Select grou~p~...'    # manager.nml:185
        _w17.command = SelectGroup    # manager.nml:186
        _w17.key = 'Gray "+"'    # manager.nml:187

        _w18.text = '~U~nselect group...'    # manager.nml:189
        _w18.command = UnselectGroup    # manager.nml:190
        _w18.key = 'Gray "-"'    # manager.nml:191

        _w19.text = 'In~v~ert selection'    # manager.nml:193
        _w19.command = InvertSelection    # manager.nml:194
        _w19.key = 'Gray "*"'    # manager.nml:195

        _w20.text = 'Advanced filter...'    # manager.nml:197
        _w20.key = 'Alt-Del'    # manager.nml:198

        _w22.text = 'Change ~d~rive'    # manager.nml:201
        _w22.key = 'Alt-C'    # manager.nml:202

        _w23.text = 'Change direc~t~ory'    # manager.nml:204
        _w23.command = ChangeDirectory    # manager.nml:205
        _w23.key = 'Alt-T'    # manager.nml:206

        _w24.text = 'Quick s~e~arch'    # manager.nml:208
        _w24.command = QuickSearch    # manager.nml:209
        _w24.key = 'Ctrl-S'    # manager.nml:210

        _w25.text = '~R~e-read'    # manager.nml:212
        _w25.command = Rescan    # manager.nml:213
        _w25.key = 'Alt-R'    # manager.nml:214

        _w26.text = '~Q~uick dirs...'    # manager.nml:216
        _w26.key = 'Alt-Shift-0'    # manager.nml:217

        _w27.text = 'History of directories...'    # manager.nml:219
        _w27.key = 'Alt-BkSp'    # manager.nml:220
