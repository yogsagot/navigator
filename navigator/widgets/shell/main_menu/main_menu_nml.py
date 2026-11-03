# navml: generated
"""Generated from ``main_menu.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navigator.commands import AsciiTable, OpenSmartpad, PrintFile, Quit, Refresh, ScreenGrab, ShowUserScreen, ToggleConsole    # main_menu.nml:1
from navigator.widgets.manager.commands import RestoreTrash, AlternateEdit, AlternateView, ArchiveFiles, Calculator, ChangeAttributes, ChangeLeft, ChangeRight, Copy, Delete, DeleteSingle, DiffFiles, Edit, EditNamed, ExtractArchive, FindFile, OpenWith, HideInactive, HideLeft, HideRight, MakeDirectory, MakeLink, EditLinkTarget, LinkAbsolute, LinkRelative, SelectBrokenLinks, QuickRename, RenameMove, SwapPanels, ToggleMiller, UserMenu, UuDecode, UuEncode, CalculateChecksums, VerifyChecksums, View, ViewAsDataBase, ViewAsHex, ViewAsSpreadsheet, ViewAsText    # main_menu.nml:2
from navigator.widgets.shell.commands import OpenEdit, OpenView, About, CloseRootAccess, ShowBackground, EditLinks, FtpLink, GvfsLink, S3Link, Game, HangUp, NavyLink, Terminal, SetupLink, SmbLink, SaversSetup, CountrySetup, ScreenRest, ToggleTrashCan, OpenTrash, EmptyTrash, ChangeColors, ColumnDefaults, HighlightGroups, EditQuickRun, ExtFileEdit, EditHGL, EditMacros, ExternalViewers, ExternalEditors, LoadColors, StoreColors, LoadDesktop, SaveDesktop, DriveInfoSetup, EditHistory, EnvEdit, ExecuteOsCommand, HistoryList, FuzzyHistory, OpenCalendar, SystemInfo, EditorDefaults, FileManagerDefaults, FileManagerSetup, InterfaceSetup, KeyBindingsSetup, LocalMenuFileEdit, MenuFileEdit, NewManager, OpenTreeWindow, OpenUsageWindow, OpenVolumesWindow, SetupConfirmation, Settings, StartupSetup, SystemSetup, ViewHistory    # main_menu.nml:3
from navml.commands import CascadeWindows, CloseAllWindows, CloseWindow, NextWindow, PreviousWindow, SizeMoveWindow, TileWindows, WindowManager, ZoomWindow    # main_menu.nml:4
from navml.widgets.menu.menu_bar import MenuBar    # main_menu.nml:5
from navml.widgets.menu.menu_item import MenuItem    # main_menu.nml:6
from navml.widgets.menu.menu_line import MenuLine    # main_menu.nml:7
from navml.widgets.menu.sub_menu import SubMenu    # main_menu.nml:8

__navml_component__ = "MainMenu"

__all__ = ["MainMenu"]


class MainMenu(MenuBar, _Component):
    """DOS Navigator 1.51's main menu, transcribed from ``dlgMainMenu`` in

    ``RESOURCE/ENGLISH/DN.DNR`` -- every entry that has a POSIX meaning, in
    the original's order and with the original's captions and hotkeys.

    Every submenu carries an ``id``, which is how Python reaches it: an id is
    an attribute of the document's class, so a plugin adds to the File menu
    with ``app.shell.menu.file.add_item(...)``.  A nested submenu's id is its
    parent's joined to its own -- ``file_view``, ``options_configuration`` --
    because an id is unique across the whole document.

    An entry names a ``command`` once the feature behind it exists, and is
    greyed until then: an entry with no command is one nobody can run, the
    same rule as a command nobody handles.  ``key`` is the original's caption
    for the entry's key, shown while no key table binds the command; a bound
    key is read off the binding instead.  Giving a feature its entry is one
    ``command:`` line here.

    **Panel is not here**: it acts on a file manager's panels and nothing else,
    so it is the file manager's own menu (``manager.nml``), on the bar only
    while one is the active window.  Manager stays, because *New* has to be
    reachable with no file manager open.  Its *Directory tree*, *Info* and
    *Quick view* went with Panel -- a departure from ``dlgMainMenu``: they put
    something in the passive panel's place, which is a panel's business.

    **What only meant something on DOS is not here either**, a departure from
    the rule that an entry with no feature yet stays greyed: some can never
    have one on POSIX.  Gone are *EGA/VGA lines* and the two *Custom video
    modes*; *Unpack diskette images* (DN's own format); *Format disk*,
    *Volume label*, *Reanimator* (FAT undelete) and *Disk editor* (sectors); *Memory Information* (conventional/XMS/EMS),
    *Phone Book*, *Open spreadsheet*, *CD Player*, and the modem's
    *Manual dial*; *Printer setup*, *Mouse* and *Terminal* under
    Configuration; and the seventeen DOS archivers under Archives, which a
    list of POSIX ones replaces once archives can be opened.
    *View as Spreadsheet* is back as *As Spreadsheet*, for a CSV or TSV file
    where DN's opened its own ``.WKZ``.
    *Navigator Link* (as *SSH link (SFTP)*, named for what is on the wire),
    *Disconnect*, *Communications* and the modem's *Terminal* (as *Remote
    shell*, ``ssh`` to the server a panel is on) are back, for connections to servers
    (``navigator/lib/drives``) where DN's were to a PC on a cable, and
    *Country support* for how dates and times are written.  Two captions say what
    they mean here: *ASCII Table* is *Character table*, and *Edit DOS
    Environment* is *Edit environment*.  *Change drive left/right* are
    *Bookmarks left/right*: the box they open lists bookmarked directories
    where DN's listed drive letters (``navigator/lib/config/bookmarks.py``).  Disk's
    *Volumes* is not DN's: it stands where *Volume label* stood, under its
    letter, and lists every mounted volume (``navigator/lib/system/volumes.py``).
    """

    #: The document this class was generated from.
    __navml_source__ = "main_menu.nml"

    #: Ids, annotated so the hand-written half completes them.
    system: SubMenu    # main_menu.nml:58
    file: SubMenu    # main_menu.nml:103
    file_view: SubMenu    # main_menu.nml:107
    file_edit: SubMenu    # main_menu.nml:143
    file_symlinks: SubMenu    # main_menu.nml:202
    file_restore_trash: MenuItem    # main_menu.nml:249
    file_checksums: SubMenu    # main_menu.nml:272
    disk: SubMenu    # main_menu.nml:297
    utilities: SubMenu    # main_menu.nml:322
    manager: SubMenu    # main_menu.nml:416
    options: SubMenu    # main_menu.nml:459
    options_configuration: SubMenu    # main_menu.nml:470
    options_file_manager: SubMenu    # main_menu.nml:504
    options_archives: SubMenu    # main_menu.nml:526
    window: SubMenu    # main_menu.nml:586

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.system = SubMenu(parent=self)    # main_menu.nml:57
        _w1 = MenuItem(parent=self.system)    # main_menu.nml:61
        _w2 = MenuItem(parent=self.system)    # main_menu.nml:64
        _w3 = MenuItem(parent=self.system)    # main_menu.nml:68
        _w4 = MenuLine(parent=self.system)    # main_menu.nml:72
        _w5 = MenuItem(parent=self.system)    # main_menu.nml:73
        _w6 = MenuItem(parent=self.system)    # main_menu.nml:78
        _w7 = MenuItem(parent=self.system)    # main_menu.nml:83
        _w8 = MenuItem(parent=self.system)    # main_menu.nml:88
        _w9 = MenuItem(parent=self.system)    # main_menu.nml:93
        _w10 = MenuLine(parent=self.system)    # main_menu.nml:97
        _w11 = MenuItem(parent=self.system)    # main_menu.nml:98
        self.file = SubMenu(parent=self)    # main_menu.nml:102
        self.file_view = SubMenu(parent=self.file)    # main_menu.nml:106
        _w12 = MenuItem(parent=self.file_view)    # main_menu.nml:109
        _w13 = MenuItem(parent=self.file_view)    # main_menu.nml:114
        _w14 = MenuItem(parent=self.file_view)    # main_menu.nml:117
        _w15 = MenuItem(parent=self.file_view)    # main_menu.nml:120
        _w16 = MenuItem(parent=self.file_view)    # main_menu.nml:126
        _w17 = MenuLine(parent=self.file_view)    # main_menu.nml:130
        _w18 = MenuItem(parent=self.file_view)    # main_menu.nml:131
        _w19 = MenuLine(parent=self.file_view)    # main_menu.nml:136
        _w20 = MenuItem(parent=self.file_view)    # main_menu.nml:138
        self.file_edit = SubMenu(parent=self.file)    # main_menu.nml:142
        _w21 = MenuItem(parent=self.file_edit)    # main_menu.nml:145
        _w22 = MenuItem(parent=self.file_edit)    # main_menu.nml:149
        _w23 = MenuLine(parent=self.file_edit)    # main_menu.nml:154
        _w24 = MenuItem(parent=self.file_edit)    # main_menu.nml:155
        _w25 = MenuItem(parent=self.file_edit)    # main_menu.nml:160
        _w26 = MenuItem(parent=self.file)    # main_menu.nml:165
        _w27 = MenuItem(parent=self.file)    # main_menu.nml:169
        _w28 = MenuItem(parent=self.file)    # main_menu.nml:173
        _w29 = MenuItem(parent=self.file)    # main_menu.nml:177
        _w30 = MenuItem(parent=self.file)    # main_menu.nml:183
        _w31 = MenuItem(parent=self.file)    # main_menu.nml:191
        _w32 = MenuItem(parent=self.file)    # main_menu.nml:195
        self.file_symlinks = SubMenu(parent=self.file)    # main_menu.nml:201
        _w33 = MenuItem(parent=self.file_symlinks)    # main_menu.nml:204
        _w34 = MenuLine(parent=self.file_symlinks)    # main_menu.nml:209
        _w35 = MenuItem(parent=self.file_symlinks)    # main_menu.nml:210
        _w36 = MenuItem(parent=self.file_symlinks)    # main_menu.nml:214
        _w37 = MenuItem(parent=self.file_symlinks)    # main_menu.nml:218
        _w38 = MenuLine(parent=self.file_symlinks)    # main_menu.nml:222
        _w39 = MenuItem(parent=self.file_symlinks)    # main_menu.nml:223
        _w40 = MenuItem(parent=self.file)    # main_menu.nml:229
        _w41 = MenuItem(parent=self.file)    # main_menu.nml:232
        _w42 = MenuItem(parent=self.file)    # main_menu.nml:236
        _w43 = MenuItem(parent=self.file)    # main_menu.nml:240
        self.file_restore_trash = MenuItem(parent=self.file)    # main_menu.nml:248
        _w44 = MenuItem(parent=self.file)    # main_menu.nml:254
        _w45 = MenuItem(parent=self.file)    # main_menu.nml:259
        _w46 = MenuItem(parent=self.file)    # main_menu.nml:264
        self.file_checksums = SubMenu(parent=self.file)    # main_menu.nml:271
        _w47 = MenuItem(parent=self.file_checksums)    # main_menu.nml:274
        _w48 = MenuItem(parent=self.file_checksums)    # main_menu.nml:278
        _w49 = MenuItem(parent=self.file)    # main_menu.nml:282
        _w50 = MenuLine(parent=self.file)    # main_menu.nml:287
        _w51 = MenuItem(parent=self.file)    # main_menu.nml:288
        _w52 = MenuItem(parent=self.file)    # main_menu.nml:292
        self.disk = SubMenu(parent=self)    # main_menu.nml:296
        _w53 = MenuItem(parent=self.disk)    # main_menu.nml:300
        _w54 = MenuItem(parent=self.disk)    # main_menu.nml:303
        _w55 = MenuItem(parent=self.disk)    # main_menu.nml:308
        _w56 = MenuLine(parent=self.disk)    # main_menu.nml:314
        _w57 = MenuItem(parent=self.disk)    # main_menu.nml:315
        _w58 = MenuItem(parent=self.disk)    # main_menu.nml:318
        self.utilities = SubMenu(parent=self)    # main_menu.nml:321
        _w59 = MenuItem(parent=self.utilities)    # main_menu.nml:325
        _w60 = MenuLine(parent=self.utilities)    # main_menu.nml:328
        _w61 = MenuItem(parent=self.utilities)    # main_menu.nml:329
        _w62 = MenuItem(parent=self.utilities)    # main_menu.nml:335
        _w63 = MenuItem(parent=self.utilities)    # main_menu.nml:338
        _w64 = MenuLine(parent=self.utilities)    # main_menu.nml:343
        _w65 = MenuItem(parent=self.utilities)    # main_menu.nml:352
        _w66 = MenuItem(parent=self.utilities)    # main_menu.nml:356
        _w67 = MenuItem(parent=self.utilities)    # main_menu.nml:359
        _w68 = MenuItem(parent=self.utilities)    # main_menu.nml:362
        _w69 = MenuItem(parent=self.utilities)    # main_menu.nml:366
        _w70 = MenuItem(parent=self.utilities)    # main_menu.nml:371
        _w71 = MenuItem(parent=self.utilities)    # main_menu.nml:375
        _w72 = MenuItem(parent=self.utilities)    # main_menu.nml:380
        _w73 = MenuItem(parent=self.utilities)    # main_menu.nml:384
        _w74 = MenuLine(parent=self.utilities)    # main_menu.nml:388
        _w75 = MenuItem(parent=self.utilities)    # main_menu.nml:389
        _w76 = MenuItem(parent=self.utilities)    # main_menu.nml:393
        _w77 = MenuItem(parent=self.utilities)    # main_menu.nml:397
        _w78 = MenuItem(parent=self.utilities)    # main_menu.nml:402
        _w79 = MenuItem(parent=self.utilities)    # main_menu.nml:407
        _w80 = MenuItem(parent=self.utilities)    # main_menu.nml:411
        self.manager = SubMenu(parent=self)    # main_menu.nml:415
        _w81 = MenuItem(parent=self.manager)    # main_menu.nml:419
        _w82 = MenuItem(parent=self.manager)    # main_menu.nml:423
        _w83 = MenuItem(parent=self.manager)    # main_menu.nml:427
        _w84 = MenuItem(parent=self.manager)    # main_menu.nml:431
        _w85 = MenuItem(parent=self.manager)    # main_menu.nml:435
        _w86 = MenuItem(parent=self.manager)    # main_menu.nml:442
        _w87 = MenuLine(parent=self.manager)    # main_menu.nml:447
        _w88 = MenuItem(parent=self.manager)    # main_menu.nml:448
        _w89 = MenuItem(parent=self.manager)    # main_menu.nml:453
        self.options = SubMenu(parent=self)    # main_menu.nml:458
        _w90 = MenuItem(parent=self.options)    # main_menu.nml:464
        _w91 = MenuLine(parent=self.options)    # main_menu.nml:468
        self.options_configuration = SubMenu(parent=self.options)    # main_menu.nml:469
        _w92 = MenuItem(parent=self.options_configuration)    # main_menu.nml:472
        _w93 = MenuItem(parent=self.options_configuration)    # main_menu.nml:475
        _w94 = MenuItem(parent=self.options_configuration)    # main_menu.nml:478
        _w95 = MenuItem(parent=self.options_configuration)    # main_menu.nml:481
        _w96 = MenuLine(parent=self.options_configuration)    # main_menu.nml:484
        _w97 = MenuItem(parent=self.options_configuration)    # main_menu.nml:485
        _w98 = MenuItem(parent=self.options_configuration)    # main_menu.nml:488
        _w99 = MenuItem(parent=self.options_configuration)    # main_menu.nml:491
        _w100 = MenuLine(parent=self.options_configuration)    # main_menu.nml:495
        _w101 = MenuItem(parent=self.options_configuration)    # main_menu.nml:496
        _w102 = MenuLine(parent=self.options_configuration)    # main_menu.nml:499
        _w103 = MenuItem(parent=self.options_configuration)    # main_menu.nml:500
        self.options_file_manager = SubMenu(parent=self.options)    # main_menu.nml:503
        _w104 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:506
        _w105 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:509
        _w106 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:513
        _w107 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:517
        _w108 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:521
        self.options_archives = SubMenu(parent=self.options)    # main_menu.nml:525
        _w109 = MenuItem(parent=self.options_archives)    # main_menu.nml:528
        _w110 = MenuLine(parent=self.options)    # main_menu.nml:531
        _w111 = MenuItem(parent=self.options)    # main_menu.nml:532
        _w112 = MenuItem(parent=self.options)    # main_menu.nml:536
        _w113 = MenuItem(parent=self.options)    # main_menu.nml:540
        _w114 = MenuItem(parent=self.options)    # main_menu.nml:544
        _w115 = MenuItem(parent=self.options)    # main_menu.nml:548
        _w116 = MenuItem(parent=self.options)    # main_menu.nml:552
        _w117 = MenuItem(parent=self.options)    # main_menu.nml:556
        _w118 = MenuItem(parent=self.options)    # main_menu.nml:560
        _w119 = MenuLine(parent=self.options)    # main_menu.nml:564
        _w120 = MenuItem(parent=self.options)    # main_menu.nml:565
        _w121 = MenuItem(parent=self.options)    # main_menu.nml:569
        _w122 = MenuLine(parent=self.options)    # main_menu.nml:573
        _w123 = MenuItem(parent=self.options)    # main_menu.nml:574
        _w124 = MenuItem(parent=self.options)    # main_menu.nml:577
        _w125 = MenuItem(parent=self.options)    # main_menu.nml:581
        self.window = SubMenu(parent=self)    # main_menu.nml:585
        _w126 = MenuItem(parent=self.window)    # main_menu.nml:589
        _w127 = MenuItem(parent=self.window)    # main_menu.nml:592
        _w128 = MenuItem(parent=self.window)    # main_menu.nml:595
        _w129 = MenuLine(parent=self.window)    # main_menu.nml:598
        _w130 = MenuItem(parent=self.window)    # main_menu.nml:599
        _w131 = MenuItem(parent=self.window)    # main_menu.nml:604
        _w132 = MenuItem(parent=self.window)    # main_menu.nml:608
        _w133 = MenuItem(parent=self.window)    # main_menu.nml:612
        _w134 = MenuItem(parent=self.window)    # main_menu.nml:616
        _w135 = MenuLine(parent=self.window)    # main_menu.nml:620
        _w136 = MenuItem(parent=self.window)    # main_menu.nml:621
        _w137 = MenuItem(parent=self.window)    # main_menu.nml:627

        self.system.text = '~≡~'    # main_menu.nml:59
        self.system.tooltip = _bind(    # main_menu.nml:60
            lambda _o: _tr('About, the screen saver, SmartPad, the Trashcan and the game'),
            yielding=True,
        )

        _w1.text = _bind(lambda _o: _tr('~A~bout...'), yielding=True)    # main_menu.nml:62
        _w1.command = About    # main_menu.nml:63

        _w2.text = _bind(lambda _o: _tr('~R~efresh display'), yielding=True)    # main_menu.nml:65
        _w2.tooltip = _bind(    # main_menu.nml:66
            lambda _o: _tr('Paint the whole screen again, over what another program left on it'),
            yielding=True,
        )
        _w2.command = Refresh    # main_menu.nml:67

        _w3.text = _bind(lambda _o: _tr('~S~creen rest'), yielding=True)    # main_menu.nml:69
        _w3.tooltip = _bind(    # main_menu.nml:70
            lambda _o: _tr('Start the screen saver now'),
            yielding=True,
        )
        _w3.command = ScreenRest    # main_menu.nml:71

        _w5.text = _bind(lambda _o: _tr('Screen gra~b~ber'), yielding=True)    # main_menu.nml:74
        _w5.tooltip = _bind(    # main_menu.nml:75
            lambda _o: _tr('Copy a rectangle of the screen to the clipboard'),
            yielding=True,
        )
        _w5.command = ScreenGrab    # main_menu.nml:76
        _w5.key = 'Shift-Alt-Ins'    # main_menu.nml:77

        _w6.text = _bind(lambda _o: _tr('~U~ser screen'), yielding=True)    # main_menu.nml:79
        _w6.tooltip = _bind(    # main_menu.nml:80
            lambda _o: _tr('Look at the console until a key is pressed'),
            yielding=True,
        )
        _w6.command = ShowUserScreen    # main_menu.nml:81
        _w6.key = 'Alt-F5'    # main_menu.nml:82

        _w7.text = _bind(lambda _o: _tr('~O~utput window'), yielding=True)    # main_menu.nml:84
        _w7.tooltip = _bind(    # main_menu.nml:85
            lambda _o: _tr('Put the windows away to type in the console, or bring them back'),
            yielding=True,
        )
        _w7.command = ToggleConsole    # main_menu.nml:86
        _w7.key = 'Ctrl-O'    # main_menu.nml:87

        _w8.text = _bind(lambda _o: _tr('S~m~artPad (TM)'), yielding=True)    # main_menu.nml:89
        _w8.tooltip = _bind(    # main_menu.nml:90
            lambda _o: _tr('A notepad kept from one session to the next'),
            yielding=True,
        )
        _w8.command = OpenSmartpad    # main_menu.nml:91
        _w8.key = 'Alt-Q'    # main_menu.nml:92

        _w9.text = _bind(lambda _o: _tr('~T~rashcan on/off'), yielding=True)    # main_menu.nml:94
        _w9.tooltip = _bind(    # main_menu.nml:95
            lambda _o: _tr('Show or hide the trash can that files are dropped on to delete them'),
            yielding=True,
        )
        _w9.command = ToggleTrashCan    # main_menu.nml:96

        _w11.text = _bind(lambda _o: _tr('~G~ame'), yielding=True)    # main_menu.nml:99
        _w11.command = Game    # main_menu.nml:100
        _w11.key = 'Alt-F9'    # main_menu.nml:101

        self.file.text = _bind(lambda _o: _tr('~F~ile'), yielding=True)    # main_menu.nml:104
        self.file.tooltip = _bind(    # main_menu.nml:105
            lambda _o: _tr('View, edit, copy, move, archive and delete files'),
            yielding=True,
        )

        self.file_view.text = _bind(lambda _o: _tr('~V~iew'), yielding=True)    # main_menu.nml:108

        _w12.text = _bind(lambda _o: _tr('~A~s is'), yielding=True)    # main_menu.nml:110
        _w12.tooltip = _bind(    # main_menu.nml:111
            lambda _o: _tr('View the file as F3 does'),
            yielding=True,
        )
        _w12.command = View    # main_menu.nml:112
        _w12.key = 'F3'    # main_menu.nml:113

        _w13.text = _bind(lambda _o: _tr('As ~T~ext'), yielding=True)    # main_menu.nml:115
        _w13.command = ViewAsText    # main_menu.nml:116

        _w14.text = _bind(lambda _o: _tr('As He~x~'), yielding=True)    # main_menu.nml:118
        _w14.command = ViewAsHex    # main_menu.nml:119

        _w15.text = _bind(lambda _o: _tr('As ~D~ataBase'), yielding=True)    # main_menu.nml:121
        _w15.tooltip = _bind(    # main_menu.nml:122
            lambda _o: _tr('View a dBase or SQLite file as a table'),
            yielding=True,
        )
        _w15.command = ViewAsDataBase    # main_menu.nml:123

        _w16.text = _bind(lambda _o: _tr('As ~S~preadsheet'), yielding=True)    # main_menu.nml:127
        _w16.tooltip = _bind(    # main_menu.nml:128
            lambda _o: _tr('View a CSV or TSV file as a spreadsheet'),
            yielding=True,
        )
        _w16.command = ViewAsSpreadsheet    # main_menu.nml:129

        _w18.text = _bind(lambda _o: _tr('Alternate vie~w~'), yielding=True)    # main_menu.nml:132
        _w18.tooltip = _bind(    # main_menu.nml:133
            lambda _o: _tr('View with the viewer F3 does not use: the external one, or the internal'),
            yielding=True,
        )
        _w18.command = AlternateView    # main_menu.nml:134
        _w18.key = 'Alt-F3'    # main_menu.nml:135

        _w20.text = _bind(lambda _o: _tr('~O~pen...'), yielding=True)    # main_menu.nml:139
        _w20.tooltip = _bind(    # main_menu.nml:140
            lambda _o: _tr('View a file chosen in a file box'),
            yielding=True,
        )
        _w20.command = OpenView    # main_menu.nml:141

        self.file_edit.text = _bind(lambda _o: _tr('~E~dit'), yielding=True)    # main_menu.nml:144

        _w21.text = _bind(lambda _o: _tr('~E~dit'), yielding=True)    # main_menu.nml:146
        _w21.command = Edit    # main_menu.nml:147
        _w21.key = 'F4'    # main_menu.nml:148

        _w22.text = _bind(lambda _o: _tr('~A~lternate edit'), yielding=True)    # main_menu.nml:150
        _w22.tooltip = _bind(    # main_menu.nml:151
            lambda _o: _tr('Edit with the editor F4 does not use: the external one, or the internal'),
            yielding=True,
        )
        _w22.command = AlternateEdit    # main_menu.nml:152
        _w22.key = 'Alt-F4'    # main_menu.nml:153

        _w24.text = _bind(lambda _o: _tr('Edit ~n~ew file...'), yielding=True)    # main_menu.nml:156
        _w24.command = EditNamed    # main_menu.nml:157
        _w24.key = 'Shift-F4'    # main_menu.nml:158

        _w25.text = _bind(lambda _o: _tr('~O~pen...'), yielding=True)    # main_menu.nml:161
        _w25.tooltip = _bind(    # main_menu.nml:162
            lambda _o: _tr('Edit a file chosen in a file box'),
            yielding=True,
        )
        _w25.command = OpenEdit    # main_menu.nml:163

        _w26.text = _bind(lambda _o: _tr('Open ~w~ith...'), yielding=True)    # main_menu.nml:166
        _w26.tooltip = _bind(    # main_menu.nml:167
            lambda _o: _tr('Open the file in a desktop application chosen from a list'),
            yielding=True,
        )
        _w26.command = OpenWith    # main_menu.nml:168

        _w27.text = _bind(lambda _o: _tr('~F~ind...'), yielding=True)    # main_menu.nml:170
        _w27.command = FindFile    # main_menu.nml:171
        _w27.key = 'Alt-F7'    # main_menu.nml:172

        _w28.text = _bind(lambda _o: _tr('~C~opy...'), yielding=True)    # main_menu.nml:174
        _w28.command = Copy    # main_menu.nml:175
        _w28.key = 'F5'    # main_menu.nml:176

        _w29.text = _bind(lambda _o: _tr('~R~ename/Move...'), yielding=True)    # main_menu.nml:178
        _w29.command = RenameMove    # main_menu.nml:179
        _w29.key = 'F6'    # main_menu.nml:180

        _w30.text = _bind(lambda _o: _tr('~Q~uick rename...'), yielding=True)    # main_menu.nml:184
        _w30.tooltip = _bind(    # main_menu.nml:185
            lambda _o: _tr('Rename the file at the cursor in a small box'),
            yielding=True,
        )
        _w30.command = QuickRename    # main_menu.nml:186
        _w30.key = 'Shift-F6'    # main_menu.nml:187

        _w31.text = _bind(lambda _o: _tr('Create arch~i~ve...'), yielding=True)    # main_menu.nml:192
        _w31.command = ArchiveFiles    # main_menu.nml:193
        _w31.key = 'Shift-F1'    # main_menu.nml:194

        _w32.text = _bind(    # main_menu.nml:196
            lambda _o: _tr('Ex~t~ract archive...'),
            yielding=True,
        )
        _w32.command = ExtractArchive    # main_menu.nml:197
        _w32.key = 'Shift-F2'    # main_menu.nml:198

        self.file_symlinks.text = _bind(    # main_menu.nml:203
            lambda _o: _tr('~S~ymlinks'),
            yielding=True,
        )

        _w33.text = _bind(lambda _o: _tr('Create ~s~ymlink...'), yielding=True)    # main_menu.nml:205
        _w33.tooltip = _bind(    # main_menu.nml:206
            lambda _o: _tr('Make a symbolic link to each selected file'),
            yielding=True,
        )
        _w33.command = MakeLink    # main_menu.nml:207
        _w33.key = 'Shift-F5'    # main_menu.nml:208

        _w35.text = _bind(    # main_menu.nml:211
            lambda _o: _tr('~E~dit link target...'),
            yielding=True,
        )
        _w35.tooltip = _bind(    # main_menu.nml:212
            lambda _o: _tr('Change what the selected links point at'),
            yielding=True,
        )
        _w35.command = EditLinkTarget    # main_menu.nml:213

        _w36.text = _bind(lambda _o: _tr('Make ~r~elative'), yielding=True)    # main_menu.nml:215
        _w36.tooltip = _bind(    # main_menu.nml:216
            lambda _o: _tr("Rewrite each selected link's target relative to the link"),
            yielding=True,
        )
        _w36.command = LinkRelative    # main_menu.nml:217

        _w37.text = _bind(lambda _o: _tr('Make ~a~bsolute'), yielding=True)    # main_menu.nml:219
        _w37.tooltip = _bind(    # main_menu.nml:220
            lambda _o: _tr("Rewrite each selected link's target as a full path"),
            yielding=True,
        )
        _w37.command = LinkAbsolute    # main_menu.nml:221

        _w39.text = _bind(    # main_menu.nml:224
            lambda _o: _tr('Select ~b~roken links'),
            yielding=True,
        )
        _w39.tooltip = _bind(    # main_menu.nml:225
            lambda _o: _tr('Tag every link here that points nowhere'),
            yielding=True,
        )
        _w39.command = SelectBrokenLinks    # main_menu.nml:226

        _w40.text = _bind(lambda _o: _tr('Compare fi~l~es...'), yielding=True)    # main_menu.nml:230
        _w40.command = DiffFiles    # main_menu.nml:231

        _w41.text = _bind(lambda _o: _tr('~P~rint'), yielding=True)    # main_menu.nml:233
        _w41.command = PrintFile    # main_menu.nml:234
        _w41.key = 'Ctrl-F9'    # main_menu.nml:235

        _w42.text = _bind(lambda _o: _tr('~M~ake directory'), yielding=True)    # main_menu.nml:237
        _w42.command = MakeDirectory    # main_menu.nml:238
        _w42.key = 'F7'    # main_menu.nml:239

        _w43.text = _bind(lambda _o: _tr('~D~elete'), yielding=True)    # main_menu.nml:241
        _w43.command = Delete    # main_menu.nml:242
        _w43.key = 'F8'    # main_menu.nml:243

        self.file_restore_trash.text = _bind(    # main_menu.nml:250
            lambda _o: _tr('Restore from Tras~h~'),
            yielding=True,
        )
        self.file_restore_trash.tooltip = _bind(    # main_menu.nml:251
            lambda _o: _tr('Put the selected files back where they were deleted from'),
            yielding=True,
        )
        self.file_restore_trash.command = RestoreTrash    # main_menu.nml:252
        self.file_restore_trash.hidden = _bind(    # main_menu.nml:253
            lambda _o: not getattr(self.context, 'shows_trash', False)
        )

        _w44.text = _bind(    # main_menu.nml:255
            lambda _o: _tr('File ~A~ttributes...'),
            yielding=True,
        )
        _w44.tooltip = _bind(    # main_menu.nml:256
            lambda _o: _tr('Permissions, owner, group, dates, ACLs and extended attributes'),
            yielding=True,
        )
        _w44.command = ChangeAttributes    # main_menu.nml:257
        _w44.key = 'Alt-E'    # main_menu.nml:258

        _w45.text = _bind(lambda _o: _tr('UU E~n~code...'), yielding=True)    # main_menu.nml:260
        _w45.tooltip = _bind(    # main_menu.nml:261
            lambda _o: _tr('Encode the file as plain text, the old way of mailing files'),
            yielding=True,
        )
        _w45.command = UuEncode    # main_menu.nml:262
        _w45.key = 'Ctrl-F7'    # main_menu.nml:263

        _w46.text = _bind(lambda _o: _tr('~U~U Decode...'), yielding=True)    # main_menu.nml:265
        _w46.tooltip = _bind(    # main_menu.nml:266
            lambda _o: _tr('Decode the files UU-encoded in this file'),
            yielding=True,
        )
        _w46.command = UuDecode    # main_menu.nml:267
        _w46.key = 'Ctrl-F8'    # main_menu.nml:268

        self.file_checksums.text = _bind(    # main_menu.nml:273
            lambda _o: _tr('Chec~k~sums'),
            yielding=True,
        )

        _w47.text = _bind(lambda _o: _tr('~C~alculate...'), yielding=True)    # main_menu.nml:275
        _w47.tooltip = _bind(    # main_menu.nml:276
            lambda _o: _tr('Hash the tagged files and write their checksums to a list'),
            yielding=True,
        )
        _w47.command = CalculateChecksums    # main_menu.nml:277

        _w48.text = _bind(lambda _o: _tr('~V~erify'), yielding=True)    # main_menu.nml:279
        _w48.tooltip = _bind(    # main_menu.nml:280
            lambda _o: _tr('Hash the files a checksum list names again and check them'),
            yielding=True,
        )
        _w48.command = VerifyChecksums    # main_menu.nml:281

        _w49.text = _bind(lambda _o: _tr('Delete single file'), yielding=True)    # main_menu.nml:283
        _w49.tooltip = _bind(    # main_menu.nml:284
            lambda _o: _tr('Delete the file at the cursor, not the selection'),
            yielding=True,
        )
        _w49.command = DeleteSingle    # main_menu.nml:285
        _w49.key = 'Shift-Del'    # main_menu.nml:286

        _w51.text = _bind(    # main_menu.nml:289
            lambda _o: _tr('Execute ~O~S command'),
            yielding=True,
        )
        _w51.tooltip = _bind(    # main_menu.nml:290
            lambda _o: _tr('Type a command in a box and run it'),
            yielding=True,
        )
        _w51.command = ExecuteOsCommand    # main_menu.nml:291

        _w52.text = _bind(lambda _o: _tr('E~x~it'), yielding=True)    # main_menu.nml:293
        _w52.command = Quit    # main_menu.nml:294
        _w52.key = 'Alt-X'    # main_menu.nml:295

        self.disk.text = _bind(lambda _o: _tr('~D~isk'), yielding=True)    # main_menu.nml:298
        self.disk.tooltip = _bind(    # main_menu.nml:299
            lambda _o: _tr('The directory tree, volumes and the Trash'),
            yielding=True,
        )

        _w53.text = _bind(lambda _o: _tr('~D~irectory tree'), yielding=True)    # main_menu.nml:301
        _w53.command = OpenTreeWindow    # main_menu.nml:302

        _w54.text = _bind(lambda _o: _tr('~V~olumes'), yielding=True)    # main_menu.nml:304
        _w54.tooltip = _bind(    # main_menu.nml:305
            lambda _o: _tr('Disks and partitions: mount, unmount and eject them'),
            yielding=True,
        )
        _w54.command = OpenVolumesWindow    # main_menu.nml:306

        _w55.text = _bind(lambda _o: _tr('Directory ~s~izes'), yielding=True)    # main_menu.nml:309
        _w55.tooltip = _bind(    # main_menu.nml:310
            lambda _o: _tr("What takes the room under the panel's directory, biggest first"),
            yielding=True,
        )
        _w55.command = OpenUsageWindow    # main_menu.nml:311

        _w57.text = _bind(lambda _o: _tr('~T~rash'), yielding=True)    # main_menu.nml:316
        _w57.command = OpenTrash    # main_menu.nml:317

        _w58.text = _bind(lambda _o: _tr('~E~mpty Trash'), yielding=True)    # main_menu.nml:319
        _w58.command = EmptyTrash    # main_menu.nml:320

        self.utilities.text = _bind(    # main_menu.nml:323
            lambda _o: _tr('~U~tilities'),
            yielding=True,
        )
        self.utilities.tooltip = _bind(    # main_menu.nml:324
            lambda _o: _tr('Calculator, calendar, remote links, the user menu and histories'),
            yielding=True,
        )

        _w59.text = _bind(    # main_menu.nml:326
            lambda _o: _tr('S~y~stem Information'),
            yielding=True,
        )
        _w59.command = SystemInfo    # main_menu.nml:327

        _w61.text = _bind(lambda _o: _tr('~C~alculator'), yielding=True)    # main_menu.nml:330
        _w61.command = Calculator    # main_menu.nml:331
        _w61.key = 'Ctrl-F6'    # main_menu.nml:332

        _w62.text = _bind(lambda _o: _tr('Ca~l~endar'), yielding=True)    # main_menu.nml:336
        _w62.command = OpenCalendar    # main_menu.nml:337

        _w63.text = _bind(lambda _o: _tr('Character ta~b~le'), yielding=True)    # main_menu.nml:339
        _w63.tooltip = _bind(    # main_menu.nml:340
            lambda _o: _tr('Pick a character to type where the cursor is'),
            yielding=True,
        )
        _w63.command = AsciiTable    # main_menu.nml:341
        _w63.key = 'Ctrl-B'    # main_menu.nml:342

        _w65.text = _bind(    # main_menu.nml:353
            lambda _o: _tr('~S~SH link (SFTP)...'),
            yielding=True,
        )
        _w65.command = NavyLink    # main_menu.nml:354
        _w65.key = 'Alt-F11'    # main_menu.nml:355

        _w66.text = _bind(lambda _o: _tr('~F~TP link...'), yielding=True)    # main_menu.nml:357
        _w66.command = FtpLink    # main_menu.nml:358

        _w67.text = _bind(    # main_menu.nml:360
            lambda _o: _tr('S~M~B link (Windows share)...'),
            yielding=True,
        )
        _w67.command = SmbLink    # main_menu.nml:361

        _w68.text = _bind(    # main_menu.nml:363
            lambda _o: _tr('S~3~ link (Amazon S3)...'),
            yielding=True,
        )
        _w68.command = S3Link    # main_menu.nml:364

        _w69.text = _bind(    # main_menu.nml:367
            lambda _o: _tr('~G~Vfs/KIO link (MTP, WebDAV...)...'),
            yielding=True,
        )
        _w69.tooltip = _bind(    # main_menu.nml:368
            lambda _o: _tr('A phone, a WebDAV share, Google Drive: anything the desktop can mount'),
            yielding=True,
        )
        _w69.command = GvfsLink    # main_menu.nml:369

        _w70.text = _bind(lambda _o: _tr('Rem~o~te shell...'), yielding=True)    # main_menu.nml:372
        _w70.tooltip = _bind(    # main_menu.nml:373
            lambda _o: _tr('A shell on the server the active panel is browsing over SSH'),
            yielding=True,
        )
        _w70.command = Terminal    # main_menu.nml:374

        _w71.text = _bind(lambda _o: _tr('~D~isconnect'), yielding=True)    # main_menu.nml:376
        _w71.tooltip = _bind(    # main_menu.nml:377
            lambda _o: _tr('Close a connection; its panels go back to the disk'),
            yielding=True,
        )
        _w71.command = HangUp    # main_menu.nml:378
        _w71.key = 'Alt-H'    # main_menu.nml:379

        _w72.text = _bind(lambda _o: _tr('Close ~r~oot access'), yielding=True)    # main_menu.nml:381
        _w72.tooltip = _bind(    # main_menu.nml:382
            lambda _o: _tr('End root access now, rather than after its timeout'),
            yielding=True,
        )
        _w72.command = CloseRootAccess    # main_menu.nml:383

        _w73.text = _bind(lambda _o: _tr('Saved l~i~nks...'), yielding=True)    # main_menu.nml:385
        _w73.tooltip = _bind(    # main_menu.nml:386
            lambda _o: _tr('The saved connections: edit them, or connect to one'),
            yielding=True,
        )
        _w73.command = EditLinks    # main_menu.nml:387

        _w75.text = _bind(lambda _o: _tr('Edi~t~ environment'), yielding=True)    # main_menu.nml:390
        _w75.tooltip = _bind(    # main_menu.nml:391
            lambda _o: _tr('Edit the environment variables commands run with'),
            yielding=True,
        )
        _w75.command = EnvEdit    # main_menu.nml:392

        _w76.text = _bind(lambda _o: _tr('~U~ser menu'), yielding=True)    # main_menu.nml:394
        _w76.command = UserMenu    # main_menu.nml:395
        _w76.key = 'F2'    # main_menu.nml:396

        _w77.text = _bind(lambda _o: _tr('Commands ~H~istory'), yielding=True)    # main_menu.nml:398
        _w77.command = HistoryList    # main_menu.nml:399
        _w77.key = 'Alt-F8'    # main_menu.nml:400

        _w78.text = _bind(    # main_menu.nml:403
            lambda _o: _tr('Fu~z~zy history search...'),
            yielding=True,
        )
        _w78.tooltip = _bind(    # main_menu.nml:404
            lambda _o: _tr('The commands typed, here and in the shell, searched by fzf'),
            yielding=True,
        )
        _w78.command = FuzzyHistory    # main_menu.nml:405
        _w78.key = 'Alt-Shift-F8'    # main_menu.nml:406

        _w79.text = _bind(lambda _o: _tr('File ~E~dit History'), yielding=True)    # main_menu.nml:408
        _w79.command = EditHistory    # main_menu.nml:409
        _w79.key = 'Alt-PgUp'    # main_menu.nml:410

        _w80.text = _bind(lambda _o: _tr('File ~V~iew History'), yielding=True)    # main_menu.nml:412
        _w80.command = ViewHistory    # main_menu.nml:413
        _w80.key = 'Alt-PgDn'    # main_menu.nml:414

        self.manager.text = _bind(lambda _o: _tr('~M~anager'), yielding=True)    # main_menu.nml:417
        self.manager.tooltip = _bind(    # main_menu.nml:418
            lambda _o: _tr('New file managers, swapping and hiding panels, bookmarks'),
            yielding=True,
        )

        _w81.text = _bind(lambda _o: _tr('~N~ew'), yielding=True)    # main_menu.nml:420
        _w81.command = NewManager    # main_menu.nml:421
        _w81.key = 'Ctrl-F3'    # main_menu.nml:422

        _w82.text = _bind(lambda _o: _tr('~S~wap panels'), yielding=True)    # main_menu.nml:424
        _w82.command = SwapPanels    # main_menu.nml:425
        _w82.key = 'Ctrl-U'    # main_menu.nml:426

        _w83.text = _bind(    # main_menu.nml:428
            lambda _o: _tr('Show/hide ~l~eft panel'),
            yielding=True,
        )
        _w83.command = HideLeft    # main_menu.nml:429
        _w83.key = 'Ctrl-F1'    # main_menu.nml:430

        _w84.text = _bind(    # main_menu.nml:432
            lambda _o: _tr('Show/hide ~r~ight panel'),
            yielding=True,
        )
        _w84.command = HideRight    # main_menu.nml:433
        _w84.key = 'Ctrl-F2'    # main_menu.nml:434

        _w85.text = _bind(    # main_menu.nml:436
            lambda _o: _tr('Show/hide inactive ~p~anel'),
            yielding=True,
        )
        _w85.tooltip = _bind(    # main_menu.nml:437
            lambda _o: _tr('Hide the panel without the keyboard, or show it again'),
            yielding=True,
        )
        _w85.command = HideInactive    # main_menu.nml:438
        _w85.key = 'Ctrl-P'    # main_menu.nml:439

        _w86.text = _bind(lambda _o: _tr('~M~iller columns'), yielding=True)    # main_menu.nml:443
        _w86.tooltip = _bind(    # main_menu.nml:444
            lambda _o: _tr('Browse in columns, each directory beside its parent'),
            yielding=True,
        )
        _w86.command = ToggleMiller    # main_menu.nml:445
        _w86.key = 'Alt-F12'    # main_menu.nml:446

        _w88.text = _bind(lambda _o: _tr('Bookmarks le~f~t'), yielding=True)    # main_menu.nml:449
        _w88.tooltip = _bind(    # main_menu.nml:450
            lambda _o: _tr('Send the left panel to a bookmarked directory'),
            yielding=True,
        )
        _w88.command = ChangeLeft    # main_menu.nml:451
        _w88.key = 'Alt-F1'    # main_menu.nml:452

        _w89.text = _bind(lambda _o: _tr('Bookmarks rig~h~t'), yielding=True)    # main_menu.nml:454
        _w89.tooltip = _bind(    # main_menu.nml:455
            lambda _o: _tr('Send the right panel to a bookmarked directory'),
            yielding=True,
        )
        _w89.command = ChangeRight    # main_menu.nml:456
        _w89.key = 'Alt-F2'    # main_menu.nml:457

        self.options.text = _bind(lambda _o: _tr('~O~ptions'), yielding=True)    # main_menu.nml:460
        self.options.tooltip = _bind(    # main_menu.nml:461
            lambda _o: _tr('Settings, configuration files, the desktop and colours'),
            yielding=True,
        )

        _w90.text = _bind(lambda _o: _tr('Sett~i~ngs...'), yielding=True)    # main_menu.nml:465
        _w90.tooltip = _bind(    # main_menu.nml:466
            lambda _o: _tr('Every setup page in one box, behind tabs'),
            yielding=True,
        )
        _w90.command = Settings    # main_menu.nml:467

        self.options_configuration.text = _bind(    # main_menu.nml:471
            lambda _o: _tr('~C~onfiguration'),
            yielding=True,
        )

        _w92.text = _bind(lambda _o: _tr('S~y~stem Setup...'), yielding=True)    # main_menu.nml:473
        _w92.command = SystemSetup    # main_menu.nml:474

        _w93.text = _bind(lambda _o: _tr('~S~tartup...'), yielding=True)    # main_menu.nml:476
        _w93.command = StartupSetup    # main_menu.nml:477

        _w94.text = _bind(lambda _o: _tr('~I~nterface...'), yielding=True)    # main_menu.nml:479
        _w94.command = InterfaceSetup    # main_menu.nml:480

        _w95.text = _bind(lambda _o: _tr('~C~onfirmations...'), yielding=True)    # main_menu.nml:482
        _w95.command = SetupConfirmation    # main_menu.nml:483

        _w97.text = _bind(lambda _o: _tr('Screen sa~v~ers...'), yielding=True)    # main_menu.nml:486
        _w97.command = SaversSetup    # main_menu.nml:487

        _w98.text = _bind(    # main_menu.nml:489
            lambda _o: _tr('C~o~untry support...'),
            yielding=True,
        )
        _w98.command = CountrySetup    # main_menu.nml:490

        _w99.text = _bind(lambda _o: _tr('Comm~u~nications...'), yielding=True)    # main_menu.nml:492
        _w99.tooltip = _bind(    # main_menu.nml:493
            lambda _o: _tr('Settings for remote connections'),
            yielding=True,
        )
        _w99.command = SetupLink    # main_menu.nml:494

        _w101.text = _bind(lambda _o: _tr('~E~ditor/Viewer...'), yielding=True)    # main_menu.nml:497
        _w101.command = EditorDefaults    # main_menu.nml:498

        _w103.text = _bind(lambda _o: _tr('~K~ey bindings...'), yielding=True)    # main_menu.nml:501
        _w103.command = KeyBindingsSetup    # main_menu.nml:502

        self.options_file_manager.text = _bind(    # main_menu.nml:505
            lambda _o: _tr('~F~ile Manager'),
            yielding=True,
        )

        _w104.text = _bind(lambda _o: _tr('~S~etup...'), yielding=True)    # main_menu.nml:507
        _w104.command = FileManagerSetup    # main_menu.nml:508

        _w105.text = _bind(    # main_menu.nml:510
            lambda _o: _tr('~I~nformation panel...'),
            yielding=True,
        )
        _w105.tooltip = _bind(    # main_menu.nml:511
            lambda _o: _tr('What the information panel (Ctrl+L) shows'),
            yielding=True,
        )
        _w105.command = DriveInfoSetup    # main_menu.nml:512

        _w106.text = _bind(    # main_menu.nml:514
            lambda _o: _tr('New Manager ~d~efaults...'),
            yielding=True,
        )
        _w106.tooltip = _bind(    # main_menu.nml:515
            lambda _o: _tr("How a new file manager's panels start"),
            yielding=True,
        )
        _w106.command = FileManagerDefaults    # main_menu.nml:516

        _w107.text = _bind(    # main_menu.nml:518
            lambda _o: _tr('~C~olumn defaults...'),
            yielding=True,
        )
        _w107.tooltip = _bind(    # main_menu.nml:519
            lambda _o: _tr('The columns a new panel shows'),
            yielding=True,
        )
        _w107.command = ColumnDefaults    # main_menu.nml:520

        _w108.text = _bind(    # main_menu.nml:522
            lambda _o: _tr('~H~ighlight groups...'),
            yielding=True,
        )
        _w108.tooltip = _bind(    # main_menu.nml:523
            lambda _o: _tr('Which files the panels show in which colour'),
            yielding=True,
        )
        _w108.command = HighlightGroups    # main_menu.nml:524

        self.options_archives.text = _bind(    # main_menu.nml:527
            lambda _o: _tr('A~r~chives'),
            yielding=True,
        )

        _w109.text = _bind(    # main_menu.nml:529
            lambda _o: _tr('Current archiver...'),
            yielding=True,
        )
        _w109.key = 'Alt-N'    # main_menu.nml:530

        _w111.text = _bind(    # main_menu.nml:533
            lambda _o: _tr('~Q~uick run file edit...'),
            yielding=True,
        )
        _w111.tooltip = _bind(    # main_menu.nml:534
            lambda _o: _tr('Edit quickrun.ini: the commands Ctrl+Shift+F1 to F10 run'),
            yielding=True,
        )
        _w111.command = EditQuickRun    # main_menu.nml:535

        _w112.text = _bind(    # main_menu.nml:537
            lambda _o: _tr('E~x~tension file edit...'),
            yielding=True,
        )
        _w112.tooltip = _bind(    # main_menu.nml:538
            lambda _o: _tr('Edit extensions.ini: what Enter runs for each kind of file'),
            yielding=True,
        )
        _w112.command = ExtFileEdit    # main_menu.nml:539

        _w113.text = _bind(    # main_menu.nml:541
            lambda _o: _tr('~H~ighlight file edit...'),
            yielding=True,
        )
        _w113.tooltip = _bind(    # main_menu.nml:542
            lambda _o: _tr('Edit highlight.ini: which syntax colours which file'),
            yielding=True,
        )
        _w113.command = EditHGL    # main_menu.nml:543

        _w114.text = _bind(    # main_menu.nml:545
            lambda _o: _tr('Macro file e~d~it...'),
            yielding=True,
        )
        _w114.tooltip = _bind(    # main_menu.nml:546
            lambda _o: _tr("Edit macros.ini: the editor's macros, offered by Ctrl+J 0"),
            yielding=True,
        )
        _w114.command = EditMacros    # main_menu.nml:547

        _w115.text = _bind(    # main_menu.nml:549
            lambda _o: _tr('~G~lobal menu definition...'),
            yielding=True,
        )
        _w115.tooltip = _bind(    # main_menu.nml:550
            lambda _o: _tr('Edit the F2 user menu used everywhere'),
            yielding=True,
        )
        _w115.command = MenuFileEdit    # main_menu.nml:551

        _w116.text = _bind(    # main_menu.nml:553
            lambda _o: _tr('Local ~m~enu definition...'),
            yielding=True,
        )
        _w116.tooltip = _bind(    # main_menu.nml:554
            lambda _o: _tr("Edit this directory's own F2 user menu"),
            yielding=True,
        )
        _w116.command = LocalMenuFileEdit    # main_menu.nml:555

        _w117.text = _bind(lambda _o: _tr('~V~iewers...'), yielding=True)    # main_menu.nml:557
        _w117.tooltip = _bind(    # main_menu.nml:558
            lambda _o: _tr('Edit viewers.ini: the external viewer for each kind of file'),
            yielding=True,
        )
        _w117.command = ExternalViewers    # main_menu.nml:559

        _w118.text = _bind(lambda _o: _tr('~E~ditors...'), yielding=True)    # main_menu.nml:561
        _w118.tooltip = _bind(    # main_menu.nml:562
            lambda _o: _tr('Edit editors.ini: the external editor for each kind of file'),
            yielding=True,
        )
        _w118.command = ExternalEditors    # main_menu.nml:563

        _w120.text = _bind(lambda _o: _tr('~S~ave desktop'), yielding=True)    # main_menu.nml:566
        _w120.tooltip = _bind(    # main_menu.nml:567
            lambda _o: _tr('Keep the open windows, to have them back later'),
            yielding=True,
        )
        _w120.command = SaveDesktop    # main_menu.nml:568

        _w121.text = _bind(lambda _o: _tr('~L~oad desktop'), yielding=True)    # main_menu.nml:570
        _w121.tooltip = _bind(    # main_menu.nml:571
            lambda _o: _tr('Replace these windows with the ones last saved'),
            yielding=True,
        )
        _w121.command = LoadDesktop    # main_menu.nml:572

        _w123.text = _bind(lambda _o: _tr('C~o~lors...'), yielding=True)    # main_menu.nml:575
        _w123.command = ChangeColors    # main_menu.nml:576

        _w124.text = _bind(lambda _o: _tr('S~t~ore palette'), yielding=True)    # main_menu.nml:578
        _w124.tooltip = _bind(    # main_menu.nml:579
            lambda _o: _tr('Save the colours as a theme of your own'),
            yielding=True,
        )
        _w124.command = StoreColors    # main_menu.nml:580

        _w125.text = _bind(lambda _o: _tr('Lo~a~d palette'), yielding=True)    # main_menu.nml:582
        _w125.tooltip = _bind(    # main_menu.nml:583
            lambda _o: _tr('Use colours saved in a file'),
            yielding=True,
        )
        _w125.command = LoadColors    # main_menu.nml:584

        self.window.text = _bind(lambda _o: _tr('~W~indow'), yielding=True)    # main_menu.nml:587
        self.window.tooltip = _bind(    # main_menu.nml:588
            lambda _o: _tr('Arrange, switch between and close windows'),
            yielding=True,
        )

        _w126.text = _bind(lambda _o: _tr('~T~ile'), yielding=True)    # main_menu.nml:590
        _w126.command = TileWindows    # main_menu.nml:591

        _w127.text = _bind(lambda _o: _tr('C~a~scade'), yielding=True)    # main_menu.nml:593
        _w127.command = CascadeWindows    # main_menu.nml:594

        _w128.text = _bind(lambda _o: _tr('Cl~o~se all'), yielding=True)    # main_menu.nml:596
        _w128.command = CloseAllWindows    # main_menu.nml:597

        _w130.text = _bind(lambda _o: _tr('~S~ize/Move'), yielding=True)    # main_menu.nml:600
        _w130.tooltip = _bind(    # main_menu.nml:601
            lambda _o: _tr('Move and size the window with the keyboard'),
            yielding=True,
        )
        _w130.command = SizeMoveWindow    # main_menu.nml:602
        _w130.key = 'Ctrl-F5'    # main_menu.nml:603

        _w131.text = _bind(lambda _o: _tr('~Z~oom'), yielding=True)    # main_menu.nml:605
        _w131.command = ZoomWindow    # main_menu.nml:606
        _w131.key = 'Alt-Z'    # main_menu.nml:607

        _w132.text = _bind(lambda _o: _tr('~N~ext'), yielding=True)    # main_menu.nml:609
        _w132.command = NextWindow    # main_menu.nml:610
        _w132.key = 'F9'    # main_menu.nml:611

        _w133.text = _bind(lambda _o: _tr('~P~revious'), yielding=True)    # main_menu.nml:613
        _w133.command = PreviousWindow    # main_menu.nml:614
        _w133.key = 'Shift-F9'    # main_menu.nml:615

        _w134.text = _bind(lambda _o: _tr('~C~lose'), yielding=True)    # main_menu.nml:617
        _w134.command = CloseWindow    # main_menu.nml:618
        _w134.key = 'Ctrl-F4'    # main_menu.nml:619

        _w136.text = _bind(lambda _o: _tr('~L~ist...'), yielding=True)    # main_menu.nml:622
        _w136.tooltip = _bind(    # main_menu.nml:623
            lambda _o: _tr('All the windows, to switch to one or close it'),
            yielding=True,
        )
        _w136.command = WindowManager    # main_menu.nml:624
        _w136.key = 'Alt-0'    # main_menu.nml:625

        _w137.text = _bind(    # main_menu.nml:628
            lambda _o: _tr('~B~ackground operation...'),
            yielding=True,
        )
        _w137.tooltip = _bind(    # main_menu.nml:629
            lambda _o: _tr('Bring back the progress box of a copy or an erase running in the background'),
            yielding=True,
        )
        _w137.command = ShowBackground    # main_menu.nml:630
