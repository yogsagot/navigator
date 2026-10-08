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
from navigator.widgets.manager.commands import AlternateEdit, AlternateView, Calculator, ChangeAttributes, ChangeLeft, ChangeRight, Copy, Delete, DeleteSingle, Edit, EditNamed, FindFile, HideInactive, HideLeft, HideRight, MakeDirectory, MakeLink, RenameMove, SwapPanels, UserMenu, UuDecode, UuEncode, View, ViewAsDataBase, ViewAsHex, ViewAsText    # main_menu.nml:2
from navigator.widgets.shell.commands import About, Game, SaversSetup, ScreenRest, ToggleTrashCan, ChangeColors, ColumnDefaults, HighlightGroups, EditQuickRun, ExtFileEdit, ExternalViewers, ExternalEditors, LoadColors, StoreColors, LoadDesktop, SaveDesktop, DriveInfoSetup, EditHistory, EnvEdit, ExecuteOsCommand, HistoryList, OpenCalendar, SystemInfo, EditorDefaults, FileManagerDefaults, FileManagerSetup, InterfaceSetup, KeyBindingsSetup, LocalMenuFileEdit, MenuFileEdit, NewManager, OpenTreeWindow, SetupConfirmation, StartupSetup, SystemSetup, ViewHistory    # main_menu.nml:3
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
    modes*; *View as Spreadsheet* and *Unpack diskette images* (DN's own
    formats); *Format disk*, *Volume label*, *Reanimator* (FAT undelete) and
    *Disk editor* (sectors); *Memory Information* (conventional/XMS/EMS),
    *Phone Book*, *Open spreadsheet*, *CD Player*, and the modem's *Terminal*,
    *Navigator Link*, *Manual dial* and *Disconnect*; *Printer setup*,
    *Country support*, *Mouse*, *Communications* and *Terminal* under
    Configuration; and the seventeen DOS archivers under Archives, which a list
    of POSIX ones replaces once archives can be opened.  Two captions say what
    they mean here: *ASCII Table* is *Character table*, and *Edit DOS
    Environment* is *Edit environment*.  *Change drive left/right* are
    *Bookmarks left/right*: the box they open lists bookmarked directories
    where DN's listed drive letters (``navigator/bookmarks.py``).
    """

    #: The document this class was generated from.
    __navml_source__ = "main_menu.nml"

    #: Ids, annotated so the hand-written half completes them.
    system: SubMenu    # main_menu.nml:51
    file: SubMenu    # main_menu.nml:88
    file_view: SubMenu    # main_menu.nml:91
    file_edit: SubMenu    # main_menu.nml:112
    disk: SubMenu    # main_menu.nml:186
    utilities: SubMenu    # main_menu.nml:192
    manager: SubMenu    # main_menu.nml:232
    options: SubMenu    # main_menu.nml:264
    options_configuration: SubMenu    # main_menu.nml:267
    options_file_manager: SubMenu    # main_menu.nml:294
    options_archives: SubMenu    # main_menu.nml:312
    window: SubMenu    # main_menu.nml:356

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.system = SubMenu(parent=self)    # main_menu.nml:50
        _w1 = MenuItem(parent=self.system)    # main_menu.nml:53
        _w2 = MenuItem(parent=self.system)    # main_menu.nml:56
        _w3 = MenuItem(parent=self.system)    # main_menu.nml:59
        _w4 = MenuLine(parent=self.system)    # main_menu.nml:62
        _w5 = MenuItem(parent=self.system)    # main_menu.nml:63
        _w6 = MenuItem(parent=self.system)    # main_menu.nml:67
        _w7 = MenuItem(parent=self.system)    # main_menu.nml:71
        _w8 = MenuItem(parent=self.system)    # main_menu.nml:75
        _w9 = MenuItem(parent=self.system)    # main_menu.nml:79
        _w10 = MenuLine(parent=self.system)    # main_menu.nml:82
        _w11 = MenuItem(parent=self.system)    # main_menu.nml:83
        self.file = SubMenu(parent=self)    # main_menu.nml:87
        self.file_view = SubMenu(parent=self.file)    # main_menu.nml:90
        _w12 = MenuItem(parent=self.file_view)    # main_menu.nml:93
        _w13 = MenuItem(parent=self.file_view)    # main_menu.nml:97
        _w14 = MenuItem(parent=self.file_view)    # main_menu.nml:100
        _w15 = MenuItem(parent=self.file_view)    # main_menu.nml:103
        _w16 = MenuLine(parent=self.file_view)    # main_menu.nml:106
        _w17 = MenuItem(parent=self.file_view)    # main_menu.nml:107
        self.file_edit = SubMenu(parent=self.file)    # main_menu.nml:111
        _w18 = MenuItem(parent=self.file_edit)    # main_menu.nml:114
        _w19 = MenuItem(parent=self.file_edit)    # main_menu.nml:118
        _w20 = MenuLine(parent=self.file_edit)    # main_menu.nml:122
        _w21 = MenuItem(parent=self.file_edit)    # main_menu.nml:123
        _w22 = MenuItem(parent=self.file)    # main_menu.nml:127
        _w23 = MenuItem(parent=self.file)    # main_menu.nml:131
        _w24 = MenuItem(parent=self.file)    # main_menu.nml:135
        _w25 = MenuItem(parent=self.file)    # main_menu.nml:139
        _w26 = MenuItem(parent=self.file)    # main_menu.nml:142
        _w27 = MenuItem(parent=self.file)    # main_menu.nml:145
        _w28 = MenuItem(parent=self.file)    # main_menu.nml:149
        _w29 = MenuItem(parent=self.file)    # main_menu.nml:153
        _w30 = MenuItem(parent=self.file)    # main_menu.nml:157
        _w31 = MenuItem(parent=self.file)    # main_menu.nml:161
        _w32 = MenuItem(parent=self.file)    # main_menu.nml:165
        _w33 = MenuItem(parent=self.file)    # main_menu.nml:169
        _w34 = MenuItem(parent=self.file)    # main_menu.nml:173
        _w35 = MenuLine(parent=self.file)    # main_menu.nml:177
        _w36 = MenuItem(parent=self.file)    # main_menu.nml:178
        _w37 = MenuItem(parent=self.file)    # main_menu.nml:181
        self.disk = SubMenu(parent=self)    # main_menu.nml:185
        _w38 = MenuItem(parent=self.disk)    # main_menu.nml:188
        self.utilities = SubMenu(parent=self)    # main_menu.nml:191
        _w39 = MenuItem(parent=self.utilities)    # main_menu.nml:194
        _w40 = MenuLine(parent=self.utilities)    # main_menu.nml:197
        _w41 = MenuItem(parent=self.utilities)    # main_menu.nml:198
        _w42 = MenuItem(parent=self.utilities)    # main_menu.nml:204
        _w43 = MenuItem(parent=self.utilities)    # main_menu.nml:207
        _w44 = MenuLine(parent=self.utilities)    # main_menu.nml:211
        _w45 = MenuItem(parent=self.utilities)    # main_menu.nml:212
        _w46 = MenuItem(parent=self.utilities)    # main_menu.nml:215
        _w47 = MenuItem(parent=self.utilities)    # main_menu.nml:219
        _w48 = MenuItem(parent=self.utilities)    # main_menu.nml:223
        _w49 = MenuItem(parent=self.utilities)    # main_menu.nml:227
        self.manager = SubMenu(parent=self)    # main_menu.nml:231
        _w50 = MenuItem(parent=self.manager)    # main_menu.nml:234
        _w51 = MenuItem(parent=self.manager)    # main_menu.nml:238
        _w52 = MenuItem(parent=self.manager)    # main_menu.nml:242
        _w53 = MenuItem(parent=self.manager)    # main_menu.nml:246
        _w54 = MenuItem(parent=self.manager)    # main_menu.nml:250
        _w55 = MenuLine(parent=self.manager)    # main_menu.nml:254
        _w56 = MenuItem(parent=self.manager)    # main_menu.nml:255
        _w57 = MenuItem(parent=self.manager)    # main_menu.nml:259
        self.options = SubMenu(parent=self)    # main_menu.nml:263
        self.options_configuration = SubMenu(parent=self.options)    # main_menu.nml:266
        _w58 = MenuItem(parent=self.options_configuration)    # main_menu.nml:269
        _w59 = MenuItem(parent=self.options_configuration)    # main_menu.nml:272
        _w60 = MenuItem(parent=self.options_configuration)    # main_menu.nml:275
        _w61 = MenuItem(parent=self.options_configuration)    # main_menu.nml:278
        _w62 = MenuLine(parent=self.options_configuration)    # main_menu.nml:281
        _w63 = MenuItem(parent=self.options_configuration)    # main_menu.nml:282
        _w64 = MenuLine(parent=self.options_configuration)    # main_menu.nml:285
        _w65 = MenuItem(parent=self.options_configuration)    # main_menu.nml:286
        _w66 = MenuLine(parent=self.options_configuration)    # main_menu.nml:289
        _w67 = MenuItem(parent=self.options_configuration)    # main_menu.nml:290
        self.options_file_manager = SubMenu(parent=self.options)    # main_menu.nml:293
        _w68 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:296
        _w69 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:299
        _w70 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:302
        _w71 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:305
        _w72 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:308
        self.options_archives = SubMenu(parent=self.options)    # main_menu.nml:311
        _w73 = MenuItem(parent=self.options_archives)    # main_menu.nml:314
        _w74 = MenuLine(parent=self.options)    # main_menu.nml:317
        _w75 = MenuItem(parent=self.options)    # main_menu.nml:318
        _w76 = MenuItem(parent=self.options)    # main_menu.nml:321
        _w77 = MenuItem(parent=self.options)    # main_menu.nml:324
        _w78 = MenuItem(parent=self.options)    # main_menu.nml:326
        _w79 = MenuItem(parent=self.options)    # main_menu.nml:329
        _w80 = MenuItem(parent=self.options)    # main_menu.nml:332
        _w81 = MenuItem(parent=self.options)    # main_menu.nml:335
        _w82 = MenuLine(parent=self.options)    # main_menu.nml:338
        _w83 = MenuItem(parent=self.options)    # main_menu.nml:339
        _w84 = MenuItem(parent=self.options)    # main_menu.nml:342
        _w85 = MenuLine(parent=self.options)    # main_menu.nml:345
        _w86 = MenuItem(parent=self.options)    # main_menu.nml:346
        _w87 = MenuItem(parent=self.options)    # main_menu.nml:349
        _w88 = MenuItem(parent=self.options)    # main_menu.nml:352
        self.window = SubMenu(parent=self)    # main_menu.nml:355
        _w89 = MenuItem(parent=self.window)    # main_menu.nml:358
        _w90 = MenuItem(parent=self.window)    # main_menu.nml:361
        _w91 = MenuItem(parent=self.window)    # main_menu.nml:364
        _w92 = MenuLine(parent=self.window)    # main_menu.nml:367
        _w93 = MenuItem(parent=self.window)    # main_menu.nml:368
        _w94 = MenuItem(parent=self.window)    # main_menu.nml:372
        _w95 = MenuItem(parent=self.window)    # main_menu.nml:376
        _w96 = MenuItem(parent=self.window)    # main_menu.nml:380
        _w97 = MenuItem(parent=self.window)    # main_menu.nml:384
        _w98 = MenuLine(parent=self.window)    # main_menu.nml:388
        _w99 = MenuItem(parent=self.window)    # main_menu.nml:389

        self.system.text = '~≡~'    # main_menu.nml:52

        _w1.text = _bind(lambda _o: _tr('~A~bout...'), yielding=True)    # main_menu.nml:54
        _w1.command = About    # main_menu.nml:55

        _w2.text = _bind(lambda _o: _tr('~R~efresh display'), yielding=True)    # main_menu.nml:57
        _w2.command = Refresh    # main_menu.nml:58

        _w3.text = _bind(lambda _o: _tr('~S~creen rest'), yielding=True)    # main_menu.nml:60
        _w3.command = ScreenRest    # main_menu.nml:61

        _w5.text = _bind(lambda _o: _tr('Screen gra~b~ber'), yielding=True)    # main_menu.nml:64
        _w5.command = ScreenGrab    # main_menu.nml:65
        _w5.key = 'Shift-Alt-Ins'    # main_menu.nml:66

        _w6.text = _bind(lambda _o: _tr('~U~ser screen'), yielding=True)    # main_menu.nml:68
        _w6.command = ShowUserScreen    # main_menu.nml:69
        _w6.key = 'Alt-F5'    # main_menu.nml:70

        _w7.text = _bind(lambda _o: _tr('~O~utput window'), yielding=True)    # main_menu.nml:72
        _w7.command = ToggleConsole    # main_menu.nml:73
        _w7.key = 'Ctrl-O'    # main_menu.nml:74

        _w8.text = _bind(lambda _o: _tr('S~m~artPad (TM)'), yielding=True)    # main_menu.nml:76
        _w8.command = OpenSmartpad    # main_menu.nml:77
        _w8.key = 'Alt-Q'    # main_menu.nml:78

        _w9.text = _bind(lambda _o: _tr('~T~rashcan on/off'), yielding=True)    # main_menu.nml:80
        _w9.command = ToggleTrashCan    # main_menu.nml:81

        _w11.text = _bind(lambda _o: _tr('~G~ame'), yielding=True)    # main_menu.nml:84
        _w11.command = Game    # main_menu.nml:85
        _w11.key = 'Alt-F9'    # main_menu.nml:86

        self.file.text = _bind(lambda _o: _tr('~F~ile'), yielding=True)    # main_menu.nml:89

        self.file_view.text = _bind(lambda _o: _tr('~V~iew'), yielding=True)    # main_menu.nml:92

        _w12.text = _bind(lambda _o: _tr('~A~s is'), yielding=True)    # main_menu.nml:94
        _w12.command = View    # main_menu.nml:95
        _w12.key = 'F3'    # main_menu.nml:96

        _w13.text = _bind(lambda _o: _tr('As ~T~ext'), yielding=True)    # main_menu.nml:98
        _w13.command = ViewAsText    # main_menu.nml:99

        _w14.text = _bind(lambda _o: _tr('As He~x~'), yielding=True)    # main_menu.nml:101
        _w14.command = ViewAsHex    # main_menu.nml:102

        _w15.text = _bind(lambda _o: _tr('As ~D~ataBase'), yielding=True)    # main_menu.nml:104
        _w15.command = ViewAsDataBase    # main_menu.nml:105

        _w17.text = _bind(lambda _o: _tr('Alternate vie~w~'), yielding=True)    # main_menu.nml:108
        _w17.command = AlternateView    # main_menu.nml:109
        _w17.key = 'Alt-F3'    # main_menu.nml:110

        self.file_edit.text = _bind(lambda _o: _tr('~E~dit'), yielding=True)    # main_menu.nml:113

        _w18.text = _bind(lambda _o: _tr('~E~dit'), yielding=True)    # main_menu.nml:115
        _w18.command = Edit    # main_menu.nml:116
        _w18.key = 'F4'    # main_menu.nml:117

        _w19.text = _bind(lambda _o: _tr('~A~lternate edit'), yielding=True)    # main_menu.nml:119
        _w19.command = AlternateEdit    # main_menu.nml:120
        _w19.key = 'Alt-F4'    # main_menu.nml:121

        _w21.text = _bind(lambda _o: _tr('Edit ~n~ew file...'), yielding=True)    # main_menu.nml:124
        _w21.command = EditNamed    # main_menu.nml:125
        _w21.key = 'Shift-F4'    # main_menu.nml:126

        _w22.text = _bind(lambda _o: _tr('~F~ind...'), yielding=True)    # main_menu.nml:128
        _w22.command = FindFile    # main_menu.nml:129
        _w22.key = 'Alt-F7'    # main_menu.nml:130

        _w23.text = _bind(lambda _o: _tr('~C~opy...'), yielding=True)    # main_menu.nml:132
        _w23.command = Copy    # main_menu.nml:133
        _w23.key = 'F5'    # main_menu.nml:134

        _w24.text = _bind(lambda _o: _tr('~R~ename/Move...'), yielding=True)    # main_menu.nml:136
        _w24.command = RenameMove    # main_menu.nml:137
        _w24.key = 'F6'    # main_menu.nml:138

        _w25.text = _bind(    # main_menu.nml:140
            lambda _o: _tr('Cop~y~ to archive...'),
            yielding=True,
        )
        _w25.key = 'Shift-F1'    # main_menu.nml:141

        _w26.text = _bind(    # main_menu.nml:143
            lambda _o: _tr('Ex~t~ract archive...'),
            yielding=True,
        )
        _w26.key = 'Shift-F2'    # main_menu.nml:144

        _w27.text = _bind(lambda _o: _tr('Create ~s~ymlink...'), yielding=True)    # main_menu.nml:146
        _w27.command = MakeLink    # main_menu.nml:147
        _w27.key = 'Shift-F5'    # main_menu.nml:148

        _w28.text = _bind(lambda _o: _tr('~P~rint'), yielding=True)    # main_menu.nml:150
        _w28.command = PrintFile    # main_menu.nml:151
        _w28.key = 'Ctrl-F9'    # main_menu.nml:152

        _w29.text = _bind(lambda _o: _tr('~M~ake directory'), yielding=True)    # main_menu.nml:154
        _w29.command = MakeDirectory    # main_menu.nml:155
        _w29.key = 'F7'    # main_menu.nml:156

        _w30.text = _bind(lambda _o: _tr('~D~elete'), yielding=True)    # main_menu.nml:158
        _w30.command = Delete    # main_menu.nml:159
        _w30.key = 'F8'    # main_menu.nml:160

        _w31.text = _bind(    # main_menu.nml:162
            lambda _o: _tr('File ~A~ttributes...'),
            yielding=True,
        )
        _w31.command = ChangeAttributes    # main_menu.nml:163
        _w31.key = 'Alt-E'    # main_menu.nml:164

        _w32.text = _bind(lambda _o: _tr('UU E~n~code...'), yielding=True)    # main_menu.nml:166
        _w32.command = UuEncode    # main_menu.nml:167
        _w32.key = 'Ctrl-F7'    # main_menu.nml:168

        _w33.text = _bind(lambda _o: _tr('~U~U Decode...'), yielding=True)    # main_menu.nml:170
        _w33.command = UuDecode    # main_menu.nml:171
        _w33.key = 'Ctrl-F8'    # main_menu.nml:172

        _w34.text = _bind(lambda _o: _tr('Delete single file'), yielding=True)    # main_menu.nml:174
        _w34.command = DeleteSingle    # main_menu.nml:175
        _w34.key = 'Shift-Del'    # main_menu.nml:176

        _w36.text = _bind(    # main_menu.nml:179
            lambda _o: _tr('Execute ~O~S command'),
            yielding=True,
        )
        _w36.command = ExecuteOsCommand    # main_menu.nml:180

        _w37.text = _bind(lambda _o: _tr('E~x~it'), yielding=True)    # main_menu.nml:182
        _w37.command = Quit    # main_menu.nml:183
        _w37.key = 'Alt-X'    # main_menu.nml:184

        self.disk.text = _bind(lambda _o: _tr('~D~isk'), yielding=True)    # main_menu.nml:187

        _w38.text = _bind(lambda _o: _tr('~D~irectory tree'), yielding=True)    # main_menu.nml:189
        _w38.command = OpenTreeWindow    # main_menu.nml:190

        self.utilities.text = _bind(    # main_menu.nml:193
            lambda _o: _tr('~U~tilities'),
            yielding=True,
        )

        _w39.text = _bind(    # main_menu.nml:195
            lambda _o: _tr('S~y~stem Information'),
            yielding=True,
        )
        _w39.command = SystemInfo    # main_menu.nml:196

        _w41.text = _bind(lambda _o: _tr('~C~alculator'), yielding=True)    # main_menu.nml:199
        _w41.command = Calculator    # main_menu.nml:200
        _w41.key = 'Ctrl-F6'    # main_menu.nml:201

        _w42.text = _bind(lambda _o: _tr('Ca~l~endar'), yielding=True)    # main_menu.nml:205
        _w42.command = OpenCalendar    # main_menu.nml:206

        _w43.text = _bind(lambda _o: _tr('Character ta~b~le'), yielding=True)    # main_menu.nml:208
        _w43.command = AsciiTable    # main_menu.nml:209
        _w43.key = 'Ctrl-B'    # main_menu.nml:210

        _w45.text = _bind(lambda _o: _tr('Edi~t~ environment'), yielding=True)    # main_menu.nml:213
        _w45.command = EnvEdit    # main_menu.nml:214

        _w46.text = _bind(lambda _o: _tr('~U~ser menu'), yielding=True)    # main_menu.nml:216
        _w46.command = UserMenu    # main_menu.nml:217
        _w46.key = 'F2'    # main_menu.nml:218

        _w47.text = _bind(lambda _o: _tr('Commands ~H~istory'), yielding=True)    # main_menu.nml:220
        _w47.command = HistoryList    # main_menu.nml:221
        _w47.key = 'Alt-F8'    # main_menu.nml:222

        _w48.text = _bind(lambda _o: _tr('File ~E~dit History'), yielding=True)    # main_menu.nml:224
        _w48.command = EditHistory    # main_menu.nml:225
        _w48.key = 'Alt-PgUp'    # main_menu.nml:226

        _w49.text = _bind(lambda _o: _tr('File ~V~iew History'), yielding=True)    # main_menu.nml:228
        _w49.command = ViewHistory    # main_menu.nml:229
        _w49.key = 'Alt-PgDn'    # main_menu.nml:230

        self.manager.text = _bind(lambda _o: _tr('~M~anager'), yielding=True)    # main_menu.nml:233

        _w50.text = _bind(lambda _o: _tr('~N~ew'), yielding=True)    # main_menu.nml:235
        _w50.command = NewManager    # main_menu.nml:236
        _w50.key = 'Ctrl-F3'    # main_menu.nml:237

        _w51.text = _bind(lambda _o: _tr('~S~wap panels'), yielding=True)    # main_menu.nml:239
        _w51.command = SwapPanels    # main_menu.nml:240
        _w51.key = 'Ctrl-U'    # main_menu.nml:241

        _w52.text = _bind(    # main_menu.nml:243
            lambda _o: _tr('Show/hide ~l~eft panel'),
            yielding=True,
        )
        _w52.command = HideLeft    # main_menu.nml:244
        _w52.key = 'Ctrl-F1'    # main_menu.nml:245

        _w53.text = _bind(    # main_menu.nml:247
            lambda _o: _tr('Show/hide ~r~ight panel'),
            yielding=True,
        )
        _w53.command = HideRight    # main_menu.nml:248
        _w53.key = 'Ctrl-F2'    # main_menu.nml:249

        _w54.text = _bind(    # main_menu.nml:251
            lambda _o: _tr('Show/hide inactive ~p~anel'),
            yielding=True,
        )
        _w54.command = HideInactive    # main_menu.nml:252
        _w54.key = 'Ctrl-P'    # main_menu.nml:253

        _w56.text = _bind(lambda _o: _tr('Bookmarks le~f~t'), yielding=True)    # main_menu.nml:256
        _w56.command = ChangeLeft    # main_menu.nml:257
        _w56.key = 'Alt-F1'    # main_menu.nml:258

        _w57.text = _bind(lambda _o: _tr('Bookmarks rig~h~t'), yielding=True)    # main_menu.nml:260
        _w57.command = ChangeRight    # main_menu.nml:261
        _w57.key = 'Alt-F2'    # main_menu.nml:262

        self.options.text = _bind(lambda _o: _tr('~O~ptions'), yielding=True)    # main_menu.nml:265

        self.options_configuration.text = _bind(    # main_menu.nml:268
            lambda _o: _tr('~C~onfiguration'),
            yielding=True,
        )

        _w58.text = _bind(lambda _o: _tr('S~y~stem Setup...'), yielding=True)    # main_menu.nml:270
        _w58.command = SystemSetup    # main_menu.nml:271

        _w59.text = _bind(lambda _o: _tr('~S~tartup...'), yielding=True)    # main_menu.nml:273
        _w59.command = StartupSetup    # main_menu.nml:274

        _w60.text = _bind(lambda _o: _tr('~I~nterface...'), yielding=True)    # main_menu.nml:276
        _w60.command = InterfaceSetup    # main_menu.nml:277

        _w61.text = _bind(lambda _o: _tr('~C~onfirmations...'), yielding=True)    # main_menu.nml:279
        _w61.command = SetupConfirmation    # main_menu.nml:280

        _w63.text = _bind(lambda _o: _tr('Screen sa~v~ers...'), yielding=True)    # main_menu.nml:283
        _w63.command = SaversSetup    # main_menu.nml:284

        _w65.text = _bind(lambda _o: _tr('~E~ditor/Viewer...'), yielding=True)    # main_menu.nml:287
        _w65.command = EditorDefaults    # main_menu.nml:288

        _w67.text = _bind(lambda _o: _tr('~K~ey bindings...'), yielding=True)    # main_menu.nml:291
        _w67.command = KeyBindingsSetup    # main_menu.nml:292

        self.options_file_manager.text = _bind(    # main_menu.nml:295
            lambda _o: _tr('~F~ile Manager'),
            yielding=True,
        )

        _w68.text = _bind(lambda _o: _tr('~S~etup...'), yielding=True)    # main_menu.nml:297
        _w68.command = FileManagerSetup    # main_menu.nml:298

        _w69.text = _bind(    # main_menu.nml:300
            lambda _o: _tr('~I~nformation panel...'),
            yielding=True,
        )
        _w69.command = DriveInfoSetup    # main_menu.nml:301

        _w70.text = _bind(    # main_menu.nml:303
            lambda _o: _tr('New Manager ~d~efaults...'),
            yielding=True,
        )
        _w70.command = FileManagerDefaults    # main_menu.nml:304

        _w71.text = _bind(    # main_menu.nml:306
            lambda _o: _tr('~C~olumn defaults...'),
            yielding=True,
        )
        _w71.command = ColumnDefaults    # main_menu.nml:307

        _w72.text = _bind(    # main_menu.nml:309
            lambda _o: _tr('~H~ighlight groups...'),
            yielding=True,
        )
        _w72.command = HighlightGroups    # main_menu.nml:310

        self.options_archives.text = _bind(    # main_menu.nml:313
            lambda _o: _tr('A~r~chives'),
            yielding=True,
        )

        _w73.text = _bind(lambda _o: _tr('Current archiver...'), yielding=True)    # main_menu.nml:315
        _w73.key = 'Alt-N'    # main_menu.nml:316

        _w75.text = _bind(    # main_menu.nml:319
            lambda _o: _tr('~Q~uick run file edit...'),
            yielding=True,
        )
        _w75.command = EditQuickRun    # main_menu.nml:320

        _w76.text = _bind(    # main_menu.nml:322
            lambda _o: _tr('E~x~tension file edit...'),
            yielding=True,
        )
        _w76.command = ExtFileEdit    # main_menu.nml:323

        _w77.text = _bind(    # main_menu.nml:325
            lambda _o: _tr('~H~ighlight file edit...'),
            yielding=True,
        )

        _w78.text = _bind(    # main_menu.nml:327
            lambda _o: _tr('~G~lobal menu definition...'),
            yielding=True,
        )
        _w78.command = MenuFileEdit    # main_menu.nml:328

        _w79.text = _bind(    # main_menu.nml:330
            lambda _o: _tr('Local ~m~enu definition...'),
            yielding=True,
        )
        _w79.command = LocalMenuFileEdit    # main_menu.nml:331

        _w80.text = _bind(lambda _o: _tr('~V~iewers...'), yielding=True)    # main_menu.nml:333
        _w80.command = ExternalViewers    # main_menu.nml:334

        _w81.text = _bind(lambda _o: _tr('~E~ditors...'), yielding=True)    # main_menu.nml:336
        _w81.command = ExternalEditors    # main_menu.nml:337

        _w83.text = _bind(lambda _o: _tr('~S~ave desktop'), yielding=True)    # main_menu.nml:340
        _w83.command = SaveDesktop    # main_menu.nml:341

        _w84.text = _bind(lambda _o: _tr('~L~oad desktop'), yielding=True)    # main_menu.nml:343
        _w84.command = LoadDesktop    # main_menu.nml:344

        _w86.text = _bind(lambda _o: _tr('C~o~lors...'), yielding=True)    # main_menu.nml:347
        _w86.command = ChangeColors    # main_menu.nml:348

        _w87.text = _bind(lambda _o: _tr('S~t~ore palette'), yielding=True)    # main_menu.nml:350
        _w87.command = StoreColors    # main_menu.nml:351

        _w88.text = _bind(lambda _o: _tr('Lo~a~d palette'), yielding=True)    # main_menu.nml:353
        _w88.command = LoadColors    # main_menu.nml:354

        self.window.text = _bind(lambda _o: _tr('~W~indow'), yielding=True)    # main_menu.nml:357

        _w89.text = _bind(lambda _o: _tr('~T~ile'), yielding=True)    # main_menu.nml:359
        _w89.command = TileWindows    # main_menu.nml:360

        _w90.text = _bind(lambda _o: _tr('C~a~scade'), yielding=True)    # main_menu.nml:362
        _w90.command = CascadeWindows    # main_menu.nml:363

        _w91.text = _bind(lambda _o: _tr('Cl~o~se all'), yielding=True)    # main_menu.nml:365
        _w91.command = CloseAllWindows    # main_menu.nml:366

        _w93.text = _bind(lambda _o: _tr('~S~ize/Move'), yielding=True)    # main_menu.nml:369
        _w93.command = SizeMoveWindow    # main_menu.nml:370
        _w93.key = 'Ctrl-F5'    # main_menu.nml:371

        _w94.text = _bind(lambda _o: _tr('~Z~oom'), yielding=True)    # main_menu.nml:373
        _w94.command = ZoomWindow    # main_menu.nml:374
        _w94.key = 'Alt-Z'    # main_menu.nml:375

        _w95.text = _bind(lambda _o: _tr('~N~ext'), yielding=True)    # main_menu.nml:377
        _w95.command = NextWindow    # main_menu.nml:378
        _w95.key = 'Alt-Tab'    # main_menu.nml:379

        _w96.text = _bind(lambda _o: _tr('~P~revious'), yielding=True)    # main_menu.nml:381
        _w96.command = PreviousWindow    # main_menu.nml:382
        _w96.key = 'Ctrl-Tab'    # main_menu.nml:383

        _w97.text = _bind(lambda _o: _tr('~C~lose'), yielding=True)    # main_menu.nml:385
        _w97.command = CloseWindow    # main_menu.nml:386
        _w97.key = 'Ctrl-F4'    # main_menu.nml:387

        _w99.text = _bind(lambda _o: _tr('~L~ist...'), yielding=True)    # main_menu.nml:390
        _w99.command = WindowManager    # main_menu.nml:391
        _w99.key = 'Alt-0'    # main_menu.nml:392
