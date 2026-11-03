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
from navigator.widgets.manager.commands import RestoreTrash, AlternateEdit, AlternateView, ArchiveFiles, Calculator, ChangeAttributes, ChangeLeft, ChangeRight, Copy, Delete, DeleteSingle, DiffFiles, Edit, EditNamed, ExtractArchive, FindFile, ReplaceInFiles, OpenWith, HideInactive, HideLeft, HideRight, MakeDirectory, MakeLink, EditLinkTarget, LinkAbsolute, LinkRelative, SelectBrokenLinks, QuickRename, RenameMove, SwapPanels, ToggleMiller, UserMenu, UuDecode, UuEncode, CalculateChecksums, VerifyChecksums, EncryptFiles, DecryptFiles, View, ViewAsDataBase, ViewAsHex, ViewAsSpreadsheet, ViewAsText    # main_menu.nml:2
from navigator.widgets.shell.commands import OpenEdit, OpenView, About, OpenCommandPalette, CloseRootAccess, ShowBackground, EditLinks, FtpLink, GvfsLink, S3Link, Game, HangUp, NavyLink, Terminal, SetupLink, SmbLink, SaversSetup, CountrySetup, ScreenRest, ToggleTrashCan, OpenTrash, EmptyTrash, ChangeColors, ColumnDefaults, HighlightGroups, EditQuickRun, ExtFileEdit, EditHGL, EditMacros, ExternalViewers, ExternalEditors, LoadColors, StoreColors, LoadDesktop, SaveDesktop, DriveInfoSetup, EditHistory, EnvEdit, ExecuteOsCommand, HistoryList, FuzzyHistory, OpenCalendar, SystemInfo, EditorDefaults, FileManagerDefaults, FileManagerSetup, InterfaceSetup, KeyBindingsSetup, LocalMenuFileEdit, MenuFileEdit, NewManager, OpenTreeWindow, OpenUsageWindow, OpenVolumesWindow, OpenProcessWindow, OpenMonitorWindow, SetupConfirmation, Settings, StartupSetup, SystemSetup, ViewHistory    # main_menu.nml:3
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
    file: SubMenu    # main_menu.nml:108
    file_view: SubMenu    # main_menu.nml:112
    file_edit: SubMenu    # main_menu.nml:148
    file_symlinks: SubMenu    # main_menu.nml:214
    file_restore_trash: MenuItem    # main_menu.nml:261
    file_checksums: SubMenu    # main_menu.nml:284
    file_encryption: SubMenu    # main_menu.nml:297
    disk: SubMenu    # main_menu.nml:322
    utilities: SubMenu    # main_menu.nml:347
    manager: SubMenu    # main_menu.nml:455
    options: SubMenu    # main_menu.nml:498
    options_configuration: SubMenu    # main_menu.nml:509
    options_file_manager: SubMenu    # main_menu.nml:543
    options_archives: SubMenu    # main_menu.nml:565
    window: SubMenu    # main_menu.nml:625

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.system = SubMenu(parent=self)    # main_menu.nml:57
        _w1 = MenuItem(parent=self.system)    # main_menu.nml:61
        _w2 = MenuItem(parent=self.system)    # main_menu.nml:65
        _w3 = MenuItem(parent=self.system)    # main_menu.nml:69
        _w4 = MenuItem(parent=self.system)    # main_menu.nml:73
        _w5 = MenuLine(parent=self.system)    # main_menu.nml:77
        _w6 = MenuItem(parent=self.system)    # main_menu.nml:78
        _w7 = MenuItem(parent=self.system)    # main_menu.nml:83
        _w8 = MenuItem(parent=self.system)    # main_menu.nml:88
        _w9 = MenuItem(parent=self.system)    # main_menu.nml:93
        _w10 = MenuItem(parent=self.system)    # main_menu.nml:98
        _w11 = MenuLine(parent=self.system)    # main_menu.nml:102
        _w12 = MenuItem(parent=self.system)    # main_menu.nml:103
        self.file = SubMenu(parent=self)    # main_menu.nml:107
        self.file_view = SubMenu(parent=self.file)    # main_menu.nml:111
        _w13 = MenuItem(parent=self.file_view)    # main_menu.nml:114
        _w14 = MenuItem(parent=self.file_view)    # main_menu.nml:119
        _w15 = MenuItem(parent=self.file_view)    # main_menu.nml:122
        _w16 = MenuItem(parent=self.file_view)    # main_menu.nml:125
        _w17 = MenuItem(parent=self.file_view)    # main_menu.nml:131
        _w18 = MenuLine(parent=self.file_view)    # main_menu.nml:135
        _w19 = MenuItem(parent=self.file_view)    # main_menu.nml:136
        _w20 = MenuLine(parent=self.file_view)    # main_menu.nml:141
        _w21 = MenuItem(parent=self.file_view)    # main_menu.nml:143
        self.file_edit = SubMenu(parent=self.file)    # main_menu.nml:147
        _w22 = MenuItem(parent=self.file_edit)    # main_menu.nml:150
        _w23 = MenuItem(parent=self.file_edit)    # main_menu.nml:154
        _w24 = MenuLine(parent=self.file_edit)    # main_menu.nml:159
        _w25 = MenuItem(parent=self.file_edit)    # main_menu.nml:160
        _w26 = MenuItem(parent=self.file_edit)    # main_menu.nml:165
        _w27 = MenuItem(parent=self.file)    # main_menu.nml:170
        _w28 = MenuItem(parent=self.file)    # main_menu.nml:174
        _w29 = MenuItem(parent=self.file)    # main_menu.nml:180
        _w30 = MenuItem(parent=self.file)    # main_menu.nml:185
        _w31 = MenuItem(parent=self.file)    # main_menu.nml:189
        _w32 = MenuItem(parent=self.file)    # main_menu.nml:195
        _w33 = MenuItem(parent=self.file)    # main_menu.nml:203
        _w34 = MenuItem(parent=self.file)    # main_menu.nml:207
        self.file_symlinks = SubMenu(parent=self.file)    # main_menu.nml:213
        _w35 = MenuItem(parent=self.file_symlinks)    # main_menu.nml:216
        _w36 = MenuLine(parent=self.file_symlinks)    # main_menu.nml:221
        _w37 = MenuItem(parent=self.file_symlinks)    # main_menu.nml:222
        _w38 = MenuItem(parent=self.file_symlinks)    # main_menu.nml:226
        _w39 = MenuItem(parent=self.file_symlinks)    # main_menu.nml:230
        _w40 = MenuLine(parent=self.file_symlinks)    # main_menu.nml:234
        _w41 = MenuItem(parent=self.file_symlinks)    # main_menu.nml:235
        _w42 = MenuItem(parent=self.file)    # main_menu.nml:241
        _w43 = MenuItem(parent=self.file)    # main_menu.nml:244
        _w44 = MenuItem(parent=self.file)    # main_menu.nml:248
        _w45 = MenuItem(parent=self.file)    # main_menu.nml:252
        self.file_restore_trash = MenuItem(parent=self.file)    # main_menu.nml:260
        _w46 = MenuItem(parent=self.file)    # main_menu.nml:266
        _w47 = MenuItem(parent=self.file)    # main_menu.nml:271
        _w48 = MenuItem(parent=self.file)    # main_menu.nml:276
        self.file_checksums = SubMenu(parent=self.file)    # main_menu.nml:283
        _w49 = MenuItem(parent=self.file_checksums)    # main_menu.nml:286
        _w50 = MenuItem(parent=self.file_checksums)    # main_menu.nml:290
        self.file_encryption = SubMenu(parent=self.file)    # main_menu.nml:296
        _w51 = MenuItem(parent=self.file_encryption)    # main_menu.nml:299
        _w52 = MenuItem(parent=self.file_encryption)    # main_menu.nml:303
        _w53 = MenuItem(parent=self.file)    # main_menu.nml:307
        _w54 = MenuLine(parent=self.file)    # main_menu.nml:312
        _w55 = MenuItem(parent=self.file)    # main_menu.nml:313
        _w56 = MenuItem(parent=self.file)    # main_menu.nml:317
        self.disk = SubMenu(parent=self)    # main_menu.nml:321
        _w57 = MenuItem(parent=self.disk)    # main_menu.nml:325
        _w58 = MenuItem(parent=self.disk)    # main_menu.nml:328
        _w59 = MenuItem(parent=self.disk)    # main_menu.nml:333
        _w60 = MenuLine(parent=self.disk)    # main_menu.nml:339
        _w61 = MenuItem(parent=self.disk)    # main_menu.nml:340
        _w62 = MenuItem(parent=self.disk)    # main_menu.nml:343
        self.utilities = SubMenu(parent=self)    # main_menu.nml:346
        _w63 = MenuItem(parent=self.utilities)    # main_menu.nml:350
        _w64 = MenuItem(parent=self.utilities)    # main_menu.nml:356
        _w65 = MenuItem(parent=self.utilities)    # main_menu.nml:363
        _w66 = MenuLine(parent=self.utilities)    # main_menu.nml:367
        _w67 = MenuItem(parent=self.utilities)    # main_menu.nml:368
        _w68 = MenuItem(parent=self.utilities)    # main_menu.nml:374
        _w69 = MenuItem(parent=self.utilities)    # main_menu.nml:377
        _w70 = MenuLine(parent=self.utilities)    # main_menu.nml:382
        _w71 = MenuItem(parent=self.utilities)    # main_menu.nml:391
        _w72 = MenuItem(parent=self.utilities)    # main_menu.nml:395
        _w73 = MenuItem(parent=self.utilities)    # main_menu.nml:398
        _w74 = MenuItem(parent=self.utilities)    # main_menu.nml:401
        _w75 = MenuItem(parent=self.utilities)    # main_menu.nml:405
        _w76 = MenuItem(parent=self.utilities)    # main_menu.nml:410
        _w77 = MenuItem(parent=self.utilities)    # main_menu.nml:414
        _w78 = MenuItem(parent=self.utilities)    # main_menu.nml:419
        _w79 = MenuItem(parent=self.utilities)    # main_menu.nml:423
        _w80 = MenuLine(parent=self.utilities)    # main_menu.nml:427
        _w81 = MenuItem(parent=self.utilities)    # main_menu.nml:428
        _w82 = MenuItem(parent=self.utilities)    # main_menu.nml:432
        _w83 = MenuItem(parent=self.utilities)    # main_menu.nml:436
        _w84 = MenuItem(parent=self.utilities)    # main_menu.nml:441
        _w85 = MenuItem(parent=self.utilities)    # main_menu.nml:446
        _w86 = MenuItem(parent=self.utilities)    # main_menu.nml:450
        self.manager = SubMenu(parent=self)    # main_menu.nml:454
        _w87 = MenuItem(parent=self.manager)    # main_menu.nml:458
        _w88 = MenuItem(parent=self.manager)    # main_menu.nml:462
        _w89 = MenuItem(parent=self.manager)    # main_menu.nml:466
        _w90 = MenuItem(parent=self.manager)    # main_menu.nml:470
        _w91 = MenuItem(parent=self.manager)    # main_menu.nml:474
        _w92 = MenuItem(parent=self.manager)    # main_menu.nml:481
        _w93 = MenuLine(parent=self.manager)    # main_menu.nml:486
        _w94 = MenuItem(parent=self.manager)    # main_menu.nml:487
        _w95 = MenuItem(parent=self.manager)    # main_menu.nml:492
        self.options = SubMenu(parent=self)    # main_menu.nml:497
        _w96 = MenuItem(parent=self.options)    # main_menu.nml:503
        _w97 = MenuLine(parent=self.options)    # main_menu.nml:507
        self.options_configuration = SubMenu(parent=self.options)    # main_menu.nml:508
        _w98 = MenuItem(parent=self.options_configuration)    # main_menu.nml:511
        _w99 = MenuItem(parent=self.options_configuration)    # main_menu.nml:514
        _w100 = MenuItem(parent=self.options_configuration)    # main_menu.nml:517
        _w101 = MenuItem(parent=self.options_configuration)    # main_menu.nml:520
        _w102 = MenuLine(parent=self.options_configuration)    # main_menu.nml:523
        _w103 = MenuItem(parent=self.options_configuration)    # main_menu.nml:524
        _w104 = MenuItem(parent=self.options_configuration)    # main_menu.nml:527
        _w105 = MenuItem(parent=self.options_configuration)    # main_menu.nml:530
        _w106 = MenuLine(parent=self.options_configuration)    # main_menu.nml:534
        _w107 = MenuItem(parent=self.options_configuration)    # main_menu.nml:535
        _w108 = MenuLine(parent=self.options_configuration)    # main_menu.nml:538
        _w109 = MenuItem(parent=self.options_configuration)    # main_menu.nml:539
        self.options_file_manager = SubMenu(parent=self.options)    # main_menu.nml:542
        _w110 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:545
        _w111 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:548
        _w112 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:552
        _w113 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:556
        _w114 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:560
        self.options_archives = SubMenu(parent=self.options)    # main_menu.nml:564
        _w115 = MenuItem(parent=self.options_archives)    # main_menu.nml:567
        _w116 = MenuLine(parent=self.options)    # main_menu.nml:570
        _w117 = MenuItem(parent=self.options)    # main_menu.nml:571
        _w118 = MenuItem(parent=self.options)    # main_menu.nml:575
        _w119 = MenuItem(parent=self.options)    # main_menu.nml:579
        _w120 = MenuItem(parent=self.options)    # main_menu.nml:583
        _w121 = MenuItem(parent=self.options)    # main_menu.nml:587
        _w122 = MenuItem(parent=self.options)    # main_menu.nml:591
        _w123 = MenuItem(parent=self.options)    # main_menu.nml:595
        _w124 = MenuItem(parent=self.options)    # main_menu.nml:599
        _w125 = MenuLine(parent=self.options)    # main_menu.nml:603
        _w126 = MenuItem(parent=self.options)    # main_menu.nml:604
        _w127 = MenuItem(parent=self.options)    # main_menu.nml:608
        _w128 = MenuLine(parent=self.options)    # main_menu.nml:612
        _w129 = MenuItem(parent=self.options)    # main_menu.nml:613
        _w130 = MenuItem(parent=self.options)    # main_menu.nml:616
        _w131 = MenuItem(parent=self.options)    # main_menu.nml:620
        self.window = SubMenu(parent=self)    # main_menu.nml:624
        _w132 = MenuItem(parent=self.window)    # main_menu.nml:628
        _w133 = MenuItem(parent=self.window)    # main_menu.nml:631
        _w134 = MenuItem(parent=self.window)    # main_menu.nml:634
        _w135 = MenuLine(parent=self.window)    # main_menu.nml:637
        _w136 = MenuItem(parent=self.window)    # main_menu.nml:638
        _w137 = MenuItem(parent=self.window)    # main_menu.nml:643
        _w138 = MenuItem(parent=self.window)    # main_menu.nml:647
        _w139 = MenuItem(parent=self.window)    # main_menu.nml:651
        _w140 = MenuItem(parent=self.window)    # main_menu.nml:655
        _w141 = MenuLine(parent=self.window)    # main_menu.nml:659
        _w142 = MenuItem(parent=self.window)    # main_menu.nml:660
        _w143 = MenuItem(parent=self.window)    # main_menu.nml:666

        self.system.text = '~≡~'    # main_menu.nml:59
        self.system.tooltip = _bind(    # main_menu.nml:60
            lambda _o: _tr('About, the screen saver, SmartPad, the Trashcan and the game'),
            yielding=True,
        )

        _w1.text = _bind(lambda _o: _tr('~A~bout...'), yielding=True)    # main_menu.nml:62
        _w1.command = About    # main_menu.nml:63

        _w2.text = _bind(lambda _o: _tr('~C~ommand palette...'), yielding=True)    # main_menu.nml:66
        _w2.tooltip = _bind(    # main_menu.nml:67
            lambda _o: _tr('Find any command by a few of its letters, and run it'),
            yielding=True,
        )
        _w2.command = OpenCommandPalette    # main_menu.nml:68

        _w3.text = _bind(lambda _o: _tr('~R~efresh display'), yielding=True)    # main_menu.nml:70
        _w3.tooltip = _bind(    # main_menu.nml:71
            lambda _o: _tr('Paint the whole screen again, over what another program left on it'),
            yielding=True,
        )
        _w3.command = Refresh    # main_menu.nml:72

        _w4.text = _bind(lambda _o: _tr('~S~creen rest'), yielding=True)    # main_menu.nml:74
        _w4.tooltip = _bind(    # main_menu.nml:75
            lambda _o: _tr('Start the screen saver now'),
            yielding=True,
        )
        _w4.command = ScreenRest    # main_menu.nml:76

        _w6.text = _bind(lambda _o: _tr('Screen gra~b~ber'), yielding=True)    # main_menu.nml:79
        _w6.tooltip = _bind(    # main_menu.nml:80
            lambda _o: _tr('Copy a rectangle of the screen to the clipboard'),
            yielding=True,
        )
        _w6.command = ScreenGrab    # main_menu.nml:81
        _w6.key = 'Shift-Alt-Ins'    # main_menu.nml:82

        _w7.text = _bind(lambda _o: _tr('~U~ser screen'), yielding=True)    # main_menu.nml:84
        _w7.tooltip = _bind(    # main_menu.nml:85
            lambda _o: _tr('Look at the console until a key is pressed'),
            yielding=True,
        )
        _w7.command = ShowUserScreen    # main_menu.nml:86
        _w7.key = 'Alt-F5'    # main_menu.nml:87

        _w8.text = _bind(lambda _o: _tr('~O~utput window'), yielding=True)    # main_menu.nml:89
        _w8.tooltip = _bind(    # main_menu.nml:90
            lambda _o: _tr('Put the windows away to type in the console, or bring them back'),
            yielding=True,
        )
        _w8.command = ToggleConsole    # main_menu.nml:91
        _w8.key = 'Ctrl-O'    # main_menu.nml:92

        _w9.text = _bind(lambda _o: _tr('S~m~artPad (TM)'), yielding=True)    # main_menu.nml:94
        _w9.tooltip = _bind(    # main_menu.nml:95
            lambda _o: _tr('A notepad kept from one session to the next'),
            yielding=True,
        )
        _w9.command = OpenSmartpad    # main_menu.nml:96
        _w9.key = 'Alt-Q'    # main_menu.nml:97

        _w10.text = _bind(lambda _o: _tr('~T~rashcan on/off'), yielding=True)    # main_menu.nml:99
        _w10.tooltip = _bind(    # main_menu.nml:100
            lambda _o: _tr('Show or hide the trash can that files are dropped on to delete them'),
            yielding=True,
        )
        _w10.command = ToggleTrashCan    # main_menu.nml:101

        _w12.text = _bind(lambda _o: _tr('~G~ame'), yielding=True)    # main_menu.nml:104
        _w12.command = Game    # main_menu.nml:105
        _w12.key = 'Alt-F9'    # main_menu.nml:106

        self.file.text = _bind(lambda _o: _tr('~F~ile'), yielding=True)    # main_menu.nml:109
        self.file.tooltip = _bind(    # main_menu.nml:110
            lambda _o: _tr('View, edit, copy, move, archive and delete files'),
            yielding=True,
        )

        self.file_view.text = _bind(lambda _o: _tr('~V~iew'), yielding=True)    # main_menu.nml:113

        _w13.text = _bind(lambda _o: _tr('~A~s is'), yielding=True)    # main_menu.nml:115
        _w13.tooltip = _bind(    # main_menu.nml:116
            lambda _o: _tr('View the file as F3 does'),
            yielding=True,
        )
        _w13.command = View    # main_menu.nml:117
        _w13.key = 'F3'    # main_menu.nml:118

        _w14.text = _bind(lambda _o: _tr('As ~T~ext'), yielding=True)    # main_menu.nml:120
        _w14.command = ViewAsText    # main_menu.nml:121

        _w15.text = _bind(lambda _o: _tr('As He~x~'), yielding=True)    # main_menu.nml:123
        _w15.command = ViewAsHex    # main_menu.nml:124

        _w16.text = _bind(lambda _o: _tr('As ~D~ataBase'), yielding=True)    # main_menu.nml:126
        _w16.tooltip = _bind(    # main_menu.nml:127
            lambda _o: _tr('View a dBase or SQLite file as a table'),
            yielding=True,
        )
        _w16.command = ViewAsDataBase    # main_menu.nml:128

        _w17.text = _bind(lambda _o: _tr('As ~S~preadsheet'), yielding=True)    # main_menu.nml:132
        _w17.tooltip = _bind(    # main_menu.nml:133
            lambda _o: _tr('View a CSV or TSV file as a spreadsheet'),
            yielding=True,
        )
        _w17.command = ViewAsSpreadsheet    # main_menu.nml:134

        _w19.text = _bind(lambda _o: _tr('Alternate vie~w~'), yielding=True)    # main_menu.nml:137
        _w19.tooltip = _bind(    # main_menu.nml:138
            lambda _o: _tr('View with the viewer F3 does not use: the external one, or the internal'),
            yielding=True,
        )
        _w19.command = AlternateView    # main_menu.nml:139
        _w19.key = 'Alt-F3'    # main_menu.nml:140

        _w21.text = _bind(lambda _o: _tr('~O~pen...'), yielding=True)    # main_menu.nml:144
        _w21.tooltip = _bind(    # main_menu.nml:145
            lambda _o: _tr('View a file chosen in a file box'),
            yielding=True,
        )
        _w21.command = OpenView    # main_menu.nml:146

        self.file_edit.text = _bind(lambda _o: _tr('~E~dit'), yielding=True)    # main_menu.nml:149

        _w22.text = _bind(lambda _o: _tr('~E~dit'), yielding=True)    # main_menu.nml:151
        _w22.command = Edit    # main_menu.nml:152
        _w22.key = 'F4'    # main_menu.nml:153

        _w23.text = _bind(lambda _o: _tr('~A~lternate edit'), yielding=True)    # main_menu.nml:155
        _w23.tooltip = _bind(    # main_menu.nml:156
            lambda _o: _tr('Edit with the editor F4 does not use: the external one, or the internal'),
            yielding=True,
        )
        _w23.command = AlternateEdit    # main_menu.nml:157
        _w23.key = 'Alt-F4'    # main_menu.nml:158

        _w25.text = _bind(lambda _o: _tr('Edit ~n~ew file...'), yielding=True)    # main_menu.nml:161
        _w25.command = EditNamed    # main_menu.nml:162
        _w25.key = 'Shift-F4'    # main_menu.nml:163

        _w26.text = _bind(lambda _o: _tr('~O~pen...'), yielding=True)    # main_menu.nml:166
        _w26.tooltip = _bind(    # main_menu.nml:167
            lambda _o: _tr('Edit a file chosen in a file box'),
            yielding=True,
        )
        _w26.command = OpenEdit    # main_menu.nml:168

        _w27.text = _bind(lambda _o: _tr('Open ~w~ith...'), yielding=True)    # main_menu.nml:171
        _w27.tooltip = _bind(    # main_menu.nml:172
            lambda _o: _tr('Open the file in a desktop application chosen from a list'),
            yielding=True,
        )
        _w27.command = OpenWith    # main_menu.nml:173

        _w28.text = _bind(lambda _o: _tr('~F~ind...'), yielding=True)    # main_menu.nml:175
        _w28.command = FindFile    # main_menu.nml:176
        _w28.key = 'Alt-F7'    # main_menu.nml:177

        _w29.text = _bind(lambda _o: _tr('Replace in files...'), yielding=True)    # main_menu.nml:181
        _w29.tooltip = _bind(    # main_menu.nml:182
            lambda _o: _tr('Find files holding a text and replace it in them, file by file'),
            yielding=True,
        )
        _w29.command = ReplaceInFiles    # main_menu.nml:183
        _w29.key = 'Alt-Shift-F7'    # main_menu.nml:184

        _w30.text = _bind(lambda _o: _tr('~C~opy...'), yielding=True)    # main_menu.nml:186
        _w30.command = Copy    # main_menu.nml:187
        _w30.key = 'F5'    # main_menu.nml:188

        _w31.text = _bind(lambda _o: _tr('~R~ename/Move...'), yielding=True)    # main_menu.nml:190
        _w31.command = RenameMove    # main_menu.nml:191
        _w31.key = 'F6'    # main_menu.nml:192

        _w32.text = _bind(lambda _o: _tr('~Q~uick rename...'), yielding=True)    # main_menu.nml:196
        _w32.tooltip = _bind(    # main_menu.nml:197
            lambda _o: _tr('Rename the file at the cursor in a small box'),
            yielding=True,
        )
        _w32.command = QuickRename    # main_menu.nml:198
        _w32.key = 'Shift-F6'    # main_menu.nml:199

        _w33.text = _bind(lambda _o: _tr('Create arch~i~ve...'), yielding=True)    # main_menu.nml:204
        _w33.command = ArchiveFiles    # main_menu.nml:205
        _w33.key = 'Shift-F1'    # main_menu.nml:206

        _w34.text = _bind(    # main_menu.nml:208
            lambda _o: _tr('Ex~t~ract archive...'),
            yielding=True,
        )
        _w34.command = ExtractArchive    # main_menu.nml:209
        _w34.key = 'Shift-F2'    # main_menu.nml:210

        self.file_symlinks.text = _bind(    # main_menu.nml:215
            lambda _o: _tr('~S~ymlinks'),
            yielding=True,
        )

        _w35.text = _bind(lambda _o: _tr('Create ~s~ymlink...'), yielding=True)    # main_menu.nml:217
        _w35.tooltip = _bind(    # main_menu.nml:218
            lambda _o: _tr('Make a symbolic link to each selected file'),
            yielding=True,
        )
        _w35.command = MakeLink    # main_menu.nml:219
        _w35.key = 'Shift-F5'    # main_menu.nml:220

        _w37.text = _bind(    # main_menu.nml:223
            lambda _o: _tr('~E~dit link target...'),
            yielding=True,
        )
        _w37.tooltip = _bind(    # main_menu.nml:224
            lambda _o: _tr('Change what the selected links point at'),
            yielding=True,
        )
        _w37.command = EditLinkTarget    # main_menu.nml:225

        _w38.text = _bind(lambda _o: _tr('Make ~r~elative'), yielding=True)    # main_menu.nml:227
        _w38.tooltip = _bind(    # main_menu.nml:228
            lambda _o: _tr("Rewrite each selected link's target relative to the link"),
            yielding=True,
        )
        _w38.command = LinkRelative    # main_menu.nml:229

        _w39.text = _bind(lambda _o: _tr('Make ~a~bsolute'), yielding=True)    # main_menu.nml:231
        _w39.tooltip = _bind(    # main_menu.nml:232
            lambda _o: _tr("Rewrite each selected link's target as a full path"),
            yielding=True,
        )
        _w39.command = LinkAbsolute    # main_menu.nml:233

        _w41.text = _bind(    # main_menu.nml:236
            lambda _o: _tr('Select ~b~roken links'),
            yielding=True,
        )
        _w41.tooltip = _bind(    # main_menu.nml:237
            lambda _o: _tr('Tag every link here that points nowhere'),
            yielding=True,
        )
        _w41.command = SelectBrokenLinks    # main_menu.nml:238

        _w42.text = _bind(lambda _o: _tr('Compare fi~l~es...'), yielding=True)    # main_menu.nml:242
        _w42.command = DiffFiles    # main_menu.nml:243

        _w43.text = _bind(lambda _o: _tr('~P~rint'), yielding=True)    # main_menu.nml:245
        _w43.command = PrintFile    # main_menu.nml:246
        _w43.key = 'Ctrl-F9'    # main_menu.nml:247

        _w44.text = _bind(lambda _o: _tr('~M~ake directory'), yielding=True)    # main_menu.nml:249
        _w44.command = MakeDirectory    # main_menu.nml:250
        _w44.key = 'F7'    # main_menu.nml:251

        _w45.text = _bind(lambda _o: _tr('~D~elete'), yielding=True)    # main_menu.nml:253
        _w45.command = Delete    # main_menu.nml:254
        _w45.key = 'F8'    # main_menu.nml:255

        self.file_restore_trash.text = _bind(    # main_menu.nml:262
            lambda _o: _tr('Restore from Tras~h~'),
            yielding=True,
        )
        self.file_restore_trash.tooltip = _bind(    # main_menu.nml:263
            lambda _o: _tr('Put the selected files back where they were deleted from'),
            yielding=True,
        )
        self.file_restore_trash.command = RestoreTrash    # main_menu.nml:264
        self.file_restore_trash.hidden = _bind(    # main_menu.nml:265
            lambda _o: not getattr(self.context, 'shows_trash', False)
        )

        _w46.text = _bind(    # main_menu.nml:267
            lambda _o: _tr('File ~A~ttributes...'),
            yielding=True,
        )
        _w46.tooltip = _bind(    # main_menu.nml:268
            lambda _o: _tr('Permissions, owner, group, dates, ACLs and extended attributes'),
            yielding=True,
        )
        _w46.command = ChangeAttributes    # main_menu.nml:269
        _w46.key = 'Alt-E'    # main_menu.nml:270

        _w47.text = _bind(lambda _o: _tr('UU E~n~code...'), yielding=True)    # main_menu.nml:272
        _w47.tooltip = _bind(    # main_menu.nml:273
            lambda _o: _tr('Encode the file as plain text, the old way of mailing files'),
            yielding=True,
        )
        _w47.command = UuEncode    # main_menu.nml:274
        _w47.key = 'Ctrl-F7'    # main_menu.nml:275

        _w48.text = _bind(lambda _o: _tr('~U~U Decode...'), yielding=True)    # main_menu.nml:277
        _w48.tooltip = _bind(    # main_menu.nml:278
            lambda _o: _tr('Decode the files UU-encoded in this file'),
            yielding=True,
        )
        _w48.command = UuDecode    # main_menu.nml:279
        _w48.key = 'Ctrl-F8'    # main_menu.nml:280

        self.file_checksums.text = _bind(    # main_menu.nml:285
            lambda _o: _tr('Chec~k~sums'),
            yielding=True,
        )

        _w49.text = _bind(lambda _o: _tr('~C~alculate...'), yielding=True)    # main_menu.nml:287
        _w49.tooltip = _bind(    # main_menu.nml:288
            lambda _o: _tr('Hash the tagged files and write their checksums to a list'),
            yielding=True,
        )
        _w49.command = CalculateChecksums    # main_menu.nml:289

        _w50.text = _bind(lambda _o: _tr('~V~erify'), yielding=True)    # main_menu.nml:291
        _w50.tooltip = _bind(    # main_menu.nml:292
            lambda _o: _tr('Hash the files a checksum list names again and check them'),
            yielding=True,
        )
        _w50.command = VerifyChecksums    # main_menu.nml:293

        self.file_encryption.text = _bind(    # main_menu.nml:298
            lambda _o: _tr('Encr~y~ption'),
            yielding=True,
        )

        _w51.text = _bind(lambda _o: _tr('~E~ncrypt...'), yielding=True)    # main_menu.nml:300
        _w51.tooltip = _bind(    # main_menu.nml:301
            lambda _o: _tr('Encrypt the tagged files with gpg or age, each beside itself'),
            yielding=True,
        )
        _w51.command = EncryptFiles    # main_menu.nml:302

        _w52.text = _bind(lambda _o: _tr('~D~ecrypt'), yielding=True)    # main_menu.nml:304
        _w52.tooltip = _bind(    # main_menu.nml:305
            lambda _o: _tr('Decrypt the tagged gpg or age files, each beside itself'),
            yielding=True,
        )
        _w52.command = DecryptFiles    # main_menu.nml:306

        _w53.text = _bind(lambda _o: _tr('Delete single file'), yielding=True)    # main_menu.nml:308
        _w53.tooltip = _bind(    # main_menu.nml:309
            lambda _o: _tr('Delete the file at the cursor, not the selection'),
            yielding=True,
        )
        _w53.command = DeleteSingle    # main_menu.nml:310
        _w53.key = 'Shift-Del'    # main_menu.nml:311

        _w55.text = _bind(    # main_menu.nml:314
            lambda _o: _tr('Execute ~O~S command'),
            yielding=True,
        )
        _w55.tooltip = _bind(    # main_menu.nml:315
            lambda _o: _tr('Type a command in a box and run it'),
            yielding=True,
        )
        _w55.command = ExecuteOsCommand    # main_menu.nml:316

        _w56.text = _bind(lambda _o: _tr('E~x~it'), yielding=True)    # main_menu.nml:318
        _w56.command = Quit    # main_menu.nml:319
        _w56.key = 'Alt-X'    # main_menu.nml:320

        self.disk.text = _bind(lambda _o: _tr('~D~isk'), yielding=True)    # main_menu.nml:323
        self.disk.tooltip = _bind(    # main_menu.nml:324
            lambda _o: _tr('The directory tree, volumes and the Trash'),
            yielding=True,
        )

        _w57.text = _bind(lambda _o: _tr('~D~irectory tree'), yielding=True)    # main_menu.nml:326
        _w57.command = OpenTreeWindow    # main_menu.nml:327

        _w58.text = _bind(lambda _o: _tr('~V~olumes'), yielding=True)    # main_menu.nml:329
        _w58.tooltip = _bind(    # main_menu.nml:330
            lambda _o: _tr('Disks and partitions: mount, unmount and eject them'),
            yielding=True,
        )
        _w58.command = OpenVolumesWindow    # main_menu.nml:331

        _w59.text = _bind(lambda _o: _tr('Directory ~s~izes'), yielding=True)    # main_menu.nml:334
        _w59.tooltip = _bind(    # main_menu.nml:335
            lambda _o: _tr("What takes the room under the panel's directory, biggest first"),
            yielding=True,
        )
        _w59.command = OpenUsageWindow    # main_menu.nml:336

        _w61.text = _bind(lambda _o: _tr('~T~rash'), yielding=True)    # main_menu.nml:341
        _w61.command = OpenTrash    # main_menu.nml:342

        _w62.text = _bind(lambda _o: _tr('~E~mpty Trash'), yielding=True)    # main_menu.nml:344
        _w62.command = EmptyTrash    # main_menu.nml:345

        self.utilities.text = _bind(    # main_menu.nml:348
            lambda _o: _tr('~U~tilities'),
            yielding=True,
        )
        self.utilities.tooltip = _bind(    # main_menu.nml:349
            lambda _o: _tr('Calculator, calendar, remote links, the user menu and histories'),
            yielding=True,
        )

        _w63.text = _bind(    # main_menu.nml:351
            lambda _o: _tr('S~y~stem Information'),
            yielding=True,
        )
        _w63.command = SystemInfo    # main_menu.nml:352

        _w64.text = _bind(lambda _o: _tr('~P~rocess list'), yielding=True)    # main_menu.nml:357
        _w64.tooltip = _bind(    # main_menu.nml:358
            lambda _o: _tr('The running processes: sort them, see one, send it a signal'),
            yielding=True,
        )
        _w64.command = OpenProcessWindow    # main_menu.nml:359

        _w65.text = _bind(lambda _o: _tr('System mo~n~itor'), yielding=True)    # main_menu.nml:364
        _w65.tooltip = _bind(    # main_menu.nml:365
            lambda _o: _tr("Each processor's load, the memory and the temperature sensors, read live"),
            yielding=True,
        )
        _w65.command = OpenMonitorWindow    # main_menu.nml:366

        _w67.text = _bind(lambda _o: _tr('~C~alculator'), yielding=True)    # main_menu.nml:369
        _w67.command = Calculator    # main_menu.nml:370
        _w67.key = 'Ctrl-F6'    # main_menu.nml:371

        _w68.text = _bind(lambda _o: _tr('Ca~l~endar'), yielding=True)    # main_menu.nml:375
        _w68.command = OpenCalendar    # main_menu.nml:376

        _w69.text = _bind(lambda _o: _tr('Character ta~b~le'), yielding=True)    # main_menu.nml:378
        _w69.tooltip = _bind(    # main_menu.nml:379
            lambda _o: _tr('Pick a character to type where the cursor is'),
            yielding=True,
        )
        _w69.command = AsciiTable    # main_menu.nml:380
        _w69.key = 'Ctrl-B'    # main_menu.nml:381

        _w71.text = _bind(    # main_menu.nml:392
            lambda _o: _tr('~S~SH link (SFTP)...'),
            yielding=True,
        )
        _w71.command = NavyLink    # main_menu.nml:393
        _w71.key = 'Alt-F11'    # main_menu.nml:394

        _w72.text = _bind(lambda _o: _tr('~F~TP link...'), yielding=True)    # main_menu.nml:396
        _w72.command = FtpLink    # main_menu.nml:397

        _w73.text = _bind(    # main_menu.nml:399
            lambda _o: _tr('S~M~B link (Windows share)...'),
            yielding=True,
        )
        _w73.command = SmbLink    # main_menu.nml:400

        _w74.text = _bind(    # main_menu.nml:402
            lambda _o: _tr('S~3~ link (Amazon S3)...'),
            yielding=True,
        )
        _w74.command = S3Link    # main_menu.nml:403

        _w75.text = _bind(    # main_menu.nml:406
            lambda _o: _tr('~G~Vfs/KIO link (MTP, WebDAV...)...'),
            yielding=True,
        )
        _w75.tooltip = _bind(    # main_menu.nml:407
            lambda _o: _tr('A phone, a WebDAV share, Google Drive: anything the desktop can mount'),
            yielding=True,
        )
        _w75.command = GvfsLink    # main_menu.nml:408

        _w76.text = _bind(lambda _o: _tr('Rem~o~te shell...'), yielding=True)    # main_menu.nml:411
        _w76.tooltip = _bind(    # main_menu.nml:412
            lambda _o: _tr('A shell on the server the active panel is browsing over SSH'),
            yielding=True,
        )
        _w76.command = Terminal    # main_menu.nml:413

        _w77.text = _bind(lambda _o: _tr('~D~isconnect'), yielding=True)    # main_menu.nml:415
        _w77.tooltip = _bind(    # main_menu.nml:416
            lambda _o: _tr('Close a connection; its panels go back to the disk'),
            yielding=True,
        )
        _w77.command = HangUp    # main_menu.nml:417
        _w77.key = 'Alt-H'    # main_menu.nml:418

        _w78.text = _bind(lambda _o: _tr('Close ~r~oot access'), yielding=True)    # main_menu.nml:420
        _w78.tooltip = _bind(    # main_menu.nml:421
            lambda _o: _tr('End root access now, rather than after its timeout'),
            yielding=True,
        )
        _w78.command = CloseRootAccess    # main_menu.nml:422

        _w79.text = _bind(lambda _o: _tr('Saved l~i~nks...'), yielding=True)    # main_menu.nml:424
        _w79.tooltip = _bind(    # main_menu.nml:425
            lambda _o: _tr('The saved connections: edit them, or connect to one'),
            yielding=True,
        )
        _w79.command = EditLinks    # main_menu.nml:426

        _w81.text = _bind(lambda _o: _tr('Edi~t~ environment'), yielding=True)    # main_menu.nml:429
        _w81.tooltip = _bind(    # main_menu.nml:430
            lambda _o: _tr('Edit the environment variables commands run with'),
            yielding=True,
        )
        _w81.command = EnvEdit    # main_menu.nml:431

        _w82.text = _bind(lambda _o: _tr('~U~ser menu'), yielding=True)    # main_menu.nml:433
        _w82.command = UserMenu    # main_menu.nml:434
        _w82.key = 'F2'    # main_menu.nml:435

        _w83.text = _bind(lambda _o: _tr('Commands ~H~istory'), yielding=True)    # main_menu.nml:437
        _w83.command = HistoryList    # main_menu.nml:438
        _w83.key = 'Alt-F8'    # main_menu.nml:439

        _w84.text = _bind(    # main_menu.nml:442
            lambda _o: _tr('Fu~z~zy history search...'),
            yielding=True,
        )
        _w84.tooltip = _bind(    # main_menu.nml:443
            lambda _o: _tr('The commands typed, here and in the shell, searched by fzf'),
            yielding=True,
        )
        _w84.command = FuzzyHistory    # main_menu.nml:444
        _w84.key = 'Alt-Shift-F8'    # main_menu.nml:445

        _w85.text = _bind(lambda _o: _tr('File ~E~dit History'), yielding=True)    # main_menu.nml:447
        _w85.command = EditHistory    # main_menu.nml:448
        _w85.key = 'Alt-PgUp'    # main_menu.nml:449

        _w86.text = _bind(lambda _o: _tr('File ~V~iew History'), yielding=True)    # main_menu.nml:451
        _w86.command = ViewHistory    # main_menu.nml:452
        _w86.key = 'Alt-PgDn'    # main_menu.nml:453

        self.manager.text = _bind(lambda _o: _tr('~M~anager'), yielding=True)    # main_menu.nml:456
        self.manager.tooltip = _bind(    # main_menu.nml:457
            lambda _o: _tr('New file managers, swapping and hiding panels, bookmarks'),
            yielding=True,
        )

        _w87.text = _bind(lambda _o: _tr('~N~ew'), yielding=True)    # main_menu.nml:459
        _w87.command = NewManager    # main_menu.nml:460
        _w87.key = 'Ctrl-F3'    # main_menu.nml:461

        _w88.text = _bind(lambda _o: _tr('~S~wap panels'), yielding=True)    # main_menu.nml:463
        _w88.command = SwapPanels    # main_menu.nml:464
        _w88.key = 'Ctrl-U'    # main_menu.nml:465

        _w89.text = _bind(    # main_menu.nml:467
            lambda _o: _tr('Show/hide ~l~eft panel'),
            yielding=True,
        )
        _w89.command = HideLeft    # main_menu.nml:468
        _w89.key = 'Ctrl-F1'    # main_menu.nml:469

        _w90.text = _bind(    # main_menu.nml:471
            lambda _o: _tr('Show/hide ~r~ight panel'),
            yielding=True,
        )
        _w90.command = HideRight    # main_menu.nml:472
        _w90.key = 'Ctrl-F2'    # main_menu.nml:473

        _w91.text = _bind(    # main_menu.nml:475
            lambda _o: _tr('Show/hide inactive ~p~anel'),
            yielding=True,
        )
        _w91.tooltip = _bind(    # main_menu.nml:476
            lambda _o: _tr('Hide the panel without the keyboard, or show it again'),
            yielding=True,
        )
        _w91.command = HideInactive    # main_menu.nml:477
        _w91.key = 'Ctrl-P'    # main_menu.nml:478

        _w92.text = _bind(lambda _o: _tr('~M~iller columns'), yielding=True)    # main_menu.nml:482
        _w92.tooltip = _bind(    # main_menu.nml:483
            lambda _o: _tr('Browse in columns, each directory beside its parent'),
            yielding=True,
        )
        _w92.command = ToggleMiller    # main_menu.nml:484
        _w92.key = 'Alt-F12'    # main_menu.nml:485

        _w94.text = _bind(lambda _o: _tr('Bookmarks le~f~t'), yielding=True)    # main_menu.nml:488
        _w94.tooltip = _bind(    # main_menu.nml:489
            lambda _o: _tr('Send the left panel to a bookmarked directory'),
            yielding=True,
        )
        _w94.command = ChangeLeft    # main_menu.nml:490
        _w94.key = 'Alt-F1'    # main_menu.nml:491

        _w95.text = _bind(lambda _o: _tr('Bookmarks rig~h~t'), yielding=True)    # main_menu.nml:493
        _w95.tooltip = _bind(    # main_menu.nml:494
            lambda _o: _tr('Send the right panel to a bookmarked directory'),
            yielding=True,
        )
        _w95.command = ChangeRight    # main_menu.nml:495
        _w95.key = 'Alt-F2'    # main_menu.nml:496

        self.options.text = _bind(lambda _o: _tr('~O~ptions'), yielding=True)    # main_menu.nml:499
        self.options.tooltip = _bind(    # main_menu.nml:500
            lambda _o: _tr('Settings, configuration files, the desktop and colours'),
            yielding=True,
        )

        _w96.text = _bind(lambda _o: _tr('Sett~i~ngs...'), yielding=True)    # main_menu.nml:504
        _w96.tooltip = _bind(    # main_menu.nml:505
            lambda _o: _tr('Every setup page in one box, behind tabs'),
            yielding=True,
        )
        _w96.command = Settings    # main_menu.nml:506

        self.options_configuration.text = _bind(    # main_menu.nml:510
            lambda _o: _tr('~C~onfiguration'),
            yielding=True,
        )

        _w98.text = _bind(lambda _o: _tr('S~y~stem Setup...'), yielding=True)    # main_menu.nml:512
        _w98.command = SystemSetup    # main_menu.nml:513

        _w99.text = _bind(lambda _o: _tr('~S~tartup...'), yielding=True)    # main_menu.nml:515
        _w99.command = StartupSetup    # main_menu.nml:516

        _w100.text = _bind(lambda _o: _tr('~I~nterface...'), yielding=True)    # main_menu.nml:518
        _w100.command = InterfaceSetup    # main_menu.nml:519

        _w101.text = _bind(lambda _o: _tr('~C~onfirmations...'), yielding=True)    # main_menu.nml:521
        _w101.command = SetupConfirmation    # main_menu.nml:522

        _w103.text = _bind(lambda _o: _tr('Screen sa~v~ers...'), yielding=True)    # main_menu.nml:525
        _w103.command = SaversSetup    # main_menu.nml:526

        _w104.text = _bind(    # main_menu.nml:528
            lambda _o: _tr('C~o~untry support...'),
            yielding=True,
        )
        _w104.command = CountrySetup    # main_menu.nml:529

        _w105.text = _bind(    # main_menu.nml:531
            lambda _o: _tr('Comm~u~nications...'),
            yielding=True,
        )
        _w105.tooltip = _bind(    # main_menu.nml:532
            lambda _o: _tr('Settings for remote connections'),
            yielding=True,
        )
        _w105.command = SetupLink    # main_menu.nml:533

        _w107.text = _bind(lambda _o: _tr('~E~ditor/Viewer...'), yielding=True)    # main_menu.nml:536
        _w107.command = EditorDefaults    # main_menu.nml:537

        _w109.text = _bind(lambda _o: _tr('~K~ey bindings...'), yielding=True)    # main_menu.nml:540
        _w109.command = KeyBindingsSetup    # main_menu.nml:541

        self.options_file_manager.text = _bind(    # main_menu.nml:544
            lambda _o: _tr('~F~ile Manager'),
            yielding=True,
        )

        _w110.text = _bind(lambda _o: _tr('~S~etup...'), yielding=True)    # main_menu.nml:546
        _w110.command = FileManagerSetup    # main_menu.nml:547

        _w111.text = _bind(    # main_menu.nml:549
            lambda _o: _tr('~I~nformation panel...'),
            yielding=True,
        )
        _w111.tooltip = _bind(    # main_menu.nml:550
            lambda _o: _tr('What the information panel (Ctrl+L) shows'),
            yielding=True,
        )
        _w111.command = DriveInfoSetup    # main_menu.nml:551

        _w112.text = _bind(    # main_menu.nml:553
            lambda _o: _tr('New Manager ~d~efaults...'),
            yielding=True,
        )
        _w112.tooltip = _bind(    # main_menu.nml:554
            lambda _o: _tr("How a new file manager's panels start"),
            yielding=True,
        )
        _w112.command = FileManagerDefaults    # main_menu.nml:555

        _w113.text = _bind(    # main_menu.nml:557
            lambda _o: _tr('~C~olumn defaults...'),
            yielding=True,
        )
        _w113.tooltip = _bind(    # main_menu.nml:558
            lambda _o: _tr('The columns a new panel shows'),
            yielding=True,
        )
        _w113.command = ColumnDefaults    # main_menu.nml:559

        _w114.text = _bind(    # main_menu.nml:561
            lambda _o: _tr('~H~ighlight groups...'),
            yielding=True,
        )
        _w114.tooltip = _bind(    # main_menu.nml:562
            lambda _o: _tr('Which files the panels show in which colour'),
            yielding=True,
        )
        _w114.command = HighlightGroups    # main_menu.nml:563

        self.options_archives.text = _bind(    # main_menu.nml:566
            lambda _o: _tr('A~r~chives'),
            yielding=True,
        )

        _w115.text = _bind(    # main_menu.nml:568
            lambda _o: _tr('Current archiver...'),
            yielding=True,
        )
        _w115.key = 'Alt-N'    # main_menu.nml:569

        _w117.text = _bind(    # main_menu.nml:572
            lambda _o: _tr('~Q~uick run file edit...'),
            yielding=True,
        )
        _w117.tooltip = _bind(    # main_menu.nml:573
            lambda _o: _tr('Edit quickrun.ini: the commands Ctrl+Shift+F1 to F10 run'),
            yielding=True,
        )
        _w117.command = EditQuickRun    # main_menu.nml:574

        _w118.text = _bind(    # main_menu.nml:576
            lambda _o: _tr('E~x~tension file edit...'),
            yielding=True,
        )
        _w118.tooltip = _bind(    # main_menu.nml:577
            lambda _o: _tr('Edit extensions.ini: what Enter runs for each kind of file'),
            yielding=True,
        )
        _w118.command = ExtFileEdit    # main_menu.nml:578

        _w119.text = _bind(    # main_menu.nml:580
            lambda _o: _tr('~H~ighlight file edit...'),
            yielding=True,
        )
        _w119.tooltip = _bind(    # main_menu.nml:581
            lambda _o: _tr('Edit highlight.ini: which syntax colours which file'),
            yielding=True,
        )
        _w119.command = EditHGL    # main_menu.nml:582

        _w120.text = _bind(    # main_menu.nml:584
            lambda _o: _tr('Macro file e~d~it...'),
            yielding=True,
        )
        _w120.tooltip = _bind(    # main_menu.nml:585
            lambda _o: _tr("Edit macros.ini: the editor's macros, offered by Ctrl+J 0"),
            yielding=True,
        )
        _w120.command = EditMacros    # main_menu.nml:586

        _w121.text = _bind(    # main_menu.nml:588
            lambda _o: _tr('~G~lobal menu definition...'),
            yielding=True,
        )
        _w121.tooltip = _bind(    # main_menu.nml:589
            lambda _o: _tr('Edit the F2 user menu used everywhere'),
            yielding=True,
        )
        _w121.command = MenuFileEdit    # main_menu.nml:590

        _w122.text = _bind(    # main_menu.nml:592
            lambda _o: _tr('Local ~m~enu definition...'),
            yielding=True,
        )
        _w122.tooltip = _bind(    # main_menu.nml:593
            lambda _o: _tr("Edit this directory's own F2 user menu"),
            yielding=True,
        )
        _w122.command = LocalMenuFileEdit    # main_menu.nml:594

        _w123.text = _bind(lambda _o: _tr('~V~iewers...'), yielding=True)    # main_menu.nml:596
        _w123.tooltip = _bind(    # main_menu.nml:597
            lambda _o: _tr('Edit viewers.ini: the external viewer for each kind of file'),
            yielding=True,
        )
        _w123.command = ExternalViewers    # main_menu.nml:598

        _w124.text = _bind(lambda _o: _tr('~E~ditors...'), yielding=True)    # main_menu.nml:600
        _w124.tooltip = _bind(    # main_menu.nml:601
            lambda _o: _tr('Edit editors.ini: the external editor for each kind of file'),
            yielding=True,
        )
        _w124.command = ExternalEditors    # main_menu.nml:602

        _w126.text = _bind(lambda _o: _tr('~S~ave desktop'), yielding=True)    # main_menu.nml:605
        _w126.tooltip = _bind(    # main_menu.nml:606
            lambda _o: _tr('Keep the open windows, to have them back later'),
            yielding=True,
        )
        _w126.command = SaveDesktop    # main_menu.nml:607

        _w127.text = _bind(lambda _o: _tr('~L~oad desktop'), yielding=True)    # main_menu.nml:609
        _w127.tooltip = _bind(    # main_menu.nml:610
            lambda _o: _tr('Replace these windows with the ones last saved'),
            yielding=True,
        )
        _w127.command = LoadDesktop    # main_menu.nml:611

        _w129.text = _bind(lambda _o: _tr('C~o~lors...'), yielding=True)    # main_menu.nml:614
        _w129.command = ChangeColors    # main_menu.nml:615

        _w130.text = _bind(lambda _o: _tr('S~t~ore palette'), yielding=True)    # main_menu.nml:617
        _w130.tooltip = _bind(    # main_menu.nml:618
            lambda _o: _tr('Save the colours as a theme of your own'),
            yielding=True,
        )
        _w130.command = StoreColors    # main_menu.nml:619

        _w131.text = _bind(lambda _o: _tr('Lo~a~d palette'), yielding=True)    # main_menu.nml:621
        _w131.tooltip = _bind(    # main_menu.nml:622
            lambda _o: _tr('Use colours saved in a file'),
            yielding=True,
        )
        _w131.command = LoadColors    # main_menu.nml:623

        self.window.text = _bind(lambda _o: _tr('~W~indow'), yielding=True)    # main_menu.nml:626
        self.window.tooltip = _bind(    # main_menu.nml:627
            lambda _o: _tr('Arrange, switch between and close windows'),
            yielding=True,
        )

        _w132.text = _bind(lambda _o: _tr('~T~ile'), yielding=True)    # main_menu.nml:629
        _w132.command = TileWindows    # main_menu.nml:630

        _w133.text = _bind(lambda _o: _tr('C~a~scade'), yielding=True)    # main_menu.nml:632
        _w133.command = CascadeWindows    # main_menu.nml:633

        _w134.text = _bind(lambda _o: _tr('Cl~o~se all'), yielding=True)    # main_menu.nml:635
        _w134.command = CloseAllWindows    # main_menu.nml:636

        _w136.text = _bind(lambda _o: _tr('~S~ize/Move'), yielding=True)    # main_menu.nml:639
        _w136.tooltip = _bind(    # main_menu.nml:640
            lambda _o: _tr('Move and size the window with the keyboard'),
            yielding=True,
        )
        _w136.command = SizeMoveWindow    # main_menu.nml:641
        _w136.key = 'Ctrl-F5'    # main_menu.nml:642

        _w137.text = _bind(lambda _o: _tr('~Z~oom'), yielding=True)    # main_menu.nml:644
        _w137.command = ZoomWindow    # main_menu.nml:645
        _w137.key = 'Alt-Z'    # main_menu.nml:646

        _w138.text = _bind(lambda _o: _tr('~N~ext'), yielding=True)    # main_menu.nml:648
        _w138.command = NextWindow    # main_menu.nml:649
        _w138.key = 'F9'    # main_menu.nml:650

        _w139.text = _bind(lambda _o: _tr('~P~revious'), yielding=True)    # main_menu.nml:652
        _w139.command = PreviousWindow    # main_menu.nml:653
        _w139.key = 'Shift-F9'    # main_menu.nml:654

        _w140.text = _bind(lambda _o: _tr('~C~lose'), yielding=True)    # main_menu.nml:656
        _w140.command = CloseWindow    # main_menu.nml:657
        _w140.key = 'Ctrl-F4'    # main_menu.nml:658

        _w142.text = _bind(lambda _o: _tr('~L~ist...'), yielding=True)    # main_menu.nml:661
        _w142.tooltip = _bind(    # main_menu.nml:662
            lambda _o: _tr('All the windows, to switch to one or close it'),
            yielding=True,
        )
        _w142.command = WindowManager    # main_menu.nml:663
        _w142.key = 'Alt-0'    # main_menu.nml:664

        _w143.text = _bind(    # main_menu.nml:667
            lambda _o: _tr('~B~ackground operation...'),
            yielding=True,
        )
        _w143.tooltip = _bind(    # main_menu.nml:668
            lambda _o: _tr('Bring back the progress box of a copy or an erase running in the background'),
            yielding=True,
        )
        _w143.command = ShowBackground    # main_menu.nml:669
