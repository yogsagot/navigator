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
from navigator.widgets.manager.commands import EnterWithoutArchive, ChangeDrive, ChangeLeft, ChangeRight, CompareDir, Copy, CountLength, Delete, DeleteSingle, DirBranch, DiskInfo, Edit, FindDuplicates    # manager.nml:2
from navigator.widgets.manager.commands import ArcTest, EditNamed, ExtractArchive, ExtractTo, FastRename, FindFile, ReplaceInFiles, HideInactive, MoveSeparator    # manager.nml:3
from navigator.widgets.manager.commands import InvertSelection, MakeDirectory, MakeLink, MakeList, PanelSetup    # manager.nml:4
from navigator.widgets.manager.commands import RememberDirectory, RememberedDirectories    # manager.nml:5
from navigator.widgets.manager.commands import PrintFile, QuickRename, QuickView, ReadFileList, RenameMove, Rescan, Panelize, MultiRename    # manager.nml:6
from navigator.widgets.manager.commands import SelectAll, SelectGroup, SetupColumns, SortBy, SwapPanels, SwitchPanel, EqualizePanels, ToggleMiller    # manager.nml:7
from navigator.widgets.manager.commands import ToggleHidden, ToggleInfoLines, ToggleMark, ToggleShowMode, ToggleTree    # manager.nml:8
from navigator.widgets.manager.commands import UnselectGroup, UserMenu, UuDecode, UuEncode, View    # manager.nml:9
from navigator.widgets.shell.commands import InsertName, InsertPath, ToggleMarkBySpace    # manager.nml:10
from navml.widgets.dialog.commands import QuickSearch    # manager.nml:11
from navigator.widgets.tree.directory_tree import DirectoryTree    # manager.nml:12
from navigator.widgets.viewer.quick_viewer import QuickViewer    # manager.nml:13
from navigator.widgets.manager.info_panel import InfoPanel    # manager.nml:14
from navigator.widgets.manager.miller import MillerView    # manager.nml:15
from navigator.widgets.manager.panel import Panel    # manager.nml:16
from navml.widgets.layout.horizontal_layout import HorizontalLayout    # manager.nml:17
from navml.widgets.menu.menu_item import MenuItem    # manager.nml:18
from navml.widgets.menu.menu_line import MenuLine    # manager.nml:19
from navml.widgets.menu.sub_menu import SubMenu    # manager.nml:20
from navml.widgets.window import Window    # manager.nml:21

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
    #: (*Reanimator*) can never mean anything on POSIX.  Alt+I, DN's second
    #: (uncaptioned) ``cmDiskInfo``, is the footer toggle here (below).
    keys = {    # manager.nml:56
        'tab': SwitchPanel,    # manager.nml:57
        'insert': ToggleMark,    # manager.nml:58
        'space': ToggleMarkBySpace,    # manager.nml:59
        'ctrl+enter': InsertName,    # manager.nml:60
        'alt+enter': InsertName,    # manager.nml:61
        'ctrl+shift+enter': InsertPath,    # manager.nml:62
        'alt+shift+enter': InsertPath,    # manager.nml:63
        'f2': UserMenu,    # manager.nml:64
        'f3': View,# manager.nml:65
        'f4': Edit,# manager.nml:66
        'alt+f3': AlternateView,    # manager.nml:67
        'ctrl+k': AlternateEdit,    # manager.nml:70
        'alt+f4': AlternateEdit,    # manager.nml:71
        'f5': Copy,# manager.nml:72
        'f6': RenameMove,    # manager.nml:73
        'f7': MakeDirectory,    # manager.nml:74
        'f8': Delete,    # manager.nml:75
        'alt+b': SortBy,    # manager.nml:76
        'alt+c': ChangeDrive,    # manager.nml:77
        'alt+f1': ChangeLeft,    # manager.nml:80
        'alt+f2': ChangeRight,    # manager.nml:81
        'alt+shift+f1': ChangeLeft(focus=True),    # manager.nml:82
        'alt+shift+f2': ChangeRight(focus=True),    # manager.nml:83
        'alt+s': PanelSetup,    # manager.nml:84
        'alt+l': MakeList,    # manager.nml:85
        'alt+f6': FastRename,    # manager.nml:86
        'shift+f6': QuickRename,    # manager.nml:87
        'alt+f7': FindFile,    # manager.nml:88
        'alt+shift+f7': ReplaceInFiles,    # manager.nml:89
        'alt+r': Rescan,    # manager.nml:90
        'alt+t': ChangeDirectory,    # manager.nml:91
        'alt+e': ChangeAttributes,    # manager.nml:92
        'ctrl+f6': Calculator,    # manager.nml:93
        'ctrl+f9': PrintFile,    # manager.nml:94
        'ctrl+f7': UuEncode,    # manager.nml:95
        'ctrl+f8': UuDecode,    # manager.nml:96
        'ctrl+l': DiskInfo,    # manager.nml:97
        'ctrl+p': HideInactive,    # manager.nml:98
        'ctrl+u': SwapPanels,    # manager.nml:99
        'alt+f12': ToggleMiller,    # manager.nml:100
        'alt+=': EqualizePanels,    # manager.nml:101
        'alt+g': CountLength,    # manager.nml:102
        'shift+enter': EnterWithoutArchive,    # manager.nml:105
        'alt+v': ReadFileList,    # manager.nml:106
        'alt+y': Panelize,    # manager.nml:107
        'alt+a': MultiRename,    # manager.nml:108
        'alt+k': SetupColumns,    # manager.nml:109
        'alt+delete': AdvancedFilter,    # manager.nml:110
        'alt+backspace': DirHistory,    # manager.nml:111
        'alt+j': JumpToDirectory,    # manager.nml:112
        'ctrl+t': ToggleTree,    # manager.nml:113
        'ctrl+q': QuickView,    # manager.nml:114
        'ctrl+y': ToggleShowMode,    # manager.nml:115
        'ctrl+h': ToggleHidden,    # manager.nml:116
        'alt+i': ToggleInfoLines,    # manager.nml:121
        'ctrl+r': Rescan,    # manager.nml:122
        'ctrl+s': QuickSearch,    # manager.nml:123
        'shift+f1': ArchiveFiles,    # manager.nml:124
        'shift+f2': ExtractArchive,    # manager.nml:125
        'shift+f4': EditNamed,    # manager.nml:126
        'shift+f5': MakeLink,    # manager.nml:127
        'shift+f8': DeleteSingle,    # manager.nml:128
    }

    #: Ids, annotated so the hand-written half completes them.
    panels: HorizontalLayout    # manager.nml:131
    left: Panel    # manager.nml:138
    right: Panel    # manager.nml:142
    tree: DirectoryTree    # manager.nml:151
    quick: QuickViewer    # manager.nml:157
    info: InfoPanel    # manager.nml:162
    miller: MillerView    # manager.nml:167
    panel_menu: SubMenu    # manager.nml:184
    panel_display: SubMenu    # manager.nml:236
    panel_remember: SubMenu    # manager.nml:254
    panel_select: SubMenu    # manager.nml:277
    panel_other: SubMenu    # manager.nml:304

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_left_dropped(self, event: _Event) -> bool:    # manager.nml:138
        """``left`` raised an event whose handler is ``on_dropped``."""
        return False

    async def on_left_execute_file(self, event: _Event) -> bool:    # manager.nml:138
        """``left`` raised an event whose handler is ``on_execute_file``."""
        return False

    async def on_left_open_file(self, event: _Event) -> bool:    # manager.nml:138
        """``left`` raised an event whose handler is ``on_open_file``."""
        return False

    async def on_right_dropped(self, event: _Event) -> bool:    # manager.nml:142
        """``right`` raised an event whose handler is ``on_dropped``."""
        return False

    async def on_right_execute_file(self, event: _Event) -> bool:    # manager.nml:142
        """``right`` raised an event whose handler is ``on_execute_file``."""
        return False

    async def on_right_open_file(self, event: _Event) -> bool:    # manager.nml:142
        """``right`` raised an event whose handler is ``on_open_file``."""
        return False

    async def on_tree_chosen(self, event: _Event) -> bool:    # manager.nml:151
        """``tree`` raised an event whose handler is ``on_chosen``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.panels = HorizontalLayout(parent=self)    # manager.nml:130
        self.left = Panel(parent=self.panels)    # manager.nml:137
        self.right = Panel(parent=self.panels)    # manager.nml:141
        self.tree = DirectoryTree(parent=self.panels)    # manager.nml:150
        self.quick = QuickViewer(parent=self.panels)    # manager.nml:156
        self.info = InfoPanel(parent=self.panels)    # manager.nml:161
        self.miller = MillerView(parent=self.panels)    # manager.nml:166
        self.panel_menu = SubMenu(parent=self)    # manager.nml:183
        _w1 = MenuItem(parent=self.panel_menu)    # manager.nml:188
        _w2 = MenuItem(parent=self.panel_menu)    # manager.nml:193
        _w3 = MenuItem(parent=self.panel_menu)    # manager.nml:199
        _w4 = MenuItem(parent=self.panel_menu)    # manager.nml:204
        _w5 = MenuItem(parent=self.panel_menu)    # manager.nml:208
        _w6 = MenuItem(parent=self.panel_menu)    # manager.nml:213
        _w7 = MenuItem(parent=self.panel_menu)    # manager.nml:218
        _w8 = MenuLine(parent=self.panel_menu)    # manager.nml:222
        _w9 = MenuItem(parent=self.panel_menu)    # manager.nml:223
        _w10 = MenuItem(parent=self.panel_menu)    # manager.nml:227
        _w11 = MenuItem(parent=self.panel_menu)    # manager.nml:231
        self.panel_display = SubMenu(parent=self.panel_menu)    # manager.nml:235
        _w12 = MenuItem(parent=self.panel_display)    # manager.nml:239
        _w13 = MenuItem(parent=self.panel_display)    # manager.nml:243
        _w14 = MenuItem(parent=self.panel_display)    # manager.nml:247
        self.panel_remember = SubMenu(parent=self.panel_display)    # manager.nml:253
        _w15 = MenuItem(parent=self.panel_remember)    # manager.nml:257
        _w16 = MenuItem(parent=self.panel_remember)    # manager.nml:261
        _w17 = MenuLine(parent=self.panel_display)    # manager.nml:265
        _w18 = MenuItem(parent=self.panel_display)    # manager.nml:268
        _w19 = MenuItem(parent=self.panel_display)    # manager.nml:272
        self.panel_select = SubMenu(parent=self.panel_menu)    # manager.nml:276
        _w20 = MenuItem(parent=self.panel_select)    # manager.nml:280
        _w21 = MenuItem(parent=self.panel_select)    # manager.nml:284
        _w22 = MenuItem(parent=self.panel_select)    # manager.nml:288
        _w23 = MenuItem(parent=self.panel_select)    # manager.nml:292
        _w24 = MenuLine(parent=self.panel_select)    # manager.nml:297
        _w25 = MenuItem(parent=self.panel_select)    # manager.nml:298
        self.panel_other = SubMenu(parent=self.panel_menu)    # manager.nml:303
        _w26 = MenuItem(parent=self.panel_other)    # manager.nml:307
        _w27 = MenuItem(parent=self.panel_other)    # manager.nml:311
        _w28 = MenuItem(parent=self.panel_other)    # manager.nml:316
        _w29 = MenuLine(parent=self.panel_other)    # manager.nml:321
        _w30 = MenuItem(parent=self.panel_other)    # manager.nml:322
        _w31 = MenuItem(parent=self.panel_other)    # manager.nml:329
        _w32 = MenuLine(parent=self.panel_menu)    # manager.nml:334
        _w33 = MenuItem(parent=self.panel_menu)    # manager.nml:335
        _w34 = MenuItem(parent=self.panel_menu)    # manager.nml:340
        _w35 = MenuItem(parent=self.panel_menu)    # manager.nml:346
        _w36 = MenuItem(parent=self.panel_menu)    # manager.nml:351
        _w37 = MenuItem(parent=self.panel_menu)    # manager.nml:355
        _w38 = MenuItem(parent=self.panel_menu)    # manager.nml:359
        _w39 = MenuItem(parent=self.panel_menu)    # manager.nml:364

        self.zoomed = True    # manager.nml:41
        self.min_width = 24    # manager.nml:42
        self.min_height = 5    # manager.nml:43

        self.panels.x = 0    # manager.nml:132
        self.panels.y = 0    # manager.nml:133
        self.panels.width = _bind(lambda _o: _o.parent.width)    # manager.nml:134
        self.panels.height = _bind(lambda _o: _o.parent.height)    # manager.nml:135

        self.left.title_margin = 5    # manager.nml:139
        self.left.on_dropped = self.on_left_dropped    # manager.nml:138
        self.left.on_execute_file = self.on_left_execute_file    # manager.nml:138
        self.left.on_open_file = self.on_left_open_file    # manager.nml:138

        self.right.title_margin = 5    # manager.nml:143
        self.right.on_dropped = self.on_right_dropped    # manager.nml:142
        self.right.on_execute_file = self.on_right_execute_file    # manager.nml:142
        self.right.on_open_file = self.on_right_open_file    # manager.nml:142

        self.tree.type_to_search = False    # manager.nml:152
        self.tree.on_chosen = self.on_tree_chosen    # manager.nml:151

        self.quick.title_margin = 5    # manager.nml:158

        self.panel_menu.text = _bind(lambda _o: _tr('~P~anel'), yielding=True)    # manager.nml:185
        self.panel_menu.tooltip = _bind(    # manager.nml:186
            lambda _o: _tr('List files, compare, sort, filter, select and change directory'),
            yielding=True,
        )
        self.panel_menu.after = 'Utilities'    # manager.nml:187

        _w1.text = _bind(lambda _o: _tr('~M~ake list file...'), yielding=True)    # manager.nml:189
        _w1.tooltip = _bind(    # manager.nml:190
            lambda _o: _tr("Write the tagged files' names to a list file"),
            yielding=True,
        )
        _w1.command = MakeList    # manager.nml:191
        _w1.key = 'Alt-L'    # manager.nml:192

        _w2.text = _bind(lambda _o: _tr('Read file ~l~ist'), yielding=True)    # manager.nml:194
        _w2.tooltip = _bind(    # manager.nml:195
            lambda _o: _tr('Show the files a list file names as a listing'),
            yielding=True,
        )
        _w2.command = ReadFileList    # manager.nml:196
        _w2.key = 'Alt-V'    # manager.nml:197

        _w3.text = _bind(    # manager.nml:200
            lambda _o: _tr('Paneli~z~e command...'),
            yielding=True,
        )
        _w3.tooltip = _bind(    # manager.nml:201
            lambda _o: _tr('Run a command and list the files it prints in the panel'),
            yielding=True,
        )
        _w3.command = Panelize    # manager.nml:202
        _w3.key = 'Alt-Y'    # manager.nml:203

        _w4.text = _bind(    # manager.nml:205
            lambda _o: _tr('~C~ompare directories'),
            yielding=True,
        )
        _w4.tooltip = _bind(    # manager.nml:206
            lambda _o: _tr('Tag what each panel has that the other lacks or has older'),
            yielding=True,
        )
        _w4.command = CompareDir    # manager.nml:207

        _w5.text = _bind(    # manager.nml:209
            lambda _o: _tr('Count directory len~g~th'),
            yielding=True,
        )
        _w5.tooltip = _bind(    # manager.nml:210
            lambda _o: _tr('Add up the bytes under the selected directories'),
            yielding=True,
        )
        _w5.command = CountLength    # manager.nml:211
        _w5.key = 'Alt-G'    # manager.nml:212

        _w6.text = _bind(lambda _o: _tr('Directory Branc~h~'), yielding=True)    # manager.nml:214
        _w6.tooltip = _bind(    # manager.nml:215
            lambda _o: _tr('Every file below this directory in one listing'),
            yielding=True,
        )
        _w6.command = DirBranch    # manager.nml:216

        _w7.text = _bind(lambda _o: _tr('Find duplicates...'), yielding=True)    # manager.nml:219
        _w7.tooltip = _bind(    # manager.nml:220
            lambda _o: _tr('List the files below this directory whose contents are the same'),
            yielding=True,
        )
        _w7.command = FindDuplicates    # manager.nml:221

        _w9.text = _bind(lambda _o: _tr('Setup c~o~lumns'), yielding=True)    # manager.nml:224
        _w9.command = SetupColumns    # manager.nml:225
        _w9.key = 'Alt-K'    # manager.nml:226

        _w10.text = _bind(lambda _o: _tr('~S~etup Panel'), yielding=True)    # manager.nml:228
        _w10.command = PanelSetup    # manager.nml:229
        _w10.key = 'Alt-S'    # manager.nml:230

        _w11.text = _bind(lambda _o: _tr('Sort ~b~y...'), yielding=True)    # manager.nml:232
        _w11.command = SortBy    # manager.nml:233
        _w11.key = 'Alt-B'    # manager.nml:234

        self.panel_display.text = _bind(    # manager.nml:237
            lambda _o: _tr('D~i~splay'),
            yielding=True,
        )
        self.panel_display.tooltip = _bind(    # manager.nml:238
            lambda _o: _tr('View mode, hidden files, the footer, directory settings and the divider'),
            yielding=True,
        )

        _w12.text = _bind(lambda _o: _tr('Vie~w~ mode'), yielding=True)    # manager.nml:240
        _w12.command = ToggleShowMode    # manager.nml:241
        _w12.key = 'Ctrl-Y'    # manager.nml:242

        _w13.text = _bind(    # manager.nml:244
            lambda _o: _tr('Show/hide h~i~dden files'),
            yielding=True,
        )
        _w13.command = ToggleHidden    # manager.nml:245
        _w13.key = 'Ctrl-H'    # manager.nml:246

        _w14.text = _bind(lambda _o: _tr('Show/hide ~f~ooter'), yielding=True)    # manager.nml:248
        _w14.command = ToggleInfoLines    # manager.nml:249
        _w14.key = 'Alt-I'    # manager.nml:250

        self.panel_remember.text = _bind(    # manager.nml:255
            lambda _o: _tr('Director~y~ settings'),
            yielding=True,
        )
        self.panel_remember.tooltip = _bind(    # manager.nml:256
            lambda _o: _tr('Remember the sort order, view and file mask for a directory, and the list of those remembered'),
            yielding=True,
        )

        _w15.text = _bind(    # manager.nml:258
            lambda _o: _tr('Remember ~f~or this directory'),
            yielding=True,
        )
        _w15.tooltip = _bind(    # manager.nml:259
            lambda _o: _tr('Keep the sort order, view, columns and file mask shown for this directory'),
            yielding=True,
        )
        _w15.command = RememberDirectory    # manager.nml:260

        _w16.text = _bind(    # manager.nml:262
            lambda _o: _tr('Remembered director~y~ list...'),
            yielding=True,
        )
        _w16.tooltip = _bind(    # manager.nml:263
            lambda _o: _tr('The directories with settings of their own: go to one, or forget it'),
            yielding=True,
        )
        _w16.command = RememberedDirectories    # manager.nml:264

        _w18.text = _bind(lambda _o: _tr('Move divider left'), yielding=True)    # manager.nml:269
        _w18.command = MoveSeparator(step=-1)    # manager.nml:270
        _w18.key = 'Alt-Left'    # manager.nml:271

        _w19.text = _bind(lambda _o: _tr('Move divider right'), yielding=True)    # manager.nml:273
        _w19.command = MoveSeparator(step=1)    # manager.nml:274
        _w19.key = 'Alt-Right'    # manager.nml:275

        self.panel_select.text = _bind(    # manager.nml:278
            lambda _o: _tr('Selectio~n~'),
            yielding=True,
        )
        self.panel_select.tooltip = _bind(    # manager.nml:279
            lambda _o: _tr('Select or unselect files by a mask, or filter them'),
            yielding=True,
        )

        _w20.text = _bind(lambda _o: _tr('Select grou~p~...'), yielding=True)    # manager.nml:281
        _w20.command = SelectGroup    # manager.nml:282
        _w20.key = 'Gray "+"'    # manager.nml:283

        _w21.text = _bind(lambda _o: _tr('~U~nselect group...'), yielding=True)    # manager.nml:285
        _w21.command = UnselectGroup    # manager.nml:286
        _w21.key = 'Gray "-"'    # manager.nml:287

        _w22.text = _bind(lambda _o: _tr('In~v~ert selection'), yielding=True)    # manager.nml:289
        _w22.command = InvertSelection    # manager.nml:290
        _w22.key = 'Gray "*"'    # manager.nml:291

        _w23.text = _bind(lambda _o: _tr('Select all files'), yielding=True)    # manager.nml:293
        _w23.tooltip = _bind(    # manager.nml:294
            lambda _o: _tr('Select every file and directory in this panel'),
            yielding=True,
        )
        _w23.command = SelectAll    # manager.nml:295
        _w23.key = 'Ctrl-A'    # manager.nml:296

        _w25.text = _bind(lambda _o: _tr('Advanced filter...'), yielding=True)    # manager.nml:299
        _w25.tooltip = _bind(    # manager.nml:300
            lambda _o: _tr('Show or hide files by extension'),
            yielding=True,
        )
        _w25.command = AdvancedFilter    # manager.nml:301
        _w25.key = 'Alt-Del'    # manager.nml:302

        self.panel_other.text = _bind(    # manager.nml:305
            lambda _o: _tr('Other ~p~anel'),
            yielding=True,
        )
        self.panel_other.tooltip = _bind(    # manager.nml:306
            lambda _o: _tr('Put a tree, information or a preview in the other panel'),
            yielding=True,
        )

        _w26.text = _bind(lambda _o: _tr('Director~y~ tree'), yielding=True)    # manager.nml:308
        _w26.command = ToggleTree    # manager.nml:309
        _w26.key = 'Ctrl-T'    # manager.nml:310

        _w27.text = _bind(lambda _o: _tr('I~n~fo'), yielding=True)    # manager.nml:312
        _w27.tooltip = _bind(    # manager.nml:313
            lambda _o: _tr('Disk and directory information in the other panel'),
            yielding=True,
        )
        _w27.command = DiskInfo    # manager.nml:314
        _w27.key = 'Ctrl-L'    # manager.nml:315

        _w28.text = _bind(lambda _o: _tr('Quic~k~ view'), yielding=True)    # manager.nml:317
        _w28.tooltip = _bind(    # manager.nml:318
            lambda _o: _tr('Preview the file at the cursor in the other panel'),
            yielding=True,
        )
        _w28.command = QuickView    # manager.nml:319
        _w28.key = 'Ctrl-Q'    # manager.nml:320

        _w30.text = _bind(    # manager.nml:323
            lambda _o: _tr('S~a~me directory in other panel'),
            yielding=True,
        )
        _w30.tooltip = _bind(    # manager.nml:324
            lambda _o: _tr('Send the other panel to this directory'),
            yielding=True,
        )
        _w30.command = EqualizePanels    # manager.nml:325
        _w30.key = 'Alt-='    # manager.nml:326

        _w31.text = _bind(lambda _o: _tr('Show in other panel'), yielding=True)    # manager.nml:330
        _w31.tooltip = _bind(    # manager.nml:331
            lambda _o: _tr('Show the found file in the other panel'),
            yielding=True,
        )
        _w31.command = ChangeInactive    # manager.nml:332
        _w31.key = 'Shift-Enter'    # manager.nml:333

        _w33.text = _bind(lambda _o: _tr('Change ~d~rive'), yielding=True)    # manager.nml:336
        _w33.tooltip = _bind(    # manager.nml:337
            lambda _o: _tr('Send this panel to a bookmarked directory'),
            yielding=True,
        )
        _w33.command = ChangeDrive    # manager.nml:338
        _w33.key = 'Alt-C'    # manager.nml:339

        _w34.text = _bind(lambda _o: _tr('Change direc~t~ory'), yielding=True)    # manager.nml:341
        _w34.tooltip = _bind(    # manager.nml:342
            lambda _o: _tr('Choose a directory from a tree'),
            yielding=True,
        )
        _w34.command = ChangeDirectory    # manager.nml:343
        _w34.key = 'Alt-T'    # manager.nml:344

        _w35.text = _bind(    # manager.nml:347
            lambda _o: _tr('~J~ump to directory...'),
            yielding=True,
        )
        _w35.tooltip = _bind(    # manager.nml:348
            lambda _o: _tr("zoxide's directories and the panels' history, searched by fzf"),
            yielding=True,
        )
        _w35.command = JumpToDirectory    # manager.nml:349
        _w35.key = 'Alt-J'    # manager.nml:350

        _w36.text = _bind(lambda _o: _tr('Quick s~e~arch'), yielding=True)    # manager.nml:352
        _w36.command = QuickSearch    # manager.nml:353
        _w36.key = 'Ctrl-S'    # manager.nml:354

        _w37.text = _bind(lambda _o: _tr('~R~e-read'), yielding=True)    # manager.nml:356
        _w37.command = Rescan    # manager.nml:357
        _w37.key = 'Alt-R'    # manager.nml:358

        _w38.text = _bind(lambda _o: _tr('~Q~uick dirs...'), yielding=True)    # manager.nml:360
        _w38.tooltip = _bind(    # manager.nml:361
            lambda _o: _tr('The bookmarks, for this panel'),
            yielding=True,
        )
        _w38.command = ListOfDirs    # manager.nml:362
        _w38.key = 'Alt-Shift-0'    # manager.nml:363

        _w39.text = _bind(    # manager.nml:365
            lambda _o: _tr('History of directories...'),
            yielding=True,
        )
        _w39.command = DirHistory    # manager.nml:366
        _w39.key = 'Alt-BkSp'    # manager.nml:367
