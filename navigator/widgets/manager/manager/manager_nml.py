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
from navigator.widgets.manager.commands import AlternateEdit, AlternateView, AdvancedFilter, ArchiveFiles, DirHistory, JumpToDirectory, ListOfDirs, Calculator, ChangeAttributes, ChangeDirectory, ChangeInactive, GoToFile    # manager.nml:1
from navigator.widgets.manager.commands import ChangeDrive, ChangeLeft, ChangeRight, CompareDir, Copy, CountLength, Delete, DeleteSingle, DirBranch, DiskInfo, Edit, FindDuplicates    # manager.nml:2
from navigator.widgets.manager.commands import ArcTest, EditNamed, ExtractArchive, ExtractTo, FastRename, FindFile, HideInactive, MoveSeparator    # manager.nml:3
from navigator.widgets.manager.commands import InvertSelection, MakeDirectory, MakeLink, MakeList, PanelSetup    # manager.nml:4
from navigator.widgets.manager.commands import PrintFile, QuickRename, QuickView, ReadFileList, RenameMove, Rescan, Panelize, MultiRename, UndoMultiRename    # manager.nml:5
from navigator.widgets.manager.commands import SelectAll, SelectGroup, SetupColumns, SortBy, SwapPanels, SwitchPanel, EqualizePanels, ToggleMiller    # manager.nml:6
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
        'ctrl+k': AlternateEdit,    # manager.nml:68
        'alt+f4': AlternateEdit,    # manager.nml:69
        'f5': Copy,# manager.nml:70
        'f6': RenameMove,    # manager.nml:71
        'f7': MakeDirectory,    # manager.nml:72
        'f8': Delete,    # manager.nml:73
        'alt+b': SortBy,    # manager.nml:74
        'alt+c': ChangeDrive,    # manager.nml:75
        'alt+f1': ChangeLeft,    # manager.nml:76
        'alt+f2': ChangeRight,    # manager.nml:77
        'alt+s': PanelSetup,    # manager.nml:78
        'alt+l': MakeList,    # manager.nml:79
        'alt+f6': FastRename,    # manager.nml:80
        'shift+f6': QuickRename,    # manager.nml:81
        'alt+f7': FindFile,    # manager.nml:82
        'alt+r': Rescan,    # manager.nml:83
        'alt+t': ChangeDirectory,    # manager.nml:84
        'alt+e': ChangeAttributes,    # manager.nml:85
        'ctrl+f6': Calculator,    # manager.nml:86
        'ctrl+f9': PrintFile,    # manager.nml:87
        'ctrl+f7': UuEncode,    # manager.nml:88
        'ctrl+f8': UuDecode,    # manager.nml:89
        'ctrl+l': DiskInfo,    # manager.nml:90
        'ctrl+p': HideInactive,    # manager.nml:91
        'ctrl+u': SwapPanels,    # manager.nml:92
        'alt+f12': ToggleMiller,    # manager.nml:93
        'alt+=': EqualizePanels,    # manager.nml:94
        'alt+g': CountLength,    # manager.nml:95
        'shift+enter': ChangeInactive,    # manager.nml:96
        'alt+v': ReadFileList,    # manager.nml:97
        'alt+y': Panelize,    # manager.nml:98
        'alt+a': MultiRename,    # manager.nml:99
        'alt+k': SetupColumns,    # manager.nml:100
        'alt+delete': AdvancedFilter,    # manager.nml:101
        'alt+backspace': DirHistory,    # manager.nml:102
        'alt+j': JumpToDirectory,    # manager.nml:103
        'ctrl+t': ToggleTree,    # manager.nml:104
        'ctrl+q': QuickView,    # manager.nml:105
        'ctrl+y': ToggleShowMode,    # manager.nml:106
        'ctrl+h': ToggleHidden,    # manager.nml:107
        'alt+i': ToggleInfoLines,    # manager.nml:108
        'ctrl+r': Rescan,    # manager.nml:109
        'ctrl+s': QuickSearch,    # manager.nml:110
        'shift+f1': ArchiveFiles,    # manager.nml:111
        'shift+f2': ExtractArchive,    # manager.nml:112
        'shift+f4': EditNamed,    # manager.nml:113
        'shift+f5': MakeLink,    # manager.nml:114
        'shift+f8': DeleteSingle,    # manager.nml:115
    }

    #: Ids, annotated so the hand-written half completes them.
    panels: HorizontalLayout    # manager.nml:118
    left: Panel    # manager.nml:125
    right: Panel    # manager.nml:129
    tree: DirectoryTree    # manager.nml:138
    quick: QuickViewer    # manager.nml:144
    info: InfoPanel    # manager.nml:149
    miller: MillerView    # manager.nml:154
    panel_menu: SubMenu    # manager.nml:164

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_left_dropped(self, event: _Event) -> bool:    # manager.nml:125
        """``left`` raised an event whose handler is ``on_dropped``."""
        return False

    async def on_left_execute_file(self, event: _Event) -> bool:    # manager.nml:125
        """``left`` raised an event whose handler is ``on_execute_file``."""
        return False

    async def on_left_open_file(self, event: _Event) -> bool:    # manager.nml:125
        """``left`` raised an event whose handler is ``on_open_file``."""
        return False

    async def on_right_dropped(self, event: _Event) -> bool:    # manager.nml:129
        """``right`` raised an event whose handler is ``on_dropped``."""
        return False

    async def on_right_execute_file(self, event: _Event) -> bool:    # manager.nml:129
        """``right`` raised an event whose handler is ``on_execute_file``."""
        return False

    async def on_right_open_file(self, event: _Event) -> bool:    # manager.nml:129
        """``right`` raised an event whose handler is ``on_open_file``."""
        return False

    async def on_tree_chosen(self, event: _Event) -> bool:    # manager.nml:138
        """``tree`` raised an event whose handler is ``on_chosen``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.panels = HorizontalLayout(parent=self)    # manager.nml:117
        self.left = Panel(parent=self.panels)    # manager.nml:124
        self.right = Panel(parent=self.panels)    # manager.nml:128
        self.tree = DirectoryTree(parent=self.panels)    # manager.nml:137
        self.quick = QuickViewer(parent=self.panels)    # manager.nml:143
        self.info = InfoPanel(parent=self.panels)    # manager.nml:148
        self.miller = MillerView(parent=self.panels)    # manager.nml:153
        self.panel_menu = SubMenu(parent=self)    # manager.nml:163
        _w1 = MenuItem(parent=self.panel_menu)    # manager.nml:168
        _w2 = MenuItem(parent=self.panel_menu)    # manager.nml:173
        _w3 = MenuItem(parent=self.panel_menu)    # manager.nml:179
        _w4 = MenuItem(parent=self.panel_menu)    # manager.nml:184
        _w5 = MenuItem(parent=self.panel_menu)    # manager.nml:188
        _w6 = MenuItem(parent=self.panel_menu)    # manager.nml:193
        _w7 = MenuItem(parent=self.panel_menu)    # manager.nml:199
        _w8 = MenuLine(parent=self.panel_menu)    # manager.nml:203
        _w9 = MenuItem(parent=self.panel_menu)    # manager.nml:205
        _w10 = MenuItem(parent=self.panel_menu)    # manager.nml:210
        _w11 = MenuLine(parent=self.panel_menu)    # manager.nml:214
        _w12 = MenuItem(parent=self.panel_menu)    # manager.nml:219
        _w13 = MenuItem(parent=self.panel_menu)    # manager.nml:223
        _w14 = MenuLine(parent=self.panel_menu)    # manager.nml:227
        _w15 = MenuItem(parent=self.panel_menu)    # manager.nml:228
        _w16 = MenuItem(parent=self.panel_menu)    # manager.nml:232
        _w17 = MenuItem(parent=self.panel_menu)    # manager.nml:236
        _w18 = MenuItem(parent=self.panel_menu)    # manager.nml:240
        _w19 = MenuItem(parent=self.panel_menu)    # manager.nml:244
        _w20 = MenuItem(parent=self.panel_menu)    # manager.nml:248
        _w21 = MenuItem(parent=self.panel_menu)    # manager.nml:254
        _w22 = MenuItem(parent=self.panel_menu)    # manager.nml:258
        _w23 = MenuLine(parent=self.panel_menu)    # manager.nml:262
        _w24 = MenuItem(parent=self.panel_menu)    # manager.nml:263
        _w25 = MenuItem(parent=self.panel_menu)    # manager.nml:267
        _w26 = MenuItem(parent=self.panel_menu)    # manager.nml:272
        _w27 = MenuLine(parent=self.panel_menu)    # manager.nml:277
        _w28 = MenuItem(parent=self.panel_menu)    # manager.nml:278
        _w29 = MenuItem(parent=self.panel_menu)    # manager.nml:282
        _w30 = MenuItem(parent=self.panel_menu)    # manager.nml:286
        _w31 = MenuItem(parent=self.panel_menu)    # manager.nml:290
        _w32 = MenuItem(parent=self.panel_menu)    # manager.nml:295
        _w33 = MenuLine(parent=self.panel_menu)    # manager.nml:300
        _w34 = MenuItem(parent=self.panel_menu)    # manager.nml:301
        _w35 = MenuItem(parent=self.panel_menu)    # manager.nml:306
        _w36 = MenuItem(parent=self.panel_menu)    # manager.nml:311
        _w37 = MenuItem(parent=self.panel_menu)    # manager.nml:315
        _w38 = MenuItem(parent=self.panel_menu)    # manager.nml:319
        _w39 = MenuItem(parent=self.panel_menu)    # manager.nml:326
        _w40 = MenuItem(parent=self.panel_menu)    # manager.nml:331
        _w41 = MenuItem(parent=self.panel_menu)    # manager.nml:336
        _w42 = MenuItem(parent=self.panel_menu)    # manager.nml:341

        self.zoomed = True    # manager.nml:40
        self.min_width = 24    # manager.nml:41
        self.min_height = 5    # manager.nml:42

        self.panels.x = 0    # manager.nml:119
        self.panels.y = 0    # manager.nml:120
        self.panels.width = _bind(lambda _o: _o.parent.width)    # manager.nml:121
        self.panels.height = _bind(lambda _o: _o.parent.height)    # manager.nml:122

        self.left.title_margin = 5    # manager.nml:126
        self.left.on_dropped = self.on_left_dropped    # manager.nml:125
        self.left.on_execute_file = self.on_left_execute_file    # manager.nml:125
        self.left.on_open_file = self.on_left_open_file    # manager.nml:125

        self.right.title_margin = 5    # manager.nml:130
        self.right.on_dropped = self.on_right_dropped    # manager.nml:129
        self.right.on_execute_file = self.on_right_execute_file    # manager.nml:129
        self.right.on_open_file = self.on_right_open_file    # manager.nml:129

        self.tree.type_to_search = False    # manager.nml:139
        self.tree.on_chosen = self.on_tree_chosen    # manager.nml:138

        self.quick.title_margin = 5    # manager.nml:145

        self.panel_menu.text = _bind(lambda _o: _tr('~P~anel'), yielding=True)    # manager.nml:165
        self.panel_menu.tooltip = _bind(    # manager.nml:166
            lambda _o: _tr('List files, compare, sort, filter, select and change directory'),
            yielding=True,
        )
        self.panel_menu.after = 'Utilities'    # manager.nml:167

        _w1.text = _bind(lambda _o: _tr('~M~ake list file...'), yielding=True)    # manager.nml:169
        _w1.tooltip = _bind(    # manager.nml:170
            lambda _o: _tr("Write the tagged files' names to a list file"),
            yielding=True,
        )
        _w1.command = MakeList    # manager.nml:171
        _w1.key = 'Alt-L'    # manager.nml:172

        _w2.text = _bind(lambda _o: _tr('Read file ~l~ist'), yielding=True)    # manager.nml:174
        _w2.tooltip = _bind(    # manager.nml:175
            lambda _o: _tr('Show the files a list file names as a listing'),
            yielding=True,
        )
        _w2.command = ReadFileList    # manager.nml:176
        _w2.key = 'Alt-V'    # manager.nml:177

        _w3.text = _bind(    # manager.nml:180
            lambda _o: _tr('Paneli~z~e command...'),
            yielding=True,
        )
        _w3.tooltip = _bind(    # manager.nml:181
            lambda _o: _tr('Run a command and list the files it prints in the panel'),
            yielding=True,
        )
        _w3.command = Panelize    # manager.nml:182
        _w3.key = 'Alt-Y'    # manager.nml:183

        _w4.text = _bind(    # manager.nml:185
            lambda _o: _tr('~C~ompare directories'),
            yielding=True,
        )
        _w4.tooltip = _bind(    # manager.nml:186
            lambda _o: _tr('Tag what each panel has that the other lacks or has older'),
            yielding=True,
        )
        _w4.command = CompareDir    # manager.nml:187

        _w5.text = _bind(    # manager.nml:189
            lambda _o: _tr('Count directory len~g~th'),
            yielding=True,
        )
        _w5.tooltip = _bind(    # manager.nml:190
            lambda _o: _tr('Add up the bytes under the selected directories'),
            yielding=True,
        )
        _w5.command = CountLength    # manager.nml:191
        _w5.key = 'Alt-G'    # manager.nml:192

        _w6.text = _bind(lambda _o: _tr('Directory Branc~h~'), yielding=True)    # manager.nml:194
        _w6.tooltip = _bind(    # manager.nml:195
            lambda _o: _tr('Every file below this directory in one listing'),
            yielding=True,
        )
        _w6.command = DirBranch    # manager.nml:196

        _w7.text = _bind(lambda _o: _tr('Find duplicates...'), yielding=True)    # manager.nml:200
        _w7.tooltip = _bind(    # manager.nml:201
            lambda _o: _tr('List the files below this directory whose contents are the same'),
            yielding=True,
        )
        _w7.command = FindDuplicates    # manager.nml:202

        _w9.text = _bind(lambda _o: _tr('Multi-rename...'), yielding=True)    # manager.nml:206
        _w9.tooltip = _bind(    # manager.nml:207
            lambda _o: _tr('Rename the tagged files by a pattern'),
            yielding=True,
        )
        _w9.command = MultiRename    # manager.nml:208
        _w9.key = 'Alt-A'    # manager.nml:209

        _w10.text = _bind(lambda _o: _tr('Undo multi-rename'), yielding=True)    # manager.nml:211
        _w10.tooltip = _bind(    # manager.nml:212
            lambda _o: _tr('Put back the names the last multi-rename changed'),
            yielding=True,
        )
        _w10.command = UndoMultiRename    # manager.nml:213

        _w12.text = _bind(lambda _o: _tr('E~x~tract to...'), yielding=True)    # manager.nml:220
        _w12.command = ExtractTo    # manager.nml:221
        _w12.key = 'Shift-F2'    # manager.nml:222

        _w13.text = _bind(lambda _o: _tr('Test archive'), yielding=True)    # manager.nml:224
        _w13.tooltip = _bind(    # manager.nml:225
            lambda _o: _tr('Read the archive through and check it for errors'),
            yielding=True,
        )
        _w13.command = ArcTest    # manager.nml:226

        _w15.text = _bind(lambda _o: _tr('Setup c~o~lumns'), yielding=True)    # manager.nml:229
        _w15.command = SetupColumns    # manager.nml:230
        _w15.key = 'Alt-K'    # manager.nml:231

        _w16.text = _bind(lambda _o: _tr('~S~etup Panel'), yielding=True)    # manager.nml:233
        _w16.command = PanelSetup    # manager.nml:234
        _w16.key = 'Alt-S'    # manager.nml:235

        _w17.text = _bind(lambda _o: _tr('Sort ~b~y...'), yielding=True)    # manager.nml:237
        _w17.command = SortBy    # manager.nml:238
        _w17.key = 'Alt-B'    # manager.nml:239

        _w18.text = _bind(lambda _o: _tr('Vie~w~ mode'), yielding=True)    # manager.nml:241
        _w18.command = ToggleShowMode    # manager.nml:242
        _w18.key = 'Ctrl-Y'    # manager.nml:243

        _w19.text = _bind(    # manager.nml:245
            lambda _o: _tr('Show/hide h~i~dden files'),
            yielding=True,
        )
        _w19.command = ToggleHidden    # manager.nml:246
        _w19.key = 'Ctrl-H'    # manager.nml:247

        _w20.text = _bind(lambda _o: _tr('Show/hide ~f~ooter'), yielding=True)    # manager.nml:249
        _w20.command = ToggleInfoLines    # manager.nml:250
        _w20.key = 'Alt-I'    # manager.nml:251

        _w21.text = _bind(lambda _o: _tr('Move divider left'), yielding=True)    # manager.nml:255
        _w21.command = MoveSeparator(step=-1)    # manager.nml:256
        _w21.key = 'Alt-Left'    # manager.nml:257

        _w22.text = _bind(lambda _o: _tr('Move divider right'), yielding=True)    # manager.nml:259
        _w22.command = MoveSeparator(step=1)    # manager.nml:260
        _w22.key = 'Alt-Right'    # manager.nml:261

        _w24.text = _bind(lambda _o: _tr('Director~y~ tree'), yielding=True)    # manager.nml:264
        _w24.command = ToggleTree    # manager.nml:265
        _w24.key = 'Ctrl-T'    # manager.nml:266

        _w25.text = _bind(lambda _o: _tr('I~n~fo'), yielding=True)    # manager.nml:268
        _w25.tooltip = _bind(    # manager.nml:269
            lambda _o: _tr('Disk and directory information in the other panel'),
            yielding=True,
        )
        _w25.command = DiskInfo    # manager.nml:270
        _w25.key = 'Ctrl-L'    # manager.nml:271

        _w26.text = _bind(lambda _o: _tr('Quic~k~ view'), yielding=True)    # manager.nml:273
        _w26.tooltip = _bind(    # manager.nml:274
            lambda _o: _tr('Preview the file at the cursor in the other panel'),
            yielding=True,
        )
        _w26.command = QuickView    # manager.nml:275
        _w26.key = 'Ctrl-Q'    # manager.nml:276

        _w28.text = _bind(lambda _o: _tr('Select grou~p~...'), yielding=True)    # manager.nml:279
        _w28.command = SelectGroup    # manager.nml:280
        _w28.key = 'Gray "+"'    # manager.nml:281

        _w29.text = _bind(lambda _o: _tr('~U~nselect group...'), yielding=True)    # manager.nml:283
        _w29.command = UnselectGroup    # manager.nml:284
        _w29.key = 'Gray "-"'    # manager.nml:285

        _w30.text = _bind(lambda _o: _tr('In~v~ert selection'), yielding=True)    # manager.nml:287
        _w30.command = InvertSelection    # manager.nml:288
        _w30.key = 'Gray "*"'    # manager.nml:289

        _w31.text = _bind(lambda _o: _tr('Select all files'), yielding=True)    # manager.nml:291
        _w31.tooltip = _bind(    # manager.nml:292
            lambda _o: _tr('Select every file and directory in this panel'),
            yielding=True,
        )
        _w31.command = SelectAll    # manager.nml:293
        _w31.key = 'Ctrl-A'    # manager.nml:294

        _w32.text = _bind(lambda _o: _tr('Advanced filter...'), yielding=True)    # manager.nml:296
        _w32.tooltip = _bind(    # manager.nml:297
            lambda _o: _tr('Show or hide files by extension'),
            yielding=True,
        )
        _w32.command = AdvancedFilter    # manager.nml:298
        _w32.key = 'Alt-Del'    # manager.nml:299

        _w34.text = _bind(lambda _o: _tr('Change ~d~rive'), yielding=True)    # manager.nml:302
        _w34.tooltip = _bind(    # manager.nml:303
            lambda _o: _tr('Send this panel to a bookmarked directory'),
            yielding=True,
        )
        _w34.command = ChangeDrive    # manager.nml:304
        _w34.key = 'Alt-C'    # manager.nml:305

        _w35.text = _bind(lambda _o: _tr('Change direc~t~ory'), yielding=True)    # manager.nml:307
        _w35.tooltip = _bind(    # manager.nml:308
            lambda _o: _tr('Choose a directory from a tree'),
            yielding=True,
        )
        _w35.command = ChangeDirectory    # manager.nml:309
        _w35.key = 'Alt-T'    # manager.nml:310

        _w36.text = _bind(lambda _o: _tr('Quick s~e~arch'), yielding=True)    # manager.nml:312
        _w36.command = QuickSearch    # manager.nml:313
        _w36.key = 'Ctrl-S'    # manager.nml:314

        _w37.text = _bind(lambda _o: _tr('~R~e-read'), yielding=True)    # manager.nml:316
        _w37.command = Rescan    # manager.nml:317
        _w37.key = 'Alt-R'    # manager.nml:318

        _w38.text = _bind(    # manager.nml:320
            lambda _o: _tr('S~a~me directory in other panel'),
            yielding=True,
        )
        _w38.tooltip = _bind(    # manager.nml:321
            lambda _o: _tr('Send the other panel to this directory'),
            yielding=True,
        )
        _w38.command = EqualizePanels    # manager.nml:322
        _w38.key = 'Alt-='    # manager.nml:323

        _w39.text = _bind(lambda _o: _tr('Show in other panel'), yielding=True)    # manager.nml:327
        _w39.tooltip = _bind(    # manager.nml:328
            lambda _o: _tr('Show the found file in the other panel'),
            yielding=True,
        )
        _w39.command = ChangeInactive    # manager.nml:329
        _w39.key = 'Shift-Enter'    # manager.nml:330

        _w40.text = _bind(lambda _o: _tr('~Q~uick dirs...'), yielding=True)    # manager.nml:332
        _w40.tooltip = _bind(    # manager.nml:333
            lambda _o: _tr('The bookmarks, for this panel'),
            yielding=True,
        )
        _w40.command = ListOfDirs    # manager.nml:334
        _w40.key = 'Alt-Shift-0'    # manager.nml:335

        _w41.text = _bind(    # manager.nml:337
            lambda _o: _tr('History of directories...'),
            yielding=True,
        )
        _w41.command = DirHistory    # manager.nml:338
        _w41.key = 'Alt-BkSp'    # manager.nml:339

        _w42.text = _bind(    # manager.nml:342
            lambda _o: _tr('~J~ump to directory...'),
            yielding=True,
        )
        _w42.tooltip = _bind(    # manager.nml:343
            lambda _o: _tr("zoxide's directories and the panels' history, searched by fzf"),
            yielding=True,
        )
        _w42.command = JumpToDirectory    # manager.nml:344
        _w42.key = 'Alt-J'    # manager.nml:345
