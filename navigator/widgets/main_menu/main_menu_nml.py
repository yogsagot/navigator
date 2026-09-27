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

from navml.component import Component as _Component
from navigator.commands import Copy, Delete, Edit, MakeDirectory, Quit, RenameMove, Rescan, ToggleConsole, ToggleTree, UserMenu, View    # main_menu.nml:1
from navml.commands import CloseWindow, NextWindow, PreviousWindow, SizeMoveWindow, ZoomWindow    # main_menu.nml:2
from navml.widgets.menu.menu_bar import MenuBar    # main_menu.nml:3
from navml.widgets.menu.menu_item import MenuItem    # main_menu.nml:4
from navml.widgets.menu.menu_line import MenuLine    # main_menu.nml:5
from navml.widgets.menu.sub_menu import SubMenu    # main_menu.nml:6

__navml_component__ = "MainMenu"

__all__ = ["MainMenu"]


class MainMenu(MenuBar, _Component):
    """DOS Navigator 1.51's main menu, transcribed from ``dlgMainMenu`` in

    ``RESOURCE/ENGLISH/DN.DNR`` -- every entry, in the original's order and
    with the original's captions and hotkeys.

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
    """

    #: The document this class was generated from.
    __navml_source__ = "main_menu.nml"

    #: Ids, annotated so the hand-written half completes them.
    system: SubMenu    # main_menu.nml:26
    file: SubMenu    # main_menu.nml:65
    file_view: SubMenu    # main_menu.nml:68
    file_edit: SubMenu    # main_menu.nml:87
    disk: SubMenu    # main_menu.nml:154
    utilities: SubMenu    # main_menu.nml:169
    panel: SubMenu    # main_menu.nml:222
    manager: SubMenu    # main_menu.nml:280
    options: SubMenu    # main_menu.nml:316
    options_configuration: SubMenu    # main_menu.nml:319
    options_file_manager: SubMenu    # main_menu.nml:346
    options_archives: SubMenu    # main_menu.nml:359
    window: SubMenu    # main_menu.nml:427

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.system = SubMenu(parent=self)    # main_menu.nml:25
        _w1 = MenuItem(parent=self.system)    # main_menu.nml:28
        _w2 = MenuItem(parent=self.system)    # main_menu.nml:30
        _w3 = MenuItem(parent=self.system)    # main_menu.nml:32
        _w4 = MenuLine(parent=self.system)    # main_menu.nml:34
        _w5 = MenuItem(parent=self.system)    # main_menu.nml:35
        _w6 = MenuItem(parent=self.system)    # main_menu.nml:38
        _w7 = MenuItem(parent=self.system)    # main_menu.nml:41
        _w8 = MenuItem(parent=self.system)    # main_menu.nml:45
        _w9 = MenuItem(parent=self.system)    # main_menu.nml:48
        _w10 = MenuLine(parent=self.system)    # main_menu.nml:50
        _w11 = MenuItem(parent=self.system)    # main_menu.nml:51
        _w12 = MenuItem(parent=self.system)    # main_menu.nml:54
        _w13 = MenuItem(parent=self.system)    # main_menu.nml:57
        _w14 = MenuLine(parent=self.system)    # main_menu.nml:60
        _w15 = MenuItem(parent=self.system)    # main_menu.nml:61
        self.file = SubMenu(parent=self)    # main_menu.nml:64
        self.file_view = SubMenu(parent=self.file)    # main_menu.nml:67
        _w16 = MenuItem(parent=self.file_view)    # main_menu.nml:70
        _w17 = MenuItem(parent=self.file_view)    # main_menu.nml:74
        _w18 = MenuItem(parent=self.file_view)    # main_menu.nml:76
        _w19 = MenuItem(parent=self.file_view)    # main_menu.nml:78
        _w20 = MenuItem(parent=self.file_view)    # main_menu.nml:80
        _w21 = MenuLine(parent=self.file_view)    # main_menu.nml:82
        _w22 = MenuItem(parent=self.file_view)    # main_menu.nml:83
        self.file_edit = SubMenu(parent=self.file)    # main_menu.nml:86
        _w23 = MenuItem(parent=self.file_edit)    # main_menu.nml:89
        _w24 = MenuItem(parent=self.file_edit)    # main_menu.nml:93
        _w25 = MenuLine(parent=self.file_edit)    # main_menu.nml:96
        _w26 = MenuItem(parent=self.file_edit)    # main_menu.nml:97
        _w27 = MenuItem(parent=self.file)    # main_menu.nml:100
        _w28 = MenuItem(parent=self.file)    # main_menu.nml:103
        _w29 = MenuItem(parent=self.file)    # main_menu.nml:107
        _w30 = MenuItem(parent=self.file)    # main_menu.nml:111
        _w31 = MenuItem(parent=self.file)    # main_menu.nml:114
        _w32 = MenuItem(parent=self.file)    # main_menu.nml:117
        _w33 = MenuItem(parent=self.file)    # main_menu.nml:120
        _w34 = MenuItem(parent=self.file)    # main_menu.nml:123
        _w35 = MenuItem(parent=self.file)    # main_menu.nml:127
        _w36 = MenuItem(parent=self.file)    # main_menu.nml:131
        _w37 = MenuItem(parent=self.file)    # main_menu.nml:134
        _w38 = MenuItem(parent=self.file)    # main_menu.nml:137
        _w39 = MenuItem(parent=self.file)    # main_menu.nml:140
        _w40 = MenuItem(parent=self.file)    # main_menu.nml:143
        _w41 = MenuLine(parent=self.file)    # main_menu.nml:146
        _w42 = MenuItem(parent=self.file)    # main_menu.nml:147
        _w43 = MenuItem(parent=self.file)    # main_menu.nml:149
        self.disk = SubMenu(parent=self)    # main_menu.nml:153
        _w44 = MenuItem(parent=self.disk)    # main_menu.nml:156
        _w45 = MenuItem(parent=self.disk)    # main_menu.nml:159
        _w46 = MenuItem(parent=self.disk)    # main_menu.nml:161
        _w47 = MenuItem(parent=self.disk)    # main_menu.nml:164
        _w48 = MenuItem(parent=self.disk)    # main_menu.nml:166
        self.utilities = SubMenu(parent=self)    # main_menu.nml:168
        _w49 = MenuItem(parent=self.utilities)    # main_menu.nml:171
        _w50 = MenuItem(parent=self.utilities)    # main_menu.nml:174
        _w51 = MenuLine(parent=self.utilities)    # main_menu.nml:176
        _w52 = MenuItem(parent=self.utilities)    # main_menu.nml:177
        _w53 = MenuItem(parent=self.utilities)    # main_menu.nml:180
        _w54 = MenuItem(parent=self.utilities)    # main_menu.nml:183
        _w55 = MenuItem(parent=self.utilities)    # main_menu.nml:186
        _w56 = MenuItem(parent=self.utilities)    # main_menu.nml:189
        _w57 = MenuLine(parent=self.utilities)    # main_menu.nml:192
        _w58 = MenuItem(parent=self.utilities)    # main_menu.nml:193
        _w59 = MenuItem(parent=self.utilities)    # main_menu.nml:196
        _w60 = MenuItem(parent=self.utilities)    # main_menu.nml:199
        _w61 = MenuItem(parent=self.utilities)    # main_menu.nml:202
        _w62 = MenuLine(parent=self.utilities)    # main_menu.nml:205
        _w63 = MenuItem(parent=self.utilities)    # main_menu.nml:206
        _w64 = MenuItem(parent=self.utilities)    # main_menu.nml:208
        _w65 = MenuItem(parent=self.utilities)    # main_menu.nml:212
        _w66 = MenuItem(parent=self.utilities)    # main_menu.nml:215
        _w67 = MenuItem(parent=self.utilities)    # main_menu.nml:218
        self.panel = SubMenu(parent=self)    # main_menu.nml:221
        _w68 = MenuItem(parent=self.panel)    # main_menu.nml:224
        _w69 = MenuItem(parent=self.panel)    # main_menu.nml:227
        _w70 = MenuItem(parent=self.panel)    # main_menu.nml:230
        _w71 = MenuItem(parent=self.panel)    # main_menu.nml:233
        _w72 = MenuItem(parent=self.panel)    # main_menu.nml:236
        _w73 = MenuLine(parent=self.panel)    # main_menu.nml:239
        _w74 = MenuItem(parent=self.panel)    # main_menu.nml:240
        _w75 = MenuItem(parent=self.panel)    # main_menu.nml:243
        _w76 = MenuItem(parent=self.panel)    # main_menu.nml:246
        _w77 = MenuLine(parent=self.panel)    # main_menu.nml:249
        _w78 = MenuItem(parent=self.panel)    # main_menu.nml:250
        _w79 = MenuItem(parent=self.panel)    # main_menu.nml:253
        _w80 = MenuItem(parent=self.panel)    # main_menu.nml:256
        _w81 = MenuItem(parent=self.panel)    # main_menu.nml:259
        _w82 = MenuLine(parent=self.panel)    # main_menu.nml:262
        _w83 = MenuItem(parent=self.panel)    # main_menu.nml:263
        _w84 = MenuItem(parent=self.panel)    # main_menu.nml:266
        _w85 = MenuItem(parent=self.panel)    # main_menu.nml:269
        _w86 = MenuItem(parent=self.panel)    # main_menu.nml:273
        _w87 = MenuItem(parent=self.panel)    # main_menu.nml:276
        self.manager = SubMenu(parent=self)    # main_menu.nml:279
        _w88 = MenuItem(parent=self.manager)    # main_menu.nml:282
        _w89 = MenuItem(parent=self.manager)    # main_menu.nml:285
        _w90 = MenuItem(parent=self.manager)    # main_menu.nml:289
        _w91 = MenuItem(parent=self.manager)    # main_menu.nml:292
        _w92 = MenuLine(parent=self.manager)    # main_menu.nml:295
        _w93 = MenuItem(parent=self.manager)    # main_menu.nml:296
        _w94 = MenuItem(parent=self.manager)    # main_menu.nml:299
        _w95 = MenuItem(parent=self.manager)    # main_menu.nml:302
        _w96 = MenuItem(parent=self.manager)    # main_menu.nml:305
        _w97 = MenuLine(parent=self.manager)    # main_menu.nml:308
        _w98 = MenuItem(parent=self.manager)    # main_menu.nml:309
        _w99 = MenuItem(parent=self.manager)    # main_menu.nml:312
        self.options = SubMenu(parent=self)    # main_menu.nml:315
        self.options_configuration = SubMenu(parent=self.options)    # main_menu.nml:318
        _w100 = MenuItem(parent=self.options_configuration)    # main_menu.nml:321
        _w101 = MenuItem(parent=self.options_configuration)    # main_menu.nml:323
        _w102 = MenuItem(parent=self.options_configuration)    # main_menu.nml:325
        _w103 = MenuItem(parent=self.options_configuration)    # main_menu.nml:327
        _w104 = MenuLine(parent=self.options_configuration)    # main_menu.nml:329
        _w105 = MenuItem(parent=self.options_configuration)    # main_menu.nml:330
        _w106 = MenuItem(parent=self.options_configuration)    # main_menu.nml:332
        _w107 = MenuItem(parent=self.options_configuration)    # main_menu.nml:334
        _w108 = MenuItem(parent=self.options_configuration)    # main_menu.nml:336
        _w109 = MenuItem(parent=self.options_configuration)    # main_menu.nml:338
        _w110 = MenuLine(parent=self.options_configuration)    # main_menu.nml:340
        _w111 = MenuItem(parent=self.options_configuration)    # main_menu.nml:341
        _w112 = MenuItem(parent=self.options_configuration)    # main_menu.nml:343
        self.options_file_manager = SubMenu(parent=self.options)    # main_menu.nml:345
        _w113 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:348
        _w114 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:350
        _w115 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:352
        _w116 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:354
        _w117 = MenuItem(parent=self.options_file_manager)    # main_menu.nml:356
        self.options_archives = SubMenu(parent=self.options)    # main_menu.nml:358
        _w118 = MenuItem(parent=self.options_archives)    # main_menu.nml:361
        _w119 = MenuItem(parent=self.options_archives)    # main_menu.nml:363
        _w120 = MenuItem(parent=self.options_archives)    # main_menu.nml:365
        _w121 = MenuItem(parent=self.options_archives)    # main_menu.nml:367
        _w122 = MenuItem(parent=self.options_archives)    # main_menu.nml:369
        _w123 = MenuItem(parent=self.options_archives)    # main_menu.nml:371
        _w124 = MenuItem(parent=self.options_archives)    # main_menu.nml:373
        _w125 = MenuItem(parent=self.options_archives)    # main_menu.nml:375
        _w126 = MenuItem(parent=self.options_archives)    # main_menu.nml:377
        _w127 = MenuItem(parent=self.options_archives)    # main_menu.nml:379
        _w128 = MenuItem(parent=self.options_archives)    # main_menu.nml:381
        _w129 = MenuItem(parent=self.options_archives)    # main_menu.nml:383
        _w130 = MenuItem(parent=self.options_archives)    # main_menu.nml:385
        _w131 = MenuItem(parent=self.options_archives)    # main_menu.nml:387
        _w132 = MenuItem(parent=self.options_archives)    # main_menu.nml:389
        _w133 = MenuItem(parent=self.options_archives)    # main_menu.nml:391
        _w134 = MenuItem(parent=self.options_archives)    # main_menu.nml:393
        _w135 = MenuLine(parent=self.options_archives)    # main_menu.nml:395
        _w136 = MenuItem(parent=self.options_archives)    # main_menu.nml:396
        _w137 = MenuLine(parent=self.options)    # main_menu.nml:399
        _w138 = MenuItem(parent=self.options)    # main_menu.nml:400
        _w139 = MenuItem(parent=self.options)    # main_menu.nml:402
        _w140 = MenuItem(parent=self.options)    # main_menu.nml:404
        _w141 = MenuItem(parent=self.options)    # main_menu.nml:406
        _w142 = MenuItem(parent=self.options)    # main_menu.nml:408
        _w143 = MenuItem(parent=self.options)    # main_menu.nml:410
        _w144 = MenuItem(parent=self.options)    # main_menu.nml:412
        _w145 = MenuLine(parent=self.options)    # main_menu.nml:414
        _w146 = MenuItem(parent=self.options)    # main_menu.nml:415
        _w147 = MenuItem(parent=self.options)    # main_menu.nml:417
        _w148 = MenuLine(parent=self.options)    # main_menu.nml:419
        _w149 = MenuItem(parent=self.options)    # main_menu.nml:420
        _w150 = MenuItem(parent=self.options)    # main_menu.nml:422
        _w151 = MenuItem(parent=self.options)    # main_menu.nml:424
        self.window = SubMenu(parent=self)    # main_menu.nml:426
        _w152 = MenuItem(parent=self.window)    # main_menu.nml:429
        _w153 = MenuItem(parent=self.window)    # main_menu.nml:431
        _w154 = MenuItem(parent=self.window)    # main_menu.nml:433
        _w155 = MenuLine(parent=self.window)    # main_menu.nml:435
        _w156 = MenuItem(parent=self.window)    # main_menu.nml:436
        _w157 = MenuItem(parent=self.window)    # main_menu.nml:440
        _w158 = MenuItem(parent=self.window)    # main_menu.nml:444
        _w159 = MenuItem(parent=self.window)    # main_menu.nml:448
        _w160 = MenuItem(parent=self.window)    # main_menu.nml:452
        _w161 = MenuLine(parent=self.window)    # main_menu.nml:456
        _w162 = MenuItem(parent=self.window)    # main_menu.nml:457

        self.system.text = '~≡~'    # main_menu.nml:27

        _w1.text = '~A~bout...'    # main_menu.nml:29

        _w2.text = '~R~efresh display'    # main_menu.nml:31

        _w3.text = '~S~creen rest'    # main_menu.nml:33

        _w5.text = 'Screen gra~b~ber'    # main_menu.nml:36
        _w5.key = 'Shift-Alt-Ins'    # main_menu.nml:37

        _w6.text = '~U~ser screen'    # main_menu.nml:39
        _w6.key = 'Alt-F5'    # main_menu.nml:40

        _w7.text = '~O~utput window'    # main_menu.nml:42
        _w7.command = ToggleConsole    # main_menu.nml:43
        _w7.key = 'Ctrl-O'    # main_menu.nml:44

        _w8.text = 'S~m~artPad (TM)'    # main_menu.nml:46
        _w8.key = 'Alt-Q'    # main_menu.nml:47

        _w9.text = '~T~rashcan on/off'    # main_menu.nml:49

        _w11.text = '~E~GA/VGA lines'    # main_menu.nml:52
        _w11.key = 'Shift-F10'    # main_menu.nml:53

        _w12.text = 'Custom video mode ~1~'    # main_menu.nml:55
        _w12.key = 'Alt-F10'    # main_menu.nml:56

        _w13.text = 'Custom video mode ~2~'    # main_menu.nml:58
        _w13.key = 'Ctrl-F10'    # main_menu.nml:59

        _w15.text = '~G~ame'    # main_menu.nml:62
        _w15.key = 'Alt-F9'    # main_menu.nml:63

        self.file.text = '~F~ile'    # main_menu.nml:66

        self.file_view.text = '~V~iew'    # main_menu.nml:69

        _w16.text = '~A~s is'    # main_menu.nml:71
        _w16.command = View    # main_menu.nml:72
        _w16.key = 'F3'    # main_menu.nml:73

        _w17.text = 'As ~T~ext'    # main_menu.nml:75

        _w18.text = 'As He~x~'    # main_menu.nml:77

        _w19.text = 'As ~D~ataBase'    # main_menu.nml:79

        _w20.text = 'As ~S~preadsheet'    # main_menu.nml:81

        _w22.text = 'Alternate vie~w~'    # main_menu.nml:84
        _w22.key = 'Alt-F3'    # main_menu.nml:85

        self.file_edit.text = '~E~dit'    # main_menu.nml:88

        _w23.text = '~E~dit'    # main_menu.nml:90
        _w23.command = Edit    # main_menu.nml:91
        _w23.key = 'F4'    # main_menu.nml:92

        _w24.text = '~A~lternate edit'    # main_menu.nml:94
        _w24.key = 'Alt-F4'    # main_menu.nml:95

        _w26.text = 'Edit ~n~ew file...'    # main_menu.nml:98
        _w26.key = 'Shift-F4'    # main_menu.nml:99

        _w27.text = '~F~ind...'    # main_menu.nml:101
        _w27.key = 'Alt-F7'    # main_menu.nml:102

        _w28.text = '~C~opy...'    # main_menu.nml:104
        _w28.command = Copy    # main_menu.nml:105
        _w28.key = 'F5'    # main_menu.nml:106

        _w29.text = '~R~ename/Move...'    # main_menu.nml:108
        _w29.command = RenameMove    # main_menu.nml:109
        _w29.key = 'F6'    # main_menu.nml:110

        _w30.text = 'Cop~y~ to archive...'    # main_menu.nml:112
        _w30.key = 'Shift-F1'    # main_menu.nml:113

        _w31.text = 'Ex~t~ract archive...'    # main_menu.nml:115
        _w31.key = 'Shift-F2'    # main_menu.nml:116

        _w32.text = '~S~plit/combine...'    # main_menu.nml:118
        _w32.key = 'Shift-F5'    # main_menu.nml:119

        _w33.text = '~P~rint'    # main_menu.nml:121
        _w33.key = 'Ctrl-F9'    # main_menu.nml:122

        _w34.text = '~M~ake directory'    # main_menu.nml:124
        _w34.command = MakeDirectory    # main_menu.nml:125
        _w34.key = 'F7'    # main_menu.nml:126

        _w35.text = '~D~elete'    # main_menu.nml:128
        _w35.command = Delete    # main_menu.nml:129
        _w35.key = 'F8'    # main_menu.nml:130

        _w36.text = 'File ~A~ttributes...'    # main_menu.nml:132
        _w36.key = 'Alt-E'    # main_menu.nml:133

        _w37.text = 'UU E~n~code...'    # main_menu.nml:135
        _w37.key = 'Ctrl-F7'    # main_menu.nml:136

        _w38.text = '~U~U Decode...'    # main_menu.nml:138
        _w38.key = 'Ctrl-F8'    # main_menu.nml:139

        _w39.text = 'Unpack diskette images'    # main_menu.nml:141
        _w39.key = 'Ctrl-I'    # main_menu.nml:142

        _w40.text = 'Delete single file'    # main_menu.nml:144
        _w40.key = 'Shift-Del'    # main_menu.nml:145

        _w42.text = 'Execute ~O~S command'    # main_menu.nml:148

        _w43.text = 'E~x~it'    # main_menu.nml:150
        _w43.command = Quit    # main_menu.nml:151
        _w43.key = 'Alt-X'    # main_menu.nml:152

        self.disk.text = '~D~isk'    # main_menu.nml:155

        _w44.text = '~F~ormat disk...'    # main_menu.nml:157
        _w44.key = 'Shift-F7'    # main_menu.nml:158

        _w45.text = '~V~olume label...'    # main_menu.nml:160

        _w46.text = '~R~eanimator...'    # main_menu.nml:162
        _w46.key = 'Shift-F6'    # main_menu.nml:163

        _w47.text = 'Disk ~e~ditor'    # main_menu.nml:165

        _w48.text = '~D~irectory tree'    # main_menu.nml:167

        self.utilities.text = '~U~tilities'    # main_menu.nml:170

        _w49.text = '~M~emory Information'    # main_menu.nml:172
        _w49.key = 'Alt-Y'    # main_menu.nml:173

        _w50.text = 'S~y~stem Information'    # main_menu.nml:175

        _w52.text = '~C~alculator'    # main_menu.nml:178
        _w52.key = 'Ctrl-F6'    # main_menu.nml:179

        _w53.text = 'ASCII Ta~b~le'    # main_menu.nml:181
        _w53.key = 'Ctrl-B'    # main_menu.nml:182

        _w54.text = '~P~hone Book'    # main_menu.nml:184
        _w54.key = 'Shift-F3'    # main_menu.nml:185

        _w55.text = '~O~pen spreadsheet'    # main_menu.nml:187
        _w55.key = 'Shift-F11'    # main_menu.nml:188

        _w56.text = 'C~D~ Player'    # main_menu.nml:190
        _w56.key = 'Ctrl-F11'    # main_menu.nml:191

        _w58.text = 'Te~r~minal'    # main_menu.nml:194
        _w58.key = 'Alt-J'    # main_menu.nml:195

        _w59.text = 'Navigator ~L~ink'    # main_menu.nml:197
        _w59.key = 'Alt-F11'    # main_menu.nml:198

        _w60.text = 'Manual di~a~l...'    # main_menu.nml:200
        _w60.key = 'Alt-A'    # main_menu.nml:201

        _w61.text = 'Di~s~connect'    # main_menu.nml:203
        _w61.key = 'Alt-H'    # main_menu.nml:204

        _w63.text = 'Edi~t~ DOS Environment'    # main_menu.nml:207

        _w64.text = '~U~ser menu'    # main_menu.nml:209
        _w64.command = UserMenu    # main_menu.nml:210
        _w64.key = 'F2'    # main_menu.nml:211

        _w65.text = 'Commands ~H~istory'    # main_menu.nml:213
        _w65.key = 'Alt-F8'    # main_menu.nml:214

        _w66.text = 'File ~E~dit History'    # main_menu.nml:216
        _w66.key = 'Alt-PgUp'    # main_menu.nml:217

        _w67.text = 'File ~V~iew History'    # main_menu.nml:219
        _w67.key = 'Alt-PgDn'    # main_menu.nml:220

        self.panel.text = '~P~anel'    # main_menu.nml:223

        _w68.text = '~M~ake list file...'    # main_menu.nml:225
        _w68.key = 'Alt-L'    # main_menu.nml:226

        _w69.text = 'Read file ~l~ist'    # main_menu.nml:228
        _w69.key = 'Alt-V'    # main_menu.nml:229

        _w70.text = '~C~ompare directories'    # main_menu.nml:231
        _w70.key = 'Ctrl-C'    # main_menu.nml:232

        _w71.text = 'Count directory len~g~th'    # main_menu.nml:234
        _w71.key = 'Alt-G'    # main_menu.nml:235

        _w72.text = 'Directory Branc~h~'    # main_menu.nml:237
        _w72.key = 'Ctrl-H'    # main_menu.nml:238

        _w74.text = 'Setup c~o~lumns'    # main_menu.nml:241
        _w74.key = 'Alt-K'    # main_menu.nml:242

        _w75.text = '~S~etup Panel'    # main_menu.nml:244
        _w75.key = 'Alt-S'    # main_menu.nml:245

        _w76.text = 'Sort ~b~y...'    # main_menu.nml:247
        _w76.key = 'Alt-B'    # main_menu.nml:248

        _w78.text = 'Select grou~p~...'    # main_menu.nml:251
        _w78.key = 'Gray "+"'    # main_menu.nml:252

        _w79.text = '~U~nselect group...'    # main_menu.nml:254
        _w79.key = 'Gray "-"'    # main_menu.nml:255

        _w80.text = 'In~v~ert selection'    # main_menu.nml:257
        _w80.key = 'Gray "*"'    # main_menu.nml:258

        _w81.text = 'Advanced filter...'    # main_menu.nml:260
        _w81.key = 'Alt-Del'    # main_menu.nml:261

        _w83.text = 'Change ~d~rive'    # main_menu.nml:264
        _w83.key = 'Alt-C'    # main_menu.nml:265

        _w84.text = 'Change direc~t~ory'    # main_menu.nml:267
        _w84.key = 'Alt-T'    # main_menu.nml:268

        _w85.text = '~R~e-read'    # main_menu.nml:270
        _w85.command = Rescan    # main_menu.nml:271
        _w85.key = 'Alt-R'    # main_menu.nml:272

        _w86.text = '~Q~uick dirs...'    # main_menu.nml:274
        _w86.key = 'Alt-Shift-0'    # main_menu.nml:275

        _w87.text = 'History of directories...'    # main_menu.nml:277
        _w87.key = 'Alt-BkSp'    # main_menu.nml:278

        self.manager.text = '~M~anager'    # main_menu.nml:281

        _w88.text = '~N~ew'    # main_menu.nml:283
        _w88.key = 'Ctrl-F3'    # main_menu.nml:284

        _w89.text = '~D~irectory tree'    # main_menu.nml:286
        _w89.command = ToggleTree    # main_menu.nml:287
        _w89.key = 'Ctrl-T'    # main_menu.nml:288

        _w90.text = '~I~nfo'    # main_menu.nml:290
        _w90.key = 'Ctrl-L'    # main_menu.nml:291

        _w91.text = '~Q~uick view'    # main_menu.nml:293
        _w91.key = 'Ctrl-Q'    # main_menu.nml:294

        _w93.text = '~S~wap panels'    # main_menu.nml:297
        _w93.key = 'Ctrl-U'    # main_menu.nml:298

        _w94.text = 'Show/hide ~l~eft panel'    # main_menu.nml:300
        _w94.key = 'Ctrl-F1'    # main_menu.nml:301

        _w95.text = 'Show/hide ~r~ight panel'    # main_menu.nml:303
        _w95.key = 'Ctrl-F2'    # main_menu.nml:304

        _w96.text = 'Show/hide inactive ~p~anel'    # main_menu.nml:306
        _w96.key = 'Ctrl-P'    # main_menu.nml:307

        _w98.text = 'Change drive le~f~t'    # main_menu.nml:310
        _w98.key = 'Alt-F1'    # main_menu.nml:311

        _w99.text = 'Change drive rig~h~t'    # main_menu.nml:313
        _w99.key = 'Alt-F2'    # main_menu.nml:314

        self.options.text = '~O~ptions'    # main_menu.nml:317

        self.options_configuration.text = '~C~onfiguration'    # main_menu.nml:320

        _w100.text = 'S~y~stem Setup...'    # main_menu.nml:322

        _w101.text = '~S~tartup...'    # main_menu.nml:324

        _w102.text = '~I~nterface...'    # main_menu.nml:326

        _w103.text = '~C~onfirmations...'    # main_menu.nml:328

        _w105.text = 'Screen sa~v~ers...'    # main_menu.nml:331

        _w106.text = 'P~r~inter setup...'    # main_menu.nml:333

        _w107.text = 'C~o~untry support...'    # main_menu.nml:335

        _w108.text = '~M~ouse...'    # main_menu.nml:337

        _w109.text = 'Comm~u~nications...'    # main_menu.nml:339

        _w111.text = '~E~ditor/Viewer...'    # main_menu.nml:342

        _w112.text = '~T~erminal...'    # main_menu.nml:344

        self.options_file_manager.text = '~F~ile Manager'    # main_menu.nml:347

        _w113.text = '~S~etup...'    # main_menu.nml:349

        _w114.text = '~I~nformation panel...'    # main_menu.nml:351

        _w115.text = 'New Manager ~d~efaults...'    # main_menu.nml:353

        _w116.text = '~C~olumn defaults...'    # main_menu.nml:355

        _w117.text = '~H~ighlight groups...'    # main_menu.nml:357

        self.options_archives.text = 'A~r~chives'    # main_menu.nml:360

        _w118.text = '~A~RC - Arc (C) NoGate Consulting'    # main_menu.nml:362

        _w119.text = 'AR~J~ - ARJ (C) Robert K. Jung'    # main_menu.nml:364

        _w120.text = '~B~SA - BSArc v1.xx (C) PhysTechSoft'    # main_menu.nml:366

        _w121.text = 'BS~2~ - BSArc v2.xx (C) PhysTechSoft'    # main_menu.nml:368

        _w122.text = '~C~HZ - ChArc (C) Dialogue'    # main_menu.nml:370

        _w123.text = '~H~A  - HA (C) Harry Hirvola'    # main_menu.nml:372

        _w124.text = 'HAP - HAP (C) Hamarsoft'    # main_menu.nml:374

        _w125.text = 'H~P~K - HPack (C) Peter Gutmann'    # main_menu.nml:376

        _w126.text = 'H~Y~P - Hyper (C) P.Sawatzki & K.P.Nicshke'    # main_menu.nml:378

        _w127.text = '~L~HA - LHArc (C) Haruyasu Yoshizaki'    # main_menu.nml:380

        _w128.text = 'L~I~M - Limit (C) J Y Lim'    # main_menu.nml:382

        _w129.text = '~R~AR - RAR (C) E. Roshal'    # main_menu.nml:384

        _w130.text = '~S~QZ - SQZ (C) J.I.Hammarberg'    # main_menu.nml:386

        _w131.text = '~T~AR - Tape ARchiver for *NIX'    # main_menu.nml:388

        _w132.text = '~U~C2 - Ultra Compressor II (C) Ad Infinitum Programs'    # main_menu.nml:390

        _w133.text = '~Z~IP - PKZIP (C) PKWARE Inc.'    # main_menu.nml:392

        _w134.text = 'ZO~O~ - Zoo (C) Rahul Dhesi'    # main_menu.nml:394

        _w136.text = 'Current archiver...'    # main_menu.nml:397
        _w136.key = 'Alt-N'    # main_menu.nml:398

        _w138.text = '~Q~uick run file edit...'    # main_menu.nml:401

        _w139.text = 'E~x~tension file edit...'    # main_menu.nml:403

        _w140.text = '~H~ighlight file edit...'    # main_menu.nml:405

        _w141.text = '~G~lobal menu definition...'    # main_menu.nml:407

        _w142.text = 'Local ~m~enu definition...'    # main_menu.nml:409

        _w143.text = '~V~iewers...'    # main_menu.nml:411

        _w144.text = '~E~ditors...'    # main_menu.nml:413

        _w146.text = '~S~ave desktop'    # main_menu.nml:416

        _w147.text = '~L~oad desktop'    # main_menu.nml:418

        _w149.text = 'C~o~lors...'    # main_menu.nml:421

        _w150.text = 'S~t~ore palette'    # main_menu.nml:423

        _w151.text = 'Lo~a~d palette'    # main_menu.nml:425

        self.window.text = '~W~indow'    # main_menu.nml:428

        _w152.text = '~T~ile'    # main_menu.nml:430

        _w153.text = 'C~a~scade'    # main_menu.nml:432

        _w154.text = 'Cl~o~se all'    # main_menu.nml:434

        _w156.text = '~S~ize/Move'    # main_menu.nml:437
        _w156.command = SizeMoveWindow    # main_menu.nml:438
        _w156.key = 'Ctrl-F5'    # main_menu.nml:439

        _w157.text = '~Z~oom'    # main_menu.nml:441
        _w157.command = ZoomWindow    # main_menu.nml:442
        _w157.key = 'Alt-Z'    # main_menu.nml:443

        _w158.text = '~N~ext'    # main_menu.nml:445
        _w158.command = NextWindow    # main_menu.nml:446
        _w158.key = 'Alt-Tab'    # main_menu.nml:447

        _w159.text = '~P~revious'    # main_menu.nml:449
        _w159.command = PreviousWindow    # main_menu.nml:450
        _w159.key = 'Ctrl-Tab'    # main_menu.nml:451

        _w160.text = '~C~lose'    # main_menu.nml:453
        _w160.command = CloseWindow    # main_menu.nml:454
        _w160.key = 'Ctrl-F4'    # main_menu.nml:455

        _w162.text = '~L~ist...'    # main_menu.nml:458
        _w162.key = 'Alt-0'    # main_menu.nml:459
