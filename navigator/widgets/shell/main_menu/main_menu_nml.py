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
from navigator.widgets.manager.commands import RestoreTrash, AlternateEdit, AlternateView, ArchiveFiles, Calculator, ChangeAttributes, ChangeLeft, ChangeRight, Copy, Delete, DeleteSingle, DiffFiles, Edit, EditNamed, ExtractArchive, ExtractTo, ArcTest, OpenArchive, MultiRename, Undo, FindFile, ReplaceInFiles, OpenWith, HideInactive, HideLeft, HideRight, MakeDirectory, MakeLink, EditLinkTarget, LinkAbsolute, LinkRelative, SelectBrokenLinks, ShowHardLinks, QuickRename, RenameMove, SwapPanels, ToggleMiller, UserMenu, UuDecode, UuEncode, SplitCombine, CalculateChecksums, VerifyChecksums, EncryptFiles, DecryptFiles, View, ViewAsDataBase, ViewAsHex, ViewAsSpreadsheet, ViewAsText, MountImage, UnmountImage    # main_menu.nml:2
from navigator.widgets.shell.commands import OpenEdit, OpenView, About, OpenCommandPalette, CloseRootAccess, ShowBackground, EditLinks, FtpLink, GvfsLink, S3Link, DockerLink, PodmanLink, AdbLink, DockerShell, PodmanShell, AdbShell, Game, HangUp, NavyLink, Terminal, SetupLink, SmbLink, SaversSetup, CountrySetup, ScreenRest, ToggleTrashCan, OpenTrash, EmptyTrash, ChangeColors, ColumnDefaults, HighlightGroups, EditQuickRun, ExtFileEdit, EditHGL, EditMacros, ExternalViewers, ExternalEditors, LoadColors, StoreColors, LoadDesktop, SaveDesktop, DriveInfoSetup, EditHistory, EnvEdit, ExecuteOsCommand, HistoryList, FuzzyHistory, OpenCalendar, SystemInfo, EditorDefaults, FileManagerDefaults, FileManagerSetup, InterfaceSetup, KeyBindingsSetup, LocalMenuFileEdit, MenuFileEdit, NewManager, OpenTreeWindow, OpenUsageWindow, OpenVolumesWindow, OpenProcessWindow, OpenServiceWindow, OpenMonitorWindow, SetupConfirmation, Settings, StartupSetup, SystemSetup, ViewHistory    # main_menu.nml:3
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
    file_symlinks: SubMenu    # main_menu.nml:260
    file_restore_trash: MenuItem    # main_menu.nml:319
    file_encoding: SubMenu    # main_menu.nml:332
    file_checksums: SubMenu    # main_menu.nml:349
    file_encryption: SubMenu    # main_menu.nml:362
    disk: SubMenu    # main_menu.nml:387
    utilities: SubMenu    # main_menu.nml:423
    utilities_link: SubMenu    # main_menu.nml:477
    utilities_shell: SubMenu    # main_menu.nml:514
    manager: SubMenu    # main_menu.nml:574
    options: SubMenu    # main_menu.nml:617
    options_configuration: SubMenu    # main_menu.nml:628
    options_file_manager: SubMenu    # main_menu.nml:662
    options_archives: SubMenu    # main_menu.nml:684
    window: SubMenu    # main_menu.nml:744

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
        _w35 = MenuItem(parent=self.file_archive)    # main_menu.nml:229
        _w36 = MenuLine(parent=self.file_archive)    # main_menu.nml:234
        _w37 = MenuItem(parent=self.file_archive)    # main_menu.nml:237
        _w38 = MenuItem(parent=self.file_archive)    # main_menu.nml:241
        _w39 = MenuLine(parent=self.file_archive)    # main_menu.nml:245
        _w40 = MenuItem(parent=self.file_archive)    # main_menu.nml:248
        _w41 = MenuItem(parent=self.file_archive)    # main_menu.nml:252
        self.file_symlinks = SubMenu(parent=self.file)    # main_menu.nml:259
        _w42 = MenuItem(parent=self.file_symlinks)    # main_menu.nml:262
        _w43 = MenuLine(parent=self.file_symlinks)    # main_menu.nml:267
        _w44 = MenuItem(parent=self.file_symlinks)    # main_menu.nml:268
        _w45 = MenuItem(parent=self.file_symlinks)    # main_menu.nml:272
        _w46 = MenuItem(parent=self.file_symlinks)    # main_menu.nml:276
        _w47 = MenuLine(parent=self.file_symlinks)    # main_menu.nml:280
        _w48 = MenuItem(parent=self.file_symlinks)    # main_menu.nml:281
        _w49 = MenuLine(parent=self.file_symlinks)    # main_menu.nml:285
        _w50 = MenuItem(parent=self.file_symlinks)    # main_menu.nml:286
        _w51 = MenuItem(parent=self.file)    # main_menu.nml:293
        _w52 = MenuItem(parent=self.file)    # main_menu.nml:299
        _w53 = MenuItem(parent=self.file)    # main_menu.nml:302
        _w54 = MenuItem(parent=self.file)    # main_menu.nml:306
        _w55 = MenuItem(parent=self.file)    # main_menu.nml:310
        self.file_restore_trash = MenuItem(parent=self.file)    # main_menu.nml:318
        _w56 = MenuItem(parent=self.file)    # main_menu.nml:324
        self.file_encoding = SubMenu(parent=self.file)    # main_menu.nml:331
        _w57 = MenuItem(parent=self.file_encoding)    # main_menu.nml:335
        _w58 = MenuItem(parent=self.file_encoding)    # main_menu.nml:340
        _w59 = MenuLine(parent=self.file_encoding)    # main_menu.nml:345
        self.file_checksums = SubMenu(parent=self.file_encoding)    # main_menu.nml:348
        _w60 = MenuItem(parent=self.file_checksums)    # main_menu.nml:351
        _w61 = MenuItem(parent=self.file_checksums)    # main_menu.nml:355
        self.file_encryption = SubMenu(parent=self.file_encoding)    # main_menu.nml:361
        _w62 = MenuItem(parent=self.file_encryption)    # main_menu.nml:364
        _w63 = MenuItem(parent=self.file_encryption)    # main_menu.nml:368
        _w64 = MenuItem(parent=self.file)    # main_menu.nml:372
        _w65 = MenuLine(parent=self.file)    # main_menu.nml:377
        _w66 = MenuItem(parent=self.file)    # main_menu.nml:378
        _w67 = MenuItem(parent=self.file)    # main_menu.nml:382
        self.disk = SubMenu(parent=self)    # main_menu.nml:386
        _w68 = MenuItem(parent=self.disk)    # main_menu.nml:390
        _w69 = MenuItem(parent=self.disk)    # main_menu.nml:393
        _w70 = MenuItem(parent=self.disk)    # main_menu.nml:400
        _w71 = MenuItem(parent=self.disk)    # main_menu.nml:404
        _w72 = MenuItem(parent=self.disk)    # main_menu.nml:409
        _w73 = MenuLine(parent=self.disk)    # main_menu.nml:415
        _w74 = MenuItem(parent=self.disk)    # main_menu.nml:416
        _w75 = MenuItem(parent=self.disk)    # main_menu.nml:419
        self.utilities = SubMenu(parent=self)    # main_menu.nml:422
        _w76 = MenuItem(parent=self.utilities)    # main_menu.nml:426
        _w77 = MenuItem(parent=self.utilities)    # main_menu.nml:432
        _w78 = MenuItem(parent=self.utilities)    # main_menu.nml:439
        _w79 = MenuItem(parent=self.utilities)    # main_menu.nml:446
        _w80 = MenuLine(parent=self.utilities)    # main_menu.nml:450
        _w81 = MenuItem(parent=self.utilities)    # main_menu.nml:451
        _w82 = MenuItem(parent=self.utilities)    # main_menu.nml:457
        _w83 = MenuItem(parent=self.utilities)    # main_menu.nml:460
        _w84 = MenuLine(parent=self.utilities)    # main_menu.nml:465
        self.utilities_link = SubMenu(parent=self.utilities)    # main_menu.nml:476
        _w85 = MenuItem(parent=self.utilities_link)    # main_menu.nml:480
        _w86 = MenuItem(parent=self.utilities_link)    # main_menu.nml:484
        _w87 = MenuItem(parent=self.utilities_link)    # main_menu.nml:487
        _w88 = MenuItem(parent=self.utilities_link)    # main_menu.nml:490
        _w89 = MenuItem(parent=self.utilities_link)    # main_menu.nml:494
        _w90 = MenuLine(parent=self.utilities_link)    # main_menu.nml:498
        _w91 = MenuItem(parent=self.utilities_link)    # main_menu.nml:500
        _w92 = MenuItem(parent=self.utilities_link)    # main_menu.nml:504
        _w93 = MenuItem(parent=self.utilities_link)    # main_menu.nml:508
        self.utilities_shell = SubMenu(parent=self.utilities)    # main_menu.nml:513
        _w94 = MenuItem(parent=self.utilities_shell)    # main_menu.nml:517
        _w95 = MenuItem(parent=self.utilities_shell)    # main_menu.nml:521
        _w96 = MenuItem(parent=self.utilities_shell)    # main_menu.nml:525
        _w97 = MenuItem(parent=self.utilities_shell)    # main_menu.nml:529
        _w98 = MenuItem(parent=self.utilities)    # main_menu.nml:533
        _w99 = MenuItem(parent=self.utilities)    # main_menu.nml:538
        _w100 = MenuItem(parent=self.utilities)    # main_menu.nml:542
        _w101 = MenuLine(parent=self.utilities)    # main_menu.nml:546
        _w102 = MenuItem(parent=self.utilities)    # main_menu.nml:547
        _w103 = MenuItem(parent=self.utilities)    # main_menu.nml:551
        _w104 = MenuItem(parent=self.utilities)    # main_menu.nml:555
        _w105 = MenuItem(parent=self.utilities)    # main_menu.nml:560
        _w106 = MenuItem(parent=self.utilities)    # main_menu.nml:565
        _w107 = MenuItem(parent=self.utilities)    # main_menu.nml:569
        self.manager = SubMenu(parent=self)    # main_menu.nml:573
        _w108 = MenuItem(parent=self.manager)    # main_menu.nml:577
        _w109 = MenuItem(parent=self.manager)    # main_menu.nml:581
        _w110 = MenuItem(parent=self.manager)    # main_menu.nml:585
        _w111 = MenuItem(parent=self.manager)    # main_menu.nml:589
        _w112 = MenuItem(parent=self.manager)    # main_menu.nml:593
        _w113 = MenuItem(parent=self.manager)    # main_menu.nml:600
        _w114 = MenuLine(parent=self.manager)    # main_menu.nml:605
        _w115 = MenuItem(parent=self.manager)    # main_menu.nml:606
        _w116 = MenuItem(parent=self.manager)    # main_menu.nml:611
        self.options = SubMenu(parent=self)    # main_menu.nml:616
        _w117 = MenuItem(parent=self.options)    # main_menu.nml:622
        _w118 = MenuLine(parent=self.options)    # main_menu.nml:626
        self.options_configuration = SubMenu(parent=self.options)    # main_menu.nml:627
        _w119 = MenuItem(parent=self.options_configuration)    # main_menu.nml:630
        _w120 = MenuItem(parent=self.options_configuration)    # main_menu.nml:633
        _w121 = MenuItem(parent=self.options_configuration)    # main_menu.nml:636
        _w122 = MenuItem(parent=self.options_configuration)    # main_menu.nml:639
        _w123 = MenuLine(parent=self.options_configuration)    # main_menu.nml:642
        _w124 = MenuItem(parent=self.options_configuration)    # main_menu.nml:643
        _w125 = MenuItem(parent=self.options_configuration)    # main_menu.nml:646
        _w126 = MenuItem(parent=self.options_configuration)    # main_menu.nml:649
        _w127 = MenuLine(parent=self.options_configuration)    # main_menu.nml:653
        _w128 = MenuItem(parent=self.options_configuration)    # main_menu.nml:654
        _w129 = MenuLine(parent=self.options_configuration)    # main_menu.nml:657
        _w130 = MenuItem(parent=self.options_configuration)    # main_menu.nml:658
        self.options_file_manager = SubMenu(parent=self.options)    # main_menu.nml:661
        _w131 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:664
        _w132 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:667
        _w133 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:671
        _w134 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:675
        _w135 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:679
        self.options_archives = SubMenu(parent=self.options)    # main_menu.nml:683
        _w136 = MenuItem(parent=self.options_archives)    # main_menu.nml:686
        _w137 = MenuLine(parent=self.options)    # main_menu.nml:689
        _w138 = MenuItem(parent=self.options)    # main_menu.nml:690
        _w139 = MenuItem(parent=self.options)    # main_menu.nml:694
        _w140 = MenuItem(parent=self.options)    # main_menu.nml:698
        _w141 = MenuItem(parent=self.options)    # main_menu.nml:702
        _w142 = MenuItem(parent=self.options)    # main_menu.nml:706
        _w143 = MenuItem(parent=self.options)    # main_menu.nml:710
        _w144 = MenuItem(parent=self.options)    # main_menu.nml:714
        _w145 = MenuItem(parent=self.options)    # main_menu.nml:718
        _w146 = MenuLine(parent=self.options)    # main_menu.nml:722
        _w147 = MenuItem(parent=self.options)    # main_menu.nml:723
        _w148 = MenuItem(parent=self.options)    # main_menu.nml:727
        _w149 = MenuLine(parent=self.options)    # main_menu.nml:731
        _w150 = MenuItem(parent=self.options)    # main_menu.nml:732
        _w151 = MenuItem(parent=self.options)    # main_menu.nml:735
        _w152 = MenuItem(parent=self.options)    # main_menu.nml:739
        self.window = SubMenu(parent=self)    # main_menu.nml:743
        _w153 = MenuItem(parent=self.window)    # main_menu.nml:747
        _w154 = MenuItem(parent=self.window)    # main_menu.nml:750
        _w155 = MenuItem(parent=self.window)    # main_menu.nml:753
        _w156 = MenuLine(parent=self.window)    # main_menu.nml:756
        _w157 = MenuItem(parent=self.window)    # main_menu.nml:757
        _w158 = MenuItem(parent=self.window)    # main_menu.nml:762
        _w159 = MenuItem(parent=self.window)    # main_menu.nml:766
        _w160 = MenuItem(parent=self.window)    # main_menu.nml:770
        _w161 = MenuItem(parent=self.window)    # main_menu.nml:774
        _w162 = MenuLine(parent=self.window)    # main_menu.nml:778
        _w163 = MenuItem(parent=self.window)    # main_menu.nml:779
        _w164 = MenuItem(parent=self.window)    # main_menu.nml:785

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
            lambda _o: _tr('Open, create, extract and test archives'),
            yielding=True,
        )

        _w35.text = _bind(lambda _o: _tr('~O~pen archive'), yielding=True)    # main_menu.nml:230
        _w35.tooltip = _bind(    # main_menu.nml:231
            lambda _o: _tr('Open the file at the cursor as an archive, whatever its name'),
            yielding=True,
        )
        _w35.command = OpenArchive    # main_menu.nml:232
        _w35.key = 'Ctrl-PgDn'    # main_menu.nml:233

        _w37.text = _bind(lambda _o: _tr('Create arch~i~ve...'), yielding=True)    # main_menu.nml:238
        _w37.command = ArchiveFiles    # main_menu.nml:239
        _w37.key = 'Shift-F1'    # main_menu.nml:240

        _w38.text = _bind(    # main_menu.nml:242
            lambda _o: _tr('Ex~t~ract archive...'),
            yielding=True,
        )
        _w38.command = ExtractArchive    # main_menu.nml:243
        _w38.key = 'Shift-F2'    # main_menu.nml:244

        _w40.text = _bind(lambda _o: _tr('E~x~tract to...'), yielding=True)    # main_menu.nml:249
        _w40.command = ExtractTo    # main_menu.nml:250
        _w40.key = 'Shift-F2'    # main_menu.nml:251

        _w41.text = _bind(lambda _o: _tr('Test archive'), yielding=True)    # main_menu.nml:253
        _w41.tooltip = _bind(    # main_menu.nml:254
            lambda _o: _tr('Read the archive through and check it for errors'),
            yielding=True,
        )
        _w41.command = ArcTest    # main_menu.nml:255

        self.file_symlinks.text = _bind(    # main_menu.nml:261
            lambda _o: _tr('Link~s~'),
            yielding=True,
        )

        _w42.text = _bind(lambda _o: _tr('Create ~l~ink...'), yielding=True)    # main_menu.nml:263
        _w42.tooltip = _bind(    # main_menu.nml:264
            lambda _o: _tr('Make a symbolic or hard link to each selected file'),
            yielding=True,
        )
        _w42.command = MakeLink    # main_menu.nml:265
        _w42.key = 'Shift-F5'    # main_menu.nml:266

        _w44.text = _bind(    # main_menu.nml:269
            lambda _o: _tr('~E~dit link target...'),
            yielding=True,
        )
        _w44.tooltip = _bind(    # main_menu.nml:270
            lambda _o: _tr('Change what the selected links point at'),
            yielding=True,
        )
        _w44.command = EditLinkTarget    # main_menu.nml:271

        _w45.text = _bind(lambda _o: _tr('Make ~r~elative'), yielding=True)    # main_menu.nml:273
        _w45.tooltip = _bind(    # main_menu.nml:274
            lambda _o: _tr("Rewrite each selected link's target relative to the link"),
            yielding=True,
        )
        _w45.command = LinkRelative    # main_menu.nml:275

        _w46.text = _bind(lambda _o: _tr('Make ~a~bsolute'), yielding=True)    # main_menu.nml:277
        _w46.tooltip = _bind(    # main_menu.nml:278
            lambda _o: _tr("Rewrite each selected link's target as a full path"),
            yielding=True,
        )
        _w46.command = LinkAbsolute    # main_menu.nml:279

        _w48.text = _bind(    # main_menu.nml:282
            lambda _o: _tr('Select ~b~roken links'),
            yielding=True,
        )
        _w48.tooltip = _bind(    # main_menu.nml:283
            lambda _o: _tr('Tag every link here that points nowhere'),
            yielding=True,
        )
        _w48.command = SelectBrokenLinks    # main_menu.nml:284

        _w50.text = _bind(lambda _o: _tr('Show ~h~ard links'), yielding=True)    # main_menu.nml:287
        _w50.tooltip = _bind(    # main_menu.nml:288
            lambda _o: _tr('List every name the file at the cursor has on its file system'),
            yielding=True,
        )
        _w50.command = ShowHardLinks    # main_menu.nml:289

        _w51.text = _bind(lambda _o: _tr('Split/com~b~ine...'), yielding=True)    # main_menu.nml:294
        _w51.tooltip = _bind(    # main_menu.nml:295
            lambda _o: _tr('Cut the file into parts of a given size, or put a split file back together'),
            yielding=True,
        )
        _w51.command = SplitCombine    # main_menu.nml:296

        _w52.text = _bind(lambda _o: _tr('Compare fi~l~es...'), yielding=True)    # main_menu.nml:300
        _w52.command = DiffFiles    # main_menu.nml:301

        _w53.text = _bind(lambda _o: _tr('~P~rint'), yielding=True)    # main_menu.nml:303
        _w53.command = PrintFile    # main_menu.nml:304
        _w53.key = 'Ctrl-F9'    # main_menu.nml:305

        _w54.text = _bind(lambda _o: _tr('~M~ake directory'), yielding=True)    # main_menu.nml:307
        _w54.command = MakeDirectory    # main_menu.nml:308
        _w54.key = 'F7'    # main_menu.nml:309

        _w55.text = _bind(lambda _o: _tr('~D~elete'), yielding=True)    # main_menu.nml:311
        _w55.command = Delete    # main_menu.nml:312
        _w55.key = 'F8'    # main_menu.nml:313

        self.file_restore_trash.text = _bind(    # main_menu.nml:320
            lambda _o: _tr('Restore from Tras~h~'),
            yielding=True,
        )
        self.file_restore_trash.tooltip = _bind(    # main_menu.nml:321
            lambda _o: _tr('Put the selected files back where they were deleted from'),
            yielding=True,
        )
        self.file_restore_trash.command = RestoreTrash    # main_menu.nml:322
        self.file_restore_trash.hidden = _bind(    # main_menu.nml:323
            lambda _o: not getattr(self.context, 'shows_trash', False)
        )

        _w56.text = _bind(    # main_menu.nml:325
            lambda _o: _tr('File ~A~ttributes...'),
            yielding=True,
        )
        _w56.tooltip = _bind(    # main_menu.nml:326
            lambda _o: _tr('Permissions, owner, group, dates, ACLs and extended attributes'),
            yielding=True,
        )
        _w56.command = ChangeAttributes    # main_menu.nml:327
        _w56.key = 'Alt-E'    # main_menu.nml:328

        self.file_encoding.text = _bind(    # main_menu.nml:333
            lambda _o: _tr('E~n~coding'),
            yielding=True,
        )
        self.file_encoding.tooltip = _bind(    # main_menu.nml:334
            lambda _o: _tr('UU encoding, checksums and encryption'),
            yielding=True,
        )

        _w57.text = _bind(lambda _o: _tr('UU E~n~code...'), yielding=True)    # main_menu.nml:336
        _w57.tooltip = _bind(    # main_menu.nml:337
            lambda _o: _tr('Encode the file as plain text, the old way of mailing files'),
            yielding=True,
        )
        _w57.command = UuEncode    # main_menu.nml:338
        _w57.key = 'Ctrl-F7'    # main_menu.nml:339

        _w58.text = _bind(lambda _o: _tr('~U~U Decode...'), yielding=True)    # main_menu.nml:341
        _w58.tooltip = _bind(    # main_menu.nml:342
            lambda _o: _tr('Decode the files UU-encoded in this file'),
            yielding=True,
        )
        _w58.command = UuDecode    # main_menu.nml:343
        _w58.key = 'Ctrl-F8'    # main_menu.nml:344

        self.file_checksums.text = _bind(    # main_menu.nml:350
            lambda _o: _tr('Chec~k~sums'),
            yielding=True,
        )

        _w60.text = _bind(lambda _o: _tr('~C~alculate...'), yielding=True)    # main_menu.nml:352
        _w60.tooltip = _bind(    # main_menu.nml:353
            lambda _o: _tr('Hash the tagged files and write their checksums to a list'),
            yielding=True,
        )
        _w60.command = CalculateChecksums    # main_menu.nml:354

        _w61.text = _bind(lambda _o: _tr('~V~erify'), yielding=True)    # main_menu.nml:356
        _w61.tooltip = _bind(    # main_menu.nml:357
            lambda _o: _tr('Hash the files a checksum list names again and check them'),
            yielding=True,
        )
        _w61.command = VerifyChecksums    # main_menu.nml:358

        self.file_encryption.text = _bind(    # main_menu.nml:363
            lambda _o: _tr('Encr~y~ption'),
            yielding=True,
        )

        _w62.text = _bind(lambda _o: _tr('~E~ncrypt...'), yielding=True)    # main_menu.nml:365
        _w62.tooltip = _bind(    # main_menu.nml:366
            lambda _o: _tr('Encrypt the tagged files with gpg or age, each beside itself'),
            yielding=True,
        )
        _w62.command = EncryptFiles    # main_menu.nml:367

        _w63.text = _bind(lambda _o: _tr('~D~ecrypt'), yielding=True)    # main_menu.nml:369
        _w63.tooltip = _bind(    # main_menu.nml:370
            lambda _o: _tr('Decrypt the tagged gpg or age files, each beside itself'),
            yielding=True,
        )
        _w63.command = DecryptFiles    # main_menu.nml:371

        _w64.text = _bind(lambda _o: _tr('Delete single file'), yielding=True)    # main_menu.nml:373
        _w64.tooltip = _bind(    # main_menu.nml:374
            lambda _o: _tr('Delete the file at the cursor, not the selection'),
            yielding=True,
        )
        _w64.command = DeleteSingle    # main_menu.nml:375
        _w64.key = 'Shift-Del'    # main_menu.nml:376

        _w66.text = _bind(    # main_menu.nml:379
            lambda _o: _tr('Execute ~O~S command'),
            yielding=True,
        )
        _w66.tooltip = _bind(    # main_menu.nml:380
            lambda _o: _tr('Type a command in a box and run it'),
            yielding=True,
        )
        _w66.command = ExecuteOsCommand    # main_menu.nml:381

        _w67.text = _bind(lambda _o: _tr('E~x~it'), yielding=True)    # main_menu.nml:383
        _w67.command = Quit    # main_menu.nml:384
        _w67.key = 'Alt-X'    # main_menu.nml:385

        self.disk.text = _bind(lambda _o: _tr('~D~isk'), yielding=True)    # main_menu.nml:388
        self.disk.tooltip = _bind(    # main_menu.nml:389
            lambda _o: _tr('The directory tree, volumes and the Trash'),
            yielding=True,
        )

        _w68.text = _bind(lambda _o: _tr('~D~irectory tree'), yielding=True)    # main_menu.nml:391
        _w68.command = OpenTreeWindow    # main_menu.nml:392

        _w69.text = _bind(lambda _o: _tr('~V~olumes'), yielding=True)    # main_menu.nml:394
        _w69.tooltip = _bind(    # main_menu.nml:395
            lambda _o: _tr('Disks and partitions: mount, unmount and eject them'),
            yielding=True,
        )
        _w69.command = OpenVolumesWindow    # main_menu.nml:396

        _w70.text = _bind(lambda _o: _tr('~M~ount image'), yielding=True)    # main_menu.nml:401
        _w70.tooltip = _bind(    # main_menu.nml:402
            lambda _o: _tr('The .iso or .img at the cursor: attached read-only, mounted and opened'),
            yielding=True,
        )
        _w70.command = MountImage    # main_menu.nml:403

        _w71.text = _bind(lambda _o: _tr('~U~nmount image'), yielding=True)    # main_menu.nml:405
        _w71.tooltip = _bind(    # main_menu.nml:406
            lambda _o: _tr('The disk image the panel is in, or at its cursor: unmounted and detached'),
            yielding=True,
        )
        _w71.command = UnmountImage    # main_menu.nml:407

        _w72.text = _bind(lambda _o: _tr('Directory ~s~izes'), yielding=True)    # main_menu.nml:410
        _w72.tooltip = _bind(    # main_menu.nml:411
            lambda _o: _tr("What takes the room under the panel's directory, biggest first"),
            yielding=True,
        )
        _w72.command = OpenUsageWindow    # main_menu.nml:412

        _w74.text = _bind(lambda _o: _tr('~T~rash'), yielding=True)    # main_menu.nml:417
        _w74.command = OpenTrash    # main_menu.nml:418

        _w75.text = _bind(lambda _o: _tr('~E~mpty Trash'), yielding=True)    # main_menu.nml:420
        _w75.command = EmptyTrash    # main_menu.nml:421

        self.utilities.text = _bind(    # main_menu.nml:424
            lambda _o: _tr('~U~tilities'),
            yielding=True,
        )
        self.utilities.tooltip = _bind(    # main_menu.nml:425
            lambda _o: _tr('Calculator, calendar, remote links, the user menu and histories'),
            yielding=True,
        )

        _w76.text = _bind(    # main_menu.nml:427
            lambda _o: _tr('S~y~stem Information'),
            yielding=True,
        )
        _w76.command = SystemInfo    # main_menu.nml:428

        _w77.text = _bind(lambda _o: _tr('~P~rocess list'), yielding=True)    # main_menu.nml:433
        _w77.tooltip = _bind(    # main_menu.nml:434
            lambda _o: _tr('The running processes: sort them, see one, send it a signal'),
            yielding=True,
        )
        _w77.command = OpenProcessWindow    # main_menu.nml:435

        _w78.text = _bind(lambda _o: _tr('~S~ervices'), yielding=True)    # main_menu.nml:440
        _w78.tooltip = _bind(    # main_menu.nml:441
            lambda _o: _tr("The system's services: start, stop, enable them, follow their log"),
            yielding=True,
        )
        _w78.command = OpenServiceWindow    # main_menu.nml:442

        _w79.text = _bind(lambda _o: _tr('System mo~n~itor'), yielding=True)    # main_menu.nml:447
        _w79.tooltip = _bind(    # main_menu.nml:448
            lambda _o: _tr("Each processor's load, the memory and the temperature sensors, read live"),
            yielding=True,
        )
        _w79.command = OpenMonitorWindow    # main_menu.nml:449

        _w81.text = _bind(lambda _o: _tr('~C~alculator'), yielding=True)    # main_menu.nml:452
        _w81.command = Calculator    # main_menu.nml:453
        _w81.key = 'Ctrl-F6'    # main_menu.nml:454

        _w82.text = _bind(lambda _o: _tr('Ca~l~endar'), yielding=True)    # main_menu.nml:458
        _w82.command = OpenCalendar    # main_menu.nml:459

        _w83.text = _bind(lambda _o: _tr('Character ta~b~le'), yielding=True)    # main_menu.nml:461
        _w83.tooltip = _bind(    # main_menu.nml:462
            lambda _o: _tr('Pick a character to type where the cursor is'),
            yielding=True,
        )
        _w83.command = AsciiTable    # main_menu.nml:463
        _w83.key = 'Ctrl-B'    # main_menu.nml:464

        self.utilities_link.text = _bind(    # main_menu.nml:478
            lambda _o: _tr('Lin~k~'),
            yielding=True,
        )
        self.utilities_link.tooltip = _bind(    # main_menu.nml:479
            lambda _o: _tr('A server, a share, a container or a phone: its files in the active panel'),
            yielding=True,
        )

        _w85.text = _bind(lambda _o: _tr('~S~SH (SFTP)...'), yielding=True)    # main_menu.nml:481
        _w85.command = NavyLink    # main_menu.nml:482
        _w85.key = 'Alt-F11'    # main_menu.nml:483

        _w86.text = _bind(lambda _o: _tr('~F~TP...'), yielding=True)    # main_menu.nml:485
        _w86.command = FtpLink    # main_menu.nml:486

        _w87.text = _bind(    # main_menu.nml:488
            lambda _o: _tr('S~M~B (Windows share)...'),
            yielding=True,
        )
        _w87.command = SmbLink    # main_menu.nml:489

        _w88.text = _bind(lambda _o: _tr('S~3~ (Amazon S3)...'), yielding=True)    # main_menu.nml:491
        _w88.command = S3Link    # main_menu.nml:492

        _w89.text = _bind(    # main_menu.nml:495
            lambda _o: _tr('~G~Vfs/KIO (MTP, WebDAV...)...'),
            yielding=True,
        )
        _w89.tooltip = _bind(    # main_menu.nml:496
            lambda _o: _tr('A phone, a WebDAV share, Google Drive: anything the desktop can mount'),
            yielding=True,
        )
        _w89.command = GvfsLink    # main_menu.nml:497

        _w91.text = _bind(    # main_menu.nml:501
            lambda _o: _tr('~D~ocker container...'),
            yielding=True,
        )
        _w91.tooltip = _bind(    # main_menu.nml:502
            lambda _o: _tr("A running container's files, through docker exec"),
            yielding=True,
        )
        _w91.command = DockerLink    # main_menu.nml:503

        _w92.text = _bind(    # main_menu.nml:505
            lambda _o: _tr('~P~odman container...'),
            yielding=True,
        )
        _w92.tooltip = _bind(    # main_menu.nml:506
            lambda _o: _tr("A running container's files, through podman exec"),
            yielding=True,
        )
        _w92.command = PodmanLink    # main_menu.nml:507

        _w93.text = _bind(    # main_menu.nml:509
            lambda _o: _tr('~A~ndroid device (adb)...'),
            yielding=True,
        )
        _w93.tooltip = _bind(    # main_menu.nml:510
            lambda _o: _tr("A phone's or a tablet's files, over USB debugging"),
            yielding=True,
        )
        _w93.command = AdbLink    # main_menu.nml:511

        self.utilities_shell.text = _bind(    # main_menu.nml:515
            lambda _o: _tr('Rem~o~te shell'),
            yielding=True,
        )
        self.utilities_shell.tooltip = _bind(    # main_menu.nml:516
            lambda _o: _tr('A shell on a server, in a container or on a phone, in a window'),
            yielding=True,
        )

        _w94.text = _bind(lambda _o: _tr('~S~SH...'), yielding=True)    # main_menu.nml:518
        _w94.tooltip = _bind(    # main_menu.nml:519
            lambda _o: _tr('A login shell on a server, ssh -t'),
            yielding=True,
        )
        _w94.command = Terminal    # main_menu.nml:520

        _w95.text = _bind(    # main_menu.nml:522
            lambda _o: _tr('~D~ocker container...'),
            yielding=True,
        )
        _w95.tooltip = _bind(    # main_menu.nml:523
            lambda _o: _tr('A shell in a running container, docker exec -it'),
            yielding=True,
        )
        _w95.command = DockerShell    # main_menu.nml:524

        _w96.text = _bind(    # main_menu.nml:526
            lambda _o: _tr('~P~odman container...'),
            yielding=True,
        )
        _w96.tooltip = _bind(    # main_menu.nml:527
            lambda _o: _tr('A shell in a running container, podman exec -it'),
            yielding=True,
        )
        _w96.command = PodmanShell    # main_menu.nml:528

        _w97.text = _bind(    # main_menu.nml:530
            lambda _o: _tr('~A~ndroid device (adb)...'),
            yielding=True,
        )
        _w97.tooltip = _bind(    # main_menu.nml:531
            lambda _o: _tr('A shell on a phone or a tablet, adb shell'),
            yielding=True,
        )
        _w97.command = AdbShell    # main_menu.nml:532

        _w98.text = _bind(lambda _o: _tr('~D~isconnect'), yielding=True)    # main_menu.nml:534
        _w98.tooltip = _bind(    # main_menu.nml:535
            lambda _o: _tr('Close a connection; its panels go back to the disk'),
            yielding=True,
        )
        _w98.command = HangUp    # main_menu.nml:536
        _w98.key = 'Alt-H'    # main_menu.nml:537

        _w99.text = _bind(lambda _o: _tr('Close ~r~oot access'), yielding=True)    # main_menu.nml:539
        _w99.tooltip = _bind(    # main_menu.nml:540
            lambda _o: _tr('End root access now, rather than after its timeout'),
            yielding=True,
        )
        _w99.command = CloseRootAccess    # main_menu.nml:541

        _w100.text = _bind(lambda _o: _tr('Saved l~i~nks...'), yielding=True)    # main_menu.nml:543
        _w100.tooltip = _bind(    # main_menu.nml:544
            lambda _o: _tr('The saved connections: edit them, or connect to one'),
            yielding=True,
        )
        _w100.command = EditLinks    # main_menu.nml:545

        _w102.text = _bind(lambda _o: _tr('Edi~t~ environment'), yielding=True)    # main_menu.nml:548
        _w102.tooltip = _bind(    # main_menu.nml:549
            lambda _o: _tr('Edit the environment variables commands run with'),
            yielding=True,
        )
        _w102.command = EnvEdit    # main_menu.nml:550

        _w103.text = _bind(lambda _o: _tr('~U~ser menu'), yielding=True)    # main_menu.nml:552
        _w103.command = UserMenu    # main_menu.nml:553
        _w103.key = 'F2'    # main_menu.nml:554

        _w104.text = _bind(lambda _o: _tr('Commands ~H~istory'), yielding=True)    # main_menu.nml:556
        _w104.command = HistoryList    # main_menu.nml:557
        _w104.key = 'Alt-F8'    # main_menu.nml:558

        _w105.text = _bind(    # main_menu.nml:561
            lambda _o: _tr('Fu~z~zy history search...'),
            yielding=True,
        )
        _w105.tooltip = _bind(    # main_menu.nml:562
            lambda _o: _tr('The commands typed, here and in the shell, searched by fzf'),
            yielding=True,
        )
        _w105.command = FuzzyHistory    # main_menu.nml:563
        _w105.key = 'Alt-Shift-F8'    # main_menu.nml:564

        _w106.text = _bind(    # main_menu.nml:566
            lambda _o: _tr('File ~E~dit History'),
            yielding=True,
        )
        _w106.command = EditHistory    # main_menu.nml:567
        _w106.key = 'Alt-PgUp'    # main_menu.nml:568

        _w107.text = _bind(    # main_menu.nml:570
            lambda _o: _tr('File ~V~iew History'),
            yielding=True,
        )
        _w107.command = ViewHistory    # main_menu.nml:571
        _w107.key = 'Alt-PgDn'    # main_menu.nml:572

        self.manager.text = _bind(lambda _o: _tr('~M~anager'), yielding=True)    # main_menu.nml:575
        self.manager.tooltip = _bind(    # main_menu.nml:576
            lambda _o: _tr('New file managers, swapping and hiding panels, bookmarks'),
            yielding=True,
        )

        _w108.text = _bind(lambda _o: _tr('~N~ew'), yielding=True)    # main_menu.nml:578
        _w108.command = NewManager    # main_menu.nml:579
        _w108.key = 'Ctrl-F3'    # main_menu.nml:580

        _w109.text = _bind(lambda _o: _tr('~S~wap panels'), yielding=True)    # main_menu.nml:582
        _w109.command = SwapPanels    # main_menu.nml:583
        _w109.key = 'Ctrl-U'    # main_menu.nml:584

        _w110.text = _bind(    # main_menu.nml:586
            lambda _o: _tr('Show/hide ~l~eft panel'),
            yielding=True,
        )
        _w110.command = HideLeft    # main_menu.nml:587
        _w110.key = 'Ctrl-F1'    # main_menu.nml:588

        _w111.text = _bind(    # main_menu.nml:590
            lambda _o: _tr('Show/hide ~r~ight panel'),
            yielding=True,
        )
        _w111.command = HideRight    # main_menu.nml:591
        _w111.key = 'Ctrl-F2'    # main_menu.nml:592

        _w112.text = _bind(    # main_menu.nml:594
            lambda _o: _tr('Show/hide inactive ~p~anel'),
            yielding=True,
        )
        _w112.tooltip = _bind(    # main_menu.nml:595
            lambda _o: _tr('Hide the panel without the keyboard, or show it again'),
            yielding=True,
        )
        _w112.command = HideInactive    # main_menu.nml:596
        _w112.key = 'Ctrl-P'    # main_menu.nml:597

        _w113.text = _bind(lambda _o: _tr('~M~iller columns'), yielding=True)    # main_menu.nml:601
        _w113.tooltip = _bind(    # main_menu.nml:602
            lambda _o: _tr('Browse in columns, each directory beside its parent'),
            yielding=True,
        )
        _w113.command = ToggleMiller    # main_menu.nml:603
        _w113.key = 'Alt-F12'    # main_menu.nml:604

        _w115.text = _bind(lambda _o: _tr('Bookmarks le~f~t'), yielding=True)    # main_menu.nml:607
        _w115.tooltip = _bind(    # main_menu.nml:608
            lambda _o: _tr('Send the left panel to a bookmarked directory'),
            yielding=True,
        )
        _w115.command = ChangeLeft    # main_menu.nml:609
        _w115.key = 'Alt-F1'    # main_menu.nml:610

        _w116.text = _bind(lambda _o: _tr('Bookmarks rig~h~t'), yielding=True)    # main_menu.nml:612
        _w116.tooltip = _bind(    # main_menu.nml:613
            lambda _o: _tr('Send the right panel to a bookmarked directory'),
            yielding=True,
        )
        _w116.command = ChangeRight    # main_menu.nml:614
        _w116.key = 'Alt-F2'    # main_menu.nml:615

        self.options.text = _bind(lambda _o: _tr('~O~ptions'), yielding=True)    # main_menu.nml:618
        self.options.tooltip = _bind(    # main_menu.nml:619
            lambda _o: _tr('Settings, configuration files, the desktop and colours'),
            yielding=True,
        )

        _w117.text = _bind(lambda _o: _tr('Sett~i~ngs...'), yielding=True)    # main_menu.nml:623
        _w117.tooltip = _bind(    # main_menu.nml:624
            lambda _o: _tr('Every setup page in one box, behind tabs'),
            yielding=True,
        )
        _w117.command = Settings    # main_menu.nml:625

        self.options_configuration.text = _bind(    # main_menu.nml:629
            lambda _o: _tr('~C~onfiguration'),
            yielding=True,
        )

        _w119.text = _bind(lambda _o: _tr('S~y~stem Setup...'), yielding=True)    # main_menu.nml:631
        _w119.command = SystemSetup    # main_menu.nml:632

        _w120.text = _bind(lambda _o: _tr('~S~tartup...'), yielding=True)    # main_menu.nml:634
        _w120.command = StartupSetup    # main_menu.nml:635

        _w121.text = _bind(lambda _o: _tr('~I~nterface...'), yielding=True)    # main_menu.nml:637
        _w121.command = InterfaceSetup    # main_menu.nml:638

        _w122.text = _bind(lambda _o: _tr('~C~onfirmations...'), yielding=True)    # main_menu.nml:640
        _w122.command = SetupConfirmation    # main_menu.nml:641

        _w124.text = _bind(lambda _o: _tr('Screen sa~v~ers...'), yielding=True)    # main_menu.nml:644
        _w124.command = SaversSetup    # main_menu.nml:645

        _w125.text = _bind(    # main_menu.nml:647
            lambda _o: _tr('C~o~untry support...'),
            yielding=True,
        )
        _w125.command = CountrySetup    # main_menu.nml:648

        _w126.text = _bind(    # main_menu.nml:650
            lambda _o: _tr('Comm~u~nications...'),
            yielding=True,
        )
        _w126.tooltip = _bind(    # main_menu.nml:651
            lambda _o: _tr('Settings for remote connections'),
            yielding=True,
        )
        _w126.command = SetupLink    # main_menu.nml:652

        _w128.text = _bind(lambda _o: _tr('~E~ditor/Viewer...'), yielding=True)    # main_menu.nml:655
        _w128.command = EditorDefaults    # main_menu.nml:656

        _w130.text = _bind(lambda _o: _tr('~K~ey bindings...'), yielding=True)    # main_menu.nml:659
        _w130.command = KeyBindingsSetup    # main_menu.nml:660

        self.options_file_manager.text = _bind(    # main_menu.nml:663
            lambda _o: _tr('~F~ile Manager'),
            yielding=True,
        )

        _w131.text = _bind(lambda _o: _tr('~S~etup...'), yielding=True)    # main_menu.nml:665
        _w131.command = FileManagerSetup    # main_menu.nml:666

        _w132.text = _bind(    # main_menu.nml:668
            lambda _o: _tr('~I~nformation panel...'),
            yielding=True,
        )
        _w132.tooltip = _bind(    # main_menu.nml:669
            lambda _o: _tr('What the information panel (Ctrl+L) shows'),
            yielding=True,
        )
        _w132.command = DriveInfoSetup    # main_menu.nml:670

        _w133.text = _bind(    # main_menu.nml:672
            lambda _o: _tr('New Manager ~d~efaults...'),
            yielding=True,
        )
        _w133.tooltip = _bind(    # main_menu.nml:673
            lambda _o: _tr("How a new file manager's panels start"),
            yielding=True,
        )
        _w133.command = FileManagerDefaults    # main_menu.nml:674

        _w134.text = _bind(    # main_menu.nml:676
            lambda _o: _tr('~C~olumn defaults...'),
            yielding=True,
        )
        _w134.tooltip = _bind(    # main_menu.nml:677
            lambda _o: _tr('The columns a new panel shows'),
            yielding=True,
        )
        _w134.command = ColumnDefaults    # main_menu.nml:678

        _w135.text = _bind(    # main_menu.nml:680
            lambda _o: _tr('~H~ighlight groups...'),
            yielding=True,
        )
        _w135.tooltip = _bind(    # main_menu.nml:681
            lambda _o: _tr('Which files the panels show in which colour'),
            yielding=True,
        )
        _w135.command = HighlightGroups    # main_menu.nml:682

        self.options_archives.text = _bind(    # main_menu.nml:685
            lambda _o: _tr('A~r~chives'),
            yielding=True,
        )

        _w136.text = _bind(    # main_menu.nml:687
            lambda _o: _tr('Current archiver...'),
            yielding=True,
        )
        _w136.key = 'Alt-N'    # main_menu.nml:688

        _w138.text = _bind(    # main_menu.nml:691
            lambda _o: _tr('~Q~uick run file edit...'),
            yielding=True,
        )
        _w138.tooltip = _bind(    # main_menu.nml:692
            lambda _o: _tr('Edit quickrun.ini: the commands Ctrl+Shift+F1 to F10 run'),
            yielding=True,
        )
        _w138.command = EditQuickRun    # main_menu.nml:693

        _w139.text = _bind(    # main_menu.nml:695
            lambda _o: _tr('E~x~tension file edit...'),
            yielding=True,
        )
        _w139.tooltip = _bind(    # main_menu.nml:696
            lambda _o: _tr('Edit extensions.ini: what Enter runs for each kind of file'),
            yielding=True,
        )
        _w139.command = ExtFileEdit    # main_menu.nml:697

        _w140.text = _bind(    # main_menu.nml:699
            lambda _o: _tr('~H~ighlight file edit...'),
            yielding=True,
        )
        _w140.tooltip = _bind(    # main_menu.nml:700
            lambda _o: _tr('Edit highlight.ini: which syntax colours which file'),
            yielding=True,
        )
        _w140.command = EditHGL    # main_menu.nml:701

        _w141.text = _bind(    # main_menu.nml:703
            lambda _o: _tr('Macro file e~d~it...'),
            yielding=True,
        )
        _w141.tooltip = _bind(    # main_menu.nml:704
            lambda _o: _tr("Edit macros.ini: the editor's macros, offered by Ctrl+J 0"),
            yielding=True,
        )
        _w141.command = EditMacros    # main_menu.nml:705

        _w142.text = _bind(    # main_menu.nml:707
            lambda _o: _tr('~G~lobal menu definition...'),
            yielding=True,
        )
        _w142.tooltip = _bind(    # main_menu.nml:708
            lambda _o: _tr('Edit the F2 user menu used everywhere'),
            yielding=True,
        )
        _w142.command = MenuFileEdit    # main_menu.nml:709

        _w143.text = _bind(    # main_menu.nml:711
            lambda _o: _tr('Local ~m~enu definition...'),
            yielding=True,
        )
        _w143.tooltip = _bind(    # main_menu.nml:712
            lambda _o: _tr("Edit this directory's own F2 user menu"),
            yielding=True,
        )
        _w143.command = LocalMenuFileEdit    # main_menu.nml:713

        _w144.text = _bind(lambda _o: _tr('~V~iewers...'), yielding=True)    # main_menu.nml:715
        _w144.tooltip = _bind(    # main_menu.nml:716
            lambda _o: _tr('Edit viewers.ini: the external viewer for each kind of file'),
            yielding=True,
        )
        _w144.command = ExternalViewers    # main_menu.nml:717

        _w145.text = _bind(lambda _o: _tr('~E~ditors...'), yielding=True)    # main_menu.nml:719
        _w145.tooltip = _bind(    # main_menu.nml:720
            lambda _o: _tr('Edit editors.ini: the external editor for each kind of file'),
            yielding=True,
        )
        _w145.command = ExternalEditors    # main_menu.nml:721

        _w147.text = _bind(lambda _o: _tr('~S~ave desktop'), yielding=True)    # main_menu.nml:724
        _w147.tooltip = _bind(    # main_menu.nml:725
            lambda _o: _tr('Keep the open windows, to have them back later'),
            yielding=True,
        )
        _w147.command = SaveDesktop    # main_menu.nml:726

        _w148.text = _bind(lambda _o: _tr('~L~oad desktop'), yielding=True)    # main_menu.nml:728
        _w148.tooltip = _bind(    # main_menu.nml:729
            lambda _o: _tr('Replace these windows with the ones last saved'),
            yielding=True,
        )
        _w148.command = LoadDesktop    # main_menu.nml:730

        _w150.text = _bind(lambda _o: _tr('C~o~lors...'), yielding=True)    # main_menu.nml:733
        _w150.command = ChangeColors    # main_menu.nml:734

        _w151.text = _bind(lambda _o: _tr('S~t~ore palette'), yielding=True)    # main_menu.nml:736
        _w151.tooltip = _bind(    # main_menu.nml:737
            lambda _o: _tr('Save the colours as a theme of your own'),
            yielding=True,
        )
        _w151.command = StoreColors    # main_menu.nml:738

        _w152.text = _bind(lambda _o: _tr('Lo~a~d palette'), yielding=True)    # main_menu.nml:740
        _w152.tooltip = _bind(    # main_menu.nml:741
            lambda _o: _tr('Use colours saved in a file'),
            yielding=True,
        )
        _w152.command = LoadColors    # main_menu.nml:742

        self.window.text = _bind(lambda _o: _tr('~W~indow'), yielding=True)    # main_menu.nml:745
        self.window.tooltip = _bind(    # main_menu.nml:746
            lambda _o: _tr('Arrange, switch between and close windows'),
            yielding=True,
        )

        _w153.text = _bind(lambda _o: _tr('~T~ile'), yielding=True)    # main_menu.nml:748
        _w153.command = TileWindows    # main_menu.nml:749

        _w154.text = _bind(lambda _o: _tr('C~a~scade'), yielding=True)    # main_menu.nml:751
        _w154.command = CascadeWindows    # main_menu.nml:752

        _w155.text = _bind(lambda _o: _tr('Cl~o~se all'), yielding=True)    # main_menu.nml:754
        _w155.command = CloseAllWindows    # main_menu.nml:755

        _w157.text = _bind(lambda _o: _tr('~S~ize/Move'), yielding=True)    # main_menu.nml:758
        _w157.tooltip = _bind(    # main_menu.nml:759
            lambda _o: _tr('Move and size the window with the keyboard'),
            yielding=True,
        )
        _w157.command = SizeMoveWindow    # main_menu.nml:760
        _w157.key = 'Ctrl-F5'    # main_menu.nml:761

        _w158.text = _bind(lambda _o: _tr('~Z~oom'), yielding=True)    # main_menu.nml:763
        _w158.command = ZoomWindow    # main_menu.nml:764
        _w158.key = 'Alt-Z'    # main_menu.nml:765

        _w159.text = _bind(lambda _o: _tr('~N~ext'), yielding=True)    # main_menu.nml:767
        _w159.command = NextWindow    # main_menu.nml:768
        _w159.key = 'F9'    # main_menu.nml:769

        _w160.text = _bind(lambda _o: _tr('~P~revious'), yielding=True)    # main_menu.nml:771
        _w160.command = PreviousWindow    # main_menu.nml:772
        _w160.key = 'Shift-F9'    # main_menu.nml:773

        _w161.text = _bind(lambda _o: _tr('~C~lose'), yielding=True)    # main_menu.nml:775
        _w161.command = CloseWindow    # main_menu.nml:776
        _w161.key = 'Ctrl-F4'    # main_menu.nml:777

        _w163.text = _bind(lambda _o: _tr('~L~ist...'), yielding=True)    # main_menu.nml:780
        _w163.tooltip = _bind(    # main_menu.nml:781
            lambda _o: _tr('All the windows, to switch to one or close it'),
            yielding=True,
        )
        _w163.command = WindowManager    # main_menu.nml:782
        _w163.key = 'Alt-0'    # main_menu.nml:783

        _w164.text = _bind(    # main_menu.nml:786
            lambda _o: _tr('~B~ackground operation...'),
            yielding=True,
        )
        _w164.tooltip = _bind(    # main_menu.nml:787
            lambda _o: _tr('Bring back the progress box of a copy or an erase running in the background'),
            yielding=True,
        )
        _w164.command = ShowBackground    # main_menu.nml:788
