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
from navigator.widgets.manager.commands import AlternateEdit, AlternateView, AdvancedFilter, ArchiveFiles, DirHistory, ListOfDirs, Calculator, ChangeAttributes, ChangeDirectory, ChangeInactive, GoToFile    # manager.nml:1
from navigator.widgets.manager.commands import ChangeDrive, ChangeLeft, ChangeRight, CompareDir, Copy, CountLength, Delete, DeleteSingle, DirBranch, DiskInfo, Edit    # manager.nml:2
from navigator.widgets.manager.commands import ArcTest, EditNamed, ExtractArchive, ExtractTo, FastRename, FindFile, HideInactive, MoveSeparator    # manager.nml:3
from navigator.widgets.manager.commands import InvertSelection, MakeDirectory, MakeLink, MakeList, PanelSetup    # manager.nml:4
from navigator.widgets.manager.commands import PrintFile, QuickRename, QuickView, ReadFileList, RenameMove, Rescan, Panelize, MultiRename, UndoMultiRename    # manager.nml:5
from navigator.widgets.manager.commands import SelectGroup, SetupColumns, SortBy, SwapPanels, SwitchPanel, EqualizePanels, ToggleMiller    # manager.nml:6
from navigator.widgets.manager.commands import ToggleHidden, ToggleInfoLines, ToggleMark, ToggleShowMode, ToggleTree    # manager.nml:7
from navigator.widgets.manager.commands import UnselectGroup, UserMenu, UuDecode, UuEncode, View    # manager.nml:8
from navigator.widgets.shell.commands import InsertName, InsertPath, ToggleMarkBySpace    # manager.nml:9
from navml.widgets.dialog.commands import QuickSearch    # manager.nml:10
from navigator.widgets.tree.directory_tree import DirectoryTree    # manager.nml:11
from navigator.widgets.viewer.quick_viewer import QuickViewer    # manager.nml:12
from navigator.widgets.manager.info_panel import InfoPanel    # manager.nml:13
from navigator.widgets.manager.miller import MillerView    # manager.nml:14
from navigator.widgets.manager.panel import Panel    # manager.nml:15
from navml.widgets.layout.horizontal_layout import HorizontalLayout    # manager.nml:16
from navml.widgets.menu.menu_item import MenuItem    # manager.nml:17
from navml.widgets.menu.menu_line import MenuLine    # manager.nml:18
from navml.widgets.menu.sub_menu import SubMenu    # manager.nml:19
from navml.widgets.window import Window    # manager.nml:20

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
    keys = {    # manager.nml:54
        'tab': SwitchPanel,    # manager.nml:55
        'insert': ToggleMark,    # manager.nml:56
        'space': ToggleMarkBySpace,    # manager.nml:57
        'ctrl+enter': InsertName,    # manager.nml:58
        'alt+enter': InsertName,    # manager.nml:59
        'ctrl+shift+enter': InsertPath,    # manager.nml:60
        'alt+shift+enter': InsertPath,    # manager.nml:61
        'f2': UserMenu,    # manager.nml:62
        'f3': View,# manager.nml:63
        'f4': Edit,# manager.nml:64
        'alt+f3': AlternateView,    # manager.nml:65
        'alt+f4': AlternateEdit,    # manager.nml:66
        'f5': Copy,# manager.nml:67
        'f6': RenameMove,    # manager.nml:68
        'f7': MakeDirectory,    # manager.nml:69
        'f8': Delete,    # manager.nml:70
        'alt+b': SortBy,    # manager.nml:71
        'alt+c': ChangeDrive,    # manager.nml:72
        'alt+f1': ChangeLeft,    # manager.nml:73
        'alt+f2': ChangeRight,    # manager.nml:74
        'alt+s': PanelSetup,    # manager.nml:75
        'alt+l': MakeList,    # manager.nml:76
        'alt+f6': FastRename,    # manager.nml:77
        'shift+f6': QuickRename,    # manager.nml:78
        'alt+f7': FindFile,    # manager.nml:79
        'alt+r': Rescan,    # manager.nml:80
        'alt+t': ChangeDirectory,    # manager.nml:81
        'alt+e': ChangeAttributes,    # manager.nml:82
        'ctrl+f6': Calculator,    # manager.nml:83
        'ctrl+f9': PrintFile,    # manager.nml:84
        'ctrl+f7': UuEncode,    # manager.nml:85
        'ctrl+f8': UuDecode,    # manager.nml:86
        'ctrl+l': DiskInfo,    # manager.nml:87
        'ctrl+p': HideInactive,    # manager.nml:88
        'ctrl+u': SwapPanels,    # manager.nml:89
        'alt+f12': ToggleMiller,    # manager.nml:90
        'alt+=': EqualizePanels,    # manager.nml:91
        'alt+g': CountLength,    # manager.nml:92
        'shift+enter': ChangeInactive,    # manager.nml:93
        'alt+v': ReadFileList,    # manager.nml:94
        'alt+y': Panelize,    # manager.nml:95
        'alt+a': MultiRename,    # manager.nml:96
        'alt+k': SetupColumns,    # manager.nml:97
        'alt+delete': AdvancedFilter,    # manager.nml:98
        'alt+backspace': DirHistory,    # manager.nml:99
        'ctrl+t': ToggleTree,    # manager.nml:100
        'ctrl+q': QuickView,    # manager.nml:101
        'ctrl+y': ToggleShowMode,    # manager.nml:102
        'ctrl+h': ToggleHidden,    # manager.nml:103
        'alt+i': ToggleInfoLines,    # manager.nml:104
        'ctrl+r': Rescan,    # manager.nml:105
        'ctrl+s': QuickSearch,    # manager.nml:106
        'shift+f1': ArchiveFiles,    # manager.nml:107
        'shift+f2': ExtractArchive,    # manager.nml:108
        'shift+f4': EditNamed,    # manager.nml:109
        'shift+f5': MakeLink,    # manager.nml:110
        'shift+f8': DeleteSingle,    # manager.nml:111
    }

    #: Ids, annotated so the hand-written half completes them.
    panels: HorizontalLayout    # manager.nml:114
    left: Panel    # manager.nml:121
    right: Panel    # manager.nml:125
    tree: DirectoryTree    # manager.nml:134
    quick: QuickViewer    # manager.nml:140
    info: InfoPanel    # manager.nml:145
    miller: MillerView    # manager.nml:150
    panel_menu: SubMenu    # manager.nml:160

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_left_dropped(self, event: _Event) -> bool:    # manager.nml:121
        """``left`` raised an event whose handler is ``on_dropped``."""
        return False

    async def on_left_execute_file(self, event: _Event) -> bool:    # manager.nml:121
        """``left`` raised an event whose handler is ``on_execute_file``."""
        return False

    async def on_left_open_file(self, event: _Event) -> bool:    # manager.nml:121
        """``left`` raised an event whose handler is ``on_open_file``."""
        return False

    async def on_right_dropped(self, event: _Event) -> bool:    # manager.nml:125
        """``right`` raised an event whose handler is ``on_dropped``."""
        return False

    async def on_right_execute_file(self, event: _Event) -> bool:    # manager.nml:125
        """``right`` raised an event whose handler is ``on_execute_file``."""
        return False

    async def on_right_open_file(self, event: _Event) -> bool:    # manager.nml:125
        """``right`` raised an event whose handler is ``on_open_file``."""
        return False

    async def on_tree_chosen(self, event: _Event) -> bool:    # manager.nml:134
        """``tree`` raised an event whose handler is ``on_chosen``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.panels = HorizontalLayout(parent=self)    # manager.nml:113
        self.left = Panel(parent=self.panels)    # manager.nml:120
        self.right = Panel(parent=self.panels)    # manager.nml:124
        self.tree = DirectoryTree(parent=self.panels)    # manager.nml:133
        self.quick = QuickViewer(parent=self.panels)    # manager.nml:139
        self.info = InfoPanel(parent=self.panels)    # manager.nml:144
        self.miller = MillerView(parent=self.panels)    # manager.nml:149
        self.panel_menu = SubMenu(parent=self)    # manager.nml:159
        _w1 = MenuItem(parent=self.panel_menu)    # manager.nml:163
        _w2 = MenuItem(parent=self.panel_menu)    # manager.nml:167
        _w3 = MenuItem(parent=self.panel_menu)    # manager.nml:172
        _w4 = MenuItem(parent=self.panel_menu)    # manager.nml:176
        _w5 = MenuItem(parent=self.panel_menu)    # manager.nml:179
        _w6 = MenuItem(parent=self.panel_menu)    # manager.nml:183
        _w7 = MenuLine(parent=self.panel_menu)    # manager.nml:186
        _w8 = MenuItem(parent=self.panel_menu)    # manager.nml:188
        _w9 = MenuItem(parent=self.panel_menu)    # manager.nml:192
        _w10 = MenuLine(parent=self.panel_menu)    # manager.nml:195
        _w11 = MenuItem(parent=self.panel_menu)    # manager.nml:200
        _w12 = MenuItem(parent=self.panel_menu)    # manager.nml:204
        _w13 = MenuLine(parent=self.panel_menu)    # manager.nml:207
        _w14 = MenuItem(parent=self.panel_menu)    # manager.nml:208
        _w15 = MenuItem(parent=self.panel_menu)    # manager.nml:212
        _w16 = MenuItem(parent=self.panel_menu)    # manager.nml:216
        _w17 = MenuItem(parent=self.panel_menu)    # manager.nml:220
        _w18 = MenuItem(parent=self.panel_menu)    # manager.nml:224
        _w19 = MenuItem(parent=self.panel_menu)    # manager.nml:228
        _w20 = MenuItem(parent=self.panel_menu)    # manager.nml:234
        _w21 = MenuItem(parent=self.panel_menu)    # manager.nml:238
        _w22 = MenuLine(parent=self.panel_menu)    # manager.nml:242
        _w23 = MenuItem(parent=self.panel_menu)    # manager.nml:243
        _w24 = MenuItem(parent=self.panel_menu)    # manager.nml:247
        _w25 = MenuItem(parent=self.panel_menu)    # manager.nml:251
        _w26 = MenuLine(parent=self.panel_menu)    # manager.nml:255
        _w27 = MenuItem(parent=self.panel_menu)    # manager.nml:256
        _w28 = MenuItem(parent=self.panel_menu)    # manager.nml:260
        _w29 = MenuItem(parent=self.panel_menu)    # manager.nml:264
        _w30 = MenuItem(parent=self.panel_menu)    # manager.nml:268
        _w31 = MenuLine(parent=self.panel_menu)    # manager.nml:272
        _w32 = MenuItem(parent=self.panel_menu)    # manager.nml:273
        _w33 = MenuItem(parent=self.panel_menu)    # manager.nml:277
        _w34 = MenuItem(parent=self.panel_menu)    # manager.nml:281
        _w35 = MenuItem(parent=self.panel_menu)    # manager.nml:285
        _w36 = MenuItem(parent=self.panel_menu)    # manager.nml:289
        _w37 = MenuItem(parent=self.panel_menu)    # manager.nml:295
        _w38 = MenuItem(parent=self.panel_menu)    # manager.nml:299
        _w39 = MenuItem(parent=self.panel_menu)    # manager.nml:303

        self.zoomed = True    # manager.nml:40
        self.min_width = 24    # manager.nml:41
        self.min_height = 5    # manager.nml:42

        self.panels.x = 0    # manager.nml:115
        self.panels.y = 0    # manager.nml:116
        self.panels.width = _bind(lambda _o: _o.parent.width)    # manager.nml:117
        self.panels.height = _bind(lambda _o: _o.parent.height)    # manager.nml:118

        self.left.title_margin = 5    # manager.nml:122
        self.left.on_dropped = self.on_left_dropped    # manager.nml:121
        self.left.on_execute_file = self.on_left_execute_file    # manager.nml:121
        self.left.on_open_file = self.on_left_open_file    # manager.nml:121

        self.right.title_margin = 5    # manager.nml:126
        self.right.on_dropped = self.on_right_dropped    # manager.nml:125
        self.right.on_execute_file = self.on_right_execute_file    # manager.nml:125
        self.right.on_open_file = self.on_right_open_file    # manager.nml:125

        self.tree.type_to_search = False    # manager.nml:135
        self.tree.on_chosen = self.on_tree_chosen    # manager.nml:134

        self.quick.title_margin = 5    # manager.nml:141

        self.panel_menu.text = _bind(lambda _o: _tr('~P~anel'), yielding=True)    # manager.nml:161
        self.panel_menu.after = 'Utilities'    # manager.nml:162

        _w1.text = _bind(lambda _o: _tr('~M~ake list file...'), yielding=True)    # manager.nml:164
        _w1.command = MakeList    # manager.nml:165
        _w1.key = 'Alt-L'    # manager.nml:166

        _w2.text = _bind(lambda _o: _tr('Read file ~l~ist'), yielding=True)    # manager.nml:168
        _w2.command = ReadFileList    # manager.nml:169
        _w2.key = 'Alt-V'    # manager.nml:170

        _w3.text = _bind(    # manager.nml:173
            lambda _o: _tr('Paneli~z~e command...'),
            yielding=True,
        )
        _w3.command = Panelize    # manager.nml:174
        _w3.key = 'Alt-Y'    # manager.nml:175

        _w4.text = _bind(    # manager.nml:177
            lambda _o: _tr('~C~ompare directories'),
            yielding=True,
        )
        _w4.command = CompareDir    # manager.nml:178

        _w5.text = _bind(    # manager.nml:180
            lambda _o: _tr('Count directory len~g~th'),
            yielding=True,
        )
        _w5.command = CountLength    # manager.nml:181
        _w5.key = 'Alt-G'    # manager.nml:182

        _w6.text = _bind(lambda _o: _tr('Directory Branc~h~'), yielding=True)    # manager.nml:184
        _w6.command = DirBranch    # manager.nml:185

        _w8.text = _bind(lambda _o: _tr('Multi-rename...'), yielding=True)    # manager.nml:189
        _w8.command = MultiRename    # manager.nml:190
        _w8.key = 'Alt-A'    # manager.nml:191

        _w9.text = _bind(lambda _o: _tr('Undo multi-rename'), yielding=True)    # manager.nml:193
        _w9.command = UndoMultiRename    # manager.nml:194

        _w11.text = _bind(lambda _o: _tr('E~x~tract to...'), yielding=True)    # manager.nml:201
        _w11.command = ExtractTo    # manager.nml:202
        _w11.key = 'Shift-F2'    # manager.nml:203

        _w12.text = _bind(lambda _o: _tr('Test archive'), yielding=True)    # manager.nml:205
        _w12.command = ArcTest    # manager.nml:206

        _w14.text = _bind(lambda _o: _tr('Setup c~o~lumns'), yielding=True)    # manager.nml:209
        _w14.command = SetupColumns    # manager.nml:210
        _w14.key = 'Alt-K'    # manager.nml:211

        _w15.text = _bind(lambda _o: _tr('~S~etup Panel'), yielding=True)    # manager.nml:213
        _w15.command = PanelSetup    # manager.nml:214
        _w15.key = 'Alt-S'    # manager.nml:215

        _w16.text = _bind(lambda _o: _tr('Sort ~b~y...'), yielding=True)    # manager.nml:217
        _w16.command = SortBy    # manager.nml:218
        _w16.key = 'Alt-B'    # manager.nml:219

        _w17.text = _bind(lambda _o: _tr('Vie~w~ mode'), yielding=True)    # manager.nml:221
        _w17.command = ToggleShowMode    # manager.nml:222
        _w17.key = 'Ctrl-Y'    # manager.nml:223

        _w18.text = _bind(    # manager.nml:225
            lambda _o: _tr('Show/hide h~i~dden files'),
            yielding=True,
        )
        _w18.command = ToggleHidden    # manager.nml:226
        _w18.key = 'Ctrl-H'    # manager.nml:227

        _w19.text = _bind(lambda _o: _tr('Show/hide ~f~ooter'), yielding=True)    # manager.nml:229
        _w19.command = ToggleInfoLines    # manager.nml:230
        _w19.key = 'Alt-I'    # manager.nml:231

        _w20.text = _bind(lambda _o: _tr('Move divider left'), yielding=True)    # manager.nml:235
        _w20.command = MoveSeparator(step=-1)    # manager.nml:236
        _w20.key = 'Alt-Left'    # manager.nml:237

        _w21.text = _bind(lambda _o: _tr('Move divider right'), yielding=True)    # manager.nml:239
        _w21.command = MoveSeparator(step=1)    # manager.nml:240
        _w21.key = 'Alt-Right'    # manager.nml:241

        _w23.text = _bind(lambda _o: _tr('Director~y~ tree'), yielding=True)    # manager.nml:244
        _w23.command = ToggleTree    # manager.nml:245
        _w23.key = 'Ctrl-T'    # manager.nml:246

        _w24.text = _bind(lambda _o: _tr('I~n~fo'), yielding=True)    # manager.nml:248
        _w24.command = DiskInfo    # manager.nml:249
        _w24.key = 'Ctrl-L'    # manager.nml:250

        _w25.text = _bind(lambda _o: _tr('Quic~k~ view'), yielding=True)    # manager.nml:252
        _w25.command = QuickView    # manager.nml:253
        _w25.key = 'Ctrl-Q'    # manager.nml:254

        _w27.text = _bind(lambda _o: _tr('Select grou~p~...'), yielding=True)    # manager.nml:257
        _w27.command = SelectGroup    # manager.nml:258
        _w27.key = 'Gray "+"'    # manager.nml:259

        _w28.text = _bind(lambda _o: _tr('~U~nselect group...'), yielding=True)    # manager.nml:261
        _w28.command = UnselectGroup    # manager.nml:262
        _w28.key = 'Gray "-"'    # manager.nml:263

        _w29.text = _bind(lambda _o: _tr('In~v~ert selection'), yielding=True)    # manager.nml:265
        _w29.command = InvertSelection    # manager.nml:266
        _w29.key = 'Gray "*"'    # manager.nml:267

        _w30.text = _bind(lambda _o: _tr('Advanced filter...'), yielding=True)    # manager.nml:269
        _w30.command = AdvancedFilter    # manager.nml:270
        _w30.key = 'Alt-Del'    # manager.nml:271

        _w32.text = _bind(lambda _o: _tr('Change ~d~rive'), yielding=True)    # manager.nml:274
        _w32.command = ChangeDrive    # manager.nml:275
        _w32.key = 'Alt-C'    # manager.nml:276

        _w33.text = _bind(lambda _o: _tr('Change direc~t~ory'), yielding=True)    # manager.nml:278
        _w33.command = ChangeDirectory    # manager.nml:279
        _w33.key = 'Alt-T'    # manager.nml:280

        _w34.text = _bind(lambda _o: _tr('Quick s~e~arch'), yielding=True)    # manager.nml:282
        _w34.command = QuickSearch    # manager.nml:283
        _w34.key = 'Ctrl-S'    # manager.nml:284

        _w35.text = _bind(lambda _o: _tr('~R~e-read'), yielding=True)    # manager.nml:286
        _w35.command = Rescan    # manager.nml:287
        _w35.key = 'Alt-R'    # manager.nml:288

        _w36.text = _bind(    # manager.nml:290
            lambda _o: _tr('S~a~me directory in other panel'),
            yielding=True,
        )
        _w36.command = EqualizePanels    # manager.nml:291
        _w36.key = 'Alt-='    # manager.nml:292

        _w37.text = _bind(lambda _o: _tr('Show in other panel'), yielding=True)    # manager.nml:296
        _w37.command = ChangeInactive    # manager.nml:297
        _w37.key = 'Shift-Enter'    # manager.nml:298

        _w38.text = _bind(lambda _o: _tr('~Q~uick dirs...'), yielding=True)    # manager.nml:300
        _w38.command = ListOfDirs    # manager.nml:301
        _w38.key = 'Alt-Shift-0'    # manager.nml:302

        _w39.text = _bind(    # manager.nml:304
            lambda _o: _tr('History of directories...'),
            yielding=True,
        )
        _w39.command = DirHistory    # manager.nml:305
        _w39.key = 'Alt-BkSp'    # manager.nml:306
