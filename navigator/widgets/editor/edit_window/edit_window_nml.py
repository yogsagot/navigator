# navml: generated
"""Generated from ``edit_window.nml``.

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
from navigator.commands import PrintFile    # edit_window.nml:1
from navigator.widgets.editor.commands import ChooseFileType, AsciiTable, CalcBlock, SwitchHiColumn, SwitchHiLine, SwitchHighLight, SwitchHiddenChars, SwitchFill, CapString, CapWord, LowString, LowWord, UpString, UpWord, DuplicateLine, SwitchDrawMode, SwitchBack, SwitchIndent, SwitchBrackets, SwitchSave, SwitchWrap, FCenter, FJustify, FLeft, FRight, SetMargins, ContSearch, LoadText, Replace, ReverseSearch, StartSearch, SaveAll, SaveTextAs, CapitalizeBlock, Clear, ClipboardCopy, ClipboardCut, ClipboardPaste, CopyBlock, GotoLineNumber, PrintBlock, IndentBlock, InsertDate, InsertTime, BlockRead, BlockWrite, LowcaseBlock, MoveBlock, SaveText, SortBlock, UnindentBlock, Undo, UpcaseBlock, SwitchBlock    # edit_window.nml:2
from navigator.widgets.editor.file_editor import FileEditor, InfoLine    # edit_window.nml:3
from navigator.settings import SETTINGS    # edit_window.nml:4
from navml.commands import CloseWindow    # edit_window.nml:5
from navml.widgets.option_strip import OptionStrip    # edit_window.nml:6
from navml.widgets.dialog.scroll_bar import ScrollBar    # edit_window.nml:7
from navml.widgets.menu.menu_item import MenuItem    # edit_window.nml:8
from navml.widgets.menu.menu_line import MenuLine    # edit_window.nml:9
from navml.widgets.menu.sub_menu import SubMenu    # edit_window.nml:10
from navml.widgets.window import Window    # edit_window.nml:11

__navml_component__ = "EditWindow"

__all__ = ["EditWindow"]


class EditWindow(Window, _Component):
    """F4: DOS Navigator's ``TEditWindow`` (``MICROED.PAS``).

    A standard window titled ``Edit - `` and the file's path, the editor filling
    the inside of its frame, a vertical scroll bar on the right frame column, a
    horizontal one along the bottom frame, and ``TInfoLine`` over the bottom
    frame's left end -- the views ``TEditWindow.Init`` inserts, in the places it
    puts them.  **It opens zoomed**, as the viewer does.

    Both scroll bars and the info line show only while the window is active, as
    ``TFileEditor.SetState`` hid the bars and ``TInfoLine.Draw`` drew nothing.
    """

    #: The document this class was generated from.
    __navml_source__ = "edit_window.nml"

    #: ``StatusDef hcEditor``: what it captions.  The editing keys are the
    #: editor's own table, and Esc and Alt+F3 close the window, asking first
    #: about a text that has changed.
    keys = {    # edit_window.nml:29
        'escape': CloseWindow,    # edit_window.nml:30
        'alt+f3': CloseWindow,    # edit_window.nml:31
        'f2': SaveText,    # edit_window.nml:32
        'ctrl+s': SaveText,    # edit_window.nml:35
        'f3': LoadText,    # edit_window.nml:36
        'shift+f2': SaveTextAs,    # edit_window.nml:37
        'ctrl+f2': SaveAll,    # edit_window.nml:38
        'f7': StartSearch,    # edit_window.nml:41
        'alt+f7': ReverseSearch,    # edit_window.nml:42
        'ctrl+f7': Replace,    # edit_window.nml:43
        'shift+f7': ContSearch,    # edit_window.nml:44
        'ctrl+shift+h': ChooseFileType,    # edit_window.nml:47
        'ctrl+shift+8': SwitchHiddenChars,    # edit_window.nml:50
        'f8': PrintFile,    # edit_window.nml:53
        'shift+f8': PrintBlock,    # edit_window.nml:54
    }

    #: Ids, annotated so the hand-written half completes them.
    editor: FileEditor    # edit_window.nml:57
    vbar: ScrollBar    # edit_window.nml:65
    hbar: ScrollBar    # edit_window.nml:80
    info: InfoLine    # edit_window.nml:93
    options: OptionStrip    # edit_window.nml:107
    edit_menu: SubMenu    # edit_window.nml:132
    edit_menu_file: SubMenu    # edit_window.nml:169
    edit_menu_search: SubMenu    # edit_window.nml:202
    edit_menu_paragraph: SubMenu    # edit_window.nml:225
    edit_menu_block: SubMenu    # edit_window.nml:248
    edit_menu_misc: SubMenu    # edit_window.nml:289
    edit_menu_misc_uppercase: SubMenu    # edit_window.nml:313
    edit_menu_misc_lowercase: SubMenu    # edit_window.nml:328
    edit_menu_misc_capitalize: SubMenu    # edit_window.nml:343
    edit_menu_options: SubMenu    # edit_window.nml:358
    edit_menu_file_type: SubMenu    # edit_window.nml:399

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_vbar_scroll(self, event: _Event) -> bool:    # edit_window.nml:65
        """``vbar`` raised an event whose handler is ``on_scroll``."""
        return False

    async def on_hbar_scroll(self, event: _Event) -> bool:    # edit_window.nml:80
        """``hbar`` raised an event whose handler is ``on_scroll``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.editor = FileEditor(parent=self)    # edit_window.nml:56
        self.vbar = ScrollBar(parent=self)    # edit_window.nml:64
        self.hbar = ScrollBar(parent=self)    # edit_window.nml:79
        self.info = InfoLine(parent=self)    # edit_window.nml:92
        self.options = OptionStrip(parent=self)    # edit_window.nml:106
        self.edit_menu = SubMenu(parent=self)    # edit_window.nml:131
        _w1 = MenuItem(parent=self.edit_menu)    # edit_window.nml:139
        _w2 = MenuLine(parent=self.edit_menu)    # edit_window.nml:143
        _w3 = MenuItem(parent=self.edit_menu)    # edit_window.nml:144
        _w4 = MenuItem(parent=self.edit_menu)    # edit_window.nml:148
        _w5 = MenuItem(parent=self.edit_menu)    # edit_window.nml:152
        _w6 = MenuItem(parent=self.edit_menu)    # edit_window.nml:156
        _w7 = MenuItem(parent=self.edit_menu)    # edit_window.nml:159
        _w8 = MenuLine(parent=self.edit_menu)    # edit_window.nml:162
        _w9 = MenuItem(parent=self.edit_menu)    # edit_window.nml:163
        _w10 = MenuLine(parent=self.edit_menu)    # edit_window.nml:167
        self.edit_menu_file = SubMenu(parent=self.edit_menu)    # edit_window.nml:168
        _w11 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:171
        _w12 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:175
        _w13 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:179
        _w14 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:183
        _w15 = MenuLine(parent=self.edit_menu_file)    # edit_window.nml:187
        _w16 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:188
        _w17 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:192
        _w18 = MenuLine(parent=self.edit_menu_file)    # edit_window.nml:196
        _w19 = MenuItem(parent=self.edit_menu_file)    # edit_window.nml:197
        self.edit_menu_search = SubMenu(parent=self.edit_menu)    # edit_window.nml:201
        _w20 = MenuItem(parent=self.edit_menu_search)    # edit_window.nml:204
        _w21 = MenuItem(parent=self.edit_menu_search)    # edit_window.nml:208
        _w22 = MenuItem(parent=self.edit_menu_search)    # edit_window.nml:212
        _w23 = MenuItem(parent=self.edit_menu_search)    # edit_window.nml:216
        _w24 = MenuItem(parent=self.edit_menu_search)    # edit_window.nml:220
        self.edit_menu_paragraph = SubMenu(parent=self.edit_menu)    # edit_window.nml:224
        _w25 = MenuItem(parent=self.edit_menu_paragraph)    # edit_window.nml:227
        _w26 = MenuItem(parent=self.edit_menu_paragraph)    # edit_window.nml:231
        _w27 = MenuItem(parent=self.edit_menu_paragraph)    # edit_window.nml:235
        _w28 = MenuItem(parent=self.edit_menu_paragraph)    # edit_window.nml:239
        _w29 = MenuLine(parent=self.edit_menu_paragraph)    # edit_window.nml:243
        _w30 = MenuItem(parent=self.edit_menu_paragraph)    # edit_window.nml:244
        self.edit_menu_block = SubMenu(parent=self.edit_menu)    # edit_window.nml:247
        _w31 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:250
        _w32 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:254
        _w33 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:258
        _w34 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:262
        _w35 = MenuLine(parent=self.edit_menu_block)    # edit_window.nml:266
        _w36 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:267
        _w37 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:271
        _w38 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:275
        _w39 = MenuLine(parent=self.edit_menu_block)    # edit_window.nml:279
        _w40 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:280
        _w41 = MenuItem(parent=self.edit_menu_block)    # edit_window.nml:284
        self.edit_menu_misc = SubMenu(parent=self.edit_menu)    # edit_window.nml:288
        _w42 = MenuItem(parent=self.edit_menu_misc)    # edit_window.nml:291
        _w43 = MenuItem(parent=self.edit_menu_misc)    # edit_window.nml:295
        _w44 = MenuItem(parent=self.edit_menu_misc)    # edit_window.nml:299
        _w45 = MenuItem(parent=self.edit_menu_misc)    # edit_window.nml:303
        _w46 = MenuItem(parent=self.edit_menu_misc)    # edit_window.nml:307
        _w47 = MenuLine(parent=self.edit_menu_misc)    # edit_window.nml:311
        self.edit_menu_misc_uppercase = SubMenu(parent=self.edit_menu_misc)    # edit_window.nml:312
        _w48 = MenuItem(parent=self.edit_menu_misc_uppercase)    # edit_window.nml:315
        _w49 = MenuItem(parent=self.edit_menu_misc_uppercase)    # edit_window.nml:319
        _w50 = MenuItem(parent=self.edit_menu_misc_uppercase)    # edit_window.nml:323
        self.edit_menu_misc_lowercase = SubMenu(parent=self.edit_menu_misc)    # edit_window.nml:327
        _w51 = MenuItem(parent=self.edit_menu_misc_lowercase)    # edit_window.nml:330
        _w52 = MenuItem(parent=self.edit_menu_misc_lowercase)    # edit_window.nml:334
        _w53 = MenuItem(parent=self.edit_menu_misc_lowercase)    # edit_window.nml:338
        self.edit_menu_misc_capitalize = SubMenu(parent=self.edit_menu_misc)    # edit_window.nml:342
        _w54 = MenuItem(parent=self.edit_menu_misc_capitalize)    # edit_window.nml:345
        _w55 = MenuItem(parent=self.edit_menu_misc_capitalize)    # edit_window.nml:349
        _w56 = MenuItem(parent=self.edit_menu_misc_capitalize)    # edit_window.nml:353
        self.edit_menu_options = SubMenu(parent=self.edit_menu)    # edit_window.nml:357
        _w57 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:360
        _w58 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:363
        _w59 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:366
        _w60 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:369
        _w61 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:372
        _w62 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:375
        _w63 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:378
        _w64 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:381
        _w65 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:384
        _w66 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:387
        _w67 = MenuItem(parent=self.edit_menu_options)    # edit_window.nml:391
        self.edit_menu_file_type = SubMenu(parent=self.edit_menu)    # edit_window.nml:398

        self.zoomed = True    # edit_window.nml:24

        self.editor.x = 1    # edit_window.nml:58
        self.editor.y = 1    # edit_window.nml:59
        self.editor.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # edit_window.nml:60
        self.editor.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # edit_window.nml:61

        self.vbar.visible = _bind(lambda _o: self.active)    # edit_window.nml:66
        self.vbar.x = _bind(lambda _o: _o.parent.width - 1)    # edit_window.nml:67
        self.vbar.y = 1    # edit_window.nml:68
        self.vbar.width = 1    # edit_window.nml:69
        self.vbar.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # edit_window.nml:70
        self.vbar.value = _bind(lambda _o: self.editor.line)    # edit_window.nml:71
        self.vbar.maximum = _bind(    # edit_window.nml:72
            lambda _o: max(0, self.editor.line_count - 1)
        )
        self.vbar.page = _bind(lambda _o: max(1, self.editor.height))    # edit_window.nml:73
        self.vbar.on_scroll = self.on_vbar_scroll    # edit_window.nml:65

        self.hbar.orientation = 'horizontal'    # edit_window.nml:81
        self.hbar.visible = _bind(lambda _o: self.active and _o.width >= 4)    # edit_window.nml:82
        self.hbar.x = 24    # edit_window.nml:83
        self.hbar.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # edit_window.nml:84
        self.hbar.width = _bind(    # edit_window.nml:85
            lambda _o: max(0, (self.options.x - 1 if self.options.visible and self.options.width else _o.parent.width - 2) - 24)
        )
        self.hbar.height = 1    # edit_window.nml:86
        self.hbar.value = _bind(lambda _o: self.editor.col)    # edit_window.nml:87
        self.hbar.maximum = _bind(lambda _o: max(255, self.editor.col))    # edit_window.nml:88
        self.hbar.page = _bind(lambda _o: max(1, self.editor.width))    # edit_window.nml:89
        self.hbar.on_scroll = self.on_hbar_scroll    # edit_window.nml:80

        self.info.visible = _bind(lambda _o: self.active)    # edit_window.nml:94
        self.info.x = 2    # edit_window.nml:95
        self.info.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # edit_window.nml:96
        self.info.width = _bind(    # edit_window.nml:97
            lambda _o: min(len(self.editor.info_text), max(0, _o.parent.width - 4))
        )
        self.info.height = 1    # edit_window.nml:98
        self.info.text = _bind(lambda _o: self.editor.info_text)    # edit_window.nml:99

        self.options.visible = _bind(    # edit_window.nml:108
            lambda _o: self.active and SETTINGS.editor.show_options
        )
        self.options.target = _bind(lambda _o: self.editor)    # edit_window.nml:109
        self.options.room = _bind(    # edit_window.nml:110
            lambda _o: max(0, _o.parent.width - 3 - (self.info.x + self.info.width) - 1)
        )
        self.options.width = _bind(lambda _o: _o.used_width)    # edit_window.nml:111
        self.options.x = _bind(    # edit_window.nml:112
            lambda _o: max(0, _o.parent.width - 3 - _o.width)
        )
        self.options.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # edit_window.nml:113
        self.options.height = 1    # edit_window.nml:114

        self.edit_menu.text = _bind(lambda _o: _tr('~E~ditor'), yielding=True)    # edit_window.nml:133
        self.edit_menu.after = 'File'    # edit_window.nml:134

        _w1.text = _bind(lambda _o: _tr('~U~ndo'), yielding=True)    # edit_window.nml:140
        _w1.command = Undo    # edit_window.nml:141
        _w1.key = 'Alt-BkSp'    # edit_window.nml:142

        _w3.text = _bind(lambda _o: _tr('Cu~t~'), yielding=True)    # edit_window.nml:145
        _w3.command = ClipboardCut    # edit_window.nml:146
        _w3.key = 'Shift-Del'    # edit_window.nml:147

        _w4.text = _bind(lambda _o: _tr('~C~opy'), yielding=True)    # edit_window.nml:149
        _w4.command = ClipboardCopy    # edit_window.nml:150
        _w4.key = 'Ctrl-Ins'    # edit_window.nml:151

        _w5.text = _bind(lambda _o: _tr('~P~aste'), yielding=True)    # edit_window.nml:153
        _w5.command = ClipboardPaste    # edit_window.nml:154
        _w5.key = 'Shift-Ins'    # edit_window.nml:155

        _w6.text = _bind(lambda _o: _tr('C~o~py to...'), yielding=True)    # edit_window.nml:157
        _w6.command = BlockWrite    # edit_window.nml:158

        _w7.text = _bind(lambda _o: _tr('P~a~ste from...'), yielding=True)    # edit_window.nml:160
        _w7.command = BlockRead    # edit_window.nml:161

        _w9.text = _bind(lambda _o: _tr('C~l~ear'), yielding=True)    # edit_window.nml:164
        _w9.command = Clear    # edit_window.nml:165
        _w9.key = 'Ctrl-Del'    # edit_window.nml:166

        self.edit_menu_file.text = _bind(    # edit_window.nml:170
            lambda _o: _tr('~F~ile'),
            yielding=True,
        )

        _w11.text = _bind(lambda _o: _tr('~O~pen...'), yielding=True)    # edit_window.nml:172
        _w11.command = LoadText    # edit_window.nml:173
        _w11.key = 'F3'    # edit_window.nml:174

        _w12.text = _bind(lambda _o: _tr('~S~ave'), yielding=True)    # edit_window.nml:176
        _w12.command = SaveText    # edit_window.nml:177
        _w12.key = 'F2'    # edit_window.nml:178

        _w13.text = _bind(lambda _o: _tr('Save ~a~s...'), yielding=True)    # edit_window.nml:180
        _w13.command = SaveTextAs    # edit_window.nml:181
        _w13.key = 'Shift-F2'    # edit_window.nml:182

        _w14.text = _bind(lambda _o: _tr('Save a~l~l...'), yielding=True)    # edit_window.nml:184
        _w14.command = SaveAll    # edit_window.nml:185
        _w14.key = 'Ctrl-F2'    # edit_window.nml:186

        _w16.text = _bind(lambda _o: _tr('~P~rint'), yielding=True)    # edit_window.nml:189
        _w16.command = PrintFile    # edit_window.nml:190
        _w16.key = 'F8'    # edit_window.nml:191

        _w17.text = _bind(lambda _o: _tr('Print ~b~lock'), yielding=True)    # edit_window.nml:193
        _w17.command = PrintBlock    # edit_window.nml:194
        _w17.key = 'Shift-F8'    # edit_window.nml:195

        _w19.text = _bind(lambda _o: _tr('E~x~it'), yielding=True)    # edit_window.nml:198
        _w19.command = CloseWindow    # edit_window.nml:199
        _w19.key = 'Ctrl-F4'    # edit_window.nml:200

        self.edit_menu_search.text = _bind(    # edit_window.nml:203
            lambda _o: _tr('~S~earch'),
            yielding=True,
        )

        _w20.text = _bind(lambda _o: _tr('~F~ind...'), yielding=True)    # edit_window.nml:205
        _w20.command = StartSearch    # edit_window.nml:206
        _w20.key = 'F7'    # edit_window.nml:207

        _w21.text = _bind(lambda _o: _tr('~R~eplace...'), yielding=True)    # edit_window.nml:209
        _w21.command = Replace    # edit_window.nml:210
        _w21.key = 'Ctrl-F7'    # edit_window.nml:211

        _w22.text = _bind(lambda _o: _tr('~S~earch again'), yielding=True)    # edit_window.nml:213
        _w22.command = ContSearch    # edit_window.nml:214
        _w22.key = 'Shift-F7'    # edit_window.nml:215

        _w23.text = _bind(lambda _o: _tr('Re~v~ersed search'), yielding=True)    # edit_window.nml:217
        _w23.command = ReverseSearch    # edit_window.nml:218
        _w23.key = 'Alt-F7'    # edit_window.nml:219

        _w24.text = _bind(    # edit_window.nml:221
            lambda _o: _tr('~G~o to line number...'),
            yielding=True,
        )
        _w24.command = GotoLineNumber    # edit_window.nml:222
        _w24.key = 'Alt-G'    # edit_window.nml:223

        self.edit_menu_paragraph.text = _bind(    # edit_window.nml:226
            lambda _o: _tr('Pa~r~agraph'),
            yielding=True,
        )

        _w25.text = _bind(lambda _o: _tr('~J~ustify'), yielding=True)    # edit_window.nml:228
        _w25.command = FJustify    # edit_window.nml:229
        _w25.key = 'Alt-J'    # edit_window.nml:230

        _w26.text = _bind(lambda _o: _tr('~R~ight'), yielding=True)    # edit_window.nml:232
        _w26.command = FRight    # edit_window.nml:233
        _w26.key = 'Alt-R'    # edit_window.nml:234

        _w27.text = _bind(lambda _o: _tr('~L~eft'), yielding=True)    # edit_window.nml:236
        _w27.command = FLeft    # edit_window.nml:237
        _w27.key = 'Alt-L'    # edit_window.nml:238

        _w28.text = _bind(lambda _o: _tr('~C~enter'), yielding=True)    # edit_window.nml:240
        _w28.command = FCenter    # edit_window.nml:241
        _w28.key = 'Alt-C'    # edit_window.nml:242

        _w30.text = _bind(lambda _o: _tr('~M~argins...'), yielding=True)    # edit_window.nml:245
        _w30.command = SetMargins    # edit_window.nml:246

        self.edit_menu_block.text = _bind(    # edit_window.nml:249
            lambda _o: _tr('~B~lock'),
            yielding=True,
        )

        _w31.text = _bind(lambda _o: _tr('~M~ove'), yielding=True)    # edit_window.nml:251
        _w31.command = MoveBlock    # edit_window.nml:252
        _w31.key = 'Ctrl K V'    # edit_window.nml:253

        _w32.text = _bind(lambda _o: _tr('~C~opy'), yielding=True)    # edit_window.nml:255
        _w32.command = CopyBlock    # edit_window.nml:256
        _w32.key = 'Ctrl K C'    # edit_window.nml:257

        _w33.text = _bind(lambda _o: _tr('~I~ndent'), yielding=True)    # edit_window.nml:259
        _w33.command = IndentBlock    # edit_window.nml:260
        _w33.key = 'Ctrl K I'    # edit_window.nml:261

        _w34.text = _bind(lambda _o: _tr('~U~nindent'), yielding=True)    # edit_window.nml:263
        _w34.command = UnindentBlock    # edit_window.nml:264
        _w34.key = 'Ctrl K U'    # edit_window.nml:265

        _w36.text = _bind(lambda _o: _tr('U~p~percase'), yielding=True)    # edit_window.nml:268
        _w36.command = UpcaseBlock    # edit_window.nml:269
        _w36.key = 'Ctrl K ['    # edit_window.nml:270

        _w37.text = _bind(lambda _o: _tr('~L~owercase'), yielding=True)    # edit_window.nml:272
        _w37.command = LowcaseBlock    # edit_window.nml:273
        _w37.key = 'Ctrl K ]'    # edit_window.nml:274

        _w38.text = _bind(lambda _o: _tr('Capi~t~alize'), yielding=True)    # edit_window.nml:276
        _w38.command = CapitalizeBlock    # edit_window.nml:277
        _w38.key = 'Ctrl K \\'    # edit_window.nml:278

        _w40.text = _bind(lambda _o: _tr('~S~ort'), yielding=True)    # edit_window.nml:281
        _w40.command = SortBlock    # edit_window.nml:282
        _w40.key = 'Alt-T'    # edit_window.nml:283

        _w41.text = _bind(lambda _o: _tr('Calc~u~late sum'), yielding=True)    # edit_window.nml:285
        _w41.command = CalcBlock    # edit_window.nml:286
        _w41.key = 'Alt-Ins'    # edit_window.nml:287

        self.edit_menu_misc.text = _bind(    # edit_window.nml:290
            lambda _o: _tr('~M~isc'),
            yielding=True,
        )

        _w42.text = _bind(lambda _o: _tr('Insert ~d~ate'), yielding=True)    # edit_window.nml:292
        _w42.command = InsertDate    # edit_window.nml:293
        _w42.key = 'Ctrl Q D'    # edit_window.nml:294

        _w43.text = _bind(lambda _o: _tr('Insert ~t~ime'), yielding=True)    # edit_window.nml:296
        _w43.command = InsertTime    # edit_window.nml:297
        _w43.key = 'Ctrl Q T'    # edit_window.nml:298

        _w44.text = _bind(lambda _o: _tr('Du~p~licate line'), yielding=True)    # edit_window.nml:300
        _w44.command = DuplicateLine    # edit_window.nml:301
        _w44.key = 'F6'    # edit_window.nml:302

        _w45.text = _bind(lambda _o: _tr('Character ta~b~le'), yielding=True)    # edit_window.nml:304
        _w45.command = AsciiTable    # edit_window.nml:305
        _w45.key = 'Ctrl P'    # edit_window.nml:306

        _w46.text = _bind(lambda _o: _tr('Line Dra~w~ing'), yielding=True)    # edit_window.nml:308
        _w46.command = SwitchDrawMode    # edit_window.nml:309
        _w46.key = 'F4'    # edit_window.nml:310

        self.edit_menu_misc_uppercase.text = _bind(    # edit_window.nml:314
            lambda _o: _tr('~U~ppercase'),
            yielding=True,
        )

        _w48.text = _bind(lambda _o: _tr('~W~ord'), yielding=True)    # edit_window.nml:316
        _w48.command = UpWord    # edit_window.nml:317
        _w48.key = 'Ctrl ['    # edit_window.nml:318

        _w49.text = _bind(lambda _o: _tr('~L~ine'), yielding=True)    # edit_window.nml:320
        _w49.command = UpString    # edit_window.nml:321
        _w49.key = 'Ctrl+Shift ['    # edit_window.nml:322

        _w50.text = _bind(lambda _o: _tr('~B~lock'), yielding=True)    # edit_window.nml:324
        _w50.command = UpcaseBlock    # edit_window.nml:325
        _w50.key = 'Ctrl K ['    # edit_window.nml:326

        self.edit_menu_misc_lowercase.text = _bind(    # edit_window.nml:329
            lambda _o: _tr('~L~owercase'),
            yielding=True,
        )

        _w51.text = _bind(lambda _o: _tr('~W~ord'), yielding=True)    # edit_window.nml:331
        _w51.command = LowWord    # edit_window.nml:332
        _w51.key = 'Ctrl ]'    # edit_window.nml:333

        _w52.text = _bind(lambda _o: _tr('~L~ine'), yielding=True)    # edit_window.nml:335
        _w52.command = LowString    # edit_window.nml:336
        _w52.key = 'Ctrl+Shift ]'    # edit_window.nml:337

        _w53.text = _bind(lambda _o: _tr('~B~lock'), yielding=True)    # edit_window.nml:339
        _w53.command = LowcaseBlock    # edit_window.nml:340
        _w53.key = 'Ctrl K ]'    # edit_window.nml:341

        self.edit_menu_misc_capitalize.text = _bind(    # edit_window.nml:344
            lambda _o: _tr('~C~apitalize'),
            yielding=True,
        )

        _w54.text = _bind(lambda _o: _tr('~W~ord'), yielding=True)    # edit_window.nml:346
        _w54.command = CapWord    # edit_window.nml:347
        _w54.key = 'Ctrl \\'    # edit_window.nml:348

        _w55.text = _bind(lambda _o: _tr('~L~ine'), yielding=True)    # edit_window.nml:350
        _w55.command = CapString    # edit_window.nml:351
        _w55.key = 'Ctrl+Shift \\'    # edit_window.nml:352

        _w56.text = _bind(lambda _o: _tr('~B~lock'), yielding=True)    # edit_window.nml:354
        _w56.command = CapitalizeBlock    # edit_window.nml:355
        _w56.key = 'Ctrl K \\'    # edit_window.nml:356

        self.edit_menu_options.text = _bind(    # edit_window.nml:359
            lambda _o: _tr('Optio~n~s'),
            yielding=True,
        )

        _w57.text = _bind(lambda _o: _tr('~B~ackspace indents'), yielding=True)    # edit_window.nml:361
        _w57.command = SwitchBack    # edit_window.nml:362

        _w58.text = _bind(lambda _o: _tr('AutoB~r~ackets'), yielding=True)    # edit_window.nml:364
        _w58.command = SwitchBrackets    # edit_window.nml:365

        _w59.text = _bind(lambda _o: _tr('Auto~i~ndent'), yielding=True)    # edit_window.nml:367
        _w59.command = SwitchIndent    # edit_window.nml:368

        _w60.text = _bind(lambda _o: _tr('~A~uto wrap'), yielding=True)    # edit_window.nml:370
        _w60.command = SwitchSave    # edit_window.nml:371

        _w61.text = _bind(lambda _o: _tr('~J~ustify on wrap'), yielding=True)    # edit_window.nml:373
        _w61.command = SwitchWrap    # edit_window.nml:374

        _w62.text = _bind(lambda _o: _tr('~V~ertical blocks'), yielding=True)    # edit_window.nml:376
        _w62.command = SwitchBlock    # edit_window.nml:377

        _w63.text = _bind(lambda _o: _tr('Opti~m~al fill'), yielding=True)    # edit_window.nml:379
        _w63.command = SwitchFill    # edit_window.nml:380

        _w64.text = _bind(    # edit_window.nml:382
            lambda _o: _tr('Current ~l~ine highlight'),
            yielding=True,
        )
        _w64.command = SwitchHiLine    # edit_window.nml:383

        _w65.text = _bind(    # edit_window.nml:385
            lambda _o: _tr('Current ~c~olumn highlight'),
            yielding=True,
        )
        _w65.command = SwitchHiColumn    # edit_window.nml:386

        _w66.text = _bind(lambda _o: _tr('Syntax ~h~ighlight'), yielding=True)    # edit_window.nml:388
        _w66.command = SwitchHighLight    # edit_window.nml:389

        _w67.text = _bind(    # edit_window.nml:392
            lambda _o: _tr('Show hi~d~den characters'),
            yielding=True,
        )
        _w67.command = SwitchHiddenChars    # edit_window.nml:393

        self.edit_menu_file_type.text = _bind(    # edit_window.nml:400
            lambda _o: _tr('File t~y~pe'),
            yielding=True,
        )
        self.edit_menu_file_type.key_command = ChooseFileType    # edit_window.nml:401
