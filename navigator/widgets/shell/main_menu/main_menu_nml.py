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
from navigator.widgets.manager.commands import RestoreTrash, AlternateEdit, AlternateView, ArchiveFiles, Calculator, ChangeAttributes, ChangeLeft, ChangeRight, Copy, Delete, DeleteSingle, DiffFiles, Edit, EditNamed, ExtractArchive, ExtractTo, ArcTest, MultiRename, Undo, FindFile, ReplaceInFiles, OpenWith, HideInactive, HideLeft, HideRight, MakeDirectory, MakeLink, EditLinkTarget, LinkAbsolute, LinkRelative, SelectBrokenLinks, ShowHardLinks, QuickRename, RenameMove, SwapPanels, ToggleMiller, UserMenu, UuDecode, UuEncode, SplitCombine, CalculateChecksums, VerifyChecksums, EncryptFiles, DecryptFiles, View, ViewAsDataBase, ViewAsHex, ViewAsSpreadsheet, ViewAsText    # main_menu.nml:2
from navigator.widgets.shell.commands import OpenEdit, OpenView, About, OpenCommandPalette, CloseRootAccess, ShowBackground, EditLinks, FtpLink, GvfsLink, S3Link, DockerLink, PodmanLink, AdbLink, DockerShell, PodmanShell, AdbShell, Game, HangUp, NavyLink, Terminal, SetupLink, SmbLink, SaversSetup, CountrySetup, ScreenRest, ToggleTrashCan, OpenTrash, EmptyTrash, ChangeColors, ColumnDefaults, HighlightGroups, EditQuickRun, ExtFileEdit, EditHGL, EditMacros, ExternalViewers, ExternalEditors, LoadColors, StoreColors, LoadDesktop, SaveDesktop, DriveInfoSetup, EditHistory, EnvEdit, ExecuteOsCommand, HistoryList, FuzzyHistory, OpenCalendar, SystemInfo, EditorDefaults, FileManagerDefaults, FileManagerSetup, InterfaceSetup, KeyBindingsSetup, LocalMenuFileEdit, MenuFileEdit, NewManager, OpenTreeWindow, OpenUsageWindow, OpenVolumesWindow, OpenProcessWindow, OpenMonitorWindow, SetupConfirmation, Settings, StartupSetup, SystemSetup, ViewHistory    # main_menu.nml:3
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
    file_rename_tools: SubMenu    # main_menu.nml:196
    file_archive: SubMenu    # main_menu.nml:223
    file_symlinks: SubMenu    # main_menu.nml:251
    file_restore_trash: MenuItem    # main_menu.nml:310
    file_encoding: SubMenu    # main_menu.nml:323
    file_checksums: SubMenu    # main_menu.nml:340
    file_encryption: SubMenu    # main_menu.nml:353
    disk: SubMenu    # main_menu.nml:378
    utilities: SubMenu    # main_menu.nml:403
    utilities_link: SubMenu    # main_menu.nml:450
    utilities_shell: SubMenu    # main_menu.nml:487
    manager: SubMenu    # main_menu.nml:547
    options: SubMenu    # main_menu.nml:590
    options_configuration: SubMenu    # main_menu.nml:601
    options_file_manager: SubMenu    # main_menu.nml:635
    options_archives: SubMenu    # main_menu.nml:657
    window: SubMenu    # main_menu.nml:717

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
        self.file_rename_tools = SubMenu(parent=self.file)    # main_menu.nml:195
        _w32 = MenuItem(parent=self.file_rename_tools)    # main_menu.nml:201
        _w33 = MenuItem(parent=self.file_rename_tools)    # main_menu.nml:208
        _w34 = MenuItem(parent=self.file)    # main_menu.nml:214
        self.file_archive = SubMenu(parent=self.file)    # main_menu.nml:222
        _w35 = MenuItem(parent=self.file_archive)    # main_menu.nml:228
        _w36 = MenuItem(parent=self.file_archive)    # main_menu.nml:232
        _w37 = MenuLine(parent=self.file_archive)    # main_menu.nml:236
        _w38 = MenuItem(parent=self.file_archive)    # main_menu.nml:239
        _w39 = MenuItem(parent=self.file_archive)    # main_menu.nml:243
        self.file_symlinks = SubMenu(parent=self.file)    # main_menu.nml:250
        _w40 = MenuItem(parent=self.file_symlinks)    # main_menu.nml:253
        _w41 = MenuLine(parent=self.file_symlinks)    # main_menu.nml:258
        _w42 = MenuItem(parent=self.file_symlinks)    # main_menu.nml:259
        _w43 = MenuItem(parent=self.file_symlinks)    # main_menu.nml:263
        _w44 = MenuItem(parent=self.file_symlinks)    # main_menu.nml:267
        _w45 = MenuLine(parent=self.file_symlinks)    # main_menu.nml:271
        _w46 = MenuItem(parent=self.file_symlinks)    # main_menu.nml:272
        _w47 = MenuLine(parent=self.file_symlinks)    # main_menu.nml:276
        _w48 = MenuItem(parent=self.file_symlinks)    # main_menu.nml:277
        _w49 = MenuItem(parent=self.file)    # main_menu.nml:284
        _w50 = MenuItem(parent=self.file)    # main_menu.nml:290
        _w51 = MenuItem(parent=self.file)    # main_menu.nml:293
        _w52 = MenuItem(parent=self.file)    # main_menu.nml:297
        _w53 = MenuItem(parent=self.file)    # main_menu.nml:301
        self.file_restore_trash = MenuItem(parent=self.file)    # main_menu.nml:309
        _w54 = MenuItem(parent=self.file)    # main_menu.nml:315
        self.file_encoding = SubMenu(parent=self.file)    # main_menu.nml:322
        _w55 = MenuItem(parent=self.file_encoding)    # main_menu.nml:326
        _w56 = MenuItem(parent=self.file_encoding)    # main_menu.nml:331
        _w57 = MenuLine(parent=self.file_encoding)    # main_menu.nml:336
        self.file_checksums = SubMenu(parent=self.file_encoding)    # main_menu.nml:339
        _w58 = MenuItem(parent=self.file_checksums)    # main_menu.nml:342
        _w59 = MenuItem(parent=self.file_checksums)    # main_menu.nml:346
        self.file_encryption = SubMenu(parent=self.file_encoding)    # main_menu.nml:352
        _w60 = MenuItem(parent=self.file_encryption)    # main_menu.nml:355
        _w61 = MenuItem(parent=self.file_encryption)    # main_menu.nml:359
        _w62 = MenuItem(parent=self.file)    # main_menu.nml:363
        _w63 = MenuLine(parent=self.file)    # main_menu.nml:368
        _w64 = MenuItem(parent=self.file)    # main_menu.nml:369
        _w65 = MenuItem(parent=self.file)    # main_menu.nml:373
        self.disk = SubMenu(parent=self)    # main_menu.nml:377
        _w66 = MenuItem(parent=self.disk)    # main_menu.nml:381
        _w67 = MenuItem(parent=self.disk)    # main_menu.nml:384
        _w68 = MenuItem(parent=self.disk)    # main_menu.nml:389
        _w69 = MenuLine(parent=self.disk)    # main_menu.nml:395
        _w70 = MenuItem(parent=self.disk)    # main_menu.nml:396
        _w71 = MenuItem(parent=self.disk)    # main_menu.nml:399
        self.utilities = SubMenu(parent=self)    # main_menu.nml:402
        _w72 = MenuItem(parent=self.utilities)    # main_menu.nml:406
        _w73 = MenuItem(parent=self.utilities)    # main_menu.nml:412
        _w74 = MenuItem(parent=self.utilities)    # main_menu.nml:419
        _w75 = MenuLine(parent=self.utilities)    # main_menu.nml:423
        _w76 = MenuItem(parent=self.utilities)    # main_menu.nml:424
        _w77 = MenuItem(parent=self.utilities)    # main_menu.nml:430
        _w78 = MenuItem(parent=self.utilities)    # main_menu.nml:433
        _w79 = MenuLine(parent=self.utilities)    # main_menu.nml:438
        self.utilities_link = SubMenu(parent=self.utilities)    # main_menu.nml:449
        _w80 = MenuItem(parent=self.utilities_link)    # main_menu.nml:453
        _w81 = MenuItem(parent=self.utilities_link)    # main_menu.nml:457
        _w82 = MenuItem(parent=self.utilities_link)    # main_menu.nml:460
        _w83 = MenuItem(parent=self.utilities_link)    # main_menu.nml:463
        _w84 = MenuItem(parent=self.utilities_link)    # main_menu.nml:467
        _w85 = MenuLine(parent=self.utilities_link)    # main_menu.nml:471
        _w86 = MenuItem(parent=self.utilities_link)    # main_menu.nml:473
        _w87 = MenuItem(parent=self.utilities_link)    # main_menu.nml:477
        _w88 = MenuItem(parent=self.utilities_link)    # main_menu.nml:481
        self.utilities_shell = SubMenu(parent=self.utilities)    # main_menu.nml:486
        _w89 = MenuItem(parent=self.utilities_shell)    # main_menu.nml:490
        _w90 = MenuItem(parent=self.utilities_shell)    # main_menu.nml:494
        _w91 = MenuItem(parent=self.utilities_shell)    # main_menu.nml:498
        _w92 = MenuItem(parent=self.utilities_shell)    # main_menu.nml:502
        _w93 = MenuItem(parent=self.utilities)    # main_menu.nml:506
        _w94 = MenuItem(parent=self.utilities)    # main_menu.nml:511
        _w95 = MenuItem(parent=self.utilities)    # main_menu.nml:515
        _w96 = MenuLine(parent=self.utilities)    # main_menu.nml:519
        _w97 = MenuItem(parent=self.utilities)    # main_menu.nml:520
        _w98 = MenuItem(parent=self.utilities)    # main_menu.nml:524
        _w99 = MenuItem(parent=self.utilities)    # main_menu.nml:528
        _w100 = MenuItem(parent=self.utilities)    # main_menu.nml:533
        _w101 = MenuItem(parent=self.utilities)    # main_menu.nml:538
        _w102 = MenuItem(parent=self.utilities)    # main_menu.nml:542
        self.manager = SubMenu(parent=self)    # main_menu.nml:546
        _w103 = MenuItem(parent=self.manager)    # main_menu.nml:550
        _w104 = MenuItem(parent=self.manager)    # main_menu.nml:554
        _w105 = MenuItem(parent=self.manager)    # main_menu.nml:558
        _w106 = MenuItem(parent=self.manager)    # main_menu.nml:562
        _w107 = MenuItem(parent=self.manager)    # main_menu.nml:566
        _w108 = MenuItem(parent=self.manager)    # main_menu.nml:573
        _w109 = MenuLine(parent=self.manager)    # main_menu.nml:578
        _w110 = MenuItem(parent=self.manager)    # main_menu.nml:579
        _w111 = MenuItem(parent=self.manager)    # main_menu.nml:584
        self.options = SubMenu(parent=self)    # main_menu.nml:589
        _w112 = MenuItem(parent=self.options)    # main_menu.nml:595
        _w113 = MenuLine(parent=self.options)    # main_menu.nml:599
        self.options_configuration = SubMenu(parent=self.options)    # main_menu.nml:600
        _w114 = MenuItem(parent=self.options_configuration)    # main_menu.nml:603
        _w115 = MenuItem(parent=self.options_configuration)    # main_menu.nml:606
        _w116 = MenuItem(parent=self.options_configuration)    # main_menu.nml:609
        _w117 = MenuItem(parent=self.options_configuration)    # main_menu.nml:612
        _w118 = MenuLine(parent=self.options_configuration)    # main_menu.nml:615
        _w119 = MenuItem(parent=self.options_configuration)    # main_menu.nml:616
        _w120 = MenuItem(parent=self.options_configuration)    # main_menu.nml:619
        _w121 = MenuItem(parent=self.options_configuration)    # main_menu.nml:622
        _w122 = MenuLine(parent=self.options_configuration)    # main_menu.nml:626
        _w123 = MenuItem(parent=self.options_configuration)    # main_menu.nml:627
        _w124 = MenuLine(parent=self.options_configuration)    # main_menu.nml:630
        _w125 = MenuItem(parent=self.options_configuration)    # main_menu.nml:631
        self.options_file_manager = SubMenu(parent=self.options)    # main_menu.nml:634
        _w126 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:637
        _w127 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:640
        _w128 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:644
        _w129 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:648
        _w130 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:652
        self.options_archives = SubMenu(parent=self.options)    # main_menu.nml:656
        _w131 = MenuItem(parent=self.options_archives)    # main_menu.nml:659
        _w132 = MenuLine(parent=self.options)    # main_menu.nml:662
        _w133 = MenuItem(parent=self.options)    # main_menu.nml:663
        _w134 = MenuItem(parent=self.options)    # main_menu.nml:667
        _w135 = MenuItem(parent=self.options)    # main_menu.nml:671
        _w136 = MenuItem(parent=self.options)    # main_menu.nml:675
        _w137 = MenuItem(parent=self.options)    # main_menu.nml:679
        _w138 = MenuItem(parent=self.options)    # main_menu.nml:683
        _w139 = MenuItem(parent=self.options)    # main_menu.nml:687
        _w140 = MenuItem(parent=self.options)    # main_menu.nml:691
        _w141 = MenuLine(parent=self.options)    # main_menu.nml:695
        _w142 = MenuItem(parent=self.options)    # main_menu.nml:696
        _w143 = MenuItem(parent=self.options)    # main_menu.nml:700
        _w144 = MenuLine(parent=self.options)    # main_menu.nml:704
        _w145 = MenuItem(parent=self.options)    # main_menu.nml:705
        _w146 = MenuItem(parent=self.options)    # main_menu.nml:708
        _w147 = MenuItem(parent=self.options)    # main_menu.nml:712
        self.window = SubMenu(parent=self)    # main_menu.nml:716
        _w148 = MenuItem(parent=self.window)    # main_menu.nml:720
        _w149 = MenuItem(parent=self.window)    # main_menu.nml:723
        _w150 = MenuItem(parent=self.window)    # main_menu.nml:726
        _w151 = MenuLine(parent=self.window)    # main_menu.nml:729
        _w152 = MenuItem(parent=self.window)    # main_menu.nml:730
        _w153 = MenuItem(parent=self.window)    # main_menu.nml:735
        _w154 = MenuItem(parent=self.window)    # main_menu.nml:739
        _w155 = MenuItem(parent=self.window)    # main_menu.nml:743
        _w156 = MenuItem(parent=self.window)    # main_menu.nml:747
        _w157 = MenuLine(parent=self.window)    # main_menu.nml:751
        _w158 = MenuItem(parent=self.window)    # main_menu.nml:752
        _w159 = MenuItem(parent=self.window)    # main_menu.nml:758

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

        self.file_rename_tools.text = _bind(    # main_menu.nml:197
            lambda _o: _tr('Rename ~t~ools'),
            yielding=True,
        )
        self.file_rename_tools.tooltip = _bind(    # main_menu.nml:198
            lambda _o: _tr('Quick rename and multi-rename'),
            yielding=True,
        )

        _w32.text = _bind(lambda _o: _tr('~Q~uick rename...'), yielding=True)    # main_menu.nml:202
        _w32.tooltip = _bind(    # main_menu.nml:203
            lambda _o: _tr('Rename the file at the cursor in a small box'),
            yielding=True,
        )
        _w32.command = QuickRename    # main_menu.nml:204
        _w32.key = 'Shift-F6'    # main_menu.nml:205

        _w33.text = _bind(lambda _o: _tr('M~u~lti-rename...'), yielding=True)    # main_menu.nml:209
        _w33.tooltip = _bind(    # main_menu.nml:210
            lambda _o: _tr('Rename the tagged files by a pattern'),
            yielding=True,
        )
        _w33.command = MultiRename    # main_menu.nml:211
        _w33.key = 'Alt-A'    # main_menu.nml:212

        _w34.text = _bind(    # main_menu.nml:215
            lambda _o: _tr('~U~ndo file operation'),
            yielding=True,
        )
        _w34.tooltip = _bind(    # main_menu.nml:216
            lambda _o: _tr('Take back the last copy, move, rename, delete to Trash or new directory'),
            yielding=True,
        )
        _w34.command = Undo    # main_menu.nml:217
        _w34.key = 'Ctrl-Z'    # main_menu.nml:218

        self.file_archive.text = _bind(    # main_menu.nml:224
            lambda _o: _tr('Arch~i~ve'),
            yielding=True,
        )
        self.file_archive.tooltip = _bind(    # main_menu.nml:225
            lambda _o: _tr('Create, extract and test archives'),
            yielding=True,
        )

        _w35.text = _bind(lambda _o: _tr('Create arch~i~ve...'), yielding=True)    # main_menu.nml:229
        _w35.command = ArchiveFiles    # main_menu.nml:230
        _w35.key = 'Shift-F1'    # main_menu.nml:231

        _w36.text = _bind(    # main_menu.nml:233
            lambda _o: _tr('Ex~t~ract archive...'),
            yielding=True,
        )
        _w36.command = ExtractArchive    # main_menu.nml:234
        _w36.key = 'Shift-F2'    # main_menu.nml:235

        _w38.text = _bind(lambda _o: _tr('E~x~tract to...'), yielding=True)    # main_menu.nml:240
        _w38.command = ExtractTo    # main_menu.nml:241
        _w38.key = 'Shift-F2'    # main_menu.nml:242

        _w39.text = _bind(lambda _o: _tr('Test archive'), yielding=True)    # main_menu.nml:244
        _w39.tooltip = _bind(    # main_menu.nml:245
            lambda _o: _tr('Read the archive through and check it for errors'),
            yielding=True,
        )
        _w39.command = ArcTest    # main_menu.nml:246

        self.file_symlinks.text = _bind(    # main_menu.nml:252
            lambda _o: _tr('Link~s~'),
            yielding=True,
        )

        _w40.text = _bind(lambda _o: _tr('Create ~l~ink...'), yielding=True)    # main_menu.nml:254
        _w40.tooltip = _bind(    # main_menu.nml:255
            lambda _o: _tr('Make a symbolic or hard link to each selected file'),
            yielding=True,
        )
        _w40.command = MakeLink    # main_menu.nml:256
        _w40.key = 'Shift-F5'    # main_menu.nml:257

        _w42.text = _bind(    # main_menu.nml:260
            lambda _o: _tr('~E~dit link target...'),
            yielding=True,
        )
        _w42.tooltip = _bind(    # main_menu.nml:261
            lambda _o: _tr('Change what the selected links point at'),
            yielding=True,
        )
        _w42.command = EditLinkTarget    # main_menu.nml:262

        _w43.text = _bind(lambda _o: _tr('Make ~r~elative'), yielding=True)    # main_menu.nml:264
        _w43.tooltip = _bind(    # main_menu.nml:265
            lambda _o: _tr("Rewrite each selected link's target relative to the link"),
            yielding=True,
        )
        _w43.command = LinkRelative    # main_menu.nml:266

        _w44.text = _bind(lambda _o: _tr('Make ~a~bsolute'), yielding=True)    # main_menu.nml:268
        _w44.tooltip = _bind(    # main_menu.nml:269
            lambda _o: _tr("Rewrite each selected link's target as a full path"),
            yielding=True,
        )
        _w44.command = LinkAbsolute    # main_menu.nml:270

        _w46.text = _bind(    # main_menu.nml:273
            lambda _o: _tr('Select ~b~roken links'),
            yielding=True,
        )
        _w46.tooltip = _bind(    # main_menu.nml:274
            lambda _o: _tr('Tag every link here that points nowhere'),
            yielding=True,
        )
        _w46.command = SelectBrokenLinks    # main_menu.nml:275

        _w48.text = _bind(lambda _o: _tr('Show ~h~ard links'), yielding=True)    # main_menu.nml:278
        _w48.tooltip = _bind(    # main_menu.nml:279
            lambda _o: _tr('List every name the file at the cursor has on its file system'),
            yielding=True,
        )
        _w48.command = ShowHardLinks    # main_menu.nml:280

        _w49.text = _bind(lambda _o: _tr('Split/com~b~ine...'), yielding=True)    # main_menu.nml:285
        _w49.tooltip = _bind(    # main_menu.nml:286
            lambda _o: _tr('Cut the file into parts of a given size, or put a split file back together'),
            yielding=True,
        )
        _w49.command = SplitCombine    # main_menu.nml:287

        _w50.text = _bind(lambda _o: _tr('Compare fi~l~es...'), yielding=True)    # main_menu.nml:291
        _w50.command = DiffFiles    # main_menu.nml:292

        _w51.text = _bind(lambda _o: _tr('~P~rint'), yielding=True)    # main_menu.nml:294
        _w51.command = PrintFile    # main_menu.nml:295
        _w51.key = 'Ctrl-F9'    # main_menu.nml:296

        _w52.text = _bind(lambda _o: _tr('~M~ake directory'), yielding=True)    # main_menu.nml:298
        _w52.command = MakeDirectory    # main_menu.nml:299
        _w52.key = 'F7'    # main_menu.nml:300

        _w53.text = _bind(lambda _o: _tr('~D~elete'), yielding=True)    # main_menu.nml:302
        _w53.command = Delete    # main_menu.nml:303
        _w53.key = 'F8'    # main_menu.nml:304

        self.file_restore_trash.text = _bind(    # main_menu.nml:311
            lambda _o: _tr('Restore from Tras~h~'),
            yielding=True,
        )
        self.file_restore_trash.tooltip = _bind(    # main_menu.nml:312
            lambda _o: _tr('Put the selected files back where they were deleted from'),
            yielding=True,
        )
        self.file_restore_trash.command = RestoreTrash    # main_menu.nml:313
        self.file_restore_trash.hidden = _bind(    # main_menu.nml:314
            lambda _o: not getattr(self.context, 'shows_trash', False)
        )

        _w54.text = _bind(    # main_menu.nml:316
            lambda _o: _tr('File ~A~ttributes...'),
            yielding=True,
        )
        _w54.tooltip = _bind(    # main_menu.nml:317
            lambda _o: _tr('Permissions, owner, group, dates, ACLs and extended attributes'),
            yielding=True,
        )
        _w54.command = ChangeAttributes    # main_menu.nml:318
        _w54.key = 'Alt-E'    # main_menu.nml:319

        self.file_encoding.text = _bind(    # main_menu.nml:324
            lambda _o: _tr('E~n~coding'),
            yielding=True,
        )
        self.file_encoding.tooltip = _bind(    # main_menu.nml:325
            lambda _o: _tr('UU encoding, checksums and encryption'),
            yielding=True,
        )

        _w55.text = _bind(lambda _o: _tr('UU E~n~code...'), yielding=True)    # main_menu.nml:327
        _w55.tooltip = _bind(    # main_menu.nml:328
            lambda _o: _tr('Encode the file as plain text, the old way of mailing files'),
            yielding=True,
        )
        _w55.command = UuEncode    # main_menu.nml:329
        _w55.key = 'Ctrl-F7'    # main_menu.nml:330

        _w56.text = _bind(lambda _o: _tr('~U~U Decode...'), yielding=True)    # main_menu.nml:332
        _w56.tooltip = _bind(    # main_menu.nml:333
            lambda _o: _tr('Decode the files UU-encoded in this file'),
            yielding=True,
        )
        _w56.command = UuDecode    # main_menu.nml:334
        _w56.key = 'Ctrl-F8'    # main_menu.nml:335

        self.file_checksums.text = _bind(    # main_menu.nml:341
            lambda _o: _tr('Chec~k~sums'),
            yielding=True,
        )

        _w58.text = _bind(lambda _o: _tr('~C~alculate...'), yielding=True)    # main_menu.nml:343
        _w58.tooltip = _bind(    # main_menu.nml:344
            lambda _o: _tr('Hash the tagged files and write their checksums to a list'),
            yielding=True,
        )
        _w58.command = CalculateChecksums    # main_menu.nml:345

        _w59.text = _bind(lambda _o: _tr('~V~erify'), yielding=True)    # main_menu.nml:347
        _w59.tooltip = _bind(    # main_menu.nml:348
            lambda _o: _tr('Hash the files a checksum list names again and check them'),
            yielding=True,
        )
        _w59.command = VerifyChecksums    # main_menu.nml:349

        self.file_encryption.text = _bind(    # main_menu.nml:354
            lambda _o: _tr('Encr~y~ption'),
            yielding=True,
        )

        _w60.text = _bind(lambda _o: _tr('~E~ncrypt...'), yielding=True)    # main_menu.nml:356
        _w60.tooltip = _bind(    # main_menu.nml:357
            lambda _o: _tr('Encrypt the tagged files with gpg or age, each beside itself'),
            yielding=True,
        )
        _w60.command = EncryptFiles    # main_menu.nml:358

        _w61.text = _bind(lambda _o: _tr('~D~ecrypt'), yielding=True)    # main_menu.nml:360
        _w61.tooltip = _bind(    # main_menu.nml:361
            lambda _o: _tr('Decrypt the tagged gpg or age files, each beside itself'),
            yielding=True,
        )
        _w61.command = DecryptFiles    # main_menu.nml:362

        _w62.text = _bind(lambda _o: _tr('Delete single file'), yielding=True)    # main_menu.nml:364
        _w62.tooltip = _bind(    # main_menu.nml:365
            lambda _o: _tr('Delete the file at the cursor, not the selection'),
            yielding=True,
        )
        _w62.command = DeleteSingle    # main_menu.nml:366
        _w62.key = 'Shift-Del'    # main_menu.nml:367

        _w64.text = _bind(    # main_menu.nml:370
            lambda _o: _tr('Execute ~O~S command'),
            yielding=True,
        )
        _w64.tooltip = _bind(    # main_menu.nml:371
            lambda _o: _tr('Type a command in a box and run it'),
            yielding=True,
        )
        _w64.command = ExecuteOsCommand    # main_menu.nml:372

        _w65.text = _bind(lambda _o: _tr('E~x~it'), yielding=True)    # main_menu.nml:374
        _w65.command = Quit    # main_menu.nml:375
        _w65.key = 'Alt-X'    # main_menu.nml:376

        self.disk.text = _bind(lambda _o: _tr('~D~isk'), yielding=True)    # main_menu.nml:379
        self.disk.tooltip = _bind(    # main_menu.nml:380
            lambda _o: _tr('The directory tree, volumes and the Trash'),
            yielding=True,
        )

        _w66.text = _bind(lambda _o: _tr('~D~irectory tree'), yielding=True)    # main_menu.nml:382
        _w66.command = OpenTreeWindow    # main_menu.nml:383

        _w67.text = _bind(lambda _o: _tr('~V~olumes'), yielding=True)    # main_menu.nml:385
        _w67.tooltip = _bind(    # main_menu.nml:386
            lambda _o: _tr('Disks and partitions: mount, unmount and eject them'),
            yielding=True,
        )
        _w67.command = OpenVolumesWindow    # main_menu.nml:387

        _w68.text = _bind(lambda _o: _tr('Directory ~s~izes'), yielding=True)    # main_menu.nml:390
        _w68.tooltip = _bind(    # main_menu.nml:391
            lambda _o: _tr("What takes the room under the panel's directory, biggest first"),
            yielding=True,
        )
        _w68.command = OpenUsageWindow    # main_menu.nml:392

        _w70.text = _bind(lambda _o: _tr('~T~rash'), yielding=True)    # main_menu.nml:397
        _w70.command = OpenTrash    # main_menu.nml:398

        _w71.text = _bind(lambda _o: _tr('~E~mpty Trash'), yielding=True)    # main_menu.nml:400
        _w71.command = EmptyTrash    # main_menu.nml:401

        self.utilities.text = _bind(    # main_menu.nml:404
            lambda _o: _tr('~U~tilities'),
            yielding=True,
        )
        self.utilities.tooltip = _bind(    # main_menu.nml:405
            lambda _o: _tr('Calculator, calendar, remote links, the user menu and histories'),
            yielding=True,
        )

        _w72.text = _bind(    # main_menu.nml:407
            lambda _o: _tr('S~y~stem Information'),
            yielding=True,
        )
        _w72.command = SystemInfo    # main_menu.nml:408

        _w73.text = _bind(lambda _o: _tr('~P~rocess list'), yielding=True)    # main_menu.nml:413
        _w73.tooltip = _bind(    # main_menu.nml:414
            lambda _o: _tr('The running processes: sort them, see one, send it a signal'),
            yielding=True,
        )
        _w73.command = OpenProcessWindow    # main_menu.nml:415

        _w74.text = _bind(lambda _o: _tr('System mo~n~itor'), yielding=True)    # main_menu.nml:420
        _w74.tooltip = _bind(    # main_menu.nml:421
            lambda _o: _tr("Each processor's load, the memory and the temperature sensors, read live"),
            yielding=True,
        )
        _w74.command = OpenMonitorWindow    # main_menu.nml:422

        _w76.text = _bind(lambda _o: _tr('~C~alculator'), yielding=True)    # main_menu.nml:425
        _w76.command = Calculator    # main_menu.nml:426
        _w76.key = 'Ctrl-F6'    # main_menu.nml:427

        _w77.text = _bind(lambda _o: _tr('Ca~l~endar'), yielding=True)    # main_menu.nml:431
        _w77.command = OpenCalendar    # main_menu.nml:432

        _w78.text = _bind(lambda _o: _tr('Character ta~b~le'), yielding=True)    # main_menu.nml:434
        _w78.tooltip = _bind(    # main_menu.nml:435
            lambda _o: _tr('Pick a character to type where the cursor is'),
            yielding=True,
        )
        _w78.command = AsciiTable    # main_menu.nml:436
        _w78.key = 'Ctrl-B'    # main_menu.nml:437

        self.utilities_link.text = _bind(    # main_menu.nml:451
            lambda _o: _tr('Lin~k~'),
            yielding=True,
        )
        self.utilities_link.tooltip = _bind(    # main_menu.nml:452
            lambda _o: _tr('A server, a share, a container or a phone: its files in the active panel'),
            yielding=True,
        )

        _w80.text = _bind(lambda _o: _tr('~S~SH (SFTP)...'), yielding=True)    # main_menu.nml:454
        _w80.command = NavyLink    # main_menu.nml:455
        _w80.key = 'Alt-F11'    # main_menu.nml:456

        _w81.text = _bind(lambda _o: _tr('~F~TP...'), yielding=True)    # main_menu.nml:458
        _w81.command = FtpLink    # main_menu.nml:459

        _w82.text = _bind(    # main_menu.nml:461
            lambda _o: _tr('S~M~B (Windows share)...'),
            yielding=True,
        )
        _w82.command = SmbLink    # main_menu.nml:462

        _w83.text = _bind(lambda _o: _tr('S~3~ (Amazon S3)...'), yielding=True)    # main_menu.nml:464
        _w83.command = S3Link    # main_menu.nml:465

        _w84.text = _bind(    # main_menu.nml:468
            lambda _o: _tr('~G~Vfs/KIO (MTP, WebDAV...)...'),
            yielding=True,
        )
        _w84.tooltip = _bind(    # main_menu.nml:469
            lambda _o: _tr('A phone, a WebDAV share, Google Drive: anything the desktop can mount'),
            yielding=True,
        )
        _w84.command = GvfsLink    # main_menu.nml:470

        _w86.text = _bind(    # main_menu.nml:474
            lambda _o: _tr('~D~ocker container...'),
            yielding=True,
        )
        _w86.tooltip = _bind(    # main_menu.nml:475
            lambda _o: _tr("A running container's files, through docker exec"),
            yielding=True,
        )
        _w86.command = DockerLink    # main_menu.nml:476

        _w87.text = _bind(    # main_menu.nml:478
            lambda _o: _tr('~P~odman container...'),
            yielding=True,
        )
        _w87.tooltip = _bind(    # main_menu.nml:479
            lambda _o: _tr("A running container's files, through podman exec"),
            yielding=True,
        )
        _w87.command = PodmanLink    # main_menu.nml:480

        _w88.text = _bind(    # main_menu.nml:482
            lambda _o: _tr('~A~ndroid device (adb)...'),
            yielding=True,
        )
        _w88.tooltip = _bind(    # main_menu.nml:483
            lambda _o: _tr("A phone's or a tablet's files, over USB debugging"),
            yielding=True,
        )
        _w88.command = AdbLink    # main_menu.nml:484

        self.utilities_shell.text = _bind(    # main_menu.nml:488
            lambda _o: _tr('Rem~o~te shell'),
            yielding=True,
        )
        self.utilities_shell.tooltip = _bind(    # main_menu.nml:489
            lambda _o: _tr('A shell on a server, in a container or on a phone, in a window'),
            yielding=True,
        )

        _w89.text = _bind(lambda _o: _tr('~S~SH...'), yielding=True)    # main_menu.nml:491
        _w89.tooltip = _bind(    # main_menu.nml:492
            lambda _o: _tr('A login shell on a server, ssh -t'),
            yielding=True,
        )
        _w89.command = Terminal    # main_menu.nml:493

        _w90.text = _bind(    # main_menu.nml:495
            lambda _o: _tr('~D~ocker container...'),
            yielding=True,
        )
        _w90.tooltip = _bind(    # main_menu.nml:496
            lambda _o: _tr('A shell in a running container, docker exec -it'),
            yielding=True,
        )
        _w90.command = DockerShell    # main_menu.nml:497

        _w91.text = _bind(    # main_menu.nml:499
            lambda _o: _tr('~P~odman container...'),
            yielding=True,
        )
        _w91.tooltip = _bind(    # main_menu.nml:500
            lambda _o: _tr('A shell in a running container, podman exec -it'),
            yielding=True,
        )
        _w91.command = PodmanShell    # main_menu.nml:501

        _w92.text = _bind(    # main_menu.nml:503
            lambda _o: _tr('~A~ndroid device (adb)...'),
            yielding=True,
        )
        _w92.tooltip = _bind(    # main_menu.nml:504
            lambda _o: _tr('A shell on a phone or a tablet, adb shell'),
            yielding=True,
        )
        _w92.command = AdbShell    # main_menu.nml:505

        _w93.text = _bind(lambda _o: _tr('~D~isconnect'), yielding=True)    # main_menu.nml:507
        _w93.tooltip = _bind(    # main_menu.nml:508
            lambda _o: _tr('Close a connection; its panels go back to the disk'),
            yielding=True,
        )
        _w93.command = HangUp    # main_menu.nml:509
        _w93.key = 'Alt-H'    # main_menu.nml:510

        _w94.text = _bind(lambda _o: _tr('Close ~r~oot access'), yielding=True)    # main_menu.nml:512
        _w94.tooltip = _bind(    # main_menu.nml:513
            lambda _o: _tr('End root access now, rather than after its timeout'),
            yielding=True,
        )
        _w94.command = CloseRootAccess    # main_menu.nml:514

        _w95.text = _bind(lambda _o: _tr('Saved l~i~nks...'), yielding=True)    # main_menu.nml:516
        _w95.tooltip = _bind(    # main_menu.nml:517
            lambda _o: _tr('The saved connections: edit them, or connect to one'),
            yielding=True,
        )
        _w95.command = EditLinks    # main_menu.nml:518

        _w97.text = _bind(lambda _o: _tr('Edi~t~ environment'), yielding=True)    # main_menu.nml:521
        _w97.tooltip = _bind(    # main_menu.nml:522
            lambda _o: _tr('Edit the environment variables commands run with'),
            yielding=True,
        )
        _w97.command = EnvEdit    # main_menu.nml:523

        _w98.text = _bind(lambda _o: _tr('~U~ser menu'), yielding=True)    # main_menu.nml:525
        _w98.command = UserMenu    # main_menu.nml:526
        _w98.key = 'F2'    # main_menu.nml:527

        _w99.text = _bind(lambda _o: _tr('Commands ~H~istory'), yielding=True)    # main_menu.nml:529
        _w99.command = HistoryList    # main_menu.nml:530
        _w99.key = 'Alt-F8'    # main_menu.nml:531

        _w100.text = _bind(    # main_menu.nml:534
            lambda _o: _tr('Fu~z~zy history search...'),
            yielding=True,
        )
        _w100.tooltip = _bind(    # main_menu.nml:535
            lambda _o: _tr('The commands typed, here and in the shell, searched by fzf'),
            yielding=True,
        )
        _w100.command = FuzzyHistory    # main_menu.nml:536
        _w100.key = 'Alt-Shift-F8'    # main_menu.nml:537

        _w101.text = _bind(    # main_menu.nml:539
            lambda _o: _tr('File ~E~dit History'),
            yielding=True,
        )
        _w101.command = EditHistory    # main_menu.nml:540
        _w101.key = 'Alt-PgUp'    # main_menu.nml:541

        _w102.text = _bind(    # main_menu.nml:543
            lambda _o: _tr('File ~V~iew History'),
            yielding=True,
        )
        _w102.command = ViewHistory    # main_menu.nml:544
        _w102.key = 'Alt-PgDn'    # main_menu.nml:545

        self.manager.text = _bind(lambda _o: _tr('~M~anager'), yielding=True)    # main_menu.nml:548
        self.manager.tooltip = _bind(    # main_menu.nml:549
            lambda _o: _tr('New file managers, swapping and hiding panels, bookmarks'),
            yielding=True,
        )

        _w103.text = _bind(lambda _o: _tr('~N~ew'), yielding=True)    # main_menu.nml:551
        _w103.command = NewManager    # main_menu.nml:552
        _w103.key = 'Ctrl-F3'    # main_menu.nml:553

        _w104.text = _bind(lambda _o: _tr('~S~wap panels'), yielding=True)    # main_menu.nml:555
        _w104.command = SwapPanels    # main_menu.nml:556
        _w104.key = 'Ctrl-U'    # main_menu.nml:557

        _w105.text = _bind(    # main_menu.nml:559
            lambda _o: _tr('Show/hide ~l~eft panel'),
            yielding=True,
        )
        _w105.command = HideLeft    # main_menu.nml:560
        _w105.key = 'Ctrl-F1'    # main_menu.nml:561

        _w106.text = _bind(    # main_menu.nml:563
            lambda _o: _tr('Show/hide ~r~ight panel'),
            yielding=True,
        )
        _w106.command = HideRight    # main_menu.nml:564
        _w106.key = 'Ctrl-F2'    # main_menu.nml:565

        _w107.text = _bind(    # main_menu.nml:567
            lambda _o: _tr('Show/hide inactive ~p~anel'),
            yielding=True,
        )
        _w107.tooltip = _bind(    # main_menu.nml:568
            lambda _o: _tr('Hide the panel without the keyboard, or show it again'),
            yielding=True,
        )
        _w107.command = HideInactive    # main_menu.nml:569
        _w107.key = 'Ctrl-P'    # main_menu.nml:570

        _w108.text = _bind(lambda _o: _tr('~M~iller columns'), yielding=True)    # main_menu.nml:574
        _w108.tooltip = _bind(    # main_menu.nml:575
            lambda _o: _tr('Browse in columns, each directory beside its parent'),
            yielding=True,
        )
        _w108.command = ToggleMiller    # main_menu.nml:576
        _w108.key = 'Alt-F12'    # main_menu.nml:577

        _w110.text = _bind(lambda _o: _tr('Bookmarks le~f~t'), yielding=True)    # main_menu.nml:580
        _w110.tooltip = _bind(    # main_menu.nml:581
            lambda _o: _tr('Send the left panel to a bookmarked directory'),
            yielding=True,
        )
        _w110.command = ChangeLeft    # main_menu.nml:582
        _w110.key = 'Alt-F1'    # main_menu.nml:583

        _w111.text = _bind(lambda _o: _tr('Bookmarks rig~h~t'), yielding=True)    # main_menu.nml:585
        _w111.tooltip = _bind(    # main_menu.nml:586
            lambda _o: _tr('Send the right panel to a bookmarked directory'),
            yielding=True,
        )
        _w111.command = ChangeRight    # main_menu.nml:587
        _w111.key = 'Alt-F2'    # main_menu.nml:588

        self.options.text = _bind(lambda _o: _tr('~O~ptions'), yielding=True)    # main_menu.nml:591
        self.options.tooltip = _bind(    # main_menu.nml:592
            lambda _o: _tr('Settings, configuration files, the desktop and colours'),
            yielding=True,
        )

        _w112.text = _bind(lambda _o: _tr('Sett~i~ngs...'), yielding=True)    # main_menu.nml:596
        _w112.tooltip = _bind(    # main_menu.nml:597
            lambda _o: _tr('Every setup page in one box, behind tabs'),
            yielding=True,
        )
        _w112.command = Settings    # main_menu.nml:598

        self.options_configuration.text = _bind(    # main_menu.nml:602
            lambda _o: _tr('~C~onfiguration'),
            yielding=True,
        )

        _w114.text = _bind(lambda _o: _tr('S~y~stem Setup...'), yielding=True)    # main_menu.nml:604
        _w114.command = SystemSetup    # main_menu.nml:605

        _w115.text = _bind(lambda _o: _tr('~S~tartup...'), yielding=True)    # main_menu.nml:607
        _w115.command = StartupSetup    # main_menu.nml:608

        _w116.text = _bind(lambda _o: _tr('~I~nterface...'), yielding=True)    # main_menu.nml:610
        _w116.command = InterfaceSetup    # main_menu.nml:611

        _w117.text = _bind(lambda _o: _tr('~C~onfirmations...'), yielding=True)    # main_menu.nml:613
        _w117.command = SetupConfirmation    # main_menu.nml:614

        _w119.text = _bind(lambda _o: _tr('Screen sa~v~ers...'), yielding=True)    # main_menu.nml:617
        _w119.command = SaversSetup    # main_menu.nml:618

        _w120.text = _bind(    # main_menu.nml:620
            lambda _o: _tr('C~o~untry support...'),
            yielding=True,
        )
        _w120.command = CountrySetup    # main_menu.nml:621

        _w121.text = _bind(    # main_menu.nml:623
            lambda _o: _tr('Comm~u~nications...'),
            yielding=True,
        )
        _w121.tooltip = _bind(    # main_menu.nml:624
            lambda _o: _tr('Settings for remote connections'),
            yielding=True,
        )
        _w121.command = SetupLink    # main_menu.nml:625

        _w123.text = _bind(lambda _o: _tr('~E~ditor/Viewer...'), yielding=True)    # main_menu.nml:628
        _w123.command = EditorDefaults    # main_menu.nml:629

        _w125.text = _bind(lambda _o: _tr('~K~ey bindings...'), yielding=True)    # main_menu.nml:632
        _w125.command = KeyBindingsSetup    # main_menu.nml:633

        self.options_file_manager.text = _bind(    # main_menu.nml:636
            lambda _o: _tr('~F~ile Manager'),
            yielding=True,
        )

        _w126.text = _bind(lambda _o: _tr('~S~etup...'), yielding=True)    # main_menu.nml:638
        _w126.command = FileManagerSetup    # main_menu.nml:639

        _w127.text = _bind(    # main_menu.nml:641
            lambda _o: _tr('~I~nformation panel...'),
            yielding=True,
        )
        _w127.tooltip = _bind(    # main_menu.nml:642
            lambda _o: _tr('What the information panel (Ctrl+L) shows'),
            yielding=True,
        )
        _w127.command = DriveInfoSetup    # main_menu.nml:643

        _w128.text = _bind(    # main_menu.nml:645
            lambda _o: _tr('New Manager ~d~efaults...'),
            yielding=True,
        )
        _w128.tooltip = _bind(    # main_menu.nml:646
            lambda _o: _tr("How a new file manager's panels start"),
            yielding=True,
        )
        _w128.command = FileManagerDefaults    # main_menu.nml:647

        _w129.text = _bind(    # main_menu.nml:649
            lambda _o: _tr('~C~olumn defaults...'),
            yielding=True,
        )
        _w129.tooltip = _bind(    # main_menu.nml:650
            lambda _o: _tr('The columns a new panel shows'),
            yielding=True,
        )
        _w129.command = ColumnDefaults    # main_menu.nml:651

        _w130.text = _bind(    # main_menu.nml:653
            lambda _o: _tr('~H~ighlight groups...'),
            yielding=True,
        )
        _w130.tooltip = _bind(    # main_menu.nml:654
            lambda _o: _tr('Which files the panels show in which colour'),
            yielding=True,
        )
        _w130.command = HighlightGroups    # main_menu.nml:655

        self.options_archives.text = _bind(    # main_menu.nml:658
            lambda _o: _tr('A~r~chives'),
            yielding=True,
        )

        _w131.text = _bind(    # main_menu.nml:660
            lambda _o: _tr('Current archiver...'),
            yielding=True,
        )
        _w131.key = 'Alt-N'    # main_menu.nml:661

        _w133.text = _bind(    # main_menu.nml:664
            lambda _o: _tr('~Q~uick run file edit...'),
            yielding=True,
        )
        _w133.tooltip = _bind(    # main_menu.nml:665
            lambda _o: _tr('Edit quickrun.ini: the commands Ctrl+Shift+F1 to F10 run'),
            yielding=True,
        )
        _w133.command = EditQuickRun    # main_menu.nml:666

        _w134.text = _bind(    # main_menu.nml:668
            lambda _o: _tr('E~x~tension file edit...'),
            yielding=True,
        )
        _w134.tooltip = _bind(    # main_menu.nml:669
            lambda _o: _tr('Edit extensions.ini: what Enter runs for each kind of file'),
            yielding=True,
        )
        _w134.command = ExtFileEdit    # main_menu.nml:670

        _w135.text = _bind(    # main_menu.nml:672
            lambda _o: _tr('~H~ighlight file edit...'),
            yielding=True,
        )
        _w135.tooltip = _bind(    # main_menu.nml:673
            lambda _o: _tr('Edit highlight.ini: which syntax colours which file'),
            yielding=True,
        )
        _w135.command = EditHGL    # main_menu.nml:674

        _w136.text = _bind(    # main_menu.nml:676
            lambda _o: _tr('Macro file e~d~it...'),
            yielding=True,
        )
        _w136.tooltip = _bind(    # main_menu.nml:677
            lambda _o: _tr("Edit macros.ini: the editor's macros, offered by Ctrl+J 0"),
            yielding=True,
        )
        _w136.command = EditMacros    # main_menu.nml:678

        _w137.text = _bind(    # main_menu.nml:680
            lambda _o: _tr('~G~lobal menu definition...'),
            yielding=True,
        )
        _w137.tooltip = _bind(    # main_menu.nml:681
            lambda _o: _tr('Edit the F2 user menu used everywhere'),
            yielding=True,
        )
        _w137.command = MenuFileEdit    # main_menu.nml:682

        _w138.text = _bind(    # main_menu.nml:684
            lambda _o: _tr('Local ~m~enu definition...'),
            yielding=True,
        )
        _w138.tooltip = _bind(    # main_menu.nml:685
            lambda _o: _tr("Edit this directory's own F2 user menu"),
            yielding=True,
        )
        _w138.command = LocalMenuFileEdit    # main_menu.nml:686

        _w139.text = _bind(lambda _o: _tr('~V~iewers...'), yielding=True)    # main_menu.nml:688
        _w139.tooltip = _bind(    # main_menu.nml:689
            lambda _o: _tr('Edit viewers.ini: the external viewer for each kind of file'),
            yielding=True,
        )
        _w139.command = ExternalViewers    # main_menu.nml:690

        _w140.text = _bind(lambda _o: _tr('~E~ditors...'), yielding=True)    # main_menu.nml:692
        _w140.tooltip = _bind(    # main_menu.nml:693
            lambda _o: _tr('Edit editors.ini: the external editor for each kind of file'),
            yielding=True,
        )
        _w140.command = ExternalEditors    # main_menu.nml:694

        _w142.text = _bind(lambda _o: _tr('~S~ave desktop'), yielding=True)    # main_menu.nml:697
        _w142.tooltip = _bind(    # main_menu.nml:698
            lambda _o: _tr('Keep the open windows, to have them back later'),
            yielding=True,
        )
        _w142.command = SaveDesktop    # main_menu.nml:699

        _w143.text = _bind(lambda _o: _tr('~L~oad desktop'), yielding=True)    # main_menu.nml:701
        _w143.tooltip = _bind(    # main_menu.nml:702
            lambda _o: _tr('Replace these windows with the ones last saved'),
            yielding=True,
        )
        _w143.command = LoadDesktop    # main_menu.nml:703

        _w145.text = _bind(lambda _o: _tr('C~o~lors...'), yielding=True)    # main_menu.nml:706
        _w145.command = ChangeColors    # main_menu.nml:707

        _w146.text = _bind(lambda _o: _tr('S~t~ore palette'), yielding=True)    # main_menu.nml:709
        _w146.tooltip = _bind(    # main_menu.nml:710
            lambda _o: _tr('Save the colours as a theme of your own'),
            yielding=True,
        )
        _w146.command = StoreColors    # main_menu.nml:711

        _w147.text = _bind(lambda _o: _tr('Lo~a~d palette'), yielding=True)    # main_menu.nml:713
        _w147.tooltip = _bind(    # main_menu.nml:714
            lambda _o: _tr('Use colours saved in a file'),
            yielding=True,
        )
        _w147.command = LoadColors    # main_menu.nml:715

        self.window.text = _bind(lambda _o: _tr('~W~indow'), yielding=True)    # main_menu.nml:718
        self.window.tooltip = _bind(    # main_menu.nml:719
            lambda _o: _tr('Arrange, switch between and close windows'),
            yielding=True,
        )

        _w148.text = _bind(lambda _o: _tr('~T~ile'), yielding=True)    # main_menu.nml:721
        _w148.command = TileWindows    # main_menu.nml:722

        _w149.text = _bind(lambda _o: _tr('C~a~scade'), yielding=True)    # main_menu.nml:724
        _w149.command = CascadeWindows    # main_menu.nml:725

        _w150.text = _bind(lambda _o: _tr('Cl~o~se all'), yielding=True)    # main_menu.nml:727
        _w150.command = CloseAllWindows    # main_menu.nml:728

        _w152.text = _bind(lambda _o: _tr('~S~ize/Move'), yielding=True)    # main_menu.nml:731
        _w152.tooltip = _bind(    # main_menu.nml:732
            lambda _o: _tr('Move and size the window with the keyboard'),
            yielding=True,
        )
        _w152.command = SizeMoveWindow    # main_menu.nml:733
        _w152.key = 'Ctrl-F5'    # main_menu.nml:734

        _w153.text = _bind(lambda _o: _tr('~Z~oom'), yielding=True)    # main_menu.nml:736
        _w153.command = ZoomWindow    # main_menu.nml:737
        _w153.key = 'Alt-Z'    # main_menu.nml:738

        _w154.text = _bind(lambda _o: _tr('~N~ext'), yielding=True)    # main_menu.nml:740
        _w154.command = NextWindow    # main_menu.nml:741
        _w154.key = 'F9'    # main_menu.nml:742

        _w155.text = _bind(lambda _o: _tr('~P~revious'), yielding=True)    # main_menu.nml:744
        _w155.command = PreviousWindow    # main_menu.nml:745
        _w155.key = 'Shift-F9'    # main_menu.nml:746

        _w156.text = _bind(lambda _o: _tr('~C~lose'), yielding=True)    # main_menu.nml:748
        _w156.command = CloseWindow    # main_menu.nml:749
        _w156.key = 'Ctrl-F4'    # main_menu.nml:750

        _w158.text = _bind(lambda _o: _tr('~L~ist...'), yielding=True)    # main_menu.nml:753
        _w158.tooltip = _bind(    # main_menu.nml:754
            lambda _o: _tr('All the windows, to switch to one or close it'),
            yielding=True,
        )
        _w158.command = WindowManager    # main_menu.nml:755
        _w158.key = 'Alt-0'    # main_menu.nml:756

        _w159.text = _bind(    # main_menu.nml:759
            lambda _o: _tr('~B~ackground operation...'),
            yielding=True,
        )
        _w159.tooltip = _bind(    # main_menu.nml:760
            lambda _o: _tr('Bring back the progress box of a copy or an erase running in the background'),
            yielding=True,
        )
        _w159.command = ShowBackground    # main_menu.nml:761
