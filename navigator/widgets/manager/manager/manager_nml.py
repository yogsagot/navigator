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
from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navigator.widgets.manager.commands import AlternateEdit, AlternateView, AdvancedFilter, ArchiveFiles, DirHistory, ListOfDirs, Calculator, ChangeAttributes, ChangeDirectory, ChangeInactive    # manager.nml:1
from navigator.widgets.manager.commands import ChangeDrive, ChangeLeft, ChangeRight, CompareDir, Copy, CountLength, Delete, DeleteSingle, DirBranch, DiskInfo, Edit    # manager.nml:2
from navigator.widgets.manager.commands import EditNamed, ExtractArchive, FastRename, FindFile, HideInactive    # manager.nml:3
from navigator.widgets.manager.commands import InvertSelection, MakeDirectory, MakeLink, MakeList, PanelSetup    # manager.nml:4
from navigator.widgets.manager.commands import PrintFile, QuickRename, QuickView, ReadFileList, RenameMove, Rescan    # manager.nml:5
from navigator.widgets.manager.commands import SelectGroup, SetupColumns, SortBy, SwapPanels, SwitchPanel    # manager.nml:6
from navigator.widgets.manager.commands import ToggleHidden, ToggleInfoLines, ToggleMark, ToggleShowMode, ToggleTree    # manager.nml:7
from navigator.widgets.manager.commands import UnselectGroup, UserMenu, UuDecode, UuEncode, View    # manager.nml:8
from navigator.widgets.shell.commands import InsertName, InsertPath, ToggleMarkBySpace    # manager.nml:9
from navml.widgets.dialog.commands import QuickSearch    # manager.nml:10
from navigator.widgets.tree.directory_tree import DirectoryTree    # manager.nml:11
from navigator.widgets.viewer.quick_viewer import QuickViewer    # manager.nml:12
from navigator.widgets.manager.info_panel import InfoPanel    # manager.nml:13
from navigator.widgets.manager.panel import Panel    # manager.nml:14
from navml.widgets.layout.horizontal_layout import HorizontalLayout    # manager.nml:15
from navml.widgets.menu.menu_item import MenuItem    # manager.nml:16
from navml.widgets.menu.menu_line import MenuLine    # manager.nml:17
from navml.widgets.menu.sub_menu import SubMenu    # manager.nml:18
from navml.widgets.window import Window    # manager.nml:19

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
    keys = {    # manager.nml:53
        'tab': SwitchPanel,    # manager.nml:54
        'insert': ToggleMark,    # manager.nml:55
        'space': ToggleMarkBySpace,    # manager.nml:56
        'ctrl+enter': InsertName,    # manager.nml:57
        'alt+enter': InsertName,    # manager.nml:58
        'ctrl+shift+enter': InsertPath,    # manager.nml:59
        'alt+shift+enter': InsertPath,    # manager.nml:60
        'f2': UserMenu,    # manager.nml:61
        'f3': View,# manager.nml:62
        'f4': Edit,# manager.nml:63
        'alt+f3': AlternateView,    # manager.nml:64
        'alt+f4': AlternateEdit,    # manager.nml:65
        'f5': Copy,# manager.nml:66
        'f6': RenameMove,    # manager.nml:67
        'f7': MakeDirectory,    # manager.nml:68
        'f8': Delete,    # manager.nml:69
        'alt+b': SortBy,    # manager.nml:70
        'alt+c': ChangeDrive,    # manager.nml:71
        'alt+f1': ChangeLeft,    # manager.nml:72
        'alt+f2': ChangeRight,    # manager.nml:73
        'alt+s': PanelSetup,    # manager.nml:74
        'alt+l': MakeList,    # manager.nml:75
        'alt+f6': FastRename,    # manager.nml:76
        'shift+f6': QuickRename,    # manager.nml:77
        'alt+f7': FindFile,    # manager.nml:78
        'alt+r': Rescan,    # manager.nml:79
        'alt+t': ChangeDirectory,    # manager.nml:80
        'alt+e': ChangeAttributes,    # manager.nml:81
        'ctrl+f6': Calculator,    # manager.nml:82
        'ctrl+f9': PrintFile,    # manager.nml:83
        'ctrl+f7': UuEncode,    # manager.nml:84
        'ctrl+f8': UuDecode,    # manager.nml:85
        'ctrl+l': DiskInfo,    # manager.nml:86
        'ctrl+p': HideInactive,    # manager.nml:87
        'ctrl+u': SwapPanels,    # manager.nml:88
        'alt+g': CountLength,    # manager.nml:89
        'shift+enter': ChangeInactive,    # manager.nml:90
        'alt+v': ReadFileList,    # manager.nml:91
        'alt+k': SetupColumns,    # manager.nml:92
        'alt+delete': AdvancedFilter,    # manager.nml:93
        'alt+backspace': DirHistory,    # manager.nml:94
        'ctrl+t': ToggleTree,    # manager.nml:95
        'ctrl+q': QuickView,    # manager.nml:96
        'ctrl+y': ToggleShowMode,    # manager.nml:97
        'ctrl+h': ToggleHidden,    # manager.nml:98
        'alt+i': ToggleInfoLines,    # manager.nml:99
        'ctrl+r': Rescan,    # manager.nml:100
        'ctrl+s': QuickSearch,    # manager.nml:101
        'shift+f1': ArchiveFiles,    # manager.nml:102
        'shift+f2': ExtractArchive,    # manager.nml:103
        'shift+f4': EditNamed,    # manager.nml:104
        'shift+f5': MakeLink,    # manager.nml:105
        'shift+f8': DeleteSingle,    # manager.nml:106
    }

    #: Ids, annotated so the hand-written half completes them.
    panels: HorizontalLayout    # manager.nml:109
    left: Panel    # manager.nml:116
    right: Panel    # manager.nml:120
    tree: DirectoryTree    # manager.nml:129
    quick: QuickViewer    # manager.nml:135
    info: InfoPanel    # manager.nml:140
    panel_menu: SubMenu    # manager.nml:150

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_left_dropped(self, event: _Event) -> bool:    # manager.nml:116
        """``left`` raised an event whose handler is ``on_dropped``."""
        return False

    async def on_left_execute_file(self, event: _Event) -> bool:    # manager.nml:116
        """``left`` raised an event whose handler is ``on_execute_file``."""
        return False

    async def on_left_open_file(self, event: _Event) -> bool:    # manager.nml:116
        """``left`` raised an event whose handler is ``on_open_file``."""
        return False

    async def on_right_dropped(self, event: _Event) -> bool:    # manager.nml:120
        """``right`` raised an event whose handler is ``on_dropped``."""
        return False

    async def on_right_execute_file(self, event: _Event) -> bool:    # manager.nml:120
        """``right`` raised an event whose handler is ``on_execute_file``."""
        return False

    async def on_right_open_file(self, event: _Event) -> bool:    # manager.nml:120
        """``right`` raised an event whose handler is ``on_open_file``."""
        return False

    async def on_tree_chosen(self, event: _Event) -> bool:    # manager.nml:129
        """``tree`` raised an event whose handler is ``on_chosen``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.panels = HorizontalLayout(parent=self)    # manager.nml:108
        self.left = Panel(parent=self.panels)    # manager.nml:115
        self.right = Panel(parent=self.panels)    # manager.nml:119
        self.tree = DirectoryTree(parent=self.panels)    # manager.nml:128
        self.quick = QuickViewer(parent=self.panels)    # manager.nml:134
        self.info = InfoPanel(parent=self.panels)    # manager.nml:139
        self.panel_menu = SubMenu(parent=self)    # manager.nml:149
        _w1 = MenuItem(parent=self.panel_menu)    # manager.nml:153
        _w2 = MenuItem(parent=self.panel_menu)    # manager.nml:157
        _w3 = MenuItem(parent=self.panel_menu)    # manager.nml:161
        _w4 = MenuItem(parent=self.panel_menu)    # manager.nml:164
        _w5 = MenuItem(parent=self.panel_menu)    # manager.nml:168
        _w6 = MenuLine(parent=self.panel_menu)    # manager.nml:171
        _w7 = MenuItem(parent=self.panel_menu)    # manager.nml:172
        _w8 = MenuItem(parent=self.panel_menu)    # manager.nml:176
        _w9 = MenuItem(parent=self.panel_menu)    # manager.nml:180
        _w10 = MenuItem(parent=self.panel_menu)    # manager.nml:184
        _w11 = MenuItem(parent=self.panel_menu)    # manager.nml:188
        _w12 = MenuItem(parent=self.panel_menu)    # manager.nml:192
        _w13 = MenuLine(parent=self.panel_menu)    # manager.nml:196
        _w14 = MenuItem(parent=self.panel_menu)    # manager.nml:197
        _w15 = MenuItem(parent=self.panel_menu)    # manager.nml:201
        _w16 = MenuItem(parent=self.panel_menu)    # manager.nml:205
        _w17 = MenuLine(parent=self.panel_menu)    # manager.nml:209
        _w18 = MenuItem(parent=self.panel_menu)    # manager.nml:210
        _w19 = MenuItem(parent=self.panel_menu)    # manager.nml:214
        _w20 = MenuItem(parent=self.panel_menu)    # manager.nml:218
        _w21 = MenuItem(parent=self.panel_menu)    # manager.nml:222
        _w22 = MenuLine(parent=self.panel_menu)    # manager.nml:226
        _w23 = MenuItem(parent=self.panel_menu)    # manager.nml:227
        _w24 = MenuItem(parent=self.panel_menu)    # manager.nml:231
        _w25 = MenuItem(parent=self.panel_menu)    # manager.nml:235
        _w26 = MenuItem(parent=self.panel_menu)    # manager.nml:239
        _w27 = MenuItem(parent=self.panel_menu)    # manager.nml:243
        _w28 = MenuItem(parent=self.panel_menu)    # manager.nml:247

        self.zoomed = True    # manager.nml:39
        self.min_width = 24    # manager.nml:40
        self.min_height = 5    # manager.nml:41

        self.panels.x = 0    # manager.nml:110
        self.panels.y = 0    # manager.nml:111
        self.panels.width = _bind(lambda _o: _o.parent.width)    # manager.nml:112
        self.panels.height = _bind(lambda _o: _o.parent.height)    # manager.nml:113

        self.left.title_margin = 5    # manager.nml:117
        self.left.on_dropped = self.on_left_dropped    # manager.nml:116
        self.left.on_execute_file = self.on_left_execute_file    # manager.nml:116
        self.left.on_open_file = self.on_left_open_file    # manager.nml:116

        self.right.title_margin = 5    # manager.nml:121
        self.right.on_dropped = self.on_right_dropped    # manager.nml:120
        self.right.on_execute_file = self.on_right_execute_file    # manager.nml:120
        self.right.on_open_file = self.on_right_open_file    # manager.nml:120

        self.tree.type_to_search = False    # manager.nml:130
        self.tree.on_chosen = self.on_tree_chosen    # manager.nml:129

        self.quick.title_margin = 5    # manager.nml:136

        self.panel_menu.text = _bind(lambda _o: _tr('~P~anel'), yielding=True)    # manager.nml:151
        self.panel_menu.after = 'Utilities'    # manager.nml:152

        _w1.text = _bind(lambda _o: _tr('~M~ake list file...'), yielding=True)    # manager.nml:154
        _w1.command = MakeList    # manager.nml:155
        _w1.key = 'Alt-L'    # manager.nml:156

        _w2.text = _bind(lambda _o: _tr('Read file ~l~ist'), yielding=True)    # manager.nml:158
        _w2.command = ReadFileList    # manager.nml:159
        _w2.key = 'Alt-V'    # manager.nml:160

        _w3.text = _bind(    # manager.nml:162
            lambda _o: _tr('~C~ompare directories'),
            yielding=True,
        )
        _w3.command = CompareDir    # manager.nml:163

        _w4.text = _bind(    # manager.nml:165
            lambda _o: _tr('Count directory len~g~th'),
            yielding=True,
        )
        _w4.command = CountLength    # manager.nml:166
        _w4.key = 'Alt-G'    # manager.nml:167

        _w5.text = _bind(lambda _o: _tr('Directory Branc~h~'), yielding=True)    # manager.nml:169
        _w5.command = DirBranch    # manager.nml:170

        _w7.text = _bind(lambda _o: _tr('Setup c~o~lumns'), yielding=True)    # manager.nml:173
        _w7.command = SetupColumns    # manager.nml:174
        _w7.key = 'Alt-K'    # manager.nml:175

        _w8.text = _bind(lambda _o: _tr('~S~etup Panel'), yielding=True)    # manager.nml:177
        _w8.command = PanelSetup    # manager.nml:178
        _w8.key = 'Alt-S'    # manager.nml:179

        _w9.text = _bind(lambda _o: _tr('Sort ~b~y...'), yielding=True)    # manager.nml:181
        _w9.command = SortBy    # manager.nml:182
        _w9.key = 'Alt-B'    # manager.nml:183

        _w10.text = _bind(lambda _o: _tr('Vie~w~ mode'), yielding=True)    # manager.nml:185
        _w10.command = ToggleShowMode    # manager.nml:186
        _w10.key = 'Ctrl-Y'    # manager.nml:187

        _w11.text = _bind(    # manager.nml:189
            lambda _o: _tr('Show/hide h~i~dden files'),
            yielding=True,
        )
        _w11.command = ToggleHidden    # manager.nml:190
        _w11.key = 'Ctrl-H'    # manager.nml:191

        _w12.text = _bind(lambda _o: _tr('Show/hide ~f~ooter'), yielding=True)    # manager.nml:193
        _w12.command = ToggleInfoLines    # manager.nml:194
        _w12.key = 'Alt-I'    # manager.nml:195

        _w14.text = _bind(lambda _o: _tr('Director~y~ tree'), yielding=True)    # manager.nml:198
        _w14.command = ToggleTree    # manager.nml:199
        _w14.key = 'Ctrl-T'    # manager.nml:200

        _w15.text = _bind(lambda _o: _tr('I~n~fo'), yielding=True)    # manager.nml:202
        _w15.command = DiskInfo    # manager.nml:203
        _w15.key = 'Ctrl-L'    # manager.nml:204

        _w16.text = _bind(lambda _o: _tr('Quic~k~ view'), yielding=True)    # manager.nml:206
        _w16.command = QuickView    # manager.nml:207
        _w16.key = 'Ctrl-Q'    # manager.nml:208

        _w18.text = _bind(lambda _o: _tr('Select grou~p~...'), yielding=True)    # manager.nml:211
        _w18.command = SelectGroup    # manager.nml:212
        _w18.key = 'Gray "+"'    # manager.nml:213

        _w19.text = _bind(lambda _o: _tr('~U~nselect group...'), yielding=True)    # manager.nml:215
        _w19.command = UnselectGroup    # manager.nml:216
        _w19.key = 'Gray "-"'    # manager.nml:217

        _w20.text = _bind(lambda _o: _tr('In~v~ert selection'), yielding=True)    # manager.nml:219
        _w20.command = InvertSelection    # manager.nml:220
        _w20.key = 'Gray "*"'    # manager.nml:221

        _w21.text = _bind(lambda _o: _tr('Advanced filter...'), yielding=True)    # manager.nml:223
        _w21.command = AdvancedFilter    # manager.nml:224
        _w21.key = 'Alt-Del'    # manager.nml:225

        _w23.text = _bind(lambda _o: _tr('Change ~d~rive'), yielding=True)    # manager.nml:228
        _w23.command = ChangeDrive    # manager.nml:229
        _w23.key = 'Alt-C'    # manager.nml:230

        _w24.text = _bind(lambda _o: _tr('Change direc~t~ory'), yielding=True)    # manager.nml:232
        _w24.command = ChangeDirectory    # manager.nml:233
        _w24.key = 'Alt-T'    # manager.nml:234

        _w25.text = _bind(lambda _o: _tr('Quick s~e~arch'), yielding=True)    # manager.nml:236
        _w25.command = QuickSearch    # manager.nml:237
        _w25.key = 'Ctrl-S'    # manager.nml:238

        _w26.text = _bind(lambda _o: _tr('~R~e-read'), yielding=True)    # manager.nml:240
        _w26.command = Rescan    # manager.nml:241
        _w26.key = 'Alt-R'    # manager.nml:242

        _w27.text = _bind(lambda _o: _tr('~Q~uick dirs...'), yielding=True)    # manager.nml:244
        _w27.command = ListOfDirs    # manager.nml:245
        _w27.key = 'Alt-Shift-0'    # manager.nml:246

        _w28.text = _bind(    # manager.nml:248
            lambda _o: _tr('History of directories...'),
            yielding=True,
        )
        _w28.command = DirHistory    # manager.nml:249
        _w28.key = 'Alt-BkSp'    # manager.nml:250
